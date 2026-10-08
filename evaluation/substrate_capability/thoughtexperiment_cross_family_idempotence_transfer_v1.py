#!/usr/bin/env python3
"""Measure graph-authored outcome-class transfer across two minting tasks."""
from __future__ import annotations
import copy, hashlib, importlib.util, json, os, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
BASE=ROOT/"evaluation/substrate_capability/thoughtexperiment_graph_authored_correction_rank_v1.py"
SOURCES=("domains/self_correction.py","domains/self_correct_dispatch.py","domains/reflective_faculty.py","seeds/composer_self_correct_graph.json","seeds/minting_recurrence_ledger.json","substrate/boot_core.py","evaluation/substrate_capability/thoughtexperiment_graph_authored_correction_rank_v1.py","evaluation/substrate_capability/thoughtexperiment_cross_family_idempotence_transfer_v1.py")
RAW=ROOT/"evaluation/reports/thoughtexperiment_cross_family_idempotence_transfer_v1_raw_20261001.json"
RESULT=ROOT/"docs/research/engine_substrate/THOUGHTEXPERIMENT_CROSS_FAMILY_IDEMPOTENCE_TRANSFER_V1_RESULTS_20261001.md"
spec=importlib.util.spec_from_file_location("rank_base",BASE);base=importlib.util.module_from_spec(spec);sys.modules[spec.name]=base;spec.loader.exec_module(base)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hashes():return {name:sha(ROOT/name) for name in SOURCES}
def training_records(ep):
 rows=[]
 for tried in ep["tried"]:
  trace=tried.get("rank_trace") or {}
  rows.append({"target_rule":ep["target_rule"],"candidate_label":tried.get("label",""),"outcome_class":trace.get("outcome_class",""),"candidate_digest":tried.get("candidate_digest",""),"converges_in_rehearsal":bool(tried.get("converges")),"selected":bool(tried.get("selected")),"adopted":bool(ep["adopted"] and tried.get("selected")),"task_utility":1.0 if ep["adopted"] and tried.get("selected") and ep["model_final_converged"] else 0.0,"rank_attempt_tag":trace.get("attempt_tag","")})
 return rows

