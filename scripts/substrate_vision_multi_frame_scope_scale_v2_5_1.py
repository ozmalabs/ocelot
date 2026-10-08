#!/usr/bin/env python3
"""Source-locked global/root-scoped settling across multi-frame graphs."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import platform
import random
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_VISION_MULTI_FRAME_SCOPE_SCALE_V2_5_1_AMENDMENT_20260929.md"
LOCK = ROOT / "evaluation/substrate_capability/vision_multi_frame_scope_scale_v2_5_1_lock_20260929.json"
RAW = ROOT / "evaluation/reports/vision_multi_frame_scope_scale_v2_5_1_workers_raw_20260929.json"
OUT = ROOT / "evaluation/reports/vision_multi_frame_scope_scale_v2_5_1_20260929.json"
CELLDIR = ROOT / "evaluation/reports/vision_multi_frame_scope_scale_v2_5_1_cells"
ANALYZER = ROOT / "scripts/analyze_substrate_vision_multi_frame_scope_scale_v2_5_1.py"
SEED_DOC = ROOT / "seeds/vision_settle.json"
SIZES = (16, 32, 48)
SEEDS = (4101, 7301, 10703)
SIBLING_CASES = ((0, "none"), (1, "equal"), (1, "contrasting"), (2, "equal"), (2, "contrasting"))
SCOPES = ("global", "scoped")
MODES = ("plain", "audit")
CAP = 10_000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_inputs() -> dict:
    from domains.engine_provenance import engine_provenance
    from substrate_rs import _native
    source_paths = (
        "runners/dsl/python/substrate_rs/__init__.py", "runners/dsl/python/substrate_rs/ext.py",
        "runners/dsl/python/substrate_rs/_native.build.json", "runners/dsl/src/py.rs",
        "runners/dsl/src/scale_audit.rs", "runners/dsl/src/rewrite.rs",
        "runners/dsl/src/substrate.rs", "runners/dsl/src/term.rs",
        "substrate/seed_loader.py", "domains/engine_provenance.py",
        "scripts/substrate_vision_two_sheet_current_source_scale_v2_4.py",
        "scripts/analyze_substrate_vision_two_sheet_current_source_scale_v2_4.py",
        "evaluation/reports/vision_two_sheet_current_source_scale_v2_4_analysis_20260927.json",
    )
    return {"protocol_sha256": sha(PROTOCOL), "runner_sha256": sha(Path(__file__)),
        "analyzer_sha256": sha(ANALYZER), "seed_sha256": sha(SEED_DOC),
        "source_sha256": {p: sha(ROOT / p) for p in source_paths},
        "native_extension_sha256": sha(Path(_native.__file__).resolve()),
        "engine_provenance": engine_provenance(), "python": sys.version,
        "platform": platform.platform(), "sizes": list(SIZES), "seeds": list(SEEDS),
        "sibling_cases": [list(x) for x in SIBLING_CASES], "scopes": list(SCOPES),
        "modes": list(MODES), "progress_cap": CAP}


def scoped_manifest(doc: dict) -> dict:
    manifest = copy.deepcopy(doc)
    found = 0
    def visit(x):
        nonlocal found
        if isinstance(x, dict):
            if x.get("type") == "NodesOfType" and x.get("node_type") == "SUnit":
                found += 1
                return {"type": "Neighbours", "node": {"type": "Var", "name": "r"},
                        "edge_type": "has_sunit", "any_type": False}
            return {k: visit(v) for k, v in x.items()}
        if isinstance(x, list): return [visit(v) for v in x]
        return x
    for rule in manifest.get("rules", []):
        if rule.get("name") == "st_settle":
            rule["name"] = "st_settle_root_scoped_benchmark"
            rule["where"] = visit(rule.get("where")); rule["effects"] = visit(rule.get("effects"))
    if found != 2: raise RuntimeError(f"expected two global SUnit populations, got {found}")
    return manifest


def peak_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value * (1024 if sys.platform.startswith("linux") else 1))


def cell_id(seed, side, siblings, sibling_state, scope, mode, omission=False):
    return f"s{seed}_n{side}_sib{siblings}_{sibling_state}_{scope}_{mode}" + ("_omit" if omission else "")


def run_cell(seed: int, side: int, siblings: int, sibling_state: str,
             scope: str, mode: str, omission: bool = False) -> dict:
    import numpy as np
    import substrate_rs as sr
    from substrate.seed_loader import engine_rules_only
    manifest = engine_rules_only(json.loads(SEED_DOC.read_text()))
    manifest["rules"] = [r for r in manifest.get("rules", []) if r.get("name") == "st_settle"]
    if scope == "scoped": manifest = scoped_manifest(manifest)
    if len(manifest["rules"]) != 1: raise RuntimeError("expected exactly st_settle")
    n = side * side; frame_count = siblings + 1
    rng = np.random.Generator(np.random.PCG64(seed + 31 * side))
    affs = [(rng.random(n) * 0.2).tolist()] + [[0.0] * n for _ in range(siblings)]
    states = [1.0] + ([1.0 if sibling_state == "equal" else 0.0] * siblings)
    outer = sr.Substrate(); inner = outer._inner; inner.load_seed_manifest(manifest)
    params = inner.nodes("SettleParams")
    if len(params) != 1: raise RuntimeError(f"expected one SettleParams, got {len(params)}")
    inner.set_attr(params[0], "settle", 1.0)
    roots=[]; sheets=[]
    for fi, state in enumerate(states):
        root = inner.add_node("World", {"name": f"frame_{fi}", "step": 0.0})
        units=[]
        for i in range(n):
            units.append(inner.add_node("SUnit", {"name": f"f{fi}_s{i}", "act": state,
                "aff": float(affs[fi][i]), "aff_step": 0.0, "act_next": -1.0}))
        for row in range(side):
            for col in range(side):
                u = units[row * side + col]
                inner.add_edge_unchecked(root, "has_sunit", u, {})
                for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
                    rr, cc = row + dr, col + dc
                    if 0 <= rr < side and 0 <= cc < side:
                        inner.add_edge_unchecked(u, "sunit_neighbour", units[rr * side + cc], {})
        roots.append(root); sheets.append(units)
    omitted = None
    if omission:
        if side != 16 or siblings != 1 or sibling_state != "contrasting":
            raise RuntimeError("omission control requires n=16, one contrasting sibling")
        omitted = sheets[0][0]
        inner.remove_edge_unchecked(roots[0], "has_sunit", omitted)
    member_ids = [[u for u in inner.neighbours(root, "has_sunit")] for root in roots]
    if [len(x) for x in member_ids] != [n - int(omission)] + [n] * siblings:
        raise RuntimeError("frame ownership counts do not match design")
    if mode == "audit":
        inner.scale_audit_set_enabled(False); inner.scale_audit_set_per_rule_enabled(False)
        inner.scale_audit_reset(); inner.scale_audit_per_rule_reset()
        inner.scale_audit_set_enabled(True); inner.scale_audit_set_per_rule_enabled(True)
    t_wall=time.perf_counter_ns(); t_cpu=time.process_time_ns()
    progress=int(inner.run_rules(CAP))
    wall=time.perf_counter_ns()-t_wall; cpu=time.process_time_ns()-t_cpu
    actual=[[float(inner.node(u)["attrs"].get("act_next", -1.0)) for u in sheet] for sheet in sheets]
    graph=inner.graph_to_dict()
    counters=dict(inner.scale_audit_snapshot()) if mode == "audit" else {}
    per_rule=[[int(i),str(m),int(v)] for i,m,v in inner.scale_audit_per_rule_snapshot()] if mode == "audit" else []
    per_clause=[[int(i),int(p),int(v)] for i,p,v in inner.scale_audit_match_clause_snapshot()] if mode == "audit" else []
    frame_digests=[]
    for fi, sheet in enumerate(sheets):
        frame_digests.append(hashlib.sha256(json.dumps({"act_next": actual[fi], "aff": affs[fi], "act": states[fi]},separators=(",",":"),sort_keys=True).encode()).hexdigest())
    return {"cell_id":cell_id(seed,side,siblings,sibling_state,scope,mode,omission),
        "seed":seed,"side":side,"units_per_frame":n,"sibling_frames":siblings,"sibling_state":sibling_state,
        "frame_count":frame_count,"scope":scope,"mode":mode,"omission":omission,"omitted_unit":None if omitted is None else int(omitted.value if hasattr(omitted,"value") else omitted),
        "pid":os.getpid(),"progress":progress,"budget":CAP,"budget_exit":progress>=CAP,
        "member_counts":[len(x) for x in member_ids],"aff_by_frame":affs,"initial_act_by_frame":states,
        "actual_act_next":actual,"frame_digests":frame_digests,"max_abs_equation_residual":None,
        "global_counters":{str(k):int(v) for k,v in counters.items()},"per_rule_counters":per_rule,"per_clause_counters":per_clause,
        "closure_wall_ns":wall,"closure_cpu_ns":cpu,"peak_rss_bytes":peak_rss_bytes(),
        "graph_node_count":len(graph.get("nodes",[])),"graph_edge_count":len(graph.get("edges",[])),
        "worker_started_inputs":None,"worker_finished_inputs":None}


def worker(*args):
    start=source_inputs(); row=run_cell(*args); end=source_inputs()
    row["worker_started_inputs"]=start;row["worker_finished_inputs"]=end;row["source_stable"]=start==end
    return row


def main():
    if sys.argv[1:] == ["--lock"]:
        print(json.dumps({"locked_inputs":source_inputs()},indent=2,sort_keys=True));return
    if len(sys.argv) in (8,9) and sys.argv[1] == "--cell":
        _,_,seed,side,siblings,state,scope,mode,*omit=sys.argv
        omission=bool(omit and omit[0].lower()=="true")
        print(json.dumps(worker(int(seed),int(side),int(siblings),state,scope,mode,omission),sort_keys=True));return
    if RAW.exists() or OUT.exists() or CELLDIR.exists(): raise SystemExit("refusing to overwrite existing v2.5 outputs")
    locked=source_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked: raise SystemExit("missing or stale v2.5 source lock")
    CELLDIR.mkdir(parents=True,exist_ok=False)
    specs=[(seed,side,sib,state,scope,mode,False) for side in SIZES for sib,state in SIBLING_CASES
           for seed in SEEDS for scope in SCOPES for mode in MODES]
    omissions=[(SEEDS[0],16,1,"contrasting",scope,mode,True) for scope in SCOPES for mode in MODES]
    random.Random(20260929).shuffle(specs); jobs=specs+omissions;random.Random(20260930).shuffle(jobs)
    runs=[]
    for ix,spec in enumerate(jobs,1):
        command=[sys.executable,str(Path(__file__).resolve()),"--cell",*map(str,spec)]
        proc=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,check=True)
        row=json.loads(proc.stdout);runs.append(row)
        (CELLDIR/f"{row['cell_id']}.json").write_text(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n")
        print(f"completed={ix}/{len(jobs)} cell={row['cell_id']} progress={row['progress']}",flush=True)
    post=source_inputs();raw={"schema_version":1,"run_id":"vision-multi-frame-scope-scale-v2.5.1-20260929",
        "locked_inputs":locked,"post_run_inputs":post,"schedule":[list(x) for x in jobs],"runs":runs}
    RAW.write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n")
    OUT.write_text(json.dumps({"raw_report":str(RAW.relative_to(ROOT)),"locked_inputs":locked,
        "post_run_inputs":post,"worker_count":len(runs),"source_stable":post==locked},indent=2,sort_keys=True)+"\n")
    print(json.dumps({"output":str(OUT),"workers":len(runs),"source_stable":post==locked},indent=2))
    if post!=locked or len({r["pid"] for r in runs})!=len(jobs):raise SystemExit("worker/source gate failed")


if __name__ == "__main__": main()
