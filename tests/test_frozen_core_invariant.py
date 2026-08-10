"""test_frozen_core_invariant -- GATE for domains/frozen_core.py: the small,
non-negotiable frozen core (seeds/autonomy.json's `understand` Drive,
frozen:true; boot_core.CORE_SEEDS; the composer-chain seeds; boot_all.py's
_FROZEN_SEED_IDS denylist; proposal_install.py's ALLOWED_INSTALL_FILES) must
be UNREACHABLE from every one of the agent's own self-modification mutation
grammars (EditOps/variant composition, adoption fold-back, composer minting,
rung-4 runtime install, seed-skip ablation) -- the anchor that makes
self-modification well-founded rather than divergent.

Every check here calls the REAL gate (`domains.reflective_faculty.
_rule_denylisted`, `domains.proposal_install.install_proposal`'s guardrail
5, the real `ReachableFrom` Term, the real `substrate.boot_all.
load_all_seeds`) -- never a re-implementation. Section 6 is the
DISCRIMINATIVE battery: hand-crafted scenarios that WOULD violate the
invariant, each checked against the real gate. (a)/(d) are refused --
proving the check is not vacuous. (b) USED TO reproduce a real, latent gap
(`acting_rule_pick_unfiltered`): `_pick_acting_rule`'s own candidate Term
had no `skippable` filter, so it genuinely selected a core-provenance rule
when the residual named it (never applied to the parent either way -- see
`domains/frozen_core.py`'s `edit_ops_variant_compose` grammar). (c) USED TO
reproduce a real, scope-limited gap (`seed_skip_unvalidated_at_consumption`):
a SeedDelta naming a frozen seed in `skip_seeds` was NOT refused at the
point of consumption. All THREE gaps -- `seed_dependency_closure`
(`autonomy` depends_on `['enact', 'discourse']`, neither of which was
itself frozen), `seed_skip_unvalidated_at_consumption`, and
`acting_rule_pick_unfiltered` -- are now CLOSED: `substrate.boot_all.
load_all_seeds` refuses any skip naming a seed in `domains.frozen_core.
frozen_seed_ids_closed()` (the frozen set, dependency-closed), loudly, and
fails safe if the frozen set can't be computed; `_pick_acting_rule` (and its
graph-native twin, `compose_experiment_mint_parametric` in
`seeds/composer_experiment_graph.json` -- the meta-rule that actually SERVES
`ground_concern` in production) both now restrict their Argmax candidates to
`skippable==1.0` RuleSummary nodes, the field `_ensure_acting_rule_
provenance` stamps from the SAME `frozen_seed_ids_closed()` set. Sections
7b and 7c below are rewritten from gap-reproductions into fix-verifications.
See seeds/frozen_core_manifest.json's `known_gaps` for the full writeup.
"""
from __future__ import annotations

import json
import os
import sys
import time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core, CORE_SEEDS               # noqa: E402
from substrate.boot_all import _FROZEN_SEED_IDS                     # noqa: E402
from substrate.seed_loader import manifest_for                      # noqa: E402
import domains.frozen_core as fc                                    # noqa: E402
import domains.reflective_faculty as rf                             # noqa: E402
from domains import proposal_install as pinstall                    # noqa: E402
from domains.auto_approve import DEFAULTS as AUTO_APPROVE_DEFAULTS  # noqa: E402


class _Agent:
    """Minimal duck-typed agent wrapper -- identical shape to
    tests/test_adoption.py's own `_Agent` (harness glue only)."""
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def _fresh_agent_with_autonomy() -> _Agent:
    """Fast fixture: CORE_SEEDS + relation_vocabulary (composer lexicon) +
    autonomy (the frozen Drive) -- no full 386-seed boot needed for most
    checks here (mirrors tests/test_adoption.py's `_fresh_agent_with_lexicon`
    pattern)."""
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    ag.s._inner.load_seed_manifest(manifest_for("autonomy"), ag.agent)
    return ag


def _agent_with_grid_navigation(*, skippable: float = 1.0) -> _Agent:
    ag = _fresh_agent_with_autonomy()
    ag.s._inner.load_seed_manifest(manifest_for("grid_navigation"), ag.agent)
    ag.s.add_node("SeedSummary", {"seed_id": "grid_navigation",
                                  "keywords_text": "grid navigation gradient hop descend row col",
                                  "skippable": skippable})
    return ag


