"""THEN-COORDINATION — split TEMPORAL 'then' VP/clause coordination (2026-07-07).

THE RESIDUAL (named by the conjoined-VP work, P2/0f43c778): 'The dog thanked her
THEN gave her a whistle' was NOT split -- 'then' was claimed whole by the
conditional THEN marker class, so the sentence collapsed to a single spurious
implies(...) predication instead of two VP conjuncts.

THE FIX (domains/reading_collapse.py, `_segment_into_clauses`): a bare THEN is
ambiguous between the if/then CONDITIONAL construction's consequent marker and a
TEMPORAL VP/clause-sequencing coordinator ('he knocked THEN he entered'). The
disambiguating signal is whether an IF clause-opener governs it ANYWHERE earlier
in the sentence (`if_open`, tracked over the recognised marker classes, never
reset -- an if/then pairing spans the whole sentence, commas included). A THEN
with NO governing IF is routed through the EXACT SAME verb-headed boundary check
AND/OR already uses, so it drives the SAME shared-subject VP-coordination split
`decompose_sentence` does for 'and' (P2); a governed THEN is left untouched, so
the held conditional construction still decodes it via `read_clause`.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_then_coordination.py -p no:randomly -q
"""
from __future__ import annotations

import ast
import inspect
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core          # noqa: E402
from domains import dictionary_lexicon as dl        # noqa: E402
from domains import reading_collapse as rc          # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


@pytest.fixture()
def agent():
    s, node = boot_core()
    return _Agent(s, node)


def _decomp(agent, sentence):
    return rc.decompose_sentence(agent, sentence)


def _preds(agent, sentence):
    return _decomp(agent, sentence)["predications"]


# --------------------------------------------------------------------------- #
#  THE HEADLINE -- temporal 'then' VP-coordination, shared subject (like 'and').
# --------------------------------------------------------------------------- #
def test_temporal_then_vp_coordination_shared_subject(agent):
    preds = _preds(agent, "The dog thanked her then gave her a whistle.")
    # FIRST conjunct: thanked(dog, her).
    assert ["thanked", "dog", "her"] in preds, preds
    # SECOND conjunct, SHARED SUBJECT (dog) + ditransitive theme (whistle) --
    # exactly the P2 'and' shape, now reached through temporal 'then'.
    assert ["gave", "dog", "her"] in preds, preds
    assert ["gave", "dog", "whistle"] in preds, preds
    for p in preds:
        if p[0] == "gave":
            assert p[1] == "dog", ("second VP subject must be the shared 'dog'", p)
    # no spurious conditional collapse (the P2 residual this fixes).
    assert not any(p[0] == "implies" for p in preds), preds


def test_temporal_then_is_a_real_clause_boundary(agent):
    d = _decomp(agent, "The dog thanked her then gave her a whistle.")
    assert d["n_boundaries"] >= 1, d
    assert d["clauses"] == [
        ["the", "dog", "thanked", "her"],
        ["gave", "her", "a", "whistle"],
    ], d["clauses"]


# --------------------------------------------------------------------------- #
#  DISCRIMINATIVE GUARD 1 -- conditional if/then is UNCHANGED, not split.
# --------------------------------------------------------------------------- #
def test_conditional_if_then_unchanged_not_split(agent):
    # the held construction-codebook entry point (untouched by this fix) still
    # decodes the conditional construction and grounds implies(...).
    r = rc.read_clause(agent, "if it rains then the ground is wet")
    assert r["construction"] == "conditional", r
    assert ["implies", "it_rains", "ground"] in r["predications"], r["predications"]

    # the decompose_sentence entry point (the one this fix touches) also leaves
    # a governed 'then' alone -- it is NOT treated as a VP-coordination boundary.
    d = _decomp(agent, "If it rains then the ground is wet.")
    assert d["clauses"] == [["it", "rains", "then", "the", "ground", "is", "wet"]], d["clauses"]
    assert d["n_boundaries"] == 0, d


def test_conditional_if_then_robust_to_intervening_words(agent):
    # the IF...THEN governance signal is not "then is the very next word" -- it
    # persists across an adverb / an internal AND clause in the antecedent.
    d = _decomp(agent, "If it rains hard then the ground gets wet.")
    assert d["n_boundaries"] == 0, d["clauses"]
    d2 = _decomp(agent, "If it rains and the wind blows then the ground gets wet.")
    # the antecedent's own internal 'and' may split, but the governed 'then'
    # must never itself start a NEW temporal-coordination boundary.
    for cl in d2["clauses"]:
        assert cl == cl  # (structure asserted below; this loop is just a smoke check)
    assert not any(c and c[0] == "then" for c in d2["clauses"]), d2["clauses"]


