"""RUNG 5 — THE FULL RE-MEASUREMENT through a properly FROZEN probe.

Everything measured before `complex_cells.freeze()` existed was contaminated:
`oja=0` does not disable learning, it ENABLES the fixed-sign Butts rules +
homeostatic rescaling (each is gated on `oja == 0.0`), so the probe rewrote the
WTA winner's synapses on every presentation. This re-runs, in one place:

  PART A  instrument calibration + the FLOOR          (PROTOCOL 1)
  PART B  the PRECONDITION: do the model's Units have simple-cell responses?
  PART C  the CUnit floor / ideal target / blob references
  PART D  the POSITIVE CONTROL: can the rule make a complex cell at all?
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np

import domains.seed_registry  # noqa: F401
from substrate.boot_core import boot_core, load_seeds_into
from domains.wave_world import WaveWorld
from domains.cortex_sheet import add_cortex, orientation_selectivity
from domains.complex_cells import (add_complex_layer, pool_weights, freeze,
                                   cell_stats, gabor, install_weights,
                                   pool_weights as pw_of)
from scripts.rung5_poscontrol import build, Trainer, structure, ORIS, PERIOD

H = W = 16
RF = 7
ETA = 5e-4


def wave_units(seed: int, steps: int):
    """The model's OWN simple layer: a retinotopic sheet trained on waves."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_maps", "vision_complex"])
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    s.set_attr(wp, "oja", 1.0)
    s.set_attr(wp, "oja_eta", ETA)
    w = WaveWorld(s, h=H, w=W, seed=seed)
    us = add_cortex(w, 6, 6, rf=RF)
    for i in range(steps):
        w.step(ignite_k=1 if i % 5 == 0 else 0)
    freeze(w)
    return w, us


def set_pool(w, cu, units, vals):
    for cs in w.s.in_neighbours(cu, "cpost"):
        pre = w.s.in_neighbours(cs, "cpre")[0]
        w.s.set_attr(cs, "cweight", float(vals[units.index(pre)]))


if __name__ == "__main__":
    np.set_printoptions(precision=3, suppress=True)

    print("=" * 76)
    print("PART A — CALIBRATION + FLOOR (frozen probe). period =", PERIOD)
    print("=" * 76)
    w, us = wave_units(0, 0)
    g = gabor(RF, 90.0, 0.0, PERIOD)
    install_weights(w, us[14], g)                       # ideal SIMPLE
    install_weights(w, us[21], g - g.min() + 0.05)      # same Gabor, all >= 0
    st = cell_stats(w, [us[14], us[21]], key="act", period=PERIOD)
    for i, nm in ((0, "ideal GABOR      "), (1, "ideal GABOR + DC ")):
        print(f"  {nm}: anisotropy={orientation_selectivity(w.receptive_field([us[14],us[21]][i])):.4f}  "
              f"OSI={st['osi'][i]:.4f}  F1/F0={st['f1f0'][i]:.3f}  "
              f"F1/F0_evoked={st['f1f0_evoked'][i]:.3f}")
    # verify the freeze actually holds
    before = np.stack([w.receptive_field(u) for u in us])
    cell_stats(w, [us[14]], key="act", period=PERIOD)
    after = np.stack([w.receptive_field(u) for u in us])
    print(f"  FREEZE CHECK: max |dw| across a probe = {np.abs(after-before).max():.3e}")

    print("\n" + "=" * 76)
    print("PART B — THE PRECONDITION: do the model's Units respond like simple cells?")
    print("=" * 76)
    for label, steps, seed in (("UNTRAINED (floor)", 0, 1), ("TRAINED 1600", 1600, 0),
                               ("TRAINED 3200", 3200, 2)):
        w, us = wave_units(seed, steps)
        st = cell_stats(w, us, key="act", period=PERIOD)
        an = np.mean([orientation_selectivity(w.receptive_field(u)) for u in us])
        wts = np.concatenate([w.receptive_field(u).flatten() for u in us])
        print(f"  {label:18s}: OSI={st['osi'].mean():.4f} (max {st['osi'].max():.4f})  "
              f"F1/F0={np.nanmean(st['f1f0']):.3f}  F1/F0_evoked={np.nanmean(st['f1f0_evoked']):.3f}")
        print(f"  {'':18s}  weight anisotropy={an:.4f}   frac(w<0)={(wts<0).mean():.4f}  "
              f"baseline/act={st['baseline'].mean()/max(st['tuning'].mean(),1e-9):.3f}")

    print("\n" + "=" * 76)
    print("PART C — CUnit REFERENCES (frozen probe)")
    print("=" * 76)
    refs = [("FLOOR  untrained (uniform pooling)", None),
            ("TARGET ideal pooling (4 phases of ori=0)", "ideal"),
            ("BLOB   pooling all 16 orientations", "blob")]
    for name, kind in refs:
        w2, units2, cu2, labels2 = build(0, trace_delta=0.2, cx_eta=ETA)
        if kind == "ideal":
            set_pool(w2, cu2, units2, [1.0 if l[0] == 0.0 else 0.0 for l in labels2])
        elif kind == "blob":
            set_pool(w2, cu2, units2, [1.0] * len(labels2))
        freeze(w2)
        st = cell_stats(w2, [cu2], key="cact", period=PERIOD)
        print(f"  {name:42s}: F1/F0={st['f1f0'][0]:.3f}  OSI={st['osi'][0]:.3f}")

    print("\n" + "=" * 76)
    print("PART D — POSITIVE CONTROL: can the rule make a complex cell at all?")
    print("=" * 76)
    for td, name in ((0.2, "SLOWNESS (trace_delta=0.2)"),
                     (1.0, "ABLATED  (trace_delta=1.0)")):
        for eta in (1e-4, 2e-5):
            w3, units3, cu3, labels3 = build(0, trace_delta=td, cx_eta=eta)
            pre = cell_stats(w3, units3[:4], key="act", period=PERIOD)
            # NOTE: cell_stats above froze the world; re-arm learning to train.
            w3.s.set_attr(w3.s.nodes("WaveParams")[0], "oja_eta", 0.0)  # bank stays fixed
            w3.s.set_attr(w3.s.nodes("ComplexParams")[0], "cx_eta", float(eta))
            Trainer(w3, 0).run(3200)
            freeze(w3)
            post = cell_stats(w3, [cu3], key="cact", period=PERIOD)
            pw = pool_weights(w3, cu3, units3)
            byo = {o: round(float(pw[[k for k, l in enumerate(labels3) if l[0] == o]].sum()), 3)
                   for o in ORIS}
            print(f"\n  {name}  cx_eta={eta:g}")
            print(f"    pooled SIMPLE cells : F1/F0={np.round(pre['f1f0'],2)}  OSI={np.round(pre['osi'],2)}")
            print(f"    the CUnit           : F1/F0={post['f1f0'][0]:.3f}  OSI={post['osi'][0]:.3f}  "
                  f"structure={structure(pw):.3f}")
            print(f"    weights by orientation: {byo}")
