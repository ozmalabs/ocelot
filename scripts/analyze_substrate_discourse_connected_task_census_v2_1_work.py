#!/usr/bin/env python3
"""Audit total work across production lifecycle writes and ordinary event settles."""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_discourse_connected_task_census_v2_1_20260926.json"
LOCK = ROOT / "evaluation/substrate_capability/discourse_connected_task_census_v2_1_lock_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_discourse_connected_task_census_v2_1_work_attribution_20260926.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


raw, lock = json.loads(RAW.read_text()), json.loads(LOCK.read_text())
checks = {
    "raw_lock_hash_matches": sha(LOCK) == raw["lock_sha256"],
    "raw_lock_record_matches": raw["locked_inputs"] == lock["locked_inputs"],
    "three_process_runner_gates_pass": all(raw["checks"].values()),
    "producer_counter_fields_present": all(
        "producer_scale_audit_counters" in cp for run in raw["runs"] for cp in run["checkpoints"]),
}
arms = []
for run in raw["runs"]:
    total = Counter()
    by_frame = defaultdict(Counter)
    producer_calls = 0
    for cp in run["checkpoints"]:
        frame = str(cp["event_frame"])
        base = cp["scale_audit_counters"]
        total.update(base)
        by_frame[frame].update(base)
        producer = cp["producer_scale_audit_counters"]
        if producer is not None:
            producer_calls += 1
            counters = producer["scale"]
            rows = producer["per_rule"]
            by_frame[frame].update(counters)
            total.update(counters)
            per_rule = Counter()
            for _, metric, count in rows:
                per_rule[metric] += count
            checks[f"{run['arm']}:producer_counter_{cp['event_index']}:candidate_per_rule_conserved"] = counters.get("cand_enum", 0) == per_rule.get("candidate_pairs", 0)
            checks[f"{run['arm']}:producer_counter_{cp['event_index']}:terms_per_rule_conserved"] = counters.get("term_evals_total", 0) == per_rule.get("term_evaluations", 0)
            checks[f"{run['arm']}:producer_counter_{cp['event_index']}:term_variants_conserved"] = counters.get("term_evals_total", 0) == sum(v for k, v in counters.items() if k.startswith("term_eval:"))
    arms.append({"arm": run["arm"], "producer_lifecycle_calls": producer_calls,
                 "ordinary_settle_candidate_pairs": sum(c["scale_audit_counters"].get("cand_enum", 0) for c in run["checkpoints"]),
                 "ordinary_settle_term_evaluations": sum(c["scale_audit_counters"].get("term_evals_total", 0) for c in run["checkpoints"]),
                 "combined_candidate_pairs": total.get("cand_enum", 0),
                 "combined_term_evaluations": total.get("term_evals_total", 0),
                 "combined_work_by_event_frame": {f: {"candidate_pairs": c.get("cand_enum", 0),
                                                       "term_evaluations": c.get("term_evals_total", 0)}
                                                  for f, c in sorted(by_frame.items())}})
checks["combined_work_equal_across_arms"] = len({(a["combined_candidate_pairs"], a["combined_term_evaluations"]) for a in arms}) == 1

result = {"schema": "substrate_discourse_connected_task_census_v2_1_work_attribution",
          "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK), "analyzer_sha256": sha(Path(__file__)),
          "checks": checks, "check_count": len(checks), "all_checks_pass": all(checks.values()),
          "arms": arms,
          "claim_boundary": "Counter reaggregation from the source-locked v2.1 run. It includes lifecycle helper closures and outer event settles; counts remain this authored ten-event fixture, not CPU instructions or a natural-task estimate."}
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"all_checks_pass": result["all_checks_pass"], "check_count": len(checks),
                  "arms": arms, "output": str(OUT)}, indent=2))
if not result["all_checks_pass"]:
    raise SystemExit(1)
