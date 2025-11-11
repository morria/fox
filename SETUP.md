# Fox BBS Setup Guide

## Prerequisites

1. **Python 3.7+** installed
2. **Direwolf TNC** installed and configured

## Installation

### 1. Set up the Python environment

```bash
cd /Users/asm/Documents/Sandbox/2025/November/fox
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Direwolf

Edit your Direwolf configuration file (usually `/etc/direwolf.conf` or `~/direwolf.conf`) and ensure AGWPE is enabled:

```conf
# Enable AGWPE protocol on port 8000
AGWPORT 8000

# Your station callsign
MYCALL W2ASM-11

# Audio device configuration
ADEVICE plughw:1,0

# PTT configuration (adjust for your hardware)
PTT GPIO 17

# Modem configuration
MODEM 1200
```

### 3. Configure Fox BBS

Edit `config/fox.yaml`:

```yaml
server:
  ssid: "W2ASM-11"              # Must match Direwolf's MYCALL
  direwolf_host: "localhost"    # Direwolf host
  direwolf_port: 8000           # AGWPE port
  radio_port: 0                 # Radio port (0 for first radio)
  max_messages: 15              # Messages shown on connect
  message_retention_hours: 24   # How long to keep messages
```

## Running

### 1. Start Direwolf

```bash
direwolf -c ~/direwolf.conf
```

You should see output indicating that AGWPE is listening on port 8000:
```
Ready to accept AGW client application 0 on port 8000 ...
```

### 2. Start Fox BBS

In a separate terminal:

```bash
cd /Users/asm/Documents/Sandbox/2025/November/fox
source .venv/bin/activate
python fox_bbs.py
```

You should see:
```
INFO - Starting Fox BBS...
INFO - Configuration loaded: SSID=W2ASM-11
INFO - Connecting to Direwolf at localhost:8000
INFO - AGWPE handler started, listening as W2ASM-11
INFO - Fox BBS (W2ASM-11) started and listening for connections
```

## Testing

### Using a Terminal Program

You can test the BBS by connecting to it from another amateur radio station using any packet radio terminal program.

### Using Direwolf's Test Mode

If you don't have a radio, you can test using Direwolf's built-in test capabilities or by running another Direwolf instance in loopback mode.

## Troubleshooting

### "Connection refused" error

- Make sure Direwolf is running
- Verify AGWPE is enabled in Direwolf config
- Check that port 8000 is not in use by another application

### No incoming connections

- Verify your callsign in both Direwolf and Fox BBS configs match
- Check Direwolf's log for incoming connection attempts
- Ensure your radio is properly configured (PTT, audio levels)

### Messages not being saved

- Check the log output for errors
- Verify file permissions in the Fox BBS directory

## Usage

When a station connects to W2ASM-11:

1. They receive a welcome banner: `Welcome to W2ASM-11 Fox BBS`
2. They see recent message history (last 15 messages from 24 hours)
3. They get a prompt: `W2ASM-11> `
4. They can type messages which are broadcast to all connected users
5. All messages are timestamped and stored

## Stopping the BBS

Press `Ctrl+C` in the terminal running Fox BBS. It will gracefully disconnect all clients and shut down.
