#!/usr/bin/env python3
"""Source-locked candidate-admission audit for control-kind classification repair."""
from __future__ import annotations
import hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
RUNNER=Path(__file__).resolve()
PREREG=ROOT/"docs/research/engine_substrate/THOUGHTEXPERIMENT_CONTROL_KIND_CLASSIFICATION_REPAIR_V1_PREREG_20261002.md"
TASK_SEED=ROOT/"seeds/control_kinds.json"
TARGET="classify_kind_family"
TRAIN=[{"name":"rotary dial","expected":"discrete_select"},
       {"name":"trackpad mouse","expected":"relative_pointer"}]
HELDOUT=[{"name":"steering wheel","expected":"continuous_rotation"},
         {"name":"trigger button","expected":"discrete_act"}]
LOCK=ROOT/"evaluation/substrate_capability/thoughtexperiment_control_kind_classification_repair_v1_lock_20261002.json"
RAW=ROOT/"evaluation/reports/thoughtexperiment_control_kind_classification_repair_v1_raw_20261002.json"
SOURCES=(
 "domains/self_correction.py","domains/edit_ops.py","domains/engine_provenance.py",
 "substrate/boot_core.py","substrate/seed_loader.py","runners/dsl/src/py.rs",
 "runners/dsl/src/substrate.rs","runners/dsl/src/graph.rs","runners/dsl/src/graph_rules.rs",
 "runners/dsl/src/term.rs","runners/dsl/src/persist.rs","runners/dsl/src/grammar.rs",
 "runners/dsl/src/sym.rs","runners/dsl/src/lib.rs","runners/dsl/Cargo.toml",
 "runners/dsl/Cargo.lock","runners/dsl/python/substrate_rs/__init__.py","seeds/control_kinds.json",
)

def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def frozen()->dict:
 from substrate_rs import _native
 rows={p:sha(ROOT/p) for p in SOURCES}
 rows.update({str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,PREREG)})
 rows["loaded_native_binary"]=sha(Path(_native.__file__).resolve())
 return rows

def canon_digest(candidate:dict)->str:
 bundle={}
 for target,rule in sorted((candidate.get("rules") or {}).items()):
  row=json.loads(json.dumps(rule,sort_keys=True)) if rule is not None else None
  if isinstance(row,dict):row.pop("name",None)
  bundle[target]=row
 raw=json.dumps(bundle,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
 return "sha256:"+hashlib.sha256(raw).hexdigest()

def rule_setup(variant:dict|None):
 from substrate.boot_core import boot_core
 from substrate.seed_loader import manifest_for
 from domains.edit_ops import apply_flip_comparison
 from domains.self_correction import _default_candidates
 s,root=boot_core(seeds=());n=s._inner
 n.load_seed_manifest(manifest_for("control_kinds"),root)
 rows=n.export_rules();idx=next(i for i,r in enumerate(rows) if r.get("name")==TARGET and r.get("active",True))
 source=rows[idx];fault=apply_flip_comparison(source,TARGET)
 if fault is None:raise RuntimeError("target has no effect comparison to fault")
 n.remove_rule(idx);n.add_rule(fault)
 if variant is not None:
  active=[i for i,r in enumerate(n.export_rules()) if r.get("name")==TARGET and r.get("active",True)]
  if not active or not all(n.remove_rule(i) for i in reversed(active)):raise RuntimeError("could not replace fault")
  n.add_rule(variant)
 candidates=_default_candidates(n,TARGET) if variant is None else []
 return s,root,n,source,fault,candidates

def score_case(variant:dict|None,case:dict)->dict:
 s,root,n,source,fault,_=rule_setup(variant)
 registry=next((node for node in s.nodes("SignalRegistry")
                if s.node(node)["attrs"].get("name")=="control_family_signals"),None)
 if registry is None:raise RuntimeError("signal registry missing")
 kind=s.add_node("ControlKind",{"name":case["name"],"name_lc":case["name"].lower(),"family_set":0.0})
 n.add_edge_unchecked(registry,"has_kind",kind)
 work=int(n.run_rules(1000));attrs=s.node(kind)["attrs"]
 return {"name":case["name"],"expected":case["expected"],
         "actual":attrs.get("effect_family"),"family_set":attrs.get("family_set"),
         "closure_work":work,"pass":attrs.get("effect_family")==case["expected"] and attrs.get("family_set")==1.0}

def worker(index:int)->dict:
 before=frozen();s,root,n,source,fault,candidates=rule_setup(None)
 usable=[c for c in candidates if c.get("rules",{}).get(TARGET) is not None]
 desc=[{"label":c["label"],"digest":canon_digest(c),"targets":sorted(c.get("rules",{}))} for c in usable]
 candidate_rows=[]
 for c,d in zip(usable,desc):
  variant=c["rules"][TARGET]
  candidate_rows.append({**d,"training":[score_case(variant,x) for x in TRAIN],
                         "heldout":[score_case(variant,x) for x in HELDOUT]})
 controls={"source":[score_case(source,x) for x in (TRAIN+HELDOUT)],
           "fault":[score_case(fault,x) for x in (TRAIN+HELDOUT)]}
 after=frozen()
 return {"worker":index,"source_before":before,"source_after":after,"source_stable":before==after,
         "candidate_descriptors":desc,"candidate_outcomes":candidate_rows,"controls":controls}

def main()->int:
 if sys.argv[1:2]==["--worker"]:
  print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(",",":")));return 0
 if sys.argv[1:]==["--lock"]:
  if LOCK.exists() or RAW.exists():raise SystemExit("refusing to overwrite lock or capture")
  from domains.engine_provenance import build_is_stale,rust_source_fingerprint
  stale=build_is_stale(str(ROOT))
  if stale:raise SystemExit("stale native engine: "+"; ".join(stale))
  LOCK.write_text(json.dumps({"schema":"ControlKindClassificationRepairV1Lock","sources":frozen(),
      "semantic_engine":rust_source_fingerprint(str(ROOT)),"workers":3,"training":TRAIN,"heldout":HELDOUT},indent=2,sort_keys=True)+"\n")
  print(LOCK.relative_to(ROOT));return 0
 if not LOCK.exists() or RAW.exists():raise SystemExit("missing lock or capture already exists")
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("stale native engine: "+"; ".join(stale))
 before=frozen();lock=json.loads(LOCK.read_text())
 if before!=lock["sources"]:raise SystemExit("source drift from lock")
 env={**os.environ,"PYTHONPATH":f"{ROOT/'runners/dsl/python'}:{ROOT}"};workers=[]
 for i in range(3):
  p=subprocess.run([sys.executable,str(RUNNER),"--worker",str(i)],cwd=ROOT,env=env,text=True,capture_output=True)
  if p.returncode:raise RuntimeError(f"worker {i}: {p.stderr[-3000:]}")
  workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
 after=frozen()
 if before!=after:raise SystemExit("source drift during capture")
 capture={"schema":"ControlKindClassificationRepairV1Capture","captured_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
  "host":{"platform":platform.platform(),"machine":platform.machine(),"python":sys.version.split()[0]},
  "lock":lock,"source_before":before,"source_after":after,"semantic_engine":rust_source_fingerprint(str(ROOT)),"workers":workers}
 RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"workers":len(workers),"candidates":len(workers[0]["candidate_descriptors"]),
  "heldout_passes":[x["label"] for x in workers[0]["candidate_outcomes"] if all(y["pass"] for y in x["heldout"])],
  "raw":str(RAW.relative_to(ROOT))},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
