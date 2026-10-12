#!/usr/bin/env python3
"""Locked fail-closed checker and native parity probe for finite-key closure."""
from __future__ import annotations
import hashlib, json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"runners/dsl/python"))
from substrate_run_manifest import capture_run_manifest, finish_console_capture, start_console_capture
from analyze_mint_termination_fragment import self_check
from substrate_rs import _native
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_FINITE_KEY_CHECKER_HARDENING_V1_1_PROTOCOL_20260926.md"
LOCK=ROOT/"evaluation/substrate_capability/mint_termination_checker_hardening_v1_1_lock_20260926.json"
OUT=ROOT/"evaluation/reports/mint_termination_checker_hardening_v1_1_20260926.json"
RUN_ID="mint-termination-checker-hardening-v1-1-20260926"
FILES=("scripts/verify_mint_termination_checker_hardening_v1_1.py","scripts/analyze_mint_termination_checker_hardening_v1_1.py","scripts/analyze_mint_termination_fragment.py","scripts/substrate_run_manifest.py","docs/research/engine_substrate/SUBSTRATE_FINITE_KEY_CHECKER_HARDENING_V1_1_PROTOCOL_20260926.md","runners/dsl/src/py.rs","runners/dsl/src/rewrite.rs","runners/dsl/src/substrate.rs","runners/dsl/python/substrate_rs/_native.build.json")
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def lock_inputs():
 return {"sha256":{p:sha(ROOT/p) for p in FILES},"native_extension_sha256":sha(Path(_native.__file__).resolve()),"commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()}
def main():
 if sys.argv[1:]==["--lock"]:
  print(json.dumps({"locked_inputs":lock_inputs()},indent=2,sort_keys=True));return 0
 started=datetime.now(timezone.utc).isoformat();log=start_console_capture(RUN_ID);locked=lock_inputs()
 if not LOCK.is_file() or json.loads(LOCK.read_text()).get("locked_inputs")!=locked:raise SystemExit("missing or stale checker hardening lock")
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit(f"native build stale: {stale}")
 print("checker hardening locked inputs:",len(FILES),"explicit files",flush=True)
 fixture=self_check();fixtures=fixture["fixtures"]
 expected={"recursive_finite_key":True,"recursive_fresh_node":False,"computed_key":False,"replacement_effect":False,"unsupported_condition_clause":False,"edge_type_is_not_binding":False,"preexisting_edge_attribute_replacement":False,"edge_endpoint_missing_from_node_inventory":False,"duplicate_initial_edge_fact":False,"duplicate_initial_node_id":False,"invalid_rule_specs_object":False,"invalid_rule_specs_string":False,"invalid_initial_edges_object":False,"invalid_initial_edges_null":False,"isolated_initial_node_counted":True}
 fixture_gate=len(fixtures)==len(expected) and all(fixtures[k]["accepted"] is v for k,v in expected.items())
 rule={"name":"recursive_finite_key","match":[["x","link","y"]],"effects":[["add_node_if_absent","w","Witness",{"tag":"shared"}],["add_edge","y","link","w",{}]]}
 s=_native.Substrate(); rid=s.add_rule(rule); access_raw=s.rule_access_sets()[rid]
 access={"reads":access_raw[3],"term_edge_reads":access_raw[4],"writes":access_raw[5],"reads_any":access_raw[6],"writes_any":access_raw[7]}
 expected_access={"reads":["edge:link","type:Witness"],"term_edge_reads":[],"writes":["attr:tag","edge:link","type:Witness"],"reads_any":False,"writes_any":False}
 empty=s.run_rules_report(100,False);a=s.add_node("Seed");b=s.add_node("Seed");s.add_edge_unchecked(a,"link",b);run=s.run_rules_report(100,False)
 graph=s.graph_to_dict();nodes={n["id"] for n in graph["nodes"]};edges={(e["src"],e["type"],e["tgt"]) for e in graph["edges"]}
 expected_edges={(int(a.value),"link",int(b.value)),(int(b.value),"link",2),(2,"link",2)}
 native={"rule_index":rid,"access":access,"expected_access":expected_access,"empty_report":empty,"triggered_report":run,"node_count":len(nodes),"edge_count":len(edges),"expected_edges_present":expected_edges<=edges,"graph":graph}
 native_gate=access==expected_access and empty["status"]=="fixed_point" and run["status"]=="fixed_point" and run["progress_steps"]==2 and len(nodes)==3 and len(edges)==3 and expected_edges<=edges
 post=lock_inputs();log_ref=finish_console_capture(log);status=0 if fixture_gate and native_gate and post==locked else 1
 manifest=capture_run_manifest(run_id=RUN_ID,runner="scripts/verify_mint_termination_checker_hardening_v1_1.py",protocol_files=(str(PROTOCOL.relative_to(ROOT)),str(LOCK.relative_to(ROOT))),source_files=tuple(p for p in FILES if p.startswith("runners/"))+ ("scripts/analyze_mint_termination_fragment.py","scripts/substrate_run_manifest.py"),analysis_files=("scripts/analyze_mint_termination_checker_hardening_v1_1.py",),started_utc=started,exit_status=status,stdout_stderr_capture=log_ref)
 result={"schema_version":1,"run_id":RUN_ID,"locked_inputs":locked,"post_run_inputs":post,"lock_sha256":sha(LOCK),"checker":{"fixture_count":len(fixtures),"expected_outcomes":expected,"fixtures":fixture,"gate":fixture_gate},"native":{"gate":native_gate,**native},"run_manifest":manifest,"exit_status":status}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps({"fixture_gate":fixture_gate,"native_gate":native_gate,"exit_status":status},sort_keys=True));return status
if __name__=="__main__":raise SystemExit(main())
