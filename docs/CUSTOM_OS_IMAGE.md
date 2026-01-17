# Intercept Custom Raspberry Pi OS Image

## Overview

Intercept provides automatically generated custom Raspberry Pi OS images with intercept pre-installed and configured to start automatically on boot. This is the easiest way to get started with intercept on a Raspberry Pi.

## Features

- **Pre-installed intercept** with all dependencies
- **Auto-starts on boot** as a systemd service
- **SSH enabled** by default
- **Ready to use** - just flash and boot
- **Automated builds** via GitHub Actions
- **Verified checksums** for security

## Quick Start

### 1. Download the Image

Download the latest custom OS image from the [Releases page](https://github.com/smittix/intercept/releases):

- Look for the latest release with attached `.img.xz` file
- Download both the image file and the `.sha256` checksum file

### 2. Verify the Image (Optional but Recommended)

```bash
sha256sum -c intercept-rpi-os-*.img.xz.sha256
```

You should see: `intercept-rpi-os-*.img.xz: OK`

### 3. Flash to SD Card

#### Using Raspberry Pi Imager (Recommended)

1. Download and install [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Insert your SD card (minimum 8GB, 16GB+ recommended)
3. Open Raspberry Pi Imager
4. Click "Choose OS" → "Use custom" → Select the downloaded `.img.xz` file
5. Click "Choose Storage" → Select your SD card
6. Click "Write" and wait for completion

#### Using Command Line (Linux/macOS)

```bash
# Extract the image
xz -d intercept-rpi-os-*.img.xz

# Find your SD card device (be very careful!)
lsblk

# Flash the image (replace /dev/sdX with your SD card device)
sudo dd if=intercept-rpi-os-*.img of=/dev/sdX bs=4M status=progress conv=fsync

# Safely unmount
sync
sudo eject /dev/sdX
```

#### Using Balena Etcher

1. Download and install [Balena Etcher](https://www.balena.io/etcher/)
2. Open Etcher
3. Click "Flash from file" → Select the `.img.xz` file
4. Click "Select target" → Select your SD card
5. Click "Flash!"

### 4. First Boot

1. Insert the SD card into your Raspberry Pi
2. Connect network cable (or configure WiFi - see below)
3. Power on the Raspberry Pi
4. Wait 2-3 minutes for first boot initialization
5. Find your Raspberry Pi's IP address (check your router or use `nmap`)

### 5. Access Intercept

Open your browser and navigate to:

```
http://<raspberry-pi-ip>:5050
```

For example: `http://192.168.1.100:5050`

## Default Credentials

### System Login (SSH)

- **Username:** `intercept`
- **Password:** `intercept`

### Raspberry Pi Default User

The standard `pi` user is also available:

- **Username:** `pi`
- **Password:** `raspberry`

**⚠️ IMPORTANT:** Change these default passwords after first login!

```bash
# SSH into the Raspberry Pi
ssh intercept@<raspberry-pi-ip>

# Change password
passwd
```

## Configuration

### WiFi Setup

If you're not using Ethernet, you can configure WiFi before first boot:

1. After flashing, the SD card will have a boot partition mounted
2. Create a file named `wpa_supplicant.conf` in the boot partition:

```conf
country=DK
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="Your_WiFi_Name"
    psk="Your_WiFi_Password"
    key_mgmt=WPA-PSK
}
```

3. Safely eject the SD card and insert into Raspberry Pi
4. Boot the Raspberry Pi - it will connect to WiFi automatically

### Hostname

The default hostname is `intercept`. You can change it:

```bash
sudo hostnamectl set-hostname my-intercept
sudo reboot
```

### Service Management

Intercept runs as a systemd service:

```bash
# Check status
sudo systemctl status intercept

# View logs
sudo journalctl -u intercept -f

# Restart service
sudo systemctl restart intercept

# Stop service
sudo systemctl stop intercept

# Start service
sudo systemctl start intercept

# Disable auto-start
sudo systemctl disable intercept

# Enable auto-start
sudo systemctl enable intercept
```

### Configuration Files

Intercept configuration is located at:
- Application: `/opt/intercept/`
- Data directory: `/opt/intercept/data/`
- Service file: `/etc/systemd/system/intercept.service`

To modify environment variables:

```bash
sudo systemctl edit intercept
```

Add your overrides:

```ini
[Service]
Environment="INTERCEPT_PORT=8080"
Environment="INTERCEPT_LOG_LEVEL=DEBUG"
```

Then restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart intercept
```

## Updating Intercept

To update intercept to the latest version:

```bash
# Stop the service
sudo systemctl stop intercept

# Navigate to intercept directory
cd /opt/intercept

# Pull latest changes
sudo -u intercept git pull

# Update dependencies if needed
sudo -u intercept venv/bin/pip install -r requirements.txt

# Restart the service
sudo systemctl start intercept
```

## Building Custom Images

### Automated Build via GitHub Actions

The custom OS image is built automatically via GitHub Actions when:

1. **Manual trigger:** Go to Actions → "Build Custom Raspberry Pi OS Image" → Run workflow
2. **Tag push:** Push a new version tag (e.g., `git tag v2.9.6 && git push --tags`)
3. **Release creation:** Create a new release on GitHub

### Workflow Parameters

When manually triggering the workflow, you can specify:

- **RPI OS version date:** The version of Raspberry Pi OS to use (default: 2024-11-19)
- **Image type:** Choose between:
  - `lite` - Minimal installation (recommended, ~2GB)
  - `desktop` - With desktop environment (~4GB)
  - `full` - Complete installation with all software (~8GB)

### Local Build (Advanced)

You can also build the image locally on a Linux system:

```bash
# Clone the repository
git clone https://github.com/smittix/intercept.git
cd intercept

# Install dependencies
sudo apt-get install -y \
    wget curl unzip xz-utils kpartx qemu-user-static \
    binfmt-support parted fdisk dosfstools e2fsprogs systemd-container

# Download base image
wget https://downloads.raspberrypi.org/raspios_lite_armhf_latest -O raspios.img.xz
xz -d raspios.img.xz
mv raspios.img base-image.img

# Expand image
dd if=/dev/zero bs=1M count=4096 >> base-image.img
echo ", +" | sudo sfdisk -N 2 base-image.img

# Mount and customize
LOOP_DEVICE=$(sudo losetup -fP --show base-image.img)
sudo e2fsck -f -y ${LOOP_DEVICE}p2 || true
sudo resize2fs ${LOOP_DEVICE}p2

sudo mkdir -p /mnt/rpi-boot /mnt/rpi-root
sudo mount ${LOOP_DEVICE}p1 /mnt/rpi-boot
sudo mount ${LOOP_DEVICE}p2 /mnt/rpi-root

# Copy files
sudo mkdir -p /mnt/rpi-root/opt/intercept
sudo cp -r . /mnt/rpi-root/opt/intercept/
sudo rm -rf /mnt/rpi-root/opt/intercept/.git

sudo cp .github/scripts/customize-image.sh /mnt/rpi-root/tmp/
sudo cp .github/scripts/intercept.service /mnt/rpi-root/etc/systemd/system/
sudo touch /mnt/rpi-boot/ssh

# Run customization in chroot
sudo cp /usr/bin/qemu-arm-static /mnt/rpi-root/usr/bin/
sudo chroot /mnt/rpi-root /bin/bash /tmp/customize-image.sh

# Cleanup
sync
sudo umount /mnt/rpi-boot
sudo umount /mnt/rpi-root
sudo losetup -d $LOOP_DEVICE

# Compress
xz -9 -T 0 base-image.img
```

## Troubleshooting

### Can't Access Web Interface

1. **Check if service is running:**
   ```bash
   sudo systemctl status intercept
   ```

2. **Check logs:**
   ```bash
   sudo journalctl -u intercept -n 50
   ```

3. **Verify network connectivity:**
   ```bash
   ip addr show
   ping google.com
   ```

4. **Check if port 5050 is open:**
   ```bash
   sudo netstat -tlnp | grep 5050
   ```

### Service Won't Start

1. **Check Python dependencies:**
   ```bash
   cd /opt/intercept
   source venv/bin/activate
   pip list
   ```

2. **Test manual start:**
   ```bash
   cd /opt/intercept
   sudo -E venv/bin/python intercept.py --debug
   ```

3. **Check permissions:**
   ```bash
   ls -la /opt/intercept
   # Should be owned by intercept:intercept
   ```

### WiFi Not Connecting

1. **Check wpa_supplicant configuration:**
   ```bash
   sudo cat /etc/wpa_supplicant/wpa_supplicant.conf
   ```

2. **Check WiFi status:**
   ```bash
   sudo iwconfig
   sudo wpa_cli status
   ```

3. **Reconfigure WiFi:**
   ```bash
   sudo raspi-config
   # Navigate to System Options → Wireless LAN
   ```

### Image Won't Boot

1. **Verify image integrity:**
   - Check SHA256 checksum before flashing
   - Try re-downloading the image

2. **Check SD card:**
   - Use a quality SD card (Class 10, A1 or better)
   - Try a different SD card
   - Check for physical damage

3. **Flash again:**
   - Some SD cards need multiple write attempts
   - Try a different flashing tool

## Hardware Requirements

### Minimum

- **Raspberry Pi:** 3B or newer
- **SD Card:** 8GB Class 10 (16GB+ recommended)
- **Power Supply:** Official Raspberry Pi power supply
- **Network:** Ethernet or WiFi

### Recommended

- **Raspberry Pi:** 4B with 4GB+ RAM
- **SD Card:** 32GB A1/A2 rated
- **SDR Hardware:** RTL-SDR dongle (RTL2832U based)
- **WiFi Adapter:** With monitor mode support (Alfa AWUS036ACH recommended)
- **GPS Dongle:** For accurate time sync (optional)
- **Bluetooth Adapter:** For BLE scanning (optional, built-in on Pi 3B+/4)

## Security Considerations

⚠️ **Important Security Notes:**

1. **Change default passwords immediately**
2. **Configure firewall if exposed to internet:**
   ```bash
   sudo apt-get install ufw
   sudo ufw allow 22/tcp    # SSH
   sudo ufw allow 5050/tcp  # Intercept
   sudo ufw enable
   ```

3. **Disable SSH if not needed:**
   ```bash
   sudo systemctl disable ssh
   ```

4. **Run on isolated network segment** when performing RF monitoring
5. **Keep system updated:**
   ```bash
   sudo apt-get update
   sudo apt-get upgrade
   ```

## Support

For issues, questions, or contributions:

- **GitHub Issues:** https://github.com/smittix/intercept/issues
- **Documentation:** https://github.com/smittix/intercept/tree/main/docs
- **Main README:** https://github.com/smittix/intercept/blob/main/README.md

## License

This custom OS image is provided under the same MIT License as the intercept project.

See [LICENSE](../LICENSE) for details.
