"""test_arc_executor_migrated — AG-5, THE EXECUTOR AND THE STATUS LIFECYCLE.

Bars: `PROGRAM_SYNTHESIS_ARC6_PREREG.md` amendment A10 (`EX1`–`EX6`), registered
BEFORE this build.
Results: `PROGRAM_SYNTHESIS_ARC6_EXECUTOR.md`.
Seed:    `seeds/arc_executor.json` (emitted by `tools/build_arc_executor_seed.py`).

WHAT THIS GATES.  Two independent rungs stopped here.  The arc-goal rung had a
pool, a ranking, a lapse and an ask, and called itself *"a planning layer with
no hands"*; the magnitude rung found decomposition blocked because a parent
goal must LEAVE THE POOL and **nothing in this tree ever wrote a terminal
status**.  This suite gates the hands and the lifecycle.

EVERY GATE IS A LIVE INVOCATION AND THE HEADLINE ONE IS A REAL MEASUREMENT.
`live_run` actually re-runs the row-verdict ceiling — two 257-task battery arms,
a seed patch applied and reverted, and the constructed-witness report — on this
binary, and every downstream gate reads that same graph.  It takes ~100 seconds
and that is the point: a fixture would gate the bookkeeping and not the loop.

BOTH DIRECTIONS, ALWAYS.  *A bug in the refuting direction is indistinguishable
from an honest null*, so every "does not fire" is asserted in the same scene as
a "does fire", and per A7 a control is only admissible once it is shown CAPABLE
of expressing the difference it rules out.

Run:
  COLUMNS=250 OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \\
    pytest tests/test_arc_executor_migrated.py --confcutdir=<this worktree> -q
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
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

from domains import arc_executor as axe  # noqa: E402
from domains import arc_goal_ingest as agi  # noqa: E402
from domains import goal_residual_ingest as gri  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402

SEED_PATH = os.path.join(ROOT, "seeds", "arc_executor.json")
RID = "arc6.verdict.row_verdict_seed_only"
AGID = "arc.remeasure." + RID
RUNNER = "arc6_remeasure_row_verdict"
ARTIFACT = "results/arc6_verdict_pricing.json"

#  A15 -- the second ExecClass (the ceiling probe on the executor's reach).
RID_2 = "arc6.structural.enum_op_table"
AGID_2 = "arc.remeasure." + RID_2
RUNNER_2 = "arc6_remeasure_structural"
ARTIFACT_2 = "results/arc6_structural_ceiling.json"


# =========================================================================== #
#  PRECONDITION — assert the engine, do not merely record it.
# =========================================================================== #
def _assert_engine_coherent(s):
    """This rung's whole first job exists because the value layer distinguishes
    list from tuple on the intended binary.  Naming a sha proves which binary
    ran, not that it was the right one; this is behavioural.  Both-as-tuple
    means the tree is incoherent — STOP AND REPORT, never re-pin a bar to it."""
    n = s.add_node("ExecEngineProbe", {"lst": [1, 2, 3], "tup": (1, 2, 3)})
    a = s.node(n)["attrs"]
    assert a["lst"] != a["tup"], (
        "VALUE LAYER ABSENT — list and tuple collapsed.  Expected engine "
        "8311d4356082…; this is not a bar to re-pin.")
    return True


def _seed():
    with open(SEED_PATH) as fh:
        return json.load(fh)


def _seed_rule(name):
    for r in _seed()["rules"]:
        if r["name"] == name:
            return r
    raise AssertionError("no such rule in seeds/arc_executor.json: " + name)


def _code_only(path):
    """Source with every string literal removed.  A source audit that greps the
    raw file greps its own DOCSTRING — this module's adapter describes the
    banned calls in prose, so the naive form fails on itself."""
    import ast
    tree = ast.parse(open(path).read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            node.value = ""
    return ast.unparse(tree)


def _walk(term, kind):
    if isinstance(term, dict):
        if term.get("type") == kind:
            yield term
        for v in term.values():
            yield from _walk(v, kind)
    elif isinstance(term, list):
        for v in term:
            yield from _walk(v, kind)


def boot():
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    cls = s.add_node("Agent", {"is_class": True})
    s._inner.add_edge_unchecked(ag, "is_a", cls)
    for sid in ("program_synthesis", "goal_residuals", "arc_goals",
                "arc_executor"):
        s._inner.load_seed_manifest(manifest_for(sid), ag)
    s._inner.load_seed_manifest(manifest_for("math_capability_shapes"), ag)
    _assert_engine_coherent(s)
    gri.install_facts(s, gri.probe_facts(s))
    agi.set_measure_epoch(s, 0)
    return s, ag


def res(s, rid=RID):
    for n in s.nodes("GoalResidual"):
        if s.node(n)["attrs"].get("rid") == rid:
            return n
    raise AssertionError("no residual " + rid)


def goal(s, agid=AGID):
    for n in s.nodes("ArcGoal"):
        if s.node(n)["attrs"].get("agid") == agid:
            return n
    raise AssertionError("no goal " + agid)


def conds(s, rid=RID):
    return [dict(s.node(n)["attrs"]) for n in s.nodes("ResidualCondition")
            if s.node(n)["attrs"].get("rid") == rid]


def answer_open_questions(s, conditioned=False):
    sent = 0
    for n in s.nodes("ArcQuestion"):
        a = s.node(n)["attrs"]
        if a.get("answered") == 1.0 or a.get("status") != "open":
            continue
        if conditioned:
            agi.attach_reply(s, n, "worth it while the op table stands",
                             cond_kind="fact_equals",
                             cond_filter_value="arc6_structural_ceiling_present",
                             cond_expected_str="1")
        else:
            agi.attach_reply(s, n, "I do not know either.")
        sent += 1
    return sent


def sole_survivor(s, agid):
    """Retire every other goal so the collapse GENUINELY selects `agid`.

    Spoofing `arc_sel_agid` by hand does NOT work — `ag_select` re-fires inside
    the next fixpoint and overwrites it — which is itself the reason the
    executor cannot be pointed at a goal the pool did not choose."""
    for n in s.nodes("ArcGoal"):
        if s.node(n)["attrs"].get("agid") != agid:
            s.set_attr(n, "status", "retired")


# =========================================================================== #
#  THE LIVE RUN — shared by every downstream gate.
# =========================================================================== #
@pytest.fixture(scope="module")
def live_run():
    """Boot, let the collapse settle, let the world answer, dispatch, and RUN
    the measurement for real.  ~100 seconds.  Returns the graph afterwards
    together with the before/after snapshots taken around the execution."""
    s, ag = boot()
    s._inner.run_rules()
    assert answer_open_questions(s, conditioned=True) == 1, (
        "the shipped graph asks exactly one question; the scene changed")
    s._inner.run_rules()
    axe.arm(s)
    s._inner.run_rules()
    pending = axe.pending_orders(s)
    assert len(pending) == 1, "expected exactly one ExecOrder, got %d" % len(pending)

    before = {"pool": axe.pool(s),
              "stale": s.node(res(s))["attrs"].get("stale"),
              "conds": conds(s),
              "epoch": agi.measure_epoch(s),
              "status": s.node(goal(s))["attrs"].get("status"),
              "testimony": sorted(
                  (s.node(n)["attrs"]["rid"], s.node(n)["attrs"].get("stale"))
                  for n in s.nodes("GoalResidual")
                  if s.node(n)["attrs"].get("evidence_kind") == "utterance")}
    rec = axe.run_order(s, pending[0], tag="gate")
    axe.refresh_evidence_facts(s)
    s._inner.run_rules()
    after = {"pool": axe.pool(s),
             "stale": s.node(res(s))["attrs"].get("stale"),
             "conds": conds(s),
             "epoch": agi.measure_epoch(s),
             "status": s.node(goal(s))["attrs"].get("status"),
             "retired_because": s.node(goal(s))["attrs"].get("retired_because")}
    return {"s": s, "rec": rec, "before": before, "after": after}


# =========================================================================== #
#  EX1 — IT ACTUALLY RUNS, AND THE CONDITION REFRESHES
# =========================================================================== #
def test_ex1_the_executor_RUNS_the_measurement_LIVE(live_run):
    """Not a fixture: two 257-task battery arms, the seed patch applied and
    reverted, and the constructed-witness report, on THIS binary."""
    rec = live_run["rec"]
    assert rec["status"] == "ran", rec
    assert rec["runner"] == RUNNER
    assert rec["elapsed_seconds"] > 10, (
        "a re-measurement that took %.1fs did not run the battery"
        % rec["elapsed_seconds"])
    assert os.path.exists(os.path.join(ROOT, rec["artifact"]))


def test_ex1_the_fresh_artifact_was_measured_on_THIS_engine(live_run):
    """A number from an unknown binary is not a measurement (protocol §10)."""
    from domains.engine_provenance import provenance_stamp
    assert live_run["rec"]["engine_sha256"] == provenance_stamp()["sha256"]


def test_ex1_the_frozen_artifacts_are_STILL_byte_identical(live_run):
    """`arc6_verdict_report.py` hard-codes its input labels and output path, so
    the runner has to move the committed artifacts and the shipped
    `seeds/program_synthesis.json` out of the way.  Frozen artifacts are
    BYTE-frozen: the runner restores them in a `finally` and this asserts it
    against `HEAD`, not against the runner's own claim."""
    assert live_run["rec"]["protected_files_restored_byte_identical"] is True
    prefix = subprocess.run(["git", "-C", ROOT, "rev-parse", "--show-prefix"],
                            capture_output=True, text=True).stdout.strip()
    for rel in ("results/arc6_verdict_before.json",
                "results/arc6_verdict_after.json",
                "results/arc6_verdict_pricing.json",
                "seeds/program_synthesis.json"):
        head = subprocess.run(["git", "-C", ROOT, "show", "HEAD:" + prefix + rel],
                              capture_output=True, text=True).stdout
        assert head, rel
        assert head == open(os.path.join(ROOT, rel)).read(), (
            "%s was NOT restored — a re-measurement must not disturb the tree" % rel)


def test_ex1_the_CONDITION_REFRESHES_and_the_residual_un_stales(live_run):
    """THE BAR.  Before: the residual holds under
    `value_layer_list_eq_tuple == "1"`, the live value is `"0"`, so it is STALE.
    After: the condition is re-anchored to the world the RE-measurement was
    taken under (`"0"`), and `gr_condition_hold` — an existing rule, untouched —
    un-stales it.  The adapter never writes `stale`."""
    b, a = live_run["before"], live_run["after"]
    assert b["stale"] == 1.0
    assert a["stale"] == 0.0
    was = {c["filter_value"]: c.get("expected_str") for c in b["conds"]}
    now = {c["filter_value"]: c.get("expected_str") for c in a["conds"]}
    assert was["value_layer_list_eq_tuple"] == "1"
    assert now["value_layer_list_eq_tuple"] == "0"
    assert "remeasured_evidence_present." + RID in now, (
        "the fresh artifact must become evidence in its own right")


def test_ex1_the_residual_NUMBERS_come_from_the_fresh_artifact(live_run):
    """The re-ingest reads the SAME dotted paths `goal_residual_ingest.SPEC`
    used for the original ingest — nothing is transcribed and nothing is
    recomputed by a different route."""
    ri = live_run["rec"]["reingest"]
    assert ri["reingested"] is True
    doc = json.load(open(os.path.join(ROOT, ri["artifact"])))
    entry = [e for e in gri.SPEC if e["rid"] == RID][0]
    assert ri["residual_after"]["ceiling_honest_n"] == float(
        len(gri._at(doc, entry["honest_ids_path"])))
    assert ri["residual_after"]["denominator_n"] == float(
        len(gri._at(doc, entry["denominator_path"])))
    assert ri["residual_after"] != ri["residual_before"], (
        "a re-measurement that changed nothing is not a re-measurement")


def test_ex1_the_reanchor_is_NOT_a_tautology_it_can_re_fail(live_run):
    """A7: the re-anchored condition must be shown CAPABLE of going false, or
    'the condition now holds' has measured the write and not the world.

    The fresh artifact leaves the disk; the fact is re-probed; the residual
    goes stale again through `gr_condition_lapse`.  Restored, it holds again.
    Both directions, in one scene."""
    s = live_run["s"]
    r = res(s)
    art = os.path.join(ROOT, s.node(r)["attrs"]["evidence_artifact"])
    moved = art + ".ex1_probe"
    assert s.node(r)["attrs"].get("stale") == 0.0
    shutil.move(art, moved)
    try:
        axe.refresh_evidence_facts(s)
        s._inner.run_rules()
        assert s.node(r)["attrs"].get("stale") == 1.0, (
            "the re-anchored condition cannot re-fail — it is a tautology")
    finally:
        shutil.move(moved, art)
    axe.refresh_evidence_facts(s)
    s._inner.run_rules()
    assert s.node(r)["attrs"].get("stale") == 0.0


# =========================================================================== #
#  EX2 — TERMINAL STATUS, AND THE POOL SHRINKS BY EXACTLY ONE
# =========================================================================== #
def test_ex2_the_completed_goal_reaches_a_TERMINAL_status(live_run):
    a = live_run["after"]
    assert a["status"] == "retired"
    assert a["retired_because"] == "source_residual_no_longer_stale", (
        "the EXISTING retire rule must be what fired")


def test_ex2_the_pool_shrinks_by_EXACTLY_ONE(live_run):
    b, a = live_run["before"], live_run["after"]
    assert len(b["pool"]) - len(a["pool"]) == 1, (b["pool"], a["pool"])
    assert sorted(set(b["pool"]) - set(a["pool"])) == [AGID]
    assert sorted(set(a["pool"]) - set(b["pool"])) == [], (
        "nothing may join the pool in the same breath — that hides the "
        "retirement in a net count")


def test_ex2_the_order_CLOSES_and_closing_is_evidence_the_loop_closed(live_run):
    s = live_run["s"]
    orders = [dict(s.node(n)["attrs"]) for n in s.nodes("ExecOrder")]
    assert len(orders) == 1, orders
    assert orders[0]["status"] == "closed"
    assert orders[0]["outcome"] == "goal_retired_source_residual_no_longer_stale"


def test_ex2_the_retirement_is_STAMPED_with_its_epoch(live_run):
    """`ax_retired_epoch` — the anti-oscillation latch is defined in epochs and
    until this rung there was no producer, so there was nothing to stamp."""
    s = live_run["s"]
    assert s.node(goal(s))["attrs"].get("retired_epoch") == live_run["after"]["epoch"]


# =========================================================================== #
#  EX3 — THE EPOCH CLOCK STARTS
# =========================================================================== #
def test_ex3_the_executor_is_the_epochs_PRODUCER(live_run):
    b, a = live_run["before"], live_run["after"]
    assert b["epoch"] == "0" and a["epoch"] == "1"


def test_ex3_a_pending_UNCONDITIONED_reply_now_EXPIRES():
    """The Angluin mechanism ticking for the first time.  An answer with no
    counterexample carries ~0 bits and lasts one epoch — and until this rung
    that was true of a counter nobody incremented."""
    s, ag = boot()
    s._inner.run_rules()
    assert answer_open_questions(s, conditioned=False) == 1
    s._inner.run_rules()
    live = [(s.node(n)["attrs"]["rid"], s.node(n)["attrs"].get("stale"))
            for n in s.nodes("GoalResidual")
            if s.node(n)["attrs"].get("evidence_kind") == "utterance"]
    assert live and all(v == 0.0 for _, v in live), live

    axe.arm(s)
    s._inner.run_rules()
    pending = axe.pending_orders(s)
    assert len(pending) == 1
    #  The epoch bump is what the executor produces; here it is exercised
    #  without the 100-second battery by bumping through the SAME adapter call
    #  `run_order` makes, so the mechanism under test is the expiry.
    agi.bump_measure_epoch(s)
    s._inner.run_rules()
    after = [(s.node(n)["attrs"]["rid"], s.node(n)["attrs"].get("stale"))
             for n in s.nodes("GoalResidual")
             if s.node(n)["attrs"].get("evidence_kind") == "utterance"]
    assert all(v == 1.0 for _, v in after), after


def test_ex3_CONTROL_a_CONDITIONED_reply_survives_the_SAME_bump():
    """A7 in the strong form: the instrument must be shown capable of
    expressing the difference.  Identical scene, identical bump, the ONLY
    change is whether the reply named a checkable reason."""
    out = {}
    for conditioned in (False, True):
        s, ag = boot()
        s._inner.run_rules()
        answer_open_questions(s, conditioned=conditioned)
        s._inner.run_rules()
        agi.bump_measure_epoch(s)
        s._inner.run_rules()
        out[conditioned] = sorted(
            s.node(n)["attrs"].get("stale") for n in s.nodes("GoalResidual")
            if s.node(n)["attrs"].get("evidence_kind") == "utterance")
    assert out[False] == [1.0], out
    assert out[True] == [0.0], out


def test_ex3_an_UNANSWERED_question_lapses_at_the_next_epoch():
    """`ag_question_retire` — 'one question sits open on the shipped graph;
    it will lapse at the next epoch that never comes.'  It comes now."""
    s, ag = boot()
    s._inner.run_rules()
    q = [n for n in s.nodes("ArcQuestion")]
    assert len(q) == 1 and s.node(q[0])["attrs"]["status"] == "open"
    agi.bump_measure_epoch(s)
    s._inner.run_rules()
    assert s.node(q[0])["attrs"]["status"] == "unanswered_lapsed"


# =========================================================================== #
#  EX4 — ANTI-OSCILLATION, BOTH DIRECTIONS, EACH HALF LOAD-BEARING
# =========================================================================== #
@pytest.fixture(scope="module")
def latch_cells(live_run):
    """Walk the latch through its four cells on the LIVE post-execution graph."""
    s = live_run["s"]
    g, r = goal(s), res(s)
    cells = {}

    def snap(k):
        cells[k] = {"status": s.node(g)["attrs"].get("status"),
                    "stale": s.node(r)["attrs"].get("stale"),
                    "epoch": agi.measure_epoch(s),
                    "in_pool": AGID in axe.pool(s),
                    "rearm_count": s.node(g)["attrs"].get("rearm_count")}

    snap("A_after_execution")
    for _ in range(3):
        s._inner.run_rules()
    snap("B_churn_same_epoch")

    art = os.path.join(ROOT, s.node(r)["attrs"]["evidence_artifact"])
    moved = art + ".latch"
    shutil.move(art, moved)
    axe.refresh_evidence_facts(s)
    s._inner.run_rules()
    snap("C_refailed_SAME_epoch")

    agi.bump_measure_epoch(s)
    s._inner.run_rules()
    snap("D_refailed_AND_epoch_advanced")

    shutil.move(moved, art)
    axe.refresh_evidence_facts(s)
    s._inner.run_rules()
    snap("E_world_restored")
    return cells


