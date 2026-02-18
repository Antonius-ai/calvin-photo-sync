# Calvin Photo Sync - Quick Start Guide

Get up and running with intelligent GPS-aware photo synchronization in minutes!

## 🚀 Installation (5 minutes)

### 1. Clone and Setup
```bash
git clone https://github.com/Antonius-ai/calvin-photo-sync.git
cd calvin-photo-sync
pip3 install Pillow --break-system-packages
npm install -g @immich/cli
```

### 2. Configure Your Devices
Edit the example configuration for your setup:
```bash
cp example_config.json ~/.calvin_photo_sync.json
```

Update device paths in `~/.calvin_photo_sync.json`:
```json
{
  "source_devices": {
    "Calvin": "/Volumes/Calvin",
    "MyCamera": "/Volumes/YOUR_DEVICE_NAME"
  },
  "destination": "/Volumes/YOUR_DESTINATION_DRIVE"
}
```

### 3. Setup Immich Authentication
```bash
immich login-key http://your-immich-server:2283 your-api-key
```

### 4. Install Automatic Daemon
```bash
./setup_calvin_daemon.sh
```

## ✅ You're Done!

The system is now monitoring for device connections. When you connect your photo device:

1. **Automatic Detection** → Receives notification "Device connected..."
2. **Intelligent Processing** → Groups photos by trips using GPS + time
3. **Location Naming** → Creates albums like "2025-05-17-Hawaii"  
4. **Upload & Archive** → Uploads to Immich and organizes files
5. **Completion Alert** → Shows statistics and results

## 🎮 Quick Commands

```bash
# Check status
./calvin_control.sh status

# View recent activity  
./calvin_control.sh logs

# Force sync right now
./calvin_control.sh force

# Get device info
./calvin_control.sh info
```

## 🔧 Common Customizations

### Add New Cities
Edit `calvin_photo_sync_optimized.py`, find `get_location_name()` method:

```python
locations = [
    # Add your locations here:
    (40.7831, -73.9712, 50, "New-York-Central-Park"),
    (25.7617, -80.1918, 100, "Miami"),
    (47.6062, -122.3321, 100, "Seattle"),
    # Format: (latitude, longitude, radius_km, "Album-Name")
]
```

### Add New Devices  
Update `~/.calvin_photo_sync.json`:
```json
"source_devices": {
  "Calvin": "/Volumes/Calvin",
  "iPhone": "/Volumes/iPhone", 
  "DroneSD": "/Volumes/DRONE_SD"
}
```

### Adjust Trip Timing
Fine-tune trip detection:
```json
"trip_detection": {
  "short_gap_hours": 8,     // Longer = more consolidation
  "long_gap_days": 3,       // Max days for same trip  
  "cluster_radius_km": 50   // GPS grouping radius
}
```

## 📊 Viewing Logs

```bash
# Live monitoring
tail -f ~/.calvin_photo_sync.log

# Recent errors
grep ERROR ~/.calvin_photo_sync.log

# Sync statistics
grep "photos copied" ~/.calvin_photo_sync.log
```

## 🆘 Troubleshooting

**Daemon not starting?**
```bash
./calvin_control.sh restart
./calvin_control.sh logs
```

**Device not detected?**
```bash
./calvin_control.sh info
ls /Volumes/  # Check mount points
```

**Upload failing?**
```bash
immich server-info  # Test connection
immich login-key <server> <key>  # Re-authenticate
```

## 🎯 What Makes This Special

- **Week-long trips stay as single albums** (GPS-aware grouping)
- **Automatic location names** in album titles
- **Smart break detection** (meals, overnight stays, travel time)  
- **Perfect deduplication** prevents re-uploads
- **Original date preservation** throughout process
- **Comprehensive monitoring** with notifications and logs

---

**Ready to sync!** Connect your photo device and watch the magic happen ✨

For detailed documentation, see [README.md](README.md)