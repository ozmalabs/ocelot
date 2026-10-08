#!/usr/bin/env python3
"""Retrospectively induce prompt-specific rule dependency graphs from a locked manifest."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "evaluation/reports/live_operation_scope_manifest_v1_20261003.json"
DEFAULT_OUTPUT = ROOT / "evaluation/reports/live_task_rule_slices_v1_20261003.json"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def summarize(nodes: set[int], edges: list[dict]) -> dict:
    adj = {uid: set() for uid in nodes}
    edge_count = 0
    resources = set()
    for edge in edges:
        a, b = int(edge["producer_rule_uid"]), int(edge["consumer_rule_uid"])
        if a in nodes and b in nodes:
            adj[a].add(b)
            adj[b].add(a)
            edge_count += 1
            resources.update(edge["resources"])
    components = []
    seen: set[int] = set()
    for uid in sorted(nodes):
        if uid in seen:
            continue
        seen.add(uid)
        stack = [uid]
        size = 0
        while stack:
            current = stack.pop()
            size += 1
            for other in adj[current] - seen:
                seen.add(other)
                stack.append(other)
        components.append(size)
    components.sort(reverse=True)
    return {
        "rule_count": len(nodes), "dependency_edge_records": edge_count,
        "resource_count": len(resources), "component_count": len(components),
        "component_sizes_desc": components,
        "largest_component_fraction": (components[0] / len(nodes)) if nodes else 0.0,
    }


def build(source: Path, runner: Path) -> dict:
    data = json.loads(source.read_text())
    scopes = data["per_rule_operation_scopes"]
    prompts = sorted({prompt for scope in scopes for prompt in scope["prompts"]})
    output = {
        "schema_version": 1,
        "analysis_type": "retrospective_prompt_induced_rule_dependency_slices",
        "inputs": {
            "manifest_path": str(source.relative_to(ROOT)),
            "manifest_sha256": sha(source),
            "runner_path": str(runner.relative_to(ROOT)),
            "runner_sha256": sha(runner),
        },
        "source_manifest_summary": data["summary"],
        "prompts": [],
        "claim_boundary": (
            "Prompt membership is the union of access-emitting rules across the three captured workers. "
            "These induced rule graphs are syntactic projections of the already-built aggregate manifest, "
            "not execution-time factor scopes, complete dependency graphs, learned frames, or a prevalence sample."
        ),
    }
    for prompt in prompts:
        nodes = {int(s["rule_uid"]) for s in scopes if prompt in s["prompts"]}
        absent = sorted(int(s["rule_uid"]) for s in scopes if prompt not in s["prompts"])
        output["prompts"].append({
            "prompt": prompt,
            "workers": 3,
            "observed_rule_count": len(nodes),
            "rules_absent_from_prompt": absent,
            "finite_resource_graph": summarize(nodes, data["finite_resource_dependency_edges"]),
            "conservative_broad_scope_graph": summarize(nodes, data["conservative_dependency_edges"]),
        })
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = build(args.input, Path(__file__).resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(args.output), "prompts": result["prompts"]}, indent=2))


if __name__ == "__main__":
    main()
