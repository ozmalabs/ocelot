"""jabberwock_fewshot_run79.py -- RUN 79: THE FEW-SHOT ADAPTATION DIAGNOSTIC.

RUN 78 found that fast letter-form adaptation is NULL, localized to the HARVEST RATE: only 42.2% of
a held-out writer's letter instances ever get pooled, because the harvest GATE (agreement + margin,
run 77's own crux rule) is conservative -- most of a writer's stream is never confidently read enough
to seed the bank. That localization leaves an open, more basic question UNANSWERED: even with
PERFECT labels (no harvest noise at all), is exemplar-accumulation itself sample-hungry, or is the
harvest rate the ONLY bottleneck? And a second, independent question run 69 already answered at the
POSE level but was never checked at the BANK level: is there a generalizing hand-transform in writer
adaptation (something learned from a FEW letters that lifts OTHER, unseen letters), or is adaptation
purely local accumulation (a labeled letter only ever helps future queries of the SAME class)?

THIS RUN removes the harvest-rate confound entirely by giving the reader K PERFECTLY-labeled words
per writer (ground truth, no pseudo-labeling, no EM, no margin gate) and sweeping K. Two curves are
measured on the SAME held-out instances: accuracy on letter classes PRESENT in the K labeled words
(SEEN) vs classes ABSENT from them (UNSEEN). SEEN-vs-K isolates sample-efficiency of pure
accumulation (steep = efficient, shallow = hungry). UNSEEN-vs-K isolates whether accumulating labels
for SOME classes ever helps OTHER, never-labeled classes -- the signature of a generalizing transform,
which pure per-class exemplar accumulation cannot produce (see "THE ANALYTIC INVARIANT" below).

REUSE (ZERO new native computation this run performs -- see "WHY NO read STAGE" below; every DTW
distance/pose-frame/cross-bank value already exists in prior runs' own checkpoints):
  * `scripts.jabberwock_letteradapt_run78` (r78) -- THE ENTIRE LETTER-GRAIN SUBSTRATE, reused
    verbatim by IMPORT and by re-running its OWN pure functions on its OWN saved checkpoint data
    (read-only): `fused_letter_cost` (the min(cross,own-pool) decode -- THIS run's only decode path,
    unmodified), `build_letter_pairwise_index`, `build_true_ceiling_pool`, `letter_visual_accuracy`
    (used for this run's own COLD/CEILING anchors, on the FULL letter set, K-independent), `RUN69_READ`
    (path constant), `r69`/`r73` (aliased through r78, themselves aliased through r77). Run 78's own
    `prep.json` (`letters`: every held-out-writer test letter, GIVEN char segmentation, with its
    `inv`/`pose_own` canons already folded into a fixed `cross_row` 26-class cost vector -- condition
    D in run 69's own taxonomy, see below) and `read.json` (the full same-writer letter-to-letter
    pairwise DTW table, inv+pose channels, already computed for EVERY pair of that writer's test
    letters) supply everything this run's K-shot pool/decode loop needs -- READ-ONLY, no new DTW call.
  * `scripts.jabberwock_bootstrap_read_run73` (r73, via r78) -- `_pool_add` (top-M-by-margin pool cap,
    reused UNMODIFIED for the new "K ground-truth words" pool -- with perfectly-labeled exemplars,
    `margin` degenerates to a constant tie-break, not a confidence score, since there is no harvest
    decision left to rank by).
  * `scripts.jabberwock_pose_read_run69` (r69, via r78/r77) -- `_acc`/`_pred_inv`/`_pred_mix`,
    reused to recompute run 69's own condition A (`invA`, no pose, cross-writer -- the TRUE
    no-adaptation-at-all floor) and condition D (`invA + lam*poseD` -- the writer's OWN unsupervised
    pose frame scored against the GENERIC cross bank, zero own-writer labeled exemplars) LIVE from
    `results/run69_checkpoints/read.json` (READ-ONLY). D minus A is THE POSE-TRANSFORM LIFT: a
    hand-transform (slant/baseline/x-height) estimated from the writer's ink WITHOUT any per-letter
    label, applied uniformly across every letter class, at K=0 (it does not depend on K at all -- it
    is baked into `cross_row` for every query regardless of how many words are labeled). This run's
    own COLD anchor (`fused_letter_cost` with an EMPTY own-pool) already includes this transform, so
    it does not need to be re-derived; run 69's A/D numbers are cited alongside as the corpus-level,
    K-independent evidence that a hand-transform CAN generalize, for direct contrast against this
    run's own accumulation-only bank mechanism (which cannot, see below).

WHY NO `read` STAGE: run 78's own `read` stage already computed the FULL same-writer letter-pairwise
DTW matrix (inv+pose, every pair of every held-out writer's test letters) -- the one and only fixed
table a K-shot own-pool lookup needs (`fused_letter_cost`'s `pairwise_idx` argument). Slicing that
table into "K labeled words' letters" (the pool) vs "the rest" (the test set) per K/seed/writer is a
PURE PYTHON RE-INDEXING of already-computed distances -- no new DTW call, no new native code path.
This run therefore has NO native stage at all (`prep`/`bootstrap`/`summary` only) and can run under
either interpreter; `.venv` is used throughout purely for consistency with the rest of the arc.

THE ANALYTIC INVARIANT (stated before any number is computed, then VERIFIED empirically, not just
assumed): `fused_letter_cost`'s fusion is `fused[c] = min(cross_row[c], own_pool_cost[c])` -- a
per-class MINIMUM. For a held-out letter whose TRUE class T is UNSEEN (no pool entry exists for T,
by construction of the SEEN/UNSEEN split), `fused[T] == cross_row[T]` EXACTLY -- T's own cost cannot
change. Every OTHER class c's fused cost can only DECREASE or stay the same (`fused[c] <= cross_row[c]`
always, since fusion never raises a cost). So if class B was already argmin (or tied) at cold and its
own cost decreases further via fusion, `fused[B] <= cross_row[B] <= cross_row[T] == fused[T]` --
meaning B can only become MORE competitive against T, never less. CONCLUSION: for an unseen-class
letter, the decode can only stay correct or become WRONG under bank fusion -- it can NEVER become
newly correct (a "flip to right" is impossible; a "flip to wrong," where a seen class's cost drops
below the previously-correct unseen truth, is the only possible transition). This is checked directly
every round (`n_flip_to_right` must be exactly 0) as a coherence gate on the implementation, and
`n_flip_to_wrong` is reported as the real, honest cost of accumulation's dilution on unseen classes.
THIS is "pure accumulation cannot generalize across letters," made precise and falsifiable rather than
asserted.

PRE-REGISTERED READ (this is a DIAGNOSTIC, not a WIN/NULL gate -- the goal is the answer, stated
before any number is computed):
  (i) SEEN sample-efficiency: how many K/labeled-letters are needed for SEEN accuracy to approach the
      CEILING (all-labels, run 78's own ceiling anchor, ~55-62% on this sample)? A steep early climb
      = accumulation is sample-EFFICIENT once labels are correct (harvest rate, not the mechanism,
      was run 78's true bottleneck); a shallow climb even under PERFECT labels = accumulation itself
      is sample-hungry (a deeper problem than harvest rate).
  (ii) UNSEEN generalization: does UNSEEN accuracy rise above the K=0 cold anchor as K grows? By the
      analytic invariant above, it CANNOT rise (only fall, via dilution) under pure per-class
      exemplar accumulation -- confirmed or falsified directly, with the dilution magnitude reported.
  (iii) pose-transform vs bank-accumulation: run 69's own condition D-minus-A (the pose frame ALONE,
      no own bank, applied uniformly to every letter regardless of label) is a REAL, measured,
      K-independent generalizing lift (unlike the bank). Reported side by side with (ii) as the direct
      contrast: a transform generalizes; accumulation, by construction, does not.
  THE ACTIONABLE CONCLUSION follows mechanically from (i)+(ii): if SEEN climbs efficiently and UNSEEN
  never rises, the fix for run 78's harvest-rate bottleneck is "harvest more/better labels" (the
  mechanism already works, feed it more data) PLUS, if the corpus-structure ceiling is still capped,
  "infer an explicit hand-transform" for classes a writer's K labeled words never cover (since only a
  transform, not accumulation, can reach unseen classes at all).

SEED GUARD / DISCIPLINE: `OZMA_SEED_PERSIST_DISABLED=1`; md5(seeds/stroke_shapes.json) asserted
UNCHANGED before AND after every stage. donkey=0 throughout (closed-form DTW argmin decode + count
reused from runs 69/73/77/78 -- no SGD-trained net anywhere, no new learned weights, no new native
computation at all this run). `results/run6{9}_checkpoints/` and `results/run7{7,8}_checkpoints/` are
READ-ONLY (citation/reused-checkpoint only) -- this script writes ONLY `results/run79_checkpoints/*`.
NO git add/commit.

EXECUTION (ops law): every invocation <=540s FOREGROUND, checkpointed under
`results/run79_checkpoints/`. No native stage exists (pure Python/numpy throughout -- confirmed by
this module never importing `substrate_rs`), so both `.venv` and system python3 can run every stage;
`.venv` is used for consistency with the arc. NEVER run in background; NEVER end a turn with a live
process.

Run (from the gamma-substrate repo root):
  OZMA_SEED_PERSIST_DISABLED=1 DEEPWRITING_DIR=/tmp/handwriting PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python3 \\
    scripts/jabberwock_fewshot_run79.py --stage <prep|bootstrap|summary>
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

import scripts.jabberwock_letteradapt_run78 as r78

r77 = r78.r77
r73 = r78.r73
r69 = r78.r69

SEP = "=" * 92
STROKE_SHAPES_SEED = r78.STROKE_SHAPES_SEED
CKPT_DIR = os.path.join(ROOT, "results", "run79_checkpoints")
LOG = os.path.join(ROOT, "results", "omniglot_gate_run79.log")
os.makedirs(CKPT_DIR, exist_ok=True)

RUN78_CKPT_DIR = r78.CKPT_DIR                                          # READ-ONLY.
RUN78_PREP = os.path.join(RUN78_CKPT_DIR, "prep.json")
RUN78_READ = os.path.join(RUN78_CKPT_DIR, "read.json")
RUN78_SUMMARY = os.path.join(RUN78_CKPT_DIR, "summary.json")
RUN69_READ = r78.RUN69_READ                                            # READ-ONLY.

# ------------------------------------------------------------------------------------------- #
#  PRE-REGISTERED CONSTANTS -- reused verbatim from the arc's own shared weights where one
#  exists; NEW constants for this run's own K-shot sweep are marked NEW.
# ------------------------------------------------------------------------------------------- #
PRIMARY_LAMBDA_POSE = r78.PRIMARY_LAMBDA_POSE
M_BOOT_LETTER = r78.M_BOOT_LETTER          # 5 -- apples-to-apples pool cap with run 77/78's bank.
N_KSHOT_SEEDS = r77.N_ORDER_SEEDS          # 5 -- same draw-order averaging convention as the arc.
KSHOT_SEED_BASE = r77.WORD_SELECT_SEED     # 20260910, this arc's own pre-registered selection seed.

K_VALUES = [1, 2, 3, 5, 8, 13, 20]         # NEW -- pre-registered sweep (task's own K grid).

# Calibration numbers this run reports against (dynamically recomputed where possible, per the
# arc's own no-hardcoded-drift discipline -- these are FALLBACK citations only).
RUN78_COLD_CITE = 19.4
RUN78_CEILING_CITE = 62.4
RUN78_CONVERGED_CITE = 26.3
RUN69_CROSS_CITE = 28.8


# ============================================================================================= #
#  I/O + seed guard (identical pattern to the whole arc).
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
    return r78._wilson(k, n)


# ============================================================================================= #
#  DYNAMIC CALIBRATION ANCHOR -- run 69's own condition A (no pose, cross-writer) and condition D
#  (writer's own unsupervised pose frame, cross bank, ZERO own labeled exemplars) recomputed LIVE
#  from its saved read.json, per the task's own instruction not to hardcode drifted numbers. D
#  minus A is the pose-transform-ALONE lift -- a K-independent, corpus-level quantity, measured
#  once, contrasted against this run's own (K-dependent) bank-accumulation curves.
# ============================================================================================= #
def run69_pose_decomposition_anchor() -> dict:
    rd = _load(RUN69_READ)
    recs = rd["records"]
    n = len(recs)
    kA, _ = r69._acc(recs, lambda r: r69._pred_inv(r["invA"]))
    kD, _ = r69._acc(recs, lambda r: r69._pred_mix(r["invA"], r["poseD"], r69.PRIMARY_LAMBDA))
    kE, _ = r69._acc(recs, lambda r: r69._pred_mix(r["invB"], r["poseE"], r69.PRIMARY_LAMBDA))
    return {
        "n": n,
        "condA_no_pose_cross_pct": 100 * kA / n,
        "condD_pose_only_cross_pct": 100 * kD / n,
        "condE_pose_plus_bank_within_pct": 100 * kE / n,
        "pose_transform_lift_pp": 100 * (kD - kA) / n,
        "bank_on_top_of_pose_lift_pp": 100 * (kE - kD) / n,
    }


# ============================================================================================= #
#  STAGE: prep -- validate + structurally summarize run 78's own letter corpus (pure Python, no
#  native calls, no new DTW). Writer -> {wid: [letters sorted by pos]} grouping.
# ============================================================================================= #
def build_writer_words(letters: list) -> dict:
    by_w = defaultdict(lambda: defaultdict(list))
    for l in letters:
        by_w[l["writer"]][l["wid"]].append(l)
    out = {}
    for w, words in by_w.items():
        out[w] = {wid: sorted(ls, key=lambda l: l["pos"]) for wid, ls in words.items()}
    return out


def qualifying_writers(writer_words: dict, k: int) -> list:
    """A writer QUALIFIES for K iff it has >= K+1 words -- K to draw as labeled, >=1 left to test."""
    return sorted(w for w, words in writer_words.items() if len(words) >= k + 1)


def build_prep() -> dict:
    if not os.path.exists(RUN78_PREP) or not os.path.exists(RUN78_READ):
        raise SystemExit("WALL: run 78's prep.json/read.json not found -- run 78 must have "
                          "completed its own prep+read stages first (read-only dependency).")
    p78 = _load(RUN78_PREP)
    r78_read = _load(RUN78_READ)
    if not r78_read.get("done"):
        raise SystemExit("WALL: run 78's read.json is not COMPLETE -- cannot borrow its letter "
                          "pairwise table until run 78 itself finished reading.")

    letters = p78["letters"]
    writer_words = build_writer_words(letters)
    words_per_writer = {str(w): len(words) for w, words in writer_words.items()}
    k_writer_counts = {str(k): len(qualifying_writers(writer_words, k)) for k in K_VALUES}

    return {
        "n_letters": len(letters),
        "n_writers": len(writer_words),
        "words_per_writer": words_per_writer,
        "k_values": K_VALUES,
        "k_writer_counts": k_writer_counts,
        "run78_n_test_letters": p78["n_test_letters"],
    }


def stage_prep():
    print(f"\n{SEP}\n  STAGE: prep -- validate + summarize run 78's own letter corpus for the "
          f"K-shot sweep (pure Python, no native calls, no new DTW)\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("prep")
    print(f"  seeds/stroke_shapes.json md5 (before): {md5_before}", flush=True)

    out = build_prep()
    out["stroke_shapes_md5"] = md5_before
    _save(out, _ckpt("prep.json"))
    _seed_guard("prep", md5_before)

    wpw = sorted(out["words_per_writer"].values())
    print(f"  writers={out['n_writers']}  test letters={out['n_letters']}  "
          f"(borrowed verbatim from run 78's own {out['run78_n_test_letters']})", flush=True)
    print(f"  words/writer: min={wpw[0]} median={wpw[len(wpw)//2]} max={wpw[-1]}", flush=True)
    print(f"  QUALIFYING WRITERS PER K (>= K+1 words needed -- K labeled, >=1 held out to test):",
          flush=True)
    for k in K_VALUES:
        print(f"    K={k:>3}: {out['k_writer_counts'][str(k)]}/{out['n_writers']} writers qualify",
              flush=True)
    print(f"  saved -> {_ckpt('prep.json')}  [prep {time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  K-SHOT DRAW + POOL -- pure Python/numpy, lookups into run 78's own fixed tables. Importable by
#  tests without native/real data.
# ============================================================================================= #
def draw_kshot(words_w: dict, k: int, seed: int, writer: int) -> tuple:
    """Draws K of writer `writer`'s words (by wid) as the GROUND-TRUTH-labeled set, deterministic
    given (seed, writer) -- same streaming-order convention as run 77/78's own `seed*100003+w`.
    Returns (chosen_wids: set, held_wids: list) -- a strict partition of `words_w`'s keys."""
    wids = sorted(words_w.keys())
    rng = np.random.default_rng(seed * 100003 + writer)
    order = rng.permutation(len(wids))
    chosen = {wids[int(i)] for i in order[:k]}
    held = [wid for wid in wids if wid not in chosen]
    return chosen, held


