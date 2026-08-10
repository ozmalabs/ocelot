"""ladefoged_broadbent_diagnostic — the LB1957 "sliding template" probe on our model.

THE QUESTION (Ladefoged & Broadbent 1957; Chodroff & Stilp 2022 replication):
does the model perceive a FIXED ambiguous test token RELATIVE to the formant range
established by a preceding CARRIER (the human extrinsic / "sliding template"
normalization), or ABSOLUTELY — by the test's own formants alone, regardless of
carrier?

DESIGN (donkey-clean: stimuli = the WORLD/synth; perception = the model unchanged):
  · ENDPOINTS — two clear vowel/word endpoints (e.g. "bit" [high F1-ish] vs "bet")
    synthesised at a NEUTRAL talker; these are the model's two banked exemplars (its
    lexicon). The category readout is which endpoint the test is nearer, in the
    model's own feature space (the same 1-NN cognition+hat the recognizer uses).
  · TEST — a FIXED token, AMBIGUOUS between the two endpoints, identical bytes in
    every condition. Synthesised once at a neutral talker.
  · CARRIER — a phrase whose formant RANGE is shifted UP (smaller vocal tract /
    higher formants) vs DOWN (larger VT / lower formants). VTL shift is a UNIFORM
    multiplicative scaling of all formants -> realised here by resampling the
    waveform (the textbook VTL warp), so the ONLY thing differing across conditions
    is the carrier's formant range. The test bytes never change.

MEASUREMENT: the model's perceived category (and a continuous category score) of the
FIXED test, in three regimes:
  (1) TEST ALONE                 — the absolute baseline (no carrier).
  (2) CARRIER-UP  + TEST         — high-formant talker context.
  (3) CARRIER-DOWN + TEST        — low-formant talker context.
The carrier+test is presented as ONE clip (one utterance), because the ONLY place the
model could pick up extrinsic context is its per-utterance CMVN (residual_track with an
empty library = subtract the per-utterance mean) — the carrier frames enter that mean.
That is the model's single candidate "sliding template" mechanism; the diagnostic
tests whether it produces the LB shift.

PREDICTION (the embarrassing one): NO carrier effect — the model perceives the test by
its absolute formants -> the relative/speaker-normalised perception is MISSING.
SURPRISE/KILL: the test category shifts with the carrier -> we already have relative
perception and the cross-speaker wall is elsewhere.

This script is WORLD + HONEST MEASUREMENT only. The perception (feature_channels +
1-NN category) is the agent's model, called UNCHANGED.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import wave

import numpy as np

import domains.learned_voice_shape as LVS
from domains.filter_settings import cochleagram, COCHLEAR_SETTINGS
from domains.allpole_spectral_envelope import allpole_ear
from domains.filter_settings import fft_ear
from domains.grown_representation import seed_patches, bands_to_patches

FS = 8000
_MIDDLE = next(s for s in COCHLEAR_SETTINGS if s[0] == "middle")
_SEED_PATCHES = seed_patches()


# ---------------------------------------------------------------------------
# WORLD: espeak voicebox + a VTL (formant) warp by resampling.
# ---------------------------------------------------------------------------

def synth_raw(word, variant="m1", pitch=50, rate=160, fs=FS):
    """Voice `word` via espeak-ng, resampled to 8 kHz mono. Pure world I/O."""
    with tempfile.TemporaryDirectory() as d:
        raw = os.path.join(d, "r.wav")
        out = os.path.join(d, "o.wav")
        subprocess.run(["espeak-ng", "-v", f"en+{variant}", "-p", str(pitch),
                        "-s", str(rate), "-w", raw, word],
                       check=True, capture_output=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw,
                        "-ar", str(fs), "-ac", "1", "-sample_fmt", "s16", out],
                       check=True, capture_output=True)
        with wave.open(out, "rb") as wv:
            x = (np.frombuffer(wv.readframes(wv.getnframes()), dtype=np.int16)
                 .astype(np.float64) / 32768.0)
    return x, fs


def vtl_warp(x, alpha):
    """VTL formant warp: scale ALL formants by `alpha` (alpha>1 = higher formants =
    smaller vocal tract; alpha<1 = lower formants = larger VT) by a TRUE spectral
    scaling in the STFT domain — shift each frame's magnitude spectrum along the
    frequency axis by `alpha` (frequencies map f -> alpha*f) and resynthesise. This
    moves the formant envelope (and harmonics) up/down WITHOUT changing duration or
    frame rate, so the only thing it shifts is the formant RANGE. Pure boundary DSP
    (the textbook VTL/formant manipulation). NB: an earlier resample-then-resample-back
    version was a no-op (it restored the original spectrum) — this one genuinely warps
    the spectrum, verified by the formant audit."""
    x = np.asarray(x, dtype=np.float64)
    n = x.size
    if n == 0 or abs(alpha - 1.0) < 1e-6:
        return x.copy()
    nfft = 512
    hop = 128
    win = np.hanning(nfft)
    # pad so framing covers the whole signal
    npad = nfft + ((n - 1) // hop + 1) * hop
    xp = np.zeros(npad, dtype=np.float64)
    xp[:n] = x
    out = np.zeros(npad, dtype=np.float64)
    wsum = np.zeros(npad, dtype=np.float64)
    half = nfft // 2 + 1
    src_bins = np.arange(half)
    for start in range(0, npad - nfft, hop):
        seg = xp[start:start + nfft] * win
        S = np.fft.rfft(seg)
        mag = np.abs(S)
        phase = np.angle(S)
        # frequency warp: the value at warped bin k comes from source bin k/alpha
        # (so a formant at f moves to alpha*f). Interpolate magnitude; keep phase
        # (phase coherence is not needed for the formant-envelope shift this probe uses).
        src_idx = src_bins / alpha
        warped_mag = np.interp(src_idx, src_bins, mag, left=0.0, right=0.0)
        warped_phase = np.interp(src_idx, src_bins, phase, left=0.0, right=0.0)
        Sw = warped_mag * np.exp(1j * warped_phase)
        frame = np.fft.irfft(Sw, n=nfft) * win
        out[start:start + nfft] += frame
        wsum[start:start + nfft] += win * win
    nz = wsum > 1e-9
    out[nz] /= wsum[nz]
    return out[:n]


def measure_formants(x, fs=FS):
    """Crude F1/F2 readout (LPC poles) for the donkey audit only — to SHOW the carrier
    formant ranges actually shifted. Not used in perception."""
    from domains.lpc_formant_representation import _lpc_roots_formants
    x = np.asarray(x, dtype=np.float64)
    win = int(0.025 * fs)
    order = int(fs / 1000) + 2
    n = x.size
    f1s, f2s = [], []
    for c in range(win, n - win, win // 2):
        seg = x[c - win // 2:c + win // 2]
        fmts = _lpc_roots_formants(seg, fs, order)
        if len(fmts) >= 2:
            f1s.append(fmts[0])
            f2s.append(fmts[1])
    if not f1s:
        return (float("nan"), float("nan"))
    return (float(np.median(f1s)), float(np.median(f2s)))


# ---------------------------------------------------------------------------
# PERCEPTION: the model's own feature channels (the seed front end) — UNCHANGED.
# residual_track(.,.,[]) = per-utterance CMVN = the model's only extrinsic-context
# candidate. The category readout is the model's own 1-NN cognition+hat.
# ---------------------------------------------------------------------------

def _l2(v):
    v = np.asarray(v, dtype=np.float64)
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def feature_channels(x, fs):
    """The model's three seed channels (gammatone flat + FFT ear + all-pole ear) — the
    exact seed front end the recognizer reads (self_directed_speech_world.feature_channels
    fallback / agent_frontend SEED_CUES). The model's perception, unchanged."""
    x = np.asarray(x, dtype=np.float64)
    _, env_cut, dur_cut, nf = _MIDDLE
    M = cochleagram(x, fs, env_cut, dur_cut, nf)
    mu = M.mean(axis=0, keepdims=True)
    flat = _l2(bands_to_patches(M - mu, _SEED_PATCHES).flatten())
    return [flat, _l2(fft_ear(x, fs)), _l2(allpole_ear(x, fs))]


