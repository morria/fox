"""Configuration management for Fox BBS."""
import yaml
from pathlib import Path
from typing import Dict, Any


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
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")

    @property
    def ssid(self) -> str:
        """Get the BBS SSID."""
        return self._config.get('server', {}).get('ssid', 'FOX-1')

    @property
    def direwolf_host(self) -> str:
        """Get the Direwolf host."""
        return self._config.get('server', {}).get('direwolf_host', 'localhost')

    @property
    def direwolf_port(self) -> int:
        """Get the Direwolf port."""
        return self._config.get('server', {}).get('direwolf_port', 8000)

    @property
    def radio_port(self) -> int:
        """Get the radio port number."""
        return self._config.get('server', {}).get('radio_port', 0)

    @property
    def max_messages(self) -> int:
        """Get the maximum number of messages to display on connect."""
        return self._config.get('server', {}).get('max_messages', 15)

    @property
    def message_retention_hours(self) -> int:
        """Get the message retention period in hours."""
        return self._config.get('server', {}).get('message_retention_hours', 24)
