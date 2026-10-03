"""Equilibrium space-climate traits (stream T3b slice 2; pack 0.5.0): adapter-level goldens.

voice.dissent, voice.error_admission, inquiry.challenge, inquiry.answered,
inquiry.unanswered, response.dismissal, response.engagement -- all `shadow`.
Synthetic windows only (pseudonyms lead_l / member_* / expert_e); no corpus, no LLM
(OZMA_NO_LLM=1). Every expectation is a seeded rule's output; the adapter only
ingests, ticks the seeded strata and reads out.
Run: OZMA_NO_LLM=1 PYTHONPATH=.:runners/dsl/python python3 -m pytest tests/test_equilibrium_climate.py -q
"""
import os

import pytest

os.environ.setdefault("OZMA_NO_LLM", "1")

from domains import equilibrium_classify as eq  # noqa: E402
from test_equilibrium_discourse import _check_wire_invariants, _q  # noqa: E402

CLIMATE_TRAITS = {"voice.dissent", "voice.error_admission", "inquiry.challenge", "inquiry.answered",
                  "inquiry.unanswered", "response.dismissal", "response.engagement"}

# ---- G-C1: one thread carrying every climate trait ---------------------------
CLIMATE = [
    ("c01", "lead_l", "The cache is cold after every deploy.", None),
    ("c02", "member_m", "I disagree, the warmup job runs first.", "c01"),        # dissent (formula)
    ("c03", "lead_l", "Stay in your lane, trust me.", "c02"),                    # dismissal of dissent
    ("c04", "member_n", "The cache isn't cold, see https://example.org/warmup/3", "c01"),  # negated echo
    ("c05", "lead_l", "Fair point, I was wrong about the warmup.", "c04"),       # engagement + admission
    ("c06", "member_m", "What's the evidence for the cold cache?", "c01"),       # challenge (evidence req.)
    ("c07", "expert_e", "The p95 latency spike lines up with the deploy.", "c06"),  # answer + engagement
    ("c08", "member_n", "Who owns the warmup job?", "c01"),                      # never answered
    ("c09", "lead_l", "I was not wrong about the deploy order.", "c05"),         # negated admission (declared self-continuation: O2 tracking would else read it as the answer to c08)
    ("c10", "member_p", "Perhaps that's not the case for every deploy.", "c07"),  # hedged dissent
]


def _turns(rows):
    return [{"id": i, "actor_ref": a, "text": t, "reply_to": r} for i, a, t, r in rows]


@pytest.fixture(scope="module")
def base():
    s, root = eq.boot()
    return s, root, s.snapshot()


def _disc(base, rows, kind="thread"):
    _, root, snap = base
    turns = _turns(rows) if len(rows[0]) == 4 else [{"id": i, "actor_ref": a, "text": t} for i, a, t in rows]
    out = eq.discourse(snap.fork(), root, {"window_id": "w_climate", "kind": kind}, turns)
    _check_wire_invariants(out, turns)
    return out


def _climate(out):
    return {k: (v["match"], v["evidence"], v["counter_evidence"]) for k, v in _q(out).items()
            if k[1] in CLIMATE_TRAITS}


def _rules(out, key):
    return {r.split("@")[0] for r in _q(out)[key]["rule_ids"]}


