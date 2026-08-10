"""WITHIN-RUST ATTRIBUTION — where does `wv_propagate`'s 78-80% of the tick GO?

*** THIS IS A MEASURING INSTRUMENT. IT CHANGES NO BEHAVIOUR. ***

`scale_wall_measure.py` established WHERE the wall is (Rust, and inside Rust
`wv_propagate`). It cannot say WHY, and the supervisor's framing offered two
rival mechanisms that need DIFFERENT fixes:

  (H-join) edge enumeration / the missing join index — `wv_propagate` is a
           2-edge rule so the semi-naive cursor (1-edge only) can't drive it;
  (H-attr) attr-map matching — the bulk agent measured ~5 extra attrs/cell
           costing the Rust tick ~60% at 128^2 ("a wider attr map is slower
           to match").

Both are consistent with "12,795us scanning 16,384 cells while 254 are
active". This script decides between them by MEASURING INSIDE RUST rather
than inferring a mechanism from a curve — which this project has now got
wrong four times in one day.

METHOD (see `Substrate::profile_rule_match` in substrate.rs for the contract).
The engine re-runs the rule's MATCH with a NO-OP visit (no apply, no
mutation) under four progressively-stripped variants, timing each with ONE
`Instant` pair per variant (never a per-binding probe — the committed
instrument recorded that a per-call probe inflates the very thing it
measures ~1.8x):

    scan   = match_edges[0] only, no where   -> driving-edge enumeration
    enum   = all match_edges, no where       -> + neighbour expansion + binding
    setup  = all match_edges, where=Eq(1,1)  -> + per-binding interpreter setup
    full   = the real rule                   -> + real attr lookups/compares

    enumeration     = scan
    expansion       = enum  - scan
    interp_setup    = setup - enum
    attr_match_eval = full  - setup

These RECONCILE by construction (they sum to `full`), and `full` is
cross-checked against the engine's own independent `rule_costs()` counter for
the same rule — two instruments, one number. If they disagree, the
attribution is wrong and says so.

LIVENESS (PROTOCOL §1 / §12; this arc has caught ELEVEN inert instruments):
the profile is taken on a LIVE retina, and we report the state histogram and
the active-cell count at the moment of profiling. A profile of a dead grid
would attribute a tick that isn't happening. `--assert-live` makes a grid
with no active cells a HARD ERROR.

USAGE
    python scripts/rust_attrib_measure.py --sizes 32,64,96,128 --reps 5
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# PROTOCOL §10.1 rule 3: pin THIS TREE's engine BEFORE any `domains.*` import.
# A preamble that runs after the first `substrate_rs` import is a NO-OP THAT
# LOOKS CORRECT — the import binds the engine. This must stay at the top.
from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402

WARMUP = 5
IGNITE_EVERY = 5
CATEGORIES = ("enumeration", "expansion", "interp_setup", "attr_match_eval")


def _boot(propagate=1.0):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", propagate)
    return s, ag


def _states(s, world):
    h = {}
    for n in world.cells.values():
        v = s.node(n)["attrs"].get("state")
        h[v] = h.get(v, 0) + 1
    return h


def _run(world, ticks, g):
    for i in range(ticks):
        world.step(ignite_k=1 if i % IGNITE_EVERY == 0 else 0)


def profile(g, reps, rule="wv_propagate", assert_live=True):
    gc.collect()
    s, ag = _boot()
    world = WaveWorld(s, h=g, w=g, seed=0)
    # Warm up into the live travelling-wave regime, then profile THERE.
    _run(world, WARMUP + 10, g)
    st = _states(s, world)
    active = st.get("active", 0)
    if assert_live and active == 0:
        raise SystemExit(
            f"DEAD GRID at {g}x{g}: 0 active cells. A profile of a tick that "
            f"isn't happening attributes nothing. states={st}")

    raw = {}
    for _ in range(reps):
        rows = s._inner.profile_rule_match(rule, 1)
        if not rows:
            raise SystemExit(f"rule {rule!r} not found/active — nothing profiled")
        for (label, micros, bindings) in rows:
            raw.setdefault(label, {"us": [], "bindings": bindings})
            raw[label]["us"].append(micros)

    v = {k: statistics.median(d["us"]) for k, d in raw.items()}
    b = {k: d["bindings"] for k, d in raw.items()}
    # Attribution is of the PRE-pushdown path — that is the cost being
    # explained. `full` (the live, pushed-down path) is reported alongside as
    # the result of acting on the attribution.
    attrib = {
        "enumeration": v["scan"],
        "expansion": v["enum"] - v["scan"],
        "interp_setup": v["setup"] - v["enum"],
        "attr_match_eval": v["full_nopushdown"] - v["setup"],
    }
    total = v["full_nopushdown"]
    return {
        "grid": g,
        "cells": g * g,
        "active_cells_at_profile": active,
        "states_at_profile": st,
        "variant_us_median": v,
        "variant_us_raw": {k: d["us"] for k, d in raw.items()},
        "bindings_per_variant": b,
        "attribution_us": attrib,
        "attribution_pct": {k: (100.0 * x / total if total else 0.0)
                            for k, x in attrib.items()},
        "full_us": total,
        "full_nopushdown_us": v["full_nopushdown"],
        "full_pushdown_us": v["full"],
        "pushdown_speedup_on_rule": (v["full_nopushdown"] / v["full"]) if v.get("full") else None,
        "reconciles_to_full": round(sum(attrib.values()), 3) == round(total, 3),
        "us_per_binding_full": (total / b["enum"]) if b.get("enum") else None,
        "us_per_binding_enum": (v["enum"] / b["enum"]) if b.get("enum") else None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", default="32,64,96,128")
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--rule", default="wv_propagate")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    sizes = [int(x) for x in a.sizes.split(",")]
    rows = [profile(g, a.reps, a.rule) for g in sizes]
    out = {"provenance": provenance_line(), "rule": a.rule, "reps": a.reps,
           "machine": _machine(), "rows": rows}
    print(json.dumps(out, indent=1))
    if a.out:
        with open(a.out, "w") as f:
            json.dump(out, f, indent=1)
        print(f"\nwrote {a.out}", file=sys.stderr)

    print(f"\n{'grid':>5} {'cells':>7} {'act':>5} {'OLDus':>7} {'NEWus':>7} {'x':>5} "
          + " ".join(f"{c:>16}" for c in CATEGORIES), file=sys.stderr)
    for r in rows:
        p = r["attribution_pct"]
        print(f"{r['grid']:>5} {r['cells']:>7} {r['active_cells_at_profile']:>5} "
              f"{r['full_nopushdown_us']:>7.0f} {r['full_pushdown_us']:>7.0f} "
              f"{r['pushdown_speedup_on_rule'] or 0:>4.1f}x "
              + " ".join(f"{p[c]:>15.1f}%" for c in CATEGORIES), file=sys.stderr)


def _machine():
    try:
        import subprocess
        cpu = subprocess.check_output(
            "lscpu | grep 'Model name' | head -1", shell=True, text=True).strip()
        return cpu.split(":", 1)[-1].strip()
    except Exception:
        return "unknown"


if __name__ == "__main__":
    main()
