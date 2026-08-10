#!/usr/bin/env python3
"""ARM D — IS THE TIE-BREAK LOAD-BEARING? (§1 clause 5, the FM-0 vacuity gate.)

The 222-test oracle asks whether a GATED number moves. That is a coarse
instrument: a test can pass while a value inside it changes. So this probe
asks the finer question directly, on the two sites the census found:

  `dv_burst_winner`  (vision_dorsal.json) -- `Eq(u, Argmax{u2: Attr(u2,dact)})`
  `oo_sunit_burst_winner` (vision_onoff.json) -- `Eq(u, Argmax{u2: Attr(u2,rate)})`

Both are WINNER-TAKE-ALL competition rules. Under `refuse_all` a TIED
competition elects NOBODY instead of an arbitrary somebody.

`D = max |value_off - value_refuse_all|` over every unit attribute, at every
step. `D == 0.0` EXACTLY would mean the tie-break is DECORATIVE at these sites.
A non-zero D is the magnitude AND direction of a number that moves.

Toggling is by the ENGINE MODE, not by a Python branch -- the arms differ only
in what the selector does with a tie.
"""
import json
import os
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from domains import engine_provenance  # noqa: E402
engine_provenance.engine_preamble()

import numpy as np  # noqa: E402
import substrate_rs as srs  # noqa: E402
native = srs._native  # noqa: E402

import domains.seed_registry  # noqa: E402,F401
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402
from domains.dorsal_world import add_dunits  # noqa: E402

EXPECT_ENGINE = os.environ.get("EXPECT_ENGINE", "")
PROV = engine_provenance.provenance_line()
if EXPECT_ENGINE and EXPECT_ENGINE not in PROV:
    raise SystemExit(f"ENGINE MISMATCH: expected {EXPECT_ENGINE!r} in {PROV!r}")

STEPS = 60
# LITERAL elements of the declared block 110000-110999 (never `base + K`).
#
# CORRECTION, RECORDED: the first version of this probe used seeds
# 110200-110207 with n_units=10 and 60 free-running wave steps and saw
# **ZERO TIES IN EVERY ARM**. `tie_break_is_load_bearing: false` from that run
# was a DEAD ARM, not a finding -- a gate that has never been ABLE to fire has
# not been tested. The census (`argmin_tie_sites`) named the configuration that
# actually ties: the DSI calibration scenario, seed 3, n_units=4, driven by
# `probe_dsi`. This probe now runs THAT, and reports the refusal count so a
# zero-D claim can never again be made on an arm that never refused.
SEEDS = [110200, 110201, 110202, 110203, 110204, 110205, 110206, 110207]


def run_dsi_full_state(mode):
    """The scenario the census proved TIES. Returns every numeric attribute of
    every DUnit and every retinal cell after the ideal-unit DSI probe, plus the
    refusal count -- so `D == 0` is only ever read next to `refusals > 0`."""
    from domains.dorsal_world import add_dunits, probe_dsi, set_dunit_ideal
    native.argmin_tie_reset()
    native.argmin_tie_enable(mode)
    try:
        s, ag = boot_core()
        load_seeds_into(s, ag, ["vision_dorsal"])
        dp = s.nodes("DorsalParams")[0]
        wp = s.nodes("WaveParams")[0]
        s.set_attr(dp, "dorsal", 1.0)
        s.set_attr(dp, "oja_eta", 5e-4)
        s.set_attr(wp, "propagate", 1.0)
        w = WaveWorld(s, h=16, w=16, seed=3, track_prev_burst=True)
        us = add_dunits(w, 4, rf=7, max_delay=3, rng=np.random.default_rng(3))
        probe_dsi(w, us, seed=3)
        for u in us:
            set_dunit_ideal(w, u, 0.0)
        probe_dsi(w, us, seed=3)
        snap = {}
        for j, u in enumerate(us):
            for k, v in s.node(u)["attrs"].items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    snap[f"u{j}.{k}"] = float(v)
        for c in w.cells.values():
            for k, v in s.node(c)["attrs"].items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    snap[f"c{c}.{k}"] = float(v)
        st = native.argmin_tie_stats()
        return snap, st
    finally:
        native.argmin_tie_enable("off")


