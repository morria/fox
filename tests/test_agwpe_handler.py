"""Tests for AGWPE handler (src/agwpe_handler.py)."""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
import threading
import time

from src.agwpe_handler import BBSReceiveHandler, AGWPEHandler


class TestBBSReceiveHandler:
    """Test BBSReceiveHandler class."""

    def test_create_handler(self):
        """Test creating a BBSReceiveHandler."""
        on_connect = Mock()
        on_disconnect = Mock()
        on_data = Mock()

        handler = BBSReceiveHandler(on_connect, on_disconnect, on_data)

        assert handler.on_connect_request == on_connect
        assert handler.on_disconnect == on_disconnect
        assert handler.on_data == on_data

    def test_connection_received_incoming(self, capture_logs):
        """Test handling incoming connection."""
        on_connect = Mock()
        on_disconnect = Mock()
        on_data = Mock()

        handler = BBSReceiveHandler(on_connect, on_disconnect, on_data)

        # Simulate incoming connection
        handler.connection_received(0, 'W1ABC', 'FOX-1', True, None)

        # Should call on_connect_request
        on_connect.assert_called_once_with(0, 'W1ABC', 'FOX-1')
        assert 'Incoming connection' in capture_logs.text

    def test_connection_received_outgoing(self, capture_logs):
        """Test handling outgoing connection confirmation."""
        on_connect = Mock()
        on_disconnect = Mock()
        on_data = Mock()

        handler = BBSReceiveHandler(on_connect, on_disconnect, on_data)

        # Simulate outgoing connection
        handler.connection_received(0, 'FOX-1', 'W1ABC', False, None)

        # Should not call on_connect_request for outgoing
        on_connect.assert_not_called()
        assert 'Outgoing connection' in capture_logs.text

    def test_connected_data(self, capture_logs):
        """Test handling incoming data."""
        on_connect = Mock()
        on_disconnect = Mock()
        on_data = Mock()

        handler = BBSReceiveHandler(on_connect, on_disconnect, on_data)

        # Simulate data received
        data = b'Hello World'
        handler.connected_data(0, 'W1ABC', 'FOX-1', 0xF0, data)

        # Should call on_data
        on_data.assert_called_once_with(0, 'W1ABC', 'FOX-1', data)

    def test_disconnected(self, capture_logs):
        """Test handling disconnection."""
        on_connect = Mock()
        on_disconnect = Mock()
        on_data = Mock()

        handler = BBSReceiveHandler(on_connect, on_disconnect, on_data)

        # Simulate disconnection
        handler.disconnected(0, 'W1ABC', 'FOX-1', None)

        # Should call on_disconnect
        on_disconnect.assert_called_once_with(0, 'W1ABC', 'FOX-1')
        assert 'Disconnected' in capture_logs.text

    def test_callsign_registered_success(self, capture_logs):
        """Test successful callsign registration."""
        handler = BBSReceiveHandler(Mock(), Mock(), Mock())

        handler.callsign_registered('FOX-1', True)

        assert 'Callsign registered: FOX-1' in capture_logs.text

    def test_callsign_registered_failure(self, capture_logs):
        """Test failed callsign registration."""
        handler = BBSReceiveHandler(Mock(), Mock(), Mock())

        handler.callsign_registered('FOX-1', False)

        assert 'Failed to register callsign' in capture_logs.text


class TestAGWPEHandlerCreation:
    """Test AGWPEHandler initialization."""

    def test_create_handler(self):
        """Test creating an AGWPEHandler."""
        on_connect = Mock()
        on_disconnect = Mock()
        on_data = Mock()

        handler = AGWPEHandler(
            host='localhost',
            port=8000,
            radio_port=0,
            mycall='FOX-1',
            on_connect_request=on_connect,
            on_disconnect=on_disconnect,
            on_data=on_data
        )

        assert handler.host == 'localhost'
        assert handler.port == 8000
        assert handler.radio_port == 0
        assert handler.mycall == 'FOX-1'
        assert handler.engine is None
        assert handler.running is False
        assert len(handler.connections) == 0


