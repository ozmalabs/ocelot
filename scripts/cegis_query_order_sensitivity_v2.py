#!/usr/bin/env python3
"""Source-locked paired probe of the CEGIS first-disagreement input-order policy."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, random, subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "runners/dsl/python")]
from domains.engine_provenance import engine_preamble, engine_provenance, rust_source_fingerprint
engine_preamble()
from substrate_rs import _native
import domains.cegis_faculty as faculty
from domains.cegis_faculty import cegis_synthesize
from domains.generator import synthesize as native_synthesize
from cegis_faculty_on_sum_of_n import make_oracle, describe, family, KNOWNS, OPS
STEM = "cegis_query_order_sensitivity_v2_20260930"
LOCK = ROOT / f"evaluation/substrate_capability/{STEM}_lock.json"
RAW = ROOT / f"evaluation/reports/{STEM}_raw.json"
RESULTS = ROOT / f"docs/research/engine_substrate/{STEM.upper()}_RESULTS.md"
PROTOCOL = ROOT / f"docs/research/engine_substrate/{STEM.upper()}_PREREG_20260930.md"
REPS, SEED = 5, 20260930
FIXED_CONSTS = (-1, 0, 1, 2, 3, 6, 10, 15, 21, 28, 36, 45, 55, 66, 78)
SOURCES = ["scripts/cegis_query_order_sensitivity_v2.py", "scripts/analyze_cegis_query_order_sensitivity_v2.py", "scripts/cegis_faculty_on_sum_of_n.py", "domains/cegis_faculty.py", "domains/generator.py", "domains/compute_grounding.py", "domains/reason.py", "domains/engine_provenance.py", "docs/research/engine_substrate/CEGIS_QUERY_ORDER_SENSITIVITY_V2_PREREG_20260930.md"]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lock_payload():
    ext=Path(_native.__file__).resolve()
    return {"schema_version":1,"source_sha256":{x:sha(ROOT/x) for x in SOURCES},"native_extension":{"path":str(ext),"sha256":sha(ext)},"native_build_manifest_sha256":sha(ROOT/"runners/dsl/python/substrate_rs/_native.build.json"),"engine_provenance":engine_provenance(),"rust_source_fingerprint":rust_source_fingerprint(str(ROOT)),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"design":{"task":"triangular(n)=sum(0..n)","knowns":[list(x) for x in KNOWNS],"candidate_inputs":[n for n in range(2,13)],"holdout":[17,23,50,99,100,250],"arms":["fixed_order","seeded_permutation"],"repetitions":REPS,"schedule_seed":SEED,"max_size":9,"timeout_s":120,"max_rounds":16,"fixed_literal_set":list(FIXED_CONSTS),"literal_control":"override each native synthesis call with this shared set, independent of observed outputs"}}
def worker(arm,rep):
    s=_native.Substrate(); oracle0=make_oracle(s); calls=[]
    synth_calls=[]
    def fixed_synthesize(*args,**kwargs):
        kwargs["consts"]=FIXED_CONSTS
        out=native_synthesize(*args,**kwargs)
        synth_calls.append({"explored":out.get("explored"),"elapsed_s":out.get("elapsed_s"),"fits":out.get("fits"),"halt_reason":out.get("halt_reason")})
        return out
    faculty.synthesize=fixed_synthesize
    def oracle(n): calls.append(n); return oracle0(n)
    base=family()
    if arm=="seeded_permutation": random.Random(SEED+rep).shuffle(base)
    elif arm!="fixed_order": raise ValueError(arm)
    order=[n for _,n in base]
    t0=time.perf_counter(); cpu0=time.process_time()
    result=cegis_synthesize(s,describe,oracle,lambda: list(base),KNOWNS,ops=OPS,max_size=9,timeout_s=120,max_rounds=16)
    wall=time.perf_counter()-t0; cpu=time.process_time()-cpu0
    held=[]
    for n in (17,23,50,99,100,250):
        got=result.evaluate(describe,n,s); expected=oracle0(n)
        held.append({"n":n,"predicted":got,"expected":expected,"exact":abs(float(got)-float(expected))<1e-9})
    selected=[r.counterexample for r in result.rounds if r.counterexample is not None]
    family_calls=[n for n in calls if n in set(order)]
    return {"arm":arm,"replicate":rep,"pid":os.getpid(),"fixed_literal_set":list(FIXED_CONSTS),"synthesis_calls":synth_calls,"candidate_order":order,"selected_queries":selected,"oracle_calls":calls,"candidate_family_oracle_calls":family_calls,"result":{"step0_term":result.step0_term_str,"final_term":result.final_term_str,"final_size":result.final_size,"fits":result.fits,"converged":result.converged,"rows":[name for name,_ in result.rows],"rounds":[{"round":r.rnd,"term":r.term_str,"counterexample":r.counterexample} for r in result.rounds],"discriminated":result.discriminated},"heldout":held,"wall_s":wall,"cpu_s":cpu}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--lock",action="store_true"); ap.add_argument("--worker",nargs=2); a=ap.parse_args()
    if a.worker: print(json.dumps(worker(a.worker[0],int(a.worker[1])),sort_keys=True)); return
    lock=lock_payload()
    if a.lock: print(json.dumps(lock,indent=2,sort_keys=True)); return
    if not LOCK.exists() or json.loads(LOCK.read_text())!=lock: raise SystemExit("missing/stale lock")
    if RAW.exists(): raise SystemExit(f"refusing to overwrite {RAW}")
    sched=[(arm,r) for r in range(1,REPS+1) for arm in ("fixed_order","seeded_permutation")]; random.Random(SEED).shuffle(sched)
    env=dict(os.environ); env["PYTHONPATH"]=f"{ROOT}:{ROOT/'scripts'}:{ROOT/'runners/dsl/python'}:{env.get('PYTHONPATH','')}"
    rows=[]; start=time.perf_counter()
    for i,(arm,rep) in enumerate(sched,1):
        p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",arm,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=300)
        if p.returncode: row={"arm":arm,"replicate":rep,"worker_error":p.stderr[-4000:]}
        else:
            try: row=json.loads(p.stdout.strip().splitlines()[-1]); row["worker_error"]=None
            except Exception as e: row={"arm":arm,"replicate":rep,"worker_error":f"parse: {type(e).__name__}: {e}"}
        rows.append(row); print(f"{i}/{len(sched)} {arm} rep={rep} error={row.get('worker_error')}",flush=True)
    raw={"protocol":STEM,"lock":lock,"schedule":[list(x) for x in sched],"workers":rows,"worker_failures":[r for r in rows if r.get("worker_error")],"elapsed_s":time.perf_counter()-start,"environment":{"python":sys.version,"platform":platform.platform()}}
    RAW.write_text(json.dumps(raw,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"raw":str(RAW),"workers":len(rows),"failures":len(raw['worker_failures']),"elapsed_s":raw['elapsed_s']}))
if __name__=="__main__": main()
