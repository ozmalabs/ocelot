#!/usr/bin/env python3
"""Measure ranking sensitivity to one deliberately misattributed outcome."""
from __future__ import annotations
import hashlib, importlib.util, json, os, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
RUNNER=Path(__file__).resolve()
AUTO=ROOT/"evaluation/substrate_capability/thoughtexperiment_automatic_outcome_persistence_transfer_v1.py"
RANK=ROOT/"evaluation/substrate_capability/thoughtexperiment_graph_authored_correction_rank_v1.py"
RAW=ROOT/"evaluation/reports/thoughtexperiment_outcome_contamination_v1_raw_20261001.json"
RESULT=ROOT/"docs/research/engine_substrate/THOUGHTEXPERIMENT_OUTCOME_CONTAMINATION_V1_RESULTS_20261001.md"
SOURCES=("domains/self_correct_dispatch.py","domains/self_correction.py","domains/reflective_faculty.py","domains/collapse_watch.py","domains/collapse_model.py","seeds/composer_self_correct_graph.json","seeds/composer_collapse_watch_graph.json","seeds/minting_recurrence_ledger.json","seeds/relation_vocabulary.json","seeds/composer_dispatch.json","seeds/autonomy.json","seeds/shape_decode_loop.json","substrate/boot_core.py",str(AUTO.relative_to(ROOT)),str(RANK.relative_to(ROOT)),str(RUNNER.relative_to(ROOT)))
def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES}

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
 for phrase,tag in ((["predict","COLLAPSE","of","DIVERGENCE"],f"noise-cw-{index}"),(["correct","DIVERGENCE","by","CANDIDATE"],f"noise-sc-{index}")):
  row=rf.induce_concern(agent,[phrase],name_hint=tag);grounded=rf.ground_concern(agent,[row["capability_key"]])
  if not grounded.get("grounded") or grounded.get("served_by")!="graph":raise RuntimeError("graph policy composer did not ground")
 native=rf._native_eval2(sub);rf._ensure_shape_decode_loop(sub,native,root)
 for name in ("sd_mint_quantum","sd_dedup_existing"):sub.add_node("RuleSummary",{"name":name,"from_seed":"outcome_contamination"})
 sub.add_node("SeedSummary",{"seed_id":"outcome_contamination","skippable":1.0})
 add_wave(sub,root,f"noise-{index}-A");cw.scan_and_predict(agent);native.run_rules(2000)
 add_wave(sub,root,f"noise-{index}-B");trained=dispatch.scan_and_self_correct(agent)
 if len(trained)!=1 or not trained[0]["result"].get("adopted"):raise RuntimeError("production correction training did not adopt")
 records=[sub.node(n)["attrs"] for n in sub.nodes("CorrectionOutcome")]
 if len(records)!=2:raise RuntimeError(f"expected two production outcomes, got {len(records)}")
 # Load the established task builder without modifying its source or protocol.
 spec=importlib.util.spec_from_file_location("auto_outcome_runner",AUTO);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 clean=sub.fork_full_copy_experiment();noisy=sub.fork_full_copy_experiment()
 fabricated={"target_rule":"mrl_offer_due_once","candidate_label":"episode_scoped_offer_guard","outcome_class":"episode_scoped_idempotence","candidate_digest":"deliberate_false_positive_v1","converges_in_rehearsal":True,"selected":True,"adopted":True,"task_utility":1.0,"rank_attempt_tag":"deliberate_contamination_v1"}
 noisy.add_node("CorrectionOutcome",fabricated)
 clean_result=mod.target_task(clean,root,"clean")
 noisy_result=mod.target_task(noisy,root,"contaminated")
 after=hashes()
 return {"pid":os.getpid(),"source_before":before,"source_after":after,"source_stable":before==after,"training":{"chosen":trained[0]["result"].get("chosen"),"adopted":trained[0]["result"].get("adopted"),"production_records":records},"contaminated_record":fabricated,"clean":clean_result,"contaminated":noisy_result}

