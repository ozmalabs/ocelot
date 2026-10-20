"""P3.A6/P3.A7 executor gates for bounded, budgeted tolerance ladders."""
from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for
from domains import reflective_faculty as rf
from tests.test_geninfer_grain_migrated import BLOCK, DT3, JIT, _rot
from tests.test_gen_infer_migrated import BASE, SHEAR_A, _lin

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = {"conflict_margin", "minimum_confidence", "settle_tolerance", "shape_match_tolerance", "basin_threshold"}


def _install(*, enabled=True, budget_enabled=False, remaining=16.0):
    s, agent = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, agent)
    native.load_seed_manifest(manifest_for("thinking_budget"), agent)
    native.load_seed_manifest(manifest_for("extended_thinking"), agent)
    mode = s.nodes("NetworkModeState")[0]
    s.set_attr(mode, "epoch", 1.0)
    s.set_attr(agent, "codebook_epoch", 0.0)
    policy = s.nodes("ExtendedThinkingPolicy")[0]
    s.set_attr(policy, "enabled", 1.0 if enabled else 0.0)
    budget = s.nodes("ThinkingBudget")[0]
    s.set_attr(budget, "enabled", 1.0 if budget_enabled else 0.0)
    s.set_attr(budget, "remaining", float(remaining))
    s.set_attr(budget, "refill_per_epoch", 0.0)
    s.set_attr(budget, "last_refill_epoch", 1.0)
    return s, agent, native


def _observation(s, agent, signature, key, dim_types=DT3):
    obs = s.add_node("Observation", {
        "signature": signature, "key": key, "status": "decoded",
        "residual": signature, "decoded_epoch": s.node(agent)["attrs"].get("codebook_epoch", 0.0), "dim_types": dim_types,
    })
    try:
        s._inner.add_edge_unchecked(agent, "observed", obs, {})
    except TypeError:
        s._inner.add_edge_unchecked(agent, "observed", obs)
    return obs


def _node_attrs(s, node_type):
    return [s.node(node)["attrs"] for node in s.nodes(node_type)]


def _fixture_a(s):
    s.add_node("ShapeSignature", {
        "name": "block", "signature": json.dumps(BLOCK), "kind": "faculty",
        "faculty": "block", "dim_types": DT3,
    })
    return _rot(JIT)


def _fixture_b(s):
    s.add_node("ShapeSignature", {
        "name": "base_L", "signature": json.dumps(BASE), "kind": "faculty",
        "faculty": "base_L", "dim_types": ["pred", "coord:r", "coord:c", "val"],
    })
    return _lin(SHEAR_A)


def test_disabled_has_no_extended_thinking_nodes_and_keeps_minted_status():
    s, agent, native = _install(enabled=False)
    sig = _fixture_a(s)
    obs = _observation(s, agent, sig, ["disabled"])
    native.run_rules()
    assert s.node(obs)["attrs"]["status"] == "minted"
    assert _node_attrs(s, "ExtendedThinkingEpisode") == []
    assert _node_attrs(s, "ExtendedThinkingStepRequest") == []
    assert _node_attrs(s, "ToleranceRelaxLease") == []


def test_dim_grain_hit_is_funded_provenanced_and_restored():
    s, agent, native = _install()
    sig = _fixture_a(s)
    obs = _observation(s, agent, sig, ["grain"])
    native.run_rules()
    attrs = s.node(obs)["attrs"]
    assert attrs["status"] == "recognized_transformed" and attrs["dim_grain"] == 1
    assert attrs["accepted_at_relaxed"] == "dim_grain_ladder"
    assert attrs["accepted_rung"] == 1
    assert _node_attrs(s, "ExtendedThinkingEpisode")[0]["steps"] == 1
    assert s.node(agent)["attrs"].get("dim_grains") in (None, [0], (0,))
    assert [x["status"] for x in _node_attrs(s, "ToleranceRelaxLease")] == ["restored"]
    assert any(x.get("superseded_by_extended_thinking") == 1 for x in _node_attrs(s, "CapabilityAxis"))


def test_scrambled_control_exhausts_both_ladders_with_defaults_restored():
    s, agent, native = _install()
    _fixture_a(s)
    coords = random.Random(811).sample([(r, c) for r in range(8) for c in range(8)], len(JIT))
    sig = [["cell", r, c] for r, c in coords]
    obs = _observation(s, agent, sig, ["scrambled"])
    native.run_rules()
    episodes = [x for x in _node_attrs(s, "ExtendedThinkingEpisode")]
    assert [x["ladder_name"] for x in episodes] == ["dim_grain_ladder", "gen_infer_ladder"]
    assert [x["outcome"] for x in episodes] == ["exhausted", "exhausted"]
    assert [x["steps"] for x in episodes] == [2, 1]
    assert s.node(obs)["attrs"].get("dim_explained") != 1
    assert s.node(obs)["attrs"].get("gen_explained") != 1
    assert s.node(agent)["attrs"].get("dim_grains") in (None, [0], (0,))
    assert s.node(agent)["attrs"].get("gen_infer_enabled") in (None, 0.0)


