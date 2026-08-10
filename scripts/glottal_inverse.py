#!/usr/bin/env python3
"""Genuine glottal-inverse validation — does the ANALYSIS fix resolve voice identity?

WORLD ADAPTER ONLY. Swaps the SATURATING source/f0 recovery
(`glottal_params_from_residual` + plain `f0_autocorr`) for the genuine glottal
inverse (`glottal_inverse_iaif` = IAIF + closed-phase covariance LPC + GCI) and
the spread-preserving cepstral f0 (`f0_cepstral`) — and re-runs the SOLVED 48 kHz
held-voice synthesis UNCHANGED (lf_excitation_transplant + lpc_bw_expand_track +
lpc_cross_resynth). Apples-to-apples with voice_impression_48k.py: only the
recovery is swapped (recover_voice_code -> recover_voice_code_v2 + the v2 source/
f0 print). NO net, NO .fit, NO gradient, NO loss, NO sweep. CortexLoop untouched.

The 48 kHz diagnosis (docs/voice_48k.md): synthesis solved (ringing 15-25%->0.4%,
oq/tilt carried in the excitation), but held-voice identity 1/8 = CHANCE because
the ANALYSIS saturated — inject oq 0.45->0.90 all read back 0.300, f0 lost its
spread, so every speaker's recovered code is near-identical -> every render
collapses to one voice. This script tests whether the genuine inverse resolves it.

VALIDATIONS:
  (a) ANALYSIS INJECTION CONTROL — synthesize voices with KNOWN oq/tilt/f0 (LF
      pulse train through a fixed synthetic tract), run the new estimator: does it
      RECOVER the injected values (oq 0.4->0.9 read back across the range, NOT
      pinned at 0.30; f0 exact)? Isolates the estimator from the corpus.
  (b) REAL VCTK 48k — recovered oq/tilt/f0 SPREAD across the 8 f0-spread speakers
      (vs the collapsed oq 0.729-0.750 / clustered f0).
  (c) END-TO-END impression — plug into the 48k harness (solved synthesis), re-run
      held-voice: FULL 4-D identity vs 1/8, f0-identity, factor separation. WAVs
      24-bit/48k to /tmp/voice_imp48k_v2/.
  (d) INTELLIGIBILITY preserved.
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
from domains.voice_impressionist import recover_voice_code_v2

CORPUS = "/tmp/vctk48/corpus"
OUT = "/tmp/voice_imp48k_v2"
os.makedirs(OUT, exist_ok=True)

# ---- 48 kHz constants (identical to voice_impression_48k.py) ----------------
FS = 48000
ORDER = 36
FRAME = 1200          # 25 ms @ 48 kHz
HOP = 480             # 10 ms
PE = 0.97
BW_FLOOR_HZ = 80.0
AM = 0.7
F0_CEIL = 290.0

SPEAKERS = ["p232", "p227", "p226", "p231", "p225", "p230", "p233", "p228"]
F0_PROBE = {"p232": 126, "p227": 132, "p226": 153, "p231": 199,
            "p225": 181, "p230": 210, "p233": 224, "p228": 225}


# ======================================================================
#  (a) ANALYSIS INJECTION CONTROL — known oq/tilt/f0 in, estimator out
# ======================================================================
def synth_known(oq, ta, f0, dur=0.8):
    """Synthesize a voiced signal with KNOWN source (oq, ta) + f0 through a FIXED
    synthetic 3-formant vocal tract (F1=600, F2=1500, F3=2500 Hz). The source is
    the owned LF glottal pulse train (lf_excitation_transplant at the known oq/ta/
    f0, flat energy envelope); the tract is a cascade of 2-pole resonators. This is
    the forward source-filter model run with KNOWN parameters, so the estimator's
    read-back can be compared to ground truth — isolating the estimator from any
    corpus confound."""
    n = int(FS * dur)
    res = np.ones(n, dtype=np.float32)               # flat energy envelope
    f0t = [float(f0)] * (n // HOP)
    exc = np.array(
        N.lf_excitation_transplant(res.tolist(), f0t, HOP, FS,
                                   float(f0), float(oq), float(ta), AM),
        dtype=np.float32)
    y = exc.copy()
    for fc, bw in [(600.0, 80.0), (1500.0, 100.0), (2500.0, 120.0)]:
        r = np.exp(-np.pi * bw / FS)
        th = 2 * np.pi * fc / FS
        a1 = -2 * r * np.cos(th)
        a2 = r * r
        out = np.zeros_like(y)
        for i in range(len(y)):
            out[i] = y[i] - a1 * (out[i - 1] if i > 0 else 0.0) - a2 * (out[i - 2] if i > 1 else 0.0)
        y = out / (np.max(np.abs(out)) + 1e-9)
    return y.astype(np.float32)


def estimate_source(y):
    """Run BOTH estimators frame-wise; return medians for old vs new oq/ta/tilt."""
    old_oq, new_oq, new_ta, new_tilt = [], [], [], []
    for st in range(0, len(y) - FRAME, HOP):
        fr = y[st:st + FRAME].tolist()
        f0 = N.f0_autocorr(fr, FS, 70.0, F0_CEIL, 0.4)
        if f0 <= 0:
            continue
        res = N.lpc_residual(fr, ORDER, PE)
        old_oq.append(N.glottal_params_from_residual(res, FS, f0)[0])
        g = N.glottal_inverse_iaif(fr, FS, f0)
        new_oq.append(g[0]); new_ta.append(g[1]); new_tilt.append(g[2])
    med = lambda v: float(np.median(v)) if v else float("nan")
    return med(old_oq), med(new_oq), med(new_ta), med(new_tilt)


def estimate_f0(y):
    ac, ce = [], []
    for st in range(0, len(y) - FRAME, HOP):
        fr = y[st:st + FRAME].tolist()
        a = N.f0_autocorr(fr, FS, 70.0, 400.0, 0.3)   # OLD gate (16 kHz-tuned)
        c = N.f0_cepstral(fr, FS, 70.0, F0_CEIL, 0.3)
        if a > 0:
            ac.append(a)
        if c > 0:
            ce.append(c)
    med = lambda v: float(np.median(v)) if v else float("nan")
    return med(ac), med(ce)


def injection_control():
    print("\n" + "=" * 74)
    print("(a) ANALYSIS INJECTION CONTROL — known oq/tilt/f0 -> estimator read-back")
    print("    (LF source @ known oq/ta/f0 through a fixed 3-formant tract)")
    print("=" * 74)
    print("\n  OQ recovery (f0=140 Hz, ta=0.02):")
    print("    inj_oq | OLD (saturating) | NEW (glottal inverse) | new_ta | new_tilt")
    oq_inj, oq_new = [], []
    for oq in [0.40, 0.50, 0.60, 0.70, 0.80, 0.90]:
        old, new, ta, tilt = estimate_source(synth_known(oq, 0.02, 140.0))
        oq_inj.append(oq); oq_new.append(new)
        print(f"     {oq:.2f}  |      {old:.3f}      |       {new:.3f}         "
              f"| {ta:.4f}| {tilt:+.1f}")
    r = float(np.corrcoef(oq_inj, oq_new)[0, 1])
    print(f"    OQ inj-vs-recovered Pearson r = {r:+.3f}  "
          f"(saturating estimator: r=nan / flat 0.300)")

    print("\n  TILT recovery (oq=0.6, f0=140 Hz, varying ta):")
    print("    inj_ta | new_ta | new_tilt")
    for ta in [0.005, 0.02, 0.05, 0.10]:
        _, _, rta, tilt = estimate_source(synth_known(0.6, ta, 140.0))
        print(f"     {ta:.3f} | {rta:.4f}| {tilt:+.1f}")

    print("\n  F0 recovery (oq=0.6, ta=0.02):")
    print("    inj_f0 | autocorr | CEPSTRAL (spread-preserving)")
    for f0 in [110.0, 140.0, 180.0, 220.0, 260.0]:
        ac, ce = estimate_f0(synth_known(0.6, 0.02, f0))
        print(f"     {f0:.0f}  |  {ac:.1f}  |  {ce:.1f}")
    return r


# ======================================================================
#  corpus + 48 kHz harness (identical to voice_impression_48k.py)
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


def clean_f0_cep(x, sr):
    """Spread-preserving median f0 of a sample via the octave-robust cepstral
    estimator (drops ceiling-pinned failed reads). The v2 f0 recovery."""
    f0s, pos = [], 0
    while pos + FRAME <= len(x):
        f = N.f0_cepstral(x[pos:pos + FRAME].tolist(), sr, 70.0, F0_CEIL, 0.40)
        if 0 < f < F0_CEIL * 0.97:
            f0s.append(f)
        pos += HOP
    return float(np.median(f0s)) if f0s else 0.0


def f0_track_of(x, sr):
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


def render_held_voice(content_file, code, vtl_render=1.0):
    """IDENTICAL render to voice_impression_48k.py — the SOLVED synthesis, unchanged."""
    sr, xc = load(content_file)
    vtl = float(np.clip(vtl_render, 0.7, 1.45))
    xw = resample_linear(xc, vtl)
    a_track = N.lpc_coeff_track(xw.tolist(), ORDER, FRAME, HOP, PE)
    res = np.array(N.lpc_residual_track(xw.tolist(), ORDER, FRAME, HOP, PE), dtype=np.float32)
    f0t = f0_track_of(xw, sr)
    a_track = N.lpc_bw_expand_track(a_track, ORDER, sr, BW_FLOOR_HZ)
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


def signal_source_vector_v2(x, sr):
    """SOURCE-SENSITIVE speaker print [log f0, oq, tilt, level] read with the GENUINE
    glottal inverse + cepstral f0 (the v2 identity instrument)."""
    f0s, oqs, tilts, pos = [], [], [], 0
    while pos + FRAME <= len(x):
        fr = x[pos:pos + FRAME]
        f0 = N.f0_cepstral(fr.tolist(), sr, 70.0, F0_CEIL, 0.40)
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


def speaker_source_print(spk, sample_tids, idx, n=4):
    vecs = []
    for tid in idx[spk]:
        if tid in sample_tids:
            continue
        v = signal_source_vector_v2(load(idx[spk][tid])[1], FS)
        if v is not None:
            vecs.append(v)
        if len(vecs) >= n:
            break
    return np.median(np.stack(vecs, 0), axis=0) if vecs else None


def time_norm_cochlea(x, sr, L=16):
    c = cochleagram(x, sr)
    if c.shape[0] < 2:
        return None
    i = np.linspace(0, c.shape[0] - 1, L).round().astype(int)
    return c[i]


# ======================================================================
#  (b)+(c)+(d) on real VCTK
# ======================================================================
def real_vctk():
    idx = build_index()
    shared = sorted(set.intersection(*[set(idx[s].keys()) for s in SPEAKERS]))
    SAMPLE_TIDS = shared[:3]
    HELD_TIDS = shared[3:]
    AUD = HELD_TIDS[0]
    print("\n" + "=" * 74)
    print("(b) REAL VCTK 48k — recovered code SPREAD across speakers (v2 estimator)")
    print("=" * 74)
    print(f"  sample tids={SAMPLE_TIDS}  held tids={HELD_TIDS}")

    codes, spk_level = {}, {}
    for spk in SPEAKERS:
        samp = np.concatenate([load(idx[spk][t])[1] for t in SAMPLE_TIDS])
        code = recover_voice_code_v2(samp, FS, order=ORDER, frame=FRAME, hop=HOP,
                                     pre_emph=PE, f0_ceil=F0_CEIL)
        cf = clean_f0_cep(samp, FS)
        if cf > 0:
            code.f0_hz = cf
        codes[spk] = code
        spk_level[spk] = formant_log_level(samp, FS) or 6.7
        print(f"    code[{spk}] (probe f0~{F0_PROBE[spk]:3d}) "
              f"f0={code.f0_hz:5.1f}Hz  oq={code.oq:.3f}  ta={code.ta_frac:.4f}  "
              f"tilt={code.tilt_db:+.2f}  level={spk_level[spk]:.2f}")
    # spread summary
    oqv = np.array([codes[s].oq for s in SPEAKERS])
    f0v = np.array([codes[s].f0_hz for s in SPEAKERS])
    tiv = np.array([codes[s].tilt_db for s in SPEAKERS])
    print(f"\n  SPREAD: oq [{oqv.min():.3f}..{oqv.max():.3f}] range {np.ptp(oqv):.3f} "
          f"(48k v1 was 0.729-0.750 range 0.021)")
    print(f"          f0 [{f0v.min():.0f}..{f0v.max():.0f}] range {np.ptp(f0v):.0f} Hz "
          f"(probe spread 126-225 = 99 Hz)")
    print(f"          tilt [{tiv.min():+.2f}..{tiv.max():+.2f}] range {np.ptp(tiv):.2f}")
    # f0 recovery accuracy vs probe.
    f0_err = np.array([abs(codes[s].f0_hz - F0_PROBE[s]) / F0_PROBE[s] for s in SPEAKERS])
    print(f"          f0 vs probe: mean |err| {100*f0_err.mean():.1f}%  "
          f"(per-spk: " + ", ".join(f'{s}:{100*abs(codes[s].f0_hz-F0_PROBE[s])/F0_PROBE[s]:.0f}%' for s in SPEAKERS) + ")")

    # source prints (z-scored).
    raw = {s: speaker_source_print(s, SAMPLE_TIDS, idx) for s in SPEAKERS}
    P = np.stack([raw[s] for s in SPEAKERS], 0)
    mu, sd = P.mean(0), P.std(0) + 1e-9
    prints = {s: (raw[s] - mu) / sd for s in SPEAKERS}

    def donor_for(S):
        return max((s for s in SPEAKERS if s != S),
                   key=lambda b: abs(F0_PROBE[b] - F0_PROBE[S]))

    def vtl_for(S, donor):
        return float(np.exp(spk_level[S] - spk_level[donor]))

    print("\n" + "=" * 74)
    print("(c) END-TO-END HELD-VOICE IMPRESSION — full 4-D identity (vs 1/8 chance)")
    print("    (SOLVED 48k synthesis unchanged; donor = farthest-f0 speaker)")
    print("=" * 74)
    rv_cache, correct = {}, 0
    for S in SPEAKERS:
        donor = donor_for(S)
        vecs = []
        for tid in HELD_TIDS:
            sr, y = render_held_voice(idx[donor][tid], codes[S], vtl_render=vtl_for(S, donor))
            if tid == AUD:
                write_wav24(f"{OUT}/held_{S}_says_t{tid}_donor_{donor}.wav", y, sr)
            v = signal_source_vector_v2(y, sr)
            if v is not None:
                vecs.append(v)
        rv = np.median(np.stack(vecs, 0), axis=0) if vecs else mu.copy()
        rvz = (rv - mu) / sd
        rv_cache[S] = (rv, rvz)
        dists = {s: float(np.linalg.norm(rvz - prints[s])) for s in SPEAKERS}
        nearest = min(dists, key=dists.get)
        rank = sorted(dists.items(), key=lambda kv: kv[1])
        ok = nearest == S
        correct += ok
        print(f"  {'OK ' if ok else 'XX '}render({S} f0={codes[S].f0_hz:.0f},donor={donor}) "
              f"-> render_f0~{np.exp(rv[0]):.0f}  nearest={nearest}  "
              + " < ".join(f"{s}:{d:.2f}" for s, d in rank[:3]))
    print(f"\n  IDENTITY (full 4-D print): {correct}/{len(SPEAKERS)}  "
          f"(chance {1.0/len(SPEAKERS):.2f})  [48k v1 was 1/8]")

    for dims, name in [([0], "f0-only"), ([0, 3], "f0+level"),
                       ([1, 2], "oq+tilt (the recovered source cues)"),
                       ([0, 1, 2, 3], "full 4-D")]:
        c = 0
        for S in SPEAKERS:
            rz = rv_cache[S][1][dims]
            dd = {b: float(np.linalg.norm(rz - prints[b][dims])) for b in SPEAKERS}
            c += (min(dd, key=dd.get) == S)
        print(f"    IDENTITY [{name}]: {c}/{len(SPEAKERS)}")

    sep_hits = sep_tot = 0
    for S in SPEAKERS:
        rvz = rv_cache[S][1]
        dS = np.linalg.norm(rvz - prints[S])
        for B in SPEAKERS:
            if B == S:
                continue
            sep_tot += 1
            sep_hits += dS < np.linalg.norm(rvz - prints[B])
    print(f"  FACTOR SEPARATION (S-render closer to S than to B): "
          f"{sep_hits}/{sep_tot} ({100.0*sep_hits/max(1,sep_tot):.1f}%; chance 50%)")

    # f0-identity + ringing.
    id_f0, f0e = 0, []
    for S in SPEAKERS:
        rv = rv_cache[S][0]
        render_f0 = float(np.exp(rv[0])); code_f0 = float(codes[S].f0_hz)
        f0e.append(100.0 * abs(render_f0 - code_f0) / code_f0)
        rf = rv_cache[S][1][0]
        dd = {b: abs(rf - prints[b][0]) for b in SPEAKERS}
        id_f0 += (min(dd, key=dd.get) == S)
    print(f"  F0-IDENTITY: {id_f0}/{len(SPEAKERS)} (48k v1 was 3/8); "
          f"RINGING (mean |render-f0-code-f0|): {np.mean(f0e):.1f}% (v1 0.4%)")

    print("\n" + "=" * 74)
    print("(d) INTELLIGIBILITY — rendered sentence preserves the donor's words?")
    print("=" * 74)
    intel = []
    for S in SPEAKERS:
        donor = donor_for(S)
        cs = []
        for tid in HELD_TIDS:
            sr, y = render_held_voice(idx[donor][tid], codes[S], vtl_render=vtl_for(S, donor))
            _, xc = load(idx[donor][tid])
            ty, tx = time_norm_cochlea(y, sr), time_norm_cochlea(xc, sr)
            if ty is None or tx is None:
                continue
            a, b = ty.ravel(), tx.ravel()
            cs.append(float(np.corrcoef(a, b)[0, 1]) if a.std() > 0 and b.std() > 0 else 0.0)
        mc = float(np.mean(cs)) if cs else 0.0
        intel.append(mc)
        print(f"  {S}: rendered-vs-raw-content cochlea corr = {mc:.3f}")
    print(f"\n  INTELLIGIBILITY (mean cochlea corr): {np.mean(intel):.3f}  (v1 0.968)")

    # reference + audition WAVs (24-bit/48k).
    for S in SPEAKERS:
        rf = idx[S].get(AUD)
        if rf:
            _, xr = load(rf)
            write_wav24(f"{OUT}/REAL_{S}_t{AUD}.wav", xr, FS)
    for S in SPEAKERS[:2]:
        donor = donor_for(S)
        _, xc = load(idx[donor][AUD])
        write_wav24(f"{OUT}/CONTENT_donor_{donor}_t{AUD}.wav", xc, FS)
    print(f"\n  WAVs (24-bit/48k): {OUT}/held_*_says_t{AUD}_*.wav + REAL_*_t{AUD}.wav + CONTENT_*.wav")
    return correct, len(SPEAKERS), id_f0, float(np.mean(f0e)), float(np.mean(intel)), \
        np.ptp(oqv), np.ptp(f0v), 100.0 * sep_hits / max(1, sep_tot)


def main():
    print("=" * 74)
    print("GENUINE GLOTTAL INVERSE — does the ANALYSIS fix resolve voice identity?")
    print("  IAIF + closed-phase covariance LPC + GCI  +  spread-preserving cepstral f0")
    print("=" * 74)
    r = injection_control()
    correct, n, id_f0, ring, intel, oq_spread, f0_spread, sep = real_vctk()
    print("\n" + "=" * 74)
    print("VERDICT NUMBERS:")
    print(f"  (a) injection: OQ inj-vs-recovered r = {r:+.3f}  "
          f"(saturating estimator was FLAT 0.300)")
    print(f"  (b) real spread: oq range {oq_spread:.3f} (v1 0.021); f0 range {f0_spread:.0f} Hz")
    print(f"  (c) identity[full-4D] {correct}/{n} (v1 1/8); f0-id {id_f0}/{n} (v1 3/8); "
          f"factor-sep {sep:.1f}%")
    print(f"  (d) intelligibility {intel:.3f} (v1 0.968)")
    print("===MARKER_GLOTTAL_INVERSE_COMPLETE===")


if __name__ == "__main__":
    main()
