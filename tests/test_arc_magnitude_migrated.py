"""test_arc_magnitude_migrated — CONSTRAINTS, ORDER-N VALUE, THE LADDER.

Prereg:  `PROGRAM_SYNTHESIS_ARC6_PREREG.md` amendment **A9** (`MG1`–`MG5`).
Results: `PROGRAM_SYNTHESIS_ARC6_MAGNITUDE.md`, `results/arc6_magnitude.json`.
Seed:    `seeds/arc_magnitude.json` (emitted by
         `tools/build_arc_magnitude_seed.py`).

WHAT THIS GATES.  `seeds/arc_goals.json` ranks arc goals by ABSOLUTE HEADROOM
IN TASKS — a *spot* valuation, priced in a vacuum.  A9 registers three missing
TERMS (not three hazards needing guards): constraints, order-N value, and a
magnitude ladder.  This suite gates all three, and gates the one thing that
makes order-N honest rather than self-justifying — **that every attrition
factor is READ from a results artifact and that a projection with no measured
basis EXPIRES.**

EVERY GATE IS A LIVE INVOCATION, IN BOTH DIRECTIONS, because *a bug in the
refuting direction is indistinguishable from an honest null*.  And per A7 a
control is admissible only once shown CAPABLE of detecting the difference it
rules out — which is why `VALUE_N` is machine-lifted from `ag_select`'s own
term rather than written beside it: the two readings are the same expression,
so "they differ" cannot be an artefact of two authors.

Run:
  COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \\
    pytest tests/test_arc_magnitude_migrated.py --confcutdir=<this worktree> -q
"""
from __future__ import annotations

import ast
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
from domains import arc_magnitude_ingest as ami  # noqa: E402
from domains import goal_residual_ingest as gri  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402

SEED_PATH = os.path.join(ROOT, "seeds", "arc_magnitude.json")
GOALS_SEED_PATH = os.path.join(ROOT, "seeds", "arc_goals.json")
STRUCTURAL = "arc.supply.arc6.seam_a.import_oracle.missing_structural_primitive"
REMEASURE = "arc.remeasure.arc6.verdict.row_verdict_seed_only"


# =========================================================================== #
#  PRECONDITION — assert the engine, do not merely record it.
# =========================================================================== #
def _assert_engine_coherent(s):
    n = s.add_node("ArcMagEngineProbe", {"lst": [1, 2, 3], "tup": (1, 2, 3)})
    a = s.node(n)["attrs"]
    assert a["lst"] != a["tup"], (
        "VALUE LAYER ABSENT — list and tuple collapsed.  Not this rung's "
        "result to re-pin: the tree is incoherent.  Expected 8311d4356082…")
    return True


def _boot(epoch=0, with_ladder=True, with_attrition=True):
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    cls = s.add_node("Agent", {"is_class": True})
    s._inner.add_edge_unchecked(ag, "is_a", cls)
    _assert_engine_coherent(s)
    for sid in ("program_synthesis", "goal_residuals", "arc_goals",
                "arc_magnitude"):
        s._inner.load_seed_manifest(manifest_for(sid), ag)
    s._inner.load_seed_manifest(manifest_for("math_capability_shapes"), ag)
    gri.install_facts(s, gri.probe_facts(s))
    agi.set_measure_epoch(s, epoch)
    if with_ladder:
        ami.install_tier_ladder(s, ami.probe_tier_ladder())
    if with_attrition:
        ami.resolve_attrition_keys(s)
    s._inner.run_rules()
    return s, ag


def _seed():
    with open(SEED_PATH) as fh:
        return json.load(fh)


def _rule(name, doc=None):
    for r in (doc or _seed())["rules"]:
        if r["name"] == name:
            return r
    raise AssertionError("no such rule: " + name)


def _value_n_term():
    return _rule("mg_select_margin")["effects"][0][3]["__term__"]


def _value_1_term():
    with open(GOALS_SEED_PATH) as fh:
        d = json.load(fh)
    for r in d["rules"]:
        if r["name"] == "ag_select_margin":
            return r["effects"][0][3]["__term__"]
    raise AssertionError("ag_select_margin missing")


def _rank(s, term, var):
    rows = []
    for n in s.nodes("ArcGoal"):
        a = s.node(n)["attrs"]
        rows.append((float(s._inner.evaluate(term, {var: n})), a["agid"]))
    rows.sort(key=lambda r: (-r[0], r[1]))
    return [r[1] for r in rows], {r[1]: r[0] for r in rows}


def _answer_horizon(s, units, *, conditioned=False, ckind="horizon", **kw):
    qs = list(s.nodes("ArcConstraintQuestion"))
    assert qs, "no ArcConstraintQuestion to answer — the ask did not fire"
    extra = {}
    if conditioned:
        extra = {"cond_kind": "fact_equals",
                 "cond_filter_value": "arc6_structural_ceiling_present",
                 "cond_expected_str": "1"}
    ami.attach_constraint_reply(s, qs[0], "answer", con_kind=ckind,
                                horizon_units=units, **extra, **kw)
    s._inner.run_rules()


def _goal(s, agid):
    for n in s.nodes("ArcGoal"):
        if s.node(n)["attrs"]["agid"] == agid:
            return s.node(n)["attrs"]
    raise AssertionError("no such goal: " + agid)


