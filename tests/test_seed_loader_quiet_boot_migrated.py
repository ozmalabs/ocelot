"""Seed boot: declarative principles must not warn the Rust engine loader."""
from __future__ import annotations

import builtins
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from substrate.seed_loader import engine_rules_only, manifest_for, normalize_declarative
from substrate.boot_all import (
    _select_seed_ids,
    _read_seed_index,
    _read_seeds,
    _topo_order,
    load_all_seeds,
    resolve_graph_content_refs,
    seed_microtheory_inventory,
)
import substrate.boot_all as boot_all
from substrate.world_adapter import WorldAdapter
from domains.self_model import _build_seed_rule_index
from substrate.boot_profiles import (
    load_conversation_content_candidates,
    load_conversation_graph_content_refs,
    load_conversation_seed_profile,
)


def test_engine_rules_only_strips_declarative_principles():
    m = manifest_for("philosophy")
    raw = engine_rules_only({"rules": [
        {"name": "Gettier_invalidates_naive_JTB", "if": ["x"], "then": ["y"]},
        {"name": "real_rule", "match": [["a", "b", "c"]], "effects": []},
    ]})
    assert len(raw["rules"]) == 1
    assert raw["rules"][0]["name"] == "real_rule"
    # philosophy has many declarative rules, few/no engine rules
    eng = engine_rules_only(m if "rules" in m else {"rules": []})
    for r in eng.get("rules") or []:
        assert isinstance(r.get("match"), list)


def test_normalize_declarative_shares_principle_detection():
    m = {"concepts": [{"name": "c", "definition": "d"}],
         "rules": [{"name": "p", "head": "h", "body": "b"}]}
    n = normalize_declarative(m)
    assert "concepts" not in n
    assert n["rules"] == []
    types = [x["type"] for x in n["nodes"]]
    assert "Concept" in types
    assert "Principle" in types


def test_seed_index_preserves_dependency_order_and_generated_override(tmp_path):
    generated = tmp_path / "generated"
    generated.mkdir()
    manifests = {
        tmp_path / "base.json": {
            "id": "base", "depends_on": [], "category": "core",
            "capability_keys": ["base_cap"],
            "nodes": [{"local_id": 1, "type": "Base",
                       "attrs": {"name": "base_node"}}],
        },
        tmp_path / "base_alt.json": {
            "id": "base_alt", "depends_on": [],
            "nodes": [{"type": "Base", "attrs": {"name": "base_node"}}],
        },
        tmp_path / "child.json": {
            "id": "child", "depends_on": ["base", "absent_dependency"],
            "rules": [{"name": "overridden_rule"}],
        },
        tmp_path / "self_load.json": {
            "id": "self_load", "self_load_only": True,
        },
        generated / "child.json": {
            "id": "child", "depends_on": ["absent_dependency"],
            "nodes": [{"local_id": 1, "type": "GeneratedChild",
                       "attrs": {"name": "child_node"}}],
            "extra_nodes": [{"type": "GeneratedChild", "name": "child_node"}],
            "edges": [{
                "src": {"type": "Base", "name": "base_node"},
                "type": "references", "tgt": {"local": 1},
            }],
            "relations": [{"src": "child_node", "edge": "references",
                           "tgt": "base_node"}],
        },
    }
    for path, payload in manifests.items():
        path.write_text(json.dumps(payload), encoding="utf-8")

    full = _read_seeds(str(tmp_path))
    index, paths = _read_seed_index(str(tmp_path))

    assert set(index) == set(full) == {"base", "base_alt", "child"}
    assert set(index["base"]) == {
        "id", "selective_content_keys", "depends_on", "category",
        "microtheory", "capability_keys",
        "group_keys", "node_types", "content_keys", "named_content_refs",
        "content_connections", "rule_names",
        "content_dependencies",
        "content_load_dependencies", "missing_content_references",
        "missing_dependencies", "typed_content_reference_count",
        "name_content_reference_count", "ambiguous_content_reference_count",
    }
    assert index["base"]["group_keys"] == [
        "capability:base_cap", "category:core",
    ]
    assert index["base"]["node_types"] == ["Base"]
    assert "base_node" in index["base"]["content_keys"]
    assert index["base"]["named_content_refs"] == [
        {"type": "Base", "name": "base_node"},
    ]
    assert index["child"]["content_dependencies"] == ["base", "base_alt"]
    assert index["child"]["content_load_dependencies"] == ["base", "base_alt"]
    assert index["child"]["missing_content_references"] == []
    assert index["child"]["typed_content_reference_count"] == 1
    assert index["child"]["content_connections"] == [{
        "src": {"type": "Base", "name": "base_node"},
        "edge": "references",
        "tgt": {"type": "GeneratedChild", "name": "child_node"},
    }]
    assert index["child"]["name_content_reference_count"] == 2
    assert index["child"]["ambiguous_content_reference_count"] == 2
    assert "child_node" in index["child"]["content_keys"]
    assert index["child"]["rule_names"] == []
    shared_base_name = next(
        key for key in index["base"]["content_keys"]
        if key == "base_node")
    assert shared_base_name is next(
        row["name"] for row in index["base_alt"]["named_content_refs"]
        if row["name"] == "base_node")
    assert paths["child"] == str(generated / "child.json")
    order = _topo_order(index)
    assert order.index("base") < order.index("child")
    selected, unresolved = _select_seed_ids(
        index,
        group_keys=["category:core"],
        content_keys=["not-present"],
    )
    assert selected == ["base"]
    assert unresolved == {
        "missing_seed_ids": [],
        "missing_content_keys": ["not-present"],
        "missing_dependencies": [],
        "missing_content_references": [],
    }
    selected, unresolved = _select_seed_ids(index, seed_ids=["child"])
    assert selected == ["base", "base_alt", "child"]
    assert unresolved == {
        "missing_seed_ids": [],
        "missing_content_keys": [],
        "missing_dependencies": [("child", "absent_dependency")],
        "missing_content_references": [],
    }
    selected, unresolved = _select_seed_ids(index, seed_ids=["unknown"])
    assert selected == []
    assert unresolved["missing_seed_ids"] == ["unknown"]
    selected, unresolved = _select_seed_ids(index, content_keys=["base_node"])
    assert selected == ["base", "base_alt"]
    assert unresolved["missing_content_keys"] == []
    scoped = {"child": [{"type": "GeneratedChild", "name": "child_node"}]}
    selected, unresolved = _select_seed_ids(
        index, scoped_content_refs=scoped)
    assert selected == ["base", "base_alt", "child"]
    assert scoped["base"] == [{"type": "Base", "name": "base_node"}]
    assert unresolved["missing_dependencies"] == [("child", "absent_dependency")]


