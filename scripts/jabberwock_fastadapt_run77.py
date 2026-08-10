"""jabberwock_fastadapt_run77.py -- RUN 77: FAST WRITER-ADAPTATION, ATTACKED DIRECTLY.

THE META-PROBLEM (creator): across the WHOLE cursive arc, every WIN is WITHIN-writer (already
adapted: run 69 55%, run 70 30.5%, run 74 70.3%, run 76-covered 38.9%, BAP 93%) and every FAILURE is
CROSS-writer/cold (unadapted: run 69 28.8%, run 70 5.9%, run 76 cross 7.4%, BAP 50%). It isn't
"reading is hard" -- it's "we can't adapt FAST to a new hand." Run 73 tried exactly this and got a
clean NULL for a crisp, localized reason: the cold reader it fed the harvest loop (context-free
per-char + a WORD-level lexicon) was too weak -- only ~29% of its "confident" pseudo-labels were
actually correct, so the bootstrapped bank stayed sparse AND noisy and the warm-up curve was FLAT
(cold 25.4% -> converged 24.5% char, gap closed -3%). Run 73's own post-mortem: "not dead, STARVED
-- retry after the prediction-dominant reader lands." Run 75 then built exactly that reader
(sentence-LM-dominant + loose visual, 51.2% word acc on synthetic sentences, +25-31pp over isolated
reading) and run 74 built the OTHER missing piece (whole-word holistic visual, 70.3% within-writer).
RUN 77 is run 73 reborn on both: does a FAR stronger judge of "which reads to trust" finally harvest
reliable seeds, so writer adaptation actually WARMS UP?

ISOLATING the adaptation question (deliberately, per the task): this run stays ENTIRELY within
DeepWriting (WITHIN-corpus) -- the visual channel is proven to work there (run 69 55%, run 74
70.3%). Run 76's cross-corpus (IAM) visual floor is a SEPARATE, already-diagnosed problem (run 76:
"cross-corpus visual death") and is not reintroduced here; mixing it in would confound "does
prediction-seeded adaptation work" with "does the visual channel transfer across corpora," two
different questions this arc has kept apart throughout (run 75's own docstring: "IAM-OnDB real
lines are the payoff follow-up... not built here").

REUSE (nothing rebuilt from scratch for the READER itself -- only the ADAPTATION LOOP + the
oracle-context reduction below are new):
  * `scripts.jabberwock_pose_read_run69` (r69) -- writer-relative pose machinery verbatim:
    `aggregate_scale_slant`/`glyphs_by_sample` (the UNSUPERVISED frame estimator -- no identity
    needed), `_group_by_writer`/`_index_by_writer_sample`, `select_bank`/`_class_cost` (cross
    char-bank, the per-char OOV fallback's fixed cold channel), `LOWER_CLASSES`, `PRIMARY_LAMBDA`.
    `cross_bank`/`population_frame` loaded VERBATIM (READ-ONLY) from
    `results/run69_checkpoints/prep.json` -- the SAME "generic/cross-writer pooled bank, not the
    target writer's labels" cold-start bank runs 69/73 use.
  * `scripts.jabberwock_cursive_wordread_run70` (r70) -- `local_frame_for_word_char`,
    `WORD_MIN_LEN`/`WORD_MAX_LEN`, `select_test_words`-style dedup convention.
  * `scripts.jabberwock_wordread_run61` (r61) -- the lexicon (READ-ONLY,
    `results/run61_checkpoints/lexicon.json`), `_wilson_ci`, `_mcnemar`.
  * `scripts.jabberwock_wholeword_run74` (r74) -- THE WORD-FORM BANK primitives, reused verbatim:
    `word_key`, `word_baseline`, `word_pose_canon` (the RICH channel: writer-pose-normalized
    whole-word DTW canon), `word_envelope_canon` (the coarse-envelope ablation), `_build_word_bank`
    (grouping real instances by label into a capped per-label template pool -- exactly what "grow
    the writer's word-form bank from seeds" means at the mechanism level).
  * `scripts.jabberwock_sentence_read_run75` (r75) -- THE PREDICTION-DOMINANT DECODER's cost
    functions, reused verbatim: `reduced_brown_sentences`/`build_bigram_counts`/`make_lm_scorer`
    (the sentence LM, donkey=0 count-based), `build_lex_by_len`, `loose_cost`/`strict_cost`,
    `topk_candidates` (the per-char LOOSE/bag visual route, this run's OOV fallback channel).
  * `scripts.jabberwock_iam_full_run76` (r76) -- `topk_candidates_iam`/`_normalize_visual`: the
    candidate-assembly/normalization MACHINERY, REUSED VERBATIM (holistic-bank labels vs per-char-
    loose fallback, min-max score normalization so one VISUAL_WEIGHT means the same thing regardless
    of which channel supplied the candidates). NOT reused: r76's own EXCLUSIVE dispatch policy
    ("prefer within if non-empty, else cross") -- that policy assumes a MATURE sight-vocabulary bank
    (real IAM documents, most candidates already covered) and actively HURTS a sparse, just-starting
    bootstrap pool (diagnosed directly during this run -- see `fuse_holistic`'s docstring). This
    run's OWN new `fuse_holistic` composes the writer's pool and the cross bank via r73's own
    min-fusion policy instead, THEN hands the single fused dict to `topk_candidates_iam` -- the
    candidate-generation/normalization code is unmodified; only the POLICY feeding it changed.
  * `scripts.jabberwock_bootstrap_read_run73` (r73) -- the EM/harvest LOOP SHAPE reused verbatim:
    `_pool_add` (top-M-by-margin pool cap), the leave-one-word-out round structure, the streaming
    causal warm-up-curve structure, `compute_margin_threshold`'s "percentile of round-0's OWN
    (empty-pool) margin distribution, fixed BEFORE any accuracy number exists" pre-registration
    discipline. NOT reused: r73's per-CHAR harvest/decode machinery itself (that IS the weak reader
    this run replaces) -- the loop SHAPE transfers, the READER underneath it is upgraded.
  * `scripts.jabberwock_cursive_curriculum_run66` (cc66) -- `dtw` (the held `DtwTo` Term, generic
    over any point list), `word_points`/`wordnorm` (via r74), `WORD_N`.
  * `domains/glyph_motor_world.py` (gmw) -- `_resample_arclen` (via r74/r70).

THE ONE NEW REDUCTION (deliberate, honestly stated): runs 75/76 jointly Viterbi-decode a WHOLE
multi-word sentence, where every position's own visual read ALSO comes from real ink (possibly
another, uninvolved writer's) -- that is the right design for "does prediction help reading in
general" (already answered: yes, WIN in both runs). THIS run asks a narrower question -- "does
prediction-seeded harvesting adapt ONE target writer's own word-form bank fast" -- and jointly
decoding every neighboring writer's own cold-start problem at the same time would confound the two
questions (a neighbor's own visual error would corrupt the LM's context signal for reasons that have
nothing to do with the TARGET writer's adaptation). So: sentence context here is ORACLE, real Brown
bigram context (the true prev/next word, drawn from an actual occurrence of the target word in the
reduced-Brown corpus reduction r75 already defined) -- the TARGET word is the only word actually
decoded from ink; its neighbors are assumed already understood (a sentence's context words don't
need to be independently re-derived from someone else's cold ink for THIS question). This is an
exact, non-lossy special case of run 75's own Viterbi with the neighbor positions' distributions
collapsed to a point mass at the truth -- not a new algorithm, a fixed-context reduction of the same
one, and it isolates the adaptation question the task asks for. Reported as arm (0) "ISOLATED, no
context" vs arm (1) "ORACLE-CONTEXT" on the SAME cold word set BEFORE any bootstrapping, to show the
prediction lift directly (the run 75 finding, reproduced on this run's own instances) as a sanity
check before the adaptation question is even asked.

THE COLD-START / CEILING / BOOTSTRAPPED definitions (mirrors run 73's own 3-way ladder, one grain
up -- WORD-FORM instead of per-CHAR):
  COLD (round 0)    = the writer's own UNSUPERVISED pose frame (baseline/x-height/slant from the
        writer's OTHER, test-excluded ink -- identity-free) + an EMPTY own word-form pool -> every
        word's dual-route candidate generation (`r76.topk_candidates_iam`) falls through to the
        GENERIC CROSS word-form bank (pooled background writers, `r74._build_word_bank`) or, if
        that bank has no same-length label either, the per-char LOOSE fallback (cross char-bank,
        r69's own mechanism) -- PLUS oracle sentence context (always available; prediction doesn't
        need to be "learned," it's a standing resource from round 0, exactly the task's premise).
  CEILING (never fed to decode, calibration only) = the SAME dual-route decoder, but the "own
        word-form pool" is built from the writer's OTHER real (TRUE-label) test-word instances,
        leave-one-out -- run 74's own WITHIN-arm mechanism, one word at a time. This is the
        never-touched target the bootstrap climbs toward.
  BOOTSTRAPPED (this run's contribution) = the SAME dual-route decoder, but the "own word-form
        pool" is built ENTIRELY from PSEUDO-labels self-harvested from the SAME held-out writer's
        OTHER unlabeled words (leave-one-word-out every round, exactly r73's anti-circularity
        guard) -- backed off to cross/per-char wherever no pseudo-label exists yet for that label.

THE HARVEST RULE (pre-registered from the SCORE distribution alone, mirrors r73's shape exactly,
one grain up): a word is harvested (its predicted label becomes a pseudo-label template) iff
  (1) AGREEMENT: the VISUAL-ONLY pick (dual-route candidate list, ranked by visual score alone, LM
      weight zeroed) equals the PREDICTION-DOMINANT pick (LM+visual, the actual decode) -- "the
      language model and the eye agree, no correction needed";
  (2) MARGIN: the gap between the best and second-best PREDICTION-DOMINANT score is >=
      MARGIN_THRESHOLD, fixed as the MEDIAN of round-0's finite margins BEFORE any accuracy number
      is computed (r73's own pre-registration discipline, transplanted unmodified).
This is THE crux measurement: run 73's harvest precision was ~29% (7 in 10 "confident" pseudo-labels
WRONG) -- too weak a judge to bootstrap from. The bet is that gating on PREDICTION-DOMINANT
confidence (not a weak isolated-word lexicon commitment) makes this number much higher.

PRE-REGISTERED READ (stated before any number is computed):
  WIN if (i) harvest precision is materially above run 73's 29% (the mechanism check), AND
  (ii) the converged bootstrapped word accuracy closes >= 40% of the cold->ceiling gap (r73's own
  bar, the one it missed at -3%) AND is CI-separated above cold.
  NULL if either fails -- LOCALIZE: if (i) fails, the prediction-dominant reader is STILL not a
  reliable enough judge on this corpus (same failure mode as run 73, at a higher baseline). If (i)
  passes but (ii) fails, the seeds are reliable but too SPARSE (DeepWriting's per-writer vocabulary
  is small -- most held-out writers rarely repeat a word, so there is little for a word-FORM bank to
  grow from even with perfect harvest precision) -- a corpus-structure limit, not a mechanism
  failure, and is reported honestly (repeat-word coverage is measured and stated regardless of
  verdict).

SEED GUARD / DISCIPLINE: `OZMA_SEED_PERSIST_DISABLED=1`; md5(seeds/stroke_shapes.json) asserted
UNCHANGED before AND after every stage. donkey=0 throughout (closed-form geometry, count-based LM,
EM harvest/threshold logic -- no SGD-trained net anywhere). `results/run6{1,9}_checkpoints/` and
`results/run7{0,3,4,5,6}_checkpoints/` are READ-ONLY (citations/reused-module only) -- this script
writes ONLY `results/run77_checkpoints/*`. NO git add/commit.

EXECUTION (ops law): every invocation <=540s FOREGROUND, checkpointed under
`results/run77_checkpoints/`, block-resumable. `.venv` python needed for `read` (native
`substrate_rs` DTW); `prep`/`bootstrap`/`summary` are pure Python (numpy + nltk) and run under
either interpreter (this run uses `.venv` throughout for consistency). NEVER run in background;
NEVER end a turn with a live process.

Run (from the gamma-substrate repo root):
  OZMA_SEED_PERSIST_DISABLED=1 DEEPWRITING_DIR=/tmp/handwriting PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python3 \\
    scripts/jabberwock_fastadapt_run77.py --stage <prep|read|bootstrap|summary>
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
import scripts.jabberwock_wholeword_run74 as r74
import scripts.jabberwock_sentence_read_run75 as r75
import scripts.jabberwock_iam_full_run76 as r76
import scripts.jabberwock_bootstrap_read_run73 as r73
import scripts.jabberwock_cursive_curriculum_run66 as cc66
from domains import deepwriting_world as dww

SEP = "=" * 92
STROKE_SHAPES_SEED = r69.STROKE_SHAPES_SEED
CKPT_DIR = os.path.join(ROOT, "results", "run77_checkpoints")
LOG = os.path.join(ROOT, "results", "omniglot_gate_run77.log")
os.makedirs(CKPT_DIR, exist_ok=True)

RUN61_LEXICON = os.path.join(ROOT, "results", "run61_checkpoints", "lexicon.json")   # READ-ONLY.
RUN69_PREP = os.path.join(ROOT, "results", "run69_checkpoints", "prep.json")         # READ-ONLY.

# ------------------------------------------------------------------------------------------- #
# PRE-REGISTERED CONSTANTS -- reused verbatim from the arc's own shared split/weights where one
# exists; NEW constants for this run's own selection/harvest are marked NEW.
# ------------------------------------------------------------------------------------------- #
SPLIT = r69.SPLIT
WRITER_SPLIT_SEED = r69.WRITER_SPLIT_SEED
N_BACKGROUND_FRAC = r69.N_BACKGROUND_FRAC
WORD_MIN_LEN, WORD_MAX_LEN = r70.WORD_MIN_LEN, r70.WORD_MAX_LEN
M_BANK_WORD = r74.M_BANK_WORD                 # 5 -- templates/label, both cross bank and boot pool.
BANK_SELECT_SEED = r74.BANK_SELECT_SEED
PRIMARY_LAMBDA_POSE = r69.PRIMARY_LAMBDA
LOWER_CLASSES = r69.LOWER_CLASSES
BEAM_K = r75.BEAM_K
LM_WEIGHT = r75.LM_WEIGHT
VISUAL_WEIGHTS = r75.VISUAL_WEIGHTS
PRIMARY_VISUAL_WEIGHT = r75.PRIMARY_VISUAL_WEIGHT      # pre-registered in run 75, reused unmodified.

MIN_OWN_WORDS = 15             # NEW -- task's own ">= ~15-20 words/writer" floor.
CAP_OWN_WORDS = 25             # NEW -- per-writer budget cap (bounds compute).
ADAPT_WRITER_CAP = 30          # NEW -- bounds total compute; ranked by depth, seeded tie-break.
WORD_SELECT_SEED = 20260910    # NEW, pre-registered before running (this arc's own convention: the
                                # date this arc's shared seeds were minted, reused verbatim as this
                                # run's own selection seed for consistency, not tuned per-run).
CONTEXT_SELECT_SEED = 20260911
M_BOOT_WORD = M_BANK_WORD       # bootstrapped word-form pool cap -- apples-to-apples with cross bank.
MAX_ROUNDS = 8
N_ORDER_SEEDS = 5
PER_CALL_BUDGET_SECONDS = 480.0
CROSS_LABEL_CAP_PER_LEN = 60    # NEW -- caps native calls; cross bank labels/length ranked by count.

# Harvest rule (mirrors r73's AGREEMENT_PRIMARY/MARGIN_PCTL_PRIMARY exactly, transplanted).
MARGIN_PCTL_PRIMARY = 50
MARGIN_PCTL_ROBUST = (30, 70)

# Calibration numbers this run reports against (prior runs' OWN numbers, different word sample).
RUN73_HARVEST_PRECISION = 29.0          # run 73's own crux number -- the bar this run must clear.
RUN73_GAP_CLOSED = -3.0                 # run 73's own gap-closed% (word) -- the bar this run must beat.
RUN69_WITHIN_CHAR, RUN69_CROSS_CHAR = 55.0, 28.8
RUN70_WITHIN_WORD, RUN70_CROSS_WORD = 30.5, 5.9
RUN74_WITHIN_HOLISTIC = 70.3
RUN75_GOLD_WORD = 51.2

GAP_CLOSE_BAR = 0.40            # pre-registered WIN bar (r73's own bar, transplanted unmodified).
HARVEST_PRECISION_BAR = 50.0    # pre-registered: "materially above 29%" -- set at run 73's number
                                 # plus a wide margin, well short of 100%, before any number is seen.


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


def _mcnemar(a, b):
    return r61._mcnemar(a, b)


# ============================================================================================= #
#  ORACLE SENTENCE CONTEXT -- per-occurrence (prev, next) pairs mined from the SAME reduced-Brown
#  reduction run 75 trains its LM on (see module docstring's "the one new reduction").
# ============================================================================================= #
def collect_word_contexts(reduced_sentences: list) -> dict:
    """word -> [(prev, next), ...], one entry per occurrence in the reduced corpus (boundary
    tokens '^'/'$' where the word is sentence-initial/final post-reduction)."""
    out = defaultdict(list)
    for toks in reduced_sentences:
        seq = ["^"] + toks + ["$"]
        for i in range(1, len(seq) - 1):
            out[seq[i]].append((seq[i - 1], seq[i + 1]))
    return dict(out)


# ============================================================================================= #
#  WRITER / WORD SELECTION -- depth per writer (need a real warm-up trajectory), preferring writers
#  with REPEAT-word structure (the only instances a word-FORM bank can actually grow from), same
#  dedup convention as r73.select_bootstrap_words.
# ============================================================================================= #
def select_adapt_words(ho_words: list, lexicon_set: set, word_contexts: dict, min_words: int,
                       cap: int, writer_cap: int, seed: int) -> tuple:
    pool = [w for w in ho_words if w["word"] in lexicon_set and w["word"] in word_contexts]
    n_excluded_no_context = sum(1 for w in ho_words if w["word"] in lexicon_set
                                and w["word"] not in word_contexts)
    by_writer = defaultdict(list)
    for w in pool:
        by_writer[w["writer"]].append(w)

    def _n_repeats(lst):
        c = Counter(w["word"] for w in lst)
        return sum(n for n in c.values() if n >= 2)

    eligible = [wid for wid, lst in by_writer.items() if len(lst) >= min_words]
    eligible.sort(key=lambda wid: (-_n_repeats(by_writer[wid]), -len(by_writer[wid]), wid))
    chosen_writers = eligible[:writer_cap]

    rng = np.random.default_rng(seed)
    selected = []
    for w in sorted(chosen_writers):
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
    return selected, n_excluded_no_context, {w: _n_repeats(by_writer[w]) for w in chosen_writers}


# ============================================================================================= #
#  STAGE: prep -- writer/word selection, own unsupervised frame, cross word-form bank, real own
#  bank (ceiling ref), LM + oracle context, per-word/per-char query canons. Pure numpy, no native.
# ============================================================================================= #
def build_prep(min_words: int = MIN_OWN_WORDS, cap: int = CAP_OWN_WORDS,
              writer_cap: int = ADAPT_WRITER_CAP, m_bank_word: int = M_BANK_WORD,
              dw=None, all_glyphs=None, run69_prep=None, lexicon=None) -> dict:
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
    bg_writers_match_run69 = (set(run69_prep["bg_writers"]) == bg_writers)
    population_frame = run69_prep["population_frame"]
    cross_charbank = run69_prep["cross_bank"]

    if lexicon is None:
        if not os.path.exists(RUN61_LEXICON):
            raise SystemExit(f"WALL: run 61's lexicon.json not found at {RUN61_LEXICON}.")
        lexicon = _load(RUN61_LEXICON)
    lexicon_set = set(lexicon["lexicon"])
    logfreq = lexicon["logfreq"]

    # -- the LM + oracle per-occurrence context (r75's own reduction, reused verbatim). --
    reduced = r75.reduced_brown_sentences()
    uni, bi = r75.build_bigram_counts(reduced)
    bi_pruned = {f"{a}|{b}": c for (a, b), c in bi.items() if c >= r75.BIGRAM_MIN_KEEP_COUNT}
    word_contexts = collect_word_contexts(reduced)

    test_words, n_excluded_no_context, repeats_by_writer = select_adapt_words(
        ho_words, lexicon_set, word_contexts, min_words, cap, writer_cap, WORD_SELECT_SEED)
    test_writers = sorted({w["writer"] for w in test_words})
    test_samples_by_writer = defaultdict(set)
    for w in test_words:
        test_samples_by_writer[w["writer"]].add(w["sample"])

    by_writer = r69._group_by_writer(all_glyphs)
    ws_index = r69._index_by_writer_sample(all_glyphs)

    # -- own UNSUPERVISED frame (label-free -- test-excluded ink only). --
    frame_of_writer, n_degenerate_frame = {}, 0
    for w in test_writers:
        gbs = r69.glyphs_by_sample(by_writer.get(w, []), exclude_samples=test_samples_by_writer[w])
        fr = r69.aggregate_scale_slant(gbs)
        frame_of_writer[w] = fr
        n_degenerate_frame += int(fr["n_xh_obs"] == 0)

    # -- CROSS word-form bank (generic, background writers -- r74's own mechanism, verbatim). --
    bg_frame = {}
    bg_glyphs_pool = {}
    for w in bg_writers:
        gbs = r69.glyphs_by_sample(by_writer.get(w, []))
        bg_frame[w] = r69.aggregate_scale_slant(gbs)
        bg_glyphs_pool.update(gbs)
    assert population_frame  # sanity: population frame citation exists (unused directly here; the
                              # per-instance OWN frame is what this run's cold channel uses).
    cross_bank_by_label = r74._build_word_bank(
        bg_words, lambda w: bg_frame[w], m_bank_word, BANK_SELECT_SEED + 10_000_000, dw, ws_index)
    length_index_cross = defaultdict(list)
    for word, canons in cross_bank_by_label.items():
        length_index_cross[len(word)].append(word)
    # cap labels/length by template-count desc (bounds native calls in `read`, documented not
    # cherry-picked -- a compute bound, not an accuracy-tuned choice).
    n_cross_labels_capped = 0
    for L, labels in length_index_cross.items():
        if len(labels) > CROSS_LABEL_CAP_PER_LEN:
            labels.sort(key=lambda w: -len(cross_bank_by_label[w]))
            n_cross_labels_capped += len(labels) - CROSS_LABEL_CAP_PER_LEN
            length_index_cross[L] = labels[:CROSS_LABEL_CAP_PER_LEN]

    # -- per-writer, per-word records: whole-word rich+env canon + per-char loose-route canon +
    #    oracle sentence context (one per instance, seeded cycle over that word's real occurrences).
    ctx_rng = np.random.default_rng(CONTEXT_SELECT_SEED)
    word_records = []
    n_word_frame_fallback = 0
    ctx_cursor = defaultdict(int)
    for wi, wd in enumerate(test_words):
        w = wd["writer"]
        own_fr = frame_of_writer[w]
        baseline, fb = r74.word_baseline(dw, wd, ws_index)
        n_word_frame_fallback += int(fb > 0)
        rich = r74.word_pose_canon(wd, baseline, own_fr["x_height"], own_fr["slant_deg"])
        env = r74.word_envelope_canon(wd)
        chars = []
        for cs in wd["char_segs"]:
            cbaseline, _fb = r70.local_frame_for_word_char(dw, wd, cs, ws_index)
            chars.append({
                "true_symbol": cs["symbol"],
                "inv": r69.invariant_canon(cs["strokes"]),
                "pose_own": r69.pose_canon(cs["strokes"], cbaseline, own_fr["x_height"],
                                           own_fr["slant_deg"]),
            })
        ctxs = word_contexts[wd["word"]]
        # seeded shuffle ONCE per label so repeated occurrences cycle DIFFERENT real contexts
        # rather than always the first one found.
        if wd["word"] not in ctx_cursor:
            perm = ctx_rng.permutation(len(ctxs))
            ctx_cursor[wd["word"]] = list(perm)
        order = ctx_cursor[wd["word"]]
        idx = order[wi % len(order)] if order else 0
        prev, nxt = ctxs[int(idx) % len(ctxs)]
        word_records.append({
            "wid": wi, "writer": w, "word": wd["word"], "len": len(wd["word"]),
            "key": list(r74.word_key(wd)),
            "rich": rich, "env": env, "chars": chars,
            "context": {"prev": prev, "next": nxt},
        })

    words_per_writer = Counter(wd["writer"] for wd in word_records)
    n_repeat_instances = sum(1 for wd in word_records
                             if sum(1 for o in word_records
                                    if o["writer"] == wd["writer"] and o["word"] == wd["word"]) >= 2)
    return {
        "bg_writers": sorted(bg_writers), "ho_writers": sorted(ho_writers),
        "bg_writers_match_run69": bg_writers_match_run69,
        "test_writers": test_writers,
        "cross_charbank": cross_charbank,
        "cross_bank_by_label": cross_bank_by_label,
        "length_index_cross": {str(k): v for k, v in length_index_cross.items()},
        "n_cross_labels_capped": n_cross_labels_capped,
        "writer_frames": {str(w): fr for w, fr in frame_of_writer.items()},
        "word_records": word_records,
        "n_test_words": len(word_records),
        "n_test_writers": len(test_writers),
        "words_per_writer": {str(w): n for w, n in words_per_writer.items()},
        "repeats_per_writer": {str(w): n for w, n in repeats_by_writer.items()},
        "n_repeat_instances": n_repeat_instances,
        "n_ho_words": len(ho_words),
        "n_excluded_no_brown_context": n_excluded_no_context,
        "n_degenerate_own_frame": n_degenerate_frame,
        "n_word_frame_fallback": n_word_frame_fallback,
        "word_len_dist": dict(Counter(wd["word"].__len__() for wd in word_records)),
        "lm": {"unigram": dict(uni), "bigram": bi_pruned},
        "run61_lexicon_n": len(lexicon["lexicon"]),
    }


def stage_prep():
    print(f"\n{SEP}\n  STAGE: prep (writer/word selection -- repeat-preferring depth -- own "
          f"unsupervised frame + cross word-form bank + oracle context + query canons)\n{SEP}",
          flush=True)
    t0 = time.time()
    md5_before = _seed_guard("prep")
    print(f"  seeds/stroke_shapes.json md5 (before): {md5_before}", flush=True)

    out = build_prep()
    out["stroke_shapes_md5"] = md5_before
    _save(out, _ckpt("prep.json"))
    _seed_guard("prep", md5_before)

    print(f"  bg writers={len(out['bg_writers'])}  ho writers={len(out['ho_writers'])}  "
          f"(match run 69's bg set: {out['bg_writers_match_run69']})", flush=True)
    print(f"  adapt writers (>= {MIN_OWN_WORDS} in-vocab, has-context words; capped at "
          f"{ADAPT_WRITER_CAP} by repeat-depth) = {out['n_test_writers']}  "
          f"total test words = {out['n_test_words']}", flush=True)
    wpw = sorted(out["words_per_writer"].values())
    print(f"  words/writer: min={wpw[0]} median={wpw[len(wpw)//2]} max={wpw[-1]}", flush=True)
    print(f"  REPEAT-WORD instances (>=2 same-writer-same-word, the only substrate a word-FORM "
          f"bank can grow from): {out['n_repeat_instances']}/{out['n_test_words']} = "
          f"{100*out['n_repeat_instances']/out['n_test_words']:.1f}%", flush=True)
    print(f"  words excluded (in lexicon but never seen in reduced-Brown context): "
          f"{out['n_excluded_no_brown_context']}", flush=True)
    print(f"  cross word-form bank: {len(out['cross_bank_by_label'])} labels  "
          f"(labels/length capped at {CROSS_LABEL_CAP_PER_LEN}, {out['n_cross_labels_capped']} "
          f"excess entries dropped)", flush=True)
    print(f"  degenerate own-frame writers: {out['n_degenerate_own_frame']}/{out['n_test_writers']}"
          f"   word-char local-frame fallback: {out['n_word_frame_fallback']}", flush=True)
    print(f"  saved -> {_ckpt('prep.json')}  [prep {time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: read -- THE ONLY NATIVE STAGE. Fixed tables (r73's own performance discipline, one grain
#  up): per-char cross cost (OOV fallback), per-word cross-bank cost (COLD holistic), and the full
#  same-writer whole-word pairwise DTW matrix (rich+env -- the only possible pseudo/true-label
#  exemplar source). Every EM round + the streaming pass is then a pure lookup, no further native
#  calls. Block-checkpointed per writer, resumable.
# ============================================================================================= #
def stage_read():
    print(f"\n{SEP}\n  STAGE: read -- native DTW precompute (per-char cross cost, per-word cross-"
          f"bank cost, same-writer whole-word pairwise matrix)\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("read")
    import substrate_rs as srs
    native = srs.Substrate()._inner
    prep = _require("prep.json")
    cross_charbank = prep["cross_charbank"]
    cross_bank_by_label = prep["cross_bank_by_label"]
    length_index_cross = {int(k): v for k, v in prep["length_index_cross"].items()}
    word_records = prep["word_records"]

    by_writer_words = defaultdict(list)
    for wd in word_records:
        by_writer_words[wd["writer"]].append(wd)
    for w in by_writer_words:
        by_writer_words[w].sort(key=lambda wd: wd["wid"])

    out_path = _ckpt("read.json")
    state = _load(out_path) if os.path.exists(out_path) else {
        "words_done": [], "pairwise_done_writers": [], "words": {}, "pairwise": [], "done": False,
    }
    if state.get("done"):
        print(f"  read already COMPLETE.", flush=True)
        return 0

    deadline = time.time() + PER_CALL_BUDGET_SECONDS
    words_done = set(state["words_done"])
    pairwise_done = set(state["pairwise_done_writers"])
    n_new = 0

    local_idx_of = {}
    writer_local_words = defaultdict(list)
    for w in sorted(by_writer_words):
        li = 0
        for wd in by_writer_words[w]:
            local_idx_of[wd["wid"]] = li
            writer_local_words[w].append(wd["wid"])
            li += 1

    # -- pass 1: per-word cross-bank cost (holistic COLD) + per-char cross cost (OOV fallback). --
    for w in sorted(by_writer_words):
        for wd in by_writer_words[w]:
            key = str(wd["wid"])
            if key in words_done:
                continue
            L = wd["len"]
            same_len = length_index_cross.get(L, [])
            cross_rich, cross_env = {}, {}
            for lab in same_len:
                others = cross_bank_by_label[lab]
                if not others:
                    continue
                cross_rich[lab] = min(cc66.dtw(native, wd["rich"], c["rich"]) for c in others)
                cross_env[lab] = min(cc66.dtw(native, wd["env"], c["env"]) for c in others)
            char_cross = []
            for ch in wd["chars"]:
                invA = r69._class_cost(native, ch["inv"], cross_charbank, "inv")
                poseC = r69._class_cost(native, ch["pose_own"], cross_charbank, "pose")
                char_cross.append([invA[c] + PRIMARY_LAMBDA_POSE * poseC[c] for c in range(26)])
            state["words"][key] = {
                "wid": wd["wid"], "writer": w, "word": wd["word"], "len": L,
                "local_idx": local_idx_of[wd["wid"]],
                "cross_rich": cross_rich, "cross_env": cross_env, "char_cross_rows": char_cross,
                "context": wd["context"],
            }
            words_done.add(key)
            n_new += 1
            if n_new % 15 == 0:
                state["words_done"] = sorted(words_done)
                _save(state, out_path)
                _seed_guard("read", md5_before)
                print(f"    ... words {len(words_done)}  [{time.time()-t0:.1f}s]", flush=True)
                if time.time() > deadline:
                    state["words_done"] = sorted(words_done)
                    state["pairwise_done_writers"] = sorted(pairwise_done)
                    _save(state, out_path)
                    _seed_guard("read", md5_before)
                    print(f"  WALL-BUDGET (word pass) -- re-invoke --stage read.", flush=True)
                    return 2

    state["words_done"] = sorted(words_done)
    _save(state, out_path)
    _seed_guard("read", md5_before)
    print(f"  word pass complete: {len(words_done)} words  [{time.time()-t0:.1f}s]", flush=True)

    # -- pass 2: full same-writer whole-word pairwise DTW (rich+env), one writer at a time. --
    for w in sorted(writer_local_words):
        if w in pairwise_done:
            continue
        wids = writer_local_words[w]
        by_wid = {wd["wid"]: wd for wd in by_writer_words[w]}
        n_local = len(wids)
        for i in range(n_local):
            wi = by_wid[wids[i]]
            for j in range(i + 1, n_local):
                wj = by_wid[wids[j]]
                d_rich = cc66.dtw(native, wi["rich"], wj["rich"])
                d_env = cc66.dtw(native, wi["env"], wj["env"])
                state["pairwise"].append([w, i, j, d_rich, d_env])
        pairwise_done.add(w)
        n_new += 1
        state["pairwise_done_writers"] = sorted(pairwise_done)
        _save(state, out_path)
        _seed_guard("read", md5_before)
        print(f"    ... pairwise writer {w} done ({n_local} words, {len(pairwise_done)}/"
              f"{len(writer_local_words)} writers)  [{time.time()-t0:.1f}s]", flush=True)
        if time.time() > deadline:
            print(f"  WALL-BUDGET (pairwise pass) -- re-invoke --stage read.", flush=True)
            return 2

    state["done"] = True
    _save(state, out_path)
    _seed_guard("read", md5_before)
    print(f"  read COMPLETE: {len(state['words'])} words, {len(state['pairwise'])} pairwise "
          f"entries, {len(pairwise_done)} writers  [{time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  BOOTSTRAP MACHINERY -- pure Python/numpy, lookups into the fixed tables from `read`. Importable
#  by tests without native/real data. Mirrors r73's shape at word grain, LM-context-aware.
# ============================================================================================= #
def build_pairwise_index(pairwise_rows: list) -> dict:
    idx = {}
    for w, i, j, drich, denv in pairwise_rows:
        idx[(w, i, j)] = (drich, denv)
        idx[(w, j, i)] = (drich, denv)
    return idx


class FastAdaptCorpus:
    """Wraps the fixed tables from `read.json`. `lm_score(prev, cur)` is r75's own bigram scorer."""

    def __init__(self, words: dict, pairwise_rows: list, lex_by_len: dict, lm_score, channel="rich"):
        self.channel = channel
        self.lex_by_len = lex_by_len
        self.lm_score = lm_score
        self.pairwise = build_pairwise_index(pairwise_rows)
        self.words = {}       # wid -> record (cross_rich/env dicts, char rows, context, true word).
        for key, rec in words.items():
            self.words[rec["wid"]] = rec

    def writers(self):
        return sorted({r["writer"] for r in self.words.values()})

    def words_of_writer(self, w):
        return sorted((wid for wid, r in self.words.items() if r["writer"] == w))

    def pair_dist(self, w, li, lj) -> float:
        drich, denv = self.pairwise[(w, li, lj)]
        return drich if self.channel == "rich" else denv

    def cross_dict(self, wid) -> dict:
        r = self.words[wid]
        return r["cross_rich"] if self.channel == "rich" else r["cross_env"]

    def pool_dict(self, wid, pool_by_wc: dict, exclude_wid=None) -> dict:
        """label -> min pairwise distance among pool entries for (writer,label), excluding any
        entry sourced from `exclude_wid` (leave-one-out). SAME-LENGTH restricted, mirroring
        `cross_dict`'s own convention (`length_index_cross`) -- without this, a writer with only
        1-2 harvested (possibly wrong-length) labels would force EVERY OTHER word of theirs,
        regardless of true length, to choose among just those labels (`topk_candidates_iam`'s
        within-route never blends with cross/per-char candidates once non-empty) -- a length-blind
        pool caused exactly this catastrophic collapse in an early run (round 0 harvest precision
        78% -> round 1 pooled precision 7.7%, word_acc 30.7%->8.7%, diagnosed and fixed here)."""
        r = self.words[wid]
        w, li, true_len = r["writer"], r["local_idx"], r["len"]
        out = {}
        for (pw, label), entries in pool_by_wc.items():
            if pw != w or len(label) != true_len:
                continue
            cands = [e for e in entries if e["wid"] != exclude_wid]
            if not cands:
                continue
            out[label] = min(self.pair_dist(w, li, e["local_idx"]) for e in cands)
        return out

    def true_word(self, wid) -> str:
        return self.words[wid]["word"]


