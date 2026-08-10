#!/usr/bin/env python3
"""SYNTH-SIDE F1/F2 CORRUPTION fix (v6) — close the analysis-by-synthesis loop in
the formant dims so the RENDERED formants/bandwidths RE-ANALYSE to the speaker's
REAL formant print, instead of being dropped as nuisance.

THE DIAGNOSIS (domain_gap.py v5, load-bearing): the 5-7/8 ceiling was
SYNTHESIS-limited. The rendered formants do NOT re-analyse to the speaker's real
formant print, so the within-register cue dims get DROPPED as nuisance:
  per-dim nuisance/signal  CORRUPTED: logF1 3.62  logF2 1.05  level 1.99
                                      logB2 1.69  logB3 1.36
                           CLEAN:     logf0 0.10  oq 0.63  tilt 0.91
                                      logF3 0.50  logB1 0.64
The within-register males can't fully resolve because the F1/F2 cue is smeared by
the forward model, not because real speakers overlap.

THE FIX (owned DSP, NO net/fit/gradient/loss/sweep-to-fit) — a deterministic
ANALYSIS-BY-SYNTHESIS formant correction. For each speaker:
  1. render -> re-analyse the rendered formants/bandwidths (lpc_formants_bw, the
     SAME analyser the real-frame compare uses).
  2. measure the DRIFT from the speaker's REAL formants (the measured ground truth
     per speaker — NOT the identity score).
  3. adjust the synthesis formant/bw TARGETS to compensate the drift
     (lpc_formant_set_track — new native primitive: SET each in-band formant pole
     to an absolute target Hz, vs the v5 ratio warp).
  4. iterate (damped fixed point, best-tracked) until the rendered formants
     re-analyse to the real formants -> the forward model HITS the target.
WHY F1/F2 drift worst (confirmed by probe): source-filter interaction at low f0.
A low-f0 male's strong low harmonics pull the rendered low formants down on
re-analysis, and a far-f0 (mismatched-register) content DONOR saturates the
reachable F2 (p227 F2 saturates at ~2375 through donor p228, but reaches 2432
through donor p231). So the loop also SELECTS the donor whose A-by-S residual to
the REAL formants is smallest — legit inverse-solving (ground = real formants).

DISCIPLINE: the A-by-S target and the donor selection are BOTH the speaker's
measured REAL formants (lpc_formants_bw over real recordings). Identity is NEVER
the selector — it is a CONSEQUENCE of the formants matching. A control renders
with the target-real-formants disabled (v5 ratio warp) and with a
target=score variant DISABLED-by-construction (no score touches the loop).

DONKEY: owned classical DSP only. New primitive lpc_formant_set_track appended to
audio_primitives.rs; py binding appended to py.rs. No foreign edits.
CortexLoop/solve_for_n.py untouched. Reuses the v5 render/recover/compare harness.
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
OUT = "/tmp/voice_imp48k_v6"
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

N_FORMANT = 3
WARP_FLO = 200.0
WARP_FHI = 3800.0
BW_ALPHA = 0.6
F_LO_FMT, F_HI_FMT = 150.0, 4000.0
BW_MAX = 700.0

# A-by-S fixed-point knobs (NOT tuned to identity — convergence of formants to the
# REAL formant ground truth; step is a damped inverse, best-tracked).
ABS_ITERS = 16
ABS_LAM = 0.6

SPEAKERS = ["p232", "p227", "p226", "p231", "p225", "p230", "p233", "p228"]
F0_PROBE = {"p232": 126, "p227": 132, "p226": 153, "p231": 199,
            "p225": 181, "p230": 210, "p233": 224, "p228": 225}
MALES = ["p232", "p227", "p226"]
DIMNAMES = ["logf0", "oq", "tilt", "level",
            "logF1", "logF2", "logF3", "logB1", "logB2", "logB3"]


# ======================================================================
#  io + corpus
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
#  recovery — f0 track / level / TRACT SIGNATURE / source print
# ======================================================================
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


def tract_signature(x, sr):
    """Median F1,F2,F3 + B1,B2,B3 over voiced frames — the SAME analyser used for
    the real-frame compare. This is what the A-by-S loop drives the render TO."""
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


def clean_f0_yin(x, sr):
    f0s, pos = [], 0
    while pos + FRAME <= len(x):
        f = N.f0_yin(x[pos:pos + FRAME].tolist(), sr, 70.0, F0_CEIL, YIN_VOICING)
        if 0 < f < F0_CEIL * 0.97:
            f0s.append(f)
        pos += HOP
    return float(np.median(f0s)) if f0s else 0.0


def signal_source_vector_v3(x, sr):
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
#  render — v5 synthesis, but the formant warp now SETS ABSOLUTE TARGETS
#  (lpc_formant_set_track) which the A-by-S loop drives. targ_f / targ_bw are in
#  the speaker's REAL (output) frame; the warp acts in the vtl-resampled frame so
#  we hand it targ/vtl. targ_f=None -> v5 ratio-warp baseline (for the control).
# ======================================================================
def render_voice(content_file, code, vtl_render, targ_f, targ_bw,
                 ratio_warp=None, ratio_bw=None):
    sr, xc = load(content_file)
    vtl = float(np.clip(vtl_render, 0.7, 1.45))
    xw = resample_linear(xc, vtl)
    a_track = N.lpc_coeff_track(xw.tolist(), ORDER, FRAME, HOP, PE)
    res = np.array(N.lpc_residual_track(xw.tolist(), ORDER, FRAME, HOP, PE), dtype=np.float32)
    f0t = f0_track_of(xw, sr)
    a_track = N.lpc_bw_expand_track(a_track, ORDER, sr, BW_FLOOR_HZ)
    if targ_f is not None:
        # ABSOLUTE-target A-by-S warp (the v6 fix).
        tf = [float(t) / vtl if t > 0 else 0.0 for t in targ_f]
        a_track = N.lpc_formant_set_track(
            a_track, ORDER, sr, tf, [float(b) for b in targ_bw],
            N_FORMANT, BW_ALPHA, WARP_FLO, WARP_FHI)
    elif ratio_warp is not None:
        # v5 ratio warp (control / baseline).
        a_track = N.lpc_formant_warp_track(
            a_track, ORDER, sr, [float(r) for r in ratio_warp],
            [float(b) for b in ratio_bw], N_FORMANT, BW_ALPHA, WARP_FLO, WARP_FHI)
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


# ======================================================================
#  the ANALYSIS-BY-SYNTHESIS FORMANT CORRECTION (the v6 fix)
# ======================================================================
def measure_render_formants(idx, donor, held, code, vtl, targ_f, targ_bw):
    """Render the held tids and RE-ANALYSE the rendered formants/bandwidths — the
    median tract signature of the SYNTHESIS output."""
    Fs, Bs = [], []
    for tid in held:
        sr, y = render_voice(idx[donor][tid], code, vtl, targ_f, targ_bw)
        sg = tract_signature(y, sr)
        if sg is not None:
            Fs.append(sg[0]); Bs.append(sg[1])
    if not Fs:
        return None
    return np.median(np.stack(Fs, 0), 0), np.median(np.stack(Bs, 0), 0)


def axs_solve(idx, S, donor, held, code, vtl, realF, realB,
              iters=ABS_ITERS, lam=ABS_LAM):
    """Deterministic A-by-S fixed point: drive the synthesis formant/bw TARGETS so
    the rendered audio re-analyses to the speaker's REAL formants (realF/realB).
    Damped step + per-dim backtrack + best-tracking. Target = REAL formants (the
    ground truth), the identity score is NEVER read. Returns (best_targF, best_targB,
    best_renderF, best_renderB, |eF12|)."""
    tF = realF.copy().astype(float)
    tB = realB.copy().astype(float)
    lamv = np.full(3, lam)
    best = (1e18, tF.copy(), tB.copy(), None, None)
    prev = None
    for _ in range(iters):
        m = measure_render_formants(idx, donor, held, code, vtl, tF, tB)
        if m is None:
            break
        rF, rB = m
        eF = realF - rF
        ne = float(np.linalg.norm(eF[:2]))  # F1,F2 are the within-register cue
        if ne < best[0]:
            best = (ne, tF.copy(), tB.copy(), rF.copy(), rB.copy())
        if prev is not None:
            worse = np.abs(eF) > np.abs(prev) + 5.0
            lamv = np.where(worse, lamv * 0.5, lamv)
            tF = np.where(worse, best[1], tF)  # dim-wise reset to best target
        tF = tF + lamv * eF
        tB = np.clip(tB + 0.5 * (realB - rB), 40.0, 650.0)
        prev = eF.copy()
    return best[1], best[2], best[3], best[4], best[0]


def main():
    print("=" * 74)
    print("SYNTH-SIDE F1/F2 CORRUPTION FIX (v6) — close the A-by-S loop in the")
    print("formant/bw dims so rendered formants RE-ANALYSE to the speaker's REAL")
    print("formant print (target = REAL formants, NOT the identity score).")
    print("  NEW primitive: lpc_formant_set_track (absolute-target pole warp)")
    print("=" * 74)

    idx = build_index()
    shared = sorted(set.intersection(*[set(idx[s].keys()) for s in SPEAKERS]))
    SAMPLE_TIDS = shared[:3]
    HELD_TIDS = shared[3:]
    AUD = HELD_TIDS[0]
    print(f"  sample tids={SAMPLE_TIDS}  held tids={HELD_TIDS}")

    # ---- recover code + real tract signature + levels per speaker ----
    codes, spk_level, realF, realB = {}, {}, {}, {}
    for spk in SPEAKERS:
        samp = np.concatenate([load(idx[spk][t])[1] for t in SAMPLE_TIDS])
        code = recover_voice_code_v3(samp, FS, order=ORDER, frame=FRAME, hop=HOP,
                                     pre_emph=PE, f0_ceil=F0_CEIL)
        cf = clean_f0_yin(samp, FS)
        if cf > 0:
            code.f0_hz = cf
        codes[spk] = code
        spk_level[spk] = formant_log_level(samp, FS) or 6.7
        Fm, Bm = tract_signature(samp, FS)
        realF[spk] = Fm
        realB[spk] = Bm

    # population reference + per-speaker SHAPE ratio (for the v5 baseline control).
    refF = np.median(np.stack([realF[s] for s in SPEAKERS], 0), axis=0)
    ratio = {}
    for s in SPEAKERS:
        raw = realF[s] / refF
        gmean = float(np.exp(np.mean(np.log(raw))))
        ratio[s] = raw / gmean

    def vtl_for(S, donor):
        return float(np.exp(spk_level[S] - spk_level[donor]))

    def farthest_f0_donor(S):
        return max((s for s in SPEAKERS if s != S),
                   key=lambda b: abs(F0_PROBE[b] - F0_PROBE[S]))

    # candidate donors: opposite register (cross-register synthesis is the test) +
    # we let the A-by-S residual to REAL formants pick which one the forward model
    # can actually HIT. Ground = real formants, NOT identity.
    DONOR_POOL = ["p231", "p225", "p230", "p233", "p228"]  # the higher-f0 half

    print("\n" + "=" * 74)
    print("(A) A-by-S FORMANT CORRECTION — drive rendered formants to REAL formants")
    print("    donor chosen by SMALLEST formant residual to REAL (ground=real, not")
    print("    score); per-speaker convergence of rendered F1/F2/F3 to the real print")
    print("=" * 74)
    axs = {}  # S -> (donor, vtl, targF, targB, renderF, renderB, eF12)
    for S in SPEAKERS:
        best = None
        for donor in DONOR_POOL:
            if donor == S:
                continue
            vtl = vtl_for(S, donor)
            tF, tB, rF, rB, e = axs_solve(idx, S, donor, HELD_TIDS, codes[S], vtl,
                                          realF[S], realB[S])
            if rF is None:
                continue
            if best is None or e < best[-1]:
                best = (donor, vtl, tF, tB, rF, rB, e)
        axs[S] = best
        donor, vtl, tF, tB, rF, rB, e = best
        print(f"  {S}{'M' if S in MALES else 'F'} donor={donor} vtl={vtl:.2f}: "
              f"realF={realF[S].round(0)} -> renderF={rF.round(0)}  "
              f"|eF1F2|={e:5.1f}Hz  (F1 {realF[S][0]-rF[0]:+.0f}, F2 {realF[S][1]-rF[1]:+.0f}, "
              f"F3 {realF[S][2]-rF[2]:+.0f})")

    # ---- the v5 RATIO-warp render (baseline) for the BEFORE comparison ----
    def render_v5(S, tid):
        donor = farthest_f0_donor(S)
        sr, y = render_voice(idx[donor][tid], codes[S], vtl_for(S, donor), None, None,
                             ratio_warp=ratio[S], ratio_bw=realB[S])
        return sr, y

    # ---- the v6 A-by-S render ----
    def render_v6(S, tid):
        donor, vtl, tF, tB, _, _, _ = axs[S]
        sr, y = render_voice(idx[donor][tid], codes[S], vtl, tF, tB)
        return sr, y

    # ====================================================================
    #  (a) PER-DIM NUISANCE/SIGNAL — BEFORE (v5 ratio) vs AFTER (v6 A-by-S)
    #      THE proof the synthesis is no longer corrupting the cue dims.
    # ====================================================================
    print("\n" + "=" * 74)
    print("(a) PER-DIM synth NUISANCE/SIGNAL — BEFORE (v5 ratio warp) vs AFTER (v6")
    print("    A-by-S). Synthesis is eliminated as limiter iff the CORRUPTED dims")
    print("    (logF1 3.62, logF2 1.05, level 1.99, logB2 1.69, logB3 1.36) drop <1.")
    print("=" * 74)

    real_prints = {}
    for s in SPEAKERS:
        vecs = [signal_full_vector(load(idx[s][tid])[1], FS) for tid in HELD_TIDS]
        vecs = [v for v in vecs if v is not None]
        real_prints[s] = np.median(np.stack(vecs, 0), 0)

    def render_prints(render_fn):
        out = {}
        for s in SPEAKERS:
            vecs = []
            for tid in HELD_TIDS:
                sr, y = render_fn(s, tid)
                v = signal_full_vector(y, sr)
                if v is not None:
                    vecs.append(v)
            out[s] = np.median(np.stack(vecs, 0), 0)
        return out

    Rreal = np.stack([real_prints[s] for s in SPEAKERS], 0)

    def nuis_sig(render_prints_d):
        G = np.stack([render_prints_d[s] for s in SPEAKERS], 0)
        OFF = G - Rreal
        return (OFF - OFF.mean(0)).std(0) / (Rreal.std(0) + 1e-9), G, OFF

    rp_v5 = render_prints(render_v5)
    rp_v6 = render_prints(render_v6)
    nz5, G5, OFF5 = nuis_sig(rp_v5)
    nz6, G6, OFF6 = nuis_sig(rp_v6)

    CORRUPT = {"logF1", "logF2", "level", "logB2", "logB3"}
    print(f"  {'dim':8} {'BEFORE(v5)':>11} {'AFTER(v6)':>10}  {'was/now':>16}")
    cleaned, still = [], []
    for d in range(10):
        nm = DIMNAMES[d]
        b, a = nz5[d], nz6[d]
        tag = ("CORRUPT" if nm in CORRUPT else "clean  ")
        status = ""
        if nm in CORRUPT:
            if a < 1.0:
                status = "  CLEANED (<1)"; cleaned.append(nm)
            else:
                status = "  STILL >1"; still.append(nm)
        print(f"  {nm:8} {b:11.3f} {a:10.3f}  {tag} {('reject->ADMIT' if (b>=1.0 and a<1.0) else '')}{status}")
    print(f"\n  CORRUPTED dims CLEANED (re-analyse to real, nuisance<1): {cleaned}")
    print(f"  CORRUPTED dims STILL synth-limited (nuisance>=1):        {still or 'NONE'}")

    # ====================================================================
    #  (b) RENDER-vs-REAL IDENTITY with the now-clean cue dims ADMITTED.
    #      Compare in RAW print space (no dim-dropping) — the corrupted dims are
    #      now trustworthy, so identity should rise toward the DATA ceiling.
    # ====================================================================
    print("\n" + "=" * 74)
    print("(b) RENDER-vs-REAL IDENTITY with the (now-clean) cue dims ADMITTED")
    print("    z-scored full-print nearest-neighbour; NO dims dropped (the v5 fix")
    print("    dropped F1/F2/level/B2/B3 — here they are trusted). v5 raw was 2/8.")
    print("=" * 74)
    mu_r, sd_r = Rreal.mean(0), Rreal.std(0) + 1e-9
    refz = {s: (real_prints[s] - mu_r) / sd_r for s in SPEAKERS}

    def identity(render_prints_d, dims=None, label=""):
        if dims is None:
            dims = list(range(10))
        correct = 0
        male_ok = 0
        m2m = 0
        rows = []
        for S in SPEAKERS:
            rz = (render_prints_d[S] - mu_r) / sd_r
            dd = {s: float(np.linalg.norm((rz - refz[s])[dims])) for s in SPEAKERS}
            near = min(dd, key=dd.get)
            ok = near == S
            correct += ok
            if S in MALES:
                male_ok += ok
                if not ok and near in MALES:
                    m2m += 1
            rank = sorted(dd.items(), key=lambda kv: kv[1])[:3]
            rows.append((S, ok, near, rank))
        return correct, male_ok, m2m, rows

    c5, m5, _, _ = identity(rp_v5)
    c6, m6, m2m6, rows6 = identity(rp_v6)
    # males-among-males (do the 3 males separate from each other?)
    mam6 = 0
    for S in MALES:
        rz = (rp_v6[S] - mu_r) / sd_r
        dd = {b: float(np.linalg.norm(rz - refz[b])) for b in MALES}
        mam6 += (min(dd, key=dd.get) == S)

    print("  per-speaker (v6 A-by-S, ALL dims admitted):")
    for S, ok, near, rank in rows6:
        print(f"    {'OK ' if ok else 'XX '}render({S}) -> nearest={near}   "
              + " < ".join(f"{s}:{d:.2f}" for s, d in rank))
    print(f"\n  IDENTITY (full N-D, all dims admitted): v5-ratio {c5}/8  ->  v6-A-by-S {c6}/8"
          f"   (chance 1/8; v5-doc raw-compare 2/8)")
    print(f"  MALES resolve to self:                  v5 {m5}/3      ->  v6 {m6}/3")
    print(f"  MALE-among-MALES (3 males only):        v6 {mam6}/3;  male->male mis {m2m6}")

    # ====================================================================
    #  (c) RESIDUAL ATTRIBUTION — for every miss, is it DATA (genuine real-formant
    #      overlap within real-measurement noise) or SYNTHESIS (the render still
    #      drifting from the real print)?
    # ====================================================================
    print("\n" + "=" * 74)
    print("(c) RESIDUAL ATTRIBUTION — every remaining miss: DATA (real formants of")
    print("    the confused pair genuinely overlap) or SYNTHESIS (render still drifts)?")
    print("=" * 74)
    # per-speaker real-formant measurement noise: std over the held tids.
    real_noise = {}
    for s in SPEAKERS:
        fs_ = []
        for tid in HELD_TIDS:
            sg = tract_signature(load(idx[s][tid])[1], FS)
            if sg is not None:
                fs_.append(sg[0])
        real_noise[s] = np.std(np.stack(fs_, 0), 0) if len(fs_) > 1 else np.array([30.0, 50.0, 50.0])

    any_synth = False
    for S, ok, near, rank in rows6:
        if ok:
            continue
        # the A-by-S render residual to S's OWN real formants (is the SYNTHESIS clean?)
        e_synth = axs[S][-1]  # |eF1F2| achieved
        # the real-formant gap between S and the confused speaker `near`.
        dF = np.abs(realF[S][:2] - realF[near][:2])
        noise = np.sqrt(real_noise[S][:2] ** 2 + real_noise[near][:2] ** 2)
        overlap = np.all(dF <= 2.0 * noise)  # within 2x measurement noise = genuine overlap
        synth_limited = e_synth > float(np.linalg.norm(noise))  # render drift exceeds noise
        verdict = ("DATA (real F1F2 overlap within meas-noise)" if overlap and not synth_limited
                   else "DATA-ish (synth clean, real formants close)" if not synth_limited
                   else "SYNTHESIS (render still drifts > meas-noise)")
        if synth_limited and not overlap:
            any_synth = True
        print(f"  {S}->{near}: real F1F2 gap={dF.round(0)}Hz  meas-noise(2σ)={(2*noise).round(0)}Hz  "
              f"render-drift={e_synth:.0f}Hz")
        print(f"     -> {verdict}")
    if not any([not ok for _, ok, _, _ in rows6]):
        print("  NO MISSES — every speaker resolves to self.")
    else:
        print(f"\n  ANY miss still attributable to SYNTHESIS? {'YES' if any_synth else 'NO'}")

    # ====================================================================
    #  (c) PRINCIPLED-NOT-FIT control — target = REAL formants, never the score.
    # ====================================================================
    print("\n" + "=" * 74)
    print("(control) PRINCIPLED-NOT-FIT — the A-by-S target is the REAL formants.")
    print("=" * 74)
    # show that the loop's objective (formant residual to REAL) is independent of
    # identity: report achieved formant residual vs identity outcome — uncorrelated
    # by construction (identity never enters axs_solve). Also: a target=POPULATION-
    # MEAN-formants ablation should HURT identity (proving the target carries the
    # speaker, not a generic lift).
    print("  achieved A-by-S formant residual to REAL (|eF1F2|, the loop's ONLY")
    print("  objective) vs whether identity landed — identity is a CONSEQUENCE:")
    for S, ok, near, _ in rows6:
        print(f"    {S}: |eF1F2|={axs[S][-1]:5.1f}Hz   identity={'self' if ok else near}")
    # ablation: drive to the POPULATION mean formants (no speaker info) -> identity drops.
    print("\n  ABLATION (target = POPULATION-MEAN formants, no speaker identity in")
    print("  the target): identity must DROP — proves the target carries the speaker.")
    popF = refF
    rp_abl = {}
    for S in SPEAKERS:
        donor, vtl, _, _, _, _, _ = axs[S]
        tF, tB, rF, rB, e = axs_solve(idx, S, donor, HELD_TIDS, codes[S], vtl,
                                      popF, realB[S], iters=ABS_ITERS, lam=ABS_LAM)
        vecs = []
        for tid in HELD_TIDS:
            sr, y = render_voice(idx[donor][tid], codes[S], vtl, tF, tB)
            v = signal_full_vector(y, sr)
            if v is not None:
                vecs.append(v)
        rp_abl[S] = np.median(np.stack(vecs, 0), 0)
    c_abl, m_abl, _, _ = identity(rp_abl)
    print(f"    identity[target=REAL formants]        : {c6}/8")
    print(f"    identity[target=POPULATION-MEAN]      : {c_abl}/8  (drop => target carries speaker)")

    # ====================================================================
    #  (d) BY EAR + intelligibility + ringing (don't regress synthesis quality)
    # ====================================================================
    print("\n" + "=" * 74)
    print("(d) BY EAR — intelligibility + ringing preserved (synthesis not regressed)")
    print("=" * 74)
    def intelligibility(render_fn):
        I = []
        for S in SPEAKERS:
            cs = []
            for tid in HELD_TIDS:
                sr, y = render_fn(S, tid)
                donor = axs[S][0]
                _, xc = load(idx[donor][tid])
                ty, tx = time_norm_cochlea(y, sr), time_norm_cochlea(xc, sr)
                if ty is None or tx is None:
                    continue
                a, b = ty.ravel(), tx.ravel()
                cs.append(float(np.corrcoef(a, b)[0, 1]) if a.std() > 0 and b.std() > 0 else 0.0)
            if cs:
                I.append(float(np.mean(cs)))
        return float(np.mean(I)) if I else float("nan")
    intel6 = intelligibility(render_v6)
    # ringing: rendered f0 vs code f0
    f0e = []
    for S in SPEAKERS:
        rf = float(np.exp(rp_v6[S][0]))
        f0e.append(100.0 * abs(rf - float(codes[S].f0_hz)) / float(codes[S].f0_hz))
    ring6 = float(np.mean(f0e))
    print(f"  intelligibility (rendered-vs-content cochlea corr): {intel6:.3f}  (v5 0.955)")
    print(f"  ringing (mean |render-f0 - code-f0|):               {ring6:.1f}%  (v5 0.1%)")

    # ---- WAVs for audition ----
    for S in SPEAKERS:
        sr, y = render_v6(S, AUD)
        donor = axs[S][0]
        write_wav24(f"{OUT}/held_{S}_says_t{AUD}_donor_{donor}.wav", y, sr)
        rf = idx[S].get(AUD)
        if rf:
            _, xr = load(rf)
            write_wav24(f"{OUT}/REAL_{S}_t{AUD}.wav", xr, FS)
    # 3 males through one donor for A/B (pick a common donor in the pool).
    common = "p231"
    for S in MALES:
        sr, y = render_voice(idx[common][AUD], codes[S], vtl_for(S, common),
                             axs[S][2], axs[S][3])
        write_wav24(f"{OUT}/AB_male_{S}_donor_{common}_t{AUD}.wav", y, sr)
    print(f"\n  WAVs (24-bit/48k) -> {OUT}/ (held_*, REAL_*, AB_male_*)")

    # ====================================================================
    #  VERDICT
    # ====================================================================
    print("\n" + "=" * 74)
    print("VERDICT NUMBERS:")
    print(f"  (a) CORRUPTED dims cleaned: {cleaned}  | still synth-limited: {still or 'NONE'}")
    print(f"  (b) identity v5-ratio {c5}/8 -> v6-A-by-S {c6}/8 (all dims admitted); "
          f"males {m5}/3 -> {m6}/3; male-among-males {mam6}/3")
    print(f"  (c) any miss still SYNTHESIS-attributable: {'YES' if any_synth else 'NO'}")
    print(f"  (c) ablation target=REAL {c6}/8 vs target=POP-MEAN {c_abl}/8 (principled-not-fit)")
    print(f"  (d) intelligibility {intel6:.3f} (v5 0.955); ringing {ring6:.1f}% (v5 0.1%)")
    print("===SYNTH_FORMANT_FIX_V6_COMPLETED===")


if __name__ == "__main__":
    main()
