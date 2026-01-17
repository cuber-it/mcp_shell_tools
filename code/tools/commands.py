"""Slash-Kommandos: /verbose, /log, /status, /transcript."""

from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

from pydantic import Field

from code.state import state
from code.persistence import session_manager

# Log-Konfiguration
DEFAULT_LOG_DIR = Path.home() / ".mcp_shell_tools"
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "tool.log"
TRANSCRIPT_DIR = DEFAULT_LOG_DIR / "transcripts"
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
LOG_BACKUP_COUNT = 3  # tool.log, tool.log.1, tool.log.2, tool.log.3
MAX_TRANSCRIPT_SIZE = 10 * 1024 * 1024  # 10 MB pro Transcript


class CommandSettings:
    """Globale Einstellungen für Kommandos."""

    def __init__(self):
        self.verbose: bool = False
        self.log_enabled: bool = False
        self.log_file: Optional[Path] = None
        # Transcript - vollständige Protokollierung
        self.transcript_enabled: bool = False
        self.transcript_file: Optional[Path] = None
        self._transcript_started: Optional[datetime] = None
        self._auto_transcript_checked: bool = False

    def _ensure_auto_transcript(self) -> None:
        """Startet Transcript automatisch beim ersten Tool-Call (lazy init)."""
        if self._auto_transcript_checked:
            return
        self._auto_transcript_checked = True
        self._start_transcript()

    def _start_transcript(self) -> str:
        """Startet ein neues Transcript."""
        TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
        
        now = datetime.now()
        self._transcript_started = now
        filename = now.strftime("%Y-%m-%d-%H-%M-%S.md")
        self.transcript_file = TRANSCRIPT_DIR / filename
        self.transcript_enabled = True
        
        # Header schreiben
        header = f"""# MCP Shell Tools Transcript
**Gestartet:** {now.strftime("%Y-%m-%d %H:%M:%S")}
**Server:** stdio (Claude Desktop)

---

"""
        self.transcript_file.write_text(header, encoding='utf-8')
        return f"Transcript gestartet: {self.transcript_file}"

    def _stop_transcript(self) -> str:
        """Stoppt das aktuelle Transcript."""
        if not self.transcript_enabled:
            return "Kein aktives Transcript"
        
        # Footer schreiben
        if self.transcript_file and self.transcript_file.exists():
            with open(self.transcript_file, 'a', encoding='utf-8') as f:
                f.write(f"\n---\n**Beendet:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        result = f"Transcript beendet: {self.transcript_file}"
        self.transcript_enabled = False
        self.transcript_file = None
        self._transcript_started = None
        return result

    def _setup_rotating_log(self, file_path: Path) -> None:
        """Richtet rollierendes Logging ein."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_file = file_path
        self.log_enabled = True

    def set_verbose(self, enabled: bool) -> str:
        """Aktiviert/deaktiviert ausführliche Ausgaben."""
        self.verbose = enabled
        return f"Verbose: {'ON' if enabled else 'OFF'}"

    def set_logging(self, enabled: bool, file_path: Optional[str] = None) -> str:
        """Aktiviert/deaktiviert Tool-Logging in Datei."""
        if enabled:
            if file_path:
                log_path = Path(file_path).expanduser().resolve()
            else:
                log_path = DEFAULT_LOG_FILE
            
            self._setup_rotating_log(log_path)
            return f"Logging: ON -> {self.log_file} (max {MAX_LOG_SIZE // 1024 // 1024}MB, {LOG_BACKUP_COUNT} Backups)"
        else:
            self.log_enabled = False
            self.log_file = None
            return "Logging: OFF"

    def log_call(self, tool: str, params: dict, result: str, success: bool) -> None:
        """Schreibt einen Tool-Call ins Log (mit Rotation) und Transcript."""
        # Auto-start Transcript beim ersten Call
        self._ensure_auto_transcript()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "OK" if success else "FAIL"

        # --- Kurzes Log (wenn aktiviert) ---
        if self.log_enabled and self.log_file:
            params_str = str(params)[:100]
            if len(str(params)) > 100:
                params_str += "..."

            line = f"[{timestamp}] {status} {tool} {params_str}\n"

            try:
                self._rotate_if_needed()
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(line)
            except Exception:
                pass

        # --- Vollständiges Transcript ---
        if self.transcript_enabled and self.transcript_file:
            self._write_transcript(timestamp, tool, params, result, success)
    
    def _rotate_if_needed(self) -> None:
        """Rotiert Log wenn zu groß."""
        if not self.log_file or not self.log_file.exists():
            return
        
        if self.log_file.stat().st_size < MAX_LOG_SIZE:
            return
        
        # Rotation: .3 löschen, .2->.3, .1->.2, log->.1
        for i in range(LOG_BACKUP_COUNT, 0, -1):
            old = self.log_file.with_suffix(f".log.{i}")
            new = self.log_file.with_suffix(f".log.{i+1}" if i < LOG_BACKUP_COUNT else ".log.delete")
            if old.exists():
                if i == LOG_BACKUP_COUNT:
                    old.unlink()  # Ältestes löschen
                else:
                    old.rename(new)
        
        # Aktuelles Log -> .1
        self.log_file.rename(self.log_file.with_suffix(".log.1"))

    def _write_transcript(self, timestamp: str, tool: str, params: dict, result: str, success: bool) -> None:
        """Schreibt vollständigen Tool-Call ins Transcript."""
        if not self.transcript_file:
            return
            
        # Transcript-Rotation prüfen
        if self.transcript_file.exists() and self.transcript_file.stat().st_size > MAX_TRANSCRIPT_SIZE:
            # Neues Transcript starten
            self._stop_transcript()
            self._start_transcript()
        
        status_emoji = "✓" if success else "✗"
        
        # Params formatieren
        params_formatted = "\n".join(f"  {k}: {v}" for k, v in params.items()) if params else "  (keine)"
        
        # Result kürzen wenn extrem lang (>50KB)
        result_text = result
        if len(result) > 50000:
            result_text = result[:50000] + f"\n\n... (gekürzt, {len(result)} Zeichen total)"
        
        entry = f"""
## [{timestamp}] {status_emoji} `{tool}`

**Parameter:**
{params_formatted}

**Result:**
```
{result_text}
```

---
"""
        try:
            with open(self.transcript_file, 'a', encoding='utf-8') as f:
                f.write(entry)
        except Exception:
            pass  # Silent fail

    def get_status(self) -> dict:
        """Gibt aktuelle Einstellungen zurück."""
        return {
            "verbose": self.verbose,
            "log_enabled": self.log_enabled,
            "log_file": str(self.log_file) if self.log_file else None,
            "transcript_enabled": self.transcript_enabled,
            "transcript_file": str(self.transcript_file) if self.transcript_file else None,
        }


# Globale Instanz
settings = CommandSettings()


# --- Tool Function ---

async def command(
    cmd: Annotated[str, Field(description="Kommando: verbose, log, transcript, status")],
    arg: Annotated[Optional[str], Field(description="Argument: on/off oder Dateipfad")] = None,
) -> str:
    """Führt ein Slash-Kommando aus.

    Verfügbare Kommandos:
    - /verbose on|off - Ausführliche Ausgaben
    - /log on|off [datei] - Tool-Logging in Datei (kurz)
    - /transcript on|off - Vollständiges Transcript aller Tool-Calls
    - /status - Zeigt aktuelle Einstellungen

    Beispiele:
      command(cmd="verbose", arg="on")
      command(cmd="log", arg="on")
      command(cmd="transcript", arg="off")
      command(cmd="status")
    """
    cmd_lower = cmd.lower().strip().lstrip('/')

    if cmd_lower == "verbose":
        if arg is None:
            return f"Verbose: {'ON' if settings.verbose else 'OFF'}"
        enabled = arg.lower() in ("on", "1", "true", "yes")
        return settings.set_verbose(enabled)

    elif cmd_lower == "log":
        if arg is None:
            status = "ON" if settings.log_enabled else "OFF"
            if settings.log_file:
                return f"Logging: {status} -> {settings.log_file}"
            return f"Logging: {status}"

        if arg.lower() in ("off", "0", "false", "no"):
            return settings.set_logging(False)
        elif arg.lower() in ("on", "1", "true", "yes"):
            return settings.set_logging(True)
        else:
            # arg ist Dateipfad
            return settings.set_logging(True, arg)

    elif cmd_lower == "transcript":
        if arg is None:
            status = "ON" if settings.transcript_enabled else "OFF"
            if settings.transcript_file:
                return f"Transcript: {status} -> {settings.transcript_file}"
            return f"Transcript: {status}"

        if arg.lower() in ("off", "0", "false", "no"):
            return settings._stop_transcript()
        elif arg.lower() in ("on", "1", "true", "yes"):
            if settings.transcript_enabled:
                return f"Transcript bereits aktiv: {settings.transcript_file}"
            return settings._start_transcript()
        else:
            return "Unbekanntes Argument. Nutze: on/off"

    elif cmd_lower == "status":
        lines = ["# Aktuelle Einstellungen\n"]

        # Verbose
        lines.append(f"- **Verbose:** {'ON' if settings.verbose else 'OFF'}")

        # Logging
        if settings.log_enabled:
            lines.append(f"- **Logging:** ON -> `{settings.log_file}`")
        else:
            lines.append("- **Logging:** OFF")

        # Transcript
        if settings.transcript_enabled:
            lines.append(f"- **Transcript:** ON -> `{settings.transcript_file}`")
            if settings._transcript_started:
                lines.append(f"  - Gestartet: {settings._transcript_started.strftime('%H:%M:%S')}")
        else:
            lines.append("- **Transcript:** OFF")

        # Working Directory
        lines.append(f"- **Working Dir:** `{state.working_dir}`")

        # Session
        if session_manager.current_session:
            session = session_manager.current_session
            lines.append(f"- **Session:** {session.project_name}")
            lines.append(f"  - Memories: {len(session.memories)}")
            lines.append(f"  - Tool-Calls: {len(session.tool_log)}")
        else:
            lines.append("- **Session:** (keine)")

        return "\n".join(lines)

    else:
        return f"Unbekanntes Kommando: {cmd}\n\nVerfügbar: verbose, log, transcript, status"
