"""Stable PMB scorecard writer; it reports records and never scores decisions."""
from __future__ import annotations

import json
from pathlib import Path

TRIAL_STATUSES = {"NOT_RUN", "UNSUPPORTED", "TIMEOUT", "FAILED", "COMPLETED"}


def write_scorecard(path, *, metadata, records):
    for record in records:
        status = record.get("status")
        if status not in TRIAL_STATUSES:
            raise ValueError(f"invalid PMB trial status {status!r}")
    payload = {
        "schema": "pmb-scorecard-v1",
        "metadata": metadata,
        "records": sorted(records, key=lambda r: (r.get("family", ""), r.get("seed", -1))),
    }
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
