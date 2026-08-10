"""Drive the StructuredDataWorld over the 12-task bank, twice — show that
the second pass costs ~0 teacher calls because the substrate has
grounded the (FormatID, CorruptionPattern, ParsingStrategy) graph data
during the first pass.

Per CLAUDE.md the world adapter does the I/O translation; the
substrate (Rust) holds the learned strategies as graph nodes/edges.
This script is a thin runner — load the native substrate, hand the
world the task bank + the teacher stub, run it twice, print the deltas.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains.structured_data_world import (
    StructuredDataWorld,
    default_task_bank,
    teacher_stub,
)


def short_repr(v, n=40):
    r = repr(v)
    return r if len(r) <= n else r[:n] + "..."


def main() -> int:
    s = _native.Substrate()
    tasks = default_task_bank()
    world = StructuredDataWorld(s, tasks, teacher_stub)

    print("=" * 72)
    print("Pass 1 — substrate boots cold, every shape needs the teacher")
    print("=" * 72)
    log1 = world.run()
    summ1 = StructuredDataWorld.summary(log1)
    print(f"Tasks: {summ1['tasks']}  Matched: {summ1['matched']}  "
          f"Teacher calls: {summ1['teacher_calls']}")
    print()
    print(f"FormatID nodes grounded:        {len(s.nodes('FormatID'))}")
    print(f"CorruptionPattern nodes:        {len(s.nodes('CorruptionPattern'))}")
    print(f"ParsingStrategy nodes:          {len(s.nodes('ParsingStrategy'))}")
    print(f"StructuredDataObservation nodes: {len(s.nodes('StructuredDataObservation'))}")
    print()

    print("Per-task (pass 1):")
    for i, e in enumerate(log1, 1):
        text_short = e["text"].replace("\n", "\\n")
        if len(text_short) > 36:
            text_short = text_short[:33] + "..."
        ok = "OK " if e["matched"] else "MIS"
        print(f"  {i:2}. [{ok}] fmt={e['format_id']:7s} "
              f"corr={e['corruption']:18s} "
              f"asks={len(e['gaps_asked'])} "
              f"teach={e['teacher_calls']} "
              f"parsed={short_repr(e['parsed'])}")

    print()
    print("=" * 72)
    print("Pass 2 — same bank, but the substrate's strategy table is grounded")
    print("=" * 72)
    log2 = world.run()
    summ2 = StructuredDataWorld.summary(log2)
    print(f"Tasks: {summ2['tasks']}  Matched: {summ2['matched']}  "
          f"Teacher calls: {summ2['teacher_calls']}")
    print()

    print("Cumulative learning:")
    print(f"  pass 1 teacher calls: {summ1['teacher_calls']}")
    print(f"  pass 2 teacher calls: {summ2['teacher_calls']}")
    print(f"  reduction:            {summ1['teacher_calls'] - summ2['teacher_calls']} "
          f"({(1 - summ2['teacher_calls']/max(1, summ1['teacher_calls']))*100:.0f}%)")
    print()

    print("Example log entries (pass 1, showing the grounding cycle):")
    for idx in (0, 4, 6):  # clean JSON, JSON trailing comma, YAML tab
        e = log1[idx]
        print(f"  text: {e['text']!r}")
        print(f"    gap asked   : {e['gaps_asked']}")
        print(f"    format ID   : {e['format_id']}")
        print(f"    corruption  : {e['corruption']}")
        print(f"    parsed      : {e['parsed']!r}")
        print(f"    expected    : {e['expected']!r}")
        print(f"    matched     : {e['matched']}")
        print(f"    teacher_calls: {e['teacher_calls']}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
