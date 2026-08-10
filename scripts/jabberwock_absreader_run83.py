"""jabberwock_absreader_run83.py -- RUN 83: WIRE THE HANDWRITING VISUAL INTO THE DEEP AbS
PREDICTIVE READER (domains/predictive_reading.py -- "THE FAST READER", commit 5542195f).

THE FRAMING (creator: "significant work done in AbS for reading ... a deep feature that should make a
large difference"). The jabberwock has a DEEP predictive reader: reading = SYNTHESIZE what the writer
will write, the noisy signal only CONFIRMS the prediction (payoff-b: char-substitution noise 100% vs
50% bottom-up). Run 82 showed the order-1 `can_follow` faculty is bigram-equivalent (59.1% synth /
15.6% IAM within). THIS reader is RICHER: predict_next_words runs FORWARD conditioned on the WHOLE
accumulating discourse context + register + class-prior, NOT order-1. Run 83 attaches OUR run-75/76
handwriting VISUAL (the noisy signal, UNCHANGED) to this predictive reader and measures the lift.

STAGE 0 -- THE FACULTY'S PREDICTIVE INTERFACE (studied, reported in the agent's final message):
  * predict_next_words(agent, ws_node, context, seen_vocab) -> a predicted WORD SET (+ provenance), the
    production faculty run forward. Sources: recurring_beat (cross-arc n-gram), context (ALL content
    words of the discourse so far -- NOT order-1), register (all seen word TYPES), production (a
    throughline rel:patient clause), class_prior (a class-corpus vocabulary). On NON-narrative Brown/IAM
    text: context + recurring_beat + register FIRE; production returns None (no throughline beat);
    class_prior fires only when a class corpus is supplied.
  * prediction_guided_segment(agent, predicted_words, noisy_text) disambiguates a NOISY CHARACTER STRING
    by AUGMENTING the base lexicon with the predicted words (missing-space + char-substitution recovery).
    Its interface is a CLEAN/NOISY TEXT STRING, NOT a scored word-lattice re-ranker -- so to wire our
    scored VISUAL lattice we apply the predicted SET as a per-position membership PRIOR (the AbS bias:
    the prediction confirms / re-ranks the visual candidates), the only lattice-compatible attachment.
  * abs_compare(agent, predicted, actual) -> the CONFIRM-FRACTION (the speed signal): a ShapeDecode
    collapse, the residual is the surprise. RICHER than order-1 in CONTEXT BREADTH (whole left context)
    but UNORDERED (a set, no prev->cur transition weight) -- reported honestly.

STAGE 1 -- HOW IT IS ATTACHED (donkey=0, native, visual UNCHANGED):
The VISUAL channel is run 75/76's own, reused VERBATIM (topk_candidates / topk_candidates_iam over the
stored per-char distance rows -- training-free, byte-identical). The reader streams sentences/lines
LEFT-TO-RIGHT; the register + context ACCUMULATE from what it has read (the "warm-up"). Per sentence it
PREDICTS the words from the accumulated model; the arriving VISUAL lattice is RE-RANKED by the predicted
set (combined = zscore(visual) + pw * bonus(word in predicted set)). Bottom-up = pw=0 (visual alone).
Register/context accumulate from the bottom-up visual reading (no truth leak). Four LM arms fed the SAME
visual lattice + sweep, exactly run 82's "swap the capability, don't touch the visual" discipline:
  * BOTTOM-UP     = pw=0, visual alone (the control the predictor must beat).
  * ABS-MEMBER    = rich predicted set, binary membership bonus.
  * ABS-TIERED    = rich predicted set, provenance-tiered bonus (context/beat/production=3, register=2,
                    class_prior=1) -- specificity, the faculty's own provenance.
  * ABS-CLASSPRIOR= rich predicted set + a class-prior register (Brown top words, the SAME corpus the
                    bigram uses), binary membership.
Best-of-sweep per arm; primary pw = 2.0.

CO-MOVEMENT ANALYSIS (creator's derived signature: "people who read cursive better are also faster
readers"): reading SPEED = the confirm-fraction, reading CURSIVE well = prediction carrying the
ambiguous signal; BOTH are downstream of PREDICTION STRENGTH (common cause). The framework predicts:
as prediction gets RICHER, cursive-reading ACCURACY and the CONFIRM-FRACTION rise TOGETHER. Measured
(a) across the prediction-richness ladder (bottom-up -> order-1 -> rich AbS): (accuracy, confirm_frac);
(b) per-sentence within the rich arm: corr(sentence accuracy, sentence confirm_frac); (c) the warm-up
(early vs late half of the stream): do BOTH rise as the model accumulates.

SEED GUARD: OZMA_SEED_PERSIST_DISABLED=1; md5(seeds/stroke_shapes.json) asserted UNCHANGED before AND
after every stage. results/run7{5,6}_checkpoints READ-ONLY. Writes ONLY results/run83_checkpoints/*.
NO git add/commit. donkey=0 (the jabberwock's OWN predictive_reading faculty; NO external LLM).

Stages: probe -> decode_synth -> decode_iam -> summary. Run (from the gamma-substrate repo root):
  OZMA_SEED_PERSIST_DISABLED=1 PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python3 scripts/jabberwock_absreader_run83.py \\
    --stage <probe|decode_synth|decode_iam|summary>
"""
from __future__ import annotations

