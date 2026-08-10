#!/usr/bin/env python3
"""Measure cold versus retained developmental mastery receipt counts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from scripts.jabberwock_humanoid_developmental_curriculum import (  # noqa: E402
    run_protocol,
)
from scripts.jabberwock_somatomotor_wave_ablation import (  # noqa: E402
    _arm_summary,
)
from scripts.jabberwock_somatomotor_wave_matrix import (  # noqa: E402
    library_mastery_receipts,
    mastery_receipts,
    rediscovery_summary,
)


DEFAULT_PROTOCOL = ROOT / "protocols" / "humanoid_developmental_smoke_v1.json"


def run_retention(
    protocol_path: Path = DEFAULT_PROTOCOL,
    *,
    library_path: Path,
) -> dict[str, Any]:
    protocol_path = protocol_path.resolve()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    protocol.setdefault("curriculum", {})["somatomotor_waves"] = True
    if library_path.exists():
        raise FileExistsError(
            f"refusing to contaminate cold retention source: {library_path}"
        )
    cold = run_protocol(
        protocol,
        protocol_path=protocol_path,
        motor_library_path=library_path,
    )
    cold_receipts = library_mastery_receipts(library_path)
    source_hash = hashlib.sha256(library_path.read_bytes()).hexdigest()
    retained = run_protocol(
        protocol,
        protocol_path=protocol_path,
        motor_library_path=library_path,
        update_motor_library=False,
    )
    if hashlib.sha256(library_path.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("retained run mutated its cold source library")
    return {
        "experiment": "somatomotor_wave_retained_rediscovery_v1",
        "protocol_path": str(protocol_path.relative_to(ROOT)),
        "design": {
            "same_engine_revision": True,
            "same_body_fixture_and_seed": True,
            "cold_library_immutable_during_retained_run": True,
            "memory_output_authority": 0,
            "fresh_receipt_required_for_remastery": True,
        },
        "cold": {
            **_arm_summary(cold),
            "reported_mastery_receipts": mastery_receipts(cold),
            "consolidated_library_mastery_receipts": cold_receipts,
        },
        "retained": {
            **_arm_summary(retained),
            "mastery_receipts": mastery_receipts(retained),
            "exact_body_recall_count": retained["exact_body_recall_count"],
            "cross_body_warm_start_count": retained[
                "cross_body_warm_start_count"
            ],
        },
        "rediscovery": rediscovery_summary(
            cold_receipts,
            mastery_receipts(retained),
        ),
        "cold_library": {
            "path": str(library_path),
            "sha256": source_hash,
            "capability_count": len(cold_receipts),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--library-out", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    result = run_retention(
        args.protocol,
        library_path=args.library_out.resolve(),
    )
    rendered = json.dumps(result, indent=2)
    if args.json_out is not None:
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    if not args.quiet:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
