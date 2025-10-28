# demo_upic_live_v2.py — UPIC live with scale quantisation, velocity loudness, save/replay
# Requires: fastapi, uvicorn, python-osc
#
# Run:
#   cd C:\Users\usuario\Documents\PR_xenakis\xenakis_py\scripts
#   python demo_upic_live_v2.py
# Then open: http://127.0.0.1:8000

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from pythonosc.udp_client import SimpleUDPClient
import math

OSC_HOST = "127.0.0.1"
OSC_PORT = 57120
osc = SimpleUDPClient(OSC_HOST, OSC_PORT)

app = FastAPI()

A4 = 440.0

# --- Scale library (degrees in semitones mod 12) ---
SCALES = {
    "Continuous (no quantise)": None,
    "Chromatic (12)": list(range(12)),
    "Major (Ionian)": [0,2,4,5,7,9,11],
    "Natural Minor (Aeolian)": [0,2,3,5,7,8,10],
    "Harmonic Minor": [0,2,3,5,7,8,11],
    "Melodic Minor (asc)": [0,2,3,5,7,9,11],
    "Pentatonic Major": [0,2,4,7,9],
    "Pentatonic Minor": [0,3,5,7,10],
    "Whole Tone": [0,2,4,6,8,10],
    "Octatonic (H-W)": [0,1,3,4,6,7,9,10],
    "Octatonic (W-H)": [0,2,3,5,6,8,9,11],
    "Messiaen Mode 2": [0,1,3,4,6,7,9,10],
    "Messiaen Mode 3": [0,2,3,4,6,7,8,10,11],
}

TONICS = {
    "C":0, "C#":1, "Db":1, "D":2, "D#":3, "Eb":3, "E":4, "F":5,
    "F#":6, "Gb":6, "G":7, "G#":8, "Ab":8, "A":9, "A#":10, "Bb":10, "B":11
}

def hz_to_semitones(freq: float, ref=A4) -> float:
    return 12.0 * math.log2(max(freq, 1e-9) / ref)

def semitones_to_hz(st: float, ref=A4) -> float:
    return ref * (2.0 ** (st / 12.0))

def quantise_freq(freq: float, scale_name: str, tonic_name: str) -> float:
    """Snap freq to nearest degree of chosen scale relative to tonic. If scale is None, return freq."""
    degrees = SCALES.get(scale_name, None)
    if degrees is None:
        return freq
    tonic = TONICS.get(tonic_name, 0)
    n = hz_to_semitones(freq)         # rel to A4
    # Convert to absolute chroma (0..11) w.r.t C = 0
    # Find nearest semitone q
    q = round(n)
    # Compute chroma with C=0
    chroma = (q % 12)
    # Shift scale degrees by tonic to get absolute chroma set
    allowed = [ (d + tonic) % 12 for d in degrees ]
    # If already allowed, keep q; else nudge q up/down to closest allowed chroma
    if chroma not in allowed:
        # search nearest delta in semitone steps up to +/-6
        best_q = q
        best_dist = 999
        for delta in range(-12,13):
            test = (q + delta) % 12
            if test in allowed and abs(delta) < best_dist:
                best_dist = abs(delta)
                best_q = q + delta
        q = best_q
    return semitones_to_hz(q)

# ---------- Models ----------
class PathData(BaseModel):
    path: list
    width: int
    height: int
    amplitude: float
    glissando_rate: float
    density: float
    scale: str
    tonic: str
    invert_y: bool = False

class PointData(BaseModel):
    x: float
    y: float
    width: int
    height: int
    amplitude: float
    glissando_rate: float
    density: float
    scale: str
    tonic: str
    invert_y: bool = False

# ---------- Helpers ----------
def y_to_freq(y: float, height: int, invert: bool) -> float:
    yy = (height - y) if invert else y
    return 200.0 + (yy / max(height,1)) * 1800.0  # 200–2000 Hz

def convert_path_to_sound(path_pts, w, h, duration=10.0, invert=False, scale="Continuous (no quantise)", tonic="C"):
    """Map X→time, Y→freq, with optional quantisation."""
    out = []
    for x, y in path_pts:
        t = (x / max(w,1)) * duration
        f = y_to_freq(y, h, invert)
        f = quantise_freq(f, scale, tonic)
        out.append((t, f))
    return out

