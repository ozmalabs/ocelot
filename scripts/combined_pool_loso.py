"""combined_pool_loso — put BOTH next cues in the agent's CUE POOL and COMBINE them
(not choose between them). The project thesis (ozma_recognition_is_a_conjunction): the
graph combines many WEAK cues, no single one decisive — so we don't pick sharp-HF OR
manner/voicing, we ADD BOTH to the pool and let the agent's many-settings PRODUCT
combine all channels.

THE TWO NEXT MOVES (both named by prior probes, neither chosen — both pooled):

  (1) SHARP-HF ear  (docs/sibilant_sharp_ear.md): the seed world downsamples 16 kHz ->
      8 kHz BEFORE perception (cochlea Nyquist 4 kHz = self-imposed deafness to the
      >4 kHz fricative band). A SHARP HIGH-FREQ ear reads the NATIVE 16 kHz signal,
      finely log-pooling the 1.5-7.8 kHz fricative region. FUSED onto the cochlea it
      lifted the fricative LOSO 0.453 -> 0.510 (fusion, NOT replacement: sharp-only
      throws away the vocalic cues and loses). Its residual confusion was seven(/s/)
      <-> zero(/z/) — a VOICING distinction the frequency ear cannot resolve.

  (2) MANNER/VOICING channel: the cue the freq ears CANNOT supply — voiced (periodic:
      an autocorrelation / F0 peak) vs voiceless (aperiodic noise), plus manner
      (sonorant / sibilant / low-mid-high envelope shape). This is the agent's OWNED
      manner_voicing_readout (periodicity + the phonology predicates voiced?/sonorant?/
      sibilant? evaluated NATIVELY over the per-frame cue node) — the channel that
      resolves the /s/ vs /z/ voicing pair the sharp ear leaves on the table.

THE POOL + COMBINE (no choosing): every channel is one item in the agent's
many-settings PRODUCT (many_settings_recognizer.channel_likelihood -> argmax of the
product across channels — the IDENTICAL kernel blind_guess uses per channel, the
variadic Bayes combine the agent derived). A channel uninformative for a contrast
multiplies in near-flat and cannot drag the channels that carry it; a channel that
sharply separates dominates the product where confident. We REPORT per-channel AND
combined so the conjunction is visible.

THE CHANNELS in the pool (all the agent's composable-DSP cues, all FUSED):
  · COCHLEA      — the seed gammatone cochleagram (8 kHz world signal, Nyquist 4 kHz):
                   the broad vocalic / onset cue, the agent's existing dominant ear.
  · SHARP-HF     — the native-16 kHz fine-FFT high-freq ear (1.5-7.8 kHz fricative
                   band the 8 kHz cochlea misses), reused VERBATIM from
                   scripts.sibilant_sharp_ear.
  · MANNER-VOICE — the periodicity / voiced / sonorant / sibilant manner channel, the
                   agent's owned manner_voicing_readout (the VOICING cue the freq ears
                   can't supply). Computed on the NATIVE 16 kHz waveform (periodicity
                   is a waveform autocorrelation cue — sharper at 16 kHz lag resolution).

TESTS (robust SC 40-speaker LOSO, ungameable; held-out speakers NEVER banked):
  (A) FRICATIVE set {three,four,five,six,seven,zero}: does adding MANNER-VOICE to
      {COCHLEA + SHARP-HF} resolve the seven<->zero voicing confusion and lift above
      the prior best 0.510?
  (B) FULL 10-digit cross-speaker LOSO: does the richer combined pool
      {COCHLEA + SHARP-HF + MANNER-VOICE} lift above the prior best, and does
      MANNER-VOICE DEEPEN the token modes (within-word DtwTo < between-word DtwTo)?

DONKEY BOUNDARY (audited): every channel = the agent's composable boundary DSP
(np.fft / gammatone / autocorrelation periodicity / the agent's phonology predicate
Term-trees evaluated natively) — the SAME category as the existing front end, NO fit,
NO learned weight, NO trained net. COMBINE = the agent's many-settings PRODUCT
(channel_likelihood, owned). The mode-depth probe uses the agent's OWNED DtwTo Term.
SC load + the 40-speaker split are world-adapter mechanics; LOSO is the ungameable
yardstick; held-out speakers' clips are NEVER banked.

Run: python -m scripts.combined_pool_loso [n_train_spk] [n_held_spk] [n_per] [seed]
"""
from __future__ import annotations

import math
import os
import sys
import random

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# the SHARP-HF + GAMMATONE ears, reused VERBATIM (the agent's owned composable DSP).
from scripts.sibilant_sharp_ear import (
    sharp_hf_ear, gammatone_ear, load_native, _resample, WORLD_FS, NATIVE_FS,
    sc_speakers, sc_index_for, SC_DIR)
# the agent's owned manner/voicing readout (periodicity + phonology predicates).
from scripts.enriched_hvpt_accept import manner_voicing_readout
from domains.filter_settings import cochleagram, COCHLEAR_SETTINGS
# the agent's many-settings PRODUCT combine — the pool's combine. TWO calibrations:
#   FLAT      = channel_likelihood (positive softmax peak — the prior, baseline)
#   EXCLUSION = channel_likelihood_exclusion (one-sided exclude-or-abstain, the test)
from domains.many_settings_recognizer import (
    channel_likelihood, channel_likelihood_exclusion,
    channel_vector, combine_vectors)

