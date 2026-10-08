#!/usr/bin/env python3
"""Source-locked producer attribution probe for deferred framebuffer samples."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"tests")]
OVERRIDE=os.environ.get("OCELot_NATIVE_IMPORT_ROOT")
if OVERRIDE: sys.path.insert(0,OVERRIDE)
RUNNER=Path(__file__).resolve()
PREREG=ROOT/"docs/research/engine_substrate/THOUGHTEXPERIMENT_DEFERRED_FB_SAMPLE_ATTRIBUTION_V1_PREREG_20261002.md"
ANALYZER=ROOT/"evaluation/substrate_capability/analyze_thoughtexperiment_deferred_fb_sample_attribution_v1.py"
LOCK=ROOT/"evaluation/substrate_capability/thoughtexperiment_deferred_fb_sample_attribution_v1_lock_20261002.json"
CAPTURE=ROOT/"evaluation/reports/thoughtexperiment_deferred_fb_sample_attribution_v1_20261002.json"
SOURCES=("runners/dsl/src/graph.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/src/py.rs","tests/test_rule_driven_look.py","tests/fb_writer.py","seeds/region_grouping.json")
WORKERS=3
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 files=(RUNNER,PREREG,ANALYZER,*(ROOT/p for p in SOURCES)); b=Path(_native.__file__).resolve()
 return {"files":{str(p.relative_to(ROOT)):sha(p) for p in files},"native_binary":{"path":str(b),"sha256":sha(b)}}
def make_case(name):
 import test_rule_driven_look as f
 from substrate_rs import _native
 wa=f._fresh(); game=f._mk_game(wa)
 fb_id=wa.inner.fb_attach(name)
 f._install_look_rule(wa,fb_id,game,2,2)
 return wa,int(game.value)
def summ(r): return {k:r.get(k) for k in ("status","progress_steps","passes_completed")}
def edges(r): return {tuple((int(e[0]),str(e[1]),int(e[2]))) for e in r["affected_edges"]}
def execute(name):
 import test_rule_driven_look as f
 from fb_writer import FbWriter
 writer=FbWriter(name,8,8)
 try:
  writer.write_frame(writer.solid_frame((30,30,30),rect=(1,1,4,4),rect_bgr=(200,40,90)))
  a,game_id=make_case(name); traced=a.inner.run_rules_delta_report(1000,False)
  b,_=make_case(name); exact=b.inner.run_rules_snapshot_delta_report(1000,False)
  c,_=make_case(name); plain=c.inner.run_rules_report(1000,False)
  ev=traced["rule_write_events"]; en={int(n) for e in ev for n in e["node_ids"]}
  ee={tuple((int(x[0]),str(x[1]),int(x[2]))) for e in ev for x in e["edges"]}
  exn=set(map(int,exact["affected_nodes"])); exe=edges(exact)
  deferred=[e for e in ev if e["deferred"]]; origin=[e for e in deferred if e["rule_name"]=="look_when_frame_advances"]
  return {"plain":summ(plain),"traced":summ(traced),"exact":summ(exact),"events":ev,"deferred_events":deferred,"origin_events":origin,
   "game_id":game_id,"region_count":len(a.inner.nodes("Region")),"world_instance_count":len(a.inner.nodes("WorldInstance")),
   "event_covers_exact_nodes":exn<=en,"event_covers_exact_edges":exe<=ee,
   "aggregate_covers_event_nodes":en<=set(map(int,traced["affected_nodes"])),"aggregate_covers_event_edges":ee<=edges(traced),
   "dropped_events":int(traced["rule_write_events_dropped"])}
 finally: writer.close()
def worker(i):
 expected=json.loads(LOCK.read_text())["sources"]; before=frozen()
 if before!=expected: raise RuntimeError("source/native fingerprint differs from lock")
 name=f"/ocelot_deferred_fb_attr_{os.getpid()}_{i}"
 result=execute(name); after=frozen()
 return {"worker_index":i,"pid":os.getpid(),"sources_before":before,"sources_after":after,"source_stable":before==after,"result":result}
def main():
 if len(sys.argv)==3 and sys.argv[1]=="--worker": print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(",",":"))); return 0
 if sys.argv[1:]==["--lock"]:
  if LOCK.exists() or CAPTURE.exists(): raise SystemExit("refusing to overwrite lock or capture")
  LOCK.write_text(json.dumps({"schema":"DeferredFbSampleAttributionV1Lock","sources":frozen(),"workers":WORKERS},indent=2,sort_keys=True)+"\n"); print(LOCK.relative_to(ROOT)); return 0
 if sys.argv[1:]!=["--run"]: raise SystemExit("usage: --lock or --run")
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock["sources"]: raise SystemExit("source/native drift from lock")
 env=dict(os.environ); env["PYTHONPATH"]=os.pathsep.join(filter(None,(OVERRIDE,str(ROOT/"runners/dsl/python"),str(ROOT/"tests"),str(ROOT))))
 ws=[]
 for i in range(WORKERS):
  p=subprocess.run([sys.executable,str(RUNNER),"--worker",str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
  if p.returncode: raise RuntimeError(f"worker {i} failed: {p.stderr[-2500:]}")
  ws.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=lock["sources"]: raise SystemExit("source/native drift during capture")
 CAPTURE.write_text(json.dumps({"schema":"DeferredFbSampleAttributionV1Results","lock_sha256":sha(LOCK),"captured_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"host":platform.platform(),"workers":ws},indent=2,sort_keys=True)+"\n"); print(CAPTURE.relative_to(ROOT)); return 0
if __name__=="__main__": raise SystemExit(main())