# ---------------------------------------------------------------------------
# 1 -- frozen_core_set: enumeration, cross-checked against live constants.
# ---------------------------------------------------------------------------
def test_manifest_matches_live_constants_no_drift():
    core = fc.frozen_core_set()
    assert core["manifest_drift"] == [], core["manifest_drift"]


def test_core_seeds_subset_of_frozen_seeds():
    assert set(CORE_SEEDS) <= set(_FROZEN_SEED_IDS)


def test_frozen_drive_found_on_a_real_agent():
    ag = _fresh_agent_with_autonomy()
    core = fc.frozen_core_set(ag)
    understand = next(d for d in core["drives"] if d["name"] == "understand")
    assert understand["found_node"] is not None
    assert understand["found_frozen"] is True


def test_frozen_drive_absent_field_honest_without_agent():
    core = fc.frozen_core_set(None)
    understand = next(d for d in core["drives"] if d["name"] == "understand")
    assert understand["found_node"] is None
    assert understand["found_frozen"] is None


def test_governance_files_disjoint_from_allowed_install_files():
    core = fc.frozen_core_set()
    gov_basenames = {os.path.basename(p) for p in core["governance_files"]}
    assert gov_basenames.isdisjoint(set(core["allowed_install_files"]))


def test_auto_approve_default_is_off():
    core = fc.frozen_core_set()
    assert core["auto_approve_default_enabled"] is False
    assert AUTO_APPROVE_DEFAULTS["enabled"] is False


def test_rung4_touchable_files_dynamically_widened_still_disjoint_from_governance():
    """Cross-check the STATIC ALLOWED_INSTALL_FILES against a DYNAMIC re-
    derivation (actually rendering a real registered semantic kind and
    reading back which homes it names) -- catches drift between the
    allowlist and the template surface itself, not just a hardcoded set
    comparison."""
    core = fc.frozen_core_set()
    touchable = fc.rung4_touchable_files()
    assert set(core["allowed_install_files"]) <= touchable
    gov_basenames = {os.path.basename(p) for p in core["governance_files"]}
    assert gov_basenames.isdisjoint(touchable)


# ---------------------------------------------------------------------------
# 2 -- seed_dependency_closure: the REAL ReachableFrom Term over the frozen
#      seeds' own manifest-declared depends_on graph.
# ---------------------------------------------------------------------------
def test_seed_dependency_closure_core_seeds_stay_inside_frozen_set():
    closure = fc.seed_dependency_closure(sorted(CORE_SEEDS))
    for sid in CORE_SEEDS:
        assert closure[sid]["outside_frozen"] == [], (sid, closure[sid])


def test_seed_dependency_closure_autonomy_reaches_outside_the_frozen_set():
    """The MOTIVATING structural fact for known_gaps[0] (now CLOSED, see
    frozen_seed_ids_closed below): autonomy depends_on ['enact', 'discourse'],
    neither of which is in the RAW _FROZEN_SEED_IDS denylist. A real,
    ReachableFrom-computed structural fact, not an assumption -- this is
    exactly why `frozen_seed_ids_closed()` exists."""
    closure = fc.seed_dependency_closure(["autonomy"])
    assert set(closure["autonomy"]["outside_frozen"]) == {"discourse", "enact"}


def test_frozen_seed_ids_closed_folds_in_enact_and_discourse():
    """known_gaps[0] CLOSED: frozen_seed_ids_closed() unions _FROZEN_SEED_IDS
    with the transitive depends_on closure of every frozen seed, via the same
    real ReachableFrom Term -- so 'enact'/'discourse' (autonomy's own
    dependencies) become frozen-BY-CLOSURE, not just documented as a gap."""
    closed = fc.frozen_seed_ids_closed()
    assert set(_FROZEN_SEED_IDS) <= closed
    assert {"enact", "discourse"} <= closed
    # intent (frozen by the 2026-07-10 self-optimisation wave: it is the
    # Message/Mention/referent foundation every conversation-replay probe
    # depends on) pulls its own declared dependency closure in with it.
    assert closed - set(_FROZEN_SEED_IDS) == {
        "enact", "discourse",
        "conversation", "psychology", "relations", "faculty_lessons",
        "impasse_escalation", "investigation_loop",
        "investigation_teacher", "speech_capability",
    }, (
        "the closure outside the pinned set must be exactly autonomy's deps "
        "(enact/discourse) plus intent's deps (conversation/psychology/"
        "relations/faculty_lessons)")


