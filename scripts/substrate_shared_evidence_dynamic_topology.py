#!/usr/bin/env python3
"""Random connected graph mutations with full/scoped native rule closure."""
from __future__ import annotations
import hashlib,json,os,random,resource,statistics,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_SHARED_EVIDENCE_DYNAMIC_TOPOLOGY_PREREG_20260925.md"
LOCK=ROOT/"evaluation/substrate_capability/shared_evidence_dynamic_topology_lock_20260925.json"
OUT=ROOT/"evaluation/reports/substrate_shared_evidence_dynamic_topology_20260925.json"
SIZES=(12,24,48); GRAPH_SEEDS=(20260925,20260926,20260927); REPS=3; ARMS=("full","scoped","scoped_omit_boundary0"); CAP=100_000
CHECKPOINTS=("initial","tree_insert_signal_1","cross_insert_signal_0_5","cross_retract_delete","cross_reinsert_signal_0_75","all_retract_delete")
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rule_set():
    attr=lambda n,k:{"type":"Attr","node":{"type":"Var","name":n},"key":k}
    lit=lambda v:{"type":"Lit","value":v}
    eq=lambda a,b:{"type":"Eq","a":a,"b":b}
    ne=lambda a,b:{"type":"Not","arg":eq(a,b)}
    match=[["e","supports","s"]]
    return [
      {"name":"dynamic_copy_active_evidence","match":match,"where":{"type":"And","items":[eq(attr("e","active"),lit(1.0)),ne(attr("s","derived"),attr("e","signal"))]},"effects":[["set_attr","s","derived",{"__term__":attr("e","signal")}]]},
      {"name":"dynamic_reset_retracted_evidence","match":match,"where":{"type":"And","items":[eq(attr("e","active"),lit(0.0)),ne(attr("s","derived"),lit(0.0))]},"effects":[["set_attr","s","derived",0.0]]},
    ]
