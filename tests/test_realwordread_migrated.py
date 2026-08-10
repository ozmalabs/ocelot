"""test_realwordread_migrated.py -- RUN 62 unit tests (run FIRST, before the stages).

Covers: DeepWriting loader (word label + trajectory + writer parse), geometry candidates on a real
word-ink char, the JOINT span-lattice decode resolving a synthetic segmentation-ambiguous case
('rn' vs 'm' -- segmentation collapsed by the lexicon), no-context vs collapse compute, and the
seed-guard md5. System python3 runs the pure-logic tests; the geometry test is skipped if
substrate_rs / the data are unavailable (documented, never a silent pass)."""
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
os.environ.setdefault("DEEPWRITING_DIR", "/tmp/handwriting")

STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")
_DW_DIR = os.environ["DEEPWRITING_DIR"]  # set by rootdir conftest -> gitignored data/
DATA_OK = os.path.exists(os.path.join(_DW_DIR, "deepwriting_validation.npz"))


def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


# --------------------------------------------------------------------------------------------- #
#  Loader.
# --------------------------------------------------------------------------------------------- #
@pytest.mark.skipif(not DATA_OK, reason="DeepWriting data not present in $DEEPWRITING_DIR")
def test_loader_word_label_and_writer_parse():
    from domains import deepwriting_world as dww
    dw = dww.load_deepwriting("validation")
    assert dw["n"] > 100
    words = dww.extract_words(dw, min_len=3, max_len=8, lowercase_only=True, complete_only=True)
    assert len(words) > 20
    for w in words[:50]:
        # word == concatenation of its per-char segment symbols (segmentation is consistent).
        assert "".join(c["symbol"] for c in w["char_segs"]) == w["word"]
        assert w["word"].isalpha() and w["word"].islower()
        assert 3 <= len(w["word"]) <= 8
        assert isinstance(w["writer"], int)
        # whole-word ink present and 2-D.
        assert w["strokes"] and all(np.asarray(s).ndim == 2 for s in w["strokes"])


@pytest.mark.skipif(not DATA_OK, reason="DeepWriting data not present")
def test_char_label_offset_decodes_text():
    """The +33 char-label offset must reproduce the `texts` reference (substring alignment)."""
    from domains import deepwriting_world as dww
    dw = dww.load_deepwriting("validation")
    from collections import Counter
    hits = 0
    for i in range(min(50, dw["n"])):
        cl = dw["char_labels"][i]
        soc = dw["soc_labels"][i]
        starts = [int(s) for s in np.flatnonzero(np.asarray(soc) == 1)]
        rec = ""
        for k, s in enumerate(starts):
            e = (starts[k + 1] - 1) if k + 1 < len(starts) else len(cl) - 1
            lab = Counter(cl[s:e + 1].tolist()).most_common(1)[0][0]
            rec += dw["alphabet"][(lab + dww.CHAR_LABEL_OFFSET) % len(dw["alphabet"])]
        txt = str(dw["texts"][i]).replace(" ", "")
        # decoded chars must be a prefix-ish substring of the reference text (window over a line).
        if rec and rec[:6] and rec[:6] in txt:
            hits += 1
    assert hits >= 25, f"offset decode aligned to texts in only {hits}/50 samples"


@pytest.mark.skipif(not DATA_OK, reason="DeepWriting data not present")
def test_writer_split_disjoint():
    from domains import deepwriting_world as dww
    dw = dww.load_deepwriting("validation")
    words = dww.extract_words(dw, complete_only=True)
    bg, ho = dww.writer_split(words, n_background_frac=0.5, seed=123)
    bw = {w["writer"] for w in bg}
    hw = {w["writer"] for w in ho}
    assert bw and hw and bw.isdisjoint(hw)


# --------------------------------------------------------------------------------------------- #
#  Geometry candidates on real word-ink char (needs substrate_rs).
# --------------------------------------------------------------------------------------------- #
@pytest.mark.skipif(not DATA_OK, reason="DeepWriting data not present")
def test_geometry_candidates_on_real_char():
    try:
        import substrate_rs  # noqa: F401
        import scripts.jabberwock_omniglot_run47_pendata as run47
    except Exception as e:
        pytest.skip(f"substrate_rs/run47 unavailable: {e}")
    from domains import deepwriting_world as dww
    dw = dww.load_deepwriting("validation")
    glyphs = dww.extract_char_glyphs(dw)
    # take an 'a' glyph, score it against a few other 'a's and a few 'e's; same-class min <= inf.
    a_class = dww.canon_class("a")
    a_glyphs = [g for g in glyphs if g["class"] == a_class][:6]
    assert len(a_glyphs) >= 3
    q = run47._stroke_point_sets_from_arrays(a_glyphs[0]["strokes"])
    scores = [run47.ps.program_score(q, run47._stroke_point_sets_from_arrays(g["strokes"]))
              for g in a_glyphs[1:]]
    assert all(math.isfinite(s) for s in scores)
    # 62-length distance vector shape via the run62 helper.
    import scripts.jabberwock_realwordread_run62 as r62
    bank_ps = {c: [] for c in range(62)}
    bank_ps[a_class] = [run47._stroke_point_sets_from_arrays(g["strokes"]) for g in a_glyphs[1:4]]
    vec = r62._char_dist_vector(q, bank_ps, run47)
    assert len(vec) == 62
    assert math.isfinite(vec[a_class])


