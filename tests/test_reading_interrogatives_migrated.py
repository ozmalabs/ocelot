"""test_reading_interrogatives_migrated — Deep-Reader Wave 1B: questions and
imperatives as first-class CONSTRUCTIONS the collapse reads, the same way
`domains/reading_collapse.py` already reads definitional/causal/enumeration prose.

Before this wave the codebook had no WH MarkerClass and no interrogative/imperative
construction — "What do you know about the moon?" minted garbage predications
(the wh-word and the main verb misread as nominal entities via the bare-SVO 'event'
fallback) and "Improve your grammar." produced an honest null (zero predications,
no skeleton marker at all: a clause-initial content verb was never recognised).

The fix is graph-DATA, not a Python classification ladder: two new marker classes
(WH, the fronted interrogative pro-form; AUXINV, the inverted subject-aux) plus one
new POSITIONALLY-synthesised marker (OBL, a question-scoped oblique preposition) and
four new `ShapeSignature{kind:'construction'}` entries
(`domain_data/reading_constructions.json`: wh_question / wh_question_oblique /
polar_question / imperative) the SAME `reflective_faculty.compose_design_for_goal`
(ShapeDecode) collapse decodes against. WHICH construction wins — hence
`speech_act`/`polar` — is read straight off that construction's own
`ground_template` data; the only Python added is (a) the POSITIONAL recognition of
the two new marker classes (structural, not semantic — see the extensive comments
in `reading_collapse._skeleton_from_words`) and (b) two new `_ground` MODES
('question'/'imperative') that mechanically re-derive the jammed subject+verb core
via the SAME held main-verb/head faculties the event-clause path already trusts.

Declarative reading is untouched: every one of the new markers is either a brand
new surface form no other class claims (WH's what/when/why/how) or fires ONLY when
a genuine subject-aux/wh-fronting structural signal holds (REL/COP repositioned to
WH/AUXINV only at the TRUE clause-initial boundary — never merely 'cur is empty',
which a determiner-as-subject like 'THIS is a test' would trip; OBL only once a
WH/AUXINV marker has already fired; the imperative fallback only when NO marker
fired anywhere AND the interior bare-SVO fallback ALSO found nothing). See
test_declarative_parity for the byte-identity gate.
"""
from __future__ import annotations

import json
import os

import pytest

from substrate.boot_core import boot_core
from domains import dictionary_lexicon as dl
from domains import reading_collapse as rc
from domains import comprehend_text as ct

_FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "speech_act_parity",
                        "speech_act.json")


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


def _fresh_agent():
    dl.warm_wordnet("en")
    s, node = boot_core()
    ag = _Agent(s, node)
    rc.ensure_codebook(ag)
    return ag


@pytest.fixture(scope="module")
def agent():
    return _fresh_agent()


# --------------------------------------------------------------------------- #
#  WH-QUESTION — "What do you know about the moon?"
# --------------------------------------------------------------------------- #
def test_wh_question_focus_and_no_junk_entities(agent):
    r = rc.read_clause(agent, "What do you know about the moon?", write=False, learn=True)
    assert r["speech_act"] == "question"
    assert not r["polar"]
    assert r["focus"] == "moon"
    assert r["addressee_role"] == "you"
    assert r["construction"] in ("wh_question", "wh_question_oblique")
    # the fix: no junk SmEntity-shaped nominal for the wh-word or the main verb —
    # every predication's arguments are drawn from {you, know/moon}, never
    # 'what'/'do'/'know' minted as a bare nominal (the pre-fix "do"/"what"/"you" /
    # "about"/"know"/"moon" garbage predications this wave replaces).
    assert r["predications"], "expected at least one predication"
    for pred in r["predications"]:
        rel, args = pred[0], pred[1:]
        assert "what" not in args and "do" not in args
        assert rel != "what" and rel != "do"
    assert ["know", "you", "moon"] in r["predications"]


def test_wh_question_bare_no_oblique(agent):
    for text in ("Who are you?", "What are you?"):
        r = rc.read_clause(agent, text, write=False, learn=True)
        assert r["speech_act"] == "question"
        assert not r["polar"]
        assert r["construction"] == "wh_question"
        assert r["addressee_role"] == "you"


