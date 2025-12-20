"""Editor-Tools: Präzises Editieren und Diff-Vorschau."""

import difflib
from typing import Optional

from pydantic import BaseModel, Field

from ..config import DEFAULT_ENCODING
from ..utils.paths import resolve_path


# --- Input Models ---

class StrReplaceInput(BaseModel):
    """Input für str_replace."""
    path: str = Field(..., description="Pfad zur Datei")
    old_str: str = Field(..., description="Zu ersetzender Text (muss exakt einmal vorkommen)")
    new_str: str = Field(default="", description="Neuer Text (leer = löschen)")
    encoding: str = Field(default=DEFAULT_ENCODING, description="Encoding")


class DiffPreviewInput(BaseModel):
    """Input für diff_preview."""
    path: str = Field(..., description="Pfad zur Datei")
    old_str: str = Field(..., description="Zu ersetzender Text")
    new_str: str = Field(default="", description="Neuer Text")
    context_lines: int = Field(default=3, description="Kontext-Zeilen im Diff")
    encoding: str = Field(default=DEFAULT_ENCODING, description="Encoding")


# --- Tool Functions ---

async def str_replace(params: StrReplaceInput) -> str:
    """Ersetzt einen Text in einer Datei.
    
    Der zu ersetzende Text muss EXAKT EINMAL in der Datei vorkommen.
    Dies verhindert versehentliche Mehrfach-Ersetzungen.
    
    Für neue Dateien nutze file_write.
    """
    path = resolve_path(params.path)
    
    if not path.exists():
        return f"Fehler: Datei existiert nicht: {path}"
    
    if not path.is_file():
        return f"Fehler: Kein reguläres File: {path}"
    
    try:
        content = path.read_text(encoding=params.encoding)
    except Exception as e:
        return f"Fehler beim Lesen: {e}"
    
    # Prüfen ob old_str vorkommt
    count = content.count(params.old_str)
    
    if count == 0:
        return f"Fehler: Text nicht gefunden in {path}:\n\n{params.old_str[:200]}{'...' if len(params.old_str) > 200 else ''}"
    
    if count > 1:
        return f"Fehler: Text kommt {count}x vor (muss genau 1x sein). Verwende mehr Kontext für Eindeutigkeit."
    
    # Ersetzen
    new_content = content.replace(params.old_str, params.new_str, 1)
    
    try:
        path.write_text(new_content, encoding=params.encoding)
    except Exception as e:
        return f"Fehler beim Schreiben: {e}"
    
    # Zusammenfassung
    old_lines = len(params.old_str.splitlines())
    new_lines = len(params.new_str.splitlines()) if params.new_str else 0
    
    if not params.new_str:
        action = f"Gelöscht: {old_lines} Zeilen"
    elif old_lines == new_lines:
        action = f"Ersetzt: {old_lines} Zeilen"
    else:
        action = f"Ersetzt: {old_lines} → {new_lines} Zeilen"
    
    return f"✓ {path}\n{action}"


async def diff_preview(params: DiffPreviewInput) -> str:
    """Zeigt Vorschau der Änderungen als Unified Diff.
    
    Nützlich um Änderungen zu prüfen bevor str_replace aufgerufen wird.
    """
    path = resolve_path(params.path)
    
    if not path.exists():
        return f"Fehler: Datei existiert nicht: {path}"
    
    try:
        content = path.read_text(encoding=params.encoding)
    except Exception as e:
        return f"Fehler beim Lesen: {e}"
    
    # Prüfen ob old_str vorkommt
    count = content.count(params.old_str)
    
    if count == 0:
        return f"Fehler: Text nicht gefunden in {path}"
    
    if count > 1:
        return f"Warnung: Text kommt {count}x vor. str_replace würde fehlschlagen."
    
    # Diff erstellen
    new_content = content.replace(params.old_str, params.new_str, 1)
    
    old_lines = content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{path.name}",
        tofile=f"b/{path.name}",
        n=params.context_lines
    )
    
    diff_text = "".join(diff)
    
    if not diff_text:
        return "Keine Änderungen (old_str == new_str)"
    
    return f"Vorschau für {path}:\n\n{diff_text}"
