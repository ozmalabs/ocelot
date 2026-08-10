"""Acceptance test for the agent's WARPED formant-dense cochlear front-end.

The agent (domains.runtime_design.agent_specify_frontend) claimed its
ArgMax-over-cochlear-bands formant is blunt because only ~16 of its 32
log-spaced bands fall in 250-2500 Hz; it asked to warp the layout to
oversample that region and raise the A1 patch count. This script tests
that claim DIRECTLY and downstream, honestly.

(a) FORMANT TRACKING — synth vowels with KNOWN F1/F2, run the real
    gammatone primitive per band on both layouts, measure how precisely
    the agent's ArgMax-over-bands peak tracks the true formant (Hz error).
(b) DISCRIMINATION — on gammatone-confused FSDD pairs, does the warped
    front-end's gammatone band-energy formant cue separate them better
    (Fisher ratio) than uniform?
(c) RECOGNITION — held-out-speaker FSDD, uniform vs warped, gammatone
    ear only (full pipeline).

Run: python3 scripts/formant_frontend_accept.py
"""
import os, sys, math, random
sys.path.insert(0, os.path.join(os.getcwd(), "runners/dsl/python"))
sys.path.insert(0, os.getcwd())
random.seed(7)
import numpy as np

from domains.stt_pipeline import DEFAULT_BANDS
from domains.formant_frontend import warped_band_centres

UNIFORM = list(DEFAULT_BANDS)
WARPED = warped_band_centres()


# ---------------------------------------------------------------------------
# Exact replica of audio_primitives.rs::gammatone_band (the primitive the
# pipeline runs). taps=256, b = 2π·1.019·(24.7+0.108·fc), unit-L2, "same".
# ---------------------------------------------------------------------------
def gammatone_band(samples: np.ndarray, fs: int, fc: float, order: int = 4) -> np.ndarray:
    n_taps = 256
    b = 2.0 * math.pi * 1.019 * (24.7 + 0.108 * fc)
    t = np.arange(n_taps, dtype=np.float64) / fs
    impulse = (t ** (order - 1)) * np.exp(-b * t) * np.cos(2.0 * math.pi * fc * t)
    energy = math.sqrt(float(np.sum(impulse * impulse)))
    if energy > 0:
        impulse = impulse / energy
    # "same"-mode convolution centred (pad = m//2), matching the Rust loop.
    return np.convolve(samples.astype(np.float64), impulse, mode="same")


def band_energies(x: np.ndarray, fs: int, centres) -> np.ndarray:
    """Per-band RMS energy — the cochlear band-activation vector the
    agent's ArgMax formant primitive reads."""
    out = np.empty(len(centres))
    for i, fc in enumerate(centres):
        band = gammatone_band(x, fs, fc)
        out[i] = math.sqrt(float(np.mean(band * band)) + 1e-20)
    return out


def argmax_formant(x, fs, centres, lo, hi):
    """The AGENT'S formant primitive: ArgMax over cochlear bands within
    [lo,hi] -> the center frequency of the most-active band. Blunt
    exactly to the band grid."""
    e = band_energies(x, fs, centres)
    idx = [i for i, fc in enumerate(centres) if lo <= fc <= hi]
    if not idx:
        return float("nan")
    best = max(idx, key=lambda i: e[i])
    return centres[best]


# ---------------------------------------------------------------------------
# (a) FORMANT TRACKING — synthetic vowels with known F1/F2.
# ---------------------------------------------------------------------------
def synth_vowel(f1, f2, f3, fs=8000, dur=0.30, f0=120.0):
    """Source-filter vowel: glottal pulse train through 3 formant
    resonators. Known F1/F2/F3."""
    n = int(dur * fs)
    # Impulse train (glottal source).
    src = np.zeros(n)
    period = int(fs / f0)
    src[::period] = 1.0
    sig = src.copy()
    for fc, bw in [(f1, 80), (f2, 100), (f3, 120)]:
        r = math.exp(-math.pi * bw / fs)
        theta = 2.0 * math.pi * fc / fs
        a1 = -2.0 * r * math.cos(theta)
        a2 = r * r
        y = np.zeros(n)
        for i in range(n):
            y[i] = sig[i] - a1 * (y[i - 1] if i >= 1 else 0.0) \
                          - a2 * (y[i - 2] if i >= 2 else 0.0)
        sig = y
    sig = sig / (np.max(np.abs(sig)) + 1e-9)
    return sig.astype(np.float32)


