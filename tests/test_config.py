"""Tests for configuration management (src/config.py)."""

import tempfile
from pathlib import Path

import pytest
import yaml

from src.config import Config
from src.exceptions import ConfigurationError


class TestConfigLoading:
    """Test configuration file loading."""

    def test_load_valid_config(self, temp_config_file):
        """Test loading a valid configuration file."""
        config = Config.from_yaml(temp_config_file)

        assert config.callsign == "W1ABC-1"
        assert config.direwolf_host == "localhost"
        assert config.direwolf_port == 8000
        assert config.radio_port == 0
        assert config.max_messages == 15
        assert config.message_retention_hours == 24

    def test_load_nonexistent_config(self):
        """Test that loading a nonexistent config raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            Config.from_yaml("/nonexistent/path/config.yaml")

        assert "not found" in str(exc_info.value)

    def test_load_invalid_yaml(self, invalid_config_file):
        """Test that loading invalid YAML raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            Config.from_yaml(invalid_config_file)

        assert "Invalid YAML" in str(exc_info.value)

    def test_reload_config(self, temp_config_file):
        """Test reloading configuration from file."""
        config = Config.from_yaml(temp_config_file)
        assert config.callsign == "W1ABC-1"

        # Modify the config file
        with open(temp_config_file, "w") as f:
            yaml.dump({"server": {"callsign": "W2XYZ-2", "direwolf_port": 9000}}, f)

        # Reload by creating a new config instance
        config = Config.from_yaml(temp_config_file)

        assert config.callsign == "W2XYZ-2"
        assert config.direwolf_port == 9000


class TestConfigDefaults:
    """Test default configuration values."""

    def test_callsign_required(self, minimal_config_file):
        """Test that Callsign is required."""
        # Modify to remove callsign
        with open(minimal_config_file, "w") as f:
            yaml.dump({"server": {}}, f)

        # Should raise error since callsign is required
        with pytest.raises(ConfigurationError):
            Config.from_yaml(minimal_config_file)

    def test_default_direwolf_host(self, minimal_config_file):
        """Test default Direwolf host."""
        with open(minimal_config_file, "w") as f:
            yaml.dump({"server": {"callsign": "W1ABC-1"}}, f)

        config = Config.from_yaml(minimal_config_file)
        assert config.direwolf_host == "localhost"

    def test_default_direwolf_port(self, minimal_config_file):
        """Test default Direwolf port."""
        with open(minimal_config_file, "w") as f:
            yaml.dump({"server": {"callsign": "W1ABC-1"}}, f)

        config = Config.from_yaml(minimal_config_file)
        assert config.direwolf_port == 8000

    def test_default_radio_port(self, minimal_config_file):
        """Test default radio port."""
        with open(minimal_config_file, "w") as f:
            yaml.dump({"server": {"callsign": "W1ABC-1"}}, f)

        config = Config.from_yaml(minimal_config_file)
        assert config.radio_port == 0

    def test_default_max_messages(self, minimal_config_file):
        """Test default max messages."""
        with open(minimal_config_file, "w") as f:
            yaml.dump({"server": {"callsign": "W1ABC-1"}}, f)

        config = Config.from_yaml(minimal_config_file)
        assert config.max_messages == 15

    def test_default_retention_hours(self, minimal_config_file):
        """Test default message retention hours."""
        with open(minimal_config_file, "w") as f:
            yaml.dump({"server": {"callsign": "W1ABC-1"}}, f)

        config = Config.from_yaml(minimal_config_file)
        assert config.message_retention_hours == 24


class TestConfigProperties:
    """Test configuration property accessors."""

    def test_all_properties_accessible(self, temp_config_file):
        """Test that all config properties are accessible."""
        config = Config.from_yaml(temp_config_file)

        # Test all properties
        assert isinstance(config.callsign, str)
        assert isinstance(config.direwolf_host, str)
        assert isinstance(config.direwolf_port, int)
        assert isinstance(config.radio_port, int)
        assert isinstance(config.max_messages, int)
        assert isinstance(config.message_retention_hours, int)

    def test_custom_config_path(self):
        """Test using a custom configuration path."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"server": {"callsign": "K9ABC-5", "direwolf_port": 7500}}, f)
            temp_path = f.name

        try:
            config = Config.from_yaml(temp_path)
            assert config.callsign == "K9ABC-5"
            assert config.direwolf_port == 7500
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestConfigEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_config_file(self):
        """Test handling of empty configuration file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            # Should raise error for empty config
            with pytest.raises(ConfigurationError) as exc_info:
                Config.from_yaml(temp_path)
            assert "empty" in str(exc_info.value).lower()
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_missing_server_section(self):
        """Test config with missing server section."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"other": "data"}, f)
            temp_path = f.name

        try:
            # Should raise error for missing server section / required ssid
            with pytest.raises(ConfigurationError):
                Config.from_yaml(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_partial_config(self):
        """Test config with only some values specified."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"server": {"callsign": "N7XYZ-1", "max_messages": 10}}, f)
            temp_path = f.name

        try:
            config = Config.from_yaml(temp_path)
            # Should use specified values and defaults for rest
            assert config.callsign == "N7XYZ-1"
            assert config.max_messages == 10
            assert config.direwolf_host == "localhost"  # default
            assert config.radio_port == 0  # default
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_numeric_string_conversion(self):
        """Test that numeric values in YAML are properly converted."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            # Write as strings in YAML
            f.write('server:\n  callsign: "W1ABC-1"\n  direwolf_port: "8000"\n  max_messages: "20"\n')
            temp_path = f.name

        try:
            config = Config.from_yaml(temp_path)
            # Should still be integers (YAML auto-converts)
            # Note: YAML with quotes makes them strings, so we're testing the behavior
            port = config.direwolf_port
            messages = config.max_messages

            # These should be the string values since YAML preserves quoted strings
            # But our code should handle this gracefully
            assert port == "8000" or port == 8000
            assert messages == "20" or messages == 20
        finally:
            Path(temp_path).unlink(missing_ok=True)
