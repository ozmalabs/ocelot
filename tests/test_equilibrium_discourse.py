"""Equilibrium behavioural quanta (streams T3b/T3c, pack 0.5.0): adapter-level goldens.

0.5.0 note: turn adjacency is no longer structure; the G-M1 meeting golden now
DECLARES the replies the old adjacency rule inferred (identical expectations), and
the same meeting without declared replies is asserted separately.

Slice-2 note: the sealed slice-1 golden windows are compared on their 0.3.0
trait vocabulary unchanged; the 0.4.0 space-climate traits they now also carry
are asserted separately (tests/test_equilibrium_climate.py has the climate goldens).

Synthetic windows only (pseudonyms actor_a / expert_e / member_###); no corpus,
no LLM (OZMA_NO_LLM=1). Every expectation below is a rule output; the adapter
only ingests, ticks the seeded strata, and reads out.
Run: OZMA_NO_LLM=1 PYTHONPATH=.:runners/dsl/python python3 -m pytest tests/test_equilibrium_discourse.py -q
"""
import os
import re
from pathlib import Path

import pytest

os.environ.setdefault("OZMA_NO_LLM", "1")

from domains import equilibrium_classify as eq  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# ---- golden windows (sealed with the PREREG; do not tune to outputs) ---------
MEETING = [  # floor dominance, uncorroborated claim later contested by grounded
    ("t01", "actor_a", "Trust me, in my 20 years this has never been the problem."),  # evidence,
    ("t02", "member_003", "Could the cache be cold after the deploy?"),               # a concession,
    ("t03", "actor_a", "That is ridiculous, I know what I'm doing."),                 # a de-escalation
    ("t04", "member_003", "Never mind, I'll leave it there."),                        # bridge and a
    ("t05", "actor_a", "We ship it as is."),                                          # withdrawal
    ("t06", "expert_e", "However, the benchmark shows p99 latency doubled, see https://example.org/bench/42"),
    ("t07", "actor_a", "Fair point, I hadn't considered that."),
    ("t08", "member_002", "Let's step back and look at the data together."),
    ("t09", "actor_a", "Agreed, let's look at it."),
]
THREAD = [  # acknowledged + corroborated claim, selective non-response, question demand
    ("p1", "actor_a", "As a nurse I see this every week.", None),
    ("p2", "member_101", "Good point, thanks for sharing.", "p1"),
    ("p3", "member_102", "Why would that matter here?", "p1"),
    ("p4", "actor_a", "Happy to help.", "p2"),
    ("p5", "expert_e", "See https://example.org/study/7 for the numbers.", "p3"),
    ("p6", "member_102", "But why should we trust that study?", "p5"),
    ("p7", "member_102", "And who funded it?", "p5"),
]


def _meeting_turns(rows=MEETING):
    return [{"id": i, "actor_ref": a, "text": t} for i, a, t in rows]


def _thread_turns(rows=THREAD):
    return [{"id": i, "actor_ref": a, "text": t, "reply_to": r} for i, a, t, r in rows]


@pytest.fixture(scope="module")
def base():
    s, root = eq.boot()
    return s, root, s.snapshot()


def _disc(base, turns, kind="thread", window_id="w_test", fork=None):
    _, root, snap = base
    return eq.discourse(fork if fork is not None else snap.fork(), root,
                        {"window_id": window_id, "kind": kind}, turns)


SHARE = "interaction.floor_share"  # 0.7.0: one per speaking actor; checked in test_floor_share_*


def _q(out, share=False):
    return {(q["actor_ref"], q["trait"], q["polarity"], q.get("target_ref")): q for q in out["quanta"]
            if share or q["trait"] != SHARE}


CLIMATE_TRAITS = {"voice.dissent", "voice.error_admission", "inquiry.challenge", "inquiry.answered",
                  "inquiry.unanswered", "response.dismissal", "response.engagement"}


def _slice1(keys):
    """Quanta keys in the slice-1 (0.3.0) trait vocabulary."""
    return {k for k in keys if k[1] not in CLIMATE_TRAITS}


def _climate(q):
    return {k: (v["match"], v["evidence"], v["counter_evidence"]) for k, v in q.items()
            if k[1] in CLIMATE_TRAITS}


