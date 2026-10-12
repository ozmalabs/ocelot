"""Wave 3 gate: the CONVERSATION EXPERIMENT WORLD — a reply_fix concern filed
from chat can now be TESTED, not just noted.

The vertical slice this proves end-to-end (all decisions graph-resident, all
Python mechanical, per CLAUDE.md):

  flag a bad reply turn (mint_reply_flag_concern files the reply_fix
  SelfConcern) -> human-gated promote (conversation bundle:
  test/replay/send/judge/adopt; the 'replay' head grounds via
  seeds/conversation_experiment.json's RelationCue) -> _concern_tick grounds
  it (induce_concern residual -> ground_concern -> the experiment composer's
  conversation branch: mint rule pinned to the held ChatWorld 'conversation'
  WorldInstance, SeedDelta = targeted reply-rule ABLATION picked by the
  agent's own RuleSummary-overlap Argmax) -> the agent's own author rule
  mints Experiment{game:'conversation', status:'requested'} ->
  experiment_dispatch routes game=='conversation' to scripts/convo_child_run.py
  (a real subprocess, as in production) -> the child replays the recorded
  corpus from the snapshot and scores flagged-turn-fixed minus regressions ->
  the agent's own judge rule reads score-per-frame sign -> supported ->
  mark_adopt_ready + perform_adoptions folds the winner back into the PARENT
  (an ablation adoption: remove-only, provenance-gated) -> the parent's own
  reply behaviour actually changes.

Also gated here: the no-op delta scores 0 -> inconclusive; a delta that breaks
an unflagged reply scores negative -> refuted; the new seed's RelationCue loads
on a full boot and reconciles churn-free on a resumed/minimal agent.

PAIRED-CONTROL-REPLAY wave: `regressions` is now checked against the child's
own independent CONTROL-pass replay of each unflagged probe, not the recorded
reply text (scripts/convo_child_run.py's module docstring has the full
diagnosis/fix). Gated here: a genuinely no-op delta scores ZERO regressions
BY CONSTRUCTION even over a corpus that exercises the state-dependent
machinery (told-status repeats) that used to manufacture false regressions
and blocked R3/R4 from adopting.
"""
from __future__ import annotations

import json
import os
import sys
import time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

jd = pytest.importorskip("jabberwock_daemon")

import domains.reflective_faculty as rf                                  # noqa: E402
from domains.experiment_dispatch import scan_and_dispatch, mint_experiment, _INFLIGHT   # noqa: E402

_CONCLUSIONS_SEED = os.path.join(ROOT, "seeds", "experiment_conclusions.json")


@pytest.fixture(autouse=True)
def _guard_conclusions_seed():
    """close_experiment_loop teach()es real verdicts into a checked-in seed —
    snapshot/restore it so gate runs leave no debris (the same guard
    scripts/autonomous_improvement_gate.py applies)."""
    existed = os.path.exists(_CONCLUSIONS_SEED)
    before = open(_CONCLUSIONS_SEED).read() if existed else None
    try:
        yield
    finally:
        if before is not None:
            with open(_CONCLUSIONS_SEED, "w") as f:
                f.write(before)
        elif not existed and os.path.exists(_CONCLUSIONS_SEED):
            os.unlink(_CONCLUSIONS_SEED)


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _have_two_turns(a) -> int:
    """Record the two-probe corpus: one stable unflagged turn + the turn whose
    reply the human will flag. Returns the flaggable turn's inbound id."""
    r1 = a.converse("Hello.", speech_act="greeting")
    assert (r1 or "").strip(), "the greeting turn must produce a recorded reply"
    r2 = a.converse("What are you?", speech_act="question")
    assert (r2 or "").strip() == "I am Jabberwock."
    return a.last_turn_inbound_id()


def _flag(a, turn_id) -> str:
    res = jd.flag_reply_turn(a, str(turn_id),
                             "identity reply rule wrong: test ablate the reply variant")
    assert res["ok"] and res.get("concern_id"), res
    return str(res["concern_id"])


def _experiments(a, game=None):
    out = []
    for n in a.s.nodes("Experiment"):
        at = a.s.node(n)["attrs"]
        if game is None or at.get("game") == game:
            out.append((n, at))
    return out


def _delta_attrs(a, exp):
    for d in a.inner.neighbours(exp, "has_delta"):
        if a.s.has_node(d):
            return a.s.node(d)["attrs"]
    return {}


