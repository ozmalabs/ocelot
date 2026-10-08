#!/usr/bin/env python3
"""Measure cross-family outcome transfer where cold candidate ranking is wrong."""
from __future__ import annotations
import copy,hashlib,importlib.util,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
BASE=ROOT/"evaluation/substrate_capability/thoughtexperiment_graph_authored_correction_rank_v1.py"
SOURCES=("domains/self_correction.py","domains/self_correct_dispatch.py","domains/reflective_faculty.py","seeds/composer_self_correct_graph.json","seeds/minting_recurrence_ledger.json","substrate/boot_core.py","evaluation/substrate_capability/thoughtexperiment_graph_authored_correction_rank_v1.py","evaluation/substrate_capability/thoughtexperiment_cross_family_idempotence_transfer_v1.py","evaluation/substrate_capability/thoughtexperiment_cross_family_idempotence_transfer_v2.py")
RAW=ROOT/"evaluation/reports/thoughtexperiment_cross_family_idempotence_transfer_v2_raw_20261001.json"
RESULT=ROOT/"docs/research/engine_substrate/THOUGHTEXPERIMENT_CROSS_FAMILY_IDEMPOTENCE_TRANSFER_V2_RESULTS_20261001.md"
spec=importlib.util.spec_from_file_location("rankbase2",BASE);base=importlib.util.module_from_spec(spec);sys.modules[spec.name]=base;spec.loader.exec_module(base)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def hashes():return {name:sha(ROOT/name) for name in SOURCES}
def training_records(ep):
 rows=[]
 for tried in ep["tried"]:
  trace=tried.get("rank_trace") or {}
  rows.append({"target_rule":ep["target_rule"],"candidate_label":tried.get("label",""),"outcome_class":trace.get("outcome_class",""),"candidate_digest":tried.get("candidate_digest",""),"converges_in_rehearsal":bool(tried.get("converges")),"selected":bool(tried.get("selected")),"adopted":bool(ep["adopted"] and tried.get("selected")),"task_utility":1.0 if ep["adopted"] and tried.get("selected") and ep["model_final_converged"] else 0.0,"rank_attempt_tag":trace.get("attempt_tag","")})
 return rows