def _check_wire_invariants(out, turns):
    ids = {t["id"] for t in turns}
    actors = {t["actor_ref"] for t in turns}
    for q in out["quanta"]:
        assert q["match"] in ("exact", "partial", "weak"), q
        assert re.fullmatch(r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*){0,7}", q["trait"]), q
        assert q["evidence"] and set(q["evidence"]) <= ids and set(q["counter_evidence"]) <= ids
        assert not set(q["evidence"]) & set(q["counter_evidence"]), q   # client rejects overlap
        assert q["actor_ref"] in actors
        assert q.get("target_ref") is None or (q["target_ref"] in actors and q["target_ref"] != q["actor_ref"])
        assert q["rule_ids"] and all("@" + eq.PACK_VERSION in r for r in q["rule_ids"])
    for e in out["episodes"]:
        assert e["turns"] and set(e["turns"]) <= ids and e["actor_refs"]
        assert e["generative"] in (True, False, None)
        assert all(f["match"] in ("exact", "partial", "weak") for f in e["facets"])


# ---- G-M1: meeting --------------------------------------------------------
def _meeting_declared(rows=MEETING):
    """The G-M1 meeting with each turn DECLARING a reply to the previous turn:
    exactly the response edges the pre-0.5.0 adjacency rule inferred for it
    (every adjacent pair has two different speakers)."""
    turns = _meeting_turns(rows)
    for prev, t in zip(turns, turns[1:]):
        t["reply_to"] = prev["id"]
    return turns


def test_meeting_without_declared_replies_tracks_structure(base):
    """0.5.0 (T3c O2): adjacency is not a forced edge; the seeded turn cursor TRACKS
    structure. 0.8.0 (T3g, held-open collapse): adjacency is one cue among others and
    a turn collapses only on strict cue-set dominance. eq-tax-0.8.0 Amendment A: the
    open room question t02 is a REPLY rival only in its conditional-relevance slot (the
    first turn by another actor after it: actor_a's dismissal t03) or for an answer
    FORM; it is no rival of the adjacent turn later (0.8.0 before the amendment held
    t05..t09 between {t02: open_question, answer_form} and their adjacent turn). So the
    meeting tracks as one chain, each turn replying locally (adjacent + addressed /
    contrast / uptake where they hold), and every later turn is under the TOPIC t02
    (the live issue, inherited via_reply). The reply-pair quanta of t05..t09 (contested,
    acknowledged, engagement, dissent, the addressed stance targets) are back; t02 stays
    open (no answer) but is ENGAGED (actor_a's t05 under its topic), so not unanswered."""
    turns = _meeting_turns()
    out = _disc(base, turns, kind="meeting", window_id="w_meet_0")
    _check_wire_invariants(out, turns)
    rows = {t["id"]: (t["responds_to"], t["basis"], t["confidence"], t["addressees"], t["answers"])
            for t in out["turns"]}
    assert rows == {
        "t01": ([], "none", None, [], []), "t02": (["t01"], "tracked", "strong", [], []),
        "t03": (["t02"], "tracked", "strong", ["member_003"], []),
        "t04": (["t03"], "tracked", "strong", ["actor_a"], []),
        "t05": (["t04"], "tracked", "strong", ["member_003"], []),
        "t06": (["t05"], "tracked", "strong", ["actor_a"], []),
        "t07": (["t06"], "tracked", "strong", ["expert_e"], []),
        "t08": (["t07"], "tracked", "strong", [], []),
        "t09": (["t08"], "tracked", "weak", [], []),
    }
    cands = {t["id"]: {c["ref"]: c["cues"] for c in t["candidates"]} for t in out["turns"]}
    assert cands["t03"] == {"t02": ["adjacent", "open_question"]}  # the slot
    assert cands["t05"] == {"t04": ["addressed", "adjacent"]}
    assert cands["t06"] == {"t05": ["adjacent", "contrast"]}
    assert cands["t08"] == {"t07": ["adjacent", "uptake"]}
    topics = {t["id"]: (t["topic_id"], {c["ref"]: c["cues"] for c in t["topic_candidates"]}) for t in out["turns"]}
    assert topics["t04"] == ("t02", {"t02": ["via_reply"]})  # the asker's own turn: via its reply only
    assert all(topics[k] == ("t02", {"t02": ["open_question", "via_reply"]})
               for k in ("t03", "t05", "t06", "t07", "t08", "t09"))
    assert {t["id"]: t["thread_id"] for t in out["turns"]} == {f"t0{k}": "t01" for k in range(1, 10)}
    q = _q(out)
    assert set(q) == {
        ("actor_a", "competence.claim_grounding", "-", None),
        ("actor_a", "competence.claimed", "+", None),
        ("actor_a", "competence.contested", "+", "expert_e"),
        ("actor_a", "interaction.floor", "+", None),
        ("actor_a", "response.dismissal", "+", "member_003"),
        ("actor_a", "response.engagement", "+", "expert_e"),
        ("actor_a", "stance.concession", "+", "expert_e"),
        ("actor_a", "stance.deescalation", "+", "expert_e"),
        ("actor_a", "stance.hostility", "+", "member_003"),
        ("actor_a", "status.claim", "+", None),
        ("expert_e", "competence.acknowledged", "+", "actor_a"),
        ("expert_e", "competence.demonstrated", "+", None),
        ("expert_e", "competence.demonstrated.citation", "+", None),
        ("expert_e", "competence.demonstrated.technical", "+", None),
        ("expert_e", "epistemic.citation", "+", None),
        ("expert_e", "voice.dissent", "+", "actor_a"),
        ("member_002", "stance.deescalation", "+", None),
        ("member_003", "competence.demonstrated", "+", None),
        ("member_003", "competence.demonstrated.technical", "+", None),
        ("member_003", "epistemic.hedging", "+", None),
        ("member_003", "interaction.withdrawal", "+", None),
    }
    assert out["open_questions"] == ["t02"]


