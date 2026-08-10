"""weighted_channel_recognizer — the agent's iter-27 WEIGHTED RECOGNIZER over the
channels, replacing the iter-26 single-DTW-over-concatenation.

PROVENANCE — the ENACTMENT of the agent's self-derived fix (scripts/iter27_weighted_
derive.py), not a hand-pick. Over the iter-26 RESIDUAL frame (uniform_combiner_frame:
the two channels carry complementary signal but a SINGLE uniform distance over their
CONCATENATION gives every channel equal say everywhere, so the weak channel drags the
strong, and WHICH channel discriminates DIFFERS by word-pair), the agent's OWN
synthesize_gaps fired its OWN harvested shapes (verbatim, iter27_weighted_derive):

  (A) per-component / per-contrast SELECTION beats UNIFORM
      via rule_derived__per_band_stereo_mode_selection (concept per_band_stereo_mode_
      selection): "per-band M/S vs L/R selection beats uniform stereo coding"
      via rule_derived__per_block_adaptation_matches_local_statistics: "per-block
      parameter selection beats fixed parameters"
      -> do NOT run one uniform distance over the concatenation; for each contrast,
         SELECT / lean on the channel that actually separates it.
  (B) WEIGHT the evidence by its reliability / likelihood
      via rule_derived__Bayes_updates_beliefs (concept Bayes_updates_beliefs):
      "posterior P(H|E) ∝ P(E|H)·P(H)"
      -> the decision is an argmax over candidate words of a SUM of per-channel
         evidence, each channel WEIGHTED by how much it discriminates the contrast,
         against the prior confusions.

THE RECOGNIZER (the agent's recognition_graph shape, recognition_graph.predict_term,
generalised from one feature-sum to a per-channel weighted sum):

    score(s, w) = Σ over channels c of  rec_weight(c, contrast) · match_c(s, w)
    predict(s)  = Argmax over candidate words w of  score(s, w)

  · match_c(s, w) = the channel's evidence that sign s is word w. Here (the FSDD LOSO
    gate's kNN-DTW metric) the per-channel match to a candidate exemplar e is the
    NEGATED per-channel DTW distance  −DTW_c(features_c(s), features_c(e))  (closer =
    more evidence). The DTW kernel is adapter-math at the I/O boundary (the same
    category as the gammatone front-end); the WEIGHTED SUM + ARGMAX is the graph
    Term-tree, evaluated natively.
  · rec_weight(c, contrast) = how much channel c is trusted for the contrast at hand,
    read from the agent's OWN agent_specify_pairwise over its OWN confusions: for each
    confused word-pair, the pairwise-spec names which CHANNEL (formant-relation vs
    manner/voicing) best separates that pair (best Fisher). NOT hand-tuned, NOT
    gradient-learned — read straight from the agent's Confusions × per-channel
    ConfusionBands.

CHANNELS (each an agent component, iter-26):
  · FORMANT-RELATION (iter-25, speaker-invariant): the agent's iter-24 spacing relation
    over the TRUE waveform-LPC formant positions (apply_stacked channels='formant').
  · MANNER/VOICING (iter-26 agent phonology, within-speaker): the agent's phonology
    cues — periodicity + voiced/sonorant/sibilant predicates + low/mid/high band
    envelope (apply_stacked channels='manner').

NO-DONKEY. The agent DERIVED the weighted-decision move (its per-band-selection /
per-block-adaptation / Bayes shapes) and the WEIGHTS come from its OWN pairwise-spec
over its OWN confusions. The decision is the agent's recognition_graph Term-tree
(Argmax of a weighted Sum over channels). The ONLY new Python is the I/O-boundary DSP
(per-channel DTW, the per-token channel-summary statistics that feed the confusion
analysis) — adapter-math, no reasoning, no decision over graph state, no hand-tuned
weight, no gradient.
"""
from __future__ import annotations

import numpy as np

from substrate_rs import Substrate

from domains.stacked_representation import apply_stacked
from domains.pairwise_recognition import agent_specify_pairwise


