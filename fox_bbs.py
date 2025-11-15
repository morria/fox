#!/usr/bin/env python3
"""Fox BBS main entry point."""
import argparse
import logging
import os
import signal
import sys
import threading
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.bbs_server import BBSServer  # noqa: E402
from src.config import Config  # noqa: E402
from src.direwolf_config_generator import ensure_direwolf_config  # noqa: E402
from src.process_manager import DirewolfProcess, ProcessCoordinator  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def _parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed command line arguments
    """
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
    parser.add_argument(
        "--direwolf-config",
        default="config/direwolf.conf",
        help="Path to Direwolf configuration file (default: config/direwolf.conf)",
    )
    parser.add_argument(
        "--skip-direwolf-check",
        action="store_true",
        help="Skip checking for Direwolf configuration (for demo mode or when not using Direwolf)",
    )
    parser.add_argument(
        "--no-auto-direwolf",
        action="store_true",
        help="Don't automatically start Direwolf (connect to external instance)",
    )
    parser.add_argument(
        "--no-process-monitoring",
        action="store_true",
        help="Don't monitor Direwolf process or shutdown if it dies",
    )
    return parser.parse_args()


def _check_direwolf_config(args: argparse.Namespace) -> None:
    """Check and ensure Direwolf configuration exists.

    Args:
        args: Command line arguments
    """
    logger.debug(f"Checking for Direwolf configuration at {args.direwolf_config}")
    if not ensure_direwolf_config(args.direwolf_config):
        logger.warning(
            "Direwolf configuration was not created. "
            "You can create it later using: ./generate_direwolf_config.py"
        )
        if not Path(args.direwolf_config).exists():
            logger.warning(
                "Starting without Direwolf configuration. " "Connection to Direwolf may fail."
            )


def _load_config(config_path: str) -> Config:
    """Load Fox BBS configuration.

    Args:
        config_path: Path to configuration file

    Returns:
        Loaded configuration

    Raises:
        SystemExit: If configuration loading fails
    """
    try:
        config = Config(config_path)
        logger.info(f"Configuration loaded: SSID={config.ssid}")
        return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)


def _setup_direwolf_coordinator(args: argparse.Namespace, config: Config) -> ProcessCoordinator:
    """Set up and start Direwolf process coordinator.

    Args:
        args: Command line arguments
        config: Fox BBS configuration

    Returns:
        Initialized process coordinator, or None if not needed

    Raises:
        SystemExit: If Direwolf startup fails
    """
    logger.debug("Initializing Direwolf process manager")

    direwolf_manager = DirewolfProcess(
        config_path=args.direwolf_config,
        host=config.direwolf_host,
        port=config.direwolf_port,
        startup_timeout=15.0,
    )

    coordinator = ProcessCoordinator(
        direwolf_manager=direwolf_manager,
        auto_shutdown=not args.no_process_monitoring,
    )

    # Check if Direwolf is already running
    if direwolf_manager.is_port_listening():
        logger.info(f"Direwolf is already running on {config.direwolf_host}:{config.direwolf_port}")
    else:
        logger.info("Direwolf not detected, starting automatically...")

        if not coordinator.start_direwolf():
            logger.error("Failed to start Direwolf")
            logger.error(
                "Please start Direwolf manually with: ./direwolf\n"
                "Or use --no-auto-direwolf to connect to external Direwolf instance"
            )
            sys.exit(1)

    return coordinator


def _create_signal_handler(server: BBSServer, coordinator: Optional[ProcessCoordinator] = None):
    """Create signal handler for graceful shutdown.

    Args:
        server: BBS server instance
        coordinator: Process coordinator instance (optional)
    """

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

        # Stop all processes
        if coordinator:
            coordinator.stop_all()

        # Now attempt graceful shutdown
        server.stop()
        watchdog.cancel()
        sys.exit(0)

    return signal_handler


def main():
    """Main entry point for Fox BBS."""
    # Parse command line arguments
    args = _parse_arguments()

    # Configure logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    logger.info("Starting Fox BBS...")
    if args.demo:
        logger.info("=== DEMO MODE === (No hardware required)")

    # Check for Direwolf configuration (unless in demo mode or explicitly skipped)
    if not args.demo and not args.skip_direwolf_check:
        _check_direwolf_config(args)

    # Load configuration
    config = _load_config(args.config)

    # Initialize process coordinator for Direwolf management
    coordinator = None
    if not args.demo and not args.no_auto_direwolf:
        coordinator = _setup_direwolf_coordinator(args, config)

    # Create and start server
    server = BBSServer(config)

    # Set up shutdown handler for process coordinator
    if coordinator:

        def shutdown_callback():
            """Callback invoked when Direwolf dies unexpectedly."""
            logger.error("Initiating shutdown due to Direwolf failure")
            try:
                server.stop()
            except Exception as e:
                logger.error(f"Error stopping server: {e}")
            finally:
                os._exit(1)

        coordinator.set_shutdown_handler(shutdown_callback)

    # Handle shutdown signals
    signal_handler = _create_signal_handler(server, coordinator)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start the server
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        if coordinator:
            coordinator.stop_all()
        server.stop()
    except Exception as e:
        logger.error(f"Server error: {e}")
        if coordinator:
            coordinator.stop_all()
        server.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
