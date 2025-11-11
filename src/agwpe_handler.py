"""AGWPE connection handler for Direwolf integration."""
import logging
from typing import Callable, Dict
from pe import PacketEngine, ReceiveHandler


logger = logging.getLogger(__name__)


class BBSReceiveHandler(ReceiveHandler):
    """Custom receive handler for BBS operations."""

    def __init__(
        self,
        on_connect_request: Callable[[int, str, str], None],
        on_disconnect: Callable[[int, str, str], None],
        on_data: Callable[[int, str, str, bytes], None]
    ):
        """Initialize the receive handler.

        Args:
            on_connect_request: Callback for incoming connections (port, from, to)
            on_disconnect: Callback for disconnections (port, from, to)
            on_data: Callback for incoming data (port, from, to, data)
        """
        super().__init__()
        self.on_connect_request = on_connect_request
        self.on_disconnect = on_disconnect
        self.on_data = on_data

    def connection_received(self, port, call_from, call_to, incoming, message):
        """Handle incoming connection."""
        if incoming:
            logger.info(f"Incoming connection: {call_from} -> {call_to} on port {port}")
            self.on_connect_request(port, call_from, call_to)
        else:
            logger.info(f"Outgoing connection confirmed: {call_from} -> {call_to}")

    def connected_data(self, port, call_from, call_to, pid, data):
        """Handle incoming data on a connection."""
        logger.debug(f"Data received from {call_from}: {len(data)} bytes")
        self.on_data(port, call_from, call_to, data)

    def disconnected(self, port, call_from, call_to, message):
        """Handle disconnection."""
        logger.info(f"Disconnected: {call_from} -> {call_to} on port {port}")
        self.on_disconnect(port, call_from, call_to)

    def callsign_registered(self, callsign, success):
        """Handle callsign registration result."""
        if success:
            logger.info(f"Callsign registered: {callsign}")
        else:
            logger.error(f"Failed to register callsign: {callsign}")


class AGWPEHandler:
    """Handles AGWPE connections to Direwolf."""

    def __init__(
        self,
        host: str,
        port: int,
        radio_port: int,
        mycall: str,
        on_connect_request: Callable[[str], None],
        on_disconnect: Callable[[str], None],
        on_data: Callable[[str, bytes], None]
    ):
        """Initialize the AGWPE handler.

        Args:
            host: Direwolf host
            port: Direwolf AGWPE port
            radio_port: Radio port number
            mycall: Our callsign (BBS callsign)
            on_connect_request: Callback when someone connects (callsign)
            on_disconnect: Callback when someone disconnects (callsign)
            on_data: Callback when data is received (callsign, data)
        """
        self.host = host
        self.port = port
        self.radio_port = radio_port
        self.mycall = mycall
        self._on_connect_request = on_connect_request
        self._on_disconnect = on_disconnect
        self._on_data = on_data

        self.engine = None
        self.running = False

        # Track connections: key = callsign, value = (port, call_from, call_to)
        self.connections: Dict[str, tuple] = {}

    def start(self) -> None:
        """Start the AGWPE handler and connect to Direwolf."""
        logger.info(f"Connecting to Direwolf at {self.host}:{self.port}")

        # Create receive handler
        handler = BBSReceiveHandler(
            on_connect_request=self._handle_connection_request,
            on_disconnect=self._handle_disconnect_internal,
            on_data=self._handle_data_internal
        )

        # Create engine
        self.engine = PacketEngine(handler)

        # Connect to server
        try:
            self.engine.connect_to_server(self.host, self.port)

            # Wait for engine to be ready (it happens in background)
            # In a production system, you'd use the signals to know when ready

            # Register our callsign
            self.engine.register_callsign(self.mycall)

            self.running = True
            logger.info(f"AGWPE handler started, listening as {self.mycall}")

        except Exception as e:
            logger.error(f"Failed to connect to Direwolf: {e}")
            raise

    def stop(self) -> None:
        """Stop the AGWPE handler."""
        logger.info("Stopping AGWPE handler...")
        self.running = False

        if self.engine and self.engine.connected_to_server:
            # Disconnect all connections
            for callsign, conn_info in list(self.connections.items()):
                try:
                    port, call_from, call_to = conn_info
                    self.engine.disconnect(port, call_from, call_to)
                except Exception as e:
                    logger.error(f"Error disconnecting {callsign}: {e}")

            self.connections.clear()

            # Unregister callsign
            try:
                self.engine.unregister_callsign(self.mycall)
            except Exception:
                pass

            # Disconnect from server
            try:
                self.engine.disconnect_from_server()
            except (AttributeError, Exception) as e:
                logger.debug(f"Error disconnecting from server: {e}")

        logger.info("AGWPE handler stopped")

    def _handle_connection_request(self, port: int, call_from: str, call_to: str) -> None:
        """Handle incoming connection request.

        Args:
            port: Radio port number
            call_from: Remote station's callsign
            call_to: Our callsign
        """
        logger.info(f"Connection request from {call_from} to {call_to} on port {port}")

        # Store connection info
        self.connections[call_from] = (port, call_from, call_to)

        # Notify BBS
        self._on_connect_request(call_from)

    def _handle_data_internal(self, port: int, call_from: str, call_to: str, data: bytes) -> None:
        """Handle incoming data from a connection.

        Args:
            port: Radio port
            call_from: Source callsign
            call_to: Destination callsign
            data: Received data
        """
        self._on_data(call_from, data)

    def _handle_disconnect_internal(self, port: int, call_from: str, call_to: str) -> None:
        """Handle disconnection.

        Args:
            port: Radio port
            call_from: Callsign that initiated connection
            call_to: Destination callsign
        """
        logger.info(f"Connection closed with {call_from}")

        if call_from in self.connections:
            del self.connections[call_from]

        self._on_disconnect(call_from)

    def send_data(self, callsign: str, data: bytes) -> bool:
        """Send data to a connected station.

        Args:
            callsign: Destination callsign
            data: Data to send

        Returns:
            True if sent successfully, False otherwise
        """
        if callsign not in self.connections:
            logger.warning(f"No connection to {callsign}")
            return False

        try:
            port, call_from, call_to = self.connections[callsign]
            # For incoming connections, we send from call_to (us) to call_from (them)
            self.engine.send_data(port, call_to, call_from, data)
            return True
        except Exception as e:
            logger.error(f"Error sending to {callsign}: {e}")
            return False

    def disconnect_client(self, callsign: str) -> None:
        """Disconnect a client.

        Args:
            callsign: Callsign to disconnect
        """
        if callsign in self.connections:
            try:
                port, call_from, call_to = self.connections[callsign]
                self.engine.disconnect(port, call_to, call_from)
            except Exception as e:
                logger.error(f"Error disconnecting {callsign}: {e}")
