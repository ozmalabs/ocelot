#!/usr/bin/env python3
"""Dynamic cross-frame link replay on runtime-derived Bigville partitions."""
from __future__ import annotations
import hashlib,importlib.util,json,os,platform,random,resource,statistics,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_BIGVILLE_RUNTIME_PARTITION_DYNAMIC_LINKS_PREREG_20260925.md"
LOCK=ROOT/"evaluation/substrate_capability/bigville_runtime_partition_dynamic_links_lock_20260925.json"
OUT=ROOT/"evaluation/reports/substrate_bigville_runtime_partition_dynamic_links_20260925.json"
BASE=ROOT/"scripts/substrate_bigville_can_runtime_partition_replay_v3_1.py"
CAST=ROOT/"seeds/bigville_cast100.json"; SEED=ROOT/"seeds/can_native_reimplementation.json"
BUILDER=ROOT/"worlds/bigville_can_beliefs.py"
TOPOLOGIES=("ring","star","random_connected"); POLICIES=("full","event","omit_evidence_notification")
REPS=3; CAP=100_000; TARGETS=tuple(range(0,100,10))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_base():
    spec=importlib.util.spec_from_file_location("bigville_dynamic_base",BASE)
    if spec is None or spec.loader is None: raise RuntimeError("cannot load v3.1 runtime partition implementation")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
def topology_pairs(topology,rep,count=100):
    if topology=="ring": return [(i,(i+1)%count) for i in range(count)]
    if topology=="star": return [(0,i) for i in range(1,count)]
    rng=random.Random(20260925+rep*1009); pairs=[]
    for child in range(1,count): pairs.append((rng.randrange(child),child))
    have={tuple(sorted(x)) for x in pairs}; candidates=[(i,j) for i in range(count) for j in range(i+1,count) if (i,j) not in have]
    rng.shuffle(candidates); pairs.extend(candidates[:count-len(pairs)])
    return pairs
