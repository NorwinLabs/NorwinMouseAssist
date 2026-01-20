"""
Mouse smoothing module for reducing jitter and rapid movements.
This helps people with Parkinson's or other conditions affecting hand stability.
"""
import threading
import time
from collections import deque
from pynput import mouse
from pynput.mouse import Controller, Button
import numpy as np


class MouseSmoother:
    """
    Smooths mouse movements by filtering out jittery and rapid movements.
    Uses a moving average filter and velocity limiting.
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
        
    def start(self):
        """Start the mouse smoothing."""
        if self.enabled:
            return
            
        self.enabled = True
        self.stop_event.clear()
        
        # Get initial position
        initial_pos = self.mouse_controller.position
        self.raw_position = list(initial_pos)
        self.smoothed_position = list(initial_pos)
        self.position_history.clear()
        
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
            
    def _on_move(self, x, y):
        """Callback for raw mouse movements."""
        if not self.enabled:
            return False
            
        with self.lock:
            # Store the raw position
            self.raw_position = [x, y]
            
    def _process_movements(self):
        """Process and smooth mouse movements."""
        while not self.stop_event.is_set():
            try:
                current_time = time.time()
                dt = current_time - self.last_update_time
                
                # Update at ~60 Hz
                if dt < 1.0 / 60.0:
                    time.sleep(0.001)
                    continue
                    
                self.last_update_time = current_time
                
                with self.lock:
                    if self.raw_position is None:
                        time.sleep(0.001)
                        continue
                        
                    raw = self.raw_position
                    
                # Add to history
                self.position_history.append(raw)
                
                # Calculate smoothed position using moving average
                if len(self.position_history) > 0:
                    positions_array = np.array(list(self.position_history))
                    smoothed = np.mean(positions_array, axis=0)
                    
                    # Calculate delta from current smoothed position
                    delta_x = smoothed[0] - self.smoothed_position[0]
                    delta_y = smoothed[1] - self.smoothed_position[1]
                    
                    # Apply jitter threshold
                    distance = np.sqrt(delta_x**2 + delta_y**2)
                    if distance < self.jitter_threshold:
                        # Movement too small, ignore (filters jitter)
                        time.sleep(0.001)
                        continue
                    
                    # Apply velocity limiting
                    if distance > self.max_velocity:
                        # Limit the movement to max_velocity
                        scale = self.max_velocity / distance
                        delta_x *= scale
                        delta_y *= scale
                    
                    # Update smoothed position
                    self.smoothed_position[0] += delta_x
                    self.smoothed_position[1] += delta_y
                    
                    # Move the actual mouse cursor
                    # We need to temporarily disable the listener to avoid feedback
                    try:
                        self.mouse_controller.position = (
                            int(self.smoothed_position[0]),
                            int(self.smoothed_position[1])
                        )
                    except Exception as e:
                        # Ignore errors from setting position
                        pass
                        
                time.sleep(0.001)
                
            except Exception as e:
                print(f"Error in smoothing loop: {e}")
                time.sleep(0.01)
                
    def update_settings(self, smoothing_window=None, max_velocity=None, jitter_threshold=None):
        """Update smoothing parameters."""
        with self.lock:
            if smoothing_window is not None:
                self.smoothing_window = smoothing_window
                self.position_history = deque(list(self.position_history), maxlen=smoothing_window)
            if max_velocity is not None:
                self.max_velocity = max_velocity
            if jitter_threshold is not None:
                self.jitter_threshold = jitter_threshold
