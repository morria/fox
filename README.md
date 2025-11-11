# Fox BBS

A Python-based BBS (Bulletin Board System) for amateur radio "fox hunting" that connects to Direwolf TNC via the AGWPE protocol.

## Features

- Connects to Direwolf TNC via AGWPE protocol (default port 8000)
- Accepts incoming AX.25 connections
- Group chat interface with message history
- Shows last 15 messages from the past 24 hours on connect
- Real-time message broadcasting to all connected clients
- Configurable SSID and settings
- Uses pyham-pe library for AGWPE protocol support

## Installation

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Edit `config/fox.yaml` to configure the BBS:

```yaml
server:
  ssid: "W2ASM-11"                 # BBS callsign/SSID
  direwolf_host: "localhost"       # Direwolf host
  direwolf_port: 8000              # Direwolf AGWPE port (default 8000)
  radio_port: 0                    # Radio port number (usually 0)
  max_messages: 15                 # Max messages shown on connect
  message_retention_hours: 24      # How long to keep messages
```

## Usage

Run the BBS server:

```bash
python fox_bbs.py
```

The server will:
1. Connect to Direwolf via AGWPE protocol on the configured port
2. Listen for incoming AX.25 connection requests
3. Show a welcome banner with the BBS SSID to connected stations
4. Display recent message history (last 15 messages from 24 hours)
5. Provide a prompt (`{SSID}> `) for users to post messages
6. Broadcast messages to all connected users in real-time

## Architecture

The codebase follows a modular, Pythonic design:

- `src/config.py` - Configuration management using YAML
- `src/message_store.py` - Message storage with time-based retention
- `src/agwpe_handler.py` - AGWPE protocol handler for Direwolf communication
- `src/ax25_client.py` - Individual AX.25 client connection handling
- `src/bbs_server.py` - Main server logic and message broadcasting
- `fox_bbs.py` - Entry point and signal handling

## Requirements

- Python 3.7+
- PyYAML
- pyham-pe (AGWPE protocol library)
- Direwolf TNC running with AGWPE enabled (typically port 8000)

## Direwolf Configuration

Ensure your Direwolf configuration includes AGWPE support. Add this to your `direwolf.conf`:

```
AGWPORT 8000
```

## License

This software is provided as-is for amateur radio use.
