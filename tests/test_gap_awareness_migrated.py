"""The agent FINDS ITS OWN GAPS -- graph-native (seeds/gap_awareness.json).

A gap is a SelfConcern node (the shared contract with the surfacing side,
tests/test_self_gaps_surfacing_migrated.py):

    agent -has_self_concern-> sc
    sc.attrs = {status:'noted', source:'implicit'|'explicit_report',
                kind:<str>, content:<topic-or-description str>}

so the human-gated self-improvement spine (jabberwock_daemon.promote_self_concern
-> StandingConcern) and the gap-surfacing reader both find it, unified with the
chat-originated SelfConcerns conversation_self_concern.json already mints.

Two mechanisms, BOTH graph rules (no Python decision):

  (1) IMPLICIT -- when the agent tries to answer a topic and CANNOT ground it,
      the adapter records outcome='unresolved' on the answer_topic Goal (a
      datum), and the rule note_unresolved_topic_gap DECIDES that is a gap and
      files SelfConcern{source:'implicit'}.

  (2) EXPLICIT -- when a human reports a limitation ("you cannot X"), a held
      DEFICIENCY concept + a SELF-word both resolve off the message (the intent
      seed's Mention -refers_to-> Concept rule), and the rule note_reported_gap
      COMPREHENDS it as a self-referential deficiency, filing
      SelfConcern{source:'explicit_report'} + a confirming reply -- instead of
      misrouting to external-topic grounding.

  (3) PRECEDENCE -- a self/meta query the front end classified as path=='meta'
      whose parsed "topic" is itself self-referential ("... in your knowledge")
      is NOT hijacked into grounding a self-word (no answer_topic goal minted);
      a genuine external topic under the same dispatch ("the moon") still routes.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _self_concerns(a, source=None):
    out = []
    for sc in a.inner.neighbours(a.agent, "has_self_concern"):
        if not a.inner.has_node(sc):
            continue
        at = a.s.node(sc)["attrs"]
        if source is None or at.get("source") == source:
            out.append(at)
    return out


def _answer_topic_goals(a, concept=None):
    out = []
    for g in a.inner.neighbours(a.agent, "has_goal"):
        if not a.inner.has_node(g):
            continue
        ga = a.s.node(g)["attrs"]
        if ga.get("kind") == "answer_topic" and (concept is None or ga.get("concept") == concept):
            out.append(g)
    return out


def test_implicit_unresolved_topic_files_a_gap(agent, monkeypatch):
    # A reflexive question about a topic the agent cannot hold or ground. Force
    # the self-heal grounder to a MISS (stands in for "no teacher / ungroundable")
    # so the outcome is deterministically 'unresolved'.
    import domains.topic_grounding as _tg
    monkeypatch.setattr(_tg, "ground_topic", lambda ag, phrase, **kw: None)

    topic = "zqxwvt"
    agent.converse(f"What do you know about {topic}?", speech_act="question")
    # the turn routed to the external topic (not a self-faculty), and the answer
    # attempt missed -> the adapter recorded outcome='unresolved' on the goal.
    goals = _answer_topic_goals(agent, topic)
    assert goals, "the reflexive topic question must route to Goal{answer_topic}"
    assert agent.s.node(goals[0])["attrs"].get("outcome") == "unresolved"

    # run the rules -> note_unresolved_topic_gap DECIDES this is a gap and files it.
    agent.comprehend()
    implicit = _self_concerns(agent, source="implicit")
    assert any(c.get("content") == topic and c.get("status") == "noted"
               and c.get("kind") == "knowledge" for c in implicit), (
        "an unresolved answer_topic goal must be filed as a "
        "SelfConcern{source:'implicit', kind:'knowledge'} about the topic")


def test_implicit_gap_is_filed_once(agent, monkeypatch):
    import domains.topic_grounding as _tg
    monkeypatch.setattr(_tg, "ground_topic", lambda ag, phrase, **kw: None)
    agent.converse("What do you know about zqxwvt?", speech_act="question")
    agent.comprehend()
    agent.comprehend()  # fixpoint re-run must NOT duplicate the gap
    implicit = [c for c in _self_concerns(agent, source="implicit")
                if c.get("content") == "zqxwvt"]
    assert len(implicit) == 1, "gap_noted guard must file exactly one gap per goal"


def test_gaps_are_deduped_by_content(agent, monkeypatch):
    # Two DISTINCT unresolved turns about the SAME topic must file ONE gap only
    # (the content-dedup guard: a rule declines to file a gap whose content
    # already exists as a SelfConcern). The per-goal gap_noted guard alone would
    # not catch this -- these are two different goals.
    import domains.topic_grounding as _tg
    monkeypatch.setattr(_tg, "ground_topic", lambda ag, phrase, **kw: None)
    agent.converse("What do you know about zqxwvt?", speech_act="question")
    agent.comprehend()
    agent.converse("What do you know about zqxwvt?", speech_act="question")
    agent.comprehend()
    dupes = [c for c in _self_concerns(agent, source="implicit")
             if c.get("content") == "zqxwvt"]
    assert len(dupes) == 1, "content-dedup guard must file each distinct gap once"


def test_agent_retires_legacy_duplicate_gaps(agent):
    # Legacy dupes (filed before the dedup guard existed): three identical +
    # one distinct, all linked. The agent must retract the extras ITSELF in its
    # rule fixpoint (keep_one_gap designates one keeper per content; retire_
    # unkept_gap retires the rest), keeping exactly one per distinct content.
    def mk(content):
        sc = agent.s.add_node("SelfConcern", {"status": "noted", "source": "implicit",
                                              "kind": "knowledge", "content": content})
        agent.inner.add_edge_unchecked(agent.agent, "has_self_concern", sc)
        return sc

    for _ in range(3):
        mk("widgets")
    mk("gizmos")

    agent.comprehend()   # the agent dedups its own list, graph-native

    active = {}
    retired = 0
    for sc in agent.s.nodes("SelfConcern"):
        a = agent.s.node(sc)["attrs"]
        if a.get("content") not in ("widgets", "gizmos"):
            continue
        if a.get("status") == "retired":
            retired += 1
        else:
            active[a["content"]] = active.get(a["content"], 0) + 1

    assert active.get("widgets") == 1, "exactly one 'widgets' gap kept after self-retire"
    assert active.get("gizmos") == 1, "the distinct gap is kept"
    assert retired == 2, "the two duplicate 'widgets' concerns are retired"

    # the surfacing reader shows each distinct content once (retired skipped)
    from domains import reflective_faculty as _rf
    state = _rf.reflect("self_gaps", None, agent.inner)
    contents = [c.get("content") for c in state.get("concerns", [])]
    assert contents.count("widgets") == 1 and contents.count("gizmos") == 1


def test_accounted_self_faculty_is_answered(agent):
    # A faculty the agent HOLDS a SelfProcess account for (collapse) is ANSWERED
    # from that account -- not the honest floor, and no gap filed.
    reply = agent.converse("How does your collapse function work?", speech_act="question")
    assert not _answer_topic_goals(agent), "a self-faculty question is not an external topic"
    assert "i work by collapse" in (reply or "").lower(), "answered from the held self-account"
    agent.comprehend()
    assert not [c for c in _self_concerns(agent, source="implicit")
                if c.get("kind") == "self_account" and "collapse" in str(c.get("content", ""))], (
        "an ANSWERED self-faculty must not file a self-account gap")


def test_unaccounted_self_faculty_files_a_clean_self_gap(agent):
    # A faculty the agent holds NO account for (reasoning) -> honest self floor ->
    # it FINDS that as a gap about itself, with the faculty named CLEANLY (the
    # possessive determiner 'your' stripped: content is 'reasoning', not 'your
    # reasoning').
    reply = agent.converse("How does your reasoning work?", speech_act="question")
    assert not _answer_topic_goals(agent), "a self-account question is not an external topic"
    assert "couldn't find it through the sources" not in (reply or "").lower()

    agent.comprehend()   # the gap rule fires in the fixpoint
    sa = [c for c in _self_concerns(agent, source="implicit") if c.get("kind") == "self_account"]
    assert any(str(c.get("content", "")).strip().lower() == "reasoning" for c in sa), (
        "the filed self-gap names the faculty CLEANLY (no 'your' possessive)")


def test_resolved_topic_files_no_gap(agent):
    # 'moon' grounds from the local wiki library (no teacher needed) -> resolved
    # -> NO implicit gap.
    agent.converse("What do you know about the moon?", speech_act="question")
    agent.comprehend()
    goals = _answer_topic_goals(agent, "moon")
    assert goals and agent.s.node(goals[0])["attrs"].get("outcome") == "resolved"
    assert not [c for c in _self_concerns(agent, source="implicit")
                if c.get("content") == "moon"], "a resolved topic is not a gap"


def test_explicit_reported_gap_is_comprehended_not_grounded(agent):
    reply = agent.converse("You cannot elaborate.", speech_act="statement")
    # a confirming reply came back from the graph rule (not the bare 'noted' floor)
    assert isinstance(reply, str) and "gap" in reply.lower()

    explicit = _self_concerns(agent, source="explicit_report")
    assert any(c.get("status") == "noted" and c.get("kind") == "reported"
               and "cannot elaborate" in str(c.get("content")).lower()
               for c in explicit), (
        "a reported self-limitation must be filed as a "
        "SelfConcern{source:'explicit_report'}")
    # it was comprehended as a self-referential deficiency, NOT routed to
    # grounding the deficiency word as an external topic.
    assert not _answer_topic_goals(agent), (
        "an explicit gap report must NOT be misrouted to external-topic grounding")


def test_precedence_self_meta_query_mints_no_answer_topic_goal(agent):
    # A self/meta gap query the front end classifies as path=='meta' with a
    # self-referential "topic" ('... in your knowledge') must stay on the meta
    # path: no comp_topic written -> route rule never fires -> no answer_topic goal.
    agent.converse("What gaps do you have in your knowledge?", speech_act="question")
    assert not _answer_topic_goals(agent), (
        "a self-referential meta query must not mint an answer_topic goal "
        "(comp_topic is not written when the front end says path=='meta' and the "
        "parsed topic is self-referential)")
