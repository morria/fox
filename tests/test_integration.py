"""Integration tests for Fox BBS.

These tests verify that all components work together correctly.
"""

import time
from threading import Thread
from unittest.mock import MagicMock, Mock, patch

from src.bbs_server import BBSServer
from src.config import Config


class TestEndToEndFlow:
    """Test complete end-to-end flows."""

    @patch("src.bbs_server.AGWPEHandler")
    def test_client_connect_and_chat(self, mock_agwpe_class, temp_config_file):
        """Test a complete client connection and chat session."""
        # Setup
        mock_handler = MagicMock()
        mock_agwpe_class.return_value = mock_handler

        config = Config(temp_config_file)
        server = BBSServer(config)

        # Start server in thread
        server_thread = Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(0.1)

        # Simulate client connection
        server._handle_connect_request("W1ABC")

        # Verify client was created
        assert "W1ABC" in server.clients
        client = server.clients["W1ABC"]

        # Simulate client sending a message
        client.handle_data(b"Hello from W1ABC\n")

        # Give time for processing
        time.sleep(0.05)

        # Verify message was stored
        messages = server.message_store.get_recent_messages()
        assert len(messages) == 1
        assert messages[0].callsign == "W1ABC"
        assert messages[0].text == "Hello from W1ABC"

        # Cleanup
        server.stop()
        server_thread.join(timeout=1)

    @patch("src.bbs_server.AGWPEHandler")
    def test_multiple_clients_chatting(self, mock_agwpe_class, temp_config_file):
        """Test multiple clients connecting and chatting."""
        # Setup
        mock_handler = MagicMock()
        mock_agwpe_class.return_value = mock_handler

        config = Config(temp_config_file)
        server = BBSServer(config)

        # Start server
        server_thread = Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(0.1)

        # Connect three clients
        server._handle_connect_request("W1ABC")
        server._handle_connect_request("W2DEF")
        server._handle_connect_request("W3GHI")

        assert len(server.clients) == 3

        # Each client sends a message
        server.clients["W1ABC"].handle_data(b"Message from ABC\n")
        time.sleep(0.05)
        server.clients["W2DEF"].handle_data(b"Message from DEF\n")
        time.sleep(0.05)
        server.clients["W3GHI"].handle_data(b"Message from GHI\n")
        time.sleep(0.05)

        # Verify all messages stored
        messages = server.message_store.get_recent_messages()
        assert len(messages) == 3

        # Cleanup
        server.stop()
        server_thread.join(timeout=1)

    @patch("src.bbs_server.AGWPEHandler")
    def test_client_sees_history_on_connect(self, mock_agwpe_class, temp_config_file):
        """Test that new clients receive message history."""
        # Setup
        mock_handler = MagicMock()
        mock_agwpe_class.return_value = mock_handler

        config = Config(temp_config_file)
        server = BBSServer(config)

        # Add some messages to history
        server.message_store.add_message("W1OLD", "Old message 1")
        server.message_store.add_message("W2OLD", "Old message 2")

        # Start server
        server_thread = Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(0.1)

        # Connect new client
        with patch("src.bbs_server.AX25Client") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client

            server._handle_connect_request("W3NEW")

            # Verify history was sent
            assert mock_client.send_message.called
            calls = [str(c) for c in mock_client.send_message.call_args_list]
            combined = " ".join(calls)
            assert "Recent messages" in combined
            assert "Old message 1" in combined
            assert "Old message 2" in combined

        # Cleanup
        server.stop()
        server_thread.join(timeout=1)

    @patch("src.bbs_server.AGWPEHandler")
    def test_message_broadcast_to_all(self, mock_agwpe_class, temp_config_file):
        """Test that messages are broadcast to all connected clients."""
        # Setup
        mock_handler = MagicMock()
        mock_agwpe_class.return_value = mock_handler

        config = Config(temp_config_file)
        server = BBSServer(config)

        # Start server
        server_thread = Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(0.1)

        # Connect clients
        server._handle_connect_request("W1ABC")
        server._handle_connect_request("W2DEF")
        server._handle_connect_request("W3GHI")

        # Reset mock calls from connection
        for client in server.clients.values():
            client.send_message.reset_mock()
            client.send_prompt.reset_mock()

        # One client sends a message
        server._handle_client_message("W1ABC", "Broadcast test")

        # All clients should receive the broadcast
        for callsign, client in server.clients.items():
            assert client.send_message.called
            assert client.send_prompt.called

        # Cleanup
        server.stop()
        server_thread.join(timeout=1)


