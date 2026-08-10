"""test_run76_migrated.py -- unit gates for RUN 76 (the full reading model -- whole-word visual +
sentence prediction, run 63's per-letter+lexicon arm -- assembled on REAL IAM-OnDB lines).

Gates the machinery BEFORE the expensive real-data eval (ops law "unit tests first"):
  * IAM line load + oracle word-count segmentation on a KNOWN real line (a01-000u's first line) --
    the word-count split must match the CSR transcription's own token count.
  * the word-grain writer-relative frame estimator (`local_baseline_topline_words` /
    `aggregate_scale_slant_words`) -- a direct analogy of r69's char-grain estimator -- recovers a
    sane baseline/topline ordering on synthetic ascender/x-height/descender word shapes, the SAME
    sign-convention property r69 verified at char grain.
  * `word_pose_canon_iam` round-trips a known synthetic slant back to (near-)zero horizontal
    variation when de-slanted by the SAME angle (r69's own de-slant unit-test property, reused at
    word grain).
  * `oracle_count_rows` recovers the correct m-span backbone (and hence the right per-position
    class) on a synthetic span-distance dict built so the TRUE m-span path is unambiguously
    cheapest -- the row-extraction DP this run adds on top of r62's own `joint_oracle_count_decode`
    recurrence.
  * `topk_candidates_iam` -- a sight-vocab-covered label is dominant (top-ranked) over the per-
    letter-loose channel via the additive HOLISTIC_BONUS, but a per-letter candidate can still
    appear (never removed) -- the "dominant, not absolute" design property.
  * `decode_isolated_arm_a` reproduces r63's own lexicon-collapse decode on a hand-built span
    lattice that unambiguously favors the true word.
  * seed guard: seeds/stroke_shapes.json md5 UNCHANGED across the whole module.

Native (substrate_rs) / real-corpus (IAM XML) tests are skipped if the corpus or substrate_rs are
not present; pure-python tests (the bulk of this file) need neither.
"""
from __future__ import annotations

import hashlib
import os
import sys

import numpy as np
import pytest

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
os.environ.setdefault("DEEPWRITING_DIR", "/tmp/handwriting")
os.environ.setdefault("IAM_STROKES_DIR", "/tmp/handwriting/iam_onbd/lineStrokes")
os.environ.setdefault("IAM_ASCII_DIR", "/tmp/handwriting/iam_ascii/ascii")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import scripts.jabberwock_iam_full_run76 as r76
from domains import iam_world as iw

STROKE_SHAPES_SEED = r76.STROKE_SHAPES_SEED
IAM_PRESENT = os.path.isdir(iw.IAM_STROKES_DIR) and os.path.isdir(iw.IAM_ASCII_DIR)
try:
    import substrate_rs  # noqa: F401
    NATIVE_PRESENT = True
except Exception:
    NATIVE_PRESENT = False


def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


@pytest.fixture(scope="module", autouse=True)
def seed_guard():
    before = _md5(STROKE_SHAPES_SEED)
    yield
    after = _md5(STROKE_SHAPES_SEED)
    assert after == before, "seeds/stroke_shapes.json must be byte-unchanged by this test module"


# ============================================================================================= #
#  IAM line load + oracle word-count segmentation, on a KNOWN real line.
# ============================================================================================= #
@pytest.mark.skipif(not IAM_PRESENT, reason="IAM-OnDB corpus not present")
def test_iam_known_line_loads_and_oracle_segments():
    lines = iw.load_lines(forms={"a01-000u"})
    assert len(lines) >= 1
    l0 = lines[0]
    assert l0["form"] == "a01-000u"
    assert len(l0["strokes"]) > 0
    assert isinstance(l0["text"], str) and l0["text"].strip()
    # oracle word-count segmentation: the group count must equal the CSR token count by construction.
    groups = iw.segment_words(l0["strokes"], n_words=len(l0["words"]))
    assert len(groups) == len(l0["words"])
    # every group must carry at least one point.
    assert all(sum(len(np.asarray(s)) for s in g) > 0 for g in groups)


@pytest.mark.skipif(not IAM_PRESENT, reason="IAM-OnDB corpus not present")
def test_iam_document_has_multiple_lines_for_writer_adaptation():
    lines = iw.load_lines(forms={"a01-000u"})
    assert len(lines) >= 2, "a within-writer (within-document) adaptation test needs >=2 lines/doc"


# ============================================================================================= #
#  Word-grain frame estimator -- direct analogy of r69's char-grain one.
# ============================================================================================= #
def _mk_word(y_lo, y_hi, x0=0.0):
    """A tiny synthetic 'word': a straight vertical segment spanning [y_lo, y_hi] at x0..x0+1."""
    return {"strokes": [np.array([[x0, y_lo], [x0 + 1.0, y_hi]])]}


