"""grown_representation_hvpt_accept — STEP 1 acceptance: the HVPT validity test.

The whole point (docs/research_polyglot_machinery.md §4-§5): does a representation
GROWN under across-speaker variability GENERALISE to an UNSEEN voice, where the
FROZEN cohort-warped front-end cannot? This is the selector's validity check, per
HVPT (across-speaker variability -> generalisation; single-cohort -> failure).

THE TEST (held-out voice — never seen during growth):
  · FROZEN cohort front-end = the agent's current path: gammatone -> VTLN warp
    to the cohort canonical_log_centroid (the baked-in single-cohort commitment)
    -> CMVN -> the FIXED 25-patch A1 bank.  (domains.invariant_units +
    the seed patch bank.)
  · GROWN-general representation = gammatone (NO cohort warp) -> the A1 patch bank
    GROWN by discrete accretion, selected by cross-voice survival
    (domains.grown_representation).

Measured on the held-out voice's utterances:
  · same-word consistency  (within-voice: mean cosine sim of same-word pairs vs
    different-word pairs -> a separation margin);
  · cross consistency / recognition: 1-NN word accuracy, held-out voice queried
    against the TRAINING voices (the polyglot generalisation: recognise the new
    talker's words using only the other talkers).

CONTROLS:
  · SHUFFLE — re-run growth with utterance->voice labels shuffled, so the
    "cross-voice survival" selector sees no real voice structure. If the grown
    representation's advantage survives the shuffle, the advantage is NOT coming
    from real cross-voice survival (the selector would be doing nothing) and the
    result is an artifact. The real run must beat the shuffle.
  · CROSS-CHECK — both a real-FSDD-speaker HVPT (5 grow / 1 held out; real
    across-speaker variability) and an agent-generated PERSONA HVPT (the agent's
    own persona_speech_world voices: 4 grow + a held-out 5th persona, the spec's
    literal multi-voice generation).

NO gradient, NO weight-fit, NO hand-picked patches anywhere — the inventory is
decided by the cross-voice survival selector (grown_representation.grow_*). The
frozen path is the regression baseline.

Run: python -m scripts.grown_representation_hvpt_accept [n_per_speaker_per_digit]
"""
import sys
import math
import random

import numpy as np

sys.path.insert(0, '/home/matt/ozma/internal/research/experiments/gamma-substrate')

from scripts.mine_whisper import gather, load_wav, silhouette_by_word
from scripts.invariant_units_accept import band_trajectory_matrix
from domains.invariant_units import invariant_transform, canonical_log_centroid
from domains.grown_representation import (
    seed_patches, bands_to_patches, grow_representation,
    transition_channel, transition_contrast_margin,
)


# ---------------------------------------------------------------------------
# Representations as per-utterance vectors (L2-pooled patch trajectory).
# ---------------------------------------------------------------------------

def l2_pool(M):
    v = M.mean(axis=0).astype(np.float64)
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def l2_flat(M):
    v = M.flatten().astype(np.float64)
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def l2(v):
    v = np.asarray(v, dtype=np.float64)
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def trans_readout(R, patches):
    """iter-31 recognition readout: the per-utterance vector IS the agent's
    order-1-over-time TRANSITION CHANNEL (transition_channel on the patch-response
    matrix) — the SAME owned operator the iter-30 selector scores on. The recognizer
    now CONSUMES the discrimination the selector built, instead of 1-NN'ing the raw
    grown patch responses (iter-30's warp-driven readout). No fit: the readout is the
    transition operator evaluated natively, L2-normalised for cosine 1-NN."""
    return l2(transition_channel(R, patches))


def frozen_repr(M_band, canonical, patches):
    """FROZEN cohort front-end: cohort-warp (VTLN to canonical) + CMVN, then the
    FIXED seed patch bank. This is the baked-in single-cohort commitment."""
    t = invariant_transform(M_band, canonical, do_vtln=True, do_cmvn=True,
                            do_context=False)
    return bands_to_patches(t, patches)


def grown_repr(M_band, patches):
    """GROWN-general representation: NO cohort warp; the grown patch bank applied
    straight to the cochleagram. Per-utterance CMVN is allowed (a per-utterance
    op, not a cohort commitment) so the comparison is fair on level/channel."""
    # per-utterance mean removal only (no cohort canonical, no VTLN warp)
    mu = M_band.mean(axis=0, keepdims=True)
    return bands_to_patches(M_band - mu, patches)


# ---------------------------------------------------------------------------
# Held-out-voice metrics.
# ---------------------------------------------------------------------------

