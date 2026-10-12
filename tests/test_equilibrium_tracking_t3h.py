"""eq-tax-0.8.0 T3h: tracking bugs / issues (graph-native rules; synthetic data only).

  * bounded candidate sets BY CONSTRUCTION (no 500 on big channels): reply candidates
    <= 4 + 3 x len(addressees); topic candidates <= 4 (the room's MaxQUD, KoS).
  * interrogative SYNTAX without '?' (speech transcripts): subject-aux inversion, wh +
    inverted auxiliary, tag questions, after turn prefaces.
  * held reply resolution grounded in conversation analysis: continuers (Schegloff 1982)
    are not the turn the speaker's continuation follows; in SPEECH a non-FPP selection
    lapses at the next transition-relevance place (SSJ 1974 rule 1); a sequence-closing
    third by the first-pair-part speaker (Schegloff 2007 ch.7) ratifies the pair.
Pseudonyms only (ana / bea / cy / dov / u<i>); no corpus, no LLM.
"""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("OZMA_NO_LLM", "1")

import test_equilibrium_tracking as trk  # noqa: E402
from domains import equilibrium_classify as eq  # noqa: E402
from equilibrium_delta_fold import DeltaFold  # noqa: E402

HELLO = trk.HELLO
base = trk.base
srv_svc = trk.srv_svc
_disc, _rows, _cands, _topic, _turns = trk._disc, trk._rows, trk._cands, trk._topic, trk._turns


def _wire(svc, cid, kind, rows, sizes=None):
    """stream rows through the service (the wire re-shape raises on any contract
    violation -- the old 500); returns the outputs"""
    turns, outs, i = _turns(rows), [], 0
    sizes = sizes or [len(turns)]
    k = 0
    while i < len(turns):
        n = sizes[min(k, len(sizes) - 1)]
        outs.append(svc.conversation_turns(cid, kind, turns[i:i + n]))
        i, k = i + n, k + 1
    return outs


def _fold_equals_one_shot(svc, name, rows, kind):
    """(as trk.test_fold_turns_delta_equals_one_shot_at_every_prefix, for any kind)"""
    revised = 0
    for size in range(1, len(rows) + 1):
        outs = _wire(svc, f"t3h:fold:{name}:{size}", kind, rows, [size])
        f = DeltaFold()
        f.turns(_turns(rows))
        for k, o in enumerate(outs, 1):
            f.apply(o)
            revised += len(o["turns_delta"])
            upto = min(k * size, len(rows))
            one = eq.discourse(*trk._fork(svc), {"window_id": "w", "kind": kind}, _turns(rows[:upto]))
            assert f.structure() == trk._structure(svc, one), (name, size, upto)
        f.apply(svc.conversation_close(f"t3h:fold:{name}:{size}"))
    return revised


# ---- issue 2: bounds by construction ---------------------------------------------------
def test_big_channel_room_questions_never_500_and_bounded(srv_svc):
    """60 actors each ask a ROOM question in one undeclared channel (each asker's question
    stays live on its pointer), then a 61st actor speaks, then a turn names 20 earlier
    speakers. 0.8.0 had O(actors) topic candidates and 3 per named addressee reply
    candidates against a fixed 16 cap (a 500). Now: topic candidates <= 4 (the room's
    MaxQUD is the room source), reply candidates <= 4 + 3 x len(addressees), and every
    emitted row passes the wire invariants."""
    from services.equilibrium_classifier import server
    rows = [(f"q{i}", f"u{i}", f"What do you all think about option {i}?") for i in range(60)]
    rows += [("z1", "zed", "I like the second one."),
             ("z2", "yan", " ".join(f"u{i}" for i in range(20)) + " please vote today.")]
    outs = _wire(srv_svc, "t3h:big", "channel", rows, [25])
    outs.append(srv_svc.conversation_close("t3h:big"))
    turns = {t["id"]: t for o in outs for t in o["turns"]}
    for row in [t for o in outs for t in o["turns"]] + [d for o in outs for d in o["turns_delta"]]:
        assert server.structure_violation(row) is None
        assert len(row["topic_candidates"]) <= server.MAX_TOPIC_CANDIDATES == 4
        assert len(row["candidates"]) <= 4 + 3 * len(row["addressees"])
    # the 61st actor's turn: its room issue is the latest room question (MaxQUD); the rest
    # come via its reply parent (q59 itself, and q59's own topic)
    z1 = {c["ref"] for c in turns["z1"]["topic_candidates"]}
    assert "q59" in z1 and len(z1) <= 4
    # 20 named addressees: well past the old cap of 16, never a 500
    assert len(turns["z2"]["addressees"]) == 20
    assert len(turns["z2"]["candidates"]) > 16


