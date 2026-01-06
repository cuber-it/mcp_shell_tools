"""Output-Formatierung und Truncation."""

from code.config import MAX_OUTPUT_BYTES, DEFAULT_ENCODING


def truncate_output(text: str, max_bytes: int = MAX_OUTPUT_BYTES) -> str:
    """Kürzt Output wenn zu lang."""
    encoded = text.encode(DEFAULT_ENCODING, errors="replace")
    if len(encoded) <= max_bytes:
        return text
    
    truncated = encoded[:max_bytes].decode(DEFAULT_ENCODING, errors="replace")
    return f"{truncated}\n\n[... TRUNCATED ({len(encoded):,} bytes total) ...]"


def format_with_line_numbers(
    content: str,
    start_line: int = 1,
    end_line: int | None = None
) -> str:
    """Formatiert Inhalt mit Zeilennummern.
    
    Args:
        content: Der Dateiinhalt
        start_line: Erste anzuzeigende Zeile (1-basiert)
        end_line: Letzte anzuzeigende Zeile (None = bis Ende)
    
    Returns:
        Formatierter String mit Zeilennummern
    """
    lines = content.splitlines()
    total_lines = len(lines)
    
    # Range validieren
    start_idx = max(0, start_line - 1)
    end_idx = total_lines if end_line is None else min(end_line, total_lines)
    
    if start_idx >= total_lines:
        return f"[Datei hat nur {total_lines} Zeilen]"
    
    selected_lines = lines[start_idx:end_idx]
    
    # Breite für Zeilennummern berechnen
    max_line_num = end_idx
    width = len(str(max_line_num))
    
    # Formatieren
    formatted_lines = []
    for i, line in enumerate(selected_lines, start=start_idx + 1):
        formatted_lines.append(f"{i:>{width}} │ {line}")
    
    result = "\n".join(formatted_lines)
    
    # Header mit Info
    header = f"[Zeilen {start_idx + 1}-{end_idx} von {total_lines}]\n"
    
    return header + result
