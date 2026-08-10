"""invariant_units_patch_accept — criterion 1 on the agent's REAL front-end path
(the 25 A1 patches, where the Whisper-mine 0.578 DTW LOSO lives).

Pipeline: gammatone 32 bands -> [forward-VTLN warp on the band axis] ->
[CMVN over frames on the band axis] -> A1 patch collapse (Gaussian band->patch)
-> DTW / cosine LOSO. Raw (no norm) vs invariant, on the patch representation
the mine measured at 0.578. The VTL warp α is forward-estimated per utterance
from its own formant centre-of-mass; CMVN is per-utterance mean(-var) removal.
Nothing is swept.

Run: python -m scripts.invariant_units_patch_accept [n_per_speaker_per_digit]
"""
import sys
import math
import numpy as np

sys.path.insert(0, '/home/matt/ozma/internal/research/experiments/gamma-substrate')

from scripts.mine_whisper import (gather, load_wav, BANDS, _PATCHES,
                                   silhouette_by_word, loso_1nn)
from scripts.invariant_units_accept import (band_trajectory_matrix, l2_pool,
                                            l2_flat, loso_dtw)
from domains.invariant_units import (invariant_transform, canonical_log_centroid)


_BC = np.array(BANDS)
# Precompute the Gaussian band->patch weights (sorted patch order, as the mine).
_W = []
for name, c, sigma in _PATCHES:
    w = np.exp(-0.5 * ((_BC - c) / sigma) ** 2)
    w = w / (w.sum() + 1e-9)
    _W.append(w)
_W = np.array(_W)                      # patches x bands


def bands_to_patches(M):
    """Collapse frames x bands -> frames x patches via the A1 Gaussian patches
    (the agent's real front-end). M may be CMVN-centred (can go negative); the
    linear patch sum is still well-defined."""
    return (M @ _W.T).astype(np.float32)   # frames x patches


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    items = gather(n_per_class_per_speaker=n)
    audio = [(*load_wav(p), str(d), s) for p, d, s in items]
    words = [a[2] for a in audio]
    speakers = [a[3] for a in audio]
    print(f"FSDD: {len(audio)} recordings, {len(set(speakers))} speakers, "
          f"{len(set(words))} digits")

    raw_bands = [band_trajectory_matrix(x, fs) for x, fs, _, _ in audio]
    canonical = canonical_log_centroid(raw_bands)

    # RAW patch path = bands -> patches (no normalization). This reproduces the
    # mine's 0.578-DTW front-end.
    raw_patch = [bands_to_patches(M) for M in raw_bands]

    def make(do_vtln, do_cmvn, do_var=True):
        out = []
        for M in raw_bands:
            t = invariant_transform(M, canonical, do_vtln=do_vtln,
                                    do_cmvn=do_cmvn, do_variance=do_var)
            out.append(bands_to_patches(t))
        return out

    inv_patch = make(True, True)
    vtln_patch = make(True, False)
    cmvn_patch = make(False, True)
    cmvn_mean_patch = make(False, True, do_var=False)

    # Per-SPEAKER VTLN (Kaldi's real granularity): estimate ONE warp per speaker
    # by averaging the formant centroid over all that speaker's utterances —
    # which averages OUT phonetic content, isolating vocal-tract length. This is
    # the honest forward VTLN (still no likelihood sweep). Then + CMVN.
    from domains.invariant_units import (estimate_vtl_logalpha, warp_bands, cmvn)
    spk_la = {}
    spk_acc = {}
    for M, (_, _, _, spk) in zip(raw_bands, audio):
        spk_acc.setdefault(spk, []).append(estimate_vtl_logalpha(M, canonical))
    for spk, las in spk_acc.items():
        spk_la[spk] = float(np.mean(las))
    spkvtln_patch = []
    spkvtln_cmvn_patch = []
    for M, (_, _, _, spk) in zip(raw_bands, audio):
        w = warp_bands(M, spk_la[spk])
        spkvtln_patch.append(bands_to_patches(w))
        spkvtln_cmvn_patch.append(bands_to_patches(cmvn(w, do_variance=True)))

    print("\n=========== LOSO-1NN WORD ACCURACY on the A1 PATCH path "
          "===========")
    print(f"{'representation':40s}{'sil(word)':>11s}{'cos-pool':>10s}"
          f"{'cos-flat':>10s}{'DTW':>8s}")

    def row(tag, Ms):
        Xp = [l2_pool(M) for M in Ms]
        Xf = [l2_flat(M) for M in Ms]
        sil = silhouette_by_word(Xf, words)
        cp = loso_1nn(Xp, words, speakers)
        cf = loso_1nn(Xf, words, speakers)
        dt = loso_dtw(Ms, words, speakers)
        print(f"{tag:40s}{sil:>+11.3f}{cp:>10.3f}{cf:>10.3f}{dt:>8.3f}")
        return dt

    raw = row("RAW patches (mine: ~0.578 DTW)", raw_patch)
    inv = row("INVARIANT (VTLN + CMVN-var)", inv_patch)
    row("  VTLN only", vtln_patch)
    row("  CMVN (mean+var)", cmvn_patch)
    row("  CMVN (mean only)", cmvn_mean_patch)
    row("  per-speaker VTLN only", spkvtln_patch)
    row("  per-speaker VTLN + CMVN", spkvtln_cmvn_patch)

    print(f"\nDTW LOSO on patch path: raw {raw:.3f} -> invariant {inv:.3f}  "
          f"(Δ {inv - raw:+.3f})")
    print("Whisper-mine ref: agent raw patch front-end DTW LOSO = 0.578; "
          "Whisper final encoder = 0.806.")


if __name__ == "__main__":
    main()
