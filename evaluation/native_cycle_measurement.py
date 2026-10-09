"""Bounded native-cycle measurement and replay check for Phase 7.

This module deliberately measures the Rust substrate boundary only.  It does
not import conversation, topic, discourse, or production modules.  Profiles
are bounded graph-authored workloads, so the observed transitions are made by
the native cycle rather than by a Python loop.
"""
from __future__ import annotations

from dataclasses import dataclass
import argparse
import json
import platform
import resource
import statistics
import time
from typing import Any

from substrate.world_adapter import WorldAdapter


SCHEMA = "native-cycle-measurement-v3"
PROFILES = (
    "fast", "deep", "recovery", "long_dialogue", "dense_graph",
    "ambiguity", "repeated_gaps", "extended_dialogue", "high_ambiguity",
    "graph_growth", "phase3_async", "phase4_deliberation",
    "phase5_recurrence", "phase6_production",
)
_PROFILE_SIZE = {
    "fast": 1,
    "deep": 24,
    "recovery": 12,
    "long_dialogue": 32,
    # Twelve candidates, each with three native-visible neighbourhood edges.
    "dense_graph": 12,
    # Eight competing evidence-bearing candidates in one native arbitration
    # neighbourhood.  The measurement observes native transitions; it does
    # not choose a winner in Python.
    "ambiguity": 8,
    # Eight recurrent gap nodes, each with detect and repair transitions.
    "repeated_gaps": 8,
    # Larger bounded loads for the Phase 7E resource-envelope increment.
    "extended_dialogue": 96,
    "high_ambiguity": 32,
    "graph_growth": 48,
    # Graph-authored workload profiles corresponding to the Phase 3–6
    # cognitive surfaces.  These names describe the workload contract, not a
    # Python implementation of those faculties.
    "phase3_async": 16,
    "phase4_deliberation": 12,
    "phase5_recurrence": 18,
    "phase6_production": 20,
}
_PROFILE_LIMITS = {
    profile: {"steps": 512, "nodes": 64, "edges": 64}
    for profile in PROFILES
}
_PROFILE_LIMITS.update({
    "extended_dialogue": {"steps": 512, "nodes": 128, "edges": 128},
    "high_ambiguity": {"steps": 512, "nodes": 64, "edges": 96},
    "graph_growth": {"steps": 512, "nodes": 64, "edges": 160},
    "phase3_async": {"steps": 512, "nodes": 32, "edges": 32},
    "phase4_deliberation": {"steps": 512, "nodes": 32, "edges": 32},
    "phase5_recurrence": {"steps": 512, "nodes": 32, "edges": 32},
    "phase6_production": {"steps": 512, "nodes": 32, "edges": 32},
})
_RSS_ABSOLUTE_OBSERVABILITY_LIMIT = 1024 * 1024 * 1024
# The execution plan's resident-memory budget is <200 MiB. Measure workload
# growth rather than the host process's inherited baseline, while retaining
# absolute RSS fields for observability.
_RSS_GROWTH_LIMIT = 200 * 1024 * 1024


def _current_rss_bytes() -> int:
    """Read current resident memory without inheriting process-wide high water.

    ``ru_maxrss`` is a useful fallback, but it is a cumulative process high
    water mark: a preceding retrieval/fixture test can make an otherwise
    bounded native profile fail.  The native envelope needs the resident state
    at this boundary, so prefer the kernel's current ``VmRSS`` measurement.
    """
    try:
        for line in open("/proc/self/status", encoding="utf-8"):
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        pass
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (
        1 if platform.system() == "Darwin" else 1024
    ))


def _edge(agent: WorldAdapter, src: Any, edge_type: str, tgt: Any) -> None:
    try:
        agent.inner.add_edge_unchecked(src, edge_type, tgt, {})
    except TypeError:
        agent.inner.add_edge_unchecked(src, edge_type, tgt)


