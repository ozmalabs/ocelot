#!/usr/bin/env python3
"""Independent audit of the locked topology/fan-out scale report."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
raw=json.loads((ROOT/"evaluation/reports/substrate_shared_evidence_topology_scale_20260925.json").read_text())
lock_path=ROOT/"evaluation/substrate_capability/shared_evidence_topology_scale_lock_20260925.json"
lock=json.loads(lock_path.read_text())
assert raw["locked_inputs"]==lock["locked_inputs"]
assert hashlib.sha256(lock_path.read_bytes()).hexdigest()==raw["lock_sha256"]
paths={"protocol_sha256":ROOT/"docs/research/engine_substrate/SUBSTRATE_SHARED_EVIDENCE_TOPOLOGY_SCALE_PREREG_20260925.md",
"runner_sha256":ROOT/"scripts/substrate_shared_evidence_topology_scale.py","rewrite_sha256":ROOT/"runners/dsl/src/rewrite.rs",
"substrate_sha256":ROOT/"runners/dsl/src/substrate.rs","py_binding_sha256":ROOT/"runners/dsl/src/py.rs"}
assert all(hashlib.sha256(p.read_bytes()).hexdigest()==lock["locked_inputs"][k] for k,p in paths.items())
assert len(raw["runs"])==108 and len(raw["paired"])==36 and len(raw["summaries"])==12
assert len({x["native_extension_sha256"] for x in raw["runs"]})==1
assert all(x["all_settled"] for x in raw["runs"])
assert all(x["full_expected"] and x["scoped_expected"] and x["full_scoped_values_equal"] for x in raw["paired"])
assert all(x["omission_control_sensitive"] for x in raw["paired"])
for run in raw["runs"]:
    cps=run["checkpoints"]
    assert len(cps)==6
    if run["arm"]=="scoped_omit_boundary0":
        assert cps[1]["wrong_state_indices"]==[0,1]
        assert cps[2]["wrong_state_indices"]==[0,1]
        assert cps[4]["wrong_state_indices"]==[0,1]
        assert not cps[0]["wrong_state_indices"] and not cps[3]["wrong_state_indices"] and not cps[5]["wrong_state_indices"]
    else:
        assert all(not cp["wrong_state_indices"] for cp in cps)
metrics=("median_full_candidates","median_scoped_candidates","median_full_term_evaluations","median_scoped_term_evaluations")
for n in (8,16,32,64):
    rows=[x for x in raw["summaries"] if x["size"]==n]
    assert len({tuple(x[k] for k in metrics) for x in rows})==1
assert all(raw["checks"].values())
print(json.dumps({"audit":"pass","workers":108,"full_scoped_pairs":36,"sensitive_omission_controls":36,
"work_counters_topology_invariant_at_each_size":True,"checks":raw["checks"]},indent=2))
