"""parent_ablation — which of the THREE moves helps? (recasts / register-gate / scale)

Runs the SELF-PICK babble baseline once, then four PARENT variants against the SAME
ungameable ADS full-lexicon held-out, on the SAME fresh start + same budget:

  FULL          — ZPD + ostensive + recasts + register-gating, scaled lexicon.
  -recasts      — full MINUS move 1 (no corrective re-utterance).
  -register     — full MINUS move 2 (parent always speaks IDS, the first-piece bug).
  -scale        — full but on the SMALL (digit-only) grid (move 3 removed).

Each variant's whole-grid + reached-cell held-out mean vs self-pick isolates the
lever. The donkey boundary is unchanged: the PARENT teaches (speaks/names/recasts/
picks-level/gates-register); the AGENT grounds; the held-out is ADS full-lexicon,
restrict_to=None, ungameable.

Run:
  PYTHONUNBUFFERED=1 python -m scripts.parent_ablation \
      [--seconds N] [--report-every S] [--lexicon-size K] [--out /tmp/abl.json]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.parent_speech_loop import run_selfpick, run_parent


def _whole_grid(hist):
    cells = sorted(hist[-1][1].keys())
    return float(np.mean([hist[-1][1].get(n, 0.0) for n in cells])), hist[-1][1]


def _reached(self_last, parent_last):
    reached = [n for n in parent_last if parent_last.get(n, 0.0) > 0.0]
    if not reached:
        return None
    rs = float(np.mean([self_last.get(n, 0.0) for n in reached]))
    rp = float(np.mean([parent_last.get(n, 0.0) for n in reached]))
    return reached, rs, rp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=int, default=420)
    ap.add_argument("--report-every", type=float, default=60.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--lexicon-size", type=int, default=40)
    ap.add_argument("--out", default="/tmp/parent_ablation.json")
    args = ap.parse_args()

    sec, rep, seed, lex = args.seconds, args.report_every, args.seed, args.lexicon_size

    print("=" * 70, flush=True)
    print(f"PARENT ABLATION  seconds={sec}/regime  lexicon={lex}  seed={seed}",
          flush=True)
    print("=" * 70, flush=True)

    print("\n##### BASELINE: SELF-PICK BABBLE (scaled grid) #####", flush=True)
    self_hist = run_selfpick(sec, rep, seed=seed, scaled=True, lexicon_size=lex)
    self_mean, self_last = _whole_grid(self_hist)

    variants = [
        ("FULL", dict(use_recasts=True, register_gate=True, scaled=True)),
        ("-recasts", dict(use_recasts=False, register_gate=True, scaled=True)),
        ("-register", dict(use_recasts=True, register_gate=False, scaled=True)),
        ("-scale", dict(use_recasts=True, register_gate=True, scaled=False)),
    ]
    results = {"self_mean": self_mean, "self_last": self_last, "variants": {}}
    for name, kw in variants:
        print(f"\n##### PARENT VARIANT: {name} #####", flush=True)
        ph = run_parent(sec, rep, seed=seed, lexicon_size=lex, **kw)
        pmean, plast = _whole_grid(ph)
        # for -scale, the self baseline must be the SMALL grid subset for a fair
        # whole-grid compare; compare on the parent's own cells.
        sl = {n: self_last.get(n, 0.0) for n in plast}
        sm = float(np.mean([sl.get(n, 0.0) for n in plast])) if plast else 0.0
        rr = _reached(self_last, plast)
        results["variants"][name] = {
            "parent_mean": pmean, "parent_last": plast,
            "self_mean_on_cells": sm, "reached": rr}
        print(f"   [{name}] whole-grid: self {sm:.3f} vs parent {pmean:.3f} "
              f"(Δ {pmean - sm:+.3f})", flush=True)
        if rr:
            reached, rs, rp = rr
            print(f"   [{name}] reached cells {sorted(reached)}: "
                  f"self {rs:.3f} vs parent {rp:.3f} (Δ {rp - rs:+.3f})", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("ABLATION SUMMARY — whole-grid Δ(parent - self) per variant", flush=True)
    print("=" * 70, flush=True)
    full = results["variants"]["FULL"]
    full_delta = full["parent_mean"] - full["self_mean_on_cells"]
    print(f"  FULL whole-grid Δ {full_delta:+.3f}", flush=True)
    for name in ("-recasts", "-register", "-scale"):
        v = results["variants"][name]
        d = v["parent_mean"] - v["self_mean_on_cells"]
        # contribution of the removed lever ~ FULL_delta - variant_delta (on its grid)
        print(f"  {name:10s} whole-grid Δ {d:+.3f}   "
              f"(removing this lever changes Δ by {d - full_delta:+.3f})", flush=True)

    with open(args.out, "w") as f:
        json.dump({k: v for k, v in results.items()}, f, indent=2, default=str)
    print(f"\n[done] -> {args.out}", flush=True)
    print("[MARKER] PARENT_ABLATION_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