def residual_traj(x, fs):
    """The model's per-utterance-CMVN residual trajectory (frames x bands) — the
    SAME feature the DtwTo recognizer reads; an empty library == CMVN over THIS clip.
    This is the model's extrinsic-context candidate: a prepended carrier enters the
    per-utterance mean."""
    return np.asarray(LVS.residual_track(np.asarray(x, dtype=np.float64), float(fs), []),
                      dtype=np.float64)


def dtw(a, b):
    """Plain DTW distance between two (frames x bands) trajectories (Euclidean per
    frame). The same alignment the agent's DtwTo computes natively; here in numpy for
    the diagnostic readout only."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if a.size == 0 or b.size == 0:
        return float("inf")
    na, nb = a.shape[0], b.shape[0]
    D = np.full((na + 1, nb + 1), np.inf)
    D[0, 0] = 0.0
    for i in range(1, na + 1):
        ai = a[i - 1]
        for j in range(1, nb + 1):
            c = float(np.linalg.norm(ai - b[j - 1]))
            D[i, j] = c + min(D[i - 1, j], D[i, j - 1], D[i - 1, j - 1])
    return float(D[na, nb] / (na + nb))


def category_score(test_traj, end0_traj, end1_traj):
    """The model's CATEGORY readout of a test token, in its own feature space: the
    1-NN-style relative distance to the two banked endpoint exemplars.

      score = d(test, end0) - d(test, end1)
    score > 0 => nearer endpoint1; score < 0 => nearer endpoint0. The sign is the
    perceived category; the magnitude is how far from the boundary. This is exactly the
    agent's nearest-exemplar Argmin decision over a 2-word lexicon (end0 vs end1).
    """
    d0 = dtw(test_traj, end0_traj)
    d1 = dtw(test_traj, end1_traj)
    return d0 - d1, d0, d1


# ---------------------------------------------------------------------------
# The LB diagnostic.
# ---------------------------------------------------------------------------

def run(end0="bid", end1="bed", test_word=None, carrier="the word is",
        alpha_up=1.18, alpha_down=0.85):
    """Run the Ladefoged-Broadbent diagnostic.

    end0/end1 : the two clear vowel/word endpoints (the model's 2-word lexicon).
    test_word : the FIXED ambiguous test token (defaults to a mid VTL-warp blend cue;
                we synth a single word at a neutral VTL and place it at the boundary by
                an intermediate VTL warp so it sits between the endpoints' ranges).
    carrier   : the carrier phrase text (its formant RANGE is what we shift).
    alpha_up/down : the VTL formant-scale of the carrier (up = higher formants).
    """
    print("=" * 72)
    print("LADEFOGED-BROADBENT (1957) DIAGNOSTIC — sliding-template / relative vowel")
    print("=" * 72)
    print(f"endpoints: '{end0}' vs '{end1}' (the model's 2-word lexicon)")
    print(f"carrier  : '{carrier}'  (VTL-warped UP alpha={alpha_up} / DOWN alpha={alpha_down})")

    # ---- ENDPOINTS (neutral talker) — the model's banked exemplars ----
    x0, _ = synth_raw(end0)
    x1, _ = synth_raw(end1)
    end0_traj = residual_traj(x0, FS)
    end1_traj = residual_traj(x1, FS)
    f0 = measure_formants(x0)
    f1 = measure_formants(x1)
    print(f"\n[donkey audit] endpoint formants (median F1,F2 Hz):")
    print(f"   {end0}: F1~{f0[0]:.0f} F2~{f0[1]:.0f}    {end1}: F1~{f1[0]:.0f} F2~{f1[1]:.0f}")

    # ---- TEST: a FIXED token, ambiguous between the endpoints ----
    # synth one neutral word, then place it at the category boundary by a VTL warp
    # chosen so its score is near zero against the two endpoints. We pick the warp that
    # MINIMISES |score| (closest to the boundary) from a small grid — donkey-clean, this
    # is stimulus construction (making an ambiguous token), not perception.
    base_test, _ = synth_raw(end0)     # same lexical frame as endpoints
    best = None
    for a in np.linspace(0.80, 1.25, 19):
        tw = vtl_warp(base_test, a)
        tr = residual_traj(tw, FS)
        sc, _, _ = category_score(tr, end0_traj, end1_traj)
        if best is None or abs(sc) < abs(best[1]):
            best = (a, sc, tw)
    test_alpha, test_score0, test_wave = best
    print(f"\n[stimulus] chose ambiguous TEST at VTL alpha={test_alpha:.3f} "
          f"(test-alone score={test_score0:+.4f}, |score| minimal = boundary)")
    ft = measure_formants(test_wave)
    print(f"[donkey audit] test formants: F1~{ft[0]:.0f} F2~{ft[1]:.0f}")

    # ---- CARRIERS: same phrase, formant range shifted UP vs DOWN ----
    car_base, _ = synth_raw(carrier)
    car_up = vtl_warp(car_base, alpha_up)
    car_down = vtl_warp(car_base, alpha_down)
    fu, fd = measure_formants(car_up), measure_formants(car_down)
    print(f"\n[donkey audit] CARRIER formant ranges (median F1,F2 Hz):")
    print(f"   carrier-UP  (alpha={alpha_up}): F1~{fu[0]:.0f} F2~{fu[1]:.0f}")
    print(f"   carrier-DOWN(alpha={alpha_down}): F1~{fd[0]:.0f} F2~{fd[1]:.0f}")

    # small gap of silence between carrier and test (a real carrier-phrase pause)
    gap = np.zeros(int(0.08 * FS), dtype=np.float64)

    def perceive_test_in_context(carrier_wave):
        """Present (carrier + gap + test) as ONE clip; the model extracts its
        per-utterance-CMVN residual over the WHOLE clip, but we read the category of the
        TEST PORTION only (the frames corresponding to the test). This is the only way
        the carrier could shift test perception: via the shared per-utterance mean."""
        clip = np.concatenate([carrier_wave, gap, test_wave])
        full_traj = residual_traj(clip, FS)
        # map the test portion: by sample fraction -> frame fraction.
        n_total = clip.size
        n_test = test_wave.size
        n_frames = full_traj.shape[0]
        start = int(round((n_total - n_test) / n_total * n_frames))
        test_part = full_traj[start:]
        if test_part.shape[0] < 2:
            test_part = full_traj[-max(2, n_frames // 4):]
        return category_score(test_part, end0_traj, end1_traj)

    # ---- the three regimes ----
    test_traj_alone = residual_traj(test_wave, FS)
    sc_alone, d0a, d1a = category_score(test_traj_alone, end0_traj, end1_traj)
    sc_up, d0u, d1u = perceive_test_in_context(car_up)
    sc_down, d0d, d1d = perceive_test_in_context(car_down)

    def cat(sc):
        return end1 if sc > 0 else end0

    print("\n" + "-" * 72)
    print("RESULT — perceived category of the FIXED test token vs carrier")
    print("-" * 72)
    print(f"  score = d(test,{end0}) - d(test,{end1})   (>0 -> {end1}; <0 -> {end0})")
    print(f"  (1) TEST ALONE          : score={sc_alone:+.4f}  -> '{cat(sc_alone)}'")
    print(f"  (2) CARRIER-UP  + TEST  : score={sc_up:+.4f}  -> '{cat(sc_up)}'")
    print(f"  (3) CARRIER-DOWN+ TEST  : score={sc_down:+.4f}  -> '{cat(sc_down)}'")

    # EFFECT SIZE: the LB prediction is that an UP carrier (high formants, "small
    # talker") makes a fixed test sound like a LOWER-formant vowel (contrast), and DOWN
    # the reverse. The measured carrier effect is the score SHIFT between up and down.
    carrier_effect = sc_up - sc_down
    flip = cat(sc_up) != cat(sc_down)
    print("\n" + "-" * 72)
    print("EFFECT SIZE")
    print("-" * 72)
    print(f"  carrier effect (score_up - score_down) = {carrier_effect:+.4f}")
    print(f"  up vs down shift each from alone: "
          f"d_up={sc_up - sc_alone:+.4f}  d_down={sc_down - sc_alone:+.4f}")
    print(f"  category FLIP between carrier-up and carrier-down: {flip}")
    # scale the effect against the endpoint separation (a natural unit: the full
    # category range is |score(end0..end1)|).
    end_sep = abs(category_score(end1_traj, end0_traj, end1_traj)[0]
                  - category_score(end0_traj, end0_traj, end1_traj)[0])
    rel = carrier_effect / end_sep if end_sep > 1e-9 else float("nan")
    print(f"  endpoint score separation = {end_sep:.4f}; "
          f"carrier effect as fraction of it = {rel:+.3f}")

    print("\n" + "=" * 72)
    print("VERDICT")
    print("=" * 72)
    thresh = 0.05 * end_sep   # 5% of the category range = a real shift
    if flip or abs(carrier_effect) > thresh:
        print("  The model SHIFTS the test category with the carrier (LB effect PRESENT).")
        print("  -> RELATIVE / speaker-normalised perception EXISTS in the model.")
        print("  -> the cross-speaker wall is NOT a missing sliding-template; it is elsewhere.")
    else:
        print("  The model shows NO carrier effect (carrier_effect ~ 0, no category flip).")
        print("  -> the test is perceived ABSOLUTELY, by its own formants, regardless of carrier.")
        print("  -> CONFIRMED: the RELATIVE / speaker-normalised ('sliding template')")
        print("     perception is MISSING. This IS the cross-speaker mechanism the")
        print("     session's cross-speaker KILLs were probing.")

    # ---- OPTIONAL minimal sliding-template FIX (does it THEN produce the shift?) ----
    print("\n" + "-" * 72)
    print("OPTIONAL — minimal sliding-template fix (normalise test by carrier range)")
    print("-" * 72)
    # the carrier's formant range (geometric-mean formant) defines the talker; warp the
    # test by the INVERSE so the test is re-expressed RELATIVE to the carrier talker.
    car_ref_up = np.sqrt(max(1.0, fu[0]) * max(1.0, fu[1]))
    car_ref_down = np.sqrt(max(1.0, fd[0]) * max(1.0, fd[1]))
    neutral_ref = np.sqrt(max(1.0, ft[0]) * max(1.0, ft[1]))  # the test's own ref
    # normalise: warp test by (neutral_ref / carrier_ref) so a high-formant carrier
    # pulls the test's effective formants DOWN relative to that talker (the contrast).
    def fixed_score(carrier_ref):
        a = neutral_ref / carrier_ref if carrier_ref > 1e-6 else 1.0
        tw = vtl_warp(test_wave, a)
        tr = residual_traj(tw, FS)
        return category_score(tr, end0_traj, end1_traj)[0], a
    sc_up_fix, a_up = fixed_score(car_ref_up)
    sc_down_fix, a_down = fixed_score(car_ref_down)
    print(f"  carrier-up   ref formant={car_ref_up:.0f} -> test warp alpha={a_up:.3f} "
          f"-> score={sc_up_fix:+.4f} -> '{cat(sc_up_fix)}'")
    print(f"  carrier-down ref formant={car_ref_down:.0f} -> test warp alpha={a_down:.3f} "
          f"-> score={sc_down_fix:+.4f} -> '{cat(sc_down_fix)}'")
    fix_effect = sc_up_fix - sc_down_fix
    print(f"  FIXED carrier effect (score_up - score_down) = {fix_effect:+.4f} "
          f"(fraction of range = {fix_effect / end_sep if end_sep>1e-9 else float('nan'):+.3f})")
    print(f"  fix produces a category flip: {cat(sc_up_fix) != cat(sc_down_fix)}")

    print("\nLB_DIAGNOSTIC_COMPLETED")
    return {
        "sc_alone": sc_alone, "sc_up": sc_up, "sc_down": sc_down,
        "carrier_effect": carrier_effect, "end_sep": end_sep, "rel": rel,
        "flip": flip, "fix_effect": fix_effect,
    }


if __name__ == "__main__":
    run()
