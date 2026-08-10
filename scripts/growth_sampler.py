#!/usr/bin/env python3
"""Sample the developmental-growth counters off a live daemon, periodically.

Measurement only: it reads the debug HTTP endpoint and appends one JSON line
per sample. It writes nothing to the graph and changes no behaviour.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request


def fetch(port: int, node_type: str, limit: int = 400) -> dict:
    url = (f"http://127.0.0.1:{port}/api/debug/graph/nodes"
           f"?type={node_type}&limit={limit}")
    with urllib.request.urlopen(url, timeout=20) as response:
        return json.loads(response.read().decode())


def sample(port: int) -> dict:
    out: dict = {"t": time.time()}
    caps = fetch(port, "EmbodiedSituatedDevelopmentalCapability")
    out["capability_total"] = caps["total"]
    attempted = []
    for node in caps["nodes"]:
        attrs = node["attrs"]
        if int(attrs.get("attempt_count") or 0) > 0:
            attempted.append({
                "id": node["id"],
                "capability": attrs.get("capability"),
                "evidence_kind": attrs.get("evidence_kind"),
                "ordinal": attrs.get("curriculum_ordinal"),
                "status": attrs.get("status"),
                "attempt": attrs.get("attempt_count"),
                "success": attrs.get("success_count"),
                "failure": attrs.get("failure_count"),
                "retention": attrs.get("retention_count"),
                "contexts": attrs.get("context_count"),
            })
    out["attempted"] = attempted
    for node_type, keys in (
        ("EmbodiedLearningSession",
         ("trial_seq", "session_status", "curriculum_ordinal")),
        ("LearningPlanStep", ("status", "curriculum_ordinal")),
        ("EnergyLedger", ("stock_units", "expenditure_units",
                          "posted_receipt_count")),
        ("EmbodiedDevelopmentReceipt",
         ("development_receipt_closed", "development_configuration_changed",
          "development_external_event", "development_receipt_seq")),
    ):
        data = fetch(port, node_type)
        out[node_type] = {
            "total": data["total"],
            "rows": [{k: n["attrs"].get(k) for k in keys}
                     for n in data["nodes"][-6:]],
        }
    for node_type in ("EmbodiedExternalTrialEvidence", "EmbodiedCausalReceipt",
                      "EmbodiedDevelopmentalContext"):
        try:
            out[node_type] = fetch(port, node_type, limit=1)["total"]
        except Exception as exc:  # noqa: BLE001 -- an absent type is a reading
            out[node_type] = f"error:{type(exc).__name__}"
    return out


def main() -> int:
    port = int(sys.argv[1])
    path = sys.argv[2]
    interval = float(sys.argv[3]) if len(sys.argv) > 3 else 120.0
    count = int(sys.argv[4]) if len(sys.argv) > 4 else 1000
    for _ in range(count):
        try:
            row = sample(port)
        except Exception as exc:  # noqa: BLE001 -- keep sampling through blips
            row = {"t": time.time(), "error": f"{type(exc).__name__}: {exc}"}
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row) + "\n")
        print(json.dumps({k: row.get(k) for k in
                          ("t", "attempted", "EmbodiedExternalTrialEvidence")}))
        sys.stdout.flush()
        time.sleep(interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
