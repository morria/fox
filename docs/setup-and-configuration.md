# Fox BBS Setup and Configuration

Complete guide for installing, configuring, and running Fox BBS.

## Prerequisites

- Python 3.7+
- Direwolf TNC installed
- Amateur radio license and equipment (or use `--demo` mode for testing)

## Installation

### 1. Install Fox BBS

```bash
cd fox
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Direwolf

Create `config/direwolf.conf` (if not already configured):

```conf
# Enable AGWPE protocol
AGWPORT 8000

# Your station callsign
MYCALL W2ASM-11

# Audio device (run 'arecord -l' to list devices)
ADEVICE plughw:1,0

# PTT configuration (adjust for your hardware)
PTT GPIO 17

# Modem
MODEM 1200
```

**Note:** MYCALL should be your station callsign. Fox BBS will connect as a different SSID (configured next).

### 3. Configure Fox BBS

Edit `config/fox.yaml`:

```yaml
server:
  # BBS callsign with SSID (required)
  callsign: "W2ASM-10"

  # Direwolf connection
  direwolf_host: "localhost"
  direwolf_port: 8000
  radio_port: 0

  # Message history
  max_messages: 15
  message_retention_hours: 24
```

## Configuration Reference

### Required Settings

#### `callsign`
**Type:** String
**Example:** `"W2ASM-10"`

Your BBS callsign with SSID. Must be valid amateur radio format.

- Format: `CALLSIGN-SSID` (e.g., `W1ABC-10`, `KE4XYZ-5`)
- SSID range: 0-15
- Validates on startup

#### `direwolf_host`
**Type:** String
**Default:** `"localhost"`

Where Direwolf is running.

- `"localhost"` - Same machine
- `"192.168.1.100"` - Remote machine

#### `direwolf_port`
**Type:** Integer
**Default:** `8000`
**Range:** 1-65535

AGWPE port. Must match Direwolf's `AGWPORT` setting.

#### `radio_port`
**Type:** Integer
**Default:** `0`
**Range:** 0-255

Radio port number in Direwolf.

- `0` - First radio
- `1` - Second radio (multi-port setups)

#### `max_messages`
**Type:** Integer
**Default:** `15`
**Range:** >= 0

Messages shown to connecting users.

- `0` - No history
- `15` - Last 15 messages (recommended)
- `25` - More context for busy BBSes

#### `message_retention_hours`
**Type:** Integer
**Default:** `24`
**Range:** > 0

**Note:** Kept for compatibility but not actively used. The `max_messages` setting controls how many messages are stored (using a bounded deque).

## Running Fox BBS

### Standard Mode

1. **Start Direwolf:**
```bash
direwolf -c config/direwolf.conf
```

Wait for: `Ready to accept AGW client application 0 on port 8000 ...`

2. **Start Fox BBS:**
```bash
python fox_bbs.py
```

Expected output:
```
INFO - Starting Fox BBS...
INFO - Configuration loaded: Callsign=W2ASM-10
INFO - Connecting to Direwolf at localhost:8000
INFO - Fox BBS (W2ASM-10) started and listening for connections
```

### Demo Mode

Test without hardware:

```bash
python fox_bbs.py --demo
```

### Debug Mode

Enable detailed logging:

```bash
python fox_bbs.py --debug
```

### Command Line Options

```bash
python fox_bbs.py [OPTIONS]

Options:
  --config PATH   Config file path (default: config/fox.yaml)
  --demo          Demo mode (no Direwolf required)
  --debug         Enable debug logging
  --help          Show help message
```

## Configuration Examples

### Minimal (Single Radio)

```yaml
server:
  callsign: "W1ABC-10"
  direwolf_host: "localhost"
  direwolf_port: 8000
  radio_port: 0
  max_messages: 15
  message_retention_hours: 24
```

### Remote Direwolf

```yaml
server:
  callsign: "W2XYZ-5"
  direwolf_host: "192.168.1.50"  # Remote Direwolf
  direwolf_port: 8000
  radio_port: 0
  max_messages: 20
  message_retention_hours: 48
```

### High-Traffic BBS

```yaml
server:
  callsign: "W3NET-10"
  direwolf_host: "localhost"
  direwolf_port: 8000
  radio_port: 0
  max_messages: 25              # More history
  message_retention_hours: 12   # (not actively used)
```

## Troubleshooting

### Cannot Connect to Direwolf

**Error:** `Connection refused`

**Solutions:**
1. Verify Direwolf is running
2. Check `AGWPORT 8000` is in direwolf.conf
3. Test port: `telnet localhost 8000`
4. Check firewall settings

### Invalid Callsign Error

**Error:** `Invalid callsign format`

**Solutions:**
1. Ensure format is `CALLSIGN-SSID` (e.g., `W1ABC-10`)
2. SSID must be 0-15
3. Callsign must be valid amateur radio format

### No Incoming Connections

**Solutions:**
1. Verify Direwolf is receiving packets
2. Check radio audio levels
3. Confirm callsign in direwolf.conf
4. Test with demo mode: `python fox_bbs.py --demo`

## Best Practices

### Callsign Selection
- Use different SSID than your main station
- Common BBS SSIDs: -10, -11, -15

### Message Settings
- `max_messages: 15` works well for most use cases
- Increase for high-traffic areas
- Decrease for low-memory systems

### Testing
1. Always test in demo mode first
2. Verify Direwolf connectivity before going live
3. Check logs with `--debug` flag

## Security Notes

**Amateur Radio Context:**
- All transmissions are PUBLIC (FCC regulations)
- No encryption needed or allowed
- Callsigns are public identifiers
- No authentication required

**Network:**
- Keep Direwolf on localhost unless needed
- Use firewall rules for remote access

## Next Steps

- See [Troubleshooting Guide](troubleshooting.md) for common issues
- See [Architecture Documentation](architecture.md) for system design
- See [Development Guide](development.md) for contributing
