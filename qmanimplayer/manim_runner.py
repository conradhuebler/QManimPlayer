"""
Manim Runner - Execute and manage manimgl processes.

Handles:
- Subprocess management for manimgl
- Output capture and error handling
- Process control (start, stop)
"""

import subprocess
import threading
import os
import signal
import time
import queue
from typing import Optional, Callable, Dict, Any
from pathlib import Path
from enum import Enum


class ManimProcessStatus(Enum):
    """Status of manim rendering process."""
    IDLE = "idle"
    RUNNING = "running"
    STOPPING = "stopping"
    FINISHED = "finished"
    ERROR = "error"
    STOPPED = "stopped"


class ManimRenderMode(Enum):
    """Render mode for manimgl execution."""
    AUTO_PLAY = "Auto-Play"          # Render and auto-loop
    PREVIEW_LOOP = "Preview Loop"    # Interactive with auto-loop
    SAVE_ONLY = "Save Only"          # Save video file, no preview


class ManimRunner:
    """Execute manim-gl scripts and manage the rendering process."""

    def __init__(self, script_path: str):
        """
        Initialize manim runner.

        Args:
            script_path: Path to the manim-gl .py script
        """
        self.script_path = Path(script_path)
        self.process: Optional[subprocess.Popen] = None
        self.status = ManimProcessStatus.IDLE
        self.output_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # Default render mode: Interactive preview with auto-loop
        self.render_mode = ManimRenderMode.PREVIEW_LOOP

        # Thread-safe queues for output (background threads → main thread)
        self.output_queue = queue.Queue()
        self.error_queue = queue.Queue()
        self.status_queue = queue.Queue()
        self.queue_timer = None

        # Callbacks (will be called from main thread via queue processing)
        self.on_status_changed: Optional[Callable[[ManimProcessStatus], None]] = None
        self.on_output: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None

    def run(self, scene_name: str = "Scene", quality: str = "low_quality",
            mode: Optional[ManimRenderMode] = None) -> bool:
        """
        Run manimgl on the script.

        Args:
            scene_name: Name of Scene class to render
            quality: Quality setting (low_quality, medium_quality, high_quality)
            mode: Render mode (AUTO_PLAY, PREVIEW_LOOP, SAVE_ONLY). Defaults to instance mode.

        Returns:
            True if process started successfully
        """
        # Race condition guard: don't start while stopping
        if self.status in (ManimProcessStatus.RUNNING, ManimProcessStatus.STOPPING):
            self._error("Process busy - please wait")
            return False

        # Kill any lingering process (safety cleanup)
        if self.process and self.process.poll() is None:
            try:
                self.process.kill()
                time.sleep(0.2)
            except:
                pass

        # Use provided mode or instance default
        render_mode = mode if mode is not None else self.render_mode

        try:
            # Build manimgl command based on render mode
            cmd = [
                "manimgl",
                str(self.script_path),
                scene_name,
                f"-{quality[0]}",  # -l, -m, -h
            ]

            # Add mode-specific flags
            if render_mode == ManimRenderMode.AUTO_PLAY:
                # Auto-play: render and loop without preview window (requires -l flag)
                cmd.append("-l")  # Loop
                cmd.append("-p")  # No preview (just loop)

            elif render_mode == ManimRenderMode.PREVIEW_LOOP:
                # Preview with loop: interactive window with auto-loop
                cmd.append("-l")  # Loop
                # No -p flag: shows interactive preview

            elif render_mode == ManimRenderMode.SAVE_ONLY:
                # Save only: render to file, no preview
                cmd.append("--write_to_movie")  # Save to video file
                cmd.append("-np")  # No preview

            # Start process with process group (Unix) for clean killing
            # preexec_fn creates new process group, so we can kill all children
            popen_kwargs = {
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "text": True,
                "bufsize": 1,
                "universal_newlines": True
            }

            # Process group only on Unix (not Windows)
            if os.name != 'nt':
                popen_kwargs["preexec_fn"] = os.setsid

            self.process = subprocess.Popen(cmd, **popen_kwargs)

            self._set_status(ManimProcessStatus.RUNNING)

            # Start output capture thread
            self.stop_event.clear()
            self.output_thread = threading.Thread(
                target=self._capture_output,
                daemon=True
            )
            self.output_thread.start()

            return True

        except FileNotFoundError:
            helpful_msg = (
                "manimgl command not found!\n\n"
                "Install it with:\n"
                "pip install manimgl\n\n"
                "Or visit: https://github.com/3b1b/manim"
            )
            self._error(helpful_msg)
            self._set_status(ManimProcessStatus.ERROR)
            return False

        except PermissionError as e:
            self._error(f"Permission denied: {e}\nCheck file permissions")
            self._set_status(ManimProcessStatus.ERROR)
            return False

        except OSError as e:
            self._error(f"OS Error: {e}\nCheck system resources and permissions")
            self._set_status(ManimProcessStatus.ERROR)
            return False

        except Exception as e:
            self._error(f"Error starting manim process: {e}")
            self._set_status(ManimProcessStatus.ERROR)
            return False

    def stop(self) -> bool:
        """
        Stop the running manim process (non-blocking).

        Returns immediately after signaling stop. Cleanup happens in background thread.

        Returns:
            True if stop was initiated
        """
        # Only stop if actually running
        if self.status != ManimProcessStatus.RUNNING:
            return False

        if self.process is None or self.process.poll() is not None:
            self._set_status(ManimProcessStatus.STOPPED)
            return False

        # Signal stop and change status
        self.stop_event.set()
        self._set_status(ManimProcessStatus.STOPPING)

        # Do actual cleanup in background thread (non-blocking!)
        cleanup_thread = threading.Thread(
            target=self._cleanup_process,
            daemon=True,
            name="ManimCleanupThread"
        )
        cleanup_thread.start()

        return True

    def _cleanup_process(self):
        """
        Background cleanup thread - forcefully terminates process.

        Uses aggressive killing strategy:
        1. Brief wait for output thread
        2. SIGKILL (force kill, can't be ignored)
        3. Process group kill if needed (kills children too)
        """
        try:
            # Wait briefly for output thread to finish reading
            if self.output_thread and self.output_thread.is_alive():
                self.output_thread.join(timeout=1.5)

            if not self.process:
                self._set_status(ManimProcessStatus.STOPPED)
                return

            # FORCE KILL - SIGKILL can't be ignored (unlike SIGTERM)
            try:
                self.process.kill()
            except:
                pass

            # Wait for process to die
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                # Process still alive? Try process group kill
                if os.name != 'nt':
                    try:
                        # Kill entire process group (kills all children)
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                        time.sleep(0.5)
                    except (ProcessLookupError, PermissionError, OSError):
                        # Process already dead or no permissions
                        pass

            self._set_status(ManimProcessStatus.STOPPED)

        except Exception as e:
            self._error(f"Cleanup error: {e}")
            self._set_status(ManimProcessStatus.ERROR)

    def is_running(self) -> bool:
        """Check if process is running."""
        if self.process is None:
            return False

        return self.process.poll() is None

    def _capture_output(self):
        """Capture stdout/stderr from the process concurrently.

        Uses separate threads for stdout and stderr to avoid blocking
        when process terminates externally.
        """
        if self.process is None:
            return

        def read_stream(stream, is_error=False):
            """Read from stream until closed or stopped."""
            if not stream:
                return

            try:
                for line in stream:
                    if self.stop_event.is_set():
                        break
                    if line.strip():
                        if is_error:
                            self._error(line.strip())
                        else:
                            self._output(line.strip())
            except (ValueError, OSError, BrokenPipeError):
                # Pipe closed - process ended, this is normal
                pass
            finally:
                try:
                    if stream and not stream.closed:
                        stream.close()
                except:
                    pass

        # Create separate threads for stdout and stderr (concurrent reading)
        stdout_thread = None
        stderr_thread = None

        try:
            if self.process.stdout:
                stdout_thread = threading.Thread(
                    target=read_stream,
                    args=(self.process.stdout, False),
                    daemon=True,
                    name="ManimStdoutReader"
                )
                stdout_thread.start()

            if self.process.stderr:
                stderr_thread = threading.Thread(
                    target=read_stream,
                    args=(self.process.stderr, True),
                    daemon=True,
                    name="ManimStderrReader"
                )
                stderr_thread.start()

            # Wait for both reader threads to complete (with timeout)
            if stdout_thread:
                stdout_thread.join(timeout=5)
            if stderr_thread:
                stderr_thread.join(timeout=5)

        except Exception as e:
            self._error(f"Error capturing output: {e}")

        finally:
            # Check final status
            if self.process:
                try:
                    returncode = self.process.poll()
                    if returncode is None:
                        # Process still running, wait a bit
                        try:
                            returncode = self.process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            pass

                    # Check exit code and set appropriate status
                    if returncode == 0:
                        self._set_status(ManimProcessStatus.FINISHED)
                    elif returncode in (-11, 139, -6):
                        # Segmentation fault / abort signal
                        self._error("Process crashed (SIGSEGV/SIGABRT)")
                        self._set_status(ManimProcessStatus.ERROR)
                    elif returncode is not None:
                        self._set_status(ManimProcessStatus.ERROR)
                except Exception:
                    # Any error in status check, just mark as error
                    self._set_status(ManimProcessStatus.ERROR)

    def _process_queues(self):
        """Process output/error/status queues (called from main thread by QTimer)."""
        # Process all pending output messages
        while not self.output_queue.empty():
            try:
                message = self.output_queue.get_nowait()
                if self.on_output:
                    self.on_output(message)
            except queue.Empty:
                break

        # Process all pending error messages
        while not self.error_queue.empty():
            try:
                message = self.error_queue.get_nowait()
                if self.on_error:
                    self.on_error(message)
            except queue.Empty:
                break

        # Process all pending status changes (CRITICAL: thread-safe GUI updates)
        while not self.status_queue.empty():
            try:
                status = self.status_queue.get_nowait()
                if self.on_status_changed:
                    self.on_status_changed(status)
            except queue.Empty:
                break

        # FALLBACK: Auto-detect dead process if status not updated
        # (handles case where _capture_output doesn't update status in time)
        if self.status == ManimProcessStatus.RUNNING and self.process:
            returncode = self.process.poll()
            if returncode is not None:
                # Process is dead but status still RUNNING - fix it
                if returncode == 0:
                    self._set_status(ManimProcessStatus.FINISHED)
                else:
                    self._set_status(ManimProcessStatus.ERROR)

    def _set_status(self, status: ManimProcessStatus):
        """Queue status change for thread-safe processing."""
        self.status = status
        self.status_queue.put(status)  # Queue instead of direct callback

    def _output(self, message: str):
        """Queue output message for thread-safe processing."""
        self.output_queue.put(message)

    def _error(self, message: str):
        """Queue error message for thread-safe processing."""
        self.error_queue.put(message)

    def get_video_path(self) -> Optional[Path]:
        """
        Try to find the output video file.

        Returns:
            Path to rendered video, or None if not found
        """
        # Typical manim output location
        media_dir = self.script_path.parent / "media" / "videos"

        if not media_dir.exists():
            return None

        # Look for .mp4 files
        mp4_files = list(media_dir.rglob("*.mp4"))
        if mp4_files:
            # Return most recently modified
            return max(mp4_files, key=lambda p: p.stat().st_mtime)

        return None
