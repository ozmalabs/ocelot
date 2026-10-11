#!/usr/bin/env python3
"""self_optimisation v1.5.0 (tranche 23): the speed judge does not override a
correctness-family verdict.

experiment_dispatch._stamp_performance_baseline gives EVERY comprehension-kind
experiment a performance_objective, and judge_performance_experiment_outcome
then overrides the generic verdict by comparing the child's replay avg_turn_ms
(a whole production turn, ~320 ms) with the parent's shadow-latency average
(the deep read alone, ~70 ms) -- so it refutes every comprehension experiment.
Measured in tranche 23: a deep_reader_correct trial that fixed its flagged turn
with 0 regressions was ruled 'refuted' after mark_adopt_ready had already
fired. A delta marked deep_reader_edit carries a correctness objective (the
reader's misreading), so the speed judge now skips it. Idempotent.
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "seeds/self_optimisation.json"
VERSION = "1.5.0"
d = json.loads(P.read_text())
if tuple(map(int, d["version"].split("."))) >= tuple(map(int, VERSION.split("."))):
    print("already applied", d["version"])
    raise SystemExit(0)
r = next(r for r in d["rules"] if r["name"] == "judge_performance_experiment_outcome")
r["where"]["items"].append({"type": "Not", "arg": {"type": "Eq", "a": {
    "type": "Attr", "node": {"type": "Var", "name": "delta"}, "key": "deep_reader_edit"},
    "b": {"type": "Lit", "value": 1.0}}})
d["description"] += (" || v1.5.0 (2026-10-10, tranche 23): judge_performance_experiment_outcome skips a delta "
                     "marked deep_reader_edit -- that family's objective is the reader's correctness, and the "
                     "speed comparison (replay turn ms vs shadow-read ms) refuted every comprehension trial "
                     "(scripts/gen_perf_judge_correctness_exempt.py).")
d["version"] = VERSION
P.write_text(json.dumps(d, indent=1, ensure_ascii=True) + "\n")
print("self_optimisation", VERSION)