import argparse
import hashlib
import json
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

import numpy as np                                        # noqa: E402
import substrate_rs as srs                                # noqa: E402
from domains import predictive_reading as pr              # noqa: E402
import scripts.jabberwock_sentence_read_run75 as r75      # noqa: E402
import scripts.jabberwock_iam_full_run76 as r76           # noqa: E402

SEP = "=" * 92
STROKE_SHAPES_SEED = os.path.join(ROOT, "seeds", "stroke_shapes.json")
CKPT_DIR = os.path.join(ROOT, "results", "run83_checkpoints")
LOG = os.path.join(ROOT, "results", "omniglot_gate_run83.log")
os.makedirs(CKPT_DIR, exist_ok=True)

RUN75_CKPT = os.path.join(ROOT, "results", "run75_checkpoints")    # READ-ONLY.
RUN76_CKPT = os.path.join(ROOT, "results", "run76_checkpoints")    # READ-ONLY.
RUN61_LEXICON = r75.RUN61_LEXICON                                  # READ-ONLY.

BEAM_K = r75.BEAM_K
PRED_WEIGHTS = (0.0, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0)
PRIMARY_PW = 2.0
CTX_WINDOW = 2          # last-N read sentences as the immediate discourse context.
SEEN_WINDOW = 8         # last-N read sentences the writer model harvests the recurring beat from.
CLASS_PRIOR_TOPN = 2000 # class-register size (top Brown unigrams -- the SAME corpus the bigram uses).

# Honest bars (run 75/76/82 numbers, cited verbatim).
BAR_SYNTH_BOTTOMUP = 26.0         # run 75 isolated / no-context (BAR_SYNTH_NO_CONTEXT).
BAR_SYNTH_BIGRAM = 57.5           # run 75 sentence-bigram strict.
BAR_SYNTH_ORDER1 = 59.1           # run 82 faculty-weighted (order-1 can_follow) best.
BAR_IAM_BIGRAM_WITHIN = 13.1
BAR_IAM_BIGRAM_CROSS = 7.4
BAR_IAM_ORDER1_WITHIN = 15.6      # run 82 faculty-weighted best, within.
BAR_IAM_ORDER1_CROSS = 13.1       # run 82 faculty-weighted best, cross.

_TIER = {"recurring_beat": 3.0, "context": 3.0, "production": 3.0,
         "register": 2.0, "class_prior": 1.0}


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


def _pearson(xs, ys):
    return pr._pearson(list(xs), list(ys))


# ============================================================================================= #
#  THE PREDICTIVE READER, wired to the visual lattice (the faculty is the agent's OWN).
# ============================================================================================= #
def _fresh_agent():
    s = srs.Substrate()
    s.add_node("Agent", {})
    return s


def _class_register(topn=CLASS_PRIOR_TOPN):
    """The class-prior register: the top-N Brown unigrams -- the SAME ~1.2M-token corpus the bigram
    control uses (run 75 prep.lm.unigram). donkey=0, no external model, no leak of the TEST words'
    identities (a frequency prior over the writer-class vocabulary)."""
    prep = _load(os.path.join(RUN75_CKPT, "prep.json"))
    uni = prep["lm"]["unigram"]
    words = sorted(uni, key=lambda w: -uni[w])
    out = [w for w in words if w.isalpha() and w.islower()][:topn]
    return out


def predict_for_sentence(prior_sents, register, class_register=None):
    """Predict the next sentence's words from the ACCUMULATED reader model (the production faculty run
    forward). Cold start (no prior read text) -> empty prediction (honest: nothing to synthesize yet).
    Returns {predicted_words, provenance}."""
    seen = prior_sents[-SEEN_WINDOW:] if prior_sents else []
    if not seen:
        return {"predicted_words": [], "provenance": {}}
    a = _fresh_agent()
    model = pr.build_writer_model(a, seen, class_register=class_register)
    context = " ".join(prior_sents[-CTX_WINDOW:])
    pred = pr.predict_next_words(a, model["writer_style"], context=context,
                                 seen_vocab=list(register))
    return {"predicted_words": pred["predicted_words"], "provenance": pred["provenance"]}