# =========================================================================== #
#  MEASURED ENGINE HAZARDS — pinned, because every one of them silently
#  produces a WRONG ANSWER rather than an error, and the coalescing in
#  `NUM()` is only correct while these hold.
# =========================================================================== #
def test_hazard_a_MISSING_attr_sorts_BELOW_any_number():
    s = srs.Substrate()
    empty = {"type": "Argmin", "source": {"type": "NodesOfType",
                                          "node_type": "NoSuchType"},
             "var_name": "x", "value": {"type": "Lit", "value": 0},
             "default": None}
    nul = {"type": "Attr", "node": empty, "key": "nope"}
    assert s._inner.evaluate(
        {"type": "Lt", "a": nul, "b": {"type": "Lit", "value": 0.0}}, {}) is True


def test_hazard_ANY_number_sorts_ABOVE_a_missing_attr():
    """THE ONE THAT WOULD HAVE BROKEN mg_tier_in_horizon.

    `Gt(cum_cost, horizon)` with NO horizon held reads TRUE, so every tier
    would have been truncated and a graph that had simply never been asked
    would have looked like one on an impossible deadline.  `NO_HORIZON()` is
    checked FIRST for this reason.
    """
    s = srs.Substrate()
    empty = {"type": "Argmin", "source": {"type": "NodesOfType",
                                          "node_type": "NoSuchType"},
             "var_name": "x", "value": {"type": "Lit", "value": 0},
             "default": None}
    nul = {"type": "Attr", "node": empty, "key": "nope"}
    assert s._inner.evaluate(
        {"type": "Gt", "a": {"type": "Lit", "value": 8.0}, "b": nul}, {}) is True


def test_hazard_NULL_IS_THE_MULTIPLICATIVE_IDENTITY():
    """THE ONE THAT WOULD HAVE BROKEN MG2 IN THE DANGEROUS DIRECTION.

    `Times(increment, null_survival)` returns the increment, so an
    UNRESOLVED attrition factor would have made an UNMEASURED projection worth
    MORE than a measured one — precisely A9's *"an authored projection is
    unbounded in the dangerous direction."*
    """
    s = srs.Substrate()
    empty = {"type": "Argmin", "source": {"type": "NodesOfType",
                                          "node_type": "NoSuchType"},
             "var_name": "x", "value": {"type": "Lit", "value": 0},
             "default": None}
    nul = {"type": "Attr", "node": empty, "key": "nope"}
    assert s._inner.evaluate(
        {"type": "Times", "items": [{"type": "Lit", "value": 16.0}, nul]},
        {}) == 16.0


def test_hazard_StringConcat_SILENTLY_DROPS_numeric_parts():
    s = srs.Substrate()
    n = s.add_node("P", {"v": 42.0})
    node = {"type": "Lit", "value": None}
    del node
    raw = {"type": "StringConcat", "parts": [
        {"type": "Lit", "value": "n="},
        {"type": "Attr", "node": {"type": "Var", "name": "p"}, "key": "v"}]}
    wrapped = {"type": "StringConcat", "parts": [
        {"type": "Lit", "value": "n="},
        {"type": "ToJsonString",
         "value": {"type": "Attr", "node": {"type": "Var", "name": "p"},
                   "key": "v"}}]}
    assert s._inner.evaluate(raw, {"p": n}) == "n="
    assert "42" in s._inner.evaluate(wrapped, {"p": n})


# =========================================================================== #
#  STRUCTURE — the seed installed, every rule present, no attrition number.
# =========================================================================== #
def test_mg5_every_rule_in_the_seed_actually_INSTALLED():
    """An unknown op or field name is a SILENT NO-OP and the loader drops a
    rule WHOLESALE when an effect references an unknown Term.  A suite that
    exercises rules without checking they installed measures nothing."""
    s, _ = _boot()
    installed = {r["name"] for r in s._inner.export_rules()}
    declared = {r["name"] for r in _seed()["rules"]}
    assert declared, "seed declares no rules"
    assert declared <= installed, sorted(declared - installed)
    assert len(declared) == 17, len(declared)


def test_mg2_THE_SEED_CONTAINS_NO_ATTRITION_NUMBER():
    """A9's bar is that the factors are READ, not authored.  The strongest
    available form of that is not a number with a citation next to it — it is
    NO NUMBER AT ALL.  Every `ArcAttritionKey` carries a name, an artifact and
    two dotted paths and nothing numeric."""
    keys = [n for n in _seed()["nodes"] if n["type"] == "ArcAttritionKey"]
    assert len(keys) == 3, len(keys)
    for k in keys:
        a = k["attrs"]
        assert a["evidence_artifact"].startswith("results/")
        assert a["numerator_path"] and a["denominator_path"]
        nums = [v for v in a.values() if isinstance(v, (int, float))
                and not isinstance(v, bool)]
        assert nums == [], (k["attrs"]["name"], nums)
        assert "factor" not in a and "numerator_n" not in a


def test_mg2_the_factors_are_RESOLVED_FROM_THE_ARTIFACT_and_traceable():
    """Each factor equals the ratio of two numbers physically present in the
    named artifact at the named path.  Re-derived here from the file, so the
    trace is checked rather than claimed."""
    s, _ = _boot()
    for k in ami.attrition(s):
        assert k["resolved"] == 1.0, k["name"]
        with open(os.path.join(ROOT, k["evidence_artifact"])) as fh:
            doc = json.load(fh)
        num = ami._resolve(doc, k["numerator_path"])
        den = ami._resolve(doc, k["denominator_path"])
        assert num == k["numerator_n"] and den == k["denominator_n"], k["name"]
        assert abs(k["factor"] - num / den) < 1e-12, k["name"]
    named = {k["name"]: k["factor"] for k in ami.attrition(s)}
    assert abs(named["inventory_to_strict_reach"] - 6.0 / 10.0) < 1e-12
    assert abs(named["reach_to_conversion"] - 8.0 / 25.0) < 1e-12


