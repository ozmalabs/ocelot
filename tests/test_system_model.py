"""Tests for `domains/system_model.py` -- the generalisation of TIER 4
(`domains/collapse_model.py`'s `predict_collapse`) to an ARBITRARY TARGET
SYSTEM: self, a subgraph, a foreign snapshot, or the agent's own
collapse-modelling machinery (TIER 5, `target="meta"`).

Fast fixtures only -- `substrate.boot_core.boot_core()` + (where needed)
`_ensure_shape_decode_loop` / the `autonomy` seed, never a full 386-seed
`load_all_seeds` boot, mirroring `tests/test_collapse_model.py`'s own
convention.
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

import substrate_rs as srs                                          # noqa: E402
from substrate.boot_core import boot_core                           # noqa: E402
from substrate.seed_loader import manifest_for                      # noqa: E402
from domains import reflective_faculty as rf                        # noqa: E402
from domains.collapse_model import predict_collapse                 # noqa: E402
from domains.system_model import (                                  # noqa: E402
    META, SELF, SystemModelResult, model_system,
)


def _shape_decode_agent():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    return s, ag, native


def _fresh_agent_with_autonomy():
    s, ag = boot_core()
    s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag)
    s._inner.load_seed_manifest(manifest_for("autonomy"), ag)
    return s, ag


def _add_pending_observation(s, ag, key: str):
    obs = s.add_node("Observation", {"signature": [[key, "X"]], "key": [key], "status": "pending"})
    s.add_edge(ag, "observed", obs)
    return obs


def _build_convergent_foreign_graph() -> dict:
    """A tiny foreign system with its OWN graph-resident dynamics: a Rule
    that fires EXACTLY ONCE (gated on Target.done<0.5, sets done=1.0, then
    its own `where` clause vetoes further matches) -- a genuine fixed point,
    not a proxy."""
    s = srs.Substrate()
    a = s.add_node("Anchor", {})
    b = s.add_node("Target", {"done": 0.0})
    s._inner.add_edge_unchecked(a, "trig", b)
    s.add_node("Rule", {
        "id": "converge_once",
        "match": [["a", "trig", "b"]],
        "where": {"type": "Lt", "a": {"type": "Attr", "node": {"type": "Var", "name": "b"}, "key": "done"},
                  "b": {"type": "Lit", "value": 0.5}},
        "effect": [["set_attr", "b", "done", 1.0]],
    })
    return s._inner.graph_to_dict()


def _build_divergent_foreign_graph() -> dict:
    """A tiny foreign system whose Rule is UNGATED and matches its own
    persistent trigger edge every pass -- each firing mints a fresh node, so
    `run_graph_rules`'s inner fixed-point loop never reaches a fixed point
    within the step budget (the exact pathology `tests/test_rule_minting_
    dialect.py`'s `test_string_concat_surface_coerces_and_mints` docstring
    documents for an ungated composer)."""
    s = srs.Substrate()
    a = s.add_node("Anchor", {})
    b = s.add_node("Target", {})
    s._inner.add_edge_unchecked(a, "trig", b)
    s.add_node("Rule", {
        "id": "diverge_always",
        "match": [["a", "trig", "b"]],
        "where": {"type": "Lit", "value": True},
        "effect": [["add_node", "x", "Thing", {}]],
    })
    return s._inner.graph_to_dict()


# ===========================================================================
# 1. SELF -- parity with predict_collapse, by construction.
# ===========================================================================
def test_self_default_target_is_settled_and_converges():
    s, ag = boot_core()
    res = model_system(s)  # target defaults to SELF
    assert isinstance(res, SystemModelResult)
    assert res.target_kind == "self"
    assert res.converged is True
    assert res.residual == 0.0
    assert res.n_volatile == 0
    assert s.has_node(res.model_node)
    assert s.node(res.model_node)["type"] == "SystemModel"


def test_self_parity_with_predict_collapse():
    """model_system(target=SELF) must agree EXACTLY with predict_collapse on
    an identically-constructed graph -- the generalisation must not change
    self-modelling. Uses two SEPARATE agent instances (rather than calling
    both on the same graph) because predict_collapse itself mints a
    CollapseModel node, which would otherwise make the second call's graph
    state differ from the first's."""
    def _mk():
        s, ag, _native = _shape_decode_agent()
        for i in range(3):
            _add_pending_observation(s, ag, f"zzzparity{i}")
        return s

    s_a = _mk()
    cm = predict_collapse(s_a, horizon=2, imagine_steps=2)

    s_b = _mk()
    sm = model_system(s_b, target=SELF, horizon=2, imagine_steps=2)

    assert sm.target_kind == "self"
    assert sm.converged == cm.converged
    assert sm.residual == cm.residual
    assert sm.n_fixed == cm.n_fixed
    assert sm.n_volatile == cm.n_volatile
    assert sm.frontier_growth_rate == cm.frontier_growth_rate
    assert sm.counts_trajectory == cm.counts_trajectory
    assert sm.forward_look_ran == cm.forward_look_ran


