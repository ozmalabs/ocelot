#!/usr/bin/env python3
"""Two-stage source-locked ranker probe with order-before-oracle scoring."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
RUNNER=Path(__file__).resolve()
PREREG=ROOT/"docs/research/engine_substrate/THOUGHTEXPERIMENT_CROSS_FAMILY_RANKER_NULL_TRANSFER_V1_1_AMENDMENT_20261002.md"
REC_RAW=ROOT/"evaluation/reports/thoughtexperiment_recurrence_candidate_admission_v1_raw_20261002.json"
REC_LOCK=ROOT/"evaluation/substrate_capability/thoughtexperiment_recurrence_candidate_admission_v1_lock_20261002.json"
TASK_LOCK=ROOT/"evaluation/substrate_capability/thoughtexperiment_control_kind_classification_repair_v1_lock_20261002.json"
TASK_SEED=ROOT/"seeds/control_kinds.json"
LOCK=ROOT/"evaluation/substrate_capability/thoughtexperiment_cross_family_ranker_null_transfer_v1_1_lock_20261002.json"
ORDERS=ROOT/"evaluation/reports/thoughtexperiment_cross_family_ranker_null_transfer_v1_1_orders_20261002.json"
SCORES=ROOT/"evaluation/reports/thoughtexperiment_cross_family_ranker_null_transfer_v1_1_scores_20261002.json"
TARGET="classify_kind_family"
SOURCES=("domains/reflective_faculty.py","domains/self_correct_dispatch.py","domains/self_correction.py","domains/edit_ops.py","domains/engine_provenance.py","substrate/boot_core.py","substrate/seed_loader.py","seeds/control_kinds.json","seeds/relation_vocabulary.json","seeds/composer_dispatch.json","seeds/autonomy.json","runners/dsl/src/py.rs","runners/dsl/src/substrate.rs","runners/dsl/src/graph.rs","runners/dsl/src/graph_rules.rs","runners/dsl/src/term.rs","runners/dsl/src/persist.rs","runners/dsl/src/grammar.rs","runners/dsl/src/sym.rs","runners/dsl/src/lib.rs","runners/dsl/Cargo.toml","runners/dsl/Cargo.lock","runners/dsl/python/substrate_rs/__init__.py")

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen()->dict:
 from substrate_rs import _native
 rows={p:sha(ROOT/p) for p in SOURCES}
 rows.update({str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,PREREG,REC_RAW,REC_LOCK,TASK_SEED,TASK_LOCK)})
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
   "descriptors":descriptors,"candidates":candidates,"default_order":[c["label"] for c in candidates],
   "prior_records":prior,"cold_order":cold_order,"experience_order":exp_order,
   "experience_traces":traces,"timing_ns":{"cold_rank":cold_ns,"experience_rank":experience_ns}}

def score_worker(payload:dict)->dict:
 """Separate post-order evaluator; receives captured candidate bundles only."""
 from substrate.boot_core import boot_core
 from substrate.seed_loader import manifest_for
 from domains.edit_ops import apply_flip_comparison
 before=frozen(); rows=[]
 heldout=[{"name":"steering wheel","expected":"continuous_rotation"},
          {"name":"trigger button","expected":"discrete_act"}]
 for candidate in payload["candidates"]:
  outcomes=[]
  for case in heldout:
   s,root=boot_core(seeds=());native=s._inner
   native.load_seed_manifest(manifest_for("control_kinds"),root)
   exported=native.export_rules();idx=next(i for i,r in enumerate(exported) if r.get("name")==TARGET and r.get("active",True))
   fault=apply_flip_comparison(exported[idx],TARGET);native.remove_rule(idx);native.add_rule(fault)
   active=[i for i,r in enumerate(native.export_rules()) if r.get("name")==TARGET and r.get("active",True)]
   if not active or not all(native.remove_rule(i) for i in reversed(active)):raise RuntimeError("fault replacement failed")
   native.add_rule(candidate["rules"][TARGET])
   registry=next(n for n in s.nodes("SignalRegistry") if s.node(n)["attrs"].get("name")=="control_family_signals")
   kind=s.add_node("ControlKind",{"name":case["name"],"name_lc":case["name"].lower(),"family_set":0.0})
   native.add_edge_unchecked(registry,"has_kind",kind);work=int(native.run_rules(1000));attrs=s.node(kind)["attrs"]
   outcomes.append({"name":case["name"],"expected":case["expected"],"actual":attrs.get("effect_family"),
                    "family_set":attrs.get("family_set"),"closure_work":work,
                    "pass":attrs.get("effect_family")==case["expected"] and attrs.get("family_set")==1.0})
  rows.append({"label":candidate["label"],"outcomes":outcomes,"utility":float(all(x["pass"] for x in outcomes))})
 after=frozen()
 return {"worker":payload["worker"],"source_before":before,"source_after":after,"source_stable":before==after,"scores":rows}

def main()->int:
 if sys.argv[1:2]==["--worker"]:
  print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(",",":")));return 0
 if sys.argv[1:2]==["--score-worker"]:
  payload=json.load(sys.stdin);print(json.dumps(score_worker(payload),sort_keys=True,separators=(",",":")));return 0
 if sys.argv[1:]==["--lock"]:
  if LOCK.exists() or ORDERS.exists() or SCORES.exists():raise SystemExit("refusing to overwrite existing lock/capture")
  from domains.engine_provenance import build_is_stale,rust_source_fingerprint
  stale=build_is_stale(str(ROOT))
  if stale:raise SystemExit("stale native engine: "+"; ".join(stale))
  LOCK.write_text(json.dumps({"schema":"CrossFamilyRankerNullTransferV1_1Lock","sources":frozen(),
   "semantic_engine":rust_source_fingerprint(str(ROOT)),"workers":3,"source_family":"recurrence_offer_idempotence",
   "evaluation_family":"control_kind_classification","outcome_origin":"locked recurrence train split only"},indent=2,sort_keys=True)+"\n")
  print(LOCK.relative_to(ROOT));return 0
 if not LOCK.exists():raise SystemExit("missing lock")
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("stale native engine: "+"; ".join(stale))
 lock=json.loads(LOCK.read_text())
 env={**os.environ,"PYTHONPATH":f"{ROOT/'runners/dsl/python'}:{ROOT}"}
 if sys.argv[1:]==["--orders"]:
  if ORDERS.exists() or SCORES.exists():raise SystemExit("refusing to overwrite order/score capture")
  before=frozen()
  if before!=lock["sources"]:raise SystemExit("source drift from lock")
  workers=[]
  for i in range(3):
   p=subprocess.run([sys.executable,str(RUNNER),"--worker",str(i)],cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(f"rank worker {i}: {p.stderr[-3000:]}")
   workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
  after=frozen()
  if before!=after:raise SystemExit("source drift during order capture")
  capture={"schema":"CrossFamilyRankerNullTransferV1_1OrderCapture","captured_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
   "host":{"platform":platform.platform(),"machine":platform.machine(),"python":sys.version.split()[0]},"lock":lock,
   "source_before":before,"source_after":after,"semantic_engine":rust_source_fingerprint(str(ROOT)),"workers":workers}
  ORDERS.write_text(json.dumps(capture,indent=2,sort_keys=True)+"\n")
  print(json.dumps({"stage":"orders_frozen","workers":len(workers),"orders":ORDERS.relative_to(ROOT)},sort_keys=True));return 0
 if sys.argv[1:]==["--score"]:
  if not ORDERS.exists() or SCORES.exists():raise SystemExit("missing order capture or score capture already exists")
  before=frozen()
  if before!=lock["sources"]:raise SystemExit("source drift from lock")
  order_capture=json.loads(ORDERS.read_text());scores=[]
  for row in order_capture["workers"]:
   payload={"worker":row["worker"],"candidates":row["candidates"]}
   p=subprocess.run([sys.executable,str(RUNNER),"--score-worker"],input=json.dumps(payload),cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode:raise RuntimeError(f"score worker {row['worker']}: {p.stderr[-3000:]}")
   scores.append(json.loads(p.stdout.strip().splitlines()[-1]))
  after=frozen()
  if before!=after:raise SystemExit("source drift during utility scoring")
  SCORES.write_text(json.dumps({"schema":"CrossFamilyRankerNullTransferV1_1ScoreCapture",
   "captured_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"orders_sha256":sha(ORDERS),
   "source_before":before,"source_after":after,"workers":scores},indent=2,sort_keys=True)+"\n")
  print(json.dumps({"stage":"heldout_scored_after_order_freeze","workers":len(scores),"score_capture":SCORES.relative_to(ROOT)},sort_keys=True));return 0
 raise SystemExit("choose --lock, --orders, or --score")
if __name__=="__main__":raise SystemExit(main())