def test_golden_meeting_window(base):
    turns = _meeting_declared()
    out = _disc(base, turns, kind="meeting", window_id="w_meet_1")
    assert {t["basis"] for t in out["turns"][1:]} == {"declared"} and out["turns"][0]["basis"] == "none"
    assert {t["thread_id"] for t in out["turns"]} == {"t01"}
    _check_wire_invariants(out, turns)
    q = _q(out)
    assert _slice1(q) == {
        ("actor_a", "competence.claim_grounding", "-", None),
        ("actor_a", "competence.claimed", "+", None),
        ("actor_a", "competence.contested", "+", "expert_e"),
        ("actor_a", "interaction.floor", "+", None),
        ("actor_a", "stance.concession", "+", "expert_e"),
        ("actor_a", "stance.deescalation", "+", "expert_e"),
        ("actor_a", "stance.hostility", "+", "member_003"),
        ("actor_a", "status.claim", "+", None),
        ("expert_e", "competence.acknowledged", "+", "actor_a"),
        ("expert_e", "competence.demonstrated", "+", None),
        ("expert_e", "competence.demonstrated.citation", "+", None),
        ("expert_e", "competence.demonstrated.technical", "+", None),
        ("expert_e", "epistemic.citation", "+", None),
        ("member_002", "stance.deescalation", "+", "actor_a"),
        ("member_003", "competence.demonstrated", "+", None),
        ("member_003", "competence.demonstrated.technical", "+", None),
        ("member_003", "epistemic.hedging", "+", None),
        ("member_003", "interaction.withdrawal", "+", None),
    }
    # floor dominance: strictly most turns. 0.7.0: evidence / counter are the holder's /
    # the runner-up's FIRST turn (bounded), the shares are interaction.floor_share
    fl = q[("actor_a", "interaction.floor", "+", None)]
    assert fl["evidence"] == ["t01"] and fl["counter_evidence"] == ["t02"] and fl["match"] == "partial"
    qs = _q(out, share=True)
    assert qs[("actor_a", SHARE, "+", None)]["evidence"] == ["t01", "t03", "t05", "t07", "t09"]
    assert qs[("member_003", SHARE, "+", None)]["evidence"] == ["t02", "t04"]
    assert {k[0] for k in qs if k[1] == SHARE} == {t["actor_ref"] for t in turns}
    # uncorroborated status claim, later contested by grounded evidence
    cl = q[("actor_a", "competence.claimed", "+", None)]
    assert cl["evidence"] == ["t01", "t03"] and cl["match"] == "exact"   # repeated act
    ung = q[("actor_a", "competence.claim_grounding", "-", None)]
    assert ung["match"] == "weak" and ung["evidence"] == ["t01", "t03"]   # capped weak
    con = q[("actor_a", "competence.contested", "+", "expert_e")]
    assert con["evidence"] == ["t01", "t03", "t06"]
    assert ("actor_a", "competence.corroborated", "+", None) not in q
    # concession (single act -> at most partial) and the acknowledgement it confers
    assert q[("actor_a", "stance.concession", "+", "expert_e")]["evidence"] == ["t07"]
    assert q[("actor_a", "stance.concession", "+", "expert_e")]["match"] == "partial"
    assert q[("expert_e", "competence.acknowledged", "+", "actor_a")]["evidence"] == ["t07"]
    # de-escalation bridge and withdrawal (never posts again -> no counter)
    assert q[("member_002", "stance.deescalation", "+", "actor_a")]["evidence"] == ["t08"]
    wd = q[("member_003", "interaction.withdrawal", "+", None)]
    assert wd["evidence"] == ["t04"] and wd["counter_evidence"] == []
    # episodes: an escalated dispute and a resolved (generative) one
    eps = {e["episode_id"]: e for e in out["episodes"]}
    assert set(eps) == {"ep:t02", "ep:t05"}
    e1, e2 = eps["ep:t02"], eps["ep:t05"]
    assert e1["turns"] == ["t02", "t03", "t04"] and e1["generative"] is False
    assert {f["code"] for f in e1["facets"]} == {"affective", "epistemic", "status"}
    assert e2["turns"] == ["t05", "t06", "t07", "t08"] and e2["generative"] is True
    assert e2["actor_refs"] == ["actor_a", "expert_e", "member_002"]
    assert [e["episode_id"] for e in out["episodes"]] == ["ep:t02", "ep:t05"]  # by first turn
    # 0.4.0 climate quanta on the same window: the question t02 met by a hostile
    # status reply (dismissal: no answer); the contrast t06 against actor_a's claim is
    # dissent, met by a concession (engagement). eq-tax-0.8.0 Amendment A: the declared
    # reply chain keeps t02's topic (t03 -> t04 -> t05 inherit it via_reply) and actor_a's
    # t05 ("We ship it as is.") is a free-form contribution under it, so t02 is ENGAGED,
    # not unanswered (0.8.0 before the amendment: unanswered)
    assert _climate(q) == {
        ("actor_a", "response.dismissal", "+", "member_003"): ("partial", ["t02", "t03"], []),
        ("actor_a", "response.engagement", "+", "expert_e"): ("partial", ["t06", "t07"], []),
        ("expert_e", "voice.dissent", "+", "actor_a"): ("partial", ["t06"], []),
    }
    assert {t["id"]: t["topic_id"] for t in out["turns"]}["t05"] == "t02"


