"""Konfiguration und Konstanten für workstation_mcp."""

from pathlib import Path

# Timeouts
SHELL_TIMEOUT_SECONDS = 30

# Output-Limits
MAX_OUTPUT_BYTES = 100_000  # ~100KB
MAX_LINES_WITHOUT_RANGE = 500  # Zeilenlimit wenn keine Range angegeben

# Encoding
DEFAULT_ENCODING = "utf-8"

# Projektdateien
PROJECT_FILE = "CLAUDE.md"

# Initiales Working Directory
INITIAL_WORKING_DIR = Path.home()
