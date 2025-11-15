# Claude AI Coding Guidelines for Fox BBS

This document provides guidelines for Claude AI when working on the Fox BBS codebase. Following these guidelines ensures consistent, high-quality code that matches the project's standards.

## Project Overview

Fox BBS is a Python-based BBS for amateur radio that uses:
- Python 3.7+ with full type hints
- AGWPE protocol for Direwolf TNC communication
- Thread-safe concurrent client handling
- YAML configuration
- Comprehensive test coverage (>80%)

## Code Style and Formatting

### Python Style

**Always follow these rules:**

1. **Use Black formatting:**
   - Line length: 88 characters
   - All code must be Black-formatted before committing
   - Run: `make format` or `black src/ tests/`

2. **Use isort for imports:**
   - Group imports: standard library, third-party, local
   - Run: `make format` or `isort src/ tests/`

3. **Follow PEP 8:**
   - Enforced by flake8
   - Check with: `make lint`

### Type Hints

**CRITICAL: All functions must have complete type hints.**

**Good:**
```python
def add_message(self, callsign: str, message: str) -> None:
    """Add a message to the store."""
    ...

def get_recent_messages(
    self, limit: int, max_age_hours: int
) -> List[Message]:
    """Retrieve recent messages within age limit."""
    ...
```

**Bad:**
```python
def add_message(self, callsign, message):  # Missing type hints
    ...

def get_recent_messages(self, limit: int):  # Incomplete hints
    ...
```

**Type hint requirements:**
- All function parameters must have type hints
- All return values must have type hints (use `-> None` for no return)
- Use `Optional[T]` for values that can be None
- Use `List[T]`, `Dict[K, V]`, etc. for collections
- Import types from `typing` module

### Docstrings

**All public functions, classes, and modules must have docstrings.**

**Format:**
```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief one-line description.

    Longer description if needed. Explain the purpose,
    behavior, and any important details.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ExceptionType: When this exception is raised

    Example:
        >>> function_name("test", 42)
        True
    """
```

**For simple functions:**
```python
def is_valid_ssid(ssid: str) -> bool:
    """Check if SSID matches amateur radio callsign format."""
```

## Code Quality Standards

### Before Submitting Code

**ALWAYS run these checks:**

```bash
make format      # Format with black and isort
make lint        # Check with flake8
make type-check  # Verify type hints with mypy
make test        # Run all tests
```

**Or run all at once:**
```bash
make all
```

**Never submit code that:**
- Doesn't pass type checking (`mypy`)
- Doesn't pass linting (`flake8`)
- Doesn't pass tests (`pytest`)
- Isn't formatted with `black`

### Writing Tests

**CRITICAL: All new code must have tests.**

**Test requirements:**
1. Test all public functions
2. Test error conditions
3. Test edge cases (empty input, None, boundary values)
4. Test thread safety for concurrent code
5. Maintain or improve coverage (>80%)

**Test structure:**
```python
def test_feature_name():
    """Test that feature does X when given Y."""
    # Arrange
    setup_test_data()

    # Act
    result = perform_operation()

    # Assert
    assert result == expected_value
```

**For thread-safe code:**
```python
def test_concurrent_access():
    """Test thread-safe concurrent operations."""
    import threading

    def worker():
        # Perform operation
        pass

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify results
    assert expected_state()
```

## Thread Safety

### When to Use Locks

**Use `threading.Lock()` for:**
- Shared mutable state (lists, dicts)
- Non-atomic operations on shared data
- Operations that must be atomic

**Example:**
```python
class MessageStore:
    """Thread-safe message storage."""

    def __init__(self):
        self._messages: List[Message] = []
        self._lock = threading.Lock()

    def add_message(self, callsign: str, message: str) -> None:
        """Thread-safe message addition."""
        with self._lock:
            self._messages.append(Message(callsign, message))
```

**Document thread safety:**
```python
class ClientManager:
    """
    Manages connected clients.

    Thread-safe: All public methods use internal locking.
    """
```

## Error Handling

### Use Custom Exceptions

**Always use custom exceptions from `src/exceptions.py`:**

```python
from src.exceptions import ConfigurationError, ConnectionError

def load_config(path: str) -> ServerConfig:
    """Load configuration from file."""
    if not os.path.exists(path):
        raise ConfigurationError(
            f"Configuration file not found: {path}"
        )
```

### Provide Descriptive Error Messages

