"""jabberwock_bootstrap_read_run73.py -- RUN 73: BOOTSTRAPPED (SELF-SUPERVISED) WRITER ADAPTATION.

THE INSIGHT (creator): a human has no lifetime cursive prior -- a rusty adult learned it from a
bounded childhood CURRICULUM and still reads it; a training-free system (curriculum bank +
writer-adaptation) IS that model. But a human reading an UNKNOWN hand doesn't get the writer's
labeled alphabet handed to them -- they read SLOWLY, the first words struggle, the writer's own
letterforms start to click, and the rest gets easier. Run 69's 55% within-writer char accuracy
CHEATED: it scored against the writer's GIVEN labeled bank. RUN 73 asks whether the SAME lift is
achievable by BOOTSTRAPPING the writer's hand from unlabeled ink alone -- no ground-truth bank, no
training, just self-supervised harvest-and-refine (EM / the homework loop's own mark -> assign ->
practice shape, one level up: here "practice" is re-reading with a growing self-harvested bank
instead of a stroke-generation drill).

REUSE (nothing new-from-scratch for the RECOGNIZER itself -- only the bootstrap LOOP is new):
  * `scripts.jabberwock_pose_read_run69` (r69) -- writer-relative pose machinery verbatim:
    `aggregate_scale_slant` / `local_baseline_topline` (the UNSUPERVISED frame estimator -- no
    identity needed, just neighbor-glyph vertical extents), `invariant_canon` / `pose_canon`,
    `_class_cost` (bank-based DTW class-cost vector), `select_bank` / `_bank_canons` (for the
    CEILING reference only), `_group_by_writer` / `_index_by_writer_sample` / `glyphs_by_sample`.
    Run 69's own `cross_bank` + `population_frame` are loaded VERBATIM (READ-ONLY) from
    `results/run69_checkpoints/prep.json` -- this IS the "generic / cross-writer pooled bank,
    NOT the target writer's labels" cold-start bank the task asks for.
  * `scripts.jabberwock_cursive_wordread_run70` (r70) -- `local_frame_for_word_char` (per-word-char
    frame plumbing), `select_test_words`-style selection pattern (adapted below for a PER-WRITER
    word budget: this run needs MANY words per held-out writer, not many writers with few words
    each, to observe a real warm-up trajectory), `decode_arm_a` / `decode_arm_b` / `_pad62` /
    `SYMBOLS62` (r61's decoders reused unmodified on this run's native 26-class posteriors).
  * `scripts.jabberwock_wordread_run61` (r61) -- the lexicon (`_lex_by_len`, WordNet+Brown counts,
    loaded READ-ONLY from `results/run61_checkpoints/lexicon.json`), `_wilson_ci`, `_mcnemar`.
  * `scripts.jabberwock_ia_read_run68` (r68) -- `_lower26` / `LETTERS26` (the 0..25 lowercase
    index space every distance vector in this run lives in).
  * `domains/homework_loop.py` -- CITED, not literally called: its mark -> assign -> babble shape
    (grounding session emits residuals -> a worksheet is DERIVED from those residuals -> practice
    consumes only the surviving residual -> a frontier/confidence gate decides what enters the next
    cycle) is the SAME shape this run's harvest -> bootstrap -> re-read loop takes, one level up
    (letters instead of ink-parse spans, an EXTERNAL lexicon-confirmation confidence signal instead
    of an internal round-trip-render score). The literal functions are NOT reused because they
    operate over a different domain object (`WorksheetItem`'s render-ready parse spans, built for
    the ink GENERATION/quantization pipeline) that has no letter-identity concept -- reading a
    known-writer's hand needs a different confidence signal (lexicon-committed margin) than judging
    whether a re-rendered stroke reproduces its own parse. This is stated honestly rather than
    forcing an inapplicable import.

THE COLD-START / CEILING DEFINITIONS (mapped onto run 69's own 5-condition ladder, so this run's
round-0 and converged-round numbers are DIRECTLY comparable to run 69/70's own reported numbers):
  COLD  (round 0, before any bootstrap) = run 69's condition D, POSE_FRAME_ONLY: invariant+pose
        scored with the WRITER'S OWN estimated frame (baseline/x-height/slant -- unsupervised,
        needs no character identity, just neighbor-glyph geometry) against the GENERIC CROSS bank
        (pooled background writers, M=3/class, run 69's own `cross_bank`). This is the strongest
        HONEST cold start: everything in it is available before a single letter of the writer's
        hand has been read (frame estimation from raw ink extents is unsupervised by construction,
        exactly per the task's step-1 framing).
  CEILING (never fed to the bootstrap loop, reported for calibration ONLY) = run 69's condition E,
        POSE_WITHIN: the SAME own-frame pose channel against the writer's REAL, GIVEN-LABEL own
        bank (M=3/class, ground truth). This is run 69/70's own "cheating" 55%/58% char, 30.5% word
        number -- the target the bootstrap is asked to climb toward, never touched by decoding.
  BOOTSTRAPPED (this run's OWN contribution) = same own-frame pose channel, but the "own bank" is
        built ENTIRELY from PSEUDO-labels self-harvested from the SAME held-out writer's OTHER
        unlabeled words -- backed off to the cross bank per-class wherever no pseudo-label for that
        class has been harvested yet (`min(boot_cost, cross_cost)`, a fusion that can only help or
        tie, never hurt, relative to cross-alone).

THE HARVEST RULE (pre-registered from the SCORE distribution alone, before looking at any accuracy
number -- avoids threshold-shopping against the outcome):
  A word is harvested (its per-position committed letters become pseudo-labels) iff:
    (1) FULL per-char agreement: the context-free per-char argmin (`decode_arm_a`) spells EXACTLY
        the same string as the lexicon-committed word (`decode_arm_b`) -- the visual channel and
        the language prior agree with no correction needed, the "I clearly read this, no
        ambiguity" case;
    (2) the lexicon commitment is NON-trivial: among same-length lexicon candidates, the margin
        between the best and second-best summed cost, normalized per character, is >=
        MARGIN_THRESHOLD -- a constant fixed as the MEDIAN of round-0's finite (n_cands>1) margins
        BEFORE any bootstrap round is scored, i.e. "top half of round-0's genuinely-competitive
        words" (words whose length has only one lexicon candidate get margin=+inf and pass (2)
        automatically, but still gated by (1)).
  Reported alongside (not cherry-picked): a looser variant (agreement>=0.8) and stricter/looser
  percentiles (30th/70th) of the SAME rule, for robustness.

THE LOOP: (round-based EM, LEAVE-ONE-WORD-OUT to guard against circular self-confirmation)
  round 0: pool = {} (empty) -> COLD decode == cross-bank-only by construction (empty pool means
           every class backs off to cross). Harvest confident words -> pool_1.
  round r: decode EVERY word using pool_{r-1} EXCLUDING any pseudo-label harvested FROM THAT SAME
           WORD (a word's own committed letters may never bootstrap the bank used to re-score it --
           the mechanism the task calls out explicitly: "pseudo-label bootstrap can DRIFT
           (confirmation bias)"). Harvest -> merge into pool_r (per (writer,class) cap M_BOOT=3,
           kept by highest margin, same cap run 69's ceiling bank uses -- an apples-to-apples pool
           size, not an unbounded-exemplar advantage).
  STOP when a round harvests zero NEW (writer,class,word) triples (the pool has saturated) or
  MAX_ROUNDS is hit (reported honestly if so).
  DRIFT CHECK: per round, the PRECISION of the pseudo-labels actually harvested that round (fraction
  of harvested CHARACTERS that are actually correct, computed against ground truth for REPORTING
  ONLY -- never fed back into the decode) is tracked; a falling precision across rounds is the
  drift signature the task asks to guard against and report honestly if it appears.

THE WARM-UP CURVE (separate from the round-based EM -- a STRICTLY CAUSAL, single-pass, per-writer
streaming read, no leave-one-out needed because nothing from the future is ever used): for each
held-out writer, words are visited in a random order; the pool available at position k contains
ONLY pseudo-labels harvested from positions 1..k-1 of THIS SAME pass. Averaged over
`N_ORDER_SEEDS` random re-orderings per writer (to smooth order-dependent noise -- still pure
lookup, no native calls), then over writers, this gives accuracy AS A FUNCTION OF WORDS-READ -- the
direct realization of "does it click like a human".

PERFORMANCE NOTE (why this run is fast despite iterating many EM rounds): DTW cost between any two
FIXED point canons never changes across rounds -- only WHICH exemplars are in the bank changes. So
the expensive native step (`cc66.dtw` via substrate_rs) is run EXACTLY ONCE per stage `read`,
producing (a) every query char's cost against the FIXED cross bank, (b) every query char's cost
against the FIXED real own bank (ceiling), and (c) the FULL PAIRWISE DTW matrix between every pair
of same-writer query chars (the only possible pseudo-label exemplar source for that writer's own
words). Every subsequent EM round and every streaming step is then a pure Python/numpy MIN-lookup
into these three fixed tables -- no further native calls, so convergence and the warm-up curve are
computed in the `bootstrap` stage without touching substrate_rs at all.

DISCIPLINE: donkey=0 (closed-form geometry + count-based lexicon + EM harvest/threshold logic, NOT
an SGD-trained net). SEED GUARD: OZMA_SEED_PERSIST_DISABLED=1, md5(seeds/stroke_shapes.json)
asserted UNCHANGED before/after every stage. `results/run6{1,6,8,9}_checkpoints/` and
`results/run70_checkpoints/` are READ-ONLY (opened, never written). This run writes ONLY
`results/run73_checkpoints/*`. NO git add/commit.

EXECUTION (ops law): every invocation <=540s FOREGROUND, checkpointed under
`results/run73_checkpoints/`. `.venv` python needed for `read` (native `substrate_rs` DTW calls);
`prep`/`bootstrap`/`summary` are pure Python (numpy only) and can run under either interpreter (run
under `.venv` throughout for consistency with the rest of this arc). NEVER run in background; NEVER
end a turn with a live process.

Run (from the gamma-substrate repo root):
  OZMA_SEED_PERSIST_DISABLED=1 DEEPWRITING_DIR=/tmp/handwriting PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python3 \\
    scripts/jabberwock_bootstrap_read_run73.py --stage <prep|read|bootstrap|summary>
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
import scripts.jabberwock_wordread_run61 as r61
import scripts.jabberwock_ia_read_run68 as r68
from domains import deepwriting_world as dww

SEP = "=" * 92
STROKE_SHAPES_SEED = r69.STROKE_SHAPES_SEED
CKPT_DIR = os.path.join(ROOT, "results", "run73_checkpoints")
LOG = os.path.join(ROOT, "results", "omniglot_gate_run73.log")
os.makedirs(CKPT_DIR, exist_ok=True)

RUN61_LEXICON = os.path.join(ROOT, "results", "run61_checkpoints", "lexicon.json")     # READ-ONLY.
RUN69_PREP = os.path.join(ROOT, "results", "run69_checkpoints", "prep.json")           # READ-ONLY.

LETTERS26 = r68.LETTERS26
_lower26 = r68._lower26
BIG = 1e6

# ------------------------------------------------------------------------------------------- #
# PRE-REGISTERED CONSTANTS.
# ------------------------------------------------------------------------------------------- #
SPLIT = r69.SPLIT
WRITER_SPLIT_SEED = r69.WRITER_SPLIT_SEED             # == the whole arc's own split seed.
N_BACKGROUND_FRAC = r69.N_BACKGROUND_FRAC
M_BANK = r69.M_BANK                                    # == ceiling bank size AND boot pool cap.
BANK_SELECT_SEED = r69.BANK_SELECT_SEED
LOCAL_WINDOW = r69.LOCAL_WINDOW
LOWER_CLASSES = r69.LOWER_CLASSES
PRIMARY_LAMBDA_POSE = r69.PRIMARY_LAMBDA               # invariant+pose mix weight (run 69's, 1.0).

WORD_MIN_LEN, WORD_MAX_LEN = 3, 8
MIN_WORDS_PER_WRITER = 10          # NEW: eligibility bar -- need real bootstrap depth per writer.
CAP_WORDS_PER_WRITER = 20          # NEW: budget cap per writer (keeps compute bounded).
WORD_SELECT_SEED = 20260910        # NEW, pre-registered before running.
M_BOOT = M_BANK                    # bootstrapped-bank cap per (writer,class) -- apples-to-apples.
MAX_ROUNDS = 8                     # EM safety cap.
N_ORDER_SEEDS = 5                  # random re-orderings per writer for the warm-up curve.
PER_CALL_BUDGET_SECONDS = 480.0

# Harvest rule, part (1): full per-char agreement is the PRIMARY bar (0.8 reported as robustness).
AGREEMENT_PRIMARY = 1.0
AGREEMENT_ROBUST = 0.8
MARGIN_PCTL_PRIMARY = 50           # median of round-0's finite margins.
MARGIN_PCTL_ROBUST = (30, 70)

# Calibration numbers this run reports against (run 69/70's OWN numbers, different word sample).
BAP_WITHIN = r69.BAP_WITHIN
BAP_CROSS = r69.BAP_CROSS
RUN69_WITHIN_CHAR = 55.0
RUN69_CROSS_CHAR = 28.8
RUN70_WITHIN_WORD = 30.5
RUN70_CROSS_WORD = 5.9

# Pre-registered WIN bar: bootstrapped word accuracy at convergence closes >=40% of the
# cold -> ceiling gap, AND is CI-separated above cold.
GAP_CLOSE_BAR = 0.40


# ============================================================================================= #
#  I/O + seed guard (identical pattern to runs 61/68/69/70).
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
#  WRITER / WORD SELECTION -- need DEPTH per writer (many words), not breadth (many writers, few
#  words each, run 69/70's own choice, correct for THAT question but wrong for this one).
# ============================================================================================= #
def select_bootstrap_words(ho_words: list, lexicon_set: set, min_words: int, cap: int,
                           seed: int) -> list:
    """Deterministic per-writer selection: only writers with >= `min_words` in-vocabulary held-out
    words are eligible (need real bootstrap depth); each eligible writer contributes up to `cap`
    seeded-shuffled, deduped words (dedup key mirrors r70.select_test_words's own convention)."""
    pool = [w for w in ho_words if w["word"] in lexicon_set]
    by_writer = defaultdict(list)
    for w in pool:
        by_writer[w["writer"]].append(w)
    rng = np.random.default_rng(seed)
    selected = []
    for w in sorted(wid for wid, lst in by_writer.items() if len(lst) >= min_words):
        lst = by_writer[w]
        order = rng.permutation(len(lst))
        seen, chosen = set(), []
        for i in order:
            wd = lst[int(i)]
            key = (wd["writer"], wd["word"], wd["sample"], tuple(wd["word_point_span"]))
            if key in seen:
                continue
            seen.add(key)
            chosen.append(wd)
            if len(chosen) >= cap:
                break
        selected.extend(chosen)
    return selected


# ============================================================================================= #
#  STAGE: prep -- writer/word selection, own UNSUPERVISED frame, REAL own bank (ceiling ref only),
#  per-char query canons. Pure numpy, no native calls.
# ============================================================================================= #
def build_prep(min_words: int = MIN_WORDS_PER_WRITER, cap: int = CAP_WORDS_PER_WRITER,
               m_bank: int = M_BANK, dw=None, all_glyphs=None, run69_prep=None,
               lexicon=None) -> dict:
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

    if run69_prep is None:
        if not os.path.exists(RUN69_PREP):
            raise SystemExit(f"WALL: run 69's prep.json not found at {RUN69_PREP}.")
        run69_prep = _load(RUN69_PREP)
    run69_bg_writers = set(run69_prep["bg_writers"])
    bg_writers_match_run69 = (run69_bg_writers == bg_writers)
    population_frame = run69_prep["population_frame"]
    cross_bank = run69_prep["cross_bank"]

    if lexicon is None:
        if not os.path.exists(RUN61_LEXICON):
            raise SystemExit(f"WALL: run 61's lexicon.json not found at {RUN61_LEXICON}.")
        lexicon = _load(RUN61_LEXICON)
    lexicon_set = set(lexicon["lexicon"])

    test_words = select_bootstrap_words(ho_words, lexicon_set, min_words, cap, WORD_SELECT_SEED)
    test_writers = sorted({w["writer"] for w in test_words})
    test_samples_by_writer = defaultdict(set)
    for w in test_words:
        test_samples_by_writer[w["writer"]].add(w["sample"])

    by_writer = r69._group_by_writer(all_glyphs)
    ws_index = r69._index_by_writer_sample(all_glyphs)

    # -- own UNSUPERVISED frame (baseline/x-height/slant from the writer's OTHER, test-excluded
    #    ink -- identity-free, needs no labels).
    frame_of_writer = {}
    n_degenerate_frame = 0
    for w in test_writers:
        gbs = r69.glyphs_by_sample(by_writer.get(w, []), exclude_samples=test_samples_by_writer[w])
        fr = r69.aggregate_scale_slant(gbs)
        frame_of_writer[w] = fr
        if fr["n_xh_obs"] == 0:
            n_degenerate_frame += 1

    # -- REAL own bank (ground-truth labels) -- CEILING REFERENCE ONLY, never fed to the bootstrap
    #    decode loop.
    real_own_bank = {}
    real_own_bank_coverage = {}
    for w in test_writers:
        pool_w = [g for g in by_writer.get(w, []) if g["sample"] not in test_samples_by_writer[w]]
        raw = r69.select_bank(pool_w, LOWER_CLASSES, m_bank,
                              np.random.default_rng(BANK_SELECT_SEED + w))
        real_own_bank[str(w)] = r69._bank_canons(raw, frame_of_writer, ws_index)
        real_own_bank_coverage[str(w)] = {str(c): len(v) for c, v in raw.items()}

    # -- per-word, per-char query canons (invariant + pose under the OWN unsupervised frame only --
    #    this run never uses the population frame; the writer's own frame IS the cold-start frame).
    word_records = []
    n_frame_fallback = 0
    for wi, wd in enumerate(test_words):
        w = wd["writer"]
        own_fr = frame_of_writer[w]
        chars = []
        for cs in wd["char_segs"]:
            baseline, fell_back = r70.local_frame_for_word_char(dw, wd, cs, ws_index)
            n_frame_fallback += int(fell_back)
            chars.append({
                "true_symbol": cs["symbol"],
                "inv": r69.invariant_canon(cs["strokes"]),
                "pose_own": r69.pose_canon(cs["strokes"], baseline, own_fr["x_height"],
                                           own_fr["slant_deg"]),
            })
        word_records.append({"wid": wi, "writer": w, "word": wd["word"], "chars": chars})

    words_per_writer = Counter(wd["writer"] for wd in word_records)
    return {
        "bg_writers": sorted(bg_writers), "ho_writers": sorted(ho_writers),
        "bg_writers_match_run69": bg_writers_match_run69,
        "test_writers": test_writers,
        "cross_bank": cross_bank,
        "writer_frames": {str(w): fr for w, fr in frame_of_writer.items()},
        "real_own_bank": real_own_bank,
        "real_own_bank_coverage": real_own_bank_coverage,
        "word_records": word_records,
        "n_test_words": len(word_records),
        "n_test_writers": len(test_writers),
        "words_per_writer": {str(w): n for w, n in words_per_writer.items()},
        "n_ho_words": len(ho_words),
        "n_degenerate_own_frame": n_degenerate_frame,
        "n_word_char_frame_fallback": n_frame_fallback,
        "word_len_dist": dict(Counter(len(wd["word"]) for wd in word_records)),
        "run61_lexicon_n": len(lexicon["lexicon"]),
    }


def stage_prep():
    print(f"\n{SEP}\n  STAGE: prep (writer/word selection -- DEPTH not breadth -- own unsupervised "
          f"frame + real own bank [ceiling ref] + query canons)\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("prep")
    print(f"  seeds/stroke_shapes.json md5 (before): {md5_before}", flush=True)

    out = build_prep()
    out["stroke_shapes_md5"] = md5_before
    _save(out, _ckpt("prep.json"))
    _seed_guard("prep", md5_before)

    print(f"  bg writers={len(out['bg_writers'])}  ho writers={len(out['ho_writers'])}  "
          f"(match run 69's bg set: {out['bg_writers_match_run69']})", flush=True)
    print(f"  eligible test writers (>= {MIN_WORDS_PER_WRITER} in-vocab words) = "
          f"{out['n_test_writers']}  total test words = {out['n_test_words']}", flush=True)
    wpw = sorted(out["words_per_writer"].values())
    print(f"  words/writer: min={wpw[0]} median={wpw[len(wpw)//2]} max={wpw[-1]}", flush=True)
    print(f"  word length dist: {sorted(out['word_len_dist'].items())}", flush=True)
    print(f"  degenerate own-frame writers: {out['n_degenerate_own_frame']} / "
          f"{out['n_test_writers']}", flush=True)
    print(f"  word-char local-frame fallback: {out['n_word_char_frame_fallback']}", flush=True)
    empty = sum(1 for cov in out["real_own_bank_coverage"].values()
               for c, n in cov.items() if n == 0)
    print(f"  real-own-bank (ceiling ref) empty (writer,class) cells: {empty} / "
          f"{out['n_test_writers'] * len(LOWER_CLASSES)}", flush=True)
    print(f"  saved -> {_ckpt('prep.json')}  [prep {time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: read -- THE ONLY NATIVE STAGE. Precomputes THREE FIXED tables (see module docstring's
#  "performance note"): cross-bank cost, ceiling-bank cost, and the full same-writer pairwise DTW
#  matrix. Block-checkpointed per writer, resumable.
# ============================================================================================= #
def stage_read():
    print(f"\n{SEP}\n  STAGE: read -- native DTW precompute (cross cost, ceiling cost, same-writer "
          f"pairwise matrix)\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("read")
    import substrate_rs as srs
    native = srs.Substrate()._inner
    prep = _require("prep.json")
    cross_bank = prep["cross_bank"]
    real_own_bank = prep["real_own_bank"]
    word_records = prep["word_records"]

    # group words by writer, assign writer-LOCAL char indices in a stable (wid, pos) order.
    by_writer_words = defaultdict(list)
    for wd in word_records:
        by_writer_words[wd["writer"]].append(wd)
    for w in by_writer_words:
        by_writer_words[w].sort(key=lambda wd: wd["wid"])

    out_path = _ckpt("read.json")
    state = _load(out_path) if os.path.exists(out_path) else {
        "chars_done": [], "pairwise_done_writers": [], "chars": {}, "pairwise": [], "done": False,
    }
    if state.get("done"):
        print(f"  read already COMPLETE.", flush=True)
        return 0

    deadline = time.time() + PER_CALL_BUDGET_SECONDS
    chars_done = set(state["chars_done"])
    pairwise_done = set(state["pairwise_done_writers"])
    n_new = 0

    # -- pass 1: per-char cross/ceiling cost + assign local index. --
    local_idx_of = {}          # (writer, wid, pos) -> local idx (stable across resumes).
    writer_local_chars = defaultdict(list)   # writer -> [(wid,pos), ...] in local-idx order.
    for w in sorted(by_writer_words):
        li = 0
        for wd in by_writer_words[w]:
            for pos in range(len(wd["chars"])):
                local_idx_of[(w, wd["wid"], pos)] = li
                writer_local_chars[w].append((wd["wid"], pos))
                li += 1

    for w in sorted(by_writer_words):
        ob = real_own_bank.get(str(w), {})
        for wd in by_writer_words[w]:
            for pos, ch in enumerate(wd["chars"]):
                key = f"{wd['wid']}:{pos}"
                if key in chars_done:
                    continue
                cross_inv = r69._class_cost(native, ch["inv"], cross_bank, "inv")
                cross_pose = r69._class_cost(native, ch["pose_own"], cross_bank, "pose")
                ceil_inv = r69._class_cost(native, ch["inv"], ob, "inv")
                ceil_pose = r69._class_cost(native, ch["pose_own"], ob, "pose")
                state["chars"][key] = {
                    "writer": w, "wid": wd["wid"], "pos": pos,
                    "local_idx": local_idx_of[(w, wd["wid"], pos)],
                    "true_symbol": ch["true_symbol"],
                    "cross_inv": cross_inv, "cross_pose": cross_pose,
                    "ceil_inv": ceil_inv, "ceil_pose": ceil_pose,
                }
                chars_done.add(key)
                n_new += 1
                if n_new % 40 == 0:
                    state["chars_done"] = sorted(chars_done)
                    _save(state, out_path)
                    _seed_guard("read", md5_before)
                    print(f"    ... chars {len(chars_done)}  [{time.time()-t0:.1f}s]", flush=True)
                    if time.time() > deadline:
                        state["chars_done"] = sorted(chars_done)
                        state["pairwise_done_writers"] = sorted(pairwise_done)
                        _save(state, out_path)
                        _seed_guard("read", md5_before)
                        print(f"  WALL-BUDGET (char pass) -- re-invoke --stage read.", flush=True)
                        return 2

    state["chars_done"] = sorted(chars_done)
    _save(state, out_path)
    _seed_guard("read", md5_before)
    print(f"  char pass complete: {len(chars_done)} chars  [{time.time()-t0:.1f}s]", flush=True)

    # -- pass 2: full same-writer pairwise DTW matrix (i<j), one writer at a time. --
    for w in sorted(writer_local_chars):
        if w in pairwise_done:
            continue
        chars_by_local = {}
        for wid, pos in writer_local_chars[w]:
            key = f"{wid}:{pos}"
            rec = state["chars"][key]
            wd = next(wd for wd in by_writer_words[w] if wd["wid"] == wid)
            chars_by_local[rec["local_idx"]] = wd["chars"][pos]
        n_local = len(chars_by_local)
        for i in range(n_local):
            ci = chars_by_local[i]
            for j in range(i + 1, n_local):
                cj = chars_by_local[j]
                dtw_inv = r69.cc66.dtw(native, ci["inv"], cj["inv"])
                dtw_pose = r69.cc66.dtw(native, ci["pose_own"], cj["pose_own"])
                state["pairwise"].append([w, i, j, dtw_inv, dtw_pose])
        pairwise_done.add(w)
        n_new += 1
        state["pairwise_done_writers"] = sorted(pairwise_done)
        _save(state, out_path)
        _seed_guard("read", md5_before)
        print(f"    ... pairwise writer {w} done ({n_local} chars, {len(pairwise_done)}/"
              f"{len(writer_local_chars)} writers)  [{time.time()-t0:.1f}s]", flush=True)
        if time.time() > deadline:
            print(f"  WALL-BUDGET (pairwise pass) -- re-invoke --stage read.", flush=True)
            return 2

    state["done"] = True
    _save(state, out_path)
    _seed_guard("read", md5_before)
    print(f"  read COMPLETE: {len(state['chars'])} chars, {len(state['pairwise'])} pairwise "
          f"entries, {len(pairwise_done)} writers  [{time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  BOOTSTRAP MACHINERY -- pure Python/numpy, lookups into the fixed tables from `read`. Importable
#  by tests without native/real data.
# ============================================================================================= #
def combined26(inv26, pose26, lam=PRIMARY_LAMBDA_POSE):
    return [inv26[c] + lam * pose26[c] for c in range(26)]


def build_pairwise_index(pairwise_rows: list) -> dict:
    """{(writer, i, j): (dtw_inv, dtw_pose)} for i<j, MIRRORED for (writer, j, i) (DTW between two
    fixed point sets is symmetric -- verified in tests/test_run73_migrated.py)."""
    idx = {}
    for w, i, j, dinv, dpose in pairwise_rows:
        idx[(w, i, j)] = (dinv, dpose)
        idx[(w, j, i)] = (dinv, dpose)
    return idx


def pairwise_cost(pairwise_idx: dict, w: int, li: int, lj: int, lam=PRIMARY_LAMBDA_POSE) -> float:
    dinv, dpose = pairwise_idx[(w, li, lj)]
    return dinv + lam * dpose


def decode_lexicon_margin(dists26: list, true_len: int, lex_by_len: dict) -> dict | None:
    """Same scoring rule as `r61.decode_lexicon` (FLAT prior, alpha=0), but ALSO returns the
    best/second-best cost and the per-char-normalized margin -- the confidence signal `decode_lexicon`
    itself discards. Not a modification of r61 (a pure addition, this run's own new need)."""
    cands = lex_by_len.get(true_len, [])
    if not cands:
        return None
    D = np.asarray(dists26)
    scored = []
    for wcand in cands:
        cls = [_lower26(ch) for ch in wcand]
        cost = float(sum(D[i, cls[i]] for i in range(true_len)))
        scored.append((cost, wcand))
    scored.sort(key=lambda x: x[0])
    best_cost, best_w = scored[0]
    if len(scored) > 1:
        second_cost = scored[1][0]
        margin_per_char = (second_cost - best_cost) / true_len
    else:
        second_cost = math.inf
        margin_per_char = math.inf
    return {"word": best_w, "best_cost": best_cost, "second_cost": second_cost,
            "margin_per_char": margin_per_char, "n_cands": len(cands)}


def harvest_ok(dists26: list, true_len: int, lex_by_len: dict, agreement_bar: float,
              margin_threshold: float) -> dict | None:
    """The harvest rule (see module docstring). Returns the margin record (with an extra
    'agreement' field) if the word PASSES, else None."""
    m = decode_lexicon_margin(dists26, true_len, lex_by_len)
    if m is None:
        return None
    a_pred = r70.decode_arm_a(dists26)
    n = min(len(a_pred), len(m["word"]))
    agree = sum(1 for i in range(n) if a_pred[i] == m["word"][i]) / true_len if true_len else 0.0
    m["agreement"] = agree
    if agree >= agreement_bar and m["margin_per_char"] >= margin_threshold:
        return m
    return None


class BootstrapCorpus:
    """Wraps the fixed tables from `read.json` into the lookups the EM loop / streaming pass need.
    Pure Python, no native/substrate dependency -- built once, reused by every round/step."""

    def __init__(self, chars: dict, pairwise_rows: list, word_records: list, lex_by_len: dict,
                lam: float = PRIMARY_LAMBDA_POSE):
        self.lam = lam
        self.lex_by_len = lex_by_len
        self.pairwise = build_pairwise_index(pairwise_rows)
        self.words = {}            # wid -> {"writer", "word", "positions": [key,...]}
        self.char_by_key = {}      # "wid:pos" -> record with cross_comb/ceil_comb/local_idx/etc.
        for key, rec in chars.items():
            cross_comb = combined26(rec["cross_inv"], rec["cross_pose"], lam)
            ceil_comb = combined26(rec["ceil_inv"], rec["ceil_pose"], lam)
            true_class = _lower26(rec["true_symbol"])
            self.char_by_key[key] = {**rec, "cross_comb": cross_comb, "ceil_comb": ceil_comb,
                                     "true_class": true_class}
        for wd in word_records:
            wid, writer, word = wd["wid"], wd["writer"], wd["word"]
            positions = [f"{wid}:{pos}" for pos in range(len(wd["chars"]))]
            self.words[wid] = {"writer": writer, "word": word, "positions": positions}

    def writers(self):
        return sorted({w["writer"] for w in self.words.values()})

    def words_of_writer(self, w):
        return sorted((wid for wid, rec in self.words.items() if rec["writer"] == w))

    def cross_dists(self, wid) -> list:
        return [self.char_by_key[k]["cross_comb"] for k in self.words[wid]["positions"]]

    def ceiling_dists(self, wid) -> list:
        return [self.char_by_key[k]["ceil_comb"] for k in self.words[wid]["positions"]]

    def boot_dists(self, wid, pool_by_wc: dict, exclude_wid=None) -> list:
        """Combined (backoff-fused) distances for word `wid` given a pool of pseudo-label
        entries. `pool_by_wc[(writer,class)]` = list of {"wid","local_idx","margin"}. Entries whose
        source `wid` == exclude_wid are skipped (leave-one-word-out)."""
        w = self.words[wid]["writer"]
        out = []
        for key in self.words[wid]["positions"]:
            rec = self.char_by_key[key]
            li = rec["local_idx"]
            row = [BIG] * 26
            for c in range(26):
                cands = [e for e in pool_by_wc.get((w, c), []) if e["wid"] != exclude_wid]
                if cands:
                    best = min(pairwise_cost(self.pairwise, w, li, e["local_idx"], self.lam)
                              for e in cands)
                else:
                    best = BIG
                row[c] = min(best, rec["cross_comb"][c])
            out.append(row)
        return out

    def true_word(self, wid) -> str:
        return self.words[wid]["word"]


def _pool_add(pool_by_wc: dict, writer: int, cls: int, wid: int, local_idx: int, margin: float,
             cap: int = M_BOOT) -> bool:
    """Adds one pseudo-label entry, keeping only the top `cap` by margin per (writer,class).
    Returns True iff this call actually changed the pool contents (used for convergence check)."""
    key = (writer, cls)
    lst = pool_by_wc.setdefault(key, [])
    if any(e["wid"] == wid and e["local_idx"] == local_idx for e in lst):
        return False
    m = margin if math.isfinite(margin) else 1e18
    lst.append({"wid": wid, "local_idx": local_idx, "margin": m})
    lst.sort(key=lambda e: -e["margin"])
    del lst[cap:]
    return True   # a genuinely new entry was proposed (even if later truncated by the cap -- the
                  # caller cares about "did a new pseudo-label arrive", not final pool membership).


def _char_acc_and_word_acc(corpus: BootstrapCorpus, wid, dists26) -> tuple:
    true = corpus.true_word(wid)
    a_pred = r70.decode_arm_a(dists26)
    b_pred = r70.decode_arm_b(dists26, len(true), corpus.lex_by_len, {})
    c_ok, _ = r70._char_acc_pair(b_pred, true)
    return c_ok, len(true), int(b_pred == true), a_pred, b_pred


def run_em(corpus: BootstrapCorpus, agreement_bar: float, margin_threshold: float,
          max_rounds: int = MAX_ROUNDS) -> dict:
    """Round-based EM with leave-one-word-out. Returns the full per-round trace + drift check."""
    pool_by_wc: dict = {}
    rounds = []
    harvested_keys = set()   # (writer, class, wid, local_idx) already in the pool ever -- for the
                              # "no NEW pseudo-label this round" convergence test.
    for r in range(max_rounds):
        char_ok = char_n = word_ok = word_n = 0
        new_this_round = []
        harvest_precision_ok = harvest_precision_n = 0
        for wid, wrec in corpus.words.items():
            w = wrec["writer"]
            dists = corpus.boot_dists(wid, pool_by_wc, exclude_wid=wid)
            c_ok, c_n, w_ok, a_pred, b_pred = _char_acc_and_word_acc(corpus, wid, dists)
            char_ok += c_ok
            char_n += c_n
            word_ok += w_ok
            word_n += 1
            rec_harv = harvest_ok(dists, len(wrec["word"]), corpus.lex_by_len, agreement_bar,
                                  margin_threshold)
            if rec_harv is not None:
                true = wrec["word"]
                for pos, ch in enumerate(rec_harv["word"]):
                    key = f"{wid}:{pos}"
                    rec = corpus.char_by_key[key]
                    cls = _lower26(ch)
                    hk = (w, cls, wid, rec["local_idx"])
                    if hk not in harvested_keys:
                        harvested_keys.add(hk)
                        new_this_round.append((w, cls, wid, rec["local_idx"],
                                               rec_harv["margin_per_char"]))
                    harvest_precision_n += 1
                    harvest_precision_ok += int(pos < len(true) and true[pos] == ch)
        for w, cls, wid, li, margin in new_this_round:
            _pool_add(pool_by_wc, w, cls, wid, li, margin)
        coverage = sum(1 for lst in pool_by_wc.values() if lst)
        rounds.append({
            "round": r, "char_acc": char_ok / char_n if char_n else 0.0,
            "word_acc": word_ok / word_n if word_n else 0.0,
            "char_ok": char_ok, "char_n": char_n, "word_ok": word_ok, "word_n": word_n,
            "n_new_harvested_chars": len(new_this_round),
            "harvest_precision": (harvest_precision_ok / harvest_precision_n
                                 if harvest_precision_n else None),
            "pool_coverage_writer_class": coverage,
        })
        if len(new_this_round) == 0:
            break
    return {"rounds": rounds, "converged_at": rounds[-1]["round"],
            "hit_max_rounds": len(rounds) == max_rounds and rounds[-1]["n_new_harvested_chars"] > 0,
            "final_pool_size": sum(len(v) for v in pool_by_wc.values())}


def run_streaming(corpus: BootstrapCorpus, agreement_bar: float, margin_threshold: float,
                  n_order_seeds: int = N_ORDER_SEEDS) -> dict:
    """Strictly causal, single-pass, per-writer streaming read -- the WARM-UP CURVE. No leave-one-
    out needed (nothing from position k is ever used to score positions < k)."""
    by_pos = defaultdict(lambda: {"char_ok": 0, "char_n": 0, "word_ok": 0, "word_n": 0})
    for seed in range(n_order_seeds):
        for w in corpus.writers():
            wids = corpus.words_of_writer(w)
            rng = np.random.default_rng(seed * 100003 + w)
            order = rng.permutation(len(wids))
            pool_by_wc: dict = {}
            for k, oi in enumerate(order):
                wid = wids[int(oi)]
                dists = corpus.boot_dists(wid, pool_by_wc, exclude_wid=None)  # causal: pool holds
                                                                              # ONLY earlier words.
                c_ok, c_n, w_ok, a_pred, b_pred = _char_acc_and_word_acc(corpus, wid, dists)
                slot = by_pos[k]
                slot["char_ok"] += c_ok
                slot["char_n"] += c_n
                slot["word_ok"] += w_ok
                slot["word_n"] += 1
                wrec = corpus.words[wid]
                rec_harv = harvest_ok(dists, len(wrec["word"]), corpus.lex_by_len, agreement_bar,
                                      margin_threshold)
                if rec_harv is not None:
                    for pos, ch in enumerate(rec_harv["word"]):
                        key = f"{wid}:{pos}"
                        rec = corpus.char_by_key[key]
                        _pool_add(pool_by_wc, w, _lower26(ch), wid, rec["local_idx"],
                                 rec_harv["margin_per_char"])
    curve = []
    for k in sorted(by_pos):
        s = by_pos[k]
        curve.append({"position": k, "n_words": s["word_n"],
                     "char_acc": s["char_ok"] / s["char_n"] if s["char_n"] else 0.0,
                     "word_acc": s["word_ok"] / s["word_n"] if s["word_n"] else 0.0})
    return {"curve": curve, "n_order_seeds": n_order_seeds}


def compute_margin_threshold(corpus: BootstrapCorpus, pctl: float) -> float:
    """PRE-REGISTRATION step: the margin threshold is fixed from round-0's (empty-pool, pure
    cross-bank) SCORE distribution alone, BEFORE any accuracy number is computed."""
    margins = []
    for wid, wrec in corpus.words.items():
        dists = corpus.cross_dists(wid)
        m = decode_lexicon_margin(dists, len(wrec["word"]), corpus.lex_by_len)
        if m is not None and math.isfinite(m["margin_per_char"]):
            margins.append(m["margin_per_char"])
    if not margins:
        return 0.0
    return float(np.percentile(margins, pctl))


def cold_and_ceiling_reports(corpus: BootstrapCorpus) -> dict:
    """Round-0-equivalent (pure cross bank, empty pool -- IDENTICAL to `boot_dists` with an empty
    pool by construction) and the ceiling (real own bank), reported once, over the SAME word set."""
    def _report(dist_fn):
        char_ok = char_n = word_ok = word_n = 0
        flags = []
        for wid in corpus.words:
            dists = dist_fn(wid)
            c_ok, c_n, w_ok, _, _ = _char_acc_and_word_acc(corpus, wid, dists)
            char_ok += c_ok
            char_n += c_n
            word_ok += w_ok
            word_n += 1
            flags.append(bool(w_ok))
        return {"char_acc": char_ok / char_n, "word_acc": word_ok / word_n, "char_n": char_n,
               "word_n": word_n, "word_ok": word_ok, "flags": flags}
    return {"cold": _report(corpus.cross_dists), "ceiling": _report(corpus.ceiling_dists)}


# ============================================================================================= #
#  STAGE: bootstrap -- pure Python, no native calls needed (lookups into `read.json`'s tables).
# ============================================================================================= #
def stage_bootstrap():
    print(f"\n{SEP}\n  STAGE: bootstrap -- EM (leave-one-word-out) + streaming warm-up curve, pure "
          f"Python lookups\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("bootstrap")
    prep = _require("prep.json")
    rd = _require("read.json")
    if not rd.get("done"):
        raise SystemExit("WALL: read not COMPLETE -- re-invoke --stage read.")
    lexicon = _load(RUN61_LEXICON)
    lex_by_len = r61._lex_by_len(lexicon["lexicon"])

    corpus = BootstrapCorpus(rd["chars"], rd["pairwise"], prep["word_records"], lex_by_len)
    print(f"  corpus: {len(corpus.words)} words, {len(corpus.writers())} writers, "
          f"{len(corpus.char_by_key)} chars  [{time.time()-t0:.1f}s]", flush=True)

    margin_thr = compute_margin_threshold(corpus, MARGIN_PCTL_PRIMARY)
    margin_thr_robust = {p: compute_margin_threshold(corpus, p) for p in MARGIN_PCTL_ROBUST}
    print(f"  PRIMARY margin threshold (median of round-0 finite margins) = {margin_thr:.4f}  "
          f"(robustness: {margin_thr_robust})", flush=True)

    cc = cold_and_ceiling_reports(corpus)
    print(f"  COLD  (round-0-equivalent): char={100*cc['cold']['char_acc']:.1f}% "
          f"word={100*cc['cold']['word_acc']:.1f}%  (n={cc['cold']['word_n']})", flush=True)
    print(f"  CEILING (real own bank, cheating ref): char={100*cc['ceiling']['char_acc']:.1f}% "
          f"word={100*cc['ceiling']['word_acc']:.1f}%  (n={cc['ceiling']['word_n']})", flush=True)

    em_primary = run_em(corpus, AGREEMENT_PRIMARY, margin_thr)
    print(f"  EM (primary rule) converged at round {em_primary['converged_at']} "
          f"(hit_max_rounds={em_primary['hit_max_rounds']})  [{time.time()-t0:.1f}s]", flush=True)
    for rr in em_primary["rounds"]:
        print(f"    round {rr['round']}: char={100*rr['char_acc']:.1f}% word={100*rr['word_acc']:.1f}% "
              f"new_harvested_chars={rr['n_new_harvested_chars']} "
              f"harvest_precision={rr['harvest_precision']} "
              f"pool_coverage={rr['pool_coverage_writer_class']}", flush=True)

    # robustness variants (not cherry-picked -- reported alongside primary).
    em_robust = {}
    em_robust["agree0.8"] = run_em(corpus, AGREEMENT_ROBUST, margin_thr)
    for p, thr in margin_thr_robust.items():
        em_robust[f"pctl{p}"] = run_em(corpus, AGREEMENT_PRIMARY, thr)
    print(f"  robustness EM variants computed  [{time.time()-t0:.1f}s]", flush=True)

    warmup = run_streaming(corpus, AGREEMENT_PRIMARY, margin_thr)
    print(f"  warm-up streaming curve computed ({len(warmup['curve'])} positions, "
          f"{N_ORDER_SEEDS} order seeds)  [{time.time()-t0:.1f}s]", flush=True)
    for row in warmup["curve"][:12]:
        print(f"    pos {row['position']:>3}: n={row['n_words']:>4}  char={100*row['char_acc']:.1f}%"
              f"  word={100*row['word_acc']:.1f}%", flush=True)

    out = {
        "margin_threshold_primary": margin_thr, "margin_threshold_robust": margin_thr_robust,
        "cold": cc["cold"], "ceiling": cc["ceiling"],
        "em_primary": em_primary, "em_robust": em_robust, "warmup": warmup,
        "n_words": len(corpus.words), "n_writers": len(corpus.writers()),
    }
    # flags are per-word bools -- keep for McNemar in summary, drop nothing here.
    _save(out, _ckpt("bootstrap.json"))
    _seed_guard("bootstrap", md5_before)
    print(f"  saved -> {_ckpt('bootstrap.json')}  [{time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: summary -- the WARM-UP CURVE + does-bootstrapping-close-the-gap VERDICT.
# ============================================================================================= #
def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 73 SCOREBOARD (BOOTSTRAPPED WRITER ADAPTATION)\n{SEP}",
          flush=True)
    md5_now = _seed_guard("summary")
    prep = _require("prep.json")
    print(f"  SEED-GUARD: seeds/stroke_shapes.json md5 = {md5_now}  "
          f"(== prep capture {prep['stroke_shapes_md5']}: "
          f"{md5_now == prep['stroke_shapes_md5']})")
    boot = _require("bootstrap.json")
    n_words, n_writers = boot["n_words"], boot["n_writers"]
    print(f"\n  n test words = {n_words}  n writers = {n_writers}")
    print(f"  calibration -- run 69 isolated char: within {RUN69_WITHIN_CHAR:.1f}% cross "
          f"{RUN69_CROSS_CHAR:.1f}%  |  run 70 within-writer word (given bank): "
          f"{RUN70_WITHIN_WORD:.1f}%  cross-writer word: {RUN70_CROSS_WORD:.1f}%  |  BAP within "
          f"{BAP_WITHIN:.1f}% cross {BAP_CROSS:.1f}%")

    cold, ceiling = boot["cold"], boot["ceiling"]
    rounds = boot["em_primary"]["rounds"]
    final = rounds[-1]
    print(f"\n  === THE WARM-UP CURVE (EM rounds, leave-one-word-out) ===")
    hdr = f"  {'round':>6}{'char_acc':>10}{'word_acc':>10}{'new_pseudo_chars':>18}" \
          f"{'harvest_prec':>14}{'pool_cov':>10}"
    print(hdr)
    for rr in rounds:
        hp = f"{100*rr['harvest_precision']:.1f}%" if rr["harvest_precision"] is not None else "n/a"
        print(f"  {rr['round']:>6}{100*rr['char_acc']:>9.1f}%{100*rr['word_acc']:>9.1f}%"
              f"{rr['n_new_harvested_chars']:>18}{hp:>14}{rr['pool_coverage_writer_class']:>10}")
    print(f"\n  COLD (round-0-equivalent, cross bank only): char={100*cold['char_acc']:.1f}% "
          f"word={100*cold['word_acc']:.1f}%")
    print(f"  CONVERGED (round {final['round']}, bootstrapped bank): char={100*final['char_acc']:.1f}% "
          f"word={100*final['word_acc']:.1f}%")
    print(f"  CEILING (real own bank, never fed to decode): char={100*ceiling['char_acc']:.1f}% "
          f"word={100*ceiling['word_acc']:.1f}%")

    def _gap_close(cold_v, final_v, ceil_v):
        span = ceil_v - cold_v
        return (final_v - cold_v) / span if span > 1e-9 else float("nan")

    gap_char = _gap_close(cold["char_acc"], final["char_acc"], ceiling["char_acc"])
    gap_word = _gap_close(cold["word_acc"], final["word_acc"], ceiling["word_acc"])
    print(f"\n  GAP CLOSED (char): {100*gap_char:.1f}%   GAP CLOSED (word): {100*gap_word:.1f}%   "
          f"(bar: >= {100*GAP_CLOSE_BAR:.0f}%)")

    ci_cold = _wilson(cold["word_ok"], cold["word_n"])
    ci_final = _wilson(final["word_ok"], final["word_n"])
    sep_above_cold = ci_final[0] > cold["word_acc"]
    win = (gap_word >= GAP_CLOSE_BAR) and sep_above_cold
    print(f"\n  MILESTONE (pre-registered: converged word acc closes >= {100*GAP_CLOSE_BAR:.0f}% of "
          f"the cold->ceiling gap AND is CI-separated above cold):")
    print(f"    cold word_acc   = {100*cold['word_acc']:.1f}%  CI=[{100*ci_cold[0]:.1f},"
          f"{100*ci_cold[1]:.1f}]")
    print(f"    converged word_acc = {100*final['word_acc']:.1f}%  CI=[{100*ci_final[0]:.1f},"
          f"{100*ci_final[1]:.1f}]  (CI-separated above cold? {sep_above_cold})")
    print(f"    ceiling word_acc = {100*ceiling['word_acc']:.1f}%")
    print(f"    VERDICT: {'WIN -- self-supervised bootstrap materially lifts unknown-writer reading toward the given-bank ceiling' if win else 'NULL -- bootstrap does not materially/robustly lift unknown-writer reading'}")

    # -- drift check --
    precisions = [rr["harvest_precision"] for rr in rounds if rr["harvest_precision"] is not None]
    drift = len(precisions) >= 2 and precisions[-1] < precisions[0] - 0.10
    print(f"\n  DRIFT CHECK: per-round harvested-pseudo-label precision = "
          f"{[f'{100*p:.1f}%' for p in precisions]}")
    print(f"    DRIFT DETECTED (final round precision fell >10pp below round-0)? {drift}")

    # -- robustness variants --
    print(f"\n  ROBUSTNESS (not cherry-picked -- alternate agreement/margin bars):")
    for label, em in boot["em_robust"].items():
        rf = em["rounds"][-1]
        gw = _gap_close(cold["word_acc"], rf["word_acc"], ceiling["word_acc"])
        print(f"    {label:<10} converged round {rf['round']}: char={100*rf['char_acc']:.1f}% "
              f"word={100*rf['word_acc']:.1f}%  gap_closed(word)={100*gw:.1f}%")

    # -- warm-up curve headline --
    curve = boot["warmup"]["curve"]
    print(f"\n  WARM-UP CURVE headline (streaming, causal, {boot['warmup']['n_order_seeds']} order "
          f"seeds averaged):")
    hdr2 = f"  {'position':>9}{'n_words':>9}{'char_acc':>10}{'word_acc':>10}"
    print(hdr2)
    for row in curve:
        print(f"  {row['position']:>9}{row['n_words']:>9}{100*row['char_acc']:>9.1f}%"
              f"{100*row['word_acc']:>9.1f}%")
    first5 = [r for r in curve if r["position"] < 5]
    last5 = [r for r in curve if r["position"] >= max(0, len(curve) - 5)]
    if first5 and last5:
        early_char = np.mean([r["char_acc"] for r in first5])
        late_char = np.mean([r["char_acc"] for r in last5])
        print(f"\n  early (first {len(first5)} positions) char_acc = {100*early_char:.1f}%   "
              f"late (last {len(last5)} positions) char_acc = {100*late_char:.1f}%   "
              f"lift = {100*(late_char-early_char):+.1f}pp")

    print(f"\n  ANOMALIES / HONEST RESIDUALS:")
    print(f"    given char+word segmentation: measures the reading/bootstrap stack, not "
          f"segmentation discovery.")
    print(f"    words/writer distribution: {sorted(Counter(prep['words_per_writer']).items())[:5]} "
          f"... (min {MIN_WORDS_PER_WRITER}, cap {CAP_WORDS_PER_WRITER})")
    print(f"    real-own-bank (ceiling ref) empty (writer,class) cells: "
          f"{sum(1 for cov in prep['real_own_bank_coverage'].values() for c, n in cov.items() if n == 0)}"
          f" / {prep['n_test_writers'] * len(LOWER_CLASSES)}")
    print(f"    pool coverage at convergence: {final['pool_coverage_writer_class']} / "
          f"{prep['n_test_writers'] * len(LOWER_CLASSES)} (writer,class) cells -- bootstrap can "
          f"never exceed what confident harvests actually cover.")

    _save({"cold": cold, "ceiling": ceiling, "final_round": final,
          "gap_closed_char": gap_char, "gap_closed_word": gap_word, "win": win, "drift": drift,
          "margin_threshold_primary": boot["margin_threshold_primary"]}, _ckpt("summary.json"))
    _seed_guard("summary", md5_now)
    print(f"\n  saved -> {_ckpt('summary.json')}")
    print(f"\n{SEP}\n  RUN 73 COMPLETE -- see final agent report.\n{SEP}", flush=True)
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True, choices=["prep", "read", "bootstrap", "summary"])
    args = p.parse_args()
    return {"prep": stage_prep, "read": stage_read, "bootstrap": stage_bootstrap,
            "summary": stage_summary}[args.stage]()


if __name__ == "__main__":
    sys.exit(main())