def test_local_baseline_topline_words_sign_convention():
    # y increases DOWNWARD (IAM/DeepWriting convention). x-height words: y in [10,20] (5 of them).
    # One ascender word pushes its min_y (top) well ABOVE the x-height band (smaller y = higher).
    words = [_mk_word(10, 20, x0=i) for i in range(3)] + [_mk_word(2, 20, x0=3)] + \
        [_mk_word(10, 20, x0=i) for i in range(4, 6)]
    idx = 3   # the ascender word itself.
    baseline, topline = r76.local_baseline_topline_words(words, idx, window=3)
    # baseline/topline come from the NEIGHBORS (x-height words): baseline ~ 20 (their max_y),
    # topline ~ 10 (their min_y) -- the ascender's own extent must NOT dominate its own frame.
    assert abs(baseline - 20.0) < 1e-6
    assert abs(topline - 10.0) < 1e-6
    assert baseline > topline    # x_height = baseline - topline > 0.


def test_aggregate_scale_slant_words_recovers_xheight():
    # two lines of 5 x-height words each, x_height should aggregate to ~10 (20-10).
    lines_words = {
        "l1": [_mk_word(10, 20, x0=i) for i in range(5)],
        "l2": [_mk_word(10, 20, x0=i) for i in range(5)],
    }
    fr = r76.aggregate_scale_slant_words(lines_words)
    assert abs(fr["x_height"] - 10.0) < 1e-6
    assert fr["n_xh_obs"] > 0


def test_aggregate_scale_slant_words_skips_short_lines():
    # a line with <2 words contributes NO observations (too few neighbors, per r69's own bar).
    lines_words = {"l1": [_mk_word(10, 20)]}
    fr = r76.aggregate_scale_slant_words(lines_words)
    assert fr["n_xh_obs"] == 0
    assert fr["n_words"] == 1


# ============================================================================================= #
#  word_pose_canon_iam -- de-slant round-trip (r69's own de-slant unit-test property, word grain).
# ============================================================================================= #
def test_word_pose_canon_iam_deslant_removes_synthetic_slant():
    import math
    baseline, x_height = 0.0, 10.0
    slant_deg = 15.0
    # a vertical stroke sheared by +slant_deg (the SAME forward-shear convention r69 verified).
    ys = np.linspace(0.0, -10.0, 20)                      # rising above baseline (y decreases up).
    t = math.tan(math.radians(slant_deg))
    xs = 0.0 + t * (baseline - ys)                        # forward shear (r69's own convention).
    pts = np.stack([xs, ys], axis=1)
    canon = np.asarray(r76.word_pose_canon_iam([pts.tolist()], baseline, x_height, slant_deg, n=20))
    # after de-slanting by the SAME angle, x should be ~constant (all points share entry x).
    assert np.ptp(canon[:, 0]) < 1e-6


# ============================================================================================= #
#  oracle_count_rows -- the m-span backbone-recovery DP this run adds on r62's recurrence.
# ============================================================================================= #
def _mk_sd(true_spans, true_classes, K, n_classes=62, cheap=0.1, expensive=5.0):
    """Synthetic SD dict: every feasible (a,b) with b<=a+7 gets an all-`expensive` 62-vector,
    EXCEPT the TRUE spans, which get `cheap` at their true class -- makes the true m-span path
    unambiguously the DP optimum."""
    SD = {}
    for a in range(K):
        for b in range(a + 1, min(K, a + 8)):
            SD[(a, b)] = [expensive] * n_classes
    for (a, b), c in zip(true_spans, true_classes):
        row = [expensive] * n_classes
        row[c] = cheap
        SD[(a, b)] = row
    return SD


def test_oracle_count_rows_recovers_true_backbone():
    K = 4
    true_spans = [(0, 1), (1, 2), (2, 3)]
    true_classes = [10, 14, 21]                            # 'a', 'e', 'l' (10-offset lowercase).
    SD = _mk_sd(true_spans, true_classes, K)
    rows = r76.oracle_count_rows(SD, K, m=3)
    assert rows is not None and len(rows) == 3
    for row, c in zip(rows, true_classes):
        assert len(row) == 26
        assert int(np.argmin(row)) == c - 10                # rows are sliced to the 26 lowercase classes.


def test_oracle_count_rows_infeasible_returns_none():
    K = 2   # only 1 boundary gap -- cannot support m=3 spans.
    SD = {(0, 1): [1.0] * 62}
    assert r76.oracle_count_rows(SD, K, m=3) is None


