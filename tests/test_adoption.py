"""test_adoption — CLOSING THE SELF-IMPROVEMENT LOOP: a SUPPORTED self-
experiment's variant gets ADOPTED INTO THE PARENT ITSELF.

Companion to tests/test_acting_variant.py (the acting-variant machinery this
loop adopts) and tests/test_structural_variant.py (the structural-edit twin) —
covering the NEW adoption machinery in domains/reflective_faculty.py:

  - `mark_adopt_ready_*` — the agent's OWN rule (composed by
    `_compose_experiment_rule`'s 'adopt' branch, gated by the new
    `adopt_winner` RelationCue) that marks a SUPPORTED Experiment carrying a
    genuine acting-variant delta `adopt_ready` — WHICH experiment is a
    candidate is entirely this rule's decision.
  - `_rule_seed_map` / `_rule_denylisted` — the provenance denylist veto
    (reuses `SeedSummary.skippable` + a new `RuleSummary.from_seed` link;
    unknown provenance DENIES).
  - `perform_adoptions` / `close_experiment_loop` — the host mechanical I/O
    that folds an adopt_ready variant into the PARENT (remove_rule the
    original + add_rule the variant + an `Adoption` record + a TaughtHint),
    gated by the denylist regardless of what any rule marked.
  - `revert_adoption` — the rollback (tombstones can't un-tombstone, so this
    re-adds the original's exact captured JSON as a fresh slot).

Per CLAUDE.md's discipline: these tests never hand-install the adopt rule's
text — they frame concerns and read back what the agent authored. The
acting-variant CONTENT they adopt is always agent-authored
(`_compose_acting_variant`, real seed-sourced rule JSON), carried on
hand-built Experiment/SeedDelta nodes so the supported/refuted/denylisted
cases can each be exercised on purpose (the same style
tests/test_acting_variant.py's test 8 and tests/test_self_delta.py's test 6
already use for Experiment/SeedDelta).
"""
from __future__ import annotations

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
    tests/test_acting_variant.py's own `_Agent` (harness glue only)."""
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def _fresh_agent_with_lexicon() -> _Agent:
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    return ag


def _agent_with_grid_navigation(*, skippable: float = 1.0) -> _Agent:
    """A lexicon-only agent that ALSO has grid_navigation.json loaded (so its
    real, live hop_descend_gradient rule exists), PLUS a real-shaped
    `SeedSummary{seed_id:'grid_navigation', skippable}` node — the provenance
    fact `substrate/boot_all.py.load_all_seeds` would mint identically (this
    seed is not in `_FROZEN_SEED_IDS`, so a genuine boot always gives
    skippable=1.0; `skippable` is a test parameter here ONLY so the denylist
    veto's 'non-skippable seed' branch can be exercised on purpose — the same
    style test_self_delta.py's test 5 mutates `SeedSummary` fixtures for).
    `_rule_seed_map`'s own re-parse of seeds/grid_navigation.json (not
    anything this node claims) is what actually proves `hop_descend_gradient`
    lives in this seed — the SeedSummary node only supplies "this agent loaded
    it, and here is whether it's skippable"."""
    ag = _fresh_agent_with_lexicon()
    ag.s._inner.load_seed_manifest(manifest_for("grid_navigation"), ag.agent)
    ag.s.add_node("SeedSummary", {"seed_id": "grid_navigation",
                                  "keywords_text": "grid navigation gradient hop descend row col",
                                  "skippable": skippable})
    return ag


def _real_acting_variant(ag: _Agent, tag: str) -> dict:
    """A genuinely agent-authored acting-variant (never hand-written rule
    text): frame a 'gradient' concern and let `_compose_acting_variant` pick +
    build it from the REAL, live `hop_descend_gradient` rule."""
    ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": [tag], "induced": 1.0,
        "residual_predicates": ["test", "send", "judge", "gradient"], "from_observation": 1.0,
        "source": "concern_induction",
    })
    av = rf._compose_acting_variant(ag, [tag], tag)
    assert av.get("built") is True, av
    return av


def _mint_experiment_with_delta(ag: _Agent, av: dict, outcome: str, tag: str):
    exp = ag.s.add_node("Experiment", {"status": "done", "hypothesis": f"h_{tag}", "game": "navigate",
                                       "run_dir": "", "outcome": outcome, "conclusion_ready": True,
                                       "axis_tag": tag})
    delta = ag.s.add_node("SeedDelta", {"skip_seeds": "[]", "add_rules": json.dumps([av["rule"]]),
                                        "remove_rules": json.dumps([av["removed_rule"]]),
                                        "act_rule_varied": av["removed_rule"], "act_shift": av.get("shift")})
    ag.inner.add_edge_unchecked(exp, "has_delta", delta)
    return exp


