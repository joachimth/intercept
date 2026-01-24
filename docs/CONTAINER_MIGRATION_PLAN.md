# INTERCEPT Container Migration Plan

> **Status:** Planning Phase
> **Target Date:** Q1 2026
> **Inspired By:** ADSB.fi/adsb.lol containerized architecture

---

## Executive Summary

This document outlines a comprehensive plan to migrate INTERCEPT from a monolithic bare-metal installation to a modern, containerized architecture. This migration will improve maintainability, security, update mechanisms, and align with industry best practices demonstrated by successful SDR platforms like ADSB.fi.

### Key Benefits

✅ **Easier Updates** - Application updates independent of OS
✅ **Better Security** - Isolation between services, no privileged mode
✅ **Simpler Maintenance** - Container restart vs full system reboot
✅ **Modular Architecture** - Enable/disable features independently
✅ **Reduced SD Card Wear** - Strategic use of tmpfs for high I/O operations
✅ **Professional Deployment** - Aligned with modern DevOps practices

---

## Current State Analysis

### Current INTERCEPT Architecture (v2.9.5)

```
┌─────────────────────────────────────────────────────────┐
│           Raspberry Pi OS (Monolithic)                  │
├─────────────────────────────────────────────────────────┤
│  System Packages (installed via apt):                  │
│   - rtl-sdr, multimon-ng, rtl_433                       │
│   - dump1090 (compiled from source)                     │
│   - acarsdec (compiled from source)                     │
│   - aircrack-ng, bluez, gpsd                            │
│   - Python 3.9+ with venv                               │
├─────────────────────────────────────────────────────────┤
│  Application (/opt/intercept):                          │
│   - Flask application (app.py)                          │
│   - 15 route modules (routes/)                          │
│   - Utilities (utils/)                                  │
│   - Templates & static files                            │
│   - SQLite database (instance/)                         │
├─────────────────────────────────────────────────────────┤
│  Systemd Service:                                       │
│   - intercept.service (auto-start)                      │
└─────────────────────────────────────────────────────────┘
```

### Problems with Current Approach

| Issue | Impact | Example |
|-------|--------|---------|
| **Monolithic Updates** | OS and app updates coupled | `apt upgrade` might break intercept |
| **Dependency Conflicts** | System-wide package versions | Python version conflicts |
| **No Rollback** | Failed updates require full reinstall | Breaking change in dump1090 |
| **Manual Compilation** | dump1090, acarsdec built during setup | 20-30 minute setup time |
| **Privilege Mixing** | Root required for WiFi but runs entire app | Security risk |
| **No Health Checks** | Crashed processes not auto-restarted | Manual intervention needed |
| **SD Card Wear** | Logs and temp files on SD card | Reduced lifespan |
| **Update Distribution** | Monthly OS image rebuilds | Users on old versions |

---

## Target Architecture

### Proposed Multi-Container Architecture

```
┌─────────────────────────────────────────────────────────┐
│         Raspberry Pi OS Lite (Minimal Base)             │
│         - Docker + Docker Compose                        │
│         - RTL-SDR udev rules & kernel blacklists        │
│         - Minimal dependencies (git, curl)              │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │   Docker Daemon         │
        │   (systemd managed)     │
        └────────┬────────────────┘
                 │
    ┌────────────┴─────────────────────────────────┐
    │      Docker Compose Stack                    │
    │      (/opt/intercept/docker-compose.yml)     │
    └────────┬─────────────────────────────────────┘
             │
    ┌────────┴──────────────────────────────────────────────┐
    │                                                        │
┌───┴────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐
│intercept-  │  │intercept-│  │intercept-│  │intercept-   │
│core        │  │adsb      │  │acars     │  │pager        │
│            │  │          │  │          │  │             │
│Flask UI    │  │dump1090  │  │acarsdec  │  │multimon-ng  │
│Orchestrator│  │tar1090   │  │          │  │rtl_fm       │
└────────────┘  └──────────┘  └──────────┘  └─────────────┘
       │
┌──────┴────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│intercept-     │  │intercept-│  │intercept-│  │watchtower│
│sensors        │  │wifi      │  │bluetooth │  │          │
│               │  │          │  │          │  │Auto-     │
│rtl_433        │  │aircrack  │  │bleak     │  │updates   │
└───────────────┘  └──────────┘  └──────────┘  └──────────┘
       │
┌──────┴────────┐  ┌──────────┐
│intercept-     │  │autoheal  │
│scanner        │  │          │
│               │  │Health    │
│rtl_fm + audio │  │monitor   │
└───────────────┘  └──────────┘
```

