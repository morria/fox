#!/usr/bin/env python3
"""Fox BBS main entry point."""
import sys
import signal
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.bbs_server import BBSServer


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for Fox BBS."""
    logger.info("Starting Fox BBS...")

    # Load configuration
    try:
        config = Config('config/fox.yaml')
        logger.info(f"Configuration loaded: SSID={config.ssid}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Create and start server
    server = BBSServer(config)

    # Handle shutdown signals
    def signal_handler(signum, frame):
        logger.info("Shutdown signal received")
        server.stop()
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


if __name__ == '__main__':
    main()