def _trans_margin_within(matrices_words, repr_fn, patches):
    """Within-voice same-word vs different-word margin read THROUGH the agent's
    order-1-over-time transition channel (transition_channel on the patch-response
    matrix). `repr_fn(M)` -> frames x patches responses; `patches` orders the
    transition channel's columns by centre Hz. This is the iter-30 selector's
    objective evaluated as a METRIC on the held-out voice."""
    Ts, words = [], []
    for M, w in matrices_words:
        R = repr_fn(M)
        Ts.append(transition_channel(R, patches))
        words.append(w)
    same, diff = [], []
    n = len(words)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = Ts[i], Ts[j]
            na, nb = np.linalg.norm(a), np.linalg.norm(b)
            if na < 1e-9 or nb < 1e-9:
                s = 1.0 if np.allclose(a, b) else 0.0
            else:
                s = float(np.dot(a, b) / (na * nb))
            (same if words[i] == words[j] else diff).append(s)
    sm = float(np.mean(same)) if same else 0.0
    dm = float(np.mean(diff)) if diff else 0.0
    return sm - dm


def within_voice_margin(vectors, words):
    """Same-word consistency on ONE voice: mean cosine sim of same-word pairs
    minus mean cosine sim of different-word pairs. Higher = the representation
    groups the WORD not the noise. Pure within-voice (no cross-speaker leakage)."""
    X = np.asarray(vectors)
    Xn = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)
    S = Xn @ Xn.T
    words = np.asarray(words)
    same_sims, diff_sims = [], []
    n = len(words)
    for i in range(n):
        for j in range(i + 1, n):
            if words[i] == words[j]:
                same_sims.append(S[i, j])
            else:
                diff_sims.append(S[i, j])
    same = float(np.mean(same_sims)) if same_sims else 0.0
    diff = float(np.mean(diff_sims)) if diff_sims else 0.0
    return same - diff, same, diff


def heldout_1nn(train_vecs, train_words, test_vecs, test_words):
    """Recognition: held-out voice queried against TRAINING voices (1-NN cosine).
    The polyglot generalisation — recognise the unseen talker's words using only
    the other talkers."""
    Xtr = np.asarray(train_vecs)
    Xtr = Xtr / (np.linalg.norm(Xtr, axis=1, keepdims=True) + 1e-9)
    Xte = np.asarray(test_vecs)
    Xte = Xte / (np.linalg.norm(Xte, axis=1, keepdims=True) + 1e-9)
    sim = Xte @ Xtr.T
    nn = sim.argmax(axis=1)
    pred = np.asarray(train_words)[nn]
    return float((pred == np.asarray(test_words)).mean())


# ---------------------------------------------------------------------------
# iter-32 — the COMBINATORIAL recognition over the two channels (the agent's
# recognition_graph Argmax of the Bayes PRODUCT of per-channel likelihoods).
# ---------------------------------------------------------------------------

from substrate_rs import Substrate                      # noqa: E402
from domains import combinatorial_recognizer as CR      # noqa: E402

_COMBO_SUB = None
_COMBO_WC: dict = {}
_COMBO_TERM = None


def _combo_substrate(candidate_words):
    """A tiny substrate holding one Concept per candidate word (tagged is_word) on
    which the agent's combinatorial Argmax-of-product Term ranges. Built once, reused;
    the per-query likelihoods are written onto these nodes each call."""
    global _COMBO_SUB, _COMBO_TERM
    if _COMBO_SUB is None:
        _COMBO_SUB = Substrate()
        _COMBO_TERM = CR._Pred(CR.predict_combinatorial_term())
    for w in candidate_words:
        if w not in _COMBO_WC:
            c = _COMBO_SUB.add_node("Concept", {"name": w})
            _COMBO_SUB.set_attr(c, CR.WORD_ATTR, 1.0)
            _COMBO_WC[w] = c
    return _COMBO_SUB


def heldout_combinatorial(train_flat, train_trans, train_words,
                          test_flat, test_trans, test_words):
    """iter-32 COMBINATORIAL recognition. Each held-out query is recognised by the
    agent's recognition_graph Argmax of the Bayes PRODUCT of the two per-channel
    likelihoods:
        P_flat(w|s)  = softmax over candidates of the FLAT channel's 1-NN exemplar
                       evidence (spectral detail — 'what is this');
        P_trans(w|s) = softmax over candidates of the TRANSITION channel's 1-NN
                       exemplar evidence (cross-voice — 'which word');
        predict(s)   = Argmax_w P_flat(w|s)·P_trans(w|s)   (graph Term, native eval).
    Each channel contributes its OWN evidence on a common [0,1] footing; a channel
    that cannot separate the candidates multiplies in near-flat and cannot drag the
    one that does. NO global hand-weight, NO fit — the product is the agent's derived
    Bayes shape; the per-channel temperature is the channel's own median distance."""
    Xf = np.asarray(train_flat)
    Xt = np.asarray(train_trans)
    candidates = sorted(set(train_words))
    sub = _combo_substrate(candidates)
    correct = 0
    for qf, qt, true_w in zip(test_flat, test_trans, test_words):
        p_flat = CR.channel_likelihood(np.asarray(qf), Xf, train_words, candidates)
        p_trans = CR.channel_likelihood(np.asarray(qt), Xt, train_words, candidates)
        for w in candidates:
            sub.set_attr(_COMBO_WC[w], CR.P_FLAT_ATTR, p_flat[w])
            sub.set_attr(_COMBO_WC[w], CR.P_TRANS_ATTR, p_trans[w])
        pred = sub.evaluate(_COMBO_TERM, {})
        pw = sub.node(pred)["attrs"].get("name") if pred is not None else None
        correct += int(pw == true_w)
    return correct / max(len(test_words), 1)


