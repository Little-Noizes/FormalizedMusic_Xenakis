from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
import os

from xenakis_py.dss_gendy import GendySynth
from xenakis_py.render import render_multichannel_to_wav

# Constants
BIT_DEPTH = 16
SAMPLE_RATE = 48000
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# FastAPI app
app = FastAPI()

# Request model
class DSSRequest(BaseModel):
    amp_lo: float
    amp_hi: float
    dur_lo: float
    dur_hi: float
    freq_lo: float
    freq_hi: float
    chaos: float
    memory: float
    duration: float

@app.post("/render-dss")
async def render_dss(request: DSSRequest):
    """
    FastAPI endpoint to render DSS waveform using GendySynth (mock backend).
    Returns stereo WAV file at 48kHz, 16-bit.
    Based on DSS principles from Formalized Music, Chapters XIII and XIV.
    """
    # Initialize GendySynth with parameters
    synth = GendySynth(
        backend="mock",
        params={
            "amp_lo": request.amp_lo,
            "amp_hi": request.amp_hi,
            "dur_lo": request.dur_lo,
            "dur_hi": request.dur_hi,
            "freq_lo": request.freq_lo,
            "freq_hi": request.freq_hi,
            "chaos": request.chaos,
            "memory": request.memory,
            "distribution": "linear"
        }
    )

    # Generate stereo waveform
    left = synth.generate_waveform(duration=request.duration, sr=SAMPLE_RATE)
    right = synth.generate_waveform(duration=request.duration, sr=SAMPLE_RATE)

    # Match lengths
    min_len = min(len(left), len(right))
    left = left[:min_len]
    right = right[:min_len]
    stereo = np.stack([left, right], axis=-1)

    # Render to WAV
    filename = os.path.join(OUTPUT_DIR, "dss_render.wav")
    render_multichannel_to_wav(stereo, filename, sr=SAMPLE_RATE, bit_depth=BIT_DEPTH)

    return {
        "message": "✅ DSS waveform rendered successfully.",
        "filename": filename
    }