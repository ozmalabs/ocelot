#!/usr/bin/env python3
"""Measure transfer-ranking sensitivity across controlled outcome-noise doses."""
from __future__ import annotations
import hashlib, importlib.util, json, os, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
RUNNER=Path(__file__).resolve();AUTO=ROOT/"evaluation/substrate_capability/thoughtexperiment_automatic_outcome_persistence_transfer_v1.py"
RANK=ROOT/"evaluation/substrate_capability/thoughtexperiment_graph_authored_correction_rank_v1.py"
RAW=ROOT/"evaluation/reports/thoughtexperiment_outcome_noise_dose_response_v1_raw_20261001.json"
RESULT=ROOT/"docs/research/engine_substrate/THOUGHTEXPERIMENT_OUTCOME_NOISE_DOSE_RESPONSE_V1_RESULTS_20261001.md"
SOURCES=("domains/self_correct_dispatch.py","domains/self_correction.py","domains/reflective_faculty.py","domains/collapse_watch.py","domains/collapse_model.py","seeds/composer_self_correct_graph.json","seeds/composer_collapse_watch_graph.json","seeds/minting_recurrence_ledger.json","seeds/relation_vocabulary.json","seeds/composer_dispatch.json","seeds/autonomy.json","seeds/shape_decode_loop.json","substrate/boot_core.py",str(AUTO.relative_to(ROOT)),str(RANK.relative_to(ROOT)),str(RUNNER.relative_to(ROOT)))
ARMS=("clean","false_positive_1","false_positive_2","false_negative_1","mixed")
def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES}
def row(label,utility,tag):return {"target_rule":"mrl_offer_due_once","candidate_label":label,"outcome_class":"episode_scoped_idempotence" if label=="episode_scoped_offer_guard" else "idempotent_mint_guard","candidate_digest":f"controlled_{tag}","converges_in_rehearsal":True,"selected":True,"adopted":True,"task_utility":utility,"rank_attempt_tag":tag}

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
 for phrase,tag in ((["predict","COLLAPSE","of","DIVERGENCE"],f"noise-dose-cw-{index}"),(["correct","DIVERGENCE","by","CANDIDATE"],f"noise-dose-sc-{index}")):
  concern=rf.induce_concern(agent,[phrase],name_hint=tag);grounded=rf.ground_concern(agent,[concern["capability_key"]])
  if not grounded.get("grounded") or grounded.get("served_by")!="graph":raise RuntimeError("graph-authored policy did not ground")
 native=rf._native_eval2(sub);rf._ensure_shape_decode_loop(sub,native,root)
 for name in ("sd_mint_quantum","sd_dedup_existing"):sub.add_node("RuleSummary",{"name":name,"from_seed":"outcome_noise_dose"})
 sub.add_node("SeedSummary",{"seed_id":"outcome_noise_dose","skippable":1.0})
 add_wave(sub,root,f"noise-dose-{index}-A");cw.scan_and_predict(agent);native.run_rules(2000)
 add_wave(sub,root,f"noise-dose-{index}-B");training=dispatch.scan_and_self_correct(agent)
 if len(training)!=1 or not training[0]["result"].get("adopted"):raise RuntimeError("normal production correction did not adopt")
 authentic=[sub.node(n)["attrs"] for n in sub.nodes("CorrectionOutcome")]
 if len(authentic)!=2:raise RuntimeError("expected two authentic production outcomes")
 spec=importlib.util.spec_from_file_location("auto_outcome_runner",AUTO);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 results={}
 for arm in ARMS:
  branch=sub.fork_full_copy_experiment()
  if arm in ("false_positive_1","false_positive_2","mixed"):
   count=2 if arm=="false_positive_2" else 1
   for copy_id in range(count):branch.add_node("CorrectionOutcome",row("episode_scoped_offer_guard",1.0,f"false_positive_{index}_{arm}_{copy_id}"))
  if arm in ("false_negative_1","mixed"):
   match=[n for n in branch.nodes("CorrectionOutcome") if branch.node(n)["attrs"].get("outcome_class")=="idempotent_mint_guard" and float(branch.node(n)["attrs"].get("task_utility",0))>=1.0]
   if len(match)!=1:raise RuntimeError(f"expected one true positive class record, found {len(match)}")
   branch.set_attr(match[0],"task_utility",0.0)
  results[arm]=mod.target_task(branch,root,arm)
 return {"pid":os.getpid(),"source_before":before,"source_after":hashes(),"source_stable":before==hashes(),"training":{"chosen":training[0]["result"].get("chosen"),"adopted":training[0]["result"].get("adopted"),"authentic_records":authentic},"arms":results}

