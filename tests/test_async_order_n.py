"""test_async_order_n — THE ORDER-N COLLAPSES ARE ASYNC + REVISABLE; the FIRST
PASS stays ORDERED.

The cortices+tick foundation (7a6cb318) ticks five cortices, but every stage still
fires ONCE in data-dependency order (each la_dispatch_* stage marks `done` and never
re-fires). That is CORRECT for the FIRST PASS (the ordered LANGUAGE + SITUATION
stream) but WRONG for the ORDER-N collapses. This gate proves the higher-order
recognitions (narrative arc, trope/theme, executive monitoring) are now MATERIAL-
TRIGGERED + REVISABLE, re-arming (done -> pending) when their input-node set GROWS or
a coherence break flags a GlobalIncoherence -- the exact sd_redecode/codebook_epoch
re-arm-on-growth mechanism (seeds/shape_decode_loop.json), mirrored for the reading
in the new la_rearm_* rules -- while the FIRST PASS keeps its one-shot ordered latch.

  * CROW byte-identical FINAL -- the async is the PROCESS; the settled report equals
    the frozen one-shot baseline byte-for-byte.
  * REVISABILITY -- feed the fable incrementally (sentence by sentence, ticking
    between); the arc/theme UPDATE as sentences accumulate (re-collapsing), not only
    at the end. An order-N collapse fires MORE THAN ONCE (revised); a first-pass stage
    fires ONCE (ordered), autonomously (nobody re-dispatches the order-N stage).
  * COHERENCE-BREAK RE-READ -- a settled arc/theme, then a later non-sequitur the
    monitor flags: the order-N RE-COLLAPSES and the interpretation CHANGES.
  * ASYNC AUDIT -- the order-N dispatch rules carry no prior-stage-`done` latch; the
    re-arm is a graph precondition/epoch (not a Python loop); the first pass stays
    ordered; no run_rules/fire_reflexes in the reading path; no import re; donkey = 0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_async_order_n.py -p no:randomly -q -s
"""
from __future__ import annotations

import ast
import inspect
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains import dictionary_lexicon as dl                           # noqa: E402
from domains import reading_drive as rd                                # noqa: E402
import jabberwock_reads_incrementally as jri                           # noqa: E402
import jabberwock_produces_analysis_from_goal as jpafg                 # noqa: E402
import jabberwock_ticks_a_reading as jtr                               # noqa: E402


_SEED = os.path.join(ROOT, "seeds", "literary_analysis_driving.json")


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


@pytest.fixture(scope="module")
def _crow():
    ad, log = jri.stream_incrementally(jri.CROW)
    return ad, log


# --------------------------------------------------------------------------- #
#  CROW byte-identical FINAL — the async is the PROCESS; the verdict is the same.
# --------------------------------------------------------------------------- #
def test_crow_streamed_final_is_byte_identical(_crow):
    ad, log = _crow
    streamed = jpafg._read_report_off_graph(ad.s)
    baseline = jtr.tick_a_reading(jri.CROW)["report"]
    print("\n" + "=" * 78 + "\nCROW streamed FINAL report (== frozen one-shot baseline)\n"
          + "=" * 78 + "\n" + streamed)
    assert streamed == baseline, "the incrementally-streamed final report drifted from the baseline"


# --------------------------------------------------------------------------- #
#  REVISABILITY — the arc/theme UPDATE as sentences accumulate (re-collapsing),
#  NOT only at the end. VERBATIM log.
# --------------------------------------------------------------------------- #
def test_arc_and_theme_update_incrementally(_crow):
    ad, log = _crow
    print("\n" + "=" * 78 + "\nINCREMENTAL crow — arc/theme AT EACH TICK (verbatim)\n" + "=" * 78)
    print("  %-3s %-9s %-9s %-46s %s" % ("k", "narr_adv", "spine_adv", "arc", "theme"))
    for r in log:
        theme = "; ".join("%s:%s" % (t["entity"], "+".join(t["tropes"])) for t in r["theme"]) or "(none)"
        print("  %-3d %-9d %-9d %-46s %s" % (r["k"], r["narrative_adv"], r["spine_adv"], str(r["arc"]), theme))

    # the arc GROWS as material accumulates — an early step is a strict subset of the
    # final (it does NOT appear only at the end).
    first_arc, final_arc = set(log[0]["arc"]), set(log[-1]["arc"])
    assert first_arc and first_arc < final_arc, "the arc did not grow as sentences accumulated"
    # at least one INTERMEDIATE step shows a partial arc distinct from the final.
    assert any(0 < len(r["arc"]) < len(log[-1]["arc"]) for r in log[:-1]), \
        "no intermediate step showed a partial (still-collapsing) arc"
    # the theme is EMPTY early and PRESENT at the end (it forms only once the
    # resolving material has streamed in — the revisable order-N collapse).
    assert not log[0]["theme"] and log[-1]["theme"], "the theme did not emerge as material accumulated"


