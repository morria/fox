"""Tests for BBS server (src/bbs_server.py)."""

import time
from datetime import datetime
from threading import Thread
from unittest.mock import MagicMock, Mock, patch

from src.bbs_server import BBSServer
from src.message_store import Message


class TestBBSServerCreation:
    """Test BBSServer initialization."""

    def test_create_server(self, mock_config):
        """Test creating a BBSServer."""
        server = BBSServer(mock_config)

        assert server.config == mock_config
        assert server.message_store is not None
        assert server.message_store.max_messages == 15
        assert len(server.clients) == 0
        assert server.running is False
        assert server.agwpe_handler is None

    def test_server_initial_state(self, bbs_server):
        """Test server initial state."""
        assert bbs_server.running is False
        assert len(bbs_server.clients) == 0
        assert bbs_server.message_store is not None


class TestBBSServerStartStop:
    """Test starting and stopping the server."""

    @patch("src.bbs_server.AGWPEHandler")
    def test_start_server(self, mock_agwpe_class, mock_config):
        """Test starting the server."""
        # Setup mock
        mock_handler = MagicMock()
        mock_agwpe_class.return_value = mock_handler

        server = BBSServer(mock_config)

        # Start in a thread (since it blocks)
        start_thread = Thread(target=server.start)
        start_thread.daemon = True
        start_thread.start()

        # Give it time to start
        time.sleep(0.1)

        # Verify
        assert server.running is True
        assert server.agwpe_handler is not None
        mock_handler.start.assert_called_once()

        # Stop
        server.stop()
        start_thread.join(timeout=1)

    @patch("src.bbs_server.AGWPEHandler")
    def test_start_server_creates_agwpe_handler(self, mock_agwpe_class, mock_config):
        """Test that starting creates AGWPE handler with correct params."""
        mock_handler = MagicMock()
        mock_agwpe_class.return_value = mock_handler

        server = BBSServer(mock_config)

        # Start in thread
        start_thread = Thread(target=server.start)
        start_thread.daemon = True
        start_thread.start()
        time.sleep(0.1)

        # Verify handler creation
        mock_agwpe_class.assert_called_once()
        call_kwargs = mock_agwpe_class.call_args[1]
        assert call_kwargs["host"] == "localhost"
        assert call_kwargs["port"] == 8000
        assert call_kwargs["radio_port"] == 0
        assert call_kwargs["mycall"] == "W1ABC-1"

        server.stop()
        start_thread.join(timeout=1)

    def test_stop_server(self, bbs_server):
        """Test stopping the server."""
        # Setup mock handler
        mock_handler = MagicMock()
        bbs_server.agwpe_handler = mock_handler
        bbs_server.running = True

        # Add some mock clients
        client1 = Mock()
        client2 = Mock()
        bbs_server.clients["W1ABC"] = client1
        bbs_server.clients["W2DEF"] = client2

        bbs_server.stop()

        # Verify cleanup
        assert bbs_server.running is False
        client1.disconnect.assert_called_once()
        client2.disconnect.assert_called_once()
        assert len(bbs_server.clients) == 0
        mock_handler.stop.assert_called_once()

    def test_stop_server_handles_client_errors(self, bbs_server, capture_logs):
        """Test that stop handles errors when disconnecting clients."""
        mock_handler = MagicMock()
        bbs_server.agwpe_handler = mock_handler
        bbs_server.running = True

        # Add client that raises on disconnect
        client = Mock()
        client.disconnect.side_effect = Exception("Disconnect error")
        bbs_server.clients["W1ABC"] = client

        # Should not raise
        bbs_server.stop()

        assert "Error disconnecting" in capture_logs.text
        assert len(bbs_server.clients) == 0


class TestConnectionHandling:
    """Test handling client connections."""

    def test_handle_connect_request(self, bbs_server):
        """Test handling a connection request."""
        # Setup mock AGWPE handler
        mock_handler = MagicMock()
        bbs_server.agwpe_handler = mock_handler

        bbs_server._handle_connect_request("W1ABC")

        # Client should be created and added
        assert "W1ABC" in bbs_server.clients
        client = bbs_server.clients["W1ABC"]
        assert client.callsign == "W1ABC"
        assert client.active is True

    def test_connect_sends_welcome(self, bbs_server):
        """Test that connecting sends welcome banner."""
        mock_handler = MagicMock()
        bbs_server.agwpe_handler = mock_handler

        with patch("src.bbs_server.AX25Client") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            bbs_server._handle_connect_request("W1ABC")

            mock_client.send_welcome.assert_called_once()

    def test_connect_sends_prompt(self, bbs_server):
        """Test that connecting sends initial prompt."""
        mock_handler = MagicMock()
        bbs_server.agwpe_handler = mock_handler

        with patch("src.bbs_server.AX25Client") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            bbs_server._handle_connect_request("W1ABC")

            mock_client.send_prompt.assert_called_once()

    def test_connect_sends_history(self, bbs_server, sample_messages):
        """Test that connecting sends message history."""
        mock_handler = MagicMock()
        bbs_server.agwpe_handler = mock_handler

        # Add some messages
        for msg in sample_messages[:5]:
            bbs_server.message_store._messages.append(msg)

        with patch("src.bbs_server.AX25Client") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            bbs_server._handle_connect_request("W1ABC")

            # Should send history
            assert mock_client.send_message.called
            # Check for history separator
            calls = mock_client.send_message.call_args_list
            assert any("---" in str(c) for c in calls)

    def test_connect_with_empty_history(self, bbs_server):
        """Test connecting when there's no message history."""
        mock_handler = MagicMock()
        bbs_server.agwpe_handler = mock_handler

        with patch("src.bbs_server.AX25Client") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            bbs_server._handle_connect_request("W1ABC")

            # Welcome and prompt should be sent, but no history
            mock_client.send_welcome.assert_called_once()
            mock_client.send_prompt.assert_called_once()


