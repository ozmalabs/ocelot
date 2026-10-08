#!/usr/bin/env python3
"""Source-locked held-out output prediction panel on Stacks string helpers."""
from __future__ import annotations
import hashlib,json,os,platform,resource,subprocess,sys,time
import re
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_STACKS_STRING_PREDICTION_PANEL_V2_1_REPLICATION_PREREG_20260927.md"
SELECTOR=ROOT/"scripts/audit_stacks_string_prediction_frame_v2_1.py"
FRAME=ROOT/"evaluation/reports/stacks_string_prediction_frame_v2_1_20260927.json"
ANALYZER=ROOT/"scripts/analyze_substrate_stacks_string_prediction_panel_v2_1.py"
LOCK=ROOT/"evaluation/substrate_capability/stacks_string_prediction_panel_v2_1_lock_20260927.json"
OUT=ROOT/"evaluation/reports/stacks_string_prediction_panel_v2_1_20260927.json"
DATA=ROOT/"data/stacks/repo";TPDATA=ROOT/"data/think_python_2e";BLOCK=re.compile(r"```(?:python)?\s*\n(.*?)\n```",re.S|re.I)
BASE_RAW=ROOT/"evaluation/reports/stacks_string_prediction_panel_v1_20260927.json"
BASE_ANALYSIS=ROOT/"evaluation/reports/stacks_string_prediction_panel_v1_analysis_20260927.json"
BASE_FRAME=ROOT/"evaluation/reports/stacks_string_prediction_frame_v1_20260927.json"
PREV_RAW=ROOT/"evaluation/reports/stacks_string_prediction_panel_v2_20260927.json"
PREV_ANALYSIS=ROOT/"evaluation/reports/stacks_string_prediction_panel_v2_analysis_20260927.json"
PREV_FRAME=ROOT/"evaluation/reports/stacks_string_prediction_frame_v2_20260927.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tree(folder,suffixes=None):return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(folder.rglob("*")) if p.is_file() and "__pycache__" not in p.parts and (suffixes is None or p.suffix in suffixes)}
def loaded_seed_tree(folder):
    paths=sorted(folder.glob("*.json"))+sorted((folder/"generated").glob("*.json"))
    return {p.relative_to(ROOT).as_posix():sha(p) for p in paths if p.is_file()}
def inputs():
    from substrate_rs import _native
    commit=subprocess.run(["git","-C",str(DATA),"rev-parse","HEAD"],text=True,capture_output=True,check=True).stdout.strip()
    return {"protocol_sha256":sha(PROTOCOL),"selector_sha256":sha(SELECTOR),"frame_sha256":sha(FRAME),"runner_sha256":sha(__file__),"analyzer_sha256":sha(ANALYZER),
      "source_trees":{"domains":tree(ROOT/"domains",{".py"}),"substrate":tree(ROOT/"substrate",{".py"}),"worlds":tree(ROOT/"worlds",{".py"}),
        "scripts":tree(ROOT/"scripts",{".py"}),"seeds":loaded_seed_tree(ROOT/"seeds"),"native_python":tree(ROOT/"runners/dsl/python",{".py"}),
        "rust":tree(ROOT/"runners/dsl/src",{".rs"}),"stacks_scripts":tree(DATA/"scripts"),
        "stacks_license_readme":{p.relative_to(ROOT).as_posix():sha(p) for p in (DATA/"scripts/LICENSE",DATA/"README")},
        "think_python_control":tree(TPDATA)},
      "stacks_repository_commit":commit,"native_extension_sha256":sha(Path(_native.__file__).resolve()),
      "baseline_artifacts":{"v1_raw":sha(BASE_RAW),"v1_analysis":sha(BASE_ANALYSIS),"v1_frame":sha(BASE_FRAME),
        "v2_raw":sha(PREV_RAW),"v2_analysis":sha(PREV_ANALYSIS),"v2_frame":sha(PREV_FRAME)}}
def nodeid(n):return int(n.value if hasattr(n,"value") else n)
def rows(a,typ,fields):return [{"id":nodeid(n),**{k:a.s.node(n)["attrs"].get(k) for k in fields}} for n in a.s.nodes(typ)]
def receipts(a):return [r for r in rows(a,"NativeReflectiveFacultyReceipt",("cluster","native_steps","native_rule")) if r.get("cluster")=="reflective_faculty.concern_decode_settlement"]
def norm(x):
    if x is None or type(x) in (bool,int,float,str):return {"type":type(x).__name__,"value":x}
    raise TypeError("nonprimitive output")
