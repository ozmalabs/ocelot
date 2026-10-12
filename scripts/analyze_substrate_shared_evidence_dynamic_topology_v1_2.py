#!/usr/bin/env python3
"""Independent audit for randomized dynamic-boundary closure v1.2."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
raw=json.loads((ROOT/"evaluation/reports/substrate_shared_evidence_dynamic_topology_v1_2_20260925.json").read_text())
lock_path=ROOT/"evaluation/substrate_capability/shared_evidence_dynamic_topology_v1_2_lock_20260925.json"
lock=json.loads(lock_path.read_text())
assert raw["locked_inputs"]==lock["locked_inputs"]
assert hashlib.sha256(lock_path.read_bytes()).hexdigest()==raw["lock_sha256"]
paths={"protocol_sha256":ROOT/"docs/research/engine_substrate/SUBSTRATE_SHARED_EVIDENCE_DYNAMIC_TOPOLOGY_V1_2_AMENDMENT_20260925.md",
"runner_sha256":ROOT/"scripts/substrate_shared_evidence_dynamic_topology_v1_2.py","rewrite_sha256":ROOT/"runners/dsl/src/rewrite.rs",
"substrate_sha256":ROOT/"runners/dsl/src/substrate.rs","py_binding_sha256":ROOT/"runners/dsl/src/py.rs"}
assert all(hashlib.sha256(p.read_bytes()).hexdigest()==lock["locked_inputs"][k] for k,p in paths.items())
assert len(raw["runs"])==81 and len(raw["paired"])==27
assert len({x["native_extension_sha256"] for x in raw["runs"]})==1
assert all(x["all_settled"] for x in raw["runs"])
for n in (12,24,48):
    for seed in (20260925,20260926,20260927):
        group=[x for x in raw["runs"] if x["size"]==n and x["graph_seed"]==seed]
        assert len(group)==9
        assert {x["tree_edge_count"] for x in group}=={n-1}
        assert {x["extra_edge_count"] for x in group}=={n//4}
for p in raw["paired"]:
    assert p["full_scoped_projection_equal"] and p["full_scoped_expected"]
    omitted=next(x for x in raw["runs"] if (x["size"],x["graph_seed"],x["replicate"],x["arm"])==(p["size"],p["graph_seed"],p["replicate"],"scoped_omit_boundary0"))
    cp=omitted["checkpoints"]
    for i in (1,2,3,4): assert cp[i]["wrong_state_indices"]==[0,1]
    assert not cp[0]["wrong_state_indices"] and not cp[5]["wrong_state_indices"]
for run in raw["runs"]:
    assert len(run["checkpoints"])==6
    for cp in run["checkpoints"]:
        assert cp["mutation_ns"]==cp["pre_closure_mutation_ns"]+cp["post_closure_graph_mutation_ns"]
        assert cp["closure_wall_ns"]>=0 and cp["mutation_ns"]>=0
assert all(raw["checks"].values())
summary=[]
for n in (12,24,48):
    row=next(x for x in raw["summaries"] if x["size"]==n)
    scoped=[x for x in raw["runs"] if x["size"]==n and x["arm"]=="scoped"]
    full=[x for x in raw["runs"] if x["size"]==n and x["arm"]=="full"]
    summary.append({"size":n,"pairs":9,"full_candidates":row["median_full_candidates"],"scoped_candidates":row["median_scoped_candidates"],
                    "full_term_evaluations":row["median_full_term_evaluations"],"scoped_term_evaluations":row["median_scoped_term_evaluations"],
                    "full_closure_ms":round(row["median_full_closure_wall_ns"]/1e6,3),"scoped_closure_ms":round(row["median_scoped_closure_wall_ns"]/1e6,3),
                    "full_mutation_ms":round(statistics.median(x["mutation_ns_total"] for x in full)/1e6,3),
                    "scoped_mutation_ms":round(statistics.median(x["mutation_ns_total"] for x in scoped)/1e6,3)})
print(json.dumps({"audit":"pass","workers":81,"full_scoped_pairs":27,"omission_controls":27,"measurements":summary,"checks":raw["checks"]},indent=2))
