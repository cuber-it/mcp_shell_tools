# workstation_mcp - Architektur

## Übersicht

**workstation_mcp** ist ein MCP-Server (Model Context Protocol), der Claude Desktop lokalen Zugriff auf das Entwicklungssystem ermöglicht. Er bietet Dateisystem-Operationen, Shell-Zugriff, präzises Code-Editing und persistentes Session-Management.

```
┌─────────────────────────────────────────────────────────────────┐
│                       Claude Desktop                             │
│                           (Client)                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                    JSON-RPC über stdio
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     workstation_mcp                              │
│                        (FastMCP)                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    server.py                              │   │
│  │           Tool-Registrierung + Auto-Logging               │   │
│  └──────────────────────────────────────────────────────────┘   │
│           │              │              │              │         │
│           ▼              ▼              ▼              ▼         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐   │
│  │   tools/   │  │   state    │  │   config   │  │persistence│  │
│  │  (7 Module)│  │            │  │            │  │           │  │
│  └────────────┘  └────────────┘  └────────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Lokales Dateisystem                           │
│              ~/.workstation_mcp/sessions/                        │
└─────────────────────────────────────────────────────────────────┘
```

## Projektstruktur

```
workstation_mcp/
├── pyproject.toml              # Package-Definition, Dependencies
├── requirements.txt            # Direkte Dependencies
├── run.sh                      # Startskript für Claude Desktop
├── README.md                   # Benutzer-Dokumentation
│
└── src/workstation_mcp/
    ├── __init__.py
    ├── server.py               # Haupt-Entry-Point, Tool-Registrierung
    ├── config.py               # Konstanten und Konfiguration
    ├── state.py                # Globaler Laufzeit-Zustand
    │
    ├── tools/                  # Tool-Implementierungen
    │   ├── filesystem.py       # file_read, file_write, file_list, glob_search
    │   ├── editor.py           # str_replace, diff_preview
    │   ├── search.py           # grep
    │   ├── shell.py            # shell_exec
    │   ├── project.py          # cd, cwd, project_init
    │   ├── memory.py           # memory_add, memory_show, memory_clear
    │   └── session.py          # session_save, session_resume, session_list
    │
    ├── persistence/            # Daten-Persistenz
    │   ├── models.py           # Pydantic-Modelle (SessionData, MemoryEntry, ToolCall)
    │   └── session_manager.py  # Session-Speicherung und -Laden
    │
    └── utils/                  # Hilfsfunktionen (optional)
```

## Komponenten

### 1. Server (`server.py`)

Der zentrale Entry-Point, basierend auf **FastMCP**:

- **Tool-Registrierung**: Alle Tools werden mit Metadaten (readOnlyHint, destructiveHint, etc.) registriert
- **Auto-Logging**: Wrapper-Decorator loggt jeden Tool-Aufruf automatisch zur Session
- **Instructions**: Workflow-Empfehlungen für Claude

```python
mcp = FastMCP("workstation_mcp", instructions="...")

register_tool("file_read", file_read, "Datei lesen")
register_tool("shell_exec", shell_exec, "Shell-Befehl", 
              read_only=False, destructive=True)
```

### 2. Zustandsverwaltung (`state.py`)

`WorkstationState` hält den Laufzeit-Zustand:

| Attribut | Typ | Beschreibung |
|----------|-----|-------------|
| `working_dir` | `Path` | Aktuelles Arbeitsverzeichnis |
| `project_context` | `Optional[str]` | Inhalt von CLAUDE.md |

Methoden:
- `change_directory()` - Wechselt Verzeichnis, lädt CLAUDE.md
- `resolve_path()` - Löst relative Pfade auf

### 3. Konfiguration (`config.py`)

| Konstante | Wert | Beschreibung |
|-----------|------|-------------|
| `SHELL_TIMEOUT_SECONDS` | 30 | Timeout für Shell-Befehle |
| `MAX_OUTPUT_BYTES` | 100.000 | Max. Output-Größe |
| `MAX_LINES_WITHOUT_RANGE` | 500 | Zeilenlimit bei file_read |
| `PROJECT_FILE` | "CLAUDE.md" | Projekt-Kontextdatei |
| `INITIAL_WORKING_DIR` | `Path.home()` | Start-Verzeichnis |

### 4. Tools (`tools/`)

#### Filesystem (`filesystem.py`)
| Tool | Funktion |
|------|----------|
| `file_read` | Datei lesen mit optionaler Zeilen-Range |
| `file_write` | Datei komplett schreiben |
| `file_list` | Verzeichnis auflisten |
| `glob_search` | Dateien nach Pattern suchen |

#### Editor (`editor.py`)
| Tool | Funktion |
|------|----------|
| `str_replace` | Präzises Ersetzen (muss exakt 1x vorkommen) |
| `diff_preview` | Unified Diff vor Änderung anzeigen |

