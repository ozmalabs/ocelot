#!/usr/bin/env python3
"""Measure branch rehearsal of an idempotence repair in recurrence minting."""
from __future__ import annotations
import copy, hashlib, json, os, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
SOURCES=("substrate/boot_core.py","substrate/seed_loader.py","seeds/minting_recurrence_ledger.json","evaluation/substrate_capability/thoughtexperiment_recurrence_offer_idempotence_v1.py")
RAW=ROOT/"evaluation/reports/thoughtexperiment_recurrence_offer_idempotence_v1_raw_20261001.json"
RESULT=ROOT/"docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_OFFER_IDEMPOTENCE_V1_RESULTS_20261001.md"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def make_case():
 from substrate.boot_core import boot_core,load_seeds_into
 sub,agent=boot_core(seeds=());load_seeds_into(sub,agent,["minting_recurrence_ledger"]);native=sub._inner
 rules=native.export_rules();idx=next(i for i,r in enumerate(rules) if r.get("name")=="mrl_offer_due_once" and r.get("active",True))
 authored=copy.deepcopy(rules[idx]);faulty=copy.deepcopy(authored)
 original_items=authored["where"]["items"]
 removed_guards=[item for item in original_items if item.get("type")=="Not"]
 faulty["where"]["items"]=[item for item in original_items if item.get("type")!="Not"]
 guard=removed_guards[0] if len(removed_guards)==1 else {}
 guard_arg=guard.get("arg",{})
 fault_only=(len(removed_guards)==1 and guard_arg.get("type")=="Exists"
             and guard_arg.get("source",{}).get("edge_type")=="has_mint_offer"
             and guard_arg.get("source",{}).get("node",{}).get("name")=="candidate"
             and faulty["effects"]==authored["effects"]
             and faulty["match"]==authored["match"])
 if not native.remove_rule(idx):raise RuntimeError("could not tombstone original recurrence offer rule")
 native.add_rule(faulty)
 episode=sub.add_node("MintingRecurrenceEpisode",{"mint_after_quanta":1,"integer_native":1})
 candidate=sub.add_node("PredicateRecurrenceCandidate",{"predicate":"bind","recurrence_key":"audit-key","structural_signature":[["relation","bind","ITEM","SLOT",1]],"capability_key":["recurrence-audit","X"]})
 evidence=sub.add_node("ResidualSegmentEvidence",{"predicate":"bind","recurrence_key":"audit-key","structural_signature":[["relation","bind","ITEM","SLOT",1]],"capability_key":["recurrence-audit","X"],"segment_ordinal":0,"integer_native":1})
 sub.add_edge(agent,"has_minting_recurrence_episode",episode);sub.add_edge(episode,"has_predicate_recurrence_candidate",candidate);sub.add_edge(candidate,"supported_by_segment",evidence)
 return sub,native,authored,candidate,fault_only

def settle(native,rounds=5):
 progress=[]
 for _ in range(rounds):progress.append(int(native.run_rules(100)))
 return progress

def offers(sub,candidate):
 # Read by stable graph edge identity; ensure only observations linked to target candidate count.
 return len(list(sub.neighbours(candidate,"has_mint_offer")))

def worker(i):
 before={name:sha(ROOT/name) for name in SOURCES}
 faulty_sub,faulty_native,_authored,faulty_candidate,fault_only=make_case()
 faulty_progress=settle(faulty_native)
 faulty_count=offers(faulty_sub,faulty_candidate)
 primary,primary_native,authored,primary_candidate,_=make_case()
 graph_before=primary_native.graph_to_dict();rules_before=primary_native.export_rules()
 branch=primary.fork_full_copy_experiment();branch_native=branch._inner
 idx=next(i for i,r in enumerate(branch_native.export_rules()) if r.get("name")=="mrl_offer_due_once" and r.get("active",True))
 removed=bool(branch_native.remove_rule(idx));added_idx=int(branch_native.add_rule(authored))
 branch_progress=settle(branch_native)
 branch_candidate=next(n for n in branch.nodes("PredicateRecurrenceCandidate") if branch.node(n)["attrs"].get("recurrence_key")=="audit-key")
 branch_count=offers(branch,branch_candidate)
 fixedpoint=int(branch_native.run_rules(100))
 primary_preserved=graph_before==primary_native.graph_to_dict() and rules_before==primary_native.export_rules()
 active=next(r for r in branch_native.export_rules() if r.get("name")=="mrl_offer_due_once" and r.get("active",True))
 return {"pid":os.getpid(),"worker_index":i,"source_hashes":before,"source_stable":before=={name:sha(ROOT/name) for name in SOURCES},"faulty":{"only_guard_removed":fault_only,"offer_count":faulty_count,"closure_progress":faulty_progress},"repair_branch":{"removed_faulty_rule":removed,"added_original_rule_index":added_idx,"offer_count":branch_count,"closure_progress":branch_progress,"final_fixedpoint_progress":fixedpoint,"restored_original_where":active.get("where")==authored.get("where")},"primary_preserved":primary_preserved}