def _mark_adopt_ready(ag: _Agent, tag: str):
    """Frame the 'adopt' concern (the agent's OWN mark_adopt_ready_* rule) and
    run it to fixpoint — the same drive shape ground_concern's other composer
    paths use, never a host-written adopt_ready=True."""
    ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": [tag], "induced": 1.0,
        "residual_predicates": ["adopt"], "from_observation": 1.0, "source": "concern_induction",
    })
    g = rf.ground_concern(ag, [tag])
    assert g.get("grounded") is True
    ag.inner.run_rules()
    return g


def _rule_active(ag: _Agent, name: str):
    """The LAST exported state for `name` (export_rules keeps one entry per
    add_rule call; the most recent reflects whether it's currently active)."""
    states = [r.get("active", True) for r in ag.inner.export_rules() if r.get("name") == name]
    return states[-1] if states else None


# ---------------------------------------------------------------------------
# 1 — the new 'adopt_winner' RelationCue loads and routes to the 'experiment'
#     composer (the ComposerCue this change also adds).
# ---------------------------------------------------------------------------
def test_adopt_relation_cue_loads():
    ag = _fresh_agent_with_lexicon()
    cues = {at["name"]: at for at in (ag.s.node(n)["attrs"] for n in ag.s.nodes("RelationCue"))}
    assert "adopt_winner" in cues
    assert json.loads(cues["adopt_winner"]["relation"]) == ["adopt", "WINNER", "as", "SELF"]


def test_adopt_concern_grounds_and_composes_mark_adopt_ready_rule():
    ag = _fresh_agent_with_lexicon()
    ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["ad1"], "induced": 1.0,
        "residual_predicates": ["adopt"], "from_observation": 1.0, "source": "concern_induction",
    })
    res = rf.ground_concern(ag, ["ad1"])
    assert res.get("grounded") is True and res.get("path") == "compose_experiment_rule"
    names = {r["name"] for r in res["rules"]}
    assert "mark_adopt_ready_ad1" in names


# ---------------------------------------------------------------------------
# 2 — provenance denylist: unknown provenance DENIES; a non-skippable seed's
#     rule DENIES even when supported; a skippable seed's rule is ALLOWED.
# ---------------------------------------------------------------------------
def test_rule_denylisted_unknown_provenance_denies():
    ag = _agent_with_grid_navigation()
    ag.s.add_node("RuleSummary", {"name": "phantom_rule", "keywords_text": "phantom",
                                  "writes_chosen_action": 1.0, "shift_count": 1.0, "shiftable": 1.0,
                                  "rule_json": "{}", "from_seed": ""})
    denied, reason = rf._rule_denylisted(ag.s, "phantom_rule")
    assert denied is True and "unknown provenance" in reason


def test_rule_denylisted_no_rulesummary_at_all_denies():
    ag = _agent_with_grid_navigation()
    denied, reason = rf._rule_denylisted(ag.s, "nonexistent_rule")
    assert denied is True and "unknown provenance" in reason


def test_rule_denylisted_non_skippable_seed_denies():
    ag = _agent_with_grid_navigation(skippable=0.0)
    rf._ensure_acting_rule_provenance(ag.s, ag.inner)
    denied, reason = rf._rule_denylisted(ag.s, "hop_descend_gradient")
    assert denied is True and "non-skippable" in reason


def test_rule_denylisted_skippable_seed_allows():
    ag = _agent_with_grid_navigation(skippable=1.0)
    rf._ensure_acting_rule_provenance(ag.s, ag.inner)
    denied, reason = rf._rule_denylisted(ag.s, "hop_descend_gradient")
    assert denied is False and reason == ""


def test_rule_seed_map_finds_hop_descend_gradient_in_grid_navigation():
    ag = _agent_with_grid_navigation()
    m = rf._rule_seed_map(ag.s)
    assert m.get("hop_descend_gradient") == "grid_navigation"


def test_ensure_acting_rule_provenance_stamps_from_seed():
    ag = _agent_with_grid_navigation()
    rf._ensure_acting_rule_provenance(ag.s, ag.inner)
    by_name = {ag.s.node(n)["attrs"]["name"]: ag.s.node(n)["attrs"] for n in ag.s.nodes("RuleSummary")}
    assert by_name["hop_descend_gradient"]["from_seed"] == "grid_navigation"


