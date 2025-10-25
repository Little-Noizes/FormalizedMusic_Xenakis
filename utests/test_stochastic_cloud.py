import time
from xenakis_py.stochastic import Uniform, Normal, Exponential, Categorical, PoissonScheduler, StochasticCloud, PrintSink

def test_fields_draw():
    u = Uniform(0, 1, seed=1)
    n = Normal(0, 1, seed=2)
    e = Exponential(2.0, seed=3)
    c = Categorical([10, 20, 30], [1, 1, 1], seed=4)
    v = [u.draw(), n.draw(), e.draw(), c.draw()]
    assert all(isinstance(x, float) for x in v[:3])
    assert v[3] in {10, 20, 30}

def test_scheduler_monotonic():
    dens = lambda t: 5.0
    sched = PoissonScheduler(dens, max_rate=5.0, seed=5)
    t = 100.0
    t1 = sched.next_time(t)
    t2 = sched.next_time(t1)
    assert t2 > t1 > t

def test_cloud_quantises_to_allowed():
    allowed = [40, 50, 60]
    dens = lambda t: 10.0
    sched = PoissonScheduler(dens, max_rate=10.0, seed=7)
    pf = Normal(55, 5, seed=8)
    cloud = StochasticCloud(
        pitch_field=pf,
        dur_field=Uniform(0.1, 0.2, seed=9),
        vel_field=Uniform(30, 100, seed=10),
        chan_field=Categorical([0], seed=11),
        scheduler=sched,
        allowed_pitches=allowed,
        pitch_quantise=True,
        seed=12
    )
    ev = cloud.draw_event(now=time.time())
    assert ev.pitch in allowed
