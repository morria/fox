"""Process management for Fox BBS and Direwolf integration.

This module provides functionality to manage Direwolf as a subprocess,
monitor its health, and coordinate graceful shutdown of both processes.
"""

import logging
import socket
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class DirewolfProcess:
    """Manages Direwolf TNC process lifecycle."""

    def __init__(
        self,
        config_path: str = "config/direwolf.conf",
        host: str = "localhost",
        port: int = 8000,
        startup_timeout: float = 10.0,
    ):
        """Initialize Direwolf process manager.

        Args:
            config_path: Path to Direwolf configuration file
            host: Host where Direwolf AGWPE will listen
            port: Port where Direwolf AGWPE will listen
            startup_timeout: Seconds to wait for Direwolf to start
        """
        self.config_path = Path(config_path)
        self.host = host
        self.port = port
        self.startup_timeout = startup_timeout
        self.process: Optional[subprocess.Popen] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._should_monitor = False
        self._on_exit_callback: Optional[Callable[[], None]] = None

    def is_port_listening(self) -> bool:
        """Check if the AGWPE port is listening.

        Returns:
            True if port is listening, False otherwise
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1.0)
                result = sock.connect_ex((self.host, self.port))
                return result == 0
        except (socket.error, OSError) as e:
            logger.debug(f"Port check failed: {e}")
            return False

    def is_running(self) -> bool:
        """Check if the Direwolf process is running.

        Returns:
            True if process is running, False otherwise
        """
        if self.process is None:
            return False

        # Check if process has terminated
        return self.process.poll() is None

    def start(self, on_exit: Optional[Callable[[], None]] = None) -> bool:
        """Start Direwolf process.

        Args:
            on_exit: Optional callback to invoke when process exits

        Returns:
            True if started successfully, False otherwise
        """
        # Check if port is already listening (Direwolf already running elsewhere)
        if self.is_port_listening():
            logger.info(
                f"Direwolf AGWPE port {self.port} is already listening "
                f"(external Direwolf instance)"
            )
            return True

        # Check if we already have a process running
        if self.is_running():
            logger.debug("Direwolf process is already running")
            return True

        # Check if config file exists
        if not self.config_path.exists():
            logger.error(f"Direwolf configuration not found: {self.config_path}")
            return False

        # Find direwolf wrapper script
        wrapper_script = Path(__file__).parent.parent / "direwolf"

        if not wrapper_script.exists():
            logger.error(f"Direwolf wrapper script not found: {wrapper_script}")
            return False

        logger.info(f"Starting Direwolf with config: {self.config_path}")

        try:
            # Start Direwolf process
            self.process = subprocess.Popen(
                [str(wrapper_script), "-c", str(self.config_path), "--skip-config-check"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,  # Line buffered
            )

            # Wait for port to start listening
            logger.info(f"Waiting for Direwolf AGWPE on port {self.port}...")
            start_time = time.time()

            while time.time() - start_time < self.startup_timeout:
                # Check if process died
                if self.process.poll() is not None:
                    logger.error("Direwolf process terminated during startup")
                    self._log_process_output()
                    return False

                # Check if port is listening
                if self.is_port_listening():
                    logger.info(f"✓ Direwolf AGWPE ready on port {self.port}")

                    # Store exit callback
                    self._on_exit_callback = on_exit

                    # Start monitoring thread
                    self._should_monitor = True
                    self._monitor_thread = threading.Thread(
                        target=self._monitor_process, daemon=True
                    )
                    self._monitor_thread.start()

                    return True

                time.sleep(0.5)

            # Timeout reached
            logger.error(
                f"Timeout waiting for Direwolf to start " f"(waited {self.startup_timeout}s)"
            )
            self._log_process_output()
            self.stop()
            return False

        except Exception as e:
            logger.error(f"Failed to start Direwolf: {e}")
            if self.process:
                self.stop()
            return False

    def stop(self) -> None:
        """Stop Direwolf process gracefully."""
        if not self.process:
            return

        logger.info("Stopping Direwolf...")

        # Stop monitoring
        self._should_monitor = False

        # Try graceful shutdown first
        try:
            if self.process.poll() is None:
                self.process.terminate()

                # Wait up to 3 seconds for graceful shutdown
                try:
                    self.process.wait(timeout=3.0)
                    logger.info("Direwolf stopped gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if still running
                    logger.warning("Direwolf did not stop gracefully, forcing kill")
                    self.process.kill()
                    self.process.wait(timeout=1.0)
                    logger.info("Direwolf killed")

        except Exception as e:
            logger.error(f"Error stopping Direwolf: {e}")

        finally:
            self.process = None

    def _monitor_process(self) -> None:
        """Monitor Direwolf process and invoke callback on exit."""
        while self._should_monitor and self.process:
            # Check if process has terminated
            if self.process.poll() is not None:
                exit_code = self.process.returncode
                logger.error(f"Direwolf process terminated unexpectedly (exit code: {exit_code})")
                self._log_process_output()

                # Invoke exit callback if set
                if self._on_exit_callback:
                    try:
                        self._on_exit_callback()
                    except Exception as e:
                        logger.error(f"Error in Direwolf exit callback: {e}")

                break

            time.sleep(1.0)

    def _log_process_output(self) -> None:
        """Log any remaining output from the process."""
        if not self.process or not self.process.stdout:
            return

        try:
            # Read any remaining output (non-blocking)
            lines = []
            while True:
                line = self.process.stdout.readline()
                if not line:
                    break
                lines.append(line.rstrip())

            if lines:
                logger.debug("Direwolf output:")
                for line in lines[-20:]:  # Last 20 lines
                    logger.debug(f"  {line}")

        except Exception as e:
            logger.debug(f"Error reading process output: {e}")


class ProcessCoordinator:
    """Coordinates Fox BBS and Direwolf processes."""

    def __init__(
        self,
        direwolf_manager: DirewolfProcess,
        auto_shutdown: bool = True,
    ):
        """Initialize process coordinator.

        Args:
            direwolf_manager: DirewolfProcess instance to manage
            auto_shutdown: If True, shutdown Fox BBS when Direwolf dies
        """
        self.direwolf = direwolf_manager
        self.auto_shutdown = auto_shutdown
        self._shutdown_handler: Optional[Callable[[], None]] = None
        self._shutting_down = False

    def set_shutdown_handler(self, handler: Callable[[], None]) -> None:
        """Set callback to invoke for Fox BBS shutdown.

        Args:
            handler: Callable to invoke for shutdown
        """
        self._shutdown_handler = handler

    def start_direwolf(self) -> bool:
        """Start Direwolf with monitoring.

        Returns:
            True if started successfully, False otherwise
        """
        return self.direwolf.start(on_exit=self._handle_direwolf_exit)

    def stop_all(self) -> None:
        """Stop all managed processes."""
        if self._shutting_down:
            return

        self._shutting_down = True
        logger.info("Stopping all processes...")

        # Stop Direwolf
        self.direwolf.stop()

        logger.info("All processes stopped")

    def _handle_direwolf_exit(self) -> None:
        """Handle unexpected Direwolf process exit."""
        if self._shutting_down:
            return

        logger.error("Direwolf process died unexpectedly")

        if self.auto_shutdown:
            logger.error("Shutting down Fox BBS due to Direwolf failure")

            # Invoke shutdown handler if set
            if self._shutdown_handler:
                try:
                    self._shutdown_handler()
                except Exception as e:
                    logger.error(f"Error in shutdown handler: {e}")


def check_port_available(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if a TCP port is available (not listening).

    Args:
        host: Hostname or IP address
        port: Port number
        timeout: Connection timeout in seconds

    Returns:
        True if port is available (nothing listening), False if port is in use
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            # Port is available if connection fails
            return result != 0
    except (socket.error, OSError):
        # Error checking port, assume unavailable
        return False