def test_order_n_re_collapses_and_role_is_re_interpreted(_crow):
    """The narrative collapse RE-COLLAPSES more than once (its advance_count climbs)
    AND a role is genuinely RE-INTERPRETED — the resolving sentence turns order 4 from
    'action' into 'solution' (supersession, not accretion)."""
    ad, log = _crow
    assert log[-1]["narrative_adv"] > 1, "the narrative order-N collapse never re-collapsed"
    # order 4 read as 'action' at some step, then RE-INTERPRETED as 'solution' later.
    role_at_4 = [dict(r["arc"]).get(4) for r in log if dict(r["arc"]).get(4) is not None]
    assert "action" in role_at_4 and role_at_4[-1] == "solution", \
        "order 4 was not re-interpreted action -> solution across the stream"
    # the re-collapse is MATERIAL-TRIGGERED, not once-per-tick: it fires exactly
    # once per increment whose SmEvent material GREW, NOT on every cognitive_tick
    # (each increment's settle runs many ticks). Under GENERIC EVENTIVE (2026-07-07)
    # every crow sentence is now eventful (found/reach/drop/rose/drink all mint an
    # SmEvent), so — unlike the pre-generic reading, where the event-free 'could not
    # reach' increment left the SmEvent count flat for one step — every increment
    # grows the material; the material-triggered property is therefore proven the
    # direct way: the number of narrative re-collapses equals the number of
    # material-growth increments (<= len(log)), FAR below the total tick count a
    # per-tick (non-material-triggered) re-collapse would produce.
    growth_increments = 1 + sum(1 for i in range(1, len(log))
                                if log[i]["smevent"] > log[i - 1]["smevent"])
    assert log[-1]["narrative_adv"] == growth_increments <= len(log), (
        "narrative re-collapse count (%d) is not once-per-material-growth-increment "
        "(%d) — it would spin every tick if not material-triggered"
        % (log[-1]["narrative_adv"], growth_increments))


def test_order_n_fires_more_than_once_first_pass_fires_once():
    """AUTONOMOUS RE-ARM: after a full read settles, grow the trigger material WITHOUT
    re-dispatching any first-pass stage. The order-N narrative collapse re-fires ON
    ITS OWN (the graph rule); the first-pass spine fires exactly ONCE (no re-arm rule)."""
    ra = jri.demonstrate_autonomous_rearm(jri.CROW)
    print("\nAUTONOMOUS RE-ARM (grow one event, no first-pass re-dispatch):")
    print("  before:", ra["before"], "\n  after :", ra["after"])
    assert ra["after"]["narrative"] > ra["before"]["narrative"], \
        "the order-N narrative collapse did not re-arm+re-collapse on material growth"
    assert ra["before"]["spine"] == 1 and ra["after"]["spine"] == 1, \
        "the first-pass spine re-fired — it must be one-shot (no re-arm rule)"


# --------------------------------------------------------------------------- #
#  COHERENCE-BREAK RE-READ — a settled arc/theme, then a later non-sequitur the
#  monitor flags: the order-N RE-COLLAPSES and the interpretation CHANGES. VERBATIM.
# --------------------------------------------------------------------------- #
def test_coherence_break_re_reads_and_changes_interpretation():
    cb = jri.demonstrate_coherence_break(jri.CROW, jri.BREAK)
    b, a = cb["before"], cb["after"]
    print("\n" + "=" * 78 + "\nCOHERENCE BREAK — before/after the non-sequitur (verbatim)\n" + "=" * 78)
    print("  break sentences:", cb["break_sentences"])
    print("  BEFORE (k=%d): GlobalIncoherence=%d narr_adv=%d trope_adv=%d\n     arc=%s\n     theme=%s"
          % (b["k"], b["global_incoherence"], b["narrative_adv"], b["trope_adv"], b["arc"],
             [t["tropes"] for t in b["theme"]]))
    print("  AFTER  (k=%d): GlobalIncoherence=%d narr_adv=%d trope_adv=%d\n     arc=%s\n     theme=%s"
          % (a["k"], a["global_incoherence"], a["narrative_adv"], a["trope_adv"], a["arc"],
             [t["tropes"] for t in a["theme"]]))
    # the monitor FLAGGED the non-sequitur (a GlobalIncoherence was raised).
    assert cb["flagged"], "the executive monitor did not flag the non-sequitur as a GlobalIncoherence"
    # the order-N collapses RE-COLLAPSED after the break (advance_count climbed).
    assert a["narrative_adv"] > b["narrative_adv"], "the narrative collapse did not re-read on the break"
    assert a["trope_adv"] > b["trope_adv"], "the trope collapse did not re-read on the break"
    # the interpretation genuinely CHANGED (the settled theme before the break is not
    # the settled theme after it — the re-read superseded the prior verdict).
    assert b["theme"] and b["theme"] != a["theme"], "the interpretation did not change on the coherence break"