def run(seed, mode):
    """Boot the dorsal stream, run STEPS waves, return every unit attribute."""
    native.argmin_tie_reset()
    native.argmin_tie_enable(mode)
    try:
        s, ag = boot_core()
        load_seeds_into(s, ag, ["vision_dorsal"])
        dp = s.nodes("DorsalParams")[0]
        wp = s.nodes("WaveParams")[0]
        s.set_attr(dp, "dorsal", 1.0)
        s.set_attr(dp, "oja_eta", 5e-4)
        s.set_attr(wp, "propagate", 1.0)
        w = WaveWorld(s, h=16, w=16, seed=seed, track_prev_burst=True)
        us = add_dunits(w, 10, rf=7, max_delay=3,
                        rng=np.random.default_rng(seed))
        trace = []
        for i in range(STEPS):
            w.step(ignite_k=1 if i % 5 == 0 else 0)
            snap = {}
            for j, u in enumerate(us):
                at = s.node(u)["attrs"]
                for k, v in at.items():
                    if isinstance(v, (int, float)) and not isinstance(v, bool):
                        snap[f"u{j}.{k}"] = float(v)
            for c in w.cells.values():
                at = s.node(c)["attrs"]
                for k, v in at.items():
                    if isinstance(v, (int, float)) and not isinstance(v, bool):
                        snap[f"c{c}.{k}"] = float(v)
            trace.append(snap)
        st = native.argmin_tie_stats()
        return trace, st
    finally:
        native.argmin_tie_enable("off")


def main():
    print(f"provenance: {PROV}")
    print(f"loadavg at start: {os.getloadavg()}")
    rows = []
    for sd in SEEDS:
        t_off, st_off = run(sd, "off")
        t_cnt, st_cnt = run(sd, "count")
        t_ref, st_ref = run(sd, "refuse_all")
        keys = set()
        for snap in t_off + t_ref:
            keys |= set(snap)
        worst = ("", 0.0)
        n_diff = 0
        for step in range(STEPS):
            a, b = t_off[step], t_ref[step]
            for k in keys:
                d = abs(a.get(k, 0.0) - b.get(k, 0.0))
                if d > 0:
                    n_diff += 1
                if d > worst[1]:
                    worst = (f"step{step}.{k}", d)
        # `count` mode must be BYTE-IDENTICAL to `off` -- the instrument's
        # own control. If this is non-zero the instrument is not passive.
        cnt_D = max(
            (abs(t_off[i].get(k, 0.0) - t_cnt[i].get(k, 0.0))
             for i in range(STEPS) for k in keys), default=0.0)
        rows.append({
            "seed": sd,
            "ties_seen_count_mode": st_cnt["ties"],
            "refusals_refuse_all": st_ref["refusals"],
            "D_max_off_vs_refuse_all": worst[1],
            "D_argmax_attr": worst[0],
            "n_attr_step_cells_that_differ": n_diff,
            "D_count_mode_vs_off_MUST_BE_ZERO": cnt_D,
        })
        print(json.dumps(rows[-1]))
    # THE ARM THAT ACTUALLY REFUSES -- the FM-0 vacuity gate, run on the
    # configuration the census named rather than one I guessed.
    a_off, s_o = run_dsi_full_state("off")
    a_cnt, s_c = run_dsi_full_state("count")
    a_ref, s_r = run_dsi_full_state("refuse_all")
    keys = set(a_off) | set(a_ref)
    D_ref = max((abs(a_off.get(k, 0.0) - a_ref.get(k, 0.0)) for k in keys),
                default=0.0)
    D_cnt = max((abs(a_off.get(k, 0.0) - a_cnt.get(k, 0.0)) for k in keys),
                default=0.0)
    worst = max(keys, key=lambda k: abs(a_off.get(k, 0.0) - a_ref.get(k, 0.0)),
                default="")
    live = {
        "scenario": "dorsal DSI calibration (seed 3, n_units 4) -- the "
                    "configuration the census proved TIES",
        "n_attributes_compared": len(keys),
        "ties_seen_count_mode": s_c["ties"],
        "refusals_exercised": s_r["refusals"],
        "D_max_off_vs_refuse_all": D_ref,
        "D_argmax_attribute": worst,
        "D_count_mode_vs_off_MUST_BE_ZERO": D_cnt,
        "arm_is_alive": s_r["refusals"] > 0,
    }
    print(json.dumps(live, indent=2))

    out = {
        "provenance": PROV,
        "live_arm": live,
        "steps": STEPS,
        "seeds": SEEDS,
        "loadavg_end": list(os.getloadavg()),
        "rows": rows,
        "instrument_is_passive": all(
            r["D_count_mode_vs_off_MUST_BE_ZERO"] == 0.0 for r in rows),
        "free_running_arm_is_DEAD": all(
            r["refusals_refuse_all"] == 0 for r in rows),
        "tie_break_is_load_bearing_ON_THE_LIVE_ARM": live[
            "D_max_off_vs_refuse_all"] > 0.0,
        "refusals_actually_happened": live["refusals_exercised"] + sum(
            r["refusals_refuse_all"] for r in rows),
    }
    (ROOT / "results" / "argmin_unique_loadbearing.json").write_text(
        json.dumps(out, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
