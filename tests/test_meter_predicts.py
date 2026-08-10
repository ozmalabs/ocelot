"""test_meter_predicts — M2: THE BRIDGE gate. Meter/rhyme as a PREDICTIVE +
DISAMBIGUATING constraint, closing the three tracks (meter, predictive reader,
parse) into ONE.

Two payoffs + the pincer, each behind a protected control:

  * VERSE CONFIRM-BOOST — on metrical verse, the meter/rhyme-guided prediction
    confirm-fraction is HIGHER than the same-unit baseline (no meter/rhyme) AND
    higher than the plain-prose predict_first_pass baseline (~25% on the crow).
    The rhyme predicts a line-end (a fresh word confirmed by resonance).
  * HERO LICENSED — the metrical-prominence factor licenses the Jabberwocky hero
    as 'he' (the metrically-prominent agent), not 'mimsy'. Before/after verbatim.
  * CROW BYTE-IDENTICAL — prose is never verse, so the prominence factor is a
    no-op: no crow entity is licensed, the crow binds are unchanged, and the
    prose predictor's confirm-fraction does NOT regress (still 25%).
  * GRAPH-NATIVE — the prediction is the metrical_reading collapse run forward;
    the prominence factor is an Attr in the antecedent Argmax value (a Term, not
    a Python override); no `import re`; donkey = 0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_meter_predicts.py -p no:randomly -q -s
"""
from __future__ import annotations

import ast
import os
import sys
from collections import Counter

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.boot_core import boot_core                       # noqa: E402
from domains import dictionary_lexicon as dl                    # noqa: E402
from domains import coref_entities as ce                        # noqa: E402
from domains import metrical_reading as mr                      # noqa: E402
from domains import predictive_reading as pr                    # noqa: E402
import jabberwock_reads_jabberwocky as jw                       # noqa: E402
import jabberwock_produces_analysis_from_goal as jpafg          # noqa: E402
import jabberwock_predicts_verse as jpv                         # noqa: E402


class _Agent:
    def __init__(self, s, node):
        self.s = s
        self.inner = s._inner
        self.agent = node


@pytest.fixture(scope="module", autouse=True)
def _warm():
    dl.warm_wordnet("en")


def _fresh():
    s, node = boot_core()
    return _Agent(s, node)


def _has_cmu() -> bool:
    return mr._cmu() is not None


requires_cmu = pytest.mark.skipif(not _has_cmu(), reason="CMUdict (nltk) not available offline")


def _lines(text: str) -> list:
    return [l for l in text.split("\n") if l.strip()]


# --------------------------------------------------------------------------- #
#  1. VERSE CONFIRM-BOOST — meter/rhyme-guided > baseline, both numbers.
# --------------------------------------------------------------------------- #
@requires_cmu
def test_verse_confirm_boost_over_same_unit_baseline():
    """On Jabberwocky, the meter/rhyme-GUIDED confirm-fraction is strictly higher
    than the SAME-UNIT baseline (the identical line-level predictor minus the
    meter/rhyme augmentation) -- the boost is attributable purely to the harmonic
    prediction. Both numbers verbatim, printed under -s."""
    out = pr.predict_verse_first_pass(_fresh(), _lines(jw.JABBERWOCKY))
    print("\n  JABBERWOCKY guided=%.3f baseline=%.3f boost=%+.3f"
          % (out["guided"], out["baseline"], out["guided"] - out["baseline"]))
    assert out["guided"] > out["baseline"], (out["guided"], out["baseline"])
    # the boost comes from rhyme-confirmed line-ends (fresh words).
    rc = [s["rhyme_confirmed_end"] for s in out["steps"] if s.get("rhyme_confirmed_end")]
    assert rc, "no rhyme-confirmed line-end -- the rhyme lever did not fire"


@requires_cmu
def test_verse_confirm_boost_over_plain_prose_baseline():
    """The categorical verse-boost the user predicted: on metrical verse, the
    meter/rhyme-guided confirm-fraction is ABOVE the plain-prose predict_first_
    pass baseline (~25% on the crow). Both numbers verbatim."""
    prose = pr.predict_first_pass(_fresh(), jpafg.CROW)["aggregate"]["confirm_frac"]
    guided = pr.predict_verse_first_pass(_fresh(), _lines(jw.JABBERWOCKY))["guided"]
    print("\n  guided(verse)=%.3f  vs  plain-prose predict_first_pass(crow)=%.3f"
          % (guided, prose))
    assert prose == pytest.approx(0.25, abs=0.02), prose      # the ~25% prose baseline
    assert guided > prose, (guided, prose)