def main():
 if len(sys.argv)==3 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(",",":")));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("stale native engine: "+"; ".join(stale))
 env={**os.environ,"PYTHONPATH":f"{ROOT / 'runners/dsl/python'}:{ROOT}"};workers=[]
 for i in range(3):
  proc=subprocess.run([sys.executable,str(RUNNER),"--worker",str(i)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  workers.append(json.loads(proc.stdout.strip().splitlines()[-1]))
 gates={"three_fresh_workers":len(workers)==3,"stable_sources":all(w["source_stable"] for w in workers),"production_training_persists_two":all(w["training"]["adopted"] and w["training"]["chosen"]=="dedup_identity_fix" and len(w["training"]["production_records"])==2 for w in workers),"clean_inherits_authentic_records":all(w["clean"]["history_count"]==2 and w["clean"]["history_records"]==w["training"]["production_records"] for w in workers),"contamination_is_single_declared_record":all(w["contaminated"]["history_count"]==3 and w["contaminated"]["history_records"][-1]==w["contaminated_record"] for w in workers),"clean_policy_uses_transfer":all(w["clean"]["trials"][0]["label"]=="dedup_identity_fix" and len(w["clean"]["trials"])==1 and w["clean"]["trials"][0]["offer_counts"]==[1,1] for w in workers),"noise_sensitivity_measured":all(w["contaminated"]["trials"][0]["label"]=="episode_scoped_offer_guard" and w["contaminated"]["trials"][0]["offer_counts"]==[1,0] and len(w["contaminated"]["trials"])==2 for w in workers),"both_arms_pass_oracle":all(w["clean"]["success"] and w["contaminated"]["success"] for w in workers),"branch_primary_isolation":all(w[a]["primary_preserved"] for w in workers for a in ("clean","contaminated"))}
 summary=[{"arm":a,"history":[w[a]["history_count"] for w in workers],"first_candidate":[w[a]["trials"][0]["label"] for w in workers],"first_oracle_output":[w[a]["trials"][0]["offer_counts"] for w in workers],"trials_to_success":[len(w[a]["trials"]) for w in workers]} for a in ("clean","contaminated")]
 from substrate_rs import _native
 binary=Path(_native.__file__).resolve()
 capture={"schema":"ThoughtexperimentOutcomeContaminationV1","captured_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"protocol":{"workers":3,"training":"normal scan_and_self_correct production hook","control":"authentic persisted training records only","treatment":"same records plus one declared false positive for episode_scoped_offer_guard","oracle":"one recurrence offer per candidate, zero-progress fixedpoint","branch_backend":"native full-copy experiment"},"source_hashes":workers[0]["source_before"],"engine_fingerprint":rust_source_fingerprint(str(ROOT)),"native_binary":{"path":str(binary),"sha256":hashlib.sha256(binary.read_bytes()).hexdigest()},"workers":workers,"summary":summary,"gates":gates}
 RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+"\n")
 lines=["# Thoughtexperiment outcome contamination v1 — results","",f"**Result:** {sum(gates.values())}/{len(gates)} preregistered gates pass.","","A production correction wrote two authentic outcomes. The treatment then received one deliberately misattributed positive outcome for the episode-scoped guard, whose staged-task oracle suppresses the later valid candidate. This tests sensitivity to one false positive; the perturbation is an explicit evaluation intervention, not a naturally observed record.","","| Arm | Inherited records | First candidate | First oracle output | Trials to oracle |","|---|---:|---|---|---:|"]
 lines += [f"| `{s['arm']}` | {s['history']} | {s['first_candidate']} | {s['first_oracle_output']} | {s['trials_to_success']} |" for s in summary]
 lines += ["","Interpretation is limited to this authored candidate pair and task. If the contaminated arm regresses, one false positive can overturn useful transfer under the current ranking policy; the study does not estimate how often such records arise. Both arms are required to eventually pass the independent oracle, and all rehearsal branches must preserve their primary state.","","## Artifacts","","- [Preregistration](THOUGHTEXPERIMENT_OUTCOME_CONTAMINATION_V1_PREREG_20261001.md)","- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_outcome_contamination_v1.py)","- [Raw capture](../../../evaluation/reports/thoughtexperiment_outcome_contamination_v1_raw_20261001.json)"]
 RESULT.write_text("\n".join(lines)+"\n")
 print(json.dumps({"gates":gates,"summary":summary},indent=2,sort_keys=True));return 0 if all(gates.values()) else 1
if __name__=="__main__":raise SystemExit(main())
