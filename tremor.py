"""
Tremor detection and cancellation.

Pure numpy (no GUI / input-device dependencies) so it can be tested headlessly.

Workflow:
    1. Record raw mouse positions while the user holds the mouse (calibration).
    2. analyze_tremor() finds the dominant tremor frequency and amplitude.
    3. TremorFilter uses notch filters at that frequency plus a low-pass filter
       to remove the tremor from live mouse input while passing slow,
       intentional movement.
"""
import json
import math
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np

# Physiological tremor (Parkinsonian rest tremor ~4-6 Hz, essential tremor ~4-12 Hz)
TREMOR_BAND = (3.0, 12.0)
ANALYSIS_FS = 100.0          # Hz, uniform rate calibration samples are resampled to
MIN_SAMPLES = 50
MIN_DURATION = 4.0           # seconds of data required to analyze
MIN_PEAK_RATIO = 6.0         # peak power / median band power to call it a tremor
MIN_AMPLITUDE_PX = 0.25      # RMS pixels

PROFILE_PATH = Path.home() / ".norwinmouseassist" / "profile.json"


@dataclass
class TremorProfile:
    """Result of a calibration run."""
    detected: bool
    frequency_hz: float = 0.0     # dominant tremor frequency
    amplitude_px: float = 0.0     # RMS tremor amplitude in pixels
    peak_ratio: float = 0.0       # how far the tremor peak stands above background
    duration_s: float = 0.0
    created: float = 0.0

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        fields = cls.__dataclass_fields__
        return cls(**{k: v for k, v in data.items() if k in fields})

    def save(self, path=PROFILE_PATH):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path=PROFILE_PATH):
        """Return the saved profile, or None if missing / unreadable."""
        try:
            return cls.from_dict(json.loads(Path(path).read_text()))
        except (OSError, ValueError, TypeError):
            return None

    @staticmethod
    def delete(path=PROFILE_PATH):
        try:
            Path(path).unlink()
        except OSError:
            pass


def resample(samples, fs=ANALYSIS_FS):
    """
    Resample irregular (t, x, y) samples to a uniform grid.
    Between mouse events the cursor is stationary, so linear interpolation of
    the position is a faithful reconstruction.

    Returns an (n, 2) array.
    """
    data = np.asarray(samples, dtype=float)
    if data.ndim != 2 or data.shape[0] < 2:
        return np.empty((0, 2))
    t = data[:, 0] - data[0, 0]
    grid = np.arange(0.0, t[-1], 1.0 / fs)
    return np.column_stack([np.interp(grid, t, data[:, 1]),
                            np.interp(grid, t, data[:, 2])])


def _remove_drift(sig, fs):
    """Subtract a ~1 s moving average so slow, intentional motion is excluded."""
    w = max(3, int(fs))
    kernel = np.ones(w) / w
    pad = w // 2
    out = np.empty_like(sig)
    for axis in range(sig.shape[1]):
        padded = np.pad(sig[:, axis], pad, mode="edge")
        trend = np.convolve(padded, kernel, mode="same")[pad:pad + len(sig)]
        out[:, axis] = sig[:, axis] - trend
    return out[pad:len(out) - pad]  # edges of a moving average are unreliable


