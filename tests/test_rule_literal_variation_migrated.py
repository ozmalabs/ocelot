"""WHERE-CLAUSE-VARIATION wave gate: the `rule_literal_edit` variation family
— the agent closes a WHERE-CLAUSE-LITERAL residual (R2/R5) through its OWN
pipeline, exactly the same shape as the RESIDUAL-CLOSURE wave's `knob_edit`
gate (tests/test_residual_closure_migrated.py), for the residual class that
family's own abstain path names explicitly: "a rule-literal threshold
outside the held node families lands here" (domains/reflective_faculty.py's
`_compose_knob_variant` docstring).

`threshold_shift` only reaches a threshold literal in a chosen_action-
writing rule's own EFFECTS (RuleSummary.writes_chosen_action provenance);
`knob_edit` only reaches a threshold that is a plain held NODE ATTR with no
owning rule. `rule_literal_edit` reaches a numeric literal embedded in a
rule's own WHERE CLAUSE (a match-guard threshold) on a rule that is neither
— e.g. seeds/reading_aperture.json's `escalate_narrative_shape`
(`sentences_read >= 3.0`), seeds/comprehension_health.json's
`note_recurring_speech_act_divergence` (a recurrence `Count >= 3.0`), and
seeds/salient_cache.json's `scell_promote` (`sc_mentions >= 3.0` / a
ten-turn span floor) — R2 and R5 of scripts/residual_closure_run.py's own
residual inventory.

Gated here:
  * structural mechanics: `_find_where_lits`/`_collect_vocab_tokens`/
    `_shift_one_where_literal`/`_rule_effect_witness` on hand-built rule
    dicts (fast, no boot);
  * provenance: `_ensure_where_literal_rule_provenance` upgrades the three
    target seeds' rules in place with genuine (from_seed, skippable)
    provenance on a fully-booted agent;
  * the pick: the held `variation_pick` Program chooses `rule_literal_edit`
    exactly when `ruleliteral` grounds, never hijacking `knob_edit`'s
    `bound` cue (and `knob_edit` still wins when BOTH ground — priority
    15 < 18);
  * the compose: `_compose_rule_literal_variant` picks the content-named
    rule + literal + direction on a real target rule, honestly abstains on
    ambiguous target/direction, and its variant body round-trips
    `jabberwock_daemon._canon_rule_body` cleanly;
  * child mechanics: `convo_child_run`'s deferred rule-swap double-pass
    (`_apply_rule_swap`, `_count_witness`) on a light agent + a synthetic
    rule;
  * the judge: `judge_rule_literal_outcome`'s verdict matrix (regression
    veto; direction-aware witness-delta comparison; tie is inconclusive);
  * adoption: the EXISTING generic remove_rule/add_rule fold
    (`perform_adoptions`) + revert + the provenance denylist veto — reused
    unchanged, zero new adoption code;
  * knob_edit parity: this family never changes knob_edit's own pick/build
    behaviour (pick-ordering parity with the RESIDUAL-CLOSURE wave's gates).
"""
from __future__ import annotations

import copy
import json
import os
import sys
import time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from substrate.world_adapter import WorldAdapter          # noqa: E402
from substrate.boot_all import load_all_seeds              # noqa: E402

jd = pytest.importorskip("jabberwock_daemon")

import domains.reflective_faculty as rf                                  # noqa: E402
from domains.experiment_dispatch import (mint_experiment,                # noqa: E402
                                         scan_and_dispatch, _INFLIGHT)
import convo_child_run as ccr                                            # noqa: E402

_GUARDED_SEEDS = (
    os.path.join(ROOT, "seeds", "experiment_conclusions.json"),
)


@pytest.fixture(autouse=True)
def _guard_seed_files():
    before = {}
    for p in _GUARDED_SEEDS:
        before[p] = open(p).read() if os.path.exists(p) else None
    try:
        yield
    finally:
        for p, content in before.items():
            if content is not None:
                with open(p, "w") as f:
                    f.write(content)
            elif os.path.exists(p):
                os.unlink(p)


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


@pytest.fixture()
def light_agent():
    return WorldAdapter(seeds=())


# --- structural mechanics (no boot) ----------------------------------------

