"""test_acting_variant — closing the "variant modifies judging not ACTING
logic" residual named at c0288920.

Companion to tests/test_self_delta.py (the SeedDelta.skip_seeds / judge-variant
machinery) and tests/test_experiment_composer.py (the mint/judge rule composer)
— covering the NEW acting-variant machinery added alongside it: SeedDelta's
`remove_rules` (mechanical tombstoning at child boot, scripts/arc_child_run.py),
`RuleSummary` provenance for chosen_action-writing rules
(`domains.reflective_faculty._ensure_acting_rule_provenance`), the
threshold-scan/shift mechanics (`_find_threshold_lits` / `_shift_rule_thresholds`),
and the agent's own selection Term (`_compose_acting_variant`, gated by the
'gradient' relation, seeds/relation_vocabulary.json's `vary_acting_gradient`
cue / seeds/composer_dispatch.json's existing test/judge routing to the
'experiment' composer — no new ComposerCue needed, see
`_compose_experiment_rule`'s module docstring).

Per CLAUDE.md's discipline: these tests never hand-install the acting-variant
rule text — they frame concerns and read back what the agent authored, or
they call the mechanical helpers directly with real, seed-sourced rule JSON
(never a hand-crafted rule shape) to test the STRUCTURAL SUBSTITUTION alone.
"""
from __future__ import annotations

import copy
import json
import os
import time

import pytest

from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for
import domains.reflective_faculty as rf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CONCLUSIONS_SEED = os.path.join(ROOT, "seeds", "experiment_conclusions.json")


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
    """Minimal duck-typed agent wrapper — identical shape to
    tests/test_self_delta.py's own `_Agent` (harness glue only)."""
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
    """A lexicon-only agent that ALSO has grid_navigation.json loaded (so its real,
    live hop_descend_gradient rule exists for _ensure_acting_rule_provenance /
    _compose_acting_variant to find via export_rules() — never a hand-written stub)."""
    ag = _fresh_agent_with_lexicon()
    ag.s._inner.load_seed_manifest(manifest_for("grid_navigation"), ag.agent)
    return ag


_ACTING_OBS = [
    ["test", "HYPOTHESIS", "about", "SELF"],
    ["send", "VARIANT", "to", "WORLD"],
    ["judge", "TRIAL", "by", "OUTCOME"],
    ["gradient", "VARIANT", "of", "ACTING"],
]


# ---------------------------------------------------------------------------
# 1 — the new 'vary_acting_gradient' RelationCue loads with the expected relation.
# ---------------------------------------------------------------------------
def test_gradient_relation_cue_loads():
    ag = _fresh_agent_with_lexicon()
    cues = {at["name"]: at for at in (ag.s.node(n)["attrs"] for n in ag.s.nodes("RelationCue"))}
    assert "vary_acting_gradient" in cues
    assert json.loads(cues["vary_acting_gradient"]["relation"]) == ["gradient", "VARIANT", "of", "ACTING"]


# ---------------------------------------------------------------------------
# 2 — the mechanical threshold-scan/shift helpers, exercised on the REAL
#     hop_descend_gradient rule text (pulled from the seed manifest, never
#     hand-written) — the structural substitution alone, no agent involved.
# ---------------------------------------------------------------------------
def _real_hop_descend_gradient_rule() -> dict:
    d = json.load(open(os.path.join(ROOT, "seeds", "grid_navigation.json")))
    return next(r for r in d["rules"] if r["name"] == "hop_descend_gradient")


def test_find_threshold_lits_finds_exactly_the_four_direction_gates():
    rule = _real_hop_descend_gradient_rule()
    nodes = rf._find_threshold_lits(rule["effects"])
    assert len(nodes) == 4
    assert sorted(n["type"] for n in nodes) == ["Gt", "Gt", "Lt", "Lt"]
    assert all(n["b"] == {"type": "Lit", "value": 0} for n in nodes)


def test_shift_rule_thresholds_shifts_only_those_four_and_renames():
    rule = _real_hop_descend_gradient_rule()
    original = copy.deepcopy(rule)
    variant = rf._shift_rule_thresholds(rule, 5.0, "hop_descend_gradient_variant_t")
    assert variant["name"] == "hop_descend_gradient_variant_t"
    shifted = rf._find_threshold_lits(variant["effects"])
    assert sorted(n["b"]["value"] for n in shifted) == [-5.0, -5.0, 5.0, 5.0]
    # the original rule dict passed in must be untouched (deep-copied, not mutated)
    assert rule == original
    # everything else about the rule (match/where) is byte-identical
    assert variant["match"] == rule["match"]
    assert variant["where"] == rule["where"]


