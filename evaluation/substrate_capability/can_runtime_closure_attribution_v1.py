#!/usr/bin/env python3
"""Source-locked paired attribution for native CAN closure growth."""
from __future__ import annotations
import hashlib, importlib.util, json, os, platform, random, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"runners/dsl/python"))
PROTOCOL=ROOT/"docs/research/engine_substrate/CAN_RUNTIME_CLOSURE_ATTRIBUTION_V1_PREREG_20260929.md"
RUNNER=Path(__file__).resolve();FIXTURE=ROOT/"scripts/substrate_can_structure_envelope.py";SEED=ROOT/"seeds/can_native_reimplementation.json"
LOCK=ROOT/"evaluation/substrate_capability/can_runtime_closure_attribution_v1_lock_20260929.json"
OUT=ROOT/"evaluation/reports/can_runtime_closure_attribution_v1_20260929.json"
SIZES=(128,256);TOPOLOGIES=("path","banded2");MODES=("2state","3state");REPLICATES=2;GRANULARITY=0.25;MAX_STEPS=100000

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(path):return {"path":path.relative_to(ROOT).as_posix(),"bytes":path.stat().st_size,"sha256":sha(path)}
def lock_inputs():
 from substrate_rs import _native
 sources=("runners/dsl/src/scale_audit.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs",
  "runners/dsl/src/can_ops.rs","runners/dsl/src/py.rs","runners/dsl/python/substrate_rs/_native.build.json")
 return {"schema_version":1,"protocol":digest(PROTOCOL),"runner":digest(RUNNER),"fixture":digest(FIXTURE),"seed":digest(SEED),
  "sources":[digest(ROOT/p) for p in sources],"native_extension":{"path":Path(_native.__file__).resolve().relative_to(ROOT).as_posix(),"sha256":sha(Path(_native.__file__).resolve())},
  "sizes":list(SIZES),"topologies":list(TOPOLOGIES),"modes":list(MODES),"replicates":REPLICATES,"granularity":GRANULARITY,"max_steps":MAX_STEPS,
  "git_head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}

def load_fixture():
 spec=importlib.util.spec_from_file_location("can_structure_fixture",FIXTURE);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def build(sr,engine_rules_only,fixture,seed_doc,n,topology,mode,rep):
 draw_seed=20260924+n*1000+rep;fr=random.Random(draw_seed*53+n);pr=random.Random(draw_seed*31+n)
 fields=[fr.uniform(-1.,1.) for _ in range(n)];weights={}
 for a,b in fixture.make_pairs(n,topology):
  w=round(pr.uniform(-1.,1.)/GRANULARITY)*GRANULARITY;weights[a,b]=w;weights[b,a]=w
 inner,concepts=fixture.build_engine(sr,engine_rules_only,seed_doc,n,mode,fields,weights)
 return inner,concepts,fields,weights,draw_seed

def worker(n,topology,mode,rep):
 import substrate_rs as sr
 from substrate.seed_loader import engine_rules_only
 fixture=load_fixture();seed_doc=json.loads(SEED.read_text());started=lock_inputs()
 inner,nodes,fields,weights,draw_seed=build(sr,engine_rules_only,fixture,seed_doc,n,topology,mode,rep)
 t=time.perf_counter_ns();plain_progress=inner.run_rules(MAX_STEPS);plain_ns=time.perf_counter_ns()-t
 plain_states=[float(inner.node(c)["attrs"].get("state",0.)) for c in nodes]
 # A separate graph prevents instrumentation counters or state from leaking between arms.
 audited,anodes,_,_,_=build(sr,engine_rules_only,fixture,seed_doc,n,topology,mode,rep)
 audited.scale_audit_reset();audited.scale_audit_set_enabled(True);audited.scale_audit_set_per_rule_enabled(True)
 t=time.perf_counter_ns();audit_progress=audited.run_rules(MAX_STEPS);audit_ns=time.perf_counter_ns()-t
 counters=dict(audited.scale_audit_snapshot());names={int(row[0]):str(row[1]) for row in audited.rule_access_sets()}
 per_rule=[{"rule_index":idx,"rule_name":names.get(idx,f"rule_{idx}"),"metric":metric,"count":count}
  for idx,metric,count in audited.scale_audit_per_rule_snapshot()]
 audited.scale_audit_set_per_rule_enabled(False);audited.scale_audit_set_enabled(False)
 audit_states=[float(audited.node(c)["attrs"].get("state",0.)) for c in anodes]
 residuals=0
 for a,state in enumerate(audit_states):
  local=fields[a]+sum(weights.get((a,b),0.)*audit_states[b] for b in range(n))
  if fixture.update(mode,local)!=state:residuals+=1
 terminal=audited.run_rules(1);ended=lock_inputs()
 return {"n":n,"topology":topology,"mode":mode,"replicate":rep,"seed":draw_seed,"worker_pid":os.getpid(),
  "directed_edges":len(weights),"plain_progress":plain_progress,"audit_progress":audit_progress,"plain_wall_ns":plain_ns,"audit_wall_ns":audit_ns,
  "progress_and_state_parity":plain_progress==audit_progress and plain_states==audit_states,
  "independent_fixed_point_residuals":residuals,"terminal_probe_progress":terminal,
  "audit_counters":counters,"per_rule_counters":per_rule,"source_lock_start":started,"source_lock_end":ended}

def main():
 if len(sys.argv)==6 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2]),sys.argv[3],sys.argv[4],int(sys.argv[5])),sort_keys=True));return
 if sys.argv[1:]==["--lock"]:
  if LOCK.exists() or OUT.exists():raise SystemExit("refusing to overwrite lock/capture")
  LOCK.write_text(json.dumps(lock_inputs(),indent=2,sort_keys=True)+"\n");print(LOCK.relative_to(ROOT));return
 lock=json.loads(LOCK.read_text())
 if lock_inputs()!=lock:raise SystemExit("source/protocol lock drift")
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("native build stale:\n"+"\n".join(stale))
 env={**os.environ,"PYTHONPATH":f"{ROOT/'runners/dsl/python'}:{ROOT}:{os.environ.get('PYTHONPATH','')}"};rows=[]
 for n in SIZES:
  for topology in TOPOLOGIES:
   for mode in MODES:
    for rep in range(REPLICATES):
     p=subprocess.run([sys.executable,str(RUNNER),"--worker",str(n),topology,mode,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=300)
     row=json.loads(p.stdout);rows.append(row);print(f"n={n} {topology} {mode} rep={rep} progress={row['plain_progress']} candidates={row['audit_counters'].get('cand_enum',0)} audit_ms={row['audit_wall_ns']/1e6:.1f}",flush=True)
 post=lock_inputs()
 checks={"worker_coverage":len(rows)==16 and len({r["worker_pid"] for r in rows})==16,
  "cell_coverage":all(sum(r["n"]==n and r["topology"]==t and r["mode"]==m for r in rows)==REPLICATES for n in SIZES for t in TOPOLOGIES for m in MODES),
  "audit_parity":all(r["progress_and_state_parity"] for r in rows),
  "fixed_point":all(r["independent_fixed_point_residuals"]==0 and r["terminal_probe_progress"]==0 for r in rows),
  "budget_not_reached":all(r["plain_progress"]<MAX_STEPS and r["audit_progress"]<MAX_STEPS for r in rows),
  "counters_present":all(r["audit_counters"] and r["per_rule_counters"] for r in rows),
  "source_stability":lock==post and all(r["source_lock_start"]==lock==r["source_lock_end"] for r in rows)}
 payload={"schema_version":1,"run_id":"can-runtime-closure-attribution-v1-20260929","status":"complete","input_lock":lock,"post_run_input_lock":post,
  "claim_boundary":"one authored CAN rule family on path/banded2 fixtures; audit timing diagnostic only","configuration":{"sizes":SIZES,"topologies":TOPOLOGIES,"modes":MODES,"replicates":REPLICATES},
  "environment":{"python":platform.python_version(),"platform":platform.platform()},"checks":checks,"runs":rows}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":OUT.relative_to(ROOT).as_posix(),"checks":checks},indent=2))
 if not all(checks.values()):raise SystemExit("closure attribution gate failed")

if __name__=="__main__":main()
