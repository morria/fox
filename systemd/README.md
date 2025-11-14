# Fox BBS systemd Service

This directory contains scripts and configuration files for running Fox BBS as a Linux systemd service. This allows Fox BBS to:

- Start automatically at system boot
- Run in the background as a daemon
- Restart automatically on failures
- Integrate with system logging (journalctl)
- Be managed with standard systemd commands

## Compatibility

Tested and supported on:
- Debian Trixie (13)
- Raspbian OS (based on Debian Trixie)

Should work on any modern Linux distribution using systemd.

## Quick Start

### Installation

1. **Ensure Fox BBS is installed and configured:**
   ```bash
   # From the Fox BBS root directory
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure your BBS:**
   Edit `config/fox.yaml` with your callsign and settings.

3. **Install the systemd service:**
   ```bash
   cd systemd
   sudo ./install-service.sh
   ```

   The installation script will:
   - Auto-detect your installation directory
   - Create a virtual environment if needed
   - Allow you to customize user, group, and paths
   - Install the service file to `/etc/systemd/system/`
   - Optionally enable and start the service

### Uninstallation

To remove the systemd service (but keep Fox BBS installed):

```bash
cd systemd
sudo ./uninstall-service.sh
```

This will stop and disable the service, then remove the service file. Your Fox BBS installation and configuration will remain intact.

## Service Management

Once installed, manage Fox BBS using standard systemd commands:

### Basic Commands

```bash
# Start the service
sudo systemctl start fox-bbs

# Stop the service
sudo systemctl stop fox-bbs

# Restart the service
sudo systemctl restart fox-bbs

# Check service status
sudo systemctl status fox-bbs

# Enable automatic startup at boot
sudo systemctl enable fox-bbs

# Disable automatic startup
sudo systemctl disable fox-bbs
```

### Service Status

Check if the service is running:
```bash
sudo systemctl is-active fox-bbs
```

Check if the service is enabled:
```bash
sudo systemctl is-enabled fox-bbs
```

View detailed status information:
```bash
sudo systemctl status fox-bbs
```

Example output:
```
● fox-bbs.service - Fox BBS - Amateur Radio Bulletin Board System
     Loaded: loaded (/etc/systemd/system/fox-bbs.service; enabled; vendor preset: enabled)
     Active: active (running) since Thu 2025-11-14 12:34:56 UTC; 1h 23min ago
       Docs: https://github.com/morria/fox
   Main PID: 1234 (python3)
      Tasks: 5 (limit: 4915)
     Memory: 45.2M
        CPU: 1.234s
     CGroup: /system.slice/fox-bbs.service
             └─1234 /home/user/fox/venv/bin/python3 /home/user/fox/fox_bbs.py --config /home/user/fox/config/fox.yaml
```

## Logging

Fox BBS logs are automatically sent to the systemd journal. Use `journalctl` to view logs:

### View Recent Logs

```bash
# Last 50 lines
sudo journalctl -u fox-bbs -n 50

# Last 100 lines
sudo journalctl -u fox-bbs -n 100
```

### Follow Logs in Real-Time

```bash
sudo journalctl -u fox-bbs -f
```

Press `Ctrl+C` to stop following.

### View Logs by Time

```bash
# Today's logs
sudo journalctl -u fox-bbs --since today

# Yesterday's logs
sudo journalctl -u fox-bbs --since yesterday --until today

# Last hour
sudo journalctl -u fox-bbs --since "1 hour ago"

# Last 30 minutes
sudo journalctl -u fox-bbs --since "30 minutes ago"

# Specific time range
sudo journalctl -u fox-bbs --since "2025-11-14 12:00:00" --until "2025-11-14 13:00:00"
```

### Filter Logs by Priority

```bash
# Errors only
sudo journalctl -u fox-bbs -p err

# Warnings and above
sudo journalctl -u fox-bbs -p warning

# Info and above (default)
sudo journalctl -u fox-bbs -p info
```

### Export Logs

```bash
# Save logs to a file
sudo journalctl -u fox-bbs > fox-bbs-logs.txt

# Save logs with timestamps
sudo journalctl -u fox-bbs --since today --no-pager > fox-bbs-$(date +%Y%m%d).log
```

### Debug Mode

To enable debug logging, edit the service file:

```bash
sudo systemctl edit fox-bbs
```

Add:
```ini
[Service]
ExecStart=
ExecStart=/path/to/venv/bin/python3 /path/to/fox_bbs.py --config /path/to/config/fox.yaml --debug
```

Then reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart fox-bbs
```

## Failure Handling

The service is configured to handle failures gracefully:

### Automatic Restart

The service will automatically restart if it crashes:
- **RestartSec**: Waits 10 seconds before restarting
- **StartLimitBurst**: Allows up to 5 restart attempts
- **StartLimitInterval**: Within a 300-second (5-minute) window

