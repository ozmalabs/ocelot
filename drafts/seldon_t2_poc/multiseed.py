"""
Robustness: repeat the whole evaluation across several panel seeds and report
the distribution of the text-uplift and the text-blind Seldon-vs-AR gap.
Guards against a single-seed fluke. Run:

    python3 drafts/seldon_t2_poc/multiseed.py
"""

from __future__ import annotations

import numpy as np
from run_poc import evaluate, paired_bootstrap_ci


def main(seeds=range(10)):
    rows = []
    for s in seeds:
        _, crps, paired, *_ = evaluate(seed=int(s))
        blind = paired["seldon_notext"].mean()
        text = paired["seldon_text"].mean()
        gar = crps["gauss_ar1"].mean()
        uplift_pct = (blind - text) / blind * 100
        seldon_vs_ar_pct = (blind - gar) / gar * 100  # negative = Seldon worse than AR
        rows.append((int(s), blind, text, gar, uplift_pct, seldon_vs_ar_pct))

    print(f"{'seed':>5}{'seldon_blind':>14}{'seldon_text':>13}{'gauss_ar1':>11}"
          f"{'uplift%':>9}{'seldon-vs-ar%':>15}")
    for r in rows:
        print(f"{r[0]:>5}{r[1]:>14.4f}{r[2]:>13.4f}{r[3]:>11.4f}{r[4]:>9.2f}{r[5]:>15.2f}")

    arr = np.array(rows)
    uplifts = arr[:, 4]
    svsa = arr[:, 5]
    print("\nAcross seeds:")
    print(f"  text uplift %:      mean {uplifts.mean():.2f}  sd {uplifts.std():.2f}  "
          f"min {uplifts.min():.2f}  max {uplifts.max():.2f}  "
          f"({(uplifts>0).sum()}/{len(uplifts)} seeds positive)")
    print(f"  Seldon-blind vs AR%: mean {svsa.mean():.2f}  sd {svsa.std():.2f}  "
          f"(positive = Seldon better; negative = AR better)")


if __name__ == "__main__":
    main()
