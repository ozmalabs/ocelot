"""iter-24 FSDD LOSO regression — does the agent's SCALE-invariant representation
BREAK the confirmed speaker-invariant digit recognizer? (vs 0.785 / iter-23 0.592)

Reuses the iter-12 FSDD LOSO harness (build_corpus + recognise_loso, the same
kNN-DTW recogniser that produced the confirmed figure). Compares, on identical
held-out-speaker splits:

  BASELINE   : invariant_transform (forward-VTLN + CMVN + predict-remove)
  RELATIONAL : iter-23 value-difference (shift-invariant)            [vs 0.592]
  SCALE-INV  : iter-24 landmark spacing (the agent's scale-invariant relation)
  STACKED    : value-difference + landmark spacing (shift + scale invariant)

Run: python -m scripts.iter24_fsdd_loso [n_per_speaker]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import domains.invariant_units as IU
from domains.relational_representation import apply_relational
from domains.scale_invariant_representation import apply_scale_invariant, apply_stacked
from scripts.iter12_xspeaker import build_corpus, recognise_loso


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    nsp = int(os.environ.get("NSPACINGS", "6"))
    corpus = build_corpus(n_per_speaker=n_per, seed=0)
    raw_mats = [M for M, _, _ in corpus]
    canonical = IU.canonical_log_centroid(raw_mats)

    def baseline(M, spk=None):
        return IU.invariant_transform(M, canonical)

    def relational(M, spk=None):
        return apply_relational(M)

    def scale_inv(M, spk=None):
        return apply_scale_invariant(M, n_spacings=nsp)

    def stacked(M, spk=None):
        return apply_stacked(M, n_spacings=nsp)

    print("=== iter-24 FSDD LOSO: scale-invariant vs confirmed / iter-23 ===")
    print(f"corpus: {len(corpus)} utts, n_per_speaker={n_per}, n_spacings={nsp}\n")

    print("--- BASELINE invariant_transform (confirmed ~0.785) ---")
    b_acc, b_uni = recognise_loso(corpus, baseline, verbose=True)
    print(f"  MEAN acc {b_acc:.3f}  unigram {b_uni:.3f}\n")

    print("--- RELATIONAL (iter-23 value-diff, ~0.592) ---")
    r_acc, _ = recognise_loso(corpus, relational, verbose=False)
    print(f"  MEAN acc {r_acc:.3f}\n")

    print("--- SCALE-INV (iter-24 landmark spacing) ---")
    s_acc, s_uni = recognise_loso(corpus, scale_inv, verbose=True)
    print(f"  MEAN acc {s_acc:.3f}  unigram {s_uni:.3f}\n")

    print("--- STACKED (value-diff + landmark spacing) ---")
    st_acc, _ = recognise_loso(corpus, stacked, verbose=False)
    print(f"  MEAN acc {st_acc:.3f}\n")

    print("=" * 60)
    print(f"  BASELINE   {b_acc:.3f}   (confirmed ~0.785)")
    print(f"  RELATIONAL {r_acc:.3f}   ({r_acc - b_acc:+.3f} vs baseline; iter-23 0.592)")
    print(f"  SCALE-INV  {s_acc:.3f}   ({s_acc - b_acc:+.3f} vs baseline)")
    print(f"  STACKED    {st_acc:.3f}   ({st_acc - b_acc:+.3f} vs baseline)")
    print("=" * 60)


if __name__ == "__main__":
    main()