def test_self_model_rule_index_reuses_effective_manifest_prepass(tmp_path):
    manifests = {
        "rules.json": {
            "id": "rules",
            "rules": [{"name": "native_rule"}],
            "nodes": [{"type": "Rule", "attrs": {"name": "graph_rule"}}],
        },
        "old.json": {"id": "override", "rules": [{"name": "stale_rule"}]},
        "generated/override.json": {
            "id": "override",
            "nodes": [{"type": "Current", "attrs": {"name": "current"}}],
        },
    }
    (tmp_path / "generated").mkdir()
    for filename, manifest in manifests.items():
        path = tmp_path / filename
        path.write_text(json.dumps(manifest), encoding="utf-8")

    assert _build_seed_rule_index(str(tmp_path)) == {
        "native_rule": "rules",
        "graph_rule": "rules",
    }


def test_seed_index_cache_reuses_map_and_hash_invalidates_same_stat_change(
        tmp_path, monkeypatch):
    manifest = tmp_path / "seed.json"
    manifest.write_text(json.dumps({"id": "seed_a", "depends_on": [],
                                    "rules": [{"name": "cached_rule"}]}),
                        encoding="utf-8")
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    cache_path = cache_dir / "index.json"
    monkeypatch.setattr(boot_all, "_seed_index_cache_path",
                        lambda _seed_dir: str(cache_path))

    build_count = 0
    real_build = boot_all._build_seed_index

    def count_build(seed_dir):
        nonlocal build_count
        build_count += 1
        return real_build(seed_dir)

    monkeypatch.setattr(boot_all, "_build_seed_index", count_build)
    first = boot_all._read_seed_index(str(tmp_path))
    boot_all._SEED_RULE_NAME_INDEX.pop(os.path.realpath(tmp_path), None)
    second = boot_all._read_seed_index(str(tmp_path))
    assert first == second
    assert build_count == 1
    assert boot_all._read_seed_rule_name_index(str(tmp_path)) == {
        "cached_rule": "seed_a",
    }

    before = manifest.stat()
    manifest.write_text(json.dumps({"id": "seed_b", "depends_on": []}),
                        encoding="utf-8")
    os.utime(manifest, ns=(before.st_atime_ns, before.st_mtime_ns))
    refreshed = boot_all._read_seed_index(str(tmp_path))
    assert set(refreshed[0]) == {"seed_b"}
    assert build_count == 2


def test_seed_prepass_inventory_is_cached_and_materialized_as_graph_data(
        tmp_path):
    (tmp_path / "area.json").write_text(json.dumps({
        "id": "area",
        "microtheory": {"name": "test_area"},
        "concepts": [
            {"name": "duplicate"}, {"name": "duplicate"},
            {"name": "another"},
        ],
    }), encoding="utf-8")
    first = seed_microtheory_inventory(str(tmp_path))
    second = seed_microtheory_inventory(str(tmp_path))

    assert first == second
    assert first["areas"] == [{"name": "test_area", "concept_count": 3}]

    agent = WorldAdapter(seeds=())
    report = load_all_seeds(agent, str(tmp_path))
    assert report["self_organisation_inventory"]["graph_linked"] is True
    from domains.self_organisation_reader import run_self_organisation
    state = run_self_organisation(agent.s)
    assert state["inventory_scope"] == "validated_seed_prepass_top12"
    assert state["areas"] == ["test_area"]
    assert state["detail"][0]["concepts"] == 3


def test_boot_reuses_source_validated_rule_index_for_self_model(tmp_path,
                                                                monkeypatch):
    seed = tmp_path / "seed.json"
    seed.write_text(json.dumps({
        "id": "boot_rule_source",
        "nodes": [{"type": "Concept", "attrs": {"name": "boot_node"}}],
    }), encoding="utf-8")
    cache_path = tmp_path / "index.json"
    monkeypatch.setattr(boot_all, "_seed_index_cache_path",
                        lambda _seed_dir: str(cache_path))

    digest_calls = 0
    real_digest = boot_all._seed_sources_digest

    def count_digest(seed_dir, paths):
        nonlocal digest_calls
        digest_calls += 1
        return real_digest(seed_dir, paths)

    monkeypatch.setattr(boot_all, "_seed_sources_digest", count_digest)
    agent = WorldAdapter(seeds=())
    report = load_all_seeds(agent, str(tmp_path))

    assert "self_model_failed" not in report
    assert digest_calls == 1


def test_selective_content_seed_loads_only_requested_named_nodes(tmp_path):
    (tmp_path / "lexicon.json").write_text(json.dumps({
        "id": "lexicon",
        "selective_content_keys": True,
        "nodes": [
            {"local_id": 1, "type": "Concept",
             "attrs": {"name": "north", "definition": "north concept"}},
            {"local_id": 2, "type": "Concept",
             "attrs": {"name": "unrequested", "definition": "other"}},
            {"local_id": 3, "type": "Concept",
             "attrs": {"name": "walk", "instruction_route": "world_action"}},
        ],
    }), encoding="utf-8")
    agent = WorldAdapter(seeds=())

    report = load_all_seeds(
        agent, str(tmp_path), seed_ids=["lexicon"],
        content_keys=["north"],
    )

    assert report["selection_complete"] is True
    assert report["content_slices"]["lexicon"] == {
        "requested_keys": ["north"],
        "matched_node_count": 1,
        "source_node_count": 3,
    }
    names = {agent.s.node(node)["attrs"].get("name")
             for node in agent.s.nodes("Concept")}
    assert "north" in names
    assert "walk" in names
    assert "unrequested" not in names


