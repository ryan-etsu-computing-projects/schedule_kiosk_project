# Raspberry Pi Kiosk Display Setup Guide

This guide will help you deploy your University Schedule Kiosk Display on a Raspberry Pi as an auto-starting service with fullscreen Chromium display.

## Prerequisites

- Raspberry Pi (3B+ or newer recommended)
- Raspberry Pi OS (Desktop version)
- Your kiosk display project files
- Internet connection for initial setup

## Part 1: System Setup and Project Deployment

### 1. Update Your Raspberry Pi

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Required System Packages

```bash
sudo apt install -y python3-pip python3-venv git chromium-browser unclutter
```

### 3. Deploy Your Project

Create a dedicated directory for your kiosk:

```bash
sudo mkdir -p /opt/kiosk-display
sudo chown pi:pi /opt/kiosk-display
cd /opt/kiosk-display
```

Copy your project files to this directory, then set up the Python environment:

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install flask flask-cors gunicorn

# Make sure your data directory exists with CSV files
mkdir -p data
# Copy your CSV files to the data directory
```

### 4. Test Your Application

Before setting up services, verify everything works:

```bash
cd /opt/kiosk-display
source .venv/bin/activate
python app.py
```

Test by opening a browser and navigating to `http://localhost:5000`

## Part 2: Create Flask Service

### 1. Create Systemd Service File

Create `/etc/systemd/system/kiosk-display.service`:

```ini
[Unit]
Description=University Schedule Kiosk Display
After=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/opt/kiosk-display
Environment=PATH=/opt/kiosk-display/.venv/bin
ExecStart=/opt/kiosk-display/.venv/bin/gunicorn -w 2 -b 127.0.0.1:5000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start the Service

```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable kiosk-display.service

# Start the service now
sudo systemctl start kiosk-display.service

# Check service status
sudo systemctl status kiosk-display.service
```

## Part 3: Configure Auto-Launch Chromium

### 1. Create Kiosk Launch Script

Create `/home/pi/start_kiosk.sh`:

```bash
#!/bin/bash

# Wait for the Flask service to be ready
echo "Waiting for Flask service to start..."
while ! curl -s http://localhost:5000 > /dev/null; do
    sleep 2
done

# Hide mouse cursor
unclutter -idle 0.5 -root &

# Launch Chromium in kiosk mode
chromium-browser \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-suggestions-service \
    --disable-translate \
    --disable-save-password-bubble \
    --disable-web-security \
    --disable-features=TranslateUI \
    --disable-extensions \
    --disable-plugins \
    --disable-default-apps \
    --disable-popup-blocking \
    --disable-prompt-on-repost \
    --no-first-run \
    --fast \
    --fast-start \
    --disable-default-apps \
    --no-default-browser-check \
    --autoplay-policy=user-gesture-required \
    --start-maximized \
    --kiosk \
    --app=http://localhost:5000
```

Make it executable:

```bash
chmod +x /home/pi/start_kiosk.sh
```

### 2. Configure Desktop Auto-Start

Create `/home/pi/.config/autostart/kiosk.desktop`:

```ini
[Desktop Entry]
Type=Application
Name=Kiosk Display
Exec=/home/pi/start_kiosk.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
```

### 3. Optional: Disable Screen Saver and Power Management

Edit `/home/pi/.config/lxsession/LXDE-pi/autostart`:

```bash
# Add these lines to disable screen saver and power management
@xset s off
@xset -dpms
@xset s noblank
```

## Part 4: System Configuration for Kiosk Mode

### 1. Configure Boot Options

Edit `/boot/config.txt` to optimize for kiosk display:

```bash
sudo nano /boot/config.txt
```

Add or modify these settings:

```ini
# Disable overscan (black borders)
disable_overscan=1

# Set GPU memory split for better graphics performance
gpu_mem=128

