# Calvin Photo Sync - Usage Examples

This document provides real-world usage examples and common scenarios.

## 📸 Usage Scenarios

### Scenario 1: Weekend Trip Photography

**Setup:**
- Device: Canon camera with SD card mounted as "Calvin"
- Trip: 2-day weekend in San Francisco
- Photos: 150 photos over Friday evening to Sunday afternoon

**What happens automatically:**
1. Insert SD card → System detects "Calvin" connection
2. Notification: "Device Calvin connected - starting enhanced photo sync with GPS detection..."
3. System analyzes 150 photos, detects GPS coordinates around San Francisco
4. Creates single album: "2025-03-14 to 03-16-San-Francisco" 
5. Uploads all photos to Immich with preserved dates
6. Notification: "✅ Sync completed! 📸 150 photos copied 🗂️ 1 trip detected ☁️ 150 photos uploaded"

### Scenario 2: Multi-Week Vacation

**Setup:**
- Device: Phone camera with photos
- Trip: 3-week European tour (Paris → London → Rome)
- Photos: 800+ photos across multiple cities

**Expected album structure:**
- `2025-06-01 to 06-07-Paris` (Week 1 in Paris)
- `2025-06-08 to 06-14-London` (Week 2 in London)  
- `2025-06-15 to 06-21-Rome` (Week 3 in Rome)

**Why it works:** GPS location changes trigger new albums despite continuous shooting

### Scenario 3: Daily Life Photography

**Setup:**
- Device: Daily phone sync
- Pattern: Random photos throughout weeks
- Photos: Mixed locations, irregular timing

**Expected behavior:**
- Short breaks (meals, work, sleep) → Single day albums
- Weekend activities → Separate albums if different locations
- Long gaps (3+ days without photos) → Always new albums
- Home photos → Grouped by day/activity based on timing

## 🎛️ Configuration Examples

### Travel Photographer Profile
```json
{
  "trip_detection": {
    "short_gap_hours": 12,
    "long_gap_days": 5, 
    "min_photos_per_trip": 5,
    "gps_clustering": {
      "enabled": true,
      "cluster_radius_km": 100,
      "min_location_photos": 10
    }
  }
}
```
**Rationale:** Longer consolidation periods, larger location clusters, higher photo thresholds

### Event Photographer Profile  
```json
{
  "trip_detection": {
    "short_gap_hours": 4,
    "long_gap_days": 1,
    "min_photos_per_trip": 10, 
    "gps_clustering": {
      "enabled": true,
      "cluster_radius_km": 25,
      "min_location_photos": 5
    }
  }
}
```
**Rationale:** Tight grouping, small location radius, separate events clearly

### Family Vacation Profile
```json
{
  "trip_detection": {
    "short_gap_hours": 10,
    "long_gap_days": 7,
    "min_photos_per_trip": 3,
    "gps_clustering": {
      "enabled": true, 
      "cluster_radius_km": 75,
      "min_location_photos": 3
    }
  }
}
```
**Rationale:** Very permissive grouping for long family trips with many breaks

## 🗺️ Location Examples

### Adding Specific Landmarks
```python
# In get_location_name() method
locations = [
    # Existing cities...
    
    # Specific landmarks
    (40.7589, -73.9851, 5, "Times-Square"),
    (40.7505, -73.9934, 5, "Empire-State-Building"),
    (37.8199, -122.4783, 10, "Golden-Gate-Bridge"),
    (34.1341, -118.3215, 15, "Hollywood"),
    
    # National parks
    (44.4280, -110.5885, 50, "Yellowstone"),
    (36.1069, -112.1129, 30, "Grand-Canyon"),
    (37.8651, -119.5383, 25, "Yosemite"),
    
    # International destinations
    (48.8584, 2.2945, 2, "Eiffel-Tower"),
    (41.9028, 12.4964, 10, "Vatican-City"),
    (35.3606, 138.7274, 20, "Mount-Fuji"),
]
```

### Location Hierarchy (City → Landmark)
```python
def get_location_name_hierarchical(self, gps_coords):
    """Get most specific location name available"""
    lat, lon = gps_coords['latitude'], gps_coords['longitude']
    
    # Check landmarks first (smaller radius)
    landmarks = [
        (40.7589, -73.9851, 2, "Times-Square"),
        (37.8199, -122.4783, 5, "Golden-Gate-Bridge"),
    ]
    
    for ref_lat, ref_lon, radius, name in landmarks:
        distance = self.calculate_distance_km({'latitude': lat, 'longitude': lon}, 
                                            {'latitude': ref_lat, 'longitude': ref_lon})
        if distance <= radius:
            return name
    
    # Fall back to cities (larger radius)  
    cities = [
        (40.7128, -74.0060, 50, "New-York"),
        (37.7749, -122.4194, 50, "San-Francisco"),
    ]
    
    for ref_lat, ref_lon, radius, name in cities:
        distance = self.calculate_distance_km({'latitude': lat, 'longitude': lon},
                                            {'latitude': ref_lat, 'longitude': ref_lon})
        if distance <= radius:
            return name
    
    return None
```

