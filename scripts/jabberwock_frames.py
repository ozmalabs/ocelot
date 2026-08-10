#!/usr/bin/env python3
"""jabberwock_frames — THE FRAME made explicit (the creator's founding ontology, 2026-07-04):
a FRAME is a SET OF DIMENSIONS with RELATIVE LOG-SCALED WEIGHTING. This demonstrator shows the
interlocutor's manifold built AS A FRAME, and audience-adaptation + reference-liveness FALLING OUT
of frame-membership — replacing the coarse cue-table classifiers. donkey=0 (no LM, no fit).

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_frames.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from domains import frame as fr                 # noqa: E402
from domains import audience_adaptation as aa   # noqa: E402
from domains import sense_of_reference as sr     # noqa: E402


AREAS = ["engineering", "video_coding_theory", "communication", "mathematics",
         "cloud_infrastructure", "machine_learning", "philosophy"]
VANE = {"id": "Cornelius Vane", "observed": True,
        "known_concepts": ["ethics", "virtue", "philosophy", "morality", "propriety", "courtesy"]}
TECHNICAL = {"id": "dev", "observed": True,
             "known_concepts": ["python", "rust", "algorithm", "compiler", "server", "database"]}
GAMER = {"id": "gamer", "observed": True,
         "known_concepts": ["bioshock", "rapture", "respawn", "playthrough", "controller"]}
WYK = "Would you kindly open the door for me?"


def main() -> None:
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    load_all_seeds(a)

    print("=" * 74)
    print("THE FRAME PRIMITIVE — a set of dimensions with relative log-scaled weights")
    print("=" * 74)
    f = fr.build_frame(a, {"universal": 1.0, "modern_tech": 1.0, "period": 1.0}, "demo")
    print(f"  dims                     : {fr.frame_dims(f, a)}")
    print(f"  equal dims -> equal wts  : "
          f"{[fr.dimension_weight(f, d, agent=a) for d in fr.frame_dims(f, a)]}")
    import math
    g = fr.build_frame(a, {"a": 1.0, "b": 1.0, "dom": math.e ** 2}, "demo2")
    print(f"  dominant dim -> +k steps : dom-a = {fr.relative_weight(g, 'dom', 'a', agent=a):.2f}")
    print(f"  absent dim -> -inf       : q = {fr.dimension_weight(g, 'q', agent=a)}")

    print("\n" + "=" * 74)
    print("MANIFOLD AS A FRAME — audience-adaptation IS frame-membership")
    print("=" * 74)
    for name, who in (("Vane (formal, no modern-tech dim)", VANE),
                      ("Technical (holds modern-tech dim)", TECHNICAL)):
        fr_m = aa.interlocutor_frame(a, who)
        has_mt = fr.in_frame(fr_m, aa.DIM_MODERN_TECH, a)
        adapted = aa.adapt_concepts(a, AREAS, who)["adapted"]
        print(f"\n  {name}")
        print(f"    modern_tech in frame? {has_mt}")
        print(f"    -> reply             : {' '.join(adapted)}")

    print("\n" + "=" * 74)
    print("REFERENCE-LIVENESS IS frame-membership — same string, opposite call")
    print("=" * 74)
    for name, who in (("gamer  (frame holds the gamer world)", GAMER),
                      ("Vane   (formal frame lacks it)", VANE)):
        v = sr.decode_reference(who, WYK)
        print(f"\n  {name}")
        print(f"    '{v['phrase']}' -> liveness={v['liveness']:14s} is_reference={v['is_reference']}")
    print("\n  graduated concept -> universal dimension, live in EVERY frame:")
    for who, tag in ((GAMER, "gamer"), (VANE, "vane"), ({"known_concepts": []}, "unknown")):
        v = sr.decode_reference(who, "we went down the rabbit hole on this")
        print(f"    {tag:8s}: liveness={v['liveness']}  is_reference={v['is_reference']}")

    print("\ndonkey=0 — no LM, no fit; the decisions are graph queries over frame-membership.")


if __name__ == "__main__":
    main()