def test_content_candidate_prepass_filters_oov_and_keeps_provider_closure(tmp_path):
    (tmp_path / "lexicon.json").write_text(json.dumps({
        "id": "lexicon",
        "selective_content_keys": True,
        "nodes": [
            {"local_id": 1, "type": "Concept",
             "attrs": {"name": "can", "definition": "ability concept"}},
            {"local_id": 2, "type": "Concept",
             "attrs": {"name": "unrequested", "definition": "other"}},
        ],
    }), encoding="utf-8")
    (tmp_path / "faculty.json").write_text(json.dumps({
        "id": "faculty", "depends_on": ["lexicon"],
        "nodes": [{"local_id": 1, "type": "Faculty",
                   "attrs": {"name": "conversation_faculty"}}],
    }), encoding="utf-8")
    (tmp_path / "rule_name_collision.json").write_text(json.dumps({
        "id": "rule_name_collision",
        "nodes": [{"local_id": 1, "type": "Rule",
                   "attrs": {"name": "can"}}],
    }), encoding="utf-8")
    agent = WorldAdapter(seeds=())

    report = load_all_seeds(
        agent, str(tmp_path), seed_ids=["faculty"],
        content_candidates=["can", "blorf"],
    )

    assert report["selection_complete"] is True
    resolution = report["selection"]["content_candidate_resolution"]
    assert resolution == {
        "candidates": ["blorf", "can"],
        "content_keys": ["can"],
        "unresolved_candidates": ["blorf"],
        "provider_seed_ids_by_key": {"can": ["lexicon"]},
        "provider_seed_ids": ["lexicon"],
        "scoped_content_refs_by_seed": {
            "lexicon": [{"type": "Concept", "name": "can"}],
        },
    }
    assert report["order"] == ["lexicon", "faculty"]
    assert report["content_slices"]["lexicon"]["requested_refs"] == [
        {"type": "Concept", "name": "can"},
    ]
    names = {agent.s.node(node)["attrs"].get("name")
             for node in agent.s.nodes("Concept")}
    assert "can" in names
    assert "unrequested" not in names


def test_provider_map_is_cached_by_validated_seed_source_digest(
        tmp_path, monkeypatch):
    from substrate import boot_all

    root = str(tmp_path.resolve())
    seeds = {
        "lexicon": {"named_content_refs": [
            {"type": "Concept", "name": "can"},
        ]},
    }
    monkeypatch.setattr(boot_all, "_SEED_CONTENT_PROVIDER_INDEX", {})
    monkeypatch.setitem(boot_all._SEED_INDEX_SOURCE_DIGEST, root, "digest-a")
    build_count = 0
    real_build = boot_all._build_seed_content_provider_index

    def count_build(index):
        nonlocal build_count
        build_count += 1
        return real_build(index)

    monkeypatch.setattr(boot_all, "_build_seed_content_provider_index",
                        count_build)
    first = boot_all.resolve_seed_content_candidates(
        seeds, ["can"], seed_dir=root)
    second = boot_all.resolve_seed_content_candidates(
        seeds, ["can"], seed_dir=root)
    assert first == second
    assert build_count == 1

    seeds["sensor_seed"] = {"named_content_refs": [
        {"type": "Concept", "name": "sensor"},
    ]}
    monkeypatch.setitem(boot_all._SEED_INDEX_SOURCE_DIGEST,
                        root, "digest-b")
    refreshed = boot_all.resolve_seed_content_candidates(
        seeds, ["sensor"], seed_dir=root)
    assert refreshed["provider_seed_ids_by_key"] == {
        "sensor": ["sensor_seed"],
    }
    assert build_count == 2


def test_selection_index_reuses_equal_concept_provider_rows():
    from substrate.boot_all import (
        _build_seed_content_provider_index,
        _build_seed_selection_index,
        _select_seed_ids,
    )

    seeds = {
        "concept_a": {
            "content_keys": ["shared", "typed_only"],
            "named_content_refs": [{"type": "Concept", "name": "shared"}],
        },
        "concept_b": {
            "content_keys": ["shared"],
            "named_content_refs": [{"type": "Concept", "name": "shared"}],
        },
    }
    concept_providers = _build_seed_content_provider_index(seeds)
    selection_index = _build_seed_selection_index(
        seeds, concept_content_providers=concept_providers)

    assert "shared" not in selection_index["content_key_providers"]
    assert selection_index["content_key_providers"]["typed_only"] == [
        "concept_a",
    ]
    selected, unresolved = _select_seed_ids(
        seeds, content_keys=["shared"], selection_index=selection_index)
    assert set(selected) == {"concept_a", "concept_b"}
    assert unresolved["missing_content_keys"] == []


def test_incremental_seed_snapshot_keeps_connected_selection_fields_only():
    from substrate.boot_all import _compact_incremental_seed_index

    connections = [{
        "src": {"type": "Concept", "name": "valley"},
        "edge": "related_to",
        "tgt": {"type": "Place", "name": "valley_region"},
    }]
    seeds = {
        "places": {
            "id": "places", "depends_on": [], "group_keys": ["category:map"],
            "content_keys": ["valley"],
            "named_content_refs": [
                {"type": "Concept", "name": "valley"},
                {"type": "Place", "name": "valley_region"},
            ],
            "content_connections": connections,
            "content_dependencies": [], "content_load_dependencies": [],
            "missing_content_references": [], "missing_dependencies": [],
            "selective_content_keys": True,
            "rule_names": ["not-needed-at-runtime"],
            "microtheory_inventory": {"not-needed-at-runtime": True},
        },
    }

    compact = _compact_incremental_seed_index(seeds)

    assert compact["places"]["content_connections"] is connections
    assert compact["places"]["named_content_refs"] == seeds["places"][
        "named_content_refs"]
    assert "rule_names" not in compact["places"]
    assert "microtheory_inventory" not in compact["places"]


