"""Configuration management for Fox BBS."""

import re
from pathlib import Path
from typing import Any, Dict

import yaml  # type: ignore[import-untyped]

from .exceptions import ConfigurationError


class Config:
    """Manages configuration for the Fox BBS."""

    def __init__(self, config_path: str = "config/fox.yaml"):
        """Initialize configuration from YAML file.

        Args:
            config_path: Path to the configuration YAML file
        """
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from YAML file.

        Raises:
            ConfigurationError: If config file is not found or contains invalid YAML
        """
        try:
            with open(self.config_path, "r") as f:
                loaded_config = yaml.safe_load(f)
                # Handle empty YAML files which return None
                self._config = loaded_config if loaded_config is not None else {}
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}")

        # Validate configuration after loading
        self._validate()

    @property
    def ssid(self) -> str:
        """Get the BBS SSID."""
        return str(self._config.get("server", {}).get("ssid", "W1FOX-1"))

    @property
    def direwolf_host(self) -> str:
        """Get the Direwolf host."""
        return str(self._config.get("server", {}).get("direwolf_host", "localhost"))

    @property
    def direwolf_port(self) -> int:
        """Get the Direwolf port."""
        return int(self._config.get("server", {}).get("direwolf_port", 8000))

    @property
    def radio_port(self) -> int:
        """Get the radio port number."""
        return int(self._config.get("server", {}).get("radio_port", 0))

    @property
    def max_messages(self) -> int:
        """Get the maximum number of messages to display on connect."""
        return int(self._config.get("server", {}).get("max_messages", 15))

    @property
    def message_retention_hours(self) -> int:
        """Get the message retention period in hours."""
        return int(self._config.get("server", {}).get("message_retention_hours", 24))

    def _validate(self) -> None:
        """Validate configuration values.

        Raises:
            ConfigurationError: If configuration values are invalid
        """
        # Validate SSID format (basic amateur radio callsign validation)
        ssid = self.ssid
        if not self._is_valid_callsign(ssid):
            raise ConfigurationError(
                f"Invalid SSID format: {ssid}. "
                f"Must be a valid amateur radio callsign (e.g., W1ABC-1)"
            )

        # Validate port numbers
        if not 1 <= self.direwolf_port <= 65535:
            raise ConfigurationError(
                f"Invalid Direwolf port: {self.direwolf_port}. Must be between 1-65535"
            )

        if not 0 <= self.radio_port <= 255:
            raise ConfigurationError(
                f"Invalid radio port: {self.radio_port}. Must be between 0-255"
            )

        # Validate message settings
        if self.max_messages < 0:
            raise ConfigurationError(f"Invalid max_messages: {self.max_messages}. Must be >= 0")

        if self.message_retention_hours <= 0:
            raise ConfigurationError(
                f"Invalid message_retention_hours: {self.message_retention_hours}. " f"Must be > 0"
            )

    @staticmethod
    def _is_valid_callsign(callsign: str) -> bool:
        """Check if a callsign is valid amateur radio format.

        Args:
            callsign: Callsign to validate

        Returns:
            True if valid, False otherwise
        """
        # Basic validation for amateur radio callsigns with optional SSID
        # Format: 1-2 letters/numbers, 1 digit, 1-3 letters, optional -SSID
        pattern = r"^[A-Z0-9]{1,2}\d[A-Z]{1,3}(-\d{1,2})?$"
        return bool(re.match(pattern, callsign.upper()))
