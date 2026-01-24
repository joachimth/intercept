# INTERCEPT Management Scripts

Collection of command-line tools for managing INTERCEPT installation.

## Installation

```bash
# One-liner installation
curl -fsSL https://raw.githubusercontent.com/smittix/intercept/main/bin/intercept-init | sudo bash

# Or manual installation
git clone https://github.com/smittix/intercept.git
cd intercept
sudo ./bin/intercept-init
```

## Commands

### intercept-init
Initial setup script. Installs Docker, clones repository, and configures system.

```bash
sudo intercept-init
```

**What it does:**
- Installs Docker and Docker Compose
- Blacklists RTL-SDR kernel modules
- Clones INTERCEPT repository to `/opt/intercept`
- Creates data directories
- Installs CLI tools
- Configures system services

### intercept-up
Start INTERCEPT containers.

```bash
intercept-up              # Start all containers
intercept-up intercept    # Start only main container
```

### intercept-down
Stop INTERCEPT containers.

```bash
intercept-down           # Stop all containers
intercept-down --volumes # Stop and remove volumes
```

### intercept-restart
Restart INTERCEPT containers.

```bash
intercept-restart         # Restart all
intercept-restart intercept # Restart main container
```

### intercept-logs
View container logs (follow mode).

```bash
intercept-logs           # All containers
intercept-logs intercept # Main container only
intercept-logs --tail=50 # Last 50 lines
```

**Tip:** Press `Ctrl+C` to exit log view

### intercept-update
Update INTERCEPT to latest version.

```bash
sudo intercept-update
```

**What it does:**
- Creates backup of current configuration
- Pulls latest code from GitHub
- Updates Docker images
- Restarts containers
- Shows changelog

## File Locations

| Path | Purpose |
|------|---------|
| `/opt/intercept` | Installation directory |
| `/opt/intercept/data` | Persistent data (SQLite DB, configs) |
| `/opt/intercept/data/backups` | Configuration backups |
| `/opt/intercept/.env` | Environment variables |
| `/usr/local/bin/intercept-*` | CLI tools (symlinks) |

## Environment Variables

Edit `/opt/intercept/.env`:

```bash
INTERCEPT_HOST=0.0.0.0        # Listen address
INTERCEPT_PORT=5050           # Web UI port
INTERCEPT_LOG_LEVEL=INFO      # Logging level (DEBUG, INFO, WARNING, ERROR)
INTERCEPT_DEBUG=false         # Debug mode
```

## Troubleshooting

### Container won't start
```bash
# Check logs
intercept-logs

# Check Docker status
sudo systemctl status docker

# Restart Docker
sudo systemctl restart docker
intercept-up
```

### Permission denied
```bash
# Add your user to docker group
sudo usermod -aG docker $USER

# Log out and back in for changes to take effect
```

### USB devices not detected
```bash
# Check if devices are visible
lsusb

# Ensure RTL-SDR kernel modules are blacklisted
cat /etc/modprobe.d/blacklist-rtl-sdr.conf

# Reconnect USB device
```

### Updates fail
```bash
# Check git status
cd /opt/intercept
git status

# Reset if needed
sudo git reset --hard origin/main
sudo intercept-update
```

## Advanced

### Manual Docker commands

```bash
cd /opt/intercept

# Build container
docker-compose build

# View running containers
docker-compose ps

# Execute command in container
docker-compose exec intercept bash

# View resource usage
docker stats intercept
```

### Enable auto-updates (Watchtower)

Edit `docker-compose.yml` and uncomment watchtower profile:

```yaml
watchtower:
  # profiles:
  #   - autoupdate
```

Then start with profile:
```bash
docker-compose --profile autoupdate up -d
```

### Backup and restore

```bash
# Manual backup
sudo tar -czf intercept_backup.tar.gz -C /opt/intercept data .env

# Restore
sudo tar -xzf intercept_backup.tar.gz -C /opt/intercept
intercept-restart
```

## Development

### Local testing

```bash
# Build local image
cd /opt/intercept
docker-compose build

# Run with custom tag
docker-compose -f docker-compose.yml up -d
```

### Contribute

See main [CONTRIBUTING.md](../CONTRIBUTING.md)
