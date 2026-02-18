# Calvin Enhanced Photo Sync

**Intelligent GPS-aware photo synchronization system for macOS that automatically detects device connections, organizes photos by trips using GPS data and time intelligence, and uploads to Immich with location-based album naming.**

## 🌟 Features

- **🔄 Automatic Sync**: Detects device connections and triggers sync automatically
- **🗺️ GPS-Aware Trip Detection**: Groups photos intelligently using GPS location and time gaps
- **📍 Location Album Naming**: Creates albums like "2025-05-17-Hawaii" or "2025-12-04-San-Francisco"
- **⏰ Smart Time Grouping**: 
  - Short breaks (≤8 hours): Continue same trip
  - Medium breaks (8h-3 days) + same location: Continue trip (perfect for week-long vacations!)
  - Different location or 3+ day gaps: New trip
- **☁️ Immich Integration**: Automatic upload with duplicate detection and album creation
- **📅 Date Preservation**: Maintains original photo creation dates throughout
- **🔔 macOS Notifications**: Real-time status updates and completion notifications
- **📊 Comprehensive Logging**: Detailed activity logs for monitoring and troubleshooting
- **🛡️ Smart Deduplication**: Prevents re-uploading existing photos

## 🚀 Quick Start

### Prerequisites

- macOS system
- Python 3.7+ with PIL/Pillow
- Immich server running and accessible
- External drives mounted at `/Volumes/[DeviceName]` and `/Volumes/[DestinationName]`

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd calvin-photo-sync
   ```

2. **Install Python dependencies:**
   ```bash
   pip3 install Pillow --break-system-packages
   ```

3. **Configure your devices** by editing the configuration (see Configuration section)

4. **Set up Immich CLI:**
   ```bash
   npm install -g @immich/cli
   immich login-key <your-immich-server-url> <your-api-key>
   ```

5. **Install the automatic daemon:**
   ```bash
   ./setup_calvin_daemon.sh
   ```

## ⚙️ Configuration

The system uses `~/.calvin_photo_sync.json` for configuration:

```json
{
  "source_devices": {
    "Calvin": "/Volumes/Calvin",
    "MyCamera": "/Volumes/MyCamera"
  },
  "destination": "/Volumes/Rainbow",
  "folders": {
    "staging": "Photo Staging",
    "new_photos": "New Photos", 
    "uploaded_photos": "Uploaded Photos"
  },
  "trip_detection": {
    "short_gap_hours": 8,
    "long_gap_days": 3,
    "min_photos_per_trip": 3,
    "gps_clustering": {
      "enabled": true,
      "cluster_radius_km": 50,
      "min_location_photos": 5
    }
  },
  "immich": {
    "cli_path": "immich",
    "server_url": "http://localhost:2283"
  }
}
```

### Adding New Devices

To add a new photo source device:

1. **Edit configuration:**
   ```json
   "source_devices": {
     "Calvin": "/Volumes/Calvin",
     "NewDevice": "/Volumes/NewDeviceName"
   }
   ```

2. **Restart the daemon:**
   ```bash
   ./calvin_control.sh restart
   ```

### Adding New Destinations

To change or add destination drives:

1. **Update destination path:**
   ```json
   "destination": "/Volumes/NewDestinationDrive"
   ```

2. **Ensure the drive has required folders or they'll be created automatically**

## 🌍 Location Expansion

### Adding New Cities/Locations

Edit `calvin_photo_sync_optimized.py` in the `get_location_name()` method:

```python
# Simple location mapping (you could use a proper geocoding API)  
locations = [
    # Existing locations
    (37.7749, -122.4194, 100, "San-Francisco"),
    (34.0522, -118.2437, 100, "Los-Angeles"),
    
    # Add your new locations here
    (40.7831, -73.9712, 50, "New-York-Central-Park"),
    (25.7617, -80.1918, 100, "Miami"),
    (41.8781, -87.6298, 100, "Chicago"),
    (47.6062, -122.3321, 100, "Seattle"),
    
    # International
    (48.8566, 2.3522, 100, "Paris"),
    (51.5074, -0.1278, 100, "London"),
    (35.6762, 139.6503, 100, "Tokyo"),
    (52.5200, 13.4050, 100, "Berlin"),
]
```

**Location format:** `(latitude, longitude, radius_km, "Album-Name")`

**Tips:**
- Use larger radius (100km) for cities, smaller (25-50km) for specific landmarks
- Album names should be hyphenated (no spaces)
- Get coordinates from Google Maps or GPS tools

### Using Online Geocoding (Advanced)

For automatic location detection, you can integrate geocoding services:

```python
def get_location_name_online(self, gps_coords):
    """Get location name using online geocoding service"""
    try:
        import requests
        lat, lon = gps_coords['latitude'], gps_coords['longitude']
        
        # Example with OpenStreetMap Nominatim (free)
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=10"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if 'address' in data:
            city = data['address'].get('city') or data['address'].get('town') or data['address'].get('village')
            country = data['address'].get('country_code', '').upper()
            if city:
                return f"{city}-{country}".replace(' ', '-')
    except Exception as e:
        logger.warning(f"Online geocoding failed: {e}")
    
    return None
