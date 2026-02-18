#!/bin/bash
set -e

echo "🎯 Calvin Enhanced Photo Sync Daemon Setup"
echo "=========================================="

# Configuration
DAEMON_SCRIPT="$HOME/.openclaw/workspace/calvin_daemon_enhanced.py"
PLIST_FILE="$HOME/.openclaw/workspace/com.calvin.photosync.daemon.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
DAEMON_PLIST="$LAUNCH_AGENTS_DIR/com.calvin.photosync.daemon.plist"

# Make daemon executable
echo "📝 Making daemon script executable..."
chmod +x "$DAEMON_SCRIPT"

# Test daemon first
echo "🧪 Testing daemon functionality..."
if python3 "$DAEMON_SCRIPT" --test; then
    echo "✅ Daemon test passed"
else
    echo "❌ Daemon test failed - check your configuration"
    exit 1
fi

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$LAUNCH_AGENTS_DIR"

# Copy plist file to LaunchAgents
echo "📋 Installing launch agent plist..."
cp "$PLIST_FILE" "$DAEMON_PLIST"

# Unload existing daemon if running
echo "🔄 Stopping existing daemon (if running)..."
launchctl unload "$DAEMON_PLIST" 2>/dev/null || true

# Load the daemon
echo "🚀 Starting Calvin Photo Sync daemon..."
launchctl load "$DAEMON_PLIST"

# Check if it's running
sleep 2
if launchctl list | grep -q "com.calvin.photosync.daemon"; then
    echo "✅ Daemon successfully started!"
    echo ""
    echo "📱 The daemon is now monitoring for Calvin device connections"
    echo "🗺️  GPS-aware trip detection is enabled"
    echo "📍 Location naming active for albums"
    echo ""
    echo "📋 Management commands:"
    echo "   View status:      launchctl list | grep calvin"
    echo "   Stop daemon:      launchctl unload ~/Library/LaunchAgents/com.calvin.photosync.daemon.plist"
    echo "   Start daemon:     launchctl load ~/Library/LaunchAgents/com.calvin.photosync.daemon.plist"
    echo "   View logs:        tail -f ~/.calvin_photo_sync.log"
    echo "   Force sync:       python3 '$DAEMON_SCRIPT' --force-sync Calvin"
    echo "   Device info:      python3 '$DAEMON_SCRIPT' --info"
    echo ""
    echo "🔔 You'll receive notifications when Calvin is connected and sync completes"
    
else
    echo "❌ Failed to start daemon"
    echo "Check logs: tail ~/.calvin_daemon.err.log"
    exit 1
fi

echo ""
echo "🎉 Setup complete! Connect Calvin to trigger automatic sync."