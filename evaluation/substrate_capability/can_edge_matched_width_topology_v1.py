#!/usr/bin/env python3
"""Compare grid and edge-matched sparse partial q-trees at known width q."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import random
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
PROTOCOL=ROOT/"docs/research/engine_substrate/CAN_EDGE_MATCHED_WIDTH_TOPOLOGY_V1_PREREG_20260929.md"
RUNNER=Path(__file__).resolve()
LOCK=ROOT/"evaluation/substrate_capability/can_edge_matched_width_topology_v1_lock_20260929.json"
OUT=ROOT/"evaluation/reports/can_edge_matched_width_topology_v1_20260929.json"
WIDTHS=(4,5,6); N=120; REPLICATES=12
FAMILIES=("grid","sparse_partial_qtree")
SOURCE="domains/graph_treewidth.py"

def digest(path):
    raw=path.read_bytes()
    return {"path":path.relative_to(ROOT).as_posix(),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}

def input_lock():
    return {"schema_version":1,"protocol":digest(PROTOCOL),"runner":digest(RUNNER),
        "source":digest(ROOT/SOURCE),"widths":list(WIDTHS),"node_count":N,
        "replicates":REPLICATES,"families":list(FAMILIES),
        "git_head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}

def grid(q):
    m=N//q; edges=set()
    for c in range(m):
        for r in range(q):
            v=c*q+r
            if r+1<q: edges.add(tuple(sorted((v,v+1))))
            if c+1<m: edges.add(tuple(sorted((v,v+q))))
    return edges,list(range(N))

def sparse_partial_qtree(q,rng,target_edges):
    core=q+1
    edges={tuple((i,j)) for i in range(core) for j in range(i+1,core)}
    bags=[frozenset(range(core))]
    attach_count=N-core
    target_attach=target_edges-len(edges)
    sizes=[1]*attach_count
    extra=target_attach-attach_count
    if extra<0 or extra>attach_count*(q-1): raise AssertionError("target edge count infeasible")
    while extra:
        order=list(range(attach_count)); rng.shuffle(order)
        for i in order:
            if extra==0: break
            if sizes[i]<q:
                sizes[i]+=1; extra-=1
    for v in range(core,N):
        clique=frozenset(rng.sample(sorted(rng.choice(bags)),q))
        parents=rng.sample(sorted(clique),sizes[v-core])
        for u in parents: edges.add(tuple(sorted((u,v))))
        bags.append(frozenset((*clique,v)))
    if len(edges)!=target_edges: raise AssertionError("edge matching failed")
    return edges,list(reversed(range(N)))

def mcs_chordal(nodes,edges):
    adj={v:set() for v in nodes}
    for a,b in edges: adj[a].add(b); adj[b].add(a)
    weight={v:0 for v in nodes}; unselected=set(nodes); order=[]
    while unselected:
        v=min(unselected,key=lambda x:(-weight[x],repr(x)))
        unselected.remove(v); order.append(v)
        for u in adj[v]&unselected: weight[u]+=1
    rank={v:len(nodes)-i for i,v in enumerate(order)}
    for v in nodes:
        earlier=[u for u in adj[v] if rank[u]>rank[v]]
        if len(earlier)>1:
            parent=min(earlier,key=lambda u:rank[u])
            if any(u!=parent and parent not in adj[u] for u in earlier): return False
    return True

def one(q,family,rep):
    from domains.graph_treewidth import build_elimination_triangulation,min_fill_upper_bound,treewidth_bound_check
    seed=20260929+q*1000003+(FAMILIES.index(family))*10007+rep*65537
    rng=random.Random(seed)
    grid_edges,grid_order=grid(q)
    if family=="grid": edges,cert_order=grid_edges,grid_order
    else: edges,cert_order=sparse_partial_qtree(q,rng,len(grid_edges))
    labels=list(range(N)); rng.shuffle(labels); remap={u:labels[u] for u in range(N)}
    edges=[tuple(sorted((remap[a],remap[b]))) for a,b in edges]; rng.shuffle(edges)
    nodes=list(range(N)); rng.shuffle(nodes)
    cert_order=[remap[v] for v in cert_order]
    certificate=build_elimination_triangulation(nodes,edges,cert_order)
    cert_width=max((len(b)-1 for b in certificate["bags"].values()),default=0)
    start=time.perf_counter_ns(); mf=min_fill_upper_bound(nodes,edges); order_ns=time.perf_counter_ns()-start
    bags=build_elimination_triangulation(nodes,edges,mf["elimination_order"])["bags"]
    start=time.perf_counter_ns(); gate=treewidth_bound_check(nodes,edges,q,max_exact_n=10); gate_ns=time.perf_counter_ns()-start
    degree=Counter()
    for a,b in edges: degree[a]+=1; degree[b]+=1
    return {"width":q,"family":family,"replicate":rep,"seed":seed,"nodes":len(nodes),
        "edges":len(edges),"paired_grid_edges":len(grid_edges),"certificate_width":cert_width,
        "clique_lower_bound":q if family=="sparse_partial_qtree" else None,
        "minfill_width":mf["treewidth"],"bag_size_histogram":dict(sorted(Counter(len(b) for b in bags.values()).items())),
        "degree_min":min(degree.values()),"degree_median":sorted(degree.values())[len(degree)//2],
        "degree_max":max(degree.values()),"chordal_by_mcs":mcs_chordal(nodes,edges),
        "gate_width":gate["treewidth"],"gate_accept_bound_q":gate["within_bound"],
        "ordering_ns":order_ns,"gate_ns":gate_ns}

def main():
    if len(sys.argv)==5 and sys.argv[1]=="--worker":
        print(json.dumps(one(int(sys.argv[2]),sys.argv[3],int(sys.argv[4])),sort_keys=True)); return
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if sys.argv[1:]==["--lock"]:
        if LOCK.exists() or OUT.exists(): raise SystemExit("refusing to overwrite lock/capture")
        LOCK.write_text(json.dumps(input_lock(),indent=2,sort_keys=True)+"\n"); print(LOCK.relative_to(ROOT)); return
    lock=json.loads(LOCK.read_text())
    if input_lock()!=lock: raise SystemExit("source/fixture lock drift")
    rows=[]
    for q in WIDTHS:
        for rep in range(REPLICATES):
            for family in FAMILIES:
                p=subprocess.run([sys.executable,str(RUNNER),"--worker",str(q),family,str(rep)],cwd=ROOT,
                    env={**os.environ,"PYTHONPATH":f"{ROOT}:{os.environ.get('PYTHONPATH','')}"},
                    text=True,capture_output=True,check=True)
                row=json.loads(p.stdout.strip()); rows.append(row)
                print(f"q={q} rep={rep} family={family} edges={row['edges']} minfill={row['minfill_width']} "
                      f"chordal={row['chordal_by_mcs']}",flush=True)
    post=input_lock()
    checks={"complete_workers":len(rows)==72,
      "coverage":all(sum(r["width"]==q and r["family"]==f for r in rows)==REPLICATES for q in WIDTHS for f in FAMILIES),
      "paired_node_and_edge_counts":all(r["nodes"]==N and r["edges"]==r["paired_grid_edges"] for r in rows),
      "width_certificates":all(r["certificate_width"]==r["width"] for r in rows),
      "minfill_no_underestimate":all(r["minfill_width"]>=r["width"] for r in rows),
      "gate_matches_estimate":all(r["gate_width"]==r["minfill_width"] and r["gate_accept_bound_q"]==(r["minfill_width"]<=r["width"]) for r in rows),
      "pre_post_lock_match":lock==post}
    payload={"schema_version":1,"run_id":"can-edge-matched-width-topology-v1-20260929","status":"complete",
      "input_lock":lock,"post_run_input_lock":post,"configuration":{"widths":WIDTHS,"nodes":N,"replicates":REPLICATES},
      "claim_boundary":"paired synthetic grids and sparse partial q-trees only; no natural task estimate",
      "environment":{"python":platform.python_version(),"platform":platform.platform()},"checks":checks,"runs":rows}
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"output":OUT.relative_to(ROOT).as_posix(),"checks":checks},indent=2))
    if not all(checks.values()): raise SystemExit("edge-matched topology integrity failure")

if __name__=="__main__": main()
