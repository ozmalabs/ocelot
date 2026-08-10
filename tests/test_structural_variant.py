"""test_structural_variant — WIDENING THE VARIANT RANGE from THRESHOLD SHIFTS
to STRUCTURAL EDITS.

Companion to tests/test_acting_variant.py (the threshold-shift acting variant
this widens) and tests/test_adoption.py (the adoption loop a structural
variant can also feed) — covering the NEW structural-edit-operator algebra:

  - domains/edit_ops.py — the mechanical (op, target) -> new-rule-JSON
    appliers (`apply_flip_comparison` / `apply_drop_match_edge` /
    `apply_add_match_guard` / `apply_swap_term_leaf`) + the read-only scans
    (`find_comparison_nodes` / `find_attr_keys`) they're built from.
  - `domains.reflective_faculty._ensure_edit_ops` / `_EDIT_OPS` — the
    graph-resident EditOp applicability catalogue.
  - `_compose_structural_variant` — the agent's own TWO-STAGE Argmax (which
    acting rule, via the SAME `_pick_acting_rule` `_compose_acting_variant`
    uses; then which EditOp, scored the same StringIndexOf-Sum overlap way)
    that builds the structural variant, and its wiring into
    `_compose_experiment_rule`'s 'structure' branch (gated by the new
    `structural_edit_variant` RelationCue / composer_dispatch 'structure'
    ComposerCue).

Per CLAUDE.md's discipline: the appliers are tested directly on REAL,
seed-sourced rule JSON (grid_navigation.json's hop_descend_gradient /
mark_visited_footprint — never hand-written rule text); the agent's OP+RULE
PICK is tested by framing concerns and reading back what the agent authored.
"""
from __future__ import annotations

import json
import os
import time

import pytest

from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for
import domains.reflective_faculty as rf
import domains.edit_ops as eo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CONCLUSIONS_SEED = os.path.join(ROOT, "seeds", "experiment_conclusions.json")
_GRID_NAV = json.load(open(os.path.join(ROOT, "seeds", "grid_navigation.json")))
_HOP = next(r for r in _GRID_NAV["rules"] if r["name"] == "hop_descend_gradient")
_FOOTPRINT = next(r for r in _GRID_NAV["rules"] if r["name"] == "mark_visited_footprint")


@pytest.fixture(autouse=True)
def _experiment_conclusions_seed_guard():
    existed = os.path.exists(_CONCLUSIONS_SEED)
    before = open(_CONCLUSIONS_SEED).read() if existed else None
    try:
        yield
    finally:
        if existed:
            with open(_CONCLUSIONS_SEED, "w") as f:
                f.write(before)
        elif os.path.exists(_CONCLUSIONS_SEED):
            os.unlink(_CONCLUSIONS_SEED)


class _Agent:
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def _fresh_agent_with_lexicon() -> _Agent:
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    return ag


def _agent_with_grid_navigation() -> _Agent:
    ag = _fresh_agent_with_lexicon()
    ag.s._inner.load_seed_manifest(manifest_for("grid_navigation"), ag.agent)
    ag.s.add_node("SeedSummary", {"seed_id": "grid_navigation",
                                  "keywords_text": "grid navigation gradient hop descend row col",
                                  "skippable": 1.0})
    return ag


# ---------------------------------------------------------------------------
# 1 — domains.edit_ops appliers: each round-trips on REAL seed-sourced rule
#     JSON — apply -> valid rule dict -> add_rule() accepts it on a scratch
#     substrate; inert cases are honestly reported (None), never fabricated.
# ---------------------------------------------------------------------------
def _scratch():
    s, agent_node = boot_core()
    return s._inner


def test_flip_comparison_round_trips_on_hop_descend_gradient():
    variant = eo.apply_flip_comparison(_HOP, "hop_flip_rt")
    assert variant is not None and variant["name"] == "hop_flip_rt"
    idx = _scratch().add_rule(variant)
    assert isinstance(idx, int)
    # every comparison direction is genuinely flipped, positionally, in the SAME tree shape
    def types_in_order(node, out):
        if isinstance(node, dict):
            if node.get("type") in ("Lt", "Gt", "Lte", "Gte"):
                out.append(node["type"])
            for v in node.values():
                types_in_order(v, out)
        elif isinstance(node, list):
            for v in node:
                types_in_order(v, out)
    orig_order, flip_order = [], []
    types_in_order(_HOP["effects"], orig_order)
    types_in_order(variant["effects"], flip_order)
    flips = {"Lt": "Gt", "Gt": "Lt", "Lte": "Gte", "Gte": "Lte"}
    assert flip_order == [flips[t] for t in orig_order]
    assert orig_order, "sanity: hop_descend_gradient must carry comparison nodes"
    # the ORIGINAL passed in is untouched (deep-copied, not mutated)
    assert _HOP == json.load(open(os.path.join(ROOT, "seeds", "grid_navigation.json")))["rules"][
        [r["name"] for r in _GRID_NAV["rules"]].index("hop_descend_gradient")]


