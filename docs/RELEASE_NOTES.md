# MCP Shell Tools - Release Notes v1.1.0

## Status: Feature Complete (stdio)

Diese Version ist die **finale stdio-Version** für Claude Desktop.

Die aktive Entwicklung konzentriert sich jetzt auf die HTTP-Version 
(`mcp_shell_tools_http`) für Remote-Zugriff via claude.ai.

## Was diese Version bietet

### Kernfunktionalität
- **Dateisystem**: Lesen, Schreiben, Auflisten, Suchen
- **Editor**: Präzises Text-Ersetzen mit Diff-Preview
- **Shell**: Befehle ausführen mit Timeout und Cleanup
- **Suche**: grep mit Regex und Kontext

### Projekt-Management  
- Working Directory Management (`cd`, `cwd`)
- Automatisches Laden von `CLAUDE.md` für Projekt-Kontext

### Persistenz
- **Memory**: Erkenntnisse, Entscheidungen, TODOs, Fragen speichern
- **Sessions**: Arbeitssitzungen speichern und fortsetzen
- **Transcript**: Vollständige Protokollierung aller Tool-Aufrufe

### Stabilität
- Sauberer Shutdown bei SIGTERM/SIGINT
- Process-Group-Killing für Shell-Befehle
- Log-Rotation für langlebige Sessions

## Deployment

### Voraussetzungen
- Python 3.10+
- Claude Desktop

### Installation
```bash
git clone https://github.com/ucuber/mcp_shell_tools.git
cd mcp_shell_tools
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Claude Desktop Config
```json
{
  "mcpServers": {
    "shell-tools": {
      "command": "/pfad/zu/mcp_shell_tools/run.sh"
    }
  }
}
```

## Bekannte Einschränkungen

- **Nur lokal**: Funktioniert nur mit Claude Desktop, nicht mit claude.ai
- **Keine Windows-Unterstützung**: Process-Group-Handling ist Linux/Mac-spezifisch
- **Kein Streaming**: Shell-Output wird gesammelt, nicht gestreamt

## Für Remote-Zugriff

Siehe [mcp_shell_tools_http](../mcp_shell_tools_http/) für:
- HTTP/SSE Transport
- OAuth-Authentifizierung
- Zugriff via claude.ai im Browser
- Zentrales Deployment für Teams

## Support

Bei Problemen:
1. `~/.mcp_shell_tools/transcripts/` prüfen
2. Claude Desktop Logs checken
3. Issue auf GitHub erstellen

---

*Release: 2026-01-17*  
*Maintainer: UC IT Service*