def worker(rep):
    before=inputs()
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from substrate_rs import _native
    from domains import code_reading
    frame=json.loads(FRAME.read_text())
    a=WorldAdapter(seeds=(),shadow_read=False,deep_ingest=False);bs,bc=time.perf_counter_ns(),time.process_time_ns();boot=load_all_seeds(a)
    bootw=time.perf_counter_ns()-bs;bootc=time.process_time_ns()-bc;calls=[]
    schedule=[("stacks",r) for r in frame["selected"]]+[("positive_control",frame["positive_control"])]
    for fi,(corpus,row) in enumerate(schedule):
      if corpus=="stacks":source=(ROOT/row["file"]).read_text(encoding="utf-8")
      else:source=list(BLOCK.finditer((TPDATA/row["chapter"]).read_text(encoding="utf-8")))[row["block_index"]].group(1)
      function_sha=row.get("function_sha256",row.get("source_sha256"));file_sha_expected=row.get("module_sha256",row.get("file_sha256"));source_sha_expected=row.get("module_sha256",row.get("source_sha256"))
      for ci,args in enumerate(row["input_cases"]):
        rb={r["id"] for r in receipts(a)};obs0={r["id"] for r in rows(a,"Observation",())};axes0={r["id"] for r in rows(a,"CapabilityAxis",())}
        n0,e0=a.inner.node_count(),a.inner.edge_count();ts,cs=time.perf_counter_ns(),time.process_time_ns();prediction=None;err=None
        try:prediction=norm(code_reading.predict_output(a,source,row["function"],args))
        except BaseException as exc:err=type(exc).__name__
        wall=time.perf_counter_ns()-ts;cpu=time.process_time_ns()-cs;newobs=[]
        for o in rows(a,"Observation",("status","covered_by","key")):
          if o["id"] not in obs0:
            oid=_native.NodeID(o["id"]);o["minted_axis_ids"]=[nodeid(x) for x in a.inner.neighbours(oid,"minted")];newobs.append(o)
        calls.append({"function_index":fi,"case_index":ci,"corpus":corpus,"function":row["function"],"function_sha256_expected":function_sha,
          "corpus_file_sha256_expected":file_sha_expected,"source_sha256_expected":source_sha_expected,"source_sha256_observed":hashlib.sha256(source.encode()).hexdigest(),"args":args,"prediction":prediction,
          "error_type":err,"abstained":err is not None,"wall_ns":wall,"cpu_ns":cpu,"receipt_delta":len({r["id"] for r in receipts(a)}-rb),
          "new_observations":newobs,"new_axis_count":len({r["id"] for r in rows(a,"CapabilityAxis",())}-axes0),"node_delta":a.inner.node_count()-n0,"edge_delta":a.inner.edge_count()-e0})
    after=inputs()
    return {"replicate":rep,"pid":os.getpid(),"source_stable":before==after,"locked_inputs_before":before,"locked_inputs_after":after,
      "boot":{"loaded":boot.get("loaded"),"total":boot.get("total"),"failed":boot.get("failed",[]),"wall_ns":bootw,"cpu_ns":bootc},
      "runtime":{"peak_rss_bytes":int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),"python":sys.version,"platform":platform.platform()},"calls":calls}
