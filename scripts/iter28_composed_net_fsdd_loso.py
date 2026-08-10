"""iter-28 FSDD LOSO — does the agent's small COMPOSED net (write-not-train) over the
band-mean frames BEAT the iter-27 weighted recognizer (0.333) and approach / clear the
BASELINE (0.567 here, confirmed ~0.785)?

Gated by RECOGNITION ACCURACY, leave-one-speaker-out, kNN-DTW (the baseline's own metric).
Representations head-to-head on identical clips, from the SAME baseline band-mean frames:
  BASELINE      : invariant_transform band matrix kNN-DTW (confirmed ~0.785) [~0.567 here]
  COMPOSED-NET  : the agent's composed per-band net  b -> [b, b^2, b^3, b_t - b_{t-1}]
                  (write-not-train: weights rendered by the gadget constructor, no fit)
  shuffle / unigram controls.

Per held-out speaker, the COMPOSED-NET path derives its band-domain scale from the TRAIN
speakers ONLY (no leakage), applies the agent's composed net (composed ONCE up front) to
each clip's invariant frames, and classifies with kNN-DTW. The net's WEIGHTS are
identical across folds (authored from understanding, not fit) — only the fixed domain
scale is train-derived.

Run: python -m scripts.iter28_composed_net_fsdd_loso [n_per_speaker]
"""
import os
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import domains.invariant_units as IU
from scripts.iter12_xspeaker import build_corpus, recognise_loso, dtw
from domains.composed_net_representation import (
    compose_band_poly_net, apply_composed_net, _band_scale)

from tests.test_gadgets import _fresh_substrate, _seed_parents
from domains.code_writing_cortex import CodeWritingCortex


def _make_cortex():
    class _A:
        def op_stats(self):
            return {}
    s = _fresh_substrate()
    _seed_parents(s)
    return CodeWritingCortex(s, agent=_A()).install()


def loso_knn_matrices(corpus, k=3):
    """Generic kNN-DTW LOSO over a list of (M, word, speaker); M already the chosen
    representation. Returns mean acc."""
    speakers = sorted(set(s for _, _, s in corpus))
    accs = []
    for held in speakers:
        train = [(M, w) for M, w, s in corpus if s != held]
        test = [(M, w) for M, w, s in corpus if s == held]
        tr_m = [M for M, _ in train]
        tr_w = [w for _, w in train]
        ok = 0
        for Mt, tw in test:
            ds = sorted((dtw(Mt, Mtr), wtr) for Mtr, wtr in zip(tr_m, tr_w))
            pred = Counter(w for _, w in ds[:k]).most_common(1)[0][0]
            ok += (pred == tw)
        accs.append(ok / len(test) if test else 0.0)
    return float(np.mean(accs))


def loso_composed(corpus_inv, cortex, asm, k=3, shuffle=False, seed=1, mode="full"):
    """kNN-DTW LOSO over the agent's COMPOSED-NET representation. Per held-out speaker:
    derive the band-domain scale from TRAIN frames only, apply the composed net to every
    clip, classify. `shuffle` shuffles train labels (control). `mode` ablates the
    components (full / poly / predres)."""
    speakers = sorted(set(s for _, _, s in corpus_inv))
    accs = []
    rng = np.random.default_rng(seed)
    for held in speakers:
        train_frames = [M for M, _, s in corpus_inv if s != held]
        centre, half = _band_scale(train_frames)
        train = [(apply_composed_net(cortex, asm, M, centre, half, mode=mode), w)
                 for M, w, s in corpus_inv if s != held]
        test = [(apply_composed_net(cortex, asm, M, centre, half, mode=mode), w)
                for M, w, s in corpus_inv if s == held]
        tr_m = [M for M, _ in train]
        tr_w = [w for _, w in train]
        if shuffle:
            tr_w = list(tr_w)
            rng.shuffle(tr_w)
        ok = 0
        for Mt, tw in test:
            ds = sorted((dtw(Mt, Mtr), wtr) for Mtr, wtr in zip(tr_m, tr_w))
            pred = Counter(w for _, w in ds[:k]).most_common(1)[0][0]
            ok += (pred == tw)
        accs.append(ok / len(test) if test else 0.0)
    return float(np.mean(accs))


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 2

    corpus_b = build_corpus(n_per_speaker=n_per, seed=0)
    canonical = IU.canonical_log_centroid([M for M, _, _ in corpus_b])
    words = [w for _, w, _ in corpus_b]
    chance = 1.0 / len(set(words))
    unigram = Counter(words).most_common(1)[0][0]
    uni_acc = float(np.mean([w == unigram for w in words]))

    print("=== iter-28 FSDD LOSO: the agent's small COMPOSED net (write-not-train) ===")
    print(f"corpus: {len(corpus_b)} utts, n_per_speaker={n_per}, "
          f"chance {chance:.3f}, unigram {uni_acc:.3f}\n")

    # BASELINE (the confirmed band-mean invariant path)
    print("--- BASELINE invariant_transform kNN-DTW (confirmed ~0.785) ---")
    b_acc, b_uni = recognise_loso(
        corpus_b, lambda M, spk=None: IU.invariant_transform(M, canonical),
        verbose=False)
    print(f"  MEAN acc {b_acc:.3f}\n")

    # the INVARIANT frames the composed net operates on (same inputs as baseline)
    corpus_inv = [(IU.invariant_transform(M, canonical), w, s)
                  for M, w, s in corpus_b]

    # the agent composes the net ONCE (write-not-train)
    print("--- composing the agent's per-band net (write-not-train) ---")
    cortex = _make_cortex()
    asm = compose_band_poly_net(cortex)
    # smoke: forward is exact on the gadget domain
    chk = cortex.forward(asm, [0.3])
    print(f"  composed net forward(0.3) = {[round(v,4) for v in chk]} "
          f"(truth [0.3, 0.09, 0.027]); weights rendered, not fit\n")

    print("--- COMPOSED-NET (full: [z, z^2, z^3, z_t - z_{t-1}]) kNN-DTW ---")
    c_acc = loso_composed(corpus_inv, cortex, asm, mode="full")
    print(f"  MEAN acc {c_acc:.3f}\n")

    print("--- ablation: POLY only ([z, z^2, z^3], gap A) ---")
    p_acc = loso_composed(corpus_inv, cortex, asm, mode="poly")
    print(f"  MEAN acc {p_acc:.3f}\n")

    print("--- ablation: PREDRES only ([z, z_t - z_{t-1}], gap B) ---")
    r_acc = loso_composed(corpus_inv, cortex, asm, mode="predres")
    print(f"  MEAN acc {r_acc:.3f}\n")

    print("--- COMPOSED-NET, SHUFFLED train labels (control) ---")
    cs_acc = loso_composed(corpus_inv, cortex, asm, shuffle=True, seed=2)
    print(f"  MEAN acc {cs_acc:.3f}  (must collapse toward unigram {uni_acc:.3f})\n")

    print("=" * 64)
    print(f"  unigram          {uni_acc:.3f}")
    print(f"  iter-27 WEIGHTED 0.333   (prior turn, fixed-DSP)")
    print(f"  BASELINE         {b_acc:.3f}   (confirmed ~0.785)")
    print(f"  COMPOSED full    {c_acc:.3f}   ({c_acc - 0.333:+.3f} vs iter-27; "
          f"{c_acc - b_acc:+.3f} vs baseline)")
    print(f"    poly only      {p_acc:.3f}")
    print(f"    predres only   {r_acc:.3f}")
    print(f"  COMPOSED shuffle {cs_acc:.3f}   (control)")
    print("=" * 64)


if __name__ == "__main__":
    main()