def test_shift_rule_thresholds_no_op_on_a_rule_with_no_thresholds():
    rule = {"name": "no_threshold_rule", "match": [], "where": None,
            "effects": [["set_attr", "g", "chosen_action", {"__term__": {"type": "Attr", "node": "n", "key": "name"}}]]}
    variant = rf._shift_rule_thresholds(rule, 3.0, "no_threshold_rule_variant")
    assert rf._find_threshold_lits(variant["effects"]) == []
    assert variant["name"] == "no_threshold_rule_variant"


# ---------------------------------------------------------------------------
# 3 — provenance: _ensure_acting_rule_provenance mirrors ONLY rules that are
#     ACTIVE and write chosen_action, with the right shift_count/shiftable,
#     and is idempotent.
# ---------------------------------------------------------------------------
def test_ensure_acting_rule_provenance_mirrors_hop_descend_gradient():
    ag = _agent_with_grid_navigation()
    rf._ensure_acting_rule_provenance(ag.s, ag.inner)
    by_name = {ag.s.node(n)["attrs"]["name"]: ag.s.node(n)["attrs"] for n in ag.s.nodes("RuleSummary")}
    assert "hop_descend_gradient" in by_name
    at = by_name["hop_descend_gradient"]
    assert at["writes_chosen_action"] == 1.0
    assert at["shift_count"] == 4.0
    assert at["shiftable"] == 1.0
    assert "gradient" in at["keywords_text"]
    assert json.loads(at["rule_json"])["name"] == "hop_descend_gradient"


def test_ensure_acting_rule_provenance_is_idempotent():
    ag = _agent_with_grid_navigation()
    rf._ensure_acting_rule_provenance(ag.s, ag.inner)
    n1 = len(list(ag.s.nodes("RuleSummary")))
    rf._ensure_acting_rule_provenance(ag.s, ag.inner)
    n2 = len(list(ag.s.nodes("RuleSummary")))
    assert n1 == n2 and n1 >= 1


def test_ensure_acting_rule_provenance_skips_non_acting_rules():
    # a lexicon-only agent (no grid_navigation, no chosen_action-writing rules at all)
    ag = _fresh_agent_with_lexicon()
    rf._ensure_acting_rule_provenance(ag.s, ag.inner)
    assert list(ag.s.nodes("RuleSummary")) == []


# ---------------------------------------------------------------------------
# 4 — back-compat: a concern that grounds 'embed' (the JUDGE-variant path,
#     tests/test_self_delta.py's own shape) but NOT 'gradient' must be
#     completely unaffected: remove_rules stays "[]", add_rules carries
#     exactly the one judge-variant, no acting_variant key surprises.
# ---------------------------------------------------------------------------
_EMBED_OBS_NO_GRADIENT = [
    ["test", "HYPOTHESIS", "about", "SELF"],
    ["vary", "SEED", "by", "DELTA"],
    ["send", "VARIANT", "to", "WORLD"],
    ["judge", "TRIAL", "by", "OUTCOME"],
    ["embed", "VARIANT", "as", "RULE"],
]


def test_embed_only_concern_keeps_remove_rules_trivial_and_is_unaffected():
    ag = _fresh_agent_with_lexicon()
    ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["ev_nogr"], "induced": 1.0,
        "residual_predicates": ["test", "vary", "send", "judge", "embed"], "from_observation": 1.0,
        "source": "concern_induction",
    })
    res = rf.ground_concern(ag, ["ev_nogr"])
    assert res.get("grounded") is True
    assert res.get("acting_variant") is None
    mint = {r["name"]: r for r in res["rules"]}["author_experiment_from_residual_ev_nogr"]
    delta_attrs = mint["effects"][1][3]
    assert delta_attrs.get("remove_rules") == "[]"
    add_rules = json.loads(delta_attrs["add_rules"])
    assert len(add_rules) == 1
    assert add_rules[0]["name"] == "judge_experiment_outcome_variant_ev_nogr"


# ---------------------------------------------------------------------------
# 5 — 'gradient' grounds but NO RuleSummary provenance exists on this
#     substrate at all (no chosen_action-writing rule loaded) -> an HONEST
#     NULL: acting_variant.built is False with a wall, remove_rules stays "[]".
# ---------------------------------------------------------------------------
def test_gradient_without_any_acting_rule_abstains_honestly():
    ag = _fresh_agent_with_lexicon()          # NO grid_navigation loaded
    ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["gr_none"], "induced": 1.0,
        "residual_predicates": ["test", "send", "judge", "gradient"], "from_observation": 1.0,
        "source": "concern_induction",
    })
    res = rf.ground_concern(ag, ["gr_none"])
    assert res.get("grounded") is True
    av = res.get("acting_variant")
    assert av is not None and av.get("built") is False
    assert "wall" in av
    mint = {r["name"]: r for r in res["rules"]}["author_experiment_from_residual_gr_none"]
    delta_attrs = mint["effects"][1][3]
    assert delta_attrs.get("remove_rules") == "[]"
    assert delta_attrs.get("add_rules") == "[]"


