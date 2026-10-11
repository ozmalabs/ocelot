#!/usr/bin/env python3
"""cognitive_scheduler v1.0.2 (tranche 22): the experiment-close demand fires on
a BOOLEAN conclusion_ready.

The agent's judge rules (reflective_faculty._compose_experiment_rule) write
Experiment.conclusion_ready = True. supervise_ready_experiment_close and its
rearm demanded `conclusion_ready > 0`, and the native Gt of a bool against 0
is False. So on the production path the `close` host action, which teaches the
verdict and performs adoptions, was never requested: measured in tranche 22, two
supported, regression-free experiments were never adopted. The guard is now
Or(conclusion_ready == True, conclusion_ready > 0). Idempotent.
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "seeds/cognitive_scheduler.json"
VERSION = "1.0.2"
d = json.loads(P.read_text())
if tuple(map(int, d["version"].split("."))) >= tuple(map(int, VERSION.split("."))):
    print("already applied", d["version"])
    raise SystemExit(0)
GT = {"type": "Gt", "a": {"type": "Attr", "node": {"type": "Var", "name": "source"}, "key": "conclusion_ready"},
      "b": {"type": "Lit", "value": 0}}
FIX = {"type": "Or", "items": [
    {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "source"}, "key": "conclusion_ready"},
     "b": {"type": "Lit", "value": True}}, GT]}
n = 0


def walk(x):
    global n
    if isinstance(x, dict):
        for k, v in list(x.items()):
            if v == GT:
                x[k] = FIX
                n += 1
            else:
                walk(v)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            if v == GT:
                x[i] = FIX
                n += 1
            else:
                walk(v)


for r in d["rules"]:
    if r["name"] in ("supervise_ready_experiment_close", "supervise_ready_experiment_close_rearm"):
        walk(r)
assert n >= 2, n
d["version"] = VERSION
P.write_text(json.dumps(d, indent=1, ensure_ascii=True) + "\n")
print("cognitive_scheduler", VERSION, "guards fixed:", n)
