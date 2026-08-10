"""many_settings_recognizer — iter-33: recognition as the agent's combinatorial
PRODUCT over MANY SETTINGS of its filters/transforms, each setting a node.

THE INSIGHT (user, iter-33): "there is no reason to have ONE setting for a
particular filter or transform; that's the whole point of a graph." iter-32's
residual was NODE QUALITY — one strong channel (the spectral-detail flat readout)
and several weaker ones. The cues are weak NOT because the filter is weak but
because each is ONE SETTING — one time-frequency tradeoff — and the uncertainty
principle caps any single setting. A GRAPH has MANY settings of the same filter,
each a node, ALL COMBINED; the cap is on one channel, but many channels at
different tradeoffs, fused, dissolve it. The agent already proved this with TWO
ears (a freq-sharp FFT ear complementary to the gammatone ear, fused beats either
— scripts/two_ears_demo.py, ozma_wall_is_self_imposed). This generalises two ears
to N ears / N settings.

THE GENERALISATION OF iter-32:
  iter-32 combined TWO channels (flat, trans) via the Bayes product
  P_flat(w|s)·P_trans(w|s). This module combines N channels — each a SETTING of a
  filter/transform — via the SAME Bayes product, the agent's derived combination
  shape (scripts/iter32_combinatorial_derive.py: Bayes_updates_beliefs,
  posterior ∝ Π likelihood). The decision is the agent's recognition_graph
  Argmax of a variadic Times over the per-setting likelihood attrs.

      P_c(w | s)  = channel c's softmax-likelihood that s is word w
                  = softmax over candidates of -D_c(s,w)/T_c
         D_c(s,w) = channel c's MIN cosine distance from s to a TRAIN exemplar of w
                    (the channel's own 1-NN exemplar evidence — the harness metric)
         T_c      = channel c's OWN scale = median candidate distance (scale-free
                    per channel; READ from the data per query, NOT searched)

      score(s, w) = Π_c P_c(w | s)              (the Bayes PRODUCT over ALL settings)
      predict(s)  = Argmax over candidate words w of score(s, w)   (graph Term)

NO-DONKEY + THE ONE HARD RULE: we COMBINE ALL settings — every instantiated
setting stays as a node feeding the product. We do NOT sweep-and-keep-the-best
(that is the forbidden negative-space search, ozma_forward_design_not_search). No
fit, no selection of a winning setting, no global hand-weight: the N likelihoods
enter the product symmetrically (the Bayes form), each scale-normalised by its OWN
median distance (read from the data, not searched). The combinatorial product
sorts the settings out — a setting uninformative for a contrast multiplies in
near-flat and cannot drag the settings that carry it; a setting that sharply
separates the candidates dominates the product where it is confident.
"""
from __future__ import annotations

import numpy as np


WORD_ATTR = "is_word"


def _V(n): return {"type": "Var", "name": n}
def _Lit(v): return {"type": "Lit", "value": v}
def _Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def _Times(items): return {"type": "Times", "items": items}
def _Argmax(src, var, val): return {"type": "Argmax", "source": src,
                                    "var_name": var, "value": val, "default": None}
def _NodesWhere(t, k, v): return {"type": "NodesWhere", "node_type": t,
                                  "attr_key": k, "value": v}


def channel_attr(i: int) -> str:
    """Attr key for the per-channel likelihood of setting i on a word node."""
    return f"p_ch{i}"


class _Pred:
    """Lightweight wrapper so a Term dict can be evaluated by substrate.evaluate
    via substrate_rs (same shape combinatorial_recognizer._Pred uses)."""
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def many_settings_score_term(n_channels: int) -> dict:
    """score(s, w) = Π_{i<n} P_i(w|s) — the Bayes PRODUCT over ALL N settings, as a
    graph Term (a variadic Times over the per-setting likelihood attrs on the
    candidate word w). Each likelihood is a graph attr the adapter populated per
    query (the setting's own 1-NN exemplar evidence, scale-free). The product is
    the agent's derived combination — every setting keeps its role; ALL combine;
    none is selected or weighted."""
    return _Times([_Attr(_V("w"), channel_attr(i)) for i in range(n_channels)])


