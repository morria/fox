"""
Test compatibility with various AX.25 clients.

This module simulates different client behaviors to ensure Fox BBS
works reliably with various popular AX.25 clients including:
- ax25call (Linux)
- Packet Commander (Windows)
- Android AX.25 apps
- Legacy terminals
"""

from unittest.mock import Mock

from src.ax25_client import AX25Client


def create_test_client(callsign, on_message, track_sent_data=None):
    """Helper to create an AX25Client for testing.

    Args:
        callsign: Client callsign
        on_message: Message callback
        track_sent_data: Optional list to track sent data
    """
    mock_handler = Mock()

    if track_sent_data is not None:
        # Track sent data in the provided list
        def send_data_tracker(to_callsign, data):
            track_sent_data.append(data)
            return True

        mock_handler.send_data = send_data_tracker
    else:
        mock_handler.send_data = Mock(return_value=True)

    def on_disconnect(client):
        pass

    return AX25Client(
        callsign=callsign,
        ssid="TEST-1",
        agwpe_handler=mock_handler,
        on_message=on_message,
        on_disconnect=on_disconnect,
    )


class TestClientLineEndings:
    """Test handling of different line ending styles from various clients."""

    def test_ax25call_lf_only(self):
        """Test ax25call typical behavior (LF-only line endings)."""
        received = []

        def on_message(callsign: str, message: str) -> None:
            received.append(message)

        client = create_test_client(
            callsign="W1TEST",
            on_message=on_message,
        )

        # Simulate ax25call sending messages with LF only
        client.handle_data(b"Hello from ax25call\n")
        client.handle_data(b"Second message\n")
        client.handle_data(b"Third message\n")

        assert len(received) == 3
        assert received[0] == "Hello from ax25call"
        assert received[1] == "Second message"
        assert received[2] == "Third message"

    def test_packet_commander_crlf(self):
        """Test Packet Commander typical behavior (CRLF line endings)."""
        received = []

        def on_message(callsign: str, message: str) -> None:
            received.append(message)

        client = create_test_client(
            callsign="W2TEST",
            on_message=on_message,
        )

        # Simulate Packet Commander sending messages with CRLF
        client.handle_data(b"Hello from Packet Commander\r\n")
        client.handle_data(b"Windows style line endings\r\n")

        assert len(received) == 2
        assert received[0] == "Hello from Packet Commander"
        assert received[1] == "Windows style line endings"

    def test_legacy_terminal_cr_only(self):
        """Test legacy terminal behavior (CR-only line endings)."""
        received = []

        def on_message(callsign: str, message: str) -> None:
            received.append(message)

        client = create_test_client(
            callsign="W3TEST",
            on_message=on_message,
        )

        # Simulate legacy terminal sending messages with CR only
        client.handle_data(b"Hello from legacy terminal\r")
        client.handle_data(b"Old Mac style\r")

        assert len(received) == 2
        assert received[0] == "Hello from legacy terminal"
        assert received[1] == "Old Mac style"

    def test_mixed_line_endings_buggy_client(self):
        """Test handling of mixed line endings from buggy clients."""
        received = []

        def on_message(callsign: str, message: str) -> None:
            received.append(message)

        client = create_test_client(
            callsign="W4TEST",
            on_message=on_message,
        )

        # Simulate buggy client mixing different line endings
        client.handle_data(b"Message with CRLF\r\n")
        client.handle_data(b"Message with LF\n")
        client.handle_data(b"Message with CR\r")
        client.handle_data(b"Back to CRLF\r\n")

        assert len(received) == 4
        assert received[0] == "Message with CRLF"
        assert received[1] == "Message with LF"
        assert received[2] == "Message with CR"
        assert received[3] == "Back to CRLF"


