"""Pytest configuration and fixtures for Fox BBS tests."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from threading import Event
from unittest.mock import MagicMock, Mock

import pytest
import yaml

# ============================================================================
# Configuration Fixtures
# ============================================================================


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    config_data = {
        "server": {
            "ssid": "W1ABC-1",
            "direwolf_host": "localhost",
            "direwolf_port": 8000,
            "radio_port": 0,
            "max_messages": 15,
            "message_retention_hours": 24,
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def invalid_config_file():
    """Create an invalid YAML config file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("invalid: yaml: content: [")
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def minimal_config_file():
    """Create a minimal config file with only required fields."""
    config_data = {"server": {"ssid": "MIN-1"}}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


# ============================================================================
# AGWPE Mock Fixtures
# ============================================================================


@pytest.fixture
def mock_packet_engine():
    """Create a mock PacketEngine for testing."""
    mock_engine = MagicMock()
    mock_engine.connected_to_server = True
    mock_engine.connect_to_server = Mock()
    mock_engine.disconnect_from_server = Mock()
    mock_engine.register_callsign = Mock()
    mock_engine.unregister_callsign = Mock()
    mock_engine.send_data = Mock(return_value=True)
    mock_engine.disconnect = Mock()
    return mock_engine


@pytest.fixture
def mock_receive_handler():
    """Create a mock ReceiveHandler for testing."""
    return MagicMock()


@pytest.fixture
def mock_agwpe_handler(mock_packet_engine):
    """Create a mock AGWPEHandler for testing."""
    from src.agwpe_handler import AGWPEHandler

    handler = Mock(spec=AGWPEHandler)
    handler.host = "localhost"
    handler.port = 8000
    handler.radio_port = 0
    handler.mycall = "TEST-1"
    handler.engine = mock_packet_engine
    handler.running = True
    handler.connections = {}
    handler.send_data = Mock(return_value=True)
    handler.disconnect_client = Mock()
    handler.start = Mock()
    handler.stop = Mock()

    return handler


# ============================================================================
# Message Fixtures
# ============================================================================


@pytest.fixture
def sample_message():
    """Create a sample message for testing."""
    from src.message_store import Message

    return Message(
        callsign="W1ABC", text="This is a test message", timestamp=datetime(2025, 11, 13, 12, 0, 0)
    )


@pytest.fixture
def sample_messages():
    """Create a list of sample messages for testing."""
    from src.message_store import Message

    base_time = datetime(2025, 11, 13, 12, 0, 0)
    messages = []

    for i in range(20):
        msg = Message(
            callsign=f"W{i}ABC",
            text=f"Test message {i}",
            timestamp=base_time + timedelta(minutes=i),
        )
        messages.append(msg)

    return messages


@pytest.fixture
def old_message():
    """Create an old message that should be expired."""
    from src.message_store import Message

    old_timestamp = datetime.now() - timedelta(hours=48)
    return Message(callsign="W1OLD", text="This is an old message", timestamp=old_timestamp)


@pytest.fixture
def recent_message():
    """Create a recent message."""
    from src.message_store import Message

    recent_timestamp = datetime.now() - timedelta(minutes=5)
    return Message(callsign="W1NEW", text="This is a recent message", timestamp=recent_timestamp)


# ============================================================================
# Client Fixtures
# ============================================================================


@pytest.fixture
def mock_client_callback():
    """Create mock callbacks for AX25Client."""
    return {"on_message": Mock(), "on_disconnect": Mock()}


@pytest.fixture
def sample_client(mock_agwpe_handler, mock_client_callback):
    """Create a sample AX25Client for testing."""
    from src.ax25_client import AX25Client

    return AX25Client(
        callsign="W1TEST",
        ssid="FOX-1",
        agwpe_handler=mock_agwpe_handler,
        on_message=mock_client_callback["on_message"],
        on_disconnect=mock_client_callback["on_disconnect"],
    )


# ============================================================================
# MessageStore Fixtures
# ============================================================================


@pytest.fixture
def message_store():
    """Create a MessageStore instance for testing."""
    from src.message_store import MessageStore

    return MessageStore(max_messages=15, retention_hours=24)


@pytest.fixture
def populated_message_store(message_store, sample_messages):
    """Create a MessageStore populated with sample messages."""
    for msg in sample_messages:
        message_store._messages.append(msg)
    return message_store


# ============================================================================
# Server Fixtures
# ============================================================================


@pytest.fixture
def mock_config():
    """Create a mock Config object for testing."""
    config = Mock()
    config.ssid = "W1ABC-1"
    config.direwolf_host = "localhost"
    config.direwolf_port = 8000
    config.radio_port = 0
    config.max_messages = 15
    config.message_retention_hours = 24
    return config


@pytest.fixture
def bbs_server(mock_config):
    """Create a BBSServer instance for testing."""
    from src.bbs_server import BBSServer

    return BBSServer(mock_config)


# ============================================================================
# Threading Fixtures
# ============================================================================


@pytest.fixture
def sync_event():
    """Create a threading Event for synchronization in tests."""
    return Event()


# ============================================================================
# Utility Fixtures
# ============================================================================


@pytest.fixture
def capture_logs(caplog):
    """Fixture to capture logs with DEBUG level."""
    import logging

    caplog.set_level(logging.DEBUG)
    return caplog
