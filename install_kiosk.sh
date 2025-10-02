#!/bin/bash

# University Schedule Kiosk Display - Raspberry Pi Installation Script
# This script automates the complete setup of the kiosk display system

set -e  # Exit on any error

# Configuration variables
INSTALL_DIR="/opt/kiosk-display"
SERVICE_NAME="kiosk-display"
USER="pi"
GROUP="pi"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root. Please run as the pi user."
        exit 1
    fi
}

# Check if we're on Raspberry Pi
check_raspberry_pi() {
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        log_warning "This doesn't appear to be a Raspberry Pi. Continuing anyway..."
    fi
}

# Update system packages
update_system() {
    log_info "Updating system packages..."
    sudo apt update && sudo apt upgrade -y
    log_success "System packages updated"
}

# Install required packages
install_packages() {
    log_info "Installing required packages..."
    sudo apt install -y python3-pip python3-venv git chromium-browser unclutter curl xdotool fonts-noto-color-emoji
    log_success "Required packages installed"
}

# Create installation directory
create_install_dir() {
    log_info "Creating installation directory..."
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown $USER:$GROUP "$INSTALL_DIR"
    log_success "Installation directory created: $INSTALL_DIR"
}

# Setup Python environment
setup_python_env() {
    log_info "Setting up Python virtual environment..."
    cd "$INSTALL_DIR"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install flask flask-cors gunicorn
    log_success "Python environment configured"
}

# Copy project files
copy_project_files() {
    log_info "Copying project files..."
    
    # Prompt user for source directory
    echo -n "Enter the path to your kiosk display project files (or press Enter for current directory): "
    read source_dir
    
    if [ -z "$source_dir" ]; then
        source_dir="."
    fi
    
    if [ ! -f "$source_dir/app.py" ]; then
        log_error "app.py not found in $source_dir"
        exit 1
    fi
    
    # Copy files
    cp "$source_dir/app.py" "$INSTALL_DIR/"
    
    # Copy static and templates directories if they exist
    if [ -d "$source_dir/static" ]; then
        cp -r "$source_dir/static" "$INSTALL_DIR/"
    fi
    
    if [ -d "$source_dir/templates" ]; then
        cp -r "$source_dir/templates" "$INSTALL_DIR/"
    fi
    
    # Create data directory
    mkdir -p "$INSTALL_DIR/data"
    
    # Copy CSV files if they exist
    if [ -d "$source_dir/data" ]; then
        cp -r "$source_dir/data/"* "$INSTALL_DIR/data/"
    else
        log_warning "No data directory found. You'll need to manually add CSV files to $INSTALL_DIR/data/"
    fi
    
    log_success "Project files copied"
}

# Create systemd service file
create_service_file() {
    log_info "Creating systemd service file..."
    
    sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=University Schedule Kiosk Display
After=network.target

[Service]
Type=simple
User=$USER
Group=$GROUP
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/.venv/bin
ExecStart=$INSTALL_DIR/.venv/bin/gunicorn -w 2 -b 127.0.0.1:5000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    log_success "Systemd service file created"
}

# Enable and start service
enable_service() {
    log_info "Enabling and starting service..."
    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME.service
    sudo systemctl start $SERVICE_NAME.service
    
    # Wait a moment and check status
    sleep 3
    if sudo systemctl is-active --quiet $SERVICE_NAME.service; then
        log_success "Service is running successfully"
    else
        log_error "Service failed to start. Check with: sudo systemctl status $SERVICE_NAME.service"
        exit 1
    fi
}

# Create kiosk launch script
create_launch_script() {
    log_info "Creating kiosk launch script..."
    
    cat > /home/$USER/start_kiosk.sh <<'EOF'
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
EOF
    
    chmod +x /home/$USER/start_kiosk.sh
    log_success "Kiosk launch script created"
}

# Create desktop autostart entry
create_autostart() {
    log_info "Creating desktop autostart entry..."
    
    mkdir -p /home/$USER/.config/autostart
    
    cat > /home/$USER/.config/autostart/kiosk.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Kiosk Display
Exec=/home/$USER/start_kiosk.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF
    
    log_success "Desktop autostart entry created"
}

# Configure LXDE session
configure_lxde() {
    log_info "Configuring LXDE session..."
    
    mkdir -p /home/$USER/.config/lxsession/LXDE-pi
    
    # Create or append to autostart file
    cat >> /home/$USER/.config/lxsession/LXDE-pi/autostart <<EOF

# Kiosk display configuration
@xset s off
@xset -dpms
@xset s noblank
@unclutter -idle 0.5

EOF
    
    log_success "LXDE session configured"
}

# Configure boot options
configure_boot() {
    log_info "Configuring boot options..."
    
    # Backup original config
    sudo cp /boot/config.txt /boot/config.txt.backup
    
    # Add kiosk-specific settings
    sudo tee -a /boot/config.txt > /dev/null <<EOF

# Kiosk display configuration
disable_overscan=1
gpu_mem=128
disable_splash=1
EOF
    
    log_success "Boot configuration updated"
}

