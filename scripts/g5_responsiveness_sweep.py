#!/usr/bin/env python3
"""G5 RESPONSIVENESS — the gate, and the RETROACTIVE sweep of every counter.

*** THIS IS A MEASURING INSTRUMENT. IT CHANGES NO BEHAVIOUR. ***

Pre-registration: `VISION_TERM_EVAL_COUNTER_PREREG.md`, committed at `7c382089`
BEFORE this file existed and before any measurement.

WHY. `VISION_VIDEO_PROBE_RERUN_RESULTS.md` §3.1: arm A8's pre-registered
counted-operation statistic was BYTE-IDENTICAL across an 11.8x range of N while
wall-clock grew 13x, and ALL FOUR of its pre-declared gates PASSED. Read
literally the pre-registered rule returned "the sd/identity layer is not the
binding term; the wall fell" -- a fluent, gated, entirely wrong answer.

The arc's eleven previously-caught inert instruments were all DEAD. That one was
ALIVE, DETERMINISTIC, CONSERVED -- AND INSENSITIVE, which no existing gate
catches, because every existing gate asks "is it non-zero?" and none asks "does
it MOVE WITH the thing being varied?"

WHAT THIS SCRIPT DOES

  1. Sweeps four axes, reading EVERY scale_audit counter at every point.
  2. Runs a CONTROL at each axis's first value, repeated the same number of
     times -- the measured noise floor G5's criterion is written against.
  3. Applies G5 per (counter, claimed axis), using the claim table fixed in the
     prereg BEFORE measurement, so no counter is judged on an axis it never
     claimed and none may pick its axis afterwards.
  4. Reports the A8 blindness systematically: every counter on SWEEP-S.

WHAT IT DOES NOT DO. It does NOT measure the sd/identity layer's scaling. That
is the next rung and is blocked on this one. Every sd workload here is
SYNTHETIC, generated from seed 67000, so the boundary is structural rather than
promised: a synthetic sweep cannot be quoted as the sd/identity measurement.

THE VERDICT IS NOT REIMPLEMENTED HERE. `AUDIT.scale_audit_g5_verdict` hands off
to `runners/dsl/src/g5.rs` -- the same function its unit tests exercise. A second
copy in Python is a copy that drifts, and a gate that has drifted from the gate
it was tested as is not a gate.

USAGE
    python scripts/g5_responsiveness_sweep.py --out results/g5_responsiveness.json
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import platform
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# PROTOCOL §10.1 rule 3 -- a non-pytest entrypoint pins its OWN tree's engine.
from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

# THE INSTRUMENT, IMPORTED WHOLE -- not reimplemented. The C/R counters are
# judged on the very workload the rungs that built them used, which is the
# fairest possible retroactive test (locality_index_measure.py's precedent).
from scripts.scale_split_measure import (  # noqa: E402
    AUDIT, _boot_eye, _frames, _run, counters,
)
from domains.wave_world import WaveWorld  # noqa: E402
from domains.lateral_world import add_lateral_retina, set_lat_params  # noqa: E402

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402

# --------------------------------------------------------------------------- #
# SEEDS -- block 67000-67999 (prereg §7). Deterministic workloads; seeds only
# generate synthetic sweep inputs.
SEED_SWEEP_S = 67000
SEED_SWEEP_G = 67001

M_POINTS = 7          # prereg §4.2: 7 sweep points, 7 control repeats
WARMUP_TICKS = 5
DT = ["pred", "coord:r", "coord:c", "val"]


# --------------------------------------------------------------------------- #
# THE CLAIM TABLE -- fixed in the prereg §4.1 BEFORE any measurement, read off
# each counter's OWN doc comment in `scale_audit.rs`.
#
# G5 is only meaningful against the axis a counter CLAIMS to track. A counter
# tested on an axis it never claimed would fail unfairly; a counter allowed to
# pick its axis afterwards would pass unfairly. Hence: declared, then measured.
CLAIMED_AXIS = {
    "ffi_calls": "B", "ffi_items": "B", "ffi_pyobjects": "B",
    "graph_writes": "B",
    "cand_enum": "G", "cand_enum_scan": "G", "cand_enum_local": "G",
    "cand_enum_hinted": "G", "cand_enum_first": "G", "cand_enum_repeat": "G",
    "cand_tested": "G", "cand_reject_bound": "G",
    "where_evals": "G", "where_evals_first": "G", "where_evals_repeat": "G",
    "where_rejects": "G",
    "pushdown_evals": "G", "pushdown_prunes": "G",
    "leaf_visits": "G", "var_collisions": "G", "bindings_cloned": "G",
    "apply_probe_rollbacks": "G",
    "rule_enumerations": "G", "rule_enumerations_repeat": "G",
    "epochs": "E", "epochs_apply_once": "E", "cand_enum_apply_once": "E",
    # New this rung. `term_units_unattributed` claims nothing -- it is a
    # diagnostic that SHOULD stay zero, so it is deliberately unassigned.
}

# The prereg's declared positive controls for G5 itself (§3.4). A gate that has
# never been shown to fail has not been tested.
G5_SELF_CONTROLS = {
    "RED_must_go_BLIND": ("epochs", "G"),
    "GREEN_must_go_RESPONSIVE": ("cand_enum", "G"),
}


# --------------------------------------------------------------------------- #
def load_state() -> dict:
    with open("/proc/loadavg") as fh:
        p = fh.read().split()
    return {"load1": float(p[0]), "load5": float(p[1]), "load15": float(p[2])}


def machine() -> dict:
    return {"platform": platform.platform(), "python": sys.version.split()[0],
            "cpu_count": os.cpu_count()}


def _counted(fn):
    """Run `fn` with the audit ON and return (counters, wall_ms).

    Reset-then-enable, exactly as every prior rung's point function does, so the
    counters describe THIS workload and not the boot that preceded it."""
    gc.collect()
    AUDIT.scale_audit_reset()
    AUDIT.scale_audit_set_enabled(True)
    t0 = time.perf_counter()
    try:
        fn()
    finally:
        AUDIT.scale_audit_set_enabled(False)
    ms = (time.perf_counter() - t0) * 1000.0
    return counters(), ms


# --------------------------------------------------------------------------- #
# SWEEP-G -- GRAPH SIZE. The axis the C/R counters claim.
#
# The workload is the committed retina drive, imported whole from
# `scale_split_measure`: the very workload the scale-split, batch-apply and
# locality-index rungs measured. Judging those counters on any other workload
# would make a retroactive verdict about a workload, not about a counter.
def point_G(g, ticks=10):
    s, ag, _ = _boot_eye(g)
    world = WaveWorld(s, h=g, w=g, seed=0, fovea_radius=0)
    add_lateral_retina(world)
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    for cp in s.nodes("ChangeParams"):
        s.set_attr(cp, "change", 1.0)
        s.set_attr(cp, "sustain", 1.0)
    set_lat_params(world, lateral=1.0)
    frames = _frames(g)
    _run(world, WARMUP_TICKS, g, "constant", frames)

    c, ms = _counted(lambda: _run(world, ticks, g, "constant", frames))
    del world, s, ag
    return c, ms, float(g * g)


# --------------------------------------------------------------------------- #
# SWEEP-B -- BOUNDARY CALLS. The axis the F counters claim.
#
# Deliberately the THINNEST possible workload: `add_node` calls and nothing
# else. The F counters charge only what exists BECAUSE the call came from
# Python, so the fair test of them is a sweep of exactly that and nothing else.
def point_B(n_calls):
    s, ag, _ = _boot_eye(4)

    def work():
        for i in range(n_calls):
            nid = s.add_node("G5Probe", {"i": float(i)})
            s.set_attr(nid, "i", float(i) + 1.0)

    c, ms = _counted(work)
    del s, ag
    return c, ms, float(n_calls)


# --------------------------------------------------------------------------- #
# SWEEP-E -- EPOCHS. The axis the epoch counters claim: Python->Rust entries
# into a rule-running method. Grid FIXED, tick count varied, so the graph the
# rules match over is constant and only the number of entries moves.
def point_E(ticks, g=12):
    s, ag, _ = _boot_eye(g)
    world = WaveWorld(s, h=g, w=g, seed=0, fovea_radius=0)
    add_lateral_retina(world)
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    for cp in s.nodes("ChangeParams"):
        s.set_attr(cp, "change", 1.0)
        s.set_attr(cp, "sustain", 1.0)
    set_lat_params(world, lateral=1.0)
    frames = _frames(g)
    _run(world, WARMUP_TICKS, g, "constant", frames)

    c, ms = _counted(lambda: _run(world, ticks, g, "constant", frames))
    del world, s, ag
    return c, ms, float(ticks)


# --------------------------------------------------------------------------- #
# SWEEP-S -- THE A8 SHAPE. A signature is an ATTRIBUTE, not a subgraph: N cells
# live inside ONE node's attribute list, so the matched graph is CONSTANT in N.
# This is the workload on which every graph-level counter went byte-identical
# across 11.8x while wall-clock grew 13x.
#
# SYNTHETIC (seed 67000), never real frames -- so this sweep cannot be mistaken
# for, or quoted as, the sd/identity measurement it is explicitly not.
def synth_cells(n, seed=SEED_SWEEP_S):
    """A deterministic pseudo-random cell set of exactly `n` relations.

    A plain LCG, not numpy: the requirement is reproducibility to the integer,
    and an LCG written here is auditable in three lines. Values are drawn from a
    small alphabet so the held signature is a realistic mixture rather than all
    distinct (all-distinct would let every comparison fail on its first slot)."""
    x = seed
    out, seen = [], set()
    while len(out) < n:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        r, c = (x >> 7) % 64, (x >> 17) % 64
        if (r, c) in seen:
            continue
        seen.add((r, c))
        out.append(["cell", r, c, f"v{(x >> 3) % 4}"])
    return out


def point_S(n_cells, k_codebook=1):
    cells = synth_cells(n_cells)
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    for i in range(k_codebook):
        sig = cells if i == 0 else synth_cells(n_cells, seed=SEED_SWEEP_S + 1 + i)
        s.add_node("ShapeSignature",
                   {"name": f"held{i}", "signature": json.dumps(sig),
                    "kind": "faculty", "faculty": f"held{i}", "dim_types": DT})
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    obs = s.add_node("Observation",
                     {"signature": cells, "key": ["probe"], "status": "decoded",
                      "residual": cells, "decoded_epoch": ep, "dim_types": DT})
    s.add_edge(ag, "observed", obs)

    c, ms = _counted(native.run_rules)
    # LIVENESS (PROTOCOL §1.1: "scores at the floor" is satisfied by DEATH).
    # A sweep of a workload that recognises nothing would be a sweep of an empty
    # loop, and every G5 verdict on it would be about the emptiness.
    status = s.node(obs)["attrs"].get("status")
    del s, ag, native
    return c, ms, float(n_cells), status


# --------------------------------------------------------------------------- #
SWEEPS = {
    # axis id -> (label, point fn, the 7 sweep values, the independent variable)
    "G": ("graph size (retina cells)", lambda v: point_G(v)[:3],
          [8, 11, 16, 22, 32, 45, 64], "cells"),
    "B": ("boundary calls", lambda v: point_B(v)[:3],
          [50, 100, 200, 400, 800, 1600, 3200], "add_node+set_attr calls"),
    "E": ("epochs (rule-running entries)", lambda v: point_E(v)[:3],
          [2, 4, 8, 16, 32, 64, 128], "ticks"),
    "S": ("sd/identity signature cells (SYNTHETIC)",
          point_S,
          [12, 20, 37, 58, 93, 123, 142], "cells in ONE attribute"),
}


def run_sweep(axis):
    label, fn, values, ivname = SWEEPS[axis]
    print(f"[SWEEP-{axis}] {label}", flush=True)
    rows = []
    for v in values:
        res = fn(v)
        c, ms, x = res[0], res[1], res[2]
        rows.append({"value": v, "axis_x": x, "counters": c,
                     "wall_ms_CONTAMINABLE": ms,
                     "liveness": res[3] if len(res) > 3 else None})
        print(f"  x={v:>6} axis={x:>10.1f}  {ms:8.1f} ms "
              f"cand_enum={c.get('cand_enum')} "
              f"term_evals={c.get('term_evals_total')} "
              f"term_units={c.get('term_units_total')} "
              f"{rows[-1]['liveness'] or ''}", flush=True)

    # THE CONTROL -- the same counter, the same number of runs, the axis held
    # FIXED at the sweep's first value. This is the noise floor G5's criterion
    # is written against; nothing is assumed to be zero (prereg §3.2).
    print(f"[SWEEP-{axis}] control at x={values[0]} x{M_POINTS}", flush=True)
    ctrl = []
    for _ in range(M_POINTS):
        res = fn(values[0])
        ctrl.append({"counters": res[0], "wall_ms_CONTAMINABLE": res[1]})

    return {"axis": axis, "label": label, "iv": ivname,
            "values": values, "rows": rows, "control": ctrl,
            "axis_fold_range": max(r["axis_x"] for r in rows) / min(r["axis_x"] for r in rows)}


# --------------------------------------------------------------------------- #
def all_counter_names(sweep):
    names = set()
    for r in sweep["rows"]:
        names |= set(r["counters"])
    for r in sweep["control"]:
        names |= set(r["counters"])
    return sorted(names)


def series(rows, name):
    """A counter's series across rows. A counter ABSENT from a snapshot reads 0:
    the per-variant rows are emitted only when non-zero (350 cells x 7 points
    would bury the signal), and absent means the cell did not move."""
    return [int(r["counters"].get(name, 0)) for r in rows]


def g5_for(sweep, name):
    sw = series(sweep["rows"], name)
    ct = series(sweep["control"], name)
    verdict = AUDIT.scale_audit_g5_verdict(sw, ct)
    axis = [r["axis_x"] for r in sweep["rows"]]
    return {"counter": name, "axis": sweep["axis"], "verdict": verdict,
            "sweep": sw, "control": ct,
            "span_sweep": max(sw) - min(sw) if sw else 0,
            "span_control": max(ct) - min(ct) if ct else 0,
            # REPORTED, NEVER GATED (g5.rs). `None` when undefined, not a
            # fabricated 0.0 that would read as "measured and blind".
            "rho_REPORTED_NEVER_GATED": AUDIT.scale_audit_g5_rho(sw, axis)}


# --------------------------------------------------------------------------- #
def overhead(repeats=5):
    """ON-vs-OFF wall cost of the Term counter, on the two workloads that
    bracket it: the retina drive (29.7M Term evaluations -- the heaviest
    `evaluate` traffic in the tree) and the sd decode (424 evaluations but
    1.4M interior units).

    PROTOCOL §13: the DEFAULT FOLLOWS THE NUMBER, and the number is measured
    rather than assumed. The two precedents are quoted in the results so the
    comparison is explicit -- the winner-value instrument measured 81.41% and
    ships OFF; the fallback trace measured 0.000% and was honestly reported as
    free BECAUSE IT NEVER FIRES.

    This is WALL-CLOCK and therefore CONTAMINABLE (this machine swings 1.66x on
    load alone, measured). It is reported as a median of `repeats` with its
    spread, alternating ON/OFF within one process so a load excursion hits both
    arms rather than one. It is the ONLY wall-clock number in this rung, and it
    decides nothing except what is reported.
    """
    import statistics

    def timed(fn, on):
        gc.collect()
        AUDIT.scale_audit_reset()
        AUDIT.scale_audit_set_enabled(on)
        t0 = time.perf_counter()
        fn()
        ms = (time.perf_counter() - t0) * 1000.0
        AUDIT.scale_audit_set_enabled(False)
        return ms

    out = {}

    # --- workload 1: the retina drive (Term-evaluation heavy) ---------------
    g = 32
    s, ag, _ = _boot_eye(g)
    world = WaveWorld(s, h=g, w=g, seed=0, fovea_radius=0)
    add_lateral_retina(world)
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    for cp in s.nodes("ChangeParams"):
        s.set_attr(cp, "change", 1.0)
        s.set_attr(cp, "sustain", 1.0)
    set_lat_params(world, lateral=1.0)
    frames = _frames(g)
    _run(world, WARMUP_TICKS, g, "constant", frames)
    on, off = [], []
    for _ in range(repeats):
        off.append(timed(lambda: _run(world, 5, g, "constant", frames), False))
        on.append(timed(lambda: _run(world, 5, g, "constant", frames), True))
    del world, s, ag
    out["retina_drive_g32"] = {
        "off_ms_median": statistics.median(off), "on_ms_median": statistics.median(on),
        "off_samples": off, "on_samples": on,
        "overhead_pct": (statistics.median(on) / statistics.median(off) - 1.0) * 100.0}

    # --- workload 2: the sd decode (interior-unit heavy) --------------------
    on, off = [], []
    for _ in range(repeats):
        AUDIT.scale_audit_set_enabled(False)
        t0 = time.perf_counter(); point_S(142); off.append((time.perf_counter() - t0) * 1000.0)
        AUDIT.scale_audit_set_enabled(True)
        t0 = time.perf_counter(); point_S(142); on.append((time.perf_counter() - t0) * 1000.0)
        AUDIT.scale_audit_set_enabled(False)
    out["sd_decode_n142"] = {
        "off_ms_median": statistics.median(off), "on_ms_median": statistics.median(on),
        "off_samples": off, "on_samples": on,
        "overhead_pct": (statistics.median(on) / statistics.median(off) - 1.0) * 100.0}

    for k, v in out.items():
        print(f"[overhead] {k}: off {v['off_ms_median']:.1f} ms -> on "
              f"{v['on_ms_median']:.1f} ms = {v['overhead_pct']:+.2f}%", flush=True)
    return out


def zero_when_off(g=16):
    """G1 -- every counter reads 0 with the audit OFF on a LIVE workload.

    On a LIVE one, deliberately: a zero-when-off gate on a dead workload proves
    only that nothing ran (PROTOCOL §1.1, "scores at the floor is satisfied by
    DEATH"). Liveness is established by re-running the SAME workload with the
    audit on and requiring non-zero."""
    s, ag, _ = _boot_eye(g)
    world = WaveWorld(s, h=g, w=g, seed=0, fovea_radius=0)
    add_lateral_retina(world)
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    for cp in s.nodes("ChangeParams"):
        s.set_attr(cp, "change", 1.0)
        s.set_attr(cp, "sustain", 1.0)
    set_lat_params(world, lateral=1.0)
    frames = _frames(g)
    _run(world, WARMUP_TICKS, g, "constant", frames)

    AUDIT.scale_audit_reset()
    AUDIT.scale_audit_set_enabled(False)
    _run(world, 5, g, "constant", frames)
    off = counters()

    AUDIT.scale_audit_reset()
    AUDIT.scale_audit_set_enabled(True)
    _run(world, 5, g, "constant", frames)
    AUDIT.scale_audit_set_enabled(False)
    on = counters()
    del world, s, ag

    nonzero_off = {k: v for k, v in off.items() if v}
    return {"nonzero_while_off": nonzero_off,
            "all_zero_while_off": not nonzero_off,
            "term_evals_while_on": on.get("term_evals_total", 0),
            "workload_was_live": on.get("term_evals_total", 0) > 0}


def determinism(n=142):
    """G3 -- two identical runs, byte-identical counters. This is what pins the
    control span at exactly zero, which is what makes G5's criterion sharp."""
    AUDIT.scale_audit_set_enabled(False)
    a = point_S(n)[0]
    b = point_S(n)[0]
    diff = {k: (a.get(k), b.get(k)) for k in set(a) | set(b) if a.get(k) != b.get(k)}
    return {"differing_counters": diff, "byte_identical": not diff}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/g5_responsiveness.json")
    a = ap.parse_args()

    prov = provenance_line()
    print(f"[provenance] {prov}", flush=True)
    out = {"provenance": prov,
           "prereg": "VISION_TERM_EVAL_COUNTER_PREREG.md",
           "prereg_commit": "7c382089",
           "machine": machine(),
           "load_state_at_start": load_state(),
           "m_points": M_POINTS,
           "claimed_axis": CLAIMED_AXIS,
           "seeds": {"SWEEP_S": SEED_SWEEP_S, "SWEEP_G": SEED_SWEEP_G}}

    print("[G1] zero-when-off on a LIVE workload", flush=True)
    out["G1_zero_when_off"] = zero_when_off()
    print(f"  -> {out['G1_zero_when_off']['all_zero_while_off']} "
          f"(live: {out['G1_zero_when_off']['workload_was_live']})", flush=True)

    print("[G3] determinism", flush=True)
    out["G3_determinism"] = determinism()
    print(f"  -> byte_identical={out['G3_determinism']['byte_identical']}", flush=True)

    out["sweeps"] = {ax: run_sweep(ax) for ax in ("G", "B", "E", "S")}

    for ax, sw in out["sweeps"].items():
        print(f"[SWEEP-{ax}] axis fold range = {sw['axis_fold_range']:.1f}x", flush=True)

    # --- G5 ON EACH COUNTER'S OWN CLAIMED AXIS ------------------------------
    verdicts = {}
    for name, ax in CLAIMED_AXIS.items():
        verdicts[name] = g5_for(out["sweeps"][ax], name)
    # The new families claim SWEEP-S. Per-variant cells are discovered from the
    # snapshots rather than listed, so a variant this workload happens to
    # exercise cannot be omitted by an author who did not think of it.
    for name in all_counter_names(out["sweeps"]["S"]):
        if name.startswith(("term_eval:", "term_unit:", "term_evals_total",
                            "term_units_total")):
            verdicts[name] = g5_for(out["sweeps"]["S"], name)
    out["g5_on_claimed_axis"] = verdicts

    # --- THE A8 BLINDNESS, SYSTEMATICALLY -----------------------------------
    # Every counter on SWEEP-S. NOT counted as a G5 failure for counters that
    # never claimed the sd axis: conflating "blind to its own axis" with "blind
    # to somebody else's" would inflate the finding, and this rung's whole
    # subject is instruments that report more than they measured.
    out["a8_blindness_on_sweep_S"] = {
        n: g5_for(out["sweeps"]["S"], n)
        for n in all_counter_names(out["sweeps"]["S"])}

    # --- THE FULL CROSS-TABLE: every counter on EVERY sweep -----------------
    #
    # The pre-registered verdict is the one on the CLAIMED axis and nothing
    # here replaces it. This table exists so that a counter judged BLIND can be
    # DIAGNOSED -- "blind to graph size but proportional to epochs" is a
    # different fact from "blind to everything", and the claim table is MINE,
    # so a mis-assignment in it is my error to report rather than a counter's
    # defect. Editing the claim table after seeing the result would be exactly
    # the "counter picks its axis afterwards" unfairness the prereg forbids;
    # reporting the whole grid is the honest alternative.
    cross = {}
    for ax, sw in out["sweeps"].items():
        for n in all_counter_names(sw):
            cross.setdefault(n, {})[ax] = g5_for(sw, n)["verdict"]
    out["cross_table_all_counters_all_sweeps"] = cross

    # --- G5's OWN POSITIVE CONTROLS (prereg §3.4) ---------------------------
    self_ctl = {}
    for label, (name, ax) in G5_SELF_CONTROLS.items():
        v = g5_for(out["sweeps"][ax], name)
        want = "BLIND" if label.startswith("RED") else "RESPONSIVE"
        self_ctl[label] = {"counter": name, "axis": ax, "got": v["verdict"],
                           "expected": want, "ok": v["verdict"] == want,
                           "detail": v}
        print(f"[G5 self-control] {label}: {name} on SWEEP-{ax} -> "
              f"{v['verdict']} (expected {want}) "
              f"{'OK' if v['verdict'] == want else 'FAILED'}", flush=True)
    out["g5_self_controls"] = self_ctl
    out["g5_self_controls_all_ok"] = all(c["ok"] for c in self_ctl.values())

    print("[overhead] ON vs OFF -- the number the DEFAULT follows (§13)", flush=True)
    out["overhead_CONTAMINABLE_WALL_CLOCK"] = overhead()

    tally = {}
    for v in verdicts.values():
        tally[v["verdict"]] = tally.get(v["verdict"], 0) + 1
    out["verdict_tally"] = tally
    print(f"[tally] {tally}", flush=True)

    out["load_state_at_end"] = load_state()
    with open(os.path.join(ROOT, a.out), "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[done] wrote {a.out}", flush=True)


if __name__ == "__main__":
    main()
