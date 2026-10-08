#!/usr/bin/env python3
"""Sequential, locked code_reading route rung-entry panel."""
from __future__ import annotations
import ast, hashlib, json, os, platform, resource, subprocess, sys, time, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_THINKPYTHON_CODE_RUNG_ENTRY_PANEL_V1_PREREG_20260927.md"
SELECTOR = ROOT / "scripts/audit_thinkpython_code_frame_v1.py"
FRAME = ROOT / "evaluation/reports/thinkpython_code_rung_frame_v1_20260927.json"
ANALYZER = ROOT / "scripts/analyze_substrate_thinkpython_code_rung_entry_panel_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/thinkpython_code_rung_entry_panel_v1_lock_20260927.json"
OUT = ROOT / "evaluation/reports/thinkpython_code_rung_entry_panel_v1_20260927.json"
DATA = ROOT / "data/think_python_2e"
BLOCK = re.compile(r"```(?:python)?\s*\n(.*?)\n```", re.S | re.I)

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha(path): return sha_bytes(Path(path).read_bytes())
def tree(folder, suffixes=None):
    out = {}
    for p in sorted(folder.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts and (suffixes is None or p.suffix in suffixes):
            out[p.relative_to(ROOT).as_posix()] = sha(p)
    return out

def inputs():
    from substrate_rs import _native
    return {"protocol_sha256": sha(PROTOCOL), "selector_sha256": sha(SELECTOR),
            "frame_sha256": sha(FRAME), "runner_sha256": sha(__file__),
            "analyzer_sha256": sha(ANALYZER),
            "source_trees": {"domains": tree(ROOT / "domains", {".py"}),
                "substrate": tree(ROOT / "substrate", {".py"}), "worlds": tree(ROOT / "worlds", {".py"}),
                "scripts": tree(ROOT / "scripts", {".py"}), "seeds": tree(ROOT / "seeds", {".json"}),
                "native_python": tree(ROOT / "runners/dsl/python", {".py"}),
                "rust": tree(ROOT / "runners/dsl/src", {".rs"}), "think_python": tree(DATA)},
            "native_extension_sha256": sha(Path(_native.__file__).resolve())}

def node_id(n): return int(n.value if hasattr(n, "value") else n)
def summaries(adapter, typ, fields):
    rows=[]
    for n in adapter.s.nodes(typ):
        a=adapter.s.node(n)["attrs"]
        rows.append({"id":node_id(n), **{k:a.get(k) for k in fields}})
    return rows
def receipts(adapter):
    return [{"id":r["id"], "native_steps":r.get("native_steps"), "native_rule":r.get("native_rule")}
            for r in summaries(adapter,"NativeReflectiveFacultyReceipt",("cluster","native_steps","native_rule"))
            if r.get("cluster")=="reflective_faculty.concern_decode_settlement"]

def extract(chapter, block_index):
    text=(DATA/chapter).read_text(encoding="utf-8")
    matches=list(BLOCK.finditer(text))
    source=matches[int(block_index)].group(1)
    return source

def worker(rep):
    before=inputs()
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from substrate_rs import _native
    frame=json.loads(FRAME.read_text())
    adapter=WorldAdapter(seeds=(), shadow_read=False, deep_ingest=False)
    bs,bc=time.perf_counter_ns(),time.process_time_ns(); boot=load_all_seeds(adapter)
    boot_wall=time.perf_counter_ns()-bs; boot_cpu=time.process_time_ns()-bc
    tasks=[]
    from domains import code_reading
    for i, selected in enumerate(frame["selected"]):
        source=extract(selected["chapter"],selected["block_index"])
        observed_sha=sha_bytes(source.encode("utf-8"))
        rb={r["id"] for r in receipts(adapter)}
        ob={r["id"] for r in summaries(adapter,"Observation",())}
        ab={r["id"] for r in summaries(adapter,"CapabilityAxis",())}
        tb={r["id"] for r in summaries(adapter,"Transform",())}
        sb={r["id"] for r in summaries(adapter,"ShapeSignature",())}
        n0,e0=adapter.inner.node_count(),adapter.inner.edge_count()
        ws,cs=time.perf_counter_ns(),time.process_time_ns(); error=None; result=None
        try: result=code_reading.read_function(adapter,source,selected["selected_function"])
        except BaseException as exc: error=f"{type(exc).__name__}: {exc}"
        wall=time.perf_counter_ns()-ws; cpu=time.process_time_ns()-cs
        rafter=receipts(adapter); newr=[r for r in rafter if r["id"] not in rb]
        obs=[r for r in summaries(adapter,"Observation",("status","covered_by","key")) if r["id"] not in ob]
        for o in obs:
            oid=_native.NodeID(o["id"])
            o["minted_axis_ids"]=[node_id(x) for x in adapter.inner.neighbours(oid,"minted")]
            o["transform_ids"]=[node_id(x) for x in adapter.inner.neighbours(oid,"has_transform")]
        axes=[r for r in summaries(adapter,"CapabilityAxis",("name","origin","provenance","induced","kind","word","shortfall","saturation","capability_keys","residual_predicates","closest_held_shape")) if r["id"] not in ab]
        for a in axes:
            word=a.pop("word",None); a["word_sha256"]=sha_bytes(str(word).encode()) if word is not None else None
        transforms=[r for r in summaries(adapter,"Transform",("name","kind","status")) if r["id"] not in tb]
        signatures=[r for r in summaries(adapter,"ShapeSignature",("name","signature","kind")) if r["id"] not in sb]
        tasks.append({"index":i,"sample_id":selected["id"],"source_sha256_expected":selected["source_sha256"],
            "source_sha256_observed":observed_sha,"error":error,"task_wall_ns":wall,"task_cpu_ns":cpu,
            "construction_present":bool(result and result.get("construction")),
            "construction":result.get("construction") if result else None,
            "route_minted":bool(result and result.get("minted")),
            "term_present":bool(result and result.get("term")),
            "receipt_delta":len(newr),"new_receipts":newr,"new_observations":obs,
            "new_capability_axes":axes,"new_induced_axes":[a for a in axes if a.get("induced")],
            "new_transforms":transforms,"new_shape_signatures":signatures,
            "node_delta":adapter.inner.node_count()-n0,"edge_delta":adapter.inner.edge_count()-e0})
        del result,source
    after=inputs()
    return {"replicate":rep,"pid":os.getpid(),"locked_inputs_before":before,"locked_inputs_after":after,
        "source_stable":before==after,"boot":{"loaded":boot.get("loaded"),"total":boot.get("total"),
        "failed":boot.get("failed",[]),"wall_ns":boot_wall,"cpu_ns":boot_cpu},
        "runtime":{"peak_rss_bytes":int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),
        "python":sys.version,"platform":platform.platform()},"tasks":tasks}

