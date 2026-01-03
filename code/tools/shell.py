"""Shell-Tool: Befehle ausführen."""

import asyncio
from typing import Optional, Annotated

from pydantic import Field

from config import (
    SHELL_TIMEOUT_SECONDS,
    DEFAULT_ENCODING,
    BLOCKED_PATTERNS,
    SUDO_NEEDS_CONFIRMATION,
)
from state import state
from utils.output import truncate_output


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
        return f"💻 $ {command}\n\n{message}"
    
    # Working Directory bestimmen
    if working_dir:
        cwd = state.resolve_path(working_dir)
        if not cwd.is_dir():
            return f"💻 $ {command}\n\nFehler: Working Directory existiert nicht: {cwd}"
    else:
        cwd = state.working_dir
    
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return f"💻 $ {command}\n\nFehler: Timeout nach {timeout}s - Prozess wurde beendet"
        
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
        
    except Exception as e:
        return f"💻 $ {command}\n\nFehler: {e}"
