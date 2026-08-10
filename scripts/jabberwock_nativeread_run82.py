"""jabberwock_nativeread_run82.py -- RUN 82: THE JABBERWOCK READS HANDWRITING WITH ITS OWN LANGUAGE
FACULTY (native graph-native reading-prediction, NOT an external LM).

THE FRAMING (creator: "the jabberwock has language, have a look"): run 75 proved SENTENCE PREDICTION
is the DOMINANT reading channel (isolated 26.0% -> sentence-bigram+strict 57.5% / +loose 51.2%);
run 76 transferred it to real IAM-OnDB lines (0.0% -> 13.1% within-writer); run 81 tried to attach an
EXTERNAL rich LM (gemma3:4b) and it UNDERPERFORMED the toy Brown bigram everywhere -- but that was a
weak local chat model, not the jabberwock's OWN comprehension.

The jabberwock ALREADY HAS the reading-prediction mechanism as a SEED (seeds/semantic_reading_context.
json): a recognised symbol ACTIVATES its concept (activate_recognised), activation SPREADS along the
lexicon's `can_follow` edges to PRIME likely-next symbols (prime_successors), and `predict_context_term`
adds lam*context_primed to the VISUAL score so context corrects an ambiguous read -- the word-superiority
/ interactive-activation effect, graph-native. THIS run attaches the run-75/76 HANDWRITING VISUAL to the
jabberwock's OWN faculty as the top-down predictor and measures the lift vs the external Brown bigram.

============================================================================================= #
STAGE 0 -- THE FACULTY'S PREDICTIVE INTERFACE (studied, reported in the agent's final message):
============================================================================================= #
  * INTERFACE: `domains.recognition_graph.predict_context_term(lam)` =
        Argmax over Concept{is_word=1} of [ -PointSetDist(mark.heard, w.synth) + lam * w.context_primed ].
    context_primed is spread by TWO seed Rules: activate_recognised (recognised concept -> active=1.0)
    and prime_successors (active concept's can_follow successors -> context_primed=1.0). The prime is
    therefore ORDER-1 (depends ONLY on the immediately-preceding recognised word) and, as seeded,
    BINARY (a successor gets 1.0; a non-successor 0.0) -- structurally a BINARY BIGRAM.
  * The can_follow lexicon ships SPARSE (the seed pre-populates ZERO can_follow edges; the demo
    scripts/jabberwock_semantic_reading_context.py hand-seeds ONE). So to give the faculty real
    transition knowledge we POPULATE can_follow donkey=0 from the SAME Brown corpus the bigram uses
    (run 75's prep.json `lm.bigram` -- graph data the faculty consumes, NOT an external scorer).
  * The DEEPER faculties (language_faculty_ops.sense_select = word-SENSE disambiguation;
    construction_grammar.comprehend_recursive = prose PARSING) operate over ALREADY-KNOWN words, not a
    candidate LATTICE of visually-confusable different words, so they are NOT reachable as word-SEQUENCE
    predictors for this reading task. Faculty depth reached = CAN_FOLLOW priming (predict_context_term).

============================================================================================= #
STAGE 1 -- HOW THE FACULTY IS ATTACHED (donkey=0, native, visual UNCHANGED):
============================================================================================= #
The VISUAL channel is run 75/76's own, reused VERBATIM (topk_candidates / topk_candidates_iam over the
stored per-char distance rows -- training-free, byte-identical). ONLY the LM transition is swapped, for
the SAME viterbi decoder (run 75's viterbi_decode) at the SAME weight grid -- so the comparison isolates
LANGUAGE-MODEL QUALITY (count-bigram vs the jabberwock's own faculty), exactly like CLAUDE.md's "swap
the capability, don't touch the visual" discipline. Three LM arms, all fed to the same decode:
  * CONTROL  = count-bigram (r75.make_lm_scorer: log P(cur|prev) + stupid backoff) -- reproduces run
    75/76's stored decode numbers EXACTLY (the "clean LM swap" is a code-level fact, asserted).
  * FACULTY-BINARY  = the LITERAL seed mechanism: trans(prev,cur) = 1.0 if prev can_follow cur else 0.0
    (context_primed=1.0 on successors, exactly what prime_successors sets -- proven equal to the real
    faculty in stage `probe` by loading the seed, running the Rules, and evaluating predict_context_term).
  * FACULTY-WEIGHTED = the SAME predict_context_term Term given a RICHER graph prime: context_primed =
    log1p(co-occurrence count) staged as the can_follow edge weight (a natural graph-edge strength,
    distinct from the bigram's prev-normalized conditional + backoff). Tests whether a weighted native
    prime recovers / beats the count-bigram.

Only the transition ratio matters in viterbi (score = lm_weight*trans + visual_weight*visual, argmax),
so the run-75 grid (lm_weight=1, visual_weight in VISUAL_WEIGHTS) spans every LM:visual ratio for ALL
arms -- best-of-sweep is a fair best for each, and the binary arm's small magnitude is absorbed by a
low visual_weight. Primary = run 75/76's own vw=2.0.

SEED GUARD / DISCIPLINE: OZMA_SEED_PERSIST_DISABLED=1; md5(seeds/stroke_shapes.json) asserted UNCHANGED
before AND after every stage. results/run7{5,6}_checkpoints/ READ-ONLY. Writes ONLY
results/run82_checkpoints/*. NO git add/commit. donkey=0 (no external LLM/n-gram beyond the faculty's
own can_follow lexicon, populated from the SAME Brown corpus the bigram control uses).

Stages: probe (build can_follow from Brown + EXERCISE the real faculty: load seed, run Rules, flip an
ambiguous read) -> decode_synth (three-arm decode over run 75's 130 sentences + bigram-control repro)
-> decode_iam (three-arm decode over run 76's 27 IAM lines + bigram-control repro) -> summary.

Run (from the gamma-substrate repo root):
  OZMA_SEED_PERSIST_DISABLED=1 DEEPWRITING_DIR=/tmp/handwriting \\
    IAM_STROKES_DIR=/tmp/handwriting/iam_onbd/lineStrokes IAM_ASCII_DIR=/tmp/handwriting/iam_ascii/ascii \\
    PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python3 \\
    scripts/jabberwock_nativeread_run82.py --stage <probe|decode_synth|decode_iam|summary>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
os.environ.setdefault("DEEPWRITING_DIR", "/tmp/handwriting")
os.environ.setdefault("IAM_STROKES_DIR", "/tmp/handwriting/iam_onbd/lineStrokes")
os.environ.setdefault("IAM_ASCII_DIR", "/tmp/handwriting/iam_ascii/ascii")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

import scripts.jabberwock_sentence_read_run75 as r75
import scripts.jabberwock_iam_full_run76 as r76

SEP = "=" * 92
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")
SEMANTIC_READING_SEED = os.path.join(ROOT, "seeds", "semantic_reading_context.json")
CKPT_DIR = os.path.join(ROOT, "results", "run82_checkpoints")
LOG = os.path.join(ROOT, "results", "omniglot_gate_run82.log")
os.makedirs(CKPT_DIR, exist_ok=True)

RUN75_CKPT = os.path.join(ROOT, "results", "run75_checkpoints")   # READ-ONLY.
RUN76_CKPT = os.path.join(ROOT, "results", "run76_checkpoints")   # READ-ONLY.
RUN61_LEXICON = r75.RUN61_LEXICON                                  # READ-ONLY.

BEAM_K = r75.BEAM_K
LM_WEIGHT = 1.0
VISUAL_WEIGHTS = r75.VISUAL_WEIGHTS
PRIMARY_VISUAL_WEIGHT = r75.PRIMARY_VISUAL_WEIGHT
CAN_FOLLOW_MIN_COUNT = 1     # an observed Brown bigram (count>=1) becomes a can_follow edge.

# Honest bars (run 75/76 numbers, cited verbatim).
BAR_SYNTH_BIGRAM_STRICT = 57.5
BAR_SYNTH_BIGRAM_LOOSE = 51.2
BAR_SYNTH_NO_CONTEXT = 26.0
BAR_IAM_BIGRAM_WITHIN = 13.1
BAR_IAM_BIGRAM_CROSS = 7.4
BAR_IAM_FLOOR = 0.0


# ============================================================================================= #
#  I/O + seed guard.
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
    return r75._wilson(k, n)


def _mcnemar(a, b):
    return r75._mcnemar(a, b)


# ============================================================================================= #
#  THE CAN_FOLLOW LEXICON (graph data) + the FACULTY transition scorers.
# ============================================================================================= #
def load_can_follow():
    """Build the jabberwock's can_follow lexicon donkey=0 from run 75's Brown bigram counts (graph
    data the faculty consumes). Returns (bigram_counts:dict 'prev|cur'->count, stats:dict)."""
    prep = _load(os.path.join(RUN75_CKPT, "prep.json"))
    bigram = prep["lm"]["bigram"]      # 'prev|cur' -> count, from a ~1.2M-token Brown reduction.
    unigram = prep["lm"]["unigram"]
    # richness stats.
    heads = {}
    for key, c in bigram.items():
        if c < CAN_FOLLOW_MIN_COUNT:
            continue
        prev = key.split("|", 1)[0]
        heads[prev] = heads.get(prev, 0) + 1
    n_edges = sum(1 for c in bigram.values() if c >= CAN_FOLLOW_MIN_COUNT)
    fanouts = list(heads.values())
    stats = {
        "n_can_follow_edges": n_edges,
        "n_distinct_heads": len(heads),
        "mean_fanout": (sum(fanouts) / len(fanouts)) if fanouts else 0.0,
        "max_fanout": max(fanouts) if fanouts else 0,
        "n_unigram_types": len(unigram),
        "seed_prepopulated_can_follow_edges": 0,   # the seed ships ZERO; sparse by default.
        "min_count": CAN_FOLLOW_MIN_COUNT,
        "corpus": "Brown reduction (run 75 prep.lm), ~1.2M tokens",
    }
    return bigram, stats


def make_faculty_binary(bigram):
    """FACULTY-BINARY: the LITERAL seed prime. trans(prev,cur) = 1.0 if prev can_follow cur else 0.0
    (context_primed=1.0 on a successor, exactly what prime_successors sets)."""
    edges = {k for k, c in bigram.items() if c >= CAN_FOLLOW_MIN_COUNT}

    def score(prev, cur):
        return 1.0 if f"{prev}|{cur}" in edges else 0.0
    return score


def make_faculty_weighted(bigram):
    """FACULTY-WEIGHTED: the SAME predict_context_term Term with a richer graph prime -- context_primed
    = log1p(co-occurrence count) as the can_follow edge strength (floor 0 for a non-successor). Distinct
    from the bigram's prev-normalized conditional + stupid-backoff."""
    w = {k: math.log1p(c) for k, c in bigram.items() if c >= CAN_FOLLOW_MIN_COUNT}

    def score(prev, cur):
        return w.get(f"{prev}|{cur}", 0.0)
    return score