def test_ex4_direction_1_a_retired_goal_does_NOT_re_mint_on_churn(latch_cells):
    assert latch_cells["B_churn_same_epoch"]["status"] == "retired"
    assert latch_cells["B_churn_same_epoch"]["in_pool"] is False


def test_ex4_the_EPOCH_half_of_the_latch_is_load_bearing(latch_cells):
    """The condition has GENUINELY re-failed and the goal still does not come
    back, because the measurement epoch has not advanced.  Hold one half fixed
    and the other is shown to be doing work — otherwise 'it did not re-mint' is
    consistent with the rule never firing at all."""
    c = latch_cells["C_refailed_SAME_epoch"]
    assert c["stale"] == 1.0, "the condition did not actually re-fail"
    assert c["status"] == "retired"
    assert c["in_pool"] is False


def test_ex4_direction_2_it_DOES_re_mint_when_the_condition_genuinely_re_fails(
        latch_cells):
    """It comes back to a NON-TERMINAL status and re-enters the pool.

    MEASURED: it may read `pursued` rather than `minted`, because once it is
    back in the pool it is again the collapse's winner and `ax_dispatch` — with
    the arming stamp still on it from before — orders it in the same fixpoint.
    That is the loop working, not a defect, so the bar is asserted as
    NON-TERMINAL AND IN POOL rather than as one particular string."""
    d = latch_cells["D_refailed_AND_epoch_advanced"]
    assert d["stale"] == 1.0
    assert d["status"] not in ("retired", "settled"), d
    assert d["status"] in ("minted", "pursued"), d
    assert d["in_pool"] is True
    assert d["rearm_count"] == 1.0


def test_ex4_the_STALE_half_of_the_latch_is_load_bearing(latch_cells):
    """Between B and D the epoch advanced too — so the other control is that a
    LATER epoch with the condition HOLDING does not re-arm.  Cell E is that:
    epoch 2, condition restored, and the goal returns to terminal rather than
    sitting in the pool."""
    e = latch_cells["E_world_restored"]
    assert e["stale"] == 0.0
    assert e["status"] == "retired", (
        "with its condition holding again the goal must be terminal again — "
        "a one-way re-arm is a ratchet, not a latch")
    assert e["rearm_count"] == 1.0, "it must not re-arm a second time"


def test_ex4_the_round_trip_CLOSES(latch_cells):
    """terminal → terminal → terminal → BACK IN THE POOL → terminal again."""
    terminal = [latch_cells[k]["status"] == "retired" for k in
                ("A_after_execution", "B_churn_same_epoch",
                 "C_refailed_SAME_epoch", "D_refailed_AND_epoch_advanced",
                 "E_world_restored")]
    assert terminal == [True, True, True, False, True], \
        [latch_cells[k]["status"] for k in
         ("A_after_execution", "B_churn_same_epoch", "C_refailed_SAME_epoch",
          "D_refailed_AND_epoch_advanced", "E_world_restored")]


# =========================================================================== #
#  CONFINEMENT — structural, not promised
# =========================================================================== #
def test_confinement_only_ONE_goal_kind_is_executable():
    """Every goal is made the collapse's GENUINE winner in turn (all others
    retired) and the executor is armed on it.  Exactly one mints an order."""
    s0, _ = boot()
    s0._inner.run_rules()
    agids = sorted(s0.node(n)["attrs"]["agid"] for n in s0.nodes("ArcGoal"))
    assert len(agids) == 8, agids
    ordered = []
    for agid in agids:
        s, _ = boot()
        s._inner.run_rules()
        sole_survivor(s, agid)
        s._inner.run_rules()
        armed = axe.arm(s)
        assert armed["arc_exec_armed_agid"] == agid, (
            "the scene did not make %s the winner" % agid)
        s._inner.run_rules()
        if [n for n in s.nodes("ExecOrder")
                if s.node(n)["attrs"].get("agid") == agid]:
            ordered.append(agid)
    assert ordered == [AGID], ordered


def test_confinement_a_TESTIMONY_sourced_re_measure_goal_is_REFUSED():
    """THE CASE THAT FOUND THE ROUTE KEY, and it is not hypothetical.

    An unconditioned reply expires at the next epoch; `ag_mint_remeasure` then
    fires ON THE TESTIMONY and mints
    `arc.remeasure.arc.testimony.<region>` with `kind: "re_measure"` and NO
    `evidence_artifact`.  A route keyed on `kind` alone — which is what this
    rung shipped first — would have handed the human's own expired answer to
    the row-verdict runner.  The key is (kind, evidence_artifact, source_rid).
    """
    s, _ = boot()
    s._inner.run_rules()
    answer_open_questions(s, conditioned=False)
    s._inner.run_rules()
    agi.bump_measure_epoch(s)
    s._inner.run_rules()
    born = [dict(s.node(n)["attrs"]) for n in s.nodes("ArcGoal")
            if str(s.node(n)["attrs"].get("agid", "")).startswith(
                "arc.remeasure.arc.testimony.")]
    assert born, "the scene no longer produces a testimony-sourced re-measure goal"
    assert born[0]["kind"] == "re_measure", "it must carry the EXECUTABLE kind"
    assert born[0].get("evidence_artifact") is None
    sole_survivor(s, born[0]["agid"])
    s._inner.run_rules()
    axe.arm(s)
    s._inner.run_rules()
    assert not [n for n in s.nodes("ExecOrder")
                if s.node(n)["attrs"].get("agid") == born[0]["agid"]]


def test_confinement_the_route_key_has_THREE_parts_and_each_is_asserted():
    """Read off the emitted seed, so a future edit that drops a key is loud."""
    r = _seed_rule("ax_dispatch")
    keys = set()
    for eq in _walk(r["where"], "Eq"):
        for side in ("a", "b"):
            t = eq.get(side) or {}
            if t.get("type") == "Attr":
                keys.add(t.get("key"))
    for k in ("kind", "evidence_artifact", "rid", "source_rid"):
        assert k in keys, (k, sorted(keys))
    cls = [n for n in _seed()["nodes"] if n["type"] == "ExecClass"]
    assert len(cls) == 2, (
        "A15 -- the ceiling probe on the executor's reach.  This PIN is "
        "INVERTED, not removed (the WH1 precedent): AG-5/A11/A12/A13/A14 "
        "each measured the executor's reach as exactly one ExecClass, and "
        "this asserted it structurally.  A15 wired a genuine second "
        "residual (arc6.structural.enum_op_table) behind ZERO rule changes "
        "-- ax_dispatch/ROUTE/_routable already filter over every "
        "ExecClass node -- so the count changing from one to two, with the "
        "three-part-key assertion above UNCHANGED, is the confinement "
        "still holding on a wider table, not a weakened guard.")
    by_runner = {c["attrs"]["runner"]: c["attrs"] for c in cls}
    assert sorted(by_runner) == sorted([RUNNER, RUNNER_2])
    assert by_runner[RUNNER]["evidence_artifact"] == ARTIFACT
    assert by_runner[RUNNER]["source_rid"] == RID
    assert by_runner[RUNNER_2]["evidence_artifact"] == ARTIFACT_2
    assert by_runner[RUNNER_2]["source_rid"] == RID_2
    #  The two classes disagree on BOTH keys, never just one -- if they ever
    #  shared an evidence_artifact or a source_rid, `_routable`'s Argmin
    #  could bind a goal to the wrong runner (WH4's own measured hazard for
    #  a kind-only key, one level down for a partially-shared key).
    assert by_runner[RUNNER]["evidence_artifact"] != by_runner[RUNNER_2]["evidence_artifact"]
    assert by_runner[RUNNER]["source_rid"] != by_runner[RUNNER_2]["source_rid"]


def test_confinement_the_capability_TABLE_refuses_an_unknown_runner():
    """The adapter half.  A `runner` name with no table entry is recorded and
    refused; it is never a path, never an argv word and never reaches a shell."""
    assert sorted(axe.RUNNERS) == sorted([RUNNER, RUNNER_2]), (
        "A15 -- inverted, not removed, same reason as the ExecClass count "
        "pin above: the capability table now names TWO permitted runners.")
    s, _ = boot()
    s._inner.run_rules()
    a = [n for n in s.nodes("ArcAgenda")][0]
    o = s.add_node("ExecOrder", {"agid": "forged", "runner": "not_a_runner",
                                 "status": "ordered", "ordered_epoch": "0"})
    s._inner.add_edge_unchecked(a, "has_exec_order", o)
    rec = axe.run_order(s, o)
    assert rec["status"] == "refused"
    assert s.node(o)["attrs"]["refused_because"] == \
        "runner_name_not_in_the_capability_table"


# =========================================================================== #
#  A15 — THE SECOND ExecClass (the ceiling probe on the executor's reach)
#
#  PROGRAM_SYNTHESIS_ARC6_PREREG.md amendment A15.  Four consecutive rungs
#  (A10/A11/A12/A13/A14) each independently measured the executor's reach as
#  EXACTLY ONE ExecClass.  This wires a genuine second one — the structural-
#  ceiling residual (`arc6.structural.enum_op_table`) — behind ZERO new
#  rules: `ax_dispatch`/`ROUTE`/`_routable`/`_dispatchable` already filter
#  over every `ExecClass` node via the three-part key, so this is SEED DATA,
#  not a rule edit.  See PROGRAM_SYNTHESIS_ARC6_SECOND_EXECCLASS.md.
#
#  THE STALENESS TRIGGER IS SYNTHETIC; THE MEASUREMENT IS NOT.  A15's own
#  design investigation found that `probe_facts`'s `expected_shas` argument —
#  the thing that would make `arc6_structural_ceiling_present` track CONTENT
#  drift, not just file presence — is never wired by any caller in this
#  tree, so the condition cannot organically detect that a re-run produces
#  different content (it was measured to: witness_ids grew 7 -> 9 on this
#  engine vs the committed evidence).  Every scene below therefore forces
#  eligibility with a `_put_fact` POKE — the SAME "narrow attribute poke"
#  methodology A13 SS7.1 validated for `headroom_n -> 0` (not a file
#  deletion: the real, committed artifact stays on disk and untouched, which
#  matters because the runner's own stash step assumes it is present) — but
#  the RE-MEASUREMENT ITSELF, once ordered, is a REAL subprocess invocation
#  of the unmodified `scripts/arc6_structural_ceiling.py` on this engine.
# =========================================================================== #
def test_a15_the_structural_residual_is_UNWIRED_by_default():
    """Adding the second ExecClass changed NOTHING about the shipped boot's
    default pool composition — the structural residual's condition still
    organically holds (only file-PRESENCE is checked, and the committed
    artifact is present), so no second `re_measure` goal exists until forced.
    This is the confinement AG-5's own boot-time free exercise, one level up:
    a wider capability table does not by itself create new work."""
    s, _ = boot()
    s._inner.run_rules()
    agids = sorted(s.node(n)["attrs"]["agid"] for n in s.nodes("ArcGoal"))
    assert len(agids) == 8, agids
    assert AGID in agids
    assert AGID_2 not in agids, (
        "the structural residual must NOT be stale on the untouched boot")


def _force_structural_stale(s):
    """The narrow poke (A13 SS7.1 precedent): write the ResidualFact the
    condition reads directly, WITHOUT touching the real, committed file."""
    axe._put_fact(s, "arc6_structural_ceiling_present", "0")


def test_a15_forcing_staleness_MINTS_the_second_remeasure_goal_and_it_ROUTES():
    """The bar: a genuinely SECOND `re_measure` goal, routed to its OWN
    runner via the three-part key, with zero cross-talk to the first class."""
    s, ag = boot()
    s._inner.run_rules()
    _force_structural_stale(s)
    s._inner.run_rules()
    born = [dict(s.node(n)["attrs"]) for n in s.nodes("ArcGoal")
            if s.node(n)["attrs"].get("agid") == AGID_2]
    assert born, "the structural residual did not mint a re-measure goal"
    assert born[0]["kind"] == "re_measure"
    assert born[0]["evidence_artifact"] == ARTIFACT_2

    sole_survivor(s, AGID_2)
    s._inner.run_rules()
    axe.arm(s)
    s._inner.run_rules()
    pending = axe.pending_orders(s)
    assert len(pending) == 1, pending
    o = s.node(pending[0])["attrs"]
    assert o["runner"] == RUNNER_2
    assert o["exec_class"] == "re_measure"
    assert o["evidence_artifact"] == ARTIFACT_2


def test_a15_the_two_classes_NEVER_cross_route():
    """Both directions, per this suite's own standing discipline (A7): the
    row-verdict goal must never be handed the structural runner, and the
    structural goal must never be handed the row-verdict runner."""
    #  Direction 1: row-verdict alone (structural NOT stale) -> RUNNER.
    s, ag = boot()
    s._inner.run_rules()
    sole_survivor(s, AGID)
    s._inner.run_rules()
    axe.arm(s)
    s._inner.run_rules()
    pending = axe.pending_orders(s)
    assert len(pending) == 1
    assert s.node(pending[0])["attrs"]["runner"] == RUNNER

    #  Direction 2: structural alone (forced stale, row-verdict retired) ->
    #  RUNNER_2, never RUNNER.
    s2, ag2 = boot()
    s2._inner.run_rules()
    _force_structural_stale(s2)
    s2._inner.run_rules()
    sole_survivor(s2, AGID_2)
    s2._inner.run_rules()
    axe.arm(s2)
    s2._inner.run_rules()
    pending2 = axe.pending_orders(s2)
    assert len(pending2) == 1
    assert s2.node(pending2[0])["attrs"]["runner"] == RUNNER_2
    assert s2.node(pending2[0])["attrs"]["runner"] != RUNNER


def test_a15_TWO_simultaneously_routable_goals_still_SERIALIZE_to_ONE_order():
    """A15's own motivating scenario, never exercised by any prior rung
    because there was only ever one executable goal: with the second
    ExecClass wired, this engine's shipped boot ALREADY has one organically
    stale residual (row-verdict — `value_layer_list_eq_tuple == '0'` on this
    engine) and can now ALSO carry a second, forced-stale one (structural)
    in the SAME pool at once.  `ax_dispatch`'s own comment claims 'at most
    one outstanding order globally' via a `Not(Exists(ExecOrder,
    status='ordered'))` guard — this is the first LIVE test of that guard
    under real multi-candidate contention, not just a read of the rule."""
    s, ag = boot()
    s._inner.run_rules()
    _force_structural_stale(s)
    s._inner.run_rules()
    agids = set(s.node(n)["attrs"]["agid"] for n in s.nodes("ArcGoal"))
    assert AGID in agids and AGID_2 in agids, (
        "both residuals must be simultaneously stale for this scene", agids)
    axe.arm(s)
    s._inner.run_rules()
    orders = [dict(s.node(n)["attrs"]) for n in s.nodes("ExecOrder")]
    assert len(orders) == 1, (
        "two simultaneously routable goals minted more than one order in "
        "one fixpoint — the serialization guard is not load-bearing", orders)
    assert orders[0]["agid"] in (AGID, AGID_2)
    assert orders[0]["runner"] in (RUNNER, RUNNER_2)


# =========================================================================== #
#  A15 — THE LIVE RUN.  A real subprocess invocation of
#  scripts/arc6_structural_ceiling.py, on THIS engine, protected-file
#  stash/restore around it (never run without a stash — A15's own design
#  investigation tripped exactly this hazard once and recorded the
#  recovery in the results doc).
# =========================================================================== #
def _sole_survivor_no_retire(s, agid):
    """Like `sole_survivor`, but leaves every OTHER goal's pool membership
    via `headroom_n -> 0` rather than `status: 'retired'` — the SAME
    distinction `_leave_pool_without_retiring` documents below, for the
    identical reason, found live while building this fixture: `sole_survivor`
    followed by a REAL run that bumps the measurement epoch (this fixture
    calls `axe.run_order`, unlike every other scene that uses
    `sole_survivor`) lets `ax_rearm` legitimately re-admit a goal whose
    underlying residual is STILL genuinely stale on this engine (true of the
    row-verdict goal here) — that is the anti-oscillation latch working
    correctly, not a bug, but it silently reintroduces AGID into the pool
    between `before` and `after` and confounds the pool-shrinks-by-one
    reading.  `headroom_n -> 0` never sets `status`, so `ax_rearm`'s
    `status=='retired'` guard never matches and this cannot happen."""
    for n in s.nodes("ArcGoal"):
        if s.node(n)["attrs"].get("agid") != agid:
            s.set_attr(n, "headroom_n", 0.0)


@pytest.fixture(scope="module")
def live_run_structural():
    s, ag = boot()
    s._inner.run_rules()
    before_sha = axe._sha256(os.path.join(ROOT, ARTIFACT_2))
    _force_structural_stale(s)
    s._inner.run_rules()
    _sole_survivor_no_retire(s, AGID_2)
    s._inner.run_rules()
    axe.arm(s)
    s._inner.run_rules()
    pending = axe.pending_orders(s)
    assert len(pending) == 1, "expected exactly one ExecOrder, got %d" % len(pending)

    before = {"pool": axe.pool(s),
              "stale": s.node(res(s, RID_2))["attrs"].get("stale"),
              "status": s.node(goal(s, AGID_2))["attrs"].get("status")}
    rec = axe.run_order(s, pending[0], tag="a15gate")
    axe.refresh_evidence_facts(s)
    s._inner.run_rules()
    after = {"pool": axe.pool(s),
             "stale": s.node(res(s, RID_2))["attrs"].get("stale"),
             "status": s.node(goal(s, AGID_2))["attrs"].get("status"),
             "retired_because": s.node(goal(s, AGID_2))["attrs"].get("retired_because")}
    return {"s": s, "rec": rec, "before": before, "after": after,
            "before_sha": before_sha}


def test_a15_it_actually_RUNS_the_structural_remeasurement_LIVE(live_run_structural):
    """Not a fixture: a real subprocess invocation of the unmodified
    measurement script, on this engine."""
    rec = live_run_structural["rec"]
    assert rec["status"] == "ran", rec
    assert rec["runner"] == RUNNER_2
    assert os.path.exists(os.path.join(ROOT, rec["artifact"]))
    from domains.engine_provenance import provenance_stamp
    assert rec["engine_sha256"] == provenance_stamp()["sha256"]


def test_a15_the_frozen_structural_artifact_is_STILL_byte_identical(live_run_structural):
    """The runner must save the one committed artifact and restore it
    byte-for-byte in a `finally` — asserted against a sha taken BEFORE the
    run (this checkout's `results/` is gitignored, so `git show HEAD:...`
    is not a usable witness here — see the pre-existing, environment-
    conditional red on the row-verdict version of this same assertion)."""
    assert live_run_structural["rec"]["protected_files_restored_byte_identical"] is True
    after_sha = axe._sha256(os.path.join(ROOT, ARTIFACT_2))
    assert after_sha == live_run_structural["before_sha"], (
        "the committed structural-ceiling artifact was NOT restored")


