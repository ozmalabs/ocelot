"""invariant_units_accept — does forward VTLN+CMVN (mined from Kaldi, designed
from the agent's own VTL science) crack the speaker-invariant-unit bottleneck?

Acceptance criterion 1 (this script): FSDD digits, 6 speakers, leave-one-
speaker-out 1-NN WORD accuracy — RAW units vs INVARIANT units. The exact metric
the Whisper mine used (agent raw front-end = 0.58 DTW). Should RISE if VTLN+CMVN
make units cluster the WORD, not the SPEAKER.

We operate on the agent's frames x BANDS trajectory (32 log-spaced gammatone
bands) — VTLN must warp the true log-frequency axis, so we normalize BEFORE the
patch collapse. Both cosine (mean-pooled) and DTW (the agent's real compare path)
are reported, raw vs invariant.

The VTL warp α is estimated FORWARD from each utterance's own formant
centre-of-mass vs the cohort canonical — never swept to maximize the score.

Run: python -m scripts.invariant_units_accept [n_per_speaker_per_digit]
"""
import sys
import math
import numpy as np

sys.path.insert(0, '/home/matt/ozma/internal/research/experiments/gamma-substrate')

from scripts.mine_whisper import (gather, load_wav, gammatone_env, BANDS,
                                   silhouette_by_word, loso_1nn)
from domains.invariant_units import (invariant_transform, canonical_log_centroid)


def band_trajectory_matrix(x, fs, n_frames=32):
    """The agent's gammatone BAND trajectory as frames x bands (32 log-bands),
    BEFORE the patch collapse — so VTLN warps the true log-frequency axis. Same
    gammatone+envelope front-end as the mine harness; we just keep bands not
    patches. No global normalization here (CMVN handles per-utterance norm)."""
    envs = [gammatone_env(x, fs, fc) for fc in BANDS]   # each: time-samples
    # duration LPF per band (same ~80ms sustained smoothing as the patch path)
    cut = 1000.0 / (2 * math.pi * 80.0)
    tau = 1.0 / (2 * math.pi * cut)
    a = math.exp(-1.0 / (tau * fs))
    smoothed = []
    for env in envs:
        sm = np.empty_like(env)
        acc = 0.0
        for i in range(len(env)):
            acc = a * acc + (1 - a) * env[i]
            sm[i] = acc
        smoothed.append(sm)
    n_src = len(smoothed[0])
    rows = []
    for tf in range(n_frames):
        sp = tf * n_src / n_frames
        i0 = int(sp); i1 = min(i0 + 1, n_src - 1); frac = sp - i0
        rows.append([buf[i0] * (1 - frac) + buf[i1] * frac for buf in smoothed])
    return np.array(rows, dtype=np.float32)            # frames x bands


def l2_pool(M):
    """Mean-pool over frames then unit-L2 — the cosine path's word vector."""
    v = M.mean(axis=0).astype(np.float32)
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def l2_flat(M):
    """Flatten frames x bands then unit-L2 — the cosine path on the full traj."""
    v = M.flatten().astype(np.float32)
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def dtw(A, B, band=8):
    """Banded DTW over frames (Euclidean per-frame). The agent's real compare."""
    nf = A.shape[0]
    INF = 1e18
    prev = [INF] * (nf + 1); prev[0] = 0.0
    for i in range(1, nf + 1):
        cur = [INF] * (nf + 1)
        jl = max(1, i - band); jh = min(nf, i + band)
        for j in range(jl, jh + 1):
            d = float(np.linalg.norm(A[i - 1] - B[j - 1]))
            cur[j] = d + min(prev[j], cur[j - 1], prev[j - 1])
        prev = cur
    return prev[nf] / nf


def loso_dtw(matrices, words, speakers):
    words = np.asarray(words); speakers = np.asarray(speakers)
    corr = tot = 0
    for held in set(speakers):
        te = np.where(speakers == held)[0]
        tr = np.where(speakers != held)[0]
        for i in te:
            best, bw = 1e18, None
            for j in tr:
                d = dtw(matrices[i], matrices[j])
                if d < best:
                    best, bw = d, words[j]
            corr += int(bw == words[i]); tot += 1
    return corr / max(tot, 1)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    items = gather(n_per_class_per_speaker=n)
    audio = [(*load_wav(p), str(d), s) for p, d, s in items]
    words = [a[2] for a in audio]
    speakers = [a[3] for a in audio]
    print(f"FSDD: {len(audio)} recordings, {len(set(speakers))} speakers, "
          f"{len(set(words))} digits")

    # Raw band trajectories.
    raw_M = [band_trajectory_matrix(x, fs) for x, fs, _, _ in audio]

    # Cohort canonical tract (mean log-centroid) — the VTLN reference.
    canonical = canonical_log_centroid(raw_M)
    print(f"cohort canonical log-centroid (VTLN reference): {canonical:.4f} "
          f"(= {math.exp(canonical):.0f} Hz)")

    # INVARIANT: forward-VTLN warp to canonical + CMVN. Per-utterance, no search.
    inv_M = [invariant_transform(M, canonical) for M in raw_M]

    # Report the spread of estimated warp factors (sanity: it varies by speaker).
    from domains.invariant_units import estimate_vtl_logalpha
    alphas = {}
    for (M, (_, _, _, spk)) in zip(raw_M, audio):
        alphas.setdefault(spk, []).append(
            math.exp(estimate_vtl_logalpha(M, canonical)))
    print("per-speaker mean forward-VTLN α (estimated, not swept):")
    for spk in sorted(alphas):
        print(f"    {spk:10s} α={np.mean(alphas[spk]):.3f}")

    print("\n================= LOSO-1NN WORD ACCURACY (raw vs invariant) "
          "=================")
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

    raw_dtw = row("RAW band trajectory (no norm)", raw_M)
    inv_dtw = row("INVARIANT (forward-VTLN + CMVN)", inv_M)

    # Ablations: each mechanism alone.
    from domains.invariant_units import invariant_transform as it
    vtln_only = [it(M, canonical, do_vtln=True, do_cmvn=False) for M in raw_M]
    cmvn_only = [it(M, canonical, do_vtln=False, do_cmvn=True) for M in raw_M]
    row("  VTLN only", vtln_only)
    row("  CMVN only", cmvn_only)

    print(f"\nDTW LOSO: raw {raw_dtw:.3f} -> invariant {inv_dtw:.3f}  "
          f"(Δ {inv_dtw - raw_dtw:+.3f})")
    print("Whisper-mine reference: agent raw front-end DTW LOSO = 0.578; "
          "Whisper log-mel = 0.289; Whisper final encoder = 0.806.")


if __name__ == "__main__":
    main()
