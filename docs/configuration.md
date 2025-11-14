# Configuration Guide

Fox BBS uses a YAML configuration file located at `config/fox.yaml`. This guide explains all available configuration options.

## Configuration File Format

The configuration file uses YAML syntax with a simple structure:

```yaml
server:
  ssid: "W2ASM-10"
  direwolf_host: "localhost"
  direwolf_port: 8000
  radio_port: 0
  max_messages: 15
  message_retention_hours: 24
```

## Configuration Options

### Server Settings

#### `ssid` (Required)

**Type:** String
**Example:** `"W2ASM-10"`

Your BBS callsign with SSID in amateur radio format. This is the identifier that stations will connect to.

**Requirements:**
- Must be a valid amateur radio callsign format
- Must include an SSID (dash followed by number 0-15)
- Examples: `W1ABC-10`, `KE4XYZ-5`, `N2QZX-1`

**Validation:**
- Callsign pattern is validated on startup
- Invalid format will raise a `ConfigurationError`

#### `direwolf_host` (Required)

**Type:** String
**Default:** `"localhost"`
**Example:** `"192.168.1.100"`

The hostname or IP address where Direwolf TNC is running.

**Common Values:**
- `"localhost"` - Direwolf running on same machine
- `"127.0.0.1"` - Same as localhost (IPv4)
- `"192.168.1.100"` - Direwolf on network machine

#### `direwolf_port` (Required)

**Type:** Integer
**Default:** `8000`
**Range:** 1-65535

The TCP port where Direwolf's AGWPE protocol is listening.

**Notes:**
- Must match the `AGWPORT` setting in your Direwolf configuration
- Standard AGWPE port is 8000
- Port must not be in use by another application

#### `radio_port` (Required)

**Type:** Integer
**Default:** `0`
**Range:** 0-255

The radio port number in Direwolf to use for AX.25 connections.

**Common Values:**
- `0` - First radio/modem
- `1` - Second radio/modem (if configured in Direwolf)

**Notes:**
- Must correspond to a configured radio port in Direwolf
- Most installations use port 0 for a single radio

#### `max_messages` (Required)

**Type:** Integer
**Default:** `15`
**Range:** 0 or positive

Maximum number of recent messages shown to users when they connect.

**Behavior:**
- `0` - No message history shown
- Positive number - Shows that many recent messages (if available)
- Messages must be within the retention period

**Recommendations:**
- 10-20 messages provides good context without overwhelming users
- Adjust based on typical message volume

#### `message_retention_hours` (Required)

**Type:** Integer
**Default:** `24`
**Range:** Positive numbers

How long to keep messages in history (in hours).

**Behavior:**
- Messages older than this are not shown to new connections
- Messages are filtered by age when users connect
- Does not automatically delete messages from memory

**Recommendations:**
- 24 hours (1 day) - Good for active BBSes
- 168 hours (1 week) - For slower-traffic BBSes
- Consider your disk space and typical activity level

## Configuration Validation

Fox BBS validates all configuration settings on startup. Invalid configuration will prevent the server from starting and display a descriptive error message.

### Validation Rules

1. **SSID Format:**
   - Must match amateur radio callsign pattern
   - Must include SSID (e.g., `-10`)

2. **Port Numbers:**
   - `direwolf_port` must be 1-65535
   - `radio_port` must be 0-255

3. **Message Settings:**
   - `max_messages` must be 0 or positive
   - `message_retention_hours` must be positive

### Error Examples

Invalid SSID:
```
ConfigurationError: Invalid SSID format: 'INVALID'. Must be amateur radio callsign with SSID (e.g., W1ABC-10)
```

Invalid port:
```
ConfigurationError: Invalid port number: 99999. Must be 1-65535
```

## Command Line Overrides

Some configuration can be overridden via command line:

```bash
# Use custom configuration file
python fox_bbs.py --config /path/to/custom.yaml

# Enable debug logging (overrides log level)
python fox_bbs.py --debug

# Run in demo mode (ignores Direwolf settings)
python fox_bbs.py --demo
```

## Example Configurations

### Minimal Configuration

```yaml
server:
  ssid: "W1ABC-10"
  direwolf_host: "localhost"
  direwolf_port: 8000
  radio_port: 0
  max_messages: 15
  message_retention_hours: 24
```

### Remote Direwolf

```yaml
server:
  ssid: "W2XYZ-5"
  direwolf_host: "192.168.1.50"  # Remote Direwolf instance
  direwolf_port: 8000
  radio_port: 0
  max_messages: 20
  message_retention_hours: 48
```

### High-Traffic BBS

```yaml
server:
  ssid: "W3NET-10"
  direwolf_host: "localhost"
  direwolf_port: 8000
  radio_port: 0
  max_messages: 25               # Show more history
  message_retention_hours: 12    # Shorter retention for active BBS
```

### Low-Traffic BBS

```yaml
server:
  ssid: "W4FH-10"
  direwolf_host: "localhost"
  direwolf_port: 8000
  radio_port: 0
  max_messages: 10
  message_retention_hours: 168   # Keep 1 week of messages
```

## Configuration Best Practices

1. **Callsign Selection:**
   - Use a different SSID than your main station
   - Common BBS SSIDs: -10, -11, -15
   - Make it memorable for users

2. **Message Retention:**
   - Balance history with resource usage
   - Consider your typical message volume
   - Longer retention for low-traffic areas

3. **Testing Configuration:**
   - Always test changes in demo mode first
   - Verify Direwolf connectivity before going live
   - Check logs for validation errors

4. **Security:**
   - Keep Direwolf on localhost unless needed
   - Use firewall rules for remote access
   - Ensure proper amateur radio licensing

## Troubleshooting Configuration

If Fox BBS won't start:

1. **Check YAML syntax:**
   - Proper indentation (2 spaces)
   - Quotes around string values
   - No tabs (use spaces)

2. **Validate values:**
   - Run with `--debug` flag to see validation errors
   - Check error messages for specific issues

3. **Test connectivity:**
   - Verify Direwolf is running
   - Test port with `telnet localhost 8000`
   - Check firewall settings

See [Troubleshooting Guide](troubleshooting.md) for more help.
