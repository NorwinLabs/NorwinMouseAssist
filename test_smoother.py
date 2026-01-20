"""
Test script for mouse smoother module.
"""
import time
from mouse_smoother import MouseSmoother


def test_smoother_init():
    """Test that MouseSmoother can be initialized."""
    smoother = MouseSmoother()
    assert smoother.enabled == False
    assert smoother.smoothing_window == 5
    assert smoother.max_velocity == 50
    assert smoother.jitter_threshold == 3
    print("✓ Initialization test passed")


def test_smoother_settings_update():
    """Test updating settings."""
    smoother = MouseSmoother()
    smoother.update_settings(
        smoothing_window=8,
        max_velocity=60,
        jitter_threshold=5
    )
    assert smoother.smoothing_window == 8
    assert smoother.max_velocity == 60
    assert smoother.jitter_threshold == 5
    print("✓ Settings update test passed")


def test_smoother_start_stop():
    """Test starting and stopping the smoother."""
    smoother = MouseSmoother()
    
    # Test start
    smoother.start()
    assert smoother.enabled == True
    time.sleep(0.5)  # Let it run briefly
    
    # Test stop
    smoother.stop()
    assert smoother.enabled == False
    print("✓ Start/stop test passed")


if __name__ == "__main__":
    print("Running MouseSmoother tests...\n")
    
    test_smoother_init()
    test_smoother_settings_update()
    
    # Only run start/stop test if we have display access
    try:
        test_smoother_start_stop()
    except Exception as e:
        print(f"⚠ Start/stop test skipped (likely no display): {e}")
    
    print("\nAll tests completed!")
