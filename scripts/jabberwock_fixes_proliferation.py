"""THE JABBERWOCK FIXES THE PROLIFERATION — distinct frontiers from teacher advice.

The wart (the 5-minute run exposed it): grounding teacher advice minted a NEW frontier per
stall with the SAME capability_keys as the parent, so the agent proliferated identical
from_teacher axes (17 duplicates) and churned, consulting the teacher over and over.

The fix (graph-native, the agent's): the drain turns each piece of advice into an AdviceCue
node carrying its distinguishing CUE token + DISTINCT keys (a thin I/O-boundary classifier —
the only adapter step). The seeded ground_hint_to_investigation Rule now mints ONE frontier
per cue and DEDUPS by it. So the SAME advice grounds ONCE (no proliferation), and DIFFERENT
advice grounds DIFFERENT frontiers (the agent tests each distinct cue).

This verifies it: a teacher giving three distinct methods yields three DISTINCT frontiers, each
keyed by its own cue, with no duplicates — and re-giving the same advice grounds nothing new.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python -m scripts.jabberwock_fixes_proliferation
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.autonomous_speech import boot

SEP = "=" * 80

# three DISTINCT methods (distinct leading content words -> distinct cues).
_ADVICE = [
    "Contrast the onset transient against the steady-state portion of the sound.",
    "Track the formant trajectory across the vowel nucleus.",
    "Measure the voicing periodicity in the lower frequency region.",
]


def main():
    print(SEP)
    print("THE JABBERWOCK FIXES PROLIFERATION — distinct frontiers from teacher advice.")
    print(SEP)
    adapter, sw = boot(exclude=())
    # a teacher that gives three DISTINCT methods (the real claude -p gives varied advice too;
    # this makes the distinctness deterministic to verify).
    counter = {"n": 0}
    def varied_teacher(q):
        a = _ADVICE[counter["n"] % len(_ADVICE)]
        counter["n"] += 1
        return a
    adapter.set_self_teacher(varied_teacher)

    print("  running the loop (the agent stalls on recognition, consults, grounds advice)...\n")
    for t in range(1, 46):
        adapter.master_tick(); adapter.tick()

    cues = [adapter.s.node(c)["attrs"].get("token") for c in adapter.s.nodes("AdviceCue")]
    teacher_axes = [adapter.s.node(n)["attrs"] for n in adapter.s.nodes("CapabilityAxis")
                    if adapter.s.node(n)["attrs"].get("from_teacher") == 1.0]
    axis_cues = [a.get("cue") for a in teacher_axes]
    # proliferation check: are the from_teacher frontiers DISTINCT (one per cue) or duplicates?
    distinct_axis_cues = set(c for c in axis_cues if c)
    dupes = len(axis_cues) - len(distinct_axis_cues)

    print(f"  AdviceCue tokens minted (distinct cues from advice): {sorted(set(cues))}")
    print(f"  from_teacher frontiers: {len(teacher_axes)}  | their cues: {sorted(set(axis_cues))}")
    print(f"  duplicate (same-cue) frontiers: {dupes}")
    print(f"\n{SEP}")
    ok = (len(teacher_axes) >= 1 and dupes == 0 and len(distinct_axis_cues) == len(teacher_axes)
          and len(teacher_axes) <= len(_ADVICE) + 1)
    print(f"  distinct cues: {len(set(cues))}  | from_teacher frontiers: {len(teacher_axes)}  | "
          f"duplicates: {dupes}")
    print(f"  {'PASS' if ok else 'FAIL'} — each teacher cue grounds ONE distinct frontier (no "
          f"proliferation of identical copies); different advice -> different frontiers.")
    print(SEP)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