def test_older_room_issue_is_maxqud_again_after_downdate(base):
    """KoS: the newer room question is the room's MaxQUD; once it is RESOLVED by the
    type-conforming answer (and downdated), the older live room question is the room
    source again -- it never lapsed."""
    rows = HELLO + [("o1", "ana", "What is blocking the release?"),
                    ("o2", "cy", "Is the demo at three?"),
                    ("o3", "dov", "Yes, at three."),
                    ("o4", "bea", "The flaky test is blocking it.")]
    out = _disc(base, rows)
    assert _topic(out, "o3")[0] == "o2"  # o2 is the room's MaxQUD (o1 comes only via o2's topic)
    assert _topic(out, "o4") == ("o1", {"o1": ["open_question"]})  # o2 downdated: o1 is top again


def test_candidate_bound_is_checked_on_the_wire():
    from services.equilibrium_classifier import server
    row = {"id": "z9", "responds_to": [], "basis": "held", "confidence": "held", "addressees": [],
           "thread_id": "z9", "answers": [], "topic_id": None, "topic_candidates": [],
           "candidates": [{"ref": f"x{i}", "cues": ["adjacent"]} for i in range(5)]}
    assert server.structure_violation(row) == "too many candidates"
    assert server.structure_violation(dict(row, addressees=["a"])) is None
    many = [{"ref": f"k{i}", "cues": ["open_question"]} for i in range(5)]
    assert server.structure_violation(dict(row, candidates=row["candidates"][:2], topic_candidates=many))


# ---- issue 3: interrogative syntax without '?' ----------------------------------------
INTERROGATIVES = ["so do you think it works", "um what do you think", "okay and is it red",
                  "how many buttons do we need", "it is a bit big isn't it", "where's the remote",
                  "yeah well can we make it smaller", "i think it's fine but what do you think about it"]
# (the interrogative rule must not fire; the pre-existing ladder's own wh-focus reading of
# a pseudo-cleft is not this rule's concern)
DECLARATIVES = ["i think we need a bigger button", "what we need is a scroll wheel",
                "when we finish we can go", "that is the one", "okay so the remote is done",
                "yeah", "how it works is simple", "so do i", "it is the red one isn't it the"]


def _acts(svc, cid, kind, texts, rule=False):
    out = svc.conversation_turns(cid, kind, [{"id": f"t{i}", "actor_ref": ("ana", "bea")[i % 2], "text": x}
                                             for i, x in enumerate(texts)])
    svc.conversation_close(cid)
    if rule:
        return [any("speech_act.interrogative" in r for r in t["labels"]["rule_ids"]) for t in out["turns"]]
    return [t["labels"].get("speech_act") for t in out["turns"]]


def test_interrogative_syntax_marks_questions_without_a_question_mark(srv_svc):
    assert _acts(srv_svc, "t3h:q", "meeting", INTERROGATIVES) == ["question"] * len(INTERROGATIVES)
    assert not any(_acts(srv_svc, "t3h:d", "meeting", DECLARATIVES, rule=True))


def test_typed_questions_and_statements_unchanged(srv_svc):
    """text: the typed '?' ladder is unchanged; a statement stays one speech act"""
    acts = _acts(srv_svc, "t3h:text", "channel", ["Is the build green?", "The build is green.",
                                                  "What time is it?"])
    assert acts == ["question", "assertion", "question"]


