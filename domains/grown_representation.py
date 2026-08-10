"""grown_representation — STEP 1 of the polyglot machinery: the
REPRESENTATION-BUILDING LOOP.

The decisive diagnosis (docs/research_polyglot_machinery.md): the agent's
representation is FROZEN and committed to ONE speaker cohort BY CONSTRUCTION.
domains/invariant_units.canonical_log_centroid warps every speaker to one
cohort tract — the HVPT single-talker failure baked in. The agent OWNS the
ingredients (a convolutional A1 STRF patch bank; feature_invention;
categorical_perception; the babble + forward-model loop; persona_speech_world
multi-voice generation) but they drive RECOGNITION, never BUILD the
representation.

THIS MODULE wires them into a representation-builder:

  Layer 0 (fixed, biological): the gammatone cochleagram (frames x bands).
  Layer 1 (convolutional, GROWN): A1 STRF patches over the cochleagram, but
     the patch INVENTORY grown from the input distribution by DISCRETE
     ACCRETION (feature_invention applied to the representation layer), NOT
     hand-placed, NOT gradient-fit.

THE SELECTOR IS EVERYTHING (the within-thesis analog of SSL masked
prediction, per the project rule — compression / cross-voice survival, NOT a
sweep, NOT an optimiser):

  · build signal = masked-frame prediction-error reduction. A patch carries
    real structure iff its response channel lowers the error of predicting a
    held-out frame's response from its temporal neighbours (the trivial
    1-step predictor — the simplest model-of-context that needs NO data to
    author, exactly composed_net_representation's forward-model analog).
  · survival across voices = the HVPT generalisation condition. A patch is
    KEPT iff its prediction-error reduction holds across DIFFERENT voices
    (every training persona / speaker), not just one. A patch that helps on
    one voice but not the others is REJECTED — that is the cohort-overfitting
    the whole redesign exists to escape.

NO-DONKEY LINE (research §5, §1d): we GROW the patch INVENTORY by discrete
accretion (in-thesis: each patch is a (centre_hz, sigma) authored from the
Gaussian formula, rendered exactly, kept by the survival selector) — we do
NOT continuously adjust STRF coefficients (that is the open weight-constructor,
out of thesis), and we do NOT hand-pick which patches survive (the selector
decides). If a reader reaches for an optimizer or hand-chooses patches, the
line is crossed.

The candidate PROPOSALS are the agent's feature_invention mechanism made
concrete on the representation layer: a patch is proposed where the current
representation under-resolves the input (high residual band-energy that no
existing patch's Gaussian covers tightly) — the "split a feature when the
distribution it pools is under-resolved" rule of speech_development, applied
to perception rather than to the recogniser.

Computed in the world adapter on the same frames x bands matrix the front-end
emits (the same role invariant_units.py plays before any Rust migration) so
the HVPT accept harness measures the MECHANISM honestly.
"""
from __future__ import annotations

import math

import numpy as np


# ---------------------------------------------------------------------------
# Layer 0 — the gammatone cochleagram axis (matches the front-end exactly:
# 32 log-spaced bands, 80..7500 Hz). On this log axis a Gaussian band->patch
# weight is the agent's A1 STRF kernel (auditory_cortex._DEFAULT_PATCHES).
# ---------------------------------------------------------------------------
_LOG_LO, _LOG_HI = math.log(80.0), math.log(7500.0)


def band_centres(n_bands: int = 32) -> np.ndarray:
    return np.array([math.exp(_LOG_LO + (_LOG_HI - _LOG_LO) * i / (n_bands - 1))
                     for i in range(n_bands)], dtype=np.float64)


# A1 STRF patch on the cochleagram = (centre_hz, sigma_hz). The response of a
# patch is the Gaussian-weighted sum of band envelopes (auditory_cortex.rs ::
# freq_weight + patch_evaluate, stationary case). Growing the inventory = adding
# (centre, sigma) entries; each is rendered EXACTLY by this formula (no fit).
def patch_weights(centre_hz: float, sigma_hz: float,
                  n_bands: int = 32) -> np.ndarray:
    bc = band_centres(n_bands)
    w = np.exp(-0.5 * ((bc - centre_hz) / max(sigma_hz, 1.0)) ** 2)
    s = w.sum()
    return (w / s).astype(np.float64) if s > 1e-9 else w


