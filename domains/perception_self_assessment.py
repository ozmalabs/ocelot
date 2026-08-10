"""perception_self_assessment — the agent's OWN quality signal on its perceived
UNITS, so poor segmentation becomes a felt need it can flag itself.

The whole STT bottleneck this session is SEGMENTATION: the agent's perceived
units are noisy sub-word fragments. But its self-monitoring is wired DOWNSTREAM —
the meta-monitor watches `discriminative_invention` with payoff = RECOGNITION, the
do-contrast probes recognition, the impasse loop reacts to confusions. Nothing
gives the agent a yardstick on the UNITS THEMSELVES: it cannot tell a fragment
from a word, so it never flags perception. Worse, its science self-assessment
keyword-matches `segmentation -> sonority_valley` and calls it COVERED.

The missing capability is a quality signal that lives ON THE UNITS. Good units are
PREDICTABLE: in real speech the next unit is strongly constrained by the current
one (phonotactics, recurring sub-word sounds). Fragmented, unstable units carry
little such structure — next-unit prediction is near chance and the sequence
barely compresses. So PREDICTABILITY / COMPRESSIBILITY of the agent's own
unit-stream IS a yardstick on segmentation quality, computable with NO labels.

This module:
  1. (world-adapter, mechanical) ingests continuous speech through the agent's
     OWN perception, reads out the ordered sign-id sequence (signs recur via the
     pipeline's DTW merge — identity = recurrence), and computes a self-signal:
       - next-unit prediction accuracy (bigram, train/test split)  [vs chance]
       - sequence information gain  H(next) - H(next|cur)          [bits]
       - a compression proxy        (bigram-coded bits / unigram bits)
     reusing the maths from scripts/sentence_learning.py.
  2. writes that as GRAPH-RESIDENT state (a PerceptionQuality node under a
     PerceptionSelfRoot) the agent can introspect — the curiosity/compression
     drive finally reaching perception.
  3. installs a graph-resident RULE that reads PerceptionQuality and sets the
     root's `frontier` to "perception" when the units are unpredictable — so the
     agent FLAGS its own perception as the frontier from its own state.
  4. registers the signal with the meta-monitor as the `unit_segmentation`
     process: effort = distinct units coined, payoff = unit-predictability — a
     self-monitor whose PAYOFF is the perception quality, not recognition.

The decisions (is perception the frontier? is the process spinning?) are
graph-resident Rules. The Python here is the measurement adapter only: ingest,
read out the agent's unit sequence, compute statistics, write nodes. No
conditionals over graph state drive behaviour. See [[ozma_meta_abilities_are_leverage]]
/ [[ozma_curiosity_drive]] (compression as quality) / [[ozma_concepts_in_gamma]].
"""
from __future__ import annotations

import math
import random

from substrate_rs import (Attr, Lit, Var, Lt, Gt, Gte, Or, And, Not, Eq, Minus,
                          IfThenElse)


# --------------------------------------------------------------------------
# sequence statistics (the curiosity signal — reused from sentence_learning)
# --------------------------------------------------------------------------

def _entropy(counts) -> float:
    vals = list(counts.values()) if isinstance(counts, dict) else list(counts)
    tot = sum(vals)
    if tot <= 0:
        return 0.0
    h = 0.0
    for v in vals:
        if v <= 0:
            continue
        p = v / tot
        h -= p * math.log2(p)
    return h


def _conditional_next_entropy(bigrams) -> float:
    total = sum(sum(d.values()) for d in bigrams.values())
    if total <= 0:
        return 0.0
    h = 0.0
    for _cur, nexts in bigrams.items():
        n_cur = sum(nexts.values())
        h += (n_cur / total) * _entropy(nexts)
    return h


def _bigram_predict(train_seqs, test_seqs, lexicon_size):
    """Learn bigram transitions on train, predict next unit on test by argmax
    P(next|cur). Returns (top1, chance, n_pred)."""
    bigrams: dict = {}
    for seq in train_seqs:
        for a, b in zip(seq, seq[1:]):
            bigrams.setdefault(a, {}).setdefault(b, 0)
            bigrams[a][b] += 1
    ranked = {cur: [s for s, _ in sorted(nx.items(), key=lambda kv: -kv[1])]
              for cur, nx in bigrams.items()}
    n_pred = top1 = 0
    for seq in test_seqs:
        for a, b in zip(seq, seq[1:]):
            n_pred += 1
            preds = ranked.get(a)
            if preds and preds[0] == b:
                top1 += 1
    chance = 1.0 / max(lexicon_size, 1)
    if n_pred == 0:
        return 0.0, chance, 0
    return top1 / n_pred, chance, n_pred