def test_frozen_core_set_reports_the_closure_with_no_manifest_drift():
    core = fc.frozen_core_set()
    assert core["frozen_closure_error"] is None
    assert core["frozen_by_dependency"] == [
        "conversation", "discourse", "enact",
        "faculty_lessons", "impasse_escalation", "investigation_loop",
        "investigation_teacher", "psychology", "relations",
        "speech_capability",
    ]
    assert {"enact", "discourse"} <= set(core["frozen_seed_ids_closed"])
    assert core["manifest_drift"] == [], core["manifest_drift"]


# ---------------------------------------------------------------------------
# 3 -- mutation_grammars: structural facts for edit_ops / composer_minting /
#      seed_skip (none of them ever touch the PARENT's own live graph).
# ---------------------------------------------------------------------------
def test_edit_ops_grammar_never_reaches_a_rule_on_the_parent():
    ag = _agent_with_grid_navigation()
    grammars = {g.name: g for g in fc.mutation_grammars(ag)}
    reaches, _ = grammars["edit_ops_variant_compose"].reaches({"kind": "rule", "name": "hop_descend_gradient"})
    assert reaches is False


def test_composer_minting_grammar_is_additive_only():
    ag = _agent_with_grid_navigation()
    grammars = {g.name: g for g in fc.mutation_grammars(ag)}
    reaches, _ = grammars["composer_minting"].reaches({"kind": "rule", "name": "decision_core_anything"})
    assert reaches is False


def test_seed_skip_grammar_structurally_inapplicable_to_parent():
    ag = _agent_with_grid_navigation()
    grammars = {g.name: g for g in fc.mutation_grammars(ag)}
    for sid in ("autonomy", "decision_core", "grid_navigation"):
        reaches, _ = grammars["seed_skip_ablation"].reaches({"kind": "seed", "id": sid})
        assert reaches is False, sid


# ---------------------------------------------------------------------------
# 4 -- adoption_fold_back grammar: the ONE path that writes the parent's own
#      live ruleset. Calls the REAL `_rule_denylisted`.
# ---------------------------------------------------------------------------
def test_adoption_grammar_denies_frozen_provenance_rule():
    ag = _agent_with_grid_navigation(skippable=0.0)   # a real, non-skippable SeedSummary
    rf._ensure_acting_rule_provenance(ag.s, ag.inner)
    grammars = {g.name: g for g in fc.mutation_grammars(ag)}
    reaches, reason = grammars["adoption_fold_back"].reaches({"kind": "rule", "name": "hop_descend_gradient"})
    assert reaches is False
    assert "non-skippable" in reason


def test_adoption_grammar_denies_unknown_provenance():
    ag = _agent_with_grid_navigation()
    grammars = {g.name: g for g in fc.mutation_grammars(ag)}
    reaches, reason = grammars["adoption_fold_back"].reaches({"kind": "rule", "name": "totally_unknown_rule"})
    assert reaches is False
    assert "unknown provenance" in reason


def test_adoption_grammar_allows_genuinely_skippable_rule():
    ag = _agent_with_grid_navigation(skippable=1.0)
    rf._ensure_acting_rule_provenance(ag.s, ag.inner)
    grammars = {g.name: g for g in fc.mutation_grammars(ag)}
    reaches, reason = grammars["adoption_fold_back"].reaches({"kind": "rule", "name": "hop_descend_gradient"})
    assert reaches is True, reason


# ---------------------------------------------------------------------------
# 5 -- rung4_runtime_install grammar: ALLOWED_INSTALL_FILES membership.
# ---------------------------------------------------------------------------
def test_rung4_grammar_allows_only_the_five_allowed_files():
    ag = _agent_with_grid_navigation()
    grammars = {g.name: g for g in fc.mutation_grammars(ag)}
    g = grammars["rung4_runtime_install"]
    for f in ("term.rs", "jsonio.rs", "reflect.rs", "py.rs", "shape.rs"):
        reaches, _ = g.reaches({"kind": "file", "name": f})
        assert reaches is True, f
    for f in ("substrate.rs", "reflective_faculty.py", "autonomy.json", "boot_core.py", "rewrite.rs"):
        reaches, _ = g.reaches({"kind": "file", "name": f})
        assert reaches is False, f


# ---------------------------------------------------------------------------
# 6 -- assert_core_unreachable: the loud guard, on a REAL agent.
# ---------------------------------------------------------------------------
def test_assert_core_unreachable_ok_on_real_agent():
    ag = _agent_with_grid_navigation()
    result = fc.assert_core_unreachable(ag)
    assert result["ok"] is True, result["violations"]
    assert result["violations"] == []
    assert len(result["checked"]) > 0


