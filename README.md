# mcp_shell_tools

MCP Server für lokale Entwicklungsarbeit via **Claude Desktop** (stdio).

Gibt Claude ähnliche Fähigkeiten wie Claude Code:
- Dateisystem-Zugriff
- Shell-Befehle
- Präzises Code-Editing
- Persistentes Gedächtnis
- Session-Management
- Automatisches Transcript

> **Hinweis:** Dies ist die **stdio-Version** für Claude Desktop.  
> Für Remote-Zugriff via claude.ai siehe [mcp_shell_tools_http](../mcp_shell_tools_http/).

## Features

### Dateisystem
| Tool | Beschreibung |
|------|--------------|
| `file_read` | Datei lesen mit Zeilennummern und Range-Support |
| `file_write` | Datei schreiben (für neue Dateien) |
| `file_list` | Verzeichnis auflisten (rekursiv, mit Hidden-Option) |
| `glob_search` | Dateien nach Pattern suchen (`**/*.py`) |

### Editor
| Tool | Beschreibung |
|------|--------------|
| `str_replace` | Präzises Editieren (Text muss einmal vorkommen) |
| `diff_preview` | Änderungsvorschau als Unified Diff |

### Suche
| Tool | Beschreibung |
|------|--------------|
| `grep` | Textsuche in Dateien (Text oder Regex, mit Kontext) |

### Shell
| Tool | Beschreibung |
|------|--------------|
| `shell_exec` | Shell-Befehle ausführen (mit Timeout, Process-Cleanup) |

### Projekt
| Tool | Beschreibung |
|------|--------------|
| `cd` | Working Directory wechseln (lädt automatisch CLAUDE.md) |
| `cwd` | Aktuelles Verzeichnis anzeigen |
| `project_init` | CLAUDE.md laden für Projekt-Kontext |

### Gedächtnis & Session
| Tool | Beschreibung |
|------|--------------|
| `memory_add` | Erkenntnis/Entscheidung/TODO/Frage speichern |
| `memory_show` | Alle Einträge anzeigen |
| `memory_clear` | Gedächtnis löschen |
| `session_save` | Session mit Zusammenfassung speichern |
| `session_resume` | Frühere Session laden |
| `session_list` | Alle Sessions auflisten |

### Kommandos
| Tool | Beschreibung |
|------|--------------|
| `command` | Slash-Kommandos: `/verbose`, `/log`, `/transcript`, `/status` |

## Installation

```bash
# Repository klonen
git clone https://github.com/ucuber/mcp_shell_tools.git
cd mcp_shell_tools

# venv erstellen und aktivieren
python -m venv .venv
source .venv/bin/activate  # Linux/Mac

# Abhängigkeiten installieren
pip install -r requirements.txt
```

## Claude Desktop Konfiguration

Füge zu `~/.config/Claude/claude_desktop_config.json` hinzu:

### Empfohlen: Mit run.sh

```bash
chmod +x /pfad/zu/mcp_shell_tools/run.sh
```

```json
{
  "mcpServers": {
    "shell-tools": {
      "command": "/pfad/zu/mcp_shell_tools/run.sh"
    }
  }
}
```

### Alternative: Direkter Aufruf

```json
{
  "mcpServers": {
    "shell-tools": {
      "command": "/pfad/zu/mcp_shell_tools/.venv/bin/python",
      "args": ["code/main.py", "serve"]
    }
  }
}
```

Danach Claude Desktop neu starten.

## Verwendung

### Session starten

```
# Letzte Session fortsetzen
session_resume()

# Oder in Projektverzeichnis wechseln
cd /home/user/projekte/mein-projekt
```

### Erkenntnisse speichern

```
memory_add("Bug gefunden: Division by Zero in calculate()", category="note")
memory_add("SQLite statt PostgreSQL wegen Simplizität", category="decision")
memory_add("Performance bei >10k Datensätzen testen", category="todo")
memory_add("Wie verhält sich der Export bei Unicode?", category="question")
```

### Session beenden

```
session_save(summary="Feature X implementiert. Tests fehlen noch.")
```

### Dateien bearbeiten

```
# Lesen mit Zeilennummern
file_read("src/main.py")

# Nur bestimmte Zeilen
file_read("src/main.py", start_line=50, end_line=100)

# Präzise ändern (NICHT file_write für Änderungen!)
str_replace(
    path="src/main.py",
    old_str="def calculate(x):\n    return x * 2",
    new_str="def calculate(x):\n    return x * 3"
)
```

## Persistenz

### Sessions & Memory

```
~/.mcp_shell_tools/
├── sessions/
│   └── projekt-name/
│       ├── session.json    # Strukturierte Daten
│       └── memory.md       # Menschenlesbares Format
└── transcripts/
    └── 2026-01-17-14-30-00.md  # Vollständiges Tool-Log
```

### Transcript

Alle Tool-Aufrufe werden automatisch protokolliert:

```markdown
# MCP Shell Tools Transcript
**Gestartet:** 2026-01-17 14:30:00

---

## [14:30:05] ✓ `file_read`

**Parameter:**
  path: src/main.py
  start_line: 1
  end_line: 50

**Result:**
[Zeilen 1-50 von 120]
  1 │ #!/usr/bin/env python3
  ...
```

Nützlich für:
- Nachvollziehbarkeit
- Debugging
- Dokumentation der Arbeit

## CLAUDE.md

Erstelle eine `CLAUDE.md` im Projektverzeichnis für automatischen Kontext:

```markdown
# Projekt: Mein Projekt

## Tech Stack
- Python 3.11
- SQLite + SQLAlchemy

## Konventionen
- Black für Formatting
- Type Hints überall

## Aktuelle Aufgabe
Feature X implementieren
```

Wird automatisch geladen bei `cd` ins Verzeichnis.

## Projektstruktur

```
mcp_shell_tools/
├── code/
│   ├── main.py              # CLI Entry Point
│   ├── server.py            # MCP Server Setup
│   ├── state.py             # Globaler State
│   ├── config.py            # Konstanten
│   ├── tools/
│   │   ├── filesystem.py    # file_read, file_write, file_list, glob_search
│   │   ├── editor.py        # str_replace, diff_preview
│   │   ├── search.py        # grep
│   │   ├── shell.py         # shell_exec (mit Process-Cleanup)
│   │   ├── project.py       # cd, cwd, project_init
│   │   ├── memory.py        # memory_add, memory_show, memory_clear
│   │   ├── session.py       # session_save, session_resume, session_list
│   │   └── commands.py      # /verbose, /log, /transcript, /status
│   ├── persistence/
│   │   ├── models.py        # SessionData, MemoryEntry
│   │   └── session_manager.py
│   └── utils/
│       ├── output.py        # Formatierung
│       ├── logging.py       # Logger-Setup
│       └── paths.py         # Pfad-Utilities
├── tests/                   # pytest Tests
├── docs/                    # Dokumentation
├── requirements.txt         # mcp, pydantic
├── pyproject.toml
├── run.sh                   # Wrapper-Script
└── README.md
```

## Entwicklung

```bash
# Tests ausführen
pytest

# Mit Coverage
pytest --cov=code
```

## Lizenz

MIT License - siehe [LICENSE](LICENSE)

## Danksagung

Entwickelt mit Unterstützung von [Claude](https://claude.ai) (Anthropic).  
Claude war Architekt, Code-Reviewer und erster Betatester seines eigenen MCP-Servers. 🤖
