"""test_arc_goals_migrated — ARC-GRAIN GOAL MINTING (`AG1`–`AG6`).

Design: `PROGRAM_SYNTHESIS_ARC6_ARC_GOALS_DESIGN.md`.
Results: `PROGRAM_SYNTHESIS_ARC6_ARC_GOALS.md`.
Seed:    `seeds/arc_goals.json` (emitted by `tools/build_arc_goals_seed.py`).

WHAT THIS GATES.  The goal-residual rung made arc 6's *refutations* graph-native
and was honest that the mechanism was left INERT: the six residuals sit at arc
grain, every `MoveCandidate` the pipeline mints is unsignatured, so the penalty
term is arithmetically `0.0` on every live candidate.  **The negative existed;
the positive did not** — no node in this tree said *"build the import oracle"*.
This suite gates the positive.

EVERY GATE IS A LIVE INVOCATION, IN BOTH DIRECTIONS.  The standing rule here is
that *a bug in the refuting direction is indistinguishable from an honest null*,
so every "does not fire" is asserted in the same scene as a "does fire".  And
per A7, a control is only admissible once it is shown CAPABLE of detecting the
difference it is used to rule out — `test_ag2_dimensionality` does that
explicitly for the dimensionless reading.

AND: assert the engine BEFORE measuring.  `_assert_engine_coherent` is a
behavioural probe of the semantics this rung depends on (the value layer),
run under `conftest.py` — a bare `python -c` from a worktree resolves the
CANONICAL tree's engine through an absolute `.pth` and reports the opposite of
the truth.

Run:
  COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \\
    pytest tests/test_arc_goals_migrated.py --confcutdir=<this worktree> -q
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import pytest  # noqa: E402
import substrate_rs as srs  # noqa: E402

from domains import arc_goal_ingest as agi  # noqa: E402
from domains import goal_residual_ingest as gri  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402

SEED_PATH = os.path.join(ROOT, "seeds", "arc_goals.json")
MBPP_FIXTURE = os.path.join(ROOT, "tests", "fixtures", "mbpp",
                            "sanitized-mbpp.json")


# =========================================================================== #
#  PRECONDITION — assert the engine, do not merely record it.
# =========================================================================== #
def _assert_engine_coherent(s):
    """The rung depends on the value layer distinguishing list from tuple.

    Naming a sha proves which binary ran, not that it was the RIGHT binary for
    the committed source.  This is behavioural.  Both-as-tuple means the value
    layer is absent and the tree is incoherent — STOP AND REPORT, never re-pin
    a bar to it.
    """
    n = s.add_node("ArcGoalEngineProbe", {"lst": [1, 2, 3], "tup": (1, 2, 3)})
    a = s.node(n)["attrs"]
    assert a["lst"] != a["tup"], (
        "VALUE LAYER ABSENT — list and tuple collapsed.  This is not this "
        "rung's result to re-pin: the tree is incoherent.  Expected engine "
        "8311d4356082…")
    return True


# =========================================================================== #
#  Scene builders.  Mechanical only.
# =========================================================================== #
def _bare(seeds=("arc_goals",)):
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    cls = s.add_node("Agent", {"is_class": True})
    s._inner.add_edge_unchecked(ag, "is_a", cls)
    for sid in seeds:
        s._inner.load_seed_manifest(manifest_for(sid), ag)
    _assert_engine_coherent(s)
    agenda = list(s.nodes("ArcAgenda"))[0]
    return s, ag, agenda


def _strip_shipped_sources(s):
    """Remove the seed's OWN mint sources so a controlled scene measures only
    what it puts in.  Scene setup, not a change to the seed."""
    for t in ("ArcSourceClaim", "ArcBlockerKey"):
        for n in list(s.nodes(t)):
            s.remove_node(n)


def _scene(seeds=("arc_goals",)):
    s, ag, agenda = _bare(seeds)
    _strip_shipped_sources(s)
    return s, ag, agenda


def _goal(s, agenda, **attrs):
    base = {"kind": "supply_blocker", "source_kind": "residual_blocker",
            "status": "minted", "reach_class_factor": 1.0,
            "novelty_bits": 0.0, "cost_bits": 0.0,
            "vocab_checked": 1.0, "vocab_explained": 1.0, "dim_checked": 1.0}
    base.update(attrs)
    g = s.add_node("ArcGoal", base)
    s._inner.add_edge_unchecked(agenda, "has_arc_goal", g)
    return g


def _residual(s, **attrs):
    base = {"stale": 0.0, "weight": 70.0, "reach_class_factor": 0.7,
            "ceiling_honest_n": 0.0, "denominator_n": 257.0}
    base.update(attrs)
    return s.add_node("GoalResidual", base)


def _sel(s):
    for n in s.nodes("ArcAgenda"):
        return s.node(n)["attrs"]
    raise AssertionError("no ArcAgenda")


def _run(s):
    return s._inner.run_rules()


def _rule_index(s, name):
    for i, r in enumerate(s._inner.export_rules()):
        r = r if isinstance(r, dict) else json.loads(r)
        if r["name"] == name:
            return i
    raise AssertionError("rule not installed: " + name)


def _code_only(path):
    """Source with every string literal and comment removed.

    A source audit that greps the raw file greps its own DOCSTRING — this one
    describes the banned calls in prose, so the naive form fails on itself.
    `ast` gives the CODE, which is the thing the audit is actually about.
    """
    import ast
    tree = ast.parse(open(path).read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            node.value = ""
    return ast.unparse(tree)


def _seed():
    with open(SEED_PATH) as fh:
        return json.load(fh)


def _seed_rule(name):
    for r in _seed()["rules"]:
        if r["name"] == name:
            return r
    raise AssertionError("no such rule in seeds/arc_goals.json: " + name)


def _walk(term, kind):
    if isinstance(term, dict):
        if term.get("type") == kind:
            yield term
        for v in term.values():
            yield from _walk(v, kind)
    elif isinstance(term, list):
        for v in term:
            yield from _walk(v, kind)


def _mentions_type(term, node_type):
    return any(t.get("node_type") == node_type
               for t in _walk(term, "NodesOfType"))


def _pool_sourced(term):
    """True when this subtree draws from the arc-goal pool (the `has_arc_goal`
    neighbourhood) — i.e. it is a RANKING source, not the penalty's own inner
    Argmax over residuals."""
    return any(t.get("edge_type") == "has_arc_goal"
               for t in _walk(term, "Neighbours"))


def _live_boot():
    """The synthesis-path boot the residuals themselves live on: the same
    seed set and the same measured facts `test_goal_residual_migrated::_boot`
    uses, plus `arc_goals`."""
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    cls = s.add_node("Agent", {"is_class": True})
    s._inner.add_edge_unchecked(ag, "is_a", cls)
    for sid in ("program_synthesis", "goal_residuals", "arc_goals"):
        s._inner.load_seed_manifest(manifest_for(sid), ag)
    s._inner.load_seed_manifest(manifest_for("math_capability_shapes"), ag)
    gri.install_facts(s, gri.probe_facts(s))
    _assert_engine_coherent(s)
    return s, ag


# =========================================================================== #
#  AG1 — THE MINT FIRES, ON A TESTABLE PREDICTION
# =========================================================================== #
def test_ag1_every_rule_in_the_seed_actually_INSTALLED():
    """AN UNKNOWN OP OR FIELD NAME IS A SILENT NO-OP, NOT A TRAP.

    The seed loader drops a rule WHOLESALE the moment any effect references an
    unknown Term — that is why `ag_dim_check_mark` exists at all.  A rule that
    silently failed to install would make every "does not fire" gate below pass
    for the wrong reason, so the inventory is asserted FIRST.
    """
    s, ag = _live_boot()
    installed = {(r if isinstance(r, dict) else json.loads(r))["name"]
                 for r in s._inner.export_rules()}
    want = {r["name"] for r in _seed()["rules"]}
    assert want <= installed, {"dropped by the loader": sorted(want - installed)}


def test_ag1_HEADLINE_the_remeasure_goal_fires_on_a_CLEAN_BOOT():
    """THE REGISTERED PREDICTION.  `arc6.verdict.row_verdict_seed_only` is
    STALE AS SHIPPED on this engine, because restoring `8311d4356082…`
    distinguishes list from tuple and so falsifies its condition
    `value_layer_list_eq_tuple == "1"`.  Nothing is injected: the boot measures
    the fact, `gr_condition_lapse` stales the residual, and `ag_mint_remeasure`
    turns the stale ceiling into an OPEN GOAL.

    That goal's content — *"the row-verdict ceiling was measured under a value
    layer that no longer exists; re-measure it"* — is a true statement about
    this tree that previously lived only in a markdown correction.
    """
    s, ag = _live_boot()
    facts = {s.node(n)["attrs"]["name"]: s.node(n)["attrs"]["value"]
             for n in s.nodes("ResidualFact")}
    assert facts["value_layer_list_eq_tuple"] == "0", (
        "the prediction rests on the value layer being PRESENT; it is not")
    _run(s)

    stale = sorted(s.node(n)["attrs"]["rid"] for n in s.nodes("GoalResidual")
                   if s.node(n)["attrs"].get("stale") == 1.0)
    assert stale == ["arc6.verdict.row_verdict_seed_only"], stale

    remeasure = [a for a in agi.arc_goals(s) if a["kind"] == "re_measure"]
    assert [a["agid"] for a in remeasure] == \
        ["arc.remeasure.arc6.verdict.row_verdict_seed_only"], remeasure
    g = remeasure[0]
    # it carries its SOURCE's signature and its MEASURED headroom, in tasks.
    assert (g["sig_seam"], g["sig_lever"], g["sig_target"]) == \
        ("row_verdict", "verdict", "mbpp_test_257")
    assert (g["headroom_n"], g["denominator_n"]) == (11.0, 15.0)
    assert g["evidence_artifact"] == "results/arc6_verdict_pricing.json"


def test_ag1_the_ANNIHILATION_TRAP_does_not_bite():
    """THE TRAP THE DESIGNER FOUND, CHECKED LIVE.

    A goal minted from residual *R* that carries *R*'s own signature would be
    charged *R*'s full weight the instant it entered the pool — mint and
    penalty would cancel and the mechanism would look inert while actually
    being self-defeating.  The re-measure goal DOES carry its source's
    signature.  It survives because the lifted matcher's `Exists` requires
    `Not(Eq(stale, 1.0))`: **a stale residual charges nothing**.

    BOTH DIRECTIONS, because "charged 0.0" is also what a broken matcher
    returns: un-stale the source and the SAME goal is charged 51.33.
    """
    s, ag = _live_boot()
    _run(s)
    g = [n for n in s.nodes("ArcGoal")
         if s.node(n)["attrs"].get("kind") == "re_measure"][0]
    pen = _seed_rule("ag_select_audit")["effects"][0][3]["__term__"]
    charged = s._inner.evaluate(pen, {"g": g})
    assert charged == 0.0, ("the mint annihilated itself: %r" % charged)

    # the refuting direction — restore the world the ceiling was measured in.
    src = [n for n in s.nodes("GoalResidual")
           if s.node(n)["attrs"]["rid"] == "arc6.verdict.row_verdict_seed_only"][0]
    s.set_attr(src, "stale", 0.0)
    assert s._inner.evaluate(pen, {"g": g}) == pytest.approx(51.333333), (
        "the matcher never charges this goal at all, so the 0.0 above proved "
        "nothing about staleness")


def test_ag1_the_retire_rule_fires_when_the_lapsed_condition_RETURNS():
    """`gr_condition_hold` is deliberately NOT latched, so a lapsed residual
    CAN come back.  When it does the re-measure goal is (a) obsolete and (b)
    suddenly charged its own source's full weight — and relying on the weight
    alone would leave a dead goal in the pool forever.

    Both directions in one scene: alive while stale, retired when not.
    """
    s, ag = _live_boot()
    _run(s)
    g = [n for n in s.nodes("ArcGoal")
         if s.node(n)["attrs"].get("kind") == "re_measure"][0]
    assert s.node(g)["attrs"]["status"] == "minted"

    # restore the fact the condition reads → gr_condition_hold un-stales it.
    for n in s.nodes("ResidualFact"):
        if s.node(n)["attrs"]["name"] == "value_layer_list_eq_tuple":
            s.set_attr(n, "value", "1")
    _run(s)
    a = s.node(g)["attrs"]
    assert a["status"] == "retired", a
    assert a["retired_because"] == "source_residual_no_longer_stale"


def test_ag1_the_MEASURED_BLOCKER_SPLIT_is_the_mint_source_not_reach_class():
    """`reach_class` alone is MEASURED nearly inert: all six residuals are
    `operator_blocked` and the structural ceiling measured
    `missing_dimension_ids: []`.  One level finer IS usable and is already on
    the node — seam A's `budget 7 / missing_dimension 4 /
    missing_structural_primitive 42` over the live-unreached 53, read
    graph-natively with `DictGet(FromJsonString(...))`, no Python parse.

    The counts are the goals' HEADROOM, in tasks.  A count of 0 mints nothing.
    """
    s, ag = _live_boot()
    _run(s)
    blockers = {a["proposed_seam"]: a["headroom_n"]
                for a in agi.arc_goals(s) if a["kind"] == "supply_blocker"}
    assert blockers == {"budget": 7, "missing_dimension": 4,
                        "missing_structural_primitive": 42}, blockers
    # and the class alone would have been inert — the control, shown capable of
    # producing a difference (it produced three distinct goals above).
    classes = {a["reach_class"] for a in agi.arc_goals(s)
               if a["kind"] == "re_measure"}
    assert classes == {"operator_blocked"}, classes


def test_ag1_the_mint_is_serialized_TWICE_OVER_and_is_idempotent():
    """Both serializers, each load-bearing for a DIFFERENT reason.

    (a) residual-level `Argmin`: two stale residuals in one pass would
        otherwise both mint, because effects apply against PRE-EFFECT reads.
    (b) condition-level `Argmin`: seam C has TWO conditions, and the edge latch
        cannot help — both bindings are collected before either effect applies.

    Then the live half: a second `run_rules` from the settled state mints
    nothing and changes nothing.
    """
    where = _seed_rule("ag_mint_remeasure")["where"]
    assert len(list(_walk(where, "Argmin"))) >= 2
    assert _mentions_type(where, "GoalResidual")

    s, ag = _live_boot()
    _run(s)
    before = json.dumps(sorted(agi.arc_goals(s), key=lambda a: a["agid"]),
                        sort_keys=True, default=str)
    n = _run(s)
    after = json.dumps(sorted(agi.arc_goals(s), key=lambda a: a["agid"]),
                       sort_keys=True, default=str)
    assert before == after, "a second pass minted or moved something"
    del n


# =========================================================================== #
#  AG2 — DIMENSIONALITY, AND WEIGHT-NOT-VETO
# =========================================================================== #
def test_ag2_HEADLINE_dimensionality_absolute_headroom_not_the_ratio():
    """`row_verdict` MUST NOT RANK EQUAL TO `ir_retarget`.

    The residual weight formula is `SCALE × factor × (1 − honest/denominator)`
    — a DIMENSIONLESS RATIO.  Right for a penalty (*how completely did this
    approach fail?*), wrong as a value, because it makes a 15-task target look
    exactly as valuable as a 257-task one.

    THE CONTROL IS SHOWN CAPABLE (A7).  The two goals below have the SAME
    ratio by construction, so the dimensionless reading returns "identical" —
    and that is only informative because the SAME instrument, reading absolute
    headroom off the SAME two nodes, separates them by 177 tasks.  A control
    that returns "identical" through a channel that cannot represent the
    distinction has measured the channel.

    BOTH DIRECTIONS: ordering follows ABSOLUTE HEADROOM, so giving the
    15-denominator goal more headroom in tasks makes it win.
    """
    s, ag, agenda = _scene()
    small = _goal(s, agenda, agid="row_verdict_like", sig_seam="row_verdict",
                  denominator_n=15.0, headroom_n=11.0)
    big = _goal(s, agenda, agid="ir_retarget_like", sig_seam="ir_retarget",
                denominator_n=257.0, headroom_n=188.4)
    _run(s)
    # the dimensionless reading: identical.
    ratio_small = 11.0 / 15.0
    ratio_big = 188.4 / 257.0
    assert round(ratio_small, 3) == round(ratio_big, 3), "scene mis-built"
    # the absolute reading, on the same nodes: 177 tasks apart, and it decides.
    assert _sel(s)["arc_sel_agid"] == "ir_retarget_like", _sel(s)
    assert _sel(s)["arc_sel_value"] == pytest.approx(188.4)

    # THE OTHER DIRECTION — it is headroom in TASKS, not the denominator.
    s2, ag2, agenda2 = _scene()
    _goal(s2, agenda2, agid="row_verdict_like", sig_seam="row_verdict",
          denominator_n=15.0, headroom_n=14.0)
    _goal(s2, agenda2, agid="ir_retarget_like", sig_seam="ir_retarget",
          denominator_n=257.0, headroom_n=10.0)
    _run(s2)
    assert _sel(s2)["arc_sel_agid"] == "row_verdict_like", _sel(s2)
    del small, big


def test_ag2_four_scenes_lifted_from_GR1():
    """The GR1 structure transfers verbatim; only the grain changes.

    | scene | expectation |
    |---|---|
    | control — no residual held           | the higher-headroom goal wins |
    | residual held on that goal's signature | the collapse FLIPS |
    | not-a-veto — raise its headroom      | it wins again WHILE STILL CHARGED |
    | look-alike differing in ONE dimension | charged exactly 0.0, SAME SCENE |
    """
    pen = _seed_rule("ag_select_audit")["effects"][0][3]["__term__"]

    # 1. control
    s, ag, agenda = _scene()
    a = _goal(s, agenda, agid="A", sig_seam="import_oracle",
              sig_lever="execution", sig_target="mbpp_live_unreached_53",
              denominator_n=53.0, headroom_n=20.0)
    _goal(s, agenda, agid="B", sig_seam="other_seam", sig_lever="proposal",
          sig_target="mbpp_test_257", denominator_n=257.0, headroom_n=10.0)
    _run(s)
    assert _sel(s)["arc_sel_agid"] == "A"
    assert _sel(s)["arc_sel_residual_penalty"] == 0.0

    # 2. hold a residual on A's signature → the collapse flips
    s, ag, agenda = _scene()
    a = _goal(s, agenda, agid="A", sig_seam="import_oracle",
              sig_lever="execution", sig_target="mbpp_live_unreached_53",
              denominator_n=53.0, headroom_n=20.0)
    _goal(s, agenda, agid="B", sig_seam="other_seam", sig_lever="proposal",
          sig_target="mbpp_test_257", denominator_n=257.0, headroom_n=10.0)
    # 4. the LOOK-ALIKE lives in this same scene, differing in exactly ONE
    #    dimension (sig_lever), so "charged 0.0" is measured alongside a
    #    non-zero charge and cannot be a matcher stuck at zero.
    look = _goal(s, agenda, agid="C", sig_seam="import_oracle",
                 sig_lever="proposal", sig_target="mbpp_live_unreached_53",
                 denominator_n=53.0, headroom_n=5.0)
    _residual(s, rid="arc6.seam_a.import_oracle", sig_seam="import_oracle",
              sig_lever="execution", sig_target="mbpp_live_unreached_53",
              weight=63.396226)
    _run(s)
    assert _sel(s)["arc_sel_agid"] == "B", _sel(s)
    assert s._inner.evaluate(pen, {"g": a}) == pytest.approx(63.396226)
    assert s._inner.evaluate(pen, {"g": look}) == 0.0, (
        "the look-alike is charged — the matcher is not discriminating")

    # 3. NOT A VETO — raise A's headroom and it wins again WHILE STILL CHARGED
    s.set_attr(a, "headroom_n", 200.0)
    _run(s)
    sel = _sel(s)
    assert sel["arc_sel_agid"] == "A", sel
    assert sel["arc_sel_residual_penalty"] == pytest.approx(63.396226), (
        "it won because the charge vanished, not because it out-earned it")
    assert sel["arc_sel_value"] == pytest.approx(200.0 - 63.396226)


def test_ag2_an_UNSIGNATURED_goal_is_charged_exactly_zero_and_PAYS_FOR_IT():
    """The `w_unsignatured` two-position test (design §12.3 — the author's own
    least-confident line).

    An `ArcGoal` with no `sig_seam` cannot be matched by ANY `GoalResidual`, so
    it escapes every refutation the agent holds.  That is measured here as
    arithmetic on the Term — and then priced: raise `w_unsignatured` and the
    unsignatured goal loses; drop it to 0 and the SAME goal wins.  A policy
    that cannot change the outcome is not a policy.
    """
    pen = _seed_rule("ag_select_audit")["effects"][0][3]["__term__"]
    s, ag, agenda = _scene()
    u = _goal(s, agenda, agid="U", denominator_n=1.0, headroom_n=30.0)
    _goal(s, agenda, agid="S", sig_seam="import_oracle", sig_lever="execution",
          sig_target="mbpp_live_unreached_53", denominator_n=53.0,
          headroom_n=20.0)
    _residual(s, rid="r", sig_seam=None, sig_lever=None, sig_target=None,
              weight=90.0)
    _run(s)
    assert s._inner.evaluate(pen, {"g": u}) == 0.0, (
        "a wildcard residual charged an unsignatured goal — it cannot, by "
        "construction, and if it does the loophole is closed for the wrong "
        "reason")
    # 30 - 25 = 5 for U;  20 - 90 = -70 for S.  U wins DESPITE the illegibility
    # cost, which is the honest reading: the cost is a price, not a ban.
    assert _sel(s)["arc_sel_agid"] == "U", _sel(s)

    pol = list(s.nodes("ArcGoalPolicy"))[0]
    s.set_attr(pol, "w_unsignatured", 200.0)
    _run(s)
    assert _sel(s)["arc_sel_agid"] == "S", (
        "w_unsignatured cannot change the outcome, so it is not a price")
    s.set_attr(pol, "w_unsignatured", 0.0)
    _run(s)
    assert _sel(s)["arc_sel_agid"] == "U"


def test_ag2_the_residual_is_a_WEIGHT_and_appears_in_NO_pool_filter():
    """The single most important structural assertion in the design.

    `GoalResidual` must appear in every ranking Argmax's VALUE, in NO Argmax
    SOURCE, and in NO `where` of the SELECTOR rules.  That is the difference
    between a weight and a veto, made structural rather than promised — the
    `test_gr3_the_penalty_is_not_a_pool_filter` form lifted to arc grain.

    `ag_ask` is NOT a selector and is deliberately out of scope here: its
    guard reads residuals precisely BECAUSE the ignorance/refutation
    distinction is its job, and it excludes no goal from the collapse.
    """
    checked = 0
    for name in ("ag_select", "ag_select_audit", "ag_select_runner_up",
                 "ag_select_margin"):
        r = _seed_rule(name)
        assert not _mentions_type(r["where"], "GoalResidual"), (
            "%s has a residual in its pool filter — that is a VETO" % name)
        # THE RANKING terms are exactly the Argmax/MaxOver whose SOURCE is the
        # arc-goal pool.  (The PENALTY subtree contains its own inner Argmax
        # over GoalResidual — that one IS the weight, and confusing the two is
        # how this gate would measure nothing.)
        for kind in ("Argmax", "MaxOver"):
            for am in _walk(r["effects"], kind):
                if not _pool_sourced(am.get("source")):
                    continue
                checked += 1
                assert not _mentions_type(am.get("source"), "GoalResidual"), (
                    "%s filters the POOL by evidence — that is a VETO" % name)
                assert _mentions_type(am.get("value"), "GoalResidual"), (
                    "%s ranks without reading the evidence at all" % name)
    assert checked == 3, (
        "the ranking-term inventory moved: ag_select's Argmax + its MaxOver, "
        "and ag_select_runner_up's Argmax. A gate that finds nothing to check "
        "passes vacuously, so the count is pinned rather than bounded (%d)"
        % checked)


def test_ag2_ties_are_reproducible_from_the_same_graph_state():
    """AN INHERITED TIE-BREAK IS A CONDITION-FREE CLAIM, and two equal-valued
    goals alternating IS the oscillation failure mode.

    MEASURED, AND STATED AS MEASURED: this engine's `Argmax` returns the
    FIRST-INSERTED node under a tie.  A LEXICAL tie-break is not expressible
    with the shipped Term set (no string-ordering primitive; `sorted`-on-strings
    is a known-unfixed defect here), so `ArcGoalPolicy.tie_break` records the
    measured behaviour — `insertion_order_stable` — rather than a lexical claim
    the seed cannot honour.  What IS gated is the property the failure mode
    needs: the same graph state yields the same winner, and re-running does not
    alternate.
    """
    def build(order):
        s, ag, agenda = _scene()
        for agid in order:
            _goal(s, agenda, agid=agid, sig_seam=agid,
                  denominator_n=50.0, headroom_n=25.0)
        _run(s)
        return s

    s = build(["zeta", "alpha", "mid"])
    first = _sel(s)["arc_sel_agid"]
    for _ in range(3):
        _run(s)
        assert _sel(s)["arc_sel_agid"] == first, "the winner ALTERNATES"
    assert build(["zeta", "alpha", "mid"])._inner is not None
    assert _sel(build(["zeta", "alpha", "mid"]))["arc_sel_agid"] == first
    assert list(s.node(n)["attrs"]["tie_break"]
                for n in s.nodes("ArcGoalPolicy")) == \
        ["insertion_order_stable"]


def test_ag2_the_cheap_goal_probe_does_NOT_capture_the_collapse():
    """§8.3's designed probe, read live.  The four `not_ingested` claims are
    the CHEAPEST goals available, so if the collapse converged on them the
    value term would be wrong — and that is observable rather than argued.

    Measured on the shipped graph: they rank LAST, because absolute headroom
    denominates value in the thing that matters and a 1-task claim cannot
    out-earn a 42-task blocker.
    """
    s, ag = _live_boot()
    _run(s)
    assert _sel(s)["arc_sel_source_kind"] != "not_ingested", _sel(s)
    assert _sel(s)["arc_sel_agid"] == \
        "arc.supply.arc6.seam_a.import_oracle.missing_structural_primitive"


# =========================================================================== #
#  AG3 — THE VOCABULARY EXTENDS, ONCE, AND TERMINATES
# =========================================================================== #
def test_ag3_HEADLINE_unrecognised_token_mints_exactly_one_then_is_RECOGNISED():
    """The sd loop's own headline gate shape, at arc grain.

    OOV token with a resolving artifact path → mint EXACTLY ONE
    `SignatureVocab` → `arc_vocab_epoch` bumps → `ag_revocab` re-arms →
    `ag_vocab_recognize` recognises it → a second pass mints NOTHING, and a
    SECOND goal proposing the SAME token is recognised at rung 1 with
    `novelty_bits == 0` (which is the whole point of a shared vocabulary).
    """
    s, ag, agenda = _scene()
    g = _goal(s, agenda, agid="G", proposed_seam="wire_typing",
              evidence_artifact="results/arc6_tier0.json",
              evidence_path="type_collapse.mechanism",
              denominator_n=53.0, headroom_n=42.0,
              vocab_checked=0.0, vocab_explained=0.0, dim_checked=0.0)
    _run(s)
    assert agi.minted_vocab(s) == ["wire_typing"]
    assert _sel(s)["arc_vocab_epoch"] == 1.0
    a = s.node(g)["attrs"]
    assert (a["sig_seam"], a["vocab_explained"], a["novelty_bits"]) == \
        ("wire_typing", 1.0, 8.0)

    # a second pass mints nothing and TERMINATES.
    assert _run(s) >= 0
    assert agi.minted_vocab(s) == ["wire_typing"]

    # a SECOND goal proposing the same token is RECOGNISED, not re-minted.
    h = _goal(s, agenda, agid="H", proposed_seam="wire_typing",
              evidence_artifact="results/arc6_tier0.json",
              evidence_path="type_collapse.mechanism",
              denominator_n=53.0, headroom_n=5.0,
              vocab_checked=0.0, vocab_explained=0.0, dim_checked=0.0)
    _run(s)
    assert agi.minted_vocab(s) == ["wire_typing"], "re-minted a held token"
    assert s.node(h)["attrs"]["novelty_bits"] == 0.0, (
        "a recognised token was priced as novel")


def test_ag3_no_artifact_path_mints_ZERO_and_is_LEGIBLY_refused():
    """PROVENANCE IS THE REAL BOUND: the vocabulary grows only as fast as
    MEASUREMENT grows.  Without a resolving `evidence_path` the mint is refused
    and the goal reaches the terminal `unsourced` status — legibly, so *"the
    agent wanted a word it could not source"* is a readable fact and a
    candidate ask region, not a silent drop.

    BOTH DIRECTIONS in one scene: the sourced twin mints.
    """
    s, ag, agenda = _scene()
    bad = _goal(s, agenda, agid="BAD", proposed_seam="unsourced_token",
                denominator_n=10.0, headroom_n=5.0,
                vocab_checked=0.0, vocab_explained=0.0, dim_checked=0.0)
    good = _goal(s, agenda, agid="GOOD", proposed_seam="sourced_token",
                 evidence_artifact="results/arc6_a_ceiling.json",
                 evidence_path="ceilings._definition.cherry_picked_concept",
                 denominator_n=10.0, headroom_n=5.0,
                 vocab_checked=0.0, vocab_explained=0.0, dim_checked=0.0)
    _run(s)
    assert agi.minted_vocab(s) == ["sourced_token"], agi.minted_vocab(s)
    a = s.node(bad)["attrs"]
    assert a["status"] == "unsourced"
    assert a["vocab_refused_because"] == \
        "no_measured_artifact_path_for_the_proposed_token"
    assert a.get("sig_seam") is None, "an unsourced token entered the signature"
    assert s.node(good)["attrs"]["sig_seam"] == "sourced_token"


def test_ag3_two_unrecognised_tokens_in_ONE_PASS_mint_exactly_one():
    """The `pcon_mint` `Argmin` serializer.  Without it BOTH mint before either
    sees the other, because this engine applies effects against PRE-EFFECT
    reads (snapshot-drain).  Asserted at the PASS level — `apply_rule_batch`
    on the mint rule alone — because `run_rules` is a fixpoint and would drain
    both regardless.
    """
    s, ag, agenda = _scene()
    for agid, tok in (("G1", "token_one"), ("G2", "token_two")):
        _goal(s, agenda, agid=agid, proposed_seam=tok,
              evidence_artifact="results/arc6_a_ceiling.json",
              evidence_path="ceilings._definition.cherry_picked_concept",
              denominator_n=10.0, headroom_n=5.0,
              vocab_checked=1.0, vocab_explained=0.0, dim_checked=1.0)
    idx = _rule_index(s, "ag_vocab_mint")
    s._inner.apply_rule_batch(idx)
    assert len(agi.minted_vocab(s)) == 1, agi.minted_vocab(s)
    s._inner.apply_rule_batch(idx)
    assert sorted(agi.minted_vocab(s)) == ["token_one", "token_two"]


def test_ag3_the_ALIAS_TABLE_ships_empty_and_no_rule_uses_string_similarity():
    """Specificity must be AUTHORED and AUDITABLE, never emergent from string
    overlap.  Seam C's loose variant "recognised" 245 of 257 tasks by substring
    and its cue set matched `turn` inside `reTURNs`; Seam D degenerated into
    per-task lookup keys (36/36 authored, LOO 0/36).  An alias table that grows
    per goal is the same failure — and because it is a countable set of nodes,
    it is VISIBLE while it happens.
    """
    d = _seed()
    assert [n for n in d["nodes"] if n["type"] == "SeamAlias"] == []
    tbl = [n for n in d["nodes"] if n["type"] == "SeamAliasTable"]
    assert tbl and tbl[0]["attrs"]["n_aliases"] == 0.0

    banned = {"StringIndexOf", "StringSlice", "Tokenize", "Tokenize2",
              "CaseFold", "SnakeCase", "MorphHead", "MorphTail", "StructSim"}

    def scan(o, rule_name):
        if isinstance(o, dict):
            assert o.get("type") not in banned, (
                "%s decides on a string-similarity Term (%s) — Seam C's "
                "failure mode" % (rule_name, o.get("type")))
            for v in o.values():
                scan(v, rule_name)
        elif isinstance(o, list):
            for v in o:
                scan(v, rule_name)

    for r in d["rules"]:
        scan(r.get("where"), r["name"])
        scan(r.get("effects"), r["name"])


def test_ag3_a_MINTED_token_is_audited_by_the_LIVE_graph_not_the_manifest():
    """THE AUDIT MUST BE RE-POINTED (design §5.3).  The moment a rule can mint
    a `SignatureVocab`, an audit that reads the MANIFEST's list is un-auditing
    the minted ones BY CONSTRUCTION — which is worse than having no audit.

    This is the scope EXTENSION, run over the LIVE node set: every minted token
    carries a `provenance`, an `evidence_artifact` and an `evidence_path`, and
    no minted token is a long verbatim substring of any MBPP prompt (the
    `verbatim_prompt_substring_of_len_ge_12` shape, applied to the minted set).
    """
    s, ag = _live_boot()
    _run(s)
    minted = [s.node(n)["attrs"] for n in s.nodes("SignatureVocab")
              if s.node(n)["attrs"].get("minted") == 1.0]
    assert minted, "nothing minted — this audit would pass vacuously"
    for v in minted:
        assert v["provenance"] == "arc_goal_mint"
        assert v["evidence_artifact"] and v["evidence_path"]
        assert len(v["token"]) >= 6

    # THE ANTI-SEAM-D AUDIT, using seam D's own instrument, over the LIVE set.
    # A token being present in its own EVIDENCE artifact is REQUIRED (that is
    # what provenance means); the failure mode is a token lifted from a TASK
    # PROMPT, which is how Seam D's 36/36 became LOO 0/36.
    if not os.path.exists(MBPP_FIXTURE):
        pytest.skip("MBPP fixture absent")
    prompts = " || ".join(t.get("prompt", "").lower()
                          for t in json.load(open(MBPP_FIXTURE)))
    offenders = [v["token"] for v in minted
                 if len(v["token"]) >= 12
                 and v["token"].replace("_", " ").lower() in prompts]
    assert offenders == [], offenders


# =========================================================================== #
#  AG4 — THE ASK DISCRIMINATES
# =========================================================================== #
def _ask_scene(with_refutation):
    """THE DISCRIMINATING PAIR.  Same margin, two worlds.

    Adding a residual would normally MOVE the margin, which would confound the
    trigger with the ranking — so the charged goal's headroom is raised by
    exactly the charge (`w_headroom == 1`, `reach_class_factor == 1`), leaving
    every value and the margin BYTE-IDENTICAL between the two scenes.  The
    assertion below checks that, or the pair proves nothing.
    """
    s, ag, agenda = _scene()
    bump = 63.396226 if with_refutation else 0.0
    _goal(s, agenda, agid="A", sig_seam="import_oracle", sig_lever="execution",
          sig_target="mbpp_live_unreached_53",
          denominator_n=53.0, headroom_n=20.0 + bump)
    _goal(s, agenda, agid="B", sig_seam="other_seam", sig_lever="proposal",
          sig_target="mbpp_test_257", denominator_n=257.0, headroom_n=18.0)
    if with_refutation:
        _residual(s, rid="arc6.seam_a.import_oracle", sig_seam="import_oracle",
                  sig_lever="execution", sig_target="mbpp_live_unreached_53",
                  weight=63.396226)
    agi.set_measure_epoch(s, 0)
    _run(s)
    return s


def test_ag4_HEADLINE_asks_under_IGNORANCE_and_NOT_under_REFUTATION():
    """The whole point of the trigger, and the thing conflating them would hide.

    * tied under **ignorance** — nothing is held either way.  ASK: a reply is
      not redundant with anything.
    * tied under **refutation** — residuals cover the region, the evidence is
      already held, the weight decides.  DO NOT ASK: asking re-litigates a
      measurement, and a human answer would be WEAKER evidence than the ceiling
      already on the node.

    Both halves in one gate, or a trigger stuck OFF passes the negative half.
    """
    ig = _ask_scene(False)
    ref = _ask_scene(True)

    # the pair is only a pair if the RANKING is identical.
    assert _sel(ig)["arc_sel_agid"] == _sel(ref)["arc_sel_agid"] == "A"
    assert _sel(ig)["arc_sel_margin"] == pytest.approx(_sel(ref)["arc_sel_margin"])
    assert _sel(ig)["arc_sel_margin"] == pytest.approx(2.0)
    # ...and only DISCRIMINATING if the residual really is being read.
    assert _sel(ig)["arc_sel_residual_penalty"] == 0.0
    assert _sel(ref)["arc_sel_residual_penalty"] == pytest.approx(63.396226)

    assert len(agi.questions(ig)) == 1, agi.questions(ig)
    assert agi.questions(ref) == [], (
        "asked under refutation — the ask is re-litigating a held measurement")


def test_ag4_the_question_carries_the_MEASURED_NUMBERS_and_asks_for_a_REASON():
    """A yes/no question has reproduced the gate and its zero bits.

    Angluin/Mitchell, recorded in this arc's own plan: *excluding a candidate
    yields ZERO BITS*.  The emitted `Message.text` must carry both `agid`s,
    both `headroom_n`/`denominator_n` pairs as MEASURED NUMBERS, the explicit
    "I hold no measurement covering either", and an interrogative asking what
    would have to change.

    (`StringConcat` SILENTLY DROPS numeric parts — measured — so every number
    goes through `ToJsonString`.  If that regressed, this gate is what says so.)
    """
    s = _ask_scene(False)
    texts = agi.ask_texts(s)
    assert len(texts) == 1
    t = texts[0]
    for frag in ("A", "B", "20", "53", "18", "257",
                 "I hold NO non-stale measurement covering either",
                 "What would have to change", "Name a checkable condition"):
        assert frag in t, (frag, t)
    assert "?" in t


def test_ag4_one_open_question_per_region_per_MEASUREMENT_EPOCH():
    """Asking on everything is a gate with extra steps.  Re-entry is gated on
    NEW MEASUREMENT — never on graph churn — which is the `codebook_epoch`
    form, and it is what makes the loop monotone in information rather than in
    time.  An unanswered question retires: that is itself data, it says the
    loop ran without input.
    """
    s = _ask_scene(False)
    for _ in range(3):
        _run(s)
    assert len(agi.questions(s)) == 1, "churn re-asked"
    agi.bump_measure_epoch(s)
    _run(s)
    qs = agi.questions(s)
    assert len(qs) == 2, qs
    assert sorted(q["status"] for q in qs) == ["open", "unanswered_lapsed"]


def test_ag4_an_UNCONDITIONED_reply_expires_at_the_next_measurement_epoch():
    """A human answer that cannot lapse is the same lie-with-a-long-half-life
    as a condition-free residual — and an engine rebuild has already falsified
    one held condition live in this tree, unprompted.

    BOTH DIRECTIONS IN ONE GATE.  A reply naming a checkable reason gets a
    `ResidualCondition` of that kind and SURVIVES the epoch bump; a reply
    naming none gets `fact_equals(arc_measure_epoch == <epoch at reply>)` and
    is STALE at the next bump.  Zero new lapse machinery: it is
    `gr_condition_lapse` / `gr_condition_hold`, verbatim.
    """
    def scene(cond):
        s, ag, agenda = _scene(("goal_residuals", "arc_goals"))
        _goal(s, agenda, agid="A", sig_seam="new_seam_a", sig_lever="proposal",
              sig_target="mbpp_test_257", denominator_n=53.0, headroom_n=20.0)
        _goal(s, agenda, agid="B", sig_seam="new_seam_b", sig_lever="proposal",
              sig_target="mbpp_test_257", denominator_n=257.0, headroom_n=18.0)
        agi.set_measure_epoch(s, 0)
        s.add_node("ResidualFact", {"name": "some_named_reason", "value": "1"})
        _run(s)
        q = list(s.nodes("ArcQuestion"))
        assert len(q) == 1, agi.questions(s)
        if cond:
            agi.attach_reply(s, q[0], "worth it while X holds",
                             cond_kind="fact_equals",
                             cond_filter_value="some_named_reason",
                             cond_expected_str="1")
        else:
            agi.attach_reply(s, q[0], "yes, do that one")
        _run(s)
        tr = [n for n in s.nodes("GoalResidual")
              if s.node(n)["attrs"].get("evidence_kind") == "utterance"]
        assert len(tr) == 1, "the reply did not become a residual"
        return s, tr[0]

    # (a) UNCONDITIONED — expires at the next epoch.
    s, tr = scene(False)
    a = s.node(tr)["attrs"]
    assert a["stale"] == 0.0 and a["reach_class_factor"] == 0.5
    assert a["weight"] == pytest.approx(50.0)
    cond = [s.node(n)["attrs"] for n in s.nodes("ResidualCondition")
            if s.node(n)["attrs"].get("filter_value") == "arc_measure_epoch"]
    assert cond and cond[0]["expected_str"] == "0", cond
    agi.bump_measure_epoch(s)
    _run(s)
    assert s.node(tr)["attrs"]["stale"] == 1.0, (
        "an unconditioned answer outlived its epoch")

    # (b) CONDITIONED — survives the same bump, and lapses only on ITS reason.
    s, tr = scene(True)
    agi.bump_measure_epoch(s)
    _run(s)
    assert s.node(tr)["attrs"]["stale"] == 0.0, (
        "a conditioned answer expired on an epoch it never referenced — the "
        "(a) result above would then be measuring the bump, not the default")
    for n in s.nodes("ResidualFact"):
        if s.node(n)["attrs"]["name"] == "some_named_reason":
            s.set_attr(n, "value", "0")
    _run(s)
    assert s.node(tr)["attrs"]["stale"] == 1.0, (
        "the named reason was falsified and the testimony did not lapse")


def test_ag4_the_ask_NEVER_blocks_a_mint():
    """Blocking is what makes a gate.  A vocabulary mint proceeds on its OWN
    guards while the question is in flight; the reply can only re-weight
    afterwards.  (The design's §12.7 — the decision its author most wanted
    challenged.)

    Measured as a NON-INTERFERENCE property: the mint outcome is byte-identical
    with the ask enabled and with it structurally impossible (margin threshold
    0), so the ask cannot be on the mint's causal path.
    """
    def run(margin_threshold):
        s, ag, agenda = _scene()
        _goal(s, agenda, agid="A", proposed_seam="ask_race_token",
              evidence_artifact="results/arc6_a_ceiling.json",
              evidence_path="ceilings._definition.cherry_picked_concept",
              denominator_n=53.0, headroom_n=20.0,
              vocab_checked=0.0, vocab_explained=0.0, dim_checked=0.0)
        _goal(s, agenda, agid="B", sig_seam="other_seam",
              denominator_n=257.0, headroom_n=18.0)
        pol = list(s.nodes("ArcAskPolicy"))[0]
        s.set_attr(pol, "margin_threshold", margin_threshold)
        agi.set_measure_epoch(s, 0)
        _run(s)
        return s

    asked = run(100.0)
    silent = run(0.0)
    assert len(agi.questions(asked)) == 1
    assert agi.questions(silent) == []
    assert agi.minted_vocab(asked) == agi.minted_vocab(silent) == \
        ["ask_race_token"], "the ask moved the mint"


# =========================================================================== #
#  AG5 — NO REGRESSION
# =========================================================================== #
def test_ag5_the_seed_is_NOT_globbed_into_every_agent_in_the_tree():
    """`substrate/boot_all.py::_read_seeds` GLOBS `seeds/*.json` and installs
    every match at boot, so a file here is live in EVERY agent the moment it
    lands.  Phase 2 is not a tree-wide-sweep rung, so the seed ships
    `self_load_only` — honoured by `_read_seeds` (it skips the manifest) while
    `seed_loader.manifest_for` still reads it by path.

    REMOVING THAT KEY IS THE TREE-WIDE ACTIVATION and needs the paired sweep
    A5 requires.  This gate is what makes that a decision rather than an
    accident.
    """
    assert _seed()["self_load_only"] is True
    from substrate.boot_all import _read_seeds
    loaded = _read_seeds(os.path.join(ROOT, "seeds"))
    assert "arc_goals" not in loaded, (
        "the arc-goal seed is now live in every agent in the tree")
    # ...and the on-demand route still works — otherwise this is just absent.
    assert manifest_for("arc_goals")["id"] == "arc_goals"


def test_ag5_the_synthesis_path_seeds_are_UNTOUCHED():
    """The confinement claim, asserted against `HEAD` rather than promised.

    AG-2 adds a NEW rule; it does not touch `ps_move_select`.  Nothing here
    edits `seeds/program_synthesis.json`, `seeds/goal_residuals.json`,
    `seeds/gap_prioritization.json` or `seeds/stopping_policy.json` — the last
    two because their population is Python-written and adding to it has
    perturbed a gate before (`concern_to_target_bridge.json`'s own
    `_non_resident_note`: a resident copy shifted `test_gap_is_idempotent`'s
    CapabilityGap count 0→1).
    """
    prefix = subprocess.run(["git", "-C", ROOT, "rev-parse", "--show-prefix"],
                            capture_output=True, text=True).stdout.strip()
    for rel in ("seeds/program_synthesis.json", "seeds/goal_residuals.json",
                "seeds/gap_prioritization.json", "seeds/stopping_policy.json"):
        head = subprocess.run(["git", "-C", ROOT, "show", "HEAD:" + prefix + rel],
                              capture_output=True, text=True).stdout
        assert head, rel
        assert head == open(os.path.join(ROOT, rel)).read(), rel


# =========================================================================== #
#  AG6 — NO PYTHON DECISIONS
# =========================================================================== #
def test_ag6_the_adapter_CANNOT_contain_a_hidden_decision():
    """The standing source audit, in the stronger module-specific form the
    goal-residual ingest adapter already passes: the new adapter never imports
    `substrate_rs`, never calls `.evaluate(`, never calls `run_rules`, and its
    only substrate contact is `add_node` / `node` / `nodes` / `set_attr` /
    `remove_node` / `load_seed_manifest` / `add_edge_unchecked`.  With no
    evaluator and no rule engine reachable from it, there is no place for a
    decision over graph state to hide.
    """
    src = _code_only(os.path.join(ROOT, "domains", "arc_goal_ingest.py"))
    for banned in ("import substrate_rs", ".evaluate(", "run_rules",
                   "graph_rewrite", "make_rule", "._match", "._apply"):
        assert banned not in src, banned
    import re
    calls = set(re.findall(r"(?:sub|s)\._inner\.(\w+)\(", src)) | \
        set(re.findall(r"(?:sub|s)\.(\w+)\(", src))
    allowed = {"add_node", "node", "nodes", "set_attr", "remove_node",
               "load_seed_manifest", "add_edge_unchecked"}
    assert calls <= allowed, sorted(calls - allowed)


def test_ag6_every_decision_lives_in_a_RULE_or_a_TERM():
    """Minting, matching, ranking, lapsing and asking are all Rules/Terms.

    Asserted by enumeration over the emitted seed: the mint, the ladder, the
    collapse, the ask and the reply each exist as a rule with a real `where`
    and real effects.  A rule with an EMPTY `And` would silently return True
    (`children_of` treats an unknown `clauses` field as an empty conjunction) —
    so every guard is asserted non-empty, and every rule's live firing is
    asserted by the scenes above.
    """
    names = {r["name"]: r for r in _seed()["rules"]}
    for name in ("ag_mint_remeasure", "ag_mint_blocker", "ag_vocab_mint",
                 "ag_select", "ag_ask",
                 "ag_reply_mints_testimony_unconditioned"):
        r = names[name]
        w = r["where"]
        assert w and w.get("type") == "And" and len(w["items"]) >= 1, name
        assert r["effects"], name
        assert all(isinstance(e, list) and e[0] in
                   {"add_node", "add_edge", "set_attr", "add_node_if_absent",
                    "del_edge"} for e in r["effects"]), name


def test_ag6_the_seed_REGENERATES_byte_identically():
    """Frozen artifacts are byte-frozen.  The PENALTY subtree is LIFTED from
    `seeds/goal_residuals.json` at build time, so if `gr_move_penalty` ever
    changes, this seed goes out of date LOUDLY instead of silently diverging
    from the rule it claims to copy verbatim.
    """
    r = subprocess.run([sys.executable, "tools/build_arc_goals_seed.py",
                        "--check"], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_ag6_the_PENALTY_subtree_really_is_gr_move_penaltys_own():
    """"Copied character for character" is a claim, so it is checked.

    The shipped `ag_select_audit` penalty term must be `gr_move_penalty`'s own
    `residual_penalty` value with exactly one substitution: the candidate var.
    Hand-copying a 400-line Term subtree is how a misspelled field name becomes
    a silent no-op — and a gate written to catch that trap has already fallen
    into it in this tree.
    """
    gr = json.load(open(os.path.join(ROOT, "seeds", "goal_residuals.json")))
    src = None
    for rule in gr["rules"]:
        if rule["name"] == "gr_move_penalty":
            for e in rule["effects"]:
                if e[0] == "set_attr" and e[2] == "residual_penalty":
                    src = e[3]["__term__"]
    assert src is not None

    def norm(o, cand):
        o = copy.deepcopy(o)

        def walk(x):
            if isinstance(x, dict):
                if x.get("type") == "Var" and x.get("name") == cand:
                    x["name"] = "__C__"
                if x.get("type") == "Var" and x.get("name") in ("grr", "agrr"):
                    x["name"] = "__R__"
                for k in ("var_name",):
                    if x.get(k) in ("grr", "agrr"):
                        x[k] = "__R__"
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
        walk(o)
        return json.dumps(o, sort_keys=True)

    ours = _seed_rule("ag_select_audit")["effects"][0][3]["__term__"]
    assert norm(ours, "g") == norm(src, "mc"), (
        "the arc-grain penalty has DIVERGED from gr_move_penalty")


def test_ag6_gr_move_penalty_MATCHES_ON_AN_EDGE_so_this_rung_needs_its_own_twin():
    """The load-bearing distinction the design found only by reading the JSON,
    pinned so it cannot be re-forgotten.

    The goal-residual doc's "grain-agnostic" claim is true of the PREDICATE and
    NOT of the RULE: `gr_move_penalty` matches on the `has_move_candidate`
    EDGE, so it can never see an `ArcGoal` however well its attrs line up.  The
    predicate transfers unchanged (asserted above); the rule does not.
    """
    gr = json.load(open(os.path.join(ROOT, "seeds", "goal_residuals.json")))
    m = [r["match"] for r in gr["rules"] if r["name"] == "gr_move_penalty"][0]
    assert m == [["g", "has_move_candidate", "mc"]], m
    assert _seed_rule("ag_select_audit")["match"] != m


# =========================================================================== #
#  EVERY RULE MUST FIRE — the anti-silent-no-op sweep.
#
#  AN UNKNOWN OP OR FIELD NAME IS A SILENT NO-OP, NOT A TRAP: a misspelled
#  `clauses` field on an `And` makes `children_of` treat it as an EMPTY
#  conjunction returning True, and a gate written to catch exactly that trap
#  has already fallen into it in this tree.  `test_ag1_every_rule_..._INSTALLED`
#  proves the loader kept them; these prove they DO something.  The three rules
#  below are the ones no scene above exercises.
# =========================================================================== #
def test_every_rule_ag_vocab_alias_FIRES_and_is_authored_not_inferred():
    """RUNG 2 of the ladder, which ships with an EMPTY table and therefore
    never fires on the shipped graph — so it is exercised here explicitly, in
    both directions.

    WITH a `SeamAlias{token, alias_of}` the goal adopts `alias_of` and is
    priced at 1 novelty bit (cheaper than a mint, dearer than a recognition).
    WITHOUT it the identical goal falls through to the mint.  The alias is
    AUTHORED GRAPH DATA — the difference between the two scenes is one node a
    human wrote down, never a string comparison.
    """
    def scene(with_alias):
        s, ag, agenda = _scene()
        if with_alias:
            s.add_node("SeamAlias", {"token": "oracle_import",
                                     "alias_of": "import_oracle"})
        s.add_node("SignatureVocab", {"dim": "sig_seam",
                                      "token": "import_oracle"})
        g = _goal(s, agenda, agid="G", proposed_seam="oracle_import",
                  evidence_artifact="results/arc6_a_ceiling.json",
                  evidence_path="ceilings._definition.cherry_picked_concept",
                  denominator_n=53.0, headroom_n=20.0,
                  vocab_checked=0.0, vocab_explained=0.0, dim_checked=0.0)
        _run(s)
        return s, s.node(g)["attrs"]

    s_a, a = scene(True)
    assert a["sig_seam"] == "import_oracle", a
    assert a["novelty_bits"] == 1.0
    assert agi.minted_vocab(s_a) == [], "rung 2 fell through to the mint"

    s_b, b = scene(False)
    assert b["sig_seam"] == "oracle_import", b
    assert b["novelty_bits"] == 8.0
    assert agi.minted_vocab(s_b) == ["oracle_import"]


def test_every_rule_ag_revocab_FIRES_and_a_refused_goal_is_RE_ARMED():
    """`sd_redecode`'s epoch guard, and the whole point of a SHARED vocabulary:
    a token minted for one goal may be the EXACT recognition another goal
    needed.

    The scene that requires it: H proposes a token it cannot source, so the
    ladder refuses it and it reaches `unsourced` with `vocab_checked=1`.  G
    then mints that same token from ITS artifact.  Without `ag_revocab`, H
    stays refused forever, because nothing re-arms a goal whose ladder already
    terminated.  With it, `arc_vocab_epoch` bumps, H re-arms and rung 1
    recognises the token.
    """
    s, ag, agenda = _scene()
    h = _goal(s, agenda, agid="H", proposed_seam="shared_token",
              denominator_n=10.0, headroom_n=5.0,
              vocab_checked=0.0, vocab_explained=0.0, dim_checked=0.0)
    _run(s)
    assert s.node(h)["attrs"]["status"] == "unsourced"
    assert s.node(h)["attrs"].get("sig_seam") is None
    epoch_before = _sel(s)["arc_vocab_epoch"]

    _goal(s, agenda, agid="G", proposed_seam="shared_token",
          evidence_artifact="results/arc6_a_ceiling.json",
          evidence_path="ceilings._definition.cherry_picked_concept",
          denominator_n=53.0, headroom_n=20.0,
          vocab_checked=0.0, vocab_explained=0.0, dim_checked=0.0)
    _run(s)
    assert agi.minted_vocab(s) == ["shared_token"]
    assert _sel(s)["arc_vocab_epoch"] == epoch_before + 1.0
    a = s.node(h)["attrs"]
    assert a["sig_seam"] == "shared_token", (
        "the refused goal was never re-armed — ag_revocab is inert: %r" % a)
    assert a["novelty_bits"] == 0.0, "a recognition was priced as a mint"
    assert a["decoded_vocab_epoch"] == _sel(s)["arc_vocab_epoch"]
    # ...and it TERMINATES.
    before = json.dumps(sorted(agi.arc_goals(s), key=lambda x: x["agid"]),
                        sort_keys=True, default=str)
    _run(s)
    assert json.dumps(sorted(agi.arc_goals(s), key=lambda x: x["agid"]),
                      sort_keys=True, default=str) == before


def test_every_rule_ag_mint_self_concern_FIRES_and_mints_UNSIGNATURED():
    """The `SelfConcern` channel, admitted at a cost.

    `CLAUDE.md` treats the gap spine as the agent's primary self-discovery
    route, so routing it in is right.  WHAT MUST NOT HAPPEN is parsing that
    free text into a signature — Seam C's failure exactly, at a grain where the
    blast radius is a whole build instead of one task.  So the minted goal
    carries NO `sig_*` at all, and pays `w_unsignatured` for being illegible to
    the evidence layer.  Mint-once, and a retired concern mints nothing.
    """
    s, ag, agenda = _scene()
    sc = s.add_node("SelfConcern", {"content": "cannot re-run a ceiling",
                                    "status": "noted", "source": "implicit"})
    s._inner.add_edge_unchecked(ag, "has_self_concern", sc)
    dead = s.add_node("SelfConcern", {"content": "already handled",
                                      "status": "retired"})
    s._inner.add_edge_unchecked(ag, "has_self_concern", dead)
    _run(s)
    goals = [a for a in agi.arc_goals(s) if a["source_kind"] == "self_concern"]
    assert [g["agid"] for g in goals] == \
        ["arc.concern.cannot re-run a ceiling"], goals
    g = goals[0]
    for dim in ("sig_seam", "sig_lever", "sig_target"):
        assert g.get(dim) is None, (
            "a signature was derived from free text — that is Seam C")
    n = len(agi.arc_goals(s))
    _run(s)
    assert len(agi.arc_goals(s)) == n, "re-minted"


def test_every_rule_ag_dim_check_mark_FIRES_and_keeps_the_mint_SATISFIABLE():
    """The deferred rung 3's Term-free marker, and why it is not decoration.

    MEASURED PRECEDENT: the seed loader drops a rule WHOLESALE the moment any
    effect references an unknown Term, so `sd_infer_dimension` failed to
    install at all pre-`DimInfer`, `dim_checked` was never set, and
    `sd_mint_quantum` DEADLOCKED for every residual-having observation.
    `ag_vocab_mint` requires `dim_checked == 1`, so without this marker the
    arc-grain mint would deadlock identically.

    Both directions: a goal that starts at `dim_checked = 0` reaches the mint;
    a goal held at `dim_explained = 1` (rung 3 claiming it) does NOT.
    """
    s, ag, agenda = _scene()
    g = _goal(s, agenda, agid="G", proposed_seam="marker_token",
              evidence_artifact="results/arc6_a_ceiling.json",
              evidence_path="ceilings._definition.cherry_picked_concept",
              denominator_n=10.0, headroom_n=5.0,
              vocab_checked=0.0, vocab_explained=0.0, dim_checked=0.0)
    _run(s)
    assert s.node(g)["attrs"]["dim_checked"] == 1.0, "the marker never fired"
    assert agi.minted_vocab(s) == ["marker_token"]

    s2, ag2, agenda2 = _scene()
    h = _goal(s2, agenda2, agid="H", proposed_seam="claimed_token",
              evidence_artifact="results/arc6_a_ceiling.json",
              evidence_path="ceilings._definition.cherry_picked_concept",
              denominator_n=10.0, headroom_n=5.0,
              vocab_checked=1.0, vocab_explained=0.0,
              dim_checked=1.0, dim_explained=1.0)
    _run(s2)
    assert agi.minted_vocab(s2) == [], (
        "rung 3 claimed the goal and the mint fired anyway — the ladder is "
        "not an Occam order")
    del h


def test_a_MISSING_attr_sorts_BELOW_any_number_and_the_ladder_survives_it():
    """A MEASURED ENGINE HAZARD, PINNED — it broke this rung once.

    `Lt(null, 0.0)` is **True** in this engine: a missing attr sorts below any
    number.  Written literally, `ag_revocab`'s epoch guard therefore re-armed
    EVERY never-decoded goal on the very first pass, which cleared
    `dim_explained` and so ERASED the deferred rung 3's claim before rung 4
    looked at it — an Occam-order violation caused by a NULL, not by a rule.
    `test_every_rule_ag_dim_check_mark_...` is what caught it.

    Both halves are pinned: the engine behaviour (so a future change is
    visible) and the guard's coalesce (so the fix cannot be simplified away).
    """
    s, ag, agenda = _scene()
    n = s.add_node("NullProbe", {})
    assert s._inner.evaluate(
        {"type": "Lt", "a": {"type": "Attr", "node": {"type": "Var", "name": "n"},
                             "key": "absent"},
         "b": {"type": "Lit", "value": 0.0}}, {"n": n}) is True

    where = json.dumps(_seed_rule("ag_revocab")["where"])
    assert "IfThenElse" in where, (
        "ag_revocab reads decoded_vocab_epoch without coalescing a missing "
        "value — re-arming every fresh goal on pass 1")

    # ...and the property that depends on it, live: a fresh goal at epoch 0 is
    # NOT re-armed, so a rung-3 claim survives to be honoured.
    g = _goal(s, agenda, agid="G", proposed_seam="tok", dim_explained=1.0,
              vocab_checked=1.0, vocab_explained=0.0, dim_checked=1.0,
              denominator_n=10.0, headroom_n=5.0)
    _run(s)
    assert s.node(g)["attrs"]["dim_explained"] == 1.0


def test_the_adapters_SELF_LOAD_is_idempotent_and_actually_installs():
    """`ensure_arc_goals` is the on-demand route the `self_load_only` key makes
    necessary — the `reading_collapse::_ensure_role_decode_loop` precedent.

    Untested loader code is how a seed ends up "shipped" and never installed,
    so both halves are asserted: the first call installs the rules and the
    agenda, and the second is a no-op rather than a second copy.
    """
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    cls = s.add_node("Agent", {"is_class": True})
    s._inner.add_edge_unchecked(ag, "is_a", cls)
    assert list(s.nodes("ArcAgenda")) == []

    assert agi.ensure_arc_goals(s, ag) is True
    installed = {(r if isinstance(r, dict) else json.loads(r))["name"]
                 for r in s._inner.export_rules()}
    assert {r["name"] for r in _seed()["rules"]} <= installed
    assert len(list(s.nodes("ArcAgenda"))) == 1

    assert agi.ensure_arc_goals(s, ag) is False, "re-installed"
    assert len(list(s.nodes("ArcAgenda"))) == 1


def test_the_measurement_epoch_is_carried_as_the_STRING_fact_equals_compares():
    """`gr_condition_lapse`'s `fact_equals` branch compares a
    `ResidualFact.value` to a `ResidualCondition.expected_str` — STRINGS.  The
    epoch is therefore stored as one throughout, so `Eq` never straddles the
    float/str boundary, and it lives as a `ResidualFact` precisely so the
    EXISTING lapse machinery consumes it unmodified."""
    s, ag, agenda = _scene()
    assert agi.measure_epoch(s) is None
    agi.set_measure_epoch(s, 0)
    assert agi.measure_epoch(s) == "0"
    agi.bump_measure_epoch(s)
    assert agi.measure_epoch(s) == "1"
    assert len([n for n in s.nodes("ResidualFact")
                if s.node(n)["attrs"]["name"] == "arc_measure_epoch"]) == 1


def test_a_SINGLE_goal_pool_has_no_margin_and_does_NOT_ask():
    """The degenerate case, checked because of the null hazard above.

    With one goal there is no runner-up, so `arc_sel_margin` is never stamped —
    and `Lt(null, threshold)` is TRUE in this engine, so a trigger reading the
    margin alone would fire on an empty comparison.  It does not, because
    `ag_ask` binds BOTH candidates as matched vars against the stamps: with no
    `arc_sel_runner_up_agid` there is nothing for `h` to bind to.  The ask is
    structurally unable to ask about a tie that does not exist.
    """
    s, ag, agenda = _scene()
    _goal(s, agenda, agid="ONLY", sig_seam="only_seam",
          denominator_n=53.0, headroom_n=20.0)
    agi.set_measure_epoch(s, 0)
    _run(s)
    sel = _sel(s)
    assert sel["arc_sel_agid"] == "ONLY"
    assert sel.get("arc_sel_runner_up_agid") is None
    assert sel.get("arc_sel_margin") is None
    assert agi.questions(s) == [], "asked about a tie with one candidate"
