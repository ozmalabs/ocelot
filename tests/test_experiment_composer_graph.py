"""test_experiment_composer_graph — the EXPERIMENT composer's graph-resident
migration (seeds/composer_experiment_graph.json + `domains.reflective_
faculty._route_experiment_composer`, dispatched from `_try_graph_composer`'s
`if composer_name == "experiment":` branch).

Companion to tests/test_composers_graph.py (the cross-composer migration
gate, which now documents `experiment` as PARTIALLY migrated) and
tests/test_dialect_experiment_terms.py (the dialect-gap closure this
migration relies on: `ToJsonString`/`FromJsonString`/`ShiftThresholdLits`/
`DictGet`, plus the pilot proof that a graph-native Argmax(RuleSummary) ->
FromJsonString -> ShiftThresholdLits -> ToJsonString chain reproduces
`_shift_rule_thresholds`'s output byte-for-byte).

What's migrated (`seeds/composer_experiment_graph.json`'s own docstring has
the full account): 7 grounded-relation combinations --
  - judge alone       -> judge_experiment_outcome_<tag>
  - adopt alone        -> mark_adopt_ready_<tag>
  - test alone         -> author_experiment_from_residual_<tag> (no send/vary)
  - test+send+judge+gradient+adopt (the standing self-improvement concern's
    OWN relation set -- the autonomy-gate combo) -> all three rules, with
    the mint rule's SeedDelta carrying a graph-native GRADIENT acting-variant
    (Argmax over RuleSummary provenance -> shift, baked once at compose
    time -- the exact operation the dialect-gap pilot proves).
  - test+vary+send+judge (bare vary, no embed) -> mint+judge, the SeedDelta's
    skip_seeds/skip_seed_id a Term DEFERRED to the minted mint-rule's OWN
    future fire time (reading axis.residual_predicates -- the shape
    tests/test_dialect_experiment_terms.py's pilot already proved reusable).
  - test+vary+send+judge+embed -> mint+judge, PLUS a graph-native
    judge-variant embedded into the mint rule's SeedDelta.add_rules, its
    threshold EAGERLY computed at compose time from cr.residual_predicates
    (Count/Div), baked into the variant's own IfThenElse as a Lit.
  - test+send+judge+structure+gradient ('structure' takes priority, same as
    the Python oracle) -> mint+judge, PLUS a graph-native STRUCTURAL variant:
    a two-stage Argmax (RuleSummary then EditOp, both over
    cr.residual_predicates) picks WHICH acting rule and WHICH of
    flip_comparison / drop_match_edge / add_match_guard / swap_term_leaf,
    applied via RewriteTreeNodes / ListDrop+guard / IndexAt+MkDict /
    AttrKeyRanking+Count-guard+IndexAt+MkDict+RewriteTreeNodes (the exact
    chains tests/test_editop_dialect_terms.py's pilots prove byte-identical
    to domains.edit_ops's own appliers) -- ALL FOUR EditOp kinds are now
    graph-native, so this combo is served_by='graph' unconditionally, not
    per-request.

RESIDUAL CLOSED (was 'swap_term_leaf''s SITE -- the top-2 MOST-REFERENCED
Attr keys in a rule's effects, by frequency -- had no graph-native "collect
distinct field values + rank by frequency" Term; `RewriteTreeNodes` only
REWRITES matching nodes in place, it doesn't accumulate a frequency table).
Closed by the `AttrKeyRanking` Term (term.rs): it walks the SAME Dict/Tuple
tree `RewriteTreeNodes` walks, tallies every `{"type":"Attr"}` node's `key`
field occurrence, and returns a `(-count, key)`-sorted ranked Tuple,
IDENTICAL to `domains/edit_ops.py`'s `find_attr_keys`. The router
(`_route_experiment_composer`) no longer pre-checks-and-declines on a swap
pick. Any OTHER partial mix (a bare 'vary' with no 'test', 'gradient'/
'structure' without their required co-relations, ...) still returns None
from the router and falls through to `_compose_experiment_rule`, unchanged
-- that is the only remaining Python residual, and it is a genuinely
different (unmigrated combo) shape, not an EditOp-family gap.
tests/test_composers_graph.py's own
`test_experiment_unmigrated_combos_router_declines` /
`test_experiment_migrated_combos_router_serves_graph` pin the router-level
ledger; this file does not re-test it at that level (it drives the real
`ground_concern` production seam instead).

Per CLAUDE.md's discipline: no test here hand-writes the minted rules' JSON.
Structural-equivalence tests compare the graph-minted rule against
`domains.reflective_faculty._compose_experiment_rule`'s OWN Python output
for the identical grounded-relation input (the oracle, imported read-only,
never modified) -- modulo the one difference the task brief calls out
(name suffixes / the `served_by` ledger). Behavioral tests fire the minted
rules for real and read the resulting graph state.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from substrate.rule_ir import rules_semantically_equal
import domains.reflective_faculty as rf

_CONCLUSIONS_SEED = os.path.join(ROOT, "seeds", "experiment_conclusions.json")


@pytest.fixture(autouse=True)
def _experiment_conclusions_seed_guard():
    """teach()-in-close_experiment_loop touches this seed file for real (same
    guard shape tests/test_self_delta.py / tests/test_acting_variant.py /
    tests/test_adoption.py already use) -- snapshot + restore so this file
    leaves no residue on a full-suite run."""
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
    """Minimal duck-typed agent wrapper -- identical shape to
    tests/test_experiment_composer.py's / tests/test_acting_variant.py's
    own `_Agent` (harness glue only, no source modified)."""
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
    return ag


def _norm_effects(effects):
    """Same normalization tests/test_composers_graph.py's own `_norm_effects`
    applies: `export_rules()`'s Rust round-trip always makes an attrs-less
    `add_edge`'s trailing `{}` explicit, which the Python builders' bare
    4-element literal never carries -- an engine-canonicalization detail,
    not authored content. Duplicated here (not imported) because tests/ has
    no package `__init__.py` for cross-file imports; same small helper,
    same reasoning."""
    out = []
    for e in (effects or []):
        if isinstance(e, list) and len(e) == 4 and e[0] == "add_edge":
            out.append(e + [{}])
        else:
            out.append(e)
    return out


def _axis(ag, tag, preds):
    return ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": [tag], "induced": 1.0,
        "residual_predicates": preds, "from_observation": 1.0, "source": "concern_induction",
    })


# ---------------------------------------------------------------------------
# SECTION 1 -- the served_by ledger, per combo (truthful both ways).
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("preds,expect_served_by", [
    (["judge"], "graph"),
    (["adopt"], "graph"),
    (["test"], "graph"),
    (["vary", "send", "judge"], "graph"),           # no 'test' -- vary/send are INERT without it; judge alone fires
    (["judge", "adopt"], "graph"),                  # no 'test' -- both meta-rules fire, judge then adopt
    (["vary", "judge", "adopt"], "graph"),          # no 'test' -- vary INERT; judge+adopt fire
    (["test", "vary", "send", "judge"], "graph"),                # bare vary -- MIGRATED
    (["test", "vary", "send", "judge", "embed"], "graph"),       # embed (judge-variant) -- MIGRATED
    # THE RESIDUAL THIS (parametric mint rule) COMMIT CLOSES: these two used
    # to fall to Python (no meta-rule minted these exact 4/4-relation combos);
    # compose_experiment_mint_parametric mints for ANY 'test'-anchored combo.
    (["test", "send", "judge", "gradient"], "graph"),           # no 'adopt' -- NOW graph
    (["test", "send", "judge", "structure"], "graph"),           # no explicit 'gradient' -- NOW graph
])
def test_served_by_ledger_truthful_per_combo(preds, expect_served_by):
    ag = _fresh_agent_with_lexicon()
    tag = "ledger_" + "_".join(preds)
    _axis(ag, tag, preds)
    res = rf.ground_concern(ag, [tag])
    assert res.get("grounded") is True
    assert res.get("served_by") == expect_served_by, (preds, res.get("served_by"))
    assert res.get("path") == "compose_experiment_rule"


def test_served_by_ledger_full_combo_is_graph():
    """The FULL combo needs grid_navigation loaded (so RuleSummary provenance
    exists for the gradient Argmax to pick from) -- otherwise identical to
    the ledger test above, split out because of that fixture difference."""
    ag = _agent_with_grid_navigation()
    _axis(ag, "ledger_full", ["test", "send", "judge", "gradient", "adopt"])
    res = rf.ground_concern(ag, ["ledger_full"])
    assert res.get("grounded") is True
    assert res.get("served_by") == "graph"
    assert res.get("path") == "compose_experiment_rule"
    names = {r["name"] for r in res.get("rules", [])}
    assert names == {"author_experiment_from_residual_ledger_full",
                      "judge_experiment_outcome_ledger_full",
                      "mark_adopt_ready_ledger_full"}


def test_served_by_ledger_structure_combo_is_graph_for_flip():
    """The structure combo (test+send+judge+structure+gradient) is served by
    the graph path when the EditOp Argmax genuinely picks a graph-native op
    (flip/drop/guard) -- needs grid_navigation for RuleSummary provenance."""
    ag = _agent_with_grid_navigation()
    _axis(ag, "ledger_struct_flip", ["test", "send", "judge", "structure", "gradient", "flip"])
    res = rf.ground_concern(ag, ["ledger_struct_flip"])
    assert res.get("grounded") is True
    assert res.get("served_by") == "graph"
    assert res.get("structural_variant", {}).get("kind") == "flip_comparison"


def test_served_by_ledger_structure_combo_is_graph_for_swap():
    """The SAME combo shape, with the residual genuinely naming 'swap' --
    swap_term_leaf's SITE (top-2-most-referenced Attr keys) is now
    graph-native too (the AttrKeyRanking Term closes the residual
    documented in composer_experiment_graph.json's own description), so
    the router no longer pre-checks-and-declines: served_by='graph' for
    EVERY EditOp kind in the structure combo, not just flip/drop/guard."""
    ag = _agent_with_grid_navigation()
    _axis(ag, "ledger_struct_swap", ["test", "send", "judge", "structure", "gradient", "swap"])
    res = rf.ground_concern(ag, ["ledger_struct_swap"])
    assert res.get("grounded") is True
    assert res.get("served_by") == "graph"
    assert res.get("structural_variant", {}).get("kind") == "swap_term_leaf"
    assert res.get("structural_variant", {}).get("built") is True


# ---------------------------------------------------------------------------
# SECTION 2 -- STRUCTURAL EQUIVALENCE: graph-minted rule vs the Python
# oracle (_compose_experiment_rule), for the same grounded-relation input.
# ---------------------------------------------------------------------------
def test_judge_alone_structurally_matches_python_oracle():
    # TWO SEPARATE agents -- the oracle call below `add_rule`s live, and
    # `__mint__` idempotently skips a rule whose NAME already exists; using
    # one shared agent for both sides would let a stale oracle-installed
    # rule silently satisfy the graph path's `expected_names` check without
    # the meta-rule having minted anything at all. Same tag on two disjoint
    # agents keeps the comparison apples-to-apples without that false
    # positive.
    tag = "struct_judge"
    rels = [("judge", "TRIAL", "by", "RESULT")]
    oracle_agent = _fresh_agent_with_lexicon()
    oracle = rf._compose_experiment_rule(oracle_agent, [tag], rels)
    assert oracle.get("grounded") is True
    oracle_rule = oracle["rules"][0]

    ag = _fresh_agent_with_lexicon()
    _axis(ag, tag, ["judge"])
    graph_res = rf.ground_concern(ag, [tag])
    assert graph_res.get("served_by") == "graph"
    graph_rule = graph_res["rules"][0]

    assert graph_rule["name"] == oracle_rule["name"] == "judge_experiment_outcome_" + tag
    assert graph_rule["match"] == oracle_rule["match"]
    assert graph_rule["where"] == oracle_rule["where"]
    assert _norm_effects(graph_rule["effects"]) == _norm_effects(oracle_rule["effects"])


def test_adopt_alone_structurally_matches_python_oracle():
    tag = "struct_adopt"
    rels = [("adopt", "WINNER", "as", "SELF")]
    oracle_agent = _fresh_agent_with_lexicon()
    oracle = rf._compose_experiment_rule(oracle_agent, [tag], rels)
    oracle_rule = oracle["rules"][0]

    ag = _fresh_agent_with_lexicon()
    _axis(ag, tag, ["adopt"])
    graph_res = rf.ground_concern(ag, [tag])
    assert graph_res.get("served_by") == "graph"
    graph_rule = graph_res["rules"][0]

    assert graph_rule["name"] == oracle_rule["name"] == "mark_adopt_ready_" + tag
    assert graph_rule["match"] == oracle_rule["match"]
    assert graph_rule["where"] == oracle_rule["where"]
    assert _norm_effects(graph_rule["effects"]) == _norm_effects(oracle_rule["effects"])


def test_test_alone_structurally_matches_python_oracle():
    tag = "struct_test"
    rels = [("test", "HYPOTHESIS", "about", "SELF")]
    oracle_agent = _fresh_agent_with_lexicon()
    oracle = rf._compose_experiment_rule(oracle_agent, [tag], rels)
    oracle_rule = oracle["rules"][0]

    ag = _fresh_agent_with_lexicon()
    _axis(ag, tag, ["test"])
    graph_res = rf.ground_concern(ag, [tag])
    assert graph_res.get("served_by") == "graph"
    graph_rule = graph_res["rules"][0]

    assert graph_rule["name"] == oracle_rule["name"] == "author_experiment_from_residual_" + tag
    assert rules_semantically_equal(graph_rule, oracle_rule)


def test_minted_rule_is_scoped_to_the_requested_capability_axis():
    """A composer request must not author a rule that tests some other live gap.

    The tag is inserted into the graph-authored predicate by the meta-rule's
    RewriteTreeNodes term; this is a behavioral gate for that dynamic compile,
    not merely an oracle-shape comparison.
    """
    ag = _fresh_agent_with_lexicon()
    requested = "scope_requested"
    _axis(ag, requested, ["test"])
    res = rf.ground_concern(ag, [requested])
    assert res.get("served_by") == "graph"

    wrong = _axis(ag, "scope_other", ["test"])
    ag.s.set_attr(wrong, "description", "a different capability gap")
    obs = ag.s.add_node("Obs", {})
    ag.inner.add_edge_unchecked(ag.agent, "observed", obs)
    ag.inner.add_edge_unchecked(obs, "minted", wrong)
    ag.inner.run_rules()

    assert list(ag.inner.neighbours(wrong, "tested_by")) == []


# ---------------------------------------------------------------------------
# SECTION 2b -- THE RESIDUAL THIS COMMIT CLOSES: no-'test' combos where
# vary/send/gradient/structure/embed are grounded ALONGSIDE judge/adopt but
# are INERT in the Python oracle (nested entirely under `if "test" in rp:`,
# which never executes without 'test'). The router now fires the judge
# and/or adopt meta-rule for exactly the grounded subset and drops the
# rest -- these tests pin that the graph output is IDENTICAL to the Python
# oracle's for representative decorated combos, and that the genuine
# no-authoring walls ({vary}, {send}, {vary,send}) are NOT fabricated.
# ---------------------------------------------------------------------------
def test_vary_send_judge_no_test_structurally_matches_python_oracle():
    """{vary, send, judge} WITHOUT 'test' -- vary/send are inert (no mint
    rule exists to refine), so the Python oracle's ONLY authored output is
    the judge rule, byte-identical to judge-alone's own oracle output."""
    tag = "no_test_vsj"
    rels = [("vary", "SEED", "by", "DELTA"), ("send", "V", "to", "W"), ("judge", "T", "by", "O")]
    oracle_agent = _fresh_agent_with_lexicon()
    oracle = rf._compose_experiment_rule(oracle_agent, [tag], rels)
    assert oracle.get("grounded") is True
    assert {r["name"] for r in oracle["rules"]} == {"judge_experiment_outcome_" + tag}
    oracle_rule = oracle["rules"][0]

    ag = _fresh_agent_with_lexicon()
    _axis(ag, tag, ["vary", "send", "judge"])
    graph_res = rf.ground_concern(ag, [tag])
    assert graph_res.get("served_by") == "graph"
    assert graph_res.get("path") == "compose_experiment_rule"
    assert {r["name"] for r in graph_res["rules"]} == {"judge_experiment_outcome_" + tag}
    graph_rule = graph_res["rules"][0]

    assert graph_rule["name"] == oracle_rule["name"]
    assert graph_rule["match"] == oracle_rule["match"]
    assert graph_rule["where"] == oracle_rule["where"]
    assert _norm_effects(graph_rule["effects"]) == _norm_effects(oracle_rule["effects"])


def test_judge_adopt_no_test_structurally_matches_python_oracle():
    """{judge, adopt}, no 'test' -- the Python oracle authors BOTH rules
    (judge then adopt, no interaction between them); the router fires both
    meta-rules and concatenates in the same order."""
    tag = "no_test_ja"
    rels = [("judge", "T", "by", "O"), ("adopt", "WINNER", "as", "SELF")]
    oracle_agent = _fresh_agent_with_lexicon()
    oracle = rf._compose_experiment_rule(oracle_agent, [tag], rels)
    assert oracle.get("grounded") is True
    oracle_by_name = {r["name"]: r for r in oracle["rules"]}
    assert set(oracle_by_name) == {"judge_experiment_outcome_" + tag, "mark_adopt_ready_" + tag}

    ag = _fresh_agent_with_lexicon()
    _axis(ag, tag, ["judge", "adopt"])
    graph_res = rf.ground_concern(ag, [tag])
    assert graph_res.get("served_by") == "graph"
    assert [r["name"] for r in graph_res["rules"]] == [
        "judge_experiment_outcome_" + tag, "mark_adopt_ready_" + tag]  # judge-then-adopt order, same as oracle
    graph_by_name = {r["name"]: r for r in graph_res["rules"]}

    for name in oracle_by_name:
        assert graph_by_name[name]["match"] == oracle_by_name[name]["match"]
        assert graph_by_name[name]["where"] == oracle_by_name[name]["where"]
        assert _norm_effects(graph_by_name[name]["effects"]) == _norm_effects(oracle_by_name[name]["effects"])


def test_vary_judge_adopt_no_test_structurally_matches_python_oracle():
    """{vary, judge, adopt}, no 'test' -- vary is inert; same judge+adopt
    pair as the combo above, just decorated with an extra inert relation."""
    tag = "no_test_vja"
    rels = [("vary", "SEED", "by", "DELTA"), ("judge", "T", "by", "O"), ("adopt", "WINNER", "as", "SELF")]
    oracle_agent = _fresh_agent_with_lexicon()
    oracle = rf._compose_experiment_rule(oracle_agent, [tag], rels)
    assert oracle.get("grounded") is True
    oracle_by_name = {r["name"]: r for r in oracle["rules"]}
    assert set(oracle_by_name) == {"judge_experiment_outcome_" + tag, "mark_adopt_ready_" + tag}

    ag = _fresh_agent_with_lexicon()
    _axis(ag, tag, ["vary", "judge", "adopt"])
    graph_res = rf.ground_concern(ag, [tag])
    assert graph_res.get("served_by") == "graph"
    graph_by_name = {r["name"]: r for r in graph_res["rules"]}
    assert set(graph_by_name) == set(oracle_by_name)

    for name in oracle_by_name:
        assert graph_by_name[name]["match"] == oracle_by_name[name]["match"]
        assert graph_by_name[name]["where"] == oracle_by_name[name]["where"]
        assert _norm_effects(graph_by_name[name]["effects"]) == _norm_effects(oracle_by_name[name]["effects"])


@pytest.mark.parametrize("preds", [["vary"], ["send"], ["vary", "send"]])
def test_no_authoring_no_test_combos_wall_identically_both_paths(preds):
    """{vary}, {send}, {vary, send} -- NEITHER judge nor adopt grounded, so
    NEITHER path authors anything: the router must return None (an honest
    miss, never a fabricated rule) and `ground_concern` must fall through to
    `_compose_experiment_rule`'s own `grounded: False` wall, with the SAME
    wall message the Python-only caller would see."""
    tag = "wall_" + "_".join(preds)
    rels = [(p, "X", "Y", "Z") for p in preds]

    oracle_agent = _fresh_agent_with_lexicon()
    oracle = rf._compose_experiment_rule(oracle_agent, [tag], rels)
    assert oracle.get("grounded") is False
    assert "wall" in oracle

    router_res = rf._try_graph_composer(_fresh_agent_with_lexicon(), "experiment", [tag],
                                         rels, set(preds))
    assert router_res is None, "router must not fabricate a rule for a no-authoring combo"

    ag = _fresh_agent_with_lexicon()
    _axis(ag, tag, preds)
    graph_res = rf.ground_concern(ag, [tag])
    assert graph_res.get("grounded") is False
    assert graph_res.get("wall") == oracle.get("wall")
    # ground_concern's own PATH 1.5 stamps served_by="python" on WHATEVER the
    # Python builder returns (via `setdefault`) once the graph router honestly
    # declines -- truthful either way: this IS the Python builder's wall, not
    # a graph fabrication, so served_by="python" is the correct ledger entry.
    assert graph_res.get("served_by") == "python"


# ---------------------------------------------------------------------------
# SECTION 3 -- the FULL combo's gradient embed: the graph-native Argmax +
# ShiftThresholdLits chain must pick the SAME acting rule and produce the
# SAME shifted-threshold variant `_compose_acting_variant`/
# `_shift_rule_thresholds` would (checked on the REAL FIRED delta node, not
# the unfired rule template -- ToJsonString's Value::Surface wire
# representation only collapses to a plain Python str once a real SetAttr
# effect application stores it on a live node's attrs, exactly the same
# storage path tests/test_dialect_experiment_terms.py's pilot already
# proves; reading the un-fired COMPILED rule's own effect literal back via
# export_rules() shows the Surface wrapper instead, which is a template-
# export representation detail, not a behavioral difference).
# ---------------------------------------------------------------------------
def test_full_combo_gradient_embed_matches_shift_rule_thresholds_oracle():
    ag = _agent_with_grid_navigation()
    tag = "full_grad"
    axis = _axis(ag, tag, ["test", "send", "judge", "gradient", "adopt"])
    res = rf.ground_concern(ag, [tag])
    assert res.get("served_by") == "graph"
    av = res.get("acting_variant")
    assert av is not None and av.get("built") is True
    assert av.get("removed_rule") == "hop_descend_gradient"
    assert av.get("shift") == 5.0          # Count(["test","send","judge","gradient","adopt"]) == 5, unscaled

    # fire the mint rule for real: ag--observed-->obs--minted-->axis, +knows->wi.
    obs = ag.s.add_node("Obs", {})
    ag.inner.add_edge_unchecked(ag.agent, "observed", obs)
    ag.inner.add_edge_unchecked(obs, "minted", axis)
    ag.s.set_attr(axis, "description", "a concern induced from an observation "
                                        "no held term-shape covers: full_grad")
    wi = ag.s.add_node("WorldInstance", {"world_type": "Game", "world_id": "game", "name": "navigate"})
    ag.inner.add_edge_unchecked(ag.agent, "knows", wi)
    ag.inner.run_rules()

    exp = next(iter(ag.inner.neighbours(axis, "tested_by")), None)
    assert exp is not None
    ea = ag.s.node(exp)["attrs"]
    assert ea.get("status") == "requested"
    assert ea.get("epistemic_scope") == "external"
    assert ea.get("game") == "navigate"

    deltas = list(ag.inner.neighbours(exp, "has_delta"))
    assert len(deltas) == 1
    da = ag.s.node(deltas[0])["attrs"]
    assert isinstance(da.get("add_rules"), str), "must be a genuine JSON STRING on the real fired node"
    assert da.get("remove_rules") == json.dumps(["hop_descend_gradient"])
    assert da.get("act_rule_varied") == "hop_descend_gradient"
    assert da.get("act_shift") == 5.0

    add_rules = json.loads(da["add_rules"])
    assert len(add_rules) == 1
    graph_variant = add_rules[0]
    assert graph_variant["name"] == "hop_descend_gradient_variant_" + tag

    # the Python reference oracle -- `_shift_rule_thresholds` applied to the
    # SAME source `_compose_acting_variant`'s own Python pick reads: the
    # EXPORTED/compiled RuleSummary.rule_json (native.export_rules()'s own
    # round trip), NOT the raw seeds/grid_navigation.json source text --
    # `native.export_rules()`'s compile+export round trip does not claim to
    # preserve every default-valued optional Term field byte-for-byte
    # (e.g. a NodesOfType's default `any_type: false`), and that is a
    # pre-existing property of the runtime shared identically by BOTH the
    # graph-native path and `_compose_acting_variant` itself (both read
    # `RuleSummary.rule_json`) -- comparing against the raw seed file would
    # penalize this migration for a gap that predates it.
    rs = next(n for n in ag.s.nodes("RuleSummary") if ag.s.node(n)["attrs"].get("name") == "hop_descend_gradient")
    exported_rule_json = json.loads(ag.s.node(rs)["attrs"]["rule_json"])
    python_reference = rf._shift_rule_thresholds(exported_rule_json, 5.0, "hop_descend_gradient_variant_" + tag)
    assert python_reference.pop("active", None) is None

    assert rules_semantically_equal(graph_variant, python_reference), (
        f"graph-native:\n{json.dumps(graph_variant, indent=2)}\n\n"
        f"python reference:\n{json.dumps(python_reference, indent=2)}")


def test_full_combo_gradient_abstains_honestly_without_any_acting_rule():
    """No grid_navigation loaded -> no RuleSummary provenance exists -> the
    graph-native Argmax abstains, exactly like `_compose_acting_variant`
    does -- an honest null, never a fabricated variant."""
    ag = _fresh_agent_with_lexicon()          # NO grid_navigation
    tag = "full_grad_none"
    _axis(ag, tag, ["test", "send", "judge", "gradient", "adopt"])
    res = rf.ground_concern(ag, [tag])
    assert res.get("served_by") == "graph"
    av = res.get("acting_variant")
    assert av is not None and av.get("built") is False
    assert "wall" in av

    mint = {r["name"]: r for r in res["rules"]}["author_experiment_from_residual_" + tag]
    delta_attrs = mint["effects"][1][3]
    # un-fired template representation: Surface-wrapped, but decodes to "[]".
    assert json.loads(_surface_or_str(delta_attrs.get("add_rules"))) == []
    assert json.loads(_surface_or_str(delta_attrs.get("remove_rules"))) == []


def _surface_or_str(v):
    """The un-fired rule TEMPLATE's own literal effect args round-trip a
    ToJsonString result as a `{"__surface__": ..., "payload": <hex>}` wire
    blob (see the module docstring above) rather than a plain Python str --
    decode either representation to the JSON string it carries."""
    if isinstance(v, str):
        return v
    if isinstance(v, dict) and "payload" in v:
        return bytes.fromhex(v["payload"]).decode("utf-8")
    raise AssertionError(f"unexpected add_rules/remove_rules representation: {v!r}")


# ---------------------------------------------------------------------------
# SECTION 4 -- BEHAVIORAL: judge-alone and adopt-alone fire for real via the
# graph-minted rule (same scenarios tests/test_experiment_composer.py /
# tests/test_adoption.py exercise against the Python builder).
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("score,frames,expected", [
    (1, 5, "supported"),
    (-2, 5, "refuted"),
    (0, 5, "inconclusive"),
])
def test_judge_alone_graph_rule_judges_outcome(score, frames, expected):
    ag = _fresh_agent_with_lexicon()
    tag = "beh_judge"
    _axis(ag, tag, ["judge"])
    res = rf.ground_concern(ag, [tag])
    assert res.get("served_by") == "graph"

    exp = ag.s.add_node("Experiment", {"status": "running", "hypothesis": "h", "game": "navigate", "run_dir": ""})
    run = ag.s.add_node("Run", {"run_id": "r", "game": "navigate", "status": "done",
                                "frames": frames, "score": score})
    ag.inner.add_edge_unchecked(exp, "produced", run)
    ag.inner.run_rules()
    assert ag.s.node(exp)["attrs"].get("outcome") == expected
    assert ag.s.node(exp)["attrs"].get("conclusion_ready") is True

    # idempotent.
    ag.inner.run_rules()
    assert ag.s.node(exp)["attrs"].get("outcome") == expected


def test_test_alone_graph_rule_mints_experiment_without_host_add_node():
    ag = _fresh_agent_with_lexicon()
    tag = "beh_test"
    axis = _axis(ag, tag, ["test"])
    ag.s.set_attr(axis, "description", "a concern induced from an observation "
                                        "no held term-shape covers: beh_test")
    res = rf.ground_concern(ag, [tag])
    assert res.get("served_by") == "graph"

    obs = ag.s.add_node("Obs", {})
    ag.inner.add_edge_unchecked(ag.agent, "observed", obs)
    ag.inner.add_edge_unchecked(obs, "minted", axis)
    ag.inner.run_rules()

    exp = next(iter(ag.inner.neighbours(axis, "tested_by")), None)
    assert exp is not None
    ea = ag.s.node(exp)["attrs"]
    assert ea.get("status") == "counterfactual_requested"
    assert ea.get("epistemic_scope") == "graph_counterfactual"
    assert ea.get("game") == ""                     # 'send' NOT grounded in this combo
    assert ea.get("axis_tag") == tag

    before = set(ag.s.nodes("Experiment"))
    ag.inner.run_rules()
    assert set(ag.s.nodes("Experiment")) == before   # idempotent


def test_adopt_alone_graph_rule_marks_adopt_ready():
    ag = _fresh_agent_with_lexicon()
    tag = "beh_adopt"
    _axis(ag, tag, ["adopt"])
    res = rf.ground_concern(ag, [tag])
    assert res.get("served_by") == "graph"

    exp = ag.s.add_node("Experiment", {"status": "done", "hypothesis": "h", "game": "navigate",
                                       "run_dir": "", "outcome": "supported"})
    delta = ag.s.add_node("SeedDelta", {"add_rules": "[]", "remove_rules": "[]", "skip_seeds": "[]",
                                        "act_rule_varied": "hop_descend_gradient", "act_shift": 4.0})
    ag.inner.add_edge_unchecked(exp, "has_delta", delta)
    ag.inner.run_rules()
    assert ag.s.node(exp)["attrs"].get("adopt_ready") is True


def test_adopt_alone_graph_rule_abstains_without_genuine_variant():
    """A SeedDelta with an EMPTY act_rule_varied (no genuine acting-variant --
    e.g. a bare judge-variant/skip_seeds-only delta) must NOT be marked
    adopt_ready, exactly matching the Python mark_adopt_ready_* rule's own
    guard."""
    ag = _fresh_agent_with_lexicon()
    tag = "beh_adopt_no"
    _axis(ag, tag, ["adopt"])
    res = rf.ground_concern(ag, [tag])
    assert res.get("served_by") == "graph"

    exp = ag.s.add_node("Experiment", {"status": "done", "hypothesis": "h", "game": "navigate",
                                       "run_dir": "", "outcome": "supported"})
    delta = ag.s.add_node("SeedDelta", {"add_rules": "[]", "remove_rules": "[]", "skip_seeds": "[]",
                                        "act_rule_varied": ""})
    ag.inner.add_edge_unchecked(exp, "has_delta", delta)
    ag.inner.run_rules()
    assert ag.s.node(exp)["attrs"].get("adopt_ready") is not True


# ---------------------------------------------------------------------------
# SECTION 5 -- close_experiment_loop / perform_adoptions still consume
# graph-minted Experiments correctly (the host-mechanical outcome->teach/
# adopt I/O these tests must NOT need to change -- CLAUDE.md's "keep
# close_experiment_loop/perform_adoptions working unchanged" requirement).
# ---------------------------------------------------------------------------
def test_close_experiment_loop_teaches_a_graph_minted_conclusion(tmp_path):
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    tag = "close_loop_graph"
    axis = a.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": [tag], "induced": 1.0,
        "residual_predicates": ["judge"], "from_observation": 1.0, "source": "concern_induction",
    })
    res = rf.ground_concern(a, [tag])
    assert res.get("served_by") == "graph"

    exp = a.s.add_node("Experiment", {"status": "running", "hypothesis": "h", "game": "navigate",
                                      "run_dir": "", "axis_tag": tag})
    run = a.s.add_node("Run", {"run_id": "r", "game": "navigate", "status": "done", "frames": 5, "score": 1})
    a.inner.add_edge_unchecked(exp, "produced", run)
    a.inner.run_rules()
    assert a.s.node(exp)["attrs"].get("conclusion_ready") is True

    recs = rf.close_experiment_loop(a)
    # teach()'s own return shape is {node, seed, category, saved, local_id}
    # (domains/teach.py) -- the taught CONTENT (topic/hypothesis/answer)
    # lives on the returned `node`'s own attrs, not on the record dict.
    taught_nodes = [r["node"] for r in recs if isinstance(r, dict) and "node" in r]
    assert taught_nodes, recs
    topics = [a.s.node(n)["attrs"].get("topic") for n in taught_nodes if a.s.has_node(n)]
    assert any(tag in str(t) for t in topics), topics
    assert a.s.node(exp)["attrs"].get("taught") is True


