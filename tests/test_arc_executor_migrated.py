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
    (AG-5's four plus A13's ax_impotent); five rules after."""
    names = sorted(r["name"] for r in _seed()["rules"])
    assert names == sorted(
        ["ax_dispatch", "ax_retired_epoch", "ax_rearm", "ax_close",
         "ax_impotent"]), names


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