def analyze_tremor(samples, fs=ANALYSIS_FS):
    """
    Detect a tremor in recorded (t, x, y) mouse samples.

    Returns a TremorProfile. profile.detected is False when no clear
    periodic component exists in the tremor band.
    """
    now = time.time()
    sig = resample(samples, fs)
    duration = len(sig) / fs
    if len(sig) < MIN_SAMPLES or duration < MIN_DURATION:
        return TremorProfile(detected=False, duration_s=duration, created=now)

    sig = _remove_drift(sig, fs)

    # Welch power spectrum summed over both axes (tremor direction is arbitrary)
    seg = min(len(sig), int(5 * fs))
    window = np.hanning(seg)
    step = max(1, seg // 2)
    freqs = np.fft.rfftfreq(seg, 1.0 / fs)
    psd = np.zeros(len(freqs))
    count = 0
    for start in range(0, len(sig) - seg + 1, step):
        for axis in range(2):
            chunk = sig[start:start + seg, axis]
            chunk = (chunk - chunk.mean()) * window
            psd += np.abs(np.fft.rfft(chunk)) ** 2
        count += 1
    if count == 0:
        return TremorProfile(detected=False, duration_s=duration, created=now)
    psd /= count

    band = (freqs >= TREMOR_BAND[0]) & (freqs <= TREMOR_BAND[1])
    band_idx = np.flatnonzero(band)
    band_psd = psd[band_idx]
    background = float(np.median(band_psd))
    peak_i = band_idx[int(np.argmax(band_psd))]
    peak_ratio = float(psd[peak_i] / background) if background > 0 else 0.0

    # Parabolic interpolation for sub-bin frequency accuracy
    freq = float(freqs[peak_i])
    if 0 < peak_i < len(psd) - 1:
        a, b, c = psd[peak_i - 1], psd[peak_i], psd[peak_i + 1]
        denom = a - 2 * b + c
        if denom != 0:
            freq += 0.5 * (a - c) / denom * (freqs[1] - freqs[0])

    # RMS amplitude of the signal within +/-1 Hz of the peak
    full = np.fft.rfftfreq(len(sig), 1.0 / fs)
    mask = np.abs(full - freq) <= 1.0
    power = 0.0
    for axis in range(2):
        spec = np.fft.rfft(sig[:, axis] - sig[:, axis].mean())
        spec[~mask] = 0
        power += float(np.var(np.fft.irfft(spec, n=len(sig))))
    amplitude = math.sqrt(power)

    detected = peak_ratio >= MIN_PEAK_RATIO and amplitude >= MIN_AMPLITUDE_PX
    return TremorProfile(
        detected=detected,
        frequency_hz=round(freq, 2),
        amplitude_px=round(amplitude, 2),
        peak_ratio=round(peak_ratio, 1),
        duration_s=round(duration, 1),
        created=now,
    )


class Biquad:
    """Second-order IIR section (direct form I), RBJ audio-EQ-cookbook designs."""

    def __init__(self, b, a):
        a0 = a[0]
        self.b = [v / a0 for v in b]
        self.a = [v / a0 for v in a]
        self.x1 = self.x2 = self.y1 = self.y2 = 0.0

    @classmethod
    def notch(cls, f0, fs, q):
        w0 = 2 * math.pi * f0 / fs
        alpha = math.sin(w0) / (2 * q)
        cw = math.cos(w0)
        return cls([1, -2 * cw, 1], [1 + alpha, -2 * cw, 1 - alpha])

    @classmethod
    def lowpass(cls, f0, fs, q=1 / math.sqrt(2)):
        w0 = 2 * math.pi * f0 / fs
        alpha = math.sin(w0) / (2 * q)
        cw = math.cos(w0)
        return cls([(1 - cw) / 2, 1 - cw, (1 - cw) / 2],
                   [1 + alpha, -2 * cw, 1 - alpha])

    def reset(self, value=0.0):
        """Settle the filter at a constant input so it starts without a transient."""
        self.x1 = self.x2 = self.y1 = self.y2 = value

    def process(self, x):
        y = (self.b[0] * x + self.b[1] * self.x1 + self.b[2] * self.x2
             - self.a[1] * self.y1 - self.a[2] * self.y2)
        self.x2, self.x1 = self.x1, x
        self.y2, self.y1 = self.y1, y
        return y


class TremorFilter:
    """
    Real-time 2-D tremor canceller: notch at the tremor frequency (and its
    second harmonic) followed by a low-pass filter below it.

    strength (1-10): higher moves the low-pass cutoff lower, rejecting more
    tremor at the cost of cursor lag.
    """
    NOTCH_Q = 1.5   # wide notch: tremor frequency drifts a little over time

    def __init__(self, frequency_hz, fs, strength=5):
        self.frequency_hz = frequency_hz
        self.fs = fs
        self.strength = strength

        nyquist_limit = 0.45 * fs
        cutoff_factor = 1.2 - 0.07 * (strength - 1)   # 1.2 .. 0.57 of tremor freq
        cutoff = min(frequency_hz * cutoff_factor, nyquist_limit)

        def chain():
            sections = [Biquad.notch(frequency_hz, fs, self.NOTCH_Q)]
            if 2 * frequency_hz < nyquist_limit:
                sections.append(Biquad.notch(2 * frequency_hz, fs, self.NOTCH_Q))
            sections.append(Biquad.lowpass(cutoff, fs))
            return sections

        self._axes = (chain(), chain())

    def reset(self, x, y):
        for sections, value in zip(self._axes, (x, y)):
            for s in sections:
                s.reset(value)

    def process(self, x, y):
        out = []
        for sections, value in zip(self._axes, (x, y)):
            for s in sections:
                value = s.process(value)
            out.append(value)
        return out[0], out[1]