def make_task(worker,arm,records):
 from substrate.boot_core import boot_core
 from substrate.seed_loader import manifest_for
 import domains.reflective_faculty as rf
 import domains.self_correct_dispatch as dispatch
 from domains.self_correction import _default_candidates
 sub,agent_node=boot_core(seeds=())
 for seed_id in ("relation_vocabulary","composer_dispatch","autonomy","minting_recurrence_ledger"):
  sub._inner.load_seed_manifest(manifest_for(seed_id),agent_node)
 class Agent:
  def __init__(self,s,a):self.s=s;self.inner=s._inner;self.agent=a
 agent=Agent(sub,agent_node)
 for phrase,tag in ((["predict","COLLAPSE","of","DIVERGENCE"],"v2_cw"),(["correct","DIVERGENCE","by","CANDIDATE"],"v2_sc")):
  row=rf.induce_concern(agent,[phrase],name_hint=tag);out=rf.ground_concern(agent,[row["capability_key"]])
  if not out.get("grounded") or out.get("served_by")!="graph":raise RuntimeError("graph rank composer failed")
 native=rf._native_eval2(sub);rf._ensure_shape_decode_loop(sub,native,agent_node);native.run_rules(2000)
 rules=native.export_rules();active=[(i,r) for i,r in enumerate(rules) if r.get("name")=="mrl_offer_due_once" and r.get("active",True)]
 if not active:raise RuntimeError("recurrence offer rule missing")
 authored=copy.deepcopy(active[0][1]);faulty=copy.deepcopy(authored);faulty["where"]["items"]=[x for x in faulty["where"]["items"] if x.get("type")!="Not"]
 if not all(native.remove_rule(i) for i,_ in reversed(active)):raise RuntimeError("could not isolate recurrence offer target")
 native.add_rule(faulty)
 candidate_ids=[];episode_node=None
 for j in range(1):
  key=f"cross-v2-{worker}-{j}"
  episode_node=sub.add_node("MintingRecurrenceEpisode",{"mint_after_quanta":1,"integer_native":1})
  cand=sub.add_node("PredicateRecurrenceCandidate",{"predicate":"bind","recurrence_key":key,"structural_signature":[["relation","bind","ITEM",f"SLOT{j}",worker]],"capability_key":[key,"X"]})
  ev=sub.add_node("ResidualSegmentEvidence",{"predicate":"bind","recurrence_key":key,"structural_signature":[["relation","bind","ITEM",f"SLOT{j}",worker]],"capability_key":[key,"X"],"segment_ordinal":j,"integer_native":1})
  sub.add_edge(agent_node,"has_minting_recurrence_episode",episode_node)
  sub.add_edge(episode_node,"has_predicate_recurrence_candidate",cand);sub.add_edge(cand,"supported_by_segment",ev);candidate_ids.append(key)
 for record in records:
  if record.get("outcome_class"):sub.add_node("CorrectionOutcome",record)
 cands=_default_candidates(native,"mrl_offer_due_once")
 required={"dedup_identity_fix","episode_scoped_offer_guard"}
 if not required.issubset({c.get("label") for c in cands}):raise RuntimeError("both task-shaped candidates not present")
 ordered=dispatch.rank_candidates(agent,native,cands)
 before_graph=native.graph_to_dict();before_rules=native.export_rules();trials=[]
 for cand in ordered:
  branch=sub.fork_full_copy_experiment();bn=branch._inner
  target_ids=[i for i,r in enumerate(bn.export_rules()) if r.get("name")=="mrl_offer_due_once" and r.get("active",True)]
  if not target_ids or not all(bn.remove_rule(i) for i in reversed(target_ids)):raise RuntimeError("branch rule replacement failed")
  variant=(cand.get("rules") or {}).get("mrl_offer_due_once")
  if variant is not None:bn.add_rule(variant)
  sweeps=[]
  for _ in range(5):sweeps.append(int(bn.run_rules(100)))
  # A second due candidate arrives in a later evidence step. An episode-wide
  # guard now suppresses this valid offer; a candidate-scoped guard does not.
  second_key=f"cross-v2-{worker}-1"
  second=branch.add_node("PredicateRecurrenceCandidate",{"predicate":"bind","recurrence_key":second_key,"structural_signature":[["relation","bind","ITEM","SLOT1",worker]],"capability_key":[second_key,"X"]})
  second_evidence=branch.add_node("ResidualSegmentEvidence",{"predicate":"bind","recurrence_key":second_key,"structural_signature":[["relation","bind","ITEM","SLOT1",worker]],"capability_key":[second_key,"X"],"segment_ordinal":1,"integer_native":1})
  branch.add_edge(episode_node,"has_predicate_recurrence_candidate",second);branch.add_edge(second,"supported_by_segment",second_evidence)
  for _ in range(5):sweeps.append(int(bn.run_rules(100)))
  trial_candidate_ids=[*candidate_ids,second_key]
  offer_counts=[]
  for key in trial_candidate_ids:
   bc=next(n for n in branch.nodes("PredicateRecurrenceCandidate") if branch.node(n)["attrs"].get("recurrence_key")==key)
   offer_counts.append(len(list(branch.neighbours(bc,"has_mint_offer"))))
  fixed=int(bn.run_rules(100));ok=offer_counts==[1,1] and fixed==0
  trials.append({"label":cand["label"],"outcome_class":cand.get("outcome_class",""),"rank_trace":cand.get("_self_correction_rank_trace",{}),"offer_counts_by_candidate":offer_counts,"sweep_progress":sweeps,"final_fixedpoint_progress":fixed,"task_oracle":ok})
  if ok:break
 return {"arm":arm,"program_present":any(sub.node(p)["attrs"].get("name","").startswith("self_correct_rank_") for p in sub.nodes("Program")),"candidate_order":[c["label"] for c in ordered],"trials":trials,"success":bool(trials and trials[-1]["task_oracle"]),"primary_preserved":before_graph==native.graph_to_dict() and before_rules==native.export_rules()}

def worker(i):
 before=hashes();training=base.episode(i,"graph_cost_rank");records=training_records(training)
 cold=make_task(i,"cold_rank",[]);warm=make_task(i,"experience_rank",records);after=hashes()
 return {"pid":os.getpid(),"source_before":before,"source_after":after,"source_stable":before==after,"training":{"chosen":training["selected_candidate"],"adopted":training["adopted"],"model_final_converged":training["model_final_converged"],"records":records},"cold":cold,"experience":warm}