# ===========================================================================
# 2. OTHER -- the headline generalisation: a genuinely FOREIGN system,
#    discriminative (convergent vs divergent), grounded via observation.
# ===========================================================================
def test_other_convergent_foreign_system_predicts_convergence():
    s, ag = boot_core()
    graph = _build_convergent_foreign_graph()
    res = model_system(s, target={"kind": "foreign_snapshot", "graph": graph},
                        horizon=3, imagine_steps=3)
    assert res.target_kind == "foreign_snapshot"
    assert res.converged is True
    assert res.frontier_growth_rate <= 0.0
    # grounded in the agent's OWN observation, not the foreign system's ground
    assert res.grounded is True
    assert "SensorAnchor" in res.grounding.get("anchors", [])
    assert s.node(res.model_node)["attrs"].get("grounded") is True


def test_other_divergent_foreign_system_predicts_divergence():
    s, ag = boot_core()
    graph = _build_divergent_foreign_graph()
    res = model_system(s, target={"kind": "foreign_snapshot", "graph": graph},
                        horizon=3, imagine_steps=3)
    assert res.target_kind == "foreign_snapshot"
    assert res.converged is False
    assert res.frontier_growth_rate > 0.0, res.counts_trajectory
    assert res.grounded is True


def test_other_is_discriminative_not_vacuous():
    """The SAME faculty, pointed at two different foreign systems, must
    disagree -- proving section 2's calls discriminate on the real dynamics,
    not on some constant "foreign systems always look X" bias."""
    s1, _ = boot_core()
    conv = model_system(s1, target={"kind": "foreign_snapshot",
                                     "graph": _build_convergent_foreign_graph()},
                         horizon=3, imagine_steps=3)
    s2, _ = boot_core()
    div = model_system(s2, target={"kind": "foreign_snapshot",
                                    "graph": _build_divergent_foreign_graph()},
                        horizon=3, imagine_steps=3)
    assert conv.converged is True
    assert div.converged is False
    assert conv.converged != div.converged


def test_other_grounding_is_observation_not_foreign_internal_state():
    """The grounding anchor is the agent's OWN SensorAnchor (an observation
    edge on the LIVE graph) -- never anything from the foreign snapshot's own
    node/edge set (which the live agent never even ingests as permanent
    structure)."""
    s, ag = boot_core()
    graph = _build_convergent_foreign_graph()
    res = model_system(s, target={"kind": "foreign_snapshot", "graph": graph})
    anchors_before = len(list(s.nodes("SensorAnchor")))
    res2 = model_system(s, target={"kind": "foreign_snapshot", "graph": graph})
    anchors_after = len(list(s.nodes("SensorAnchor")))
    # idempotent singleton anchor -- re-observing another foreign system does
    # not mint a second SensorAnchor
    assert anchors_before == anchors_after == 1
    assert res.grounded and res2.grounded
    # the foreign graph's own node ids never become live nodes: the
    # SystemModel's fixed/volatile sample is reported as foreign DATA
    # (an attr), never as live graph edges (see mint_node_edges=False in
    # domains.system_model._model_foreign_snapshot)
    assert s.node(res.model_node)["attrs"].get("target_kind") == "foreign_snapshot"
    assert "fixed_sample_foreign_ids" in s.node(res.model_node)["attrs"] or \
           "volatile_sample_foreign_ids" in s.node(res.model_node)["attrs"]


# ===========================================================================
# 3. SUBGRAPH -- a bounded piece of the agent's OWN live graph.
# ===========================================================================
def test_subgraph_target_by_types_is_not_grounded_via_sensor():
    s, ag, native = _shape_decode_agent()
    for i in range(2):
        _add_pending_observation(s, ag, f"zzzsub{i}")
    res = model_system(s, target={"kind": "subgraph", "types": ["Observation"]},
                        horizon=2, imagine_steps=2)
    assert res.target_kind == "subgraph"
    assert res.node_count >= 2
    # subgraph is part of the agent's OWN graph (self-referential) -- not the
    # OTHER-system observation-grounding case
    assert res.grounded is False


def test_subgraph_target_by_root_and_hops_resolves_a_bounded_closure():
    s, ag, native = _shape_decode_agent()
    obs = _add_pending_observation(s, ag, "zzzroot0")
    res = model_system(s, target={"kind": "subgraph", "root": obs, "hops": 1},
                        horizon=1, imagine_steps=1)
    assert res.target_kind == "subgraph"
    assert res.node_count >= 1


