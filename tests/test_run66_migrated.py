"""test_run66_migrated.py -- RUN 66 unit gates: the cursive-writing CURRICULUM machinery.

Each test exercises ONE curriculum primitive on REAL DeepWriting ink (donkey=0, all geometry
DECISIONS via native Terms -- StrokeQuantize / StrokeRender / DtwTo / Argmin):

  1. letter-form quantization on a real cursive char (learn a letter as a ShapeSignature).
  2. join extraction from a real adjacent letter PAIR (the connector: A.exit -> B.entry).
  3. GENERATE a 2-letter sequence -> a connected trajectory WITH a join, and the no-join
     concatenation is DIFFERENT (the join changes the geometry).
  4. AbS compare: whole-word DTW of a generated word vs the SAME real word is LOWER than vs a
     different real word (generation-as-reading is discriminative at all).
  5. teach() a letter-form redirected to an ISOLATED seeds dir -> the REAL seeds/stroke_shapes.json
     md5 is UNCHANGED (seed guard).

Run:
  OZMA_SEED_PERSIST_DISABLED=1 DEEPWRITING_DIR=/tmp/handwriting PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python3 -m pytest tests/test_run66_migrated.py -q
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import numpy as np
import pytest

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
os.environ.setdefault("DEEPWRITING_DIR", "/tmp/handwriting")

ROOT = Path(__file__).resolve().parent.parent
import sys
for _p in (str(ROOT), str(ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

cc66 = pytest.importorskip("scripts.jabberwock_cursive_curriculum_run66")
dww = pytest.importorskip("domains.deepwriting_world")
srs = pytest.importorskip("substrate_rs")

REAL_SEED = ROOT / "seeds" / "stroke_shapes.json"


def _md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def native():
    return srs.Substrate()._inner


@pytest.fixture(scope="module")
def glyphs():
    if not (Path(dww.TRAIN_NPZ).exists() or Path(dww.VALID_NPZ).exists()):
        pytest.skip("DeepWriting corpus not present")
    dw = dww.load_deepwriting("validation")
    return dww.extract_words(dw, min_len=3, max_len=8, lowercase_only=True, complete_only=True), dw


def test_letter_form_quantize_render_roundtrip(native, glyphs):
    """A real single-stroke cursive letter quantizes to a ShapeSignature whose StrokeRender is a
    faithful inverse (invariant round-trip DTW small) -- the generative letter model."""
    words, dw = glyphs
    exemplar = None
    for w in words:
        for cs in w["char_segs"]:
            if len(cs["strokes"]) == 1 and len(cs["strokes"][0]) >= 8:
                exemplar = np.asarray(cs["strokes"][0], float)
                break
        if exemplar is not None:
            break
    assert exemplar is not None, "no single-stroke cursive letter found"
    form = cc66.learn_letter_form(native, exemplar)
    assert form["signature"], "empty signature"
    render = cc66.render_form_canonical(native, form)
    assert render.shape[1] == 2 and len(render) >= 8
    # both invariant-normalized -> faithful inverse.
    inv_orig = np.asarray(cc66.invariant(exemplar, len(render)))
    d = cc66.dtw(native, cc66.invariant(render, len(render)), inv_orig)
    assert d < 0.20, f"round-trip infidelity {d:.3f} (expected < 0.20)"


def test_join_extraction_from_pair(native, glyphs):
    """From a real adjacent letter pair, the join = the connector displacement A.exit -> B.entry
    (in normalized letter units) is a finite 2-vector."""
    words, dw = glyphs
    pair = None
    for w in words:
        segs = [cs for cs in w["char_segs"] if len(cs["strokes"]) == 1 and len(cs["strokes"][0]) >= 6]
        if len(segs) >= 2:
            pair = (np.asarray(segs[0]["strokes"][0], float),
                    np.asarray(segs[1]["strokes"][0], float))
            break
    assert pair is not None
    join = cc66.extract_join(pair[0], pair[1])
    assert len(join) == 2 and all(np.isfinite(join))


def test_generate_two_letter_with_and_without_join(native, glyphs):
    """Generating a 2-letter sequence WITH the learned join produces a connected trajectory that
    DIFFERS from the no-join side-by-side concatenation (the join materially changes geometry)."""
    words, dw = glyphs
    forms = {}
    for w in words:
        for cs in w["char_segs"]:
            c = cs["class"]
            if c not in forms and len(cs["strokes"]) == 1 and len(cs["strokes"][0]) >= 8:
                forms[c] = cc66.learn_letter_form(native, np.asarray(cs["strokes"][0], float))
        if len(forms) >= 2:
            break
    (ca, fa), (cb, fb) = list(forms.items())[:2]
    join = np.array([0.05, 0.02])
    with_join = cc66.generate_word(native, [fa, fb], join_gap=join, joins=True)
    no_join = cc66.generate_word(native, [fa, fb], join_gap=join, joins=False)
    assert len(with_join) >= 4 and len(no_join) >= 4
    dv = cc66.dtw(native, cc66.wordnorm(with_join), cc66.wordnorm(no_join))
    assert dv > 1e-3, "join vs no-join generated identical geometry"


def test_abs_compare_generated_vs_real_discriminates(native, glyphs):
    """Whole-word DTW of a real word's OWN generated form is lower than vs an unrelated real word
    (generation-as-reading carries signal)."""
    words, dw = glyphs
    usable = [w for w in words
              if all(len(cs["strokes"]) == 1 and len(cs["strokes"][0]) >= 6 for cs in w["char_segs"])]
    assert len(usable) >= 4
    forms_by_class = {}
    for w in usable:
        for cs in w["char_segs"]:
            forms_by_class.setdefault(cs["class"], np.asarray(cs["strokes"][0], float))
    def gen(word_segs):
        fs = [cc66.learn_letter_form(native, np.asarray(cs["strokes"][0], float)) for cs in word_segs]
        return cc66.generate_word(native, fs, join_gap=np.zeros(2), joins=True)
    w0 = usable[0]
    q = cc66.word_points(w0)                              # real query ink
    g_self = gen(w0["char_segs"])                         # its own generation
    # an unrelated word of possibly different content
    w1 = next((w for w in usable[1:] if w["word"] != w0["word"]), usable[1])
    g_other = gen(w1["char_segs"])
    d_self = cc66.dtw(native, cc66.wordnorm(q), cc66.wordnorm(g_self))
    d_other = cc66.dtw(native, cc66.wordnorm(q), cc66.wordnorm(g_other))
    assert d_self < d_other + 1e-6, f"self {d_self:.3f} not <= other {d_other:.3f}"


def test_teach_letter_form_isolated_seed_guard(native, glyphs, tmp_path):
    """teach()-ing a learned letter-form redirected to an ISOLATED seeds dir leaves the REAL
    seeds/stroke_shapes.json md5 UNCHANGED, and writes into the isolated dir."""
    words, dw = glyphs
    exemplar = None
    for w in words:
        for cs in w["char_segs"]:
            if len(cs["strokes"]) == 1 and len(cs["strokes"][0]) >= 8:
                exemplar = np.asarray(cs["strokes"][0], float)
                break
        if exemplar is not None:
            break
    before = _md5(REAL_SEED)
    iso = tmp_path / "seeds"
    iso.mkdir()
    ag = srs.Substrate()
    form = cc66.learn_letter_form(native, exemplar)
    cc66.teach_letter_form(ag, symbol="e", allo=0, form=form, seeds_dir=iso)
    after = _md5(REAL_SEED)
    assert before == after, "REAL stroke_shapes.json md5 changed -- teach leaked to real seed dir!"
    written = list(iso.glob("*.json"))
    assert written, "isolated teach wrote nothing"