def test_ensure_acting_rule_provenance_from_seed_empty_without_seed_summary():
    # NO SeedSummary at all — the honest 'unknown provenance' shape.
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    ag.s._inner.load_seed_manifest(manifest_for("grid_navigation"), ag.agent)
    rf._ensure_acting_rule_provenance(ag.s, ag.inner)
    by_name = {ag.s.node(n)["attrs"]["name"]: ag.s.node(n)["attrs"] for n in ag.s.nodes("RuleSummary")}
    assert by_name["hop_descend_gradient"]["from_seed"] == ""


# ---------------------------------------------------------------------------
# 3 — mark_adopt_ready_* fires ONLY on a supported Experiment carrying a
#     genuine acting-variant delta; a refuted one is never marked.
# ---------------------------------------------------------------------------
def test_mark_adopt_ready_fires_on_supported_with_acting_variant():
    ag = _agent_with_grid_navigation()
    av = _real_acting_variant(ag, "mk_sup")
    exp = _mint_experiment_with_delta(ag, av, "supported", "mk_sup")
    _mark_adopt_ready(ag, "mk_sup_mark")
    assert ag.s.node(exp)["attrs"].get("adopt_ready") is True


def test_mark_adopt_ready_does_not_fire_on_refuted():
    ag = _agent_with_grid_navigation()
    av = _real_acting_variant(ag, "mk_ref")
    exp = _mint_experiment_with_delta(ag, av, "refuted", "mk_ref")
    _mark_adopt_ready(ag, "mk_ref_mark")
    assert ag.s.node(exp)["attrs"].get("adopt_ready") is not True


def test_mark_adopt_ready_does_not_fire_without_a_genuine_delta():
    # a supported Experiment whose delta has NO act_rule_varied (a bare judge-
    # variant / skip_seeds-only delta) must never be marked.
    ag = _fresh_agent_with_lexicon()
    exp = ag.s.add_node("Experiment", {"status": "done", "hypothesis": "h", "game": "navigate",
                                       "run_dir": "", "outcome": "supported", "conclusion_ready": True,
                                       "axis_tag": "bare"})
    delta = ag.s.add_node("SeedDelta", {"skip_seeds": "[]", "add_rules": "[]", "remove_rules": "[]"})
    ag.inner.add_edge_unchecked(exp, "has_delta", delta)
    _mark_adopt_ready(ag, "bare_mark")
    assert ag.s.node(exp)["attrs"].get("adopt_ready") is not True


# ---------------------------------------------------------------------------
# 4 — perform_adoptions: the mechanical fold-back. Supported+allowed adopts
#     (export_rules shows the tombstone + the active variant, an Adoption
#     record with the original JSON, a TaughtHint); supported+denylisted is
#     denied; idempotent.
# ---------------------------------------------------------------------------
def test_perform_adoptions_adopts_supported_and_allowed():
    ag = _agent_with_grid_navigation(skippable=1.0)
    av = _real_acting_variant(ag, "pa_ok")
    exp = _mint_experiment_with_delta(ag, av, "supported", "pa_ok")
    _mark_adopt_ready(ag, "pa_ok_mark")

    recs = rf.perform_adoptions(ag)
    assert len(recs) == 1 and recs[0].get("saved") is True
    assert ag.s.node(exp)["attrs"].get("adopted") is True
    assert _rule_active(ag, av["removed_rule"]) is False
    assert _rule_active(ag, av["rule"]["name"]) is True

    adoption = next(iter(ag.s.nodes("Adoption")))
    at = ag.s.node(adoption)["attrs"]
    assert at["rule_removed"] == av["removed_rule"]
    assert at["rule_added"] == av["rule"]["name"]
    assert json.loads(at["original_rule_json"])["name"] == av["removed_rule"]

    with open(_CONCLUSIONS_SEED) as f:
        saved = json.load(f)
    hints = [n for n in saved.get("nodes", []) if n.get("type") == "TaughtHint"]
    assert any("adoption:" in h["attrs"].get("topic", "") for h in hints)


def test_perform_adoptions_denies_denylisted_even_if_supported():
    ag = _agent_with_grid_navigation(skippable=0.0)
    av = _real_acting_variant(ag, "pa_deny")
    exp = _mint_experiment_with_delta(ag, av, "supported", "pa_deny")
    _mark_adopt_ready(ag, "pa_deny_mark")

    recs = rf.perform_adoptions(ag)
    assert len(recs) == 1 and recs[0].get("denied") is True
    assert ag.s.node(exp)["attrs"].get("adopted") is not True
    assert ag.s.node(exp)["attrs"].get("adopt_denied") is True
    assert _rule_active(ag, av["removed_rule"]) is True   # untouched


