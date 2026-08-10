#!/usr/bin/env python3
"""Read `results/pixelseam.json` and print the tables the results file quotes.

POST-HOC READING ONLY -- it computes no verdict.  Every verdict is decided in
`scripts/pixelseam_measure.py` and stored in the artifact; this script only
groups and prints what is already there, so a table in the write-up can be
regenerated from the committed artifact rather than transcribed by hand.
"""
from __future__ import annotations
import collections
import json
import sys

REC = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "results/pixelseam.json"))
Q = REC["q_grid"]


def cell(rows, q):
    return [r for r in rows if r["q"] == q]


print("ENGINE :", REC["provenance"])
print("PREREG :", REC["prereg_commit"])
print("LOADAVG: start", REC.get("loadavg"), "end", REC.get("loadavg_end"))
print("ELAPSED: %.0fs" % REC.get("elapsed_s", 0))
print()

print("== A0 WIRING CONTROL")
for k, v in REC["A0"].items():
    print("  %-4s %-12s off=%s probe_coord_dims=%s"
          % (k, v["status"], v["offset"], v.get("probe_coord_dims")))
print()

print("== PATCH ARMS: explained / live / n, by q")
print("  %-5s %s" % ("q", "  ".join("%-22s" % a for a in REC["patch"])))
for q in Q:
    row = []
    for arm, rows in REC["patch"].items():
        c = cell(rows, q)
        row.append("%-22s" % ("expl %3d  live %3d  n %3d"
                              % (sum(r["explained"] for r in c),
                                 sum(r["live"] for r in c), len(c))))
    print("  %-5d %s" % (q, "  ".join(row)))
print()

print("== THE COMPLEMENTARITY: explained vs live, cross-tabulated")
for arm, rows in REC["patch"].items():
    t = collections.Counter((bool(r["live"]), bool(r["explained"])) for r in rows)
    print("  %-4s live&expl %4d | live&refused %4d | dead&expl %4d | dead&refused %4d"
          % (arm, t[(True, True)], t[(True, False)], t[(False, True)], t[(False, False)]))
print()

print("== DIAGNOSIS (the INDEPENDENT requirement reading), by arm")
for arm, rows in REC["patch"].items():
    t = collections.Counter(r["diagnosis"] for r in rows)
    print("  %-4s %s" % (arm, dict(sorted(t.items()))))
for arm, rows in REC.get("dense", {}).items():
    t = collections.Counter(r["diagnosis"] for r in rows)
    print("  %-4s %s" % (arm, dict(sorted(t.items()))))
print()

print("== DENSE ARMS: explained / live / n, and `checked` (refusal vs failure)")
for arm, rows in REC.get("dense", {}).items():
    for q in Q:
        c = cell(rows, q)
        ck = collections.Counter(r["checked"] for r in c)
        print("  %-3s q=%-4d expl %d/%d  live %d/%d  checked=%s"
              % (arm, q, sum(r["explained"] for r in c), len(c),
                 sum(r["live"] for r in c), len(c), dict(ck)))
print()

print("== E4g vs E4t, PAIRED (does a GROUND-TRUTH support rescue anything?)")
by = {(r["arm"], r["q"], r["seed"]): r for a in REC["patch"] for r in REC["patch"][a]}
g_beats = [k for k, r in by.items() if k[0] == "E4g" and r["explained"]
           and not by[("E4t", k[1], k[2])]["explained"]]
t_beats = [k for k, r in by.items() if k[0] == "E4t" and r["explained"]
           and not by[("E4g", k[1], k[2])]["explained"]]
print("  E4g explains where E4t does not: %d" % len(g_beats))
print("    by q:", dict(sorted(collections.Counter(k[1] for k in g_beats).items())))
print("    their E4t diagnosis:",
      dict(collections.Counter(by[("E4t", k[1], k[2])]["diagnosis"] for k in g_beats)))
print("  E4t explains where E4g does not: %d" % len(t_beats))
print()

print("== LIVE FRACTION BY q (the corpus's own photometry)")
print(" ", REC.get("live_fraction_by_q"))
print("  underpowered cells (live < MIN_LIVE=%s):" % REC.get("min_live"),
      REC.get("underpowered_cells"))
print()

print("== VERDICTS"); print(json.dumps(REC.get("verdicts", {}), indent=1))
print("== COUNTS");   print(json.dumps(REC.get("counts", {}), indent=1))
