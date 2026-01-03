"""Project-Tools: Verzeichniswechsel und Projekt-Kontext."""

from typing import Annotated

from pydantic import Field

from ..config import PROJECT_FILE
from ..state import state
from ..persistence import session_manager


# --- Tool Functions ---

async def cwd() -> str:
    """Zeigt das aktuelle Working Directory und ggf. geladenen Projekt-Kontext."""
    result = f"📁 Working Directory: {state.working_dir}"
    
    if state.project_context:
        result += f"\n\n📋 {PROJECT_FILE} geladen ({len(state.project_context)} Zeichen)"
    
    # Session-Info hinzufügen
    if session_manager.current_session:
        session = session_manager.current_session
        result += f"\n\n💾 Session: {session.project_name} ({len(session.memories)} Einträge)"
    
    return result


async def cd(
    path: Annotated[str, Field(description="Neues Working Directory")],
) -> str:
    """Wechselt das Working Directory.
    
    Lädt automatisch CLAUDE.md falls im Zielverzeichnis vorhanden.
    Initialisiert oder lädt eine Session für das Projekt.
    """
    new_path = state.resolve_path(path)
    
    if not new_path.exists():
        return f"Fehler: Verzeichnis existiert nicht: {new_path}"
    
    if not new_path.is_dir():
        return f"Fehler: Kein Verzeichnis: {new_path}"
    
    state.change_directory(new_path)
    
    # Session initialisieren/laden
    session = session_manager.init_session(new_path)
    if state.project_context:
        session.project_context = state.project_context
    
    result = f"📁 {state.working_dir}"
    
    # Session-Info
    if session.memories:
        result += f"\n\n💾 Session geladen: {len(session.memories)} Gedächtnis-Einträge"
        if session.summary:
            result += f"\n📝 Letzte Zusammenfassung: _{session.summary[:100]}{'...' if len(session.summary) > 100 else ''}_"
    else:
        result += "\n\n💾 Neue Session gestartet"
    
    if state.project_context:
        result += f"\n\n📋 {PROJECT_FILE} gefunden:\n\n{state.project_context}"
    
    return result


async def project_init(
    path: Annotated[str, Field(description="Projektverzeichnis")] = ".",
) -> str:
    """Initialisiert Projekt-Kontext aus CLAUDE.md.
    
    Liest CLAUDE.md aus dem angegebenen Verzeichnis und gibt
    den Inhalt zurück. Nützlich um Kontext über ein Projekt zu laden.
    
    Falls kein CLAUDE.md existiert, wird eine Vorlage vorgeschlagen.
    """
    resolved = state.resolve_path(path)
    
    if not resolved.exists():
        return f"Fehler: Verzeichnis existiert nicht: {resolved}"
    
    if not resolved.is_dir():
        return f"Fehler: Kein Verzeichnis: {resolved}"
    
    project_file = resolved / PROJECT_FILE
    
    if project_file.exists():
        try:
            content = project_file.read_text(encoding="utf-8")
            state.project_context = content
            return f"📋 {PROJECT_FILE} aus {resolved}:\n\n{content}"
        except Exception as e:
            return f"Fehler beim Lesen von {PROJECT_FILE}: {e}"
    else:
        template = f"""# Projekt: [Name]

## Übersicht
[Kurze Beschreibung]

## Tech Stack
- Sprache: 
- Framework: 
- Datenbank: 

## Konventionen
- Code-Style: 
- Tests: 

## Aktuelle Aufgabe
[Was gerade ansteht]

## Notizen
[Sonstiges]
"""
        return f"""Keine {PROJECT_FILE} in {resolved} gefunden.

Erstelle eine mit folgendem Template:

```markdown
{template}
```

Nutze: file_write(path="{resolved / PROJECT_FILE}", content="...")
"""
