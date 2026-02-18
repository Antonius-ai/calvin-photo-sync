#!/usr/bin/env python3
"""
Calvin Photo Sync - Optimized for large drives
Minimal processing on source drive, heavy lifting on destination
"""

import os
import sys
import json
import shutil
import hashlib
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import argparse

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
except ImportError:
    print("Installing required dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "Pillow", "--break-system-packages"], check=True)
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS

class PhotoSyncConfig:
    """Configuration management for photo sync"""
    
    def __init__(self, config_path="~/.calvin_photo_sync.json"):
        self.config_path = Path(config_path).expanduser()
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file or create default"""
        default_config = {
            "source_devices": {
                "Calvin": "/Volumes/Calvin",
                # Add more devices as needed
            },
            "destination": "/Volumes/Rainbow",
            "folders": {
                "staging": "Photo Staging",  # New: staging area for processing
                "new_photos": "New Photos",
                "uploaded_photos": "Uploaded Photos"
            },
            "photo_extensions": [".jpg", ".jpeg", ".png", ".heic", ".raw", ".cr2", ".nef", ".mov", ".mp4"],
            "scanning": {
                "common_photo_dirs": ["DCIM", "Photos", "Pictures", "Camera", "IMG", "Images"],
                "max_scan_depth": 10,  # Don't go too deep into folder structures
                "batch_size": 50,      # Process in batches to show progress
                "quick_scan": True     # Stop at first photo directory found
            },
            "immich": {
                "cli_path": "immich",
                "server_url": "http://localhost:2283",
                "email": "antonius.abooboo@gmail.com",
                "password": "LeastRecentlyUsed1337"
            },
            "trip_detection": {
                "short_gap_hours": 8,
                "long_gap_days": 3,
                "min_photos_per_trip": 3,
                "gps_clustering": {
                    "enabled": True,
                    "cluster_radius_km": 50,
                    "min_location_photos": 5,
                    "location_weight": 0.7
                }
            },
            "notifications": {
                "enabled": True,
                "sound": True
            }
        }
        
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        else:
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config=None):
        """Save configuration to file"""
        if config:
            self.config = config
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)

class FastScanner:
    """Optimized scanner that minimizes source drive access"""
    
    def __init__(self, config):
        self.config = config
        self.photo_extensions = set(ext.lower() for ext in config['photo_extensions'])
    
    def find_all_directories_with_photos(self, source_path):
        """Find ALL directories containing photos with full depth search"""
        photo_dirs = []
        
        try:
            print(f"Full scan of {source_path} for photo directories...")
            print("This may take a moment for large drives...")
            
            def scan_directory(directory, depth=0):
                """Recursively scan directory for photos"""
                found_photos_here = False
                subdirs_to_scan = []
                
                try:
                    # Get items in this directory
                    items = list(directory.iterdir())
                    
                    # Check for photo files in this directory
                    for item in items:
                        if item.is_file():
                            if item.suffix.lower() in self.photo_extensions:
                                found_photos_here = True
                                break
                        elif item.is_dir():
                            subdirs_to_scan.append(item)
                    
                    # If this directory has photos, add it to our list
                    if found_photos_here:
                        photo_dirs.append(directory)
                        print(f"{'  ' * depth}📁 Found photos in: {directory.relative_to(source_path)}")
                    
                    # Recursively scan subdirectories (but limit depth for sanity)
                    if depth < self.config['scanning']['max_scan_depth']:
                        for subdir in subdirs_to_scan:
                            scan_directory(subdir, depth + 1)
                    
                except (PermissionError, OSError) as e:
                    print(f"{'  ' * depth}❌ Cannot access: {directory.name} ({e})")
                    pass
            
            # Start scanning from root
            scan_directory(source_path)
            
            print(f"Found {len(photo_dirs)} directories containing photos")
            return photo_dirs
            
        except Exception as e:
            print(f"Error during full scan: {e}")
            return []
    
    def copy_all_photos(self, photo_dirs, staging_path, dry_run=False, max_photos=None):
        """Copy all photos from discovered directories"""
        batch_size = self.config['scanning']['batch_size']
        total_copied = 0
        
        if not dry_run:
            staging_path.mkdir(parents=True, exist_ok=True)
        
        for photo_dir in photo_dirs:
            relative_path = photo_dir.relative_to(Path(photo_dirs[0]).anchor)
            print(f"Processing: {relative_path}")
            
            try:
                # Get all files in this directory
                all_files = [f for f in photo_dir.iterdir() if f.is_file()]
                
                # Filter for photo files (exclude Apple metadata files)
                photo_files = []
                for file_path in all_files:
                    # Skip Apple metadata files and other system files
                    if (file_path.suffix.lower() in self.photo_extensions and 
                        not file_path.name.startswith('._') and
                        not file_path.name.startswith('.DS_Store')):
                        photo_files.append(file_path)
                
                if not photo_files:
                    continue
                    
                print(f"  📸 {len(photo_files)} photos found")
                
                # Process in batches with progress
                for i in range(0, len(photo_files), batch_size):
                    batch = photo_files[i:i + batch_size]
                    batch_end = min(i + batch_size, len(photo_files))
                    
                    if len(photo_files) > batch_size:
                        print(f"    Batch {i//batch_size + 1}: copying {i+1}-{batch_end}")
                    
                    for photo_file in batch:
                        # Handle name conflicts by preserving directory structure info
                        base_name = photo_file.stem
                        extension = photo_file.suffix
                        
                        # Create unique name if needed
                        dest_path = staging_path / photo_file.name
                        counter = 1
                        
                        while dest_path.exists() and not dry_run:
                            # Check if it's the same file
                            try:
                                if photo_file.stat().st_size == dest_path.stat().st_size:
                                    print(f"    ↪️ Skipped duplicate: {photo_file.name}")
                                    break
                            except OSError:
                                pass
                            
                            # Create new name with counter
                            dest_path = staging_path / f"{base_name}_{counter}{extension}"
                            counter += 1
                        else:
                            # Copy the file
                            if not dry_run:
                                if not dest_path.exists():
                                    shutil.copy2(photo_file, dest_path)
                                    # Preserve original creation time from EXIF if possible
                                    self.preserve_creation_time(photo_file, dest_path)
                                    total_copied += 1
                                    if total_copied % 10 == 0:  # Progress indicator
                                        print(f"    📋 Copied {total_copied} photos so far...")
                                    
                                    # Stop if we've reached max_photos limit
                                    if max_photos and total_copied >= max_photos:
                                        print(f"    🛑 Reached limit of {max_photos} photos")
                                        return total_copied
                            else:
                                print(f"    📋 Would copy: {photo_file.name}")
                                total_copied += 1
                                
                                # Stop if we've reached max_photos limit
                                if max_photos and total_copied >= max_photos:
                                    print(f"    🛑 Would reach limit of {max_photos} photos")
                                    return total_copied
                
            except Exception as e:
                print(f"❌ Error processing {photo_dir}: {e}")
                continue
        
        return total_copied
    
    def preserve_creation_time(self, source_file, dest_file):
        """Preserve original creation time using EXIF data if available"""
        try:
            from PIL import Image
            # Try to get creation time from EXIF
            with Image.open(source_file) as img:
                exif_data = img._getexif()
                if exif_data:
                    for field in ['DateTimeOriginal', 'DateTime', 'DateTimeDigitized']:
                        if field in exif_data:
                            try:
                                creation_time = datetime.strptime(exif_data[field], '%Y:%m:%d %H:%M:%S')
                                timestamp = creation_time.timestamp()
                                os.utime(dest_file, (timestamp, timestamp))
                                return
                            except (ValueError, KeyError):
                                continue
        except Exception:
            pass
        
        # Fallback: preserve original file times using shutil.copy2 (already done)

class PhotoMetadata:
    """Extract and analyze photo metadata - optimized for local processing"""
    
    @staticmethod
    def get_exif_data(image_path):
        """Extract EXIF data from image"""
        try:
            with Image.open(image_path) as image:
                exif_data = image._getexif()
                if exif_data is not None:
                    exif = {}
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        exif[tag] = value
                    return exif
        except Exception as e:
            # Silently fail for unsupported formats
            pass
        return {}
    
    @staticmethod
    def get_gps_data(exif_data):
        """Extract GPS coordinates from EXIF data"""
        gps_info = exif_data.get('GPSInfo')
        if not gps_info:
            return None
        
        def convert_to_degrees(value):
            d, m, s = value
            return d + (m / 60.0) + (s / 3600.0)
        
        try:
            lat = convert_to_degrees(gps_info[2])
            if gps_info[1] == 'S':
                lat = -lat
            
            lon = convert_to_degrees(gps_info[4])
            if gps_info[3] == 'W':
                lon = -lon
            
            return {'latitude': lat, 'longitude': lon}
        except (KeyError, TypeError, ValueError):
            return None
    
    @staticmethod
    def get_photo_datetime(image_path):
        """Get photo creation datetime"""
        try:
            exif_data = PhotoMetadata.get_exif_data(image_path)
            
            # Try various EXIF datetime fields
            for field in ['DateTimeOriginal', 'DateTime', 'DateTimeDigitized']:
                if field in exif_data:
                    try:
                        return datetime.strptime(exif_data[field], '%Y:%m:%d %H:%M:%S')
                    except ValueError:
                        continue
            
            # Fallback to file modification time
            return datetime.fromtimestamp(os.path.getmtime(image_path))
        except Exception:
            return datetime.fromtimestamp(os.path.getmtime(image_path))

class LocalTripDetector:
    """Enhanced trip detection with GPS clustering and flexible time windows"""
    
    def __init__(self, config):
        self.short_gap_hours = config.get('short_gap_hours', 8)
        self.long_gap_days = config.get('long_gap_days', 3)
        self.min_photos_per_trip = config.get('min_photos_per_trip', 3)
        self.gps_config = config.get('gps_clustering', {
            'enabled': True,
            'cluster_radius_km': 50,
            'min_location_photos': 5,
            'location_weight': 0.7
        })
    
    def analyze_and_organize_photos(self, staging_path, destination_base, dry_run=False):
        """Analyze staged photos and organize into trip folders"""
        
        print(f"Analyzing photos in {staging_path}...")
        
        # Get all photos from staging
        photo_files = []
        for ext in ['.jpg', '.jpeg', '.png', '.heic', '.raw', '.cr2', '.nef']:
            photo_files.extend(staging_path.glob(f"*{ext}"))
            photo_files.extend(staging_path.glob(f"*{ext.upper()}"))
        
        print(f"Found {len(photo_files)} photos to analyze")
        
        if not photo_files:
            return []
        
        # Extract datetime and GPS for each photo (fast local operation)
        photos_metadata = []
        for i, photo in enumerate(photo_files):
            if i % 20 == 0:  # Progress indicator
                print(f"  Analyzed {i}/{len(photo_files)} photos...")
            
            dt = PhotoMetadata.get_photo_datetime(photo)
            exif_data = PhotoMetadata.get_exif_data(photo)
            gps = PhotoMetadata.get_gps_data(exif_data) if exif_data else None
            
            photos_metadata.append({
                'path': photo,
                'datetime': dt,
                'gps': gps
            })
        
        print(f"Completed metadata analysis for {len(photos_metadata)} photos")
        
        # Sort by datetime
        photos_metadata.sort(key=lambda x: x['datetime'])
        
        # Group into trips using enhanced logic
        trips = self.group_photos_by_enhanced_trips(photos_metadata)
        
        # Organize into trip folders
        organized_files = []
        for i, trip_data in enumerate(trips, 1):
            trip_info = self.get_trip_info(trip_data)
            trip_folder = destination_base / trip_info['name']
            
            print(f"Trip {i}: {trip_info['name']} ({trip_info['photo_count']} photos)")
            if trip_info.get('location_name'):
                print(f"  Location: {trip_info['location_name']}")
            
            if not dry_run:
                trip_folder.mkdir(parents=True, exist_ok=True)
            
            for photo_data in trip_data['photos']:
                photo_path = photo_data['path']
                dest_path = trip_folder / photo_path.name
                
                if not dry_run:
                    shutil.move(str(photo_path), str(dest_path))
                    organized_files.append(dest_path)
                else:
                    organized_files.append(dest_path)
                    print(f"  Would move: {photo_path.name} -> {trip_info['name']}/")
        
        return organized_files
    
    def group_photos_by_enhanced_trips(self, photos_metadata):
        """Enhanced trip grouping with GPS clustering"""
        if not photos_metadata:
            return []
        
        trips = []
        current_trip = [photos_metadata[0]]
        
        for i in range(1, len(photos_metadata)):
            current_photo = photos_metadata[i]
            prev_photo = photos_metadata[i-1]
            
            time_gap = current_photo['datetime'] - prev_photo['datetime']
            
            # Decision logic for trip boundaries
            should_start_new_trip = False
            
            # Rule 1: Long time gap always starts new trip
            if time_gap > timedelta(days=self.long_gap_days):
                should_start_new_trip = True
                reason = f"Long gap ({time_gap.days} days)"
            
            # Rule 2: Short gap + location change = new trip
            elif time_gap > timedelta(hours=self.short_gap_hours):
                if self.gps_config['enabled']:
                    # Check if location significantly changed
                    location_changed = self.detect_location_change(current_trip, current_photo)
                    if location_changed:
                        should_start_new_trip = True
                        reason = f"Location change after {time_gap.total_seconds()/3600:.1f}h gap"
                    else:
                        # Same location, extend trip
                        reason = f"Same location, extending trip despite {time_gap.total_seconds()/3600:.1f}h gap"
                else:
                    # No GPS, use old logic
                    should_start_new_trip = True
                    reason = f"Time gap ({time_gap.total_seconds()/3600:.1f}h)"
            else:
                reason = f"Continuing trip ({time_gap.total_seconds()/3600:.1f}h gap)"
            
            if should_start_new_trip:
                # Finalize current trip if it has enough photos
                if len(current_trip) >= self.min_photos_per_trip:
                    trips.append({
                        'photos': current_trip,
                        'reason': reason
                    })
                current_trip = [current_photo]
            else:
                current_trip.append(current_photo)
        
        # Add the last trip
        if len(current_trip) >= self.min_photos_per_trip:
            trips.append({
                'photos': current_trip,
                'reason': "Final trip"
            })
        
        return trips
    
    def detect_location_change(self, current_trip_photos, new_photo):
        """Detect if new photo represents a significant location change"""
        if not self.gps_config['enabled'] or not new_photo.get('gps'):
            return False
        
        # Get GPS coordinates of photos in current trip
        trip_gps_coords = [p['gps'] for p in current_trip_photos if p.get('gps')]
        
        if len(trip_gps_coords) < self.gps_config['min_location_photos']:
            return False  # Not enough GPS data to determine location
        
        # Calculate average location of current trip
        avg_lat = sum(coord['latitude'] for coord in trip_gps_coords) / len(trip_gps_coords)
        avg_lon = sum(coord['longitude'] for coord in trip_gps_coords) / len(trip_gps_coords)
        trip_center = {'latitude': avg_lat, 'longitude': avg_lon}
        
        # Check if new photo is within cluster radius
        distance = self.calculate_distance_km(trip_center, new_photo['gps'])
        
        return distance > self.gps_config['cluster_radius_km']
    
    def calculate_distance_km(self, gps1, gps2):
        """Calculate distance between two GPS coordinates in km"""
        import math
        
        if not gps1 or not gps2:
            return float('inf')
        
        # Haversine formula
        R = 6371  # Earth's radius in km
        
        lat1, lon1 = math.radians(gps1['latitude']), math.radians(gps1['longitude'])
        lat2, lon2 = math.radians(gps2['latitude']), math.radians(gps2['longitude'])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def get_location_name(self, gps_coords):
        """Get location name from GPS coordinates (simplified)"""
        if not gps_coords:
            return None
            
        lat, lon = gps_coords['latitude'], gps_coords['longitude']
        
        # Simple location mapping (you could use a proper geocoding API)
        locations = [
            # California
            (37.7749, -122.4194, 100, "San-Francisco"),
            (34.0522, -118.2437, 100, "Los-Angeles"),
            (32.7157, -117.1611, 100, "San-Diego"),
            
            # Hawaii
            (21.3099, -157.8581, 100, "Hawaii"),
            
            # New York
            (40.7128, -74.0060, 100, "New-York"),
            
            # International
            (48.8566, 2.3522, 100, "Paris"),
            (51.5074, -0.1278, 100, "London"),
            (35.6762, 139.6503, 100, "Tokyo"),
        ]
        
        for ref_lat, ref_lon, radius, name in locations:
            distance = self.calculate_distance_km({'latitude': lat, 'longitude': lon}, {'latitude': ref_lat, 'longitude': ref_lon})
            if distance <= radius:
                return name
        
        return None
    
    def get_trip_info(self, trip_data):
        """Generate trip information with enhanced naming and GPS location"""
        photos = trip_data['photos']
        reason = trip_data.get('reason', '')
        
        dates = [photo['datetime'] for photo in photos]
        start_date = min(dates)
        end_date = max(dates)
        
        # Create base trip name
        if start_date.date() == end_date.date():
            trip_name = start_date.strftime("%Y-%m-%d")
        else:
            days_span = (end_date - start_date).days
            if days_span <= 7:
                trip_name = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%m-%d')}"
            else:
                trip_name = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        
        # Add location info if available
        gps_photos = [p for p in photos if p.get('gps')]
        location_name = None
        
        if len(gps_photos) >= 5:  # Enough GPS data
            # Calculate center point
            avg_lat = sum(p['gps']['latitude'] for p in gps_photos) / len(gps_photos)
            avg_lon = sum(p['gps']['longitude'] for p in gps_photos) / len(gps_photos)
            
            # Get location name
            location_name = self.get_location_name({'latitude': avg_lat, 'longitude': avg_lon})
            
            if location_name:
                trip_name += f"-{location_name}"
        
        return {
            'name': trip_name,
            'start_date': start_date,
            'end_date': end_date,
            'photo_count': len(photos),
            'days_span': (end_date - start_date).days + 1,
            'gps_photos': len(gps_photos),
            'reason': reason,
            'location_name': location_name
        }

class OptimizedCalvinPhotoSync:
    """Optimized photo sync for large drives"""
    
    def __init__(self, dry_run=False):
        self.config = PhotoSyncConfig()
        self.dry_run = dry_run
        self.scanner = FastScanner(self.config.config)
        self.trip_detector = LocalTripDetector(self.config.config['trip_detection'])
        self.stats = {
            'photos_found': 0,
            'photos_copied': 0,
            'photos_organized': 0,
            'photos_uploaded': 0,
            'trips_detected': 0,
            'errors': []
        }
    
    def notify(self, message, title="Calvin Photo Sync"):
        """Send macOS notification"""
        if not self.config.config['notifications']['enabled']:
            return
        
        # Escape quotes in message and title for AppleScript
        safe_message = message.replace('"', '\\"')
        safe_title = title.replace('"', '\\"')
        
        script = f'display notification "{safe_message}" with title "{safe_title}"'
        
        if self.config.config['notifications']['sound']:
            script += ' sound name "Glass"'
        
        try:
            subprocess.run(['osascript', '-e', script], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Notification error: {e}")
            print(f"Notification: {title} - {message}")
    
    def find_source_device(self, device_name=None):
        """Find and validate source device"""
        devices = self.config.config['source_devices']
        
        if device_name and device_name in devices:
            path = Path(devices[device_name])
            if path.exists():
                return path
            else:
                print(f"Device '{device_name}' not found at {path}")
                return None
        
        # Auto-detect available devices
        for name, path in devices.items():
            device_path = Path(path)
            if device_path.exists():
                print(f"Found device: {name} at {device_path}")
                return device_path
        
        return None
    
    def upload_to_immich(self, photos):
        """Upload photos to Immich"""
        if not photos:
            return True
        
        immich_config = self.config.config['immich']
        
        try:
            # First, check if we need to authenticate
            if not self.dry_run:
                self.authenticate_immich()
            
            cmd = [immich_config['cli_path'], 'upload']
            
            if self.dry_run:
                cmd.append('--dry-run')
            
            # Add options for better organization
            cmd.extend(['--album', '--recursive'])
            
            # Add all photo paths
            for photo in photos:
                cmd.append(str(photo))
            
            print(f"Uploading {len(photos)} photos to Immich...")
            
            if not self.dry_run:
                result = subprocess.run(cmd, capture_output=True, text=True)
                print(f"Immich output: {result.stdout}")
                if result.stderr:
                    print(f"Immich stderr: {result.stderr}")
                
                if result.returncode == 0:
                    self.stats['photos_uploaded'] = len(photos)
                    return True
                else:
                    self.stats['errors'].append(f"Immich upload failed: {result.stderr}")
                    return False
            else:
                print(f"Would upload {len(photos)} photos to Immich")
                return True
        
        except FileNotFoundError:
            self.stats['errors'].append("Immich CLI not found. Please install and configure Immich CLI.")
            return False
    
    def authenticate_immich(self):
        """Authenticate with Immich using API key (requires manual setup)"""
        immich_config = self.config.config['immich']
        
        print("🔑 Immich authentication note:")
        print("   The Immich CLI requires an API key for authentication.")
        print("   Please generate an API key in your Immich server settings")
        print("   and run: immich login-key <server-url> <api-key>")
        print(f"   Server URL: {immich_config['server_url']}")
        if 'email' in immich_config:
            print(f"   Account: {immich_config['email']}")
        else:
            print("   Account: (configured via API key)")
        print()
        
        # Check if already authenticated
        try:
            result = subprocess.run([immich_config['cli_path'], 'server-info'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Already authenticated with Immich")
                return True
            else:
                print("❌ Not authenticated with Immich")
                print("   Please authenticate manually with API key")
                return False
        except Exception as e:
            print(f"Error checking Immich authentication: {e}")
            return False
    
    def move_to_uploaded(self, photos):
        """Move photos from New Photos to Uploaded Photos"""
        new_photos_base = Path(self.config.config['destination']) / self.config.config['folders']['new_photos']
        uploaded_photos_base = Path(self.config.config['destination']) / self.config.config['folders']['uploaded_photos']
        
        if not self.dry_run:
            uploaded_photos_base.mkdir(parents=True, exist_ok=True)
        
        for photo in photos:
            # Maintain relative path structure
            try:
                relative_path = photo.relative_to(new_photos_base)
                dest_path = uploaded_photos_base / relative_path
                
                if not self.dry_run:
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(photo), str(dest_path))
                    print(f"Moved: {relative_path}")
                else:
                    print(f"Would move: {relative_path}")
            except ValueError:
                # Path not relative to new_photos_base, skip
                print(f"Skipped moving {photo} (not in expected location)")
    
    def run_optimized_sync(self, device_name=None):
        """Run the optimized sync process"""
        start_time = time.time()
        
        print(f"Calvin Photo Sync - OPTIMIZED {'(DRY RUN)' if self.dry_run else ''}")
        print("=" * 60)
        
        # Find source device
        source_path = self.find_source_device(device_name)
        if not source_path:
            self.notify("No source device found", "Error")
            return False
        
        # Check destination
        destination_root = Path(self.config.config['destination'])
        if not destination_root.exists():
            self.notify("Rainbow drive not found", "Error")
            return False
        
        staging_path = destination_root / self.config.config['folders']['staging']
        new_photos_base = destination_root / self.config.config['folders']['new_photos']
        
        # Check if we have photos already in staging (resume from interruption)
        existing_photos = []
        if staging_path.exists():
            for ext in ['.jpg', '.jpeg', '.png', '.heic', '.raw', '.cr2', '.nef', '.mp4', '.mov']:
                existing_photos.extend(staging_path.glob(f"*{ext}"))
                existing_photos.extend(staging_path.glob(f"*{ext.upper()}"))
        
        if existing_photos and not self.dry_run:
            print(f"RESUMING: Found {len(existing_photos)} photos in staging area")
            print("Skipping Phase 1 (copy) - proceeding to analysis")
            copied_count = len(existing_photos)
            self.stats['photos_copied'] = copied_count
        else:
            # Phase 1: Quick scan and copy from source drive
            print("PHASE 1: Fast copy from source drive")
            print("-" * 40)
            
            photo_dirs = self.scanner.find_all_directories_with_photos(source_path)
            if not photo_dirs:
                print("No directories containing photos found")
                self.notify("No photos found", "Calvin Photo Sync")
                return True
            
            max_photos = None  # Full sync - no limit
            copied_count = self.scanner.copy_all_photos(photo_dirs, staging_path, self.dry_run, max_photos=max_photos)
            self.stats['photos_copied'] = copied_count
            
            print(f"Copied {copied_count} photos to staging area")
        
        # Phase 2: Local processing on Rainbow
        print(f"\nPHASE 2: Local analysis and organization")
        print("-" * 40)
        
        organized_photos = self.trip_detector.analyze_and_organize_photos(
            staging_path, new_photos_base, self.dry_run
        )
        self.stats['photos_organized'] = len(organized_photos)
        
        # Count trips
        if organized_photos:
            trip_folders = set(photo.parent for photo in organized_photos)
            self.stats['trips_detected'] = len(trip_folders)
        
        # Phase 3: Upload to Immich
        if organized_photos or self.dry_run:
            print(f"\nPHASE 3: Upload to Immich")
            print("-" * 40)
            
            upload_success = self.upload_to_immich(organized_photos if not self.dry_run else organized_photos[:5])
            
            if upload_success and not self.dry_run:
                # Phase 4: Move to uploaded folder
                print(f"\nPHASE 4: Archive uploaded photos")
                print("-" * 40)
                self.move_to_uploaded(organized_photos)
        
        # Clean up staging area
        if not self.dry_run and staging_path.exists():
            try:
                # Remove empty staging directory
                if not any(staging_path.iterdir()):
                    staging_path.rmdir()
                    print("Cleaned up staging area")
            except OSError:
                pass  # Directory not empty or other issue, leave it
        
        # Report results
        duration = time.time() - start_time
        self.report_results(duration)
        
        return len(self.stats['errors']) == 0
    
    def report_results(self, duration):
        """Generate and display sync results"""
        stats = self.stats
        
        print("\n" + "=" * 60)
        print("SYNC RESULTS")
        print("=" * 60)
        print(f"Photos copied from source: {stats['photos_copied']}")
        print(f"Photos organized: {stats['photos_organized']}")
        print(f"Trips detected: {stats['trips_detected']}")
        print(f"Photos uploaded: {stats['photos_uploaded']}")
        print(f"Duration: {duration:.1f} seconds")
        
        if stats['errors']:
            print(f"Errors: {len(stats['errors'])}")
            for error in stats['errors']:
                print(f"  - {error}")
        
        # Send notification
        if stats['photos_copied'] > 0 or self.dry_run:
            if self.dry_run:
                message = f"Would process {stats['photos_copied']} photos in {stats['trips_detected']} trips"
            else:
                message = f"Synced {stats['photos_copied']} photos in {stats['trips_detected']} trips"
            
            self.notify(message, "Calvin Photo Sync Complete")

def main():
    parser = argparse.ArgumentParser(description='Calvin Photo Sync - Optimized for Large Drives')
    parser.add_argument('--device', '-d', help='Specific device name to sync from')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Preview actions without executing')
    parser.add_argument('--config', '-c', action='store_true', help='Show current configuration')
    parser.add_argument('--test', '-t', action='store_true', help='Test mode: process only 100 photos')
    
    args = parser.parse_args()
    
    if args.config:
        config = PhotoSyncConfig()
        print("Current Configuration:")
        print(json.dumps(config.config, indent=2))
        return
    
    sync = OptimizedCalvinPhotoSync(dry_run=args.dry_run)
    if args.test:
        sync.test_mode = True
        print("🧪 TEST MODE: Processing only 100 photos")
    success = sync.run_optimized_sync(args.device)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()