# ---------------------------------------------------------------------------
# SECTION 6 -- bare-VARY and EMBED: structural equivalence (graph-minted vs
# the Python oracle, _compose_experiment_rule) + behavioral (real fire).
# ---------------------------------------------------------------------------
def _norm_match(match):
    """export_rules()'s matcher groups a compiled rule's match edges by
    src_var (a pre-existing engine canonicalization -- reproduced identically
    on the ALREADY-migrated full-combo's own 3-edge match, nothing new here);
    compare as a multiset, not list order."""
    return sorted(tuple(e) for e in (match or []))


def test_vary_bare_structurally_matches_python_oracle():
    tag = "struct_vary"
    rels = [("test", "H", "about", "S"), ("vary", "SEED", "by", "DELTA"),
            ("send", "V", "to", "W"), ("judge", "T", "by", "O")]
    oracle_agent = _fresh_agent_with_lexicon()
    _axis(oracle_agent, tag, ["test", "vary", "send", "judge"])
    oracle = rf._compose_experiment_rule(oracle_agent, [tag], rels)
    assert oracle.get("grounded") is True
    oracle_mint = next(r for r in oracle["rules"] if r["name"] == "author_experiment_from_residual_" + tag)
    oracle_judge = next(r for r in oracle["rules"] if r["name"] == "judge_experiment_outcome_" + tag)

    ag = _fresh_agent_with_lexicon()
    _axis(ag, tag, ["test", "vary", "send", "judge"])
    graph_res = rf.ground_concern(ag, [tag])
    assert graph_res.get("served_by") == "graph"
    graph_mint = next(r for r in graph_res["rules"] if r["name"] == "author_experiment_from_residual_" + tag)
    graph_judge = next(r for r in graph_res["rules"] if r["name"] == "judge_experiment_outcome_" + tag)

    assert rules_semantically_equal(graph_mint, oracle_mint)
    assert graph_judge["match"] == oracle_judge["match"]
    assert graph_judge["where"] == oracle_judge["where"]
    assert _norm_effects(graph_judge["effects"]) == _norm_effects(oracle_judge["effects"])
    # both sides carry the trivial (un-fired-Argmax-template) delta shape --
    # the SeedDelta's own skip_seeds Argmax is a Term deferred to the mint
    # rule's own future fire (checked behaviorally below, not here).
    graph_delta = graph_mint["effects"][1][3]
    oracle_delta = oracle_mint["effects"][1][3]
    assert graph_delta.get("add_rules") == "[]" == oracle_delta.get("add_rules")