# ---------------------------------------------------------------------------
# 6 — 'gradient' grounds WITH the real hop_descend_gradient rule live -> the
#     agent's own Argmax picks it (genuine textual overlap: 'gradient' is a
#     literal substring of the rule's own name) and builds a real variant.
# ---------------------------------------------------------------------------
def test_gradient_with_real_acting_rule_builds_a_genuine_variant():
    ag = _agent_with_grid_navigation()
    ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["gr_real"], "induced": 1.0,
        "residual_predicates": ["test", "send", "judge", "gradient"], "from_observation": 1.0,
        "source": "concern_induction",
    })
    res = rf.ground_concern(ag, ["gr_real"])
    assert res.get("grounded") is True
    av = res.get("acting_variant")
    assert av.get("built") is True
    assert av.get("removed_rule") == "hop_descend_gradient"
    assert av.get("shift") == 4.0        # Count(["test","send","judge","gradient"]) == 4, unscaled
    mint = {r["name"]: r for r in res["rules"]}["author_experiment_from_residual_gr_real"]
    delta_attrs = mint["effects"][1][3]
    assert delta_attrs.get("remove_rules") == json.dumps(["hop_descend_gradient"])
    assert delta_attrs.get("act_shift") == 4.0
    assert delta_attrs.get("act_rule_varied") == "hop_descend_gradient"
    add_rules = json.loads(delta_attrs["add_rules"])
    assert len(add_rules) == 1
    assert add_rules[0]["name"] == "hop_descend_gradient_variant_gr_real"
    shifted = rf._find_threshold_lits(add_rules[0]["effects"])
    assert sorted(n["b"]["value"] for n in shifted) == [-4.0, -4.0, 4.0, 4.0]


# ---------------------------------------------------------------------------
# 7 — BOTH 'embed' and 'gradient' ground together: add_rules carries TWO
#     variants (judge + acting), remove_rules carries the acting one only.
# ---------------------------------------------------------------------------
def test_embed_and_gradient_together_carry_both_variants():
    ag = _agent_with_grid_navigation()
    ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["both1"], "induced": 1.0,
        "residual_predicates": ["test", "vary", "send", "judge", "embed", "gradient"], "from_observation": 1.0,
        "source": "concern_induction",
    })
    res = rf.ground_concern(ag, ["both1"])
    assert res.get("grounded") is True
    assert res.get("acting_variant", {}).get("built") is True
    mint = {r["name"]: r for r in res["rules"]}["author_experiment_from_residual_both1"]
    delta_attrs = mint["effects"][1][3]
    add_rules = json.loads(delta_attrs["add_rules"])
    names = sorted(r["name"] for r in add_rules)
    assert names == ["hop_descend_gradient_variant_both1", "judge_experiment_outcome_variant_both1"]
    assert delta_attrs.get("remove_rules") == json.dumps(["hop_descend_gradient"])


# ---------------------------------------------------------------------------
# 8 — close_experiment_loop's taught topic names WHICH acting rule was
#     varied (additive suffix — the skip_seed_id-only wording is unchanged,
#     tests/test_self_delta.py's own assertion on that exact string still
#     holds because it never sets act_rule_varied).
# ---------------------------------------------------------------------------
def test_close_experiment_loop_names_the_varied_acting_rule():
    ag = _fresh_agent_with_lexicon()
    exp = ag.s.add_node("Experiment", {
        "status": "done", "hypothesis": "h", "game": "navigate", "run_dir": "",
        "outcome": "refuted", "conclusion_ready": True, "axis_tag": "tag_y",
    })
    delta = ag.s.add_node("SeedDelta", {
        "skip_seeds": "[]", "add_rules": "[]",
        "remove_rules": '["hop_descend_gradient"]',
        "act_rule_varied": "hop_descend_gradient", "act_shift": 4.0,
    })
    ag.inner.add_edge_unchecked(exp, "has_delta", delta)

    recs = rf.close_experiment_loop(ag)
    assert len(recs) == 1 and recs[0].get("saved") is True
    with open(_CONCLUSIONS_SEED) as f:
        saved = json.load(f)
    hints = [n for n in saved.get("nodes", []) if n.get("type") == "TaughtHint"]
    topics = [h["attrs"].get("topic") for h in hints]
    assert any("acting rule 'hop_descend_gradient' replaced (shift=4.0)" in t for t in topics)
    assert any(t.startswith("self-experiment for tag_y;") for t in topics)


