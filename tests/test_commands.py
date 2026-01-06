"""Tests für tools/commands.py."""

import pytest
from pathlib import Path

from code.tools.commands import command, settings, CommandSettings


class TestCommandSettings:
    """Tests für CommandSettings."""

    def test_initial_state(self):
        """Initiale Einstellungen."""
        s = CommandSettings()
        assert s.verbose is False
        assert s.log_enabled is False
        assert s.log_file is None

    def test_set_verbose(self):
        """Verbose ein/aus."""
        s = CommandSettings()

        result = s.set_verbose(True)
        assert s.verbose is True
        assert "ON" in result

        result = s.set_verbose(False)
        assert s.verbose is False
        assert "OFF" in result

    def test_set_logging(self, temp_dir):
        """Logging ein/aus."""
        s = CommandSettings()

        log_file = temp_dir / "test.log"
        result = s.set_logging(True, str(log_file))

        assert s.log_enabled is True
        assert s.log_file == log_file
        assert "ON" in result

        result = s.set_logging(False)
        assert s.log_enabled is False
        assert "OFF" in result


class TestCommand:
    """Tests für command Tool."""

    @pytest.mark.asyncio
    async def test_verbose_on(self):
        """Verbose aktivieren."""
        result = await command(cmd="verbose", arg="on")
        assert "ON" in result
        assert settings.verbose is True

    @pytest.mark.asyncio
    async def test_verbose_off(self):
        """Verbose deaktivieren."""
        settings.verbose = True
        result = await command(cmd="verbose", arg="off")
        assert "OFF" in result
        assert settings.verbose is False

    @pytest.mark.asyncio
    async def test_verbose_status(self):
        """Verbose Status abfragen."""
        settings.verbose = True
        result = await command(cmd="verbose")
        assert "ON" in result

    @pytest.mark.asyncio
    async def test_log_on(self, temp_dir):
        """Logging aktivieren."""
        log_file = temp_dir / "cmd.log"
        result = await command(cmd="log", arg=str(log_file))

        assert "ON" in result
        assert settings.log_enabled is True

    @pytest.mark.asyncio
    async def test_log_off(self):
        """Logging deaktivieren."""
        settings.log_enabled = True
        result = await command(cmd="log", arg="off")

        assert "OFF" in result
        assert settings.log_enabled is False

    @pytest.mark.asyncio
    async def test_status(self):
        """Status anzeigen."""
        result = await command(cmd="status")

        assert "Verbose" in result
        assert "Logging" in result
        assert "Working Dir" in result

    @pytest.mark.asyncio
    async def test_unknown_command(self):
        """Unbekanntes Kommando."""
        result = await command(cmd="unknown")
        assert "Unbekanntes Kommando" in result

    @pytest.mark.asyncio
    async def test_slash_prefix(self):
        """Kommando mit Slash-Prefix."""
        result = await command(cmd="/verbose", arg="on")
        assert "ON" in result
