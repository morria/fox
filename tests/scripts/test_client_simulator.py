#!/usr/bin/env python3
"""
Test client simulator for Fox BBS compatibility testing.

Simulates behavior of various AX.25 clients to ensure compatibility.
"""

import argparse
import logging
import sys
import os
import time
from typing import Dict, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src.ax25_client import AX25Client  # noqa: E402


# Client behavior profiles
class ClientBehavior:
    """Defines behavior patterns for different client types."""

    def __init__(
        self,
        name: str,
        line_ending: str,
        chunk_size: int,
        encoding: str,
        send_delay: float,
        test_messages: List[str],
    ):
        """
        Initialize client behavior profile.

        Args:
            name: Client name
            line_ending: Line ending to use (\\r\\n, \\n, \\r)
            chunk_size: Bytes per chunk (0 = send all at once)
            encoding: Character encoding to use
            send_delay: Delay between chunks in seconds
            test_messages: Messages to send during test
        """
        self.name = name
        self.line_ending = line_ending
        self.chunk_size = chunk_size
        self.encoding = encoding
        self.send_delay = send_delay
        self.test_messages = test_messages


# Define known client behaviors
CLIENT_PROFILES: Dict[str, ClientBehavior] = {
    "ax25call": ClientBehavior(
        name="ax25call (Linux standard)",
        line_ending="\n",
        chunk_size=0,  # Send complete lines
        encoding="latin-1",
        send_delay=0.0,
        test_messages=[
            "Hello from ax25call",
            "Testing with LF line endings",
            "Special chars: ÄÖÜ",
        ],
    ),
    "packet-commander": ClientBehavior(
        name="Packet Commander (Windows)",
        line_ending="\r\n",
        chunk_size=64,  # Moderate buffering
        encoding="latin-1",
        send_delay=0.01,
        test_messages=[
            "Hello from Packet Commander",
            "Testing with CRLF line endings",
            "Windows-style formatting",
        ],
    ),
    "android": ClientBehavior(
        name="Android AX.25 App",
        line_ending="\n",
        chunk_size=32,  # Smaller chunks (mobile)
        encoding="utf-8",  # May try UTF-8
        send_delay=0.02,
        test_messages=[
            "Hello from Android",
            "Mobile client test",
            "Emoji test: 📻",  # Will fail gracefully
        ],
    ),
    "legacy": ClientBehavior(
        name="Legacy Terminal (CR only)",
        line_ending="\r",
        chunk_size=1,  # Character-by-character
        encoding="ascii",
        send_delay=0.005,
        test_messages=[
            "Hello from legacy terminal",
            "Character by character transmission",
            "Old Mac CR endings",
        ],
    ),
    "mixed": ClientBehavior(
        name="Mixed Line Endings (buggy client)",
        line_ending="\r\n",  # Primary
        chunk_size=0,
        encoding="latin-1",
        send_delay=0.0,
        test_messages=[
            "Message with CRLF\r\n",
            "Message with LF\n",
            "Message with CR\r",
            "Back to CRLF\r\n",
        ],
    ),
}