class TestAGWPEHandlerStartStop:
    """Test starting and stopping the AGWPE handler."""

    @patch('src.agwpe_handler.PacketEngine')
    @patch('src.agwpe_handler.tocsin')
    def test_start_handler(self, mock_tocsin, mock_packet_engine_class):
        """Test starting the AGWPE handler."""
        # Setup mocks
        mock_engine = MagicMock()
        mock_packet_engine_class.return_value = mock_engine
        mock_engine.connected_to_server = True

        # Create signal mock
        mock_signal = MagicMock()
        mock_tocsin.signal.return_value = mock_signal

        handler = AGWPEHandler(
            host='localhost',
            port=8000,
            radio_port=0,
            mycall='FOX-1',
            on_connect_request=Mock(),
            on_disconnect=Mock(),
            on_data=Mock()
        )

        # Simulate engine ready signal
        def trigger_ready(*args):
            # Trigger the engine ready callback
            if mock_signal.listen.called:
                callback = mock_signal.listen.call_args[0][0]
                callback('engine_ready', None)

        mock_engine.connect_to_server.side_effect = trigger_ready

        handler.start()

        # Verify initialization
        assert handler.running is True
        assert handler.engine is not None
        mock_engine.connect_to_server.assert_called_once_with('localhost', 8000)
        mock_engine.register_callsign.assert_called_once_with('FOX-1')

    @patch('src.agwpe_handler.PacketEngine')
    @patch('src.agwpe_handler.tocsin')
    def test_start_timeout(self, mock_tocsin, mock_packet_engine_class):
        """Test start timeout when engine doesn't become ready."""
        mock_engine = MagicMock()
        mock_packet_engine_class.return_value = mock_engine

        # Don't trigger the ready signal
        mock_signal = MagicMock()
        mock_tocsin.signal.return_value = mock_signal

        handler = AGWPEHandler(
            host='localhost',
            port=8000,
            radio_port=0,
            mycall='FOX-1',
            on_connect_request=Mock(),
            on_disconnect=Mock(),
            on_data=Mock()
        )

        # Should raise TimeoutError
        with pytest.raises(TimeoutError):
            handler.start()

    def test_stop_handler(self):
        """Test stopping the AGWPE handler."""
        handler = AGWPEHandler(
            host='localhost',
            port=8000,
            radio_port=0,
            mycall='FOX-1',
            on_connect_request=Mock(),
            on_disconnect=Mock(),
            on_data=Mock()
        )

        # Setup mock engine
        mock_engine = MagicMock()
        mock_engine.connected_to_server = True
        handler.engine = mock_engine
        handler.running = True

        # Add some connections
        handler.connections['W1ABC'] = (0, 'W1ABC', 'FOX-1')
        handler.connections['W2DEF'] = (0, 'W2DEF', 'FOX-1')

        handler.stop()

        # Verify cleanup
        assert handler.running is False
        assert len(handler.connections) == 0
        mock_engine.disconnect.assert_called()
        mock_engine.unregister_callsign.assert_called_once_with('FOX-1')

    def test_stop_without_engine(self):
        """Test stopping when engine is None."""
        handler = AGWPEHandler(
            host='localhost',
            port=8000,
            radio_port=0,
            mycall='FOX-1',
            on_connect_request=Mock(),
            on_disconnect=Mock(),
            on_data=Mock()
        )

        # Should not raise
        handler.stop()
        assert handler.running is False


