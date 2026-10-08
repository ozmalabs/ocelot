#!/usr/bin/env python3
"""Measure automatic correction outcome persistence into a later experiment branch."""
from __future__ import annotations
import copy,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
SOURCES=("domains/self_correct_dispatch.py","domains/self_correction.py","domains/reflective_faculty.py","domains/collapse_watch.py","domains/collapse_model.py","seeds/composer_self_correct_graph.json","seeds/composer_collapse_watch_graph.json","seeds/minting_recurrence_ledger.json","seeds/relation_vocabulary.json","seeds/composer_dispatch.json","seeds/autonomy.json","seeds/shape_decode_loop.json","substrate/boot_core.py","evaluation/substrate_capability/thoughtexperiment_graph_authored_correction_rank_v1.py","evaluation/substrate_capability/thoughtexperiment_automatic_outcome_persistence_transfer_v1.py")
RAW=ROOT/"evaluation/reports/thoughtexperiment_automatic_outcome_persistence_transfer_v1_raw_20261001.json"
RESULT=ROOT/"docs/research/engine_substrate/THOUGHTEXPERIMENT_AUTOMATIC_OUTCOME_PERSISTENCE_TRANSFER_V1_RESULTS_20261001.md"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hashes():return {n:sha(ROOT/n) for n in SOURCES}
def target_task(sub,root,arm):
 from substrate.seed_loader import manifest_for
 import domains.reflective_faculty as rf
 import domains.self_correct_dispatch as dispatch
 from domains.self_correction import _default_candidates
 sub._inner.load_seed_manifest(manifest_for("minting_recurrence_ledger"),root)
 class Agent:
  def __init__(self,s,node):self.s=s;self.inner=s._inner;self.agent=node
 agent=Agent(sub,root);native=sub._inner
 active=[(i,r) for i,r in enumerate(native.export_rules()) if r.get("name")=="mrl_offer_due_once" and r.get("active",True)]
 if not active:raise RuntimeError("mrl_offer_due_once not loaded")
 authored=copy.deepcopy(active[0][1]);faulty=copy.deepcopy(authored);faulty["where"]["items"]=[x for x in faulty["where"]["items"] if x.get("type")!="Not"]
 if not all(native.remove_rule(i) for i,_ in reversed(active)):raise RuntimeError("cannot isolate recurrence target")
 native.add_rule(faulty)
 episode=sub.add_node("MintingRecurrenceEpisode",{"mint_after_quanta":1,"integer_native":1})
 key0=f"auto-{arm}-0";candidate0=sub.add_node("PredicateRecurrenceCandidate",{"predicate":"bind","recurrence_key":key0,"structural_signature":[["relation","bind","ITEM","SLOT0",arm]],"capability_key":[key0,"X"]})
 evidence0=sub.add_node("ResidualSegmentEvidence",{"predicate":"bind","recurrence_key":key0,"structural_signature":[["relation","bind","ITEM","SLOT0",arm]],"capability_key":[key0,"X"],"segment_ordinal":0,"integer_native":1})
 sub.add_edge(root,"has_minting_recurrence_episode",episode);sub.add_edge(episode,"has_predicate_recurrence_candidate",candidate0);sub.add_edge(candidate0,"supported_by_segment",evidence0)
 cands=_default_candidates(native,"mrl_offer_due_once")
 if not {"dedup_identity_fix","episode_scoped_offer_guard"}.issubset({c["label"] for c in cands}):raise RuntimeError("recurrence candidate set incomplete")
 ordered=dispatch.rank_candidates(agent,native,cands)
 graph_before=native.graph_to_dict();rules_before=native.export_rules();trials=[];keys=[key0]
 for cand in ordered:
  branch=sub.fork_full_copy_experiment();bn=branch._inner
  target_ids=[i for i,r in enumerate(bn.export_rules()) if r.get("name")=="mrl_offer_due_once" and r.get("active",True)]
  if not target_ids or not all(bn.remove_rule(i) for i in reversed(target_ids)):raise RuntimeError("branch rule replacement failed")
  variant=(cand.get("rules") or {}).get("mrl_offer_due_once")
  if variant is not None:bn.add_rule(variant)
  progress=[int(bn.run_rules(100)) for _ in range(5)]
  key1=f"auto-{arm}-1";keys1=[*keys,key1]
  candidate1=branch.add_node("PredicateRecurrenceCandidate",{"predicate":"bind","recurrence_key":key1,"structural_signature":[["relation","bind","ITEM","SLOT1",arm]],"capability_key":[key1,"X"]})
  evidence1=branch.add_node("ResidualSegmentEvidence",{"predicate":"bind","recurrence_key":key1,"structural_signature":[["relation","bind","ITEM","SLOT1",arm]],"capability_key":[key1,"X"],"segment_ordinal":1,"integer_native":1})
  branch.add_edge(episode,"has_predicate_recurrence_candidate",candidate1);branch.add_edge(candidate1,"supported_by_segment",evidence1)
  progress.extend(int(bn.run_rules(100)) for _ in range(5));counts=[]
  for key in keys1:
   node=next(n for n in branch.nodes("PredicateRecurrenceCandidate") if branch.node(n)["attrs"].get("recurrence_key")==key)
   counts.append(len(list(branch.neighbours(node,"has_mint_offer"))))
  fixed=int(bn.run_rules(100));ok=counts==[1,1] and fixed==0
  trials.append({"label":cand["label"],"rank_trace":cand.get("_self_correction_rank_trace",{}),"offer_counts":counts,"fixedpoint_progress":fixed,"task_oracle":ok,"sweep_progress":progress})
  if ok:break
 history_records=[sub.node(n)["attrs"] for n in sub.nodes("CorrectionOutcome")]
 return {"arm":arm,"history_count":len(history_records),"history_records":history_records,"program_present":any(sub.node(p)["attrs"].get("name","").startswith("self_correct_rank_") for p in sub.nodes("Program")),"candidate_order":[c["label"] for c in ordered],"trials":trials,"success":bool(trials and trials[-1]["task_oracle"]),"primary_preserved":graph_before==native.graph_to_dict() and rules_before==native.export_rules()}

