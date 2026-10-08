#!/usr/bin/env python3
"""Two-worker source-locked code prediction panel over bounded AST cases."""
from __future__ import annotations
import ast,hashlib,json,os,platform,resource,subprocess,sys,time,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_THINKPYTHON_CODE_PREDICTION_PANEL_V2_1_PREREG_20260927.md"
SELECTOR=ROOT/"scripts/audit_thinkpython_code_prediction_frame_v2_1.py"
FRAME=ROOT/"evaluation/reports/thinkpython_code_prediction_frame_v2_1_20260927.json"
ANALYZER=ROOT/"scripts/analyze_substrate_thinkpython_code_prediction_panel_v2_1.py"
LOCK=ROOT/"evaluation/substrate_capability/thinkpython_code_prediction_panel_v2_1_lock_20260927.json"
OUT=ROOT/"evaluation/reports/thinkpython_code_prediction_panel_v2_1_20260927.json"
DATA=ROOT/"data/think_python_2e";BLOCK=re.compile(r"```(?:python)?\s*\n(.*?)\n```",re.S|re.I)
def sha(b):return hashlib.sha256(b).hexdigest()
def file_sha(p):return sha(Path(p).read_bytes())
def tree(folder,suffixes=None):
 out={}
 for p in sorted(folder.rglob("*")):
  if p.is_file() and "__pycache__" not in p.parts and (suffixes is None or p.suffix in suffixes):out[p.relative_to(ROOT).as_posix()]=file_sha(p)
 return out
def inputs():
 from substrate_rs import _native
 return {"protocol_sha256":file_sha(PROTOCOL),"selector_sha256":file_sha(SELECTOR),"frame_sha256":file_sha(FRAME),"runner_sha256":file_sha(__file__),"analyzer_sha256":file_sha(ANALYZER),
  "source_trees":{"domains":tree(ROOT/"domains",{".py"}),"substrate":tree(ROOT/"substrate",{".py"}),"worlds":tree(ROOT/"worlds",{".py"}),"scripts":tree(ROOT/"scripts",{".py"}),"seeds":tree(ROOT/"seeds",{".json"}),"native_python":tree(ROOT/"runners/dsl/python",{".py"}),"rust":tree(ROOT/"runners/dsl/src",{".rs"}),"think_python":tree(DATA)},"native_extension_sha256":file_sha(Path(_native.__file__).resolve())}
def extract(row):return list(BLOCK.finditer((DATA/row["chapter"]).read_text(encoding="utf-8")))[row["block_index"]].group(1)
def decode_input(x):
 if isinstance(x,dict) and set(x)=={"$tuple"}:return tuple(decode_input(v) for v in x["$tuple"])
 if isinstance(x,dict):return {k:decode_input(v) for k,v in x.items()}
 if isinstance(x,list):return [decode_input(v) for v in x]
 return x
def norm(x):
 t=type(x).__name__
 if isinstance(x,tuple):v=[norm(y) for y in x]
 elif isinstance(x,list):v=[norm(y) for y in x]
 elif isinstance(x,dict):v={str(k):norm(y) for k,y in sorted(x.items(),key=lambda z:str(z[0]))}
 elif x is None or isinstance(x,(bool,int,float,str)):v=x
 else:raise TypeError("nonprimitive output type "+t)
 return {"type":t,"value":v}
def nodeid(n):return int(n.value if hasattr(n,"value") else n)
def ids(a,typ):return {nodeid(n) for n in a.s.nodes(typ)}
def receipts(a):
 out=set()
 for n in a.s.nodes("NativeReflectiveFacultyReceipt"):
  if a.s.node(n)["attrs"].get("cluster")=="reflective_faculty.concern_decode_settlement":out.add(nodeid(n))
 return out
