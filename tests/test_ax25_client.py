"""Tests for AX.25 client handling (src/ax25_client.py)."""
import pytest
from unittest.mock import Mock, call

from src.ax25_client import AX25Client


class TestAX25ClientCreation:
    """Test AX25Client initialization."""

    def test_create_client(self, mock_agwpe_handler, mock_client_callback):
        """Test creating an AX25Client."""
        client = AX25Client(
            callsign='W1TEST',
            ssid='FOX-1',
            agwpe_handler=mock_agwpe_handler,
            on_message=mock_client_callback['on_message'],
            on_disconnect=mock_client_callback['on_disconnect']
        )

        assert client.callsign == 'W1TEST'
        assert client.ssid == 'FOX-1'
        assert client.agwpe_handler == mock_agwpe_handler
        assert client.buffer == ''
        assert client.active is True

    def test_client_initial_state(self, sample_client):
        """Test client initial state."""
        assert sample_client.active is True
        assert sample_client.buffer == ''


class TestDataHandling:
    """Test handling incoming data."""

    def test_handle_simple_message(self, sample_client, mock_client_callback):
        """Test handling a simple message with newline."""
        data = b'Hello World\n'

        sample_client.handle_data(data)

        # Callback should be called with the message
        mock_client_callback['on_message'].assert_called_once_with('W1TEST', 'Hello World')

    def test_handle_message_with_crlf(self, sample_client, mock_client_callback):
        """Test handling message with CRLF line ending."""
        data = b'Hello World\r\n'

        sample_client.handle_data(data)

        mock_client_callback['on_message'].assert_called_once_with('W1TEST', 'Hello World')

    def test_handle_message_with_cr(self, sample_client, mock_client_callback):
        """Test handling message with CR line ending."""
        data = b'Hello World\r'

        sample_client.handle_data(data)

        mock_client_callback['on_message'].assert_called_once_with('W1TEST', 'Hello World')

    def test_handle_multiple_messages(self, sample_client, mock_client_callback):
        """Test handling multiple messages in one data packet."""
        data = b'First\nSecond\nThird\n'

        sample_client.handle_data(data)

        # Should have three calls
        assert mock_client_callback['on_message'].call_count == 3
        calls = [
            call('W1TEST', 'First'),
            call('W1TEST', 'Second'),
            call('W1TEST', 'Third')
        ]
        mock_client_callback['on_message'].assert_has_calls(calls)

    def test_handle_incomplete_message(self, sample_client, mock_client_callback):
        """Test handling incomplete message (buffering)."""
        data1 = b'Hello '
        data2 = b'World\n'

        sample_client.handle_data(data1)
        # Callback should not be called yet
        mock_client_callback['on_message'].assert_not_called()
        assert sample_client.buffer == 'Hello '

        sample_client.handle_data(data2)
        # Now callback should be called
        mock_client_callback['on_message'].assert_called_once_with('W1TEST', 'Hello World')

    def test_handle_mixed_line_endings(self, sample_client, mock_client_callback):
        """Test handling mixed line endings."""
        data = b'First\r\nSecond\nThird\r'

        sample_client.handle_data(data)

        assert mock_client_callback['on_message'].call_count == 3
        calls = [
            call('W1TEST', 'First'),
            call('W1TEST', 'Second'),
            call('W1TEST', 'Third')
        ]
        mock_client_callback['on_message'].assert_has_calls(calls)

    def test_handle_empty_lines(self, sample_client, mock_client_callback):
        """Test that empty lines are ignored."""
        data = b'\n\nHello\n\n\n'

        sample_client.handle_data(data)

        # Should only get one callback for 'Hello'
        mock_client_callback['on_message'].assert_called_once_with('W1TEST', 'Hello')

    def test_handle_whitespace_only_lines(self, sample_client, mock_client_callback):
        """Test that whitespace-only lines are ignored."""
        data = b'   \nHello\n  \t  \n'

        sample_client.handle_data(data)

        # Should only get one callback for 'Hello'
        mock_client_callback['on_message'].assert_called_once_with('W1TEST', 'Hello')

    def test_handle_latin1_encoding(self, sample_client, mock_client_callback):
        """Test handling latin-1 encoded data."""
        # Latin-1 specific characters
        data = 'Café'.encode('latin-1')

        sample_client.handle_data(data + b'\n')

        mock_client_callback['on_message'].assert_called_once_with('W1TEST', 'Café')

    def test_handle_invalid_encoding(self, sample_client, mock_client_callback):
        """Test handling data with invalid encoding."""
        # Send some invalid bytes (should be ignored due to errors='ignore')
        data = b'\xff\xfeHello\n'

        sample_client.handle_data(data)

        # Should still process the message (invalid chars ignored)
        assert mock_client_callback['on_message'].called

    def test_buffer_persistence(self, sample_client):
        """Test that buffer persists across multiple data calls."""
        sample_client.handle_data(b'Part1')
        assert sample_client.buffer == 'Part1'

        sample_client.handle_data(b' Part2')
        assert sample_client.buffer == 'Part1 Part2'

        sample_client.handle_data(b' Part3\n')
        assert sample_client.buffer == ''

    def test_handle_data_exception(self, sample_client, mock_client_callback, capture_logs):
        """Test that exceptions in data handling are caught and logged."""
        # Make callback raise an exception
        mock_client_callback['on_message'].side_effect = Exception('Test error')

        # Should not raise, but log error
        sample_client.handle_data(b'Hello\n')

        # Check that error was logged
        assert 'Error handling data' in capture_logs.text