def make_task(worker,arm,records):
 from substrate.boot_core import boot_core,load_seeds_into
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
 for phrase,tag in ((["predict","COLLAPSE","of","DIVERGENCE"],"cross_cw"),(["correct","DIVERGENCE","by","CANDIDATE"],"cross_sc")):
  induced=rf.induce_concern(agent,[phrase],name_hint=tag);grounded=rf.ground_concern(agent,[induced["capability_key"]])
  if not grounded.get("grounded") or grounded.get("served_by")!="graph":raise RuntimeError("graph correction policy did not ground")
 native=rf._native_eval2(sub);rf._ensure_shape_decode_loop(sub,native,agent_node);native.run_rules(2000)
 rows=native.export_rules();target_rows=[(i,r) for i,r in enumerate(rows) if r.get("name")=="mrl_offer_due_once" and r.get("active",True)]
 if not target_rows:raise RuntimeError("recurrence offer rule not installed")
 authored=copy.deepcopy(target_rows[0][1]);faulty=copy.deepcopy(authored);faulty["where"]["items"]=[x for x in faulty["where"]["items"] if x.get("type")!="Not"]
 if not all(native.remove_rule(i) for i,_ in reversed(target_rows)):raise RuntimeError("failed to isolate recurrence offer rule")
 native.add_rule(faulty)
 active=next(r for r in native.export_rules() if r.get("name")=="mrl_offer_due_once" and r.get("active",True))
 if active.get("where")==authored.get("where"):raise RuntimeError("faulted recurrence rule did not omit authored guard")
 episode=sub.add_node("MintingRecurrenceEpisode",{"mint_after_quanta":1,"integer_native":1})
 candidate=sub.add_node("PredicateRecurrenceCandidate",{"predicate":"bind","recurrence_key":f"cross-{worker}","structural_signature":[["relation","bind","ITEM","SLOT",worker]],"capability_key":[f"cross-{worker}","X"]})
 evidence=sub.add_node("ResidualSegmentEvidence",{"predicate":"bind","recurrence_key":f"cross-{worker}","structural_signature":[["relation","bind","ITEM","SLOT",worker]],"capability_key":[f"cross-{worker}","X"],"segment_ordinal":0,"integer_native":1})
 sub.add_edge(agent_node,"has_minting_recurrence_episode",episode);sub.add_edge(episode,"has_predicate_recurrence_candidate",candidate);sub.add_edge(candidate,"supported_by_segment",evidence)
 for row in records:
  if row.get("outcome_class"):sub.add_node("CorrectionOutcome",row)
 cands=_default_candidates(native,"mrl_offer_due_once")
 if not any(c.get("outcome_class")=="idempotent_mint_guard" for c in cands):raise RuntimeError(f"recurrence repair candidate missing; labels={[c.get('label') for c in cands]}; where={next(r for r in native.export_rules() if r.get('name')=='mrl_offer_due_once' and r.get('active',True)).get('where')}")
 ordered=dispatch.rank_candidates(agent,native,cands)
 before_graph=native.graph_to_dict();before_rules=native.export_rules()
 trials=[]
 for cand in ordered:
  branch=sub.fork_full_copy_experiment();bn=branch._inner
  target_is=[i for i,r in enumerate(bn.export_rules()) if r.get("name")=="mrl_offer_due_once" and r.get("active",True)]
  if not target_is or not all(bn.remove_rule(i) for i in reversed(target_is)):raise RuntimeError("branch target rule removal failed")
  variant=(cand.get("rules") or {}).get("mrl_offer_due_once")
  if variant is not None:bn.add_rule(variant)
  progresses=[]
  for _ in range(5):progresses.append(int(bn.run_rules(100)))
  bc=next(n for n in branch.nodes("PredicateRecurrenceCandidate") if branch.node(n)["attrs"].get("recurrence_key")==f"cross-{worker}")
  count=len(list(branch.neighbours(bc,"has_mint_offer")));final=int(bn.run_rules(100))
  ok=count==1 and final==0
  trials.append({"label":cand["label"],"outcome_class":cand.get("outcome_class",""),"rank_trace":cand.get("_self_correction_rank_trace",{}),"offer_count":count,"sweep_progress":progresses,"final_fixedpoint_progress":final,"task_oracle":ok})
  if ok:break
 return {"worker":worker,"arm":arm,"program_present":any(sub.node(p)["attrs"].get("name","").startswith("self_correct_rank_") for p in sub.nodes("Program")),"outcome_count":len(records) if arm=="experience_rank" else 0,"default_order":[c["label"] for c in cands],"candidate_order":[c["label"] for c in ordered],"trials":trials,"success":bool(trials and trials[-1]["task_oracle"]),"primary_preserved":before_graph==native.graph_to_dict() and before_rules==native.export_rules()}

def worker(i):
 before=hashes();training=base.episode(i,"graph_cost_rank");records=training_records(training)
 cold=make_task(i,"cold_rank",[]);warm=make_task(i,"experience_rank",records)
 after=hashes()
 return {"pid":os.getpid(),"source_before":before,"source_after":after,"source_stable":before==after,"training":{"target_rule":training["target_rule"],"selected":training["selected_candidate"],"adopted":training["adopted"],"model_final_converged":training["model_final_converged"],"records":records},"cold":cold,"experience":warm}

