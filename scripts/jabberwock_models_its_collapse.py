#!/usr/bin/env python3
"""jabberwock_models_its_collapse -- standalone demonstrator + DISCRIMINATIVE
gate for `domains/collapse_model.py`: TIER 4 of the collapse-modeling stack,
the graph's model of its OWN total collapse as one object.

Mirrors `scripts/jabberwock_frozen_core_check.py`'s console-report shape.
Sections:

  1. CONVERGENT baseline -- a settled boot_core() graph (no volatile
     frontier at all): predict_collapse reports converged=True, residual
     0.0, frontier_growth_rate <= 0.

  2. THE HEADLINE -- reconstruct the axis-runaway condition (a graph where
     each collapse round mints new unresolved CapabilityAxes, the exact
     pathology the live 10-minute run showed BEFORE the novelty-gate fix
     2996d48a) and show predict_collapse PREDICTS non-convergence (growing
     frontier) from a FEW bounded, reversible forward-look rounds -- BEFORE
     running the pathology out.

  3. THE CONTROL -- the SAME forward-look mechanism against a FULLY-COVERED
     residual (recognized, never minted) predicts convergence -- proving
     section 2 discriminates on the real rule outcome, not on "we added
     nodes so the count went up".

  4. FIXED POINTS INCLUDE THE FROZEN CORE -- the recursion anchor: the
     tier-5 recursion (a model of a graph containing a model of that graph)
     is well-founded because it bottoms out at nodes `domains/frozen_core.py`
     proves no mutation grammar can ever move.

  5. SELF-INCLUSION -- the CollapseModel node is itself in the graph; a
     re-run sees the prior CollapseModel and does not blow up.

  6. TRACTABILITY -- on a REAL, fully-booted ~17.5k-node agent
     (`substrate.boot_all.load_all_seeds`), predict_collapse's own measured
     runtime is reported -- the empirical proof this is not a full-graph
     K-step simulation.

Exit code: 0 iff every discriminative expectation in sections 1-5 holds.
Section 6 is a report only (no pass/fail -- there is no "correct" runtime
threshold to gate on, only the STRUCTURAL claim that it is cheap, which the
printed number lets a human verify).
"""
from __future__ import annotations

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                           # noqa: E402
from substrate.seed_loader import manifest_for                      # noqa: E402
from domains import reflective_faculty as rf                        # noqa: E402
from domains.collapse_model import (                                # noqa: E402
    fixed_points, predict_collapse, volatile_frontier,
)


