"""AUTONOMOUS SPEECH, RUN LONG + ESCALATE — let the agent hit the wall until it AUTHORS a new faculty.

Same pump as autonomous_speech, but (1) wires the ORDER-4 (author a new operator) + ORDER-6 (rethink self)
escalation reflexes that consume the impasse_escalation ladder's needs_tool / self_rethink markers -- the
driver omitted these, so the ladder could climb but nothing built the tool -- and (2) runs long so an axis
with real shortfall (the piper-AbS recognition wall, match=0.0) climbs past REFRAMING into needs_tool, and the
self-extend reflex AUTHORS the agent's ear (effect-gated repertoire-cue growth; a designed CONVOLUTION filter
if the cues plateau). The agent decides; this only enables and observes.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  SPEECH_TEACHER=stub SPEECH_LOCAL_ONLY=1 PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.autonomous_speech_escalate [ticks]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.autonomous_speech import boot, understanding, SEP


def main():
    n_ticks = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    print(SEP)
    print("AUTONOMOUS SPEECH + ESCALATION — run long, hit the wall, author a new faculty. The agent decides.")
    print(SEP)
    adapter, sw = boot()
    adapter.wire_escalation_faculties()                # enable order-4 (author) + order-6 (rethink)
    s = adapter.s
    print(f"  booted + escalation wired: "
          f"{len([n for n in s.nodes('CapabilityAxis') if s.node(n)['attrs'].get('is_axis')==1.0])} axes, "
          f"{len(s.nodes('Operator'))} faculties\n", flush=True)

    seen_mc, consults = set(), 0
    esc_seen, authored_seen, rethink_seen = set(), set(), set()
    for t in range(1, n_ticks + 1):
        adapter.master_tick()
        adapter.tick()
        for mc in s.nodes("MeasuredCapability"):
            a = s.node(mc)["attrs"]; key = (mc, a.get("note"))
            if key in seen_mc:
                continue
            seen_mc.add(key)
            print(f"  [tick {t:3d}] {a.get('metric')}={a.get('measured')}  {a.get('note')!r}")
        c = len([m for m in s.nodes("Impasse") if s.node(m)["attrs"].get("kind") == "frontier_stall"])
        if c > consults:
            consults = c
            print(f"  [tick {t:3d}] stalled -> method-teacher ({consults})")
        for mi in s.nodes("Impasse"):
            a = s.node(mi)["attrs"]
            if (a.get("kind") == "self_extend" or adapter.inner.neighbours(mi, "needs_tool")) and mi not in esc_seen:
                esc_seen.add(mi)
                ax = adapter.inner.neighbours(mi, "needs_tool")
                keys = s.node(ax[0])["attrs"].get("capability_keys") if ax else None
                print(f"  [tick {t:3d}] *** ESCALATED to ORDER-4 (needs a new tool) for {keys}")
        for op in s.nodes("Operator"):
            a = s.node(op)["attrs"]
            if a.get("authored_by_escalation") == 1.0 and op not in authored_seen:
                authored_seen.add(op)
                print(f"  [tick {t:3d}] *** AUTHORED FACULTY: {a.get('name')!r}  runner={a.get('runner')}  "
                      f"approach={a.get('approach')!r}")
        for rn in s.nodes("SelfReassessment"):
            if rn not in rethink_seen:
                rethink_seen.add(rn)
                print(f"  [tick {t:3d}] *** ORDER-6 self-rethink: {s.node(rn)['attrs'].get('summary')!r}")

    print("\n" + SEP)
    print("WHAT THE AGENT BUILT (self-authored under escalation):")
    authored = [s.node(op)["attrs"] for op in s.nodes("Operator")
                if s.node(op)["attrs"].get("authored_by_escalation") == 1.0]
    for a in authored:
        print(f"  authored faculty: {a.get('name')!r}  runner={a.get('runner')}  approach={a.get('approach')!r}")
    if not authored:
        print("  (no faculty authored yet — the ladder did not reach order-4 needs_tool in this many ticks)")
    print("\nWHAT THE AGENT UNDERSTANDS (its frontier):")
    for u in understanding(adapter):
        tag = " [teacher]" if u["from_teacher"] else ""
        print(f"  {str(u['keys']):<54} sat={u['saturation']} last={u['last_measured']} att={u['mf_stall']}{tag}")
    print(f"\n  {len(seen_mc)} measurements, {consults} consults, {len(esc_seen)} order-4 escalations, "
          f"{len(authored)} faculties AUTHORED, {len(rethink_seen)} self-rethinks.")
    print(SEP)


if __name__ == "__main__":
    main()