# Disable rainbow splash screen
disable_splash=1
```

### 2. Configure Auto-Login (Optional)

If you want the Pi to auto-login to the desktop:

```bash
sudo raspi-config
```

Navigate to: `System Options` → `Boot / Auto Login` → `Desktop Autologin`

### 3. Set Up Automatic Refresh (Optional)

To make the kiosk refresh periodically, create a cron job:

```bash
crontab -e
```

Add this line to refresh every 30 minutes:

```bash
*/30 * * * * DISPLAY=:0 xdotool key F5
```

## Part 5: Testing and Monitoring

### 1. Test the Complete Setup

Reboot your Raspberry Pi and verify:

```bash
sudo reboot
```

After reboot, you should see:
1. The Pi boots to desktop
2. Flask service starts automatically
3. Chromium launches in fullscreen with your kiosk display

### 2. Monitor Service Status

Check if your service is running:

```bash
# Check service status
sudo systemctl status kiosk-display.service

# View service logs
sudo journalctl -u kiosk-display.service -f
```

### 3. Debugging Common Issues

**Flask service not starting:**
```bash
# Check service logs
sudo journalctl -u kiosk-display.service

# Test manually
cd /opt/kiosk-display
source .venv/bin/activate
python app.py
```

**Chromium not launching:**
```bash
# Check if script is executable
ls -la /home/pi/start_kiosk.sh

# Test script manually
/home/pi/start_kiosk.sh
```

## Part 6: HDMI Display Configuration

### Force HDMI Output

If your display doesn't show anything or you're having HDMI detection issues, add this line to `/boot/config.txt`:

```bash
sudo nano /boot/config.txt
```

Add:
```ini
# Force HDMI output even when no display is detected
hdmi_force_hotplug=1
```

This is especially useful for:
- Displays that don't properly identify themselves to the Pi
- KVM switches or HDMI splitters
- Some older monitors
- Situations where the Pi boots without a display connected

After adding this setting, reboot the Pi:
```bash
sudo reboot
```

## Part 7: Maintenance and Updates

### 1. Updating Your Application

To update your kiosk display:

```bash
cd /opt/kiosk-display
sudo systemctl stop kiosk-display.service

# Update your application files
# Update CSV data files

sudo systemctl start kiosk-display.service
```

### 2. Remote Management

For easier management, consider setting up SSH:

```bash
sudo systemctl enable ssh
sudo systemctl start ssh
```

### 3. Backup Configuration

Create a backup of your configuration:

```bash
# Create backup directory
mkdir -p /home/pi/kiosk-backup

# Backup important files
cp /etc/systemd/system/kiosk-display.service /home/pi/kiosk-backup/
cp /home/pi/start_kiosk.sh /home/pi/kiosk-backup/
cp /home/pi/.config/autostart/kiosk.desktop /home/pi/kiosk-backup/
```

## Troubleshooting

**Problem: Service fails to start**
- Check file permissions on your project directory
- Verify virtual environment is properly set up
- Check CSV files are present in the data directory

**Problem: Chromium doesn't launch in fullscreen**
- Ensure the start_kiosk.sh script is executable
- Check that the Flask service is responding before Chromium starts
- Verify autostart configuration is correct

**Problem: Display shows error messages**
- Check Flask application logs: `sudo journalctl -u kiosk-display.service`
- Verify CSV file formats match expected structure
- Test the application manually first

## Additional Features

### Auto-Update CSV Files

You could extend this setup to automatically pull updated CSV files from a network location:

```bash
# Add to crontab for automatic updates
0 6 * * * rsync -av user@server:/path/to/csv/ /opt/kiosk-display/data/
```

### Network Health Check

Add a network connectivity check to the start script:

```bash
# Add to start_kiosk.sh before launching Chromium
while ! ping -c 1 google.com &> /dev/null; do
    echo "Waiting for network connection..."
    sleep 5
done
```

This setup provides a robust, auto-starting kiosk display that will reliably restart after power outages or reboots.