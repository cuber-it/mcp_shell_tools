# Changelog

Alle wichtigen Änderungen an diesem Projekt werden hier dokumentiert.

Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).

## [1.1.0] - 2026-01-17

### Added
- **Transcript-Feature** - Automatische Protokollierung aller Tool-Aufrufe
  - Vollständige Parameter und Ergebnisse (bis 50KB pro Call)
  - Markdown-Format in `~/.mcp_shell_tools/transcripts/`
  - Automatischer Start beim ersten Tool-Call
  - Rotation bei >10MB
  - Manuell steuerbar via `/transcript on|off`
- **Neues Kommando** `/transcript` - Transcript an/aus schalten
- **Log-Rotation** - tool.log rotiert automatisch bei >5MB (3 Backups)

### Changed
- `/status` zeigt jetzt auch Transcript-Status an
- `log_call()` schreibt vollständiges Result ins Transcript (nicht nur 50 Zeichen)

### Fixed
- **Signal-Handling für sauberen Shutdown** - Claude Desktop friert nicht mehr ein
  - `SIGTERM`/`SIGINT`-Handler in `main.py`
  - `asyncio.CancelledError`-Handling in `shell_exec`
  - Process-Group-Killing für Shell-Befehle samt Kindprozessen
  - Neue Prozess-Registry mit `cleanup_all_processes()`

### Removed
- HTTP-Modus entfernt (jetzt in separatem Repository `mcp_shell_tools_http`)

## [1.0.0] - 2026-01-06

### Added
- Initiales Release
- Dateisystem-Tools: `file_read`, `file_write`, `file_list`, `glob_search`
- Editor-Tools: `str_replace`, `diff_preview`
- Such-Tool: `grep`
- Shell-Tool: `shell_exec` mit Timeout und Sicherheitsprüfungen
- Projekt-Tools: `cd`, `cwd`, `project_init`
- Memory-Tools: `memory_add`, `memory_show`, `memory_clear`
- Session-Management: `session_save`, `session_resume`, `session_list`
- Slash-Kommandos: `/verbose`, `/log`, `/status`
- Python Logging-Modul mit konfigurierbarem Level
- File-Locking und Auto-Save-Throttling für Stabilität