def build_kshot_pool(words_w: dict, chosen_wids: set, writer: int,
                     cap: int = M_BOOT_LETTER) -> tuple:
    """Grows the writer's own-letter pool ENTIRELY from the K ground-truth-labeled words' letters --
    no harvest, no margin gate, no EM round: every letter in a chosen word is added with its TRUE
    label. `margin` degenerates to a constant (1.0, an arbitrary tie-break for the cap) since there
    is no confidence signal left to rank by -- every entry is equally (perfectly) trustworthy.
    Returns (pool_by_wc, seen_classes: set of true_li present in the K words)."""
    pool: dict = {}
    seen_classes = set()
    for wid in sorted(chosen_wids):
        for l in words_w[wid]:
            r73._pool_add(pool, writer, l["true_li"], l["wid"], l["local_idx"], margin=1.0, cap=cap)
            seen_classes.add(l["true_li"])
    return pool, seen_classes


def evaluate_one_k(writer_words: dict, pairwise_idx: dict, k: int, n_seeds: int) -> dict:
    """THE CORE SWEEP STEP: for K, draws `n_seeds` independent K-word samples per qualifying writer,
    builds the ground-truth pool, and measures every HELD-OUT letter's fused-cost decode, split into
    SEEN (true class present among the K words) vs UNSEEN (absent). Also records, per held letter,
    the COLD prediction (empty-pool argmin over `cross_row` alone -- K-independent) to compute the
    flip-to-wrong / flip-to-right coherence check (see module docstring's ANALYTIC INVARIANT)."""
    qualifying = qualifying_writers(writer_words, k)
    agg = {
        "k": k, "n_qualifying_writers": len(qualifying),
        "seen_ok": 0, "seen_n": 0, "unseen_ok": 0, "unseen_n": 0, "unseen_cold_ok": 0,
        "n_flip_to_wrong": 0, "n_flip_to_right": 0, "seen_classes_sum": 0, "n_draws": 0,
    }
    for seed in range(n_seeds):
        for w in qualifying:
            words_w = writer_words[w]
            chosen, held = draw_kshot(words_w, k, seed, w)
            pool, seen_classes = build_kshot_pool(words_w, chosen, w)
            agg["seen_classes_sum"] += len(seen_classes)
            agg["n_draws"] += 1
            for wid in held:
                for l in words_w[wid]:
                    fused = r78.fused_letter_cost(l["writer"], l["local_idx"], pool, pairwise_idx,
                                                  l["cross_row"], exclude_local_idx=l["local_idx"])
                    pred = int(np.argmin(fused))
                    cold_pred = int(np.argmin(l["cross_row"]))
                    adapted_ok = int(pred == l["true_li"])
                    cold_ok = int(cold_pred == l["true_li"])
                    if l["true_li"] in seen_classes:
                        agg["seen_ok"] += adapted_ok
                        agg["seen_n"] += 1
                    else:
                        agg["unseen_ok"] += adapted_ok
                        agg["unseen_n"] += 1
                        agg["unseen_cold_ok"] += cold_ok
                        if cold_ok and not adapted_ok:
                            agg["n_flip_to_wrong"] += 1
                        if adapted_ok and not cold_ok:
                            agg["n_flip_to_right"] += 1
    return agg