# ===========================================================================
# 4. META -- TIER 5: model of the agent's own modelling machinery. Prove the
#    RECURSION TERMINATES: fixed points include the frozen core, and
#    n_volatile does not grow across the tower (tier4 -> tier5 -> tier6).
# ===========================================================================
def test_meta_target_fixed_points_include_frozen_core():
    s, ag = _fresh_agent_with_autonomy()
    res = model_system(s, target=META)
    assert res.target_kind == "meta"
    assert res.fixed_points.get("frozen_drive"), "the frozen 'understand' Drive must be a fixed point"
    names = {s.node(n)["attrs"].get("name") for n in res.fixed_points["frozen_drive"]}
    assert "understand" in names


def test_meta_tower_does_not_grow_n_volatile_and_self_includes():
    s, ag = _fresh_agent_with_autonomy()

    tier4 = predict_collapse(s)             # TIER 4: model of the graph
    tier5 = model_system(s, target=META)    # TIER 5: model of tier-4's machinery
    tier6 = model_system(s, target=META)    # model THAT -- the would-be tier 6

    # the tower is CONVERGENT, not an explosion: n_volatile is identical at
    # every level (tier 5/6 reuse tier 4's whole-graph accounting verbatim
    # and add ZERO new tracked-volatile types of their own)
    assert tier5.n_volatile == tier4.n_volatile
    assert tier6.n_volatile == tier5.n_volatile

    # fixed points anchor the tower: tier 6 must include tier 5's own
    # SystemModel node as a settled (self-inclusion) fixed point -- it froze
    # the instant tier 5 minted it
    assert tier5.model_node in tier6.fixed_points.get("settled_system_model", [])
    # ...and the frozen core is present at every level of the tower
    assert tier5.fixed_points.get("frozen_drive")
    assert tier6.fixed_points.get("frozen_drive")

    # n_fixed only ever grows (each frozen snapshot adds itself) -- never
    # shrinks, and never grows by more than the self-inclusion delta
    assert tier6.n_fixed >= tier5.n_fixed >= tier4.n_fixed


def test_meta_models_edges_point_at_the_collapse_model_it_describes():
    s, ag = boot_core()
    cm = predict_collapse(s)
    sm = model_system(s, target=META)
    modeled = list(s._inner.neighbours(sm.model_node, "models"))
    assert cm.model_node in modeled


# ===========================================================================
# 5. TRACTABLE -- model_system stays cheap: structural / target-bounded, not
#    a full re-sim per target.
# ===========================================================================
def test_model_system_is_cheap_for_every_target_kind():
    s, ag, native = _shape_decode_agent()
    for i in range(3):
        _add_pending_observation(s, ag, f"zzztiming{i}")

    t0 = time.time()
    r_self = model_system(s, target=SELF, horizon=3, imagine_steps=2)
    dt_self = time.time() - t0
    assert dt_self < 5.0
    assert r_self.runtime_s < 5.0

    t0 = time.time()
    r_meta = model_system(s, target=META, horizon=3, imagine_steps=2)
    dt_meta = time.time() - t0
    assert dt_meta < 5.0
    assert r_meta.runtime_s < 5.0

    t0 = time.time()
    r_sub = model_system(s, target={"kind": "subgraph", "types": ["Observation"]},
                          horizon=2, imagine_steps=2)
    dt_sub = time.time() - t0
    assert dt_sub < 5.0
    assert r_sub.runtime_s < 5.0

    t0 = time.time()
    r_other = model_system(s, target={"kind": "foreign_snapshot",
                                       "graph": _build_divergent_foreign_graph()},
                            horizon=3, imagine_steps=3)
    dt_other = time.time() - t0
    assert dt_other < 5.0
    assert r_other.runtime_s < 5.0


# ===========================================================================
# 6. API sanity: the minted SystemModel carries the documented edges/attrs.
# ===========================================================================
def test_system_model_edges_and_dict_shapes():
    s, ag, native = _shape_decode_agent()
    for i in range(2):
        _add_pending_observation(s, ag, f"zzzedges{i}")

    res = model_system(s, target=SELF, horizon=1, imagine_steps=1)
    fixed_edges = list(s._inner.neighbours(res.model_node, "fixed_point"))
    volatile_edges = list(s._inner.neighbours(res.model_node, "volatile_frontier"))
    assert len(volatile_edges) == len(res.volatile_sample)
    assert len(fixed_edges) == len(res.fixed_sample)
    attrs = s.node(res.model_node)["attrs"]
    assert attrs.get("target_kind") == "self"
    assert attrs.get("target_id") == "self"


def test_invalid_target_raises():
    s, ag = boot_core()
    with pytest.raises(ValueError):
        model_system(s, target={"kind": "not_a_real_kind"})
