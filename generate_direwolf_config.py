#!/usr/bin/env python3
"""Standalone CLI tool for generating Direwolf configuration.

This script provides a user-friendly wizard for generating a direwolf.conf
file for use with Fox BBS. It can be run independently of the main BBS application.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.direwolf_config_generator import (  # noqa: E402
    DirewolfConfigGenerator,
    run_interactive_setup,
)
from src.exceptions import ConfigurationError  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main() -> int:
    """Main entry point for the configuration generator CLI.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Generate Direwolf configuration for Fox BBS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run interactive wizard (recommended)
  python generate_direwolf_config.py

  # Generate with specific parameters (non-interactive)
  python generate_direwolf_config.py --callsign W1ABC-10 --device plughw:1,0

  # Force overwrite existing configuration
  python generate_direwolf_config.py --overwrite

For more information, see docs/setup.md
        """,
    )

    parser.add_argument(
        "--config",
        default="config/direwolf.conf",
        help="Path to output configuration file (default: config/direwolf.conf)",
    )

    parser.add_argument(
        "--callsign",
        help="Amateur radio callsign (e.g., W1ABC-10). If not provided, "
        "interactive mode will prompt for it",
    )

    parser.add_argument(
        "--device",
        help="ALSA audio device (e.g., plughw:1,0). If not provided, "
        "devices will be detected automatically",
    )

    parser.add_argument(
        "--agwpe-port",
        type=int,
        default=8000,
        help="AGWPE port number (default: 8000)",
    )

    parser.add_argument(
        "--baud-rate",
        type=int,
        default=1200,
        help="Modem baud rate (default: 1200)",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing configuration file",
    )

    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run in non-interactive mode (requires --callsign)",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    # Configure logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # Create generator instance
    generator = DirewolfConfigGenerator(args.config)

    try:
        # Check if file exists and handle overwrite
        config_path = Path(args.config)
        if config_path.exists() and not args.overwrite:
            logger.error(
                f"Configuration file already exists: {config_path}\n"
                f"Use --overwrite to replace it, or specify a different path with --config"
            )
            return 1

        # Determine mode: interactive vs non-interactive
        if args.non_interactive or args.callsign:
            # Non-interactive mode
            if not args.callsign:
                logger.error(
                    "Error: --callsign is required in non-interactive mode\n"
                    "Use --callsign YOURCALL-SSID or remove --non-interactive "
                    "for interactive setup"
                )
                return 1

            logger.info("Running in non-interactive mode...")

            # Detect audio device if not provided
            audio_device = args.device
            if not audio_device:
                logger.info("Detecting audio devices...")
                devices = generator.detect_audio_devices()
                if devices:
                    audio_device = devices[0].alsa_device
                    logger.info(f"Using detected audio device: {audio_device}")
                else:
                    audio_device = DirewolfConfigGenerator.DEFAULT_AUDIO_DEVICE
                    logger.warning(f"No audio devices detected, using default: {audio_device}")

            # Generate configuration
            config_file = generator.write_config(
                callsign=args.callsign,
                audio_device=audio_device,
                agwpe_port=args.agwpe_port,
                baud_rate=args.baud_rate,
                overwrite=args.overwrite,
            )

            print(f"\n✓ Configuration written to: {config_file}")
            print("\nNext steps:")
            print(f"1. Review and customize: {config_file}")
            print("2. Configure PTT (Push-To-Talk) for your hardware")
            print("3. Start Direwolf: direwolf -c config/direwolf.conf")
            print("4. Start Fox BBS: python fox_bbs.py")

        else:
            # Interactive mode
            logger.info("Starting interactive configuration wizard...")
            config_file = run_interactive_setup(args.config)

            if not config_file:
                logger.info("Configuration cancelled by user")
                return 1

        return 0

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n\nConfiguration cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=args.debug)
        return 1


if __name__ == "__main__":
    sys.exit(main())
