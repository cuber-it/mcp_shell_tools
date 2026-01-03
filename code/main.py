#!/usr/bin/env python3
"""MCP Shell Tools - Haupteinstiegspunkt.

MCP-Server für lokale Entwicklungsarbeit - Dateisystem, Shell, Editor.

Aufruf:
    python code/main.py serve                    # MCP-Server starten (stdio)
    python code/main.py serve --http 8080        # HTTP-Modus
"""
import argparse
import sys
from pathlib import Path

# code/ zum Pfad hinzufügen für direkte Ausführung
sys.path.insert(0, str(Path(__file__).parent))


def create_parser() -> argparse.ArgumentParser:
    """Erstellt den Argument-Parser."""
    parser = argparse.ArgumentParser(
        prog="mcp-shell-tools",
        description="MCP-Server für lokale Entwicklungsarbeit. "
                    "Dateisystem, Shell, Editor.",
        epilog="Beispiele:\n"
               "  %(prog)s serve                     Startet den MCP-Server\n"
               "  %(prog)s serve --http 8080         HTTP-Modus auf Port 8080\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # Globale Optionen
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Ausführliche Ausgabe",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(
        dest="command",
        title="Befehle",
        description="Verfügbare Befehle (--help für Details)",
    )
    
    # serve - Server starten
    serve_parser = subparsers.add_parser(
        "serve",
        help="MCP-Server starten",
        description="Startet den MCP-Server. Standard: stdio-Modus für Claude Desktop.",
    )
    serve_parser.add_argument(
        "--http",
        type=int,
        nargs="?",
        const=8080,
        metavar="PORT",
        help="HTTP-Modus statt stdio (Standard-Port: 8080)",
    )
    
    return parser


def cmd_serve(args):
    """Startet den MCP-Server."""
    from server import mcp
    
    if args.http:
        print(f"Starte MCP-Server (HTTP auf Port {args.http})...")
        mcp.run(transport="sse", port=args.http)
    else:
        if args.verbose:
            print("Starte MCP-Server (stdio)...", file=sys.stderr)
        mcp.run()


def main() -> int:
    """Hauptfunktion."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    commands = {
        "serve": cmd_serve,
    }
    
    try:
        return commands[args.command](args) or 0
    except KeyboardInterrupt:
        print("\nServer beendet.")
        return 0
    except Exception as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
