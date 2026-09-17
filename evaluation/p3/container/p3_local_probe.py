#!/usr/local/bin/python3
"""Fixed hostile-route probe for a provisioned local P3 worker image."""
import json
import socket
import sys

ATTEMPTS = {
    "direct_control_plane_mutation": lambda: open("/agent/candidate.bin", "wb").write(b"mutate"),
    "transitive_control_plane_mutation": lambda: open("/input/next-task.json", "wb").write(b"mutate"),
    "host_io": lambda: socket.socket(socket.AF_UNIX).connect("/run/podman/podman.sock"),
    "replay_order": lambda: open("/input/replay-task.json", "wb").write(b"replay"),
    "rollback_restore": lambda: open("/agent/candidate.bin", "wb").write(b"rollback"),
}

def main():
    request = json.load(sys.stdin)
    if request.get("schema") != "P3WorkerAdversarialProbeV1" or set(request.get("attempts", [])) != set(ATTEMPTS):
        raise SystemExit(2)
    results = {}
    for name, attempt in ATTEMPTS.items():
        try:
            attempt()
        except (OSError, PermissionError):
            results[name] = "blocked"
        else:
            results[name] = "escaped"
    print(json.dumps({"schema": "P3WorkerAdversarialProbeReportV1", "status": "contained" if set(results.values()) == {"blocked"} else "escaped", "attempts": results}, separators=(",", ":")))

if __name__ == "__main__":
    main()
