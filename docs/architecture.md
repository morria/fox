# Architecture Documentation

This document describes the technical architecture, design principles, and component interactions in Fox BBS.

## Overview

Fox BBS is built as a modular, event-driven system that bridges amateur radio packet networks (via Direwolf TNC) with a multi-user chat application. The architecture emphasizes thread safety, type safety, and clean separation of concerns.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Fox BBS                              │
│                                                               │
│  ┌───────────────┐      ┌──────────────┐      ┌──────────┐ │
│  │   fox_bbs.py  │──────│ BBSServer    │──────│ Message  │ │
│  │  (Entry Point)│      │              │      │  Store   │ │
│  └───────────────┘      └──────────────┘      └──────────┘ │
│                                │                             │
│                         ┌──────┴──────┐                     │
│                         │             │                     │
│                    ┌────▼───┐    ┌───▼────┐               │
│                    │ AGWPE  │    │ AX.25  │               │
│                    │Handler │    │ Client │               │
│                    └────────┘    └────────┘               │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ AGWPE Protocol (TCP port 8000)
                      │
               ┌──────▼──────┐
               │  Direwolf   │
               │     TNC     │
               └──────┬──────┘
                      │
                      │ Audio/Radio Interface
                      │
               ┌──────▼──────┐
               │    Radio    │
               │  Hardware   │
               └─────────────┘
```

## Components

### 1. fox_bbs.py (Entry Point)

**Purpose:** Application entry point with command-line interface and signal handling.

**Responsibilities:**
- Parse command-line arguments
- Load configuration
- Initialize and start BBSServer
- Handle graceful shutdown (SIGINT, SIGTERM)
- Provide demo mode support

**Key Features:**
- Signal handler for clean shutdown
- Configuration validation
- Error handling and logging setup

**Location:** `fox_bbs.py:1-100`

### 2. config.py (Configuration Management)

**Purpose:** Load, validate, and provide access to configuration settings.

**Responsibilities:**
- Load YAML configuration from file
- Validate configuration values
- Provide type-safe configuration access
- Raise descriptive errors for invalid config

**Data Model:**
```python
@dataclass
class ServerConfig:
    ssid: str                      # BBS callsign/SSID
    direwolf_host: str            # Direwolf hostname
    direwolf_port: int            # AGWPE port
    radio_port: int               # Radio port number
    max_messages: int             # Max history messages
    message_retention_hours: int  # Message retention period
```

**Validation Rules:**
- SSID must match amateur radio callsign format
- Ports must be in valid ranges
- Message settings must be positive

**Location:** `src/config.py`

### 3. message_store.py (Message Storage)

**Purpose:** Thread-safe storage and retrieval of chat messages.

**Responsibilities:**
- Store messages with timestamps and callsigns
- Filter messages by age (retention period)
- Provide recent message history
- Thread-safe concurrent access

**Data Model:**
```python
@dataclass
class Message:
    timestamp: datetime
    callsign: str
    text: str
