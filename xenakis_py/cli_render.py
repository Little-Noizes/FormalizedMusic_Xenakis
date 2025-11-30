# xenakis_py/cli_render.py

import argparse
import numpy as np

from xenakis_py.dss_gendy import GendySynth
from xenakis_py.render import render_multichannel_to_wav


def make_breathing_pan(num_samples: int, sr: int, speed_hz: float,
                       noise_strength: float = 0.25, seed=None) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.arange(num_samples) / sr

    # Slow LFO drift
    lfo = np.sin(2 * np.pi * speed_hz * t)

    # Smooth random walk
    steps = rng.normal(scale=0.015, size=num_samples)
    walk = np.cumsum(steps)
    win = max(1, int(sr * 0.5))  # ~0.5s smoothing
    kernel = np.ones(win) / win
    walk_smoothed = np.convolve(walk, kernel, mode="same")
    walk_smoothed /= (np.max(np.abs(walk_smoothed)) + 1e-12)

    pan = 0.7 * lfo + noise_strength * walk_smoothed
    return np.clip(pan, -1.0, 1.0)


def equal_power_stereo(mono: np.ndarray, pan: np.ndarray) -> np.ndarray:
    theta = (pan + 1.0) * (np.pi / 4.0)
    left = mono * np.cos(theta)
    right = mono * np.sin(theta)
    return np.column_stack([left, right])


def main():
    parser = argparse.ArgumentParser(description="DSS / GENDY Renderer — Option A (stereo breathing)")

    parser.add_argument("--duration", type=float, default=8.0)
    parser.add_argument("--sr", type=int, default=48000)
    parser.add_argument("--bit-depth", type=int, default=32, choices=[16, 24, 32])
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--filename", type=str, default="gendy")
    parser.add_argument("--chaos", type=float, default=None)
    parser.add_argument("--memory", type=float, default=None)

    # Timbre mode selector (A1/A2/A3)
    parser.add_argument("--mode", type=str, default="A1", choices=["A1", "A2", "A3"],
                        help="A1: warm/dark, A2: midgrain, A3: bright/glassy")

    # ✅ NEW: Global rate (slows waveform evolution)
    parser.add_argument("--rate", type=float, default=1.0,
                        help="DSS evolution speed (0.1 = slow, 1.0 = normal)")

    # ✅ NEW: Breathing pan speed (controls 'BPM' of stereo motion)
    parser.add_argument("--sway", type=float, default=0.08,
                        help="Stereo breathing speed in Hz (0.03 = slow, 0.12 = fast)")

    args = parser.parse_args()

    # Build synth
    synth = GendySynth(
        backend="mock",
        timbre_mode=args.mode,
        params={
            "amp_lo": -0.9,
            "amp_hi": 0.9,
            "dur_lo": 0.002,
            "dur_hi": 0.03,
            "freq_lo": 100.0,
            "freq_hi": 800.0,
            "chaos": args.chaos if args.chaos is not None else 0.5,
            "memory": args.memory if args.memory is not None else 0.5,
            "rate": args.rate,   # ✅ now dynamic / MIDI-ready
        }
    )

    mono = synth.generate_waveform(duration=args.duration, sr=args.sr)

    pan = make_breathing_pan(len(mono), args.sr, speed_hz=args.sway, seed=args.seed)
    stereo = equal_power_stereo(mono, pan)

    # normalize headroom safely
    peak = np.max(np.abs(stereo))
    if peak > 0:
        stereo = stereo / (peak / 0.98)

    render_multichannel_to_wav(
        waveform=stereo,
        filename=f"{args.filename}_{args.mode.lower()}",
        sr=args.sr,
        bit_depth=args.bit_depth
    )


if __name__ == "__main__":
    main()