def graph_edges(n,seed):
    rng=random.Random(seed*1009+n); tree=[]
    for child in range(1,n): tree.append((rng.randrange(child),child))
    all_edges=[(i,j) for i in range(n) for j in range(i+1,n) if (i,j) not in {tuple(sorted(e)) for e in tree}]
    rng.shuffle(all_edges)
    extras=all_edges[:n//4]
    return [(min(a,b),max(a,b)) for a,b in tree],[(min(a,b),max(a,b)) for a,b in extras]
def setup(n,seed):
    from substrate.world_adapter import WorldAdapter
    a=WorldAdapter(seeds=())
    for r in rule_set(): a.inner.add_rule(r)
    frames=[]; scopes=[]
    for i in range(n):
        f=a.s.add_node("DynamicBenchFrame",{"frame_index":i}); mt=a.inner.add_node("Microtheory",{"name":f"frame_{i}"})
        a.inner.add_edge_unchecked(mt,"has_concept",f,{}); frames.append(f); scopes.append(mt)
    tree,extras=graph_edges(n,seed); serial=[0]
    def add_boundary(edge,key,signal=0.0,active=0.0,with_support=False):
        left,right=edge; idx=serial[0]; serial[0]+=1
        ev=a.s.add_node("DynamicBenchEvidence",{"boundary_key":key,"active":float(active),"signal":float(signal),"left_frame":left,"right_frame":right})
        states=[]
        for owner,side in ((left,"left"),(right,"right")):
            state=a.s.add_node("DynamicBenchLocalState",{"boundary_key":key,"owner_frame":owner,"side":side,"derived":0.0})
            a.inner.add_edge_unchecked(frames[owner],"has_output",state); a.inner.add_edge_unchecked(state,"boundary_source",ev)
            a.inner.add_edge_unchecked(scopes[owner],"has_concept",state,{})
            states.append(state)
        for owner in (left,right): a.inner.add_edge_unchecked(scopes[owner],"has_concept",ev,{})
        item={"index":idx,"key":key,"edge":edge,"evidence":ev,"states":states,"active":float(active),"signal":float(signal),"supports":False}
        if with_support: insert_support(item)
        return item
    def insert_support(item):
        ev=item["evidence"]
        for s in item["states"]: a.inner.add_edge_unchecked(ev,"supports",s)
        item["supports"]=True
    def remove_boundary(item):
        ev=item["evidence"]; left,right=item["edge"]; removed=0; memberships=0
        for s in item["states"]:
            removed+=int(a.inner.remove_edge(ev,"supports",s))
            removed+=int(a.inner.remove_edge(s,"boundary_source",ev))
        for owner,s in zip((left,right),item["states"]):
            removed+=int(a.inner.remove_edge(frames[owner],"has_output",s))
            memberships+=int(a.inner.remove_edge(scopes[owner],"has_concept",s))
            memberships+=int(a.inner.remove_edge(scopes[owner],"has_concept",ev))
        item["supports"]=False
        return removed,memberships
    bounds=[add_boundary(e,f"tree_{i}") for i,e in enumerate(tree)]
    return a,frames,scopes,bounds,extras,add_boundary,insert_support,remove_boundary
def closure(a,scopes,arm,bounds):
    w0,c0=time.perf_counter_ns(),time.process_time_ns()
    if arm=="full":
        r=a.inner.run_rules_report(CAP,False); return r["status"],int(r["progress_steps"]),0,time.perf_counter_ns()-w0,time.process_time_ns()-c0
    omitted={bounds[0]["edge"][0],bounds[0]["edge"][1]} if arm=="scoped_omit_boundary0" and bounds else set()
    moved=turns=rounds=0; last=0
    while rounds<CAP:
        rounds+=1; last=0
        for i,mt in enumerate(scopes):
            if i in omitted: continue
            count=int(a.inner.run_rules_scoped(CAP-moved,False,mt)); moved+=count; turns+=1; last+=count
            if moved>=CAP: break
        if last==0 or moved>=CAP: break
    return ("scoped_no_progress" if last==0 and moved<CAP else "scoped_budget"),moved,turns,time.perf_counter_ns()-w0,time.process_time_ns()-c0
def project(a,bounds):
    rows=[]
    for b in bounds:
        for side,state in zip(("left","right"),b["states"]):
            rows.append({"boundary":b["key"],"side":side,"owner":b["edge"][0 if side=="left" else 1],"derived":float(a.s.node(state)["attrs"]["derived"])})
    return rows
def worker(n,seed,rep,arm):
    from substrate_rs import _native
    a,frames,scopes,bounds,extras,add_boundary,insert_support,remove_boundary=setup(n,seed)
    tree_count=len(bounds); removed_edges=extras[:max(1,len(extras)//2)]; remaining_extra=extras[len(removed_edges):]
    a.inner.scale_audit_set_enabled(True); reports=[]; mutation_total=0
    for cp,name in enumerate(CHECKPOINTS):
        m0=time.perf_counter_ns(); removed_memberships=added_memberships=boundary_edge_mutations=0
        if cp==1:
            for b in bounds:
                insert_support(b); boundary_edge_mutations+=2; a.s.set_attr(b["evidence"],"active",1.0); a.s.set_attr(b["evidence"],"signal",1.0); b["active"]=1.0; b["signal"]=1.0
        elif cp==2:
            for b in bounds:
                a.s.set_attr(b["evidence"],"signal",0.5); b["signal"]=0.5
            dynamic=[]
            for i,e in enumerate(extras):
                b=add_boundary(e,f"cross_{i}",0.5,1.0,True); dynamic.append(b); bounds.append(b); added_memberships+=4; boundary_edge_mutations+=2
        elif cp==3:
            for b in bounds:
                if b["key"].startswith("cross_") and int(b["key"].split("_")[1]) < len(removed_edges):
                    a.s.set_attr(b["evidence"],"active",0.0); b["active"]=0.0
        elif cp==4:
            for b in bounds:
                if b["active"]:
                    a.s.set_attr(b["evidence"],"signal",0.75); b["signal"]=0.75
            for i,e in enumerate(removed_edges):
                b=add_boundary(e,f"reinsert_{i}",0.75,1.0,True); bounds.append(b); added_memberships+=4; boundary_edge_mutations+=2
        elif cp==5:
            for b in bounds:
                if b["active"]: a.s.set_attr(b["evidence"],"active",0.0); b["active"]=0.0
        mutation_before_close=time.perf_counter_ns()-m0
        a.inner.scale_audit_reset(); status,progress,turns,wall,cpu=closure(a,scopes,arm,bounds)
        rows=project(a,bounds)
        wrong=[]
        for idx,(row,b) in enumerate(( (row,b) for b in bounds for row in [
            {"derived":float(a.s.node(b["states"][0])["attrs"]["derived"]),"boundary":b["key"],"side":"left"},
            {"derived":float(a.s.node(b["states"][1])["attrs"]["derived"]),"boundary":b["key"],"side":"right"}])):
            exp=(b["signal"] if b["active"] else 0.0)
            if row["derived"]!=exp: wrong.append(idx)
        audit=dict(a.inner.scale_audit_snapshot())
        removed=0
        if cp==3:
            gone=[b for b in bounds if b["key"].startswith("cross_") and int(b["key"].split("_")[1])<len(removed_edges)]
            for b in gone:
                edge_count,membership_count=remove_boundary(b); removed+=edge_count; removed_memberships+=membership_count; boundary_edge_mutations+=2; bounds.remove(b); b["active"]=0.0
        elif cp==5:
            gone=list(bounds)
            for b in gone:
                edge_count,membership_count=remove_boundary(b); removed+=edge_count; removed_memberships+=membership_count; boundary_edge_mutations+=2; bounds.remove(b)
        mutation_ns=time.perf_counter_ns()-m0
        mutation_total+=mutation_ns
        reports.append({"checkpoint":name,"settlement_status":status,"progress":progress,"frame_turns":turns,"wall_ns":wall,"cpu_ns":cpu,"mutation_ns":mutation_ns,"boundary_support_edge_mutations":boundary_edge_mutations,"added_scope_memberships":added_memberships,"removed_scope_memberships":removed_memberships,"removed_total_graph_edges":removed,"remaining_boundaries":len(bounds),"state_projection":rows,"wrong_state_indices":wrong,"scale_audit":audit})
    a.inner.scale_audit_set_enabled(False); native=Path(_native.__file__).resolve()
    return {"size":n,"graph_seed":seed,"replicate":rep,"arm":arm,"tree_edge_count":tree_count,"extra_edge_count":len(extras),"checkpoints":reports,"all_settled":all(x["settlement_status"] in ("fixed_point","scoped_no_progress") for x in reports),"native_extension_sha256":sha(native),"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"mutation_ns_total":mutation_total}
def main():
    if len(sys.argv)==6 and sys.argv[1]=="--worker":
        print(json.dumps(worker(int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),sys.argv[5]),sort_keys=True)); return
    locked={"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(__file__),"rewrite_sha256":sha(ROOT/"runners/dsl/src/rewrite.rs"),"substrate_sha256":sha(ROOT/"runners/dsl/src/substrate.rs"),"py_binding_sha256":sha(ROOT/"runners/dsl/src/py.rs")}
    if sys.argv[1:]==["--lock"]: print(json.dumps(locked,indent=2,sort_keys=True)); return
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked: raise SystemExit("missing lock or locked inputs changed")
    env=dict(os.environ); env["PYTHONPATH"]=f"{ROOT}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
    stale=subprocess.check_output([sys.executable,"-c","from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"],cwd=ROOT,env=env,text=True).strip()
    if stale: raise SystemExit("native build stale:\n"+stale)
    jobs=[(n,s,r,arm) for n in SIZES for s in GRAPH_SEEDS for r in range(REPS) for arm in ARMS]; random.Random(20260925).shuffle(jobs); runs=[]
    for n,s,r,arm in jobs:
        q=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(n),str(s),str(r),arm],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
        row=json.loads(q.stdout); runs.append(row); print(f"n={n} graph_seed={s} rep={r} arm={arm} settled={row['all_settled']}",flush=True)
    ix={(x["size"],x["graph_seed"],x["replicate"],x["arm"]):x for x in runs}; pairs=[]
    for n in SIZES:
      for seed in GRAPH_SEEDS:
       for r in range(REPS):
        f,s,o=(ix[n,seed,r,k] for k in ARMS)
        fcp,scp,ocp=(x["checkpoints"] for x in (f,s,o))
        parity=[x["state_projection"] for x in fcp]==[x["state_projection"] for x in scp]
        expected=all(not x["wrong_state_indices"] for x in fcp+scp)
        omission=ocp[1]["wrong_state_indices"]==[0,1] and ocp[2]["wrong_state_indices"]==[0,1] and ocp[4]["wrong_state_indices"]==[0,1] and not ocp[0]["wrong_state_indices"] and not ocp[3]["wrong_state_indices"] and not ocp[5]["wrong_state_indices"]
        pairs.append({"size":n,"graph_seed":seed,"replicate":r,"full_scoped_projection_equal":parity,"full_scoped_expected":expected,"omission_control_sensitive":omission,"full_candidates":sum(x["scale_audit"].get("cand_enum",0) for x in fcp),"scoped_candidates":sum(x["scale_audit"].get("cand_enum",0) for x in scp),"full_term_evaluations":sum(x["scale_audit"].get("term_evals_total",0) for x in fcp),"scoped_term_evaluations":sum(x["scale_audit"].get("term_evals_total",0) for x in scp),"full_closure_wall_ns":sum(x["wall_ns"] for x in fcp),"scoped_closure_wall_ns":sum(x["wall_ns"] for x in scp),"scoped_mutation_ns":sum(x["mutation_ns"] for x in scp)})
    checks={"worker_count_81":len(runs)==81,"all_arms_settled":all(x["all_settled"] for x in runs),"all_full_scoped_expected_and_equal":all(p["full_scoped_expected"] and p["full_scoped_projection_equal"] for p in pairs),"all_omission_controls_sensitive":all(p["omission_control_sensitive"] for p in pairs),"matrix_complete":len(pairs)==27}
    summaries=[]
    for n in SIZES:
      ps=[p for p in pairs if p["size"]==n]
      summaries.append({"size":n,"seed_replicate_pairs":len(ps),**{f"median_{k}":int(statistics.median(p[k] for p in ps)) for k in ("full_candidates","scoped_candidates","full_term_evaluations","scoped_term_evaluations","full_closure_wall_ns","scoped_closure_wall_ns","scoped_mutation_ns")}})
    payload={"schema_version":1,"run_id":"shared-evidence-dynamic-topology-20260925-v1","claim_boundary":"random connected sparse graphs at N≤48; benchmark-authored copy/retract rules; caller-maintained memberships and scope visitation","locked_inputs":locked,"lock_sha256":sha(LOCK),"checks":checks,"summaries":summaries,"paired":pairs,"runs":runs}
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n"); print(json.dumps({"output":str(OUT.relative_to(ROOT)),"checks":checks,"summaries":summaries},indent=2))
    if not all(checks.values()): raise SystemExit("dynamic topology gate failed; preserve raw report")
if __name__=="__main__": main()