def test_perform_adoptions_never_fires_on_refuted():
    ag = _agent_with_grid_navigation()
    av = _real_acting_variant(ag, "pa_ref")
    exp = _mint_experiment_with_delta(ag, av, "refuted", "pa_ref")
    _mark_adopt_ready(ag, "pa_ref_mark")     # honest no-op (test 3 above)
    recs = rf.perform_adoptions(ag)
    assert recs == []
    assert _rule_active(ag, av["removed_rule"]) is True


def test_perform_adoptions_is_idempotent():
    ag = _agent_with_grid_navigation()
    av = _real_acting_variant(ag, "pa_idem")
    _mint_experiment_with_delta(ag, av, "supported", "pa_idem")
    _mark_adopt_ready(ag, "pa_idem_mark")
    recs1 = rf.perform_adoptions(ag)
    assert len(recs1) == 1
    recs2 = rf.perform_adoptions(ag)
    assert recs2 == []


def test_close_experiment_loop_also_performs_adoptions():
    ag = _agent_with_grid_navigation()
    av = _real_acting_variant(ag, "cel_adopt")
    exp = _mint_experiment_with_delta(ag, av, "supported", "cel_adopt")
    _mark_adopt_ready(ag, "cel_adopt_mark")
    recs = rf.close_experiment_loop(ag)
    kinds = {("adoption" if "rule_removed" in r else "conclusion") for r in recs}
    assert "adoption" in kinds
    assert ag.s.node(exp)["attrs"].get("adopted") is True


# ---------------------------------------------------------------------------
# 5 — revert_adoption: rolls back a real adoption (tombstones the variant,
#     re-adds the original as a fresh slot with byte-identical structure);
#     idempotent on an already-reverted Adoption.
# ---------------------------------------------------------------------------
def test_revert_adoption_restores_original_and_tombstones_variant():
    ag = _agent_with_grid_navigation()
    av = _real_acting_variant(ag, "rev1")
    # the ROUND-TRIPPED original (add_rule then export_rules on a fresh substrate, same
    # serialisation path revert_adoption's own captured original_rule_json went through —
    # export_rules omits default-valued fields like Neighbours' any_type:false on the way
    # out, so this is the fair "byte-identical modulo the Rust round-trip" comparison, not
    # the raw un-round-tripped seed JSON).
    gnav_rules = json.load(open(os.path.join(ROOT, "seeds", "grid_navigation.json")))["rules"]
    hop_raw = next(r for r in gnav_rules if r["name"] == "hop_descend_gradient")
    s2, agent_node2 = boot_core()
    s2._inner.add_rule(hop_raw)
    original_rule = next(r for r in s2._inner.export_rules() if r.get("name") == "hop_descend_gradient")
    exp = _mint_experiment_with_delta(ag, av, "supported", "rev1")
    _mark_adopt_ready(ag, "rev1_mark")
    rf.perform_adoptions(ag)
    assert _rule_active(ag, av["removed_rule"]) is False
    assert _rule_active(ag, av["rule"]["name"]) is True

    adoption = next(iter(ag.s.nodes("Adoption")))
    rv = rf.revert_adoption(ag, adoption)
    assert rv.get("reverted") is True
    assert rv.get("restored_rule") == av["removed_rule"]
    assert rv.get("tombstoned_variant") == av["rule"]["name"]
    assert _rule_active(ag, av["rule"]["name"]) is False
    assert _rule_active(ag, av["removed_rule"]) is True
    # the re-added rule is the BYTE-IDENTICAL original structure (match/where/effects) —
    # a real "behaves like pre-adoption" restoration, not a re-derived guess.
    restored = [r for r in ag.inner.export_rules() if r.get("name") == av["removed_rule"]][-1]
    assert restored["match"] == original_rule["match"]
    assert restored["where"] == original_rule["where"]
    assert restored["effects"] == original_rule["effects"]
    assert ag.s.node(exp)["attrs"].get("adopted") is False


def test_revert_adoption_is_idempotent():
    ag = _agent_with_grid_navigation()
    av = _real_acting_variant(ag, "rev2")
    _mint_experiment_with_delta(ag, av, "supported", "rev2")
    _mark_adopt_ready(ag, "rev2_mark")
    rf.perform_adoptions(ag)
    adoption = next(iter(ag.s.nodes("Adoption")))
    rv1 = rf.revert_adoption(ag, adoption)
    assert rv1.get("reverted") is True
    rv2 = rf.revert_adoption(ag, adoption)
    assert rv2.get("reverted") is False and "already" in rv2.get("reason", "")