def worker(rep):
 before=inputs()
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 from domains import code_reading
 from substrate_rs import _native
 frame=json.loads(FRAME.read_text());a=WorldAdapter(seeds=(),shadow_read=False,deep_ingest=False)
 bs,bc=time.perf_counter_ns(),time.process_time_ns();boot=load_all_seeds(a);bootw=time.perf_counter_ns()-bs;bootc=time.process_time_ns()-bc
 calls=[]
 for fi,row in enumerate(frame["selected"]):
  src=extract(row); observed=sha(src.encode())
  for ci,args in enumerate(row["input_cases"]):
   rb=receipts(a);ob=ids(a,"Observation");ax=ids(a,"CapabilityAxis");n0,e0=a.inner.node_count(),a.inner.edge_count()
   ts,cs=time.perf_counter_ns(),time.process_time_ns();prediction=None;err=None
   try:prediction=norm(code_reading.predict_output(a,src,row["function"],decode_input(args)))
   except BaseException as exc:err=type(exc).__name__
   wall=time.perf_counter_ns()-ts;cpu=time.process_time_ns()-cs;newobs=[]
   for node in a.s.nodes("Observation"):
    nid=nodeid(node)
    if nid not in ob:
     attrs=a.s.node(node)["attrs"];newobs.append({"id":nid,"status":attrs.get("status"),"minted_axis_ids":[nodeid(x) for x in a.inner.neighbours(_native.NodeID(nid),"minted")]})
   calls.append({"function_index":fi,"case_index":ci,"sample_id":row["id"],"source_sha256_expected":row["source_sha256"],"source_sha256_observed":observed,"args":args,
    "prediction":prediction,"error_type":err,"abstained":err is not None,"wall_ns":wall,"cpu_ns":cpu,"receipt_delta":len(receipts(a)-rb),"new_observations":newobs,"new_axis_count":len(ids(a,"CapabilityAxis")-ax),"node_delta":a.inner.node_count()-n0,"edge_delta":a.inner.edge_count()-e0})
  del src
 after=inputs()
 return {"replicate":rep,"pid":os.getpid(),"locked_inputs_before":before,"locked_inputs_after":after,"source_stable":before==after,
  "boot":{"loaded":boot.get("loaded"),"total":boot.get("total"),"failed":boot.get("failed",[]),"wall_ns":bootw,"cpu_ns":bootc},"runtime":{"peak_rss_bytes":int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),"python":sys.version,"platform":platform.platform()},"calls":calls}
def main():
 if sys.argv[1:]==["--lock"]:print(json.dumps({"locked_inputs":inputs()},indent=2,sort_keys=True));return
 if sys.argv[1:]==["--worker"]:print(json.dumps(worker(int(os.environ["OCEL0_TP_PRED_V2_1_REP"])),sort_keys=True));return
 lock=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=lock:raise SystemExit("missing or stale Think Python prediction v2.1 lock")
 env={**os.environ,"PYTHONPATH":f"{ROOT}:{ROOT/'runners/dsl/python'}","OZMA_SEED_PERSIST_DISABLED":"1"};runs=[]
 for rep in (0,1):
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker"],cwd=ROOT,env={**env,"OCEL0_TP_PRED_V2_1_REP":str(rep)},text=True,capture_output=True,timeout=1800)
  try:r=json.loads(p.stdout)
  except Exception:r={"replicate":rep,"worker_error":p.stderr or p.stdout}
  r.update({"worker_returncode":p.returncode,"worker_stderr":p.stderr});runs.append(r);print(f"completed=worker{rep} rc={p.returncode}",file=sys.stderr,flush=True)
 post=inputs();checks={"two_fresh_workers":len(runs)==2 and len({r.get("pid") for r in runs})==2,"parent_lock_stable":post==lock,
  "worker_lock_stable":all(r.get("source_stable") and r.get("locked_inputs_before")==lock==r.get("locked_inputs_after") for r in runs),
  "all_selected_calls":all(len(r.get("calls",[]))==36 for r in runs),"workers_succeeded":all(r.get("worker_returncode")==0 and r.get("boot",{}).get("loaded",0)>0 for r in runs)}
 report={"schema_version":2,"run_id":"thinkpython-code-prediction-panel-v2.1-20260927","locked_inputs":lock,"post_run_inputs":post,"integrity_checks":checks,"integrity_pass":all(checks.values()),"runs":runs,
  "claim_boundary":"Typed native-Term prediction versus independent bounded AST interpretation on the 36 calls in a statically selected Think Python subset; no broad general-code capability estimate."}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"report":OUT.relative_to(ROOT).as_posix(),"integrity_checks":checks},indent=2))
 if not report["integrity_pass"]:raise SystemExit("panel integrity gates failed")
if __name__=="__main__":main()