```

**Thread Safety:**
- Uses `threading.Lock` for all operations
- Safe for concurrent reads and writes
- Lock acquired for list operations

**Key Methods:**
- `add_message(callsign: str, message: str) -> None`
- `get_recent_messages(limit: int, max_age_hours: int) -> List[Message]`

**Location:** `src/message_store.py`

### 4. agwpe_handler.py (AGWPE Protocol Handler)

**Purpose:** Handle AGWPE protocol communication with Direwolf TNC.

**Responsibilities:**
- Connect to Direwolf via TCP socket
- Register with AGWPE protocol
- Listen for incoming AX.25 connection requests
- Accept connections and create AX25Client instances
- Handle protocol-level communication

**AGWPE Protocol:**
- Version 1.0 protocol support
- Frame types: 'k' (register), 'C' (connect request)
- Binary protocol with specific frame structure

**Connection Flow:**
1. Connect to Direwolf TCP socket
2. Send registration frame ('k' type)
3. Listen for incoming connection frames ('C' type)
4. Create AX25Client for each connection
5. Notify BBSServer of new clients

**Location:** `src/agwpe_handler.py`

### 5. ax25_client.py (Client Connection Handler)

**Purpose:** Handle individual AX.25 client connections and message I/O.

**Responsibilities:**
- Manage single client connection state
- Send welcome banner and message history
- Receive messages from client
- Send messages to client
- Handle connection errors and disconnection
- Provide thread-safe message queuing

**Client Lifecycle:**
1. Connection established by AGWPEHandler
2. Welcome banner sent
3. Message history sent
4. Enter message loop (receive/send)
5. Handle disconnection
6. Cleanup resources

**Message Protocol:**
- Text-based line protocol
- Prompt format: `{SSID}> `
- Messages broadcast to all clients

**Thread Safety:**
- Each client runs in own thread
- Message queue for outbound messages
- Safe disconnection handling

**Location:** `src/ax25_client.py`

### 6. bbs_server.py (Main Server Logic)

**Purpose:** Orchestrate all components and manage client lifecycle.

**Responsibilities:**
- Initialize all components (config, message store, AGWPE handler)
- Manage collection of connected clients
- Broadcast messages to all clients
- Handle client connection/disconnection
- Coordinate server startup and shutdown

**Key Workflows:**

**Startup:**
1. Load configuration
2. Create MessageStore
3. Create and start AGWPEHandler
4. Register new client callback
5. Enter main loop

**New Client:**
1. AGWPEHandler accepts connection
2. Create AX25Client instance
3. Add to client collection
4. Send welcome banner and history
5. Start client message loop

**Message Broadcast:**
1. Client receives message from station
2. Add message to MessageStore
3. Broadcast to all connected clients
4. Log message

**Shutdown:**
1. Receive shutdown signal
2. Disconnect all clients gracefully
3. Stop AGWPEHandler
4. Cleanup resources

**Location:** `src/bbs_server.py`

### 7. exceptions.py (Custom Exceptions)

**Purpose:** Define custom exception types for clear error handling.

**Exception Types:**
- `ConfigurationError` - Invalid configuration
- `ConnectionError` - Direwolf connection issues
- `ProtocolError` - AGWPE protocol errors

**Location:** `src/exceptions.py`

## Design Principles

### 1. Separation of Concerns

Each component has a single, well-defined responsibility:
- Configuration → config.py
- Message storage → message_store.py
- AGWPE protocol → agwpe_handler.py
- Client handling → ax25_client.py
- Orchestration → bbs_server.py

### 2. Type Safety

- Full type hints throughout codebase
- Dataclasses for structured data
- mypy strict mode compliance
- Clear type contracts between components

### 3. Thread Safety

- Explicit locking for shared state
- Thread-safe message store
- Safe client collection management
- Documented thread-safety guarantees

### 4. Error Handling

- Custom exceptions with descriptive messages
- Graceful degradation where possible
- Comprehensive logging
- Clean resource cleanup

### 5. Testability

- Dependency injection
- Mock-friendly interfaces
- Comprehensive test coverage (>80%)
- Integration tests for full workflows

### 6. Documentation

- Docstrings for all public APIs
- Type hints as inline documentation
- Architecture documentation
- Code comments for complex logic

## Data Flow

### Incoming Message Flow

```
Radio → Direwolf → AGWPEHandler → AX25Client → BBSServer
                                                    ↓
                                               MessageStore
                                                    ↓
                                              Broadcast Loop
                                                    ↓
BBSServer → All AX25Clients → AGWPEHandler → Direwolf → Radio
```

### Connection Flow

```
Station sends connect request
            ↓
Direwolf receives request
            ↓
AGWPEHandler gets 'C' frame
            ↓
Create AX25Client instance
            ↓
BBSServer registers client
            ↓
AX25Client sends welcome banner
            ↓
AX25Client sends message history
            ↓
