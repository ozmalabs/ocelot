"""Frozen-mechanics PMB Phase 6 runner (development and registered draw).

Python supplies instances, I/O and external scoring. Process choice remains
inside the Rust seed-rule graph. Families without an honest executable
adapter produce explicit UNSUPPORTED rows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "runners/dsl/python"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from evaluation.process_mastery import generators as gen  # noqa: E402
from evaluation.process_mastery import program_adapter  # noqa: E402
from evaluation.process_mastery.harness import Agent  # noqa: E402
from evaluation.process_mastery.scorecard import write_scorecard  # noqa: E402
import substrate_rs  # noqa: E402

PHASE = "linear-p6-v1"
LIMITS = {"max_ticks": 3, "max_steps": 100}
SEED_BLOCKS = {
    "loopover": (1_000_000, 200),
    "d4": (1_000_200, 200),
    "mechanism": (1_000_400, 200),
    "controls": (1_000_600, 100),
}


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _provenance() -> dict[str, Any]:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        commit = "unavailable"
    paths = ["evaluation/process_mastery/linear_p6_v1.py",
             "evaluation/process_mastery/analyze_linear_p6_v1.py",
             "evaluation/process_mastery/program_adapter.py",
             "evaluation/process_mastery/harness.py",
             "evaluation/process_mastery/generators.py",
             "substrate/boot_profiles.py", "seeds/cognition_on_params.json",
             "seeds/process_schema.json", "seeds/invention_operators.json",
             "seeds/invention_round.json", "seeds/invariant_miner.json",
             "seeds/process_solving.json", "tests/fixtures/mbpp/provenance.json",
             "tests/fixtures/mbpp/sanitized-mbpp.json"]
    h = hashlib.sha256()
    for rel in paths:
        h.update(rel.encode() + b"\0" + (ROOT / rel).read_bytes() + b"\0")
    engine_h = hashlib.sha256()
    for rel in ("runners/dsl/Cargo.toml", "runners/dsl/src/process_algebra.rs",
                "runners/dsl/src/term.rs", "runners/dsl/src/eval.rs"):
        path = ROOT / rel
        if path.exists():
            engine_h.update(rel.encode() + b"\0" + path.read_bytes() + b"\0")
    return {"phase": PHASE, "git_commit": commit,
            "runner_source_sha256": _hash(Path(__file__).read_bytes()),
            "profile_source_bundle_sha256": h.hexdigest(),
            "engine_source_bundle_sha256": engine_h.hexdigest(),
            "engine_binary_sha256": _hash(Path(substrate_rs.__file__).read_bytes()),
            "python": sys.version.split()[0], "limits": dict(LIMITS)}


def _loopover(seed: int, *, split: str) -> list[dict[str, Any]]:
    start = gen.loopover_scramble(2, seed, length=8)
    records = []
    for track_i in (False, True):
        profile = "track-i" if track_i else "baseline"
        agent = Agent(track_i=track_i, profile=profile)
        before_nodes = len(agent.s.nodes())
        agent.add_loopover_domain(2)
        task = agent.add_solve_task("loopover_2", start, list(range(4)),
                                    pmb_seed=seed)
        t0 = time.perf_counter()
        run = agent.run(**LIMITS)
        attrs = agent.attrs(task)
        solved = attrs.get("status") == "solved" and attrs.get("state") == attrs.get("goal")
        trial_status = ("COMPLETED" if solved else
                        "FAILED" if run["quiescent"] else "TIMEOUT")
        records.append(agent.trial_record(
            trial_status, family="a", seed=seed,
            split=split, profile=profile, task_id=f"loopover-2x2-{seed}",
            initial_state=start, goal=list(range(4)), outcome="solved" if solved else "unsolved",
            steps=attrs.get("steps"), process_trace=[str(x) for x in attrs.get("trace", [])],
            compute={"ticks": run["ticks"], "seconds": round(time.perf_counter() - t0, 6),
                     "graph_nodes_added": len(agent.s.nodes()) - before_nodes,
                     "max_steps_per_tick": LIMITS["max_steps"],
                     "quiescent": run["quiescent"]},
            observation={"state": attrs.get("state"), "status": attrs.get("status")},
            hidden_truth_sha256=None))
    return records


def _not_run(family: str, seed: int, profile: str, reason: str,
             hidden: Any = None, *, split: str) -> dict[str, Any]:
    record = Agent.trial_record("NOT_RUN", family=family, seed=seed,
                                split=split, profile=profile, reason=reason)
    if hidden is not None:
        record["scorer_hidden_sha256"] = _hash(json.dumps(
            hidden, sort_keys=True).encode())
    return record


def _family_rows(family: str, seed: int, *, split: str) -> list[dict[str, Any]]:
    if family == "loopover":
        return _loopover(seed, split=split)
    if family == "d4":
        task = gen.d4_task(seed)
        # The task world is constructed, but neither PMB arm has a grounded
        # D4 action adapter. Only a digest of the hidden transform is retained.
        return [_not_run("c", seed, profile,
                         "no registered D4 action/effect adapter",
                         task["transform"], split=split)
                for profile in ("baseline", "track-i")]
    if family == "mechanism":
        task = gen.blicket_task(seed)
        return [_not_run("b", seed, profile,
                         "no registered intervention/observation adapter",
                         task["truth"], split=split)
                for profile in ("baseline", "track-i")]
    raise ValueError(f"unknown family: {family}")


def _controls(seed_start: int, count: int) -> list[dict[str, Any]]:
    records = []
    for i in range(count):
        kind = ("malformed", "stale", "opaque")[i % 3]
        agent = Agent(track_i=True, profile="track-i", view_enabled=True)
        state = {"probe": i}
        if kind == "malformed":
            schema = agent.s.add_node("ProcessSchema", {
                "kind": "unsupported_control_kind", "params": [],
                "status": "active", "owner_agent": agent.ag,
                "domain": f"control-{i}", "source_epoch": 0,
            })
        else:
            if kind == "stale":
                source = agent.s.add_node("Program", {
                    "name": f"control-program-{i}", "owner_agent": agent.ag,
                    "source_epoch": 1, "model_epoch": 1, "frame_epoch": 0,
                    "probe_epoch": 0,
                })
                ir = {"type": "ProgSeq", "stmts": [{"type": "ProgReturn",
                      "value": {"type": "Lit", "value": 1}}]}
                root = agent.native.add_term_subgraph(ir)
                agent.native.add_edge_unchecked(source, "ir_subgraph", root, {})
                state = {"input": 1}
            else:
                source = agent.s.add_node("TransitionHypothesis", {
                    "owner_agent": agent.ag, "source_epoch": 1, "model_epoch": 1,
                    "frame_epoch": 0, "probe_epoch": 0,
                    "source_state_kind": "cold", "action_kind": "heat",
                    "successor_state_kind": "warm",
                })
            agent.run(max_ticks=20)
            schema = next(s for s in agent.schemas(f"native:{'Program' if kind == 'stale' else 'TransitionHypothesis'}")
                          if agent.attrs(s).get("realised_by") == source)
            if kind == "stale":
                agent.s.set_attr(source, "source_epoch", 2)
        before = json.dumps([agent.s.node(n)["attrs"] for n in agent.s.nodes()],
                            sort_keys=True, default=str)
        value = agent.s._inner.evaluate(
            {"type": "ProcessApply", "p": {"type": "Var", "name": "process"},
             "state": {"type": "Var", "name": "state"}},
            {"process": schema, "state": state},
        )
        after = json.dumps([agent.s.node(n)["attrs"] for n in agent.s.nodes()],
                           sort_keys=True, default=str)
        unchanged = before == after
        status = "COMPLETED" if value is None and unchanged else "FAILED"
        records.append(agent.trial_record(
            status, family="control", seed=seed_start + i, profile="track-i",
            control=f"{kind}_view_fails_closed", result=value,
            graph_unchanged=unchanged))
    return records


def _program_rows(*, split: str, ids: list[int]) -> list[dict[str, Any]]:
    records = []
    for task_id in ids:
        for track_i in (False, True):
            row = program_adapter.run_task(task_id, track_i=track_i, split=split)
            row["seed"] = task_id
            row["split"] = split
            records.append(row)
    return records


def run(*, split: str, n: int | None = None, self_check: bool = False) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    if self_check:
        records.extend(_family_rows("loopover", 0, split="development"))
        records.extend(_family_rows("d4", 200, split="development"))
        records.extend(_family_rows("mechanism", 400, split="development"))
        validation = program_adapter.load_task(554, split="validation")
        if "unsupported_reason" not in validation["task"]:
            records.extend(_program_rows(split="validation", ids=[554]))
        else:
            raise RuntimeError("self-check MBPP validation task 554 is not runnable")
        records.extend(_controls(600, 3))
    else:
        n = 200 if n is None else n
        if n != 200:
            raise ValueError("registered P6 draw fixes n=200 for each world family")
        offset = 1_000_000 if split == "heldout" else 0
        for i in range(n):
            records.extend(_family_rows("loopover", offset + i, split=split))
            records.extend(_family_rows("d4", offset + 200 + i, split=split))
            records.extend(_family_rows("mechanism", offset + 400 + i, split=split))
        records.extend(_controls(offset + 600, 100))
        from scripts import mbpp_zero_shot_baseline as mbpp
        tasks = json.loads(program_adapter.FIXTURE.read_text())
        dataset_split = "test" if split == "heldout" else "validation"
        mbpp_split = mbpp.split_tasks(tasks)[dataset_split]
        ids = [task["task_id"] for task in mbpp_split
               if mbpp.build_task_rows(mbpp._strip_code(task))[0] is not None]
        records.extend(_program_rows(split=dataset_split, ids=ids))
    seed_offset = 1_000_000 if split == "heldout" else 0
    metadata = {**_provenance(), "split": split,
                "seed_blocks": {k: {"start": v[0] - 1_000_000 + seed_offset,
                                     "count": v[1]}
                                for k, v in SEED_BLOCKS.items()},
                "dataset": program_adapter.dataset_provenance(
                    "validation" if split == "development" else "test"),
                "arms": ["baseline", "track-i"],
                "unsupported_families": {"d4": "no D4 action/effect adapter",
                                         "mechanism": "no intervention/observation adapter"},
                "self_check": self_check}
    return {"schema": "pmb-scorecard-v1", "metadata": metadata, "records": records}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("development", "heldout"), default="heldout")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    payload = run(split=args.split, n=args.n, self_check=args.self_check)
    if args.output:
        write_scorecard(args.output, metadata=payload["metadata"],
                        records=payload["records"])
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
