#!/usr/bin/env python3
"""Independent audit for the read-only shared-evidence scope replay."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
raw_path=ROOT/"evaluation/reports/substrate_conversation_readonly_boundary_scale_20260925.json"
lock_path=ROOT/"evaluation/substrate_capability/conversation_readonly_boundary_scale_lock_20260925.json"
raw=json.loads(raw_path.read_text()); lock=json.loads(lock_path.read_text())
assert raw["locked_inputs"]==lock["locked_inputs"]
assert hashlib.sha256(lock_path.read_bytes()).hexdigest()==raw["lock_sha256"]
paths={"preregistration_sha256":ROOT/"docs/research/engine_substrate/SUBSTRATE_CONVERSATION_READONLY_BOUNDARY_SCALE_PREREG_20260925.md",
"runner_sha256":ROOT/"scripts/substrate_conversation_readonly_boundary_scale.py","seed_sha256":ROOT/"seeds/conversation_deliberation_phase4a.json",
"materializer_sha256":ROOT/"domains/conversation_deliberation.py","rewrite_sha256":ROOT/"runners/dsl/src/rewrite.rs",
"substrate_sha256":ROOT/"runners/dsl/src/substrate.rs","py_binding_sha256":ROOT/"runners/dsl/src/py.rs"}
assert all(hashlib.sha256(p.read_bytes()).hexdigest()==lock["locked_inputs"][key] for key,p in paths.items())
seed=json.loads(paths["seed_sha256"].read_text())
serialized=json.dumps(seed["rules"])
assert "supports_candidate" not in serialized and "SharedGroundingEvidence" not in serialized
assert len(raw["runs"])==24 and len(raw["paired"])==12
assert all(x["all_expected_task_outcomes"] and x["outcome"]["status"]=="fixed_point" for x in raw["runs"])
assert all(x["projection_equal"] and x["fixed_point_both"] for x in raw["paired"])
assert {(x["size"],x["replicate"]) for x in raw["paired"]}=={(n,r) for n in (1,2,4,8) for r in range(3)}
print(json.dumps({"audit":"pass","workers":24,"pairs":12,"all_semantic_gates":True,
"rule_reads_shared_evidence_edge":False,"paired_projection_parity_by_size":{str(n):sum(x["projection_equal"] for x in raw["paired"] if x["size"]==n) for n in (1,2,4,8)}},indent=2))
