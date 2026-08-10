"""test_run64_migrated.py -- unit gates for RUN 64 (decisive best-case cursive char reading).

Gates the machinery BEFORE the expensive eval (ops law "unit tests first"):
  * the parse-marginal recognizer produces a per-char candidate/verdict on a REAL DeepWriting char;
  * per-class pair-error vector (STAGE 2 ingredient) is well-formed + lower-is-better convention;
  * within-corpus bank is cross-writer DISJOINT from the test-word writers;
  * lexicon-collapse reuse (run 61 decoders) runs on a parse-marginal error vector;
  * seed-guard md5 of seeds/stroke_shapes.json is UNCHANGED across staging.

System python3 (per ops law: unit tests on system python). These need substrate_rs +
DeepWriting data; each guard skips honestly if a prerequisite is missing rather than failing.
"""
import hashlib
import os
import sys
import tempfile

import numpy as np
import pytest

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
os.environ.setdefault("DEEPWRITING_DIR", "/tmp/handwriting")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")


def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _have_deepwriting():
    return os.path.exists(os.path.join(os.environ["DEEPWRITING_DIR"], "deepwriting_validation.npz"))


def _have_srs():
    try:
        import substrate_rs  # noqa: F401
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not (_have_deepwriting() and _have_srs()),
                                reason="needs DeepWriting npz + substrate_rs")


@pytest.fixture(scope="module")
def glyphs():
    from domains import deepwriting_world as dww
    dw = dww.load_deepwriting("validation")
    gl = dww.extract_char_glyphs(dw)
    return [g for g in gl if 10 <= g["class"] <= 35]      # lowercase only


def _stage_small_bank(scratch, glyphs, ar, tmpdir, classes, m=2):
    import scripts.jabberwock_realwordread_run64 as r64
    from collections import defaultdict
    byc = defaultdict(list)
    for g in glyphs:
        byc[g["class"]].append(g)
    node2class = {}
    class2nodes = defaultdict(list)
    for c in classes:
        for j, g in enumerate(byc[c][:m]):
            p = os.path.join(tmpdir, f"b_{c}_{j}.txt")
            r64.write_omni_file(g["strokes"], p)
            node = ar.stage_parse_char(scratch, p, is_query=False, name=str(c))
            node2class[node] = c
            class2nodes[c].append(node)
    return node2class, dict(class2nodes)


def test_parse_marginal_produces_char_verdict(glyphs):
    """The FULL parse-marginal pipeline yields a per-char verdict (a candidate node whose `name`
    decodes to a lowercase class) on a REAL DeepWriting connected char -- the decisive recognizer
    is live on this data."""
    import substrate_rs as srs
    from domains import abs_read as ar
    import scripts.jabberwock_realwordread_run64 as r64

    md5_before = _md5(STROKE_SHAPES_SEED)
    classes = [10, 11, 12, 13, 14]     # a b c d e
    have = [c for c in classes if any(g["class"] == c for g in glyphs)]
    assert len(have) >= 3, "need a few lowercase classes in the validation split"

    with tempfile.TemporaryDirectory() as tmp:
        scratch = srs.Substrate()
        node2class, _ = _stage_small_bank(scratch, glyphs, ar, tmp, have, m=2)
        assert len(node2class) >= 3
        # query = a real glyph of the first available class
        q = next(g for g in glyphs if g["class"] == have[0])
        qp = os.path.join(tmp, "q.txt")
        r64.write_omni_file(q["strokes"], qp)
        qn = ar.stage_parse_char(scratch, qp, is_query=True)
        w = ar.parse_marginal_verdict(scratch, qn)
        assert w is not None, "verdict must return a candidate node"
        pred = node2class.get(w, None)
        assert pred in set(have), "winner must decode to a staged lowercase class"

    assert _md5(STROKE_SHAPES_SEED) == md5_before, "SEED GUARD: stroke_shapes.json changed"