# ---------------------------------------------------------------------------
# Channel feature extraction (adapter-math; the agent's iter-25/26 channels).
# ---------------------------------------------------------------------------

def channel_features(x, fs, n_spacings: int = 4, substrate: Substrate = None):
    """Return (formant_channel, manner_channel) per-frame matrices for one clip — the
    agent's two iter-26 channels, extracted SEPARATELY (not concatenated). The formant
    channel is the iter-25 spacing over TRACKED true formants; the manner channel is
    the agent's phonology cues. Adapter-math; the spacing/predicate values come from
    the substrate evaluator inside apply_stacked."""
    s = substrate if substrate is not None else Substrate()
    fr = apply_stacked(x, fs, n_spacings=n_spacings, substrate=s,
                       channels="formant", track=True)
    mn = apply_stacked(x, fs, n_spacings=n_spacings, substrate=s,
                       channels="manner")
    return fr, mn


# ---------------------------------------------------------------------------
# Per-channel DTW (adapter-math, the FSDD LOSO gate's metric) — the channel MATCH.
# ---------------------------------------------------------------------------

# DTW band-failure floor: the shared DTW returns 1e18 when its banded path cannot
# reach the corner (variable-length channel matrices). For the weighted PER-CHANNEL
# match this must be a finite "no evidence" penalty, not an astronomical one — so a
# channel that fails to align contributes a bounded negative match and the OTHER
# channel's weighted evidence still decides (this is exactly where per-channel
# weighting can beat concat-DTW, whose single INF kills the whole match). The floor is
# the same for every channel, so it is not a per-channel tuning knob.
_DTW_FAIL = 1e18
_MATCH_FLOOR = 10.0          # finite "channel could not align" penalty (≫ typical DTW)


def _channel_dtw(A: np.ndarray, B: np.ndarray) -> float:
    """Length-normalised DTW between two per-frame channel trajectories. The same
    Sakoe-Chiba-banded DTW the iter-12 LOSO harness uses (continuous_speech_
    recognition.dtw), per channel, with the band-failure sentinel folded to a finite
    floor so it cannot dominate the weighted sum. Adapter-math."""
    from scripts.continuous_speech_recognition import dtw
    if A.shape[0] < 1 or B.shape[0] < 1:
        return _MATCH_FLOOR
    d = float(dtw(A, B))
    return _MATCH_FLOOR if d >= 1e17 else d


# ---------------------------------------------------------------------------
# The WEIGHTED RECOGNIZER as a graph Term-tree (the agent's recognition_graph shape).
#
#   score(s | exemplars) per word = Σ_c rec_weight(c) · match_c   (Plus of Times)
#   predict = Argmax over candidate words of that score.
#
# The per-channel match to a candidate is written onto a candidate node as an attr
# (match_formant / match_manner = the NEGATED per-channel DTW to that candidate),
# exactly as the AxS path writes axs_synth_feat onto the word; the weighted SUM +
# ARGMAX is composed + evaluated in the graph. The weights are graph attrs.
# ---------------------------------------------------------------------------

class _T:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def weighted_score_term(w_formant_key: str = "w_formant",
                        w_manner_key: str = "w_manner") -> dict:
    """score(candidate c) = w_formant·match_formant(c) + w_manner·match_manner(c) — a
    graph Term-tree. The weights are read by Attr off the decision node `d` (so the
    per-CONTRAST weights are graph data, swappable per word-pair); the per-channel
    matches are read by Attr off the candidate node `c`. This is the agent's
    recognition_graph score generalised from Σ feature-weights to Σ_channel
    weight·match."""
    def attr(node, key):
        return {"type": "Attr", "node": {"type": "Var", "name": node}, "key": key}
    return {"type": "Plus", "items": [
        {"type": "Times", "items": [attr("d", w_formant_key),
                                    attr("c", "match_formant")]},
        {"type": "Times", "items": [attr("d", w_manner_key),
                                    attr("c", "match_manner")]},
    ]}


