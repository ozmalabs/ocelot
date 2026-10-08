#!/usr/bin/env python3
"""Independent audit of the v1.2 native shared-evidence replay."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
raw=json.loads((ROOT/"evaluation/reports/substrate_shared_evidence_rule_propagation_v1_2_20260925.json").read_text())
lock_path=ROOT/"evaluation/substrate_capability/shared_evidence_rule_propagation_v1_2_lock_20260925.json"
lock=json.loads(lock_path.read_text())
assert raw["locked_inputs"]==lock["locked_inputs"]
assert hashlib.sha256(lock_path.read_bytes()).hexdigest()==raw["lock_sha256"]
paths={"protocol_sha256":ROOT/"docs/research/engine_substrate/SUBSTRATE_SHARED_EVIDENCE_RULE_PROPAGATION_V1_2_AMENDMENT_20260925.md",
"runner_sha256":ROOT/"scripts/substrate_shared_evidence_rule_propagation_v1_2.py",
"rewrite_sha256":ROOT/"runners/dsl/src/rewrite.rs","substrate_sha256":ROOT/"runners/dsl/src/substrate.rs","py_binding_sha256":ROOT/"runners/dsl/src/py.rs"}
assert all(hashlib.sha256(p.read_bytes()).hexdigest()==lock["locked_inputs"][k] for k,p in paths.items())
assert len(raw["runs"])==36 and len(raw["paired"])==12
assert len({x["native_extension_sha256"] for x in raw["runs"]})==1
assert all(x["all_settled"] for x in raw["runs"])
assert all(x["all_expected"] for x in raw["runs"] if x["arm"] in ("full","scoped"))
assert all(x["full_scoped_values_equal"] for x in raw["paired"])
for pair in raw["paired"]:
    omitted=next(x for x in raw["runs"] if x["size"]==pair["size"] and x["replicate"]==pair["replicate"] and x["arm"]=="scoped_omit_boundary0")
    wrong=omitted["checkpoints"][1]["wrong_state_indices"]
    assert wrong==([] if pair["size"]==1 else [0,1])
    assert all(not cp["wrong_state_indices"] for cp in omitted["checkpoints"] if cp["checkpoint"]!="activate_1")
assert all(raw["checks"].values())
print(json.dumps({"audit":"pass","workers":36,"pairs":12,"full_scoped_semantic_parity":True,
"omission_control_stale_state_indices_by_size":{str(n):([] if n==1 else [0,1]) for n in (1,2,4,8)},
"checks":raw["checks"]},indent=2))