def main():
 if len(sys.argv)==3 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(",",":")));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("stale native engine: "+"; ".join(stale))
 env={**os.environ,"PYTHONPATH":f"{ROOT / 'runners/dsl/python'}:{ROOT}"};workers=[]
 for i in range(3):
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(i)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
 gates={"three_fresh_workers":len(workers)==3,"stable_sources":all(w["source_stable"] for w in workers),"training_success_class":all(w["training"]["selected"]=="dedup_identity_fix" and w["training"]["adopted"] and any(r["outcome_class"]=="idempotent_mint_guard" and r["task_utility"]==1 for r in w["training"]["records"]) for w in workers),"graph_policy_present_both_arms":all(w[arm]["program_present"] for w in workers for arm in ("cold","experience")),"cold_has_no_cross_family_prior":all(w["cold"]["trials"][0]["rank_trace"].get("prior_successes",0)==0 for w in workers),"transfer_consumes_cross_target_success":all(w["experience"]["trials"][0]["rank_trace"].get("prior_successes",0)>=1 and w["experience"]["trials"][0]["rank_trace"].get("target_rule")=="mrl_offer_due_once" for w in workers),"both_arms_find_task_repair":all(w[arm]["success"] for w in workers for arm in ("cold","experience")),"both_preserve_primaries":all(w[arm]["primary_preserved"] for w in workers for arm in ("cold","experience")),"independent_oracles_pass":all(w[arm]["success"] and w[arm]["trials"][-1]["task_oracle"] for w in workers for arm in ("cold","experience"))}
 summaries=[]
 for arm in ("cold","experience"):
  rows=[w[arm] for w in workers];summaries.append({"arm":arm,"trials_to_utility":[len(r["trials"]) for r in rows],"cross_target_prior_successes":[r["trials"][0]["rank_trace"].get("prior_successes",0) for r in rows],"orders":[r["candidate_order"] for r in rows],"heldout_oracle_passes":sum(r["success"] for r in rows)})
 from substrate_rs import _native
 binary=Path(_native.__file__).resolve()
 capture={"schema":"ThoughtexperimentCrossFamilyIdempotenceTransferV1","captured_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"protocol":{"workers":3,"families":["shape-axis deduplication training","recurrence-ledger offer idempotence evaluation"],"transfer":"typed CorrectionOutcome rows keyed by shared idempotent_mint_guard class","branch_backend":"native full-copy experiment"},"source_hashes":workers[0]["source_before"],"engine_fingerprint":rust_source_fingerprint(str(ROOT)),"native_binary":{"path":str(binary),"sha256":hashlib.sha256(binary.read_bytes()).hexdigest()},"workers":workers,"summary":summaries,"gates":gates}
 RAW.parent.mkdir(parents=True,exist_ok=True);RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+"\n")
 out=f"# Thoughtexperiment cross-family idempotence transfer v1 — results\n\n**Result:** {sum(gates.values())}/{len(gates)} amended confirmatory gates pass; see the [protocol amendment](THOUGHTEXPERIMENT_CROSS_FAMILY_IDEMPOTENCE_TRANSFER_V1_AMENDMENT_20261001.md).\n\nThree workers each trained on an actual shape-axis correction, then compared cold and outcome-informed ranking on fresh recurrence-ledger tasks. The recurrence task's independent oracle requires exactly one candidate-linked offer and a zero-progress closure; candidate rehearsal occurs only on full-copy branches.\n\n| Arm | Trials to oracle | Cross-target prior successes | Oracle passes |\n|---|---:|---:|---:|\n"+"".join(f"| `{s['arm']}` | {s['trials_to_utility']} | {s['cross_target_prior_successes']} | {s['heldout_oracle_passes']}/3 |\n" for s in summaries)+"\nOutcome transfer reaches the graph-authored policy across the two target rules: the cold traces have no matching class history, while each transfer trace sees the training success. However, both cold and transfer arms rank the repair first and pass in one trial. The structural-cost prior already chooses correctly, so this panel shows evidence consumption but no measured improvement in search cost or outcome. A future evaluation needs a preregistered task on which cold ranking is demonstrably suboptimal before claiming utility gain. The substrate did not invent the shared class, repair, or utility label, and record transport remains host-managed.\n\n## Artifacts\n\n- [Preregistration](THOUGHTEXPERIMENT_CROSS_FAMILY_IDEMPOTENCE_TRANSFER_V1_PREREG_20261001.md)\n- [Amendment](THOUGHTEXPERIMENT_CROSS_FAMILY_IDEMPOTENCE_TRANSFER_V1_AMENDMENT_20261001.md)\n- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_cross_family_idempotence_transfer_v1.py)\n- [Raw capture](../../../evaluation/reports/thoughtexperiment_cross_family_idempotence_transfer_v1_raw_20261001.json)\n"
 RESULT.write_text(out);print(json.dumps({"gates":gates,"summary":summaries},indent=2,sort_keys=True));return 0 if all(gates.values()) else 1
if __name__=="__main__":raise SystemExit(main())