class TestClientBuffering:
    """Test handling of different buffering behaviors from various clients."""

    def test_character_by_character_legacy_terminal(self):
        """Test legacy terminal sending one character at a time."""
        received = []

        def on_message(callsign: str, message: str) -> None:
            received.append(message)

        client = create_test_client(
            callsign="W5TEST",
            on_message=on_message,
        )

        # Simulate character-by-character transmission
        message = "Hello\n"
        for char in message:
            client.handle_data(char.encode("latin-1"))

        assert len(received) == 1
        assert received[0] == "Hello"

    def test_small_chunks_mobile_client(self):
        """Test mobile client sending data in small chunks."""
        received = []

        def on_message(callsign: str, message: str) -> None:
            received.append(message)

        client = create_test_client(
            callsign="W6TEST",
            on_message=on_message,
        )

        # Simulate Android app sending in 8-byte chunks
        message = b"This is a longer message from mobile client\n"
        chunk_size = 8
        for i in range(0, len(message), chunk_size):
            chunk = message[i : i + chunk_size]
            client.handle_data(chunk)

        assert len(received) == 1
        assert received[0] == "This is a longer message from mobile client"

    def test_large_buffer_desktop_client(self):
        """Test desktop client sending large chunks of data."""
        received = []

        def on_message(callsign: str, message: str) -> None:
            received.append(message)

        client = create_test_client(
            callsign="W7TEST",
            on_message=on_message,
        )

        # Simulate client sending multiple messages in one chunk
        data = b"First message\nSecond message\nThird message\n"
        client.handle_data(data)

        assert len(received) == 3
        assert received[0] == "First message"
        assert received[1] == "Second message"
        assert received[2] == "Third message"

    def test_incomplete_message_across_multiple_calls(self):
        """Test message split across multiple handle_data calls."""
        received = []

        def on_message(callsign: str, message: str) -> None:
            received.append(message)

        client = create_test_client(
            callsign="W8TEST",
            on_message=on_message,
        )

        # Send incomplete message
        client.handle_data(b"This is an incomplete")
        assert len(received) == 0  # No newline yet

        # Complete the message
        client.handle_data(b" message\n")
        assert len(received) == 1
        assert received[0] == "This is an incomplete message"


class TestClientEncoding:
    """Test handling of different encoding from various clients."""

    def test_ascii_only_client(self):
        """Test client sending only ASCII characters."""
        received = []

        def on_message(callsign: str, message: str) -> None:
            received.append(message)

        client = create_test_client(
            callsign="W9TEST",
            on_message=on_message,
        )

        client.handle_data(b"Hello World 123\n")
        assert len(received) == 1
        assert received[0] == "Hello World 123"

    def test_latin1_extended_characters(self):
        """Test client sending Latin-1 extended characters."""
        received = []

        def on_message(callsign: str, message: str) -> None:
            received.append(message)

        client = create_test_client(
            callsign="N1TEST",
            on_message=on_message,
        )

        # Latin-1 extended characters (Café)
        client.handle_data("Café\n".encode("latin-1"))

        assert len(received) == 1
        assert received[0] == "Café"

    def test_invalid_utf8_graceful_degradation(self):
        """Test handling of invalid UTF-8 (client misconfigured)."""
        received = []

        def on_message(callsign: str, message: str) -> None:
            received.append(message)

        client = create_test_client(
            callsign="N2TEST",
            on_message=on_message,
        )

        # Send invalid byte sequences (should be ignored gracefully)
        # Valid text with invalid bytes mixed in
        client.handle_data(b"Hello\xff\xfeWorld\n")

        # Should receive something (invalid bytes ignored)
        assert len(received) == 1
        # Message should contain the valid parts
        assert "Hello" in received[0]
        assert "World" in received[0]


class TestClientInteraction:
    """Test realistic client interaction patterns."""

    def test_typical_ax25call_session(self):
        """Simulate a typical ax25call session."""
        received_messages = []
        sent_data = []

        def on_message(callsign: str, message: str) -> None:
            received_messages.append((callsign, message))

        client = create_test_client(
            callsign="KA1TEST",
            on_message=on_message,
            track_sent_data=sent_data,
        )

        # 1. Client connects and receives welcome (simulated by send)
        client.send_data(b"Welcome to the BBS\r\n")
        assert len(sent_data) == 1

        # 2. Client receives prompt
        client.send_prompt()
        assert len(sent_data) == 2
        assert b"KA1TEST>" in sent_data[1]

        # 3. Client sends first message
        client.handle_data(b"Hello everyone!\n")
        assert len(received_messages) == 1
        assert received_messages[0] == ("KA1TEST", "Hello everyone!")

        # 4. Client sends second message
        client.handle_data(b"Testing the BBS\n")
        assert len(received_messages) == 2
        assert received_messages[1] == ("KA1TEST", "Testing the BBS")

        # 5. Client disconnects
        client.disconnect()
        assert not client.active

    def test_packet_commander_quick_messages(self):
        """Simulate Packet Commander sending multiple quick messages."""
        received = []

        def on_message(callsign: str, message: str) -> None:
            received.append(message)

        client = create_test_client(
            callsign="KB1TEST",
            on_message=on_message,
        )

        # Packet Commander user typing fast, hitting Enter after each
        client.handle_data(b"Testing\r\n")
        client.handle_data(b"Quick\r\n")
        client.handle_data(b"Messages\r\n")

        assert len(received) == 3
        assert received == ["Testing", "Quick", "Messages"]

    def test_android_slow_typing(self):
        """Simulate Android user typing slowly with touch keyboard."""
        received = []

        def on_message(callsign: str, message: str) -> None:
            received.append(message)

        client = create_test_client(
            callsign="KC1TEST",
            on_message=on_message,
        )

        # Simulate slow character-by-character input (buffered until newline)
        message = "Hello from Android"
        for char in message:
            client.handle_data(char.encode("latin-1"))
            # No message until newline
            assert len(received) == 0

        # User hits Enter
        client.handle_data(b"\n")
        assert len(received) == 1
        assert received[0] == "Hello from Android"


