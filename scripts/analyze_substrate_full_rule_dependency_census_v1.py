#!/usr/bin/env python3
"""Derive dependency and cut summaries from the locked native access census."""
from __future__ import annotations
import hashlib,json,random,statistics,sys
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/substrate_full_rule_dependency_census_v1_20260925.json"
OUT=ROOT/"evaluation/reports/substrate_full_rule_dependency_census_v1_analysis_20260925.json"
LOCK=ROOT/"evaluation/substrate_capability/full_rule_dependency_census_lock_20260925.json"
BASE=ROOT/"evaluation/reports/substrate_seed_boot_prefix_scale_v1_20260925.json"
CORPUS=ROOT/"evaluation/substrate_capability/problem_shape_eventized_rule_order_seed_corpus_lock_v1_7_20260925.json"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def components(nodes,edges,strong=False):
    adj=[set() for _ in nodes]
    if strong:
        rev=[set() for _ in nodes]
        for u,v in edges:adj[u].add(v);rev[v].add(u)
        seen=set();order=[]
        def dfs(v):
            seen.add(v)
            for w in adj[v]:
                if w not in seen:dfs(w)
            order.append(v)
        for v in nodes:
            if v not in seen:dfs(v)
        seen.clear();out=[]
        def dfs2(v,c):
            seen.add(v);c.append(v)
            for w in rev[v]:
                if w not in seen:dfs2(w,c)
        for v in reversed(order):
            if v not in seen:
                c=[];dfs2(v,c);out.append(c)
        return out
    for u,v in edges:adj[u].add(v);adj[v].add(u)
    seen=set();out=[]
    for v in nodes:
        if v in seen:continue
        stack=[v];seen.add(v);c=[]
        while stack:
            x=stack.pop();c.append(x)
            for y in adj[x]:
                if y not in seen:seen.add(y);stack.append(y)
        out.append(c)
    return out
def cut_summary(n,edges,order,widths):
    pos={v:i for i,v in enumerate(order)};result={}
    for width in widths:
        block=lambda v:pos[v]//width
        crossing=[(u,v) for u,v in edges if block(u)!=block(v)]
        sizes=Counter(block(v) for v in order)
        boundary=set(x for e in crossing for x in e)
        result[str(width)]={"frame_count":len(sizes),"max_frame_rules":max(sizes.values(),default=0),
                            "crossing_dependencies":len(crossing),"crossing_fraction":len(crossing)/len(edges) if edges else 0.0,
                            "boundary_rule_count":len(boundary),"boundary_fraction":len(boundary)/n if n else 0.0}
    return result