def test_golden_climate_window(base):
    out = _disc(base, CLIMATE)
    assert _climate(out) == {
        ("member_m", "voice.dissent", "+", "lead_l"): ("partial", ["c02"], []),
        ("member_n", "voice.dissent", "+", "lead_l"): ("partial", ["c04"], []),
        ("member_p", "voice.dissent", "+", "expert_e"): ("partial", ["c10"], []),
        ("lead_l", "response.dismissal", "+", "member_m"): ("partial", ["c02", "c03"], []),
        ("lead_l", "response.engagement", "+", "member_n"): ("partial", ["c04", "c05"], []),
        ("lead_l", "voice.error_admission", "+", None): ("weak", ["c05"], ["c09"]),
        ("member_m", "inquiry.challenge", "+", "lead_l"): ("partial", ["c06"], []),
        ("expert_e", "inquiry.answered", "+", "member_m"): ("partial", ["c06", "c07"], []),
        ("expert_e", "response.engagement", "+", "member_m"): ("partial", ["c06", "c07"], []),
        ("member_n", "inquiry.unanswered", "+", None): ("partial", ["c08"], []),
    }
    msgs = {m["id"]: m for m in out["messages"]}
    # which dissent shape fired is auditable per turn
    assert msgs["c02"]["labels"]["msg.dissent"]["rule_ids"] == ["eq.msg.dissent.disagreement_cue@0.5.0"]
    assert msgs["c04"]["labels"]["msg.dissent"]["rule_ids"] == ["eq.msg.dissent.negated_echo@0.5.0"]
    assert "msg.dissent_hedged" in msgs["c10"]["labels"]
    assert "msg.error_admission_negated" in msgs["c09"]["labels"]
    assert "msg.error_admission" not in msgs["c09"]["labels"]
    assert _rules(out, ("member_n", "inquiry.unanswered", "+", None)) == {
        "eq.quanta.inquiry.unanswered", "eq.quanta.match.partial"}
    assert _rules(out, ("expert_e", "inquiry.answered", "+", "member_m")) == {
        "eq.quanta.inquiry.answered", "eq.quanta.match.partial"}


# ---- error admission: negation-aware -----------------------------------------
NEAR = [  # (text, labels that MUST fire, labels that must NOT fire)
    ("I was wrong about that.", {"msg.error_admission"}, {"msg.error_admission_negated"}),
    ("I was not wrong.", {"msg.error_admission_negated"}, {"msg.error_admission"}),
    ("I wasn't wrong about the deploy.", {"msg.error_admission_negated"}, {"msg.error_admission"}),
    ("It was not my mistake.", {"msg.error_admission_negated"}, {"msg.error_admission"}),
    ("I stand corrected.", {"msg.error_admission", "msg.concession"}, {"msg.error_admission_negated"}),
    ("Maybe I misread it.", {"msg.error_admission", "msg.error_admission_hedged"}, set()),
    ("You were wrong.", set(), {"msg.error_admission", "msg.error_admission_negated"}),
    ("I disagree.", {"msg.disagreement"}, {"msg.disagreement_negated"}),
    ("I don't disagree.", {"msg.disagreement_negated"}, {"msg.disagreement"}),
    ("Any source for that?", {"msg.evidence_request"}, {"msg.evidence_request_negated"}),
    ("I don't need a source.", {"msg.evidence_request_negated"}, {"msg.evidence_request"}),
    ("Open source is fine.", set(), {"msg.evidence_request"}),
]


def test_climate_cue_negation_near_misses(base):
    _, root, snap = base
    out = eq.classify(snap.fork(), root, [{"id": f"n{i}", "text": t} for i, (t, _y, _n) in enumerate(NEAR)])
    for o, (text, must, mustnt) in zip(out, NEAR):
        got = set(o["labels"])
        assert must <= got, (text, got)
        assert not (mustnt & got), (text, got)
        assert all(o["labels"][k]["status"] == "shadow" for k in got), text


def test_negated_error_admission_alone_mints_nothing(base):
    out = _disc(base, [("x1", "member_a", "I was not wrong.", None),
                       ("x2", "member_b", "I wasn't mistaken either.", "x1")])
    assert not any(k[1] == "voice.error_admission" for k in _q(out))