def worker(topology,rep,policy):
    import substrate_rs as sr
    from substrate_rs import _native
    from domains.engine_provenance import engine_provenance
    from worlds import bigville_can_beliefs as bigville
    base=load_base(); cast=json.loads(CAST.read_text())["residents"]; seed_doc=json.loads(SEED.read_text())
    (outer,inner,residents,mts,concepts,frame_nodes,node_frame,edges,cross,ref_by_id,node_flat)=base.build(sr,cast,seed_doc,bigville)
    if len(frame_nodes)!=100 or set(map(len,frame_nodes))!={5} or cross:
        raise RuntimeError("runtime partition precondition failed before benchmark links")
    weights=base.weights_by_id(concepts,residents,bigville,node_flat)
    all_pairs=topology_pairs(topology,rep); removed_pairs=all_pairs[::3]
    active={}; checkpoints=[]; mutated_evidence=False
    def add_pair(pair,weight):
        left,right=pair; ar=concepts[left]["world_safe"]; br=concepts[right]["world_safe"]
        aid,bid=base.nid(ar),base.nid(br)
        inner.add_edge_unchecked(ar,"causal_influence",br,{"weight":weight}); inner.add_edge_unchecked(br,"causal_influence",ar,{"weight":weight})
        edges.extend(((aid,bid),(bid,aid))); cross.extend(((aid,bid),(bid,aid)))
        weights.extend(((node_flat[aid],node_flat[bid],weight),(node_flat[bid],node_flat[aid],weight)))
        active[pair]={"left_id":aid,"right_id":bid,"left_flat":node_flat[aid],"right_flat":node_flat[bid],"weight":weight}
    def remove_pair(pair):
        rec=active.pop(pair); ar=ref_by_id[rec["left_id"]]; br=ref_by_id[rec["right_id"]]
        inner.remove_edge(ar,"causal_influence",br); inner.remove_edge(br,"causal_influence",ar)
        edges.remove((rec["left_id"],rec["right_id"])); edges.remove((rec["right_id"],rec["left_id"]))
        cross.remove((rec["left_id"],rec["right_id"])); cross.remove((rec["right_id"],rec["left_id"]))
        wanted={(rec["left_flat"],rec["right_flat"]),(rec["right_flat"],rec["left_flat"])}
        weights[:]=[x for x in weights if (x[0],x[1]) not in wanted]
    def residual_projection():
        state_rows=base.states(inner,concepts); field_rows=base.fields(inner,concepts)
        residual=base.residuals(state_rows,field_rows,weights)
        return state_rows,field_rows,residual
    def settle(stage,seed_frames,mutation_ns):
        start=time.perf_counter_ns()
        if policy=="full": record=base.settle_full(inner,mts,audit=True)
        else: record=base.settle_event(inner,mts,frame_nodes,node_frame,edges,ref_by_id,seed_frames,audit=True)
        elapsed=time.perf_counter_ns()-start
        states,field_rows,residual=residual_projection()
        checkpoints.append({"stage":stage,"states":states,"fields":field_rows,"weights_by_flat_index":[list(x) for x in weights],"active_cross_links":[[a,b,v["weight"]] for (a,b),v in sorted(active.items())],"cross_frame_directed_edge_count":len(cross),"residual_count":sum(residual),"settlement":record,"settlement_wall_ns":elapsed,"mutation_ns":mutation_ns,"seed_frames":sorted(seed_frames)})
    # Baseline closure on the original runtime-derived independent partitions.
    initial=base.settle_full(inner,mts)
    initial_states=base.states(inner,concepts)
    settle("runtime_partition_baseline",set(),0)
    # Add the connected graph after component derivation. Notify changed endpoints.
    t0=time.perf_counter_ns()
    for pair in all_pairs: add_pair(pair,0.2)
    affected={v for e in all_pairs for v in e}; mutation_ns=time.perf_counter_ns()-t0
    settle("insert_cross_links",set() if policy=="omit_evidence_notification" else affected,mutation_ns)
    # Authored scenario evidence is applied once; omission arm intentionally misses this notification.
    t0=time.perf_counter_ns()
    for target in TARGETS: base.mutate(inner,concepts,residents,bigville,target)
    mutation_ns=time.perf_counter_ns()-t0
    seeds=set() if policy=="omit_evidence_notification" else set(TARGETS)
    settle("authored_evidence_update",seeds,mutation_ns)
    # Delete one third of injected boundaries after updating both endpoint frames.
    t0=time.perf_counter_ns()
    for pair in removed_pairs: remove_pair(pair)
    affected={v for e in removed_pairs for v in e}; mutation_ns=time.perf_counter_ns()-t0
    settle("delete_one_third",affected,mutation_ns)
    # Replace remaining edge weights by remove/insert; notify every endpoint.
    t0=time.perf_counter_ns(); to_replace=list(active)
    for pair in to_replace: remove_pair(pair); add_pair(pair,0.35)
    affected={v for e in to_replace for v in e}; mutation_ns=time.perf_counter_ns()-t0
    settle("reweight_remaining",affected,mutation_ns)
    # Reinsert deleted endpoint pairs with new weight.
    t0=time.perf_counter_ns()
    for pair in removed_pairs: add_pair(pair,0.35)
    affected={v for e in removed_pairs for v in e}; mutation_ns=time.perf_counter_ns()-t0
    settle("reinsert_deleted_pairs",affected,mutation_ns)
    # Remove all links and notify all affected endpoints.
    t0=time.perf_counter_ns()
    for pair in list(active): remove_pair(pair)
    affected={v for e in all_pairs for v in e}; mutation_ns=time.perf_counter_ns()-t0
    settle("remove_all_cross_links",affected,mutation_ns)
    native=Path(_native.__file__).resolve()
    return {"topology":topology,"replicate":rep,"policy":policy,"pair_count":len(all_pairs),"removed_pair_count":len(removed_pairs),"runtime_component_count":len(frame_nodes),"runtime_component_sizes":[len(x) for x in frame_nodes],"runtime_node_frame":node_frame,"initial_settled":initial["complete"],"initial_states":initial_states,"checkpoints":checkpoints,"native_extension_sha256":sha(native),"engine_provenance":engine_provenance(),"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
def main():
    if len(sys.argv)==5 and sys.argv[1]=="--worker": print(json.dumps(worker(sys.argv[2],int(sys.argv[3]),sys.argv[4]),sort_keys=True)); return
    locked={"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),"base_runner_sha256":sha(BASE),"cast_sha256":sha(CAST),"seed_sha256":sha(SEED),"builder_sha256":sha(BUILDER),"rewrite_sha256":sha(ROOT/"runners/dsl/src/rewrite.rs"),"substrate_sha256":sha(ROOT/"runners/dsl/src/substrate.rs"),"py_binding_sha256":sha(ROOT/"runners/dsl/src/py.rs")}
    if sys.argv[1:]==["--lock"]: print(json.dumps(locked,indent=2,sort_keys=True)); return
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked: raise SystemExit("missing lock or locked inputs changed")
    env=dict(os.environ); env["PYTHONPATH"]=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
    stale=subprocess.check_output([sys.executable,"-c","from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"],cwd=ROOT,env=env,text=True).strip()
    if stale: raise SystemExit("native build stale:\n"+stale)
    jobs=[(t,r,p) for t in TOPOLOGIES for r in range(REPS) for p in POLICIES]; random.Random(20260925).shuffle(jobs); runs=[]
    for t,r,p in jobs:
        proc=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",t,str(r),p],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
        row=json.loads(proc.stdout); runs.append(row); print(f"{t} rep={r} policy={p} checkpoints={len(row['checkpoints'])}",flush=True)
    ix={(x["topology"],x["replicate"],x["policy"]):x for x in runs}; pairs=[]
    for t in TOPOLOGIES:
      for r in range(REPS):
        full,event,omit=(ix[t,r,p] for p in POLICIES)
        cp_full,cp_event,cp_omit=(x["checkpoints"] for x in (full,event,omit))
        pairs.append({"topology":t,"replicate":r,"event_all_residuals_zero":all(x["residual_count"]==0 for x in cp_event),"full_all_residuals_zero":all(x["residual_count"]==0 for x in cp_full),"event_full_state_equal":[x["states"] for x in cp_full]==[x["states"] for x in cp_event],"omission_detected_after_evidence":cp_omit[2]["residual_count"]>0 and cp_omit[2]["states"]!=cp_event[2]["states"],"full_turns":[x["settlement"]["turns"] for x in cp_full],"event_turns":[x["settlement"]["turns"] for x in cp_event],"full_candidates":sum(x["settlement"]["audit"]["cand_enum"] for x in cp_full),"event_candidates":sum(x["settlement"]["audit"]["cand_enum"] for x in cp_event),"full_terms":sum(x["settlement"]["audit"]["term_evals_total"] for x in cp_full),"event_terms":sum(x["settlement"]["audit"]["term_evals_total"] for x in cp_event)})
    checks={"worker_count_27":len(runs)==27,"runtime_derived_100_five_concept_frames":all(x["runtime_component_count"]==100 and set(x["runtime_component_sizes"])=={5} for x in runs),"full_event_residuals_zero":all(p["full_all_residuals_zero"] and p["event_all_residuals_zero"] for p in pairs),"omitted_evidence_notification_detected":all(p["omission_detected_after_evidence"] for p in pairs),"matrix_complete":len(pairs)==9}
    summaries=[]
    for t in TOPOLOGIES:
        ps=[p for p in pairs if p["topology"]==t]
        summaries.append({"topology":t,"replicates":len(ps),"all_checkpoints_event_full_equal":all(p["event_full_state_equal"] for p in ps),"median_full_candidates":int(statistics.median(p["full_candidates"] for p in ps)),"median_event_candidates":int(statistics.median(p["event_candidates"] for p in ps)),"median_full_terms":int(statistics.median(p["full_terms"] for p in ps)),"median_event_terms":int(statistics.median(p["event_terms"] for p in ps))})
    payload={"schema_version":1,"run_id":"bigville-runtime-partition-dynamic-links-20260925-v1","claim_boundary":"runtime-derived Bigville resident partitions; caller-notified Python dependency queue; injected dynamic cross-frame links; not native notifications","locked_inputs":locked,"lock_sha256":sha(LOCK),"checks":checks,"summaries":summaries,"comparisons":pairs,"runs":runs}
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n"); print(json.dumps({"output":str(OUT.relative_to(ROOT)),"checks":checks,"summaries":summaries},indent=2))
    if not all(checks.values()): raise SystemExit("dynamic Bigville semantic gate failed; preserve raw report")
if __name__=="__main__": main()