def test_a15_the_fresh_measurement_genuinely_DIFFERS_from_committed_evidence(live_run_structural):
    """The load-bearing finding this candidate was picked FOR (A15's design
    investigation item 7): re-running this residual's measurement on this
    engine is not a no-op — it finds MORE witnesses than the committed
    evidence (measured on an older engine), which the current condition
    mechanism cannot see on its own (item 6) but which a live re-run does."""
    ri = live_run_structural["rec"]["reingest"]
    assert ri["reingested"] is True
    fresh = json.load(open(os.path.join(ROOT, live_run_structural["rec"]["artifact"])))
    committed = json.load(open(os.path.join(ROOT, ARTIFACT_2)))
    fresh_witnesses = set(fresh.get("witness_ids") or [])
    committed_witnesses = set(committed.get("witness_ids") or [])
    assert fresh_witnesses != committed_witnesses, (
        "a re-measurement that changed nothing is not a re-measurement",
        sorted(fresh_witnesses), sorted(committed_witnesses))
    assert ri["residual_after"] != ri["residual_before"]


def test_a15_the_CONDITION_REANCHORS_and_the_residual_UNSTALES(live_run_structural):
    """Mirrors EX1's own bar for the first ExecClass: the condition is
    re-anchored to the world as probed AT re-measurement time (here, the
    committed file's real presence, restored by the runner's own `finally`
    before this re-ingest runs), and un-stales through the EXISTING,
    UNMODIFIED `gr_condition_hold` — the adapter never writes `stale`."""
    b, a = live_run_structural["before"], live_run_structural["after"]
    assert b["stale"] == 1.0
    assert a["stale"] == 0.0
    assert a["status"] == "retired"
    assert a["retired_because"] == "source_residual_no_longer_stale"
    assert len(b["pool"]) - len(a["pool"]) == 1
    assert sorted(set(b["pool"]) - set(a["pool"])) == [AGID_2]


def test_a15_the_seed_added_ZERO_new_rules():
    """EC2/EC3's own headline cost claim, gated rather than left as prose:
    the second ExecClass is a seed DATA addition. Five rules before A15
    (AG-5's four plus A13's ax_impotent); five rules after A15 — asserted
    below as a SUBSET, not the total, because A18 added a SIXTH rule
    (`ax_world_probe_epoch`) afterwards. The WH1 precedent: invert a pin
    with a docstring, never silently remove it — A15's own claim (zero NEW
    rules, only seed DATA) is still true and still checked; it is just no
    longer the total rule count, which `test_a18_AR18d_the_new_rule_is_the_
    ONLY_addition_to_the_seed` now asserts instead."""
    names = set(r["name"] for r in _seed()["rules"])
    assert names >= {"ax_dispatch", "ax_retired_epoch", "ax_rearm", "ax_close",
                      "ax_impotent"}, names


def test_a15_no_third_party_dependency_in_the_new_runner():
    """The cost-comparison finding that RULED OUT seam A (`sympy`, not
    importable under this tree's default `python3` — A15 item 8): the
    chosen runner imports nothing beyond the stdlib."""
    import ast
    tree = ast.parse(open(os.path.join(
        ROOT, "scripts", "arc6_remeasure_structural.py")).read())
    STDLIB = {"__future__", "hashlib", "json", "os", "shutil", "subprocess",
              "sys", "tempfile", "time"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] in STDLIB, alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] in STDLIB, node.module


def test_a15_the_new_runner_makes_no_decision_either():
    """Mirrors `test_ex6_the_runner_makes_no_decision_either` for the second
    runner: it never touches the substrate at all."""
    src = _code_only(os.path.join(ROOT, "scripts",
                                  "arc6_remeasure_structural.py"))
    for banned in ("import substrate_rs", "substrate_rs", ".evaluate(",
                   "run_rules", "ArcGoal", "GoalResidual"):
        assert banned not in src, banned


# =========================================================================== #
#  THE TRANSIENT-STAMP HAZARD — the bug this rung found in itself
# =========================================================================== #
def test_the_stamp_is_a_TRANSIENT_inside_the_fixpoint_that_writes_it():
    """MEASURED, and it is why `ax_dispatch` needs the two-tick agreement.

    `run_rules` is a fixpoint with no rule ordering, so `ag_select`'s
    `arc_sel_agid` is a TRANSIENT while `ag_mint_*` is still populating the
    pool.  The first draft of `ax_dispatch` read it in the same fixpoint and
    ordered the RUNNER-UP on the shipped boot — nothing errored, the wrong
    thing simply happened.  This gate asserts the guard, in both directions:
    unarmed nothing dispatches however the fixpoint wobbles; armed on the
    SETTLED winner it does."""
    s, _ = boot()
    s._inner.run_rules()
    assert list(s.nodes("ExecOrder")) == [], (
        "an order minted with nothing armed — the guard is not load-bearing")
    settled = agi.selection(s).get("arc_sel_agid")
    assert settled == "arc.supply.arc6.seam_a.import_oracle." \
                      "missing_structural_primitive", settled

    #  Armed on the settled (unroutable) winner: still nothing, and that is the
    #  confinement branch exercised by the SHIPPED BOOT rather than a fixture.
    axe.arm(s)
    s._inner.run_rules()
    assert list(s.nodes("ExecOrder")) == []

    #  The world answers; the collapse now settles on the re-measurement goal;
    #  armed on THAT, an order mints.
    answer_open_questions(s, conditioned=True)
    s._inner.run_rules()
    assert agi.selection(s).get("arc_sel_agid") == AGID
    axe.arm(s)
    s._inner.run_rules()
    orders = [dict(s.node(n)["attrs"]) for n in s.nodes("ExecOrder")]
    assert [o["agid"] for o in orders] == [AGID]
    assert orders[0]["runner"] == RUNNER


def test_the_armed_stamp_cannot_be_SPOOFED_from_outside():
    """Writing `arc_sel_agid` by hand does not point the executor anywhere:
    `ag_select` re-fires inside the next fixpoint and overwrites it, so the
    armed value stops agreeing.  The executor can only act on what the pool
    actually chose."""
    s, _ = boot()
    s._inner.run_rules()
    a = [n for n in s.nodes("ArcAgenda")][0]
    for k, v in (("arc_sel_agid", AGID), ("arc_sel_value", 999.0),
                 ("arc_exec_armed_agid", AGID), ("arc_exec_armed_value", 999.0)):
        s.set_attr(a, k, v)
    s._inner.run_rules()
    assert list(s.nodes("ExecOrder")) == [], (
        "a hand-written stamp dispatched a job")


# =========================================================================== #
#  TWO COLLAPSES — A11 / WH1.  THE HANDS NOW FOLLOW ORDER-N.
#
#  This block REPLACES `test_the_hands_follow_ag_select_NOT_the_magnitude_
#  collapse`, which pinned the pre-A11 wiring and said in its own docstring
#  that it existed "so that wiring order-N in is a LOUD change rather than a
#  silent one".  A11 made that change deliberately; the pin has been INVERTED
#  rather than deleted, so the property is still gated in both directions.
# =========================================================================== #
def _boot_with_magnitude(ladder=True):
    from domains import arc_magnitude_ingest as ami
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    cls = s.add_node("Agent", {"is_class": True})
    s._inner.add_edge_unchecked(ag, "is_a", cls)
    for sid in ("program_synthesis", "goal_residuals", "arc_goals",
                "arc_magnitude", "arc_executor"):
        s._inner.load_seed_manifest(manifest_for(sid), ag)
    s._inner.load_seed_manifest(manifest_for("math_capability_shapes"), ag)
    _assert_engine_coherent(s)
    gri.install_facts(s, gri.probe_facts(s))
    agi.set_measure_epoch(s, 0)
    ami.resolve_attrition_keys(s)
    if ladder:
        ami.install_tier_ladder(s, ami.probe_tier_ladder())
    return s, ag


def test_wh1_the_hands_now_follow_the_ORDER_N_collapse():
    """A11/WH1.  With the measured tier ladder installed the two collapses
    DISAGREE on the shipped boot — `ag_select` names the 42-task blocker
    (undiscounted paper inventory, no `ExecClass`) and `mg_select` names the
    re-measurement goal, the one goal this executor can run.  The hands follow
    order-N, and they do it **with no human reply anywhere in the scene**.

    Asserted on the ORDER, not on the adapter's return value: the order carries
    `selected_by` and both collapses' stamps as it saw them, so "acted on a goal
    order-1 did not choose" is a graph fact."""
    s, _ = _boot_with_magnitude(ladder=True)
    s._inner.run_rules()
    at = s.node([n for n in s.nodes("ArcAgenda")][0])["attrs"]
    assert at["arc_sel_agid"] != at["mg_sel_agid"], (
        "the two collapses agree — the divergence WH1 is about is not present")
    assert at["mg_sel_agid"] == AGID, at["mg_sel_agid"]
    order1_winner = at["arc_sel_agid"]

    axe.arm(s)
    s._inner.run_rules()
    orders = [dict(s.node(n)["attrs"]) for n in s.nodes("ExecOrder")]
    assert [o["agid"] for o in orders] == [AGID], [o["agid"] for o in orders]
    o = orders[0]
    assert o["runner"] == RUNNER
    assert o["selected_by"] == "order_n_mg_select", o["selected_by"]
    assert o["order1_sel_agid"] == order1_winner
    assert o["orderN_sel_agid"] == AGID
    assert o["agid"] != o["order1_sel_agid"], (
        "the executor acted on the goal order-1 had already chosen — this "
        "scene cannot show the swap")
    #  Nobody was asked and nobody replied.
    assert all(q.get("answered") != 1.0 for q in agi.questions(s))


def test_wh1_CONTROL_without_the_tier_ladder_the_two_collapses_AGREE():
    """A7: the swap must be shown to be the LADDER's divergence, not a property
    of loading `arc_magnitude`.  Same seeds, same boot, ladder withheld — the
    two collapses agree on the blocker and NOTHING dispatches, for the same
    structural reason as always (the winner has no `ExecClass`)."""
    s, _ = _boot_with_magnitude(ladder=False)
    s._inner.run_rules()
    at = s.node([n for n in s.nodes("ArcAgenda")][0])["attrs"]
    assert at["arc_sel_agid"] == at["mg_sel_agid"], (
        "the collapses diverged without the ladder — the control is not a "
        "control")
    axe.arm(s)
    s._inner.run_rules()
    assert list(s.nodes("ExecOrder")) == []


def test_wh3_the_fallback_when_the_order_N_collapse_is_NOT_on_the_graph():
    """`arc_magnitude` is `self_load_only` and is NOT in this seed's
    `depends_on`, so the executor must still work on a graph that has never
    heard of the order-N collapse.  `mg_sel_agid` is absent, `SEL_AGID` takes
    the order-1 branch, and the shipped boot behaves exactly as it did before
    A11: armed on the settled (unroutable) winner, nothing mints; after a reply
    moves the collapse onto the re-measurement goal, an order mints and records
    that it followed order-1."""
    s, _ = boot()                       # no arc_magnitude
    s._inner.run_rules()
    at = s.node([n for n in s.nodes("ArcAgenda")][0])["attrs"]
    assert at.get("mg_sel_agid") is None
    axe.arm(s)
    s._inner.run_rules()
    assert list(s.nodes("ExecOrder")) == []

    answer_open_questions(s, conditioned=True)
    s._inner.run_rules()
    assert agi.selection(s).get("arc_sel_agid") == AGID
    axe.arm(s)
    s._inner.run_rules()
    orders = [dict(s.node(n)["attrs"]) for n in s.nodes("ExecOrder")]
    assert [o["agid"] for o in orders] == [AGID]
    assert orders[0]["selected_by"] == "order_1_ag_select"


def test_wh3_arming_on_the_ORDER_1_winner_no_longer_dispatches_under_order_N():
    """The inverted pin, and the half that makes the swap load-bearing rather
    than additive: with the order-N collapse live and disagreeing, arming ONLY
    the order-1 stamps must mint nothing.  Without this the suite would be
    consistent with a rule that follows whichever stamp happens to be set."""
    s, _ = _boot_with_magnitude(ladder=True)
    s._inner.run_rules()
    a = [n for n in s.nodes("ArcAgenda")][0]
    at = s.node(a)["attrs"]
    assert at["arc_sel_agid"] != at["mg_sel_agid"]
    s.set_attr(a, "arc_exec_armed_agid", at["arc_sel_agid"])
    s.set_attr(a, "arc_exec_armed_value", at["arc_sel_value"])
    s._inner.run_rules()
    assert list(s.nodes("ExecOrder")) == [], (
        "the order-1 stamps alone dispatched a job while order-N was live")


def test_wh3_the_ORDER_N_stamp_OUTLIVES_the_pool_and_the_pool_guard_catches_it():
    """`ax_dispatch`'s comment item (3) says the pool predicate is re-asserted on
    the bound goal because *"ag_select writes arc_sel_agid only while the pool is
    non-empty, so the stamp can outlive its goal's membership."*  `mg_select`'s
    guard is the SAME lifted pool `Exists` — `Exists(POOL_AS("mgx"), True)` — so
    the order-N stamp inherits the identical exposure, and the swap does not
    weaken the guard because the guard is on the BOUND GOAL and does not care
    which stamp bound it.

    Both directions, live: the stamp really does outlive membership (a claim
    about the exposure, not about the guard), and nothing dispatches anyway."""
    s, _ = _boot_with_magnitude(ladder=True)
    s._inner.run_rules()
    a = [n for n in s.nodes("ArcAgenda")][0]
    assert s.node(a)["attrs"]["mg_sel_agid"] == AGID
    axe.arm(s)
    #  Empty the pool entirely, so `mg_select`'s own Exists guard is false and
    #  it cannot rewrite the stamp.
    for n in s.nodes("ArcGoal"):
        s.set_attr(n, "status", "retired")
    s._inner.run_rules()
    assert axe.pool(s) == []
    assert s.node(a)["attrs"]["mg_sel_agid"] == AGID, (
        "the stamp was cleared — this scene no longer exercises the exposure")
    assert s.node(a)["attrs"]["arc_exec_armed_mg_agid"] == AGID
    assert list(s.nodes("ExecOrder")) == [], (
        "the executor ran a goal that had left the pool")


def test_wh1_the_adapter_carry_is_a_CONSTANT_TABLE_not_a_choice():
    """The adapter must not be where "which collapse" is decided.  `arm` copies
    a module-level constant of (source, destination) names and never inspects a
    value; the branch lives in `ax_dispatch`'s `IfThenElse`."""
    assert dict(axe.ARM_CARRY) == {
        "arc_sel_agid": "arc_exec_armed_agid",
        "arc_sel_value": "arc_exec_armed_value",
        "mg_sel_agid": "arc_exec_armed_mg_agid",
        "mg_sel_value": "arc_exec_armed_mg_value",
    }
    where = _seed_rule("ax_dispatch")["where"]
    w = json.dumps(where)
    for stamp in ("mg_sel_agid", "mg_sel_value", "arc_exec_armed_mg_agid",
                  "arc_exec_armed_mg_value", "arc_sel_agid", "arc_sel_value"):
        assert stamp in w, stamp

    #  EVERY collapse-selecting branch must pair a stamp with ITS OWN TWIN and
    #  must be gated on the SAME absence test, or the guard could straddle two
    #  rankings — e.g. compare order-N's winner against order-1's value.
    pairs = {("arc_sel_agid", "mg_sel_agid"),
             ("arc_sel_value", "mg_sel_value"),
             ("arc_exec_armed_agid", "arc_exec_armed_mg_agid"),
             ("arc_exec_armed_value", "arc_exec_armed_mg_value")}
    seen = set()
    for ite in _walk(where, "IfThenElse"):
        if ite["then"].get("type") != "Attr":
            continue                              # the headroom_n coalesce
        pair = (ite["then"]["key"], ite["other"]["key"])
        assert pair in pairs, pair
        assert ite["cond"] == {
            "type": "Eq",
            "a": {"type": "Attr", "node": {"type": "Var", "name": "agenda"},
                  "key": "mg_sel_agid"},
            "b": {"type": "Lit", "value": None}}, ite["cond"]
        seen.add(pair)
    assert seen == pairs, sorted(pairs - seen)


# =========================================================================== #
#  A13/WH4(c) — THE IMPOTENCE TERM.
#  Bars: `PROGRAM_SYNTHESIS_ARC6_PREREG.md` amendment A13 (IM1–IM5), registered
#  BEFORE this block.  `_routable`/`ROUTE`/`POOL` are reused verbatim; the only
#  new rule is `ax_impotent`.
# =========================================================================== #
def _leave_pool_without_retiring(s, agid):
    """Remove one goal from `POOL()` WITHOUT touching `status` — headroom_n
    to 0 rather than `status: 'retired'`.  Deliberately NOT `sole_survivor`'s
    retire-everything-else shape: retiring AGID by hand leaves its
    `retired_epoch` unset, `ax_retired_epoch` stamps it, and because its
    underlying `GoalResidual` never actually got re-measured (still
    genuinely stale on THIS engine — the value-layer collapse is real, not a
    fixture), `ax_rearm`'s latch legitimately brings it back the moment the
    epoch advances.  That is the anti-oscillation latch working correctly,
    not a bug in this test — but it would confound an isolated mint/lapse
    demonstration, so the pool-exit here is via headroom (a path `ax_rearm`
    never looks at) and the goal is left `status: 'minted'`."""
    for n in s.nodes("ArcGoal"):
        if s.node(n)["attrs"].get("agid") == agid:
            s.set_attr(n, "headroom_n", 0.0)
            return
    raise AssertionError("no such goal: " + agid)


def test_im1_fires_when_the_WHOLE_POOL_is_unroutable():
    """IM1, positive case.  AGID (the one routable kind) leaves the pool; the
    remaining seven goals are `supply_blocker` / `source_claim` kinds with no
    `ExecClass` match at all, so the pool is collectively unroutable and the
    verdict mints, carrying the pool it saw."""
    s, _ = boot()
    s._inner.run_rules()
    assert axe.agenda_verdicts(s, "impotent") == [], (
        "fires before anything left the pool")
    _leave_pool_without_retiring(s, AGID)
    s._inner.run_rules()
    avs = axe.agenda_verdicts(s, "impotent")
    assert len(avs) == 1, avs
    av = avs[0]
    assert av["pool_n"] == 7
    seen_pool = json.loads(av["pool_agids"])
    assert AGID not in seen_pool
    assert sorted(seen_pool) == axe.pool(s)
    assert av["stale"] == 0.0
    #  A15 -- inverted, not removed (the WH1 precedent).  `exec_classes_held`
    #  is a RAW MapList over every ExecClass node's `name` attr, never
    #  deduplicated (`_r_impotent`, untouched by A15 — editing it would be a
    #  rule edit this rung's own registered threshold avoids).  With TWO
    #  ExecClass nodes sharing the semantic name "re_measure" (by design —
    #  the name is the KIND label, not a per-class identity; A15's own
    #  Second-ExecClass results doc §"what broke" names this explicitly),
    #  the list legitimately grows a duplicate entry.  A14 §3 already
    #  established this field "carries ZERO information about concentration
    #  vs spread" because it is a property of the SEED, not the pool — that
    #  finding is unaffected; only the raw count changed.
    assert json.loads(av["exec_classes_held"]) == ["re_measure", "re_measure"]


