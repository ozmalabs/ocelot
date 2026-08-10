"""test_aperture_escalation_migrated — FOVEATION-AS-HINT (2026-07-11): the
reading aperture (`stages`/`max_sentences`/`window`, threaded off a winning
`ShapeSignatureRegister` — seeds/register_source.json — by
`register_source.route_reading`/`reading_drive.run_reading_flow`) is a HINT,
never fixed. Today the `conversational` register runs spine-only over <=3
sentences and STOPS regardless of what the read encountered; this gate
covers the RESIDUAL-DRIVEN ESCALATION layer over it (seeds/reading_
aperture.json): three graph rules that read signals the read's OWN output
already produced (a truncation datum, a heavy fallback-parse ratio, a
narrative shape under a light hint) and, within a held per-register
`ApertureBudget` belief, mint ADDITIONAL `AnalysisStage` nodes for the SAME
flow — the existing `la_dispatch_*` machinery (unchanged) runs them.

No new Python decision anywhere: `_shim_spine` (domains/reading_drive.py)
only mechanically records `sentences_total`/`sentences_read` and reads a
graph-set `max_sentences_override`; the escalate_* rules ARE the decision.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                              # noqa: E402
from substrate.world_adapter import WorldAdapter                       # noqa: E402
from substrate.boot_all import load_all_seeds                          # noqa: E402
from domains import dictionary_lexicon as dl                           # noqa: E402
from domains import reading_drive as rd                                # noqa: E402
from domains import register_source as rs                              # noqa: E402
from domains import narrative_structure as ns                          # noqa: E402
from domains.reflective_faculty import _ensure_seed_chain              # noqa: E402

jd = pytest.importorskip("jabberwock_daemon")

# jpafg carries the thirsty-crow fable used elsewhere in the migrated bench
# (6 sentences, no dialogue, known clean under this reader).
import jabberwock_produces_analysis_from_goal as jpafg                 # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


def _agent(s, node):
    return type("A", (), {"s": s, "inner": s._inner, "agent": node})()


def _fresh_agent():
    s, node = boot_core()
    return _agent(s, node)


def _stages(s):
    return [(s.node(n)["attrs"].get("name"), s.node(n)["attrs"].get("status"),
             s.node(n)["attrs"].get("escalated"), s.node(n)["attrs"].get("escalation_reason"))
            for n in s.nodes("AnalysisStage")]


def _escalated_stages(s):
    return [row for row in _stages(s) if row[2]]


def _conversational_run(agent, text, *, max_sentences=None, register="conversational",
                        stages=("spine",)):
    ap = rs.conversational_aperture(agent) if register == "conversational" else {}
    ms = max_sentences if max_sentences is not None else (ap.get("max_sentences") or 3)
    return rd.run_reading_flow(
        agent, text, report="comprehend",
        stages=list(stages) if stages is not None else ap.get("stages"),
        max_sentences=ms, window=ap.get("window") or 1, register=register)


def _budget_node(s, register):
    for n in s.nodes("ApertureBudget"):
        if s.node(n)["attrs"].get("register") == register:
            return n
    return None


# --------------------------------------------------------------------------- #
#  Fixture texts.
# --------------------------------------------------------------------------- #
CLEAN_2 = "Hello there. How are you today?"
CLEAN_3 = "The weather is nice today. I went to the store. We bought some bread."
FRAGMENTS_6 = "Hello. Yes. Wow. Okay. Great. Sure."
FRAGMENTS_8 = "Hello. Yes. Wow. Okay. Great. Sure. Fine. Nice."
NARRATIVE_3 = ("A fox saw a crow perched in a tree. The crow was holding a piece of "
              "cheese in its beak. The fox wanted the cheese very much and began to "
              "think of a plan.")


# --------------------------------------------------------------------------- #
#  1. A CLEAN, SHORT chat turn escalates ZERO times.
# --------------------------------------------------------------------------- #
def test_clean_short_turn_zero_escalations():
    agent = _fresh_agent()
    _conversational_run(agent, CLEAN_2)
    assert _escalated_stages(agent.s) == []
    assert len(agent.s.nodes("AnalysisStage")) == 1   # spine only, no widening

    agent2 = _fresh_agent()
    _conversational_run(agent2, CLEAN_3)
    assert _escalated_stages(agent2.s) == []


def test_shadow_latency_battery_unaffected():
    """Re-run of test_shadow_read_migrated's own steady-state latency gate —
    a clean turn must never pay for an escalation, so the shadow-read
    latency battery (which this wave's `register='conversational'` threading
    now touches) stays bounded exactly as before."""
    a = WorldAdapter(seeds=(), shadow_read=True)
    load_all_seeds(a)
    a.converse("What do you know about the moon?", speech_act="question")
    latencies = []
    for i in range(6):
        a.converse("Tell me a fact about topic number %d." % i, speech_act="statement")
        mid = a._last_turn_inbound
        latencies.append(a.s.node(mid)["attrs"].get("shadow_latency_ms"))
    med = sorted(latencies)[len(latencies) // 2]
    assert med < 1000.0, "steady-state shadow-read latency pathological: %.1fms median" % med
    # none of these plain statements should have tripped an escalation rule
    for mid_n in a.s.nodes("Message"):
        pass  # escalated AnalysisStage nodes are flow-scoped, not Message-scoped;
              # the real proof is the stage census below.
    escalated = [row for row in _stages(a.s) if row[2]]
    assert escalated == [], "a clean shadow-read battery must escalate zero times: %r" % (escalated,)


# --------------------------------------------------------------------------- #
#  2. A TRUNCATED document read escalates once and reads the FULL text.
# --------------------------------------------------------------------------- #
def test_truncated_document_read_escalates_once_and_reads_full_text():
    agent = _fresh_agent()
    bb = rd.comprehension_result(agent, jpafg.CROW, max_sentences=2, register="default")
    src = agent.s.nodes("Source")[0]
    at = agent.s.node(src)["attrs"]
    assert at["sentences_total"] == 6.0
    assert at["sentences_read"] == 6.0, "escalation must widen the read to the FULL text"
    assert at["max_sentences_override"] == 6.0

    escalated = _escalated_stages(agent.s)
    assert len(escalated) == 1
    assert escalated[0][0] == "spine" and escalated[0][3] == "truncated_read"

    # HeldAnswers/salience read off the SITUATION MODEL (spine's own output),
    # which in turn is read off the durable SentenceParse ledger the widened
    # spine re-mints — the flow must now hold a SentenceParse for EVERY
    # sentence (not just the original truncated cap of 2), the mechanical
    # proof the re-collapse covered the LATE sentences too (sentence 5 of 6,
    # "Picking up some small pebbles...", was unreachable at the old cap).
    flow = bb.get("flow")
    sp_rows = [n for n in agent.s.nodes("SentenceParse")
              if agent.s.node(n)["attrs"].get("flow") == flow]
    assert len(sp_rows) == 6, (
        "widened spine must re-mint a SentenceParse for every sentence: %r" % sp_rows)
    last_sentence = [agent.s.node(n)["attrs"].get("sentence") for n in sp_rows
                     if agent.s.node(n)["attrs"].get("order") == 5]
    assert last_sentence and "pebble" in last_sentence[0]


def test_budget_exhausted_blocks_a_second_simultaneous_escalation():
    """Two conditions true at once (truncated AND fallback-heavy) under the
    tight `conversational` budget (max_escalations=1): only ONE escalation
    type fires; the flow's own Source/Goal still carry the honest datum of
    what happened (no further escalation silently retried)."""
    agent = _fresh_agent()
    _conversational_run(agent, FRAGMENTS_8, max_sentences=3)
    escalated = _escalated_stages(agent.s)
    assert len(escalated) == 1, "budget=1 must cap the flow at ONE escalation event: %r" % (escalated,)
    src = agent.s.nodes("Source")[0]
    at = agent.s.node(src)["attrs"]
    # an honest datum either way: sentences_total/read are always stamped,
    # regardless of which escalation (if either) actually fired.
    assert at["sentences_total"] == 8.0
    assert at["sentences_read"] in (3.0, 8.0)


# --------------------------------------------------------------------------- #
#  3. A NARRATIVE text under the conversational hint escalates to narrative
#     depth and gets the SAME protagonist as a direct narrative-register read.
# --------------------------------------------------------------------------- #
def test_narrative_shape_escalates_and_matches_direct_register():
    escalated_agent = _fresh_agent()
    _conversational_run(escalated_agent, NARRATIVE_3, max_sentences=3)
    escalated = _escalated_stages(escalated_agent.s)
    assert len(escalated) == 9, "the full remaining comprehension depth must be minted: %r" % (escalated,)
    assert {row[0] for row in escalated} == {
        "infer_goal", "discourse", "infer_causal", "enabling", "centrality",
        "monitoring", "tom", "narrative", "trope"}
    assert all(row[3] == "narrative_shape" for row in escalated)
    src = escalated_agent.s.nodes("Source")[0]
    # no truncation here (3 sentences read == 3 sentences total) — this
    # escalation is REGISTER-shape driven, not truncation driven.
    at = escalated_agent.s.node(src)["attrs"]
    assert at["sentences_total"] == at["sentences_read"] == 3.0

    escalated_verdict = ns.protagonist_by_arc_agency(escalated_agent)

    direct_agent = _fresh_agent()
    rd.run_reading_flow(direct_agent, NARRATIVE_3, report="comprehend", register="narrative")
    direct_verdict = ns.protagonist_by_arc_agency(direct_agent)

    assert escalated_verdict.get("protagonist") == direct_verdict.get("protagonist") == "fox"


def test_narrative_shape_does_not_fire_within_the_visible_window_alone():
    """The thirsty-crow fable's first 3 sentences have 2 animate entities
    (Birds, Crow) but NO explicit want/goal SmEvent (it never says
    'wanted') — narrative_shape must not fire on that signal alone (only
    truncated_read, covered above, escalates it)."""
    agent = _fresh_agent()
    _conversational_run(agent, jpafg.CROW, max_sentences=3)
    reasons = {row[3] for row in _escalated_stages(agent.s)}
    assert "narrative_shape" not in reasons


# --------------------------------------------------------------------------- #
#  4. Unparsed-clauses escalation fires on garbage-heavy text, not clean text.
# --------------------------------------------------------------------------- #
def test_unparsed_clauses_fires_on_fragments_not_on_clean_text():
    garbage_agent = _fresh_agent()
    _conversational_run(garbage_agent, FRAGMENTS_6, max_sentences=6)
    escalated = _escalated_stages(garbage_agent.s)
    reasons = {row[3] for row in escalated}
    assert "unparsed_clauses" in reasons
    names = {row[0] for row in escalated if row[3] == "unparsed_clauses"}
    assert names == {"discourse", "monitoring"}

    clean_agent = _fresh_agent()
    _conversational_run(clean_agent, CLEAN_3, max_sentences=3)
    assert _escalated_stages(clean_agent.s) == []

    declarative_agent = _fresh_agent()
    _conversational_run(declarative_agent, "The weather is nice today. I went to the "
                        "store. We bought some bread.", max_sentences=3)
    assert _escalated_stages(declarative_agent.s) == []


# --------------------------------------------------------------------------- #
#  5. The budget is a HELD BELIEF — editing the node changes behaviour with
#     ZERO code change.
# --------------------------------------------------------------------------- #
def test_budget_node_edit_to_zero_blocks_all_escalation():
    agent = _fresh_agent()
    _ensure_seed_chain(agent.s, agent.inner, agent.agent,
                       ("literary_analysis_driving", "reading_aperture"))
    budget = _budget_node(agent.s, "conversational")
    assert budget is not None
    agent.s.set_attr(budget, "max_escalations", 0.0)
    _conversational_run(agent, FRAGMENTS_8, max_sentences=3)
    assert _escalated_stages(agent.s) == [], "max_escalations=0 must block every escalate_* rule"
    src = agent.s.nodes("Source")[0]
    at = agent.s.node(src)["attrs"]
    assert at["sentences_read"] == 3.0 and at["sentences_total"] == 8.0, (
        "the truncation datum stays honest even when the budget forbids acting on it")


def test_budget_node_max_stage_count_gates_the_deep_escalation():
    """`max_stage_count` is the SECOND independent lever (task 3): lowering
    it below what escalate_narrative_shape needs (1 initial spine + 9 more)
    blocks JUST that rule with zero code change, while the SAME text at the
    default (generous) ceiling escalates to full narrative depth."""
    blocked_agent = _fresh_agent()
    _ensure_seed_chain(blocked_agent.s, blocked_agent.inner, blocked_agent.agent,
                       ("literary_analysis_driving", "reading_aperture"))
    budget = _budget_node(blocked_agent.s, "conversational")
    blocked_agent.s.set_attr(budget, "max_stage_count", 5.0)
    _conversational_run(blocked_agent, NARRATIVE_3, max_sentences=3)
    assert _escalated_stages(blocked_agent.s) == [], (
        "max_stage_count=5 must block a 9-stage narrative_shape escalation")

    default_agent = _fresh_agent()
    _conversational_run(default_agent, NARRATIVE_3, max_sentences=3)
    assert len(_escalated_stages(default_agent.s)) == 9, (
        "the SAME text at the default (unedited) budget must still escalate to full depth")


# --------------------------------------------------------------------------- #
#  6. Seed hygiene — canon round-trip, churn-free reconcile, ApertureBudget
#     node reconciliation on resume.
# --------------------------------------------------------------------------- #
def test_seed_canon_round_trip_and_reconcile_churn_free():
    d = json.load(open(os.path.join(ROOT, "seeds", "reading_aperture.json")))
    for r in d["rules"]:
        body = {k: v for k, v in r.items() if k != "active"}
        c1 = jd._canon_rule_body(body)
        c2 = jd._canon_rule_body(json.loads(json.dumps(body)))
        assert c1 and c1 == c2, r["name"]

    assert "reading_aperture" in jd._REFRESHABLE_SEEDS

    a = WorldAdapter()

    def _budget_registers():
        return [a.s.node(n)["attrs"].get("register") for n in a.s.nodes("ApertureBudget")]

    assert "conversational" not in _budget_registers()
    added = jd._reconcile_seed_typed_nodes(a, "ApertureBudget", "register")
    assert added > 0
    assert _budget_registers().count("conversational") == 1
    assert jd._reconcile_seed_typed_nodes(a, "ApertureBudget", "register") == 0

    n1 = jd._reconcile_seed_rules(a)
    assert n1 > 0
    n2 = jd._reconcile_seed_rules(a)
    assert n2 == 0, "a second reconcile pass on an already-reconciled graph must install/refresh nothing"


# --------------------------------------------------------------------------- #
#  7. Live daemon-shaped smoke: a casual pasted text escalates and answers a
#     "what do you know about X" question from the arc it read.
# --------------------------------------------------------------------------- #
def _run_live_daemon_smoke():
    """Exercises the SAME machinery a daemon would: a WorldAdapter, a light-
    aperture read of a pasted casual narrative (forced narrow to demonstrate
    the escalation this wave adds — a full `route_reading` document upload
    already reads at max_sentences=10_000 and would never truncate), then
    the EXISTING HeldAnswer bridge (`_mint_document_held_answers`, already
    used by `_deep_read_document` for real uploads) renders the flow's
    salient content queryable, then a real `converse()` turn answers from
    it. Returns (reply, source_attrs) for the transcript report."""
    a = WorldAdapter(seeds=(), shadow_read=True, deep_ingest=True)
    load_all_seeds(a)
    text = jpafg.CROW  # the thirsty-crow fable, pasted as a casual .txt
    route = rs.route_reading(a, text, hint="casual", max_sentences=2)
    assert route.get("flow") is not None
    src = None
    for n in a.s.nodes("Source"):
        if a.s.node(n)["attrs"].get("flow") == route["flow"]:
            src = n
    assert src is not None
    at = a.s.node(src)["attrs"]
    a._mint_document_held_answers("smoke_doc", route["flow"])
    reply = a.converse("What do you know about the crow?", speech_act="question")
    return reply, dict(at)


def test_live_daemon_smoke_casual_paste_escalates_and_answers():
    reply, at = _run_live_daemon_smoke()
    assert at["sentences_read"] == at["sentences_total"] == 6.0, (
        "the casual paste must have escalated past its forced max_sentences=2 cap")
    assert isinstance(reply, str) and reply.strip()


if __name__ == "__main__":
    reply, src_attrs = _run_live_daemon_smoke()
    print("Source attrs after escalation:", src_attrs)
    print("converse() reply:", reply)
