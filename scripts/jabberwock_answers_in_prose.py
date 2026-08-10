"""jabberwock_answers_in_prose — DEMO: self/meta chat replies are FLUENT PROSE,
never a raw k=v dict dump. Drives the real chat path (WorldAdapter.answer_
question — the same seam scripts/jabberwock_knows_itself.py already gates),
prints the verbatim before/after-shaped answers for a battery of self/meta
questions (the deliverable — what the agent actually said), and asserts none
of them carries the old raw-dict-fallback's machine-tail fingerprints.

  PYTHONPATH=runners/dsl/python:. python3 scripts/jabberwock_answers_in_prose.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for p in (str(_ROOT), str(_ROOT / "runners" / "dsl" / "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

_RAW_DUMP_TELLS = ("found=True", "; rule_name=", "meta_shapes=[", "detail=[{")

_BATTERY = [
    "What does hop_descend_gradient do?",
    "How are you organised?",
    "What shape are you?",
    "which parts of me touch chosen_action?",
    "which rules do you have about navigation?",
]


def main() -> int:
    print("=" * 78)
    print("BOOTING the full seed set...")
    agent = WorldAdapter(seeds=())
    rep = load_all_seeds(agent)
    print(f"boot: {rep['loaded']}/{rep['total']} seeds loaded, {len(rep.get('failed') or [])} failed")
    print("-" * 78)

    ok = True
    for q in _BATTERY:
        ans = agent.answer_question(q)
        ans = ans if isinstance(ans, str) else str(ans)
        print(f"Q: {q}")
        print(f"A: {ans}")
        bad = [t for t in _RAW_DUMP_TELLS if t in ans]
        if bad:
            ok = False
            print(f"   ** RAW-DICT FALLBACK STILL PRESENT: {bad} **")
        print("-" * 78)

    print("ALL FLUENT (no raw k=v dump)" if ok else "**FAILED** — raw dict dump survived")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
