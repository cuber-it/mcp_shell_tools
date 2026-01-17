#!/usr/bin/env python3
"""
Bietet Claude Zugriff auf:
- Dateisystem (lesen, schreiben, suchen)
- Präzises Editieren (str_replace)
- Shell-Befehle
- Projekt-Kontext (CLAUDE.md)
- Persistentes Gedächtnis (Memory)
- Session-Management
"""

from functools import wraps
from typing import Any, Callable

from mcp.server.fastmcp import FastMCP

from code.persistence import session_manager

# Tool-Imports
from code.tools.filesystem import (
    file_read,
    file_write,
    file_list,
    glob_search,
)
from code.tools.editor import (
    str_replace,
    diff_preview,
)
from code.tools.search import grep
from code.tools.shell import shell_exec
from code.tools.project import cd, cwd, project_init
from code.tools.memory import (
    memory_add,
    memory_show,
    memory_clear,
)
from code.tools.session import (
    session_save,
    session_resume,
    session_list,
)
from code.tools.commands import command, settings as command_settings


# --- Server Setup ---

mcp = FastMCP(
    "mcp_shell_tools",
    instructions="""Workstation MCP Server für lokale Entwicklung.

Workflow-Empfehlungen:
1. 'session_resume' lädt letzte Session oder 'cd' ins Projektverzeichnis
2. 'project_init' lädt CLAUDE.md mit Projekt-Kontext
3. 'file_read' mit Zeilennummern zum Lesen
4. 'str_replace' für präzise Änderungen (nie ganze Datei überschreiben)
5. 'grep' und 'glob_search' zum Finden von Code
6. 'shell_exec' für Git, Tests, Build-Befehle
7. 'memory_add' für Erkenntnisse und Entscheidungen
8. 'session_save' am Ende mit Zusammenfassung

Tool-Aufrufe werden automatisch geloggt und persistiert.
"""
)


# --- Auto-Log Wrapper ---

def with_auto_log(tool_name: str, func: Callable) -> Callable:
    """Wrapper der Tool-Aufrufe automatisch loggt."""
    import asyncio

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Params sind jetzt direkt in kwargs (flache Signatur)
        params = kwargs.copy()

        try:
            result = await func(*args, **kwargs)

            # Result als String
            result_str = result if isinstance(result, str) else str(result)
            
            # Summary für Session-Log (kurz)
            summary = result_str[:50].replace('\n', ' ')

            # Session-Log (nur wenn Session aktiv)
            session_manager.log_tool_call(
                tool=tool_name,
                params=params,
                result_summary=summary,
                success=True
            )

            # File-Log + Transcript (vollständiges Result für Transcript!)
            command_settings.log_call(tool_name, params, result_str, True)

            return result

        except asyncio.CancelledError:
            # Request wurde abgebrochen - nicht loggen, direkt weitergeben
            raise
        except Exception as e:
            error_str = str(e)
            session_manager.log_tool_call(
                tool=tool_name,
                params=params,
                result_summary=error_str[:50],
                success=False
            )
            command_settings.log_call(tool_name, params, error_str, False)
            raise

    return wrapper


# --- Tool Registration Helper ---

def register_tool(
    name: str,
    func: Callable,
    title: str,
    read_only: bool = True,
    destructive: bool = False,
    idempotent: bool = True,
    open_world: bool = False,
    log: bool = True
):
    """Registriert ein Tool mit optionalem Auto-Logging."""
    wrapped = with_auto_log(name, func) if log else func
    
    mcp.tool(
        name=name,
        annotations={
            "title": title,
            "readOnlyHint": read_only,
            "destructiveHint": destructive,
            "idempotentHint": idempotent,
            "openWorldHint": open_world,
        }
    )(wrapped)


# --- Tool Registration ---

# Filesystem
register_tool("file_read", file_read, "Datei lesen")
register_tool("file_write", file_write, "Datei schreiben", read_only=False, destructive=True)
register_tool("file_list", file_list, "Verzeichnis auflisten")
register_tool("glob_search", glob_search, "Dateien suchen (glob)")

# Editor
register_tool("str_replace", str_replace, "Text ersetzen", read_only=False)
register_tool("diff_preview", diff_preview, "Änderungsvorschau")

# Search
register_tool("grep", grep, "Textsuche in Dateien")

# Shell
register_tool("shell_exec", shell_exec, "Shell-Befehl ausführen", 
              read_only=False, destructive=True, idempotent=False, open_world=True)

# Project
register_tool("cd", cd, "Verzeichnis wechseln", read_only=False, log=False)  # cd loggt nicht sich selbst
register_tool("cwd", cwd, "Aktuelles Verzeichnis")
register_tool("project_init", project_init, "Projekt initialisieren")

# Memory
register_tool("memory_add", memory_add, "Erkenntnis speichern", read_only=False, log=False)
register_tool("memory_show", memory_show, "Gedächtnis anzeigen")
register_tool("memory_clear", memory_clear, "Gedächtnis löschen", read_only=False, destructive=True, log=False)

# Session
register_tool("session_save", session_save, "Session speichern", read_only=False, log=False)
register_tool("session_resume", session_resume, "Session laden", read_only=False, log=False)
register_tool("session_list", session_list, "Sessions auflisten")

# Commands (Slash-Kommandos)
register_tool("command", command, "Slash-Kommando ausführen", read_only=False, log=False)


# --- Entry Point ---

def main():
    """Entry Point für das Package."""
    mcp.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Cleanup bei Ctrl+C
        from code.tools.shell import cleanup_all_processes
        cleanup_all_processes()
        print("Server beendet.")
