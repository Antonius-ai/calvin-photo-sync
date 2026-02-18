#!/bin/bash

# Calvin Photo Sync Daemon Control Script

DAEMON_SCRIPT="$HOME/.openclaw/workspace/calvin_daemon_enhanced.py"
DAEMON_PLIST="$HOME/Library/LaunchAgents/com.calvin.photosync.daemon.plist"

show_help() {
    echo "🎯 Calvin Photo Sync Control"
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start      - Start the daemon"
    echo "  stop       - Stop the daemon"
    echo "  restart    - Restart the daemon"
    echo "  status     - Show daemon status"
    echo "  logs       - Show recent logs"
    echo "  info       - Show device information"
    echo "  force      - Force sync Calvin device"
    echo "  test       - Test device detection"
    echo "  reset      - Reset sync history"
    echo "  help       - Show this help"
}

daemon_status() {
    if launchctl list | grep -q "com.calvin.photosync.daemon"; then
        echo "✅ Calvin daemon is running"
        launchctl list | grep calvin
    else
        echo "❌ Calvin daemon is not running"
    fi
}

case "$1" in
    start)
        echo "🚀 Starting Calvin daemon..."
        launchctl load "$DAEMON_PLIST"
        sleep 1
        daemon_status
        ;;
    
    stop)
        echo "🛑 Stopping Calvin daemon..."
        launchctl unload "$DAEMON_PLIST"
        echo "✅ Daemon stopped"
        ;;
    
    restart)
        echo "🔄 Restarting Calvin daemon..."
        launchctl unload "$DAEMON_PLIST" 2>/dev/null || true
        sleep 1
        launchctl load "$DAEMON_PLIST"
        sleep 1
        daemon_status
        ;;
    
    status)
        daemon_status
        echo ""
        echo "Recent activity:"
        tail -5 ~/.calvin_photo_sync.log 2>/dev/null || echo "No logs found"
        ;;
    
    logs)
        echo "📋 Recent Calvin daemon logs:"
        echo "============================"
        tail -20 ~/.calvin_photo_sync.log 2>/dev/null || echo "No logs found"
        ;;
    
    info)
        echo "📱 Device information:"
        python3 "$DAEMON_SCRIPT" --info
        ;;
    
    force)
        echo "🚀 Force syncing Calvin device..."
        python3 "$DAEMON_SCRIPT" --force-sync Calvin
        ;;
    
    test)
        echo "🧪 Testing device detection..."
        python3 "$DAEMON_SCRIPT" --test
        ;;
    
    reset)
        echo "🗑️  Resetting sync history..."
        python3 "$DAEMON_SCRIPT" --reset-history
        ;;
    
    help|--help|-h)
        show_help
        ;;
    
    "")
        show_help
        ;;
    
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac