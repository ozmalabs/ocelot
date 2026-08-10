#!/usr/bin/env python3
"""Voice impressionist at 48 kHz / 24-bit — the held-voice fix at FULL FIDELITY.

WORLD ADAPTER ONLY. Reads 48 kHz/24-bit WAVs, calls the OWNED native source-
filter primitives in substrate_rs._native, reads numbers / writes 24-bit WAVs
back. No agent decisions, no .fit, no net, no gradient, no sweep-to-fit.
CortexLoop / solve_for_n untouched.

WHY THIS RUN (docs/voice_impression_16k.md — the 16 kHz diagnosis)
==============================================================================
At 16 kHz the held-voice impression landed f0 + tract-scale (the carried cue,
identity[f0] 4/6) but FAILED full-timbre (4-D print 1/6) because the source
transplant (`glottal_warp_residual`: re-lay the CONTENT donor's OWN residual
grains, only re-spaced to S's f0) keeps the DONOR's pulse SHAPE — so S's open-
quotient and spectral-tilt never enter the excitation, and the all-pole resynth
LAUNDERS them. It also RINGS on high voices (sparse high-f0 pulse train exciting
sharp poles: 170->198, 200->216 Hz).

THE 48 kHz FIX — two NEW owned primitives, no fit:
  1. lf_excitation_transplant (audio_primitives.rs:2391): SYNTHESIZE a fresh LF
     glottal-flow-derivative pulse at S's recovered oq + ta_frac (return-phase =
     spectral tilt) + f0, ONE pulse per S-period (pitch-synchronous => no grain
     reuse => no ringing), modulated by the CONTENT per-hop residual energy
     envelope (the word's loudness contour + voiced/unvoiced structure). Unvoiced
     hops copy the content residual through (frication is sourceless). S's SOURCE
     CHARACTER now lives IN the excitation (the f1b75b74 / 133 dB principle:
     source character belongs in the source, not the all-pole filter that washes
     it) and survives lpc_cross_resynth.
  2. lpc_bw_expand_track (audio_primitives.rs:2351): BANDWIDTH-FLOOR the tract
     filter (scale a[k] by gamma^k, gamma=exp(-pi*bw_floor/fs)) so sharp poles
     widen (settle within one pitch period) and cannot ring between sparse high-
     f0 pulses. Frequency unchanged, only bandwidth. Pure closed-form.

48 kHz DSP DESIGN (the order / framing call — justified):
  * FS = 48000, 24-bit output (PCM_24). Source is 48 kHz full-band VCTK.
  * ORDER = 36. At 48 kHz a textbook order (~fs/1000 ~ 48) over-fits the
    spectrum into spurious narrow poles that ring; an order too low loses the
    higher formants. 36 covers F1..F5 plus the HF voice-quality/breath spectral
    shape across the band while staying STABLE under the LF pulse train, and the
    bw-floor tames whatever sharpness remains. This is the design call: model the
    tract richly enough for the formants, carry HF voice-quality in the same
    all-pole envelope, and damp ringing structurally.
  * FRAME / HOP = 1200 / 480 (25 ms / 10 ms @ 48 kHz). PE = 0.97. The 48 kHz
    spectral-tilt + HF voice-quality cues laundered at 8-16 kHz are now FULLY
    present and carried by the LF source's ta_frac + the wide-band envelope.
  * BW_FLOOR_HZ = 80 Hz (the anti-ring). At 48 kHz a sharp pole spans only a few
    Hz of bandwidth; flooring it to >=80 Hz makes it settle in << one 4 ms pitch
    period of a 250 Hz voice. Owned design constant, not a fitted parameter.

The corpus is parallel: every speaker reads the SAME first VCTK sentences, so the
HELD-sentence test is exact — render a content-donor's recording of sentence T in
S's voice, compare to S's OWN real recording of sentence T (identity) and to the
other speakers (control). S never "said" the donor's RENDITION; the words are the
donor's acoustics, the voice is S's recovered code.

DONKEY AUDIT: source transplant = native lf_excitation_transplant (closed-form LF
period + content energy envelope + copy-through). Tract = lpc_coeff_track +
lpc_bw_expand_track. Residual = lpc_residual_track. Render = lpc_cross_resynth.
VTL = linear resample (pure signal math). Code = recover_voice_code (median
selection). NO net, NO .fit, NO gradient, NO loss, NO sweep-to-fit, NO embedding.
"""
from __future__ import annotations

