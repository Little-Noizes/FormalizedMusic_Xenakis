from __future__ import annotations
import math
import random
import time
from dataclasses import dataclass, field
from typing import Callable, Iterable, List, Optional, Sequence, Tuple, Union, Dict

Number = Union[int, float]

# ---------- Utility distributions ----------

def clamp(x: Number, lo: Number, hi: Number) -> Number:
    return lo if x < lo else hi if x > hi else x

def draw_uniform(a: Number, b: Number, rng: random.Random) -> float:
    return rng.uniform(a, b)

def draw_normal(mu: Number, sigma: Number, rng: random.Random) -> float:
    return rng.gauss(mu, sigma)

def draw_exponential(lmbda: Number, rng: random.Random) -> float:
    # mean = 1/lambda
    return rng.expovariate(lmbda)

def draw_categorical(weights: Sequence[float], values: Sequence[Number], rng: random.Random) -> Number:
    assert len(weights) == len(values) and len(values) > 0
    total = sum(weights)
    r = rng.uniform(0.0, total)
    acc = 0.0
    for w, v in zip(weights, values):
        acc += w
        if r <= acc:
            return v
    return values[-1]

# ---------- Probability fields ----------

class ProbField:
    """
    A draw() -> value callable with optional S&H (sample-hold) and jitter.
    """
    def __init__(
        self,
        fn: Callable[[random.Random], float],
        *,
        hold: Optional[float] = None,     # seconds to hold last value
        jitter: float = 0.0,              # additive uniform +-jitter
        hard_clip: Optional[Tuple[float, float]] = None,
        seed: Optional[int] = None
    ):
        self.fn = fn
        self.hold = hold
        self.jitter = jitter
        self.clip = hard_clip
        self.rng = random.Random(seed)
        self._last_val: Optional[float] = None
        self._last_t: float = -1e9

    def draw(self, now: Optional[float] = None) -> float:
        now = time.time() if now is None else now
        # sample & hold
        if self.hold is not None and (now - self._last_t) < self.hold and self._last_val is not None:
            val = self._last_val
        else:
            val = float(self.fn(self.rng))
            self._last_val = val
            self._last_t = now
        # jitter
        if self.jitter:
            val += self.rng.uniform(-self.jitter, +self.jitter)
        # clip
        if self.clip:
            val = clamp(val, self.clip[0], self.clip[1])
        return val

# Convenience builders
def Uniform(a: Number, b: Number, **kw) -> ProbField:
    return ProbField(lambda rng: draw_uniform(a, b, rng), **kw)

def Normal(mu: Number, sigma: Number, **kw) -> ProbField:
    return ProbField(lambda rng: draw_normal(mu, sigma, rng), **kw)

def Exponential(lmbda: Number, **kw) -> ProbField:
    return ProbField(lambda rng: draw_exponential(lmbda, rng), **kw)

def Categorical(values: Sequence[Number], weights: Optional[Sequence[float]] = None, **kw) -> ProbField:
    if weights is None:
        weights = [1.0] * len(values)
    values = list(values)
    weights = list(weights)
    return ProbField(lambda rng: draw_categorical(weights, values, rng), **kw)

# ---------- Event model ----------

@dataclass
class CloudEvent:
    t0: float            # absolute time (s, epoch) the event should start
    pitch: int           # MIDI pitch 0..127
    dur_s: float         # seconds
    vel: int             # MIDI velocity 1..127
    channel: int = 0     # MIDI channel 0..15
    meta: Dict = field(default_factory=dict)

# ---------- Density / timing (Poisson process) ----------

class PoissonScheduler:
    """
    Inhomogeneous Poisson scheduler via thinning:
    - density_fn returns expected events per second at time 't'.
    - max_rate is an upper bound of density_fn over the run window.
    """
    def __init__(self, density_fn: Callable[[float], float], max_rate: float, seed: Optional[int] = None):
        assert max_rate > 0.0
        self.density_fn = density_fn
        self.max_rate = max_rate
        self.rng = random.Random(seed)

    def next_time(self, t: float) -> float:
        # Lewis-Shedler thinning
        while True:
            w = self.rng.expovariate(self.max_rate)
            t = t + w
            u = self.rng.random()
            if u <= (self.density_fn(t) / self.max_rate):
                return t

# ---------- Stochastic Cloud engine ----------

