#!/usr/bin/env python3
"""Sample the embodied trial pipeline's lifecycle states off a live daemon.

Measurement only. Node type names are spelled EXACTLY as the seeds mint them
(`Experiment` for the counterfactual trial, `EmbodiedResetRequest` for the
reset, `CognitiveCheckIn` with a capital I) -- querying a type that does not
exist returns a total of 0, which is indistinguishable from a drained pool and
has already produced one wrong diagnosis in this line.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from collections import Counter

TYPES = (
    "Experiment",
    "EmbodiedResetRequest",
    "EmbodiedExternalTrialRequest",
    "EmbodiedLearningTrialReceipt",
    "EmbodiedLearningCheckin",
    "EmbodiedMotorBootstrapSelection",
)


class UnknownNodeType(RuntimeError):
    """A queried node type is not minted by any seed and not present in the
    graph — so a total of 0 would be a TYPO, not a measurement."""


def known_node_types(seed_dir=None):
    """Every node type any seed can mint or declare.

    Read from the seeds rather than from the live graph, because a type that
    is real but currently unpopulated must still be queryable — the distinction
    this whole module exists to preserve is exactly "absent because nothing is
    there" versus "absent because you asked the wrong question".
    """
    import pathlib
    seed_dir = pathlib.Path(seed_dir or (
        pathlib.Path(__file__).resolve().parents[1] / "seeds"))
    types: set[str] = set()
    for path in seed_dir.glob("*.json"):
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 -- a malformed seed is not our business
            continue
        for node in manifest.get("nodes") or []:
            if isinstance(node, dict) and isinstance(node.get("type"), str):
                types.add(node["type"])
        for production in manifest.get("productions") or []:
            for side in ("src", "tgt"):
                spec = production.get(side)
                if isinstance(spec, dict) and isinstance(spec.get("type"), str):
                    types.add(spec["type"])
        for rule in manifest.get("rules") or []:
            if not isinstance(rule, dict):
                continue
            for effect in rule.get("effects") or []:
                if (isinstance(effect, list) and len(effect) >= 3
                        and effect[0] == "add_node"
                        and isinstance(effect[2], str)):
                    types.add(effect[2])
    return types


_KNOWN = None


def fetch(port, node_type, limit=800):
    """Query one node type — refusing a type no seed can produce.

    A QUERY FOR A NON-EXISTENT TYPE RETURNS total 0, WHICH IS INDISTINGUISHABLE
    FROM A REAL EMPTY POOL. That produced two wrong diagnoses in one day:
    `CognitiveCheckin` for `CognitiveCheckIn`, and
    `EmbodiedActiveResetRequest`/`CounterfactualEmbodiedTrial` for
    `EmbodiedResetRequest`/`Experiment` — each time the instrument reported a
    drained pipeline that was in fact healthy. The same defect the seeds have,
    in the tooling: an absence produced by a LOOKUP is not evidence of a
    measurement.
    """
    global _KNOWN
    if _KNOWN is None:
        _KNOWN = known_node_types()
    if node_type not in _KNOWN:
        raise UnknownNodeType(
            f"{node_type!r} is minted by no seed; a count of 0 here would be a "
            f"typo reading as an empty pool, not a measurement")
    url = (f"http://127.0.0.1:{port}/api/debug/graph/nodes"
           f"?type={node_type}&limit={limit}")
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode())


def main() -> int:
    port, path = int(sys.argv[1]), sys.argv[2]
    interval = float(sys.argv[3]) if len(sys.argv) > 3 else 60.0
    for _ in range(int(sys.argv[4]) if len(sys.argv) > 4 else 100000):
        try:
            row = {"t": time.time()}
            for node_type in TYPES:
                data = fetch(port, node_type)
                row[node_type] = {
                    "total": data["total"],
                    "status": dict(Counter(n["attrs"].get("status")
                                           for n in data["nodes"])),
                }
            ev = fetch(port, "EmbodiedExternalTrialEvidence")
            row["trials"] = ev["total"]
            row["l1"] = dict(Counter(
                n["attrs"].get("proprioceptive_configuration_l1_units")
                for n in ev["nodes"]))
            caps = fetch(port, "EmbodiedSituatedDevelopmentalCapability")
            row["attempted"] = [
                {"name": n["attrs"].get("name"),
                 "ord": n["attrs"].get("ordinal"),
                 "status": n["attrs"].get("status"),
                 "a": n["attrs"].get("attempt_count"),
                 "s": n["attrs"].get("success_count"),
                 "f": n["attrs"].get("failure_count"),
                 "r": n["attrs"].get("retention_count")}
                for n in caps["nodes"]
                if int(n["attrs"].get("attempt_count") or 0) > 0]
            steps = fetch(port, "LearningPlanStep")
            row["steps"] = dict(Counter(n["attrs"].get("status")
                                        for n in steps["nodes"]))
            row["contexts"] = fetch(
                port, "EmbodiedDevelopmentalContext", limit=1)["total"]
        except Exception as exc:  # noqa: BLE001 -- keep sampling through blips
            row = {"t": time.time(), "error": f"{type(exc).__name__}: {exc}"}
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row) + "\n")
        print(json.dumps(row)[:340], flush=True)
        time.sleep(interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
