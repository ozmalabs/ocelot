#!/usr/bin/env python3
"""Diagnostic: compare RatioInduce output with the native linear-map semantics.

This is a measurement runner, not a test. It intentionally reports the
semantic mismatch on a 3:2 aspect-ratio population and preserves engine
provenance in its JSON output.
"""
from __future__ import annotations

import json
from pathlib import Path

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from substrate.boot_core import boot_core  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402


def frame(scale: int) -> list[list[object]]:
    x, y = 2 * scale, 3 * scale
    return [["cell", 0, 0, 1], ["cell", x, 0, 1],
            ["cell", 0, y, 1], ["cell", x, y, 1]]


def extent(rows: list[list[object]], slot: int) -> int:
    values = [int(row[slot]) for row in rows]
    return max(values) - min(values)


def apply_linear_native_semantics(rows: list[list[object]], matrix: list[int]) -> list[list[object]]:
    """Mirror apply_linear_once for the two declared coordinate slots [1,2]."""
    n = 2
    mins = [min(int(r[d]) for r in rows) for d in (1, 2)]
    result = []
    for row in rows:
        out = list(row)
        v = [int(row[d]) - mins[i] for i, d in enumerate((1, 2))]
        for i, d in enumerate((1, 2)):
            out[d] = sum(matrix[i * n + j] * v[j] for j in range(n))
        result.append(out)
    return result


def main() -> int:
    substrate, agent = boot_core()
    native = rf._native_eval2(substrate)
    rf._ensure_shape_decode_loop(substrate, native, agent)
    substrate.add_node("ShapeSignature", {
        "name": "ratio_semantics_probe",
        "signature": json.dumps([frame(1)[0]]),
        "kind": "faculty", "faculty": "ratio_semantics_probe",
        "dim_types": ["pred", "coord:x", "coord:y", "val"],
    })
    population = [frame(s) for s in (1, 2, 3, 5)]
    out = native.evaluate({
        "type": "RatioInduce",
        "population": {"type": "Lit", "value": population},
        "field": "",
    }, {})

    matrix = [int(v) for v in (out.get("matrix") or [])]
    source = population[0]
    transformed = apply_linear_native_semantics(source, matrix) if matrix else None
    before_ratio = (extent(source, 2), extent(source, 1))
    after_ratio = ((extent(transformed, 2), extent(transformed, 1))
                   if transformed is not None else None)
    result = {
        "engine": provenance_line(),
        "probe": "ratioinduce_nonpow2_map_semantics",
        "planted_ratio_y_x": [3, 2],
        "population_scales": [1, 2, 3, 5],
        "explained": bool(out.get("explained")),
        "induced_ratios_flat": list(out.get("ratios") or []),
        "latent_name": out.get("latent_name"),
        "emitted_matrix": matrix,
        "source_extent_y_x": list(before_ratio),
        "apply_linear_once_semantics_replay_extent_y_x": list(after_ratio) if after_ratio else None,
        "preserves_planted_ratio": bool(after_ratio and
            after_ratio[0] * 2 == after_ratio[1] * 3),
        "interpretation": (
            "detector returns the planted ratio, but emitted matrix does not "
            "preserve/apply it under apply_linear_once semantics"
            if matrix and after_ratio and not (after_ratio[0] * 2 == after_ratio[1] * 3)
            else "no counterexample in this fixture; further semantic cases required"
        ),
    }
    path = Path("evaluation/reports/substrate_ratioinduce_semantics_probe_20260926.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    print(f"RAW: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