def test_live_conversation_prepass_incrementally_loads_selective_content(
        monkeypatch):
    from domains import self_model

    agent = WorldAdapter(seeds=())
    profile = load_conversation_seed_profile(agent)
    assert profile["selection_complete"] is True
    assert agent._conversation_route_concepts_preloaded is True
    assert agent._concept_by_name("can") is None
    assert agent._concept_by_name("valley") is None

    from substrate import seed_loader
    original_manifest_for = seed_loader.manifest_for
    route_manifest_reads = []

    def track_route_manifest_reads(seed_id):
        if seed_id in {"comprehend_instruction", "conversation_self_concern",
                       "conversation_self_reply"}:
            route_manifest_reads.append(seed_id)
        return original_manifest_for(seed_id)

    monkeypatch.setattr(seed_loader, "manifest_for", track_route_manifest_reads)
    agent._ensure_comprehension_seeds()
    assert route_manifest_reads == []

    def unexpected_self_model_refresh(*_args, **_kwargs):
        raise AssertionError("Concept-only content cannot change Rule/Program mirrors")

    monkeypatch.setattr(self_model, "ensure_self_model",
                        unexpected_self_model_refresh)

    first = load_conversation_content_candidates(
        agent, ["can", "blorf"])
    assert first["status"] == "loaded"
    assert first["candidate_resolution"]["content_keys"] == ["can"]
    assert first["candidate_resolution"]["unresolved_candidates"] == ["blorf"]
    assert first["loaded_seed_ids"] == ["learned_lexicon"]
    assert agent._concept_by_name("can") is not None
    assert agent._concept_by_name("valley") is None

    repeated = load_conversation_content_candidates(agent, ["can"])
    assert repeated["status"] == "already_available"
    assert len(agent.inner.nodes_where("Concept", "name", "can")) == 1
    second = load_conversation_content_candidates(agent, ["valley"])
    assert second["status"] == "loaded"
    assert second["loaded_seed_ids"] == ["learned_lexicon"]
    assert agent._concept_by_name("valley") is not None
    assert len(agent.inner.nodes_where("Concept", "name", "can")) == 1


def test_loader_refreshes_self_model_when_rule_source_is_added(tmp_path,
                                                              monkeypatch):
    from domains import self_model

    (tmp_path / "rules.json").write_text(json.dumps({
        "id": "rule_source",
        "nodes": [{"local_id": 1, "type": "Rule",
                   "attrs": {"name": "new_graph_rule"}}],
    }), encoding="utf-8")
    refreshes = []

    def record_refresh(agent, **kwargs):
        refreshes.append((agent, kwargs))
        return {"rules": {"minted": 1}, "programs": {"minted": 0}}

    monkeypatch.setattr(self_model, "ensure_self_model", record_refresh)
    report = load_all_seeds(WorldAdapter(seeds=()), str(tmp_path))
    assert report["loaded"] == 1
    assert report["self_model"]["rules"]["minted"] == 1
    assert len(refreshes) == 1


def test_runtime_prepass_reuses_index_until_manifest_metadata_changes(
        tmp_path, monkeypatch):
    from substrate import boot_all

    lexicon = tmp_path / "lexicon.json"
    lexicon.write_text(json.dumps({
        "id": "lexicon", "selective_content_keys": True,
        "nodes": [
            {"local_id": 1, "type": "Concept", "attrs": {"name": "can"}},
            {"local_id": 2, "type": "Concept", "attrs": {"name": "valley"}},
        ],
    }), encoding="utf-8")
    agent = WorldAdapter(seeds=())
    agent._conversation_seed_profile_state = {
        "seed_dir": str(tmp_path), "loaded_seed_ids": set(),
        "loaded_content_by_seed": {}, "loaded_content_keys": set(),
        "known_unprovided_candidates": set(),
        "provider_seed_ids_by_key": {}, "selective_seed_ids": {"lexicon"},
        "incremental_content_loading": True, "prepass_reports": [],
    }
    digest_calls = 0
    real_digest = boot_all._seed_sources_digest

    def count_digest(seed_dir, paths):
        nonlocal digest_calls
        digest_calls += 1
        return real_digest(seed_dir, paths)

    monkeypatch.setattr(boot_all, "_seed_sources_digest", count_digest)
    first = load_conversation_content_candidates(agent, ["can"])
    assert first["status"] == "loaded", (
        first.get("selection_complete"), first.get("failed"),
        first.get("refused_skips"))
    # A new key reuses the already validated connection map; it does not
    # re-hash every seed manifest on this turn.
    assert load_conversation_content_candidates(agent, ["valley"])["status"] == "loaded"
    assert agent._conversation_seed_profile_state[
        "provider_seed_ids_by_key"] == {"valley": ["lexicon"]}
    assert digest_calls == 1

    # A changed manifest set/content metadata invalidates the runtime snapshot
    # and forces the authoritative content-hash validation path again.
    lexicon.write_text(json.dumps({
        "id": "lexicon", "selective_content_keys": True,
        "nodes": [
            {"local_id": 1, "type": "Concept", "attrs": {"name": "can"}},
            {"local_id": 2, "type": "Concept", "attrs": {"name": "valley"}},
            {"local_id": 3, "type": "Concept", "attrs": {"name": "sensor"}},
        ],
    }), encoding="utf-8")
    assert load_conversation_content_candidates(agent, ["sensor"])["status"] == "loaded"
    assert digest_calls == 2