def _frequency_predict(train_seqs, test_seqs):
    """Context-FREE baseline: always predict the globally most-frequent next unit.
    Uses NO sequential structure — only unit frequency. The bigram predictor must
    beat THIS to show the units carry order, not just a few dominant high-frequency
    units (silence/filler). This is the shuffle control's frequency floor. Returns
    (top1, n_pred)."""
    freq: dict = {}
    for seq in train_seqs:
        for b in seq[1:]:
            freq[b] = freq.get(b, 0) + 1
    top1_unit = max(freq, key=freq.get) if freq else None
    n_pred = hit = 0
    for seq in test_seqs:
        for b in seq[1:]:
            n_pred += 1
            if b == top1_unit:
                hit += 1
    if n_pred == 0:
        return 0.0, 0
    return hit / n_pred, n_pred


def measure_unit_predictability(sequences, seed: int = 1) -> dict:
    """Pure statistics on the agent's OWN unit sequences (list of [unit_key,...]).
    Returns the self-signal: next-unit prediction accuracy vs chance, sequence
    information gain (bits), and a compression proxy. No graph, no I/O — just the
    maths on the agent's output, so it can be reused/tested in isolation."""
    rng = random.Random(seed)
    seqs = [s for s in sequences if len(s) >= 2]
    seen = {tok for s in sequences for tok in s}
    lexicon_size = len(seen)
    tokens = sum(len(s) for s in sequences)

    unigram: dict = {}
    bigrams: dict = {}
    for seq in seqs:
        for a, b in zip(seq, seq[1:]):
            unigram[b] = unigram.get(b, 0) + 1
            bigrams.setdefault(a, {}).setdefault(b, 0)
            bigrams[a][b] += 1
    h_next = _entropy(unigram)
    h_next_cur = _conditional_next_entropy(bigrams)
    info_gain = h_next - h_next_cur
    # compression proxy: a perfectly-segmented stream codes the next unit in
    # H(next|cur) bits; a fragmented one needs ~H(next). ratio in (0,1]; lower =
    # MORE compressible = better units. 1.0 = order buys nothing (bag of noise).
    compress_ratio = (h_next_cur / h_next) if h_next > 1e-9 else 1.0

    rng.shuffle(seqs)
    split = max(1, int(0.8 * len(seqs))) if len(seqs) > 1 else 1
    train_seqs, test_seqs = seqs[:split], seqs[split:] or seqs[:1]
    top1, chance, n_pred = _bigram_predict(train_seqs, test_seqs, lexicon_size)
    # the honest control: how much of that predictability is the SEQUENCE vs raw
    # unit frequency (a few dominant filler units repeating)? predict_over_freq
    # near 1.0 means the apparent structure is a frequency artifact, NOT grounded
    # segmentation — exactly the trap the transcript-alignment work fell into.
    freq_top1, _ = _frequency_predict(train_seqs, test_seqs)
    predict_over_freq = top1 / freq_top1 if freq_top1 > 1e-9 else (
        float("inf") if top1 > 0 else 1.0)

    # SHUFFLE CONTROL (the yardstick's reliability witness). Pool all tokens, shuffle,
    # re-chunk into same-length pseudo-utterances: the unit FREQUENCY distribution is
    # preserved but temporal ORDER is destroyed. The same predict_over_freq is then
    # computed on this order-free stream. If the real units carry genuine order, the
    # shuffled pof drops MEANINGFULLY below the real pof (shuffle BITES). If the real
    # and shuffled pof are equal (as on a starved, singleton-dominated sample), the
    # measurement cannot see order vs no-order — the reading is unreliable. This is
    # the second of the two reliability witnesses the gate Rule reads. (Same maths as
    # scripts/sentence_learning.py's shuffle contrast.)
    all_tokens = [tok for s in seqs for tok in s]
    lengths = [len(s) for s in seqs]
    rng.shuffle(all_tokens)
    shuf_seqs, idx = [], 0
    for L in lengths:
        shuf_seqs.append(all_tokens[idx:idx + L])
        idx += L
    rng.shuffle(shuf_seqs)
    s_split = max(1, int(0.8 * len(shuf_seqs))) if len(shuf_seqs) > 1 else 1
    s_train = shuf_seqs[:s_split]
    s_test = shuf_seqs[s_split:] or shuf_seqs[:1]
    s_top1, _, s_npred = _bigram_predict(s_train, s_test, lexicon_size)
    s_freq, _ = _frequency_predict(s_train, s_test)
    shuffled_over_freq = s_top1 / s_freq if s_freq > 1e-9 else (
        float("inf") if s_top1 > 0 else 1.0)

    recurrence = (tokens - lexicon_size) / max(tokens, 1)
    # tokens-per-lexicon: the sample-adequacy witness. A stream with ~1 token per
    # distinct unit (lex ~= tokens) is singleton-dominated — there is no statistical
    # power for a bigram table, so any pof reading off it is noise, not a verdict on
    # the units. The 108-utterance FSDD subset that mis-fired sat here (lex 31, tok 61).
    tokens_per_lexicon = tokens / max(lexicon_size, 1)
    return {
        "n_utterances": len(seqs),
        "n_tokens": tokens,
        "lexicon_size": lexicon_size,
        "tokens_per_lexicon": tokens_per_lexicon,
        "recurrence": recurrence,
        "predict_top1": top1,
        "predict_chance": chance,
        "predict_over_chance": top1 / max(chance, 1e-9),
        "predict_freq_baseline": freq_top1,
        "predict_over_freq": predict_over_freq,
        "shuffled_over_freq": shuffled_over_freq,
        "n_predictions": n_pred,
        "n_shuffled_predictions": s_npred,
        "info_gain_bits": info_gain,
        "compress_ratio": compress_ratio,
    }


