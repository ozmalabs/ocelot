"""jabberwock_letteradapt_run78.py -- RUN 78: LOCALIZING RUN 77's FIX -- ADAPT LETTERS, NOT WORDS.

RUN 77 established two facts on the SAME held-out-writer stream: (i) the prediction-dominant
reader's CONFIDENT word reads are a reliable judge -- pooled harvest precision 77.6%
CI=[71.0,83.0] (n=62), far above run 73's 29% floor -- so trustworthy pseudo-labels DO exist; but
(ii) bootstrapping a WORD-FORM bank from them barely moved the needle (cold->ceiling word gap
closed only 14.3%) because DeepWriting's per-writer vocabulary is small: only 28.6% of a held-out
writer's test words are ever REPEATED by that same writer (`n_repeat_instances`/`n_test_words` in
`results/run77_checkpoints/prep.json`) -- a word-FORM bank can only help a word it has seen that
writer produce before, and most words are seen exactly once. Run 77's own diagnosis named the fix
directly: "a corpus-structure limit, not a mechanism failure."

RUN 78's bet: the SAME 77.6%-precision harvest, decomposed into its GIVEN constituent LETTERS
(every word uses several of only 26 possible classes), should give a FAR higher repeat-coverage
substrate than whole words do -- letters repeat within a writer's first half-dozen words, long
before most WORDS repeat. If harvested letter-labels are also reasonably precise, growing the
writer's PER-LETTER allograph bank (run 69's own machinery: `pose_canon`/`invariant_canon`/
`_class_cost`, decoupled inv+pose channels) should climb per-letter VISUAL (no-context) accuracy
from run 69's cross-writer floor (28.8%) toward its within-writer ceiling (55.0%) -- the 26.2pp
headroom run 69 itself measured and never closed with self-supervised adaptation.

REUSE (nothing rebuilt from scratch for the reader/harvest machinery -- only the LETTER-GRAIN pool
+ the two new per-letter native precompute/decode paths below are new):
  * `scripts.jabberwock_pose_read_run69` (r69) -- `_class_cost`/`invariant_canon`/`pose_canon`,
    `PRIMARY_LAMBDA` (=1.0), `LOWER_CLASSES`, `_pred_inv`/`_pred_mix`/`_acc` (used here ONLY to
    recompute run 69's own within/cross anchor numbers straight from its checkpoint files, per the
    task's own instruction to not hardcode drifted numbers), `BIG`.
  * `scripts.jabberwock_fastadapt_run77` (r77) -- THE ENTIRE WORD-LEVEL SUBSTRATE, reused verbatim
    by IMPORT and by re-running its OWN pure functions on its OWN saved checkpoint data (read-only):
    `FastAdaptCorpus`, `decode_one`, `harvest_ok` (THE crux harvest rule -- agreement + pre-
    registered round-0 margin percentile -- transplanted UNMODIFIED, not re-derived), `fuse_holistic`
    (the min(own,cross) fusion policy this run also applies at LETTER grain), `compute_margin_
    threshold`, `_acc_for`, `r73._pool_add` (the top-M-by-margin pool cap, reused for the NEW
    per-(writer,letter-class) pool exactly as it caps the per-(writer,word-label) one). Run 77's own
    `prep.json`/`read.json` (READ-ONLY) supply: the writer/word selection (30 held-out writers,
    15-25 in-vocab has-context words each, 693 words total), each word's GIVEN char segmentation
    (`chars`: per-position true symbol + invariant + writer-pose canons), the oracle sentence
    context, the fixed per-word cross-bank/per-char-cross-bank DTW tables, and the same-writer
    whole-WORD pairwise DTW matrix (unused here except for citation -- this run does not touch
    run 77's own word-form adaptation, it runs a SEPARATE letter-grain pool alongside it so the
    two questions never confound each other).
  * `scripts.jabberwock_sentence_read_run75` (r75) -- `topk_candidates` (the per-char LOOSE/bag
    visual route -- THIS run's ONLY word-decode route, see below), `build_lex_by_len`,
    `make_lm_scorer`, `LM_WEIGHT`, `PRIMARY_VISUAL_WEIGHT`, `BEAM_K`.
  * `scripts.jabberwock_iam_full_run76` (r76) -- `_normalize_visual` (per-position min-max
    normalization so one VISUAL_WEIGHT means the same thing regardless of which round's rows fed
    the candidate ranking).

THE ONE NEW REDUCTION, stated honestly: run 77's downstream word decode is DUAL-ROUTE (whole-word
holistic bank OR per-char loose fallback, whichever the word's length has coverage for) because
run 77 was adapting the WORD-FORM route itself. This run adapts the PER-CHAR route instead, so its
own downstream "word accuracy WITH context" number is measured with the whole-word holistic route
DISABLED (both `within_dict` and `cross_dict` passed empty to the candidate generator, forcing the
per-char LOOSE route unconditionally) -- otherwise a word whose length happens to have holistic
cross-bank coverage would never touch this run's own per-letter-adapted rows at all, and the
downstream number would silently measure nothing about this run's own lever. This is a deliberate,
stated isolation (in run 75/77's own tradition), not an accidental omission -- the per-letter VISUAL
number (computed independently, with NO word/context involvement whatsoever) is this run's real
headline; the context-aided word number is explicitly secondary/downstream, per the task's own
warning against letting oracle context mask the adaptation signal.

THE COLD / CEILING / BOOTSTRAPPED ladder (mirrors run 69's own A/E conditions and run 77's
cold/ceiling/bootstrapped shape, one grain finer -- LETTER instead of WORD-FORM):
  COLD (round 0)   = per-letter cost is the FIXED cross-bank cost alone (`char_cross_rows` from
        run 77's own read.json, i.e. r69's own `_class_cost` against the GENERIC cross bank,
        already computed, no new native calls needed for this arm at all) -- own-writer pool EMPTY.
  CEILING (never fed to decode, calibration only) = the writer's OWN TRUE-labeled OTHER letter
        instances (leave-one-out over ALL of that writer's test letters, not a capped random-M
        sample the way run 69's own bank was -- a STRONGER, freshly-computed ceiling on this run's
        own sample, reported alongside but not required to reproduce run 69's literal 55.0%).
  BOOTSTRAPPED (this run's contribution) = `fuse_holistic`-style min(cross, own-pool) where the
        own-pool is built ENTIRELY from letters DECOMPOSED out of confidently-harvested WORD reads
        (run 77's own harvest rule, replayed VERBATIM on run 77's own corpus/threshold so the set of
        harvested words is BYTE-IDENTICAL to run 77's actual run -- letter harvesting is a pure
        SIDE EFFECT of that same decision, never a separate/looser gate).

PRE-REGISTERED READ (stated before any number is computed):
  WIN if converged per-letter VISUAL (no-context) char accuracy closes >= 40% of the cold->ceiling
  gap (run 73/77's own bar, transplanted), CI-separated above cold (Wilson, matching run 69/77's own
  methodology), AND letter-coverage (structural repeat-rate, and actual harvested pool coverage)
  is materially higher than run 77's own 28.6% word-repeat coverage, ideally near-saturating within
  a handful of EM rounds.
  NULL otherwise -- localize to (a) per-letter harvest precision (decomposing a confident WORD read
  into letters may be noisier per-letter than the word-level number, checked directly and reported,
  not assumed equal to 77.6%), (b) fusion dilution (own-pool ever making the ARGMIN worse than
  cross-only for some class, checked directly -- the per-class-cost invariant "min can only lower a
  cost" does NOT by itself guarantee the argmin decode never flips to a newly-cheapened wrong
  class), or (c) bank non-responsiveness (too few own exemplars per class even after several
  rounds).

SEED GUARD / DISCIPLINE: `OZMA_SEED_PERSIST_DISABLED=1`; md5(seeds/stroke_shapes.json) asserted
UNCHANGED before AND after every stage. donkey=0 throughout (closed-form DTW/geometry + count-based
LM + EM harvest/threshold logic reused verbatim from runs 69/73/75/76/77 -- no SGD-trained net
anywhere, no new learned weights). `results/run6{1,9}_checkpoints/` and
`results/run7{5,7}_checkpoints/` are READ-ONLY (citation/reused-module/reused-checkpoint only) --
this script writes ONLY `results/run78_checkpoints/*`. NO git add/commit.

EXECUTION (ops law): every invocation <=540s FOREGROUND, checkpointed under
`results/run78_checkpoints/`, block-resumable. `.venv` python needed for `read` (native
`substrate_rs` DTW, the ONLY new native computation this run performs -- the same-writer
letter-to-letter pairwise DTW matrix, inv+pose channels); `prep`/`bootstrap`/`summary` are pure
Python (numpy only) and run under either interpreter (this run uses `.venv` throughout for
consistency with the rest of the arc). NEVER run in background; NEVER end a turn with a live
process.

Run (from the gamma-substrate repo root):
  OZMA_SEED_PERSIST_DISABLED=1 DEEPWRITING_DIR=/tmp/handwriting PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python3 \\
    scripts/jabberwock_letteradapt_run78.py --stage <prep|read|bootstrap|summary>
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

import scripts.jabberwock_fastadapt_run77 as r77

r69 = r77.r69
r70 = r77.r70
r61 = r77.r61
r73 = r77.r73
r74 = r77.r74
r75 = r77.r75
r76 = r77.r76
cc66 = r77.cc66

SEP = "=" * 92
STROKE_SHAPES_SEED = r77.STROKE_SHAPES_SEED
CKPT_DIR = os.path.join(ROOT, "results", "run78_checkpoints")
LOG = os.path.join(ROOT, "results", "omniglot_gate_run78.log")
os.makedirs(CKPT_DIR, exist_ok=True)

RUN77_CKPT_DIR = os.path.join(ROOT, "results", "run77_checkpoints")   # READ-ONLY.
RUN69_CKPT_DIR = os.path.join(ROOT, "results", "run69_checkpoints")   # READ-ONLY.
RUN77_PREP = os.path.join(RUN77_CKPT_DIR, "prep.json")
RUN77_READ = os.path.join(RUN77_CKPT_DIR, "read.json")
RUN77_SUMMARY = os.path.join(RUN77_CKPT_DIR, "summary.json")
RUN69_PREP = os.path.join(RUN69_CKPT_DIR, "prep.json")
RUN69_READ = os.path.join(RUN69_CKPT_DIR, "read.json")

# ------------------------------------------------------------------------------------------- #
#  PRE-REGISTERED CONSTANTS -- reused verbatim from the arc's own shared weights where one
#  exists; NEW constants for this run's own letter-grain pool are marked NEW.
# ------------------------------------------------------------------------------------------- #
PRIMARY_LAMBDA_POSE = r77.PRIMARY_LAMBDA_POSE      # 1.0, r69's own pre-registered pose weight.
LM_WEIGHT = r77.LM_WEIGHT
PRIMARY_VISUAL_WEIGHT = r77.PRIMARY_VISUAL_WEIGHT
BEAM_K = r77.BEAM_K
MAX_ROUNDS = r77.MAX_ROUNDS                        # 8 -- same round budget as run 77.
N_ORDER_SEEDS = r77.N_ORDER_SEEDS                  # 5 -- same streaming-order averaging as run 77.
MARGIN_PCTL_PRIMARY = r77.MARGIN_PCTL_PRIMARY
BIG = r69.BIG

M_BOOT_LETTER = 5              # NEW -- per-(writer,letter-class) pool cap, same value as r74's
                                # M_BANK_WORD (apples-to-apples cap convention across the arc).
PER_CALL_BUDGET_SECONDS = 480.0

GAP_CLOSE_BAR = 0.40            # pre-registered WIN bar (r73/r77's own bar, transplanted).

# Calibration numbers this run reports against (dynamically recomputed where possible -- see
# `run69_anchor_numbers`/`run77_anchor_numbers` -- these are FALLBACK citations only, used if a
# prior run's checkpoint is somehow unavailable at report time).
RUN69_CROSS_CHAR_CITE = 28.8    # run 69's own condition A (cross-writer, inv-only) char accuracy.
RUN69_WITHIN_CHAR_CITE = 55.0   # run 69's own condition E (within-writer, +pose) char accuracy.
RUN77_WORD_COVERAGE_CITE = 28.6     # run 77's own n_repeat_instances/n_test_words (%).
RUN77_GAP_CLOSED_WORD_CITE = 14.3   # run 77's own gap_closed_word (%).
RUN77_HARVEST_PRECISION_CITE = 77.6 # run 77's own harvest_precision_pooled (%).


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
    return r61._wilson_ci(k, n)


# ============================================================================================= #
#  DYNAMIC CALIBRATION ANCHORS -- recomputed straight from prior runs' OWN checkpoint files
#  (read-only) rather than hardcoded, per the task's own instruction (numbers can drift).
# ============================================================================================= #
def run69_anchor_numbers() -> dict:
    """Recomputes run 69's own condition A (cross-writer, inv-only) and condition E (within-writer,
    +pose) char accuracy DIRECTLY from its saved read.json -- the exact same reduction
    `r69.stage_summary` itself performs (`_acc`/`_pred_inv`/`_pred_mix`), so this always matches
    run 69's own printed numbers rather than a hand-copied (and potentially stale) citation."""
    rd = _load(RUN69_READ)
    recs = rd["records"]
    n = len(recs)
    kA, _ = r69._acc(recs, lambda r: r69._pred_inv(r["invA"]))
    kE, _ = r69._acc(recs, lambda r: r69._pred_mix(r["invB"], r["poseE"], r69.PRIMARY_LAMBDA))
    return {"cross_pct": 100 * kA / n, "within_pct": 100 * kE / n, "n": n, "kA": kA, "kE": kE}


