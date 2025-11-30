import numpy as np
import soundfile as sf
from xenakis_py.render import render_multichannel_to_wav

# Import GendySynth from your DSS module
from xenakis_py.dss_gendy import GendySynth

# Import multichannel render function
from xenakis_py.render import render_multichannel_to_wav

# -------------------------------
# 🎼 DSS Demo Script: GendySynth
# -------------------------------
# This script demonstrates Dynamic Stochastic Synthesis (DSS)
# as described in Chapters XIII and XIV of "Formalized Music"
# by Iannis Xenakis. It uses a mock backend to generate a stereo
# waveform and exports it to a WAV file.

# Initialize GendySynth with mock backend
synth = GendySynth(backend="mock")

# Generate two mono waveforms for stereo output

min_len = min(len(left_waveform), len(right_waveform))
left_waveform = left_waveform[:min_len]
right_waveform = right_waveform[:min_len]
left_waveform = synth.generate(duration=10.0, seed=42)
right_waveform = synth.generate(duration=10.0, seed=84)

# Stack waveforms into stereo format [samples, channels]
stereo_waveform = np.stack([left_waveform, right_waveform], axis=-1)

# Export to WAV file
render_multichannel_to_wav(stereo_waveform, "gendy_stereo_demo.wav", sr=44100)

print("✅ DSS stereo waveform generated and saved to 'gendy_stereo_demo.wav'")