def test_im1_does_NOT_fire_while_the_pool_is_healthy():
    """IM1, negative case.  The shipped, untouched boot: a routable goal
    (AGID) is present.  No verdict."""
    s, _ = boot()
    s._inner.run_rules()
    assert AGID in axe.pool(s)
    assert axe.agenda_verdicts(s, "impotent") == []


def test_im1_an_EMPTY_pool_is_not_impotent_it_is_DONE():
    """`Not(Exists(pool, ...))` is vacuously True over an empty pool — the
    non-emptiness guard is what keeps a finished agenda from reading as a
    stuck one."""
    s, _ = boot()
    s._inner.run_rules()
    for n in s.nodes("ArcGoal"):
        s.set_attr(n, "status", "retired")
    s._inner.run_rules()
    assert axe.pool(s) == []
    assert axe.agenda_verdicts(s, "impotent") == []


def test_im1_the_REAL_live_run_scene_reaches_impotence_too(live_run):
    """Not a fixture-only claim: `live_run`'s own post-execution state (a REAL
    138s remeasurement retired the one routable goal for real, pool 8 -> 7) is
    independently an impotent pool — no scene construction, reusing the
    already-paid cost.

    `live_run` is a MODULE-scoped fixture shared with `test_ex4_*`
    (`latch_cells`), which walks the anti-oscillation latch through a real
    epoch bump on this SAME graph — correctly minting a second, later verdict
    while the first goes stale (IM5, live).  So this asserts on the CURRENTLY
    LIVE (non-stale) subset, which is exactly one regardless of how much of
    that history has already run when this test executes."""
    s = live_run["s"]
    avs = axe.agenda_verdicts(s, "impotent")
    assert avs, "the real remeasurement's post-execution pool never registered as impotent"
    live_avs = [a for a in avs if a["stale"] != 1.0]
    assert len(live_avs) == 1, avs
    assert AGID not in json.loads(live_avs[0]["pool_agids"])
    assert live_avs[0]["pool_n"] == len(axe.pool(s))


def test_im2_the_discriminator_a_winner_only_reading_would_be_WRONG_here():
    """IM2.  The shipped boot IS the discriminating scene A12/WH4 SS5.1 named:
    order-1's own winner is the 42-task blocker, unroutable — a winner-only
    reading (the CURRENT `_why_no_dispatch` measurement-script shape) would
    call this impotent.  The pool-quantified term must not, because AGID sits
    lower in the ranking and IS routable."""
    s, _ = boot()
    s._inner.run_rules()
    at = s.node([n for n in s.nodes("ArcAgenda")][0])["attrs"]
    winner = at["arc_sel_agid"]
    assert winner != AGID, (
        "the winner must be the UNROUTABLE blocker for this scene to "
        "discriminate anything")
    assert AGID in axe.pool(s), (
        "the routable goal must still be IN the pool, merely not winning")
    assert axe.agenda_verdicts(s, "impotent") == [], (
        "a winner-only implementation would have fired here; the "
        "pool-quantified one must not")


def test_im4_composes_with_the_order_N_wiring():
    """IM4.  With `arc_magnitude` loaded and the tier ladder installed, AGID is
    order-N's OWN pick (WH1) — retiring it makes BOTH `ax_dispatch` armed
    selections (order-1 AND order-N) name an unroutable goal, and the rest of
    the pool is unroutable too.  The fact must fire there specifically, and
    must not fire one step earlier while AGID was still in the pool."""
    s, _ = _boot_with_magnitude(ladder=True)
    s._inner.run_rules()
    at = s.node([n for n in s.nodes("ArcAgenda")][0])["attrs"]
    assert at["mg_sel_agid"] == AGID, (
        "order-N must still be picking the routable goal here — see WH1")
    assert axe.agenda_verdicts(s, "impotent") == [], (
        "must not fire while the routable goal is still in the pool")

    _leave_pool_without_retiring(s, AGID)
    s._inner.run_rules()
    at2 = s.node([n for n in s.nodes("ArcAgenda")][0])["attrs"]
    assert at2["arc_sel_agid"] == at2["mg_sel_agid"] != AGID, (
        "both collapses must now agree on an UNROUTABLE goal for this to be "
        "the composed case IM4 asks for")
    avs = axe.agenda_verdicts(s, "impotent")
    assert len(avs) == 1, avs
    assert AGID not in json.loads(avs[0]["pool_agids"])
    assert avs[0]["nearest_unroutable_agid"] == at2["mg_sel_agid"], (
        "descriptive field reads whichever collapse is live (SEL_AGID), "
        "order-N here")


def test_im5_mint_once_by_pool_signature_not_by_tick():
    """IM5, half 1.  Repeated `run_rules()` passes over an UNCHANGED impotent
    pool must not double-mint."""
    s, _ = boot()
    s._inner.run_rules()
    _leave_pool_without_retiring(s, AGID)
    s._inner.run_rules()
    first = axe.agenda_verdicts(s, "impotent")
    assert len(first) == 1
    s._inner.run_rules()
    s._inner.run_rules()
    second = axe.agenda_verdicts(s, "impotent")
    assert len(second) == 1, "an unchanged impotent pool must not double-mint"
    assert second[0]["_id"] == first[0]["_id"]


def test_im5_a_DIFFERENT_impotent_pool_mints_its_OWN_verdict():
    """IM5, half 2 (the other side of 'keyed on the pool signature, not the
    tick').  A second, genuinely different impotent pool — reached inside the
    SAME epoch, no measurement — mints its OWN verdict rather than being
    silently absorbed by the first."""
    s, _ = boot()
    s._inner.run_rules()
    _leave_pool_without_retiring(s, AGID)
    s._inner.run_rules()
    assert len(axe.agenda_verdicts(s, "impotent")) == 1
    for n in s.nodes("ArcGoal"):
        if s.node(n)["attrs"].get("agid") == "arc6.claim.tier0_hs1_0_of_10":
            s.set_attr(n, "headroom_n", 0.0)
    s._inner.run_rules()
    avs = axe.agenda_verdicts(s, "impotent")
    assert len(avs) == 2, avs
    assert {a["pool_n"] for a in avs} == {7, 6}
    assert all(a["stale"] == 0.0 for a in avs), (
        "both are true statements about DIFFERENT historical pool states — "
        "see the results doc's remaining-uncertainties section")


def test_im5_lapses_through_the_UNMODIFIED_gr_condition_lapse():
    """IM5, half 3.  No new lapse mechanism: bumping `arc_measure_epoch` (the
    SAME fact `gr_condition_lapse`'s `fact_equals` branch already reads for
    the testimony precedent) marks the held verdict stale, and because the
    pool is STILL impotent a fresh verdict mints for the new epoch."""
    s, _ = boot()
    s._inner.run_rules()
    _leave_pool_without_retiring(s, AGID)
    s._inner.run_rules()
    before = axe.agenda_verdicts(s, "impotent")
    assert before and before[0]["stale"] == 0.0
    before_epoch = before[0]["epoch"]

    agi.bump_measure_epoch(s)
    s._inner.run_rules()
    avs = axe.agenda_verdicts(s, "impotent")
    stale_now = [a for a in avs if a["epoch"] == before_epoch]
    assert stale_now and stale_now[0]["stale"] == 1.0, (
        "the held verdict must go stale on a genuinely new measurement epoch")
    live_now = [a for a in avs if a["stale"] != 1.0]
    assert len(live_now) == 1 and live_now[0]["epoch"] != before_epoch


def test_im5_goal_residuals_seed_is_UNMODIFIED_the_lapse_is_RIDDEN_not_rebuilt():
    """`gr_condition_lapse` / `gr_condition_hold` (`seeds/goal_residuals.json`)
    are untouched by this rung — the behavioural claim above rides the
    EXISTING rule because its `match` carries no type constraint on the node
    it lapses, not because a new lapse rule was added."""
    prefix = subprocess.run(["git", "-C", ROOT, "rev-parse", "--show-prefix"],
                            capture_output=True, text=True).stdout.strip()
    head = subprocess.run(["git", "-C", ROOT, "show",
                           "HEAD:" + prefix + "seeds/goal_residuals.json"],
                          capture_output=True, text=True).stdout
    assert head
    assert head == open(os.path.join(ROOT, "seeds",
                                     "goal_residuals.json")).read()


# =========================================================================== #
#  EVERY RULE MUST HAVE MOVED SOMETHING
# =========================================================================== #
def test_every_rule_in_this_seed_is_shown_to_FIRE_live(live_run, latch_cells):
    """An unknown op or field name is a SILENT NO-OP in this engine — a
    misspelled key on an `And` makes it an EMPTY conjunction that returns True.
    So a rule is only real once it is shown to have MOVED something."""
    s = live_run["s"]
    g = s.node(goal(s))["attrs"]
    orders = [dict(s.node(n)["attrs"]) for n in s.nodes("ExecOrder")]
    assert orders and orders[0]["runner"] == RUNNER          # ax_dispatch
    assert g.get("retired_epoch") is not None                # ax_retired_epoch
    assert g.get("rearm_count") == 1.0                       # ax_rearm
    assert orders[0]["status"] == "closed"                   # ax_close
    assert axe.agenda_verdicts(s, "impotent")                # ax_impotent
    #  A19 -- `live_run` boots WITHOUT arc_magnitude (`boot()`, no order-N
    #  collapse ever on this graph), so the fallback is live from tick 0.
    fb = axe.agenda_verdicts(s, "order_n_fallback")
    assert fb and any(a["active"] == 1.0 for a in fb)        # ax_fallback_silent
    #  ax_fallback_cleared is shown to fire in its own dedicated scene below
    #  (test_ar19b_the_fact_CLEARS...) -- it structurally cannot fire on
    #  this fixture, which never loads arc_magnitude.
    #  ax_impotent_pool_lapse/ax_impotent_pool_hold (A21) are shown to fire in
    #  their own dedicated scenes below (test_a21_AR21c_*) -- this fixture
    #  only ever retires ONE goal via a single real remeasurement, so the
    #  pool's composition never drifts a SECOND time within one epoch here.


def test_no_guard_is_an_EMPTY_conjunction():
    for r in _seed()["rules"]:
        w = r["where"]
        assert w and w.get("type") == "And" and len(w["items"]) >= 1, r["name"]
        assert r["effects"], r["name"]
        assert all(isinstance(e, list) and e[0] in
                   {"add_node", "add_edge", "set_attr", "add_node_if_absent",
                    "del_edge"} for e in r["effects"]), r["name"]


def test_the_null_hazards_are_COALESCED_not_assumed():
    """`Gt(8.0, null)` is TRUE and `Lt(null, 0.0)` is TRUE on this engine, so a
    missing attr sorts however the comparison happens to fall.  Asserted
    behaviourally AND asserted present in the shipped guard."""
    s, _ = boot()
    assert s._inner.evaluate({"type": "Gt", "a": {"type": "Lit", "value": 8.0},
                              "b": {"type": "Lit", "value": None}}) is True
    #  the pool predicate must not read headroom_n raw
    w = json.dumps(_seed_rule("ax_dispatch")["where"])
    assert '"IfThenElse"' in w and '"headroom_n"' in w, (
        "headroom_n is compared without a coalesce — an unmeasured goal would "
        "read as having headroom")


# =========================================================================== #
#  EX6 — NO REGRESSION, NO PYTHON DECISIONS
# =========================================================================== #
def test_ex6_the_adapter_CANNOT_contain_a_hidden_decision():
    """The standing source audit in its module-specific form: the adapter never
    imports `substrate_rs`, never calls `.evaluate(`, never calls `run_rules`,
    and its only substrate contact is the mechanical mutators.  With no
    evaluator and no rule engine reachable from it there is nowhere for a
    decision over graph state to hide."""
    src = _code_only(os.path.join(ROOT, "domains", "arc_executor.py"))
    for banned in ("import substrate_rs", ".evaluate(", "run_rules",
                   "graph_rewrite", "make_rule", "._match", "._apply"):
        assert banned not in src, banned
    import re
    calls = set(re.findall(r"(?:sub|s)\._inner\.(\w+)\(", src)) | \
        set(re.findall(r"(?:sub|s)\.(\w+)\(", src))
    allowed = {"add_node", "node", "nodes", "set_attr", "remove_node",
               "load_seed_manifest", "add_edge_unchecked"}
    assert calls <= allowed, sorted(calls - allowed)


def test_ex6_the_runner_makes_no_decision_either():
    """`scripts/arc6_remeasure_row_verdict.py` re-runs three existing scripts in
    a fixed order.  It never touches the substrate at all — asserted, so that a
    future edit that reaches into the graph from the runner is loud."""
    src = _code_only(os.path.join(ROOT, "scripts",
                                  "arc6_remeasure_row_verdict.py"))
    for banned in ("import substrate_rs", "substrate_rs", ".evaluate(",
                   "run_rules", "ArcGoal", "GoalResidual"):
        assert banned not in src, banned


def test_ex6_the_seed_is_NOT_globbed_into_every_agent_in_the_tree():
    """An executor that dispatches jobs is the LAST thing that should arrive in
    every agent in the tree by a glob.  `arc_goals` and `arc_magnitude` both
    ship `self_load_only` and this keeps the gating; removing the key is the
    tree-wide activation and needs the paired sweep A5 requires."""
    assert _seed()["self_load_only"] is True
    from substrate.boot_all import _read_seeds
    loaded = _read_seeds(os.path.join(ROOT, "seeds"))
    assert "arc_executor" not in loaded
    assert manifest_for("arc_executor")["id"] == "arc_executor"