def run77_anchor_numbers() -> dict:
    """Recomputes run 77's own headline word-adaptation numbers from its saved checkpoints
    (read-only) -- the number THIS run's letter-coverage/gap-closed figures are compared against."""
    summ = _load(RUN77_SUMMARY)
    prep = _load(RUN77_PREP)
    word_coverage_pct = 100 * prep["n_repeat_instances"] / prep["n_test_words"]
    return {
        "harvest_precision_pooled_pct": summ["harvest_precision_pooled"],
        "gap_closed_word_pct": 100 * summ["gap_closed_word"],
        "word_repeat_coverage_pct": word_coverage_pct,
        "n_test_words": prep["n_test_words"],
        "n_repeat_word_instances": prep["n_repeat_instances"],
    }


# ============================================================================================= #
#  LETTER DECOMPOSITION -- given char segmentation (run 77's own `word_records[*]['chars']`),
#  turn each word instance into its constituent (letter, canon) records. Pure Python, no I/O.
# ============================================================================================= #
def build_letters(run77_prep: dict, run77_read: dict) -> tuple:
    """Decomposes every one of run 77's 693 test-word instances into its GIVEN constituent letters
    (`word_records[*]['chars']`, already segmented+canon-computed by run 77's own prep stage) and
    pairs each with its FIXED cross-bank cost row (`char_cross_rows`, already computed by run 77's
    own read stage -- no new native call needed for this, the cold arm is a pure lookup). Assigns a
    per-writer `local_idx` (sorted by (wid, pos), i.e. the writer's own word-stream order) -- the
    index space the NEW native pairwise stage below fills in."""
    word_records = run77_prep["word_records"]
    words_state = run77_read["words"]
    letters = []
    lid = 0
    for wd in word_records:
        wid = wd["wid"]
        wrec = words_state[str(wid)]
        rows = wrec["char_cross_rows"]
        for pos, ch in enumerate(wd["chars"]):
            true_symbol = ch["true_symbol"]
            assert "a" <= true_symbol <= "z", f"unexpected symbol {true_symbol!r}"
            letters.append({
                "lid": lid, "wid": wid, "pos": pos, "writer": wd["writer"], "word": wd["word"],
                "true_symbol": true_symbol, "true_li": ord(true_symbol) - ord("a"),
                "inv": ch["inv"], "pose_own": ch["pose_own"], "cross_row": rows[pos],
            })
            lid += 1
    by_writer = defaultdict(list)
    for l in letters:
        by_writer[l["writer"]].append(l)
    for w, lst in by_writer.items():
        lst.sort(key=lambda l: (l["wid"], l["pos"]))
        for i, l in enumerate(lst):
            l["local_idx"] = i
    return letters, dict(by_writer)