def main():
 if len(sys.argv)==3 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(",",":")));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("stale native engine: "+"; ".join(stale))
 env={**os.environ,"PYTHONPATH":f"{ROOT / 'runners/dsl/python'}:{ROOT}"};workers=[]
 for i in range(3):
  p=subprocess.run([sys.executable,str(RUNNER),"--worker",str(i)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
 gates={"three_fresh_workers":len(workers)==3,"source_hashes_stable":all(w["source_stable"] for w in workers),"production_training_authentic":all(w["training"]["adopted"] and w["training"]["chosen"]=="dedup_identity_fix" and len(w["training"]["authentic_records"])==2 for w in workers),"clean_transfer_baseline":all(w["arms"]["clean"]["history_records"]==w["training"]["authentic_records"] and w["arms"]["clean"]["trials"][0]["label"]=="dedup_identity_fix" and len(w["arms"]["clean"]["trials"])==1 for w in workers),"false_positive_doses_recorded":all(len(w["arms"]["false_positive_1"]["history_records"])==3 and len(w["arms"]["false_positive_2"]["history_records"])==4 for w in workers),"false_negative_mutation_recorded":all(len(w["arms"]["false_negative_1"]["history_records"])==2 and sum(float(x.get("task_utility",0))>=1 for x in w["arms"]["false_negative_1"]["history_records"] if x.get("outcome_class")=="idempotent_mint_guard")==0 for w in workers),"mixed_noise_recorded":all(len(w["arms"]["mixed"]["history_records"])==3 for w in workers),"all_arms_eventually_pass":all(w["arms"][a]["success"] for w in workers for a in ARMS),"all_primary_branches_preserved":all(w["arms"][a]["primary_preserved"] for w in workers for a in ARMS)}
 summary=[]
 for arm in ARMS:
  rows=[w["arms"][arm] for w in workers];first=[r["trials"][0] for r in rows]
  summary.append({"arm":arm,"history_count":[r["history_count"] for r in rows],"first_candidate":[t["label"] for t in first],"first_prior_successes":[t["rank_trace"].get("prior_successes",0) for t in first],"first_prior_failures":[t["rank_trace"].get("prior_failures",0) for t in first],"first_oracle_output":[t["offer_counts"] for t in first],"trials_to_success":[len(r["trials"]) for r in rows]})
 from substrate_rs import _native
 binary=Path(_native.__file__).resolve()
 capture={"schema":"ThoughtexperimentOutcomeNoiseDoseResponseV1","captured_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"protocol":{"workers":3,"arms":list(ARMS),"training":"production scan_and_self_correct","oracle":"one recurrence offer per candidate, zero-progress fixedpoint","branch_backend":"native full-copy experiment"},"source_hashes":workers[0]["source_before"],"engine_fingerprint":rust_source_fingerprint(str(ROOT)),"native_binary":{"path":str(binary),"sha256":hashlib.sha256(binary.read_bytes()).hexdigest()},"workers":workers,"summary":summary,"gates":gates}
 RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+"\n")
 out=["# Thoughtexperiment outcome noise dose-response v1 — results","",f"**Result:** {sum(gates.values())}/{len(gates)} preregistered gates pass.","","All conditions fork from the same production-trained primary. The false-positive dose adds one or two positive rows for the known-bad episode guard; the false-negative condition changes the genuine candidate-scoped success to zero utility; mixed noise applies both interventions. These are controlled sensitivity conditions, not natural error-rate samples.","","| Arm | History rows | First candidate | Prior successes / failures | First oracle output | Trials to success |","|---|---:|---|---|---|---:|"]
 for s in summary:out.append(f"| `{s['arm']}` | {s['history_count']} | {s['first_candidate']} | {list(zip(s['first_prior_successes'],s['first_prior_failures']))} | {s['first_oracle_output']} | {s['trials_to_success']} |")
 out += ["","Interpretation is limited to this candidate pair and task. Compare the false-positive 1/2 arms for saturation, and false-negative/mixed arms for the effect of removing reliable positive evidence. The panel neither estimates natural noise prevalence nor supports broad learning claims.","","## Artifacts","","- [Preregistration](THOUGHTEXPERIMENT_OUTCOME_NOISE_DOSE_RESPONSE_V1_PREREG_20261001.md)","- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_outcome_noise_dose_response_v1.py)","- [Raw capture](../../../evaluation/reports/thoughtexperiment_outcome_noise_dose_response_v1_raw_20261001.json)"]
 RESULT.write_text("\n".join(out)+"\n");print(json.dumps({"gates":gates,"summary":summary},indent=2,sort_keys=True));return 0 if all(gates.values()) else 1
if __name__=="__main__":raise SystemExit(main())