def predict_many_settings_term(n_channels: int) -> dict:
    """predict(s) = Argmax over candidate words of Π_i P_i(w|s). The whole
    many-settings combinatorial decision as graph data the agent owns — the same
    Argmax-of-score shape as recognition_graph.predict_term, the score being the
    Bayes product over ALL the settings' per-candidate likelihoods."""
    return _Argmax(_NodesWhere("Concept", WORD_ATTR, _Lit(1.0)), "w",
                   many_settings_score_term(n_channels))


# ---- per-channel likelihood (one setting's own 1-NN exemplar evidence) ----

def _channel_distances(query_vec: np.ndarray, train_vecs: np.ndarray,
                       train_words, candidate_words) -> dict:
    """D_c(s, w) per candidate = the channel's MIN cosine distance from the query
    to any TRAIN exemplar of w (the channel's 1-NN exemplar evidence — the SAME
    cosine the harness's heldout_1nn uses, kept per-word). {word: min_dist}."""
    q = query_vec / (np.linalg.norm(query_vec) + 1e-9)
    Xn = train_vecs / (np.linalg.norm(train_vecs, axis=1, keepdims=True) + 1e-9)
    sims = Xn @ q
    dist = 1.0 - sims
    tw = np.asarray(train_words)
    out = {}
    for w in candidate_words:
        mask = (tw == w)
        out[w] = float(dist[mask].min()) if mask.any() else float("inf")
    return out


def likelihood_from_distances(dists: dict) -> dict:
    """P_c(w|s) = softmax over candidates of -D_c(s,w)/T_c, T_c = the channel's OWN
    scale = median finite candidate distance (scale-free; read from the data, NOT
    searched). {word: distance} -> {word: likelihood in [0,1]}. The shared softmax-
    by-own-median EVERY channel uses; factored out so a channel whose distance is
    NOT a cosine (e.g. the AxS node's DTW synth-error) reuses the identical math —
    same no-fit temperature, no per-channel weight, no tuning."""
    finite = [d for d in dists.values() if np.isfinite(d)]
    if not finite:
        n = max(len(dists), 1)
        return {w: 1.0 / n for w in dists}
    T = float(np.median(finite)) or 1e-6
    logits = {w: (-d / T if np.isfinite(d) else -1e9) for w, d in dists.items()}
    m = max(logits.values())
    exps = {w: np.exp(v - m) for w, v in logits.items()}
    Z = sum(exps.values()) + 1e-12
    return {w: float(e / Z) for w, e in exps.items()}


def channel_likelihood(query_vec: np.ndarray, train_vecs: np.ndarray,
                       train_words, candidate_words) -> dict:
    """P_c(w|s) for one setting = softmax over candidates of -D_c(s,w)/T_c, with
    T_c = the setting's OWN scale = median finite candidate distance (scale-free;
    read from the data, NOT searched). {word: likelihood in [0,1]}.

    Identical math to combinatorial_recognizer.channel_likelihood — the per-setting
    evidence on a common [0,1] footing so ALL settings can be MULTIPLIED. A setting
    that cannot separate the candidates yields a near-flat likelihood (multiplies in
    near-uniform, cannot drag the rest); a setting that sharply prefers one
    candidate yields a peaked likelihood and dominates the product where confident."""
    dists = _channel_distances(query_vec, train_vecs, train_words, candidate_words)
    return likelihood_from_distances(dists)


# ---------------------------------------------------------------------------
# EXCLUSION-CALIBRATED likelihood (ozma_recognition_is_exclusion): the ear works
# BACKWARDS. The positive question ("is it X?") is FUZZY; the negative ("is it
# NOT-X?") is SHARP — the reliable information is in the NOTs. So a cue's
# likelihood is a ONE-SIDED EXCLUSION, not a positive peak:
#   · ABSTAIN (likelihood ~1) for EVERY candidate the cue cannot confidently rule
#     out — the best match AND every consistent-or-ambiguous candidate. No positive
#     vote is cast; "maybe" is treated as "yes for now" (= no information removed).
#   · EXCLUDE (likelihood -> 0) ONLY where the cue CONFIDENTLY rules the candidate
#     out: its distance to that word's banked evidence is far BEYOND a margin past
#     the nearest (most-consistent) candidate. A penalty, never a peak.
#   · GATE: if the cue cannot separate the candidates at all (its candidate-distance
#     SPREAD is small relative to its own scale — low separability), the WHOLE cue
#     abstains (~flat) and contributes nothing to the product.
# The margin is DERIVED from the cue's OWN distance spread (median absolute
# deviation) — no fit, no training, no searched temperature. Combined under the
# product, a candidate SURVIVES unless some cue confidently excludes it; argmax
# over survivors. Adding a cue can then only EXCLUDE (help) or ABSTAIN (free) —
# never cast a noisy positive vote. This is the Bayes product, exclusion-calibrated.

