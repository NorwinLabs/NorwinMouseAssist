"""
Example script showing programmatic usage of MouseSmoother.
This demonstrates how to use the MouseSmoother class without the GUI.
"""
from mouse_smoother import MouseSmoother
import time


def example_basic_usage():
    """Basic example of starting and stopping the smoother."""
    print("Creating mouse smoother...")
    smoother = MouseSmoother()
    
    print("Starting mouse smoothing...")
    smoother.start()
    
    print("Mouse smoothing active for 10 seconds...")
    print("Try moving your mouse - movements should be smoother!")
    time.sleep(10)
    
    print("Stopping mouse smoothing...")
    smoother.stop()
    print("Done!")


def example_custom_settings():
    """Example with custom smoothing settings."""
    print("\nExample with custom settings:")
    print("Creating smoother with gentle settings...")
    
    # Create smoother with custom parameters
    smoother = MouseSmoother(
        smoothing_window=3,      # Light smoothing
        max_velocity=70,         # Allow faster movements
        jitter_threshold=2       # Light jitter filtering
    )
    
    smoother.start()
    print("Gentle smoothing active for 5 seconds...")
    time.sleep(5)
    
    print("Updating to aggressive settings...")
    smoother.update_settings(
        smoothing_window=8,      # Heavy smoothing
        max_velocity=30,         # Slower movements
        jitter_threshold=6       # Strong jitter filtering
    )
    
    print("Aggressive smoothing active for 5 seconds...")
    time.sleep(5)
    
    smoother.stop()
    print("Done!")


def example_adaptive_smoothing():
    """Example that changes settings over time."""
    print("\nExample with adaptive smoothing:")
    smoother = MouseSmoother()
    smoother.start()
    
    # Start with light smoothing
    print("Phase 1: Light smoothing (5s)...")
    smoother.update_settings(smoothing_window=3, jitter_threshold=2)
    time.sleep(5)
    
    # Increase to medium
    print("Phase 2: Medium smoothing (5s)...")
    smoother.update_settings(smoothing_window=5, jitter_threshold=4)
    time.sleep(5)
    
    # Maximum smoothing
    print("Phase 3: Heavy smoothing (5s)...")
    smoother.update_settings(smoothing_window=9, jitter_threshold=7)
    time.sleep(5)
    
    smoother.stop()
    print("Done!")


if __name__ == "__main__":
    print("=" * 50)
    print("MouseSmoother Examples")
    print("=" * 50)
    
    print("\nNote: These examples require a display/GUI environment.")
    print("They demonstrate programmatic control of the smoother.\n")
    
    try:
        # Run basic example
        example_basic_usage()
        
        # Uncomment to run other examples:
        # example_custom_settings()
        # example_adaptive_smoothing()
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure you have:")
        print("  - A display/GUI environment (X11, Wayland, or Windows)")
        print("  - Required packages installed (pip install -r requirements.txt)")