# ============================================================================================= #
#  STAGE: prep -- decompose run 77's own word stream into letters (pure Python, no native calls).
# ============================================================================================= #
def build_prep() -> dict:
    if not os.path.exists(RUN77_PREP) or not os.path.exists(RUN77_READ):
        raise SystemExit("WALL: run 77's prep.json/read.json not found -- run 77 must have "
                          "completed its own prep+read stages first (read-only dependency).")
    run77_prep = _load(RUN77_PREP)
    run77_read = _load(RUN77_READ)
    if not run77_read.get("done"):
        raise SystemExit("WALL: run 77's read.json is not COMPLETE -- cannot borrow its word-level "
                          "corpus until run 77 itself finished reading.")

    letters, by_writer = build_letters(run77_prep, run77_read)
    n_letters = len(letters)

    counts = Counter((l["writer"], l["true_li"]) for l in letters)
    n_repeat_letters = sum(1 for l in letters if counts[(l["writer"], l["true_li"])] >= 2)

    letters_per_writer = {str(w): len(lst) for w, lst in by_writer.items()}
    class_dist = dict(Counter(l["true_symbol"] for l in letters))
    distinct_classes_per_writer = {str(w): len({l["true_li"] for l in lst})
                                   for w, lst in by_writer.items()}

    return {
        "letters": letters,
        "n_test_letters": n_letters,
        "n_test_writers": len(by_writer),
        "letters_per_writer": letters_per_writer,
        "distinct_classes_per_writer": distinct_classes_per_writer,
        "n_repeat_letter_instances": n_repeat_letters,
        "class_dist": class_dist,
        "run77_n_test_words": run77_prep["n_test_words"],
        "run77_n_repeat_word_instances": run77_prep["n_repeat_instances"],
        "run77_n_test_writers": run77_prep["n_test_writers"],
    }