# --------------------------------------------------------------------------
# world-adapter: read the agent's OWN perceived unit sequence
# --------------------------------------------------------------------------

def read_unit_sequences(substrate, pipe, utterances, tick_steps: int = 50000):
    """Mechanical: ingest each utterance through the agent's perception, read out
    the ordered sign-id sequence. Signs recur (same NodeID/value) via the
    pipeline's DTW merge, so the `value` key IS the agent's unit identity. Returns
    a list of [unit_key, ...] per utterance. (utterances = iterable of np arrays.)"""
    sequences = []
    for samples in utterances:
        try:
            signs = pipe.ingest(substrate, samples)
        except Exception:
            continue
        substrate.tick(tick_steps)
        seq = []
        for s in signs:
            v = getattr(s, "value", None)
            seq.append(v if v is not None else repr(s))
        if len(seq) >= 2:
            sequences.append(seq)
    return sequences


# --------------------------------------------------------------------------
# graph-resident state + the flagging rule (the agent's own yardstick)
# --------------------------------------------------------------------------

def _root(substrate, signal="speech"):
    # ONE self-root PER SIGNAL (the faculty is modality-agnostic: speech sign-ids, visual
    # objects across frames, any perceived-unit stream). A root without a `signal` attr is
    # the original speech root, so the existing speech path matches unchanged. New signals
    # get their own root -> their own PerceptionQuality, frontier flag, and minted gap.
    for n in substrate.nodes("PerceptionSelfRoot"):
        if substrate.node(n)["attrs"].get("signal", "speech") == signal:
            return n
    # Thresholds are dials on the root (graph data, not Python constants). They say
    # what "good units" means. The PRIMARY yardstick is predict_over_freq: the
    # bigram predictor must beat the units' OWN frequency baseline by a margin —
    # otherwise the apparent predictability is a frequency artifact (a few dominant
    # filler units repeating), NOT grounded segmentation. predict_over_chance is
    # kept only as context (it is the misleading number that hid the problem).
    _r = substrate.add_node("PerceptionSelfRoot", {
        "origin": "perception_self_assessment",
        "predict_over_freq_floor": 1.25,    # bigram must beat raw frequency by 25%
        "compress_ratio_ceiling": 0.85,     # ~1.0 -> bag of noise, no structure
        # --- RELIABILITY GATE dials (graph data, the agent's "is this reading
        # trustworthy?" thresholds — never Python constants). The gate suppresses a
        # FALSE 'perception' flag on a starved / merge-grain sample.
        # (a) ADEQUATE SAMPLE: at least this many tokens per distinct unit, else the
        #     bigram table is singleton-dominated and any pof is noise. The 108-utt
        #     FSDD subset that mis-fired had tok/lex ~= 2.0; a reliable sample clears 4.
        "min_tokens_per_lexicon": 4.0,
        # (b) SHUFFLE BITES: when the units APPEAR to pass (pof >= floor), the real pof
        #     must exceed the order-destroyed (shuffled) pof by this margin — otherwise
        #     the apparent pass is a small-sample fluke, not real temporal order. A pass
        #     that survives the shuffle is a RELIABLE 'none'; one that does not is
        #     inconclusive (we cannot trust the units passed).
        "shuffle_bite_margin": 0.10,
        # the gate's verdict on the latest reading: 'high' (trustworthy) or 'low'
        # (starved / shuffle-degenerate). Written by the reliability Rule.
        "reliability": "high",
        "frontier": "none",
        "perception_quality_pending": 0,
        # The pipeline ranks the frontier-rank Rule writes from the flag (graph
        # data, not Python constants). perception/units is the most-upstream rank;
        # when the flag is 'none' the frontier is unknown -> a far-downstream
        # default so nothing sits below it. These mirror gap_prioritiser's
        # PIPELINE_LEVELS["perception_units"] / the assessor's 999 default.
        "perception_units_rank": 1.0,
        "frontier_unknown_rank": 999.0,
        # written by set_frontier_rank_from_flag (the migrated decision); seeded so
        # any reader sees a number before the rule has fired.
        "frontier_rank": 999.0,
        "frontier_rank_pending": 0,
        # the units-failing synthesis (Step 2): pending until the synthesis Rule
        # has minted the perception/units CapabilityAxis for the current shortfall.
        "perception_gap_pending": 0,
        "signal": signal,                   # which modality this root assesses (any signal)
    })
    # the self-marker the frontier-rank + gap-synthesis Rules match on (so a freshly
    # created per-signal root is immediately judged + can mint its own gap).
    try:
        substrate.add_production({
            "src": {"type": "PerceptionSelfRoot", "var": "a"}, "edge_type": "psr_self",
            "tgt": {"type": "PerceptionSelfRoot", "var": "a"},
            "provenance": "perception_self_assessment:psr_self"})
    except Exception:
        pass
    try:
        substrate.add_edge(_r, "psr_self", _r, {})
    except Exception:
        pass
    return _r


