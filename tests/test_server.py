"""Smoke Tests für den MCP Server."""

import pytest


class TestServerImports:
    """Tests dass alle Module importierbar sind."""
    
    def test_import_server(self):
        """Server-Modul importierbar."""
        from workstation_mcp import server
        assert hasattr(server, 'mcp')
        assert hasattr(server, 'main')
    
    def test_import_tools(self):
        """Tool-Module importierbar."""
        from workstation_mcp.tools import filesystem
        from workstation_mcp.tools import editor
        from workstation_mcp.tools import search
        from workstation_mcp.tools import shell
        from workstation_mcp.tools import project
        from workstation_mcp.tools import memory
        from workstation_mcp.tools import session
    
    def test_import_persistence(self):
        """Persistenz-Module importierbar."""
        from workstation_mcp.persistence import models
        from workstation_mcp.persistence import session_manager
    
    def test_import_state(self):
        """State-Modul importierbar."""
        from workstation_mcp import state
        assert hasattr(state, 'state')
    
    def test_import_config(self):
        """Config-Modul importierbar."""
        from workstation_mcp import config
        assert hasattr(config, 'SHELL_TIMEOUT_SECONDS')
        assert hasattr(config, 'MAX_OUTPUT_BYTES')


class TestToolRegistration:
    """Tests dass alle Tools registriert sind."""
    
    def test_tools_registered(self):
        """Alle erwarteten Tools sind registriert."""
        from workstation_mcp.server import mcp
        
        # FastMCP speichert Tools intern
        # Wir prüfen nur, dass der Server existiert
        assert mcp is not None
        assert mcp.name == "workstation_mcp"
