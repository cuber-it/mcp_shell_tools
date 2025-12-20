"""Tests für tools/editor.py."""

import pytest

from workstation_mcp.tools.editor import (
    StrReplaceInput,
    DiffPreviewInput,
    str_replace,
    diff_preview,
)


class TestStrReplace:
    """Tests für str_replace."""
    
    @pytest.mark.asyncio
    async def test_simple_replace(self, sample_file):
        """Einfaches Ersetzen."""
        result = await str_replace(StrReplaceInput(
            path=str(sample_file),
            old_str='return "Hello, World!"',
            new_str='return "Hallo, Welt!"'
        ))
        
        assert "✓" in result or "Ersetzt" in result
        
        # Prüfen, dass Änderung durchgeführt wurde
        content = sample_file.read_text()
        assert 'return "Hallo, Welt!"' in content
        assert 'return "Hello, World!"' not in content
    
    @pytest.mark.asyncio
    async def test_replace_not_found(self, sample_file):
        """Fehler wenn Text nicht gefunden."""
        result = await str_replace(StrReplaceInput(
            path=str(sample_file),
            old_str="dieser text existiert nicht",
            new_str="egal"
        ))
        
        assert "nicht gefunden" in result.lower() or "fehler" in result.lower()
    
    @pytest.mark.asyncio
    async def test_replace_multiple_matches(self, temp_dir):
        """Fehler bei mehrfachem Vorkommen."""
        filepath = temp_dir / "duplicate.txt"
        filepath.write_text("foo\nbar\nfoo\n", encoding="utf-8")
        
        result = await str_replace(StrReplaceInput(
            path=str(filepath),
            old_str="foo",
            new_str="baz"
        ))
        
        # Sollte Fehler melden wegen Mehrdeutigkeit
        assert "2" in result or "mehrfach" in result.lower() or "eindeutig" in result.lower()
    
    @pytest.mark.asyncio
    async def test_delete_text(self, sample_file):
        """Löschen durch leeren Ersatz."""
        original = sample_file.read_text()
        
        await str_replace(StrReplaceInput(
            path=str(sample_file),
            old_str='if __name__ == "__main__":\n    print(hello())\n',
            new_str=''
        ))
        
        content = sample_file.read_text()
        assert '__main__' not in content


class TestDiffPreview:
    """Tests für diff_preview."""
    
    @pytest.mark.asyncio
    async def test_show_diff(self, sample_file):
        """Zeigt Unified Diff an."""
        result = await diff_preview(DiffPreviewInput(
            path=str(sample_file),
            old_str='return "Hello, World!"',
            new_str='return "Hallo, Welt!"'
        ))
        
        # Unified Diff Format
        assert "---" in result or "+++" in result or "-return" in result
    
    @pytest.mark.asyncio
    async def test_diff_not_found(self, sample_file):
        """Fehler wenn Text nicht gefunden."""
        result = await diff_preview(DiffPreviewInput(
            path=str(sample_file),
            old_str="nicht vorhanden",
            new_str="egal"
        ))
        
        assert "nicht gefunden" in result.lower() or "fehler" in result.lower()