# ---------- Routes ----------
@app.get("/", response_class=HTMLResponse)
async def home():
    # One-page UI
    # (Note: backslashes in regex are escaped in the Python triple-quoted string)
    scale_options = "".join([f'<option value="{name}">{name}</option>' for name in SCALES.keys()])
    tonic_options = "".join([f'<option value="{name}">{name}</option>' for name in ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]])

    return HTMLResponse(f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>UPIC Live v2</title>
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 20px; }}
    canvas {{ border: 1px solid #000; }}
    .controls {{ margin-top: 10px; }}
    label {{ margin-right: 16px; }}
    .row {{ display: flex; gap: 16px; align-items: center; flex-wrap: wrap; margin: 8px 0; }}
    button {{ padding: 6px 10px; }}
  </style>
</head>
<body>
  <h2>UPIC Live v2 — draw and hear (with scale quantisation)</h2>

  <canvas id="drawCanvas" width="800" height="400"></canvas>

  <div class="controls">
    <div class="row">
      <label>Amplitude:
        <input type="range" id="amp" min="0" max="1" step="0.01" value="0.5">
      </label>
      <label>Gliss:
        <input type="range" id="gliss" min="0" max="1" step="0.01" value="0.2">
      </label>
      <label>Density:
        <input type="range" id="dens" min="0" max="1" step="0.01" value="0.8">
      </label>
      <label>Live:
        <input type="checkbox" id="live" checked>
      </label>
      <label>Invert Y:
        <input type="checkbox" id="invert">
      </label>
    </div>

    <div class="row">
      <label>Scale:
        <select id="scale">
          {scale_options}
        </select>
      </label>
      <label>Tonic:
        <select id="tonic">
          {tonic_options}
        </select>
      </label>
      <button onclick="sendPath()">Send to Synth</button>
      <button onclick="replayPath()">Replay</button>
      <button onclick="saveJSON()">Save</button>
      <button onclick="clearCanvas()">Clear</button>
    </div>

    <div style="margin-top:10px">
      <small>Pitch legend (200 Hz → 2000 Hz)</small><br>
      <canvas id="legend" width="240" height="14" style="border:1px solid #ccc"></canvas>
    </div>
  </div>

  <script>
  const canvas = document.getElementById('drawCanvas');
  const ctx = canvas.getContext('2d');
  ctx.lineWidth = 3;
  ctx.lineCap = 'round';

  let drawing = false;
  let path = [];
  let lastSend = 0;
  let lastX = null, lastY = null, lastT = null;
  const THROTTLE_MS = 25; // ~40 fps

  function yToFreq(y, height, invert) {{
    const yy = invert ? (height - y) : y;
    return 200 + (yy / height) * 1800;
  }}
  function freqToColour(freq) {{
    const fMin = 200, fMax = 2000;
    const t = Math.min(1, Math.max(0, (freq - fMin) / (fMax - fMin)));
    const hue = 240 * (1 - t); // blue->red
    return `hsl(${{hue}}, 90%, 50%)`;
  }}
  function freqAmpToColour(freq, amp) {{
    const base = freqToColour(freq);
    const l = 30 + (Math.min(1, Math.max(0, amp)) * 35);
    const m = base.match(/hsl\\(([-\\d.]+),\\s*([\\d.]+)%,\\s*([\\d.]+)%\\)/);
    const hue = Number(m[1]), sat = Number(m[2]);
    return `hsl(${{hue}}, ${{sat}}%, ${{l}}%)`;
  }}

  function drawLegend(){{
    const lg = document.getElementById('legend').getContext('2d');
    for (let i = 0; i < 240; i++) {{
      const t = i / 239;
      const f = 200 + t * (2000 - 200);
      lg.fillStyle = `hsl(${{240*(1-t)}},90%,50%)`;
      lg.fillRect(i, 0, 1, 14);
    }}
  }}
  drawLegend();

  function strokeVelocity(x, y){{
    const t = performance.now();
    if (lastX === null) {{ lastX = x; lastY = y; lastT = t; return 0; }}
    const dt = Math.max(1, t - lastT);
    const dist = Math.hypot(x - lastX, y - lastY);
    lastX = x; lastY = y; lastT = t;
    return dist / dt; // px/ms
  }}
  function velToAmp(v){{
    const base = parseFloat(document.getElementById('amp').value);
    const vNorm = Math.min(1, v * 0.6); // sensitivity
    return Math.max(0, Math.min(1, base * (0.4 + 0.6 * vNorm)));
  }}

  canvas.addEventListener('mousedown', (e) => {{
    drawing = true;
    path = [];
    lastX = lastY = lastT = null;
    ctx.beginPath();
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const invert = document.getElementById('invert').checked;
    const amp = parseFloat(document.getElementById('amp').value);
    const f = yToFreq(y, canvas.height, invert);
    ctx.strokeStyle = freqAmpToColour(f, amp);
    ctx.moveTo(x, y);
  }});

  canvas.addEventListener('mouseup', () => {{
    drawing = false;
    fetch('/point_release', {{ method: 'POST' }}).catch(()=>{{}});
  }});

  canvas.addEventListener('mousemove', (e) => {{
    if (!drawing) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    path.push([x, y]);

    const invert = document.getElementById('invert').checked;
    const gliss = parseFloat(document.getElementById('gliss').value);
    const dens  = parseFloat(document.getElementById('dens').value);
    const scale = document.getElementById('scale').value;
    const tonic = document.getElementById('tonic').value;

    const v = strokeVelocity(x, y);
    const ampDyn = velToAmp(v);

    const f = yToFreq(y, canvas.height, invert);
    ctx.strokeStyle = freqAmpToColour(f, ampDyn);
    ctx.lineTo(x, y);
    ctx.stroke();

    if (document.getElementById('live').checked) {{
      const now = performance.now();
      if (now - lastSend >= THROTTLE_MS) {{
        lastSend = now;
        fetch('/point', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{
            x, y,
            width: canvas.width,
            height: canvas.height,
            amplitude: ampDyn,
            glissando_rate: gliss,
            density: dens,
            scale: scale,
            tonic: tonic,
            invert_y: invert
          }})
        }}).catch(()=>{{}});
      }}
    }}
  }});

  function sendPath() {{
    const gliss = parseFloat(document.getElementById('gliss').value);
    const dens  = parseFloat(document.getElementById('dens').value);
    const amp   = parseFloat(document.getElementById('amp').value);
    const scale = document.getElementById('scale').value;
    const tonic = document.getElementById('tonic').value;
    const invert = document.getElementById('invert').checked;

    fetch('/send_path', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{
        path: path,
        width: canvas.width,
        height: canvas.height,
        amplitude: amp,
        glissando_rate: gliss,
        density: dens,
        scale: scale,
        tonic: tonic,
        invert_y: invert
      }})
    }}).then(r => r.text()).then(t => alert(t));
  }}

  function replayPath(){{
    sendPath();
  }}

  function saveJSON(){{
    const blob = new Blob([JSON.stringify({{path}}, null, 2)], {{type:'application/json'}});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'upic_sketch.json';
    a.click();
    URL.revokeObjectURL(a.href);
  }}

  function clearCanvas(){{
    ctx.clearRect(0,0,canvas.width,canvas.height);
  }}
  </script>
</body>
</html>
    """)

@app.post("/send_path")
async def send_path(data: PathData):
    events = convert_path_to_sound(
        data.path, data.width, data.height, duration=10.0,
        invert=data.invert_y, scale=data.scale, tonic=data.tonic
    )
    for t, f in events:
        # Batch events → /upic (SC spawns short notes)
        osc.send_message("/upic", [t, f, float(data.amplitude),
                                   float(data.glissando_rate), float(data.density)])
    return "Path sent to SuperCollider"

@app.post("/point")
async def point(data: PointData):
    raw = y_to_freq(data.y, data.height, data.invert_y)
    freq = quantise_freq(raw, data.scale, data.tonic)
    osc.send_message("/upic_live", [float(freq),
                                    float(data.amplitude),
                                    float(data.glissando_rate),
                                    float(data.density)])
    return {"ok": True}

@app.post("/point_release")
async def point_release():
    osc.send_message("/upic_live_release", [])
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("demo_upic_live_v2:app", host="127.0.0.1", port=8000, reload=True, log_level="info")