def fuse_holistic(pool_dict: dict, cross_dict: dict) -> dict:
    """FUSION, not exclusive dispatch (r73's own policy, `min(boot_cost, cross_cost)`, transplanted
    to word-form labels): every label seen in EITHER the writer's own (pseudo-labeled) pool OR the
    generic cross bank stays a competing candidate, at whichever source gives it the lower distance.
    This is the correct policy for a SPARSE, still-growing pool -- r76's own `topk_candidates_iam`
    was built for a MATURE sight-vocabulary bank (real IAM documents, most candidates already
    covered) where "prefer within exclusively once non-empty" is reasonable; here, a pool with only
    1-2 harvested labels would otherwise force EVERY OTHER same-length word by that writer to choose
    among just those labels (diagnosed directly: an early version of this run collapsed round 0's
    78% harvest precision to a 7.7% round-1 catastrophe this way). Fusion can only ADD a competing
    candidate or IMPROVE an existing one's distance -- it can never remove the true label from
    consideration the way exclusive dispatch did."""
    if not pool_dict and not cross_dict:
        return {}
    out = dict(cross_dict)
    for label, d in pool_dict.items():
        out[label] = min(d, out[label]) if label in out else d
    return out


def decode_one(corpus: FastAdaptCorpus, wid: int, pool_dict: dict, lm_weight: float,
              visual_weight: float, K: int = BEAM_K) -> dict:
    """The unified decoder every condition (cold/ceiling/bootstrapped, isolated/oracle-context)
    shares -- only `pool_dict`, `lm_weight`, `visual_weight` differ across conditions."""
    r = corpus.words[wid]
    rows = r["char_cross_rows"]
    cross_dict = corpus.cross_dict(wid)
    fused = fuse_holistic(pool_dict, cross_dict)
    cand_words, vscores = r76.topk_candidates_iam(rows, corpus.lex_by_len, fused, {},
                                                   bool(fused), K)
    if len(cand_words) == 0:
        return {"pred": "", "margin": 0.0, "visual_pred": "", "n_cands": 0}
    vnorm = r76._normalize_visual([vscores])[0]
    prev, nxt = r["context"]["prev"], r["context"]["next"]
    lm_scores = np.array([corpus.lm_score(prev, c) + corpus.lm_score(c, nxt) for c in cand_words])
    combined = lm_weight * lm_scores + visual_weight * vnorm
    order = np.argsort(-combined)
    best_i = int(order[0])
    second = float(combined[order[1]]) if len(order) > 1 else -math.inf
    margin = float(combined[best_i]) - second if math.isfinite(second) else math.inf
    visual_pred = cand_words[int(np.argmax(vnorm))]
    return {"pred": cand_words[best_i], "margin": margin, "visual_pred": visual_pred,
           "n_cands": len(cand_words)}