def _dispatch_until(a, runs_dir, exp, timeout_s=300.0):
    """Production-shaped dispatch: scan_and_dispatch spawns the detached child
    subprocess; poll (never block) until THIS experiment leaves requested/
    running. Other requested experiments (e.g. the seeded standing ARC
    concern's) run alongside, as they would in the daemon."""
    _INFLIGHT.clear()
    t0 = time.time()
    scan_and_dispatch(a, str(runs_dir))
    while time.time() - t0 < timeout_s:
        status = a.s.node(exp)["attrs"].get("status")
        if status not in ("requested", "running"):
            return status
        time.sleep(0.5)
        scan_and_dispatch(a, str(runs_dir))
    return a.s.node(exp)["attrs"].get("status")


def _probe_judge_rule(tag: str) -> dict:
    """The SAME judge shape the composer authors (score-per-frame sign as a held
    IfThenElse) under a test-local tag — installed as graph data so the
    mechanical-level gates below (no-op / regression) get a verdict without
    running the whole promote pipeline again."""
    V = lambda n: {"type": "Var", "name": n}
    L = lambda v: {"type": "Lit", "value": v}
    Attr = lambda nd, k: {"type": "Attr", "node": nd, "key": k}
    outcome = {"type": "IfThenElse",
               "cond": {"type": "Gt", "a": {"type": "Div", "a": Attr(V("run"), "score"),
                                             "b": Attr(V("run"), "frames")}, "b": L(0.0)},
               "then": L("supported"),
               "other": {"type": "IfThenElse",
                         "cond": {"type": "Lt", "a": {"type": "Div", "a": Attr(V("run"), "score"),
                                                       "b": Attr(V("run"), "frames")}, "b": L(0.0)},
                         "then": L("refuted"), "other": L("inconclusive")}}
    return {
        "name": "judge_experiment_outcome_" + tag,
        "match": [["exp", "produced", "run"]],
        "where": {"type": "And", "items": [
            {"type": "Eq", "a": Attr(V("run"), "status"), "b": L("done")},
            {"type": "Not", "arg": {"type": "Exists",
                                     "source": {"type": "Neighbours", "node": V("exp"),
                                                "edge_type": "analysed"},
                                     "var_name": "_j", "predicate": L(True)}},
        ]},
        "effects": [
            ["set_attr", "exp", "outcome", {"__term__": outcome}],
            ["add_edge", "exp", "analysed", "run"],
            ["set_attr", "exp", "conclusion_ready", True],
        ],
    }


# --- THE VERTICAL SLICE -------------------------------------------------------

def test_flag_promote_experiment_judge_adopt_closes(agent, tmp_path):
    turn_id = _have_two_turns(agent)
    concern_id = _flag(agent, turn_id)

    # human-gated promote -> the conversation experiment bundle
    p = jd.promote_self_concern(agent, concern_id)
    assert p["ok"], p
    assert p["pipeline"] == "experiment"
    import substrate_rs as srs
    standing = srs.NodeID(int(p["standing_concern"]))
    heads = {r[0] for r in (agent.s.node(standing)["attrs"].get("relations") or []) if r}
    assert {"test", "replay", "send", "judge", "adopt"} <= heads
    assert "gradient" not in heads and "vary" not in heads, \
        "the conversation bundle carries neither the ARC acting-variant nor the seed-skip vary"

    # the promote held the conversation world (ChatWorld type, never 'Game')
    convo_wi = [n for n in agent.s.nodes("WorldInstance")
                if agent.s.node(n)["attrs"].get("name") == "conversation"]
    assert convo_wi and all(
        agent.s.node(n)["attrs"].get("world_type") == "ChatWorld" for n in convo_wi)

    # grounding: the daemon's own hook -> the agent's own author rule mints the Experiment
    jd._concern_tick(agent)
    convo_exps = [(n, at) for n, at in _experiments(agent, game="conversation")]
    assert len(convo_exps) == 1, \
        f"exactly one conversation experiment expected, got {[(int(n.value), at.get('axis_tag')) for n, at in convo_exps]}"
    exp, at = convo_exps[0]
    assert at.get("status") == "requested"
    assert at.get("axis_tag") == f"promoted_self_concern_{concern_id}"
    da = _delta_attrs(agent, exp)
    assert json.loads(da.get("remove_rules") or "[]") == ["reply_self_identity"], da
    assert da.get("act_rule_varied") == "reply_self_identity"
    assert da.get("ablation") == 1.0
    assert json.loads(da.get("add_rules") or "[]") == []
    assert json.loads(da.get("skip_seeds") or "[]") == []

    # dispatch: real subprocess, production path
    status = _dispatch_until(agent, tmp_path / "runs", exp)
    assert status == "done", (status, agent.s.node(exp)["attrs"].get("error"))
    runs = [r for r in agent.inner.neighbours(exp, "produced") if agent.s.has_node(r)]
    assert runs, "Experiment -produced-> Run must be ingested"
    ra = agent.s.node(runs[0])["attrs"]
    assert ra["status"] == "done"
    assert int(ra["frames"]) == 2, "two recorded turns -> two probes"
    # TRANCHE 4 JUDGE: ablating reply_self_identity changes the flagged reply
    # into the adapter's fixed ERROR surface. That is a BROKEN fix, not a fix:
    # it scores -1 and the experiment is refuted, so nothing is adopted.
    assert int(ra["score"]) <= -1, "a change into the error surface is a broken fix"
    child = json.load(open(os.path.join(agent.s.node(exp)["attrs"]["run_dir"], "result.json")))
    assert child["broken_fixes"] == 1 and child["flagged_changed"] == 0, child
    obs = [o for o in agent.inner.neighbours(runs[0], "observed") if agent.s.has_node(o)]
    assert len(obs) == 2 and all(
        agent.s.node(o)["attrs"].get("action") == "reply" for o in obs), \
        "the frame-shaped trace must ingest as RunObservation nodes unchanged"

    # judge: the agent's OWN authored rule reads the run -> refuted, never adopted
    agent.comprehend()
    at = agent.s.node(exp)["attrs"]
    assert at.get("outcome") == "refuted", at
    assert at.get("conclusion_ready") is True
    assert not at.get("adopt_ready"), at
    rf.close_experiment_loop(agent)
    at = agent.s.node(exp)["attrs"]
    assert not at.get("adopted"), at
    live = [r.get("name") for r in agent.inner.export_rules() if r.get("active")]
    assert "reply_self_identity" in live, "a broken fix must not be folded into the parent"
    r = agent.converse("What are you?", speech_act="question")
    assert (r or "").strip() == "I am Jabberwock.", "the parent keeps its working reply"