### Container Breakdown

| Container | Base Image | Purpose | Size Est. | Required |
|-----------|------------|---------|-----------|----------|
| **intercept-core** | python:3.11-slim | Web UI, API, orchestration | ~200MB | ✅ Yes |
| **intercept-adsb** | debian:bookworm-slim | ADS-B tracking (dump1090, tar1090) | ~150MB | Optional |
| **intercept-acars** | debian:bookworm-slim | ACARS messages (acarsdec) | ~100MB | Optional |
| **intercept-pager** | debian:bookworm-slim | Pager decoding (multimon-ng, rtl_fm) | ~80MB | Optional |
| **intercept-sensors** | debian:bookworm-slim | 433MHz sensors (rtl_433) | ~80MB | Optional |
| **intercept-wifi** | kalilinux/kali-rolling | WiFi scanning (aircrack-ng) | ~300MB | Optional |
| **intercept-bluetooth** | python:3.11-slim | Bluetooth scanning (bleak) | ~150MB | Optional |
| **intercept-scanner** | debian:bookworm-slim | Frequency scanner + audio | ~100MB | Optional |
| **watchtower** | containrrr/watchtower | Auto container updates | ~15MB | Optional |
| **autoheal** | willfarrell/autoheal | Health monitoring | ~10MB | Optional |

**Total Stack Size:** ~1.2GB (vs current ~3-4GB monolithic image)

---

## Migration Strategy

### Phase 1: Container Development (Weeks 1-3)

#### 1.1 Create Base Container Structure

```
intercept/
├── containers/
│   ├── core/
│   │   ├── Dockerfile
│   │   ├── entrypoint.sh
│   │   └── requirements.txt
│   ├── adsb/
│   │   ├── Dockerfile
│   │   ├── build-dump1090.sh
│   │   └── entrypoint.sh
│   ├── acars/
│   │   ├── Dockerfile
│   │   ├── build-acarsdec.sh
│   │   └── entrypoint.sh
│   ├── pager/
│   │   ├── Dockerfile
│   │   └── entrypoint.sh
│   ├── sensors/
│   │   ├── Dockerfile
│   │   └── entrypoint.sh
│   ├── wifi/
│   │   ├── Dockerfile
│   │   └── entrypoint.sh
│   ├── bluetooth/
│   │   ├── Dockerfile
│   │   └── entrypoint.sh
│   └── scanner/
│       ├── Dockerfile
│       └── entrypoint.sh
├── docker-compose.yml
├── docker-compose.override.yml.example
└── .env.example
```

#### 1.2 Core Container Dockerfile

```dockerfile
# containers/core/Dockerfile
FROM python:3.11-slim

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create app user (non-root)
RUN useradd -m -u 1000 intercept && \
    mkdir -p /app /data && \
    chown -R intercept:intercept /app /data

WORKDIR /app

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py config.py intercept.py ./
COPY routes/ ./routes/
COPY utils/ ./utils/
COPY data/ ./data/
COPY templates/ ./templates/
COPY static/ ./static/

# Switch to non-root user
USER intercept

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:5050/health || exit 1

# Expose port
EXPOSE 5050

# Run application
CMD ["python", "intercept.py", "--host", "0.0.0.0"]
```

#### 1.3 ADSB Container Dockerfile

