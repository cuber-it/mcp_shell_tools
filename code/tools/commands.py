"""Slash-Kommandos: /verbose, /log, /status."""

from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

from pydantic import Field

from code.state import state
from code.persistence import session_manager


class CommandSettings:
    """Globale Einstellungen für Kommandos."""

    def __init__(self):
        self.verbose: bool = False
        self.log_enabled: bool = False
        self.log_file: Optional[Path] = None
        self._log_handle = None

    def set_verbose(self, enabled: bool) -> str:
        """Aktiviert/deaktiviert ausführliche Ausgaben."""
        self.verbose = enabled
        return f"Verbose: {'ON' if enabled else 'OFF'}"

    def set_logging(self, enabled: bool, file_path: Optional[str] = None) -> str:
        """Aktiviert/deaktiviert Tool-Logging in Datei."""
        if enabled:
            if file_path:
                self.log_file = Path(file_path).expanduser().resolve()
            else:
                # Default: ~/.mcp_shell_tools/tool.log
                self.log_file = Path.home() / ".mcp_shell_tools" / "tool.log"

            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            self.log_enabled = True
            return f"Logging: ON -> {self.log_file}"
        else:
            self.log_enabled = False
            self.log_file = None
            return "Logging: OFF"

    def log_call(self, tool: str, params: dict, result: str, success: bool) -> None:
        """Schreibt einen Tool-Call ins Log."""
        if not self.log_enabled or not self.log_file:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "OK" if success else "FAIL"

        # Parameter kürzen
        params_str = str(params)[:100]
        if len(str(params)) > 100:
            params_str += "..."

        line = f"[{timestamp}] {status} {tool} {params_str}\n"

        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(line)
        except Exception:
            pass  # Silent fail bei Log-Fehlern

    def get_status(self) -> dict:
        """Gibt aktuelle Einstellungen zurück."""
        return {
            "verbose": self.verbose,
            "log_enabled": self.log_enabled,
            "log_file": str(self.log_file) if self.log_file else None,
        }


# Globale Instanz
settings = CommandSettings()


# --- Tool Function ---

async def command(
    cmd: Annotated[str, Field(description="Kommando: verbose, log, status")],
    arg: Annotated[Optional[str], Field(description="Argument: on/off oder Dateipfad")] = None,
) -> str:
    """Führt ein Slash-Kommando aus.

    Verfügbare Kommandos:
    - /verbose on|off - Ausführliche Ausgaben
    - /log on|off [datei] - Tool-Logging in Datei
    - /status - Zeigt aktuelle Einstellungen

    Beispiele:
      command(cmd="verbose", arg="on")
      command(cmd="log", arg="on")
      command(cmd="log", arg="off")
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

    elif cmd_lower == "status":
        lines = ["# Aktuelle Einstellungen\n"]

        # Verbose
        lines.append(f"- **Verbose:** {'ON' if settings.verbose else 'OFF'}")

        # Logging
        if settings.log_enabled:
            lines.append(f"- **Logging:** ON -> `{settings.log_file}`")
        else:
            lines.append("- **Logging:** OFF")

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
        return f"Unbekanntes Kommando: {cmd}\n\nVerfügbar: verbose, log, status"
