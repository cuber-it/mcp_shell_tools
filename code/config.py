"""Konfiguration und Konstanten für mcp_shell_tools."""

import re
from pathlib import Path

# Timeouts
SHELL_TIMEOUT_SECONDS = 30

# Shell Security - Gefährliche Befehle blocken
BLOCKED_PATTERNS: list[re.Pattern] = [
    # rm -rf auf kritische Pfade (inkl. //, /./, etc.)
    re.compile(r'rm\s+(-[a-zA-Z]*\s+)*-[a-zA-Z]*r[a-zA-Z]*\s+(-[a-zA-Z]*\s+)*(/+\.?/?|~|\*)'),
    # dd auf /dev/ (mit oder ohne if=)
    re.compile(r'dd\s+.*of=/dev/'),
    re.compile(r'dd\s+.*if=/dev/.*of='),
    # mkfs (alle Varianten)
    re.compile(r'mkfs'),
    # chmod 777 oder -R auf kritische Pfade
    re.compile(r'chmod\s+(-[a-zA-Z]*\s+)*777\s+/'),
    re.compile(r'chmod\s+.*-R.*\s+777\s+(/|/etc|/usr|/var|/home)'),
    re.compile(r'chmod\s+777\s+.*-R.*(/|/etc|/usr|/var|/home)'),
    # Redirect auf Block-Devices (verschiedene Schreibweisen)
    re.compile(r'>\s*/dev/[sh]d'),
    re.compile(r'cat\s+.*>\s*/dev/[sh]d'),
    re.compile(r'tee\s+/dev/[sh]d'),
    # Gefährliche Pipes zu dd
    re.compile(r'\|\s*dd\s+of=/dev/'),
    # Fork-Bombs
    re.compile(r':\(\)\s*\{\s*:\|:'),
    re.compile(r'\.\s*/dev/null\s*\|'),
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