def test_withdrawal_with_return_is_contested(base):
    rows = MEETING[:4] + [("t04b", "member_003", "Actually one more thing on the cache.")] + MEETING[4:]
    q = _q(_disc(base, _meeting_turns(rows), kind="meeting"))
    wd = q[("member_003", "interaction.withdrawal", "+", None)]
    assert wd["evidence"] == ["t04"] and wd["counter_evidence"] == ["t04b"] and wd["match"] == "weak"


# ---- G-T1: thread ---------------------------------------------------------
def test_golden_thread_window(base):
    turns = _thread_turns()
    out = _disc(base, turns, kind="thread", window_id="w_thr_1")
    _check_wire_invariants(out, turns)
    q = _q(out)
    assert _slice1(q) == {
        ("actor_a", "competence.acknowledged", "+", "member_101"),
        ("actor_a", "competence.claim_grounding", "+", None),
        ("actor_a", "competence.claimed", "+", None),
        ("actor_a", "competence.corroborated", "+", None),
        ("actor_a", "interaction.responsiveness", "-", "member_102"),
        ("expert_e", "competence.demonstrated", "+", None),
        ("expert_e", "competence.demonstrated.citation", "+", None),
        ("expert_e", "epistemic.citation", "+", None),
        ("member_101", "stance.concession", "+", "actor_a"),
        ("member_101", "stance.deescalation", "+", "actor_a"),
        ("member_102", "epistemic.question_demand", "+", "expert_e"),
        ("member_102", "interaction.floor", "+", None),
        # O2: consecutive turns p6 -> p7 by the same actor (`eq_continues`, an
        # ordering edge, NOT a response: p7's responds_to stays the declared p5)
        ("member_102", "interaction.run", "+", None),
    }
    tw = {t["id"]: t for t in out["turns"]}
    assert tw["p7"]["responds_to"] == ["p5"] and tw["p7"]["basis"] == "declared"
    assert tw["p3"]["responds_to"] == ["p1"] and tw["p3"]["basis"] == "declared"
    assert tw["p3"]["addressees"] == ["actor_a"] and tw["p5"]["answers"] == ["p3"]
    assert tw["p1"]["basis"] == "none" and {t["thread_id"] for t in out["turns"]} == {"p1"}
    assert out["open_questions"] == ["p6", "p7"]
    assert q[("actor_a", "competence.claimed", "+", None)]["match"] == "partial"  # one act
    assert q[("actor_a", "competence.corroborated", "+", None)]["evidence"] == ["p1", "p2"]
    assert q[("actor_a", "competence.claim_grounding", "+", None)]["evidence"] == ["p1", "p2"]
    rs = q[("actor_a", "interaction.responsiveness", "-", "member_102")]
    assert rs["evidence"] == ["p3"] and rs["counter_evidence"] == []
    qd = q[("member_102", "epistemic.question_demand", "+", "expert_e")]
    assert qd["evidence"] == ["p6", "p7"] and qd["match"] == "exact"
    assert [e["episode_id"] for e in out["episodes"]] == ["ep:p5"]
    assert out["episodes"][0]["generative"] is False
    # 0.4.0: p3 answered (with a link) by expert_e; p6 contests with a leading "but".
    # p6/p7 are not unanswered: nobody else posted after them (absence is relative)
    assert _climate(q) == {
        ("expert_e", "inquiry.answered", "+", "member_102"): ("partial", ["p3", "p5"], []),
        ("expert_e", "response.engagement", "+", "member_102"): ("partial", ["p3", "p5"], []),
        ("member_102", "inquiry.challenge", "+", "expert_e"): ("partial", ["p6"], []),
    }


