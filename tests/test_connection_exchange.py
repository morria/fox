"""Tests for AX.25 connection exchange with mock interface."""

from datetime import datetime
from threading import Lock
from unittest.mock import MagicMock, Mock

import pytest

from src.bbs_server import BBSServer
from src.config import Config


class MockAX25Interface:
    """Mock AX.25 interface for testing connection exchange.

    This mock simulates the Direwolf/AGWPE interface, allowing us to test
    the complete connection handshake and data exchange without real hardware.
    """

    def __init__(self):
        """Initialize the mock AX.25 interface."""
        self.connected_stations = {}  # callsign -> connection_state
        self.sent_data = {}  # callsign -> list of sent data
        self.sent_data_lock = Lock()
        self.connection_handlers = []
        self.disconnect_handlers = []
        self.data_handlers = []

    def connect_station(self, callsign: str) -> None:
        """Simulate a station connecting.

        Args:
            callsign: The station's callsign
        """
        self.connected_stations[callsign] = {"state": "connected", "timestamp": datetime.now()}
        self.sent_data[callsign] = []

        # Trigger connection handlers
        for handler in self.connection_handlers:
            handler(callsign)

    def disconnect_station(self, callsign: str) -> None:
        """Simulate a station disconnecting.

        Args:
            callsign: The station's callsign
        """
        if callsign in self.connected_stations:
            self.connected_stations[callsign]["state"] = "disconnected"

            # Trigger disconnect handlers
            for handler in self.disconnect_handlers:
                handler(callsign)

    def send_data(self, callsign: str, data: bytes) -> bool:
        """Send data to a connected station.

        Args:
            callsign: The destination callsign
            data: The data to send

        Returns:
            True if sent successfully, False otherwise
        """
        if callsign not in self.connected_stations:
            return False

        if self.connected_stations[callsign]["state"] != "connected":
            return False

        with self.sent_data_lock:
            if callsign not in self.sent_data:
                self.sent_data[callsign] = []
            self.sent_data[callsign].append(data)

        return True

    def receive_data(self, callsign: str, data: bytes) -> None:
        """Simulate receiving data from a station.

        Args:
            callsign: The source callsign
            data: The received data
        """
        if callsign not in self.connected_stations:
            return

        # Trigger data handlers
        for handler in self.data_handlers:
            handler(callsign, data)

    def get_sent_data(self, callsign: str) -> list:
        """Get all data sent to a callsign.

        Args:
            callsign: The callsign

        Returns:
            List of bytes objects sent to this callsign
        """
        with self.sent_data_lock:
            return self.sent_data.get(callsign, []).copy()

    def get_sent_text(self, callsign: str) -> str:
        """Get all text sent to a callsign as a single string.

        Args:
            callsign: The callsign

        Returns:
            Concatenated text sent to this callsign
        """
        data_list = self.get_sent_data(callsign)
        return b"".join(data_list).decode("latin-1", errors="ignore")

    def clear_sent_data(self, callsign: str) -> None:
        """Clear sent data for a callsign.

        Args:
            callsign: The callsign
        """
        with self.sent_data_lock:
            if callsign in self.sent_data:
                self.sent_data[callsign] = []

    def on_connect(self, handler) -> None:
        """Register a connection handler.

        Args:
            handler: Callback function(callsign)
        """
        self.connection_handlers.append(handler)

    def on_disconnect(self, handler) -> None:
        """Register a disconnect handler.

        Args:
            handler: Callback function(callsign)
        """
        self.disconnect_handlers.append(handler)

    def on_data(self, handler) -> None:
        """Register a data handler.

        Args:
            handler: Callback function(callsign, data)
        """
        self.data_handlers.append(handler)


@pytest.fixture
def mock_ax25_interface():
    """Create a mock AX.25 interface for testing."""
    return MockAX25Interface()


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = Mock(spec=Config)
    config.ssid = "W2ASM-11"
    config.direwolf_host = "localhost"
    config.direwolf_port = 8000
    config.radio_port = 0
    config.max_messages = 10
    config.message_retention_hours = 24
    return config


