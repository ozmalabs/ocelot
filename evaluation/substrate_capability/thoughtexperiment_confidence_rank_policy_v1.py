#!/usr/bin/env python3
"""Compare raw-count and smoothed graph-authored correction ranking."""
from __future__ import annotations
import hashlib, importlib.util, json, os, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
RUNNER=Path(__file__).resolve();AUTO=ROOT/"evaluation/substrate_capability/thoughtexperiment_automatic_outcome_persistence_transfer_v1.py"
RANK=ROOT/"evaluation/substrate_capability/thoughtexperiment_graph_authored_correction_rank_v1.py"
LOCK=ROOT/"evaluation/substrate_capability/thoughtexperiment_confidence_rank_policy_v1_lock_20261001.json"
RAW=ROOT/"evaluation/reports/thoughtexperiment_confidence_rank_policy_v1_raw_20261001.json"
RESULT=ROOT/"docs/research/engine_substrate/THOUGHTEXPERIMENT_CONFIDENCE_RANK_POLICY_V1_RESULTS_20261001.md"
SOURCES=("docs/research/engine_substrate/THOUGHTEXPERIMENT_CONFIDENCE_RANK_POLICY_V1_PREREG_20261001.md","domains/self_correct_dispatch.py","domains/self_correction.py","domains/reflective_faculty.py","domains/collapse_watch.py","domains/collapse_model.py","seeds/composer_self_correct_graph.json","seeds/composer_collapse_watch_graph.json","seeds/minting_recurrence_ledger.json","seeds/relation_vocabulary.json","seeds/composer_dispatch.json","seeds/autonomy.json","seeds/shape_decode_loop.json","substrate/boot_core.py",str(AUTO.relative_to(ROOT)),str(RANK.relative_to(ROOT)),str(RUNNER.relative_to(ROOT)))
ARMS=("raw_count","smoothed_mean")
def sha(path):return "sha256:"+hashlib.sha256(Path(path).read_bytes()).hexdigest()
def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES}
def row(label,utility,tag):return {"target_rule":"mrl_offer_due_once","candidate_label":label,"outcome_class":"episode_scoped_idempotence" if label=="episode_scoped_offer_guard" else "idempotent_mint_guard","candidate_digest":f"controlled_{tag}","converges_in_rehearsal":True,"selected":True,"adopted":True,"task_utility":utility,"rank_attempt_tag":tag}

def _attr(key):return {"type":"Attr","node":{"type":"Var","name":"x"},"key":key}

def _smoothed_program():
 source={"type":"Filter","source":{"type":"NodesOfType","node_type":"CorrectionCandidate"},"var_name":"x","predicate":{"type":"Eq","a":_attr("attempt_tag"),"b":{"type":"Var","name":"tag"}}}
 posterior={"type":"Div","a":{"type":"Plus","items":[_attr("prior_successes"),{"type":"Lit","value":1.0}]},"b":{"type":"Plus","items":[_attr("prior_successes"),_attr("prior_failures"),{"type":"Lit","value":2.0}]}}
 score={"type":"Plus","items":[{"type":"Minus","a":{"type":"Lit","value":1.0},"b":posterior},{"type":"Times","items":[{"type":"Lit","value":0.000001},_attr("cost")]}]}
 return {"type":"Argmin","source":source,"var_name":"x","value":score,"default":None}

def _install_smoothed_program(branch):
 found=[]
 for node in branch.nodes("Program"):
  attrs=branch.node(node)["attrs"]
  if str(attrs.get("name","")).startswith("self_correct_rank_"):
   branch.set_attr(node,"program",json.dumps(_smoothed_program(),sort_keys=True,separators=(",",":")));found.append(node)
 if len(found)!=1:raise RuntimeError(f"expected one graph rank Program, got {len(found)}")
 return str(branch.node(found[0])["attrs"].get("name"))