def test_vary_bare_graph_rule_fires_and_picks_skip_seeds():
    """Behavioral: fire the graph-minted mint rule for real on a substrate
    that carries a genuinely-overlapping skippable SeedSummary -- the
    skip_seeds Argmax (deferred to the mint rule's own fire time) must pick
    it, exactly like the Python oracle's 'vary' branch would."""
    ag = _fresh_agent_with_lexicon()
    tag = "beh_vary"
    axis_preds = ["test", "vary", "send", "judge", "astronomy"]
    ax = _axis(ag, tag, axis_preds)
    ag.s.set_attr(ax, "description", "a concern induced from an observation: " + tag)
    ag.s.add_node("SeedSummary", {"seed_id": "astronomy_foundation",
                                  "keywords_text": "astronomy stars planets", "skippable": 1.0})
    res = rf.ground_concern(ag, [tag])
    assert res.get("served_by") == "graph"

    obs = ag.s.add_node("Obs", {})
    ag.inner.add_edge_unchecked(ag.agent, "observed", obs)
    ag.inner.add_edge_unchecked(obs, "minted", ax)
    wi = ag.s.add_node("WorldInstance", {"world_type": "Game", "world_id": "game", "name": "navigate"})
    ag.inner.add_edge_unchecked(ag.agent, "knows", wi)
    ag.inner.run_rules()

    exp = next(iter(ag.inner.neighbours(ax, "tested_by")), None)
    assert exp is not None
    ea = ag.s.node(exp)["attrs"]
    assert ea.get("status") == "requested" and ea.get("game") == "navigate"
    deltas = list(ag.inner.neighbours(exp, "has_delta"))
    da = ag.s.node(deltas[0])["attrs"]
    assert da.get("varied") == 1.0
    assert da.get("skip_seed_id") == "astronomy_foundation"
    assert da.get("skip_seeds") == json.dumps(["astronomy_foundation"])
    assert da.get("add_rules") == "[]", "no 'embed' grounded -> no variant embedded"


