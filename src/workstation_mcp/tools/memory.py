"""Memory-Tools: Erkenntnisse speichern und abrufen."""

from typing import Literal

from pydantic import BaseModel, Field

from ..persistence import session_manager


# --- Input Models ---

class MemoryAddInput(BaseModel):
    """Input für memory_add."""
    content: str = Field(..., description="Die zu speichernde Erkenntnis, Entscheidung oder Notiz")
    category: Literal["note", "decision", "question", "todo"] = Field(
        default="note",
        description="Kategorie: note (Erkenntnis), decision (Entscheidung), question (Offene Frage), todo (Nächster Schritt)"
    )


# --- Tool Functions ---

async def memory_add(params: MemoryAddInput) -> str:
    """Speichert eine Erkenntnis, Entscheidung oder Notiz.
    
    Kategorien:
    - note: Allgemeine Erkenntnisse und Beobachtungen
    - decision: Getroffene Entscheidungen mit Begründung
    - question: Offene Fragen die noch zu klären sind
    - todo: Nächste Schritte und Aufgaben
    
    Beispiele:
    - memory_add("Bug gefunden: Division by Zero in calculate_returns()", category="note")
    - memory_add("SQLite statt PostgreSQL wegen einfacherem Deployment", category="decision")
    - memory_add("Performance bei >10k Datensätzen testen", category="todo")
    """
    if not session_manager.current_session:
        return "Fehler: Keine aktive Session. Nutze erst 'cd' um in ein Projektverzeichnis zu wechseln."
    
    success = session_manager.add_memory(params.content, params.category)
    
    if success:
        category_emoji = {
            "note": "📝",
            "decision": "✅", 
            "question": "❓",
            "todo": "📋"
        }
        emoji = category_emoji.get(params.category, "📝")
        return f"{emoji} Gespeichert ({params.category}): {params.content[:100]}{'...' if len(params.content) > 100 else ''}"
    else:
        return "Fehler beim Speichern."


async def memory_show() -> str:
    """Zeigt alle gespeicherten Erkenntnisse der aktuellen Session.
    
    Gruppiert nach Kategorie: Entscheidungen, Erkenntnisse, Offene Fragen, Nächste Schritte.
    """
    if not session_manager.current_session:
        return "Keine aktive Session. Nutze 'cd' oder 'session_resume'."
    
    session = session_manager.current_session
    
    if not session.memories:
        return f"Keine Einträge im Gedächtnis für '{session.project_name}'."
    
    # Nach Kategorie gruppieren
    categories = {
        "decision": ("✅ Entscheidungen", []),
        "note": ("📝 Erkenntnisse", []),
        "question": ("❓ Offene Fragen", []),
        "todo": ("📋 Nächste Schritte", []),
    }
    
    for mem in session.memories:
        cat = mem.category if mem.category in categories else "note"
        categories[cat][1].append(mem)
    
    lines = [f"# Gedächtnis: {session.project_name}\n"]
    
    for cat_key, (cat_name, entries) in categories.items():
        if entries:
            lines.append(f"\n## {cat_name}\n")
            for entry in entries:
                timestamp = entry.timestamp.strftime("%m-%d %H:%M")
                if cat_key == "todo":
                    lines.append(f"- [ ] {entry.content}")
                else:
                    lines.append(f"- [{timestamp}] {entry.content}")
    
    return "\n".join(lines)


async def memory_clear() -> str:
    """Löscht alle Einträge aus dem Gedächtnis der aktuellen Session.
    
    Achtung: Diese Aktion kann nicht rückgängig gemacht werden.
    """
    if not session_manager.current_session:
        return "Keine aktive Session."
    
    count = len(session_manager.current_session.memories)
    
    if count == 0:
        return "Gedächtnis ist bereits leer."
    
    success = session_manager.clear_memories()
    
    if success:
        return f"🗑️ {count} Einträge gelöscht."
    else:
        return "Fehler beim Löschen."
