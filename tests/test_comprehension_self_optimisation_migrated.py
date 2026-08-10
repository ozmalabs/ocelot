"""SELF-OPTIMISATION gate: the jabberwock notices its own comprehension
process's deficiencies as ITS OWN gaps, and its experiment machinery gets an
EFFICIENCY objective so a promoted performance concern can run end-to-end.

Sense side (seeds/comprehension_health.json):
  - note_recurring_speech_act_divergence: >=3 Messages sharing the SAME
    (comp_kind, shadow_speech_act) pair -> one SelfConcern{kind:'comprehension'},
    filed once (content-deduped) even as more matching turns accumulate.
  - note_comprehension_latency_gap: the agent's own rolling
    shadow_latency_recent_avg (world_adapter._record_shadow_health) crossing
    the held HealthNorm{metric:'shadow_latency_ms'} ceiling -> one
    SelfConcern{kind:'performance'}; below the ceiling, none.

Lab side (seeds/self_optimisation.json + the mechanical plumbing in
scripts/convo_child_run.py / domains/experiment_dispatch.py):
  - a performance/comprehension-kind concern promotes into the SAME
    conversation experiment bundle a reply_fix concern gets
    (scripts/jabberwock_daemon.py._promote_relations_for_concern);
  - the dispatched conversation child now times its replay
    (scripts/convo_child_run.py) and reports avg_turn_ms, carried onto the
    Run + Experiment by domains/experiment_dispatch.py._ingest_result;
  - domains/experiment_dispatch.py._stamp_performance_baseline mechanically
    copies the agent's live shadow_latency_recent_avg onto the dispatched
    SeedDelta as baseline_avg_turn_ms + performance_objective, at dispatch
    time, ONLY for a performance/comprehension-driven Experiment;
  - seeds/self_optimisation.json's judge_performance_experiment_outcome
    OVERRIDES the generic score-sign verdict for any such Experiment:
    supported iff regressions==0 AND avg_turn_ms improved on the baseline;
  - note_experiments_exhausted leaves an honest trail (surfaced by
    reflective_faculty._run_self_improvement_status) when every dispatched
    trial for a concern reached a terminal verdict and none is adopt-ready.
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
from domains.experiment_dispatch import scan_and_dispatch, mint_experiment, _INFLIGHT  # noqa: E402

_CONCLUSIONS_SEED = os.path.join(ROOT, "seeds", "experiment_conclusions.json")


@pytest.fixture(autouse=True)
def _guard_conclusions_seed():
    """close_experiment_loop teach()es real verdicts into a checked-in seed —
    snapshot/restore it so gate runs leave no debris (the same guard
    test_convo_experiment_migrated.py applies)."""
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
    a = WorldAdapter(seeds=(), shadow_read=True)
    load_all_seeds(a)
    return a


def _self_concerns(a, kind=None):
    out = []
    for n in a.s.nodes("SelfConcern"):
        at = a.s.node(n)["attrs"]
        if kind is None or at.get("kind") == kind:
            out.append((n, at))
    return out


def _mk_divergent_message(a, i, text):
    """Directly craft a Message carrying the SAME mechanical facts
    world_adapter._write_comprehension_to_graph / _record_shadow_health write
    on a real divergent turn (comp_kind disagreeing with shadow_speech_act),
    to exercise the seed rule deterministically without depending on which
    real utterances happen to diverge on this build."""
    S, I = a.s, a.inner
    mid = S.add_node("Message", {"from": "interlocutor", "text": text,
                                 "comp_kind": "statement", "shadow_speech_act": "question",
                                 "speech_act_divergence": 1.0, "shadow_seq": float(i)})
    I.add_edge_unchecked(a.agent, "received", mid)
    return mid


def _delta_attrs(a, exp):
    for d in a.inner.neighbours(exp, "has_delta"):
        if a.s.has_node(d):
            return a.s.node(d)["attrs"]
    return {}


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


def _probe_judge_rule(tag: str) -> dict:
    """The SAME judge shape the composer authors (score-per-frame sign as a held
    IfThenElse), installed as graph data under a test-local tag — a hand-minted
    Experiment (mint_experiment) carries no author-composed judge rule of its
    own, so the generic 'analysed' edge my judge_performance_experiment_outcome
    rule's MATCH clause depends on (see seeds/self_optimisation.json's comment
    on why that edge must be a match clause, not a where-only Exists) never
    appears without one. Identical to test_convo_experiment_migrated.py's
    _probe_judge_rule."""
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


def _have_two_turns(a) -> int:
    r1 = a.converse("Hello.", speech_act="greeting")
    assert (r1 or "").strip()
    r2 = a.converse("What are you?", speech_act="question")
    assert (r2 or "").strip() == "I am Jabberwock."
    return a.last_turn_inbound_id()


# --- (a) recurring divergence -------------------------------------------------

def test_recurring_divergence_files_exactly_one_comprehension_concern(agent):
    a = agent
    assert not _self_concerns(a, "comprehension")
    for i, text in enumerate(["alpha one", "alpha two"], start=1):
        _mk_divergent_message(a, i, text)
    a.comprehend()
    assert not _self_concerns(a, "comprehension"), "two divergent turns is not yet recurrence"

    _mk_divergent_message(a, 3, "alpha three")
    a.comprehend()
    concerns = _self_concerns(a, "comprehension")
    assert len(concerns) == 1, concerns
    _, at = concerns[0]
    assert at["status"] == "noted" and at["source"] == "implicit"
    assert "statement" in at["content"] and "question" in at["content"]

    # a further matching turn must NOT mint a second concern (content dedup)
    _mk_divergent_message(a, 4, "alpha four")
    a.comprehend()
    assert len(_self_concerns(a, "comprehension")) == 1

    # a DIFFERENT pair gets its OWN concern
    S, I = a.s, a.inner
    for i, text in enumerate(["beta one", "beta two", "beta three"], start=10):
        mid = S.add_node("Message", {"from": "interlocutor", "text": text,
                                     "comp_kind": "instruction", "shadow_speech_act": "statement",
                                     "speech_act_divergence": 1.0, "shadow_seq": float(i)})
        I.add_edge_unchecked(a.agent, "received", mid)
    a.comprehend()
    assert len(_self_concerns(a, "comprehension")) == 2


# --- (b) latency norm ----------------------------------------------------------

def test_latency_above_norm_files_performance_concern_below_does_not(agent):
    a = agent
    S, I = a.s, a.inner
    mid = S.add_node("Message", {"from": "interlocutor", "text": "hi", "shadow_seq": 1.0})
    I.add_edge_unchecked(a.agent, "received", mid)

    I.set_attr(a.agent, "shadow_latency_recent_avg", 10.0)   # HealthNorm ceiling is 50.0
    a.comprehend()
    assert not _self_concerns(a, "performance")

    I.set_attr(a.agent, "shadow_latency_recent_avg", 75.0)
    a.comprehend()
    concerns = _self_concerns(a, "performance")
    assert len(concerns) == 1, concerns
    _, at = concerns[0]
    assert at["metric"] == "shadow_latency_ms"

    # still above ceiling later -> no second concern (content dedup)
    I.set_attr(a.agent, "shadow_latency_recent_avg", 80.0)
    a.comprehend()
    assert len(_self_concerns(a, "performance")) == 1


def test_shadow_read_maintains_rolling_latency_and_seq(agent):
    a = agent
    a.converse("Hello there.", speech_act="greeting")
    a.converse("What are you?", speech_act="question")
    at = a.s.node(a.agent)["attrs"]
    assert at.get("shadow_latency_recent_avg") is not None
    assert at.get("shadow_latency_recent_n") == 2.0
    seqs = sorted(a.s.node(m)["attrs"]["shadow_seq"] for m in a.s.nodes("Message")
                 if "shadow_seq" in a.s.node(m)["attrs"])
    assert seqs == [1.0, 2.0]


# --- (c) the efficiency objective end-to-end -----------------------------------

def test_performance_experiment_supported_when_faster_and_clean(agent, tmp_path):
    a = agent
    _have_two_turns(a)
    exp = mint_experiment(a, "efficiency probe: no-op delta, generous baseline", "conversation")
    a.inner.add_rule(_probe_judge_rule("perf_supported_probe"))
    da = _delta_attrs(a, exp)
    # Mimic what _stamp_performance_baseline writes at dispatch time (a
    # generous/high baseline so ANY real replay wall-time reads as an
    # improvement) — deterministic without depending on absolute wall-clock.
    for d in a.inner.neighbours(exp, "has_delta"):
        if a.s.has_node(d):
            a.inner.set_attr(d, "performance_objective", 1.0)
            a.inner.set_attr(d, "baseline_avg_turn_ms", 10_000.0)
    status = _dispatch_until(a, tmp_path / "runs", exp)
    assert status == "done", (status, a.s.node(exp)["attrs"].get("error"))
    a.comprehend()
    at = a.s.node(exp)["attrs"]
    assert at.get("avg_turn_ms") is not None and at["avg_turn_ms"] < 10_000.0
    assert int(at.get("regressions") or 0) == 0
    assert at.get("performance_judged") is True
    assert at.get("outcome") == "supported", at


def test_performance_experiment_refuted_when_slower_even_with_no_regressions(agent, tmp_path):
    a = agent
    _have_two_turns(a)
    exp = mint_experiment(a, "efficiency probe: no-op delta, impossible baseline", "conversation")
    a.inner.add_rule(_probe_judge_rule("perf_refuted_slow_probe"))
    for d in a.inner.neighbours(exp, "has_delta"):
        if a.s.has_node(d):
            a.inner.set_attr(d, "performance_objective", 1.0)
            a.inner.set_attr(d, "baseline_avg_turn_ms", 0.000001)   # unbeatable
    status = _dispatch_until(a, tmp_path / "runs", exp)
    assert status == "done", (status, a.s.node(exp)["attrs"].get("error"))
    a.comprehend()
    at = a.s.node(exp)["attrs"]
    assert int(at.get("regressions") or 0) == 0
    assert at.get("outcome") in ("refuted", "inconclusive"), at
    assert at.get("outcome") != "supported"


def test_performance_experiment_refuted_on_regression_regardless_of_speed(agent, tmp_path):
    a = agent
    _have_two_turns(a)
    # ablate the adjacency-pair reply -> breaks the unflagged greeting turn
    # (the SAME regression fixture test_convo_experiment_migrated uses).
    exp = mint_experiment(a, "efficiency probe: breaking delta, generous baseline", "conversation",
                          remove_rules=["reply_to_adjacency_pair"])
    a.inner.add_rule(_probe_judge_rule("perf_refuted_regress_probe"))
    for d in a.inner.neighbours(exp, "has_delta"):
        if a.s.has_node(d):
            a.inner.set_attr(d, "performance_objective", 1.0)
            a.inner.set_attr(d, "baseline_avg_turn_ms", 10_000.0)   # trivially "faster"
    status = _dispatch_until(a, tmp_path / "runs", exp)
    assert status == "done", (status, a.s.node(exp)["attrs"].get("error"))
    a.comprehend()
    at = a.s.node(exp)["attrs"]
    assert int(at.get("regressions") or 0) >= 1
    assert at.get("performance_judged") is True
    assert at.get("outcome") == "refuted", \
        "a regression must refute even though avg_turn_ms beat the (generous) baseline"


def test_promoted_performance_concern_reaches_a_dispatched_experiment(agent, tmp_path):
    """The end-to-end sense->lab wiring: a filed 'performance' SelfConcern,
    promoted over the SAME human-gated pipeline a reply_fix concern uses,
    reaches a conversation Experiment with a performance_objective delta."""
    a = agent
    _have_two_turns(a)
    S, I = a.s, a.inner
    I.set_attr(a.agent, "shadow_latency_recent_avg", 999.0)
    sc = S.add_node("SelfConcern", {"status": "noted", "source": "implicit", "kind": "performance",
                                    "content": "shadow-read comprehension latency (rolling average) exceeds its held ceiling",
                                    "metric": "shadow_latency_ms"})
    I.add_edge_unchecked(a.agent, "has_self_concern", sc)

    p = jd.promote_self_concern(a, str(int(sc.value)))
    assert p["ok"] and p["pipeline"] == "experiment", p
    heads = {r[0] for r in (a.s.node(srs_node(p["standing_concern"]))["attrs"].get("relations") or [])}
    assert {"test", "replay", "send", "judge", "adopt"} <= heads

    jd._concern_tick(a)
    exps = [n for n in S.nodes("Experiment") if S.node(n)["attrs"].get("game") == "conversation"]
    assert len(exps) == 1, exps
    exp = exps[0]
    assert S.node(exp)["attrs"].get("axis_tag") == f"promoted_self_concern_{int(sc.value)}"

    status = _dispatch_until(a, tmp_path / "runs", exp)
    assert status == "done", (status, S.node(exp)["attrs"].get("error"))
    da = _delta_attrs(a, exp)
    assert da.get("performance_objective") == 1.0, da
    assert da.get("baseline_avg_turn_ms") == 999.0, da

    a.comprehend()
    at = S.node(exp)["attrs"]
    assert at.get("avg_turn_ms") is not None
    assert at.get("performance_judged") is True
    assert at.get("outcome") in ("supported", "refuted", "inconclusive")


def srs_node(int_id):
    import substrate_rs as srs
    return srs.NodeID(int(int_id))


# --- (d) the exhausted trail is readable ----------------------------------------

def test_exhausted_experiments_trail_surfaces_in_status(agent, tmp_path):
    a = agent
    _have_two_turns(a)
    S, I = a.s, a.inner
    I.set_attr(a.agent, "shadow_latency_recent_avg", 999.0)
    # Content matching what note_comprehension_latency_gap actually files: its
    # words don't overlap any acting-rule's provenance keywords, so the
    # reply-ablation variation pick (seeds/variation_ops.json) abstains (empty
    # delta) -- the concern can never become adopt-ready, which is exactly the
    # 'exhausted' case this rule is for.
    sc = S.add_node("SelfConcern", {"status": "noted", "source": "implicit", "kind": "performance",
                                    "content": "shadow-read comprehension latency (rolling average) exceeds its held ceiling",
                                    "metric": "shadow_latency_ms"})
    I.add_edge_unchecked(a.agent, "has_self_concern", sc)
    p = jd.promote_self_concern(a, str(int(sc.value)))
    assert p["ok"]
    jd._concern_tick(a)
    exps = [n for n in S.nodes("Experiment") if S.node(n)["attrs"].get("game") == "conversation"]
    assert len(exps) == 1
    exp = exps[0]
    status = _dispatch_until(a, tmp_path / "runs", exp)
    assert status == "done"
    a.comprehend()
    rf.close_experiment_loop(a)

    standing = None
    tag = S.node(exp)["attrs"].get("axis_tag")
    for n in S.nodes("StandingConcern"):
        if S.node(n)["attrs"].get("name") == tag:
            standing = n
    assert standing is not None
    sat = S.node(standing)["attrs"]
    # this concern's content shares no acting-rule provenance keywords, so the
    # reply-ablation variation family abstains (empty delta) -> never adopt-ready.
    assert sat.get("adopt_ready") in (None, False, "")
    assert sat.get("experiments_exhausted") is True
    assert sat.get("exhausted_note")

    result = rf._run_self_improvement_status(a.s)
    assert "experiments exhausted" in result["note"]


# --- (e) seed hygiene ------------------------------------------------------------

def test_new_seeds_canon_round_trip_and_reconcile_churn_free():
    for fname in ("comprehension_health.json", "self_optimisation.json"):
        d = json.load(open(os.path.join(ROOT, "seeds", fname)))
        for r in d["rules"]:
            body = {k: v for k, v in r.items() if k != "active"}
            c1 = jd._canon_rule_body(body)
            c2 = jd._canon_rule_body(json.loads(json.dumps(body)))
            assert c1 and c1 == c2, (fname, r["name"])

    a = WorldAdapter()
    def _health_norms():
        return [a.s.node(n)["attrs"].get("metric") for n in a.s.nodes("HealthNorm")]
    assert "shadow_latency_ms" not in _health_norms()
    added = jd._reconcile_seed_typed_nodes(a, "HealthNorm", "metric")
    assert added > 0
    assert _health_norms().count("shadow_latency_ms") == 1
    assert jd._reconcile_seed_typed_nodes(a, "HealthNorm", "metric") == 0

    n1 = jd._reconcile_seed_rules(a)
    assert n1 > 0
    n2 = jd._reconcile_seed_rules(a)
    assert n2 == 0, "a second reconcile pass on an already-reconciled graph must install/refresh nothing"