def test_mg2_the_ladder_key_is_a_MEASURED_population_join():
    """Which blocker class the tier ladder describes is settled by SET
    EQUALITY of two measured id lists, re-derived here from both files.  An
    authored per-goal ladder assignment would be Seam D's 36/36 again."""
    rec = ami.probe_tier_ladder()
    assert rec["ladder_key"] == "missing_structural_primitive"
    j = rec["population_join"]
    assert j["names_whose_id_list_is_EQUAL_to_the_ladder_population"] == \
        ["missing_structural_primitive"]
    assert len(j["blocker_names_offered"]) == 3, j["blocker_names_offered"]
    assert j["ladder_population_n"] == 42
    with open(os.path.join(ROOT, "results/arc6_a_ceiling.json")) as fh:
        ac = json.load(fh)
    with open(os.path.join(ROOT,
                           "results/arc6_structural_ceiling.json")) as fh:
        sc = json.load(fh)
    assert sorted(ac["blocker_split"]["ids_over_live_unreached"]
                  ["missing_structural_primitive"]) == \
        sorted(sc["population"]["structural_42_ids"])


def test_mg2_the_tier_ladder_is_READ_from_bundles_not_authored():
    s, _ = _boot()
    ts = ami.tiers(s)
    assert [t["increment_n"] for t in ts] == [10.0, 16.0, 6.0, 10.0]
    assert [t["cum_cost_units"] for t in ts] == [8.0, 18.0, 24.0, 28.0]
    with open(os.path.join(ROOT,
                           "results/arc6_structural_ceiling.json")) as fh:
        b = json.load(fh)["bundles"]
    assert [x["n_unlocked"] for x in b] == [10, 26, 32, 42]
    assert [x["n_units"] for x in b] == [8, 18, 24, 28]


# =========================================================================== #
#  MG2 — THE LIFT.  order-N is order-1 with ONE substitution.
# =========================================================================== #
def _strip(t):
    return json.dumps(t, sort_keys=True)


def test_mg2_VALUE_N_is_ag_selects_OWN_value_term_with_ONE_substitution():
    """THE A7 CONTROL, STRUCTURAL.

    "order-N differs from order-1" is only a measurement if the two readings
    are the SAME instrument.  `VALUE_N` is machine-lifted from
    `ag_select_margin`'s own value effect; this test re-derives the lift and
    proves the whole difference is (a) one `Attr` key and (b) an outer
    subtraction.  If it were two independently written terms the difference
    could be anywhere and the comparison would mean nothing.
    """
    v1 = _value_1_term()
    vn = _value_n_term()
    # (b): VALUE_N is `Minus(<something>, <scope charge>)`.
    assert vn["type"] == "Minus", vn["type"]
    inner = vn["a"]
    # (a): that <something> is v1 with h->mh renamed and ONE key swapped.
    s1 = _strip(v1).replace('"name": "h"', '"name": "mh"') \
                   .replace('"var_name": "h"', '"var_name": "mh"')
    s2 = _strip(inner)
    assert s1.count('"key": "headroom_n"') == 1, s1.count('"key": "headroom_n"')
    assert s2.count('"key": "orderN_headroom_n"') == 1
    assert s2.count('"key": "headroom_n"') == 0
    assert s1.replace('"key": "headroom_n"',
                      '"key": "orderN_headroom_n"') == s2, \
        "VALUE_N is NOT ag_select's own term with exactly one substitution"


def test_mg2_the_POOL_is_ag_selects_OWN_pool():
    """mg_select ranks THE SAME POOL, lifted, so a reordering cannot be an
    artefact of a differently-scoped candidate set."""
    with open(GOALS_SEED_PATH) as fh:
        g = json.load(fh)
    pool1 = None
    for r in g["rules"]:
        if r["name"] == "ag_select":
            for e in r["effects"]:
                if e[2] == "arc_sel_value":
                    pool1 = e[3]["__term__"]["source"]
    assert pool1 is not None
    pooln = _rule("mg_select")["effects"][1][3]["__term__"]["source"]
    a = _strip(pool1).replace('"g2"', '"__V__')
    b = _strip(pooln).replace('"mg2"', '"__V__')
    assert a == b, "mg_select is not ranking ag_select's pool"


# =========================================================================== #
#  MG2 — THE HEADLINE, on the shipped graph.
# =========================================================================== #
def test_mg2_HEADLINE_order_N_differs_from_order_1_and_the_top_two_INVERT():
    s, _ = _boot()
    o1, v1 = _rank(s, _value_1_term(), "h")
    on, vn = _rank(s, _value_n_term(), "mh")
    assert o1 != on, "order-N is identical to order-1 — nothing was repriced"
    assert o1[0] == STRUCTURAL, o1[0]
    assert on[0] == REMEASURE, on[0]
    # ...and it is the STRUCTURAL goal that moves, by its ladder.
    g = _goal(s, STRUCTURAL)
    assert g["headroom_n"] == 42
    assert abs(g["orderN_headroom_n"] - 13.637248) < 1e-6, \
        g["orderN_headroom_n"]
    assert g["order_n_basis"] == "measured_tier_ladder"
    # ...while a goal with NO ladder is UNCHANGED — A9's re-measurement case.
    r = _goal(s, REMEASURE)
    assert r["headroom_n"] == r["orderN_headroom_n"] == 11.0
    assert r["order_n_basis"] == "no_ladder_order_1_IS_total_value"