_SAMPLE_RULE = {
    "name": "sample_threshold_rule",
    "match": [["m", "flag", "m"]],
    "where": {"type": "And", "items": [
        {"type": "Gte", "a": {"type": "Attr", "node": {"type": "Var", "name": "m"}, "key": "sentences_read"},
         "b": {"type": "Lit", "value": 3.0}},
        {"type": "Gte", "a": {"type": "Count", "source": {
            "type": "Filter", "source": {"type": "NodesOfType", "node_type": "SmEntity"},
            "var_name": "e", "predicate": {"type": "Eq",
                "a": {"type": "Attr", "node": {"type": "Var", "name": "e"}, "key": "coref_category"},
                "b": {"type": "Lit", "value": "person"}}}},
         "b": {"type": "Lit", "value": 2.0}},
    ]},
    "effects": [
        ["add_node", "sc", "SelfConcern", {"status": "noted", "source": "implicit",
                                           "kind": "comprehension", "flag": "sample"}],
        ["set_attr", "m", "sample_noted", 1.0],
    ],
}


def test_find_where_lits_scopes_to_where_only():
    cands = rf._find_where_lits(_SAMPLE_RULE["where"])
    assert len(cands) == 2
    assert cands[0]["type"] == "Gte" and cands[0]["b"]["value"] == 3.0
    assert cands[1]["b"]["value"] == 2.0
    # match/effects are never scanned
    assert rf._find_where_lits(_SAMPLE_RULE["match"]) == []
    assert rf._find_where_lits(_SAMPLE_RULE["effects"]) == []


def test_collect_vocab_tokens_reads_attr_and_type_and_lit_strings():
    cands = rf._find_where_lits(_SAMPLE_RULE["where"])
    v0 = rf._collect_vocab_tokens(cands[0])
    assert v0 == {"sentences", "read"}
    v1 = rf._collect_vocab_tokens(cands[1])
    assert {"coref", "category", "smentity", "person"} <= v1


def test_shift_one_where_literal_floor_direction():
    up = rf._shift_one_where_literal(_SAMPLE_RULE, 0, 1.0, "increase_fires", "sample_variant_t")
    assert up["name"] == "sample_variant_t"
    assert rf._find_where_lits(up["where"])[0]["b"]["value"] == pytest.approx(2.0)
    down = rf._shift_one_where_literal(_SAMPLE_RULE, 0, 1.0, "decrease_fires", "sample_variant_t2")
    assert rf._find_where_lits(down["where"])[0]["b"]["value"] == pytest.approx(4.0)
    # original untouched (deep copy)
    assert rf._find_where_lits(_SAMPLE_RULE["where"])[0]["b"]["value"] == 3.0
    assert rf._shift_one_where_literal(_SAMPLE_RULE, 99, 1.0, "increase_fires", "x") is None


def test_rule_effect_witness_prefers_typed_add_node_literal_attrs():
    w = rf._rule_effect_witness(_SAMPLE_RULE)
    # 'status' is excluded (see _WITNESS_VOLATILE_ATTRS — a lifecycle field
    # routinely advanced by other dispatch machinery before anything counts
    # it; a witness pinned to its mint-time value would undercount forever)
    assert w == {"kind": "typed", "node_type": "SelfConcern",
                "attrs": {"source": "implicit", "kind": "comprehension", "flag": "sample"}}
    # a rule with only set_attr effects falls back to attr_any
    only_setattr = {"effects": [["set_attr", "c", "promoted", 1.0],
                                ["set_attr", "c", "promote_turn", {"__term__": {"type": "Lit", "value": 0}}]]}
    w2 = rf._rule_effect_witness(only_setattr)
    assert w2 == {"kind": "attr_any", "attr": "promoted", "value": 1.0}
    assert rf._rule_effect_witness({"effects": []}) is None
    # a set_attr effect whose ONLY key is 'status' is skipped (volatile),
    # falling through to honest None when nothing stable follows it
    only_status = {"effects": [["set_attr", "m", "status", "done"]]}
    assert rf._rule_effect_witness(only_status) is None


