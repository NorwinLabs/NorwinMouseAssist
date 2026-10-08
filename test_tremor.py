"""
Tests for tremor detection and cancellation (no display or mouse needed).
"""
import numpy as np

from tremor import TremorFilter, TremorProfile, analyze_tremor


def synth(freq=5.5, amp=3.0, seconds=15.0, rate=250.0, drift=True, seed=0):
    """Simulated (t, x, y) mouse samples: slow intentional drift + tremor + noise."""
    rng = np.random.default_rng(seed)
    t = np.arange(0, seconds, 1.0 / rate)
    x = 500 + (40 * np.sin(2 * np.pi * 0.15 * t) if drift else 0)
    y = 400 + (25 * np.cos(2 * np.pi * 0.1 * t) if drift else 0)
    x = x + amp * np.sin(2 * np.pi * freq * t) + rng.normal(0, 0.2, t.size)
    y = y + 0.6 * amp * np.sin(2 * np.pi * freq * t + 1.0) + rng.normal(0, 0.2, t.size)
    return np.column_stack([t, np.round(x), np.round(y)])  # mouse positions are integers


def test_detects_tremor_frequency():
    for freq in (4.0, 5.5, 8.0, 10.5):
        profile = analyze_tremor(synth(freq=freq))
        assert profile.detected, f"missed {freq} Hz tremor"
        assert abs(profile.frequency_hz - freq) < 0.4, (freq, profile.frequency_hz)
        assert 1.5 < profile.amplitude_px < 4.0
    print("✓ Tremor frequency detection test passed")


def test_no_tremor_not_detected():
    rng = np.random.default_rng(1)
    t = np.arange(0, 15, 1 / 250)
    samples = np.column_stack([
        t,
        np.round(500 + 40 * np.sin(2 * np.pi * 0.15 * t) + rng.normal(0, 0.2, t.size)),
        np.round(400 + rng.normal(0, 0.2, t.size)),
    ])
    assert not analyze_tremor(samples).detected
    print("✓ No-tremor test passed")


def test_too_little_data():
    assert not analyze_tremor(synth(seconds=1.0)).detected
    assert not analyze_tremor([]).detected
    print("✓ Insufficient data test passed")


def test_filter_cancels_tremor_and_keeps_motion():
    fs = 120.0
    t = np.arange(0, 20, 1 / fs)
    intent = 300 + 100 * np.sin(2 * np.pi * 0.3 * t)          # slow deliberate sweep
    tremor = 4 * np.sin(2 * np.pi * 6.0 * t)
    settled = slice(int(5 * fs), None)

    def run(signal, start):
        f = TremorFilter(6.0, fs, strength=5)
        f.reset(start, 0.0)
        return np.array([f.process(v, 0.0)[0] for v in signal])

    combined = run(intent + tremor, intent[0])
    clean = run(intent, intent[0])

    # The filter is linear, so combined - clean is what the tremor turned into.
    residual = combined[settled] - clean[settled]
    assert np.std(residual) < 0.1 * np.std(tremor[settled])  # >= 20 dB reduction

    # The deliberate sweep survives: output tracks the intended path (small lag)
    assert np.max(np.abs(clean[settled] - intent[settled])) < 25

    # DC / slow movement passes: constant input converges to itself
    h = TremorFilter(6.0, fs, strength=10)
    h.reset(0.0, 0.0)
    for _ in range(int(3 * fs)):
        last = h.process(200.0, -50.0)
    assert abs(last[0] - 200.0) < 0.5 and abs(last[1] + 50.0) < 0.5
    print("✓ Tremor filter test passed")


def test_profile_roundtrip(tmp_path=None):
    import tempfile
    from pathlib import Path
    path = Path(tempfile.mkdtemp()) / "profile.json"
    p = analyze_tremor(synth())
    p.save(path)
    loaded = TremorProfile.load(path)
    assert loaded == p
    assert TremorProfile.load(path.with_name("missing.json")) is None
    print("✓ Profile save/load test passed")


if __name__ == "__main__":
    print("Running tremor tests...\n")
    test_detects_tremor_frequency()
    test_no_tremor_not_detected()
    test_too_little_data()
    test_filter_cancels_tremor_and_keeps_motion()
    test_profile_roundtrip()
    print("\nAll tremor tests completed!")