# how many spread-units of excess distance past the nearest candidate before a
# candidate is considered confidently EXCLUDED. Derived stance, not a fit knob:
# k=2 is "two robust-sigma beyond the best match" — the same 2-sigma confident-not
# the seven<->zero voicing separation used (zero /z/ 0.57 vs six /s/ 0.32, ~2.7sigma).
_EXCL_MARGIN_K = 2.0
# the cue-level separability gate: if the candidate distances' robust spread is below
# this fraction of the cue's own scale (median distance), the cue cannot discriminate
# this contrast -> the whole cue abstains (flat). Derived from the cue's own numbers.
_EXCL_GATE_FRAC = 0.05


def exclusion_likelihood_from_distances(dists: dict) -> dict:
    """L_c(w|s) = the cue's ONE-SIDED EXCLUSION over candidates. 1.0 (ABSTAIN) for
    every candidate within the margin of the nearest; decays toward 0 (EXCLUDE) only
    for candidates whose distance is confidently beyond the margin. {word: dist} ->
    {word: likelihood in (0,1]}. Margin + gate derived from the cue's OWN distance
    spread (median + MAD) — no fit, no searched temperature, no positive peak."""
    finite = [d for d in dists.values() if np.isfinite(d)]
    if len(finite) < 2:
        # cannot form a contrast -> the cue abstains on everything.
        return {w: 1.0 for w in dists}
    arr = np.asarray(finite, dtype=np.float64)
    d_min = float(arr.min())
    med = float(np.median(arr))
    # robust spread = median absolute deviation about the median (scaled to ~std for a
    # normal), floored to the cue's scale so a degenerate spread can't divide-by-zero.
    mad = float(np.median(np.abs(arr - med))) * 1.4826
    scale = med if med > 1e-9 else 1.0
    spread = max(mad, 1e-9)
    # GATE: if the candidate distances barely spread relative to the cue's own scale,
    # the cue cannot tell the candidates apart -> abstain on ALL (flat, contributes 1).
    if spread < _EXCL_GATE_FRAC * scale:
        return {w: 1.0 for w in dists}
    out = {}
    for w, d in dists.items():
        if not np.isfinite(d):
            # no banked evidence for w under this cue -> the cue cannot exclude it
            # (absence of evidence is not evidence of exclusion). Abstain.
            out[w] = 1.0
            continue
        # excess distance past the nearest (most-consistent) candidate, in spread units.
        excess = (d - d_min) / spread
        if excess <= _EXCL_MARGIN_K:
            out[w] = 1.0                      # within margin -> consistent -> ABSTAIN
        else:
            # confidently far -> EXCLUDE. Smooth one-sided decay so it is graded, not a
            # hard cliff: exp(-(excess - k)) in (0,1), reaching ~0 for very-far candidates.
            out[w] = float(np.exp(-(excess - _EXCL_MARGIN_K)))
    return out


def channel_likelihood_exclusion(query_vec: np.ndarray, train_vecs: np.ndarray,
                                 train_words, candidate_words) -> dict:
    """EXCLUSION-calibrated per-cue likelihood: ABSTAIN (~1) for consistent candidates,
    EXCLUDE (->0) only the confidently-far. Drop-in for channel_likelihood but with the
    exclusion shape (ozma_recognition_is_exclusion). Same 1-NN exemplar distances; the
    only change is the calibration from a positive softmax peak to a one-sided exclusion
    gated by the cue's own separability."""
    dists = _channel_distances(query_vec, train_vecs, train_words, candidate_words)
    return exclusion_likelihood_from_distances(dists)


