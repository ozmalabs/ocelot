#!/usr/bin/env python3
"""Paired join-order evaluation for the three measured CAN closure hotspots."""
from __future__ import annotations
import copy,hashlib,importlib.util,json,os,platform,random,statistics,subprocess,sys,time
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"runners/dsl/python"))
PROTOCOL=ROOT/"docs/research/engine_substrate/CAN_RUNTIME_MATCH_ORDER_SENSITIVITY_V1_PREREG_20260929.md"
RUNNER=Path(__file__).resolve();BASE_RUNNER=ROOT/"evaluation/substrate_capability/can_runtime_closure_attribution_v1.py"
SEED=ROOT/"seeds/can_native_reimplementation.json";BASE_RAW=ROOT/"evaluation/reports/can_runtime_closure_attribution_v1_20260929.json"
BASE_LOCK=ROOT/"evaluation/substrate_capability/can_runtime_closure_attribution_v1_lock_20260929.json"
LOCK=ROOT/"evaluation/substrate_capability/can_runtime_match_order_sensitivity_v1_lock_20260929.json"
OUT=ROOT/"evaluation/reports/can_runtime_match_order_sensitivity_v1_20260929.json"
SIZES=(128,256);TOPOLOGIES=("path","banded2");MODES=("2state","3state");REPLICATES=2;MAX_STEPS=100000;TARGETS=("can_native_hebbian_mint","can_native_hebbian_reweight")
_spec=importlib.util.spec_from_file_location("closure_baseline",BASE_RUNNER);BASE=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(BASE)

