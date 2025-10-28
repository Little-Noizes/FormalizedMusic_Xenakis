# demo_upic_live.py — self-contained UPIC demo with live playback + colour-by-pitch
# Requires: fastapi, uvicorn, python-osc
#
# Run:
#   cd C:\Users\usuario\Documents\PR_xenakis\xenakis_py\scripts
#   python demo_upic_live.py
#
# Then open: http://127.0.0.1:8000

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from pythonosc.udp_client import SimpleUDPClient

# ---------- OSC config (SuperCollider defaults) ----------
OSC_HOST = "127.0.0.1"
OSC_PORT = 57120
osc = SimpleUDPClient(OSC_HOST, OSC_PORT)

# ---------- FastAPI app ----------
app = FastAPI()

# ---------- Models ----------
class PathData(BaseModel):
    path: list
    width: int
    height: int
    amplitude: float
    glissando_rate: float
    density: float

class PointData(BaseModel):
    x: float
    y: float
    width: int
    height: int
    amplitude: float
    glissando_rate: float
    density: float

# ---------- Helpers ----------
def convert_path_to_sound(path_pts, w, h, duration=10.0):
    """Map X→time (0..duration), Y→freq (200..2000 Hz)."""
    out = []
    for x, y in path_pts:
        t = (x / w) * duration
        f = 200 + (y / h) * 1800
        out.append((t, f))
    return out

# ---------- Routes ----------
@app.get("/", response_class=HTMLResponse)
async def home():
    # One-page UI (canvas + sliders + live toggle + colour legend)
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>UPIC Drawing Interface</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 20px; }
    canvas { border: 1px solid #000; }
    .controls { margin-top: 10px; }
    label { display: block; margin: 6px 0; }
    .row { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; }
  </style>
</head>
<body>
  <h2>Draw your score (X = time, Y = frequency)</h2>

  <canvas id="drawCanvas" width="800" height="400"></canvas>
  <div class="controls">
    <div class="row">
      <label>Amplitude:
        <input type="range" id="amp" min="0" max="1" step="0.01" value="0.5">
      </label>
      <label>Glissando Rate:
        <input type="range" id="gliss" min="0" max="1" step="0.01" value="0.2">
      </label>
      <label>Density:
        <input type="range" id="dens" min="0" max="1" step="0.01" value="0.8">
      </label>
      <label>Live (play while drawing):
        <input type="checkbox" id="live" checked>
      </label>
      <button onclick="sendPath()">Send to Synth</button>
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
  const THROTTLE_MS = 25; // ~40 fps

  // ---- Mapping helpers ----
  function yToFreq(y, height) {
    // Top high → bottom low (swap to height - y if you want top = low)
    return 200 + (y / height) * 1800; // 200–2000 Hz
  }
  function freqToColour(freq) {
    // 200..2000 Hz -> hue 240 (blue) .. 0 (red)
    const fMin = 200, fMax = 2000;
    const t = Math.min(1, Math.max(0, (freq - fMin) / (fMax - fMin)));
    const hue = 240 * (1 - t); // 240→0
    return `hsl(${hue}, 90%, 50%)`;
  }
  function freqAmpToColour(freq, amp) {
    const base = freqToColour(freq);
    const l = 30 + (Math.min(1, Math.max(0, amp)) * 35); // brightness by amplitude
    const m = base.match(/hsl\\(([-\\d.]+),\\s*([\\d.]+)%,\\s*([\\d.]+)%\\)/);
    const hue = Number(m[1]), sat = Number(m[2]);
    return `hsl(${hue}, ${sat}%, ${l}%)`;
  }

  function drawLegend(){
    const lg = document.getElementById('legend').getContext('2d');
    for (let i = 0; i < 240; i++) {
      const t = i / 239;
      const f = 200 + t * (2000 - 200);
      lg.fillStyle = `hsl(${240*(1-t)},90%,50%)`;
      lg.fillRect(i, 0, 1, 14);
    }
  }
  drawLegend();

  canvas.addEventListener('mousedown', (e) => {
    drawing = true;
    path = [];
    ctx.beginPath();
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const amp  = parseFloat(document.getElementById('amp').value);
    const f = yToFreq(y, canvas.height);
    ctx.strokeStyle = freqAmpToColour(f, amp);
    ctx.moveTo(x, y);
  });

  canvas.addEventListener('mouseup', () => {
    drawing = false;
    fetch('/point_release', { method: 'POST' }).catch(()=>{});
  });

  canvas.addEventListener('mousemove', (e) => {
    if (!drawing) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    path.push([x, y]);

    // Colour-by-pitch for the current segment
    const amp  = parseFloat(document.getElementById('amp').value);
    const gliss = parseFloat(document.getElementById('gliss').value);
    const dens = parseFloat(document.getElementById('dens').value);
    const f = yToFreq(y, canvas.height);
    ctx.strokeStyle = freqAmpToColour(f, amp);

    ctx.lineTo(x, y);
    ctx.stroke();

    if (document.getElementById('live').checked) {
      const now = performance.now();
      if (now - lastSend >= THROTTLE_MS) {
        lastSend = now;
        fetch('/point', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            x, y,
            width: canvas.width,
            height: canvas.height,
            amplitude: amp,
            glissando_rate: gliss,
            density: dens
          })
        }).catch(()=>{});
      }
    }
  });

  function sendPath() {
    const amp  = parseFloat(document.getElementById('amp').value);
    const gliss = parseFloat(document.getElementById('gliss').value);
    const dens = parseFloat(document.getElementById('dens').value);
    fetch('/send_path', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        path: path,
        width: canvas.width,
        height: canvas.height,
        amplitude: amp,
        glissando_rate: gliss,
        density: dens
      })
    }).then(r => r.text()).then(t => alert(t));
  }
  </script>
</body>
</html>
    """)

@app.post("/send_path")
async def send_path(data: PathData):
    events = convert_path_to_sound(data.path, data.width, data.height, duration=10.0)
    for t, f in events:
        # Batch events → /upic (SC will spawn short notes)
        osc.send_message("/upic", [t, f, float(data.amplitude),
                                   float(data.glissando_rate), float(data.density)])
    return "Path sent to SuperCollider"

@app.post("/point")
async def point(data: PointData):
    # Live: map Y→freq (top high). Invert by (height - y) if desired.
    freq = 200 + (data.y / data.height) * 1800
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
    uvicorn.run("demo_upic_live:app", host="127.0.0.1", port=8000, reload=True, log_level="info")
