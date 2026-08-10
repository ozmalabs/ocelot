"""jabberwock_how_do_you — the operational self-introspection demo.

The long tail of "how do you X?" self-questions used to DEFLECT ("I can't say
precisely how I learn."). The agent IS its own process knowledge as graph data;
now it INTROSPECTS it. A reflexive "how do you <verb>" process-question the agent
holds a true self-account for (a taught SelfProcess: learning=collapse,
perceiving=sd-decode, world-attachment=adapter-ingest) is answered SUBSTANTIVELY
and TRUTHFULLY from that held account; a process it genuinely has no account for
keeps the honest floor.

Shows the BEFORE (an agent booted without the taught accounts -> the deflection)
next to the AFTER (the full agent -> the substantive true account), so the delta
is the HELD self-knowledge, not anything hardcoded in the answer path.

    PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_how_do_you.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds


SUBSTANTIVE = [
    "How do you learn something new?",
    "How do you learn?",
    "How do you perceive?",
    "How does a world attach to you?",
]
HONEST_FLOOR = [
    "How do you dream?",
]


def main() -> int:
    before = WorldAdapter(seeds=())
    load_all_seeds(before, skip=("self_processes",))   # no taught accounts held
    after = WorldAdapter(seeds=())
    load_all_seeds(after)                              # holds the taught accounts

    print("=" * 78)
    print("SUBSTANTIVE — the agent introspects how it OPERATES (held self-accounts)")
    print("=" * 78)
    for q in SUBSTANTIVE:
        print(f"\nQ: {q}")
        print(f"  BEFORE (no held account): {before.answer_question(q)!r}")
        print(f"  AFTER  (held account):    {after.answer_question(q)!r}")

    print("\n" + "=" * 78)
    print("HONEST FLOOR — a process it genuinely has no self-account for")
    print("=" * 78)
    for q in HONEST_FLOOR:
        print(f"\nQ: {q}")
        print(f"  -> {after.answer_question(q)!r}")

    print("\n" + "=" * 78)
    print("UNCHANGED — how it IS / how it is SHAPED / who it is")
    print("=" * 78)
    for q in ("How are you organised?", "What shape are you?", "What are you?"):
        print(f"\nQ: {q}")
        print(f"  -> {after.answer_question(q)!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