def test_world_adapter_runs_content_prepass_before_first_live_turn():
    agent = WorldAdapter(seeds=())
    profile = load_conversation_seed_profile(agent)
    assert profile["selection_complete"] is True
    assert "domains.language_world" in profile["runtime_modules_warmed"]
    assert "domains.morphology_reference" in profile["runtime_modules_warmed"]
    assert agent._concept_by_name("valley") is None

    agent.converse("What do you know about the valley?",
                   speech_act="question")

    prepass = agent._last_conversation_content_prepass
    assert prepass["status"] == "loaded"
    assert "valley" in prepass["candidate_resolution"]["content_keys"]
    assert agent._concept_by_name("valley") is not None


def test_conversation_content_prepass_survives_checkpoint_resume(tmp_path):
    agent = WorldAdapter(seeds=())
    profile = load_conversation_seed_profile(agent)
    assert profile["selection_complete"] is True
    assert agent._concept_by_name("valley") is None
    agent.s.add_node("DaemonSeedProfile", {"profile": "conversation"})
    assert load_conversation_content_candidates(agent, ["valley"])[
        "status"] == "loaded"

    current_checkpoint = tmp_path / "conversation-current.json"
    agent.save(current_checkpoint)
    checkpoint_state = json.loads(current_checkpoint.read_text())[
        "conversation_seed_profile_state"]
    assert checkpoint_state["provider_seed_ids_by_key"] == {}
    assert "valley" in checkpoint_state["loaded_content_by_seed"][
        "learned_lexicon"]
    resumed = WorldAdapter.load(current_checkpoint)
    assert resumed._conversation_seed_profile_state[
        "loaded_seed_ids"] == agent._conversation_seed_profile_state[
            "loaded_seed_ids"]
    result = load_conversation_content_candidates(resumed, ["valley"])
    assert result["status"] == "already_available"
    result = load_conversation_content_candidates(resumed, ["sensor"])
    assert result["status"] == "loaded"
    assert resumed._concept_by_name("sensor") is not None

    # Simulate a checkpoint written before the cache-state field existed.
    # The graph-resident daemon profile marker plus SeedSummary inventory is
    # sufficient to restore incremental connected loading conservatively.
    del agent._conversation_seed_profile_state
    legacy_checkpoint = tmp_path / "conversation-legacy.json"
    agent.save(legacy_checkpoint)
    legacy_resumed = WorldAdapter.load(legacy_checkpoint)
    assert legacy_resumed._conversation_seed_profile_state[
        "loaded_seed_ids"]
    legacy_result = load_conversation_content_candidates(
        legacy_resumed, ["valley"])
    assert legacy_result["status"] == "loaded"
    assert legacy_resumed._concept_by_name("valley") is not None


def test_preloaded_conversation_profile_does_not_load_out_of_set_candidates(
        monkeypatch):
    from substrate import boot_all

    agent = WorldAdapter(seeds=())
    agent._conversation_seed_profile_state = {
        "seed_dir": ".",
        "incremental_content_loading": False,
        "provider_seed_ids_by_key": {"can": ["learned_lexicon"]},
        "loaded_content_by_seed": {"learned_lexicon": {"can"}},
        "loaded_seed_ids": {"learned_lexicon"},
        "prepass_reports": [],
    }

    def unexpected_seed_load(*_args, **_kwargs):
        raise AssertionError("sealed pre-load profile must not load seeds")

    monkeypatch.setattr(boot_all, "load_all_seeds", unexpected_seed_load)
    result = load_conversation_content_candidates(agent, ["can", "valley"])

    assert result == {
        "status": "preload_only_unavailable",
        "candidates": ["can", "valley"],
        "not_preloaded": ["valley"],
        "seed_loading_performed": False,
    }
    assert agent._conversation_seed_profile_state["prepass_reports"] == [result]


def test_sealed_prepass_releases_global_indexes_but_keeps_agent_provider_map(
        tmp_path, monkeypatch):
    from substrate import boot_all, boot_profiles

    root = str(tmp_path.resolve())
    other_root = str((tmp_path / "other").resolve())
    boot_all._SEED_INDEX_MEMORY_CACHE[root] = ((), "digest", {}, {}, {}, {})
    boot_all._SEED_INDEX_MEMORY_CACHE[other_root] = (
        (), "other-digest", {}, {}, {}, {})
    boot_all._SEED_CONTENT_PROVIDER_INDEX[(root, "digest")] = {}
    boot_all._SEED_CONTENT_PROVIDER_INDEX[(other_root, "other-digest")] = {}
    boot_all._SEED_SELECTION_INDEX[(root, "digest")] = {}
    boot_all._SEED_SELECTION_INDEX[(other_root, "other-digest")] = {}

    def report(*_args, **_kwargs):
        return {
            "selection_complete": True,
            "failed": [],
            "loaded_seed_ids": ["lexicon"],
            "loaded_content_keys_by_seed": {"lexicon": ["known"]},
            "selection": {"content_candidate_resolution": {
                "content_keys": ["known"],
                "unresolved_candidates": ["unprovided"],
                "provider_seed_ids_by_key": {"known": ["lexicon"]},
            }},
        }

    monkeypatch.setattr(boot_all, "load_all_seeds", report)
    monkeypatch.setattr(boot_profiles, "_prewarm_conversation_runtime", lambda: ())
    agent = WorldAdapter(seeds=())
    boot_profiles.load_conversation_seed_profile(
        agent, root, content_candidates=["known", "unprovided"],
        incremental_content_loading=False)

    assert root not in boot_all._SEED_INDEX_MEMORY_CACHE
    assert (root, "digest") not in boot_all._SEED_CONTENT_PROVIDER_INDEX
    assert (root, "digest") not in boot_all._SEED_SELECTION_INDEX
    assert other_root in boot_all._SEED_INDEX_MEMORY_CACHE
    assert (other_root, "other-digest") in boot_all._SEED_CONTENT_PROVIDER_INDEX
    assert (other_root, "other-digest") in boot_all._SEED_SELECTION_INDEX
    result = boot_profiles.load_conversation_content_candidates(
        agent, ["known", "unprovided", "outside-prepass"])
    assert result["status"] == "preload_only_unavailable"
    assert result["not_preloaded"] == ["outside-prepass", "unprovided"]


