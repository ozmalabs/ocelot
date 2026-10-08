#!/usr/bin/env python3
"""Locked native-Term prediction panel over a safe textbook AST sample."""
from __future__ import annotations
import ast, hashlib, json, os, platform, resource, subprocess, sys, time, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_THINKPYTHON_CODE_PREDICTION_PANEL_V1_PREREG_20260927.md"
SELECTOR=ROOT/"scripts/audit_thinkpython_code_prediction_frame_v1.py"
FRAME=ROOT/"evaluation/reports/thinkpython_code_prediction_frame_v1_20260927.json"
ANALYZER=ROOT/"scripts/analyze_substrate_thinkpython_code_prediction_panel_v1.py"
LOCK=ROOT/"evaluation/substrate_capability/thinkpython_code_prediction_panel_v1_lock_20260927.json"
OUT=ROOT/"evaluation/reports/thinkpython_code_prediction_panel_v1_20260927.json"
DATA=ROOT/"data/think_python_2e"; BLOCK=re.compile(r"```(?:python)?\s*\n(.*?)\n```",re.S|re.I)
def sha(b):return hashlib.sha256(b).hexdigest()
def file_sha(p):return sha(Path(p).read_bytes())
def tree(folder,suffixes=None):
    out={}
    for p in sorted(folder.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts and (suffixes is None or p.suffix in suffixes):out[p.relative_to(ROOT).as_posix()]=file_sha(p)
    return out
def inputs():
    from substrate_rs import _native
    return {"protocol_sha256":file_sha(PROTOCOL),"selector_sha256":file_sha(SELECTOR),"frame_sha256":file_sha(FRAME),
        "runner_sha256":file_sha(__file__),"analyzer_sha256":file_sha(ANALYZER),"source_trees":{
        "domains":tree(ROOT/"domains",{".py"}),"substrate":tree(ROOT/"substrate",{".py"}),
        "worlds":tree(ROOT/"worlds",{".py"}),"scripts":tree(ROOT/"scripts",{".py"}),
        "seeds":tree(ROOT/"seeds",{".json"}),"native_python":tree(ROOT/"runners/dsl/python",{".py"}),
        "rust":tree(ROOT/"runners/dsl/src",{".rs"}),"think_python":tree(DATA)},
        "native_extension_sha256":file_sha(Path(_native.__file__).resolve())}
def extract(row):return list(BLOCK.finditer((DATA/row["chapter"]).read_text(encoding="utf-8")))[row["block_index"]].group(1)
def normalize(x):
    typ=type(x).__name__
    if isinstance(x,tuple): value=[normalize(v) for v in x]
    elif isinstance(x,list): value=[normalize(v) for v in x]
    elif isinstance(x,dict): value={str(k):normalize(v) for k,v in sorted(x.items(),key=lambda z:str(z[0]))}
    elif x is None or isinstance(x,(bool,int,float,str)): value=x
    else: raise TypeError("non-primitive native result: "+typ)
    return {"type":typ,"value":value}
def nodeid(n):return int(n.value if hasattr(n,"value") else n)
def ids(adapter,typ):return {nodeid(n) for n in adapter.s.nodes(typ)}
def concern_ids(adapter):
    out=set()
    for n in adapter.s.nodes("NativeReflectiveFacultyReceipt"):
        if adapter.s.node(n)["attrs"].get("cluster")=="reflective_faculty.concern_decode_settlement":out.add(nodeid(n))
    return out
def worker(rep):
    before=inputs()
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains import code_reading
    from substrate_rs import _native
    frame=json.loads(FRAME.read_text())
    a=WorldAdapter(seeds=(),shadow_read=False,deep_ingest=False)
    bs,bc=time.perf_counter_ns(),time.process_time_ns(); boot=load_all_seeds(a)
    boot_wall=time.perf_counter_ns()-bs; boot_cpu=time.process_time_ns()-bc; calls=[]
    for fi,row in enumerate(frame["selected"]):
        src=extract(row); observed=sha(src.encode());
        for ci,args in enumerate(row["input_cases"]):
            cb=concern_ids(a); ob=ids(a,"Observation"); axis=ids(a,"CapabilityAxis")
            n0,e0=a.inner.node_count(),a.inner.edge_count(); ts,cs=time.perf_counter_ns(),time.process_time_ns()
            value=None; error=None
            try:value=normalize(code_reading.predict_output(a,src,row["function"],args))
            except BaseException as exc:error=type(exc).__name__
            wall=time.perf_counter_ns()-ts; cpu=time.process_time_ns()-cs
            observations=[]
            for n in a.s.nodes("Observation"):
                nid=nodeid(n)
                if nid in ob:continue
                attrs=a.s.node(n)["attrs"]; native=_native.NodeID(nid)
                observations.append({"id":nid,"status":attrs.get("status"),
                    "minted_axis_ids":[nodeid(x) for x in a.inner.neighbours(native,"minted")]})
            calls.append({"function_index":fi,"case_index":ci,"sample_id":row["id"],"source_sha256_expected":row["source_sha256"],
                "source_sha256_observed":observed,"args":args,"prediction":value,"error_type":error,
                "abstained":error is not None,"wall_ns":wall,"cpu_ns":cpu,
                "new_receipt_count":len(concern_ids(a)-cb),"new_observations":observations,
                "new_axis_count":len(ids(a,"CapabilityAxis")-axis),"node_delta":a.inner.node_count()-n0,"edge_delta":a.inner.edge_count()-e0})
        del src
    after=inputs()
    return {"replicate":rep,"pid":os.getpid(),"locked_inputs_before":before,"locked_inputs_after":after,"source_stable":before==after,
        "boot":{"loaded":boot.get("loaded"),"total":boot.get("total"),"failed":boot.get("failed",[]),"wall_ns":boot_wall,"cpu_ns":boot_cpu},
        "runtime":{"peak_rss_bytes":int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024),"python":sys.version,"platform":platform.platform()},"calls":calls}
