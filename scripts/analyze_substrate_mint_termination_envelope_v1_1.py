#!/usr/bin/env python3
"""Independent checks for the locked recursive-mint envelope replay."""
from __future__ import annotations
import hashlib, json, math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_mint_termination_envelope_v1_1_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_mint_termination_envelope_v1_1_analysis_20260926.json"
def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
def main() -> None:
    raw=json.loads(RAW.read_text()); records=raw["records"]; conf=raw["configuration"]
    expected={(n,r,e) for n in conf["sizes"] for r in range(conf["repeats"]) for e in ("add_node","add_node_if_absent")}
    seen={(x["size_links"],x["repeat"],x["effect"]) for x in records}
    checks={
      "complete_size_repeat_arm_factorial": len(records)==len(expected) and seen==expected,
      "unrestricted_mint_exhibits_capped_growth": all(x["status"]=="progress_budget_reached" and x["nodes_after"]>x["nodes_before"] for x in records if x["effect"]=="add_node"),
      "keyed_mint_reaches_exact_fixture_fixed_point": all(x["status"]=="fixed_point" and x["exact_bounded_state"] and x["nodes_after"]==x["expected_bounded_nodes"] and x["edges_after"]==x["expected_bounded_edges"] for x in records if x["effect"]=="add_node_if_absent"),
      "runner_semantic_gates_pass": raw["summary"]["all_checks_pass"] and all(x["status_and_state_match"] for x in records),
      "source_lock_stable": raw.get("locked_inputs")==raw.get("post_run_inputs") and bool(raw.get("lock_sha256")),
      "manifest_success_and_engine_fresh": raw.get("exit_status")==0 and raw["run_manifest"].get("manifest_schema")=="substrate-run-manifest-v1" and raw["run_manifest"].get("exit_status")==0 and not raw["run_manifest"]["engine"]["build_is_stale"],
      "parent_log_hash_matches": (lambda x: x.is_file() and digest(x)==raw["run_manifest"]["stdout_stderr_capture"]["sha256"] and x.stat().st_size==raw["run_manifest"]["stdout_stderr_capture"]["bytes"] and x.stat().st_size>0)(ROOT/raw["run_manifest"]["stdout_stderr_capture"]["path"]),
      "native_hash_matches": digest(Path(raw["run_manifest"]["engine"]["native_extension_path"]))==raw["run_manifest"]["engine"]["native_extension_sha256"],
      "timings_are_finite_nonnegative": all(math.isfinite(x["wall_time_ns"]) and math.isfinite(x["cpu_time_ns"]) and x["wall_time_ns"]>=0 and x["cpu_time_ns"]>=0 for x in records),
    }
    result={"schema_version":1,"source":str(RAW.relative_to(ROOT)),"checks":checks,"all_checks_pass":all(checks.values()),"claim_boundary":"One recursive rule fixture with three sizes and three repeats under a finite progress budget. Capped growth is not proof of nontermination; keyed deduplication is not a general weak-acyclicity or polynomial-time theorem."}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps(result,indent=2,sort_keys=True))
    if not result["all_checks_pass"]: raise SystemExit(1)
if __name__=="__main__":main()