# ---------------------------------------------------------------------------
# One HVPT experiment given {voice: [(M_band, word), ...]} and a held-out voice.
# ---------------------------------------------------------------------------

def run_hvpt(voice_data, held_voice, rounds=4, shuffle=False, verbose=False,
             selector="transition"):
    """Run one HVPT fold. `selector`:
      · "transition" (iter-30) — grow under the CROSS-VOICE TRANSITION-CONTRAST
        margin (the agent's order-1-over-time operator); words carried as labels.
      · "smoothness" (iter-29) — grow under the masked-prediction smoothness
        signal (voice/contrast-agnostic), for the head-to-head comparison.

    The SHUFFLE control shuffles utterance->voice labels (keeping words attached),
    so the cross-voice same-word structure the transition selector depends on is
    destroyed. The decisive read: REAL must beat SHUFFLE under "transition"."""
    train_voices = [v for v in voice_data if v != held_voice]
    # Growth input: training voices' (word, band-matrix) grouped by voice.
    voice_word_matrices = {v: [(w, M) for (M, w) in voice_data[v]]
                           for v in train_voices}
    if shuffle:
        # SHUFFLE CONTROL: re-assign every training (word,utterance) to a random
        # pseudo-voice, so the cross-voice survival selector sees no real voice
        # structure. WORDS STAY ATTACHED — only the voice partition is randomised,
        # which is exactly the structure the cross-voice same-word margin needs.
        flat = [(w, M) for v in train_voices for (M, w) in voice_data[v]]
        rng = random.Random(1234)
        rng.shuffle(flat)
        k = len(train_voices)
        voice_word_matrices = {f"shuf{i}": [] for i in range(k)}
        for idx, (w, M) in enumerate(flat):
            voice_word_matrices[f"shuf{idx % k}"].append((w, M))
    # band-matrix-only view (used by candidate proposal + smoothness selector).
    voice_band_matrices = {v: [M for (_, M) in items]
                           for v, items in voice_word_matrices.items()}

    # GROW (selector decides the inventory; no sweep, no fit).
    seed = seed_patches()
    if selector == "transition":
        grown = grow_representation(
            voice_band_matrices, seed=seed, rounds=rounds, verbose=verbose,
            selector="transition", voice_word_matrices=voice_word_matrices)
    else:
        grown = grow_representation(voice_band_matrices, seed=seed, rounds=rounds,
                                   verbose=verbose, selector="smoothness")
    grown_patches = grown["patches"]

    # CONTROL — UNSELECTED ACCRETION: add ALL proposed candidates without the
    # cross-voice survival test (min_voices_frac=0 keeps every candidate). This
    # isolates the SELECTOR's contribution: if grown beats this, the cross-voice
    # survival selector — not merely adding patches — is doing the work.
    from domains.grown_representation import propose_candidates
    all_mats = [M for mats in voice_band_matrices.values() for M in mats]
    allcand = list(seed)
    for _r in range(rounds):
        cs = propose_candidates(all_mats, allcand, n_candidates=8)
        if not cs:
            break
        allcand.extend(cs)
    grown_all_patches = allcand

    # Cohort canonical for the FROZEN path — computed from TRAINING voices only
    # (the cohort the frozen front-end is committed to; held-out is unseen).
    train_band = [M for v in train_voices for (M, _) in voice_data[v]]
    canonical = canonical_log_centroid(train_band)

    # Build per-utterance vectors for train + held-out, all representations.
    # Each repr produces THREE readout vectors per utterance:
    #   · flat  = L2-normalised flattened raw patch-response matrix (iter-30 readout)
    #   · pool  = L2-normalised time-pooled raw patch responses    (iter-30 readout)
    #   · trans = the agent's order-1-over-time TRANSITION CHANNEL  (iter-31 readout,
    #             the SAME operator the selector scores on — the recognizer now reads
    #             THROUGH the channel the selector built).
    # `repr_fn(M)` -> R (frames x patches); `patches` orders the transition columns.
    def vecs(matrices_words, repr_fn, patches):
        flat_vecs, pooled, trans, words = [], [], [], []
        for M, w in matrices_words:
            R = repr_fn(M)
            flat_vecs.append(l2_flat(R))
            pooled.append(l2_pool(R))
            trans.append(trans_readout(R, patches))
            words.append(w)
        return flat_vecs, pooled, trans, words

    held_mw = voice_data[held_voice]
    train_mw = [(M, w) for v in train_voices for (M, w) in voice_data[v]]

    frozen_held_flat, frozen_held_pool, frozen_held_trans, held_words = vecs(
        held_mw, lambda M: frozen_repr(M, canonical, seed), seed)
    grown_held_flat, grown_held_pool, grown_held_trans, _ = vecs(
        held_mw, lambda M: grown_repr(M, grown_patches), grown_patches)
    frozen_tr_flat, frozen_tr_pool, frozen_tr_trans, train_words = vecs(
        train_mw, lambda M: frozen_repr(M, canonical, seed), seed)
    grown_tr_flat, grown_tr_pool, grown_tr_trans, _ = vecs(
        train_mw, lambda M: grown_repr(M, grown_patches), grown_patches)

    # ABLATION — NO-WARP SEED: per-utterance norm + the FIXED seed bank, no cohort
    # warp. Separates "dropping the cohort commitment" from "the grown patches".
    nowarp_held_flat, nowarp_held_pool, nowarp_held_trans, _ = vecs(
        held_mw, lambda M: grown_repr(M, seed), seed)
    nowarp_tr_flat, nowarp_tr_pool, nowarp_tr_trans, _ = vecs(
        train_mw, lambda M: grown_repr(M, seed), seed)
    # CONTROL — UNSELECTED ACCRETION (grown-all): no warp + ALL candidates.
    gall_held_flat, gall_held_pool, gall_held_trans, _ = vecs(
        held_mw, lambda M: grown_repr(M, grown_all_patches), grown_all_patches)
    gall_tr_flat, gall_tr_pool, gall_tr_trans, _ = vecs(
        train_mw, lambda M: grown_repr(M, grown_all_patches), grown_all_patches)

    out = {"held_voice": held_voice, "shuffle": shuffle,
           "grown_added": len(grown["grown"]),
           "grown_inventory": len(grown_patches),
           "grown_all_inventory": len(grown_all_patches),
           "seed_inventory": len(seed),
           "history": grown["history"]}

    # Same-word consistency ON THE HELD-OUT VOICE (within-voice margin).
    out["frozen_margin"], out["frozen_same"], out["frozen_diff"] = \
        within_voice_margin(frozen_held_flat, held_words)
    out["grown_margin"], out["grown_same"], out["grown_diff"] = \
        within_voice_margin(grown_held_flat, held_words)
    out["nowarp_margin"], _, _ = within_voice_margin(nowarp_held_flat, held_words)
    out["grown_all_margin"], _, _ = within_voice_margin(gall_held_flat, held_words)

    # TRANSITION-CHANNEL same-word margin ON THE HELD-OUT VOICE: the metric the
    # iter-30 selector optimises, evaluated through the agent's order-1-over-time
    # transition operator on the UNSEEN voice (within-voice same-word margin).
    out["frozen_trans_margin"] = _trans_margin_within(
        held_mw, lambda M: frozen_repr(M, canonical, seed), seed)
    out["grown_trans_margin"] = _trans_margin_within(
        held_mw, lambda M: grown_repr(M, grown_patches), grown_patches)
    out["nowarp_trans_margin"] = _trans_margin_within(
        held_mw, lambda M: grown_repr(M, seed), seed)

    # Recognition on held-out voice vs training voices (1-NN), pooled + flat.
    out["frozen_1nn_pool"] = heldout_1nn(frozen_tr_pool, train_words,
                                          frozen_held_pool, held_words)
    out["grown_1nn_pool"] = heldout_1nn(grown_tr_pool, train_words,
                                         grown_held_pool, held_words)
    out["frozen_1nn_flat"] = heldout_1nn(frozen_tr_flat, train_words,
                                          frozen_held_flat, held_words)
    out["grown_1nn_flat"] = heldout_1nn(grown_tr_flat, train_words,
                                         grown_held_flat, held_words)
    out["nowarp_1nn_pool"] = heldout_1nn(nowarp_tr_pool, train_words,
                                          nowarp_held_pool, held_words)
    out["nowarp_1nn_flat"] = heldout_1nn(nowarp_tr_flat, train_words,
                                          nowarp_held_flat, held_words)
    out["grown_all_1nn_pool"] = heldout_1nn(gall_tr_pool, train_words,
                                             gall_held_pool, held_words)
    out["grown_all_1nn_flat"] = heldout_1nn(gall_tr_flat, train_words,
                                             gall_held_flat, held_words)

    # iter-31: RECOGNITION-THROUGH-TRANSITION. 1-NN read on the TRANSITION-CHANNEL
    # readout (the same owned operator the selector scores on) — the recognizer now
    # consumes the discrimination the selector built, not the raw grown patches.
    out["frozen_1nn_trans"] = heldout_1nn(frozen_tr_trans, train_words,
                                           frozen_held_trans, held_words)
    out["grown_1nn_trans"] = heldout_1nn(grown_tr_trans, train_words,
                                          grown_held_trans, held_words)
    out["nowarp_1nn_trans"] = heldout_1nn(nowarp_tr_trans, train_words,
                                           nowarp_held_trans, held_words)
    out["grown_all_1nn_trans"] = heldout_1nn(gall_tr_trans, train_words,
                                              gall_held_trans, held_words)

    # iter-32: the COMBINATORIAL recognition — the agent's recognition_graph Argmax of
    # the Bayes PRODUCT of the FLAT (spectral-detail) and TRANSITION (cross-voice)
    # per-channel likelihoods, each keeping its role. Reported for every representation
    # so it can be read vs flat-only (iter-31) and trans-only (iter-31) and frozen.
    out["grown_1nn_combo"] = heldout_combinatorial(
        grown_tr_flat, grown_tr_trans, train_words,
        grown_held_flat, grown_held_trans, held_words)
    out["frozen_1nn_combo"] = heldout_combinatorial(
        frozen_tr_flat, frozen_tr_trans, train_words,
        frozen_held_flat, frozen_held_trans, held_words)
    out["nowarp_1nn_combo"] = heldout_combinatorial(
        nowarp_tr_flat, nowarp_tr_trans, train_words,
        nowarp_held_flat, nowarp_held_trans, held_words)
    out["grown_all_1nn_combo"] = heldout_combinatorial(
        gall_tr_flat, gall_tr_trans, train_words,
        gall_held_flat, gall_held_trans, held_words)

    out["n_held"] = len(held_words)
    out["n_train"] = len(train_words)
    return out


