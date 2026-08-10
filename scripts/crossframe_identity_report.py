#!/usr/bin/env python3
"""CROSS-FRAME IDENTITY — read the confirmatory artifact into the tables the
results file reports. Presentation only: it computes nothing the runner did not
already decide, and it selects nothing (every pre-registered cell is printed).

USAGE:  PYTHONPATH=runners/dsl/python:. python scripts/crossframe_identity_report.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, "results", "crossframe_identity.json")))


def row(s):
    return (f"{s['trial_acc']:.4f} [{s['wilson_lo']:.4f},{s['wilson_hi']:.4f}]  "
            f"frame {s['frame_acc']:.4f} [{s['frame_lo']:.4f},{s['frame_hi']:.4f}]  "
            f"ent {s['answer_entropy']:.3f}  tie>1 {s['frac_tied_gt1']:.3f}  "
            f"ub {s['true_achieves_max_upper_bound']:.4f}  "
            f"nn {s['nn_agreement']:.4f}  nn_score {s['nn_score_agreement']:.4f}  "
            f"nn_untied {s['nn_agreement_untied']}")


print("=" * 100)
print("PROVENANCE:", d["provenance"])
print("MACHINE   :", d["machine_state_at_start"]["loadavg"], "->",
      d.get("machine_state_at_end", {}).get("loadavg"))
for p in d["machine_state_at_start"]["top_processes"][:4]:
    print("           ", p[:110])
print("=" * 100)

for cid, meta in d["corpora"].items():
    print(f"\nCORPUS {cid}: " + json.dumps(
        {k: v for k, v in meta.items() if k not in ("files",)})[:200])

for cid, g in d.get("gates", {}).items():
    print(f"\n--- GATES {cid} ---")
    for name in ("G1_ceiling", "G2_noise", "G5_order"):
        s = g.get(name)
        if s:
            print(f"  {name:12s} {row(s)}  mean_ntied {s['mean_ntied']:.3f}")
    print(f"  run ms/base-frame {g['run_ms_per_base_frame']['mean']:.0f} "
          f"(sd {g['run_ms_per_base_frame']['sd']:.0f}) "
          f"[UNDER CONCURRENT LOAD — not a result]")

for cid, arms in d.get("arms", {}).items():
    print(f"\n--- ARMS {cid} (chance {d['constants']['chance']:.4f}) ---")
    for key in sorted(arms, key=lambda x: (x.split("|")[1], int(x.split("|d")[1]),
                                           x.split("|")[0])):
        print(f"  {key:14s} {row(arms[key])}")

for cid, m in d.get("motion", {}).items():
    s = m["mean_abs_diff_d1"]
    print(f"\nMOTION {cid} mean|frame_t+1 - frame_t| = {s['mean']:.3f} "
          f"(sd {s['sd']:.3f}, min {s['min']:.3f}, max {s['max']:.3f})")

if d.get("aperture") and "error" not in d["aperture"]:
    print("\n--- C3 APERTURE (BSDS300, KNOWN displacement, SYNTHETIC motion) ---")
    for key in sorted(d["aperture"], key=lambda x: (int(x.split("|d")[1]),
                                                    x.split("|")[0])):
        a = d["aperture"][key]
        print(f"  {key:10s} n {a['n']:4d}  acc {a['acc']:.4f} "
              f"[{a['wilson_lo']:.4f},{a['wilson_hi']:.4f}]  "
              f"ent {a['answer_entropy']:.3f}  ntied {a['mean_ntied']:.2f}  "
              f"nn {a['nn_agreement']:.4f}")

print("\n--- PRE-REGISTERED VERDICTS ---")
print(json.dumps(d.get("verdicts", {}), indent=1))