# --------------------------------------------------------------------------- #
#  POLAR (yes/no) QUESTION — "Are you an LLM?", "Can you dance?"
# --------------------------------------------------------------------------- #
def test_polar_question_copula():
    ag = _fresh_agent()
    r = rc.read_clause(ag, "Are you an LLM?", write=False, learn=True)
    assert r["speech_act"] == "question"
    assert r["polar"] is True
    assert r["construction"] == "polar_question"
    assert r["addressee_role"] == "you"
    assert r["focus"] == "llm"
    assert ["is_a", "you", "llm"] in r["predications"]


def test_polar_question_modal():
    ag = _fresh_agent()
    r = rc.read_clause(ag, "Can you dance?", write=False, learn=True)
    assert r["speech_act"] == "question"
    assert r["polar"] is True
    assert r["construction"] == "polar_question"
    assert r["addressee_role"] == "you"
    assert ["dance", "you"] in r["predications"]


# --------------------------------------------------------------------------- #
#  IMPERATIVE (instruction) — "Improve your grammar.", "Read this: the cat sat."
# --------------------------------------------------------------------------- #
def test_imperative_predicate_and_object():
    ag = _fresh_agent()
    r = rc.read_clause(ag, "Improve your grammar.", write=False, learn=True)
    assert r["construction"] == "imperative"
    assert r["speech_act"] == "instruction"
    assert r["addressee_role"] == "you"
    assert r["focus"] == "grammar"
    assert ["improve", "you", "grammar"] in r["predications"]


def test_imperative_colon_clause_pronominal_object():
    # "Read this: the cat sat." — the colon separates the directive (matrix clause)
    # from its PAYLOAD; read_clause's speech-turn colon segmentation reads the
    # pre-colon clause as the imperative and surfaces the rest additively.
    ag = _fresh_agent()
    r = rc.read_clause(ag, "Read this: the cat sat.", write=False, learn=True)
    assert r["construction"] == "imperative"
    assert r["speech_act"] == "instruction"
    # 'this' is DET-class glue in every OTHER position (it modifies a following
    # noun); here it IS the object, and must survive as one — the pronominal-object
    # fix (reading raw words, not the glue-filtered content list, for the
    # imperative fallback).
    assert ["read", "you", "this"] in r["predications"]
    assert r["payload"] == "the cat sat."


def test_imperative_is_speech_turn_gated():
    """A bare verb-initial WORDS-LIST (a narrative clause fragment from the
    decompose/descent path — e.g. 'stop' quoted inside a fable) must NOT read as an
    imperative: the frozen reading-parity corpus fixes fragment-grain reading, and
    only a whole chat turn is a directive to the reader. The same clause as a
    STRING (a speech turn) is the imperative."""
    ag = _fresh_agent()
    frag = rc.read_clause(ag, ["improve", "your", "grammar"], write=False, learn=True)
    assert frag["construction"] != "imperative"
    assert frag["speech_act"] == "statement"
    turn = rc.read_clause(ag, "improve your grammar", write=False, learn=True)
    assert turn["construction"] == "imperative"


def test_event_predication_for_sentence_abstains_for_chat_clauses(agent):
    """The coref spine's fallback ladder (coref_entities.py:1758-1763) tries
    `event_predication_for_sentence` before `read_clause`; every one of the four
    target sentences must ABSTAIN (return []) there so read_clause's new
    construction handling is what actually grounds them, exactly the existing
    contract inverted-syntax clauses already rely on."""
    for text in ("What do you know about the moon?", "Improve your grammar.",
                "Are you an LLM?", "Can you dance?"):
        assert rc.event_predication_for_sentence(agent, text) == []


# --------------------------------------------------------------------------- #
#  DECLARATIVE PARITY — kind=statement is the default; every pre-existing
#  construction reads BYTE-IDENTICALLY (construction/skeleton/predications) to
#  before this wave. Captured against the committed HEAD baseline of
#  reading_collapse.py/reading_constructions.json (see the commit this test ships
#  in for the exact before/after diff) and hardcoded here so the gate has no
#  runtime dependency on git.
# --------------------------------------------------------------------------- #
_DECLARATIVE_PARITY = [
    # (sentence, expected construction, expected skeleton, expected predications)
    ("The crow dropped the pebbles into the pitcher.", "event", [["VERB"]],
     [["dropped", "crow", "pebbles_into_pitcher"]]),
    ("This is a test.", "definitional", [["COP"]], []),
    ("The sky is blue.", "definitional", [["COP"]], [["is_a", "sky", "blue"]]),
    ("A computer includes a CPU, memory, and storage.", "enumeration_includes",
     [["INCL"]], [["part_of", "cpu_memory", "computer"],
                  ["part_of", "storage", "computer"]]),
    ("Igneous rock is rock formed from magma.", "definitional", [["COP"], ["FROM"]],
     [["is_a", "igneous_rock", "rock_formed"]]),
    # a REL word ('how') mid-clause (an embedded complementizer, NOT a fronted
    # question) must stay exactly what it always was — content, not a WH marker.
    ("no matter how he tried the crow could not reach the water", "event",
     [["VERB"]], None),  # exact predication not asserted; only the construction/
                         # skeleton (the WH-mid-clause non-regression) matters here
]