class TestDataHandling:
    """Test handling data from clients."""

    def test_handle_data(self, bbs_server):
        """Test handling data from a client."""
        # Add a mock client
        mock_client = Mock()
        bbs_server.clients["W1ABC"] = mock_client

        data = b"Hello World"
        bbs_server._handle_data("W1ABC", data)

        # Should pass data to client
        mock_client.handle_data.assert_called_once_with(data)

    def test_handle_data_unknown_client(self, bbs_server, capture_logs):
        """Test handling data from unknown client."""
        data = b"Hello"
        bbs_server._handle_data("W1UNKNOWN", data)

        # Should log warning
        assert "unknown client" in capture_logs.text.lower()

    def test_handle_client_message(self, bbs_server):
        """Test handling a message from a client."""
        # Add mock clients
        client1 = Mock()
        client1.active = True
        client2 = Mock()
        client2.active = True
        bbs_server.clients["W1ABC"] = client1
        bbs_server.clients["W2DEF"] = client2

        # Handle message
        bbs_server._handle_client_message("W1ABC", "Test message")

        # Message should be stored
        messages = bbs_server.message_store.get_recent_messages()
        assert len(messages) == 1
        assert messages[0].callsign == "W1ABC"
        assert messages[0].text == "Test message"

        # Message should be broadcast to all clients
        assert client1.send_message.called
        assert client2.send_message.called


class TestDisconnectionHandling:
    """Test handling client disconnections."""

    def test_handle_disconnect(self, bbs_server):
        """Test handling client disconnection."""
        # Add a mock client
        mock_client = Mock()
        bbs_server.clients["W1ABC"] = mock_client

        bbs_server._handle_disconnect("W1ABC")

        # Client should be cleaned up and removed
        mock_client.cleanup.assert_called_once()
        assert "W1ABC" not in bbs_server.clients

    def test_handle_disconnect_unknown_client(self, bbs_server):
        """Test handling disconnect for unknown client."""
        # Should not raise
        bbs_server._handle_disconnect("W1UNKNOWN")

    def test_handle_client_disconnect_callback(self, bbs_server):
        """Test client disconnect callback."""
        # Add a mock client
        mock_client = Mock()
        mock_client.callsign = "W1ABC"
        bbs_server.clients["W1ABC"] = mock_client

        bbs_server._handle_client_disconnect(mock_client)

        # Client should be removed
        assert "W1ABC" not in bbs_server.clients

    def test_handle_client_disconnect_already_removed(self, bbs_server):
        """Test client disconnect callback when already removed."""
        mock_client = Mock()
        mock_client.callsign = "W1ABC"

        # Should not raise
        bbs_server._handle_client_disconnect(mock_client)


class TestMessageBroadcasting:
    """Test message broadcasting."""

    def test_broadcast_message(self, bbs_server):
        """Test broadcasting a message to all clients."""
        # Add mock clients
        client1 = Mock()
        client1.active = True
        client2 = Mock()
        client2.active = True
        client3 = Mock()
        client3.active = True

        bbs_server.clients["W1ABC"] = client1
        bbs_server.clients["W2DEF"] = client2
        bbs_server.clients["W3GHI"] = client3

        # Create and broadcast message
        msg = Message("W1ABC", "Test broadcast")
        bbs_server._broadcast_message(msg)

        # All clients should receive message and prompt
        assert client1.send_message.called
        assert client1.send_prompt.called
        assert client2.send_message.called
        assert client2.send_prompt.called
        assert client3.send_message.called
        assert client3.send_prompt.called

    def test_broadcast_only_to_active_clients(self, bbs_server):
        """Test that broadcast only sends to active clients."""
        # Add mock clients
        client1 = Mock()
        client1.active = True
        client2 = Mock()
        client2.active = False  # Inactive
        client3 = Mock()
        client3.active = True

        bbs_server.clients["W1ABC"] = client1
        bbs_server.clients["W2DEF"] = client2
        bbs_server.clients["W3GHI"] = client3

        # Broadcast message
        msg = Message("W1ABC", "Test")
        bbs_server._broadcast_message(msg)

        # Active clients should receive
        assert client1.send_message.called
        assert client3.send_message.called

        # Inactive client should not receive
        assert not client2.send_message.called

    def test_broadcast_message_formatting(self, bbs_server):
        """Test that broadcast message is formatted correctly."""
        client = Mock()
        client.active = True
        bbs_server.clients["W1ABC"] = client

        msg = Message("W2DEF", "Hello World", datetime(2025, 11, 13, 14, 30, 0))
        bbs_server._broadcast_message(msg)

        # Check formatting
        call_args = client.send_message.call_args[0][0]
        assert "\r\n" in call_args
        assert "W2DEF" in call_args
        assert "Hello World" in call_args