def main():
    if sys.argv[1:]==["--frame"]:
      import runpy
      f=runpy.run_path(str(SELECTOR));selected=f["candidates"]();chapter="ch06_thinkpython2007.txt";block_index=17
      text=(TPDATA/chapter).read_text(encoding="utf-8");snippet=list(BLOCK.finditer(text))[block_index].group(1);import ast
      fn=next(n for n in ast.parse(snippet).body if isinstance(n,ast.FunctionDef))
      control={"chapter":chapter,"block_index":block_index,"function":fn.name,"args":[a.arg for a in fn.args.args],"source_sha256":hashlib.sha256(snippet.encode()).hexdigest(),
        "file_sha256":sha(TPDATA/chapter),"input_cases":[{"x":6,"y":3},{"x":7,"y":2}]}
      FRAME.write_text(json.dumps({"schema_version":2,"candidate_count":len(selected),"selected":selected,"positive_control":control},indent=2,sort_keys=True)+"\n");print(FRAME.relative_to(ROOT));return
    if sys.argv[1:]==["--lock"]:print(json.dumps({"locked_inputs":inputs()},indent=2,sort_keys=True));return
    if sys.argv[1:]==["--worker"]:print(json.dumps(worker(int(os.environ["OCEL0_STACKS_PRED_V2_1_REP"])),sort_keys=True));return
    locked=inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale Stacks prediction lock")
    from scripts.substrate_run_manifest import start_console_capture,finish_console_capture,capture_run_manifest
    run_id="stacks-string-prediction-panel-v2-1-20260927";started=datetime.now(timezone.utc).isoformat();capture_state=start_console_capture(run_id)
    env={**os.environ,"PYTHONPATH":f"{ROOT}:{ROOT/'runners/dsl/python'}","OZMA_SEED_PERSIST_DISABLED":"1"};runs=[]
    for rep in (0,1):
      p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker"],cwd=ROOT,env={**env,"OCEL0_STACKS_PRED_V2_1_REP":str(rep)},text=True,capture_output=True,timeout=1800)
      try:r=json.loads(p.stdout)
      except Exception:r={"replicate":rep,"worker_error":p.stderr or p.stdout}
      r.update({"worker_returncode":p.returncode,"worker_stderr":p.stderr});runs.append(r);print(f"completed=worker{rep} rc={p.returncode}",file=sys.stderr,flush=True)
    post=inputs();frame=json.loads(FRAME.read_text());checks={"two_fresh_workers":len(runs)==2 and len({r.get("pid") for r in runs})==2,
      "parent_lock_stable":post==locked,"worker_source_stability":all(r.get("source_stable") and r.get("locked_inputs_before")==locked==r.get("locked_inputs_after") for r in runs),
      "all_cases_each":all(len(r.get("calls",[]))==sum(len(x["input_cases"]) for x in frame["selected"])+len(frame["positive_control"]["input_cases"]) for r in runs),
      "workers_succeeded":all(r.get("worker_returncode")==0 and r.get("boot",{}).get("loaded",0)>0 for r in runs)}
    console=finish_console_capture(capture_state);trees=locked["source_trees"]
    source_paths=sorted({p for k,v in trees.items() if k not in ("stacks_scripts","stacks_license_readme","think_python_control") for p in v});data_paths=sorted({p for k in ("stacks_scripts","stacks_license_readme","think_python_control") for p in trees[k]})+[p.relative_to(ROOT).as_posix() for p in (BASE_RAW,BASE_ANALYSIS,BASE_FRAME,PREV_RAW,PREV_ANALYSIS,PREV_FRAME)]
    manifest=capture_run_manifest(run_id=run_id,runner="scripts/substrate_stacks_string_prediction_panel_v2_1.py",
      protocol_files=[PROTOCOL.relative_to(ROOT).as_posix(),"docs/research/engine_substrate/SUBSTRATE_STACKS_STRING_PREDICTION_PANEL_V2_1_AMENDMENT_20260927.md",SELECTOR.relative_to(ROOT).as_posix(),FRAME.relative_to(ROOT).as_posix(),"docs/research/engine_substrate/SUBSTRATE_STACKS_STRING_PREDICTION_PANEL_V1_PREREG_20260927.md","docs/research/engine_substrate/SUBSTRATE_STACKS_STRING_PREDICTION_PANEL_V2_PREREG_20260927.md"],
      source_files=source_paths+[LOCK.relative_to(ROOT).as_posix()],data_files=data_paths,analysis_files=[ANALYZER.relative_to(ROOT).as_posix()],
      started_utc=started,exit_status=0 if all(checks.values()) else 1,stdout_stderr_capture=console,
      child_processes=[{"replicate":r.get("replicate"),"pid":r.get("pid"),"returncode":r.get("worker_returncode"),"stderr":r.get("worker_stderr"),"structured_stdout_embedded_in_raw":True} for r in runs])
    report={"schema_version":1,"run_id":run_id,"locked_inputs":locked,"post_run_inputs":post,"run_manifest":manifest,"integrity_checks":checks,"integrity_pass":all(checks.values()),"runs":runs,
      "claim_boundary":"Exact replication of the targeted v2 behavior on current boot-profile/runtime source for 25 Stacks strings and two controls; not a blind transfer or broad code capability claim."}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n");print(json.dumps({"report":OUT.relative_to(ROOT).as_posix(),"integrity_checks":checks},indent=2))
    if not report["integrity_pass"]:raise SystemExit("panel integrity gates failed")
if __name__=="__main__":main()
