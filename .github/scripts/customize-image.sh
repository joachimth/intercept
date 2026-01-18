#!/bin/bash
# Intercept Custom OS Image Customization Script
# This script runs in a chroot environment to customize the Raspberry Pi OS image

set -e

echo "================================"
echo "Intercept OS Customization"
echo "================================"

# Prevent initramfs updates during package installation (doesn't work properly in chroot)
echo "[0/8] Disabling initramfs updates temporarily..."
export INITRD=No
cat > /usr/sbin/policy-rc.d << 'EOF'
#!/bin/sh
exit 101
EOF
chmod +x /usr/sbin/policy-rc.d

# Update package lists
echo "[1/8] Updating package lists..."
apt-get update

# Upgrade existing packages
echo "[2/8] Upgrading system packages..."
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y || {
    echo "Warning: Some packages had errors during upgrade, continuing..."
}

# Install base dependencies
echo "[3/8] Installing base system dependencies..."
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    git \
    wget \
    curl \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    pkg-config \
    cmake \
    libusb-1.0-0-dev \
    librtlsdr-dev \
    rtl-sdr \
    sox \
    libsox-fmt-all \
    gnuplot \
    gnuplot-x11 \
    sqlite3 \
    bluez \
    bluez-tools \
    libbluetooth-dev \
    python3-bluez \
    gpsd \
    gpsd-clients \
    python3-gps \
    aircrack-ng \
    wireless-tools \
    net-tools \
    iw \
    hcxtools \
    hcxdumptool \
    ffmpeg \
    libavcodec-extra

# Install RTL-SDR tools
echo "[4/8] Installing RTL-SDR and SDR tools..."
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    rtl-433 \
    multimon-ng \
    dump1090-mutability \
    soapysdr-tools \
    soapysdr-module-rtlsdr \
    hackrf \
    limesuite \
    soapysdr-module-hackrf \
    soapysdr-module-lms7

# Try to install kalibrate-rtl if available (not in all repos)
DEBIAN_FRONTEND=noninteractive apt-get install -y kalibrate-rtl || {
    echo "kalibrate-rtl not available in repos, skipping..."
}

# Try to install acarsdec if available
DEBIAN_FRONTEND=noninteractive apt-get install -y acarsdec || {
    echo "acarsdec not available in repos, will be built from source if needed"
}

# Try to install direwolf if available
DEBIAN_FRONTEND=noninteractive apt-get install -y direwolf || {
    echo "direwolf not available in repos, will be built from source if needed"
}

# Configure RTL-SDR udev rules and blacklist
echo "[5/8] Configuring RTL-SDR..."
cat > /etc/udev/rules.d/rtl-sdr.rules << 'EOF'
# RTL-SDR
SUBSYSTEM=="usb", ATTRS{idVendor}=="0bda", ATTRS{idProduct}=="2838", GROUP="plugdev", MODE="0666", SYMLINK+="rtl_sdr"
# HackRF
SUBSYSTEM=="usb", ATTRS{idVendor}=="1d50", ATTRS{idProduct}=="6089", GROUP="plugdev", MODE="0666"
# LimeSDR
SUBSYSTEM=="usb", ATTRS{idVendor}=="1d50", ATTRS{idProduct}=="6108", GROUP="plugdev", MODE="0666"
EOF

# Blacklist DVB-T drivers that conflict with RTL-SDR
cat > /etc/modprobe.d/blacklist-rtl-sdr.conf << 'EOF'
blacklist dvb_usb_rtl28xxu
blacklist rtl2832
blacklist rtl2830
EOF

# Create intercept user if it doesn't exist
echo "[6/8] Setting up intercept user..."
if ! id -u intercept > /dev/null 2>&1; then
    useradd -m -s /bin/bash -G sudo,plugdev,bluetooth intercept
    echo "intercept:intercept" | chpasswd
    echo "Created user 'intercept' with password 'intercept'"
fi

# Setup intercept application
echo "[7/8] Installing intercept application..."
cd /opt/intercept

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment and install requirements
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
fi

# Install optional dependencies for full functionality
pip install bleak skyfield pyserial || true

deactivate

# Set proper ownership
chown -R intercept:intercept /opt/intercept

# Create data directory
mkdir -p /opt/intercept/data
chown -R intercept:intercept /opt/intercept/data

# Enable and configure services
echo "[8/8] Configuring system services..."

# Enable and start gpsd
systemctl enable gpsd || true

# Enable and start bluetooth
systemctl enable bluetooth
systemctl start bluetooth || true

# Enable intercept service
systemctl enable intercept.service

# Configure hostname (optional)
echo "intercept" > /etc/hostname
sed -i 's/raspberrypi/intercept/g' /etc/hosts

# Set timezone to UTC (change as needed)
timedatectl set-timezone UTC || ln -sf /usr/share/zoneinfo/UTC /etc/localtime

# Configure network (enable WiFi if available)
# User will need to configure WiFi credentials via wpa_supplicant or raspi-config

# Clean up
echo "Cleaning up..."
apt-get autoremove -y
apt-get clean
rm -rf /var/lib/apt/lists/*
rm -rf /tmp/*
rm -rf /var/tmp/*

# Remove policy-rc.d
rm -f /usr/sbin/policy-rc.d

# Create welcome message
cat > /etc/motd << 'EOF'

 _____ _   _ _____ _____ ____   ____ _____ ____ _____
|_   _| \ | |_   _| ____|  _ \ / ___| ____|  _ \_   _|
  | | |  \| | | | |  _| | |_) | |   |  _| | |_) || |
  | | | |\  | | | | |___|  _ <| |___| |___|  __/ | |
  |_| |_| \_| |_| |_____|_| \_\\____|_____|_|    |_|

Signal Intelligence (SIGINT) Platform
https://github.com/smittix/intercept

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Welcome to the Intercept Custom Raspberry Pi OS!

Intercept is now running as a systemd service.
Access the web interface at: http://$(hostname -I | awk '{print $1}'):5050

Useful commands:
  sudo systemctl status intercept    - Check service status
  sudo systemctl restart intercept   - Restart intercept
  sudo journalctl -u intercept -f    - View logs
  cd /opt/intercept                  - Go to intercept directory

Default credentials:
  User: intercept
  Password: intercept

⚠️  IMPORTANT: Change the default password after first login!
    Run: passwd

For more information, visit the documentation at:
/opt/intercept/README.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF

echo "================================"
echo "Customization complete!"
echo "================================"
