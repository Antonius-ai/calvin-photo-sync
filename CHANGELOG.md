# Changelog

All notable changes to Calvin Photo Sync will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-02-17

### Added
- **GPS-Aware Trip Detection**: Intelligent photo grouping using GPS location and time gaps
- **Location Album Naming**: Automatic album names like "2025-05-17-Hawaii" based on GPS data  
- **Enhanced Daemon System**: Automatic device detection and sync triggering
- **Smart Time Grouping**: 
  - Short breaks (≤8 hours): Continue same trip
  - Medium breaks (8h-3 days) + same location: Continue trip (perfect for week-long vacations!)
  - Different location or 3+ day gaps: New trip
- **Immich Integration**: Full upload automation with duplicate detection
- **Original Date Preservation**: Maintains photo creation dates throughout process
- **macOS Notifications**: Real-time sync status and completion alerts
- **Comprehensive Logging**: Detailed activity logs for monitoring and troubleshooting
- **Control Script**: Easy daemon management with `calvin_control.sh`
- **Three-Phase Processing**: Optimized workflow minimizing slow device access
- **Full-Depth Scanning**: Discovers photos in any directory structure
- **Resume Capability**: Can resume interrupted syncs
- **Batch Processing**: Handles large photo collections efficiently

### Features
- **Supported Locations**: San-Francisco, Los-Angeles, San-Diego, Hawaii, New-York, Paris, London, Tokyo
- **Supported File Types**: JPG, JPEG, PNG, HEIC, RAW, CR2, NEF, MOV, MP4
- **Device Support**: Any mounted volume (cameras, phones, SD cards)
- **GPS Clustering**: 50km radius clustering with configurable parameters
- **Smart Deduplication**: Prevents re-uploading existing photos
- **LaunchAgent Integration**: Starts automatically with macOS

### Configuration
- JSON-based configuration in `~/.calvin_photo_sync.json`
- Device mapping for multiple photo sources
- Customizable trip detection parameters
- Immich server integration settings
- Notification preferences

### Tools Included
- `calvin_photo_sync_optimized.py` - Main sync engine
- `calvin_daemon_enhanced.py` - Device monitoring daemon
- `calvin_control.sh` - Easy management script
- `setup_calvin_daemon.sh` - Automated installation
- `com.calvin.photosync.daemon.plist` - macOS LaunchAgent configuration

### Documentation
- Comprehensive README with installation and usage instructions
- API documentation for developers
- Usage examples and common scenarios
- Contributing guidelines
- Troubleshooting guide

### Performance
- Optimized for large photo collections (3,000+ photos tested)
- Minimal processing on slow source devices
- Progress tracking with batch processing
- Memory-efficient metadata handling
- Automatic cleanup and error recovery

### Tested Scenarios
- End-to-end sync of 3,332 photos across 59 automatically created albums
- Perfect deduplication preventing re-uploads
- GPS location detection and album naming
- Week-long trip consolidation using GPS clustering
- Multiple device support with different configurations
- Daemon reliability and automatic restart capabilities

---

**Initial release featuring complete GPS-aware photo synchronization system with intelligent trip detection and automatic Immich integration.**