def test_ex6_the_seeds_below_this_rung_are_UNTOUCHED():
    """Confinement asserted against `HEAD`, not promised.  `arc_goals` and
    `arc_magnitude` are byte-frozen and gated by their own suites; this rung
    ADDS rules, it does not edit theirs.

    A16/MG4 EXCEPTION, NAMED — the WH1 precedent (invert a pin with a
    docstring, never silently remove it).  `seeds/arc_magnitude.json` is no
    longer on this list: A16 (order-N decomposition) added ONE additive
    guard to `mg_goal_order_n_default` (excluding a node carrying
    `parent_agid`, absent on every goal this suite's own scenes mint) and
    bumped the seed to v1.1.0.  This executor rung's OWN gates never load
    `arc_decompose` and never mint a `parent_agid`-bearing goal, so the
    guard is INERT here by the same construction `test_arc_magnitude_
    migrated`'s own 43 gates already confirm it inert on — checked below by
    regenerating `arc_magnitude`'s OWN current emitter and diffing against
    it (still byte-frozen, just no longer frozen to a stale `HEAD`), rather
    than by widening this rung's own scope to review A16's build."""
    prefix = subprocess.run(["git", "-C", ROOT, "rev-parse", "--show-prefix"],
                            capture_output=True, text=True).stdout.strip()
    for rel in ("seeds/arc_goals.json", "seeds/goal_residuals.json",
                "seeds/program_synthesis.json", "domains/arc_goal_ingest.py",
                "domains/goal_residual_ingest.py"):
        head = subprocess.run(["git", "-C", ROOT, "show", "HEAD:" + prefix + rel],
                              capture_output=True, text=True).stdout
        assert head, rel
        assert head == open(os.path.join(ROOT, rel)).read(), rel

    r = subprocess.run([sys.executable, os.path.join(
        ROOT, "tools", "build_arc_magnitude_seed.py"), "--check"],
        capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr


def test_ex6_the_seed_REGENERATES_byte_identically():
    """Frozen artifacts are byte-frozen.  The Term idioms are IMPORTED from
    `tools/build_arc_goals_seed.py`, so if `MEASURE_EPOCH` or the pool
    predicate changes there this seed goes out of date LOUDLY."""
    r = subprocess.run([sys.executable,
                        os.path.join(ROOT, "tools", "build_arc_executor_seed.py"),
                        "--check"], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr


def test_ex6_the_epoch_producer_claim_is_TRUE_of_the_code_not_the_prose():
    """`arc_measure_epoch` had no producer through two rungs.  Assert that the
    executor's run path is one — by reading the code, not the write-up."""
    src = _code_only(os.path.join(ROOT, "domains", "arc_executor.py"))
    assert "bump_measure_epoch" in src
    #  ...and that it is inside `run_order`, i.e. a measurement produced it.
    import ast
    tree = ast.parse(open(os.path.join(ROOT, "domains",
                                       "arc_executor.py")).read())
    fn = [n for n in tree.body
          if isinstance(n, ast.FunctionDef) and n.name == "run_order"][0]
    assert "bump_measure_epoch" in ast.unparse(fn)


# =========================================================================== #
#  A18 — THE RE-ARM DEADLOCK, CLOSED WITHOUT RUNNING ANYTHING.
#  Bars: PROGRAM_SYNTHESIS_ARC6_PREREG.md amendment A18 (AR18a-AR18d),
#  registered BEFORE this build.  Results: PROGRAM_SYNTHESIS_ARC6_REARM_
#  DEADLOCK.md.
# =========================================================================== #
def test_a18_AR18a_the_deadlock_REPRODUCED_live_on_the_UNFIXED_graph():
    """AR18a.  `scripts/arc6_rearm_deadlock_measure.py` was run BEFORE this
    rung's rule/adapter change existed (registered process discipline: measure
    before building) and wrote `results/arc6_rearm_deadlock_before_fix.json`.
    This reads that artifact back: on the CURRENT (post-A17) shipped graph,
    with a REAL live execution retiring the row-verdict goal and the OTHER
    ExecClass confirmed not organically stale (zero executable pool members,
    matching PREREG A18 item 3's own finding), a genuine world change (the
    artifact removed) leaves the goal stuck retired, epoch unchanged, across
    SIX repeated probe/fixpoint cycles — not merely one."""
    doc = json.load(open(os.path.join(
        ROOT, "results", "arc6_rearm_deadlock_before_fix.json")))
    assert doc["DEADLOCK_REPRODUCES"] is True, doc
    assert doc["zero_executable_goals_at_retirement"] is True, doc
    stuck = [st for st in doc["steps"]
             if st["tag"].startswith(("2_", "3_", "4_"))]
    assert len(stuck) >= 6, "not enough repeated cycles to call this 'stuck'"
    assert all(st["goal_status"] == "retired" and not st["in_pool"]
               for st in stuck), stuck
    epochs = {st["epoch"] for st in stuck}
    assert epochs == {doc["steps"][1]["epoch"]}, (
        "the epoch must never move across repeated churn/probes alone", epochs)


@pytest.fixture(scope="module")
def world_probe_cells(latch_cells, live_run):
    """A18 — CONTINUES the SAME live graph `latch_cells` already walked to
    cell E (retired again, epoch advanced once already, condition holding),
    and shows the deadlock closing a SECOND time WITHOUT ever running an
    order: two SEPARATE, externally-triggered `refresh_evidence_facts`
    probes, `axe.world_probe_advance_epoch` (the mechanical read-and-act
    half), and nothing else — no subprocess, no `run_order`, no hand-poked
    `bump_measure_epoch`."""
    s = live_run["s"]
    g, r = goal(s), res(s)
    cells = {}

    def snap(k, advance=None):
        cells[k] = {"status": s.node(g)["attrs"].get("status"),
                    "stale": s.node(r)["attrs"].get("stale"),
                    "epoch": agi.measure_epoch(s),
                    "in_pool": AGID in axe.pool(s),
                    "rearm_count": s.node(g)["attrs"].get("rearm_count"),
                    "world_drift_confirmed": s.node(g)["attrs"].get(
                        "world_drift_confirmed"),
                    "advance_call_result": advance}

    snap("F_start_retired_again")

    art = os.path.join(ROOT, s.node(r)["attrs"]["evidence_artifact"])
    moved = art + ".a18_probe"
    shutil.move(art, moved)
    try:
        axe.refresh_evidence_facts(s)
        s._inner.run_rules()
        adv1 = axe.world_probe_advance_epoch(s)
        snap("G_refailed_FIRST_probe_only", adv1)

        axe.refresh_evidence_facts(s)
        s._inner.run_rules()
        adv2 = axe.world_probe_advance_epoch(s)
        snap("H_refailed_SECOND_separate_probe", adv2)

        s._inner.run_rules()
        snap("I_after_the_SECOND_producer_fired")
    finally:
        shutil.move(moved, art)
    axe.refresh_evidence_facts(s)
    s._inner.run_rules()
    snap("J_world_restored_again")
    return cells


def test_a18_AR18b_a_SINGLE_world_probe_does_NOT_confirm_drift_or_advance_the_epoch(
        world_probe_cells):
    """AR18b, half 1.  The discriminator against collapsing EX4's cell C into
    cell D: ONE probe finding a genuine re-failure must not, by itself, be
    enough for the second epoch producer to fire — exactly EX4's own
    direction (a single re-failure alone does not re-mint), now checked
    against the NEW mechanism specifically, not only against `ax_rearm`."""
    f = world_probe_cells["F_start_retired_again"]
    assert f["status"] == "retired" and f["stale"] == 0.0
    g = world_probe_cells["G_refailed_FIRST_probe_only"]
    assert g["stale"] == 1.0, "the condition did not actually re-fail"
    assert g["status"] == "retired"
    assert g["in_pool"] is False
    assert g["world_drift_confirmed"] != 1.0, (
        "a SINGLE probe must not confirm drift")
    assert g["advance_call_result"] is None, (
        "the second epoch producer must be a no-op after only one probe")
    assert g["epoch"] == f["epoch"], "the epoch must not move on one probe"


def test_a18_AR18c_TWO_separate_probes_confirm_drift_and_the_SECOND_producer_fires(
        world_probe_cells):
    """AR18c, and this is the primary bar.  A SECOND, separate probe — still
    no subprocess, no `run_order` — confirms the drift and the mechanical
    adapter call bumps the epoch; the NEXT fixpoint re-arms the goal exactly
    as EX4's cell D did, but nothing here ever ran a measurement."""
    h = world_probe_cells["H_refailed_SECOND_separate_probe"]
    assert h["stale"] == 1.0
    assert h["world_drift_confirmed"] == 1.0, (
        "TWO separate probes of a genuine, persisting re-failure must confirm it")
    adv = h["advance_call_result"]
    assert adv is not None, "the second epoch producer must fire here"
    assert int(adv["epoch_after"]) == int(adv["epoch_before"]) + 1
    assert AGID in adv["triggered_by"]

    i = world_probe_cells["I_after_the_SECOND_producer_fired"]
    assert i["status"] not in ("retired", "settled"), i
    assert i["status"] in ("minted", "pursued"), i
    assert i["in_pool"] is True
    assert i["rearm_count"] == 2.0, (
        "the SECOND rearm event on this goal — latch_cells' cell D was the "
        "first, via the manual epoch bump; this one via the world-probe "
        "producer, with no order ever run")


def test_a18_AR18c_NO_order_was_EVER_run_to_close_this_deadlock(
        world_probe_cells, live_run):
    """The headline claim, asserted structurally, on the RIGHT property.

    A re-armed goal is AGAIN the collapse's winner, and `ax_dispatch`'s own
    two-tick agreement can legitimately be satisfied by a STALE `armed_*`
    stamp from `live_run`'s ORIGINAL `axe.arm` call (this fixture never calls
    `axe.arm` again) — EXECUTOR.md's own EX4 §5 already documented exactly
    this for cell D ("status may read `pursued` rather than `minted`...
    that is the loop working, not a defect").  So a SECOND `ExecOrder` node
    CAN legitimately be MINTED (bookkeeping) without anything running it —
    and, once minted, `ax_dispatch`'s own "at most one OUTSTANDING order
    globally" guard (status=='ordered') blocks a THIRD, so this world-probe
    rearm mints no order of its own.  The property this rung's own AR18c
    claim actually rests on is narrower and correct: no order EVER reached
    `ran`/`closed` a second time — no subprocess, no measurement, anywhere
    in this fixture, only in `live_run`'s own single call."""
    s = live_run["s"]  # the SAME graph object world_probe_cells mutated
    orders = [dict(s.node(n)["attrs"]) for n in s.nodes("ExecOrder")]
    ran_or_closed = [o for o in orders if o.get("status") in ("ran", "closed")]
    assert len(ran_or_closed) == 1, (
        "closing the deadlock a second time must not have RUN anything", orders)
    assert ran_or_closed[0]["agid"] == AGID
    assert ran_or_closed[0]["status"] == "closed"
    #  Any OTHER order that exists is bookkeeping only — minted, never run —
    #  the SAME pre-existing "loop working" property EX4's own cell D
    #  already exercises, not something this rung introduces or must guard.
    for o in orders:
        if o is not ran_or_closed[0]:
            assert o["status"] == "ordered", o


def test_a18_AR18c_the_round_trip_CLOSES_again(world_probe_cells):
    """`terminal -> stuck (1 probe) -> confirmed (2 probes) -> BACK IN THE
    POOL -> terminal again` — the SAME round-trip shape EX4's cell E closed,
    now driven entirely by world probes."""
    j = world_probe_cells["J_world_restored_again"]
    assert j["stale"] == 0.0
    assert j["status"] == "retired", (
        "with its condition holding again the goal must be terminal again")
    assert j["rearm_count"] == 2.0, "it must not re-arm a third time on its own"


def test_a18_AR18d_the_source_audit_still_passes_on_the_EDITED_adapter():
    """The module-specific source audit, re-run against the file this rung
    edited — the same allow-list `test_ex6_the_adapter_CANNOT_contain_a_
    hidden_decision` checks, confirming the new functions
    (`world_drift_confirmed_goals`, `world_probe_advance_epoch`, and the
    `refresh_evidence_facts` snapshot) introduce no new substrate call
    outside the mechanical allow-list."""
    src = _code_only(os.path.join(ROOT, "domains", "arc_executor.py"))
    for banned in ("import substrate_rs", ".evaluate(", "run_rules",
                   "graph_rewrite", "make_rule", "._match", "._apply"):
        assert banned not in src, banned
    import re
    calls = set(re.findall(r"(?:sub|s)\._inner\.(\w+)\(", src)) | \
        set(re.findall(r"(?:sub|s)\.(\w+)\(", src))
    allowed = {"add_node", "node", "nodes", "set_attr", "remove_node",
               "load_seed_manifest", "add_edge_unchecked"}
    assert calls <= allowed, sorted(calls - allowed)


def test_a18_AR18d_the_new_rule_is_the_ONLY_addition_to_the_seed():
    """A18's OWN cost bar, about THAT rung, not a standing invariant — the
    WH1 precedent (invert a pin with a docstring, never silently remove it),
    applied a second time: A19 adds two MORE rules afterwards, so the exact
    post-A18 list is no longer the seed's total.  A18's own claim (`ax_
    world_probe_epoch` is additive, every prior rule present unedited by
    name) is still true and still checked, as a PREFIX of the current list;
    `test_a19_AR19d_the_new_rules_are_the_ONLY_addition_to_the_seed` now
    asserts the total."""
    doc = _seed()
    names = [r["name"] for r in doc["rules"]]
    assert names[:6] == ["ax_dispatch", "ax_retired_epoch", "ax_rearm",
                         "ax_close", "ax_impotent", "ax_world_probe_epoch"]


def test_a18_AR18d_ax_rearms_OWN_body_is_UNCHANGED():
    """A18 does not touch `ax_rearm` — read its match/where/effects back off
    the regenerated seed and confirm they are IDENTICAL to the byte-for-byte
    text EXECUTOR.md SS5 quotes: two conjuncts on the residual (stale==1),
    three on the goal's own retired_epoch, nothing about a second probe."""
    r = _seed_rule("ax_rearm")
    where = json.dumps(r["where"], sort_keys=True)
    assert '"stale_at_last_probe"' not in where
    assert '"world_drift_confirmed"' not in where
    assert r["match"] == [["agenda", "uses_policy", "pol"],
                          ["agenda", "has_arc_goal", "g"],
                          ["r", "remeasure_goal", "g"]]


# =========================================================================== #
#  A19 — THE SILENT ORDER-N FALLBACK, MADE OBSERVABLE.
#  Bars: `PROGRAM_SYNTHESIS_ARC6_PREREG.md` amendment A19 (AR19a–AR19d),
#  registered BEFORE this block.  `_order_n_is_not_live()` is reused verbatim
#  by the new rules — the same Term `SEL_AGID` itself branches on.
# =========================================================================== #
def test_a19_AR19a_the_fallback_is_a_STANDING_FACT_the_instant_order_N_is_absent():
    """AR19a, positive case.  A boot with NO `arc_magnitude` on the graph at
    all — the real shape WIRE_HANDS SS8.1 names ('a boot without arc_
    magnitude') — is exactly the scene where `mg_select` never fires.  Before
    the first `run_rules()` the fact does not exist (nothing has run yet);
    after it, `AgendaVerdict{kind:'order_n_fallback', active:1.0}` is present
    and readable through the existing, unmodified `agenda_verdicts`."""
    s, _ = boot()                       # no arc_magnitude
    assert axe.agenda_verdicts(s, "order_n_fallback") == [], (
        "fires before anything has run")
    s._inner.run_rules()
    at = s.node([n for n in s.nodes("ArcAgenda")][0])["attrs"]
    assert at.get("mg_sel_agid") is None, (
        "order-N must be genuinely absent for this to be AR19a's scene")
    fb = axe.agenda_verdicts(s, "order_n_fallback")
    assert len(fb) == 1, fb
    assert fb[0]["active"] == 1.0
    assert fb[0]["reason"] == (
        "mg_sel_agid_absent_order_n_collapse_not_producing_a_stamp")
    assert fb[0]["epoch"] == "0"


def test_a19_AR19a_mint_once_repeated_passes_do_not_double_mint():
    """The `ax_impotent`-precedent mint-once guard, checked the same way
    `test_im5_mint_once_by_pool_signature_not_by_tick` checks it: repeated
    `run_rules()` over an UNCHANGED absent-order-N graph must not spawn a
    second active verdict."""
    s, _ = boot()
    s._inner.run_rules()
    first = axe.agenda_verdicts(s, "order_n_fallback")
    assert len(first) == 1
    s._inner.run_rules()
    s._inner.run_rules()
    second = axe.agenda_verdicts(s, "order_n_fallback")
    assert len(second) == 1, "an unchanged absent-order-N graph must not double-mint"
    assert second[0]["_id"] == first[0]["_id"]


def test_a19_AR19b_CONTROL_the_fact_never_mints_when_order_N_is_live_from_the_start():
    """AR19b, negative control (i).  The WH1 scene: `arc_magnitude` loaded and
    the tier ladder installed FROM THE FIRST `run_rules()` call — order-N is
    live throughout the whole scene, so the fallback verdict must never
    mint, not even transiently."""
    s, _ = _boot_with_magnitude(ladder=True)
    s._inner.run_rules()
    at = s.node([n for n in s.nodes("ArcAgenda")][0])["attrs"]
    assert at.get("mg_sel_agid") is not None, (
        "order-N must be live for this to be the control")
    assert axe.agenda_verdicts(s, "order_n_fallback") == [], (
        "the fallback verdict minted while order-N was live from the start")

    #  A19c, folded in here rather than duplicated: the new rules add NOTHING
    #  to ax_dispatch's own outcome on this exact scene — same assertions
    #  WIRE_HANDS' own WH1 recorded.
    axe.arm(s)
    s._inner.run_rules()
    orders = [dict(s.node(n)["attrs"]) for n in s.nodes("ExecOrder")]
    assert [o["agid"] for o in orders] == [AGID], [o["agid"] for o in orders]
    assert orders[0]["selected_by"] == "order_n_mg_select"
    assert axe.agenda_verdicts(s, "order_n_fallback") == [], (
        "still nothing minted after dispatch — the two rule pairs are inert "
        "on this scene, exactly as they must be")


def test_a19_AR19b_CONTROL_without_the_tier_ladder_STILL_no_fallback():
    """The WH1-CONTROL-C precedent, re-run for THIS rung's own claim: `arc_
    magnitude` loaded but the ladder withheld still makes the two collapses
    AGREE (`mg_select` fires — it just agrees with order-1), so `mg_sel_agid`
    is NOT absent and the fallback fact must not mint here either.  This is
    the discriminator against a wrong implementation that mistook 'the two
    collapses agree' for 'order-N is not live'."""
    s, _ = _boot_with_magnitude(ladder=False)
    s._inner.run_rules()
    at = s.node([n for n in s.nodes("ArcAgenda")][0])["attrs"]
    assert at["arc_sel_agid"] == at["mg_sel_agid"] is not None, (
        "mg_select must have fired and merely agreed, not be absent")
    assert axe.agenda_verdicts(s, "order_n_fallback") == []


def test_a19_AR19b_the_fact_CLEARS_when_order_N_becomes_live_mid_graph_no_epoch_bump():
    """AR19b, transition (ii) — the strongest demonstration, and the reason
    the mechanism is a direct reversible pair rather than an epoch-lapse:
    start from AR19a's exact scene (fact active), load `arc_magnitude` onto
    the SAME live graph (`test_wh3_*` vs `test_wh1_*`'s own difference — no
    epoch bump anywhere in that transition), and show the held verdict's
    `active` flips to 0.0 on the very next `run_rules()` pass."""
    from domains import arc_magnitude_ingest as ami
    s, ag = boot()                      # no arc_magnitude yet
    s._inner.run_rules()
    before = axe.agenda_verdicts(s, "order_n_fallback")
    assert len(before) == 1 and before[0]["active"] == 1.0
    epoch_before = agi.measure_epoch(s)

    #  Order-N becomes live ON THE SAME GRAPH — no re-boot, no epoch bump.
    s._inner.load_seed_manifest(manifest_for("arc_magnitude"), ag)
    ami.resolve_attrition_keys(s)
    ami.install_tier_ladder(s, ami.probe_tier_ladder())
    s._inner.run_rules()

    at = s.node([n for n in s.nodes("ArcAgenda")][0])["attrs"]
    assert at.get("mg_sel_agid") is not None, (
        "order-N must have actually gone live for this to be the transition")
    assert agi.measure_epoch(s) == epoch_before, (
        "the clearing must NOT depend on an epoch bump — none happened here")

    after = axe.agenda_verdicts(s, "order_n_fallback")
    assert len(after) == 1, after
    assert after[0]["_id"] == before[0]["_id"], (
        "the SAME node must be cleared, not a fresh one minted")
    assert after[0]["active"] == 0.0, "the fact must CLEAR once order-N is live"
    assert after[0].get("cleared_epoch") == str(epoch_before)


def test_a19_AR19c_order_1_dispatch_still_works_ALONGSIDE_the_new_standing_fact():
    """AR19c, on the order-1 (fallback-live) side.  `test_wh3_the_fallback_
    when_the_order_N_collapse_is_NOT_on_the_graph`'s own scene, unmodified,
    reproduces byte-identically WITH the two new rules installed and the
    fact minted alongside it — the fallback still fires exactly as before,
    only now with a standing fact sitting next to it."""
    s, _ = boot()                       # no arc_magnitude
    s._inner.run_rules()
    assert axe.agenda_verdicts(s, "order_n_fallback"), (
        "the fact must be present here")
    axe.arm(s)
    s._inner.run_rules()
    assert list(s.nodes("ExecOrder")) == [], (
        "dispatch behaviour changed — the unroutable order-1 winner must "
        "still mint nothing")

    answer_open_questions(s, conditioned=True)
    s._inner.run_rules()
    assert agi.selection(s).get("arc_sel_agid") == AGID
    axe.arm(s)
    s._inner.run_rules()
    orders = [dict(s.node(n)["attrs"]) for n in s.nodes("ExecOrder")]
    assert [o["agid"] for o in orders] == [AGID]
    assert orders[0]["selected_by"] == "order_1_ag_select", (
        "dispatch must still follow order-1 exactly as WIRE_HANDS recorded")


def test_a19_AR19c_the_guard_TERM_is_IDENTICAL_to_SEL_AGIDs_own_absence_test():
    """Structural proof, not merely behavioural: the new rules cannot drift
    from `ax_dispatch`'s own notion of 'order-N is not live', because they
    read the IDENTICAL Eq(mg_sel_agid, null) subterm — same shape as `test_
    wh1_the_adapter_carry_is_a_CONSTANT_TABLE_not_a_choice`'s own structural
    check on `ax_dispatch`."""
    absence_test = {
        "type": "Eq",
        "a": {"type": "Attr", "node": {"type": "Var", "name": "agenda"},
              "key": "mg_sel_agid"},
        "b": {"type": "Lit", "value": None}}
    dispatch_where = _seed_rule("ax_dispatch")["where"]
    seen_in_dispatch = list(_walk(dispatch_where, "Eq"))
    assert absence_test in seen_in_dispatch, (
        "the reference term itself must appear in ax_dispatch's own where")

    silent = _seed_rule("ax_fallback_silent")["where"]
    assert silent["items"][0] == absence_test

    cleared = _seed_rule("ax_fallback_cleared")["where"]
    assert cleared["items"][0] == {"type": "Not", "arg": absence_test}


def test_a19_AR19d_the_new_rules_are_the_ONLY_addition_to_the_seed():
    """A20 INVERTS THIS PIN TO A PREFIX CHECK, NOT REMOVES IT — the WH1/A18
    precedent ('the old pin had to be deleted to land the change, which is
    the pin working, not a regression') applied a third time.  A20 appends a
    NINTH and TENTH rule (`ax_ask_divergence_active`/`_cleared`), so the
    exact-eight-name assertion this test made through A19 is now false BY
    CONSTRUCTION.  `test_a20_AR20d_the_new_rules_are_the_ONLY_addition_to_
    the_seed` below asserts the full, current ten-name list and version; this
    one still proves the ORIGINAL eight are an unbroken PREFIX, in order,
    unedited by name."""
    doc = _seed()
    names = [r["name"] for r in doc["rules"]]
    assert names[:8] == ["ax_dispatch", "ax_retired_epoch", "ax_rearm", "ax_close",
                         "ax_impotent", "ax_world_probe_epoch",
                         "ax_fallback_silent", "ax_fallback_cleared"], names[:8]


def test_a19_AR19d_ax_dispatch_and_every_prior_rule_body_is_UNCHANGED():
    """The five rule bodies A19 must not touch, read back off the regenerated
    seed and diffed against `HEAD`'s own emitted copy — the same 'no new Rust,
    no new adapter decision' confinement standard every prior rung in this
    arc has been held to, at the rule-body grain.

    A21 NARROWS `ax_impotent` OUT OF THIS SET, NOT SILENTLY — it is the one
    rule A21 is registered to touch (additively: one new `pool_stale:0.0`
    stamp in its effects, `where`/`match`/mint-once guard byte-unchanged).
    `test_a21_AR21d_ax_impotents_where_and_match_and_mint_once_guard_are_
    UNCHANGED` covers it at the FIRING-behaviour grain, which is the
    property this test's own name is actually about."""
    prefix = subprocess.run(["git", "-C", ROOT, "rev-parse", "--show-prefix"],
                            capture_output=True, text=True).stdout.strip()
    head_doc = json.loads(subprocess.run(
        ["git", "-C", ROOT, "show", "HEAD:" + prefix + "seeds/arc_executor.json"],
        capture_output=True, text=True).stdout)
    head_rules = {r["name"]: r for r in head_doc["rules"]}
    cur_rules = {r["name"]: r for r in _seed()["rules"]}
    for name in ("ax_dispatch", "ax_retired_epoch", "ax_rearm", "ax_close",
                 "ax_world_probe_epoch"):
        assert cur_rules[name] == head_rules[name], name


def test_a19_AR19d_the_adapter_is_BYTE_IDENTICAL_to_HEAD():
    """A19's design investigation (item 5) predicted `domains/arc_executor.py`
    needs no edit at all: `agenda_verdicts(sub, kind=None)` is already
    generic over `kind`, so the whole mechanism lives in the seed.  Checked
    here rather than merely claimed — a STRONGER bar than the module-specific
    source audit, which only proves no NEW banned call was added."""
    prefix = subprocess.run(["git", "-C", ROOT, "rev-parse", "--show-prefix"],
                            capture_output=True, text=True).stdout.strip()
    head = subprocess.run(["git", "-C", ROOT, "show",
                           "HEAD:" + prefix + "domains/arc_executor.py"],
                          capture_output=True, text=True).stdout
    assert head
    assert head == open(os.path.join(ROOT, "domains", "arc_executor.py")).read()


def test_a19_AR19d_the_seeds_below_this_rung_are_still_UNTOUCHED():
    """Same confinement `test_ex6_the_seeds_below_this_rung_are_UNTOUCHED`
    checks, re-run for A19: this rung edits only `seeds/arc_executor.json`
    and its own emitter."""
    prefix = subprocess.run(["git", "-C", ROOT, "rev-parse", "--show-prefix"],
                            capture_output=True, text=True).stdout.strip()
    for rel in ("seeds/arc_goals.json", "seeds/goal_residuals.json",
                "seeds/program_synthesis.json", "domains/arc_goal_ingest.py",
                "domains/goal_residual_ingest.py", "domains/arc_magnitude_ingest.py"):
        head = subprocess.run(["git", "-C", ROOT, "show", "HEAD:" + prefix + rel],
                              capture_output=True, text=True).stdout
        assert head, rel
        assert head == open(os.path.join(ROOT, rel)).read(), rel

    r = subprocess.run([sys.executable, os.path.join(
        ROOT, "tools", "build_arc_magnitude_seed.py"), "--check"],
        capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr


# =========================================================================== #
#  A20 — `ag_ask` VS `ax_dispatch`, READING DIFFERENT COLLAPSES, MADE
#  OBSERVABLE.  `PROGRAM_SYNTHESIS_ARC6_PREREG.md` amendment A20 (AR20a—d),
#  registered before this build.  The A19 pattern (a standing, queryable
#  AgendaVerdict, mint-once ON / reversible-pair OFF) applied to a DIFFERENT
#  comparison: not "is order-N live," but "given that it is, does it name
#  the SAME goal `ag_ask` asked about."  `ag_ask`/`seeds/arc_goals.json` are
#  UNTOUCHED throughout — see `test_a20_AR20d_the_seeds_below_this_rung_
#  including_arc_goals_are_still_UNTOUCHED`.
# =========================================================================== #
SB_MSP = "arc.supply.arc6.seam_a.import_oracle.missing_structural_primitive"


def test_a20_AR20a_the_divergence_fact_mints_on_the_shipped_boot():
    """AR20a.  The WH1 shipped-boot scene: order-N live, tier ladder
    installed — `ag_ask`'s winner (`arc_sel_agid`, the 42-task blocker) and
    `ax_dispatch`'s target (`SEL_AGID()`, the re-measurement goal) genuinely
    disagree, exactly as WIRE_HANDS SS2.1 measured.  The standing fact must
    mint, naming both stamps plus the descriptive runner-up check."""
    s, _ = _boot_with_magnitude(ladder=True)
    s._inner.run_rules()
    at = s.node([n for n in s.nodes("ArcAgenda")][0])["attrs"]
    assert at["arc_sel_agid"] == SB_MSP
    assert at["mg_sel_agid"] == AGID
    assert at["arc_sel_agid"] != at["mg_sel_agid"], "must genuinely disagree"

    div = axe.agenda_verdicts(s, "ask_dispatch_divergence")
    assert len(div) == 1, div
    assert div[0]["active"] == 1.0
    assert div[0]["asked_about_agid"] == SB_MSP
    assert div[0]["dispatch_target_agid"] == AGID
    assert div[0]["asked_about_runner_up_agid"] == AGID, (
        "on the shipped boot the dispatch target IS ag_ask's OTHER "
        "candidate — the structural-bound finding, descriptive here")
    assert div[0]["dispatch_matches_runner_up"] == 1.0
    assert div[0]["reason"] == (
        "ax_dispatch_is_acting_on_a_goal_ag_ask_did_not_name_as_its_winner")


def test_a20_AR20a_CONTROL_no_fact_when_order_N_is_absent():
    """Order-1 only (no `arc_magnitude`): `SEL_AGID()` falls back to
    `arc_sel_agid` by construction (A11's own ITE), so the two stamps this
    fact compares are IDENTICAL by definition and it must never mint —
    exactly as A19's own fallback fact does not mint here, for the same
    structural reason, checked independently for THIS fact."""
    s, _ = boot()                       # no arc_magnitude
    s._inner.run_rules()
    at = s.node([n for n in s.nodes("ArcAgenda")][0])["attrs"]
    assert at.get("mg_sel_agid") is None
    assert axe.agenda_verdicts(s, "ask_dispatch_divergence") == []


def test_a20_AR20a_CONTROL_without_the_tier_ladder_the_two_collapses_AGREE():
    """WH1-CONTROL-C, re-run for this rung's own claim: order-N live but the
    ladder withheld makes the two collapses AGREE on the same winner — the
    fact must not mint, discriminating against a wrong implementation that
    mistook 'order-N is live' for 'order-N disagrees with order-1'."""
    s, _ = _boot_with_magnitude(ladder=False)
    s._inner.run_rules()
    at = s.node([n for n in s.nodes("ArcAgenda")][0])["attrs"]
    assert at["arc_sel_agid"] == at["mg_sel_agid"] is not None
    assert axe.agenda_verdicts(s, "ask_dispatch_divergence") == []


def test_a20_AR20a_mint_once_repeated_passes_do_not_double_mint():
    s, _ = _boot_with_magnitude(ladder=True)
    s._inner.run_rules()
    first = axe.agenda_verdicts(s, "ask_dispatch_divergence")
    assert len(first) == 1
    s._inner.run_rules()
    s._inner.run_rules()
    second = axe.agenda_verdicts(s, "ask_dispatch_divergence")
    assert len(second) == 1, "an unchanged divergent graph must not double-mint"
    assert second[0]["_id"] == first[0]["_id"]


def test_a20_AR20a_the_fact_CLEARS_when_the_collapses_AGREE_no_epoch_bump():
    """The transition, mirroring A19's own AR19b(ii): start from the
    divergent scene (fact active), remove the ONE goal responsible for the
    divergence (`SB_MSP`, via the validated `headroom_n -> 0` pool-exit —
    A13 SS7.1, NEVER `status -> 'retired'`) so the two collapses converge on
    the SAME winner, and show the SAME node flips `active` to 0.0 with no
    epoch bump anywhere in the scene."""
    s, _ = _boot_with_magnitude(ladder=True)
    s._inner.run_rules()
    before = axe.agenda_verdicts(s, "ask_dispatch_divergence")
    assert len(before) == 1 and before[0]["active"] == 1.0
    epoch_before = agi.measure_epoch(s)

    for n in s.nodes("ArcGoal"):
        if s.node(n)["attrs"].get("agid") == SB_MSP:
            s.set_attr(n, "headroom_n", 0.0)
    s._inner.run_rules()

    at = s.node([n for n in s.nodes("ArcAgenda")][0])["attrs"]
    assert at["arc_sel_agid"] == at["mg_sel_agid"] == AGID, (
        "removing the one laddered goal must make the collapses converge")
    assert agi.measure_epoch(s) == epoch_before, (
        "the clearing must NOT depend on an epoch bump — none happened here")

    after = axe.agenda_verdicts(s, "ask_dispatch_divergence")
    assert len(after) == 1, after
    assert after[0]["_id"] == before[0]["_id"], "the SAME node, not a fresh mint"
    assert after[0]["active"] == 0.0
    assert after[0].get("cleared_epoch") == str(epoch_before)


def test_a20_AR20c_dispatch_behaviour_is_UNCHANGED_WH1_scene():
    """AR20c / the GO criterion's own condition (ii): re-run WH1's exact
    live scene with the two new rules installed and show the SAME order
    mints, byte-identical `selected_by`/`agid` — the new rules only ever
    add/edit `AgendaVerdict` nodes, never anything `ax_dispatch` reads."""
    s, _ = _boot_with_magnitude(ladder=True)
    s._inner.run_rules()
    axe.arm(s)
    s._inner.run_rules()
    orders = [dict(s.node(n)["attrs"]) for n in s.nodes("ExecOrder")]
    assert [o["agid"] for o in orders] == [AGID], [o["agid"] for o in orders]
    assert orders[0]["selected_by"] == "order_n_mg_select"
    #  the divergence fact persists alongside dispatch, undisturbed
    assert axe.agenda_verdicts(s, "ask_dispatch_divergence")[0]["active"] == 1.0


def test_a20_AR20c_dispatch_behaviour_is_UNCHANGED_WH3_scene():
    """The mirror case: order-1 fallback, unroutable winner, no order — the
    new rules must not perturb this either.  `test_wh3_the_fallback_when_
    the_order_N_collapse_is_NOT_on_the_graph`'s own scene, unmodified."""
    s, _ = boot()                       # no arc_magnitude
    s._inner.run_rules()
    axe.arm(s)
    s._inner.run_rules()
    assert list(s.nodes("ExecOrder")) == []
    answer_open_questions(s, conditioned=True)
    s._inner.run_rules()
    assert agi.selection(s).get("arc_sel_agid") == AGID
    axe.arm(s)
    s._inner.run_rules()
    orders = [dict(s.node(n)["attrs"]) for n in s.nodes("ExecOrder")]
    assert [o["agid"] for o in orders] == [AGID]
    assert orders[0]["selected_by"] == "order_1_ag_select"
    #  order-N was never on this graph, so the divergence fact never applies
    assert axe.agenda_verdicts(s, "ask_dispatch_divergence") == []


def test_a20_AR20c_the_guard_TERM_reuses_arc_sel_agid_and_SEL_AGID_VERBATIM():
    """Structural proof: the new rules cannot drift from `ax_dispatch`'s own
    notion of 'what the dispatch target is', because `SEL_AGID()` is the
    IDENTICAL Term (same ITE tree) `ax_dispatch`'s `where` embeds four times
    over (`SEL_AGID`/`SEL_VALUE`/`ARMED_AGID`/`ARMED_VALUE` all branch on the
    SAME `_order_n_is_not_live()`).  Extracted here by walking for the exact
    `Attr(agenda, 'arc_sel_agid')` subterm and confirming it appears, un-
    re-derived, inside both new rules' own `where`."""
    arc_sel_agid_attr = {
        "type": "Attr", "node": {"type": "Var", "name": "agenda"},
        "key": "arc_sel_agid"}
    dispatch_where = _seed_rule("ax_dispatch")["where"]
    assert arc_sel_agid_attr in list(_walk(dispatch_where, "Attr")), (
        "the reference term itself must appear in ax_dispatch's own where "
        "(via SEL_AGID's ITE)")

    active_where = _seed_rule("ax_ask_divergence_active")["where"]
    assert arc_sel_agid_attr in list(_walk(active_where, "Attr"))

    cleared_where = _seed_rule("ax_ask_divergence_cleared")["where"]
    assert arc_sel_agid_attr in list(_walk(cleared_where, "Attr"))


def test_a20_AR20d_the_new_rules_are_the_ONLY_addition_to_the_seed():
    """A21 INVERTS THIS PIN TO A PREFIX CHECK, NOT REMOVES IT — the WH1/A18/
    A19 precedent applied a fourth time.  A21 appends an ELEVENTH and
    TWELFTH rule (`ax_impotent_pool_lapse`/`_hold`), so the exact-ten-name
    assertion this test made through A20 is now false BY CONSTRUCTION.
    `test_a21_AR21d_the_new_rules_are_the_ONLY_addition_to_the_seed` below
    asserts the full, current twelve-name list and version; this one still
    proves the ORIGINAL ten are an unbroken PREFIX, in order, unedited by
    name."""
    doc = _seed()
    names = [r["name"] for r in doc["rules"]]
    assert names[:10] == [
        "ax_dispatch", "ax_retired_epoch", "ax_rearm", "ax_close",
        "ax_impotent", "ax_world_probe_epoch",
        "ax_fallback_silent", "ax_fallback_cleared",
        "ax_ask_divergence_active", "ax_ask_divergence_cleared"], names[:10]


def test_a20_AR20d_every_prior_rule_body_is_UNCHANGED():
    """The eight rule bodies A20 must not touch, read back off the
    regenerated seed and diffed against `HEAD`'s own emitted copy.

    A21 NARROWS `ax_impotent` OUT OF THIS SET — see the dated note on
    `test_a19_AR19d_ax_dispatch_and_every_prior_rule_body_is_UNCHANGED`
    above; the same reasoning applies here unchanged."""
    prefix = subprocess.run(["git", "-C", ROOT, "rev-parse", "--show-prefix"],
                            capture_output=True, text=True).stdout.strip()
    head_doc = json.loads(subprocess.run(
        ["git", "-C", ROOT, "show", "HEAD:" + prefix + "seeds/arc_executor.json"],
        capture_output=True, text=True).stdout)
    head_rules = {r["name"]: r for r in head_doc["rules"]}
    cur_rules = {r["name"]: r for r in _seed()["rules"]}
    for name in ("ax_dispatch", "ax_retired_epoch", "ax_rearm", "ax_close",
                 "ax_world_probe_epoch",
                 "ax_fallback_silent", "ax_fallback_cleared"):
        assert cur_rules[name] == head_rules[name], name


def test_a20_AR20d_the_adapter_is_BYTE_IDENTICAL_to_HEAD():
    """No adapter edit was needed: `agenda_verdicts(sub, kind=...)` was
    already generic (A19's own finding, reused here verbatim)."""
    prefix = subprocess.run(["git", "-C", ROOT, "rev-parse", "--show-prefix"],
                            capture_output=True, text=True).stdout.strip()
    head = subprocess.run(["git", "-C", ROOT, "show",
                           "HEAD:" + prefix + "domains/arc_executor.py"],
                          capture_output=True, text=True).stdout
    assert head
    assert head == open(os.path.join(ROOT, "domains", "arc_executor.py")).read()


def test_a20_AR20d_the_seeds_below_this_rung_including_arc_goals_are_still_UNTOUCHED():
    """THE HIGH-BAR CONFINEMENT CHECK THIS RUNG REGISTERED (A20's own AR20d):
    `seeds/arc_goals.json` — i.e. `ag_ask` itself — stays byte-identical to
    `HEAD`, same as every prior rung in this arc has held it, plus the usual
    sibling seeds/adapters this rung does not touch."""
    prefix = subprocess.run(["git", "-C", ROOT, "rev-parse", "--show-prefix"],
                            capture_output=True, text=True).stdout.strip()
    for rel in ("seeds/arc_goals.json", "seeds/goal_residuals.json",
                "seeds/program_synthesis.json", "seeds/arc_magnitude.json",
                "seeds/arc_decompose.json", "domains/arc_goal_ingest.py",
                "domains/goal_residual_ingest.py", "domains/arc_magnitude_ingest.py"):
        head = subprocess.run(["git", "-C", ROOT, "show", "HEAD:" + prefix + rel],
                              capture_output=True, text=True).stdout
        assert head, rel
        assert head == open(os.path.join(ROOT, rel)).read(), rel

    r = subprocess.run([sys.executable, os.path.join(
        ROOT, "tools", "build_arc_goals_seed.py"), "--check"],
        capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr


# =========================================================================== #
#  A21 — POOL-COMPOSITION DRIFT, CLOSED WITHOUT TOUCHING `gr_condition_lapse`.
#  Bars: `PROGRAM_SYNTHESIS_ARC6_PREREG.md` amendment A21 (AR21a–AR21d),
#  registered BEFORE this block.  `ax_impotent`'s own `where`/`match`/
#  mint-once guard are UNCHANGED — only its effects gain an additive
#  `pool_stale:0.0` stamp at mint, read and flipped by two new rules.
#  `gr_condition_lapse`/`seeds/goal_residuals.json` are UNTOUCHED throughout.
# =========================================================================== #
_SECOND_AGID = "arc6.claim.tier0_hs1_0_of_10"


def test_a21_AR21c_fires_on_pool_composition_drift_with_NO_epoch_bump():
    """AR21c, direction (i).  A verdict mints for the 7-goal pool
    (pool_stale:0.0).  A SECOND goal then leaves the pool — composition
    drift — with NO epoch bump anywhere in the scene.  Within the SAME
    run_rules() fixpoint: a fresh verdict mints for the new 6-goal pool
    (IM5's own mint-once-by-signature behaviour, unmodified) AND the FIRST
    verdict's pool_stale flips to 1.0, while its epoch-keyed `stale` stays
    0.0 — no measurement has happened, only the pool moved."""
    s, _ = boot()
    s._inner.run_rules()
    _leave_pool_without_retiring(s, AGID)
    s._inner.run_rules()
    first = axe.agenda_verdicts(s, "impotent")
    assert len(first) == 1, first
    assert first[0]["pool_stale"] == 0.0
    assert first[0]["stale"] == 0.0
    first_id = first[0]["_id"]

    _leave_pool_without_retiring(s, _SECOND_AGID)
    s._inner.run_rules()
    after = axe.agenda_verdicts(s, "impotent")
    by_id = {a["_id"]: a for a in after}
    assert set(by_id) >= {first_id}, "the first verdict must still be held"
    assert by_id[first_id]["pool_stale"] == 1.0, (
        "the superseded verdict's pool composition marker must flip the "
        "instant the pool it described has moved")
    assert by_id[first_id]["stale"] == 0.0, (
        "no measurement happened — the EPOCH-keyed flag must be untouched "
        "by pool drift, the two axes are orthogonal")
    fresh = [a for a in after if a["_id"] != first_id]
    assert len(fresh) == 1, after
    assert fresh[0]["pool_n"] == 6
    assert fresh[0]["pool_stale"] == 0.0
    assert AGID not in json.loads(fresh[0]["pool_agids"])
    assert _SECOND_AGID not in json.loads(fresh[0]["pool_agids"])


def test_a21_AR21c_does_NOT_fire_across_a_genuine_epoch_bump_WITHOUT_drift():
    """AR21c, direction (ii).  Reproduce IM5's own 'bump arc_measure_epoch,
    pool composition UNCHANGED' scene: `pool_stale` must NOT flip on either
    the superseded or the fresh verdict — this mechanism must be provably
    orthogonal to the epoch-shaped `gr_condition_lapse` one, not a duplicate
    trigger for it."""
    s, _ = boot()
    s._inner.run_rules()
    _leave_pool_without_retiring(s, AGID)
    s._inner.run_rules()
    before = axe.agenda_verdicts(s, "impotent")
    assert len(before) == 1
    assert before[0]["stale"] == 0.0 and before[0]["pool_stale"] == 0.0

    agi.bump_measure_epoch(s)
    s._inner.run_rules()
    after = axe.agenda_verdicts(s, "impotent")
    assert len(after) == 2, (
        "IM5's own behaviour: the old verdict goes epoch-stale, a fresh one "
        "mints for the SAME (unchanged) pool signature")
    assert all(a["pool_stale"] == 0.0 for a in after), (
        "the pool never moved — pool_stale must stay 0.0 on EVERY held "
        "verdict, including the one gr_condition_lapse just marked "
        "epoch-stale")
    assert sorted({a["stale"] for a in after}) == [0.0, 1.0], (
        "the epoch-keyed flag must still show the SAME split IM5 measured "
        "— this rung does not change gr_condition_lapse's own behaviour")


def test_a21_AR21c_the_reverse_direction_pool_hold_is_TWO_SIDED():
    """The gr_condition_lapse/gr_condition_hold precedent is two-sided by
    construction, and so is this: restoring the pool to EXACTLY the
    composition the first verdict recorded must restore pool_stale to 0.0,
    not leave it permanently latched at 1.0."""
    s, _ = boot()
    s._inner.run_rules()
    _leave_pool_without_retiring(s, AGID)
    s._inner.run_rules()
    first = axe.agenda_verdicts(s, "impotent")[0]
    first_id = first["_id"]
    assert first["pool_stale"] == 0.0

    orig_headroom = None
    for n in s.nodes("ArcGoal"):
        if s.node(n)["attrs"].get("agid") == _SECOND_AGID:
            orig_headroom = s.node(n)["attrs"].get("headroom_n")
    assert orig_headroom is not None
    _leave_pool_without_retiring(s, _SECOND_AGID)
    s._inner.run_rules()
    drifted = [a for a in axe.agenda_verdicts(s, "impotent")
               if a["_id"] == first_id][0]
    assert drifted["pool_stale"] == 1.0

    for n in s.nodes("ArcGoal"):
        if s.node(n)["attrs"].get("agid") == _SECOND_AGID:
            s.set_attr(n, "headroom_n", orig_headroom)
    s._inner.run_rules()
    restored = [a for a in axe.agenda_verdicts(s, "impotent")
                if a["_id"] == first_id][0]
    assert restored["pool_stale"] == 0.0, (
        "a one-way lapse would itself be an unrevisable claim — the "
        "gr_condition_lapse/gr_condition_hold precedent this rule reuses")


def test_a21_AR21c_twin_run_determinism():
    def scene():
        s, _ = boot()
        s._inner.run_rules()
        _leave_pool_without_retiring(s, AGID)
        s._inner.run_rules()
        _leave_pool_without_retiring(s, _SECOND_AGID)
        s._inner.run_rules()
        avs = axe.agenda_verdicts(s, "impotent")
        return sorted(
            [{k: v for k, v in a.items() if k != "_id"} for a in avs],
            key=lambda a: (a["pool_n"], a["pool_stale"]))
    r1, r2 = scene(), scene()
    assert r1 == r2 and r1


def test_a21_AR21d_the_new_rules_are_the_ONLY_addition_to_the_seed():
    """A23 INVERTS THIS PIN TO A PREFIX CHECK, NOT REMOVES IT — the WH1/A18/
    A19/A20 precedent applied a fifth time.  A23 appends a THIRTEENTH and
    FOURTEENTH rule (`ax_ask_impotent`/`_reply`), so the exact-twelve-name
    and exact-version assertion this test made through A21 is now false BY
    CONSTRUCTION.  `test_a23_AR23b_the_new_rules_are_the_ONLY_addition_to_
    the_seed` below asserts the full, current fourteen-name list and
    version; this one still proves the ORIGINAL twelve are an unbroken
    PREFIX, in order, unedited by name."""
    doc = _seed()
    names = [r["name"] for r in doc["rules"]]
    assert names[:12] == [
        "ax_dispatch", "ax_retired_epoch", "ax_rearm", "ax_close",
        "ax_impotent", "ax_world_probe_epoch",
        "ax_fallback_silent", "ax_fallback_cleared",
        "ax_ask_divergence_active", "ax_ask_divergence_cleared",
        "ax_impotent_pool_lapse", "ax_impotent_pool_hold"], names[:12]


def test_a21_AR21d_every_prior_rule_body_is_UNCHANGED_EXCEPT_ax_impotents_ADDITIVE_stamp():
    """Nine of the ten prior rule bodies are byte-identical to `HEAD`.  The
    tenth, `ax_impotent`, is DELIBERATELY not in that set — its `effects`
    gained one additive key (`pool_stale: 0.0` at mint) — so it is checked
    separately below, at the `where`/`match` grain, which must be
    byte-identical (the mint-once guard this rung must not touch)."""
    prefix = subprocess.run(["git", "-C", ROOT, "rev-parse", "--show-prefix"],
                            capture_output=True, text=True).stdout.strip()
    head_doc = json.loads(subprocess.run(
        ["git", "-C", ROOT, "show", "HEAD:" + prefix + "seeds/arc_executor.json"],
        capture_output=True, text=True).stdout)
    head_rules = {r["name"]: r for r in head_doc["rules"]}
    cur_rules = {r["name"]: r for r in _seed()["rules"]}
    for name in ("ax_dispatch", "ax_retired_epoch", "ax_rearm", "ax_close",
                 "ax_world_probe_epoch", "ax_fallback_silent",
                 "ax_fallback_cleared", "ax_ask_divergence_active",
                 "ax_ask_divergence_cleared"):
        assert cur_rules[name] == head_rules[name], name


#  A21 landed on 45eab90 (main's tip when this rung started).  This ONE test
#  is INHERENTLY a diff against the PRE-rung state (it asserts pool_stale is
#  an ADDITION), so it must anchor to that FIXED commit rather than `HEAD` —
#  the GR4 §10.3 precedent ("not an engine issue... committing the rung made
#  HEAD contain the change... re-pointed to a fixed pre-rung commit") applied
#  here before it could bite, not after.  Every OTHER confinement test in
#  this file diffs against `HEAD` correctly, because what THEY check is
#  UNCHANGED by this rung's own commit either way.
_A21_PRE_RUNG_COMMIT = "45eab90"


def test_a21_AR21d_ax_impotents_where_and_match_and_mint_once_guard_are_UNCHANGED():
    """The one rule this rung's mechanism reads from (`ax_impotent`) must
    keep its FIRING behaviour byte-for-byte identical — this rung only adds
    a stamp on top of what it already mints, never changes when it mints."""
    prefix = subprocess.run(["git", "-C", ROOT, "rev-parse", "--show-prefix"],
                            capture_output=True, text=True).stdout.strip()
    head_doc = json.loads(subprocess.run(
        ["git", "-C", ROOT, "show",
         _A21_PRE_RUNG_COMMIT + ":" + prefix + "seeds/arc_executor.json"],
        capture_output=True, text=True).stdout)
    head_impotent = [r for r in head_doc["rules"] if r["name"] == "ax_impotent"][0]
    cur_impotent = _seed_rule("ax_impotent")
    assert cur_impotent["match"] == head_impotent["match"]
    assert cur_impotent["where"] == head_impotent["where"]
    assert cur_impotent["batch"] == head_impotent["batch"]
    #  The effects diff is EXACTLY the one additive stamp — nothing removed,
    #  nothing else added, nothing else edited.
    head_effects = head_impotent["effects"]
    cur_effects = cur_impotent["effects"]
    assert len(cur_effects) == len(head_effects), "no effect added or removed"
    for h, c in zip(head_effects, cur_effects):
        assert h[0] == c[0] and h[1] == c[1] and h[2] == c[2], (h, c)
        if h[0] == "add_node" and h[2] == "AgendaVerdict":
            head_attrs, cur_attrs = h[3], c[3]
            assert head_attrs.get("kind") == "impotent"
            assert "pool_stale" not in head_attrs
            assert cur_attrs.get("pool_stale") == 0.0
            #  every OTHER attr on the AgendaVerdict node is untouched
            for k in head_attrs:
                assert cur_attrs[k] == head_attrs[k], k
            assert set(cur_attrs) - set(head_attrs) == {"pool_stale"}


def test_a21_AR21d_the_adapter_is_BYTE_IDENTICAL_to_HEAD():
    """No adapter edit was needed: `agenda_verdicts(sub, kind=...)` was
    already generic (A19's own finding, reused here verbatim a third time)."""
    prefix = subprocess.run(["git", "-C", ROOT, "rev-parse", "--show-prefix"],
                            capture_output=True, text=True).stdout.strip()
    head = subprocess.run(["git", "-C", ROOT, "show",
                           "HEAD:" + prefix + "domains/arc_executor.py"],
                          capture_output=True, text=True).stdout
    assert head
    assert head == open(os.path.join(ROOT, "domains", "arc_executor.py")).read()


def test_a21_AR21d_gr_condition_lapse_and_every_sibling_seed_are_still_UNTOUCHED():
    """THE HEADLINE CONFINEMENT CHECK THIS RUNG REGISTERED (A21's own AR21b/
    AR21d): `seeds/goal_residuals.json` — i.e. `gr_condition_lapse`'s closed
    `MISMATCH` vocabulary — stays byte-identical to `HEAD`, same as every
    prior rung in this arc has held it, plus the usual sibling seeds/
    adapters this rung does not touch."""
    prefix = subprocess.run(["git", "-C", ROOT, "rev-parse", "--show-prefix"],
                            capture_output=True, text=True).stdout.strip()
    for rel in ("seeds/arc_goals.json", "seeds/goal_residuals.json",
                "seeds/program_synthesis.json", "seeds/arc_magnitude.json",
                "seeds/arc_decompose.json", "domains/arc_goal_ingest.py",
                "domains/goal_residual_ingest.py", "domains/arc_magnitude_ingest.py"):
        head = subprocess.run(["git", "-C", ROOT, "show", "HEAD:" + prefix + rel],
                              capture_output=True, text=True).stdout
        assert head, rel
        assert head == open(os.path.join(ROOT, rel)).read(), rel

    r = subprocess.run([sys.executable, os.path.join(
        ROOT, "tools", "build_goal_residual_seed.py"), "--check"],
        capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr


# =========================================================================== #
#  A23 (PROGRAM_SYNTHESIS_ARC6_PREREG.md amendment A23) -- candidate (a),
#  NATIVE FORM: ax_ask_impotent / ax_ask_impotent_reply.  Mirrors A19-A21's
#  own confinement-test shape exactly.
# =========================================================================== #
def test_a23_AR23b_the_new_rules_are_the_ONLY_addition_to_the_seed():
    """A24 INVERTS THIS PIN TO A PREFIX CHECK, NOT REMOVES IT — the WH1/A18/
    A19/A20/A23 precedent applied a sixth time.  A24 appends a FIFTEENTH
    rule (`ax_ask_impotent_testify`), so the exact-fourteen-name and
    exact-version assertion this test made through A23 is now false BY
    CONSTRUCTION.  `test_a24_AR24b_the_new_rule_is_the_ONLY_addition_to_
    the_seed` below asserts the full, current fifteen-name list and
    version; this one still proves the ORIGINAL fourteen are an unbroken
    PREFIX, in order, unedited by name."""
    doc = _seed()
    names = [r["name"] for r in doc["rules"]]
    assert names[:14] == [
        "ax_dispatch", "ax_retired_epoch", "ax_rearm", "ax_close",
        "ax_impotent", "ax_world_probe_epoch",
        "ax_fallback_silent", "ax_fallback_cleared",
        "ax_ask_divergence_active", "ax_ask_divergence_cleared",
        "ax_impotent_pool_lapse", "ax_impotent_pool_hold",
        "ax_ask_impotent", "ax_ask_impotent_reply"], names[:14]


def test_a23_AR23b_every_prior_rule_body_is_UNCHANGED():
    """All twelve prior rule bodies (A11-A21) are byte-identical to `HEAD` —
    this rung reads `ax_impotent`'s effects (`nearest_unroutable_kind`/
    `nearest_unroutable_agid`/`pool_n`) and `av`'s own mint-once identity; it
    edits none of them."""
    prefix = subprocess.run(["git", "-C", ROOT, "rev-parse", "--show-prefix"],
                            capture_output=True, text=True).stdout.strip()
    head_doc = json.loads(subprocess.run(
        ["git", "-C", ROOT, "show", "HEAD:" + prefix + "seeds/arc_executor.json"],
        capture_output=True, text=True).stdout)
    head_rules = {r["name"]: r for r in head_doc["rules"]}
    cur_rules = {r["name"]: r for r in _seed()["rules"]}
    for name in ("ax_dispatch", "ax_retired_epoch", "ax_rearm", "ax_close",
                 "ax_impotent", "ax_world_probe_epoch", "ax_fallback_silent",
                 "ax_fallback_cleared", "ax_ask_divergence_active",
                 "ax_ask_divergence_cleared", "ax_impotent_pool_lapse",
                 "ax_impotent_pool_hold"):
        assert cur_rules[name] == head_rules[name], name


def test_a23_AR23b_the_new_rules_mint_no_GoalResidual_or_testimony():
    """STATIC confinement check on AR23b's own registered scope boundary:
    candidate (a) only asks a different question, it never mints a
    GoalResidual/testimony (candidate (b) territory, already NO-GO'd by
    A22).  Scans both new rules' effects for any `add_node ... GoalResidual`
    — none may appear."""
    for name in ("ax_ask_impotent", "ax_ask_impotent_reply"):
        rule = _seed_rule(name)
        for eff in rule["effects"]:
            if eff[0] == "add_node":
                assert eff[2] != "GoalResidual", (name, eff)


def test_a23_AR23b_the_new_question_type_is_DISTINCT_from_ArcQuestion():
    """CAUGHT LIVE during this rung's own AR23c measurement (see
    `ax_ask_impotent`'s comment): an `ArcQuestion`-typed node here would
    ALSO match `ag_reply_mints_testimony_conditioned`/`_unconditioned`'s own
    `TypeOf(q)=='ArcQuestion'` guard (`seeds/arc_goals.json`, untouched by
    this rung), silently minting testimony on every reply — candidate (b)'s
    territory, by accident.  `ax_ask_impotent` must mint a type ag_ask's own
    reply rules cannot see."""
    rule = _seed_rule("ax_ask_impotent")
    mint = [e for e in rule["effects"]
            if e[0] == "add_node" and e[1] == "q"][0]
    assert mint[2] == "ArcImpotenceQuestion"
    assert mint[2] != "ArcQuestion"
    reply_rule = _seed_rule("ax_ask_impotent_reply")
    type_check = reply_rule["where"]["items"][0]
    assert type_check["b"]["value"] == "ArcImpotenceQuestion"

    #  Cross-checked against arc_goals.json's own reply rules, read fresh —
    #  they are generic over EVERY ArcQuestion, confirming the risk this
    #  rung's type choice avoids is real, not hypothetical.
    with open(os.path.join(ROOT, "seeds", "arc_goals.json")) as fh:
        goals_doc = json.load(fh)
    for name in ("ag_reply_mints_testimony_conditioned",
                 "ag_reply_mints_testimony_unconditioned"):
        r = [x for x in goals_doc["rules"] if x["name"] == name][0]
        items = r["where"]["items"]
        typeof_checks = [it for it in items
                         if it.get("a", {}).get("type") == "TypeOf"]
        assert typeof_checks and typeof_checks[0]["b"]["value"] == "ArcQuestion"


def test_a23_AR23c_native_ask_is_class_scoped_and_reaches_a_fixed_point():
    """LIVE, THE CRUX GATE.  On the SAME multi-drift testimony chain AR23c
    measured (A22's own decompose + synthetic-exit construction for BOTH
    `re_measure` goals, A14 group-2's own unconditioned reply-chain
    mechanism, which drives `nearest_unroutable_agid`/`kind` to drift across
    KINDS within ONE measurement epoch on an UNCHANGED pool — reproduced
    live here, not assumed from the one-off script's own committed
    artifact): `ax_ask_impotent` mints EXACTLY ONE `ArcImpotenceQuestion`
    for the WHOLE chain, even though this test's own premise requires the
    live winner to visit at least THREE distinct kinds (at least two real
    drifts) for the check to be meaningful at all.  This IS the fixed-point
    property AR23c's design investigation predicted and
    `results/arc6_question_driver_impotence_ask.json` measured
    quantitatively (twin-run byte-identical, native=1 / naive=3 there); this
    test is the standing regression gate for the SAME live property, so a
    future rung cannot silently regress it back to a per-goal guard."""
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import arc6_impotence_resweep_measure as rw  # noqa: E402  (imported for reuse)

    s, ag = rw.boot()
    rw.drive_decompose(s, 5.0)
    s._inner.run_rules()
    #  The structural re_measure ArcGoal does not exist until its own
    #  residual actually goes stale (A22 SS8.3's own finding) — force
    #  staleness first, the SAME narrow poke A13 SS7.1/A15 SS4.2 validated.
    axe._put_fact(s, "arc6_structural_ceiling_present", "0")
    s._inner.run_rules()
    for agid in (rw.AGID_ROW, rw.AGID_STRUCT):
        found = False
        for n in s.nodes("ArcGoal"):
            if s.node(n)["attrs"].get("agid") == agid:
                s.set_attr(n, "headroom_n", 0.0)
                found = True
        assert found, agid
    s._inner.run_rules()

    kinds = []
    pool_sigs = set()
    for _ in range(8):
        at = rw._agenda_attrs(s)
        sel = at.get("arc_sel_agid") if at.get("mg_sel_agid") is None else at.get("mg_sel_agid")
        kinds.append(rw._goal_kind(s, sel) if sel else None)
        pool_sigs.add(tuple(sorted(axe.pool(s))))
        sent = 0
        for n in s.nodes("ArcQuestion"):
            a = s.node(n)["attrs"]
            if a.get("answered") == 1.0 or a.get("status") != "open":
                continue
            agi.attach_reply(s, n, "I do not know either; use your judgement.")
            sent += 1
        s._inner.run_rules()
        if sent == 0:
            break

    assert len(pool_sigs) == 1, (
        "this test's premise (testimony reweights WITHOUT changing "
        "membership, A14's own headline finding) must hold for the fixed-"
        "point property to mean anything: %r" % pool_sigs)
    n_distinct_kinds = len(set(kinds))
    assert n_distinct_kinds >= 3, (
        "this test needs at least 2 real drifts (3 distinct kinds) to be a "
        "meaningful fixed-point check on THIS engine/seed combination: %r"
        % kinds)

    native = list(s.nodes("ArcImpotenceQuestion"))
    assert len(native) == 1, (
        "ax_ask_impotent must mint EXACTLY ONCE across a chain that drifts "
        "nearest_unroutable_agid/kind multiple times on an UNCHANGED pool "
        "-- this is the fixed-point property AR23c measured", native,
        kinds)


# =========================================================================== #
#  A24 (PROGRAM_SYNTHESIS_ARC6_PREREG.md amendment A24) -- THE REPLY SIDE:
#  ax_ask_impotent_testify, class-scoped by kind, NOT a gr_move_penalty
#  reuse (the design investigation found that reuse structurally inert on
#  its own target population -- see the rule's own comment).  Mirrors
#  A19-A23's own confinement-test shape exactly.
# =========================================================================== #
def test_a24_AR24b_the_new_rule_is_the_ONLY_addition_to_the_seed():
    """`seeds/arc_executor.json` regenerates byte-identically from its own
    (edited, version-bumped) emitter; the new rule is purely additive —
    every rule through A23 is still present, unedited, by name and in
    order, with exactly one more appended."""
    doc = _seed()
    assert doc["version"] == "1.9.0"
    names = [r["name"] for r in doc["rules"]]
    assert names == [
        "ax_dispatch", "ax_retired_epoch", "ax_rearm", "ax_close",
        "ax_impotent", "ax_world_probe_epoch",
        "ax_fallback_silent", "ax_fallback_cleared",
        "ax_ask_divergence_active", "ax_ask_divergence_cleared",
        "ax_impotent_pool_lapse", "ax_impotent_pool_hold",
        "ax_ask_impotent", "ax_ask_impotent_reply",
        "ax_ask_impotent_testify"], names
    r = subprocess.run([sys.executable,
                        os.path.join(ROOT, "tools", "build_arc_executor_seed.py"),
                        "--check"], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr


def test_a24_AR24b_every_prior_rule_body_is_UNCHANGED():
    """All fourteen prior rule bodies (A11-A23) are byte-identical to
    `HEAD` — `ax_ask_impotent`/`ax_ask_impotent_reply` in particular, so
    A23's own 'this rule only asks, it does not reprice' statement stays
    literally true after this rung: this rung reads `q.region`/`q.agid_a`/
    `q.asked_epoch` and the `mints_testimony`/`responds_to` edges, it edits
    neither prior rule."""
    prefix = subprocess.run(["git", "-C", ROOT, "rev-parse", "--show-prefix"],
                            capture_output=True, text=True).stdout.strip()
    head_doc = json.loads(subprocess.run(
        ["git", "-C", ROOT, "show", "HEAD:" + prefix + "seeds/arc_executor.json"],
        capture_output=True, text=True).stdout)
    head_rules = {r["name"]: r for r in head_doc["rules"]}
    cur_rules = {r["name"]: r for r in _seed()["rules"]}
    for name in ("ax_dispatch", "ax_retired_epoch", "ax_rearm", "ax_close",
                 "ax_impotent", "ax_world_probe_epoch", "ax_fallback_silent",
                 "ax_fallback_cleared", "ax_ask_divergence_active",
                 "ax_ask_divergence_cleared", "ax_impotent_pool_lapse",
                 "ax_impotent_pool_hold", "ax_ask_impotent",
                 "ax_ask_impotent_reply"):
        assert cur_rules[name] == head_rules[name], name


def test_a24_AR24b_the_new_rule_mints_no_GoalResidual():
    """STATIC confinement check on the design investigation's own finding:
    `gr_move_penalty`'s `MATCH` refuses every candidate this pool can ever
    contain, so a `GoalResidual` minted here would be inert by
    construction, not merely mis-scoped.  `ax_ask_impotent_testify` must
    never mint one."""
    rule = _seed_rule("ax_ask_impotent_testify")
    for eff in rule["effects"]:
        if eff[0] == "add_node":
            assert eff[2] != "GoalResidual", eff


def test_a24_AR24b_the_testimony_type_is_DISTINCT_and_carries_no_weight_field():
    """The testimony node is a NEW, DISTINCT type (`ArcImpotenceTestimony`,
    not `GoalResidual` and not `ArcImpotenceQuestion`), and — per CLAUDE.md's
    SHAPES-not-numbers standing rule — carries no `weight`/`residual_penalty`
    field: nothing downstream reads a class-scoped testimony weight yet, so
    none is authored."""
    rule = _seed_rule("ax_ask_impotent_testify")
    mint = [e for e in rule["effects"]
            if e[0] == "add_node" and e[1] == "t"][0]
    assert mint[2] == "ArcImpotenceTestimony"
    attrs = mint[3]
    assert "weight" not in attrs
    assert "residual_penalty" not in attrs
    assert set(attrs) == {
        "kind", "agid_a", "scope", "asked_epoch", "reply_epoch",
        "evidence_kind", "reach_class", "stale", "_no_weight_by_design"}


def test_a24_AR24b_gr_move_penalty_MATCH_PENALTY_and_AG2_VALUE_are_UNTOUCHED():
    """The design investigation's own headline claim, checked by diff, not
    trusted from prose: `seeds/goal_residuals.json` (`gr_move_penalty`'s
    `MATCH`/`PENALTY`) and `seeds/arc_goals.json` (AG-2's `VALUE`, `ag_ask`,
    both reply rules) are byte-identical to `HEAD` — this rung reads
    neither."""
    prefix = subprocess.run(["git", "-C", ROOT, "rev-parse", "--show-prefix"],
                            capture_output=True, text=True).stdout.strip()
    for rel in ("seeds/arc_goals.json", "seeds/goal_residuals.json",
                "seeds/program_synthesis.json", "domains/arc_goal_ingest.py",
                "domains/goal_residual_ingest.py",
                "domains/arc_magnitude_ingest.py", "domains/arc_executor.py"):
        head = subprocess.run(["git", "-C", ROOT, "show", "HEAD:" + prefix + rel],
                              capture_output=True, text=True).stdout
        assert head, rel
        assert head == open(os.path.join(ROOT, rel)).read(), rel


def _a24_scene_step1(s):
    """Boot, leave the executable AGID out of the pool (A23's own IM1 idiom)
    so the FIRST impotent verdict (`av1`) mints and gets asked about,
    return its own question node."""
    s._inner.run_rules()
    _leave_pool_without_retiring(s, AGID)
    s._inner.run_rules()
    qs = [n for n in s.nodes("ArcImpotenceQuestion")]
    assert len(qs) == 1, qs
    return qs[0]


def test_a24_AR24b_LIVE_scope_defaults_to_unspecified_the_structured_field_works_and_it_lapses():
    """LIVE.  Three things in one scene, each a real graph read, none
    assumed: (1) a reply with no structured `impotence_scope` field mints a
    testimony whose `scope` reads back `'unspecified'` — the null-coalesce
    Term, not a Python default; (2) a reply that DOES carry the field
    (set the SAME way `cond_kind` already is — a structured field on the
    reply `Message`, mechanical translation, never parsed from text) mints
    a testimony carrying it verbatim; (3) the testimony LAPSES through the
    EXISTING, UNMODIFIED `gr_condition_lapse` the instant the measurement
    epoch advances — zero new lapse mechanism, the SAME 'expires at the
    next measurement' idiom every other testimony in this tree already
    uses."""
    s, _ = boot()
    q = _a24_scene_step1(s)
    m = agi.attach_reply(s, q, "not sure, use your judgement")
    s._inner.run_rules()
    ts = list(s.nodes("ArcImpotenceTestimony"))
    assert len(ts) == 1, ts
    t0 = s.node(ts[0])["attrs"]
    assert t0["scope"] == "unspecified"
    assert t0["stale"] == 0.0
    assert t0["kind"] == s.node(q)["attrs"]["region"]

    #  re-run must NOT double-mint (the self-extinguishing edge-existence
    #  guard, the same shape ax_ask_impotent's own re-entry gate uses).
    s._inner.run_rules()
    assert len(list(s.nodes("ArcImpotenceTestimony"))) == 1

    agi.bump_measure_epoch(s)
    s._inner.run_rules()
    t0_after = s.node(ts[0])["attrs"]
    assert t0_after["stale"] == 1.0, (
        "the testimony must lapse through the UNMODIFIED gr_condition_lapse "
        "the instant the epoch it was minted under advances")


def test_a24_AR24b_LIVE_the_structured_scope_field_is_carried_verbatim():
    s, _ = boot()
    q = _a24_scene_step1(s)
    m = agi.attach_reply(s, q, "it applies to every supply_blocker goal")
    s.set_attr(m, "impotence_scope", "class")
    s._inner.run_rules()
    ts = list(s.nodes("ArcImpotenceTestimony"))
    assert len(ts) == 1, ts
    assert s.node(ts[0])["attrs"]["scope"] == "class"


# --------------------------------------------------------------------------- #
#  AR24c -- THE EPOCH-ADVANCE TEST, LIVE, THE CRUX GATE.
# --------------------------------------------------------------------------- #
def _a24_epoch_advance_scene():
    """A23 §7 item 1's own charter, discharged: mint av1, ask q1 about it,
    ANSWER q1; THEN genuinely change the pool's live membership (a SECOND
    goal leaves the pool, A23's own IM1 idiom applied a second time) AND
    bump the measurement epoch (`agi.bump_measure_epoch`, the SAME
    mechanical call `run_order`/`world_probe_advance_epoch` already make)
    — a REAL epoch advance, not graph churn inside one epoch (the case A23
    already covered live).  Returns the full live state needed to check the
    crux property: does the genuinely NEW verdict (av2, different
    pool_agids) get its OWN fresh ask, or does the re-entry gate's
    per-node `InNeighbours(av, asked_about_verdict)` check wrongly block it
    because SOME verdict (av1) was already asked about?"""
    s, _ = boot()
    q1 = _a24_scene_step1(s)
    agi.attach_reply(s, q1, "I do not know either.")
    s._inner.run_rules()
    assert s.node(q1)["attrs"]["answered"] == 1.0

    _leave_pool_without_retiring(s, _SECOND_AGID)
    agi.bump_measure_epoch(s)
    s._inner.run_rules()

    qs = list(s.nodes("ArcImpotenceQuestion"))
    avs = axe.agenda_verdicts(s, "impotent")
    #  Map each question to the verdict node id(s) it asks about.
    q_to_av = {}
    for q in qs:
        tgt = s._inner.neighbours(q, "asked_about_verdict")
        q_to_av[q] = tgt
    return {
        "q1": q1, "n_questions": len(qs), "questions": qs,
        "q_to_av": q_to_av, "avs": avs,
        "av_stale_by_agids": sorted(
            (a["pool_agids"], a["stale"], a["pool_n"]) for a in avs),
    }


def test_a24_AR24c_a_genuinely_new_verdict_after_a_real_epoch_bump_gets_its_own_fresh_ask():
    """LIVE, THE CRUX GATE for AR24c.  A23 §7 item 1 named this precisely
    as unmeasured: 'does a genuinely NEW impotent pool state (a different
    AgendaVerdict node, different pool_agids) correctly get its own fresh
    ask?'  Confirmed here across a REAL measurement-epoch advance, not
    merely reasoned about from the guard's construction."""
    r = _a24_epoch_advance_scene()

    #  TWO DISTINCT AgendaVerdicts now exist, with DIFFERENT pool_agids —
    #  the pool composition genuinely moved, not merely re-weighted.
    assert len(r["avs"]) == 2, r["avs"]
    pool_agid_sets = {a["pool_agids"] for a in r["avs"]}
    assert len(pool_agid_sets) == 2, (
        "the second verdict must describe a GENUINELY different pool, or "
        "this test's own premise is not met", pool_agid_sets)

    #  TWO DISTINCT ArcImpotenceQuestions now exist — the second was NOT
    #  suppressed by the first verdict's own already-asked-about state.
    assert r["n_questions"] == 2, r["questions"]

    #  Exactly one question targets each verdict (a 1:1 pairing), and the
    #  OLD question (q1, already answered) still targets the OLD verdict —
    #  the new question was minted for the NEW verdict, not a re-ask of
    #  the old one.
    targets = [tuple(v) for v in r["q_to_av"].values()]
    assert len(targets) == 2
    assert len(set(targets)) == 2, (
        "both questions must target DIFFERENT verdicts", r["q_to_av"])
    q1_target = r["q_to_av"][r["q1"]]
    assert q1_target != [], (
        "q1 must still point at SOME verdict after the epoch advance", q1_target)


def test_a24_AR24c_LIVE_full_trace_and_the_old_question_is_untouched():
    """The same scene, read for the full trace: the OLD verdict is now
    STALE (`pool_stale`/`stale` — its own `pool_agids` no longer equal the
    live pool), the NEW verdict is fresh, `q1` (answered under the OLD
    verdict) is UNCHANGED by the epoch advance, and the NEW question is
    open and targets the NEW verdict specifically."""
    s, _ = boot()
    q1 = _a24_scene_step1(s)
    agi.attach_reply(s, q1, "I do not know either.")
    s._inner.run_rules()
    q1_attrs_before = dict(s.node(q1)["attrs"])

    _leave_pool_without_retiring(s, _SECOND_AGID)
    agi.bump_measure_epoch(s)
    s._inner.run_rules()

    #  q1 is byte-unchanged by the epoch advance — this rung never revisits
    #  an already-answered question.
    assert s.node(q1)["attrs"] == q1_attrs_before

    qs = list(s.nodes("ArcImpotenceQuestion"))
    assert len(qs) == 2, qs
    q2 = [q for q in qs if q != q1][0]
    assert s.node(q2)["attrs"]["answered"] == 0.0
    assert s.node(q2)["attrs"]["status"] == "open"

    av1_tgt = s._inner.neighbours(q1, "asked_about_verdict")
    av2_tgt = s._inner.neighbours(q2, "asked_about_verdict")
    assert av1_tgt and av2_tgt
    assert av1_tgt != av2_tgt, "the new question must target a DIFFERENT verdict"

    #  Read the two verdicts back via whichever node q1/q2's own edge
    #  points at, not by re-deriving them from agenda_verdicts() — the
    #  same "trust the stamp, not a re-derivation" discipline this arc's
    #  own RUNNER_UP()/SEL_AGID Terms use.
    av1_node = av1_tgt[0]
    av2_node = av2_tgt[0]
    av1_a = s.node(av1_node)["attrs"]
    av2_a = s.node(av2_node)["attrs"]
    assert av1_a["pool_agids"] != av2_a["pool_agids"]
    assert av1_a["stale"] == 1.0, "the OLD verdict lapses on the epoch bump"
    assert av2_a["stale"] == 0.0, "the NEW verdict is fresh"


def test_a24_AR24c_TWIN_RUN_DETERMINISM():
    """The same scene, built and measured twice: the mint counts and the
    (question, verdict) pairing must be identical both times — the IM5/
    A14/A21/A22/A23 twin-run precedent, applied to the epoch-advance
    scene."""
    def run():
        s, _ = boot()
        q1 = _a24_scene_step1(s)
        agi.attach_reply(s, q1, "I do not know either.")
        s._inner.run_rules()
        _leave_pool_without_retiring(s, _SECOND_AGID)
        agi.bump_measure_epoch(s)
        s._inner.run_rules()
        qs = list(s.nodes("ArcImpotenceQuestion"))
        avs = axe.agenda_verdicts(s, "impotent")
        return {
            "n_questions": len(qs),
            "n_verdicts": len(avs),
            "answered_flags": sorted(s.node(q)["attrs"]["answered"] for q in qs),
            "pool_agids": sorted(a["pool_agids"] for a in avs),
            "stale_flags": sorted(a["stale"] for a in avs),
        }
    r1, r2 = run(), run()
    assert r1 == r2 and r1["n_questions"] == 2 and r1["n_verdicts"] == 2, (r1, r2)