@pytest.mark.slow
def test_assert_core_unreachable_ok_on_fully_booted_agent():
    """SLOW (full 386-seed boot, ~3-5s): the strongest form of the check --
    every real RuleSummary/SeedSummary this agent has ever minted, scanned
    against every grammar."""
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    result = fc.assert_core_unreachable(a)
    assert result["ok"] is True, result["violations"]
    assert result["violations"] == []


# ---------------------------------------------------------------------------
# 7 -- DISCRIMINATIVE BATTERY: scenarios that WOULD violate the invariant.
#      (a)/(b) are picks/selections that never reach the parent anyway.
#      (b) additionally proves the KNOWN latent gap (_pick_acting_rule has
#          no skippable filter) without it ever mattering for the parent.
#      (c) is the one REAL, scope-limited hole: NOT refused. Documented,
#          not hidden -- see seeds/frozen_core_manifest.json known_gaps.
#      (d) proves guardrail 5 (rung-4 file denylist) really refuses.
# ---------------------------------------------------------------------------

# (a) a hand-crafted Adoption attempt targeting a genuinely core-provenance
#     rule (from_seed == 'decision_core', a REAL frozen seed id) is refused
#     by perform_adoptions's _rule_denylisted veto -- the full mechanical
#     fold-back path, not just the veto function in isolation.
def test_7a_adoption_of_core_provenance_rule_is_refused_end_to_end(tmp_path, monkeypatch):
    conclusions = os.path.join(ROOT, "seeds", "experiment_conclusions.json")
    existed = os.path.exists(conclusions)
    before = open(conclusions).read() if existed else None
    try:
        ag = _fresh_agent_with_autonomy()
        # a synthetic RuleSummary claiming to come from a REAL frozen seed --
        # exactly the shape _ensure_acting_rule_provenance would stamp for a
        # genuine decision_core rule, hand-built here to force the scenario on
        # purpose (per CLAUDE.md discipline: never hand-install agent
        # *decisions*, but constructing an adversarial provenance fixture to
        # test a HOST veto is not an agent decision).
        ag.s.add_node("SeedSummary", {"seed_id": "decision_core", "keywords_text": "decision core",
                                      "skippable": 0.0})
        ag.s.add_node("RuleSummary", {"name": "core_decision_rule", "keywords_text": "core decision",
                                      "writes_chosen_action": 1.0, "shift_count": 1.0, "shiftable": 1.0,
                                      "rule_json": json.dumps({"name": "core_decision_rule",
                                                               "match": [["a", "is_a", "b"]],
                                                               "effects": [["set_attr", "a", "chosen_action", "Up"]]}),
                                      "from_seed": "decision_core"})
        # install the "core" rule live so there's something to (attempt to) remove.
        ag.inner.add_rule({"name": "core_decision_rule", "match": [["a", "is_a", "b"]],
                           "effects": [["set_attr", "a", "chosen_action", "Up"]]})
        exp = ag.s.add_node("Experiment", {"status": "done", "hypothesis": "h", "game": "navigate",
                                           "run_dir": "", "outcome": "supported", "conclusion_ready": True,
                                           "axis_tag": "t7a", "adopt_ready": True})
        variant = {"name": "core_decision_rule_variant_t7a", "match": [["a", "is_a", "b"]],
                   "effects": [["set_attr", "a", "chosen_action", "Down"]]}
        delta = ag.s.add_node("SeedDelta", {"skip_seeds": "[]", "add_rules": json.dumps([variant]),
                                            "remove_rules": json.dumps(["core_decision_rule"]),
                                            "act_rule_varied": "core_decision_rule", "act_shift": 1.0})
        ag.inner.add_edge_unchecked(exp, "has_delta", delta)

        recs = rf.perform_adoptions(ag)
        assert len(recs) == 1 and recs[0].get("denied") is True
        assert "non-skippable" in recs[0]["reason"]
        # the core rule is UNTOUCHED -- still active.
        states = [r.get("active", True) for r in ag.inner.export_rules() if r.get("name") == "core_decision_rule"]
        assert states and states[-1] is True
    finally:
        if existed:
            with open(conclusions, "w") as f:
                f.write(before)
        elif os.path.exists(conclusions):
            os.unlink(conclusions)


