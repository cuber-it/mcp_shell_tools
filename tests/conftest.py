"""Pytest Fixtures für workstation_mcp Tests."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Temporäres Verzeichnis für Tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_file(temp_dir):
    """Erstellt eine Beispieldatei."""
    filepath = temp_dir / "sample.py"
    filepath.write_text("""#!/usr/bin/env python3
\"\"\"Sample module.\"\"\" 

def hello():
    return "Hello, World!"

def add(a, b):
    return a + b

if __name__ == "__main__":
    print(hello())
""", encoding="utf-8")
    return filepath


@pytest.fixture
def sample_project(temp_dir):
    """Erstellt eine Beispiel-Projektstruktur."""
    # Verzeichnisse
    (temp_dir / "src").mkdir()
    (temp_dir / "tests").mkdir()
    
    # Dateien
    (temp_dir / "CLAUDE.md").write_text("""# Test Project

## Tech Stack
- Python 3.12
- pytest

## Konventionen
- Type Hints
""", encoding="utf-8")
    
    (temp_dir / "src" / "main.py").write_text("""def main():
    print("Hello")
""", encoding="utf-8")
    
    return temp_dir


@pytest.fixture
def reset_state():
    """Setzt den globalen State zurück."""
    from workstation_mcp.state import state
    from workstation_mcp.config import INITIAL_WORKING_DIR
    
    original_dir = state.working_dir
    original_context = state.project_context
    
    yield state
    
    # Wiederherstellen
    state.working_dir = original_dir
    state.project_context = original_context
