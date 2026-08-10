#!/usr/bin/env python3
"""INCREMENTAL MATCH — measurement harness (block 192000, ladder rung A).

Prereg: `INCREMENTAL_MATCH_PREREG.md`, committed ALONE before any number here.

ONE engine mechanism, DEFAULT OFF, a DROPPABLE BYTE-IDENTICAL MIRROR:

  * `incremental_match` (engine flag) — validate semi-naive cursors against
    PER-EDGE-TYPE delete versions instead of the single global one, so a delete
    of an UNRELATED edge type no longer forces a full rescan. Byte-identity to
    the committed (full-rescan) engine IS the gate.
  * `incremental_match_unsound` (engine flag) — THE RETRACTION FALSIFIER.
    Accepts a stale cursor regardless of its edge type's delete version. MUST
    diverge on a deleting workload.

The scaling metric is the deterministic WORK COUNT `cand_enum` (candidate
enumerations), read from `scale_audit`, NOT wall-clock. Mechanical I/O +
measurement only; every decision lives in the Rust engine or in graph data.
"""
from __future__ import annotations

import json
import math
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts import per_sensor_epoch_measure as P  # noqa: E402
import scripts.empty_match_proof_measure as E      # noqa: E402

SEED = 192000
OUTDIR = os.path.join(ROOT, "results", "incremental_match")
MAX_ROUNDS = P.MAX_ROUNDS


# --------------------------------------------------------------- the flag -----
def _set_incr(inner, on, unsound=False):
    """Toggle THIS rung's flag. On the BASE engine (no such method) the OFF arm
    is a no-op returning False (so the identical harness runs on both engines for
    C1); the ON arm raises."""
    fn = getattr(inner, "set_incremental_match", None)
    if fn is None:
        if on:
            raise RuntimeError("this engine has no set_incremental_match (rebuild)")
        return False
    fn(on)
    if unsound:
        inner.set_incremental_match_unsound(True)
    return True


import contextlib  # noqa: E402


@contextlib.contextmanager
def _incr_setter():
    """SCOPED reuse of the 189000 battery: temporarily rebind
    `empty_match_proof_measure._set_proof` so its ("off","proof","unsound") arms
    toggle OUR flag instead — then RESTORE it. This reuses every validated
    workload (vision_carve, scheduler, quiet_areas, scheduler_wide, conversation,
    doom_accel), the landed 160x120 carve, the graph-path onset stream and the
    no-free-lunch control, swapping only WHICH engine flag the arms drive
    ("proof" == incremental ON). CRITICAL: the rebind is scoped and restored so
    importing this module NEVER pollutes the shared 189000 harness — otherwise a
    same-session `test_empty_match_proof_migrated` run would silently toggle THIS
    flag instead of empty_match_proof (which is exactly the harness-leak this
    replaces)."""
    saved = E._set_proof
    E._set_proof = _set_incr
    try:
        yield
    finally:
        E._set_proof = saved


def run_workload(name, incr, unsound=False):
    """Run a 189000 battery workload with OUR flag driving the arm (scoped)."""
    with _incr_setter():
        return E.WORKLOADS[name](incr, unsound)


def run_landed_carve(incr, unsound=False):
    with _incr_setter():
        return E.landed_carve(incr, unsound)


def run_graph_onsets(incr, unsound=False):
    with _incr_setter():
        return E.graph_path_onsets(incr, unsound)


def has_flag():
    import substrate_rs as srs
    return hasattr(srs.Substrate()._inner, "set_incremental_match")


# ---- C1/C2 REDUCTION on the 189000 battery (off == incremental-ON) -----------
def battery_identity(arms=("off", "incr", "unsound")):
    """Full float-exact dump on every 189000 workload, per arm. off vs incr =
    C2 (reduction: incremental ON ≡ full rescan). off dump is also the C1 base
    comparison target when run on the base engine."""
    arm_flags = {"off": (False, False), "incr": (True, False),
                 "unsound": (True, True)}
    out = {}
    for name in E.WORKLOADS:
        row = {}
        for a in arms:
            on, uns = arm_flags[a]
            try:
                row[a] = run_workload(name, on, uns)
            except RuntimeError:
                row[a] = None  # base engine, ON arm unavailable
        out[name] = {
            "off_eq_incr": row.get("off") is not None and row["off"] == row.get("incr"),
            "off_eq_unsound": row.get("off") is not None and row["off"] == row.get("unsound"),
            "digests": {a: (hash(json.dumps(row[a], sort_keys=True, default=str))
                            if row.get(a) is not None else None) for a in arms},
            "_dumps": row,
        }
    return out