# ---------------------------------------------------------------------------
# VECTOR-WEIGHTED per-cue likelihood (ozma_weighting_is_a_vector): a cue's stance
# toward a candidate is NEVER one number. The FLAT recognizer projected it onto the
# POSITIVE/RANK axis only (a noisy positive vote -> the manner cue HURT, -0.050). The
# EXCLUSION recognizer projected it onto the EXCLUDE axis only (abstain-or-rule-out ->
# the ceiling DROPPED, abstention left flat survivors with no positive signal). Both
# are a VECTOR PROJECTED ONTO A SCALAR. The fix is to KEEP THE VECTOR: each cue emits
# a 2-component vector per candidate
#
#       v_c(w | s) = [ EXCLUDE_c(w|s),  RANK_c(w|s) ]
#
#   · EXCLUDE axis = the one-sided exclusion (exclusion_likelihood_from_distances):
#     ~1 ABSTAIN within margin, decaying to 0 EXCLUDE confidently beyond, the whole
#     cue gated to ABSTAIN when it can't separate the contrast. The "NOT" axis — it
#     rules out confident-nots.
#   · RANK axis = the positive match score (the FLAT softmax likelihood): the signal
#     that RANKS among survivors. The positive evidence.
#
# COMBINE WITHOUT COLLAPSE — the two axes compose by DIFFERENT operators, neither
# projected away:
#   · EXCLUDE combines by PRODUCT (conjunction): a candidate survives unless SOME cue
#     confidently excludes it (Π exclude).
#   · RANK combines by SUM (accumulation): positive evidence accumulates across cues
#     (Σ rank).
#   · final score(w) = exclude_product(w) * rank_sum(w) — the surviving mass scaled by
#     the accumulated positive rank; argmax over candidates. Both axes kept: the
#     exclude product gates OUT the confident-nots (recovering the exclusion "not"), the
#     rank sum RANKS the survivors (recovering the ceiling pure-exclude lost). No
#     projection to a single positive vote; no projection to pure exclude.
# Per-contrast (the existing separability gate lives inside the EXCLUDE axis). Composed
# from the agent's owned ops (the same exclusion + softmax likelihoods); NO fit, NO
# searched temperature, NO learned weight, NO net.

def channel_vector(query_vec: np.ndarray, train_vecs: np.ndarray,
                   train_words, candidate_words) -> dict:
    """v_c(w|s) = [EXCLUDE_c(w|s), RANK_c(w|s)] per candidate — the cue's VECTOR stance.
    EXCLUDE = the one-sided exclusion (exclusion_likelihood, the "not" axis); RANK = the
    positive softmax match (channel_likelihood, the survivor-ranking axis). Both from the
    SAME 1-NN exemplar distances, computed ONCE. {word: (exclude, rank)}. The cue is NOT
    collapsed to either scalar — both axes are returned for the no-collapse combine."""
    dists = _channel_distances(query_vec, train_vecs, train_words, candidate_words)
    exclude = exclusion_likelihood_from_distances(dists)   # the NOT axis
    rank = likelihood_from_distances(dists)                # the positive RANK axis
    return {w: (exclude[w], rank[w]) for w in candidate_words}


def combine_vectors(per_cue_vectors: list, candidate_words) -> dict:
    """COMBINE WITHOUT COLLAPSE over a list of per-cue {word: (exclude, rank)} vectors.
    EXCLUDE axis -> PRODUCT (conjunction: a candidate survives unless some cue confidently
    excludes it). RANK axis -> SUM (positive evidence accumulates). Final score per word =
    exclude_product * rank_sum — the surviving mass scaled by the accumulated positive
    rank. {word: score}; argmax over this is the agent's vector-weighted decision. Both
    axes are kept through to the final compose; neither is projected away."""
    excl_prod = {w: 1.0 for w in candidate_words}   # Π over cues (conjunction)
    rank_sum = {w: 0.0 for w in candidate_words}    # Σ over cues (accumulation)
    for vec in per_cue_vectors:
        for w in candidate_words:
            e, r = vec[w]
            excl_prod[w] *= e
            rank_sum[w] += r
    # compose the two axes WITHOUT collapsing either: surviving mass * accumulated rank.
    return {w: excl_prod[w] * rank_sum[w] for w in candidate_words}