def test_gen_infer_hit_follows_dim_exhaustion_and_restores_default():
    s, agent, native = _install()
    sig = _fixture_b(s)
    obs = _observation(s, agent, sig, ["shear"], ["pred", "coord:r", "coord:c", "val"])
    native.run_rules()
    episodes = _node_attrs(s, "ExtendedThinkingEpisode")
    assert [x["ladder_name"] for x in episodes] == ["dim_grain_ladder", "gen_infer_ladder"]
    assert [x["outcome"] for x in episodes] == ["exhausted", "hit"]
    assert episodes[1]["steps"] == 1
    assert s.node(obs)["attrs"]["status"] == "recognized_transformed"
    assert any(s.node(n)["type"] == "DimensionGenerator" and s.node(n)["attrs"].get("name", "").startswith("genlin_") for n in s.nodes())
    assert s.node(agent)["attrs"].get("gen_infer_enabled") in (None, 0.0)


def test_budget_denial_does_not_write_grain():
    s, agent, native = _install(budget_enabled=True, remaining=0.0)
    sig = _fixture_a(s)
    obs = _observation(s, agent, sig, ["denied"])
    native.run_rules()
    assert _node_attrs(s, "ExtendedThinkingEpisode")[0]["outcome"] == "denied"
    assert s.node(agent)["attrs"].get("dim_grains") is None
    assert s.node(obs)["attrs"]["status"] == "minted"


def test_generated_seed_writes_only_the_two_allowlisted_ladders():
    seed = json.loads((ROOT / "seeds" / "extended_thinking.json").read_text())
    writes = {effect[2] for rule in seed["rules"] for effect in rule.get("effects", []) if effect[0] == "set_attr"}
    assert not (writes & FORBIDDEN)
    assert {"dim_grains", "gen_infer_enabled"} <= writes


def test_settled_episode_is_a_fixpoint():
    s, agent, native = _install()
    sig = _fixture_a(s)
    obs = _observation(s, agent, sig, ["fixed"])
    native.run_rules()
    before = len(list(s.nodes()))
    native.run_rules()
    assert len(list(s.nodes())) == before
    assert s.node(obs)["attrs"]["accepted_at_relaxed"] == "dim_grain_ladder"


def test_generator_reproduces_committed_seed_exactly():
    import importlib.util
    spec = importlib.util.spec_from_file_location("gen_extended_thinking_seed", ROOT / "scripts" / "gen_extended_thinking_seed.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    expected = json.dumps(module.build(), indent=1) + "\n"
    assert (ROOT / "seeds" / "extended_thinking.json").read_text() == expected


def test_grain_cache_second_encounter_starts_at_winner_and_uses_one_step():
    s, agent, native = _install()
    sig = _fixture_a(s)
    first = _observation(s, agent, sig, ["repeat"])
    native.run_rules()
    second = _observation(s, agent, sig, ["repeat"])
    native.run_rules()
    episodes = _node_attrs(s, "ExtendedThinkingEpisode")
    second_ep = next(x for x in episodes if x.get("opened_epoch") == 1.0 and x.get("from_cache") == 1)
    assert second_ep["outcome"] == "hit"
    assert second_ep["steps"] == 1
    assert second_ep["rung_index"] == 1
    cache = _node_attrs(s, "ExtendedThinkingCacheEntry")
    assert len(cache) == 1 and cache[0]["hits"] == 1
    assert s.node(first)["attrs"]["status"] == s.node(second)["attrs"]["status"] == "recognized_transformed"


def test_cached_rung_that_is_too_fine_continues_within_ladder_bound():
    s, agent, native = _install()
    sig = _fixture_a(s)
    _observation(s, agent, sig, ["shared"])
    native.run_rules()
    coords = random.Random(811).sample([(r, c) for r in range(8) for c in range(8)], len(JIT))
    control = [["cell", r, c] for r, c in coords]
    obs = _observation(s, agent, control, ["shared"])
    native.run_rules()
    ep = next(x for x in _node_attrs(s, "ExtendedThinkingEpisode") if x.get("from_cache") == 1)
    assert ep["outcome"] == "exhausted"
    assert ep["steps"] == 2
    assert ep["steps"] <= 2
    assert s.node(obs)["attrs"].get("accepted_at_relaxed") is None


def test_gen_infer_minted_generator_is_the_second_encounter_cache():
    s, agent, native = _install()
    sig = _fixture_b(s)
    _observation(s, agent, sig, ["shear"], ["pred", "coord:r", "coord:c", "val"])
    native.run_rules()
    before = len(_node_attrs(s, "ExtendedThinkingEpisode"))
    second = _observation(s, agent, sig, ["shear-again"], ["pred", "coord:r", "coord:c", "val"])
    native.run_rules()
    assert s.node(second)["attrs"]["status"] == "recognized_transformed"
    assert len(_node_attrs(s, "ExtendedThinkingEpisode")) == before
