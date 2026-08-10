"""SCALE WALL — measure where the retina's per-tick cost breaks, and WHY.

*** THIS IS A MEASURING INSTRUMENT. IT CHANGES NO BEHAVIOUR. ***

Boots the committed `vision_waves` world at a range of grid sizes, times the
tick, and attributes the cost. No seed is edited, no rule is added, no default
is changed, no Rust is touched. `wave_world.py` is imported and used exactly as
every committed rung uses it.

THE QUESTION (creator, 2026-07-17): 16x16 is a toy. Human-level is ~150k
high-acuity samplers in a moving aperture (~126M photoreceptors -> ~1M axons,
a ~100:1 compression AT THE SENSOR; retina->V1 ~50-70ms; asynchronous, no
frame). Where does this actually break, and is the wall ARITHMETIC (a GPU/SIMD
primitive would help), RULE RESCAN (an index problem no GPU touches), FIXPOINT
DEPTH (loop shape), or NODE MINTING?

--------------------------------------------------------------------------
WHAT I GOT WRONG BUILDING THIS INSTRUMENT — both errors are recorded here
because §1 says the instrument is the highest risk, and both would have
produced a confident wrong answer.

  1. `tick()`'s RETURN IS NOT A FIRING COUNT. I first used it as the
     positive control ("firings > 0"). It reads 1-4 per tick while HUNDREDS
     of cells change state. It counts PROGRESSING RULE VISITS: the store's
     `run_rules` fires EVERY binding of a rule in ONE visit
     (`try_incremental_match` snapshot semantics), so one visit == one step
     no matter how many cells it recruits. A control that reads "3" on a
     live retina and "3" on an idle one is nearly inert. The real witness
     is the STATE DISTRIBUTION and a moving checksum; `tick()`'s return is
     kept, correctly relabelled `rule_visits`, as the FIXPOINT-DEPTH datum.
  2. A PER-CALL PROBE BIASES ITS OWN ATTRIBUTION. Wrapping the hot calls
     (`node`/`set_attr`, ~100k/tick) and `tick` (20/tick) inflates exactly
     the Python side it is trying to measure — it reported ~1.8x total
     overhead concentrated on the calls it wrapped. Attribution here is
     therefore read from (a) the ENGINE'S OWN native `rule_costs()`
     counters for the Rust side and (b) a TICK-ONLY wrapper (20 calls/run,
     ~14us perturbation) for the split, never from a per-call probe.

HOW THE INSTRUMENT IS CONTROLLED (PROTOCOL §1; this arc has caught TEN inert
instruments, incl. a "flawless all-zero dissociation" off a dead one):

  * LIVENESS IS PROVEN PER N, NOT ASSUMED. Per point we report the state
    histogram (active/recruited/refractory/rested), a checksum that MUST
    move across ticks, and the engine's own per-rule `progress` counters.
    `--assert-live` makes a frozen checksum or a zero-progress wave rule a
    HARD ERROR. A tick that does nothing is infinitely fast and scales
    beautifully; that is the exact failure this arc keeps catching.
  * THE RUST SIDE IS READ FROM THE ENGINE'S OWN COUNTERS. `rule_costs()`
    returns (name, micros, visits, progress) per rule — native, unbiased,
    and immune to the trajectory-change confound that makes
    neutering-and-timing lie.
  * TWO IGNITION REGIMES, BOTH REPORTED. `constant` (ignite_k=1, the
    committed schedule) holds WORK fixed while N grows -- it isolates the
    price of a cell merely EXISTING. `density` (ignite_k ~ area) holds wave
    DENSITY fixed so work scales with N -- the biologically honest sweep.
    Reporting only one would answer a different question than was asked.

USAGE
    python scripts/scale_wall_measure.py --mode sweep
    python scripts/scale_wall_measure.py --mode all --out results/scale_wall.json

NO SEEDS ARE CLAIMED (16000-16999 was offered; this is a measurement, not a
confirmatory experiment, so none was needed). The RNG seed is fixed at 0
throughout purely so the sweep is reproducible.
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# PROTOCOL §10.1 rule 3: a non-pytest entrypoint pins its OWN tree's engine.
# MUST precede any `substrate_rs` import (and any module that does one).
from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import numpy as np  # noqa: E402

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402

SIZES = [16, 24, 32, 48, 64, 96, 128]
WARMUP = 5
REPEATS = 3
TICKS = 20
IGNITE_EVERY = 5
WAVE_RULES = ("wv_propagate", "wv_refract", "wv_recover")


class TickOnly:
    """Wraps ONLY `tick()`. 20 calls per timed run => ~14us perturbation, far
    below the signal. Deliberately NOT a per-call probe: wrapping the ~100k
    hot node()/set_attr() calls inflates the very Python cost under study."""

    def __init__(self, s):
        object.__setattr__(self, "_s", s)
        object.__setattr__(self, "t", 0.0)
        object.__setattr__(self, "visits", [])

    def __getattr__(self, name):
        real = getattr(object.__getattribute__(self, "_s"), name)
        if name != "tick":
            return real

        def wrapped(*a, **k):
            t0 = time.perf_counter()
            out = real(*a, **k)
            object.__setattr__(self, "t",
                               object.__getattribute__(self, "t") + time.perf_counter() - t0)
            # NOT a firing count -- progressing RULE VISITS (see module docstring).
            object.__getattribute__(self, "visits").append(out)
            return out
        return wrapped


def _boot(g, propagate=1.0):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", propagate)
    return s, ag


def _states(s, world):
    """State histogram — the honest liveness witness (`tick()`'s return is not)."""
    h = {}
    for n in world.cells.values():
        v = s.node(n)["attrs"].get("state")
        h[v] = h.get(v, 0) + 1
    return h


def _checksum(s, world):
    act = 0
    lb = 0.0
    for n in world.cells.values():
        at = s.node(n)["attrs"]
        if at.get("state") == "active":
            act += 1
        lb += float(at.get("last_burst", -999.0))
    return (act, round(lb, 3))


def _ignite_k(g, regime):
    """`constant` = the committed schedule (work fixed as N grows).
    `density` = ignitions ~ area, so wave density matches 16x16's."""
    return 1 if regime == "constant" else max(1, round(g * g / 256))


def _run(world, ticks, g, regime):
    k = _ignite_k(g, regime)
    for i in range(ticks):
        world.step(ignite_k=k if i % IGNITE_EVERY == 0 else 0)


def sweep(sizes, repeats=REPEATS, ticks=TICKS, regime="constant", assert_live=True):
    rows = []
    for g in sizes:
        wall, rust = [], []
        first = {}
        for rep in range(repeats):
            gc.collect()
            s, ag = _boot(g)
            nodes0 = s._inner.node_count()
            p = TickOnly(s)
            world = WaveWorld(p, h=g, w=g, seed=0)
            nodes1 = s._inner.node_count()
            _run(world, WARMUP, g, regime)
            chk0 = _checksum(s, world)
            object.__setattr__(p, "t", 0.0)
            object.__getattribute__(p, "visits").clear()
            s._inner.reset_rule_costs()
            t0 = time.perf_counter()
            _run(world, ticks, g, regime)
            t1 = time.perf_counter()
            chk1 = _checksum(s, world)
            tot = t1 - t0
            rt = object.__getattribute__(p, "t")
            wall.append(tot / ticks * 1000.0)
            rust.append(rt / ticks * 1000.0)
            if rep == 0:
                rc = [r for r in s._inner.rule_costs() if r[1] > 0 or r[2] > 0]
                rc.sort(key=lambda r: -r[1])
                first = {
                    "rule_costs_top": [
                        {"rule": n, "us_per_tick": us / ticks,
                         "visits_per_tick": c / ticks, "progress_per_tick": pr / ticks}
                        for (n, us, c, pr) in rc[:6]],
                    "rust_rules_us_per_tick": sum(r[1] for r in rc) / ticks,
                    "states": _states(s, world),
                    "checksum_before": chk0, "checksum_after": chk1,
                    "rule_visits_per_tick": float(np.mean(
                        object.__getattribute__(p, "visits"))),
                    "cells_nodes_minted": nodes1 - nodes0,
                }
                # ---- §1: LIVENESS IS A HARD GATE, NOT A HOPE ----
                if assert_live:
                    if chk0 == chk1:
                        raise SystemExit(
                            f"FROZEN WORLD at g={g}: checksum {chk0} did not move. "
                            "The timing would be measuring an empty loop.")
                    prog = {n: pr for (n, us, c, pr) in rc}
                    dead = [r for r in WAVE_RULES if prog.get(r, 0) == 0]
                    if dead:
                        raise SystemExit(
                            f"DEAD RULES at g={g}: {dead} made ZERO progress. "
                            "A silent arm is a failed gate, not a fast one.")
            del world, s, ag, p

        row = {
            "grid": g, "cells": g * g, "regime": regime,
            "ignite_k": _ignite_k(g, regime),
            "ms_per_tick_mean": float(np.mean(wall)),
            "ms_per_tick_sd": float(np.std(wall, ddof=1)) if len(wall) > 1 else 0.0,
            "ms_per_tick_raw": [round(x, 4) for x in wall],
            "rust_ms_mean": float(np.mean(rust)),
            "rust_ms_raw": [round(x, 4) for x in rust],
            "python_ms_mean": float(np.mean(wall)) - float(np.mean(rust)),
            "rust_pct": 100.0 * float(np.mean(rust)) / float(np.mean(wall)),
            "us_per_cell": float(np.mean(wall)) * 1000.0 / (g * g),
            "nodes_per_cell": first["cells_nodes_minted"] / (g * g),
            **first,
        }
        rows.append(row)
        print(f"g={g:4d} cells={g*g:7d} k={row['ignite_k']:4d} "
              f"wall={row['ms_per_tick_mean']:9.3f}ms sd={row['ms_per_tick_sd']:6.3f} "
              f"rust={row['rust_ms_mean']:8.3f}({row['rust_pct']:4.1f}%) "
              f"us/cell={row['us_per_cell']:6.3f} visits={row['rule_visits_per_tick']:4.1f}",
              flush=True)
    return rows


def fit(rows, key="ms_per_tick_mean"):
    """log-log slope vs cells, reported WITH r2 so a bad fit cannot pass as a
    clean exponent."""
    x = np.log(np.array([r["cells"] for r in rows], float))
    y = np.log(np.array([r[key] for r in rows], float))
    A = np.vstack([x, np.ones_like(x)]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = A @ coef
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    return {"exponent": float(coef[0]), "intercept": float(coef[1]),
            "r2": (1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan"),
            "n_points": len(rows)}


def latency_ceiling(rows, budget_ms):
    """Largest measured N under budget, and the N the fit predicts hits it."""
    under = [r for r in rows if r["ms_per_tick_mean"] <= budget_ms]
    f = fit(rows)
    # ms = e^b * cells^a  =>  cells = (budget / e^b)^(1/a)
    cells = (budget_ms / np.exp(f["intercept"])) ** (1.0 / f["exponent"])
    return {"budget_ms": budget_ms,
            "largest_measured_grid_under": (max(r["grid"] for r in under) if under else None),
            "largest_measured_cells_under": (max(r["cells"] for r in under) if under else None),
            "predicted_cells_at_budget": float(cells),
            "predicted_grid_at_budget": float(np.sqrt(cells))}


def sparsity(grid=32, ticks=60, drift=False, regime="constant"):
    """Fraction of cells whose (state, driven) CHANGES per tick.

    THE number that decides the architecture: a few percent => event-driven
    wins and a GPU is the wrong tool; most cells => dense wins.
    """
    s, ag = _boot(grid)
    world = WaveWorld(s, h=grid, w=grid, seed=0)
    img = None
    if drift:
        rng = np.random.default_rng(7)
        # A SMOOTH natural-ish image drifted 1px/tick — a moving aperture.
        # A fresh random field per tick would be maximally non-sparse BY
        # CONSTRUCTION and would answer a question nobody asked.
        base = rng.random((grid * 3, grid * 3)).astype(np.float32)
        for _ in range(6):
            base = (base + np.roll(base, 1, 0) + np.roll(base, -1, 0)
                    + np.roll(base, 1, 1) + np.roll(base, -1, 1)) / 5.0
        img = base
    k = _ignite_k(grid, regime)
    prev, fracs, bursts = None, [], []
    for i in range(ticks):
        frame = img[i:i + grid, i:i + grid] if drift else None
        world.step(ignite_k=k if i % IGNITE_EVERY == 0 else 0, frame=frame)
        cur = {}
        for rc, n in world.cells.items():
            at = s.node(n)["attrs"]
            cur[rc] = (at.get("state"), at.get("driven"))
        bursts.append(sum(1 for n in world.cells.values()
                          if float(s.node(n)["attrs"].get("bursting", 0.0)) == 1.0)
                      / (grid * grid))
        if prev is not None:
            fracs.append(sum(1 for kk in cur if cur[kk] != prev[kk]) / (grid * grid))
        prev = cur
    return {"grid": grid, "drift": drift, "regime": regime, "ticks": ticks,
            "changed_frac_mean": float(np.mean(fracs)),
            "changed_frac_sd": float(np.std(fracs, ddof=1)),
            "changed_frac_max": float(np.max(fracs)),
            "bursting_frac_mean": float(np.mean(bursts)),
            "bursting_frac_max": float(np.max(bursts))}


def rules_vs_nodes(grid=32, ticks=20, repeats=5):
    """Hold nodes fixed, vary RULE count -- by loading ADDITIONAL committed
    seeds. No rule is invented or edited.

    REPEATS ARE LOAD-BEARING, AND I LEARNED THAT HERE. A single-run version of
    this table read 4.50 -> 6.17 -> 6.19 ms/tick and looked like a real
    +37% rule-count effect. At 5 repeats it is 4.126 +/- 0.406 -> 4.187 +/-
    0.719 -> 4.365 +/- 0.834: every arm inside every other arm's SD. The
    "effect" was NOISE from one run. A single timing is not a datum.

    The node confound is measured, not assumed: the extra seeds add <= 4 nodes
    (728 -> 732), so this is ~pure rule count.

    NOTE the count comes from `_inner.rule_count()` (the RewriteRule STORE).
    `s.nodes("Rule")` returns 0 here -- the seed installs rules into the store,
    NOT as graph Rule nodes. Counting Rule nodes would have reported 0 and made
    this table meaningless.
    """
    out = []
    for extra, label in (([], "vision_waves only"),
                         (["vision_onoff"], "+vision_onoff"),
                         (["vision_onoff", "vision_lateral"], "+onoff+lateral")):
        ms, rust_us = [], []
        n_rules = n_nodes = nz = 0
        for _ in range(repeats):
            gc.collect()
            s, ag = boot_core()
            try:
                load_seeds_into(s, ag, ["vision_waves"] + extra)
            except Exception as e:
                out.append({"label": label, "error": str(e)})
                print(f"  {label:22s} SKIPPED: {e}", flush=True)
                break
            n_rules = s._inner.rule_count()
            n_nodes = s._inner.node_count()
            wp = s.nodes("WaveParams")[0]
            s.set_attr(wp, "propagate", 1.0)
            world = WaveWorld(s, h=grid, w=grid, seed=0)
            _run(world, WARMUP, grid, "constant")
            s._inner.reset_rule_costs()
            t0 = time.perf_counter()
            _run(world, ticks, grid, "constant")
            t1 = time.perf_counter()
            rc = [r for r in s._inner.rule_costs() if r[1] > 0]
            ms.append((t1 - t0) / ticks * 1000.0)
            rust_us.append(sum(r[1] for r in rc) / ticks)
            nz = len(rc)
            del s, ag, world
        if not ms:
            continue
        out.append({"label": label, "n_rules_store": n_rules,
                    "n_nodes_at_boot": n_nodes, "grid": grid,
                    "repeats": repeats,
                    "ms_per_tick_mean": float(np.mean(ms)),
                    "ms_per_tick_sd": float(np.std(ms, ddof=1)),
                    "ms_per_tick_raw": [round(x, 4) for x in ms],
                    "rust_rules_us_per_tick": float(np.mean(rust_us)),
                    "n_rules_with_nonzero_cost": nz})
        print(f"  rules={n_rules:4d} nodes={n_nodes:5d} ({label:20s}) "
              f"{np.mean(ms):8.3f} +/- {np.std(ms, ddof=1):5.3f} ms/tick "
              f"rust={np.mean(rust_us):7.1f}us nonzero={nz}", flush=True)
    return out


def ffi_decompose(grid=128):
    """Decompose the Python side: what does ONE pass over all cells cost?

    `wave_world.step()` makes ~2N `node()` reads + ~2N `set_attr()` writes per
    tick. This times each in isolation and compares the sum against a real
    tick, so the Python share is ATTRIBUTED rather than inferred. Independently
    corroborated by py-spy sampling (node 32.4% / set_attr 22.0% / tick 19.7%
    at 128^2) -- two methods, one answer.
    """
    s, ag = _boot(grid)
    world = WaveWorld(s, h=grid, w=grid, seed=0)
    _run(world, WARMUP, grid, "constant")
    cells = list(world.cells.values())
    n = len(cells)
    R = 5

    def bench(fn):
        t0 = time.perf_counter()
        for _ in range(R):
            fn()
        return (time.perf_counter() - t0) / R

    b_node = bench(lambda: [s.node(x) for x in cells])
    b_get = bench(lambda: [s.node(x)["attrs"].get("state") for x in cells])
    b_set = bench(lambda: [s.set_attr(x, "driven", 0.0) for x in cells])
    b_loop = bench(lambda: [x for x in cells])
    t0 = time.perf_counter()
    for _ in range(10):
        world.step(ignite_k=0)
    real = (time.perf_counter() - t0) / 10
    est = 2 * b_get + 2 * b_set
    out = {"grid": grid, "cells": n,
           "node_us_per_cell": b_node / n * 1e6,
           "node_get_state_us_per_cell": b_get / n * 1e6,
           "set_attr_us_per_cell": b_set / n * 1e6,
           "bare_python_loop_us_per_cell": b_loop / n * 1e6,
           "estimate_2node_2setattr_ms": est * 1000,
           "measured_step_ms": real * 1000,
           "ffi_share_of_tick_pct": 100 * est / real}
    for k, v in out.items():
        if isinstance(v, float):
            print(f"  {k:34s} {v:10.3f}", flush=True)
    return out


def memory(sizes=(16, 32, 64, 96, 128, 192)):
    """Bytes per RetinaCell vs N, from /proc VmRSS.

    NOT `ru_maxrss`: that is a HIGH-WATER MARK that never decreases, so it
    charges each grid for every allocation the process ever made. My first cut
    used it and reported 10112 / 228 / 128 / 0 B/cell -- obvious nonsense, and
    it would have been reported as a cache finding.

    ONE GRID PER PROCESS IS LOAD-BEARING, AND THAT IS ALSO MEASURED. Running
    every grid in ONE process (even with VmRSS) reads 10048 / 456 / 708 / 519 /
    542 / 732 B/cell -- non-monotone nonsense, because a freed grid's pages are
    reused by the next and the delta stops meaning "what this grid cost".
    Forked one per process it converges cleanly (10304 / 3280 / 1586 / 1187 /
    1092 / 983), the small-N values being fixed allocator overhead amortising
    away.
    """
    out = []
    for g in sizes:
        # Fork: a fresh process per grid, so VmRSS's baseline is uncontaminated
        # by any previous grid's freed-and-reused pages.
        r = subprocess.run(
            [sys.executable, os.path.abspath(__file__), "--mode", "_memory_one",
             "--sizes", str(g)],
            capture_output=True, text=True, cwd=ROOT)
        try:
            row = json.loads(r.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            print(f"  g={g:4d} FAILED: {r.stderr.strip().splitlines()[-1:]}", flush=True)
            continue
        out.append(row)
        print(f"  g={g:4d} cells={row['cells']:7d} B/cell={row['bytes_per_cell']:8.1f} "
              f"nodes={row['nodes_minted']:7d} edges={row['edges_total']:7d}", flush=True)
    return out


def _memory_one(g):
    """One grid, one process — the child of `memory()`. Prints one JSON line."""
    def rss():
        with open("/proc/self/status") as f:
            for ln in f:
                if ln.startswith("VmRSS"):
                    return int(ln.split()[1]) * 1024
        return 0
    s, ag = _boot(g)
    base, n0 = rss(), s._inner.node_count()
    world = WaveWorld(s, h=g, w=g, seed=0)
    after, n1 = rss(), s._inner.node_count()
    print(json.dumps({
        "grid": g, "cells": g * g, "rss_delta_bytes": after - base,
        "bytes_per_cell": (after - base) / (g * g),
        "nodes_minted": n1 - n0, "edges_total": s._inner.edge_count()}))
    return None


def fovea_node_count(grid=32):
    """Does `fovea_radius` reduce NODE COUNT, or only mask the drive channel?

    `wave_world.__init__` mints h*w RetinaCells unconditionally; `fovea_radius`
    is read ONLY inside `drive()`. A one-line check with a real answer either way.
    """
    out = []
    for rad in (0, 4, 8):
        s, ag = _boot(grid)
        world = WaveWorld(s, h=grid, w=grid, seed=0, fovea_radius=rad)
        cells = len(s.nodes("RetinaCell"))
        _run(world, 3, grid, "constant")
        rng = np.random.default_rng(1)
        t0 = time.perf_counter()
        for _ in range(10):
            world.step(ignite_k=0, frame=rng.random((grid, grid)).astype(np.float32))
        t1 = time.perf_counter()
        out.append({"fovea_radius": rad, "retina_cells": cells,
                    "ms_per_driven_tick": (t1 - t0) / 10 * 1000.0})
        print(f"  fovea_radius={rad:2d} -> RetinaCell nodes={cells:6d}  "
              f"{(t1-t0)/10*1000:8.3f} ms/tick", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="sweep",
                    choices=["sweep", "sparsity", "rules", "fovea", "ffi",
                             "memory", "_memory_one", "all"])
    ap.add_argument("--sizes", default=None)
    ap.add_argument("--regime", default="both", choices=["constant", "density", "both"])
    ap.add_argument("--repeats", type=int, default=REPEATS)
    ap.add_argument("--ticks", type=int, default=TICKS)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    sizes = [int(x) for x in a.sizes.split(",")] if a.sizes else SIZES
    if a.mode == "_memory_one":          # child of memory(): one JSON line, no chatter
        _memory_one(sizes[0])
        return
    prov = provenance_line()
    print(prov, flush=True)
    res = {"provenance": prov, "sizes": sizes, "repeats": a.repeats,
           "ticks": a.ticks, "machine": _machine()}
    print(res["machine"], flush=True)

    regimes = ["constant", "density"] if a.regime == "both" else [a.regime]
    if a.mode in ("sweep", "all"):
        for rg in regimes:
            print(f"== SWEEP regime={rg} ==", flush=True)
            rows = sweep(sizes, repeats=a.repeats, ticks=a.ticks, regime=rg)
            res[f"sweep_{rg}"] = rows
            res[f"fit_{rg}"] = fit(rows)
            res[f"fit_{rg}_rust"] = fit(rows, "rust_ms_mean")
            res[f"fit_{rg}_python"] = fit(rows, "python_ms_mean")
            print(f"   fit total : exp={res[f'fit_{rg}']['exponent']:.3f} "
                  f"r2={res[f'fit_{rg}']['r2']:.4f}")
            print(f"   fit rust  : exp={res[f'fit_{rg}_rust']['exponent']:.3f}")
            print(f"   fit python: exp={res[f'fit_{rg}_python']['exponent']:.3f}")
            if len(rows) >= 4:
                h = len(rows) // 2
                res[f"fit_{rg}_small"] = fit(rows[:h])
                res[f"fit_{rg}_large"] = fit(rows[h:])
                print(f"   fit small half: exp={res[f'fit_{rg}_small']['exponent']:.3f} "
                      f"| large half: exp={res[f'fit_{rg}_large']['exponent']:.3f}")
            for b in (50.0, 16.0):
                c = latency_ceiling(rows, b)
                res.setdefault(f"latency_{rg}", []).append(c)
                print(f"   <= {b:4.0f}ms: largest measured grid={c['largest_measured_grid_under']} "
                      f"| fit predicts {c['predicted_cells_at_budget']:.0f} cells "
                      f"(~{c['predicted_grid_at_budget']:.0f}^2)")
    if a.mode in ("sparsity", "all"):
        print("== SPARSITY ==", flush=True)
        for drift in (False, True):
            for rg in regimes:
                r = sparsity(drift=drift, regime=rg)
                res.setdefault("sparsity", []).append(r)
                print(f"   drift={drift!s:5s} regime={rg:8s} changed/tick="
                      f"{r['changed_frac_mean']*100:5.2f}% (max {r['changed_frac_max']*100:5.2f}%) "
                      f"bursting={r['bursting_frac_mean']*100:5.2f}%", flush=True)
    if a.mode in ("rules", "all"):
        print("== RULES vs NODES ==", flush=True)
        res["rules_vs_nodes"] = rules_vs_nodes()
    if a.mode in ("fovea", "all"):
        print("== FOVEA NODE COUNT ==", flush=True)
        res["fovea"] = fovea_node_count()
    if a.mode in ("ffi", "all"):
        print("== FFI DECOMPOSITION (the Python side) ==", flush=True)
        res["ffi"] = ffi_decompose()
    if a.mode in ("memory", "all"):
        print("== MEMORY (VmRSS, not ru_maxrss) ==", flush=True)
        res["memory"] = memory()

    if a.out:
        d = os.path.dirname(a.out)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(a.out, "w") as f:
            json.dump(res, f, indent=2)
        print("wrote", a.out)


def _machine():
    cpu = "unknown"
    try:
        with open("/proc/cpuinfo") as f:
            for ln in f:
                if ln.startswith("model name"):
                    cpu = ln.split(":", 1)[1].strip()
                    break
    except OSError:
        pass
    mem = ""
    try:
        with open("/proc/meminfo") as f:
            mem = f.readline().split(":", 1)[1].strip()
    except OSError:
        pass
    return f"{cpu} | {os.cpu_count()} logical cores | MemTotal {mem}"


if __name__ == "__main__":
    main()
