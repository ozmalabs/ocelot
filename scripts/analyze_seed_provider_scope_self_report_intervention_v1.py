#!/usr/bin/env python3
"""Independent integrity and contrast analysis for provider-scope intervention."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/"evaluation/reports/seed_provider_scope_self_report_intervention_v1_20260927.json"
LOCK=ROOT/"evaluation/substrate_capability/seed_provider_scope_self_report_intervention_v1_lock_20260927.json"
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_SEED_PROVIDER_SCOPE_SELF_REPORT_INTERVENTION_V1_PREREG_20260927.md"
AMENDMENT=ROOT/"docs/research/engine_substrate/SUBSTRATE_SEED_PROVIDER_SCOPE_SELF_REPORT_INTERVENTION_V1_1_AMENDMENT_20260927.md"
RUNNER=ROOT/"scripts/probe_seed_provider_scope_self_report_intervention_v1.py"
OLD=ROOT/"evaluation/substrate_capability/fixtures/boot_all_before_provider_scope_20260927.py"
SCOPE=ROOT/"evaluation/substrate_capability/fixtures/boot_all_provider_scope_only_20260927.py"
OUT=ROOT/"evaluation/reports/seed_provider_scope_self_report_intervention_v1_analysis_20260927.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());rows=raw["runs"];groups={c:[r for r in rows if r["condition"]==c] for c in ("old","provider_scope_only")}
 checks={"six_workers":len(rows)==6,"six_unique_pids":len({r["pid"] for r in rows})==6,
  "three_per_condition":all(len(v)==3 for v in groups.values()),"driver_post_locks_match":raw["driver_lock"]==raw["post_run_lock"]==lock,
  "protocol_amendment_runner_fixture_hashes_match":lock["protocol_sha256"]==sha(PROTOCOL) and lock["amendment_sha256"]==sha(AMENDMENT) and lock["runner_sha256"]==sha(RUNNER) and lock["old_boot_all_sha256"]==sha(OLD) and lock["provider_scope_only_sha256"]==sha(SCOPE),
  "all_worker_source_locks_match":all(r["worker_start_lock"]==lock["source_lock"]==r["worker_end_lock"] for r in rows),
  "condition_source_hashes_match":all(r["old_boot_all_sha256"]==lock["old_boot_all_sha256"] and r["provider_scope_only_sha256"]==lock["provider_scope_only_sha256"] for r in rows),
  "within_condition_repeats":all(len({(r["route"],r["reply"],r["semantic_graph_sha256"],tuple(r["loaded_seed_ids"])) for r in v})==1 for v in groups.values())}
 summaries={}
 for c,rs in groups.items():
  ids=set(rs[0]["loaded_seed_ids"]);summaries[c]={"route":rs[0]["route"],"reply":rs[0]["reply"],"comprehension":rs[0]["comprehension"],"goal_count":rs[0]["goal_count"],"loaded_seed_count":len(ids),"loaded_seed_ids":sorted(ids),"failed_seeds":rs[0]["failed_seeds"],"graph_nodes":rs[0]["graph_nodes"],"graph_edges":rs[0]["graph_edges"],"semantic_graph_sha256":rs[0]["semantic_graph_sha256"],"replicates":len(rs)}
 old=set(summaries["old"]["loaded_seed_ids"]);new=set(summaries["provider_scope_only"]["loaded_seed_ids"])
 delta={"only_old":sorted(old-new),"only_current":sorted(new-old)}
 checks["loaded_manifest_sets_repeated"]=all(len({tuple(r["loaded_seed_ids"]) for r in v})==1 for v in groups.values())
 result={"schema_version":1,"raw_sha256":sha(RAW),"lock_sha256":sha(LOCK),"checks":checks,"all_checks_pass":all(checks.values()),"conditions":summaries,"loaded_seed_delta":delta,"claim_boundary":"A one-file boot-module contrast on one prompt, source-locked across six fresh processes. Loaded-seed differences are candidate mediators, not individually isolated causes."}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps({"output":str(OUT),"checks":checks,"all_checks_pass":result["all_checks_pass"],"conditions":{k:{x:v[x] for x in ("route","loaded_seed_count","goal_count","graph_nodes","graph_edges")} for k,v in summaries.items()},"loaded_seed_delta":{"only_old":delta["only_old"],"only_current":delta["only_current"]}},indent=2))
 if not result["all_checks_pass"]:raise SystemExit("intervention analysis gates failed")
if __name__=="__main__":main()