def _zscore(vscores):
    a = np.asarray(vscores, dtype=np.float64)
    if a.size == 0:
        return a
    sd = a.std()
    return (a - a.mean()) / (sd + 1e-9)


def _bonus(word, predset, provenance, mode):
    if word not in predset:
        return 0.0
    if mode == "membership":
        return 1.0
    return _TIER.get(provenance.get(word), 1.0)


def _decode_position(cand_words, vscores, predset, provenance, pw, mode):
    """Re-rank the UNCHANGED visual lattice by the predicted-set prior: argmax over candidates of
    zscore(visual) + pw*bonus. pw=0 => pure visual (bottom-up)."""
    if not cand_words:
        return ""
    v = _zscore(vscores)
    best, best_sc = "", None
    for i, w in enumerate(cand_words):
        sc = float(v[i]) + pw * _bonus(w, predset, provenance, mode)
        if best_sc is None or sc > best_sc:
            best_sc, best = sc, w
    return best


def _confirm_fraction(agent, predicted_words, truth_words):
    """The CONFIRM-FRACTION for one sentence: of the arriving CONTENT words, the fraction the prediction
    covered (abs_compare's ShapeDecode collapse -- the residual is the surprise). The speed signal."""
    cmp = pr.abs_compare(agent, predicted_words, truth_words)
    return cmp["confirm_frac"], cmp["hit_rate"]


def _can_follow_coverage(truths, bigram, min_count=1):
    """The ORDER-1 predictor's 'confirm fraction': of the adjacent truth word pairs, the fraction that
    are an observed can_follow bigram (count>=min_count). Comparable to the AbS confirm-fraction -- what
    fraction of transitions the order-1 model predicts."""
    edges = {k for k, c in bigram.items() if c >= min_count}
    tot = hit = 0
    for words in truths:
        for i in range(1, len(words)):
            tot += 1
            if f"{words[i-1]}|{words[i]}" in edges:
                hit += 1
    return (hit / tot) if tot else 0.0


# ============================================================================================= #
#  THE STREAM DECODE -- two-pass (pass 1 builds the accumulated register from the bottom-up visual
#  reading; pass 2 predicts + re-ranks every arm at every position, register frozen from pass 1).
# ============================================================================================= #
def decode_stream(sentence_positions, sentence_truths, class_register):
    """sentence_positions: list per sentence of list of (cand_words, vscores) per position.
    sentence_truths:    list per sentence of the truth word list.
    Returns a dict of per-arm/per-pw flat prediction lists (parallel to a flat truth list), the
    per-sentence confirm-fractions, and the per-sentence rich-arm accuracy."""
    n_sent = len(sentence_positions)
    # ---- PASS 1: bottom-up visual reading -> the accumulated register + context. ----
    bottomup_dec = []                          # per sentence: decoded words (visual argmax).
    for si in range(n_sent):
        dec = [_decode_position(cw, vs, set(), {}, 0.0, "membership")
               for (cw, vs) in sentence_positions[si]]
        bottomup_dec.append(dec)
    register_before, context_before = [], []
    reg, seen_sents = [], []
    for si in range(n_sent):
        register_before.append(list(reg))
        context_before.append(list(seen_sents))
        for w in bottomup_dec[si]:
            if w and w not in reg:
                reg.append(w)
        seen_sents.append(" ".join(w for w in bottomup_dec[si] if w))

    # ---- PASS 2: predict per sentence, re-rank every arm/pw. ----
    arms = ("bottomup", "abs_member", "abs_tiered", "abs_classprior")
    # arm -> pw(str) -> flat list of predictions
    preds = {a: {str(pw): [] for pw in PRED_WEIGHTS} for a in arms}
    flat_truth = []
    confirm = []               # per sentence: {confirm_frac, confirm_frac_cp, hit_rate, n_content}
    rich_sent_acc = []         # per sentence: rich-arm (abs_member @ primary pw) word accuracy
    agent = _fresh_agent()     # a persistent agent for the abs_compare confirm measurement.

    for si in range(n_sent):
        prior = context_before[si]
        regb = register_before[si]
        pr_rich = predict_for_sentence(prior, regb, class_register=None)
        pr_cp = predict_for_sentence(prior, regb, class_register=class_register)
        set_rich = set(pr_rich["predicted_words"])
        prov_rich = pr_rich["provenance"]
        set_cp = set(pr_cp["predicted_words"])
        prov_cp = pr_cp["provenance"]

        truth = sentence_truths[si]
        truth_content = pr._content_words(agent, " ".join(truth)) if truth else []
        cf, hr = _confirm_fraction(agent, pr_rich["predicted_words"], truth)
        cf_cp, _ = _confirm_fraction(agent, pr_cp["predicted_words"], truth)
        confirm.append({"confirm_frac": cf, "confirm_frac_cp": cf_cp, "hit_rate": hr,
                        "n_content": len(truth_content), "n_words": len(truth),
                        "k": si})

        positions = sentence_positions[si]
        # rich-arm per-sentence accuracy at primary pw (for the per-sentence co-movement corr).
        rich_ok = rich_tot = 0
        for pi, (cw, vs) in enumerate(positions):
            t = truth[pi] if pi < len(truth) else None
            for pw in PRED_WEIGHTS:
                pws = str(pw)
                preds["bottomup"][pws].append(
                    _decode_position(cw, vs, set(), {}, 0.0, "membership"))
                preds["abs_member"][pws].append(
                    _decode_position(cw, vs, set_rich, prov_rich, pw, "membership"))
                preds["abs_tiered"][pws].append(
                    _decode_position(cw, vs, set_rich, prov_rich, pw, "tiered"))
                preds["abs_classprior"][pws].append(
                    _decode_position(cw, vs, set_cp, prov_cp, pw, "membership"))
            flat_truth.append(t)
            p_rich = _decode_position(cw, vs, set_rich, prov_rich, PRIMARY_PW, "membership")
            rich_tot += 1
            rich_ok += int(p_rich == t)
        rich_sent_acc.append((rich_ok / rich_tot) if rich_tot else 0.0)

    return {"arms": arms, "preds": preds, "flat_truth": flat_truth,
            "confirm": confirm, "rich_sent_acc": rich_sent_acc, "n_sent": n_sent}