class TestSendingData:
    """Test sending data to client."""

    def test_send_data(self, sample_client, mock_agwpe_handler):
        """Test sending data to client."""
        result = sample_client.send_data('Hello World')

        assert result is True
        mock_agwpe_handler.send_data.assert_called_once()
        call_args = mock_agwpe_handler.send_data.call_args
        assert call_args[0][0] == 'W1TEST'
        assert call_args[0][1] == b'Hello World'

    def test_send_message(self, sample_client, mock_agwpe_handler):
        """Test sending a message."""
        sample_client.send_message('Test message')

        mock_agwpe_handler.send_data.assert_called_once()
        call_args = mock_agwpe_handler.send_data.call_args
        assert call_args[0][1] == b'Test message'

    def test_send_prompt(self, sample_client, mock_agwpe_handler):
        """Test sending prompt."""
        sample_client.send_prompt()

        mock_agwpe_handler.send_data.assert_called_once()
        call_args = mock_agwpe_handler.send_data.call_args
        assert b'FOX-1>' in call_args[0][1]

    def test_send_welcome(self, sample_client, mock_agwpe_handler):
        """Test sending welcome banner."""
        sample_client.send_welcome()

        mock_agwpe_handler.send_data.assert_called_once()
        call_args = mock_agwpe_handler.send_data.call_args
        assert b'Welcome' in call_args[0][1]
        assert b'FOX-1' in call_args[0][1]

    def test_send_data_when_inactive(self, sample_client, mock_agwpe_handler):
        """Test that sending data when inactive returns False."""
        sample_client.active = False

        result = sample_client.send_data('Hello')

        assert result is False
        mock_agwpe_handler.send_data.assert_not_called()

    def test_send_data_with_latin1_encoding(self, sample_client, mock_agwpe_handler):
        """Test sending data with latin-1 encoding."""
        sample_client.send_data('Café')

        call_args = mock_agwpe_handler.send_data.call_args
        assert call_args[0][1] == 'Café'.encode('latin-1')

    def test_send_data_exception(self, sample_client, mock_agwpe_handler, capture_logs):
        """Test that exceptions in send_data are caught and logged."""
        mock_agwpe_handler.send_data.side_effect = Exception('Send error')

        result = sample_client.send_data('Hello')

        assert result is False
        assert 'Error sending' in capture_logs.text


