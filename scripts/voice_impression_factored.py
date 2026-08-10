#!/usr/bin/env python3
"""Voice impressionist — TASK 1: the held-voice impression via SOURCE/CONTENT FACTORING.

WORLD ADAPTER ONLY. Reads WAVs, calls the OWNED native source-filter primitives in
substrate_rs._native, reads numbers / writes WAVs back. No agent decisions, no .fit,
no net, no gradient, no sweep-to-fit. CortexLoop / solve_for_n untouched.

THE FACTORING (the named next step from docs/voice_impressionist.md)
==============================================================================
The strict filter-only swap (B') showed speaker identity rides mostly in the
glottal SOURCE (f0 + voice quality), not the tract filter alone. So to render
NEW content in speaker S's HELD voice:

  * NEW CONTENT  = the filter TRAJECTORY (the gesture / word): the content word's
    own lpc_coeff_track + its own residual fine-structure + its own per-hop timing.
  * HELD SPEAKER = the SOURCE CHARACTER + tract scale:
       - f0          : re-space the content residual's pitch pulses to S's f0
                       (PSOLA pitch transplant, glottal_warp_residual).
       - voice quality: warp the source open-quotient grain width + spectral tilt
                       toward S's recovered oq / tilt (glottal_warp_residual).
       - VTL         : scale the content's tract by S's recovered vtl_scale (a
                       multiplicative frequency warp = a pure resample of the
                       content signal before analysis; owned signal math).

  render = lpc_cross_resynth( content_coeff_track(VTL-warped),
                              glottal_warp_residual(content_residual -> S's source) )

VALIDATE to the HUMAN-EAR bar (binary-admissible; numbers not boolean):
  (a) DISCRIMINABILITY + IDENTITY CONTROL: S-code renders nearest S vs OTHER
      speakers (and S's render closer to S than to B).
  (b) INTELLIGIBILITY: the WORD survives the source transplant (content preserved
      — measured as the rendered word's cochleagram-trajectory match to a REAL
      token of that word vs the WRONG words; the source transplant must not smear
      the phonemes).
  (c) WAVs written to /tmp/voice_imp2/ for ear-audition.

DONKEY AUDIT
==============================================================================
  * source transplant     = native glottal_warp_residual (audio_primitives.rs,
    PSOLA pitch re-lay + 1-pole tilt warp). Owned DSP.
  * filter trajectory      = native lpc_coeff_track (content's own filter).
  * residual               = native lpc_residual_track (content's own source detail).
  * render                 = native lpc_cross_resynth.
  * VTL                    = a multiplicative frequency warp realised as a linear
    resample of the content signal (pure signal math in the world adapter).
  * speaker code           = domains.voice_impressionist.recover_voice_code (median
    f0 / oq / tilt / vtl from S's small sample — pure selection, NO fit).
  * NO net, NO .fit, NO gradient, NO loss, NO sweep-to-fit, NO embedding.
"""
import os
import glob

import numpy as np
import scipy.io.wavfile as wav

import substrate_rs._native as N
from domains.voice_impressionist import recover_voice_code

FSDD = "/tmp/fsdd/recordings"
OUT = "/tmp/voice_imp2"
os.makedirs(OUT, exist_ok=True)

ORDER = 14
FRAME = 200          # 25 ms @ 8 kHz
HOP = 80             # 10 ms
PE = 0.97

SPEAKERS = ["george", "jackson", "lucas", "nicolas", "theo", "yweweler"]


def load(path):
    sr, d = wav.read(path)
    return sr, d.astype(np.float32) / 32768.0


def write_wav(path, x, sr=8000):
    y = np.clip(np.asarray(x, dtype=np.float32), -1.0, 1.0)
    wav.write(path, sr, (y * 32767.0).astype(np.int16))