def digest(path):
 raw=path.read_bytes();return {"path":path.relative_to(ROOT).as_posix(),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
def lock_inputs():
 from substrate_rs import _native
 sources=("runners/dsl/src/scale_audit.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/src/can_ops.rs","runners/dsl/src/py.rs","runners/dsl/python/substrate_rs/_native.build.json")
 return {"schema_version":1,"protocol":digest(PROTOCOL),"runner":digest(RUNNER),"baseline_runner":digest(BASE_RUNNER),
  "seed":digest(SEED),"baseline_capture":digest(BASE_RAW),"baseline_lock":digest(BASE_LOCK),"sources":[digest(ROOT/p) for p in sources],
  "native_extension":{"path":Path(_native.__file__).resolve().relative_to(ROOT).as_posix(),"sha256":hashlib.sha256(Path(_native.__file__).resolve().read_bytes()).hexdigest()},
  "sizes":list(SIZES),"topologies":list(TOPOLOGIES),"modes":list(MODES),"replicates":REPLICATES,"targets":list(TARGETS),
  "git_head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}

def variant_seed(seed_doc):
 doc=copy.deepcopy(seed_doc);changes=[]
 for rule in doc["rules"]:
  if rule.get("name") in TARGETS:
   before=rule["match"]
   if len(before)!=4:raise AssertionError(f"unexpected target match width {rule.get('name')}")
   rule["match"]=[before[2],before[3],before[0],before[1]]
   changes.append({"rule":rule["name"],"before":before,"after":rule["match"]})
 if {x["rule"] for x in changes}!=set(TARGETS):raise AssertionError("target rule coverage mismatch")
 return doc,changes

def graph_signature(inner):
 graph=inner.graph_to_dict();nodes={n["id"]:n for n in graph["nodes"]};edges=graph["edges"]
 concept={i:"C:"+str(n["attrs"].get("name")) for i,n in nodes.items() if n["type"]=="Concept"}
 mt_ids=[i for i,n in nodes.items() if n["type"]=="Microtheory"]
 token=dict(concept)
 for j,i in enumerate(sorted(mt_ids)):token[i]=f"MT:{j}"
 coact_left=defaultdict(list);coact_right=defaultdict(list)
 for e in edges:
  if e["type"]=="coactivated_with":coact_left[e["tgt"]].append(token.get(e["src"],str(e["src"])))
  elif e["type"]=="coactivation_of":coact_right[e["src"]].append(token.get(e["tgt"],str(e["tgt"])))
 for i,n in nodes.items():
  if n["type"]=="Coactivation":
   left=sorted(coact_left[i]);right=sorted(coact_right[i])
   token[i]="Coact:"+",".join(left)+"→"+",".join(right)
 for i,n in nodes.items():
  token.setdefault(i,n["type"]+":"+json.dumps(n["attrs"],sort_keys=True,default=repr))
 ns=[(token[i],n["type"],n["attrs"]) for i,n in nodes.items()]
 es=[(token[e["src"]],e["type"],token[e["tgt"]],e["attrs"]) for e in edges]
 ns.sort(key=lambda x:json.dumps(x,sort_keys=True,default=repr));es.sort(key=lambda x:json.dumps(x,sort_keys=True,default=repr))
 blob=json.dumps({"nodes":ns,"edges":es},sort_keys=True,default=repr,separators=(",",":"))
 return hashlib.sha256(blob.encode()).hexdigest(),len(nodes),len(edges)

def run_arm(sr,engine_rules_only,fixture,seed_doc,n,topology,mode,rep,audit=False):
 inner,concepts,fields,weights,draw_seed=BASE.build(sr,engine_rules_only,fixture,seed_doc,n,topology,mode,rep)
 if audit:
  inner.scale_audit_reset();inner.scale_audit_set_enabled(True);inner.scale_audit_set_per_rule_enabled(True)
 t=time.perf_counter_ns();progress=inner.run_rules(MAX_STEPS);wall_ns=time.perf_counter_ns()-t
 states={int(c.value):float(inner.node(c)["attrs"].get("state",0.)) for c in concepts}
 if audit:
  counters=dict(inner.scale_audit_snapshot());names={int(x[0]):str(x[1]) for x in inner.rule_access_sets()}
  per=[{"rule_name":names.get(i,f"rule_{i}"),"metric":m,"count":v} for i,m,v in inner.scale_audit_per_rule_snapshot()]
  inner.scale_audit_set_per_rule_enabled(False);inner.scale_audit_set_enabled(False)
 else:counters={};per=[]
 mt=inner.nodes("Microtheory")[0]
 import domains.can_junction_tree as cjt
 net=cjt.can_network_from_mt(inner,mt)
 vocab=(-1.0,1.0) if mode=="2state" else (-1.0,0.0,1.0);residuals=0
 for v,state in states.items():
  local=net["unary"].get(v,0.)+sum(w*states.get(next(iter(pair-{v})),0.) for pair,w in net["pairwise"].items() if v in pair)
  if fixture.update(mode,local)!=state:residuals+=1
 terminal=inner.run_rules(1)
 sig,node_count,edge_count=graph_signature(inner)
 model={"nodes":len(net["nodes"]),"edges":sorted(tuple(sorted(e)) for e in net["edges"]),
        "unary":sorted((int(k),float(v)) for k,v in net["unary"].items()),
        "pairwise":sorted((tuple(sorted(int(x) for x in k)),float(v)) for k,v in net["pairwise"].items()),"vocab":vocab}
 return {"progress":progress,"wall_ns":wall_ns,"states":states,"graph_signature":sig,"graph_nodes":node_count,"graph_edges":edge_count,
  "model_signature":hashlib.sha256(json.dumps(model,sort_keys=True).encode()).hexdigest(),"residuals":residuals,"terminal":terminal,
  "counters":counters,"per_rule":per,"seed":draw_seed}

def worker(n,topology,mode,rep):
 import substrate_rs as sr
 from substrate.seed_loader import engine_rules_only
 fixture=BASE.load_fixture();seed_doc=json.loads(SEED.read_text());alt_doc,changes=variant_seed(seed_doc);started=lock_inputs()
 arms=("baseline","reordered") if rep%2==0 else ("reordered","baseline")
 outputs={}
 for arm in arms:
  outputs[arm]=run_arm(sr,engine_rules_only,fixture,seed_doc if arm=="baseline" else alt_doc,n,topology,mode,rep)
 audited=run_arm(sr,engine_rules_only,fixture,alt_doc,n,topology,mode,rep,audit=True)
 end=lock_inputs()
 base_capture=json.loads(BASE_RAW.read_text())
 base_row=next(r for r in base_capture["runs"] if (r["n"],r["topology"],r["mode"],r["replicate"])==(n,topology,mode,rep))
 counts=Counter()
 for x in audited["per_rule"]:
  if x["rule_name"] in TARGETS and x["metric"] in ("candidate_pairs","term_evaluations"):
   counts[(x["rule_name"],x["metric"])]+=x["count"]
 baseline_counts=Counter()
 for x in base_row["per_rule_counters"]:
  if x["rule_name"] in TARGETS and x["metric"] in ("candidate_pairs","term_evaluations"):
   baseline_counts[(x["rule_name"],x["metric"])]+=x["count"]
 b=outputs["baseline"];v=outputs["reordered"]
 return {"n":n,"topology":topology,"mode":mode,"replicate":rep,"worker_pid":os.getpid(),"arm_order":arms,"changes":changes,
  "baseline":{"progress":b["progress"],"wall_ns":b["wall_ns"],"graph_signature":b["graph_signature"],"model_signature":b["model_signature"],"residuals":b["residuals"],"terminal":b["terminal"]},
  "reordered":{"progress":v["progress"],"wall_ns":v["wall_ns"],"graph_signature":v["graph_signature"],"model_signature":v["model_signature"],"residuals":v["residuals"],"terminal":v["terminal"]},
  "audited_variant":{"progress":audited["progress"],"graph_signature":audited["graph_signature"],"model_signature":audited["model_signature"],"residuals":audited["residuals"],"terminal":audited["terminal"],"counters":audited["counters"],"per_rule":audited["per_rule"]},
  "semantic_parity":b["progress"]==v["progress"] and b["states"]==v["states"] and b["graph_signature"]==v["graph_signature"] and b["model_signature"]==v["model_signature"],
  "audit_parity":v["progress"]==audited["progress"] and v["states"]==audited["states"] and v["graph_signature"]==audited["graph_signature"] and v["model_signature"]==audited["model_signature"],
  "baseline_target_counters":dict((f"{k[0]}::{k[1]}",x) for k,x in baseline_counts.items()),
  "variant_target_counters":dict((f"{k[0]}::{k[1]}",x) for k,x in counts.items()),"source_lock_start":started,"source_lock_end":end}

def main():
 if len(sys.argv)==6 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2]),sys.argv[3],sys.argv[4],int(sys.argv[5])),sort_keys=True));return
 if sys.argv[1:]==["--lock"]:
  if LOCK.exists() or OUT.exists():raise SystemExit("refusing to overwrite lock/capture")
  LOCK.write_text(json.dumps(lock_inputs(),indent=2,sort_keys=True)+"\n");print(LOCK.relative_to(ROOT));return
 lock=json.loads(LOCK.read_text())
 if lock_inputs()!=lock:raise SystemExit("source/input lock drift")
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("native build stale:\n"+"\n".join(stale))
 env={**os.environ,"PYTHONPATH":f"{ROOT/'runners/dsl/python'}:{ROOT}:{os.environ.get('PYTHONPATH','')}"};rows=[]
 for n in SIZES:
  for topology in TOPOLOGIES:
   for mode in MODES:
    for rep in range(REPLICATES):
     p=subprocess.run([sys.executable,str(RUNNER),"--worker",str(n),topology,mode,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=300)
     r=json.loads(p.stdout);rows.append(r);b=r["baseline_target_counters"];v=r["variant_target_counters"]
     btot=sum(x for k,x in b.items() if k.endswith("candidate_pairs"));vtot=sum(x for k,x in v.items() if k.endswith("candidate_pairs"))
     print(f"n={n} {topology} {mode} rep={rep} semantic={r['semantic_parity']} target_candidates={btot}->{vtot} plain_ms={r['baseline']['wall_ns']/1e6:.1f}->{r['reordered']['wall_ns']/1e6:.1f}",flush=True)
 post=lock_inputs()
 checks={"worker_coverage":len(rows)==16 and len({r["worker_pid"] for r in rows})==16,
  "cell_coverage":all(sum((r["n"],r["topology"],r["mode"])==(n,t,m) for r in rows)==REPLICATES for n in SIZES for t in TOPOLOGIES for m in MODES),
  "variant_changes_only_target_orders":all({x["rule"] for x in r["changes"]}==set(TARGETS) for r in rows),
  "semantic_parity":all(r["semantic_parity"] for r in rows),"audit_parity":all(r["audit_parity"] for r in rows),
  "fixed_points":all(all(a[k]["residuals"]==0 and a[k]["terminal"]==0 for k in ("baseline","reordered","audited_variant")) for a in rows),
  "target_counters_complete":all(all(k in r["variant_target_counters"] and k in r["baseline_target_counters"] for k in (f"{t}::{m}" for t in TARGETS for m in ("candidate_pairs","term_evaluations"))) for r in rows),
  "source_stability":lock==post and all(r["source_lock_start"]==lock==r["source_lock_end"] for r in rows)}
 summaries=[]
 for n in SIZES:
  for topology in TOPOLOGIES:
   for mode in MODES:
    g=[r for r in rows if (r["n"],r["topology"],r["mode"])==(n,topology,mode)]
    med=lambda f:statistics.median(f(r) for r in g)
    summaries.append({"n":n,"topology":topology,"mode":mode,"replicates":len(g),"semantic_parity":all(r["semantic_parity"] for r in g),
     "median_baseline_ms":med(lambda r:r["baseline"]["wall_ns"])/1e6,"median_reordered_ms":med(lambda r:r["reordered"]["wall_ns"])/1e6,
     "median_baseline_target_candidates":med(lambda r:sum(x for k,x in r["baseline_target_counters"].items() if k.endswith("candidate_pairs"))),
     "median_reordered_target_candidates":med(lambda r:sum(x for k,x in r["variant_target_counters"].items() if k.endswith("candidate_pairs"))),
     "median_baseline_target_term_evals":med(lambda r:sum(x for k,x in r["baseline_target_counters"].items() if k.endswith("term_evaluations"))),
     "median_reordered_target_term_evals":med(lambda r:sum(x for k,x in r["variant_target_counters"].items() if k.endswith("term_evaluations")))})
 payload={"schema_version":1,"run_id":"can-runtime-match-order-sensitivity-v1-20260929","status":"complete","input_lock":lock,"post_run_input_lock":post,
  "configuration":{"sizes":SIZES,"topologies":TOPOLOGIES,"modes":MODES,"replicates":REPLICATES,"targets":TARGETS,"permutation":[2,3,0,1]},
  "claim_boundary":"in-memory conjunct order change for two authored CAN rules only; no natural task or general optimizer claim","environment":{"python":platform.python_version(),"platform":platform.platform()},
  "checks":checks,"summaries":summaries,"runs":rows}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":OUT.relative_to(ROOT).as_posix(),"checks":checks},indent=2))
 if not all(checks.values()):raise SystemExit("match-order sensitivity gate failed")
if __name__=="__main__":main()