def record_perception_quality(substrate, signal: dict, modality="speech"):
    """Attach the measured self-signal as graph-resident state the agent can
    introspect: a PerceptionQuality node under the PerceptionSelfRoot for this
    `modality` (any signal). Sets the `pending` flag so the agent's flagging rule
    re-evaluates. Returns the node."""
    try:
        substrate.add_production({
            "src": {"type": "PerceptionSelfRoot", "var": "a"},
            "edge_type": "assesses",
            "tgt": {"type": "PerceptionQuality", "var": "b"},
            "provenance": "perception_self_assessment:assesses"})
    except Exception:
        pass
    root = _root(substrate, modality)
    # clamp a non-finite over_freq (no frequency hits) to a large finite number
    pof = signal.get("predict_over_freq", 1.0)
    pof = 99.0 if pof == float("inf") else float(pof)
    sof = signal.get("shuffled_over_freq", pof)
    sof = 99.0 if sof == float("inf") else float(sof)
    # tokens-per-lexicon: prefer the measured value; fall back to a derived ratio so
    # callers that hand-build a signal (tests, legacy) still feed the gate a number.
    tpl = signal.get("tokens_per_lexicon")
    if tpl is None:
        tpl = signal.get("n_tokens", 0) / max(signal.get("lexicon_size", 1), 1)
    tpl = float(tpl)
    q = substrate.add_node("PerceptionQuality", {
        "origin": "perception_self_assessment",
        "signal": modality,                              # which modality this reading assesses
        "predict_top1": float(signal["predict_top1"]),
        "predict_chance": float(signal["predict_chance"]),
        "predict_over_chance": float(signal["predict_over_chance"]),
        "predict_freq_baseline": float(signal.get("predict_freq_baseline", 0.0)),
        "predict_over_freq": pof,
        "shuffled_over_freq": sof,
        "tokens_per_lexicon": tpl,
        "info_gain_bits": float(signal["info_gain_bits"]),
        "compress_ratio": float(signal["compress_ratio"]),
        "recurrence": float(signal["recurrence"]),
        "lexicon_size": int(signal["lexicon_size"]),
        "n_tokens": int(signal["n_tokens"]),
    })
    # mirror the latest scores onto the root for the rule + meta-monitor to read
    substrate.set_attr(root, "predict_over_chance", float(signal["predict_over_chance"]))
    substrate.set_attr(root, "predict_over_freq", pof)
    substrate.set_attr(root, "shuffled_over_freq", sof)
    substrate.set_attr(root, "tokens_per_lexicon", tpl)
    substrate.set_attr(root, "compress_ratio", float(signal["compress_ratio"]))
    substrate.set_attr(root, "lexicon_size", int(signal["lexicon_size"]))
    substrate.set_attr(root, "perception_quality_pending", 1)
    try:
        substrate.add_edge(root, "assesses", q)
    except Exception:
        pass
    return q


