# xenakis_py/midi_out.py
from dataclasses import dataclass
from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo

@dataclass
class MidiEvent:
    time: float        # absolute seconds
    pitch: int
    velocity: int = 64
    duration: float = 0.1
    channel: int = 0

class MidiRenderer:
    def __init__(self, ticks_per_beat: int = 480, tempo: int = 120):
        self.ticks_per_beat = ticks_per_beat
        self.tempo_bpm = tempo
        self.events: list[MidiEvent] = []

    def add_event(self, ev: MidiEvent) -> None:
        self.events.append(ev)

    def _sec_to_ticks(self, seconds: float, tempo_us_per_beat: int) -> int:
        # ticks = seconds * (ticks_per_beat * 1e6 / tempo_us_per_beat)
        ticks = seconds * (self.ticks_per_beat * 1_000_000 / tempo_us_per_beat)
        return max(0, int(round(ticks)))

    def save(self, filename: str) -> None:
        """
        Robust save:
        - Build absolute tick times for note_on and note_off
        - Sort by (abs_tick, order) with note_off before note_on at the same tick
        - Emit deltas as non-negative times (clamped at 0 if numerical jitter appears)
        """
        tempo_us = bpm2tempo(self.tempo_bpm)

        abs_msgs: list[tuple[int, int, Message]] = []
        for ev in self.events:
            start = max(0.0, float(ev.time))
            end   = max(0.0, float(ev.time) + float(getattr(ev, "duration", 0.1)))

            on_tick  = self._sec_to_ticks(start, tempo_us)
            off_tick = self._sec_to_ticks(end,   tempo_us)

            # order: 0 = note_off first at same tick, 1 = note_on
            abs_msgs.append((
                on_tick, 1,
                Message('note_on',
                        note=int(ev.pitch),
                        velocity=int(getattr(ev, 'velocity', 64)),
                        channel=int(getattr(ev, 'channel', 0)),
                        time=0)
            ))
            abs_msgs.append((
                off_tick, 0,
                Message('note_off',
                        note=int(ev.pitch),
                        velocity=0,
                        channel=int(getattr(ev, 'channel', 0)),
                        time=0)
            ))

        # Sort to guarantee non-decreasing time
        abs_msgs.sort(key=lambda t: (t[0], t[1]))

        mid = MidiFile(ticks_per_beat=self.ticks_per_beat)
        track = MidiTrack()
        mid.tracks.append(track)
        track.append(MetaMessage('set_tempo', tempo=tempo_us, time=0))

        # (optional but helpful for audibility)
        track.append(MetaMessage('track_name', name='Analogique A', time=0))
        track.append(Message('program_change', channel=0, program=0, time=0))
        track.append(Message('control_change', channel=0, control=7, value=120, time=0))
        last_tick = 0
        for abs_tick, _order, msg in abs_msgs:
            delta = abs_tick - last_tick
            if delta < 0:
                # absolute safety against any rounding/backwards insertion
                delta = 0
            msg.time = delta
            track.append(msg)
            last_tick = abs_tick

        mid.save(filename)
