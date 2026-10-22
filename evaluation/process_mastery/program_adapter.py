"""PMB family-e adapter for the repository's existing MBPP synthesis loop.

This module is a mechanical dataset/runner/scorer boundary.  Candidate
selection stays in ``domains.prog_synthesis`` and its native seed rules.
Held-out assertions are retained by this adapter and never passed to the
agent or written into its graph.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "runners" / "dsl" / "python", ROOT / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from domains import prog_synthesis as psy  # noqa: E402
from domains import prog_chunk_growth as pcg  # noqa: E402
from evaluation.process_mastery import harness  # noqa: E402
from scripts import mbpp_zero_shot_baseline as mbpp  # noqa: E402

FIXTURE = ROOT / "tests/fixtures/mbpp/sanitized-mbpp.json"
PROVENANCE = ROOT / "tests/fixtures/mbpp/provenance.json"


def dataset_provenance(split: str = "test") -> dict[str, Any]:
    raw = FIXTURE.read_bytes()
    return {
        **json.loads(PROVENANCE.read_text()),
        "fixture": str(FIXTURE.relative_to(ROOT)),
        "fixture_sha256": hashlib.sha256(raw).hexdigest(),
        "split": {"test": "test task_id 11..510 (vendored subset)",
                  "validation": "validation task_id 511..600 (vendored subset)"}[split],
        "revealed_rule": "first parseable test_list assertion",
        "held_out_rule": "remaining parseable test_list assertions",
    }


def load_task(task_id: int, *, split: str = "test") -> dict[str, Any]:
    """Return only public prompt/revealed rows and a detached scorer record."""
    tasks = json.loads(FIXTURE.read_text())
    tasks_for_split = mbpp.split_tasks(tasks)[split]
    task = next((t for t in tasks_for_split if t["task_id"] == task_id), None)
    if task is None:
        raise KeyError(f"task_id {task_id} is not in the frozen MBPP test split")
    task = mbpp._strip_code(task)
    spec, report = mbpp.build_task_rows(task)
    public = {"task_id": task_id, "prompt": task["prompt"]}
    if spec is None:
        public["unsupported_reason"] = report["outcome"]
        scorer = {"held_out_rows": [], "report": report}
    else:
        public["revealed_rows"] = spec["revealed_rows"]
        scorer = {"held_out_rows": spec["held_out_rows"], "report": report}
    return {"task": public, "scorer": scorer, "split": split}


def _graph_has_heldout(agent, held_out_rows: list[dict[str, Any]]) -> bool:
    """Defensive audit that serialized held-out rows do not appear in graph attrs."""
    graph = json.dumps([agent.s.node(n)["attrs"] for n in agent.s.nodes()],
                       sort_keys=True, default=str)
    return any(json.dumps(row, sort_keys=True, default=str) in graph
               for row in held_out_rows)


def run_task(task_id: int, *, track_i: bool, split: str = "test") -> dict[str, Any]:
    """Run one frozen test task through a real PMB arm and the native solver."""
    bundle = load_task(task_id, split=split)
    task, scorer = bundle["task"], bundle["scorer"]
    profile = "track-i" if track_i else "baseline"
    start = time.perf_counter()
    agent = harness.Agent(track_i=track_i, profile=profile)
    graph_nodes_before = len(agent.s.nodes())
    if "unsupported_reason" in task:
        return agent.trial_record("UNSUPPORTED", family="e", task_id=task_id,
                                   profile=profile, reason=task["unsupported_reason"],
                                   dataset=dataset_provenance(split))

    # The identical pre-existing synthesis rules are enabled in both arms;
    # only the declared Track-I closure differs between profiles.
    psy.ensure_program_synthesis(agent.s, agent.native, agent.ag)
    pcg.install_mined_chunks(agent.s)
    examples = [(row["inputs"], row["expected"])
                for row in task["revealed_rows"]]
    try:
        result = psy.synthesize_from_request(agent.s, agent.ag, task["prompt"], examples)
    except Exception as exc:  # preserve runner failures as measured outcomes
        return agent.trial_record(
            "FAILED", family="e", task_id=task_id, profile=profile,
            reason=f"runner_exception:{type(exc).__name__}",
            compute={"seconds": time.perf_counter() - start,
                     "graph_nodes_added": len(agent.s.nodes()) - graph_nodes_before},
            dataset=dataset_provenance(split))
    hidden_leak = _graph_has_heldout(agent, scorer["held_out_rows"])
    if hidden_leak:
        return agent.trial_record("FAILED", family="e", task_id=task_id,
                                  profile=profile, reason="heldout_graph_leak")

    status = result.get("status")
    compute = {"seconds": round(time.perf_counter() - start, 6),
               "attempts": result.get("attempts"),
               "solver_budget": result.get("budget"),
               "rungs": result.get("rungs"),
               "graph_nodes_added": len(agent.s.nodes()) - graph_nodes_before}
    record = {
        "family": "e", "task_id": task_id, "profile": profile,
        "dataset": dataset_provenance(split), "split_report": scorer["report"],
        "candidate_program": result.get("ir") if status == "accepted" else None,
        "candidate_node": (str(result.get("program"))
                           if status == "accepted" and result.get("program") is not None
                           else None),
        "solver_status": status, "construction": result.get("construction"),
        "compute": compute, "heldout_rows_scored": len(scorer["held_out_rows"]),
        "evidence_boundary": "held-out rows remain in adapter scorer; not in agent graph",
    }
    if status == "accepted":
        record["external_outcome"] = mbpp.holdout_verdict(
            result["ir"], scorer["held_out_rows"])
        trial_status = "COMPLETED" if record["external_outcome"]["all_ok"] else "FAILED"
    elif status is None:
        record["external_outcome"] = {"status": "NOT_RECOGNIZED"}
        trial_status = "UNSUPPORTED"
    else:
        record["external_outcome"] = {"status": "NO_CANDIDATE", "solver_status": status}
        trial_status = "FAILED"
    return agent.trial_record(trial_status, **record)


def register(agent: harness.Agent) -> None:
    """Register family-e's explicit adapter on an already declared PMB arm."""
    agent.adapters["program"] = lambda _agent, _ignored, task, **kw: run_task(
        int(task["task_id"]), track_i=_agent.track_i, **kw)

