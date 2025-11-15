# Claude AI Coding Guidelines for Fox BBS

This document provides Fox BBS-specific guidelines. Standard Python best practices (PEP 8, type hints, docstrings) are enforced by tooling (Black, mypy, flake8) and not repeated here.

## Project Overview

Fox BBS is a group chat system for amateur radio using:
- AGWPE protocol for Direwolf TNC communication
- Thread-safe concurrent client handling (realistic max: <10 clients)
- Latin-1 encoding (standard for packet radio)
- In-memory message storage (no persistence)

## Amateur Radio Context

**Critical constraints:**
- All transmissions are PUBLIC (FCC regulations)
- No encryption allowed
- Callsigns are public identifiers
- Trust model: licensed amateur radio operators

**Implications:**
- No authentication needed
- No sensitive data handling
- Simple text-only protocol
- Input validation for callsign format only

## Fox BBS-Specific Patterns

### 1. Callsign Validation

Always use the Config class validator:

```python
# Good - uses built-in validator
config = Config.from_yaml("config/fox.yaml")  # Validates callsign

# Bad - manual regex without validation
if not re.match(r"[A-Z]\d[A-Z]", callsign):  # Incomplete pattern
```

### 2. Message Encoding

**Always use Latin-1 encoding with error handling:**

```python
# Good
text = data.decode("latin-1", errors="ignore")
data = text.encode("latin-1", errors="ignore")

# Bad
text = data.decode("utf-8")  # Will fail on packet radio data
```

**Why:** Packet radio uses single-byte encoding. Latin-1 handles all byte values 0x00-0xFF.

### 3. Line Ending Handling

**Support all three line ending types:**

```python
# Correct - handles LF, CRLF, CR
if "\r\n" in buffer:
    line, buffer = buffer.split("\r\n", 1)
elif "\n" in buffer:
    line, buffer = buffer.split("\n", 1)
elif "\r" in buffer:
    line, buffer = buffer.split("\r", 1)
```

**Why:** Different AX.25 clients use different line endings (Unix: `\n`, Windows: `\r\n`, Legacy Mac: `\r`).

### 4. Thread Safety

**Use locks for shared mutable state:**

```python
class MessageStore:
    def __init__(self):
        self._messages = deque(maxlen=15)
        self._lock = Lock()  # Required

    def add_message(self, callsign: str, text: str) -> Message:
        with self._lock:  # Always lock
            self._messages.append(Message(callsign, text))
```

**When to lock:**
- Modifying client list
- Adding/reading messages
- Any shared mutable state

**Expected concurrency:** < 10 simultaneous clients (radio bandwidth limited).

### 5. Error Handling for AGWPE

**Use custom exceptions from `src/exceptions.py`:**

```python
from src.exceptions import ConfigurationError, ConnectionError

# Good
if not direwolf_connected:
    raise ConnectionError(f"Cannot connect to Direwolf at {host}:{port}")

# Bad
if not direwolf_connected:
    raise Exception("Connection failed")  # Too generic
```

### 6. Message Flow

**Key pattern: Broadcast to all clients**

```python
def _broadcast_message(self, message: Message) -> None:
    """Broadcast to all connected clients."""
    formatted = f"\r\n{message}\r\n"
    with self.clients_lock:
        for callsign, client in list(self.clients.items()):
            if client.active:
                client.send_message(formatted)
                client.send_prompt()
```

**Important:** Use `list(self.clients.items())` to avoid modification-during-iteration errors.

## Pre-Commit Checklist

Before committing:

```bash
make format      # Black + isort
make lint        # flake8
make type-check  # mypy
make test        # pytest
```

Or run all at once:
```bash
make all
```

## Common Mistakes

**1. Forgetting Latin-1 encoding**
```python
# Wrong
data.decode("utf-8")

# Right
data.decode("latin-1", errors="ignore")
```

**2. Not using `list()` when iterating with modification**
```python
# Wrong - may raise "dictionary changed size during iteration"
for callsign, client in self.clients.items():
    del self.clients[callsign]

# Right
for callsign, client in list(self.clients.items()):
    del self.clients[callsign]
```

**3. Assuming message persistence**
```python
# Wrong assumption - messages are in-memory only
# There is no database, messages lost on restart
```

**4. Over-engineering for scale**
```python
# Unnecessary - typical use is < 5 concurrent clients
# Radio bandwidth is the bottleneck, not code
```

## Testing Requirements

**All new code must have tests:**

1. Unit tests for logic
2. Thread safety tests for concurrent code
3. Client compatibility tests for protocol changes
4. Maintain >80% coverage

**Run tests:**
```bash
pytest tests/ -v  # All tests
pytest tests/test_config.py -v  # Specific file
```

## Architecture

**Key design:**
- `config.py` - Configuration (dataclass-based)
- `message_store.py` - In-memory messages (deque with maxlen)
- `agwpe_handler.py` - AGWPE protocol via pyham-pe library
- `ax25_client.py` - Per-client state and I/O
- `bbs_server.py` - Orchestration

**Data flow:**
```
Radio → Direwolf → AGWPEHandler → AX25Client → BBSServer → MessageStore
                                                        ↓
                                                Broadcast to all clients
```

## Resources

- [AGWPE Protocol](http://www.elcom.gr/developer/agwpe.htm)
- [AX.25 Specification](https://www.tapr.org/pdf/AX25.2.2.pdf)
- [Direwolf Documentation](https://github.com/wb2osz/direwolf)

## Summary

**Focus on:**
1. Latin-1 encoding everywhere
2. Handle all line ending types
3. Thread safety for shared state
4. Amateur radio context (public, no auth)
5. Test thoroughly

**Don't worry about:**
1. Encryption/security (not allowed in amateur radio)
2. High scale (radio bandwidth limited)
3. Persistence (in-memory by design)
4. Complex authentication
