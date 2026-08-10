"""voiced_whisper_probe — THE VOICED<->WHISPER INVARIANCE FALSIFIER.

THE INSIGHT (ozma_whisper_message_is_the_filter): whispering ablates the SOURCE
(no f0 / voicing / periodicity) and keeps the FILTER (vocal-tract / formants); the
linguistic message survives -> the message lives in the FILTER.  So a FILTER /
RELATIONAL representation should recognise a WHISPERED word it only ever heard
VOICED (invariant to the serialization).  A SOURCE representation structurally
CANNOT (there is no periodicity left to read).  This is the clean test of whether
our winning whole-unit relational shape reads STRUCTURE-INVARIANT-TO-SERIALIZATION
or something source-specific riding along.

WHISPER SYNTHESIS — controlled, owned LPC source-filter machinery, I/O boundary only
--------------------------------------------------------------------------------
For each voiced clip the agent's OWNED native ops separate source from filter:
  * FILTER  = `lpc_coeff_track`     (the per-frame vocal-tract pole trajectory).
  * SOURCE  = `lpc_residual_track`  (the recovered glottal excitation).
The whisper version holds the FILTER LITERALLY IDENTICAL and replaces ONLY the
source: white Gaussian noise, per-frame RMS-matched to the residual, driven through
the SAME filter via `lpc_cross_resynth`.  Voiced and synth-whisper therefore differ
in EXACTLY ONE variable (pulses -> noise).  Verified (stage-0 prints):
  * f0 collapses from the real ~105-130 Hz (voiced) to the f0-estimator's noise rail
    320-400 Hz (whisper) -> NO periodicity -> the SOURCE is gone.
  * formant frequencies (F1/F2/F3) are preserved within estimation noise -> the
    FILTER is kept.
This is the cleanest possible whisper: signal-processing at the I/O boundary on the
agent's owned LPC primitives.  Permitted there.

DO-CONTRAST — three representations, the SAME native DtwTo nearest-exemplar decision
--------------------------------------------------------------------------------
  (A) SURFACE     raw gammatone band-energy trajectory (frames x bands).  Baseline.
  (B) RELATIONAL  the winning whole-unit relational shape (domains/relational_shape:
                  ordinal band-rank + whole-unit self-similarity), composed from the
                  agent's owned ops and evaluated NATIVELY.
  (C) SOURCE      a periodicity / correlogram trajectory (frames x lags) from the
                  agent's owned TFS chain (gammatone_band -> band_autocorr ->
                  summary_autocorrelogram).  The NEGATIVE CONTROL — it SHOULD collapse
                  on whisper since whisper has no periodicity; that collapse proves
                  the test discriminates source from filter.

In ALL arms the recognition distance is the native DtwTo Term (substrate.evaluate),
argmin over VOICED exemplars.  No .fit, no net, no sweep.

VENUE: FSDD digits (10-way), WITHIN-SPEAKER (train + test from the SAME speakers but
DISJOINT clips) — this isolates the SOURCE variable (cross-speaker is a later
compounding test).  Train exemplars are VOICED; test BOTH voiced (within-condition
ceiling) AND synth-whisper (cross-condition).

THE KEY NUMBERS (k/N + % for every cell):
  voiced->voiced (within) = the ceiling per representation.
  voiced->whisper (cross).
  the DROP (within - cross) per representation = THE FALSIFIER.
PREDICTION: (B) RELATIONAL survives (small drop) = PASS (reads the filter);
            (A) SURFACE degrades more; (C) SOURCE collapses toward chance = the test
            discriminates.  IF (B) ALSO collapses -> the falsifier FAILS relational
            (it was source-dependent) -> reported plainly.  READ THE NUMBERS.

Run: python -m scripts.voiced_whisper_probe [n_train] [n_test] [seed]
"""
from __future__ import annotations

import os
import re
import sys
import time
import wave
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import substrate_rs._native as N
from substrate_rs import Substrate
import domains.recognition_graph as RG
from scripts.invariant_units_accept import band_trajectory_matrix
from domains.relational_shape import relational_shape


DATA_DIR = "/tmp/fsdd/recordings"
_DIGITS = ["zero", "one", "two", "three", "four", "five",
           "six", "seven", "eight", "nine"]
_FN_RE = re.compile(r"(\d)_([a-z]+)_(\d+)\.wav")
FS = 8000

