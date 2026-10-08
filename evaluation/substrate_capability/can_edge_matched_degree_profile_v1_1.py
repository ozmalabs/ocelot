#!/usr/bin/env python3
"""Matched exact-inference study isolating hub degree concentration."""
from __future__ import annotations
import hashlib, importlib.util, json, math, os, platform, random, statistics, subprocess, sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
PROTOCOL=ROOT/"docs/research/engine_substrate/CAN_EDGE_MATCHED_DEGREE_PROFILE_V1_PREREG_20260929.md"
RUNNER=Path(__file__).resolve()
BASE_PATH=ROOT/"evaluation/substrate_capability/can_edge_matched_inference_cost_v1.py"
LOCK=ROOT/"evaluation/substrate_capability/can_edge_matched_degree_profile_v1_1_lock_20260929.json"
OUT=ROOT/"evaluation/reports/can_edge_matched_degree_profile_v1_1_20260929.json"
WIDTHS=(4,5,6); N=120; REPLICATES=6
FAMILIES=("grid","sparse_partial_qtree","hub_partial_qtree")

def digest(path):
    raw=path.read_bytes()
    return {"path":path.relative_to(ROOT).as_posix(),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}

def hub_partial_qtree(q,rng,target_edges):
    """Width-q construction with surplus edges concentrated on a fixed core."""
    del rng
    core=q+1
    edges={(i,j) for i in range(core) for j in range(i+1,core)}
    count=N-core
    extras=target_edges-len(edges)-count
    if extras<0 or extras>count*(q-1):
        raise ValueError("target edge count cannot be realized by the hub construction")
    sizes=[1]*count
    for i in range(count):
        add=min(q-1,extras)
        sizes[i]+=add
        extras-=add
    if extras: raise AssertionError("edge allocation incomplete")
    for i,v in enumerate(range(core,N)):
        # Every new neighborhood is a subset of the initial core clique.
        parents=list(range(sizes[i]))
        edges.update(tuple(sorted((u,v))) for u in parents)
    return edges,list(reversed(range(N)))

def load_base():
    spec=importlib.util.spec_from_file_location("edge_cost_base",BASE_PATH)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    mod.FAMILIES=FAMILIES
    original_fixture=mod.fixture
    def fixture(q,family,rep):
        if family!="hub_partial_qtree":
            return original_fixture(q,family,rep)
        seed=20260929+q*1000003+FAMILIES.index(family)*10007+rep*65537
        rng=random.Random(seed)
        grid_edges,grid_order=mod.GEN.grid(q)
        edges,cert=hub_partial_qtree(q,rng,len(grid_edges))
        labels=list(range(N)); rng.shuffle(labels); remap={u:labels[u] for u in range(N)}
        edges=[tuple(sorted((remap[a],remap[b]))) for a,b in edges]; rng.shuffle(edges)
        nodes=list(range(N)); rng.shuffle(nodes); cert=[remap[v] for v in cert]
        prng=random.Random(0xC0FFEE+q*100003+rep*503)
        unary={i:prng.randint(-8,8)/4.0 for i in range(N)}
        pair={edge:prng.randint(-8,8)/4.0 for edge in sorted(edges)}
        return seed,nodes,edges,cert,unary,pair,len(grid_edges)
    mod.fixture=fixture
    return mod

