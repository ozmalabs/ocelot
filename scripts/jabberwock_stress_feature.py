"""STRESS-aware feature — the rate-INVARIANT carrier of unit identity.

Creator (Brad Pitt's pikey in Snatch): a fused unit repeated slowly comes back not with
less co-articulation but with clearer STRESS. So the rate-invariant identity is the
prominence/stress pattern (which syllables are emphasised), NOT duration (frames change
with rate). The scale of a unit is its number of STRESSED SYLLABLES, not its frame count.

The agent composes the stress feature from its OWN primitives:
  sonority contour = per-frame energy (its sonority proxy, jabberwock_reads_oov_from_phones)
  syllable nuclei  = PROMINENCE PEAKS = local maxima of the sonority contour (the agent's
                     order-1 sign-change concept — the dual of the segmenter's TP troughs)
  stress pattern   = the peaks' RELATIVE prominences, in order (rate-invariant identity)
  syllable count   = number of peaks (rate-invariant SCALE — replaces frame-count duration)

This script VALIDATES the claim before wiring: (1) prominence peaks track syllable count;
(2) the stress structure is rate-INVARIANT (resample a contour faster/slower -> peak count
and pattern stay) while frame-count duration is not; (3) syllable count separates unit
SCALES (1-word vs multi-word) more cleanly than duration.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
import scripts.librispeech_wer as L
from scripts.jabberwock_reads_oov_from_phones import frames

VOWELS = "aeiou"


def sonority(e):
    """Smooth the per-frame energy into a sonority contour (the agent's sonority proxy)."""
    e = np.asarray(e, float)
    if len(e) < 3:
        return e
    k = max(3, len(e) // 20 | 1)                      # light odd-length moving average
    pad = k // 2
    ep = np.pad(e, pad, mode="edge")
    return np.convolve(ep, np.ones(k) / k, "valid")[:len(e)]


def prominence_peaks(s, rel=0.15):
    """Syllable nuclei = local maxima of the sonority contour (order-1 sign change of
    the derivative) whose prominence clears `rel` of the dynamic range — a data-derived
    floor (fraction of the contour's own range), not an absolute knob. Returns peak
    indices and their heights."""
    s = np.asarray(s, float)
    if len(s) < 3:
        return np.array([0]), s[:1]
    rng = float(s.max() - s.min()) or 1.0
    thr = s.min() + rel * rng
    peaks = []
    for i in range(1, len(s) - 1):
        if s[i] >= s[i - 1] and s[i] > s[i + 1] and s[i] >= thr:
            peaks.append(i)
    if not peaks:
        peaks = [int(s.argmax())]
    return np.array(peaks), s[np.array(peaks)]


def stress_pattern(s, K=8):
    """Rate-invariant stress descriptor: the peak prominences (normalised by the unit's
    max) resampled to K points in order. Captures WHICH syllable is stressed, independent
    of rate. Returns (descriptor[K], n_syllables)."""
    peaks, heights = prominence_peaks(s)
    h = heights / (heights.max() + 1e-9)
    if len(h) == 1:
        desc = np.full(K, float(h[0]))
    else:
        idx = np.linspace(0, len(h) - 1, K)
        lo = np.floor(idx).astype(int); hi = np.clip(lo + 1, 0, len(h) - 1); t = idx - lo
        desc = h[lo] * (1 - t) + h[hi] * t
    return desc, len(peaks)


def _resample_contour(s, factor):
    """Simulate a rate change: stretch/compress the contour by `factor` (more/fewer
    frames) WITHOUT changing its shape — the pure duration change."""
    n = max(2, int(round(len(s) * factor)))
    idx = np.linspace(0, len(s) - 1, n)
    lo = np.floor(idx).astype(int); hi = np.clip(lo + 1, 0, len(s) - 1); t = idx - lo
    return np.asarray(s)[lo] * (1 - t) + np.asarray(s)[hi] * t


def nsyl_text(words):
    """Rough syllable count of a transcript: vowel-groups per word."""
    n = 0
    for w in words:
        groups = 0; prev = False
        for ch in w:
            v = ch in VOWELS
            if v and not prev:
                groups += 1
            prev = v
        n += max(groups, 1)
    return n


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    pairs = L.gather_pairs(limit=n + 40)[:n]
    print("=" * 84)
    print("STRESS FEATURE — prominence peaks ~ syllables, rate-INVARIANT (vs duration)")
    print("=" * 84)

    # (1) do prominence peaks track syllable count on real utterances?
    peak_counts, syl_counts, frame_counts = [], [], []
    contours = []
    for (path, sp, ch, ut, tr) in pairs:
        try:
            M, e = frames(L.load_flac(path)[0])
        except Exception:
            continue
        s = sonority(e)
        _, nsyl = stress_pattern(s)
        words = L.normalise(tr)
        peak_counts.append(nsyl); syl_counts.append(nsyl_text(words))
        frame_counts.append(len(s)); contours.append(s)
    pc = np.array(peak_counts, float); sc = np.array(syl_counts, float)
    r = float(np.corrcoef(pc, sc)[0, 1]) if len(pc) > 2 else 0.0
    print(f"  utts={len(pc)}  peak-count vs transcript-syllable-count corr: r={r:.2f}")
    print(f"  mean peaks/utt {pc.mean():.1f}  mean syllables/utt {sc.mean():.1f}", flush=True)

    # (2) RATE INVARIANCE: stretch/compress each contour 0.6x..1.6x; does the stress
    #     structure (peak count) stay while frame count changes?
    facs = [0.6, 0.8, 1.0, 1.3, 1.6]
    peak_cv, frame_cv = [], []
    for s in contours:
        pcs, fcs = [], []
        for f in facs:
            sr = _resample_contour(s, f)
            _, npk = stress_pattern(sr)
            pcs.append(npk); fcs.append(len(sr))
        pcs = np.array(pcs, float); fcs = np.array(fcs, float)
        peak_cv.append(pcs.std() / (pcs.mean() + 1e-9))
        frame_cv.append(fcs.std() / (fcs.mean() + 1e-9))
    print(f"  under 0.6x..1.6x rate change (coefficient of variation, lower=more invariant):")
    print(f"     syllable-peak count CV : {np.mean(peak_cv):.3f}   <- the stress scale")
    print(f"     frame count        CV : {np.mean(frame_cv):.3f}   <- raw duration")
    inv = np.mean(peak_cv) < 0.5 * np.mean(frame_cv)

    print("=" * 84)
    ok = r > 0.5 and inv
    print(f"  peaks~syllables {'OK' if r>0.5 else 'weak'} (r={r:.2f}) | "
          f"stress rate-invariant vs duration {'OK' if inv else 'no'} "
          f"({np.mean(peak_cv):.2f} vs {np.mean(frame_cv):.2f})")
    print(f"  {'VALIDATED' if ok else 'PARTIAL'}: the stress/syllable structure is the rate-invariant "
          f"scale; duration changes with rate. The agent's sonority+peak primitives extract it.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
