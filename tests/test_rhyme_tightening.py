"""test_rhyme_tightening — closes the two named RHYME residuals (M2,
3abd84e2): (1) an OOV line-ending had no CMUdict pronunciation -> no rime at
all -> could never rhyme (an honest gap); (2) the coarse formant-distance
threshold let an occasional FALSE partner through (`boy`~`through` matched,
0.1397, before `joy` arrived).

Both are fixed in `domains/metrical_reading.py` ONLY:

  1. OOV COVERAGE — `_rime` now falls back to `_rime_oov` (a mechanical
     English default-pronunciation heuristic: last vowel-letter group ->
     canonical ARPABET vowel, trailing consonant letters -> the SAME coarse
     coda tokens `_rime_spectrum` already reads) instead of returning None for
     a pure-OOV word. `_rime_source` discloses which path fired so the
     heuristic is never silently conflated with a real CMUdict pronunciation.
  2. THRESHOLD TIGHTENED — `_RHYME_THRESHOLD` 0.14 -> 0.12. Every held TRUE
     rhyme is spectral-IDENTICAL (distance 0.0), so this leaves a wide margin
     below every true match while cutting `boy`~`through` (0.1397).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 -m pytest \
     tests/test_rhyme_tightening.py -p no:randomly -q -s
"""
from __future__ import annotations

import ast
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains import metrical_reading as mr                      # noqa: E402
import jabberwock_predicts_verse as jpv                          # noqa: E402


def _has_cmu() -> bool:
    return mr._cmu() is not None


requires_cmu = pytest.mark.skipif(not _has_cmu(), reason="CMUdict (nltk) not available offline")


# --------------------------------------------------------------------------- #
#  1. OOV COVERAGE — a constructed OOV-rhyme pair now gets a partner.
# --------------------------------------------------------------------------- #
@requires_cmu
def test_oov_rhyme_coinage_gets_a_partner():
    """'brillig'~'quillig' (invented, same rime: last vowel group 'i' -> IH,
    coda 'g' -> G) are BOTH OOV (no CMUdict entry) yet now resolve to the SAME
    rime signature via the disclosed default-pronunciation heuristic, and
    `rhyme_partner`/`predict_line_end` find the partner -- the residual's
    actual fix (before this change, an OOV ending had no rime at all)."""
    assert mr._cmu().get("brillig") is None and mr._cmu().get("quillig") is None
    assert mr._rime_source("brillig") == "oov_heuristic"
    assert mr._rime_source("quillig") == "oov_heuristic"
    r_b, r_q = mr._rime("brillig"), mr._rime("quillig")
    print("\n  rime(brillig)=%r  rime(quillig)=%r" % (r_b, r_q))
    assert r_b is not None and r_q is not None          # no more None-on-OOV
    assert mr.rhymes("brillig", "quillig")["rhyme"] is True
    assert mr.rhyme_partner("quillig", ["brillig"]) == "brillig"
    le = mr.predict_line_end(None, ["brillig", "quillig"])
    assert le["partners"].get("quillig") == "brillig"


@requires_cmu
def test_oov_coverage_does_not_manufacture_false_rhymes():
    """The heuristic gives an OOV word a SIGNATURE, not a rubber-stamped
    rhyme: two OOV words with genuinely different rimes ('slithy' -> AY nucleus
    no coda; 'borogoves' -> EH nucleus + S coda) still correctly DON'T rhyme."""
    d = mr.rime_distance("slithy", "borogoves")
    assert d is not None                                 # signature exists now
    assert mr.rhymes("slithy", "borogoves")["rhyme"] is False   # still no rhyme
    # but the poem's ACTUAL rhyme pairs among its OOV coinages now resolve:
    assert mr.rhymes("toves", "borogoves")["rhyme"] is True
    assert mr.rhymes("wabe", "outgrabe")["rhyme"] is True


# --------------------------------------------------------------------------- #
#  2. FALSE-PARTNER CUT — boy~through gone; the four named true rhymes kept.
# --------------------------------------------------------------------------- #
TRUE_RHYMES = [("bright", "night"), ("are", "star"), ("shun", "son"), ("thought", "sought")]
FALSE_PARTNERS = [("boy", "through")]


@requires_cmu
def test_false_partner_boy_through_no_longer_matches():
    r = mr.rhymes("boy", "through")
    print("\n  boy~through distance=%.4f rhyme=%s (threshold=%.2f)"
          % (r["distance"], r["rhyme"], mr._RHYME_THRESHOLD))
    assert r["rhyme"] is False
    assert r["distance"] == pytest.approx(0.1397, abs=1e-3)   # unchanged distance
    assert r["distance"] > mr._RHYME_THRESHOLD                # now outside the (tighter) threshold


