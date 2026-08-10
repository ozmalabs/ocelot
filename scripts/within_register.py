#!/usr/bin/env python3
"""Within-register tract-shape resolver — does a recovered per-formant TRACT
SIGNATURE separate same-register males the 4-D source print cannot?

WORLD ADAPTER ONLY. The f0_resolver run (docs/f0_resolver.md) RETIRED f0
resolution as the cause: three independent pitch estimators agree the three male
VCTK speakers genuinely co-locate ~115-120 Hz, and the 4-D SOURCE print
[f0, oq, tilt, level] co-locates with them, so it cannot separate same-register
voices however perfect the pitch (full identity 2/8, oq+tilt 2/8, f0+level 0/8,
males-resolve 1/3). The discriminating cue must SURVIVE f0 overlap.

THE CUE I CHOOSE: TRACT GEOMETRY — the speaker's per-formant FORMANT-SPACE
signature (his idiosyncratic F1:F2:F3 offsets, i.e. tract SHAPE, which the single
VTL scalar throws away) PLUS his per-formant BANDWIDTHS (filter sharpness). This
is cleanly SPEAKER not CONTENT (tract geometry, not the phoneme being said), and
on this corpus it SPREADS the co-located males where f0/oq/tilt give nothing:
F2 medians p232/p227/p226 = 1809/2433/2318 Hz (range 624 Hz) vs an f0 range of
~4 Hz; F1 = 471/791/530 Hz (range 320 Hz). The 4-D print discards this because it
collapses the whole tract to one VTL scalar (uniform formant scale).

THE BUILD (new owned-DSP primitive, NO net/fit/gradient/loss/sweep):
  RECOVER  — per speaker, the median F1,F2,F3 + bandwidths over voiced frames, and
             the per-formant RATIO to the population reference (his tract SHAPE),
             AND a uniform-VTL scalar from the geometric-mean formant offset (kept
             separate so the SHAPE warp does not double-count VTL).
  RENDER   — `lpc_formant_warp_track` (audio_primitives.rs, APPENDED): roots each
             content LPC frame, MULTIPLIES the first 3 in-band formant-pole angles
             by the speaker's per-formant ratio (shifts the content's formants to
             the speaker's tract SHAPE while preserving their MOTION = words), and
             blends each pole radius toward the speaker's target bandwidth. Then
             re-forms the polynomial. The held excitation (f0/oq/tilt) + uniform
             VTL resample are UNCHANGED — apples-to-apples with v3, the warp is the
             one addition.

VALIDATIONS (numbers, not boolean):
  (a) WITHIN-REGISTER DISCRIMINABILITY — does the recovered tract signature SPREAD
      the co-located males where the source print gave ~none? Per-speaker values.
  (b) END-TO-END — full identity (now N-D incl. the tract cue) vs 2/8; MALES-RESOLVE
      vs 1/3 (do male->male mis-lands drop?); per-sub-print identity; factor sep.
  (c) SPEAKER-not-CONTENT control (the rendered formant signature tracks the
      SPEAKER across different content donors, not the donor) + INTELLIGIBILITY
      preserved + RINGING ~0 (synthesis not regressed). WAVs 24-bit/48k.
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict

import numpy as np
import soundfile as sf

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs._native as N
from domains.voice_impressionist import recover_voice_code_v3

CORPUS = "/tmp/vctk48/corpus"
OUT = "/tmp/voice_imp48k_v4"
os.makedirs(OUT, exist_ok=True)

FS = 48000
ORDER = 36
FRAME = 1200
HOP = 480
PE = 0.97
BW_FLOOR_HZ = 80.0
AM = 0.7
F0_CEIL = 290.0
YIN_VOICING = 0.10

# tract-shape warp knobs
N_FORMANT = 3           # warp F1..F3 (the resolvable, speaker-idiosyncratic ones)
WARP_FLO = 200.0        # formant search band for the warp (skip f0 pole)
WARP_FHI = 3800.0
BW_ALPHA = 0.6          # bandwidth blend toward speaker target
F_LO_FMT, F_HI_FMT = 150.0, 4000.0
BW_MAX = 700.0

SPEAKERS = ["p232", "p227", "p226", "p231", "p225", "p230", "p233", "p228"]
F0_PROBE = {"p232": 126, "p227": 132, "p226": 153, "p231": 199,
            "p225": 181, "p230": 210, "p233": 224, "p228": 225}
MALES = ["p232", "p227", "p226"]


# ======================================================================
#  corpus + io
# ======================================================================
def build_index():
    idx = defaultdict(dict)
    for fn in sorted(os.listdir(CORPUS)):
        if not fn.endswith(".wav"):
            continue
        spk, tid = fn[:-4].split("_t")
        idx[spk][tid] = os.path.join(CORPUS, fn)
    return idx


def load(path):
    x, fs = sf.read(path, dtype="float32")
    if x.ndim > 1:
        x = x.mean(1)
    return fs, np.asarray(x, dtype=np.float32)


def write_wav24(path, x, sr=FS):
    y = np.clip(np.asarray(x, dtype=np.float32), -1.0, 1.0)
    sf.write(path, y, sr, subtype="PCM_24")


def erb_centres(n=48, lo=120.0, hi=18000.0):
    hz2erb = lambda f: 21.4 * np.log10(4.37e-3 * f + 1.0)
    erb2hz = lambda e: (10 ** (e / 21.4) - 1.0) / 4.37e-3
    e = np.linspace(hz2erb(lo), hz2erb(hi), n)
    return [float(erb2hz(v)) for v in e]


CENTRES = erb_centres()


def cochleagram(x, sr, win=960, hop=480):
    bands = []
    for fc in CENTRES:
        env = np.abs(np.array(N.gammatone_band(x.tolist(), sr, fc, 4), dtype=np.float32))
        bands.append(env)
    bands = np.stack(bands, 0)
    T = bands.shape[1]
    frames, pos = [], 0
    while pos + win <= T:
        frames.append(10.0 * np.log10(bands[:, pos:pos + win].mean(axis=1) + 1e-6))
        pos += hop
    return np.stack(frames, 0) if frames else np.zeros((1, len(CENTRES)))


def resample_linear(x, ratio):
    n = len(x)
    if abs(ratio - 1.0) < 1e-3 or n < 2:
        return np.asarray(x, dtype=np.float32)
    m = max(2, int(round(n / ratio)))
    xi = np.linspace(0, n - 1, m)
    return np.interp(xi, np.arange(n), x).astype(np.float32)


def time_norm_cochlea(x, sr, L=16):
    c = cochleagram(x, sr)
    if c.shape[0] < 2:
        return None
    i = np.linspace(0, c.shape[0] - 1, L).round().astype(int)
    return c[i]


# ======================================================================
#  recovery — f0 track / level / TRACT SIGNATURE
# ======================================================================
def f0_track_of(x, sr):
    """Per-hop f0 track for the SYNTHESIS excitation (unchanged from v3)."""
    f0t, pos = [], 0
    while pos + FRAME <= len(x):
        f = N.f0_autocorr(x[pos:pos + FRAME].tolist(), sr, 70.0, 300.0, 0.45)
        f0t.append(f if f > 0 else 0.0)
        pos += HOP
    return f0t if f0t else [0.0]


def formant_log_level(x, sr):
    levels, pos = [], 0
    while pos + FRAME <= len(x):
        fbw = N.lpc_formants_bw(x[pos:pos + FRAME].tolist(), sr, ORDER, PE, 150.0, 4000.0, 700.0)
        if len(fbw) >= 6:
            levels.append(float(np.mean(np.log(np.asarray(fbw[0::2][:3]) + 1e-9))))
        pos += HOP
    return float(np.median(levels)) if levels else None


def tract_signature(x, sr):
    """Recover the speaker's median F1,F2,F3 and B1,B2,B3 over VOICED frames — the
    tract-geometry signature. Pure owned DSP (lpc_formants_bw), median selection."""
    F = [[], [], []]
    B = [[], [], []]
    pos = 0
    while pos + FRAME <= len(x):
        fr = x[pos:pos + FRAME]
        f0 = N.f0_yin(fr.tolist(), sr, 70.0, F0_CEIL, YIN_VOICING)
        if 0 < f0 < F0_CEIL * 0.97:
            fbw = N.lpc_formants_bw(fr.tolist(), sr, ORDER, PE, F_LO_FMT, F_HI_FMT, BW_MAX)
            ff = fbw[0::2]
            bb = fbw[1::2]
            if len(ff) >= 3:
                for k in range(3):
                    F[k].append(ff[k])
                    B[k].append(bb[k])
        pos += HOP
    if not F[0]:
        return None
    Fmed = np.array([float(np.median(F[k])) for k in range(3)])
    Bmed = np.array([float(np.median(B[k])) for k in range(3)])
    return Fmed, Bmed


# ======================================================================
#  render — the SOLVED 48k synthesis + the ONE addition: tract-shape warp
# ======================================================================
def render_held_voice(content_file, code, vtl_render, freq_ratio, targ_bw):
    """IDENTICAL render to v3 EXCEPT: after bandwidth-expansion, the content LPC
    track is WARPED toward the speaker's per-formant tract signature
    (`lpc_formant_warp_track`). freq_ratio/targ_bw len-3; pass None to disable
    (the v3 baseline)."""
    sr, xc = load(content_file)
    vtl = float(np.clip(vtl_render, 0.7, 1.45))
    xw = resample_linear(xc, vtl)
    a_track = N.lpc_coeff_track(xw.tolist(), ORDER, FRAME, HOP, PE)
    res = np.array(N.lpc_residual_track(xw.tolist(), ORDER, FRAME, HOP, PE), dtype=np.float32)
    f0t = f0_track_of(xw, sr)
    a_track = N.lpc_bw_expand_track(a_track, ORDER, sr, BW_FLOOR_HZ)
    if freq_ratio is not None:
        # The content was resampled by `vtl` (uniform tract scale), so its formants
        # sit at content_F/vtl. freq_ratio is the speaker's per-formant SHAPE vs the
        # population reference; the uniform VTL is already applied by resampling, so
        # the warp imprints only the residual SHAPE (no double-count).
        a_track = N.lpc_formant_warp_track(
            a_track, ORDER, sr,
            [float(r) for r in freq_ratio], [float(b) for b in targ_bw],
            N_FORMANT, BW_ALPHA, WARP_FLO, WARP_FHI)
    exc = np.array(
        N.lf_excitation_transplant(res.tolist(), f0t, HOP, sr,
                                   float(code.f0_hz) * vtl, float(code.oq),
                                   float(code.ta_frac), AM),
        dtype=np.float32)
    yw = np.array(N.lpc_cross_resynth(a_track, exc.tolist(), ORDER, HOP, PE), dtype=np.float32)
    y = resample_linear(yw, 1.0 / vtl)
    if len(y) > len(xc):
        y = y[:len(xc)]
    elif len(y) < len(xc):
        y = np.concatenate([y, np.zeros(len(xc) - len(y), dtype=np.float32)])
    peak = float(np.max(np.abs(y))) if y.size else 0.0
    if peak > 1.0:
        y = y / peak
    return sr, y


def clean_f0_yin(x, sr):
    f0s, pos = [], 0
    while pos + FRAME <= len(x):
        f = N.f0_yin(x[pos:pos + FRAME].tolist(), sr, 70.0, F0_CEIL, YIN_VOICING)
        if 0 < f < F0_CEIL * 0.97:
            f0s.append(f)
        pos += HOP
    return float(np.median(f0s)) if f0s else 0.0


def signal_source_vector_v3(x, sr):
    """The v3 4-D SOURCE print [log f0, oq, tilt, level] — UNCHANGED."""
    f0s, oqs, tilts, pos = [], [], [], 0
    while pos + FRAME <= len(x):
        fr = x[pos:pos + FRAME]
        f0 = N.f0_yin(fr.tolist(), sr, 70.0, F0_CEIL, YIN_VOICING)
        if 0 < f0 < F0_CEIL * 0.97:
            g = N.glottal_inverse_iaif(fr.tolist(), sr, f0)
            f0s.append(f0); oqs.append(g[0]); tilts.append(g[2])
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


def signal_full_vector(x, sr):
    """The v4 N-D print = the v3 4-D SOURCE print AUGMENTED with the within-register
    TRACT signature: [log f0, oq, tilt, level, logF1, logF2, logF3, logB1, logB2,
    logB3]. The tract dims are the cue that survives f0 overlap."""
    src = signal_source_vector_v3(x, sr)
    if src is None:
        return None
    sig = tract_signature(x, sr)
    if sig is None:
        return None
    Fmed, Bmed = sig
    tract = np.log(np.concatenate([Fmed, Bmed]) + 1e-9)
    return np.concatenate([src, tract])


# ======================================================================
#  (a) WITHIN-REGISTER DISCRIMINABILITY
# ======================================================================
def discriminability(prints, dims, names, group):
    """Min pairwise distance (z-scored) within `group` over `dims` — the margin the
    cue gives. Returns (min_margin, mean_margin, per-pair)."""
    P = np.stack([prints[s][dims] for s in group], 0)
    mu, sd = P.mean(0), P.std(0) + 1e-9
    Z = (P - mu) / sd
    pairs = []
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            d = float(np.linalg.norm(Z[i] - Z[j]))
            pairs.append((group[i], group[j], d))
    ds = [p[2] for p in pairs]
    return min(ds), float(np.mean(ds)), pairs


def main():
    print("=" * 74)
    print("WITHIN-REGISTER TRACT-SHAPE RESOLVER — does a per-formant tract")
    print("signature separate same-register males the 4-D source print cannot?")
    print("  NEW primitive: lpc_formant_warp_track (per-formant angle warp + bw blend)")
    print("=" * 74)

    idx = build_index()
    shared = sorted(set.intersection(*[set(idx[s].keys()) for s in SPEAKERS]))
    SAMPLE_TIDS = shared[:3]
    HELD_TIDS = shared[3:]
    AUD = HELD_TIDS[0]
    print(f"  sample tids={SAMPLE_TIDS}  held tids={HELD_TIDS}")

    # ---- recover code + tract signature per speaker ----
    codes, spk_level, sigF, sigB = {}, {}, {}, {}
    for spk in SPEAKERS:
        samp = np.concatenate([load(idx[spk][t])[1] for t in SAMPLE_TIDS])
        code = recover_voice_code_v3(samp, FS, order=ORDER, frame=FRAME, hop=HOP,
                                     pre_emph=PE, f0_ceil=F0_CEIL)
        cf = clean_f0_yin(samp, FS)
        if cf > 0:
            code.f0_hz = cf
        codes[spk] = code
        spk_level[spk] = formant_log_level(samp, FS) or 6.7
        Fmed, Bmed = tract_signature(samp, FS)
        sigF[spk] = Fmed
        sigB[spk] = Bmed

    # population reference formants (shared) -> per-speaker formant-SHAPE ratio.
    refF = np.median(np.stack([sigF[s] for s in SPEAKERS], 0), axis=0)
    # uniform geometric-mean offset per speaker = the VTL component; remove it from
    # the ratio so the warp carries only the residual SHAPE (VTL is applied by the
    # render's resample, not double-counted).
    ratio = {}
    for s in SPEAKERS:
        raw = sigF[s] / refF                          # full per-formant offset
        gmean = float(np.exp(np.mean(np.log(raw))))   # the uniform (VTL) part
        ratio[s] = raw / gmean                         # residual SHAPE (gmean=1)

    print("\n" + "=" * 74)
    print("(a) WITHIN-REGISTER DISCRIMINABILITY — recovered TRACT signature")
    print("    (the cue that must SPREAD the co-located males; source print gave ~0)")
    print("=" * 74)
    print("  per-speaker recovered tract signature:")
    print("   spk  probe  F1    F2    F3   | B1   B2   B3  | SHAPE ratio F1/F2/F3")
    for s in SPEAKERS:
        tag = "M" if s in MALES else "F"
        print(f"   {s}{tag} {F0_PROBE[s]:4d}  {sigF[s][0]:4.0f}  {sigF[s][1]:4.0f}  "
              f"{sigF[s][2]:4.0f} | {sigB[s][0]:3.0f}  {sigB[s][1]:3.0f}  {sigB[s][2]:3.0f} | "
              f"{ratio[s][0]:.3f} {ratio[s][1]:.3f} {ratio[s][2]:.3f}")

    # source-print vs tract-cue discriminability ON THE MALES (the key contrast).
    src_prints = {s: signal_source_vector_v3(
        np.concatenate([load(idx[s][t])[1] for t in SAMPLE_TIDS]), FS) for s in SPEAKERS}
    tract_prints = {s: np.log(np.concatenate([sigF[s], sigB[s]]) + 1e-9) for s in SPEAKERS}
    # z-scored full prints for distances
    src4 = {s: src_prints[s] for s in SPEAKERS}

    src_min, src_mean, src_pairs = discriminability(src4, [0, 1, 2, 3], None, MALES)
    tr_min, tr_mean, tr_pairs = discriminability(tract_prints, list(range(6)), None, MALES)
    # formant-only (no bw) too
    trf_min, trf_mean, trf_pairs = discriminability(tract_prints, [0, 1, 2], None, MALES)
    print("\n  MALE within-register margins (z-scored pairwise distance):")
    print(f"    4-D SOURCE print  [f0,oq,tilt,level] : min {src_min:.3f}  mean {src_mean:.3f}")
    for a, b, d in src_pairs:
        print(f"        {a}-{b}: {d:.3f}")
    print(f"    TRACT signature   [F1..3,B1..3]      : min {tr_min:.3f}  mean {tr_mean:.3f}")
    for a, b, d in tr_pairs:
        print(f"        {a}-{b}: {d:.3f}")
    print(f"    TRACT formants only [F1,F2,F3]       : min {trf_min:.3f}  mean {trf_mean:.3f}")
    # raw Hz spreads, the human-legible version
    mF = np.stack([sigF[s] for s in MALES], 0)
    print(f"\n  MALE raw formant spread: F1 {np.ptp(mF[:,0]):.0f}Hz  F2 {np.ptp(mF[:,1]):.0f}Hz  "
          f"F3 {np.ptp(mF[:,2]):.0f}Hz   (vs f0 range ~4 Hz from f0_resolver)")

    # ---- prints over the full corpus for identity ----
    print("\n" + "=" * 74)
    print("(b) END-TO-END HELD-VOICE IMPRESSION — N-D print incl. tract cue (vs 2/8)")
    print("    donor = farthest-f0 speaker; warp imprints the held speaker's tract shape")
    print("=" * 74)

    # reference prints = real speaker N-D prints over held tids (held-out from sample).
    raw_prints = {}
    for s in SPEAKERS:
        vecs = []
        for tid in HELD_TIDS:
            v = signal_full_vector(load(idx[s][tid])[1], FS)
            if v is not None:
                vecs.append(v)
        raw_prints[s] = np.median(np.stack(vecs, 0), axis=0) if vecs else None
    P = np.stack([raw_prints[s] for s in SPEAKERS], 0)
    mu, sd = P.mean(0), P.std(0) + 1e-9
    ref_prints = {s: (raw_prints[s] - mu) / sd for s in SPEAKERS}

    def donor_for(S):
        return max((s for s in SPEAKERS if s != S),
                   key=lambda b: abs(F0_PROBE[b] - F0_PROBE[S]))

    def vtl_for(S, donor):
        return float(np.exp(spk_level[S] - spk_level[donor]))

    rv_cache = {}
    correct = 0
    male_set = set(MALES)
    male_to_male = 0
    for S in SPEAKERS:
        donor = donor_for(S)
        vecs = []
        for tid in HELD_TIDS:
            sr, y = render_held_voice(idx[donor][tid], codes[S], vtl_for(S, donor),
                                      ratio[S], sigB[S])
            if tid == AUD:
                write_wav24(f"{OUT}/held_{S}_says_t{tid}_donor_{donor}.wav", y, sr)
            v = signal_full_vector(y, sr)
            if v is not None:
                vecs.append(v)
        rv = np.median(np.stack(vecs, 0), axis=0) if vecs else mu.copy()
        rvz = (rv - mu) / sd
        rv_cache[S] = (rv, rvz)
        dists = {s: float(np.linalg.norm(rvz - ref_prints[s])) for s in SPEAKERS}
        nearest = min(dists, key=dists.get)
        rank = sorted(dists.items(), key=lambda kv: kv[1])
        ok = nearest == S
        correct += ok
        if S in male_set and not ok and nearest in male_set:
            male_to_male += 1
        print(f"  {'OK ' if ok else 'XX '}render({S},donor={donor}) -> "
              f"nearest={nearest}  " + " < ".join(f"{s}:{d:.2f}" for s, d in rank[:3]))

    print(f"\n  IDENTITY (full N-D print): {correct}/{len(SPEAKERS)}  "
          f"(chance {1.0/len(SPEAKERS):.2f})  [v3 4-D was 2/8]")
    male_correct = sum(
        1 for S in MALES
        if min({s: float(np.linalg.norm(rv_cache[S][1] - ref_prints[s])) for s in SPEAKERS},
               key=lambda s: float(np.linalg.norm(rv_cache[S][1] - ref_prints[s]))) == S)
    print(f"  MALE resolution: {male_correct}/3 males identify to self; "
          f"male->male mis-lands {male_to_male} (v3: 1/3, mis 2)")

    SRC_DIMS = [0, 1, 2, 3]
    TRACT_DIMS = [4, 5, 6, 7, 8, 9]
    FMT_DIMS = [4, 5, 6]
    for dims, name in [(SRC_DIMS, "4-D source (v3 print)"),
                       (FMT_DIMS, "tract formants F1..3"),
                       (TRACT_DIMS, "tract sig F1..3+B1..3"),
                       (list(range(10)), "full N-D")]:
        c = 0
        for S in SPEAKERS:
            rz = rv_cache[S][1][dims]
            dd = {b: float(np.linalg.norm(rz - ref_prints[b][dims])) for b in SPEAKERS}
            c += (min(dd, key=dd.get) == S)
        print(f"    IDENTITY [{name}]: {c}/{len(SPEAKERS)}")

    sep_hits = sep_tot = 0
    for S in SPEAKERS:
        rvz = rv_cache[S][1]
        dS = np.linalg.norm(rvz - ref_prints[S])
        for B in SPEAKERS:
            if B == S:
                continue
            sep_tot += 1
            sep_hits += dS < np.linalg.norm(rvz - ref_prints[B])
    print(f"  FACTOR SEPARATION (render closer to self than to B): "
          f"{sep_hits}/{sep_tot} ({100.0*sep_hits/max(1,sep_tot):.1f}%; chance 50%)")

    # ringing: rendered f0 vs code f0
    f0e = []
    for S in SPEAKERS:
        rf = float(np.exp(rv_cache[S][0][0]))
        f0e.append(100.0 * abs(rf - float(codes[S].f0_hz)) / float(codes[S].f0_hz))
    print(f"  RINGING (mean |render-f0 - code-f0|): {np.mean(f0e):.1f}%  (v3 0.2%)")

    # ===================================================================
    # (c) SPEAKER-not-CONTENT control + intelligibility
    # ===================================================================
    print("\n" + "=" * 74)
    print("(c) SPEAKER-not-CONTENT control — does the RENDERED formant signature")
    print("    track the SPEAKER (not the content donor)?")
    print("=" * 74)
    # render the SAME held speaker through TWO different content donors; the
    # recovered tract signature of the render should match the SPEAKER, and the
    # cross-donor variation should be << cross-speaker variation.
    test_speakers = MALES + ["p225"]
    donor_pair = ["p233", "p228"]  # two female donors (very different content tracts)
    within_spk, across_spk = [], []
    sig_by_render = {}
    for S in test_speakers:
        sigs = []
        for donor in donor_pair:
            vecs = []
            for tid in HELD_TIDS[:2]:
                sr, y = render_held_voice(idx[donor][tid], codes[S], vtl_for(S, donor),
                                          ratio[S], sigB[S])
                sg = tract_signature(y, sr)
                if sg is not None:
                    vecs.append(np.log(np.concatenate(sg) + 1e-9))
            if vecs:
                sigs.append(np.median(np.stack(vecs, 0), 0))
        if len(sigs) == 2:
            within_spk.append(float(np.linalg.norm(sigs[0] - sigs[1])))
            sig_by_render[S] = np.median(np.stack(sigs, 0), 0)
        print(f"  {S}: render-tract-sig via donor {donor_pair[0]} vs {donor_pair[1]} "
              f"-> within-speaker cross-donor dist = "
              f"{within_spk[-1] if within_spk else float('nan'):.3f}")
    # across-speaker distance (same donor): how far apart different speakers render.
    keys = list(sig_by_render)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            across_spk.append(float(np.linalg.norm(sig_by_render[keys[i]] - sig_by_render[keys[j]])))
    wm = float(np.mean(within_spk)) if within_spk else float("nan")
    am_ = float(np.mean(across_spk)) if across_spk else float("nan")
    print(f"\n  CROSS-DONOR (same speaker) mean dist : {wm:.3f}")
    print(f"  CROSS-SPEAKER (rendered)   mean dist : {am_:.3f}")
    print(f"  RATIO across/within = {am_/max(wm,1e-9):.2f}  "
          f"(>>1 => the rendered tract cue tracks the SPEAKER, not the content donor)")

    print("\n" + "=" * 74)
    print("(c) INTELLIGIBILITY — rendered sentence preserves the donor's words?")
    print("=" * 74)
    intel = []
    for S in SPEAKERS:
        donor = donor_for(S)
        cs = []
        for tid in HELD_TIDS:
            sr, y = render_held_voice(idx[donor][tid], codes[S], vtl_for(S, donor),
                                      ratio[S], sigB[S])
            _, xc = load(idx[donor][tid])
            ty, tx = time_norm_cochlea(y, sr), time_norm_cochlea(xc, sr)
            if ty is None or tx is None:
                continue
            a, b = ty.ravel(), tx.ravel()
            cs.append(float(np.corrcoef(a, b)[0, 1]) if a.std() > 0 and b.std() > 0 else 0.0)
        mc = float(np.mean(cs)) if cs else 0.0
        intel.append(mc)
        print(f"  {S}: rendered-vs-raw-content cochlea corr = {mc:.3f}")
    intel_mean = float(np.mean(intel))
    print(f"\n  INTELLIGIBILITY (mean cochlea corr): {intel_mean:.3f}  (v3 0.957)")

    # also: intelligibility WITHOUT the warp (baseline) to show the warp's cost.
    intel_nowarp = []
    for S in SPEAKERS:
        donor = donor_for(S)
        cs = []
        for tid in HELD_TIDS:
            sr, y = render_held_voice(idx[donor][tid], codes[S], vtl_for(S, donor), None, None)
            _, xc = load(idx[donor][tid])
            ty, tx = time_norm_cochlea(y, sr), time_norm_cochlea(xc, sr)
            if ty is None or tx is None:
                continue
            a, b = ty.ravel(), tx.ravel()
            cs.append(float(np.corrcoef(a, b)[0, 1]) if a.std() > 0 and b.std() > 0 else 0.0)
        if cs:
            intel_nowarp.append(float(np.mean(cs)))
    intel_nowarp_mean = float(np.mean(intel_nowarp)) if intel_nowarp else float("nan")
    print(f"  INTELLIGIBILITY (no-warp v3 baseline): {intel_nowarp_mean:.3f}  "
          f"(warp cost = {intel_nowarp_mean - intel_mean:+.3f})")

    # ---- reference / content WAVs for by-ear audition ----
    for S in SPEAKERS:
        rf = idx[S].get(AUD)
        if rf:
            _, xr = load(rf)
            write_wav24(f"{OUT}/REAL_{S}_t{AUD}.wav", xr, FS)
    for S in SPEAKERS[:2]:
        donor = donor_for(S)
        _, xc = load(idx[donor][AUD])
        write_wav24(f"{OUT}/CONTENT_donor_{donor}_t{AUD}.wav", xc, FS)
    # also write the three males rendered through the SAME donor for direct A/B.
    common_donor = "p228"
    for S in MALES:
        sr, y = render_held_voice(idx[common_donor][AUD], codes[S], vtl_for(S, common_donor),
                                  ratio[S], sigB[S])
        write_wav24(f"{OUT}/AB_male_{S}_donor_{common_donor}_t{AUD}.wav", y, sr)
    print(f"\n  WAVs (24-bit/48k) -> {OUT}/  (held_*, REAL_*, CONTENT_*, AB_male_*)")

    print("\n" + "=" * 74)
    print("VERDICT NUMBERS:")
    print(f"  (a) within-register MALE margin: TRACT min {tr_min:.3f} vs SOURCE min {src_min:.3f} "
          f"(formants F2 spread {np.ptp(mF[:,1]):.0f}Hz vs f0 ~4Hz)")
    print(f"  (b) identity[full N-D] {correct}/{len(SPEAKERS)} (v3 4-D 2/8); "
          f"males-resolve {male_correct}/3 (v3 1/3); male->male mis {male_to_male} (v3 2); "
          f"factor-sep {100.0*sep_hits/max(1,sep_tot):.1f}%")
    print(f"  (c) speaker-not-content across/within ratio {am_/max(wm,1e-9):.2f}; "
          f"intelligibility {intel_mean:.3f} (v3 0.957); ringing {np.mean(f0e):.1f}%")
    print("===MARKER_WITHIN_REGISTER_COMPLETE===")


if __name__ == "__main__":
    main()
