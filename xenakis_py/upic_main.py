from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from xenakis_py.upic_draw import convert_path_to_sound
from pythonosc.udp_client import SimpleUDPClient

app = FastAPI()
app.mount("/static", StaticFiles(directory="webui"), name="static")

class PathData(BaseModel):
    path: list
    width: int
    height: int

osc_client = SimpleUDPClient("127.0.0.1", 57120)  # SuperCollider default port

@app.get("/", response_class=HTMLResponse)
async def get_canvas():
    with open("webui/canvas.html", "r") as f:
        return f.read()

@app.post("/send_path")
async def send_path(data: PathData):
    sound_events = convert_path_to_sound(data.path, data.width, data.height)
    for time, freq in sound_events:
        osc_client.send_message("/upic", [time, freq])
    return "Path sent to SuperCollider"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)