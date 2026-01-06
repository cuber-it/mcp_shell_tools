"""Editor-Tools: Präzises Editieren und Diff-Vorschau."""

import difflib
from typing import Annotated

from pydantic import Field

from code.config import DEFAULT_ENCODING
from code.utils.paths import resolve_path


# --- Tool Functions ---

async def str_replace(
    path: Annotated[str, Field(description="Pfad zur Datei")],
    old_str: Annotated[str, Field(description="Zu ersetzender Text (muss exakt einmal vorkommen)")],
    new_str: Annotated[str, Field(description="Neuer Text (leer = löschen)")] = "",
    encoding: Annotated[str, Field(description="Encoding")] = DEFAULT_ENCODING,
) -> str:
    """Ersetzt einen Text in einer Datei.
    
    Der zu ersetzende Text muss EXAKT EINMAL in der Datei vorkommen.
    Dies verhindert versehentliche Mehrfach-Ersetzungen.
    
    Für neue Dateien nutze file_write.
    """
    resolved = resolve_path(path)
    
    if not resolved.exists():
        return f"Fehler: Datei existiert nicht: {resolved}"
    
    if not resolved.is_file():
        return f"Fehler: Kein reguläres File: {resolved}"
    
    try:
        content = resolved.read_text(encoding=encoding)
    except Exception as e:
        return f"Fehler beim Lesen: {e}"
    
    # Prüfen ob old_str vorkommt
    count = content.count(old_str)
    
    if count == 0:
        return f"Fehler: Text nicht gefunden in {resolved}:\n\n{old_str[:200]}{'...' if len(old_str) > 200 else ''}"
    
    if count > 1:
        return f"Fehler: Text kommt {count}x vor (muss genau 1x sein). Verwende mehr Kontext für Eindeutigkeit."
    
    # Ersetzen
    new_content = content.replace(old_str, new_str, 1)
    
    try:
        resolved.write_text(new_content, encoding=encoding)
    except Exception as e:
        return f"Fehler beim Schreiben: {e}"
    
    # Zusammenfassung
    old_lines = len(old_str.splitlines())
    new_lines = len(new_str.splitlines()) if new_str else 0
    
    if not new_str:
        action = f"Gelöscht: {old_lines} Zeilen"
    elif old_lines == new_lines:
        action = f"Ersetzt: {old_lines} Zeilen"
    else:
        action = f"Ersetzt: {old_lines} → {new_lines} Zeilen"
    
    return f"✓ {resolved}\n{action}"


async def diff_preview(
    path: Annotated[str, Field(description="Pfad zur Datei")],
    old_str: Annotated[str, Field(description="Zu ersetzender Text")],
    new_str: Annotated[str, Field(description="Neuer Text")] = "",
    context_lines: Annotated[int, Field(description="Kontext-Zeilen im Diff")] = 3,
    encoding: Annotated[str, Field(description="Encoding")] = DEFAULT_ENCODING,
) -> str:
    """Zeigt Vorschau der Änderungen als Unified Diff.
    
    Nützlich um Änderungen zu prüfen bevor str_replace aufgerufen wird.
    """
    resolved = resolve_path(path)
    
    if not resolved.exists():
        return f"Fehler: Datei existiert nicht: {resolved}"
    
    try:
        content = resolved.read_text(encoding=encoding)
    except Exception as e:
        return f"Fehler beim Lesen: {e}"
    
    # Prüfen ob old_str vorkommt
    count = content.count(old_str)
    
    if count == 0:
        return f"Fehler: Text nicht gefunden in {resolved}"
    
    if count > 1:
        return f"Warnung: Text kommt {count}x vor. str_replace würde fehlschlagen."
    
    # Diff erstellen
    new_content = content.replace(old_str, new_str, 1)
    
    old_lines = content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{resolved.name}",
        tofile=f"b/{resolved.name}",
        n=context_lines
    )
    
    diff_text = "".join(diff)
    
    if not diff_text:
        return "Keine Änderungen (old_str == new_str)"
    
    return f"Vorschau für {resolved}:\n\n{diff_text}"
