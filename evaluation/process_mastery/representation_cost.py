"""Mechanical canonical description-cost encoding for P11 evidence records.

This module serializes candidate evidence only. Candidate selection and
adoption stay in the Rust graph rules.
"""
from __future__ import annotations

import json


REQUIRED_PACKAGE_FIELDS = frozenset({
    "basis", "grain", "aperture", "latent_schema", "model", "parameters",
    "forward_map", "inverse_map", "exceptions", "decoder",
    "retained_residuals", "lost_residuals", "escape_residuals",
})


def canonical_package_bytes(package: dict) -> bytes:
    missing = REQUIRED_PACKAGE_FIELDS - package.keys()
    if missing:
        raise ValueError(f"incomplete representation package: {sorted(missing)}")
    return json.dumps(package, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def package_description_bits(package: dict) -> int:
    return 8 * len(canonical_package_bytes(package))


def residual_code_bits(residuals: list[dict], *, bits_per_record: int) -> int:
    if bits_per_record <= 0:
        raise ValueError("residual code must have positive fixed cost")
    return len(residuals) * bits_per_record


def total_training_bits(package: dict, residuals: list[dict], *, bits_per_record: int) -> int:
    return package_description_bits(package) + residual_code_bits(
        residuals, bits_per_record=bits_per_record)
