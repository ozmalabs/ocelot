"""Wave 2 -- NL STEERING of the gap pipeline + pipeline introspection + autonomy
narration. Graph-native throughout: every DECISION is a seed rule; the daemon
hooks only execute what the rules marked and the readers only read.

  * STEERING (seeds/conversation_steering.json): 'Work on the <content> gap.'
    -- the rule steer_promote_concern resolves WHICH noted SelfConcern the turn
    names by content-word overlap (a non-stopword Mention occurring inside the
    concern's content), marks it promote_requested=1.0, claims the turn
    (comprehended=1.0, so no spurious instruction gap files) and mints the
    confirming reply. The HUMAN GATE is preserved: only an interlocutor turn
    can mark, and the daemon hook (_steer_tick) merely executes the EXISTING
    human-gated promote_self_concern on what the rule marked.
  * 'Drop the <content> gap.' -- steer_retire_concern mirrors gap_awareness's
    retire_duplicate_gap effects (status='retired' + del_edge has_self_concern).
  * AMBIGUITY FLOOR: a steering verb + gap-noun with NO overlapping noted
    concern -> steer_clarify_no_match replies honestly and mints NOTHING.
  * INTROSPECTION (reflective_faculty): _run_self_improvement_status reads
    StandingConcern + Experiment nodes; _run_adoptions reads Adoption records;
    both are routed from NL via seeds/question_targets.json meta-target
    entries ('what are you working on' / 'what have you changed about
    yourself'), with the existing self_gaps routing untouched (parity).
  * NARRATION (jabberwock_daemon._narrate_tick): a concluded pipeline
    transition becomes ONE agent-initiated chat turn per monitor pass; the
    narrated=1.0 marker lives ON THE NODE so idempotence survives restart.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

jd = pytest.importorskip("jabberwock_daemon")


@pytest.fixture(scope="module")
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _concerns(a, **want):
    out = []
    for sc in a.s.nodes("SelfConcern"):
        if not a.s.has_node(sc):
            continue
        at = a.s.node(sc)["attrs"]
        if all(at.get(k) == v for k, v in want.items()):
            out.append((sc, at))
    return out


def _standing(a):
    return [n for n in a.s.nodes("StandingConcern")
            if a.s.node(n)["attrs"].get("source") == "conversation_promoted"]


# --- (a) file a gap, then steer it to promotion over NL ----------------------

def test_steer_promote_marks_the_named_concern(agent):
    # File a gap through the existing unhandled-instruction path.
    r0 = agent.converse("Summarise the report.", speech_act="request")
    assert "filed it as a gap" in r0.lower()
    noted = _concerns(agent, status="noted", content="summarise report")
    assert len(noted) == 1, "precondition: the gap is on file"

    n_gaps_before = len(list(agent.s.nodes("SelfConcern")))
    reply = agent.converse("Work on the summarise report gap.", speech_act="request")

    # The rule decided WHICH concern the turn names and marked it.
    sc, at = _concerns(agent, content="summarise report")[0]
    assert at.get("promote_requested") == 1.0, (
        "steer_promote_concern must mark the overlapping noted concern")
    assert at.get("status") == "noted", "marking is not promotion — the hook promotes"
    # Confirming reply, same turn.
    assert reply and reply.lower().startswith("promoting:") and "summarise report" in reply
    # The steering turn was CLAIMED (comprehended) -> no spurious instruction gap.
    mid = agent._last_turn_inbound
    assert agent.s.node(mid)["attrs"].get("comprehended") == 1.0
    assert len(list(agent.s.nodes("SelfConcern"))) == n_gaps_before, (
        "a steering turn must not file a new SelfConcern")
    # Nothing auto-promoted: the human-gated hook has not run yet.
    assert not _standing(agent)


def test_focus_gap_imperative_routes_by_held_graph_verb_and_preserves_human_gate():
    # The legacy parse snapshot tagged sentence-initial `Focus` as a noun.
    # With an explicit gap noun, the graph path must recognize the held
    # steering route from typed Mention/Concept evidence, not a Python list.
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    concern = agent.s.add_node("SelfConcern", {
        "source": "implicit", "kind": "instruction", "status": "noted",
        "content": "reading work", "promote_requested": 0.0,
    })
    agent.inner.add_edge_unchecked(agent.agent, "has_self_concern", concern)

    reply = agent.converse("Focus on the reading work gap.", speech_act="request")

    attrs = agent.s.node(concern)["attrs"]
    assert attrs.get("promote_requested") == 1.0
    assert attrs.get("status") == "noted", "graph routing must not bypass human promotion"
    assert reply and reply.lower().startswith("promoting:")
    trace = agent.reply_turn_trace(agent.last_turn_inbound_id())
    release = trace["production_release"]
    assert release["parse_back_mode"] == "conversation_instruction_graph"
    assert release["semantic_event"] == "promote"


# --- (b) the hook EXECUTES what the rule marked (human gate preserved) -------

def test_steer_tick_promotes_marked_concern_to_standing(agent):
    before = len(_standing(agent))
    promoted = jd._steer_tick(agent)
    assert len(promoted) == 1 and promoted[0]["ok"]
    after = _standing(agent)
    assert len(after) == before + 1, (
        "_steer_tick must execute the EXISTING promote_self_concern -> "
        "StandingConcern{pending}")
    st = agent.s.node(after[-1])["attrs"]
    assert st.get("status") == "pending" and "summarise report" in str(st.get("about"))
    # the concern flipped noted -> promoted, so the hook never re-fires on it
    sc, at = _concerns(agent, content="summarise report")[0]
    assert at.get("status") == "promoted"
    assert jd._steer_tick(agent) == [], "idempotent: nothing left to promote"


# --- (c) retire over NL -------------------------------------------------------

def test_steer_retire_retires_the_named_concern(agent):
    r0 = agent.converse("Transmogrify the data.", speech_act="request")
    assert "filed it as a gap" in r0.lower()
    (sc, at), = _concerns(agent, status="noted", content="transmogrify data")

    reply = agent.converse("Drop the transmogrify data gap.", speech_act="request")
    assert reply and reply.lower().startswith("retiring:") and "transmogrify data" in reply
    at2 = agent.s.node(sc)["attrs"]
    assert at2.get("status") == "retired", "steer_retire_concern must retire it"
    assert sc not in list(agent.inner.neighbours(agent.agent, "has_self_concern")), (
        "the has_self_concern edge is deleted (the retire_duplicate_gap contract)")
    # a retired concern is invisible to the steering hook
    assert jd._steer_tick(agent) == []


# --- (d) ambiguity floor: no matching concern -> clarify, mint nothing --------

def test_steering_verb_with_no_match_clarifies_and_mints_nothing(agent):
    # The first live turn may file the separately established implicit
    # boot-integrity concern from BootSeedAnomaly evidence. The ambiguity floor
    # must not add a concern for this request; keep that unrelated baseline out
    # of the request-effect assertion.
    def request_concerns():
        return [node for node in agent.s.nodes("SelfConcern")
                if agent.s.node(node)["attrs"].get("kind") != "boot_integrity"]

    n_sc = len(request_concerns())
    n_st = len(list(agent.s.nodes("StandingConcern")))
    reply = agent.converse("Pursue the flurble gap.", speech_act="request")
    assert reply and "couldn't tell which gap" in reply.lower(), (
        "the clarify floor must name that it couldn't identify the gap")
    assert len(request_concerns()) == n_sc, "no request concern minted"
    assert len(list(agent.s.nodes("StandingConcern"))) == n_st, "nothing promoted"
    assert not [1 for _sc, at in _concerns(agent)
                if at.get("promote_requested") == 1.0 and at.get("status") == "noted"], (
        "no concern was marked for promotion")
    mid = agent._last_turn_inbound
    # the clarify CLAIMED the turn -> instruction outcome 'handled', no gap files
    assert agent.s.node(mid)["attrs"].get("comprehended") == 1.0
    assert not _concerns(agent, kind="instruction", content="pursue flurble gap")


# --- (e) pipeline introspection readers + NL routing ---------------------------

def test_self_improvement_status_reads_standing_and_experiments(agent):
    from domains import reflective_faculty as rf
    # the REAL pipeline state from (b) is visible
    state = rf.reflect("self_improvement_status", None, agent.inner)
    assert "unwired" not in state
    assert any("summarise report" in c["about"] for c in state["standing"])
    assert "summarise report" in state["note"]

    # fixture experiment nodes are read mechanically, with outcome
    agent.s.add_node("Experiment", {"status": "done", "outcome": "supported",
                                    "hypothesis": "skip rule X helps"})
    state = rf.reflect("self_improvement_status", None, agent.inner)
    assert any(e["status"] == "done" and e["outcome"] == "supported"
               for e in state["experiments"])
    assert "skip rule X helps" in state["note"] and "supported" in state["note"]

    # NL routes to it (the question_targets meta lexicon)
    from domains import comprehend_text as ct
    for q in ("What are you working on?", "What are you improving?",
              "What experiments are you running?"):
        comp = ct.comprehend_text(agent, q)
        d = comp.dispatch or {}
        spec = d.get("spec")
        mt = getattr(spec, "meta_target", None) if spec is not None else d.get("meta_target")
        assert mt == "self_improvement_status", f"{q!r} must route to the status reader"
    # end-to-end through the same reflect()/surface path answer_question uses
    ans = agent.answer_question("What are you working on?")
    assert "summarise report" in ans


def test_self_adoptions_reads_adoption_records(agent):
    from domains import reflective_faculty as rf
    state = rf.reflect("self_adoptions", None, agent.inner)
    assert "unwired" not in state
    assert state["count"] == 0 and "haven't adopted" in state["note"]

    agent.s.add_node("Adoption", {"rule_removed": "hop_descend_gradient",
                                  "rule_added": "hop_descend_gradient_v2",
                                  "experiment_id": "77", "tick": 1.0})
    state = rf.reflect("self_adoptions", None, agent.inner)
    assert state["count"] == 1
    assert "hop_descend_gradient" in state["note"] and "77" in state["note"]

    from domains import comprehend_text as ct
    for q in ("What have you changed about yourself?", "What have you adopted?",
              "What did you improve?"):
        comp = ct.comprehend_text(agent, q)
        d = comp.dispatch or {}
        spec = d.get("spec")
        mt = getattr(spec, "meta_target", None) if spec is not None else d.get("meta_target")
        assert mt == "self_adoptions", f"{q!r} must route to the adoptions reader"
    ans = agent.answer_question("What have you changed about yourself?")
    assert "hop_descend_gradient" in ans


# --- (f) parity: existing routes undisturbed -----------------------------------

def test_existing_question_routes_unchanged(agent):
    from domains import comprehend_text as ct

    def route(q):
        comp = ct.comprehend_text(agent, q)
        d = comp.dispatch or {}
        spec = d.get("spec")
        return (getattr(spec, "meta_target", None) if spec is not None
                else d.get("meta_target"))

    assert route("What gaps do you have?") == "self_gaps", "self_gaps parity"
    assert route("What limitations do you have?") == "self_gaps"
    assert route("What are you?") == "self_identity", (
        "the bare identity question keeps its intercept (region-final shape)")
    assert route("Who are you?") == "self_identity"
    assert route("what sort of thing are you?") == "self_identity"
    assert route("Are you an LLM?") == "self_kind", "polar self-classification parity"


# --- narration: transition -> exactly one chat turn, restart-safe --------------

def _mk_state(agent, tmp_path):
    state = jd.DaemonState(agent, booted_from="test")
    state.chat_history_path = tmp_path / "chat_history.json"
    events = []
    state.publish_event = events.append   # capture instead of SSE
    return state, events


def test_narration_is_one_turn_per_pass_and_restart_safe(agent, tmp_path):
    # Two fresh concluded transitions -> two candidates.
    e1 = agent.s.add_node("Experiment", {"status": "done", "outcome": "refuted",
                                         "hypothesis": "narrate me first"})
    e2 = agent.s.add_node("Experiment", {"status": "failed", "outcome": "",
                                         "hypothesis": "narrate me second"})
    # Pre-existing concluded nodes from earlier tests get marked as we go; use
    # a fresh state and drain until our two candidates are the ones served.
    state, events = _mk_state(agent, tmp_path)

    served = []
    for _ in range(20):                      # bounded drain of the queue
        turn = jd._narrate_tick(state)
        if turn is None:
            break
        served.append(turn["reply"])
    assert any("narrate me first" in s and "refuted" in s for s in served)
    assert any("narrate me second" in s for s in served)
    # THROTTLE: each pass produced at most one narration -> the number of chat
    # events equals the number of narrated turns (one per _narrate_tick call).
    chat_events = [e for e in events if e.get("type") == "chat"]
    assert len(chat_events) == len(served)
    assert all(e.get("reply_from") == "agent" for e in chat_events)

    # markers persisted ON the nodes
    assert agent.s.node(e1)["attrs"].get("narrated") == 1.0
    assert agent.s.node(e2)["attrs"].get("narrated") == 1.0

    # RESTART-SAFE: a brand-new DaemonState over the same graph re-narrates nothing.
    state2, events2 = _mk_state(agent, tmp_path)
    assert jd._narrate_tick(state2) is None
    assert not events2


def test_narration_covers_adoptions(agent, tmp_path):
    agent.s.add_node("Adoption", {"rule_removed": "old_rule", "rule_added": "new_rule",
                                  "experiment_id": "88", "tick": 2.0})
    state, events = _mk_state(agent, tmp_path)
    served = []
    for _ in range(20):
        turn = jd._narrate_tick(state)
        if turn is None:
            break
        served.append(turn["reply"])
    assert any("old_rule" in s and "new_rule" in s for s in served), (
        "an Adoption mint is narrated with the rule replacement")


# --- seed hygiene: the steering rules round-trip _canon_rule_body --------------

def test_steering_rules_round_trip_canon_body():
    # If these ever stop round-tripping byte-identically, the daemon's
    # rule-refresh reconciliation would churn them on every resume (the
    # 'leak-free' property test_self_concern_promote_migrated gates).
    import json
    from substrate.seed_loader import SEED_DIR
    seed = json.load(open(os.path.join(str(SEED_DIR), "conversation_steering.json")))
    for r in seed["rules"]:
        c1 = jd._canon_rule_body(r)
        assert c1, f"{r['name']} must canonicalise"
        assert jd._canon_rule_body(json.loads(c1)) == c1, (
            f"{r['name']} must round-trip byte-identically")


def test_steer_promotes_the_best_matching_concern_not_the_oldest():
    """conversation_steering v1.2.0 (tranche 14): an OLDER concern that shares
    one word with the steer turn (here a shadow-read divergence concern that
    quotes an earlier steer phrase) must not steal the promote from the
    concern the turn actually names."""
    import jabberwock_daemon as jd
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.converse("Hello.", speech_act="greeting")
    old = a.s.add_node("SelfConcern", {
        "kind": "comprehension", "status": "noted", "source": "implicit",
        "content": "comprehension classified this as 'instruction' but the deep reader heard "
                   "'statement' (recurring; e.g. \"Work on the condense data gap.\")"})
    a.inner.add_edge_unchecked(a.agent, "has_self_concern", old)
    a.converse("Alphabetise the data.", speech_act="request")
    a.converse("Work on the alphabetise data gap.", speech_act="request")
    p = jd._steer_tick(a)
    assert p and p[0].get("ok") and p[0].get("kind") == "instruction"
    assert "alphabetise" in p[0].get("about", "")
    assert a.s.node(old)["attrs"].get("status") == "noted"
