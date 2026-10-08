"""Wave 6 gate: THE AGENT-SIDE ADOPTION SAFETY GATE — a supported-but-
regressing variant is never adopted.

The hole this closes: the conversation judge nets its score
(flagged_changed − regressions), so a variant that fixes the flagged turns
but breaks one previously-working turn can still judge 'supported'
(+2−1=+1) and reach mark_adopt_ready. The fix is GRAPH DATA, not Python:

  * the child already reports `regressions` in result.json; the dispatch
    ingest (domains/experiment_dispatch.py::_ingest_result) now carries it
    mechanically onto the Run AND the Experiment node;
  * seeds/adoption_safety.json's `adopt_denied_on_regression` rule VETOES
    (sets `adopt_denied` + an honest `adopt_denied_reason`) any Experiment
    whose own child reported regressions > 0 — perform_adoptions honours the
    denial unconditionally;
  * the denial is readable over NL: the self_improvement_status reader
    surfaces "blocked from adoption (<reason>)" for 'what are you working
    on?'.

Chosen over a stricter mark_adopt_ready where-clause deliberately: the
authored mark_adopt_ready_* bodies stay byte-identical, so the graph-meta
oracle parity (seeds/composer_experiment_graph.json's
wants_experiment_adopt_rule) is preserved untouched — and the headline test
below PROVES the where-clause is unchanged: adopt_ready still goes True on
the regressing experiment; the veto, not a narrower candidate rule, blocks
it.
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


def _dispatch_until(a, runs_dir, exp, timeout_s=300.0):
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


def _delta_of(a, exp):
    for d in a.inner.neighbours(exp, "has_delta"):
        if a.s.has_node(d):
            return d
    return None


def _probe_judge_rule(tag: str) -> dict:
    """The SAME judge shape the composer authors (test_convo_experiment's probe)."""
    V = lambda n: {"type": "Var", "name": n}
    L = lambda v: {"type": "Lit", "value": v}
    Attr = lambda nd, k: {"type": "Attr", "node": nd, "key": k}
    rate = {"type": "Div", "a": Attr(V("run"), "score"), "b": Attr(V("run"), "frames")}
    outcome = {"type": "IfThenElse", "cond": {"type": "Gt", "a": rate, "b": L(0.0)},
               "then": L("supported"),
               "other": {"type": "IfThenElse", "cond": {"type": "Lt", "a": rate, "b": L(0.0)},
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


def _probe_adopt_rule(tag: str) -> dict:
    """BYTE-SHAPE of the authored mark_adopt_ready_* non-cue path (see
    _compose_experiment_rule's adopt builder) — installed under a test tag so
    the mechanical slice gets an adopt-readiness decision without the promote
    pipeline. Deliberately UNCHANGED by this wave: the safety gate is the
    standing veto rule, never a narrower candidate rule."""
    V = lambda n: {"type": "Var", "name": n}
    L = lambda v: {"type": "Lit", "value": v}
    Attr = lambda nd, k: {"type": "Attr", "node": nd, "key": k}
    Eq = lambda a, b: {"type": "Eq", "a": a, "b": b}
    Not = lambda x: {"type": "Not", "arg": x}
    return {
        "name": "mark_adopt_ready_" + tag,
        "match": [["exp", "has_delta", "delta"]],
        "where": {"type": "And", "items": [
            Eq(Attr(V("exp"), "outcome"), L("supported")),
            Not(Eq(Attr(V("exp"), "adopt_ready"), L(True))),
            Not(Eq(Attr(V("delta"), "act_rule_varied"), L(""))),
            Not(Eq(Attr(V("delta"), "act_rule_varied"), L(None))),
        ]},
        "effects": [["set_attr", "exp", "adopt_ready", True]],
    }


def _identity_corpus(a, n_turns=3):
    """Record `n_turns` identity turns; return their inbound ids."""
    turns = []
    for _ in range(n_turns):
        r = a.converse("What are you?", speech_act="question")
        assert (r or "").strip() == "I am Jabberwock."
        turns.append(a.last_turn_inbound_id())
    return turns


def _flag(a, turn_id, note):
    res = jd.flag_reply_turn(a, str(turn_id), note)
    assert res["ok"], res
    return res


# --- THE HEADLINE GATE ----------------------------------------------------------


def _replacement_identity_rule():
    """A real (non-error) replacement for reply_self_identity, so the variant's
    changed reply is a genuine change and not the adapter's error surface
    (tranche 4: the replay judge scores a change INTO the error surface as a
    broken fix). Same match/where as the shipped rule, different text."""
    from substrate.world_adapter import WorldAdapter as _WA  # noqa: F401
    V = lambda n: {"type": "Var", "name": n}
    L = lambda v: {"type": "Lit", "value": v}
    A = lambda n, k: {"type": "Attr", "node": V(n), "key": k}
    NotEq = lambda a, b: {"type": "Not", "arg": {"type": "Eq", "a": a, "b": b}}
    return {
        "name": "reply_self_identity_variant",
        "match": [["agent", "received", "m"], ["agent", "operates_in", "mt"]],
        "where": {"type": "And", "items": [
            {"type": "Eq", "a": A("m", "comp_dispatch_meta"), "b": L("self_identity")},
            NotEq(A("mt", "substrate_name"), L(None)),
            NotEq(A("m", "self_replied"), L(1.0)),
            NotEq(A("m", "attachment_pending"), L(1.0)),
            NotEq(A("m", "topic_pending"), L(1.0))]},
        "effects": [["set_attr", "m", "self_replied", 1.0],
                    ["add_node", "reply", "Message", {"from": "agent", "text": {"__term__": {
                        "type": "StringConcat", "parts": [L("My name is "), A("mt", "substrate_name"), L(".")]}}}],
                    ["add_edge", "reply", "responds_to", "m"], ["add_edge", "agent", "sent", "reply"]],
    }

def test_net_positive_but_regressing_variant_is_not_adopted(agent, tmp_path):
    # Corpus: three identity turns; flag 1+2, leave 3 unflagged. Ablating the
    # identity reply changes all three -> +2 (flagged fixed) − 1 (regression)
    # = net +1: judged supported, and EXACTLY the case that must not adopt.
    turns = _identity_corpus(agent, 3)
    _flag(agent, turns[0], "identity reply rule wrong: probe one")
    _flag(agent, turns[1], "identity reply rule wrong: probe two")

    exp = mint_experiment(agent, "net-positive-but-regressing ablation", "conversation",
                          remove_rules=["reply_self_identity"],
                          add_rules=[_replacement_identity_rule()])
    delta = _delta_of(agent, exp)
    # mark the delta a genuine ablation variant (what the authored composer
    # writes on the promote path — test authoring, same as mint_experiment)
    agent.s.set_attr(delta, "act_rule_varied", "reply_self_identity")
    agent.s.set_attr(delta, "ablation", 1.0)
    agent.inner.add_rule(_probe_judge_rule("safety_probe"))
    agent.inner.add_rule(_probe_adopt_rule("safety_probe"))

    status = _dispatch_until(agent, tmp_path / "runs", exp)
    assert status == "done", (status, agent.s.node(exp)["attrs"].get("error"))

    # the child's own accounting: net positive WITH a regression
    child = json.load(open(os.path.join(agent.s.node(exp)["attrs"]["run_dir"], "result.json")))
    assert child["flagged"] == 2 and child["flagged_changed"] == 2
    assert child["regressions"] == 1 and child["score"] == 1

    # ingest carried the accounting onto the graph (Run AND Experiment)
    run = next(r for r in agent.inner.neighbours(exp, "produced") if agent.s.has_node(r))
    ra = agent.s.node(run)["attrs"]
    assert ra.get("regressions") == 1 and ra.get("flagged") == 2 and ra.get("flagged_changed") == 2
    assert agent.s.node(exp)["attrs"].get("regressions") == 1

    # judge + adopt-candidate rules fire UNCHANGED (supported, adopt_ready) —
    # proving the safety gate is the veto, not a narrowed candidate rule —
    # and the standing seed rule vetoes in the same fixpoint.
    agent.comprehend()
    at = agent.s.node(exp)["attrs"]
    assert at.get("outcome") == "supported", at
    assert at.get("adopt_ready") is True
    assert at.get("adopt_denied") is True, \
        "adopt_denied_on_regression (seeds/adoption_safety.json) must veto regressions > 0"
    assert "regressions" in str(at.get("adopt_denied_reason") or "")

    # perform_adoptions honours the denial: nothing folds back into the parent
    rf.close_experiment_loop(agent)
    at = agent.s.node(exp)["attrs"]
    assert not at.get("adopted")
    assert not [n for n in agent.s.nodes("Adoption")
                if agent.s.node(n)["attrs"].get("rule_removed") == "reply_self_identity"]
    live = {r.get("name") for r in agent.inner.export_rules() if r.get("active")}
    assert "reply_self_identity" in live, "the parent's rule must survive the veto"
    r = agent.converse("What are you?", speech_act="question")
    assert (r or "").strip() == "I am Jabberwock.", "parent behaviour unchanged"

    # and the denial is READABLE over NL ('what are you working on?')
    state = rf.reflect("self_improvement_status", None, agent.inner)
    assert any(e.get("adopt_denied") and e.get("adopt_denied_reason")
               for e in state["experiments"])
    assert "blocked from adoption" in state["note"]
    ans = agent.answer_question("What are you working on?")
    assert "blocked from adoption" in (ans or "")


# --- POSITIVE CONTROL: zero regressions -> the veto stays silent -----------------

def test_zero_regression_variant_is_not_vetoed(agent, tmp_path):
    turns = _identity_corpus(agent, 2)
    _flag(agent, turns[0], "identity reply rule wrong: probe one")
    _flag(agent, turns[1], "identity reply rule wrong: probe two")

    exp = mint_experiment(agent, "clean ablation (all affected turns flagged)", "conversation",
                          remove_rules=["reply_self_identity"],
                          add_rules=[_replacement_identity_rule()])
    delta = _delta_of(agent, exp)
    agent.s.set_attr(delta, "act_rule_varied", "reply_self_identity")
    agent.s.set_attr(delta, "ablation", 1.0)
    agent.inner.add_rule(_probe_judge_rule("safety_ctl"))
    agent.inner.add_rule(_probe_adopt_rule("safety_ctl"))

    status = _dispatch_until(agent, tmp_path / "runs", exp)
    assert status == "done", (status, agent.s.node(exp)["attrs"].get("error"))
    child = json.load(open(os.path.join(agent.s.node(exp)["attrs"]["run_dir"], "result.json")))
    assert child["regressions"] == 0 and child["score"] == 2

    agent.comprehend()
    at = agent.s.node(exp)["attrs"]
    assert at.get("regressions") == 0, "the zero count is still carried (an honest 0, not absence)"
    assert at.get("outcome") == "supported" and at.get("adopt_ready") is True
    assert not at.get("adopt_denied"), "the veto must not fire on regressions == 0"
    # (the actual fold-back on the promote path is test_convo_experiment's +
    # the graduation gate's standing coverage; this control isolates the veto)


# --- SEED HYGIENE -----------------------------------------------------------------

def test_adoption_safety_seed_loads_and_round_trips(agent):
    # full boot holds the veto rule exactly once
    live = [r for r in agent.inner.export_rules()
            if r.get("active") and r.get("name") == "adopt_denied_on_regression"]
    assert len(live) == 1, "seeds/adoption_safety.json must load exactly once on a full boot"

    # the rule round-trips canonically (the _REFRESHABLE_SEEDS contract: an
    # unchanged rule is never churned by the resume refresh path)
    seed = json.load(open(os.path.join(ROOT, "seeds", "adoption_safety.json")))
    assert seed["id"] == "adoption_safety" and len(seed["rules"]) == 1
    file_canon = jd._canon_rule_body(seed["rules"][0])
    live_canon = jd._canon_rule_body(live[0])
    assert file_canon and file_canon == live_canon, \
        "adopt_denied_on_regression must round-trip byte-identically through the engine"
    assert "adoption_safety" in jd._REFRESHABLE_SEEDS, \
        "edit-the-seed/restart/it-applies must cover the safety rule"