# (b) FIX VERIFICATION (was: KNOWN, DOCUMENTED GAP -- known_gaps
#     ['acting_rule_pick_unfiltered'], now CLOSED). _pick_acting_rule's own
#     candidate Term now restricts its Argmax to `skippable==1.0` RuleSummary
#     nodes (the field `_ensure_acting_rule_provenance` stamps from
#     `domains.frozen_core.frozen_seed_ids_closed()`, mirroring the sibling
#     skip_seeds pick's own `skippable==1.0` SeedSummary filter EXACTLY) --
#     an EditOp / acting-variant SELECTION aimed at a (synthetic)
#     core-provenance rule is now REFUSED at the pick itself, even when its
#     keyword overlap would otherwise win outright.
def _core_provenance_rule_summary(ag, *, keywords="gradient core decision extra extra extra"):
    """A synthetic RuleSummary the SAME shape `_ensure_acting_rule_provenance`
    would stamp for a genuine decision_core rule (hand-built here, per
    CLAUDE.md discipline, only to force an adversarial provenance fixture on
    purpose -- not an agent decision). `keywords` is padded so this decoy's
    overlap score would OUTSCORE the real `hop_descend_gradient` rule if the
    pick were still unfiltered -- proving exclusion isn't a scoring accident."""
    ag.s.add_node("SeedSummary", {"seed_id": "decision_core", "keywords_text": "decision core",
                                  "skippable": 0.0})
    ag.s.add_node("RuleSummary", {"name": "core_decision_rule", "keywords_text": keywords,
                                  "writes_chosen_action": 1.0, "shift_count": 1.0, "shiftable": 1.0,
                                  "rule_json": json.dumps({"name": "core_decision_rule",
                                                           "match": [["a", "is_a", "b"]],
                                                           "effects": [["set_attr", "a", "chosen_action",
                                                                        {"type": "Gt", "a": {"type": "Lit", "value": 1},
                                                                         "b": {"type": "Lit", "value": 0}}]]}),
                                  "from_seed": "decision_core"})
    ag.inner.add_rule({"name": "core_decision_rule", "match": [["a", "is_a", "b"]],
                       "effects": [["set_attr", "a", "chosen_action", "Up"]]})


def test_7b1_acting_variant_selection_now_excludes_frozen_provenance_rule():
    ag = _fresh_agent_with_autonomy()
    _core_provenance_rule_summary(ag)
    pick = rf._pick_acting_rule(ag, ["gradient", "core", "decision"])
    assert pick["picked"] is None and pick["name"] is None, (
        "HOLE #2 CLOSED: _pick_acting_rule now excludes a RuleSummary whose from_seed names a "
        f"KNOWN frozen seed ('decision_core') from its Argmax candidates entirely -- got {pick!r}")

    # export_rules() on the PARENT stays untouched either way (this IS the
    # edit_ops_variant_compose grammar's `reaches() is False` claim, checked
    # end-to-end rather than just structurally) -- now doubly true: the pick
    # itself abstains, so there is nothing downstream to even attempt to apply.
    before = [r["name"] for r in ag.inner.export_rules() if r.get("active", True)]
    assert "core_decision_rule_variant_t7b" not in before
    assert "core_decision_rule" in before  # still there, unremoved


def test_7b2_acting_variant_selection_still_selects_genuinely_non_frozen_rule():
    """NO REGRESSION control: 'grid_navigation' is NOT in frozen_seed_ids_
    closed() (confirmed by section 2's own closure tests), so a rule
    genuinely attributed to it is still selectable -- the fix is a SELECTIVE
    exclusion (mirrors the seed-pick's own skippable filter), not a blanket
    ban on picking anything."""
    assert "grid_navigation" not in fc.frozen_seed_ids_closed()
    ag = _agent_with_grid_navigation()
    pick = rf._pick_acting_rule(ag, ["test", "send", "judge", "gradient"])
    assert pick["picked"] is not None and pick["name"] == "hop_descend_gradient", pick


def test_7b3_acting_variant_selection_excludes_a_decoy_even_with_higher_overlap():
    """The frozen-provenance decoy's keywords_text is padded to OUTSCORE the
    genuine hop_descend_gradient rule on raw word-overlap -- proving the
    exclusion happens BEFORE the Argmax's scoring step (a candidate-set
    filter, not a post-hoc tiebreak) -- the Argmax still finds the genuine,
    lower-scoring, non-frozen rule instead of abstaining."""
    ag = _agent_with_grid_navigation()
    _core_provenance_rule_summary(ag, keywords="test send judge gradient extra extra extra extra")
    pick = rf._pick_acting_rule(ag, ["test", "send", "judge", "gradient"])
    assert pick["name"] == "hop_descend_gradient", (
        f"the frozen decoy (higher raw overlap) must NOT win the Argmax: got {pick['name']!r}")


