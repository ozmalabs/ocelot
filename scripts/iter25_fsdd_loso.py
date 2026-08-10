"""iter-25 FSDD LOSO regression — does the iter-24 spacing relation, run over the LPC
SMOOTHED envelope's TRUE formants (the agent's iter-25 fix), RECOVER the FSDD digit
recognizer vs iter-24's regression to 0.253? (refs: confirmed 0.785 / iter-23 0.592 /
iter-24 0.253)

Reuses the iter-12 FSDD LOSO harness (build_corpus + recognise_loso, the same kNN-DTW
recogniser that produced the confirmed figure). Compares, on identical held-out-speaker
splits:

  BASELINE   : invariant_transform (forward-VTLN + CMVN + predict-remove)   [~0.785]
  SCALE-INV  : iter-24 spacing over RAW-spectrum peaks                       [0.253]
  LPC-SCALE  : iter-25 SAME spacing over the LPC SMOOTHED envelope (true formants)
  LPC-STACKED: value-difference + LPC spacing (LEVEL + VTL invariant, true formants)

LPC order = the agent's OWN specified value (agent_specify_lpc_formants -> 8).

Run: python -m scripts.iter25_fsdd_loso [n_per_speaker]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import domains.invariant_units as IU
from domains.scale_invariant_representation import apply_scale_invariant
from domains.lpc_formant_representation import (
    apply_lpc_scale_invariant, apply_lpc_stacked,
)
from scripts.iter12_xspeaker import build_corpus, recognise_loso


def _agent_lpc_order():
    try:
        from substrate_rs import Substrate
        from domains.runtime_design import agent_specify_lpc_formants
        return int(agent_specify_lpc_formants(Substrate())["order"])
    except Exception:
        return 8


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    nsp = int(os.environ.get("NSPACINGS", "6"))
    order = int(os.environ.get("LPC_ORDER", str(_agent_lpc_order())))
    corpus = build_corpus(n_per_speaker=n_per, seed=0)
    raw_mats = [M for M, _, _ in corpus]
    canonical = IU.canonical_log_centroid(raw_mats)

    def baseline(M, spk=None):
        return IU.invariant_transform(M, canonical)

    def scale_inv(M, spk=None):
        return apply_scale_invariant(M, n_spacings=nsp)

    def lpc_scale(M, spk=None):
        return apply_lpc_scale_invariant(M, n_spacings=nsp, order=order)

    def lpc_stacked(M, spk=None):
        return apply_lpc_stacked(M, n_spacings=nsp, order=order)

    print("=== iter-25 FSDD LOSO: LPC-envelope spacing vs raw-peak spacing ===")
    print(f"corpus: {len(corpus)} utts, n_per_speaker={n_per}, n_spacings={nsp}, "
          f"LPC order={order} [agent-specified]\n")

    print("--- BASELINE invariant_transform (confirmed ~0.785) ---")
    b_acc, b_uni = recognise_loso(corpus, baseline, verbose=True)
    print(f"  MEAN acc {b_acc:.3f}  unigram {b_uni:.3f}\n")

    print("--- SCALE-INV (iter-24 raw-peak spacing, 0.253) ---")
    s_acc, _ = recognise_loso(corpus, scale_inv, verbose=False)
    print(f"  MEAN acc {s_acc:.3f}\n")

    print("--- LPC-SCALE (iter-25 LPC-envelope spacing) ---")
    l_acc, l_uni = recognise_loso(corpus, lpc_scale, verbose=True)
    print(f"  MEAN acc {l_acc:.3f}  unigram {l_uni:.3f}\n")

    print("--- LPC-STACKED (value-diff + LPC spacing) ---")
    st_acc, _ = recognise_loso(corpus, lpc_stacked, verbose=False)
    print(f"  MEAN acc {st_acc:.3f}\n")

    print("=" * 60)
    print(f"  BASELINE    {b_acc:.3f}   (confirmed ~0.785)")
    print(f"  SCALE-INV   {s_acc:.3f}   (iter-24 raw-peak spacing, 0.253)")
    print(f"  LPC-SCALE   {l_acc:.3f}   ({l_acc - s_acc:+.3f} vs raw-peak spacing)")
    print(f"  LPC-STACKED {st_acc:.3f}   ({st_acc - s_acc:+.3f} vs raw-peak spacing)")
    print("=" * 60)


if __name__ == "__main__":
    main()