def install_perception_frontier_rule(substrate) -> dict:
    """Install the agent's JUDGEMENT as a graph-resident Rule, GATED by a reliability
    predicate so it never mis-fires on a starved / merge-grain sample.

    The unit verdict (unchanged): the units are poor if the bigram predictor barely
    beats their OWN frequency baseline (predict_over_freq below the floor) OR the
    sequence hardly compresses (compress_ratio above the ceiling) — either symptom
    means the units carry too little real structure.

    The RELIABILITY GATE (the fix): a reading is trustworthy only when —
      • a FAIL ("bad units", pof below floor) is asserted off an ADEQUATE SAMPLE
        (tokens_per_lexicon >= min): with ~1 token per distinct unit the bigram table
        is singleton-dominated and a low pof is noise, not a verdict — exactly the
        108-utt FSDD subset (lex 31 ~= tok 61) that mis-fired. Inadequate -> the FAIL
        is untrustworthy.
      • a PASS ("good units") is asserted only when the SHUFFLE BITES (real pof
        exceeds the order-destroyed shuffled pof by the margin): a pass that the
        shuffle control cannot distinguish from order-free chance is a small-sample
        fluke, not real temporal order.
    When the reading is unreliable the Rule writes frontier = 'inconclusive' and
    reliability = 'low' — NOT a false 'perception'. When reliable it writes
    'perception' (bad units) or 'none' (good units) as before, reliability = 'high'.

    This is the agent flagging perception as its frontier FROM ITS OWN STATE, with no
    external label and no Python decision: a graph-resident IfThenElse over the sample
    + shuffle-collapse predicates, with the dials on the root. Returns
    {'root','rule_index'}."""
    nat = substrate._inner if hasattr(substrate, "_inner") else substrate
    root = _root(substrate)
    R = Var("R")
    # --- the unit verdict (same predicates as before) ---
    freq_artifact = Lt(a=Attr(R, "predict_over_freq"),
                       b=Attr(R, "predict_over_freq_floor"))
    incompressible = Gt(a=Attr(R, "compress_ratio"),
                        b=Attr(R, "compress_ratio_ceiling"))
    bad_units = Or(items=(freq_artifact, incompressible))
    # --- the two reliability witnesses (graph predicates over the dials) ---
    adequate_sample = Gte(a=Attr(R, "tokens_per_lexicon"),
                          b=Attr(R, "min_tokens_per_lexicon"))
    shuffle_gap = Minus(a=Attr(R, "predict_over_freq"),
                        b=Attr(R, "shuffled_over_freq"))
    shuffle_bites = Gte(a=shuffle_gap, b=Attr(R, "shuffle_bite_margin"))
    # a FAIL is reliable iff the sample is adequate; a PASS is reliable iff the shuffle
    # bites (real order, not a fluke). reliable = bad_units ? adequate : shuffle_bites.
    reliable = IfThenElse(bad_units, adequate_sample, shuffle_bites)
    # the gated verdict: reliable -> ('perception' if bad else 'none'); else
    # 'inconclusive' (the false 'perception' is suppressed).
    verdict = IfThenElse(bad_units, Lit("perception"), Lit("none"))
    frontier_next = IfThenElse(reliable, verdict, Lit("inconclusive"))
    reliability_next = IfThenElse(reliable, Lit("high"), Lit("low"))
    # the downstream rank / synthesis rules must arm ONLY on a reliable reading:
    # an 'inconclusive' frontier must not synthesise a perception/units gap or pull
    # the rank to 1.0. So re-arm them iff reliable, leave them 0 otherwise.
    arm_if_reliable = IfThenElse(reliable, Lit(1), Lit(0))
    # Bind R to the root by matching the root's `assesses` edge (root -> quality):
    # the source of an `assesses` edge is exactly the PerceptionSelfRoot.
    rule = {
        "name": "flag_perception_frontier",
        "match": [["R", "assesses", "Q"]],
        "where": Lit(True).to_dict(),
        "effects": [
            ["set_attr", "R", "frontier", {"__term__": frontier_next.to_dict()}],
            ["set_attr", "R", "reliability",
             {"__term__": reliability_next.to_dict()}],
            ["set_attr", "R", "perception_quality_pending", 0],
            # arm the downstream decisions that read the freshly-set flag — but ONLY
            # when the reading is reliable, so an inconclusive reading never drives the
            # rank-from-flag Rule (Step-1) or the units-gap synthesis Rule (Step-2).
            ["set_attr", "R", "frontier_rank_pending",
             {"__term__": arm_if_reliable.to_dict()}],
            ["set_attr", "R", "perception_gap_pending",
             {"__term__": arm_if_reliable.to_dict()}],
        ],
    }
    return {"root": root, "rule_index": nat.add_rule(rule)}


