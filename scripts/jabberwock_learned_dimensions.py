#!/usr/bin/env python3
"""jabberwock_learned_dimensions — DEMONSTRATE learning a concept's dimension FROM ITS EDGES.

The creator's log-number ontology (2026-07-04): a concept's position in the frame geometry is a
LOG-NUMBER read off the graph, learned by an N-STEP RECURSIVE COARSE-TO-FINE DESCENT (dynamic-
quantization recursed). Rung 1 = the coarse WORLD region (the exponent); the recursion's tail = the
fine within-region log-position (the mantissa); depth is DYNAMIC per concept (foveated). Foreignness
/ liveness = DEPTH OF CO-DESCENT relative to the interlocutor's frame — learned, not an absolute
modern-tech cue table.

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_learned_dimensions.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from domains import concept_graph as cg          # noqa: E402
from domains import sense_of_reference as sr      # noqa: E402


def main() -> None:
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    load_all_seeds(a)

    VANE = ["ethics", "virtue", "philosophy", "morality", "propriety", "courtesy"]
    DEV = ["python", "rust", "algorithm", "compiler", "server", "database"]
    AREAS = ["engineering", "video_coding_theory", "computer_architecture", "communication",
             "mathematics", "databases_and_storage", "embedded_iot_realtime",
             "security_and_cryptography", "art_design_drawing", "cloud_infrastructure",
             "machine_learning", "philosophy"]

    print("=" * 78)
    print("N-STEP RECURSIVE DESCENT — a concept's PATH read from its has_concept edges")
    print("  rung1 = coarse world region (EXPONENT) ; tail = fine log-position (MANTISSA)")
    print("=" * 78)
    for c in ["machine_learning", "cloud_infrastructure", "ethics", "computer_architecture",
              "mathematics", "engineering"]:
        d = cg.descend(a, c)
        mant = {k: round(v, 3) for k, v in d["mantissa"].items()}
        print(f"  {c:24s} depth={d['depth']}  path={d['path']}")
        print(f"  {'':24s} mantissa={mant}  [{d['source']}]")

    print("\n" + "=" * 78)
    print("MANTISSA — central vs peripheral in the SAME dimension (universal)")
    print("=" * 78)
    for c in ["ethics", "philosophy", "agriculture", "gastronomy"]:
        m = cg.descend(a, c)["mantissa"].get(cg.REGION_UNIVERSAL, 0.0)
        print(f"  {c:24s} universal-mantissa={m:.3f}  {'(central)' if m > 0.3 else '(peripheral)'}")

    print("\n" + "=" * 78)
    print("RELATIVE FOREIGNNESS = depth of co-descent with the INTERLOCUTOR'S FRAME")
    print(f"  Vane frame dims (edge-derived): {sorted(cg.frame_dimensions(a, VANE))}")
    print(f"  Dev  frame dims (edge-derived): {sorted(cg.frame_dimensions(a, DEV))}")
    print("=" * 78)
    for c in AREAS:
        fv = cg.is_foreign_to_frame(a, c, VANE)
        fd = cg.is_foreign_to_frame(a, c, DEV)
        sd = cg.shared_depth(a, c, VANE)
        print(f"  {c:26s} vs Vane: {'FOREIGN' if fv else 'live':7s} (co-descent depth {sd}) "
              f"| vs Dev: {'FOREIGN' if fd else 'live'}")

    print("\n" + "=" * 78)
    print("GENERALIZATION — a concept the retired 60-token cue table NEVER listed, placed by edges")
    print("=" * 78)
    for c in ["computer_vision", "realtime_systems", "rhetoric", "blacksmithing"]:
        region, source = cg.world_dimension(a, c)
        print(f"  {c:24s} -> {region:11s} [{source}]  foreignToVane={cg.is_foreign_to_frame(a, c, VANE)}")

    print("\n" + "=" * 78)
    print("REFERENCE LIVENESS via edges (coarse axis) — the minimal-pair shape, learned")
    print("=" * 78)
    for ref in ["rabbit_hole", "machine_learning", "cryptography"]:
        for nm, fr in [("Vane", VANE), ("Dev", DEV)]:
            r = sr.liveness_via_edges(a, ref, fr)
            verdict = "LIVE allusion" if r["live"] else "speech pattern"
            print(f"  {ref:18s} for {nm:4s}: {verdict:14s} (dim={r['dimension']}, depth={r['shared_depth']})")

    print("\n" + "=" * 78)
    print("CONNECTIVITY SUFFICIENCY (measured — the hard honesty guard)")
    print("=" * 78)
    rep = cg.connectivity_report(a, AREAS)
    print(f"  edge-learned: {rep['edge']}/{rep['n']}  ({rep['edge_fraction']*100:.0f}%)   "
          f"anchor (graph fell short): {rep['anchor']}/{rep['n']}")
    for r in rep["rows"]:
        if r["source"] == "anchor":
            print(f"    ANCHOR  {r['concept']:26s} bag={r['bag']:3d}  -> {r['region']}")
    print("\n  HONEST: the has_concept neighbourhood edge-learns the concept-BEARING domains; the")
    print("  zero-edge ones (computer_architecture bag<=2, compilers, mathematics) + one generic tie")
    print("  (communication) fall to the small labelled seed anchor — the demoted residual of the")
    print("  retired 60-token cue table. The finer gamer-vs-literary reference world-type is NOT")
    print("  edge-groundable (no gaming/literary microtheories with concept edges) and stays anchored.")


if __name__ == "__main__":
    main()