def degree_metrics(edges):
    deg=Counter()
    for a,b in edges: deg[a]+=1; deg[b]+=1
    values=sorted(deg.get(i,0) for i in range(N))
    total=sum(values)
    gini=(2*sum((i+1)*x for i,x in enumerate(values))/(N*total)-(N+1)/N) if total else 0.0
    return {"degree_min":values[0],"degree_median":values[N//2],"degree_p90":values[math.ceil(.9*N)-1],
            "degree_max":values[-1],"degree_gini":gini}

def input_lock():
    return {"schema_version":1,"protocol":digest(PROTOCOL),"runner":digest(RUNNER),
            "base_inference_runner":digest(BASE_PATH),
            "amendment":digest(ROOT/"docs/research/engine_substrate/CAN_EDGE_MATCHED_DEGREE_PROFILE_V1_1_AMENDMENT_20260929.md"),
            "sources":[digest(ROOT/p) for p in ("domains/can_junction_tree.py","domains/graph_treewidth.py",
                "runners/dsl/python/substrate_rs/_native.abi3.so","runners/dsl/python/substrate_rs/_native.build.json")],
            "widths":list(WIDTHS),"nodes":N,"replicates":REPLICATES,"families":list(FAMILIES),
            "git_head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}

def worker(q,family,rep):
    base=load_base()
    row=base.worker(q,family,rep)
    _,nodes,edges,_,_,_,_=base.fixture(q,family,rep)
    row.update(degree_metrics(edges))
    return row

def main():
    if len(sys.argv)==5 and sys.argv[1]=="--worker":
        print(json.dumps(worker(int(sys.argv[2]),sys.argv[3],int(sys.argv[4])),sort_keys=True)); return
    if sys.argv[1:]==["--lock"]:
        if LOCK.exists() or OUT.exists(): raise SystemExit("refusing to overwrite lock/capture")
        LOCK.write_text(json.dumps(input_lock(),indent=2,sort_keys=True)+"\n")
        print(LOCK.relative_to(ROOT)); return
    lock=json.loads(LOCK.read_text())
    if input_lock()!=lock: raise SystemExit("source/protocol lock drift")
    from domains.engine_provenance import build_is_stale
    stale=build_is_stale(str(ROOT))
    if stale: raise SystemExit("native build stale:\n"+"\n".join(stale))
    env={**os.environ,"PYTHONPATH":f"{ROOT/'runners/dsl/python'}:{ROOT}:{os.environ.get('PYTHONPATH','')}"}
    rows=[]
    for q in WIDTHS:
        for rep in range(REPLICATES):
            for family in FAMILIES:
                p=subprocess.run([sys.executable,str(RUNNER),"--worker",str(q),family,str(rep)],cwd=ROOT,env=env,
                                 text=True,capture_output=True,check=True)
                row=json.loads(p.stdout.strip()); rows.append(row)
                print(f"q={q} rep={rep} family={family} E={row['edges']} cert={row['certificate_width']} "
                      f"maxdeg={row['degree_max']} JT={row['timing_ns']['jt_minfill_wall']/1e6:.2f}ms",flush=True)
    post=input_lock()
    checks={"complete_workers":len(rows)==54,
      "coverage":all(sum(r["width"]==q and r["family"]==f for r in rows)==REPLICATES for q in WIDTHS for f in FAMILIES),
      "paired_node_edge_counts":all(r["nodes"]==N and r["edges"]==r["expected_edges"] for r in rows),
      "width_certificates":all(r["certificate_width"]==r["width"] for r in rows),
      "exact_extraction":all(r["extraction_exact"] for r in rows),
      "oracle_match":all(abs(r["minfill_direct_energy"]-r["oracle_energy"])<1e-8 and
                         abs(r["certificate_direct_energy"]-r["oracle_energy"])<1e-8 and
                         abs(r["minfill_energy"]-r["oracle_energy"])<1e-8 and
                         abs(r["certificate_energy"]-r["oracle_energy"])<1e-8 for r in rows),
      "no_mutation":all(r["no_mutation"] for r in rows),
      "degree_metrics_complete":all(all(k in r for k in ("degree_min","degree_median","degree_p90","degree_max","degree_gini")) for r in rows),
      "pre_post_lock_match":lock==post}
    payload={"schema_version":1,"run_id":"can-edge-matched-degree-profile-v1.1-20260929","status":"complete",
      "configuration":{"widths":WIDTHS,"nodes":N,"replicates":REPLICATES,"families":FAMILIES},
      "input_lock":lock,"post_run_input_lock":post,
      "claim_boundary":"matched synthetic graph topologies only; no natural task distribution or learned frame discovery",
      "environment":{"python":platform.python_version(),"platform":platform.platform()},"checks":checks,"runs":rows}
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"output":OUT.relative_to(ROOT).as_posix(),"checks":checks},indent=2))
    if not all(checks.values()): raise SystemExit("degree-profile inference integrity failure")

if __name__=="__main__": main()