def stage_prep():
    print(f"\n{SEP}\n  STAGE: prep -- decompose run 77's own 693-word stream into GIVEN letters "
          f"(pure Python, no native calls)\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("prep")
    print(f"  seeds/stroke_shapes.json md5 (before): {md5_before}", flush=True)

    out = build_prep()
    out["stroke_shapes_md5"] = md5_before
    _save(out, _ckpt("prep.json"))
    _seed_guard("prep", md5_before)

    lpw = sorted(out["letters_per_writer"].values())
    print(f"  writers={out['n_test_writers']}  test letters={out['n_test_letters']}  "
          f"(from run 77's {out['run77_n_test_words']} test words)", flush=True)
    print(f"  letters/writer: min={lpw[0]} median={lpw[len(lpw)//2]} max={lpw[-1]}", flush=True)
    word_cov = 100 * out["run77_n_repeat_word_instances"] / out["run77_n_test_words"]
    letter_cov = 100 * out["n_repeat_letter_instances"] / out["n_test_letters"]
    print(f"  STRUCTURAL REPEAT COVERAGE (the substrate an adapted bank can grow from):", flush=True)
    print(f"    run 77 WORD-repeat coverage   = {out['run77_n_repeat_word_instances']}/"
          f"{out['run77_n_test_words']} = {word_cov:.1f}%", flush=True)
    print(f"    run 78 LETTER-repeat coverage = {out['n_repeat_letter_instances']}/"
          f"{out['n_test_letters']} = {letter_cov:.1f}%   (delta: {letter_cov-word_cov:+.1f}pp)",
          flush=True)
    print(f"  class dist (top 10): {Counter(out['class_dist']).most_common(10)}", flush=True)
    print(f"  saved -> {_ckpt('prep.json')}  [prep {time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: read -- THE ONLY NEW NATIVE STAGE. Full same-writer letter-to-letter pairwise DTW
#  (inv + pose channels, decoupled per r69's own convention). Block-checkpointed per writer.
# ============================================================================================= #
def stage_read():
    print(f"\n{SEP}\n  STAGE: read -- native same-writer LETTER pairwise DTW precompute (inv + "
          f"pose channels)\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("read")
    import substrate_rs as srs
    native = srs.Substrate()._inner
    prep = _require("prep.json")
    letters = prep["letters"]

    by_writer = defaultdict(list)
    for l in letters:
        by_writer[l["writer"]].append(l)
    for w in by_writer:
        by_writer[w].sort(key=lambda l: l["local_idx"])

    out_path = _ckpt("read.json")
    state = _load(out_path) if os.path.exists(out_path) else {
        "pairwise": [], "done_writers": [], "done": False,
    }
    if state.get("done"):
        print(f"  read already COMPLETE ({len(state['pairwise'])} pairwise entries).", flush=True)
        return 0

    done_writers = set(state["done_writers"])
    deadline = time.time() + PER_CALL_BUDGET_SECONDS
    n_new = 0
    total_pairs_est = sum(n * (n - 1) // 2 for n in (len(lst) for lst in by_writer.values()))
    print(f"  {len(by_writer)} writers, {total_pairs_est} same-writer letter pairs to compute "
          f"(x2 DTW channels = ~{2*total_pairs_est} native calls)", flush=True)

    for w in sorted(by_writer):
        if w in done_writers:
            continue
        lst = by_writer[w]
        n = len(lst)
        for i in range(n):
            for j in range(i + 1, n):
                d_inv = cc66.dtw(native, lst[i]["inv"], lst[j]["inv"])
                d_pose = cc66.dtw(native, lst[i]["pose_own"], lst[j]["pose_own"])
                state["pairwise"].append([w, i, j, d_inv, d_pose])
        done_writers.add(w)
        n_new += 1
        state["done_writers"] = sorted(done_writers)
        _save(state, out_path)
        _seed_guard("read", md5_before)
        print(f"    ... writer {w} done ({n} letters, {n*(n-1)//2} pairs, "
              f"{len(done_writers)}/{len(by_writer)} writers)  [{time.time()-t0:.1f}s]", flush=True)
        if time.time() > deadline:
            print(f"  WALL-BUDGET -- re-invoke --stage read to resume.", flush=True)
            return 2

    state["done"] = True
    _save(state, out_path)
    _seed_guard("read", md5_before)
    print(f"  read COMPLETE: {len(state['pairwise'])} pairwise entries, {len(done_writers)} writers "
          f"[{time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  BOOTSTRAP MACHINERY -- pure Python/numpy, lookups into the fixed tables from `read`. Importable
#  by tests without native/real data.
# ============================================================================================= #
def build_letter_pairwise_index(pairwise_rows: list) -> dict:
    idx = {}
    for w, i, j, d_inv, d_pose in pairwise_rows:
        idx[(w, i, j)] = (d_inv, d_pose)
        idx[(w, j, i)] = (d_inv, d_pose)
    return idx


def fused_letter_cost(writer: int, local_idx: int, pool_by_wc: dict, pairwise_idx: dict,
                      cross_row: list, exclude_local_idx=None, lam: float = PRIMARY_LAMBDA_POSE
                      ) -> list:
    """The per-letter 26-class FUSED cost vector: `fuse_holistic`'s min(own,cross) policy
    (r77, transplanted to letter grain) -- fused[c] = min(cross_row[c], own_pool_cost[c]). The
    own-pool cost, when a class has >=1 pool entry, is computed the SAME decoupled way r69's own
    `_class_cost` computes a bank cost (best INV exemplar and best POSE exemplar chosen
    independently, then combined) -- just sourced from the fixed pairwise table instead of fresh
    DTW calls. `exclude_local_idx` is the ALWAYS-ON leave-one-out guard: a query letter must never
    see itself as its own pool evidence."""
    out = list(cross_row)
    for c in range(26):
        entries = pool_by_wc.get((writer, c))
        if not entries:
            continue
        cands = [e for e in entries if e["local_idx"] != exclude_local_idx]
        if not cands:
            continue
        d_inv = min(pairwise_idx[(writer, local_idx, e["local_idx"])][0] for e in cands)
        d_pose = min(pairwise_idx[(writer, local_idx, e["local_idx"])][1] for e in cands)
        pool_cost = d_inv + lam * d_pose
        if pool_cost < out[c]:
            out[c] = pool_cost
    return out


def letter_visual_accuracy(letter_index: list, pool_by_wc: dict, pairwise_idx: dict) -> dict:
    """Per-letter VISUAL accuracy, NO context/LM/word-level information whatsoever -- pure argmin
    over the fused 26-class cost vector. THE headline signal."""
    ok = n = 0
    per_class_ok, per_class_n = Counter(), Counter()
    for l in letter_index:
        fused = fused_letter_cost(l["writer"], l["local_idx"], pool_by_wc, pairwise_idx,
                                  l["cross_row"], exclude_local_idx=l["local_idx"])
        pred_li = int(np.argmin(fused))
        is_ok = int(pred_li == l["true_li"])
        ok += is_ok
        n += 1
        per_class_n[l["true_li"]] += 1
        per_class_ok[l["true_li"]] += is_ok
    return {"acc": ok / n if n else 0.0, "ok": ok, "n": n,
           "per_class_ok": dict(per_class_ok), "per_class_n": dict(per_class_n)}


def decompose_harvest(pred_word: str, letters_of_word: list) -> list:
    """THE per-letter harvest step: given a confidently-harvested WORD read (`pred_word`, already
    gated by `harvest_ok`) and that word's GIVEN char segmentation (`letters_of_word`, position-
    ordered), returns one `(pos, pseudo_li, true_li, correct)` record per letter position. A wrong
    word read can still get some letters right (and vice versa) -- `correct` is checked per
    position here, never assumed equal to the word-level verdict. Positions beyond `len(pred_word)`
    are skipped (defensive only -- candidate generation is always length-matched to the true word,
    so this should never trigger on real data)."""
    out = []
    for pos, l in enumerate(letters_of_word):
        if pos >= len(pred_word):
            break
        pseudo_li = ord(pred_word[pos]) - ord("a")
        out.append({"pos": pos, "pseudo_li": pseudo_li, "true_li": l["true_li"],
                   "correct": int(pseudo_li == l["true_li"])})
    return out


def build_true_ceiling_pool(letter_index: list) -> dict:
    """CEILING pool (never fed to decode, calibration only): TRUE-labeled leave-one-out grouping
    -- `{(writer, true_class): [local_idx, ...]}` over ALL of that writer's OTHER test letters. A
    stronger, freshly-computed ceiling on THIS run's own sample (not run 69's capped random-M
    bank) -- reported alongside, not required to reproduce run 69's literal 55.0%."""
    pool = defaultdict(list)
    for l in letter_index:
        pool[(l["writer"], l["true_li"])].append({"local_idx": l["local_idx"], "margin": 1e18})
    return dict(pool)


def decode_word_via_letters(rows: list, wrec: dict, lex_by_len: dict, lm_score, lm_weight: float,
                            visual_weight: float, K: int = BEAM_K) -> dict:
    """The downstream 'word accuracy WITH context' decoder -- per-char LOOSE route ONLY (see module
    docstring's 'one new reduction': the whole-word holistic bank route is deliberately disabled so
    this number actually reflects the per-letter-adapted `rows`, never bypasses them)."""
    cand_words, vscores = r75.topk_candidates(rows, lex_by_len, "loose", K)
    if len(cand_words) == 0:
        return {"pred": "", "n_cands": 0}
    vnorm = r76._normalize_visual([vscores])[0]
    prev, nxt = wrec["context"]["prev"], wrec["context"]["next"]
    lm_scores = np.array([lm_score(prev, c) + lm_score(c, nxt) for c in cand_words])
    combined = lm_weight * lm_scores + visual_weight * vnorm
    best_i = int(np.argmax(combined))
    return {"pred": cand_words[best_i], "n_cands": len(cand_words)}


def _word_acc_via_letters(corpus77, letters_by_wid: dict, pool_by_wc_letters: dict,
                          pairwise_idx: dict, lex_by_len: dict, lm_score, lm_weight: float,
                          visual_weight: float) -> dict:
    char_ok = char_n = word_ok = word_n = 0
    for wid, wl in letters_by_wid.items():
        rows = [fused_letter_cost(l["writer"], l["local_idx"], pool_by_wc_letters, pairwise_idx,
                                  l["cross_row"], exclude_local_idx=l["local_idx"]) for l in wl]
        dec = decode_word_via_letters(rows, corpus77.words[wid], lex_by_len, lm_score,
                                      lm_weight, visual_weight)
        true = corpus77.true_word(wid)
        pred = dec["pred"]
        n = min(len(pred), len(true))
        char_ok += sum(1 for i in range(n) if pred[i] == true[i])
        char_n += len(true)
        word_ok += int(pred == true)
        word_n += 1
    return {"char_acc": char_ok / char_n if char_n else 0.0,
           "word_acc": word_ok / word_n if word_n else 0.0,
           "char_n": char_n, "word_n": word_n}


# ============================================================================================= #
#  THE EM LOOP -- word-level harvest decisions REPLAY run 77's OWN `run_em` (r77.py lines ~814-856)
#  VERBATIM (same corpus, same margin threshold, same `decode_one`/`harvest_ok`/`r73._pool_add`
#  calls, same word-form pool growth) so the harvested-word set is BYTE-IDENTICAL to run 77's own
#  actual run. The ONLY addition: every harvested word is ALSO decomposed into its given letters,
#  growing a SEPARATE per-(writer, letter-class) pool this run measures independently.
# ============================================================================================= #
def run_em_and_harvest_letters(corpus77, letters_by_wid: dict, letter_index: list,
                               pairwise_idx: dict, lex_by_len: dict, lm_score,
                               margin_threshold: float, lm_weight: float, visual_weight: float,
                               max_rounds: int = MAX_ROUNDS) -> dict:
    pool_by_wc_words: dict = {}
    pool_by_wc_letters: dict = {}
    rounds = []
    harvested_word_keys = set()
    harvested_letter_keys = set()   # (writer, wid, pos) -- a letter is only ever pooled once.

    for rnd in range(max_rounds):
        # -- (a) per-letter VISUAL accuracy + downstream word-with-context, using the pool as it
        #    stood at the END of the PREVIOUS round (round 0 = COLD, empty pool). --
        lv = letter_visual_accuracy(letter_index, pool_by_wc_letters, pairwise_idx)
        wctx = _word_acc_via_letters(corpus77, letters_by_wid, pool_by_wc_letters, pairwise_idx,
                                     lex_by_len, lm_score, LM_WEIGHT, PRIMARY_VISUAL_WEIGHT)

        # -- (b) word-level EM step, VERBATIM r77.run_em body (word-form pool growth + harvest). --
        char_ok = char_n = word_ok = word_n = 0
        new_this_round = []
        hp_ok = hp_n = 0
        new_letters_this_round = []
        for wid, wrec in corpus77.words.items():
            w = wrec["writer"]
            pool = corpus77.pool_dict(wid, pool_by_wc_words, exclude_wid=wid)
            dec = r77.decode_one(corpus77, wid, pool, lm_weight, visual_weight)
            c_ok, c_n, w_ok = r77._acc_for(corpus77, wid, dec["pred"])
            char_ok += c_ok
            char_n += c_n
            word_ok += w_ok
            word_n += 1
            if r77.harvest_ok(dec, margin_threshold):
                hk = (w, dec["pred"], wid)
                true = wrec["word"]
                if hk not in harvested_word_keys:
                    harvested_word_keys.add(hk)
                    new_this_round.append((w, dec["pred"], wid, wrec["local_idx"], dec["margin"]))
                    # -- NEW: decompose the harvested word read into its given letters. --
                    for rec in decompose_harvest(dec["pred"], letters_by_wid[wid]):
                        lk = (w, wid, rec["pos"])
                        if lk in harvested_letter_keys:
                            continue
                        harvested_letter_keys.add(lk)
                        l = letters_by_wid[wid][rec["pos"]]
                        r73._pool_add(pool_by_wc_letters, w, rec["pseudo_li"], l["wid"],
                                      l["local_idx"], dec["margin"], cap=M_BOOT_LETTER)
                        new_letters_this_round.append(rec["correct"])
                hp_n += 1
                hp_ok += int(dec["pred"] == true)
        for w, label, wid, li, margin in new_this_round:
            r73._pool_add(pool_by_wc_words, w, label, wid, li, margin, cap=r77.M_BOOT_WORD)

        pool_cov_words = sum(1 for lst in pool_by_wc_words.values() if lst)
        pool_cov_letters = sum(1 for lst in pool_by_wc_letters.values() if lst)
        covered_letter_instances = sum(
            1 for l in letter_index if pool_by_wc_letters.get((l["writer"], l["true_li"])))
        rounds.append({
            "round": rnd,
            "word_char_acc": char_ok / char_n if char_n else 0.0,
            "word_word_acc": word_ok / word_n if word_n else 0.0,
            "n_new_harvested_words": len(new_this_round),
            "word_harvest_precision": (hp_ok / hp_n if hp_n else None), "word_harvest_n": hp_n,
            "letter_visual_acc": lv["acc"], "letter_visual_n": lv["n"],
            "word_ctx_char_acc": wctx["char_acc"], "word_ctx_word_acc": wctx["word_acc"],
            "n_new_letters_harvested": len(new_letters_this_round),
            "letter_harvest_precision": (sum(new_letters_this_round) / len(new_letters_this_round)
                                         if new_letters_this_round else None),
            "letter_harvest_n": len(new_letters_this_round),
            "pool_coverage_writer_word": pool_cov_words,
            "pool_coverage_writer_letterclass": pool_cov_letters,
            "covered_letter_instances": covered_letter_instances,
        })
        if len(new_this_round) == 0:
            break

    # -- final round's per-letter visual acc / downstream word acc reflect the CONVERGED pool. --
    lv_final = letter_visual_accuracy(letter_index, pool_by_wc_letters, pairwise_idx)
    wctx_final = _word_acc_via_letters(corpus77, letters_by_wid, pool_by_wc_letters, pairwise_idx,
                                       lex_by_len, lm_score, LM_WEIGHT, PRIMARY_VISUAL_WEIGHT)
    return {
        "rounds": rounds,
        "converged_at": rounds[-1]["round"],
        "hit_max_rounds": len(rounds) == max_rounds and rounds[-1]["n_new_harvested_words"] > 0,
        "final_letter_visual": lv_final,
        "final_word_ctx": wctx_final,
        "final_pool_size_letters": sum(len(v) for v in pool_by_wc_letters.values()),
        "final_pool_size_words": sum(len(v) for v in pool_by_wc_words.values()),
    }


# ============================================================================================= #
#  STREAMING WARM-UP CURVE -- strictly causal (r77's `run_streaming` shape, lines ~859-888,
#  transplanted with a letter side-channel): per-writer single pass, harvest gated the SAME way,
#  measuring LETTER visual accuracy as a function of words-read-so-far (position k never sees
#  pseudo-labels from position >= k in the SAME pass).
# ============================================================================================= #
def run_streaming_letters(corpus77, letters_by_wid: dict, pairwise_idx: dict,
                          margin_threshold: float, lm_weight: float, visual_weight: float,
                          n_order_seeds: int = N_ORDER_SEEDS) -> dict:
    by_pos = defaultdict(lambda: {"letter_ok": 0, "letter_n": 0, "n_words": 0,
                                  "letters_harvested_cum_sum": 0})
    for seed in range(n_order_seeds):
        for w in corpus77.writers():
            wids = corpus77.words_of_writer(w)
            rng = np.random.default_rng(seed * 100003 + w)
            order = rng.permutation(len(wids))
            pool_by_wc_words: dict = {}
            pool_by_wc_letters: dict = {}
            n_letters_harvested = 0
            for k, oi in enumerate(order):
                wid = wids[int(oi)]
                wl = letters_by_wid[wid]
                l_ok = 0
                for l in wl:
                    fused = fused_letter_cost(l["writer"], l["local_idx"], pool_by_wc_letters,
                                              pairwise_idx, l["cross_row"],
                                              exclude_local_idx=l["local_idx"])
                    l_ok += int(int(np.argmin(fused)) == l["true_li"])
                slot = by_pos[k]
                slot["letter_ok"] += l_ok
                slot["letter_n"] += len(wl)
                slot["n_words"] += 1
                slot["letters_harvested_cum_sum"] += n_letters_harvested

                pool = corpus77.pool_dict(wid, pool_by_wc_words, exclude_wid=None)  # causal: earlier only.
                dec = r77.decode_one(corpus77, wid, pool, lm_weight, visual_weight)
                if r77.harvest_ok(dec, margin_threshold):
                    r73._pool_add(pool_by_wc_words, w, dec["pred"], wid,
                                  corpus77.words[wid]["local_idx"], dec["margin"], cap=r77.M_BOOT_WORD)
                    for rec in decompose_harvest(dec["pred"], wl):
                        l = wl[rec["pos"]]
                        r73._pool_add(pool_by_wc_letters, w, rec["pseudo_li"], l["wid"],
                                      l["local_idx"], dec["margin"], cap=M_BOOT_LETTER)
                        n_letters_harvested += 1
    curve = []
    for k in sorted(by_pos):
        s = by_pos[k]
        curve.append({
            "position": k, "n_words": s["n_words"],
            "letter_visual_acc": s["letter_ok"] / s["letter_n"] if s["letter_n"] else 0.0,
            "avg_letters_harvested_cum": (s["letters_harvested_cum_sum"] / s["n_words"]
                                         if s["n_words"] else 0.0),
        })
    return {"curve": curve, "n_order_seeds": n_order_seeds}


# ============================================================================================= #
#  STAGE: bootstrap -- pure Python, lookups into run 77's + this run's own fixed tables.
# ============================================================================================= #
def _build_corpus77():
    """Rebuilds run 77's OWN word-level corpus from its saved (read-only) checkpoints -- the exact
    same construction `r77.stage_bootstrap` performs -- so `decode_one`/`harvest_ok`/margin
    threshold are BYTE-IDENTICAL to run 77's own actual run."""
    run77_prep = _load(RUN77_PREP)
    run77_read = _load(RUN77_READ)
    lexicon = _load(r77.RUN61_LEXICON)
    lex_by_len = r75.build_lex_by_len(lexicon["lexicon"])
    lm_score = r75.make_lm_scorer(run77_prep["lm"]["unigram"], run77_prep["lm"]["bigram"],
                                  lexicon["logfreq"])
    corpus77 = r77.FastAdaptCorpus(run77_read["words"], run77_read["pairwise"], lex_by_len,
                                   lm_score, channel="rich")
    return corpus77, run77_prep, lex_by_len, lm_score


def stage_bootstrap():
    print(f"\n{SEP}\n  STAGE: bootstrap -- EM (letter side-channel on run 77's own word harvest) + "
          f"streaming warm-up curve\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("bootstrap")
    prep = _require("prep.json")
    rd = _require("read.json")
    if not rd.get("done"):
        raise SystemExit("WALL: read not COMPLETE -- re-invoke --stage read.")

    corpus77, run77_prep, lex_by_len, lm_score = _build_corpus77()
    print(f"  run 77 corpus rebuilt: {len(corpus77.words)} words, {len(corpus77.writers())} "
          f"writers  [{time.time()-t0:.1f}s]", flush=True)

    margin_thr = r77.compute_margin_threshold(corpus77, MARGIN_PCTL_PRIMARY, LM_WEIGHT,
                                              PRIMARY_VISUAL_WEIGHT)
    run77_summary = _load(RUN77_SUMMARY) if os.path.exists(RUN77_SUMMARY) else None
    match_note = ""
    if run77_summary is not None:
        rep = run77_summary.get("margin_threshold_primary")
        match_note = f"  (run 77's own saved value: {rep}, match: {abs(rep-margin_thr)<1e-9})"
    print(f"  margin threshold (median of round-0 finite margins) = {margin_thr:.4f}{match_note}",
          flush=True)

    letter_index = prep["letters"]
    letters_by_wid = defaultdict(list)
    for l in letter_index:
        letters_by_wid[l["wid"]].append(l)
    for wid in letters_by_wid:
        letters_by_wid[wid].sort(key=lambda l: l["pos"])
    letters_by_wid = dict(letters_by_wid)

    pairwise_idx = build_letter_pairwise_index(rd["pairwise"])
    print(f"  letter pairwise index: {len(pairwise_idx)} directed entries  [{time.time()-t0:.1f}s]",
          flush=True)

    # -- COLD (empty pool) / CEILING (true-label leave-one-out, never fed to decode). --
    cold = letter_visual_accuracy(letter_index, {}, pairwise_idx)
    ceiling_pool = build_true_ceiling_pool(letter_index)
    ceiling = letter_visual_accuracy(letter_index, ceiling_pool, pairwise_idx)
    print(f"  COLD    letter visual acc = {100*cold['acc']:.1f}%  (n={cold['n']})", flush=True)
    print(f"  CEILING letter visual acc = {100*ceiling['acc']:.1f}%  (n={ceiling['n']})", flush=True)

    # -- EM: word-level harvest replayed VERBATIM on run 77's own corpus + letter side-channel. --
    em = run_em_and_harvest_letters(corpus77, letters_by_wid, letter_index, pairwise_idx,
                                    lex_by_len, lm_score, margin_thr, LM_WEIGHT,
                                    PRIMARY_VISUAL_WEIGHT, MAX_ROUNDS)
    print(f"  EM converged at round {em['converged_at']} (hit_max_rounds={em['hit_max_rounds']})  "
          f"[{time.time()-t0:.1f}s]", flush=True)
    for rr in em["rounds"]:
        whp = (f"{100*rr['word_harvest_precision']:.1f}%" if rr["word_harvest_precision"] is not None
              else "n/a")
        lhp = (f"{100*rr['letter_harvest_precision']:.1f}%"
              if rr["letter_harvest_precision"] is not None else "n/a")
        print(f"    round {rr['round']}: letter_visual={100*rr['letter_visual_acc']:.1f}%  "
              f"word_ctx_word={100*rr['word_ctx_word_acc']:.1f}%  new_words={rr['n_new_harvested_words']}"
              f" (word_hp={whp})  new_letters={rr['n_new_letters_harvested']} (letter_hp={lhp})  "
              f"letter_pool_cov={rr['pool_coverage_writer_letterclass']}  "
              f"covered_letter_instances={rr['covered_letter_instances']}", flush=True)

    # -- streaming warm-up curve. --
    warmup = run_streaming_letters(corpus77, letters_by_wid, pairwise_idx, margin_thr, LM_WEIGHT,
                                   PRIMARY_VISUAL_WEIGHT, N_ORDER_SEEDS)
    print(f"  warm-up streaming curve computed ({len(warmup['curve'])} positions)  "
          f"[{time.time()-t0:.1f}s]", flush=True)
    for row in warmup["curve"][:12]:
        print(f"    pos {row['position']:>3}: n={row['n_words']:>4}  "
              f"letter_visual={100*row['letter_visual_acc']:.1f}%  "
              f"avg_letters_harvested_cum={row['avg_letters_harvested_cum']:.1f}", flush=True)

    # -- per-class monotonicity check (own-pool fusion should never make a class WORSE than
    #    cross-only, but the ARGMIN-DECODE invariant is not automatic -- check directly). --
    cold_per_class = {c: (cold["per_class_ok"].get(c, 0) / cold["per_class_n"][c])
                      for c in cold["per_class_n"]}
    final_lv = em["final_letter_visual"]
    final_per_class = {c: (final_lv["per_class_ok"].get(c, 0) / final_lv["per_class_n"][c])
                       for c in final_lv["per_class_n"]}
    violations = {c: (cold_per_class[c], final_per_class.get(c, 0.0)) for c in cold_per_class
                 if final_per_class.get(c, 0.0) < cold_per_class[c] - 1e-9}
    print(f"  MONOTONICITY CHECK (per-class acc, cold vs converged; fused cost can only lower each "
          f"class's OWN cost, but that does not automatically guarantee the ARGMIN decode never "
          f"flips worse): {len(violations)}/26 classes regressed", flush=True)
    if violations:
        for c, (c0, c1) in sorted(violations.items()):
            print(f"    REGRESSION class '{chr(97+c)}': cold={100*c0:.1f}% -> converged={100*c1:.1f}%",
                  flush=True)

    out = {
        "margin_threshold": margin_thr,
        "cold": cold, "ceiling": ceiling,
        "em": em, "warmup": warmup,
        "cold_per_class": cold_per_class, "final_per_class": final_per_class,
        "monotonicity_violations": violations,
        "n_letters": len(letter_index), "n_writers": prep["n_test_writers"],
    }
    _save(out, _ckpt("bootstrap.json"))
    _seed_guard("bootstrap", md5_before)
    print(f"  saved -> {_ckpt('bootstrap.json')}  [{time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: summary -- letter-coverage vs run 77's 28.6%; the warm-up curve; % of cold->ceiling gap
#  closed vs run 77's own 14.3% (word); the does-letter-adaptation-work VERDICT.
# ============================================================================================= #
def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 78 SCOREBOARD (LETTER-GRAIN WRITER ADAPTATION)\n{SEP}",
          flush=True)
    md5_now = _seed_guard("summary")
    prep = _require("prep.json")
    print(f"  SEED-GUARD: seeds/stroke_shapes.json md5 = {md5_now}  "
          f"(== prep capture {prep['stroke_shapes_md5']}: {md5_now == prep['stroke_shapes_md5']})")
    boot = _require("bootstrap.json")

    r69a = run69_anchor_numbers()
    r77a = run77_anchor_numbers()
    print(f"\n  CALIBRATION ANCHORS (recomputed live from prior runs' own checkpoints, not "
          f"hardcoded):")
    print(f"    run 69 cross-writer char acc (cite {RUN69_CROSS_CHAR_CITE:.1f}%) = "
          f"{r69a['cross_pct']:.1f}%  (n={r69a['n']})")
    print(f"    run 69 within-writer char acc (cite {RUN69_WITHIN_CHAR_CITE:.1f}%) = "
          f"{r69a['within_pct']:.1f}%  (n={r69a['n']})")
    print(f"    run 77 word-repeat coverage (cite {RUN77_WORD_COVERAGE_CITE:.1f}%) = "
          f"{r77a['word_repeat_coverage_pct']:.1f}%  ({r77a['n_repeat_word_instances']}/"
          f"{r77a['n_test_words']})")
    print(f"    run 77 gap_closed(word) (cite {RUN77_GAP_CLOSED_WORD_CITE:.1f}%) = "
          f"{r77a['gap_closed_word_pct']:.1f}%")
    print(f"    run 77 harvest precision, word-grain (cite {RUN77_HARVEST_PRECISION_CITE:.1f}%) = "
          f"{r77a['harvest_precision_pooled_pct']:.1f}%")

    letter_cov_pct = 100 * prep["n_repeat_letter_instances"] / prep["n_test_letters"]
    print(f"\n  === STRUCTURAL LETTER-COVERAGE vs RUN 77's WORD-COVERAGE (the core comparison) ===")
    print(f"  run 78 letter-repeat coverage = {prep['n_repeat_letter_instances']}/"
          f"{prep['n_test_letters']} = {letter_cov_pct:.1f}%")
    print(f"  run 77 word-repeat  coverage  = {r77a['n_repeat_word_instances']}/"
          f"{r77a['n_test_words']} = {r77a['word_repeat_coverage_pct']:.1f}%")
    print(f"  DELTA = {letter_cov_pct - r77a['word_repeat_coverage_pct']:+.1f}pp  "
          f"(letter-coverage {'materially higher' if letter_cov_pct > r77a['word_repeat_coverage_pct']+10 else 'NOT materially higher'})")

    em = boot["em"]
    rounds = em["rounds"]
    final = em["final_letter_visual"]
    final_wctx = em["final_word_ctx"]
    cold, ceiling = boot["cold"], boot["ceiling"]

    print(f"\n  === THE PER-LETTER VISUAL WARM-UP CURVE (EM rounds; NO context, pure visual) ===")
    hdr = (f"  {'round':>6}{'letter_vis':>12}{'word_ctx_wd':>13}{'new_words':>11}{'word_hp':>10}"
          f"{'new_letters':>13}{'letter_hp':>11}{'letter_pool':>13}{'cov_inst':>10}")
    print(hdr)
    for rr in rounds:
        whp = f"{100*rr['word_harvest_precision']:.1f}%" if rr["word_harvest_precision"] is not None else "n/a"
        lhp = f"{100*rr['letter_harvest_precision']:.1f}%" if rr["letter_harvest_precision"] is not None else "n/a"
        print(f"  {rr['round']:>6}{100*rr['letter_visual_acc']:>11.1f}%{100*rr['word_ctx_word_acc']:>12.1f}%"
              f"{rr['n_new_harvested_words']:>11}{whp:>10}{rr['n_new_letters_harvested']:>13}{lhp:>11}"
              f"{rr['pool_coverage_writer_letterclass']:>13}{rr['covered_letter_instances']:>10}")

    print(f"\n  COLD    per-letter visual acc = {100*cold['acc']:.1f}%  (calibration cite: "
          f"{RUN69_CROSS_CHAR_CITE:.1f}% / recomputed {r69a['cross_pct']:.1f}%)")
    print(f"  CONVERGED (round {em['converged_at']}) per-letter visual acc = {100*final['acc']:.1f}%")
    print(f"  CEILING per-letter visual acc = {100*ceiling['acc']:.1f}%  (calibration cite: "
          f"{RUN69_WITHIN_CHAR_CITE:.1f}% / recomputed {r69a['within_pct']:.1f}%)")

    def _gap_close(cold_v, final_v, ceil_v):
        span = ceil_v - cold_v
        return (final_v - cold_v) / span if abs(span) > 1e-9 else float("nan")

    gap_letter = _gap_close(cold["acc"], final["acc"], ceiling["acc"])
    print(f"\n  GAP CLOSED (letter visual): {100*gap_letter:.1f}%   (bar: >= {100*GAP_CLOSE_BAR:.0f}%; "
          f"run 77's own word-grain number was {RUN77_GAP_CLOSED_WORD_CITE:+.1f}%, recomputed "
          f"{r77a['gap_closed_word_pct']:+.1f}%)")

    ci_cold = _wilson(cold["ok"], cold["n"])
    ci_final = _wilson(final["ok"], final["n"])
    sep_above_cold = ci_final[0] > cold["acc"]

    hp_letters = [rr for rr in rounds if rr["letter_harvest_precision"] is not None]
    hp_ok_total = sum(rr["letter_harvest_n"] * rr["letter_harvest_precision"] for rr in hp_letters)
    hp_n_total = sum(rr["letter_harvest_n"] for rr in hp_letters)
    letter_precision_pooled = 100 * hp_ok_total / hp_n_total if hp_n_total else float("nan")
    letter_precision_ci = _wilson(int(round(hp_ok_total)), hp_n_total) if hp_n_total else (float("nan"),) * 2

    print(f"\n  === THE CRUX: PER-LETTER HARVEST PRECISION (decomposed from word-grain reads) ===")
    print(f"  pooled letter harvest precision = {letter_precision_pooled:.1f}% CI=["
          f"{100*letter_precision_ci[0]:.1f},{100*letter_precision_ci[1]:.1f}]  (n={hp_n_total})")
    print(f"  run 77's own WORD-grain harvest precision: {r77a['harvest_precision_pooled_pct']:.1f}%  "
          f"(letter-grain {'noisier' if letter_precision_pooled < r77a['harvest_precision_pooled_pct'] - 2 else 'comparable'})")

    fast_coverage = (em["rounds"][-1]["covered_letter_instances"] / boot["n_letters"]) >= 0.5 \
        if boot["n_letters"] else False
    letter_coverage_dominant = letter_cov_pct > r77a["word_repeat_coverage_pct"] + 10

    win = (sep_above_cold and gap_letter >= GAP_CLOSE_BAR and letter_coverage_dominant)
    print(f"\n  MILESTONE (pre-registered: converged letter-visual acc closes >= "
          f"{100*GAP_CLOSE_BAR:.0f}% of cold->ceiling, CI-separated above cold, AND letter-coverage "
          f"materially exceeds run 77's {RUN77_WORD_COVERAGE_CITE:.1f}% word-coverage):")
    print(f"    cold      = {100*cold['acc']:.1f}%  CI=[{100*ci_cold[0]:.1f},{100*ci_cold[1]:.1f}]")
    print(f"    converged = {100*final['acc']:.1f}%  CI=[{100*ci_final[0]:.1f},{100*ci_final[1]:.1f}]"
          f"  (CI-separated above cold? {sep_above_cold})")
    print(f"    ceiling   = {100*ceiling['acc']:.1f}%")
    print(f"    letter-coverage dominant over run 77's word-coverage? {letter_coverage_dominant}  "
          f"(near-saturating (>=50% of instances covered) by final round? {fast_coverage})")
    print(f"    VERDICT: {'WIN -- letter-grain adaptation closes real headroom, faster/higher coverage than word-form' if win else 'NULL -- see localization below'}")
    if not win:
        if not letter_coverage_dominant:
            print(f"    LOCALIZE (a): letter-coverage ({letter_cov_pct:.1f}%) is NOT materially "
                  f"above run 77's word-coverage ({r77a['word_repeat_coverage_pct']:.1f}%) -- the "
                  f"hypothesis that letters structurally repeat far more than words on THIS corpus "
                  f"is not supported at the >10pp bar.")
        if letter_precision_pooled < 50.0:
            print(f"    LOCALIZE (b): pooled letter-harvest precision ({letter_precision_pooled:.1f}%)"
                  f" is weak -- decomposing a confident WORD read into per-letter pseudo-labels is "
                  f"noisier than the word-level number ({r77a['harvest_precision_pooled_pct']:.1f}%) "
                  f"suggested; some letters in an otherwise-correct word read are still wrong, or "
                  f"vice versa.")
        if boot["monotonicity_violations"]:
            print(f"    LOCALIZE (c): min-fusion DILUTED rather than helped for "
                  f"{len(boot['monotonicity_violations'])}/26 classes (per-class argmin-decode "
                  f"accuracy fell below cold-only for that class) -- fusion can only lower a class's "
                  f"OWN cost, but that does not prevent the ARGMIN from flipping to a newly-"
                  f"cheapened WRONG class.")
        if not sep_above_cold:
            print(f"    LOCALIZE: converged CI overlaps cold -- any lift is not statistically "
                  f"distinguishable from noise at this sample size (n={final['n']}).")
        if gap_letter < GAP_CLOSE_BAR and letter_coverage_dominant and letter_precision_pooled >= 50.0 \
                and not boot["monotonicity_violations"]:
            print(f"    LOCALIZE (d): coverage is high and harvested labels are precise and fusion "
                  f"is not diluting, yet the gap still didn't close enough -- the per-letter visual "
                  f"bank appears NON-RESPONSIVE to added own-writer exemplars in this regime (too "
                  f"few templates per class even after {MAX_ROUNDS} rounds, or a genuine "
                  f"bank-capacity/matching ceiling).")

    curve = boot["warmup"]["curve"]
    print(f"\n  WARM-UP CURVE (streaming, causal, {boot['warmup']['n_order_seeds']} order seeds "
          f"averaged) -- LETTER visual acc AS A FUNCTION OF WORDS-READ:")
    hdr2 = f"  {'position':>9}{'n_words':>9}{'letter_visual':>15}{'avg_letters_harvested':>24}"
    print(hdr2)
    for row in curve:
        print(f"  {row['position']:>9}{row['n_words']:>9}{100*row['letter_visual_acc']:>14.1f}%"
              f"{row['avg_letters_harvested_cum']:>24.1f}")
    first_n = min(5, len(curve))
    last_n = min(5, len(curve))
    words_to_click = None
    if curve:
        early = np.mean([r["letter_visual_acc"] for r in curve[:first_n]])
        late = np.mean([r["letter_visual_acc"] for r in curve[-last_n:]])
        print(f"\n  early (first {first_n} positions) letter_visual = {100*early:.1f}%   "
              f"late (last {last_n} positions) letter_visual = {100*late:.1f}%   "
              f"lift = {100*(late-early):+.1f}pp")
        for row in curve:
            if row["position"] >= 2 and row["letter_visual_acc"] > early:
                words_to_click = row["position"]
                break
        print(f"  words-to-click (first position >=2 whose letter_visual exceeds the early-position "
              f"mean): {words_to_click if words_to_click is not None else 'NEVER within '+str(len(curve))+' positions'}")

    print(f"\n  ANOMALIES / HONEST RESIDUALS:")
    print(f"    given char+word segmentation throughout (this arc's own standing convention).")
    print(f"    word-harvest decisions are BYTE-IDENTICAL to run 77's own actual run (same corpus, "
          f"same margin threshold, same decode_one/harvest_ok) -- letter harvesting is a pure side "
          f"effect, never a separately-gated/looser decision.")
    print(f"    downstream 'word acc WITH context' forces the per-char LOOSE route exclusively "
          f"(whole-word holistic bank disabled) so it actually reflects this run's own "
          f"per-letter-adapted rows -- a deliberate isolation, see module docstring.")
    print(f"    ceiling is a FRESH leave-one-out true-label pool on this run's own sample (not run "
          f"69's capped random-M-per-class bank) -- reported alongside, not required to reproduce "
          f"55.0% exactly.")
    print(f"    monotonicity violations (fusion made per-class decode WORSE than cold): "
          f"{len(boot['monotonicity_violations'])}/26 classes.")

    _save({
        "cold": cold["acc"], "ceiling": ceiling["acc"], "converged": final["acc"],
        "gap_closed_letter": gap_letter,
        "letter_repeat_coverage_pct": letter_cov_pct,
        "run77_word_repeat_coverage_pct": r77a["word_repeat_coverage_pct"],
        "letter_harvest_precision_pooled_pct": letter_precision_pooled,
        "run77_word_harvest_precision_pct": r77a["harvest_precision_pooled_pct"],
        "run69_cross_anchor_pct": r69a["cross_pct"], "run69_within_anchor_pct": r69a["within_pct"],
        "converged_word_ctx_word_acc": final_wctx["word_acc"],
        "converged_word_ctx_char_acc": final_wctx["char_acc"],
        "monotonicity_violations": boot["monotonicity_violations"],
        "words_to_click": words_to_click,
        "sep_above_cold": sep_above_cold, "letter_coverage_dominant": letter_coverage_dominant,
        "win": win,
        "margin_threshold": boot["margin_threshold"],
    }, _ckpt("summary.json"))
    _seed_guard("summary", md5_now)
    print(f"\n  saved -> {_ckpt('summary.json')}")
    print(f"\n{SEP}\n  RUN 78 COMPLETE -- see final agent report.\n{SEP}", flush=True)
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True, choices=["prep", "read", "bootstrap", "summary"])
    args = p.parse_args()
    return {"prep": stage_prep, "read": stage_read, "bootstrap": stage_bootstrap,
            "summary": stage_summary}[args.stage]()


if __name__ == "__main__":
    sys.exit(main())
