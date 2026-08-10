"""jabberwock_finds_its_own_gaps — the agent turns its collapse loop INWARD and
PERCEIVES a gap in its OWN competence.

The foundation of self-improvement: notice a failing faculty in YOURSELF, not just
a gap in the world.  An external developer finds these by running the agent and
reading the failures; here the agent runs a CHALLENGE BATTERY through its own real
faculties, PREDICTS competence (the battery is its competence self-claim), OBSERVES
each outcome mechanically (substantive result vs a known-failure surface), and the
RESIDUAL (predicted-competent BUT observed-failure) is a CapabilityGap — the SAME
manifold-collapse cognition it runs on a maze or a person, pointed at itself.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_finds_its_own_gaps.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import self_capability_collapse as scc


def _agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.learn_sign("hello", "greeting")
    a.learn_sign("noted", "acknowledgment")
    a._donkey = {"n": 0}
    a.set_self_teacher(lambda q: (a._donkey.__setitem__("n", a._donkey["n"] + 1), "D")[1])
    return a


def main():
    print("=" * 92)
    print("THE JABBERWOCK TURNS ITS COLLAPSE LOOP INWARD — self-gap perception")
    print("=" * 92)
    a = _agent()
    battery = scc.load_battery()
    out = scc.perceive_capability_gaps(a, battery)

    print("\n  CHALLENGE BATTERY (each is something the agent is EXPECTED to handle):")
    for r in out["records"]:
        mark = "OK " if r["outcome"] == scc.SUBSTANTIVE else "GAP"
        reply = (r.get("reply") or "").strip().replace("\n", " ")
        if len(reply) > 54:
            reply = reply[:51] + "..."
        print(f"    [{mark}] {r['faculty']:<26} outcome={r['outcome']:<14} reply={reply!r}")

    print("\n  COLLAPSE RESIDUAL (predicted-competent BUT observed-failure = a gap):")
    if out["residual"]:
        for faculty, cls in out["residual"]:
            print(f"    gap -> faculty {faculty!r} failed with a {cls} surface")
    else:
        print("    (none — every claimed faculty produced a substantive result)")

    print("\n  MINTED CapabilityGap NODES (localized, graph-resident Concerns):")
    for g in out["gaps"]:
        at = a.s.node(g)["attrs"]
        print(f"    #{g}: {at.get('description')}")

    # HAND-OFF: show a perceived gap is a well-formed, groundable Concern.
    if out["gaps"]:
        verdict = scc.ground_gap_as_concern(a, out["gaps"][0])
        print("\n  HAND-OFF to the composer (induce_concern consumes the gap as a Concern):")
        print(f"    {verdict.get('note')}")

    handled = sum(1 for r in out["records"] if r["outcome"] == scc.SUBSTANTIVE)
    ok = (len(out["gaps"]) >= 1 and handled >= 1 and a._donkey["n"] == 0
          and all(f == "explain_planning_failure" for f, _ in out["residual"]))
    print("\n" + "=" * 92)
    print(f"  {'PASS' if ok else 'FAIL'} — the agent PERCEIVED a gap in itself: {handled} faculties handled "
          f"(no gap), {len(out['gaps'])} failing faculty minted a CapabilityGap.")
    print("  PREDICT competence -> OBSERVE outcome -> RESIDUAL = a localized gap; reused run_collapse,")
    print(f"  the gap is a groundable Concern, donkey={a._donkey['n']}.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
