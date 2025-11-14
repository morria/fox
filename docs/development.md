# Development Guide

This guide covers setting up a development environment, running tests, code quality tools, and contributing to Fox BBS.

## Development Setup

### Prerequisites

- Python 3.7 or higher
- Git
- Virtual environment support

### Initial Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd fox
```

2. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install development dependencies:**
```bash
pip install -r requirements-dev.txt
```

This installs both production dependencies and development tools:
- pytest (testing framework)
- black (code formatter)
- isort (import sorter)
- mypy (type checker)
- flake8 (linter)
- coverage (code coverage)

## Running Tests

Fox BBS has a comprehensive test suite with >80% code coverage.

### Run All Tests

```bash
# Using make (recommended)
make test

# Using pytest directly
pytest tests/ -v
```

### Run Specific Tests

```bash
# Test a specific file
pytest tests/test_config.py -v

# Test a specific function
pytest tests/test_message_store.py::test_add_message -v

# Run tests matching a pattern
pytest tests/ -k "test_config" -v
```

### Test Coverage

```bash
# Run tests with coverage report
make test-cov

# View HTML coverage report
make test-cov
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

Coverage reports show:
- Line coverage by file
- Uncovered lines
- Branch coverage
- Overall project coverage

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures and mocks
├── test_config.py           # Configuration tests
├── test_message_store.py    # Message storage tests
├── test_ax25_client.py      # Client handler tests
├── test_agwpe_handler.py    # AGWPE protocol tests
├── test_bbs_server.py       # Server logic tests
└── test_integration.py      # End-to-end tests
```

### Writing Tests

Follow these guidelines when writing tests:

1. **Use descriptive names:**
```python
def test_config_validates_invalid_ssid():
    """Test that invalid SSID format raises ConfigurationError."""
```

2. **Use fixtures from conftest.py:**
```python
def test_message_store(message_store):
    """message_store fixture provides a clean MessageStore instance."""
```

3. **Test edge cases:**
```python
def test_message_store_with_empty_history(message_store):
    """Test behavior when no messages exist."""
```

4. **Test thread safety for concurrent code:**
```python
def test_concurrent_message_addition(message_store):
    """Test thread-safe message additions."""
```

## Code Quality Tools

### Code Formatting

Fox BBS uses **black** for code formatting and **isort** for import sorting.

```bash
# Format all code
make format

# Check formatting without making changes
black --check src/ tests/
isort --check-only src/ tests/
```

**Black settings** (in `pyproject.toml`):
- Line length: 88 characters
- Python 3.7+ syntax

**isort settings** (in `pyproject.toml`):
- Compatible with black
- Multi-line mode: 3

### Linting

Use **flake8** for code linting:

```bash
# Run linter
make lint

# Run flake8 directly
flake8 src/ tests/
```

**Flake8 configuration** (in `.flake8`):
- Max line length: 88 (matches black)
- Ignores: E203, W503 (conflicts with black)

### Type Checking

Fox BBS uses full type hints throughout. Use **mypy** for type checking:

```bash
# Run type checker
make type-check

