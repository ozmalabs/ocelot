#!/usr/bin/env python3
"""variation_ops v1.20.0 (tranche 23): the `deep_reader_correct` family.

VariationOp{deep_reader_correct}: requires_kind 'comprehension' (the agent's
own recurring shallow/deep reader disagreement, comprehension_health),
cue_head 'replay', priority 9 (ahead of reply_ablation, 20). Builder:
domains/reflective_faculty._compose_deep_reader_correct. It replaces the
misreading arbitration rule with a copy guarded by the deep reader's verdict,
and adds a neutral-receipt arbitration and reply for that disagreement.
Judged by the production-path replay. Idempotent.
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "seeds/variation_ops.json"
VERSION = "1.20.0"
d = json.loads(P.read_text())
if tuple(map(int, d["version"].split("."))) >= tuple(map(int, VERSION.split("."))):
    print("already applied", d["version"])
    raise SystemExit(0)
lid = max(n.get("local_id", 0) for n in d["nodes"]) + 1
d["nodes"].append({"local_id": lid, "type": "VariationOp", "attrs": {
    "name": "deep_reader_correct", "family": "deep_reader_correct", "priority": 9,
    "cue_head": "replay", "also_head": "", "requires_kind": "comprehension",
    "keywords_text": "deep reader shadow divergence comprehension correct arbitration veto receipt"}})
d["description"] += (" v1.20.0 (2026-10-10, tranche 23): `deep_reader_correct` (requires_kind 'comprehension', "
                     "priority 9) -- the deep reader's verdict vetoes the shallow arbitration for the agent's own "
                     "recurring disagreement and answers with the neutral receipt (scripts/gen_deep_reader_correct_op.py).")
d["version"] = VERSION
P.write_text(json.dumps(d, indent=1, ensure_ascii=True) + "\n")
print("variation_ops", VERSION)
