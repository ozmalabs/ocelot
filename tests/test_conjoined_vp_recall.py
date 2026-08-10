"""CONJOINED-VP RECALL — recover the DROPPED SECOND CONJUNCT (2026-07-07).

THE CEILING (named by the throughlines work, 762a0352): a conjoined verb phrase
'The dog thanked her AND gave her a whistle' dropped the second conjunct -- the
reader returned only thanked(dog, her), so the gift 'whistle' never registered.
This blocked the causal PAYOFF throughline (the gifts never appeared in the
helping arcs) and lost events everywhere.

THE FIX (graph-native, reusing the held faculties in domains/reading_collapse.py):

  1. VP-COORDINATION recognition. A clause with TWO verb phrases joined by a
     coordinator ('and'/'then') where the SECOND VP has no explicit subject SHARES
     the first VP's subject. The signal is the held _clause_subject_words faculty
     (main verb via the held is_verb_headed POS Term; a verb-initial clause has no
     subject of its own) -- NOT a hardcoded splitter. The shared subject is the
     first VP's subject word-run, prepended so the second conjunct binds to it.

  2. DITRANSITIVE THEME. 'gave her a whistle' is a double-object frame (recipient
     'her' + theme 'whistle'); the theme -- the transferred gift the single-object
     read drops -- surfaces as its OWN binary predication [verb, subj, theme], so
     the gift registers as a patient. The preposition guard keeps a monotransitive
     + PP ('dropped them INTO the pitcher') from being mis-read as ditransitive.

Discriminative: VP-coordination (two verbs, one subject -> shared subject + both
predications) is distinguished from CLAUSE-coordination (two subjects, unchanged)
and NP-coordination (conjoined object, no spurious verb).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_conjoined_vp_recall.py -p no:randomly -q
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


def _preds(agent, sentence):
    return rc.decompose_sentence(agent, sentence)["predications"]


# --------------------------------------------------------------------------- #
#  THE HEADLINE — the conjoined gift clause keeps BOTH predications, subject shared.
# --------------------------------------------------------------------------- #
def test_conjoined_vp_keeps_both_predications_with_shared_subject(agent):
    preds = _preds(agent, "The dog thanked her and gave her a whistle.")
    # FIRST conjunct: thanked(dog, her).
    assert ["thanked", "dog", "her"] in preds, preds
    # SECOND conjunct, SHARED SUBJECT (dog) + ditransitive theme (whistle):
    # gave(dog, her) [recipient] AND gave(dog, whistle) [theme] -- together the
    # ditransitive gave(dog, her, whistle). The gift 'whistle' now registers.
    assert ["gave", "dog", "her"] in preds, preds
    assert ["gave", "dog", "whistle"] in preds, preds
    # the shared subject of the second VP is the FIRST VP's subject.
    for p in preds:
        if p[0] == "gave":
            assert p[1] == "dog", ("second VP subject must be the shared 'dog'", p)


def test_gift_theme_registers_for_each_arc(agent):
    # the three helping arcs' gift clauses each recover their theme (whistle /
    # feather / lantern) -- the objects the payoff throughline needs.
    for helper, gift in (("dog", "whistle"), ("bird", "feather"), ("family", "lantern")):
        preds = _preds(agent, "The %s thanked her and gave her a %s." % (helper, gift))
        assert ["thanked", helper, "her"] in preds, (helper, preds)
        assert ["gave", helper, gift] in preds, (gift, preds)


# --------------------------------------------------------------------------- #
#  DISCRIMINATIVE — VP-coord vs CLAUSE-coord vs NP-coord.
# --------------------------------------------------------------------------- #
def test_clause_coordination_two_subjects_unchanged(agent):
    # two TRANSITIVE clauses, each with its OWN subject -> two predications, no
    # subject sharing (the second clause 'the cat climbed the tree' keeps 'cat').
    preds = _preds(agent, "The dog chased the cat and the cat climbed the tree.")
    assert ["chased", "dog", "cat"] in preds, preds
    assert ["climbed", "cat", "tree"] in preds, preds
    # 'dog' is NOT wrongly shared onto the second clause's verb.
    assert not any(p[0] == "climbed" and p[1] == "dog" for p in preds), preds


def test_np_coordination_conjoined_object_no_spurious_verb(agent):
    # 'bread and water' is a conjoined OBJECT (role glue), not a second VP -> ONE
    # predication with a single verb; no second verb-headed predication is invented.
    preds = _preds(agent, "She gave bread and water.")
    verbs = [p[0] for p in preds]
    assert verbs.count("gave") <= 1, ("no spurious second verb for NP-coord", preds)
    # the sole predication is the give event (its conjoined object head).
    assert any(p[0] == "gave" and p[1] == "she" for p in preds), preds


def test_pp_not_mistaken_for_ditransitive(agent):
    # 'dropped them INTO the pitcher' is monotransitive + a PP goal, NOT a double-
    # object frame: the theme detector's preposition guard yields NO drop(he,pitcher).
    preds = _preds(agent, "He dropped them into the pitcher, and the water rose.")
    assert ["dropped", "he", "them"] in preds, preds
    assert not any(p[0] == "dropped" and p[2] == "pitcher" for p in preds), preds


# --------------------------------------------------------------------------- #
#  GRAPH-NATIVE AUDIT — held marker + verb-headed + argument-structure faculty;
#  no hardcoded splitter, no import re, donkey = 0.
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


def test_shared_subject_is_the_held_verb_headed_faculty(agent):
    # the VP-coordination subject decision reads the held POS main-verb faculty
    # (_find_main_verb -> is_verb_headed) -- a verb-initial clause returns no
    # subject; a subject-bearing clause returns its subject run.
    assert rc._clause_subject_words(agent, ["gave", "her", "a", "whistle"]) is None
    assert rc._clause_subject_words(agent, ["the", "dog", "thanked", "her"]) is not None