def harvest_ok(dec: dict, margin_threshold: float) -> bool:
    """THE HARVEST RULE (see module docstring): prediction-dominant pick agrees with the
    visual-only pick, AND the margin clears the pre-registered (round-0 percentile) threshold."""
    if dec["n_cands"] == 0 or not dec["pred"]:
        return False
    return dec["pred"] == dec["visual_pred"] and dec["margin"] >= margin_threshold


def _acc_for(corpus: FastAdaptCorpus, wid: int, pred: str) -> tuple:
    true = corpus.true_word(wid)
    n = min(len(pred), len(true))
    c_ok = sum(1 for i in range(n) if pred[i] == true[i])
    return c_ok, len(true), int(pred == true)


def compute_margin_threshold(corpus: FastAdaptCorpus, pctl: float, lm_weight: float,
                             visual_weight: float) -> float:
    """PRE-REGISTRATION: fixed from round-0's (empty-pool) margin distribution alone."""
    margins = []
    for wid in corpus.words:
        dec = decode_one(corpus, wid, {}, lm_weight, visual_weight)
        if dec["n_cands"] > 1 and math.isfinite(dec["margin"]):
            margins.append(dec["margin"])
    if not margins:
        return 0.0
    return float(np.percentile(margins, pctl))


def cold_and_ceiling_reports(corpus: FastAdaptCorpus, lm_weight: float, visual_weight: float) -> dict:
    """COLD (empty pool) and CEILING (TRUE-label own-vocabulary pool, leave-one-out) -- the two
    ends of the ladder the bootstrap loop is measured against."""
    true_pool = defaultdict(list)
    for wid, r in corpus.words.items():
        true_pool[(r["writer"], r["word"])].append({"wid": wid, "local_idx": r["local_idx"]})

    def _report(pool_fn):
        char_ok = char_n = word_ok = word_n = 0
        flags = []
        for wid in corpus.words:
            pool = pool_fn(wid)
            dec = decode_one(corpus, wid, pool, lm_weight, visual_weight)
            c_ok, c_n, w_ok = _acc_for(corpus, wid, dec["pred"])
            char_ok += c_ok
            char_n += c_n
            word_ok += w_ok
            word_n += 1
            flags.append(bool(w_ok))
        return {"char_acc": char_ok / char_n if char_n else 0.0,
               "word_acc": word_ok / word_n if word_n else 0.0,
               "char_n": char_n, "word_n": word_n, "word_ok": word_ok, "flags": flags}

    cold = _report(lambda wid: {})

    def _ceiling_pool(wid):
        r = corpus.words[wid]
        entries = [e for e in true_pool[(r["writer"], r["word"])] if e["wid"] != wid]
        return {r["word"]: min(corpus.pair_dist(r["writer"], r["local_idx"], e["local_idx"])
                               for e in entries)} if entries else {}

    ceiling = _report(_ceiling_pool)
    return {"cold": cold, "ceiling": ceiling}


