"""Search-Tool: Textsuche in Dateien."""

import re
from pathlib import Path
from typing import Annotated

from pydantic import Field

from ..config import DEFAULT_ENCODING
from ..utils.output import truncate_output
from ..utils.paths import resolve_path


# --- Helper ---

def _search_in_file(
    file_path: Path,
    pattern: str,
    ignore_case: bool,
    is_regex: bool,
    context_lines: int
) -> list[dict]:
    """Sucht in einer einzelnen Datei."""
    try:
        content = file_path.read_text(encoding=DEFAULT_ENCODING)
    except (UnicodeDecodeError, PermissionError):
        return []
    
    lines = content.splitlines()
    results = []
    
    # Pattern vorbereiten
    flags = re.IGNORECASE if ignore_case else 0
    if is_regex:
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return [{"error": f"Ungültiger Regex: {e}"}]
        match_func = lambda line: regex.search(line) is not None
    else:
        if ignore_case:
            pattern_lower = pattern.lower()
            match_func = lambda line: pattern_lower in line.lower()
        else:
            match_func = lambda line: pattern in line
    
    # Zeilen durchsuchen
    for i, line in enumerate(lines, start=1):
        if match_func(line):
            result = {
                "line_num": i,
                "line": line,
                "context_before": [],
                "context_after": []
            }
            
            # Kontext sammeln
            if context_lines > 0:
                start = max(0, i - 1 - context_lines)
                end = min(len(lines), i + context_lines)
                result["context_before"] = [
                    (j + 1, lines[j]) for j in range(start, i - 1)
                ]
                result["context_after"] = [
                    (j + 1, lines[j]) for j in range(i, end)
                ]
            
            results.append(result)
    
    return results


# --- Tool Function ---

async def grep(
    pattern: Annotated[str, Field(description="Suchmuster (Text oder Regex)")],
    path: Annotated[str, Field(description="Datei oder Verzeichnis")] = ".",
    recursive: Annotated[bool, Field(description="Rekursiv in Unterverzeichnissen suchen")] = True,
    ignore_case: Annotated[bool, Field(description="Groß-/Kleinschreibung ignorieren")] = False,
    is_regex: Annotated[bool, Field(description="Pattern als Regex interpretieren")] = False,
    file_pattern: Annotated[str, Field(description="Glob-Pattern für Dateien, z.B. '*.py'")] = "*",
    context_lines: Annotated[int, Field(description="Kontext-Zeilen vor/nach Treffer (0-5)")] = 0,
    max_results: Annotated[int, Field(description="Maximale Anzahl Treffer")] = 50,
) -> str:
    """Sucht nach einem Muster in Dateien.
    
    Ähnlich wie grep auf der Kommandozeile. Sucht Text oder Regex
    in einer Datei oder rekursiv in einem Verzeichnis.
    
    Beispiele:
      - grep(pattern="TODO", path=".", recursive=True)
      - grep(pattern="def.*test", is_regex=True, file_pattern="*.py")
    """
    resolved = resolve_path(path)
    context = min(context_lines, 5)  # Max 5 Kontext-Zeilen
    
    if not resolved.exists():
        return f"Fehler: Pfad existiert nicht: {resolved}"
    
    # Dateien sammeln
    if resolved.is_file():
        files = [resolved]
    elif resolved.is_dir():
        if recursive:
            files = list(resolved.rglob(file_pattern))
        else:
            files = list(resolved.glob(file_pattern))
        files = [f for f in files if f.is_file()]
    else:
        return f"Fehler: Weder Datei noch Verzeichnis: {resolved}"
    
    if not files:
        return f"Keine Dateien gefunden für '{file_pattern}' in {resolved}"
    
    # Suchen
    all_results = []
    files_with_matches = 0
    
    for file in sorted(files):
        # Versteckte Dateien/Verzeichnisse überspringen
        if any(part.startswith(".") for part in file.parts):
            continue
        
        results = _search_in_file(
            file, 
            pattern, 
            ignore_case, 
            is_regex,
            context
        )
        
        if results:
            # Fehler prüfen
            if results and "error" in results[0]:
                return results[0]["error"]
            
            files_with_matches += 1
            for r in results:
                r["file"] = file
                all_results.append(r)
                
                if len(all_results) >= max_results:
                    break
        
        if len(all_results) >= max_results:
            break
    
    if not all_results:
        return f"Keine Treffer für '{pattern}' in {len(files)} Dateien"
    
    # Formatieren
    output_lines = [
        f"Treffer für '{pattern}': {len(all_results)} in {files_with_matches} Dateien\n"
    ]
    
    current_file = None
    for r in all_results:
        # Datei-Header
        if r["file"] != current_file:
            current_file = r["file"]
            try:
                relative = current_file.relative_to(resolved)
            except ValueError:
                relative = current_file
            output_lines.append(f"\n📄 {relative}")
        
        # Kontext vorher
        for num, line in r.get("context_before", []):
            output_lines.append(f"  {num:>4} │ {line}")
        
        # Treffer-Zeile
        output_lines.append(f"  {r['line_num']:>4} │ {r['line']}  ◀")
        
        # Kontext nachher
        for num, line in r.get("context_after", []):
            output_lines.append(f"  {num:>4} │ {line}")
    
    if len(all_results) >= max_results:
        output_lines.append(f"\n[Limit erreicht: {max_results} Treffer]")
    
    return truncate_output("\n".join(output_lines))
