"""Ask the jabberwock what it NEEDS to give itself a memory-management self-faculty.
Per the user: ask it. The agent's OWN self-extension loop (domains/self_extension.
SelfExtensionDriver.extend) IS the "what do I need to build X" mechanism — its
DIAGNOSE step reads the gap's definition and classifies the wall-kind (reducible to
held / needs-primitive / acquirable / design-from-scratch), names the spike (the
required action), then DESIGN/BUILD/SELF-VERIFY/WIRE as far as it can. This shell only
poses the gap (the faculty + an English definition) and reports what the agent did and
what it says it needs. No reasoning added.
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains import self_extension as SE       # noqa: E402

# The gap = the faculty it lacked when we asked it (it walled on "what do you have to
# manage your memory"). Pose THAT as the stall; ask the self-extension loop what it
# needs to build it.
STALL = SE.Stall(
    question_id="memory_self_faculty",
    asked="give yourself a faculty to assess and manage your own memory while you "
          "watch many videos, so you do not run out of memory",
    gap_ops=["memory_self_management"],
    definition={
        "memory_self_management":
            "a faculty by which the agent observes its own state growth (nodes / "
            "edges it accumulates as it ingests videos), judges what to keep versus "
            "consolidate versus forget, and bounds itself so it never exhausts "
            "memory — self-knowledge of, and control over, its own resource use"},
    object_desc={"subject": "the agent's own graph state"},
    answer=None)


def main():
    print("=" * 78)
    print("ASKING THE JABBERWOCK — what do you need to give yourself a memory faculty?")
    print("=" * 78)
    driver = SE.SelfExtensionDriver()
    ext = driver.extend(STALL)
    print(f"  asked: {STALL.asked}\n")
    # report what the agent's machinery did, generically (field names vary by version)
    def dump(obj, indent="  "):
        for k in dir(obj):
            if k.startswith("_"):
                continue
            try:
                v = getattr(obj, k)
            except Exception:
                continue
            if callable(v):
                continue
            print(f"{indent}{k}: {str(v)[:240]}")
    print("  EXTENSION (what the loop achieved):")
    dump(ext)
    rungs = getattr(ext, "rungs", None) or []
    for i, r in enumerate(rungs):
        print(f"\n  RUNG {i} — the agent's diagnose/design/build trace:")
        dump(r, indent="    ")
    print("=" * 78)


if __name__ == "__main__":
    raise SystemExit(main())