def _report(out, tag):
    print(f"\n--- {tag}: held-out voice = {out['held_voice']}"
          f"{' [SHUFFLE control]' if out['shuffle'] else ''} ---")
    print(f"  patch inventory: seed {out['seed_inventory']} -> grown "
          f"{out['grown_inventory']} (+{out['grown_added']} survived "
          f"cross-voice)")
    print(f"  held-out utterances: {out['n_held']}  train utterances: "
          f"{out['n_train']}")
    print(f"  same-word margin (held-out)  FROZEN {out['frozen_margin']:+.4f}"
          f"   GROWN {out['grown_margin']:+.4f}"
          f"   (Δ {out['grown_margin'] - out['frozen_margin']:+.4f})")
    print(f"  TRANSITION-chan margin (h.o.) FROZEN {out['frozen_trans_margin']:+.4f}"
          f"   GROWN {out['grown_trans_margin']:+.4f}"
          f"   (Δ {out['grown_trans_margin'] - out['frozen_trans_margin']:+.4f})")
    print(f"  recognition 1-NN pooled      FROZEN {out['frozen_1nn_pool']:.3f}"
          f"   GROWN {out['grown_1nn_pool']:.3f}"
          f"   (Δ {out['grown_1nn_pool'] - out['frozen_1nn_pool']:+.3f})")
    print(f"  recognition 1-NN flat        FROZEN {out['frozen_1nn_flat']:.3f}"
          f"   GROWN {out['grown_1nn_flat']:.3f}"
          f"   (Δ {out['grown_1nn_flat'] - out['frozen_1nn_flat']:+.3f})")
    print(f"  recognition 1-NN TRANS (i31) FROZEN {out['frozen_1nn_trans']:.3f}"
          f"   GROWN {out['grown_1nn_trans']:.3f}"
          f"   (Δ {out['grown_1nn_trans'] - out['frozen_1nn_trans']:+.3f})"
          f"   <- readout THROUGH the transition channel")
    print(f"  recognition 1-NN COMBO (i32) FROZEN {out['frozen_1nn_combo']:.3f}"
          f"   GROWN {out['grown_1nn_combo']:.3f}"
          f"   (Δ {out['grown_1nn_combo'] - out['frozen_1nn_combo']:+.3f})"
          f"   <- COMBINATORIAL: flat AND trans (Bayes product)")
    print(f"    ablation no-warp+seed bank   1NN-pool {out['nowarp_1nn_pool']:.3f}"
          f"  1NN-flat {out['nowarp_1nn_flat']:.3f}"
          f"  1NN-trans {out['nowarp_1nn_trans']:.3f}"
          f"  margin {out['nowarp_margin']:+.4f}")
    print(f"    control  no-warp+ALL cands   1NN-pool "
          f"{out['grown_all_1nn_pool']:.3f}  1NN-flat "
          f"{out['grown_all_1nn_flat']:.3f}  1NN-trans "
          f"{out['grown_all_1nn_trans']:.3f}  margin {out['grown_all_margin']:+.4f}"
          f"  (inv {out['grown_all_inventory']})")


