import os
import numpy as np
import soundfile as sf
from datetime import datetime

# Force output directory
ROOT_OUT = r"C:\Users\usuario\Documents\PR_xenakis"

def render_multichannel_to_wav(
    waveform: np.ndarray,
    filename: str,
    sr: int = 48000,
    bit_depth: int = 16
) -> str:
    """
    Save a multichannel audio waveform to WAV with timestamp.
    waveform must be shape [samples, channels].
    """

    if waveform.ndim != 2:
        raise ValueError("waveform must be 2D [samples, channels].")

    # Normalise if peak exceeds 1.0
    peak = float(np.max(np.abs(waveform)))
    if peak > 1.0:
        waveform = waveform / peak

    # Create timestamped filename
    timestamp = datetime.now().strftime("_%Y%m%d_%H%M")
    base, ext = os.path.splitext(filename)
    if not ext:
        ext = ".wav"
    final_name = f"{base}{timestamp}{ext}"

    # Ensure output directory exists
    os.makedirs(ROOT_OUT, exist_ok=True)
    full_path = os.path.join(ROOT_OUT, final_name)

    # Bit depth subtype + dtype handling
    subtype_map = {
        16: ('PCM_16', np.int16,  32767),
        24: ('PCM_24', np.int32,  8388607),
        32: ('FLOAT',  np.float32, 1.0),
    }

    if bit_depth not in subtype_map:
        raise ValueError("bit_depth must be 16, 24 or 32")

    subtype, dtype, scale = subtype_map[bit_depth]

    if bit_depth == 32:
        out = waveform.astype(np.float32)
    else:
        out = (waveform * scale).clip(-scale, scale-1).astype(dtype)

    # Write file
    sf.write(full_path, out, sr, subtype=subtype)

    print(f"✅ Saved WAV → {full_path}")
    return full_path
