"""iter-25b FSDD LOSO — the FAITHFUL enactment of the agent's LPC spec: TRUE formant
frequencies from LPC roots of the raw WAVEFORM (bypassing the gammatone band wall),
then the agent's iter-24 spacing relation over the LOG formant positions.

The band-spectrum smoothing (iter25_fsdd_loso) inherits the agent's own gammatone wall
(only ~handful of bands in the formant region, so the all-pole fit saturates at ~2
resolvable peaks -> spacings collapse to zeros). This script enacts the agent's spec
as written (autocorrelation of the pre-emphasised waveform -> Levinson -> roots of
A(z) -> pole angles = formant Hz), recovering formants at full waveform resolution.

Compares, on identical held-out-speaker splits (same kNN-DTW LOSO recogniser):
  BASELINE     : invariant_transform band matrix (confirmed ~0.785)            [0.544 here]
  FORMANT-SPACE: iter-24 spacing relation over waveform-LPC TRUE formant positions

Run: python -m scripts.iter25_fsdd_audio [n_per_speaker]
"""
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import domains.invariant_units as IU
import scripts.fsdd_learner_world as fl
from scripts.iter12_xspeaker import build_corpus, recognise_loso, DIGITS
from domains.lpc_formant_representation import (
    formant_spacings_from_audio, formant_count_from_audio,
)


def _agent_lpc_order(fs=8000):
    try:
        return int(fs / 1000) + 2     # agent's spec rule for waveform LPC
    except Exception:
        return 10


def build_audio_corpus(feat_fn, n_per_speaker=6, seed=0):
    """Parallel to build_corpus, but each entry's matrix is the formant-spacing
    feature computed from the raw waveform (feat_fn(x, fs) -> frames x k)."""
    rng = np.random.default_rng(seed)
    files = fl.gather_files()
    buckets = defaultdict(list)
    for path, d, spk, idx in files:
        buckets[(d, spk)].append(path)
    corpus = []
    cnts = []
    for (d, spk), paths in sorted(buckets.items()):
        paths = sorted(paths)
        rng.shuffle(paths)
        for p in paths[:n_per_speaker]:
            x, fs = fl.load_wav(p)
            F = feat_fn(x, fs)
            if F.shape[0] >= 2:
                corpus.append((F, DIGITS[d], spk))
                if len(cnts) < 60:
                    cnts.append(formant_count_from_audio(x, fs)["mean"])
    return corpus, (float(np.mean(cnts)) if cnts else 0.0)


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    nsp = int(os.environ.get("NSPACINGS", "4"))
    order = int(os.environ.get("LPC_ORDER", str(_agent_lpc_order())))

    # Baseline band-matrix corpus (the confirmed path).
    corpus = build_corpus(n_per_speaker=n_per, seed=0)
    canonical = IU.canonical_log_centroid([M for M, _, _ in corpus])
    print("=== iter-25b FSDD LOSO: waveform-LPC TRUE formant spacings ===")
    print(f"corpus: {len(corpus)} utts, n_per_speaker={n_per}, n_spacings={nsp}, "
          f"LPC order={order} [agent spec]\n")

    print("--- BASELINE invariant_transform (confirmed ~0.785) ---")
    b_acc, b_uni = recognise_loso(
        corpus, lambda M, spk=None: IU.invariant_transform(M, canonical),
        verbose=True)
    print(f"  MEAN acc {b_acc:.3f}  unigram {b_uni:.3f}\n")

    def feat(x, fs):
        return formant_spacings_from_audio(x, fs, n_spacings=nsp, order=order)

    fcorpus, fmt_mean = build_audio_corpus(feat, n_per_speaker=n_per, seed=0)
    print(f"  waveform-LPC formants/frame mean: {fmt_mean:.2f} "
          f"(target: the 2-3 true formants)")
    print("--- FORMANT-SPACE (iter-24 spacing over waveform-LPC formants) ---")
    f_acc, f_uni = recognise_loso(
        fcorpus, lambda M, spk=None: M, verbose=True)
    print(f"  MEAN acc {f_acc:.3f}  unigram {f_uni:.3f}\n")

    print("=" * 60)
    print(f"  BASELINE      {b_acc:.3f}   (confirmed ~0.785)")
    print(f"  FORMANT-SPACE {f_acc:.3f}   (iter-24 raw-peak spacing was 0.253)")
    print("=" * 60)


if __name__ == "__main__":
    main()