**Good:**
```python
raise ConfigurationError(
    f"Invalid SSID format: '{ssid}'. "
    f"Must be amateur radio callsign with SSID (e.g., W1ABC-10)"
)
```

**Bad:**
```python
raise ValueError("Invalid SSID")  # Not descriptive, wrong exception type
```

### Error Handling Guidelines

1. **Catch specific exceptions**, not broad `Exception`
2. **Log errors** with appropriate level (ERROR, WARNING)
3. **Clean up resources** in finally blocks or context managers
4. **Don't silently ignore errors** (no empty except blocks)

**Good:**
```python
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    handle_error(e)
finally:
    cleanup_resources()
```

**Bad:**
```python
try:
    result = risky_operation()
except Exception:
    pass  # Silent failure - BAD!
```

## Architecture Guidelines

### Separation of Concerns

**Each module should have ONE responsibility:**

- `config.py` → Configuration management only
- `message_store.py` → Message storage only
- `agwpe_handler.py` → AGWPE protocol only
- `ax25_client.py` → Client connection handling only
- `bbs_server.py` → Orchestration only

**Don't:**
- Put database code in the web handler
- Mix protocol handling with business logic
- Combine unrelated functionality

### Dependency Injection

**Use dependency injection for testability:**

**Good:**
```python
class BBSServer:
    def __init__(
        self,
        config: ServerConfig,
        message_store: MessageStore,
        agwpe_handler: AGWPEHandler
    ):
        self._config = config
        self._store = message_store
        self._handler = agwpe_handler
```

**Bad:**
```python
class BBSServer:
    def __init__(self):
        self._config = load_config()  # Hard to test
        self._store = MessageStore()  # Hard to mock
```

### Immutability Where Possible

**Prefer immutable data structures:**

```python
from dataclasses import dataclass

@dataclass(frozen=True)  # Immutable
class Message:
    timestamp: datetime
    callsign: str
    text: str
```

## Logging

### Log Levels

Use appropriate log levels:

- **DEBUG:** Detailed information for debugging (use `--debug` flag)
- **INFO:** General informational messages
- **WARNING:** Warning messages (deprecated features, non-critical issues)
- **ERROR:** Error messages (operation failures)
- **CRITICAL:** Critical errors (system failures)

**Example:**
```python
import logging

logger = logging.getLogger(__name__)

logger.debug(f"Received frame: {frame}")
logger.info(f"Client connected: {callsign}")
logger.warning(f"Unusual condition: {condition}")
logger.error(f"Failed to send message: {error}")
logger.critical(f"System failure: {error}")
```

### Logging Guidelines

1. **Use f-strings** for log messages
2. **Include context** (callsign, port, etc.)
3. **Don't log sensitive data** (though amateur radio has no secrets)
4. **Use appropriate levels**

## Configuration

### Adding New Configuration Options

**Follow this pattern:**

1. **Add to ServerConfig dataclass:**
```python
@dataclass
class ServerConfig:
    # Existing fields...
    new_option: int  # Add new field with type
```

2. **Add validation:**
```python
def validate_config(config: ServerConfig) -> None:
    """Validate configuration values."""
    # Existing validations...

    if config.new_option < 0:
        raise ConfigurationError(
            f"new_option must be non-negative, got: {config.new_option}"
        )
```

3. **Update config/fox.yaml example:**
```yaml
server:
  # Existing options...
  new_option: 42  # Description of what this does
```

4. **Update documentation:**
- Add to `docs/configuration.md`
- Update README if user-facing

## Common Patterns

### Context Managers

**Use context managers for resource cleanup:**

```python
class AGWPEHandler:
    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

# Usage
with AGWPEHandler(config) as handler:
    handler.listen()
# Automatically disconnected
```

### Dataclasses

**Use dataclasses for structured data:**

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Message:
    """A chat message."""
    timestamp: datetime
    callsign: str
    text: str
```

### Properties

**Use properties for computed values:**

```python
class Client:
    @property
    def is_connected(self) -> bool:
        """Check if client is still connected."""
        return self._socket is not None and not self._disconnected
```

## Security Considerations

### Amateur Radio Context

**Remember:**
- Amateur radio transmissions are PUBLIC
- No encryption allowed (FCC regulations)
- Callsigns are public identifiers
- Trust model based on amateur radio regulations

### Input Validation

**Always validate input:**

```python
def set_ssid(self, ssid: str) -> None:
    """Set station SSID."""
    if not self._is_valid_ssid(ssid):
        raise ConfigurationError(f"Invalid SSID: {ssid}")
    self._ssid = ssid