def test_variant_body_round_trips_canon_rule_body():
    variant = rf._shift_one_where_literal(_SAMPLE_RULE, 0, 1.0, "increase_fires", "sample_variant_canon")
    body = jd._canon_rule_body(variant)
    assert body != "", "the variant body must round-trip the Rust rule serializer cleanly"
    # idempotent: canonicalising twice yields the same string
    assert body == jd._canon_rule_body(json.loads(json.dumps(variant)))


# --- provenance --------------------------------------------------------------

def test_where_literal_provenance_covers_the_three_target_rules(agent):
    a = agent
    sub, native, _ag = rf._resolve_agent(a)
    rf._ensure_where_literal_rule_provenance(sub, native)
    by_name = {}
    for n in sub.nodes("RuleSummary"):
        at = sub.node(n)["attrs"]
        nm = at.get("name")
        if nm:
            by_name[nm] = at
    for name, seed_id in (("escalate_narrative_shape", "reading_aperture"),
                          ("note_recurring_speech_act_divergence", "comprehension_health"),
                          ("scell_promote", "salient_cache")):
        assert name in by_name, f"{name} not mirrored as a RuleSummary"
        at = by_name[name]
        assert at.get("writes_where_literal") == 1.0, (name, at)
        assert at.get("where_shiftable") == 1.0, (name, at)
        assert at.get("where_shift_count", 0) >= 1.0, (name, at)
        assert at.get("from_seed") == seed_id, (name, at.get("from_seed"))
        if name == "note_recurring_speech_act_divergence":
            # tranche 19: this rule FILES the loop's own SelfConcerns, so it is
            # self-improvement-loop machinery (seeds/improvement_integrity.json)
            # -- mirrored for provenance, but never a variation candidate.
            assert at.get("improvement_machinery") == 1.0, (name, at)
            assert at.get("skippable") == 0.0, (name, "loop machinery must not be adoptable")
            continue
        assert at.get("skippable") == 1.0, (name, "must be adoptable — not alignment/core-frozen")


# --- the pick ------------------------------------------------------------------

_CONVO = ["test", "replay", "send", "judge", "adopt"]


def test_variation_pick_chooses_rule_literal_edit_and_never_hijacks_bound(light_agent):
    a = light_agent
    a.s.add_node("StandingConcern", {"name": "rl_rep", "kind": "reported"})
    assert rf._pick_variation_op(a, _CONVO + ["ruleliteral"], "rl_rep") == "rule_literal_edit"
    assert rf._pick_variation_op(a, _CONVO, "rl_rep") == "reply_ablation"
    # a concern naming a HELD KNOB ('bound') is untouched by this family
    assert rf._pick_variation_op(a, _CONVO + ["bound"], "rl_rep") == "knob_edit"
    # when BOTH ground, knob_edit still wins (priority 15 < 18) — documented ordering
    assert rf._pick_variation_op(a, _CONVO + ["bound", "ruleliteral"], "rl_rep") == "knob_edit"
    # never hijacks the instruction family's cue_set_edit (priority 10 < 18)
    a.s.add_node("StandingConcern", {"name": "rl_ins", "kind": "instruction"})
    assert rf._pick_variation_op(a, _CONVO + ["ruleliteral"], "rl_ins") == "cue_set_edit"


# --- the compose -----------------------------------------------------------

def _promote(a, content, name="rl_narrative", kind="reported"):
    sc = a.s.add_node("SelfConcern", {"status": "noted", "source": "explicit_report",
                                      "kind": kind, "content": content})
    st = a.s.add_node("StandingConcern", {"name": name, "kind": kind})
    a.inner.add_edge_unchecked(sc, "promoted_to", st)
    return sc, st


def test_compose_rule_literal_variant_picks_named_literal_and_direction(agent):
    a = agent
    _promote(a, "your narrative shape escalation floor of three sentences read before it "
                "fires makes you escalate too rarely on short stories")
    rep = rf._compose_rule_literal_variant(a, ["rl_narrative"], "t1")
    assert rep["built"] is True, rep
    assert rep["removed_rule"] == "escalate_narrative_shape"
    assert rep["old_value"] == pytest.approx(3.0)
    assert rep["direction"] == "increase_fires"
    assert rep["new_value"] == pytest.approx(2.0)
    assert rep["rule"]["name"] == "escalate_narrative_shape_variant_t1"
    assert rep["witness"]["kind"] == "typed"
    assert rep["witness"]["node_type"] == "AnalysisStage"
    assert rep["witness"]["attrs"].get("escalation_reason") == "narrative_shape"
    # variant body is installable / canon-clean
    assert jd._canon_rule_body(rep["rule"]) != ""


