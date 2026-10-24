#!/usr/bin/env python3
"""Write the fixed non-efficacy schedule/config seed for P27."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEED = {
    "schema": "scheduled_learning_state_seed_v1",
    "phase": "p27-scheduled-learning-v1",
    "arms": ["frozen_ancestor", "evidence_selection_only",
             "process_search_only", "combined"],
    "checkpoints": ["g0", "g1", "g2", "g3"],
    "cumulative_primitive_work_thresholds": [0, 1000, 2000, 4000],
    "cumulative_source_exposure_thresholds": [0, 0, 0, 0],
    "max_graph_bytes": 2000000,
    "max_native_rule_steps": 250000,
    "required_counters": ["primitive_work", "source_exposure",
                           "native_rule_steps", "graph_bytes",
                           "budget_debits", "task_world_accesses"],
    "capture_statuses": ["initial", "progress", "no_change", "search_failed",
                         "no_candidate_qualified", "authorization_pending", "error"],
    "heldout_feedback": False,
    "scheduled_capture_authorizes_actions": False,
}


def main() -> None:
    path = ROOT / "seeds/scheduled_learning_state.json"
    payload = json.dumps(SEED, indent=2, sort_keys=True) + "\n"
    path.write_text(payload)
    print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