# --------------------------------------------------------------------------- #
#  ASYNC AUDIT — the mechanism is graph-native and correctly scoped.
# --------------------------------------------------------------------------- #
def _rule(seed, name):
    return next(r for r in seed["rules"] if r["name"] == name)


def _mentions_stage_done(where) -> bool:
    """Does this where-clause gate on a prior AnalysisStage being `done` (the old
    one-shot latch)? A recursive scan for an Exists over AnalysisStage with a
    status=='done' equality."""
    blob = json.dumps(where)
    return '"node_type": "AnalysisStage"' in blob and '"value": "done"' in blob


def test_order_n_dispatch_has_no_prior_stage_done_latch():
    with open(_SEED) as f:
        seed = json.load(f)
    for name in ("la_dispatch_narrative", "la_dispatch_trope"):
        assert not _mentions_stage_done(_rule(seed, name)["where"]), \
            "%s still gates on a prior-stage-`done` latch — not material-triggered" % name
    # the first-pass 'enabling'/'centrality' dispatch DO still chain on prior-stage
    # done (the ordered first pass is UNCHANGED) — proves the change is scoped.
    assert _mentions_stage_done(_rule(seed, "la_dispatch_enabling")["where"]), \
        "the first-pass enabling stage lost its ordered gate — the first pass must stay ordered"


def test_re_arm_rules_are_graph_preconditions_on_growth():
    with open(_SEED) as f:
        seed = json.load(f)
    names = {r["name"] for r in seed["rules"]}
    for nm in ("la_rearm_narrative", "la_rearm_trope", "la_rearm_monitoring"):
        assert nm in names, "missing re-arm rule %s" % nm
        r = _rule(seed, nm)
        blob = json.dumps(r["where"])
        # the re-arm is a graph precondition: a DONE stage whose input_epoch is Lt a
        # live Count of its trigger node type (the sd_redecode/codebook_epoch mirror).
        assert '"value": "done"' in blob and '"type": "Lt"' in blob and '"input_epoch"' in blob
        assert r["effects"] == [["set_attr", "stage", "status", "pending"]], \
            "%s must re-arm (done -> pending), the sd_redecode idiom" % nm
    # narrative + trope also re-arm on a coherence break (coh_epoch < Count(GlobalIncoherence)).
    for nm in ("la_rearm_narrative", "la_rearm_trope"):
        assert '"coh_epoch"' in json.dumps(_rule(seed, nm)["where"]) and \
               '"GlobalIncoherence"' in json.dumps(_rule(seed, nm)["where"])


def test_reading_path_drives_via_tick_not_run_rules():
    """The incremental reading path rides cognitive_tick — no hand-called run_rules()/
    fire_reflexes() (AST, ignoring docstring prose)."""
    def calls(fn):
        names = set()
        for n in ast.walk(ast.parse(inspect.getsource(fn))):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                names.add(n.func.attr)
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                names.add(n.func.id)
        return names
    for fn in (jri.stream_incrementally, jri._settle, jri.demonstrate_coherence_break):
        c = calls(fn)
        assert "run_rules" not in c and "fire_reflexes" not in c, \
            "%s hand-calls run_rules/fire_reflexes in the reading path" % fn.__name__
    assert "cognitive_tick" in calls(jri._settle), "the settle loop must ride cognitive_tick"
    # the epoch stamping + re-collapse supersession live on the tick's advance shim.
    src = inspect.getsource(rd._advance_cortex_stage)
    assert "input_epoch" in src and "coh_epoch" in src and "_supersede_order_n" in src


def test_no_import_re_donkey_zero():
    for mod in (jri, rd):
        tree = ast.parse(inspect.getsource(mod))
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                assert not any(a.name == "re" for a in n.names), "import re in %s" % mod.__name__
            if isinstance(n, ast.ImportFrom):
                assert n.module != "re", "from re import in %s" % mod.__name__
    src = inspect.getsource(jri) + inspect.getsource(rd)
    for banned in ("openai", "anthropic", "requests.post", "call_model"):
        assert banned not in src, "donkey found: %s" % banned