def worker(index):
 from substrate.boot_core import boot_core
 from substrate.seed_loader import manifest_for
 import domains.reflective_faculty as rf
 import domains.self_correct_dispatch as dispatch
 from domains import collapse_watch as cw
 from evaluation.substrate_capability.thoughtexperiment_graph_authored_correction_rank_v1 import add_wave
 before=hashes();sub,root=boot_core()
 for seed in ("relation_vocabulary","composer_dispatch","autonomy"):sub._inner.load_seed_manifest(manifest_for(seed),root)
 class Agent:
  def __init__(self,s,node):self.s=s;self.inner=s._inner;self.agent=node
 agent=Agent(sub,root)
 for phrase,tag in ((["predict","COLLAPSE","of","DIVERGENCE"],f"confidence-cw-{index}"),(["correct","DIVERGENCE","by","CANDIDATE"],f"confidence-sc-{index}")):
  concern=rf.induce_concern(agent,[phrase],name_hint=tag);grounded=rf.ground_concern(agent,[concern["capability_key"]])
  if not grounded.get("grounded") or grounded.get("served_by")!="graph":raise RuntimeError("graph-authored policy did not ground")
 native=rf._native_eval2(sub);rf._ensure_shape_decode_loop(sub,native,root)
 for name in ("sd_mint_quantum","sd_dedup_existing"):sub.add_node("RuleSummary",{"name":name,"from_seed":"confidence_rank_policy"})
 sub.add_node("SeedSummary",{"seed_id":"confidence_rank_policy","skippable":1.0})
 add_wave(sub,root,f"confidence{index}A");cw.scan_and_predict(agent);native.run_rules(2000)
 add_wave(sub,root,f"confidence{index}B");training=dispatch.scan_and_self_correct(agent)
 if len(training)!=1 or not training[0]["result"].get("adopted"):raise RuntimeError("production correction training did not adopt")
 authentic=[sub.node(n)["attrs"] for n in sub.nodes("CorrectionOutcome")]
 if len(authentic)!=2:raise RuntimeError("expected two authentic production outcomes")
 primary_graph_before=native.graph_to_dict();primary_rules_before=native.export_rules()
 contaminated=sub.fork_full_copy_experiment()
 positive=row("episode_scoped_offer_guard",1.0,f"unverified_positive_{index}")
 contaminated.add_node("CorrectionOutcome",positive)
 spec=importlib.util.spec_from_file_location("auto_outcome_runner",AUTO);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 probe=contaminated.fork_full_copy_experiment();calibration=mod.target_task(probe,root,f"calibration-{index}")
 first=calibration["trials"][0]
 if first["label"]!="episode_scoped_offer_guard" or first["offer_counts"]!=[1,0]:raise RuntimeError("independent calibration oracle failed to expose bad first choice")
 negative={"target_rule":"mrl_offer_due_once","candidate_label":"episode_scoped_offer_guard","outcome_class":"episode_scoped_idempotence","candidate_digest":(first.get("rank_trace") or {}).get("candidate_digest",""),"converges_in_rehearsal":False,"selected":True,"adopted":False,"task_utility":0.0,"rank_attempt_tag":(first.get("rank_trace") or {}).get("attempt_tag",""),"verified_by_independent_task_oracle":True,"oracle_offer_counts":first["offer_counts"]}
 contaminated.add_node("CorrectionOutcome",negative)
 history=[contaminated.node(n)["attrs"] for n in contaminated.nodes("CorrectionOutcome")]
 results={}
 policy_name=None
 for arm in ARMS:
  branch=contaminated.fork_full_copy_experiment()
  if arm=="smoothed_mean":
   programs=[n for n in branch.nodes("Program") if branch.node(n)["attrs"].get("name","").startswith("self_correct_rank_")]
   if len(programs)!=1:raise RuntimeError("graph rank Program missing or ambiguous")
   branch.set_attr(programs[0],"program",json.dumps(_smoothed_program(),sort_keys=True,separators=(",",":")))
   policy_name=branch.node(programs[0])["attrs"].get("name")
  results[arm]=mod.target_task(branch,root,f"{arm}-{index}")
 primary_unchanged=native.graph_to_dict()==primary_graph_before and native.export_rules()==primary_rules_before
 return {"pid":os.getpid(),"source_before":before,"source_after":hashes(),"source_stable":before==hashes(),"training":{"chosen":training[0]["result"].get("chosen"),"adopted":training[0]["result"].get("adopted"),"authentic_records":authentic},"positive":positive,"calibration":{"first_label":first["label"],"offer_counts":first["offer_counts"],"trials":calibration["trials"]},"verified_negative":negative,"shared_history":history,"arms":results,"confidence_program_name":policy_name,"primary_unchanged":primary_unchanged}

