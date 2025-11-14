#!/usr/bin/env python3
"""Fox BBS main entry point."""
import argparse
import logging
import os
import signal
import sys
import threading
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.bbs_server import BBSServer  # noqa: E402
from src.config import Config  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for Fox BBS."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fox BBS - Amateur Radio Bulletin Board System")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode with simulated connections (no Direwolf required)",
    )
    parser.add_argument(
        "--config",
        default="config/fox.yaml",
        help="Path to configuration file (default: config/fox.yaml)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    # Configure logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    logger.info("Starting Fox BBS...")
    if args.demo:
        logger.info("=== DEMO MODE === (No hardware required)")

    # Load configuration
    try:
        config = Config(args.config)
        logger.info(f"Configuration loaded: SSID={config.ssid}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Create and start server
    server = BBSServer(config)

    # Handle shutdown signals
    def signal_handler(signum, frame):
        logger.info("Shutdown signal received")

        # Start a watchdog timer to force exit if graceful shutdown hangs
        def force_exit():
            logger.warning("Graceful shutdown timed out, forcing exit")
            os._exit(1)

        watchdog = threading.Timer(3.0, force_exit)
        watchdog.daemon = True
        watchdog.start()

        # Try to forcefully close the socket to unblock receiver thread
        try:
            if server.agwpe_handler and server.agwpe_handler.engine:
                if (
                    hasattr(server.agwpe_handler.engine, "_sock")
                    and server.agwpe_handler.engine._sock
                ):
                    logger.info("Forcing socket close to unblock receiver thread")
                    server.agwpe_handler.engine._sock.close()
        except Exception as e:
            logger.debug(f"Error closing socket: {e}")

        # Now attempt graceful shutdown
        server.stop()
        watchdog.cancel()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start the server
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        server.stop()
    except Exception as e:
        logger.error(f"Server error: {e}")
        server.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