class TestAGWPEHandlerConnections:
    """Test connection management."""

    def test_handle_connection_request(self):
        """Test handling a connection request."""
        on_connect = Mock()
        handler = AGWPEHandler(
            host='localhost',
            port=8000,
            radio_port=0,
            mycall='FOX-1',
            on_connect_request=on_connect,
            on_disconnect=Mock(),
            on_data=Mock()
        )

        handler._handle_connection_request(0, 'W1ABC', 'FOX-1')

        # Should store connection info
        assert 'W1ABC' in handler.connections
        assert handler.connections['W1ABC'] == (0, 'W1ABC', 'FOX-1')

        # Should call callback
        on_connect.assert_called_once_with('W1ABC')

    def test_handle_data_internal(self):
        """Test handling incoming data."""
        on_data = Mock()
        handler = AGWPEHandler(
            host='localhost',
            port=8000,
            radio_port=0,
            mycall='FOX-1',
            on_connect_request=Mock(),
            on_disconnect=Mock(),
            on_data=on_data
        )

        data = b'Test message'
        handler._handle_data_internal(0, 'W1ABC', 'FOX-1', data)

        # Should call callback
        on_data.assert_called_once_with('W1ABC', data)

    def test_handle_disconnect_internal(self):
        """Test handling disconnection."""
        on_disconnect = Mock()
        handler = AGWPEHandler(
            host='localhost',
            port=8000,
            radio_port=0,
            mycall='FOX-1',
            on_connect_request=Mock(),
            on_disconnect=on_disconnect,
            on_data=Mock()
        )

        # Add connection
        handler.connections['W1ABC'] = (0, 'W1ABC', 'FOX-1')

        handler._handle_disconnect_internal(0, 'W1ABC', 'FOX-1')

        # Should remove connection
        assert 'W1ABC' not in handler.connections

        # Should call callback
        on_disconnect.assert_called_once_with('W1ABC')


class TestAGWPEHandlerDataSending:
    """Test sending data."""

    def test_send_data_success(self):
        """Test sending data to a connected station."""
        handler = AGWPEHandler(
            host='localhost',
            port=8000,
            radio_port=0,
            mycall='FOX-1',
            on_connect_request=Mock(),
            on_disconnect=Mock(),
            on_data=Mock()
        )

        # Setup mock engine
        mock_engine = MagicMock()
        handler.engine = mock_engine

        # Add connection
        handler.connections['W1ABC'] = (0, 'W1ABC', 'FOX-1')

        # Send data
        data = b'Test message'
        result = handler.send_data('W1ABC', data)

        assert result is True
        mock_engine.send_data.assert_called_once_with(0, 'FOX-1', 'W1ABC', data)

    def test_send_data_no_connection(self, capture_logs):
        """Test sending data to non-connected station."""
        handler = AGWPEHandler(
            host='localhost',
            port=8000,
            radio_port=0,
            mycall='FOX-1',
            on_connect_request=Mock(),
            on_disconnect=Mock(),
            on_data=Mock()
        )

        mock_engine = MagicMock()
        handler.engine = mock_engine

        # Try to send to non-existent connection
        result = handler.send_data('W1ABC', b'Test')

        assert result is False
        mock_engine.send_data.assert_not_called()
        assert 'No connection to W1ABC' in capture_logs.text

    def test_send_data_exception(self, capture_logs):
        """Test handling exception when sending data."""
        handler = AGWPEHandler(
            host='localhost',
            port=8000,
            radio_port=0,
            mycall='FOX-1',
            on_connect_request=Mock(),
            on_disconnect=Mock(),
            on_data=Mock()
        )

        # Setup mock engine that raises
        mock_engine = MagicMock()
        mock_engine.send_data.side_effect = Exception('Send error')
        handler.engine = mock_engine

        # Add connection
        handler.connections['W1ABC'] = (0, 'W1ABC', 'FOX-1')

        # Send data
        result = handler.send_data('W1ABC', b'Test')

        assert result is False
        assert 'Error sending' in capture_logs.text