@pytest.mark.parametrize("text,exp_construction,exp_skeleton,exp_preds", _DECLARATIVE_PARITY)
def test_declarative_parity(text, exp_construction, exp_skeleton, exp_preds):
    ag = _fresh_agent()
    r = rc.read_clause(ag, text, write=False, learn=True)
    assert r["construction"] == exp_construction
    assert r["skeleton"] == exp_skeleton
    if exp_preds is not None:
        assert r["predications"] == exp_preds
    # additive-only: speech_act defaults to 'statement' for every pre-existing
    # construction (none of these end '?').
    assert r["speech_act"] == "statement"
    assert r["focus"] is None
    assert r["addressee_role"] is None
    assert r["polar"] is False


# --------------------------------------------------------------------------- #
#  CORPUS AGREEMENT — the 133 chat-shaped utterances in
#  tests/fixtures/speech_act_parity/speech_act.json (READ-ONLY fixture). Every
#  utterance's `text` is read through read_clause; `speech_act` is compared
#  against the fixture's recorded `kind`. fastpath/meta rows are EXCLUDED from
#  the floor (the mission's own carve-out: those routes may legitimately diverge
#  from a purely structural reader — a pragmatic/dispatch-level classification,
#  not a construction-shape fact); they are still counted in the printed totals.
# --------------------------------------------------------------------------- #
def _load_corpus():
    with open(_FIXTURE) as f:
        data = json.load(f)
    out = []
    for cat, items in data["corpus"].items():
        for it in items:
            out.append((cat, it))
    return out


def test_corpus_agreement_floor(agent, capsys):
    corpus = _load_corpus()
    total = agree = 0
    gen_total = gen_agree = 0
    disagreements = []
    for cat, it in corpus:
        text = it["text"]
        expected = it["kind"]
        r = rc.read_clause(agent, text, write=False, learn=True)
        got = r["speech_act"]
        ok = got == expected
        total += 1
        agree += int(ok)
        is_general = not it.get("fastpath") and it.get("dispatch_path") != "meta"
        if is_general:
            gen_total += 1
            gen_agree += int(ok)
        if not ok:
            disagreements.append((cat, text, expected, got,
                                  it.get("fastpath"), it.get("dispatch_path")))

    print(f"\nspeech_act corpus agreement: {agree}/{total} = {agree / total:.1%} "
         f"(all rows); {gen_agree}/{gen_total} = {gen_agree / gen_total:.1%} "
         f"(general-path, excl. fastpath/meta)")
    print("DISAGREEMENTS (for Wave 2's divergence work):")
    for cat, text, expected, got, fastpath, dispatch_path in disagreements:
        print(f"  [{cat}] fastpath={fastpath} dispatch={dispatch_path!r} "
             f"expected={expected!r} got={got!r} :: {text!r}")

    # floor: measured 94.3% general-path agreement at authoring time (99/105; the
    # remaining disagreements are recorded-taxonomy differences — imperative-form
    # utterances the comp ladder files as 'question' for satisfiable/table dispatch
    # ('Name/Show/List/Enumerate your ...'), and politeness-prefixed turns whose
    # strip lives in comprehend_text (Wave 2's join). Assert a conservative floor
    # with margin, not the measured ceiling, so unrelated sibling-module drift
    # (comprehend_text/consumption_quality tokenisation) does not flake this gate.
    assert gen_total > 0
    assert gen_agree / gen_total >= 0.85, (
        f"general-path speech_act agreement dropped below floor: "
        f"{gen_agree}/{gen_total} = {gen_agree / gen_total:.1%}")