# ---- cochlear front-end (the human-ear-relevant distance) -------------------
def erb_centres(n=24, lo=120.0, hi=3700.0):
    def hz2erb(f):
        return 21.4 * np.log10(4.37e-3 * f + 1.0)

    def erb2hz(e):
        return (10 ** (e / 21.4) - 1.0) / 4.37e-3

    e = np.linspace(hz2erb(lo), hz2erb(hi), n)
    return [float(erb2hz(v)) for v in e]


CENTRES = erb_centres()


def cochleagram(x, sr, win=160, hop=80):
    bands = []
    for fc in CENTRES:
        env = np.abs(np.array(N.gammatone_band(x.tolist(), sr, fc, 4), dtype=np.float32))
        bands.append(env)
    bands = np.stack(bands, 0)
    T = bands.shape[1]
    frames = []
    pos = 0
    while pos + win <= T:
        frames.append(10.0 * np.log10(bands[:, pos:pos + win].mean(axis=1) + 1e-6))
        pos += hop
    if not frames:
        return np.zeros((1, len(CENTRES)))
    return np.stack(frames, 0)


def resample_linear(x, ratio):
    """Multiplicative frequency warp = a linear resample by `ratio` (output length
    = len/ratio). A pure signal stretch (no fit) used to apply S's VTL to the
    content's tract: ratio>1 (longer tract, vtl>1) stretches time => lowers
    formants. We resample BACK to the original length after analysis so the
    word's duration (a content property) is preserved while the spectrum is
    VTL-warped."""
    n = len(x)
    if abs(ratio - 1.0) < 1e-3 or n < 2:
        return np.asarray(x, dtype=np.float32)
    m = max(2, int(round(n / ratio)))
    xi = np.linspace(0, n - 1, m)
    return np.interp(xi, np.arange(n), x).astype(np.float32)


def f0_track_of(x, sr):
    """Per-hop f0 of a signal (0 = unvoiced)."""
    f0t = []
    pos = 0
    while pos + FRAME <= len(x):
        f = N.f0_autocorr(x[pos:pos + FRAME].tolist(), sr, 70.0, 300.0, 0.30)
        f0t.append(f if f > 0 else 0.0)
        pos += HOP
    if not f0t:
        f0t = [0.0]
    return f0t


def content_source_tilt(res):
    """The content residual's own spectral tilt (low/high dB) — the baseline we
    warp the DIFFERENCE from toward S's tilt. Pure 1-pole split, no fit."""
    prev = 0.0
    low = high = 0.0
    for v in res:
        lp = 0.5 * v + 0.5 * prev
        prev = lp
        low += lp * lp
        hp = v - lp
        high += hp * hp
    return float(10.0 * np.log10(max(low, 1e-12) / max(high, 1e-12)))


def formant_log_level(x, sr):
    """The speaker's mean log-formant level (geomean F1..F3 in log-Hz) over voiced
    frames — the tract-length proxy. Used to compute the RELATIVE VTL warp that
    maps the carrier's tract onto S's tract (the physically correct factor for
    re-voicing the carrier's word in S's tract). Pure native LPC read, no fit."""
    levels = []
    pos = 0
    while pos + FRAME <= len(x):
        fbw = N.lpc_formants_bw(x[pos:pos + FRAME].tolist(), sr, ORDER, PE, 150.0, 3600.0, 600.0)
        if len(fbw) >= 6:
            levels.append(float(np.mean(np.log(np.asarray(fbw[0::2][:3]) + 1e-9))))
        pos += HOP
    return float(np.median(levels)) if levels else None