def _acc_flags(pred_list, truth_list):
    flags = [(p == t) for p, t in zip(pred_list, truth_list)]
    ok = sum(flags)
    return (ok / len(flags)) if flags else 0.0, flags


def _best_arm(preds_arm, truth_list):
    best_pw, best_acc, best_flags = None, -1.0, None
    sweep = {}
    for pw in PRED_WEIGHTS:
        acc, flags = _acc_flags(preds_arm[str(pw)], truth_list)
        sweep[str(pw)] = acc
        if acc > best_acc:
            best_pw, best_acc, best_flags = pw, acc, flags
    return {"best_pw": best_pw, "best_acc": best_acc, "best_flags": best_flags,
            "primary_pw": PRIMARY_PW,
            "primary_acc": _acc_flags(preds_arm[str(PRIMARY_PW)], truth_list)[0],
            "sweep": sweep}


# ============================================================================================= #
#  STAGE: probe -- study the interface + fire predict_next_words on Brown + payoff-b on OUR signal.
# ============================================================================================= #
def stage_probe():
    print(f"\n{SEP}\n  STAGE: probe -- predictive interface + which sources fire (non-narrative)"
          f"\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("probe")

    a = _fresh_agent()
    seen = ["the state government said the new tax would help the schools .",
            "the new report said the state would raise the tax again ."]
    model = pr.build_writer_model(a, seen)
    pred = pr.predict_next_words(a, model["writer_style"],
                                 context="the committee reviewed the new tax report",
                                 seen_vocab=["the", "state", "government", "tax", "report", "new"])
    srcs = sorted(set(pred["provenance"].values()))
    # class-prior fires only with a class corpus.
    cr = _class_register(50)
    m2 = pr.build_writer_model(a, seen, class_register=cr)
    p2 = pr.predict_next_words(a, m2["writer_style"], context="", seen_vocab=[])
    srcs_cp = sorted(set(p2["provenance"].values()))

    # payoff-b on OUR signal: prediction flips a char-substituted / run-together token.
    predicted = ["river", "bird", "flew"]
    bottom = pr.bottom_up_segment(a, "r1ver")
    guided = pr.prediction_guided_segment(a, predicted, "r1ver")
    payoff = {
        "bottom_up": bottom, "guided": guided,
        "bottom_up_acc": pr.segmentation_accuracy(bottom, ["river"]),
        "guided_acc": pr.segmentation_accuracy(guided, ["river"]),
        "missing_space": pr.prediction_guided_segment(a, ["the", "bird", "river"], "thebirdriver"),
    }

    # richness contrast: is it richer than order-1? predict from a 6-token-back context word.
    richness = {
        "predicts_context_word_4back": "report" in pred["predicted_words"],
        "predicts_context_word_6back": "committee" in pred["predicted_words"],
        "n_predicted": len(pred["predicted_words"]),
        "production_fires": pred["production"] is not None,
    }
    out = {"sources_fire_non_narrative": srcs, "sources_with_class_prior": srcs_cp,
           "predicted_sample": pred["predicted_words"][:20],
           "payoff_b": payoff, "richness": richness,
           "interface": "predict_next_words -> predicted SET (+provenance); prediction_guided_segment "
                        "takes a NOISY TEXT STRING (augments lexicon), NOT a scored lattice; the visual "
                        "lattice is re-ranked by the predicted-set membership prior.",
           "stroke_shapes_md5": md5_before}
    _save(out, _ckpt("probe.json"))
    _seed_guard("probe", md5_before)
    print(f"  sources firing on non-narrative Brown text: {srcs}", flush=True)
    print(f"  sources with class corpus supplied: {srcs_cp}", flush=True)
    print(f"  RICHER-than-order-1: predicts context word 4-back={richness['predicts_context_word_4back']} "
          f"6-back={richness['predicts_context_word_6back']}; production_fires={richness['production_fires']}",
          flush=True)
    print(f"  payoff-b on OUR signal: bottom-up 'r1ver' acc={payoff['bottom_up_acc']:.2f} -> "
          f"prediction-guided acc={payoff['guided_acc']:.2f}  (guided={guided})", flush=True)
    print(f"  saved -> {_ckpt('probe.json')}  [probe {time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: decode_synth -- run 75's 130 sentences, real DeepWriting word-ink visual (UNCHANGED).
# ============================================================================================= #
def stage_decode_synth():
    print(f"\n{SEP}\n  STAGE: decode_synth -- AbS predictive reader over run 75's 130 sentences"
          f"\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("decode_synth")

    prep = _load(os.path.join(RUN75_CKPT, "prep.json"))
    rd = _load(os.path.join(RUN75_CKPT, "read.json"))
    dists = {iid: rec["within_dists"] for iid, rec in rd["instances"].items()}
    lexicon = _load(RUN61_LEXICON)
    lex_by_len = r75.build_lex_by_len(lexicon["lexicon"])
    sentences = prep["sentences"]
    bigram = prep["lm"]["bigram"]
    class_register = _class_register()

    arm = "strict"
    sentence_positions, sentence_truths = [], []
    for s in sentences:
        positions = []
        for iid in s["iids"]:
            cw, vs = r75.topk_candidates(dists[iid], lex_by_len, arm, BEAM_K)
            positions.append((cw, list(np.asarray(vs, dtype=float))))
        sentence_positions.append(positions)
        sentence_truths.append(list(s["words"]))

    res = decode_stream(sentence_positions, sentence_truths, class_register)
    truth = res["flat_truth"]
    reports = {a: _best_arm(res["preds"][a], truth) for a in res["arms"]}

    # McNemar: each AbS arm (best) vs bottom-up (primary=pw0, same everywhere).
    bu_flags = _acc_flags(res["preds"]["bottomup"][str(PRIMARY_PW)], truth)[1]
    mcn = {}
    for a in ("abs_member", "abs_tiered", "abs_classprior"):
        mcn[f"{a}_vs_bottomup"] = _mcnemar(bu_flags, reports[a]["best_flags"])

    order1_cf = _can_follow_coverage(sentence_truths, bigram)
    out = {"reports": reports, "mcnemar_vs_bottomup": mcn,
           "confirm": res["confirm"], "rich_sent_acc": res["rich_sent_acc"],
           "order1_can_follow_coverage": order1_cf,
           "n_sentences": len(sentences), "n_words": len(truth),
           "bars": {"bottomup": BAR_SYNTH_BOTTOMUP, "bigram": BAR_SYNTH_BIGRAM,
                    "order1": BAR_SYNTH_ORDER1},
           "stroke_shapes_md5": md5_before}
    _save(out, _ckpt("decode_synth.json"))
    _seed_guard("decode_synth", md5_before)

    for a in res["arms"]:
        print(f"  {a:15} primary(pw={PRIMARY_PW})={100*reports[a]['primary_acc']:5.1f}%   "
              f"best(pw={reports[a]['best_pw']})={100*reports[a]['best_acc']:5.1f}%", flush=True)
    mean_cf = sum(c["confirm_frac"] for c in res["confirm"]) / max(1, len(res["confirm"]))
    print(f"  mean confirm-fraction (rich): {100*mean_cf:.1f}%   order-1 can_follow coverage: "
          f"{100*order1_cf:.1f}%", flush=True)
    print(f"  bars: bottom-up {BAR_SYNTH_BOTTOMUP}% | bigram {BAR_SYNTH_BIGRAM}% | order-1 {BAR_SYNTH_ORDER1}%",
          flush=True)
    print(f"  saved -> {_ckpt('decode_synth.json')}  [decode_synth {time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: decode_iam -- run 76's real IAM-OnDB lines, within + cross writer (visual UNCHANGED).
# ============================================================================================= #
def _load_iam_assembled():
    prep = _load(os.path.join(RUN76_CKPT, "prep.json"))
    rec = _load(os.path.join(RUN76_CKPT, "recognize.json"))
    hol = _load(os.path.join(RUN76_CKPT, "holistic.json"))
    if not rec.get("done") or not hol.get("done"):
        raise SystemExit("WALL: run 76's recognize/holistic checkpoints are not COMPLETE.")
    lexicon = prep["lexicon"]
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
    return prep, queries, lex_by_len, rows_by_wid, within_by_wid, cross_by_wid


def stage_decode_iam():
    print(f"\n{SEP}\n  STAGE: decode_iam -- AbS predictive reader over run 76's IAM lines"
          f"\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("decode_iam")

    prep, queries, lex_by_len, rows_by_wid, within_by_wid, cross_by_wid = _load_iam_assembled()
    sent_lines = prep["sent_lines"]
    bigram = prep["lm"]["bigram"]
    class_register = _class_register()

    result = {}
    confirm_by_channel = {}
    rich_sent_acc_by_channel = {}
    for channel, use_within in (("within", True), ("cross", False)):
        sentence_positions, sentence_truths = [], []
        for line in sent_lines:
            positions = []
            truth = []
            for wid in line["wids"]:
                cw, vs = r76.topk_candidates_iam(
                    rows_by_wid[wid], lex_by_len, within_by_wid.get(wid, {}),
                    cross_by_wid.get(wid, {}), use_within, BEAM_K)
                positions.append((cw, list(np.asarray(vs, dtype=float))))
                truth.append(queries[wid]["word"])
            sentence_positions.append(positions)
            sentence_truths.append(truth)

        res = decode_stream(sentence_positions, sentence_truths, class_register)
        truth = res["flat_truth"]
        reports = {a: _best_arm(res["preds"][a], truth) for a in res["arms"]}
        bu_flags = _acc_flags(res["preds"]["bottomup"][str(PRIMARY_PW)], truth)[1]
        mcn = {}
        for a in ("abs_member", "abs_tiered", "abs_classprior"):
            mcn[f"{a}_vs_bottomup"] = _mcnemar(bu_flags, reports[a]["best_flags"])
        result[channel] = {"reports": reports, "mcnemar_vs_bottomup": mcn,
                           "order1_can_follow_coverage": _can_follow_coverage(sentence_truths, bigram),
                           "n_words": len(truth)}
        confirm_by_channel[channel] = res["confirm"]
        rich_sent_acc_by_channel[channel] = res["rich_sent_acc"]

    out = {"result": result, "confirm": confirm_by_channel,
           "rich_sent_acc": rich_sent_acc_by_channel,
           "n_lines": len(sent_lines),
           "bars": {"bigram_within": BAR_IAM_BIGRAM_WITHIN, "bigram_cross": BAR_IAM_BIGRAM_CROSS,
                    "order1_within": BAR_IAM_ORDER1_WITHIN, "order1_cross": BAR_IAM_ORDER1_CROSS},
           "stroke_shapes_md5": md5_before}
    _save(out, _ckpt("decode_iam.json"))
    _seed_guard("decode_iam", md5_before)

    for channel in ("within", "cross"):
        rep = result[channel]["reports"]
        print(f"  {channel:7} n={result[channel]['n_words']}", flush=True)
        for a in ("bottomup", "abs_member", "abs_tiered", "abs_classprior"):
            print(f"    {a:15} primary={100*rep[a]['primary_acc']:5.1f}%  "
                  f"best(pw={rep[a]['best_pw']})={100*rep[a]['best_acc']:5.1f}%", flush=True)
        cf = confirm_by_channel[channel]
        mean_cf = sum(c["confirm_frac"] for c in cf) / max(1, len(cf))
        print(f"    mean confirm-fraction={100*mean_cf:.1f}%  order-1 coverage="
              f"{100*result[channel]['order1_can_follow_coverage']:.1f}%", flush=True)
    print(f"  saved -> {_ckpt('decode_iam.json')}  [decode_iam {time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: summary -- the reading-lift table + confirm-fraction + co-movement + verdict.
# ============================================================================================= #
def _comovement(levels):
    """levels: list of (name, accuracy_pct, confirm_frac_pct). Returns Pearson r + monotone flags."""
    accs = [l[1] for l in levels]
    cfs = [l[2] for l in levels]
    r = _pearson(accs, cfs)
    mono_acc = all(accs[i] <= accs[i + 1] + 1e-9 for i in range(len(accs) - 1))
    mono_cf = all(cfs[i] <= cfs[i + 1] + 1e-9 for i in range(len(cfs) - 1))
    return {"levels": levels, "pearson_r": r, "accuracy_monotone_up": mono_acc,
            "confirm_monotone_up": mono_cf, "co_move": mono_acc and mono_cf}


def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 83 SCOREBOARD (DEEP AbS PREDICTIVE READER on handwriting)"
          f"\n{SEP}", flush=True)
    md5_now = _seed_guard("summary")
    probe = _require("probe.json")
    ds = _require("decode_synth.json")
    di = _require("decode_iam.json")
    print(f"  SEED-GUARD: seeds/stroke_shapes.json md5 = {md5_now} "
          f"(== probe capture: {md5_now == probe['stroke_shapes_md5']})", flush=True)

    # ---- best AbS arm per corpus (best of member / tiered / classprior, best-of-sweep). ----
    def best_abs(reports):
        cands = {a: reports[a]["best_acc"] for a in ("abs_member", "abs_tiered", "abs_classprior")}
        a = max(cands, key=cands.get)
        return a, 100 * reports[a]["best_acc"], 100 * reports["bottomup"]["best_acc"]

    s_arm, s_abs, s_bu = best_abs(ds["reports"])
    s_mean_cf = 100 * sum(c["confirm_frac"] for c in ds["confirm"]) / max(1, len(ds["confirm"]))
    s_order1_cf = 100 * ds["order1_can_follow_coverage"]

    print(f"\n  SYNTHETIC (run 75, n_words={ds['n_words']}, n_sentences={ds['n_sentences']})", flush=True)
    print(f"    bottom-up(visual) {s_bu:5.1f}%  | bigram {BAR_SYNTH_BIGRAM}%  | order-1 {BAR_SYNTH_ORDER1}%"
          f"  | AbS-predictive({s_arm}) {s_abs:5.1f}%", flush=True)

    iam = {}
    for channel in ("within", "cross"):
        rep = di["result"][channel]["reports"]
        a, abs_acc, bu_acc = best_abs(rep)
        cf = di["confirm"][channel]
        mean_cf = 100 * sum(c["confirm_frac"] for c in cf) / max(1, len(cf))
        iam[channel] = {"arm": a, "abs": abs_acc, "bottomup": bu_acc,
                        "mean_cf": mean_cf,
                        "order1_cf": 100 * di["result"][channel]["order1_can_follow_coverage"],
                        "n": di["result"][channel]["n_words"]}
    print(f"\n  REAL IAM (run 76)", flush=True)
    for channel in ("within", "cross"):
        bg = BAR_IAM_BIGRAM_WITHIN if channel == "within" else BAR_IAM_BIGRAM_CROSS
        o1 = BAR_IAM_ORDER1_WITHIN if channel == "within" else BAR_IAM_ORDER1_CROSS
        c = iam[channel]
        print(f"    {channel:7} bottom-up {c['bottomup']:5.1f}%  | bigram {bg}%  | order-1 {o1}%  | "
              f"AbS-predictive({c['arm']}) {c['abs']:5.1f}%", flush=True)

    # ---- CONFIRM-FRACTION (speed signal). ----
    print(f"\n  CONFIRM-FRACTION (speed signal):  synthetic rich={s_mean_cf:.1f}%  "
          f"order-1 coverage={s_order1_cf:.1f}%", flush=True)
    for channel in ("within", "cross"):
        print(f"    IAM {channel}: rich confirm={iam[channel]['mean_cf']:.1f}%  "
              f"order-1 coverage={iam[channel]['order1_cf']:.1f}%", flush=True)

    # ---- CO-MOVEMENT (creator's derived signature). Across the richness ladder + per-sentence. ----
    # ladder: bottom-up (confirm 0) -> order-1 (can_follow coverage, cited acc) -> rich AbS.
    synth_ladder = [
        ("bottom_up", s_bu, 0.0),
        ("order1", BAR_SYNTH_ORDER1, s_order1_cf),
        ("abs_rich", s_abs, s_mean_cf),
    ]
    synth_cm = _comovement(synth_ladder)
    # per-sentence within the rich arm.
    per_sent_acc = ds["rich_sent_acc"]
    per_sent_cf = [c["confirm_frac"] for c in ds["confirm"]]
    synth_persent_r = _pearson(per_sent_acc, per_sent_cf)
    # warm-up: early vs late half of the stream (do BOTH rise as the model accumulates).
    half = len(per_sent_acc) // 2
    early_acc = sum(per_sent_acc[:half]) / max(1, half)
    late_acc = sum(per_sent_acc[half:]) / max(1, len(per_sent_acc) - half)
    early_cf = sum(per_sent_cf[:half]) / max(1, half)
    late_cf = sum(per_sent_cf[half:]) / max(1, len(per_sent_cf) - half)

    iam_ladders = {}
    for channel in ("within", "cross"):
        o1 = BAR_IAM_ORDER1_WITHIN if channel == "within" else BAR_IAM_ORDER1_CROSS
        ladder = [("bottom_up", iam[channel]["bottomup"], 0.0),
                  ("order1", o1, iam[channel]["order1_cf"]),
                  ("abs_rich", iam[channel]["abs"], iam[channel]["mean_cf"])]
        iam_ladders[channel] = _comovement(ladder)

    print(f"\n  CO-MOVEMENT (accuracy vs confirm-fraction across prediction richness):", flush=True)
    print(f"    SYNTH ladder r={synth_cm['pearson_r']:+.3f}  co_move={synth_cm['co_move']}  "
          f"(acc up={synth_cm['accuracy_monotone_up']}, cf up={synth_cm['confirm_monotone_up']})",
          flush=True)
    print(f"    SYNTH per-sentence r(acc,cf)={synth_persent_r:+.3f}   warm-up early->late: "
          f"acc {100*early_acc:.1f}->{100*late_acc:.1f}%  cf {100*early_cf:.1f}->{100*late_cf:.1f}%",
          flush=True)
    for channel in ("within", "cross"):
        cm = iam_ladders[channel]
        print(f"    IAM {channel} ladder r={cm['pearson_r']:+.3f}  co_move={cm['co_move']}", flush=True)

    # ---- VERDICT. WIN if AbS-predictive materially BEATS order-1 AND bigram on BOTH corpora. ----
    def beats(acc, bar, margin=0.5):
        return acc > bar + margin
    synth_win = beats(s_abs, BAR_SYNTH_ORDER1) and beats(s_abs, BAR_SYNTH_BIGRAM)
    iam_win = beats(iam["within"]["abs"], BAR_IAM_ORDER1_WITHIN) and \
        beats(iam["within"]["abs"], BAR_IAM_BIGRAM_WITHIN)
    verdict = "WIN" if (synth_win and iam_win) else ("PARTIAL" if (synth_win or iam_win) else "NULL")

    out = {
        "stage0_interface": probe["interface"],
        "sources_fire_non_narrative": probe["sources_fire_non_narrative"],
        "richness": probe["richness"], "payoff_b": probe["payoff_b"],
        "synthetic": {"bottomup": s_bu, "bigram": BAR_SYNTH_BIGRAM, "order1": BAR_SYNTH_ORDER1,
                      "abs_predictive": s_abs, "abs_arm": s_arm, "confirm_frac": s_mean_cf,
                      "order1_confirm": s_order1_cf, "n_words": ds["n_words"],
                      "mcnemar_vs_bottomup": ds["mcnemar_vs_bottomup"]},
        "iam": iam,
        "iam_mcnemar": {c: di["result"][c]["mcnemar_vs_bottomup"] for c in ("within", "cross")},
        "comovement": {"synth_ladder": synth_cm, "synth_per_sentence_r": synth_persent_r,
                       "synth_warmup": {"early_acc": 100 * early_acc, "late_acc": 100 * late_acc,
                                        "early_cf": 100 * early_cf, "late_cf": 100 * late_cf},
                       "iam_within_ladder": iam_ladders["within"],
                       "iam_cross_ladder": iam_ladders["cross"]},
        "verdict": verdict, "synth_win": synth_win, "iam_win": iam_win,
        "bars": {"synth_bigram": BAR_SYNTH_BIGRAM, "synth_order1": BAR_SYNTH_ORDER1,
                 "iam_bigram_within": BAR_IAM_BIGRAM_WITHIN, "iam_order1_within": BAR_IAM_ORDER1_WITHIN},
        "stroke_shapes_md5": md5_now,
    }
    _save(out, _ckpt("verdict.json"))
    _save(out, _ckpt("summary.json"))
    print(f"\n  VERDICT: {verdict}  (synth_win={synth_win}  iam_win={iam_win})", flush=True)
    print(f"  saved -> {_ckpt('summary.json')}", flush=True)
    print(f"\n{SEP}\n  RUN 83 COMPLETE -- see final agent report.\n{SEP}", flush=True)
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
