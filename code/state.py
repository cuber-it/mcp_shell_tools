"""Globaler Zustand für mcp_shell_tools."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from code.config import INITIAL_WORKING_DIR, PROJECT_FILE


@dataclass
class WorkstationState:
    """Hält den Zustand zwischen Tool-Aufrufen."""
    
    working_dir: Path = field(default_factory=lambda: INITIAL_WORKING_DIR)
    project_context: Optional[str] = None
    
    def change_directory(self, new_path: Path) -> None:
        """Wechselt das Working Directory und lädt ggf. CLAUDE.md."""
        self.working_dir = new_path
        self._load_project_context()
    
    def _load_project_context(self) -> None:
        """Lädt CLAUDE.md falls vorhanden."""
        project_file = self.working_dir / PROJECT_FILE
        if project_file.exists() and project_file.is_file():
            try:
                self.project_context = project_file.read_text(encoding="utf-8")
            except Exception:
                self.project_context = None
        else:
            self.project_context = None
    
    def resolve_path(self, path: str) -> Path:
        """Löst einen Pfad relativ zum Working Directory auf."""
        p = Path(path)
        if p.is_absolute():
            return p.resolve()
        return (self.working_dir / p).resolve()


# Globale Instanz
state = WorkstationState()
