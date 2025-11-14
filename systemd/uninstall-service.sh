#!/bin/bash
# Fox BBS systemd service uninstallation script

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
    echo "Usage: sudo ./uninstall-service.sh"
    exit 1
fi

SERVICE_FILE="/etc/systemd/system/fox-bbs.service"

print_info "================================================================"
print_info "Fox BBS systemd Service Uninstallation"
print_info "================================================================"
print_info ""

# Check if service file exists
if [ ! -f "$SERVICE_FILE" ]; then
    print_warning "Service file not found at $SERVICE_FILE"
    print_info "The service may not be installed"
    exit 0
fi

# Check if service is running
if systemctl is-active --quiet fox-bbs.service; then
    SERVICE_RUNNING=true
    print_warning "Service is currently running"
else
    SERVICE_RUNNING=false
fi

# Check if service is enabled
if systemctl is-enabled --quiet fox-bbs.service 2>/dev/null; then
    SERVICE_ENABLED=true
    print_warning "Service is enabled for automatic startup"
else
    SERVICE_ENABLED=false
fi

print_info ""
print_info "This will remove the Fox BBS systemd service."
print_info "Your Fox BBS installation and configuration will not be deleted."
print_info ""

read -p "Continue with uninstallation? (y/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    print_info "Uninstallation cancelled"
    exit 0
fi

print_info ""

# Stop the service if running
if [ "$SERVICE_RUNNING" = true ]; then
    print_info "Stopping Fox BBS service..."
    if systemctl stop fox-bbs.service; then
        print_success "Service stopped"
    else
        print_error "Failed to stop service"
        print_info "You may need to stop it manually: sudo systemctl stop fox-bbs"
    fi
fi

# Disable the service if enabled
if [ "$SERVICE_ENABLED" = true ]; then
    print_info "Disabling Fox BBS service..."
    if systemctl disable fox-bbs.service; then
        print_success "Service disabled"
    else
        print_warning "Failed to disable service"
    fi
fi

# Remove service file
print_info "Removing service file..."
if rm -f "$SERVICE_FILE"; then
    print_success "Service file removed"
else
    print_error "Failed to remove service file"
    exit 1
fi

# Reload systemd daemon
print_info "Reloading systemd daemon..."
systemctl daemon-reload
print_success "Systemd daemon reloaded"

# Reset failed state if any
systemctl reset-failed fox-bbs.service 2>/dev/null || true

print_info ""
print_info "================================================================"
print_info "Uninstallation Complete!"
print_info "================================================================"
print_info ""
print_info "The Fox BBS systemd service has been removed."
print_info ""
print_info "Note: Your Fox BBS installation, configuration, and logs"
print_info "      have been preserved and can still be used."
print_info ""
print_info "To reinstall the service, run:"
print_info "  sudo ./install-service.sh"
print_info ""

print_success "Uninstallation completed successfully!"
