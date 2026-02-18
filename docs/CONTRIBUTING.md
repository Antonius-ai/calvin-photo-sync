# Contributing to Calvin Photo Sync

Thank you for your interest in contributing! This document provides guidelines for contributing to the Calvin Photo Sync project.

## 🚀 Getting Started

### Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/calvin-photo-sync.git
   cd calvin-photo-sync
   ```

2. **Install dependencies:**
   ```bash
   pip3 install Pillow --break-system-packages
   npm install -g @immich/cli
   ```

3. **Set up test environment:**
   ```bash
   # Create test configuration
   cp ~/.calvin_photo_sync.json ~/.calvin_photo_sync.test.json
   
   # Edit test config to use test directories
   # Change destination to a test folder
   ```

### Running Tests

```bash
# Test device detection
python3 calvin_daemon_enhanced.py --test

# Test sync with dry run
python3 calvin_photo_sync_optimized.py --dry-run --test

# Test control script
./calvin_control.sh test
```

## 🛠️ Development Guidelines

### Code Style

- **Python**: Follow PEP 8 style guidelines
- **Shell scripts**: Use bash with set -e for error handling
- **Comments**: Clear, concise comments explaining complex logic
- **Logging**: Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)

### Naming Conventions

- **Files**: snake_case for Python, kebab-case for shell scripts
- **Functions**: snake_case
- **Classes**: PascalCase
- **Constants**: UPPER_CASE
- **Variables**: snake_case

### Error Handling

- Always use try/except blocks for external operations
- Log errors with context information
- Provide graceful degradation when possible
- Use specific exception types

### Testing

- Test with various photo collections (small, large, mixed dates)
- Verify GPS parsing with different camera models
- Test edge cases (no GPS data, corrupted files, etc.)
- Validate on different macOS versions

## 🏗️ Architecture Overview

### Core Components

```
calvin_photo_sync_optimized.py
├── PhotoSyncConfig          # Configuration management
├── PhotoMetadata           # EXIF/GPS extraction
├── LocalTripDetector       # GPS-aware trip detection
└── OptimizedCalvinPhotoSync # Main sync orchestrator

calvin_daemon_enhanced.py
└── EnhancedDeviceMonitor   # Device connection monitoring
```

### Data Flow

1. **Device Detection** → EnhancedDeviceMonitor detects new device
2. **Photo Discovery** → Scan device for photos
3. **Metadata Extraction** → Extract GPS, date, EXIF data
4. **Trip Analysis** → Group photos using GPS + time intelligence
5. **File Organization** → Copy and organize by trips
6. **Upload Process** → Upload to Immich with album creation
7. **Archiving** → Move to uploaded photos folder

## 🎯 Common Contribution Areas

### 1. Location Detection Enhancement

**Current system:** Simple distance-based matching
**Opportunities:**
- Online geocoding integration (Google Maps, OpenStreetMap)
- Landmark detection using photo recognition
- Time zone-based location inference
- Hierarchical location naming (Country → State → City → Landmark)

**Example implementation:**
```python
def enhanced_location_detection(self, gps_coords, photo_path):
    # Try online geocoding
    online_result = self.geocode_online(gps_coords)
    if online_result:
        return online_result
    
    # Try landmark detection from image
    landmark = self.detect_landmark_from_image(photo_path)
    if landmark:
        return landmark
        
    # Fall back to static mapping
    return self.get_location_name_static(gps_coords)
```

### 2. Advanced Trip Detection

**Current system:** Time gaps + GPS clustering
**Opportunities:**
- Activity recognition (hiking, driving, flying)
- Photo content analysis (indoor vs outdoor)
- Calendar integration (scheduled events)
- Weather data correlation
- Social media check-ins integration

**Example implementation:**
```python
class AdvancedTripDetector(LocalTripDetector):
    def detect_activity_change(self, photos):
        # Analyze photo metadata for activity patterns
        pass
        
    def integrate_calendar_data(self, photo_datetime):
        # Check calendar for scheduled events
        pass
