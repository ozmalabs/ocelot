"""Meaning-level review of a collapse reading (domains/reading_review.py).

reading_collapse.read_clause commits to the first shape-match: 'I could of done
that' grounds the nonsense possessive `[of, i_could, done_that]` with no flag. This
adds the review it lacked — a clean-but-nonsense shape ESCALATES across adjacency
domains until a near-neighbour re-decodes coherently, and the corruption's DOMAIN
EMERGES from the adjacency that resolved it. ONE mechanism, TWO error classes.

Discriminative gates (donkey = 0):

  * TRANSCRIPTION recovery (>=2 surface domains, domain emerges) — could of ->
    PHONOLOGY 'could have' (speech); freind -> KEYBOARD 'friend' (typing); tai1 ->
    GLYPH 'tail' (ocr).
  * COGNITIVE recovery (concept domain, SAME mechanism) — 'intensive purposes' ->
    CONCEPT 'intents and purposes' (cognitive).
  * NO FALSE REPAIR — a correctly-used possessive / concept scores LOW salience and
    is NOT escalated or repaired.
  * ORDER-N + SALIENCE — a multi-error text orders most-incoherent-first and RECURSES.
  * STOPS BY SUFFICIENCY — a coherent clause => 0 review passes.
  * GRAPH-NATIVE SOURCE AUDIT — order/escalate/pick/stop are seeded Programs; the
    adjacency is dimension-space structure; the re-decode is read_clause; no regex.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest tests/test_reading_review.py -p no:randomly -q
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core            # noqa: E402
from domains import dictionary_lexicon as dl          # noqa: E402
from domains import reading_collapse as rc            # noqa: E402
from domains import reading_review as rr              # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture(scope="module")
def agent():
    dl.warm_wordnet("en")
    s, node = boot_core()
    return _Agent(s, node)


# --------------------------------------------------------------------------- #
#  TRANSCRIPTION RECOVERY — >=2 surface domains, the domain EMERGES.
# --------------------------------------------------------------------------- #
def test_transcription_phonology_speech(agent):
    """'I could of done that': the faulty possessive is MOST salient -> ESCALATE ->
    PHONOLOGY-adjacent 'could have' re-decodes COHERENT -> domain=speech emerges."""
    r = rr.review_clause(agent, "I could of done that")
    assert r["reading"]["predications"] == [["of", "i_could", "done_that"]], r["reading"]
    assert r["salience"] > 0.5, r["salience"]                 # incoherent -> salient
    assert r["repaired"] is True, r["note"]
    rep = r["repair"]
    assert rep["domain"] == "speech", rep                     # the DOMAIN emerged
    assert rep["token"].lower() == "of" and rep["neighbor"].lower() == "have", rep
    assert rep["new_predications"] == [["could", "i", "have_done_that"]], rep
    # the ladder STAYED at the first (phonology) rung — no escalation past it.
    assert rep["ladder"][0]["domain"] == "speech", rep["ladder"]


def test_transcription_keyboard_typing(agent):
    """'the child hugged her freind': the non-word arg is salient -> ESCALATE ->
    (phonology has no neighbour) -> KEYBOARD-adjacent 'friend' coheres -> typing."""
    r = rr.review_clause(agent, "the child hugged her freind")
    assert r["repaired"] is True, r["note"]
    rep = r["repair"]
    assert rep["domain"] == "typing", rep
    assert rep["token"].lower() == "freind" and rep["neighbor"].lower() == "friend", rep
    assert rep["new_predications"] == [["hugged", "child", "her_friend"]], rep
    # it ESCALATED: phonology yielded nothing, keyboard resolved it.
    assert [x["domain"] for x in rep["ladder"]] == ["speech", "typing"], rep["ladder"]


def test_transcription_glyph_ocr(agent):
    """'the dog wagged its tai1': ESCALATE past phonology + keyboard -> GLYPH-adjacent
    'tail' (1<->l) coheres -> domain=ocr emerges."""
    r = rr.review_clause(agent, "the dog wagged its tai1")
    assert r["repaired"] is True, r["note"]
    rep = r["repair"]
    assert rep["domain"] == "ocr", rep
    assert rep["token"].lower() == "tai1" and rep["neighbor"].lower() == "tail", rep
    assert rep["new_predications"] == [["wagged", "dog", "its_tail"]], rep
    assert [x["domain"] for x in rep["ladder"]] == ["speech", "typing", "ocr"], rep["ladder"]


def test_two_surface_domains_distinct(agent):
    """The SAME review recovers errors from DIFFERENT surface domains — the domain is
    not fixed, it EMERGES from which adjacency resolves each."""
    doms = {rr.review_clause(agent, c)["repair"]["domain"]
            for c in ("I could of done that", "the child hugged her freind",
                      "the dog wagged its tai1")}
    assert {"speech", "typing", "ocr"} <= doms, doms


# --------------------------------------------------------------------------- #
#  COGNITIVE RECOVERY — the concept domain rides the SAME collapse.
# --------------------------------------------------------------------------- #
def test_cognitive_concept(agent):
    """'for all intensive purposes' reads THIN (grounds nothing) -> ESCALATE past
    every surface domain -> CONCEPT-adjacent 'intents and purposes' collapses out a
    coherent predication -> domain=cognitive emerges. Proves the concept domain is
    not a separate corrector — it is the last rung of the SAME ladder."""
    r = rr.review_clause(agent, "for all intensive purposes")
    assert r["repaired"] is True, r["note"]
    rep = r["repair"]
    assert rep["domain"] == "cognitive", rep
    assert rep["neighbor"].lower() == "intents and purposes", rep
    assert rep["new_predications"] == [["for", "all_intents", "purposes"]], rep
    # it escalated through ALL surface domains first — concept is the last rung.
    assert [x["domain"] for x in rep["ladder"]] == ["speech", "typing", "ocr", "cognitive"], rep["ladder"]


# --------------------------------------------------------------------------- #
#  NO FALSE REPAIR — a correct reading scores LOW salience and is NOT touched.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("clause,pred", [
    ("the capital of france", ["of", "capital", "france"]),
    ("the king of spain",     ["of", "king", "spain"]),
    ("the cat chased the mouse", ["chased", "cat", "mouse"]),
    ("the dog wagged its tail",   ["wagged", "dog", "its_tail"]),
    ("I gave it to her",          None),
])
def test_no_false_repair(agent, clause, pred):
    """A coherent possessive / event / prepositional-pronoun reading scores 0
    incoherence -> NOT escalated, NOT repaired. The review must not 'correct' a
    correct reading."""
    r = rr.review_clause(agent, clause)
    assert r["incoherence"] == 0.0, (clause, r["incoherence"], r["reading"])
    assert r["repaired"] is False, (clause, r["note"])
    if pred is not None:
        assert pred in r["reading"]["predications"], (clause, r["reading"])


# --------------------------------------------------------------------------- #
#  ORDER-N + SALIENCE — order most-incoherent-first, RECURSE (>=2 passes).
# --------------------------------------------------------------------------- #
def test_order_n_salience_and_recursion(agent):
    out = rr.review_text(agent, "the freind chased the mvoie. the dog wagged its tai1.")
    assert out["n_passes"] >= 2, out
    # PASS 1 ranks the two-error clause (incoherence 1.0) ABOVE the one-error clause.
    p1 = out["passes"][0]["ranking"]
    assert "freind" in p1[0]["clause"] and "tai1" in p1[1]["clause"], p1
    assert p1[0]["salience"] > p1[1]["salience"], p1          # most-incoherent first
    # it RECURSED to coherence: every error repaired, across >=2 adjacency domains.
    assert out["clauses"] == ["the friend chased the movie", "the dog wagged its tail"], out["clauses"]
    domains = {rp["domain"] for rp in out["repairs"]}
    assert {"typing", "ocr"} <= domains, out["repairs"]
    assert len(out["repairs"]) == 3, out["repairs"]


# --------------------------------------------------------------------------- #
#  STOPS BY SUFFICIENCY — coherent => 0 passes; faulty => repairs until coherent.
# --------------------------------------------------------------------------- #
def test_stops_by_sufficiency_coherent_zero_passes(agent):
    out = rr.review_text(agent, "the cat chased the mouse. the capital of france.")
    assert out["n_passes"] == 0, out
    assert out["repairs"] == [], out


def test_faulty_repairs_until_coherent(agent):
    out = rr.review_text(agent, "the dog wagged its tai1.")
    assert out["clauses"] == ["the dog wagged its tail"], out["clauses"]
    assert out["repairs"] and out["repairs"][0]["domain"] == "ocr", out["repairs"]


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE SOURCE AUDIT — decisions are Programs; adjacency is structure;
#  the re-decode is the collapse; NO regex.
# --------------------------------------------------------------------------- #
def test_source_audit_graph_native_no_regex():
    with open(os.path.join(ROOT, "domains", "reading_review.py")) as f:
        src = f.read()
    # the order / escalate / winner / stop are the seeded graph Programs (reused).
    assert "gap_priority" in src or "gap_prioritization" in src
    assert "review_escalate" in src and "candidate_pick" in src
    assert "should_continue" in src
    # the re-decode IS the collapse (reading_collapse.read_clause), never a parser.
    assert "read_clause" in src
    # NOT a from->to corrector: no regex module, no pattern ops.
    assert "\nimport re\n" not in src and "\nimport re " not in src
    for bad in ("re.compile", "re.search", "re.match", "re.findall", "re.split", "re.sub"):
        assert bad not in src, bad


def test_adjacency_is_seeded_dimension_space(agent):
    """The per-domain adjacency is seeded dimension-space STRUCTURE (a phonology set,
    the QWERTY layout, a glyph-confusable set, a concept-confusable set) — legitimate
    domain adjacency, not a hardcoded output map. A neighbour still WINS by re-decode."""
    rr.ensure_review_seed(agent)
    s = agent.s
    assert len(s.nodes("ReviewRung")) == 4                    # the domain ladder
    assert len(s.nodes("PhonologyPair")) >= 1
    assert len(s.nodes("GlyphPair")) >= 3
    assert len(s.nodes("ConceptPair")) >= 1
    assert len(s.nodes("KeyboardLayout")) == 1                # QWERTY as structure
    # the winning neighbour is decided by RE-DECODE coherence: the glyph set holds
    # 1<->l, but 'tail' only wins because re-decoding 'its tail' grounds coherently.
    nbrs = rr._neighbors_in_domain(s, "tai1", "glyph")
    assert "tail" in nbrs, nbrs


def test_escalation_is_the_seeded_program(agent):
    """The escalate-or-stay decision is the seeded review_escalate Program (the
    cascade_pick pattern over ReviewRung), evaluated in Rust — not a Python branch."""
    from domains import reflective_faculty as rf
    rr.ensure_review_seed(agent)
    prog = rf._load_program(agent.s, "review_escalate")
    native = agent.s._inner
    assert prog is not None
    # a coherent candidate (margin >= gate) STAYS at the current rung (domain emerges).
    assert native.evaluate(prog, {"margin": 1.0, "threshold": 0.5, "current": "phonology"}) == "phonology"
    # no candidate (margin -1) ESCALATES to the next rung.
    assert native.evaluate(prog, {"margin": -1.0, "threshold": 0.5, "current": "phonology"}) == "keyboard"


# =========================================================================== #
#  V2 — RICHER COHERENCE (cohere-in-CONTEXT), HOLD-OPEN LICENSING, FALSE FRIENDS.
#  The coherence measure forms MORE manifold than groundability: it reads the
#  RELATION's selectional fit to its arguments (a mental verb needs a sentient
#  subject; a physical verb cannot take a proposition) from the held sense faculty
#  (dictionary_lexicon.pick_sense — CURRENT-USAGE WordNet classes, NOT etymology).
#  The collapse is LICENSED only when the best candidate clears an absolute floor
#  and beats both its same-token runner-up and the token-as-itself by a margin;
#  otherwise it HOLDS OPEN (the anti-polygraph rule).
# =========================================================================== #


def test_hold_open_underformed_vs_wellformed(agent):
    """HOLD-OPEN discriminative gate, SAME token, SAME two groundable neighbours
    ('bat' animate / 'bet' inanimate), context decides. UNDER-FORMED: a perception
    verb does NOT disambiguate -> the two cohere within the margin -> HELD OPEN,
    flagged with candidates + confidences, NOT force-collapsed. WELL-FORMED: a
    COGNITION verb ('understood') selectionally excludes the inanimate 'bet' -> 'bat'
    is the unique context-fit neighbour -> LICENSED collapse."""
    under = rr.review_clause(agent, "she saw the bst")
    print("\nUNDER-FORMED  %r" % "she saw the bst")
    print("  ", under["note"])
    assert under["repaired"] is False and under["held_open"] is True, under
    cands = {c["neighbor"] for c in under["repair"]["candidates"]}
    assert {"bat", "bet"} <= cands, under["repair"]["candidates"]
    # both neighbours cohere ~equally: best and runner-up within the margin.
    assert under["repair"]["runnerup_coherence"] >= under["repair"]["coherence"] - 0.15, under["repair"]

    well = rr.review_clause(agent, "the bst understood the plan")
    print("WELL-FORMED   %r" % "the bst understood the plan")
    print("  ", well["note"])
    assert well["repaired"] is True and well["held_open"] is False, well
    rep = well["repair"]
    assert rep["token"].lower() == "bst" and rep["neighbor"].lower() == "bat", rep
    # licensed: the context-fit neighbour beats the runner-up by the margin.
    assert rep["coherence"] - rep["runnerup_coherence"] >= 0.15, rep


def test_richer_measure_catches_malapropism(agent):
    """The richer measure recovers a real-word malapropism groundability MISSED.
    BEFORE: 'the report infers that prices will rise' grounds (infer is a real verb,
    report a real noun) so groundability scores it 0 — NOT flagged. AFTER: the
    selectional fit sees the mental verb 'infers' with the inanimate subject 'report'
    (a report cannot infer) -> incoherent -> ESCALATE to the CONCEPT domain -> the
    context-fit neighbour 'implies' (a communication verb, which a report CAN do)
    re-decodes coherent -> recovered, domain=cognitive."""
    clause = "the report infers that prices will rise"
    read = rc.read_clause(agent, ["the", "report", "infers", "that", "prices", "will", "rise"], write=False)
    print("\nBEFORE (groundability only): incoherence %.2f  reading %s"
          % (rr.reading_incoherence(read), read["predications"]))
    assert rr.reading_incoherence(read) == 0.0                   # groundability passes it
    assert rr.selectional_incoherence(agent, read) > 0.0         # the richer measure flags it
    r = rr.review_clause(agent, clause)
    print("AFTER  (contextual fit):    incoherence %.2f  %s" % (r["incoherence"], r["note"]))
    assert r["repaired"] is True, r["note"]
    rep = r["repair"]
    assert rep["domain"] == "cognitive", rep
    assert rep["token"].lower() == "infers" and rep["neighbor"].lower() == "implies", rep
    assert rep["new_predications"] == [["implies", "report", "that_prices_will_rise"]], rep


@pytest.mark.parametrize("clause", [
    "the horse has a peculiar gait",     # gait fits -> NOT repaired to goat/gaot
    "he plays the bass",                 # instrument sense fits -> NOT repaired
    "he was chomping at the bit",        # CURRENT-USAGE correct -> NOT 'corrected' to champing
    "the noise will affect his sleep",   # correct 'affect' -> NOT repaired
])
def test_false_friend_direction_a_not_repaired(agent, clause):
    """DIRECTION A — a token that coheres-in-context AS ITSELF is NOT repaired, even
    when a commoner / 'more original' surface-adjacent word exists. The context
    LICENSES the token. Includes the etymology-vs-usage false friend: 'chomping at
    the bit' is current-usage-correct, so it is NOT collapsed to the etymological
    'champing' — correctness is anchored to living usage, not origin/authority."""
    r = rr.review_clause(agent, clause)
    print("\nDIR-A  %-34s selectional %.2f  combined %.2f  repaired=%s"
          % (repr(clause), rr.selectional_incoherence(agent, r["reading"]),
             r["incoherence"], r["repaired"]))
    # the contextual coherence that protects it: no selectional violation, groundable.
    assert r["incoherence"] == 0.0, (clause, r["reading"])
    assert r["repaired"] is False and r["held_open"] is False, (clause, r["note"])


def test_false_friend_direction_b_recovered(agent):
    """DIRECTION B — a token that grounds but does NOT cohere-in-context, where a
    neighbour DOES, is recovered. 'infers' grounds as a verb but violates its
    subject's animacy; 'implies' fits -> recovered (the malapropism crux)."""
    r = rr.review_clause(agent, "the report infers that prices will rise")
    print("\nDIR-B  %r -> %s" % ("the report infers that prices will rise", r["note"]))
    assert r["repaired"] is True and r["repair"]["neighbor"].lower() == "implies", r