```

### No SQL Injection Risk

- No database (everything in memory)
- No SQL queries to inject

### No XSS Risk

- No web interface
- Text-only protocol

## Testing Best Practices

### Test Structure

**Organize tests logically:**

```python
class TestMessageStore:
    """Tests for MessageStore class."""

    def test_add_message(self, message_store):
        """Test adding a message."""
        ...

    def test_get_recent_messages(self, message_store):
        """Test retrieving recent messages."""
        ...

    def test_message_age_filtering(self, message_store):
        """Test filtering by message age."""
        ...
```

### Use Fixtures

**Define fixtures in conftest.py:**

```python
@pytest.fixture
def message_store():
    """Provide a clean MessageStore instance."""
    return MessageStore()

@pytest.fixture
def sample_config():
    """Provide a valid test configuration."""
    return ServerConfig(
        ssid="W1ABC-10",
        direwolf_host="localhost",
        direwolf_port=8000,
        radio_port=0,
        max_messages=15,
        message_retention_hours=24
    )
```

### Mock External Dependencies

**Mock Direwolf connection in tests:**

```python
from unittest.mock import Mock, patch

def test_server_startup(sample_config):
    """Test server startup without real Direwolf."""
    with patch('src.agwpe_handler.socket.socket') as mock_socket:
        mock_socket.return_value.connect.return_value = None
        server = BBSServer(sample_config)
        server.start()
        assert server.is_running
```

## Documentation

### Update Documentation

**When making changes, update:**

1. **Code docstrings** - Keep in sync with implementation
2. **README.md** - If user-facing features change
3. **docs/** - Update relevant documentation files
4. **CLAUDE.md** - If coding standards change

### Documentation Style

**Use clear, concise language:**

- Write for users, not just developers
- Include examples
- Explain WHY, not just WHAT
- Keep formatting consistent

## Git Commit Messages

### Commit Message Format

**Use this format:**

```
Brief summary (50 chars or less)

More detailed explanation if needed. Wrap at 72 characters.
Explain what changed and why, not how (code shows how).

- Bullet points for multiple changes
- Keep each point focused
- Reference issues if applicable
```

**Good examples:**
```
Add message age filtering to MessageStore

Implement time-based filtering so users only see recent
messages based on the configured retention period.

- Add get_recent_messages method with max_age_hours parameter
- Add tests for age filtering
- Update documentation
```

**Bad examples:**
```
Fixed bug  # Too vague
Update code  # No information
Changed stuff in message store  # Not descriptive
```

## Pre-Commit Checklist

**Before committing code, verify:**

- [ ] Code is formatted (`make format`)
- [ ] Linting passes (`make lint`)
- [ ] Type checking passes (`make type-check`)
- [ ] All tests pass (`make test`)
- [ ] New code has tests
- [ ] Coverage hasn't decreased
- [ ] Docstrings added/updated
- [ ] Documentation updated
- [ ] Commit message is descriptive

**Run all checks:**
```bash
make all && echo "✓ Ready to commit"
```

## Common Mistakes to Avoid

### Don't Do This

1. **Missing type hints:**
```python
def process(data):  # Bad - no type hints
    ...
```

2. **Broad exception catching:**
```python
try:
    risky_operation()
except Exception:  # Bad - too broad
    pass
```

3. **Mutable default arguments:**
```python
def func(items=[]):  # Bad - mutable default
    items.append(1)
```

4. **Not using locks for shared state:**
```python
class Store:
    def __init__(self):
        self.items = []  # Bad - no lock for shared list

    def add(self, item):
        self.items.append(item)  # Race condition!
```

5. **Ignoring test failures:**
```python
# Bad - don't skip failing tests without good reason
@pytest.mark.skip("TODO: fix this later")
def test_important_feature():
    ...
```

## Summary

**Key principles:**

1. **Type hints everywhere** - No exceptions
2. **Thread safety** - Use locks for shared state
3. **Test everything** - Maintain >80% coverage
4. **Format consistently** - Use black and isort
5. **Handle errors properly** - Use custom exceptions
6. **Document well** - Docstrings and external docs
7. **Run all checks** - Before committing

**When in doubt:**
- Check existing code for patterns
- Review [Architecture Documentation](docs/architecture.md)
- Follow [Development Guide](docs/development.md)
- Run `make all` to verify everything works

**Remember:** This is amateur radio software. Keep it clean, well-tested, and maintainable!
