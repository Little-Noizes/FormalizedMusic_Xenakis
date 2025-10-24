"""
Demo: Generate pitches from a Xenakis-style sieve and write/send MIDI or OSC.
Usage:
    python demo_sievescape.py --scene scenes/default.yaml

Features:
- Loads a YAML scene with sieve clauses (union, intersection, negation), bpm, routing, etc.
- Applies optional shift to sieve set.
- Generates a pitch sequence mapped into a MIDI range.
- Writes a .mid file and/or sends notes via OSC.
"""

import argparse
import time
import yaml
from typing import List, Tuple, Dict, Set
from mido import Message, MidiFile, MidiTrack, bpm2tempo
from pythonosc.udp_client import SimpleUDPClient
from sieve import Sieve

# -----------------------------
# Sieve Class with Negation + Shift
# -----------------------------

class Sieve:
    def __init__(self, clauses: List[Tuple[str, Dict]], shift: int = 0):
        self.clauses = clauses
        self.shift = shift

    def generate(self, start: int, end: int) -> Set[int]:
        sets = []
        for op, params in self.clauses:
            modulus = params['modulus']
            residue = params['residue']
            s = {i for i in range(start, end) if i % modulus == residue}
            sets.append((op, s))

        result = set()
        for op, s in sets:
            if op == 'union':
                result |= s
            elif op == 'intersection':
                result &= s if result else s
            elif op == 'negation':
                result -= s

        if self.shift:
            result = {i + self.shift for i in result}

        return result

    def period(self) -> int:
        from math import lcm
        moduli = [clause[1]['modulus'] for clause in self.clauses]
        return lcm(*moduli)

# -----------------------------
# MIDI and OSC Output
# -----------------------------

def write_midi(pitches: List[int], bpm: int, filename: str, channel: int = 0):
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    tempo = bpm2tempo(bpm)
    track.append(Message('program_change', program=12, time=0))
    track.append(Message('control_change', control=64, value=127, time=0))
    track.insert(0, Message('set_tempo', tempo=tempo, time=0))

    for pitch in pitches:
        track.append(Message('note_on', note=pitch, velocity=96, time=0, channel=channel))
        track.append(Message('note_off', note=pitch, velocity=64, time=480, channel=channel))

    mid.save(filename)
    print(f"[OK] MIDI file written: {filename}")

def send_osc(pitches: List[int], host: str, port: int):
    client = SimpleUDPClient(host, port)
    for pitch in pitches:
        client.send_message("/note", pitch)

# -----------------------------
# Main Demo Logic
# -----------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", default="scenes/default.yaml", help="Path to YAML scene")
    args = parser.parse_args()

    with open(args.scene, "r") as f:
        scene = yaml.safe_load(f)

    bpm = scene.get("bpm", 96)
    length_steps = scene.get("length_steps", 32)
    pitch_map = scene.get("pitch_map", {"low": 48, "high": 84})
    low, high = pitch_map["low"], pitch_map["high"]

    sieve_cfg = scene.get("sieve", {})
    shift = sieve_cfg.get("shift", 0)
    clauses = sieve_cfg.get("clauses", [])
    parsed_clauses = [(op, {k: v for k, v in d.items() if k in ["modulus", "residue"]}) for op, d in clauses]

    sv = Sieve(parsed_clauses, shift=shift)
    period = sv.period()
    sieve_set = sv.generate(0, max(256, period * 2))

    span = max(1, high - low + 1)
    pitches = [low + (i % span) for i in sorted(sieve_set)[:length_steps]]

    output_cfg = scene.get("output", {})
    if output_cfg.get("write_midi_file", False):
        filename = output_cfg.get("midi_filename", "output.mid")
        write_midi(pitches, bpm, filename)

    if output_cfg.get("realtime", False):
        osc_cfg = scene.get("routing", {}).get("osc", {})
        host = osc_cfg.get("host", "127.0.0.1")
        port = osc_cfg.get("port", 57120)
        send_osc(pitches, host, port)

    metadata = scene.get("metadata", {})
    print(f"Scene: {metadata.get('scene_name', 'Unnamed')}")
    print(f"Author: {metadata.get('author', 'Unknown')}")
    print(f"Period: {period}")
    print(f"Pitches: {pitches}")

if __name__ == "__main__":
    main()