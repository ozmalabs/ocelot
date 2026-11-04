"""Sampling-weight controls over fixed, verified world receipts."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import random
import math
from typing import Iterable, Mapping


@dataclass(frozen=True)
class ReceiptPresentation:
    event_id: str
    type_id: str
    token_id: str
    adverse: bool
    prediction_error: bool
    coordinates: tuple[float, float, float] | None
    presentation_index: int
    presentation_weight: float


def verified_receipt_row(world, receipt, *, type_id: str, token_id: str,
                         prediction_error: bool) -> dict:
    """Build a scorer row from an actual authorized simulator receipt."""
    if not callable(getattr(world, "verify_receipt", None)) or not world.verify_receipt(receipt):
        raise ValueError("distribution panel requires a verified source receipt")
    if not receipt.action_authorized:
        raise ValueError("unauthorized world actions cannot be distribution evidence")
    return {
        "event_id": receipt.event_id, "type_id": str(type_id),
        "token_id": str(token_id), "adverse": bool(receipt.adverse_consequence),
        "prediction_error": bool(prediction_error),
        "coordinates": tuple(float(value) for value in receipt.raw_coordinates),
    }


def present_regime(receipts: Iterable[Mapping], regime: str, *, seed: int = 2810,
                   token_frequency: Mapping[str, float] | None = None) -> list[ReceiptPresentation]:
    """Assign presentation weights without cloning or rewriting evidence.

    `uniform_type` gives each observed type equal total weight. The measured
    and shuffled regimes use a separate token-frequency table, so event
    multiplicity and language frequency cannot be conflated.
    """
    if regime not in {"uniform_type", "measured_token_frequency", "shuffled_frequency"}:
        raise ValueError("unknown distribution regime")
    source = [dict(row) for row in receipts]
    if any(not row.get("event_id") or not row.get("type_id") or not row.get("token_id")
           for row in source):
        raise ValueError("distribution rows require source event, type, and token IDs")
    for row in source:
        if "coordinates" in row:
            coordinates = tuple(float(value) for value in row["coordinates"])
            if (len(coordinates) != 3 or not all(math.isfinite(value) for value in coordinates)):
                raise ValueError("geometry coordinates must contain three finite values")
            row["coordinates"] = coordinates
    if any("coordinates" in row for row in source) and not all("coordinates" in row for row in source):
        raise ValueError("geometry coordinates must be present for every source event")
    event_ids = [str(row["event_id"]) for row in source]
    if len(event_ids) != len(set(event_ids)):
        raise ValueError("receipt replay cannot become independent distribution support")
    types = sorted({str(row["type_id"]) for row in source})
    tokens = sorted({str(row["token_id"]) for row in source})
    if regime == "uniform_type":
        by_type = Counter(str(row["type_id"]) for row in source)
        weights = [1.0 / len(types) / by_type[str(row["type_id"])] for row in source]
    else:
        if token_frequency is None or any(token not in token_frequency for token in tokens):
            raise ValueError("measured token-frequency regime requires each token's frequency")
        frequencies = {token: float(token_frequency[token]) for token in tokens}
        if any(value < 0 for value in frequencies.values()):
            raise ValueError("token frequencies cannot be negative")
        if regime == "shuffled_frequency":
            shuffled = [frequencies[token] for token in tokens]
            random.Random(seed).shuffle(shuffled)
            frequencies = dict(zip(tokens, shuffled))
        events_per_token = Counter(str(row["token_id"]) for row in source)
        weights = [frequencies[str(row["token_id"])] / events_per_token[str(row["token_id"])]
                   for row in source]
    return [ReceiptPresentation(
        event_id=str(row["event_id"]), type_id=str(row["type_id"]),
        token_id=str(row["token_id"]), adverse=bool(row["adverse"]),
        prediction_error=bool(row["prediction_error"]), presentation_index=index,
        coordinates=row.get("coordinates"), presentation_weight=weights[index])
        for index, row in enumerate(source)]


def summarize_presentations(rows: Iterable[ReceiptPresentation]) -> dict:
    records = list(rows)
    unique_events = {row.event_id: row for row in records}
    by_type: dict[str, list[ReceiptPresentation]] = {}
    for row in unique_events.values():
        by_type.setdefault(row.type_id, []).append(row)
    adverse = [row for row in unique_events.values() if row.adverse]
    weighted_total = sum(row.presentation_weight for row in unique_events.values())
    weighted_error = sum(row.presentation_weight * row.prediction_error
                         for row in unique_events.values())
    adverse_weight = sum(row.presentation_weight for row in adverse)
    adverse_weighted_error = sum(row.presentation_weight * row.prediction_error for row in adverse)
    geometry_rows = [row for row in unique_events.values() if row.coordinates is not None]
    geometry = None
    if geometry_rows:
        def center(rows, weights):
            total = sum(weights)
            return tuple(sum(weight * row.coordinates[axis]
                             for row, weight in zip(rows, weights)) / total
                         for axis in range(3)) if total else None

        type_centers = []
        for values in by_type.values():
            type_centers.append(tuple(sum(row.coordinates[axis] for row in values
                                          if row.coordinates is not None)
                                      / len([row for row in values if row.coordinates is not None])
                                      for axis in range(3)))
        geometry = {
            "event_weighted_centroid": center(geometry_rows, [1.0] * len(geometry_rows)),
            "type_weighted_centroid": tuple(sum(point[axis] for point in type_centers)
                                             / len(type_centers) for axis in range(3)),
            "token_frequency_weighted_centroid": center(
                geometry_rows, [row.presentation_weight for row in geometry_rows]),
        }
    return {
        "presentation_count": len(records),
        "unique_event_count": len(unique_events),
        "unique_type_count": len(by_type),
        "event_error_rate": sum(row.prediction_error for row in unique_events.values()) / max(1, len(unique_events)),
        "type_weighted_error_rate": sum(
            sum(row.prediction_error for row in values) / len(values)
            for values in by_type.values()) / max(1, len(by_type)),
        "token_weighted_error_rate": weighted_error / weighted_total if weighted_total else None,
        "adverse_event_count": len(adverse),
        "adverse_error_rate": (sum(row.prediction_error for row in adverse) / len(adverse)
                               if adverse else None),
        "adverse_status": "measured" if adverse else "unknown_no_adverse_events",
        "adverse_token_weighted_error_rate": (adverse_weighted_error / adverse_weight
                                               if adverse_weight else None),
        "adverse_event_ids": sorted(row.event_id for row in adverse),
        "total_presentation_weight": weighted_total,
        "geometry": geometry,
    }


__all__ = ["ReceiptPresentation", "present_regime", "summarize_presentations",
           "verified_receipt_row"]