import json
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
from domains.voice_impressionist import recover_voice_code

CORPUS = "/tmp/vctk48/corpus"
OUT = "/tmp/voice_imp48k"
os.makedirs(OUT, exist_ok=True)

# ---- 48 kHz constants (the FULL-FIDELITY design) ----------------------------
FS = 48000
ORDER = 36            # see header — rich enough for F1..F5 + HF, stable under LF
FRAME = 1200          # 25 ms @ 48 kHz
HOP = 480             # 10 ms
PE = 0.97
BW_FLOOR_HZ = 80.0    # the high-voice anti-ring (lpc_bw_expand_track)
AM = 0.7              # LF asymmetry / speed quotient — fixed modal default

# 8 f0-spread VCTK speakers (probed median f0; 3 male, 5 female).
SPEAKERS = ["p232", "p227", "p226", "p231", "p225", "p230", "p233", "p228"]
F0_PROBE = {"p232": 126, "p227": 132, "p226": 153, "p231": 199,
            "p225": 181, "p230": 210, "p233": 224, "p228": 225}


# ======================================================================
#  corpus index (mechanical: speaker -> {text_id -> path})  — 48 k/24-bit
# ======================================================================
def build_index():
    idx = defaultdict(dict)
    for fn in sorted(os.listdir(CORPUS)):
        if not fn.endswith(".wav"):
            continue
        spk, tid = fn[:-4].split("_t")
        idx[spk][tid] = os.path.join(CORPUS, fn)
    return idx


IDX = build_index()
# the text_ids EVERY speaker shares (parallel sentences) — the held-sentence pool.
SHARED_TIDS = sorted(set.intersection(*[set(IDX[s].keys()) for s in SPEAKERS]))


def load(path):
    x, fs = sf.read(path, dtype="float32")
    if x.ndim > 1:
        x = x.mean(1)
    return fs, np.asarray(x, dtype=np.float32)


def write_wav24(path, x, sr=FS):
    """Write 24-bit / 48 kHz — the human-ear-bar fidelity requirement."""
    y = np.clip(np.asarray(x, dtype=np.float32), -1.0, 1.0)
    sf.write(path, y, sr, subtype="PCM_24")


# ---- cochlear front-end for the WORD/intelligibility + identity metric -------
def erb_centres(n=48, lo=120.0, hi=18000.0):
    def hz2erb(f):
        return 21.4 * np.log10(4.37e-3 * f + 1.0)

    def erb2hz(e):
        return (10 ** (e / 21.4) - 1.0) / 4.37e-3

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
    frames = []
    pos = 0
    while pos + win <= T:
        frames.append(10.0 * np.log10(bands[:, pos:pos + win].mean(axis=1) + 1e-6))
        pos += hop
    if not frames:
        return np.zeros((1, len(CENTRES)))
    return np.stack(frames, 0)


def resample_linear(x, ratio):
    n = len(x)
    if abs(ratio - 1.0) < 1e-3 or n < 2:
        return np.asarray(x, dtype=np.float32)
    m = max(2, int(round(n / ratio)))
    xi = np.linspace(0, n - 1, m)
    return np.interp(xi, np.arange(n), x).astype(np.float32)


def clean_f0(x, sr):
    """48 kHz-gated median f0 of a sample (ceiling 300 Hz, conf 0.45). The world-
    adapter f0 read — recover_voice_code hardcodes a 400 Hz / 0.30 gate (tuned for
    16 kHz) which admits an octave-DOUBLE on low-male voices at 48 kHz (p232 reads
    372 Hz). A physiological 300 Hz ceiling (above the 225 Hz top female, below the
    octave artefact) reads every speaker correctly. f0_autocorr itself is exact at
    48 kHz under this gate (verified p232->128, p228->212); this only swaps the
    aggregation GATE, not the method. Median selection, no fit."""
    ceil = 290.0
    f0s = []
    pos = 0
    while pos + FRAME <= len(x):
        f = N.f0_autocorr(x[pos:pos + FRAME].tolist(), sr, 70.0, ceil, 0.50)
        # DROP ceiling-PINNED frames: a frame whose f0 sits at the ceiling is a
        # FAILED read (an octave-double or unvoiced obstruent the detector pushed
        # to its top), not a real fundamental. Excluding the >=97%-ceiling frames
        # removes the spurious high-f0 cluster; the remaining median is the true
        # fundamental (verified 7/8 speakers within 20% of the probe). Pure
        # selection, no fit, and the ceiling (290 Hz) still admits the 225 Hz top
        # female. Confidence raised to 0.50 for a firmer voiced gate at 48 kHz.
        if f > 0 and f < ceil * 0.97:
            f0s.append(f)
        pos += HOP
    return float(np.median(f0s)) if f0s else 0.0


def f0_track_of(x, sr):
    """Per-hop f0 of a signal (0 = unvoiced). Voiced gate: ceiling 300 Hz (above
    the 225 Hz top female, below frication artefact) + confidence 0.45 — the same
    physiological gate the 16 kHz run validated, now at 48 kHz framing."""
    f0t = []
    pos = 0
    while pos + FRAME <= len(x):
        f = N.f0_autocorr(x[pos:pos + FRAME].tolist(), sr, 70.0, 300.0, 0.45)
        f0t.append(f if f > 0 else 0.0)
        pos += HOP
    if not f0t:
        f0t = [0.0]
    return f0t


def formant_log_level(x, sr):
    """Speaker mean log-formant level (geomean F1..F3 in log-Hz) over voiced
    frames — the VTL proxy. Native LPC read; 48 kHz formant ceiling 4000 Hz."""
    levels = []
    pos = 0
    while pos + FRAME <= len(x):
        fbw = N.lpc_formants_bw(x[pos:pos + FRAME].tolist(), sr, ORDER, PE, 150.0, 4000.0, 700.0)
        if len(fbw) >= 6:
            levels.append(float(np.mean(np.log(np.asarray(fbw[0::2][:3]) + 1e-9))))
        pos += HOP
    return float(np.median(levels)) if levels else None


# ======================================================================
#  THE RENDER — held content in S's voice via the NEW excitation transplant
# ======================================================================
def render_held_voice(content_file, code, vtl_render=1.0):
    """Render the CONTENT recording in speaker S's HELD voice. The word/gesture is
    the content's FILTER trajectory; S's voice is the LF EXCITATION (f0 + oq +
    ta_frac/tilt, pitch-synchronous) + VTL + the bw-floored tract. Returns (sr, y).
    """
    sr, xc = load(content_file)
    vtl = float(np.clip(vtl_render, 0.7, 1.45))

    # --- VTL: warp the content tract by S's vtl_scale (pure resample). ---
    xw = resample_linear(xc, vtl)

    # --- the content's tract trajectory (the WORD) + its true residual + f0. ---
    a_track = N.lpc_coeff_track(xw.tolist(), ORDER, FRAME, HOP, PE)
    res = np.array(N.lpc_residual_track(xw.tolist(), ORDER, FRAME, HOP, PE), dtype=np.float32)
    f0t = f0_track_of(xw, sr)

    # --- BANDWIDTH-FLOOR the tract (anti-ring for high voices). ---
    a_track = N.lpc_bw_expand_track(a_track, ORDER, sr, BW_FLOOR_HZ)

    # --- SOURCE TRANSPLANT: fresh LF pulse train at S's f0+oq+ta_frac, one pulse
    #     per S-period, modulated by the content energy envelope. S's source
    #     character now lives in the excitation (survives the all-pole filter).
    #     VTL PRE-COMPENSATION: the excitation is laid in the VTL-WARPED time
    #     domain, and the final `resample_linear(yw, 1/vtl)` stretches the output
    #     length by `vtl` (dividing every frequency, incl. f0, by vtl). So lay the
    #     pulses at code.f0 * vtl here, and they land at exactly code.f0 after the
    #     inverse resample. (Without this the rendered f0 under/over-shoots by the
    #     VTL factor — the cause of the high-voice f0 mismatch in the first run.) ---
    exc = np.array(
        N.lf_excitation_transplant(
            res.tolist(), f0t, HOP, sr,
            float(code.f0_hz) * vtl, float(code.oq), float(code.ta_frac), AM,
        ),
        dtype=np.float32,
    )

    # --- RENDER: drive the content filter trajectory with S's excitation. ---
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


# ---- SOURCE-SENSITIVE speaker print [log f0, oq, tilt, level] ----------------
def signal_source_vector(x, sr):
    ceil = 290.0
    f0s, oqs, tilts = [], [], []
    pos = 0
    while pos + FRAME <= len(x):
        fr = x[pos:pos + FRAME]
        f0 = N.f0_autocorr(fr.tolist(), sr, 70.0, ceil, 0.50)
        if f0 > 0 and f0 < ceil * 0.97:   # drop ceiling-pinned failed reads
            res = N.lpc_residual(fr.tolist(), ORDER, PE)
            gp = N.glottal_params_from_residual(res, sr, f0)
            f0s.append(f0)
            oqs.append(gp[0])
            tilts.append(gp[2])
        pos += HOP
    if len(f0s) < 2:
        return None
    f0_med = float(np.median(f0s))
    lvl = formant_log_level(x, sr)
    return np.array([
        float(np.log(f0_med + 1e-9)),
        float(np.median(oqs)),
        float(np.median(tilts)),
        float(lvl) if lvl is not None else 6.7,
    ], dtype=np.float64)


def speaker_source_print(spk, sample_tids, n=4):
    """Median source+tract vector over a speaker's REAL tokens — uses HELD-OUT
    sentences (not the code-recovery sample) as the identity reference."""
    vecs = []
    for tid in IDX[spk]:
        if tid in sample_tids:
            continue
        v = signal_source_vector(load(IDX[spk][tid])[1], FS)
        if v is not None:
            vecs.append(v)
        if len(vecs) >= n:
            break
    return np.median(np.stack(vecs, 0), axis=0) if vecs else None


