"""Konfiguration und Konstanten für workstation_mcp."""

import re
from pathlib import Path

# Timeouts
SHELL_TIMEOUT_SECONDS = 30

# Shell Security
BLOCKED_PATTERNS: list[re.Pattern] = [
    re.compile(r'rm\s+(-[a-zA-Z]*)?\s*-[a-zA-Z]*r[a-zA-Z]*\s+(-[a-zA-Z]*\s+)*(/|~|\*)'),  # rm -rf / ~ *
    re.compile(r'dd\s+.*\s*(if|of)=/dev/'),          # dd auf /dev/
    re.compile(r'mkfs'),                              # mkfs
    re.compile(r'chmod\s+777\s+/'),                   # chmod 777 /
    re.compile(r'>\s*/dev/sd'),                       # > /dev/sd
]
SUDO_NEEDS_CONFIRMATION: bool = True

# Output-Limits
MAX_OUTPUT_BYTES = 100_000  # ~100KB
MAX_LINES_WITHOUT_RANGE = 500  # Zeilenlimit wenn keine Range angegeben

# Encoding
DEFAULT_ENCODING = "utf-8"

# Projektdateien
PROJECT_FILE = "CLAUDE.md"

# Initiales Working Directory
INITIAL_WORKING_DIR = Path.home()