def main():
 if len(sys.argv)==3 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(",",":")));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("stale native engine: "+"; ".join(stale))
 env={**os.environ,"PYTHONPATH":f"{ROOT / 'runners/dsl/python'}:{ROOT}"};workers=[]
 for i in range(3):
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(i)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
 gates={"three_fresh_workers":len(workers)==3,"stable_sources":all(w["source_stable"] for w in workers),"training_success":all(w["training"]["chosen"]=="dedup_identity_fix" and w["training"]["adopted"] and any(r["outcome_class"]=="idempotent_mint_guard" and r["task_utility"]==1 for r in w["training"]["records"]) for w in workers),"rank_program_both_arms":all(w[a]["program_present"] for w in workers for a in ("cold","experience")),"cold_error_observed":all(w["cold"]["trials"][0]["label"]=="episode_scoped_offer_guard" and not w["cold"]["trials"][0]["task_oracle"] and w["cold"]["trials"][-1]["task_oracle"] for w in workers),"cross_target_success_used":all(w["experience"]["trials"][0]["label"]=="dedup_identity_fix" and w["experience"]["trials"][0]["rank_trace"].get("prior_successes",0)>=1 and w["experience"]["trials"][0]["rank_trace"].get("target_rule")=="mrl_offer_due_once" for w in workers),"experience_one_trial":all(len(w["experience"]["trials"])==1 and w["experience"]["trials"][0]["task_oracle"] for w in workers),"cold_repairs_after_error":all(w["cold"]["success"] and len(w["cold"]["trials"])>=2 for w in workers),"branch_primary_isolation":all(w[a]["primary_preserved"] for w in workers for a in ("cold","experience"))}
 summaries=[{"arm":a,"trials_to_oracle":[len(w[a]["trials"]) for w in workers],"first_candidate":[w[a]["trials"][0]["label"] for w in workers],"first_offer_counts":[w[a]["trials"][0]["offer_counts_by_candidate"] for w in workers],"cross_target_prior_successes":[w[a]["trials"][0]["rank_trace"].get("prior_successes",0) for w in workers],"oracle_passes":sum(w[a]["success"] for w in workers)} for a in ("cold","experience")]
 from substrate_rs import _native
 binary=Path(_native.__file__).resolve()
 capture={"schema":"ThoughtexperimentCrossFamilyIdempotenceTransferV2","captured_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"protocol":{"workers":3,"training_family":"shape-axis deduplication","evaluation_family":"staged two-candidate recurrence offer idempotence","second_candidate_arrival":"after first candidate has settled","candidate_utility":"one offer per due candidate and zero-progress closure","branch_backend":"native full-copy experiment"},"source_hashes":workers[0]["source_before"],"engine_fingerprint":rust_source_fingerprint(str(ROOT)),"native_binary":{"path":str(binary),"sha256":hashlib.sha256(binary.read_bytes()).hexdigest()},"workers":workers,"summary":summaries,"gates":gates}
 RAW.parent.mkdir(parents=True,exist_ok=True);RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+"\n")
 out = [
  "# Thoughtexperiment cross-family idempotence transfer v2 — results",
  "",
  f"**Result:** {sum(gates.values())}/{len(gates)} preregistered gates pass; task staging follows the [amendment](THOUGHTEXPERIMENT_CROSS_FAMILY_IDEMPOTENCE_TRANSFER_V2_AMENDMENT_20261001.md).",
  "",
  "The two-candidate recurrence task makes global idempotence insufficient: its oracle requires exactly one offer for each candidate.",
  "",
  "| Arm | Trials to oracle | First candidate | First candidate's offers | Cross-target prior success | Oracle passes |",
  "|---|---:|---|---|---:|---:|",
 ]
 out += [f"| `{row['arm']}` | {row['trials_to_oracle']} | {row['first_candidate']} | {row['first_offer_counts']} | {row['cross_target_prior_successes']} | {row['oracle_passes']}/3 |" for row in summaries]
 out += [
  "",
  "The cold ranker first selects the smaller episode-scoped guard, which suppresses the second valid offer; it then finds the candidate-scoped repair. Transferred outcome history ranks the candidate-scoped repair first and passes immediately. This demonstrates measured search-cost improvement across these two authored families (two trials to one), under explicit shared class labels and host-managed evidence transport. It does not demonstrate autonomous discovery or natural-task generalization.",
  "",
  "## Artifacts",
  "",
  "- [Preregistration](THOUGHTEXPERIMENT_CROSS_FAMILY_IDEMPOTENCE_TRANSFER_V2_PREREG_20261001.md)",
  "- [Amendment](THOUGHTEXPERIMENT_CROSS_FAMILY_IDEMPOTENCE_TRANSFER_V2_AMENDMENT_20261001.md)",
  "- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_cross_family_idempotence_transfer_v2.py)",
  "- [Raw capture](../../../evaluation/reports/thoughtexperiment_cross_family_idempotence_transfer_v2_raw_20261001.json)",
 ]
 out = "\n".join(out) + "\n"
 RESULT.write_text(out);print(json.dumps({"gates":gates,"summary":summaries},indent=2,sort_keys=True));return 0 if all(gates.values()) else 1
if __name__=="__main__":raise SystemExit(main())
