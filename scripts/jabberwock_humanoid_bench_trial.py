"""Run the graph-native humanoid learner on official HumanoidBench H1."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from domains.humanoid_bench_world import HumanoidBenchWorld
from scripts.jabberwock_humanoid_walk import (
    _configuration,
    _run_arm,
)


DEFAULT_PROTOCOL = ROOT / "protocols" / "humanoid_bench_h1_walk_v1.json"


def run_experiment(
    protocol_path: Path,
    *,
    simulator_root: Path,
) -> dict[str, Any]:
    protocol_path = protocol_path.resolve()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    environment_id = str(protocol["environment_id"])

    def world_factory(configuration, seed):
        return HumanoidBenchWorld(
            configuration,
            simulator_root=simulator_root,
            environment_id=environment_id,
            seed=seed,
        )

    runs = {
        mode: _run_arm(
            protocol,
            mode,
            world_factory=world_factory,
        )
        for mode in protocol["locomotion"]["modes"]
    }
    walking = runs["directed_walk"]
    tonic = runs["tonic_posture_control"]
    evaluation = protocol["evaluation"]
    return {
        "experiment": protocol["protocol"],
        "protocol_path": str(protocol_path.relative_to(ROOT)),
        "simulator": protocol["simulator"],
        "environment_id": environment_id,
        "benchmark_revision": walking["benchmark"]["revision"],
        "policy_owner": "rust_graph",
        "joint_count": walking["non_tonic_actuator_count"] // 2,
        "opaque_actuator_count": walking["actuator_count"],
        "physics_time_step_seconds": _configuration(protocol).time_step,
        "walking": walking,
        "tonic_control": tonic,
        "paired_effect": {
            "directed_progress_advantage": (
                walking["directed_progress"] - tonic["directed_progress"]
            ),
            "walking_passed": (
                walking["first_fall_action"] is None
                and not walking["benchmark"]["terminated"]
                and walking["directed_progress"]
                >= float(evaluation["minimum_directed_progress_metres"])
                and abs(walking["lateral_offset"])
                <= float(
                    evaluation["maximum_final_lateral_drift_metres"]
                )
            ),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--simulator-root", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    result = run_experiment(
        args.protocol,
        simulator_root=args.simulator_root,
    )
    rendered = json.dumps(result, indent=2)
    if args.json_out is not None:
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    if not args.quiet:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
