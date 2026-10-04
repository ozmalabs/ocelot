"""PREDICATE RETRACTION (block 194000, ladder rung B) — measurement.

IMPORT-INERT (the exact A revert bug): this module NEVER mutates shared engine
state at module top level. Every flag toggle happens inside `_flags`, a scoped
context manager that restores OFF on exit, around each measured call.

The covered shape is the ABSTRACT stable-edge attr-flip A named: N STABLE
`hub -has_cell-> cell` + `cell -has_flag-> flag` edges (never deleted); a where-
rule fires when `cell.armed==1` AND the cell has no `fired` edge yet (a STRUCTURAL
edge guard — idempotent, so full-rescan OFF and node-seeded ON produce the SAME
graph); the effect adds the `fired` edge. Each tick the host flips `armed` on
only K cells. Full rescan re-scans all N (O(N)); node-seeded re-eval touches only
the K flipped cells (O(K)) — byte-identical.
"""
from __future__ import annotations
import contextlib
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runners", "dsl", "python"))

import substrate_rs as srs  # noqa: E402

MAX_ROUNDS = 200


def _lit(v):
    return {"type": "Lit", "value": v}


def _var(n):
    return {"type": "Var", "name": n}


def _no_edge_out(var, et):
    return {"type": "Not", "arg": {"type": "Exists", "var_name": "_y", "predicate": _lit(1.0),
            "source": {"type": "Neighbours", "node": _var(var), "edge_type": et, "any_type": False}}}


@contextlib.contextmanager
def _flags(inner, *, pred, unsound=False):
    """Scoped: set the predicate-retraction flags for the duration, restore OFF.

    BOTH arms also run with `write_frontier` (edge locality) ON. Since 616bd532
    (COW fork support) a rule-effect write of an edge type a consumer reads in a
    TERM clears that consumer's cursor (`hits_term_edge` in mark_dirty_for: a term
    read may change predicates of stable bindings). The covered rule reads its
    own effect edge `fired` in its where-clause, so every firing cleared its OWN
    cursor and the next pass was a full O(N) re-match in both arms (measured with
    the committed binaries: f1fbf43f ON 6 / 6 at N=64 / 256, 616bd532 ON 70 / 262).
    `write_frontier` is the engine's mechanism for exactly that read shape
    (`Neighbours` of a match variable -> re-check only the edge's endpoints);
    with it the OFF arm is still a full rescan (the external attr flip) and only
    predicate retraction flattens the ON arm, so the arms still isolate rung B."""
    inner.set_write_frontier(True)
    inner.set_predicate_retraction(pred)
    inner.set_predicate_retraction_unsound(unsound)
    try:
        yield
    finally:
        inner.set_predicate_retraction_unsound(False)
        inner.set_predicate_retraction(False)
        inner.set_write_frontier(False)


def _build(N):
    s = srs.Substrate()
    inner = s._inner
    inner.add_rule({
        "name": "fire_armed_cell",
        "match": [["hub", "has_cell", "cell"], ["cell", "has_flag", "flag"]],
        "where": {"type": "And", "items": [
            {"type": "Eq",
             "a": {"type": "Attr", "node": _var("cell"), "key": "armed"}, "b": _lit(1.0)},
            _no_edge_out("cell", "fired"),
        ]},
        "effects": [["add_edge", "cell", "fired", "flag"]],
    })
    hub = s.add_node("Hub", {"v": 0.0})
    cells = []
    for i in range(N):
        c = s.add_node("Cell", {"armed": 0.0, "v": float(i)})
        f = s.add_node("Flag", {"v": float(i)})
        inner.add_edge_unchecked(hub, "has_cell", c)
        inner.add_edge_unchecked(c, "has_flag", f)
        cells.append(c)
    return s, inner, cells


def _dump(inner):
    import scripts.per_sensor_epoch_measure as P
    return P.dump(inner)