# Setup automatic refresh (optional)
setup_auto_refresh() {
    echo -n "Do you want to enable automatic page refresh every 30 minutes? (y/n): "
    read -r enable_refresh
    
    if [[ $enable_refresh =~ ^[Yy]$ ]]; then
        log_info "Setting up automatic refresh..."
        
        # Add cron job for page refresh
        (crontab -l 2>/dev/null; echo "*/30 * * * * DISPLAY=:0 xdotool key F5") | crontab -
        
        log_success "Automatic refresh configured"
    fi
}

# Create backup script
create_backup_script() {
    log_info "Creating backup script..."
    
    cat > /home/$USER/backup_kiosk_config.sh <<EOF
#!/bin/bash

# Backup kiosk configuration
BACKUP_DIR="/home/$USER/kiosk-backup-\$(date +%Y%m%d)"
mkdir -p "\$BACKUP_DIR"

# Backup important files
cp /etc/systemd/system/$SERVICE_NAME.service "\$BACKUP_DIR/"
cp /home/$USER/start_kiosk.sh "\$BACKUP_DIR/"
cp /home/$USER/.config/autostart/kiosk.desktop "\$BACKUP_DIR/"
cp /home/$USER/.config/lxsession/LXDE-pi/autostart "\$BACKUP_DIR/"
cp /boot/config.txt "\$BACKUP_DIR/"

# Backup project files
cp -r "$INSTALL_DIR" "\$BACKUP_DIR/kiosk-display"

echo "Backup created in: \$BACKUP_DIR"
EOF
    
    chmod +x /home/$USER/backup_kiosk_config.sh
    log_success "Backup script created at /home/$USER/backup_kiosk_config.sh"
}

# Test the installation
test_installation() {
    log_info "Testing installation..."
    
    # Test service status
    if sudo systemctl is-active --quiet $SERVICE_NAME.service; then
        log_success "Service is running"
    else
        log_error "Service is not running"
        return 1
    fi
    
    # Test web server response
    if curl -s http://localhost:5000 > /dev/null; then
        log_success "Web server is responding"
    else
        log_error "Web server is not responding"
        return 1
    fi
    
    log_success "Installation test passed"
}

# Create uninstall script
create_uninstall_script() {
    log_info "Creating uninstall script..."
    
    cat > /home/$USER/uninstall_kiosk.sh <<EOF
#!/bin/bash

# Uninstall kiosk display system
echo "Uninstalling kiosk display system..."

# Stop and disable service
sudo systemctl stop $SERVICE_NAME.service
sudo systemctl disable $SERVICE_NAME.service
sudo rm /etc/systemd/system/$SERVICE_NAME.service
sudo systemctl daemon-reload

# Remove autostart entries
rm -f /home/$USER/.config/autostart/kiosk.desktop
rm -f /home/$USER/start_kiosk.sh

# Remove cron job
crontab -l | grep -v "xdotool key F5" | crontab -

# Remove installation directory
sudo rm -rf "$INSTALL_DIR"

# Restore boot config
sudo cp /boot/config.txt.backup /boot/config.txt

echo "Kiosk display system uninstalled"
echo "Note: System packages were not removed"
EOF
    
    chmod +x /home/$USER/uninstall_kiosk.sh
    log_success "Uninstall script created at /home/$USER/uninstall_kiosk.sh"
}

# Main installation function
main() {
    echo "=========================================="
    echo "  University Schedule Kiosk Display"
    echo "  Raspberry Pi Installation Script"
    echo "=========================================="
    echo
    
    check_root
    check_raspberry_pi
    
    log_info "Starting installation..."
    
    # System setup
    update_system
    install_packages
    
    # Application setup
    create_install_dir
    setup_python_env
    copy_project_files
    
    # Service setup
    create_service_file
    enable_service
    
    # Kiosk setup
    create_launch_script
    create_autostart
    configure_lxde
    configure_boot
    setup_auto_refresh
    
    # Utility scripts
    create_backup_script
    create_uninstall_script
    
    # Final test
    test_installation
    
    echo
    log_success "Installation completed successfully!"
    echo
    echo "=========================================="
    echo "  Installation Summary"
    echo "=========================================="
    echo "Service: $SERVICE_NAME"
    echo "Install directory: $INSTALL_DIR"
    echo "Launch script: /home/$USER/start_kiosk.sh"
    echo "Backup script: /home/$USER/backup_kiosk_config.sh"
    echo "Uninstall script: /home/$USER/uninstall_kiosk.sh"
    echo
    echo "To complete the setup:"
    echo "1. Add your CSV files to $INSTALL_DIR/data/"
    echo "2. Reboot the system: sudo reboot"
    echo "3. The kiosk display should start automatically"
    echo
    echo "Useful commands:"
    echo "- Check service status: sudo systemctl status $SERVICE_NAME"
    echo "- View service logs: sudo journalctl -u $SERVICE_NAME -f"
    echo "- Test manually: $INSTALL_DIR/.venv/bin/python $INSTALL_DIR/app.py"
    echo "=========================================="
}

# Run main function
main "$@"