def test_flip_comparison_inert_when_no_comparison_nodes():
    rule = {"name": "no_cmp", "match": [], "where": None,
            "effects": [["set_attr", "g", "chosen_action", {"__term__": {"type": "Lit", "value": "Up"}}]]}
    assert eo.apply_flip_comparison(rule, "no_cmp_flip") is None


def test_swap_term_leaf_round_trips_row_col_on_hop_descend_gradient():
    variant = eo.apply_swap_term_leaf(_HOP, "row", "col", "hop_swap_rt")
    assert variant is not None
    idx = _scratch().add_rule(variant)
    assert isinstance(idx, int)
    keys_before = dict(eo.find_attr_keys(_HOP["effects"]))
    keys_after = dict(eo.find_attr_keys(variant["effects"]))
    assert keys_before.get("row", 0) > 0 and "row" not in keys_after
    assert keys_after.get("col", 0) == keys_before.get("row", 0) + keys_before.get("col", 0)


def test_swap_term_leaf_inert_when_key_absent():
    assert eo.apply_swap_term_leaf(_HOP, "no_such_key_anywhere", "row", "x") is None


def test_drop_match_edge_round_trips_on_mark_visited_footprint():
    assert len(_FOOTPRINT["match"]) == 2          # real, multi-edge match (needed for a non-inert drop)
    variant = eo.apply_drop_match_edge(_FOOTPRINT, 0, "footprint_drop0")
    assert variant is not None
    assert variant["match"] == [_FOOTPRINT["match"][1]]
    idx = _scratch().add_rule(variant)
    assert isinstance(idx, int)


def test_drop_match_edge_inert_on_a_single_edge_match():
    assert len(_HOP["match"]) == 1                 # hop_descend_gradient's real match — only one edge
    assert eo.apply_drop_match_edge(_HOP, 0, "hop_drop0") is None


def test_add_match_guard_round_trips_and_narrows_where():
    variant = eo.apply_add_match_guard(_HOP, "game", "probe_attr", True, "hop_guard_rt")
    assert variant["where"]["type"] == "And"
    assert variant["where"]["items"][-1] == {
        "type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "game"}, "key": "probe_attr"},
        "b": {"type": "Lit", "value": True}}
    idx = _scratch().add_rule(variant)
    assert isinstance(idx, int)
    # a rule whose where was None gets the guard as its WHOLE where (no dangling And)
    bare = {"name": "bare", "match": [["a", "e", "b"]], "where": None, "effects": []}
    variant2 = eo.apply_add_match_guard(bare, "a", "k", 1.0, "bare_guard")
    assert variant2["where"]["type"] == "Eq"


def test_find_comparison_nodes_and_find_attr_keys_are_scoped_reads():
    assert len(eo.find_comparison_nodes(_HOP["effects"])) == 4
    keys = dict(eo.find_attr_keys(_HOP["effects"]))
    assert keys.get("row", 0) == 4 and keys.get("col", 0) == 4


# ---------------------------------------------------------------------------
# 2 — the graph-resident EditOp catalogue: idempotent mint, all four kinds.
# ---------------------------------------------------------------------------
def test_ensure_edit_ops_mints_all_four_kinds_idempotently():
    ag = _fresh_agent_with_lexicon()
    rf._ensure_edit_ops(ag.s)
    kinds1 = sorted(ag.s.node(n)["attrs"]["kind"] for n in ag.s.nodes("EditOp"))
    assert kinds1 == ["add_match_guard", "drop_match_edge", "flip_comparison", "swap_term_leaf"]
    rf._ensure_edit_ops(ag.s)
    kinds2 = sorted(ag.s.node(n)["attrs"]["kind"] for n in ag.s.nodes("EditOp"))
    assert kinds1 == kinds2