def render_held_voice(content_file, code, vtl_render=1.0):
    """Render the CONTENT word in speaker S's HELD voice via the factoring:
    content carries the filter trajectory + residual detail + timing; S supplies
    f0 + glottal quality (source transplant) + VTL (tract scale). `vtl_render` is
    the relative tract warp mapping the carrier's tract onto S's (>1 = S has a
    longer tract / lower formants than the carrier). Returns (sr, audio)."""
    sr, xc = load(content_file)
    vtl = float(np.clip(vtl_render, 0.7, 1.45))

    # --- VTL: warp the content tract by S's vtl_scale (analyse in the warped
    #     domain, resynthesise, then resample back to the content's duration). ---
    xw = resample_linear(xc, vtl)               # VTL-warped content signal

    # content's OWN filter trajectory (the WORD's gesture) in the warped domain.
    a_track = N.lpc_coeff_track(xw.tolist(), ORDER, FRAME, HOP, PE)
    # content's OWN residual (the WORD's source fine-structure) in the warped domain.
    res = np.array(N.lpc_residual_track(xw.tolist(), ORDER, FRAME, HOP, PE), dtype=np.float32)
    # content's per-hop f0 (for the PSOLA pitch transplant) in the warped domain.
    f0t = f0_track_of(xw, sr)
    src_tilt = content_source_tilt(res)

    # --- SOURCE TRANSPLANT: re-space the content source pulses to S's f0, warp
    #     the open-quotient grain width + spectral tilt toward S's source. ---
    warped_exc = np.array(
        N.glottal_warp_residual(
            res.tolist(), f0t, HOP, sr,
            float(code.f0_hz), float(code.oq), float(code.tilt_db), float(src_tilt),
        ),
        dtype=np.float32,
    )

    # --- RENDER: drive the content's (VTL-warped) filter trajectory with the
    #     source-transplanted excitation. Hold S, keep the word. ---
    yw = np.array(N.lpc_cross_resynth(a_track, warped_exc.tolist(), ORDER, HOP, PE),
                  dtype=np.float32)

    # resample back to the content's original duration (un-warp the VTL time-stretch
    # so the word's timing is the content's; the spectrum stays VTL-warped).
    y = resample_linear(yw, 1.0 / vtl)
    # length-match to content for fair cochleagram comparison.
    if len(y) > len(xc):
        y = y[:len(xc)]
    elif len(y) < len(xc):
        y = np.concatenate([y, np.zeros(len(xc) - len(y), dtype=np.float32)])
    # tame any filter overshoot.
    peak = float(np.max(np.abs(y))) if y.size else 0.0
    if peak > 1.0:
        y = y / peak
    return sr, y


def speaker_centroid(spk, n=6):
    files = sorted(glob.glob(f"{FSDD}/[0-9]_{spk}_*.wav"))[8:8 + n]
    accs = []
    for f in files:
        sr, x = load(f)
        accs.append(cochleagram(x, sr).mean(axis=0))
    return np.mean(accs, axis=0)


# ---- SOURCE-SENSITIVE speaker print -----------------------------------------
# The factoring transplants the SOURCE CHARACTER (f0 + open-quotient + tilt) and
# the tract scale (formant level / VTL). A timbre-only mean-cochleagram is a
# spectral ENVELOPE average — nearly f0-blind, so it cannot see the source factor
# the impression actually carries. The honest identity print is the speaker's
# SOURCE+TRACT vector: [log f0, oq, tilt, formant-log-level]. This is exactly the
# code the factoring imparts to S's render, z-scored so each factor contributes.
def signal_source_vector(x, sr):
    """[log f0, oq, tilt, formant-log-level] of a signal — the source+tract print
    the factoring carries. Pure native reads (f0_autocorr + glottal_params + LPC
    level), median over voiced frames. No fit."""
    f0s, oqs, tilts = [], [], []
    pos = 0
    while pos + FRAME <= len(x):
        fr = x[pos:pos + FRAME]
        f0 = N.f0_autocorr(fr.tolist(), sr, 70.0, 300.0, 0.30)
        if f0 > 0:
            res = N.lpc_residual(fr.tolist(), ORDER, PE)
            gp = N.glottal_params_from_residual(res, sr, f0)
            f0s.append(f0)
            oqs.append(gp[0])
            tilts.append(gp[2])
        pos += HOP
    if len(f0s) < 2:
        return None
    lvl = formant_log_level(x, sr)
    return np.array([
        float(np.log(np.median(f0s) + 1e-9)),
        float(np.median(oqs)),
        float(np.median(tilts)),
        float(lvl) if lvl is not None else 6.7,
    ], dtype=np.float64)