def test_compose_rule_literal_variant_opposite_direction(agent):
    a = agent
    # targets scell_promote's SPAN literal (last_turn - first_turn >= 10.0) —
    # its where-clause vocabulary ({'first','last','turn'}) is cleanly
    # reachable by natural words; the SIBLING sc_mentions literal on the
    # SAME rule splits to {'sc','mentions'} and 'sc' is shorter than the
    # >2-char content-word floor both this builder and _compose_knob_variant
    # apply — a genuine, honestly-scoped residual of the length guard (a
    # concern would need to repeat 'mentions' to clear the 2-word minimum),
    # not exercised by this unit (the closure run targets the span literal).
    _promote(a, "your salient cell promotion turn span between last turn and first turn of "
                "ten turns is far too eager and fires too often on light chit chat",
             name="rl_salient")
    rep = rf._compose_rule_literal_variant(a, ["rl_salient"], "t2")
    assert rep["built"] is True, rep
    assert rep["removed_rule"] == "scell_promote"
    assert rep["direction"] == "decrease_fires"
    assert rep["old_value"] == pytest.approx(10.0)
    assert rep["new_value"] == pytest.approx(11.0)


def test_compose_rule_literal_variant_abstains_on_ambiguous_target(agent):
    a = agent
    _promote(a, "you always mumble incoherently and nothing makes sense", name="rl_none")
    rep = rf._compose_rule_literal_variant(a, ["rl_none"], "t3")
    assert rep["built"] is False and "abstain" in rep["wall"]


def test_compose_rule_literal_variant_abstains_on_ambiguous_direction(agent):
    a = agent
    # names the sentences_read literal genuinely but gives NO direction cue at all
    _promote(a, "your narrative shape escalation floor of three sentences read before it "
                "fires is what I am asking about", name="rl_nodir")
    rep = rf._compose_rule_literal_variant(a, ["rl_nodir"], "t4")
    assert rep["built"] is False and "ambiguous direction" in rep["wall"]


# --- child mechanics (deferred rule swap + witness) -------------------------

def test_apply_rule_swap_deferred_and_witness_counting(light_agent):
    a = light_agent
    a.inner.add_rule(_SAMPLE_RULE)
    variant = rf._shift_one_where_literal(_SAMPLE_RULE, 0, 1.0, "increase_fires", "sample_variant_child")
    delta = {"skip_seeds": [], "add_rules": [variant], "remove_rules": ["sample_threshold_rule"],
             "add_concepts": [], "remove_concepts": [], "set_node_attrs": [],
             "parent_shadow_read": False, "rule_literal_edit": 1.0, "rule_literal_witness": ""}
    removed = ccr.apply_delta(a, delta, defer_rules=True)
    assert removed == []
    exported = a.inner.export_rules()
    assert any(r.get("name") == "sample_threshold_rule" and r.get("active", True) for r in exported), (
        "a deferred delta must NOT swap the rule yet")
    removed2 = ccr._apply_rule_swap(a, delta)
    assert removed2 == ["sample_threshold_rule"]
    exported2 = a.inner.export_rules()
    live_names = {r["name"] for r in exported2 if r.get("active", True)}
    assert "sample_threshold_rule" not in live_names
    assert "sample_variant_child" in live_names


def test_count_witness_typed_and_attr_any(light_agent):
    a = light_agent
    a.s.add_node("SelfConcern", {"status": "noted", "kind": "comprehension", "flag": "sample"})
    a.s.add_node("SelfConcern", {"status": "noted", "kind": "other", "flag": "sample"})
    typed_w = {"kind": "typed", "node_type": "SelfConcern",
               "attrs": {"status": "noted", "kind": "comprehension", "flag": "sample"}}
    assert ccr._count_witness(a, typed_w) == 1
    a.s.add_node("Anything", {"promoted": 1.0})
    a.s.add_node("SomethingElse", {"promoted": 1.0})
    a.s.add_node("SomethingElse", {"promoted": 0.0})
    attr_w = {"kind": "attr_any", "attr": "promoted", "value": 1.0}
    assert ccr._count_witness(a, attr_w) == 2
    assert ccr._count_witness(a, None) == 0


