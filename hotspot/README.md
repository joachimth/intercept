# INTERCEPT WiFi Hotspot Captive Portal

Automatic WiFi setup for INTERCEPT when no network is detected at boot.

## How It Works

1. **Boot Detection**: System checks for network connectivity at boot
2. **Hotspot Launch**: If no network found, automatically starts WiFi hotspot
3. **Captive Portal**: User connects via mobile device to `intercept-setup` network
4. **Configuration**: Web portal allows WiFi network selection and password entry
5. **Connection**: System connects to selected network and INTERCEPT becomes available

## Files

- `hotspot-app.py` - Flask captive portal application
- `hostapd.conf.template` - Hostapd configuration (access point)
- `dnsmasq.conf.template` - DNS/DHCP configuration
- `start-hotspot.sh` - Hotspot startup script

## Manual Usage

Start hotspot manually:

```bash
sudo /opt/intercept/hotspot/start-hotspot.sh
```

This will:
1. Configure wlan0 with static IP (192.168.199.1)
2. Start hostapd (WiFi AP)
3. Start dnsmasq (DHCP/DNS)
4. Launch captive portal on port 80

## Access

Connect to WiFi network:
- **SSID**: `intercept-setup`
- **Password**: None (open network)

Your device should automatically open captive portal. If not, visit:
- http://192.168.199.1

## Architecture

```
┌─────────────────────────────────────────┐
│  Mobile Device                          │
│  Connects to "intercept-setup"          │
└──────────────┬──────────────────────────┘
               │
               ↓ DNS redirect (dnsmasq)
┌──────────────────────────────────────────┐
│  Captive Portal (Flask on port 80)      │
│  - Scan WiFi networks (iwlist)           │
│  - Display selection form                │
│  - Configure wpa_supplicant              │
│  - Restart networking                    │
└──────────────┬───────────────────────────┘
               │
               ↓ Connect to home WiFi
┌──────────────────────────────────────────┐
│  INTERCEPT Main App                      │
│  Available at http://intercept.local:5050│
└──────────────────────────────────────────┘
```

## Captive Portal Detection

The portal responds to common captive portal detection URLs:

- `/generate_204` - Android detection
- `/hotspot-detect.html` - iOS detection
- `/` - All other requests

All DNS queries are redirected to 192.168.199.1 via dnsmasq `address` directive.

## Security Notes

- Hotspot is **open** (no WPA) for ease of setup
- Only used for initial configuration
- Automatically disabled after WiFi is configured
- No sensitive data transmitted over hotspot

## Customization

### Change SSID

Edit `hotspot/hostapd.conf.template`:

```bash
ssid=your-custom-name
```

### Change IP Range

Edit `hotspot/dnsmasq.conf.template`:

```bash
dhcp-range=192.168.X.10,192.168.X.250,255.255.255.0,24h
dhcp-option=3,192.168.X.1
```

And update `start-hotspot.sh`:

```bash
ip addr add 192.168.X.1/24 dev wlan0
```

## Troubleshooting

### Hotspot doesn't start

```bash
# Check wlan0 exists
ip link show wlan0

# Check services
systemctl status hostapd
systemctl status dnsmasq

# View logs
journalctl -u hostapd -f
journalctl -u dnsmasq -f
```

### Can't see SSID

```bash
# Ensure wlan0 supports AP mode
iw list | grep -A 10 "Supported interface modes"

# Restart hostapd
systemctl restart hostapd
```

### Captive portal doesn't open

```bash
# Check Flask is running
ps aux | grep hotspot-app.py

# Check port 80
netstat -tlnp | grep :80

# Manual access
curl http://192.168.199.1
```

### WiFi configuration fails

```bash
# Check wpa_supplicant
cat /etc/wpa_supplicant/wpa_supplicant.conf

# Test connection manually
wpa_cli -i wlan0 reconfigure
wpa_cli -i wlan0 status
```

## Future Enhancements

- [ ] Automatic boot detection service
- [ ] Progress indicator during connection
- [ ] Connection status check before redirect
- [ ] Support for WPA-Enterprise networks
- [ ] Bluetooth pairing alternative
- [ ] QR code configuration option