def test_mg2_the_order_sum_is_the_MEASURED_tiers_times_their_survival():
    """Arithmetic re-derived from the artifact, so the 13.637 is checked and
    not merely reported."""
    s, _ = _boot()
    f = {k["name"]: k["factor"] for k in ami.attrition(s)}
    fs, fp = f["inventory_to_strict_reach"], f["reach_to_conversion"]
    ts = ami.tiers(s)
    want = sum(t["increment_n"] * (1.0 if t["order"] == 1.0
                                   else fs * fp ** (t["order"] - 1.0))
               for t in ts)
    assert abs(_goal(s, STRUCTURAL)["orderN_headroom_n"] - want) < 1e-9
    assert abs(want - (10 + 16 * .192 + 6 * .06144 + 10 * .0196608)) < 1e-9


# =========================================================================== #
#  MG2 — THE EXPIRY LANE, both directions.
# =========================================================================== #
def test_mg2_a_MEASURED_projection_survives_until_its_ARTIFACT_changes():
    s, _ = _boot()
    pr = [s.node(n)["attrs"] for n in s.nodes("ArcProjection")]
    assert len(pr) == 1 and pr[0]["basis"] == "measured_attrition"
    assert pr[0]["stale"] == 0.0
    assert _goal(s, STRUCTURAL)["order_n_basis"] == "measured_tier_ladder"
    for n in s.nodes("ResidualFact"):
        if s.node(n)["attrs"]["name"] == "arc6_structural_ceiling_present":
            s.set_attr(n, "value", "0")
    s._inner.run_rules()
    pr2 = [s.node(n)["attrs"] for n in s.nodes("ArcProjection")]
    assert pr2[0]["stale"] == 1.0, "the projection did not lapse"
    g = _goal(s, STRUCTURAL)
    assert g["order_n_basis"] == "projection_expired_fell_back_to_order_1"
    assert g["orderN_headroom_n"] == 42, g["orderN_headroom_n"]


def test_mg2_an_UNMEASURED_projection_EXPIRES_at_the_next_epoch():
    """A9's registered bar, live: *a projection with no measured basis must
    default-expire at the next epoch, exactly as an unconditioned human answer
    does.*  The refuting half is the test above — a projection that expired
    whatever its basis would be measuring the epoch bump, not the basis."""
    s, _ = _boot(with_attrition=False)
    pr = [s.node(n)["attrs"] for n in s.nodes("ArcProjection")]
    assert len(pr) == 1, pr
    assert pr[0]["basis"] == "NO_MEASURED_BASIS"
    assert pr[0]["stale"] == 0.0
    agi.bump_measure_epoch(s)
    s._inner.run_rules()
    pr2 = [s.node(n)["attrs"] for n in s.nodes("ArcProjection")]
    assert pr2[0]["stale"] == 1.0, "an unmeasured projection did not expire"


def test_mg2_an_unmeasured_projection_is_worth_NOTHING_not_its_full_increment():
    """The `Times(x, null) == x` trap, closed.  With no attrition resolved the
    orders above 1 must contribute ZERO, not their undiscounted increments."""
    s, _ = _boot(with_attrition=False)
    g = _goal(s, STRUCTURAL)
    assert g["orderN_headroom_n"] == 10.0, g["orderN_headroom_n"]


# =========================================================================== #
#  MG1 — constraints lapse through the EXISTING machinery.
# =========================================================================== #
def test_mg1_an_ArcConstraint_lapses_through_gr_condition_lapse_BOTH_WAYS():
    """No new lapse mechanism: `gr_condition_lapse`/`gr_condition_hold` match
    on the `holds_under` EDGE with no type restriction on their left var."""
    s, _ = _boot()
    _answer_horizon(s, 20.0, conditioned=True)
    k = [s.node(n)["attrs"] for n in s.nodes("ArcConstraint")]
    assert len(k) == 1 and k[0]["stale"] == 0.0
    node = list(s.nodes("ArcConstraint"))[0]
    for n in s.nodes("ResidualFact"):
        if s.node(n)["attrs"]["name"] == "arc6_structural_ceiling_present":
            s.set_attr(n, "value", "0")
    s._inner.run_rules()
    assert s.node(node)["attrs"]["stale"] == 1.0
    assert _goal(s, STRUCTURAL)["magnitude_rung"] == "unknown_no_horizon"
    for n in s.nodes("ResidualFact"):
        if s.node(n)["attrs"]["name"] == "arc6_structural_ceiling_present":
            s.set_attr(n, "value", "1")
    s._inner.run_rules()
    assert s.node(node)["attrs"]["stale"] == 0.0
    assert _goal(s, STRUCTURAL)["magnitude_rung"] == "balance"


def test_mg1_the_lapse_rules_are_NOT_redefined_in_this_seed():
    """Structural: this seed must contain no rule that writes `stale` on a
    constraint.  If it did, "zero new lapse machinery" would be false."""
    for r in _seed()["rules"]:
        for e in r["effects"]:
            assert not (e[0] == "set_attr" and e[2] == "stale"), r["name"]


def test_mg1_an_UNCONDITIONED_constraint_expires_at_the_next_epoch():
    s, _ = _boot()
    _answer_horizon(s, 5.0, conditioned=False)
    node = list(s.nodes("ArcConstraint"))[0]
    assert s.node(node)["attrs"]["stale"] == 0.0
    assert _goal(s, STRUCTURAL)["magnitude_rung"] == "push_back"
    agi.bump_measure_epoch(s)
    s._inner.run_rules()
    assert s.node(node)["attrs"]["stale"] == 1.0
    assert _goal(s, STRUCTURAL)["magnitude_rung"] == "unknown_no_horizon"


