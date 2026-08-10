"""Tests for `domains/collapse_model.py` -- TIER 4 of the collapse-modeling
stack: the graph's model of its OWN total collapse, as one object. Mirrors
the standalone demonstrator `scripts/jabberwock_models_its_collapse.py` in
pytest form; this file is the FAST regression the gate runs (fast fixtures
only -- `substrate.boot_core.boot_core()` + `_ensure_shape_decode_loop`,
never a full 386-seed `load_all_seeds` boot, mirroring the fast-fixture
convention `tests/test_frozen_core_invariant.py` / `tests/test_axis_mint_
novelty.py` already established; the full-graph confirmation lives in the
standalone script).
"""
from __future__ import annotations

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core                           # noqa: E402
from substrate.seed_loader import manifest_for                      # noqa: E402
from domains import reflective_faculty as rf                        # noqa: E402
from domains.collapse_model import (                                # noqa: E402
    CollapseModelResult, fixed_points, predict_collapse, volatile_frontier,
)


def _shape_decode_agent():
    """Fast fixture: boot_core() + the shape_decode_loop seed family, the
    SAME setup tests/test_axis_mint_novelty.py uses."""
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    return s, ag, native


def _fresh_agent_with_autonomy():
    """Fast fixture: CORE_SEEDS + relation_vocabulary + autonomy (the
    frozen Drive) -- no full 386-seed boot, mirrors tests/test_frozen_core_
    invariant.py's `_fresh_agent_with_autonomy`."""
    s, ag = boot_core()
    s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag)
    s._inner.load_seed_manifest(manifest_for("autonomy"), ag)
    return s, ag


def _add_pending_observation(s, ag, key: str):
    obs = s.add_node("Observation", {"signature": [[key, "X"]], "key": [key], "status": "pending"})
    s.add_edge(ag, "observed", obs)
    return obs


# ---------------------------------------------------------------------------
# 1. CONVERGENT: a settled graph (no volatile frontier at all).
# ---------------------------------------------------------------------------
def test_settled_graph_converges_with_low_residual():
    s, ag = boot_core()
    res = predict_collapse(s)
    assert isinstance(res, CollapseModelResult)
    assert res.converged is True
    assert res.residual == 0.0
    assert res.n_volatile == 0
    assert res.frontier_growth_rate <= 0.0
    # the durable CollapseModel trace exists on the live graph
    assert s.has_node(res.model_node)
    assert s.node(res.model_node)["type"] == "CollapseModel"
    assert s.node(res.model_node)["attrs"]["converged"] is True


# ---------------------------------------------------------------------------
# 2. THE HEADLINE: reconstruct the axis-runaway condition (each collapse
#    round mints new unresolved CapabilityAxes -- the exact pathology the
#    live 10-min run showed before the novelty-gate fix, 2996d48a) ->
#    predict_collapse PREDICTS non-convergence BEFORE running it out.
# ---------------------------------------------------------------------------
def test_axis_runaway_condition_predicts_divergence():
    s, ag, native = _shape_decode_agent()
    baseline = sum(len(v) for v in volatile_frontier(s).values())

    # three GENUINELY novel, distinct residuals -- exactly test_axis_mint_
    # novelty.py's own "a genuinely-distinct novel residual still mints"
    # shape, repeated: this is real, unforced novelty, not a bypass of the
    # (real, installed, read-only) dedup guard.
    for i in range(3):
        _add_pending_observation(s, ag, f"zzzrunaway{i}")

    t0 = time.time()
    res = predict_collapse(s, horizon=3, imagine_steps=2)
    runtime = time.time() - t0

    assert res.n_volatile == baseline + 3
    assert res.forward_look_ran is True
    assert res.frontier_growth_rate > 0.0, res.counts_trajectory
    assert res.converged is False
    # monotonically non-decreasing trajectory -- the runaway signature
    traj = res.counts_trajectory
    assert all(traj[i + 1] >= traj[i] for i in range(len(traj) - 1)), traj
    assert traj[-1] > traj[0]
    # tractable: a handful of bounded rounds on a small snapshot, not a
    # full-graph K-step simulation
    assert runtime < 5.0, f"predict_collapse took {runtime}s -- should be sub-second on this fixture"


# ---------------------------------------------------------------------------
# 3. THE CONTROL: a FULLY-COVERED residual (matches a held ShapeSignature
#    exactly) resolves via sd_recognize, never mints -- the SAME forward-
#    look mechanism, run against a shape that the codebook already covers,
#    must predict CONVERGENCE, not divergence. Proves the divergence call
#    above is discriminating on the real rule outcome, not just "we injected
#    nodes so the count went up".
# ---------------------------------------------------------------------------
def test_covered_residual_predicts_convergence():
    s, ag, native = _shape_decode_agent()
    sig = [["zzzcovered", "X"]]
    s.add_node("ShapeSignature", {"name": "zzzcovered_shape", "signature": sig})
    obs = s.add_node("Observation", {"signature": sig, "key": ["zzzcovered"], "status": "pending"})
    s.add_edge(ag, "observed", obs)

    res = predict_collapse(s, horizon=3, imagine_steps=2)
    assert res.forward_look_ran is True
    assert res.frontier_growth_rate <= 0.0, res.counts_trajectory
    assert res.converged is True
    # the frontier actually SHRINKS to zero (recognized, not minted)
    assert res.counts_trajectory[-1] == 0, res.counts_trajectory