def _probe(profile: str = "fast") -> WorldAdapter:
    """Create a bounded graph-authored native workload for one profile."""
    if profile not in PROFILES:
        raise ValueError(f"unknown native measurement profile: {profile}")
    agent = WorldAdapter(seeds=())
    root = agent.s.add_node("Phase7ANativeRoot", {})
    size = _PROFILE_SIZE[profile]
    if profile == "fast":
        probe = agent.s.add_node("Phase7ANativeProbe", {"ran": 0})
        _edge(agent, root, "has_phase7a_probe", probe)
        _add_transition(agent, "phase7_native_fast", root, probe, "ran", 0, 1)
    elif profile == "deep":
        previous = root
        for index in range(size):
            node = agent.s.add_node("Phase7NativeDepth", {"stage": 0})
            _edge(agent, previous, "has_phase7a_depth", node)
            _add_transition(agent, f"phase7_native_depth_{index:02d}", previous, node, "stage", 0, 1)
            previous = node
    elif profile == "recovery":
        for index in range(size):
            node = agent.s.add_node("Phase7NativeRecovery", {"state": 0})
            _edge(agent, root, "has_phase7a_recovery", node)
            _add_transition(agent, f"phase7_native_recovery_detect_{index:02d}", root, node, "state", 0, 1)
            _add_transition(agent, f"phase7_native_recovery_close_{index:02d}", root, node, "state", 1, 2)
    elif profile == "ambiguity":
        for index in range(size):
            candidate = agent.s.add_node(
                "Phase7AmbiguousCandidate",
                {"state": 0, "ordinal": index, "evidence": 1},
            )
            _edge(agent, root, "has_phase7a_ambiguity_candidate", candidate)
            _edge(agent, candidate, "has_phase7a_ambiguity_context", root)
        _add_ambiguity_transition(agent)
    elif profile == "repeated_gaps":
        for index in range(size):
            gap = agent.s.add_node(
                "Phase7RepeatedGap",
                {"state": 0, "ordinal": index, "recurrence": 2},
            )
            _edge(agent, root, "has_phase7a_repeated_gap", gap)
        _add_repeated_gap_transition(agent, "phase7_native_gap_detect", 0, 1)
        _add_repeated_gap_transition(agent, "phase7_native_gap_repair", 1, 2)
    elif profile == "high_ambiguity":
        for index in range(size):
            candidate = agent.s.add_node(
                "Phase7HighAmbiguityCandidate",
                {"state": 0, "ordinal": index, "evidence": 1},
            )
            _edge(agent, root, "has_phase7a_high_ambiguity_candidate", candidate)
            _edge(agent, candidate, "has_phase7a_high_ambiguity_context", root)
        _add_high_ambiguity_transition(agent)
    elif profile == "graph_growth":
        for index in range(size):
            candidate = agent.s.add_node(
                "Phase7GraphGrowthCandidate", {"resolved": 0, "ordinal": index}
            )
            _edge(agent, root, "has_phase7a_growth_candidate", candidate)
            _edge(agent, root, "has_phase7a_growth_context", candidate)
            _edge(agent, candidate, "has_phase7a_growth_backlink", root)
        for edge_type in (
            "has_phase7a_growth_candidate",
            "has_phase7a_growth_context",
            "has_phase7a_growth_backlink",
        ):
            _add_dense_transition(agent, f"phase7_native_growth_{edge_type}", edge_type)
    elif profile == "extended_dialogue":
        for index in range(size):
            event = agent.s.add_node(
                "Phase7ExtendedDialogueEvent", {"processed": 0, "ordinal": index}
            )
            _edge(agent, root, "has_phase7a_extended_dialogue_event", event)
        _add_extended_dialogue_transition(agent)
    elif profile == "phase3_async":
        _add_phase_workload(
            agent, root, size, "Phase3AsyncResidual", "has_phase3_async_residual",
            "state", ((0, 1), (1, 2)),
        )
    elif profile == "phase4_deliberation":
        _add_phase_workload(
            agent, root, size, "Phase4DeliberationCandidate", "has_phase4_candidate",
            "state", ((0, 1), (1, 2), (2, 3)),
        )
    elif profile == "phase5_recurrence":
        _add_phase_workload(
            agent, root, size, "Phase5RecurrenceIdentity", "has_phase5_identity",
            "state", ((0, 1), (1, 2), (2, 3)),
        )
    elif profile == "phase6_production":
        _add_phase_workload(
            agent, root, size, "Phase6ProductionSurface", "has_phase6_surface",
            "state", ((0, 1), (1, 2)),
        )
    else:
        if profile == "dense_graph":
            for index in range(size):
                candidate = agent.s.add_node("Phase7DenseCandidate", {"resolved": 0, "ordinal": index})
                _edge(agent, root, "has_phase7a_dense_candidate", candidate)
                _edge(agent, root, "has_phase7a_dense_context", candidate)
                _edge(agent, candidate, "has_phase7a_dense_backlink", root)
            for edge_type in (
                "has_phase7a_dense_candidate",
                "has_phase7a_dense_context",
                "has_phase7a_dense_backlink",
            ):
                _add_dense_transition(agent, f"phase7_native_dense_{edge_type}", edge_type)
            return agent
        for index in range(size):
            event = agent.s.add_node("Phase7NativeDialogueEvent", {"processed": 0, "ordinal": index})
            _edge(agent, root, "has_phase7a_dialogue_event", event)
            _add_transition(agent, f"phase7_native_dialogue_{index:02d}", root, event, "processed", 0, 1)
    return agent