def test_pair_error_vector_wellformed(glyphs):
    """The STAGE-2 ingredient: a 62-length parse-marginal error vector, lowercase entries finite,
    non-lowercase entries the large sentinel, argmin lands on a lowercase class (lower=better)."""
    import substrate_rs as srs
    from domains import abs_read as ar
    import scripts.jabberwock_realwordread_run64 as r64

    classes = [10, 11, 12, 13, 14]
    have = [c for c in classes if any(g["class"] == c for g in glyphs)][:4]
    assert len(have) >= 3
    with tempfile.TemporaryDirectory() as tmp:
        scratch = srs.Substrate()
        _, class2nodes = _stage_small_bank(scratch, glyphs, ar, tmp, have, m=2)
        q = next(g for g in glyphs if g["class"] == have[0])
        qp = os.path.join(tmp, "q.txt")
        r64.write_omni_file(q["strokes"], qp)
        qn = ar.stage_parse_char(scratch, qp, is_query=True)
        # limit LOWER_CLASSES scan to the staged classes for this small test
        orig = r64.LOWER_CLASSES
        r64.LOWER_CLASSES = have
        try:
            vec = r64._char_error_vector(scratch, qn, class2nodes, ar)
        finally:
            r64.LOWER_CLASSES = orig
        assert len(vec) == 62
        for c in have:
            assert vec[c] < 1e6, "a staged lowercase class must have a finite error"
        assert vec[0] == 1e6 and vec[40] == 1e6, "unstaged classes stay at sentinel"
        assert int(np.argmin(vec)) in set(have), "argmin lands on a staged lowercase class"


def test_bank_writer_disjoint_from_test():
    """Within-corpus bank is cross-writer: background (bank) writers DISJOINT from held-out
    (test-word) writers -- the same writer_split run 62 used."""
    from domains import deepwriting_world as dww
    import scripts.jabberwock_realwordread_run64 as r64
    dw = dww.load_deepwriting("validation")
    from nltk.corpus import brown, wordnet as wn  # noqa: F401  (ensure corpora importable)
    words = dww.extract_words(dw, min_len=3, max_len=8, lowercase_only=True, complete_only=True)
    if len(words) < 4:
        pytest.skip("validation split has too few complete words for a split test")
    bg, ho = dww.writer_split(words, n_background_frac=r64.N_BACKGROUND_FRAC,
                              seed=r64.WRITER_SPLIT_SEED)
    bg_w = {w["writer"] for w in bg}
    ho_w = {w["writer"] for w in ho}
    assert bg_w.isdisjoint(ho_w), "bank writers must be disjoint from test-word writers"


def test_lexicon_collapse_reuse():
    """run 61's decoders consume a parse-marginal-shaped 62-length DISTANCE vector: no-context
    argmin + length-constrained lexicon collapse both run and return lowercase strings."""
    import scripts.jabberwock_wordread_run61 as r61
    import scripts.jabberwock_realwordread_run64 as r64
    lex = ["cat", "cab", "dog"]
    lex_by_len = r61._lex_by_len(lex)
    logfreq = {w: 0.0 for w in lex}
    # synthetic per-char distance vectors favouring c,a,t (lower=better).
    def vec(cls):
        v = [1e6] * 62
        v[cls] = 0.1
        return v
    dists = [vec(r61._lower_class(ch)) for ch in "cat"]
    nc = r61.decode_no_context(dists, r64.SYMBOLS)
    lx = r61.decode_lexicon(dists, 3, lex_by_len, logfreq, 0.0)
    assert nc == "cat"
    assert lx == "cat"


def test_omni_roundtrip_format():
    """write_omni_file emits a file omniglot_world.load_strokes parses back to the same stroke
    count + point counts (mechanical I/O correctness)."""
    from domains import omniglot_world as ow
    import scripts.jabberwock_realwordread_run64 as r64
    strokes = [np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 0.5]]),
               np.array([[3.0, 3.0], [4.0, 2.0]])]
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "s.txt")
        r64.write_omni_file(strokes, p)
        back = ow.load_strokes(p)
    assert len(back) == 2
    assert [len(s) for s in back] == [3, 2]
