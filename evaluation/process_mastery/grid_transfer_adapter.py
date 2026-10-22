"""Grid-transfer task adapter with explicit source and split provenance.

Only the repository's generated D4 transformation family is currently wired
to PMB. ARC and LS20 ingestion/evaluation adapters are not part of this API.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from evaluation.process_mastery.generators import D4, d4_task, split_seed


@dataclass(frozen=True)
class GridTransferTask:
    source: str
    split: str
    seed: int
    source_task_id: str
    base: tuple[tuple[int, int], ...]
    goal: tuple[tuple[int, int], ...]
    affordances: tuple[str, ...]
    transform_hidden_from_agent: bool


def task(split: str, index: int) -> GridTransferTask:
    seed = split_seed(split, index)
    generated = d4_task(seed)
    return GridTransferTask(
        source="pmb_generated_d4_v1", split=split, seed=seed,
        source_task_id=f"pmb-d4-{split}-{index:06d}",
        base=tuple(tuple(x) for x in generated["base"]),
        goal=tuple(tuple(x) for x in generated["goal"]),
        affordances=tuple(D4), transform_hidden_from_agent=True)


def agent_view(value: GridTransferTask) -> dict:
    """Return equal observable state/actions, omitting the hidden answer."""
    return {"source": value.source, "split": value.split, "seed": value.seed,
            "task_id": value.source_task_id, "base": [list(x) for x in value.base],
            "goal": [list(x) for x in value.goal],
            "affordances": list(value.affordances)}


def record(value: GridTransferTask, *, arm: str, output, exact: bool) -> dict:
    return {**asdict(value), "arm": arm, "actual_output": output,
            "exact_match": bool(exact), "target_solution_exposed": False}


def source_audit() -> dict:
    return {"supported": ["pmb_generated_d4_v1"],
            "unsupported": {"ARC": "no registered source/split ingestion adapter",
                            "LS20": "no registered source/split ingestion adapter"},
            "licenses": {"pmb_generated_d4_v1": "repository-generated; no external dataset license",
                         "ARC": None, "LS20": None}}
