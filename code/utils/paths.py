"""Pfad-Utilities."""

from pathlib import Path

from state import state


def resolve_path(path: str) -> Path:
    """Löst einen Pfad relativ zum Working Directory auf.
    
    Wrapper um state.resolve_path für einfacheren Import.
    """
    return state.resolve_path(path)