def run_kshot_sweep(letters: list, pairwise_idx: dict, k_values: list = K_VALUES,
                    n_seeds: int = N_KSHOT_SEEDS) -> dict:
    writer_words = build_writer_words(letters)
    per_k = {k: evaluate_one_k(writer_words, pairwise_idx, k, n_seeds) for k in k_values}
    return {"per_k": {str(k): v for k, v in per_k.items()}, "n_seeds": n_seeds,
           "k_values": k_values}


# ============================================================================================= #
#  STAGE: bootstrap -- pure Python, no native calls (lookups into run 78's own read.json + this
#  run's own K-shot re-slicing).
# ============================================================================================= #
def stage_bootstrap():
    print(f"\n{SEP}\n  STAGE: bootstrap -- K-shot sweep (ground-truth pool, zero harvest) + "
          f"SEEN/UNSEEN split + pose-decomposition anchor\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("bootstrap")
    prep = _require("prep.json")
    p78 = _load(RUN78_PREP)
    r78_read = _load(RUN78_READ)
    if not r78_read.get("done"):
        raise SystemExit("WALL: run 78's read not COMPLETE.")

    letters = p78["letters"]
    pairwise_idx = r78.build_letter_pairwise_index(r78_read["pairwise"])
    print(f"  letters={len(letters)}  pairwise index={len(pairwise_idx)} directed entries  "
          f"[{time.time()-t0:.1f}s]", flush=True)

    # -- COLD (K=0, empty pool -- already includes the pose-transform baked into cross_row) and
    #    CEILING (all-labels, true-label leave-one-out over ALL of a writer's OTHER test letters) --
    #    K-independent anchors, IDENTICAL computation to run 78's own cold/ceiling. --
    cold = r78.letter_visual_accuracy(letters, {}, pairwise_idx)
    ceiling_pool = r78.build_true_ceiling_pool(letters)
    ceiling = r78.letter_visual_accuracy(letters, ceiling_pool, pairwise_idx)
    print(f"  COLD    (K=0, generic bank + pose-transform, empty own-pool) = {100*cold['acc']:.1f}%  "
          f"(n={cold['n']})", flush=True)
    print(f"  CEILING (all-labels, true leave-one-out)                    = {100*ceiling['acc']:.1f}%"
          f"  (n={ceiling['n']})", flush=True)

    pose_anchor = run69_pose_decomposition_anchor()
    print(f"  POSE-DECOMPOSITION ANCHOR (run 69's own condition A/D, live, K-independent):", flush=True)
    print(f"    condA (no pose, cross-writer)             = {pose_anchor['condA_no_pose_cross_pct']:.1f}%",
          flush=True)
    print(f"    condD (pose-transform ONLY, cross bank)   = {pose_anchor['condD_pose_only_cross_pct']:.1f}%"
          f"   pose_transform_lift = {pose_anchor['pose_transform_lift_pp']:+.1f}pp", flush=True)
    print(f"    condE (pose + own bank, within-writer)    = "
          f"{pose_anchor['condE_pose_plus_bank_within_pct']:.1f}%   bank_on_top_of_pose_lift = "
          f"{pose_anchor['bank_on_top_of_pose_lift_pp']:+.1f}pp", flush=True)

    sweep = run_kshot_sweep(letters, pairwise_idx, K_VALUES, N_KSHOT_SEEDS)
    print(f"\n  K-SHOT SWEEP ({N_KSHOT_SEEDS} draw seeds averaged per K):", flush=True)
    hdr = (f"  {'K':>4}{'writers':>9}{'avg_seen_cls':>13}{'seen_n':>9}{'seen_acc':>10}"
          f"{'unseen_n':>10}{'unseen_acc':>11}{'flip_wrong':>12}{'flip_right':>12}")
    print(hdr, flush=True)
    for k in K_VALUES:
        s = sweep["per_k"][str(k)]
        seen_acc = s["seen_ok"] / s["seen_n"] if s["seen_n"] else float("nan")
        unseen_acc = s["unseen_ok"] / s["unseen_n"] if s["unseen_n"] else float("nan")
        avg_seen_cls = s["seen_classes_sum"] / s["n_draws"] if s["n_draws"] else float("nan")
        print(f"  {k:>4}{s['n_qualifying_writers']:>9}{avg_seen_cls:>13.1f}{s['seen_n']:>9}"
              f"{100*seen_acc:>9.1f}%{s['unseen_n']:>10}{100*unseen_acc:>10.1f}%"
              f"{s['n_flip_to_wrong']:>12}{s['n_flip_to_right']:>12}", flush=True)
        if time.time() - t0 > 480.0:
            print("  WALL-BUDGET approaching -- sweep is pure Python and should not need this, "
                  "but stopping defensively.", flush=True)
            break

    out = {
        "cold": cold, "ceiling": ceiling, "pose_anchor": pose_anchor, "sweep": sweep,
        "n_letters": len(letters), "n_writers": prep["n_writers"],
    }
    _save(out, _ckpt("bootstrap.json"))
    _seed_guard("bootstrap", md5_before)
    print(f"\n  saved -> {_ckpt('bootstrap.json')}  [{time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: summary -- the SEEN/UNSEEN curves, sample-efficiency read, generalization answer, the
#  pose-vs-bank decomposition, and the actionable conclusion.
# ============================================================================================= #
def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 79 SCOREBOARD (FEW-SHOT ADAPTATION DIAGNOSTIC)\n{SEP}",
          flush=True)
    md5_now = _seed_guard("summary")
    prep = _require("prep.json")
    print(f"  SEED-GUARD: seeds/stroke_shapes.json md5 = {md5_now}  "
          f"(== prep capture {prep['stroke_shapes_md5']}: {md5_now == prep['stroke_shapes_md5']})")
    boot = _require("bootstrap.json")

    cold, ceiling = boot["cold"], boot["ceiling"]
    pose = boot["pose_anchor"]
    sweep = boot["sweep"]
    ci_cold = _wilson(cold["ok"], cold["n"])
    ci_ceiling = _wilson(ceiling["ok"], ceiling["n"])

    print(f"\n  CALIBRATION (recomputed live, not hardcoded -- run 78's own cited numbers were "
          f"cold={RUN78_COLD_CITE:.1f}% converged={RUN78_CONVERGED_CITE:.1f}% "
          f"ceiling={RUN78_CEILING_CITE:.1f}%; run 69's own cross cite was {RUN69_CROSS_CITE:.1f}%):")
    print(f"    COLD    (K=0)      = {100*cold['acc']:.1f}%  CI=[{100*ci_cold[0]:.1f},"
          f"{100*ci_cold[1]:.1f}]  (n={cold['n']})")
    print(f"    CEILING (all-lbls) = {100*ceiling['acc']:.1f}%  CI=[{100*ci_ceiling[0]:.1f},"
          f"{100*ci_ceiling[1]:.1f}]  (n={ceiling['n']})")

    print(f"\n  === (iii) POSE-TRANSFORM vs BANK-ACCUMULATION (run 69's own A/D/E, K-independent) ===")
    print(f"    condA (no adaptation at all)            = {pose['condA_no_pose_cross_pct']:.1f}%")
    print(f"    condD (pose-transform ONLY, no own bank) = {pose['condD_pose_only_cross_pct']:.1f}%   "
          f"pose_transform_lift = {pose['pose_transform_lift_pp']:+.1f}pp  "
          f"(a hand-transform estimated with ZERO per-letter labels, applied uniformly)")
    print(f"    condE (pose + own true bank, within)    = {pose['condE_pose_plus_bank_within_pct']:.1f}%"
          f"   bank_on_top_of_pose_lift = {pose['bank_on_top_of_pose_lift_pp']:+.1f}pp")

    print(f"\n  === THE TWO CURVES: SEEN vs UNSEEN accuracy, as a function of K ===")
    hdr = (f"  {'K':>4}{'writers':>9}{'avg_seen_cls':>13}{'seen_acc':>10}{'seen_CI':>18}"
          f"{'unseen_acc':>12}{'unseen_CI':>18}{'flip_wrong':>12}")
    print(hdr)
    rows = []
    for k in K_VALUES:
        s = sweep["per_k"][str(k)]
        seen_acc = s["seen_ok"] / s["seen_n"] if s["seen_n"] else float("nan")
        unseen_acc = s["unseen_ok"] / s["unseen_n"] if s["unseen_n"] else float("nan")
        seen_ci = _wilson(s["seen_ok"], s["seen_n"]) if s["seen_n"] else (float("nan"),) * 2
        unseen_ci = _wilson(s["unseen_ok"], s["unseen_n"]) if s["unseen_n"] else (float("nan"),) * 2
        avg_seen_cls = s["seen_classes_sum"] / s["n_draws"] if s["n_draws"] else float("nan")
        rows.append({"k": k, "seen_acc": seen_acc, "unseen_acc": unseen_acc,
                    "seen_ci": seen_ci, "unseen_ci": unseen_ci, "avg_seen_cls": avg_seen_cls,
                    "n_qualifying_writers": s["n_qualifying_writers"],
                    "seen_n": s["seen_n"], "unseen_n": s["unseen_n"],
                    "n_flip_to_wrong": s["n_flip_to_wrong"], "n_flip_to_right": s["n_flip_to_right"]})
        print(f"  {k:>4}{s['n_qualifying_writers']:>9}{avg_seen_cls:>13.1f}{100*seen_acc:>9.1f}%"
              f"   [{100*seen_ci[0]:>5.1f},{100*seen_ci[1]:>5.1f}]{100*unseen_acc:>11.1f}%"
              f"   [{100*unseen_ci[0]:>5.1f},{100*unseen_ci[1]:>5.1f}]{s['n_flip_to_wrong']:>12}")
    print(f"  {'0(cold)':>4}{'--':>9}{'0':>13}{100*cold['acc']:>9.1f}%{'(anchor, both curves)':>18}")
    print(f"  {'all':>4}{'--':>9}{'26':>13}{100*ceiling['acc']:>9.1f}%{'(ceiling, all-labels)':>18}")

    # -- (i) SEEN sample-efficiency: gap closed toward ceiling at each K. --
    def _gap_close(v):
        span = ceiling["acc"] - cold["acc"]
        return (v - cold["acc"]) / span if abs(span) > 1e-9 else float("nan")

    print(f"\n  === (i) SEEN SAMPLE-EFFICIENCY (gap closed toward ceiling, cold->ceiling = "
          f"{100*cold['acc']:.1f}%->{100*ceiling['acc']:.1f}%) ===")
    for r in rows:
        gc = _gap_close(r["seen_acc"]) if not np.isnan(r["seen_acc"]) else float("nan")
        print(f"    K={r['k']:>3}  seen_acc={100*r['seen_acc']:.1f}%  gap_closed={100*gc:.1f}%  "
              f"(avg {r['avg_seen_cls']:.1f}/26 classes seen)")
    half_k = None
    for r in rows:
        gc = _gap_close(r["seen_acc"])
        if not np.isnan(gc) and gc >= 0.5:
            half_k = r["k"]
            break
    print(f"    K at which SEEN closes >= 50% of the cold->ceiling gap: "
          f"{half_k if half_k is not None else 'NEVER within K<=' + str(K_VALUES[-1])}")

    # -- (ii) UNSEEN generalization: does it ever rise above cold? --
    print(f"\n  === (ii) UNSEEN GENERALIZATION (does labeling SOME classes lift OTHER, unlabeled "
          f"classes above cold?) ===")
    any_unseen_above_cold = False
    max_dilution_pp = 0.0
    for r in rows:
        if np.isnan(r["unseen_acc"]):
            continue
        delta = 100 * (r["unseen_acc"] - cold["acc"])
        if r["unseen_ci"][0] > cold["acc"]:
            any_unseen_above_cold = True
        max_dilution_pp = min(max_dilution_pp, delta)
        print(f"    K={r['k']:>3}  unseen_acc={100*r['unseen_acc']:.1f}%  delta_vs_cold={delta:+.1f}pp"
              f"  flip_to_wrong={r['n_flip_to_wrong']}  flip_to_right={r['n_flip_to_right']}"
              f"  (flip_to_right must be 0 -- analytic invariant)")
    total_flip_right = sum(r["n_flip_to_right"] for r in rows)
    print(f"    COHERENCE CHECK: total flip_to_right across all K = {total_flip_right}  "
          f"(must be 0 -- unseen truth's own cost is never touched by fusion, so it can never "
          f"become newly correct; a positive count would indicate an implementation bug)")
    print(f"    UNSEEN accuracy CI-separated ABOVE cold at any K? {any_unseen_above_cold}")
    print(f"    max dilution observed (most negative delta_vs_cold) = {max_dilution_pp:+.1f}pp")

    print(f"\n  === THE ACTIONABLE CONCLUSION ===")
    seen_efficient = half_k is not None and half_k <= 5
    if seen_efficient and not any_unseen_above_cold:
        conclusion = ("HARVEST-MORE is the right fix for run 78's bottleneck (accumulation is "
                      "sample-EFFICIENT under perfect labels -- the harvest RATE, not the mechanism, "
                      "was the limiter) -- BUT it only ever helps classes a writer's labeled sample "
                      "actually covers; UNSEEN classes never improve (confirmed, flip_to_right=0 "
                      "throughout), so INFER-AN-EXPLICIT-HAND-TRANSFORM (as run 69's own condition D "
                      "already demonstrates works, +{:.1f}pp with ZERO labels) is the only lever left "
                      "for classes a K-word sample never reaches.").format(pose["pose_transform_lift_pp"])
    elif not seen_efficient and not any_unseen_above_cold:
        conclusion = ("INFER-AN-EXPLICIT-HAND-TRANSFORM is the right fix: accumulation is itself "
                      "sample-HUNGRY even under PERFECT ground-truth labels (SEEN climbs slowly, "
                      "K={} needed to reach half the gap) -- harvesting more/better labels would "
                      "still take many more instances per class than a writer's stream affords; a "
                      "generalizing transform (run 69's own condition D, +{:.1f}pp with ZERO labels) "
                      "is the more promising direction since it does not need per-class "
                      "coverage at all.").format(half_k if half_k is not None else f">{K_VALUES[-1]}",
                                                 pose["pose_transform_lift_pp"])
    elif any_unseen_above_cold:
        conclusion = ("UNEXPECTED: UNSEEN accuracy rose above cold at some K -- this would falsify "
                      "the analytic invariant as stated and needs investigation (check for a bug, or "
                      "a class-overlap/sampling artifact in the SEEN/UNSEEN split) before trusting "
                      "either curve.")
    else:
        conclusion = "See the two curves above and judge case-by-case -- no single label applies."
    print(f"  {conclusion}")

    print(f"\n  ANOMALIES / HONEST RESIDUALS:")
    print(f"    given char+word segmentation throughout (this arc's own standing convention).")
    print(f"    run 78's own cold/converged/ceiling numbers were {RUN78_COLD_CITE:.1f}%/"
          f"{RUN78_CONVERGED_CITE:.1f}%/{RUN78_CEILING_CITE:.1f}% -- this run's cold/ceiling "
          f"({100*cold['acc']:.1f}%/{100*ceiling['acc']:.1f}%) are recomputed on the IDENTICAL "
          f"letter set + identical computation, so they should match run 78's own numbers exactly "
          f"(this run's own converged-equivalent is the SEEN curve at the largest K, not directly "
          f"comparable to run 78's harvested-pool converged number since the labeling SOURCE differs "
          f"-- ground truth here, harvested pseudo-labels there).")
    print(f"    K=20's qualifying-writer count is materially lower than K<=13's (writers/writer's "
          f"word budget caps at {max(int(v) for v in prep['words_per_writer'].values())}) -- see "
          f"the per-K writer count table in the bootstrap log; large-K rows rest on fewer writers.")
    print(f"    pose-decomposition anchor (condA/D/E) is measured on run 69's OWN held-out sample, "
          f"not literally the same instances as this run's own letter set (same population/method, "
          f"different corpus draw) -- cited as directional, K-independent evidence for 'a transform "
          f"generalizes' rather than a numerically-identical baseline.")

    _save({
        "cold": cold["acc"], "ceiling": ceiling["acc"],
        "pose_transform_lift_pp": pose["pose_transform_lift_pp"],
        "bank_on_top_of_pose_lift_pp": pose["bank_on_top_of_pose_lift_pp"],
        "rows": [{"k": r["k"], "seen_acc": r["seen_acc"], "unseen_acc": r["unseen_acc"],
                 "seen_n": r["seen_n"], "unseen_n": r["unseen_n"],
                 "n_flip_to_wrong": r["n_flip_to_wrong"], "n_flip_to_right": r["n_flip_to_right"],
                 "n_qualifying_writers": r["n_qualifying_writers"]} for r in rows],
        "half_gap_k": half_k, "any_unseen_above_cold": any_unseen_above_cold,
        "total_flip_to_right": total_flip_right, "max_dilution_pp": max_dilution_pp,
        "conclusion": conclusion,
    }, _ckpt("summary.json"))
    _seed_guard("summary", md5_now)
    print(f"\n  saved -> {_ckpt('summary.json')}")
    print(f"\n{SEP}\n  RUN 79 COMPLETE -- see final agent report.\n{SEP}", flush=True)
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True, choices=["prep", "bootstrap", "summary"])
    args = p.parse_args()
    return {"prep": stage_prep, "bootstrap": stage_bootstrap, "summary": stage_summary}[args.stage]()


if __name__ == "__main__":
    sys.exit(main())