```dockerfile
# containers/adsb/Dockerfile
FROM debian:bookworm-slim AS builder

# Build dump1090-fa from source
RUN apt-get update && apt-get install -y --no-install-recommends \
    git build-essential libncurses-dev librtlsdr-dev pkg-config \
    && git clone --depth 1 https://github.com/flightaware/dump1090.git /tmp/dump1090 \
    && cd /tmp/dump1090 \
    && make RTLSDR=yes \
    && rm -rf /var/lib/apt/lists/*

FROM debian:bookworm-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    librtlsdr0 libncurses6 lighttpd \
    && rm -rf /var/lib/apt/lists/*

# Copy built binary from builder
COPY --from=builder /tmp/dump1090/dump1090 /usr/local/bin/
COPY --from=builder /tmp/dump1090/public_html /var/www/html/

# Create data directory
RUN mkdir -p /data/adsb && chmod 777 /data/adsb

EXPOSE 30003 30005 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s \
  CMD netstat -an | grep -q ':30003' || exit 1

CMD ["dump1090", "--net", "--quiet"]
```

#### 1.4 Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  core:
    container_name: intercept-core
    build:
      context: .
      dockerfile: containers/core/Dockerfile
    image: intercept/core:${VERSION:-latest}
    restart: unless-stopped
    ports:
      - "${INTERCEPT_PORT:-5050}:5050"
    volumes:
      - ./data/config:/data/config
      - ./data/instance:/app/instance
      - /etc/localtime:/etc/localtime:ro
      - /etc/timezone:/etc/timezone:ro
    environment:
      - INTERCEPT_HOST=0.0.0.0
      - INTERCEPT_PORT=5050
      - INTERCEPT_LOG_LEVEL=${LOG_LEVEL:-INFO}
    tmpfs:
      - /tmp:size=64M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5050/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - intercept-network

  adsb:
    container_name: intercept-adsb
    build:
      context: .
      dockerfile: containers/adsb/Dockerfile
    image: intercept/adsb:${VERSION:-latest}
    restart: unless-stopped
    devices:
      - "c 189:* rwm"  # USB character devices
    volumes:
      - ./data/adsb:/data/adsb
      - /etc/localtime:/etc/localtime:ro
    environment:
      - ADSB_ENABLED=${ADSB_ENABLED:-true}
    tmpfs:
      - /tmp:size=64M
      - /var/log:size=32M
    networks:
      - intercept-network
    profiles:
      - adsb
      - full

  acars:
    container_name: intercept-acars
    build:
      context: .
      dockerfile: containers/acars/Dockerfile
    image: intercept/acars:${VERSION:-latest}
    restart: unless-stopped
    devices:
      - "c 189:* rwm"
    volumes:
      - ./data/acars:/data/acars
    tmpfs:
      - /tmp:size=64M
    networks:
      - intercept-network
    profiles:
      - acars
      - full

  pager:
    container_name: intercept-pager
    build:
      context: .
      dockerfile: containers/pager/Dockerfile
    image: intercept/pager:${VERSION:-latest}
    restart: unless-stopped
    devices:
      - "c 189:* rwm"
    volumes:
      - ./data/pager:/data/pager
    tmpfs:
      - /tmp:size=64M
    networks:
      - intercept-network
    profiles:
      - pager
      - full

  sensors:
    container_name: intercept-sensors
    build:
      context: .
      dockerfile: containers/sensors/Dockerfile
    image: intercept/sensors:${VERSION:-latest}
    restart: unless-stopped
    devices:
      - "c 189:* rwm"
    volumes:
      - ./data/sensors:/data/sensors
    tmpfs:
      - /tmp:size=64M
    networks:
      - intercept-network
    profiles:
      - sensors
      - full

  wifi:
    container_name: intercept-wifi
    build:
      context: .
      dockerfile: containers/wifi/Dockerfile
    image: intercept/wifi:${VERSION:-latest}
    restart: unless-stopped
    network_mode: host  # Required for monitor mode
    cap_add:
      - NET_ADMIN
      - NET_RAW
    volumes:
      - ./data/wifi:/data/wifi
    tmpfs:
      - /tmp:size=128M
    profiles:
      - wifi
      - full

  bluetooth:
    container_name: intercept-bluetooth
    build:
      context: .
      dockerfile: containers/bluetooth/Dockerfile
    image: intercept/bluetooth:${VERSION:-latest}
    restart: unless-stopped
    cap_add:
      - NET_ADMIN
    volumes:
      - ./data/bluetooth:/data/bluetooth
      - /var/run/dbus:/var/run/dbus:ro
    tmpfs:
      - /tmp:size=64M
    networks:
      - intercept-network
    profiles:
      - bluetooth
      - full

  scanner:
    container_name: intercept-scanner
    build:
      context: .
      dockerfile: containers/scanner/Dockerfile
    image: intercept/scanner:${VERSION:-latest}
    restart: unless-stopped
    devices:
      - "c 189:* rwm"
    volumes:
      - ./data/scanner:/data/scanner
    tmpfs:
      - /tmp:size=64M
    networks:
      - intercept-network
    profiles:
      - scanner
      - full

  # Auto-update containers (optional)
  watchtower:
    container_name: intercept-watchtower
    image: containrrr/watchtower:latest
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - WATCHTOWER_CLEANUP=true
      - WATCHTOWER_POLL_INTERVAL=86400  # Check daily
      - WATCHTOWER_INCLUDE_STOPPED=true
      - WATCHTOWER_REVIVE_STOPPED=false
    profiles:
      - auto-update
      - full

  # Auto-restart unhealthy containers (optional)
  autoheal:
    container_name: intercept-autoheal
    image: willfarrell/autoheal:latest
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - AUTOHEAL_CONTAINER_LABEL=all
      - AUTOHEAL_INTERVAL=10
      - AUTOHEAL_START_PERIOD=30
    profiles:
      - auto-heal
      - full

