# INTERCEPT

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Raspberry%20Pi-lightgrey.svg" alt="Platform">
  <a href="https://github.com/smittix/intercept/releases/latest">
    <img src="https://img.shields.io/badge/Raspberry%20Pi%20OS-ready--to--use%20image-C51A4A?logo=raspberry-pi&logoColor=white" alt="Raspberry Pi OS Image">
  </a>
  <img src="https://img.shields.io/github/v/release/smittix/intercept?label=latest%20release" alt="Latest Release">
  <img src="https://img.shields.io/github/actions/workflow/status/smittix/intercept/build-custom-os.yml?label=image%20build" alt="RPi Image Build">
</p>

<p align="center">
Support the developer of this open-source project 
</p>

<p align="center">
  <a href="https://www.buymeacoffee.com/smittix" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" ></a>
</p>
<p align="center">
  <strong>Signal Intelligence Platform</strong><br>
  A web-based interface for software-defined radio tools.
</p>

<p align="center">
  <img src="static/images/screenshots/intercept-main.png" alt="Screenshot">
</p>

> **🎉 New!** Pre-built Raspberry Pi OS images now available! Get up and running in minutes with our [ready-to-use images](#raspberry-pi-custom-os-image-easiest-). Just flash to SD card and boot!

---

## Features

- **Pager Decoding** - POCSAG/FLEX via rtl_fm + multimon-ng
- **433MHz Sensors** - Weather stations, TPMS, IoT devices via rtl_433
- **Aircraft Tracking** - ADS-B via dump1090 with real-time map and radar
- **ACARS Messaging** - Aircraft datalink messages via acarsdec
- **Listening Post** - Frequency scanner with audio monitoring
- **Satellite Tracking** - Pass prediction using TLE data
- **WiFi Scanning** - Monitor mode reconnaissance via aircrack-ng
- **Bluetooth Scanning** - Device discovery and tracker detection

---

## Installation / Debian / Ubuntu / MacOS

```

**1. Clone and run:**
```bash
git clone https://github.com/smittix/intercept.git
cd intercept
./setup.sh
sudo -E venv/bin/python intercept.py
```

### Docker (Alternative)

```bash
git clone https://github.com/smittix/intercept.git
cd intercept
docker compose up -d
```

> **Note:** Docker requires privileged mode for USB SDR access. See `docker-compose.yml` for configuration options.

### Raspberry Pi Custom OS Image (Easiest) ⚡

**Pre-built Raspberry Pi OS images with intercept ready to use!**

We automatically build and release custom Raspberry Pi OS images monthly. These images have intercept pre-installed with all dependencies and auto-start on boot.

#### 📥 Download

**Latest Release:** [Download from GitHub Releases](https://github.com/smittix/intercept/releases/latest)

- **File:** `intercept-rpi-os-*.img.xz` (~2-3 GB compressed)
- **Base:** Raspberry Pi OS Lite (latest)
- **Updated:** Automatically built monthly

#### 🚀 Quick Installation

1. **Download** the latest `.img.xz` file from [Releases](https://github.com/smittix/intercept/releases)
2. **Flash** to SD card (8GB+) using:
   - [Raspberry Pi Imager](https://www.raspberrypi.com/software/) (recommended)
   - [Balena Etcher](https://www.balena.io/etcher/)
3. **Insert** SD card into your Raspberry Pi (3B+ or newer)
4. **Power on** and wait 2-3 minutes for first boot
5. **Access** intercept at `http://<raspberry-pi-ip>:5050`

#### 🔐 Default Credentials

- **User:** `intercept`
- **Password:** `intercept`

**⚠️ Change password after first login:** `ssh intercept@<ip>` then run `passwd`

#### 📖 Additional Info

- SSH is enabled by default
- Intercept runs automatically as a systemd service
- WiFi setup: See [Custom OS Image Documentation](docs/CUSTOM_OS_IMAGE.md)
- Service control: `sudo systemctl status intercept`
- View logs: `sudo journalctl -u intercept -f`

**Full documentation:** [Custom OS Image Guide](docs/CUSTOM_OS_IMAGE.md)

### Open the Interface

After starting, open **http://localhost:5050** in your browser.

---

## Hardware Requirements

| Hardware | Purpose | Price |
|----------|---------|-------|
| **RTL-SDR** | Required for all SDR features | ~$25-35 |
| **WiFi adapter** | Must support promiscuous (monitor) mode | ~$20-40 |
| **Bluetooth adapter** | Device scanning (usually built-in) | - |
| **GPS** | Any Linux supported GPS Unit | ~10 |

Most features work with a basic RTL-SDR dongle (RTL2832U + R820T2).

| :exclamation:  Not using an RTL-SDR Device?   |
|-----------------------------------------------
|Intercept supports any device that SoapySDR supports. You must however have the correct module for your device installed! For example if you have an SDRPlay device you'd need to install soapysdr-module-sdrplay.

| :exclamation:  GPS Usage   |
|-----------------------------------------------
|gpsd is needed for real time location. Intercept automatically checks to see if you're running gpsd in the background when any maps are rendered.

---

## Discord Server

<p align="center">
  <a href="https://discord.gg/EyeksEJmWE">Join our Discord</a>
</p>


---

## Documentation

- [Usage Guide](docs/USAGE.md) - Detailed instructions for each mode
- [Hardware Guide](docs/HARDWARE.md) - SDR hardware and advanced setup
- [Custom OS Image](docs/CUSTOM_OS_IMAGE.md) - Pre-built Raspberry Pi OS images
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [Security](docs/SECURITY.md) - Network security and best practices

---

## Disclaimer

This project was developed using AI as a coding partner, combining human direction with AI-assisted implementation. The goal: make Software Defined Radio more accessible by providing a clean, unified interface for common SDR tools.

**This software is for educational and authorized testing purposes only.**

- Only use with proper authorization
- Intercepting communications without consent may be illegal
- You are responsible for compliance with applicable laws

---

## License

MIT License - see [LICENSE](LICENSE)

## Author

Created by **smittix** - [GitHub](https://github.com/smittix)

## Acknowledgments

[rtl-sdr](https://osmocom.org/projects/rtl-sdr/wiki) |
[multimon-ng](https://github.com/EliasOenal/multimon-ng) |
[rtl_433](https://github.com/merbanan/rtl_433) |
[dump1090](https://github.com/flightaware/dump1090) |
[acarsdec](https://github.com/TLeconte/acarsdec) |
[aircrack-ng](https://www.aircrack-ng.org/) |
[Leaflet.js](https://leafletjs.com/) |
[Celestrak](https://celestrak.org/)