```

## 🎮 Usage

### Automatic Mode (Recommended)

Once installed, the system runs automatically:

1. **Connect your photo device** (e.g., Calvin)
2. **Receive notification**: "Device Calvin connected - starting enhanced photo sync with GPS detection..."
3. **Wait for completion notification** with statistics
4. **Check Immich** for new albums with GPS-based names

### Manual Control

Use the control script for manual operations:

```bash
# Check daemon status
./calvin_control.sh status

# View recent activity
./calvin_control.sh logs

# Force sync a device right now
./calvin_control.sh force

# Get device information
./calvin_control.sh info

# Stop/start daemon
./calvin_control.sh stop
./calvin_control.sh start

# Reset sync history (forces re-sync)
./calvin_control.sh reset
```

### Manual Sync (One-time)

For one-time manual syncing without the daemon:

```bash
# Dry run (preview only)
python3 calvin_photo_sync_optimized.py --dry-run

# Actual sync
python3 calvin_photo_sync_optimized.py

# Sync specific device
python3 calvin_photo_sync_optimized.py --device Calvin

# Test with limited photos
python3 calvin_photo_sync_optimized.py --test --dry-run
```

## 📊 Monitoring & Logs

### Primary Log File
```bash
# Real-time monitoring
tail -f ~/.calvin_photo_sync.log

# Recent entries
tail -20 ~/.calvin_photo_sync.log

# Search for errors
grep ERROR ~/.calvin_photo_sync.log
```

### Daemon System Logs
```bash
# Stdout logs
tail ~/.calvin_daemon.out.log

# Error logs  
tail ~/.calvin_daemon.err.log

# Check daemon status
launchctl list | grep calvin
```

### Log Levels and Content

The logs include:
- **INFO**: Device connections, sync start/completion, statistics
- **WARNING**: Non-critical issues, fallback actions
- **ERROR**: Sync failures, configuration problems
- **DEBUG**: Detailed processing information (enable by modifying logging level)

### Key Log Patterns to Watch

```bash
# Successful connections
grep "New device detected" ~/.calvin_photo_sync.log

# Sync completions
grep "Sync completed" ~/.calvin_photo_sync.log  

# Upload statistics
grep "photos uploaded" ~/.calvin_photo_sync.log

# Errors requiring attention
grep -E "(ERROR|Failed)" ~/.calvin_photo_sync.log
```

## 🔧 Advanced Configuration

### Trip Detection Fine-Tuning

Adjust these parameters based on your photography patterns:

```json
"trip_detection": {
  "short_gap_hours": 8,        // Increase for longer daily breaks
  "long_gap_days": 3,          // Decrease for shorter trip consolidation
  "min_photos_per_trip": 3,    // Minimum photos to create an album
  "gps_clustering": {
    "cluster_radius_km": 50,   // Larger = more liberal location grouping
    "min_location_photos": 5   // GPS photos needed for location detection
  }
}
```

**Common Adjustments:**
- **Travel photographer**: `short_gap_hours: 12, long_gap_days: 5, cluster_radius_km: 100`
- **Event photographer**: `short_gap_hours: 4, long_gap_days: 1, cluster_radius_km: 25`
- **Vacation photographer**: `short_gap_hours: 10, long_gap_days: 7, cluster_radius_km: 75`

### Daemon Behavior

Edit `com.calvin.photosync.daemon.plist` to adjust daemon behavior:

```xml
<!-- Check interval (seconds) -->
<string>--interval</string>
<string>15</string>