def run_em(corpus: FastAdaptCorpus, margin_threshold: float, lm_weight: float, visual_weight: float,
          max_rounds: int = MAX_ROUNDS) -> dict:
    """Round-based EM, leave-one-word-out (r73's own anti-circularity guard)."""
    pool_by_wc: dict = {}
    rounds = []
    harvested_keys = set()
    for rnd in range(max_rounds):
        char_ok = char_n = word_ok = word_n = 0
        new_this_round = []
        hp_ok = hp_n = 0
        for wid, wrec in corpus.words.items():
            w = wrec["writer"]
            pool = corpus.pool_dict(wid, pool_by_wc, exclude_wid=wid)
            dec = decode_one(corpus, wid, pool, lm_weight, visual_weight)
            c_ok, c_n, w_ok = _acc_for(corpus, wid, dec["pred"])
            char_ok += c_ok
            char_n += c_n
            word_ok += w_ok
            word_n += 1
            if harvest_ok(dec, margin_threshold):
                hk = (w, dec["pred"], wid)
                true = wrec["word"]
                if hk not in harvested_keys:
                    harvested_keys.add(hk)
                    new_this_round.append((w, dec["pred"], wid, wrec["local_idx"], dec["margin"]))
                hp_n += 1
                hp_ok += int(dec["pred"] == true)
        for w, label, wid, li, margin in new_this_round:
            r73._pool_add(pool_by_wc, w, label, wid, li, margin, cap=M_BOOT_WORD)
        coverage = sum(1 for lst in pool_by_wc.values() if lst)
        rounds.append({
            "round": rnd, "char_acc": char_ok / char_n if char_n else 0.0,
            "word_acc": word_ok / word_n if word_n else 0.0,
            "char_ok": char_ok, "char_n": char_n, "word_ok": word_ok, "word_n": word_n,
            "n_new_harvested_words": len(new_this_round),
            "harvest_precision": (hp_ok / hp_n if hp_n else None), "harvest_n": hp_n,
            "pool_coverage_writer_label": coverage,
        })
        if len(new_this_round) == 0:
            break
    return {"rounds": rounds, "converged_at": rounds[-1]["round"],
            "hit_max_rounds": len(rounds) == max_rounds and rounds[-1]["n_new_harvested_words"] > 0,
            "final_pool_size": sum(len(v) for v in pool_by_wc.values())}


