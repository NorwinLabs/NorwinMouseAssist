"""
Mouse smoothing module for reducing jitter and rapid movements.
This helps people with Parkinson's or other conditions affecting hand stability.
"""
import sys
import threading
import time
from collections import deque
from pynput import mouse
from pynput.mouse import Controller
import numpy as np

from tremor import TremorFilter

# Update rates of the processing loop
DEFAULT_RATE_HZ = 60.0
TREMOR_RATE_HZ = 120.0


def _set_timer_resolution(enable):
    """Ask Windows for 1 ms timers so the processing loop keeps its update rate."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        winmm = ctypes.windll.winmm
        (winmm.timeBeginPeriod if enable else winmm.timeEndPeriod)(1)
    except Exception:
        pass


class MouseRecorder:
    """Records timestamped raw mouse positions (used for tremor calibration)."""

    def __init__(self):
        self.samples = []
        self._listener = None

    def start(self):
        self.samples = []
        self._listener = mouse.Listener(on_move=self._on_move)
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()
            self._listener = None
        return self.samples

    def _on_move(self, x, y):
        self.samples.append((time.perf_counter(), x, y))


class MouseSmoother:
    """
    Smooths mouse movements by filtering out jittery and rapid movements.
    Uses a moving average filter and velocity limiting, or - when a tremor
    profile from calibration is set - a notch/low-pass filter tuned to the
    user's own tremor frequency.
    """

    def __init__(self, smoothing_window=5, max_velocity=50, jitter_threshold=3):
        """
        Initialize the mouse smoother.

        Args:
            smoothing_window: Number of samples to average (higher = smoother but more lag)
            max_velocity: Maximum pixels per update to move (limits rapid movements)
            jitter_threshold: Minimum movement in pixels to register (filters micro-jitters)
        """
        self.smoothing_window = smoothing_window
        self.max_velocity = max_velocity
        self.jitter_threshold = jitter_threshold

        self.enabled = False
        self.position_history = deque(maxlen=smoothing_window)
        self.mouse_controller = Controller()
        self.listener = None
        self.processing_thread = None
        self.stop_event = threading.Event()

        self.raw_position = None
        self.smoothed_position = None
        self.last_update_time = time.time()
        self.lock = threading.Lock()

        # Where the OS cursor was last seen, and positions we moved it to
        # ourselves (so those move events are not mistaken for hand movement)
        self._cursor = None
        self._injected = deque(maxlen=16)

        # Tremor cancellation (set from a calibration profile)
        self.tremor_profile = None
        self.tremor_strength = 5
        self.tremor_filter = None

    @property
    def tremor_active(self):
        return self.tremor_filter is not None

    def set_tremor_profile(self, profile, strength=None):
        """Use calibrated tremor cancellation. Pass None to go back to plain smoothing."""
        with self.lock:
            if strength is not None:
                self.tremor_strength = strength
            self.tremor_profile = profile
            self._build_tremor_filter()

    def _build_tremor_filter(self):
        profile = self.tremor_profile
        if profile is None or not profile.detected:
            self.tremor_filter = None
            return
        self.tremor_filter = TremorFilter(
            profile.frequency_hz, TREMOR_RATE_HZ, self.tremor_strength)
        if self.smoothed_position is not None:
            self.tremor_filter.reset(*self.smoothed_position)

    def start(self):
        """Start the mouse smoothing."""
        if self.enabled:
            return

        self.enabled = True
        self.stop_event.clear()
        _set_timer_resolution(True)

        # Get initial position
        initial_pos = self.mouse_controller.position
        self.raw_position = list(initial_pos)
        self.smoothed_position = list(initial_pos)
        self._cursor = tuple(initial_pos)
        self._injected.clear()
        self.position_history.clear()
        with self.lock:
            self._build_tremor_filter()

        # Start listener for raw mouse movements
        self.listener = mouse.Listener(on_move=self._on_move)
        self.listener.start()

        # Start processing thread
        self.processing_thread = threading.Thread(target=self._process_movements, daemon=True)
        self.processing_thread.start()

    def stop(self):
        """Stop the mouse smoothing."""
        if not self.enabled:
            return

        self.enabled = False
        self.stop_event.set()

        if self.listener:
            self.listener.stop()
            self.listener = None

        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)
            self.processing_thread = None
        _set_timer_resolution(False)

    def _on_move(self, x, y):
        """Callback for raw mouse movements."""
        if not self.enabled:
            return False

        with self.lock:
            if (x, y) in self._injected:
                # Echo of a move we made ourselves, not the user's hand
                self._injected.remove((x, y))
                self._cursor = (x, y)
                return

            # The cursor sits at our filtered position, so the hand's real
            # movement is the change since the last known cursor position.
            if self._cursor is None:
                self._cursor = (x, y)
            self.raw_position = [
                self.raw_position[0] + (x - self._cursor[0]),
                self.raw_position[1] + (y - self._cursor[1]),
            ]
            self._cursor = (x, y)

    def _move_cursor(self, x, y):
        """Move the real cursor, remembering the move so its echo can be ignored."""
        target = (int(round(x)), int(round(y)))
        with self.lock:
            if target == self._cursor:
                return
            self._injected.append(target)
            self._cursor = target
        try:
            self.mouse_controller.position = target
        except Exception:
            # Ignore errors from setting position
            pass

    def _process_movements(self):
        """Process and smooth mouse movements."""
        while not self.stop_event.is_set():
            try:
                with self.lock:
                    tremor_filter = self.tremor_filter
                rate = TREMOR_RATE_HZ if tremor_filter else DEFAULT_RATE_HZ
                step = 1.0 / rate

                current_time = time.time()
                dt = current_time - self.last_update_time

                if dt < step:
                    time.sleep(0.001)
                    continue

                self.last_update_time = current_time

                with self.lock:
                    if self.raw_position is None:
                        continue
                    raw = tuple(self.raw_position)

                if tremor_filter:
                    # Run one filter step per elapsed tick so the filter's
                    # timebase stays correct even if the loop falls behind.
                    for _ in range(min(max(1, round(dt / step)), 10)):
                        filtered = tremor_filter.process(*raw)
                    delta_x = filtered[0] - self.smoothed_position[0]
                    delta_y = filtered[1] - self.smoothed_position[1]
                else:
                    # Add to history
                    self.position_history.append(raw)
                    smoothed = np.mean(np.array(list(self.position_history)), axis=0)
                    delta_x = smoothed[0] - self.smoothed_position[0]
                    delta_y = smoothed[1] - self.smoothed_position[1]

                    # Apply jitter threshold
                    if np.hypot(delta_x, delta_y) < self.jitter_threshold:
                        # Movement too small, ignore (filters jitter)
                        continue

                # Apply velocity limiting
                distance = np.hypot(delta_x, delta_y)
                if distance > self.max_velocity:
                    scale = self.max_velocity / distance
                    delta_x *= scale
                    delta_y *= scale

                # Update smoothed position and move the actual mouse cursor
                self.smoothed_position[0] += delta_x
                self.smoothed_position[1] += delta_y
                self._move_cursor(*self.smoothed_position)

            except Exception as e:
                print(f"Error in smoothing loop: {e}")
                time.sleep(0.01)

    def update_settings(self, smoothing_window=None, max_velocity=None,
                        jitter_threshold=None, tremor_strength=None):
        """Update smoothing parameters."""
        with self.lock:
            if smoothing_window is not None:
                self.smoothing_window = smoothing_window
                self.position_history = deque(list(self.position_history), maxlen=smoothing_window)
            if max_velocity is not None:
                self.max_velocity = max_velocity
            if jitter_threshold is not None:
                self.jitter_threshold = jitter_threshold
            if tremor_strength is not None and tremor_strength != self.tremor_strength:
                self.tremor_strength = tremor_strength
                self._build_tremor_filter()