class TestDisconnection:
    """Test client disconnection."""

    def test_disconnect(self, sample_client, mock_agwpe_handler, mock_client_callback):
        """Test disconnecting a client."""
        sample_client.disconnect()

        assert sample_client.active is False
        mock_agwpe_handler.disconnect_client.assert_called_once_with('W1TEST')
        mock_client_callback['on_disconnect'].assert_called_once_with(sample_client)

    def test_disconnect_when_already_inactive(self, sample_client, mock_agwpe_handler, mock_client_callback):
        """Test disconnecting when already inactive."""
        sample_client.active = False

        sample_client.disconnect()

        # Should not call handlers
        mock_agwpe_handler.disconnect_client.assert_not_called()
        mock_client_callback['on_disconnect'].assert_not_called()

    def test_cleanup(self, sample_client, capture_logs):
        """Test client cleanup."""
        sample_client.cleanup()

        assert sample_client.active is False
        assert 'Cleaning up client' in capture_logs.text

    def test_cleanup_idempotent(self, sample_client):
        """Test that cleanup can be called multiple times safely."""
        sample_client.cleanup()
        assert sample_client.active is False

        sample_client.cleanup()
        assert sample_client.active is False


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_very_long_message(self, sample_client, mock_client_callback):
        """Test handling very long message."""
        long_message = 'A' * 10000 + '\n'

        sample_client.handle_data(long_message.encode('latin-1'))

        mock_client_callback['on_message'].assert_called_once()
        assert len(mock_client_callback['on_message'].call_args[0][1]) == 10000

    def test_rapid_data_chunks(self, sample_client, mock_client_callback):
        """Test handling rapid small data chunks."""
        message = "Hello World\n"

        # Send one byte at a time
        for char in message:
            sample_client.handle_data(char.encode('latin-1'))

        # Should get one callback after newline
        mock_client_callback['on_message'].assert_called_once_with('W1TEST', 'Hello World')

    def test_multiple_clients_independence(self, mock_agwpe_handler, mock_client_callback):
        """Test that multiple clients are independent."""
        client1 = AX25Client(
            'W1ABC', 'FOX-1', mock_agwpe_handler,
            mock_client_callback['on_message'],
            mock_client_callback['on_disconnect']
        )
        client2 = AX25Client(
            'W2DEF', 'FOX-1', mock_agwpe_handler,
            mock_client_callback['on_message'],
            mock_client_callback['on_disconnect']
        )

        # Send data to each
        client1.handle_data(b'Hello')
        client2.handle_data(b'World')

        # Buffers should be independent
        assert client1.buffer == 'Hello'
        assert client2.buffer == 'World'

    def test_binary_data(self, sample_client, mock_client_callback):
        """Test handling binary data."""
        # Send some binary data with a newline
        data = bytes([0x00, 0x01, 0x02, 0xFF]) + b'\n'

        sample_client.handle_data(data)

        # Should process but with ignored invalid chars
        assert mock_client_callback['on_message'].called

    def test_empty_data(self, sample_client, mock_client_callback):
        """Test handling empty data."""
        sample_client.handle_data(b'')

        # Should not crash
        mock_client_callback['on_message'].assert_not_called()
        assert sample_client.buffer == ''

    def test_only_newlines(self, sample_client, mock_client_callback):
        """Test data with only newlines."""
        sample_client.handle_data(b'\n\n\n\n')

        # Should not call callback (empty lines stripped)
        mock_client_callback['on_message'].assert_not_called()

    def test_message_with_leading_trailing_spaces(self, sample_client, mock_client_callback):
        """Test that leading/trailing spaces are stripped."""
        sample_client.handle_data(b'  Hello World  \n')

        mock_client_callback['on_message'].assert_called_once_with('W1TEST', 'Hello World')

    def test_special_ssid_characters(self, mock_agwpe_handler, mock_client_callback):
        """Test client with special characters in SSID."""
        client = AX25Client(
            'W1TEST', 'FOX-BBS-1', mock_agwpe_handler,
            mock_client_callback['on_message'],
            mock_client_callback['on_disconnect']
        )

        client.send_prompt()

        call_args = mock_agwpe_handler.send_data.call_args
        assert b'FOX-BBS-1>' in call_args[0][1]
