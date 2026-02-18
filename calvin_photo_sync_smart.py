#!/usr/bin/env python3
"""
Calvin Photo Sync - Smart Version with Pre-Check
Only transfers files that aren't already uploaded
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

class SmartPhotoSync:
    """Smart photo sync that only transfers missing files"""
    
    def __init__(self, config_path="~/.calvin_photo_sync.json"):
        self.config_path = Path(config_path).expanduser()
        self.config = self.load_config()
        
    def load_config(self):
        """Load configuration from file"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        
        # Default config
        return {
            "source_devices": {"Calvin": "/Volumes/Calvin"},
            "destination": "/Volumes/Rainbow",
            "folders": {
                "staging": "Photo Staging",
                "new_photos": "New Photos", 
                "uploaded_photos": "Uploaded Photos"
            },
            "photo_extensions": [".jpg", ".jpeg", ".png", ".heic", ".raw", ".cr2", ".nef", ".mov", ".mp4"],
            "trip_detection": {
                "time_gap_hours": 8,
                "gps_clustering_enabled": True,
                "max_consolidation_days": 3,
                "gps_cluster_distance_km": 50
            }
        }
    
    def get_uploaded_files(self):
        """Get set of all files already in Uploaded Photos folder"""
        uploaded_files = set()
        uploaded_path = Path(self.config["destination"]) / self.config["folders"]["uploaded_photos"]
        
        if uploaded_path.exists():
            print(f"📂 Scanning uploaded files in {uploaded_path}...")
            for file_path in uploaded_path.rglob("*"):
                if file_path.is_file():
                    # Normalize filename for comparison (uppercase, no path)
                    uploaded_files.add(file_path.name.upper())
            print(f"   Found {len(uploaded_files)} already uploaded files")
        else:
            print("⚠️  Uploaded Photos folder not found - assuming empty")
            
        return uploaded_files
    
    def get_manifest_files(self):
        """Get files from manifest if it exists"""
        manifest_files = set()
        manifest_path = Path(self.config["destination"]) / "ARCHIVE_MANIFEST.txt"
        
        if manifest_path.exists():
            print(f"📋 Reading archive manifest...")
            with open(manifest_path, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        # Extract filename from manifest line
                        parts = line.strip().split('\t')
                        if len(parts) >= 1:
                            filename = Path(parts[0]).name.upper()
                            manifest_files.add(filename)
            print(f"   Found {len(manifest_files)} files in manifest")
        
        return manifest_files
    
    def scan_calvin_files(self, calvin_path):
        """Quick scan of files on Calvin device"""
        calvin_files = {}  # filename -> full_path
        
        if not calvin_path.exists():
            print(f"❌ Calvin device not found at {calvin_path}")
            return calvin_files
            
        print(f"📂 Quick scanning Calvin device...")
        
        for root, dirs, files in os.walk(calvin_path):
            for filename in files:
                # Check if it's a photo/video file
                file_path = Path(root) / filename
                if (file_path.suffix.lower() in self.config["photo_extensions"] and
                    not filename.startswith('._') and
                    not filename.startswith('.DS_Store')):
                    calvin_files[filename.upper()] = file_path
        
        print(f"   Found {len(calvin_files)} media files on Calvin")
        return calvin_files
    
    def find_missing_files(self, calvin_files, uploaded_files, manifest_files=None):
        """Find files that exist on Calvin but not in uploaded folders"""
        all_uploaded = uploaded_files.copy()
        if manifest_files:
            all_uploaded.update(manifest_files)
        
        missing_files = {}
        for filename, file_path in calvin_files.items():
            if filename not in all_uploaded:
                missing_files[filename] = file_path
                
        return missing_files
    
    def smart_sync(self, device_name="Calvin", dry_run=False):
        """Perform smart sync - only transfer missing files"""
        
        print("🧠 CALVIN PHOTO SYNC - SMART MODE")
        print("="*60)
        
        # Get Calvin device path
        calvin_path = Path(self.config["source_devices"][device_name])
        if not calvin_path.exists():
            print(f"❌ Device '{device_name}' not found at {calvin_path}")
            return False
            
        print(f"✅ Found device: {device_name} at {calvin_path}")
        
        # Step 1: Get already uploaded files
        uploaded_files = self.get_uploaded_files()
        manifest_files = self.get_manifest_files()
        
        # Step 2: Quick scan of Calvin
        calvin_files = self.scan_calvin_files(calvin_path)
        
        # Step 3: Find missing files
        missing_files = self.find_missing_files(calvin_files, uploaded_files, manifest_files)
        
        print()
        print("📊 SMART ANALYSIS RESULTS")
        print("="*30)
        print(f"Files on Calvin: {len(calvin_files)}")
        print(f"Files already uploaded: {len(uploaded_files)}")
        print(f"Files in manifest: {len(manifest_files) if manifest_files else 0}")
        print(f"Missing files to sync: {len(missing_files)}")
        
        if not missing_files:
            print("\n✅ No missing files found! All Calvin files are already uploaded.")
            return True
            
        # Step 4: Show missing files
        print(f"\n📋 MISSING FILES TO SYNC:")
        print("-" * 40)
        sorted_missing = sorted(missing_files.items())
        for i, (filename, file_path) in enumerate(sorted_missing, 1):
            file_size = file_path.stat().st_size / (1024*1024)  # MB
            print(f"{i:3d}. {filename} ({file_size:.1f}MB)")
            if i >= 20:
                remaining = len(sorted_missing) - 20
                if remaining > 0:
                    print(f"     ... and {remaining} more files")
                break
        
        if dry_run:
            print(f"\n🔍 DRY RUN: Would sync {len(missing_files)} missing files")
            return True
            
        # Step 5: Copy only missing files
        print(f"\n📥 COPYING {len(missing_files)} MISSING FILES...")
        print("-" * 50)
        
        staging_path = Path(self.config["destination"]) / self.config["folders"]["staging"]
        staging_path.mkdir(exist_ok=True)
        
        copied_count = 0
        for filename, file_path in missing_files.items():
            dest_path = staging_path / filename.lower()  # Use original case
            
            try:
                print(f"📥 Copying: {filename}")
                shutil.copy2(file_path, dest_path)
                copied_count += 1
            except Exception as e:
                print(f"❌ Failed to copy {filename}: {e}")
        
        print(f"\n✅ SMART COPY COMPLETE")
        print(f"   Files copied: {copied_count}/{len(missing_files)}")
        print(f"   Ready for Phase 2 processing...")
        
        return True

def main():
    parser = argparse.ArgumentParser(description='Calvin Photo Sync - Smart Mode')
    parser.add_argument('--device', '-d', default='Calvin', help='Device name to sync from')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Preview actions without executing')
    parser.add_argument('--config', '-c', action='store_true', help='Show current configuration')
    
    args = parser.parse_args()
    
    syncer = SmartPhotoSync()
    
    if args.config:
        print("Current Configuration:")
        print(json.dumps(syncer.config, indent=2))
        return
    
    try:
        success = syncer.smart_sync(args.device, args.dry_run)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Sync cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Sync failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()