def test_mg1_a_CONDITIONED_constraint_survives_the_same_epoch_bump():
    """The refuting half of the test above, in the same shape: a constraint
    that expired whatever its condition would mean the first test was
    measuring the bump rather than the default."""
    s, _ = _boot()
    _answer_horizon(s, 5.0, conditioned=True)
    node = list(s.nodes("ArcConstraint"))[0]
    agi.bump_measure_epoch(s)
    s._inner.run_rules()
    assert s.node(node)["attrs"]["stale"] == 0.0
    assert _goal(s, STRUCTURAL)["magnitude_rung"] == "push_back"


# =========================================================================== #
#  MG1 — THE BAR.  One horizon answer reprices the pool.
# =========================================================================== #
def test_mg1_HEADLINE_ONE_horizon_answer_reprices_the_pool():
    """A9's registered bar: **>=2 goals change relative order** from ONE
    answer.  That asymmetry — one answer reprices everything, an approval
    returns one bit — is the argument for asking constraints."""
    s, _ = _boot()
    vn = _value_n_term()
    before, _ = _rank(s, vn, "mh")
    _answer_horizon(s, 5.0)
    after, _ = _rank(s, vn, "mh")
    pairs = [(x, y) for i, x in enumerate(before) for y in before[i + 1:]
             if after.index(x) > after.index(y)]
    assert len(pairs) >= 2, pairs
    assert len(pairs) == 6, pairs
    movers = sorted({g for p in pairs for g in p})
    assert STRUCTURAL in movers
    assert len(movers) == 7, movers
    assert before.index(STRUCTURAL) == 1
    assert after.index(STRUCTURAL) == len(after) - 1


def test_mg1_the_repricing_is_the_HORIZON_and_not_the_reply_arriving():
    """THE CONTROL THAT MAKES THE ABOVE ADMISSIBLE.  A reply of the same shape
    that names a SCOPE rather than a horizon must NOT produce the horizon's
    reordering — otherwise "the pool was repriced" could just mean "a Message
    was added"."""
    s, _ = _boot()
    vn = _value_n_term()
    before, _ = _rank(s, vn, "mh")
    qs = list(s.nodes("ArcConstraintQuestion"))
    ami.attach_constraint_reply(s, qs[0], "scope answer", con_kind="scope",
                                scope_seam="missing_structural_primitive")
    s._inner.run_rules()
    after, _ = _rank(s, vn, "mh")
    assert _goal(s, STRUCTURAL)["magnitude_rung"] == "unknown_no_horizon", \
        "a scope reply set a horizon — the channels are crossed"
    assert after.index(STRUCTURAL) == before.index(STRUCTURAL)


def test_mg1_a_COMPETING_requirement_consumes_the_horizon():
    s, _ = _boot()
    _answer_horizon(s, 30.0)
    assert _goal(s, STRUCTURAL)["magnitude_rung"] == "absorb"
    q = s.add_node("ArcConstraintQuestion", {"answered": 0.0, "status": "open",
                                             "asked_epoch": "0"})
    m = s.add_node("Message", {"from": "interlocutor", "con_kind": "competing",
                               "con_competing_units": 25.0,
                               "kind": "arc_constraint_reply"})
    s._inner.add_edge_unchecked(m, "responds_to", q)
    s._inner.run_rules()
    assert _goal(s, STRUCTURAL)["magnitude_rung"] == "push_back"


def test_mg1_scope_is_a_WEIGHT_and_not_a_VETO():
    """An out-of-scope goal stays IN THE POOL and is charged.  A9's framing
    correction: scope was a missing input, so it is a term."""
    s, _ = _boot()
    qs = list(s.nodes("ArcConstraintQuestion"))
    ami.attach_constraint_reply(s, qs[0], "scope", con_kind="scope",
                                scope_seam="row_verdict")
    s._inner.run_rules()
    charged = {g["agid"]: g.get("out_of_scope") for g in ami.goal_rows(s)}
    assert charged[REMEASURE] == 0.0
    assert charged[STRUCTURAL] == 1.0
    # it is still IN THE POOL — a veto would have removed it.
    order, vals = _rank(s, _value_n_term(), "mh")
    assert STRUCTURAL in order
    # ...and the charge is real, not a stamp nothing reads.
    s2, _ = _boot()
    _, vals2 = _rank(s2, _value_n_term(), "mh")
    assert vals[STRUCTURAL] < vals2[STRUCTURAL]
    assert abs((vals2[STRUCTURAL] - vals[STRUCTURAL]) - 25.0) < 1e-9


def test_mg1_scope_CLEARS_when_the_constraint_lapses():
    s, _ = _boot()
    qs = list(s.nodes("ArcConstraintQuestion"))
    ami.attach_constraint_reply(s, qs[0], "scope", con_kind="scope",
                                scope_seam="row_verdict")
    s._inner.run_rules()
    assert _goal(s, STRUCTURAL)["out_of_scope"] == 1.0
    agi.bump_measure_epoch(s)
    s._inner.run_rules()
    assert _goal(s, STRUCTURAL)["out_of_scope"] == 0.0


