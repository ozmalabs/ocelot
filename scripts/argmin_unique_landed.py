#!/usr/bin/env python3
"""ARM M2 — THE LANDED NUMBERS THEMSELVES, at the exact three sites that TIE.

The 222-test oracle answers "did a GATE flip". This answers the finer and more
dangerous question: **did the NUMBER move while the gate still passed?**

The census attributed all 201 ties on the bench to exactly three tests, and to
exactly two selector sites -- both `Argmax`, both WINNER-TAKE-ALL:

  dv_burst_winner       `Eq(u, Argmax{u2: Attr(u2,"dact")})`   vision_dorsal
  oo_sunit_burst_winner `Eq(u, Argmax{u2: Attr(u2,"rate")})`   vision_onoff

So this reproduces those three tests' READOUTS -- the committed floats -- under
`off` and under `refuse_all`, and reports `off - refuse_all` for each.

**§5, declared in advance: if a number moves, that is the result. No rescue.**

There is NO Python branch on the mode: both arms run identical code and differ
only in what the engine's selector does with a tie.
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

EXPECT_ENGINE = os.environ.get("EXPECT_ENGINE", "")
PROV = engine_provenance.provenance_line()
if EXPECT_ENGINE and EXPECT_ENGINE not in PROV:
    raise SystemExit(f"ENGINE MISMATCH: expected {EXPECT_ENGINE!r} in {PROV!r}")


# --- readout 1: the dorsal DSI calibration gate (ideal 0.600 / floor 0.111) --
def dsi_readout():
    from domains.dorsal_world import add_dunits, probe_dsi, set_dunit_ideal
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_dorsal"])
    dp = s.nodes("DorsalParams")[0]
    wp = s.nodes("WaveParams")[0]
    s.set_attr(dp, "dorsal", 1.0)
    s.set_attr(dp, "oja_eta", 5e-4)
    s.set_attr(wp, "propagate", 1.0)
    w = WaveWorld(s, h=16, w=16, seed=3, track_prev_burst=True)
    us = add_dunits(w, 4, rf=7, max_delay=3, rng=np.random.default_rng(3))
    untrained = float(probe_dsi(w, us, seed=3).mean())
    for u in us:
        set_dunit_ideal(w, u, 0.0)
    ideal = float(probe_dsi(w, us, seed=3).mean())
    return {"dsi_untrained_floor": untrained, "dsi_ideal": ideal}


# --- readout 2: the on/off no-threshold OSI (committed ~0.0006) --------------
def osi_readout():
    sys.path.insert(0, str(ROOT / "tests"))
    from test_vision_onoff_migrated import (        # noqa: E402
        _world, install_signed_rf, gabor, set_params, freeze, cell_stats,
        RF, PERIOD,
    )
    w, us, _ = _world(n_units=2)
    install_signed_rf(w, us[0], gabor(RF, 0.0, 0.0, period=PERIOD))
    install_signed_rf(w, us[1], gabor(RF, 90.0, 0.0, period=PERIOD))
    set_params(w, homeo=0.0)
    freeze(w)
    st = cell_stats(w, us, key="rate", period=PERIOD)
    return {"onoff_no_threshold_osi_mean": float(st["osi"].mean())}


# --- readout 3: the composed-pathway blindness (ideal ~0.13 vs 1.0) ---------
def compose_readout():
    from scripts.rung8_lib import (
        adapt_theta, build, develop_retina, ideal_split_gabor, osi_of,
    )
    w, us, _a, _b = build(seed=0, n_units=6, channels="lateral")
    develop_retina(w, 3000)
    for u in us:
        ideal_split_gabor(w, u, theta=0.0, phase=0.0)
    adapt_theta(w, 400)
    o_lat, _ = osi_of(w, us)
    return {"compose_ideal_osi_lateral": float(np.mean(o_lat))}


READOUTS = {
    "dorsal_dsi": dsi_readout,
    "onoff_osi": osi_readout,
    "compose_osi": compose_readout,
}


def run(name, mode):
    native.argmin_tie_reset()
    native.argmin_tie_enable(mode)
    try:
        vals = READOUTS[name]()
    finally:
        native.argmin_tie_enable("off")
    return vals, native.argmin_tie_stats()


def main():
    print(f"provenance: {PROV}")
    print(f"loadavg at start: {os.getloadavg()}")
    rows = []
    for name in READOUTS:
        v_off, s_off = run(name, "off")
        v_cnt, s_cnt = run(name, "count")
        v_ref, s_ref = run(name, "refuse_all")
        for k in v_off:
            rows.append({
                "readout": name,
                "number": k,
                "off": v_off[k],
                "count": v_cnt[k],
                "refuse_all": v_ref[k],
                "delta_off_minus_refuse_all": v_off[k] - v_ref[k],
                "moved": v_off[k] != v_ref[k],
                "count_mode_identical_to_off": v_off[k] == v_cnt[k],
                "ties_seen": s_cnt["ties"],
                "refusals": s_ref["refusals"],
            })
            print(json.dumps(rows[-1]))
    out = {
        "provenance": PROV,
        "loadavg_end": list(os.getloadavg()),
        "rows": rows,
        "n_numbers_measured": len(rows),
        "n_moved": sum(1 for r in rows if r["moved"]),
        "instrument_passive": all(r["count_mode_identical_to_off"]
                                  for r in rows),
        "total_refusals_exercised": sum(r["refusals"] for r in rows),
    }
    (ROOT / "results" / "argmin_unique_landed.json").write_text(
        json.dumps(out, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
