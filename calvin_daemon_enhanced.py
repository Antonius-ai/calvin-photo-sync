#!/usr/bin/env python3
"""
Calvin Photo Sync Daemon - Enhanced version with GPS-aware trip detection
Monitors for device connections and triggers automatic sync
"""

import os
import sys
import time
import subprocess
import json
import logging
from pathlib import Path
from datetime import datetime
from calvin_photo_sync_optimized import OptimizedCalvinPhotoSync, PhotoSyncConfig

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path.home() / '.calvin_photo_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedDeviceMonitor:
    """Enhanced device monitor with smart sync capabilities"""
    
    def __init__(self):
        self.config = PhotoSyncConfig()
        self.known_devices = set()
        self.last_sync_times = {}
        self.update_known_devices()
        
        # Load last sync times
        self.sync_history_file = Path.home() / '.calvin_sync_history.json'
        self.load_sync_history()
    
    def load_sync_history(self):
        """Load sync history from file"""
        try:
            if self.sync_history_file.exists():
                with open(self.sync_history_file, 'r') as f:
                    self.last_sync_times = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load sync history: {e}")
            self.last_sync_times = {}
    
    def save_sync_history(self):
        """Save sync history to file"""
        try:
            with open(self.sync_history_file, 'w') as f:
                json.dump(self.last_sync_times, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save sync history: {e}")
    
    def update_known_devices(self):
        """Update list of currently connected devices"""
        self.known_devices = set(self.get_connected_devices().keys())
    
    def get_connected_devices(self):
        """Get list of currently connected devices"""
        connected = {}
        
        for device_name, device_path in self.config.config['source_devices'].items():
            device_path_obj = Path(device_path)
            if device_path_obj.exists():
                # Additional check - make sure it's actually a mounted volume
                try:
                    # Quick test to see if we can list the directory
                    list(device_path_obj.iterdir())
                    connected[device_name] = device_path
                    logger.debug(f"Device {device_name} is connected and accessible")
                except (OSError, PermissionError):
                    logger.debug(f"Device {device_name} path exists but is not accessible")
        
        return connected
    
    def should_sync_device(self, device_name):
        """Determine if we should sync this device based on history and settings"""
        # Check if we've synced recently
        last_sync = self.last_sync_times.get(device_name)
        if last_sync:
            try:
                last_sync_dt = datetime.fromisoformat(last_sync)
                time_since_sync = datetime.now() - last_sync_dt
                
                # Don't sync if we synced less than 1 hour ago
                if time_since_sync.total_seconds() < 3600:
                    logger.info(f"Skipping sync for {device_name} - last synced {time_since_sync} ago")
                    return False
            except ValueError:
                # Invalid date format, proceed with sync
                pass
        
        return True
    
    def check_for_new_devices(self):
        """Check for newly connected devices"""
        current_devices = set(self.get_connected_devices().keys())
        new_devices = current_devices - self.known_devices
        
        if new_devices:
            logger.info(f"New devices detected: {list(new_devices)}")
            self.known_devices = current_devices
            return list(new_devices)
        
        # Update known devices to handle disconnections
        if self.known_devices != current_devices:
            disconnected = self.known_devices - current_devices
            if disconnected:
                logger.info(f"Devices disconnected: {list(disconnected)}")
            self.known_devices = current_devices
        
        return []
    
    def notify(self, message, title="Calvin Photo Sync"):
        """Send macOS notification"""
        try:
            # Escape quotes for AppleScript
            safe_message = message.replace('"', '\\"')
            safe_title = title.replace('"', '\\"')
            
            script = f'display notification "{safe_message}" with title "{safe_title}" sound name "Glass"'
            subprocess.run(['osascript', '-e', script], check=True)
        except Exception as e:
            logger.warning(f"Could not send notification: {e}")
    
    def run_sync_for_device(self, device_name):
        """Run enhanced photo sync for a specific device"""
        if not self.should_sync_device(device_name):
            return True
        
        logger.info(f"Starting enhanced photo sync for device: {device_name}")
        self.notify(f"Device {device_name} connected - starting enhanced photo sync with GPS detection...")
        
        start_time = datetime.now()
        
        try:
            # Run enhanced sync
            sync = OptimizedCalvinPhotoSync(dry_run=False)
            success = sync.run_optimized_sync(device_name)
            
            duration = datetime.now() - start_time
            
            if success:
                # Update sync history
                self.last_sync_times[device_name] = start_time.isoformat()
                self.save_sync_history()
                
                # Get stats from the sync
                stats = sync.stats
                message = f"✅ Sync completed for {device_name}!\n"
                message += f"📸 {stats['photos_copied']} photos copied\n"
                message += f"🗂️ {stats['trips_detected']} trips detected\n"
                message += f"☁️ {stats['photos_uploaded']} photos uploaded\n"
                message += f"⏱️ Duration: {duration.total_seconds():.1f}s"
                
                logger.info(message.replace('\n', ' | '))
                self.notify(message, "Calvin Sync Complete")
                
            else:
                error_msg = f"❌ Sync failed for {device_name}"
                logger.error(error_msg)
                self.notify(error_msg, "Calvin Sync Failed")
            
            return success
            
        except Exception as e:
            error_msg = f"Error running sync for {device_name}: {e}"
            logger.error(error_msg)
            self.notify(f"Sync error for {device_name}: {str(e)}", "Calvin Sync Error")
            return False
    
    def get_device_info(self, device_name):
        """Get information about a device"""
        connected_devices = self.get_connected_devices()
        if device_name not in connected_devices:
            return None
        
        device_path = Path(connected_devices[device_name])
        
        try:
            # Get basic info
            stat_info = device_path.stat()
            
            # Count photos (quick estimate)
            photo_count = 0
            for photo_dir in ['DCIM', 'Photos', 'Pictures']:
                photo_dir_path = device_path / photo_dir
                if photo_dir_path.exists():
                    try:
                        for ext in ['.jpg', '.jpeg', '.JPG', '.JPEG']:
                            photo_count += len(list(photo_dir_path.rglob(f'*{ext}')))
                        break  # Stop after finding first photo directory
                    except:
                        pass
            
            return {
                'path': str(device_path),
                'accessible': True,
                'estimated_photos': photo_count,
                'last_sync': self.last_sync_times.get(device_name, 'Never')
            }
            
        except Exception as e:
            return {
                'path': str(device_path),
                'accessible': False,
                'error': str(e)
            }
    
    def start_monitoring(self, check_interval=10):
        """Start monitoring for device connections"""
        logger.info("🎯 Calvin Enhanced Photo Sync Daemon started")
        logger.info("📱 Monitoring for device connections with GPS-aware trip detection...")
        logger.info(f"🔧 Configured devices: {list(self.config.config['source_devices'].keys())}")
        logger.info(f"📍 GPS location naming: {'✅ Enabled' if self.config.config['trip_detection']['gps_clustering']['enabled'] else '❌ Disabled'}")
        logger.info(f"⏱️ Check interval: {check_interval} seconds")
        logger.info("Press Ctrl+C to stop\n")
        
        try:
            while True:
                new_devices = self.check_for_new_devices()
                
                for device in new_devices:
                    logger.info(f"🔌 New device detected: {device}")
                    
                    # Get device info
                    device_info = self.get_device_info(device)
                    if device_info and device_info['accessible']:
                        logger.info(f"📊 Device info - Photos: ~{device_info['estimated_photos']}, Last sync: {device_info['last_sync']}")
                    
                    # Run sync
                    self.run_sync_for_device(device)
                
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Daemon stopped by user")
        except Exception as e:
            logger.error(f"💥 Daemon error: {e}")
            raise

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Calvin Enhanced Photo Sync Daemon')
    parser.add_argument('--interval', '-i', type=int, default=10, 
                      help='Check interval in seconds (default: 10)')
    parser.add_argument('--test', '-t', action='store_true', 
                      help='Test device detection without monitoring')
    parser.add_argument('--info', action='store_true',
                      help='Show device info and exit')
    parser.add_argument('--reset-history', action='store_true',
                      help='Reset sync history')
    parser.add_argument('--force-sync', metavar='DEVICE',
                      help='Force sync for specified device')
    
    args = parser.parse_args()
    
    monitor = EnhancedDeviceMonitor()
    
    if args.reset_history:
        monitor.last_sync_times = {}
        monitor.save_sync_history()
        print("✅ Sync history reset")
        return
    
    if args.force_sync:
        device = args.force_sync
        if device in monitor.config.config['source_devices']:
            print(f"🚀 Force syncing device: {device}")
            # Temporarily remove from history to force sync
            old_time = monitor.last_sync_times.get(device)
            if old_time:
                del monitor.last_sync_times[device]
            success = monitor.run_sync_for_device(device)
            if not success and old_time:
                monitor.last_sync_times[device] = old_time
            return
        else:
            print(f"❌ Device '{device}' not found in configuration")
            print(f"Available devices: {list(monitor.config.config['source_devices'].keys())}")
            return
    
    if args.test or args.info:
        print("🔍 Testing device detection...")
        connected = monitor.get_connected_devices()
        
        if connected:
            print(f"\n✅ Connected devices ({len(connected)}):")
            for name, path in connected.items():
                print(f"\n📱 Device: {name}")
                print(f"   Path: {path}")
                
                device_info = monitor.get_device_info(name)
                if device_info:
                    if device_info['accessible']:
                        print(f"   Status: ✅ Accessible")
                        print(f"   Estimated photos: ~{device_info['estimated_photos']}")
                        print(f"   Last sync: {device_info['last_sync']}")
                    else:
                        print(f"   Status: ❌ Not accessible - {device_info.get('error', 'Unknown error')}")
        else:
            print("❌ No configured devices currently connected")
            print(f"Looking for: {list(monitor.config.config['source_devices'].keys())}")
    else:
        monitor.start_monitoring(args.interval)

if __name__ == "__main__":
    main()