def main():
    if sys.argv[1:]==["--lock"]:
        print(json.dumps({"locked_inputs":inputs()},indent=2,sort_keys=True)); return
    if sys.argv[1:]==["--worker"]:
        print(json.dumps(worker(int(os.environ["OCEL0_TP_CODE_REP"])),sort_keys=True)); return
    locked=inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:
        raise SystemExit("missing or stale Think Python code rung-entry lock")
    env={**os.environ,"PYTHONPATH":f"{ROOT}:{ROOT/'runners/dsl/python'}","OZMA_SEED_PERSIST_DISABLED":"1"}
    runs=[]
    for rep in (0,1):
        proc=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker"],cwd=ROOT,
            env={**env,"OCEL0_TP_CODE_REP":str(rep)},text=True,capture_output=True,timeout=1800)
        try: row=json.loads(proc.stdout)
        except Exception: row={"replicate":rep,"worker_error":proc.stderr or proc.stdout}
        row.update({"worker_returncode":proc.returncode,"worker_stderr":proc.stderr}); runs.append(row)
        print(f"completed=worker{rep} rc={proc.returncode}",file=sys.stderr,flush=True)
    post=inputs(); checks={"two_fresh_workers":len(runs)==2 and len({r.get("pid") for r in runs})==2,
        "parent_lock_stable":post==locked,"worker_source_stability":all(r.get("source_stable") and r.get("locked_inputs_before")==locked==r.get("locked_inputs_after") for r in runs),
        "all_64_rows_each":all(len(r.get("tasks",[]))==64 for r in runs),"workers_succeeded":all(r.get("worker_returncode")==0 and r.get("boot",{}).get("loaded",0)>0 for r in runs)}
    report={"schema_version":1,"run_id":"thinkpython-code-rung-entry-panel-v1-20260927","locked_inputs":locked,
        "post_run_inputs":post,"integrity_checks":checks,"integrity_pass":all(checks.values()),"runs":runs,
        "claim_boundary":"Sequential production code_reading route outcomes and costs for a fixed 64-example Think Python sample; not semantic accuracy or representative software-workload prevalence."}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"report":OUT.relative_to(ROOT).as_posix(),"integrity_checks":checks},indent=2))
    if not report["integrity_pass"]: raise SystemExit("integrity gates failed")

if __name__=="__main__": main()