# --- LPC analysis/resynthesis constants (owned source-filter primitives) -------
# Identical framing to scripts/voice_impressionist_validate.py (8 kHz FSDD).
LPC_ORDER = 14
LPC_FRAME = 200          # 25 ms @ 8 kHz
LPC_HOP = 80             # 10 ms
LPC_PE = 0.97

# --- SOURCE rep (periodicity / correlogram) TFS chain --------------------------
# Verbatim owned chain from scripts/stage2_periodicity_gate.py.
TFS_FCS = (150.0, 250.0, 400.0, 600.0, 900.0, 1400.0, 2200.0, 3200.0)
TFS_WIN = 256            # 32 ms @ 8 kHz
TFS_HOP = 96             # 12 ms
TFS_MAXLAG = 100         # F0 80-320 Hz -> lag 25..100 @ 8 kHz
TFS_NLAGS = TFS_MAXLAG + 1


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------
def load_wav(path):
    with wave.open(path, "rb") as w:
        fs = w.getframerate()
        buf = w.readframes(w.getnframes())
    arr = np.frombuffer(buf, dtype=np.int16).astype(np.float32) / 32768.0
    peak = max(float(np.abs(arr).max()), 1.0)
    return (arr * 0.7 / peak).astype(np.float32), fs


def gather_files():
    out = []
    for fn in sorted(os.listdir(DATA_DIR)):
        m = _FN_RE.match(fn)
        if not m:
            continue
        digit, speaker, idx = m.groups()
        out.append((os.path.join(DATA_DIR, fn), int(digit), speaker, int(idx)))
    return out


