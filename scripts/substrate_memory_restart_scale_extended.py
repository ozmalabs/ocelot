#!/usr/bin/env python3
"""Extended record-count envelope reusing the locked scale-v1 child protocol."""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import substrate_memory_restart_scale as base  # noqa: E402

SIZES = (10_000, 50_000)
REPEATS = 3


def main() -> None:
    results = []
    started = time.perf_counter()
    for count in SIZES:
        for repeat in range(REPEATS):
            with tempfile.TemporaryDirectory(prefix=f"ocelot-memory-scale-{count}-") as temp:
                store = Path(temp) / "records"
                store.mkdir()
                t0 = time.perf_counter()
                write = base.run_child("writer", store, count)
                read = base.run_child("reader", store, count)
                results.append({"count": count, "repeat": repeat + 1,
                                "write": write, "read": read,
                                "two_process_wall_seconds": time.perf_counter() - t0})
    payload = {"probe": "substrate-memory-restart-scale-extended-v1",
               "sizes": list(SIZES), "repeats": REPEATS,
               "total_wall_seconds": time.perf_counter() - started,
               "results": results}
    out = ROOT / "evaluation/reports/substrate_memory_restart_scale_extended_20260925.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