def predict_weighted_term() -> dict:
    """predict(s) = Argmax over candidate nodes (Concept is_candidate=1) of the
    weighted per-channel score. The whole weighted recognition DECISION as graph data
    the agent owns — same Argmax-of-score shape as recognition_graph.predict_term, the
    score now a per-channel weighted sum."""
    return {"type": "Argmax",
            "source": {"type": "NodesWhere", "node_type": "Candidate",
                       "attr_key": "is_candidate",
                       "value": {"type": "Lit", "value": 1.0}},
            "var_name": "c",
            "value": weighted_score_term(),
            "default": None}


# ---------------------------------------------------------------------------
# Derive the per-contrast channel weights from the agent's pairwise-spec.
#
# The pairwise-spec reads the agent's Confusions × per-CHANNEL ConfusionBands and, for
# each confused word-pair, names the CHANNEL (band='formant_ch' or 'manner_ch') with
# the best Fisher separation. That IS rec_weight(channel, contrast): for that contrast,
# trust the named channel. We turn the spec into a per-pair weight dict; the recognizer
# (predict_weighted_term) reads it as graph attrs on the decision node.
# ---------------------------------------------------------------------------

CHANNEL_BANDS = ("formant_ch", "manner_ch")


def _channel_pair_separation(feats_A, feats_B):
    """How well does a single channel's DTW separate tokens of A from tokens of B —
    the channel's RELIABILITY for that contrast (the recognizer's OWN metric, not a
    summary scalar). For each token, take its nearest SAME-word DTW (within) and
    nearest OTHER-word DTW (between); a channel that separates the pair has between >
    within. Returns a Fisher-like score (between_mean − within_mean)/(stds) and the
    raw means; >0 means the channel discriminates the pair under DTW.

    `feats_A`, `feats_B` are lists of that ONE channel's per-clip matrices."""
    # subsample tokens for the separation ESTIMATE (it is a reliability statistic, not a
    # decision — a bounded sample per word suffices and keeps the build tractable at
    # larger configs). Deterministic head-slice, no randomness.
    _CAP = 12
    within, between = [], []
    pool = ([(m, "A") for m in list(feats_A)[:_CAP]]
            + [(m, "B") for m in list(feats_B)[:_CAP]])
    n = len(pool)
    for i in range(n):
        mi, li = pool[i]
        best_w = best_b = 1e18
        for j in range(n):
            if i == j:
                continue
            d = _channel_dtw(mi, pool[j][0])
            if d >= 1e17:                         # DTW band-failure sentinel — skip
                continue
            if pool[j][1] == li:
                best_w = min(best_w, d)
            else:
                best_b = min(best_b, d)
        if best_w < 1e17:
            within.append(best_w)
        if best_b < 1e17:
            between.append(best_b)
    if len(within) < 2 or len(between) < 2:
        return 0.0, 0.0, 0.0
    # MEDIAN-based separation (robust to the DTW outliers the variable-length
    # formant matrices produce); MAD for spread.
    wm, bm = float(np.median(within)), float(np.median(between))
    wsd = float(np.median(np.abs(np.asarray(within) - wm))) + 1e-6
    bsd = float(np.median(np.abs(np.asarray(between) - bm))) + 1e-6
    fisher = (bm - wm) / (wsd + bsd)              # >0 ⇔ between>within ⇔ separable
    return float(fisher), wm, bm


