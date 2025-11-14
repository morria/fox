# Manual Client Compatibility Testing

This guide helps you test Fox BBS with real AX.25 clients.

## Prerequisites

1. Fox BBS running with Direwolf
2. Radio hardware or `soundmodem` for testing
3. Test clients installed

## Test Procedure

### 1. Test with ax25call (Linux)

**Setup:**
```bash
# Install ax25-tools if not present
sudo apt-get install ax25-tools

# Configure ax25 interface (if not already done)
# This requires Direwolf running
```

**Test:**
```bash
# Connect to BBS
ax25call radio W1ABC-10

# Expected behavior:
# 1. See welcome banner
# 2. See message history (if any)
# 3. See prompt with YOUR callsign
# 4. Type message and press Enter
# 5. See your message broadcast
# 6. Disconnect cleanly (Ctrl-D or ~.)
```

**Validation checklist:**
- [ ] Welcome banner displays correctly
- [ ] Prompt shows client callsign (not BBS callsign)
- [ ] Messages send and receive properly
- [ ] Line endings work (Enter key)
- [ ] Disconnect is clean (no errors in BBS log)

---

### 2. Test with Packet Commander (Windows)

**Setup:**
1. Install Packet Commander
2. Configure AGWPE connection to Direwolf
3. Set terminal to "ANSI" or "TTY" mode

**Test:**
```
# In Packet Commander:
1. Connect to BBS callsign
2. Observe welcome sequence
3. Type test message
4. Send message
5. Disconnect
```

**Validation checklist:**
- [ ] CRLF line endings handled
- [ ] Unicode/extended characters handled gracefully
- [ ] Large message buffers work
- [ ] Disconnect doesn't hang

---

### 3. Test with Android AX.25 Apps

**Popular Android apps to test:**
- APRSdroid (if it supports connected mode)
- HamGPS
- Other packet radio apps

**Test:**
```
1. Configure app to connect via Direwolf
2. Connect to BBS
3. Verify display formatting
4. Send messages
5. Verify reception
```

**Validation checklist:**
- [ ] Mobile display formatting acceptable
- [ ] Touch keyboard line endings work
- [ ] App doesn't timeout waiting for data
- [ ] Disconnect is clean

---

### 4. Test with BPQ32 Terminal

**Setup:**
1. Install BPQ32 suite
2. Configure AGWPE port
3. Open terminal window

**Test:**
```
# Connect via BPQ
C W1ABC-10

# Test interaction
# Disconnect
B
```

**Validation checklist:**
- [ ] Legacy encoding compatibility
- [ ] Terminal control codes handled
- [ ] Message formatting preserved

---

## Automated Test Client Script

For automated testing, use the provided test client:

```bash
# Run automated client compatibility test
python tests/scripts/test_client_simulator.py --client ax25call
python tests/scripts/test_client_simulator.py --client packet-commander
python tests/scripts/test_client_simulator.py --client android
```

---

## Logging Test Results

Document results in `tests/compatibility_results.md`:

```markdown
## Test Session: 2025-11-14

### ax25call 0.0.15
- Status: ✅ PASS
- Platform: Linux (Debian 12)
- Notes: All features work correctly

### Packet Commander 1.3
- Status: ⚠️ PARTIAL
- Platform: Windows 11
- Issues: Extended characters display as `?`
- Workaround: Use ASCII-only messages
```

---

## Common Issues & Solutions

### Issue: Client sees garbage characters
**Cause:** Encoding mismatch
**Solution:** BBS uses latin-1, client should match

### Issue: Messages don't appear until Enter pressed twice
**Cause:** Client expecting different line ending
**Solution:** BBS already handles all endings, may be client-side buffering

### Issue: Prompt doesn't appear
**Cause:** Client not flushing output or BBS not sending
**Solution:** Check BBS logs for send errors

### Issue: Connection drops immediately
**Cause:** AGWPE/Direwolf configuration
**Solution:** Check radio port configuration in config/fox.yaml

---

## Continuous Testing

**Recommended schedule:**
1. Test with ax25call before each release
2. Test with at least 2 different clients per major version
3. Maintain compatibility matrix in docs/

**Automated CI testing:**
- Use mock AGWPE interface (already in test suite)
- Simulate different client behaviors
- Run on every commit