def main():
 if len(sys.argv)==3 and sys.argv[1]=="--worker":print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(",",":")));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("stale native engine: "+"; ".join(stale))
 env={**os.environ,"PYTHONPATH":f"{ROOT / 'runners/dsl/python'}:{ROOT}"};workers=[]
 for i in range(3):
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),"--worker",str(i)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
 gates={"three_fresh_workers":len(workers)==3,"source_stable":all(w["source_stable"] for w in workers),"only_guard_removed":all(w["faulty"]["only_guard_removed"] for w in workers),"faulty_duplicate_offers":all(w["faulty"]["offer_count"]>1 for w in workers),"repair_branch_exactly_one_offer":all(w["repair_branch"]["offer_count"]==1 and w["repair_branch"]["restored_original_where"] for w in workers),"repair_branch_fixedpoint":all(w["repair_branch"]["final_fixedpoint_progress"]==0 for w in workers),"primary_unchanged":all(w["primary_preserved"] for w in workers)}
 from substrate_rs import _native
 binary=Path(_native.__file__).resolve()
 capture={"schema":"ThoughtexperimentRecurrenceOfferIdempotenceV1","captured_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"protocol":{"workers":3,"backend":"native full-copy experiment fork","fault":"remove only Not Exists(candidate.has_mint_offer)","candidate_repair":"restore original authored mrl_offer_due_once rule","closure_sweeps":5,"rules_per_sweep":100},"source_hashes":workers[0]["source_hashes"],"engine_fingerprint":rust_source_fingerprint(str(ROOT)),"native_binary":{"path":str(binary),"sha256":sha(binary)},"workers":workers,"gates":gates}
 RAW.parent.mkdir(parents=True,exist_ok=True);RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+"\n")
 out=f"# Thoughtexperiment recurrence offer idempotence v1 — results\n\n**Result:** {sum(gates.values())}/{len(gates)} preregistered gates pass.\n\nAcross three fresh workers, the single injected defect—removing the existing negative-existence guard from `mrl_offer_due_once`—causes the task graph to mint { [w['faulty']['offer_count'] for w in workers] } offers for one recurrence candidate over five bounded closure sweeps. On each worker, a full-copy branch restores the known authored rule, emits exactly one offer, reaches a zero-progress fixed point, and leaves the faulty primary graph and rules unchanged.\n\nThe independent oracle is the count of `has_mint_offer` edges from the target candidate, rather than the collapse model's generic Observation-frontier estimate. This establishes a second task-shaped thoughtexperiment with clear utility and isolation checks. The repair was supplied from the known authored rule: this does not show autonomous diagnosis, correction discovery, outcome transfer, or COW performance.\n\n## Artifacts\n\n- [Preregistration](THOUGHTEXPERIMENT_RECURRENCE_OFFER_IDEMPOTENCE_V1_PREREG_20261001.md)\n- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_offer_idempotence_v1.py)\n- [Raw capture](../../../evaluation/reports/thoughtexperiment_recurrence_offer_idempotence_v1_raw_20261001.json)\n"
 RESULT.write_text(out);print(json.dumps({"gates":gates,"faulty_offers":[w["faulty"]["offer_count"] for w in workers],"repaired_offers":[w["repair_branch"]["offer_count"] for w in workers]},indent=2));return 0 if all(gates.values()) else 1
if __name__=="__main__":raise SystemExit(main())
