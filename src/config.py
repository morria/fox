"""Configuration management for Fox BBS."""

import re
from dataclasses import dataclass
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from .exceptions import ConfigurationError


@dataclass
class Config:
    """Configuration for the Fox BBS."""

    callsign: str
    direwolf_host: str = "localhost"
    direwolf_port: int = 8000
    radio_port: int = 0
    max_messages: int = 15
    message_retention_hours: int = 24

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate()

    @classmethod
    def from_yaml(cls, config_path: str = "config/fox.yaml") -> "Config":
        """Load configuration from YAML file.

        Args:
            config_path: Path to the configuration YAML file

        Returns:
            Config instance

        Raises:
            ConfigurationError: If config file is not found or contains invalid YAML
        """
        path = Path(config_path)
        try:
            with open(path, "r") as f:
                loaded_config = yaml.safe_load(f)
                # Handle empty YAML files which return None
                if loaded_config is None:
                    raise ConfigurationError("Configuration file is empty")

                server_config = loaded_config.get("server", {})
                # Convert numeric strings to integers if needed
                if "direwolf_port" in server_config:
                    server_config["direwolf_port"] = int(server_config["direwolf_port"])
                if "radio_port" in server_config:
                    server_config["radio_port"] = int(server_config["radio_port"])
                if "max_messages" in server_config:
                    server_config["max_messages"] = int(server_config["max_messages"])
                if "message_retention_hours" in server_config:
                    server_config["message_retention_hours"] = int(
                        server_config["message_retention_hours"]
                    )
                return cls(**server_config)

        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {path}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}")
        except TypeError as e:
            raise ConfigurationError(f"Invalid configuration structure: {e}")

    def _validate(self) -> None:
        """Validate configuration values.

        Raises:
            ConfigurationError: If configuration values are invalid
        """
        # Validate callsign format (basic amateur radio callsign validation)
        if not self._is_valid_callsign(self.callsign):
            raise ConfigurationError(
                f"Invalid callsign format: {self.callsign}. "
                f"Must be a valid amateur radio callsign with SSID (e.g., W1ABC-1)"
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
        # Format: 1-2 letters, 1 digit, 1-3 letters, optional -SSID
        # Must start with a letter, contain exactly one digit, end with letters
        pattern = r"^[A-Z]{1,2}\d[A-Z]{1,4}(-\d{1,2})?$"
        return bool(re.match(pattern, callsign.upper()))