@requires_cmu
def test_rhyme_predicts_a_line_end():
    """The RHYME predicts the line-end: on a nursery rhyme with FRESH rhyme words
    (no verbatim repeat), 'are' resonates with the established partner 'star' and
    'sky' with 'high' -- a fresh line-end confirmed at the sound level, exactly
    the strongest single predictor in verse."""
    out = pr.predict_verse_first_pass(_fresh(), _lines(jpv.NURSERY))
    partners = {s["rhyme_partner"][0]: s["rhyme_partner"][1]
                for s in out["steps"] if s.get("rhyme_partner")}
    print("\n  nursery rhyme partners: %r" % partners)
    assert partners.get("are") == "star"
    assert partners.get("sky") == "high"
    # and those fresh line-ends were CONFIRMED by the rhyme (boost over baseline).
    assert out["guided"] > out["baseline"], (out["guided"], out["baseline"])


@requires_cmu
def test_predict_line_end_is_a_forward_run_of_the_spectral_recognizer():
    """predict_line_end runs the RHYME recognizer forward off accumulated
    endings: it names the partner and never mutates the graph (pure perception)."""
    r = mr.predict_line_end(_fresh(), ["star", "high", "are"])
    assert "are" in r["candidates"] and "star" in r["candidates"]
    assert r["partners"].get("are") == "star"          # 'are' rhymed with 'star'
    assert mr.rhyme_partner("sky", ["high", "star"]) == "high"
    assert mr.rhyme_partner("orange", ["star", "high"]) is None   # honest: no partner


# --------------------------------------------------------------------------- #
#  2. HERO LICENSED — before/after (mimsy -> he), verbatim.
# --------------------------------------------------------------------------- #
def _hero_vote(r) -> list:
    c = Counter(x["concept"] for x in r["resolutions"]
                if x["resolved"] and x["surface"] == "he")
    return c.most_common(4)


@requires_cmu
def test_hero_licensed_as_metrically_prominent_agent_not_mimsy():
    """BEFORE (verse gate off -- the poem flattened to prose): 'he' scatters onto
    the salient-but-wrong antecedent 'foe' (Res3's inverted-verse role-completeness
    now binds 'foe' as an object role, so it out-mentions the old 'mimsy' recency
    artefact). AFTER (verse gate on -- metrical): the prominence factor licenses
    ONE hero labelled 'he'. The licensing mechanism is unchanged; only the
    un-licensed baseline moved as the parse bound more roles. Before/after verbatim."""
    before = ce.read_into_situation_model(_fresh(), jw.JABBERWOCKY.replace("\n", " "))
    after = ce.read_into_situation_model(_fresh(), jw.JABBERWOCKY)
    bv, av = _hero_vote(before), _hero_vote(after)
    print("\n  BEFORE he-> %r\n  AFTER  he-> %r" % (bv, av))
    assert bv and bv[0][0] == "foe"                    # the salient-but-wrong antecedent (foe, now role-bound by Res3)
    assert av and av[0][0] == "he"                     # the licensed metrical hero (unchanged)
    assert av[0][1] >= 5                                # unified (>=5 hero pronouns)
    # 'mimsy' is demoted from the runaway artefact it was.
    assert after["situation_model"]["he"]["coref_metrical_prominence"] == 1.0
    mimsy = after["situation_model"].get("mimsy", {})
    assert (mimsy.get("coref_mentions") or 0.0) < after["situation_model"]["he"]["coref_mentions"]


@requires_cmu
def test_verse_gate_separates_verse_from_prose():
    """The gate is a pure perceptual read: Jabberwocky (newline verse) -> True;
    the crow (a single prose paragraph, 0 newlines) -> False; a bare prose
    sentence -> False (protects the coref unit tests)."""
    assert ce._text_is_verse(jw.JABBERWOCKY) is True
    assert ce._text_is_verse(jpafg.CROW) is False
    assert ce._text_is_verse("John met Bill. He left the room.") is False
    assert ce._text_is_verse(jpv.NURSERY) is True


