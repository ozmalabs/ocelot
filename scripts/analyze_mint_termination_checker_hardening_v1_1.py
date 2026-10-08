#!/usr/bin/env python3
"""Independent audit of checker hardening and native parser parity capture."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/mint_termination_checker_hardening_v1_1_20260926.json"
OUT=ROOT/"evaluation/reports/mint_termination_checker_hardening_v1_1_analysis_20260926.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 r=json.loads(RAW.read_text());log=r["run_manifest"]["stdout_stderr_capture"];lp=ROOT/log["path"];f=r["checker"]["fixtures"]["fixtures"]
 checks={"malformed_rule_and_edge_containers_rejected":all(not f[k]["accepted"] for k in ("invalid_rule_specs_object","invalid_rule_specs_string","invalid_initial_edges_object","invalid_initial_edges_null")),"positive_finite_key_fixture_preserved":f["recursive_finite_key"]["accepted"],"all_registered_checker_outcomes_match":r["checker"]["gate"] and r["checker"]["fixture_count"]==15,"native_access_contract_exact":r["native"]["access"]==r["native"]["expected_access"],"native_parser_and_runtime_fixed_point":r["native"]["gate"] and r["native"]["triggered_report"]["status"]=="fixed_point" and r["native"]["triggered_report"]["progress_steps"]==2,"exact_native_graph":r["native"]["node_count"]==3 and r["native"]["edge_count"]==3 and r["native"]["expected_edges_present"],"pre_post_lock_equal":r["locked_inputs"]==r["post_run_inputs"],"manifest_success_and_fresh_build":r["exit_status"]==0 and r["run_manifest"]["exit_status"]==0 and not r["run_manifest"]["engine"]["build_is_stale"],"parent_log_hash_matches":lp.is_file() and sha(lp)==log["sha256"] and lp.stat().st_size==log["bytes"] and lp.stat().st_size>0,"native_extension_hash_matches":sha(Path(r["run_manifest"]["engine"]["native_extension_path"]))==r["run_manifest"]["engine"]["native_extension_sha256"],"required_explicit_inputs_present":all(r["run_manifest"]["explicit_inputs"].get(p,{}).get("exists") for p in ("scripts/analyze_mint_termination_fragment.py","runners/dsl/src/py.rs","scripts/analyze_mint_termination_checker_hardening_v1_1.py"))}
 o={"schema_version":1,"source":str(RAW.relative_to(ROOT)),"checks":checks,"all_checks_pass":all(checks.values()),"claim_boundary":"Malformed top-level checker inputs are rejected, one accepted recursive finite-key fixture remains native-loadable and settles exactly. This does not validate every accepted syntax combination or prove a broader termination theorem."}
 OUT.write_text(json.dumps(o,indent=2,sort_keys=True)+"\n");print(json.dumps(o,indent=2,sort_keys=True))
 if not o["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