def run_tick(N, K, *, pred, unsound=False):
    """Build N cells, settle (nothing armed), then ONE tick: flip `armed` on K
    cells and run_rules. Returns (fired_count, cand_enum, float-exact dump)."""
    s, inner, cells = _build(N)
    inner.run_rules(MAX_ROUNDS)  # settle: establish cursors, nothing armed
    with _flags(inner, pred=pred, unsound=unsound):
        srs._native.Substrate.scale_audit_set_enabled(True)
        srs._native.Substrate.scale_audit_reset()
        for i in range(K):
            s.set_attr(cells[i], "armed", 1.0)
        inner.run_rules(MAX_ROUNDS)
        snap = dict(srs._native.Substrate.scale_audit_snapshot())
        srs._native.Substrate.scale_audit_set_enabled(False)
    fired = 0
    for c in cells:
        for _ in inner.out_edges(c, "fired") if hasattr(inner, "out_edges") else []:
            fired += 1
            break
    dump = _dump(inner)
    return {"cand_enum": snap.get("cand_enum", 0),
            "cand_tested": snap.get("cand_tested", 0),
            "where_evals": snap.get("where_evals", 0),
            "dump": dump}


def _fired_count(s, inner, cells):
    n = 0
    for c in cells:
        outs = inner.out_neighbours(c, "fired") if hasattr(inner, "out_neighbours") else None
        if outs:
            n += 1
    return n


def scaling(sizes=(64, 128, 256, 512), K=3):
    """H1 — per-tick cand_enum vs N for a K-cell flip, OFF (full rescan) vs ON
    (node-seeded). Fit the exponent."""
    out = {"sizes": list(sizes), "K": K, "per_n": {"off": {}, "on": {}}}
    for arm, pred in (("off", False), ("on", True)):
        for N in sizes:
            r = run_tick(N, K, pred=pred)
            out["per_n"][arm][N] = {k: r[k] for k in ("cand_enum", "cand_tested", "where_evals")}
    for arm in ("off", "on"):
        xs = [math.log(n) for n in sizes]
        ys = [math.log(max(1, out["per_n"][arm][n]["cand_enum"])) for n in sizes]
        out.setdefault("cand_enum_exponent", {})[arm] = _slope(xs, ys)
    return out


def _slope(xs, ys):
    n = len(xs); sx = sum(xs); sy = sum(ys)
    sxx = sum(x * x for x in xs); sxy = sum(x * y for x, y in zip(xs, ys))
    d = n * sxx - sx * sx
    return (n * sxy - sx * sy) / d if d else float("nan")


def byte_identity(N=128, K=5):
    """C2 — OFF (full rescan) vs ON (node-seeded), same tick, float-exact dump."""
    off = run_tick(N, K, pred=False)
    on = run_tick(N, K, pred=True)
    return {"identical": off["dump"] == on["dump"],
            "off_cand_enum": off["cand_enum"], "on_cand_enum": on["cand_enum"]}


def falsifier(N=128, K=5):
    """F1 — the unsound arm (drops one dirty node) MUST diverge from full rescan."""
    off = run_tick(N, K, pred=False)
    unsound = run_tick(N, K, pred=True, unsound=True)
    return {"diverges": off["dump"] != unsound["dump"],
            "off_cand_enum": off["cand_enum"], "unsound_cand_enum": unsound["cand_enum"]}


def has_flag():
    return hasattr(srs.Substrate()._inner, "set_predicate_retraction")


if __name__ == "__main__":
    import json
    print("flag present:", has_flag())
    print("byte_identity:", json.dumps(byte_identity()))
    print("falsifier:", json.dumps(falsifier()))
    sc = scaling()
    for arm in ("off", "on"):
        print(f"  {arm}: ", {n: sc['per_n'][arm][n]['cand_enum'] for n in sc['sizes']},
              "exp=%.3f" % sc["cand_enum_exponent"][arm])
