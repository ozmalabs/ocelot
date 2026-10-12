#!/usr/bin/env python3
"""Independent audit of the connected deliberation boundary replay."""
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
raw=json.loads((ROOT/"evaluation/reports/substrate_conversation_connected_frame_scale_20260925.json").read_text())
lock=json.loads((ROOT/"evaluation/substrate_capability/conversation_connected_frame_scale_lock_20260925.json").read_text())
assert raw["locked_inputs"]==lock["locked_inputs"]
assert hashlib.sha256((ROOT/"evaluation/substrate_capability/conversation_connected_frame_scale_lock_20260925.json").read_bytes()).hexdigest()==raw["lock_sha256"]
locked_paths={"protocol_sha256":ROOT/"docs/research/engine_substrate/SUBSTRATE_CONVERSATION_CONNECTED_FRAME_SCALE_PREREG_20260925.md",
              "runner_sha256":ROOT/"scripts/substrate_conversation_connected_frame_scale.py",
              "seed_sha256":ROOT/"seeds/conversation_deliberation_phase4a.json",
              "materializer_sha256":ROOT/"domains/conversation_deliberation.py",
              "rewrite_sha256":ROOT/"runners/dsl/src/rewrite.rs",
              "substrate_sha256":ROOT/"runners/dsl/src/substrate.rs",
              "py_binding_sha256":ROOT/"runners/dsl/src/py.rs"}
assert all(hashlib.sha256(p.read_bytes()).hexdigest()==lock["locked_inputs"][k] for k,p in locked_paths.items())
assert len(raw["runs"])==24 and len(raw["paired"])==12
assert all(x["outcome"]["status"]=="fixed_point" for x in raw["runs"])
assert all(x["all_expected_task_outcomes"] for x in raw["runs"] if x["size"]==1)
by_size={n:[x for x in raw["paired"] if x["size"]==n] for n in (1,2,4,8)}
assert all(x["projection_equal"] for x in by_size[1])
assert all(not x["projection_equal"] for n in (2,4,8) for x in by_size[n])
assert all(not x["all_expected_task_outcomes"] for x in raw["runs"] if x["size"]>1 and x["arm"]=="scoped")
assert all(x["all_expected_task_outcomes"] for x in raw["runs"] if x["size"]==2 and x["arm"]=="full")
assert all(not x["all_expected_task_outcomes"] for x in raw["runs"] if x["size"] in (4,8))
report={"audit":"pass; semantic benchmark gate failed as preregistered failure case", "workers":24,
        "fixed_point_workers":sum(x["outcome"]["status"]=="fixed_point" for x in raw["runs"]),
        "projection_parity_pairs_by_size":{str(n):sum(x["projection_equal"] for x in by_size[n]) for n in by_size},
        "decision_pass_workers_by_size_arm":{f"{n}_{arm}":sum(x["all_expected_task_outcomes"] for x in raw["runs"] if x["size"]==n and x["arm"]==arm) for n in by_size for arm in ("full","scoped")}}
print(json.dumps(report,indent=2))