def worker(index):
 from substrate.boot_core import boot_core
 from substrate.seed_loader import manifest_for
 import domains.reflective_faculty as rf
 from domains import collapse_watch as cw
 from domains import self_correct_dispatch as dispatch
 from evaluation.substrate_capability.thoughtexperiment_graph_authored_correction_rank_v1 import add_wave
 before=hashes();sub,root=boot_core()
 for seed in ("relation_vocabulary","composer_dispatch","autonomy"):sub._inner.load_seed_manifest(manifest_for(seed),root)
 class Agent:
  def __init__(self,s,node):self.s=s;self.inner=s._inner;self.agent=node
 agent=Agent(sub,root)
 for phrase,tag in ((["predict","COLLAPSE","of","DIVERGENCE"],f"persistcw{index}"),(["correct","DIVERGENCE","by","CANDIDATE"],f"persistsc{index}")):
  row=rf.induce_concern(agent,[phrase],name_hint=tag);grounded=rf.ground_concern(agent,[row["capability_key"]])
  if not grounded.get("grounded") or grounded.get("served_by")!="graph":raise RuntimeError("graph policy composer did not ground")
 native=rf._native_eval2(sub);rf._ensure_shape_decode_loop(sub,native,root)
 for name in ("sd_mint_quantum","sd_dedup_existing"):sub.add_node("RuleSummary",{"name":name,"from_seed":"automatic_outcome_transfer"})
 sub.add_node("SeedSummary",{"seed_id":"automatic_outcome_transfer","skippable":1.0})
 add_wave(sub,root,f"automatic{index}A");cw.scan_and_predict(agent);native.run_rules(2000)
 ready=[node for node in sub.nodes("Impasse") if sub.node(node)["attrs"].get("correct_ready")]
 add_wave(sub,root,f"automatic{index}B")
 cold=sub.fork_full_copy_experiment()
 trained=dispatch.scan_and_self_correct(agent)
 if not trained:raise RuntimeError("normal scan hook did not execute")
 persisted=[sub.node(n)["attrs"] for n in sub.nodes("CorrectionOutcome")]
 warm=sub.fork_full_copy_experiment()
 cold_arm=target_task(cold,root,"cold");warm_arm=target_task(warm,root,"warm")
 after=hashes()
 return {"pid":os.getpid(),"source_before":before,"source_after":after,"source_stable":before==after,"ready_impasse_count":len(ready),"training":{"attempt_count":len(trained),"target":trained[0]["target_rule"],"chosen":trained[0]["result"].get("chosen"),"adopted":trained[0]["result"].get("adopted"),"model_final_converged":bool(trained[0]["result"].get("model_final") and trained[0]["result"]["model_final"].converged),"persisted":persisted},"cold":cold_arm,"experience":warm_arm}

