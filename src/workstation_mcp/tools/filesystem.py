"""Filesystem-Tools: Lesen, Schreiben, Auflisten, Suchen."""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from ..config import DEFAULT_ENCODING, MAX_LINES_WITHOUT_RANGE
from ..utils.output import truncate_output, format_with_line_numbers
from ..utils.paths import resolve_path


# --- Input Models ---

class FileReadInput(BaseModel):
    """Input für file_read."""
    path: str = Field(..., description="Pfad zur Datei (absolut oder relativ)")
    start_line: Optional[int] = Field(
        default=None, 
        description="Erste Zeile (1-basiert). Ohne Angabe: von Anfang."
    )
    end_line: Optional[int] = Field(
        default=None,
        description="Letzte Zeile. Ohne Angabe: bis Ende (max 500 Zeilen ohne Range)."
    )
    encoding: str = Field(default=DEFAULT_ENCODING, description="Encoding")


class FileWriteInput(BaseModel):
    """Input für file_write."""
    path: str = Field(..., description="Pfad zur Datei")
    content: str = Field(..., description="Neuer Inhalt")
    encoding: str = Field(default=DEFAULT_ENCODING, description="Encoding")


class FileListInput(BaseModel):
    """Input für file_list."""
    path: str = Field(default=".", description="Verzeichnis")
    recursive: bool = Field(default=False, description="Rekursiv auflisten")
    max_depth: int = Field(default=3, description="Max. Tiefe bei rekursiv")
    show_hidden: bool = Field(default=False, description="Versteckte Dateien zeigen")


class GlobSearchInput(BaseModel):
    """Input für glob_search."""
    pattern: str = Field(..., description="Glob-Pattern, z.B. '**/*.py' oder 'src/**/*.js'")
    path: str = Field(default=".", description="Startverzeichnis")


# --- Tool Functions ---

async def file_read(params: FileReadInput) -> str:
    """Liest eine Datei mit optionaler Zeilen-Range.
    
    Gibt Inhalt mit Zeilennummern zurück. Bei großen Dateien ohne
    Range-Angabe werden nur die ersten 500 Zeilen gezeigt.
    """
    path = resolve_path(params.path)
    
    if not path.exists():
        return f"Fehler: Datei existiert nicht: {path}"
    
    if not path.is_file():
        return f"Fehler: Kein reguläres File: {path}"
    
    try:
        content = path.read_text(encoding=params.encoding)
    except UnicodeDecodeError:
        size = path.stat().st_size
        return f"Binärdatei: {path} ({size:,} bytes) - kann nicht als Text gelesen werden"
    except Exception as e:
        return f"Fehler beim Lesen: {e}"
    
    # Range bestimmen
    total_lines = len(content.splitlines())
    start = params.start_line or 1
    
    if params.end_line:
        end = params.end_line
    elif params.start_line:
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


async def file_write(params: FileWriteInput) -> str:
    """Schreibt kompletten Inhalt in eine Datei.
    
    Erstellt Verzeichnisse falls nötig. Für präzise Änderungen
    nutze stattdessen str_replace.
    """
    path = resolve_path(params.path)
    
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(params.content, encoding=params.encoding)
        lines = len(params.content.splitlines())
        return f"Geschrieben: {path} ({lines} Zeilen, {len(params.content):,} Zeichen)"
    except Exception as e:
        return f"Fehler beim Schreiben: {e}"


async def file_list(params: FileListInput) -> str:
    """Listet Dateien und Verzeichnisse auf."""
    path = resolve_path(params.path)
    
    if not path.exists():
        return f"Fehler: Verzeichnis existiert nicht: {path}"
    
    if not path.is_dir():
        return f"Fehler: Kein Verzeichnis: {path}"
    
    lines = [f"📁 {path}\n"]
    
    try:
        if params.recursive:
            items = sorted(path.rglob("*"))
        else:
            items = sorted(path.iterdir())
        
        for item in items:
            # Hidden files filtern
            if not params.show_hidden and item.name.startswith("."):
                continue
            
            # Bei rekursiv: Tiefe prüfen
            if params.recursive:
                try:
                    relative = item.relative_to(path)
                    depth = len(relative.parts)
                    if depth > params.max_depth:
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
        return f"Fehler: Keine Berechtigung für {path}"
    except Exception as e:
        return f"Fehler: {e}"


async def glob_search(params: GlobSearchInput) -> str:
    """Sucht Dateien nach Glob-Pattern.
    
    Beispiele:
      - '*.py' - Python-Dateien im aktuellen Verzeichnis
      - '**/*.py' - Python-Dateien rekursiv
      - 'src/**/*.{js,ts}' - JS/TS-Dateien unter src/
    """
    path = resolve_path(params.path)
    
    if not path.exists():
        return f"Fehler: Verzeichnis existiert nicht: {path}"
    
    if not path.is_dir():
        return f"Fehler: Kein Verzeichnis: {path}"
    
    try:
        matches = sorted(path.glob(params.pattern))
        
        if not matches:
            return f"Keine Treffer für '{params.pattern}' in {path}"
        
        lines = [f"Treffer für '{params.pattern}' in {path}:\n"]
        
        for match in matches[:100]:  # Limit auf 100 Treffer
            relative = match.relative_to(path)
            if match.is_dir():
                lines.append(f"📁 {relative}/")
            else:
                lines.append(f"📄 {relative}")
        
        if len(matches) > 100:
            lines.append(f"\n[... und {len(matches) - 100} weitere Treffer]")
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"Fehler: {e}"