# --- MECHANICAL-LEVEL GATES: no-op and regression deltas ----------------------

def test_noop_delta_scores_zero_and_is_inconclusive(agent, tmp_path):
    turn_id = _have_two_turns(agent)
    _flag(agent, turn_id)                       # a flagged probe exists; the delta is a no-op
    exp = mint_experiment(agent, "no-op conversation delta", "conversation")
    agent.inner.add_rule(_probe_judge_rule("noop_probe"))
    status = _dispatch_until(agent, tmp_path / "runs", exp)
    assert status == "done", (status, agent.s.node(exp)["attrs"].get("error"))
    run = next(r for r in agent.inner.neighbours(exp, "produced") if agent.s.has_node(r))
    ra = agent.s.node(run)["attrs"]
    assert int(ra["frames"]) == 2
    assert int(ra["score"]) == 0, "a no-op delta must change nothing -> score 0"
    agent.comprehend()
    assert agent.s.node(exp)["attrs"].get("outcome") == "inconclusive"


def test_breaking_delta_scores_negative_and_is_refuted(agent, tmp_path):
    turn_id = _have_two_turns(agent)
    _flag(agent, turn_id)
    # ablating the adjacency-pair reply breaks the UNFLAGGED greeting turn while
    # leaving the flagged identity turn intact -> a pure regression.
    exp = mint_experiment(agent, "break the greeting reply", "conversation",
                          remove_rules=["reply_to_adjacency_pair"])
    agent.inner.add_rule(_probe_judge_rule("regress_probe"))
    status = _dispatch_until(agent, tmp_path / "runs", exp)
    assert status == "done", (status, agent.s.node(exp)["attrs"].get("error"))
    run = next(r for r in agent.inner.neighbours(exp, "produced") if agent.s.has_node(r))
    ra = agent.s.node(run)["attrs"]
    assert int(ra["score"]) <= -1, "a delta that breaks an unflagged reply must score negative"
    agent.comprehend()
    assert agent.s.node(exp)["attrs"].get("outcome") == "refuted"


