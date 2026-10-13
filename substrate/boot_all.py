"""Boot the ENTIRE jabberwock from seeds/ — natively, no domains/.

The agent IS the loaded seeds. This reads every seed JSON in ``seeds/``,
resolves each seed's ``depends_on`` FROM THE JSON ITSELF (not
``domains/seed_registry``), topologically loads each via the Rust
``load_seed_manifest`` (nodes / edges / productions / rules) and registers its
concepts natively (Term-JSON definitions -> the Holds concept registry; every
concept -> a ``Concept`` node so the agent knows it).

This is the substrate-level replacement for
``domains/arc3_full_seed.install_full_seed_set`` — which is ``domains/`` Python
written against the dead CuriousAgent interface (``mind_graph`` /
``_concept_nodes``) and is scheduled for deletion along with the rest of
``domains/``. Pure mechanical loading; no agent logic, no decisions.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import sys
import tempfile

from substrate.seed_loader import SEED_DIR, engine_rules_only

_CONVERSATION_INCREMENTAL_LOAD_TOKEN = object()

_SEED_RULE_NAME_INDEX: dict[str, dict[str, str]] = {}
_SEED_MICROTHEORY_INVENTORY: dict[str, dict] = {}
_SEED_INDEX_SOURCE_DIGEST: dict[str, str] = {}
_SEED_INDEX_MEMORY_CACHE: dict[str, tuple] = {}
_SEED_CONTENT_PROVIDER_INDEX: dict[tuple[str, str], dict[str, list[str]]] = {}
_SEED_SELECTION_INDEX: dict[tuple[str, str], dict] = {}

_INCREMENTAL_SEED_INDEX_FIELDS = (
    "depends_on", "group_keys", "content_keys", "named_content_refs",
    "content_connections", "content_dependencies",
    "content_load_dependencies", "missing_content_references",
    "missing_dependencies", "selective_content_keys",
)


def _compact_incremental_seed_index(seeds: dict) -> dict:
    """Retain only fields required by future connected candidate selections.

    The source-validated full index is used to build the provider and selection
    caches first. An open-ended conversation needs the same dependency and
    typed-connection closure, but not the inventory, rule-name, or summary
    metadata used by other boot/evaluation paths.
    """
    return {
        str(seed_id): {
            key: meta[key] for key in _INCREMENTAL_SEED_INDEX_FIELDS
            if key in meta
        }
        for seed_id, meta in seeds.items()
    }


def _release_seed_index_memory_cache(seed_dir: str) -> None:
    """Release the full per-seed index after a live profile caches its closure map."""
    _SEED_INDEX_MEMORY_CACHE.pop(os.path.realpath(seed_dir), None)


def _release_seed_selection_caches(seed_dir: str) -> None:
    """Drop build-time maps after a sealed conversation prepass.

    The sealed profile keeps its candidate-to-provider result on the agent.
    It will not resolve new candidates, so retaining the complete source index
    and all-seed lookup tables would only consume memory after selection.
    Incremental profiles deliberately keep these caches for later candidates.
    """
    root = os.path.realpath(seed_dir)
    _SEED_INDEX_MEMORY_CACHE.pop(root, None)
    for cache in (_SEED_CONTENT_PROVIDER_INDEX, _SEED_SELECTION_INDEX):
        for key in tuple(cache):
            if key[0] == root:
                cache.pop(key, None)


def _seed_manifest_paths(seed_dir: str) -> list[str]:
    # Hand-authored seeds (seed_dir/*.json) AND the agent's OWN library (seed_dir/generated/*.json) —
    # the affordance for "the jabberwock builds its own seeds": it authors graph data into generated/
    # and the loader installs it alongside the curated seeds (generated loaded after, so it can extend).
    return sorted(glob.glob(os.path.join(seed_dir, "*.json"))) \
        + sorted(glob.glob(os.path.join(seed_dir, "generated", "*.json")))


def _read_seeds(seed_dir: str) -> dict:
    seeds: dict = {}
    for f in _seed_manifest_paths(seed_dir):
        try:
            with open(f, encoding="utf-8") as stream:
                d = json.load(stream)
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        if d.get("self_load_only"):
            # DATA-ONLY defaults loaded ON DEMAND via seed_loader.manifest_for
            # (e.g. the reading pipeline's goal-layer default codebooks, self-
            # loaded by domains/actor_goals.ensure_*_defaults). NOT swept into a
            # full load_all_seeds boot, so they never pollute an agent that did
            # not read a document -- and never over-populate a codebook a test
            # controls. manifest_for reads the file by path, so on-demand load is
            # unaffected. Nothing depends_on these, so skipping is topo-safe.
            continue
        sid = d.get("id") or os.path.basename(f)[:-5]
        seeds[sid] = d
    return seeds


def _intern_seed_index_values(value):
    """Canonicalize repeated source labels in the retained connectivity map."""
    if isinstance(value, str):
        return sys.intern(value)
    if isinstance(value, dict):
        for key, item in tuple(value.items()):
            value[key] = _intern_seed_index_values(item)
        return value
    if isinstance(value, list):
        for offset, item in enumerate(value):
            value[offset] = _intern_seed_index_values(item)
        return value
    if isinstance(value, tuple):
        return tuple(_intern_seed_index_values(item) for item in value)
    return value


def _canonicalize_seed_index(index, paths, rule_name_index,
                             microtheory_inventory):
    """Share repeated IDs/labels across the index and its companion maps."""
    index = {
        sys.intern(seed_id): _intern_seed_index_values(meta)
        for seed_id, meta in index.items()
    }
    paths = {sys.intern(seed_id): path for seed_id, path in paths.items()}
    rule_name_index = {
        sys.intern(name): sys.intern(seed_id)
        for name, seed_id in rule_name_index.items()
    }
    microtheory_inventory = _intern_seed_index_values(
        microtheory_inventory)
    return index, paths, rule_name_index, microtheory_inventory


def _build_seed_index(seed_dir: str) -> tuple[dict, dict[str, str]]:
    """Build the compact boot plan without retaining full manifests.

    This is deliberately a pre-pass: dependencies determine safe ordering,
    while category/microtheory/capability and declared-content keys form the
    cached grouping map for selective loading and seed-provenance lookups.
    Typed graph refs and name-based relation endpoints are resolved against
    declared seed content.
    """
    index: dict = {}
    paths: dict[str, str] = {}
    references_by_seed: dict[str, list[dict]] = {}
    name_references_by_seed: dict[str, list[str]] = {}
    providers_by_type: dict[str, set[str]] = {}
    providers_by_attr: dict[tuple[str, str, str], set[str]] = {}
    provider_keys_by_seed: dict[str, set[tuple]] = {}
    rule_names_by_seed: dict[str, set[str]] = {}

    def add_provider(sid, node_type, attrs):
        keys = provider_keys_by_seed.setdefault(sid, set())
        type_key = ("type", node_type)
        providers_by_type.setdefault(node_type, set()).add(sid)
        keys.add(type_key)
        if isinstance(attrs, dict):
            for attr in ("name", "id"):
                if isinstance(attrs.get(attr), str):
                    value_key = json.dumps(attrs[attr], sort_keys=True,
                                          separators=(",", ":"))
                    provider_key = (node_type, attr, value_key)
                    providers_by_attr.setdefault(provider_key, set()).add(sid)
                    keys.add(("attr",) + provider_key)

    def remove_seed_providers(sid):
        for key in provider_keys_by_seed.pop(sid, set()):
            if key[0] == "type":
                providers_by_type[key[1]].discard(sid)
            else:
                providers_by_attr[key[1:]].discard(sid)
    for path in _seed_manifest_paths(seed_dir):
        try:
            with open(path, encoding="utf-8") as stream:
                manifest = json.load(stream)
        except Exception:
            continue
        if not isinstance(manifest, dict):
            continue
        sid = manifest.get("id") or os.path.basename(path)[:-5]
        rule_names = {
            str(rule["name"])
            for rule in manifest.get("rules", ())
            if isinstance(rule, dict) and rule.get("name")
        }
        rule_names.update(
            str((node.get("attrs") or {})["name"])
            for node in manifest.get("nodes", ())
            if (isinstance(node, dict) and node.get("type") == "Rule"
                and isinstance(node.get("attrs") or {}, dict)
                and (node.get("attrs") or {}).get("name"))
        )
        # Like seed manifests themselves, generated IDs replace hand-authored
        # declarations. Keep self-load-only names in the provenance index even
        # though they are not candidates for bulk installation.
        rule_names_by_seed[sid] = rule_names
        if manifest.get("self_load_only"):
            continue
        # Generated manifests override hand-authored IDs; replace their
        # provider signatures just as the boot index replaces their metadata.
        remove_seed_providers(sid)
        for node in manifest.get("nodes", ()):
            if isinstance(node, dict) and node.get("type"):
                add_provider(sid, str(node["type"]), node.get("attrs") or {})
        for concept in manifest.get("concepts", ()):
            if isinstance(concept, dict):
                add_provider(sid, "Concept",
                             {k: v for k, v in concept.items() if k != "local_id"})
        declared_mt = manifest.get("microtheory")
        if isinstance(declared_mt, dict) and isinstance(declared_mt.get("name"), str):
            add_provider(sid, "Microtheory", declared_mt)
        elif isinstance(declared_mt, str):
            add_provider(sid, "Microtheory", {"name": declared_mt})
        microtheory = manifest.get("microtheory")
        category = manifest.get("category")
        if isinstance(microtheory, dict):
            category = category or microtheory.get("category") or microtheory.get("domain")
            microtheory = microtheory.get("name")
        node_types = sorted({
            str(node.get("type")) for node in manifest.get("nodes", ())
            if isinstance(node, dict) and node.get("type")
        })
        references = [
            dict(ref)
            for edge in manifest.get("edges", ()) if isinstance(edge, dict)
            for side in ("src", "tgt")
            for ref in (edge.get(side),)
            if (isinstance(ref, dict) and isinstance(ref.get("type"), str)
                and "local" not in ref and "role" not in ref)
        ]
        content_keys = set()
        named_content_refs = set()
        for concept in manifest.get("concepts", ()):
            if isinstance(concept, dict) and concept.get("name"):
                content_keys.add(str(concept["name"]))
                named_content_refs.add(("Concept", str(concept["name"])))
        for node in manifest.get("nodes", ()):
            if not isinstance(node, dict):
                continue
            attrs = node.get("attrs") or {}
            if isinstance(attrs, dict) and attrs.get("name"):
                content_keys.add(str(attrs["name"]))
                if node.get("type"):
                    named_content_refs.add((str(node["type"]),
                                            str(attrs["name"])))
        for rule in manifest.get("rules", ()):
            if isinstance(rule, dict) and rule.get("name"):
                name = str(rule["name"])
                content_keys.add(name)
        for extra_node in manifest.get("extra_nodes", ()):
            if isinstance(extra_node, dict) and extra_node.get("name"):
                content_keys.add(str(extra_node["name"]))
                if extra_node.get("type"):
                    named_content_refs.add((str(extra_node["type"]),
                                            str(extra_node["name"])))
        local_content_refs = {}
        for node in manifest.get("nodes", ()):
            if not isinstance(node, dict) or node.get("local_id") is None:
                continue
            attrs = node.get("attrs") or {}
            if node.get("type") and isinstance(attrs, dict) and attrs.get("name"):
                local_content_refs[str(node["local_id"])] = (
                    str(node["type"]), str(attrs["name"]))
        for concept in manifest.get("concepts", ()):
            if (isinstance(concept, dict) and concept.get("local_id") is not None
                    and concept.get("name")):
                local_content_refs[str(concept["local_id"])] = (
                    "Concept", str(concept["name"]))

        def content_signature(ref):
            if not isinstance(ref, dict):
                return None
            if "local" in ref:
                return local_content_refs.get(str(ref["local"]))
            if (isinstance(ref.get("type"), str)
                    and isinstance(ref.get("name"), str)):
                return ref["type"], ref["name"]
            return None

        content_connections = set()
        for edge in manifest.get("edges", ()):
            if not isinstance(edge, dict):
                continue
            source = content_signature(edge.get("src"))
            target = content_signature(edge.get("tgt"))
            edge_type = edge.get("type")
            if (source and target and isinstance(edge_type, str)
                    and edge_type):
                content_connections.add((source[0], source[1], edge_type,
                                         target[0], target[1]))
        typed_names_by_name: dict[str, set[tuple[str, str]]] = {}
        for node_type, name in named_content_refs:
            typed_names_by_name.setdefault(name, set()).add((node_type, name))
        for relation in manifest.get("relations", ()):
            if (not isinstance(relation, dict)
                    or not isinstance(relation.get("src"), str)
                    or not isinstance(relation.get("tgt"), str)
                    or not isinstance(relation.get("edge"), str)):
                continue
            for source in typed_names_by_name.get(relation["src"], ()):
                for target in typed_names_by_name.get(relation["tgt"], ()):
                    content_connections.add((
                        source[0], source[1], relation["edge"],
                        target[0], target[1]))
        inventory_areas = {
            str(name) for node_type, name in named_content_refs
            if node_type == "Microtheory"
        }
        inventory_concept_connections = []
        manifest_mt = manifest.get("microtheory")
        inventory_mt_name = (
            manifest_mt.get("name") if isinstance(manifest_mt, dict)
            else manifest_mt if isinstance(manifest_mt, str) else None
        )
        if (not inventory_mt_name and "nodes" not in manifest
                and manifest.get("id")
                and (manifest.get("concepts") or manifest.get("rules"))):
            inventory_mt_name = str(manifest["id"])
        if inventory_mt_name:
            inventory_mt_name = str(inventory_mt_name)
            inventory_areas.add(inventory_mt_name)
            inventory_concept_connections.extend(
                (inventory_mt_name, str(concept["name"]))
                for concept in manifest.get("concepts", ())
                if isinstance(concept, dict) and concept.get("name")
            )
        for edge in manifest.get("edges", ()):
            if not isinstance(edge, dict) or edge.get("type") != "has_concept":
                continue
            source = content_signature(edge.get("src"))
            target = content_signature(edge.get("tgt"))
            if (source and target and source[0] == "Microtheory"
                    and target[0] == "Concept"):
                inventory_concept_connections.append(
                    (str(source[1]), str(target[1])))
        inventory_name_relations = [
            [str(relation["src"]), str(relation["tgt"])]
            for relation in manifest.get("relations", ())
            if isinstance(relation, dict)
            and relation.get("edge") == "has_concept"
            and isinstance(relation.get("src"), str)
            and isinstance(relation.get("tgt"), str)
        ]
        if microtheory:
            content_keys.add(str(microtheory))
        elif ("nodes" not in manifest and manifest.get("id")
              and (manifest.get("concepts") or manifest.get("rules"))):
            content_keys.add(str(manifest["id"]))
        name_references = [
            str(rel[key])
            for rel in manifest.get("relations", ())
            if isinstance(rel, dict)
            for key in ("src", "tgt")
            if isinstance(rel.get(key), str) and rel.get(key)
        ]
        mt = manifest.get("microtheory")
        parent_name = ((mt.get("parent") if isinstance(mt, dict) else None)
                       or manifest.get("parent_mt") or manifest.get("parent"))
        if isinstance(parent_name, str) and parent_name:
            name_references.append(parent_name)
        group_keys = set()
        if isinstance(category, str) and category:
            group_keys.add(f"category:{category}")
        if isinstance(microtheory, str) and microtheory:
            group_keys.add(f"microtheory:{microtheory}")
        group_keys.update(
            f"capability:{key}" for key in manifest.get("capability_keys") or []
            if isinstance(key, str) and key
        )
        # Preserve generated-seed override ordering from _read_seeds.
        index[sid] = {
            "id": sid,
            "selective_content_keys": bool(
                manifest.get("selective_content_keys", False)),
            "depends_on": manifest.get("depends_on") or [],
            "category": category,
            "microtheory": microtheory,
            "capability_keys": sorted({
                key for key in (manifest.get("capability_keys") or [])
                if isinstance(key, str) and key
            }),
            "group_keys": sorted(group_keys),
            "node_types": node_types,
            "content_keys": sorted(content_keys),
            "named_content_refs": [
                {"type": node_type, "name": name}
                for node_type, name in sorted(named_content_refs)
            ],
            "content_connections": [
                {"src": {"type": row[0], "name": row[1]},
                 "edge": row[2],
                 "tgt": {"type": row[3], "name": row[4]}}
                for row in sorted(content_connections)
            ],
            "inventory_areas": sorted(inventory_areas),
            "inventory_concept_connections": [
                [area, concept]
                for area, concept in sorted(inventory_concept_connections)
            ],
            "inventory_name_relations": inventory_name_relations,
            "rule_names": sorted(rule_names),
        }
        paths[sid] = os.path.realpath(path)
        references_by_seed[sid] = references
        name_references_by_seed[sid] = name_references

    for sid, references in references_by_seed.items():
        content_dependencies = set()
        missing_references = []
        ambiguous_references = 0
        for reference in references:
            node_type = reference["type"]
            ref_attrs = {key: value for key, value in reference.items()
                         if key != "type"}
            if not ref_attrs:
                providers = providers_by_type.get(node_type, set())
            elif (len(ref_attrs) == 1
                  and next(iter(ref_attrs)) in {"name", "id"}
                  and isinstance(next(iter(ref_attrs.values())), str)):
                attr, value = next(iter(ref_attrs.items()))
                value_key = json.dumps(value, sort_keys=True, separators=(",", ":"))
                providers = providers_by_attr.get((node_type, attr, value_key), set())
            else:
                # Only name/id and type-only cross-ref shapes are indexed. A
                # richer ref is surfaced unresolved until its signature form
                # is explicitly supported by this pre-pass.
                providers = set()
            ambiguous_references += len(providers) > 1
            if not providers:
                missing_references.append(reference)
            content_dependencies.update(providers - {sid})
        index[sid]["content_dependencies"] = sorted(content_dependencies)
        index[sid]["content_load_dependencies"] = sorted(content_dependencies)
        index[sid]["missing_content_references"] = missing_references
        index[sid]["typed_content_reference_count"] = len(references)
        index[sid]["ambiguous_content_reference_count"] = ambiguous_references
    providers_by_content_key: dict[str, set[str]] = {}
    for sid, meta in index.items():
        for key in meta["content_keys"]:
            providers_by_content_key.setdefault(key, set()).add(sid)
    for sid, name_references in name_references_by_seed.items():
        content_dependencies = set(index[sid]["content_dependencies"])
        missing_references = list(index[sid]["missing_content_references"])
        for name in name_references:
            providers = providers_by_content_key.get(name, set())
            content_dependencies.update(providers - {sid})
            index[sid]["ambiguous_content_reference_count"] += len(providers) > 1
            if not providers:
                missing_references.append({"type": "name", "name": name})
        index[sid]["content_dependencies"] = sorted(content_dependencies)
        index[sid]["missing_content_references"] = missing_references
        index[sid]["name_content_reference_count"] = len(name_references)
    for meta in index.values():
        meta["missing_dependencies"] = sorted({
            dependency for dependency in meta["depends_on"]
            if dependency not in index
        })
    inventory_areas = {
        area for meta in index.values()
        for area in meta.get("inventory_areas", ())
    }
    inventory_concepts = {
        row["name"]
        for meta in index.values()
        for row in meta.get("named_content_refs", ())
        if row.get("type") == "Concept"
    }
    inventory_counts = {area: 0 for area in inventory_areas}
    for meta in index.values():
        for area, concept in meta.get("inventory_concept_connections", ()):
            if area in inventory_counts and concept in inventory_concepts:
                inventory_counts[area] += 1
        for area, concept in meta.get("inventory_name_relations", ()):
            if area in inventory_counts and concept in inventory_concepts:
                inventory_counts[area] += 1
    inventory = {
        "schema": "seed_microtheory_inventory.v1",
        "areas": [
            {"name": area, "concept_count": count}
            for area, count in sorted(
                inventory_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
    }
    # The per-manifest edge contributions are only build-time inputs. Keep
    # the persistent connectivity index compact: its cache stores the merged
    # inventory above, not every contributing Concept name for every seed.
    for meta in index.values():
        meta.pop("inventory_areas", None)
        meta.pop("inventory_concept_connections", None)
        meta.pop("inventory_name_relations", None)
    rule_name_index: dict[str, str] = {}
    for sid, names in rule_names_by_seed.items():
        for name in names:
            rule_name_index.setdefault(name, sid)
    index, paths, rule_name_index, inventory = _canonicalize_seed_index(
        index, paths, rule_name_index, inventory)
    _SEED_RULE_NAME_INDEX[os.path.realpath(seed_dir)] = rule_name_index
    _SEED_MICROTHEORY_INVENTORY[os.path.realpath(seed_dir)] = inventory
    return index, paths


# Bump this when _build_seed_index's output semantics change; source bytes and
# this schema jointly define the persistent derived-cache validity boundary.
_SEED_INDEX_CACHE_SCHEMA = "ocelot-seed-connectivity-index.v11"


def _seed_index_cache_path(seed_dir: str) -> str:
    """Return a per-user temp-cache path; the cache is disposable and derived."""
    root = os.path.realpath(seed_dir)
    root_key = hashlib.sha256(root.encode("utf-8")).hexdigest()
    user_id = getattr(os, "getuid", lambda: 0)()
    return os.path.join(
        tempfile.gettempdir(), f"ocelot-seed-index-v1-{user_id}",
        f"{root_key}.json",
    )


def _seed_sources_digest(seed_dir: str, paths: list[str]) -> str:
    """Hash path identity and file bytes without retaining manifest contents."""
    root = os.path.realpath(seed_dir)
    digest = hashlib.sha256()
    for path in paths:
        relative = os.path.relpath(os.path.realpath(path), root).replace(os.sep, "/")
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        with open(path, "rb") as stream:
            digest.update(hashlib.file_digest(stream, "sha256").digest())
        digest.update(b"\0")
    return digest.hexdigest()


def _seed_sources_stat_snapshot(paths: list[str]) -> tuple | None:
    """Return a cheap runtime change detector for a validated seed index.

    Index construction/cache validation remains content-hash based. The live
    conversation profile uses this metadata snapshot between novel lexical
    candidates and pays the full digest only when a manifest set or stat
    changes. Seed manifests are immutable during ordinary turns; generated
    manifest additions and edits change this snapshot and force full
    revalidation before the map is reused.
    """
    snapshot = []
    try:
        # `_seed_manifest_paths()` already yields a deterministic path set.
        # Normalize lexically here; realpath() performs several lstat calls
        # per path and erased much of the intended metadata-check savings.
        for path in sorted(os.path.abspath(path) for path in paths):
            stat = os.stat(path)
            snapshot.append((path, int(stat.st_size), int(stat.st_mtime_ns)))
    except OSError:
        return None
    return tuple(snapshot)


def _seed_index_payload_digest(index: dict, paths: dict[str, str],
                               rule_name_index: dict[str, str],
                               microtheory_inventory: dict) -> str:
    body = json.dumps(
        {"index": index, "paths": paths,
         "rule_name_index": rule_name_index,
         "microtheory_inventory": microtheory_inventory}, sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def _read_seed_index(seed_dir: str) -> tuple[dict, dict[str, str]]:
    """Load the cached connectivity map or build and atomically refresh it.

    A process-local validated index is reused while its complete manifest-path
    and stat snapshot is unchanged. Any metadata change forces the full source
    digest and persistent-cache validation; a cold process always hashes all
    sources. Hashing is streaming and does not load the corpus into memory.
    """
    seed_dir = str(seed_dir)
    manifest_paths = _seed_manifest_paths(seed_dir)
    root = os.path.realpath(seed_dir)
    source_stat = _seed_sources_stat_snapshot(manifest_paths)
    memory_cached = _SEED_INDEX_MEMORY_CACHE.get(root)
    if (source_stat is not None and memory_cached is not None
            and memory_cached[0] == source_stat):
        _, source_digest, index, paths, rule_name_index, inventory = memory_cached
        _SEED_INDEX_SOURCE_DIGEST[root] = source_digest
        _SEED_RULE_NAME_INDEX[root] = rule_name_index
        _SEED_MICROTHEORY_INVENTORY[root] = inventory
        return index, paths
    try:
        source_digest = _seed_sources_digest(seed_dir, manifest_paths)
    except OSError:
        # Preserve the regular loader's best-effort handling of unreadable
        # manifests; simply skip cache lookup/write for this pass.
        _SEED_INDEX_SOURCE_DIGEST.pop(root, None)
        _SEED_INDEX_MEMORY_CACHE.pop(root, None)
        return _build_seed_index(seed_dir)

    cache_path = _seed_index_cache_path(seed_dir)
    source_paths = {os.path.realpath(path) for path in manifest_paths}
    try:
        with open(cache_path, encoding="utf-8") as stream:
            cached = json.load(stream)
        index, paths = cached.get("index"), cached.get("paths")
        rule_name_index = cached.get("rule_name_index")
        microtheory_inventory = cached.get("microtheory_inventory")
        if (cached.get("schema") == _SEED_INDEX_CACHE_SCHEMA
                and cached.get("source_digest") == source_digest
                and isinstance(index, dict) and isinstance(paths, dict)
                and isinstance(rule_name_index, dict)
                and isinstance(microtheory_inventory, dict)
                and set(index) == set(paths)
                and all(os.path.realpath(path) in source_paths
                        for path in paths.values())
                and cached.get("payload_digest") ==
                    _seed_index_payload_digest(
                        index, paths, rule_name_index, microtheory_inventory)):
            index, paths, rule_name_index, microtheory_inventory = (
                _canonicalize_seed_index(
                    index, paths, rule_name_index, microtheory_inventory))
            _SEED_RULE_NAME_INDEX[os.path.realpath(seed_dir)] = rule_name_index
            _SEED_INDEX_SOURCE_DIGEST[os.path.realpath(seed_dir)] = source_digest
            microtheory_inventory = dict(microtheory_inventory)
            microtheory_inventory["source_digest"] = source_digest
            _SEED_MICROTHEORY_INVENTORY[os.path.realpath(seed_dir)] = microtheory_inventory
            _SEED_INDEX_MEMORY_CACHE[root] = (
                source_stat, source_digest, index, paths, rule_name_index,
                microtheory_inventory)
            return index, paths
    except (OSError, ValueError, TypeError, AttributeError):
        pass

    index, paths = _build_seed_index(seed_dir)
    _SEED_INDEX_SOURCE_DIGEST[os.path.realpath(seed_dir)] = source_digest
    rule_name_index = _SEED_RULE_NAME_INDEX.get(os.path.realpath(seed_dir), {})
    microtheory_inventory = _SEED_MICROTHEORY_INVENTORY.get(
        os.path.realpath(seed_dir), {})
    microtheory_inventory = dict(microtheory_inventory)
    index, paths, rule_name_index, microtheory_inventory = (
        _canonicalize_seed_index(
            index, paths, rule_name_index, microtheory_inventory))
    microtheory_inventory["source_digest"] = source_digest
    _SEED_MICROTHEORY_INVENTORY[os.path.realpath(seed_dir)] = microtheory_inventory
    _SEED_INDEX_MEMORY_CACHE[root] = (
        source_stat, source_digest, index, paths, rule_name_index,
        microtheory_inventory)
    envelope = {
        "schema": _SEED_INDEX_CACHE_SCHEMA,
        "source_digest": source_digest,
        "payload_digest": _seed_index_payload_digest(
            index, paths, rule_name_index, microtheory_inventory),
        "index": index,
        "paths": paths,
        "rule_name_index": rule_name_index,
        "microtheory_inventory": microtheory_inventory,
    }
    temporary_path = None
    try:
        cache_directory = os.path.dirname(cache_path)
        os.makedirs(cache_directory, mode=0o700, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=cache_directory,
            prefix="seed-index-", suffix=".tmp", delete=False,
        ) as stream:
            temporary_path = stream.name
            # `index` insertion order determines the deterministic tie order
            # used by _topo_order. Preserve it across cold and warm loads;
            # sorting JSON object keys silently changed seed installation and
            # native rule order after the first cache write.
            json.dump(envelope, stream, sort_keys=False, separators=(",", ":"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, cache_path)
    except OSError:
        # The derived cache is an optimization, never a boot prerequisite.
        pass
    finally:
        if temporary_path and os.path.exists(temporary_path):
            try:
                os.unlink(temporary_path)
            except OSError:
                pass
    return index, paths


def seed_microtheory_inventory(seed_dir=None) -> dict:
    """Return the source-validated, seed-derived Microtheory summary.

    The same connectivity pre-pass that selects bounded boot closures derives
    this compact inventory. Callers may materialize it into the graph as a
    summary node without loading every area seed or its Concept content.
    """
    root = str(seed_dir or SEED_DIR)
    _read_seed_index(root)
    return json.loads(json.dumps(
        _SEED_MICROTHEORY_INVENTORY.get(os.path.realpath(root), {})))


def _read_seed_rule_name_index(seed_dir: str) -> dict[str, str]:
    """Return rule provenance derived in the same source-validated pre-pass."""
    _read_seed_index(seed_dir)
    return _SEED_RULE_NAME_INDEX.get(os.path.realpath(seed_dir), {})


def _topo_order(seeds: dict, *, include_content_dependencies=False) -> list:
    """Topological order over the seeds' own ``depends_on`` edges (cycle-safe,
    missing deps skipped) — deps load before dependents. Optional typed-content
    edges are resolved by the native loader during installation; name-based
    legacy relations resolve after all seeds load and expand selection closure
    without constraining install order."""
    order: list = []
    state: dict = {}  # sid -> 0 visiting / 1 done

    def visit(sid: str) -> None:
        if state.get(sid) is not None:
            return  # done, or currently visiting (cycle) — either way skip
        state[sid] = 0
        meta = seeds.get(sid, {})
        dependencies = list(meta.get("depends_on") or [])
        if include_content_dependencies:
            dependencies.extend(meta.get("content_load_dependencies") or [])
        for dep in dependencies:
            if dep in seeds:
                visit(dep)
        state[sid] = 1
        order.append(sid)

    for sid in seeds:
        visit(sid)
    return order


def _select_seed_ids(
    seeds: dict,
    *,
    seed_ids=(),
    group_keys=(),
    content_keys=(),
    scoped_content_refs=None,
    selection_index=None,
) -> tuple[list[str], dict[str, list[str]]]:
    """Resolve a selection through the pre-pass map and dependency closure.

    Exact content-key matches may have multiple providers, so all providers are
    included rather than making a lexical or recency-based choice. Group keys
    are explicit manifest metadata (category, microtheory, capability), not
    inferred from seed names. ``scoped_content_refs`` selects exact typed names
    only inside the explicitly named seed; it does not expand same-name global
    providers.
    """
    requested = set(seed_ids)
    full_requested = set(requested)
    scoped_refs_by_seed: dict[str, set[tuple[str, str]]] = {}
    missing_scoped_content_refs = []
    for raw_sid, refs in (scoped_content_refs or {}).items():
        sid = str(raw_sid)
        requested.add(sid)
        seed = seeds.get(sid)
        available = {
            (row.get("type"), row.get("name"))
            for row in (seed or {}).get("named_content_refs", ())
        }
        for ref in refs or ():
            if not isinstance(ref, dict):
                missing_scoped_content_refs.append({"seed_id": sid,
                                                    "ref": ref})
                continue
            signature = (ref.get("type"), ref.get("name"))
            if (not isinstance(signature[0], str)
                    or not isinstance(signature[1], str)
                    or signature not in available):
                missing_scoped_content_refs.append({
                    "seed_id": sid, "ref": dict(ref),
                })
            else:
                scoped_refs_by_seed.setdefault(sid, set()).add(signature)
    selection_index = selection_index or _build_seed_selection_index(seeds)
    group_providers = selection_index["group_key_providers"]
    group_seeds = set().union(*(
        group_providers.get(key, ()) for key in set(group_keys)
    )) if group_keys else set()
    requested.update(group_seeds)
    full_requested.update(group_seeds)
    providers = selection_index["content_key_providers"]
    concept_providers = selection_index["concept_content_providers"]
    missing_content = []
    for key in content_keys:
        matches = providers.get(key, concept_providers.get(key, ()))
        if not matches:
            missing_content.append(key)
        requested.update(matches)
        full_requested.update(matches)

    missing_seeds = sorted(requested - set(seeds))
    selected = requested - set(missing_seeds)
    closure = set(selected)
    full_queue = [sid for sid in selected
                  if sid in full_requested or sid not in scoped_refs_by_seed]
    scoped_queue = [
        (sid, signature)
        for sid, refs in scoped_refs_by_seed.items() if sid in closure
        for signature in refs
    ]
    typed_nonconcept_providers = selection_index[
        "typed_nonconcept_providers"]
    concept_providers = selection_index["concept_content_providers"]
    traversed_full = set()
    traversed_scoped = set()
    while full_queue or scoped_queue:
        if full_queue:
            sid = full_queue.pop()
            if sid in traversed_full:
                continue
            traversed_full.add(sid)
            dependencies = list(seeds[sid].get("depends_on") or ())
            dependencies.extend(seeds[sid].get("content_dependencies") or ())
            for dependency in dependencies:
                if dependency in seeds and dependency not in closure:
                    closure.add(dependency)
                    full_queue.append(dependency)
            # Full-seed selection dominates any narrower refs for that seed.
            continue

        sid, signature = scoped_queue.pop()
        if (sid, signature) in traversed_scoped or sid in traversed_full:
            continue
        traversed_scoped.add((sid, signature))
        # Declared seed dependencies are required even when only one content
        # node is selected. Cross-content dependencies, however, are followed
        # one content edge from this node, rather than recursively traversing
        # an entire connected component or unrelated manifest content.
        for dependency in seeds[sid].get("depends_on") or ():
            if dependency in seeds and dependency not in closure:
                closure.add(dependency)
                full_queue.append(dependency)
        for connection in seeds[sid].get("content_connections") or ():
            src = connection.get("src") or {}
            tgt = connection.get("tgt") or {}
            src_signature = (src.get("type"), src.get("name"))
            tgt_signature = (tgt.get("type"), tgt.get("name"))
            if src_signature == signature:
                neighbour = tgt_signature
            elif tgt_signature == signature:
                neighbour = src_signature
            else:
                continue
            if neighbour[0] == "Concept":
                neighbour_providers = set(
                    concept_providers.get(neighbour[1], ()))
            else:
                neighbour_providers = set(
                    typed_nonconcept_providers.get(neighbour, ()))
            # Prefer the provider already carrying the selected source node:
            # it is the strongest available context for this edge. If the
            # endpoint lives elsewhere, retain providers from the same
            # explicit content group. Only use an ungrouped global provider
            # when it is unique; loading every same-named provider here makes
            # an unrelated lexicon/domain leak into an otherwise scoped boot.
            current_refs = {
                (row.get("type"), row.get("name"))
                for row in seeds[sid].get("named_content_refs") or ()
                if isinstance(row, dict)
            }
            if neighbour in current_refs:
                neighbour_providers = {sid}
            else:
                declared_load_dependencies = set(
                    seeds[sid].get("content_load_dependencies") or ())
                declared_providers = neighbour_providers & declared_load_dependencies
                if declared_providers:
                    neighbour_providers = declared_providers
                else:
                    source_groups = set(seeds[sid].get("group_keys") or ())
                    same_group = {
                        provider for provider in neighbour_providers
                        if source_groups & set(
                            seeds[provider].get("group_keys") or ())
                    }
                    if same_group:
                        neighbour_providers = same_group
                    elif len(neighbour_providers) != 1:
                        neighbour_providers = set()
            for provider in sorted(neighbour_providers):
                if provider not in closure:
                    closure.add(provider)
                if provider not in traversed_full:
                    scoped_refs_by_seed.setdefault(provider, set()).add(neighbour)
                    for dependency in seeds[provider].get("depends_on") or ():
                        if dependency in seeds and dependency not in closure:
                            closure.add(dependency)
                            full_queue.append(dependency)
    if isinstance(scoped_content_refs, dict):
        scoped_content_refs.clear()
        scoped_content_refs.update({
            sid: [
                {"type": node_type, "name": name}
                for node_type, name in sorted(refs)
            ]
            for sid, refs in scoped_refs_by_seed.items()
        })
    order = [sid for sid in selection_index["topological_order"]
             if sid in closure]
    missing_dependencies = sorted(
        (sid, dependency)
        for sid in closure
        for dependency in seeds[sid].get("missing_dependencies", ())
    )
    unresolved = {
        "missing_seed_ids": missing_seeds,
        "missing_content_keys": sorted(missing_content),
        "missing_dependencies": missing_dependencies,
        "missing_content_references": sorted(
            (sid, json.dumps(reference, sort_keys=True, separators=(",", ":")))
            for sid in closure
            for reference in seeds[sid].get("missing_content_references", ())
        ),
    }
    if scoped_content_refs is not None:
        unresolved["missing_scoped_content_refs"] = sorted(
            missing_scoped_content_refs,
            key=lambda row: json.dumps(row, sort_keys=True, default=str),
        )
    return order, unresolved


def _build_seed_content_provider_index(seeds: dict) -> dict[str, list[str]]:
    providers: dict[str, list[str]] = {}
    for seed_id, meta in seeds.items():
        for reference in meta.get("named_content_refs") or ():
            if (isinstance(reference, dict)
                    and reference.get("type") == "Concept"
                    and isinstance(reference.get("name"), str)):
                providers.setdefault(reference["name"], []).append(
                    str(seed_id))
    return {key: sorted(set(seed_ids))
            for key, seed_ids in providers.items()}


def _seed_content_provider_index(
        seeds: dict, seed_dir: str | None = None) -> dict[str, list[str]]:
    cache_key = None
    if seed_dir is not None:
        root = os.path.realpath(seed_dir)
        source_digest = _SEED_INDEX_SOURCE_DIGEST.get(root)
        if source_digest:
            cache_key = (root, source_digest)
            cached = _SEED_CONTENT_PROVIDER_INDEX.get(cache_key)
            if cached is not None:
                return cached
    providers = _build_seed_content_provider_index(seeds)
    if cache_key is not None:
        for old_key in list(_SEED_CONTENT_PROVIDER_INDEX):
            if old_key[0] == cache_key[0] and old_key != cache_key:
                _SEED_CONTENT_PROVIDER_INDEX.pop(old_key, None)
        _SEED_CONTENT_PROVIDER_INDEX[cache_key] = providers
    return providers


def _build_seed_selection_index(
        seeds: dict, concept_content_providers=None) -> dict:
    """Build immutable lookup tables used by repeated connected closures."""
    concept_content_providers = (
        concept_content_providers
        if concept_content_providers is not None
        else _build_seed_content_provider_index(seeds)
    )
    content_key_providers: dict[str, list[str]] = {}
    group_key_providers: dict[str, set[str]] = {}
    typed_content_providers: dict[tuple[str, str], set[str]] = {}
    for seed_id, meta in seeds.items():
        for key in meta.get("content_keys") or ():
            content_key_providers.setdefault(key, []).append(seed_id)
        for key in meta.get("group_keys") or ():
            group_key_providers.setdefault(key, set()).add(seed_id)
        for row in meta.get("named_content_refs") or ():
            if (isinstance(row, dict) and isinstance(row.get("type"), str)
                    and isinstance(row.get("name"), str)):
                if row["type"] == "Concept":
                    continue
                typed_content_providers.setdefault(
                    (row["type"], row["name"]), set()).add(seed_id)
    # Concept names dominate content keys and already have a validated
    # provider map shared with candidate resolution. Store only content-key
    # deltas whose provider set differs; selectors fall back to the Concept
    # map for omitted equal entries. This avoids a duplicate list/dict entry
    # for the common case without changing provider collisions or closure.
    for key in tuple(content_key_providers):
        if set(content_key_providers[key]) == set(
                concept_content_providers.get(key, ())):
            content_key_providers.pop(key)
    return {
        "content_key_providers": content_key_providers,
        "group_key_providers": group_key_providers,
        # Concept provider names are the dominant typed content population;
        # share the already-cached provider map instead of duplicating every
        # key as a (type,name)->set entry.
        "concept_content_providers": concept_content_providers,
        "typed_nonconcept_providers": typed_content_providers,
        "topological_order": _topo_order(
            seeds, include_content_dependencies=True),
    }


def _seed_selection_index(seeds: dict, seed_dir: str | None = None) -> dict:
    """Return lookup tables cached against the validated manifest digest."""
    cache_key = None
    if seed_dir is not None:
        root = os.path.realpath(seed_dir)
        source_digest = _SEED_INDEX_SOURCE_DIGEST.get(root)
        if source_digest:
            cache_key = (root, source_digest)
            cached = _SEED_SELECTION_INDEX.get(cache_key)
            if cached is not None:
                return cached
    index = _build_seed_selection_index(
        seeds, concept_content_providers=_seed_content_provider_index(
            seeds, seed_dir))
    if cache_key is not None:
        for old_key in list(_SEED_SELECTION_INDEX):
            if old_key[0] == cache_key[0] and old_key != cache_key:
                _SEED_SELECTION_INDEX.pop(old_key, None)
        _SEED_SELECTION_INDEX[cache_key] = index
    return index


def resolve_seed_content_candidates(seeds: dict, candidates=(), *,
                                    seed_dir: str | None = None) -> dict:
    """Resolve upstream lexical/content candidates against indexed providers.

    Unknown candidates are reported separately instead of being passed to the
    strict selector as missing content keys. This keeps OOV input unresolved
    without making an otherwise complete connected closure fail.
    """
    providers = _seed_content_provider_index(seeds, seed_dir)
    requested = sorted({str(key) for key in candidates if str(key)})
    resolved = [key for key in requested if key in providers]
    return {
        "candidates": requested,
        "content_keys": resolved,
        "unresolved_candidates": [key for key in requested if key not in providers],
        "provider_seed_ids_by_key": {key: providers[key] for key in resolved},
        "scoped_content_refs_by_seed": {
            seed_id: [
                {"type": "Concept", "name": key}
                for key in resolved if seed_id in providers[key]
            ]
            for seed_id in sorted({
                seed_id for key in resolved for seed_id in providers[key]
            })
        },
        "provider_seed_ids": sorted({
            seed_id for key in resolved for seed_id in providers[key]
        }),
    }


def resolve_graph_content_refs(
    graph_refs,
    *,
    seed_dir=None,
    seed_index=None,
    group_keys=(),
    graph_connections=(),
    graph_ref_contexts=(),
    graph_provider_refs=(),
) -> tuple[dict[str, list[dict]], dict]:
    """Bind typed refs already resolved by cognition to seed providers.

    ``graph_refs`` is deliberately a graph-boundary contract: each item is a
    ``{type, name}`` readback from a resolved graph node, never an utterance
    token or an expected-label annotation. Provider collisions are rejected
    unless explicit graph context (category/microtheory/capability group keys)
    or direct typed graph connections declared by a provider narrow the ref
    to exactly one seed. This keeps provider choice
    deterministic and prevents a common Concept name from pulling unrelated
    seed families into the content closure.

    The provider map comes from the source-validated cached seed index unless
    an index is injected by a caller/test. The returned scoped refs can be
    passed directly to ``load_all_seeds``.
    Ambiguities and missing refs are returned as diagnostics; callers must not
    silently pick a provider or convert them back to lexical matching.
    """
    if seed_index is None:
        seed_index, _ = _read_seed_index(str(seed_dir or SEED_DIR))
    seeds = seed_index
    candidates_by_ref: dict[tuple[str, str], set[str]] = {}
    connection_providers: dict[
        tuple[tuple[str, str], str, tuple[str, str]], set[str]
    ] = {}
    for sid, meta in seeds.items():
        for row in meta.get("named_content_refs", ()):
            if isinstance(row, dict):
                signature = (row.get("type"), row.get("name"))
                if all(isinstance(part, str) and part for part in signature):
                    candidates_by_ref.setdefault(signature, set()).add(str(sid))
        for connection in meta.get("content_connections", ()):
            if not isinstance(connection, dict):
                continue
            source, target = connection.get("src"), connection.get("tgt")
            edge_type = connection.get("edge")
            if not isinstance(source, dict) or not isinstance(target, dict):
                continue
            source_signature = (source.get("type"), source.get("name"))
            target_signature = (target.get("type"), target.get("name"))
            if (all(isinstance(part, str) and part
                    for part in source_signature + target_signature)
                    and isinstance(edge_type, str) and edge_type):
                key = (source_signature, edge_type, target_signature)
                connection_providers.setdefault(key, set()).add(str(sid))

    allowed_groups = set(group_keys or ())
    scoped: dict[str, set[tuple[str, str]]] = {}
    unresolved = {
        "missing_graph_refs": [], "ambiguous_graph_refs": [],
        "invalid_graph_providers": [], "unprovided_graph_refs": [],
    }
    normalized = set()
    for row in graph_refs or ():
        if not isinstance(row, dict):
            unresolved["missing_graph_refs"].append({"ref": row})
            continue
        signature = (row.get("type"), row.get("name"))
        if not all(isinstance(part, str) and part for part in signature):
            unresolved["missing_graph_refs"].append({"ref": dict(row)})
            continue
        normalized.add(signature)

    contexts_by_ref: dict[tuple[str, str], list[set[str]]] = {}
    contextual_refs = set()
    for row in graph_ref_contexts or ():
        if not isinstance(row, dict) or not isinstance(row.get("ref"), dict):
            continue
        ref = row["ref"]
        signature = (ref.get("type"), ref.get("name"))
        if not all(isinstance(part, str) and part for part in signature):
            continue
        context = {str(key) for key in (row.get("group_keys") or ())
                   if isinstance(key, str) and key}
        if context:
            contexts_by_ref.setdefault(signature, []).append(context)
            contextual_refs.add(signature)

    provider_by_ref: dict[tuple[str, str], set[str]] = {}
    invalid_graph_providers = []
    for row in graph_provider_refs or ():
        if not isinstance(row, dict) or not isinstance(row.get("ref"), dict):
            invalid_graph_providers.append({"ref": row})
            continue
        ref = row["ref"]
        signature = (ref.get("type"), ref.get("name"))
        sid = row.get("seed_id")
        if (not all(isinstance(part, str) and part for part in signature)
                or not isinstance(sid, str) or not sid):
            invalid_graph_providers.append({"ref": dict(ref), "seed_id": sid})
            continue
        if (sid not in seeds
                or signature not in {
                    (item.get("type"), item.get("name"))
                    for item in seeds[sid].get("named_content_refs", ())
                    if isinstance(item, dict)
                }):
            invalid_graph_providers.append({"ref": dict(ref), "seed_id": sid})
            continue
        provider_by_ref.setdefault(signature, set()).add(sid)

    normalized_connections = set()
    for row in graph_connections or ():
        if not isinstance(row, dict):
            continue
        source, target = row.get("src"), row.get("tgt")
        edge_type = row.get("edge")
        if not isinstance(source, dict) or not isinstance(target, dict):
            continue
        source_signature = (source.get("type"), source.get("name"))
        target_signature = (target.get("type"), target.get("name"))
        if (all(isinstance(part, str) and part
                for part in source_signature + target_signature)
                and isinstance(edge_type, str) and edge_type
                and source_signature in normalized
                and target_signature in normalized):
            normalized_connections.add((source_signature, edge_type,
                                        target_signature))

    requests = []
    provider_contextual_refs = set(provider_by_ref)
    for signature in sorted(normalized - contextual_refs - provider_contextual_refs):
        requests.append((signature, set()))
    for signature, contexts in contexts_by_ref.items():
        if signature not in provider_contextual_refs:
            requests.extend((signature, context) for context in contexts)
    for signature, providers in provider_by_ref.items():
        requests.extend((signature, set(), sid) for sid in providers)

    for request in sorted(
            requests, key=lambda row: (row[0], sorted(row[1]),
                                       row[2] if len(row) > 2 else "")):
        (node_type, name), ref_group_keys = request[:2]
        signature = (node_type, name)
        exact_seed_id = request[2] if len(request) > 2 else None
        provider_set = ({exact_seed_id} if exact_seed_id else
                        set(candidates_by_ref.get(signature, ())))
        active_groups = allowed_groups | ref_group_keys
        if active_groups and exact_seed_id is None:
            provider_set &= {
                sid for sid in provider_set
                if set(seeds[sid].get("group_keys") or ()) & active_groups
            }
        connected_context = [
            set(connection_providers.get(connection, ()))
            for connection in normalized_connections
            if signature in (connection[0], connection[2])
        ]
        if connected_context and exact_seed_id is None:
            # A provider must declare every graph connection adjacent to this
            # resolved ref. Partial matches do not disambiguate a collision.
            provider_set &= set.intersection(*connected_context)
        providers = sorted(provider_set)
        if not providers:
            unresolved["unprovided_graph_refs"].append(
                {"type": node_type, "name": name})
        elif len(providers) > 1:
            unresolved["ambiguous_graph_refs"].append({
                "type": node_type, "name": name,
                "candidate_seed_ids": providers,
            })
        else:
            scoped.setdefault(providers[0], set()).add((node_type, name))

    unresolved["invalid_graph_providers"] = invalid_graph_providers
    return ({sid: [{"type": node_type, "name": name}
                   for node_type, name in sorted(refs)]
             for sid, refs in sorted(scoped.items())}, unresolved)


# ---------------------------------------------------------------------------
# MINIMAL SEED PROVENANCE — one compact SeedSummary node per loaded seed, so
# a later agent-authored decision (e.g. reflective_faculty._compose_experiment_
# rule's SeedDelta.skip_seeds pick) can query "which seed is THIS content from"
# without per-node from_seed edges (386 seeds; a summary node per seed is the
# cheap queryable form, not a Rule/Concept-fanout of provenance edges). Pure
# mechanical translation of what the manifest JSON already says (id, rule
# names, RelationCue keywords, concept names, description words) into one
# node's `keywords_text` — no decision, no agent reasoning.
#
# `skippable`: a CONSERVATIVE DENYLIST (not an allowlist — with 386 seeds, an
# allowlist enumerating every ablatable topic is impractical; a short denylist
# of foundational/self-referential/alignment-frozen seeds, documented here, is
# the cheaper and equally conservative form: every seed defaults skippable=True
# EXCEPT the ones this set names). Frozen for three reasons:
#   (1) boot_core.CORE_SEEDS — foundational cognition; ablating one answers
#       "does the agent still think at all", not "what does it lose", so it's
#       out of scope for a self-experiment about a specific capability.
#   (2) the self-experiment/composer machinery's OWN dependencies
#       (relation_vocabulary / composer_dispatch / shape_decode_loop /
#       self_design_axis / math_capability_shapes) — ablating one of these
#       would break the very faculty deciding to run the next experiment, a
#       bootstrapping hazard, not a legitimate capability ablation.
#   (3) `autonomy` — the understand Drive, frozen for alignment reasons
#       (CLAUDE.md).
# Everything else (the ~370 topic/world/vocabulary/knowledge seeds) is
# skippable=True: genuinely ablatable content the agent can test losing.
# ---------------------------------------------------------------------------
_FROZEN_SEED_IDS = frozenset({
    "decision_core", "learning_core", "perception_core", "epistemics_core",
    "motor_core", "experimentation_core", "goal_construction",
    "self_monitoring", "memory_core", "reflex_core", "theorem_core",
    "affective_state_core",
    "dual_process_core",
    "episodic_working_memory_core",
    "adaptive_control_core",
    "generative_world_model",
    "default_mode_core",
    "relation_vocabulary", "composer_dispatch", "shape_decode_loop",
    "self_design_axis", "math_capability_shapes",
    "self_repair", "clause_synthesis", "repair_escalation",
    "self_change_reasoning", "program_self_modification",
    "autonomy",
    # plan P5 (2026-10-10): the operator-authorship meta-evaluation, its
    # mutation grammar and its qualification rule are frozen -- the loop may
    # not vary how a new variation family is judged
    "operator_authorship",
    # (4) SELF-OPTIMISATION (Wave: 2026-07-10) — `intent` is the Message/Mention/
    # referent-resolution foundation EVERY conversation-replay experiment probe
    # depends on (comprehension_health.json, gap_awareness.json, and every
    # conversation_* seed all sit on top of it); ablating it in a 'vary' pick
    # would break replay itself rather than test losing a specific capability,
    # so it is out of scope for a self-experiment the same way boot_core's own
    # CORE_SEEDS are. The reading-family seed JSON files (breadth,
    # predictive_reading, reading_constructions/cortices/dwell/faculties/
    # hearing_neuroscience/review/skeleton, register_source,
    # semantic_reading_context — the deep-reader/shadow-read machinery
    # world_adapter._shadow_read_turn loads) are deliberately NOT added here —
    # they default skippable=True like every non-frozen seed, and ablating one
    # to test whether it is the source of a comprehension-latency/divergence
    # gap is exactly the meaningful experiment this wave's efficiency
    # objective wants available (the reading Python modules, e.g.
    # reading_collapse.py/reading_drive.py, are domain CODE, not seed JSON —
    # they have no SeedSummary and are not ablatable this way at all).
    "intent",
    # (5) IMPROVEMENT INTEGRITY (tranche 19) — the held list of node types
    # whose rules ARE the self-improvement loop (seeds/improvement_integrity
    # .json). The loop must not ablate or edit the list that protects it.
    "improvement_integrity",
    # (6) JUDGE V2 (plan P1, 2026-10-10) -- the adoption vetoes (regression,
    # overridden verdict, reply-quality drop). The loop must not ablate the
    # gate it is judged by; a human authored and froze it.
    "adoption_safety",
})

_SEED_SUMMARY_TYPE = "SeedSummary"


def _begin_boot_observation(agent, seed_count: int):
    """Expose one external boot event to the graph, without interpreting it.

    Seed loading is an I/O boundary: Python can report what the Rust loader
    returned, but whether an incomplete boot is a problem is the agent's
    decision.  The ``boot_metacognition`` seed makes that decision in graph
    rules.  Keeping only the cycle plus anomalous seed outcomes avoids adding
    hundreds of successful-load nodes on every boot.
    """
    try:
        cycle = agent.s.add_node("BootCycle", {
            "status": "loading",
            "seed_count": int(seed_count),
            "integrity": "unassessed",
        })
        agent.inner.add_edge_unchecked(agent.agent, "observed_boot", cycle)
        return cycle
    except Exception:
        return None


def _record_boot_anomaly(agent, cycle, seed_id: str, outcome: str, detail: str) -> None:
    """Mechanically translate one non-success loader result into graph data."""
    if cycle is None:
        return
    try:
        obs = agent.s.add_node("BootSeedAnomaly", {
            "seed_id": str(seed_id),
            "outcome": str(outcome),
            "detail": str(detail),
            "assessment": "unexamined",
        })
        agent.inner.add_edge_unchecked(cycle, "has_seed_anomaly", obs)
    except Exception:
        pass


def _complete_boot_observation(agent, cycle, rep: dict) -> None:
    """Close the external event with report facts; graph rules assess them."""
    if cycle is None:
        return
    try:
        agent.inner.set_attr(cycle, "loaded_count", int(rep.get("loaded", 0)))
        agent.inner.set_attr(cycle, "failed_count", len(rep.get("failed", ())))
        agent.inner.set_attr(cycle, "degraded_count", len(rep.get("rules_skipped", ())))
        agent.inner.set_attr(cycle, "status", "complete")
    except Exception:
        pass


def _seed_keywords_text(sid: str, d: dict, *, max_words: int = 120) -> str:
    """Mechanical extraction: words the seed's OWN manifest already declares
    (its id, its rules' names, any RelationCue keyword phrases it carries, its
    concepts' names, and the first ~40 words of its description) — no new
    vocabulary invented, just concatenated + lowercased for cheap StringIndexOf
    overlap scoring. Capped so a 386-seed sweep stays small (~120 words/seed)."""
    words: list = []
    words.extend(str(sid).replace("-", "_").split("_"))
    for r in (d.get("rules") or []):
        if isinstance(r, dict) and r.get("name"):
            words.extend(str(r["name"]).split("_"))
    for n in (d.get("nodes") or []):
        if not isinstance(n, dict):
            continue
        at = n.get("attrs") or {}
        if n.get("type") == "RelationCue":
            for kw in (at.get("keywords") or []):
                words.extend(str(kw).lower().split())
        elif n.get("type") == "Rule" and at.get("name"):
            words.extend(str(at["name"]).split("_"))
    for c in (d.get("concepts") or []):
        if isinstance(c, dict) and c.get("name"):
            words.extend(str(c["name"]).split("_"))
    desc = d.get("description") or ""
    words.extend(str(desc).lower().split()[:40])
    seen, out = set(), []
    for w in words:
        w = w.strip().lower().strip(".,:;()[]{}\"'")
        if w and w not in seen:
            seen.add(w)
            out.append(w)
        if len(out) >= max_words:
            break
    return " ".join(out)


def _mint_seed_summary(agent, sid: str, d: dict) -> None:
    """Idempotently mint one SeedSummary{seed_id, keywords_text, skippable}
    node for a loaded seed. Pure mechanical translation of the manifest's own
    declared content (see module docstring above) — no agent decision."""
    try:
        for n in agent.s.nodes(_SEED_SUMMARY_TYPE):
            if agent.s.node(n)["attrs"].get("seed_id") == sid:
                return   # already summarised (idempotent re-load)
    except Exception:
        pass
    try:
        agent.s.add_node(_SEED_SUMMARY_TYPE, {
            "seed_id": sid,
            "keywords_text": _seed_keywords_text(sid, d),
            "skippable": 0.0 if sid in _FROZEN_SEED_IDS else 1.0,
        })
    except Exception:
        pass


def _backfill_seed_capkeys(agent, sid: str, d: dict) -> int:
    """CAPKEY LOAD-TIME BACKFILL (the self-extension spec's named seam,
    docs/jabberwock_self_extension_spec.md 'open seams': *"seeded axes/
    primitives need a backfill rule to mint requires_key/provides_key from
    their existing capability_keys list-attrs on boot, so this works without
    rewriting every seed by hand"*). A seed manifest declaring a top-level
    ``capability_keys`` list advertises what the loaded seed PROVIDES: mint one
    interned ``CapKey{name}`` per token (get-or-create by name — the same dedup
    move ``WorldAdapter.wire_self_extension`` uses for live node attrs) and
    wire ``SeedSummary -provides_key-> CapKey`` (the SeedSummary is the seed's
    graph-resident provenance node, already minted per load). The
    ``compose_from_held_primitives`` join (seeds/self_extension.json:
    ``axis -requires_key-> k <-provides_key- p``) then sees keys from OUTSIDE
    self_extension.json's own hand-wired fixtures. Idempotent (key-interned,
    edge-once); pure mechanical translation of what the manifest declares —
    no agent decision. Returns the number of provides_key edges added."""
    keys = [str(k) for k in (d.get("capability_keys") or []) if k]
    if not keys:
        return 0
    summary = None
    try:
        for n in agent.s.nodes(_SEED_SUMMARY_TYPE):
            if agent.s.node(n)["attrs"].get("seed_id") == sid:
                summary = n
                break
    except Exception:
        return 0
    if summary is None:
        return 0
    keymap = {}
    try:
        for ck in agent.s.nodes("CapKey"):
            nm = agent.s.node(ck)["attrs"].get("name")
            if nm:
                keymap.setdefault(nm, ck)
    except Exception:
        return 0
    added = 0
    for k in keys:
        ck = keymap.get(k)
        if ck is None:
            try:
                ck = agent.s.add_node("CapKey", {"name": k})
            except Exception:
                continue
            keymap[k] = ck
        try:
            if ck not in agent.inner.neighbours(summary, "provides_key"):
                agent.inner.add_edge_unchecked(summary, "provides_key", ck)
                added += 1
        except Exception:
            continue
    # a never-measured seed-provider defaults to the same flat 0.5 prior
    # wire_self_extension gives never-measured primitives (spec section 0).
    try:
        if added and "reliability" not in agent.s.node(summary)["attrs"]:
            agent.inner.set_attr(summary, "reliability", 0.5)
    except Exception:
        pass
    return added


def _enforce_skip_not_frozen(skip: set) -> tuple:
    """CONSUMER-SIDE enforcement (closes known_gaps['seed_skip_unvalidated_at_
    consumption']): refuse to skip any seed in ``domains.frozen_core.
    frozen_seed_ids_closed()`` (``_FROZEN_SEED_IDS`` plus the transitive
    ``depends_on`` closure of every id in it), NO MATTER WHO ASKED. Before this,
    ``skip`` was applied verbatim -- the only reason a dispatched child never
    skipped a frozen seed was that the one producer wired to the agent's own
    composer (``_compose_experiment_rule``'s 'vary' branch) happened to filter
    its pick to skippable seeds; a different producer of the same SeedDelta
    shape (e.g. ``domains.experiment_dispatch.mint_experiment``, documented as
    a test/authoring helper, or a hand-built delta) could ask for anything,
    including ``'autonomy'`` itself. This is THE choke point every skip
    request flows through (``scripts/arc_child_run.py:boot_child_agent`` calls
    straight into this function; no other code path ever consumes
    ``skip_seeds``/``skip=``) -- so enforcing here makes the guarantee
    consumer-ENFORCED, not producer-hoped.

    FAILS SAFE: if the frozen set can't be computed at all (import error,
    graph error, anything), this refuses EVERY requested skip rather than let
    an un-checked skip through -- a computation failure is treated the same as
    "everything is frozen", never as "nothing is frozen".

    Returns ``(allowed_skip: set, refused: list[str])``. Loudly logs (``[seed]``
    tag, matching ``runners/dsl/src/py.rs``'s own seed-loader diagnostic
    convention) every refusal, naming the seed.
    """
    if not skip:
        return skip, []
    try:
        from domains.frozen_core import frozen_seed_ids_closed
        frozen = frozen_seed_ids_closed()
    except Exception as e:  # noqa: BLE001 -- FAIL SAFE: refuse everything, never silently allow
        refused = []
        for sid in sorted(skip):
            print(f"[seed] REFUSED skip of {sid!r}: could not compute the frozen-core set "
                  f"({type(e).__name__}: {e}) -- failing safe, refusing ALL skip requests this "
                  f"boot rather than risk skipping a frozen seed unchecked")
            refused.append(sid)
        return set(), refused
    blocked = skip & frozen
    refused = []
    for sid in sorted(blocked):
        print(f"[seed] REFUSED skip of frozen seed {sid!r} (frozen directly, or by dependency "
              f"closure of a frozen seed -- see seeds/frozen_core_manifest.json) -- this seed is "
              f"part of the agent's non-negotiable frozen core and cannot be withheld by any "
              f"skip request, enforced at substrate.boot_all.load_all_seeds")
        refused.append(sid)
    return skip - blocked, refused


def load_all_seeds(agent, seed_dir=None, skip=(), *, seed_ids=None,
                   group_keys=None, content_keys=None,
                   content_candidates=None,
                   scoped_content_refs=None,
                   _preloaded_seed_ids=(), _profile_token=None,
                   _seed_index_snapshot=None,
                   track_content_node_provenance=False) -> dict:
    """Load seeds in dependency order, optionally from a connected selection.

    ``skip`` lists seed ids already installed (e.g. the CORE_SEEDS a bare boot
    loaded). Returns a report: ``{total, loaded, concepts, failed, order}``.
    Failures are recorded per seed, never aborting the boot.

    With no selection arguments, this preserves the full-corpus boot. If any
    of ``seed_ids``, ``group_keys``, ``content_keys``, ``content_candidates`` or
    ``scoped_content_refs`` is supplied, the cached pre-pass resolves those
    anchors and their declared/content dependency closure. Scoped references
    select exact typed names only within the explicitly named seed, preventing
    lexical keys from selecting unrelated same-named providers. An incomplete
    closure is rejected before boot graph mutation.

    ``track_content_node_provenance`` is an opt-in evaluation/readback aid. It
    retains native local-to-global node identities for declared content in the
    returned report; normal boots pay no per-node report cost.

    Any id in ``skip`` that names a frozen-core seed (directly, or by
    dependency closure -- see ``domains.frozen_core.frozen_seed_ids_closed``)
    is REFUSED regardless of who requested it (``rep["refused_skips"]``) --
    this is the sole consumption choke point for ``skip_seeds``/``skip=``, so
    enforcing here protects every caller (a direct call, or a dispatched
    child booted via ``scripts/arc_child_run.py:boot_child_agent``).
    The private ``_preloaded_seed_ids`` path is reserved for incremental
    conversation-profile content loading. Each id must have a graph-resident
    successful ``SeedSummary``; this is distinct from and does not weaken the
    consumer-validated user ``skip`` path. Selective providers may be reopened
    only to load newly requested named content.
    """
    seed_dir = str(seed_dir or SEED_DIR)
    skip, refused_skips = _enforce_skip_not_frozen(set(skip))
    preloaded_seed_ids = set(map(str, _preloaded_seed_ids or ()))
    if preloaded_seed_ids:
        if _profile_token is not _CONVERSATION_INCREMENTAL_LOAD_TOKEN:
            raise ValueError("preloaded seed reuse is reserved for the conversation profile")
        observed_summaries = {
            str(agent.s.node(node)["attrs"].get("seed_id"))
            for node in agent.s.nodes(_SEED_SUMMARY_TYPE)
            if agent.s.node(node)["attrs"].get("seed_id")
        }
        unverified = preloaded_seed_ids - observed_summaries
        if unverified:
            raise ValueError(
                "cannot reuse unverified preloaded seeds: "
                f"{sorted(unverified)}")
    if _seed_index_snapshot is not None:
        if _profile_token is not _CONVERSATION_INCREMENTAL_LOAD_TOKEN:
            raise ValueError("cached seed index reuse is reserved for the conversation profile")
        seed_index, seed_paths, snapshot_digest = _seed_index_snapshot
        if _SEED_INDEX_SOURCE_DIGEST.get(os.path.realpath(seed_dir)) != snapshot_digest:
            raise ValueError("conversation seed index snapshot is stale")
    else:
        seed_index, seed_paths = _read_seed_index(seed_dir)
    seed_inventory = _SEED_MICROTHEORY_INVENTORY.get(
        os.path.realpath(seed_dir), {})
    # `_read_seed_index` has already source-validated this companion map.
    # Reuse it for the boot-time self-model mirror rather than validating and
    # hashing the complete manifest corpus a second time later in this boot.
    validated_seed_rule_index = _SEED_RULE_NAME_INDEX.get(
        os.path.realpath(seed_dir), {})
    scoped_content_refs = (
        {str(sid): [dict(ref) for ref in refs or ()]
         for sid, refs in scoped_content_refs.items()}
        if scoped_content_refs is not None else None
    )
    candidate_resolution = None
    candidate_scoped_content_seeds = set()
    if content_candidates is not None:
        candidate_resolution = resolve_seed_content_candidates(
            seed_index, content_candidates, seed_dir=seed_dir)
        scoped_content_refs = scoped_content_refs or {}
        for sid, refs in candidate_resolution.get(
                "scoped_content_refs_by_seed", {}).items():
            candidate_scoped_content_seeds.add(str(sid))
            existing = {
                (ref.get("type"), ref.get("name"))
                for ref in scoped_content_refs.setdefault(sid, [])
                if isinstance(ref, dict)
            }
            for ref in refs:
                signature = (ref["type"], ref["name"])
                if signature not in existing:
                    scoped_content_refs[sid].append(dict(ref))
                    existing.add(signature)
    selection_requested = (
        seed_ids is not None or group_keys is not None or content_keys is not None
        or content_candidates is not None or scoped_content_refs is not None
    )
    selection = None
    if selection_requested:
        order, unresolved = _select_seed_ids(
            seed_index,
            seed_ids=() if seed_ids is None else seed_ids,
            group_keys=() if group_keys is None else group_keys,
            content_keys=() if content_keys is None else content_keys,
            scoped_content_refs=scoped_content_refs,
            selection_index=_seed_selection_index(seed_index, seed_dir),
        )
        candidate_scoped_content_seeds.update(
            str(sid) for sid in (scoped_content_refs or {}))
        selection = {
            "seed_ids": sorted(set(seed_ids or ())),
            "group_keys": sorted(set(group_keys or ())),
            "content_keys": sorted(set(content_keys or ())),
            "scoped_content_refs": {
                str(sid): [dict(ref) for ref in refs or ()]
                for sid, refs in sorted((scoped_content_refs or {}).items())
            },
            "selected_seed_ids": list(order),
            "unresolved": unresolved,
        }
        if candidate_resolution is not None:
            selection["content_candidate_resolution"] = candidate_resolution
        complete = not any(unresolved.values())
        corpus_total = len(seed_index)
        provider_content_keys = {
            sid: set(seed_index[sid].get("content_keys") or ())
            for sid in order
        }
        rep = {
            "total": len(order),
            "corpus_total": corpus_total,
            "loaded": 0,
            "concepts": 0,
            "microtheories": 0,
            "failed": [],
            "rules_skipped": [],
            "order": order,
            "refused_skips": refused_skips,
            "preloaded_seed_ids": sorted(preloaded_seed_ids),
            "selective_seed_ids": sorted(
                sid for sid in order
                if seed_index[sid].get("selective_content_keys")),
            "selection": selection,
            "selection_complete": complete,
        }
        if not complete:
            rep["status"] = "selection_incomplete"
            return rep
        # Selection needs the full connectivity graph only until its closure is
        # resolved. Retain paths for the chosen seeds only, then release the
        # 734-entry content/reference map before native installation and event
        # processing; otherwise profile boots pay to keep the planning graph
        # resident for the lifetime of this whole loader call.
        selected_paths = {sid: seed_paths[sid] for sid in order}
        del seed_index, seed_paths
        seed_paths = selected_paths
    else:
        order = _topo_order(seed_index)
        provider_content_keys = {}
        rep = {"total": len(seed_index), "loaded": 0, "concepts": 0, "microtheories": 0,
               "failed": [], "rules_skipped": [], "order": order, "refused_skips": refused_skips}
        del seed_index
    if track_content_node_provenance:
        rep["content_node_provenance"] = {}
    pending_seed_count = sum(
        sid not in skip and sid not in preloaded_seed_ids for sid in order)
    boot_cycle = _begin_boot_observation(agent, pending_seed_count)
    requested_content_keys = {str(key) for key in (content_keys or ())}
    requested_scoped_content_refs = {
        str(sid): {(str(ref.get("type")), str(ref.get("name")))
                   for ref in refs or () if isinstance(ref, dict)}
        for sid, refs in (scoped_content_refs or {}).items()
    }
    # Names of Microtheory nodes already present (from {nodes:[...]}-format
    # seeds), so the singular-{microtheory:{...}} header materialisation below
    # never duplicates an existing Mt.
    seen_mts = set()
    mt_id_by_name: dict = {}
    node_id_by_name: dict = {}          # name -> node id (any type) for relation resolution
    pending_genlmt: list = []          # (child_mt_id, parent_name) resolved after the loop
    pending_relations: list = []       # (sid, src_name, edge_type, tgt_name) name-based edges
    self_model_sources_changed = False
    try:
        for n in agent.s.nodes("Microtheory"):
            nm = agent.s.node(n)["attrs"].get("name")
            if nm:
                seen_mts.add(nm)
                mt_id_by_name.setdefault(nm, n)
                node_id_by_name.setdefault(nm, n)
    except Exception:
        pass
    # Productions so the encyclopedic {microtheory,concepts,rules,parent} format
    # can be FULLY materialised (Mt -has_concept-> Concept, Mt -has_rule-> Rule,
    # Mt -genlMt-> parent Mt) — the wiring the install_*_seed builders add. The
    # native loader admits has_concept but not has_rule / genlMt; declare them so
    # the generic boot reproduces the builders (and the builders can be burned).
    for _et, _tgt in (("has_concept", "Concept"), ("has_rule", "Rule"),
                      ("genlMt", "Microtheory")):
        try:
            agent.s.add_production({"src": {"type": "Microtheory", "var": "s"},
                                    "edge_type": _et, "tgt": {"type": _tgt, "var": "t"},
                                    "where": None, "weight": {"type": "Lit", "value": 1.0},
                                    "provenance": "boot_all"})
        except Exception:
            pass

    for sid in order:
        if sid in skip or sid in preloaded_seed_ids:
            continue
        try:
            with open(seed_paths[sid], encoding="utf-8") as stream:
                d = json.load(stream)
            if not isinstance(d, dict) or d.get("self_load_only"):
                continue
            scoped_refs = requested_scoped_content_refs.get(sid)
            if (d.pop("selective_content_keys", False)
                    and (requested_content_keys or scoped_refs)):
                original_nodes = d.get("nodes") or []
                original_concepts = d.get("concepts") or []
                selected_nodes = []
                selected_concepts = []
                for node in original_nodes:
                    if not isinstance(node, dict):
                        continue
                    node_type = str(node.get("type") or "")
                    name = str((node.get("attrs") or {}).get("name") or "")
                    if ((node_type, name) in scoped_refs if scoped_refs is not None
                            else name in requested_content_keys):
                        selected_nodes.append(node)
                for concept in original_concepts:
                    if not isinstance(concept, dict):
                        continue
                    name = str(concept.get("name") or "")
                    if (("Concept", name) in scoped_refs
                            if scoped_refs is not None
                            else name in requested_content_keys):
                        selected_concepts.append(concept)
                content_local_ids = {
                    str(node["local_id"])
                    for node in selected_nodes
                    if node.get("local_id") is not None
                }
                local_nodes = {
                    str(node["local_id"]): node
                    for node in original_nodes
                    if isinstance(node, dict) and node.get("local_id") is not None
                }
                # Route-tagged Concepts are executable vocabulary consumed by
                # instruction routing, not optional lexical content. Keep
                # them in a selective slice so the first live turn does not
                # need to reopen the seed manifest to repair its route table.
                route_local_ids = {
                    str(node["local_id"])
                    for node in original_nodes
                    if isinstance(node, dict)
                    and node.get("type") == "Concept"
                    and (node.get("attrs") or {}).get("instruction_route")
                    and node.get("local_id") is not None
                }
                selected_node_ids = {
                    str(node.get("local_id")) for node in selected_nodes
                    if isinstance(node, dict) and node.get("local_id") is not None
                }
                selected_nodes.extend(
                    node for node in original_nodes
                    if isinstance(node, dict)
                    and str(node.get("local_id")) in route_local_ids
                    and str(node.get("local_id")) not in selected_node_ids
                )
                # Retain Microtheory scaffolding that owns selected concepts,
                # plus its declared parent chain. These nodes carry grouping
                # and inherited-rule context, not unrelated content; omitting
                # them changes native rule behavior even if edge refs are
                # simply discarded.
                scaffold_local_ids = set()
                for edge in d.get("edges") or ():
                    if (not isinstance(edge, dict)
                            or edge.get("type") != "has_concept"):
                        continue
                    src, tgt = edge.get("src"), edge.get("tgt")
                    if (isinstance(src, dict) and isinstance(tgt, dict)
                            and str(tgt.get("local")) in content_local_ids
                            and src.get("local") is not None):
                        parent_id = str(src["local"])
                        parent_node = local_nodes.get(parent_id)
                        if (parent_node is not None
                                and parent_node.get("type") == "Microtheory"):
                            scaffold_local_ids.add(parent_id)
                pending_scaffolds = list(scaffold_local_ids)
                while pending_scaffolds:
                    parent_id = pending_scaffolds.pop()
                    for edge in d.get("edges") or ():
                        if (not isinstance(edge, dict)
                                or edge.get("type") != "genlMt"):
                            continue
                        src, tgt = edge.get("src"), edge.get("tgt")
                        if (isinstance(src, dict) and isinstance(tgt, dict)
                                and str(src.get("local")) == parent_id
                                and tgt.get("local") is not None):
                            ancestor_id = str(tgt["local"])
                            ancestor = local_nodes.get(ancestor_id)
                            if (ancestor is not None
                                    and ancestor.get("type") == "Microtheory"
                                    and ancestor_id not in scaffold_local_ids):
                                scaffold_local_ids.add(ancestor_id)
                                pending_scaffolds.append(ancestor_id)
                selected_nodes.extend(
                    local_nodes[local_id] for local_id in sorted(scaffold_local_ids)
                    if local_id in local_nodes
                )
                retained_local_ids = (content_local_ids | scaffold_local_ids
                                      | route_local_ids)
                if "nodes" in d or original_nodes:
                    d["nodes"] = selected_nodes
                # A native manifest's local edge references are scoped to its
                # node table. Once that table is content-sliced, retaining an
                # edge to an omitted local node makes the native loader fail
                # after partially installing the selected nodes; the fallback
                # retry then duplicates those nodes. Keep only edges whose
                # local endpoints survived the slice (external role refs such
                # as ``agent_root`` remain valid).
                if "edges" in d:
                    def _edge_survives_content_slice(edge):
                        if not isinstance(edge, dict):
                            return True
                        for endpoint in (edge.get("src"), edge.get("tgt")):
                            if (isinstance(endpoint, dict)
                                    and endpoint.get("local") is not None
                                    and str(endpoint["local"])
                                    not in retained_local_ids):
                                return False
                        return True

                    original_edges = d.get("edges") or []
                    d["edges"] = [
                        edge for edge in original_edges
                        if _edge_survives_content_slice(edge)
                    ]
                    slice_report = {
                        "dropped_edge_count": len(original_edges) - len(d["edges"]),
                    }
                else:
                    slice_report = {}
                if "concepts" in d or original_concepts:
                    d["concepts"] = selected_concepts
                slice_report.update({
                    "matched_node_count": len(content_local_ids),
                    "source_node_count": len(original_nodes),
                })
                if scaffold_local_ids:
                    slice_report["retained_scaffold_node_count"] = len(
                        scaffold_local_ids)
                if "concepts" in d or original_concepts:
                    slice_report["matched_concept_count"] = len(
                        selected_concepts)
                    slice_report["source_concept_count"] = len(
                        original_concepts)
                if scoped_refs is not None:
                    slice_report["requested_refs"] = [
                        {"type": node_type, "name": name}
                        for node_type, name in sorted(scoped_refs)
                    ]
                else:
                    slice_report["requested_keys"] = sorted(
                        requested_content_keys)
                rep.setdefault("content_slices", {})[sid] = slice_report
        except Exception as e:
            rep["failed"].append(f"{sid}:{type(e).__name__}:{e}")
            _record_boot_anomaly(
                agent, boot_cycle, sid, "failed",
                f"{type(e).__name__}: {e}",
            )
            continue
        d_engine = engine_rules_only(d)
        primary_error = None
        load_summary = {}
        try:
            load_summary = agent.inner.load_seed_manifest(d_engine, agent.agent)
        except Exception as e1:
            primary_error = f"{type(e1).__name__}: {e1}"
            # Fall back without rules if the manifest still has incompatible schema.
            d2 = {k: v for k, v in d_engine.items() if k != "rules"}
            try:
                load_summary = agent.inner.load_seed_manifest(d2, agent.agent)
                rep["rules_skipped"].append(sid)
                _record_boot_anomaly(agent, boot_cycle, sid, "rules_skipped", primary_error)
            except Exception as e2:  # record, never abort the boot
                rep["failed"].append(f"{sid}:{type(e2).__name__}:{e2}")
                _record_boot_anomaly(
                    agent, boot_cycle, sid, "failed",
                    f"{type(e2).__name__}: {e2}",
                )
                continue
        if (int(load_summary.get("rules", 0) or 0) > 0
                or any(isinstance(node, dict)
                       and node.get("type") in {"Rule", "Program"}
                       for node in (d_engine.get("nodes") or ()))
                or bool(d.get("rules"))
                or any(isinstance(node, dict)
                       and node.get("type") in {"Rule", "Program"}
                       for node in (d.get("extra_nodes") or ()))):
            self_model_sources_changed = True
        if track_content_node_provenance:
            local_node_ids = load_summary.get("local_node_ids") or {}
            for node in d.get("nodes") or ():
                if not isinstance(node, dict):
                    continue
                attrs = node.get("attrs") or {}
                local_id = node.get("local_id")
                global_id = local_node_ids.get(local_id)
                if (global_id is None and local_id is not None
                        and isinstance(local_node_ids, dict)):
                    global_id = local_node_ids.get(str(local_id))
                if (global_id is not None and node.get("type")
                        and isinstance(attrs, dict) and attrs.get("name")):
                    rep["content_node_provenance"][int(global_id)] = {
                        "seed_id": str(sid),
                        "type": str(node["type"]),
                        "name": str(attrs["name"]),
                    }
        # Materialise a singular {microtheory: {...}} header as a Microtheory
        # node carrying ALL its scalar attrs. The native load_seed_manifest only
        # handles nodes/edges, so without this the Mt header is silently dropped
        # for every {microtheory,concepts,rules}-format seed (~208 of them) —
        # including the identity seed's substrate_name / is_substrate_identity.
        # Created BEFORE concepts/rules so they can be wired to it (this is the
        # full migration of the install_*_seed builders into the generic loader).
        # Identify the Microtheory this seed defines across the THREE encyclopedic
        # schema variants the builders use:
        #   {microtheory: {...}}        - singular dict header
        #   {microtheory: "name"}       - bare string name
        #   {id, concepts, rules, ...}  - id IS the Mt name (no microtheory key)
        # Native {nodes/edges} seeds define no Mt here (load_seed_manifest did).
        mt = d.get("microtheory")
        mt_name, mt_attrs = None, {}
        mt_parent = d.get("parent_mt") or d.get("parent")
        if isinstance(mt, dict) and mt.get("name"):
            mt_name = mt["name"]
            mt_attrs = {k: v for k, v in mt.items() if isinstance(v, (str, int, float, bool))}
            mt_parent = mt.get("parent") or mt_parent
        elif isinstance(mt, str) and mt:
            mt_name = mt
        elif mt is None and "nodes" not in d and d.get("id") and \
                (d.get("concepts") or d.get("rules")):
            mt_name = d["id"]
            mt_attrs = {"name": d["id"], "version": d.get("version", ""),
                        "description": d.get("description", ""), "origin": d["id"]}

        mt_id = None
        if mt_name:
            mt_id = mt_id_by_name.get(mt_name)
            if mt_id is None and mt_name not in seen_mts:
                try:
                    mt_attrs.setdefault("name", mt_name)
                    for _bk, _bv in list(mt_attrs.items()):
                        if _bv is True:
                            mt_attrs[_bk] = 1.0
                        elif _bv is False:
                            mt_attrs[_bk] = 0.0
                    mt_id = agent.s.add_node("Microtheory", mt_attrs)
                    mt_id_by_name[mt_name] = mt_id
                    node_id_by_name.setdefault(mt_name, mt_id)
                    seen_mts.add(mt_name)
                    rep["microtheories"] += 1
                    if mt_parent:
                        pending_genlmt.append((mt_id, mt_parent))
                except Exception as e:
                    rep["failed"].append(f"{sid}:microtheory:{type(e).__name__}")

        for c in (d.get("concepts") or []):
            if not isinstance(c, dict):
                continue
            nm = c.get("name")
            if not nm:
                continue
            defn = c.get("definition")
            try:
                if isinstance(defn, dict):
                    agent.register_concept(nm, defn)
                    rep["concepts"] += 1
                # a Concept node so the agent KNOWS this concept (recall / Holds);
                # carry the concept's metadata (why/category/term/origin) too.
                cattrs = {"name": nm, "definition": defn if isinstance(defn, str) else "",
                          "domain": c.get("domain", "")}
                for k in ("why", "category", "term", "origin", "kind",
                          "semantic_role"):
                    if isinstance(c.get(k), (str, int, float, bool)):
                        cattrs[k] = c[k]
                cid = agent.s.add_node("Concept", cattrs)
                if track_content_node_provenance:
                    rep["content_node_provenance"][int(cid.value)] = {
                        "seed_id": str(sid), "type": "Concept",
                        "name": str(nm),
                    }
                node_id_by_name.setdefault(nm, cid)
                if mt_id is not None:           # wire Mt -has_concept-> Concept
                    try:
                        agent.s.add_edge(mt_id, "has_concept", cid, None)
                    except Exception:
                        pass
            except Exception as e:
                rep["failed"].append(f"{sid}:concept:{nm}:{type(e).__name__}")

        # Materialise the encyclopedic prose rules as Rule nodes wired
        # Mt -has_rule-> Rule (what the install_*_seed builders do), carrying
        # whatever clause keys the schema uses (head/body or if/then). Only when
        # this seed defines an Mt here, so native executable rules (handled by
        # load_seed_manifest) are NOT double-processed.
        if mt_id is not None:
            for r in (d.get("rules") or []):
                if not isinstance(r, dict) or not r.get("name"):
                    continue
                try:
                    rattrs = {"name": r["name"]}
                    for k, v in r.items():
                        if k != "name" and isinstance(v, (str, int, float, bool, list)):
                            rattrs[k] = v
                    rid = agent.s.add_node("Rule", rattrs)
                    node_id_by_name.setdefault(r["name"], rid)
                    try:
                        agent.s.add_edge(mt_id, "has_rule", rid, None)
                    except Exception:
                        pass
                    rep["rules_materialised"] = rep.get("rules_materialised", 0) + 1
                except Exception as e:
                    rep["failed"].append(f"{sid}:rule:{r.get('name')}:{type(e).__name__}")

        # extra_nodes: arbitrary typed nodes a captured builder added beyond the
        # Mt/concepts/rules (e.g. SourceEvent). {type, name, ...attrs}.
        for en in (d.get("extra_nodes") or []):
            if not isinstance(en, dict) or not en.get("type") or not en.get("name"):
                continue
            try:
                if en["name"] in node_id_by_name:
                    continue                   # already present (shared node)
                eattrs = {k: v for k, v in en.items()
                          if k != "type" and isinstance(v, (str, int, float, bool, list))}
                eid = agent.s.add_node(en["type"], eattrs)
                if track_content_node_provenance:
                    rep["content_node_provenance"][int(eid.value)] = {
                        "seed_id": str(sid), "type": str(en["type"]),
                        "name": str(en["name"]),
                    }
                node_id_by_name.setdefault(en["name"], eid)
                rep["extra_nodes"] = rep.get("extra_nodes", 0) + 1
            except Exception as e:
                rep["failed"].append(f"{sid}:extra_node:{en.get('name')}:{type(e).__name__}")

        # relations: name-based edges a captured builder computed (built_from,
        # depends_on, genlMt to another seed's node, ...). Resolved after the
        # loop so forward/cross-seed endpoints exist. {src, edge, tgt}.
        for rel in (d.get("relations") or []):
            if isinstance(rel, dict) and rel.get("src") and rel.get("edge") and rel.get("tgt"):
                pending_relations.append((sid, rel["src"], rel["edge"], rel["tgt"]))

        _mint_seed_summary(agent, sid, d)
        capkeys_added = _backfill_seed_capkeys(agent, sid, d)
        if capkeys_added:
            rep["capkeys"] = rep.get("capkeys", 0) + capkeys_added

        rep["loaded"] += 1
        rep.setdefault("loaded_seed_ids", []).append(str(sid))
        if sid in rep.get("content_slices", {}):
            actual_keys = {
                str((node.get("attrs") or {}).get("name"))
                for node in (d.get("nodes") or ())
                if isinstance(node, dict)
                and (node.get("attrs") or {}).get("name")
            }
            actual_keys.update(
                str(concept["name"])
                for concept in (d.get("concepts") or ())
                if isinstance(concept, dict) and concept.get("name")
            )
        else:
            actual_keys = provider_content_keys.get(sid, set())
        rep.setdefault("loaded_content_keys_by_seed", {})[str(sid)] = sorted(
            actual_keys)

    # Resolve parent links (Mt -genlMt-> parent Mt) now that every Mt exists.
    for child_id, parent_name in pending_genlmt:
        pid = mt_id_by_name.get(parent_name)
        if pid is not None:
            try:
                agent.s.add_edge(child_id, "genlMt", pid, None)
            except Exception:
                pass

    # Wire the agent into its substrate-identity Microtheory so graph self-reply
    # rules (conversation_self_reply.json) can read substrate_name.
    for mt_id in mt_id_by_name.values():
        try:
            attrs = agent.s.node(mt_id)["attrs"]
            if not attrs.get("is_substrate_identity"):
                continue
            agent.inner.add_edge_unchecked(agent.agent, "operates_in", mt_id)
            sn = attrs.get("substrate_name")
            if sn:
                agent.inner.set_attr(agent.agent, "substrate_name", str(sn))
        except Exception:  # noqa: BLE001
            pass

    # Resolve name-based relations (captured builder structure: built_from,
    # depends_on, ...). Install a production for each (src_type,edge,tgt_type)
    # so the edge is admissible, then add it by resolved name.
    declared = set()
    def _type_of(nid):
        try:
            return agent.s.node(nid).get("type") or agent.s.node(nid)["attrs"].get("__type__")
        except Exception:
            return None
    for sid, src_name, edge_type, tgt_name in pending_relations:
        sidn = node_id_by_name.get(src_name)
        tidn = node_id_by_name.get(tgt_name)
        if sidn is None or tidn is None:
            rep["relations_unresolved"] = rep.get("relations_unresolved", 0) + 1
            continue
        st, tt = _type_of(sidn), _type_of(tidn)
        key = (st, edge_type, tt)
        if key not in declared and st and tt:
            try:
                agent.s.add_production({"src": {"type": st, "var": "s"},
                                        "edge_type": edge_type, "tgt": {"type": tt, "var": "t"},
                                        "where": None, "weight": {"type": "Lit", "value": 1.0},
                                        "provenance": "boot_all:relation"})
            except Exception:
                pass
            declared.add(key)
        try:
            agent.s.add_edge(sidn, edge_type, tidn, None)
            rep["relations"] = rep.get("relations", 0) + 1
        except Exception:
            rep["relations_unresolved"] = rep.get("relations_unresolved", 0) + 1

    # FULL SELF-MODEL MIRROR — every rule the agent now holds (not just the
    # chosen_action-writing subset the acting-variant composer mirrors) as a
    # queryable RuleSummary, so a booted agent can always answer "what does
    # rule X do?" / "which rules ... about Y?" / "which parts of me touch Z?"
    # (see domains/self_model.py). Mechanical, idempotent; never a decision.
    if self_model_sources_changed:
        try:
            from domains import self_model as _sm
            rep["self_model"] = _sm.ensure_self_model(
                agent, validated_seed_rule_index=validated_seed_rule_index)
        except Exception as e:
            rep["self_model_failed"] = f"{type(e).__name__}: {e}"
    else:
        # The mirror is a view of Rule/Program sources. Concept-only content
        # loading cannot change it, so avoid a whole rule export and graph
        # scan on every incremental lexical prepass.
        rep["self_model_refresh_skipped"] = "no_new_rule_or_program_sources"

    # Optional self-account readers are connected to the selected seed closure.
    # Full boot retains the historical complete registration. A bounded profile
    # must not import unrelated curriculum/readback faculties: doing so defeats
    # the dependency pre-pass and can pull large corpus stacks (e.g. Parquet
    # readers) into a conversation-only process. Register each reader only when
    # its supporting seeds are present in the resolved closure.
    selected_ids = set(order)
    code_capability_seeds = {
        "code_authoring_targets", "code_write_constructions",
        "code_write_gap", "code_write_request_cues", "program_synthesis",
        "programming_languages", "programs", "program_properties",
    }
    if not selection_requested or selected_ids.intersection(code_capability_seeds):
        try:
            from domains import code_curriculum as _cc
            _cc.ensure_code_capabilities_dispatch()
        except Exception as e:
            rep["code_curriculum_dispatch_failed"] = f"{type(e).__name__}: {e}"

    if not selection_requested or "curriculum_study" in selected_ids:
        try:
            from domains import curriculum_study as _csw
            _csw.ensure_roadmap_dispatch()
        except Exception as e:
            rep["curriculum_study_dispatch_failed"] = f"{type(e).__name__}: {e}"

    # LEXICAL QUALIA INDEX — every held word links to one or more qualia. The
    # Quale nodes and their has_quale DAG load as native seed data
    # (seeds/lexical_qualia.json); this mechanical, idempotent pass installs the
    # persisted word -> sense links onto held Concepts via the Concept.name
    # index (domains/lexical_qualia.py). No decision: the table is the seed's.
    try:
        from domains import lexical_qualia as _lq
        rep["lexical_qualia"] = _lq.install_word_links(agent)
    except Exception as e:
        rep["lexical_qualia_failed"] = f"{type(e).__name__}: {e}"
    # GROUNDING-REACHABILITY SUBSTRATE — mint `grounded_in` edges from the
    # grounding signals that already exist (perception ingestion, a real
    # teacher_hook exchange, a judged Experiment outcome, a live vision-world
    # binding) onto the anchor vocabulary the `grounding_anchors` seed names.
    # Mechanical + idempotent, same shape as the self-model mirror above; see
    # domains/grounding_reach.py's module docstring for the full signal map.
    try:
        from domains import grounding_reach as _gr
        rep["grounding_reach"] = _gr.ensure_grounding_edges(agent)
    except Exception as e:
        rep["grounding_reach_failed"] = f"{type(e).__name__}: {e}"
    # Materialize the bounded inventory projection computed by the validated
    # seed pre-pass on the graph's existing Agent root. This is graph data, not
    # a Python-side answer cache: the self-organisation reader consumes it to
    # report the same static inventory without loading every area's content
    # or adding another graph node type to the bounded profile.
    try:
        inventory = seed_inventory
        inventory_attrs = {
            "microtheory_inventory_schema": "seed_microtheory_inventory.v1",
            "microtheory_inventory_source_digest": str(
                inventory.get("source_digest") or ""),
            "microtheory_inventory_areas_json": json.dumps(
                (inventory.get("areas") or ())[:12], separators=(",", ":")),
            "microtheory_inventory_area_count": len(
                inventory.get("areas") or []),
        }
        for key, value in inventory_attrs.items():
            agent.inner.set_attr(agent.agent, key, value)
        rep["self_organisation_inventory"] = {
            "area_count": inventory_attrs["microtheory_inventory_area_count"],
            "source_digest": inventory_attrs[
                "microtheory_inventory_source_digest"],
            "graph_linked": True,
        }
    except Exception as e:
        rep["self_organisation_inventory_failed"] = (
            f"{type(e).__name__}: {e}")
    _complete_boot_observation(agent, boot_cycle, rep)
    return rep


def load_one_seed(substrate, seed_id, seed_dir=None):
    """Materialise a SINGLE encyclopedic seed (seeds/<seed_id>.json) into a raw
    ``substrate``, returning the Microtheory node id. The GENERIC replacement for
    the bespoke ``domains/<x>.py`` ``install_*_seed`` builders: it reads the same
    Mt + concepts (has_concept) + rules (has_rule) + extra_nodes + relations the
    builder produced, straight from the seed JSON. Idempotent by Mt name. Callers
    that did ``mt = install_X_seed(s)`` become ``mt = load_one_seed(s, "X")`` —
    and the builder Python can then be burned."""
    seed_dir = str(seed_dir or SEED_DIR)
    with open(os.path.join(seed_dir, f"{seed_id}.json")) as f:
        d = json.load(f)
    for _et, _tgt in (("has_concept", "Concept"), ("has_rule", "Rule"),
                      ("genlMt", "Microtheory")):
        try:
            substrate.add_production({"src": {"type": "Microtheory", "var": "s"},
                                      "edge_type": _et, "tgt": {"type": _tgt, "var": "t"},
                                      "where": None, "weight": {"type": "Lit", "value": 1.0},
                                      "provenance": "load_one_seed"})
        except Exception:
            pass
    mt = d.get("microtheory")
    if isinstance(mt, dict) and mt.get("name"):
        mt_name = mt["name"]
        mt_attrs = {k: v for k, v in mt.items() if isinstance(v, (str, int, float, bool))}
    elif isinstance(mt, str) and mt:
        mt_name, mt_attrs = mt, {"name": mt}
    else:
        mt_name = d.get("id") or seed_id
        mt_attrs = {"name": mt_name, "version": d.get("version", ""),
                    "description": d.get("description", ""), "origin": mt_name}

    # FULL existing-node index from graph_to_dict (every type) so the load is
    # IDEMPOTENT: a node already present (by name, or by full attrs for a NAMELESS
    # node like DesignExclusion) is reused, never duplicated. name2id/name2type
    # also drive name-based relation resolution.
    name2id, name2type, nameless = {}, {}, {}

    def _norm(v):
        # the substrate stores list attrs as TUPLES (read back as tuples); a
        # captured seed has them as lists. Normalise both to lists so a nameless
        # node's signature matches across a re-load (idempotency).
        if isinstance(v, (list, tuple)):
            return [_norm(x) for x in v]
        return v

    def _sig(attrs):
        return frozenset((k, repr(_norm(v))) for k, v in attrs.items())

    try:
        # enumerate node TYPES from graph_to_dict, but resolve ids via
        # substrate.nodes(t) so the index holds real NodeID objects (graph_to_dict
        # ids are raw ints, which add_edge rejects).
        types = {n.get("type") for n in substrate.graph_to_dict().get("nodes", [])
                 if n.get("type")}
        for t in types:
            for nid in substrate.nodes(t):
                a = substrate.node(nid)["attrs"]
                nm = a.get("name")
                if nm:
                    name2id.setdefault(nm, nid); name2type.setdefault(nm, t)
                else:
                    nameless.setdefault((t, _sig(a)), nid)
    except Exception:
        pass

    def _carry(src, drop=()):
        return {k: v for k, v in src.items()
                if k not in drop and isinstance(v, (str, int, float, bool, list))}

    def _node(node_type, attrs):
        """Idempotent node create: reuse an existing node with the same (type,
        name) or, when nameless, the same (type, full attrs). Returns the id."""
        nm = attrs.get("name")
        if nm is not None:
            ex = name2id.get(nm)
            if ex is not None and name2type.get(nm) == node_type:
                return ex
            nid = substrate.add_node(node_type, attrs)
            name2id[nm], name2type[nm] = nid, node_type
            return nid
        key = (node_type, _sig(attrs))
        if key in nameless:
            return nameless[key]
        nid = substrate.add_node(node_type, attrs)
        nameless[key] = nid
        return nid

    def _edge(src_id, edge_type, tgt_id, src_t=None, tgt_t=None):
        if src_t and tgt_t:
            try:
                substrate.add_production({"src": {"type": src_t, "var": "s"},
                                          "edge_type": edge_type, "tgt": {"type": tgt_t, "var": "t"},
                                          "where": None, "weight": {"type": "Lit", "value": 1.0},
                                          "provenance": "load_one_seed:edge"})
            except Exception:
                pass
        try:
            if substrate.has_edge(src_id, edge_type, tgt_id):   # idempotent
                return
        except Exception:
            pass
        try:
            substrate.add_edge(src_id, edge_type, tgt_id, None)
        except Exception:
            pass

    mt_attrs.setdefault("name", mt_name)
    mt_id = _node("Microtheory", mt_attrs)

    for c in (d.get("concepts") or []):
        if not isinstance(c, dict) or not c.get("name"):
            continue
        defn = c.get("definition")
        cattrs = {"name": c["name"], "definition": defn if isinstance(defn, str) else "",
                  "domain": c.get("domain", "")}
        for k in ("why", "category", "term", "origin"):
            if isinstance(c.get(k), (str, int, float, bool)):
                cattrs[k] = c[k]
        cid = _node("Concept", cattrs)
        _edge(mt_id, "has_concept", cid, "Microtheory", "Concept")
    for r in (d.get("rules") or []):
        if not isinstance(r, dict) or not r.get("name"):
            continue
        rid = _node("Rule", _carry(r))
        _edge(mt_id, "has_rule", rid, "Microtheory", "Rule")
    # extra_nodes: arbitrary typed nodes (DesignPattern / CodeTarget /
    # DesignExclusion / ...), named OR nameless, with ALL attrs incl nested-list
    # weight matrices — reproduced idempotently.
    for en in (d.get("extra_nodes") or []):
        if not isinstance(en, dict) or not en.get("type"):
            continue
        _node(en["type"], _carry(en, drop=("type",)))

    # parent(s) + relations -> name-based edges (genlMt to compiler_theory /
    # code_authoring / neural_networks, built_from, ...).
    rels = list(d.get("relations") or [])
    parent = (mt.get("parent") if isinstance(mt, dict) else None) \
        or d.get("parent_mt") or d.get("parent")
    for p in ([parent] if isinstance(parent, str) else (parent or [])):
        if p:
            rels.append({"src": mt_name, "edge": "genlMt", "tgt": p})
    for rel in rels:
        if not (isinstance(rel, dict) and rel.get("src") and rel.get("edge") and rel.get("tgt")):
            continue
        sidn, tidn = name2id.get(rel["src"]), name2id.get(rel["tgt"])
        if sidn is None or tidn is None:
            continue
        _edge(sidn, rel["edge"], tidn, name2type.get(rel["src"]), name2type.get(rel["tgt"]))
    return mt_id