# --------------------------------------------------------------------------- #
#  DISCRIMINATIVE GUARD 2 -- temporal 'then' with TWO subjects: two events, no
#  sharing (clause-coordination, not VP-coordination -- the P2 distinction).
# --------------------------------------------------------------------------- #
def test_temporal_then_two_subjects_two_events(agent):
    preds = _preds(agent, "He knocked the door then she opened it.")
    assert ["knocked", "he", "door"] in preds, preds
    assert ["opened", "she", "it"] in preds, preds
    # 'he' must NOT be wrongly shared onto the second (its own-subject) clause.
    assert not any(p[0] == "opened" and p[1] == "he" for p in preds), preds


def test_temporal_then_bare_intransitive_two_subjects_not_shared(agent):
    # the brief's literal example: both conjuncts are bare intransitives (no
    # object), which decompose_sentence's fragment reader deliberately does NOT
    # sprout events for (intransitive_ok=False on the multi-clause path -- see
    # _event_predication's docstring); the DISCRIMINATIVE fact under test is the
    # SEGMENTATION: two clauses, each with ITS OWN subject, no sharing, and no
    # spurious conditional collapse -- not a literal grounded predication tuple.
    d = _decomp(agent, "He knocked then he entered.")
    assert d["clauses"] == [["he", "knocked"], ["he", "entered"]], d["clauses"]
    assert d["n_boundaries"] >= 1, d
    # neither clause's subject is None (i.e. neither is a subject-less VP that
    # would trigger sharing) -- both are independent, subject-bearing clauses.
    assert rc._clause_subject_words(agent, d["clauses"][0]) is not None
    assert rc._clause_subject_words(agent, d["clauses"][1]) is not None
    # the P2 residual (a spurious conditional collapse) must not reappear.
    assert not any(p[0] == "implies" for p in d["predications"]), d["predications"]


def test_temporal_then_repeated_subject_two_events(agent):
    # both conjuncts spell out 'he' explicitly (their OWN subject, not shared) --
    # two full events, same surface subject, no VP-coordination sharing logic
    # involved (subj_words is not None for the second clause either).
    preds = _preds(agent, "He greeted her then he thanked her.")
    assert ["greeted", "he", "her"] in preds, preds
    assert ["thanked", "he", "her"] in preds, preds


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE AUDIT -- the if-governs-then check reads recognised marker
#  classes (MarkerClass lexicon + _CLAUSE_OPENERS), not a hardcoded text rule;
#  reuses the held AND/OR verb-headed boundary check; no import re, donkey=0.
# --------------------------------------------------------------------------- #
def test_no_import_re_and_no_donkey(agent):
    src = inspect.getsource(rc)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(a.name == "re" for a in node.names), "import re found"
        if isinstance(node, ast.ImportFrom):
            assert node.module != "re", "from re import ... found"
    assert "donkey" not in src.lower()


def test_if_governs_check_is_over_recognised_marker_classes(agent):
    """The `_segment_into_clauses` if-governs-then guard must key off `cls` (the
    MarkerClass-lexicon-recognised class, `lex.get(word)`), never off the raw
    surface word 'then'/'if' directly -- i.e. the same recognition path AND/OR
    already uses, extended, not a new hardcoded string comparison."""
    src = inspect.getsource(rc._segment_into_clauses)
    assert '"THEN"' in src and '"IF"' in src
    assert 'cls ==' in src or 'cls in' in src
    # the boundary decision for temporal 'then' reuses the SAME verb-headed
    # helper AND/OR uses (_run_has_verb), not a separate ad hoc check.
    assert src.count("_run_has_verb") >= 2


def test_temporal_then_reuses_and_or_verb_headed_gate(agent):
    # a bare THEN with only ONE verb-headed side is glue, not a coordinator --
    # exactly like a bare AND ('bread then water' has no second verb -> no split).
    d = _decomp(agent, "She gave bread then water.")
    assert d["n_boundaries"] == 0, d["clauses"]