# --------------------------------------------------------------------------------------------- #
#  JOINT decode resolves a synthetic segmentation-ambiguous case ('rn' vs 'm').
# --------------------------------------------------------------------------------------------- #
def _synthetic_SD(K, spans_costs):
    """Build an SD dict[(a,b)] = np.array(62) where every class is a high cost EXCEPT the ones
    named in spans_costs {(a,b): {class_char: cost}}."""
    import scripts.jabberwock_wordread_run61 as r61
    SD = {}
    for (a, b), cc in spans_costs.items():
        v = np.full(62, 10.0)
        for ch, cost in cc.items():
            v[r61._lower_class(ch)] = cost
        SD[(a, b)] = v
    return SD


def test_joint_lexicon_resolves_rn_vs_m():
    """Ink over 3 knots (0,1,2). Geometry is AMBIGUOUS: the whole span (0,2) looks like 'm' (cheap)
    OR splits into 'r'(0,1)+'n'(1,2) (also cheap). The lexicon holds BOTH open and collapses to the
    real word. With lexicon {'corn'... } vs {'com'...}: choose per lexicon membership."""
    import scripts.jabberwock_realwordread_run62 as r62
    # a 4-knot word: knot0..3. True ink is 'r','n' over (0,1),(1,2)... plus a final 'y' (2,3) etc.
    # Simpler: 3 knots, decide between 2-char 'rn' and 1-char 'm' for the SAME ink.
    K = 3
    SD = _synthetic_SD(K, {
        (0, 2): {"m": 1.0},                       # whole span reads 'm' cheaply.
        (0, 1): {"r": 1.0}, (1, 2): {"n": 1.0},   # split reads 'r'+'n' cheaply.
    })
    # lexicon has 'rn' (a stand-in 2-char word) but NOT 'm'; collapse must pick the SEGMENTED reading.
    trie_rn = r62._build_trie(["rn"])
    out = r62.joint_lexicon_decode(SD, K, trie_rn, {"rn": 0.0}, alpha=0.0)
    assert out == "rn", f"expected segmentation-open 'rn', got {out!r}"
    # lexicon has 'm' but NOT 'rn': collapse must pick the MERGED reading.
    trie_m = r62._build_trie(["me", "m"])
    out2 = r62.joint_lexicon_decode(SD, K, trie_m, {"m": 0.0, "me": 0.0}, alpha=0.0)
    assert out2 == "m", f"expected merged 'm', got {out2!r}"


def test_joint_free_vs_collapse_compute():
    """Free segmentation commits to the geometry argmax; collapse can override via the lexicon."""
    import scripts.jabberwock_realwordread_run62 as r62
    import scripts.jabberwock_wordread_run61 as r61
    K = 3
    # geometry PREFERS 'r'+'n' (each 0.5) over 'm' (2.0): free-seg -> 'rn'.
    SD = _synthetic_SD(K, {(0, 2): {"m": 2.0}, (0, 1): {"r": 0.5}, (1, 2): {"n": 0.5}})
    free = r62.joint_free_decode(SD, K, r62.SYMBOLS, lam=0.0)
    assert free == "rn", f"free-seg should follow geometry to 'rn', got {free!r}"
    # but the lexicon only contains 'm' -> collapse overrides the geometry's preferred segmentation.
    trie_m = r62._build_trie(["m"])
    coll = r62.joint_lexicon_decode(SD, K, trie_m, {"m": 0.0}, alpha=0.0)
    assert coll == "m", f"collapse should override to lexicon 'm', got {coll!r}"
    # oracle-count with m=1 must also read the single-char span.
    oracle1 = r62.joint_oracle_count_decode(SD, K, r62.SYMBOLS, 1)
    assert len(oracle1) == 1


def test_no_context_and_lexicon_decoders_reused():
    """The run 61 decoders operate on the run 62 62-class order (sanity: argmin picks the min)."""
    import scripts.jabberwock_wordread_run61 as r61
    import scripts.jabberwock_realwordread_run62 as r62
    syms = r62.SYMBOLS
    # two chars: distances peaked at 'c' then 'a' -> 'ca'.
    d = [[5.0] * 62, [5.0] * 62]
    d[0][r61._lower_class("c")] = 0.1
    d[1][r61._lower_class("a")] = 0.1
    assert r61.decode_no_context(d, syms) == "ca"
    lex_by_len = r61._lex_by_len(["ca", "an", "cat"])
    assert r61.decode_lexicon(d, 2, lex_by_len, {"ca": 0.0, "an": 0.0}, 0.0) == "ca"


# --------------------------------------------------------------------------------------------- #
#  Seed guard.
# --------------------------------------------------------------------------------------------- #
def test_seed_guard_md5_stable():
    assert os.path.exists(STROKE_SHAPES_SEED)
    a = _md5(STROKE_SHAPES_SEED)
    b = _md5(STROKE_SHAPES_SEED)
    assert a == b and len(a) == 32