networks:
  intercept-network:
    driver: bridge

volumes:
  config:
  instance:
  adsb:
  acars:
  pager:
  sensors:
  wifi:
  bluetooth:
  scanner:
```

### Phase 2: Installation Scripts (Week 4)

#### 2.1 intercept-init Script

```bash
#!/bin/bash
# bin/intercept-init - Initial setup script

set -e

INSTALL_DIR="/opt/intercept"
REPO_URL="https://github.com/smittix/intercept.git"

echo "=================================="
echo "  INTERCEPT Installation Script"
echo "=================================="
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   exit 1
fi

# Detect architecture
ARCH=$(uname -m)
if [[ "$ARCH" != "armv7l" && "$ARCH" != "aarch64" && "$ARCH" != "x86_64" ]]; then
    echo "Unsupported architecture: $ARCH"
    exit 1
fi

# Install minimal system dependencies
echo "Installing system dependencies..."
apt-get update
apt-get install -y --no-install-recommends \
    git \
    curl \
    jq \
    ca-certificates \
    gnupg \
    lsb-release

# Blacklist RTL-SDR kernel drivers
echo "Blacklisting RTL-SDR kernel modules..."
cat > /etc/modprobe.d/blacklist-rtl-sdr.conf <<EOF
blacklist dvb_usb_rtl28xxu
blacklist rtl2832
blacklist rtl2830
EOF

# Install Docker if not already installed
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker pi || true
else
    echo "Docker already installed"
fi

# Install Docker Compose if not already installed
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | jq -r '.tag_name')
    curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose already installed"
fi

# Clone or update repository
if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull --ff-only
else
    echo "Cloning repository..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Create .env file if not exists
if [ ! -f .env ]; then
    echo "Creating .env configuration..."
    cp .env.example .env
    echo "Please edit /opt/intercept/.env to configure your installation"
fi

# Create data directories
echo "Creating data directories..."
mkdir -p data/{config,instance,adsb,acars,pager,sensors,wifi,bluetooth,scanner}
chown -R 1000:1000 data/

