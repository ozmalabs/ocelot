"""RUN 61 unit tests -- language-context word reading (tests/test_wordread_migrated.py).

Pure-python tests (word composition, synthetic lexicon decode, no-context/with-context compute,
seed-guard md5) run under SYSTEM python3. The one geometry test (top-K per-char candidates) needs
`substrate_rs` and is SKIPPED when it is unavailable (run under `.venv` to exercise it).
"""
from __future__ import annotations

import hashlib
import math
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import scripts.jabberwock_wordread_run61 as wr

# The real-ink tests need the DigiLeTs raw corpus on disk (environment-bound
# dataset; absent on machines without data/handwriting populated).
try:
    from domains import pen_world as _pw
    _DIGILETS_PRESENT = bool(_pw._digilets_participant_files(_pw.DIGILETS_RAW_DIR))
except Exception:  # noqa: BLE001
    _DIGILETS_PRESENT = False


def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


# ------------------------------------------------------------------------------------------- #
@pytest.mark.skipif(not _DIGILETS_PRESENT,
                    reason="DigiLeTs raw corpus not present (dataset not on this machine)")
def test_word_composition_cross_writer_labels():
    """A word composes to a sequence of REAL glyph instances from ONE word-writer, correct labels,
    and that writer is NOT a bank writer (cross-writer)."""
    from domains import pen_world as pw
    samples = pw.load_digilets_samples()
    background, heldout = pw.digilets_writer_split(
        samples, n_background=wr.N_BACKGROUND_WRITERS, seed=wr.WRITER_SPLIT_SEED)
    bg_writers = {s["writer_id"] for s in background}
    ho_writers = sorted({s["writer_id"] for s in heldout})
    assert bg_writers.isdisjoint(ho_writers)

    wc_index = wr._index_by_writer_class([s for s in samples if s["writer_id"] in set(ho_writers)])
    writer = ho_writers[0]
    rng = np.random.default_rng(0)
    chars = wr.compose_word("hello", writer, wc_index, rng)
    assert [c["sym"] for c in chars] == list("hello")
    # correct lowercase class ids (a=10 .. z=35); 'h'=17, 'e'=14, 'l'=21, 'o'=24.
    assert [c["class"] for c in chars] == [wr._lower_class(ch) for ch in "hello"]
    assert writer not in bg_writers          # cross-writer glyphs vs the bank
    for c in chars:
        assert np.asarray(c["strokes"][0]).shape[1] == 2   # real pen xy strokes


# ------------------------------------------------------------------------------------------- #
def test_lexicon_decode_resolves_homoglyph():
    """The load-bearing test: the geometry recognizer says '0' (digit) over 'o' at position 0 for
    'old' (a homoglyph tie it CANNOT break), so NO-CONTEXT reads '0ld'; the lexicon prior FORCES
    'old'. Fully synthetic, deterministic lattice + a tiny synthetic lexicon."""
    symbols, sym2c = wr._sym_maps()
    L = 3
    HI = 10.0
    dists = [[HI] * 62 for _ in range(L)]
    # position 0: digit '0' (class 0) slightly favored over lowercase 'o' -> homoglyph trap.
    dists[0][sym2c["0"]] = 4.9          # argmin -> NO-CONTEXT picks '0'
    dists[0][sym2c["o"]] = 5.0
    dists[0][sym2c["O"]] = 5.1
    # position 1: 'l' clear-ish but '1' close (another homoglyph), 'l' favored.
    dists[1][sym2c["l"]] = 3.0
    dists[1][sym2c["1"]] = 3.2
    # position 2: 'd' clear.
    dists[2][sym2c["d"]] = 2.0

    nc = wr.decode_no_context(dists, symbols)
    assert nc[0] == "0" and nc != "old"    # NO-CONTEXT falls for the homoglyph

    lex_by_len = {3: ["old", "and", "the", "odd"]}
    logfreq = {w: math.log(1.0 / 4) for w in lex_by_len[3]}
    lx = wr.decode_lexicon(dists, L, lex_by_len, logfreq, alpha=0.0)
    assert lx == "old", f"lexicon should resolve to 'old', got '{lx}'"
    # and it is a genuine homoglyph resolution at position 0.
    assert wr._is_homoglyph_pair("o", "0")