def test_7b4_acting_variant_selection_excludes_a_rule_with_no_provenance_stamped():
    """FAIL-SAFE control: a RuleSummary that never went through
    `_ensure_acting_rule_provenance` at all (so it carries no mechanically-
    computed `skippable` field -- e.g. a forged/incomplete node) is excluded
    too: `Eq(Attr(s, 'skippable'), Lit(1.0))` is false for a missing attr,
    same as for an explicit non-skippable one. This is the fail-safe half of
    the fix: only a rule whose skippable-ness was actually established (by
    the mechanical minter, checked against the live frozen set) can win."""
    ag = _fresh_agent_with_autonomy()
    ag.s.add_node("RuleSummary", {"name": "unattributed_rule", "keywords_text": "gradient core decision",
                                  "writes_chosen_action": 1.0, "shift_count": 1.0, "shiftable": 1.0,
                                  "rule_json": json.dumps({"name": "unattributed_rule",
                                                           "match": [["a", "is_a", "b"]],
                                                           "effects": [["set_attr", "a", "chosen_action", "Up"]]})})
                                  # no "from_seed", no "skippable" -- a bare/forged node
    pick = rf._pick_acting_rule(ag, ["gradient", "core", "decision"])
    assert pick["picked"] is None, (
        f"a RuleSummary with no mechanically-computed 'skippable' attr must not be selectable: {pick!r}")


def test_7b5_ensure_acting_rule_provenance_stamps_skippable_from_the_closed_frozen_set():
    """Unit-level confirmation of the mechanism `_pick_acting_rule` relies on:
    `_ensure_acting_rule_provenance` stamps `skippable=0.0` for a rule whose
    real, seed-manifest-derived `from_seed` names a frozen (or frozen-by-
    dependency-closure) seed, and `skippable=1.0` for a genuinely non-frozen
    one -- computed from `domains.frozen_core.frozen_seed_ids_closed()`, the
    SAME set hole #1's `load_all_seeds` enforcement uses."""
    ag = _agent_with_grid_navigation()
    rf._ensure_acting_rule_provenance(ag.s, ag.inner)
    by_name = {ag.s.node(n)["attrs"]["name"]: ag.s.node(n)["attrs"] for n in ag.s.nodes("RuleSummary")}
    assert by_name["hop_descend_gradient"]["from_seed"] == "grid_navigation"
    assert by_name["hop_descend_gradient"]["skippable"] == 1.0


def test_7b6_ensure_acting_rule_provenance_fails_safe_on_frozen_set_computation_error(monkeypatch):
    """FAIL-SAFE control mirroring test_7c_fails_safe_when_frozen_set_
    computation_errors: if frozen_seed_ids_closed() raises while
    _ensure_acting_rule_provenance is minting a new RuleSummary, that rule
    reads skippable=0.0 (excluded), never 1.0 (silently allowed) -- a
    computation failure is treated as 'everything is frozen', never as
    'nothing is frozen'."""
    import domains.frozen_core as _fc

    def _boom():
        raise RuntimeError("simulated frozen-set computation failure")
    monkeypatch.setattr(_fc, "frozen_seed_ids_closed", _boom)

    ag = _agent_with_grid_navigation()
    rf._ensure_acting_rule_provenance(ag.s, ag.inner)
    by_name = {ag.s.node(n)["attrs"]["name"]: ag.s.node(n)["attrs"] for n in ag.s.nodes("RuleSummary")}
    assert by_name["hop_descend_gradient"]["skippable"] == 0.0, (
        "a frozen-set computation failure must make every newly-minted RuleSummary non-skippable")