# --------------------------------------------------------------------------
# Step-1 migration: the frontier-flag -> frontier-RANK decision, as a graph Rule.
#
# WHY (architecture rule, [[ozma_concepts_in_gamma]] / CLAUDE.md). The previous
# process_meta_assessor.frontier_rank_from_perception was a PYTHON conditional over
# graph state: it read the flag and DECIDED the rank (`'perception' -> 1.0 else
# 999`). That `if` is a decision, so it must live in a Rule. This Rule reads the
# PerceptionSelfRoot's own `frontier` flag (already graph state, set by
# flag_perception_frontier) and writes `frontier_rank` natively via IfThenElse over
# string Eq — the same Term family the flag rule itself uses. The ranks are dials on
# the root (perception_units_rank / frontier_unknown_rank), not Python constants.
# After this, the Python feed is a mechanical read-back of the attr the Rule wrote.
# --------------------------------------------------------------------------

def install_frontier_rank_rule(substrate) -> dict:
    """Install the flag->rank DECISION as a graph-resident Rule: when the root's
    `frontier` flag is 'perception', set `frontier_rank` to the perception/units
    rank (the most-upstream pipeline rank); otherwise to the unknown/far-downstream
    default. Reads the flag + both rank dials off the root and writes the rank
    natively (IfThenElse / Eq / Attr) — no Python decision. Binds R to the root via
    a self-edge marker. Returns {'root','rule_index'}."""
    nat = substrate._inner if hasattr(substrate, "_inner") else substrate
    root = _root(substrate)
    # A DISTINCT self-marker edge ('psr_self', not the generic 'self' that
    # gap_prioritiser / measurement_feedback use on their FrontierRoot) so this
    # rule binds ONLY to the PerceptionSelfRoot and never collides with those
    # rules' self-edge matches.
    try:
        substrate.add_production({
            "src": {"type": "PerceptionSelfRoot", "var": "a"},
            "edge_type": "psr_self",
            "tgt": {"type": "PerceptionSelfRoot", "var": "b"},
            "provenance": "perception_self_assessment:psr_self"})
        substrate.add_edge(root, "psr_self", root, {})
    except Exception:
        pass
    R = Var("R")
    is_perception = Eq(a=Attr(R, "frontier"), b=Lit("perception"))
    rank_next = IfThenElse(is_perception,
                           Attr(R, "perception_units_rank"),
                           Attr(R, "frontier_unknown_rank"))
    rule = {
        "name": "set_frontier_rank_from_flag",
        "match": [["R", "psr_self", "R"]],
        "where": Eq(a=Attr(R, "frontier_rank_pending"), b=Lit(1)).to_dict(),
        "effects": [
            ["set_attr", "R", "frontier_rank", {"__term__": rank_next.to_dict()}],
            ["set_attr", "R", "frontier_rank_pending", 0],
        ],
    }
    return {"root": root, "rule_index": nat.add_rule(rule)}


def agent_set_frontier_rank(substrate, rule_index: int,
                            max_iters: int = 50) -> float:
    """Fire the flag->rank Rule until its pending flag clears, then read back the
    rank the Rule wrote. The DECISION is the Rule's; this only drives + reads."""
    nat = substrate._inner if hasattr(substrate, "_inner") else substrate
    root = _root(substrate)
    for _ in range(max_iters):
        if substrate.node(root)["attrs"].get("frontier_rank_pending") != 1:
            break
        nat.apply_rule_once(rule_index)
    return float(substrate.node(root)["attrs"].get("frontier_rank", 999.0))


# --------------------------------------------------------------------------
# Step-2 fixer: units-failing -> SYNTHESISE a perception/units CapabilityAxis.
#
# WHY (the iter-6 residual, the session's convergence point). The yardstick flags
# frontier='perception' when the units fail (predict_over_freq < floor), and the
# guided ranker (gap_prioritiser) penalises every axis below that frontier — but
# order_n_postulates synthesises NO perception/units gap (iter-6: 0 of 29 axes),
# so the closest the redirect can land is segmentation (rank 2), still below the
# rank-1 frontier. The loop cannot land on its OWN frontier.
#
# This Rule CLOSES that seam graph-resident: when the root's flag is 'perception',
# it MINTS a perception/units CapabilityAxis (level_rank = perception_units_rank,
# i.e. AT the frontier) as a real SynthesizedGap-bearing axis the ranker ranges
# over, with provenance edges back to the yardstick shortfall (the PerceptionQuality
# node) so the gap is grounded in the measured failure, not invented. The
# connection is a Rule reading the flag the yardstick set + the dials on the root;
# Python only fires it + the env-build adapter reads the node back. Idempotent:
# guarded by perception_gap_pending, cleared in the same effect.
# --------------------------------------------------------------------------