def test_embed_structurally_matches_python_oracle():
    tag = "struct_embed"
    rels = [("test", "H", "about", "S"), ("vary", "SEED", "by", "DELTA"), ("send", "V", "to", "W"),
            ("judge", "T", "by", "O"), ("embed", "V", "as", "R")]
    oracle_agent = _fresh_agent_with_lexicon()
    _axis(oracle_agent, tag, ["test", "vary", "send", "judge", "embed"])
    oracle = rf._compose_experiment_rule(oracle_agent, [tag], rels)
    assert oracle.get("grounded") is True
    oracle_mint = next(r for r in oracle["rules"] if r["name"] == "author_experiment_from_residual_" + tag)
    oracle_delta = oracle_mint["effects"][1][3]
    oracle_variant = json.loads(oracle_delta["add_rules"])[0]

    ag = _fresh_agent_with_lexicon()
    _axis(ag, tag, ["test", "vary", "send", "judge", "embed"])
    graph_res = rf.ground_concern(ag, [tag])
    assert graph_res.get("served_by") == "graph"
    graph_mint = next(r for r in graph_res["rules"] if r["name"] == "author_experiment_from_residual_" + tag)
    graph_delta = graph_mint["effects"][1][3]
    graph_variant = json.loads(_surface_or_str(graph_delta["add_rules"]))[0]

    assert graph_variant["name"] == oracle_variant["name"] == "judge_experiment_outcome_variant_" + tag
    assert graph_variant["match"] == oracle_variant["match"]
    assert graph_variant["where"] == oracle_variant["where"]
    assert _norm_effects(graph_variant["effects"]) == _norm_effects(oracle_variant["effects"])