def test_scoped_typed_content_ref_avoids_same_name_seed_providers(tmp_path):
    (tmp_path / "lexicon.json").write_text(json.dumps({
        "id": "lexicon",
        "selective_content_keys": True,
        "nodes": [
            {"local_id": 1, "type": "Concept",
             "attrs": {"name": "signal", "definition": "lexical"}},
            {"local_id": 2, "type": "Concept",
             "attrs": {"name": "unrequested", "definition": "other"}},
            {"local_id": 3, "type": "Rule",
             "attrs": {"name": "signal"}},
        ],
    }), encoding="utf-8")
    (tmp_path / "communications.json").write_text(json.dumps({
        "id": "communications",
        "nodes": [{"local_id": 1, "type": "Concept",
                   "attrs": {"name": "signal", "definition": "domain"}}],
    }), encoding="utf-8")
    agent = WorldAdapter(seeds=())

    report = load_all_seeds(
        agent, str(tmp_path), scoped_content_refs={
            "lexicon": [{"type": "Concept", "name": "signal"}],
        },
    )

    assert report["selection_complete"] is True
    assert report["selection"]["selected_seed_ids"] == ["lexicon"]
    assert report["selection"]["unresolved"][
        "missing_scoped_content_refs"] == []
    assert report["content_slices"]["lexicon"] == {
        "matched_node_count": 1,
        "source_node_count": 3,
        "requested_refs": [{"type": "Concept", "name": "signal"}],
    }
    concepts = [agent.s.node(node)["attrs"].get("name")
                for node in agent.s.nodes("Concept")]
    assert concepts == ["signal"]
    assert "communications" not in report["order"]

    incomplete_agent = WorldAdapter(seeds=())
    before_concepts = list(incomplete_agent.s.nodes("Concept"))
    incomplete = load_all_seeds(
        incomplete_agent, str(tmp_path), scoped_content_refs={
            "lexicon": [{"type": "Concept", "name": "not-present"}],
        },
    )
    assert incomplete["selection_complete"] is False
    assert incomplete["loaded"] == 0
    assert incomplete["selection"]["unresolved"][
        "missing_scoped_content_refs"] == [
            {"seed_id": "lexicon",
             "ref": {"type": "Concept", "name": "not-present"}},
        ]
    assert list(incomplete_agent.s.nodes("Concept")) == before_concepts


def test_graph_refs_resolve_only_unique_or_explicitly_grouped_providers(tmp_path):
    seeds = {
        "lexicon": {
            "group_keys": ["category:language"],
            "named_content_refs": [{"type": "Concept", "name": "signal"}],
        },
        "sensors": {
            "group_keys": ["category:engineering"],
            "named_content_refs": [
                {"type": "Concept", "name": "sensor"},
                {"type": "Concept", "name": "signal"},
            ],
            "content_connections": [{
                "src": {"type": "Concept", "name": "sensor"},
                "edge": "measures",
                "tgt": {"type": "Concept", "name": "signal"},
            }],
        },
        "colour": {
            "group_keys": ["category:perception"],
            "named_content_refs": [{"type": "Concept", "name": "blue"}],
        },
    }

    scoped, unresolved = resolve_graph_content_refs(
        [
            {"type": "Concept", "name": "blue"},
            {"type": "Concept", "name": "signal"},
        ], seed_index=seeds,
    )
    assert scoped == {"colour": [{"type": "Concept", "name": "blue"}]}
    assert unresolved == {
        "missing_graph_refs": [],
        "ambiguous_graph_refs": [{
            "type": "Concept", "name": "signal",
            "candidate_seed_ids": ["lexicon", "sensors"],
        }],
        "invalid_graph_providers": [],
        "unprovided_graph_refs": [],
    }

    scoped, unresolved = resolve_graph_content_refs(
        [{"type": "Concept", "name": "signal"}], seed_index=seeds,
        group_keys=["category:engineering"],
    )
    assert scoped == {"sensors": [{"type": "Concept", "name": "signal"}]}
    assert unresolved == {
        "missing_graph_refs": [], "ambiguous_graph_refs": [],
        "invalid_graph_providers": [],
        "unprovided_graph_refs": [],
    }
    scoped, unresolved = resolve_graph_content_refs(
        [
            {"type": "Concept", "name": "sensor"},
            {"type": "Concept", "name": "signal"},
        ], seed_index=seeds,
        graph_connections=[{
            "src": {"type": "Concept", "name": "sensor"},
            "edge": "measures",
            "tgt": {"type": "Concept", "name": "signal"},
        }],
    )
    assert scoped == {"sensors": [
        {"type": "Concept", "name": "sensor"},
        {"type": "Concept", "name": "signal"},
    ]}
    assert unresolved == {
        "missing_graph_refs": [], "ambiguous_graph_refs": [],
        "invalid_graph_providers": [],
        "unprovided_graph_refs": [],
    }

    scoped, unresolved = resolve_graph_content_refs(
        [{"type": "Concept", "name": "signal"}], seed_index=seeds,
        graph_provider_refs=[{
            "ref": {"type": "Concept", "name": "signal"},
            "seed_id": "sensors",
        }],
    )
    assert scoped == {"sensors": [{"type": "Concept", "name": "signal"}]}
    assert unresolved == {
        "missing_graph_refs": [], "ambiguous_graph_refs": [],
        "invalid_graph_providers": [],
        "unprovided_graph_refs": [],
    }

    scoped, unresolved = resolve_graph_content_refs(
        [{"type": "Concept", "name": "absent"}], seed_index=seeds,
    )
    assert scoped == {}
    assert unresolved["unprovided_graph_refs"] == [
        {"type": "Concept", "name": "absent"},
    ]
    assert unresolved["missing_graph_refs"] == []

    (tmp_path / "grounded_provider.json").write_text(json.dumps({
        "id": "grounded_provider",
        "category": "language",
        "nodes": [{"local_id": 1, "type": "Concept",
                   "attrs": {"name": "translated_concept"}}],
    }), encoding="utf-8")
    scoped, unresolved = resolve_graph_content_refs(
        [{"type": "Concept", "name": "translated_concept"}],
        seed_dir=str(tmp_path),
    )
    assert scoped == {
        "grounded_provider": [
            {"type": "Concept", "name": "translated_concept"},
        ],
    }
    assert unresolved == {
        "missing_graph_refs": [], "ambiguous_graph_refs": [],
        "invalid_graph_providers": [],
        "unprovided_graph_refs": [],
    }