# ---------------------------------------------------------------------------
# REAL-SPEAKER HVPT (primary): 6 FSDD speakers, real across-speaker variability.
# ---------------------------------------------------------------------------

def real_speaker_hvpt(n_per, rounds=4):
    items = gather(n_per_class_per_speaker=n_per)
    audio = [(*load_wav(p), str(d), s) for p, d, s in items]
    print(f"FSDD: {len(audio)} recordings, "
          f"{len(set(a[3] for a in audio))} speakers, "
          f"{len(set(a[2] for a in audio))} digits")
    # band matrices per speaker.
    voice_data: dict = {}
    for x, fs, word, spk in audio:
        M = band_trajectory_matrix(x, fs)
        voice_data.setdefault(spk, []).append((M, word))
    speakers = sorted(voice_data)
    print(f"speakers (voices): {speakers}")

    # Hold out EACH speaker in turn (full LOSO over the HVPT test). For each fold:
    #   · iter-30 TRANSITION selector (real + its SHUFFLE — the decisive control);
    #   · iter-29 SMOOTHNESS selector (real — the head-to-head comparison).
    results, shuf_results, smooth_results = [], [], []
    for held in speakers:
        out = run_hvpt(voice_data, held, rounds=rounds, selector="transition")
        _report(out, "REAL-SPEAKER HVPT [TRANSITION selector]")
        results.append(out)
        sh = run_hvpt(voice_data, held, rounds=rounds, shuffle=True,
                      selector="transition")
        _report(sh, "REAL-SPEAKER HVPT [TRANSITION selector]")
        shuf_results.append(sh)
        sm = run_hvpt(voice_data, held, rounds=rounds, selector="smoothness")
        _report(sm, "REAL-SPEAKER HVPT [SMOOTHNESS selector (iter-29)]")
        smooth_results.append(sm)
    return results, shuf_results, smooth_results