<!-- Throttle restarts -->  
<key>ThrottleInterval</key>
<integer>5</integer>
```

### Notification Customization

Modify notification behavior in `calvin_daemon_enhanced.py`:

```python
def notify(self, message, title="Calvin Photo Sync"):
    # Custom notification logic
    script = f'display notification "{safe_message}" with title "{safe_title}" sound name "Glass"'
    
    # Alternative sounds: "Basso", "Blow", "Bottle", "Frog", "Funk", "Glass", "Hero", "Morse", "Ping", "Pop", "Purr", "Sosumi", "Submarine", "Tink"
```

## 🛠️ Troubleshooting

### Common Issues

**Daemon not starting:**
```bash
# Check logs
./calvin_control.sh logs

# Verify plist syntax
plutil ~/Library/LaunchAgents/com.calvin.photosync.daemon.plist

# Test daemon manually
python3 calvin_daemon_enhanced.py --test
```

**Device not detected:**
```bash
# Check mount points
ls /Volumes/

# Verify configuration
python3 calvin_daemon_enhanced.py --info

# Test permissions
ls -la /Volumes/YourDevice/
```

**Immich upload failing:**
```bash
# Test Immich CLI directly
immich server-info

# Re-authenticate if needed
immich login-key <server-url> <api-key>

# Check for CLI updates
npm update -g @immich/cli
```

**GPS location not detected:**
```bash
# Check if photos have GPS data
python3 -c "
from calvin_photo_sync_optimized import PhotoMetadata
import sys
metadata = PhotoMetadata.get_exif_data(sys.argv[1])
gps = PhotoMetadata.get_gps_data(metadata)
print(f'GPS: {gps}')
" /path/to/photo.jpg
```

### Reset Everything

If you need to start fresh:

```bash
# Stop daemon
./calvin_control.sh stop

# Remove daemon
rm ~/Library/LaunchAgents/com.calvin.photosync.daemon.plist

# Clear history and logs
rm ~/.calvin_sync_history.json ~/.calvin_photo_sync.log

# Remove configuration (will recreate with defaults)
rm ~/.calvin_photo_sync.json

# Reinstall
./setup_calvin_daemon.sh
```

## 📁 Repository Structure

```
calvin-photo-sync/
├── README.md                          # This file
├── calvin_photo_sync_optimized.py     # Main sync engine with GPS intelligence
├── calvin_daemon_enhanced.py          # Device monitoring daemon
├── calvin_control.sh                  # Easy control script
├── setup_calvin_daemon.sh            # Installation script  
├── com.calvin.photosync.daemon.plist # macOS LaunchAgent configuration
├── docs/
│   ├── EXAMPLES.md                    # Usage examples and scenarios
│   ├── API.md                         # Python API documentation
│   └── CONTRIBUTING.md                # Development guidelines
└── tests/
    ├── test_trip_detection.py         # Trip detection unit tests
    └── test_gps_parsing.py            # GPS parsing tests
```

## 🤝 Contributing

Contributions welcome! Please see `docs/CONTRIBUTING.md` for development guidelines.

### Development Setup

```bash
# Clone repository
git clone <repo-url>
cd calvin-photo-sync

# Install development dependencies
pip3 install -r requirements-dev.txt

# Run tests
python3 -m pytest tests/

# Test daemon manually
python3 calvin_daemon_enhanced.py --test
```

### Adding Features

Common enhancement areas:
- **New location detection methods** (online geocoding APIs)
- **Additional photo source formats** (cloud services, network drives)  
- **Enhanced trip detection algorithms** (activity recognition, landmark detection)
- **Integration with other photo management systems** (Google Photos, Adobe Lightroom)

## 📄 License

MIT License - feel free to modify and distribute.

## 🆘 Support

- **Issues**: Please create GitHub issues for bugs or feature requests
- **Logs**: Always include relevant log excerpts when reporting issues
- **Configuration**: Share your (sanitized) config file for configuration-related issues

---

**Created with ❤️ for intelligent photo organization**