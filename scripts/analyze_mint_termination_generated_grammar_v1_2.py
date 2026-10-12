#!/usr/bin/env python3
"""Independent checks for generated finite-key syntax/native closure capture."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/mint_termination_generated_grammar_v1_2_20260926.json"
OUT=ROOT/"evaluation/reports/mint_termination_generated_grammar_v1_2_analysis_20260926.json"
ACCEPTED={"literal_null","literal_false","literal_true","literal_zero","literal_negative","literal_string","literal_unicode","empty_key","multi_attr_key","existing_matching_witness","repeated_variable_self_join","two_edge_join","three_edge_join","minted_endpoint_recursion","two_rule_interaction"}
REJECTED={"extra_rule_field","empty_match","unrestricted_mint","computed_key","nonempty_output_edge_attrs","unbound_endpoint","forward_endpoint","reused_mint_variable","unsupported_effect","edge_attr_write_conflict"}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 r=json.loads(RAW.read_text());rows={x["name"]:x for x in r["rows"]};m=r["run_manifest"];log=m["stdout_stderr_capture"];lp=ROOT/log["path"]
 checks={"exact_registered_fixture_inventory":set(rows)==ACCEPTED|REJECTED and r["case_count"]==25 and r["accepted_count"]==15 and r["rejected_count"]==10,"all_accepted_syntax_is_admitted":all(rows[n]["expected_accept"] and rows[n]["checker_accepted"] and rows[n]["passed"] for n in ACCEPTED),"accepted_native_runs_reach_fixed_point":all(rows[n].get("native_status")=="fixed_point" for n in ACCEPTED),"accepted_native_graphs_match_independent_oracle":all(rows[n].get("exact_graph_match") for n in ACCEPTED),"accepted_progress_within_static_bound":all(rows[n].get("within_bound") for n in ACCEPTED),"all_registered_rejections_are_refused":all(not rows[n]["expected_accept"] and not rows[n]["checker_accepted"] and rows[n]["passed"] for n in REJECTED),"all_case_gates_pass":r["all_checks_pass"] and r["passed_count"]==25,"source_lock_stable":r["locked_inputs"]==r["post_run_inputs"] and bool(r["lock_sha256"]),"manifest_success_and_fresh_build":m["manifest_schema"]=="substrate-run-manifest-v1" and m["exit_status"]==0 and not m["engine"]["build_is_stale"],"parent_log_hash_matches":lp.is_file() and sha(lp)==log["sha256"] and lp.stat().st_size==log["bytes"] and lp.stat().st_size>0,"native_extension_hash_matches":sha(Path(m["engine"]["native_extension_path"]))==m["engine"]["native_extension_sha256"],"required_inputs_present":all(m["explicit_inputs"].get(p,{}).get("exists") for p in ("scripts/verify_mint_termination_generated_grammar_v1_2.py","scripts/analyze_mint_termination_fragment.py","runners/dsl/src/py.rs","scripts/analyze_mint_termination_generated_grammar_v1_2.py"))}
 out={"schema_version":1,"source":str(RAW.relative_to(ROOT)),"checks":checks,"all_checks_pass":all(checks.values()),"claim_boundary":"Fifteen declared accepted fixtures and ten declared refusals over representative finite-key grammar forms; exact interpreter parity for these accepted fixtures only, not exhaustive parser equivalence or arbitrary accepted programs."}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps(out,indent=2,sort_keys=True))
 if not out["all_checks_pass"]:raise SystemExit(1)
if __name__=="__main__":main()
