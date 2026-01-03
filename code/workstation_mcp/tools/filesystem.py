"""Filesystem-Tools: Lesen, Schreiben, Auflisten, Suchen."""

from pathlib import Path
from typing import Optional, Annotated

from pydantic import Field

from ..config import DEFAULT_ENCODING, MAX_LINES_WITHOUT_RANGE
from ..utils.output import truncate_output, format_with_line_numbers
from ..utils.paths import resolve_path


# --- Tool Functions ---

async def file_read(
    path: Annotated[str, Field(description="Pfad zur Datei (absolut oder relativ)")],
    start_line: Annotated[Optional[int], Field(description="Erste Zeile (1-basiert). Ohne Angabe: von Anfang.")] = None,
    end_line: Annotated[Optional[int], Field(description="Letzte Zeile. Ohne Angabe: bis Ende (max 500 Zeilen ohne Range).")] = None,
    encoding: Annotated[str, Field(description="Encoding")] = DEFAULT_ENCODING,
) -> str:
    """Liest eine Datei mit optionaler Zeilen-Range.
    
    Gibt Inhalt mit Zeilennummern zurück. Bei großen Dateien ohne
    Range-Angabe werden nur die ersten 500 Zeilen gezeigt.
    """
    resolved = resolve_path(path)
    
    if not resolved.exists():
        return f"Fehler: Datei existiert nicht: {resolved}"
    
    if not resolved.is_file():
        return f"Fehler: Kein reguläres File: {resolved}"
    
    try:
        content = resolved.read_text(encoding=encoding)
    except UnicodeDecodeError:
        size = resolved.stat().st_size
        return f"Binärdatei: {resolved} ({size:,} bytes) - kann nicht als Text gelesen werden"
    except Exception as e:
        return f"Fehler beim Lesen: {e}"
    
    # Range bestimmen
    total_lines = len(content.splitlines())
    start = start_line or 1
    
    if end_line:
        end = end_line
    elif start_line:
        # Start angegeben aber kein Ende: bis zum Ende
        end = total_lines
    else:
        # Keine Range: limitieren auf MAX_LINES
        end = min(total_lines, MAX_LINES_WITHOUT_RANGE)
        if total_lines > MAX_LINES_WITHOUT_RANGE:
            hint = f"\n[Datei hat {total_lines} Zeilen. Nutze start_line/end_line für mehr.]"
        else:
            hint = ""
    
    formatted = format_with_line_numbers(content, start, end)
    
    if 'hint' in locals():
        formatted += hint
    
    return truncate_output(formatted)


async def file_write(
    path: Annotated[str, Field(description="Pfad zur Datei")],
    content: Annotated[str, Field(description="Neuer Inhalt")],
    encoding: Annotated[str, Field(description="Encoding")] = DEFAULT_ENCODING,
) -> str:
    """Schreibt kompletten Inhalt in eine Datei.
    
    Erstellt Verzeichnisse falls nötig. Für präzise Änderungen
    nutze stattdessen str_replace.
    """
    resolved = resolve_path(path)
    
    try:
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding=encoding)
        lines = len(content.splitlines())
        return f"Geschrieben: {resolved} ({lines} Zeilen, {len(content):,} Zeichen)"
    except Exception as e:
        return f"Fehler beim Schreiben: {e}"


async def file_list(
    path: Annotated[str, Field(description="Verzeichnis")] = ".",
    recursive: Annotated[bool, Field(description="Rekursiv auflisten")] = False,
    max_depth: Annotated[int, Field(description="Max. Tiefe bei rekursiv")] = 3,
    show_hidden: Annotated[bool, Field(description="Versteckte Dateien zeigen")] = False,
) -> str:
    """Listet Dateien und Verzeichnisse auf."""
    resolved = resolve_path(path)
    
    if not resolved.exists():
        return f"Fehler: Verzeichnis existiert nicht: {resolved}"
    
    if not resolved.is_dir():
        return f"Fehler: Kein Verzeichnis: {resolved}"
    
    lines = [f"📁 {resolved}\n"]
    
    try:
        if recursive:
            items = sorted(resolved.rglob("*"))
        else:
            items = sorted(resolved.iterdir())
        
        for item in items:
            # Hidden files filtern
            if not show_hidden and item.name.startswith("."):
                continue
            
            # Bei rekursiv: Tiefe prüfen
            if recursive:
                try:
                    relative = item.relative_to(resolved)
                    depth = len(relative.parts)
                    if depth > max_depth:
                        continue
                    indent = "  " * (depth - 1)
                except ValueError:
                    continue
            else:
                indent = ""
                relative = item.name
            
            if item.is_dir():
                lines.append(f"{indent}📁 {item.name}/")
            else:
                size = item.stat().st_size
                lines.append(f"{indent}📄 {item.name}  ({size:,} bytes)")
        
        return truncate_output("\n".join(lines))
        
    except PermissionError:
        return f"Fehler: Keine Berechtigung für {resolved}"
    except Exception as e:
        return f"Fehler: {e}"


async def glob_search(
    pattern: Annotated[str, Field(description="Glob-Pattern, z.B. '**/*.py' oder 'src/**/*.js'")],
    path: Annotated[str, Field(description="Startverzeichnis")] = ".",
) -> str:
    """Sucht Dateien nach Glob-Pattern.
    
    Beispiele:
      - '*.py' - Python-Dateien im aktuellen Verzeichnis
      - '**/*.py' - Python-Dateien rekursiv
      - 'src/**/*.{js,ts}' - JS/TS-Dateien unter src/
    """
    resolved = resolve_path(path)
    
    if not resolved.exists():
        return f"Fehler: Verzeichnis existiert nicht: {resolved}"
    
    if not resolved.is_dir():
        return f"Fehler: Kein Verzeichnis: {resolved}"
    
    try:
        matches = sorted(resolved.glob(pattern))
        
        if not matches:
            return f"Keine Treffer für '{pattern}' in {resolved}"
        
        lines = [f"Treffer für '{pattern}' in {resolved}:\n"]
        
        for match in matches[:100]:  # Limit auf 100 Treffer
            relative = match.relative_to(resolved)
            if match.is_dir():
                lines.append(f"📁 {relative}/")
            else:
                lines.append(f"📄 {relative}")
        
        if len(matches) > 100:
            lines.append(f"\n[... und {len(matches) - 100} weitere Treffer]")
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"Fehler: {e}"
