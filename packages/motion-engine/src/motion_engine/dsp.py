"""Advanced Audio DSP, Filter Sweeps, and Convolution Acoustics via SciPy."""
from __future__ import annotations

from typing import Literal
import numpy as np
from scipy import signal


def butter_filter(
    audio_data: np.ndarray,
    cutoff_hz: float,
    fs: int = 48000,
    btype: Literal["low", "high", "bandpass"] = "low",
    order: int = 4
) -> np.ndarray:
    """
    Applies Butterworth IIR digital filter (zero-phase distortion via filtfilt).
    Useful for cinematic lowpass sweeps, bass cuts, and telephone/radio bandpasses.
    """
    nyq = 0.5 * fs
    normal_cutoff = np.clip(cutoff_hz / nyq, 0.001, 0.999)
    b, a = signal.butter(order, normal_cutoff, btype=btype, analog=False)
    
    if audio_data.ndim == 1:
        return signal.filtfilt(b, a, audio_data)
    else:
        # Process stereo channels independently
        left = signal.filtfilt(b, a, audio_data[:, 0])
        right = signal.filtfilt(b, a, audio_data[:, 1])
        return np.column_stack([left, right])


def create_synthetic_impulse_response(
    decay_seconds: float = 1.2,
    fs: int = 48000,
    damping: float = 3.5
) -> np.ndarray:
    """Generate a synthetic stereo room impulse response (diffuse reflections)."""
    n_samples = int(decay_seconds * fs)
    t = np.linspace(0, decay_seconds, n_samples)
    rng = np.random.default_rng(260926)

    # Decaying noise burst filtered for warm acoustic room
    noise_l = rng.standard_normal(n_samples) * np.exp(-damping * t)
    noise_r = rng.standard_normal(n_samples) * np.exp(-damping * t)
    ir = np.column_stack([noise_l, noise_r])

    # Lowpass filter the impulse response to simulate air absorption of high frequencies
    return butter_filter(ir, cutoff_hz=4200.0, fs=fs, btype="low")


def convolution_reverb(
    audio_data: np.ndarray,
    decay_seconds: float = 1.0,
    fs: int = 48000,
    wet_mix: float = 0.25
) -> np.ndarray:
    """Apply stereo convolution reverb for spatial depth and physical scale."""
    ir = create_synthetic_impulse_response(decay_seconds=decay_seconds, fs=fs)
    
    if audio_data.ndim == 1:
        wet_l = signal.fftconvolve(audio_data, ir[:, 0], mode="full")[:len(audio_data)]
        wet_r = signal.fftconvolve(audio_data, ir[:, 1], mode="full")[:len(audio_data)]
        dry_stereo = np.column_stack([audio_data, audio_data])
    else:
        wet_l = signal.fftconvolve(audio_data[:, 0], ir[:, 0], mode="full")[:len(audio_data)]
        wet_r = signal.fftconvolve(audio_data[:, 1], ir[:, 1], mode="full")[:len(audio_data)]
        dry_stereo = audio_data

    wet_stereo = np.column_stack([wet_l, wet_r])
    # Normalize wet signal
    max_wet = np.max(np.abs(wet_stereo))
    if max_wet > 0.0:
        wet_stereo = (wet_stereo / max_wet) * np.max(np.abs(dry_stereo))

    return dry_stereo * (1.0 - wet_mix) + wet_stereo * wet_mix