# ---------------------------------------------------------------------------
# PERSONA HVPT (cross-check): the agent's own persona_speech_world voices.
# The agent generates across-speaker variability by re-voicing each real digit
# through each persona (pitch f0 + vocal-tract scale vtl), exactly speak_as's
# transform. 4 personas grow + a held-out 5th persona (never seen).
# ---------------------------------------------------------------------------

def _repitch_retract(x, fs, vtl):
    """The persona_speech_world.speak_as vocal-tract transform: a longer tract
    (vtl>1) lowers formants; resampling the waveform shifts the whole spectrum —
    the cheap speaker-difference the agent must hear past. Pure I/O transform."""
    if vtl == 1.0 or x.size == 0:
        return x
    n = max(1, int(round(x.size / vtl)))
    idx = np.clip((np.arange(n) * vtl).astype(int), 0, x.size - 1)
    return np.ascontiguousarray(x[idx])


def persona_hvpt(n_per, rounds=4):
    from domains.persona_speech_world import DEFAULT_PERSONAS
    # A held-out 5th persona never seen during growth.
    held_persona = ("quinn", 150.0, 4.5, 1.25)
    personas = list(DEFAULT_PERSONAS) + [held_persona]
    # Use ONE source speaker's digits as the base content, re-voiced through each
    # persona's vocal tract -> the SAME words across DIFFERENT voices (HVPT input
    # the agent generates itself). Source speaker fixed so the only variation
    # across voices is the persona transform.
    items = gather(n_per_class_per_speaker=n_per)
    src_spk = "george"
    base = [(load_wav(p)[0], load_wav(p)[1], str(d))
            for p, d, s in items if s == src_spk]
    print(f"\nPERSONA source: {src_spk}, {len(base)} base digit recordings")
    print(f"personas (voices): {[p[0] for p in personas]}  "
          f"(held-out: {held_persona[0]})")
    voice_data: dict = {}
    for name, f0, q, vtl in personas:
        for x, fs, word in base:
            xv = _repitch_retract(x, fs, vtl)
            M = band_trajectory_matrix(xv, fs)
            voice_data.setdefault(name, []).append((M, word))
    out = run_hvpt(voice_data, held_persona[0], rounds=rounds)
    _report(out, "PERSONA HVPT (agent-generated voices)")
    sh = run_hvpt(voice_data, held_persona[0], rounds=rounds, shuffle=True)
    _report(sh, "PERSONA HVPT (agent-generated voices)")
    return out, sh


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    print("=" * 72)
    print("STEP 1 HVPT ACCEPT — grown-under-variability vs frozen-cohort "
          "front-end")
    print("=" * 72)

    real, real_shuf, smooth = real_speaker_hvpt(n_per)
    persona, persona_shuf = persona_hvpt(n_per)

    # ---- aggregate verdict ----
    def mean(rs, k):
        return float(np.mean([r[k] for r in rs]))

    print("\n" + "=" * 72)
    print("VERDICT (mean over held-out voices)")
    print("=" * 72)

    print("\nREAL-SPEAKER HVPT (LOSO over 6 FSDD speakers) — TRANSITION selector:")
    fm, gm = mean(real, "frozen_margin"), mean(real, "grown_margin")
    fp, gp = mean(real, "frozen_1nn_pool"), mean(real, "grown_1nn_pool")
    ff, gf = mean(real, "frozen_1nn_flat"), mean(real, "grown_1nn_flat")
    ftm, gtm = mean(real, "frozen_trans_margin"), mean(real, "grown_trans_margin")
    print(f"  same-word margin (flat) FROZEN {fm:+.4f}  GROWN {gm:+.4f}  "
          f"(Δ {gm - fm:+.4f})")
    print(f"  TRANSITION-chan margin  FROZEN {ftm:+.4f}  GROWN {gtm:+.4f}  "
          f"(Δ {gtm - ftm:+.4f})")
    print(f"  1-NN pooled        FROZEN {fp:.3f}   GROWN {gp:.3f}   "
          f"(Δ {gp - fp:+.3f})")
    print(f"  1-NN flat          FROZEN {ff:.3f}   GROWN {gf:.3f}   "
          f"(Δ {gf - ff:+.3f})")
    ftt, gtt = mean(real, "frozen_1nn_trans"), mean(real, "grown_1nn_trans")
    print(f"  1-NN TRANS (i31)   FROZEN {ftt:.3f}   GROWN {gtt:.3f}   "
          f"(Δ {gtt - ftt:+.3f})   <- recognition THROUGH the transition channel")
    fcc, gcc = mean(real, "frozen_1nn_combo"), mean(real, "grown_1nn_combo")
    print(f"  1-NN COMBO (i32)   FROZEN {fcc:.3f}   GROWN {gcc:.3f}   "
          f"(Δ {gcc - fcc:+.3f})   <- COMBINATORIAL recognition (flat AND trans)")
    print(f"  *** COMBINATORIAL vs EACH SINGLE CHANNEL (grown) ***")
    print(f"      COMBO {gcc:.3f}  vs  flat-only(i31) {gf:.3f} "
          f"(Δ {gcc - gf:+.3f})  vs  trans-only(i31) {gtt:.3f} "
          f"(Δ {gcc - gtt:+.3f})  vs  frozen {fcc:.3f} (Δ {gcc - fcc:+.3f})")
    print(f"      => COMBO beats BOTH single channels? "
          f"vs-flat {'YES' if gcc > gf else 'no'}  "
          f"vs-trans {'YES' if gcc > gtt else 'no'}  "
          f"=> {'BEATS BOTH' if (gcc > gf and gcc > gtt) else 'does NOT beat both'}")
    # ablation: dropping the cohort warp alone (fixed seed bank, no warp).
    nwm = mean(real, "nowarp_margin")
    nwp, nwf = mean(real, "nowarp_1nn_pool"), mean(real, "nowarp_1nn_flat")
    nwt = mean(real, "nowarp_1nn_trans")
    nwc = mean(real, "nowarp_1nn_combo")
    print(f"  ABLATION no-warp+seed bank   margin {nwm:+.4f}  1NN-pool {nwp:.3f}"
          f"  1NN-flat {nwf:.3f}  1NN-trans {nwt:.3f}  1NN-combo {nwc:.3f}"
          f"   (isolates: drop cohort warp, keep 25 patches)")
    # control: the SELECTOR — grown-by-survival vs add-ALL-candidates (no select).
    gam = mean(real, "grown_all_margin")
    gap_, gaf = mean(real, "grown_all_1nn_pool"), mean(real, "grown_all_1nn_flat")
    gat = mean(real, "grown_all_1nn_trans")
    gac = mean(real, "grown_all_1nn_combo")
    print(f"  CONTROL  no-warp+ALL cands   margin {gam:+.4f}  1NN-pool {gap_:.3f}"
          f"  1NN-flat {gaf:.3f}  1NN-trans {gat:.3f}  1NN-combo {gac:.3f}"
          f"   (selector must beat unselected accretion)")

    print("\n  *** THE DECISIVE SHUFFLE TEST (transition selector + readout) ***")
    smp = mean(real_shuf, "grown_1nn_pool")
    smf = mean(real_shuf, "grown_1nn_flat")
    smt = mean(real_shuf, "grown_1nn_trans")
    smc = mean(real_shuf, "grown_1nn_combo")
    smm = mean(real_shuf, "grown_margin")
    stm = mean(real_shuf, "grown_trans_margin")
    print(f"  REAL    GROWN trans-margin {gtm:+.4f}  flat-margin {gm:+.4f}  "
          f"1NN-flat {gf:.3f}  1NN-pool {gp:.3f}  1NN-trans {gtt:.3f}  "
          f"1NN-combo {gcc:.3f}")
    print(f"  SHUFFLE GROWN trans-margin {stm:+.4f}  flat-margin {smm:+.4f}  "
          f"1NN-flat {smf:.3f}  1NN-pool {smp:.3f}  1NN-trans {smt:.3f}  "
          f"1NN-combo {smc:.3f}")
    # iter-31 bite: the recognition-through-transition readout must beat shuffle
    # (AND on its objective the trans-margin), the clean-generalisation bar.
    bites = (gtm > stm) and (gtt > smt)
    print(f"  => selector+readout BITES (REAL beats SHUFFLE)? "
          f"trans-margin {'YES' if gtm > stm else 'no'}  "
          f"1NN-trans {'YES' if gtt > smt else 'no'}  "
          f"=> {'BITES' if bites else 'DOES NOT BITE'}")
    print(f"     (legacy iter-30 flat-readout bite: 1NN-flat "
          f"{'YES' if gf > smf else 'no'})")
    # iter-32 combinatorial bite: the COMBINATORIAL recognition must beat shuffle.
    print(f"  => COMBINATORIAL recognition beats SHUFFLE? 1NN-combo REAL {gcc:.3f} "
          f"> SHUFFLE {smc:.3f} ? {'YES' if gcc > smc else 'no'}")
    print(f"  patches added (mean): "
          f"{mean(real, 'grown_added'):.1f} (transition) / "
          f"{mean(smooth, 'grown_added'):.1f} (smoothness)")

    print("\n  HEAD-TO-HEAD: transition-grown vs SMOOTHNESS-grown (iter-29):")
    sgm = mean(smooth, "grown_margin")
    sgp, sgf = mean(smooth, "grown_1nn_pool"), mean(smooth, "grown_1nn_flat")
    sgt = mean(smooth, "grown_1nn_trans")
    sgtm = mean(smooth, "grown_trans_margin")
    print(f"  flat-margin   TRANS {gm:+.4f}  SMOOTH {sgm:+.4f}")
    print(f"  trans-margin  TRANS {gtm:+.4f}  SMOOTH {sgtm:+.4f}")
    print(f"  1-NN flat     TRANS {gf:.3f}   SMOOTH {sgf:.3f}")
    print(f"  1-NN pooled   TRANS {gp:.3f}   SMOOTH {sgp:.3f}")
    print(f"  1-NN trans    TRANS {gtt:.3f}   SMOOTH {sgt:.3f}")

    print("\nPERSONA HVPT (agent-generated voices, held-out persona):")
    print(f"  same-word margin   FROZEN {persona['frozen_margin']:+.4f}  "
          f"GROWN {persona['grown_margin']:+.4f}  "
          f"(Δ {persona['grown_margin'] - persona['frozen_margin']:+.4f})")
    print(f"  1-NN pooled        FROZEN {persona['frozen_1nn_pool']:.3f}   "
          f"GROWN {persona['grown_1nn_pool']:.3f}   "
          f"(Δ {persona['grown_1nn_pool'] - persona['frozen_1nn_pool']:+.3f})")
    print(f"  1-NN flat (i31)    FROZEN {persona['frozen_1nn_flat']:.3f}   "
          f"GROWN {persona['grown_1nn_flat']:.3f}   "
          f"(Δ {persona['grown_1nn_flat'] - persona['frozen_1nn_flat']:+.3f})")
    print(f"  1-NN TRANS (i31)   FROZEN {persona['frozen_1nn_trans']:.3f}   "
          f"GROWN {persona['grown_1nn_trans']:.3f}   "
          f"(Δ {persona['grown_1nn_trans'] - persona['frozen_1nn_trans']:+.3f})")
    print(f"  1-NN COMBO (i32)   FROZEN {persona['frozen_1nn_combo']:.3f}   "
          f"GROWN {persona['grown_1nn_combo']:.3f}   "
          f"(Δ {persona['grown_1nn_combo'] - persona['frozen_1nn_combo']:+.3f})"
          f"  <- COMBINATORIAL")
    print(f"  COMBO vs single (grown): combo {persona['grown_1nn_combo']:.3f} "
          f"vs flat {persona['grown_1nn_flat']:.3f} "
          f"vs trans {persona['grown_1nn_trans']:.3f}  "
          f"=> {'beats both' if (persona['grown_1nn_combo'] > persona['grown_1nn_flat'] and persona['grown_1nn_combo'] > persona['grown_1nn_trans']) else 'not both'}")
    print(f"  SHUFFLE control    GROWN-1NN-pool "
          f"{persona_shuf['grown_1nn_pool']:.3f}   GROWN-1NN-trans "
          f"{persona_shuf['grown_1nn_trans']:.3f}   GROWN-1NN-combo "
          f"{persona_shuf['grown_1nn_combo']:.3f}")

    print("\n(grown = NO cohort warp + accreted patches selected by cross-voice "
          "survival; frozen = VTLN-to-cohort-canonical + fixed 25-patch bank)")


if __name__ == "__main__":
    main()