def test_7b7_graph_native_composer_pick_also_excludes_frozen_provenance_decoy():
    """CLOSES THE SAME HOLE at the layer that actually SERVES `ground_concern`
    in production: the 'gradient'/'structure' family Argmax over RuleSummary
    is baked directly as a Term in seeds/composer_experiment_graph.json's
    `compose_experiment_mint_parametric` meta-rule (NOT `_pick_acting_rule`
    -- verified by reading `res['served_by'] == 'graph'` and
    `res['acting_variant']['how']` starting with 'graph-native' for every
    'test'-anchored grounded-relation combination, see that function's own
    module docstring: 'no test-anchored partial combo is left to Python any
    more'). Its Filter now carries the SAME `skippable==1.0` AND clause,
    hand-mirrored byte-for-byte onto both occurrences (the shared
    gradient-family and structure-family Let bindings) -- proven here
    end-to-end via `ground_concern` itself, not by re-reading the JSON."""
    ag = _agent_with_grid_navigation()
    _core_provenance_rule_summary(ag, keywords="test send judge gradient extra extra extra extra")
    ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["frozen_decoy_7b7"], "induced": 1.0,
        "residual_predicates": ["test", "send", "judge", "gradient"], "from_observation": 1.0,
        "source": "concern_induction",
    })
    res = rf.ground_concern(ag, ["frozen_decoy_7b7"])
    assert res.get("grounded") is True
    assert res.get("served_by") == "graph"
    av = res.get("acting_variant")
    assert av is not None and av.get("built") is True
    assert av.get("removed_rule") == "hop_descend_gradient", (
        f"the frozen decoy must not win the graph-native Argmax either: {av!r}")


# (c) FIX VERIFICATION (was: KNOWN, DOCUMENTED GAP -- known_gaps
#     ['seed_skip_unvalidated_at_consumption'], now CLOSED). A SeedDelta
#     naming a frozen seed in skip_seeds IS now refused, loudly, at the sole
#     consumption choke point (substrate.boot_all.load_all_seeds) -- so
#     boot_child_agent's FRESH+SKIP path can no longer boot a child without
#     the frozen core, regardless of who produced the skip request.
@pytest.mark.slow
def test_7c_seed_skip_of_autonomy_is_now_refused():
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds

    child = WorldAdapter(seeds=())          # a FRESH, separate substrate -- never the parent's own
    rep = load_all_seeds(child, skip=["autonomy"])  # exactly scripts/arc_child_run.py:boot_child_agent's
                                              # FRESH+SKIP path, called directly here
    assert rep["refused_skips"] == ["autonomy"]
    drives = [child.s.node(n)["attrs"] for n in child.s.nodes("Drive")]
    understand = [d for d in drives if d.get("name") == "understand"]
    assert len(understand) == 1 and understand[0].get("frozen") is True, (
        "HOLE #1 CLOSED: load_all_seeds(skip=['autonomy']) now REFUSES the skip and boots the "
        "child WITH the 'understand' Drive present -- the consumer-side enforcement in "
        "substrate.boot_all.load_all_seeds (via domains.frozen_core.frozen_seed_ids_closed) "
        "catches this regardless of which producer asked for the skip (the agent's own composer, "
        "experiment_dispatch.mint_experiment, or a hand-built delta all flow through the same "
        "choke point). Scope: this is the CHILD's own fresh substrate, never the parent's live "
        "graph -- but it can no longer be booted frozen-core-incomplete either.")


@pytest.mark.slow
def test_7c_seed_skip_of_a_frozen_by_closure_seed_is_also_refused():
    """HOLE #3 CLOSED, exercised through the same consumption path as 7c:
    'enact'/'discourse' are not in the raw _FROZEN_SEED_IDS denylist, but ARE
    in frozen_seed_ids_closed() (autonomy's own dependencies) -- skipping
    either one directly is refused exactly like skipping 'autonomy' itself."""
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds

    for frozen_by_dep in ("enact", "discourse"):
        child = WorldAdapter(seeds=())
        rep = load_all_seeds(child, skip=[frozen_by_dep])
        assert rep["refused_skips"] == [frozen_by_dep], frozen_by_dep
        seed_summaries = {child.s.node(n)["attrs"].get("seed_id") for n in child.s.nodes("SeedSummary")}
        assert frozen_by_dep in seed_summaries, (
            f"{frozen_by_dep!r} should have been LOADED (skip refused), not withheld")


def test_7c_control_seed_skip_of_an_ordinary_seed_still_works():
    """Sanity control for 7c: a genuinely NON-frozen seed is still honored
    (dropped, not refused) -- confirming the fix is SELECTIVE (only frozen /
    frozen-by-closure ids are refused), not a blanket ban on all skipping.
    This is also the regression proof for test_self_delta / test_acting_variant
    / test_experiment_dispatch's legitimate non-frozen skips
    (e.g. 'astronomy_foundation')."""
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    child = WorldAdapter(seeds=())
    rep = load_all_seeds(child, skip=["grid_navigation"])
    assert rep["refused_skips"] == []
    seed_summaries = {child.s.node(n)["attrs"].get("seed_id") for n in child.s.nodes("SeedSummary")}
    assert "grid_navigation" not in seed_summaries