# ---------------------------------------------------------------------------
# 3 — the 'structural_edit_variant' RelationCue loads and routes to the
#     'experiment' composer.
# ---------------------------------------------------------------------------
def test_structural_edit_variant_relation_cue_loads():
    ag = _fresh_agent_with_lexicon()
    cues = {at["name"]: at for at in (ag.s.node(n)["attrs"] for n in ag.s.nodes("RelationCue"))}
    assert "structural_edit_variant" in cues
    assert json.loads(cues["structural_edit_variant"]["relation"]) == ["structure", "VARIANT", "of", "ACTING"]


# ---------------------------------------------------------------------------
# 4 — THE DISCRIMINATIVE CHECK: the agent's own two-stage Argmax (which acting
#     rule, which EditOp) picks a DIFFERENT EditOp kind for each of four
#     residual vocabularies naming flip / swap / drop / guard — a genuine
#     pick, never a hand-picked op.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("cue_word,expected_kind", [
    ("flip", "flip_comparison"),
    ("swap", "swap_term_leaf"),
    ("guard", "add_match_guard"),
    # 'drop' is deliberately absent here: it is genuinely INERT on hop_descend_gradient
    # (see test_structural_variant_drop_is_honestly_inert_on_hop_descend_gradient below) —
    # the discriminative property under test for 'drop' is that the pick abstains/fails
    # honestly, not that it silently picks something else.
])
def test_structural_variant_pick_is_discriminative(cue_word, expected_kind):
    ag = _agent_with_grid_navigation()
    ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": [f"sv_{cue_word}"], "induced": 1.0,
        "residual_predicates": ["test", "send", "judge", "structure", "gradient", cue_word],
        "from_observation": 1.0, "source": "concern_induction",
    })
    res = rf.ground_concern(ag, [f"sv_{cue_word}"])
    assert res.get("grounded") is True and res.get("path") == "compose_experiment_rule"
    sv = res.get("structural_variant")
    assert sv is not None and sv.get("built") is True, sv
    assert sv.get("kind") == expected_kind
    assert sv.get("removed_rule") == "hop_descend_gradient"
    print(f"structural_variant[{cue_word}] = {json.dumps(sv, default=str)}")   # Gate B: 'print it'


def test_structural_variant_drop_is_honestly_inert_on_hop_descend_gradient():
    ag = _agent_with_grid_navigation()
    ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["sv_drop"], "induced": 1.0,
        "residual_predicates": ["test", "send", "judge", "structure", "gradient", "drop"],
        "from_observation": 1.0, "source": "concern_induction",
    })
    res = rf.ground_concern(ag, ["sv_drop"])
    sv = res.get("structural_variant")
    assert sv is not None
    assert sv.get("built") is False
    assert sv.get("kind") == "drop_match_edge"
    assert "INERT" in sv.get("wall", "")


def test_structural_variant_abstains_without_genuine_rule_overlap():
    ag = _fresh_agent_with_lexicon()          # no grid_navigation loaded at all
    ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["sv_none"], "induced": 1.0,
        "residual_predicates": ["test", "send", "judge", "structure", "flip"],
        "from_observation": 1.0, "source": "concern_induction",
    })
    res = rf.ground_concern(ag, ["sv_none"])
    sv = res.get("structural_variant")
    assert sv is not None and sv.get("built") is False
    assert "wall" in sv


# ---------------------------------------------------------------------------
# 5 — the structural variant is embedded into the mint rule's SeedDelta
#     (remove_rules + add_rules + edit_op_kind), exactly the acting-variant
#     shape but for a structural edit; 'structure' takes priority over
#     'gradient' when both ground on the same concern (never two conflicting
#     replacements of the same rule).
# ---------------------------------------------------------------------------
def test_structural_variant_embedded_into_mint_delta():
    ag = _agent_with_grid_navigation()
    ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["emb_flip"], "induced": 1.0,
        "residual_predicates": ["test", "send", "judge", "structure", "gradient", "flip"],
        "from_observation": 1.0, "source": "concern_induction",
    })
    res = rf.ground_concern(ag, ["emb_flip"])
    mint = {r["name"]: r for r in res["rules"]}["author_experiment_from_residual_emb_flip"]
    delta_attrs = mint["effects"][1][3]
    assert delta_attrs.get("remove_rules") == json.dumps(["hop_descend_gradient"])
    assert delta_attrs.get("act_rule_varied") == "hop_descend_gradient"
    assert delta_attrs.get("edit_op_kind") == "flip_comparison"
    add_rules = json.loads(delta_attrs["add_rules"])
    assert len(add_rules) == 1
    assert add_rules[0]["name"].startswith("hop_descend_gradient_structvariant_")


