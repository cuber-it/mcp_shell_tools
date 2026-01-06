"""Tests für persistence/."""

import json
import pytest
from pathlib import Path

from code.persistence.models import (
    MemoryEntry,
    ToolCall,
    SessionData,
)
from code.persistence.session_manager import SessionManager


class TestMemoryEntry:
    """Tests für MemoryEntry Model."""
    
    def test_create_note(self):
        """Erstellt eine Notiz."""
        entry = MemoryEntry(content="Test note", category="note")
        
        assert entry.content == "Test note"
        assert entry.category == "note"
        assert entry.timestamp is not None
    
    def test_create_decision(self):
        """Erstellt eine Entscheidung."""
        entry = MemoryEntry(content="Use SQLite", category="decision")
        
        assert entry.category == "decision"


class TestSessionData:
    """Tests für SessionData Model."""
    
    def test_create_session(self):
        """Erstellt eine neue Session."""
        session = SessionData(
            project_path="/home/test/project",
            project_name="testproject",
            working_dir="/home/test/project"
        )
        
        assert session.project_name == "testproject"
        assert session.memories == []
        assert session.tool_log == []
    
    def test_add_memory(self):
        """Fügt Memory-Eintrag hinzu."""
        session = SessionData(
            project_path="/test",
            project_name="test",
            working_dir="/test"
        )
        
        session.add_memory("Important finding", category="note")
        
        assert len(session.memories) == 1
        assert session.memories[0].content == "Important finding"
    
    def test_log_tool_call(self):
        """Loggt Tool-Aufruf."""
        session = SessionData(
            project_path="/test",
            project_name="test",
            working_dir="/test"
        )
        
        session.log_tool_call(
            tool="file_read",
            params={"path": "test.py"},
            result_summary="OK",
            success=True
        )
        
        assert len(session.tool_log) == 1
        assert session.tool_log[0].tool == "file_read"
    
    def test_tool_log_limit(self):
        """Begrenzt Tool-Log auf 100 Einträge."""
        session = SessionData(
            project_path="/test",
            project_name="test",
            working_dir="/test"
        )
        
        for i in range(150):
            session.log_tool_call(
                tool=f"tool_{i}",
                params={},
                result_summary="",
                success=True
            )
        
        assert len(session.tool_log) == 100
        # Sollte die neuesten behalten
        assert session.tool_log[-1].tool == "tool_149"


class TestSessionManager:
    """Tests für SessionManager."""
    
    @pytest.fixture
    def manager(self, temp_dir):
        """Erstellt SessionManager mit temp Verzeichnis."""
        return SessionManager(base_dir=temp_dir)
    
    def test_init_session(self, manager, temp_dir):
        """Initialisiert neue Session."""
        project_path = temp_dir / "myproject"
        project_path.mkdir()
        
        session = manager.init_session(project_path)
        
        assert session.project_name == "myproject"
        assert manager.current_session is not None
    
    def test_save_and_load_session(self, manager, temp_dir):
        """Speichert und lädt Session."""
        project_path = temp_dir / "myproject"
        project_path.mkdir()
        
        # Session erstellen und speichern
        manager.init_session(project_path)
        manager.add_memory("Test memory", category="note")
        manager.save_session(summary="Test summary")
        
        # Prüfen, dass Dateien existieren
        session_file = manager._session_file("myproject")
        memory_file = manager._memory_file("myproject")
        
        assert session_file.exists()
        assert memory_file.exists()
        
        # Neu laden
        loaded = manager.load_session("myproject")
        
        assert loaded is not None
        assert loaded.summary == "Test summary"
        assert len(loaded.memories) == 1
    
    def test_list_sessions(self, manager, temp_dir):
        """Listet alle Sessions."""
        # Mehrere Sessions erstellen
        for name in ["project_a", "project_b"]:
            path = temp_dir / name
            path.mkdir()
            manager.init_session(path)
            manager.save_session()
        
        sessions = manager.list_sessions()
        
        assert len(sessions) == 2
        names = [s["name"] for s in sessions]
        assert "project_a" in names
        assert "project_b" in names
    
    def test_memory_markdown_format(self, manager, temp_dir):
        """Prüft Markdown-Ausgabe."""
        project_path = temp_dir / "mdtest"
        project_path.mkdir()
        
        manager.init_session(project_path)
        manager.add_memory("A decision", category="decision")
        manager.add_memory("A todo item", category="todo")
        manager.save_session(summary="Test session")
        
        memory_file = manager._memory_file("mdtest")
        content = memory_file.read_text()
        
        assert "# Session Memory: mdtest" in content
        assert "## Zusammenfassung" in content
        assert "## Entscheidungen" in content
        assert "## Nächste Schritte" in content
        assert "- [ ] A todo item" in content  # Checkbox für TODOs
