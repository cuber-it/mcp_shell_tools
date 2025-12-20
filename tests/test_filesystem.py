"""Tests für tools/filesystem.py."""

import pytest

from workstation_mcp.tools.filesystem import (
    FileReadInput,
    FileWriteInput,
    FileListInput,
    GlobSearchInput,
    file_read,
    file_write,
    file_list,
    glob_search,
)


class TestFileRead:
    """Tests für file_read."""
    
    @pytest.mark.asyncio
    async def test_read_existing_file(self, sample_file):
        """Liest eine existierende Datei."""
        result = await file_read(FileReadInput(path=str(sample_file)))
        
        assert "def hello():" in result
        assert "def add(a, b):" in result
        # Zeilennummern sollten enthalten sein
        assert "1 \u2502" in result or "1\u2502" in result
    
    @pytest.mark.asyncio
    async def test_read_with_range(self, sample_file):
        """Liest nur bestimmte Zeilen."""
        result = await file_read(FileReadInput(
            path=str(sample_file),
            start_line=4,
            end_line=5
        ))
        
        assert "def hello():" in result
        assert "def add" not in result
    
    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, temp_dir):
        """Fehler bei nicht-existierender Datei."""
        result = await file_read(FileReadInput(
            path=str(temp_dir / "nonexistent.txt")
        ))
        
        assert "Fehler" in result or "existiert nicht" in result.lower()


class TestFileWrite:
    """Tests für file_write."""
    
    @pytest.mark.asyncio
    async def test_write_new_file(self, temp_dir):
        """Schreibt eine neue Datei."""
        filepath = temp_dir / "new_file.txt"
        content = "Hello, World!\nLine 2"
        
        result = await file_write(FileWriteInput(
            path=str(filepath),
            content=content
        ))
        
        assert filepath.exists()
        assert filepath.read_text() == content
        assert "Geschrieben" in result
    
    @pytest.mark.asyncio
    async def test_write_creates_directories(self, temp_dir):
        """Erstellt fehlende Verzeichnisse."""
        filepath = temp_dir / "subdir" / "deep" / "file.txt"
        
        await file_write(FileWriteInput(
            path=str(filepath),
            content="test"
        ))
        
        assert filepath.exists()


class TestFileList:
    """Tests für file_list."""
    
    @pytest.mark.asyncio
    async def test_list_directory(self, sample_project):
        """Listet Verzeichnisinhalt auf."""
        result = await file_list(FileListInput(path=str(sample_project)))
        
        assert "src" in result
        assert "tests" in result
        assert "CLAUDE.md" in result
    
    @pytest.mark.asyncio
    async def test_list_recursive(self, sample_project):
        """Rekursive Auflistung."""
        result = await file_list(FileListInput(
            path=str(sample_project),
            recursive=True
        ))
        
        assert "main.py" in result


class TestGlobSearch:
    """Tests für glob_search."""
    
    @pytest.mark.asyncio
    async def test_glob_pattern(self, sample_project):
        """Sucht mit Glob-Pattern."""
        result = await glob_search(GlobSearchInput(
            path=str(sample_project),
            pattern="**/*.py"
        ))
        
        assert "main.py" in result
    
    @pytest.mark.asyncio
    async def test_glob_md_files(self, sample_project):
        """Sucht Markdown-Dateien."""
        result = await glob_search(GlobSearchInput(
            path=str(sample_project),
            pattern="*.md"
        ))
        
        assert "CLAUDE.md" in result