def test_no_context_and_with_context_both_compute():
    """Both readers produce a same-length string for a clean lattice."""
    symbols, sym2c = wr._sym_maps()
    word = "cat"
    dists = [[10.0] * 62 for _ in word]
    for i, ch in enumerate(word):
        dists[i][sym2c[ch]] = 1.0
    nc = wr.decode_no_context(dists, symbols)
    lex_by_len = {3: ["cat", "dog", "car"]}
    logfreq = {w: 0.0 for w in lex_by_len[3]}
    lx = wr.decode_lexicon(dists, 3, lex_by_len, logfreq, alpha=0.0)
    assert nc == "cat" and lx == "cat"
    assert len(nc) == len(word) and len(lx) == len(word)


def test_char_bigram_decode_computes():
    """Open-vocab char-bigram Viterbi returns a same-length string."""
    symbols, sym2c = wr._sym_maps()
    word = "the"
    dists = [[10.0] * 62 for _ in word]
    for i, ch in enumerate(word):
        dists[i][sym2c[ch]] = 1.0
    # trivial uniform transition
    lt = lambda a, b: math.log(1.0 / 28)
    out = wr.decode_char_bigram(dists, symbols, lt, beta=1.0)
    assert len(out) == 3 and out == "the"   # emission dominates under uniform transition


def test_homoglyph_groups_match_run48():
    """The homoglyph groups are reproduced verbatim from run 48."""
    import scripts.jabberwock_omniglot_run48_digilets as run48
    assert wr.HOMOGLYPH_GROUPS == run48.HOMOGLYPH_GROUPS


def test_seed_guard_md5_stable():
    """decode_* / compose_* / _sym_maps must not mutate the stroke-shapes seed."""
    before = _md5(wr.STROKE_SHAPES_SEED)
    symbols, sym2c = wr._sym_maps()
    dists = [[1.0] * 62 for _ in range(3)]
    wr.decode_no_context(dists, symbols)
    wr.decode_lexicon(dists, 3, {3: ["cat"]}, {"cat": 0.0}, alpha=0.0)
    after = _md5(wr.STROKE_SHAPES_SEED)
    assert before == after


# ------------------------------------------------------------------------------------------- #
# Geometry test -- needs substrate_rs (run under .venv). Skips cleanly otherwise.
# ------------------------------------------------------------------------------------------- #
@pytest.mark.skipif(not _DIGILETS_PRESENT,
                    reason="DigiLeTs raw corpus not present (dataset not on this machine)")
def test_topk_candidates_from_geometry():
    try:
        import substrate_rs  # noqa: F401
        import scripts.jabberwock_omniglot_run47_pendata as run47  # noqa: F401
    except Exception:
        import pytest
        pytest.skip("substrate_rs unavailable (run under .venv to exercise geometry)")

    from domains import pen_world as pw
    samples = pw.load_digilets_samples()
    background, heldout = pw.digilets_writer_split(
        samples, n_background=wr.N_BACKGROUND_WRITERS, seed=wr.WRITER_SPLIT_SEED)
    from collections import defaultdict
    by_class = defaultdict(list)
    for s in background:
        by_class[s["class"]].append(s)
    bank_ps = {c: [run47._stroke_point_sets_from_arrays(by_class[c][i]["strokes"])
                   for i in range(min(3, len(by_class[c])))] for c in range(62)}
    # a held-out lowercase 'a' query.
    ho = [s for s in heldout if s["class"] == wr._lower_class("a")][0]
    q = run47._stroke_point_sets_from_arrays(ho["strokes"])
    dists = wr.char_distance_vector(q, bank_ps)
    assert len(dists) == 62
    order = list(np.argsort(dists))
    topk = order[:8]
    # the true class 'a' should be within the top-8 candidates (visual recall).
    assert wr._lower_class("a") in topk, f"true class not in top-8: {[pw.DIGILETS_SYMBOLS[c] for c in topk]}"