# Canonical American-English vowel formants (Hz) — Peterson & Barney-ish.
VOWELS = {
    "iy": (270, 2290, 3010),
    "ih": (390, 1990, 2550),
    "eh": (530, 1840, 2480),
    "ae": (660, 1720, 2410),
    "aa": (730, 1090, 2440),
    "ao": (570, 840, 2410),
    "uh": (440, 1020, 2240),
    "uw": (300, 870, 2240),
}
FS = 8000


def formant_tracking():
    print("=" * 72)
    print("(a) FORMANT TRACKING — agent's ArgMax-over-bands vs known F1/F2")
    print("    (synthetic source-filter vowels, fs=8000)")
    print("=" * 72)
    rows = []
    for layout_name, centres in [("uniform-32", UNIFORM), ("warped-32", WARPED)]:
        f1_err, f2_err = [], []
        for vname, (f1, f2, f3) in VOWELS.items():
            x = synth_vowel(f1, f2, f3, fs=FS)
            est_f1 = argmax_formant(x, FS, centres, 250, 1000)
            est_f2 = argmax_formant(x, FS, centres, 1000, 2500)
            f1_err.append(abs(est_f1 - f1))
            f2_err.append(abs(est_f2 - f2))
        rows.append((layout_name, np.mean(f1_err), np.mean(f2_err),
                     np.mean(f1_err) + np.mean(f2_err)))
        print(f"  {layout_name:11s}  F1 mean-err = {np.mean(f1_err):6.1f} Hz   "
              f"F2 mean-err = {np.mean(f2_err):6.1f} Hz   "
              f"(F1+F2 = {np.mean(f1_err)+np.mean(f2_err):6.1f} Hz)")
    u, w = rows[0], rows[1]
    print(f"\n  Δ(warped - uniform): F1 {w[1]-u[1]:+.1f} Hz, F2 {w[2]-u[2]:+.1f} Hz, "
          f"total {w[3]-u[3]:+.1f} Hz  "
          f"({'SHARPER' if w[3] < u[3] else 'NOT sharper'})")
    return rows


# ---------------------------------------------------------------------------
# (b) DISCRIMINATION — Fisher ratio on gammatone-confused FSDD pairs.
# ---------------------------------------------------------------------------
import wave

FSDD = "/tmp/fsdd/recordings"