# ---------------------------------------------------------------------------
# 4. FIXED POINTS INCLUDE THE FROZEN CORE -- the recursion anchor. The
#    tier-5 recursion (a model of a graph containing a model of that graph)
#    is well-founded because it bottoms out at nodes domains/frozen_core.py
#    proves no mutation grammar can ever move.
# ---------------------------------------------------------------------------
def test_fixed_points_include_the_frozen_core():
    s, ag = _fresh_agent_with_autonomy()
    fp = fixed_points(s)
    assert fp["_closure_error"] is None
    assert fp["frozen_drive"], "the frozen 'understand' Drive must be a fixed point"
    names = {s.node(n)["attrs"].get("name") for n in fp["frozen_drive"]}
    assert "understand" in names
    for n in fp["frozen_drive"]:
        assert s.node(n)["attrs"].get("frozen") is True

    res = predict_collapse(s)
    fixed_ids = {n for k, v in res.fixed_points.items() if not k.startswith("_") for n in v}
    understand = next(n for n in fp["frozen_drive"] if s.node(n)["attrs"].get("name") == "understand")
    assert understand in fixed_ids


# ---------------------------------------------------------------------------
# 5. SELF-INCLUSION: the CollapseModel node is ITSELF in the graph -- a
#    re-run sees the prior CollapseModel and does not blow up (the model of
#    the model converges, no unbounded volatility from its own existence).
# ---------------------------------------------------------------------------
def test_self_inclusion_does_not_add_volatility():
    s, ag = boot_core()
    res1 = predict_collapse(s)
    n_volatile_before = res1.n_volatile
    res2 = predict_collapse(s)
    res3 = predict_collapse(s)

    # CollapseModel nodes exist and accumulate...
    assert len(list(s.nodes("CollapseModel"))) == 3
    # ...but are NEVER counted as volatile (not a tracked type)
    assert res2.n_volatile == n_volatile_before
    assert res3.n_volatile == n_volatile_before

    # ...and each prior CollapseModel becomes a settled fixed point the
    # instant it exists (self-inclusion, well-founded, no explosion)
    fp3 = fixed_points(s)
    assert len(fp3["settled_collapse_model"]) == 3
    assert res1.model_node in fp3["settled_collapse_model"]
    assert res2.model_node in fp3["settled_collapse_model"]


# ---------------------------------------------------------------------------
# 6. TRACTABLE: predict_collapse is CHEAP on the shape-decode fixture with a
#    live forward-look -- not a full-graph K-step simulation.
# ---------------------------------------------------------------------------
def test_predict_collapse_is_cheap_and_reports_its_own_runtime():
    s, ag, native = _shape_decode_agent()
    for i in range(3):
        _add_pending_observation(s, ag, f"zzztiming{i}")
    t0 = time.time()
    res = predict_collapse(s, horizon=3, imagine_steps=2)
    wall = time.time() - t0
    assert res.runtime_s > 0.0
    assert res.runtime_s < 5.0
    assert wall < 5.0


# ---------------------------------------------------------------------------
# 7. API sanity: volatile_frontier / fixed_points are the documented shape,
#    and the minted CollapseModel carries fixed_point/volatile_frontier
#    edges a follow-on agent-authored rule can read.
# ---------------------------------------------------------------------------
def test_collapse_model_edges_and_dict_shapes():
    s, ag, native = _shape_decode_agent()
    for i in range(2):
        _add_pending_observation(s, ag, f"zzzedges{i}")

    vf = volatile_frontier(s)
    assert set(vf.keys()) == {"Observation", "CapabilityAxis", "Impasse", "Goal"}
    assert len(vf["Observation"]) == 2

    fp = fixed_points(s)
    assert {"frozen_drive", "frozen_seed", "frozen_rule", "settled_observation",
            "settled_capability_axis", "settled_impasse", "settled_goal",
            "settled_collapse_model"} <= set(fp.keys())

    res = predict_collapse(s, horizon=1, imagine_steps=1)
    fixed_edges = list(s._inner.neighbours(res.model_node, "fixed_point"))
    volatile_edges = list(s._inner.neighbours(res.model_node, "volatile_frontier"))
    assert len(volatile_edges) == len(res.volatile_sample)
    assert len(fixed_edges) == len(res.fixed_sample)
