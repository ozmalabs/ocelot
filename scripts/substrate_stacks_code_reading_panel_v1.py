#!/usr/bin/env python3
"""Two-worker, source-locked Stacks Project code-reading panel."""
from __future__ import annotations
import hashlib, json, os, platform, resource, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_STACKS_CODE_READING_PANEL_V1_PREREG_20260927.md"
SELECTOR = ROOT / "scripts/audit_stacks_code_reading_frame_v1.py"
FRAME = ROOT / "evaluation/reports/stacks_code_reading_frame_v1_20260927.json"
ANALYZER = ROOT / "scripts/analyze_substrate_stacks_code_reading_panel_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/stacks_code_reading_panel_v1_lock_20260927.json"
OUT = ROOT / "evaluation/reports/stacks_code_reading_panel_v1_20260927.json"
DATA = ROOT / "data/stacks/repo"

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def tree(folder, suffixes=None):
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(folder.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts and (suffixes is None or p.suffix in suffixes)}
def loaded_seed_tree(folder):
    paths=sorted(folder.glob("*.json"))+sorted((folder/"generated").glob("*.json"))
    return {p.relative_to(ROOT).as_posix():sha(p) for p in paths if p.is_file()}
def inputs():
    from substrate_rs import _native
    source_commit = subprocess.run(["git", "-C", str(DATA), "rev-parse", "HEAD"],
                                   text=True, capture_output=True, check=True).stdout.strip()
    return {"protocol_sha256": sha(PROTOCOL), "selector_sha256": sha(SELECTOR),
            "frame_sha256": sha(FRAME), "runner_sha256": sha(__file__),
            "analyzer_sha256": sha(ANALYZER),
            "source_trees": {"domains": tree(ROOT/"domains", {".py"}),
                "substrate": tree(ROOT/"substrate", {".py"}), "worlds": tree(ROOT/"worlds", {".py"}),
                "scripts": tree(ROOT/"scripts", {".py"}), "seeds": loaded_seed_tree(ROOT/"seeds"),
                "native_python": tree(ROOT/"runners/dsl/python", {".py"}),
                "rust": tree(ROOT/"runners/dsl/src", {".rs"}), "stacks_scripts": tree(DATA/"scripts"),
                "stacks_license": {p.relative_to(ROOT).as_posix(): sha(p) for p in (DATA/"scripts/LICENSE", DATA/"README")}},
            "stacks_repository_commit": source_commit,
            "native_extension_sha256": sha(Path(_native.__file__).resolve())}
def node_id(n): return int(n.value if hasattr(n, "value") else n)
def summaries(a, typ, fields):
    return [{"id": node_id(n), **{k:a.s.node(n)["attrs"].get(k) for k in fields}} for n in a.s.nodes(typ)]
def receipts(a):
    return [r for r in summaries(a,"NativeReflectiveFacultyReceipt",("cluster","native_steps","native_rule"))
            if r.get("cluster")=="reflective_faculty.concern_decode_settlement"]
def worker(rep):
    before=inputs()
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from substrate_rs import _native
    from domains import code_reading
    frame=json.loads(FRAME.read_text())
    a=WorldAdapter(seeds=(), shadow_read=False, deep_ingest=False)
    bs,bc=time.perf_counter_ns(),time.process_time_ns(); boot=load_all_seeds(a)
    bootw=time.perf_counter_ns()-bs; bootc=time.process_time_ns()-bc
    tasks=[]
    for i,row in enumerate(frame["selected"]):
        source=(ROOT/row["file"]).read_text(encoding="utf-8")
        observed=hashlib.sha256(source.encode()).hexdigest()
        rb={r["id"] for r in receipts(a)}; ob={r["id"] for r in summaries(a,"Observation",())}
        ab={r["id"] for r in summaries(a,"CapabilityAxis",())}; tb={r["id"] for r in summaries(a,"Transform",())}
        sb={r["id"] for r in summaries(a,"ShapeSignature",())}; n0,e0=a.inner.node_count(),a.inner.edge_count()
        ts,cs=time.perf_counter_ns(),time.process_time_ns(); err=None; result=None
        try: result=code_reading.read_function(a,source,row["function"])
        except BaseException as exc: err=f"{type(exc).__name__}: {exc}"
        wall=time.perf_counter_ns()-ts; cpu=time.process_time_ns()-cs
        obs=[]
        for r in summaries(a,"Observation",("status","covered_by","key")):
            if r["id"] not in ob:
                oid=_native.NodeID(r["id"]); r["minted_axis_ids"]=[node_id(x) for x in a.inner.neighbours(oid,"minted")]; obs.append(r)
        axes=[r for r in summaries(a,"CapabilityAxis",("name","origin","provenance","induced","kind","shortfall","saturation","capability_keys","residual_predicates","closest_held_shape")) if r["id"] not in ab]
        for axis in axes:
            surface=axis.pop("word",None); axis["word_sha256"]=hashlib.sha256(str(surface).encode()).hexdigest() if surface is not None else None
        tasks.append({"index":i,"file":row["file"],"function":row["function"],"function_sha256_expected":row["function_sha256"],
            "module_sha256_expected":row["module_sha256"],"module_sha256_observed":observed,"error":err,
            "task_wall_ns":wall,"task_cpu_ns":cpu,"construction_present":bool(result and result.get("construction")),
            "construction":result.get("construction") if result else None,"route_minted":bool(result and result.get("minted")),
            "term_present":bool(result and result.get("term")),"receipt_delta":len({r["id"] for r in receipts(a)}-rb),
            "new_observations":obs,"new_capability_axes":axes,"new_transforms":len([x for x in summaries(a,"Transform",()) if x["id"] not in tb]),
            "new_shape_signatures":len([x for x in summaries(a,"ShapeSignature",()) if x["id"] not in sb]),
            "node_delta":a.inner.node_count()-n0,"edge_delta":a.inner.edge_count()-e0})
    after=inputs()
    return {"replicate":rep,"pid":os.getpid(),"locked_inputs_before":before,"locked_inputs_after":after,"source_stable":before==after,
        "boot":{"loaded":boot.get("loaded"),"total":boot.get("total"),"failed":boot.get("failed",[]),"wall_ns":bootw,"cpu_ns":bootc},
        "runtime":{"peak_rss_bytes":int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),"python":sys.version,"platform":platform.platform()},"tasks":tasks}
