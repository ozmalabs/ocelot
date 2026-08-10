"""RUNG 3B harness. Identical to r3lib except for the bistable knobs."""
import numpy as np
import domains.seed_registry
from substrate.boot_core import boot_core, load_seeds_into
from domains.wave_world import WaveWorld
from domains.dorsal_world import add_dunits, probe_dsi, gaze_walk, dunit_weights

H = W = 16; RF = 7; MAXD = 3; NU = 10
P1 = 1600; P2 = 1600            # FROZEN (rung 3)
ETA = 2e-3                      # FROZEN (rung 3's positive control)
VIDEO32 = "scratchpad3/video420_32.npy"
ARMS = ("untrained", "dark", "normal", "strobe")


def boot(seed, *, bistable=0.0, bi_eta=0.0):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_dorsal"])
    dp = s.nodes("DorsalParams")[0]; wp = s.nodes("WaveParams")[0]
    s.set_attr(dp, "dorsal", 1.0)
    s.set_attr(dp, "oja_eta", ETA)
    s.set_attr(dp, "bistable", float(bistable))
    s.set_attr(dp, "bi_eta", float(bi_eta))
    s.set_attr(wp, "propagate", 1.0)
    w = WaveWorld(s, h=H, w=W, seed=seed, track_prev_burst=True)
    us = add_dunits(w, NU, rf=RF, max_delay=MAXD, rng=np.random.default_rng(seed))
    return s, w, us, dp, wp


def retinal_stream(video32, seed):
    return gaze_walk(video32, P2, H, W, rng=np.random.default_rng(seed + 91_000))


def run(arm, seed, video32, *, bistable=0.0, bi_eta=0.0):
    s, w, us, dp, wp = boot(seed, bistable=bistable, bi_eta=bi_eta)
    if arm == "untrained":
        return float(probe_dsi(w, us, seed=seed).mean())
    for i in range(P1):
        w.step(ignite_k=1 if i % 5 == 0 else 0, frame=None)
    if arm == "dark":
        for i in range(P2):
            w.step(ignite_k=1 if i % 5 == 0 else 0, frame=None)
    else:
        s.set_attr(wp, "propagate", 0.0)
        fr = retinal_stream(video32, seed)
        if arm == "strobe":
            fr = fr[np.random.default_rng(seed + 77_000).permutation(len(fr))]
        for i in range(P2):
            w.step(ignite_k=0, frame=fr[i])
    return float(probe_dsi(w, us, seed=seed).mean())


def signflip(d, rng, n=20000):
    obs = d.mean()
    c = sum(abs((d * rng.choice([-1.0, 1.0], size=len(d))).mean()) >= abs(obs)
            for _ in range(n))
    bs = np.array([rng.choice(d, len(d)).mean() for _ in range(n)])
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return obs, c / n, lo, hi
