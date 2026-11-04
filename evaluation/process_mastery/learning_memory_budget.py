"""Mechanical executor for eviction decisions selected by native P25 rules.

This adapter performs graph storage I/O only. It never chooses a victim or
changes a retention priority; those decisions are represented by native
LearningMemoryItem availability transitions.
"""
from __future__ import annotations

import json
import hashlib


def add_measured_content_item(agent, *, item_id: str, content_class: str,
                             graph_nodes, admission_epoch: float,
                             overhead_bytes: int = 32) -> dict:
    """Create a byte-measured item over existing learner graph nodes."""
    if not item_id or not content_class or overhead_bytes < 0:
        raise ValueError("item identity/class must be nonempty and overhead nonnegative")
    unique_nodes = list(dict.fromkeys(graph_nodes))
    if not unique_nodes:
        raise ValueError("a charged content item must reference learner graph state")
    dynamic = [{"native_type": agent.s.node(node)["type"],
                "attrs": agent.s.node(node)["attrs"]} for node in unique_nodes]
    serialized = {"item_id": item_id, "content_class": content_class,
                  "admission_epoch": float(admission_epoch),
                  "dynamic_graph_records": dynamic,
                  "native_node_references": [int(node.value) for node in unique_nodes]}
    payload_bytes = len(json.dumps(serialized, sort_keys=True, separators=(",", ":"),
                                   ensure_ascii=False, allow_nan=False).encode("utf-8"))
    charged = (payload_bytes + overhead_bytes + len(item_id.encode("utf-8"))
               + 8 * len(unique_nodes))
    item = agent.s.add_node("LearningMemoryItem", {
        "item_id": item_id, "content_class": content_class,
        "availability": "pending_admission", "charged_bytes": float(charged),
        "admission_epoch": float(admission_epoch), "retention_priority": 0.0,
        "payload": None, "protection_class": "ordinary",
        "payload_sha256": hashlib.sha256(
            json.dumps(serialized, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest(),
    })
    agent.s.add_edge(agent.ag, "has_learning_memory_item", item, {})
    for node in unique_nodes:
        wrapper = agent.s.add_node("LearningMemoryGraphNode", {
            "graph_node_id": int(node.value),
            "content_type": agent.s.node(node)["type"],
        })
        agent.s.add_edge(item, "has_learning_memory_graph_node", wrapper, {})
    return {"item_id": item_id, "node_count": len(unique_nodes),
            "payload_bytes": payload_bytes, "charged_bytes": charged,
            "payload_sha256": agent.s.node(item)["attrs"]["payload_sha256"],
            "item_node": item}


def charge_persistent_summaries(agent, *, overhead_bytes: int = 32) -> list[dict]:
    """Measure native summary bundles and stage the measured charge for native admission."""
    measured = []
    item_by_id = {str(agent.s.node(item)["attrs"].get("item_id")): item
                  for item in agent.s.nodes("LearningMemoryItem")}
    for summary_node in agent.s.nodes("PersistentLearnedSummary"):
        summary = agent.s.node(summary_node)["attrs"]
        if summary.get("summary_charge_status") == "charged":
            continue
        summary_id = str(summary["summary_id"])
        item_node = item_by_id.get(summary_id)
        if item_node is None:
            raise RuntimeError(f"persistent summary {summary_id} has no budget item")
        hypotheses = list(agent.s.neighbours(summary_node,
                                             "projects_to_process_hypothesis"))
        if len(hypotheses) != 1:
            raise RuntimeError(f"persistent summary {summary_id} has no unique native hypothesis")
        hypothesis = agent.s.node(hypotheses[0])["attrs"]
        for graph_node, content_type in ((summary_node, "PersistentLearnedSummary"),
                                         (hypotheses[0], "ProcessInductionHypothesis")):
            wrapper = agent.s.add_node("LearningMemoryGraphNode", {
                "graph_node_id": int(graph_node.value), "content_type": content_type,
            })
            agent.s.add_edge(item_node, "has_learning_memory_graph_node", wrapper, {})
        record = {"summary": summary, "native_hypothesis": hypothesis,
                  "witness_event_ids": [summary.get("witness_event_1"),
                                        summary.get("witness_event_2")],
                  "decoder": summary.get("decoder_kind"),
                  "exceptions_retained": summary.get("exceptions_retained")}
        payload_bytes = len(json.dumps(record, sort_keys=True, separators=(",", ":"),
                                       ensure_ascii=False, allow_nan=False).encode("utf-8"))
        # Charge serialized content, the durable key/index, fixed entry
        # overhead, and graph references to both witnesses and the hypothesis.
        charged = payload_bytes + overhead_bytes + len(summary_id.encode("utf-8")) + 24
        charged += 8 * (len(record["witness_event_ids"]) + 1)
        agent.s.set_attr(summary_node, "serialized_bytes", float(charged))
        agent.s.set_attr(summary_node, "summary_charge_status", "charged")
        agent.s.set_attr(item_node, "charged_bytes", float(charged))
        agent.s.set_attr(item_node, "availability", "pending_admission")
        measured.append({"summary_id": summary_id, "charged_bytes": charged,
                         "payload_bytes": payload_bytes})
    return measured

def apply_native_evictions(agent) -> list[str]:
    """Remove payload-bearing graph nodes named by native eviction decisions."""
    applied = []
    for item in list(agent.s.nodes("LearningMemoryItem")):
        attrs = agent.s.node(item)["attrs"]
        if attrs.get("availability") not in {"evicted", "rejected_capacity"} or attrs.get("eviction_applied"):
            continue
        item_id = str(attrs.get("item_id", item))
        for link in list(agent.s.neighbours(item, "has_learning_memory_graph_node")):
            # Wrappers keep the policy's graph vocabulary generic; the
            # adapter interprets their numeric native node handle as I/O.
            link_attrs = agent.s.node(link)["attrs"]
            payload_id = int(link_attrs["graph_node_id"])
            payload_type = str(link_attrs["content_type"])
            payload_node = next((node for node in agent.s.nodes(payload_type)
                                 if int(node.value) == payload_id), None)
            if payload_node is None:
                continue
            agent.s.remove_node(payload_node)
            agent.s.remove_node(link)
        agent.s.set_attr(item, "payload", None)
        agent.s.set_attr(item, "eviction_applied", True)
        applied.append(item_id)
    return applied