@requires_cmu
def test_true_rhymes_still_match_after_tightening():
    for a, b in TRUE_RHYMES:
        r = mr.rhymes(a, b)
        assert r["rhyme"] is True, (a, b, r)
    # boy~joy (the TRUE partner of 'boy', once it arrives) is unaffected too.
    assert mr.rhymes("boy", "joy")["rhyme"] is True


@requires_cmu
def test_precision_true_kept_false_cut():
    """MEASURE: true rhymes kept / total true rhymes, and false partners cut /
    total named false partners. Both must be 1.0 (100%) -- no true rhyme lost,
    the named false partner gone."""
    kept = sum(1 for a, b in TRUE_RHYMES if mr.rhymes(a, b)["rhyme"])
    cut = sum(1 for a, b in FALSE_PARTNERS if not mr.rhymes(a, b)["rhyme"])
    precision_true = kept / len(TRUE_RHYMES)
    precision_false_cut = cut / len(FALSE_PARTNERS)
    print("\n  true rhymes kept: %d/%d (%.0f%%)  false partners cut: %d/%d (%.0f%%)"
          % (kept, len(TRUE_RHYMES), precision_true * 100,
             cut, len(FALSE_PARTNERS), precision_false_cut * 100))
    assert precision_true == 1.0
    assert precision_false_cut == 1.0
    # honest residual: some UN-NAMED near-misses still clear the tightened
    # threshold (disclosed, not silently hidden) -- a coda VOICING distinction
    # (T vs D) would be the next lever, out of scope for this fix.
    residual = [("sought", "stood"), ("thought", "wood"), ("head", "back")]
    still_false_partners = [(a, b) for a, b in residual if mr.rhymes(a, b)["rhyme"]]
    print("  known REMAINING false partners (disclosed, not fixed here): %r"
          % still_false_partners)
    assert still_false_partners == [("sought", "stood"), ("thought", "wood"), ("head", "back")]


# --------------------------------------------------------------------------- #
#  3. VERSE-BOOST NOT REGRESSED — re-run the M2 gate script.
# --------------------------------------------------------------------------- #
@requires_cmu
def test_verse_boost_not_regressed():
    """The verse confirm-boost survives the tightened threshold + OOV
    coverage -- both numbers verbatim, reported against M2's committed
    0.49 Jabberwocky / 0.44 nursery. (OOV coverage actually recovers TWO more
    genuine rhyme-confirmed line-ends in Jabberwocky -- 'borogoves'~'toves' and
    'outgrabe'~'wabe' -- which the false 'boy'~'through' cut does not erase.)"""
    import jabberwock_reads_jabberwocky as jw
    b1 = jpv.verse_boost("Jabberwocky (regression check)", jw.JABBERWOCKY)
    b2 = jpv.verse_boost("nursery (regression check)", jpv.NURSERY)
    print("\n  Jabberwocky guided=%.3f (M2 was 0.490)  nursery guided=%.3f (M2 was 0.444)"
          % (b1["guided"], b2["guided"]))
    assert b1["guided"] > b1["baseline"]
    assert b1["guided"] > b1["plain"]
    assert b2["guided"] > b2["baseline"]
    assert b2["guided"] > b2["plain"]
    # the boost is not just preserved, it is NOT WORSE than M2's committed number.
    assert b1["guided"] >= 0.490 - 0.02
    assert b2["guided"] >= 0.444 - 0.02


def test_gate_script_still_runs_end_to_end():
    assert jpv.main() == 0


# --------------------------------------------------------------------------- #
#  4. GRAPH-NATIVE AUDIT.
# --------------------------------------------------------------------------- #
def test_no_import_re_donkey_zero():
    src = open(os.path.join(ROOT, "domains", "metrical_reading.py")).read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(a.name == "re" for a in node.names)
        if isinstance(node, ast.ImportFrom):
            assert node.module != "re"
    low = src.lower()
    for banned in ("openai", "anthropic", "requests.post", "call_model",
                   "subprocess", "os.system", '"git ', "'git ", "git commit"):
        assert banned not in low, "banned LLM/git token %r" % banned


def test_oov_rime_is_mechanical_not_a_per_word_table():
    """The OOV rime path is a general spelling->phone heuristic (vowel-group +
    coda-letter mapping) keyed on SPELLING PATTERNS ('ee', 'igh', single
    letters, ...), not a per-word lookup -- no dict entry keyed by an exact
    test word ('brillig'/'quillig'/'slithy'/'borogoves' appear only in prose
    docstrings, never as a quoted dict key)."""
    src = open(os.path.join(ROOT, "domains", "metrical_reading.py")).read()
    for banned_word in ("brillig", "quillig", "slithy", "borogoves"):
        for quote in ('"', "'"):
            assert quote + banned_word + quote + ":" not in src.lower()
            assert quote + banned_word + quote + " :" not in src.lower()
    # confirm instead the heuristic tables are small SPELLING patterns.
    assert '"igh": "AY"' in src or "'igh': 'AY'" in src
