#!/usr/bin/env python3
"""Source-locked ranker probe for unrelated-family outcome records."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
RUNNER=Path(__file__).resolve()
PREREG=ROOT/"docs/research/engine_substrate/THOUGHTEXPERIMENT_CROSS_FAMILY_RANKER_NULL_TRANSFER_V1_PREREG_20261002.md"
REC_RAW=ROOT/"evaluation/reports/thoughtexperiment_recurrence_candidate_admission_v1_raw_20261002.json"
REC_LOCK=ROOT/"evaluation/substrate_capability/thoughtexperiment_recurrence_candidate_admission_v1_lock_20261002.json"
TASK_RAW=ROOT/"evaluation/reports/thoughtexperiment_control_kind_classification_repair_v1_raw_20261002.json"
TASK_LOCK=ROOT/"evaluation/substrate_capability/thoughtexperiment_control_kind_classification_repair_v1_lock_20261002.json"
LOCK=ROOT/"evaluation/substrate_capability/thoughtexperiment_cross_family_ranker_null_transfer_v1_lock_20261002.json"
RAW=ROOT/"evaluation/reports/thoughtexperiment_cross_family_ranker_null_transfer_v1_raw_20261002.json"
TARGET="classify_kind_family"
SOURCES=("domains/reflective_faculty.py","domains/self_correct_dispatch.py","domains/self_correction.py","domains/edit_ops.py","domains/engine_provenance.py","substrate/boot_core.py","substrate/seed_loader.py","seeds/control_kinds.json","seeds/relation_vocabulary.json","seeds/composer_dispatch.json","seeds/autonomy.json","runners/dsl/src/py.rs","runners/dsl/src/substrate.rs","runners/dsl/src/graph.rs","runners/dsl/src/graph_rules.rs","runners/dsl/src/term.rs","runners/dsl/src/persist.rs","runners/dsl/src/grammar.rs","runners/dsl/src/sym.rs","runners/dsl/src/lib.rs","runners/dsl/Cargo.toml","runners/dsl/Cargo.lock","runners/dsl/python/substrate_rs/__init__.py")

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen()->dict:
 from substrate_rs import _native
 rows={p:sha(ROOT/p) for p in SOURCES}
 rows.update({str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,PREREG,REC_RAW,REC_LOCK,TASK_RAW,TASK_LOCK)})
 rows["loaded_native_binary"]=sha(Path(_native.__file__).resolve())
 return rows
def digest(c:dict)->str:
 rules={}
 for name,rule in sorted((c.get("rules") or {}).items()):
  value=json.loads(json.dumps(rule,sort_keys=True)) if rule else None
  if isinstance(value,dict):value.pop("name",None)
  rules[name]=value
 return "sha256:"+hashlib.sha256(json.dumps(rules,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def worker(index:int)->dict:
 from substrate.boot_core import boot_core
 from substrate.seed_loader import manifest_for
 import domains.reflective_faculty as rf
 from domains.edit_ops import apply_flip_comparison
 from domains.self_correction import _default_candidates
 from domains.self_correct_dispatch import rank_candidates
 before=frozen();s,root=boot_core(seeds=());native=s._inner
 for seed in ("relation_vocabulary","composer_dispatch","autonomy","control_kinds"):
  native.load_seed_manifest(manifest_for(seed),root)
 class Agent:
  def __init__(self,sub,node):self.s=sub;self.inner=sub._inner;self.agent=node
 agent=Agent(s,root)
 inducted=rf.induce_concern(agent,[["correct","DIVERGENCE","by","CANDIDATE"]],name_hint=f"nullrank_{index}")
 grounded=rf.ground_concern(agent,[inducted["capability_key"]])
 programs=[s.node(n)["attrs"].get("name") for n in s.nodes("Program") if str(s.node(n)["attrs"].get("name","")).startswith("self_correct_rank_")]
 if not grounded.get("grounded") or not programs:raise RuntimeError("graph-authored ranker did not compose")
 rows=native.export_rules();idx=next(i for i,r in enumerate(rows) if r.get("name")==TARGET and r.get("active",True))
 bad=apply_flip_comparison(rows[idx],TARGET);native.remove_rule(idx);native.add_rule(bad)
 candidates=_default_candidates(native,TARGET)
 candidates=[c for c in candidates if c.get("rules",{}).get(TARGET) is not None]
 descriptors=[{"label":c["label"],"digest":digest(c),"outcome_class":c.get("outcome_class","")} for c in candidates]
 started=time.perf_counter_ns();cold=rank_candidates(agent,native,[dict(c) for c in candidates]);cold_ns=time.perf_counter_ns()-started
 cold_order=[c["label"] for c in cold]
 source=json.loads(REC_RAW.read_text())["workers"][index]["candidate_outcomes"]
 prior=[]
 for row in source:
  prior.append({"target_rule":"mrl_offer_due_once","candidate_label":row["label"],
    "outcome_class":row.get("outcome_class","") or "",
    "task_utility":float(row["training"]["pass"]),
    "candidate_digest":row["digest"],"source":"recurrence_candidate_admission_training"})
 for row in prior:s.add_node("CorrectionOutcome",row)
 started=time.perf_counter_ns();experienced=rank_candidates(agent,native,[dict(c) for c in candidates]);experience_ns=time.perf_counter_ns()-started
 exp_order=[c["label"] for c in experienced]
 traces={c["label"]:c.get("_self_correction_rank_trace") for c in experienced}
 after=frozen()
 return {"worker":index,"source_before":before,"source_after":after,"source_stable":before==after,
   "composer":{"grounded":grounded.get("grounded"),"served_by":grounded.get("served_by"),"programs":programs},
   "descriptors":descriptors,"prior_records":prior,"cold_order":cold_order,"experience_order":exp_order,
   "experience_traces":traces,"timing_ns":{"cold_rank":cold_ns,"experience_rank":experience_ns}}

def main()->int:
 if sys.argv[1:2]==["--worker"]:
  print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(",",":")));return 0
 if sys.argv[1:]==["--lock"]:
  if LOCK.exists() or RAW.exists():raise SystemExit("refusing to overwrite existing lock/capture")
  from domains.engine_provenance import build_is_stale,rust_source_fingerprint
  stale=build_is_stale(str(ROOT))
  if stale:raise SystemExit("stale native engine: "+"; ".join(stale))
  LOCK.write_text(json.dumps({"schema":"CrossFamilyRankerNullTransferV1Lock","sources":frozen(),
   "semantic_engine":rust_source_fingerprint(str(ROOT)),"workers":3,"source_family":"recurrence_offer_idempotence",
   "evaluation_family":"control_kind_classification","outcome_origin":"locked recurrence train split only"},indent=2,sort_keys=True)+"\n")
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
 RAW.write_text(json.dumps({"schema":"CrossFamilyRankerNullTransferV1Capture","captured_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
  "host":{"platform":platform.platform(),"machine":platform.machine(),"python":sys.version.split()[0]},"lock":lock,
  "source_before":before,"source_after":after,"semantic_engine":rust_source_fingerprint(str(ROOT)),"workers":workers},indent=2,sort_keys=True)+"\n")
 print(json.dumps({"workers":len(workers),"orders_equal":all(w["cold_order"]==w["experience_order"] for w in workers),
  "raw":str(RAW.relative_to(ROOT))},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