# =========================================================================== #
#  MG1 — the ask discriminates.
# =========================================================================== #
def test_mg1_the_ask_fires_under_IGNORANCE_and_is_WITHHELD_when_a_horizon_HOLDS():
    """THE DISCRIMINATING PAIR — same epoch bump, two worlds.  Both scenes take
    the SAME bump; only whether a horizon holds differs.  The instrument is
    shown able to mint a second question before it is used to show one was
    withheld (A7)."""
    a, _ = _boot()
    assert len(ami.constraint_questions(a)) == 1
    agi.bump_measure_epoch(a)
    a._inner.run_rules()
    assert len(ami.constraint_questions(a)) == 2, "the ask cannot re-fire"

    b, _ = _boot()
    _answer_horizon(b, 40.0, conditioned=True)
    assert len(ami.constraint_questions(b)) == 1
    agi.bump_measure_epoch(b)
    b._inner.run_rules()
    assert len(ami.constraint_questions(b)) == 1, "asked while not ignorant"

    # ...and a LAPSED horizon is ignorance again.
    for n in b.nodes("ResidualFact"):
        if b.node(n)["attrs"]["name"] == "arc6_structural_ceiling_present":
            b.set_attr(n, "value", "0")
    agi.bump_measure_epoch(b)
    b._inner.run_rules()
    assert len(ami.constraint_questions(b)) == 2


def test_mg1_the_question_carries_the_MEASURED_NUMBERS():
    """`StringConcat` silently drops numeric parts, so a question can look
    fine and say nothing.  The text must carry the ladder's real costs."""
    s, _ = _boot()
    txt = [s.node(n)["attrs"]["text"] for n in s.nodes("Message")
           if s.node(n)["attrs"].get("kind") == "arc_constraint_question"]
    assert len(txt) == 1
    t = txt[0]
    assert "28" in t and "8" in t, t
    assert "operator units" in t
    assert "reprices" in t


def test_mg1_the_ask_asks_for_a_CONSTRAINT_not_for_APPROVAL():
    s, _ = _boot()
    t = [s.node(n)["attrs"]["text"] for n in s.nodes("Message")
         if s.node(n)["attrs"].get("kind") == "arc_constraint_question"][0]
    assert "WHAT IS THE HORIZON" in t
    assert "approve" in t.lower()
    assert "one bit" in t


# =========================================================================== #
#  MG3 — the ladder routes by ratio, both directions.
# =========================================================================== #
def test_mg3_HEADLINE_the_SAME_goal_changes_rung_when_ONLY_the_horizon_does():
    """A9's registered bar, both directions.  The goal, its ladder, its costs
    and its attrition are identical across every boot; the only thing that
    differs is one number in one utterance."""
    seen = []
    for h in (40.0, 20.0, 5.0, 20.0, 40.0):
        s, _ = _boot()
        _answer_horizon(s, h)
        g = _goal(s, STRUCTURAL)
        seen.append(g["magnitude_rung"])
        assert g["magnitude_cost_units"] == 28.0
    assert seen == ["absorb", "balance", "push_back", "balance", "absorb"], seen


def test_mg3_the_rung_is_a_RATIO_and_the_only_number_is_ONE():
    """No authored cutoff anywhere: cost and horizon are both in operator
    units, so 1.0 is what "fits" MEANS, not a knob."""
    r = _rule("mg_rung")
    lits = []

    def walk(o):
        if isinstance(o, dict):
            if o.get("type") == "Lit" and isinstance(o.get("value"), (int, float)) \
                    and not isinstance(o.get("value"), bool):
                lits.append(float(o["value"]))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(r["effects"])
    assert set(lits) <= {0.0, 1.0, -1.0}, sorted(set(lits))
    pol = [n for n in _seed()["nodes"] if n["type"] == "ArcMagPolicy"][0]
    assert not any(k for k in pol["attrs"]
                   if "ratio" in k or "threshold" in k or "cutoff" in k)


def test_mg3_the_ratios_are_the_MEASURED_costs_over_the_MEASURED_horizon():
    s, _ = _boot()
    _answer_horizon(s, 20.0)
    g = _goal(s, STRUCTURAL)
    assert abs(g["magnitude_ratio"] - 28.0 / 20.0) < 1e-9
    assert abs(g["magnitude_ratio_first_tier"] - 8.0 / 20.0) < 1e-9


def test_mg3_NO_HORIZON_is_its_OWN_rung_and_not_absorb():
    """"We have not been told" must not masquerade as "it fits" — and it would
    have, since `Gt(x, null)` is TRUE and `Div(x, null)` is 0.0."""
    s, _ = _boot()
    assert _goal(s, STRUCTURAL)["magnitude_rung"] == "unknown_no_horizon"
    assert _goal(s, STRUCTURAL)["decompose_required"] == 0.0


def test_mg3_push_back_marks_DECOMPOSE_REQUIRED_and_names_its_MEASURED_ladder():
    """MG4 is DESIGNED, NOT BUILT.  The rung says decomposition is required and
    names the measured ladder it would split on; nothing splits it."""
    s, _ = _boot()
    _answer_horizon(s, 5.0)
    g = _goal(s, STRUCTURAL)
    assert g["magnitude_rung"] == "push_back"
    assert g["decompose_required"] == 1.0
    assert g["decompose_ladder_key"] == "missing_structural_primitive"
    # NOTHING SPLIT IT — no child goals, no new ArcGoal.
    assert len(list(s.nodes("ArcGoal"))) == 8
    assert not any(s.node(n)["attrs"].get("parent_agid")
                   for n in s.nodes("ArcGoal"))


def test_mg3_absorb_and_balance_do_NOT_require_decomposition():
    for h, want in ((40.0, "absorb"), (20.0, "balance")):
        s, _ = _boot()
        _answer_horizon(s, h)
        g = _goal(s, STRUCTURAL)
        assert g["magnitude_rung"] == want
        assert g["decompose_required"] == 0.0


