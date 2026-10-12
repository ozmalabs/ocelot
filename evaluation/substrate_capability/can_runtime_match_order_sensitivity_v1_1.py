#!/usr/bin/env python3
"""Held-out matched replay of sparse-first CAN rule join order."""
from __future__ import annotations
import hashlib,importlib.util,json,os,platform,statistics,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"runners/dsl/python"))
PROTOCOL=ROOT/"docs/research/engine_substrate/CAN_RUNTIME_MATCH_ORDER_SENSITIVITY_V1_1_HELDOUT_PREREG_20260929.md"
RUNNER=Path(__file__).resolve();BASE_RUNNER=ROOT/"evaluation/substrate_capability/can_runtime_match_order_sensitivity_v1.py"
SEED=ROOT/"seeds/can_native_reimplementation.json";FIXTURE=ROOT/"scripts/substrate_can_structure_envelope.py"
LOCK=ROOT/"evaluation/substrate_capability/can_runtime_match_order_sensitivity_v1_1_lock_20260929.json"
OUT=ROOT/"evaluation/reports/can_runtime_match_order_sensitivity_v1_1_20260929.json"
SIZES=(128,256);TOPOLOGIES=("path","banded2");MODES=("2state","3state");REPLICATES=(2,3);TARGETS=("can_native_hebbian_mint","can_native_hebbian_reweight");MAX_STEPS=100000
spec=importlib.util.spec_from_file_location("match_order_base",BASE_RUNNER);BASE=importlib.util.module_from_spec(spec);spec.loader.exec_module(BASE)