# ---------------------------------------------------------------------------
# WHISPER SYNTHESIS — owned LPC ops, filter held IDENTICAL, source -> noise.
# ---------------------------------------------------------------------------
def synth_whisper(x, seed=0):
    """Voiced clip -> synth-whisper: keep the LPC FILTER track identical, replace
    the residual with per-frame RMS-matched white Gaussian noise, drive the same
    filter.  Owned native ops only (lpc_coeff_track / lpc_residual_track /
    lpc_cross_resynth).  Differs from the voiced resynth in EXACTLY the source."""
    xl = x.tolist()
    a_frames = N.lpc_coeff_track(xl, LPC_ORDER, LPC_FRAME, LPC_HOP, LPC_PE)
    res = np.array(N.lpc_residual_track(xl, LPC_ORDER, LPC_FRAME, LPC_HOP, LPC_PE),
                   dtype=np.float32)
    rng = np.random.default_rng(seed)
    exc = rng.standard_normal(len(res)).astype(np.float32)
    # per-frame RMS-match the noise to the residual so the FILTER sees the same
    # frame energies (only the within-frame TEMPORAL structure changes: a noise
    # spectrum instead of a pulse train).
    for i in range(len(res) // LPC_HOP):
        sl = slice(i * LPC_HOP, (i + 1) * LPC_HOP)
        rms_s = float(np.sqrt((res[sl] ** 2).mean()) + 1e-12)
        rms_n = float(np.sqrt((exc[sl] ** 2).mean()) + 1e-12)
        exc[sl] = exc[sl] * (rms_s / rms_n)
    y = np.array(N.lpc_cross_resynth(a_frames, exc.tolist(), LPC_ORDER,
                                     LPC_HOP, LPC_PE), dtype=np.float32)
    # match overall RMS to the original clip so the front-ends see comparable level
    rms_x = float(np.sqrt((x ** 2).mean()) + 1e-12)
    rms_y = float(np.sqrt((y ** 2).mean()) + 1e-12)
    return (y * (rms_x / rms_y)).astype(np.float32)


def voiced_resynth(x):
    """The control resynth: same LPC chain but driven by the TRUE residual (the
    glottal source).  Used only by the stage-0 verification print."""
    xl = x.tolist()
    a_frames = N.lpc_coeff_track(xl, LPC_ORDER, LPC_FRAME, LPC_HOP, LPC_PE)
    res = N.lpc_residual_track(xl, LPC_ORDER, LPC_FRAME, LPC_HOP, LPC_PE)
    return np.array(N.lpc_cross_resynth(a_frames, res, LPC_ORDER, LPC_HOP, LPC_PE),
                    dtype=np.float32)


# ---------------------------------------------------------------------------
# REPRESENTATIONS.  All three are frames x D trajectories DtwTo can match over.
# ---------------------------------------------------------------------------
def surface_rep(x, fs):
    """(A) SURFACE — raw gammatone band-energy trajectory."""
    M = band_trajectory_matrix(x, fs)
    return M if M is not None and len(M) >= 2 else None


def relational_rep(x, fs, n_anchors=6):
    """(B) RELATIONAL — the agent's whole-unit relational shape (native eval)."""
    M = band_trajectory_matrix(x, fs)
    if M is None or len(M) < 2:
        return None
    return relational_shape(M, n_anchors=n_anchors)


def source_rep(x, fs):
    """(C) SOURCE — periodicity / correlogram trajectory (frames x lags), the
    agent's owned TFS chain: gammatone_band -> band_autocorr ->
    summary_autocorrelogram.  The negative control."""
    s = np.asarray(x, dtype=np.float32)
    if len(s) < TFS_WIN:
        return None
    sl = s.tolist()
    band_acs = []
    for fc in TFS_FCS:
        band = N.gammatone_band(sl, FS, float(fc), 4)
        ac = N.band_autocorr(band, TFS_WIN, TFS_HOP, TFS_MAXLAG)
        if ac:
            band_acs.append(ac)
    if not band_acs:
        return None
    sacf = N.summary_autocorrelogram(band_acs, TFS_NLAGS)
    if not sacf:
        return None
    M = np.array(sacf, dtype=np.float32)
    nf = len(M) // TFS_NLAGS
    if nf < 2:
        return None
    return M[:nf * TFS_NLAGS].reshape(nf, TFS_NLAGS).astype(np.float32)


# ---------------------------------------------------------------------------
# Stage-0 verification: synth-whisper really removes the source + keeps the filter.
# ---------------------------------------------------------------------------
def verify_whisper(files, n=6):
    print("=" * 72, flush=True)
    print("STAGE 0 — whisper synthesis verification "
          "(source removed? filter kept?)", flush=True)
    print("=" * 72, flush=True)
    print(f"{'clip':18s} {'orig_f0':>8s} {'whisp_f0':>9s}   "
          f"{'F1 orig->whisp':>16s} {'F2 orig->whisp':>16s}", flush=True)

    def median_f0(sig):
        vals = []
        for i in range(0, len(sig) - LPC_FRAME, LPC_HOP):
            fr = sig[i:i + LPC_FRAME]
            if np.sqrt((fr ** 2).mean()) < 0.01:
                continue
            f0 = N.f0_autocorr(fr.tolist(), FS, 70.0, 400.0, 0.30)
            if f0 > 0:
                vals.append(f0)
        return float(np.median(vals)) if vals else 0.0

    for path, word, sp in files[:n]:
        x, fs = load_wav(path)
        w = synth_whisper(x, seed=0)
        f0_o, f0_w = median_f0(x), median_f0(w)
        best = max(range(0, len(x) - LPC_FRAME, LPC_HOP),
                   key=lambda i: (x[i:i + LPC_FRAME] ** 2).mean())
        fo = N.lpc_formants_bw(x[best:best + LPC_FRAME].tolist(), FS, LPC_ORDER,
                               LPC_PE, 150.0, 3600.0, 600.0)
        fw = N.lpc_formants_bw(w[best:best + LPC_FRAME].tolist(), FS, LPC_ORDER,
                               LPC_PE, 150.0, 3600.0, 600.0)
        # formants come back flat [f1,bw1,f2,bw2,...]
        F1o, F2o = (fo[0] if len(fo) > 0 else 0), (fo[2] if len(fo) > 2 else 0)
        F1w, F2w = (fw[0] if len(fw) > 0 else 0), (fw[2] if len(fw) > 2 else 0)
        name = os.path.basename(path)
        print(f"{name:18s} {f0_o:8.1f} {f0_w:9.1f}   "
              f"{F1o:6.0f}->{F1w:<6.0f}    {F2o:6.0f}->{F2w:<6.0f}", flush=True)
    print("\n  EXPECT: orig_f0 ~100-130 Hz (real pitch); whisp_f0 railed high / "
          "incoherent (no periodicity -> SOURCE removed).", flush=True)
    print("  EXPECT: F1/F2 preserved within estimation noise (FILTER kept).\n",
          flush=True)


# ---------------------------------------------------------------------------
# Native DtwTo nearest-exemplar — IDENTICAL machinery to
# scripts/relational_shape_xspeaker.py.  No numpy in the score; no .fit.
# ---------------------------------------------------------------------------
class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def as_tuple(M):
    return tuple(tuple(float(v) for v in row) for row in np.asarray(M))


def main():
    n_train = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    n_test = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    rng = np.random.default_rng(seed)

    t0 = time.time()
    files = gather_files()
    speakers = sorted({f[2] for f in files})
    chance = 1.0 / len(_DIGITS)
    print("=" * 72, flush=True)
    print("VOICED<->WHISPER INVARIANCE PROBE — FSDD digits, within-speaker", flush=True)
    print("=" * 72, flush=True)
    print(f"speakers: {speakers}  (10-way, chance {100*chance:.1f}%)", flush=True)

    # WITHIN-SPEAKER split: for each (speaker,digit) split clips into train/test by
    # index parity-of-clip so train and test are DISJOINT clips of the SAME speaker.
    by_key = defaultdict(list)
    for path, digit, sp, idx in files:
        by_key[(sp, digit)].append((path, idx))
    train_files, test_files = [], []
    for (sp, digit), lst in by_key.items():
        lst = sorted(lst, key=lambda t: t[1])
        # first ~70% of a speaker-digit's clips -> train exemplars, last ~30% -> test
        cut = int(round(0.7 * len(lst)))
        for p, _ in lst[:cut]:
            train_files.append((p, _DIGITS[digit], sp))
        for p, _ in lst[cut:]:
            test_files.append((p, _DIGITS[digit], sp))
    rng.shuffle(train_files)
    rng.shuffle(test_files)
    train_files = train_files[:n_train]
    test_files = test_files[:n_test]
    print(f"train exemplars (VOICED): {len(train_files)}   "
          f"test clips: {len(test_files)} (DISJOINT clips, same speakers)", flush=True)
    print(f"per-clip resolution: {100.0/max(len(test_files),1):.3f}%\n", flush=True)

    # Verify the whisper synthesis on a handful of test clips first.
    verify_whisper(test_files, n=6)

    # ---- precompute representations ----------------------------------------
    # Train exemplars: VOICED only, three reps each.
    print("computing TRAIN (voiced) representations...", flush=True)
    tr = {"SURFACE": [], "RELATIONAL": [], "SOURCE": []}
    for path, w, sp in train_files:
        x, fs = load_wav(path)
        rs = surface_rep(x, fs)
        rr = relational_rep(x, fs)
        rc = source_rep(x, fs)
        if rs is None or rr is None or rc is None:
            continue
        tr["SURFACE"].append((rs, w))
        tr["RELATIONAL"].append((rr, w))
        tr["SOURCE"].append((rc, w))
    print(f"  usable train exemplars: {len(tr['SURFACE'])}  "
          f"({time.time()-t0:.0f}s)", flush=True)

    # Test clips: each in BOTH conditions (voiced and synth-whisper), three reps.
    print("computing TEST representations (voiced + synth-whisper)...", flush=True)
    te = {("SURFACE", "voiced"): [], ("SURFACE", "whisper"): [],
          ("RELATIONAL", "voiced"): [], ("RELATIONAL", "whisper"): [],
          ("SOURCE", "voiced"): [], ("SOURCE", "whisper"): []}
    for path, w, sp in test_files:
        x, fs = load_wav(path)
        xw = synth_whisper(x, seed=seed)
        for cond, sig in (("voiced", x), ("whisper", xw)):
            rs = surface_rep(sig, fs)
            rr = relational_rep(sig, fs)
            rc = source_rep(sig, fs)
            if rs is None or rr is None or rc is None:
                continue
            te[("SURFACE", cond)].append((rs, w))
            te[("RELATIONAL", cond)].append((rr, w))
            te[("SOURCE", cond)].append((rc, w))
    print(f"  test (voiced): {len(te[('SURFACE','voiced')])}  "
          f"test (whisper): {len(te[('SURFACE','whisper')])}  "
          f"({time.time()-t0:.0f}s)\n", flush=True)

    # ---- native DtwTo nearest-exemplar -------------------------------------
    sub = Substrate()
    sign = sub.add_node("HeardSign", {})
    err = _Pred(RG._DtwTo(RG._Attr(RG._V("s"), "rep"),
                          RG._Attr(RG._V("w"), "rep")))

    def build_lexicon(train_reprs):
        exs = []
        for M, w in train_reprs:
            c = sub.add_node("Exemplar", {"word": w})
            sub.set_attr(c, "rep", as_tuple(M))
            exs.append((c, w))
        return exs

    def score(exs, test_reprs):
        corr = tot = 0
        per_word = defaultdict(lambda: [0, 0])
        for M, w in test_reprs:
            sub.set_attr(sign, "rep", as_tuple(M))
            best_d, best_w = 1e18, None
            for c, ew in exs:
                d = sub.evaluate(err, {"s": sign, "w": c})
                if d < best_d:
                    best_d, best_w = d, ew
            ok = int(best_w == w)
            corr += ok
            tot += 1
            per_word[w][0] += ok
            per_word[w][1] += 1
        return corr, tot, dict(per_word)

    results = {}
    for rep in ("SURFACE", "RELATIONAL", "SOURCE"):
        print("=" * 72, flush=True)
        print(f"ARM {rep} — native DtwTo nearest-exemplar over VOICED exemplars",
              flush=True)
        print("=" * 72, flush=True)
        exs = build_lexicon(tr[rep])
        for cond in ("voiced", "whisper"):
            c, t, pw = score(exs, te[(rep, cond)])
            acc = c / max(t, 1)
            se = (acc * (1 - acc) / max(t, 1)) ** 0.5
            results[(rep, cond)] = {"corr": c, "tot": t, "acc": acc, "se": se}
            print(f"  voiced->{cond:8s}  {c}/{t} = {100*acc:.2f}%  "
                  f"(SE {100*se:.2f}%, chance {100*chance:.1f}%)", flush=True)
        for c, _ in exs:
            sub.remove_node(c)
        print("", flush=True)

    # ---- THE FALSIFIER: drops -------------------------------------------------
    print("=" * 72, flush=True)
    print("VERDICT — voiced->voiced ceiling, voiced->whisper, and THE DROP", flush=True)
    print("=" * 72, flush=True)
    print(f"  {'rep':12s} {'v->v (ceiling)':>16s} {'v->whisper':>14s} "
          f"{'DROP (pts)':>12s} {'DROP (rel)':>11s}", flush=True)
    drops = {}
    for rep in ("SURFACE", "RELATIONAL", "SOURCE"):
        vv = results[(rep, "voiced")]
        vw = results[(rep, "whisper")]
        drop_pts = 100 * (vv["acc"] - vw["acc"])
        drop_rel = (1 - vw["acc"] / vv["acc"]) * 100 if vv["acc"] > 0 else float("nan")
        drops[rep] = drop_pts
        print(f"  {rep:12s} {vv['corr']:>5d}/{vv['tot']:<4d}={100*vv['acc']:5.1f}% "
              f"  {vw['corr']:>4d}/{vw['tot']:<4d}={100*vw['acc']:5.1f}% "
              f"  {drop_pts:+8.1f}    {drop_rel:8.1f}%", flush=True)

    print(f"\n  chance = {100*chance:.1f}%", flush=True)
    print("\n  PREDICTION: RELATIONAL small drop (reads the FILTER) = PASS; "
          "SURFACE larger drop;\n  SOURCE collapses toward chance "
          "(no periodicity in whisper) = the test discriminates.", flush=True)

    rel_drop = drops["RELATIONAL"]
    src_drop = drops["SOURCE"]
    surf_drop = drops["SURFACE"]
    src_floor = results[("SOURCE", "whisper")]["acc"]
    # READ THE NUMBERS, not a boolean — but summarise the observed pattern.
    print("\n  OBSERVED PATTERN:", flush=True)
    if src_drop > rel_drop and src_floor <= chance + 0.10 and rel_drop < surf_drop + 5:
        print("  >>> PREDICTED SIGNATURE: SOURCE collapses (proving the test "
              "discriminates) while\n      RELATIONAL survives the source ablation "
              "better than SURFACE. The winning\n      relational shape reads "
              "structure in the FILTER, invariant to the source\n      "
              "serialization. FALSIFIER PASSES relational.", flush=True)
    elif src_drop > rel_drop and src_floor <= chance + 0.10:
        print("  >>> TEST DISCRIMINATES (SOURCE collapsed) but RELATIONAL did not "
              "clearly beat\n      SURFACE on the drop. Report both drops plainly.",
              flush=True)
    elif rel_drop >= src_drop or rel_drop > surf_drop + 5:
        print("  >>> FALSIFIER FAILS RELATIONAL: the relational shape drops AS MUCH "
              "AS (or more\n      than) the source / surface arms on whisper -> it "
              "was source-dependent\n      after all. Honest, important result — "
              "report the numbers.", flush=True)
    else:
        print("  >>> MIXED / UNEXPECTED pattern. Report every cell's k/N and the "
              "drops as-is;\n      do NOT sweep or manufacture a story.", flush=True)

    print(f"\n  total wall: {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
