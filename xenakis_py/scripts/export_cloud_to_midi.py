import math
import time
from datetime import datetime
from pathlib import Path

from mido import Message, MidiFile, MidiTrack, MetaMessage, bpm2tempo
from xenakis_py.stochastic import (
    StochasticCloud, Normal, Exponential, Categorical, PoissonScheduler
)

# Allowed pitches from your Sieve
ALLOWED = sorted(set(
    [36,38,41,42,45,47,48,50,53,54,57,59,60,62,65,66,69,71,72,74,77,78,81,83,84,86,89,90,93,95]
))

def density_fn(t_abs: float) -> float:
    x = math.sin(t_abs / 10.0) * 0.5 + 0.5
    return 0.5 + 5.5 * x

def build_cloud(seed: int = 99) -> StochasticCloud:
    scheduler = PoissonScheduler(density_fn, max_rate=6.0, seed=2025)

    pitch_field = Normal(mu=66, sigma=12, hard_clip=(36, 96), seed=1)
    dur_field   = Exponential(lmbda=2.0, hard_clip=(0.05, 2.5), seed=2)
    vel_field   = Normal(mu=90, sigma=25, hard_clip=(20, 127), seed=3)
    chan_field  = Categorical(values=[0,1], weights=[3,1], seed=4)

    return StochasticCloud(
        pitch_field=pitch_field,
        dur_field=dur_field,
        vel_field=vel_field,
        chan_field=chan_field,
        scheduler=scheduler,
        allowed_pitches=ALLOWED,
        pitch_quantise=True,
        pitch_span=(36, 96),
        seed=seed
    )

def generate_events_offline(cloud: StochasticCloud, duration_s: float):
    t = time.time()
    end = t + duration_s
    events = []
    while True:
        t = cloud.scheduler.next_time(t)
        if t > end:
            break
        events.append(cloud.draw_event(now=t))
    return events

def seconds_to_ticks(seconds, ticks_per_beat, tempo):
    return int(round(seconds * (ticks_per_beat * (1_000_000 / tempo))))

def export_to_midi(events, out_path, bpm=120, ticks_per_beat=480, separate_tracks_by_channel=True):
    events = sorted(events, key=lambda e: e.t0)
    mid = MidiFile(ticks_per_beat=ticks_per_beat)
    tempo = bpm2tempo(bpm)

    meta = MidiTrack()
    meta.append(MetaMessage('set_tempo', tempo=tempo, time=0))
    mid.tracks.append(meta)

    timed_msgs = []
    t0_ref = events[0].t0 if events else 0.0
    for ev in events:
        start_s = ev.t0 - t0_ref
        end_s = start_s + ev.dur_s
        timed_msgs.append((start_s, ev.channel, Message('note_on', note=ev.pitch, velocity=ev.vel, channel=ev.channel)))
        timed_msgs.append((end_s,   ev.channel, Message('note_off', note=ev.pitch, velocity=0, channel=ev.channel)))

    timed_msgs.sort(key=lambda x: (x[0], 0 if x[2].type == 'note_off' else 1))

    if separate_tracks_by_channel:
        tracks = {}
        last_time_by_channel = {}
        for abs_time_s, ch, msg in timed_msgs:
            if ch not in tracks:
                tracks[ch] = MidiTrack()
                mid.tracks.append(tracks[ch])
                last_time_by_channel[ch] = 0.0
            dt = abs_time_s - last_time_by_channel[ch]
            msg.time = seconds_to_ticks(dt, ticks_per_beat, tempo)
            tracks[ch].append(msg)
            last_time_by_channel[ch] = abs_time_s
    else:
        track = MidiTrack()
        mid.tracks.append(track)
        last_time = 0.0
        for abs_time_s, ch, msg in timed_msgs:
            dt = abs_time_s - last_time
            msg.time = seconds_to_ticks(dt, ticks_per_beat, tempo)
            track.append(msg)
            last_time = abs_time_s

    mid.save(out_path)
    return Path(out_path)

if __name__ == "__main__":
    cloud = build_cloud(seed=99)
    evs = generate_events_offline(cloud, duration_s=60.0)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name = f"cloud_sieve_demo_{stamp}.mid"

    out = export_to_midi(evs, out_path=out_name)
    print(f"Wrote {out.resolve()}")