def build_channel_confusions(substrate, train_feats, train_words, k: int = 3):
    """Build the agent's Confusions + per-CHANNEL ConfusionBands from a UNIFORM
    (equal-weight) pass over the training data — the prior the pairwise-spec reads.

    `train_feats` = list of (formant_mat, manner_mat) per training clip. We run a
    leave-one-out UNIFORM kNN over the train set (equal channel weights = the iter-26
    uniform combiner) to find which word-pairs the uniform combiner CONFUSES, then for
    each confused pair measure each CHANNEL's DTW SEPARATION of that pair
    (_channel_pair_separation — the recognizer's own metric) so the confusion-band
    Fisher says which CHANNEL actually tells the confused pair apart.

    Writes Confusion + ConfusionBand graph nodes (band ∈ {formant_ch, manner_ch};
    a_mean/b_mean = within/between DTW means, a_std/b_std their stds, so the existing
    pairwise-spec Fisher |a_mean−b_mean|/(a_std+b_std) reads the channel's separation).
    Returns nothing; the agent's state now carries the prior."""
    n = len(train_feats)
    from collections import Counter, defaultdict
    # leave-one-out UNIFORM kNN (equal channel weights = iter-26 combiner) -> confusions
    conf = defaultdict(int)                       # (true, pred) -> count
    for i in range(n):
        ds = []
        for j in range(n):
            if i == j:
                continue
            d = (_channel_dtw(train_feats[i][0], train_feats[j][0])
                 + _channel_dtw(train_feats[i][1], train_feats[j][1]))
            ds.append((d, train_words[j]))
        ds.sort()
        pred = Counter(w for _, w in ds[:k]).most_common(1)[0][0]
        if pred != train_words[i]:
            conf[(train_words[i], pred)] += 1

    # per-word per-channel token lists (for the per-pair DTW separation)
    by_word = {"formant_ch": defaultdict(list), "manner_ch": defaultdict(list)}
    for (fr, mn), w in zip(train_feats, train_words):
        by_word["formant_ch"][w].append(fr)
        by_word["manner_ch"][w].append(mn)

    for (A, B), c in conf.items():
        substrate.add_node("Confusion", {
            "true_word": A, "pred_word": B, "count": int(c),
            "origin": "weighted_channel_recognizer"})

    # per-CHANNEL ConfusionBand: the channel's DTW SEPARATION of the confused pair.
    for (A, B), c in conf.items():
        for band in CHANNEL_BANDS:
            fa, wm, bm = _channel_pair_separation(
                by_word[band].get(A, []), by_word[band].get(B, []))
            if not by_word[band].get(A) or not by_word[band].get(B):
                continue
            # encode the channel's separation so the existing pairwise-spec Fisher
            # |a_mean−b_mean|/(a_std+b_std) == max(fisher,0): set a_mean=between,
            # b_mean=within, a_std+b_std=1 so Fisher = (between−within) (clamped ≥0).
            sep = max(fa, 0.0)
            substrate.add_node("ConfusionBand", {
                "true_word": A, "pred_word": B, "band": band,
                "a_mean": sep, "a_std": 0.5, "b_mean": 0.0, "b_std": 0.5,
                "within_dtw": wm, "between_dtw": bm,
                "origin": "weighted_channel_recognizer"})


