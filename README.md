# Fox BBS

A Python-based BBS (Bulletin Board System) for amateur radio "fox hunting" that connects to Direwolf TNC via the AGWPE protocol.

## Features

- **Real-time Group Chat**: Multiple amateur radio stations can connect and chat simultaneously
- **Message History**: New connections receive recent messages (configurable, default: last 15 from 24 hours)
- **AGWPE Protocol**: Connects to Direwolf TNC via AGWPE protocol (default port 8000)
- **AX.25 Support**: Accepts incoming AX.25 connections from amateur radio stations
- **Thread-safe**: Proper locking for concurrent client connections
- **Configurable**: YAML-based configuration for easy customization
- **Well-tested**: Comprehensive test suite with >80% coverage
- **Type-hinted**: Full type annotations for better code quality
- **Demo Mode**: Run without hardware for development and testing

## Quick Start

### Installation

1. **Create a virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure the BBS:**
Edit `config/fox.yaml` with your callsign and settings:
```yaml
server:
  ssid: "W2ASM-10"                 # Your BBS callsign/SSID
  direwolf_host: "localhost"       # Direwolf host
  direwolf_port: 8000              # Direwolf AGWPE port
  radio_port: 0                    # Radio port number
  max_messages: 15                 # Max messages shown on connect
  message_retention_hours: 24      # How long to keep messages
```

4. **Run the BBS:**
```bash
python fox_bbs.py
```

## Usage

### Command Line Options

```bash
python fox_bbs.py [OPTIONS]

Options:
  --demo        Run in demo mode (no Direwolf required)
  --config PATH Configuration file path (default: config/fox.yaml)
  --debug       Enable debug logging
  --help        Show help message
```

### Demo Mode (No Hardware Required)

For development or testing without Direwolf/radio hardware:

```bash
python fox_bbs.py --demo
```

This allows you to develop and test the BBS functionality without needing actual radio equipment.

### Normal Operation

The server will:
1. Connect to Direwolf via AGWPE protocol on the configured port
2. Listen for incoming AX.25 connection requests
3. Show a welcome banner with the BBS SSID to connected stations
4. Display recent message history
5. Provide a prompt (`{SSID}> `) for users to post messages
6. Broadcast messages to all connected users in real-time

## Development

### Setup Development Environment

Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage report
make test-cov

# Run specific test file
pytest tests/test_config.py -v
```

### Code Quality Tools

```bash
# Format code with black and isort
make format

# Run linter
make lint

# Run type checker
make type-check

# Run all checks
make all
```

### Project Structure

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
│   ├── test_config.py
│   ├── test_message_store.py
│   ├── test_ax25_client.py
│   ├── test_agwpe_handler.py
│   ├── test_bbs_server.py
│   └── test_integration.py
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
├── pyproject.toml        # Tool configurations
├── .flake8               # Flake8 configuration
└── Makefile              # Development commands
```

## Configuration

### Configuration File Format

The `config/fox.yaml` file uses YAML format:

```yaml
server:
  # Required: Your BBS callsign with SSID (e.g., W1ABC-10)
  ssid: "W2ASM-10"

  # Direwolf connection settings
  direwolf_host: "localhost"
  direwolf_port: 8000

  # Radio port number (usually 0 for first radio)
  radio_port: 0

  # Message history settings
  max_messages: 15              # Max messages sent to new connections
  message_retention_hours: 24   # How long to keep messages
```

### Configuration Validation

The BBS automatically validates configuration on startup:
- **SSID**: Must be valid amateur radio callsign format (e.g., W1ABC-1)
- **Ports**: Direwolf port must be 1-65535, radio port 0-255
- **Message settings**: max_messages >= 0, retention_hours > 0

Invalid configuration will raise a `ConfigurationError` with a descriptive message.

## Direwolf Setup

Ensure Direwolf is configured with AGWPE support. Add to your `direwolf.conf`:

```
AGWPORT 8000
```

Start Direwolf before starting the BBS:
```bash
direwolf -c direwolf.conf
```

## Architecture

The codebase follows a clean, modular design with separation of concerns:

### Components

- **`config.py`**: Configuration management with YAML loading and validation
- **`message_store.py`**: Thread-safe message storage with time-based retention
- **`agwpe_handler.py`**: AGWPE protocol handler for Direwolf communication
- **`ax25_client.py`**: Individual AX.25 client connection handling
- **`bbs_server.py`**: Main server orchestration and message broadcasting
- **`fox_bbs.py`**: Entry point with signal handling and CLI arguments
- **`exceptions.py`**: Custom exception classes for error handling

### Design Principles

- **Type Safety**: Full type hints throughout the codebase
- **Thread Safety**: Proper locking for concurrent operations
- **Error Handling**: Custom exceptions with descriptive messages
- **Testability**: Dependency injection and mocking support
- **Documentation**: Comprehensive docstrings and inline comments

## Testing

The project includes a comprehensive test suite covering:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test components working together
- **Thread Safety**: Concurrent operation tests
- **Edge Cases**: Boundary conditions and error scenarios

### Test Coverage

```bash
# Run tests with coverage report
make test-cov

# View HTML coverage report
open htmlcov/index.html
```

Current coverage: **>80%** across all modules

### Test Structure

- `tests/conftest.py`: Shared fixtures and mocks
- `tests/test_*.py`: Test modules for each source file
- `tests/test_integration.py`: End-to-end integration tests

## Troubleshooting

### Common Issues

**BBS won't start:**
- Check Direwolf is running: `ps aux | grep direwolf`
- Verify AGWPE port in config matches Direwolf
- Check firewall isn't blocking port 8000

**No connections:**
- Verify your radio is properly configured
- Check Direwolf is receiving packets
- Ensure SSID in config matches your callsign

**Connection errors:**
- Check logs with `--debug` flag
- Verify AX.25 client is using correct callsign format
- Ensure Direwolf AGWPE is enabled

### Debug Mode

Run with debug logging for more information:
```bash
python fox_bbs.py --debug
```

## Contributing

1. Install development dependencies: `make install-dev`
2. Make your changes
3. Run tests: `make test`
4. Format code: `make format`
5. Run linters: `make lint`
6. Run type checker: `make type-check`

All checks must pass before submitting changes.

## Requirements

- **Python**: 3.7 or higher
- **PyYAML**: 6.0 or higher
- **pyham-pe**: 0.4.0 or higher (AGWPE protocol library)
- **Direwolf**: TNC software with AGWPE enabled (for production use)

### Development Requirements

See `requirements-dev.txt` for full list of development dependencies including:
- pytest (testing framework)
- black (code formatter)
- mypy (type checker)
- flake8 (linter)

## License

This software is provided as-is for amateur radio use.

## Resources

- [Direwolf Documentation](https://github.com/wb2osz/direwolf)
- [AGWPE Protocol](http://www.elcom.gr/developer/agwpe.htm)
- [AX.25 Protocol](https://www.tapr.org/pdf/AX25.2.2.pdf)
- [Amateur Radio Packet](https://en.wikipedia.org/wiki/Packet_radio)
