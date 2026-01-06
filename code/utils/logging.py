"""Logging-Konfiguration für MCP Shell Tools."""

import logging
import sys
from pathlib import Path
from typing import Optional

# Default-Konfiguration
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: int = DEFAULT_LOG_LEVEL,
    log_file: Optional[Path] = None,
    console: bool = False,
) -> logging.Logger:
    """Konfiguriert das Logging-System.

    Args:
        level: Log-Level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optionaler Pfad zur Log-Datei
        console: True = auch auf stderr ausgeben

    Returns:
        Root-Logger für das Package
    """
    logger = logging.getLogger("mcp_shell_tools")
    logger.setLevel(level)

    # Existierende Handler entfernen
    logger.handlers.clear()

    formatter = logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT)

    # File-Handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Console-Handler (stderr für MCP-Kompatibilität)
    if console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # NullHandler falls keine Handler konfiguriert
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())

    return logger


def get_logger(name: str) -> logging.Logger:
    """Gibt einen Sub-Logger zurück.

    Args:
        name: Modul-Name (z.B. "tools.shell")

    Returns:
        Logger-Instanz
    """
    return logging.getLogger(f"mcp_shell_tools.{name}")


# Standard-Logger initialisieren
_root_logger = setup_logging()


def set_log_level(level: int) -> None:
    """Ändert das Log-Level zur Laufzeit."""
    _root_logger.setLevel(level)
    for handler in _root_logger.handlers:
        handler.setLevel(level)


def enable_file_logging(log_file: Path, level: int = DEFAULT_LOG_LEVEL) -> None:
    """Aktiviert File-Logging zur Laufzeit."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(
        logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT)
    )
    _root_logger.addHandler(file_handler)


def disable_file_logging() -> None:
    """Deaktiviert File-Logging."""
    _root_logger.handlers = [
        h for h in _root_logger.handlers
        if not isinstance(h, logging.FileHandler)
    ]