# ---- inquiry: answered vs unanswered ---------------------------------------
def test_answered_and_unanswered_questions(base):
    rows = [("q1", "member_a", "Is the queue drained?", None),
            ("a1", "member_b", "Yes, it drained an hour ago.", "q1"),       # substantive answer
            ("q2", "member_a", "Who restarts the workers?", None),
            ("a2", "member_b", "Why do you ask?", "q2"),                    # counter-question: not an answer
            ("q3", "member_a", "Can we roll back?", None),
            ("a3", "member_c", "That is ridiculous.", "q3"),                # hostile: dismissal, not an answer
            ("z1", "member_c", "The build is green.", None)]
    q = _climate(_disc(base, rows))
    assert q[("member_b", "inquiry.answered", "+", "member_a")] == ("partial", ["q1", "a1"], [])
    # the absence of an answer is read over the completed window (S2 after S1);
    # the asker's answered question is the counter-evidence
    assert q[("member_a", "inquiry.unanswered", "+", None)] == ("partial", ["q2", "q3"], ["q1"])
    assert q[("member_c", "response.dismissal", "+", "member_a")] == ("partial", ["q3", "a3"], [])
    assert q[("member_b", "response.engagement", "+", "member_a")] == ("partial", ["q2", "a2"], [])
    assert ("member_c", "inquiry.answered", "+", "member_a") not in q


def test_trailing_question_is_not_unanswered(base):
    """Absence is relative: nobody else posted after the question."""
    rows = [("s1", "member_a", "The cache is cold.", None),
            ("s2", "member_b", "Is it cold after every deploy?", "s1")]
    assert not any(k[1] == "inquiry.unanswered" for k in _climate(_disc(base, rows)))


def test_meeting_answer_is_tracked_not_adjacent(base):
    """0.5.0 (T3c O2): no declared replies, so the turn cursor TRACKS them: m2
    answers the open room question m1; m3 (a new question) responds to the address
    m2 made to its author; the withdrawal m5 responds to the most recent open
    question m4 but does NOT close it. The tracked meeting reproduces the
    declared-reply result exactly."""
    rows = [("m1", "member_a", "Did the deploy finish?"), ("m2", "member_b", "Yes, at noon."),
            ("m3", "member_a", "Who has the rollback plan?"), ("m4", "member_a", "Anyone?"),
            ("m5", "member_c", "Never mind, let's pause.")]  # withdrawal: not an answer
    out = _disc(base, rows, kind="meeting")
    assert {t["id"]: (t["responds_to"], t["basis"], t["answers"]) for t in out["turns"]} == {
        "m1": ([], "none", []), "m2": (["m1"], "tracked", ["m1"]), "m3": (["m2"], "tracked", []),
        "m4": ([], "none", []), "m5": (["m4"], "tracked", [])}
    assert out["open_questions"] == ["m3", "m4"]
    q = _climate(out)
    assert q[("member_b", "inquiry.answered", "+", "member_a")] == ("partial", ["m1", "m2"], [])
    assert q[("member_a", "inquiry.unanswered", "+", None)] == ("partial", ["m3", "m4"], ["m1"])
    decl = [r + (p,) for r, p in zip(rows, (None, "m1", None, None, "m4"))]
    assert _climate(_disc(base, decl, kind="meeting")) == q


# ---- response: dismissal vs engagement of dissent --------------------------
def test_dismissal_vs_engagement_of_dissent(base):
    rows = [("d1", "lead_l", "We ship it on Friday.", None),
            ("d2", "member_x", "I disagree, the tests are flaky.", "d1"),
            ("d3", "lead_l", "Trust me, in my 20 years this works.", "d2"),            # status, no grounding
            ("d4", "member_y", "I'm not convinced the rollback works.", "d1"),
            ("d5", "lead_l", "Good point, the rollback query timed out in staging.", "d4"),  # concession + tech
            ("d6", "member_z", "That's not true, Friday is a freeze.", "d1"),
            ("d7", "lead_l", "Ridiculous, see https://example.org/calendar", "d6")]   # hostile + link
    q = _climate(_disc(base, rows))
    assert q[("lead_l", "response.dismissal", "+", "member_x")] == ("partial", ["d2", "d3"], [])
    assert q[("lead_l", "response.engagement", "+", "member_y")] == ("partial", ["d4", "d5"], [])
    # a hostile reply carrying a link is a dismissal, never also engagement
    assert q[("lead_l", "response.dismissal", "+", "member_z")] == ("partial", ["d6", "d7"], [])
    assert ("lead_l", "response.engagement", "+", "member_z") not in q
    assert ("lead_l", "response.engagement", "+", "member_x") not in q
    assert {k[0] for k in q if k[1] == "voice.dissent"} == {"member_x", "member_y", "member_z"}