def landed_carve_identity():
    """C2b — the landed 160x120 carve, off vs incremental ON (+ unsound)."""
    off = run_landed_carve(False, False)
    incr = run_landed_carve(True, False)
    unsound = run_landed_carve(True, True)
    return {"off": off, "incr": incr, "unsound": unsound,
            "off_eq_incr": off == incr, "off_eq_unsound": off == unsound}


def graph_onsets_identity():
    """C2d/F1 target — graph-path onset stream, off vs ON (+ unsound)."""
    off = run_graph_onsets(False, False)
    incr = run_graph_onsets(True, False)
    unsound = run_graph_onsets(True, True)
    return {"off": off, "incr": incr, "unsound": unsound,
            "off_eq_incr": off == incr, "off_eq_unsound": off == unsound}


# ---- H1: the COVERED append-only shape, cand_enum vs graph size --------------
def _build_covered(n, incr, unsound=False):
    """A WHERE-LESS 2-edge CROSS rule: match [hub,link,c],[hub,other,d] ->
    set_attr d 'seen' 1. Full-rescan enumerates link x other = O(n^2); the
    incremental path after a settle scans only the NEW link edges = O(n).
    Where-less, so `mark_node_mutation` (fired by add_node) does NOT clear its
    cursor under ON — this is exactly the covered shape (rung B is the WHERE
    shape). An unrelated `zombie` edge is deleted each tick to prove the cursor
    survives an unrelated-type delete."""
    import substrate_rs as srs
    s = srs.Substrate()
    inner = s._inner
    _set_incr(inner, incr, unsound)
    hub = s.add_node("Hub", {"v": 0.0})
    lefts, rights = [], []
    for i in range(n):
        li = s.add_node("L", {"v": float(i)})
        ri = s.add_node("R", {"v": float(i)})
        inner.add_edge_unchecked(hub, "link", li)
        inner.add_edge_unchecked(hub, "other", ri)
        lefts.append(li); rights.append(ri)
    # unrelated edge type, for the per-tick unrelated delete
    zt = s.add_node("Z", {"v": 0.0})
    inner.add_edge_unchecked(hub, "zombie", zt)
    inner.add_rule({
        "name": "covered_cross",
        "match": [["h", "link", "c"], ["h", "other", "d"]],
        "effects": [["set_attr", "d", "seen", 1.0]],
    })
    return s, inner, hub, zt


def covered_scaling(sizes=(25, 50, 100, 200), reps=3):
    """H1 — cand_enum for ONE tick (add 1 new left cell + delete the unrelated
    zombie edge + run_rules) vs graph size n, under full-rescan (off) and
    incremental (on). Fit the exponent of cand_enum-vs-n."""
    import substrate_rs as srs
    out = {"per_n": {}, "sizes": list(sizes)}
    for arm, incr in (("off", False), ("incr", True)):
        ces = {}
        for n in sizes:
            vals = []
            for _ in range(reps):
                s, inner, hub, zt = _build_covered(n, incr)
                inner.run_rules(MAX_ROUNDS)          # settle: cursors established
                srs._native.Substrate.scale_audit_set_enabled(True)
                srs._native.Substrate.scale_audit_reset()
                # ONE tick: add a new left cell (+edge), delete unrelated zombie
                li = s.add_node("L", {"v": float(n)})
                inner.add_edge_unchecked(hub, "link", li)
                inner.remove_edge_unchecked(hub, "zombie", zt)  # unrelated delete
                inner.run_rules(MAX_ROUNDS)
                snap = dict(srs._native.Substrate.scale_audit_snapshot())
                srs._native.Substrate.scale_audit_set_enabled(False)
                vals.append({k: snap.get(k, 0) for k in
                             ("cand_enum", "cand_tested", "where_evals",
                              "bindings_cloned", "rule_enumerations")})
            # median per counter
            med = {k: statistics.median(v[k] for v in vals) for k in vals[0]}
            ces[n] = med
        out["per_n"][arm] = ces
    # exponent fit on cand_enum
    for arm in ("off", "incr"):
        xs = [math.log(n) for n in sizes]
        ys = [math.log(max(1, out["per_n"][arm][n]["cand_enum"])) for n in sizes]
        out.setdefault("cand_enum_exponent", {})[arm] = _slope(xs, ys)
    return out


def _slope(xs, ys):
    n = len(xs); sx = sum(xs); sy = sum(ys)
    sxx = sum(x * x for x in xs); sxy = sum(x * y for x, y in zip(xs, ys))
    d = n * sxx - sx * sx
    return (n * sxy - sx * sy) / d if d else float("nan")