def test_responsiveness_counter_and_absent_actor_not_marked(base):
    rows = THREAD[:4] + [("p3b", "member_102", "Is that weekly on average?", "p1"),
                         ("p4b", "actor_a", "Yes, roughly.", "p3b")]
    q = _q(_disc(base, _thread_turns(rows)))
    rs = q[("actor_a", "interaction.responsiveness", "-", "member_102")]
    assert rs["evidence"] == ["p3"] and rs["counter_evidence"] == ["p3b"]
    # actor who never posts after the question is not marked (absence is relative)
    rows2 = [("p1", "actor_a", "As a nurse I see this every week.", None),
             ("p2", "member_102", "Why would that matter here?", "p1")]
    q2 = _q(_disc(base, _thread_turns(rows2)))
    assert not any(k[1] == "interaction.responsiveness" for k in q2)


def test_floor_tie_mints_nothing(base):
    rows = [("a1", "actor_a", "ok"), ("b1", "member_201", "ok"),
            ("a2", "actor_a", "ok"), ("b2", "member_201", "ok")]
    q = _q(_disc(base, _meeting_turns(rows), kind="meeting"))
    assert not any(k[1] == "interaction.floor" for k in q)


def test_generative_null_when_reescalated_after_resolution(base):
    """PREREG G11 under the DESIGN §8.3 shapes: resolve then re-escalate -> null."""
    rows = [("g1", "actor_a", "The cache is cold.", None),
            ("g2", "member_401", "However, the cache was warmed.", "g1"),
            ("g3", "actor_a", "Fair point.", "g2"),
            ("g4", "member_401", "But that is still ridiculous.", "g3")]
    out = _disc(base, _thread_turns(rows))
    assert [(e["episode_id"], e["turns"], e["generative"]) for e in out["episodes"]] == [
        ("ep:g1", ["g1", "g2", "g3", "g4"], None),
        # documented v1 limitation (DESIGN §12.4, merging deferred): the re-escalation
        # also roots its own overlapping episode
        ("ep:g3", ["g3", "g4"], False)]