def main():
    if sys.argv[1:]==["--lock"]:print(json.dumps({"locked_inputs":inputs()},indent=2,sort_keys=True));return
    if sys.argv[1:]==["--worker"]:print(json.dumps(worker(int(os.environ["OCEL0_TP_PRED_REP"])),sort_keys=True));return
    lock=inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs")!=lock:raise SystemExit("missing or stale Think Python prediction lock")
    env={**os.environ,"PYTHONPATH":f"{ROOT}:{ROOT/'runners/dsl/python'}","OZMA_SEED_PERSIST_DISABLED":"1"}; runs=[]
    for rep in (0,1):
        p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker"],cwd=ROOT,env={**env,"OCEL0_TP_PRED_REP":str(rep)},text=True,capture_output=True,timeout=1800)
        try:r=json.loads(p.stdout)
        except Exception:r={"replicate":rep,"worker_error":p.stderr or p.stdout}
        r.update({"worker_returncode":p.returncode,"worker_stderr":p.stderr});runs.append(r);print(f"completed=worker{rep} rc={p.returncode}",file=sys.stderr,flush=True)
    post=inputs(); checks={"two_fresh_workers":len(runs)==2 and len({r.get("pid") for r in runs})==2,
        "parent_lock_stable":post==lock,"worker_lock_stable":all(r.get("source_stable") and r.get("locked_inputs_before")==lock==r.get("locked_inputs_after") for r in runs),
        "expected_call_count":all(len(r.get("calls",[]))==9 for r in runs),"workers_succeeded":all(r.get("worker_returncode")==0 and r.get("boot",{}).get("loaded",0)>0 for r in runs)}
    report={"schema_version":1,"run_id":"thinkpython-code-prediction-panel-v1-20260927","locked_inputs":lock,"post_run_inputs":post,
        "integrity_checks":checks,"integrity_pass":all(checks.values()),"runs":runs,
        "claim_boundary":"Typed native-Term prediction versus a separately implemented safe AST oracle over nine fixed inputs for four textbook functions; no broad code-capability estimate."}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"report":OUT.relative_to(ROOT).as_posix(),"integrity_checks":checks},indent=2))
    if not report["integrity_pass"]:raise SystemExit("panel integrity gates failed")
if __name__=="__main__":main()
