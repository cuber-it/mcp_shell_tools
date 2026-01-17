#!/usr/bin/env python3
"""MCP Shell Tools - Haupteinstiegspunkt.

MCP-Server für lokale Entwicklungsarbeit - Dateisystem, Shell, Editor.

Aufruf:
    python code/main.py serve                    # MCP-Server starten (stdio)
"""
import argparse
import asyncio
import signal
import sys
from pathlib import Path

# Projekt-Root zum Pfad hinzufügen für direkte Ausführung
sys.path.insert(0, str(Path(__file__).parent.parent))

# Flag für Shutdown
_shutdown_requested = False


def _signal_handler(signum, frame):
    """Handler für SIGTERM/SIGINT - initiiert sauberen Shutdown."""
    global _shutdown_requested

    sig_name = signal.Signals(signum).name
    print(f"\n[{sig_name}] Shutdown angefordert...", file=sys.stderr)

    if _shutdown_requested:
        # Zweites Signal = force exit
        print("Force exit!", file=sys.stderr)
        sys.exit(1)

    _shutdown_requested = True

    # Cleanup von laufenden Prozessen
    try:
        from code.tools.shell import cleanup_all_processes
        cleanup_all_processes()
    except Exception as e:
        print(f"Cleanup-Fehler: {e}", file=sys.stderr)

    # Event-Loop beenden falls vorhanden
    try:
        loop = asyncio.get_running_loop()
        loop.stop()
    except RuntimeError:
        pass  # Kein laufender Loop

    sys.exit(0)


def create_parser() -> argparse.ArgumentParser:
    """Erstellt den Argument-Parser."""
    parser = argparse.ArgumentParser(
        prog="mcp-shell-tools",
        description="MCP-Server für lokale Entwicklungsarbeit. "
                    "Dateisystem, Shell, Editor.",
        epilog="Beispiel:\n"
               "  %(prog)s serve                     Startet den MCP-Server\n",
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
        description="Startet den MCP-Server im stdio-Modus für Claude Desktop.",
    )
    
    return parser


def cmd_serve(args):
    """Startet den MCP-Server."""
    from code.server import mcp

    # Signal-Handler registrieren für sauberen Shutdown
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

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
        # Cleanup bei Ctrl+C
        try:
            from code.tools.shell import cleanup_all_processes
            cleanup_all_processes()
        except Exception:
            pass
        print("\nServer beendet.", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