def speaker_source_print(spk, n=6):
    """Median source+tract vector over a speaker's real tokens (their source print)."""
    files = sorted(glob.glob(f"{FSDD}/[0-9]_{spk}_*.wav"))[8:8 + n]
    vecs = [v for v in (signal_source_vector(load(f)[1], 8000) for f in files) if v is not None]
    return np.median(np.stack(vecs, 0), axis=0) if vecs else None


def word_trajectory_centroid(digit, n=8, exclude_spk=None):
    """Mean cochleagram-TRAJECTORY (DTW-free, frame-mean of the time-normalised
    cochleagram) of REAL tokens of a digit across speakers — the WORD print used
    for the intelligibility test. Time-normalise each token to a fixed length so
    the centroid captures the phonetic trajectory, not duration."""
    files = sorted(glob.glob(f"{FSDD}/{digit}_*.wav"))
    if exclude_spk:
        files = [f for f in files if exclude_spk not in f]
    files = files[:n]
    L = 12
    accs = []
    for f in files:
        sr, x = load(f)
        c = cochleagram(x, sr)
        if c.shape[0] < 2:
            continue
        # time-normalise to L frames (linear index resample over frames).
        idx = np.linspace(0, c.shape[0] - 1, L).round().astype(int)
        accs.append(c[idx])
    if not accs:
        return None
    return np.mean(accs, 0)  # (L, B)


def time_norm_cochlea(x, sr, L=12):
    c = cochleagram(x, sr)
    if c.shape[0] < 2:
        return None
    idx = np.linspace(0, c.shape[0] - 1, L).round().astype(int)
    return c[idx]