# ---------------------------------------------------------------------------
# QUANTUM-PROBABILITY recognizer (ozma_postulate_is_a_quantum_state /
# ozma_collapse_is_gamma_application). The classical combines (FLAT product,
# EXCLUSION, VECTOR) are ALL commutative (order-blind) and interference-free
# (a sum/product of paths, no cross-terms). The quantum framing:
#   · WORD-STATE  psi  = a COMPLEX amplitude vector over the candidate words — a
#     SUPERPOSITION of held word-hypotheses (init uniform, the flat prior). This
#     is the postulate-as-quantum-state: candidate identities held OPEN at once.
#   · CUE = MEASUREMENT OPERATOR M_c, built FROM the cue's per-word 1-NN distances
#     (the SAME evidence the classical recognizer uses). Applied psi -> M_c psi,
#     renormalized — a (weak) measurement that amplifies consistent words and
#     suppresses inconsistent ones. = Gamma-application / collapse.
#   · SEQUENTIAL, NON-COMMUTING: psi_final = M_K ... M_2 M_1 psi. Order can matter
#     because the operators need not commute (the off-diagonal coupling below).
#   · BORN: P(w) = |psi_final(w)|^2 ; recognize = argmax. The interference lives in
#     the complex cross-terms — the soft/vector Gamma is the Born weighting.
#
# THE OPERATOR (composable linear algebra, owned ops; NO fit / net / searched param):
#   From cue c's distances D_c(w) build the COMPLEX evidence amplitude vector e_c:
#     |e_c(w)|   = exp(-D_c(w) / (2 T_c)),  T_c = the cue's OWN scale = median finite
#                  candidate distance (read from the data, NOT searched). The SQRT of
#                  the classical Gaussian likelihood, so |e_c(w)|^2 reduces EXACTLY to
#                  the classical softmax-likelihood factor.  (Born: |amp|^2 = prob.)
#     arg(e_c(w)) = PHI * margin_c(w),  margin_c(w) = (med_c - D_c(w)) / spread_c, the
#                  cue's SIGNED MARGIN in robust-spread (MAD) units — POSITIVE where the
#                  cue prefers w (nearer than typical), NEGATIVE where it disprefers it.
#                  The phase is DERIVED from the cue's own signed margin; PHI = pi/2 is a
#                  fixed structural quarter-turn per spread-unit (a unit choice, NOT tuned
#                  on accuracy). Zeroing PHI removes the phase => no interference.
#   The measurement operator couples a per-word DIAGONAL consistency term with a rank-1
#   complex outer-product BACK-ACTION term (the part that makes M_c NON-DIAGONAL, hence
#   NON-COMMUTING, and produces |psi|^2 cross-terms):
#     M_c = (1 - BETA) * diag(e_c)  +  BETA * (e_hat_c  e_hat_c^dagger)
#   with e_hat_c = e_c / ||e_c|| the normalized complex evidence direction. BETA in [0,1]
#   is the measurement STRENGTH (how projective the cue is). At BETA = 0 the operator is
#   purely diagonal => operators COMMUTE and |psi_final|^2 is exactly the classical
#   product (the quantum recognizer CONTAINS the classical one as its zero-coupling,
#   zero-phase limit). At BETA > 0 the rank-1 term mixes word amplitudes => the operators
#   stop commuting (order effects) and the Born readout carries interference cross-terms.
#   BETA is a fixed structural constant (1/2 — the maximally-balanced weak measurement,
#   half diagonal half projective), documented, NOT searched on accuracy.

# the phase-per-spread-unit (a quarter turn per robust-spread unit of signed margin). A
# UNIT choice (derived from the cue's own MAD spread), NOT a knob fit on accuracy.
_Q_PHI = np.pi / 2.0
# the measurement strength: half diagonal (consistency), half rank-1 projector
# (back-action / interference). The maximally-balanced weak measurement; structural, not fit.
_Q_BETA = 0.5


