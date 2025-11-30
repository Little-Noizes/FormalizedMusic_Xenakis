from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from pythonosc.udp_client import SimpleUDPClient
import yaml
from pydantic import BaseModel

# Load scene preset
with open("../scenes/upic_demo.yaml", "r") as f:
    scene = yaml.safe_load(f)

# OSC setup
osc_client = SimpleUDPClient(scene["osc"]["host"], scene["osc"]["port"])
osc_address = scene["osc"]["address"]

# FastAPI app
app = FastAPI()

# Data model for POST
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

# Drawing-to-sound conversion
def convert_path_to_sound(path_points, canvas_width, canvas_height, duration=10.0):
    sound_events = []
    for x, y in path_points:
        time = (x / canvas_width) * duration
        frequency = 200 + (y / canvas_height) * 1800  # Map Y to 200Hz–2000Hz
        sound_events.append((time, frequency))
    return sound_events

# Serve canvas UI
@app.get("/", response_class=HTMLResponse)
async def get_canvas():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>UPIC Drawing Interface</title>
        <style>canvas { border: 1px solid black; }</style>
    </head>
    <body>
        <h2>Draw your score (X=time, Y=frequency)</h2>
        <canvas id="drawCanvas" width="800" height="400"></canvas><br>
        <label>Amplitude: <input type="range" id="amp" min="0" max="1" step="0.01" value="0.5"></label><br>
        <label>Glissando Rate: <input type="range" id="gliss" min="0" max="1" step="0.01" value="0.2"></label><br>
        <label>Density: <input type="range" id="dens" min="0" max="1" step="0.01" value="0.8"></label><br>
        <label>Live (play while drawing): <input type="checkbox" id="live" checked></label><br>
        <button onclick="sendPath()">Send to Synth</button>

        <script>
            const canvas = document.getElementById('drawCanvas');
            const ctx = canvas.getContext('2d');
            let drawing = false;
            let path = [];

            canvas.addEventListener('mousedown', () => { drawing = true; path = []; });
            canvas.addEventListener('mouseup', () => { drawing = false; });
            canvas.addEventListener('mousemove', (e) => {
                if (!drawing) return;
                const rect = canvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                path.push([x, y]);
                ctx.fillRect(x, y, 2, 2);
            });

            function sendPath() {
                const amp = parseFloat(document.getElementById('amp').value);
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
                }).then(response => response.text()).then(data => alert(data));
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

# Handle drawing submission
@app.post("/send_path")
async def send_path(data: PathData):
    sound_events = convert_path_to_sound(
        data.path,
        data.width,
        data.height,
        scene["canvas"]["duration"]
    )
    for time, freq in sound_events:
        osc_client.send_message(osc_address, [time, freq, data.amplitude, data.glissando_rate, data.density])
    return "Path sent to SuperCollider"
@app.post("/point")
async def point(data: PointData):
    # Map canvas Y → frequency (top = high). Invert if you prefer.
    freq = 200 + (data.y / data.height) * 1800  # 200–2000 Hz
    amp  = float(data.amplitude)
    gliss = float(data.glissando_rate)
    dens = float(data.density)
    osc_client.send_message("/upic_live", [freq, amp, gliss, dens])
    return {"ok": True}

@app.post("/point_release")
async def point_release():
    osc_client.send_message("/upic_live_release", [])
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("demo_upic:app", host="127.0.0.1", port=8000, reload=True, log_level="debug")
