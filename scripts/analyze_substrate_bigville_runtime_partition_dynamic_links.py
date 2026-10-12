#!/usr/bin/env python3
"""Independent state/residual and provenance audit for Bigville dynamic links."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_bigville_runtime_partition_dynamic_links_20260925.json"
LOCK_PATH=ROOT/"evaluation/substrate_capability/bigville_runtime_partition_dynamic_links_lock_20260925.json"
ANALYSIS=ROOT/"evaluation/reports/substrate_bigville_runtime_partition_dynamic_links_analysis_20260925.json"
TOPICS=("trust_mayor","claim_credible","world_safe","self_worth","debtor_trustworthy")
THRESHOLD=0.5493061443340548
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def residual_count(cp):
    flat=[float(row[k]) for row in cp["states"] for k in TOPICS]
    fields=cp["fields"]
    assert len(flat)==len(fields)==500
    sums=[float(v[0])+float(v[1]) for v in fields]
    for src,dst,w in cp["weights_by_flat_index"]: sums[int(src)]+=float(w)*flat[int(dst)]
    return sum((1.0 if 1.5*h>THRESHOLD else -1.0 if 1.5*h < -THRESHOLD else 0.0)!=state for h,state in zip(sums,flat))
raw=json.loads(RAW.read_text()); lock=json.loads(LOCK_PATH.read_text())
assert raw["locked_inputs"]==lock["locked_inputs"] and sha(LOCK_PATH)==raw["lock_sha256"]
paths={"protocol_sha256":ROOT/"docs/research/engine_substrate/SUBSTRATE_BIGVILLE_RUNTIME_PARTITION_DYNAMIC_LINKS_PREREG_20260925.md",
"runner_sha256":ROOT/"scripts/substrate_bigville_runtime_partition_dynamic_links.py","base_runner_sha256":ROOT/"scripts/substrate_bigville_can_runtime_partition_replay_v3_1.py",
"cast_sha256":ROOT/"seeds/bigville_cast100.json","seed_sha256":ROOT/"seeds/can_native_reimplementation.json",
"builder_sha256":ROOT/"worlds/bigville_can_beliefs.py","rewrite_sha256":ROOT/"runners/dsl/src/rewrite.rs",
"substrate_sha256":ROOT/"runners/dsl/src/substrate.rs","py_binding_sha256":ROOT/"runners/dsl/src/py.rs"}
assert all(sha(path)==lock["locked_inputs"][key] for key,path in paths.items())
assert len(raw["runs"])==27 and len(raw["comparisons"])==9
assert len({x["native_extension_sha256"] for x in raw["runs"]})==1
assert all(x["initial_settled"] and x["runtime_component_count"]==100 and set(x["runtime_component_sizes"])=={5} for x in raw["runs"])
results=[]
for run in raw["runs"]:
    assert len(run["checkpoints"])==7
    for i,cp in enumerate(run["checkpoints"]):
        recomputed=residual_count(cp); assert recomputed==cp["residual_count"]
        assert cp["cross_frame_directed_edge_count"]==2*len(cp["active_cross_links"])
        expected_counts=(0,run["pair_count"]*2,run["pair_count"]*2,(run["pair_count"]-len(range(0,run["pair_count"],3)))*2,(run["pair_count"]-len(range(0,run["pair_count"],3)))*2,run["pair_count"]*2,0)
        assert cp["cross_frame_directed_edge_count"]==expected_counts[i]
        if run["policy"] in ("full","event"):
            assert cp["settlement"]["complete"] and recomputed==0
        if i==4 and cp["active_cross_links"]: assert {x[2] for x in cp["active_cross_links"]}=={0.35}
    if run["policy"]=="omit_evidence_notification":
        assert run["checkpoints"][2]["residual_count"]>0
results=[]
for topology in ("ring","star","random_connected"):
    pairs=[]; full_c=[]; event_c=[]; full_t=[]; event_t=[]; full_ms=[]; event_ms=[]; omitted=[]
    for rep in range(3):
        full=next(x for x in raw["runs"] if x["topology"]==topology and x["replicate"]==rep and x["policy"]=="full")
        event=next(x for x in raw["runs"] if x["topology"]==topology and x["replicate"]==rep and x["policy"]=="event")
        omit=next(x for x in raw["runs"] if x["topology"]==topology and x["replicate"]==rep and x["policy"]=="omit_evidence_notification")
        equal=[x["states"] for x in full["checkpoints"]]==[x["states"] for x in event["checkpoints"]]
        assert all(x["residual_count"]==0 for x in full["checkpoints"]+event["checkpoints"])
        assert omit["checkpoints"][2]["residual_count"]>0 and omit["checkpoints"][2]["states"]!=event["checkpoints"][2]["states"]
        pairs.append(equal)
        full_c.append(sum(x["settlement"]["audit"]["cand_enum"] for x in full["checkpoints"]))
        event_c.append(sum(x["settlement"]["audit"]["cand_enum"] for x in event["checkpoints"]))
        full_t.append(sum(x["settlement"]["audit"]["term_evals_total"] for x in full["checkpoints"]))
        event_t.append(sum(x["settlement"]["audit"]["term_evals_total"] for x in event["checkpoints"]))
        full_ms.append(sum(x["settlement_wall_ns"] for x in full["checkpoints"])/1e6)
        event_ms.append(sum(x["settlement_wall_ns"] for x in event["checkpoints"])/1e6)
        omitted.append(omit["checkpoints"][2]["residual_count"])
    results.append({"topology":topology,"replicates":3,"exact_state_pairs":sum(pairs),"full_candidates_median":int(statistics.median(full_c)),"event_candidates_median":int(statistics.median(event_c)),"full_terms_median":int(statistics.median(full_t)),"event_terms_median":int(statistics.median(event_t)),"full_settlement_ms_median":round(statistics.median(full_ms),3),"event_settlement_ms_median":round(statistics.median(event_ms),3),"omitted_notification_residuals":omitted})
checks={"workers_27":len(raw["runs"])==27,"runtime_partitions_verified":True,"all_full_event_residuals_zero":True,"all_state_residuals_independently_recomputed":True,"omission_control_sensitive":True,"all_three_replicates_each_topology":True}
assert all(checks.values())
analysis={"audit":"pass","checks":checks,"independent_residual_formula":"recomputed from stored frame states, external/identity fields, directed weights, and fixed threshold","topology_results":results}
ANALYSIS.write_text(json.dumps(analysis,indent=2,sort_keys=True)+"\n")
print(json.dumps(analysis,indent=2))