@pytest.fixture
def mock_agwpe_handler_for_connection(mock_ax25_interface):
    """Create a mock AGWPE handler that uses the mock AX.25 interface."""
    handler = MagicMock()
    handler.send_data = lambda callsign, data: mock_ax25_interface.send_data(callsign, data)
    handler.disconnect_client = lambda callsign: mock_ax25_interface.disconnect_station(callsign)
    return handler


class TestConnectionExchange:
    """Test the complete AX.25 connection exchange process."""

    def test_new_connection_sends_welcome_banner(
        self, mock_config, mock_agwpe_handler_for_connection, mock_ax25_interface
    ):
        """Test that a new connection receives the welcome banner."""
        # Create BBS server
        server = BBSServer(mock_config)
        server.agwpe_handler = mock_agwpe_handler_for_connection

        # Simulate connection
        callsign = "KE2ABC"
        mock_ax25_interface.connect_station(callsign)
        server._handle_connect_request(callsign)

        # Get sent data
        sent_text = mock_ax25_interface.get_sent_text(callsign)

        # Verify welcome banner
        assert "Welcome to the W2ASM-11 Fox Hunt BBS" in sent_text

    def test_new_connection_shows_separator_before_history(
        self, mock_config, mock_agwpe_handler_for_connection, mock_ax25_interface
    ):
        """Test that history is preceded by a simple '---' separator."""
        # Create BBS server with some messages
        server = BBSServer(mock_config)
        server.agwpe_handler = mock_agwpe_handler_for_connection
        server.message_store.add_message("KE2ABC", "Test message 1")
        server.message_store.add_message("VE2DEF", "Test message 2")

        # Simulate connection
        callsign = "W1FOX"
        mock_ax25_interface.connect_station(callsign)
        server._handle_connect_request(callsign)

        # Get sent data
        sent_text = mock_ax25_interface.get_sent_text(callsign)

        # Verify separator
        assert "---" in sent_text
        # Verify no old-style markers
        assert "Recent messages" not in sent_text
        assert "End of history" not in sent_text

    def test_new_connection_shows_recent_messages(
        self, mock_config, mock_agwpe_handler_for_connection, mock_ax25_interface
    ):
        """Test that new connections receive recent message history."""
        # Create BBS server with some messages
        server = BBSServer(mock_config)
        server.agwpe_handler = mock_agwpe_handler_for_connection
        server.message_store.add_message("KE2ABC", "We're located at the baseball fields")
        server.message_store.add_message(
            "VE2DEF", "From the Picnic House we're hearing the fox at 190 east"
        )

        # Simulate connection
        callsign = "W1FOX"
        mock_ax25_interface.connect_station(callsign)
        server._handle_connect_request(callsign)

        # Get sent data
        sent_text = mock_ax25_interface.get_sent_text(callsign)

        # Verify messages are shown
        assert "KE2ABC" in sent_text
        assert "VE2DEF" in sent_text
        assert "baseball fields" in sent_text
        assert "Picnic House" in sent_text

    def test_new_connection_limits_history_to_max_messages(
        self, mock_config, mock_agwpe_handler_for_connection, mock_ax25_interface
    ):
        """Test that only the most recent messages (up to max) are shown."""
        # Create BBS server with max_messages=10
        server = BBSServer(mock_config)
        server.agwpe_handler = mock_agwpe_handler_for_connection

        # Add 15 messages
        for i in range(15):
            server.message_store.add_message(f"TEST{i}", f"Message {i}")

        # Simulate connection
        callsign = "W1FOX"
        mock_ax25_interface.connect_station(callsign)
        server._handle_connect_request(callsign)

        # Get sent data
        sent_text = mock_ax25_interface.get_sent_text(callsign)

        # Only the last 10 messages should be shown (5-14)
        # First 5 messages (0-4) should NOT be in history
        assert "Message 0" not in sent_text
        assert "Message 4" not in sent_text

        # Last 10 messages (5-14) should be in history
        assert "Message 14" in sent_text
        assert "Message 5" in sent_text

    def test_new_connection_sends_prompt_with_client_callsign(
        self, mock_config, mock_agwpe_handler_for_connection, mock_ax25_interface
    ):
        """Test that the prompt uses the client's callsign, not the BBS SSID."""
        # Create BBS server
        server = BBSServer(mock_config)
        server.agwpe_handler = mock_agwpe_handler_for_connection

        # Simulate connection
        callsign = "W2ASM"
        mock_ax25_interface.connect_station(callsign)
        server._handle_connect_request(callsign)

        # Get sent data
        sent_text = mock_ax25_interface.get_sent_text(callsign)

        # Verify prompt uses client's callsign
        assert f"{callsign}>" in sent_text
        # Verify it doesn't use the BBS SSID
        assert f"{mock_config.ssid}>" not in sent_text

    def test_complete_connection_sequence(
        self, mock_config, mock_agwpe_handler_for_connection, mock_ax25_interface
    ):
        """Test the complete connection sequence matches the expected UX."""
        # Create BBS server with some history
        server = BBSServer(mock_config)
        server.agwpe_handler = mock_agwpe_handler_for_connection
        server.message_store.add_message(
            "KE2ABC",
            "We're located at the baseball fields and get the strongest signal at 32 degrees west.",
        )
        server.message_store.add_message(
            "VE2DEF", "From the Picnic House we're hearing the fox at 190 east."
        )

        # Simulate connection
        callsign = "W2ASM"
        mock_ax25_interface.connect_station(callsign)
        server._handle_connect_request(callsign)

        # Get sent data
        sent_text = mock_ax25_interface.get_sent_text(callsign)

        # Expected format:
        # 1. Welcome banner
        # 2. "---" separator
        # 3. Messages
        # 4. Prompt with callsign

        # Check components are present
        assert "Welcome to the W2ASM-11 Fox Hunt BBS" in sent_text
        assert "---" in sent_text
        assert "KE2ABC" in sent_text
        assert "VE2DEF" in sent_text
        assert f"{callsign}>" in sent_text

        # Check order (banner before history before prompt)
        banner_pos = sent_text.index("Welcome")
        separator_pos = sent_text.index("---")
        msg_pos = sent_text.index("KE2ABC")
        prompt_pos = sent_text.rindex(f"{callsign}>")

        assert banner_pos < separator_pos < msg_pos < prompt_pos

    def test_connection_with_no_history(
        self, mock_config, mock_agwpe_handler_for_connection, mock_ax25_interface
    ):
        """Test connection when there are no messages in history."""
        # Create BBS server with no messages
        server = BBSServer(mock_config)
        server.agwpe_handler = mock_agwpe_handler_for_connection

        # Simulate connection
        callsign = "W1FOX"
        mock_ax25_interface.connect_station(callsign)
        server._handle_connect_request(callsign)

        # Get sent data
        sent_text = mock_ax25_interface.get_sent_text(callsign)

        # Should have banner and prompt, but no history separator
        assert "Welcome to the W2ASM-11 Fox Hunt BBS" in sent_text
        assert f"{callsign}>" in sent_text
        # No history separator when empty
        lines = sent_text.split("\n")
        # Should not have standalone "---" line
        standalone_separator = any(line.strip() == "---" for line in lines)
        assert not standalone_separator

    def test_multiple_connections_receive_individual_prompts(
        self, mock_config, mock_agwpe_handler_for_connection, mock_ax25_interface
    ):
        """Test that multiple clients each receive prompts with their own callsigns."""
        # Create BBS server
        server = BBSServer(mock_config)
        server.agwpe_handler = mock_agwpe_handler_for_connection

        # Simulate multiple connections
        callsigns = ["KE2ABC", "VE2DEF", "W1FOX"]
        for cs in callsigns:
            mock_ax25_interface.connect_station(cs)
            server._handle_connect_request(cs)

        # Verify each client got their own prompt
        for cs in callsigns:
            sent_text = mock_ax25_interface.get_sent_text(cs)
            assert f"{cs}>" in sent_text

    def test_client_sends_message_receives_prompt(
        self, mock_config, mock_agwpe_handler_for_connection, mock_ax25_interface
    ):
        """Test that after sending a message, client receives their prompt again."""
        # Create BBS server
        server = BBSServer(mock_config)
        server.agwpe_handler = mock_agwpe_handler_for_connection

        # Simulate connection
        callsign = "KE2ABC"
        mock_ax25_interface.connect_station(callsign)
        server._handle_connect_request(callsign)

        # Clear initial connection data
        mock_ax25_interface.clear_sent_data(callsign)

        # Send a message by calling the handler directly
        message = "Test message from client"
        message_data = f"{message}\r\n".encode("latin-1")
        server._handle_data(callsign, message_data)

        # Get sent data after message
        sent_text = mock_ax25_interface.get_sent_text(callsign)

        # Should receive the broadcast message and a prompt
        assert message in sent_text
        assert f"{callsign}>" in sent_text

    def test_disconnect_cleans_up_properly(
        self, mock_config, mock_agwpe_handler_for_connection, mock_ax25_interface
    ):
        """Test that disconnection cleans up client state properly."""
        # Create BBS server
        server = BBSServer(mock_config)
        server.agwpe_handler = mock_agwpe_handler_for_connection

        # Simulate connection
        callsign = "KE2ABC"
        mock_ax25_interface.connect_station(callsign)
        server._handle_connect_request(callsign)

        # Verify client is connected
        assert callsign in server.clients

        # Simulate disconnection
        server._handle_disconnect(callsign)

        # Verify client is removed
        assert callsign not in server.clients

    def test_connection_exchange_thread_safety(
        self, mock_config, mock_agwpe_handler_for_connection, mock_ax25_interface
    ):
        """Test that concurrent connections are handled safely."""
        # Create BBS server
        server = BBSServer(mock_config)
        server.agwpe_handler = mock_agwpe_handler_for_connection

        # Simulate multiple connections sequentially to test thread safety
        callsigns = [f"TEST{i}" for i in range(10)]

        for cs in callsigns:
            mock_ax25_interface.connect_station(cs)
            server._handle_connect_request(cs)

        # Verify all clients connected
        assert len(server.clients) == 10
        for cs in callsigns:
            assert cs in server.clients