# ---------------------------------------------------------------------------
# 9 — SLOW, true end-to-end: PART A (the agent's own mint rule fires via
#     tick, authors remove_rules/add_rules, dispatches, the child tombstones
#     the original rule) + PART B (a control/variant pair, dispatched via the
#     blessed mint_experiment host helper — see scripts/jabberwock_varies_
#     acting.py's module docstring "WHY TWO DISPATCH PATHS" for why Part B
#     doesn't reuse Part A's snapshot path) produces a MEASURABLE behavioural
#     difference in the two children's action streams.
# ---------------------------------------------------------------------------
@pytest.mark.slow
def test_full_acting_variant_loop_offline(tmp_path):
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains.experiment_dispatch import mint_experiment, scan_and_dispatch, _INFLIGHT
    from worlds.arc import ArcWorld
    from arc3_env import NavigateEnv

    # --- PART A: the full self-authored loop ---
    _INFLIGHT.clear()
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    S, I = a.s, a.inner

    w = ArcWorld(NavigateEnv())
    sub, ctx = w.reset()
    a.perceive_frame(sub)
    a.tick()

    ind = rf.induce_concern(a, _ACTING_OBS, name_hint="acting_full_loop_concern_test9")
    key = ind.get("capability_key")
    g = rf.ground_concern(a, [key])
    assert g.get("grounded") is True and g.get("path") == "compose_experiment_rule"
    av = g.get("acting_variant")
    assert av.get("built") is True and av.get("removed_rule") == "hop_descend_gradient"

    a.tick()
    I.run_rules()
    axis = next(n for n in S.nodes("CapabilityAxis") if str(n) == str(ind.get("axis_id")))
    exp_a = next(iter(I.neighbours(axis, "tested_by")), None)
    assert exp_a is not None
    da = S.node(next(iter(I.neighbours(exp_a, "has_delta"))))["attrs"]
    assert da.get("remove_rules") == json.dumps(["hop_descend_gradient"])
    assert json.loads(da.get("add_rules"))[0]["name"].startswith("hop_descend_gradient_variant_")

    runs_dir_a = tmp_path / "runs_a"
    t0 = time.time()
    status_a = None
    while time.time() - t0 < 90:
        scan_and_dispatch(a, runs_dir_a)
        status_a = S.node(exp_a)["attrs"].get("status")
        if status_a not in ("requested", "running"):
            break
        time.sleep(0.5)
    assert status_a == "done"
    run_dir_a = S.node(exp_a)["attrs"]["run_dir"]
    result_a = json.loads(open(os.path.join(run_dir_a, "result.json")).read())
    assert result_a.get("removed_rules") == ["hop_descend_gradient"]

    I.run_rules()
    assert S.node(exp_a)["attrs"].get("conclusion_ready") is True
    recs = rf.close_experiment_loop(a)
    assert any(r.get("saved") for r in recs)

    # --- PART B: clean control/variant behavioural comparison ---
    _INFLIGHT.clear()
    b = WorldAdapter(seeds=())
    load_all_seeds(b)
    Sb, Ib = b.s, b.inner
    ind_b = rf.induce_concern(b, [["test", "HYPOTHESIS", "about", "SELF"],
                                 ["judge", "TRIAL", "by", "OUTCOME"],
                                 ["gradient", "VARIANT", "of", "ACTING"]],
                              name_hint="acting_behavioural_concern_test9")
    g_b = rf.ground_concern(b, [ind_b.get("capability_key")])
    av_b = g_b.get("acting_variant")
    assert av_b.get("built") is True

    exp_c = mint_experiment(b, "control", "navigate", skip_seeds=[], add_rules=[], remove_rules=[])
    exp_v = mint_experiment(b, "variant", "navigate", skip_seeds=[], add_rules=[av_b["rule"]],
                            remove_rules=[av_b["removed_rule"]])
    runs_dir_b = tmp_path / "runs_b"
    t0 = time.time()
    while time.time() - t0 < 90:
        scan_and_dispatch(b, runs_dir_b)
        sc = Sb.node(exp_c)["attrs"].get("status")
        sv = Sb.node(exp_v)["attrs"].get("status")
        if sc not in ("requested", "running") and sv not in ("requested", "running"):
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
    # a robust, non-vacuous claim (see jabberwock_varies_acting.py's module docstring for why
    # this is a count, not a fixed percentage: tie-breaking order is not perfectly stable run
    # to run, but the two arms differing at all is the discriminative property under test)
    assert actions_c != actions_v
    assert n_diff >= 1, f"control and variant actions never diverged: {actions_c} vs {actions_v}"