def _add_transition(agent: WorldAdapter, name: str, source: Any, target: Any,
                    key: str, before: int, after: int) -> None:
    """Add one native rule; all workload decisions remain graph-authored."""
    edge_type = {
        "ran": "has_phase7a_probe",
        "stage": "has_phase7a_depth",
        "state": "has_phase7a_recovery",
        "processed": "has_phase7a_dialogue_event",
    }[key]
    agent.inner.add_rule({
        "name": name,
        "area": "measurement",
        "order": 0,
        "latency_class": "soft_realtime",
        "match": [["source", edge_type, "target"]],
        "where": {
            "type": "Eq",
            "a": {"type": "Attr", "node": {"type": "Var", "name": "target"}, "key": key},
            "b": {"type": "Lit", "value": before},
        },
        "effects": [["set_attr", "target", key, after]],
    })


def _add_dense_transition(agent: WorldAdapter, name: str, edge_type: str) -> None:
    """Add a native transition for one edge in a dense graph neighbourhood."""
    agent.inner.add_rule({
        "name": name,
        "area": "measurement",
        "order": 0,
        "latency_class": "soft_realtime",
        "match": [["source", edge_type, "target"]],
        "where": {
            "type": "Eq",
            "a": {"type": "Attr", "node": {"type": "Var", "name": "target"}, "key": "resolved"},
            "b": {"type": "Lit", "value": 0},
        },
        "effects": [["set_attr", "target", "resolved", 1]],
    })


def _add_ambiguity_transition(agent: WorldAdapter) -> None:
    """Advance all competing candidates through a native-visible state."""
    agent.inner.add_rule({
        "name": "phase7_native_ambiguity_observe",
        "area": "measurement",
        "order": 0,
        "latency_class": "soft_realtime",
        "match": [["source", "has_phase7a_ambiguity_candidate", "target"]],
        "where": {
            "type": "Eq",
            "a": {"type": "Attr", "node": {"type": "Var", "name": "target"}, "key": "state"},
            "b": {"type": "Lit", "value": 0},
        },
        "effects": [["set_attr", "target", "state", 1]],
    })


def _add_high_ambiguity_transition(agent: WorldAdapter) -> None:
    """Advance a larger competing set through one native observation."""
    agent.inner.add_rule({
        "name": "phase7_native_high_ambiguity_observe",
        "area": "measurement",
        "order": 0,
        "latency_class": "soft_realtime",
        "match": [["source", "has_phase7a_high_ambiguity_candidate", "target"]],
        "where": {
            "type": "Eq",
            "a": {"type": "Attr", "node": {"type": "Var", "name": "target"}, "key": "state"},
            "b": {"type": "Lit", "value": 0},
        },
        "effects": [["set_attr", "target", "state", 1]],
    })


def _add_extended_dialogue_transition(agent: WorldAdapter) -> None:
    """Process an extended event set through one graph-authored native rule."""
    agent.inner.add_rule({
        "name": "phase7_native_extended_dialogue",
        "area": "measurement",
        "order": 0,
        "latency_class": "soft_realtime",
        "match": [["source", "has_phase7a_extended_dialogue_event", "target"]],
        "where": {
            "type": "Eq",
            "a": {"type": "Attr", "node": {"type": "Var", "name": "target"}, "key": "processed"},
            "b": {"type": "Lit", "value": 0},
        },
        "effects": [["set_attr", "target", "processed", 1]],
    })


