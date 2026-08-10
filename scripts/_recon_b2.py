"""RECON (rung B) part 2 — isolate WHERE the work is and whether B can reduce it.

(1) Per-tick NEW has_task edge count vs cells (is the driver O(cells)?).
(2) The ABSTRACT stable-edge attr-flip shape B targets: N stable hub->cell edges,
    a where-rule reading a per-cell attr; each tick flip the attr on only K cells.
    Measure committed-matcher where_evals/cand_enum vs N (the reducible opportunity).
All on the COMMITTED engine — structural diagnosis, not a rung-B result.
"""
from __future__ import annotations
import math, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runners", "dsl", "python"))
import substrate_rs as srs
from scripts import _recon_b as R
from domains import doom_photon_world as dpw


def new_task_edges_per_tick():
    print("=== (1) new has_task edges per tick vs cells (driver cost) ===")
    for (ne, na) in [(8, 10), (12, 15), (16, 20), (20, 25)]:
        eye = R.build_eye(ne, na); inner = eye.substrate._inner
        rng = np.random.default_rng(R.SEED)
        for t in range(4):
            luma = R.moving_bar_frame(ne, na, t)
            eye.submit_photons_2d(dpw.photon_packets(luma, rng))
            inner.run_cognitive_tasks(1); inner.run_rules(); eye.prune_settled_tasks()
        before = len(list(eye.substrate.nodes("CognitiveTask")))
        eye.submit_photons_2d(dpw.photon_packets(R.moving_bar_frame(ne, na, 4), rng))
        after = len(list(eye.substrate.nodes("CognitiveTask")))
        print(f"  cells={ne*na:5d}  new CognitiveTask nodes this tick = {after-before}")


def fit(cells, vals):
    xs = [math.log(c) for c in cells]; ys = [math.log(max(v, 1)) for v in vals]
    n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
    return sum((x-mx)*(y-my) for x, y in zip(xs, ys)) / sum((x-mx)**2 for x in xs)


def abstract_stable_attr_flip(K=3):
    """N cells, each a STABLE hub->cell edge + cell->flag edge (never deleted).
    A where-rule fires when cell.armed==1 & flag exists. Each tick, the host
    flips `armed` on only K cells (a sparse where-flip on stable edges). Measure
    committed-engine per-tick match work vs N. This is EXACTLY B's target shape,
    which — unlike the eye — has stable edges and sparse per-tick attr change."""
    print(f"\n=== (2) abstract stable-edge attr-flip shape, K={K} flipped/tick ===")
    cells_list, ce, we = [], [], []
    for N in [64, 128, 256, 512]:
        s = srs.Substrate(); inner = s._inner
        # Rule: hub -has_cell-> cell ; cell -has_flag-> flag ; where cell.armed==1
        #       effect: set cell.fired=1  (idempotent-ish; guarded by Not fired==1)
        inner.add_rule({
            "name": "fire_armed_cell",
            "match": [["hub", "has_cell", "cell"], ["cell", "has_flag", "flag"]],
            "where": {"type": "And", "items": [
                {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "cell"}, "key": "armed"},
                 "b": {"type": "Lit", "value": 1.0}},
                {"type": "Not", "arg": {"type": "Eq",
                 "a": {"type": "Attr", "node": {"type": "Var", "name": "cell"}, "key": "fired"},
                 "b": {"type": "Lit", "value": 1.0}}},
            ]},
            "effects": [["set_attr", "cell", "fired", 1.0]],
        })
        hub = s.add_node("Hub", {"v": 0.0})
        cells = []
        for i in range(N):
            c = s.add_node("Cell", {"armed": 0.0, "fired": 0.0, "v": float(i)})
            f = s.add_node("Flag", {"v": float(i)})
            inner.add_edge_unchecked(hub, "has_cell", c)
            inner.add_edge_unchecked(c, "has_flag", f)
            cells.append(c)
        inner.run_rules()  # settle: nothing armed
        # measure one tick: flip armed on K cells, reset their fired, run_rules
        srs._native.Substrate.scale_audit_set_enabled(True)
        srs._native.Substrate.scale_audit_reset()
        for i in range(K):
            s.set_attr(cells[i], "armed", 1.0)
            s.set_attr(cells[i], "fired", 0.0)
        inner.run_rules()
        snap = dict(srs._native.Substrate.scale_audit_snapshot())
        srs._native.Substrate.scale_audit_set_enabled(False)
        cells_list.append(N); ce.append(snap.get("cand_enum", 0)); we.append(snap.get("where_evals", 0))
        print(f"  N={N:5d}  cand_enum={snap.get('cand_enum',0):6d}  where_evals={snap.get('where_evals',0):6d}"
              f"  (only K={K} cells flipped)")
    print(f"  EXPONENT cand_enum={fit(cells_list,ce):.3f}  where_evals={fit(cells_list,we):.3f}")
    print("  -> if exponent ~1.0 the committed matcher re-scans ALL N on a K-cell flip (B's opportunity: reduce to O(K))")


def _j(d):
    import json
    return json.dumps(d)


def _install_rule(inner, rule):
    # Fallback: use the same install path the eye seeds use.
    import json
    manifest = {"id": "recon_abstract", "version": "1.0.0", "nodes": [], "edges": [],
                "productions": [], "rules": [rule]}
    agent = None
    inner.load_seed_manifest(json.dumps(manifest), agent)


if __name__ == "__main__":
    new_task_edges_per_tick()
    abstract_stable_attr_flip(K=3)