# =========================================================================== #
#  EVERY RULE FIRES — including the ones no scene above reaches.
# =========================================================================== #
def test_every_rule_mg_vocab_paths_fire_at_least_once():
    """A rule that never fires proves nothing, and an unknown field name is a
    SILENT NO-OP, so each rule is shown to have MOVED something."""
    s, _ = _boot()
    _answer_horizon(s, 20.0, conditioned=True)
    fired = {
        "mg_attrition_factor": any(k.get("factor") is not None
                                   for k in ami.attrition(s)),
        "mg_tier_survival": all(t.get("survival") is not None
                                for t in ami.tiers(s)),
        "mg_tier_in_horizon": all(t.get("in_horizon") is not None
                                  for t in ami.tiers(s)),
        "mg_projection_mint_measured": any(
            s.node(n)["attrs"]["basis"] == "measured_attrition"
            for n in s.nodes("ArcProjection")),
        "mg_goal_order_n": any(g.get("order_n_basis") == "measured_tier_ladder"
                               for g in ami.goal_rows(s)),
        "mg_goal_order_n_default": any(
            g.get("order_n_basis") == "no_ladder_order_1_IS_total_value"
            for g in ami.goal_rows(s)),
        "mg_rung": all(g.get("magnitude_rung") for g in ami.goal_rows(s)),
        "mg_scope_clear": all(g.get("out_of_scope") == 0.0
                              for g in ami.goal_rows(s)),
        "mg_select": bool(ami.mag_selection(s).get("mg_sel_agid")),
        "mg_select_audit": ami.mag_selection(s).get("mg_sel_rung") is not None,
        "mg_select_runner_up": bool(
            ami.mag_selection(s).get("mg_sel_runner_up_agid")),
        "mg_select_margin": ami.mag_selection(s).get("mg_sel_margin") is not None,
        "mg_constraint_from_reply_conditioned": any(
            q.get("status") == "answered_conditioned"
            for q in ami.constraint_questions(s)),
    }
    assert all(fired.values()), [k for k, v in fired.items() if not v]

    s2, _ = _boot(with_attrition=False)
    assert any(s2.node(n)["attrs"]["basis"] == "NO_MEASURED_BASIS"
               for n in s2.nodes("ArcProjection")), \
        "mg_projection_mint_unmeasured never fired"

    s3, _ = _boot()
    _answer_horizon(s3, 5.0, ckind="scope", scope_seam="row_verdict")
    assert any(g.get("out_of_scope") == 1.0 for g in ami.goal_rows(s3)), \
        "mg_scope_charge never fired"
    assert any(q.get("status") == "answered_unconditioned"
               for q in ami.constraint_questions(s3)), \
        "mg_constraint_from_reply_unconditioned never fired"
    assert len(ami.constraint_questions(_boot()[0])) == 1, \
        "mg_ask_constraints never fired"


def test_the_fixpoint_TERMINATES_a_second_pass_moves_nothing():
    s, _ = _boot()
    _answer_horizon(s, 20.0, conditioned=True)
    before = sorted((g["agid"], g.get("orderN_headroom_n"),
                     g.get("magnitude_rung"), g.get("out_of_scope"))
                    for g in ami.goal_rows(s))
    n_before = (len(list(s.nodes("ArcGoal"))),
                len(list(s.nodes("ArcProjection"))),
                len(list(s.nodes("ArcConstraint"))),
                len(list(s.nodes("ArcConstraintQuestion"))))
    s._inner.run_rules()
    s._inner.run_rules()
    after = sorted((g["agid"], g.get("orderN_headroom_n"),
                    g.get("magnitude_rung"), g.get("out_of_scope"))
                   for g in ami.goal_rows(s))
    n_after = (len(list(s.nodes("ArcGoal"))),
               len(list(s.nodes("ArcProjection"))),
               len(list(s.nodes("ArcConstraint"))),
               len(list(s.nodes("ArcConstraintQuestion"))))
    assert before == after and n_before == n_after


def test_the_collapse_is_DETERMINISTIC_on_the_same_graph_state():
    s, _ = _boot()
    _answer_horizon(s, 20.0)
    term = _value_n_term()
    first, _ = _rank(s, term, "mh")
    for _ in range(4):
        s._inner.run_rules()
        again, _ = _rank(s, term, "mh")
        assert again == first


# =========================================================================== #
#  MG5 — no regression, no Python decisions, confinement.
# =========================================================================== #
def test_mg5_the_seed_regenerates_byte_identically():
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools",
                                      "build_arc_magnitude_seed.py"), "--check"],
        capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr


def test_mg5_the_EXISTING_seeds_are_BYTE_IDENTICAL_to_HEAD():
    """Confinement, asserted against git rather than promised.  This rung must
    not have moved `arc_goals`, `goal_residuals` or the synthesis seeds — if it
    had, `test_arc_goals_migrated`'s 37 gates would be measuring a moved
    target."""
    for rel in ("seeds/arc_goals.json", "seeds/goal_residuals.json",
                "seeds/program_synthesis.json", "seeds/gap_prioritization.json",
                "seeds/stopping_policy.json", "seeds/question_driving.json"):
        r = subprocess.run(["git", "diff", "--exit-code", "HEAD", "--", rel],
                           capture_output=True, text=True, cwd=ROOT)
        assert r.returncode == 0, (rel, r.stdout[:400])


