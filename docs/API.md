# Calvin Photo Sync - API Documentation

This document describes the Python API for developers who want to integrate with or extend Calvin Photo Sync.

## Core Classes

### PhotoSyncConfig

Manages configuration loading, saving, and validation.

```python
from calvin_photo_sync_optimized import PhotoSyncConfig

# Initialize with default or custom config path
config = PhotoSyncConfig("~/.calvin_photo_sync.json")

# Access configuration
print(config.config['source_devices'])
print(config.config['trip_detection']['short_gap_hours'])

# Update configuration
config.config['trip_detection']['short_gap_hours'] = 10
config.save_config()
```

**Methods:**
- `load_config()` - Load configuration from file or create defaults
- `save_config(config=None)` - Save configuration to file

### OptimizedCalvinPhotoSync

Main synchronization engine with GPS-aware trip detection.

```python
from calvin_photo_sync_optimized import OptimizedCalvinPhotoSync

# Create sync instance  
sync = OptimizedCalvinPhotoSync(dry_run=False)

# Run full sync
success = sync.run_optimized_sync("Calvin")

# Access statistics
print(f"Photos copied: {sync.stats['photos_copied']}")
print(f"Trips detected: {sync.stats['trips_detected']}")
print(f"Photos uploaded: {sync.stats['photos_uploaded']}")
```

**Constructor Parameters:**
- `dry_run` (bool): Preview mode, no actual file operations

**Methods:**
- `run_optimized_sync(device_name=None)` - Execute full sync process
- `find_source_device(device_name=None)` - Locate and validate source device
- `notify(message, title)` - Send macOS notification

**Properties:**
- `stats` (dict): Sync statistics and results
- `config` (PhotoSyncConfig): Configuration instance

### LocalTripDetector

Enhanced trip detection with GPS clustering and flexible time windows.

```python
from calvin_photo_sync_optimized import LocalTripDetector

# Initialize with configuration
trip_config = {
    'short_gap_hours': 8,
    'long_gap_days': 3, 
    'min_photos_per_trip': 3,
    'gps_clustering': {
        'enabled': True,
        'cluster_radius_km': 50,
        'min_location_photos': 5
    }
}

detector = LocalTripDetector(trip_config)

# Analyze photos and organize into trips
photos_metadata = [...]  # List of photo metadata dicts
organized_files = detector.analyze_and_organize_photos(
    staging_path, destination_base, dry_run=False
)
```

**Methods:**
- `analyze_and_organize_photos(staging_path, destination_base, dry_run)` - Main processing method
- `group_photos_by_enhanced_trips(photos_metadata)` - Group photos using GPS + time logic
- `detect_location_change(current_trip_photos, new_photo)` - Check if location significantly changed
- `calculate_distance_km(gps1, gps2)` - Calculate distance between GPS coordinates
- `get_location_name(gps_coords)` - Get human-readable location name
- `get_trip_info(trip_data)` - Generate trip information with naming

### PhotoMetadata

Utility class for extracting metadata from photos.

```python
from calvin_photo_sync_optimized import PhotoMetadata

# Extract EXIF data
exif_data = PhotoMetadata.get_exif_data("/path/to/photo.jpg")

# Get GPS coordinates  
gps_data = PhotoMetadata.get_gps_data(exif_data)
print(gps_data)  # {'latitude': 37.7749, 'longitude': -122.4194}

# Get photo creation date
photo_date = PhotoMetadata.get_photo_datetime("/path/to/photo.jpg")
print(photo_date)  # datetime object
```

**Static Methods:**
- `get_exif_data(image_path)` - Extract EXIF data dictionary
- `get_gps_data(exif_data)` - Parse GPS coordinates from EXIF
- `get_photo_datetime(image_path)` - Get creation datetime

### EnhancedDeviceMonitor

Daemon class for monitoring device connections and triggering automatic sync.

```python
from calvin_daemon_enhanced import EnhancedDeviceMonitor

# Initialize monitor
monitor = EnhancedDeviceMonitor()

# Check for connected devices
devices = monitor.get_connected_devices()
print(devices)  # {'Calvin': '/Volumes/Calvin'}

# Get device information
device_info = monitor.get_device_info("Calvin")
print(device_info['estimated_photos'])

# Run sync for device
success = monitor.run_sync_for_device("Calvin")
```