def digest(path):
 raw=path.read_bytes();return {"path":path.relative_to(ROOT).as_posix(),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
def lock_inputs():
 from substrate_rs import _native
 sources=("domains/can_junction_tree.py","domains/graph_treewidth.py","domains/can_native_orchestration.py",
  "runners/dsl/src/scale_audit.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/src/can_ops.rs",
  "runners/dsl/src/py.rs","runners/dsl/src/graph.rs","runners/dsl/python/substrate_rs/_native.build.json")
 return {"schema_version":1,"protocol":digest(PROTOCOL),"runner":digest(RUNNER),"base_runner":digest(BASE_RUNNER),
  "fixture":digest(FIXTURE),"seed":digest(SEED),"sources":[digest(ROOT/p) for p in sources],
  "native_extension":{"path":Path(_native.__file__).resolve().relative_to(ROOT).as_posix(),"sha256":hashlib.sha256(Path(_native.__file__).resolve().read_bytes()).hexdigest()},
  "sizes":list(SIZES),"topologies":list(TOPOLOGIES),"modes":list(MODES),"replicates":list(REPLICATES),"targets":list(TARGETS),
  "git_head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}

def rule_counts(arm):
 out={}
 for x in arm["per_rule"]:
  if x["rule_name"] in TARGETS and x["metric"] in ("candidate_pairs","term_evaluations"):
   k=f"{x['rule_name']}::{x['metric']}";out[k]=out.get(k,0)+x["count"]
 return out

def worker(n,topology,mode,rep):
 import substrate_rs as sr
 from substrate.seed_loader import engine_rules_only
 from collections import Counter
 fixture=BASE.BASE.load_fixture();seed_doc=__import__('json').loads(SEED.read_text());alt_doc,changes=BASE.variant_seed(seed_doc);started=lock_inputs()
 order=("baseline","reordered") if rep%2==0 else ("reordered","baseline")
 plain={}
 for arm in order:
  plain[arm]=BASE.run_arm(sr,engine_rules_only,fixture,seed_doc if arm=="baseline" else alt_doc,n,topology,mode,rep,audit=False)
 audit_order=tuple(reversed(order));audited={}
 for arm in audit_order:
  audited[arm]=BASE.run_arm(sr,engine_rules_only,fixture,seed_doc if arm=="baseline" else alt_doc,n,topology,mode,rep,audit=True)
 ended=lock_inputs();b=plain["baseline"];v=plain["reordered"];ab=audited["baseline"];av=audited["reordered"]
 return {"n":n,"topology":topology,"mode":mode,"replicate":rep,"worker_pid":os.getpid(),"plain_order":order,"audit_order":audit_order,"changes":changes,
  "baseline":{"progress":b["progress"],"wall_ns":b["wall_ns"],"graph_signature":b["graph_signature"],"model_signature":b["model_signature"],"residuals":b["residuals"],"terminal":b["terminal"]},
  "reordered":{"progress":v["progress"],"wall_ns":v["wall_ns"],"graph_signature":v["graph_signature"],"model_signature":v["model_signature"],"residuals":v["residuals"],"terminal":v["terminal"]},
  "audited_baseline":{"progress":ab["progress"],"graph_signature":ab["graph_signature"],"model_signature":ab["model_signature"],"residuals":ab["residuals"],"terminal":ab["terminal"],"counters":rule_counts(ab)},
  "audited_reordered":{"progress":av["progress"],"graph_signature":av["graph_signature"],"model_signature":av["model_signature"],"residuals":av["residuals"],"terminal":av["terminal"],"counters":rule_counts(av)},
  "semantic_parity":b["progress"]==v["progress"] and b["graph_signature"]==v["graph_signature"] and b["model_signature"]==v["model_signature"],
  "audit_parity":b["progress"]==ab["progress"]==v["progress"]==av["progress"] and b["graph_signature"]==ab["graph_signature"]==v["graph_signature"]==av["graph_signature"] and b["model_signature"]==ab["model_signature"]==v["model_signature"]==av["model_signature"],
  "source_lock_start":started,"source_lock_end":ended}

def main():
 if len(sys.argv)==6 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2]),sys.argv[3],sys.argv[4],int(sys.argv[5])),sort_keys=True));return
 if sys.argv[1:]==["--lock"]:
  if LOCK.exists() or OUT.exists():raise SystemExit("refusing to overwrite lock/capture")
  LOCK.write_text(json.dumps(lock_inputs(),indent=2,sort_keys=True)+"\n");print(LOCK.relative_to(ROOT));return
 lock=json.loads(LOCK.read_text())
 if lock_inputs()!=lock:raise SystemExit("source/held-out lock drift")
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("native build stale:\n"+"\n".join(stale))
 env={**os.environ,"PYTHONPATH":f"{ROOT/'runners/dsl/python'}:{ROOT}:{os.environ.get('PYTHONPATH','')}"};rows=[]
 for n in SIZES:
  for topology in TOPOLOGIES:
   for mode in MODES:
    for rep in REPLICATES:
     cp=subprocess.run([sys.executable,str(RUNNER),"--worker",str(n),topology,mode,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=300)
     row=json.loads(cp.stdout);rows.append(row)
     b=row["audited_baseline"]["counters"];v=row["audited_reordered"]["counters"]
     bc=sum(x for k,x in b.items() if k.endswith("candidate_pairs"));vc=sum(x for k,x in v.items() if k.endswith("candidate_pairs"))
     print(f"n={n} {topology} {mode} rep={rep} semantic={row['semantic_parity']} candidates={bc}->{vc} plain_ms={row['baseline']['wall_ns']/1e6:.1f}->{row['reordered']['wall_ns']/1e6:.1f}",flush=True)
 post=lock_inputs()
 checks={"worker_coverage":len(rows)==16 and len({r["worker_pid"] for r in rows})==16,
  "cell_coverage":all(sum((r["n"],r["topology"],r["mode"],r["replicate"])==(n,t,m,rep) for r in rows)==1 for n in SIZES for t in TOPOLOGIES for m in MODES for rep in REPLICATES),
  "variant_rules":all({x["rule"] for x in r["changes"]}==set(TARGETS) for r in rows),
  "semantic_parity":all(r["semantic_parity"] for r in rows),"audit_parity":all(r["audit_parity"] for r in rows),
  "fixed_points":all(all(r[name]["residuals"]==0 and r[name]["terminal"]==0 for name in ("baseline","reordered","audited_baseline","audited_reordered")) for r in rows),
  "target_counters_complete":all(all(k in r[arm]["counters"] for arm in ("audited_baseline","audited_reordered") for k in (f"{t}::{metric}" for t in TARGETS for metric in ("candidate_pairs","term_evaluations"))) for r in rows),
  "source_stability":lock==post and all(r["source_lock_start"]==lock==r["source_lock_end"] for r in rows)}
 summaries=[]
 for n in SIZES:
  for top in TOPOLOGIES:
   for mode in MODES:
    g=[r for r in rows if (r["n"],r["topology"],r["mode"])==(n,top,mode)]
    med=lambda f:statistics.median(f(r) for r in g)
    summaries.append({"n":n,"topology":top,"mode":mode,"replicates":len(g),"semantic_parity":all(r["semantic_parity"] for r in g),
     "median_baseline_ms":med(lambda r:r["baseline"]["wall_ns"])/1e6,"median_reordered_ms":med(lambda r:r["reordered"]["wall_ns"])/1e6,
     "median_baseline_candidates":med(lambda r:sum(x for k,x in r["audited_baseline"]["counters"].items() if k.endswith("candidate_pairs"))),
     "median_reordered_candidates":med(lambda r:sum(x for k,x in r["audited_reordered"]["counters"].items() if k.endswith("candidate_pairs"))),
     "median_baseline_terms":med(lambda r:sum(x for k,x in r["audited_baseline"]["counters"].items() if k.endswith("term_evaluations"))),
     "median_reordered_terms":med(lambda r:sum(x for k,x in r["audited_reordered"]["counters"].items() if k.endswith("term_evaluations")))})
 payload={"schema_version":1,"run_id":"can-runtime-match-order-sensitivity-v1.1-heldout-20260929","status":"complete","input_lock":lock,"post_run_input_lock":post,
  "configuration":{"sizes":SIZES,"topologies":TOPOLOGIES,"modes":MODES,"replicates":REPLICATES,"targets":TARGETS,"heldout_seed_replicates":REPLICATES},
  "claim_boundary":"held-out fixture seeds for one authored CAN rule family; no natural task or second-family claim","environment":{"python":platform.python_version(),"platform":platform.platform()},
  "checks":checks,"summaries":summaries,"runs":rows}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":OUT.relative_to(ROOT).as_posix(),"checks":checks},indent=2))
 if not all(checks.values()):raise SystemExit("held-out match-order gate failed")
if __name__=="__main__":main()
