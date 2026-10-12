#!/usr/bin/env python3
"""variation_ops v1.19.0 (tranche 22): the `disposition_generalise` family.

VariationOp{disposition_generalise}: requires_kind 'unanswered' (the agent's
own recurring unanswered turn class, seeds/unanswered_gap.json), cue_head
'replay' (the conversation bundle), priority 9 -- after cue_set_edit (10 is for
instruction concerns only, so no competition), ahead of reply_ablation (20).
Builder: domains/reflective_faculty._compose_disposition_generalise. It makes
add-only copies of a held arbitration rule and its reply rule, with one guard
relaxed to the unanswered turn's own evidence, judged by the production-path
replay. Idempotent.
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "seeds/variation_ops.json"
VERSION = "1.19.0"
d = json.loads(P.read_text())
if tuple(map(int, d["version"].split("."))) >= tuple(map(int, VERSION.split("."))):
    print("already applied", d["version"])
    raise SystemExit(0)
lid = max(n.get("local_id", 0) for n in d["nodes"]) + 1
d["nodes"].append({"local_id": lid, "type": "VariationOp", "attrs": {
    "name": "disposition_generalise", "family": "disposition_generalise", "priority": 9,
    "cue_head": "replay", "also_head": "", "requires_kind": "unanswered",
    "keywords_text": "disposition generalise arbitration receipt unanswered reply guard relax"}})
d["description"] += (" v1.19.0 (2026-10-10, tranche 22): `disposition_generalise` (requires_kind 'unanswered', "
                     "priority 9) -- add-only generalisation of a held arbitration+reply rule pair to the agent's own "
                     "unanswered turn class, one guard relaxed (scripts/gen_disposition_generalise_op.py).")
d["version"] = VERSION
P.write_text(json.dumps(d, indent=1, ensure_ascii=True) + "\n")
print("variation_ops", VERSION)
