#!/usr/bin/env python3
"""Curves for block 187000 (DIRTY-PROPAGATION PRECISION).

Four panels, all read off `results/dirty_precision/dirty_precision.json`:
  (a) WHERE the dirty-marks come from — the diagnosis;
  (b) marks per tick, over-approximate vs precise, on both real paths;
  (c) the no-op fraction as the retina ADAPTS (185000's exact fixed point,
      seen through the dirty path);
  (d) THE NEGATIVE — dirty AREAS and per-tick cost vs the fraction of the scene
      that changed.
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "dirty_precision")


def main():
    rep = json.load(open(os.path.join(OUT, "dirty_precision.json")))
    fig, ax = plt.subplots(2, 2, figsize=(13, 9))

    # (a) the diagnosis
    d20 = rep["diagnosis"]["settled_tick"]
    d160 = rep["diagnosis_doom_accel"]["settled_tick"]
    labels = ["P1 dirty_by_writeset\n(rule effects)",
              "P2 mark_edge_type_dirty", "P3 EXTERNAL blanket\n(mark_node_mutation)"]
    a = ax[0][0]
    x = range(3)
    a.bar([i - 0.2 for i in x],
          [d20["P1_writeset"], d20["P2_edge_type"], d20["P3_external"]],
          width=0.4, label="graph retina 20x15")
    a.bar([i + 0.2 for i in x],
          [d160["P1_writeset"], d160["P2_edge_type"], d160["P3_external"]],
          width=0.4, label="Doom 160x120 (accel, shipped)")
    a.set_yscale("symlog")
    a.set_xticks(list(x))
    a.set_xticklabels(labels, fontsize=8)
    a.set_ylabel("dirty-MARKS per settled photon tick")
    a.set_title("(a) THE DIAGNOSIS: the blanket EXTERNAL path makes 86-100% of\n"
                "every dirty-mark; dirty_by_writeset makes ZERO", fontsize=9)
    a.legend(fontsize=8)

    # (b) marks: over-approx vs precise
    a = ax[0][1]
    p20 = rep["diagnosis_precise"]["settled_tick"]
    p160 = rep["diagnosis_doom_accel_precise"]["settled_tick"]
    names = ["20x15 graph", "160x120 accel"]
    over = [d20["marks_total_before_settlement"], d160["marks_total_before_settlement"]]
    prec = [p20["marks_total_before_settlement"], p160["marks_total_before_settlement"]]
    a.bar([0 - 0.2, 1 - 0.2], over, width=0.4, label="over-approximate (committed)")
    a.bar([0 + 0.2, 1 + 0.2], prec, width=0.4, label="precise (this rung)")
    for i, (o, p) in enumerate(zip(over, prec)):
        a.text(i, max(o, p) * 1.1, f"{o / max(1, p):.2f}x", ha="center", fontsize=9)
    a.set_yscale("log")
    a.set_xticks([0, 1])
    a.set_xticklabels(names)
    a.set_ylabel("dirty-marks per tick")
    a.set_title("(b) precision cuts the MARKS 7.3x on the shipped path\n"
                "(and the dirty RULES 16 -> 8)", fontsize=9)
    a.legend(fontsize=8)

    # (c) no-op fraction vs hold
    a = ax[1][0]
    rows = rep["noop_vs_hold"]
    a.plot([r["hold"] for r in rows], [100 * r["noop_frac"] for r in rows],
           "o-", label="no-op attr writes (%)")
    a.axvline(71, ls="--", c="grey")
    a.text(72, 45, "185000's exact EMA\nfixed point t* ~ 71", fontsize=8, color="grey")
    a.set_xlabel("ticks held on a static frame")
    a.set_ylabel("% of per-cell attr writes that change NOTHING")
    a.set_title("(c) once the sheet ADAPTS, 4 of its 5 per-cell writes are\n"
                "bit-identical no-ops; the 5th is the epoch STAMP", fontsize=9)
    a.set_ylim(0, 100)
    a.legend(fontsize=8)

    # (d) THE NEGATIVE
    a = ax[1][1]
    sw = rep["H_scene_fraction"]["sweep"]
    for arm, mk in (("over_approx", "o-"), ("precise", "s--")):
        rows = [r for r in sw if r["arm"] == arm]
        a.plot([100 * r["change_fraction"] for r in rows],
               [1e3 * r["median_tick_seconds"] for r in rows], mk,
               label=f"{arm} (ms/tick)")
    a.set_xlabel("% of the scene that CHANGED")
    a.set_ylabel("median settlement ms / tick")
    a.set_ylim(0, 3.5)
    a2 = a.twinx()
    for arm, mk in (("over_approx", "^-"), ("precise", "v--")):
        rows = [r for r in sw if r["arm"] == arm]
        a2.plot([100 * r["change_fraction"] for r in rows],
                [r["n_dirty_areas"] for r in rows], mk, color="crimson", alpha=0.6)
    a2.set_ylabel("dirty AREAS (red)", color="crimson")
    a2.set_ylim(0, 7)
    a.set_title("(d) THE NEGATIVE: 6/6 areas dirty at EVERY change fraction,\n"
                "and 2.88-2.91 ms/tick either way", fontsize=9)
    a.legend(fontsize=8, loc="lower left")

    fig.suptitle("Block 187000 — DIRTY-PROPAGATION PRECISION: the blanket is the "
                 "over-approximation, and cutting it 7.3x buys NO time",
                 fontsize=11)
    fig.tight_layout()
    path = os.path.join(OUT, "dirty_precision.png")
    fig.savefig(path, dpi=130)
    print("wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
