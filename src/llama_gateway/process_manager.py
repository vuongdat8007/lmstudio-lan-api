"""Process manager for llama-server subprocess control."""

import asyncio
import signal
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum

import httpx
import aiofiles

from .command_builder import build_llama_server_command, command_to_string
from .logging_config import get_logger
from .model_registry import Model
from .settings import settings

logger = get_logger("process_manager")


class ProcessStatus(str, Enum):
    """Process status enum."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class LlamaServerManager:
    """Manager for llama-server subprocess."""

    def __init__(self):
        """Initialize the process manager."""
        self.process: Optional[asyncio.subprocess.Process] = None
        self.current_model: Optional[Model] = None
        self.status: ProcessStatus = ProcessStatus.STOPPED
        self.started_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self._log_tasks: List[asyncio.Task] = []
        self._health_check_task: Optional[asyncio.Task] = None
        self._stdout_buffer: List[str] = []
        self._stderr_buffer: List[str] = []
        self._max_log_lines = 1000

        # Ensure log directory exists
        log_dir = Path(settings.LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)

    async def start(self, model: Model) -> None:
        """
        Start llama-server with the given model.

        Args:
            model: Model configuration

        Raises:
            RuntimeError: If llama-server is already running or fails to start
        """
        if self.status not in [ProcessStatus.STOPPED, ProcessStatus.ERROR]:
            raise RuntimeError(f"Cannot start: current status is {self.status}")

        logger.info(f"Starting llama-server with model: {model.model_id}")
        self.status = ProcessStatus.STARTING
        self.current_model = model
        self.error_message = None

        try:
            # Build command
            cmd = build_llama_server_command(model)
            cmd_str = command_to_string(cmd)
            logger.info(f"Command: {cmd_str}")

            # Start process
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=None if not hasattr(signal, 'SIGTERM') else lambda: signal.signal(signal.SIGTERM, signal.SIG_DFL)
            )

            self.started_at = datetime.utcnow()
            logger.info(f"Process started with PID: {self.process.pid}")

            # Start log capture tasks
            self._start_log_capture()

            # Wait for health check
            await self._wait_for_health()

            self.status = ProcessStatus.RUNNING
            logger.info(f"llama-server is running and healthy")

        except Exception as e:
            self.status = ProcessStatus.ERROR
            self.error_message = str(e)
            logger.exception(f"Failed to start llama-server: {e}")
            await self._cleanup_process()
            raise RuntimeError(f"Failed to start llama-server: {e}")

    async def stop(self, force: bool = False) -> None:
        """
        Stop llama-server gracefully or forcefully.

        Args:
            force: If True, send SIGKILL immediately

        Raises:
            RuntimeError: If stopping fails
        """
        if self.status == ProcessStatus.STOPPED:
            logger.info("llama-server already stopped")
            return

        logger.info(f"Stopping llama-server (force={force})")
        self.status = ProcessStatus.STOPPING

        try:
            if self.process is None:
                self.status = ProcessStatus.STOPPED
                return

            if force:
                # Forceful shutdown
                self.process.kill()
                await asyncio.wait_for(self.process.wait(), timeout=5)
            else:
                # Graceful shutdown
                self.process.terminate()
                try:
                    await asyncio.wait_for(
                        self.process.wait(),
                        timeout=settings.SHUTDOWN_TIMEOUT
                    )
                except asyncio.TimeoutError:
                    logger.warning("Graceful shutdown timeout, forcing kill")
                    self.process.kill()
                    await asyncio.wait_for(self.process.wait(), timeout=5)

            logger.info("llama-server stopped successfully")
            self.status = ProcessStatus.STOPPED

        except Exception as e:
            logger.exception(f"Error stopping llama-server: {e}")
            self.status = ProcessStatus.ERROR
            self.error_message = str(e)
            raise RuntimeError(f"Failed to stop llama-server: {e}")

        finally:
            await self._cleanup_process()

    async def restart(self) -> None:
        """
        Restart llama-server with the current model.

        Raises:
            RuntimeError: If no model is loaded or restart fails
        """
        if self.current_model is None:
            raise RuntimeError("Cannot restart: no model loaded")

        logger.info(f"Restarting llama-server with model: {self.current_model.model_id}")
        model = self.current_model
        await self.stop()
        await self.start(model)

    async def is_running(self) -> bool:
        """
        Check if llama-server process is running.

        Returns:
            True if running, False otherwise
        """
        if self.process is None:
            return False

        return self.process.returncode is None

    async def is_healthy(self) -> bool:
        """
        Check if llama-server is healthy via health endpoint.

        Returns:
            True if healthy, False otherwise
        """
        if not await self.is_running():
            return False

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{settings.llama_server_base_url}/health"
                )
                return response.status_code == 200
        except Exception as e:
            logger.debug(f"Health check failed: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status information.

        Returns:
            Dictionary with status information
        """
        return {
            "status": self.status.value,
            "model": self.current_model.model_dump() if self.current_model else None,
            "started_at": self.started_at.isoformat() + "Z" if self.started_at else None,
            "uptime_seconds": (
                int((datetime.utcnow() - self.started_at).total_seconds())
                if self.started_at and self.status == ProcessStatus.RUNNING
                else None
            ),
            "error_message": self.error_message,
            "pid": self.process.pid if self.process else None,
        }

    def get_logs(self, lines: int = 50) -> Dict[str, List[str]]:
        """
        Get recent log lines.

        Args:
            lines: Number of lines to return

        Returns:
            Dictionary with stdout and stderr logs
        """
        return {
            "stdout": self._stdout_buffer[-lines:] if self._stdout_buffer else [],
            "stderr": self._stderr_buffer[-lines:] if self._stderr_buffer else [],
        }

    async def _wait_for_health(self) -> None:
        """
        Wait for llama-server to become healthy.

        Raises:
            RuntimeError: If health check times out
        """
        logger.info("Waiting for llama-server to become healthy...")
        timeout = settings.STARTUP_TIMEOUT
        interval = settings.HEALTH_CHECK_INTERVAL
        elapsed = 0

        while elapsed < timeout:
            if await self.is_healthy():
                logger.info(f"Health check passed after {elapsed}s")
                return

            await asyncio.sleep(interval)
            elapsed += interval

            # Check if process died
            if not await self.is_running():
                stderr_tail = "\n".join(self._stderr_buffer[-20:]) if self._stderr_buffer else "No stderr output"
                raise RuntimeError(
                    f"llama-server process died during startup. Recent stderr:\n{stderr_tail}"
                )

        raise RuntimeError(f"Health check timeout after {timeout}s")

    def _start_log_capture(self) -> None:
        """Start background tasks to capture stdout/stderr."""
        if self.process is None:
            return

        # Cancel existing tasks
        for task in self._log_tasks:
            task.cancel()
        self._log_tasks.clear()

        # Create new tasks
        stdout_task = asyncio.create_task(
            self._capture_stream(self.process.stdout, "stdout", self._stdout_buffer)
        )
        stderr_task = asyncio.create_task(
            self._capture_stream(self.process.stderr, "stderr", self._stderr_buffer)
        )

        self._log_tasks.extend([stdout_task, stderr_task])

    async def _capture_stream(
        self,
        stream: Optional[asyncio.StreamReader],
        name: str,
        buffer: List[str]
    ) -> None:
        """
        Capture output from a stream.

        Args:
            stream: Stream reader
            name: Stream name (stdout/stderr)
            buffer: Buffer to store lines
        """
        if stream is None:
            return

        log_file = Path(settings.LOG_DIR) / f"llama-server-{name}.log"

        try:
            async with aiofiles.open(log_file, "a", encoding="utf-8") as f:
                while True:
                    line = await stream.readline()
                    if not line:
                        break

                    line_str = line.decode("utf-8").rstrip()
                    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                    log_line = f"[{timestamp}] {line_str}"

                    # Add to buffer
                    buffer.append(log_line)
                    if len(buffer) > self._max_log_lines:
                        buffer.pop(0)

                    # Write to file
                    await f.write(log_line + "\n")
                    await f.flush()

                    # Log errors to main logger
                    if name == "stderr" and line_str.strip():
                        logger.warning(f"llama-server stderr: {line_str}")

        except asyncio.CancelledError:
            logger.debug(f"Log capture task cancelled: {name}")
        except Exception as e:
            logger.exception(f"Error capturing {name}: {e}")

    async def _cleanup_process(self) -> None:
        """Clean up process resources."""
        # Cancel log capture tasks
        for task in self._log_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._log_tasks.clear()

        # Cancel health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None

        self.process = None
        self.current_model = None
        self.started_at = None
