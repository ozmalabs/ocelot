"""iter-23 FSDD LOSO regression — does the agent's relational representation BREAK
the confirmed speaker-invariant digit recognizer (LOSO 0.785)?

Reuses the iter-12 FSDD LOSO harness (build_corpus + recognise_loso, the same
kNN-DTW recogniser that produced the confirmed 0.785). Compares, on identical
held-out-speaker splits:

  BASELINE   : invariant_transform (forward-VTLN + CMVN + predict-remove) — the
               confirmed 0.785 path.
  RELATIONAL : the agent's self-derived relational representation (apply_relational)
               applied ALONE (replacing the absolute-value trajectory, as the gap
               dictates).
  REL+CMVN   : the relational representation on top of the proven CMVN base (the
               strongest invariant front-end, relationalized).

Don't break the confirmed win: relational is acceptable for the perceptual gate as
long as it does not regress FSDD far below 0.785 (and ideally helps).

Run: python -m scripts.iter23_fsdd_loso [n_per_speaker]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import domains.invariant_units as IU
from domains.relational_representation import apply_relational
from scripts.iter12_xspeaker import build_corpus, recognise_loso


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    corpus = build_corpus(n_per_speaker=n_per, seed=0)
    raw_mats = [M for M, _, _ in corpus]
    canonical = IU.canonical_log_centroid(raw_mats)

    def baseline(M, spk=None):
        return IU.invariant_transform(M, canonical)

    def relational(M, spk=None):
        return apply_relational(M)

    def rel_cmvn(M, spk=None):
        return apply_relational(IU.invariant_transform(M, canonical))

    print("=== iter-23 FSDD LOSO: relational vs confirmed invariant_transform ===")
    print(f"corpus: {len(corpus)} utts, n_per_speaker={n_per}\n")

    print("--- BASELINE invariant_transform (confirmed ~0.785) ---")
    b_acc, b_uni = recognise_loso(corpus, baseline, verbose=True)
    print(f"  MEAN acc {b_acc:.3f}  unigram {b_uni:.3f}\n")

    print("--- RELATIONAL (agent-derived, alone) ---")
    r_acc, r_uni = recognise_loso(corpus, relational, verbose=True)
    print(f"  MEAN acc {r_acc:.3f}  unigram {r_uni:.3f}\n")

    print("--- REL + CMVN (relational on the proven invariant base) ---")
    rc_acc, rc_uni = recognise_loso(corpus, rel_cmvn, verbose=True)
    print(f"  MEAN acc {rc_acc:.3f}  unigram {rc_uni:.3f}\n")

    print("=" * 60)
    print(f"  BASELINE   {b_acc:.3f}   (confirmed ~0.785)")
    print(f"  RELATIONAL {r_acc:.3f}   ({r_acc - b_acc:+.3f} vs baseline)")
    print(f"  REL+CMVN   {rc_acc:.3f}   ({rc_acc - b_acc:+.3f} vs baseline)")
    print("=" * 60)


if __name__ == "__main__":
    main()
