"""Tests for process manager module."""

import socket
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from src.process_manager import (
    DirewolfProcess,
    ProcessCoordinator,
    check_port_available,
)


class TestCheckPortAvailable:
    """Tests for check_port_available function."""

    def test_port_available(self):
        """Test checking an available port."""
        # Use a high port that's unlikely to be in use
        result = check_port_available("127.0.0.1", 59999, timeout=0.1)
        assert result is True

    def test_port_unavailable(self):
        """Test checking a port that's in use."""
        # Create a listening socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))  # Bind to any available port
            sock.listen(1)
            port = sock.getsockname()[1]

            # Port should be unavailable
            result = check_port_available("127.0.0.1", port, timeout=0.1)
            assert result is False


class TestDirewolfProcess:
    """Tests for DirewolfProcess class."""

    def test_initialization(self):
        """Test initializing DirewolfProcess."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "direwolf.conf"

            proc = DirewolfProcess(
                config_path=str(config_path),
                host="localhost",
                port=8000,
                startup_timeout=5.0,
            )

            assert proc.config_path == config_path
            assert proc.host == "localhost"
            assert proc.port == 8000
            assert proc.startup_timeout == 5.0
            assert proc.process is None

    def test_is_port_listening_false(self):
        """Test checking port when nothing is listening."""
        proc = DirewolfProcess(port=59999)
        assert proc.is_port_listening() is False

    def test_is_port_listening_true(self):
        """Test checking port when something is listening."""
        # Create a listening socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            sock.listen(1)
            port = sock.getsockname()[1]

            proc = DirewolfProcess(host="127.0.0.1", port=port)
            assert proc.is_port_listening() is True

    def test_is_running_no_process(self):
        """Test is_running when no process exists."""
        proc = DirewolfProcess()
        assert proc.is_running() is False

    def test_is_running_with_process(self):
        """Test is_running with an active process."""
        proc = DirewolfProcess()

        # Create a mock process
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process still running
        proc.process = mock_process

        assert proc.is_running() is True

    def test_is_running_terminated_process(self):
        """Test is_running with a terminated process."""
        proc = DirewolfProcess()

        # Create a mock terminated process
        mock_process = Mock()
        mock_process.poll.return_value = 0  # Process terminated
        proc.process = mock_process

        assert proc.is_running() is False

    def test_start_port_already_listening(self):
        """Test start when port is already listening."""
        # Create a listening socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            sock.listen(1)
            port = sock.getsockname()[1]

            proc = DirewolfProcess(host="127.0.0.1", port=port)
            result = proc.start()

            assert result is True
            assert proc.process is None  # No process started

    def test_start_config_missing(self):
        """Test start when config file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "missing.conf"

            proc = DirewolfProcess(config_path=str(config_path))
            result = proc.start()

            assert result is False
            assert proc.process is None

    @patch("subprocess.Popen")
    def test_start_wrapper_missing(self, mock_popen):
        """Test start when direwolf wrapper script is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "direwolf.conf"
            config_path.write_text("# Test config\n")

            proc = DirewolfProcess(config_path=str(config_path))

            # Mock the wrapper script path check
            with patch.object(Path, "exists") as mock_exists:
                # Config exists, wrapper doesn't
                mock_exists.side_effect = lambda: str(self) == str(config_path)

                result = proc.start()

                assert result is False

    def test_stop_no_process(self):
        """Test stop when no process exists."""
        proc = DirewolfProcess()
        proc.stop()  # Should not raise

        assert proc.process is None

    def test_stop_with_process(self):
        """Test stop with an active process."""
        proc = DirewolfProcess()

        # Create a mock process
        mock_process = Mock()
        mock_process.poll.return_value = None  # Running
        mock_process.terminate.return_value = None
        mock_process.wait.return_value = None
        proc.process = mock_process

        proc.stop()

        # Should have called terminate and wait
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called()
        assert proc.process is None

    def test_stop_force_kill(self):
        """Test stop with force kill when graceful shutdown fails."""
        proc = DirewolfProcess()

        # Create a mock process that doesn't terminate gracefully
        mock_process = Mock()
        mock_process.poll.return_value = None  # Running
        mock_process.terminate.return_value = None
        mock_process.wait.side_effect = [
            subprocess.TimeoutExpired("cmd", 3.0),  # First wait times out
            None,  # Second wait succeeds
        ]
        mock_process.kill.return_value = None
        proc.process = mock_process

        proc.stop()

        # Should have called terminate, then kill
        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()
        assert proc.process is None


class TestProcessCoordinator:
    """Tests for ProcessCoordinator class."""

    def test_initialization(self):
        """Test initializing ProcessCoordinator."""
        mock_direwolf = Mock(spec=DirewolfProcess)

        coordinator = ProcessCoordinator(direwolf_manager=mock_direwolf, auto_shutdown=True)

        assert coordinator.direwolf is mock_direwolf
        assert coordinator.auto_shutdown is True
        assert coordinator._shutdown_handler is None

    def test_set_shutdown_handler(self):
        """Test setting shutdown handler."""
        mock_direwolf = Mock(spec=DirewolfProcess)
        coordinator = ProcessCoordinator(direwolf_manager=mock_direwolf)

        handler = Mock()
        coordinator.set_shutdown_handler(handler)

        assert coordinator._shutdown_handler is handler

    def test_start_direwolf(self):
        """Test starting Direwolf through coordinator."""
        mock_direwolf = Mock(spec=DirewolfProcess)
        mock_direwolf.start.return_value = True

        coordinator = ProcessCoordinator(direwolf_manager=mock_direwolf)
        result = coordinator.start_direwolf()

        assert result is True
        mock_direwolf.start.assert_called_once()

    def test_start_direwolf_failure(self):
        """Test starting Direwolf when it fails."""
        mock_direwolf = Mock(spec=DirewolfProcess)
        mock_direwolf.start.return_value = False

        coordinator = ProcessCoordinator(direwolf_manager=mock_direwolf)
        result = coordinator.start_direwolf()

        assert result is False

    def test_stop_all(self):
        """Test stopping all processes."""
        mock_direwolf = Mock(spec=DirewolfProcess)

        coordinator = ProcessCoordinator(direwolf_manager=mock_direwolf)
        coordinator.stop_all()

        mock_direwolf.stop.assert_called_once()

    def test_stop_all_idempotent(self):
        """Test that stop_all can be called multiple times safely."""
        mock_direwolf = Mock(spec=DirewolfProcess)

        coordinator = ProcessCoordinator(direwolf_manager=mock_direwolf)
        coordinator.stop_all()
        coordinator.stop_all()  # Second call

        # Should only call stop once (idempotent)
        mock_direwolf.stop.assert_called_once()

    def test_handle_direwolf_exit_with_auto_shutdown(self):
        """Test handling Direwolf exit with auto_shutdown enabled."""
        mock_direwolf = Mock(spec=DirewolfProcess)

        coordinator = ProcessCoordinator(direwolf_manager=mock_direwolf, auto_shutdown=True)

        # Set up shutdown handler
        shutdown_handler = Mock()
        coordinator.set_shutdown_handler(shutdown_handler)

        # Simulate Direwolf exit
        coordinator._handle_direwolf_exit()

        # Shutdown handler should have been called
        shutdown_handler.assert_called_once()

    def test_handle_direwolf_exit_without_auto_shutdown(self):
        """Test handling Direwolf exit with auto_shutdown disabled."""
        mock_direwolf = Mock(spec=DirewolfProcess)

        coordinator = ProcessCoordinator(direwolf_manager=mock_direwolf, auto_shutdown=False)

        # Set up shutdown handler
        shutdown_handler = Mock()
        coordinator.set_shutdown_handler(shutdown_handler)

        # Simulate Direwolf exit
        coordinator._handle_direwolf_exit()

        # Shutdown handler should NOT have been called
        shutdown_handler.assert_not_called()

    def test_handle_direwolf_exit_no_handler(self):
        """Test handling Direwolf exit without shutdown handler set."""
        mock_direwolf = Mock(spec=DirewolfProcess)

        coordinator = ProcessCoordinator(direwolf_manager=mock_direwolf, auto_shutdown=True)

        # No shutdown handler set
        # This should not raise an exception
        coordinator._handle_direwolf_exit()

    def test_handle_direwolf_exit_during_shutdown(self):
        """Test that exit handler doesn't run during intentional shutdown."""
        mock_direwolf = Mock(spec=DirewolfProcess)

        coordinator = ProcessCoordinator(direwolf_manager=mock_direwolf, auto_shutdown=True)

        # Set up shutdown handler
        shutdown_handler = Mock()
        coordinator.set_shutdown_handler(shutdown_handler)

        # Start shutdown
        coordinator.stop_all()

        # Simulate Direwolf exit during shutdown
        coordinator._handle_direwolf_exit()

        # Shutdown handler should NOT be called (already shutting down)
        shutdown_handler.assert_not_called()


class TestProcessManagerIntegration:
    """Integration tests for process manager."""

    def test_direwolf_process_lifecycle(self):
        """Test full lifecycle of DirewolfProcess (without actual Direwolf)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "direwolf.conf"
            config_path.write_text("# Test config\n")

            proc = DirewolfProcess(config_path=str(config_path), port=59998)

            # Initially not running
            assert not proc.is_running()
            assert not proc.is_port_listening()

            # Can't actually start Direwolf in tests, so we'll just test stop
            proc.stop()  # Should handle gracefully

            assert not proc.is_running()

    def test_coordinator_lifecycle(self):
        """Test full lifecycle of ProcessCoordinator."""
        mock_direwolf = Mock(spec=DirewolfProcess)
        mock_direwolf.start.return_value = True

        coordinator = ProcessCoordinator(direwolf_manager=mock_direwolf, auto_shutdown=True)

        # Start Direwolf
        result = coordinator.start_direwolf()
        assert result is True

        # Stop all
        coordinator.stop_all()

        mock_direwolf.stop.assert_called_once()