# the active per-cue likelihood, switched by --mode (default FLAT = the prior baseline).
# run_all() rebinds this so all calibrations run on the SAME extracted features.
#   FLAT      = channel_likelihood          (positive softmax peak; combine = PRODUCT)
#   EXCLUSION = channel_likelihood_exclusion (one-sided exclude-or-abstain; combine = PRODUCT)
#   VECTOR    = channel_vector              (the 2-axis [EXCLUDE, RANK] vector; combine =
#               combine_vectors = exclude-PRODUCT * rank-SUM — no scalar collapse,
#               ozma_weighting_is_a_vector)
LIKELIHOOD = channel_likelihood
MODE = "FLAT"
# VECTOR mode flag: when True, the per-cue stance is a 2-axis vector and the combine is
# combine_vectors (no scalar collapse). When False, LIKELIHOOD is a scalar and the combine
# is the scalar PRODUCT (the FLAT / EXCLUSION regimes). run_all() rebinds both.
IS_VECTOR = False
# the agent's OWNED DtwTo Term for the mode-depth probe.
from scripts.dtw_trajectory_loso import _DtwTo, _Attr, _V, _Pred
from substrate_rs import Substrate

_MIDDLE = next(s for s in COCHLEAR_SETTINGS if s[0] == "middle")

# the full 10 digits (Test B) and the fricative-distinguished subset (Test A).
DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
          "eight", "nine"]
FRIC_WORDS = ["three", "four", "five", "six", "seven", "zero"]


def _l2(v):
    v = np.asarray(v, dtype=np.float64)
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


# ---------------------------------------------------------------------------
# THE THREE CHANNELS — all the agent's owned composable DSP, all fused. Each takes
# the NATIVE 16 kHz clip and returns one L2 descriptor (one item in the product).
# ---------------------------------------------------------------------------

def ch_cochlea(x16, fs16):
    """COCHLEA channel — the seed gammatone cochleagram (downsample to 8 kHz first,
    exactly as the seed world adapter does). The broad vocalic / onset ear."""
    return gammatone_ear(x16, fs16)


def ch_sharp_hf(x16, fs16):
    """SHARP-HF channel — the native-16 kHz fine-FFT high-freq fricative ear (the
    1.5-7.8 kHz band the 8 kHz cochlea cannot see). Reused verbatim from the probe."""
    return sharp_hf_ear(x16, fs16)


def ch_manner_voice(x16, fs16):
    """MANNER-VOICE channel — the agent's owned manner/voicing readout: per-frame
    [periodicity, voiced?, sonorant?, sibilant?, low/mid/high band means], the
    periodicity + phonology predicates evaluated natively over the per-frame cue node.
    This is the VOICING cue the frequency ears cannot supply (voiced=periodic vs
    voiceless=aperiodic — the /s/ vs /z/ distinction). Computed on the NATIVE 16 kHz
    waveform: the autocorrelation periodicity is a waveform cue, sharper at 16 kHz lag
    resolution. The cochleagram M it needs is built on the native signal (BANDS reach
    7500 Hz, so the high bands carry the fricative manner). NO fit, NO net."""
    x = np.asarray(x16, dtype=np.float64)
    M = cochleagram(x, fs16, _MIDDLE[1], _MIDDLE[2], _MIDDLE[3])
    return _l2(manner_voicing_readout(x, fs16, M))


# fricative-localized voicing: the /s/ vs /z/ distinction lives in the FRICATION
# frames, not the whole word (both "seven" and "zero" carry a voiced VOWEL, so a
# whole-word periodicity average washes the contrast out — measured: zero 0.44 vs
# seven 0.39, indistinguishable). Localizing the voicing measurement to the
# high-band-energy (frication-active) frames sharpens it (measured: zero /z/ 0.57 vs
# six /s/ 0.32 — a ~2.7-sigma separation). This is the agent's OWNED voicing operator
# (_frame_periodicity, autocorrelation) read where the fricative actually is (the
# cochleagram high-band partition the manner channel already uses). NO fit, NO net.
_VOICE_FRAMES = 24