Client enters message loop
```

## Threading Model

Fox BBS uses multiple threads for concurrent operation:

### Main Thread
- Runs BBSServer main loop
- Handles startup and shutdown
- Coordinates component lifecycle

### AGWPE Handler Thread
- Listens for AGWPE frames
- Accepts incoming connections
- Creates new client instances

### Client Threads (one per client)
- Handle individual client I/O
- Receive messages from station
- Send messages to station
- Manage client state

### Synchronization
- MessageStore uses lock for thread-safe access
- Client collection uses lock for modifications
- No deadlock potential (no nested locks)

## Configuration System

Configuration flows through the system:

```
config/fox.yaml → ConfigLoader → ServerConfig → Components
```

Each component receives only the configuration it needs:
- AGWPEHandler gets connection settings
- MessageStore gets retention settings
- AX25Client gets display settings

## Error Handling Strategy

### Startup Errors
- Configuration validation fails → Raise ConfigurationError, exit
- Direwolf connection fails → Raise ConnectionError, exit
- Invalid settings → Descriptive error message, exit

### Runtime Errors
- Client disconnection → Log, remove client, continue
- Message parsing error → Log, skip message, continue
- Protocol error → Log, attempt recovery, continue

### Shutdown
- Graceful shutdown on SIGINT/SIGTERM
- Disconnect all clients with goodbye message
- Clean resource cleanup
- No data loss

## Performance Considerations

### Realistic Concurrency Expectations

**Expected load:** 1-5 concurrent clients (typical amateur radio use)
**Tested capacity:** 10 simultaneous clients
**Theoretical limit:** Limited by radio bandwidth, not software

**Why concurrency is low:**
- Amateur radio packet networks typically support 1-5 simultaneous connections
- Radio bandwidth is ~1200 baud (very limited)
- Channel capacity (not CPU) is the bottleneck
- Python GIL is not a concern at this scale

**Implications:**
- Thread safety is correct but possibly over-cautious
- No need to optimize for high concurrency
- Memory usage is negligible (< 100 messages in memory)
- CPU usage is minimal

### Memory
- Messages stored in deque with maxlen=15 (automatic memory management)
- Client collection: ~1KB per client
- Total memory: < 1MB for typical use
- Reasonable for expected load (< 10 concurrent clients)

### CPU
- Minimal processing per message
- No encryption or compression
- Efficient message broadcasting
- Low overhead protocol
- Bottleneck is radio bandwidth, not CPU

### Network
- Single TCP connection to Direwolf
- Low bandwidth per client
- Text-based protocol
- No special optimizations needed

## Extensibility

### Adding Features

**New configuration options:**
1. Add field to ServerConfig dataclass
2. Add validation in config.py
3. Update config/fox.yaml
4. Use in relevant component

**New AGWPE frame types:**
1. Add handler in agwpe_handler.py
2. Update frame type mapping
3. Add tests

**New message filters:**
1. Add method to MessageStore
2. Update get_recent_messages
3. Add tests

### Future Enhancements

Potential areas for extension:
- Message persistence (database)
- User authentication
- Message commands (/help, /users, etc.)
- File transfer support
- Logging to disk
- Statistics and monitoring
- Multiple BBS instances

## Security Considerations

### Amateur Radio Context
- Fox BBS operates in amateur radio context
- All transmissions are public
- No encryption (per FCC regulations)
- Callsigns are public identifiers

### Input Validation
- Configuration validated on startup
- SSID format validation
- Port range validation
- No SQL injection risk (no database)
- No XSS risk (no web interface)

### Resource Limits
- No explicit connection limits
- No message rate limiting
- Trust model: amateur radio operators
- Malicious users violate amateur radio regulations

## Testing Strategy

### Unit Tests
- Test each component in isolation
- Mock dependencies
- Test edge cases and error conditions
- Verify thread safety

### Integration Tests
- Test component interactions
- End-to-end message flow
- Startup and shutdown
- Error recovery

### Coverage Goals
- Maintain >80% code coverage
- 100% coverage for critical paths
- Test all error conditions
- Test concurrent operations

## Dependencies

### Production Dependencies
- **PyYAML** - Configuration file parsing
- **pyham-pe** - AGWPE protocol implementation

### Development Dependencies
- **pytest** - Testing framework
- **black** - Code formatter
- **mypy** - Type checker
- **flake8** - Linter
- **coverage** - Code coverage

### Rationale
- Minimal dependencies reduce complexity
- Well-maintained, stable libraries
- Type-safe interfaces
- Strong testing tools

## References

- [AGWPE Protocol Specification](http://www.elcom.gr/developer/agwpe.htm)
- [AX.25 Protocol](https://www.tapr.org/pdf/AX25.2.2.pdf)
- [Direwolf TNC](https://github.com/wb2osz/direwolf)
- [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)