# --- PAIRED-CONTROL REPLAY: the determinism gate -------------------------------
#
# scripts/convo_child_run.py used to replay the corpus TWICE on ONE booted
# substrate (a "control" pass, then the delta, then a "variant" pass on top of
# the control pass's own mutations) and score `regressions` against the
# RECORDED reply text. Since the interlocutor waves made converse() genuinely
# STATE-DEPENDENT (told-status repeats fire "as I mentioned..."; gap/concern
# dedup guards; party-model evolution), that shape manufactured false
# regressions in EARLY, delta-unrelated turns purely from replaying a corpus
# that was itself once a live, stateful conversation — this is what blocked
# R3/R4 from adopting (commit f111cb6e4e). The fix is PAIRED-CONTROL REPLAY:
# two INDEPENDENT boots of the same snapshot, `regressions` now checked
# against the CONTROL pass's reply for the SAME probe, not the recorded text.
# A genuinely no-op delta must therefore score ZERO regressions BY
# CONSTRUCTION, even over a corpus that exercises the exact state-dependent
# machinery that broke the old shape (a topic asked twice, tripping
# seeds/conversation_grice.json's `reply_topic_repeat_known`).

def test_paired_control_replay_scores_zero_regressions_on_stateful_corpus(agent, tmp_path):
    a = agent
    a.converse("Hi, I am Nora.", speech_act="statement")
    a.learn_from_teacher("what is zqxbelt",
                         {"answer": "zqxbelt is a made up test concept",
                          "learn": [{"phrase": "zqxbelt"}]})
    a.converse("What do you know about zqxbelt?", speech_act="question")
    # the SECOND ask of the same topic is the state-dependent turn: the
    # concept is now in believed_concepts, so `reply_topic_repeat_known` can
    # fire on it -- exactly the mechanism that manufactured a false
    # regression for R3 under the old shared-substrate double-pass.
    r2 = a.converse("What do you know about zqxbelt?", speech_act="question")
    assert (r2 or "").strip(), "the second ask must still produce a recorded reply"

    exp = mint_experiment(a, "no-op paired-control determinism probe", "conversation")
    status = _dispatch_until(a, tmp_path / "runs", exp)
    assert status == "done", (status, a.s.node(exp)["attrs"].get("error"))
    run = next(r for r in a.inner.neighbours(exp, "produced") if a.s.has_node(r))
    ra = a.s.node(run)["attrs"]
    assert int(ra["frames"]) == 3, "three interlocutor turns recorded -> three probes"
    assert int(ra.get("regressions") or 0) == 0, (
        "a genuinely no-op delta must score ZERO regressions under paired-control "
        "replay, even over a corpus exercising told-status/state-dependent replies")
    assert int(ra["score"]) == 0


# --- SEED HYGIENE --------------------------------------------------------------

def test_replay_cue_loads_and_reconciles_churn_free(agent):
    # full boot holds the new seed's RelationCue
    cues = [n for n in agent.s.nodes("RelationCue")
            if agent.s.node(n)["attrs"].get("name") == "replay_conversation"]
    assert len(cues) == 1, "seeds/conversation_experiment.json must load exactly once on a full boot"

    # a minimal (checkpoint-shaped) agent lacks it; typed-node reconciliation
    # installs it exactly once and is idempotent (the resumed-daemon path).
    a = WorldAdapter()
    def _cue_names():
        return [a.s.node(n)["attrs"].get("name") for n in a.s.nodes("RelationCue")]
    assert "replay_conversation" not in _cue_names()
    added = jd._reconcile_seed_typed_nodes(a, "RelationCue", "name")
    assert added > 0
    assert _cue_names().count("replay_conversation") == 1
    assert jd._reconcile_seed_typed_nodes(a, "RelationCue", "name") == 0

    # churn-freeness of THIS wave's seed edits: conversation_experiment ships
    # ZERO rules (one RelationCue node only), so it can never trip the
    # _canon_rule_body refresh path. (A global `_reconcile_seed_rules(a) == 0`
    # assertion is deliberately NOT made here — the tree carries pre-existing
    # refresh churn in conversation_attachment_reply / conversation_capability_
    # reply / conversation_topic_reply / upload_foveated_text, which is NAMED
    # here rather than counted.)
    #
    # BASELINE REFERENCE CORRECTED 2026-07-21 (comment only; no assertion moved).
    # This read "part of the documented 19-failure baseline". That baseline was a
    # COUNT, and it is now 144 node ids with no rung on the path negligent — a
    # count can be HELD, so it absorbs new reds and silently swallows fixes. The
    # four seeds above are named explicitly for that reason; the enumerated
    # baseline is `results/failure_baseline.json`, gated by
    # tests/test_failure_baseline_migrated.py. Do not re-cite a number here.
    seed = json.load(open(os.path.join(ROOT, "seeds", "conversation_experiment.json")))
    assert seed["rules"] == [] and seed["id"] == "conversation_experiment"