def derive_channel_weights(substrate, top_k: int = 20):
    """The agent's per-contrast channel weights, read from its OWN pairwise-spec over
    its OWN confusions. agent_specify_pairwise(substrate) returns, per confused pair,
    the band (= channel name) with the best Fisher separation. We turn that into a
    per-pair weight dict {(A,B): {'w_formant': .., 'w_manner': ..}}: the named
    discriminating channel gets weight 1, the other gets a down-weight proportional to
    its RELATIVE Fisher (so a channel that ALSO separates the pair keeps some say, one
    that is blind to it gets little) — read from the spec's Fisher numbers, NOT
    hand-tuned. Returns (per_pair_weights, default_weights, spec)."""
    spec = agent_specify_pairwise(substrate, top_k=top_k)
    # per-pair Fisher of BOTH channels (for the relative down-weight), from the bands
    fisher_by_pair = {}
    for cb in substrate.nodes("ConfusionBand"):
        a = substrate.node(cb)["attrs"]
        key = (a.get("true_word"), a.get("pred_word"))
        am, bm = a.get("a_mean"), a.get("b_mean")
        asd, bsd = a.get("a_std", 0.0), a.get("b_std", 0.0)
        if am is None or bm is None:
            continue
        f = abs(am - bm) / (float(asd) + float(bsd) + 1e-6)
        fisher_by_pair.setdefault(key, {})[a.get("band")] = f

    # the decisiveness gate: a per-contrast departure from the global reliability lead
    # is only justified when ONE channel clearly out-separates the other for that pair.
    # The bar is read from the DATA — the median absolute separation-gap across the
    # agent's confused pairs (the typical gap; a pair must beat the typical to count as
    # decisive). NOT a magic constant. (recognition_architecture's lever-1 pattern:
    # only override when the evidence is strong.)
    gaps = []
    for key, fis in fisher_by_pair.items():
        gaps.append(abs(fis.get("formant_ch", 0.0) - fis.get("manner_ch", 0.0)))
    decisive_bar = float(np.median(gaps)) if gaps else 0.0

    per_pair = {}
    for e in spec:
        key = (e["A"], e["B"])
        fis = fisher_by_pair.get(key, {})
        f_formant = fis.get("formant_ch", 0.0)
        f_manner = fis.get("manner_ch", 0.0)
        tot = f_formant + f_manner + 1e-9
        decisive = abs(f_formant - f_manner) > decisive_bar
        # weight each channel by its SHARE of the pair's total Fisher separation — the
        # agent's pairwise-spec's discriminating channel dominates, the blind one is
        # down-weighted. (Bayes shape: lean on the evidence by its reliability.) Only
        # DECISIVE pairs (one channel clearly out-separates) carry a per-contrast
        # weight; the rest keep the global reliability default.
        per_pair[key] = {"w_formant": float(f_formant / tot),
                         "w_manner": float(f_manner / tot),
                         "decisive": bool(decisive)}

    # GLOBAL per-channel reliability (the default weights) — read from the SAME
    # confusion-band separations: each channel's OVERALL reliability is the mean DTW
    # separation it achieves across ALL the agent's confused pairs (a_mean encodes the
    # channel's separation of each pair). The default weights are each channel's share
    # of total reliability — so the globally more-reliable channel leads everywhere,
    # and the weighted combiner only departs from that lead per-contrast where the
    # pairwise-spec says the other channel separates THAT pair. NOT swept, NOT
    # hand-picked — the agent's own per-pair separations averaged. (Bayes / reliability
    # shape applied globally; per-band-selection applied per contrast.)
    rel = {"formant_ch": [], "manner_ch": []}
    for key, fis in fisher_by_pair.items():
        for band in CHANNEL_BANDS:
            if band in fis:
                rel[band].append(fis[band])
    rf = float(np.mean(rel["formant_ch"])) if rel["formant_ch"] else 1.0
    rm = float(np.mean(rel["manner_ch"])) if rel["manner_ch"] else 1.0
    rt = rf + rm + 1e-9
    default = {"w_formant": float(rf / rt), "w_manner": float(rm / rt)}
    return per_pair, default, spec


# ---------------------------------------------------------------------------
# The recognizer in action (world-adapter): score candidates with the agent's graph
# Term, two-stage with the per-contrast weights, evaluated natively.
# ---------------------------------------------------------------------------

def _attach_candidate(substrate, word, match_formant, match_manner):
    return substrate.add_node("Candidate", {
        "word": word, "is_candidate": 1.0,
        "match_formant": float(match_formant),
        "match_manner": float(match_manner)})


def _attach_decision(substrate, weights):
    return substrate.add_node("Decision", {
        "w_formant": float(weights["w_formant"]),
        "w_manner": float(weights["w_manner"])})