def test_tribal_reference_quantum_and_facet(base):
    """PREREG G12: address + collective -> quantum and tribal facet; group noun alone -> nothing."""
    rows = [("r1", "actor_a", "The cache is cold.", None),
            ("r2", "member_501", "You people never listen, this is ridiculous.", "r1"),
            ("r3", "member_502", "The team looked at it.", "r1")]
    out = _disc(base, _thread_turns(rows))
    q = _q(out)
    assert q[("member_501", "tribal.outgroup_reference", "+", None)]["evidence"] == ["r2"]
    assert not any(k[0] == "member_502" and k[1].startswith("tribal") for k in q)
    assert "tribal" in {f["code"] for e in out["episodes"] for f in e["facets"]}


def test_question_demand_negative_control(base):
    """PREREG G8 control: the same question with no prior evidence turn -> no quantum."""
    rows = [("s1", "expert_e", "The cache is cold.", None),
            ("s2", "actor_a", "Is that faster", "s1")]
    assert not any(k[1] == "epistemic.question_demand" for k in _q(_disc(base, _thread_turns(rows))))


def test_no_cue_window_is_empty(base):
    """PREREG G14: neutral logistics chat -> no quanta, no episodes (0.7.0: apart from
    each speaker's interaction.floor_share, which every turn feeds)."""
    rows = [("z1", "member_601", "ok", None), ("z2", "member_602", "the build is green", None)]
    out = _disc(base, _thread_turns(rows))
    assert _q(out) == {} and out["episodes"] == []
    assert [(q["actor_ref"], q["evidence"], q["match"]) for q in out["quanta"]] == [
        ("member_601", ["z1"], "partial"), ("member_602", ["z2"], "partial")]


def test_floor_share_is_monotone_and_floor_swap_is_bounded(base):
    """0.7.0: every turn is evidence of its author's floor share; a runner-up change
    moves ONE counter ref on the floor quantum (0.6.0: every turn of both runners-up)."""
    rows = [("a1", "actor_a", "the cache is cold"), ("a2", "actor_a", "the disk is full"),
            ("b1", "member_201", "lunch is at noon"), ("a3", "actor_a", "the build is green"),
            ("c1", "member_202", "the runner is slow"), ("c2", "member_202", "the log is long")]
    q4 = _q(_disc(base, _meeting_turns(rows[:4]), kind="meeting"), share=True)
    q6 = _q(_disc(base, _meeting_turns(rows), kind="meeting"), share=True)
    f4, f6 = q4[("actor_a", "interaction.floor", "+", None)], q6[("actor_a", "interaction.floor", "+", None)]
    assert (f4["evidence"], f4["counter_evidence"]) == (["a1"], ["b1"])
    assert (f6["evidence"], f6["counter_evidence"]) == (["a1"], ["c1"])  # runner-up member_201 -> member_202
    assert q6[("actor_a", SHARE, "+", None)]["evidence"] == ["a1", "a2", "a3"]
    assert q6[("member_202", SHARE, "+", None)]["evidence"] == ["c1", "c2"]
    assert q6[("member_202", SHARE, "+", None)]["match"] == "exact" and q6[("member_201", SHARE, "+", None)]["match"] == "partial"


def test_no_numeric_literal_comparison_operands():
    """PREREG P3(c): no numeric literal in any pack rule (the singleton set-size is |{pick(E)}|)."""
    found = []

    def walk(x, where):
        if isinstance(x, dict):
            if x.get("type") == "Lit" and isinstance(x.get("value"), (int, float)) \
                    and not isinstance(x.get("value"), bool):
                found.append(where)
            for v in x.values():
                walk(v, where)
        elif isinstance(x, list):
            for v in x:
                walk(v, where)
    for m in eq.pack_manifests():
        for r in m.get("rules", []):
            walk(r.get("where"), r["name"])
            walk(r.get("effects"), r["name"])
    assert found == []