# ---- C3 + F1: RETRACTION on a DELETING workload ------------------------------
def deleting_workload(incr, unsound=False, n=60):
    """A rule R2 reads edge type `vlink` in a WHERE (negation): match
    [hub,slot,s] where NOT (s has an incoming block edge) -> set_attr s 'open' 1.
    Build with every slot blocked (a `block` edge), settle (nothing open), then
    DELETE half the block edges and run_rules. Deleting a block edge FLIPS the
    where on a STABLE `slot` edge -> the slot becomes open. Sound incremental
    must catch this (invalidate_readers_of_deleted_edge_type); the UNSOUND arm
    accepts the stale cursor and MISSES it -> diverges. Returns the float-exact
    dump."""
    import substrate_rs as srs
    s = srs.Substrate()
    inner = s._inner
    _set_incr(inner, incr, unsound)
    hub = s.add_node("Hub", {"v": 0.0})
    slots, blocks = [], []
    for i in range(n):
        si = s.add_node("Slot", {"v": float(i), "open": 0.0})
        inner.add_edge_unchecked(hub, "slot", si)
        bi = s.add_node("Blk", {"v": float(i)})
        inner.add_edge_unchecked(bi, "block", si)      # block -> slot
        slots.append(si); blocks.append((bi, si))
    inner.add_rule({
        "name": "open_when_unblocked",
        "match": [["h", "slot", "s"]],
        "where": {"type": "Not", "arg": {
            "type": "Exists",
            "source": {"type": "InNeighbours",
                       "node": {"type": "Var", "name": "s"},
                       "edge_type": "block"},
            "var_name": "b",
            "predicate": {"type": "Lit", "value": 1.0}}},
        "effects": [["set_attr", "s", "open", 1.0]],
    })
    inner.run_rules(MAX_ROUNDS)                          # settle: none open
    # RETRACT support: delete the block edge on the first half of the slots.
    for (bi, si) in blocks[: n // 2]:
        inner.remove_edge(bi, "block", si)              # checked delete
    inner.run_rules(MAX_ROUNDS)
    out = P.dump(inner)
    n_open = sum(1 for si in slots
                 if s.node(si)["attrs"].get("open", 0.0) == 1.0)
    return {"dump": out, "n_open": n_open}


def retraction_identity(n=60):
    """C3 + F1 on the where-flip-on-delete NEGATION workload. A `Not Exists`
    where over a `block` edge is read by a rule that matches `slot`; deleting a
    block edge FLIPS the where on a STABLE slot edge -> the slot opens. This is
    the ONE observable delete-effect in a monotone forward-chaining engine
    (retraction that RE-ENABLES a match), so it is the right F1 target.

      C3 (sound): off == incr, and both RETRACT — every unblocked slot opens
          (n/2), because the checked delete clears the where-reader's cursor.
      F1 (unsound): the falsifier SKIPS that cursor clear, so the where-flip is
          silently missed -> fewer slots open -> the dump DIVERGES. A wrong
          retraction that broke nothing would make the reduction gate vacuous."""
    off = deleting_workload(False, False, n)
    incr = deleting_workload(True, False, n)
    unsound = deleting_workload(True, True, n)
    return {
        "n": n,
        "off_n_open": off["n_open"], "incr_n_open": incr["n_open"],
        "unsound_n_open": unsound["n_open"],
        "off_eq_incr": off["dump"] == incr["dump"],
        "unsound_diverges": off["dump"] != unsound["dump"],
    }


# --------------------------------------------------------------- main ---------
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    os.makedirs(OUTDIR, exist_ok=True)
    mode = argv[0] if argv else "all"
    res = {}
    if mode in ("all", "base"):
        # C1 base: off-arm dumps on WHATEVER engine is installed (run this on
        # the BASE engine first, then compare to the rung engine's off arm).
        res["battery_off"] = {name: run_workload(name, False)
                              for name in E.WORKLOADS}
    if mode in ("all", "reduction"):
        res["battery"] = {k: {kk: vv for kk, vv in v.items() if kk != "_dumps"}
                          for k, v in battery_identity().items()}
        res["landed_carve"] = {k: v for k, v in landed_carve_identity().items()
                               if k in ("off_eq_incr", "off_eq_unsound")}
        res["retraction"] = retraction_identity()
    if mode in ("all", "scaling"):
        res["covered_scaling"] = covered_scaling()
    out = os.path.join(OUTDIR, f"incremental_match_{mode}.json")
    with open(out, "w") as f:
        json.dump(res, f, indent=2, default=str)
    print(json.dumps(res, indent=2, default=str)[:4000])
    print("WROTE", out)
    return res


if __name__ == "__main__":
    main()