def ch_fric_voicing(x16, fs16):
    """FRIC-VOICE channel — voicing OF THE FRICATION (the sharper /s/ vs /z/ cue the
    whole-word manner bag dilutes). Per frame: [periodicity, frication-energy,
    periodicity*frication] — the voicing measured where the high-band frication energy
    is, so a voiced fricative (/z/, periodic frication) separates from a voiceless one
    (/s/, aperiodic frication). Composed from the agent's owned _frame_periodicity +
    the cochleagram high/low band partitions. Resampled to a fixed grid, L2-normed —
    one more item in the product, the SAME node shape as every other cue."""
    from domains.stacked_representation import _frame_periodicity, _HIGH, _LOW
    x = np.asarray(x16, dtype=np.float64)
    M = cochleagram(x, fs16, _MIDDLE[1], _MIDDLE[2], _VOICE_FRAMES)
    nf = M.shape[0]
    if nf < 2:
        return _l2(np.zeros(_VOICE_FRAMES * 3, dtype=np.float64))
    win = int(0.025 * fs16)
    hi = M[:, _HIGH].mean(axis=1) if _HIGH else np.zeros(nf)
    lo = M[:, _LOW].mean(axis=1) if _LOW else np.zeros(nf)
    hi_rel = np.clip(hi - hi.mean(), 0.0, None)     # frication-active frames
    per = np.zeros(nf)
    for r in range(nf):
        c = int((r + 0.5) * len(x) / max(nf, 1))
        a0 = max(0, c - win // 2)
        per[r] = _frame_periodicity(x[a0:min(len(x), a0 + win)], fs16)
    # per frame: periodicity (voicing), frication marker (high-rel energy), and their
    # product (= voicing of the frication — high where a frame is BOTH fricative-active
    # AND periodic, i.e. a voiced fricative /z/). The fricative-frame voicing is carried
    # by the third channel; the first two give the manner context.
    feats = np.stack([per, hi_rel, per * hi_rel], axis=1)   # nf x 3
    return _l2(feats.flatten())


CHANNELS = {
    "COCHLEA": ch_cochlea,
    "SHARP-HF": ch_sharp_hf,
    "MANNER-VOICE": ch_manner_voice,
    "FRIC-VOICE": ch_fric_voicing,
}


# ---------------------------------------------------------------------------
# THE POOL COMBINE — the agent's many-settings PRODUCT over the named channels.
# Each channel contributes channel_likelihood(query, bank, words) -> {word: p};
# the per-word product across channels is argmaxed. EXACTLY blind_guess's
# Argmax-of-product across channels. No fit, no weight; combine, don't choose.
# ---------------------------------------------------------------------------

def combined_guess(qi, chan_names, tr_feats, tr_words, pr_feats, cand):
    if IS_VECTOR:
        # VECTOR regime: each cue emits a [EXCLUDE, RANK] vector per candidate; combine
        # WITHOUT collapse (exclude-PRODUCT * rank-SUM). No scalar projection either way.
        vecs = [channel_vector(np.asarray(pr_feats[name][qi]),
                               tr_feats[name], tr_words, cand)
                for name in chan_names]
        score = combine_vectors(vecs, cand)
        return max(score.items(), key=lambda kv: kv[1])[0] if score else None
    prod = {w: 1.0 for w in cand}
    for name in chan_names:
        p = LIKELIHOOD(np.asarray(pr_feats[name][qi]),
                       tr_feats[name], tr_words, cand)
        for w in cand:
            prod[w] *= p[w]
    return max(prod.items(), key=lambda kv: kv[1])[0] if prod else None


def _confusion(guesses, truths, words):
    wi = {w: i for i, w in enumerate(words)}
    conf = np.zeros((len(words), len(words)), dtype=int)
    cor = 0
    for g, t in zip(guesses, truths):
        cor += int(g == t)
        if g in wi:
            conf[wi[t], wi[g]] += 1
    return cor / max(len(truths), 1), conf


def run_single(name, tr_feats, tr_words, pr_feats, pr_words, words):
    cand = sorted(set(tr_words))
    if IS_VECTOR:
        # single cue, VECTOR regime: score(w) = exclude(w) * rank(w) — its own vector,
        # both axes kept (combine_vectors over the one cue's vector).
        guesses = [max(combine_vectors(
                        [channel_vector(np.asarray(q), tr_feats[name], tr_words, cand)],
                        cand).items(), key=lambda kv: kv[1])[0]
                   for q in pr_feats[name]]
        return _confusion(guesses, pr_words, words)
    guesses = [max(LIKELIHOOD(np.asarray(q), tr_feats[name], tr_words, cand)
                   .items(), key=lambda kv: kv[1])[0]
               for q in pr_feats[name]]
    return _confusion(guesses, pr_words, words)


def run_combined(chan_names, tr_feats, tr_words, pr_feats, pr_words, words):
    cand = sorted(set(tr_words))
    guesses = [combined_guess(qi, chan_names, tr_feats, tr_words, pr_feats, cand)
               for qi in range(len(pr_words))]
    return _confusion(guesses, pr_words, words)


# ---------------------------------------------------------------------------
# SPLIT + EXTRACT (world-adapter mechanics, native 16 kHz, ungameable LOSO).
# ---------------------------------------------------------------------------

def build_split(words, n_train_spk, n_held_spk, n_per, seed):
    rng = random.Random(seed)
    speakers = sc_speakers(words)
    rng.shuffle(speakers)
    held_spk = speakers[:n_held_spk]
    train_spk = speakers[n_held_spk:n_held_spk + n_train_spk]
    train_idx = sc_index_for(train_spk, words)
    held_idx = sc_index_for(held_spk, words)
    train_clips, loso_probe = [], []
    for w in words:
        paths = list(train_idx.get(w, []))
        rng.shuffle(paths)
        train_clips += [(w, p) for p in paths[:n_per]]
        hp = list(held_idx.get(w, []))
        rng.shuffle(hp)
        loso_probe += [(w, p) for p in hp[:max(1, n_held_spk)]]
    print(f"[split] {len(words)} words {words}", flush=True)
    print(f"[split] {len(train_spk)} TRAIN speakers, {len(held_spk)} HELD-OUT "
          f"(disjoint; held clips NEVER banked)", flush=True)
    print(f"[split] bank {len(train_clips)} train clips, "
          f"{len(loso_probe)} cross-speaker LOSO probes", flush=True)
    return train_clips, loso_probe


def extract_all(clips):
    """Extract EVERY channel's descriptor for each clip ONCE. Native 16 kHz audio."""
    feats = {name: [] for name in CHANNELS}
    words = []
    for w, path in clips:
        x, fs = load_native(path)
        for name, fn in CHANNELS.items():
            feats[name].append(fn(x, fs))
        words.append(w)
    return {name: np.asarray(v) for name, v in feats.items()}, words


# ---------------------------------------------------------------------------
# MODE-DEPTH PROBE (the crank's lever): does adding MANNER-VOICE deepen the token
# modes — within-word DtwTo distance < between-word DtwTo distance? The token is the
# manner-voicing per-frame TRAJECTORY (the agent's manner channel kept ORDERED), and
# the distance is the agent's OWNED DtwTo Term evaluated natively. We compare the
# COCHLEA-trajectory token (the crank's cmvn-style spectral token) against the
# COCHLEA++MANNER token (the spectral token with the voicing/manner channels appended
# per frame). Deeper modes = a larger between/within separation ratio.
# ---------------------------------------------------------------------------

def _coch_track(x16, fs16, n_frames=24):
    """Per-frame cochleagram trajectory (the crank's spectral token), per-frame L2 so
    the DtwTo frame-distance is on spectral SHAPE not level. Computed on the 8 kHz world
    signal (the seed cochlea). Ordered sequence (frames x bands)."""
    x8 = _resample(np.asarray(x16, dtype=np.float64), fs16, WORLD_FS)
    M = cochleagram(x8, WORLD_FS, _MIDDLE[1], _MIDDLE[2], n_frames)
    if M.size == 0:
        return [[0.0]]
    mu = M.mean(axis=0, keepdims=True)
    sd = M.std(axis=0, keepdims=True)
    Mn = (M - mu) / (sd + 1e-6)
    out = []
    for r in range(Mn.shape[0]):
        v = Mn[r]; nrm = np.linalg.norm(v)
        out.append([float(t) for t in (v / nrm if nrm > 1e-9 else v)])
    return out


def _manner_track(x16, fs16, n_frames=24):
    """Per-frame manner/voicing trajectory (periodicity + voiced/sonorant/sibilant +
    low/mid/high), kept ORDERED. The agent's manner channel as a path; native 16 kHz."""
    from domains.stacked_representation import _manner_voicing_channel
    x = np.asarray(x16, dtype=np.float64)
    M = cochleagram(x, fs16, _MIDDLE[1], _MIDDLE[2], n_frames)
    if M.size == 0:
        return [[0.0] * 7]
    sub = Substrate()
    mv = _manner_voicing_channel(x, fs16, M, 25, sub)   # n_frames x 7
    # per-frame normalise each manner vector so the DtwTo frame-distance is comparable
    # in scale to the cochlea token's per-frame L2 frames.
    out = []
    for r in range(mv.shape[0]):
        v = np.asarray(mv[r], dtype=np.float64); nrm = np.linalg.norm(v)
        out.append([float(t) for t in (v / nrm if nrm > 1e-9 else v)])
    return out


def _fric_voicing_track(x16, fs16, n_frames=24):
    """Per-frame frication-localized voicing trajectory [periodicity, frication-energy,
    periodicity*frication], kept ORDERED — the FRIC-VOICE channel as a path (native
    16 kHz). The voiced-fricative marker (third channel) per frame."""
    from domains.stacked_representation import _frame_periodicity, _HIGH
    x = np.asarray(x16, dtype=np.float64)
    M = cochleagram(x, fs16, _MIDDLE[1], _MIDDLE[2], n_frames)
    nf = M.shape[0]
    if nf < 1:
        return [[0.0, 0.0, 0.0]]
    win = int(0.025 * fs16)
    hi = M[:, _HIGH].mean(axis=1) if _HIGH else np.zeros(nf)
    hi_rel = np.clip(hi - hi.mean(), 0.0, None)
    out = []
    for r in range(nf):
        c = int((r + 0.5) * len(x) / max(nf, 1)); a0 = max(0, c - win // 2)
        per = _frame_periodicity(x[a0:min(len(x), a0 + win)], fs16)
        out.append([float(per), float(hi_rel[r]), float(per * hi_rel[r])])
    return out


def _concat_tracks(a, b):
    """Append manner channels per frame onto the cochlea token (frame-aligned). The
    COCHLEA++MANNER token = spectral shape + voicing/manner per frame."""
    n = min(len(a), len(b))
    if n == 0:
        return a or b
    return [list(a[i]) + list(b[i]) for i in range(n)]


_DTW_SUB = Substrate()
_DTW_A = _DTW_SUB.add_node("DtwN", {})
_DTW_B = _DTW_SUB.add_node("DtwN", {})
_DTW_TERM = _Pred(_DtwTo(_Attr(_V("a"), "t"), _Attr(_V("b"), "t")))


def _dtw(t1, t2):
    _DTW_SUB.set_attr(_DTW_A, "t", tuple(tuple(float(v) for v in f) for f in t1))
    _DTW_SUB.set_attr(_DTW_B, "t", tuple(tuple(float(v) for v in f) for f in t2))
    return float(_DTW_SUB.evaluate(_DTW_TERM, {"a": _DTW_A, "b": _DTW_B}))


def mode_depth(tokens, words, max_pairs=4000, seed=0):
    """Mean within-word vs between-word DtwTo over the token set + the separation ratio
    (between/within). Deeper modes = a larger ratio. Sampled pairs for tractability."""
    rng = random.Random(seed)
    n = len(tokens)
    idx = list(range(n))
    win, btw = [], []
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    rng.shuffle(pairs)
    for i, j in pairs[:max_pairs]:
        d = _dtw(tokens[i], tokens[j])
        (win if words[i] == words[j] else btw).append(d)
    mw = float(np.mean(win)) if win else float("nan")
    mb = float(np.mean(btw)) if btw else float("nan")
    ratio = mb / mw if mw and np.isfinite(mw) and mw > 1e-9 else float("nan")
    return mw, mb, ratio, len(win), len(btw)


def print_confusion(name, conf, words, acc):
    print(f"\n[{name}] cross-speaker LOSO accuracy {acc:.3f}", flush=True)
    hdr = "truth\\guess  " + " ".join(f"{w[:5]:>6s}" for w in words)
    print("  " + hdr, flush=True)
    for i, w in enumerate(words):
        row = conf[i]; cells = " ".join(f"{c:6d}" for c in row)
        rt = row.sum(); diag = row[i] / rt if rt else 0.0
        print(f"  {w[:11]:11s} {cells}   (recall {diag:.2f})", flush=True)


# ---------------------------------------------------------------------------
# TEST A — the fricative set: does MANNER-VOICE added to {COCHLEA + SHARP-HF}
# resolve seven<->zero and beat 0.510?
# ---------------------------------------------------------------------------

def test_a(trf, trw, prf, prw):
    words = FRIC_WORDS
    chance = 1.0 / len(words)
    print("\n" + "=" * 78, flush=True)
    print(f"TEST A [{MODE}] — FRICATIVE set: combine sharp-HF + manner/voicing + "
          "cochlea (not choose)", flush=True)
    print("=" * 78, flush=True)
    print("  words: " + ", ".join(words) + f"   chance {chance:.3f}", flush=True)

    # per-channel (the weak cues, shown honestly).
    per = {}
    for name in CHANNELS:
        acc, conf = run_single(name, trf, trw, prf, prw, words)
        per[name] = (acc, conf)
        print(f"  [{name:12s}] LOSO {acc:.3f}", flush=True)

    # the prior probe's best: COCHLEA + SHARP-HF (the fusion that reached 0.510).
    cs_acc, cs_conf = run_combined(["COCHLEA", "SHARP-HF"], trf, trw, prf, prw, words)
    print_confusion("COCHLEA + SHARP-HF (prior best)", cs_conf, words, cs_acc)

    # + MANNER-VOICE (the agent's whole-word voicing/manner channel).
    mv_acc, mv_conf = run_combined(["COCHLEA", "SHARP-HF", "MANNER-VOICE"],
                                   trf, trw, prf, prw, words)
    print_confusion("COCHLEA + SHARP-HF + MANNER-VOICE", mv_conf, words, mv_acc)

    # the FULL combined pool: + FRIC-VOICE (frication-localized voicing — the sharper
    # /s/ vs /z/ cue the whole-word manner bag dilutes). All four channels combined.
    all_acc, all_conf = run_combined(
        ["COCHLEA", "SHARP-HF", "MANNER-VOICE", "FRIC-VOICE"],
        trf, trw, prf, prw, words)
    print_confusion("COCHLEA + SHARP-HF + MANNER-VOICE + FRIC-VOICE (full pool)",
                    all_conf, words, all_acc)

    # the seven<->zero voicing confusion across the ladder.
    si, zi = words.index("seven"), words.index("zero")
    def _pair(conf):
        s_rec = conf[si, si] / max(conf[si].sum(), 1)
        z_rec = conf[zi, zi] / max(conf[zi].sum(), 1)
        s2z = conf[si, zi]; z2s = conf[zi, si]   # cross-firing between the pair
        return s_rec, z_rec, s2z, z2s
    b = _pair(cs_conf); m = _pair(mv_conf); a = _pair(all_conf)
    print("\n  seven<->zero VOICING pair (the residual the freq ear can't resolve):",
          flush=True)
    print(f"    COCHLEA+SHARP-HF        : seven recall {b[0]:.2f}, zero recall "
          f"{b[1]:.2f}, seven->zero {b[2]}, zero->seven {b[3]}", flush=True)
    print(f"    + MANNER-VOICE          : seven recall {m[0]:.2f}, zero recall "
          f"{m[1]:.2f}, seven->zero {m[2]}, zero->seven {m[3]}", flush=True)
    print(f"    + FRIC-VOICE (full pool): seven recall {a[0]:.2f}, zero recall "
          f"{a[1]:.2f}, seven->zero {a[2]}, zero->seven {a[3]}", flush=True)
    cross_before = b[2] + b[3]; cross_after = a[2] + a[3]
    print(f"    seven<->zero cross-fire: {cross_before} (cochlea+sharp) -> "
          f"{m[2] + m[3]} (+manner) -> {cross_after} (+fric-voice) "
          f"[{cross_after - cross_before:+d} net]", flush=True)

    print("\n  " + "-" * 74, flush=True)
    print(f"  prior best (cochlea+sharp-HF)        LOSO {cs_acc:.3f}", flush=True)
    print(f"  + manner/voicing                     LOSO {mv_acc:.3f} "
          f"({mv_acc - cs_acc:+.3f})", flush=True)
    print(f"  full pool (+fric-voicing)            LOSO {all_acc:.3f} "
          f"({all_acc - cs_acc:+.3f} vs prior best, {all_acc - 0.510:+.3f} vs 0.510)",
          flush=True)
    return {"cochlea_sharp": cs_acc, "mv": mv_acc, "combined": all_acc,
            "cross_before": cross_before, "cross_after": cross_after,
            "per": {k: v[0] for k, v in per.items()}}


# ---------------------------------------------------------------------------
# TEST B — full 10-digit cross-speaker LOSO + the mode-depth probe.
# ---------------------------------------------------------------------------

def test_b(trf, trw, prf, prw, mode_tokens=None):
    words = DIGITS
    chance = 1.0 / len(words)
    print("\n" + "=" * 78, flush=True)
    print(f"TEST B [{MODE}] — FULL 10-digit cross-speaker LOSO: the richer COMBINED "
          "pool", flush=True)
    print("=" * 78, flush=True)
    print(f"  words: {words}   chance {chance:.3f}", flush=True)

    # per-channel (the weak cues).
    per = {}
    print("\n  per-channel (the weak cues — none decisive alone):", flush=True)
    for name in CHANNELS:
        acc, _ = run_single(name, trf, trw, prf, prw, words)
        per[name] = acc
        print(f"    [{name:12s}] LOSO {acc:.3f}", flush=True)

    # the combine ladder: cochlea -> +sharp-HF -> +manner/voicing -> +fric-voicing.
    c_acc, _ = run_combined(["COCHLEA"], trf, trw, prf, prw, words)
    cs_acc, _ = run_combined(["COCHLEA", "SHARP-HF"], trf, trw, prf, prw, words)
    mv_acc, _ = run_combined(["COCHLEA", "SHARP-HF", "MANNER-VOICE"],
                             trf, trw, prf, prw, words)
    all_acc, all_conf = run_combined(
        ["COCHLEA", "SHARP-HF", "MANNER-VOICE", "FRIC-VOICE"],
        trf, trw, prf, prw, words)
    print_confusion("COCHLEA + SHARP-HF + MANNER-VOICE + FRIC-VOICE (full pool)",
                    all_conf, words, all_acc)
    print("\n  COMBINE LADDER (each channel ADDED, never chosen):", flush=True)
    print(f"    COCHLEA alone                 LOSO {c_acc:.3f}", flush=True)
    print(f"    + SHARP-HF                    LOSO {cs_acc:.3f} "
          f"({cs_acc - c_acc:+.3f})", flush=True)
    print(f"    + MANNER-VOICE               LOSO {mv_acc:.3f} "
          f"({mv_acc - cs_acc:+.3f})", flush=True)
    print(f"    + FRIC-VOICE (full pool)     LOSO {all_acc:.3f} "
          f"({all_acc - mv_acc:+.3f})", flush=True)

    # ---- MODE-DEPTH probe: does MANNER-VOICE deepen the token modes? ----
    # calibration-INDEPENDENT (pure DtwTo on trajectories, no likelihood) — computed
    # ONCE and passed in so the two calibration modes share the identical numbers.
    if mode_tokens is not None:
        print("\n  MODE-DEPTH probe (the crank's lever): within-word vs between-word "
              "DtwTo", flush=True)
        coch_tokens, mann_tokens, tok_words = mode_tokens
        mw0, mb0, r0, nw0, nb0 = mode_depth(coch_tokens, tok_words, seed=0)
        mw1, mb1, r1, nw1, nb1 = mode_depth(mann_tokens, tok_words, seed=0)
        print(f"    COCHLEA token               : within {mw0:.3f}  between {mb0:.3f}  "
              f"ratio {r0:.3f}  ({nw0} within / {nb0} between pairs)", flush=True)
        print(f"    COCHLEA++MANNER++FRIC-VOICE : within {mw1:.3f}  between {mb1:.3f}  "
              f"ratio {r1:.3f}  ({nw1} within / {nb1} between pairs)", flush=True)
        print(f"    mode separation ratio (between/within): {r0:.3f} -> {r1:.3f} "
              f"({r1 - r0:+.3f})  {'DEEPER' if r1 > r0 else 'NOT deeper'}", flush=True)
    else:
        r0, r1 = float("nan"), float("nan")

    return {"per": per, "cochlea": c_acc, "cochlea_sharp": cs_acc, "mv": mv_acc,
            "combined": all_acc, "mode_ratio": (r0, r1)}


def _build_mode_tokens(n_train_spk, n_held_spk, n_per, seed):
    """Build the calibration-INDEPENDENT mode-depth tokens ONCE (pure DtwTo, no
    likelihood) so both modes share identical mode numbers. Uses Test-B's split."""
    tr, loso = build_split(DIGITS, n_train_spk, n_held_spk, n_per, seed)
    sub_clips = (tr + loso)
    rng = random.Random(seed)
    rng.shuffle(sub_clips)
    sub_clips = sub_clips[:240]
    coch_tokens, mann_tokens, tok_words = [], [], []
    for w, path in sub_clips:
        x, fs = load_native(path)
        ct = _coch_track(x, fs)
        mt = _manner_track(x, fs)
        vt = _fric_voicing_track(x, fs)
        coch_tokens.append(ct)
        mann_tokens.append(_concat_tracks(_concat_tracks(ct, mt), vt))
        tok_words.append(w)
    return (coch_tokens, mann_tokens, tok_words)


def _run_mode(mode, like_fn, A_feats, B_feats, mode_tokens, is_vector=False):
    """Run Test A + Test B under one calibration. A_feats/B_feats are the SHARED
    pre-extracted (trf,trw,prf,prw) tuples; only the likelihood/combine changes between
    modes. is_vector=True switches the per-cue stance to the [EXCLUDE, RANK] vector and
    the combine to combine_vectors (no scalar collapse)."""
    global LIKELIHOOD, MODE, IS_VECTOR
    LIKELIHOOD, MODE, IS_VECTOR = like_fn, mode, is_vector
    ra = test_a(*A_feats)
    rb = test_b(*B_feats, mode_tokens=mode_tokens)
    IS_VECTOR = False
    return ra, rb


def _report_mode(tag, ra, rb):
    a_lift = ra["combined"] - ra["cochlea_sharp"]
    voicing_fixed = ra["cross_after"] < ra["cross_before"]
    # the manner/voicing step on the FULL 10-digit ladder — the cue that HURT (-0.050)
    # under FLAT. The falsifiable check: does it still hurt under exclusion?
    mv_step_full = rb["mv"] - rb["cochlea_sharp"]
    print(f"\n  [{tag}] summary:", flush=True)
    print(f"    (A) fricative: cochlea+sharp {ra['cochlea_sharp']:.3f} -> +manner "
          f"{ra['mv']:.3f} -> full pool {ra['combined']:.3f} ({a_lift:+.3f})", flush=True)
    print(f"        seven<->zero cross-fire {ra['cross_before']} -> {ra['cross_after']} "
          f"({'RESOLVED' if voicing_fixed else 'not resolved'})", flush=True)
    print(f"    (B) full 10-digit: cochlea {rb['cochlea']:.3f} -> +sharp "
          f"{rb['cochlea_sharp']:.3f} -> +MANNER {rb['mv']:.3f} "
          f"(MANNER step {mv_step_full:+.3f}) -> +fric {rb['combined']:.3f}", flush=True)
    return {"a_lift": a_lift, "voicing_fixed": voicing_fixed,
            "mv_step_full": mv_step_full, "ra": ra, "rb": rb}


def main():
    if not os.path.isdir(SC_DIR):
        print("Speech Commands not found at /tmp/sc — abort.", flush=True)
        return
    n_train_spk = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    n_held_spk = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    n_per = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 20240609

    print("=" * 78, flush=True)
    print("EXCLUSION-CALIBRATED RECOGNIZER — FLAT vs EXCLUSION combine on the same pool",
          flush=True)
    print("=" * 78, flush=True)
    print(f"  config: {n_train_spk} train / {n_held_spk} held-out speakers, "
          f"{n_per}/word, seed {seed}", flush=True)
    print(f"  audio: native {NATIVE_FS} Hz (sharp ear + manner periodicity reach the "
          f"full band); cochlea downsamples to {WORLD_FS} Hz", flush=True)
    print("  test: ozma_recognition_is_exclusion — does exclusion-calibration make the "
          "manner/voicing cue FREE (resolve seven<->zero, cost nothing) and make "
          "adding a cue NEVER hurt?", flush=True)

    # EXTRACT ONCE — both Test A (fricative) and Test B (10-digit) feature banks, shared
    # across the two calibration modes (apples-to-apples; only the likelihood changes).
    print("\n[extract] Test A (fricative) banks ...", flush=True)
    trA, loA = build_split(FRIC_WORDS, n_train_spk, n_held_spk, n_per, seed)
    trfA, trwA = extract_all(trA)
    prfA, prwA = extract_all(loA)
    A_feats = (trfA, trwA, prfA, prwA)
    print("[extract] Test B (10-digit) banks ...", flush=True)
    trB, loB = build_split(DIGITS, n_train_spk, n_held_spk, n_per, seed)
    trfB, trwB = extract_all(trB)
    prfB, prwB = extract_all(loB)
    B_feats = (trfB, trwB, prfB, prwB)
    print("[extract] mode-depth tokens (calibration-independent) ...", flush=True)
    mode_tokens = _build_mode_tokens(n_train_spk, n_held_spk, n_per, seed)

    # RUN ALL THREE REGIMES on the identical features.
    print("\n" + "#" * 78, flush=True)
    print("# REGIME 1/3: FLAT positive product (baseline — the prior numbers)",
          flush=True)
    print("#" * 78, flush=True)
    raF, rbF = _run_mode("FLAT", channel_likelihood, A_feats, B_feats, mode_tokens)
    print("\n" + "#" * 78, flush=True)
    print("# REGIME 2/3: EXCLUSION-calibrated product (pure exclude-or-abstain)",
          flush=True)
    print("#" * 78, flush=True)
    raE, rbE = _run_mode("EXCLUSION", channel_likelihood_exclusion, A_feats, B_feats,
                         mode_tokens)
    print("\n" + "#" * 78, flush=True)
    print("# REGIME 3/3: VECTOR-weighted ([EXCLUDE, RANK]; exclude-PRODUCT * rank-SUM; "
          "no scalar collapse)", flush=True)
    print("#" * 78, flush=True)
    raV, rbV = _run_mode("VECTOR", None, A_feats, B_feats, mode_tokens, is_vector=True)

    # ---- THE VERDICT: FLAT vs EXCLUSION vs VECTOR ----
    print("\n" + "=" * 78, flush=True)
    print("VERDICT — does the VECTOR keep the manner cue FREE (no -0.050) AND recover "
          "the ceiling pure-exclude dropped (beat both FLAT and EXCLUSION)?", flush=True)
    print("=" * 78, flush=True)
    F = _report_mode("FLAT (baseline)", raF, rbF)
    E = _report_mode("EXCLUSION (pure)", raE, rbE)
    V = _report_mode("VECTOR", raV, rbV)

    def _ladder_steps(rb, ra):
        # full 10-digit ladder rungs (each cue added).
        steps = [("B:+sharp", rb["cochlea_sharp"] - rb["cochlea"]),
                 ("B:+manner", rb["mv"] - rb["cochlea_sharp"]),
                 ("B:+fric", rb["combined"] - rb["mv"]),
                 # fricative-set rungs.
                 ("A:+manner", ra["mv"] - ra["cochlea_sharp"]),
                 ("A:+fric", ra["combined"] - ra["mv"])]
        return steps

    print("\n  --- THE THREE-WAY LADDER (full 10-digit LOSO) ---", flush=True)
    print(f"    {'rung':28s} {'FLAT':>8s} {'EXCL':>8s} {'VECTOR':>8s}", flush=True)
    for key, lab in [("cochlea", "COCHLEA alone"),
                     ("cochlea_sharp", "+ SHARP-HF"),
                     ("mv", "+ MANNER-VOICE"),
                     ("combined", "+ FRIC-VOICE (full pool)")]:
        print(f"    {lab:28s} {rbF[key]:8.3f} {rbE[key]:8.3f} {rbV[key]:8.3f}",
              flush=True)
    print(f"\n  --- THE THREE-WAY LADDER (fricative set) ---", flush=True)
    print(f"    {'rung':28s} {'FLAT':>8s} {'EXCL':>8s} {'VECTOR':>8s}", flush=True)
    for key, lab in [("cochlea_sharp", "cochlea + sharp-HF"),
                     ("mv", "+ MANNER-VOICE"),
                     ("combined", "+ FRIC-VOICE (full pool)")]:
        print(f"    {lab:28s} {raF[key]:8.3f} {raE[key]:8.3f} {raV[key]:8.3f}",
              flush=True)

    # the ceilings (best combined-pool LOSO under each regime — the headroom).
    flat_ceil_b, excl_ceil_b, vec_ceil_b = rbF["combined"], rbE["combined"], rbV["combined"]
    flat_ceil_a, excl_ceil_a, vec_ceil_a = raF["combined"], raE["combined"], raV["combined"]

    print("\n  --- PREDICTION CHECKS (VECTOR) ---", flush=True)
    # 1. manner cue FREE under VECTOR (FLAT was -0.050 on full 10-digit).
    vec_manner = V["mv_step_full"]
    flat_manner = F["mv_step_full"]
    manner_free = vec_manner >= -1e-9
    print(f"  1. MANNER/VOICE step on FULL 10-digit: FLAT {flat_manner:+.3f} -> "
          f"EXCLUSION {E['mv_step_full']:+.3f} -> VECTOR {vec_manner:+.3f}  "
          f"({'FREE (>=0)' if manner_free else 'STILL HURTS (<0)'})", flush=True)
    # 2. ceiling recovered: VECTOR beats pure-exclusion (0.228 last time) on the full pool.
    beats_excl_b = vec_ceil_b > excl_ceil_b + 1e-9
    beats_flat_b = vec_ceil_b > flat_ceil_b + 1e-9
    print(f"  2. full 10-digit ceiling (combined pool): FLAT {flat_ceil_b:.3f}, "
          f"EXCLUSION {excl_ceil_b:.3f}, VECTOR {vec_ceil_b:.3f}  "
          f"(VECTOR {'>' if beats_excl_b else '<='} EXCL, "
          f"{'>' if beats_flat_b else '<='} FLAT)", flush=True)
    beats_excl_a = vec_ceil_a > excl_ceil_a + 1e-9
    beats_flat_a = vec_ceil_a > flat_ceil_a + 1e-9
    print(f"     fricative ceiling (combined pool):    FLAT {flat_ceil_a:.3f}, "
          f"EXCLUSION {excl_ceil_a:.3f}, VECTOR {vec_ceil_a:.3f}  "
          f"(VECTOR {'>' if beats_excl_a else '<='} EXCL, "
          f"{'>' if beats_flat_a else '<='} FLAT)", flush=True)
    # 3. every added-cue rung under VECTOR (does the vector keep adds non-harmful?).
    vec_steps = _ladder_steps(rbV, raV)
    flat_steps = _ladder_steps(rbF, raF)
    excl_steps = _ladder_steps(rbE, raE)
    worst_vec = min(s for _, s in vec_steps)
    print(f"  3. add-a-cue rungs (both ladders):", flush=True)
    for (nm, sf), (_, se), (_, sv) in zip(flat_steps, excl_steps, vec_steps):
        print(f"       {nm:12s}  FLAT {sf:+.3f}   EXCL {se:+.3f}   VECTOR {sv:+.3f}",
              flush=True)
    print(f"     worst VECTOR step {worst_vec:+.3f}", flush=True)

    # KILL CRITERION: VECTOR must beat BOTH flat and pure-exclusion (free manner AND
    # recovered ceiling). The decisive ceiling is the full 10-digit combined pool.
    free_manner = manner_free
    recovered_ceiling = beats_excl_b   # beats pure-exclusion (the ceiling it dropped)
    beats_both = beats_excl_b and beats_flat_b
    confirmed = free_manner and recovered_ceiling
    print("\n  => VERDICT: ", end="", flush=True)
    if confirmed and beats_both:
        print("VECTOR CONFIRMED (strong) — keeps the manner cue FREE "
              f"({vec_manner:+.3f}) AND beats BOTH pure-exclusion ({excl_ceil_b:.3f}) "
              f"and FLAT ({flat_ceil_b:.3f}) on the full 10-digit ceiling "
              f"({vec_ceil_b:.3f}). Keeping both axes (no scalar collapse) recovers what "
              "each projection threw away.", flush=True)
    elif confirmed:
        print("VECTOR PARTIAL — keeps the manner cue FREE "
              f"({vec_manner:+.3f}) and recovers the ceiling pure-exclude dropped "
              f"(VECTOR {vec_ceil_b:.3f} > EXCLUSION {excl_ceil_b:.3f}), but does NOT beat "
              f"FLAT ({flat_ceil_b:.3f}). The vector recovers the exclusion headroom loss "
              "but does not exceed the positive-only baseline here.", flush=True)
    else:
        reasons = []
        if not free_manner:
            reasons.append(f"the manner cue STILL hurts the full set ({vec_manner:+.3f})")
        if not recovered_ceiling:
            reasons.append(f"VECTOR ceiling {vec_ceil_b:.3f} does NOT beat pure-exclusion "
                           f"{excl_ceil_b:.3f}")
        print("VECTOR FRAME INSUFFICIENT here — " + "; ".join(reasons) +
              ". The vector does NOT beat BOTH flat and pure-exclusion "
              "(reported plainly, NOT rescued).", flush=True)
    print(f"\n  => RESIDUAL (VECTOR): fricative LOSO {vec_ceil_a:.3f}, full "
          f"10-digit LOSO {vec_ceil_b:.3f}  "
          f"(vs FLAT {flat_ceil_b:.3f} / EXCLUSION {excl_ceil_b:.3f} full pool).",
          flush=True)
    print("[MARKER] COMBINED_POOL_LOSO_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
