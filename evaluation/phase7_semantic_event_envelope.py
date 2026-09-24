"""Phase 7K: bounded envelope measurement for neutral semantic ingress.

This is an evaluation-only harness.  It exercises the existing
``WorldAdapter.ingest_semantic_event`` boundary with language-neutral frames;
it does not add a parser, reply path, or cognition authority.  Python
materializes the supplied semantic evidence and reads the graph.  Native
rules remain authoritative for proposition lifecycle state, and the existing
situation-model faculty remains authoritative for consequence recognition.

The malformed case is deliberately reported at the proposition boundary:
ingress still records its semantic event/discourse observation, while the
invalid proposition must not create a Proposition or PropositionEvidence
node.  This distinguishes mechanical observation from fail-closed
proposition materialization instead of claiming that observation itself did
not occur.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import platform
import resource
import time
from typing import Any, Mapping

from domains.proposition_commitment import (
    EVIDENCE_KIND,
    EVIDENCE_SCHEMA,
    apply_situation_consequence,
)
from substrate.boot_all import load_all_seeds
from substrate.seed_loader import manifest_for
from substrate.world_adapter import WorldAdapter


SCHEMA = "phase7-semantic-event-envelope.v1"
RSS_GROWTH_LIMIT = 100 * 1024 * 1024


def _rss_bytes() -> int:
    """Prefer current RSS; retain the existing native-measurement fallback."""
    try:
        for line in open("/proc/self/status", encoding="utf-8"):
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        pass
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (
        1 if platform.system() == "Darwin" else 1024
    ))


def _new_agent() -> WorldAdapter:
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    # The lifecycle is self-load-only and is intentionally loaded by this
    # measurement, not by production ingress.
    agent.inner.load_seed_manifest(
        manifest_for("proposition_commitment_lifecycle"), agent.agent)
    return agent


def _frame(step: Mapping[str, Any]) -> dict[str, Any]:
    frame: dict[str, Any] = {
        "event_id": step["event_id"],
        "speech_act": "assertion",
        "communicative_force": "assertion_or_correction",
        "cognitive_goal": "update_common_ground",
        "grounding_status": step.get("grounding_status", "candidate_grounded"),
        "interaction_mode": "non_turn",
    }
    if "proposition" in step:
        frame["proposition"] = step["proposition"]
    return frame


def _counts(agent: WorldAdapter) -> dict[str, Any]:
    graph = agent.inner.graph_to_dict()
    node_types = Counter(item["type"] for item in graph["nodes"])
    edge_types = Counter(item["type"] for item in graph["edges"])
    return {
        "node_count": agent.s.node_count(),
        "edge_count": agent.s.edge_count(),
        "node_types": dict(sorted(node_types.items())),
        "edge_types": dict(sorted(edge_types.items())),
    }


def _attrs(agent: WorldAdapter, node) -> dict[str, Any]:
    return dict(agent.s.node(node)["attrs"]) if node is not None else {}


def _propositions(agent: WorldAdapter) -> list[dict[str, Any]]:
    rows = []
    for node in agent.s.nodes("Proposition"):
        attrs = _attrs(agent, node)
        evidence = list(agent.inner.neighbours(node, "evidenced_by"))
        origins = list(agent.inner.neighbours(node, "originated_in"))
        consequences = [
            c for c in agent.s.nodes("SituationModelConsequence")
            if agent.inner.has_edge(c, "for_proposition", node)
        ]
        rows.append({
            "evidence_id": attrs.get("evidence_id"),
            "predicate": attrs.get("predicate"),
            "polarity": attrs.get("polarity"),
            "commitment_status": attrs.get("commitment_status"),
            "uptake_signal": attrs.get("uptake_signal"),
            "uptake_applied": attrs.get("uptake_applied"),
            "evidence_present": bool(evidence),
            "origin_event_present": bool(origins),
            "consequences": sorted(
                ({
                    "source": _attrs(agent, c).get("source"),
                    "predicate": _attrs(agent, c).get("predicate"),
                    "originated_in": bool(agent.inner.neighbours(c, "originated_in")),
                } for c in consequences),
                key=lambda item: (item["predicate"] or "", item["source"] or ""),
            ),
        })
    return sorted(rows, key=lambda row: row["evidence_id"] or "")


def _common_ground(agent: WorldAdapter) -> list[dict[str, Any]]:
    rows = []
    for node in agent.s.nodes("CommonGround"):
        attrs = _attrs(agent, node)
        rows.append({
            "scope_key": attrs.get("scope_key", "shared"),
            "scope_addressee": attrs.get("scope_addressee"),
            "claims": list(attrs.get("claims") or []),
            "participants": list(attrs.get("participants") or []),
            "revision": attrs.get("revision", 0),
        })
    return sorted(rows, key=lambda row: str(row["scope_key"]))


def _native_drain(agent: WorldAdapter) -> int | None:
    """Record an observable post-ingress native drain when supported.

    ``ingest_semantic_event`` already invokes ``run_rules`` internally.  The
    public substrate API does not expose that invocation's per-call trace, so
    this is explicitly labelled as a post-ingress drain rather than attributed
    to the Python ingress.  A missing/unsupported return remains ``None``.
    """
    try:
        value = agent.inner.run_rules()
    except (AttributeError, TypeError):
        return None
    return int(value) if isinstance(value, int) else None


SEQUENCE: tuple[dict[str, Any], ...] = (
    {
        "id": "challenged_proposition",
        "event_id": "phase7k-challenge",
        "proposition": {
            "schema": EVIDENCE_SCHEMA,
            "kind": EVIDENCE_KIND,
            "predicate": "state_open",
            "arguments": {"theme": "gate"},
            "polarity": "affirmed",
            "provider": "phase7k-neutral-adapter",
            "evidence_id": "phase7k-challenged",
            "commitment_status": "proposed",
            "uptake_signal": "challenge",
        },
    },
    {
        "id": "accepted_typed_consequence",
        "event_id": "phase7k-accept-drop",
        "proposition": {
            "schema": EVIDENCE_SCHEMA,
            "kind": EVIDENCE_KIND,
            "predicate": "drop",
            "arguments": {"agent": "john", "theme": "glass"},
            "polarity": "affirmed",
            "provider": "phase7k-neutral-adapter",
            "evidence_id": "phase7k-accepted-drop",
            "commitment_status": "proposed",
            "uptake_signal": "accept",
        },
    },
    {
        "id": "malformed_evidence",
        "event_id": "phase7k-malformed",
        "proposition": {
            "schema": EVIDENCE_SCHEMA,
            "kind": EVIDENCE_KIND,
            "text": "surface evidence is not a neutral proposition",
            "predicate": "drop",
            "arguments": {"agent": "john", "theme": "glass"},
            "polarity": "affirmed",
            "provider": "phase7k-neutral-adapter",
            "evidence_id": "phase7k-malformed",
            "commitment_status": "proposed",
        },
    },
)


def measure_sequence(sequence: tuple[dict[str, Any], ...] = SEQUENCE) -> dict[str, Any]:
    agent = _new_agent()
    before = _counts(agent)
    rss_before = _rss_bytes()
    rows: list[dict[str, Any]] = []
    native_drains: list[int] = []
    message_count_before = len(agent.s.nodes("Message"))
    turn_count_before = len(agent.s.nodes("Turn"))
    start = time.perf_counter_ns()

    for step in sequence:
        props_before = len(agent.s.nodes("Proposition"))
        evidence_before = len(agent.s.nodes("PropositionEvidence"))
        result = agent.ingest_semantic_event(
            _frame(step), provider="phase7k-neutral-adapter",
            interaction_mode="non_turn", conversation_id="phase7k")
        drain = _native_drain(agent)
        if drain is not None:
            native_drains.append(drain)
        consequence = None
        proposition_result = result.get("proposition") or {}
        proposition = proposition_result.get("proposition")
        if step["id"] == "accepted_typed_consequence" and proposition is not None:
            consequence = apply_situation_consequence(agent, proposition)
        rows.append({
            "id": step["id"],
            "event_identity": bool(result.get("discourse_event_id")),
            "supported": bool(proposition_result.get("supported")),
            "error": proposition_result.get("error"),
            "proposition_count_delta": len(agent.s.nodes("Proposition")) - props_before,
            "evidence_count_delta": len(agent.s.nodes("PropositionEvidence")) - evidence_before,
            "consequence_supported": bool(consequence and consequence.get("supported")),
            "reply": result.get("reply"),
        })

    elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000.0
    after = _counts(agent)
    rss_after = _rss_bytes()
    message_count = len(agent.s.nodes("Message"))
    turn_count = len(agent.s.nodes("Turn"))
    readback = {
        "propositions": _propositions(agent),
        "common_ground": _common_ground(agent),
        "situation_consequence_count": len(agent.s.nodes("SituationModelConsequence")),
        "message_count": message_count,
        "turn_count": turn_count,
        "rows": rows,
    }
    rule_names = sorted(str(item.get("name")) for item in agent.inner.export_rules()
                        if item.get("name"))
    return {
        "schema": SCHEMA,
        "sequence_length": len(sequence),
        "graph_before": before,
        "graph_after": after,
        "graph_growth": {
            "nodes": after["node_count"] - before["node_count"],
            "edges": after["edge_count"] - before["edge_count"],
        },
        "rows": rows,
        "readback": readback,
        "no_message_created": message_count == message_count_before,
        "no_turn_created": turn_count == turn_count_before,
        "no_reply_created": all(row["reply"] is None for row in rows),
        "malformed_proposition_failed_closed": (
            rows[-1]["supported"] is False
            and rows[-1]["proposition_count_delta"] == 0
            and rows[-1]["evidence_count_delta"] == 0
        ),
        "python_materialization": {
            "semantic_event_and_discourse_write": True,
            "proposition_validation_and_graph_write": True,
            "surface_parser_invoked": False,
            "reply_selection": False,
        },
        "native_authority": {
            "lifecycle_seed": "proposition_commitment_lifecycle",
            "lifecycle_status_read_from_graph": True,
            "consequence_faculty": "situation_model_reader",
            "native_rule_names_loaded": rule_names,
            "post_ingress_drain_steps": native_drains,
            "post_ingress_drain_observable": bool(native_drains),
        },
        "latency_ms": elapsed_ms,
        "rss_before_bytes": rss_before,
        "rss_after_bytes": rss_after,
        "rss_delta_bytes": max(0, rss_after - rss_before),
        "resource_assertions": {
            "rss_measured": rss_before > 0 and rss_after > 0,
            "rss_growth_bounded": max(0, rss_after - rss_before) <= RSS_GROWTH_LIMIT,
        },
    }


def _replay_readback(report: Mapping[str, Any]) -> dict[str, Any]:
    """Remove host timing and graph ids while retaining cognitive readback."""
    return {
        "graph_growth": report["graph_growth"],
        "readback": report["readback"],
        "rows": report["rows"],
        "no_message_created": report["no_message_created"],
        "no_turn_created": report["no_turn_created"],
        "no_reply_created": report["no_reply_created"],
        "malformed_proposition_failed_closed": report["malformed_proposition_failed_closed"],
    }


def measure_with_replay() -> dict[str, Any]:
    primary = measure_sequence()
    replay = measure_sequence()
    left, right = _replay_readback(primary), _replay_readback(replay)
    primary["replay_equal"] = left == right
    primary["replay_difference"] = None if primary["replay_equal"] else {
        "primary": left, "replay": right,
    }
    primary["replay_runtime"] = {
        "second_run_latency_ms": replay["latency_ms"],
        "second_run_rss_delta_bytes": replay["rss_delta_bytes"],
    }
    return primary


if __name__ == "__main__":
    print(json.dumps(measure_with_replay(), indent=2, sort_keys=True))
