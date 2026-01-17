"""Shell-Tool: Befehle ausführen."""

import asyncio
import os
import signal
from typing import Optional, Annotated, Set

from pydantic import Field

from code.config import (
    SHELL_TIMEOUT_SECONDS,
    DEFAULT_ENCODING,
    BLOCKED_PATTERNS,
    SUDO_NEEDS_CONFIRMATION,
)
from code.state import state
from code.utils.output import truncate_output
from code.utils.logging import get_logger

logger = get_logger("tools.shell")

# Registry für laufende Prozesse (für Cleanup bei Shutdown)
_running_processes: Set[asyncio.subprocess.Process] = set()


async def _kill_process_tree(proc: asyncio.subprocess.Process):
    """Killt einen Prozess und alle seine Kindprozesse.

    Da wir start_new_session=True nutzen, können wir die ganze
    Process-Group auf einmal terminieren.
    """
    if proc.returncode is not None:
        return  # Schon beendet

    pid = proc.pid
    logger.info(f"Killing process tree (PID {pid})")

    try:
        # Ganze Process-Group terminieren (SIGTERM an die Gruppe)
        os.killpg(pid, signal.SIGTERM)

        # Kurz warten auf sauberes Beenden
        try:
            await asyncio.wait_for(proc.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            # Force kill der Process-Group
            logger.warning(f"Process {pid} didn't terminate, force killing")
            try:
                os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            await proc.wait()
    except ProcessLookupError:
        pass  # Schon beendet
    except OSError as e:
        logger.warning(f"Error killing process {pid}: {e}")
        # Fallback: nur den Hauptprozess killen
        try:
            proc.kill()
            await proc.wait()
        except ProcessLookupError:
            pass


def cleanup_all_processes():
    """Beendet alle laufenden Subprozesse (synchron, für Shutdown)."""
    for proc in list(_running_processes):
        if proc.returncode is None:  # Noch am Laufen
            pid = proc.pid
            logger.info(f"Cleanup: Killing process {pid}")
            try:
                os.killpg(pid, signal.SIGTERM)
            except (ProcessLookupError, OSError):
                try:
                    proc.terminate()
                except ProcessLookupError:
                    pass
    _running_processes.clear()


def check_command_safety(command: str) -> tuple[bool, str]:
    """Prüft ob ein Befehl sicher ist.
    
    Returns:
        (is_safe, message) - False + Fehlermeldung wenn geblockt
    """
    # Gegen Blocked Patterns prüfen
    for pattern in BLOCKED_PATTERNS:
        if pattern.search(command):
            return False, f"❌ Blocked: Gefährliches Pattern erkannt ({pattern.pattern})"
    
    # Sudo-Warnung
    if SUDO_NEEDS_CONFIRMATION and command.strip().startswith('sudo '):
        return False, "⚠️ Sudo-Befehl erkannt. Bitte explizit bestätigen."
    
    return True, ""


# --- Tool Function ---

async def shell_exec(
    command: Annotated[str, Field(description="Shell-Befehl (bash)")],
    timeout: Annotated[int, Field(description="Timeout in Sekunden", ge=1, le=300)] = SHELL_TIMEOUT_SECONDS,
    working_dir: Annotated[Optional[str], Field(description="Working Directory (default: aktuelles)")] = None,
) -> str:
    """Führt einen Shell-Befehl aus.
    
    Läuft im aktuellen Working Directory (siehe cwd/cd).
    Stdout und Stderr werden zurückgegeben.
    
    Für lang laufende Prozesse den Timeout erhöhen.
    Für interaktive Befehle (vim, less, etc.) nicht geeignet.
    """
    # Sicherheitsprüfung
    is_safe, message = check_command_safety(command)
    if not is_safe:
        logger.warning(f"Blocked command: {command[:50]}")
        return f"💻 $ {command}\n\n{message}"
    
    # Working Directory bestimmen
    if working_dir:
        cwd = state.resolve_path(working_dir)
        if not cwd.is_dir():
            return f"💻 $ {command}\n\nFehler: Working Directory existiert nicht: {cwd}"
    else:
        cwd = state.working_dir
    
    proc = None
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            # Neue Process-Group für sauberes Kill
            start_new_session=True,
        )

        # Prozess registrieren für Cleanup
        _running_processes.add(proc)

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            await _kill_process_tree(proc)
            logger.warning(f"Command timeout after {timeout}s: {command[:50]}")
            return f"💻 $ {command}\n\nFehler: Timeout nach {timeout}s - Prozess wurde beendet"
        except asyncio.CancelledError:
            # KRITISCH: Client hat Request abgebrochen (Claude Desktop)
            logger.warning(f"Command cancelled: {command[:50]}")
            await _kill_process_tree(proc)
            raise  # CancelledError weitergeben
        finally:
            # Aus Registry entfernen
            _running_processes.discard(proc)

        result_parts = [f"💻 $ {command}"]

        # Working Dir anzeigen wenn nicht default
        if working_dir:
            result_parts.append(f"   (in {cwd})")

        result_parts.append("")  # Leerzeile

        # Stdout
        if stdout:
            stdout_text = stdout.decode(DEFAULT_ENCODING, errors="replace")
            result_parts.append(truncate_output(stdout_text))

        # Stderr
        if stderr:
            stderr_text = stderr.decode(DEFAULT_ENCODING, errors="replace")
            result_parts.append(f"[STDERR]\n{truncate_output(stderr_text)}")

        # Exit Code (nur bei Fehler)
        if proc.returncode != 0:
            result_parts.append(f"[Exit Code: {proc.returncode}]")

        # Wenn keine Ausgabe
        if not stdout and not stderr:
            result_parts.append("(keine Ausgabe)")

        return "\n".join(result_parts)

    except asyncio.CancelledError:
        # Weitergeben damit MCP-Framework sauber beenden kann
        raise
    except Exception as e:
        return f"💻 $ {command}\n\nFehler: {e}"
    finally:
        # Safety: Falls Prozess noch läuft, killen
        if proc and proc.returncode is None:
            await _kill_process_tree(proc)
            _running_processes.discard(proc)