## 🎮 Control Script Examples

### Daily Monitoring
```bash
# Morning check - see overnight activity
./calvin_control.sh status

# Check what happened with yesterday's sync
./calvin_control.sh logs | grep "$(date -v-1d '+%Y-%m-%d')"

# Quick device check before connecting camera
./calvin_control.sh info
```

### Troubleshooting Workflow
```bash
# Something seems wrong, check current status
./calvin_control.sh status

# Look at recent errors
./calvin_control.sh logs | grep ERROR

# Test device detection
./calvin_control.sh test

# Force a manual sync to see what happens
./calvin_control.sh force

# If needed, restart the daemon
./calvin_control.sh restart
```

### Preparing for Travel
```bash
# Before trip: reset history to ensure fresh sync
./calvin_control.sh reset

# After trip: check how many photos were processed
./calvin_control.sh logs | grep "photos copied"

# Verify all devices are detected
./calvin_control.sh info
```

## 📊 Log Analysis Examples

### Finding Sync Statistics
```bash
# Get summary of all syncs
grep "Sync completed" ~/.calvin_photo_sync.log

# Count photos processed in last week
grep "$(date -v-7d '+%Y-%m')" ~/.calvin_photo_sync.log | grep "photos copied" | awk '{sum += $4} END {print sum}'

# Find largest sync sessions
grep "photos copied" ~/.calvin_photo_sync.log | sort -k4 -nr | head -10
```

### Error Investigation
```bash
# Find all errors
grep ERROR ~/.calvin_photo_sync.log

# Look for network/upload issues
grep -i "upload\|immich\|network" ~/.calvin_photo_sync.log | grep -i error

# Check GPS processing issues
grep -i "gps\|location" ~/.calvin_photo_sync.log | grep -E "(error|warning)"
```

### Performance Monitoring
```bash
# Find slow syncs (duration > 60 seconds)
grep "Duration:" ~/.calvin_photo_sync.log | awk '$4 > 60 {print $0}'

# Monitor memory usage during sync
while true; do ps aux | grep calvin_daemon_enhanced | grep -v grep; sleep 5; done
```

## 🔄 Automation Examples

### Scheduled Health Checks
```bash
#!/bin/bash
# Add to crontab: 0 8 * * * ~/calvin_health_check.sh

echo "=== Daily Calvin Health Check ===" >> ~/calvin_health.log
date >> ~/calvin_health.log

# Check daemon status
if ./calvin_control.sh status | grep -q "running"; then
    echo "✅ Daemon is running" >> ~/calvin_health.log
else
    echo "❌ Daemon is not running - restarting" >> ~/calvin_health.log
    ./calvin_control.sh start >> ~/calvin_health.log 2>&1
fi

# Check recent errors
recent_errors=$(grep ERROR ~/.calvin_photo_sync.log | tail -5)
if [ -n "$recent_errors" ]; then
    echo "⚠️  Recent errors found:" >> ~/calvin_health.log
    echo "$recent_errors" >> ~/calvin_health.log
fi

echo "" >> ~/calvin_health.log
```

### Backup Configuration
```bash
#!/bin/bash
# Backup Calvin configuration and history
backup_dir="$HOME/calvin_backups/$(date +%Y-%m-%d)"
mkdir -p "$backup_dir"

cp ~/.calvin_photo_sync.json "$backup_dir/"
cp ~/.calvin_sync_history.json "$backup_dir/" 2>/dev/null
cp ~/.calvin_photo_sync.log "$backup_dir/"

echo "✅ Calvin configuration backed up to $backup_dir"
```

### Multi-Device Setup
```json
{
  "source_devices": {
    "Calvin": "/Volumes/Calvin",
    "CanonSD": "/Volumes/EOS_DIGITAL", 
    "iPhone": "/Volumes/iPhone",
    "DroneSD": "/Volumes/DRONE_SD"
  },
  "destination": "/Volumes/PhotoArchive"
}
```

**With device-specific rules:**
```python
# In calvin_daemon_enhanced.py
def get_device_specific_config(self, device_name):
    """Apply device-specific settings"""
    configs = {
        "Calvin": {
            "short_gap_hours": 8,
            "cluster_radius_km": 50
        },
        "DroneSD": {
            "short_gap_hours": 2,  # Tight grouping for drone flights
            "cluster_radius_km": 25
        },
        "iPhone": {
            "short_gap_hours": 12,  # Loose grouping for daily photos  
            "cluster_radius_km": 100
        }
    }
    
    return configs.get(device_name, self.config.config['trip_detection'])
```