# ---- issue 1: held resolution grounded in conversation analysis -----------------------
def test_continuer_is_not_the_turn_a_continuation_follows(base):
    """SPEECH: ana talks, bea's 'mm-hmm' is a continuer, ana continues: ana's continuation
    follows her own talk (adjacent = her run's prior turn, cy's), not the continuer."""
    rows = HELLO + [("c1", "cy", "The budget is twelve euros."), ("c2", "ana", "We need a cheaper case."),
                    ("c3", "bea", "Mm-hmm."), ("c4", "ana", "And fewer buttons.")]
    out = _disc(base, rows, kind="meeting")
    assert _cands(out, "c4") == {"c1": ["adjacent"]}
    assert _cands(out, "c3") == {"c2": ["adjacent"]}  # the continuer itself follows ana
    # a response token right after a QUESTION is its answer, not a continuer
    rows = HELLO + [("c1", "ana", "Is the case blue?"), ("c2", "bea", "Yeah."), ("c3", "ana", "Okay.")]
    assert "c2" in _cands(_disc(base, rows, kind="meeting"), "c3")


def test_non_fpp_selection_lapses_in_speech_not_in_text(base):
    """bea addresses ana with an ASSERTION; cy then takes the floor; ana speaks. SPEECH:
    the selection lapsed at the next transition-relevance place (SSJ 1974 rule 1) -- the
    address is no candidate. TEXT (quasi-synchronous): it persists. A QUESTION keeps the
    response conditionally relevant in both."""
    rows = HELLO + [("a1", "bea", "Ana, the build passed."), ("a2", "cy", "Lunch is at noon."),
                    ("a3", "ana", "Great news.")]
    assert set(_cands(_disc(base, rows, kind="meeting"), "a3")) == {"a2"}
    assert set(_cands(_disc(base, rows, kind="channel"), "a3")) == {"a1", "a2"}
    rows[4] = ("a1", "bea", "Ana, did the build pass?")
    assert "a1" in _cands(_disc(base, rows, kind="meeting"), "a3")


SCT = HELLO + [("s1", "bea", "Ana, is the build green?"), ("s2", "cy", "The demo is at three."),
               ("s3", "ana", "Yes, it passed."), ("s4", "bea", "Okay.")]


def test_sequence_closing_third_ratifies_the_pair(srv_svc):
    """SPEECH: ana's polar answer s3 is held between bea's question s1 (slot / answer form)
    and cy's adjacent s2. bea -- the question's speaker -- closes the sequence with a
    minimal post-expansion ('Okay.', Schegloff 2007 ch.7): s3 is the second pair part of
    s1, so cy's s2 is ruled out and s3 collapses onto s1 (turns_delta), answering it."""
    outs = _wire(srv_svc, "t3h:sct", "meeting", SCT, [len(SCT) - 1, 1])
    s3 = next(t for t in outs[0]["turns"] if t["id"] == "s3")
    assert s3["basis"] == "held" and {c["ref"] for c in s3["candidates"]} == {"s1", "s2"}
    d = {x["id"]: x for x in outs[1]["turns_delta"]}["s3"]
    assert (d["responds_to"], d["basis"], d["confidence"], d["answers"]) == (["s1"], "tracked", "strong", ["s1"])
    assert [c["ref"] for c in d["candidates"]] == ["s1"] and "uptake" in d["candidates"][0]["cues"]
    srv_svc.conversation_close("t3h:sct")
    # a continuer by the asker, or a closing third by someone else, does not ratify
    for last in (("s4", "bea", "Mm-hmm."), ("s4", "dov", "Okay.")):
        out = _disc(trk_base(srv_svc), SCT[:-1] + [last], kind="meeting")
        assert _rows(out, {"s3"})["s3"][1] == "held", last


def trk_base(svc):
    return (None, svc.root, svc.snap)


def test_sct_fold_equals_one_shot(srv_svc):
    assert _fold_equals_one_shot(srv_svc, "sct", SCT, "meeting")
