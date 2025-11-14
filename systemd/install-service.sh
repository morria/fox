#!/bin/bash
# Fox BBS systemd service installation script
# Works on Debian Trixie and Raspbian OS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print colored messages
print_error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
}

print_success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

print_info() {
    echo -e "$1"
}

# Check if running with appropriate privileges
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run with sudo or as root"
    echo "Usage: sudo ./install-service.sh"
    exit 1
fi

# Get the actual user who invoked sudo (not root)
if [ -n "$SUDO_USER" ]; then
    INSTALL_USER="$SUDO_USER"
else
    INSTALL_USER="root"
fi

# Detect installation directory (parent of this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
DEFAULT_USER="$INSTALL_USER"
DEFAULT_GROUP="$(id -gn "$INSTALL_USER")"
DEFAULT_VENV_PATH="$INSTALL_DIR/venv"
DEFAULT_CONFIG_PATH="$INSTALL_DIR/config/fox.yaml"

print_info "================================================================"
print_info "Fox BBS systemd Service Installation"
print_info "================================================================"
print_info ""
print_info "Detected settings:"
print_info "  Installation directory: $INSTALL_DIR"
print_info "  Default user:          $DEFAULT_USER"
print_info "  Default group:         $DEFAULT_GROUP"
print_info "  Virtual environment:   $DEFAULT_VENV_PATH"
print_info "  Configuration file:    $DEFAULT_CONFIG_PATH"
print_info ""

# Validate installation directory
if [ ! -f "$INSTALL_DIR/fox_bbs.py" ]; then
    print_error "fox_bbs.py not found in $INSTALL_DIR"
    print_error "Please run this script from the systemd/ directory of the Fox BBS installation"
    exit 1
fi

# Check for virtual environment
if [ ! -d "$DEFAULT_VENV_PATH" ]; then
    print_warning "Virtual environment not found at $DEFAULT_VENV_PATH"
    print_info "Creating virtual environment..."

    # Create venv as the installation user, not root
    sudo -u "$INSTALL_USER" python3 -m venv "$DEFAULT_VENV_PATH"

    print_info "Installing Python dependencies..."
    sudo -u "$INSTALL_USER" "$DEFAULT_VENV_PATH/bin/pip" install --upgrade pip
    sudo -u "$INSTALL_USER" "$DEFAULT_VENV_PATH/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

    print_success "Virtual environment created"
fi

# Check if Python executable exists in venv
if [ ! -f "$DEFAULT_VENV_PATH/bin/python3" ]; then
    print_error "Python executable not found in virtual environment"
    print_error "Expected: $DEFAULT_VENV_PATH/bin/python3"
    exit 1
fi

# Check if configuration file exists
if [ ! -f "$DEFAULT_CONFIG_PATH" ]; then
    print_warning "Configuration file not found at $DEFAULT_CONFIG_PATH"
    print_info "You'll need to create it before starting the service"
fi

# Allow customization
print_info ""
print_info "Press Enter to use default values, or type custom values:"
print_info ""

read -p "User to run service as [$DEFAULT_USER]: " CUSTOM_USER
SERVICE_USER="${CUSTOM_USER:-$DEFAULT_USER}"

read -p "Group to run service as [$DEFAULT_GROUP]: " CUSTOM_GROUP
SERVICE_GROUP="${CUSTOM_GROUP:-$DEFAULT_GROUP}"

read -p "Virtual environment path [$DEFAULT_VENV_PATH]: " CUSTOM_VENV
VENV_PATH="${CUSTOM_VENV:-$DEFAULT_VENV_PATH}"

read -p "Configuration file path [$DEFAULT_CONFIG_PATH]: " CUSTOM_CONFIG
CONFIG_PATH="${CUSTOM_CONFIG:-$DEFAULT_CONFIG_PATH}"

# Validate user and group
if ! id "$SERVICE_USER" >/dev/null 2>&1; then
    print_error "User '$SERVICE_USER' does not exist"
    exit 1
fi

if ! getent group "$SERVICE_GROUP" >/dev/null 2>&1; then
    print_error "Group '$SERVICE_GROUP' does not exist"
    exit 1
fi

# Confirm installation
print_info ""
print_info "================================================================"
print_info "Service will be installed with the following settings:"
print_info "================================================================"
print_info "  User:              $SERVICE_USER"
print_info "  Group:             $SERVICE_GROUP"
print_info "  Install directory: $INSTALL_DIR"
print_info "  Virtual env:       $VENV_PATH"
print_info "  Config file:       $CONFIG_PATH"
print_info ""

read -p "Continue with installation? (y/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    print_info "Installation cancelled"
    exit 0
fi

# Create service file from template
print_info ""
print_info "Installing systemd service..."

SERVICE_FILE="/etc/systemd/system/fox-bbs.service"

# Read template and replace placeholders
sed -e "s|USER_PLACEHOLDER|$SERVICE_USER|g" \
    -e "s|GROUP_PLACEHOLDER|$SERVICE_GROUP|g" \
    -e "s|INSTALL_DIR_PLACEHOLDER|$INSTALL_DIR|g" \
    -e "s|VENV_PATH_PLACEHOLDER|$VENV_PATH|g" \
    -e "s|CONFIG_PATH_PLACEHOLDER|$CONFIG_PATH|g" \
    "$SCRIPT_DIR/fox-bbs.service" > "$SERVICE_FILE"

# Set proper permissions
chmod 644 "$SERVICE_FILE"

print_success "Service file created at $SERVICE_FILE"

# Reload systemd
print_info "Reloading systemd daemon..."
systemctl daemon-reload

print_success "Systemd daemon reloaded"

# Ask if user wants to enable and start the service
print_info ""
read -p "Enable service to start at boot? (y/N): " ENABLE_SERVICE
if [[ "$ENABLE_SERVICE" =~ ^[Yy]$ ]]; then
    systemctl enable fox-bbs.service
    print_success "Service enabled for automatic startup"
fi

print_info ""
read -p "Start service now? (y/N): " START_SERVICE
if [[ "$START_SERVICE" =~ ^[Yy]$ ]]; then
    print_info "Starting Fox BBS service..."

    if systemctl start fox-bbs.service; then
        print_success "Service started successfully"
        print_info ""
        print_info "Service status:"
        systemctl status fox-bbs.service --no-pager || true
    else
        print_error "Failed to start service"
        print_info "Check logs with: journalctl -u fox-bbs.service -n 50"
        exit 1
    fi
fi

# Print usage information
print_info ""
print_info "================================================================"
print_info "Installation Complete!"
print_info "================================================================"
print_info ""
print_info "Useful commands:"
print_info "  Start service:     sudo systemctl start fox-bbs"
print_info "  Stop service:      sudo systemctl stop fox-bbs"
print_info "  Restart service:   sudo systemctl restart fox-bbs"
print_info "  Service status:    sudo systemctl status fox-bbs"
print_info "  Enable at boot:    sudo systemctl enable fox-bbs"
print_info "  Disable at boot:   sudo systemctl disable fox-bbs"
print_info ""
print_info "View logs:"
print_info "  Recent logs:       sudo journalctl -u fox-bbs -n 50"
print_info "  Follow logs:       sudo journalctl -u fox-bbs -f"
print_info "  Today's logs:      sudo journalctl -u fox-bbs --since today"
print_info ""
print_info "Configuration file: $CONFIG_PATH"
print_info ""

if [ ! -f "$CONFIG_PATH" ]; then
    print_warning "Don't forget to create your configuration file before starting the service!"
fi

print_success "Installation completed successfully!"