def run_streaming(corpus: FastAdaptCorpus, margin_threshold: float, lm_weight: float,
                  visual_weight: float, n_order_seeds: int = N_ORDER_SEEDS) -> dict:
    """Strictly causal, single-pass, per-writer streaming read -- THE WARM-UP CURVE."""
    by_pos = defaultdict(lambda: {"char_ok": 0, "char_n": 0, "word_ok": 0, "word_n": 0})
    for seed in range(n_order_seeds):
        for w in corpus.writers():
            wids = corpus.words_of_writer(w)
            rng = np.random.default_rng(seed * 100003 + w)
            order = rng.permutation(len(wids))
            pool_by_wc: dict = {}
            for k, oi in enumerate(order):
                wid = wids[int(oi)]
                pool = corpus.pool_dict(wid, pool_by_wc, exclude_wid=None)   # causal: only earlier.
                dec = decode_one(corpus, wid, pool, lm_weight, visual_weight)
                c_ok, c_n, w_ok = _acc_for(corpus, wid, dec["pred"])
                slot = by_pos[k]
                slot["char_ok"] += c_ok
                slot["char_n"] += c_n
                slot["word_ok"] += w_ok
                slot["word_n"] += 1
                if harvest_ok(dec, margin_threshold):
                    r73._pool_add(pool_by_wc, w, dec["pred"], wid, corpus.words[wid]["local_idx"],
                                 dec["margin"], cap=M_BOOT_WORD)
    curve = []
    for k in sorted(by_pos):
        s = by_pos[k]
        curve.append({"position": k, "n_words": s["word_n"],
                     "char_acc": s["char_ok"] / s["char_n"] if s["char_n"] else 0.0,
                     "word_acc": s["word_ok"] / s["word_n"] if s["word_n"] else 0.0})
    return {"curve": curve, "n_order_seeds": n_order_seeds}


