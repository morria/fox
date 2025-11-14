# Client Compatibility Test Results

This file tracks real-world testing results with various AX.25 clients.

## Test Results

### Automated Tests

| Test Suite | Status | Date | Notes |
|------------|--------|------|-------|
| Unit tests (test_client_compatibility.py) | ✅ PASS | 2025-11-14 | 30+ test cases covering all scenarios |
| Client simulator (5 profiles) | ✅ PASS | 2025-11-14 | All simulated client behaviors work |
| Existing integration tests | ✅ PASS | 2025-11-14 | Thread safety and concurrent handling verified |

### Real-World Client Testing

| Client | Version | Platform | Status | Tested By | Date | Notes |
|--------|---------|----------|--------|-----------|------|-------|
| Mock AGWPE | N/A | All | ✅ PASS | Automated | 2025-11-14 | Comprehensive test coverage |
| ax25call | TBD | Linux | 🔄 To Test | - | - | Standard Linux tool |
| Packet Commander | TBD | Windows | 🔄 To Test | - | - | Popular Windows GUI |
| APRSdroid | TBD | Android | 🔄 To Test | - | - | Mobile client |
| BPQ32 Terminal | TBD | Windows | 🔄 To Test | - | - | Legacy BBS software |

## Test Scenarios Verified

### Line Endings ✅
- [x] LF only (`\n`) - Linux/Unix clients
- [x] CRLF (`\r\n`) - Windows clients
- [x] CR only (`\r`) - Legacy Mac/terminal clients
- [x] Mixed line endings - Buggy clients

### Buffering ✅
- [x] Character-by-character transmission
- [x] Small chunks (8-32 bytes) - Mobile clients
- [x] Medium chunks (64 bytes) - Desktop clients
- [x] Large buffers - Multiple messages at once
- [x] Incomplete messages across multiple calls

### Encoding ✅
- [x] ASCII (7-bit)
- [x] Latin-1 (8-bit) with extended characters
- [x] Invalid byte sequences (graceful degradation)
- [x] UTF-8 misconfiguration handling

### Edge Cases ✅
- [x] Empty messages (ignored correctly)
- [x] Whitespace-only messages (ignored correctly)
- [x] Very long messages (1000+ characters)
- [x] Rapid connect/disconnect
- [x] Null bytes in stream
- [x] Binary data with newlines

### Concurrent Operations ✅
- [x] 10 simultaneous connections
- [x] 50 concurrent messages (5 clients × 10 messages)
- [x] Thread-safe client collection
- [x] Thread-safe message broadcasting

## Known Issues

None currently identified in automated testing.

## Recommendations for Real-World Testing

### High Priority
1. **ax25call (Linux)** - Most common command-line tool
2. **Packet Commander (Windows)** - Popular GUI client
3. **One mobile client** - Android or iOS AX.25 app

### Medium Priority
4. BPQ32 Terminal - Common in BBS networks
5. YAAC - Java-based cross-platform client
6. Any other clients your community uses

### Testing Checklist

For each client, verify:
- [ ] Welcome banner displays correctly
- [ ] Message history shows (if any messages exist)
- [ ] Prompt shows YOUR callsign (not BBS callsign)
- [ ] Can send messages successfully
- [ ] Messages appear for other connected clients
- [ ] Line endings work correctly (Enter key)
- [ ] Disconnect is clean (no errors)
- [ ] Can reconnect successfully

## How to Test

### Automated Testing
```bash
# Run compatibility test suite
pytest tests/test_client_compatibility.py -v

# Run client simulator (all profiles)
python tests/scripts/test_client_simulator.py

# Run specific client profile
python tests/scripts/test_client_simulator.py --client ax25call
```

### Manual Testing
Follow the guide: `tests/manual_test_clients.md`

## Recording Results

When testing a new client, update this file with:

```markdown
| Client Name | Version | Platform | ✅/⚠️/❌ | Your Name | YYYY-MM-DD | Notes about behavior |
```

**Status codes:**
- ✅ PASS - Works perfectly
- ⚠️ PARTIAL - Works with minor issues
- ❌ FAIL - Does not work

## Contributing

Tested a client not listed here? Please:
1. Follow the manual testing guide
2. Document your results
3. Open a pull request updating this file
4. Include any issues encountered and solutions

---

## Test Session Log

### Session: 2025-11-14 (Automated Testing)

**Tester:** Automated Test Suite

**Tests Run:**
- 30 unit tests in `test_client_compatibility.py`
- 5 client behavior profiles in simulator
- All existing integration tests

**Results:** ✅ All tests passed

**Notes:**
- Initial implementation of compatibility test suite
- Covers all identified client behavior patterns
- Ready for real-world client testing

---

*For questions about compatibility testing, see: `docs/client-compatibility.md`*