class TestMessageHistory:
    """Test message history handling."""

    def test_send_history_to_client(self, bbs_server, sample_messages):
        """Test sending message history to a client."""
        # Add messages
        for msg in sample_messages[:10]:
            bbs_server.message_store._messages.append(msg)

        # Create mock client
        mock_client = Mock()

        bbs_server._send_history_to_client(mock_client)

        # Should send history with separator
        assert mock_client.send_message.called
        calls = [str(c) for c in mock_client.send_message.call_args_list]
        combined = " ".join(calls)
        assert "---" in combined
        # Verify messages are present
        assert "Test message" in combined

    def test_send_empty_history(self, bbs_server):
        """Test sending history when there are no messages."""
        mock_client = Mock()

        bbs_server._send_history_to_client(mock_client)

        # Should not send anything
        mock_client.send_message.assert_not_called()


class TestThreadSafety:
    """Test thread safety of BBS server."""

    def test_concurrent_client_connections(self, bbs_server):
        """Test concurrent client connections."""
        mock_handler = MagicMock()
        bbs_server.agwpe_handler = mock_handler

        def connect_client(callsign):
            bbs_server._handle_connect_request(callsign)

        # Create multiple threads connecting simultaneously
        threads = []
        for i in range(10):
            t = Thread(target=connect_client, args=(f"W{i}ABC",))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All clients should be added
        assert len(bbs_server.clients) == 10

    def test_concurrent_message_handling(self, bbs_server):
        """Test concurrent message handling."""
        # Add mock clients
        for i in range(5):
            client = Mock()
            client.active = True
            bbs_server.clients[f"W{i}ABC"] = client

        def send_message(callsign, text):
            bbs_server._handle_client_message(callsign, text)

        # Send messages from multiple threads
        threads = []
        for i in range(5):
            for j in range(10):
                t = Thread(target=send_message, args=(f"W{i}ABC", f"Message {j}"))
                threads.append(t)
                t.start()

        for t in threads:
            t.join()

        # Should have last 15 messages (deque maxlen is 15)
        messages = bbs_server.message_store._messages
        assert len(messages) == 15

    def test_concurrent_disconnect(self, bbs_server):
        """Test concurrent client disconnections."""
        # Add clients
        for i in range(10):
            client = Mock()
            bbs_server.clients[f"W{i}ABC"] = client

        def disconnect_client(callsign):
            bbs_server._handle_disconnect(callsign)

        # Disconnect from multiple threads
        threads = []
        for i in range(10):
            t = Thread(target=disconnect_client, args=(f"W{i}ABC",))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All clients should be removed
        assert len(bbs_server.clients) == 0


class TestEdgeCases:
    """Test edge cases."""

    def test_multiple_messages_from_same_client(self, bbs_server):
        """Test handling multiple messages from the same client."""
        # Add mock clients
        client = Mock()
        client.active = True
        bbs_server.clients["W1ABC"] = client

        # Send multiple messages
        for i in range(10):
            bbs_server._handle_client_message("W1ABC", f"Message {i}")

        # All messages should be stored
        messages = bbs_server.message_store.get_recent_messages()
        assert len(messages) == 10

    def test_broadcast_with_no_clients(self, bbs_server):
        """Test broadcasting when there are no clients."""
        msg = Message("W1ABC", "Test")

        # Should not raise
        bbs_server._broadcast_message(msg)

    def test_client_list_modification_during_broadcast(self, bbs_server):
        """Test that client list can be safely modified during broadcast."""
        # Add clients
        for i in range(5):
            client = Mock()
            client.active = True
            bbs_server.clients[f"W{i}ABC"] = client

        # Broadcast (uses list() to avoid modification during iteration)
        msg = Message("W1ABC", "Test")
        bbs_server._broadcast_message(msg)

        # Should complete without errors
        assert True

    def test_server_stop_during_start(self, mock_config):
        """Test stopping server during startup."""
        with patch("src.bbs_server.AGWPEHandler") as mock_agwpe_class:
            mock_handler = MagicMock()
            mock_agwpe_class.return_value = mock_handler

            server = BBSServer(mock_config)

            # Start in thread
            start_thread = Thread(target=server.start)
            start_thread.daemon = True
            start_thread.start()

            # Immediately stop
            time.sleep(0.05)
            server.stop()

            start_thread.join(timeout=1)

            assert server.running is False
