"""LAUNCH the agent's SELF-EXTENSION over the dynamic-communication goal.

Boots the agent with its communication concepts + the expression genus + the full self-driving
stack (autonomy -> investigation -> teacher -> escalation -> the code-writing cortex + self-
modification), sets the real teacher, and PUMPS. The agent reasons from its own communication
concepts, consults the teacher on method, and uses its self-modification features (author -> emit
-> cargo check -> rebuild -> reload, guarded + audited) to extend itself. No emit/build by hand —
the agent does it. The driver only pumps and reports what the agent did.

Run: SPEECH_TEACHER=real PYTHONPATH=.:runners/dsl/python python -m scripts.extend_communication [rounds]
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from substrate.seed_loader import manifest_for

SEP = "=" * 84


def main():
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    print(SEP)
    print("LAUNCH SELF-EXTENSION — agent extends itself for a dynamic communication set")
    print(SEP)
    a = boot()                                   # autonomy + genus + teacher + escalation
    for sid in ("pragmatics", "ling_pragmatics", "discourse"):   # more communication concepts
        try:
            a.inner.load_seed_manifest(manifest_for(sid), a.agent)
        except Exception as e:
            print(f"  (seed {sid} skipped: {e})")
    # boot the agent's code-writing cortex (its author -> cargo-check -> install self-mod loop)
    cx = None
    try:
        from domains.code_writing_cortex import CodeWritingCortex
        cx = CodeWritingCortex(a.s, agent=a.agent).install()
        print("  code-writing cortex installed (self-modification active)")
    except Exception as e:
        print(f"  (code-writing cortex unavailable: {e})")
    print(f"  teacher={os.environ.get('SPEECH_TEACHER','real')}; pumping {rounds} rounds\n",
          flush=True)

    def snap():
        return {
            "PrimitiveSpec": len(a.s.nodes("PrimitiveSpec")),
            "ReplacementTarget": len(a.s.nodes("ReplacementTarget")),
            "Draft": len(a.s.nodes("Draft")) if "Draft" in {a.s.node(n)["type"] for n in a.s.nodes()[:1]} or True else 0,
            "Operator_authored": len([o for o in a.s.nodes("Operator")
                                      if a.s.node(o)["attrs"].get("authored_by_escalation") == 1.0]),
            "Subroutine": len(a.s.nodes("Subroutine")),
            "Impasse": len(a.s.nodes("Impasse")),
        }

    for t in range(1, rounds + 1):
        a.master_tick(); a.tick()
        if cx is not None:
            try:
                fired = cx.tick()
                if fired:
                    print(f"  [r{t:2d}] cortex fired: {fired}", flush=True)
            except Exception as e:
                print(f"  [r{t:2d}] cortex err: {type(e).__name__}: {e}", flush=True)

    print("\n" + SEP)
    s = snap()
    print(f"  what the agent produced: {s}")
    for ty, label in (("PrimitiveSpec", "specced primitive"), ("Subroutine", "authored faculty")):
        for n in a.s.nodes(ty):
            at = a.s.node(n)["attrs"]
            print(f"    {label}: {at.get('name')}  {str(at.get('purpose') or at.get('why_new') or '')[:90]}")
    audit = os.path.join(ROOT, "var", "self_mod_audit.log")
    if os.path.exists(audit):
        import collections
        lines = open(audit).read().strip().splitlines()[-6:]
        print(f"  self-mod audit tail ({len(lines)}):")
        for ln in lines:
            print(f"    {ln[:110]}")
    print(SEP)


if __name__ == "__main__":
    main()