# --- the judge -----------------------------------------------------------------

def _mint_lit_experiment(a, *, control=3, variant=2, direction="increase_fires",
                         regressions=0, outcome="supported"):
    exp = mint_experiment(a, "rule literal probe", "conversation",
                          add_rules=[{"name": "sample_variant"}],
                          remove_rules=["sample_threshold_rule"])
    delta = next(d for d in a.inner.neighbours(exp, "has_delta"))
    a.inner.set_attr(delta, "rule_literal_edit", 1.0)
    a.inner.set_attr(delta, "rule_literal_direction", direction)
    a.inner.set_attr(delta, "act_rule_varied", "sample_threshold_rule")
    a.inner.set_attr(exp, "status", "done")
    a.inner.set_attr(exp, "outcome", outcome)
    a.inner.set_attr(exp, "regressions", regressions)
    a.inner.set_attr(exp, "control_witness_fires", control)
    a.inner.set_attr(exp, "variant_witness_fires", variant)
    a.inner.set_attr(exp, "adopt_ready", True)
    return exp, delta


def _run_judge(a, exp):
    # the generic per-axis judge rule (installed dynamically by
    # _compose_experiment_rule per capability key, not present on a bare
    # hand-minted Experiment) normally adds the 'analysed' edge as part of
    # ITS OWN judging; a direct unit test of judge_rule_literal_outcome
    # stands that edge up by hand (mechanical fixture setup, not a decision).
    run = a.s.add_node("Run", {"status": "done", "frames": 3, "score": 0})
    a.inner.add_edge_unchecked(exp, "produced", run)
    a.inner.add_edge_unchecked(exp, "analysed", run)
    a.tick()


def test_judge_rule_literal_outcome_matrix(agent):
    a = agent

    exp1, _ = _mint_lit_experiment(a, control=3, variant=5, direction="increase_fires", regressions=0)
    _run_judge(a, exp1)
    assert a.s.node(exp1)["attrs"].get("outcome") == "supported"

    exp2, _ = _mint_lit_experiment(a, control=3, variant=3, direction="increase_fires", regressions=0)
    _run_judge(a, exp2)
    assert a.s.node(exp2)["attrs"].get("outcome") == "inconclusive"

    exp3, _ = _mint_lit_experiment(a, control=3, variant=1, direction="increase_fires", regressions=0)
    _run_judge(a, exp3)
    assert a.s.node(exp3)["attrs"].get("outcome") == "refuted"

    exp4, _ = _mint_lit_experiment(a, control=5, variant=2, direction="decrease_fires", regressions=0)
    _run_judge(a, exp4)
    assert a.s.node(exp4)["attrs"].get("outcome") == "supported"

    exp5, _ = _mint_lit_experiment(a, control=5, variant=2, direction="increase_fires", regressions=2)
    _run_judge(a, exp5)
    assert a.s.node(exp5)["attrs"].get("outcome") == "refuted", "any regression always refutes"


# --- adoption + revert + denylist veto (reuses the GENERIC rule-replace fold) --