If the service fails more than 5 times in 5 minutes, systemd will stop trying to restart it automatically.

### Check for Failed Service

```bash
# Check if service is in failed state
sudo systemctl is-failed fox-bbs

# View failure information
sudo systemctl status fox-bbs
```

### Reset Failed State

If the service has reached its restart limit:

```bash
# Reset the failure counter
sudo systemctl reset-failed fox-bbs

# Then try starting again
sudo systemctl start fox-bbs
```

### Monitor for Crashes

Watch for service restarts:
```bash
# View all service starts/stops
sudo journalctl -u fox-bbs | grep -E "(Starting|Started|Stopped|Failed)"
```

## Configuration Changes

After modifying `config/fox.yaml`:

```bash
# Simply restart the service
sudo systemctl restart fox-bbs

# Verify it restarted successfully
sudo systemctl status fox-bbs
```

## Updating Fox BBS

When you update the Fox BBS code:

```bash
# 1. Stop the service
sudo systemctl stop fox-bbs

# 2. Update your code (git pull, etc.)
cd /path/to/fox
git pull

# 3. Update dependencies if needed
source venv/bin/activate
pip install -r requirements.txt

# 4. Start the service
sudo systemctl start fox-bbs

# 5. Verify it's running
sudo systemctl status fox-bbs
```

## Troubleshooting

### Service Won't Start

1. **Check the service status:**
   ```bash
   sudo systemctl status fox-bbs
   ```

2. **View recent error logs:**
   ```bash
   sudo journalctl -u fox-bbs -n 50
   ```

3. **Common issues:**
   - Configuration file not found or invalid
   - Python dependencies not installed
   - Virtual environment path incorrect
   - Permission issues

### Test Configuration Manually

Try running Fox BBS manually to see detailed errors:
```bash
cd /path/to/fox
source venv/bin/activate
python3 fox_bbs.py --config config/fox.yaml --debug
```

### Permission Denied Errors

Ensure the service user has permission to:
- Read the Fox BBS directory
- Read the configuration file
- Access the virtual environment

```bash
# Check file ownership
ls -la /path/to/fox

# Fix if needed (replace 'user' with your service user)
sudo chown -R user:user /path/to/fox
```

### Service File Changes

If you modify the service file at `/etc/systemd/system/fox-bbs.service`:

```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Restart the service
sudo systemctl restart fox-bbs
```

### Network Issues

If Fox BBS can't connect to Direwolf:

1. **Ensure Direwolf is running:**
   ```bash
   ps aux | grep direwolf
   ```

2. **Check Direwolf AGWPE port:**
   ```bash
   netstat -tln | grep 8000
   ```

3. **Verify configuration:**
   ```bash
   cat config/fox.yaml | grep -A 2 direwolf
   ```

## Security Hardening

The service includes several security features:

- **NoNewPrivileges**: Prevents privilege escalation
- **PrivateTmp**: Provides private `/tmp` directory
- **ProtectSystem=strict**: Makes most of system read-only
- **ProtectHome=read-only**: Protects home directories
- **ReadWritePaths**: Only allows writes to Fox BBS directory

These settings help contain the service and limit potential security risks.

## Advanced Usage

### Running Multiple Instances

To run multiple Fox BBS instances (e.g., for different radios):

1. Create separate installation directories
2. Create separate configuration files
3. Copy the service file with different names:
   ```bash
   sudo cp /etc/systemd/system/fox-bbs.service /etc/systemd/system/fox-bbs-vhf.service
   sudo cp /etc/systemd/system/fox-bbs.service /etc/systemd/system/fox-bbs-uhf.service
   ```
4. Edit each service file to point to its own config
5. Manage them independently:
   ```bash
   sudo systemctl start fox-bbs-vhf
   sudo systemctl start fox-bbs-uhf
   ```

### Custom Service Overrides

Use systemd drop-in files for custom configurations:

```bash
sudo systemctl edit fox-bbs
```

This creates an override file at `/etc/systemd/system/fox-bbs.service.d/override.conf`

Example override to change restart behavior:
```ini
[Service]
RestartSec=5
StartLimitBurst=10
```

Save and exit, then:
```bash
sudo systemctl daemon-reload
sudo systemctl restart fox-bbs
```

## Files

- `fox-bbs.service` - systemd service file template
- `install-service.sh` - Installation script
- `uninstall-service.sh` - Uninstallation script
- `README.md` - This documentation

## Support

For issues specific to the systemd service:
1. Check the logs: `sudo journalctl -u fox-bbs -n 100`
2. Verify configuration: `sudo systemctl status fox-bbs`
3. Test manually: `python3 fox_bbs.py --debug`
4. Report issues at: https://github.com/morria/fox/issues

## References

- [systemd Service Documentation](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [journalctl Documentation](https://www.freedesktop.org/software/systemd/man/journalctl.html)
- [Fox BBS Documentation](../docs/)