class ClientSimulator:
    """Simulates a client connecting to Fox BBS."""

    def __init__(self, behavior: ClientBehavior):
        """Initialize simulator with behavior profile."""
        self.behavior = behavior
        self.client: AX25Client = None
        self.received_messages: List[str] = []
        self.logger = logging.getLogger(f"ClientSimulator[{behavior.name}]")

    def setup_client(self) -> AX25Client:
        """Create and configure AX25Client for testing."""

        # Mock send handler that captures output
        def mock_send_handler(data: bytes) -> bool:
            decoded = data.decode("latin-1", errors="ignore")
            self.received_messages.append(decoded)
            self.logger.debug(f"Received: {repr(decoded)}")
            return True

        # Create client with mock sender
        client = AX25Client(
            callsign="W1TEST",
            port=0,
            send_handler=mock_send_handler,
            on_message=self._on_message,
        )

        self.client = client
        return client

    def _on_message(self, callsign: str, message: str) -> None:
        """Handle incoming messages from client."""
        self.logger.info(f"Message from {callsign}: {message}")

    def send_message(self, message: str) -> None:
        """Send a message using the client's behavior profile."""
        # Add line ending if not already in mixed mode
        if "with" not in message:  # Skip if message has explicit ending
            message = message + self.behavior.line_ending

        # Encode according to profile
        try:
            data = message.encode(self.behavior.encoding)
        except UnicodeEncodeError as e:
            self.logger.warning(f"Encoding error with {self.behavior.encoding}: {e}")
            data = message.encode(self.behavior.encoding, errors="ignore")

        # Send in chunks if configured
        if self.behavior.chunk_size > 0:
            for i in range(0, len(data), self.behavior.chunk_size):
                chunk = data[i : i + self.behavior.chunk_size]
                self.client.handle_data(chunk)
                if self.behavior.send_delay > 0:
                    time.sleep(self.behavior.send_delay)
        else:
            # Send all at once
            self.client.handle_data(data)

    def run_test(self) -> bool:
        """
        Run compatibility test with this client profile.

        Returns:
            True if test passed, False otherwise
        """
        self.logger.info(f"Starting test for: {self.behavior.name}")
        self.logger.info(f"  Line ending: {repr(self.behavior.line_ending)}")
        self.logger.info(f"  Chunk size: {self.behavior.chunk_size}")
        self.logger.info(f"  Encoding: {self.behavior.encoding}")

        try:
            # Setup
            self.setup_client()

            # Simulate connection (would normally receive welcome/prompt)
            # In real scenario, BBS sends welcome banner
            initial_prompt = f"{self.client.callsign}> "
            self.client.handle_data(initial_prompt.encode("latin-1"))

            # Send test messages
            for i, message in enumerate(self.behavior.test_messages, 1):
                self.logger.info(f"Sending message {i}/{len(self.behavior.test_messages)}")
                self.send_message(message)
                time.sleep(0.1)  # Brief pause between messages

            # Validate received data
            self.logger.info(f"Test complete. Received {len(self.received_messages)} responses")

            # Basic validation
            success = True
            if not self.received_messages:
                self.logger.error("❌ No responses received from BBS")
                success = False
            else:
                self.logger.info("✅ Client successfully communicated with BBS")

            return success

        except Exception as e:
            self.logger.error(f"❌ Test failed with exception: {e}", exc_info=True)
            return False


def run_all_tests() -> None:
    """Run tests for all client profiles."""
    results = {}

    print("=" * 70)
    print("Fox BBS Client Compatibility Test Suite")
    print("=" * 70)
    print()

    for profile_name, behavior in CLIENT_PROFILES.items():
        print(f"\n{'=' * 70}")
        print(f"Testing: {behavior.name}")
        print(f"{'=' * 70}")

        simulator = ClientSimulator(behavior)
        success = simulator.run_test()
        results[profile_name] = success

        print()

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    for profile_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:10} - {CLIENT_PROFILES[profile_name].name}")

    all_passed = all(results.values())
    print("=" * 70)
    if all_passed:
        print("✅ All client compatibility tests PASSED")
    else:
        print("❌ Some client compatibility tests FAILED")
        sys.exit(1)


def run_single_test(profile_name: str) -> None:
    """Run test for a single client profile."""
    if profile_name not in CLIENT_PROFILES:
        print(f"Error: Unknown client profile '{profile_name}'")
        print(f"Available profiles: {', '.join(CLIENT_PROFILES.keys())}")
        sys.exit(1)

    behavior = CLIENT_PROFILES[profile_name]
    print(f"Testing: {behavior.name}")
    print()

    simulator = ClientSimulator(behavior)
    success = simulator.run_test()

    print()
    if success:
        print(f"✅ Test PASSED for {behavior.name}")
    else:
        print(f"❌ Test FAILED for {behavior.name}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test Fox BBS compatibility with various AX.25 clients"
    )
    parser.add_argument(
        "--client",
        type=str,
        help=f"Test specific client profile: {', '.join(CLIENT_PROFILES.keys())}",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available client profiles",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s - %(name)s - %(message)s",
    )

    # List profiles
    if args.list:
        print("Available client profiles:")
        for name, behavior in CLIENT_PROFILES.items():
            print(f"  {name:20} - {behavior.name}")
        return

    # Run tests
    if args.client:
        run_single_test(args.client)
    else:
        run_all_tests()


if __name__ == "__main__":
    main()
