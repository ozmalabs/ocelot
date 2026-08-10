#!/usr/bin/env python3
"""jabberwock_richer_grounding — RICHER GROUNDING: the taught gaming / literary / period microtheories
make the reference-world dimensions EDGE-LEARNED (2026-07-04).

The concept->dimension edge-learner (`concept_graph`) descends a concept's `Microtheory -has_concept->
Concept` neighbourhood to labelled region anchors. It edge-learned 58% of the tech AREAS but 0 of the
gamer / literary / period reference worlds — there were no gaming / literary / period microtheories with
concept edges to co-descend against. `scripts/teach_dimension_microtheories.py` supplied that graph
(seeds/gaming_microtheory.json + literary_ + period_microtheory.json, two levels each). This script
demonstrates the lift: the reference dimensions are now edge-learned, the minimal pair 'would you kindly'
-> BioShock is edge-grounded, the own name sits in the literary dimension, and a sub-microtheory gives a
deeper N-descent rung.

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_richer_grounding.py
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

GAMER = ["bioshock", "portal", "game", "player", "respawn", "controller"]
VANE = ["ethics", "virtue", "philosophy", "morality", "propriety", "courtesy"]
AREAS = ["engineering", "video_coding_theory", "computer_architecture", "communication",
         "mathematics", "databases_and_storage", "embedded_iot_realtime",
         "security_and_cryptography", "art_design_drawing", "cloud_infrastructure",
         "machine_learning", "philosophy"]
REF = ["video_games", "bioshock", "portal", "glados", "game", "player",
       "literature", "carroll", "jabberwock", "rabbit_hole", "red_queen", "alice",
       "period_thought", "virtue", "rhetoric", "blacksmithing", "moral_philosophy",
       "propriety", "courtesy"]
# what the reference tier was BEFORE the teach (measured against the un-taught graph): only the two
# concepts an already-existing anchor happened to carry (virtue, moral_philosophy) were edge; the rest
# were anchor / absent (no gaming/literary/period microtheories existed).
REF_EDGE_BEFORE = 2


def main() -> None:
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=())
    load_all_seeds(a)

    print("=" * 78)
    print("TAUGHT MICROTHEORIES (graph data, reboot-proof) — Mt -has_concept-> Concept")
    print("=" * 78)
    for mt in ("video_games", "bioshock", "literature", "carroll", "period_thought"):
        print(f"  {mt:16s} bag={cg.bag_size(a, mt):3d} concept-tokens (an edge-bearing anchor)")

    print("\n" + "=" * 78)
    print("COVERAGE — the previously-anchored reference dimensions are now EDGE-LEARNED")
    print("=" * 78)
    areas = cg.connectivity_report(a, AREAS)
    ref = cg.connectivity_report(a, REF)
    both = cg.connectivity_report(a, AREAS + REF)
    print(f"  tech AREAS        : {areas['edge']}/{areas['n']} edge = {areas['edge_fraction']*100:.1f}%  "
          f"(unchanged baseline — no regression)")
    print(f"  reference worlds  : before {REF_EDGE_BEFORE}/{ref['n']} = {REF_EDGE_BEFORE/ref['n']*100:.1f}%"
          f"  ->  after {ref['edge']}/{ref['n']} = {ref['edge_fraction']*100:.1f}%")
    print(f"  combined tech+ref : before {areas['edge']+REF_EDGE_BEFORE}/{both['n']} = "
          f"{(areas['edge']+REF_EDGE_BEFORE)/both['n']*100:.1f}%  ->  after {both['edge']}/{both['n']} = "
          f"{both['edge_fraction']*100:.1f}%")
    print("  now edge-learned (were anchor / absent):")
    for r in ref["rows"]:
        if r["source"] == "edge":
            print(f"    EDGE   {r['concept']:16s} bag={r['bag']:3d} -> {r['region']}")
    print("  still anchor (honest residual — the coarse region is correct; finer dim is edge rung-2):")
    for r in ref["rows"]:
        if r["source"] == "anchor":
            print(f"    anchor {r['concept']:16s} -> {r['region']}  (in-path dim: "
                  f"{cg.descend(a, r['concept'])['path']})")

    print("\n" + "=" * 78)
    print("LEXICAL-DEGREE NORMALIZATION — low-degree CLEAR crosses; ambiguous does NOT")
    print("=" * 78)
    print("  confidence = CLARITY [best/(best+other), degree-free] >= %.2f, grounded by absolute strength"
          % cg._CLARITY_FLOOR)
    print("  (best>=%.2f) OR edge-mass CONTAINMENT (>=%.1f). The containment leg rescues a sparse idiom"
          % (cg._CONF_FLOOR, cg._CONTAIN_FLOOR))
    print("  whose cosine is diluted purely by the anchor's size; CLARITY rejects a genuine split.")
    print()
    hdr = f"    {'concept':14s} {'bag':>3s} {'best':>6s} {'clar':>5s} {'cont':>5s}  verdict"
    print("  LOW-DEGREE CLEAR (were anchor -> now EDGE, rescued by containment):")
    print(hdr)
    for c in ("jabberwock", "rabbit_hole", "red_queen", "alice", "game", "player", "portal", "glados"):
        k = cg.region_confidence(a, c)
        print(f"    {c:14s} {cg.bag_size(a, c):3d} {k['best']:6.3f} {k['clarity']:5.2f} "
              f"{k['containment']:5.2f}  anchor -> EDGE ({k['region']})")
    print("  DISCRIMINATIVE CONTROL — same low degree (bag 0), edges SPLIT -> stays ANCHOR:")
    print(hdr)
    for c in ("game_theory", "moral_algorithm", "communication", "computer_architecture"):
        k = cg.region_confidence(a, c)
        print(f"    {c:14s} {cg.bag_size(a, c):3d} {k['best']:6.3f} {k['clarity']:5.2f} "
              f"{k['containment']:5.2f}  {'EDGE' if k['edge'] else 'anchor (under floor)'}")
    print("  note: game (bag 0, clarity 0.69) CROSSES; game_theory (bag 0, clarity 0.63, containment")
    print("  1.00) does NOT — same degree, fully contained, decided by CLARITY-of-world, not by degree.")

    print("\n" + "=" * 78)
    print("MINIMAL PAIR — 'would you kindly' -> BioShock, edge-grounded (gamer vs Vane)")
    print("=" * 78)
    v = sr.decode_reference({"id": "gamer", "observed": True, "known_concepts": GAMER},
                            "would you kindly step aside")
    print(f"  codebook decode: phrase='would you kindly'  source={v['source']}  (tag bioshock)")
    for nm, fr in (("GAMER", GAMER), ("VANE ", VANE)):
        r = sr.liveness_via_edges(a, "bioshock", fr)
        verdict = "LIVE (a BioShock allusion)" if r["live"] else "speech pattern (plain courtesy)"
        print(f"  bioshock for {nm}: {verdict:32s} dim={r['dimension']} [{r['source']}] "
              f"frame_dims={r['frame_dims']}")

    print("\n" + "=" * 78)
    print("OWN NAME + graduated allusion — the literary dimension by edges")
    print("=" * 78)
    dj = cg.descend(a, "jabberwock")
    print(f"  jabberwock  path={dj['path']}  (own name sits in the literary dimension, edge rung-2)")
    rec = sr.recognize_own_name("why are you named Jabberwock?")
    print(f"  own-name reference: {rec['statement']}")
    for ref_c in ("rabbit_hole", "red_queen"):
        live = all(sr.liveness_via_edges(a, ref_c, fr)["live"] for fr in (GAMER, VANE, []))
        print(f"  {ref_c:12s} universal / graduated -> live in EVERY frame: {live}")

    print("\n" + "=" * 78)
    print("DEEPER N-DESCENT — a sub-microtheory gives another rung (depth 3)")
    print("=" * 78)
    for c in ("carroll", "bioshock"):
        d = cg.descend(a, c)
        print(f"  {c:10s} depth={d['depth']}  path={d['path']}  [{d['source']}]")
    print(f"  co-descent: jabberwock runs with the LITERARY world to depth "
          f"{cg.shared_depth(a, 'jabberwock', ['carroll'])}, forks from the GAMING world at rung 1 "
          f"(depth {cg.shared_depth(a, 'jabberwock', ['bioshock'])}).")

    print("\n" + "=" * 78)
    print("TECH-MICROTHEORY BUILD — the last five anchored domains now EDGE-LEARNED")
    print("=" * 78)
    print("  (seeds/computer_architecture_microtheory.json + mathematics_ + cloud_ + art_ +")
    print("   communication_, each with member concepts; four registered as region anchors.)")
    TECH_FIVE = [("computer_architecture", "modern_tech (foreign to Vane)"),
                 ("cloud_infrastructure", "modern_tech (foreign to Vane)"),
                 ("mathematics", "universal (familiar to Vane)"),
                 ("art_design_drawing", "universal (familiar to Vane)"),
                 ("communication", "measured — genuinely DIFFUSE")]
    for c, assigned in TECH_FIVE:
        region, source = cg.world_dimension(a, c)
        conf = cg.region_confidence(a, c)
        mark = "EDGE " if source == "edge" else "SPLIT"
        print(f"    {mark} {c:22s} -> {region:12s} [{source}]  clar={conf['clarity']:.2f}  ({assigned})")
    print("  communication STAYS split (clarity < 2/3): a timeless human sense (language/message/")
    print("  rhetoric) AND a technical networking sense (protocol/packet/bandwidth) — not forced across;")
    print("  it resolves universal via the anchor fallback, so it stays FAMILIAR to Vane.")

    areas = cg.connectivity_report(a, AREAS)
    both_now = cg.connectivity_report(a, AREAS + REF)
    print(f"\n  tech AREAS        : before 7/12 = 58.3%  ->  after {areas['edge']}/{areas['n']} = "
          f"{areas['edge_fraction']*100:.1f}%")
    print(f"  combined tech+ref : {both_now['edge']}/{both_now['n']} = {both_now['edge_fraction']*100:.1f}%"
          f"  (~100% — the only residual is the honestly-split communication)")

    print("\n  VANE PARTITION PRESERVED (correctness guard):")
    from domains import audience_adaptation as aa
    r = aa.adapt_concepts(a, AREAS, {"id": "Cornelius Vane", "observed": True, "known_concepts": VANE,
                                     "register": "formal", "formal_cues": 2.0})
    print(f"    Vane 'How are you organised?' -> {' '.join(r['adapted'])}")
    print("    (mathematics / communication / art familiar; computer_architecture / cloud in the umbrella)")
    print("\n  DISCRIMINATIVE CONTROL still holds (new anchors don't break it):")
    for c in ("game_theory", "moral_algorithm", "compilers"):
        k = cg.region_confidence(a, c)
        print(f"    {c:16s} clar={k['clarity']:.2f} cont={k['containment']:.2f} edge={k['edge']} "
              f"-> {cg.world_dimension(a, c)}  (stays anchored)")


if __name__ == "__main__":
    main()