**Methods:**
- `get_connected_devices()` - Get currently connected devices
- `check_for_new_devices()` - Check for newly connected devices  
- `get_device_info(device_name)` - Get detailed device information
- `run_sync_for_device(device_name)` - Execute sync for specific device
- `should_sync_device(device_name)` - Check if device should be synced
- `start_monitoring(check_interval)` - Start continuous monitoring
- `notify(message, title)` - Send system notification

## Data Structures

### Photo Metadata Dictionary

```python
photo_metadata = {
    'path': Path('/path/to/photo.jpg'),
    'datetime': datetime(2025, 5, 17, 14, 30, 0),
    'gps': {
        'latitude': 37.7749,
        'longitude': -122.4194
    }
}
```

### Trip Data Structure

```python
trip_data = {
    'photos': [photo_metadata1, photo_metadata2, ...],
    'reason': 'Location change after 12.5h gap'
}
```

### Trip Information

```python
trip_info = {
    'name': '2025-05-17-San-Francisco',
    'start_date': datetime(2025, 5, 17, 9, 0, 0),
    'end_date': datetime(2025, 5, 17, 18, 30, 0), 
    'photo_count': 45,
    'days_span': 1,
    'gps_photos': 42,
    'reason': 'Trip detection reason',
    'location_name': 'San-Francisco'
}
```

### Sync Statistics

```python
sync_stats = {
    'photos_found': 150,
    'photos_copied': 150, 
    'photos_organized': 150,
    'photos_uploaded': 145,
    'trips_detected': 3,
    'errors': ['Upload failed for IMG_001.jpg']
}
```

## Configuration Schema

### Main Configuration

```python
config_schema = {
    'source_devices': {
        'DeviceName': '/Volumes/DeviceName'  # Device mapping
    },
    'destination': '/Volumes/Destination',   # Destination drive
    'folders': {
        'staging': 'Photo Staging',          # Temporary processing  
        'new_photos': 'New Photos',          # Organized photos
        'uploaded_photos': 'Uploaded Photos' # Archived photos
    },
    'photo_extensions': [                    # Supported file types
        '.jpg', '.jpeg', '.png', '.heic', 
        '.raw', '.cr2', '.nef', '.mov', '.mp4'
    ],
    'scanning': {
        'common_photo_dirs': [               # Directories to scan
            'DCIM', 'Photos', 'Pictures'
        ],
        'max_scan_depth': 10,                # Max directory depth
        'batch_size': 50                     # Processing batch size
    },
    'immich': {
        'cli_path': 'immich',                # CLI command path
        'server_url': 'http://localhost:2283' # Server URL
    },
    'trip_detection': {
        'short_gap_hours': 8,                # Short break threshold
        'long_gap_days': 3,                  # Long break threshold  
        'min_photos_per_trip': 3,            # Minimum trip size
        'gps_clustering': {
            'enabled': True,                 # Enable GPS grouping
            'cluster_radius_km': 50,         # Location cluster size
            'min_location_photos': 5         # Min GPS photos needed
        }
    },
    'notifications': {
        'enabled': True,                     # Enable notifications
        'sound': True                        # Play notification sound
    }
}
```

## Usage Examples

### Custom Trip Detection

```python
from calvin_photo_sync_optimized import LocalTripDetector

# Custom configuration for event photography
event_config = {
    'short_gap_hours': 2,
    'long_gap_days': 1,
    'min_photos_per_trip': 10,
    'gps_clustering': {
        'enabled': True,
        'cluster_radius_km': 10,  # Tight clustering
        'min_location_photos': 3
    }
}

detector = LocalTripDetector(event_config)

# Process photos with custom logic
organized_files = detector.analyze_and_organize_photos(
    staging_path="/tmp/photos",
    destination_base="/Volumes/Events/New",
    dry_run=False
)
```

### Manual Photo Processing