def seed_patches() -> list[tuple[float, float]]:
    """The agent's existing 25-patch A1 bank (auditory_cortex._DEFAULT_PATCHES)
    as the Layer-1 SEED inventory — the starting point the loop grows from."""
    from scripts.mine_whisper import _PATCHES
    return [(float(c), float(s)) for _, c, s in _PATCHES]


def bands_to_patches(M: np.ndarray, patches: list[tuple[float, float]]
                     ) -> np.ndarray:
    """Collapse frames x bands -> frames x patches through the patch inventory
    (the A1 convolutional layer). M may be CMVN-centred; the linear patch sum is
    still well-defined."""
    n_bands = M.shape[1]
    W = np.array([patch_weights(c, s, n_bands) for c, s in patches])  # P x B
    return (M @ W.T).astype(np.float64)                               # frames x P


# ---------------------------------------------------------------------------
# The BUILD SIGNAL — masked-frame prediction error (the SSL analog, no fit).
# ---------------------------------------------------------------------------

def masked_prediction_error(R: np.ndarray) -> np.ndarray:
    """Per-patch masked-frame prediction error on a frames x patches response
    matrix R. The trivial 1-step predictor r_hat_t = r_{t-1} (the simplest
    model-of-context that needs NO data to author — composed_net_representation's
    forward-model analog). Returns a per-patch mean |r_t - r_{t-1}| residual,
    z-scaled per patch so patches of different magnitude compare fairly.

    Interpretation: a patch whose channel is SMOOTH/PREDICTABLE in time (low
    residual once normalised by its own scale) is carrying coherent acoustic
    structure rather than noise. The build signal rewards patches whose response
    is predictable from its temporal neighbours."""
    if R.shape[0] < 2:
        return np.zeros(R.shape[1])
    diff = np.abs(R[1:] - R[:-1])          # (frames-1) x patches
    resid = diff.mean(axis=0)              # per patch
    scale = np.abs(R).mean(axis=0) + 1e-9  # per-patch magnitude
    return (resid / scale).astype(np.float64)


def representation_quality(R: np.ndarray) -> float:
    """Scalar build-signal quality of a representation on one utterance: the
    NEGATIVE mean normalised masked-prediction residual (higher = better, i.e.
    the representation's channels are more predictable / carry more coherent
    structure). This is the SSL masked-prediction objective turned into the
    project's selector value — no gradient, no fit."""
    return -float(masked_prediction_error(R).mean())


# ---------------------------------------------------------------------------
# THE TRANSITION CHANNEL — the agent's OWNED order-1-over-time operator
# (dynamics_features.compose_formant_transitions / order_n_concepts order-1-time),
# lifted down from RECOGNITION into the BUILD signal (iter-30, the dyslexia fix).
#
# The deficit research (docs/research_speech_deficits.md) names this exactly:
# phoneme identity lives in the FAST TEMPORAL TRANSITION, not the smooth spectrum.
# iter-29's smoothness build signal PENALISED the transition; this reads THROUGH it.
#
# The operator, mirrored from the graph Term-tree the agent composes:
#   F(t) = ArgMax over a region's (frequency-ordered) channels at time-window t
#          = the formant FREQUENCY (peak channel index) — the agent's ArgMax.
#   transition(region) = F(late) - F(early)   = order-1-over-TIME (the agent's
#          nth_order_terms(.., 1) over the two time windows).
# Here the "region's channels" are the patch responses ordered by patch centre Hz
# (so ArgMax-index IS a frequency), and the early/late split is the same half-split
# enrich_sign_windows uses. NO Python computes a fit; this is the agent's own
# transition operator evaluated on the patch-response matrix.
# ---------------------------------------------------------------------------