class TestConfigurationIntegration:
    """Test that configuration correctly affects server behavior."""

    @patch("src.bbs_server.AGWPEHandler")
    def test_config_ssid_used(self, mock_agwpe_class, temp_config_file):
        """Test that configured SSID is used throughout."""
        mock_handler = MagicMock()
        mock_agwpe_class.return_value = mock_handler

        config = Config(temp_config_file)
        assert config.ssid == "TEST-1"

        server = BBSServer(config)

        # Start server
        server_thread = Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(0.1)

        # Verify AGWPE handler was created with correct SSID
        call_kwargs = mock_agwpe_class.call_args[1]
        assert call_kwargs["mycall"] == "TEST-1"

        # Connect a client
        server._handle_connect_request("W1ABC")
        client = server.clients["W1ABC"]
        assert client.ssid == "TEST-1"

        # Cleanup
        server.stop()
        server_thread.join(timeout=1)

    @patch("src.bbs_server.AGWPEHandler")
    def test_config_max_messages(self, mock_agwpe_class, temp_config_file):
        """Test that max_messages config is respected."""
        mock_handler = MagicMock()
        mock_agwpe_class.return_value = mock_handler

        config = Config(temp_config_file)
        server = BBSServer(config)

        # Add more messages than max
        for i in range(30):
            server.message_store.add_message(f"W{i}ABC", f"Message {i}")

        # Get recent messages
        recent = server.message_store.get_recent_messages()

        # Should only get max_messages (15 from config)
        assert len(recent) <= config.max_messages

    @patch("src.bbs_server.AGWPEHandler")
    def test_config_direwolf_connection(self, mock_agwpe_class, temp_config_file):
        """Test that Direwolf connection uses config values."""
        mock_handler = MagicMock()
        mock_agwpe_class.return_value = mock_handler

        config = Config(temp_config_file)
        server = BBSServer(config)

        # Start server
        server_thread = Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(0.1)

        # Verify handler created with correct connection params
        call_kwargs = mock_agwpe_class.call_args[1]
        assert call_kwargs["host"] == config.direwolf_host
        assert call_kwargs["port"] == config.direwolf_port
        assert call_kwargs["radio_port"] == config.radio_port

        # Cleanup
        server.stop()
        server_thread.join(timeout=1)


class TestErrorHandling:
    """Test error handling across components."""

    @patch("src.bbs_server.AGWPEHandler")
    def test_client_disconnect_during_message(self, mock_agwpe_class, temp_config_file):
        """Test handling client disconnect during message processing."""
        mock_handler = MagicMock()
        mock_agwpe_class.return_value = mock_handler

        config = Config(temp_config_file)
        server = BBSServer(config)

        # Start server
        server_thread = Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(0.1)

        # Connect clients
        server._handle_connect_request("W1ABC")
        server._handle_connect_request("W2DEF")

        # Disconnect one client
        server._handle_disconnect("W1ABC")
        assert "W1ABC" not in server.clients

        # Other client sends message (should not crash)
        server._handle_client_message("W2DEF", "Test message")

        # Message should be stored
        messages = server.message_store.get_recent_messages()
        assert len(messages) == 1

        # Cleanup
        server.stop()
        server_thread.join(timeout=1)

    @patch("src.bbs_server.AGWPEHandler")
    def test_invalid_data_handling(self, mock_agwpe_class, temp_config_file):
        """Test handling of invalid/malformed data."""
        mock_handler = MagicMock()
        mock_agwpe_class.return_value = mock_handler

        config = Config(temp_config_file)
        server = BBSServer(config)

        # Start server
        server_thread = Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(0.1)

        # Connect client
        server._handle_connect_request("W1ABC")
        client = server.clients["W1ABC"]

        # Send various malformed data (should not crash)
        client.handle_data(b"")
        client.handle_data(b"\x00\x00\x00")
        client.handle_data(b"\xff\xfe\xfd")
        client.handle_data(b"\n\n\n\n\n")

        # Should still be connected
        assert "W1ABC" in server.clients

        # Cleanup
        server.stop()
        server_thread.join(timeout=1)