# --------------------------------------------------------------------------- #
#  3. CROW BYTE-IDENTICAL — the hard guard: prose is untouched.
# --------------------------------------------------------------------------- #
@requires_cmu
def test_crow_prose_is_byte_identical_and_untouched():
    """The crow (prose) is never verse, so the prominence factor is a no-op: no
    crow entity is licensed, the reads are deterministic (byte-identical), and
    the crow's pronoun binds are unchanged (he -> crow). The hard byte-identity
    guard the licensing must not cross."""
    c1 = ce.read_into_situation_model(_fresh(), jpafg.CROW)
    c2 = ce.read_into_situation_model(_fresh(), jpafg.CROW)
    assert c1["situation_model"] == c2["situation_model"]     # deterministic
    assert not any(at.get("coref_metrical_prominence") == 1.0
                   for at in c1["situation_model"].values())  # factor never fired
    he = [x for x in c1["resolutions"] if x["surface"] == "he" and x["resolved"]]
    assert he and all(x["concept"] == "crow" for x in he)     # unchanged bind


@requires_cmu
def test_prose_confirm_fraction_does_not_regress():
    """The PROSE confirm-fraction must NOT regress: meter/rhyme only ADDS on
    verse. predict_first_pass on the crow still confirms ~25% (the committed
    prose baseline) -- the verse machinery does not touch the prose predictor."""
    a = pr.predict_first_pass(_fresh(), jpafg.CROW)["aggregate"]["confirm_frac"]
    b = pr.predict_first_pass(_fresh(), jpafg.CROW)["aggregate"]["confirm_frac"]
    print("\n  prose confirm_frac=%.4f (deterministic=%s)" % (a, a == b))
    assert a == b                                       # deterministic
    assert a == pytest.approx(0.25, abs=0.02)           # the ~25% baseline, unregressed


# --------------------------------------------------------------------------- #
#  4. GRAPH-NATIVE SOURCE AUDIT — Term factor, forward collapse, no regex.
# --------------------------------------------------------------------------- #
def test_prominence_is_a_graph_term_factor_not_a_python_override():
    """The metrical-prominence factor is an Attr('coref_metrical_prominence')
    node inside the antecedent Argmax's `value` Term (an IfThenElse weighting,
    the SAME shape as the is_cb centering factor) -- Python never inspects a
    candidate to pick the hero; the DSL evaluator does."""
    term = ce.antecedent_argmax_term(ce._PRONOUNS["he"], None)
    assert term["type"] == "Argmax"

    def _has_prom(node) -> bool:
        if isinstance(node, dict):
            if (node.get("type") == "Attr"
                    and node.get("key") == "coref_metrical_prominence"):
                return True
            return any(_has_prom(v) for v in node.values())
        if isinstance(node, list):
            return any(_has_prom(v) for v in node)
        return False

    assert _has_prom(term["value"])
    # the licensing helper mints/tags via mechanical adapter I/O, never max()/sorted().
    import inspect
    src = inspect.getsource(ce._license_metrical_hero)
    assert "max(" not in src and "sorted(" not in src


def test_no_import_re_donkey_zero_in_edited_modules():
    """No `import re` (recognition/perception only) and donkey = 0 (no LLM call
    token) in the three edited modules + the script. `donkey = 0` in a docstring
    is the ASSERTION of zero LLM, not a violation -- so this checks for actual
    LLM-call tokens, exactly like the summit's donkey-zero audit."""
    for rel in ("domains/metrical_reading.py", "domains/predictive_reading.py",
                "domains/coref_entities.py", "scripts/jabberwock_predicts_verse.py"):
        src = open(os.path.join(ROOT, rel)).read()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not any(a.name == "re" for a in node.names), "import re in %s" % rel
            if isinstance(node, ast.ImportFrom):
                assert node.module != "re", "from re in %s" % rel
        low = src.lower()
        for banned in ("openai", "anthropic", "requests.post", "call_model",
                       "subprocess", "os.system", '"git ', "'git ", "git commit"):
            assert banned not in low, "banned LLM/git token %r in %s" % (banned, rel)


def test_meter_rhyme_prediction_is_the_metrical_collapse_run_forward():
    """The prediction IS the metrical_reading collapse run forward: predict_next_
    beat (temporal harmonic) extends the recognized period; predict_line_end
    (spectral harmonic) runs the rhyme recognizer off accumulated endings."""
    nb = mr.predict_next_beat(list("wSwSwSwS"), ["w", "S"], 2)
    assert nb["predicted"] == ["w", "S"]               # the period predicts the next beat
    le = mr.predict_line_end(_fresh(), ["star", "are"])
    assert le["partners"].get("are") == "star"         # the rhyme predicts the line-end


def test_gate_script_runs_end_to_end():
    """The M2 gate driver runs the whole bridge end-to-end (both payoffs + the
    pincer + the crow guard) and returns 0."""
    assert jpv.main() == 0
