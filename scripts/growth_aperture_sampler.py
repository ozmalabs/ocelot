#!/usr/bin/env python3
"""Sample the actuation aperture and the capability counters together.

Measurement only. The aperture (`measurement_frame_count` on the evidence) is
the quantity the proprioceptive success criterion turns out to depend on, so it
is sampled beside the counters it is supposed to move.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from collections import Counter


def fetch(port, node_type, limit=600):
    url = (f"http://127.0.0.1:{port}/api/debug/graph/nodes"
           f"?type={node_type}&limit={limit}")
    with urllib.request.urlopen(url, timeout=25) as response:
        return json.loads(response.read().decode())


def main() -> int:
    port, path = int(sys.argv[1]), sys.argv[2]
    interval = float(sys.argv[3]) if len(sys.argv) > 3 else 60.0
    count = int(sys.argv[4]) if len(sys.argv) > 4 else 10000
    for _ in range(count):
        try:
            ev = fetch(port, "EmbodiedExternalTrialEvidence")
            frames = Counter(n["attrs"].get("measurement_frame_count")
                             for n in ev["nodes"])
            l1 = Counter(n["attrs"].get("proprioceptive_configuration_l1_units")
                         for n in ev["nodes"])
            rc = fetch(port, "EmbodiedLearningTrialReceipt")
            changed = Counter(
                n["attrs"].get("development_configuration_changed")
                for n in rc["nodes"])
            caps = fetch(port, "EmbodiedSituatedDevelopmentalCapability")
            attempted = [
                {"id": n["id"], "kind": n["attrs"].get("evidence_kind"),
                 "status": n["attrs"].get("status"),
                 "a": n["attrs"].get("attempt_count"),
                 "s": n["attrs"].get("success_count"),
                 "f": n["attrs"].get("failure_count"),
                 "r": n["attrs"].get("retention_count"),
                 "ctx": len(n["attrs"].get("context_ids") or [])}
                for n in caps["nodes"]
                if int(n["attrs"].get("attempt_count") or 0) > 0]
            prog = fetch(port, "EmbodiedMotorProgram")
            pframes = Counter(n["attrs"].get("simulator_frames")
                              for n in prog["nodes"])
            bodies = fetch(port, "EmbodiedBodySchema")
            aperture = [{"k": n["attrs"].get("temporal_aperture_log_units"),
                         "measured": n["attrs"].get("temporal_aperture_measured")}
                        for n in bodies["nodes"]]
            eps = fetch(port, "EmbodiedDevelopmentEpisode")
            window = [{"w": n["attrs"].get("development_evidence_window"),
                       "measured": n["attrs"].get(
                           "development_evidence_window_measured"),
                       "relatum": n["attrs"].get(
                           "development_evidence_window_relatum")}
                      for n in eps["nodes"]]
            ctx = fetch(port, "EmbodiedDevelopmentalContext", limit=1)["total"]
            row = {"t": time.time(), "trials": ev["total"],
                   "receipts": rc["total"],
                   "evidence_frame_counts": dict(frames),
                   "evidence_l1": dict(l1),
                   "receipt_config_changed": dict(changed),
                   "program_simulator_frames": dict(pframes),
                   "body_aperture": aperture, "evidence_window": window,
                   "contexts_total": ctx, "attempted": attempted}
        except Exception as exc:  # noqa: BLE001 -- keep sampling through blips
            row = {"t": time.time(), "error": f"{type(exc).__name__}: {exc}"}
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row) + "\n")
        print(json.dumps(row)[:400], flush=True)
        time.sleep(interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
