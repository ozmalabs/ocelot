"""Boot outcomes become evidence; graph rules decide whether to self-concern."""
from __future__ import annotations

import json
from pathlib import Path

from substrate.boot_all import load_all_seeds
from substrate.seed_loader import manifest_for
from substrate.world_adapter import WorldAdapter


def _attrs(agent, node_type):
    return [dict(agent.s.node(n)["attrs"]) for n in agent.s.nodes(node_type)]


def _agent_with_metacognition():
    agent = WorldAdapter(seeds=())
    agent.inner.load_seed_manifest(manifest_for("boot_metacognition"), agent.agent)
    return agent


def test_loader_only_exposes_evidence_then_graph_files_concern(tmp_path: Path):
    agent = _agent_with_metacognition()
    (tmp_path / "good.json").write_text(json.dumps({
        "id": "good", "version": "1", "nodes": [], "edges": [],
        "productions": [], "rules": [],
    }))
    # Valid JSON, invalid native seed schema: the node deliberately lacks local_id.
    (tmp_path / "broken.json").write_text(json.dumps({
        "id": "broken", "version": "1",
        "nodes": [{"type": "Concept", "attrs": {"name": "broken"}}],
        "edges": [], "productions": [], "rules": [],
    }))

    report = load_all_seeds(agent, seed_dir=tmp_path)
    assert len(report["failed"]) == 1
    cycles = _attrs(agent, "BootCycle")
    anomalies = _attrs(agent, "BootSeedAnomaly")
    assert cycles[-1]["status"] == "complete"
    assert cycles[-1]["integrity"] == "unassessed"
    assert anomalies == [{
        "seed_id": "broken", "outcome": "failed",
        "detail": "ValueError: seed node missing local_id",
        "assessment": "unexamined",
    }]
    assert _attrs(agent, "SelfConcern") == []

    agent.inner.run_rules()

    cycles = _attrs(agent, "BootCycle")
    concerns = [a for a in _attrs(agent, "SelfConcern")
                if a.get("kind") == "boot_integrity"]
    assert cycles[-1]["integrity"] == "compromised"
    assert cycles[-1]["failed_count"] == 1
    assert cycles[-1]["degraded_count"] == 0
    assert len(concerns) == 1
    assert concerns[0]["source"] == "implicit"
    assert concerns[0]["content"] == (
        "core boot integrity is compromised; inspect the linked seed-load evidence")
    assert _attrs(agent, "BootSeedAnomaly")[0]["assessment"] == "evidence_for_concern"

    # Fixed-point re-runs neither duplicate the concern nor lose the evidence.
    agent.inner.run_rules()
    assert len([a for a in _attrs(agent, "SelfConcern")
                if a.get("kind") == "boot_integrity"]) == 1

    # A later failed boot is new evidence for the same live concern, not a
    # second copy of the same metacognitive gap.
    load_all_seeds(agent, seed_dir=tmp_path)
    agent.inner.run_rules()
    assert len([a for a in _attrs(agent, "SelfConcern")
                if a.get("kind") == "boot_integrity"]) == 1
    assert [a["integrity"] for a in _attrs(agent, "BootCycle")] == [
        "compromised", "compromised"]
    assert all(a["assessment"] == "evidence_for_concern"
               for a in _attrs(agent, "BootSeedAnomaly"))


def test_graph_assesses_an_anomaly_free_boot_as_healthy(tmp_path: Path):
    agent = _agent_with_metacognition()
    (tmp_path / "good.json").write_text(json.dumps({
        "id": "good", "version": "1", "nodes": [], "edges": [],
        "productions": [], "rules": [],
    }))

    report = load_all_seeds(agent, seed_dir=tmp_path)
    assert report["failed"] == [] and report["rules_skipped"] == []
    agent.inner.run_rules()

    assert _attrs(agent, "BootCycle")[-1]["integrity"] == "healthy"
    assert _attrs(agent, "BootSeedAnomaly") == []
    assert not [a for a in _attrs(agent, "SelfConcern")
                if a.get("kind") == "boot_integrity"]


def test_many_failed_seeds_file_one_concern_with_all_evidence(tmp_path: Path):
    """v1.1.0: a boot with N failed seeds is ONE compromised-boot assessment
    (one SelfConcern) supported by all N anomalies -- v1.0.0 matched per
    anomaly and minted N concerns in a single rule pass."""
    agent = _agent_with_metacognition()
    for i in range(4):
        (tmp_path / f"broken{i}.json").write_text(json.dumps({
            "id": f"broken{i}", "version": "1",
            "nodes": [{"type": "Concept", "attrs": {"name": f"b{i}"}}],
            "edges": [], "productions": [], "rules": [],
        }))
    load_all_seeds(agent, seed_dir=tmp_path)
    agent.inner.run_rules()
    concerns = [n for n in agent.s.nodes("SelfConcern")
                if agent.s.node(n)["attrs"].get("kind") == "boot_integrity"]
    assert len(concerns) == 1
    assert len(list(agent.inner.neighbours(concerns[0], "supported_by"))) == 4
