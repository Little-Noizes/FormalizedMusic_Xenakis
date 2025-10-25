"""
Demo: Generate pitches from a Xenakis-style sieve and write a MIDI file.
Usage:
    python -m scripts.demo_sievescape --scene scenes/default.yaml
"""

import argparse
from typing import List
from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo
import yaml
from datetime import datetime
from xenakis_py.sieve import Sieve  # use the real engine

def load_scene(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def sieve_from_scene(scene: dict) -> Sieve:
    # scene["sieve"]["clauses"] can use 'residues' (preferred) or legacy 'residue'
    clauses_in = scene.get("sieve", {}).get("clauses", [])
    clauses: List = []
    for op, d in clauses_in:
        op_norm = "complement" if op == "negation" else op  # accept 'negation' as alias
        m = int(d["modulus"])
        if "residues" in d and d["residues"] is not None:
            res = [int(r) for r in d["residues"]]
        else:
            # legacy single residue
            res = [int(d["residue"])]
        clauses.append((op_norm, {"modulus": m, "residues": res}))
    s = Sieve(clauses)
    # allow shift at either scene root or under sieve:{shift:...}
    shift = scene.get("shift", scene.get("sieve", {}).get("shift", 0))
    s.shift(int(shift))
    return s

def generate_sequence(sv: Sieve, length_steps: int, low: int, high: int) -> List[int]:
    # Build a reservoir across at least two periods for variety
    period = max(1, sv.period())
    ints = sv.generate(0, max(512, period * 2))  # inclusive in your engine
    if not ints:
        return []
    # Turn sparse set into a stepwise sequence by tiling through periods
    seq = []
    i = 0
    while len(seq) < length_steps:
        seq.append(ints[i % len(ints)] + (i // len(ints)) * period)
        i += 1
    # Map to MIDI register
    span = max(1, high - low + 1)
    return [low + (n % span) for n in seq]

def write_midi(pitches: List[int], bpm: int, filename: str, channel: int = 0):
    """
    Write a sequence of MIDI notes to file, with timestamped filename to avoid overwriting.
    
    Parameters:
        pitches (List[int]): List of MIDI note numbers.
        bpm (int): Tempo in beats per minute.
        filename (str): Base output filename (e.g., 'demo_sieve.mid').
        channel (int): MIDI channel (0–15).
    """

    # Add timestamp so files never overwrite
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if "." in filename:
        base, ext = filename.rsplit(".", 1)
        filename = f"{base}_{timestamp}.{ext}"
    else:
        filename = f"{filename}_{timestamp}.mid"

    # Create MIDI container
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    # Set tempo
    tempo = bpm2tempo(bpm)
    track.insert(0, MetaMessage('set_tempo', tempo=tempo, time=0))

    # Note length in ticks (480 tpq default -> 240 = eighth note, 480 = quarter note)
    step_ticks = 480

    # Write notes
    for note in pitches:
        track.append(Message('note_on', note=note, velocity=96, time=0, channel=channel))
        track.append(Message('note_off', note=note, velocity=64, time=step_ticks, channel=channel))

    # Save
    mid.save(filename)
    print(f"[OK] MIDI file written: {filename}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", default="scenes/default.yaml", help="Path to YAML scene")
    args = ap.parse_args()

    scene = load_scene(args.scene)
    bpm = int(scene.get("bpm", 96))
    length_steps = int(scene.get("length_steps", 64))
    pitch_map = scene.get("pitch_map", {"low": 48, "high": 84})
    low, high = int(pitch_map["low"]), int(pitch_map["high"])
    channel = int(scene.get("routing", {}).get("midi", {}).get("channel", 0))

    sieve = sieve_from_scene(scene)
    pitches = generate_sequence(sieve, length_steps, low, high)
    if not pitches:
        print("[WARN] Sieve produced no notes—check clauses/residues/shift.")
        return

    out_cfg = scene.get("output", {})
    if out_cfg.get("write_midi_file", True):
        filename = out_cfg.get("midi_filename", "demo_sieve.mid")
        write_midi(pitches, bpm, filename, channel=channel)

    # OSC optional (commented out so python-osc isn’t required yet)
    # if out_cfg.get("realtime", False):
    #     from pythonosc.udp_client import SimpleUDPClient
    #     host = scene.get("routing", {}).get("osc", {}).get("host", "127.0.0.1")
    #     port = scene.get("routing", {}).get("osc", {}).get("port", 57120)
    #     client = SimpleUDPClient(host, port)
    #     for p in pitches:
    #         client.send_message("/note", p)

    # Print some scene info
    print(f"Period (LCM): {sieve.period()}")
    print(f"First 16 pitches: {pitches[:16]}")

if __name__ == "__main__":
    main()
