"""Seed the comprehension GAPS as goals, give the jabberwock the teachers, and let it TICK.

The gaps the creator + jabberwock identified (situation model, inference, semantic roles, discourse
coherence, event/causal, theory of mind, argument/logic, modality/scope) are seeded as understand-drive
CapabilityAxes (seeds/comprehension_goals.json). The loop body is literally `master_tick(); tick()`:
the understand Drive picks the highest-shortfall gap, mints a plan, binds it to its operator, the
ComprehensionWorld grounds that gap's concepts through the on-disk teachers and measures coverage, the
bank rule updates the shortfall, and the frontier SHIFTS. We seed only the goals + the teachers and
watch how far it gets on its own.

Run:
  SPEECH_TEACHER=stub PYTHONPATH=.:runners/dsl/python python -m scripts.comprehension_autonomy [ticks]
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from substrate.world_adapter import WorldAdapter
from substrate.seed_loader import manifest_for
from domains.libraries import attach_libraries
from domains.comprehension_world import ComprehensionWorld

SEP = "=" * 96
SEEDS = ["enact", "discourse", "autonomy", "investigation_loop", "investigation_teacher",
         "comprehension_goals"]


def main():
    n_ticks = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    print(SEP)
    print("COMPREHENSION AUTONOMY — seed the gaps as goals, give the teachers, then tick")
    print(SEP)
    a = WorldAdapter()
    for sid in SEEDS:
        try:
            a.inner.load_seed_manifest(manifest_for(sid), a.agent)
        except Exception as e:
            print(f"  (seed {sid!r} skipped: {e})")
    attach_libraries(a, log=lambda *x: None)             # the on-disk teachers (dictionary/wordnet/wiki/tropes)

    world = ComprehensionWorld(a)
    world.register_affordances()
    mt = next((n for n in a.s.nodes("Microtheory")
               if a.s.node(n)["attrs"].get("name") == "comprehension_world"), None)
    if mt is not None:
        a.inner.add_edge_unchecked(a.agent, "operates_in", mt)
    a.wire_autonomy_faculty()
    a.wire_enact_faculty()
    a.wire_investigation_faculty(world)
    # (stall-escalation to a free-text teacher is the NEXT rung; the dictionary chain here is the
    #  grounding teacher, so held gaps simply stay high-shortfall — which is the finding we want.)

    axes = [n for n in a.s.nodes("CapabilityAxis") if a.s.node(n)["attrs"].get("is_axis") == 1.0]
    print(f"\n  seeded {len(axes)} comprehension goals (understand drive), teachers attached:")
    for ax in sorted(axes, key=lambda x: -a.s.node(x)["attrs"]["shortfall"]):
        at = a.s.node(ax)["attrs"]
        print(f"    {at['capability_keys'][1]:20} shortfall={at['shortfall']:.2f}")

    print("\n  ticking (master_tick(); tick()) — the agent decides what to investigate:\n")
    seen_mc = set()
    investigated = []
    for t in range(1, n_ticks + 1):
        a.master_tick(); a.tick()
        for mc in a.s.nodes("MeasuredCapability"):
            if mc in seen_mc:
                continue
            seen_mc.add(mc)
            at = a.s.node(mc)["attrs"]
            tgt = a.inner.neighbours(mc, "measures_axis")
            gap = a.s.node(tgt[0])["attrs"]["capability_keys"][1] if tgt else "?"
            investigated.append((gap, at.get("measured")))
            print(f"  [t{t:2d}] investigated {gap:20} coverage={at.get('measured')}  {at.get('note','')[:88]}")

    print("\n" + SEP)
    print(f"  the agent autonomously investigated {len(investigated)} gap(s) "
          f"({len({g for g,_ in investigated})} distinct), grounding each gap's concepts via the teachers.")
    print("  final shortfalls (lower = more understood; the drive re-ranks and shifts each tick):")
    for ax in sorted(axes, key=lambda x: a.s.node(x)["attrs"]["shortfall"]):
        at = a.s.node(ax)["attrs"]
        print(f"    {at['capability_keys'][1]:20} shortfall={at['shortfall']:.3f}  "
              f"saturation={at.get('saturation'):.3f}  investigated_count={at.get('investigated_count')}")
    base = len([n for n in a.s.nodes('Concept')])
    print(f"\n  concepts now held: {base}.  Seeded ONE thing (the understand drive over the gaps) + the")
    print("  teachers; the loop body was master_tick(); tick() — every WHAT-to-investigate decision was")
    print("  the agent's frontier pick. Gaps it could not ground stay high-shortfall (the teacher has no")
    print("  definition) — exactly the residual the next escalation rung (author/ask) would target.")
    print(SEP)


if __name__ == "__main__":
    main()