def _hr(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def _shape_decode_agent():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    return s, ag, native


def _add_pending_observation(s, ag, key: str):
    obs = s.add_node("Observation", {"signature": [[key, "X"]], "key": [key], "status": "pending"})
    s.add_edge(ag, "observed", obs)
    return obs


def main() -> int:
    ok_overall = True

    # -------------------------------------------------------------------
    _hr("1. CONVERGENT baseline -- a settled graph, no volatile frontier")
    s1, ag1 = boot_core()
    res1 = predict_collapse(s1)
    print(f"converged={res1.converged} residual={res1.residual} "
          f"n_fixed={res1.n_fixed} n_volatile={res1.n_volatile} "
          f"growth_rate={res1.frontier_growth_rate} runtime_s={res1.runtime_s:.4f}")
    ok1 = res1.converged is True and res1.residual == 0.0 and res1.frontier_growth_rate <= 0.0
    print(f"expected converged=True, residual==0.0, growth<=0: {ok1}")
    ok_overall = ok_overall and ok1

    # -------------------------------------------------------------------
    _hr("2. THE HEADLINE -- axis-runaway condition predicts NON-convergence")
    s2, ag2, native2 = _shape_decode_agent()
    for i in range(3):
        _add_pending_observation(s2, ag2, f"zzzrunaway{i}")
    t0 = time.time()
    res2 = predict_collapse(s2, horizon=3, imagine_steps=2)
    dt2 = time.time() - t0
    print(f"counts_trajectory={res2.counts_trajectory}")
    print(f"converged={res2.converged} growth_rate={res2.frontier_growth_rate} "
          f"forward_look_ran={res2.forward_look_ran} runtime_s={dt2:.4f}")
    ok2 = (res2.forward_look_ran and res2.frontier_growth_rate > 0.0
           and res2.converged is False
           and res2.counts_trajectory[-1] > res2.counts_trajectory[0])
    print(f"expected converged=False, growth>0, trajectory strictly grows: {ok2}")
    print("(this is a FEW bounded forward-look rounds on a small snapshot -- "
          f"predicted BEFORE running the pathology out; {dt2:.4f}s wall)")
    ok_overall = ok_overall and ok2

    # -------------------------------------------------------------------
    _hr("3. THE CONTROL -- a fully-covered residual predicts convergence")
    s3, ag3, native3 = _shape_decode_agent()
    sig = [["zzzcovered", "X"]]
    s3.add_node("ShapeSignature", {"name": "zzzcovered_shape", "signature": sig})
    obs3 = s3.add_node("Observation", {"signature": sig, "key": ["zzzcovered"], "status": "pending"})
    s3.add_edge(ag3, "observed", obs3)
    res3 = predict_collapse(s3, horizon=3, imagine_steps=2)
    print(f"counts_trajectory={res3.counts_trajectory}")
    print(f"converged={res3.converged} growth_rate={res3.frontier_growth_rate}")
    ok3 = (res3.forward_look_ran and res3.frontier_growth_rate <= 0.0
           and res3.converged is True and res3.counts_trajectory[-1] == 0)
    print(f"expected converged=True, growth<=0, trajectory shrinks to 0: {ok3}")
    print("(SAME forward-look mechanism as section 2 -- this proves the divergence "
          "call is discriminating on the real rule outcome, not merely on node count)")
    ok_overall = ok_overall and ok3

    # -------------------------------------------------------------------
    _hr("4. FIXED POINTS INCLUDE THE FROZEN CORE (the recursion anchor)")
    s4, ag4 = boot_core()
    s4._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag4)
    s4._inner.load_seed_manifest(manifest_for("autonomy"), ag4)
    fp4 = fixed_points(s4)
    understand = [n for n in fp4["frozen_drive"] if s4.node(n)["attrs"].get("name") == "understand"]
    ok4 = (fp4["_closure_error"] is None and bool(understand)
           and s4.node(understand[0])["attrs"].get("frozen") is True)
    print(f"frozen_drive fixed points: {[s4.node(n)['attrs'].get('name') for n in fp4['frozen_drive']]}")
    print(f"closure_error={fp4['_closure_error']}")
    print(f"expected: 'understand' Drive present and frozen=True: {ok4}")
    print("(tier-5 recursion is well-founded because it bottoms out here -- "
          "domains/frozen_core.py proves no mutation grammar can ever move these nodes)")
    ok_overall = ok_overall and ok4

    # -------------------------------------------------------------------
    _hr("5. SELF-INCLUSION -- the model of the model does not blow up")
    s5, ag5 = boot_core()
    n_v0 = predict_collapse(s5).n_volatile
    r2 = predict_collapse(s5)
    r3 = predict_collapse(s5)
    n_models = len(list(s5.nodes("CollapseModel")))
    fp5 = fixed_points(s5)
    ok5 = (n_models == 3 and r2.n_volatile == n_v0 and r3.n_volatile == n_v0
           and len(fp5["settled_collapse_model"]) == 3)
    print(f"CollapseModel nodes after 3 calls: {n_models}, n_volatile stable at {n_v0}, "
          f"settled_collapse_model fixed points: {len(fp5['settled_collapse_model'])}")
    print(f"expected: 3 models minted, volatility unchanged, all 3 are fixed points: {ok5}")
    ok_overall = ok_overall and ok5

    # -------------------------------------------------------------------
    _hr("6. TRACTABILITY -- predict_collapse on a REAL, fully-booted agent")
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    t0 = time.time()
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    boot_s = time.time() - t0
    n_nodes = len(list(a.s.nodes()))
    print(f"booted a full agent ({n_nodes} nodes) in {boot_s:.2f}s")
    t0 = time.time()
    res6 = predict_collapse(a)
    dt6 = time.time() - t0
    print(f"predict_collapse: converged={res6.converged} n_fixed={res6.n_fixed} "
          f"n_volatile={res6.n_volatile} growth_rate={res6.frontier_growth_rate} "
          f"residual={res6.residual}")
    print(f"predict_collapse runtime: {dt6:.4f}s (self-reported on the node: "
          f"{res6.runtime_s:.4f}s) over {n_nodes} nodes")
    print("STRUCTURAL SHORTCUT: fixed/volatile counts are O(count of a handful of "
          "TRACKED TYPES) via sub.nodes(<type>), never O(total graph size); the "
          "optional forward-look snapshots a FOCUS-RESTRICTED edge closure around "
          "a bounded frontier sample (imagine()'s own focus_hops mechanism), so "
          "per-round rule-matching cost is bounded by the frontier neighbourhood, "
          "not by the graph's total node/edge count -- NOT a full 17k-node K-step "
          "simulation.")

    # -------------------------------------------------------------------
    _hr("SUMMARY")
    print(f"1 (settled converges): {ok1}")
    print(f"2 (axis-runaway predicts divergence -- THE HEADLINE): {ok2}")
    print(f"3 (covered residual predicts convergence -- the control): {ok3}")
    print(f"4 (fixed points include the frozen core): {ok4}")
    print(f"5 (self-inclusion does not blow up): {ok5}")
    print(f"6 (tractable on {n_nodes}-node real graph): {dt6:.4f}s (report only, no gate)")
    print(f"\nALL DISCRIMINATIVE EXPECTATIONS HOLD: {ok_overall}")
    return 0 if ok_overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
