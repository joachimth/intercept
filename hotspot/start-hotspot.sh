#!/bin/bash
# start-hotspot.sh - Start WiFi hotspot for INTERCEPT setup

set -e

echo "Starting INTERCEPT WiFi hotspot..."

# Stop services
systemctl stop hostapd 2>/dev/null || true
systemctl stop dnsmasq 2>/dev/null || true
systemctl stop dhcpcd 2>/dev/null || true

# Configure wlan0
ip link set wlan0 down
ip addr flush dev wlan0
ip addr add 192.168.199.1/24 dev wlan0
ip link set wlan0 up

# Copy configuration files
cp /opt/intercept/hotspot/hostapd.conf.template /etc/hostapd/hostapd.conf
cp /opt/intercept/hotspot/dnsmasq.conf.template /etc/dnsmasq.conf

# Start services
systemctl start dnsmasq
systemctl start hostapd

echo "Hotspot started: SSID=intercept-setup"
echo "Starting captive portal..."

# Start captive portal
python3 /opt/intercept/hotspot/hotspot-app.py
