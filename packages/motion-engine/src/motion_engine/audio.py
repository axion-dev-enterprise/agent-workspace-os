"""Procedural Audio Synthesis Engine in Pure NumPy (No External Samples Needed)."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Sequence
import wave
import numpy as np


def note_to_freq(midi_note: float) -> float:
    """Convert standard MIDI note number to Frequency in Hertz (A4 = 440 Hz = 69)."""
    return 440.0 * (2.0 ** ((midi_note - 69.0) / 12.0))


def sub_bass_drop(
    duration: float = 2.5,
    sample_rate: int = 48000,
    f_start: float = 130.0,
    f_end: float = 35.0,
    decay: float = 4.0
) -> np.ndarray:
    """Generate a powerful exponential sub-bass drop with smooth sin² attack."""
    n_samples = max(2, int(duration * sample_rate))
    t = np.linspace(0.0, duration, n_samples, endpoint=False)
    freq = f_end + (f_start - f_end) * np.exp(-decay * t)
    phase = 2.0 * np.pi * np.cumsum(freq) / sample_rate
    attack_samples = max(1, int(0.03 * sample_rate))
    env = np.ones_like(t)
    env[:attack_samples] = np.sin(np.linspace(0, np.pi / 2.0, attack_samples)) ** 2
    env *= np.exp(-1.2 * t)
    return np.sin(phase) * env


def cinematic_riser(
    duration: float = 3.5,
    sample_rate: int = 48000,
    f_start: float = 70.0,
    f_end: float = 880.0
) -> np.ndarray:
    """Generate an exponential tension-building pitch riser with harmonic saturation."""
    n_samples = max(2, int(duration * sample_rate))
    t = np.linspace(0.0, duration, n_samples, endpoint=False)
    freq = f_start * ((f_end / f_start) ** (t / duration))
    phase = 2.0 * np.pi * np.cumsum(freq) / sample_rate
    env = (t / duration) ** 2.2
    raw = np.sin(phase) + 0.25 * np.sin(2.0 * phase)
    return (raw / 1.25) * env


def metallic_click(
    duration: float = 0.08,
    sample_rate: int = 48000,
    fc: float = 1400.0,
    fm: float = 420.0,
    mod_index: float = 4.0,
    tau: float = 0.02
) -> np.ndarray:
    """Generate a crisp metallic transient click using 2-operator FM synthesis."""
    n_samples = max(2, int(duration * sample_rate))
    t = np.linspace(0.0, duration, n_samples, endpoint=False)
    i_t = mod_index * np.exp(-t / tau)
    modulator = np.sin(2.0 * np.pi * fm * t)
    carrier = np.sin(2.0 * np.pi * fc * t + i_t * modulator)
    env = np.exp(-t / (tau * 1.5))
    return carrier * env


def ambient_drone(
    duration: float = 15.0,
    sample_rate: int = 48000,
    base_midi: float = 36.0 # C2
) -> np.ndarray:
    """Generate an evolving stereophonic ambient drone with binaural phase beating."""
    n_samples = max(2, int(duration * sample_rate))
    t = np.linspace(0.0, duration, n_samples, endpoint=False)
    base_f = note_to_freq(base_midi)

    # Left & Right slightly detuned by 0.5 Hz for rich stereo depth
    left = 0.5 * np.sin(2.0 * np.pi * base_f * t) + 0.25 * np.sin(2.0 * np.pi * (base_f * 2.0) * t)
    right = 0.5 * np.sin(2.0 * np.pi * (base_f + 0.5) * t) + 0.25 * np.sin(2.0 * np.pi * (base_f * 2.0 - 0.3) * t)

    fade_in_len = min(n_samples // 4, int(2.0 * sample_rate))
    fade_out_len = min(n_samples // 4, int(3.0 * sample_rate))
    env = np.ones(n_samples, dtype=np.float64)
    if fade_in_len > 0:
        env[:fade_in_len] = np.sin(np.linspace(0, np.pi / 2.0, fade_in_len)) ** 2
    if fade_out_len > 0:
        env[-fade_out_len:] = np.sin(np.linspace(np.pi / 2.0, 0, fade_out_len)) ** 2

    return np.column_stack([left * env, right * env])


class ProceduralAudioEngine:
    """Stateful multichannel procedural audio compositor with deterministic PRNG."""

    def __init__(self, duration: float = 15.0, sample_rate: int = 48000, seed: int = 260926):
        self.duration = float(duration)
        self.sample_rate = int(sample_rate)
        self.sample_count = round(self.duration * self.sample_rate)
        self.mix = np.zeros((self.sample_count, 2), dtype=np.float64)
        self.rng = np.random.default_rng(seed)

    def add_sound(
        self,
        mono_or_stereo: np.ndarray,
        start_time: float,
        gain: float = 1.0,
        pan: float = 0.0
    ) -> None:
        """Mix a sound layer into the master stereo bus with equal-power panning."""
        start_frame = round(start_time * self.sample_rate)
        if start_frame >= self.sample_count:
            return

        sound = np.asarray(mono_or_stereo, dtype=np.float64)
        if sound.ndim == 1:
            pan_val = float(np.clip(pan, -1.0, 1.0))
            theta = (pan_val + 1.0) * (np.pi / 4.0)
            stereo = np.column_stack([sound * np.cos(theta), sound * np.sin(theta)])
        else:
            stereo = sound

        end_frame = min(start_frame + len(stereo), self.sample_count)
        frames_to_copy = end_frame - start_frame
        if frames_to_copy > 0:
            self.mix[start_frame:end_frame] += stereo[:frames_to_copy] * gain

    def export(self, output_path: str | Path, target_dbfs: float = -1.5) -> Path:
        """Export composite audio to 16-bit PCM WAV with sample ceiling guard."""
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        export_pcm_wav(self.mix, self.sample_rate, out_p, target_dbfs)
        return out_p


def export_pcm_wav(
    mix: np.ndarray,
    sample_rate: int,
    output_path: Path,
    target_dbfs: float = -1.5
) -> None:
    """Normalize and write audio samples to 16-bit PCM stereo WAV."""
    mix_copy = np.copy(mix)
    peak = float(np.max(np.abs(mix_copy)))
    if peak > 0.0:
        ceiling_linear = 10.0 ** (target_dbfs / 20.0)
        if peak > ceiling_linear:
            mix_copy *= ceiling_linear / peak

    pcm_data = np.clip(mix_copy * 32767.0, -32768.0, 32767.0).astype(np.int16)
    with wave.open(str(output_path), 'wb') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm_data.tobytes())