# Run mypy directly
mypy src/
```

**mypy settings** (in `pyproject.toml`):
- Strict mode enabled
- No implicit optional
- Warn on redundant casts

### Run All Checks

```bash
# Run formatter, linter, type checker, and tests
make all
```

This runs:
1. `black` and `isort` (formatting)
2. `flake8` (linting)
3. `mypy` (type checking)
4. `pytest` (tests)

## Project Structure

```
fox/
├── fox_bbs.py              # Main entry point
├── config/
│   └── fox.yaml           # Configuration file
├── src/                   # Source code
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── message_store.py   # Message storage & retrieval
│   ├── agwpe_handler.py   # AGWPE protocol handler
│   ├── ax25_client.py     # Client connection handler
│   ├── bbs_server.py      # Main server logic
│   └── exceptions.py      # Custom exceptions
├── tests/                 # Test suite
│   ├── conftest.py        # Test fixtures
│   ├── test_*.py          # Test modules
│   └── test_integration.py
├── docs/                  # Documentation
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
├── pyproject.toml        # Tool configurations
├── .flake8               # Flake8 configuration
└── Makefile              # Development commands
```

## Makefile Commands

The `Makefile` provides convenient commands for common tasks:

```bash
make install-dev    # Install development dependencies
make test          # Run tests
make test-cov      # Run tests with coverage
make format        # Format code with black and isort
make lint          # Run flake8 linter
make type-check    # Run mypy type checker
make all           # Run all checks (format, lint, type-check, test)
make clean         # Remove build artifacts and cache files
```

## Coding Standards

### Python Style

- Follow PEP 8 (enforced by flake8)
- Use black for formatting (88 character line length)
- Sort imports with isort
- Use type hints for all functions

### Type Hints

All functions must have type hints:

```python
def add_message(self, callsign: str, message: str) -> None:
    """Add a message to the store."""
    ...

def get_recent_messages(self, limit: int) -> List[Message]:
    """Retrieve recent messages."""
    ...
```

### Docstrings

Use docstrings for all public functions, classes, and modules:

```python
def connect_to_server(self, ssid: str, port: int) -> None:
    """
    Connect to Direwolf AGWPE server.

    Args:
        ssid: Station callsign with SSID (e.g., 'W1ABC-10')
        port: Radio port number (0-255)

    Raises:
        ConnectionError: If connection to Direwolf fails
        ConfigurationError: If SSID format is invalid
    """
```

### Error Handling

- Use custom exceptions from `exceptions.py`
- Provide descriptive error messages
- Log errors appropriately

```python
from src.exceptions import ConfigurationError

if not valid_ssid(ssid):
    raise ConfigurationError(
        f"Invalid SSID format: '{ssid}'. "
        f"Must be amateur radio callsign with SSID (e.g., W1ABC-10)"
    )
```

### Thread Safety

- Use locks for shared state
- Document thread-safety guarantees
- Test concurrent operations

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

## Contributing

### Before Submitting Changes

1. **Run all checks:**
```bash
make all
```

2. **Ensure tests pass:**
```bash
make test-cov
```

3. **Check coverage hasn't decreased**

4. **Update documentation if needed**

### Commit Messages

Use clear, descriptive commit messages:

```
Add message filtering by age

- Implement time-based message filtering in MessageStore
- Add tests for retention period functionality
- Update documentation with new configuration option
```

### Pull Request Checklist

- [ ] All tests pass (`make test`)
- [ ] Code is formatted (`make format`)
- [ ] Linter passes (`make lint`)
- [ ] Type checker passes (`make type-check`)
- [ ] Coverage maintained or improved
- [ ] Documentation updated
- [ ] Commit messages are clear

## Debugging

### Debug Mode

Run with debug logging:

```bash
python fox_bbs.py --debug
```

This enables detailed logging including:
- AGWPE protocol messages
- Client connection events
- Message broadcasting
- Error tracebacks

### Demo Mode for Development

Test without Direwolf:

```bash
python fox_bbs.py --demo
```

Benefits:
- No need for Direwolf or radio hardware
- Faster iteration during development
- Safe testing of changes

### Common Development Issues

**Import errors:**
```bash
# Ensure you're in the virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements-dev.txt
```

**Test failures:**
```bash
# Run specific failing test with verbose output
pytest tests/test_specific.py::test_name -vv

# Check for test pollution (run tests in isolation)
pytest tests/test_specific.py --forked
```

**Type checking errors:**
```bash
# Run mypy with more detail
mypy --show-error-codes src/

# Ignore specific errors (use sparingly)
# type: ignore[error-code]
```

## Resources

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [pytest Documentation](https://docs.pytest.org/)
- [black Code Style](https://black.readthedocs.io/)
- [PEP 8 Style Guide](https://pep8.org/)
