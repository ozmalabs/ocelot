"""Run the graph-native humanoid balance and coordination curriculum."""
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


DEFAULT_PROTOCOL = (
    ROOT / "protocols" / "humanoid_coordination_curriculum_v1.json"
)


def run_experiment(
    protocol_path: Path = DEFAULT_PROTOCOL,
    *,
    motor_library_path: Path | None = None,
) -> dict[str, Any]:
    protocol_path = protocol_path.resolve()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    motor_library = (
        json.loads(motor_library_path.read_text(encoding="utf-8"))
        if motor_library_path is not None and motor_library_path.exists()
        else None
    )
    result = _run_arm(
        protocol,
        "directed_walk",
        motor_library=motor_library,
        motor_library_out=motor_library_path,
    )
    challenge_rows = result["curriculum"]["challenges"]
    sampled = [
        row for row in challenge_rows if float(row["sample_count"]) > 0.0
    ]
    return {
        "experiment": protocol["protocol"],
        "protocol_path": str(protocol_path.relative_to(ROOT)),
        "policy_owner": "rust_graph",
        "curriculum_owner": "rust_graph",
        "world_adapter_role": "normalized_force_transduction_only",
        "sampled_challenge_count": len(sampled),
        "challenge_count": len(challenge_rows),
        "safe_receipt_count": result["curriculum"]["safe_challenges"],
        "completed_receipt_count": result["curriculum"][
            "completed_challenges"
        ],
        "first_fall_action": result["first_fall_action"],
        "minimum_height": result["minimum_height"],
        "peak_tilt": result["peak_tilt"],
        "directed_progress": result["directed_progress"],
        "support_alternations": result["support_alternations"],
        "maximum_motor_bundle_width": result[
            "maximum_motor_bundle_width"
        ],
        "challenge_frontier": challenge_rows,
        "run": result,
    }


def run_epochs(
    protocol_path: Path,
    *,
    motor_library_path: Path,
    epochs: int,
) -> dict[str, Any]:
    if isinstance(epochs, bool) or not isinstance(epochs, int) or epochs < 1:
        raise ValueError("epochs must be a positive integer")
    runs = [
        run_experiment(
            protocol_path,
            motor_library_path=motor_library_path,
        )
        for _ in range(epochs)
    ]
    first = runs[0]
    last = runs[-1]
    return {
        "experiment": "humanoid_coordination_curriculum_epochs_v1",
        "policy_owner": "rust_graph",
        "curriculum_owner": "rust_graph",
        "epoch_count": epochs,
        "motor_library_path": str(motor_library_path),
        "epochs": runs,
        "change": {
            "directed_progress": (
                last["directed_progress"] - first["directed_progress"]
            ),
            "safe_receipts": (
                last["safe_receipt_count"] - first["safe_receipt_count"]
            ),
            "peak_tilt": last["peak_tilt"] - first["peak_tilt"],
            "support_alternations": (
                last["support_alternations"]
                - first["support_alternations"]
            ),
            "sampled_challenges": (
                last["sampled_challenge_count"]
                - first["sampled_challenge_count"]
            ),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--motor-library", type=Path)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    if args.epochs > 1:
        motor_library_path = (
            args.motor_library
            if args.motor_library is not None
            else ROOT / "results" / "humanoid_coordination_library_v1.json"
        )
        result = run_epochs(
            args.protocol,
            motor_library_path=motor_library_path,
            epochs=args.epochs,
        )
    else:
        result = run_experiment(
            args.protocol,
            motor_library_path=args.motor_library,
        )
    rendered = json.dumps(result, indent=2)
    if args.json_out is not None:
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    if not args.quiet:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
