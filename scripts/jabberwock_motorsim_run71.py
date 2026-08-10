"""jabberwock_motorsim_run71.py -- RUN 71: INCREMENTAL MOTOR-SIMULATION AbS
(CURSIVE_PLAN.md step 3, the 55->93 lever).

THE HYPOTHESIS (BAP's own mechanism, Gilet/Diard/Bessiere 2011): BAP reaches 93.36% within-writer
by MOTOR SIMULATION -- "perceiving a letter would entail a motor simulation of movements associated
with the writing of that letter" (analysis-by-synthesis, C3/C4). Run 69's STATIC writer-relative
pose recognizer (nearest-exemplar DTW match against a bank of REAL ink) reached 55.0% within-writer
isolated char / run 70's 58.0% word-context char -- decent but far below BAP's 93%. This run tests
whether replacing the STATIC bank-match emission with a GENERATE-AND-COMPARE (AbS) emission --
render each candidate letter via run 66's learned writer (StrokeQuantize -> StrokeRender, the exact
inverse proven faithful on real cursive), placed into the SAME writer-relative frame run 69 built,
then DTW-compared to the observed ink -- lifts within-writer char accuracy toward BAP's 93%, and
whether GENERATING WITH COARTICULATION (run 66's learned join model, applied to the true left/right
neighbors) closes run 70's word-context gap (49.5% word-context vs 55.0% isolated char).

REUSE (nothing new-from-scratch):
  * run 69 (`r69`, results/run69_checkpoints/prep.json + read.json, READ-ONLY) -- the writer frame
    (`aggregate_scale_slant`, `local_baseline_topline`), the STATIC bank/DTW machinery
    (`_class_cost`, `select_bank`, `glyphs_by_sample`, `_group_by_writer`, `_index_by_writer_sample`,
    `invariant_canon`, `pose_canon`), and its ALREADY-COMPUTED isolated-char query canons +
    STATIC arm distances (invA/invB/poseC/poseE) -- arm A (static) is loaded verbatim, no
    recomputation.
  * run 70 (`r70`, results/run70_checkpoints/prep.json + read.json, READ-ONLY) -- the word-context
    query canons + STATIC combined within/cross distances (already-summed inv+lambda*pose 26-vectors
    per char), and the lexicon-collapse decoders (via r61, reused through r70's own `decode_arm_a`/
    `decode_arm_b`/`_pad62` machinery).
  * run 66 (`cc66`, results/run66_checkpoints/letters.json + joins.json, READ-ONLY) -- the CROSS
    (population-trained) letter-form codebook (`learn_letter_form`/`render_form_canonical`'s
    output: StrokeQuantize signature + StrokeRender canonical polyline + natural theta/arclen) and
    the learned JOIN model (`generate_word`, `extract_join`'s global gap) -- THE FORWARD MODEL.
  * run 61 (`r61`) -- lexicon + decoders (`decode_no_context`, `decode_lexicon`, `_lex_by_len`,
    `_wilson_ci`, `_mcnemar`), reused via r70's `_pad62`/`decode_arm_a`/`decode_arm_b`.

THE MOTOR-SIM EMISSION (the new piece -- "generate, then place in the writer's frame, then
compare"): a candidate letter's LEARNED FORM (`{signature, theta, arclen, canon}`, run 66's own
schema) already carries `canon` = the StrokeRender output, re-normalized to StrokeQuantize's own
invariant frame (start at origin, initial heading rotated to 0, arclen 1) -- exactly run 66/69's
`invariant()` channel, reused verbatim as `gen_inv_from_form`. The NEW `gen_pose_from_form` does to
a GENERATED form what run 69's `pose_canon` does to RAW ink: undo the invariant rotation (recover
the form's NATURAL absolute heading via `theta`, exactly `_place_letter`'s own rotation step), scale
into X-HEIGHT UNITS (so the output lands in the SAME normalized coordinate space `pose_canon`
produces for real ink), then shear by the writer's slant (same shear `deslant_points` uses). The
X-HEIGHT scale is a per-class constant `class_scale[c] = median(exemplar_arclen / exemplar_local_
x_height)` over BACKGROUND single-stroke exemplars (closed-form, donkey=0) for the CROSS condition
(population-typical proportions, writer-agnostic by construction -- the derivation shows the
writer's own x-height cancels out of the formula); for WITHIN, the SPECIFIC writer-owned exemplar's
own measured `arclen` divided by THAT writer's own frame x-height is used directly (no population
constant needed -- the writer's own instance already carries real scale). See `gen_pose_from_form`'s
docstring for the full derivation.

THE THREE ARMS (within-writer AND cross-writer, isolated AND word-context):
  (A) STATIC        -- run 69/70's own bank-of-real-exemplars DTW match, LOADED VERBATIM (no new
                        compute). invariant + writer-relative-pose, PRIMARY_LAMBDA=1.0 (r69's own,
                        not re-tuned).
  (B) MOTOR-SIM      -- GENERATE each candidate via run 66's forward model (CROSS: run 66's
                        population codebook; WITHIN: a per-test-writer codebook LEARNED here from
                        that writer's OWN single-stroke exemplars via `cc66.learn_letter_form`,
                        the exact same quantize/render call run 66 uses to teach a letter),
                        PLACED in the SAME writer-relative frame as (A), compared via the SAME
                        `_class_cost`/DTW machinery (drop-in bank swap: real exemplars -> generated
                        templates).
  (C) MOTOR-SIM + COARTICULATION (word-context only, WITHIN-writer) -- generate a LOCAL WINDOW
                        (true-left-neighbor + candidate + true-right-neighbor, at word/line
                        boundaries whichever neighbors exist) via `cc66.generate_word(...,
                        joins=True)` with run 66's LEARNED join gap, `cc66.wordnorm`-normalized, and
                        DTW-compared to the OBSERVED local window (the true neighbors' + candidate's
                        OWN raw ink concatenated the same way run 66's `word_points` does) -- one
                        scalar AbS score per candidate, no separate inv/pose split (this arm tests
                        whether MODELING the neighbor's join changes which candidate best explains a
                        wider observed span, directly targeting run 70's coarticulation finding that
                        word-context chars (49.5%) score below isolated chars (55.0%) despite the
                        SAME per-char posterior).

GIVEN char (+word) segmentation throughout (run 69/70's own convention) -- isolates the emission-
model question from segmentation.

WITHIN-writer TEST-SAMPLE EXCLUSION (this run's own, STRICTER than reusing r69/r70's separately):
since a writer can appear in BOTH r69's isolated test set and r70's word test set, this run
regenerates BOTH test sets itself (byte-identically -- verified against r69/r70's saved output,
see `tests/test_run71_migrated.py`) so it can exclude the UNION of every sample used by either test
set for a writer before drawing that writer's OWN single-stroke exemplars to LEARN its motor-sim
codebook (`build_prep`'s `exclude_samples`). This run's own `WITHIN_GEN_SELECT_SEED` (decoupled
from r69/r70's own bank seeds) draws the M_BANK=3 exemplars/class used to learn each writer's forms.

PRE-REGISTERED READ (stated before any number is computed):
  WIN if motor-sim (B or C) materially lifts within-writer char accuracy above the static 55-58%
  toward BAP's 93% -- bar: within-writer char > BAR_WITHIN_CHAR (65%), CI-separated above (A) --
  AND within-writer WORD reading (lexicon collapse on the best emission) rises above run 70's 30.5%
  (CI-separated).
  Report isolated vs word-context separately; report whether coarticulation-aware generation (C)
  closes run 70's 49.5->55.0 word-context gap.
  NULL if motor-sim does not beat static -> the static pose recognizer is this featureset's
  ceiling; localize (generator fidelity via round-trip DTW on the SAME writers; given-seg;
  cost/pruning simplifications named honestly).

DISCIPLINE: donkey=0 (writer = our own StrokeQuantize/StrokeRender/DtwTo, closed-form placement
geometry -- median/percentile/shear/rotation, NOT an SGD-trained net). NO git add/commit. SEED
GUARD: OZMA_SEED_PERSIST_DISABLED=1, md5(seeds/stroke_shapes.json) asserted UNCHANGED before/after
every stage. run6{1,6,8,9}_checkpoints and run70_checkpoints are READ-ONLY (opened, never written).

Stages: prep (numpy only) -> genforms (native: learn each test writer's own motor-sim codebook,
checkpointed per writer) -> read_iso (native: arms A[reused]/B on isolated test chars, checkpointed)
-> read_word (native: arms A[reused]/B/C on word-context chars, checkpointed) -> decode (lexicon
collapse on the best emission) -> summary.

Run:
  OZMA_SEED_PERSIST_DISABLED=1 DEEPWRITING_DIR=/tmp/handwriting PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python3 scripts/jabberwock_motorsim_run71.py \\
    --stage <prep|genforms|read_iso|read_word|decode|summary>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
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

SEP = "=" * 92
STROKE_SHAPES_SEED = r69.STROKE_SHAPES_SEED
CKPT_DIR = os.path.join(ROOT, "results", "run71_checkpoints")
LOG = os.path.join(ROOT, "results", "omniglot_gate_run71.log")
os.makedirs(CKPT_DIR, exist_ok=True)

RUN66_CKPT = os.path.join(ROOT, "results", "run66_checkpoints")          # READ-ONLY.
RUN66_LETTERS = os.path.join(RUN66_CKPT, "letters.json")
RUN66_JOINS = os.path.join(RUN66_CKPT, "joins.json")
RUN69_PREP = r70.RUN69_PREP                                               # READ-ONLY.
RUN69_READ = os.path.join(ROOT, "results", "run69_checkpoints", "read.json")
RUN70_PREP = os.path.join(ROOT, "results", "run70_checkpoints", "prep.json")  # READ-ONLY.
RUN70_READ = os.path.join(ROOT, "results", "run70_checkpoints", "read.json")
RUN61_LEXICON = r70.RUN61_LEXICON

LOWER_CLASSES = r69.LOWER_CLASSES
CANON_N = cc66.CANON_N
LETTERS26 = [chr(ord("a") + i) for i in range(26)]

# ------------------------------------------------------------------------------------------- #
#  PRE-REGISTERED CONSTANTS -- reused verbatim from runs 61/66/69/70 where a shared constant
#  exists; new constants marked NEW.
# ------------------------------------------------------------------------------------------- #
SPLIT = r69.SPLIT
WRITER_SPLIT_SEED = r69.WRITER_SPLIT_SEED
N_BACKGROUND_FRAC = r69.N_BACKGROUND_FRAC
M_BANK = r69.M_BANK                                    # 3 -- same bank size as r69/r70's own.
PRIMARY_LAMBDA = r69.PRIMARY_LAMBDA                    # 1.0, r69's pre-registered pose weight.

WITHIN_GEN_SELECT_SEED = 20260810                      # NEW: this run's OWN bank-exemplar draw,
                                                        # decoupled from r69/r70's own bank seeds.
DEFAULT_CLASS_SCALE = 2.0                              # NEW: fallback arclen/x_height ratio for a
                                                        # class with no background observations.
PER_CALL_BUDGET_SECONDS = 460.0

BAP_WITHIN = r69.BAP_WITHIN
BAP_CROSS = r69.BAP_CROSS
RUN69_WITHIN_ISO_CHAR = 55.0        # run 69's own reported number (condition E).
RUN69_CROSS_ISO_CHAR = 28.8         # run 69's own reported number (condition C).
RUN70_WITHIN_WORD_CHAR = 58.0       # run 70's own reported number (arm a, within, word-context).
RUN70_CROSS_WORD_CHAR = 23.6        # run 70's own reported number (arm a, cross, word-context).
RUN70_WITHIN_WORD_ACC = 30.5        # run 70's own reported WORD accuracy (arm b, within, lexicon).
BAR_WITHIN_CHAR = 65.0              # pre-registered WIN bar (task spec: "state a bar, e.g. >65%").
BAR_WITHIN_WORD = RUN70_WITHIN_WORD_ACC   # WIN bar: must rise above run 70's number, CI-separated.


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
#  THE MOTOR-SIM EMISSION -- generate a candidate letter's canon (from a LEARNED form) into the
#  SAME writer-relative pose space r69's `pose_canon` builds from raw ink. Pure numpy, donkey=0.
# ============================================================================================= #
def gen_inv_from_form(form: dict) -> list:
    """The invariant channel of a GENERATED form -- `form["canon"]` IS ALREADY StrokeQuantize's
    own invariant frame (start at origin, initial heading rotated to 0, arclen 1) -- run 66's own
    channel (`cc66._char_cost_vector`), reused verbatim, no new geometry."""
    return form["canon"]


def gen_pose_from_form(form: dict, k_scale: float, slant_deg: float) -> list:
    """The WRITER-RELATIVE pose channel of a GENERATED form -- what `pose_canon` does to RAW ink,
    applied to a RENDERED template instead.

    DERIVATION (dimensional, closed-form): `form["canon"]` has arclen=1 and initial heading
    rotated to 0 (StrokeQuantize's canonical_pose convention). Undo the heading rotation via
    `form["theta"]` (exactly `_place_letter`'s own rotation step) to recover the letter's NATURAL
    absolute orientation, still at arclen=1. To land in the SAME normalized space `pose_canon`
    produces (real-ink coordinates divided by the writer's x-height), the arclen-1 shape must be
    scaled by (true_arclen / x_height) = `k_scale`:
      * CROSS (population): true_arclen ~= class_scale[c] * x_height (a per-class constant
        estimated from many background exemplars, see `compute_class_scale`) => k_scale =
        class_scale[c] -- the target writer's x_height CANCELS OUT of the ratio, so this is
        writer-agnostic by construction (the population's typical letter proportions).
      * WITHIN (a specific writer-owned exemplar): true_arclen = the exemplar's OWN measured
        `form["arclen"]`, x_height = THAT writer's own frame x-height => k_scale =
        `form["arclen"] / writer_x_height` (computed by the caller, passed in directly).
    Then shear by the writer's slant exactly as `deslant_points` does (baseline=0 here, since the
    generated shape's start point sits at the origin after rotation -- rotation fixes the origin,
    so no separate baseline/x0 subtraction is needed, unlike `pose_canon`'s raw-ink path)."""
    canon = np.asarray(form["canon"], float)
    th = float(form["theta"])
    c, s = math.cos(th), math.sin(th)
    R = np.array([[c, -s], [s, c]])
    nat = canon @ R.T                              # natural absolute orientation, arclen=1.
    scaled = nat * float(k_scale)                  # now in x-height units.
    t = math.tan(math.radians(slant_deg))
    x2 = scaled[:, 0] + t * scaled[:, 1]            # shear (pose_canon's deslant, baseline=0).
    return np.stack([x2, scaled[:, 1]], axis=1).tolist()


def build_cross_gen_bank(codebook: dict, class_scale: dict, pop_slant_deg: float) -> dict:
    """{class_str: [{"inv":..., "pose":...}, ...]} from run 66's POPULATION-trained codebook (ALL
    K_ALLO allographs), placed via the population frame's slant + this class's population scale --
    the motor-sim analogue of run 69's condition C (pop frame, cross bank)."""
    bank = {}
    for c in LOWER_CLASSES:
        forms = codebook.get(str(c), [])
        k = class_scale.get(str(c), DEFAULT_CLASS_SCALE)
        bank[str(c)] = [{"inv": gen_inv_from_form(f), "pose": gen_pose_from_form(f, k, pop_slant_deg)}
                         for f in forms]
    return bank


def build_within_gen_bank(writer_forms: dict, writer_frame: dict) -> dict:
    """{class_str: [...]} from a per-writer LEARNED codebook (up to M_BANK forms/class, learned
    from that writer's OWN single-stroke exemplars), placed via that writer's OWN frame -- the
    motor-sim analogue of run 69's condition E (own frame, own bank)."""
    xh = float(writer_frame.get("x_height") or 1.0) or 1.0
    slant = float(writer_frame.get("slant_deg") or 0.0)
    bank = {}
    for c in LOWER_CLASSES:
        forms = writer_forms.get(str(c), [])
        recs = []
        for f in forms:
            k = float(f["arclen"]) / xh
            recs.append({"inv": gen_inv_from_form(f), "pose": gen_pose_from_form(f, k, slant)})
        bank[str(c)] = recs
    return bank


def compute_class_scale(all_glyphs: list, bg_writers: set, ws_index: dict) -> tuple:
    """class_scale[c] = median(exemplar_arclen / exemplar_local_x_height) over BACKGROUND
    single-stroke lowercase exemplars of class c -- closed-form (median reduction), donkey=0.
    Returns (class_scale: {class:int -> float}, n_obs: {class:int -> int})."""
    ratios = defaultdict(list)
    for g in all_glyphs:
        if g["writer"] not in bg_writers or g["class"] not in LOWER_CLASSES:
            continue
        strokes = g["strokes"]
        if len(strokes) != 1 or len(strokes[0]) < 6:
            continue
        pts = np.asarray(strokes[0], float)
        arclen = cc66._arclen(pts)
        gl = ws_index.get((g["writer"], g["sample"]))
        if not gl:
            continue
        try:
            idx = next(i for i, x in enumerate(gl) if x["char_idx"] == g["char_idx"])
        except StopIteration:
            continue
        baseline, topline = r69.local_baseline_topline(gl, idx)
        xh = baseline - topline
        if xh > 1e-6 and arclen > 1e-6:
            ratios[g["class"]].append(arclen / xh)
    scale = {c: (float(np.median(ratios[c])) if ratios.get(c) else DEFAULT_CLASS_SCALE)
             for c in LOWER_CLASSES}
    n_obs = {c: len(ratios.get(c, [])) for c in LOWER_CLASSES}
    return scale, n_obs


# ============================================================================================= #
#  STAGE: prep -- regenerate r69/r70's OWN test sets (byte-identical, verified), the UNIONED
#  exclusion set, per-writer frames, own-writer single-stroke exemplar pools, class_scale. Pure
#  numpy, no native calls.
# ============================================================================================= #
def build_prep() -> dict:
    dw = dww.load_deepwriting(SPLIT)
    all_glyphs = dww.extract_char_glyphs(dw)
    by_writer = r69._group_by_writer(all_glyphs)
    ws_index = r69._index_by_writer_sample(all_glyphs)

    words_for_split = dww.extract_words(dw, min_len=3, max_len=8, lowercase_only=True,
                                        complete_only=True)
    bg_words, ho_words = dww.writer_split(words_for_split, n_background_frac=N_BACKGROUND_FRAC,
                                          seed=WRITER_SPLIT_SEED)
    bg_writers = {w["writer"] for w in bg_words}
    ho_writers = {w["writer"] for w in ho_words}
    assert bg_writers.isdisjoint(ho_writers), "writer split must be disjoint"

    run69_prep = _load(RUN69_PREP)
    run70_prep = _load(RUN70_PREP)
    bg_match_69 = (set(run69_prep["bg_writers"]) == bg_writers)
    bg_match_70 = (set(run70_prep["bg_writers"]) == bg_writers)

    # -- regenerate r69's isolated test-char selection (byte-identical: writer ids are ints, so
    #    set iteration is hash-stable across processes; verified in tests/ and cross-checked here).
    test_chars = r69.select_test_chars(by_writer, ho_writers, r69.N_TEST_TARGET, r69.TEST_SELECT_SEED)
    iso_match = (len(test_chars) == len(run69_prep["queries"]) and
                 all(g["writer"] == q["writer"] and g["class"] == q["true_class"]
                     for g, q in zip(test_chars, run69_prep["queries"])))

    # -- regenerate r70's word test selection (byte-identical, same check). --
    lexicon = _load(RUN61_LEXICON)
    lexicon_set = set(lexicon["lexicon"])
    test_word_pool = [w for w in ho_words if w["word"] in lexicon_set]
    test_words = r70.select_test_words(test_word_pool, r70.N_TEST_WORDS_TARGET,
                                       r70.TEST_WORD_SELECT_SEED)
    word_match = (len(test_words) == len(run70_prep["word_records"]) and
                  all(w["writer"] == rec["writer"] and w["word"] == rec["word"]
                      for w, rec in zip(test_words, run70_prep["word_records"])))

    # -- UNIONED exclusion set: every sample used by EITHER test set, per writer (stricter than
    #    r69/r70's own separate exclusions -- this run's own within-writer generator must not leak
    #    on either evaluation). --
    exclude_samples = defaultdict(set)
    for g in test_chars:
        exclude_samples[g["writer"]].add(g["sample"])
    for wd in test_words:
        exclude_samples[wd["writer"]].add(wd["sample"])

    iso_writers = sorted({g["writer"] for g in test_chars})
    word_writers = sorted({wd["writer"] for wd in test_words})
    test_writers = sorted(set(iso_writers) | set(word_writers))

    # -- per-writer frame, THIS run's own recompute (own exclusion set). --
    writer_frames = {}
    for w in test_writers:
        gbs = r69.glyphs_by_sample(by_writer.get(w, []), exclude_samples=exclude_samples[w])
        writer_frames[str(w)] = r69.aggregate_scale_slant(gbs)

    # -- own RAW single-stroke exemplars per (writer, class) -- the training pool for THIS
    #    writer's motor-sim codebook (`stage_genforms`). --
    own_raw_bank = {}
    own_raw_coverage = {}
    for w in test_writers:
        pool = [g for g in by_writer.get(w, [])
                if g["sample"] not in exclude_samples[w] and g["class"] in LOWER_CLASSES
                and len(g["strokes"]) == 1 and len(g["strokes"][0]) >= 6]
        raw = r69.select_bank(pool, LOWER_CLASSES, M_BANK,
                              np.random.default_rng(WITHIN_GEN_SELECT_SEED + w))
        own_raw_bank[str(w)] = {str(c): [np.asarray(g["strokes"][0], float)[:, :2].tolist()
                                          for g in insts]
                                 for c, insts in raw.items()}
        own_raw_coverage[str(w)] = {str(c): len(v) for c, v in raw.items()}

    class_scale, class_scale_n = compute_class_scale(all_glyphs, bg_writers, ws_index)

    # -- word records WITH raw strokes (needed for arm C's local-window coarticulation compare). --
    word_records = []
    for wi, wd in enumerate(test_words):
        chars = [{"true_symbol": cs["symbol"],
                  "strokes": [np.asarray(s, float)[:, :2].tolist() for s in cs["strokes"]]}
                 for cs in wd["char_segs"]]
        word_records.append({"wid": wi, "writer": wd["writer"], "word": wd["word"], "chars": chars})

    return {
        "bg_writers": sorted(bg_writers), "ho_writers": sorted(ho_writers),
        "bg_match_run69": bg_match_69, "bg_match_run70": bg_match_70,
        "iso_test_match_run69": iso_match, "word_test_match_run70": word_match,
        "n_iso_test_chars": len(test_chars), "n_word_test_words": len(test_words),
        "iso_writers": iso_writers, "word_writers": word_writers, "test_writers": test_writers,
        "writer_frames": writer_frames,
        "own_raw_bank": own_raw_bank, "own_raw_coverage": own_raw_coverage,
        "class_scale": {str(c): class_scale[c] for c in LOWER_CLASSES},
        "class_scale_n": {str(c): class_scale_n[c] for c in LOWER_CLASSES},
        "word_records": word_records,
    }


def stage_prep():
    print(f"\n{SEP}\n  STAGE: prep (regenerate r69/r70 test sets + unioned exclusion + writer "
          f"frames + own-exemplar pools + class_scale -- pure numpy, no native)\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("prep")
    print(f"  seeds/stroke_shapes.json md5 (before): {md5_before}", flush=True)

    out = build_prep()
    out["stroke_shapes_md5"] = md5_before
    _save(out, _ckpt("prep.json"))
    _seed_guard("prep", md5_before)

    print(f"  bg_writers match r69/r70: {out['bg_match_run69']}/{out['bg_match_run70']}", flush=True)
    print(f"  iso test-char reproduction matches r69: {out['iso_test_match_run69']} "
          f"(n={out['n_iso_test_chars']})", flush=True)
    print(f"  word test-word reproduction matches r70: {out['word_test_match_run70']} "
          f"(n={out['n_word_test_words']})", flush=True)
    print(f"  test writers (union): {len(out['test_writers'])}  "
          f"(iso-only: {len(set(out['iso_writers'])-set(out['word_writers']))}, "
          f"word-only: {len(set(out['word_writers'])-set(out['iso_writers']))}, "
          f"both: {len(set(out['iso_writers'])&set(out['word_writers']))})", flush=True)
    empty_cells = sum(1 for cov in out["own_raw_coverage"].values()
                      for c, n in cov.items() if n == 0)
    print(f"  own-exemplar-pool empty (writer,class) cells: {empty_cells} / "
          f"{len(out['test_writers']) * len(LOWER_CLASSES)}", flush=True)
    cs = out["class_scale"]
    csn = out["class_scale_n"]
    print(f"  class_scale (arclen/x_height): median={np.median(list(cs.values())):.3f}  "
          f"n_obs range=[{min(csn.values())},{max(csn.values())}]", flush=True)
    print(f"  saved -> {_ckpt('prep.json')}  [prep {time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: genforms -- LEARN each test writer's own motor-sim codebook (native StrokeQuantize +
#  StrokeRender via cc66.learn_letter_form). Checkpointed per writer, resumable.
# ============================================================================================= #
def stage_genforms():
    print(f"\n{SEP}\n  STAGE: genforms (learn each test writer's OWN motor-sim codebook -- native "
          f"StrokeQuantize/StrokeRender)\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("genforms")
    import substrate_rs as srs
    native = srs.Substrate()._inner
    prep = _require("prep.json")
    own_raw_bank = prep["own_raw_bank"]

    out_path = _ckpt("genforms.json")
    state = _load(out_path) if os.path.exists(out_path) else {"writer_forms": {}, "done": False}
    if state.get("done"):
        print(f"  genforms already COMPLETE (n={len(state['writer_forms'])} writers).", flush=True)
        return 0
    remaining = [w for w in prep["test_writers"] if str(w) not in state["writer_forms"]]
    deadline = time.time() + PER_CALL_BUDGET_SECONDS
    n_new = 0
    n_forms_total = 0

    for w in remaining:
        wf = {}
        for c in LOWER_CLASSES:
            insts = own_raw_bank.get(str(w), {}).get(str(c), [])
            forms = [cc66.learn_letter_form(native, pts) for pts in insts]
            wf[str(c)] = forms
            n_forms_total += len(forms)
        state["writer_forms"][str(w)] = wf
        n_new += 1
        if n_new % 15 == 0:
            _save(state, out_path)
            _seed_guard("genforms", md5_before)
            print(f"    ... {len(state['writer_forms'])}/{len(prep['test_writers'])} writers  "
                  f"[{time.time()-t0:.1f}s]", flush=True)
            if time.time() > deadline:
                _save(state, out_path)
                _seed_guard("genforms", md5_before)
                print(f"  WALL-BUDGET: {len(state['writer_forms'])}/{len(prep['test_writers'])} "
                      f"done -- re-invoke --stage genforms to resume.", flush=True)
                return 2

    state["done"] = True
    _save(state, out_path)
    _seed_guard("genforms", md5_before)
    print(f"  learned {len(state['writer_forms'])} writer codebooks ({n_forms_total} forms total)"
          f"  [{time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: read_iso -- arms A (reused verbatim from r69) / B (motor-sim) on ISOLATED test chars.
# ============================================================================================= #
def stage_read_iso():
    print(f"\n{SEP}\n  STAGE: read_iso -- arm A[reused] / arm B[motor-sim] on ISOLATED test chars\n"
          f"{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("read_iso")
    import substrate_rs as srs
    native = srs.Substrate()._inner
    prep = _require("prep.json")
    genforms = _require("genforms.json")
    if not genforms.get("done"):
        raise SystemExit("WALL: genforms not COMPLETE -- re-invoke --stage genforms.")
    writer_forms = genforms["writer_forms"]
    writer_frames = prep["writer_frames"]
    class_scale = prep["class_scale"]

    r69_prep = _load(RUN69_PREP)
    r69_read = _load(RUN69_READ)
    if not r69_read.get("done"):
        raise SystemExit("WALL: run 69's read.json is not COMPLETE -- run 69 must be finished.")
    codebook = _load(RUN66_LETTERS)["codebook"]
    pop_slant = r69_prep["population_frame"]["slant_deg"]
    cross_gen_bank = build_cross_gen_bank(codebook, class_scale, pop_slant)

    static_by_qid = {r["qid"]: r for r in r69_read["records"]}
    queries = r69_prep["queries"]

    out_path = _ckpt("read_iso.json")
    state = _load(out_path) if os.path.exists(out_path) else {"records": [], "done": False}
    if state.get("done"):
        print(f"  read_iso already COMPLETE (n={len(state['records'])}).", flush=True)
        return 0
    done = {r["qid"] for r in state["records"]}
    deadline = time.time() + PER_CALL_BUDGET_SECONDS
    n_new = 0
    within_bank_cache = {}

    for q in queries:
        if q["qid"] in done:
            continue
        w = str(q["writer"])
        if w not in within_bank_cache:
            within_bank_cache[w] = build_within_gen_bank(
                writer_forms.get(w, {}), writer_frames.get(w, {"x_height": 1.0, "slant_deg": 0.0}))
        within_bank = within_bank_cache[w]
        genB_inv = r69._class_cost(native, q["inv"], within_bank, "inv")
        genB_pose = r69._class_cost(native, q["pose_own"], within_bank, "pose")
        genC_inv = r69._class_cost(native, q["inv"], cross_gen_bank, "inv")
        genC_pose = r69._class_cost(native, q["pose_pop"], cross_gen_bank, "pose")
        sr = static_by_qid[q["qid"]]
        state["records"].append({
            "qid": q["qid"], "writer": q["writer"], "true_class": q["true_class"],
            "symbol": q["symbol"],
            "static_invB": sr["invB"], "static_poseE": sr["poseE"],     # arm A within (r69's E).
            "static_invA": sr["invA"], "static_poseC": sr["poseC"],     # arm A cross (r69's C).
            "genB_inv": genB_inv, "genB_pose": genB_pose,               # arm B within.
            "genC_inv": genC_inv, "genC_pose": genC_pose,               # arm B cross.
        })
        n_new += 1
        if n_new % 20 == 0:
            _save(state, out_path)
            _seed_guard("read_iso", md5_before)
            n = len(state["records"])

            def _acc(inv_key, pose_key):
                ok = 0
                for r in state["records"]:
                    v = np.asarray(r[inv_key]) + PRIMARY_LAMBDA * np.asarray(r[pose_key])
                    ok += int((int(np.argmin(v)) + 10) == r["true_class"])
                return 100.0 * ok / n

            print(f"    ... {n}/{len(queries)}  static_within={_acc('static_invB','static_poseE'):.1f}%"
                  f"  genB_within={_acc('genB_inv','genB_pose'):.1f}%  "
                  f"genC_cross={_acc('genC_inv','genC_pose'):.1f}%  [{time.time()-t0:.1f}s]",
                  flush=True)
            if time.time() > deadline:
                _save(state, out_path)
                _seed_guard("read_iso", md5_before)
                print(f"  WALL-BUDGET: {len(state['records'])}/{len(queries)} done -- re-invoke "
                      f"--stage read_iso to resume.", flush=True)
                return 2

    state["done"] = True
    _save(state, out_path)
    _seed_guard("read_iso", md5_before)
    print(f"  read_iso {len(state['records'])} queries  [{time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: read_word -- arms A[reused]/B[motor-sim]/C[motor-sim+coarticulation, within-writer only]
#  on WORD-CONTEXT chars.
# ============================================================================================= #
def _observed_window(chars: list, i: int) -> list:
    """Concatenate raw strokes of chars[i-1..i+1] (whichever exist) -- run 66's `word_points`
    convention (ALL strokes of a char_seg, in order)."""
    lo, hi = max(0, i - 1), min(len(chars), i + 2)
    out = []
    for ch in chars[lo:hi]:
        for s in ch["strokes"]:
            out.append(np.asarray(s, float)[:, :2])
    if not out:
        return np.zeros((2, 2))
    return np.concatenate(out, axis=0)


def _form_for(cls: int, writer_forms: dict, codebook: dict):
    """First available WITHIN form for this writer/class, else the CROSS medoid (allograph 0)."""
    wf = writer_forms.get(str(cls), [])
    if wf:
        return wf[0]
    cf = codebook.get(str(cls), [])
    return cf[0] if cf else None


def coartic_scores(native, chars: list, i: int, writer_forms: dict, codebook: dict,
                    join_gap: np.ndarray) -> list:
    """26-length AbS score (lower=better): DTW(observed local window, GENERATED local window with
    the TRUE left/right neighbor forms + the learned join model, candidate class in the middle)."""
    lo, hi = max(0, i - 1), min(len(chars), i + 2)
    left_cls = dww.canon_class(chars[i - 1]["true_symbol"]) if i - 1 >= lo and i > 0 else None
    right_cls = dww.canon_class(chars[i + 1]["true_symbol"]) if i + 1 < hi else None
    left_form = _form_for(left_cls, writer_forms, codebook) if left_cls is not None else None
    right_form = _form_for(right_cls, writer_forms, codebook) if right_cls is not None else None
    observed = cc66.wordnorm(_observed_window(chars, i))
    vec = [1e6] * 26
    for c in LOWER_CLASSES:
        li = c - 10
        cand_form = _form_for(c, writer_forms, codebook)
        if cand_form is None:
            continue
        forms = [f for f in (left_form, cand_form, right_form) if f is not None]
        if not forms:
            continue
        gen = cc66.generate_word(native, forms, join_gap, joins=True)
        vec[li] = cc66.dtw(native, observed, cc66.wordnorm(gen))
    return vec


def stage_read_word():
    print(f"\n{SEP}\n  STAGE: read_word -- arm A[reused] / B[motor-sim] / C[+coarticulation, "
          f"within] on WORD-CONTEXT chars\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("read_word")
    import substrate_rs as srs
    native = srs.Substrate()._inner
    prep = _require("prep.json")
    genforms = _require("genforms.json")
    if not genforms.get("done"):
        raise SystemExit("WALL: genforms not COMPLETE -- re-invoke --stage genforms.")
    writer_forms_all = genforms["writer_forms"]
    writer_frames = prep["writer_frames"]
    class_scale = prep["class_scale"]

    r69_prep = _load(RUN69_PREP)
    r70_prep = _load(RUN70_PREP)
    r70_read = _load(RUN70_READ)
    if not r70_read.get("done"):
        raise SystemExit("WALL: run 70's read.json is not COMPLETE -- run 70 must be finished.")
    codebook = _load(RUN66_LETTERS)["codebook"]
    joins = _load(RUN66_JOINS)
    join_gap = np.asarray(joins["global"], float)
    pop_slant = r69_prep["population_frame"]["slant_deg"]
    cross_gen_bank = build_cross_gen_bank(codebook, class_scale, pop_slant)

    my_words = prep["word_records"]
    r70_words = r70_prep["word_records"]
    r70_static = {r["wid"]: r for r in r70_read["records"]}
    assert len(my_words) == len(r70_words), "word-record count mismatch vs run 70"
    for a, b in zip(my_words, r70_words):
        assert a["writer"] == b["writer"] and a["word"] == b["word"], \
            "word-record alignment mismatch vs run 70 -- selection did not reproduce byte-identically"

    out_path = _ckpt("read_word.json")
    state = _load(out_path) if os.path.exists(out_path) else {"records": [], "done": False}
    if state.get("done"):
        print(f"  read_word already COMPLETE (n={len(state['records'])}).", flush=True)
        return 0
    done = {r["wid"] for r in state["records"]}
    deadline = time.time() + PER_CALL_BUDGET_SECONDS
    n_new = 0
    within_bank_cache = {}

    for mywd, r70wd in zip(my_words, r70_words):
        wid = mywd["wid"]
        if wid in done:
            continue
        w = str(mywd["writer"])
        wf = writer_forms_all.get(w, {})
        if w not in within_bank_cache:
            within_bank_cache[w] = build_within_gen_bank(
                wf, writer_frames.get(w, {"x_height": 1.0, "slant_deg": 0.0}))
        within_bank = within_bank_cache[w]

        genB_within, genB_cross, coartic = [], [], []
        for i, ch in enumerate(r70wd["chars"]):
            genB_inv = r69._class_cost(native, ch["inv"], within_bank, "inv")
            genB_pose = r69._class_cost(native, ch["pose_own"], within_bank, "pose")
            genC_inv = r69._class_cost(native, ch["inv"], cross_gen_bank, "inv")
            genC_pose = r69._class_cost(native, ch["pose_pop"], cross_gen_bank, "pose")
            genB_within.append([genB_inv[c] + PRIMARY_LAMBDA * genB_pose[c] for c in range(26)])
            genB_cross.append([genC_inv[c] + PRIMARY_LAMBDA * genC_pose[c] for c in range(26)])
            coartic.append(coartic_scores(native, mywd["chars"], i, wf, codebook, join_gap))

        sr = r70_static[wid]
        state["records"].append({
            "wid": wid, "writer": mywd["writer"], "word": mywd["word"],
            "static_within": sr["within_dists"], "static_cross": sr["cross_dists"],
            "genB_within": genB_within, "genB_cross": genB_cross,
            "coartic_within": coartic,
        })
        n_new += 1
        if n_new % 15 == 0:
            _save(state, out_path)
            _seed_guard("read_word", md5_before)
            n = len(state["records"])

            def _cacc(key):
                ok = tot = 0
                for r in state["records"]:
                    for i, row in enumerate(r[key]):
                        pred = LETTERS26[int(np.argmin(row))]
                        ok += int(pred == r["word"][i])
                        tot += 1
                return 100.0 * ok / tot if tot else 0.0

            print(f"    ... {n}/{len(my_words)} words  static_within={_cacc('static_within'):.1f}%"
                  f"  genB_within={_cacc('genB_within'):.1f}%  coartic_within={_cacc('coartic_within'):.1f}%"
                  f"  [{time.time()-t0:.1f}s]", flush=True)
            if time.time() > deadline:
                _save(state, out_path)
                _seed_guard("read_word", md5_before)
                print(f"  WALL-BUDGET: {len(state['records'])}/{len(my_words)} done -- re-invoke "
                      f"--stage read_word to resume.", flush=True)
                return 2

    state["done"] = True
    _save(state, out_path)
    _seed_guard("read_word", md5_before)
    print(f"  read_word {len(state['records'])} words  [{time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: decode -- lexicon collapse (r61/r70's decoders, reused verbatim) on EACH word-context
#  emission (static / motor-sim / +coarticulation), within AND cross where applicable.
# ============================================================================================= #
def stage_decode():
    print(f"\n{SEP}\n  STAGE: decode (lexicon collapse on each emission, r61/r70 decoders reused "
          f"verbatim)\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("decode")
    lexicon = _load(RUN61_LEXICON)
    lex_by_len = r61._lex_by_len(lexicon["lexicon"])
    logfreq = lexicon["logfreq"]

    rw = _require("read_word.json")
    if not rw.get("done"):
        raise SystemExit("WALL: read_word not COMPLETE -- re-invoke --stage read_word.")

    per_word = []
    for r in rw["records"]:
        word = r["word"]
        L = len(word)
        rec = {"wid": r["wid"], "writer": r["writer"], "word": word, "len": L}
        for label, dists in (("static_within", r["static_within"]),
                             ("static_cross", r["static_cross"]),
                             ("genB_within", r["genB_within"]),
                             ("genB_cross", r["genB_cross"]),
                             ("coartic_within", r["coartic_within"])):
            rec[f"{label}_a"] = r70.decode_arm_a(dists)
            rec[f"{label}_b"] = r70.decode_arm_b(dists, L, lex_by_len, logfreq)
        per_word.append(rec)
        if len(per_word) % 50 == 0:
            print(f"    ... decoded {len(per_word)}/{len(rw['records'])}  [{time.time()-t0:.1f}s]",
                  flush=True)

    _save({"per_word": per_word, "stroke_shapes_md5": md5_before}, _ckpt("decode.json"))
    _seed_guard("decode", md5_before)
    print(f"  decoded {len(per_word)} words  [{time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  REPORTING / VERDICT.
# ============================================================================================= #
def _char_acc_pair(pred: str, true: str) -> tuple:
    n = min(len(pred), len(true))
    return sum(1 for i in range(n) if pred[i] == true[i]), len(true)


def _word_report(per_word: list, label: str, arm: str) -> dict:
    n = len(per_word)
    word_ok = char_ok = n_char = 0
    flags = []
    for pw in per_word:
        pred = pw[f"{label}_{arm}"]
        true = pw["word"]
        ok = (pred == true)
        word_ok += ok
        flags.append(ok)
        c, tot = _char_acc_pair(pred, true)
        char_ok += c
        n_char += tot
    return {"n": n, "word_ok": word_ok, "word_acc": word_ok / n if n else 0.0,
            "word_ci": list(_wilson(word_ok, n)), "char_acc": char_ok / n_char if n_char else 0.0,
            "n_char": n_char, "flags": flags}


def _iso_acc(records: list, inv_key: str, pose_key: str) -> dict:
    n = len(records)
    ok = 0
    flags = []
    for r in records:
        v = np.asarray(r[inv_key]) + PRIMARY_LAMBDA * np.asarray(r[pose_key])
        c = int(np.argmin(v)) + 10
        hit = (c == r["true_class"])
        ok += hit
        flags.append(hit)
    return {"n": n, "k": ok, "acc": ok / n if n else 0.0, "ci": list(_wilson(ok, n)), "flags": flags}


def _row(label, acc, ci, n, extra=""):
    print(f"  {label:<46}{100*acc:>8.1f}%{f'[{100*ci[0]:.1f},{100*ci[1]:.1f}]':>15}"
          f"{'n='+str(n):>9}  {extra}")


def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 71 SCOREBOARD (INCREMENTAL MOTOR-SIMULATION AbS)\n{SEP}",
          flush=True)
    md5_now = _seed_guard("summary")
    prep = _require("prep.json")
    print(f"  SEED-GUARD: seeds/stroke_shapes.json md5 = {md5_now}  "
          f"(== prep capture {prep['stroke_shapes_md5']}: {md5_now == prep['stroke_shapes_md5']})")
    print(f"  test-set reproduction: iso matches r69={prep['iso_test_match_run69']}  "
          f"word matches r70={prep['word_test_match_run70']}")

    ri = _require("read_iso.json")
    if not ri.get("done"):
        print("  WALL: read_iso not COMPLETE."); return 1
    rw_dec = _require("decode.json")
    per_word = rw_dec["per_word"]

    print(f"\n  BAP calibration (Gilet/Diard/Bessiere 2011): within {BAP_WITHIN:.1f}%  "
          f"cross {BAP_CROSS:.1f}%")
    print(f"  run 69 isolated char (static): within {RUN69_WITHIN_ISO_CHAR:.1f}%  "
          f"cross {RUN69_CROSS_ISO_CHAR:.1f}%")
    print(f"  run 70 word-context char (static): within {RUN70_WITHIN_WORD_CHAR:.1f}%  "
          f"cross {RUN70_CROSS_WORD_CHAR:.1f}%  |  run 70 within WORD (lexicon): "
          f"{RUN70_WITHIN_WORD_ACC:.1f}%")

    # -------------------------------------------------------------------------------------- #
    #  TABLE 1 -- ISOLATED char accuracy, arms A(reused)/B(motor-sim) x within/cross.
    # -------------------------------------------------------------------------------------- #
    recs = ri["records"]
    n_iso = len(recs)
    A_within = _iso_acc(recs, "static_invB", "static_poseE")
    A_cross = _iso_acc(recs, "static_invA", "static_poseC")
    B_within = _iso_acc(recs, "genB_inv", "genB_pose")
    B_cross = _iso_acc(recs, "genC_inv", "genC_pose")
    print(f"\n  === TABLE 1: ISOLATED char accuracy (n={n_iso}) -- arm A[STATIC, reused] vs "
          f"arm B[MOTOR-SIM] ===")
    hdr = f"  {'condition':<46}{'char_acc':>9}{'char_CI':>15}{'n':>9}"
    print(hdr); print("  " + "-" * (len(hdr) - 2))
    _row("A within (static, run69's E)", A_within["acc"], A_within["ci"], n_iso)
    _row("B within (motor-sim)", B_within["acc"], B_within["ci"], n_iso)
    _row("A cross  (static, run69's C)", A_cross["acc"], A_cross["ci"], n_iso)
    _row("B cross  (motor-sim)", B_cross["acc"], B_cross["ci"], n_iso)
    mc_iso_within = _mcnemar(A_within["flags"], B_within["flags"])
    mc_iso_cross = _mcnemar(A_cross["flags"], B_cross["flags"])
    print(f"  McNemar (B vs A, within): fixed={mc_iso_within['fixed']} "
          f"broken={mc_iso_within['broken']} p={mc_iso_within['p']:.3g}")
    print(f"  McNemar (B vs A, cross):  fixed={mc_iso_cross['fixed']} "
          f"broken={mc_iso_cross['broken']} p={mc_iso_cross['p']:.3g}")

    # -------------------------------------------------------------------------------------- #
    #  TABLE 2 -- WORD-CONTEXT char accuracy, arms A/B/C(within only) x within/cross.
    # -------------------------------------------------------------------------------------- #
    def word_char_acc(label):
        ok = tot = 0
        for pw in per_word:
            preds = pw[f"{label}_a"]  # arm 'a' = no-context per-char argmin -> raw char acc.
            for i, ch in enumerate(preds):
                ok += int(ch == pw["word"][i])
                tot += 1
        return ok, tot

    print(f"\n  === TABLE 2: WORD-CONTEXT char accuracy (no-context per-char, n_words="
          f"{len(per_word)}) -- arm A[STATIC,reused] / B[MOTOR-SIM] / C[+COARTICULATION] ===")
    hdr2 = f"  {'condition':<46}{'char_acc':>9}{'char_CI':>15}{'n_char':>9}"
    print(hdr2); print("  " + "-" * (len(hdr2) - 2))
    word_rows = {}
    for label, disp in (("static_within", "A within (static, run70's arm a)"),
                        ("genB_within", "B within (motor-sim)"),
                        ("coartic_within", "C within (motor-sim+coarticulation)"),
                        ("static_cross", "A cross  (static, run70's arm a)"),
                        ("genB_cross", "B cross  (motor-sim)")):
        ok, tot = word_char_acc(label)
        ci = _wilson(ok, tot)
        word_rows[label] = (ok, tot, ci)
        _row(disp, ok / tot if tot else 0.0, ci, tot)

    # -------------------------------------------------------------------------------------- #
    #  TABLE 3 -- WORD accuracy (lexicon collapse, arm 'b'), WITHIN-writer, all emissions.
    # -------------------------------------------------------------------------------------- #
    print(f"\n  === TABLE 3: WORD accuracy WITH LEXICON (n_words={len(per_word)}), WITHIN-writer "
          f"-- vs run 70's {RUN70_WITHIN_WORD_ACC:.1f}% ===")
    hdr3 = f"  {'emission':<46}{'word_acc':>9}{'word_CI':>15}{'char_acc':>11}"
    print(hdr3); print("  " + "-" * (len(hdr3) - 2))
    reports = {}
    for label, disp in (("static_within", "A static (reused, == run 70's arm b)"),
                        ("genB_within", "B motor-sim"),
                        ("coartic_within", "C motor-sim+coarticulation")):
        rep = _word_report(per_word, label, "b")
        reports[label] = rep
        print(f"  {disp:<46}{100*rep['word_acc']:>8.1f}%"
              f"{f'[{100*rep['word_ci'][0]:.1f},{100*rep['word_ci'][1]:.1f}]':>15}"
              f"{100*rep['char_acc']:>10.1f}%")
    best_label = max(reports, key=lambda k: reports[k]["word_acc"])
    best = reports[best_label]
    mc_static_vs_best = _mcnemar(reports["static_within"]["flags"], best["flags"]) \
        if best_label != "static_within" else None
    if mc_static_vs_best:
        print(f"  McNemar (best={best_label} vs static): fixed={mc_static_vs_best['fixed']} "
              f"broken={mc_static_vs_best['broken']} p={mc_static_vs_best['p']:.3g}")

    # -------------------------------------------------------------------------------------- #
    #  VERDICT.
    # -------------------------------------------------------------------------------------- #
    iso_win_char = (100 * B_within["acc"] > BAR_WITHIN_CHAR) and \
        (100 * B_within["ci"][0] > 100 * A_within["ci"][1] or 100 * B_within["ci"][0] > BAR_WITHIN_CHAR)
    word_win = (100 * best["word_acc"] > BAR_WITHIN_WORD) and (100 * best["word_ci"][0] > RUN70_WITHIN_WORD_ACC)
    coartic_ok, coartic_tot, _ = word_rows["coartic_within"]
    static_ok, static_tot, _ = word_rows["static_within"]
    coartic_lifts_gap = (coartic_ok / coartic_tot) > (static_ok / static_tot) if static_tot else False

    print(f"\n  MILESTONE (pre-registered: within-writer char > {BAR_WITHIN_CHAR:.0f}% [B isolated] "
          f"AND within-writer word acc CI-separated above run70's {RUN70_WITHIN_WORD_ACC:.1f}%):")
    print(f"    B within isolated char = {100*B_within['acc']:.1f}% "
          f"CI=[{100*B_within['ci'][0]:.1f},{100*B_within['ci'][1]:.1f}]  "
          f"(> {BAR_WITHIN_CHAR:.0f}%? {100*B_within['acc'] > BAR_WITHIN_CHAR})")
    print(f"    best within word emission = {best_label}: {100*best['word_acc']:.1f}% "
          f"CI=[{100*best['word_ci'][0]:.1f},{100*best['word_ci'][1]:.1f}]  "
          f"(> run70 {RUN70_WITHIN_WORD_ACC:.1f}%, CI-separated? "
          f"{100*best['word_ci'][0] > RUN70_WITHIN_WORD_ACC})")
    print(f"    coarticulation (C) word-context char {'CLOSES' if coartic_lifts_gap else 'does NOT close'} "
          f"the gap vs static ({100*coartic_ok/coartic_tot:.1f}% vs {100*static_ok/static_tot:.1f}%)")
    win = iso_win_char and word_win
    print(f"    VERDICT: {'WIN -- motor-simulation AbS lifts reading toward BAP and beats run 70 word reading' if win else 'NULL -- motor-simulation does not materially beat the static writer-relative-pose recognizer'}")

    print(f"\n  ANOMALIES / HONEST RESIDUALS:")
    print(f"    given char+word segmentation throughout (measures the emission model, not "
          f"segmentation).")
    print(f"    within-writer generator pruning: CROSS uses ALL run66 K_ALLO allographs (min over "
          f"bank); WITHIN uses up to M_BANK={M_BANK} own exemplars (min over bank); coarticulation "
          f"(C) uses ONLY the FIRST available form per class (no min-over-bank) to bound cost.")
    print(f"    coarticulation (C) restricted to WITHIN-writer (the pre-registered question).")
    print(f"    class_scale n_obs range: {min(prep['class_scale_n'].values())}-"
          f"{max(prep['class_scale_n'].values())} background exemplars per class.")

    _save({"iso": {"A_within": A_within, "A_cross": A_cross, "B_within": B_within,
                   "B_cross": B_cross},
           "word_char": {k: {"ok": v[0], "tot": v[1], "ci": list(v[2])} for k, v in word_rows.items()},
           "word_acc": {k: {kk: vv for kk, vv in v.items() if kk != "flags"}
                        for k, v in reports.items()},
           "best_label": best_label, "win": win}, _ckpt("summary.json"))
    _seed_guard("summary", md5_now)
    print(f"\n  saved -> {_ckpt('summary.json')}")
    print(f"\n{SEP}\n  RUN 71 COMPLETE -- see final agent report.\n{SEP}", flush=True)
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True,
                   choices=["prep", "genforms", "read_iso", "read_word", "decode", "summary"])
    args = p.parse_args()
    return {"prep": stage_prep, "genforms": stage_genforms, "read_iso": stage_read_iso,
            "read_word": stage_read_word, "decode": stage_decode,
            "summary": stage_summary}[args.stage]()


if __name__ == "__main__":
    sys.exit(main())
