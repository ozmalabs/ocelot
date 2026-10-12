#!/usr/bin/env python3
"""Independent structural audit of the locked conversation scale report."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
raw = json.loads((ROOT / "evaluation/reports/substrate_conversation_frame_scoped_scale_v1_1_20260925.json").read_text())
assert len(raw["runs"]) == 24
assert len(raw["paired"]) == 12
assert all(raw["checks"].values())
assert all(x["projection_equal"] and x["fixed_point_both"] for x in raw["paired"])
assert {(x["size"], x["replicate"]) for x in raw["paired"]} == {(n, r) for n in (1, 2, 4, 8) for r in range(3)}
assert all(x["outcome"]["status"] == "fixed_point" for x in raw["runs"])
assert all(x["all_expected_task_outcomes"] for x in raw["runs"])
print(json.dumps({"independent_audit": "pass", "workers": len(raw["runs"]), "pairs": len(raw["paired"]), "sizes": [1, 2, 4, 8], "reps_per_size": 3}))