def main():
 if len(sys.argv)==3 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(",",":")));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("stale native engine: "+"; ".join(stale))
 env={**os.environ,"PYTHONPATH":f"{ROOT / 'runners/dsl/python'}:{ROOT}"};workers=[]
 for i in range(3):
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(i)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
 gates={"three_fresh_workers":len(workers)==3,"stable_sources":all(w["source_stable"] for w in workers),"one_ready_training_impasse":all(w["ready_impasse_count"]==1 and w["training"]["attempt_count"]==1 and w["training"]["target"]=="sd_mint_quantum" for w in workers),"training_adopts_and_persists_outcomes":all(w["training"]["chosen"]=="dedup_identity_fix" and w["training"]["adopted"] and w["training"]["model_final_converged"] and any(x.get("outcome_class")=="idempotent_mint_guard" and x.get("task_utility")==1 for x in w["training"]["persisted"]) and any(x.get("task_utility")==0 for x in w["training"]["persisted"]) for w in workers),"cold_fork_has_no_history":all(w["cold"]["history_count"]==0 for w in workers),"trained_fork_inherits_exact_records":all(w["experience"]["history_count"]==len(w["training"]["persisted"])==2 and w["experience"]["history_records"]==w["training"]["persisted"] for w in workers),"both_rank_programs_present":all(w[a]["program_present"] for w in workers for a in ("cold","experience")),"cold_ranking_error":all(w["cold"]["trials"][0]["label"]=="episode_scoped_offer_guard" and w["cold"]["trials"][0]["offer_counts"]==[1,0] and len(w["cold"]["trials"])==2 for w in workers),"inherited_history_ranks_correct_fix":all(w["experience"]["trials"][0]["label"]=="dedup_identity_fix" and w["experience"]["trials"][0]["rank_trace"].get("prior_successes")==1 for w in workers),"experience_passes_in_one_trial":all(len(w["experience"]["trials"])==1 and w["experience"]["trials"][0]["offer_counts"]==[1,1] for w in workers),"branch_primary_isolation":all(w[a]["primary_preserved"] for w in workers for a in ("cold","experience"))}
 summaries=[{"arm":a,"trials_to_oracle":[len(w[a]["trials"]) for w in workers],"history_count":[w[a]["history_count"] for w in workers],"first_candidate":[w[a]["trials"][0]["label"] for w in workers],"first_oracle_output":[w[a]["trials"][0]["offer_counts"] for w in workers],"oracle_passes":sum(w[a]["success"] for w in workers)} for a in ("cold","experience")]
 from substrate_rs import _native
 binary=Path(_native.__file__).resolve()
 capture={"schema":"ThoughtexperimentAutomaticOutcomePersistenceTransferV1","captured_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"protocol":{"workers":3,"training":"production scan_and_self_correct persists outcome nodes","control":"fork before correction","treatment":"fork after correction from the same trained primary","task_oracle":"one recurrence offer per candidate, zero-progress fixedpoint","branch_backend":"native full-copy experiment"},"source_hashes":workers[0]["source_before"],"engine_fingerprint":rust_source_fingerprint(str(ROOT)),"native_binary":{"path":str(binary),"sha256":hashlib.sha256(binary.read_bytes()).hexdigest()},"workers":workers,"summary":summaries,"gates":gates}
 RAW.parent.mkdir(parents=True,exist_ok=True);RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+"\n")
 out=["# Thoughtexperiment automatic outcome persistence transfer v1 — results","",f"**Result:** {sum(gates.values())}/{len(gates)} preregistered gates pass.","","The production correction hook writes outcome nodes into the training primary. A cold branch forked before correction has no records; the experience branch forked afterward inherits the graph-resident success and failure records. Neither outcome nodes nor their attributes are created or transported by the evaluation harness.","","| Arm | Trials to oracle | Inherited history | First candidate | First oracle output | Oracle passes |","|---|---:|---:|---|---|---:|"]
 out += [f"| `{s['arm']}` | {s['trials_to_oracle']} | {s['history_count']} | {s['first_candidate']} | {s['first_oracle_output']} | {s['oracle_passes']}/3 |" for s in summaries]
 out += ["","The outcome written through the normal scan path changes the later branch ranking: cold evaluation first tries an episode-scoped guard and fails `[1, 0]`, then passes on trial two; the inherited record ranks the candidate-scoped repair first and passes `[1, 1]` on trial one. This demonstrates graph-resident outcome persistence and inheritance through a native thoughtexperiment fork. It remains an authored two-family demonstration with a hand-designed outcome class and task oracle, not autonomous self-improvement or natural-task generalization.","","## Artifacts","","- [Preregistration](THOUGHTEXPERIMENT_AUTOMATIC_OUTCOME_PERSISTENCE_TRANSFER_V1_PREREG_20261001.md)","- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_automatic_outcome_persistence_transfer_v1.py)","- [Raw capture](../../../evaluation/reports/thoughtexperiment_automatic_outcome_persistence_transfer_v1_raw_20261001.json)"]
 RESULT.write_text("\n".join(out)+"\n");print(json.dumps({"gates":gates,"summary":summaries},indent=2,sort_keys=True));return 0 if all(gates.values()) else 1
if __name__=="__main__":raise SystemExit(main())