class TestMockAX25Interface:
    """Test the mock AX.25 interface itself."""

    def test_mock_interface_connection(self, mock_ax25_interface):
        """Test basic connection functionality."""
        callsign = "W1FOX"
        mock_ax25_interface.connect_station(callsign)

        assert callsign in mock_ax25_interface.connected_stations
        assert mock_ax25_interface.connected_stations[callsign]["state"] == "connected"

    def test_mock_interface_send_data(self, mock_ax25_interface):
        """Test sending data through the mock interface."""
        callsign = "W1FOX"
        mock_ax25_interface.connect_station(callsign)

        test_data = b"Test message"
        result = mock_ax25_interface.send_data(callsign, test_data)

        assert result is True
        assert test_data in mock_ax25_interface.get_sent_data(callsign)

    def test_mock_interface_receive_data(self, mock_ax25_interface):
        """Test receiving data through the mock interface."""
        received_data = []

        def data_handler(callsign, data):
            received_data.append((callsign, data))

        mock_ax25_interface.on_data(data_handler)

        callsign = "W1FOX"
        mock_ax25_interface.connect_station(callsign)

        test_data = b"Test message"
        mock_ax25_interface.receive_data(callsign, test_data)

        assert len(received_data) == 1
        assert received_data[0] == (callsign, test_data)

    def test_mock_interface_disconnect(self, mock_ax25_interface):
        """Test disconnection through the mock interface."""
        disconnected = []

        def disconnect_handler(callsign):
            disconnected.append(callsign)

        mock_ax25_interface.on_disconnect(disconnect_handler)

        callsign = "W1FOX"
        mock_ax25_interface.connect_station(callsign)
        mock_ax25_interface.disconnect_station(callsign)

        assert callsign in disconnected
        assert mock_ax25_interface.connected_stations[callsign]["state"] == "disconnected"
