# workstation_mcp

MCP Server für lokale Entwicklungsarbeit. Gibt Claude.ai ähnliche Fähigkeiten wie Claude Code, plus persistentes Gedächtnis und Session-Management.

## Features

### Dateisystem
| Tool | Beschreibung |
|------|--------------|
| `file_read` | Datei lesen mit Zeilennummern und Range-Support |
| `file_write` | Datei schreiben (für neue Dateien) |
| `file_list` | Verzeichnis auflisten |
| `glob_search` | Dateien nach Pattern suchen |

### Editor
| Tool | Beschreibung |
|------|--------------|
| `str_replace` | Präzises Editieren (Text ersetzen) |
| `diff_preview` | Änderungsvorschau als Unified Diff |

### Suche
| Tool | Beschreibung |
|------|--------------|
| `grep` | Textsuche in Dateien (mit Regex-Support) |

### Shell
| Tool | Beschreibung |
|------|--------------|
| `shell_exec` | Shell-Befehle ausführen |

### Projekt
| Tool | Beschreibung |
|------|--------------|
| `cd` / `cwd` | Working Directory verwalten |
| `project_init` | CLAUDE.md laden für Projekt-Kontext |

### Gedächtnis & Session
| Tool | Beschreibung |
|------|--------------|
| `memory_add` | Erkenntnis/Entscheidung/TODO speichern |
| `memory_show` | Alle Einträge anzeigen |
| `memory_clear` | Gedächtnis löschen |
| `session_save` | Session mit Zusammenfassung speichern |
| `session_resume` | Frühere Session laden |
| `session_list` | Alle Sessions auflisten |

## Installation

```bash
# Repository klonen oder ZIP entpacken
cd workstation_mcp

# venv erstellen und aktivieren
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# oder: .venv\Scripts\activate  # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt

# Paket installieren (editable mode)
pip install -e .
```

## Test

```bash
# Server starten (sollte auf stdin warten)
workstation-mcp

# Oder direkt
python -m workstation_mcp.server
```

## Claude Desktop Konfiguration

Füge zu `~/.config/Claude/claude_desktop_config.json` hinzu:

### Variante 1: Mit Wrapper-Script (empfohlen)

```bash
chmod +x /pfad/zu/workstation_mcp/run.sh
```

```json
{
  "mcpServers": {
    "workstation": {
      "command": "/pfad/zu/workstation_mcp/run.sh"
    }
  }
}
```

### Variante 2: Direkter Python-Aufruf

```json
{
  "mcpServers": {
    "workstation": {
      "command": "/pfad/zu/workstation_mcp/.venv/bin/python",
      "args": ["-m", "workstation_mcp.server"]
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
cd /home/ulrich/projekte/stocktracker
```

### Erkenntnisse speichern

```
# Verschiedene Kategorien
memory_add("Bug in calculate_returns() gefunden: Division by Zero", category="note")
memory_add("SQLite statt PostgreSQL wegen Simplizität", category="decision")
memory_add("Performance bei >10k Datensätzen testen", category="todo")
memory_add("Wie verhält sich der Export bei Unicode?", category="question")
```

### Session beenden

```
session_save(summary="Excel-Export implementiert. Tests fehlen noch.")
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

Sessions und Gedächtnis werden automatisch gespeichert unter:

```
~/.mcp_shell_tools/
└── sessions/
    └── stocktracker/
        ├── session.json    # Strukturierte Daten
        └── memory.md       # Menschenlesbares Format
```

### memory.md Beispiel

```markdown
# Session Memory: stocktracker

**Projekt:** `/home/ulrich/projekte/stocktracker`
**Aktualisiert:** 2025-01-15 16:30

## Zusammenfassung
Excel-Export implementiert. Tests fehlen noch.

## ✅ Entscheidungen
- [01-15 14:30] SQLite statt PostgreSQL wegen einfacherem Deployment

## 📝 Erkenntnisse
- [01-15 15:45] Bug in calculate_returns() - Division by Zero bei leeren Portfolios

## 📋 Nächste Schritte
- [ ] Unit Tests für Excel-Export
- [ ] Error Handling verbessern

## Letzte Aktionen
- `16:25:03` ✓ **str_replace** ✓ src/export.py
- `16:28:41` ✓ **shell_exec** pytest tests/
```

## CLAUDE.md

Erstelle eine `CLAUDE.md` im Projektverzeichnis für automatischen Kontext:

```markdown
# Projekt: Stocktracker

## Tech Stack
- Python 3.11
- SQLite + SQLAlchemy
- pytest

## Konventionen
- Black für Formatting
- Type Hints überall
- Docstrings im Google-Style

## Aktuelle Aufgabe
Excel-Export für Portfolio-Daten implementieren
```

Diese wird automatisch geladen wenn du mit `cd` ins Verzeichnis wechselst.

## Projektstruktur

```
workstation_mcp/
├── pyproject.toml
├── requirements.txt
├── run.sh
├── README.md
├── .gitignore
└── src/workstation_mcp/
    ├── __init__.py
    ├── server.py           # Entry Point
    ├── config.py           # Konstanten
    ├── state.py            # WorkstationState
    ├── tools/
    │   ├── filesystem.py   # file_read, file_write, file_list, glob_search
    │   ├── editor.py       # str_replace, diff_preview
    │   ├── search.py       # grep
    │   ├── shell.py        # shell_exec
    │   ├── project.py      # cd, cwd, project_init
    │   ├── memory.py       # memory_add, memory_show, memory_clear
    │   └── session.py      # session_save, session_resume, session_list
    ├── persistence/
    │   ├── models.py       # SessionData, MemoryEntry
    │   └── session_manager.py
    └── utils/
        ├── output.py       # Formatierung
        └── paths.py        # Pfad-Utilities
```

## Lizenz

MIT License - siehe [LICENSE](LICENSE)

## Acknowledgements

Dieses Projekt wurde mit Unterstützung von [Claude](https://claude.ai) (Anthropic) entwickelt.
Claude hat bei Architektur, Code-Review und Dokumentation geholfen – quasi der erste Betatester seines eigenen MCP-Servers. 🤖
