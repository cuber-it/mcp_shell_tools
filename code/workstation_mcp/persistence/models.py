"""Datenmodelle für Persistenz."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MemoryEntry(BaseModel):
    """Ein einzelner Eintrag im Gedächtnis."""
    timestamp: datetime = Field(default_factory=datetime.now)
    category: str = Field(default="note", description="note|decision|question|todo")
    content: str
    

class ToolCall(BaseModel):
    """Log eines Tool-Aufrufs."""
    timestamp: datetime = Field(default_factory=datetime.now)
    tool: str
    params: dict
    result_summary: str = ""
    success: bool = True


class SessionData(BaseModel):
    """Kompletter Session-State."""
    project_path: str
    project_name: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    working_dir: str
    
    # Gedächtnis
    memories: list[MemoryEntry] = Field(default_factory=list)
    
    # Tool-Log (letzte N Einträge)
    tool_log: list[ToolCall] = Field(default_factory=list)
    
    # Kontext aus CLAUDE.md
    project_context: Optional[str] = None
    
    # Zusammenfassung beim Speichern
    summary: str = ""
    
    def add_memory(self, content: str, category: str = "note") -> None:
        """Fügt einen Memory-Eintrag hinzu."""
        self.memories.append(MemoryEntry(content=content, category=category))
        self.updated_at = datetime.now()
    
    def log_tool_call(self, tool: str, params: dict, result_summary: str = "", success: bool = True) -> None:
        """Loggt einen Tool-Aufruf."""
        self.tool_log.append(ToolCall(
            tool=tool,
            params=params,
            result_summary=result_summary,
            success=success
        ))
        # Nur letzte 100 Einträge behalten
        if len(self.tool_log) > 100:
            self.tool_log = self.tool_log[-100:]
        self.updated_at = datetime.now()
