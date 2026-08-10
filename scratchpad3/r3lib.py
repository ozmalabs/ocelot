"""RUNG 3 shared harness. One place that defines the arms, so the pilot and the
confirmatory run cannot drift apart."""
import numpy as np
import domains.seed_registry
from substrate.boot_core import boot_core, load_seeds_into
from domains.wave_world import WaveWorld
from domains.dorsal_world import add_dunits, probe_dsi, gaze_walk, dunit_weights

H = W = 16
RF = 7
MAXD = 3
NU = 10
P1 = 1600           # phase 1: waves, to the Oja fixed point (rung-2's verified length)
P2 = 1600           # phase 2: equal duration in EVERY arm (fixed by the positive control)
ETA = 2e-3          # FIXED by the POSITIVE CONTROL, before any arm: at 5e-4 the
                    # rule moves DSI by 0.000 even on a PERFECT single-direction
                    # stimulus at 400 steps, so the arms would be a null
                    # instrument. At 2e-3 it reaches 0.215 (21% of dynamic range)
                    # by 1600 steps and is measurably STABLE (0 NaN everywhere) --
                    # the dorsal delay-gating keeps y far below the ventral
                    # population, which is what diverges at this rate.
VIDEO32 = "scratchpad3/video420_32.npy"

ARMS = ("untrained", "dark", "normal", "strobe")


def _boot(seed):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_dorsal"])
    dp = s.nodes("DorsalParams")[0]
    wp = s.nodes("WaveParams")[0]
    s.set_attr(dp, "dorsal", 1.0)
    s.set_attr(dp, "oja_eta", ETA)
    s.set_attr(wp, "propagate", 1.0)
    w = WaveWorld(s, h=H, w=W, seed=seed, track_prev_burst=True)
    # SAME rng draw per seed => the DELAYS ARE IDENTICAL ACROSS ARMS. That is
    # what makes the pairing valid: random delays confer a real innate direction
    # bias (measured floor 0.111), and it cancels in the paired difference only
    # if every arm inherits the same one.
    us = add_dunits(w, NU, rf=RF, max_delay=MAXD, rng=np.random.default_rng(seed))
    return s, w, us, dp, wp


def retinal_stream(video32, seed):
    """The `normal` arm's retinal frames: real video seen through a drifting
    eye. `strobe` gets the SAME frames permuted, so the two arms have identical
    spatial statistics and identical duty cycle and differ ONLY in order."""
    return gaze_walk(video32, P2, H, W, rng=np.random.default_rng(seed + 91_000))


def run(arm, seed, video32):
    s, w, us, dp, wp = _boot(seed)
    if arm == "untrained":
        return float(probe_dsi(w, us, seed=seed).mean())
    for i in range(P1):                       # phase 1: identical in every arm
        w.step(ignite_k=1 if i % 5 == 0 else 0, frame=None)
    if arm == "dark":                         # dark-reared: waves CONTINUE
        for i in range(P2):
            w.step(ignite_k=1 if i % 5 == 0 else 0, frame=None)
    else:
        s.set_attr(wp, "propagate", 0.0)      # eye opening: waves cease
        fr = retinal_stream(video32, seed)
        if arm == "strobe":                   # strobe-reared: order destroyed
            fr = fr[np.random.default_rng(seed + 77_000).permutation(len(fr))]
        for i in range(P2):
            w.step(ignite_k=0, frame=fr[i])
    return float(probe_dsi(w, us, seed=seed).mean())


def event_rates(seed, video32):
    """Descriptive only: the transient (onset) rate each arm actually delivers.
    Reported so the reader knows what each arm was, never tested."""
    out = {}
    for arm in ("dark", "normal", "strobe"):
        s, w, us, dp, wp = _boot(seed)
        if arm == "dark":
            gen = (None for _ in range(200))
            ig = True
        else:
            s.set_attr(wp, "propagate", 0.0)
            f = retinal_stream(video32, seed)
            if arm == "strobe":
                f = f[np.random.default_rng(seed + 77_000).permutation(len(f))]
            gen = (f[i] for i in range(200))
            ig = False
        n_tr = n_bu = 0
        for i, fr in enumerate(gen):
            w.step(ignite_k=(1 if (ig and i % 5 == 0) else 0), frame=fr)
            st = float(w.s.node(w.retina)["attrs"]["step"])
            for c in w.cells.values():
                at = w.s.node(c)["attrs"]
                n_tr += int(float(at["dlast_burst"]) == st)
                n_bu += int(float(at["bursting"]) == 1.0)
        out[arm] = (n_tr / (200 * H * W), n_bu / (200 * H * W))
    return out


def signflip(d, rng, n=20000):
    obs = d.mean()
    c = sum(abs((d * rng.choice([-1.0, 1.0], size=len(d))).mean()) >= abs(obs)
            for _ in range(n))
    bs = np.array([rng.choice(d, len(d)).mean() for _ in range(n)])
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return obs, c / n, lo, hi
