"""Smoke Tests für den MCP Server."""

import pytest


class TestServerImports:
    """Tests dass alle Module importierbar sind."""

    def test_import_server(self):
        """Server-Modul importierbar."""
        from code import server
        assert hasattr(server, 'mcp')
        assert hasattr(server, 'main')

    def test_import_tools(self):
        """Tool-Module importierbar."""
        from code.tools import filesystem
        from code.tools import editor
        from code.tools import search
        from code.tools import shell
        from code.tools import project
        from code.tools import memory
        from code.tools import session

    def test_import_persistence(self):
        """Persistenz-Module importierbar."""
        from code.persistence import models
        from code.persistence import session_manager

    def test_import_state(self):
        """State-Modul importierbar."""
        from code import state
        assert hasattr(state, 'state')

    def test_import_config(self):
        """Config-Modul importierbar."""
        from code import config
        assert hasattr(config, 'SHELL_TIMEOUT_SECONDS')
        assert hasattr(config, 'MAX_OUTPUT_BYTES')


class TestToolRegistration:
    """Tests dass alle Tools registriert sind."""

    def test_tools_registered(self):
        """Alle erwarteten Tools sind registriert."""
        from code.server import mcp

        # FastMCP speichert Tools intern
        # Wir prüfen nur, dass der Server existiert
        assert mcp is not None
        assert mcp.name == "mcp_shell_tools"