def main():
    sys.setrecursionlimit(20000)
    raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());base=json.loads(BASE.read_text());corpus=json.loads(CORPUS.read_text());errors=[]
    if not raw.get("all_gates_pass"):errors.append("runner gates failed")
    if raw.get("lock")!=lock:errors.append("raw lock mismatch")
    if raw.get("source_hashes_after")!=lock.get("sources"):errors.append("source hashes changed")
    post_measurement_source_drift=[p for p,h in lock["sources"].items() if sha(ROOT/p)!=h]
    if sha(ROOT/"docs/research/engine_substrate/SUBSTRATE_FULL_RULE_DEPENDENCY_CENSUS_PREREG_20260925.md")!=lock["protocol_sha256"]:errors.append("protocol hash mismatch")
    if sha(ROOT/"scripts/substrate_full_rule_dependency_census_v1.py")!=lock["runner_sha256"]:errors.append("runner hash mismatch")
    if sha(BASE)!=lock["baseline_raw_sha256"]:errors.append("frozen baseline changed")
    if corpus["corpus_digest"]!=lock["corpus_digest"]:errors.append("corpus lock digest mismatch")
    for item in corpus["manifests"]:
        if sha(Path(base["snapshot"]["full_seed_dir"])/item["path"])!=item["sha256"]:errors.append(f"frozen file changed: {item['path']}");break
    workers=[x["worker"] for x in raw["workers"]]
    if len(workers)!=2 or workers[0]["access_rows"]!=workers[1]["access_rows"]:errors.append("native access rows differ across workers")
    rows=workers[0]["access_rows"] if workers else []
    if len(rows)!=workers[0].get("slot_count",-1) or len(rows)!=workers[0].get("active_count",-2):errors.append("access rows/active count mismatch")
    n=len(rows);active=[r for r in rows if r["active"]];names=[r["name"] for r in active]
    snapshot=Path(base["snapshot"]["full_seed_dir"]);seed_files={}
    for p in sorted(snapshot.glob("*.json"))+sorted((snapshot/"generated").glob("*.json")):
        try:d=json.loads(p.read_text())
        except Exception:continue
        if isinstance(d,dict):seed_files[d.get("id") or p.stem]=d
    seed_order=base["snapshot"]["subsets"]["737"]["order"]
    candidates=[]
    for sid in seed_order:
        d=seed_files.get(sid,{})
        area=d.get("area")
        if not isinstance(area,str):
            mt=d.get("microtheory");area=mt.get("category") if isinstance(mt,dict) else (mt if isinstance(mt,str) else None)
        for rule in d.get("rules",[]) or []:
            if isinstance(rule,dict) and rule.get("active",True) and isinstance(rule.get("match"),list) and rule.get("name"):
                candidates.append((str(rule["name"]),sid,area))
    # Align active native slots to manifest-declared candidates in load order, allowing
    # native-skipped/missing candidates while preserving duplicate-name ordering.
    attribution={};cursor=0
    for row in active:
        while cursor<len(candidates) and candidates[cursor][0]!=row["name"]:cursor+=1
        if cursor==len(candidates):break
        _,sid,area=candidates[cursor];attribution[row["index"]]={"seed_id":sid,"area":area};cursor+=1
    attribution_rate=len(attribution)/len(active) if active else 0
    # Active-slot compact IDs keep component algorithms independent of inactive slots.
    slot_to_local={r["index"]:i for i,r in enumerate(active)};local_rows=active;N=len(active)
    readers=defaultdict(set);writers=defaultdict(set)
    for i,r in enumerate(local_rows):
        for key in set(r["reads"]+r["term_edge_reads"]):readers[key].add(i)
        for key in set(r["writes"]):writers[key].add(i)
    exact=set()
    for key,ws in writers.items():
        for u in ws:
            for v in readers.get(key,()):exact.add((u,v))
    resource_pair_load=[]
    for key,ws in writers.items():
        rs=readers.get(key,())
        if rs:
            pairs={(u,v) for u in ws for v in rs}
            resource_pair_load.append({"resource":key,"writer_count":len(ws),"reader_count":len(rs),"directed_pair_product":len(ws)*len(rs),"unique_directed_edges":len(pairs)})
    resource_pair_load.sort(key=lambda x:(x["directed_pair_product"],x["writer_count"],x["reader_count"]),reverse=True)
    complete=set(exact)
    any_writers=[i for i,r in enumerate(local_rows) if r["writes_any"]]
    any_readers=[i for i,r in enumerate(local_rows) if r["reads_any"]]
    all_ids=set(range(N))
    for u in any_writers:
        for v in all_ids:complete.add((u,v))
    for v in any_readers:
        for u in all_ids:complete.add((u,v))
    def graph_stats(edges):
        outdeg=Counter();indeg=Counter()
        for u,v in edges:outdeg[u]+=1;indeg[v]+=1
        weak=components(range(N),edges);strong=components(range(N),edges,True)
        def dist(vals):
            xs=sorted(vals);return {"min":xs[0] if xs else 0,"median":statistics.median(xs) if xs else 0,"p90":xs[min(len(xs)-1,int(.9*(len(xs)-1)))] if xs else 0,"max":xs[-1] if xs else 0}
        return {"directed_edges":len(edges),"self_edges":sum(u==v for u,v in edges),"weak_component_count":len(weak),"weak_component_sizes":sorted((len(c) for c in weak),reverse=True)[:50],"scc_count":len(strong),"scc_sizes":sorted((len(c) for c in strong),reverse=True)[:50],"out_degree":dist(outdeg.get(i,0) for i in range(N)),"in_degree":dist(indeg.get(i,0) for i in range(N))}
    widths=lock["frame_widths"];shuffles=lock["shuffle_seeds"]
    structure={}
    for label,edges in (("resource_intersection",exact),("wildcard_completed",complete)):
        metas={"unattributed":0,"attributed":len(attribution)}
        same_seed=same_area=cross_area=unknown_area=cross_seed=attributed_edges=0
        for u,v in edges:
            mu=attribution.get(local_rows[u]["index"]);mv=attribution.get(local_rows[v]["index"])
            if not mu or not mv:continue
            attributed_edges+=1
            if mu["seed_id"]==mv["seed_id"]:same_seed+=1
            else:cross_seed+=1
            if mu["area"] is None or mv["area"] is None:unknown_area+=1
            elif mu["area"]==mv["area"]:same_area+=1
            else:cross_area+=1
        order=list(range(N));canonical=cut_summary(N,edges,order,widths)
        shuffled={str(w):[] for w in widths}
        for seed in shuffles:
            perm=list(range(N));random.Random(seed).shuffle(perm)
            one=cut_summary(N,edges,perm,widths)
            for w in widths:shuffled[str(w)].append(one[str(w)])
        structure[label]={**graph_stats(edges),"ruleidx_block_cuts":canonical,
                          "shuffled_cut_medians":{w:{k:statistics.median(x[k] for x in vals) for k in vals[0]} for w,vals in shuffled.items()},
                          "cross_seed_dependency_count":cross_seed,"within_seed_dependency_count":same_seed,"unattributed_dependency_count":len(edges)-attributed_edges,
                          "same_area_dependency_count":same_area,"cross_area_dependency_count":cross_area,"unknown_area_edge_count":unknown_area}
    result={"schema_version":1,"analysis_id":"full-rule-dependency-census-v1-analysis-20260925","raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"all_checks_pass":not errors,"validation_errors":errors,
            "workload":{"seed_ids":737,"physical_manifests":833,"rule_slots":len(rows),"active_rules":N,"inactive_rules":len(rows)-N,"source_attribution_rate":attribution_rate,"attributed_unique_seeds":len({x["seed_id"] for x in attribution.values()}),"attributed_area_count":len({x["area"] for x in attribution.values() if x["area"] is not None})},
            "current_tree_source_drift_since_measurement":post_measurement_source_drift,
            "resource_summary":{"distinct_read_keys":len(readers),"distinct_write_keys":len(writers),"read_resource_occurrences":sum(len(r["reads"])+len(r["term_edge_reads"]) for r in local_rows),"write_resource_occurrences":sum(len(r["writes"]) for r in local_rows),"reads_any_rules":len(any_readers),"writes_any_rules":len(any_writers)},
            "highest_resource_pair_load":resource_pair_load[:30],"wildcard_rules":{"reads_any":[r["name"] for r in local_rows if r["reads_any"]],"writes_any":[r["name"] for r in local_rows if r["writes_any"]]},
            "projections":structure,"claim_limit":"static native declared access graph over the full loaded authored rule library; no dynamic access traces, actual task-frame hierarchy, or semantic partition execution are measured."}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":result["all_checks_pass"],"validation_errors":errors,"analysis":str(OUT)}));return 0 if not errors else 2
if __name__=="__main__":raise SystemExit(main())