def test_live_graph_prepass_loads_connected_provider_and_dependencies(tmp_path):
    (tmp_path / "base.json").write_text(json.dumps({
        "id": "base",
        "nodes": [
            {"local_id": 1, "type": "Concept", "attrs": {"name": "sensor"}},
            {"local_id": 2, "type": "Concept", "attrs": {"name": "signal"}},
        ],
    }), encoding="utf-8")
    (tmp_path / "device_core.json").write_text(json.dumps({
        "id": "device_core",
        "nodes": [{"local_id": 1, "type": "Concept",
                   "attrs": {"name": "device_core_content"}}],
    }), encoding="utf-8")
    (tmp_path / "lexicon.json").write_text(json.dumps({
        "id": "lexicon", "selective_content_keys": True,
        "nodes": [{"local_id": 1, "type": "Concept",
                   "attrs": {"name": "signal", "definition": "generic"}}],
    }), encoding="utf-8")
    (tmp_path / "sensors.json").write_text(json.dumps({
        "id": "sensors", "depends_on": ["device_core"],
        "selective_content_keys": True,
        "nodes": [
            {"local_id": 1, "type": "Concept", "attrs": {"name": "sensor"}},
            {"local_id": 2, "type": "Concept", "attrs": {"name": "signal"}},
            {"local_id": 3, "type": "Concept", "attrs": {"name": "unused"}},
        ],
        "relations": [{"src": "sensor", "edge": "measures",
                       "tgt": "signal"}],
    }), encoding="utf-8")

    agent = WorldAdapter(seeds=())
    base_report = load_all_seeds(agent, str(tmp_path), seed_ids={"base"})
    sensor = agent._concept_by_name("sensor")
    signal = agent._concept_by_name("signal")
    agent.inner.add_edge_unchecked(sensor, "measures", signal)
    agent._conversation_seed_profile_state = {
        "seed_dir": str(tmp_path),
        "loaded_seed_ids": set(base_report["loaded_seed_ids"]),
        "loaded_content_by_seed": {
            str(seed_id): set(names)
            for seed_id, names in base_report.get(
                "loaded_content_keys_by_seed", {}).items()
        },
        "loaded_content_keys": set(),
        "known_unprovided_candidates": set(),
        "provider_seed_ids_by_key": {}, "selective_seed_ids": set(),
        "incremental_content_loading": True, "prepass_reports": [],
    }
    result = agent.ingest_semantic_event(
        {"speech_act": "assertion", "relation_scope": "event_specific",
         "content_refs": [
             {"type": "Concept", "name": "sensor"},
             {"type": "Concept", "name": "signal"},
         ]},
        provider="language_adapter:test",
    )
    result = result["content_prepass"]

    assert result["status"] == "loaded", result
    assert result["selected_seed_ids"] == ["device_core", "sensors"]
    assert "lexicon" not in result["selected_seed_ids"]
    assert "device_core" in agent._conversation_seed_profile_state[
        "loaded_seed_ids"]
    assert agent._concept_by_name("sensor") is not None
    assert agent._concept_by_name("signal") is not None
    assert agent._concept_by_name("unused") is None
    assert agent._concept_by_name("device_core_content") is not None
    assert agent._conversation_seed_profile_state[
        "graph_provider_seed_ids_by_ref"] == {
            "Concept:sensor": ["sensors"],
            "Concept:signal": ["sensors"],
        }
    assert agent._conversation_seed_profile_state[
        "loaded_typed_content_by_seed"]["sensors"] == {
            ("Concept", "sensor"), ("Concept", "signal"),
        }

    before = agent.s.node_count()
    ambiguous = load_conversation_graph_content_refs(agent, {
        "refs": [{"type": "Concept", "name": "signal"}],
    })
    assert ambiguous["status"] == "graph_refs_unresolved"
    assert ambiguous["graph_content_resolution"]["ambiguous_graph_refs"]
    assert agent.s.node_count() == before

    ungrounded = load_conversation_graph_content_refs(agent, {
        "refs": [{"type": "Concept", "name": "fabricated"}],
    })
    assert ungrounded["status"] == "graph_refs_unresolved"
    assert ungrounded["graph_content_resolution"]["missing_graph_refs"]
    assert agent.s.node_count() == before

    fabricated_edge = load_conversation_graph_content_refs(agent, {
        "refs": [
            {"type": "Concept", "name": "sensor"},
            {"type": "Concept", "name": "signal"},
        ],
        "graph_connections": [{
            "src": {"type": "Concept", "name": "sensor"},
            "edge": "invented_connection",
            "tgt": {"type": "Concept", "name": "signal"},
        }],
    })
    assert fabricated_edge["status"] == "graph_refs_unresolved"
    assert fabricated_edge["graph_content_resolution"]["missing_graph_refs"]
    assert agent.s.node_count() == before

    # Once sealed, a checkpoint preserves the exact typed provider grouping;
    # resumed ingress can verify it without rebuilding or widening selection.
    state = agent._conversation_seed_profile_state
    state["incremental_content_loading"] = False
    state["content_prepass_manifest_digest"] = "sealed-manifest-digest"
    checkpoint = tmp_path / "graph-connected-profile.json"
    agent.save(checkpoint)
    resumed = WorldAdapter.load(checkpoint)
    assert resumed._conversation_seed_profile_state[
        "content_prepass_manifest_digest"] == "sealed-manifest-digest"
    assert resumed._conversation_seed_profile_state[
        "graph_provider_seed_ids_by_ref"] == state[
            "graph_provider_seed_ids_by_ref"]
    assert resumed._conversation_seed_profile_state[
        "loaded_typed_content_by_seed"]["sensors"] == {
            ("Concept", "sensor"), ("Concept", "signal"),
        }
    already_loaded = load_conversation_graph_content_refs(resumed, {
        "refs": [
            {"type": "Concept", "name": "sensor"},
            {"type": "Concept", "name": "signal"},
        ],
        "graph_provider_refs": [
            {"ref": {"type": "Concept", "name": "sensor"},
             "seed_id": "sensors"},
            {"ref": {"type": "Concept", "name": "signal"},
             "seed_id": "sensors"},
        ],
    })
    assert already_loaded["status"] == "already_available"
    assert already_loaded["seed_loading_performed"] is False