class TestClientEdgeCases:
    """Test edge cases that might occur with various clients."""

    def test_empty_messages_ignored(self):
        """Test that clients sending empty lines don't create messages."""
        received = []

        def on_message(callsign: str, message: str) -> None:
            received.append(message)

        client = create_test_client(
            callsign="KD1TEST",
            on_message=on_message,
        )

        # Client sends various forms of empty messages
        client.handle_data(b"\n")
        client.handle_data(b"\r\n")
        client.handle_data(b"   \n")
        client.handle_data(b"\t\n")

        # No messages should be generated
        assert len(received) == 0

    def test_very_long_message_from_script(self):
        """Test handling of very long messages (e.g., from automated script)."""
        received = []

        def on_message(callsign: str, message: str) -> None:
            received.append(message)

        client = create_test_client(
            callsign="KE1TEST",
            on_message=on_message,
        )

        # Send a very long message (1000 characters)
        long_message = "A" * 1000 + "\n"
        client.handle_data(long_message.encode("latin-1"))

        assert len(received) == 1
        assert len(received[0]) == 1000
        assert received[0] == "A" * 1000

    def test_rapid_connect_disconnect(self):
        """Test client rapidly connecting and disconnecting."""
        sent_data = []

        client = create_test_client(
            callsign="KF1TEST",
            on_message=lambda c, m: None,
            track_sent_data=sent_data,
        )

        # Send some data
        assert client.active
        client.send_data(b"Test\r\n")
        assert len(sent_data) == 1

        # Disconnect
        client.disconnect()
        assert not client.active

        # Try to send after disconnect (should fail gracefully)
        result = client.send_data(b"Should not send\r\n")
        assert not result
        assert len(sent_data) == 1  # No additional sends

    def test_null_bytes_in_stream(self):
        """Test handling of null bytes in data stream (protocol errors)."""
        received = []

        def on_message(callsign: str, message: str) -> None:
            received.append(message)

        client = create_test_client(
            callsign="KG1TEST",
            on_message=on_message,
        )

        # Send message with null bytes (shouldn't crash)
        client.handle_data(b"Hello\x00World\n")

        # Should handle gracefully
        assert len(received) == 1
        # Null bytes handled by latin-1 decoder


# Integration test combining multiple aspects
class TestRealisticClientScenarios:
    """Test realistic multi-client scenarios."""

    def test_multiple_clients_different_behaviors(self):
        """Test multiple clients with different behaviors simultaneously."""
        # This would be more meaningful with BBSServer, but we can
        # demonstrate that individual clients are isolated

        clients = []
        received_per_client = {f"W{i}TEST": [] for i in range(3)}

        def make_on_message(callsign):
            def on_message(cs: str, message: str) -> None:
                received_per_client[callsign].append(message)

            return on_message

        # Client 1: ax25call style (LF)
        client1 = create_test_client(
            callsign="W0TEST",
            on_message=make_on_message("W0TEST"),
        )
        clients.append(client1)

        # Client 2: Packet Commander style (CRLF)
        client2 = create_test_client(
            callsign="W1TEST",
            on_message=make_on_message("W1TEST"),
        )
        clients.append(client2)

        # Client 3: Legacy style (CR)
        client3 = create_test_client(
            callsign="W2TEST",
            on_message=make_on_message("W2TEST"),
        )
        clients.append(client3)

        # Each client sends messages in their own style
        client1.handle_data(b"From ax25call\n")
        client2.handle_data(b"From Packet Commander\r\n")
        client3.handle_data(b"From legacy terminal\r")

        # Verify each client's messages were received correctly
        assert received_per_client["W0TEST"] == ["From ax25call"]
        assert received_per_client["W1TEST"] == ["From Packet Commander"]
        assert received_per_client["W2TEST"] == ["From legacy terminal"]