def main():
    if sys.argv[1:]==["--frame"]:
        import runpy
        ns=runpy.run_path(str(SELECTOR)); frame={"schema_version":1,"candidate_count":len(ns["candidates"]()),"selected":ns["candidates"]()}
        FRAME.write_text(json.dumps(frame,indent=2,sort_keys=True)+"\n"); print(FRAME.relative_to(ROOT)); return
    if sys.argv[1:]==["--lock"]: print(json.dumps({"locked_inputs":inputs()},indent=2,sort_keys=True)); return
    if sys.argv[1:]==["--worker"]: print(json.dumps(worker(int(os.environ["OCEL0_STACKS_CODE_REP"])),sort_keys=True)); return
    locked=inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked: raise SystemExit("missing or stale Stacks code-reading lock")
    env={**os.environ,"PYTHONPATH":f"{ROOT}:{ROOT/'runners/dsl/python'}","OZMA_SEED_PERSIST_DISABLED":"1"}; runs=[]
    from scripts.substrate_run_manifest import start_console_capture, finish_console_capture, capture_run_manifest
    run_id="stacks-code-reading-panel-v1-20260927"
    started=datetime.now(timezone.utc).isoformat(); capture_state=start_console_capture(run_id)
    for rep in (0,1):
        p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker"],cwd=ROOT,env={**env,"OCEL0_STACKS_CODE_REP":str(rep)},text=True,capture_output=True,timeout=1800)
        try:r=json.loads(p.stdout)
        except Exception:r={"replicate":rep,"worker_error":p.stderr or p.stdout}
        r.update({"worker_returncode":p.returncode,"worker_stderr":p.stderr});runs.append(r)
        print(f"completed=worker{rep} rc={p.returncode}",file=sys.stderr,flush=True)
    post=inputs(); frame=json.loads(FRAME.read_text())
    checks={"two_fresh_workers":len(runs)==2 and len({r.get("pid") for r in runs})==2,"parent_lock_stable":post==locked,
      "worker_source_stability":all(r.get("source_stable") and r.get("locked_inputs_before")==locked==r.get("locked_inputs_after") for r in runs),
      "all_selected_rows_each":all(len(r.get("tasks",[]))==frame["candidate_count"] for r in runs),
      "workers_succeeded":all(r.get("worker_returncode")==0 and r.get("boot",{}).get("loaded",0)>0 for r in runs)}
    console=finish_console_capture(capture_state)
    input_sets=locked["source_trees"]
    source_paths=sorted({p for k,v in input_sets.items() if k not in ("stacks_scripts","stacks_license") for p in v})
    data_paths=sorted({p for k in ("stacks_scripts","stacks_license") for p in input_sets[k]})
    manifest=capture_run_manifest(run_id=run_id,runner="scripts/substrate_stacks_code_reading_panel_v1.py",
      protocol_files=[PROTOCOL.relative_to(ROOT).as_posix(),SELECTOR.relative_to(ROOT).as_posix(),FRAME.relative_to(ROOT).as_posix()],
      source_files=source_paths+ [LOCK.relative_to(ROOT).as_posix()], data_files=data_paths,
      analysis_files=[ANALYZER.relative_to(ROOT).as_posix()],started_utc=started,
      exit_status=0 if all(checks.values()) else 1,stdout_stderr_capture=console,
      child_processes=[{"replicate":r.get("replicate"),"pid":r.get("pid"),"returncode":r.get("worker_returncode"),
                        "stderr":r.get("worker_stderr"),"structured_stdout_embedded_in_raw":True} for r in runs])
    report={"schema_version":1,"run_id":run_id,"locked_inputs":locked,"post_run_inputs":post,"run_manifest":manifest,
      "integrity_checks":checks,"integrity_pass":all(checks.values()),"runs":runs,
      "claim_boundary":"Production code_reading route outcomes on every top-level function in six Apache-2.0 Stacks Project helper scripts; one repository slice, not semantic accuracy or software-workload prevalence."}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"report":OUT.relative_to(ROOT).as_posix(),"integrity_checks":checks},indent=2))
    if not report["integrity_pass"]: raise SystemExit("integrity gates failed")
if __name__=="__main__": main()