#### Search (`search.py`)
| Tool | Funktion |
|------|----------|
| `grep` | Text/Regex-Suche in Dateien, rekursiv |

#### Shell (`shell.py`)
| Tool | Funktion |
|------|----------|
| `shell_exec` | Bash-Befehl ausführen mit Timeout |

#### Project (`project.py`)
| Tool | Funktion |
|------|----------|
| `cd` | Verzeichnis wechseln, Session initialisieren |
| `cwd` | Aktuelles Verzeichnis anzeigen |
| `project_init` | CLAUDE.md laden/erstellen |

#### Memory (`memory.py`)
| Tool | Funktion |
|------|----------|
| `memory_add` | Erkenntnis speichern (note/decision/question/todo) |
| `memory_show` | Alle Einträge anzeigen |
| `memory_clear` | Gedächtnis löschen |

#### Session (`session.py`)
| Tool | Funktion |
|------|----------|
| `session_save` | Session mit Zusammenfassung speichern |
| `session_resume` | Letzte oder benannte Session laden |
| `session_list` | Alle Sessions auflisten |

### 5. Persistenz (`persistence/`)

#### Datenmodelle (`models.py`)

```python
class MemoryEntry(BaseModel):
    timestamp: datetime
    category: str       # note | decision | question | todo
    content: str

class ToolCall(BaseModel):
    timestamp: datetime
    tool: str
    params: dict
    result_summary: str
    success: bool

class SessionData(BaseModel):
    project_path: str
    project_name: str
    created_at: datetime
    updated_at: datetime
    working_dir: str
    memories: list[MemoryEntry]
    tool_log: list[ToolCall]      # Max 100 Einträge
    project_context: Optional[str]
    summary: str
```

#### Session Manager (`session_manager.py`)

Verwaltet Session-Persistenz unter `~/.workstation_mcp/sessions/<projekt>/`:

```
~/.workstation_mcp/
└── sessions/
    └── workstation_mcp/           # Beispiel-Projekt
        ├── session.json           # Kompletter Zustand (JSON)
        └── memory.md              # Lesbare Markdown-Zusammenfassung
```

Kernfunktionen:
- `init_session()` - Neue Session oder bestehende laden
- `save_session()` - JSON + Markdown schreiben
- `load_session()` - Session aus Datei laden
- `list_sessions()` - Alle Sessions auflisten
- `add_memory()` - Eintrag hinzufügen und speichern
- `log_tool_call()` - Tool-Aufruf loggen (Auto-Save)

## Datenfluss

```
┌─────────────┐    Tool-Aufruf     ┌─────────────┐
│   Claude    │ ─────────────────▶ │   server    │
│   Desktop   │                    │   (FastMCP) │
└─────────────┘                    └──────┬──────┘
                                          │
                         ┌────────────────┼────────────────┐
                         ▼                ▼                ▼
                   ┌──────────┐    ┌──────────┐    ┌──────────┐
                   │  tools/  │    │  state   │    │persistence│
                   │filesystem│    │          │    │  manager  │
                   └────┬─────┘    └──────────┘    └─────┬────┘
                        │                                │
                        ▼                                ▼
                ┌───────────────┐              ┌─────────────────┐
                │  Dateisystem  │              │ ~/.workstation_ │
                │  (lokal)      │              │   mcp/sessions/ │
                └───────────────┘              └─────────────────┘
```

1. Claude Desktop sendet JSON-RPC-Request über stdio
2. FastMCP routet zum entsprechenden Tool
3. Auto-Log Wrapper protokolliert den Aufruf
4. Tool führt Operation aus (Filesystem, Shell, etc.)
5. Session Manager speichert automatisch (nach jedem Tool-Aufruf)
6. Ergebnis geht zurück an Claude

## Dependencies

| Package | Version | Zweck |
|---------|---------|-------|
| `mcp` | ≥1.0.0 | MCP Server Framework (FastMCP) |
| `pydantic` | ≥2.0.0 | Datenvalidierung und Serialisierung |

**Python-Version:** ≥3.10

## Konfiguration Claude Desktop

`~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "workstation": {
      "command": "/home/ucuber/Workspace/ucuber/workstation_mcp/run.sh"
    }
  }
}
```

## Erweiterungspunkte

1. **Neue Tools**: Modul in `tools/` anlegen, in `server.py` registrieren
2. **Neue Memory-Kategorien**: In `models.py` erweitern
3. **Alternative Persistenz**: `SessionManager` durch andere Implementierung ersetzen (z.B. SQLite)
4. **Zusätzliche Ressourcen**: MCP-Resources über `mcp.resource()` hinzufügen

## Logging

MCP-Logs werden von Claude Desktop unter `~/.config/Claude/logs/` gespeichert:
- `mcp.log` - Client-Server Kommunikation
- `mcp-server-workstation.log` - Server-Output
