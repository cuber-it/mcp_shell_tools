"""Session-Management: Speichern, Laden, Auflisten."""

import json
import fcntl
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from code.persistence.models import SessionData, MemoryEntry

# Minimaler Abstand zwischen Auto-Saves in Sekunden
AUTO_SAVE_THROTTLE_SECONDS = 5


class SessionManager:
    """Verwaltet Session-Persistenz.

    Sessions werden unter ~/.workstation_mcp/sessions/<projekt>/ gespeichert.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path.home() / ".workstation_mcp"
        self.sessions_dir = self.base_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

        self.current_session: Optional[SessionData] = None
        self.current_project: Optional[str] = None
        self._last_save: Optional[datetime] = None
    
    def _project_dir(self, project_name: str) -> Path:
        """Gibt das Verzeichnis für ein Projekt zurück."""
        # Sanitize project name für Dateisystem
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in project_name)
        return self.sessions_dir / safe_name
    
    def _session_file(self, project_name: str) -> Path:
        """Pfad zur session.json."""
        return self._project_dir(project_name) / "session.json"
    
    def _memory_file(self, project_name: str) -> Path:
        """Pfad zur memory.md."""
        return self._project_dir(project_name) / "memory.md"
    
    def init_session(self, project_path: Path, project_name: Optional[str] = None) -> SessionData:
        """Initialisiert eine neue Session oder lädt eine bestehende."""
        name = project_name or project_path.name
        self.current_project = name
        
        # Bestehende Session laden falls vorhanden
        existing = self.load_session(name)
        if existing:
            existing.working_dir = str(project_path)
            existing.updated_at = datetime.now()
            self.current_session = existing
            return existing
        
        # Neue Session erstellen
        self.current_session = SessionData(
            project_path=str(project_path),
            project_name=name,
            working_dir=str(project_path),
        )
        return self.current_session
    
    def load_session(self, project_name: str) -> Optional[SessionData]:
        """Lädt eine Session aus der Datei."""
        session_file = self._session_file(project_name)
        
        if not session_file.exists():
            return None
        
        try:
            data = json.loads(session_file.read_text(encoding="utf-8"))
            return SessionData.model_validate(data)
        except Exception:
            return None
    
    def save_session(self, summary: str = "", force: bool = False) -> bool:
        """Speichert die aktuelle Session.

        Args:
            summary: Optionale Zusammenfassung
            force: True = immer speichern, False = Throttling beachten
        """
        if not self.current_session or not self.current_project:
            return False

        if summary:
            self.current_session.summary = summary

        self.current_session.updated_at = datetime.now()

        project_dir = self._project_dir(self.current_project)
        project_dir.mkdir(parents=True, exist_ok=True)

        # JSON speichern mit File-Locking
        session_file = self._session_file(self.current_project)
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                # Exclusive Lock für Schreibzugriff
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    f.write(self.current_session.model_dump_json(indent=2))
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            self._last_save = datetime.now()
        except Exception as e:
            print(f"Session-Speicherfehler: {e}", file=sys.stderr)
            return False

        # Markdown generieren
        self._write_memory_markdown()

        return True
    
    def _write_memory_markdown(self) -> None:
        """Schreibt memory.md im Markdown-Format."""
        if not self.current_session or not self.current_project:
            return
        
        session = self.current_session
        lines = [
            f"# Session Memory: {session.project_name}",
            "",
            f"**Projekt:** `{session.project_path}`  ",
            f"**Erstellt:** {session.created_at.strftime('%Y-%m-%d %H:%M')}  ",
            f"**Aktualisiert:** {session.updated_at.strftime('%Y-%m-%d %H:%M')}",
            "",
        ]
        
        if session.summary:
            lines.extend([
                "## Zusammenfassung",
                "",
                session.summary,
                "",
            ])
        
        # Memories nach Kategorie gruppieren
        categories = {
            "decision": ("Entscheidungen", []),
            "note": ("Erkenntnisse", []),
            "question": ("Offene Fragen", []),
            "todo": ("Nächste Schritte", []),
        }
        
        for mem in session.memories:
            cat = mem.category if mem.category in categories else "note"
            categories[cat][1].append(mem)
        
        for cat_key, (cat_name, entries) in categories.items():
            if entries:
                lines.extend([f"## {cat_name}", ""])
                for entry in entries:
                    timestamp = entry.timestamp.strftime("%Y-%m-%d %H:%M")
                    if cat_key == "todo":
                        lines.append(f"- [ ] {entry.content}")
                    else:
                        lines.append(f"- **{timestamp}:** {entry.content}")
                lines.append("")
        
        # Letzte Tool-Aufrufe
        if session.tool_log:
            lines.extend(["## Letzte Aktionen", ""])
            for call in session.tool_log[-10:]:
                timestamp = call.timestamp.strftime("%H:%M:%S")
                status = "✓" if call.success else "✗"
                lines.append(f"- `{timestamp}` {status} **{call.tool}** {call.result_summary[:50]}")
            lines.append("")
        
        memory_file = self._memory_file(self.current_project)
        memory_file.write_text("\n".join(lines), encoding="utf-8")
    
    def list_sessions(self) -> list[dict]:
        """Listet alle verfügbaren Sessions."""
        sessions = []
        
        for project_dir in self.sessions_dir.iterdir():
            if not project_dir.is_dir():
                continue
            
            session_file = project_dir / "session.json"
            if session_file.exists():
                try:
                    data = json.loads(session_file.read_text(encoding="utf-8"))
                    sessions.append({
                        "name": data.get("project_name", project_dir.name),
                        "path": data.get("project_path", ""),
                        "updated": data.get("updated_at", ""),
                        "summary": data.get("summary", "")[:100],
                        "memories": len(data.get("memories", [])),
                    })
                except Exception:
                    continue
        
        # Nach Aktualisierungsdatum sortieren
        sessions.sort(key=lambda x: x["updated"], reverse=True)
        return sessions
    
    def add_memory(self, content: str, category: str = "note") -> bool:
        """Fügt einen Memory-Eintrag hinzu und speichert."""
        if not self.current_session:
            return False
        
        self.current_session.add_memory(content, category)
        return self.save_session()
    
    def log_tool_call(self, tool: str, params: dict, result_summary: str = "", success: bool = True) -> None:
        """Loggt einen Tool-Aufruf."""
        if self.current_session:
            self.current_session.log_tool_call(tool, params, result_summary, success)
            # Auto-Save mit Throttling (nicht bei jedem Aufruf)
            if self._should_auto_save():
                self.save_session()

    def _should_auto_save(self) -> bool:
        """Prüft ob Auto-Save durchgeführt werden soll (Throttling)."""
        if self._last_save is None:
            return True
        elapsed = (datetime.now() - self._last_save).total_seconds()
        return elapsed >= AUTO_SAVE_THROTTLE_SECONDS
    
    def clear_memories(self) -> bool:
        """Löscht alle Memory-Einträge."""
        if not self.current_session:
            return False
        
        self.current_session.memories = []
        return self.save_session()


# Globale Instanz
session_manager = SessionManager()