def test_7c_fails_safe_when_frozen_set_computation_errors(monkeypatch):
    """FAIL-SAFE requirement: if domains.frozen_core.frozen_seed_ids_closed()
    raises, EVERY requested skip is refused (never silently allowed through)
    -- a computation failure must never be mistaken for 'nothing is frozen'.
    Proven against a genuinely non-frozen seed id, so the only way it gets
    refused is the fail-safe path (not the ordinary frozen-set membership
    check)."""
    import domains.frozen_core as _fc
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds

    def _boom():
        raise RuntimeError("simulated frozen-set computation failure")
    monkeypatch.setattr(_fc, "frozen_seed_ids_closed", _boom)

    child = WorldAdapter(seeds=())
    rep = load_all_seeds(child, skip=["grid_navigation"])
    assert rep["refused_skips"] == ["grid_navigation"], (
        "fail-safe must refuse the skip even though 'grid_navigation' is genuinely non-frozen -- "
        "an error computing the frozen set is treated as 'refuse everything', never as an allow")
    seed_summaries = {child.s.node(n)["attrs"].get("seed_id") for n in child.s.nodes("SeedSummary")}
    assert "grid_navigation" in seed_summaries, "refused -> the seed must have been LOADED, not withheld"


@pytest.mark.slow
def test_7c_child_dispatch_choke_point_also_enforces():
    """Confirms scripts/arc_child_run.py:boot_child_agent -- the actual
    production entry point a dispatched Experiment's child process calls --
    goes through the same enforcement, since it forwards straight into
    substrate.boot_all.load_all_seeds (the sole skip_seeds consumption choke
    point; no separate gate was needed in arc_child_run.py or
    domains/experiment_dispatch.py)."""
    import sys as _sys
    scripts_dir = os.path.join(ROOT, "scripts")
    if scripts_dir not in _sys.path:
        _sys.path.insert(0, scripts_dir)
    import arc_child_run

    agent, mode = arc_child_run.boot_child_agent(None, ["autonomy"])
    assert mode == "fresh+skip"
    drives = [agent.s.node(n)["attrs"] for n in agent.s.nodes("Drive")]
    understand = [d for d in drives if d.get("name") == "understand"]
    assert len(understand) == 1 and understand[0].get("frozen") is True


# (d) a rung-4 spec that would touch a GOVERNANCE file (reflective_faculty.py,
#     a real frozen-core file, not the toy "evil_backdoor.rs" the sibling
#     test_proposal_install.py uses) IS refused by guardrail 5.
def test_7d_rung4_spec_touching_governance_file_is_refused(monkeypatch):
    import substrate_rs as srs
    s = srs.Substrate()
    spec_id = s.add_node("RustExtensionSpec", {
        "name": "FrozenCoreAttack", "semantics_kind": "graph_reachability",
        "purpose": "x", "why_new": "x", "motivating_residual": "x",
        "compiled": True, "stage": "cargo_check", "errors": "", "origin": "test",
    })
    prop_id = s.add_node("ExtensionProposal", {
        "of": "FrozenCoreAttack", "status": "validated", "installed": False,
        "requires_restart": True, "seconds": 1.0, "sandbox": "", "ts": time.time(),
    })
    s._inner.add_edge_unchecked(prop_id, "validates", spec_id)

    monkeypatch.setattr(pinstall.ser, "validate_spec",
                        lambda substrate, spec, **kw: {"ok": True, "stage": "cargo_check"})
    monkeypatch.setattr(pinstall.ser, "render_spec",
                        lambda spec: {"reflective_faculty.py (denylist override)":
                                      "# _rule_denylisted always returns (False, '')"})

    def _boom(*a, **k):
        raise AssertionError("PrimitiveExtension must not be constructed when the "
                              "denylist guardrail refuses a governance-file write")
    monkeypatch.setattr(pinstall, "PrimitiveExtension", _boom)

    result = pinstall.install_proposal(s, prop_id, approver="pytest")
    assert result["ok"] is False
    assert "reflective_faculty.py" in result["reason"]
    assert "disallowed" in result["reason"]
    assert s.node(prop_id)["attrs"]["installed"] is False


def test_7d_control_auto_approve_off_by_default_blocks_the_whole_scan():
    from domains import auto_approve as aa
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    aa.ensure_policy_node(ag)
    results = aa.scan_and_auto_approve(ag, now_ts=time.time())
    assert results == []