def isolated_vs_oracle_context(corpus: FastAdaptCorpus, visual_weight: float) -> dict:
    """Sanity control BEFORE any bootstrapping: at the COLD (empty-pool) state, how much does
    ADDING the oracle sentence context lift reading over visual-only (LM weight zeroed)? Reproduces
    run 75's own "prediction lift" finding directionally on this run's instances."""
    def _rep(lm_w):
        char_ok = char_n = word_ok = word_n = 0
        flags = []
        for wid in corpus.words:
            dec = decode_one(corpus, wid, {}, lm_w, visual_weight)
            c_ok, c_n, w_ok = _acc_for(corpus, wid, dec["pred"])
            char_ok += c_ok
            char_n += c_n
            word_ok += w_ok
            word_n += 1
            flags.append(bool(w_ok))
        return {"char_acc": char_ok / char_n if char_n else 0.0,
               "word_acc": word_ok / word_n if word_n else 0.0, "word_n": word_n,
               "word_ok": word_ok, "flags": flags}
    return {"isolated": _rep(0.0), "oracle_context": _rep(LM_WEIGHT)}


# ============================================================================================= #
#  STAGE: bootstrap -- pure Python, no native calls (lookups into `read.json`'s tables).
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
    lex_by_len = r75.build_lex_by_len(lexicon["lexicon"])
    lm_score = r75.make_lm_scorer(prep["lm"]["unigram"], prep["lm"]["bigram"], lexicon["logfreq"])

    corpus = FastAdaptCorpus(rd["words"], rd["pairwise"], lex_by_len, lm_score, channel="rich")
    corpus_env = FastAdaptCorpus(rd["words"], rd["pairwise"], lex_by_len, lm_score, channel="env")
    print(f"  corpus: {len(corpus.words)} words, {len(corpus.writers())} writers  "
          f"[{time.time()-t0:.1f}s]", flush=True)

    isolated_check = isolated_vs_oracle_context(corpus, PRIMARY_VISUAL_WEIGHT)
    iso, orc = isolated_check["isolated"], isolated_check["oracle_context"]
    print(f"  SANITY (cold, before bootstrap): isolated(no context) word={100*iso['word_acc']:.1f}%"
          f"  oracle-context word={100*orc['word_acc']:.1f}%  "
          f"lift={100*(orc['word_acc']-iso['word_acc']):+.1f}pp", flush=True)

    margin_thr = compute_margin_threshold(corpus, MARGIN_PCTL_PRIMARY, LM_WEIGHT,
                                          PRIMARY_VISUAL_WEIGHT)
    margin_thr_robust = {p: compute_margin_threshold(corpus, p, LM_WEIGHT, PRIMARY_VISUAL_WEIGHT)
                         for p in MARGIN_PCTL_ROBUST}
    print(f"  PRIMARY margin threshold (median of round-0 finite margins) = {margin_thr:.4f}  "
          f"(robustness: {margin_thr_robust})", flush=True)

    cc = cold_and_ceiling_reports(corpus, LM_WEIGHT, PRIMARY_VISUAL_WEIGHT)
    print(f"  COLD    : char={100*cc['cold']['char_acc']:.1f}%  word={100*cc['cold']['word_acc']:.1f}%"
          f"  (n={cc['cold']['word_n']})", flush=True)
    print(f"  CEILING : char={100*cc['ceiling']['char_acc']:.1f}%  "
          f"word={100*cc['ceiling']['word_acc']:.1f}%  (n={cc['ceiling']['word_n']})", flush=True)

    cc_env = cold_and_ceiling_reports(corpus_env, LM_WEIGHT, PRIMARY_VISUAL_WEIGHT)
    print(f"  (ablation, envelope channel) COLD word={100*cc_env['cold']['word_acc']:.1f}%  "
          f"CEILING word={100*cc_env['ceiling']['word_acc']:.1f}%", flush=True)

    em_primary = run_em(corpus, margin_thr, LM_WEIGHT, PRIMARY_VISUAL_WEIGHT)
    print(f"  EM (primary rule) converged at round {em_primary['converged_at']} "
          f"(hit_max_rounds={em_primary['hit_max_rounds']})  [{time.time()-t0:.1f}s]", flush=True)
    for rr in em_primary["rounds"]:
        hp = f"{100*rr['harvest_precision']:.1f}%" if rr["harvest_precision"] is not None else "n/a"
        print(f"    round {rr['round']}: char={100*rr['char_acc']:.1f}% word={100*rr['word_acc']:.1f}% "
              f"new_harvested_words={rr['n_new_harvested_words']} harvest_precision={hp} "
              f"(n={rr['harvest_n']}) pool_coverage={rr['pool_coverage_writer_label']}", flush=True)

    em_robust = {}
    for p, thr in margin_thr_robust.items():
        em_robust[f"pctl{p}"] = {"em": run_em(corpus, thr, LM_WEIGHT, PRIMARY_VISUAL_WEIGHT),
                                 "cold_ceiling": cc}    # same visual_weight as primary -> same anchors.
    for vw in VISUAL_WEIGHTS:
        if vw == PRIMARY_VISUAL_WEIGHT:
            continue
        thr_vw = compute_margin_threshold(corpus, MARGIN_PCTL_PRIMARY, LM_WEIGHT, vw)
        cc_vw = cold_and_ceiling_reports(corpus, LM_WEIGHT, vw)
        em_robust[f"vw{vw}"] = {"em": run_em(corpus, thr_vw, LM_WEIGHT, vw), "cold_ceiling": cc_vw}
    print(f"  robustness EM variants computed  [{time.time()-t0:.1f}s]", flush=True)
    print(f"  VISUAL-WEIGHT SWEEP (own cold/ceiling anchors per weight, primary="
          f"{PRIMARY_VISUAL_WEIGHT} marked *):")
    for vw in VISUAL_WEIGHTS:
        mark = "*" if vw == PRIMARY_VISUAL_WEIGHT else " "
        cc_v = cc if vw == PRIMARY_VISUAL_WEIGHT else em_robust[f"vw{vw}"]["cold_ceiling"]
        rf = (em_primary if vw == PRIMARY_VISUAL_WEIGHT else em_robust[f"vw{vw}"]["em"])["rounds"][-1]
        print(f"    vw={vw:>5.2f}{mark}  cold={100*cc_v['cold']['word_acc']:>5.1f}%  "
              f"ceiling={100*cc_v['ceiling']['word_acc']:>5.1f}%  "
              f"converged={100*rf['word_acc']:>5.1f}%", flush=True)

    warmup = run_streaming(corpus, margin_thr, LM_WEIGHT, PRIMARY_VISUAL_WEIGHT)
    print(f"  warm-up streaming curve computed ({len(warmup['curve'])} positions, "
          f"{N_ORDER_SEEDS} order seeds)  [{time.time()-t0:.1f}s]", flush=True)
    for row in warmup["curve"][:12]:
        print(f"    pos {row['position']:>3}: n={row['n_words']:>4}  char={100*row['char_acc']:.1f}%"
              f"  word={100*row['word_acc']:.1f}%", flush=True)

    out = {
        "isolated_vs_oracle_context": isolated_check,
        "margin_threshold_primary": margin_thr, "margin_threshold_robust": margin_thr_robust,
        "cold": cc["cold"], "ceiling": cc["ceiling"],
        "cold_env": cc_env["cold"], "ceiling_env": cc_env["ceiling"],
        "em_primary": em_primary, "em_robust": em_robust, "warmup": warmup,
        "n_words": len(corpus.words), "n_writers": len(corpus.writers()),
    }
    _save(out, _ckpt("bootstrap.json"))
    _seed_guard("bootstrap", md5_before)
    print(f"  saved -> {_ckpt('bootstrap.json')}  [{time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: summary -- harvest PRECISION vs run 73's 29%; the WARM-UP CURVE; % of cold->ceiling gap
#  closed vs run 73's -3%; the does-fast-adaptation-work-now VERDICT.
# ============================================================================================= #
def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 77 SCOREBOARD (FAST WRITER-ADAPTATION, PREDICTION-"
          f"SEEDED)\n{SEP}", flush=True)
    md5_now = _seed_guard("summary")
    prep = _require("prep.json")
    print(f"  SEED-GUARD: seeds/stroke_shapes.json md5 = {md5_now}  "
          f"(== prep capture {prep['stroke_shapes_md5']}: "
          f"{md5_now == prep['stroke_shapes_md5']})")
    boot = _require("bootstrap.json")
    n_words, n_writers = boot["n_words"], boot["n_writers"]
    print(f"\n  n test words = {n_words}  n adapt writers = {n_writers}")
    print(f"  repeat-word coverage: {prep['n_repeat_instances']}/{prep['n_test_words']} = "
          f"{100*prep['n_repeat_instances']/prep['n_test_words']:.1f}% (the substrate a word-FORM "
          f"bank can grow from)")
    print(f"  calibration -- run 69 within/cross char: {RUN69_WITHIN_CHAR:.1f}%/{RUN69_CROSS_CHAR:.1f}%"
          f"  |  run 70 within/cross word: {RUN70_WITHIN_WORD:.1f}%/{RUN70_CROSS_WORD:.1f}%  |  "
          f"run 74 within-holistic word: {RUN74_WITHIN_HOLISTIC:.1f}%  |  run 75 GOLD sentence word: "
          f"{RUN75_GOLD_WORD:.1f}%  |  run 73 harvest precision: {RUN73_HARVEST_PRECISION:.1f}%  "
          f"gap closed: {RUN73_GAP_CLOSED:+.1f}%")

    iso_ck = boot["isolated_vs_oracle_context"]
    iso, orc = iso_ck["isolated"], iso_ck["oracle_context"]
    print(f"\n  === SANITY CHECK (cold, pre-bootstrap): does prediction lift COLD reading at all? ===")
    print(f"  isolated (no context) word_acc = {100*iso['word_acc']:.1f}%")
    print(f"  oracle-context word_acc        = {100*orc['word_acc']:.1f}%   "
          f"lift = {100*(orc['word_acc']-iso['word_acc']):+.1f}pp   (run 75's own isolated->gold "
          f"lift was +{RUN75_GOLD_WORD-26.0:.1f}pp on synthetic sentences, directional citation)")

    cold, ceiling = boot["cold"], boot["ceiling"]
    cold_env, ceiling_env = boot["cold_env"], boot["ceiling_env"]
    rounds = boot["em_primary"]["rounds"]
    final = rounds[-1]
    print(f"\n  === THE WARM-UP CURVE (EM rounds, leave-one-word-out) ===")
    hdr = f"  {'round':>6}{'char_acc':>10}{'word_acc':>10}{'new_pseudo_words':>18}" \
          f"{'harvest_prec':>14}{'harvest_n':>11}{'pool_cov':>10}"
    print(hdr)
    for rr in rounds:
        hp = f"{100*rr['harvest_precision']:.1f}%" if rr["harvest_precision"] is not None else "n/a"
        print(f"  {rr['round']:>6}{100*rr['char_acc']:>9.1f}%{100*rr['word_acc']:>9.1f}%"
              f"{rr['n_new_harvested_words']:>18}{hp:>14}{rr['harvest_n']:>11}"
              f"{rr['pool_coverage_writer_label']:>10}")
    print(f"\n  COLD (round-0-equivalent, cross bank + oracle context): char={100*cold['char_acc']:.1f}%"
          f" word={100*cold['word_acc']:.1f}%")
    print(f"  CONVERGED (round {final['round']}, bootstrapped bank): char={100*final['char_acc']:.1f}% "
          f"word={100*final['word_acc']:.1f}%")
    print(f"  CEILING (real own-vocabulary bank, never fed to decode): char={100*ceiling['char_acc']:.1f}%"
          f" word={100*ceiling['word_acc']:.1f}%")
    print(f"  (ablation, envelope channel) COLD word={100*cold_env['word_acc']:.1f}%  CEILING word="
          f"{100*ceiling_env['word_acc']:.1f}%")

    def _gap_close(cold_v, final_v, ceil_v):
        span = ceil_v - cold_v
        return (final_v - cold_v) / span if abs(span) > 1e-9 else float("nan")

    gap_char = _gap_close(cold["char_acc"], final["char_acc"], ceiling["char_acc"])
    gap_word = _gap_close(cold["word_acc"], final["word_acc"], ceiling["word_acc"])
    print(f"\n  GAP CLOSED (char): {100*gap_char:.1f}%   GAP CLOSED (word): {100*gap_word:.1f}%   "
          f"(bar: >= {100*GAP_CLOSE_BAR:.0f}%; run 73's own number here was {RUN73_GAP_CLOSED:+.1f}%)")

    ci_cold = _wilson(cold["word_ok"], cold["word_n"])
    ci_final = _wilson(final["word_ok"], final["word_n"])
    sep_above_cold = ci_final[0] > cold["word_acc"]

    # -- THE CRUX: harvest precision, pooled across all rounds that harvested anything. --
    hp_ok_total = sum(rr["harvest_n"] * (rr["harvest_precision"] or 0.0) for rr in rounds
                      if rr["harvest_precision"] is not None)
    hp_n_total = sum(rr["harvest_n"] for rr in rounds if rr["harvest_precision"] is not None)
    pooled_precision = 100 * hp_ok_total / hp_n_total if hp_n_total else float("nan")
    precision_ci = _wilson(int(round(hp_ok_total)), hp_n_total) if hp_n_total else (float("nan"),) * 2
    precision_win = hp_n_total > 0 and pooled_precision > HARVEST_PRECISION_BAR

    print(f"\n  === THE CRUX: HARVEST PRECISION (prediction-dominant judge vs run 73's weak one) ===")
    print(f"  pooled harvest precision = {pooled_precision:.1f}% CI=[{100*precision_ci[0]:.1f},"
          f"{100*precision_ci[1]:.1f}]  (n={hp_n_total} harvested-word decisions across all rounds)")
    print(f"  run 73's own number: {RUN73_HARVEST_PRECISION:.1f}%   "
          f"materially above (bar {HARVEST_PRECISION_BAR:.0f}%)? {precision_win}")

    win = precision_win and (gap_word >= GAP_CLOSE_BAR) and sep_above_cold
    print(f"\n  MILESTONE (pre-registered: harvest precision materially > {RUN73_HARVEST_PRECISION:.0f}%"
          f" AND converged word acc closes >= {100*GAP_CLOSE_BAR:.0f}% of cold->ceiling AND is "
          f"CI-separated above cold):")
    print(f"    cold word_acc      = {100*cold['word_acc']:.1f}%  CI=[{100*ci_cold[0]:.1f},"
          f"{100*ci_cold[1]:.1f}]")
    print(f"    converged word_acc = {100*final['word_acc']:.1f}%  CI=[{100*ci_final[0]:.1f},"
          f"{100*ci_final[1]:.1f}]  (CI-separated above cold? {sep_above_cold})")
    print(f"    ceiling word_acc   = {100*ceiling['word_acc']:.1f}%")
    print(f"    VERDICT: {'WIN -- prediction-seeded harvesting now works: reliable seeds AND a real warm-up' if win else 'NULL -- see localization below'}")
    if not win:
        if not precision_win:
            print(f"    LOCALIZE: harvest precision ({pooled_precision:.1f}%) did not clear the bar "
                  f"-- the prediction-dominant reader is STILL not a reliable enough judge on this "
                  f"corpus/sample (same failure MODE as run 73, possibly a higher baseline).")
        elif gap_word < GAP_CLOSE_BAR:
            print(f"    LOCALIZE: harvest precision cleared the bar (seeds are RELIABLE) but the "
                  f"gap did not close enough -- localize to SEED SPARSITY: repeat-word coverage is "
                  f"only {100*prep['n_repeat_instances']/prep['n_test_words']:.1f}% (a word-FORM "
                  f"bank can only help words the writer repeats) -- a corpus-structure limit, not a "
                  f"mechanism failure.")
        if not sep_above_cold:
            print(f"    LOCALIZE: converged word_acc CI overlaps cold -- the lift, if any, is not "
                  f"statistically distinguishable from noise at this sample size.")

    # -- drift check. --
    precisions = [rr["harvest_precision"] for rr in rounds if rr["harvest_precision"] is not None]
    drift = len(precisions) >= 2 and precisions[-1] < precisions[0] - 0.10
    print(f"\n  DRIFT CHECK: per-round harvested-pseudo-label precision = "
          f"{[f'{100*p:.1f}%' for p in precisions]}")
    print(f"    DRIFT DETECTED (final round precision fell >10pp below round-0)? {drift}")

    # -- robustness (each variant scored against ITS OWN cold/ceiling anchors -- visual-weight
    #    variants have a DIFFERENT decode policy than the primary, so their cold/ceiling differ
    #    too; margin-percentile variants share the primary's visual weight, so they share its
    #    cold/ceiling exactly). --
    print(f"\n  ROBUSTNESS (not cherry-picked -- alternate margin percentile / visual-weight bars, "
          f"each scored against ITS OWN cold/ceiling anchors):")
    for label, variant in boot["em_robust"].items():
        rf = variant["em"]["rounds"][-1]
        cc_v = variant["cold_ceiling"]
        gw = _gap_close(cc_v["cold"]["word_acc"], rf["word_acc"], cc_v["ceiling"]["word_acc"])
        hp = rf["harvest_precision"]
        hp_s = f"{100*hp:.1f}%" if hp is not None else "n/a"
        print(f"    {label:<10} cold={100*cc_v['cold']['word_acc']:.1f}%  "
              f"ceiling={100*cc_v['ceiling']['word_acc']:.1f}%  converged (round {rf['round']})="
              f"{100*rf['word_acc']:.1f}%  gap_closed(word)={100*gw:.1f}%  "
              f"last-round harvest_precision={hp_s}")

    # -- warm-up curve headline. --
    curve = boot["warmup"]["curve"]
    print(f"\n  WARM-UP CURVE (streaming, causal, {boot['warmup']['n_order_seeds']} order seeds "
          f"averaged) -- accuracy AS A FUNCTION OF WORDS-READ:")
    hdr2 = f"  {'position':>9}{'n_words':>9}{'char_acc':>10}{'word_acc':>10}"
    print(hdr2)
    for row in curve:
        print(f"  {row['position']:>9}{row['n_words']:>9}{100*row['char_acc']:>9.1f}%"
              f"{100*row['word_acc']:>9.1f}%")
    first_n = min(5, len(curve))
    last_n = min(5, len(curve))
    first5 = curve[:first_n]
    last5 = curve[-last_n:]
    words_to_warm_up = None
    if first5 and last5:
        early_word = np.mean([r["word_acc"] for r in first5])
        late_word = np.mean([r["word_acc"] for r in last5])
        print(f"\n  early (first {first_n} positions) word_acc = {100*early_word:.1f}%   "
              f"late (last {last_n} positions) word_acc = {100*late_word:.1f}%   "
              f"lift = {100*(late_word-early_word):+.1f}pp")
        # first position whose word_acc CI lower bound clears the early mean -- an operational
        # "does it click" indicator, reported honestly if it never does.
        for row in curve:
            lo, _hi = _wilson(int(round(row["word_acc"] * row["n_words"])), row["n_words"])
            if row["position"] >= 3 and lo > early_word:
                words_to_warm_up = row["position"]
                break
        print(f"  words-to-warm-up (first position >=3 whose Wilson-lower CI clears the early-"
              f"position mean): {words_to_warm_up if words_to_warm_up is not None else 'NEVER within '
              + str(len(curve)) + ' positions -- no detectable click'}")

    print(f"\n  ANOMALIES / HONEST RESIDUALS:")
    print(f"    given char+word segmentation throughout (measures the reading/adaptation stack, "
          f"not segmentation discovery) -- this arc's own standing convention.")
    print(f"    SENTENCE CONTEXT IS ORACLE (true neighboring words, not jointly-decoded ink from "
          f"other writers) -- a deliberate reduction isolating the ADAPTATION question from the "
          f"already-answered joint-sentence-decode question (runs 75/76); see module docstring.")
    print(f"    words/writer distribution: min={min(int(v) for v in prep['words_per_writer'].values())}"
          f" median-ish sample: {sorted(Counter(prep['words_per_writer']).items())[:5]} ... "
          f"(min {MIN_OWN_WORDS}, cap {CAP_OWN_WORDS})")
    print(f"    words excluded for no reduced-Brown context: {prep['n_excluded_no_brown_context']}")
    print(f"    cross word-form bank labels/length capped at {CROSS_LABEL_CAP_PER_LEN} "
          f"({prep['n_cross_labels_capped']} excess entries dropped -- a compute bound, not tuned "
          f"to the outcome).")
    print(f"    pool coverage at convergence: {final['pool_coverage_writer_label']} (writer,label) "
          f"cells -- bootstrap can never exceed what confident harvests actually cover.")
    print(f"    per-CHAR route stays FIXED at the cold cross-bank throughout (only the WORD-FORM "
          f"bank grows) -- an explicitly scoped-out optional extension (task's own 'letterforms "
          f"optional'), not attempted here.")

    _save({"cold": cold, "ceiling": ceiling, "final_round": final,
          "gap_closed_char": gap_char, "gap_closed_word": gap_word,
          "harvest_precision_pooled": pooled_precision, "precision_win": precision_win,
          "win": win, "drift": drift, "words_to_warm_up": words_to_warm_up,
          "margin_threshold_primary": boot["margin_threshold_primary"]}, _ckpt("summary.json"))
    _seed_guard("summary", md5_now)
    print(f"\n  saved -> {_ckpt('summary.json')}")
    print(f"\n{SEP}\n  RUN 77 COMPLETE -- see final agent report.\n{SEP}", flush=True)
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True, choices=["prep", "read", "bootstrap", "summary"])
    args = p.parse_args()
    return {"prep": stage_prep, "read": stage_read, "bootstrap": stage_bootstrap,
            "summary": stage_summary}[args.stage]()


if __name__ == "__main__":
    sys.exit(main())