# Install CLI symlinks
echo "Installing CLI tools..."
ln -sf "$INSTALL_DIR/bin/intercept-init" /usr/local/bin/intercept-init
ln -sf "$INSTALL_DIR/bin/intercept-update" /usr/local/bin/intercept-update
ln -sf "$INSTALL_DIR/bin/intercept-up" /usr/local/bin/intercept-up
ln -sf "$INSTALL_DIR/bin/intercept-down" /usr/local/bin/intercept-down
ln -sf "$INSTALL_DIR/bin/intercept-logs" /usr/local/bin/intercept-logs

# Enable Docker service
systemctl enable docker
systemctl start docker

echo ""
echo "=================================="
echo "  Installation Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit configuration: nano $INSTALL_DIR/.env"
echo "2. Start INTERCEPT: intercept-up"
echo "3. View logs: intercept-logs"
echo "4. Access UI: http://$(hostname -I | awk '{print $1}'):5050"
echo ""
```

#### 2.2 intercept-update Script

```bash
#!/bin/bash
# bin/intercept-update - Update script

set -e

INSTALL_DIR="/opt/intercept"

echo "=================================="
echo "  INTERCEPT Update"
echo "=================================="
echo ""

cd "$INSTALL_DIR"

# Pull latest code
echo "Pulling latest code..."
git pull --ff-only

# Pull latest container images
echo "Pulling container images..."
docker-compose pull

# Restart containers
echo "Restarting containers..."
docker-compose up -d

echo ""
echo "Update complete!"
echo "View logs: intercept-logs"
```

#### 2.3 Helper Scripts

```bash
# bin/intercept-up
#!/bin/bash
cd /opt/intercept
docker-compose up -d "$@"

# bin/intercept-down
#!/bin/bash
cd /opt/intercept
docker-compose down "$@"

# bin/intercept-logs
#!/bin/bash
cd /opt/intercept
docker-compose logs -f "$@"

# bin/intercept-env
#!/bin/bash
cd /opt/intercept
nano .env
```

### Phase 3: Core Application Refactoring (Weeks 5-6)

#### 3.1 Modify app.py for Container Communication

```python
# app.py - Container-aware modifications

import os
import requests

# Container endpoints (via Docker network)
CONTAINER_ENDPOINTS = {
    'adsb': os.getenv('ADSB_ENDPOINT', 'http://intercept-adsb:30003'),
    'acars': os.getenv('ACARS_ENDPOINT', 'http://intercept-acars:5550'),
    'pager': os.getenv('PAGER_ENDPOINT', 'http://intercept-pager:7355'),
    'sensors': os.getenv('SENSORS_ENDPOINT', 'http://intercept-sensors:1433'),
}