def test_embed_graph_rule_fires_and_embeds_a_real_variant():
    ag = _fresh_agent_with_lexicon()
    tag = "beh_embed"
    axis_preds = ["test", "vary", "send", "judge", "embed"]
    ax = _axis(ag, tag, axis_preds)
    ag.s.set_attr(ax, "description", "a concern induced from an observation: " + tag)
    res = rf.ground_concern(ag, [tag])
    assert res.get("served_by") == "graph"

    obs = ag.s.add_node("Obs", {})
    ag.inner.add_edge_unchecked(ag.agent, "observed", obs)
    ag.inner.add_edge_unchecked(obs, "minted", ax)
    wi = ag.s.add_node("WorldInstance", {"world_type": "Game", "world_id": "game", "name": "navigate"})
    ag.inner.add_edge_unchecked(ag.agent, "knows", wi)
    ag.inner.run_rules()

    exp = next(iter(ag.inner.neighbours(ax, "tested_by")), None)
    assert exp is not None
    deltas = list(ag.inner.neighbours(exp, "has_delta"))
    da = ag.s.node(deltas[0])["attrs"]
    add_rules = json.loads(da["add_rules"])
    assert len(add_rules) == 1
    variant = add_rules[0]
    assert variant["name"] == "judge_experiment_outcome_variant_" + tag
    assert variant["match"] == [["exp", "produced", "run"]]
    # shift = Count(5 residual preds) / 10.0 = 0.5, baked in as a literal
    inner = variant["effects"][0][3]["__term__"]
    assert inner["cond"]["b"]["value"] == 0.5
    assert inner["other"]["cond"]["b"]["value"] == -0.5