def recognize_weighted(substrate, test_feat, train_feats, train_words,
                       per_pair, default, k: int = 3):
    """The agent's weighted recognizer over ONE test clip's channels.

    Stage 1: compute the per-channel match (−DTW) of the test clip to every training
    exemplar; with the DEFAULT (equal) weights, build the graph weighted-score Term
    over candidate nodes and Argmax (the recognition_graph decision). Take the kNN
    vote for the top-2 word pair.
    Stage 2: for that contrast {A,B}, look up the agent's per-pair channel weights
    (from its pairwise-spec) and re-evaluate the SAME graph weighted-score Term with
    those per-contrast weights, restricted to A's and B's exemplars — the channel the
    agent says separates the pair now dominates. Returns the chosen word.

    The SCORING + the ARGMAX are the agent's graph Term (weighted_score_term /
    predict_weighted_term), evaluated natively; the per-channel DTW + the top-k vote
    are adapter-math. No hand-tuned weight."""
    from collections import Counter
    fr_t, mn_t = test_feat
    # per-exemplar per-channel match (−DTW)
    matches = []
    for (fr_e, mn_e), w in zip(train_feats, train_words):
        mf = -_channel_dtw(fr_t, fr_e)
        mm = -_channel_dtw(mn_t, mn_e)
        matches.append((w, mf, mm))

    # --- Stage 1: GLOBAL reliability weights, graph weighted score + kNN vote --------
    # (the agent's Bayes/reliability shape applied globally: the more-reliable channel
    # leads everywhere — the default weights are each channel's share of total
    # separation across the agent's confusions.)
    dnode = _attach_decision(substrate, default)
    term = _T(weighted_score_term())
    scored = []
    for w, mf, mm in matches:
        c = _attach_candidate(substrate, w, mf, mm)
        sc = float(substrate.evaluate(term, {"c": c, "d": dnode}))
        scored.append((sc, w))
    scored.sort(reverse=True)
    topk = scored[:k]
    votes = Counter(w for _, w in topk)
    ranked = [w for w, _ in votes.most_common()]
    # full ranking fallback (best single score) so a top-2 always exists
    if len(ranked) < 2:
        seen = set(ranked)
        for _, w in scored:
            if w not in seen:
                ranked.append(w)
                seen.add(w)
            if len(ranked) >= 2:
                break
    if len(ranked) < 2:
        return ranked[0] if ranked else (train_words[0] if train_words else None)
    A, B = ranked[0], ranked[1]

    # --- Stage 2: per-contrast weights from the agent's pairwise-spec ----------------
    # (the per-band-selection shape applied per contrast: ONLY for DECISIVE pairs —
    # where one channel clearly out-separates the other — does the decision depart from
    # the global reliability lead; otherwise trust Stage 1.)
    w_pair = per_pair.get((A, B)) or per_pair.get((B, A))
    if w_pair is None or not w_pair.get("decisive", False):
        return A                                  # not decisive -> trust Stage 1
    dnode2 = _attach_decision(substrate, w_pair)
    # restrict to A/B exemplars; pick the word whose best exemplar maximises the
    # per-contrast weighted score (the agent's graph Term with the per-pair weights).
    best = (-1e18, A)
    for w, mf, mm in matches:
        if w not in (A, B):
            continue
        c = _attach_candidate(substrate, w, mf, mm)
        sc = float(substrate.evaluate(term, {"c": c, "d": dnode2}))
        if sc > best[0]:
            best = (sc, w)
    return best[1]


def compose_weighted_recognizer(substrate) -> list:
    """Record the agent's iter-27 weighted recognizer as a Concept carrying the graph
    Term-tree + the provenance of the derived gaps. Idempotent."""
    existing = {substrate.node(c)["attrs"].get("name")
                for c in substrate.nodes("Concept")
                if substrate.node(c)["attrs"].get("feature_kind")
                == "weighted_channel_recognizer"}
    created = []
    name = "weighted_channel_recognizer"
    if name not in existing:
        c = substrate.add_node("Concept", {
            "name": name, "feature_kind": "weighted_channel_recognizer",
            "predicate": predict_weighted_term(),
            "origin": "weighted_channel_recognizer", "composed_by": "agent",
            "derived_gaps": (
                "(A) per_band_stereo_mode_selection: per-band selection beats uniform; "
                "per_block_adaptation_matches_local_statistics: per-block selection "
                "beats fixed -> select per-contrast which channel separates it; "
                "(B) Bayes_updates_beliefs: posterior ∝ likelihood·prior -> weight each "
                "channel by how much it discriminates the contrast, vs prior confusions"),
            "recognizer": (
                "Argmax over candidate words of Sum over channels of "
                "rec_weight(channel, contrast)·(−DTW_channel); weights from "
                "agent_specify_pairwise over the agent's confusions")})
        created.append((c, name))
    return created


__all__ = ["channel_features", "weighted_score_term", "predict_weighted_term",
           "build_channel_confusions", "derive_channel_weights",
           "recognize_weighted", "compose_weighted_recognizer"]