def load_fsdd(path):
    w = wave.open(path)
    r = (np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
         .astype(np.float32) / 32768.0)
    fr = w.getframerate()
    if fr != FS:  # FSDD is 8000 already, but be safe.
        step = max(1, fr // FS)
        r = r[::step]
    return r


def fsdd_files(digits, per=30):
    out = {}
    if not os.path.isdir(FSDD):
        return out
    for d in digits:
        fs = [f for f in sorted(os.listdir(FSDD))
              if f.startswith(f"{d}_") and f.endswith(".wav")]
        random.shuffle(fs)
        out[d] = [os.path.join(FSDD, f) for f in fs[:per]]
    return out


def formant_cue(x, centres):
    """A gammatone-only formant cue vector: [F1, F2, F2/F1] from the
    agent's ArgMax-over-bands primitive. Pure cochlear, no FFT ear."""
    f1 = argmax_formant(x, FS, centres, 250, 1000)
    f2 = argmax_formant(x, FS, centres, 1000, 2500)
    return np.array([f1, f2, (f2 + 1) / (f1 + 1)])


def fisher(a, b):
    """Multivariate Fisher ratio (trace form) between two clouds."""
    a, b = np.array(a), np.array(b)
    mu = (a.mean(0) - b.mean(0))
    sw = a.var(0) + b.var(0) + 1e-9
    return float(np.sum(mu * mu / sw))


CONFUSED_PAIRS = [("2", "3"), ("7", "9"), ("1", "9"), ("5", "9"), ("6", "8")]


def discrimination():
    print("\n" + "=" * 72)
    print("(b) DISCRIMINATION — Fisher ratio of the gammatone formant cue")
    print("    on FSDD confused pairs (higher = better separation)")
    print("=" * 72)
    digits = sorted({d for p in CONFUSED_PAIRS for d in p})
    files = fsdd_files(digits, per=40)
    if not files:
        print("  [FSDD not found at", FSDD, "- skipping]")
        return
    cues = {name: {} for name in ("uniform", "warped")}
    for name, centres in [("uniform", UNIFORM), ("warped", WARPED)]:
        for d in digits:
            cues[name][d] = np.array([formant_cue(load_fsdd(p), centres)
                                       for p in files[d]])
    print(f"  {'pair':8s} {'uniform':>10s} {'warped':>10s}  verdict")
    u_tot = w_tot = 0.0
    for a, b in CONFUSED_PAIRS:
        fu = fisher(cues["uniform"][a], cues["uniform"][b])
        fw = fisher(cues["warped"][a], cues["warped"][b])
        u_tot += fu; w_tot += fw
        print(f"  {a}/{b:6s} {fu:10.3f} {fw:10.3f}  "
              f"{'warped+' if fw > fu else 'uniform+'}")
    print(f"  {'MEAN':8s} {u_tot/len(CONFUSED_PAIRS):10.3f} "
          f"{w_tot/len(CONFUSED_PAIRS):10.3f}  "
          f"{'WARPED SEPARATES BETTER' if w_tot > u_tot else 'no improvement'}")


# ---------------------------------------------------------------------------
# (c) RECOGNITION — held-out-speaker FSDD via the real pipeline.
# ---------------------------------------------------------------------------
def recognition():
    print("\n" + "=" * 72)
    print("(c) RECOGNITION — held-out speaker (jackson), gammatone ear only")
    print("=" * 72)
    try:
        from substrate_rs import Substrate
        import scripts.fsdd_learner_world as fl
        from domains.stt_pipeline import STTPipeline, STTParams
        from domains.speech_cortex import SpeechCortex
        from domains.acoustic_resolution import _root
    except Exception as e:
        print("  [skipped — import failed:", e, "]")
        return

    af = fl.gather_files(limit=None)

    def nrm(v):
        n = np.linalg.norm(v)
        return v / n if n > 0 else v

    def run(params, label):
        sub = Substrate()
        pipe = STTPipeline(params)
        pipe.attach(sub)
        pipe._ensure_audio_pipeline(sub)
        SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()
        sub.set_attr(_root(sub), "resolution", 12)

        def feats(path):
            s, fs = fl.load_wav(path)
            pipe.ingest(sub, s); sub.tick(50000)
            st = None
            for n in sub.nodes("AudioStream"):
                st = n
            sg = fl._collect_signs_from_stream(sub, st) if st else []
            g = []
            for sid in sg:
                t = sub.node(sid)["attrs"].get("trajectory")
                if t:
                    g.append(np.array(t, dtype=float))
            return nrm(np.mean(g, 0)) if g else None

        tr, te = [], []
        for path, digit, sp, idx in af:
            r = feats(path)
            if r is None:
                continue
            (te if sp == "jackson" else tr).append((digit, r))

        def knn(q, k=5):
            sims = sorted(((float(np.dot(q, g)), d) for d, g in tr), reverse=True)
            from collections import Counter
            return Counter(d for _, d in sims[:k]).most_common(1)[0][0]

        ok = sum(knn(g) == d for d, g in te)
        print(f"  {label:18s}: {100*ok/len(te):.0f}%  "
              f"({ok}/{len(te)} held-out, 10-way, chance 10%)")
        return ok, len(te)

    run(STTParams(sample_rate=8000), "uniform-32")
    run(STTParams.warped(sample_rate=8000), "warped-32")


if __name__ == "__main__":
    print("WARPED layout: %d bands in 250-2500 Hz vs %d uniform\n" % (
        sum(1 for f in WARPED if 250 <= f <= 2500),
        sum(1 for f in UNIFORM if 250 <= f <= 2500)))
    formant_tracking()
    discrimination()
    recognition()