class TestAGWPEHandlerDisconnect:
    """Test disconnecting clients."""

    def test_disconnect_client(self):
        """Test disconnecting a client."""
        handler = AGWPEHandler(
            host='localhost',
            port=8000,
            radio_port=0,
            mycall='FOX-1',
            on_connect_request=Mock(),
            on_disconnect=Mock(),
            on_data=Mock()
        )

        # Setup mock engine
        mock_engine = MagicMock()
        handler.engine = mock_engine

        # Add connection
        handler.connections['W1ABC'] = (0, 'W1ABC', 'FOX-1')

        handler.disconnect_client('W1ABC')

        # Should call engine disconnect
        mock_engine.disconnect.assert_called_once_with(0, 'FOX-1', 'W1ABC')

    def test_disconnect_nonexistent_client(self):
        """Test disconnecting a non-existent client."""
        handler = AGWPEHandler(
            host='localhost',
            port=8000,
            radio_port=0,
            mycall='FOX-1',
            on_connect_request=Mock(),
            on_disconnect=Mock(),
            on_data=Mock()
        )

        mock_engine = MagicMock()
        handler.engine = mock_engine

        # Try to disconnect non-existent client
        handler.disconnect_client('W1ABC')

        # Should not crash
        mock_engine.disconnect.assert_not_called()

    def test_disconnect_client_exception(self, capture_logs):
        """Test handling exception when disconnecting."""
        handler = AGWPEHandler(
            host='localhost',
            port=8000,
            radio_port=0,
            mycall='FOX-1',
            on_connect_request=Mock(),
            on_disconnect=Mock(),
            on_data=Mock()
        )

        # Setup mock engine that raises
        mock_engine = MagicMock()
        mock_engine.disconnect.side_effect = Exception('Disconnect error')
        handler.engine = mock_engine

        # Add connection
        handler.connections['W1ABC'] = (0, 'W1ABC', 'FOX-1')

        # Should not raise
        handler.disconnect_client('W1ABC')

        assert 'Error disconnecting' in capture_logs.text


class TestAGWPEHandlerEdgeCases:
    """Test edge cases."""

    def test_multiple_connections(self):
        """Test managing multiple connections."""
        on_connect = Mock()
        handler = AGWPEHandler(
            host='localhost',
            port=8000,
            radio_port=0,
            mycall='FOX-1',
            on_connect_request=on_connect,
            on_disconnect=Mock(),
            on_data=Mock()
        )

        # Add multiple connections
        handler._handle_connection_request(0, 'W1ABC', 'FOX-1')
        handler._handle_connection_request(0, 'W2DEF', 'FOX-1')
        handler._handle_connection_request(0, 'W3GHI', 'FOX-1')

        assert len(handler.connections) == 3
        assert on_connect.call_count == 3

    def test_connection_info_persistence(self):
        """Test that connection info persists correctly."""
        handler = AGWPEHandler(
            host='localhost',
            port=8000,
            radio_port=0,
            mycall='FOX-1',
            on_connect_request=Mock(),
            on_disconnect=Mock(),
            on_data=Mock()
        )

        # Add connection
        handler._handle_connection_request(0, 'W1ABC', 'FOX-1')

        # Verify stored info
        port, call_from, call_to = handler.connections['W1ABC']
        assert port == 0
        assert call_from == 'W1ABC'
        assert call_to == 'FOX-1'

    def test_stop_with_multiple_connections(self):
        """Test stopping with multiple active connections."""
        handler = AGWPEHandler(
            host='localhost',
            port=8000,
            radio_port=0,
            mycall='FOX-1',
            on_connect_request=Mock(),
            on_disconnect=Mock(),
            on_data=Mock()
        )

        mock_engine = MagicMock()
        mock_engine.connected_to_server = True
        handler.engine = mock_engine
        handler.running = True

        # Add multiple connections
        handler.connections['W1ABC'] = (0, 'W1ABC', 'FOX-1')
        handler.connections['W2DEF'] = (0, 'W2DEF', 'FOX-1')
        handler.connections['W3GHI'] = (0, 'W3GHI', 'FOX-1')

        handler.stop()

        # All connections should be disconnected
        assert mock_engine.disconnect.call_count == 3
        assert len(handler.connections) == 0