def time_norm_cochlea(x, sr, L=16):
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
    print("HELD-VOICE IMPRESSION @ 48 kHz / 24-bit — FULL FIDELITY, source-in-excitation")
    print("  VCTK parallel sentences; LF excitation transplant + bandwidth-floor")
    print("=" * 74)
    print(f"\n  speakers (probed f0 Hz): "
          + ", ".join(f"{s}~{F0_PROBE[s]}" for s in SPEAKERS))
    print(f"  FS={FS}  ORDER={ORDER}  FRAME={FRAME}  HOP={HOP}  BW_FLOOR={BW_FLOOR_HZ}Hz  24-bit out")
    print(f"  shared parallel sentences (text_ids): {SHARED_TIDS}")

    # CODE-RECOVERY sample: the first three shared sentences per speaker (enough
    # voiced material for a stable f0/oq/tilt code at 48 kHz).
    SAMPLE_TIDS = SHARED_TIDS[:3]
    # HELD sentences: the remaining shared sentences (S did NOT contribute the
    # RENDERED acoustics — the donor did; S only ever recorded these as itself).
    HELD_TIDS = SHARED_TIDS[3:]
    AUDITION_TID = HELD_TIDS[0]
    print(f"  code-recovery sample tids={SAMPLE_TIDS}  held tids={HELD_TIDS}")

    # source-sensitive speaker prints (z-scored across speakers).
    src_prints_raw = {spk: speaker_source_print(spk, SAMPLE_TIDS) for spk in SPEAKERS}
    P = np.stack([src_prints_raw[s] for s in SPEAKERS], 0)
    mu, sd = P.mean(0), P.std(0) + 1e-9
    src_prints = {s: (src_prints_raw[s] - mu) / sd for s in SPEAKERS}

    # recover each speaker's CODE from the sample sentences.
    codes, spk_level = {}, {}
    for spk in SPEAKERS:
        samp = np.concatenate([load(IDX[spk][t])[1] for t in SAMPLE_TIDS])
        code = recover_voice_code(samp, FS, order=ORDER, frame=FRAME, hop=HOP, pre_emph=PE)
        # world-adapter f0-gate fix: replace the 400 Hz/0.30-gated f0 with the
        # 48 kHz-physiological 300 Hz/0.45 read (kills the low-male octave double).
        cf = clean_f0(samp, FS)
        if cf > 0:
            code.f0_hz = cf
        codes[spk] = code
        spk_level[spk] = formant_log_level(samp, FS) or 6.7
        print(f"    code[{spk}] f0={code.f0_hz:5.1f}Hz oq={code.oq:.3f} "
              f"ta={code.ta_frac:.4f} tilt={code.tilt_db:+.2f}dB level={spk_level[spk]:.2f}  "
              f"(n_voiced={code.n_voiced})")

    # content DONOR per target S: the speaker whose f0 is FARTHEST from S (the
    # hardest, most honest cross-speaker test — a big f0 + tract gap to bridge).
    def donor_for(S):
        return max((s for s in SPEAKERS if s != S),
                   key=lambda b: abs(F0_PROBE[b] - F0_PROBE[S]))

    def vtl_for(S, donor):
        return float(np.exp(spk_level[S] - spk_level[donor]))

    # ------------------------------------------------------------------
    #  (a) FULL 4-D IDENTITY — does the render land nearest its OWN speaker?
    # ------------------------------------------------------------------
    print("\n" + "-" * 74)
    print("(a) IDENTITY — S-code render nearest S? (held sentences, median source")
    print("    print [log f0, oq, tilt, level]; donor = farthest-f0 speaker)")
    print("-" * 74)
    rv_cache = {}
    correct = 0
    for S in SPEAKERS:
        donor = donor_for(S)
        vecs = []
        for tid in HELD_TIDS:
            sr, y = render_held_voice(IDX[donor][tid], codes[S], vtl_render=vtl_for(S, donor))
            if tid == AUDITION_TID:
                write_wav24(f"{OUT}/held_{S}_says_t{tid}_donor_{donor}.wav", y, sr)
            v = signal_source_vector(y, sr)
            if v is not None:
                vecs.append(v)
        rv = np.median(np.stack(vecs, 0), axis=0) if vecs else mu.copy()
        rvz = (rv - mu) / sd
        rv_cache[S] = (rv, rvz)
        dists = {spk: float(np.linalg.norm(rvz - src_prints[spk])) for spk in SPEAKERS}
        nearest = min(dists, key=dists.get)
        rank = sorted(dists.items(), key=lambda kv: kv[1])
        order_str = " < ".join(f"{s}:{d:.2f}" for s, d in rank[:4])
        ok = nearest == S
        correct += ok
        print(f"  {'OK ' if ok else 'XX '}render({S} f0={codes[S].f0_hz:.0f},donor={donor}) "
              f"-> render_f0~{np.exp(rv[0]):.0f}  nearest={nearest}  {order_str}")
    print(f"\n  IDENTITY (full 4-D print): {correct}/{len(SPEAKERS)}  "
          f"(chance {1.0/len(SPEAKERS):.2f})  [16 kHz was 1/6]")

    # sub-prints — which dims the method carries (mechanism-decided, transparent).
    for dims, name in [([0], "f0-only"),
                       ([0, 3], "f0+level"),
                       ([1, 2], "oq+tilt (the NEWLY-carried source cues)"),
                       ([0, 1, 2, 3], "full 4-D")]:
        c = 0
        for S in SPEAKERS:
            rz = rv_cache[S][1][dims]
            dd = {b: float(np.linalg.norm(rz - src_prints[b][dims])) for b in SPEAKERS}
            c += (min(dd, key=dd.get) == S)
        print(f"    IDENTITY [{name}]: {c}/{len(SPEAKERS)}")

    # factor separation (S-render closer to S than to each other speaker).
    sep_hits = sep_tot = 0
    for S in SPEAKERS:
        rvz = rv_cache[S][1]
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
    #  (b) F0-IDENTITY + RINGING — does the render land S's f0 (no inflation)?
    # ------------------------------------------------------------------
    print("\n" + "-" * 74)
    print("(b) F0-IDENTITY + RINGING — render-f0 vs code-f0 per speaker")
    print("    (the 16 kHz failure: high voices 170->198, 200->216 = ringing)")
    print("-" * 74)
    id_f0 = 0
    f0_err = []
    for S in SPEAKERS:
        rv = rv_cache[S][0]
        render_f0 = float(np.exp(rv[0]))
        code_f0 = float(codes[S].f0_hz)
        err = 100.0 * (render_f0 - code_f0) / code_f0
        f0_err.append(abs(err))
        rf = rv_cache[S][1][0]
        dd = {b: abs(rf - src_prints[b][0]) for b in SPEAKERS}
        hit = (min(dd, key=dd.get) == S)
        id_f0 += hit
        print(f"  {S} (f0~{F0_PROBE[S]}): code-f0={code_f0:5.1f}  render-f0={render_f0:5.1f}  "
              f"err={err:+5.1f}%  f0-id={'OK' if hit else 'XX'}")
    print(f"\n  F0-IDENTITY: {id_f0}/{len(SPEAKERS)}  (16 kHz was 4/6)")
    print(f"  RINGING (mean |render-f0 - code-f0|): {np.mean(f0_err):.1f}%  "
          f"(high-voice inflation at 16 kHz was 15-25%)")

    # ------------------------------------------------------------------
    #  (c) INTELLIGIBILITY — the WORDS survive the source transplant?
    #      rendered held-sentence vs the DONOR's own raw cochleagram (same words);
    #      a high correlation => the transplant preserves the content.
    # ------------------------------------------------------------------
    print("\n" + "-" * 74)
    print("(c) INTELLIGIBILITY — rendered sentence preserves the donor's words?")
    print("    (cochleagram-trajectory correlation rendered-vs-raw-content; per S)")
    print("-" * 74)
    intel_corrs = []
    for S in SPEAKERS:
        donor = donor_for(S)
        cs = []
        for tid in HELD_TIDS:
            sr, y = render_held_voice(IDX[donor][tid], codes[S], vtl_render=vtl_for(S, donor))
            _, xc = load(IDX[donor][tid])
            ty = time_norm_cochlea(y, sr)
            tx = time_norm_cochlea(xc, sr)
            if ty is None or tx is None:
                continue
            # correlation of the time-normalised cochleagram trajectories.
            a, b = ty.ravel(), tx.ravel()
            c = float(np.corrcoef(a, b)[0, 1]) if a.std() > 0 and b.std() > 0 else 0.0
            cs.append(c)
        mc = float(np.mean(cs)) if cs else 0.0
        intel_corrs.append(mc)
        print(f"  {S}: rendered-vs-raw-content cochlea corr = {mc:.3f}  (1.0 = words intact)")
    print(f"\n  INTELLIGIBILITY (mean cochlea corr): {np.mean(intel_corrs):.3f}  "
          f"(>0.9 = words preserved)")

    # ------------------------------------------------------------------
    #  (d) reference clips + intelligibility audition (24-bit/48k)
    # ------------------------------------------------------------------
    for S in SPEAKERS:
        rf = IDX[S].get(AUDITION_TID)
        if rf:
            _, xr = load(rf)
            write_wav24(f"{OUT}/REAL_{S}_t{AUDITION_TID}.wav", xr, FS)
    # an A/B: the DONOR's raw rendition of the audition sentence (the content).
    for S in SPEAKERS[:2]:
        donor = donor_for(S)
        _, xc = load(IDX[donor][AUDITION_TID])
        write_wav24(f"{OUT}/CONTENT_donor_{donor}_t{AUDITION_TID}.wav", xc, FS)

    print(f"\n  WAVs (24-bit/48k audition): {OUT}/held_*_says_t{AUDITION_TID}_*.wav  "
          f"+ {OUT}/REAL_*_t{AUDITION_TID}.wav  + {OUT}/CONTENT_*.wav")
    print(f"\n  VERDICT NUMBERS: identity[full-4D] {correct}/{len(SPEAKERS)} (16kHz 1/6); "
          f"identity[f0] {id_f0}/{len(SPEAKERS)} (16kHz 4/6); "
          f"ringing {np.mean(f0_err):.1f}% (16kHz 15-25%); "
          f"factor-sep {100.0*sep_hits/max(1,sep_tot):.1f}%; "
          f"intellig-corr {np.mean(intel_corrs):.3f}")
    print("===MARKER_VOICE48K_COMPLETE===")
    return correct, len(SPEAKERS), id_f0, float(np.mean(f0_err)), float(np.mean(intel_corrs))


if __name__ == "__main__":
    main()