# ---------------------------------------------------------------------------
# SECTION 7 -- STRUCTURE: structural equivalence (graph-minted variant vs
# domains.edit_ops's own appliers -- the applier IS the oracle for this
# family, same discipline test_editop_dialect_terms.py already pins) +
# behavioral (real fire on the grid_navigation seed's hop_descend_gradient).
# ---------------------------------------------------------------------------
from domains import edit_ops as _eo  # noqa: E402  (import after module setup, matches file's own style)


def _grid_agent_with_edit_ops():
    ag = _agent_with_grid_navigation()
    from domains.reflective_faculty import _ensure_edit_ops, _ensure_acting_rule_provenance
    _ensure_edit_ops(ag.s)
    _ensure_acting_rule_provenance(ag.s, ag.inner)
    return ag


def _hop_rule_json(ag):
    for n in ag.s.nodes("RuleSummary"):
        if ag.s.node(n)["attrs"].get("name") == "hop_descend_gradient":
            return json.loads(ag.s.node(n)["attrs"]["rule_json"])
    raise AssertionError("hop_descend_gradient RuleSummary not found")


def _swap_oracle(rj, name):
    """Same site-pick `_compose_structural_variant`'s swap branch makes:
    the top-2 MOST-REFERENCED Attr keys in `rj['effects']`, via the SAME
    `find_attr_keys` oracle `AttrKeyRanking` was proven byte-identical to
    (see tests/test_dialect_experiment_terms.py-style Rust unit pins in
    term.rs). Not called unless >=2 distinct keys exist -- callers only
    reach this via the parametrized oracle_fn on hop_descend_gradient,
    which genuinely has 6."""
    keys_found = _eo.find_attr_keys(rj.get("effects"))
    assert len(keys_found) >= 2, "this oracle is only meaningful with >=2 distinct Attr keys"
    old_key, new_key = keys_found[0][0], keys_found[1][0]
    return _eo.apply_swap_term_leaf(rj, old_key, new_key, name)


