# xenakis_py/dss_gendy.py

import numpy as np
import socket
from typing import Literal


class GendySynth:
    """
    Dynamic Stochastic Synthesis (DSS / GENDYN)
    Smooth stochastic parameter evolution (no clicks)
    Continuous-phase oscillator implementation for mock backend
    """

    def __init__(
        self,
        backend: Literal["sc", "csound", "mock"] = "mock",
        osc_host: str = "127.0.0.1",
        osc_port: int = 57120,
        params: dict | None = None,
        timbre_mode: Literal["A1", "A2", "A3"] = "A1",
    ):
        self.backend = backend
        self.osc_host = osc_host
        self.osc_port = osc_port

        # Base parameter defaults (can be overridden)
        self.params = params or {
            "amp_lo": -0.8,
            "amp_hi": 0.8,
            "dur_lo": 0.002,
            "dur_hi": 0.03,
            "freq_lo": 100.0,
            "freq_hi": 800.0,
            "chaos": 0.5,
            "memory": 0.5,
            "rate": 1.0,       # <- important: this is MIDI-controllable later
        }

        self.timbre_mode = timbre_mode
        self.apply_timbre_mode()

    def apply_timbre_mode(self):
        """
        A1/A2/A3 = spectral region presets.
        User can still override via CLI or later MIDI mapping.
        """
        mode = self.timbre_mode

        if mode == "A1":  # warm / breathing / low-mid
            self.params["freq_lo"] = 28.0
            self.params["freq_hi"] = 220.0

        elif mode == "A2":  # midgrain / whispering swarm
            self.params["freq_lo"] = 200.0
            self.params["freq_hi"] = 2000.0

        elif mode == "A3":  # bright crystalline cloud
            self.params["freq_lo"] = 1200.0
            self.params["freq_hi"] = 8000.0

        else:
            raise ValueError(f"Unknown timbre mode: {mode}")

    # ---------------------------------------------------------
    # ✅ Correct smooth waveform generator (no clicks)
    # ---------------------------------------------------------
    def generate_waveform(self, duration: float = 5.0, sr: int = 44100) -> np.ndarray:
        if self.backend != "mock":
            raise NotImplementedError("Waveform generation only available in mock mode.")

        amp_lo = self.params["amp_lo"]
        amp_hi = self.params["amp_hi"]
        freq_lo = self.params["freq_lo"]
        freq_hi = self.params["freq_hi"]
        dur_lo = self.params["dur_lo"]
        dur_hi = self.params["dur_hi"]
        memory = self.params["memory"]

        amp = 0.0
        freq = (freq_lo + freq_hi) / 2.0
        phase = 0.0

        t = 0.0
        out = []

        while t < duration:
            # ✅ This is where MIDI will later modify rate live
            rate = float(self.params.get("rate", 1.0))
            seg_dur = np.random.uniform(dur_lo, dur_hi) / max(rate, 1e-6)
            seg_samples = max(1, int(seg_dur * sr))

            next_amp = memory * amp + (1 - memory) * np.random.uniform(amp_lo, amp_hi)
            next_freq = (memory * 0.85) * freq + (1 - memory * 0.85) * np.random.uniform(freq_lo, freq_hi)

            blend = np.linspace(0, 1, seg_samples)
            amp_env = (1 - blend**1.5) * amp + (blend**1.5) * next_amp
            freq_env = np.linspace(freq, next_freq, seg_samples)

            two_pi = 2 * np.pi
            for k in range(seg_samples):
                phase += two_pi * freq_env[k] / sr
                out.append(amp_env[k] * np.sin(phase))

            amp = next_amp
            freq = next_freq
            t += seg_dur

        return np.array(out, dtype=np.float32)

    # ---------------------------------------------------------
    # OSC backend (unchanged)
    # ---------------------------------------------------------
    def send_osc(self, synth_name: str = "Gendy1", duration: float = 5.0):
        if self.backend not in ["sc", "csound"]:
            raise ValueError("OSC backend must be 'sc' or 'csound'.")

        msg = [
            f"/gendy/{synth_name}",
            self.params["amp_lo"], self.params["amp_hi"],
            self.params["dur_lo"], self.params["dur_hi"],
            self.params["freq_lo"], self.params["freq_hi"],
            self.params["chaos"], self.params["memory"], duration,
        ]

        osc_msg = self._build_osc_message(msg)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(osc_msg, (self.osc_host, self.osc_port))
        sock.close()

    def _build_osc_message(self, values):
        def encode_string(s):
            s = s.encode("utf-8")
            return s + b"\x00" * (4 - len(s) % 4)
        def encode_float(f):
            return np.float32(f).tobytes()

        address = encode_string(values[0])
        type_tags = encode_string("," + "f" * (len(values) - 1))
        args = b"".join(encode_float(v) for v in values[1:])
        return address + type_tags + args