class TestConcurrency:
    """Test concurrent operations across the system."""

    @patch("src.bbs_server.AGWPEHandler")
    def test_concurrent_clients_and_messages(self, mock_agwpe_class, temp_config_file):
        """Test many clients connecting and sending messages concurrently."""
        mock_handler = MagicMock()
        mock_agwpe_class.return_value = mock_handler

        config = Config(temp_config_file)
        server = BBSServer(config)

        # Start server
        server_thread = Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(0.1)

        # Connect many clients concurrently
        def connect_and_send(i):
            callsign = f"W{i}ABC"
            server._handle_connect_request(callsign)
            time.sleep(0.01)
            if callsign in server.clients:
                for j in range(5):
                    server._handle_client_message(callsign, f"Message {j} from {callsign}")
                    time.sleep(0.01)

        threads = []
        for i in range(10):
            t = Thread(target=connect_and_send, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Verify results
        assert len(server.clients) == 10
        # Should have 50 messages (10 clients * 5 messages each)
        messages = server.message_store._messages
        assert len(messages) == 50

        # Cleanup
        server.stop()
        server_thread.join(timeout=1)

    @patch("src.bbs_server.AGWPEHandler")
    def test_concurrent_connect_disconnect(self, mock_agwpe_class, temp_config_file):
        """Test concurrent connections and disconnections."""
        mock_handler = MagicMock()
        mock_agwpe_class.return_value = mock_handler

        config = Config(temp_config_file)
        server = BBSServer(config)

        # Start server
        server_thread = Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(0.1)

        # Connect and disconnect clients concurrently
        def connect_disconnect(i):
            callsign = f"W{i}ABC"
            server._handle_connect_request(callsign)
            time.sleep(0.05)
            server._handle_disconnect(callsign)

        threads = []
        for i in range(20):
            t = Thread(target=connect_disconnect, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All clients should be disconnected
        assert len(server.clients) == 0

        # Cleanup
        server.stop()
        server_thread.join(timeout=1)


class TestRealWorldScenarios:
    """Test realistic usage scenarios."""

    @patch("src.bbs_server.AGWPEHandler")
    def test_fox_hunt_scenario(self, mock_agwpe_class, temp_config_file):
        """Simulate a fox hunt with multiple hunters checking in."""
        mock_handler = MagicMock()
        mock_agwpe_class.return_value = mock_handler

        config = Config(temp_config_file)
        server = BBSServer(config)

        # Start server
        server_thread = Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(0.1)

        # Base station connects
        server._handle_connect_request("W1BASE")
        server._handle_client_message("W1BASE", "Fox hunt starting at 14:00")
        time.sleep(0.05)

        # Hunters join
        hunters = ["W2HUNT", "W3HUNT", "W4HUNT"]
        for hunter in hunters:
            server._handle_connect_request(hunter)
            time.sleep(0.05)

        # Hunters send status updates
        server._handle_client_message("W2HUNT", "On location, searching")
        time.sleep(0.05)
        server._handle_client_message("W3HUNT", "Signal detected on 146.520")
        time.sleep(0.05)
        server._handle_client_message("W4HUNT", "Found it! Near the oak tree")
        time.sleep(0.05)

        # Verify all messages stored
        messages = server.message_store.get_recent_messages()
        assert len(messages) == 4
        assert any("Fox hunt starting" in m.text for m in messages)
        assert any("Found it" in m.text for m in messages)

        # Cleanup
        server.stop()
        server_thread.join(timeout=1)

    @patch("src.bbs_server.AGWPEHandler")
    def test_long_running_session(self, mock_agwpe_class, temp_config_file):
        """Simulate a longer running session with clients coming and going."""
        mock_handler = MagicMock()
        mock_agwpe_class.return_value = mock_handler

        config = Config(temp_config_file)
        server = BBSServer(config)

        # Start server
        server_thread = Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()
        time.sleep(0.1)

        # First wave of clients
        server._handle_connect_request("W1ABC")
        server._handle_connect_request("W2DEF")
        server._handle_client_message("W1ABC", "Hello everyone")
        server._handle_client_message("W2DEF", "Good morning")

        # First client leaves
        server._handle_disconnect("W1ABC")

        # New clients join
        server._handle_connect_request("W3GHI")
        server._handle_connect_request("W4JKL")

        # More messages
        server._handle_client_message("W2DEF", "Welcome to the new folks")
        server._handle_client_message("W3GHI", "Thanks!")

        # Verify state
        assert "W1ABC" not in server.clients
        assert "W2DEF" in server.clients
        assert "W3GHI" in server.clients
        assert "W4JKL" in server.clients

        messages = server.message_store.get_recent_messages()
        assert len(messages) == 4

        # Cleanup
        server.stop()
        server_thread.join(timeout=1)
