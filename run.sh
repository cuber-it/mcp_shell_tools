#!/bin/bash
# Startet den mcp_tools Server aus dem venv
# Verwende dieses Script in der Claude Desktop Config

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Desktop-Session Env-Vars holen (für GUI-Apps aus shell_exec)
# Sucht einen laufenden Desktop-Prozess und extrahiert dessen Umgebung
if [ -z "$DISPLAY" ]; then
    DESKTOP_PID=$(pgrep -u "$USER" 'cinnamon|gnome-shell|plasmashell|xfce4-panel|mate-panel' 2>/dev/null | head -1)
    if [ -n "$DESKTOP_PID" ] && [ -r "/proc/$DESKTOP_PID/environ" ]; then
        while IFS= read -r -d '' line; do
            case "$line" in
                DISPLAY=*|XAUTHORITY=*|XDG_RUNTIME_DIR=*|DBUS_SESSION_BUS_ADDRESS=*)
                    export "$line"
                    ;;
            esac
        done < "/proc/$DESKTOP_PID/environ"
    fi
fi

exec "$SCRIPT_DIR/.venv/bin/workstation-mcp" "$@"