# ---- negation / hedge near misses (cue recognition on the base) ------------
NEAR = [  # (text, labels that MUST fire, labels that must NOT fire)
    ("That's not a good point.", {"msg.concession_negated"}, {"msg.concession"}),
    ("Not a fair point at all.", {"msg.concession_negated"}, {"msg.concession"}),
    ("I don't think you're right.", {"msg.concession_negated"}, {"msg.concession"}),
    ("No, that's a fair point.", {"msg.concession"}, {"msg.concession_negated"}),       # comma = clause
    ("It's not ideal but fair point.", {"msg.concession"}, {"msg.concession_negated"}),  # boundary word
    ("Perhaps a fair point.", {"msg.concession", "msg.concession_hedged", "msg.hedge"}, set()),
    ("That is not ridiculous.", {"msg.hostility_negated"}, {"msg.hostility"}),
    ("This is ridiculous.", {"msg.hostility"}, {"msg.hostility_negated"}),
    ("I'm not sorry.", {"msg.deescalation_negated"}, {"msg.deescalation"}),
    ("No worries!", {"msg.deescalation"}, {"msg.deescalation_negated"}),                # head is 'no'
    ("Don't trust me on this.", {"msg.status_claim_negated"}, {"msg.status_claim"}),
    ("Trust me on this.", {"msg.status_claim"}, {"msg.status_claim_negated"}),
    ("I'm not a doctor.", {"msg.credential_negated"}, {"msg.credential"}),
    ("As a nurse I see this weekly.", {"msg.credential"}, {"msg.credential_negated"}),
    ("I'm a bit worried.", set(), {"msg.credential"}),                                  # not noun.person
    ("Never mind.", {"msg.withdrawal"}, {"msg.withdrawal_negated"}),
    ("You people never listen.", {"msg.tribal"}, set()),
    ("Thank you, team.", set(), {"msg.tribal"}),                                        # chain stops at comma
    ("These caches and queries are slow.", set(), set()),                               # see lemma test
    # documented v1 LIMITATION (double negation is not resolved): still negated
    ("It's not that it isn't a good point.", {"msg.concession_negated"}, {"msg.concession"}),
]


def test_negation_near_misses(base):
    _, root, snap = base
    out = eq.classify(snap.fork(), root, [{"id": f"n{i}", "text": t} for i, (t, _y, _n) in enumerate(NEAR)])
    for o, (text, must, mustnt) in zip(out, NEAR):
        got = set(o["labels"])
        assert must <= got, (text, got)
        assert not (mustnt & got), (text, got)
        for lab in got:
            assert o["labels"][lab]["status"] == "shadow", (text, lab)


def test_lemma_tolerant_technical_grounding(base):
    _, root, snap = base
    texts = ["These caches and queries are slow.", "The indexes look fine.", "Two deadlocks today.",
             "We benchmarked it."]  # last: WordNet has no 'benchmarked' -> stays a miss (limit)
    out = eq.classify(snap.fork(), root, [{"id": f"l{i}", "text": t} for i, t in enumerate(texts)])
    tech = [o["labels"].get("msg.domain", {}).get("values") == ["technical"] for o in out]
    assert tech == [True, True, True, False]
    assert eq.lemma("caches") == "cache" and eq.lemma("queries") == "query"


def test_question_via_speech_act_feeds_quanta(base):
    rows = [("q1", "expert_e", "See `make test` for the fix.", None),
            ("q2", "actor_a", "Is that faster", "q1")]  # no '?': subject-aux inversion
    out = _disc(base, _thread_turns(rows))
    assert out["messages"][1]["labels"]["msg.speech_act"]["values"] == ["question"]
    assert ("actor_a", "epistemic.question_demand", "+", "expert_e") in _q(out)


def test_negated_and_hedged_concession_quanta(base):
    rows = [("c0", "expert_e", "The cache is cold.", None),
            ("c1", "actor_a", "That's not a fair point.", "c0"),
            ("c2", "actor_a", "Fair point.", "c0"),
            ("c3", "member_301", "Perhaps a fair point.", "c0"),
            ("c4", "member_301", "Fair point.", "c0")]
    turns = _thread_turns(rows)
    out = _disc(base, turns)
    _check_wire_invariants(out, turns)
    q = _q(out)
    pos = q[("actor_a", "stance.concession", "+", "expert_e")]
    neg = q[("actor_a", "stance.concession", "-", "expert_e")]
    assert (pos["evidence"], pos["counter_evidence"], pos["match"]) == (["c2"], ["c1"], "weak")
    assert (neg["evidence"], neg["counter_evidence"], neg["match"]) == (["c1"], ["c2"], "weak")
    hed = q[("member_301", "stance.concession", "+", "expert_e")]
    assert hed["evidence"] == ["c3", "c4"] and hed["match"] == "partial"  # hedged caps at partial


