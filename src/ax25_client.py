"""AX.25 client handling for Fox BBS."""
import logging
from typing import Callable, Optional


logger = logging.getLogger(__name__)


class AX25Client:
    """Represents a connected AX.25 client."""

    def __init__(
        self,
        callsign: str,
        ssid: str,
        agwpe_handler,
        on_message: Callable[[str, str], None],
        on_disconnect: Callable[['AX25Client'], None]
    ):
        """Initialize an AX.25 client.

        Args:
            callsign: Client's callsign
            ssid: BBS SSID for prompts
            agwpe_handler: AGWPE handler for sending data
            on_message: Callback when client sends a message (callsign, text)
            on_disconnect: Callback when client disconnects
        """
        self.callsign = callsign
        self.ssid = ssid
        self.agwpe_handler = agwpe_handler
        self.on_message = on_message
        self.on_disconnect = on_disconnect
        self.buffer = ""
        self.active = True

    def handle_data(self, data: bytes) -> None:
        """Handle incoming data from the client.

        Args:
            data: Received data
        """
        try:
            # Decode the data
            text = data.decode('latin-1', errors='ignore')
            self.buffer += text

            # Process complete lines
            while '\n' in self.buffer or '\r' in self.buffer:
                # Handle both \n and \r\n line endings
                if '\r\n' in self.buffer:
                    line, self.buffer = self.buffer.split('\r\n', 1)
                elif '\n' in self.buffer:
                    line, self.buffer = self.buffer.split('\n', 1)
                elif '\r' in self.buffer:
                    line, self.buffer = self.buffer.split('\r', 1)
                else:
                    break

                line = line.strip()
                if line:
                    # User sent a message
                    logger.debug(f"Message from {self.callsign}: {line}")
                    self.on_message(self.callsign, line)

        except Exception as e:
            logger.error(f"Error handling data from {self.callsign}: {e}")

    def send_data(self, text: str) -> bool:
        """Send text to the client.

        Args:
            text: Text to send

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.active:
            return False

        try:
            data = text.encode('latin-1', errors='ignore')
            return self.agwpe_handler.send_data(self.callsign, data)
        except Exception as e:
            logger.error(f"Error sending to {self.callsign}: {e}")
            return False

    def send_message(self, message: str) -> None:
        """Send a message to the client.

        Args:
            message: Message to send
        """
        self.send_data(message)

    def send_prompt(self) -> None:
        """Send the prompt to the client."""
        self.send_data(f"\r\n{self.ssid}> ")

    def send_welcome(self) -> None:
        """Send the welcome banner to the client."""
        banner = f"\r\nWelcome to {self.ssid} Fox BBS\r\n"
        self.send_data(banner)

    def disconnect(self) -> None:
        """Disconnect the client."""
        if self.active:
            self.active = False
            self.agwpe_handler.disconnect_client(self.callsign)
            self.on_disconnect(self)

    def cleanup(self) -> None:
        """Clean up the client."""
        logger.info(f"Cleaning up client {self.callsign}")
        self.active = False
