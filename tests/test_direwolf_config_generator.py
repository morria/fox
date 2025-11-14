"""Tests for Direwolf configuration generator."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.direwolf_config_generator import (
    AudioDevice,
    DirewolfConfigGenerator,
    ensure_direwolf_config,
)
from src.exceptions import ConfigurationError


class TestAudioDevice:
    """Tests for AudioDevice class."""

    def test_audio_device_creation(self):
        """Test creating an audio device."""
        device = AudioDevice(card=1, device=0, name="USB Audio")

        assert device.card == 1
        assert device.device == 0
        assert device.name == "USB Audio"
        assert device.description == "USB Audio"

    def test_audio_device_with_description(self):
        """Test creating an audio device with custom description."""
        device = AudioDevice(
            card=1, device=0, name="USB Audio", description="USB Audio Device - Codec"
        )

        assert device.description == "USB Audio Device - Codec"

    def test_alsa_device_string(self):
        """Test ALSA device string generation."""
        device = AudioDevice(card=1, device=0, name="USB Audio")

        assert device.alsa_device == "plughw:1,0"

    def test_audio_device_string_representation(self):
        """Test string representation of audio device."""
        device = AudioDevice(card=2, device=1, name="USB Audio", description="USB Audio Device")

        assert str(device) == "Card 2, Device 1: USB Audio Device"


class TestDirewolfConfigGenerator:
    """Tests for DirewolfConfigGenerator class."""

    def test_generator_initialization(self):
        """Test initializing the generator."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "direwolf.conf"
            generator = DirewolfConfigGenerator(str(config_path))

            assert generator.config_path == config_path
            assert generator.audio_devices == []

    def test_parse_arecord_output(self):
        """Test parsing arecord output."""
        arecord_output = """**** List of CAPTURE Hardware Devices ****
card 0: PCH [HDA Intel PCH], device 0: ALC269VC Analog [ALC269VC Analog]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
card 1: Device [USB Audio Device], device 0: USB Audio [USB Audio]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
card 2: CODEC [USB Audio CODEC], device 0: USB Audio [USB Audio]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
"""

        generator = DirewolfConfigGenerator()
        devices = generator._parse_arecord_output(arecord_output)

        assert len(devices) == 3
        assert devices[0].card == 0
        assert devices[0].device == 0
        assert "PCH" in devices[0].name

        assert devices[1].card == 1
        assert devices[1].device == 0
        assert "Device" in devices[1].name

        assert devices[2].card == 2
        assert devices[2].device == 0
        assert "CODEC" in devices[2].name

    def test_parse_arecord_output_empty(self):
        """Test parsing empty arecord output."""
        generator = DirewolfConfigGenerator()
        devices = generator._parse_arecord_output("")

        assert devices == []

    def test_detect_via_proc_asound(self):
        """Test detecting devices via /proc/asound/cards."""
        proc_asound_content = """ 0 [PCH            ]: HDA-Intel - HDA Intel PCH
                      HDA Intel PCH at 0xf7c00000 irq 128
 1 [Device         ]: USB-Audio - USB Audio Device
                      USB Audio Device at usb-0000:00:14.0-1
 2 [CODEC          ]: USB-Audio - USB Audio CODEC
                      C-Media USB Audio Device
"""

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=proc_asound_content)):
                generator = DirewolfConfigGenerator()
                devices = generator._detect_via_proc_asound()

                assert len(devices) == 3
                assert devices[0].card == 0
                assert "PCH" in devices[0].name

                assert devices[1].card == 1
                assert "Device" in devices[1].name

                assert devices[2].card == 2
                assert "CODEC" in devices[2].name

    def test_detect_audio_devices_with_arecord(self):
        """Test detecting audio devices using arecord."""
        arecord_output = """card 1: Device [USB Audio Device], device 0: USB Audio [USB Audio]"""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=arecord_output)

            generator = DirewolfConfigGenerator()
            devices = generator.detect_audio_devices()

            assert len(devices) > 0
            assert generator.audio_devices == devices

    def test_detect_audio_devices_fallback(self):
        """Test audio device detection fallback when arecord fails."""
        proc_asound_content = """ 1 [Device         ]: USB-Audio - USB Audio Device
                      USB Audio Device
"""

        with patch("subprocess.run", side_effect=FileNotFoundError()):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("builtins.open", mock_open(read_data=proc_asound_content)):
                    generator = DirewolfConfigGenerator()
                    devices = generator.detect_audio_devices()

                    assert len(devices) > 0

    def test_detect_audio_devices_none_found(self):
        """Test when no audio devices are found."""
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            with patch("pathlib.Path.exists", return_value=False):
                generator = DirewolfConfigGenerator()
                devices = generator.detect_audio_devices()

                assert devices == []

    def test_validate_callsign_valid(self):
        """Test validating valid callsigns."""
        generator = DirewolfConfigGenerator()

        assert generator._is_valid_callsign("W1ABC")
        assert generator._is_valid_callsign("W2ASM-10")
        assert generator._is_valid_callsign("K6TU-5")
        assert generator._is_valid_callsign("N0CALL")
        assert generator._is_valid_callsign("AA1A")
        assert generator._is_valid_callsign("KG4XYZ-15")

    def test_validate_callsign_invalid(self):
        """Test validating invalid callsigns."""
        generator = DirewolfConfigGenerator()

        assert not generator._is_valid_callsign("")
        assert not generator._is_valid_callsign("INVALID")
        assert not generator._is_valid_callsign("W1")
        assert not generator._is_valid_callsign("123ABC")
        assert not generator._is_valid_callsign("W1ABC-")
        assert not generator._is_valid_callsign("W1ABC-100")  # SSID too large

    def test_generate_config(self):
        """Test generating configuration content."""
        generator = DirewolfConfigGenerator()

        config = generator.generate_config(
            callsign="W1ABC-10",
            audio_device="plughw:1,0",
            agwpe_port=8000,
            baud_rate=1200,
        )

        assert "MYCALL W1ABC-10" in config
        assert "ADEVICE plughw:1,0" in config
        assert "AGWPORT 8000" in config
        assert "MODEM 1200" in config
        assert "Fox BBS" in config  # Generated by Fox BBS comment

    def test_generate_config_invalid_callsign(self):
        """Test generating config with invalid callsign raises error."""
        generator = DirewolfConfigGenerator()

        with pytest.raises(ConfigurationError) as exc_info:
            generator.generate_config(callsign="INVALID")

        assert "Invalid callsign" in str(exc_info.value)

    def test_generate_config_default_audio_device(self):
        """Test generating config with default audio device."""
        generator = DirewolfConfigGenerator()

        config = generator.generate_config(callsign="W1ABC")

        # Should use default device when audio_device is None
        assert "ADEVICE plughw:1,0" in config

    def test_write_config(self):
        """Test writing configuration file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "direwolf.conf"
            generator = DirewolfConfigGenerator(str(config_path))

            result_path = generator.write_config(callsign="W1ABC-10", audio_device="plughw:1,0")

            assert result_path == config_path
            assert config_path.exists()

            # Check content
            content = config_path.read_text()
            assert "MYCALL W1ABC-10" in content
            assert "ADEVICE plughw:1,0" in content

    def test_write_config_create_directory(self):
        """Test that write_config creates parent directory if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "subdir" / "direwolf.conf"
            generator = DirewolfConfigGenerator(str(config_path))

            generator.write_config(callsign="W1ABC", audio_device="plughw:1,0")

            assert config_path.exists()
            assert config_path.parent.exists()

    def test_write_config_overwrite_false(self):
        """Test that write_config raises error when file exists and overwrite=False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "direwolf.conf"
            generator = DirewolfConfigGenerator(str(config_path))

            # Create initial config
            generator.write_config(callsign="W1ABC", audio_device="plughw:1,0")

            # Try to write again without overwrite
            with pytest.raises(ConfigurationError) as exc_info:
                generator.write_config(callsign="W2DEF", audio_device="plughw:2,0", overwrite=False)

            assert "already exists" in str(exc_info.value)

    def test_write_config_overwrite_true(self):
        """Test that write_config overwrites when overwrite=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "direwolf.conf"
            generator = DirewolfConfigGenerator(str(config_path))

            # Create initial config
            generator.write_config(callsign="W1ABC", audio_device="plughw:1,0")

            # Overwrite with new config
            generator.write_config(callsign="W2DEF", audio_device="plughw:2,0", overwrite=True)

            # Check that new content is present
            content = config_path.read_text()
            assert "MYCALL W2DEF" in content
            assert "ADEVICE plughw:2,0" in content

    def test_write_config_invalid_callsign(self):
        """Test that write_config raises error for invalid callsign."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "direwolf.conf"
            generator = DirewolfConfigGenerator(str(config_path))

            with pytest.raises(ConfigurationError) as exc_info:
                generator.write_config(callsign="INVALID")

            assert "Invalid callsign" in str(exc_info.value)


class TestEnsureDirewolfConfig:
    """Tests for ensure_direwolf_config function."""

    def test_config_exists(self):
        """Test when config file already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "direwolf.conf"
            config_path.write_text("# Existing config\n")

            result = ensure_direwolf_config(str(config_path))

            assert result is True
            # Content should be unchanged
            assert config_path.read_text() == "# Existing config\n"

    def test_config_missing_non_interactive(self):
        """Test creating default config in non-interactive mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "direwolf.conf"

            # Mock stdin as non-TTY (non-interactive)
            with patch("sys.stdin.isatty", return_value=False):
                with patch(
                    "src.direwolf_config_generator.DirewolfConfigGenerator.detect_audio_devices"
                ) as mock_detect:
                    # Mock no devices detected
                    mock_detect.return_value = []

                    result = ensure_direwolf_config(str(config_path))

                    assert result is True
                    assert config_path.exists()

                    # Check that placeholder callsign is in config
                    content = config_path.read_text()
                    assert "N0CALL-0" in content

    def test_config_missing_interactive_cancelled(self):
        """Test when user cancels interactive setup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "direwolf.conf"

            # Mock stdin as TTY (interactive)
            with patch("sys.stdin.isatty", return_value=True):
                with patch("src.direwolf_config_generator.run_interactive_setup") as mock_setup:
                    # Simulate user cancellation
                    mock_setup.side_effect = ConfigurationError("User cancelled")

                    result = ensure_direwolf_config(str(config_path))

                    assert result is False
                    assert not config_path.exists()


