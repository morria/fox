# Client Compatibility

Fox BBS is designed to work with any AX.25 client supporting connected mode.

## How Compatibility is Achieved

### 1. Flexible Line Endings

Handles all three types:
- Unix/Linux (ax25call): `\n`
- Windows (Packet Commander): `\r\n`
- Legacy Mac: `\r`

**Implementation:** `src/ax25_client.py:59-68`

### 2. Incremental Buffering

Accepts data in any chunk size:
- Character-by-character
- Small chunks (mobile apps)
- Large buffers (desktop apps)

**Implementation:** `src/ax25_client.py:40-78`

### 3. Latin-1 Encoding

Uses Latin-1 with graceful error handling:
- Supports all byte values 0x00-0xFF
- Compatible with ASCII
- Standard for packet radio

**Implementation:** `src/ax25_client.py:50`

## Tested Clients

### Verified
- **ax25call** (Linux) - ✅ Working
- **Mock clients** (Testing) - ✅ Automated suite

### Should Work (Not Yet Tested)
- Packet Commander (Windows)
- APRSdroid (Android) - if supports connected mode
- BPQ32 Terminal (Windows)
- YAAC (Cross-platform)
- Xastir (Linux)

## Testing Your Client

### Quick Test

1. **Start Fox BBS:**
```bash
python fox_bbs.py
```

2. **Connect from your client:**
```
C W2ASM-10  # Or whatever callsign you configured
```

3. **Verify you see:**
- Welcome banner
- Message history (if any)
- Your prompt

4. **Send a test message:**
```
Hello world
```

5. **Success criteria:**
- Message appears immediately
- Other connected clients receive it
- You see your prompt again

### Common Issues

**Messages appear garbled:**
- Configure client to use Latin-1 or ASCII encoding

**Messages don't appear until multiple newlines:**
- Client may not be flushing output buffer
- Check client configuration

**Connection drops immediately:**
- Verify Direwolf is running
- Check callsigns don't conflict

## Reporting Compatibility Issues

If you find a client that doesn't work:

1. Client name and version
2. Platform (OS, version)
3. Fox BBS version
4. Log output with `--debug` flag
5. Expected vs. actual behavior

Open an issue on GitHub with this information.

## Protocol Details

### Connection Sequence

1. Client connects via AGWPE/Direwolf
2. BBS sends welcome banner
3. BBS sends message history (if any)
4. BBS sends prompt: `YOURCALLSIGN> `
5. Client can send messages
6. Messages broadcast to all clients

### Message Format

**Timestamp:** `[HH:MM]` (24-hour)
**Broadcast:** `\r\n[{time}] {callsign}: {message}\r\n`
**Prompt:** `{client_callsign}> ` (no newline after)

### Encoding

**Recommended:** Latin-1 (ISO-8859-1)
**Also works:** ASCII (7-bit)
**Not recommended:** UTF-8 (multi-byte issues)

## Automated Tests

Fox BBS includes automated compatibility tests:

```bash
# Run compatibility test suite
pytest tests/test_client_compatibility.py -v

# Run full test suite
make test
```

Tests cover:
- All line ending types
- Various chunk sizes
- Different encodings
- Edge cases (empty messages, long messages)

## Summary

Fox BBS handles client compatibility through:
- ✅ Flexible line endings (LF, CRLF, CR)
- ✅ Robust buffering (any chunk size)
- ✅ Encoding tolerance (Latin-1 with error handling)
- ✅ Thread-safe concurrent connections

**Expected compatibility:** HIGH - should work with any standard AX.25 client.

**Need help?** See [Troubleshooting Guide](troubleshooting.md).