def install_perception_gap_rule(substrate) -> dict:
    """Install the units-gap SYNTHESIS as a graph-resident Rule. When the root's
    `frontier` flag is 'perception' (the yardstick says the units fail) AND a gap
    is pending, mint a perception/units CapabilityAxis AT the frontier rank and an
    `assesses`-style provenance edge from the root to it; clear the pending flag so
    exactly one axis is minted per shortfall. The whole connection (yardstick flag
    -> synthesised frontier gap) is this Rule, not Python glue. Returns
    {'root','rule_index'}."""
    nat = substrate._inner if hasattr(substrate, "_inner") else substrate
    root = _root(substrate)
    # admissible edges: root -> axis (provenance the gap was synthesised from the
    # yardstick shortfall). The self-binding uses a DISTINCT 'psr_self' marker (not
    # the generic 'self' that gap_prioritiser / measurement_feedback use on their
    # FrontierRoot) so this rule binds ONLY to the PerceptionSelfRoot.
    for et, tt in (("synthesised_gap", "CapabilityAxis"),
                   ("psr_self", "PerceptionSelfRoot")):
        try:
            substrate.add_production({
                "src": {"type": "PerceptionSelfRoot", "var": "a"},
                "edge_type": et, "tgt": {"type": tt, "var": "b"},
                "provenance": f"perception_self_assessment:{et}"})
        except Exception:
            pass
    try:
        substrate.add_edge(root, "psr_self", root, {})
    except Exception:
        pass
    R = Var("R")
    fires = And(items=(Eq(a=Attr(R, "frontier"), b=Lit("perception")),
                       Eq(a=Attr(R, "perception_gap_pending"), b=Lit(1))))
    rule = {
        "name": "synthesise_perception_units_gap",
        "match": [["R", "psr_self", "R"]],
        "where": fires.to_dict(),
        "effects": [
            # mint the perception/units axis AT the frontier rank (the dial on the
            # root), flagged is_axis so the ranker's NodesWhere ranges over it.
            ["add_node", "A", "CapabilityAxis", {
                "is_axis": 1.0,
                "signal": {"__term__": Attr(R, "signal").to_dict()},   # which sense this gap is about
                "level_rank": {"__term__": Attr(R, "perception_units_rank").to_dict()},
                "pipeline_level": "perception_units",
                "min_order": 1.0,
                "attempted_marginal": 0.0,
                "axis_sig": ["improve-unit-predictiveness",
                             "perception-units", "unit-invariance"],
                "capability_keys": ["improve-unit-predictiveness",
                                    "perception-units", "unit-invariance"],
                "gap_text": ("improve the perceived units' predictiveness / "
                             "invariance — the yardstick (predict_over_freq) "
                             "flags them below the floor; this is the frontier"),
                "origin": "perception_self_assessment:units_failing",
                "provenance": "synthesised_from_yardstick_shortfall",
                "composed_by": "agent",
            }],
            ["add_edge", "R", "synthesised_gap", "A", {}],
            ["set_attr", "R", "perception_gap_pending", 0],
        ],
    }
    return {"root": root, "rule_index": nat.add_rule(rule)}


def agent_synthesise_perception_gap(substrate, rule_index: int,
                                    max_iters: int = 8):
    """Fire the units-gap synthesis Rule until its pending flag clears; return the
    minted CapabilityAxis node id (or None if the flag was not 'perception', so no
    gap was synthesised). The DECISION (mint iff units fail) is the Rule's."""
    nat = substrate._inner if hasattr(substrate, "_inner") else substrate
    root = _root(substrate)
    before = set(substrate.nodes("CapabilityAxis"))
    for _ in range(max_iters):
        if substrate.node(root)["attrs"].get("perception_gap_pending") != 1:
            break
        nat.apply_rule_once(rule_index)
    minted = [n for n in substrate.nodes("CapabilityAxis") if n not in before]
    if minted:
        return minted[0]
    # idempotent re-call: return the existing synthesised axis if present.
    for n in substrate.neighbours(root, "synthesised_gap"):
        return n
    return None


def agent_flag_perception(substrate, rule_index: int, max_iters: int = 50) -> str:
    """Fire the flagging rule until the root's pending flag clears, then read back
    the agent's verdict. Returns the current `frontier` ('perception' or 'none')."""
    nat = substrate._inner if hasattr(substrate, "_inner") else substrate
    root = _root(substrate)
    for _ in range(max_iters):
        if substrate.node(root)["attrs"].get("perception_quality_pending") != 1:
            break
        nat.apply_rule_once(rule_index)
    return substrate.node(root)["attrs"].get("frontier", "none")


def get_frontier(substrate) -> str:
    for n in substrate.nodes("PerceptionSelfRoot"):
        return substrate.node(n)["attrs"].get("frontier", "none")
    return "none"