```python
from calvin_photo_sync_optimized import PhotoMetadata
from pathlib import Path

# Process individual photos
photo_path = Path("/Volumes/Calvin/DCIM/IMG_001.jpg")

# Extract metadata
exif_data = PhotoMetadata.get_exif_data(photo_path)
gps_data = PhotoMetadata.get_gps_data(exif_data) 
photo_date = PhotoMetadata.get_photo_datetime(photo_path)

print(f"Photo taken: {photo_date}")
if gps_data:
    print(f"Location: {gps_data['latitude']}, {gps_data['longitude']}")
```

### Custom Device Monitoring

```python
from calvin_daemon_enhanced import EnhancedDeviceMonitor
import time

# Create custom monitor
monitor = EnhancedDeviceMonitor()

# Override device detection logic
def custom_should_sync(device_name):
    # Custom logic for when to sync
    if device_name == "Calvin":
        return True  # Always sync Calvin
    elif device_name == "iPhone":
        # Only sync iPhone during work hours
        hour = time.localtime().tm_hour
        return 9 <= hour <= 17
    return False

# Patch method
monitor.should_sync_device = custom_should_sync

# Start monitoring with custom logic
monitor.start_monitoring(check_interval=5)
```

### Batch Processing Multiple Devices

```python
from calvin_photo_sync_optimized import OptimizedCalvinPhotoSync

devices = ["Calvin", "CanonSD", "DroneSD"] 

for device in devices:
    print(f"Processing device: {device}")
    
    sync = OptimizedCalvinPhotoSync(dry_run=False)
    success = sync.run_optimized_sync(device)
    
    if success:
        stats = sync.stats
        print(f"✅ {device}: {stats['photos_copied']} photos, {stats['trips_detected']} trips")
    else:
        print(f"❌ {device}: Sync failed")
```

## Error Handling

### Exception Types

The system uses standard Python exceptions:

- `FileNotFoundError` - Device or destination not found
- `PermissionError` - Access denied to files/directories  
- `subprocess.CalledProcessError` - External command failures (Immich CLI)
- `json.JSONDecodeError` - Configuration file parsing errors
- `ValueError` - Invalid configuration values
- `OSError` - General I/O errors

### Error Recovery Patterns

```python
from calvin_photo_sync_optimized import OptimizedCalvinPhotoSync

try:
    sync = OptimizedCalvinPhotoSync(dry_run=False)
    success = sync.run_optimized_sync("Calvin")
    
except FileNotFoundError as e:
    print(f"Device not found: {e}")
    # Handle device connection issues
    
except PermissionError as e:
    print(f"Permission denied: {e}")  
    # Handle access rights issues
    
except subprocess.CalledProcessError as e:
    print(f"Command failed: {e}")
    # Handle external tool failures
    
except Exception as e:
    print(f"Unexpected error: {e}")
    # Handle unexpected issues
    
finally:
    # Cleanup if needed
    if 'sync' in locals():
        print(f"Final stats: {sync.stats}")
```

## Extension Points

### Custom Location Detection

```python
class CustomLocationDetector(LocalTripDetector):
    def get_location_name(self, gps_coords):
        """Custom location detection logic"""
        # Try online geocoding first
        online_name = self.get_online_location(gps_coords)
        if online_name:
            return online_name
            
        # Fall back to built-in mapping
        return super().get_location_name(gps_coords)
    
    def get_online_location(self, gps_coords):
        """Use online service for location names"""
        # Implement custom geocoding logic
        pass
```

### Custom Notification Handler

```python
class CustomNotificationSync(OptimizedCalvinPhotoSync):
    def notify(self, message, title="Calvin Photo Sync"):
        """Custom notification logic"""
        # Send to Slack, email, etc.
        super().notify(message, title)  # Still send system notification
        
        # Custom notification logic
        import requests
        slack_webhook = "https://hooks.slack.com/..."
        requests.post(slack_webhook, json={
            'text': f"{title}: {message}"
        })
```

### Custom File Organization

```python
class CustomFileOrganizer(LocalTripDetector):
    def get_trip_info(self, trip_data):
        """Custom trip naming logic"""
        info = super().get_trip_info(trip_data)
        
        # Add custom naming logic
        photos = trip_data['photos']
        if len(photos) > 100:
            info['name'] += "-Large-Collection"
        elif any('wedding' in str(p['path']).lower() for p in photos):
            info['name'] += "-Wedding"
            
        return info
```