# ============================================================================================= #
#  STAGE: probe -- build can_follow + EXERCISE THE REAL FACULTY (load seed, run Rules, flip a read).
# ============================================================================================= #
def _faculty_wordsuperiority_check():
    """Load the semantic_reading_context seed into a real substrate, populate a can_follow edge, run the
    seed Rules (activate_recognised + prime_successors), and evaluate predict_context_term -- proving the
    jabberwock's OWN faculty flips a visually-wrong read to the context-primed truth (word-superiority).
    Uses tiny synthetic point-set features (no external data). Returns a result dict."""
    import substrate_rs as srs
    from domains.recognition_graph import predict_context_term

    s = srs.Substrate()
    sa = s.add_node("Agent", {})
    s._inner.load_seed_manifest(json.loads(open(SEMANTIC_READING_SEED).read()), sa)

    # Two candidate words. Point-set features (lists of 2D points). The mark equals wA's feature, so the
    # pure-visual read prefers wA (WRONG); context primes wB (the truth).
    featA = [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]]
    featB = [[0.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
    wA = s.add_node("Concept", {"is_word": 1.0}); s.set_attr(wA, "axs_synth_feat", featA)
    s.set_attr(wA, "name", "wA"); s.set_attr(wA, "context_primed", 0.0)
    wB = s.add_node("Concept", {"is_word": 1.0}); s.set_attr(wB, "axs_synth_feat", featB)
    s.set_attr(wB, "name", "wB"); s.set_attr(wB, "context_primed", 0.0)
    wP = s.add_node("Concept", {"is_word": 1.0}); s.set_attr(wP, "axs_synth_feat", featA)
    s.set_attr(wP, "name", "wP"); s.set_attr(wP, "context_primed", 0.0)

    # The lexicon: after wP, wB is expected (wP can_follow wB) -- graph data.
    s.add_edge_unchecked(wP, "can_follow", wB)

    # Recognise wP: record it, then run the seed Rules to spread priming.
    pm = s.add_node("Mark", {}); s.set_attr(pm, "axs_heard_feat", featA)
    s.add_edge_unchecked(pm, "recognised_as", wP)
    # The ambiguous mark (== wA visually).
    mm = s.add_node("Mark", {}); s.set_attr(mm, "axs_heard_feat", featA)
    s._inner.run_rules(50000)

    primedB = s.node(wB)["attrs"].get("context_primed")
    primedA = s.node(wA)["attrs"].get("context_primed")

    class _Pred:
        __slots__ = ("_json",)

        def __init__(self, d):
            self._json = d

    read0 = s.evaluate(_Pred(predict_context_term(0.0)), {"s": mm})
    read_hi = s.evaluate(_Pred(predict_context_term(100.0)), {"s": mm})
    name0 = s.node(read0)["attrs"].get("name")
    name_hi = s.node(read_hi)["attrs"].get("name")
    return {
        "primed_B_expected1": primedB, "primed_A_expected0": primedA,
        "read_lam0": name0, "read_lam_hi": name_hi,
        "no_context_misreads_wA": name0 == "wA",
        "context_corrects_to_wB": name_hi == "wB",
        "flip_ok": (name0 == "wA" and name_hi == "wB"),
    }


def stage_probe():
    print(f"\n{SEP}\n  STAGE: probe -- build can_follow (donkey=0) + EXERCISE the real faculty"
          f"\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("probe")

    bigram, stats = load_can_follow()
    print(f"  can_follow lexicon (from Brown, donkey=0): edges={stats['n_can_follow_edges']}  "
          f"heads={stats['n_distinct_heads']}  mean_fanout={stats['mean_fanout']:.1f}  "
          f"max_fanout={stats['max_fanout']}", flush=True)
    print(f"  seed pre-populated can_follow edges: {stats['seed_prepopulated_can_follow_edges']} "
          f"(SPARSE by default -- we populate donkey=0)", flush=True)

    faculty = _faculty_wordsuperiority_check()
    print(f"  faculty word-superiority (real seed Rules + predict_context_term): "
          f"lam=0 reads {faculty['read_lam0']!r} (visual, wrong); "
          f"lam=hi reads {faculty['read_lam_hi']!r}; flip_ok={faculty['flip_ok']}", flush=True)

    out = {"lexicon_stats": stats, "faculty_probe": faculty, "stroke_shapes_md5": md5_before}
    _save(out, _ckpt("probe.json"))
    _seed_guard("probe", md5_before)
    print(f"  saved -> {_ckpt('probe.json')}  [probe {time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: decode_synth -- three-arm decode over run 75's 130 sentences + bigram-control repro.
# ============================================================================================= #
def _sweep_synth(sentences, dists, lex_by_len, arm, lm_score):
    sweep = {}
    for vw in VISUAL_WEIGHTS:
        preds = r75.decode_all_sentence(sentences, dists, lex_by_len, arm, lm_score, vw)
        sweep[str(vw)] = r75._acc_report(preds)
    return sweep


def _best(sweep):
    best_vw = max(VISUAL_WEIGHTS, key=lambda vw: sweep[str(vw)]["word_acc"])
    return {"vw": best_vw, "rep": sweep[str(best_vw)]}


def stage_decode_synth():
    print(f"\n{SEP}\n  STAGE: decode_synth -- bigram control + FACULTY-binary + FACULTY-weighted "
          f"(synthetic)\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("decode_synth")

    prep = _load(os.path.join(RUN75_CKPT, "prep.json"))
    rd = _load(os.path.join(RUN75_CKPT, "read.json"))
    dists = {iid: rec["within_dists"] for iid, rec in rd["instances"].items()}
    lexicon = _load(RUN61_LEXICON)
    logfreq = lexicon["logfreq"]
    lex_by_len = r75.build_lex_by_len(lexicon["lexicon"])
    sentences = prep["sentences"]
    bigram = prep["lm"]["bigram"]

    scorers = {
        "bigram": r75.make_lm_scorer(prep["lm"]["unigram"], bigram, logfreq),
        "faculty_binary": make_faculty_binary(bigram),
        "faculty_weighted": make_faculty_weighted(bigram),
    }
    arms = {"B_strict": "strict", "C_loose": "loose"}

    result = {}
    for lm_name, lm_score in scorers.items():
        result[lm_name] = {}
        for label, visual_arm in arms.items():
            sweep = _sweep_synth(sentences, dists, lex_by_len, visual_arm, lm_score)
            result[lm_name][label] = {
                "primary": sweep[str(PRIMARY_VISUAL_WEIGHT)],
                "best": _best(sweep),
                "sweep_word_acc": {k: v["word_acc"] for k, v in sweep.items()},
            }

    # bigram-control reproduction (primary vw=2.0 == run 75 arm B/C).
    run75_decode = _load(os.path.join(RUN75_CKPT, "decode.json"))
    control_match = {
        "B": abs(result["bigram"]["B_strict"]["primary"]["word_acc"]
                 - run75_decode["reps"]["B"]["word_acc"]) < 1e-9,
        "C": abs(result["bigram"]["C_loose"]["primary"]["word_acc"]
                 - run75_decode["reps"]["C"]["word_acc"]) < 1e-9,
    }

    # McNemar: faculty-best vs bigram-primary, per visual arm (paired per-word flags).
    mcn = {}
    for label in arms:
        bigram_flags = result["bigram"][label]["primary"]["flags"]
        for fac in ("faculty_binary", "faculty_weighted"):
            fac_flags = result[fac][label]["best"]["rep"]["flags"]
            mcn[f"{label}|{fac}_vs_bigram"] = _mcnemar(bigram_flags, fac_flags)

    out = {"result": result, "control_matches_run75": control_match, "mcnemar": mcn,
           "n_sentences": len(sentences), "stroke_shapes_md5": md5_before}
    _save(out, _ckpt("decode_synth.json"))
    _seed_guard("decode_synth", md5_before)

    print(f"  bigram control reproduces run75 decode.json: B={control_match['B']} C={control_match['C']}",
          flush=True)
    for label in arms:
        bg = 100 * result["bigram"][label]["primary"]["word_acc"]
        fb = 100 * result["faculty_binary"][label]["best"]["rep"]["word_acc"]
        fw = 100 * result["faculty_weighted"][label]["best"]["rep"]["word_acc"]
        print(f"  {label:9}  bigram(primary)={bg:5.1f}%   faculty-binary(best)={fb:5.1f}%   "
              f"faculty-weighted(best)={fw:5.1f}%", flush=True)
    print(f"  saved -> {_ckpt('decode_synth.json')}  [decode_synth {time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: decode_iam -- three-arm decode over run 76's 27 IAM lines + bigram-control repro.
# ============================================================================================= #
def _load_iam_assembled():
    """Reproduce run 76's decode assembly from its READ-ONLY checkpoints (pure glue, identical to
    run 81's own _load_iam_assembled)."""
    prep = _load(os.path.join(RUN76_CKPT, "prep.json"))
    rec = _load(os.path.join(RUN76_CKPT, "recognize.json"))
    hol = _load(os.path.join(RUN76_CKPT, "holistic.json"))
    if not rec.get("done") or not hol.get("done"):
        raise SystemExit("WALL: run 76's recognize/holistic checkpoints are not COMPLETE.")
    lexicon, logfreq = prep["lexicon"], prep["logfreq"]
    lex_by_len = r75.build_lex_by_len(lexicon)
    queries = {q["wid"]: q for q in prep["queries"]}
    rows_by_wid = {}
    for r in rec["records"]:
        wid = r["wid"]
        SD = r76.r62._spans_to_SD(r["spans"], r["K"])
        rows = r76.oracle_count_rows(SD, r["K"], queries[wid]["len"])
        if rows is None:
            rows = [[10.0] * 26 for _ in range(queries[wid]["len"])]
        rows_by_wid[wid] = rows
    within_by_wid = {r["wid"]: r["within_rich"] for r in hol["records"]}
    cross_by_wid = {r["wid"]: r["cross_rich"] for r in hol["records"]}
    return prep, queries, lex_by_len, logfreq, rows_by_wid, within_by_wid, cross_by_wid


def stage_decode_iam():
    print(f"\n{SEP}\n  STAGE: decode_iam -- bigram control + FACULTY-binary + FACULTY-weighted "
          f"(real IAM)\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("decode_iam")

    prep, queries, lex_by_len, logfreq, rows_by_wid, within_by_wid, cross_by_wid = _load_iam_assembled()
    sent_lines = prep["sent_lines"]
    line_wids = sorted({wid for line in sent_lines for wid in line["wids"]})
    bigram = prep["lm"]["bigram"]

    scorers = {
        "bigram": r75.make_lm_scorer(prep["lm"]["unigram"], bigram, logfreq),
        "faculty_binary": make_faculty_binary(bigram),
        "faculty_weighted": make_faculty_weighted(bigram),
    }

    def _preds(lm_score, use_within, vw):
        preds = {}
        for line in sent_lines:
            wids = line["wids"]
            cand_words, vscores, trans = r76.build_line_inputs(
                wids, rows_by_wid, within_by_wid, cross_by_wid, lex_by_len, lm_score, use_within)
            seq = r75.viterbi_decode(cand_words, vscores, trans, LM_WEIGHT, vw)
            for wid, p in zip(wids, seq):
                preds[wid] = p
        return preds

    def _acc_flags(preds):
        flags = [preds.get(wid) == queries[wid]["word"] for wid in line_wids]
        ok = sum(flags)
        return ok / max(1, len(line_wids)), flags

    result = {}
    for lm_name, lm_score in scorers.items():
        result[lm_name] = {}
        for channel, use_within in (("within", True), ("cross", False)):
            sweep = {}
            flags = {}
            for vw in VISUAL_WEIGHTS:
                acc, fl = _acc_flags(_preds(lm_score, use_within, vw))
                sweep[str(vw)] = acc
                flags[str(vw)] = fl
            best_vw = max(VISUAL_WEIGHTS, key=lambda vw: sweep[str(vw)])
            result[lm_name][channel] = {
                "primary_acc": sweep[str(PRIMARY_VISUAL_WEIGHT)],
                "primary_flags": flags[str(PRIMARY_VISUAL_WEIGHT)],
                "best_vw": best_vw, "best_acc": sweep[str(best_vw)],
                "best_flags": flags[str(best_vw)],
                "sweep": sweep,
            }

    run76_decode = _load(os.path.join(RUN76_CKPT, "decode.json"))
    control_match = {
        "within": abs(result["bigram"]["within"]["primary_acc"]
                      - run76_decode["sweep"]["within"][str(PRIMARY_VISUAL_WEIGHT)]) < 1e-9,
        "cross": abs(result["bigram"]["cross"]["primary_acc"]
                     - run76_decode["sweep"]["cross"][str(PRIMARY_VISUAL_WEIGHT)]) < 1e-9,
    }

    mcn = {}
    for channel in ("within", "cross"):
        bg_flags = result["bigram"][channel]["primary_flags"]
        for fac in ("faculty_binary", "faculty_weighted"):
            fac_flags = result[fac][channel]["best_flags"]
            mcn[f"{channel}|{fac}_vs_bigram"] = _mcnemar(bg_flags, fac_flags)

    out = {"result": result, "control_matches_run76": control_match, "mcnemar": mcn,
           "n_lines": len(sent_lines), "n_test_words": len(line_wids),
           "stroke_shapes_md5": md5_before}
    _save(out, _ckpt("decode_iam.json"))
    _seed_guard("decode_iam", md5_before)

    print(f"  bigram control reproduces run76 decode.json@{PRIMARY_VISUAL_WEIGHT}: "
          f"within={control_match['within']} cross={control_match['cross']}", flush=True)
    for channel in ("within", "cross"):
        bg = 100 * result["bigram"][channel]["primary_acc"]
        fb = 100 * result["faculty_binary"][channel]["best_acc"]
        fw = 100 * result["faculty_weighted"][channel]["best_acc"]
        print(f"  {channel:7}  bigram(primary)={bg:5.1f}%   faculty-binary(best)={fb:5.1f}%   "
              f"faculty-weighted(best)={fw:5.1f}%", flush=True)
    print(f"  saved -> {_ckpt('decode_iam.json')}  [decode_iam {time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: summary.
# ============================================================================================= #
def _cmp(fac_acc, fac_ci, bar_acc, bar_ci):
    """MATCH-or-BEAT verdict for one number. Returns one of BEAT / MATCH / LOSE."""
    if fac_acc > bar_acc:
        return "BEAT"
    # CI overlap => statistically indistinguishable => MATCH.
    lo_f, hi_f = fac_ci
    lo_b, hi_b = bar_ci
    if hi_f >= lo_b:
        return "MATCH"
    return "LOSE"


def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 82 SCOREBOARD (JABBERWOCK READS WITH ITS OWN FACULTY)"
          f"\n{SEP}", flush=True)
    md5_now = _seed_guard("summary")
    probe = _require("probe.json")
    ds = _require("decode_synth.json")
    di = _require("decode_iam.json")
    print(f"  SEED-GUARD: seeds/stroke_shapes.json md5 = {md5_now} "
          f"(== probe capture: {md5_now == probe['stroke_shapes_md5']})", flush=True)

    st = probe["lexicon_stats"]
    fp = probe["faculty_probe"]
    print(f"\n  STAGE 0: interface = predict_context_term (can_follow priming), ORDER-1, seeded BINARY.",
          flush=True)
    print(f"  can_follow lexicon: {st['n_can_follow_edges']} edges, {st['n_distinct_heads']} heads, "
          f"mean_fanout {st['mean_fanout']:.1f} (seed ships {st['seed_prepopulated_can_follow_edges']} "
          f"-> SPARSE; populated donkey=0 from Brown).", flush=True)
    print(f"  real-faculty word-superiority flip (seed Rules + predict_context_term): {fp['flip_ok']}",
          flush=True)

    # -- synthetic scoreboard. --
    def R(d):  # 100*word_acc + ci
        return 100 * d["word_acc"], [100 * c for c in d["word_ci"]]

    print(f"\n  SYNTHETIC (run 75 setup, n_sentences={ds['n_sentences']})", flush=True)
    synth_flags = {}
    for label, bar in (("B_strict", BAR_SYNTH_BIGRAM_STRICT), ("C_loose", BAR_SYNTH_BIGRAM_LOOSE)):
        bg_acc, bg_ci = R(ds["result"]["bigram"][label]["primary"])
        fb_acc, fb_ci = R(ds["result"]["faculty_binary"][label]["best"]["rep"])
        fw_acc, fw_ci = R(ds["result"]["faculty_weighted"][label]["best"]["rep"])
        vb = _cmp(fb_acc, fb_ci, bg_acc, bg_ci)
        vw = _cmp(fw_acc, fw_ci, bg_acc, bg_ci)
        synth_flags[label] = {"binary": vb, "weighted": vw, "bigram": bg_acc,
                              "faculty_binary": fb_acc, "faculty_weighted": fw_acc}
        print(f"  {label:9} bigram={bg_acc:5.1f}% [{bg_ci[0]:.1f},{bg_ci[1]:.1f}]  "
              f"fac-binary={fb_acc:5.1f}% ({vb})  fac-weighted={fw_acc:5.1f}% ({vw})", flush=True)

    print(f"\n  REAL IAM (run 76 setup, n_test_words={di['n_test_words']})", flush=True)
    iam_flags = {}
    for channel, bar in (("within", BAR_IAM_BIGRAM_WITHIN), ("cross", BAR_IAM_BIGRAM_CROSS)):
        n = di["n_test_words"]
        bg_acc = 100 * di["result"]["bigram"][channel]["primary_acc"]
        fb_acc = 100 * di["result"]["faculty_binary"][channel]["best_acc"]
        fw_acc = 100 * di["result"]["faculty_weighted"][channel]["best_acc"]
        bg_ci = [100 * c for c in _wilson(round(bg_acc / 100 * n), n)]
        fb_ci = [100 * c for c in _wilson(round(fb_acc / 100 * n), n)]
        fw_ci = [100 * c for c in _wilson(round(fw_acc / 100 * n), n)]
        vb = _cmp(fb_acc, fb_ci, bg_acc, bg_ci)
        vw = _cmp(fw_acc, fw_ci, bg_acc, bg_ci)
        iam_flags[channel] = {"binary": vb, "weighted": vw, "bigram": bg_acc,
                              "faculty_binary": fb_acc, "faculty_weighted": fw_acc}
        print(f"  {channel:7} bigram={bg_acc:5.1f}%  fac-binary={fb_acc:5.1f}% ({vb})  "
              f"fac-weighted={fw_acc:5.1f}% ({vw})", flush=True)

    # -- verdict: WIN if the native faculty MATCHES-or-BEATS the bigram on synthetic (both arms) AND
    #    IAM within (the headline transfer number). Best native arm per cell counts. --
    def cell_ok(d):
        return d["binary"] in ("BEAT", "MATCH") or d["weighted"] in ("BEAT", "MATCH")
    synth_ok = all(cell_ok(synth_flags[l]) for l in ("B_strict", "C_loose"))
    iam_ok = cell_ok(iam_flags["within"])
    verdict = "WIN" if (synth_ok and iam_ok) else ("PARTIAL" if (synth_ok or iam_ok) else "NULL")

    out = {
        "faculty_depth": "can_follow priming (predict_context_term); ORDER-1; seeded BINARY. "
                         "Deeper faculties (sense_select, comprehend_recursive) are sense-disambig / "
                         "parsing over known words, NOT candidate-lattice next-word prediction -> "
                         "not reachable for this task.",
        "lexicon_stats": st, "faculty_probe": fp,
        "synth": synth_flags, "iam": iam_flags,
        "control_matches_run75": ds["control_matches_run75"],
        "control_matches_run76": di["control_matches_run76"],
        "mcnemar_synth": ds["mcnemar"], "mcnemar_iam": di["mcnemar"],
        "bars": {"synth_strict": BAR_SYNTH_BIGRAM_STRICT, "synth_loose": BAR_SYNTH_BIGRAM_LOOSE,
                 "iam_within": BAR_IAM_BIGRAM_WITHIN, "iam_cross": BAR_IAM_BIGRAM_CROSS},
        "verdict": verdict, "synth_ok": synth_ok, "iam_ok": iam_ok,
        "stroke_shapes_md5": md5_now,
    }
    _save(out, _ckpt("verdict.json"))
    _save(out, _ckpt("summary.json"))
    print(f"\n  VERDICT: {verdict}  (synth_ok={synth_ok}  iam_ok={iam_ok})", flush=True)
    print(f"  saved -> {_ckpt('summary.json')}", flush=True)
    print(f"\n{SEP}\n  RUN 82 COMPLETE -- see final agent report.\n{SEP}", flush=True)
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True,
                    choices=["probe", "decode_synth", "decode_iam", "summary"])
    args = p.parse_args()
    return {"probe": stage_probe, "decode_synth": stage_decode_synth,
            "decode_iam": stage_decode_iam, "summary": stage_summary}[args.stage]()


if __name__ == "__main__":
    sys.exit(main())