def test_rule_literal_adoption_folds_via_generic_path_and_revert_restores(light_agent):
    a = light_agent
    a.inner.add_rule(_SAMPLE_RULE)
    variant = rf._shift_one_where_literal(_SAMPLE_RULE, 0, 1.0, "increase_fires", "sample_threshold_rule_variant_ad")
    exp = mint_experiment(a, "rule literal probe", "conversation",
                          add_rules=[variant], remove_rules=["sample_threshold_rule"])
    delta = next(d for d in a.inner.neighbours(exp, "has_delta"))
    a.inner.set_attr(delta, "rule_literal_edit", 1.0)
    a.inner.set_attr(delta, "act_rule_varied", "sample_threshold_rule")
    a.inner.set_attr(exp, "status", "done")
    a.inner.set_attr(exp, "outcome", "supported")
    a.inner.set_attr(exp, "regressions", 0)
    a.inner.set_attr(exp, "adopt_ready", True)
    # provenance: mark this rule adoptable (skippable seed), as the real
    # _ensure_where_literal_rule_provenance would for a genuine seed rule
    a.s.add_node("RuleSummary", {"name": "sample_threshold_rule", "from_seed": "sample_seed",
                                 "writes_where_literal": 1.0, "skippable": 1.0})
    a.s.add_node("SeedSummary", {"seed_id": "sample_seed", "skippable": 1.0})

    records = rf.perform_adoptions(a)
    fold = [r for r in records if r.get("rule_removed") == "sample_threshold_rule"]
    assert len(fold) == 1, records
    assert a.s.node(exp)["attrs"].get("adopted") is True
    live_names = {r["name"] for r in a.inner.export_rules() if r.get("active", True)}
    assert "sample_threshold_rule" not in live_names
    assert "sample_threshold_rule_variant_ad" in live_names

    adoption = fold[0]["adoption"]
    r = rf.revert_adoption(a, adoption)
    assert r["reverted"] is True
    live_names2 = {r2["name"] for r2 in a.inner.export_rules() if r2.get("active", True)}
    assert "sample_threshold_rule" in live_names2
    assert "sample_threshold_rule_variant_ad" not in live_names2


def test_rule_literal_adoption_vetoed_on_non_skippable_provenance(light_agent):
    a = light_agent
    a.inner.add_rule(_SAMPLE_RULE)
    variant = rf._shift_one_where_literal(_SAMPLE_RULE, 0, 1.0, "increase_fires", "sample_threshold_rule_variant_veto")
    exp = mint_experiment(a, "rule literal probe", "conversation",
                          add_rules=[variant], remove_rules=["sample_threshold_rule"])
    delta = next(d for d in a.inner.neighbours(exp, "has_delta"))
    a.inner.set_attr(delta, "rule_literal_edit", 1.0)
    a.inner.set_attr(delta, "act_rule_varied", "sample_threshold_rule")
    a.inner.set_attr(exp, "status", "done")
    a.inner.set_attr(exp, "outcome", "supported")
    a.inner.set_attr(exp, "regressions", 0)
    a.inner.set_attr(exp, "adopt_ready", True)
    # NO RuleSummary provenance at all for this rule -> unknown provenance -> DENY by default
    records = rf.perform_adoptions(a)
    denied = [r for r in records if r.get("rule") == "sample_threshold_rule"]
    assert len(denied) == 1 and denied[0]["denied"] is True
    assert a.s.node(exp)["attrs"].get("adopted") is not True
    live_names = {r["name"] for r in a.inner.export_rules() if r.get("active", True)}
    assert "sample_threshold_rule" in live_names, "a denied rule-literal adoption must leave the parent unchanged"


# --- knob_edit parity (this family must never change knob_edit behaviour) -----

def test_knob_edit_pick_and_compose_unaffected(agent):
    a = agent
    # Fixed-step path pinned: since variation_ops v1.15.0 (tranche 12) the
    # default is step_mode="grain", which abstains on an agent that has
    # observed no gated-signal values (no frame to step on).
    rf._ensure_seed_chain(a.s, a.inner, a.agent, ("variation_ops",))
    for _n in a.s.nodes("VariationOp"):
        if a.s.node(_n)["attrs"].get("name") == "knob_edit":
            a.s.set_attr(_n, "step_mode", "fixed")
    sc = a.s.add_node("SelfConcern", {
        "status": "noted", "source": "explicit_report", "kind": "reported",
        "content": "your reading reform swallowed threshold is wrong"})
    st = a.s.add_node("StandingConcern", {"name": "k_knob_parity", "kind": "reported"})
    a.inner.add_edge_unchecked(sc, "promoted_to", st)
    rep = rf._compose_knob_variant(a, ["k_knob_parity"], "tp")
    assert rep["built"] is True
    assert rep["attr"] == "reform_swallowed_threshold"


def test_residual_closure_runner_source_discipline_unaffected():
    import residual_closure_run as rcr
    violations = rcr.audit_source_discipline()
    assert violations == [], violations