def cue_amplitude(query_vec: np.ndarray, train_vecs: np.ndarray,
                  train_words, candidate_words, phi: float = _Q_PHI) -> np.ndarray:
    """e_c = the cue's COMPLEX evidence amplitude vector over candidates, from the SAME
    1-NN distances. |e_c(w)| = exp(-D/(2T)) (sqrt of the classical likelihood; Born-exact);
    arg(e_c(w)) = phi * (med - D)/spread = phi * the cue's SIGNED MARGIN in robust-spread
    units (positive where the cue prefers w). Returns a complex vector aligned to
    candidate_words. phi=0 => real amplitudes (no phase, the interference-OFF control)."""
    dists = _channel_distances(query_vec, train_vecs, train_words, candidate_words)
    d = np.array([dists[w] for w in candidate_words], dtype=np.float64)
    finite = d[np.isfinite(d)]
    if finite.size == 0:
        n = len(candidate_words)
        return np.ones(n, dtype=np.complex128) / np.sqrt(max(n, 1))
    T = float(np.median(finite)) or 1e-6
    med = float(np.median(finite))
    mad = float(np.median(np.abs(finite - med))) * 1.4826
    spread = mad if mad > 1e-9 else (T if T > 1e-9 else 1.0)
    d_filled = np.where(np.isfinite(d), d, med + 4.0 * spread)   # unseen word: far, low amp
    mag = np.exp(-d_filled / (2.0 * T))                          # sqrt classical likelihood
    margin = (med - d_filled) / spread                          # SIGNED margin (cue's stance)
    phase = phi * margin                                        # DERIVED phase, not fit
    return mag * np.exp(1j * phase)


def cue_operator(e_c: np.ndarray, beta: float = _Q_BETA) -> np.ndarray:
    """M_c = (1-beta) diag(e_c) + beta * e_hat e_hat^dagger — the cue's MEASUREMENT
    operator. Diagonal consistency term (reduces to the classical product) PLUS a rank-1
    complex outer-product back-action term (the NON-diagonal part: makes M_c non-commuting
    and seeds interference). beta=0 => purely diagonal (classical limit, commutes); beta>0
    => quantum (order effects + cross-terms). Pure owned linear algebra; no fit."""
    n = e_c.shape[0]
    nrm = np.linalg.norm(e_c)
    e_hat = e_c / nrm if nrm > 1e-12 else np.ones(n, dtype=np.complex128) / np.sqrt(max(n, 1))
    diag = np.diag(e_c)
    proj = np.outer(e_hat, np.conj(e_hat))           # |e_hat><e_hat| (Hermitian rank-1)
    return (1.0 - beta) * diag + beta * proj


def quantum_recognize(per_cue_amplitudes: list, candidate_words,
                      beta: float = _Q_BETA, psi0: np.ndarray = None) -> dict:
    """Apply the cue measurement operators SEQUENTIALLY to the superposition and read out
    the Born probabilities. psi_final = M_K ... M_1 psi0 (renormalized after each cue);
    P(w) = |psi_final(w)|^2. per_cue_amplitudes is an ORDERED list of complex e_c vectors
    (one per cue, aligned to candidate_words) — ORDER MATTERS when beta>0. Returns
    {word: born_probability}. The whole quantum combine: superpose -> measure in sequence
    -> collapse (Born)."""
    n = len(candidate_words)
    if psi0 is None:
        psi = np.ones(n, dtype=np.complex128) / np.sqrt(max(n, 1))   # uniform superposition
    else:
        psi = np.asarray(psi0, dtype=np.complex128).copy()
    for e_c in per_cue_amplitudes:
        M = cue_operator(np.asarray(e_c, dtype=np.complex128), beta=beta)
        psi = M @ psi
        nrm = np.linalg.norm(psi)
        if nrm > 1e-12:
            psi = psi / nrm
    born = np.abs(psi) ** 2
    Z = float(born.sum()) + 1e-12
    return {w: float(born[i] / Z) for i, w in enumerate(candidate_words)}


__all__ = ["channel_attr", "many_settings_score_term",
           "predict_many_settings_term", "channel_likelihood",
           "likelihood_from_distances", "channel_likelihood_exclusion",
           "exclusion_likelihood_from_distances", "channel_vector",
           "combine_vectors", "WORD_ATTR", "_Pred",
           "cue_amplitude", "cue_operator", "quantum_recognize"]
