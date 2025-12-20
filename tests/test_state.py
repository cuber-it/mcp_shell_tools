"""Tests für state.py."""

import pytest
from pathlib import Path

from workstation_mcp.state import WorkstationState
from workstation_mcp.config import PROJECT_FILE


class TestWorkstationState:
    """Tests für WorkstationState."""
    
    def test_initial_state(self):
        """Prüft initialen Zustand."""
        state = WorkstationState()
        
        assert state.working_dir == Path.home()
        assert state.project_context is None
    
    def test_change_directory(self, temp_dir):
        """Verzeichniswechsel."""
        state = WorkstationState()
        state.change_directory(temp_dir)
        
        assert state.working_dir == temp_dir
    
    def test_load_claude_md(self, sample_project):
        """Lädt CLAUDE.md automatisch."""
        state = WorkstationState()
        state.change_directory(sample_project)
        
        assert state.project_context is not None
        assert "Test Project" in state.project_context
        assert "Python 3.12" in state.project_context
    
    def test_no_claude_md(self, temp_dir):
        """Kein Fehler ohne CLAUDE.md."""
        state = WorkstationState()
        state.change_directory(temp_dir)
        
        assert state.project_context is None
    
    def test_resolve_absolute_path(self, temp_dir):
        """Löst absoluten Pfad auf."""
        state = WorkstationState()
        state.working_dir = temp_dir
        
        resolved = state.resolve_path("/etc/passwd")
        assert resolved == Path("/etc/passwd")
    
    def test_resolve_relative_path(self, temp_dir):
        """Löst relativen Pfad auf."""
        state = WorkstationState()
        state.working_dir = temp_dir
        
        resolved = state.resolve_path("subdir/file.txt")
        assert resolved == (temp_dir / "subdir" / "file.txt").resolve()
    
    def test_resolve_parent_path(self, temp_dir):
        """Löst Pfad mit .. auf."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        
        state = WorkstationState()
        state.working_dir = subdir
        
        resolved = state.resolve_path("../file.txt")
        assert resolved == (temp_dir / "file.txt").resolve()