def _add_repeated_gap_transition(agent: WorldAdapter, name: str, before: int, after: int) -> None:
    """Advance every recurrent gap through the same native lifecycle."""
    agent.inner.add_rule({
        "name": name,
        "area": "measurement",
        "order": 0,
        "latency_class": "soft_realtime",
        "match": [["source", "has_phase7a_repeated_gap", "target"]],
        "where": {
            "type": "Eq",
            "a": {"type": "Attr", "node": {"type": "Var", "name": "target"}, "key": "state"},
            "b": {"type": "Lit", "value": before},
        },
        "effects": [["set_attr", "target", "state", after]],
    })


def _add_phase_workload(agent: WorldAdapter, root: Any, size: int,
                        node_type: str, edge_type: str, key: str,
                        transitions: tuple[tuple[int, int], ...]) -> None:
    """Install one graph-authored Phase 3–6 workload.

    The workload is deliberately expressed as graph nodes, edges, and native
    productions.  No Python loop selects an outcome; the Python loop in the
    constructor only materializes the input graph, as it does for the older
    measurement profiles.
    """
    for index in range(size):
        node = agent.s.add_node(node_type, {key: 0, "ordinal": index})
        _edge(agent, root, edge_type, node)
    for stage, (before, after) in enumerate(transitions):
        agent.inner.add_rule({
            "name": f"phase7_native_{node_type}_{stage}",
            "area": "measurement",
            "order": stage,
            "latency_class": "soft_realtime",
            "match": [["source", edge_type, "target"]],
            "where": {
                "type": "Eq",
                "a": {"type": "Attr", "node": {"type": "Var", "name": "target"}, "key": key},
                "b": {"type": "Lit", "value": before},
            },
            "effects": [["set_attr", "target", key, after]],
        })


def _snapshot(agent: WorldAdapter) -> dict[str, Any]:
    # The native substrate owns the complete edge index (the Python TypedGraph
    # view is not involved here), so use its canonical diagnostic export.
    graph = agent.inner.graph_to_dict()
    return {
        "nodes": sorted(graph["nodes"], key=lambda item: item["id"]),
        "edges": sorted(graph["edges"], key=lambda item: (item["src"], item["type"], item["tgt"])),
        "node_count": agent.s.node_count(),
        "edge_count": agent.s.edge_count(),
    }


def _stable_report(report: dict[str, Any]) -> dict[str, Any]:
    """Keep only replay-observable native outputs, excluding no wall clock."""
    return {
        key: report.get(key)
        for key in (
            "steps", "clock_commits", "needs_reflex_dispatch", "reflexes_fired",
            "needs_thread_dispatch", "needs_result_fold", "needs_system_two",
            "system_one_commits", "system_two_escalations", "system_two_stale",
            "system_two_lease_blocked", "system_two_steps", "trace",
        )
    }


@dataclass(frozen=True)
class NativeCycleMeasurement:
    schema: str
    plan: str
    iterations: int
    warmup: int
    durations_ms: tuple[float, ...]
    steps: tuple[int, ...]
    reports: tuple[dict[str, Any], ...]
    graph: dict[str, Any]
    replay_equal: bool
    replay_difference: dict[str, Any] | None
    rss_before_bytes: int
    rss_after_bytes: int
    rss_delta_bytes: int
    peak_rss_bytes: int
    runtime: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "plan": self.plan,
            "iterations": self.iterations,
            "warmup": self.warmup,
            "durations_ms": list(self.durations_ms),
            "latency_ms": {
                "min": min(self.durations_ms),
                "median": statistics.median(self.durations_ms),
                "max": max(self.durations_ms),
            },
            "steps": list(self.steps),
            "reports": list(self.reports),
            "graph": self.graph,
            "replay_equal": self.replay_equal,
            "replay_difference": self.replay_difference,
            "rss_before_bytes": self.rss_before_bytes,
            "rss_after_bytes": self.rss_after_bytes,
            "rss_delta_bytes": self.rss_delta_bytes,
            "peak_rss_bytes": self.peak_rss_bytes,
            "runtime": self.runtime,
        }


