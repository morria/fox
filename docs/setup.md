# Fox BBS Setup Guide

This guide provides step-by-step instructions for setting up Fox BBS with Direwolf TNC.

## Prerequisites

- **Python 3.7+** installed on your system
- **Direwolf TNC** installed and configured
- **Amateur radio license** and equipment (or use demo mode for testing)

## Installation Steps

### 1. Set up Python Environment

Create and activate a virtual environment:

```bash
cd fox
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configure Direwolf

Direwolf must be configured to enable the AGWPE protocol. Edit your Direwolf configuration file (usually `/etc/direwolf.conf` or `~/direwolf.conf`):

```conf
# Enable AGWPE protocol on port 8000
AGWPORT 8000

# Your station callsign
MYCALL W2ASM-11

# Audio device configuration (adjust for your hardware)
ADEVICE plughw:1,0

# PTT configuration (adjust for your hardware)
PTT GPIO 17

# Modem configuration
MODEM 1200
```

**Important:** The MYCALL in Direwolf should match the SSID you configure for Fox BBS.

### 3. Configure Fox BBS

Edit the configuration file at `config/fox.yaml`:

```yaml
server:
  # Must match or be related to Direwolf's MYCALL
  ssid: "W2ASM-10"

  # Direwolf connection settings
  direwolf_host: "localhost"
  direwolf_port: 8000

  # Radio port (0 for first radio, 1 for second, etc.)
  radio_port: 0

  # Message history settings
  max_messages: 15              # Messages shown to new connections
  message_retention_hours: 24   # How long to keep messages
```

See [Configuration Guide](configuration.md) for detailed configuration options.

## Running Fox BBS

### Starting Direwolf

First, start Direwolf in one terminal:

```bash
direwolf -c ~/direwolf.conf
```

You should see output indicating AGWPE is ready:
```
Ready to accept AGW client application 0 on port 8000 ...
```

### Starting Fox BBS

In a separate terminal, activate your virtual environment and start Fox BBS:

```bash
cd fox
source venv/bin/activate
python fox_bbs.py
```

Expected output:
```
INFO - Starting Fox BBS...
INFO - Configuration loaded: SSID=W2ASM-10
INFO - Connecting to Direwolf at localhost:8000
INFO - AGWPE handler started, listening as W2ASM-10
INFO - Fox BBS (W2ASM-10) started and listening for connections
```

### Demo Mode (Testing Without Radio)

For testing without radio hardware:

```bash
python fox_bbs.py --demo
```

This allows you to test the BBS functionality without requiring Direwolf or radio equipment.

## Testing Your Setup

### Using Amateur Radio Equipment

Connect to the BBS from another amateur radio station using any packet radio terminal program. The station should:

1. Connect to your BBS callsign (e.g., `C W2ASM-10`)
2. Receive the welcome banner
3. See recent message history
4. Be able to send and receive messages

### Using Direwolf Test Mode

If you don't have access to multiple radios, you can test using:

- Direwolf's built-in test capabilities
- A second Direwolf instance in loopback mode
- Audio loopback between two Direwolf instances

## Stopping Fox BBS

To gracefully shut down the BBS:

1. Press `Ctrl+C` in the terminal running Fox BBS
2. The server will disconnect all clients
3. All message history will be preserved

## Next Steps

- Review [Configuration Options](configuration.md) to customize your BBS
- Check [Troubleshooting Guide](troubleshooting.md) if you encounter issues
- See [Architecture Documentation](architecture.md) to understand how Fox BBS works

## Common Setup Issues

See the [Troubleshooting Guide](troubleshooting.md) for solutions to common problems:

- Connection refused errors
- No incoming connections
- Message history not working
- AGWPE protocol issues
