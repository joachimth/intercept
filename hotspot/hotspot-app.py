#!/usr/bin/env python3
"""
WiFi Hotspot Captive Portal for INTERCEPT
Automatically launched when no network is detected at boot
"""

from flask import Flask, request, render_template_string, redirect
import subprocess
import os
import sys

app = Flask(__name__)

# HTML template for captive portal
PORTAL_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>INTERCEPT WiFi Setup</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            max-width: 400px;
            width: 100%;
            padding: 40px;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 24px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        label {
            display: block;
            color: #333;
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 14px;
        }
        select, input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            margin-bottom: 20px;
            transition: border-color 0.3s;
        }
        select:focus, input:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        button:active {
            transform: translateY(0);
        }
        .message {
            background: #f0f9ff;
            border: 1px solid #0ea5e9;
            color: #0c4a6e;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
        }
        .error {
            background: #fef2f2;
            border-color: #ef4444;
            color: #7f1d1d;
        }
        .loading {
            display: none;
            text-align: center;
            margin-top: 20px;
        }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛰️ INTERCEPT Setup</h1>
        <p class="subtitle">Connect to your WiFi network</p>

        {% if message %}
        <div class="message {{ 'error' if error else '' }}">
            {{ message }}
        </div>
        {% endif %}

        <form method="POST" id="wifiForm">
            <label for="ssid">WiFi Network</label>
            <select name="ssid" id="ssid" required>
                <option value="">Select network...</option>
                {% for network in networks %}
                <option value="{{ network }}">{{ network }}</option>
                {% endfor %}
            </select>

            <label for="password">Password</label>
            <input type="password" name="password" id="password"
                   placeholder="Enter WiFi password" required>

            <button type="submit">Connect</button>
        </form>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p style="margin-top: 15px; color: #666;">Connecting...</p>
        </div>
    </div>

    <script>
        document.getElementById('wifiForm').addEventListener('submit', function() {
            document.getElementById('loading').style.display = 'block';
        });
    </script>
</body>
</html>
"""

SUCCESS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>INTERCEPT - Connected</title>
    <meta http-equiv="refresh" content="10;url=http://intercept.local:5050">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            max-width: 400px;
            width: 100%;
            padding: 40px;
            text-align: center;
        }
        .checkmark {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            display: block;
            stroke-width: 3;
            stroke: #10b981;
            stroke-miterlimit: 10;
            margin: 0 auto 20px;
            box-shadow: inset 0px 0px 0px #10b981;
            animation: fill .4s ease-in-out .4s forwards, scale .3s ease-in-out .9s both;
        }
        .checkmark__circle {
            stroke-dasharray: 166;
            stroke-dashoffset: 166;
            stroke-width: 3;
            stroke-miterlimit: 10;
            stroke: #10b981;
            fill: none;
            animation: stroke 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;
        }
        .checkmark__check {
            transform-origin: 50% 50%;
            stroke-dasharray: 48;
            stroke-dashoffset: 48;
            animation: stroke 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.8s forwards;
        }
        @keyframes stroke {
            100% { stroke-dashoffset: 0; }
        }
        @keyframes fill {
            100% { box-shadow: inset 0px 0px 0px 30px #10b981; }
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 24px;
        }
        p {
            color: #666;
            margin-bottom: 10px;
            line-height: 1.6;
        }
    </style>
</head>
<body>
    <div class="container">
        <svg class="checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
            <circle class="checkmark__circle" cx="26" cy="26" r="25" fill="none"/>
            <path class="checkmark__check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
        </svg>
        <h1>✅ Connected!</h1>
        <p>INTERCEPT is connecting to <strong>{{ ssid }}</strong></p>
        <p style="margin-top: 20px; font-size: 14px;">
            Redirecting to INTERCEPT in 10 seconds...<br>
            Or visit: <a href="http://intercept.local:5050">http://intercept.local:5050</a>
        </p>
    </div>
</body>
</html>
"""


def scan_wifi_networks():
    """Scan for available WiFi networks"""
    try:
        # Run iwlist scan
        result = subprocess.run(
            ['iwlist', 'wlan0', 'scan'],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Parse SSIDs from output
        networks = []
        for line in result.stdout.split('\n'):
            if 'ESSID:' in line:
                ssid = line.split('ESSID:')[1].strip('"').strip()
                if ssid and ssid not in networks:
                    networks.append(ssid)

        return sorted(networks)
    except Exception as e:
        print(f"Error scanning networks: {e}", file=sys.stderr)
        return ['Example-Network', 'Home-WiFi']  # Fallback


def configure_wifi(ssid, password):
    """Configure wpa_supplicant with WiFi credentials"""
    try:
        # Create wpa_supplicant configuration
        config = f"""
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
"""

        # Write to wpa_supplicant.conf
        with open('/etc/wpa_supplicant/wpa_supplicant.conf', 'w') as f:
            f.write(config)

        # Restart networking
        subprocess.run(['systemctl', 'restart', 'dhcpcd'], check=True)
        subprocess.run(['wpa_cli', '-i', 'wlan0', 'reconfigure'], check=True)

        return True
    except Exception as e:
        print(f"Error configuring WiFi: {e}", file=sys.stderr)
        return False


@app.route('/', methods=['GET', 'POST'])
@app.route('/generate_204')  # Android captive portal detection
@app.route('/hotspot-detect.html')  # iOS captive portal detection
def index():
    if request.method == 'POST':
        ssid = request.form.get('ssid')
        password = request.form.get('password')

        if not ssid or not password:
            networks = scan_wifi_networks()
            return render_template_string(
                PORTAL_HTML,
                networks=networks,
                message="Please select a network and enter password",
                error=True
            )

        # Configure WiFi
        if configure_wifi(ssid, password):
            return render_template_string(SUCCESS_HTML, ssid=ssid)
        else:
            networks = scan_wifi_networks()
            return render_template_string(
                PORTAL_HTML,
                networks=networks,
                message="Failed to configure WiFi. Please try again.",
                error=True
            )

    # GET request - show form
    networks = scan_wifi_networks()
    return render_template_string(PORTAL_HTML, networks=networks, message=None)


if __name__ == '__main__':
    # Run captive portal on port 80 (requires root)
    app.run(host='0.0.0.0', port=80, debug=False)