def test_structure_takes_priority_over_gradient_when_both_ground():
    ag = _agent_with_grid_navigation()
    ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["both_sg"], "induced": 1.0,
        "residual_predicates": ["test", "send", "judge", "structure", "gradient", "swap"],
        "from_observation": 1.0, "source": "concern_induction",
    })
    res = rf.ground_concern(ag, ["both_sg"])
    assert res.get("acting_variant") is None          # the 'gradient' (threshold-shift) path did NOT build
    assert res.get("structural_variant", {}).get("built") is True
    mint = {r["name"]: r for r in res["rules"]}["author_experiment_from_residual_both_sg"]
    delta_attrs = mint["effects"][1][3]
    add_rules = json.loads(delta_attrs["add_rules"])
    assert len(add_rules) == 1                        # exactly ONE variant, not two conflicting ones
    assert add_rules[0]["name"].startswith("hop_descend_gradient_structvariant_")


# ---------------------------------------------------------------------------
# 6 — SLOW, true end-to-end: a dispatched CONTROL vs. a dispatched STRUCTURAL-
#     VARIANT child on the same offline navigate game produce measurably
#     different action streams — the same discriminative shape
#     tests/test_acting_variant.py's Part B uses for the threshold-shift
#     variant, here for a genuine structural edit (flip_comparison).
# ---------------------------------------------------------------------------
@pytest.mark.slow
def test_full_structural_variant_loop_offline(tmp_path):
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains.experiment_dispatch import mint_experiment, scan_and_dispatch, _INFLIGHT
    from worlds.arc import ArcWorld
    from arc3_env import NavigateEnv

    _INFLIGHT.clear()
    b = WorldAdapter(seeds=())
    load_all_seeds(b)
    Sb, Ib = b.s, b.inner

    ind_b = rf.induce_concern(b, [["test", "H", "about", "S"], ["judge", "T", "by", "O"],
                                 ["structure", "V", "of", "A"], ["gradient", "V", "of", "A"],
                                 ["flip", "OP", "of", "COMPARISON"]],
                              name_hint="structural_behavioural_concern")
    g_b = rf.ground_concern(b, [ind_b["capability_key"]])
    sv_b = g_b.get("structural_variant")
    assert sv_b.get("built") is True and sv_b.get("kind") == "flip_comparison"
    assert sv_b.get("removed_rule") == "hop_descend_gradient"

    exp_c = mint_experiment(b, "control: same acting rules as the parent", "navigate",
                            skip_seeds=[], add_rules=[], remove_rules=[])
    exp_v = mint_experiment(b, "structural variant: hop_descend_gradient's comparisons flipped",
                            "navigate", skip_seeds=[], add_rules=[sv_b["rule"]],
                            remove_rules=[sv_b["removed_rule"]])
    runs_dir = tmp_path / "runs"
    t0 = time.time()
    while time.time() - t0 < 90:
        scan_and_dispatch(b, runs_dir)
        sc = Sb.node(exp_c)["attrs"].get("status")
        sv_status = Sb.node(exp_v)["attrs"].get("status")
        if sc not in ("requested", "running") and sv_status not in ("requested", "running"):
            break
        time.sleep(0.5)
    assert Sb.node(exp_c)["attrs"].get("status") == "done"
    assert Sb.node(exp_v)["attrs"].get("status") == "done"

    run_dir_c = Sb.node(exp_c)["attrs"]["run_dir"]
    run_dir_v = Sb.node(exp_v)["attrs"]["run_dir"]
    result_c = json.loads(open(os.path.join(run_dir_c, "result.json")).read())
    result_v = json.loads(open(os.path.join(run_dir_v, "result.json")).read())
    assert result_c.get("removed_rules") == []
    assert result_v.get("removed_rules") == ["hop_descend_gradient"]

    def _actions(run_dir):
        p = os.path.join(run_dir, "trace.jsonl")
        return [json.loads(l)["action"] for l in open(p) if l.strip()]

    actions_c = _actions(run_dir_c)
    actions_v = _actions(run_dir_v)
    n_common = min(len(actions_c), len(actions_v))
    n_diff = sum(1 for i in range(n_common) if actions_c[i] != actions_v[i])
    assert actions_c != actions_v, f"control and structural-variant actions never diverged: {actions_c} vs {actions_v}"
    assert n_diff >= 1
