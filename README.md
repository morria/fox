# Fox BBS

A Python-based BBS (Bulletin Board System) for amateur radio "fox hunting" that connects to Direwolf TNC via the AGWPE protocol.

## What is Fox BBS?

Fox BBS provides a real-time group chat system for amateur radio operators. Multiple stations can connect simultaneously via AX.25 and participate in a shared conversation. When users connect, they receive recent message history and can immediately start chatting with other connected stations.

## Features

- Real-time group chat for multiple amateur radio stations
- Message history shown on connection (last 15 messages from 24 hours)
- AGWPE protocol support for Direwolf TNC integration
- Demo mode for testing without radio hardware
- Thread-safe for concurrent connections
- Fully type-hinted and well-tested codebase

## Quick Start

### Prerequisites

- Python 3.7 or higher
- Direwolf TNC with AGWPE enabled (or use demo mode)

### Installation

1. **Clone and navigate to the project:**
```bash
cd fox
```

2. **Create a virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Generate Direwolf configuration (recommended):**
Fox BBS includes an automatic configuration wizard:
```bash
./generate_direwolf_config.py
```

This wizard will:
- Prompt for your callsign/SSID
- Auto-detect your sound card
- Generate `config/direwolf.conf` automatically

Alternatively, you can create `config/direwolf.conf` manually (see docs/setup.md).

5. **Configure the BBS:**
Edit `config/fox.yaml` with your callsign (should match your Direwolf MYCALL):
```yaml
server:
  ssid: "W2ASM-10"                 # Your BBS callsign/SSID
  direwolf_host: "localhost"       # Direwolf host
  direwolf_port: 8000              # Direwolf AGWPE port
  radio_port: 0                    # Radio port number
```

6. **Run the BBS:**

For demo mode (no hardware required):
```bash
python fox_bbs.py --demo
```

For normal operation (Direwolf starts automatically):
```bash
python fox_bbs.py
```

Fox BBS will automatically:
- Check if Direwolf is running
- Start Direwolf if needed
- Monitor both processes
- Shutdown gracefully if either process fails

Alternatively, you can manually start Direwolf first:
```bash
# Terminal 1: Start Direwolf
./direwolf

# Terminal 2: Start Fox BBS
python fox_bbs.py --no-auto-direwolf
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

### What Users See

When a station connects to the BBS:

1. Welcome banner with the BBS SSID
2. Recent message history (last 15 messages from 24 hours)
3. A prompt (`W2ASM-10> `) to type messages
4. Real-time messages from other connected users

## Documentation

- **[Setup Guide](docs/setup.md)** - Detailed setup instructions for Direwolf and Fox BBS
- **[Configuration](docs/configuration.md)** - Complete configuration reference
- **[Development](docs/development.md)** - Development setup, testing, and contributing
- **[Architecture](docs/architecture.md)** - Technical architecture and design
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

## Requirements

- Python 3.7+
- PyYAML 6.0+
- pyham-pe 0.4.0+ (AGWPE protocol library)
- Direwolf TNC with AGWPE enabled (for production use)

## Project Structure

```
fox/
├── fox_bbs.py              # Main entry point
├── config/fox.yaml         # Configuration file
├── src/                    # Source code
│   ├── config.py           # Configuration management
│   ├── message_store.py    # Message storage
│   ├── agwpe_handler.py    # AGWPE protocol handler
│   ├── ax25_client.py      # Client connection handler
│   └── bbs_server.py       # Main server logic
├── tests/                  # Test suite
└── docs/                   # Documentation
```

## License

This software is provided as-is for amateur radio use.

## Resources

- [Direwolf Documentation](https://github.com/wb2osz/direwolf)
- [AGWPE Protocol](http://www.elcom.gr/developer/agwpe.htm)
- [AX.25 Protocol](https://www.tapr.org/pdf/AX25.2.2.pdf)