def test_hold_open_over_garbage_repair(agent):
    """CALIBRATION / anti-polygraph: a thin no-predication reading ('a mute point')
    where the only 'improving' surface neighbours ground a NONSENSE predication by
    inserting a spurious token — the manifold is under-formed (the surface candidates
    tie and none dominates the token-as-itself with confidence). The review HOLDS
    OPEN rather than force the least-perturbation garbage repair."""
    r = rr.review_clause(agent, "a mute point")
    print("\nHOLD-OVER-GARBAGE  %r -> %s" % ("a mute point", r["note"]))
    assert r["repaired"] is False, r["note"]
    assert r["held_open"] is True, r["note"]


def test_calibration_no_overcorrection(agent):
    """The richer, more-sensitive measure must NOT start falsely repairing correct
    real-words. A correctly-used real word surface-adjacent to a commoner one, in a
    context that does not license a collapse, is LEFT (or held), never overcorrected.
    'the horse has a peculiar gait' is the temptation (gait ~ goat/gaot); it is left."""
    tempt = ["the horse has a peculiar gait", "he plays the bass",
             "the noise will affect his sleep"]
    for c in tempt:
        r = rr.review_clause(agent, c)
        assert r["repaired"] is False, (c, r["note"])   # not overcorrected


def test_selectional_and_license_are_seeded_graph(agent):
    """GRAPH-NATIVE audit for the v2 upgrades: the selectional restrictions are seeded
    dimension structure (SelectionalRestriction), and the licensing decision is the
    seeded review_license Program (Rust), not a Python branch. The contextual fit is
    read from the held sense faculty (pick_sense), not a hardcoded word->meaning map."""
    from domains import reflective_faculty as rf
    rr.ensure_review_seed(agent)
    s = agent.s
    kinds = {s.node(n)["attrs"].get("kind") for n in s.nodes("SelectionalRestriction")}
    assert {"animate_subject", "propositional_object"} <= kinds, kinds
    assert len(s.nodes("ReviewLicense")) == 1
    prog = rf._load_program(s, "review_license")
    native = s._inner
    assert prog is not None
    # LICENSED: best clears floor AND beats runner-up AND beats self by the margin.
    assert native.evaluate(prog, {"best": 1.0, "runnerup": 0.0, "self": 0.2,
                                  "margin": 0.15, "floor": 0.5}) is True
    # a two-way TIE (runner-up within the margin) is NOT licensed -> hold open.
    assert native.evaluate(prog, {"best": 1.0, "runnerup": 1.0, "self": 0.2,
                                  "margin": 0.15, "floor": 0.5}) is False


def test_richer_measure_no_regex_and_reads_held_faculty():
    """The contextual coherence is read from the held faculties (pick_sense for the
    sense class, is_nominal for clausal detection) — NOT a from->to word map, NOT
    regex. reading_review.py imports no regex module."""
    with open(os.path.join(ROOT, "domains", "reading_review.py")) as f:
        src = f.read()
    assert "pick_sense" in src                      # contextual fit via the held faculty
    assert "is_nominal" in src                      # clausal detection via the held faculty
    assert "review_license" in src and "selectional_incoherence" in src
    assert "\nimport re\n" not in src and "\nimport re " not in src
    for bad in ("re.compile", "re.search", "re.match", "re.findall", "re.split", "re.sub"):
        assert bad not in src, bad
