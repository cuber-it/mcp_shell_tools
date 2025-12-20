#!/bin/bash
# Startet den workstation_mcp Server aus dem venv
# Verwende dieses Script in der Claude Desktop Config

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/.venv/bin/workstation-mcp" "$@"