class TestConfigGeneratorEdgeCases:
    """Tests for edge cases and error handling."""

    def test_parse_arecord_malformed_output(self):
        """Test parsing malformed arecord output."""
        malformed_output = """This is not valid output
Some random text
card without proper format
"""

        generator = DirewolfConfigGenerator()
        devices = generator._parse_arecord_output(malformed_output)

        # Should handle gracefully and return empty list
        assert devices == []

    def test_detect_audio_devices_timeout(self):
        """Test handling timeout when running arecord."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = TimeoutError()

            with patch("pathlib.Path.exists", return_value=False):
                generator = DirewolfConfigGenerator()
                devices = generator.detect_audio_devices()

                # Should handle gracefully and return empty list
                assert devices == []

    def test_write_config_permission_error(self):
        """Test handling permission error when writing config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "direwolf.conf"
            generator = DirewolfConfigGenerator(str(config_path))

            with patch("builtins.open", side_effect=PermissionError()):
                with pytest.raises(ConfigurationError) as exc_info:
                    generator.write_config(callsign="W1ABC")

                assert "Failed to write" in str(exc_info.value)

    def test_callsign_case_insensitive(self):
        """Test that callsigns are converted to uppercase."""
        generator = DirewolfConfigGenerator()

        config = generator.generate_config(callsign="w1abc-10")

        # Should be converted to uppercase
        assert "MYCALL W1ABC-10" in config