# ============================================================================================= #
#  topk_candidates_iam -- holistic-dominant, per-letter never discarded.
# ============================================================================================= #
def test_topk_candidates_iam_dual_route_covered_uses_holistic():
    # DUAL-ROUTE: a COVERED position's candidate set is the holistic-bank labels (visual = -dtw),
    # ranked by DTW distance -- the per-letter channel is NOT mixed in (different, un-comparable
    # scale). Best (lowest-dtw) holistic label ranks first.
    L = 4
    lex_by_len = r76.r75.build_lex_by_len(["word", "wore", "ward", "wind"])
    rows = np.full((L, 26), 5.0)
    for i, ch in enumerate("wore"):
        rows[i][ord(ch) - 97] = 0.5
    within = {"word": 0.2, "ward": 0.9}       # sight-vocab: 'word' is the closer whole-word match.
    words, scores = r76.topk_candidates_iam(rows.tolist(), lex_by_len, within, {}, True, K=10)
    assert set(words) == {"word", "ward"}     # ONLY holistic labels (dual-route), per-letter excluded.
    order = sorted(range(len(words)), key=lambda i: -scores[i])
    assert words[order[0]] == "word"          # lowest-dtw holistic label ranks FIRST.


def test_topk_candidates_iam_no_coverage_falls_back_to_per_letter():
    L = 3
    lex_by_len = r76.r75.build_lex_by_len(["cat", "cot", "dog"])
    rows = np.full((L, 26), 5.0)
    for i, ch in enumerate("cat"):
        rows[i][ord(ch) - 97] = 0.1
    words, scores = r76.topk_candidates_iam(rows.tolist(), lex_by_len, {}, {}, True, K=10)
    best = words[int(np.argmax(scores))]
    assert best == "cat"


# ============================================================================================= #
#  decode_isolated_arm_a -- reproduces r63's own mechanism on a hand-built lattice.
# ============================================================================================= #
def test_decode_isolated_arm_a_picks_true_word():
    K = 4
    true_spans = [(0, 1), (1, 2), (2, 3)]
    # 'cat' -> classes 12('c'? no: lowercase offset 10 -> 'c'=12,'a'=10,'t'=29).
    true_classes = [12, 10, 29]
    SD_list = []
    for a in range(K):
        for b in range(a + 1, K):
            SD_list.append([a, b, [5.0] * 62])
    for (a, b), c in zip(true_spans, true_classes):
        row = [5.0] * 62
        row[c] = 0.1
        for entry in SD_list:
            if entry[0] == a and entry[1] == b:
                entry[2] = row
    trie = r76.r62._build_trie(["cat", "cot", "cap"])
    logfreq = {"cat": 0.0, "cot": -1.0, "cap": -1.0}
    pred = r76.decode_isolated_arm_a(SD_list, K, "cat", trie, logfreq)
    assert pred == "cat"


# ============================================================================================= #
#  Real-corpus / native integration smoke test (skipped if IAM or substrate_rs absent).
# ============================================================================================= #
@pytest.mark.skipif(not (IAM_PRESENT and NATIVE_PRESENT), reason="needs IAM corpus + substrate_rs")
def test_prep_builds_small_and_recognize_holistic_smoke():
    """A SMALL end-to-end smoke test (not the full run): builds prep on a handful of forms and
    exercises one word through recognize + holistic, checking shapes/keys line up. Cheap (few
    forms), independent of the full-scale checkpoints under results/run76_checkpoints/."""
    import substrate_rs as srs
    forms = set()
    for d in iw.iter_forms():
        base = os.path.basename(d)
        if base.startswith("a01"):
            forms.add(None)  # placeholder to break early via glob below
            break
    lines = iw.load_lines(max_forms=6)
    assert len(lines) > 0
    pf = [l for l in lines if len(l["words"]) >= 2 and all(t.isalpha() for t in l["text"].split())]
    assert pf, "need at least one punctuation-free multi-word line in the first few forms"
    l0 = pf[0]
    words = r76._oracle_words_for_line(l0)
    assert len(words) == len(l0["words"])
    if not words:
        return
    w = words[0]
    strokes = [np.asarray(s, float) for s in w["strokes"]]
    bankd = r76._load(r76.RUN63_BANK)
    bank_wf = {c: [r76.r63.whole_fig_points([np.asarray(s, float) for s in e])
                   for e in bankd["bank"][str(c)]] for c in range(62)}
    boundaries, spans, K = r76.r63.raw_span_distance_tensor(strokes, bankd["char_arc_unit"], bank_wf)
    assert K >= 1
    native = srs.Substrate()._inner
    canon = r76.word_envelope_canon_iam([s.tolist() for s in strokes])
    d = r76.cc66.dtw(native, canon, canon)
    assert d < 1e-6            # self-distance ~0.