def get_reliability(substrate) -> str:
    """The gate's verdict on the latest reading: 'high' (trustworthy — frontier is a
    real call) or 'low' (starved / shuffle-degenerate — frontier was suppressed to
    'inconclusive'). Pure read of the attr the reliability gate wrote."""
    for n in substrate.nodes("PerceptionSelfRoot"):
        return substrate.node(n)["attrs"].get("reliability", "high")
    return "high"


# --------------------------------------------------------------------------
# meta-monitor wiring: a process whose PAYOFF is unit predictability
# --------------------------------------------------------------------------

def register_with_meta_monitor(substrate):
    """Register `unit_segmentation` with the meta-monitor so the spinning detector
    finally watches a process whose PAYOFF is perception quality (unit
    predictability), not recognition. Effort = distinct units coined. Returns the
    Process node, or None if the meta-monitor is not installed."""
    try:
        from domains.meta_monitor import register_process
    except Exception:
        return None
    return register_process(
        substrate, "unit_segmentation",
        effort_label="distinct units coined (lexicon size)",
        payoff_label="next-unit predictability over chance")


def report_to_meta_monitor(substrate, signal: dict):
    """Feed the latest self-signal to the meta-monitor for `unit_segmentation`:
    effort = lexicon size (units coined), payoff = predict_over_freq (the HONEST
    signal — context beyond the units' own frequency, not the recurrence-inflated
    over-chance number). If effort rises while this stays flat, the meta-monitor
    flags the SAME spinning pattern it flags for recognition — but now ON
    perception: the agent keeps coining units without making them more structured."""
    try:
        from domains.meta_monitor import report as meta_report
    except Exception:
        return
    pof = signal.get("predict_over_freq", 1.0)
    pof = 99.0 if pof == float("inf") else float(pof)
    meta_report(substrate, "unit_segmentation",
                float(signal["lexicon_size"]), pof)


def assess_perception(substrate, pipe, utterances, meta: bool = True) -> dict:
    """One call the world adapter makes each cycle: read the agent's own unit
    sequence from continuous speech, compute the predictability/compression
    self-signal, write it as graph-resident state, (optionally) feed the
    meta-monitor. Returns the signal dict. The agent's flagging RULE then reads
    the state and decides whether perception is its frontier."""
    sequences = read_unit_sequences(substrate, pipe, utterances)
    signal = measure_unit_predictability(sequences)
    record_perception_quality(substrate, signal)
    if meta:
        register_with_meta_monitor(substrate)
        report_to_meta_monitor(substrate, signal)
    return signal


def assess_signal(substrate, sequences, signal="speech", seed=1):
    """Generalised perception self-assessment for ANY signal. Given the agent's ordered
    perceived-unit-id sequences from any modality — speech sign-ids, visual objects tracked
    across frames, or any other perceived-unit stream — measure their predictability /
    compressibility (NO labels: good units are predictable; a unit that vanishes or jumps
    frame-to-frame is unpredictable) and record it as THIS signal's PerceptionQuality. With
    install_self_assessment in place, the frontier + gap-synthesis Rules then flag poor
    perception and MINT a CapabilityAxis tagged with this signal — the agent feels the sense
    is weak and names the gap itself. The maths + the decisions are modality-agnostic; only
    the readout (turning a raw signal into ordered unit-ids) differs per signal."""
    stats = measure_unit_predictability(sequences, seed)
    record_perception_quality(substrate, stats, modality=signal)
    return stats


def install_self_assessment(substrate) -> dict:
    """Install the whole self-assessment loop ONCE: judge poor units (frontier rule), rank
    the frontier, and SYNTHESISE a CapabilityAxis from the shortfall. The Rules match every
    PerceptionSelfRoot (Var R), so they fire PER SIGNAL — one assessment, flag and minted gap
    for each modality the agent assesses via assess_signal. This is the builder: the agent
    mints its own perception gaps (vision, audio, any) from felt shortfall, none handed in."""
    return {
        "frontier": install_perception_frontier_rule(substrate),
        "rank": install_frontier_rank_rule(substrate),
        "gap": install_perception_gap_rule(substrate),
    }


__all__ = [
    "measure_unit_predictability", "read_unit_sequences",
    "record_perception_quality", "install_perception_frontier_rule",
    "agent_flag_perception", "get_frontier", "get_reliability",
    "register_with_meta_monitor",
    "report_to_meta_monitor", "assess_perception",
    "install_frontier_rank_rule", "agent_set_frontier_rank",
    "install_perception_gap_rule", "agent_synthesise_perception_gap",
    "assess_signal", "install_self_assessment",
]
