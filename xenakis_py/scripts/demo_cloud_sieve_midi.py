import math
import time
from xenakis_py.stochastic import (
    StochasticCloud, ProbField, Uniform, Normal, Exponential, Categorical,
    PoissonScheduler, PrintSink, MidiSink
)

# ---- Your sieve output (replace with actual import) ----
# Suppose your sieve returns allowed MIDI pitches (e.g., 36..96 with patterning).
ALLOWED = sorted(set(
    [36,38,41,42,45,47,48,50,53,54,57,59,60,62,65,66,69,71,72,74,77,78,81,83,84,86,89,90,93,95]
))

# ---- Density as a function of time (events/sec) ----
def density_fn(t_abs: float) -> float:
    # slow 10s breathing between 0.5 and 6.0 eps
    x = math.sin(t_abs / 10.0) * 0.5 + 0.5  # 0..1
    return 0.5 + 5.5 * x

scheduler = PoissonScheduler(density_fn, max_rate=6.0, seed=2025)

pitch_field   = Normal(mu=66, sigma=12, hold=0.0, hard_clip=(36, 96), seed=1)
dur_field     = Exponential(lmbda=2.0, hard_clip=(0.05, 2.5), seed=2)   # mean 0.5 s, clipped
vel_field     = Normal(mu=90, sigma=25, hard_clip=(20, 127), seed=3)
chan_field    = Categorical(values=[0,1], weights=[3,1], seed=4)        # mostly ch 0, sometimes ch 1

cloud = StochasticCloud(
    pitch_field=pitch_field,
    dur_field=dur_field,
    vel_field=vel_field,
    chan_field=chan_field,
    scheduler=scheduler,
    allowed_pitches=ALLOWED,        # <- sieve constraint
    pitch_quantise=True,
    pitch_span=(36, 96),
    seed=99
)

sink = PrintSink()
# If you have mido + a virtual port to your synth:
# from xenakis_py.stochastic import MidiSink
# sink = MidiSink()  # or MidiSink("Focusrite USB MIDI") etc.

cloud.run(
    sink,
    t_start=time.time(),
    t_end=time.time() + 20.0,  # run 20 seconds for the demo
)
