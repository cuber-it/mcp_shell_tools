"""Session-Tools: Speichern, Laden, Auflisten von Sessions."""

from typing import Optional

from pydantic import BaseModel, Field

from ..persistence import session_manager
from ..state import state


# --- Input Models ---

class SessionSaveInput(BaseModel):
    """Input für session_save."""
    summary: str = Field(
        default="",
        description="Zusammenfassung des aktuellen Stands (was wurde erreicht, was steht an)"
    )


class SessionResumeInput(BaseModel):
    """Input für session_resume."""
    project_name: Optional[str] = Field(
        default=None,
        description="Name des Projekts. Ohne Angabe: letzte Session."
    )


# --- Tool Functions ---

async def session_save(params: SessionSaveInput) -> str:
    """Speichert die aktuelle Session explizit mit optionaler Zusammenfassung.
    
    Die Session wird auch automatisch nach jedem Tool-Aufruf gespeichert.
    Nutze dieses Tool um eine explizite Zusammenfassung hinzuzufügen,
    z.B. am Ende einer Arbeitssitzung.
    
    Beispiel:
    session_save(summary="Excel-Export implementiert. Tests fehlen noch. Bug in Zeile 45 gefunden.")
    """
    if not session_manager.current_session:
        return "Keine aktive Session. Nutze 'cd' um in ein Projektverzeichnis zu wechseln."
    
    success = session_manager.save_session(params.summary)
    
    if success:
        session = session_manager.current_session
        path = session_manager._session_file(session_manager.current_project)
        memory_path = session_manager._memory_file(session_manager.current_project)
        
        result = f"💾 Session gespeichert: {session.project_name}\n"
        result += f"   📁 {path}\n"
        result += f"   📄 {memory_path}\n"
        result += f"   📝 {len(session.memories)} Gedächtnis-Einträge\n"
        result += f"   📋 {len(session.tool_log)} Tool-Aufrufe geloggt"
        
        if params.summary:
            result += f"\n\n**Zusammenfassung:**\n{params.summary}"
        
        return result
    else:
        return "Fehler beim Speichern der Session."


async def session_resume(params: SessionResumeInput) -> str:
    """Lädt eine frühere Session und stellt den Kontext wieder her.
    
    Ohne Angabe eines Projektnamens wird die zuletzt aktualisierte Session geladen.
    Zeigt die gespeicherten Erkenntnisse und die letzte Zusammenfassung.
    """
    sessions = session_manager.list_sessions()
    
    if not sessions:
        return "Keine gespeicherten Sessions gefunden."
    
    # Projekt auswählen
    if params.project_name:
        target = next((s for s in sessions if s["name"] == params.project_name), None)
        if not target:
            available = ", ".join(s["name"] for s in sessions[:5])
            return f"Session '{params.project_name}' nicht gefunden.\nVerfügbar: {available}"
    else:
        target = sessions[0]  # Neueste
    
    # Session laden
    session_data = session_manager.load_session(target["name"])
    if not session_data:
        return f"Fehler beim Laden der Session '{target['name']}'."
    
    # State aktualisieren
    from pathlib import Path
    project_path = Path(session_data.project_path)
    
    if project_path.exists():
        state.change_directory(project_path)
        session_manager.current_session = session_data
        session_manager.current_project = target["name"]
    else:
        return f"Projektverzeichnis existiert nicht mehr: {project_path}"
    
    # Ausgabe formatieren
    lines = [
        f"# Session wiederhergestellt: {session_data.project_name}",
        "",
        f"📁 **Verzeichnis:** `{session_data.project_path}`",
        f"📅 **Letzte Aktualisierung:** {session_data.updated_at.strftime('%Y-%m-%d %H:%M')}",
        "",
    ]
    
    if session_data.summary:
        lines.extend([
            "## Letzte Zusammenfassung",
            "",
            session_data.summary,
            "",
        ])
    
    if session_data.memories:
        lines.extend([
            f"## Gedächtnis ({len(session_data.memories)} Einträge)",
            "",
        ])
        
        # Letzte 5 Einträge zeigen
        for mem in session_data.memories[-5:]:
            timestamp = mem.timestamp.strftime("%m-%d %H:%M")
            emoji = {"decision": "✅", "note": "📝", "question": "❓", "todo": "📋"}.get(mem.category, "📝")
            lines.append(f"- {emoji} [{timestamp}] {mem.content[:80]}{'...' if len(mem.content) > 80 else ''}")
        
        if len(session_data.memories) > 5:
            lines.append(f"- ... und {len(session_data.memories) - 5} weitere (nutze 'memory_show' für alle)")
    
    if session_data.project_context:
        lines.extend([
            "",
            "## CLAUDE.md",
            "",
            session_data.project_context[:500] + ("..." if len(session_data.project_context) > 500 else ""),
        ])
    
    return "\n".join(lines)


async def session_list() -> str:
    """Listet alle verfügbaren Sessions auf.
    
    Zeigt Projektname, letztes Update und Zusammenfassung.
    """
    sessions = session_manager.list_sessions()
    
    if not sessions:
        return "Keine gespeicherten Sessions gefunden."
    
    lines = ["# Verfügbare Sessions\n"]
    
    for i, s in enumerate(sessions, 1):
        updated = s["updated"][:16] if s["updated"] else "?"
        lines.append(f"{i}. **{s['name']}**")
        lines.append(f"   📁 `{s['path']}`")
        lines.append(f"   📅 {updated} | 📝 {s['memories']} Einträge")
        if s["summary"]:
            lines.append(f"   💬 _{s['summary']}_")
        lines.append("")
    
    lines.append("Nutze `session_resume(project_name='...')` zum Laden.")
    
    return "\n".join(lines)