def test_loader_tracks_native_local_to_global_content_provenance(tmp_path):
    (tmp_path / "content.json").write_text(json.dumps({
        "id": "content_seed",
        "nodes": [{"local_id": 41, "type": "Concept",
                   "attrs": {"name": "typed_content"}}],
    }), encoding="utf-8")
    agent = WorldAdapter(seeds=())

    report = load_all_seeds(
        agent, str(tmp_path), track_content_node_provenance=True)

    assert len(report["content_node_provenance"]) == 1
    global_id, source = next(iter(report["content_node_provenance"].items()))
    assert source == {
        "seed_id": "content_seed", "type": "Concept", "name": "typed_content",
    }
    assert global_id in {node.value for node in agent.s.nodes("Concept")}

    ordinary_agent = WorldAdapter(seeds=())
    ordinary_report = load_all_seeds(ordinary_agent, str(tmp_path))
    assert "content_node_provenance" not in ordinary_report


def test_operating_systems_dependency_closure_resolves_llvm_seed_id():
    index, _ = _read_seed_index("seeds")
    order, unresolved = _select_seed_ids(index, seed_ids=["operating_systems"])

    assert {"operating_systems", "compiler_theory", "llvm_passes",
            "llvm_ir_vocabulary"}.issubset(order)
    assert unresolved == {
        "missing_seed_ids": [],
        "missing_content_keys": [],
        "missing_dependencies": [],
        "missing_content_references": [],
    }


def test_load_all_seeds_emits_no_malformed_rule_warnings(capsys):
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    err = capsys.readouterr().err
    assert "skipping malformed rule" not in err


def test_selected_seed_boot_loads_connected_content_closure(tmp_path):
    manifests = {
        "base.json": {
            "id": "base",
            "extra_nodes": [{"type": "ContentAnchor", "name": "target"}],
        },
        "root.json": {
            "id": "root",
            "extra_nodes": [{"type": "SelectionRoot", "name": "root_node"}],
            "relations": [{"src": "root_node", "edge": "uses", "tgt": "target"}],
        },
        "unrelated.json": {
            "id": "unrelated",
            "extra_nodes": [{"type": "Unrelated", "name": "unrelated"}],
        },
    }
    for filename, manifest in manifests.items():
        (tmp_path / filename).write_text(json.dumps(manifest), encoding="utf-8")

    agent = WorldAdapter(seeds=())
    report = load_all_seeds(agent, str(tmp_path), seed_ids=["root"])

    assert report["selection_complete"] is True
    assert set(report["order"]) == {"base", "root"}
    assert report["loaded"] == 2
    assert list(agent.s.nodes("ContentAnchor"))
    assert list(agent.s.nodes("SelectionRoot"))
    assert not list(agent.s.nodes("Unrelated"))
    assert report.get("relations") == 1


def test_named_conversation_profile_resolves_closure_without_unselected_curriculum_faculties(
        monkeypatch):
    agent = WorldAdapter(seeds=())
    imported_optional_faculties = []
    original_import = builtins.__import__

    def track_optional_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "domains":
            imported_optional_faculties.extend(
                item for item in (fromlist or ())
                if item in {"code_curriculum", "curriculum_study"})
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", track_optional_import)
    report = load_conversation_seed_profile(agent)

    assert report["selection_complete"] is True
    # The explicit closure is derived from live seed connectivity; assert that
    # every selected seed loaded rather than freezing the current corpus size.
    assert report["loaded"] == report["total"]
    assert "communication_causal_identity_binding" in report["order"]
    assert "communication_causal_evidence_promotion" in report["order"]
    assert "communication_reported_content_recall" in report["order"]
    assert report["selection"]["unresolved"] == {
        "missing_seed_ids": [],
        "missing_content_keys": [],
        "missing_dependencies": [],
        "missing_content_references": [],
    }
    assert "embodied_motor_program" not in report["order"]
    assert imported_optional_faculties == []


def test_full_seed_boot_keeps_optional_curriculum_dispatches_registered():
    agent = WorldAdapter(seeds=())
    report = load_all_seeds(agent)
    from domains import reflective_faculty

    assert report.get("selection") is None
    assert reflective_faculty._DISPATCH["code_capabilities"].__module__ == (
        "domains.code_curriculum")
    assert reflective_faculty._DISPATCH["emitter_roadmap"].__module__ == (
        "domains.curriculum_study")


def test_selected_seed_boot_rejects_incomplete_closure_before_mutation(tmp_path):
    manifest = {
        "id": "root",
        "depends_on": ["missing_dependency"],
        "extra_nodes": [{"type": "SelectionRoot", "name": "root_node"}],
    }
    (tmp_path / "root.json").write_text(json.dumps(manifest), encoding="utf-8")
    agent = WorldAdapter(seeds=())
    before = (agent.s.node_count(), agent.s.edge_count())

    report = load_all_seeds(agent, str(tmp_path), seed_ids=["root"])

    assert report["status"] == "selection_incomplete"
    assert report["selection_complete"] is False
    assert report["selection"]["unresolved"]["missing_dependencies"] == [
        ("root", "missing_dependency"),
    ]
    assert report["loaded"] == 0
    assert (agent.s.node_count(), agent.s.edge_count()) == before
