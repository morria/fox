# Troubleshooting Guide

This guide covers common issues and their solutions when running Fox BBS.

## Table of Contents

- [Startup Issues](#startup-issues)
- [Connection Issues](#connection-issues)
- [Message Issues](#message-issues)
- [Configuration Issues](#configuration-issues)
- [Performance Issues](#performance-issues)
- [Debug Mode](#debug-mode)

## Startup Issues

### BBS Won't Start

#### Error: "Connection refused" or "Cannot connect to Direwolf"

**Symptoms:**
```
ERROR - Failed to connect to Direwolf at localhost:8000
ConnectionError: [Errno 111] Connection refused
```

**Causes:**
- Direwolf is not running
- Direwolf AGWPE is not enabled
- Wrong port number in configuration
- Firewall blocking the connection

**Solutions:**

1. **Check if Direwolf is running:**
```bash
ps aux | grep direwolf
```

If not running, start Direwolf:
```bash
direwolf -c ~/direwolf.conf
```

2. **Verify AGWPE is enabled in Direwolf config:**
```bash
grep AGWPORT ~/direwolf.conf
```

Should show:
```
AGWPORT 8000
```

If missing, add it to `direwolf.conf` and restart Direwolf.

3. **Verify port number:**
Check that `direwolf_port` in `config/fox.yaml` matches the `AGWPORT` in Direwolf.

4. **Test port connectivity:**
```bash
telnet localhost 8000
```

If connection refused, Direwolf is not listening on that port.

5. **Check firewall:**
```bash
# Linux
sudo iptables -L | grep 8000

# macOS
sudo pfctl -s rules | grep 8000
```

#### Error: "Invalid configuration"

**Symptoms:**
```
ConfigurationError: Invalid SSID format: 'INVALID'
```

**Solution:**
Fix the configuration in `config/fox.yaml`. See [Configuration Issues](#configuration-issues) section.

### BBS Starts But No Output

**Symptoms:**
- BBS appears to start
- No error messages
- No "BBS started and listening" message

**Solutions:**

1. **Run with debug logging:**
```bash
python fox_bbs.py --debug
```

2. **Check log output** for any warnings or errors

3. **Verify configuration is loaded:**
Look for "Configuration loaded" message

## Connection Issues

### No Incoming Connections

**Symptoms:**
- BBS is running
- No stations can connect
- No connection attempts logged

**Causes:**
- SSID mismatch between Direwolf and Fox BBS
- Radio not properly configured
- Direwolf not receiving packets
- Wrong radio port

**Solutions:**

1. **Verify SSID configuration:**

In `config/fox.yaml`:
```yaml
server:
  ssid: "W2ASM-10"
```

In Direwolf config, ensure MYCALL is compatible:
```
MYCALL W2ASM-11  # Different SSID is okay
```

2. **Check Direwolf is receiving packets:**
Watch Direwolf output for incoming packets. If no packets appear, check:
- Radio audio levels
- PTT configuration
- Antenna connection
- Radio frequency

3. **Verify radio port:**
Ensure `radio_port` in `config/fox.yaml` matches your Direwolf setup (usually 0).

4. **Test with demo mode:**
```bash
python fox_bbs.py --demo
```

If demo mode works, the issue is with Direwolf/radio configuration.

### Connections Drop Immediately

**Symptoms:**
- Stations connect
- Connection drops immediately
- No welcome banner received

**Causes:**
- Client not compatible with AGWPE protocol
- Network issues between Direwolf and Fox BBS
- Errors in message sending

**Solutions:**

1. **Run with debug mode:**
```bash
python fox_bbs.py --debug
```

2. **Check logs** for errors during client connection

3. **Verify Direwolf logs** for connection establishment

4. **Test message sending:**
Check that welcome banner is sent successfully

### Connection Errors in Logs

**Symptoms:**
```
ERROR - Error handling client: [Error details]
```

**Solution:**
Run with `--debug` flag and check the full error traceback. Common issues:
- Protocol errors (check AGWPE compatibility)
- Network timeouts (check network stability)
- Resource exhaustion (check system resources)

## Message Issues

### Messages Not Saved

**Symptoms:**
- Messages sent by users
- New connections don't see message history
- No messages in history

**Causes:**
- Message retention period too short
- Timestamp issues
- MessageStore errors

**Solutions:**

1. **Check retention period:**
In `config/fox.yaml`:
```yaml
server:
  message_retention_hours: 24  # Increase if needed
```

2. **Check system time:**
```bash
date
```

Ensure system time is correct.

3. **Run with debug mode** and check for MessageStore errors

4. **Verify max_messages setting:**
```yaml
server:
  max_messages: 15  # Must be > 0 to show history
```

### Messages Not Broadcasting

**Symptoms:**
- User sends message
- Other connected users don't receive it
- No errors logged

**Causes:**
- Client disconnected
- Message broadcast error
- Network issues

**Solutions:**

1. **Run with debug mode** to see broadcast attempts

2. **Check connected clients count** in logs

3. **Verify clients are actually connected:**
Debug logs should show "New client connected"

4. **Test with multiple demo mode clients** to isolate the issue

## Configuration Issues

### Invalid SSID Format

**Error:**
```
ConfigurationError: Invalid SSID format: 'CALLSIGN'
```

**Solution:**
SSID must include a dash and number (0-15):
```yaml
server:
  ssid: "W2ASM-10"  # Correct
  # ssid: "W2ASM"   # Wrong - missing SSID
  # ssid: "INVALID" # Wrong - not callsign format
```

### Invalid Port Numbers

**Error:**
```
ConfigurationError: Invalid port number: 99999
```

**Solution:**
Ensure ports are in valid ranges:
```yaml
server:
  direwolf_port: 8000  # Must be 1-65535
  radio_port: 0        # Must be 0-255
```

### YAML Syntax Errors

**Error:**
```
yaml.scanner.ScannerError: mapping values are not allowed here
```

**Causes:**
- Incorrect indentation
- Missing quotes
- Tabs instead of spaces

**Solution:**
Fix YAML syntax:
```yaml
# Correct:
server:
  ssid: "W2ASM-10"
  direwolf_host: "localhost"

# Wrong (indentation):
server:
ssid: "W2ASM-10"

# Wrong (missing quotes):
server:
  ssid: W2ASM-10  # Should be quoted
```

### Configuration File Not Found

**Error:**
```
FileNotFoundError: config/fox.yaml not found
```

**Solutions:**

1. **Check working directory:**
```bash
pwd  # Should be in fox/ directory
```

2. **Specify config path:**
```bash
python fox_bbs.py --config /full/path/to/fox.yaml
```

3. **Create default config:**
Ensure `config/fox.yaml` exists with valid content

## Performance Issues

### High CPU Usage

**Symptoms:**
- Fox BBS using excessive CPU
- System becomes slow

**Causes:**
- Busy loop in message handling
- Too many clients
- Message flooding

**Solutions:**

1. **Check number of connected clients** in logs

2. **Monitor message rate** - look for flooding

3. **Check for infinite loops** in error handling

4. **Restart BBS** to clear transient issues

### High Memory Usage

**Symptoms:**
- Memory usage grows over time
- System runs out of memory

**Causes:**
- Message history not cleaned up
- Client objects not released
- Memory leak

**Solutions:**

1. **Reduce message retention:**
```yaml
server:
  message_retention_hours: 12  # Reduce from 24
  max_messages: 10            # Reduce from 15
```

2. **Restart BBS periodically** if issue persists

3. **Check for disconnected clients** still in memory

## Debug Mode

### Enabling Debug Mode

Run Fox BBS with detailed logging:

```bash
python fox_bbs.py --debug
```

### What Debug Mode Shows

Debug mode provides detailed information about:

- **Configuration loading:**
```
DEBUG - Loading configuration from config/fox.yaml
DEBUG - Configuration validated successfully
```

- **Direwolf connection:**
```
DEBUG - Connecting to Direwolf at localhost:8000
DEBUG - AGWPE registration frame sent
DEBUG - AGWPE handler started successfully
```

- **Client connections:**
```
DEBUG - Incoming connection from W1ABC-5
DEBUG - Created new AX25Client for W1ABC-5
DEBUG - Sending welcome banner to W1ABC-5
DEBUG - Sending 5 message(s) to W1ABC-5
```

- **Message handling:**
```
DEBUG - Received message from W1ABC-5: "Hello everyone"
DEBUG - Added message to store: W1ABC-5: Hello everyone
DEBUG - Broadcasting to 3 connected client(s)
DEBUG - Message sent to W2XYZ-10
```

- **Disconnections:**
```
DEBUG - Client W1ABC-5 disconnected
DEBUG - Removed client W1ABC-5 from active clients
```

### Interpreting Debug Output

**Normal operation shows:**
- Regular heartbeat/keepalive messages
- Client connections and disconnections
- Message broadcasts

**Problems indicated by:**
- Repeated connection attempts
- Error tracebacks
- Missing expected messages
- Timeouts

## Common Error Messages

### "AGWPE protocol error"

**Meaning:** Communication error with Direwolf

**Solutions:**
- Check Direwolf is running
- Verify AGWPE port is correct
- Restart Direwolf
- Check for Direwolf updates

### "Client disconnected unexpectedly"

**Meaning:** Client connection lost without clean disconnect

**Solutions:**
- Normal for radio connections (signal loss)
- Check for network instability
- Verify radio configuration
- Check Direwolf logs

### "Message broadcast failed"

**Meaning:** Could not send message to one or more clients

**Solutions:**
- Client may have disconnected
- Check client connection state
- Verify network connectivity
- Review debug logs for specifics

## Getting Help

If issues persist after trying these solutions:

1. **Enable debug mode** and capture full output:
```bash
python fox_bbs.py --debug 2>&1 | tee fox_bbs_debug.log
```

2. **Check Direwolf logs** for related errors

3. **Review configuration** against examples in [Configuration Guide](configuration.md)

4. **Verify setup** against [Setup Guide](setup.md)

5. **Check system resources:**
```bash
# CPU and memory
top

# Disk space
df -h

# Network connections
netstat -an | grep 8000
```

6. **Test in demo mode** to isolate radio/Direwolf issues:
```bash
python fox_bbs.py --demo
```

## Quick Reference

### Diagnostic Commands

```bash
# Check if Direwolf is running
ps aux | grep direwolf

# Test AGWPE port
telnet localhost 8000

# Check port in use
netstat -an | grep 8000
lsof -i :8000

# View recent logs
tail -f /var/log/direwolf.log

# Test configuration
python fox_bbs.py --demo --debug
```

### Log Locations

- **Fox BBS:** stdout/stderr (redirect to file if needed)
- **Direwolf:** Usually `/var/log/direwolf.log` or stdout

### Configuration Validation

```bash
# Test YAML syntax
python -c "import yaml; yaml.safe_load(open('config/fox.yaml'))"

# Validate config without running
python -c "from src.config import load_config; load_config('config/fox.yaml')"
```

## Related Documentation

- [Setup Guide](setup.md) - Initial setup instructions
- [Configuration Guide](configuration.md) - Configuration options
- [Architecture Guide](architecture.md) - How Fox BBS works
- [Development Guide](development.md) - Development and testing