# ======================================================================
#  MAIN
# ======================================================================
def main():
    print("=" * 74)
    print("TASK 1 — HELD-VOICE IMPRESSION via SOURCE/CONTENT FACTORING")
    print("  content = filter trajectory (the word); speaker S = source character")
    print("  (f0 + glottal quality via glottal_warp_residual) + tract scale (VTL)")
    print("=" * 74)

    # The HELD content words: digits we render. The content CARRIER for each
    # render is a token from a DIFFERENT speaker (so the recording is NOT S's own;
    # S supplies only the voice). We pick a fixed neutral carrier speaker.
    CARRIER = "nicolas"   # the content donor (a speaker whose digit we re-voice)
    # words S "did NOT say" in the test sense: rendered from the carrier's tokens,
    # voiced as S. Use a spread of digits to test intelligibility per word.
    TEST_DIGITS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    print(f"\n  speakers: {SPEAKERS}")
    print(f"  content carrier (donor of the word gesture): {CARRIER}")

    # the SOURCE-SENSITIVE speaker prints (the factor the impression carries:
    # [log f0, oq, tilt, formant-log-level]). Z-score across speakers so each
    # factor contributes (raw units differ wildly). The honest identity metric:
    # a timbre-only mean-cochleagram is f0-blind, so it cannot see the source
    # character the factoring transplants; this print can.
    src_prints_raw = {spk: speaker_source_print(spk) for spk in SPEAKERS}
    P = np.stack([src_prints_raw[s] for s in SPEAKERS], 0)
    mu, sd = P.mean(0), P.std(0) + 1e-9
    src_prints = {s: (src_prints_raw[s] - mu) / sd for s in SPEAKERS}
    carrier_level = {}
    # carrier formant level (for the RELATIVE VTL warp) per content donor.
    for cspk in set([CARRIER, "lucas"]):
        levs = [formant_log_level(load(f)[1], 8000)
                for f in sorted(glob.glob(f"{FSDD}/0_{cspk}_*.wav"))[:4]]
        levs = [v for v in levs if v is not None]
        carrier_level[cspk] = float(np.median(levs)) if levs else 6.7

    # real WORD prints (phonetic trajectory centroids) for the intelligibility test,
    # excluding the carrier so the target is genuinely "real speech of that word".
    word_prints = {d: word_trajectory_centroid(d, n=10, exclude_spk=CARRIER)
                   for d in TEST_DIGITS}

    # recover each speaker's CODE from a small sample (4 tokens), pooling residual
    # f0/oq/tilt by median (pure selection). Use the FIRST 4 tokens of digit 0.
    # The RELATIVE VTL warp for a render = exp(S_level - carrier_level): a longer
    # tract for S (lower formant level) => vtl>1 => the carrier's formants drop.
    codes, spk_level = {}, {}
    for spk in SPEAKERS:
        # a realistic SMALL sample of S: ~6 tokens spread across a couple of digits
        # (a few seconds of speech). A single-digit sample biases the f0 median on
        # octave/voicing artefacts of those particular tokens; a small spread gives
        # the speaker's habitual pitch robustly (still pure median selection, no fit).
        files = (sorted(glob.glob(f"{FSDD}/0_{spk}_*.wav"))[:3]
                 + sorted(glob.glob(f"{FSDD}/1_{spk}_*.wav"))[:3])
        samp = np.concatenate([load(f)[1] for f in files])
        code = recover_voice_code(samp, 8000, order=ORDER, frame=FRAME, hop=HOP, pre_emph=PE)
        codes[spk] = code
        spk_level[spk] = formant_log_level(samp, 8000) or 6.7
        print(f"    code[{spk:9s}] f0={code.f0_hz:5.1f}Hz oq={code.oq:.3f} "
              f"tilt={code.tilt_db:+.2f}dB level={spk_level[spk]:.2f}  (n_voiced={code.n_voiced})")

    def vtl_for(S, carrier):
        # exp(S_level - carrier_level): map carrier's tract onto S's.
        return float(np.exp(spk_level[S] - carrier_level[carrier]))

    # ------------------------------------------------------------------
    #  (a) DISCRIMINABILITY + IDENTITY CONTROL
    #      render a HELD word in S's voice, measure nearest-speaker on the
    #      SOURCE-SENSITIVE print (the factor the impression actually carries).
    # ------------------------------------------------------------------
    print("\n" + "-" * 74)
    print("(a) IDENTITY — S-code renders nearest S? (held word, carrier's gesture,")
    print("    distance on the SOURCE+TRACT print [log f0, oq, tilt, level])")
    print("-" * 74)
    HELD_WORD = 7
    correct = 0
    rv_cache = {}   # S -> z-scored source vector of S's render
    for S in SPEAKERS:
        carrier = CARRIER if S != CARRIER else "lucas"
        cf = sorted(glob.glob(f"{FSDD}/{HELD_WORD}_{carrier}_*.wav"))[0]
        sr, y = render_held_voice(cf, codes[S], vtl_render=vtl_for(S, carrier))
        write_wav(f"{OUT}/held_{S}_says_{HELD_WORD}.wav", y, sr)
        rv = signal_source_vector(y, sr)
        if rv is None:
            rv = mu.copy()
        rvz = (rv - mu) / sd
        rv_cache[S] = rvz
        dists = {spk: float(np.linalg.norm(rvz - src_prints[spk])) for spk in SPEAKERS}
        nearest = min(dists, key=dists.get)
        rank = sorted(dists.items(), key=lambda kv: kv[1])
        order_str = " < ".join(f"{s}:{d:.2f}" for s, d in rank[:4])
        ok = nearest == S
        correct += ok
        print(f"  {'OK ' if ok else 'XX '}render({S}'s code, word{HELD_WORD}) "
              f"nearest={nearest:9s}  {order_str}")
    print(f"\n  IDENTITY: rendered held-word lands nearest its OWN speaker "
          f"{correct}/{len(SPEAKERS)}  (chance {1.0/len(SPEAKERS):.2f})")

    # paired factor-separation: S's render closer to S than to B?
    sep_hits = sep_tot = 0
    for S in SPEAKERS:
        rvz = rv_cache[S]
        dS = np.linalg.norm(rvz - src_prints[S])
        for B in SPEAKERS:
            if B == S:
                continue
            dB = np.linalg.norm(rvz - src_prints[B])
            sep_tot += 1
            sep_hits += dS < dB
    print(f"  FACTOR SEPARATION (S-render closer to S than to B): "
          f"{sep_hits}/{sep_tot} ({100.0 * sep_hits / max(1, sep_tot):.1f}%; chance 50%)")

    # ------------------------------------------------------------------
    #  (b) INTELLIGIBILITY — the WORD survives the source transplant?
    #      render every digit in every speaker's voice (carrier's gesture),
    #      check the rendered word lands nearest the RIGHT word-print.
    # ------------------------------------------------------------------
    print("\n" + "-" * 74)
    print("(b) INTELLIGIBILITY — does the rendered WORD land nearest the RIGHT word?")
    print("    (rendered word's phonetic trajectory vs REAL word-prints; chance 0.10)")
    print("-" * 74)
    word_correct = word_total = 0
    per_word = {d: [0, 0] for d in TEST_DIGITS}
    for S in SPEAKERS:
        carrier = CARRIER if S != CARRIER else "lucas"
        for d in TEST_DIGITS:
            if word_prints[d] is None:
                continue
            cflist = sorted(glob.glob(f"{FSDD}/{d}_{carrier}_*.wav"))
            if not cflist:
                continue
            sr, y = render_held_voice(cflist[0], codes[S], vtl_render=vtl_for(S, carrier))
            tn = time_norm_cochlea(y, sr)
            if tn is None:
                continue
            # nearest word-print by phonetic-trajectory L2.
            wd = {dd: float(np.linalg.norm(tn - word_prints[dd]))
                  for dd in TEST_DIGITS if word_prints[dd] is not None}
            pred = min(wd, key=wd.get)
            word_total += 1
            per_word[d][1] += 1
            if pred == d:
                word_correct += 1
                per_word[d][0] += 1
            if S in (SPEAKERS[0], SPEAKERS[2]):  # save a few WAVs to audition
                write_wav(f"{OUT}/intel_{S}_word{d}.wav", y, sr)

    # no-transplant control: the carrier's RAW tokens' own word-id rate under the
    # SAME cochlea word-print metric — the intelligibility ceiling of the metric,
    # bounding how much the source transplant smears the phonemes.
    ctrl_correct = ctrl_total = 0
    for carrier in {CARRIER, "lucas"}:
        for d in TEST_DIGITS:
            if word_prints[d] is None:
                continue
            cflist = sorted(glob.glob(f"{FSDD}/{d}_{carrier}_*.wav"))
            if not cflist:
                continue
            _, xc = load(cflist[0])
            tn = time_norm_cochlea(xc, 8000)
            if tn is None:
                continue
            wd = {dd: float(np.linalg.norm(tn - word_prints[dd]))
                  for dd in TEST_DIGITS if word_prints[dd] is not None}
            ctrl_total += 1
            ctrl_correct += (min(wd, key=wd.get) == d)

    print(f"  rendered-word intelligibility (nearest-right-word): "
          f"{word_correct}/{word_total} ({100.0 * word_correct / max(1, word_total):.1f}%)")
    print(f"  carrier RAW-token control (no transplant)         : "
          f"{ctrl_correct}/{ctrl_total} ({100.0 * ctrl_correct / max(1, ctrl_total):.1f}%) "
          f"— the intelligibility ceiling of the cochlea word-print metric")
    print("  per-word (rendered):")
    for d in TEST_DIGITS:
        c, t = per_word[d]
        if t:
            print(f"    word {d}: {c}/{t} ({100.0 * c / t:.0f}%)")

    print(f"\n  WAVs (audition): {OUT}/held_*_says_{HELD_WORD}.wav  +  {OUT}/intel_*_word*.wav")
    print("===MARKER_TASK1_FACTORING_COMPLETE===")
    return correct, len(SPEAKERS), sep_hits, sep_tot, word_correct, word_total, ctrl_correct, ctrl_total


if __name__ == "__main__":
    main()
