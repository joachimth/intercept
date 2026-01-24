# CLAUDE.md - AI Assistant Guide for INTERCEPT

> **Last Updated:** 2026-01-24
> **Version:** 2.9.5
> **Purpose:** Comprehensive guide for AI assistants working on the INTERCEPT codebase

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Codebase Architecture](#codebase-architecture)
3. [Directory Structure](#directory-structure)
4. [Key Conventions](#key-conventions)
5. [Development Workflow](#development-workflow)
6. [Testing Strategy](#testing-strategy)
7. [Common Development Tasks](#common-development-tasks)
8. [Important Design Patterns](#important-design-patterns)
9. [Security Considerations](#security-considerations)
10. [External Dependencies](#external-dependencies)
11. [Troubleshooting Guide](#troubleshooting-guide)

---

## Project Overview

**INTERCEPT** is a web-based Signal Intelligence (SIGINT) platform that provides a unified interface for various software-defined radio (SDR) and wireless reconnaissance tools.

### Core Features
- **Pager Decoding** - POCSAG/FLEX via rtl_fm + multimon-ng
- **433MHz Sensors** - Weather stations, TPMS, IoT devices via rtl_433
- **Aircraft Tracking** - ADS-B via dump1090 with real-time map
- **ACARS Messaging** - Aircraft datalink messages via acarsdec
- **APRS Tracking** - Amateur radio position reporting via direwolf
- **Listening Post** - Frequency scanner with audio monitoring
- **Satellite Tracking** - Pass prediction using TLE data
- **WiFi Scanning** - Monitor mode reconnaissance via aircrack-ng
- **Bluetooth Scanning** - Device discovery and tracker detection
- **TSCM** - Technical Surveillance Countermeasures and threat detection

### Technology Stack
- **Backend:** Python 3.9+ with Flask 2.0+
- **Frontend:** Vanilla JavaScript with Leaflet.js for maps
- **Database:** SQLite for settings and historical data
- **Real-time:** Server-Sent Events (SSE) and WebSockets
- **Containerization:** Docker with privileged mode for USB access
- **CI/CD:** GitHub Actions for automated Raspberry Pi image builds

---

## Codebase Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Flask Application (app.py)               │
│  - Global state (processes, queues, locks, data stores)     │
│  - Security headers                                         │
│  - Process lifecycle management                             │
└────────────────┬────────────────────────────────────────────┘
                 │
    ┌────────────┴────────────┐
    │   Blueprint Registration │
    │   (routes/__init__.py)   │
    └────────┬─────────────────┘
             │
    ┌────────┴─────────────────────────────────────────┐
    │         15 Independent Route Blueprints          │
    ├──────────────────────────────────────────────────┤
    │ pager_bp       │ sensor_bp      │ adsb_bp        │
    │ acars_bp       │ aprs_bp        │ satellite_bp   │
    │ wifi_bp        │ bluetooth_bp   │ gps_bp         │
    │ listening_bp   │ tscm_bp        │ correlation_bp │
    │ settings_bp    │ audio_ws       │ ...            │
    └────────┬─────────────────────────────────────────┘
             │
    ┌────────┴──────────────────────────────────────────┐
    │            Shared Utilities Layer                 │
    ├───────────────────────────────────────────────────┤
    │ utils/                                            │
    │  - dependencies.py   (tool availability checks)   │
    │  - validation.py     (input validation)           │
    │  - process.py        (subprocess management)      │
    │  - cleanup.py        (auto-expiring DataStore)    │
    │  - database.py       (SQLite operations)          │
    │  - sdr/              (hardware abstraction)       │
    │  - tscm/             (threat detection)           │
    └───────────────────────────────────────────────────┘
```

### Process Management Model

Each RF mode has its own:
1. **Global process variable** (e.g., `current_process`, `sensor_process`, `adsb_process`)
2. **Queue** for data aggregation (max 100 items)
3. **Threading lock** for thread-safe updates
4. **SSE endpoint** for real-time frontend updates

Example structure in `app.py`:
```python
# Pager decoder
current_process = None
output_queue = queue.Queue(maxsize=100)
process_lock = threading.Lock()

# ADS-B aircraft
adsb_process = None
adsb_queue = queue.Queue(maxsize=100)
adsb_lock = threading.Lock()
```

### Flask Blueprint Pattern

Each mode is implemented as an independent blueprint:
```python
# Example: routes/pager.py
from flask import Blueprint

pager_bp = Blueprint('pager', __name__, url_prefix='/pager')

@pager_bp.route('/start', methods=['POST'])
def start_pager():
    # Implementation
    pass
```

Blueprints are registered in `routes/__init__.py`:
```python
def register_blueprints(app):
    from .pager import pager_bp
    from .sensor import sensor_bp
    # ... import all blueprints

    app.register_blueprint(pager_bp)
    app.register_blueprint(sensor_bp)
    # ... register all
```

---

## Directory Structure

```
intercept/
├── app.py                      # Flask application core + global state
├── config.py                   # Configuration management (env vars)
├── intercept.py                # Entry point script (CLI args)
├── setup.sh                    # Installation script (22KB bash)
├── pyproject.toml              # Project metadata, tool configs
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Dev dependencies (pytest, ruff, mypy)
├── Dockerfile                  # Multi-stage container build
├── docker-compose.yml          # Container orchestration
├── README.md                   # User documentation
├── CHANGELOG.md                # Release notes
├── LICENSE                     # MIT License
│
├── routes/                     # Flask Blueprints (15 modules)
│   ├── __init__.py            # Blueprint registration
│   ├── pager.py               # POCSAG/FLEX pager decoding
│   ├── sensor.py              # 433MHz RTL_433 sensors
│   ├── adsb.py                # Aircraft tracking (dump1090)
│   ├── acars.py               # Aircraft messaging
│   ├── aprs.py                # Amateur radio tracking (64KB)
│   ├── satellite.py           # Satellite pass prediction
│   ├── wifi.py                # WiFi reconnaissance (45KB)
│   ├── bluetooth.py           # Bluetooth scanning
│   ├── listening_post.py      # Frequency scanner (31KB)
│   ├── audio_websocket.py     # WebSocket audio streaming
│   ├── gps.py                 # GPS integration
│   ├── correlation.py         # Device correlation engine
│   ├── settings.py            # Settings persistence
│   └── tscm.py                # TSCM counter-surveillance (128KB)
│
├── utils/                      # Shared utilities (NO Flask deps)
│   ├── __init__.py
│   ├── dependencies.py        # Tool availability checks
│   ├── validation.py          # Input validation functions
│   ├── constants.py           # Centralized constants
│   ├── process.py             # Process lifecycle management
│   ├── process_monitor.py     # Process monitoring
│   ├── cleanup.py             # DataStore with auto-cleanup
│   ├── database.py            # SQLite utilities
│   ├── logging.py             # Logger configuration
│   ├── sse.py                 # Server-Sent Events helpers
│   ├── aircraft_db.py         # Aircraft database lookup
│   ├── correlation.py         # Device correlation logic
│   ├── gps.py                 # GPS utilities
│   │
│   ├── sdr/                   # Hardware abstraction layer
│   │   ├── __init__.py        # SDRFactory exports
│   │   ├── base.py            # Abstract base classes
│   │   ├── detection.py       # Device detection
│   │   ├── rtlsdr.py          # RTL-SDR implementation
│   │   ├── limesdr.py         # LimeSDR implementation
│   │   ├── hackrf.py          # HackRF implementation
│   │   ├── airspy.py          # Airspy implementation
│   │   ├── sdrplay.py         # SDRPlay implementation
│   │   └── validation.py      # SDR parameter validation
│   │
│   └── tscm/                  # Technical Surveillance Countermeasures
│       ├── __init__.py
│       ├── baseline.py        # Baseline recording/comparison
│       ├── detector.py        # Threat detection engine
│       ├── correlation.py     # Signal correlation
│       ├── ble_scanner.py     # BLE device scanning
│       ├── device_identity.py # Device fingerprinting
│       ├── advanced.py        # Advanced analysis
│       └── reports.py         # Report generation
│
├── data/                       # Reference data modules
│   ├── __init__.py
│   ├── oui.py                 # MAC address OUI database
│   ├── satellites.py          # Satellite TLE data
│   ├── patterns.py            # Detection patterns
│   └── tscm_frequencies.py    # TSCM frequency presets
│
├── templates/                  # Jinja2 HTML templates
│   ├── index.html             # Main interface
│   ├── adsb_dashboard.html    # Aircraft tracking dashboard
│   ├── satellite_dashboard.html
│   └── partials/modes/        # Modal templates
│       ├── pager.html
│       ├── sensor.html
│       ├── adsb.html
│       ├── wifi.html
│       ├── bluetooth.html
│       ├── satellite.html
│       ├── tscm.html
│       ├── aprs.html
│       └── listening-post.html
│
├── static/                     # Static assets
│   ├── css/                   # Stylesheets
│   │   ├── index.css
│   │   ├── responsive.css
│   │   ├── adsb_dashboard.css
│   │   └── modes/             # Mode-specific styles
│   ├── js/                    # JavaScript
│   │   ├── core/
│   │   │   ├── app.js         # Main application logic
│   │   │   ├── audio.js       # Audio handling
│   │   │   └── utils.js       # Helper functions
│   │   ├── components/
│   │   │   └── radio-knob.js  # Interactive radio dial
│   │   └── modes/
│   │       └── listening-post.js
│   └── images/                # Screenshots, logos
│
├── tests/                      # Test suite (pytest)
│   ├── conftest.py            # Fixtures & configuration
│   ├── test_app.py            # Application tests
│   ├── test_routes.py         # Route handler tests
│   ├── test_validation.py     # Input validation tests
│   ├── test_config.py         # Configuration tests
│   ├── test_database.py       # Database tests (9KB)
│   ├── test_correlation.py    # Correlation engine (12KB)
│   ├── test_satellite.py      # Satellite tracking tests
│   ├── test_bluetooth.py      # Bluetooth tests
│   ├── test_wifi.py           # WiFi tests
│   └── test_utils.py          # Utility tests
│
├── instance/                   # Runtime data (SQLite DB, logs)
│   └── intercept.db           # Created at runtime
│
├── docs/                       # Documentation
│   ├── USAGE.md
│   ├── HARDWARE.md
│   ├── CUSTOM_OS_IMAGE.md
│   ├── SECURITY.md
│   └── TROUBLESHOOTING.md
│
├── .github/                    # GitHub configuration
│   ├── workflows/
│   │   └── build-custom-os.yml  # Monthly RPi image builds
│   └── scripts/
│       ├── customize-image.sh   # Image customization
│       └── intercept.service    # Systemd service file
│
├── promo/                      # Marketing materials
├── aircraft_db.json            # Aircraft metadata (15MB)
├── aircraft_db_meta.json       # Aircraft DB metadata
└── oui_database.json           # MAC address lookup
```

---

## Key Conventions

### Code Style

- **Language:** Python 3.9+ (type hints encouraged, not enforced)
- **Formatter:** Black (line length 120)
- **Linter:** Ruff (replaces flake8, isort, pyupgrade)
- **Type Checker:** Mypy (for critical utilities, not tests)
- **Line Length:** 120 characters
- **Imports:** Sorted by isort (first-party: app, config, routes, utils, data)

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| **Modules** | `snake_case.py` | `listening_post.py` |
| **Classes** | `PascalCase` | `SDRFactory`, `DataStore` |
| **Functions** | `snake_case()` | `check_tool()`, `validate_frequency()` |
| **Constants** | `UPPER_SNAKE_CASE` | `MAX_AIRCRAFT_AGE_SECONDS` |
| **Blueprints** | `name_bp` | `pager_bp`, `wifi_bp` |
| **Process vars** | `mode_process` | `sensor_process`, `adsb_process` |
| **Queue vars** | `mode_queue` | `sensor_queue`, `adsb_queue` |
| **Lock vars** | `mode_lock` | `sensor_lock`, `adsb_lock` |

### File Organization

1. **Imports** (grouped: stdlib, third-party, first-party)
2. **Constants** (module-level configuration)
3. **Blueprint creation** (if route module)
4. **Helper functions** (internal use, prefixed with `_`)
5. **Route handlers** (decorated with `@bp.route()`)
6. **Main logic** (if standalone utility)

### Documentation

- **Docstrings:** Google-style for public functions, optional for internal
- **Type hints:** Encouraged for function signatures
- **Comments:** Explain "why" not "what" (code should be self-documenting)
- **TODO format:** `# TODO(context): Description`

Example:
```python
def validate_frequency(freq: str) -> tuple[bool, str]:
    """Validate frequency string format and range.

    Args:
        freq: Frequency string (e.g., "433.92M", "1090MHz")

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty.
    """
    # Implementation
```

### Error Handling

- **Use specific exceptions:** `ValueError`, `subprocess.TimeoutExpired`, etc.
- **Catch narrow:** Only catch what you can handle
- **Log errors:** Use module-specific loggers from `utils.logging`
- **Return error info:** Routes return `jsonify({'status': 'error', 'message': str})`
- **Never silence errors:** Always log or propagate

Example:
```python
from utils.logging import pager_logger as logger

@pager_bp.route('/start', methods=['POST'])
def start_pager():
    try:
        # Implementation
        return jsonify({'status': 'success'})
    except ValueError as e:
        logger.error(f"Invalid frequency: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        logger.exception("Unexpected error starting pager")
        return jsonify({'status': 'error', 'message': 'Internal error'}), 500
```

### Environment Variables

All configuration via environment variables prefixed with `INTERCEPT_`:

```bash
INTERCEPT_HOST=0.0.0.0           # Listen address
INTERCEPT_PORT=5050              # Web port
INTERCEPT_DEBUG=false            # Debug mode
INTERCEPT_LOG_LEVEL=WARNING      # Logging level
INTERCEPT_PAGER_FREQ=929.6125M   # Default pager frequency
INTERCEPT_DEFAULT_GAIN=40        # SDR gain setting
INTERCEPT_DEFAULT_DEVICE=0       # Default SDR device index
```

Accessed via `config.py` helpers:
```python
from config import PORT, HOST, LOG_LEVEL
```

---

## Development Workflow

### Initial Setup

```bash
# Clone repository
git clone https://github.com/smittix/intercept.git
cd intercept

# Run setup script (installs dependencies)
./setup.sh

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Run application (root needed for WiFi/BT)
sudo -E venv/bin/python intercept.py

# Access at http://localhost:5050
```

### Development Loop

1. **Create feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes** (follow conventions above)

3. **Run tests**
   ```bash
   pytest                          # All tests
   pytest -v tests/test_routes.py  # Specific file
   pytest -k "test_pager"          # Match pattern
   ```

4. **Check code quality**
   ```bash
   ruff check .                    # Linting
   black --check .                 # Format check
   mypy utils/ data/               # Type check (not required)
   ```

5. **Auto-format code**
   ```bash
   black .                         # Format all files
   ruff --fix .                    # Auto-fix linting issues
   ```

6. **Run coverage**
   ```bash
   pytest --cov=app --cov=routes --cov=utils --cov=data
   ```

7. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add feature description"
   # Commit message format: type: description
   # Types: feat, fix, docs, style, refactor, test, chore
   ```

8. **Push and create PR**
   ```bash
   git push origin feature/my-feature
   # Create PR on GitHub
   ```

### Running in Docker

```bash
# Build and run
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down

# Rebuild after changes
docker compose up -d --build
```

### Debugging

1. **Enable debug mode**
   ```bash
   python intercept.py --debug
   # OR
   export INTERCEPT_DEBUG=true
   python intercept.py
   ```

2. **Check dependency status**
   ```bash
   python intercept.py --check-deps
   ```

3. **View process status**
   ```bash
   # Access /health endpoint
   curl http://localhost:5050/health | jq
   ```

4. **Check logs**
   ```bash
   # Enable verbose logging
   export INTERCEPT_LOG_LEVEL=DEBUG
   python intercept.py 2>&1 | tee intercept.log
   ```

5. **Device diagnostics**
   ```bash
   # Access /devices/debug endpoint
   curl http://localhost:5050/devices/debug | jq
   ```

---

## Testing Strategy

### Test Organization

- **Location:** `tests/` directory
- **Framework:** Pytest
- **Coverage:** `pytest-cov`
- **Mocking:** `pytest-mock`

### Test Structure

```python
# tests/test_example.py
import pytest
from flask import Flask

def test_something(client):
    """Test description following Google docstring style."""
    # Arrange
    data = {'key': 'value'}

    # Act
    response = client.post('/endpoint', json=data)

    # Assert
    assert response.status_code == 200
    assert response.json['status'] == 'success'
```

### Fixtures (conftest.py)

Common fixtures available:
```python
@pytest.fixture
def app():
    """Flask application instance for testing."""
    # Returns configured Flask app

@pytest.fixture
def client(app):
    """Flask test client."""
    # Returns test client for making requests
```

### Running Tests

```bash
# All tests
pytest

# Verbose output
pytest -v

# Specific file
pytest tests/test_validation.py

# Pattern matching
pytest -k "test_frequency"

# With coverage
pytest --cov=app --cov=routes --cov=utils

# Coverage report in HTML
pytest --cov=app --cov-report=html
# Open htmlcov/index.html

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l
```

### Testing Guidelines

1. **Test file naming:** `test_<module>.py`
2. **Test function naming:** `test_<description>`
3. **Arrange-Act-Assert:** Structure tests clearly
4. **Mock external calls:** Use `pytest-mock` for subprocess, network calls
5. **Test edge cases:** Empty inputs, invalid data, boundary values
6. **Avoid test interdependence:** Each test should be isolated
7. **Use fixtures:** Reuse setup code via fixtures

### Writing New Tests

When adding a new route:
```python
# routes/new_feature.py
@new_feature_bp.route('/start', methods=['POST'])
def start_feature():
    data = request.json
    if not data.get('frequency'):
        return jsonify({'status': 'error', 'message': 'Missing frequency'}), 400
    return jsonify({'status': 'success'})

# tests/test_new_feature.py
def test_start_feature_success(client):
    """Test successful feature start."""
    response = client.post('/new_feature/start', json={'frequency': '100M'})
    assert response.status_code == 200
    assert response.json['status'] == 'success'

def test_start_feature_missing_frequency(client):
    """Test error when frequency is missing."""
    response = client.post('/new_feature/start', json={})
    assert response.status_code == 400
    assert 'Missing frequency' in response.json['message']
```

---

## Common Development Tasks

### Adding a New RF Mode

1. **Create route module** (`routes/my_mode.py`)
   ```python
   from flask import Blueprint, request, jsonify
   import app as app_module

   my_mode_bp = Blueprint('my_mode', __name__, url_prefix='/my_mode')

   @my_mode_bp.route('/start', methods=['POST'])
   def start_my_mode():
       # Implementation
       return jsonify({'status': 'success'})

   @my_mode_bp.route('/stop', methods=['POST'])
   def stop_my_mode():
       # Implementation
       return jsonify({'status': 'success'})

   @my_mode_bp.route('/stream')
   def stream_my_mode():
       # SSE implementation
       pass
   ```

2. **Add global state to app.py**
   ```python
   # My Mode
   my_mode_process = None
   my_mode_queue = queue.Queue(maxsize=QUEUE_MAX_SIZE)
   my_mode_lock = threading.Lock()
   ```

3. **Register blueprint** (`routes/__init__.py`)
   ```python
   from .my_mode import my_mode_bp
   app.register_blueprint(my_mode_bp)
   ```

4. **Add template** (`templates/partials/modes/my_mode.html`)

5. **Add JavaScript handler** (`static/js/modes/my_mode.js` or in `app.js`)

6. **Add tests** (`tests/test_my_mode.py`)

7. **Update dependencies** (`utils/dependencies.py`)
   ```python
   TOOL_DEPENDENCIES['my_mode'] = {
       'name': 'My Mode',
       'tools': {
           'tool_binary': {'required': True, 'install': 'sudo apt install tool'}
       }
   }
   ```

### Adding a New SDR Hardware Type

1. **Create command builder** (`utils/sdr/my_sdr.py`)
   ```python
   from .base import CommandBuilder, SDRCapabilities

   class MySDRCommandBuilder(CommandBuilder):
       def get_capabilities(self) -> SDRCapabilities:
           return SDRCapabilities(
               min_freq=100e6,
               max_freq=6000e6,
               sample_rates=[2.4e6, 10e6],
               # ...
           )

       def build_fm_command(self, frequency: str, sample_rate: int, gain: str) -> list[str]:
           return ['my_sdr_fm', '-f', frequency, '-g', gain]
   ```

2. **Add detection logic** (`utils/sdr/detection.py`)
   ```python
   # Add to detect_devices()
   if 'MySDR' in device_string:
       devices.append(SDRDevice(
           device_type=SDRDeviceType.MYSDR,
           index=idx,
           serial='...',
           name='MySDR Device'
       ))
   ```

3. **Update factory** (`utils/sdr/__init__.py`)
   ```python
   from .my_sdr import MySDRCommandBuilder

   # In SDRFactory.get_builder():
   elif device.device_type == SDRDeviceType.MYSDR:
       return MySDRCommandBuilder(device)
   ```

4. **Add tests** (`tests/test_sdr_my_sdr.py`)

### Adding Input Validation

Add to `utils/validation.py`:
```python
def validate_my_parameter(value: str) -> tuple[bool, str]:
    """Validate my parameter.

    Args:
        value: Parameter value to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not value:
        return False, "Parameter cannot be empty"

    if not value.isdigit():
        return False, "Parameter must be numeric"

    num = int(value)
    if not (MIN_VALUE <= num <= MAX_VALUE):
        return False, f"Parameter must be between {MIN_VALUE} and {MAX_VALUE}"

    return True, ""
```

Use in route:
```python
from utils.validation import validate_my_parameter

@bp.route('/endpoint', methods=['POST'])
def endpoint():
    value = request.json.get('parameter')
    valid, error = validate_my_parameter(value)
    if not valid:
        return jsonify({'status': 'error', 'message': error}), 400
    # Continue...
```

### Adding Database Table

1. **Define schema** (`utils/database.py`)
   ```python
   def init_db():
       conn = get_db_connection()
       cursor = conn.cursor()
       cursor.execute("""
           CREATE TABLE IF NOT EXISTS my_table (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               field1 TEXT NOT NULL,
               field2 INTEGER,
               created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
           )
       """)
       conn.commit()
   ```

2. **Add CRUD functions** (`utils/database.py`)
   ```python
   def insert_my_record(field1: str, field2: int) -> int:
       """Insert record and return ID."""
       conn = get_db_connection()
       cursor = conn.cursor()
       cursor.execute(
           "INSERT INTO my_table (field1, field2) VALUES (?, ?)",
           (field1, field2)
       )
       conn.commit()
       return cursor.lastrowid

   def get_my_records(limit: int = 100) -> list[dict]:
       """Get records as list of dicts."""
       conn = get_db_connection()
       cursor = conn.cursor()
       cursor.execute("SELECT * FROM my_table ORDER BY created_at DESC LIMIT ?", (limit,))
       columns = [col[0] for col in cursor.description]
       return [dict(zip(columns, row)) for row in cursor.fetchall()]
   ```

3. **Add tests** (`tests/test_database.py`)

### Adding Configuration Option

1. **Add to config.py**
   ```python
   MY_NEW_SETTING = _get_env_int('MY_NEW_SETTING', 100)
   ```

2. **Use in code**
   ```python
   from config import MY_NEW_SETTING

   def my_function():
       timeout = MY_NEW_SETTING
       # ...
   ```

3. **Document in README** (environment variables section)

---

## Important Design Patterns

### 1. Factory Pattern (SDR Hardware)

**Purpose:** Abstract hardware differences behind a common interface

**Location:** `utils/sdr/`

**Usage:**
```python
from utils.sdr import SDRFactory

# Detect all available SDR devices
devices = SDRFactory.detect_devices()

# Get command builder for specific device
device = devices[0]
builder = SDRFactory.get_builder(device)

# Build command for any hardware type
cmd = builder.build_fm_command(frequency='100M', sample_rate=2400000, gain='40')
```

**Key classes:**
- `SDRFactory` - Detects devices, returns appropriate builder
- `CommandBuilder` - Abstract base for all builders
- `RTLSDRCommandBuilder`, `LimeSDRCommandBuilder`, etc. - Concrete implementations

### 2. DataStore Pattern (Auto-Cleanup)

**Purpose:** Automatically remove stale entries to prevent memory leaks

**Location:** `utils/cleanup.py`

**Usage:**
```python
from utils.cleanup import DataStore, cleanup_manager

# Create DataStore with 60-second expiration
my_data = DataStore(max_age_seconds=60, name='my_data')

# Register with cleanup manager
cleanup_manager.register(my_data)

# Use like a dictionary
my_data['key'] = {'data': 'value', 'timestamp': time.time()}

# Entries automatically removed after 60 seconds
```

**Examples in code:**
- `wifi_networks` - WiFi network data (configurable age)
- `adsb_aircraft` - Aircraft tracking data (60 seconds)
- `bt_devices` - Bluetooth device data (300 seconds)

### 3. Process Management Pattern

**Purpose:** Safely manage subprocess lifecycle across multiple threads

**Location:** `utils/process.py`

**Structure:**
```python
# Global state in app.py
my_process = None
my_queue = queue.Queue(maxsize=100)
my_lock = threading.Lock()

# Safe process start
with my_lock:
    if my_process is not None:
        # Kill existing process
        my_process.terminate()
        my_process.wait(timeout=5)

    # Start new process
    my_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Start output reader thread
    threading.Thread(
        target=read_output,
        args=(my_process, my_queue),
        daemon=True
    ).start()
```

### 4. Repository Pattern (Database)

**Purpose:** Centralize database access logic

**Location:** `utils/database.py`

**Pattern:**
```python
# Thread-local connections
_thread_local = threading.local()

def get_db_connection():
    """Get thread-local database connection."""
    if not hasattr(_thread_local, 'connection'):
        _thread_local.connection = sqlite3.connect(DB_PATH)
        _thread_local.connection.row_factory = sqlite3.Row
    return _thread_local.connection

# CRUD operations
def insert_record(...): ...
def get_records(...): ...
def update_record(...): ...
def delete_record(...): ...
```

### 5. Validation Layer Pattern

**Purpose:** Centralize and standardize input validation

**Location:** `utils/validation.py`

**Return format:**
```python
def validate_something(value: str) -> tuple[bool, str]:
    """
    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty.
    """
    if invalid:
        return False, "Error message"
    return True, ""
```

**Usage in routes:**
```python
valid, error = validate_frequency(freq)
if not valid:
    return jsonify({'status': 'error', 'message': error}), 400
```

### 6. SSE (Server-Sent Events) Pattern

**Purpose:** Real-time updates to frontend without WebSocket complexity

**Location:** `utils/sse.py`, individual route modules

**Implementation:**
```python
from flask import Response
from utils.sse import sse_stream

@bp.route('/stream')
def stream():
    def generate():
        while True:
            try:
                # Get data from queue (non-blocking with timeout)
                data = my_queue.get(timeout=30)
                yield f"data: {json.dumps(data)}\n\n"
            except queue.Empty:
                # Send keepalive
                yield ": keepalive\n\n"

    return Response(generate(), mimetype='text/event-stream')
```

**Frontend consumption:**
```javascript
const eventSource = new EventSource('/my_mode/stream');
eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // Update UI
};
```

---

## Security Considerations

### Input Validation

**CRITICAL:** Always validate user input before:
- Passing to shell commands
- Using in SQL queries
- Rendering in HTML
- File operations

**Validation checklist:**
1. **Frequency:** Use `validate_frequency()` - checks format and range
2. **Gain:** Use `validate_gain()` - ensures valid number/string
3. **MAC Address:** Use `validate_mac()` - checks format
4. **IP Address:** Use `validate_ip()` - checks format
5. **Coordinates:** Use `validate_latitude()`, `validate_longitude()` - checks bounds
6. **File paths:** Never allow `..` or absolute paths from user input
7. **HTML content:** Use `html.escape()` before rendering user data

### Command Injection Prevention

**NEVER do this:**
```python
# BAD - vulnerable to command injection
os.system(f"rtl_fm -f {user_frequency}")
```

**ALWAYS do this:**
```python
# GOOD - use list for subprocess, validate input first
valid, error = validate_frequency(user_frequency)
if not valid:
    raise ValueError(error)

subprocess.Popen(['rtl_fm', '-f', user_frequency])
```

### SQL Injection Prevention

**NEVER do this:**
```python
# BAD - vulnerable to SQL injection
cursor.execute(f"SELECT * FROM data WHERE id = {user_id}")
```

**ALWAYS do this:**
```python
# GOOD - use parameterized queries
cursor.execute("SELECT * FROM data WHERE id = ?", (user_id,))
```

### XSS Prevention

**Security headers** (already configured in `app.py`):
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: SAMEORIGIN`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

**Template rendering:**
- Jinja2 auto-escapes by default
- For JSON data, use `jsonify()` not manual `json.dumps()` in templates

### Authentication & Authorization

**Current state:** No authentication (designed for local/trusted network use)

**If adding auth:**
1. Use Flask-Login for session management
2. Hash passwords with bcrypt/argon2
3. Implement CSRF protection with Flask-WTF
4. Add rate limiting with Flask-Limiter
5. Use HTTPS in production

### Secrets Management

**NEVER commit:**
- API keys
- Passwords
- Private keys
- Tokens

**Use:**
- Environment variables for secrets
- `.env` files (add to `.gitignore`)
- Secret management systems for production

### Privilege Requirements

Some features require root:
- WiFi monitor mode (airmon-ng)
- Raw Bluetooth operations (hcitool)
- Direct USB device access (some systems)

**Best practice:**
1. Run as unprivileged user when possible
2. Use `sudo -E` to preserve environment when root needed
3. Add udev rules for USB device access without root
4. Document privilege requirements in feature docs

---

## External Dependencies

### Python Packages

| Package | Version | Purpose | Required |
|---------|---------|---------|----------|
| flask | >=2.0.0 | Web framework | Yes |
| skyfield | >=1.45 | Satellite calculations | Yes |
| pyserial | >=3.5 | GPS serial communication | Optional |
| requests | >=2.28.0 | HTTP client (TLE fetching) | Yes |
| bleak | >=0.21.0 | Bluetooth LE scanning | Optional |
| flask-sock | latest | WebSocket audio streaming | Optional |

### System Tools

#### RF/SDR Tools
| Tool | Purpose | Installation | Required For |
|------|---------|--------------|--------------|
| rtl_fm | RTL-SDR FM demodulation | `apt install rtl-sdr` | Pager, Listening Post |
| multimon-ng | POCSAG/FLEX decoder | `apt install multimon-ng` | Pager |
| rtl_433 | 433MHz sensor decoder | `apt install rtl-433` | 433MHz Sensors |
| dump1090 | ADS-B decoder | Manual build | Aircraft Tracking |
| acarsdec | ACARS decoder | Manual build | ACARS |
| direwolf | APRS decoder | `apt install direwolf` | APRS |

#### WiFi Tools
| Tool | Purpose | Installation | Required For |
|------|---------|--------------|--------------|
| airmon-ng | Monitor mode setup | `apt install aircrack-ng` | WiFi Scanning |
| airodump-ng | Network scanning | `apt install aircrack-ng` | WiFi Scanning |
| aireplay-ng | Deauth/PMKID capture | `apt install aircrack-ng` | WiFi Scanning |

#### Bluetooth Tools
| Tool | Purpose | Installation | Required For |
|------|---------|--------------|--------------|
| bluetoothctl | Bluetooth control | `apt install bluez` | Bluetooth Scanning |
| hcitool | Device scanning | `apt install bluez` | Bluetooth Scanning |

#### SDR Hardware Drivers
| Package | Supported Hardware | Installation |
|---------|-------------------|--------------|
| rtl-sdr | RTL2832U dongles | `apt install rtl-sdr` |
| hackrf | HackRF One | `apt install hackrf` |
| limesuite | LimeSDR | `apt install limesuite` |
| sdrplay | SDRPlay devices | Manual install |
| soapysdr | Multi-vendor support | `apt install soapysdr-tools` |

#### Utilities
| Tool | Purpose | Installation |
|------|---------|--------------|
| lsusb | USB device listing | `apt install usbutils` |
| iw | WiFi device control | `apt install iw` |
| gpsd | GPS daemon | `apt install gpsd` |

### Checking Dependencies

```bash
# Check all dependencies
python intercept.py --check-deps

# Check via API
curl http://localhost:5050/dependencies | jq

# Check specific tool
which rtl_fm && echo "Installed" || echo "Missing"
```

### Installing Dependencies

```bash
# Automated (recommended)
./setup.sh

# Manual (Debian/Ubuntu)
sudo apt update
sudo apt install rtl-sdr multimon-ng rtl-433 aircrack-ng bluez \
    gpsd python3 python3-pip python3-venv

# Manual (macOS)
brew install rtl-sdr multimon-ng rtl_433 aircrack-ng python@3.11
```

---

## Troubleshooting Guide

### Common Issues

#### 1. No SDR Devices Detected

**Symptoms:** Empty device list, "No supported devices found"

**Diagnosis:**
```bash
# Check USB connection
lsusb | grep -i rtl

# Check if kernel driver is blocking
rtl_test -t

# View detailed diagnostics
curl http://localhost:5050/devices/debug | jq
```

**Solutions:**
```bash
# Unload conflicting kernel modules
sudo modprobe -r dvb_usb_rtl28xxu rtl2832 rtl2830

# Add udev rules for permissions
sudo cp /path/to/rtl-sdr.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules

# Reconnect device
```

#### 2. WiFi Monitor Mode Fails

**Symptoms:** "Failed to enable monitor mode", interface not found

**Diagnosis:**
```bash
# Check WiFi interfaces
iw dev

# Check if interface supports monitor mode
iw list | grep -A 8 "Supported interface modes"

# Check if running as root
whoami
```

**Solutions:**
```bash
# Run as root
sudo -E venv/bin/python intercept.py

# Kill conflicting processes
sudo airmon-ng check kill

# Manually enable monitor mode
sudo ip link set wlan0 down
sudo iw dev wlan0 set type monitor
sudo ip link set wlan0 up
```

#### 3. Permission Denied Errors

**Symptoms:** "Permission denied" when starting processes

**Solutions:**
```bash
# Run with sudo (preserves environment)
sudo -E venv/bin/python intercept.py

# Add user to dialout group (for serial devices)
sudo usermod -a -G dialout $USER
# Logout and login again

# Add udev rules for USB devices
sudo cp rules/*.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
```

#### 4. Import Errors

**Symptoms:** `ModuleNotFoundError: No module named 'flask'`

**Solutions:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Check Python version (needs 3.9+)
python --version
```

#### 5. Process Won't Stop

**Symptoms:** "Kill all processes" doesn't stop everything

**Solutions:**
```bash
# Manual cleanup
sudo pkill -f rtl_fm
sudo pkill -f multimon-ng
sudo pkill -f dump1090
sudo pkill -f airodump-ng

# Force kill if needed
sudo pkill -9 -f rtl_fm

# Check for orphaned processes
ps aux | grep rtl
```

#### 6. Database Errors

**Symptoms:** "database is locked", "no such table"

**Solutions:**
```bash
# Remove and reinitialize database
rm instance/intercept.db
# Restart application (will auto-create)

# Check file permissions
ls -la instance/
chmod 644 instance/intercept.db
```

#### 7. Docker USB Access

**Symptoms:** No SDR devices in Docker container

**Solutions:**
```yaml
# Ensure privileged mode in docker-compose.yml
services:
  intercept:
    privileged: true
    devices:
      - /dev/bus/usb:/dev/bus/usb  # Explicit USB passthrough

# OR run with --privileged flag
docker run --privileged -p 5050:5050 intercept
```

#### 8. Port Already in Use

**Symptoms:** "Address already in use" on port 5050

**Solutions:**
```bash
# Find process using port
sudo lsof -i :5050
sudo netstat -tlnp | grep 5050

# Kill process
sudo kill <PID>

# OR use different port
python intercept.py --port 5051
```

### Debug Logging

Enable verbose logging:
```bash
export INTERCEPT_LOG_LEVEL=DEBUG
python intercept.py 2>&1 | tee debug.log
```

View specific module logs:
```python
# In code
from utils.logging import pager_logger
pager_logger.setLevel(logging.DEBUG)
```

### Getting Help

1. **Check documentation:** `docs/TROUBLESHOOTING.md`
2. **Search issues:** https://github.com/smittix/intercept/issues
3. **Discord server:** https://discord.gg/EyeksEJmWE
4. **Create issue:** Provide logs, OS, Python version, error messages

---

## Quick Reference

### Start Application

```bash
# Development
python intercept.py

# Production (with root)
sudo -E venv/bin/python intercept.py

# Custom port/host
python intercept.py --host 0.0.0.0 --port 8080

# Debug mode
python intercept.py --debug
```

### Run Tests

```bash
pytest                  # All tests
pytest -v              # Verbose
pytest -k wifi         # Match pattern
pytest --cov           # With coverage
pytest -x              # Stop on first fail
```

### Code Quality

```bash
black .                # Format code
ruff check .           # Lint code
ruff --fix .           # Auto-fix issues
mypy utils/            # Type check
```

### Docker

```bash
docker compose up -d          # Start
docker compose down           # Stop
docker compose logs -f        # View logs
docker compose up -d --build  # Rebuild
```

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Main interface |
| `/health` | GET | Health check |
| `/devices` | GET | List SDR devices |
| `/devices/debug` | GET | Device diagnostics |
| `/dependencies` | GET | Tool dependency status |
| `/pager/start` | POST | Start pager decoder |
| `/pager/stop` | POST | Stop pager decoder |
| `/pager/stream` | GET | SSE stream of pager messages |
| `/wifi/start` | POST | Start WiFi scanning |
| `/adsb/start` | POST | Start aircraft tracking |
| `/killall` | POST | Kill all processes |

### File Locations

| Purpose | Location |
|---------|----------|
| Application code | `app.py`, `routes/`, `utils/` |
| Configuration | `config.py`, environment variables |
| Templates | `templates/` |
| Static assets | `static/` |
| Tests | `tests/` |
| Database | `instance/intercept.db` |
| Logs | `instance/logs/` (if enabled) |
| Documentation | `docs/`, `README.md` |

---

## Appendix: Glossary

| Term | Definition |
|------|------------|
| **ADS-B** | Automatic Dependent Surveillance-Broadcast (aircraft tracking) |
| **ACARS** | Aircraft Communications Addressing and Reporting System |
| **APRS** | Automatic Packet Reporting System (amateur radio) |
| **Blueprint** | Flask's modular routing system |
| **POCSAG** | Post Office Code Standardisation Advisory Group (pager protocol) |
| **FLEX** | Pager protocol (successor to POCSAG) |
| **RTL-SDR** | Realtek SDR (USB TV tuner repurposed as SDR) |
| **SDR** | Software-Defined Radio |
| **SSE** | Server-Sent Events (one-way server push) |
| **TSCM** | Technical Surveillance Countermeasures |
| **TLE** | Two-Line Element (satellite orbital data) |
| **TPMS** | Tire Pressure Monitoring System |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-24 | Initial comprehensive CLAUDE.md creation |

---

**End of CLAUDE.md**

For questions or improvements to this guide, please open an issue at:
https://github.com/smittix/intercept/issues
