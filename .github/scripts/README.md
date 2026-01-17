# Custom OS Image Build Scripts

This directory contains scripts used by the GitHub Actions workflow to build custom Raspberry Pi OS images with intercept pre-installed.

## Files

### `customize-image.sh`

This script runs inside a chroot environment on the Raspberry Pi OS image and:

1. Updates and upgrades all system packages
2. Installs all system dependencies (RTL-SDR tools, aircrack-ng, bluez, etc.)
3. Configures RTL-SDR udev rules and blacklists conflicting drivers
4. Creates the `intercept` user with sudo privileges
5. Sets up Python virtual environment and installs intercept dependencies
6. Configures system services (gpsd, bluetooth)
7. Enables the intercept systemd service
8. Sets hostname to `intercept`
9. Creates a welcome message with usage instructions

### `intercept.service`

Systemd service unit file that:

- Starts intercept automatically on boot
- Runs as root (required for WiFi monitor mode and SDR access)
- Restarts automatically on failure
- Waits for network and bluetooth services to be available
- Logs output to systemd journal

## Usage

These scripts are automatically used by the GitHub Actions workflow (`.github/workflows/build-custom-os.yml`).

For manual usage, see the [Custom OS Image Documentation](../../docs/CUSTOM_OS_IMAGE.md).

## Customization

You can modify these scripts to:

- Change default user credentials
- Add additional packages
- Modify service configuration
- Change network settings
- Add pre-configured WiFi credentials

After modifications, the next workflow run will include your changes in the generated image.