@pytest.mark.parametrize("cue_word,expected_kind,oracle_fn", [
    ("flip", "flip_comparison", lambda rj, name: _eo.apply_flip_comparison(rj, name)),
    ("guard", "add_match_guard",
     lambda rj, name: _eo.apply_add_match_guard(rj, "game", "adopted_variant_probe", True, name)),
    ("swap", "swap_term_leaf", _swap_oracle),
])
def test_structure_variant_matches_edit_ops_oracle(cue_word, expected_kind, oracle_fn):
    tag = "struct_" + cue_word
    ag = _grid_agent_with_edit_ops()
    _axis(ag, tag, ["test", "send", "judge", "structure", "gradient", cue_word])
    res = rf.ground_concern(ag, [tag])
    assert res.get("served_by") == "graph"
    sv = res.get("structural_variant")
    assert sv is not None and sv.get("built") is True and sv.get("kind") == expected_kind

    mint = next(r for r in res["rules"] if r["name"] == "author_experiment_from_residual_" + tag)
    delta = mint["effects"][1][3]
    add_rules = json.loads(_surface_or_str(delta["add_rules"]))
    assert len(add_rules) == 1
    variant = add_rules[0]
    assert variant["name"].startswith("hop_descend_gradient_structvariant_")

    hop_rule_json = _hop_rule_json(ag)
    oracle = oracle_fn(hop_rule_json, variant["name"])
    assert variant["match"] == oracle["match"]
    assert variant["where"] == oracle["where"], (variant["where"], oracle["where"])
    assert _norm_effects(variant["effects"]) == _norm_effects(oracle["effects"])


def test_structure_variant_drop_matches_edit_ops_oracle_on_a_multi_edge_rule():
    """flip/guard above use hop_descend_gradient (1 match edge -- drop is
    INERT on it, see the honest-null test below); drop's SUCCESS case needs
    a 2+-edge acting rule, so this pilots ListDrop directly (mirroring
    tests/test_editop_dialect_terms.py's own drop success pilot) rather than
    through the full mint-rule Argmax (which always picks hop_descend_
    gradient on this seed -- the ONLY chosen_action-writing rule)."""
    ag = _grid_agent_with_edit_ops()
    footprint = next(r for r in ag.inner.export_rules()
                      if isinstance(r, dict) and r.get("name") == "mark_visited_footprint")
    assert footprint is not None and len(footprint["match"]) == 2
    oracle = _eo.apply_drop_match_edge(footprint, 0, "mark_visited_footprint_structvariant_pilot")
    assert oracle is not None and oracle["match"] == [footprint["match"][1]]


def test_structure_variant_drop_is_honestly_inert_via_router():
    tag = "struct_drop_inert"
    ag = _grid_agent_with_edit_ops()
    _axis(ag, tag, ["test", "send", "judge", "structure", "gradient", "drop"])
    res = rf.ground_concern(ag, [tag])
    assert res.get("served_by") == "graph"
    sv = res.get("structural_variant")
    assert sv is not None and sv.get("built") is False
    assert sv.get("kind") == "drop_match_edge"
    assert "INERT" in sv.get("wall", "")

    mint = next(r for r in res["rules"] if r["name"] == "author_experiment_from_residual_" + tag)
    delta = mint["effects"][1][3]
    assert json.loads(_surface_or_str(delta["add_rules"])) == []

    oracle = _eo.apply_drop_match_edge(_hop_rule_json(ag), 0, tag)
    assert oracle is None, "hop_descend_gradient has exactly one match edge -- the Python oracle is ALSO inert"


def test_structure_variant_flip_installs_and_inverts_decision():
    """BEHAVIORAL: a flip_comparison structural-variant child must install
    cleanly (add_rule accepts it, same round-trip
    tests/test_structural_variant.py's `test_flip_comparison_round_trips_on_
    hop_descend_gradient` already pins) AND genuinely invert the decision --
    the acting rule's own effects literally flip Lt<->Gt, so the SAME scene
    (game+avatar+one frontier cell at _adist==1.0, hop_descend_gradient's
    real gate) that makes the CONTROL rule choose one direction makes the
    VARIANT choose the opposite. Evaluates each rule's own exported SetAttr
    'chosen_action' term directly against the identical bound environment
    (game/A) -- the exact Term the compiled rule would apply on a real
    match/where fire, without needing to reverse-engineer every other
    grid_navigation rule's ordering/dispatch quirks (the REAL end-to-end
    install+dispatch proof already lives in
    tests/test_structural_variant.py::test_full_structural_variant_loop_
    offline, via the actual ArcWorld/NavigateEnv scan_and_dispatch path --
    unchanged, still gated)."""
    ag = _grid_agent_with_edit_ops()
    tag = "struct_flip_behavior"
    _axis(ag, tag, ["test", "send", "judge", "structure", "gradient", "flip"])
    res = rf.ground_concern(ag, [tag])
    sv = res.get("structural_variant")
    assert sv.get("built") is True and sv.get("kind") == "flip_comparison"
    mint = next(r for r in res["rules"] if r["name"] == "author_experiment_from_residual_" + tag)
    delta = mint["effects"][1][3]
    variant = json.loads(_surface_or_str(delta["add_rules"]))[0]

    # install the variant on a SEPARATE scratch substrate -- same shape
    # tests/test_structural_variant.py's own round-trip pilot uses.
    var_ag = _agent_with_grid_navigation()
    var_idx = var_ag.inner.add_rule(variant)
    assert isinstance(var_idx, int)
    var_exported = next(r for r in var_ag.inner.export_rules()
                         if isinstance(r, dict) and r.get("name") == variant["name"])

    hop_rule_json = _hop_rule_json(ag)

    # a real scene matching hop_descend_gradient's own gate (match: game
    # -reached-> A, where A.is_avatar_cell==1; effects: Argmin over 'reached'
    # neighbours filtered by n._adist+0==1.0 and n._epoch+0==game.flood_epoch+0,
    # i.e. the ONE frontier cell hop_descend_gradient's own flood-fill mints).
    game = ag.s.add_node("Game", {"flood_epoch": 0.0, "nav_mode": ""})
    a_cell = ag.s.add_node("Cell", {"row": 2.0, "col": 2.0, "is_avatar_cell": 1.0})
    goal = ag.s.add_node("Cell", {"row": 5.0, "col": 2.0, "_adist": 1.0, "_epoch": 0.0})
    ag.inner.add_edge_unchecked(game, "reached", a_cell)
    ag.inner.add_edge_unchecked(game, "reached", goal)
    env = {"game": game, "A": a_cell}

    ctrl_action = ag.inner.evaluate(hop_rule_json["effects"][0][3]["__term__"], env)
    var_action = ag.inner.evaluate(var_exported["effects"][0][3]["__term__"], env)
    assert ctrl_action, "control (unmodified) rule must choose SOME action"
    assert var_action, "flipped variant must ALSO choose some action (it installed cleanly)"
    assert ctrl_action != var_action, (
        f"flip_comparison must invert the decision: control={ctrl_action!r} variant={var_action!r}")