```

### 3. Additional Photo Sources

**Current system:** Local mounted volumes
**Opportunities:**
- Cloud storage integration (iCloud, Google Photos, Dropbox)
- Network attached storage (NAS)
- Camera Wi-Fi direct download
- Email attachment processing
- Social media photo backup

### 4. Enhanced User Interface

**Current system:** Command line tools
**Opportunities:**
- macOS menu bar app
- Web-based dashboard
- Mobile companion app
- System preferences panel
- Finder integration

### 5. Performance Optimizations

**Current areas for improvement:**
- Parallel photo processing
- Incremental metadata caching
- Smarter duplicate detection
- Batch upload optimizations
- Memory usage optimization for large collections

## 🐛 Bug Reports

### Before Submitting

1. **Search existing issues** to avoid duplicates
2. **Test with latest version** from main branch
3. **Reproduce with minimal test case** if possible
4. **Gather relevant logs** and configuration

### Issue Template

```markdown
## Bug Description
Brief description of the issue

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should have happened

## Actual Behavior  
What actually happened

## Environment
- macOS version: 
- Python version:
- Calvin Photo Sync version:
- Device type:
- Photo count:

## Logs
```
Relevant log excerpts
```

## Configuration
```json
{
  "sanitized": "configuration"
}
```
```

### Priority Labels

- **Critical**: System crashes, data loss
- **High**: Core functionality broken
- **Medium**: Feature doesn't work as expected
- **Low**: Minor issues, cosmetic problems

## ✨ Feature Requests

### Feature Request Template

```markdown
## Feature Description
Clear description of the new feature

## Use Case
Why is this feature needed? What problem does it solve?

## Proposed Solution
How should this feature work?

## Alternatives Considered
What other approaches were considered?

## Implementation Notes
Any technical considerations or constraints
```

## 🔄 Pull Request Process

### Before Submitting

1. **Create feature branch** from main
2. **Test thoroughly** with various scenarios
3. **Update documentation** if needed
4. **Follow code style** guidelines
5. **Add appropriate comments** and logging

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tested with small photo collections
- [ ] Tested with large photo collections  
- [ ] Tested GPS parsing accuracy
- [ ] Tested error conditions
- [ ] Updated/added tests

## Documentation
- [ ] Updated README if needed
- [ ] Updated API documentation
- [ ] Added example usage
- [ ] Updated configuration schema

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Commented complex code sections
- [ ] No breaking changes without version bump
```

### Review Process

1. **Automated checks** must pass
2. **Manual testing** by maintainers
3. **Code review** for style and logic
4. **Documentation review** for clarity
5. **Merge** once approved

## 📚 Documentation Guidelines

### README Updates

- Keep examples current and tested
- Update configuration sections when adding options
- Maintain clear installation instructions
- Include troubleshooting for new features

### API Documentation

- Document all public methods and classes
- Include parameter types and descriptions
- Provide usage examples
- Update when changing interfaces

### Code Comments

```python
def complex_gps_calculation(self, coords):
    """
    Calculate enhanced GPS clustering with time weighting.
    
    Args:
        coords (list): List of GPS coordinate tuples
        
    Returns:
        dict: Cluster information with centroids and groupings
        
    Note:
        This algorithm uses Haversine distance with temporal decay
        to weight recent photos more heavily in clustering decisions.
    """
    # Implementation details...
```

## 🚀 Release Process

### Version Numbering

- **Major** (X.0.0): Breaking changes, major features
- **Minor** (1.X.0): New features, backward compatible  
- **Patch** (1.1.X): Bug fixes, small improvements

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in relevant files
- [ ] Git tag created
- [ ] Release notes prepared

## 🤝 Community

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: Questions, ideas, showcase
- **Pull Requests**: Code contributions

### Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers get started
- Share knowledge and learn from others

Thank you for contributing to Calvin Photo Sync! 🎉