def test_revert_adoption_on_unknown_node_is_honest():
    ag = _agent_with_grid_navigation()
    rv = rf.revert_adoption(ag, 999999)
    assert rv.get("reverted") is False


# ---------------------------------------------------------------------------
# 6 — SLOW, true end-to-end: PART A (the agent's own mint+judge+acting-
#     variant+adopt-marker rules all fire via tick, a REAL child is
#     dispatched and judged) + PART B (a driven supported case proves the
#     mechanical fold-back + a live NavigateEnv episode on the PARENT
#     diverges before vs. after adoption) — see
#     scripts/jabberwock_improves_itself.py for the full narrative version.
# ---------------------------------------------------------------------------
@pytest.mark.slow
def test_full_adoption_loop_offline(tmp_path):
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains.experiment_dispatch import scan_and_dispatch, _INFLIGHT
    from worlds.arc import ArcWorld
    from arc3_env import NavigateEnv
    import arc_run

    # --- PART A: the full self-authored loop, real dispatch, honest outcome ---
    _INFLIGHT.clear()
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    S, I = a.s, a.inner

    w = ArcWorld(NavigateEnv())
    sub, ctx = w.reset()
    a.perceive_frame(sub)
    a.tick()

    ind = rf.induce_concern(a, [["test", "H", "about", "S"], ["send", "V", "to", "W"],
                               ["judge", "T", "by", "O"], ["gradient", "V", "of", "A"],
                               ["adopt", "W", "as", "S"]],
                           name_hint="full_adoption_loop_concern")
    key = ind.get("capability_key")
    g = rf.ground_concern(a, [key])
    assert g.get("grounded") is True
    av = g.get("acting_variant")
    assert av.get("built") is True

    a.tick()
    I.run_rules()
    axis = next(n for n in S.nodes("CapabilityAxis") if str(n) == str(ind.get("axis_id")))
    exp_a = next(iter(I.neighbours(axis, "tested_by")), None)
    assert exp_a is not None

    runs_dir = tmp_path / "runs"
    t0 = time.time()
    status_a = None
    while time.time() - t0 < 90:
        scan_and_dispatch(a, runs_dir)
        status_a = S.node(exp_a)["attrs"].get("status")
        if status_a not in ("requested", "running"):
            break
        time.sleep(0.5)
    assert status_a == "done"

    I.run_rules()
    outcome = S.node(exp_a)["attrs"].get("outcome")
    assert outcome in ("supported", "refuted", "inconclusive")
    rf.close_experiment_loop(a)
    if outcome == "supported":
        assert S.node(exp_a)["attrs"].get("adopted") is True
        assert _rule_active(_Agent(S, None), av["removed_rule"]) is False
    else:
        # honest: adoption must NOT fire on a non-supported real outcome
        assert S.node(exp_a)["attrs"].get("adopted") is not True

    # --- PART B: a DRIVEN supported case (never left to chance) + behavioral divergence ---
    b = WorldAdapter(seeds=())
    load_all_seeds(b)
    ind_b = rf.induce_concern(b, [["test", "H", "about", "S"], ["send", "V", "to", "W"],
                                 ["judge", "T", "by", "O"], ["gradient", "V", "of", "A"]],
                              name_hint="full_adoption_loop_concern_b")
    g_b = rf.ground_concern(b, [ind_b["capability_key"]])
    av_b = g_b["acting_variant"]
    assert av_b.get("built") is True

    def _actions(agent):
        prod = arc_run._setup_speech(agent)
        describe_ctx = arc_run.setup_describe(agent, prod)
        agent.inner.add_rule(arc_run.MS_CHOOSE_EXPAND)
        out = []
        arc_run.run_episode(agent, ArcWorld(NavigateEnv()), 20, "cells", prod, describe_ctx,
                            on_frame=lambda rec: out.append(rec["action"]))
        return out

    actions_before = _actions(b)

    exp_b = _mint_experiment_with_delta(_Agent(b.s, b.agent), av_b, "supported", "full_loop_b")
    _mark_adopt_ready(_Agent(b.s, b.agent), "full_loop_b_mark")
    rf.close_experiment_loop(b)
    assert b.s.node(exp_b)["attrs"].get("adopted") is True

    actions_after = _actions(b)
    n_common = min(len(actions_before), len(actions_after))
    n_diff = sum(1 for i in range(n_common) if actions_before[i] != actions_after[i])
    assert actions_before != actions_after, \
        f"the parent's own next episode never diverged: {actions_before} vs {actions_after}"
    assert n_diff >= 1
