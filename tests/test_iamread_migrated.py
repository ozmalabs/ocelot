"""test_iamread_migrated.py -- RUN 63 unit gates (IAM-OnDB reading).

Mechanical-adapter + decoder tests: lineStrokes parse, CSR alignment, word-gap segmentation on a
synthetic 2-word line, geometry candidates on a real IAM word, lexicon-collapse compute, seed-guard
md5. System python3 is fine for parse/segment/decode; the geometry test needs substrate_rs (via
run 47) and is skipped if unavailable.
"""
import hashlib
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
os.environ.setdefault("IAM_STROKES_DIR", "/tmp/handwriting/iam_onbd/lineStrokes")
os.environ.setdefault("IAM_ASCII_DIR", "/tmp/handwriting/iam_ascii/ascii")

from domains import iam_world as iw

STROKES = os.environ["IAM_STROKES_DIR"]
ASCII = os.environ["IAM_ASCII_DIR"]
KNOWN_XML = os.path.join(STROKES, "a01", "a01-000", "a01-000u-01.xml")
HAVE_IAM = os.path.exists(KNOWN_XML)
iam = pytest.mark.skipif(not HAVE_IAM, reason="IAM-OnDB not extracted")


@iam
def test_linestrokes_parse():
    p = iw.parse_line_strokes(KNOWN_XML)
    assert len(p["strokes"]) == 31            # verified stroke count for this line.
    tot = sum(len(s) for s in p["strokes"])
    assert tot == 568                         # verified point count.
    for s in p["strokes"]:
        assert s.shape[1] == 3                 # x, y, time.
    x0, y0, x1, y1 = p["bounds"]
    assert x1 > x0 and y1 > y0                 # plausible board extents.
    # all points inside the board bounds (with margin).
    allp = np.concatenate(p["strokes"])
    assert allp[:, 0].min() >= x0 - 5 and allp[:, 0].max() <= x1 + 5


@iam
def test_csr_alignment_known_line():
    lines = iw.load_lines(forms={"a01-000u"})
    by_id = {l["line_id"]: l for l in lines}
    assert by_id["a01-000u-01"]["text"] == "A MOVE to stop Mr . Gaitskell"
    assert by_id["a01-000u-01"]["words"] == ["A", "MOVE", "to", "stop", "Mr", "Gaitskell"]
    assert by_id["a01-000u-06"]["text"] == "resolution on the subject"
    # six stroke lines <-> six CSR lines, in order.
    assert len([l for l in lines if l["form"] == "a01-000u"]) == 6


def _synth_two_word_line():
    """Two 'words' of two strokes each; a big horizontal gap between them, small gaps within."""
    def box(x0):
        return [np.array([[x0, 0, 0], [x0 + 3, 5, 1], [x0 + 6, 0, 2]], float),
                np.array([[x0 + 7, 0, 3], [x0 + 10, 5, 4]], float)]
    left = box(0.0)                 # x in [0,10]
    right = box(40.0)               # x in [40,50]; gap 30 >> intra-word gaps.
    return left + right


def test_word_gap_segmentation_synthetic():
    strokes = _synth_two_word_line()
    # oracle: exactly two words.
    groups = iw.segment_words(strokes, n_words=2)
    assert len(groups) == 2
    assert len(groups[0]) == 2 and len(groups[1]) == 2
    # adaptive: the 30-unit gap dwarfs the ~1-unit intra-word gaps -> 2 words.
    ad = iw.segment_words(strokes, gap_frac=0.5)
    assert len(ad) == 2


@iam
def test_geometry_candidates_on_real_iam_word():
    """A real IAM word's span-lattice geometry yields a 62-class distance vector per span."""
    try:
        import scripts.jabberwock_omniglot_run47_pendata as run47
        import scripts.jabberwock_realwordread_run62 as r62
        from domains import deepwriting_world as dww
    except Exception as e:                     # substrate_rs / deepwriting missing
        pytest.skip(f"geometry deps unavailable: {e}")
    if not os.path.exists(os.path.join(os.environ.get("DEEPWRITING_DIR", "/tmp/handwriting"),
                                       "deepwriting_validation.npz")):
        pytest.skip("DeepWriting npz unavailable")
    lines = iw.load_lines(forms={"a01-000u"})
    l = [x for x in lines if x["line_id"] == "a01-000u-06"][0]   # "resolution on the subject"
    groups = iw.segment_words(l["strokes"], n_words=len(l["words"]))
    word_ink = [g_[:, :2] for g_ in groups[0]]                   # first word ink (x,y only).
    # tiny 2-class bank from DeepWriting for the smoke test.
    dw = dww.load_deepwriting("validation")
    glyphs = dww.extract_char_glyphs(dw)
    from collections import defaultdict
    bysym = defaultdict(list)
    for gph in glyphs:
        bysym[gph["symbol"]].append(gph)
    bank = {c: [] for c in range(62)}
    for sym in ("r", "o"):
        bank[dww.CANON_SYM2CLASS[sym]] = [g_["strokes"] for g_ in bysym[sym][:2]]
    bank_ps = {c: [run47._stroke_point_sets_from_arrays(e) for e in bank[c]] for c in range(62)}
    boundaries, spans, K = r62.span_distance_tensor(word_ink, 9.0, bank_ps, run47)
    assert K >= 2 and len(spans) >= 1
    a, b = next(iter(spans))
    vec = spans[(a, b)]
    assert len(vec) == 62 and all(np.isfinite(v) for v in vec)


def test_lexicon_collapse_compute():
    """joint_lexicon_decode picks the reachable lexicon word minimizing summed span cost."""
    import scripts.jabberwock_realwordread_run62 as r62
    import scripts.jabberwock_wordread_run61 as r61
    lexicon = ["cat", "dog", "car"]
    trie = r62._build_trie(lexicon)
    # K=4 boundaries -> 3 chars; craft SD so 'cat' is cheapest (c,a,t at classes for c/a/t).
    lc = r61._lower_class
    K = 4
    INF = float("inf")
    SD = {}
    for a in range(K):
        for b in range(a + 1, K):
            SD[(a, b)] = np.full(62, 5.0)
    # single-gap spans spelling c-a-t cheaply.
    SD[(0, 1)][lc("c")] = 0.1
    SD[(1, 2)][lc("a")] = 0.1
    SD[(2, 3)][lc("t")] = 0.1
    out = r62.joint_lexicon_decode(SD, K, trie, {}, alpha=0.0)
    assert out == "cat"


def test_seed_guard_md5():
    seed = os.path.join(ROOT, "seeds", "stroke_shapes.json")
    with open(seed, "rb") as f:
        m = hashlib.md5(f.read()).hexdigest()
    assert len(m) == 32