def main():
 if len(sys.argv)==3 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(",",":")));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("stale native engine: "+"; ".join(stale))
 env={**os.environ,"PYTHONPATH":f"{ROOT / 'runners/dsl/python'}:{ROOT}"};workers=[]
 for i in range(3):
  p=subprocess.run([sys.executable,str(RUNNER),"--worker",str(i)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
 source_lock=json.loads(LOCK.read_text());locked=all(sha(ROOT/p)==h for p,h in source_lock["sources"].items())
 from substrate_rs import _native
 binary=Path(_native.__file__).resolve()
 negative_ok=all(w["verified_negative"]["verified_by_independent_task_oracle"] and w["verified_negative"]["oracle_offer_counts"]==[1,0] for w in workers)
 gates={"three_fresh_workers":len({w["pid"] for w in workers})==3,"source_hashes_stable":all(w["source_stable"] for w in workers),"source_native_lock":locked and sha(binary)==source_lock["native_binary"]["sha256"],"production_training_authentic":all(w["training"]["adopted"] and w["training"]["chosen"]=="dedup_identity_fix" and len(w["training"]["authentic_records"])==2 for w in workers),"calibration_exposes_bad_candidate":all(w["calibration"]["first_label"]=="episode_scoped_offer_guard" and w["calibration"]["offer_counts"]==[1,0] for w in workers),"negative_record_oracle_verified":negative_ok,"arms_share_identical_evidence":all(w["arms"]["raw_count"]["history_records"]==w["arms"]["smoothed_mean"]["history_records"]==w["shared_history"] for w in workers),"raw_policy_repeats_bad_first_choice":all(w["arms"]["raw_count"]["trials"][0]["label"]=="episode_scoped_offer_guard" and w["arms"]["raw_count"]["trials"][0]["offer_counts"]==[1,0] and len(w["arms"]["raw_count"]["trials"])==2 for w in workers),"smoothed_policy_selects_good_first":all(w["arms"]["smoothed_mean"]["trials"][0]["label"]=="dedup_identity_fix" and w["arms"]["smoothed_mean"]["trials"][0]["offer_counts"]==[1,1] and len(w["arms"]["smoothed_mean"]["trials"])==1 for w in workers),"both_final_oracles_pass":all(w["arms"][a]["success"] for w in workers for a in ARMS),"primary_isolation":all(w["primary_unchanged"] and all(w["arms"][a]["primary_preserved"] for a in ARMS) for w in workers)}
 summary=[{"policy":a,"first_candidate":[w["arms"][a]["trials"][0]["label"] for w in workers],"first_oracle_output":[w["arms"][a]["trials"][0]["offer_counts"] for w in workers],"trials_to_success":[len(w["arms"][a]["trials"]) for w in workers]} for a in ARMS]
 capture={"schema":"ThoughtexperimentConfidenceRankPolicyV1","captured_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"protocol":{"workers":3,"training":"production scan_and_self_correct","policies":list(ARMS),"treatment":"branch-local graph Program for Beta(1,1) smoothed mean","verified_negative":"independent recurrence oracle [1,0]"},"source_hashes":workers[0]["source_before"],"engine_fingerprint":rust_source_fingerprint(str(ROOT)),"native_binary":{"path":str(binary),"sha256":sha(binary)},"lock_sha256":sha(LOCK),"workers":workers,"summary":summary,"gates":gates}
 RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"gates":gates,"summary":summary,"raw":str(RAW)},indent=2,sort_keys=True));return 0 if all(gates.values()) else 1
if __name__=="__main__":raise SystemExit(main())