def test_mg5_the_seed_is_NOT_globbed_into_every_agent_in_the_tree():
    """BOTH HALVES, because "absent" must not be mistaken for "safe": a full
    `_read_seeds` must skip it, AND the on-demand route must still work.
    Removing `self_load_only` is the tree-wide activation and needs A5's
    paired sweep."""
    assert _seed()["self_load_only"] is True
    from substrate.boot_all import _read_seeds
    loaded = _read_seeds(os.path.join(ROOT, "seeds"))
    assert "arc_magnitude" not in loaded, \
        "the seed IS globbed — it is live in every agent in the tree"
    assert "arc_goals" not in loaded, "its dependency is globbed too"
    assert manifest_for("arc_magnitude")["id"] == "arc_magnitude"
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    for sid in ("goal_residuals", "arc_goals"):
        s._inner.load_seed_manifest(manifest_for(sid), ag)
    assert ami.ensure_arc_magnitude(s, ag) is True
    assert ami.ensure_arc_magnitude(s, ag) is False
    assert any(r["name"].startswith("mg_") for r in s._inner.export_rules())


def test_mg5_no_python_decision_was_added():
    """The adapter is held to the module-specific form `arc_goal_ingest`
    passes.  Read through `ast` with string literals stripped — a source audit
    that greps the raw file greps its own docstring, and this one names the
    banned calls in prose."""
    path = os.path.join(ROOT, "domains", "arc_magnitude_ingest.py")
    tree = ast.parse(open(path).read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            node.value = ""
    src = ast.unparse(tree)
    for banned in ("import substrate_rs", ".evaluate(", "run_rules",
                   "graph_rewrite", "add_rule"):
        assert banned not in src, banned
    allowed = {"add_node", "node", "nodes", "set_attr", "remove_node",
               "add_edge_unchecked", "load_seed_manifest"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
            if node.attr.startswith("_") or node.attr in allowed:
                continue
    assert "_inner" in src  # the adapter does touch the substrate, mechanically


def test_mg5_the_arc_goals_gates_still_see_their_own_graph():
    """The order-1 collapse is UNTOUCHED by this rung: with `arc_magnitude`
    loaded, `ag_select` still picks the structural goal at value 10.0 with
    margin 2.3 — the numbers `test_arc_goals_migrated` pins."""
    s, _ = _boot()
    sel = agi.selection(s)
    assert sel["arc_sel_agid"] == STRUCTURAL
    assert abs(sel["arc_sel_value"] - 10.0) < 1e-9
    assert abs(sel["arc_sel_margin"] - 2.3) < 1e-9
    assert sel["arc_sel_headroom_n"] == 42


def test_mg5_JOB0_qd_decompose_is_RESIDENT_AND_DEAD_and_the_probe_can_tell():
    """JOB 0, gated so the finding cannot rot.  `SubgoalSpec` is minted nowhere
    in the tree, so `qd_decompose` can never fire — AND the same probe is shown
    able to make it fire when the population exists (A7)."""
    # 2026-08-04 — BOTH GREPS BECAME SELF-REFERENTIAL AND ARE NOW SCOPED TO
    # CODE-BEARING DIRECTORIES.  They originally ran tree-wide.  Recording the
    # finding defeated both of them: the write-up, the results artifact, the
    # measurement script and this test mention the edge name, and the write-up
    # QUOTES the mint pattern verbatim while stating that it never occurs — so
    # documenting the absence manufactured the presence.
    #
    # A first repair scoped only the edge grep and left the mint grep tree-wide
    # on the reasoning that "prose cannot satisfy it".  That was wrong, and it
    # failed immediately: prose containing the literal satisfies a literal
    # grep.  Recorded rather than quietly amended.
    #
    # THE MECHANISM CLAIM IS UNCHANGED — nothing in `seeds`, `domains`,
    # `substrate` or `runners` references the edge, and nothing there mints the
    # node.  Those are the only directories from which either could actually
    # happen; a markdown file cannot mint a node.  If a mint is ever added in
    # code, this still reds.
    _CODE_DIRS = ["seeds", "domains", "substrate", "runners"]
    r = subprocess.run(["git", "grep", "-l", "has_subgoal_spec", "--", *_CODE_DIRS],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.stdout.split() == ["seeds/question_driving.json"], r.stdout
    r2 = subprocess.run(["git", "grep", "-c", 'add_node("SubgoalSpec"',
                        "--", *_CODE_DIRS],
                        capture_output=True, text=True, cwd=ROOT)
    assert r2.stdout.strip() == "", r2.stdout

    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    s._inner.load_seed_manifest(manifest_for("question_driving"), ag)
    assert {"qd_decompose", "qd_compound_resolve", "qd_compound_wall"} <= \
        {x["name"] for x in s._inner.export_rules()}
    assert len(list(s.nodes("SubgoalSpec"))) == 0
    s._inner.run_rules()
    assert len(list(s.nodes("Goal"))) == 0

    parent = s.add_node("Goal", {"kind": "compound", "raw": "P",
                                 "gap_depth": 0.0, "status": "waiting"})
    s._inner.add_edge_unchecked(ag, "has_goal", parent)
    for raw in ("a", "b"):
        sp = s.add_node("SubgoalSpec", {"kind": "know", "raw": raw,
                                        "materialized": 0.0})
        s._inner.add_edge_unchecked(parent, "has_subgoal_spec", sp)
    s._inner.run_rules()
    assert len(list(s.nodes("Goal"))) == 3, "the probe cannot see liveness"
    for n in s.nodes("Goal"):
        if s.node(n)["attrs"].get("raw") in ("a", "b"):
            s.set_attr(n, "status", "resolved")
            s.set_attr(n, "answer", "A")
    s._inner.run_rules()
    assert s.node(parent)["attrs"]["status"] == "resolved"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
