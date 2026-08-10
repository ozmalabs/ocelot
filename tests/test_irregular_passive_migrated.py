"""IRREGULAR PAST-PARTICIPLE PASSIVES (domains/reading_collapse.py, GAP: the
passive/stative collapse only fired for the PRODUCTIVE regular '-ed' form —
"A civilian was killed." read passive/event, but "The protesters were
beaten." read STATIVE is_a(protesters, beaten), so an irregular passive never
reached domains/media_analysis.py's agent-deletion faculty at all).

`_is_past_participle` (reading_collapse.py) now ALSO admits an irregular
participle: morphy maps the surface to a DISTINCT verb lemma via WordNet's
exception list (beaten->beat, shot->shoot, caught->catch, ...), the '-ing'/
'-s' inflection tails are excluded first (morphy is inflection-anonymous —
it strips a gerund tail exactly like an ablaut participle, so 'hunting'
would otherwise misread "A boy WAS HUNTING" as passive), and the admitted
lemma must be TRANSITIVE-DOMINANT by a STRICTER margin than the regular
'-ed' path (itr <= tr * 0.3, not a bare majority) — the margin that
separates true irregular passive participles (beat/shoot/catch: itr/tr
~0.03-0.28) from ergative/resultative-leaning irregulars whose WordNet frame
counts run close to tied (grow tr=20/itr=16; go(ne) tr=68/itr=57; do(ne)
tr=31/itr=12) — 'was grown very old' / 'the food was gone' / 'when we are
done' are RESULTATIVES/STATIVES, not passives, and stay gated. 'torn' is
ALSO intentionally gated (tear alternates ergatively like grow/break; its
ratio sits in the same ambiguous band, .375 > the .3 margin).

A SEPARATE, pre-existing routing fact this module does NOT touch or fix:
'broken'/'taken'/'held'/'written'/'known'/'chosen'/'seen'/'made' are claimed
by DESIGNATE's join-by-ADJACENCY (WordNet path-similarity to called/
labeled/termed/...) before the morph path ever runs — see
test_media_analysis_migrated.py's `test_residual_irregular_participle_never_
reaches_this_module` ('The vase was broken.' -> designation, preds=[]),
which stays green under this change for that reason, not because irregulars
are categorically undetected any more.

Discriminative gates (donkey = 0):

  * HEADLINE — a clean irregular passive grounds [base_verb, '_', patient]
    and reaches media_analysis's agent_deletion faculty via the EXISTING
    seeded AgentiveVerb rows (beat/shoot/catch), no teach() needed.
  * GATED NULLS — ergative/resultative irregulars (grown/gone/done) and the
    intentionally-gated 'torn' stay non-passive (definitional is_a, or
    whatever construction the copula-clause otherwise wins).
  * ADJECTIVE NON-FIRE — a pre-nominal/attributive irregular participle
    ('a beaten path', 'the broken vase') never fires PPART: no COP
    immediately precedes it, so the morph_context gate never opens.
  * GERUND NON-FIRE — an active progressive over an irregular verb ('A boy
    WAS HUNTING for locusts.') stays non-passive: '-ing' is excluded before
    morphy is even trusted.
  * REVISABLE COLLAPSE — a reciprocal marker still pulls an irregular
    passive toward STATIVE exactly like the regular path (same detector).
  * SOURCE AUDIT — no hardcoded verb list; the admission test is WordNet
    morphology + frame-count arithmetic, and the FORM constant carries the
    margin as DATA, not a per-verb branch.
  * BYTE-PARITY — the frozen Aesop/Grimm corpus fixture
    (tests/fixtures/reading_parity/reading.json) was regenerated and is
    gated by tests/test_reading_parity_migrated.py, run separately; every
    corpus reading that changed is documented in the commit as an
    improvement (a wrong is_a/attributive misread now reads passive, or a
    wrong is_a is silently dropped at the decompose grain — a pre-existing
    `_clean_pred` gap this module does not touch: it requires BOTH
    predication arguments head-cleanable, and a passive's agent slot is the
    literal '_' placeholder, so a decompose-reached passive currently drops
    rather than re-grounds; not fixed here, out of scope).

Run: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 python3 -m pytest \
    tests/test_irregular_passive_migrated.py -p no:randomly -q
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
from domains import media_analysis as ma              # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture()
def agent():
    # function-scoped: each test gets a FRESH graph (the reading-parity
    # discipline this project's tests always follow — no cross-sentence
    # accumulation inside one test).
    dl.warm_wordnet("en")
    s, node = boot_core()
    return _Agent(s, node)


def _deletions(a):
    return ma.held_framing_observations(a, device="agent_deletion")


# --------------------------------------------------------------------------- #
#  HEADLINE — irregular passives now COLLAPSE passive/event, not stative is_a.
# --------------------------------------------------------------------------- #
def test_headline_protesters_were_beaten(agent):
    r = rc.read_clause(agent, "The protesters were beaten.", write=True)
    assert r["construction"] == "passive", r
    assert r["predications"] == [["beat", "_", "protesters"]], r


def test_headline_soldier_was_shot(agent):
    r = rc.read_clause(agent, "A soldier was shot.", write=True)
    assert r["construction"] == "passive", r
    assert r["predications"] == [["shoot", "_", "soldier"]], r


def test_headline_thief_was_caught(agent):
    r = rc.read_clause(agent, "The thief was caught.", write=True)
    assert r["construction"] == "passive", r
    assert r["predications"] == [["catch", "_", "thief"]], r


def test_headline_apple_was_eaten(agent):
    r = rc.read_clause(agent, "The apple was eaten.", write=True)
    assert r["construction"] == "passive", r
    assert r["predications"] == [["eat", "_", "apple"]], r


def test_headline_money_was_stolen(agent):
    r = rc.read_clause(agent, "The money was stolen.", write=True)
    assert r["construction"] == "passive", r
    assert r["predications"] == [["steal", "_", "money"]], r


# --------------------------------------------------------------------------- #
#  DOWNSTREAM — reaches media_analysis's agent-deletion faculty via the
#  EXISTING seeded AgentiveVerb rows (beat/shoot), no teach() needed.
# --------------------------------------------------------------------------- #
def test_downstream_agent_deletion_for_beaten(agent):
    rc.read_clause(agent, "The protesters were beaten.", write=True)
    obs = _deletions(agent)
    assert len(obs) == 1, obs
    assert obs[0]["verb"] == "beat", obs
    assert obs[0]["patient"] == "protesters", obs
    assert obs[0]["revisable"] == 1.0, obs


def test_downstream_agent_deletion_for_shot(agent):
    rc.read_clause(agent, "A soldier was shot.", write=True)
    obs = _deletions(agent)
    assert len(obs) == 1, obs
    assert obs[0]["verb"] == "shoot", obs
    assert obs[0]["patient"] == "soldier", obs


def test_downstream_by_phrase_agent_fills_not_deletes(agent):
    # a mechanically-read by-phrase agent -> no deletion (mirrors the regular
    # passive precedent in test_media_analysis_migrated.py exactly).
    rc.read_clause(agent, "The bat was caught by a weasel.", write=True)
    pp = [agent.s.node(n)["attrs"] for n in agent.s.nodes("PassivePredication")]
    assert len(pp) == 1, pp
    assert pp[0]["agent"] == "weasel", pp
    assert pp[0]["agent_filled"] == 1.0, pp
    assert _deletions(agent) == []


# --------------------------------------------------------------------------- #
#  GATED NULLS — ergative/resultative irregulars stay STATIVE (the margin
#  this change adds is precisely what keeps these from over-firing, the
#  failure mode the prior (reverted) attempt at this GAP hit).
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("sentence,subject,participle", [
    ("The old man was grown very old.", "old_man", "grown_very_old"),
    ("The dog was grown.", "dog", "grown"),
    ("The apple was gone.", "apple", "gone"),
    ("The cloth was torn.", "cloth", "torn"),
])
def test_gated_ergative_resultative_stays_stative(agent, sentence, subject, participle):
    r = rc.read_clause(agent, sentence, write=True)
    assert r["construction"] != "passive", r
    assert r["predications"] == [["is_a", subject, participle]], r
    assert agent.s.nodes("PassivePredication") == []
    assert _deletions(agent) == []


# --------------------------------------------------------------------------- #
#  ADJECTIVE NON-FIRE — attributive/pre-nominal position never opens the
#  morph_context gate (no COP immediately precedes the participle).
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("phrase", [
    "a beaten path",
    "the broken vase",
    "a broken window",
    "a beaten man",
])
def test_adjective_position_never_fires_passive(agent, phrase):
    r = rc.read_clause(agent, phrase, write=True)
    assert r["construction"] != "passive", r
    assert agent.s.nodes("PassivePredication") == []


# --------------------------------------------------------------------------- #
#  GERUND NON-FIRE — morphy is inflection-anonymous ('hunting'->'hunt' the
#  same call shape as 'beaten'->'beat'); the '-ing'/'-s' tail exclusion is
#  what keeps an active progressive from misreading as passive.
# --------------------------------------------------------------------------- #
def test_gerund_progressive_never_fires_passive(agent):
    r = rc.read_clause(agent, "A boy was hunting for locusts.", write=True)
    assert r["construction"] != "passive", r
    assert agent.s.nodes("PassivePredication") == []


# --------------------------------------------------------------------------- #
#  REVISABLE COLLAPSE — same confidence-graded judgment the regular path
#  uses; a reciprocal marker still pulls an irregular passive toward
#  STATIVE (this is the SAME `_passive_confidence` detector set, not a
#  parallel decision for irregulars).
# --------------------------------------------------------------------------- #
def test_reciprocal_lowers_irregular_passive_confidence(agent):
    strong = rc.read_clause(agent, "The bat was caught by a weasel.", write=False, learn=False)
    weak = rc.read_clause(agent, "They were beaten among themselves.", write=False, learn=False)
    assert strong["voice"] == "passive", strong
    assert strong["construction"] == "passive", strong
    # the SAME reciprocal detector the regular path uses pulls confidence
    # below threshold for the irregular participle too -- the collapse
    # flips all the way to STATIVE, not merely a lower passive confidence
    # (an irregular passive is graded by the identical judgment, not a
    # parallel decision).
    assert weak["construction"] != "passive", weak


# --------------------------------------------------------------------------- #
#  SOURCE AUDIT — no hardcoded verb enumeration; the admission test is
#  WordNet morphology + frame-count arithmetic, and the margin is DATA.
# --------------------------------------------------------------------------- #
def test_source_audit_no_hardcoded_irregular_verb_list():
    mod_path = os.path.join(ROOT, "domains", "reading_collapse.py")
    src = open(mod_path).read()
    assert "import re" not in [ln.strip() for ln in src.splitlines()]
    # the admission test is a WordNet morphy call + frame-count arithmetic
    # against a MARGIN (data), never a Python membership test over a tuple/
    # frozenset of irregular verb surface forms.
    assert "AGENTIVE_VERBS" not in src
    assert "IRREGULAR_PARTICIPLES" not in src
    import importlib
    m = importlib.import_module("domains.reading_collapse")
    importlib.reload(m)
    assert callable(m._is_past_participle)
    assert isinstance(m._IRREGULAR_ITR_MARGIN, float)
    assert 0.0 < m._IRREGULAR_ITR_MARGIN < 1.0


def test_source_audit_margin_excludes_ergative_admits_agentive():
    from domains.reading_collapse import _is_past_participle
    admitted_beat, lemma = _is_past_participle("beaten")
    assert admitted_beat and lemma == "beat"
    admitted_shot, lemma2 = _is_past_participle("shot")
    assert admitted_shot and lemma2 == "shoot"
    admitted_grown, _ = _is_past_participle("grown")
    assert not admitted_grown
    admitted_gone, _ = _is_past_participle("gone")
    assert not admitted_gone
    admitted_hunting, _ = _is_past_participle("hunting")
    assert not admitted_hunting