# ---------------------------------------------------------------------------
# SECTION 7 -- THE PARAMETRIC MINT RULE EQUIVALENCE MATRIX. The FIVE former
# exact-combo meta-rules (compose_experiment_mint_graph/_full_graph/
# _vary_graph/_embed_graph/_structure_graph) are RETIRED; ONE meta-rule
# (compose_experiment_mint_parametric) now mints author_experiment_from_
# residual_<tag> for ANY 'test'-anchored grounded-relation combination,
# driven by has_send/has_vary/has_judge/has_gradient/has_structure/has_embed
# flags. This matrix proves the parametric assembly matches
# `_compose_experiment_rule`'s own conditional Python assembly for the
# PREVIOUSLY-exact-5 combos (still exact) PLUS the previously-residual
# PARTIAL combos this migration closes (never minted by any graph meta-rule
# before) -- e.g. test+send+judge+gradient with no adopt, test+send+judge
# with no vary/gradient/structure at all, bare test+judge with no send, and
# structure/gradient combined with vary in ways the 5 old rules never
# covered. `_norm_effects` (deep JSON-string-aware, see `_parse_json_
# strings` below) handles two independent, pre-existing serialization
# details neither of which is new content: `export_rules()`'s attrs-less
# add_edge canonicalization (`_norm_effects`'s own top-level pass, shared
# with every other test in this file) and add_rules/remove_rules being
# JSON-encoded STRINGS whose serializer (Python `json.dumps` on the oracle
# side vs the Rust `ToJsonString` Term on the graph side) may order dict
# keys differently for byte-identical CONTENT -- exactly the parse-before-
# compare approach `test_full_combo_gradient_embed_matches_shift_rule_
# thresholds_oracle` above already established for this exact reason.
# ---------------------------------------------------------------------------
def _parse_json_strings(v):
    """Recursively parse any string that looks like JSON (add_rules/
    remove_rules) so structural comparison is by CONTENT, not by incidental
    key-order in the JSON text a different serializer produced."""
    if isinstance(v, str) and v[:1] in ("[", "{"):
        try:
            return _parse_json_strings(json.loads(v))
        except Exception:
            return v
    if isinstance(v, dict):
        return {k: _parse_json_strings(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_parse_json_strings(x) for x in v]
    return v


def _norm_effects_deep(effects):
    return _parse_json_strings(_norm_effects(effects))


def _norm_match(match):
    """export_rules()'s matcher groups a compiled rule's match edges by
    src_var (a pre-existing engine canonicalization, reproduced identically
    on ANY __mint__'d rule with a multi-edge match, not new to this
    migration -- see this file's own `_norm_match` above); compare as a
    multiset, not list order."""
    return sorted(tuple(e) for e in (match or []))


# (combo, needs_grid) -- needs_grid=True installs grid_navigation so a
# RuleSummary/EditOp Argmax has real provenance to pick from (gradient/
# structure); needs_grid=False combos never reference gradient/structure.
_EQUIV_MATRIX = [
    # --- the previously-exact 5, still exact under the parametric rule ---
    ("mint_alone", ["test"], False),
    ("full_autonomy_gate", ["test", "send", "judge", "gradient", "adopt"], True),
    ("bare_vary", ["test", "vary", "send", "judge"], True),
    ("embed", ["test", "vary", "send", "judge", "embed"], True),
    ("structure_flip", ["test", "send", "judge", "structure", "gradient", "flip"], True),
    ("structure_swap", ["test", "send", "judge", "structure", "gradient", "swap"], True),
    ("structure_guard", ["test", "send", "judge", "structure", "gradient", "guard"], True),
    # --- the residual THIS migration closes: never minted by any exact
    #     per-combo meta-rule before, now graph-native via the flags ---
    ("send_only", ["test", "send"], False),
    ("gradient_no_adopt", ["test", "send", "judge", "gradient"], True),
    ("judge_no_variant", ["test", "send", "judge"], False),
    ("bare_judge_no_send", ["test", "judge"], False),
    ("structure_no_send_no_adopt", ["test", "judge", "structure", "flip"], True),
    ("vary_no_send", ["test", "vary", "judge"], False),
    ("vary_plus_structure", ["test", "vary", "judge", "structure", "flip"], True),
    ("vary_embed_plus_gradient", ["test", "vary", "embed", "judge", "gradient"], True),
]


@pytest.mark.parametrize("label,preds,needs_grid", _EQUIV_MATRIX, ids=[m[0] for m in _EQUIV_MATRIX])
def test_parametric_mint_matches_python_oracle_matrix(label, preds, needs_grid):
    tag = "matrix_" + label
    rels = [(p, "X", "Y", "Z") for p in preds]

    oracle_agent = _agent_with_grid_navigation() if needs_grid else _fresh_agent_with_lexicon()
    if needs_grid:
        rf._ensure_acting_rule_provenance(oracle_agent.s, oracle_agent.inner)
        rf._ensure_edit_ops(oracle_agent.s)
    _axis(oracle_agent, tag, list(preds))
    oracle = rf._compose_experiment_rule(oracle_agent, [tag], rels)
    assert oracle.get("grounded") is True, (label, oracle)
    oracle_by_name = {r["name"]: r for r in oracle["rules"]}

    ag = _agent_with_grid_navigation() if needs_grid else _fresh_agent_with_lexicon()
    _axis(ag, tag, list(preds))
    graph_res = rf.ground_concern(ag, [tag])
    assert graph_res.get("served_by") == "graph", (label, graph_res.get("served_by"))
    assert graph_res.get("path") == "compose_experiment_rule"
    graph_by_name = {r["name"]: r for r in graph_res["rules"]}

    assert set(graph_by_name) == set(oracle_by_name), (label, set(graph_by_name), set(oracle_by_name))
    for name in oracle_by_name:
        g, o = graph_by_name[name], oracle_by_name[name]
        assert rules_semantically_equal(g, o), (
            label, name, json.dumps(_norm_effects_deep(g["effects"])),
            json.dumps(_norm_effects_deep(o["effects"])))


def test_parametric_mint_router_never_falls_through_for_any_test_anchored_combo():
    """served_by ledger, generalized: EVERY combo in the equivalence matrix
    above is graph-served (no exceptions) -- the router's own honest-miss
    path (`return None`) is now reserved for combos that ground NEITHER
    test, judge, NOR adopt (see test_no_authoring_no_test_combos_wall_
    identically_both_paths above), not for any partial 'test'-anchored
    mix."""
    for label, preds, needs_grid in _EQUIV_MATRIX:
        tag = "ledger2_" + label
        ag = _agent_with_grid_navigation() if needs_grid else _fresh_agent_with_lexicon()
        if needs_grid:
            rf._ensure_acting_rule_provenance(ag.s, ag.inner)
            rf._ensure_edit_ops(ag.s)
        _axis(ag, tag, list(preds))
        res = rf._try_graph_composer(ag, "experiment", [tag], [(p, "X", "Y", "Z") for p in preds], set(preds))
        assert res is not None and res.get("served_by") == "graph", (label, preds)
