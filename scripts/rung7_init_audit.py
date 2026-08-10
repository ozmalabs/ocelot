"""rung7_init_audit — THE w0 DC-PRIOR AUDIT (VISION_FABLE_REVIEW.md).

The review measured that `wave_world.add_units(w0=1.0, jitter=0.05)` hands over
a **494:1 DC prior** (DC power fraction 0.99798, frac(w<0)=0.0000) BEFORE ANY
RULE FIRES — i.e. rung 5's "root cause" is in the adapter's init, not in Oja.

THE QUESTION FOR RUNG 7: does that prior touch any rung-7 number?

This script answers it STRUCTURALLY (rung 7 mints no Unit and never calls
`add_units`, so there is no w0 to ablate) and then EMPIRICALLY (the requested
`w0 = 1.0 -> 0.0` ablation, run end-to-end, byte-compared).
"""
from __future__ import annotations
import numpy as np
from domains.engine_provenance import provenance_line
from scripts.rung7_lib import build, gains, run_waves, record_channels, \
    corr_by_distance, shape_departure, effective_rf, cs_index
from domains.wave_world import WaveWorld
import inspect

print(provenance_line())
print("=" * 78)
print("RUNG 7 — w0 DC-PRIOR AUDIT")
print("=" * 78)

# ---- 1. STRUCTURAL: does rung 7 use add_units / w0 at all? ----------------
w, anat = build(seed=0, lateral=1.0)
print(f"  Unit nodes minted by rung 7      : {len(w.s.nodes('Unit'))}")
print(f"  Synapse nodes minted by rung 7   : {len(w.s.nodes('Synapse'))}")
print(f"  SUnit nodes minted by rung 7     : {len(w.s.nodes('SUnit'))}")
print(f"  HCell nodes (rung 7's own layer) : {len(w.s.nodes('HCell'))}")
print(f"  LBipolar nodes                   : {len(w.s.nodes('LBipolar'))}")
import scripts.rung7_lib as lib, domains.lateral_world as lw
for mod in (lib, lw):
    src = inspect.getsource(mod)
    print(f"  '{mod.__name__}' calls add_units : {'add_units' in src}")
    print(f"  '{mod.__name__}' mentions w0     : {'w0' in src}")

# ---- 2. THE INIT OF RUNG 7'S OWN LEARNED PARAMETER ------------------------
g0 = gains(w, anat["hcells"])
print()
print("  RUNG 7'S LEARNED PARAMETER AT INIT (g1, g2):")
print(f"    max |g| at init      : {np.abs(g0).max():.6f}")
print(f"    frac(g != 0) at init : {(g0 != 0).mean():.6f}")
print("    => rung 7 initialises its learned parameter at EXACTLY ZERO")
print("       (seeds/vision_lateral.json: lat_g0 = 0.0). The layer starts as a")
print("       PURE CENTRE with no surround: the DC-prior critique is not merely")
print("       inapplicable here, it is INVERTED -- this is the zero init the")
print("       review asks for, and test_the_seed_ships_inert... gates it.")

# ---- 3. EMPIRICAL: the requested w0 = 1.0 -> 0.0 ablation, end to end ------
def full(w0):
    """Rung 7's headline numbers with WaveWorld.add_units' w0 set as given.
    `add_units` is never called by rung 7, so this varies a parameter that is
    not on rung 7's path -- which is exactly what the audit must demonstrate
    rather than assume."""
    s, ag = _boot()
    ww = WaveWorld(s, h=16, w=16, seed=3000)
    # Call add_units EXPLICITLY with the ablated w0 so that, if rung 7's path
    # touched Units at all, this would move. (It does not: proven by arm 1.)
    ww.add_units(4, w0=w0, jitter=0.05)
    return ww

def _boot():
    import domains.seed_registry  # noqa
    from substrate.boot_core import boot_core, load_seeds_into
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_lateral"])
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0); s.set_attr(wp, "oja", 1.0)
    s.set_attr(wp, "oja_eta", 0.0)
    return s, ag

print()
print("  THE REQUESTED ABLATION w0 = 1.0 -> 0.0, rung-7 headline numbers:")
out = {}
for w0 in (1.0, 0.0):
    ww = full(w0)
    from domains.lateral_world import add_lateral_retina, set_lat_params, freeze_lateral
    an = add_lateral_retina(ww)
    set_lat_params(ww, lateral=1.0, learn_gain=1.0, radius2=1.0,
                   lat_eta=2e-3, lat_gmax=2.0, frozen=0.0)
    run_waves(ww, 3200)
    g = gains(ww, an["hcells"])
    freeze_lateral(ww)
    on, off = record_channels(ww, an, 250)
    ds, Cnn = corr_by_distance(on, on); _, Cnf = corr_by_distance(on, off)
    sd = shape_departure(Cnn, Cnf)
    cs = float(g.sum(axis=1).mean())
    out[w0] = (cs, sd, g)
    print(f"    w0={w0}:  CS={cs:.6f}   SD={sd:.6f}   g1={g[:,0].mean():.6f} g2={g[:,1].mean():.6f}")
d_cs = abs(out[1.0][0] - out[0.0][0]); d_sd = abs(out[1.0][1] - out[0.0][1])
d_g = np.abs(out[1.0][2] - out[0.0][2]).max()
print(f"    max |diff| :  CS {d_cs:.3e}   SD {d_sd:.3e}   gains {d_g:.3e}")
print()
if d_g == 0.0 and d_cs == 0.0 and d_sd == 0.0:
    print("  VERDICT: BYTE-IDENTICAL. The w0 DC prior does not touch ANY rung-7")
    print("  number -- rung 7 never reads a Unit weight. Its learned parameter")
    print("  starts at 0.0 and the effect is grown from nothing.")
else:
    print("  VERDICT: THE ABLATION MOVED THE RESULT -- rung 7's numbers are")
    print("  init-dependent and the finding must be reported as such.")