def _run(iterations: int, warmup: int, plan: str, profile: str) -> tuple[dict[str, Any], NativeCycleMeasurement]:
    if iterations < 1 or warmup < 0 or iterations > 256 or warmup > 64:
        raise ValueError("bounded measurement requires 1<=iterations<=256 and 0<=warmup<=64")
    agent = _probe(profile)
    before_cycle = _snapshot(agent)
    rss_before = _current_rss_bytes()
    max_steps = 512
    for _ in range(warmup):
        agent.inner.run_cycle(plan, max_steps)
    durations = []
    reports = []
    for _ in range(iterations):
        start = time.perf_counter_ns()
        reports.append(dict(agent.inner.run_cycle(plan, max_steps, trace=True)))
        durations.append((time.perf_counter_ns() - start) / 1_000_000.0)
    snapshot = _snapshot(agent)
    rss_after = _current_rss_bytes()

    replay = _probe(profile)
    for _ in range(warmup):
        replay.inner.run_cycle(plan, max_steps)
    replay_reports = [dict(replay.inner.run_cycle(plan, max_steps, trace=True)) for _ in range(iterations)]
    left = {"reports": [_stable_report(r) for r in reports], "graph": snapshot}
    right = {"reports": [_stable_report(r) for r in replay_reports], "graph": _snapshot(replay)}
    difference = None if left == right else {"first": left, "replay": right}
    measurement = NativeCycleMeasurement(
        schema=SCHEMA,
        plan=f"{profile}:{plan}",
        iterations=iterations,
        warmup=warmup,
        durations_ms=tuple(durations),
        steps=tuple(int(r["steps"]) for r in reports),
        reports=tuple(_stable_report(r) for r in reports),
        graph=snapshot,
        replay_equal=difference is None,
        replay_difference=difference,
        rss_before_bytes=rss_before,
        rss_after_bytes=rss_after,
        rss_delta_bytes=max(0, rss_after - rss_before),
        peak_rss_bytes=rss_after,
        runtime={"python": platform.python_version(), "platform": platform.platform()},
    )
    first_steps = [int(r["steps"]) for r in reports]
    trace_counts = [sum(int(item[2]) for item in r.get("trace", ())) for r in reports]
    authority = {
        "outcome_source": "native_trace",
        "graph_authored_workload": True,
        "python_outcome_selection": False,
        "pre_cycle_graph": before_cycle,
        "native_trace_observed": all((steps == 0 or count > 0) for steps, count in zip(first_steps, trace_counts)),
        "native_step_trace_alignment": all((steps == 0 or steps == count) for steps, count in zip(first_steps, trace_counts)),
        "native_trace_rule_ids": sorted({
            str(item[3]) for report in reports for item in report.get("trace", ())
            if item
        }),
        "graph_changed_after_native_cycle": before_cycle != snapshot,
    }
    result = {"reports": [_stable_report(r) for r in reports], "graph": snapshot, "native_authority": authority}
    return result, measurement


def measure_native_cycle(*, iterations: int = 8, warmup: int = 1, plan: str = "default",
                         profile: str = "fast") -> dict[str, Any]:
    """Run a bounded native measurement and return JSON-compatible evidence."""
    run_result, measurement = _run(iterations, warmup, plan, profile)
    result = measurement.to_dict()
    result["profile"] = profile
    result["workload_size"] = _PROFILE_SIZE[profile]
    limits = _PROFILE_LIMITS[profile]
    result["resource_limits"] = dict(limits)
    result["resource_limits"]["rss_bytes"] = _RSS_ABSOLUTE_OBSERVABILITY_LIMIT
    result["resource_limits"]["rss_growth_bytes"] = _RSS_GROWTH_LIMIT
    result["rss_assertion"] = {
        "basis": "workload_rss_growth",
        "measured_field": "rss_delta_bytes",
        "limit_field": "resource_limits.rss_growth_bytes",
        "limit_bytes": _RSS_GROWTH_LIMIT,
        "absolute_fields_observability_only": True,
    }
    result["resource_assertions"] = {
        "bounded_steps": all(step <= limits["steps"] for step in result["steps"]),
        "bounded_graph": (
            result["graph"]["node_count"] <= limits["nodes"]
            and result["graph"]["edge_count"] <= limits["edges"]
        ),
        "bounded_rss": result["rss_delta_bytes"] <= result["resource_limits"]["rss_growth_bytes"],
        "rss_measured": result["rss_before_bytes"] > 0 and result["rss_after_bytes"] > 0,
        "replay_equal": result["replay_equal"],
    }
    result["native_authority"] = run_result["native_authority"]
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=8)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--plan", default="default", choices=("default", "master_legacy", "cognitive_legacy"))
    parser.add_argument("--profile", default="fast", choices=PROFILES)
    args = parser.parse_args()
    print(json.dumps(measure_native_cycle(iterations=args.iterations, warmup=args.warmup,
                                          plan=args.plan, profile=args.profile), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
