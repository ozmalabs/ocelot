"""jabberwock_wholeword_run74.py -- RUN 74: WHOLE-WORD HOLISTIC READING.

THE REFRAME (creator): "with cursive -- and reading generally -- you typically are NOT reading
the letters. You look at the SHAPE OF THE WORD first." The whole arc so far (runs 62-72) built
only the ANALYTIC route: segment into letters, recognize each letter, collapse with a lexicon
(run 70: 30.5% within-writer word / 58.0% char). Humans read FAMILIAR words holistically -- the
word as one gesture, no segmentation, no per-letter discrimination. THIS RUN asks: does matching
the query word's FULL trajectory against REAL word-form exemplars (writer-pose-normalized, run
69's frame, at the WHOLE-WORD grain) beat the per-letter route on words the reader has "seen
written before" (the sight vocabulary)?

WHY REAL EXEMPLARS, NOT GENERATED ONES (run 72's finding, carried in verbatim): run 72 proved
generated-vs-real recognition has NEGATIVE separation for ANY compact closed-form generator
(quantized or continuous motor-plan) -- generation is a lossy compression that discards the fine
idiosyncratic detail real ink discrimination needs. The STATIC real-exemplar recognizer (real ink
vs real ink) is what separates (run 69: 55% char). So this run's word-form BANK is REAL held-out
word instances, never a generated template.

WHY RICH TRAJECTORY, NOT THE COARSE ENVELOPE (run 66's own finding, carried in verbatim): run 66's
whole-word matcher used `wordnorm` -- translate-to-start + scale-by-own-arclength + arc-length
resample, NO de-slant, NO writer-relative size -- and it FLOORED: a shuffled-letter (wrong content,
same letters) control generated almost as close a match as the correct order (shuffle-mean minus
join-mean margin only +0.0209, `results/omniglot_gate_run66.log` line 138) because that whole-word
DTW is dominated by the shared left-to-right cursive ENVELOPE, not letter content. THIS run's
"rich" channel is run 69's own writer-relative POSE frame (de-slant shear, translate to local
baseline, SCALE BY THE WRITER'S OWN x-height) applied at the WHOLE-WORD grain instead of run 66's
naive start+arclen-only normalization -- reusing `r69.deslant_points` / `r69.aggregate_scale_slant`
/ `r70.local_frame_for_word_char` VERBATIM, just resampled to `cc66.WORD_N` (64) points instead of
`CANON_N` (24) per letter. The run's own coarse-envelope channel (`cc66.wordnorm`, byte-identical
to run 66's own function) is kept and measured ALONGSIDE the rich channel throughout, as the
ablation control this run's own pre-registration demands ("does it beat the envelope's +0.021
margin").

THE WORD-FORM BANK ("sight vocabulary"): DeepWriting cursive words, grouped BY LABEL. A word is
"in the sight vocabulary" for a query iff the reader has seen >=1 OTHER real instance of it --
WITHIN (the SAME held-out writer wrote it more than once) or CROSS (some BACKGROUND writer wrote
it, pooled). Held query instances are NEVER their own template (exact (writer, sample,
word_point_span) identity is excluded from every bank the query is scored against). COVERAGE
(the fraction of held-out words with >=1 template) is reported honestly over the FULL held-out
population (n=1340, unbiased) -- Zipfian: "the"(300)/"and"(139)/"her"(122)/"are"(88)/... dominate,
exactly the corpus's own sight-vocabulary shape.

THE ARMS:
  (A) PER-LETTER route (run 70, reused): frame+bank machinery from `r69`, decoders from `r70`/`r61`
      applied to per-char 26-class posteriors -- reproduced HERE (own compute, own query set, not
      just cited) so arm (A) and arm (B)/(C) are measured on the IDENTICAL query instances (a
      paired comparison, not two different samples). Run 70's own number (30.5% within / 5.9%
      cross, on ITS OWN 220-word sample) is independently reproduced from its own `decode.json` in
      `tests/test_run74_migrated.py` as a correctness check on this run's own accuracy-computation
      code, and cited here for context.
  (B) WHOLE-WORD HOLISTIC: query's full-word rich (pose) trajectory vs the word-form bank via
      whole-word DTW (held `DtwTo` Term, `cc66.dtw`, UNMODIFIED) -> nearest template's label. NO
      segmentation, NO per-letter comparison -- the competitor set is every OTHER label in the
      bank (same-writer vocabulary for WITHIN, same-length cross-writer labels for CROSS), so this
      is genuine word RECOGNITION among real confusable competitors, not a two-way check against
      one distractor.
  (C) DUAL-ROUTE: holistic (B) where the word is covered (rich channel); per-letter route (A,
      arm b/lexicon) fallback where it is not. The "common words holistic, rare words analytic"
      reading model, measured end to end over the FULL query set (not just the covered subset).

THE ANAGRAM CONTROL (does the whole-word GESTURE beat the envelope's own +0.0209 margin, i.e. does
it use internal trajectory structure and not just start/end/length): (1) a REAL-corpus anagram set
mined from the actual DeepWriting label vocabulary (same-letter-different-order word pairs with
enough instances to support a held-out query PLUS a leave-one-out template of its own label PLUS
>=1 instance of its anagram partner as a competitor -- was/saw, how/who, mean/name, there/three,
any/nay, room/moor, early/layer, left/felt, these/sheet, are/ear, angel/angle); for every queryable
instance, RICH-channel and ENVELOPE-channel margins (partner distance minus true-label distance)
are BOTH computed on the identical query/template pool, so the RICH-vs-ENVELOPE comparison is a
matched, within-run control, not a cross-run citation. (2) a SYNTHETIC construction (deterministic
geometry, no corpus dependency, exercised in `tests/test_run74_migrated.py`): two "letter-like"
sub-shapes ("up", "loop") concatenated in each of two orders share an IDENTICAL start point, end
point, bounding box, and arc-length by construction (pure translation composition is
order-invariant in those four summary statistics) -- so a coarse SUMMARY-STATISTIC "envelope"
(`_envelope_summary`) is mathematically unable to separate the two orders, while whole-word DTW
over the resampled RICH trajectory (`cc66.dtw`) picks the same-order template every time. This
proves the code path is genuinely order-sensitive where a coarse-enough envelope provably is not
(the sharpest version of what run 66's own real-corpus finding showed empirically).

PRE-REGISTERED READ (stated before any accuracy number is computed):
  WIN  if, on COVERED query words, whole-word holistic (B, rich channel) WITHIN-writer word
       accuracy is CI-separated ABOVE run 70's 30.5% per-letter baseline, AND the real-corpus
       anagram discrimination rate (rich channel, fraction of queryable anagram instances whose
       true-label distance beats their anagram partner's) is >= 70% AND materially exceeds the
       matched envelope-channel discrimination rate on the SAME query/template pairs.
  NULL if holistic doesn't clear the bar -- localize: does it work WITHIN-writer at all (bank-size/
       writer-vocabulary-limited) even if CROSS-writer floors (writer-idiosyncratic word-shape
       variability, matching the per-letter arc's own within/cross split)? Does the anagram test
       show the rich channel beating envelope even if absolute word accuracy is weak (localizes to
       "some order-sensitivity present but insufficient discriminative power over ~hundreds of
       real competitor labels", vs "no order-sensitivity gained over run 66's envelope at all")?
  Coverage (the sight-vocabulary fraction) is reported honestly regardless of verdict -- holistic
  reading is BY CONSTRUCTION only available for words seen before; that IS the dual-route point.

DISCIPLINE: donkey=0 -- every geometry primitive (deslant shear, arclength resample, DTW argmin)
is closed-form or the SAME held `DtwTo` Term runs 66/69/70 use, never an SGD-trained net.
OZMA_SEED_PERSIST_DISABLED=1; md5(seeds/stroke_shapes.json) asserted UNCHANGED before/AND after
every stage. `results/run6{1,6,9}_checkpoints/` and `results/run70_checkpoints/` are READ-ONLY
(lexicon, run 66's own log citation, run 69's geometry module, run 70's decode.json for the
per-letter reproduction / cross-check) -- this script writes ONLY `results/run74_checkpoints/*`.
NO git add/commit. `.venv` python for `read` (needs substrate_rs); system python3 fine for the
pure-python stages.

Stages: prep (word selection + word-form bank + writer frames + per-char/per-word query canons,
pure numpy) -> read (whole-word + per-char DTW evaluation + anagram evaluation, needs
substrate_rs, block-checkpointed, resumable) -> decode (arms A/B/C) -> summary.
Run (from the gamma-substrate repo root):
  OZMA_SEED_PERSIST_DISABLED=1 DEEPWRITING_DIR=/tmp/handwriting PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python3 \\
    scripts/jabberwock_wholeword_run74.py --stage <prep|read|decode|summary>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections import Counter, defaultdict

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
os.environ.setdefault("DEEPWRITING_DIR", "/tmp/handwriting")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

import scripts.jabberwock_pose_read_run69 as r69
import scripts.jabberwock_cursive_wordread_run70 as r70
import scripts.jabberwock_cursive_curriculum_run66 as cc66
import scripts.jabberwock_wordread_run61 as r61
from domains import deepwriting_world as dww
from domains import glyph_motor_world as gmw

SEP = "=" * 92
STROKE_SHAPES_SEED = cc66.STROKE_SHAPES_SEED
CKPT_DIR = os.path.join(ROOT, "results", "run74_checkpoints")
LOG = os.path.join(ROOT, "results", "omniglot_gate_run74.log")
os.makedirs(CKPT_DIR, exist_ok=True)

RUN61_CKPT = os.path.join(ROOT, "results", "run61_checkpoints")   # READ-ONLY.
RUN61_LEXICON = os.path.join(RUN61_CKPT, "lexicon.json")
RUN70_CKPT = os.path.join(ROOT, "results", "run70_checkpoints")   # READ-ONLY.
RUN70_DECODE = os.path.join(RUN70_CKPT, "decode.json")
RUN70_SUMMARY = os.path.join(RUN70_CKPT, "summary.json")

# ------------------------------------------------------------------------------------------- #
#  PRE-REGISTERED CONSTANTS -- reused verbatim from 62-70's shared split where one exists; NEW
#  constants for this run's own word-form-bank/query selection are marked NEW.
# ------------------------------------------------------------------------------------------- #
SPLIT = r69.SPLIT                                     # "training"
WRITER_SPLIT_SEED = r69.WRITER_SPLIT_SEED             # 20260706, identical to 62/64/66/69/70.
N_BACKGROUND_FRAC = r69.N_BACKGROUND_FRAC             # 0.5
WORD_MIN_LEN, WORD_MAX_LEN = r70.WORD_MIN_LEN, r70.WORD_MAX_LEN   # 3, 8
LOCAL_WINDOW = r69.LOCAL_WINDOW
M_BANK_CHAR = r69.M_BANK                              # 3 -- per-letter route (arm A), r69's own.
PRIMARY_LAMBDA_POSE = r70.PRIMARY_LAMBDA_POSE         # 1.0, r69's own pre-registered mix weight.
LOWER_CLASSES = r69.LOWER_CLASSES
LETTERS26 = r70.LETTERS26
WORD_N = cc66.WORD_N                                  # 64 -- whole-word DTW resample length.

M_BANK_WORD = 5                        # NEW: templates/label in the word-form bank (both conds).
CROSS_EXTRA_TARGET = 150               # NEW: extra cross-only-covered queries beyond the within
                                        # pool (which is the FULL corpus within-covered population).
TEST_SELECT_SEED_EXTRA = 20260904      # NEW, pre-registered before running.
BANK_SELECT_SEED = 20260905            # NEW, pre-registered before running.
PER_CALL_BUDGET_SECONDS = 480.0

# Reading floors/citations this run reports against (task-given / prior-run, cited verbatim).
RUN70_WITHIN_WORD = 30.5     # run 70's own within-writer per-letter+lexicon word accuracy (%).
RUN70_CROSS_WORD = 5.9       # run 70's own cross-writer per-letter+lexicon word accuracy (%).
RUN66_SHUFFLE_MARGIN = 0.0209   # run 66's own coarse-envelope shuffled-letter margin (DTW units,
                                 # `results/omniglot_gate_run66.log` line 138) -- context only, NOT
                                 # unit-comparable to this run's x-height-scaled rich channel (see
                                 # ANOMALIES).

BAR_WITHIN_HOLISTIC = RUN70_WITHIN_WORD   # pre-registered WIN bar for arm (B) within-writer.
BAR_ANAGRAM_RATE = 70.0                   # pre-registered WIN bar for the real-corpus anagram test.


# ============================================================================================= #
#  I/O + seed guard (identical pattern to runs 61/66/68/69/70).
# ============================================================================================= #
def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _ckpt(name):
    return os.path.join(CKPT_DIR, name)


def _save(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f)


def _load(path):
    with open(path) as f:
        return json.load(f)


def _require(name):
    p = _ckpt(name)
    if not os.path.exists(p):
        raise SystemExit(f"WALL: run the stage that produces {name} first.")
    return _load(p)


def _seed_guard(stage, before=None):
    cur = _md5(STROKE_SHAPES_SEED)
    if before is not None and cur != before:
        raise SystemExit(f"HARD STOP: seeds/stroke_shapes.json md5 changed during {stage} "
                          f"({before} -> {cur}).")
    return cur


def _wilson(k, n):
    return r61._wilson_ci(k, n)


def _mcnemar(a, b):
    return r61._mcnemar(a, b)


# ============================================================================================= #
#  GEOMETRY -- the RICH (writer-pose, run 69's frame at word grain) + ENVELOPE (run 66's own
#  `wordnorm`, unmodified) whole-word channels. Pure numpy, donkey=0.
# ============================================================================================= #
def word_key(w: dict) -> tuple:
    return (w["writer"], w["word"], w["sample"], tuple(w["word_point_span"]))


def _norm_key(k) -> tuple:
    """Canonicalize a word-identity key (list-of-4 or tuple-of-4, span either a list or tuple) to
    one hashable/comparable tuple form -- so a JSON round-trip (tuples -> lists) never defeats an
    identity comparison."""
    return (k[0], k[1], k[2], tuple(k[3]))


def word_baseline(dw: dict, word_rec: dict, ws_index: dict):
    """Median local baseline over the word's own char_segs (reuses `r70.local_frame_for_word_char`
    VERBATIM per char, per-word aggregation is the only new arithmetic: a median is the
    closed-form robust choice run 69 itself uses for x_height/slant). Returns (baseline,
    n_fallback)."""
    bases, n_fb = [], 0
    for cs in word_rec["char_segs"]:
        b, fb = r70.local_frame_for_word_char(dw, word_rec, cs, ws_index)
        bases.append(b)
        n_fb += int(fb)
    return (float(np.median(bases)) if bases else 0.0), n_fb


def word_pose_canon(word_rec: dict, baseline: float, x_height: float, slant_deg: float,
                     n: int = WORD_N) -> list:
    """THE RICH whole-word channel: `r69.pose_canon`'s exact recipe (de-slant shear, translate to
    baseline + own entry-x, scale by the WRITER'S x-height, arc-length resample) applied to the
    word's FULL connected trajectory (`cc66.word_points`) instead of one letter's strokes, resampled
    to `WORD_N` (64, run 66's own whole-word length) instead of `CANON_N` (24, per-letter)."""
    pts = cc66.word_points(word_rec)
    ds = r69.deslant_points(pts, slant_deg, baseline)
    xh = x_height or 1.0
    x0 = ds[0, 0]
    norm = np.stack([(ds[:, 0] - x0) / xh, (ds[:, 1] - baseline) / xh], axis=1)
    return gmw._resample_arclen(norm, n).tolist()


def word_envelope_canon(word_rec: dict, n: int = WORD_N) -> list:
    """THE COARSE-ENVELOPE control channel: `cc66.wordnorm`, byte-identical to run 66's own whole-
    word normalization (translate-to-start + scale-by-OWN-arclength + resample; NO de-slant, NO
    writer-relative size). Kept alongside the rich channel throughout as the ablation this run's
    pre-registration demands."""
    return cc66.wordnorm(cc66.word_points(word_rec), n)


def _build_word_bank(pool_words: list, frame_by_writer_fn, m_bank: int, seed: int, dw: dict,
                      ws_index: dict) -> dict:
    """THE WORD-FORM BANK: group `pool_words` BY LABEL, keep up to `m_bank` seeded exemplars/label
    (rich + envelope canon, using each exemplar's OWN writer's frame via `frame_by_writer_fn`).
    IDENTITY KEYS are kept on every bank entry (`word_key`) so a query can be SELF-EXCLUDED
    (leave-one-out) from its own label's templates AT READ TIME -- this function does NOT exclude
    "this run's test set" up front. That distinction matters: a (writer, word) group of size
    EXACTLY 2 is the most common real-corpus within-covered case (84/133 such groups) -- BOTH
    instances become their own query (see `build_prep`'s `within_pool_all`). Excluding the whole
    test set here would leave EACH of those two queries with an EMPTY bank for their own true
    label (the only other instance IS also a query, hence also excluded) -- collapsing "has
    within-writer coverage" to a false promise for the majority of the within-covered population.
    Leave-one-out at read time (`stage_read`'s `_others`) is the correct exclusion: a bank entry
    that also happens to serve as another query elsewhere in this evaluation is fine to reuse as a
    TEMPLATE (ordinary leave-one-out cross-validation), it just may never be its OWN template. See
    `tests/test_run74_migrated.py::test_build_word_bank_and_self_exclusion_survive_group_size_two`."""
    by_word = defaultdict(list)
    for w in pool_words:
        by_word[w["word"]].append(w)
    out = {}
    for i, word in enumerate(sorted(by_word)):
        insts = by_word[word]
        rng = np.random.default_rng(seed + i)
        idx = rng.choice(len(insts), size=min(m_bank, len(insts)), replace=False)
        canons = []
        for j in idx:
            w = insts[int(j)]
            fr = frame_by_writer_fn(w["writer"])
            baseline, _fb = word_baseline(dw, w, ws_index)
            canons.append({"key": list(word_key(w)),
                           "rich": word_pose_canon(w, baseline, fr["x_height"], fr["slant_deg"]),
                           "env": word_envelope_canon(w)})
        out[word] = canons
    return out


def _envelope_summary(pts) -> np.ndarray:
    """A DELIBERATELY coarser-than-run-66 envelope for the SYNTHETIC anagram unit test only: start
    point, end point, x-extent, arc-length (6 numbers). Two same-part-set, different-ORDER
    trajectories built by pure translation composition (`_synthetic_word`) are IDENTICAL in every
    one of these 6 numbers by construction (composition of translations is order-invariant in
    start/end/extent/length) -- so this representation is PROVABLY unable to separate them, the
    sharpest version of what run 66's real-corpus +0.0209 margin showed empirically. Not used
    anywhere in the real-corpus pipeline (which always uses the richer `wordnorm`/rich-trajectory
    channels, both already order-SENSITIVE to some degree per run 66's own finding)."""
    pts = np.asarray(pts, float)
    d = np.diff(pts, axis=0)
    arclen = float(np.sum(np.linalg.norm(d, axis=1))) if len(pts) > 1 else 0.0
    return np.array([pts[0, 0], pts[0, 1], pts[-1, 0], pts[-1, 1],
                      pts[:, 0].max() - pts[:, 0].min(), arclen])


def _synthetic_letterlike_shape(kind: str, n: int = 20) -> np.ndarray:
    """Two distinguishable synthetic 'letter' sub-shapes, each an (n,2) polyline that starts AND
    ends at y=0 with x running 0->1 -- a upward bump ('up') vs a shallower downward bump ('loop'),
    clearly distinct in shape (opposite sign, different depth) but with IDENTICAL local start
    (0,0) and end (1,0). Both endpoints pinned to y=0 is what makes `_synthetic_word`'s
    concatenation gap a pure HORIZONTAL step regardless of which shape precedes it -- the property
    the order-invariance proof (`_envelope_summary`'s docstring) actually needs."""
    t = np.linspace(0.0, 1.0, n)
    if kind == "up":
        y = 4.0 * t * (1.0 - t)              # bump UP, peak height 1 at t=0.5.
    else:
        y = -2.0 * t * (1.0 - t)             # bump DOWN, peak depth -0.5 at t=0.5 -- distinct shape.
    return np.stack([t, y], axis=1)


def _synthetic_word(order: tuple, gap: float = 1.2) -> np.ndarray:
    """Concatenate the two sub-shapes end to end (pen-continuity gap) in the given ORDER. Pure
    translation composition -> start point, end point, x-extent, and arc-length are IDENTICAL
    across any permutation of the same parts (see `_envelope_summary`'s docstring); only the
    per-position trajectory differs by order."""
    shapes = {"up": _synthetic_letterlike_shape("up"), "loop": _synthetic_letterlike_shape("loop")}
    cursor = np.zeros(2)
    out = []
    for k in order:
        s = shapes[k] + cursor
        out.append(s)
        cursor = s[-1] + np.array([gap, 0.0])
    return np.concatenate(out, axis=0)


def synthetic_anagram_demo(native) -> dict:
    """THE SYNTHETIC anagram control (pre-registered unit-test construction, also run here for the
    report): query = ('up','loop') order; SAME-order template = ('up','loop'); REORDERED template
    = ('loop','up'). RICH (whole-word DTW over the resampled trajectory) must prefer the same-order
    template; the coarse `_envelope_summary` must be UNABLE to separate them (identical by
    construction)."""
    q = gmw._resample_arclen(_synthetic_word(("up", "loop")), WORD_N).tolist()
    same = gmw._resample_arclen(_synthetic_word(("up", "loop")), WORD_N).tolist()
    reordered = gmw._resample_arclen(_synthetic_word(("loop", "up")), WORD_N).tolist()
    d_same = cc66.dtw(native, q, same)
    d_reordered = cc66.dtw(native, q, reordered)
    env_q = _envelope_summary(_synthetic_word(("up", "loop")))
    env_same = _envelope_summary(_synthetic_word(("up", "loop")))
    env_reordered = _envelope_summary(_synthetic_word(("loop", "up")))
    env_d_same = float(np.linalg.norm(env_q - env_same))
    env_d_reordered = float(np.linalg.norm(env_q - env_reordered))
    return {"d_same": d_same, "d_reordered": d_reordered, "rich_separates": d_same < d_reordered,
            "env_d_same": env_d_same, "env_d_reordered": env_d_reordered,
            "env_separates": abs(env_d_same - env_d_reordered) > 1e-9}


# ============================================================================================= #
#  REAL-CORPUS ANAGRAM SET.
# ============================================================================================= #
ANAGRAM_PAIRS = [("was", "saw"), ("how", "who"), ("mean", "name"), ("there", "three"),
                  ("any", "nay"), ("room", "moor"), ("early", "layer"), ("left", "felt"),
                  ("these", "sheet"), ("are", "ear"), ("angel", "angle")]


# ============================================================================================= #
#  STAGE: prep -- word selection, word-form bank (within + cross), writer frames, query canons.
#  Pure numpy, no native calls.
# ============================================================================================= #
def build_prep(m_bank_word: int = M_BANK_WORD, m_bank_char: int = M_BANK_CHAR,
               cross_extra_target: int = CROSS_EXTRA_TARGET, dw=None, all_glyphs=None) -> dict:
    if dw is None:
        dw = dww.load_deepwriting(SPLIT)
    if all_glyphs is None:
        all_glyphs = dww.extract_char_glyphs(dw)

    words_for_split = dww.extract_words(dw, min_len=WORD_MIN_LEN, max_len=WORD_MAX_LEN,
                                        lowercase_only=True, complete_only=True)
    bg_words, ho_words = dww.writer_split(words_for_split, n_background_frac=N_BACKGROUND_FRAC,
                                          seed=WRITER_SPLIT_SEED)
    bg_writers = {w["writer"] for w in bg_words}
    ho_writers = {w["writer"] for w in ho_words}
    assert bg_writers.isdisjoint(ho_writers), "writer split must be disjoint"

    by_writer = r69._group_by_writer(all_glyphs)
    ws_index = r69._index_by_writer_sample(all_glyphs)

    # ---- coverage over the FULL held-out population (unbiased, the honest sight-vocab number). ---
    bg_by_word = defaultdict(list)
    for w in bg_words:
        bg_by_word[w["word"]].append(w)
    ho_by_ww = defaultdict(list)
    for w in ho_words:
        ho_by_ww[(w["writer"], w["word"])].append(w)
    ho_by_writer = defaultdict(list)
    for w in ho_words:
        ho_by_writer[w["writer"]].append(w)

    within_pool_all = [w for w in ho_words if len(ho_by_ww[(w["writer"], w["word"])]) >= 2]
    cross_pool_all = [w for w in ho_words if w["word"] in bg_by_word]
    within_keys_all = {word_key(w) for w in within_pool_all}
    coverage = {
        "n_ho_total": len(ho_words),
        "n_within_covered": len(within_pool_all),
        "n_cross_covered": len(cross_pool_all),
        "n_either_covered": len({word_key(w) for w in within_pool_all} |
                                 {word_key(w) for w in cross_pool_all}),
    }

    # ---- the evaluation query set: ALL within-covered (the full achievable population, n=390) +
    #      a seeded, per-writer-capped sample of cross-ONLY-covered instances (r70's OWN generic
    #      `select_test_words`, unmodified -- it only needs writer/word/sample/word_point_span). --
    cross_only_pool = [w for w in cross_pool_all if word_key(w) not in within_keys_all]
    cross_extra = r70.select_test_words(cross_only_pool, cross_extra_target, TEST_SELECT_SEED_EXTRA)
    test_words = within_pool_all + cross_extra
    has_within_flag = {word_key(w): (word_key(w) in within_keys_all) for w in test_words}
    has_cross_flag = {word_key(w): (w["word"] in bg_by_word) for w in test_words}

    test_writers = sorted({w["writer"] for w in test_words})
    test_samples_by_writer = defaultdict(set)
    for w in test_words:
        test_samples_by_writer[w["writer"]].add(w["sample"])

    # ---- writer frames: OWN (test writers, excluding their own selected-query samples) + ALL
    #      background writers (no exclusion -- they never serve as a query). Same convention as
    #      r69/r70's `frame_of_writer`. ----
    own_frame = {}
    n_degenerate_own = 0
    for w in test_writers:
        gbs = r69.glyphs_by_sample(by_writer.get(w, []), exclude_samples=test_samples_by_writer[w])
        fr = r69.aggregate_scale_slant(gbs)
        own_frame[w] = fr
        n_degenerate_own += int(fr["n_xh_obs"] == 0)

    bg_frame = {}
    bg_glyphs_pool = {}
    for w in bg_writers:
        gbs = r69.glyphs_by_sample(by_writer.get(w, []))
        bg_frame[w] = r69.aggregate_scale_slant(gbs)
        bg_glyphs_pool.update(gbs)
    population_frame = r69.aggregate_scale_slant(bg_glyphs_pool)

    # ---- WORD-FORM BANK (A): per-test-writer vocabulary -- every word THAT writer wrote (ho), up
    #      to `m_bank_word` templates/word, seeded so re-running prep is deterministic. Doubles as
    #      the WITHIN-condition competitor set (a writer's own vocabulary IS the label space a
    #      within-bank query is decoded over). See `_build_word_bank`'s own docstring for why
    #      exclusion is leave-one-out at READ time, not up front here.
    within_vocab_by_writer = {}
    for w in test_writers:
        within_vocab_by_writer[str(w)] = _build_word_bank(
            ho_by_writer.get(w, []), lambda _w: own_frame[w], m_bank_word, BANK_SELECT_SEED + w,
            dw, ws_index)

    cross_bank_by_label = _build_word_bank(
        bg_words, lambda w: bg_frame[w], m_bank_word, BANK_SELECT_SEED + 10_000_000, dw, ws_index)
    length_index_cross = defaultdict(list)
    for word in cross_bank_by_label:
        length_index_cross[len(word)].append(word)

    # ---- per-letter route (arm A) frame/bank -- LITERAL reuse of r69's own bank machinery
    #      (`select_bank`/`_bank_canons`), on THIS run's own test writers, so arm A is measured on
    #      the identical query instances as arm B/C. ----
    frame_of_writer_all = {**{str(k): v for k, v in bg_frame.items()},
                           **{str(k): v for k, v in own_frame.items()}}
    frame_of_writer_all_int = {**bg_frame, **own_frame}
    own_charbank_by_writer, own_charbank_coverage = {}, {}
    for w in test_writers:
        pool_w = [g for g in by_writer.get(w, []) if g["sample"] not in test_samples_by_writer[w]]
        raw = r69.select_bank(pool_w, LOWER_CLASSES, m_bank_char,
                              np.random.default_rng(BANK_SELECT_SEED + 20_000_000 + w))
        own_charbank_by_writer[str(w)] = r69._bank_canons(raw, frame_of_writer_all_int, ws_index)
        own_charbank_coverage[str(w)] = {str(c): len(v) for c, v in raw.items()}

    cross_char_pool = [g for w in bg_writers for g in by_writer.get(w, []) if g["class"] in LOWER_CLASSES]
    cross_charbank_raw = r69.select_bank(cross_char_pool, LOWER_CLASSES, m_bank_char,
                                         np.random.default_rng(BANK_SELECT_SEED + 30_000_000))
    cross_charbank = r69._bank_canons(cross_charbank_raw, frame_of_writer_all_int, ws_index)

    # ---- per-query canons: whole-word RICH + ENVELOPE, and per-char inv/pose (arm A). ----
    queries = []
    n_word_frame_fallback = 0
    for wid, wd in enumerate(test_words):
        w = wd["writer"]
        own_fr = own_frame[w]
        baseline, n_fb = word_baseline(dw, wd, ws_index)
        n_word_frame_fallback += int(n_fb > 0)
        rich = word_pose_canon(wd, baseline, own_fr["x_height"], own_fr["slant_deg"])
        env = word_envelope_canon(wd)
        chars = []
        for cs in wd["char_segs"]:
            cbaseline, _cfb = r70.local_frame_for_word_char(dw, wd, cs, ws_index)
            chars.append({
                "true_symbol": cs["symbol"],
                "inv": r69.invariant_canon(cs["strokes"]),
                "pose_own": r69.pose_canon(cs["strokes"], cbaseline, own_fr["x_height"],
                                           own_fr["slant_deg"]),
                "pose_pop": r69.pose_canon(cs["strokes"], cbaseline, population_frame["x_height"],
                                           population_frame["slant_deg"]),
            })
        queries.append({
            "wid": wid, "writer": w, "word": wd["word"], "sample": wd["sample"],
            "word_point_span": list(wd["word_point_span"]), "len": len(wd["word"]),
            "has_within": has_within_flag[word_key(wd)], "has_cross": has_cross_flag[word_key(wd)],
            "rich": rich, "env": env, "chars": chars,
        })

    # ---- ANAGRAM instances: every corpus instance (bg+ho pooled) of every word appearing in
    #      ANAGRAM_PAIRS, rich+env canon precomputed (own writer's frame, no test-sample exclusion
    #      -- see ANOMALIES; this is a targeted diagnostic control, not the headline table). ----
    anagram_words = sorted({w for pair in ANAGRAM_PAIRS for w in pair})
    all_words_pool = bg_words + ho_words
    anagram_instances = defaultdict(list)
    for w in all_words_pool:
        if w["word"] not in anagram_words:
            continue
        writer = w["writer"]
        fr = own_frame.get(writer) or bg_frame.get(writer)
        if fr is None:
            gbs = r69.glyphs_by_sample(by_writer.get(writer, []))
            fr = r69.aggregate_scale_slant(gbs)
        baseline, _fb = word_baseline(dw, w, ws_index)
        anagram_instances[w["word"]].append({
            "key": list(word_key(w)),
            "rich": word_pose_canon(w, baseline, fr["x_height"], fr["slant_deg"]),
            "env": word_envelope_canon(w),
        })

    return {
        "bg_writers": sorted(bg_writers), "ho_writers": sorted(ho_writers),
        "test_writers": test_writers,
        "coverage": coverage,
        "n_within_pool": len(within_pool_all), "n_cross_extra": len(cross_extra),
        "n_test_words": len(test_words),
        "n_degenerate_own_frame": n_degenerate_own,
        "n_word_frame_fallback": n_word_frame_fallback,
        "word_len_dist": dict(Counter(len(wd["word"]) for wd in test_words)),
        "word_label_top": Counter(wd["word"] for wd in test_words).most_common(15),
        "within_vocab_by_writer": within_vocab_by_writer,
        "cross_bank_by_label": cross_bank_by_label,
        "length_index_cross": length_index_cross,
        "own_charbank_by_writer": own_charbank_by_writer,
        "own_charbank_coverage": own_charbank_coverage,
        "cross_charbank": cross_charbank,
        "queries": queries,
        "anagram_pairs": ANAGRAM_PAIRS,
        "anagram_instances": {k: v for k, v in anagram_instances.items()},
    }


def stage_prep():
    print(f"\n{SEP}\n  STAGE: prep (word-form bank + writer frames + query canons -- pure numpy, "
          f"no native)\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("prep")
    print(f"  seeds/stroke_shapes.json md5 (before): {md5_before}", flush=True)

    out = build_prep()
    out["stroke_shapes_md5"] = md5_before
    _save(out, _ckpt("prep.json"))
    _seed_guard("prep", md5_before)

    cov = out["coverage"]
    print(f"  bg writers={len(out['bg_writers'])}  ho writers={len(out['ho_writers'])}", flush=True)
    print(f"  SIGHT-VOCAB COVERAGE (full held-out population, n={cov['n_ho_total']}, unbiased):", flush=True)
    print(f"    within: {cov['n_within_covered']}/{cov['n_ho_total']} = "
          f"{100*cov['n_within_covered']/cov['n_ho_total']:.1f}%", flush=True)
    print(f"    cross:  {cov['n_cross_covered']}/{cov['n_ho_total']} = "
          f"{100*cov['n_cross_covered']/cov['n_ho_total']:.1f}%", flush=True)
    print(f"    either: {cov['n_either_covered']}/{cov['n_ho_total']} = "
          f"{100*cov['n_either_covered']/cov['n_ho_total']:.1f}%", flush=True)
    print(f"  evaluation sample (enriched by design, NOT organic): within_pool={out['n_within_pool']} "
          f"+ cross_extra={out['n_cross_extra']} = {out['n_test_words']} test words, "
          f"{len(out['test_writers'])} test writers", flush=True)
    print(f"  word length dist: {sorted(out['word_len_dist'].items())}", flush=True)
    print(f"  top word labels in sample: {out['word_label_top']}", flush=True)
    print(f"  degenerate own-frame writers: {out['n_degenerate_own_frame']}/{len(out['test_writers'])}"
          f"  word-char local-frame fallback: {out['n_word_frame_fallback']}", flush=True)
    n_anagram_insts = sum(len(v) for v in out["anagram_instances"].values())
    print(f"  anagram instances found: {n_anagram_insts} across "
          f"{len(out['anagram_instances'])}/{len(set(w for p in ANAGRAM_PAIRS for w in p))} words", flush=True)
    print(f"  saved -> {_ckpt('prep.json')}  [prep {time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: read -- holistic whole-word DTW (rich+env, within+cross), per-letter 26-class posteriors,
#  anagram evaluation. Needs substrate_rs. Block-checkpointed, resumable.
# ============================================================================================= #
def _argmin_label(dists: dict):
    if not dists:
        return None, None
    lab = min(dists, key=dists.get)
    return lab, dists[lab]


def stage_read():
    print(f"\n{SEP}\n  STAGE: read -- whole-word holistic DTW + per-letter posteriors + anagram "
          f"(native DTW)\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("read")
    import substrate_rs as srs
    native = srs.Substrate()._inner
    prep = _require("prep.json")
    queries = prep["queries"]
    within_vocab_by_writer = prep["within_vocab_by_writer"]
    cross_bank_by_label = prep["cross_bank_by_label"]
    length_index_cross = prep["length_index_cross"]
    own_charbank_by_writer = prep["own_charbank_by_writer"]
    cross_charbank = prep["cross_charbank"]

    out_path = _ckpt("read.json")
    state = _load(out_path) if os.path.exists(out_path) else {"records": [], "anagram": None,
                                                               "synthetic": None, "done": False}
    if state.get("done"):
        print(f"  read already COMPLETE (n={len(state['records'])}).", flush=True)
        return 0
    done = {r["wid"] for r in state["records"]}
    deadline = time.time() + PER_CALL_BUDGET_SECONDS
    n_new = 0

    for q in queries:
        if q["wid"] in done:
            continue
        w = str(q["writer"])
        L = q["len"]
        qkey = _norm_key([q["writer"], q["word"], q["sample"], q["word_point_span"]])

        def _others(canons):
            """Leave-one-out: drop the bank entry that IS this exact query instance (self-
            exclusion by identity key, not by pre-filtering the whole test set -- see
            `_build_word_bank`'s docstring). Keys are normalized (`_norm_key`) so list/tuple
            nesting differences from a JSON round-trip never defeat the comparison."""
            return [c for c in canons if _norm_key(c["key"]) != qkey]

        # -- holistic WITHIN: competitor set = this writer's own vocabulary. --
        vocab = within_vocab_by_writer.get(w, {})
        within_rich, within_env = {}, {}
        for lab, canons in vocab.items():
            others = _others(canons)
            if not others:
                continue
            within_rich[lab] = min(cc66.dtw(native, q["rich"], c["rich"]) for c in others)
            within_env[lab] = min(cc66.dtw(native, q["env"], c["env"]) for c in others)

        # -- holistic CROSS: competitor set = same-length cross-bank labels. --
        same_len = length_index_cross.get(str(L), length_index_cross.get(L, []))
        cross_rich, cross_env = {}, {}
        for lab in same_len:
            others = _others(cross_bank_by_label[lab])
            if not others:
                continue
            cross_rich[lab] = min(cc66.dtw(native, q["rich"], c["rich"]) for c in others)
            cross_env[lab] = min(cc66.dtw(native, q["env"], c["env"]) for c in others)

        # -- per-letter route (arm A), reproducing r69/r70's own combined posterior. --
        ob = own_charbank_by_writer.get(w, {})
        within_char_dists, cross_char_dists = [], []
        for ch in q["chars"]:
            invB = r69._class_cost(native, ch["inv"], ob, "inv")
            poseE = r69._class_cost(native, ch["pose_own"], ob, "pose")
            invA = r69._class_cost(native, ch["inv"], cross_charbank, "inv")
            poseC = r69._class_cost(native, ch["pose_pop"], cross_charbank, "pose")
            within_char_dists.append([invB[c] + PRIMARY_LAMBDA_POSE * poseE[c] for c in range(26)])
            cross_char_dists.append([invA[c] + PRIMARY_LAMBDA_POSE * poseC[c] for c in range(26)])

        state["records"].append({
            "wid": q["wid"], "writer": q["writer"], "word": q["word"], "len": L,
            "has_within": q["has_within"], "has_cross": q["has_cross"],
            "within_rich": within_rich, "within_env": within_env,
            "cross_rich": cross_rich, "cross_env": cross_env,
            "within_char_dists": within_char_dists, "cross_char_dists": cross_char_dists,
        })
        n_new += 1
        if n_new % 25 == 0:
            _save(state, out_path)
            _seed_guard("read", md5_before)
            n = len(state["records"])
            print(f"    ... {n}/{len(queries)} words  [{time.time()-t0:.1f}s]", flush=True)
            if time.time() > deadline:
                _save(state, out_path)
                _seed_guard("read", md5_before)
                print(f"  WALL-BUDGET: {len(state['records'])}/{len(queries)} done -- re-invoke "
                      f"--stage read to resume.", flush=True)
                return 2

    # -- anagram evaluation (leave-one-out over pooled corpus instances) + synthetic demo. --
    anagram_instances = prep["anagram_instances"]
    pair_partner = {}
    for a, b in prep["anagram_pairs"]:
        pair_partner[a] = b
        pair_partner[b] = a
    anagram_records = []
    for word, partner in pair_partner.items():
        insts = anagram_instances.get(word, [])
        partner_insts = anagram_instances.get(partner, [])
        if not partner_insts:
            continue
        for qi, q in enumerate(insts):
            templates_true = [insts[j] for j in range(len(insts)) if j != qi]
            if not templates_true:
                continue
            d_true_rich = min(cc66.dtw(native, q["rich"], t["rich"]) for t in templates_true)
            d_partner_rich = min(cc66.dtw(native, q["rich"], t["rich"]) for t in partner_insts)
            d_true_env = min(cc66.dtw(native, q["env"], t["env"]) for t in templates_true)
            d_partner_env = min(cc66.dtw(native, q["env"], t["env"]) for t in partner_insts)
            anagram_records.append({
                "word": word, "partner": partner, "key": q["key"],
                "d_true_rich": d_true_rich, "d_partner_rich": d_partner_rich,
                "d_true_env": d_true_env, "d_partner_env": d_partner_env,
                "correct_rich": d_true_rich < d_partner_rich,
                "correct_env": d_true_env < d_partner_env,
            })
    state["anagram"] = anagram_records
    state["synthetic"] = synthetic_anagram_demo(native)

    state["done"] = True
    _save(state, out_path)
    _seed_guard("read", md5_before)
    print(f"  read {len(state['records'])} words  |  anagram queries={len(anagram_records)}  "
          f"[{time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  DECODERS -- pure, importable, reused by tests.
# ============================================================================================= #
def decode_holistic(dists: dict):
    lab, _d = _argmin_label(dists)
    return lab


def decode_per_letter(char_dists: list, true_len: int, lex_by_len: dict, logfreq: dict):
    return {"a": r70.decode_arm_a(char_dists), "b": r70.decode_arm_b(char_dists, true_len,
                                                                     lex_by_len, logfreq)}


def decode_dual(holistic_pred, covered: bool, per_letter_b_pred: str):
    return holistic_pred if (covered and holistic_pred is not None) else per_letter_b_pred


# ============================================================================================= #
#  STAGE: decode -- arms A/B/C over WITHIN and CROSS, envelope ablation, for every test word.
# ============================================================================================= #
def stage_decode():
    print(f"\n{SEP}\n  STAGE: decode (arms A/per-letter, B/holistic rich+env, C/dual-route)\n{SEP}",
          flush=True)
    t0 = time.time()
    md5_before = _seed_guard("decode")
    lexicon = _load(RUN61_LEXICON)
    lex_by_len = r61._lex_by_len(lexicon["lexicon"])
    logfreq = lexicon["logfreq"]

    rd = _require("read.json")
    if not rd.get("done"):
        raise SystemExit("WALL: read not COMPLETE -- re-invoke --stage read.")

    per_word = []
    for r in rd["records"]:
        word, L = r["word"], r["len"]
        pl_within = decode_per_letter(r["within_char_dists"], L, lex_by_len, logfreq)
        pl_cross = decode_per_letter(r["cross_char_dists"], L, lex_by_len, logfreq)
        hol_within_rich = decode_holistic(r["within_rich"])
        hol_within_env = decode_holistic(r["within_env"])
        hol_cross_rich = decode_holistic(r["cross_rich"])
        hol_cross_env = decode_holistic(r["cross_env"])
        rec = {
            "wid": r["wid"], "writer": r["writer"], "word": word, "len": L,
            "has_within": r["has_within"], "has_cross": r["has_cross"],
            "within": {"a": pl_within["a"], "b": pl_within["b"],
                      "hol_rich": hol_within_rich, "hol_env": hol_within_env,
                      "dual": decode_dual(hol_within_rich, r["has_within"], pl_within["b"])},
            "cross": {"a": pl_cross["a"], "b": pl_cross["b"],
                     "hol_rich": hol_cross_rich, "hol_env": hol_cross_env,
                     "dual": decode_dual(hol_cross_rich, r["has_cross"], pl_cross["b"])},
        }
        per_word.append(rec)

    _save({"per_word": per_word, "stroke_shapes_md5": md5_before}, _ckpt("decode.json"))
    _seed_guard("decode", md5_before)
    print(f"  decoded {len(per_word)} words  [{time.time()-t0:.1f}s]", flush=True)
    print(f"  saved -> {_ckpt('decode.json')}", flush=True)
    return 0


# ============================================================================================= #
#  REPORTING / VERDICT.
# ============================================================================================= #
def _acc_report(per_word: list, cond: str, arm: str, only_covered: bool, cov_key: str) -> dict:
    word_ok = char_ok = n_char = n = 0
    flags = []
    for pw in per_word:
        if only_covered and not pw[cov_key]:
            continue
        pred = pw[cond][arm]
        true = pw["word"]
        n += 1
        if pred is None:
            flags.append(False)
            n_char += len(true)
            continue
        ok = (pred == true)
        word_ok += ok
        flags.append(ok)
        c = sum(1 for i in range(min(len(pred), len(true))) if pred[i] == true[i])
        char_ok += c
        n_char += len(true)
    return {"n": n, "word_ok": word_ok, "word_acc": word_ok / n if n else 0.0,
            "word_ci": list(_wilson(word_ok, n)), "char_acc": char_ok / n_char if n_char else 0.0,
            "flags": flags}


def _row(label, rep):
    pct = 100 * rep["word_acc"]
    ci = rep["word_ci"]
    print(f"  {label:<44}{pct:>9.1f}%{f'[{100*ci[0]:.1f},{100*ci[1]:.1f}]':>15}"
          f"{100*rep['char_acc']:>11.1f}%{'n='+str(rep['n']):>9}")


def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 74 SCOREBOARD (WHOLE-WORD HOLISTIC READING)\n{SEP}",
          flush=True)
    md5_now = _seed_guard("summary")
    prep = _require("prep.json")
    print(f"  SEED-GUARD: seeds/stroke_shapes.json md5 = {md5_now}  "
          f"(== prep capture {prep['stroke_shapes_md5']}: "
          f"{md5_now == prep['stroke_shapes_md5']})")
    dec = _require("decode.json")
    per_word = dec["per_word"]
    n = len(per_word)
    cov = prep["coverage"]

    print(f"\n  n test words = {n}  (test writers: {len(prep['test_writers'])})")
    print(f"  SIGHT-VOCAB COVERAGE (full held-out population, n={cov['n_ho_total']}, unbiased):")
    print(f"    within {100*cov['n_within_covered']/cov['n_ho_total']:.1f}%  "
          f"cross {100*cov['n_cross_covered']/cov['n_ho_total']:.1f}%  "
          f"either {100*cov['n_either_covered']/cov['n_ho_total']:.1f}%")
    print(f"  (evaluation sample is ENRICHED for statistical power -- within pool taken in FULL "
          f"({prep['n_within_pool']}), cross topped up with a seeded {prep['n_cross_extra']}-word "
          f"sample; this is NOT the organic coverage rate, reported above.)")

    print(f"\n  === WORD + CHAR ACCURACY -- arm (A) per-letter+lexicon vs (B) holistic vs (C) "
          f"dual-route, x WITHIN vs CROSS, on COVERED query words ===")
    hdr = f"  {'condition':<44}{'word_acc':>9}{'word_CI':>15}{'char_acc':>11}{'n':>9}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))

    reps = {}
    for cond, cov_key in (("within", "has_within"), ("cross", "has_cross")):
        reps[(cond, "a")] = _acc_report(per_word, cond, "a", True, cov_key)
        reps[(cond, "b")] = _acc_report(per_word, cond, "b", True, cov_key)
        reps[(cond, "hol_rich")] = _acc_report(per_word, cond, "hol_rich", True, cov_key)
        reps[(cond, "hol_env")] = _acc_report(per_word, cond, "hol_env", True, cov_key)
        reps[(cond, "dual_full")] = _acc_report(per_word, cond, "dual", False, cov_key)

    for cond, lab in (("within", "WITHIN-writer"), ("cross", "CROSS-writer")):
        _row(f"(A) {lab} per-letter no-context", reps[(cond, "a")])
        _row(f"(A) {lab} per-letter +lexicon", reps[(cond, "b")])
        _row(f"(B) {lab} HOLISTIC rich (covered)", reps[(cond, "hol_rich")])
        _row(f"(B) {lab} holistic ENVELOPE (covered, ablation)", reps[(cond, "hol_env")])
        _row(f"(C) {lab} DUAL-ROUTE (full query set)", reps[(cond, "dual_full")])
        print()

    print(f"  citation: run 70's OWN 220-word sample -- within {RUN70_WITHIN_WORD:.1f}% / "
          f"cross {RUN70_CROSS_WORD:.1f}% (per-letter+lexicon; see "
          f"tests/test_run74_migrated.py for the bit-for-bit reproduction check).")

    verdicts = {}
    for cond in ("within", "cross"):
        rep_a, rep_hol = reps[(cond, "b")], reps[(cond, "hol_rich")]
        mc = _mcnemar(rep_a["flags"], rep_hol["flags"]) if rep_a["n"] == rep_hol["n"] else None
        ci_sep_above_a = rep_hol["word_ci"][0] > rep_a["word_acc"]
        hol_beats_letter = (100 * rep_hol["word_acc"] > 100 * rep_a["word_acc"]) and ci_sep_above_a
        print(f"  {cond.upper()}: holistic(rich, covered) {100*rep_hol['word_acc']:.1f}% "
              f"[{100*rep_hol['word_ci'][0]:.1f},{100*rep_hol['word_ci'][1]:.1f}] vs per-letter+lex "
              f"(SAME covered subset, n={rep_a['n']}) {100*rep_a['word_acc']:.1f}%  "
              f"CI-separated above? {ci_sep_above_a}")
        verdicts[cond] = {"rep_letter": rep_a, "rep_hol_rich": rep_hol, "hol_beats_letter": hol_beats_letter}

    # -- rich vs envelope, same covered subset (does pose-normalization matter for the headline). --
    for cond in ("within", "cross"):
        rr, re_ = reps[(cond, "hol_rich")], reps[(cond, "hol_env")]
        print(f"  {cond.upper()}: holistic RICH {100*rr['word_acc']:.1f}% vs ENVELOPE (ablation) "
              f"{100*re_['word_acc']:.1f}%  (same covered query/template pool)")

    # -- ANAGRAM. --
    print(f"\n  === REAL-CORPUS ANAGRAM CONTROL (does the gesture beat the envelope) ===")
    rd = _require("read.json")
    anagram = rd.get("anagram") or []
    n_anag = len(anagram)
    if n_anag:
        k_rich = sum(1 for r in anagram if r["correct_rich"])
        k_env = sum(1 for r in anagram if r["correct_env"])
        m_rich = float(np.mean([r["d_partner_rich"] - r["d_true_rich"] for r in anagram]))
        m_env = float(np.mean([r["d_partner_env"] - r["d_true_env"] for r in anagram]))
        ci_rich = _wilson(k_rich, n_anag)
        ci_env = _wilson(k_env, n_anag)
        print(f"  n anagram-queryable instances = {n_anag}  (pairs: {prep['anagram_pairs']})")
        print(f"  RICH:     discrimination rate = {100*k_rich/n_anag:.1f}% "
              f"[{100*ci_rich[0]:.1f},{100*ci_rich[1]:.1f}]  mean margin (partner-true) = {m_rich:+.4f}")
        print(f"  ENVELOPE: discrimination rate = {100*k_env/n_anag:.1f}% "
              f"[{100*ci_env[0]:.1f},{100*ci_env[1]:.1f}]  mean margin (partner-true) = {m_env:+.4f}")
        print(f"  run 66's own coarse-envelope shuffled-letter margin (context, NOT unit-comparable "
              f"-- different normalization scale): {RUN66_SHUFFLE_MARGIN:+.4f}")
        per_pair = defaultdict(lambda: [0, 0])
        for r in anagram:
            per_pair[(r["word"], r["partner"])][0] += int(r["correct_rich"])
            per_pair[(r["word"], r["partner"])][1] += 1
        for (wd_, pt_), (k_, tot_) in sorted(per_pair.items()):
            print(f"    {wd_:<8}vs {pt_:<8} rich correct {k_}/{tot_}")
        anagram_win = (100 * k_rich / n_anag >= BAR_ANAGRAM_RATE) and (k_rich > k_env or ci_rich[0] > ci_env[1])
    else:
        anagram_win = False
        print(f"  NO anagram-queryable instances found -- cannot evaluate the anagram control.")

    synth = rd.get("synthetic") or {}
    print(f"\n  SYNTHETIC anagram demo (deterministic geometry, no corpus dependency):")
    print(f"    RICH:     d(same-order)={synth.get('d_same', float('nan')):.4f} < "
          f"d(reordered)={synth.get('d_reordered', float('nan')):.4f}  "
          f"-> separates: {synth.get('rich_separates')}")
    print(f"    ENVELOPE: d(same-order)={synth.get('env_d_same', float('nan')):.4f} == "
          f"d(reordered)={synth.get('env_d_reordered', float('nan')):.4f}  "
          f"-> separates: {synth.get('env_separates')}")

    win_within = verdicts["within"]["hol_beats_letter"]
    win = win_within and anagram_win
    print(f"\n  MILESTONE (pre-registered: WITHIN-writer holistic word acc CI-separated above run "
          f"70's {BAR_WITHIN_HOLISTIC:.1f}% AND real-corpus anagram rate >= {BAR_ANAGRAM_RATE:.0f}% "
          f"AND beating envelope):")
    print(f"    holistic beats per-letter (WITHIN, covered subset): {win_within}")
    print(f"    anagram control passes: {anagram_win}")
    print(f"    VERDICT: {'WIN -- whole-word holistic reading beats the per-letter route on the sight vocabulary' if win else 'NULL -- see localization above (within/cross split, rich-vs-envelope, anagram rate)'}")

    print(f"\n  ANOMALIES / HONEST RESIDUALS:")
    print(f"    given segmentation for the per-letter arm; the holistic arm needs NO segmentation "
          f"at all (word-level ink only) -- an architectural difference in what each arm assumes.")
    print(f"    evaluation sample is ENRICHED (within pool taken in full, cross topped up) -- NOT a "
          f"random draw from the held-out population; coverage % reported separately (above) is the "
          f"honest organic number.")
    print(f"    anagram frame lookup does not exclude the query's own sample from its writer's "
          f"aggregate x_height/slant (unlike the main pipeline's own_frame) -- a small, accepted "
          f"leak for this targeted diagnostic (see docstring); negligible given each frame pools "
          f"dozens of glyphs.")
    print(f"    rich vs run-66 envelope margins are NOT unit-comparable across runs (different "
          f"normalization scale: x-height-relative here vs arclength-normalized-to-1 in run 66) -- "
          f"the honest within-run RICH-vs-ENVELOPE comparison (above, same query/template pool) is "
          f"the one this run's verdict rests on.")
    print(f"    degenerate own-frame writers: {prep['n_degenerate_own_frame']}/{len(prep['test_writers'])}"
          f"  word-char local-frame fallback: {prep['n_word_frame_fallback']}")
    print(f"    word length dist: {sorted(prep['word_len_dist'].items())}")

    reps_serialized = {f"{c}|{a}": {k: v for k, v in r.items() if k != "flags"}
                       for (c, a), r in reps.items()}
    _save({"reps": reps_serialized, "verdicts": verdicts, "anagram_win": anagram_win, "win": win,
          "n_anagram": n_anag}, _ckpt("summary.json"))
    _seed_guard("summary", md5_now)
    print(f"\n  saved -> {_ckpt('summary.json')}")
    print(f"\n{SEP}\n  RUN 74 COMPLETE -- see final agent report.\n{SEP}", flush=True)
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True, choices=["prep", "read", "decode", "summary"])
    args = p.parse_args()
    return {"prep": stage_prep, "read": stage_read, "decode": stage_decode,
            "summary": stage_summary}[args.stage]()


if __name__ == "__main__":
    sys.exit(main())