# ---- PREREG P4: determinism + invariances ---------------------------------
def test_determinism_and_actor_relabelling_invariance(base):
    turns = _meeting_declared()
    a = _disc(base, turns, kind="meeting")
    b = _disc(base, turns, kind="meeting")
    a.pop("steps"), b.pop("steps")
    assert a == b
    ren = {"actor_a": "member_901", "member_003": "member_902", "expert_e": "member_903",
           "member_002": "member_904"}
    c = _disc(base, [{**t, "actor_ref": ren[t["actor_ref"]]} for t in turns], kind="meeting")
    back = {v: k for k, v in ren.items()}
    mapped = {(back[q["actor_ref"]], q["trait"], q["polarity"], back.get(q.get("target_ref"))):
              (q["match"], q["evidence"], q["counter_evidence"]) for q in c["quanta"]}
    assert mapped == {k: (v["match"], v["evidence"], v["counter_evidence"]) for k, v in _q(a, share=True).items()}


def test_prepended_neutral_turn_invariance_thread(base):
    a = _q(_disc(base, _thread_turns()))
    b = _q(_disc(base, _thread_turns([("p0", "member_900", "ok", None)] + THREAD)))  # (shares not compared)
    assert {k: (v["match"], v["evidence"], v["counter_evidence"]) for k, v in b.items()} == \
           {k: (v["match"], v["evidence"], v["counter_evidence"]) for k, v in a.items()}


# ---- PREREG P5: a new trait / composite is graph DATA only ----------------
def _add_codebook(fork, root, typ, edge, attrs):
    n = eq._native(fork)
    x = n.add_node(typ, attrs)
    n.add_edge(root, edge, x)


def test_new_trait_and_composite_are_data_only(base):
    _, root, snap = base
    fork = snap.fork()
    _add_codebook(fork, root, "EqTraitCue", "eq_has_trait_cue", {
        "trait": "probe.link_sharing", "pole": "+", "lab_key": "eqlab:msg.substantive_markers=link",
        "role": "evidence", "owner": "author", "targetable": False})
    _add_codebook(fork, root, "EqTraitCompose", "eq_has_trait_compose", {
        "trait": "probe.combo", "pole": "+", "req_a_trait": "stance.hostility", "req_a_pole": "+",
        "req_b_trait": "status.claim", "req_b_pole": "+", "same_target": False})
    _add_codebook(fork, root, "EqTraitCompose", "eq_has_trait_compose", {  # disabled: never minted
        "trait": "pattern.sealioning", "pole": "+", "req_a_trait": "stance.hostility", "req_a_pole": "+",
        "req_b_trait": "status.claim", "req_b_pole": "+", "same_target": False})
    q = _q(_disc(base, _meeting_declared(), kind="meeting", fork=fork))
    assert q[("expert_e", "probe.link_sharing", "+", None)]["evidence"] == ["t06"]
    combo = q[("actor_a", "probe.combo", "+", None)]
    assert combo["match"] == "partial"  # weakest of hostility(partial) and status.claim(exact)
    assert set(combo["evidence"]) == {"t01", "t03"}
    assert ("actor_a", "pattern.sealioning", "+", None) not in q
    # and the frozen base never saw any of it
    assert not any(k[1].startswith("probe.") for k in _q(_disc(base, _meeting_declared(), kind="meeting")))


# ---- compliance -------------------------------------------------------------
def test_pack_rules_are_graph_data_and_versioned():
    names = [r["name"] for m in eq.pack_manifests() for r in m.get("rules", [])]
    assert len(names) == len(set(names))
    for m in eq.pack_manifests():
        assert m["version"] == eq.PACK_VERSION and m["taxonomy_version"] == eq.TAXONOMY_VERSION
        assert m["self_load_only"] is True
    traits = next(m for m in eq.pack_manifests() if m["id"] == "equilibrium_traits")
    assert {n["type"] for n in traits["nodes"]} == {"EqTrait", "EqTraitCue"}


def test_no_llm_reachable_from_request_path():
    for rel in ("domains/equilibrium_classify.py", "services/equilibrium_classifier/server.py",
                "scripts/_equilibrium_quanta_rules.py", "scripts/build_equilibrium_seed_pack.py"):
        src = (ROOT / rel).read_text().lower()
        for bad in ("anthropic", "openai", "teacher_via_claude", "language_world", "nltk.download"):
            assert bad not in src, (rel, bad)
