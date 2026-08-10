"""Run the graph-native human-development-inspired motor curriculum."""
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

from scripts.jabberwock_humanoid_walk import _run_arm  # noqa: E402


DEFAULT_PROTOCOL = ROOT / "protocols" / "humanoid_developmental_curriculum_v1.json"


def run_protocol(
    protocol: dict[str, Any],
    *,
    protocol_path: Path = DEFAULT_PROTOCOL,
    motor_library_path: Path | None = None,
    update_motor_library: bool = True,
) -> dict[str, Any]:
    """Run one already-resolved experimental protocol."""
    protocol_path = protocol_path.resolve()
    motor_library = (
        json.loads(motor_library_path.read_text(encoding="utf-8"))
        if motor_library_path is not None and motor_library_path.exists()
        else None
    )
    run = _run_arm(
        protocol,
        "directed_walk",
        motor_library=motor_library,
        motor_library_out=(
            motor_library_path if update_motor_library else None
        ),
    )
    curriculum = run["curriculum"]
    stages = curriculum["developmental_stages"]
    mastered = [stage for stage in stages if stage["status"] == "mastered"]
    active = next(
        (stage for stage in stages if stage["name"] == curriculum["active_capability"]),
        None,
    )
    return {
        "experiment": protocol["protocol"],
        "protocol_path": str(protocol_path.relative_to(ROOT)),
        "policy_owner": "rust_graph",
        "curriculum_owner": "rust_graph",
        "world_adapter_role": (
            "declared_fixture_and_mechanical_sensor_transduction_only"
        ),
        "active_stage_ordinal": curriculum["stage_ordinal"],
        "active_goal": curriculum["developmental_goal"],
        "stage_transition_count": curriculum[
            "developmental_stage_transition_count"
        ],
        "demonstrated_capabilities": [stage["name"] for stage in mastered],
        "demonstrated_human_analogues": [
            stage["human_analogue"] for stage in mastered
        ],
        "demonstrated_clinical_milestones": [
            stage["human_analogue"] for stage in mastered
            if stage.get("clinical_milestone", 0) == 1
        ],
        "active_capability": curriculum["active_capability"],
        "active_human_analogue": (
            active["human_analogue"] if active is not None else "inactive"
        ),
        "active_developmental_ecology": (
            active["developmental_ecology"] if active is not None else "inactive"
        ),
        "mastery_count": curriculum["mastery_count"],
        "somatomotor_waves": curriculum.get("somatomotor_waves", {}),
        "cross_body_warm_start_count": curriculum[
            "cross_body_warm_start_count"
        ],
        "exact_body_recall_count": curriculum["exact_body_recall_count"],
        "stages": stages,
        "get_up_attempt_count": run["get_up_attempt_count"],
        "recovery_basin_transition_count": run[
            "recovery_basin_transition_count"
        ],
        "directed_progress": run["directed_progress"],
        "support_alternations": run["support_alternations"],
        "first_fall_action": run["first_fall_action"],
        "minimum_height": run["minimum_height"],
        "peak_tilt": run["peak_tilt"],
        "run": run,
    }


def run_experiment(
    protocol_path: Path = DEFAULT_PROTOCOL,
    motor_library_path: Path | None = None,
) -> dict[str, Any]:
    protocol_path = protocol_path.resolve()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    return run_protocol(
        protocol,
        protocol_path=protocol_path,
        motor_library_path=motor_library_path,
        update_motor_library=True,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument(
        "--motor-library",
        type=Path,
        help="Load and update output-null shape-indexed motor/capability memory.",
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    result = run_experiment(args.protocol, args.motor_library)
    rendered = json.dumps(result, indent=2)
    if args.json_out is not None:
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    if not args.quiet:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
