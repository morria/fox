"""Direwolf configuration file generator for Fox BBS.

This module provides functionality to automatically generate a direwolf.conf
file by detecting system audio devices and prompting the user for their callsign.
"""

import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class AudioDevice:
    """Represents an audio device on the system."""

    def __init__(self, card: int, device: int, name: str, description: Optional[str] = None):
        """Initialize an audio device.

        Args:
            card: ALSA card number
            device: ALSA device number
            name: Device name
            description: Optional device description
        """
        self.card = card
        self.device = device
        self.name = name
        self.description = description or name

    @property
    def alsa_device(self) -> str:
        """Get the ALSA device string for Direwolf."""
        return f"plughw:{self.card},{self.device}"

    def __str__(self) -> str:
        """String representation of the device."""
        return f"Card {self.card}, Device {self.device}: {self.description}"


class DirewolfConfigGenerator:
    """Generates Direwolf configuration files."""

    DEFAULT_BAUD_RATE = 1200
    DEFAULT_AGWPE_PORT = 8000
    DEFAULT_AUDIO_DEVICE = "plughw:1,0"  # Fallback if detection fails

    # Direwolf configuration template
    TEMPLATE = """#
# Direwolf configuration for Fox BBS
# Generated automatically by Fox BBS configuration wizard
#
# For more information about Direwolf configuration options, see:
# https://github.com/wb2osz/direwolf/blob/master/doc/User-Guide.pdf
#

# Amateur radio callsign and SSID for this station
MYCALL {callsign}

# Modem configuration
# Most amateur packet radio uses 1200 baud AFSK on VHF
MODEM {baud_rate}

# Audio device configuration
# Input device (for receiving)
ADEVICE {audio_device}

# PTT (Push-To-Talk) configuration
# Uncomment and configure based on your hardware:
# For GPIO PTT (Raspberry Pi):
# PTT GPIO 17
#
# For serial port RTS/DTR:
# PTT RTS /dev/ttyUSB0
# PTT DTR /dev/ttyUSB0
#
# For CM108/C-Media USB sound card GPIO:
# PTT CM108

# AGWPE network protocol for applications to connect
# This allows Fox BBS and other applications to use Direwolf
AGWPORT {agwpe_port}

# Log received packets to this file
# Uncomment to enable logging:
# LOGDIR /var/log/direwolf

# Digipeater configuration
# Uncomment to enable digipeating:
# DIGIPEAT 0 0 ^WIDE[3-7]-[1-7]$|^TEST$ ^WIDE[12]-[12]$ TRACE

# Beaconing configuration
# Uncomment to send periodic beacon messages:
# PBEACON delay=1 every=30 overlay=S symbol="digi" lat=42.6 long=-71.3 \\
#   power=50 height=20 gain=4 comment="Fox BBS - APRS Digipeater"

# APRS Internet Gateway (IGate) configuration
# Uncomment to enable IGate functionality:
# IGSERVER noam.aprs2.net
# IGLOGIN {callsign_base} {passcode}

# Fix bits mode - try to fix corrupted packets
FIX_BITS 1

# End of configuration
"""

    def __init__(self, config_path: str = "config/direwolf.conf"):
        """Initialize the configuration generator.

        Args:
            config_path: Path where the direwolf.conf file should be created
        """
        self.config_path = Path(config_path)
        self.audio_devices: List[AudioDevice] = []

    def detect_audio_devices(self) -> List[AudioDevice]:
        """Detect available audio devices on the system.

        Returns:
            List of detected audio devices

        Raises:
            ConfigurationError: If audio device detection fails critically
        """
        logger.debug("Detecting audio devices...")
        devices: List[AudioDevice] = []

        try:
            # Try to detect using arecord (part of alsa-utils)
            result = subprocess.run(
                ["arecord", "-l"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

            if result.returncode == 0:
                devices = self._parse_arecord_output(result.stdout)
                logger.debug(f"Detected {len(devices)} audio devices via arecord")

        except FileNotFoundError:
            logger.warning("arecord not found, trying alternative detection")
        except subprocess.TimeoutExpired:
            logger.warning("arecord timeout, trying alternative detection")
        except Exception as e:
            logger.warning(f"arecord failed: {e}, trying alternative detection")

        # If arecord failed, try reading /proc/asound/cards
        if not devices:
            try:
                devices = self._detect_via_proc_asound()
                logger.debug(f"Detected {len(devices)} audio devices via /proc/asound")
            except Exception as e:
                logger.warning(f"Failed to detect via /proc/asound: {e}")

        # Store detected devices
        self.audio_devices = devices

        if not devices:
            logger.warning("No audio devices detected, will use default")

        return devices

    def _parse_arecord_output(self, output: str) -> List[AudioDevice]:
        """Parse output from arecord -l command.

        Args:
            output: Output from arecord -l

        Returns:
            List of detected audio devices
        """
        devices: List[AudioDevice] = []

        # Parse lines like:
        # card 1: Device [USB Audio Device], device 0: USB Audio [USB Audio]
        card_pattern = re.compile(
            r"card\s+(\d+):\s+([^,]+),\s+device\s+(\d+):\s+([^\[]+)\[([^\]]+)\]"
        )

        for line in output.split("\n"):
            match = card_pattern.search(line)
            if match:
                card = int(match.group(1))
                card_name = match.group(2).strip()
                device = int(match.group(3))
                device_desc = match.group(5).strip()

                # Create descriptive name
                full_name = f"{card_name} - {device_desc}"

                devices.append(AudioDevice(card, device, card_name, full_name))

        return devices

    def _detect_via_proc_asound(self) -> List[AudioDevice]:
        """Detect audio devices via /proc/asound/cards.

        Returns:
            List of detected audio devices
        """
        devices: List[AudioDevice] = []
        cards_file = Path("/proc/asound/cards")

        if not cards_file.exists():
            logger.debug("/proc/asound/cards not found")
            return devices

        try:
            with open(cards_file, "r") as f:
                content = f.read()

            # Parse lines like:
            # 1 [Device         ]: USB-Audio - USB Audio Device
            pattern = re.compile(r"^\s*(\d+)\s+\[([^\]]+)\]\s*:\s*(.+)$", re.MULTILINE)

            for match in pattern.finditer(content):
                card = int(match.group(1))
                card_name = match.group(2).strip()
                full_desc = match.group(3).strip()

                # Most USB audio devices have device 0
                devices.append(AudioDevice(card, 0, card_name, full_desc))

        except Exception as e:
            logger.warning(f"Failed to read /proc/asound/cards: {e}")

        return devices

    def prompt_for_callsign(self, default: Optional[str] = None) -> str:
        """Prompt user for their amateur radio callsign.

        Args:
            default: Default callsign to suggest

        Returns:
            Validated callsign

        Raises:
            ConfigurationError: If user input is invalid or cancelled
        """
        prompt = "Enter your amateur radio callsign"
        if default:
            prompt += f" [{default}]"
        prompt += ": "

        while True:
            try:
                callsign = input(prompt).strip()

                # Use default if provided and user pressed enter
                if not callsign and default:
                    callsign = default

                if not callsign:
                    print("Error: Callsign is required")
                    continue

                # Validate callsign format
                if self._is_valid_callsign(callsign):
                    return callsign.upper()
                else:
                    print(f"Error: '{callsign}' is not a valid amateur radio callsign")
                    print("Format: 1-2 letters/numbers, 1 digit, 1-3 letters, " "optional -SSID")
                    print("Examples: W1ABC, W2ASM-10, K6TU-5")

            except (EOFError, KeyboardInterrupt):
                print("\nConfiguration cancelled")
                raise ConfigurationError("User cancelled configuration")

    def _prompt_for_default_device(self) -> str:
        """Ask user if they want to use the default audio device.

        Returns:
            Default audio device string

        Raises:
            ConfigurationError: If user cancels
        """
        print("\nWarning: No audio devices detected automatically")
        print(f"Use default device ({self.DEFAULT_AUDIO_DEVICE})? [Y/n]: ", end="")

        try:
            response = input().strip().lower()
            if response in ("", "y", "yes"):
                return self.DEFAULT_AUDIO_DEVICE
            else:
                print("Please configure audio device manually in direwolf.conf")
                return self.DEFAULT_AUDIO_DEVICE
        except (EOFError, KeyboardInterrupt):
            print("\nConfiguration cancelled")
            raise ConfigurationError("User cancelled configuration")

    def _handle_device_selection(self, choice: int) -> Optional[str]:
        """Handle user's device selection.

        Args:
            choice: User's numeric selection

        Returns:
            Selected device string, or None if selection was invalid
        """
        # Handle custom device entry
        if choice == len(self.audio_devices) + 1:
            custom = input("Enter ALSA device string (e.g., plughw:1,0): ")
            custom = custom.strip()
            if custom:
                return custom
            else:
                print("Error: Device string cannot be empty")
                return None

        # Handle device selection
        if 1 <= choice <= len(self.audio_devices):
            selected_device = self.audio_devices[choice - 1]
            return selected_device.alsa_device
        else:
            print(f"Error: Selection must be between 1 and {len(self.audio_devices) + 1}")
            return None

    def prompt_for_audio_device(self) -> str:
        """Prompt user to select an audio device.

        Returns:
            Selected audio device string for Direwolf

        Raises:
            ConfigurationError: If user input is invalid or cancelled
        """
        # Detect devices if not already done
        if not self.audio_devices:
            self.detect_audio_devices()

        # If no devices detected, ask user if they want to use default
        if not self.audio_devices:
            return self._prompt_for_default_device()

        # Display detected devices
        print("\nDetected audio devices:")
        for i, device in enumerate(self.audio_devices, 1):
            print(f"  {i}. {device}")

        print(f"  {len(self.audio_devices) + 1}. Enter custom device")

        # Prompt for selection
        while True:
            try:
                prompt = f"Select audio device [1-{len(self.audio_devices) + 1}]: "
                selection = input(prompt).strip()

                if not selection:
                    print("Error: Selection is required")
                    continue

                try:
                    choice = int(selection)
                except ValueError:
                    print(f"Error: Invalid selection '{selection}'")
                    continue

                # Handle the selection
                selected: Optional[str] = self._handle_device_selection(choice)
                if selected:
                    return selected

            except (EOFError, KeyboardInterrupt):
                print("\nConfiguration cancelled")
                raise ConfigurationError("User cancelled configuration")

    def generate_config(
        self,
        callsign: str,
        audio_device: Optional[str] = None,
        agwpe_port: int = DEFAULT_AGWPE_PORT,
        baud_rate: int = DEFAULT_BAUD_RATE,
    ) -> str:
        """Generate Direwolf configuration content.

        Args:
            callsign: Amateur radio callsign
            audio_device: ALSA audio device string (None = auto-detect)
            agwpe_port: AGWPE port number (default: 8000)
            baud_rate: Modem baud rate (default: 1200)

        Returns:
            Generated configuration file content

        Raises:
            ConfigurationError: If configuration generation fails
        """
        # Validate callsign
        if not self._is_valid_callsign(callsign):
            raise ConfigurationError(
                f"Invalid callsign: {callsign}. " f"Must be valid amateur radio callsign format"
            )

        callsign = callsign.upper()

        # Use default audio device if not provided
        if audio_device is None:
            audio_device = self.DEFAULT_AUDIO_DEVICE

        # Extract base callsign (without SSID) for APRS
        callsign_base = callsign.split("-")[0]

        # Generate configuration from template
        config = self.TEMPLATE.format(
            callsign=callsign,
            callsign_base=callsign_base,
            audio_device=audio_device,
            agwpe_port=agwpe_port,
            baud_rate=baud_rate,
            passcode="12345",  # Placeholder - user should set their own
        )

        return config

    def write_config(
        self,
        callsign: str,
        audio_device: Optional[str] = None,
        agwpe_port: int = DEFAULT_AGWPE_PORT,
        baud_rate: int = DEFAULT_BAUD_RATE,
        overwrite: bool = False,
    ) -> Path:
        """Generate and write Direwolf configuration file.

        Args:
            callsign: Amateur radio callsign
            audio_device: ALSA audio device string (None = auto-detect)
            agwpe_port: AGWPE port number (default: 8000)
            baud_rate: Modem baud rate (default: 1200)
            overwrite: Whether to overwrite existing config file

        Returns:
            Path to the written configuration file

        Raises:
            ConfigurationError: If file exists and overwrite is False,
                              or if writing fails
        """
        # Check if file exists
        if self.config_path.exists() and not overwrite:
            raise ConfigurationError(
                f"Configuration file already exists: {self.config_path}. "
                f"Use overwrite=True to replace it"
            )

        # Generate configuration content
        config_content = self.generate_config(
            callsign=callsign,
            audio_device=audio_device,
            agwpe_port=agwpe_port,
            baud_rate=baud_rate,
        )

        # Ensure parent directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write configuration file
        try:
            with open(self.config_path, "w") as f:
                f.write(config_content)

            logger.info(f"Direwolf configuration written to {self.config_path}")
            return self.config_path

        except IOError as e:
            raise ConfigurationError(f"Failed to write configuration file {self.config_path}: {e}")

    def interactive_setup(self) -> Path:
        """Run interactive configuration wizard.

        Returns:
            Path to the written configuration file

        Raises:
            ConfigurationError: If setup fails or is cancelled
        """
        print("\n" + "=" * 60)
        print("Fox BBS - Direwolf Configuration Wizard")
        print("=" * 60)

        # Check if config already exists
        if self.config_path.exists():
            print(f"\nConfiguration file already exists: {self.config_path}")
            try:
                response = input("Do you want to overwrite it? [y/N]: ").strip().lower()
                if response not in ("y", "yes"):
                    print("Configuration cancelled")
                    raise ConfigurationError("User cancelled overwrite")
                overwrite = True
            except (EOFError, KeyboardInterrupt):
                print("\nConfiguration cancelled")
                raise ConfigurationError("User cancelled configuration")
        else:
            overwrite = True

        # Step 1: Get callsign
        print("\n" + "-" * 60)
        print("Step 1: Callsign Configuration")
        print("-" * 60)
        print("Enter your amateur radio callsign with optional SSID")
        print("Examples: W1ABC, W2ASM-10, K6TU-5")
        callsign = self.prompt_for_callsign()
        print(f"✓ Callsign set to: {callsign}")

        # Step 2: Select audio device
        print("\n" + "-" * 60)
        print("Step 2: Audio Device Configuration")
        print("-" * 60)
        print("Detecting audio devices...")
        audio_device = self.prompt_for_audio_device()
        print(f"✓ Audio device set to: {audio_device}")

        # Step 3: Write configuration
        print("\n" + "-" * 60)
        print("Step 3: Writing Configuration")
        print("-" * 60)

        config_file = self.write_config(
            callsign=callsign, audio_device=audio_device, overwrite=overwrite
        )

        print(f"✓ Configuration written to: {config_file}")

        # Step 4: Summary and next steps
        print("\n" + "=" * 60)
        print("Configuration Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print(f"1. Review and customize: {config_file}")
        print("2. Configure PTT (Push-To-Talk) for your hardware")
        print("3. Start Direwolf: direwolf -c config/direwolf.conf")
        print("4. Start Fox BBS: python fox_bbs.py")
        print("\nFor more information, see docs/setup.md")
        print()

        return config_file

    @staticmethod
    def _is_valid_callsign(callsign: str) -> bool:
        """Validate amateur radio callsign format.

        Args:
            callsign: Callsign to validate

        Returns:
            True if valid, False otherwise
        """
        # Basic validation for amateur radio callsigns with optional SSID
        # Format: 1-2 letters, 1 digit, 1-3 letters, optional -SSID
        # Must start with a letter, contain exactly one digit, end with letters
        pattern = r"^[A-Z]{1,2}\d[A-Z]{1,4}(-\d{1,2})?$"
        return bool(re.match(pattern, callsign.upper()))


def run_interactive_setup(config_path: str = "config/direwolf.conf") -> Optional[Path]:
    """Run the interactive Direwolf configuration setup wizard.

    Args:
        config_path: Path where direwolf.conf should be created

    Returns:
        Path to created config file, or None if cancelled

    Raises:
        ConfigurationError: If setup fails
    """
    generator = DirewolfConfigGenerator(config_path)

    try:
        return generator.interactive_setup()
    except ConfigurationError:
        # Error already logged/displayed
        return None
    except Exception as e:
        logger.error(f"Unexpected error during configuration: {e}")
        raise ConfigurationError(f"Configuration failed: {e}")


def ensure_direwolf_config(config_path: str = "config/direwolf.conf") -> bool:
    """Ensure direwolf.conf exists, creating it if needed.

    This function is idempotent - it only creates the config if it doesn't exist.
    If the config file already exists, this function does nothing and returns True.

    Args:
        config_path: Path where direwolf.conf should exist

    Returns:
        True if config exists or was created successfully, False otherwise
    """
    config_file = Path(config_path)

    # If config already exists, we're done
    if config_file.exists():
        logger.debug(f"Direwolf configuration already exists: {config_path}")
        return True

    # Config doesn't exist - check if we're in interactive mode
    if sys.stdin.isatty():
        # Interactive mode - run wizard
        logger.info("Direwolf configuration not found, starting setup wizard...")
        try:
            run_interactive_setup(config_path)
            return config_file.exists()
        except ConfigurationError as e:
            logger.warning(f"Configuration setup cancelled or failed: {e}")
            return False
    else:
        # Non-interactive mode - create default config
        logger.info("Non-interactive mode: creating default Direwolf configuration...")
        try:
            generator = DirewolfConfigGenerator(config_path)

            # Try to detect audio device
            devices = generator.detect_audio_devices()
            audio_device = (
                devices[0].alsa_device if devices else DirewolfConfigGenerator.DEFAULT_AUDIO_DEVICE
            )

            # Create default config with placeholder callsign
            generator.write_config(
                callsign="N0CALL-0",  # User must change this
                audio_device=audio_device,
                overwrite=False,
            )

            logger.warning(
                f"Created default configuration at {config_path}. "
                f"IMPORTANT: Edit the file and set your callsign!"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to create default configuration: {e}")
            return False
