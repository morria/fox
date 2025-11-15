"""Main BBS server for Fox BBS."""

import logging
import time
from threading import Lock
from typing import Dict, Optional

from .agwpe_handler import AGWPEHandler
from .ax25_client import AX25Client
from .config import Config
from .message_store import Message, MessageStore

logger = logging.getLogger(__name__)


class BBSServer:
    """Main BBS server that handles AX.25 connections via Direwolf."""

    def __init__(self, config: Config):
        """Initialize the BBS server.

        Args:
            config: Configuration object
        """
        self.config = config
        self.message_store = MessageStore(
            max_messages=config.max_messages, retention_hours=config.message_retention_hours
        )
        self.clients: Dict[str, AX25Client] = {}
        self.clients_lock = Lock()
        self.running = False
        self.agwpe_handler: Optional[AGWPEHandler] = None

    def start(self) -> None:
        """Start the BBS server."""
        self.running = True

        # Create AGWPE handler
        logger.info(
            f"Connecting to Direwolf at " f"{self.config.direwolf_host}:{self.config.direwolf_port}"
        )

        self.agwpe_handler = AGWPEHandler(
            host=self.config.direwolf_host,
            port=self.config.direwolf_port,
            radio_port=self.config.radio_port,
            mycall=self.config.callsign,
            on_connect_request=self._handle_connect_request,
            on_disconnect=self._handle_disconnect,
            on_data=self._handle_data,
        )

        try:
            # Start the AGWPE handler
            self.agwpe_handler.start()

            logger.info(f"Fox BBS ({self.config.callsign}) started and listening for connections")

            # Keep running until stopped
            while self.running:
                time.sleep(1)

        except Exception as e:
            logger.error(f"Error starting server: {e}")
            self.stop()
            raise

    def _handle_connect_request(self, callsign: str) -> None:
        """Handle incoming connection request.

        Args:
            callsign: Connecting station's callsign
        """
        logger.info(f"New connection from {callsign}")

        # Create client
        assert self.agwpe_handler is not None
        client = AX25Client(
            callsign=callsign,
            ssid=self.config.callsign,
            agwpe_handler=self.agwpe_handler,
            on_message=self._handle_client_message,
            on_disconnect=self._handle_client_disconnect,
        )

        # Add to client list
        with self.clients_lock:
            self.clients[callsign] = client

        # Send welcome banner
        client.send_welcome()

        # Send message history
        self._send_history_to_client(client)

        # Send initial prompt
        client.send_prompt()

    def _handle_data(self, callsign: str, data: bytes) -> None:
        """Handle incoming data from a client.

        Args:
            callsign: Source callsign
            data: Received data
        """
        with self.clients_lock:
            if callsign in self.clients:
                self.clients[callsign].handle_data(data)
            else:
                logger.warning(f"Received data from unknown client: {callsign}")

    def _handle_disconnect(self, callsign: str) -> None:
        """Handle client disconnection.

        Args:
            callsign: Disconnected callsign
        """
        logger.info(f"Client disconnected: {callsign}")

        with self.clients_lock:
            if callsign in self.clients:
                client = self.clients[callsign]
                client.cleanup()
                del self.clients[callsign]

    def _send_history_to_client(self, client: AX25Client) -> None:
        """Send message history to a newly connected client.

        Args:
            client: The client
        """
        messages = self.message_store.get_recent_messages()
        if messages:
            client.send_message("---\r\n")
            for msg in messages:
                client.send_message(f"\r\n{msg}")
            client.send_message("\r\n")

    def _handle_client_message(self, callsign: str, text: str) -> None:
        """Handle a message from a client.

        Args:
            callsign: The sender's callsign
            text: The message text
        """
        # Store the message
        message = self.message_store.add_message(callsign, text)

        logger.info(f"Message from {callsign}: {text}")

        # Broadcast to all clients
        self._broadcast_message(message)

    def _broadcast_message(self, message: Message) -> None:
        """Broadcast a message to all connected clients.

        Args:
            message: The message to broadcast
        """
        formatted_message = f"\r\n{message}\r\n"

        with self.clients_lock:
            for callsign, client in list(self.clients.items()):
                if client.active:
                    client.send_message(formatted_message)
                    client.send_prompt()

    def _handle_client_disconnect(self, client: AX25Client) -> None:
        """Handle client disconnection callback.

        Args:
            client: The disconnected client
        """
        with self.clients_lock:
            if client.callsign in self.clients:
                del self.clients[client.callsign]

    def stop(self) -> None:
        """Stop the BBS server."""
        logger.info("Stopping Fox BBS server...")
        self.running = False

        # Disconnect all clients
        with self.clients_lock:
            for callsign, client in list(self.clients.items()):
                try:
                    client.disconnect()
                except Exception as e:
                    logger.error(f"Error disconnecting {callsign}: {e}")
            self.clients.clear()

        # Stop AGWPE handler
        if self.agwpe_handler:
            try:
                self.agwpe_handler.stop()
            except Exception as e:
                logger.error(f"Error stopping AGWPE handler: {e}")

        logger.info("Fox BBS server stopped")
