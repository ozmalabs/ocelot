"""RUNG 3 — POSITIVE CONTROL OF THE LEARNING RULE (instrument check, burned
seeds only). NOT an experimental arm.

Question: can dv_oja_learn produce direction selectivity AT ALL, given the most
favourable input that exists — bars drifting in ONE consistent direction? If it
cannot, then every experimental arm is a null instrument and no confirmatory
test is worth running. Also fixes the TIMESCALE: how many steps does it need?
"""
import sys, time
import numpy as np
sys.path.insert(0,'scratchpad3')
import domains.seed_registry
from substrate.boot_core import boot_core, load_seeds_into
from domains.wave_world import WaveWorld
from domains.dorsal_world import (add_dunits, probe_dsi, drifting_bar,
                                  reset_retina, dunit_weights)

H=W=16; RF=7; MAXD=3; NU=10

def mk(seed, eta):
    s,ag=boot_core(); load_seeds_into(s,ag,['vision_dorsal'])
    dp=s.nodes('DorsalParams')[0]; wp=s.nodes('WaveParams')[0]
    s.set_attr(dp,'dorsal',1.0); s.set_attr(dp,'oja_eta',eta)
    s.set_attr(wp,'propagate',0.0)
    w=WaveWorld(s,h=H,w=W,seed=seed,track_prev_burst=True)
    us=add_dunits(w,NU,rf=RF,max_delay=MAXD,rng=np.random.default_rng(seed))
    return s,w,us

def train_one_direction(w, steps, theta=0.0):
    """Bars drifting in ONE direction, repeatedly. The most direction-structured
    input possible."""
    i=0
    while i < steps:
        reset_retina(w)
        for p in np.arange(-2.0, 18.0, 1.0):
            if i>=steps: break
            w.step(ignite_k=0, frame=drifting_bar(H,W,theta,float(p)))
            i+=1

print("POSITIVE CONTROL — can the rule learn direction from a ONE-DIRECTION stimulus?")
print("(burned seeds 0-5; NOT an experimental arm)\n")
for eta in (5e-4, 2e-3, 1e-2):
    print("eta=%.0e" % eta)
    for steps in (0, 400, 1600, 6400):
        vals=[]; nan=0
        for sd in range(4):
            s,w,us=mk(sd,eta)
            train_one_direction(w, steps)
            W_=np.concatenate([dunit_weights(w,u) for u in us])
            nan+=int(np.isnan(W_).sum())
            vals.append(float(probe_dsi(w,us,seed=sd).mean()))
        print("   %5d steps   DSI %+.4f  (SD %.4f)  NaN=%d"
              % (steps, np.mean(vals), np.std(vals,ddof=1), nan), flush=True)