def check_container_health(service):
    """Check if a container service is running."""
    try:
        endpoint = CONTAINER_ENDPOINTS.get(service)
        if not endpoint:
            return False
        response = requests.get(f"{endpoint}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

@app.route('/services/status')
def services_status():
    """Get status of all container services."""
    return jsonify({
        service: check_container_health(service)
        for service in CONTAINER_ENDPOINTS.keys()
    })
```

#### 3.2 Create Container Health Endpoints

Each container needs a simple health endpoint:

```python
# In each container's service
from flask import Flask, jsonify

health_app = Flask(__name__)

@health_app.route('/health')
def health():
    # Check if primary process is running
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    health_app.run(host='0.0.0.0', port=8080)
```

### Phase 4: Testing & Validation (Week 7)

#### 4.1 Local Testing

```bash
# Build all containers
docker-compose build

# Start core services only
docker-compose up -d core

# Start with specific profile
docker-compose --profile adsb up -d

# Start full stack
docker-compose --profile full up -d

# Test health
curl http://localhost:5050/health
curl http://localhost:5050/services/status

# View logs
docker-compose logs -f core
```

#### 4.2 Raspberry Pi Testing

```bash
# Test on Raspberry Pi 4
# Transfer compose files
scp -r docker-compose.yml containers/ pi@raspberrypi:/tmp/

# SSH and test
ssh pi@raspberrypi
cd /tmp
docker-compose up -d core
```

### Phase 5: Documentation (Week 8)

#### 5.1 Update Documentation

- `docs/DOCKER_INSTALLATION.md` - Container installation guide
- `docs/CONTAINER_ARCHITECTURE.md` - Architecture documentation
- `docs/MIGRATION_GUIDE.md` - Migration from monolithic to containers
- `docs/TROUBLESHOOTING_DOCKER.md` - Container-specific troubleshooting
- `README.md` - Update with new installation methods

#### 5.2 Create Video Guides

- Installation walkthrough
- Configuration guide
- Update procedure
- Troubleshooting common issues

### Phase 6: GitHub Actions CI/CD (Week 9)

#### 6.1 Container Build Workflow

```yaml
# .github/workflows/build-containers.yml
name: Build and Push Docker Containers

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        container: [core, adsb, acars, pager, sensors, wifi, bluetooth, scanner]

    steps:
      - uses: actions/checkout@v4

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: intercept/${{ matrix.container }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          file: containers/${{ matrix.container }}/Dockerfile
          platforms: linux/amd64,linux/arm64,linux/arm/v7
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

#### 6.2 Raspberry Pi Image Build (Updated)

```yaml
# .github/workflows/build-rpi-image.yml
# Simplified version that installs Docker instead of all dependencies

- name: Customize image
  run: |
    # Install Docker only
    chroot /mnt/rpi-root /bin/bash -c "curl -fsSL https://get.docker.com | sh"

    # Install intercept-init script
    cp bin/intercept-init /mnt/rpi-root/usr/local/bin/
    chmod +x /mnt/rpi-root/usr/local/bin/intercept-init

    # Create first-boot service
    cp .github/scripts/intercept-firstboot.service /mnt/rpi-root/etc/systemd/system/
    chroot /mnt/rpi-root systemctl enable intercept-firstboot
```

### Phase 7: Release & Migration Support (Week 10)

#### 7.1 Create Release

- Tag release: `v3.0.0` (major version bump for architecture change)
- Publish containers to Docker Hub
- Release Raspberry Pi image with Docker pre-installed
- Publish documentation

#### 7.2 Migration Support

Create migration script for existing users:

```bash
#!/bin/bash
# migrate-to-containers.sh

echo "Migrating INTERCEPT to containerized architecture..."

# Backup current installation
sudo systemctl stop intercept
sudo cp -r /opt/intercept /opt/intercept.backup

# Run new installer
curl -fsSL https://raw.githubusercontent.com/smittix/intercept/main/install.sh | sudo bash

# Migrate data
sudo cp /opt/intercept.backup/instance/intercept.db /opt/intercept/data/instance/
sudo cp -r /opt/intercept.backup/data/* /opt/intercept/data/config/

# Start new stack
intercept-up

echo "Migration complete! Old installation backed up to /opt/intercept.backup"
```

---

## Implementation Checklist

### Must-Have (v3.0.0)

- [ ] Core container with Flask application
- [ ] ADSB container with dump1090
- [ ] Docker Compose configuration
- [ ] Installation script (intercept-init)
- [ ] Update script (intercept-update)
- [ ] Basic documentation
- [ ] GitHub Actions for container builds
- [ ] Migration guide for existing users

### Should-Have (v3.1.0)

- [ ] ACARS container
- [ ] Pager container
- [ ] Sensors container
- [ ] Health monitoring (autoheal)
- [ ] Auto-updates (watchtower)
- [ ] Comprehensive documentation
- [ ] Video tutorials

### Could-Have (v3.2.0)

- [ ] WiFi container (complex due to network_mode: host)
- [ ] Bluetooth container
- [ ] Scanner container
- [ ] Web-based container management UI
- [ ] Automatic backup/restore
- [ ] Container resource limits configuration
- [ ] Advanced logging (ELK stack integration)

---

## Success Metrics

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| **Setup Time** | 20-30 min | <5 min | Time from download to running |
| **Update Time** | Manual reinstall | <2 min | Time for `intercept-update` |
| **Image Size** | 3-4GB | <2GB | Base image + containers |
| **Memory Usage** | ~800MB | ~600MB | docker stats |
| **Restart Time** | 60-90s | <20s | Service restart duration |
| **Failed Updates** | N/A | <1% | User reports |
| **SD Card Lifespan** | ~1 year | >2 years | Community feedback |

---

## Risk Assessment & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Learning curve for users** | Medium | High | Detailed docs, video tutorials, migration script |
| **Container networking complexity** | High | Medium | Extensive testing, fallback to host network |
| **WiFi monitor mode in container** | High | High | Document limitations, provide host network option |
| **USB device passthrough issues** | High | Medium | Test on multiple platforms, document device cgroups |
| **Increased complexity** | Medium | High | Keep simple default config, advanced options optional |
| **Breaking changes for existing users** | High | High | Maintain v2.x branch, provide migration path |
| **Docker Hub rate limits** | Medium | Low | Push to GHCR as backup registry |

---

## Timeline Summary

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **Phase 1** | 3 weeks | Container structure, Dockerfiles, docker-compose.yml |
| **Phase 2** | 1 week | Installation scripts, CLI tools |
| **Phase 3** | 2 weeks | Application refactoring, container communication |
| **Phase 4** | 1 week | Testing on multiple platforms |
| **Phase 5** | 1 week | Documentation, video guides |
| **Phase 6** | 1 week | CI/CD workflows, automated builds |
| **Phase 7** | 1 week | Release, migration support, community feedback |

**Total: 10 weeks (~2.5 months)**

---

## Alternative Approaches Considered

### 1. Balena Cloud

**Pros:**
- OTA updates via cloud
- Fleet management
- Easy multi-device deployment

**Cons:**
- Cloud dependency
- Monthly fees for >10 devices
- Less control for power users
- Privacy concerns

**Decision:** Not recommended for INTERCEPT due to privacy-focused user base

### 2. Kubernetes (K3s)

**Pros:**
- Industry standard orchestration
- Advanced features (auto-scaling, rollbacks)
- Service mesh capabilities

**Cons:**
- Overkill for single-device deployment
- High resource usage on Raspberry Pi
- Steep learning curve
- Complex troubleshooting

**Decision:** Not recommended - Docker Compose is sufficient

### 3. Snap Packages

**Pros:**
- Automatic updates
- Easy distribution
- Built-in isolation

**Cons:**
- Limited USB device access
- Ubuntu-only (not Raspberry Pi OS)
- Less flexible than containers
- Canonical-specific

**Decision:** Not recommended - doesn't align with Raspberry Pi ecosystem

### 4. Keep Current Monolithic + Add Update Script

**Pros:**
- Minimal changes
- No learning curve
- Simpler architecture

**Cons:**
- Doesn't solve core problems
- No isolation between services
- Still couples OS and app updates
- Misses industry best practices

**Decision:** Rejected - doesn't provide long-term benefits

---

## Conclusion

Migrating INTERCEPT to a containerized architecture inspired by ADSB.fi will significantly improve maintainability, security, and user experience. The multi-container approach provides:

1. **Separation of Concerns** - OS updates don't affect applications
2. **Modular Design** - Users enable only features they need
3. **Easy Updates** - `intercept-update` handles everything
4. **Professional Infrastructure** - Aligns with modern DevOps practices
5. **Future-Proof** - Easier to add new features and integrations

The 10-week implementation plan is ambitious but achievable with focused development. The phased approach allows for iterative testing and community feedback.

**Recommendation:** Proceed with Phase 1 immediately to validate the architecture before committing to full migration.

---

## Next Steps

1. **Approval** - Get community feedback on proposed architecture
2. **Proof of Concept** - Build core + adsb containers for testing
3. **Community Testing** - Beta release for early adopters
4. **Documentation** - Create comprehensive guides
5. **Production Release** - v3.0.0 with container architecture

---

**Document Version:** 1.0
**Author:** Claude (AI Assistant)
**Date:** 2026-01-24
**Status:** Proposal - Pending Approval