def transition_channel(R: np.ndarray, patches: list[tuple[float, float]]
                       ) -> np.ndarray:
    """The agent's ORDER-1-OVER-TIME transition descriptor for one utterance's
    patch-response matrix R (frames x patches) — the operator the agent owns
    (order_n_concepts.nth_order_terms(samples, 1) over the TIME dimension; the
    dynamics_features rise/transition family). This is the FAST CHANGE the
    dyslexia deficit names as carrying phoneme identity — read in place of the
    static spectrum the smoothness signal preferred.

    Mirrors the operator:
      · order patch columns by centre Hz (so the channels are frequency-ordered,
        the agent's ArgMax-of-region frame; accreted patches append out of order,
        so we sort here);
      · split frames into an EARLY and a LATE half (the enrich_sign_windows split
        compose_formant_transitions uses);
      · per ORDERED CHANNEL, the order-1-over-time difference = late mean - early
        mean (nth_order_terms over the two time windows). This is the per-channel
        transition profile.

    It additionally appends the agent's two-region FORMANT-TRANSITION read
    (compose_formant_transitions: F_late - F_early, F = ArgMax over a region =
    the formant FREQUENCY sweep), F1 (low half) and F2 (high half) — the
    place-of-articulation dynamic. Both terms are the same owned operator at two
    granularities; together they form the transition descriptor on which the
    cross-voice contrast margin is measured. Returns a (P+2)-vector."""
    n_frames, n_patch = R.shape
    if n_frames < 2 or n_patch < 1:
        return np.zeros(n_patch + 2, dtype=np.float64)
    order = np.argsort([c for c, _ in patches])      # columns by centre Hz
    Ro = R[:, order]
    h = max(1, n_frames // 2)
    early = Ro[:h].mean(axis=0)                       # per-(ordered)patch, early
    late = Ro[h:].mean(axis=0)                        # per-(ordered)patch, late
    per_channel = late - early                        # order-1 over TIME, per chan
    # the agent's two-region formant-frequency transition (ArgMax sweep).
    half = max(1, n_patch // 2)
    regions = ((0, half), (half, n_patch)) if n_patch >= 2 else ((0, n_patch),)
    formant = []
    for lo, hi in regions:
        f_e = float(np.argmax(early[lo:hi]))          # F(early) = ArgMax region
        f_l = float(np.argmax(late[lo:hi]))           # F(late)  = ArgMax region
        formant.append(f_l - f_e)                     # order-1 over TIME
    while len(formant) < 2:
        formant.append(0.0)
    return np.concatenate([per_channel, np.asarray(formant, dtype=np.float64)])


def _cos(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < 1e-9 or nb < 1e-9:
        # zero transition vectors: define agreement by exact equality (both flat
        # = same null transition) so an all-zero pair is "same", not undefined.
        return 1.0 if np.allclose(a, b) else 0.0
    return float(np.dot(a, b) / (na * nb))


def transition_contrast_margin(
        voice_word_T: dict, patches: list[tuple[float, float]]) -> float:
    """The CROSS-VOICE TRANSITION-CONTRAST MARGIN (iter-30 build signal), read
    THROUGH the agent's order-1-over-time transition channel:

        margin = mean sim(SAME word, DIFFERENT voices)
               - mean sim(DIFFERENT words)                       [any voices]

    The two terms are the two dyslexia sub-lesions made into one selector:
      · same-word-ACROSS-DIFFERENT-VOICES similarity = the categorical / cross-
        voice CONTRAST term (the phonological-core + phonagnosia⊥word-deafness
        axis: the *what* invariant to the *who*);
      · minus different-word similarity = the discrimination term.
    Measured on the transition descriptor, so it is the *fast change* that carries
    phoneme identity — exactly the cue the smoothness signal discarded.

    `voice_word_T` is {voice: [(word, T_vec), ...]} — the transition descriptors
    already computed per utterance under a given patch inventory. This is a
    DISCRIMINATION margin (sign-of-margin selector), NOT a gradient fit.

    CRUCIAL for the shuffle test: the same-word term is restricted to pairs from
    DIFFERENT voices, so when voice labels are shuffled the same-word-across-voices
    structure is destroyed and the margin must collapse."""
    same_cross_voice = []
    diff = []
    voices = list(voice_word_T.keys())
    for vi in range(len(voices)):
        for vj in range(len(voices)):
            if vj < vi:
                continue
            same_voice = (vi == vj)
            for k, (wa, Ta) in enumerate(voice_word_T[voices[vi]]):
                items_j = voice_word_T[voices[vj]]
                start = k + 1 if same_voice else 0
                for m in range(start, len(items_j)):
                    wb, Tb = items_j[m]
                    s = _cos(Ta, Tb)
                    if wa == wb:
                        if not same_voice:          # SAME word, DIFFERENT voices
                            same_cross_voice.append(s)
                    else:
                        diff.append(s)              # different words (any voices)
    same = float(np.mean(same_cross_voice)) if same_cross_voice else 0.0
    diffm = float(np.mean(diff)) if diff else 0.0
    return same - diffm


def _voice_word_transitions(voice_word_matrices: dict,
                            patches: list[tuple[float, float]]) -> dict:
    """{voice: [(word, M)]} -> {voice: [(word, T_vec)]} through the patch bank +
    the agent's transition channel."""
    out = {}
    for voice, items in voice_word_matrices.items():
        out[voice] = [(w, transition_channel(bands_to_patches(M, patches), patches))
                      for (w, M) in items]
    return out


# ---------------------------------------------------------------------------
# CANDIDATE PROPOSAL — feature_invention on the representation layer.
# ---------------------------------------------------------------------------

def propose_candidates(band_matrices: list[np.ndarray],
                       existing: list[tuple[float, float]],
                       n_candidates: int = 8,
                       sigma_frac: float = 0.5) -> list[tuple[float, float]]:
    """Propose candidate A1 patches where the current inventory UNDER-RESOLVES
    the input — the agent's feature_invention rule ('split / add a feature where
    the distribution it must pool is under-resolved') applied to perception.

    Mechanism (no fit, no sweep-to-score):
      1. mean band-energy profile over all heard frames (the input distribution
         on the log-frequency axis);
      2. coverage profile = how tightly the EXISTING patches' Gaussians already
         pool each band (sum of existing weights at each band);
      3. residual = energy * (1 - normalised coverage) — band regions that carry
         energy but are poorly covered by the current inventory;
      4. propose patches centred at the residual peaks (greedy, suppressing a
         neighbourhood after each pick so candidates spread across the
         under-resolved regions), sigma = sigma_frac of the local band spacing.

    The proposals are DISCRETE (centre, sigma) authored from the cochlear axis —
    NOT optimised. The selector (cross-voice survival) decides which survive."""
    n_bands = band_matrices[0].shape[1]
    bc = band_centres(n_bands)
    # 1. input energy profile (mean over all frames of all utterances).
    energy = np.zeros(n_bands)
    nfr = 0
    for M in band_matrices:
        energy += np.abs(M).sum(axis=0)
        nfr += M.shape[0]
    energy = energy / max(nfr, 1)
    if energy.max() > 1e-12:
        energy = energy / energy.max()
    # 2. coverage by existing patches.
    coverage = np.zeros(n_bands)
    for c, s in existing:
        coverage += patch_weights(c, s, n_bands)
    if coverage.max() > 1e-12:
        coverage = coverage / coverage.max()
    # 3. residual = energy in poorly-covered bands.
    residual = energy * (1.0 - coverage)
    # 4. greedy peak picking with neighbourhood suppression.
    cands: list[tuple[float, float]] = []
    r = residual.copy()
    # local band spacing in Hz (for sigma) — log axis, so spacing grows with f.
    spacing = np.gradient(bc)
    supp = max(1, n_bands // 12)   # suppression radius in band indices
    for _ in range(n_candidates):
        bi = int(np.argmax(r))
        if r[bi] <= 1e-9:
            break
        centre = float(bc[bi])
        sigma = float(max(spacing[bi] * (1.0 / max(sigma_frac, 1e-3)),
                          spacing[bi]))
        cands.append((centre, sigma))
        lo, hi = max(0, bi - supp), min(n_bands, bi + supp + 1)
        r[lo:hi] = 0.0
    return cands


# ---------------------------------------------------------------------------
# THE SELECTOR — cross-voice survival (the whole point; not a sweep).
# ---------------------------------------------------------------------------

def patch_survives(candidate: tuple[float, float],
                   current: list[tuple[float, float]],
                   voice_band_matrices: dict[str, list[np.ndarray]],
                   min_voices_frac: float = 1.0) -> tuple[bool, dict]:
    """Decide whether to KEEP `candidate`, by CROSS-VOICE SURVIVAL.

    For each voice (persona / speaker) independently, measure whether adding the
    candidate patch IMPROVES the build signal (mean representation_quality over
    that voice's utterances). The candidate SURVIVES iff it improves the build
    signal on at least `min_voices_frac` of the voices (default ALL of them) —
    the structural definition of speaker-invariant carried by the patch, and the
    HVPT generalisation condition. A patch that helps one voice but not the
    others is the cohort-overfitting failure; it is REJECTED.

    NO score is swept; NO optimiser runs. The selector reads the sign of the
    per-voice build-signal change and counts voices. Returns (survives, info)."""
    with_cand = current + [candidate]
    per_voice_delta: dict[str, float] = {}
    helped = 0
    for voice, mats in voice_band_matrices.items():
        if not mats:
            continue
        q_before = np.mean([representation_quality(bands_to_patches(M, current))
                            for M in mats])
        q_after = np.mean([representation_quality(bands_to_patches(M, with_cand))
                           for M in mats])
        d = float(q_after - q_before)
        per_voice_delta[voice] = d
        if d > 0.0:
            helped += 1
    n_voices = len(per_voice_delta)
    survives = (n_voices > 0
                and helped >= math.ceil(min_voices_frac * n_voices))
    return survives, {"helped_voices": helped, "n_voices": n_voices,
                      "per_voice_delta": per_voice_delta}


# ---------------------------------------------------------------------------
# THE iter-30 SELECTOR — CROSS-VOICE TRANSITION-CONTRAST SURVIVAL.
# Replaces the smoothness build signal (representation_quality) with the agent's
# owned order-1-over-time transition operator + a cross-voice same-vs-different
# margin. Same voice-counting shell as patch_survives; the build signal is the
# discriminating contrast the dyslexia deficit named — no fit, no sweep.
# ---------------------------------------------------------------------------

def _heldvoice_margin(held: str, voice_word_T: dict) -> float:
    """The cross-voice transition-contrast margin ANCHORED on one held voice:
        mean sim(held voice's word, the SAME word in any OTHER voice)
      - mean sim(held voice's word, DIFFERENT words in any other voice).
    A per-voice value (so the survival shell can count voices) that is still
    intrinsically CROSS-voice (held vs others) — so shuffling voice labels
    destroys the same-word-across-voice structure it depends on."""
    others = [v for v in voice_word_T if v != held]
    if not others:
        return 0.0
    same, diff = [], []
    for (wa, Ta) in voice_word_T[held]:
        for ov in others:
            for (wb, Tb) in voice_word_T[ov]:
                s = _cos(Ta, Tb)
                (same if wa == wb else diff).append(s)
    sm = float(np.mean(same)) if same else 0.0
    dm = float(np.mean(diff)) if diff else 0.0
    return sm - dm


def patch_survives_transition(
        candidate: tuple[float, float],
        current: list[tuple[float, float]],
        voice_word_matrices: dict,
        min_voices_frac: float = 1.0) -> tuple[bool, dict]:
    """iter-30 selector: KEEP `candidate` iff adding it RAISES the CROSS-VOICE
    TRANSITION-CONTRAST MARGIN — measured THROUGH the agent's order-1-over-time
    transition channel — on at least `min_voices_frac` of the voices.

    For each voice v held as the anchor, compute the margin
    [sim(same word, across the OTHER voices) - sim(different words, across the
    other voices)] on the transition descriptors, before and after adding the
    candidate patch. The candidate survives iff that margin rises on enough
    anchored voices. This is the within-thesis discrimination selector the
    dyslexia deficit prescribes (transition resolver + categorical contrast),
    NOT a gradient fit: it reads the SIGN of a margin change and counts voices.

    `voice_word_matrices` = {voice: [(word, M_band), ...]}. Returns (survives,
    info)."""
    T_before = _voice_word_transitions(voice_word_matrices, current)
    T_after = _voice_word_transitions(voice_word_matrices, current + [candidate])
    per_voice_delta: dict[str, float] = {}
    helped = 0
    for voice in voice_word_matrices:
        m_before = _heldvoice_margin(voice, T_before)
        m_after = _heldvoice_margin(voice, T_after)
        d = float(m_after - m_before)
        per_voice_delta[voice] = d
        if d > 0.0:
            helped += 1
    n_voices = len(per_voice_delta)
    survives = (n_voices > 0
                and helped >= math.ceil(min_voices_frac * n_voices))
    return survives, {"helped_voices": helped, "n_voices": n_voices,
                      "per_voice_delta": per_voice_delta}


def grow_representation(voice_band_matrices: dict[str, list[np.ndarray]],
                        seed: list[tuple[float, float]] | None = None,
                        rounds: int = 4,
                        candidates_per_round: int = 8,
                        min_voices_frac: float = 1.0,
                        selector: str = "smoothness",
                        voice_word_matrices: dict | None = None,
                        verbose: bool = False) -> dict:
    """The REPRESENTATION-BUILDING LOOP. Grow the A1 patch inventory by DISCRETE
    ACCRETION across rounds, driven by a cross-voice survival selector.

    `voice_band_matrices`: {voice_name: [frames x bands matrices]} — the
    across-speaker variability (HVPT input). The held-out voice is NEVER in this
    dict (it is only used at test time). Used for candidate PROPOSAL always, and
    for the `smoothness` selector.

    `selector`:
      · "smoothness" (iter-29, default for back-compat) — keep a patch iff it
        raises the masked-prediction (temporal-smoothness) build signal on the
        voices. VOICE-AGNOSTIC + CONTRAST-AGNOSTIC (survives its own shuffle).
      · "transition" (iter-30) — keep a patch iff it raises the CROSS-VOICE
        TRANSITION-CONTRAST MARGIN (same-word-across-voices minus different-word,
        read through the agent's owned order-1-over-time transition operator).
        Requires `voice_word_matrices` = {voice: [(word, M_band), ...]}.

    Each round:
      1. propose candidate patches where the CURRENT inventory under-resolves the
         pooled input (feature_invention);
      2. for each candidate, KEEP it iff it survives across the voices (selector);
      3. accrete survivors into the inventory; re-render next round.

    Returns {patches, grown (the patches added), history}. The selector — not a
    sweep, not a human — decides the inventory. No gradient, no fit."""
    if selector == "transition" and voice_word_matrices is None:
        raise ValueError("selector='transition' requires voice_word_matrices "
                         "{voice: [(word, M_band)]}")
    current = list(seed if seed is not None else seed_patches())
    all_mats = [M for mats in voice_band_matrices.values() for M in mats]
    grown: list[tuple[float, float]] = []
    history: list[dict] = []
    for rnd in range(rounds):
        cands = propose_candidates(all_mats, current,
                                   n_candidates=candidates_per_round)
        added_this_round = 0
        for cand in cands:
            if selector == "transition":
                survives, info = patch_survives_transition(
                    cand, current, voice_word_matrices,
                    min_voices_frac=min_voices_frac)
            else:
                survives, info = patch_survives(
                    cand, current, voice_band_matrices,
                    min_voices_frac=min_voices_frac)
            if survives:
                current.append(cand)
                grown.append(cand)
                added_this_round += 1
                if verbose:
                    print(f"  round {rnd}: KEEP patch centre={cand[0]:.0f}Hz "
                          f"sigma={cand[1]:.0f}  "
                          f"(helped {info['helped_voices']}/{info['n_voices']} "
                          f"voices)")
            elif verbose:
                print(f"  round {rnd}: reject centre={cand[0]:.0f}Hz "
                      f"(helped {info['helped_voices']}/{info['n_voices']})")
        history.append({"round": rnd, "candidates": len(cands),
                        "kept": added_this_round,
                        "inventory_size": len(current)})
        if added_this_round == 0:
            break    # accretion saturated — no candidate survives cross-voice
    return {"patches": current, "grown": grown, "history": history,
            "seed_size": len(seed if seed is not None else seed_patches())}


__all__ = [
    "band_centres", "patch_weights", "seed_patches", "bands_to_patches",
    "masked_prediction_error", "representation_quality",
    "transition_channel", "transition_contrast_margin",
    "patch_survives_transition",
    "propose_candidates", "patch_survives", "grow_representation",
]
