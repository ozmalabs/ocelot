"""jabberwock_cursive_wordread_run70.py -- RUN 70: THE CURSIVE WORD-READING PAYOFF (combines
CURSIVE_PLAN.md steps 1+2, RE-SCOPED per the run-70 task spec).

THE PAYOFF: run 69 made the per-letter CURSIVE posterior DECENT within-writer (55.0% char, writer-
relative pose scored in the writer's own frame -- `results/omniglot_gate_run69.log`). This run
asks the two questions that number was built to answer:
  (1) does 55%-char within-writer + lexicon collapse (run 61) give USABLE cursive WORD reading --
      does run 61's print multiplier (67% char -> 78% word) hold on cursive?
  (2) does the bidirectional word<->letter loop (run 68 -- NULL on hand-print, because print's
      posterior was already decent/entrenched and the loop had nothing to rescue) now help, in
      its OWN pre-registered intended regime: a decent-but-weak posterior with genuinely weak
      letters for the lexicon to pull up (CURSIVE_PLAN.md step 3's own framing, "after writer-
      adaptation, in the weak-letters-to-rescue regime")?

REUSE (nothing new-from-scratch -- literal function calls into three existing, unmodified runs):
  * `scripts.jabberwock_pose_read_run69` (r69) -- the writer-relative POSE recognizer: frame
    estimation (`aggregate_scale_slant`, `local_baseline_topline`), pose/invariant canon
    construction (`pose_canon`, `invariant_canon`), the exemplar-bank machinery (`select_bank`,
    `_bank_canons`, `glyphs_by_sample`, `_group_by_writer`, `_index_by_writer_sample`), and the
    per-class DTW cost (`_class_cost`). r69's own CROSS-writer bank + population frame are loaded
    VERBATIM from `results/run69_checkpoints/prep.json` (READ-ONLY) -- same bg_writers, same
    M_BANK, same BANK_SELECT_SEED, so no recompute is needed for the cross-writer condition at
    all; only the WITHIN-writer own-frame/own-bank machinery is re-run, on THIS run's own
    word-defined test-writer set (a superset/different sample of held-out writers than run 69's
    own char-based test selection, per this run's own `select_test_words`).
  * `scripts.jabberwock_wordread_run61` (r61) -- the LEXICON (WordNet+Brown, donkey=0 count data,
    loaded READ-ONLY from `results/run61_checkpoints/lexicon.json`), `decode_no_context` (arm a),
    `decode_lexicon` (arm b, FLAT/uniform prior, alpha=0 -- run 61's own primary arm), `_lex_by_len`,
    `_wilson_ci`, `_mcnemar`. Run 61's 62-class decoders are reused UNMODIFIED by padding this
    run's native 26-class (lowercase-only) distance vectors into a 62-slot row with the 36
    non-lowercase slots set to a cost no distance can reach (`_pad62`) -- `decode_lexicon` only
    ever indexes the lowercase 10..35 sub-range (`_lower_class`), so the padding is a no-op for it
    and a correctness-preserving no-op for `decode_no_context`'s argmin (see
    `tests/test_run70_migrated.py::test_pad62_preserves_argmin`).
  * `scripts.jabberwock_ia_read_run68` (r68) -- the bidirectional interactive-activation loop
    (`ia_decode`, `LAMBDAS` sweep, `build_lex_by_len` == r61's `_lex_by_len`). `ia_decode` is fed
    `b = -dists` (this run's native (L,26) lowercase log-score, exactly the shape r68 expects) and
    the SAME length-matched lexicon candidate set arm (b) uses -- `ia_decode(b, cands, None,
    lam=0.0)` is EXACTLY arm (b) (r68's own hard-tested invariant, re-verified here on THIS run's
    data in `tests/test_run70_migrated.py::test_loop_lambda_zero_equals_lexicon_collapse`).

GIVEN char+word segmentation (`domains.deepwriting_world.extract_words`, run 62/66's own loader --
per-char boundaries and word boundaries are corpus ground truth, not discovered). This isolates the
reading-stack question (does a decent-but-weak posterior + context produce usable word reading)
from segmentation, stated honestly per this arc's own convention.

THE WRITER-RELATIVE FRAME FOR A WORD CHARACTER: `local_baseline_topline` (r69, unmodified) needs a
per-SAMPLE list of neighbor glyphs sorted by their corpus `char_idx`. A word's `char_segs` (from
`extract_words`) don't carry `char_idx` directly, but DO carry `pt_start` -- and `extract_words`
computes its per-word char list from the exact same per-sample `starts = _char_starts(soc)` array,
in the exact same `enumerate(starts)` order, as `extract_char_glyphs` does when it assigns
`char_idx`. So `_local_frame_for_word_char` recovers `char_idx` for a word char by looking up
`pt_start`'s position in that SAME per-sample `starts` array (`dww._char_starts`, a read-only call
into the existing adapter -- no modification to `domains/deepwriting_world.py`, which is untouched
by this run per the "touch only your own new files" rule), then indexes into the SAME
`ws_index[(writer, sample)]` (`r69._index_by_writer_sample(all_glyphs)`) run 69 itself builds --
i.e. the word char gets baseline/topline from the FULL isolated-glyph neighbor pool for its line,
identically to how run 69 frames an isolated test char. A degenerate fallback (word's own char
list as the neighbor pool) covers the rare case a word's sample isn't found in the isolated-glyph
index; both paths are covered by unit tests and the fallback rate is reported honestly.

THE COMBINED POSTERIOR (the "decent" one run 69 built, reused verbatim): for each char position,
  within_dist[c] = invB[c] + PRIMARY_LAMBDA_POSE * poseE[c]   (own bank, own frame -- run 69's E)
  cross_dist[c]  = invA[c] + PRIMARY_LAMBDA_POSE * poseC[c]   (cross bank, population frame -- C)
using r69's own `_class_cost` and r69's own PRIMARY_LAMBDA (=1.0, pre-registered in run 69, NOT
re-tuned here). This is exactly run 69's own scoring rule, applied to word characters instead of
isolated test characters.

THE THREE READING ARMS (same per-char posteriors, same lexicon, x WITHIN vs CROSS):
  (a) per-char argmax, NO context                 -- `r61.decode_no_context` (padded).
  (b) + LEXICON COLLAPSE, one-directional          -- `r61.decode_lexicon` (padded, alpha=0, FLAT).
  (c) + BIDIRECTIONAL IA LOOP on top of (b)        -- `r68.ia_decode`, lambda in r68.LAMBDAS,
                                                       lambda=0.0 IS arm (b) by construction.

PRE-REGISTERED READ (stated before any number is computed):
  WIN  if WITHIN-writer word accuracy with lexicon (arm b) is CI-separated above the run-66
       cursive floor (0.7% word, `RUN66_WORD_FLOOR`) AND clears BAR_WITHIN_WORD = 30.0% (the low
       end of the task's own suggested 30-40% "materially usable" bar).
  The loop (c) question is reported regardless of (b)'s verdict: does best-lambda arm (c) beat
  arm (b) CI-separated, in EITHER writer condition -- the plan-refinement test (step 1 was NULL on
  print because print's posterior had nothing to rescue; this posterior is the one step 1's own
  docstring predicted the loop needs).
  NULL (localize which): if arm (b) doesn't clear the bar, is char accuracy on WORD chars close to
  run 69's 55%/28.8% (posterior didn't transfer to word-context chars) or well below (word-length
  compounding / lexicon coverage / own-bank attrition on the word-test-writer sample)?

SEED GUARD (this arc's binding rule): `OZMA_SEED_PERSIST_DISABLED=1` at import; every stage asserts
md5(seeds/stroke_shapes.json) UNCHANGED before AND after. Trains nothing; reads three read-only
JSON/py sources (run 61's lexicon, run 69's prep.json, the DeepWriting corpus) and writes only
`results/run70_checkpoints/*`.

EXECUTION (ops law): every invocation <=540s FOREGROUND, checkpointed under
`results/run70_checkpoints/`; `results/run6{1,8,9}_checkpoints/` are READ-ONLY reference (opened,
never written). `.venv` python for `read` (needs substrate_rs); system python3 fine for the other
(pure-python) stages. NEVER run in background; NEVER end a turn with a live process.

Run (from the gamma-substrate repo root):
  OZMA_SEED_PERSIST_DISABLED=1 DEEPWRITING_DIR=/tmp/handwriting PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python3 \\
    scripts/jabberwock_cursive_wordread_run70.py --stage <prep|read|decode|summary>
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
import scripts.jabberwock_wordread_run61 as r61
import scripts.jabberwock_ia_read_run68 as r68
from domains import deepwriting_world as dww

SEP = "=" * 92
STROKE_SHAPES_SEED = r69.STROKE_SHAPES_SEED
CKPT_DIR = os.path.join(ROOT, "results", "run70_checkpoints")
LOG = os.path.join(ROOT, "results", "omniglot_gate_run70.log")
os.makedirs(CKPT_DIR, exist_ok=True)

RUN61_CKPT = os.path.join(ROOT, "results", "run61_checkpoints")   # READ-ONLY.
RUN61_LEXICON = os.path.join(RUN61_CKPT, "lexicon.json")
RUN69_CKPT = os.path.join(ROOT, "results", "run69_checkpoints")   # READ-ONLY.
RUN69_PREP = os.path.join(RUN69_CKPT, "prep.json")

LETTERS26 = r68.LETTERS26
BIG = 1e6

# ------------------------------------------------------------------------------------------- #
# PRE-REGISTERED CONSTANTS -- reused verbatim from runs 61/68/69 where a shared constant exists;
# new constants for this run's own word selection are marked NEW.
# ------------------------------------------------------------------------------------------- #
SPLIT = r69.SPLIT
WRITER_SPLIT_SEED = r69.WRITER_SPLIT_SEED             # == run 62/64/66/69's own split seed.
N_BACKGROUND_FRAC = r69.N_BACKGROUND_FRAC
M_BANK = r69.M_BANK
BANK_SELECT_SEED = r69.BANK_SELECT_SEED
LOCAL_WINDOW = r69.LOCAL_WINDOW
PER_WRITER_CAP_MULT = r69.PER_WRITER_CAP_MULT
PRIMARY_LAMBDA_POSE = r69.PRIMARY_LAMBDA               # invariant+pose mix weight (run 69's, 1.0).
LOOP_LAMBDAS = r68.LAMBDAS                             # IA feedback-strength sweep (run 68's).

WORD_MIN_LEN, WORD_MAX_LEN = 3, 8                      # NEW (matches run61/69's own bounds).
N_TEST_WORDS_TARGET = 220                              # NEW: >= 150 pre-reg, margin for attrition.
TEST_WORD_SELECT_SEED = 20260802                       # NEW, pre-registered before running.
PER_CALL_BUDGET_SECONDS = 480.0

# BAP calibration (Gilet/Diard/Bessiere 2011) -- CHARACTER-level, carried from run 69 for context.
BAP_WITHIN = r69.BAP_WITHIN
BAP_CROSS = r69.BAP_CROSS

# Reading floors this run reports against (task-given, WORD-level).
RUN66_WORD_FLOOR = 0.7        # run 66's own cursive no-context/lexicon-collapse word floor (%).
RUN61_PRINT_WORD = 78.0       # run 61's hand-PRINT lexicon word accuracy (%), the multiplier target.
BAR_WITHIN_WORD = 30.0        # pre-registered WIN bar: within-writer lexicon word acc (%), low end
                               # of the task's own stated 30-40% "materially usable" range.


# ============================================================================================= #
#  I/O + seed guard (identical pattern to runs 61/68/69).
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
#  62-CLASS PADDING -- reuse r61's decoders UNMODIFIED on this run's native 26-class posteriors.
# ============================================================================================= #
def _pad62(vec26: list) -> list:
    """Embed a 26-length lowercase distance vector (lower=better) into r61's 62-class scheme
    (digits + lower + upper), with the 36 non-lowercase slots set to BIG -- unreachable by any
    real distance, so `decode_no_context`'s argmin and `decode_lexicon`'s lowercase-only indexing
    (`_lower_class`) are IDENTICAL to operating on the 26-vector directly. See
    `tests/test_run70_migrated.py::test_pad62_preserves_argmin`."""
    d = [BIG] * 62
    for c in range(26):
        d[10 + c] = vec26[c]
    return d


def _sym_table():
    symbols, _ = r61._sym_maps()
    return symbols


SYMBOLS62 = _sym_table()


# ============================================================================================= #
#  WRITER-RELATIVE FRAME FOR A WORD CHARACTER (reuses r69.local_baseline_topline verbatim).
# ============================================================================================= #
def local_frame_for_word_char(dw: dict, word: dict, char_seg: dict, ws_index: dict):
    """Returns (baseline, fell_back). Primary path: recover the word char's corpus `char_idx` via
    its `pt_start`'s position in the SAME per-sample `starts` array `extract_char_glyphs` used, then
    call r69's OWN `local_baseline_topline` against the FULL isolated-glyph neighbor pool for that
    sample -- identical treatment to an isolated run-69 test char. Fallback (sample/char not found
    in the isolated-glyph index -- a mechanical I/O edge case): use the word's own char list as the
    neighbor pool (r69's own function, unmodified, just a different neighbor list)."""
    writer, sample = word["writer"], word["sample"]
    try:
        soc = dw["soc_labels"][sample]
        starts = dww._char_starts(soc)
        k = starts.index(char_seg["pt_start"])
        gl = ws_index[(writer, sample)]
        idx = next(i for i, x in enumerate(gl) if x["char_idx"] == k)
        base, _top = r69.local_baseline_topline(gl, idx, window=LOCAL_WINDOW)
        return base, False
    except (KeyError, StopIteration, ValueError):
        word_glyphs = [{"strokes": cs["strokes"]} for cs in word["char_segs"]]
        idx2 = word["char_segs"].index(char_seg)
        base, _top = r69.local_baseline_topline(word_glyphs, idx2, window=LOCAL_WINDOW)
        return base, True


# ============================================================================================= #
#  TEST-WORD SELECTION (mirrors r69.select_test_chars, adapted to words).
# ============================================================================================= #
def select_test_words(pool: list, target_n: int, seed: int) -> list:
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(pool))
    writers_in_pool = {w["writer"] for w in pool}
    cap = max(2, (target_n // max(1, len(writers_in_pool))) * PER_WRITER_CAP_MULT)
    per_writer_count = Counter()
    seen_keys = set()
    selected = []
    for i in order:
        wd = pool[int(i)]
        key = (wd["writer"], wd["word"], wd["sample"], tuple(wd["word_point_span"]))
        if key in seen_keys:
            continue
        if per_writer_count[wd["writer"]] >= cap:
            continue
        seen_keys.add(key)
        selected.append(wd)
        per_writer_count[wd["writer"]] += 1
        if len(selected) >= target_n:
            break
    return selected


# ============================================================================================= #
#  STAGE: prep -- word selection, own-writer frame/bank, per-char query canons. Pure numpy.
# ============================================================================================= #
def build_prep(target_n: int = N_TEST_WORDS_TARGET, m_bank: int = M_BANK, dw=None,
               all_glyphs=None, run69_prep=None, lexicon=None) -> dict:
    if dw is None:
        dw = dww.load_deepwriting(SPLIT)
    if all_glyphs is None:
        all_glyphs = dww.extract_char_glyphs(dw)

    # EXACT reproduction of run 62/64/66/69's own writer split (same extract_words call + seed).
    words_for_split = dww.extract_words(dw, min_len=WORD_MIN_LEN, max_len=WORD_MAX_LEN,
                                        lowercase_only=True, complete_only=True)
    bg_words, ho_words = dww.writer_split(words_for_split, n_background_frac=N_BACKGROUND_FRAC,
                                          seed=WRITER_SPLIT_SEED)
    bg_writers = {w["writer"] for w in bg_words}
    ho_writers = {w["writer"] for w in ho_words}
    assert bg_writers.isdisjoint(ho_writers), "writer split must be disjoint"

    if run69_prep is None:
        if not os.path.exists(RUN69_PREP):
            raise SystemExit(f"WALL: run 69's prep.json not found at {RUN69_PREP} (READ-ONLY "
                              f"reuse target missing -- run 69 must have been run already).")
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

    test_word_pool = [w for w in ho_words if w["word"] in lexicon_set]
    n_ho_not_invocab = len(ho_words) - len(test_word_pool)

    by_writer = r69._group_by_writer(all_glyphs)
    ws_index = r69._index_by_writer_sample(all_glyphs)

    test_words = select_test_words(test_word_pool, target_n, TEST_WORD_SELECT_SEED)
    test_writers = sorted({w["writer"] for w in test_words})
    test_samples_by_writer = defaultdict(set)
    for w in test_words:
        test_samples_by_writer[w["writer"]].add(w["sample"])

    # -- own frame per test writer (OTHER ink, excluding samples containing a selected test word).
    frame_of_writer = {}
    n_degenerate_frame = 0
    for w in test_writers:
        gbs = r69.glyphs_by_sample(by_writer.get(w, []), exclude_samples=test_samples_by_writer[w])
        fr = r69.aggregate_scale_slant(gbs)
        frame_of_writer[w] = fr
        if fr["n_xh_obs"] == 0:
            n_degenerate_frame += 1

    # -- own bank per test writer (M exemplars/class from OTHER, test-excluded ink).
    own_bank = {}
    own_bank_coverage = {}
    for w in test_writers:
        pool_w = [g for g in by_writer.get(w, []) if g["sample"] not in test_samples_by_writer[w]]
        raw = r69.select_bank(pool_w, r69.LOWER_CLASSES, m_bank,
                              np.random.default_rng(BANK_SELECT_SEED + w))
        own_bank[str(w)] = r69._bank_canons(raw, frame_of_writer, ws_index)
        own_bank_coverage[str(w)] = {str(c): len(v) for c, v in raw.items()}

    # -- per-word, per-char query canons (invariant + pose under OWN and POPULATION frames).
    word_records = []
    n_frame_fallback = 0
    for wi, wd in enumerate(test_words):
        w = wd["writer"]
        own_fr = frame_of_writer[w]
        chars = []
        for cs in wd["char_segs"]:
            baseline, fell_back = local_frame_for_word_char(dw, wd, cs, ws_index)
            n_frame_fallback += int(fell_back)
            chars.append({
                "true_symbol": cs["symbol"],
                "inv": r69.invariant_canon(cs["strokes"]),
                "pose_own": r69.pose_canon(cs["strokes"], baseline, own_fr["x_height"],
                                           own_fr["slant_deg"]),
                "pose_pop": r69.pose_canon(cs["strokes"], baseline, population_frame["x_height"],
                                           population_frame["slant_deg"]),
            })
        word_records.append({"wid": wi, "writer": w, "word": wd["word"], "chars": chars})

    return {
        "bg_writers": sorted(bg_writers), "ho_writers": sorted(ho_writers),
        "bg_writers_match_run69": bg_writers_match_run69,
        "test_writers": test_writers,
        "population_frame": population_frame,
        "cross_bank": cross_bank,
        "writer_frames": {str(w): fr for w, fr in frame_of_writer.items()},
        "own_bank": own_bank,
        "own_bank_coverage": own_bank_coverage,
        "word_records": word_records,
        "n_test_words": len(word_records),
        "n_test_writers": len(test_writers),
        "n_ho_words": len(ho_words), "n_ho_not_invocab": n_ho_not_invocab,
        "n_degenerate_own_frame": n_degenerate_frame,
        "n_word_char_frame_fallback": n_frame_fallback,
        "word_len_dist": dict(Counter(len(wd["word"]) for wd in word_records)),
        "run61_lexicon_n": len(lexicon["lexicon"]),
    }


def stage_prep():
    print(f"\n{SEP}\n  STAGE: prep (word selection + own writer frame/bank + query canons -- pure "
          f"numpy, no native)\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("prep")
    print(f"  seeds/stroke_shapes.json md5 (before): {md5_before}", flush=True)

    out = build_prep()
    out["stroke_shapes_md5"] = md5_before
    _save(out, _ckpt("prep.json"))
    _seed_guard("prep", md5_before)

    print(f"  bg writers={len(out['bg_writers'])}  ho writers={len(out['ho_writers'])}  "
          f"(match run 69's bg set: {out['bg_writers_match_run69']})", flush=True)
    print(f"  test writers={out['n_test_writers']}  test words={out['n_test_words']}  "
          f"(ho words={out['n_ho_words']}, not-in-vocab={out['n_ho_not_invocab']})", flush=True)
    print(f"  word length dist: {sorted(out['word_len_dist'].items())}", flush=True)
    print(f"  degenerate own-frame writers (no OTHER x-height obs): {out['n_degenerate_own_frame']}"
          f" / {out['n_test_writers']}", flush=True)
    print(f"  word-char local-frame fallback (word-only neighbor pool): "
          f"{out['n_word_char_frame_fallback']}", flush=True)
    empty_own = sum(1 for cov in out["own_bank_coverage"].values()
                    for c, n in cov.items() if n == 0)
    print(f"  own-bank empty (writer,class) cells: {empty_own} / "
          f"{out['n_test_writers'] * len(r69.LOWER_CLASSES)}", flush=True)
    print(f"  saved -> {_ckpt('prep.json')}  [prep {time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: read -- per-char WITHIN/CROSS combined (invariant+pose) 26-class distance vectors.
#  Needs substrate_rs (r69's `_class_cost` -> `cc66.dtw`). Block-checkpointed, resumable.
# ============================================================================================= #
def stage_read():
    print(f"\n{SEP}\n  STAGE: read -- per-char WITHIN/CROSS combined posterior (native DTW)\n{SEP}",
          flush=True)
    t0 = time.time()
    md5_before = _seed_guard("read")
    import substrate_rs as srs
    native = srs.Substrate()._inner
    prep = _require("prep.json")
    own_bank = prep["own_bank"]
    cross_bank = prep["cross_bank"]
    words = prep["word_records"]

    out_path = _ckpt("read.json")
    state = _load(out_path) if os.path.exists(out_path) else {"records": [], "done": False}
    if state.get("done"):
        print(f"  read already COMPLETE (n={len(state['records'])}).", flush=True)
        return 0
    done = {r["wid"] for r in state["records"]}
    deadline = time.time() + PER_CALL_BUDGET_SECONDS
    n_new = 0

    for wd in words:
        if wd["wid"] in done:
            continue
        w = str(wd["writer"])
        ob = own_bank.get(w, {})
        within_dists, cross_dists = [], []
        for ch in wd["chars"]:
            invB = r69._class_cost(native, ch["inv"], ob, "inv")
            poseE = r69._class_cost(native, ch["pose_own"], ob, "pose")
            invA = r69._class_cost(native, ch["inv"], cross_bank, "inv")
            poseC = r69._class_cost(native, ch["pose_pop"], cross_bank, "pose")
            within_dists.append([invB[c] + PRIMARY_LAMBDA_POSE * poseE[c] for c in range(26)])
            cross_dists.append([invA[c] + PRIMARY_LAMBDA_POSE * poseC[c] for c in range(26)])
        state["records"].append({"wid": wd["wid"], "writer": wd["writer"], "word": wd["word"],
                                  "within_dists": within_dists, "cross_dists": cross_dists})
        n_new += 1
        if n_new % 20 == 0:
            _save(state, out_path)
            _seed_guard("read", md5_before)
            n = len(state["records"])

            def _char_acc(key):
                ok = tot = 0
                for r in state["records"]:
                    dists = r[key]
                    for i, row in enumerate(dists):
                        pred = LETTERS26[int(np.argmin(row))]
                        ok += int(pred == r["word"][i])
                        tot += 1
                return 100.0 * ok / tot if tot else 0.0

            print(f"    ... {n}/{len(words)} words  within_char={_char_acc('within_dists'):.1f}%  "
                  f"cross_char={_char_acc('cross_dists'):.1f}%  [{time.time()-t0:.1f}s]", flush=True)
            if time.time() > deadline:
                _save(state, out_path)
                _seed_guard("read", md5_before)
                print(f"  WALL-BUDGET: {len(state['records'])}/{len(words)} done -- re-invoke "
                      f"--stage read to resume.", flush=True)
                return 2

    state["done"] = True
    _save(state, out_path)
    _seed_guard("read", md5_before)
    print(f"  read {len(state['records'])} words  [{time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  DECODERS -- pure, importable, reused by tests. Arms (a)/(b)/(c) over ONE word's dists.
# ============================================================================================= #
def decode_arm_a(dists26: list) -> str:
    """(a) per-char argmax, no context -- literally `r61.decode_no_context` on the padded row."""
    padded = [_pad62(row) for row in dists26]
    return r61.decode_no_context(padded, SYMBOLS62)


def decode_arm_b(dists26: list, true_len: int, lex_by_len: dict, logfreq: dict) -> str:
    """(b) + lexicon collapse, one-directional -- `r61.decode_lexicon`, FLAT prior (alpha=0)."""
    padded = [_pad62(row) for row in dists26]
    return r61.decode_lexicon(padded, true_len, lex_by_len, logfreq, alpha=0.0)


def decode_arm_c(dists26: list, lex_by_len: dict, lambdas=LOOP_LAMBDAS) -> dict:
    """(c) + bidirectional IA loop on top of (b) -- `r68.ia_decode` per lambda in the sweep.
    lambda=0.0 is BY CONSTRUCTION identical to arm (b) (r68's own invariant, re-checked in
    `tests/test_run70_migrated.py`)."""
    b = np.array([[-v for v in row] for row in dists26], dtype=np.float64)
    cands = lex_by_len.get(len(dists26), [])
    out = {}
    for lam in lambdas:
        res = r68.ia_decode(b, cands, None, lam=lam)
        out[str(lam)] = res["word"]
    return out


def _char_acc_pair(pred: str, true: str) -> tuple:
    n = min(len(pred), len(true))
    return sum(1 for i in range(n) if pred[i] == true[i]), len(true)


# ============================================================================================= #
#  STAGE: decode -- run arms a/b/c over WITHIN and CROSS, for every test word.
# ============================================================================================= #
def stage_decode():
    print(f"\n{SEP}\n  STAGE: decode (arms a/no-context, b/lexicon, c/+loop x WITHIN vs CROSS)\n"
          f"{SEP}", flush=True)
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
        word = r["word"]
        L = len(word)
        rec = {"wid": r["wid"], "writer": r["writer"], "word": word, "len": L}
        for cond, key in (("within", "within_dists"), ("cross", "cross_dists")):
            dists = r[key]
            a_pred = decode_arm_a(dists)
            b_pred = decode_arm_b(dists, L, lex_by_len, logfreq)
            c_preds = decode_arm_c(dists, lex_by_len)
            rec[cond] = {"a": a_pred, "b": b_pred, "c": c_preds}
        per_word.append(rec)
        if len(per_word) % 50 == 0:
            print(f"    ... decoded {len(per_word)}/{len(rd['records'])}  "
                  f"[{time.time()-t0:.1f}s]", flush=True)

    _save({"per_word": per_word, "lambdas": LOOP_LAMBDAS, "stroke_shapes_md5": md5_before},
          _ckpt("decode.json"))
    _seed_guard("decode", md5_before)
    print(f"  decoded {len(per_word)} words  [{time.time()-t0:.1f}s]", flush=True)
    print(f"  saved -> {_ckpt('decode.json')}", flush=True)
    return 0


# ============================================================================================= #
#  REPORTING / VERDICT.
# ============================================================================================= #
def _acc_report(per_word: list, cond: str, arm: str, lam: str | None = None) -> dict:
    n = len(per_word)
    word_ok = char_ok = n_char = 0
    flags = []
    for pw in per_word:
        true = pw["word"]
        if arm == "c":
            pred = pw[cond]["c"][lam]
        else:
            pred = pw[cond][arm]
        ok = (pred == true)
        word_ok += ok
        flags.append(ok)
        c, tot = _char_acc_pair(pred, true)
        char_ok += c
        n_char += tot
    return {"n": n, "word_ok": word_ok, "word_acc": word_ok / n if n else 0.0,
            "word_ci": list(_wilson(word_ok, n)), "char_acc": char_ok / n_char if n_char else 0.0,
            "n_char": n_char, "flags": flags}


def _row(label, rep):
    pct = 100 * rep["word_acc"]
    ci = rep["word_ci"]
    print(f"  {label:<34}{pct:>9.1f}%{f'[{100*ci[0]:.1f},{100*ci[1]:.1f}]':>15}"
          f"{100*rep['char_acc']:>11.1f}%{'n='+str(rep['n']):>9}")


def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 70 SCOREBOARD (CURSIVE WORD-READING PAYOFF)\n{SEP}",
          flush=True)
    md5_now = _seed_guard("summary")
    prep = _require("prep.json")
    print(f"  SEED-GUARD: seeds/stroke_shapes.json md5 = {md5_now}  "
          f"(== prep capture {prep['stroke_shapes_md5']}: "
          f"{md5_now == prep['stroke_shapes_md5']})")
    dec = _require("decode.json")
    per_word = dec["per_word"]
    n = len(per_word)
    print(f"\n  n test words = {n}  (test writers: {prep['n_test_writers']}; "
          f"bg writers match run 69: {prep['bg_writers_match_run69']})")
    print(f"  word length dist: {sorted(prep['word_len_dist'].items())}")
    print(f"  BAP char calibration (run 69): within {BAP_WITHIN:.1f}%  cross {BAP_CROSS:.1f}%")
    print(f"  reading floors: run-66 cursive word floor {RUN66_WORD_FLOOR:.1f}%  |  "
          f"run-61 hand-PRINT lexicon word acc {RUN61_PRINT_WORD:.1f}%")

    print(f"\n  === WORD + CHAR ACCURACY, arms (a)/(b)/(c) x WITHIN vs CROSS-writer "
          f"(n_words={n}) ===")
    hdr = f"  {'condition':<34}{'word_acc':>9}{'word_CI':>15}{'char_acc':>11}{'n':>9}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))

    reps = {}
    for cond in ("within", "cross"):
        reps[(cond, "a")] = _acc_report(per_word, cond, "a")
        reps[(cond, "b")] = _acc_report(per_word, cond, "b")
        for lam in LOOP_LAMBDAS:
            reps[(cond, "c", str(lam))] = _acc_report(per_word, cond, "c", str(lam))

    for cond, lab in (("within", "WITHIN-writer"), ("cross", "CROSS-writer")):
        _row(f"(a) {lab} no-context", reps[(cond, "a")])
        _row(f"(b) {lab} +lexicon", reps[(cond, "b")])
        best_lam = max((str(l) for l in LOOP_LAMBDAS if l != 0.0),
                       key=lambda l: reps[(cond, "c", l)]["word_acc"])
        _row(f"(c) {lab} +loop (best lam={best_lam})", reps[(cond, "c", best_lam)])
        print()

    print(f"  LAMBDA SWEEP (word acc %, arm c; lam=0.0 must equal arm b):")
    hdr2 = f"  {'lambda':>8}{'within':>12}{'cross':>12}"
    print(hdr2)
    for lam in LOOP_LAMBDAS:
        rw = reps[("within", "c", str(lam))]["word_acc"]
        rc = reps[("cross", "c", str(lam))]["word_acc"]
        mark = " (== arm b)" if lam == 0.0 else ""
        print(f"  {lam:>7.2f}{100*rw:>11.1f}%{100*rc:>11.1f}%{mark}")

    verdicts = {}
    for cond in ("within", "cross"):
        rep_a, rep_b = reps[(cond, "a")], reps[(cond, "b")]
        best_lam = max((str(l) for l in LOOP_LAMBDAS if l != 0.0),
                       key=lambda l: reps[(cond, "c", l)]["word_acc"])
        rep_c = reps[(cond, "c", best_lam)]
        mc_ba = _mcnemar(rep_a["flags"], rep_b["flags"])
        mc_cb = _mcnemar(rep_b["flags"], rep_c["flags"])
        print(f"\n  {cond.upper()}: McNemar (b vs a): fixed={mc_ba['fixed']} broken={mc_ba['broken']}"
              f" p={mc_ba['p']:.3g}")
        print(f"  {cond.upper()}: McNemar (c[lam={best_lam}] vs b): fixed={mc_cb['fixed']} "
              f"broken={mc_cb['broken']} p={mc_cb['p']:.3g}")
        loop_ci_sep = rep_c["word_ci"][0] > rep_b["word_acc"]
        loop_helps = loop_ci_sep or (mc_cb["fixed"] > mc_cb["broken"] and mc_cb["p"] < 0.05)
        loop_hurts = (rep_c["word_ci"][1] < rep_b["word_acc"]) or \
                     (mc_cb["broken"] > mc_cb["fixed"] and mc_cb["p"] < 0.05)
        verdicts[cond] = {"rep_a": rep_a, "rep_b": rep_b, "rep_c_best": rep_c,
                          "best_lambda": best_lam, "mc_ba": mc_ba, "mc_cb": mc_cb,
                          "loop_helps": loop_helps, "loop_hurts": loop_hurts}
        print(f"  {cond.upper()}: loop {'HELPS' if loop_helps else ('HURTS' if loop_hurts else 'no material effect (NULL)')} "
              f"vs the lexicon-only arm (b) at best lambda={best_lam}")

    within_b = verdicts["within"]["rep_b"]
    ci_sep_floor = 100 * within_b["word_ci"][0] > RUN66_WORD_FLOOR
    win = (100 * within_b["word_acc"] > BAR_WITHIN_WORD) and ci_sep_floor
    print(f"\n  MILESTONE (pre-registered: WITHIN-writer lexicon word acc > {BAR_WITHIN_WORD:.0f}% "
          f"AND CI-separated above run-66's {RUN66_WORD_FLOOR:.1f}% floor):")
    print(f"    (b) WITHIN word_acc = {100*within_b['word_acc']:.1f}%  "
          f"CI=[{100*within_b['word_ci'][0]:.1f},{100*within_b['word_ci'][1]:.1f}]  "
          f"(> {BAR_WITHIN_WORD:.0f}%? {100*within_b['word_acc'] > BAR_WITHIN_WORD})  "
          f"(CI-separated above {RUN66_WORD_FLOOR:.1f}%? {ci_sep_floor})")
    print(f"    vs run-61 hand-PRINT lexicon word acc: {RUN61_PRINT_WORD:.1f}%  "
          f"(cursive/print ratio: {100*within_b['word_acc']/RUN61_PRINT_WORD:.2f}x)")
    print(f"    VERDICT: {'WIN -- cursive within-writer lexicon reading is materially usable' if win else 'NULL -- the decent-but-weak posterior does not collapse to usable cursive words'}")

    print(f"\n  ANOMALIES / HONEST RESIDUALS:")
    print(f"    given segmentation: char + word boundaries are corpus ground truth (not "
          f"discovered) -- this measures the READING STACK, not segmentation.")
    print(f"    own-bank empty (writer,class) cells: "
          f"{sum(1 for cov in prep['own_bank_coverage'].values() for c, nn in cov.items() if nn == 0)}"
          f" / {prep['n_test_writers'] * len(r69.LOWER_CLASSES)}")
    print(f"    degenerate own-frame writers (no OTHER x-height obs, fell back to defaults): "
          f"{prep['n_degenerate_own_frame']} / {prep['n_test_writers']}")
    print(f"    word-char local-frame fallback (word-only neighbor pool, sample not found in "
          f"isolated-glyph index): {prep['n_word_char_frame_fallback']}")
    print(f"    word length distribution (compounding risk for longer words): "
          f"{sorted(prep['word_len_dist'].items())}")

    reps_serialized = {}
    for key, rep in reps.items():
        cond, arm = key[0], key[1]
        lam_suffix = f":{key[2]}" if len(key) > 2 else ""
        rep_out = {k: v for k, v in rep.items() if k != "flags"}   # flags are per-word bools, drop.
        reps_serialized[f"{cond}|{arm}{lam_suffix}"] = rep_out
    _save({"reps": reps_serialized, "verdicts": verdicts, "win": win}, _ckpt("summary.json"))
    _seed_guard("summary", md5_now)
    print(f"\n  saved -> {_ckpt('summary.json')}")
    print(f"\n{SEP}\n  RUN 70 COMPLETE -- see final agent report.\n{SEP}", flush=True)
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True, choices=["prep", "read", "decode", "summary"])
    args = p.parse_args()
    return {"prep": stage_prep, "read": stage_read, "decode": stage_decode,
            "summary": stage_summary}[args.stage]()


if __name__ == "__main__":
    sys.exit(main())