class StochasticCloud:
    """
    Probability-field driven note generator with density scheduling
    and sieve-based pitch constraints.
    """
    def __init__(
        self,
        *,
        pitch_field: ProbField,
        dur_field: ProbField,
        vel_field: ProbField,
        chan_field: ProbField,
        scheduler: PoissonScheduler,
        allowed_pitches: Optional[Iterable[int]] = None,
        pitch_quantise: bool = True,
        pitch_span: Tuple[int, int] = (0, 127),
        seed: Optional[int] = None,
    ):
        self.pitch_field = pitch_field
        self.dur_field = dur_field
        self.vel_field = vel_field
        self.chan_field = chan_field
        self.scheduler = scheduler
        self.allowed_pitches = sorted(set(allowed_pitches)) if allowed_pitches is not None else None
        self.pitch_quantise = pitch_quantise
        self.pitch_span = pitch_span
        self.rng = random.Random(seed)

    # --- helpers ---
    def _quantise_pitch(self, p: float) -> int:
        pi = int(round(p))
        pi = clamp(pi, self.pitch_span[0], self.pitch_span[1])
        if self.allowed_pitches is None or not self.pitch_quantise:
            return int(pi)
        # snap to nearest allowed pitch (in MIDI space)
        ap = self.allowed_pitches
        # early outs
        if pi <= ap[0]: return ap[0]
        if pi >= ap[-1]: return ap[-1]
        # binary search
        lo, hi = 0, len(ap) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if ap[mid] < pi:
                lo = mid + 1
            else:
                hi = mid - 1
        # lo is first >= pi
        idxs = [max(0, lo - 1), min(len(ap) - 1, lo)]
        return min(idxs, key=lambda i: abs(ap[i] - pi))  # return index
        # OOPS! The above returns index; fix below.

    def _quantise_pitch(self, p: float) -> int:  # override with correct return
        pi = int(round(p))
        pi = int(clamp(pi, self.pitch_span[0], self.pitch_span[1]))
        if self.allowed_pitches is None or not self.pitch_quantise:
            return pi
        ap = self.allowed_pitches
        # fast bounds
        if pi <= ap[0]: return ap[0]
        if pi >= ap[-1]: return ap[-1]
        # nearest
        # - find insertion point
        lo, hi = 0, len(ap)
        while lo < hi:
            mid = (lo + hi) // 2
            if ap[mid] < pi:
                lo = mid + 1
            else:
                hi = mid
        # candidates ap[lo-1], ap[lo]
        a = ap[lo - 1]
        b = ap[lo] if lo < len(ap) else ap[-1]
        return a if abs(a - pi) <= abs(b - pi) else b

    # --- main draw ---
    def draw_event(self, now: Optional[float] = None) -> CloudEvent:
        now = time.time() if now is None else now
        pitch = self._quantise_pitch(self.pitch_field.draw(now))
        dur_s = max(0.01, float(self.dur_field.draw(now)))
        vel = int(clamp(round(self.vel_field.draw(now)), 1, 127))
        ch = int(clamp(round(self.chan_field.draw(now)), 0, 15))
        t0 = now  # caller can schedule in real-time using PoissonScheduler.next_time()
        return CloudEvent(t0=t0, pitch=pitch, dur_s=dur_s, vel=vel, channel=ch)

    # --- realtime run loop ---
    def run(
        self,
        sink: "EventSink",
        *,
        t_start: Optional[float] = None,
        t_end: Optional[float] = None,
        max_events: Optional[int] = None,
        time_provider: Callable[[], float] = time.time,
        sleeper: Callable[[float], None] = time.sleep,
    ):
        """
        Realtime loop: schedules events via Poisson thinning and delivers to sink.
        """
        t = time_provider() if t_start is None else t_start
        n = 0
        while True:
            if t_end is not None and t >= t_end:
                break
            if max_events is not None and n >= max_events:
                break
            t = self.scheduler.next_time(t)
            # sleep until t
            dt = t - time_provider()
            if dt > 0:
                sleeper(dt)
            ev = self.draw_event(now=t)
            sink.handle(ev)
            n += 1

# ---------- Sinks ----------

class EventSink:
    def handle(self, ev: CloudEvent) -> None:
        raise NotImplementedError

class PrintSink(EventSink):
    def handle(self, ev: CloudEvent) -> None:
        print(f"[{ev.t0:.3f}] ch={ev.channel:02d} pitch={ev.pitch:03d} "
              f"vel={ev.vel:03d} dur={ev.dur_s:.3f}s")

# Optional: MIDI sink (requires mido + python-rtmidi)
try:
    import mido
    class MidiSink(EventSink):
        def __init__(self, port_name: Optional[str] = None, sustain: bool = False):
            self.out = mido.open_output(port_name) if port_name else mido.open_output()
            self.sustain = sustain

        def handle(self, ev: CloudEvent) -> None:
            now = time.time()
            self.out.send(mido.Message('note_on', note=ev.pitch, velocity=ev.vel, channel=ev.channel, time=0))
            # simplistic scheduling for note_off; in production move to a scheduler thread
            off = mido.Message('note_off', note=ev.pitch, velocity=0, channel=ev.channel, time=ev.dur_s)
            self.out.send(off)
except Exception:
    MidiSink = None  # mido not installed; safe fallback