def test_status_reply_with_grounding_is_not_dismissal(base):
    rows = [("g1", "member_a", "Why is the p95 so high?", None),
            ("g2", "lead_l", "Trust me, the connection pool is exhausted.", "g1")]
    q = _climate(_disc(base, rows))
    assert ("lead_l", "response.dismissal", "+", "member_a") not in q
    assert ("lead_l", "response.engagement", "+", "member_a") in q
    assert ("lead_l", "inquiry.answered", "+", "member_a") in q


# ---- dissent / challenge near misses ---------------------------------------
def test_dissent_near_misses(base):
    rows = [("e1", "member_a", "The cache is not cold.", None),
            ("e2", "member_b", "The cache is not cold.", "e1"),       # agreeing restatement: echo is negated in e1
            ("e3", "member_c", "That is not the plan.", "e1"),        # negator + function word: no echo
            ("e4", "member_d", "I don't disagree.", "e1"),            # negated formula
            ("e5", "member_e", "But is it cold?", "e1")]              # contesting QUESTION: challenge, not dissent
    q = _climate(_disc(base, rows))
    assert not any(k[1] == "voice.dissent" for k in q)
    assert ("member_e", "inquiry.challenge", "+", "member_a") in q


def test_dissent_counter_from_negated_formula(base):
    rows = [("f1", "lead_l", "We ship it on Friday.", None),
            ("f2", "member_x", "I disagree, the tests are flaky.", "f1"),
            ("f3", "member_x", "Well, I don't disagree with the date.", "f1")]
    q = _climate(_disc(base, rows))
    assert q[("member_x", "voice.dissent", "+", "lead_l")] == ("weak", ["f2"], ["f3"])


# ---- vocabulary / status ---------------------------------------------------
def test_climate_traits_are_shadow_and_versioned(base):
    _, root, snap = base
    st = eq._label_status(snap.fork(), root)
    for t in CLIMATE_TRAITS:
        assert st[t]["status"] == "shadow" and st[t]["kind"] == "trait" and st[t]["since_pack"] == "0.4.0", t
    assert eq.PACK_VERSION == "0.5.0" and eq.TAXONOMY_VERSION == "eq-tax-0.5.0"
    climate = next(m for m in eq.pack_manifests() if m["id"] == "equilibrium_climate")
    assert {n["type"] for n in climate["nodes"]} == {"EqClimateCue"}
    assert {r["name"] for r in climate["rules"]} == {
        "eq.quanta.response.dismissal", "eq.quanta.response.engagement", "eq.quanta.inquiry.answered",
        "eq.quanta.inquiry.unanswered", "eq.quanta.inquiry.unanswered.counter"}


def test_disabling_a_climate_trait_is_data_only(base):
    """LabelStatus gate in the graph: flipping one row to disabled stops minting."""
    _, root, snap = base
    fork = snap.fork()
    n = eq._native(fork)
    for x in n.neighbours(root, "eq_has_label_status"):
        if n.node(x)["attrs"]["label"] == "inquiry.unanswered":
            n.set_attr(x, "status", "disabled")
    out = eq.discourse(fork, root, {"window_id": "w", "kind": "thread"}, _turns(CLIMATE))
    keys = set(_q(out))
    assert not any(k[1] == "inquiry.unanswered" for k in keys)
    assert ("expert_e", "inquiry.answered", "+", "member_m") in keys
