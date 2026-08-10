"""rule_join_profile — BEFORE/AFTER measurement for the R10 join-index wave
(rule_mention_resolves_to_concept's O(held concepts x accumulated mentions)
equality join, named in docs/comprehension_decision_ledger.md Wave 3).

Boots a full-seed shadow-read WorldAdapter, runs a multi-turn conversation
(growing the accumulated-mentions side of the join every turn), and reports
per-rule cost via the engine's OWN `rule_costs()` self-instrumentation
(micros, count, progress) — the same instrument Wave 3 used, and the same
one scripts/rule_index_frame_scaling.py uses for a different rule.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/rule_join_profile.py
"""
from __future__ import annotations
import os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter

RULE = "rule_mention_resolves_to_concept"

TURNS = [
    "What do you know about the moon?",
    "Tell me a fact about topic number 0.",
    "Tell me a fact about topic number 1.",
    "Tell me a fact about topic number 2.",
    "Tell me a fact about topic number 3.",
    "Tell me a fact about topic number 4.",
    "Tell me a fact about topic number 5.",
    "Tell me a fact about topic number 6.",
    "Tell me a fact about topic number 7.",
    "Tell me a fact about topic number 8.",
    "Tell me a fact about topic number 9.",
    "Tell me a fact about topic number 10.",
    "Tell me a fact about topic number 11.",
    "Tell me a fact about topic number 12.",
    "Tell me a fact about topic number 13.",
    "Tell me a fact about topic number 14.",
    "Tell me a fact about topic number 15.",
    "Tell me a fact about topic number 16.",
    "Tell me a fact about topic number 17.",
    "Tell me a fact about topic number 18.",
]


def _rule_us(a, name):
    for rname, micros, count, prog in a.s._inner.rule_costs():
        if rname == name:
            return micros, count, prog
    return (0, 0, 0)


def main():
    a = WorldAdapter(seeds=(), shadow_read=True)
    print("=" * 90)
    print(f"R10 join-index profile — {RULE}")
    print("=" * 90)
    n_concepts = len(a.s.nodes("Concept"))
    print(f"boot: {n_concepts} Concept nodes held")
    print(f"{'turn':>4} | {'mentions':>8} | {'total_ms':>9} | {'shadow_ms':>9} | "
          f"{'mention_rule_us':>15} | {'count':>6} | {'progress':>8}")
    print("-" * 90)
    rows = []
    for i, text in enumerate(TURNS):
        a.s._inner.reset_rule_costs()
        t0 = time.perf_counter()
        a.converse(text, speech_act="question" if i == 0 else "statement")
        dt = (time.perf_counter() - t0) * 1e3
        mid = a._last_turn_inbound
        shadow_ms = a.s.node(mid)["attrs"].get("shadow_latency_ms")
        n_mentions = len(a.s.nodes("Mention"))
        us, cnt, prog = _rule_us(a, RULE)
        rows.append((i, n_mentions, dt, shadow_ms, us, cnt, prog))
        print(f"{i:>4} | {n_mentions:>8} | {dt:>9.2f} | "
              f"{(shadow_ms or 0):>9.2f} | {us:>15} | {cnt:>6} | {prog:>8}")

    top = sorted(a.s._inner.rule_costs(), key=lambda r: -r[1])[:8]
    print()
    print("Top 8 rules by accumulated cost (last turn's pass):")
    for name, micros, count, prog in top:
        print(f"  {name:<45} {micros:>10} us  count={count:<6} progress={prog}")

    print()
    steady = rows[-8:]
    avg_total = sum(r[2] for r in steady) / len(steady)
    avg_shadow = sum(r[3] or 0 for r in steady) / len(steady)
    avg_rule_us = sum(r[4] for r in steady) / len(steady)
    print(f"steady-state (last 8 turns): avg total={avg_total:.2f}ms "
          f"avg shadow={avg_shadow:.2f}ms avg {RULE}={avg_rule_us:.1f}us")


if __name__ == "__main__":
    main()
