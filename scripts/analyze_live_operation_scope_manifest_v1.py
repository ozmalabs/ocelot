#!/usr/bin/env python3
"""Build a source-linked candidate read/write manifest for live traced rules."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import tempfile
from collections import Counter, defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_LIVE_OPERATION_SCOPE_MANIFEST_V1_PREREG_20261003.md"
LOCK = ROOT / "evaluation/substrate_capability/live_operation_scope_manifest_v1_lock_20261003.json"
RAW_IN = ROOT / "evaluation/reports/substrate_live_frame_rule_scope_capture_v1_1_workers_raw_20261003.json.gz"
CAPTURE_SUMMARY = ROOT / "evaluation/reports/substrate_live_frame_rule_scope_capture_v1_1_20261003.json"
CAPTURE_ANALYSIS = ROOT / "evaluation/reports/live_frame_rule_scope_capture_v1_1_analysis_20261003.json"
TERM_INVENTORY = ROOT / "evaluation/reports/term_access_dependency_coverage_v1_1_20261003.json"
TERM_JOIN = ROOT / "evaluation/reports/live_frame_term_scope_join_v1_20261003.json"
OUT = ROOT / "evaluation/reports/live_operation_scope_manifest_v1_20261003.json"
SOURCES = {
    "term": ROOT / "runners/dsl/src/term.rs",
    "rewrite": ROOT / "runners/dsl/src/rewrite.rs",
    "access_trace": ROOT / "runners/dsl/src/access_trace.rs",
    "py": ROOT / "runners/dsl/src/py.rs",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lock_inputs() -> dict:
    return {
        "protocol_sha256": sha(PROTOCOL), "runner_sha256": sha(Path(__file__).resolve()),
        "request_time_capture_lock_sha256": sha(ROOT / "evaluation/substrate_capability/live_frame_rule_scope_capture_v1_1_lock_20261003.json"),
        "request_time_capture_summary_sha256": sha(CAPTURE_SUMMARY),
        "request_time_capture_analysis_sha256": sha(CAPTURE_ANALYSIS),
        "request_time_raw_archive_sha256": sha(RAW_IN),
        "term_inventory_sha256": sha(TERM_INVENTORY), "term_join_sha256": sha(TERM_JOIN),
        "source_sha256": {name: sha(path) for name, path in SOURCES.items()},
    }


def walk_terms(value, known: set[str], unknown: set[str] | None = None):
    if isinstance(value, dict):
        term_type = value.get("type")
        if isinstance(term_type, str) and term_type[:1].isupper():
            if term_type in known:
                yield value
            elif unknown is not None:
                unknown.add(term_type)
        for key, child in value.items():
            if term_type == "Lit" and key == "value":
                continue
            yield from walk_terms(child, known, unknown)
    elif isinstance(value, list):
        for child in value:
            yield from walk_terms(child, known, unknown)


def effect_term_roots(value):
    if isinstance(value, dict):
        if "__term__" in value:
            yield value["__term__"]
        else:
            for child in value.values():
                yield from effect_term_roots(child)
    elif isinstance(value, list):
        for child in value:
            yield from effect_term_roots(child)


def literal_key(value) -> str | None:
    return value if isinstance(value, str) and value else None


def parse_rule_scope(rule: dict, term_rows: dict[str, dict], known_terms: set[str]) -> dict:
    reads = set()
    writes = set()
    broad_reads = set()
    broad_writes = set()
    read_attrs = set()
    read_edge_types = set()
    read_population_types = set()
    write_attrs = set()
    write_edge_types = set()
    write_population_types = set()
    dynamic_term_sites = []
    external_dependencies = []
    population_queries = []
    unknown_effects = []
    rule_store_effects = []

    match_edges = []
    for edge in rule.get("match") or []:
        if isinstance(edge, list) and len(edge) >= 3:
            edge_type = literal_key(edge[1])
            if edge_type:
                reads.add("edge:" + edge_type)
                read_edge_types.add(edge_type)
                match_edges.append(edge_type)
            else:
                reads.add("edge:*")
                broad_reads.add("untyped_match_edge")

    unclassified_term_types: set[str] = set()
    terms = list(walk_terms(rule.get("where"), known_terms, unclassified_term_types))
    for root in effect_term_roots(rule.get("effects")):
        terms.extend(walk_terms(root, known_terms, unclassified_term_types))
    for term in terms:
        variant = str(term["type"])
        source = term_rows[variant]
        cls = source["access_class"]
        if source.get("external_dependency"):
            external_dependencies.append({"term": variant, "dependency": source["external_dependency"]})
            reads.add("external:" + variant)
        if source.get("source_review_kind") == "dynamic_helper":
            dynamic_term_sites.append({"term": variant, "source_review": source.get("source_review"),
                                       "access_class": cls})
        if cls == "wildcard_reads_any":
            broad_reads.add("source_reads_any:" + variant)
            reads.add("all_graph:*")

        if variant in {"Attr"}:
            key = literal_key(term.get("key"))
            if key:
                read_attrs.add(key)
                reads.add("attr:" + key)
            else:
                broad_reads.add("dynamic_attribute_key")
                reads.add("attr:*")
        elif variant == "AttrByName":
            broad_reads.add("dynamic_attribute_key")
            reads.add("attr:*")
        elif variant == "TypeOf":
            broad_reads.add("bound_node_type_read")
            reads.add("population:*")
        elif variant == "NodesOfType":
            node_type = literal_key(term.get("node_type"))
            population_queries.append({"term": variant, "node_type": node_type,
                                      "whole_population_candidate": True})
            if node_type:
                read_population_types.add(node_type)
                reads.add("population:" + node_type)
            else:
                reads.add("population:*")
                broad_reads.add("dynamic_population_type")
        elif variant == "NodesWhere":
            node_type = literal_key(term.get("node_type"))
            attr_key = literal_key(term.get("attr_key"))
            population_queries.append({"term": variant, "node_type": node_type,
                                      "attribute_key": attr_key,
                                      "whole_population_candidate": True,
                                      "index_or_scan_path_runtime_dependent": True})
            if node_type:
                read_population_types.add(node_type)
                reads.add("population:" + node_type)
            else:
                reads.add("population:*")
                broad_reads.add("dynamic_population_type")
            if attr_key:
                read_attrs.add(attr_key)
                reads.add("attr:" + attr_key)
            else:
                reads.add("attr:*")
                broad_reads.add("dynamic_attribute_key")
        elif variant in {"Neighbours", "InNeighbours", "MapNeighbours", "SlideNeighbours", "Edges"}:
            edge_type = literal_key(term.get("edge_type"))
            if edge_type:
                read_edge_types.add(edge_type)
                reads.add("edge:" + edge_type)
            else:
                reads.add("edge:*")
                broad_reads.add("all_edge_types_local_adjacency")
        elif variant == "ScalarAttrTriples":
            population_queries.append({"term": variant, "node_type": None,
                                      "whole_population_candidate": True})
            broad_reads.add("whole_graph_scalar_attribute_scan")
            reads.add("all_graph:*")
        elif variant == "EdgeAttr":
            edge_attr = literal_key(term.get("key"))
            if edge_attr:
                reads.add("edge_attr:*:" + edge_attr)
            else:
                reads.add("edge_attr:*:*")
                broad_reads.add("dynamic_edge_attribute_key")

    effect_kinds = []
    for effect in rule.get("effects") or []:
        if not isinstance(effect, list) or not effect:
            unknown_effects.append({"shape": effect, "reason": "not_an_effect_array"})
            broad_writes.add("unknown_effect_shape")
            writes.add("all_graph:*")
            continue
        kind = str(effect[0])
        effect_kinds.append(kind)
        if kind in {"add_edge", "del_edge"}:
            edge_type = literal_key(effect[2]) if len(effect) > 2 else None
            if edge_type:
                reads.add("edge:" + edge_type)
                writes.add("edge:" + edge_type)
                write_edge_types.add(edge_type)
            else:
                reads.add("edge:*")
                writes.add("edge:*")
                broad_writes.add("dynamic_edge_write")
                broad_reads.add("dynamic_edge_read")
            attrs = effect[4] if kind == "add_edge" and len(effect) > 4 and isinstance(effect[4], dict) else {}
            for key in attrs:
                reads.add("edge_attr:*:" + str(key))
                writes.add("edge_attr:*:" + str(key))
        elif kind in {"add_node", "add_node_if_absent"}:
            node_type = literal_key(effect[2]) if len(effect) > 2 else None
            if node_type:
                writes.add("population:" + node_type)
                write_population_types.add(node_type)
                if kind == "add_node_if_absent":
                    reads.add("population:" + node_type)
            else:
                writes.add("population:*")
                broad_writes.add("dynamic_node_type_write")
                if kind == "add_node_if_absent":
                    reads.add("population:*")
                    broad_reads.add("dynamic_node_type_read")
            attrs = effect[3] if len(effect) > 3 and isinstance(effect[3], dict) else {}
            for key in attrs:
                write_attrs.add(str(key))
                writes.add("attr:" + str(key))
                if kind == "add_node_if_absent":
                    reads.add("attr:" + str(key))
        elif kind in {"set_attr", "set_attr_if_different"}:
            attr_key = literal_key(effect[2]) if len(effect) > 2 else None
            if attr_key:
                write_attrs.add(attr_key)
                writes.add("attr:" + attr_key)
                if kind == "set_attr_if_different":
                    reads.add("attr:" + attr_key)
            else:
                writes.add("attr:*")
                broad_writes.add("dynamic_attribute_write")
                if kind == "set_attr_if_different":
                    reads.add("attr:*")
                    broad_reads.add("dynamic_attribute_read")
        elif kind == "del_node":
            writes.add("all_graph:*")
            broad_writes.add("node_delete_removes_incident_edges_and_attributes")
        elif kind in {"define_concept", "set_rule_clause", "add_rule", "remove_rule", "delete_rule"}:
            writes.add("rule_store:*")
            rule_store_effects.append(kind)
        else:
            unknown_effects.append({"kind": kind, "shape": effect})
            writes.add("all_graph:*")
            broad_writes.add("unrecognized_effect:" + kind)

    return {
        "rule_uid": int(rule["rule_uid"]), "name": rule.get("name"),
        "definition_sha256": hashlib.sha256(json.dumps(rule, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest(),
        "match_edge_types": sorted(set(match_edges)),
        "read_edge_types": sorted(read_edge_types), "read_attribute_keys": sorted(read_attrs),
        "read_population_types": sorted(read_population_types),
        "population_queries": population_queries,
        "write_edge_types": sorted(write_edge_types), "write_attribute_keys": sorted(write_attrs),
        "write_population_types": sorted(write_population_types),
        "read_resources": sorted(reads), "write_resources": sorted(writes),
        "broad_read_reasons": sorted(broad_reads), "broad_write_reasons": sorted(broad_writes),
        "dynamic_term_sites": sorted(dynamic_term_sites, key=lambda row: (row["term"], row["source_review"] or "")),
        "external_dependencies": external_dependencies,
        "rule_store_effects": sorted(set(rule_store_effects)),
        "effect_kinds": sorted(set(effect_kinds)),
        "unrecognized_effects": unknown_effects,
        "unclassified_term_variants": sorted(unclassified_term_types),
        "term_variant_counts": dict(sorted(Counter(str(term["type"]) for term in terms).items())),
    }


def dependency_graph(scopes: list[dict], conservative: bool) -> dict:
    readers: dict[str, set[int]] = defaultdict(set)
    writers: dict[str, set[int]] = defaultdict(set)
    broad_reader_ids: set[int] = set()
    broad_writer_ids: set[int] = set()
    for scope in scopes:
        uid = int(scope["rule_uid"])
        for resource in scope["read_resources"]:
            if not conservative and "*" in resource:
                continue
            readers[resource].add(uid)
        for resource in scope["write_resources"]:
            if not conservative and "*" in resource:
                continue
            writers[resource].add(uid)
        if scope["broad_read_reasons"]:
            broad_reader_ids.add(uid)
        if scope["broad_write_reasons"]:
            broad_writer_ids.add(uid)
    edges: set[tuple[int, int, str]] = set()
    for resource in sorted(set(readers) & set(writers)):
        for producer in writers[resource]:
            for consumer in readers[resource]:
                edges.add((producer, consumer, resource))
    if conservative:
        all_writers = set().union(*writers.values()) if writers else set()
        all_readers = set().union(*readers.values()) if readers else set()
        for consumer in broad_reader_ids:
            for producer in all_writers:
                edges.add((producer, consumer, "broad_read"))
        for producer in broad_writer_ids:
            for consumer in all_readers:
                edges.add((producer, consumer, "broad_write"))

    adjacency: dict[int, set[int]] = defaultdict(set)
    for producer, consumer, _ in edges:
        adjacency[producer].add(consumer)
        adjacency[consumer].add(producer)
    all_ids = {int(scope["rule_uid"]) for scope in scopes}
    seen: set[int] = set()
    component_sizes = []
    for root in sorted(all_ids):
        if root in seen:
            continue
        todo = [root]
        seen.add(root)
        size = 0
        while todo:
            current = todo.pop()
            size += 1
            for neighbor in adjacency[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    todo.append(neighbor)
        component_sizes.append(size)
    pair_resources: dict[tuple[int, int], set[str]] = defaultdict(set)
    for producer, consumer, resource in edges:
        pair_resources[(producer, consumer)].add(resource)
    pair_outdegree: Counter[int] = Counter(producer for producer, _ in pair_resources)
    pair_indegree: Counter[int] = Counter(consumer for _, consumer in pair_resources)
    return {
        "mode": "conservative_with_broad_edges" if conservative else "finite_declared_resource_overlap",
        "rule_count": len(all_ids), "resource_edge_count": len(edges),
        "rule_pair_count": len(pair_resources), "resource_key_count": len(set(readers) | set(writers)),
        "component_count": len(component_sizes), "largest_undirected_component": max(component_sizes, default=0),
        "component_size_distribution_desc": sorted(component_sizes, reverse=True),
        "max_distinct_rule_consumer_count": max(pair_outdegree.values(), default=0),
        "max_distinct_rule_producer_count": max(pair_indegree.values(), default=0),
        "readers_by_resource": {key: sorted(value) for key, value in sorted(readers.items())},
        "writers_by_resource": {key: sorted(value) for key, value in sorted(writers.items())},
        "dependency_edges": [{"producer_rule_uid": a, "consumer_rule_uid": b,
                               "resources": sorted(resources)}
                              for (a, b), resources in sorted(pair_resources.items())],
    }


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".operation-scope-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    except BaseException:
        try:
            os.unlink(temp)
        except FileNotFoundError:
            pass
        raise


def build() -> dict:
    capture_summary = json.loads(CAPTURE_SUMMARY.read_text())
    capture_analysis = json.loads(CAPTURE_ANALYSIS.read_text())
    inventory = json.loads(TERM_INVENTORY.read_text())
    term_join = json.loads(TERM_JOIN.read_text())
    if sha(RAW_IN) != capture_summary["raw_compressed_sha256"]:
        raise SystemExit("request-time raw archive hash mismatch")
    if not all(capture_analysis["checks"].values()) or not all(inventory["checks"].values()) or not all(term_join["checks"].values()):
        raise SystemExit("an upstream locked capture or source audit has failed checks")
    for name, expected in inventory["inputs"].items():
        source_name = {"term_rs_sha256": "term", "rewrite_rs_sha256": "rewrite",
                       "access_trace_rs_sha256": "access_trace"}[name]
        if sha(SOURCES[source_name]) != expected:
            raise SystemExit(f"Term inventory source is stale: {source_name}")
    locked = lock_inputs()
    with gzip.open(RAW_IN, "rt", encoding="utf-8") as stream:
        raw = json.load(stream)
    term_rows = {row["variant"]: row for row in inventory["rows"]}
    known_terms = set(term_rows)
    runtime_uids: set[int] = set()
    prompt_by_uid: dict[int, set[str]] = defaultdict(set)
    observed_weight_by_uid: Counter[int] = Counter()
    observed_event_kinds: dict[int, Counter[str]] = defaultdict(Counter)
    request_uid_rows = []
    selected_definitions: dict[int, dict] = {}
    definition_hashes: dict[int, set[str]] = defaultdict(set)
    all_uids_resolve = True
    for run in raw["runs"]:
        for index, snapshot in enumerate(run["request_rule_snapshots"]):
            prompt = str(snapshot["prompt"])
            after = {int(rule["rule_uid"]): rule for rule in snapshot["after_rules"]}
            request = run["capture"]["requests"][index]
            request_uids = {int(row[0]) for row in request["access_rows"]}
            missing = sorted(request_uids - after.keys())
            all_uids_resolve &= not missing
            for access in request["access_rows"]:
                uid, kind, count = int(access[0]), str(access[1]), int(access[6])
                runtime_uids.add(uid)
                prompt_by_uid[uid].add(prompt)
                observed_weight_by_uid[uid] += count
                observed_event_kinds[uid][kind] += count
            for uid in request_uids & after.keys():
                rule = after[uid]
                fingerprint = hashlib.sha256(json.dumps(rule, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
                definition_hashes[uid].add(fingerprint)
                selected_definitions.setdefault(uid, rule)
            request_uid_rows.append({"replicate": int(run["replicate"]), "turn": index,
                                     "prompt": prompt, "observed_uid_count": len(request_uids),
                                     "unmapped_uids": missing})
    definition_stable = all(len(values) == 1 for values in definition_hashes.values())
    scope_rows = []
    unknown_term_variants: set[str] = set()
    for uid in sorted(runtime_uids):
        rule = selected_definitions.get(uid)
        if rule is None:
            continue
        scope = parse_rule_scope(rule, term_rows, known_terms)
        scope["prompts"] = sorted(prompt_by_uid[uid])
        scope["weighted_access_events_across_workers"] = observed_weight_by_uid[uid]
        scope["observed_event_kinds"] = dict(sorted(observed_event_kinds[uid].items()))
        unknown_term_variants.update(scope["unclassified_term_variants"])
        scope_rows.append(scope)

    finite_graph = dependency_graph(scope_rows, conservative=False)
    conservative_graph = dependency_graph(scope_rows, conservative=True)
    total_weight = sum(observed_weight_by_uid.values())
    effect_kind_counts: Counter[str] = Counter()
    unknown_effect_counts: Counter[str] = Counter()
    broad_read_rule_count = broad_write_rule_count = 0
    population_query_rule_count = 0
    for scope in scope_rows:
        broad_read_rule_count += bool(scope["broad_read_reasons"])
        broad_write_rule_count += bool(scope["broad_write_reasons"])
        population_query_rule_count += bool(scope["population_queries"])
        for kind in scope["effect_kinds"] if "effect_kinds" in scope else []:
            effect_kind_counts[kind] += 1
        for unknown in scope["unrecognized_effects"]:
            unknown_effect_counts[str(unknown.get("kind", unknown.get("reason", "unknown")))] += 1
    checks = {
        "all_input_hashes_stable": lock_inputs() == locked,
        "all_capture_observed_uids_resolve": all_uids_resolve,
        "request_time_definitions_stable_across_workers": definition_stable,
        "every_captured_rule_uid_has_one_scope": len(scope_rows) == len(runtime_uids) == 401,
        "all_term_variants_map_to_source_inventory": not unknown_term_variants,
        "weighted_access_conservation": total_weight == 1_650_456,
        "both_dependency_graphs_cover_all_scope_rows": finite_graph["rule_count"] == conservative_graph["rule_count"] == len(scope_rows),
    }
    result = {
        "schema_version": 1,
        "run_id": "live-operation-scope-manifest-v1-20261003",
        "locked_inputs": locked,
        "post_analysis_inputs": lock_inputs(),
        "checks": checks,
        "summary": {
            "runtime_touched_rule_count": len(scope_rows),
            "distinct_runtime_term_variants": len(set().union(*(set(scope["term_variant_counts"]) for scope in scope_rows))),
            "weighted_access_events": total_weight,
            "rules_with_broad_or_dynamic_reads": int(broad_read_rule_count),
            "rules_with_broad_or_unresolved_writes": int(broad_write_rule_count),
            "rules_with_population_query_terms": int(population_query_rule_count),
            "effect_kind_rule_counts": dict(sorted(effect_kind_counts.items())),
            "unrecognized_effect_counts": dict(sorted(unknown_effect_counts.items())),
            "finite_dependency_graph": {k: v for k, v in finite_graph.items()
                                         if k not in {"dependency_edges", "readers_by_resource", "writers_by_resource"}},
            "conservative_dependency_graph": {k: v for k, v in conservative_graph.items()
                                               if k not in {"dependency_edges", "readers_by_resource", "writers_by_resource"}},
        },
        "request_uid_coverage": request_uid_rows,
        "term_source_inventory": str(TERM_INVENTORY.relative_to(ROOT)),
        "term_scope_join": str(TERM_JOIN.relative_to(ROOT)),
        "finite_resource_dependency_edges": finite_graph["dependency_edges"],
        "conservative_dependency_edges": conservative_graph["dependency_edges"],
        "finite_resource_maps": {"readers": finite_graph["readers_by_resource"],
                                 "writers": finite_graph["writers_by_resource"]},
        "conservative_resource_maps": {"readers": conservative_graph["readers_by_resource"],
                                       "writers": conservative_graph["writers_by_resource"]},
        "per_rule_operation_scopes": scope_rows,
        "claim_boundary": "Source-linked syntactic candidate operation scopes over rules that emitted access rows in this authored prompt pair. Broad dependency edges are conservative projections from declared broad reads/writes. Unobserved rules, execution-time branch conditions, implicit/evaluator/callback dependencies, and factor variables/domains are not complete. The graph is not proof of frame locality, exact partition semantics, or speedup.",
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", action="store_true")
    args = parser.parse_args()
    if args.lock:
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps({"locked_inputs": lock_inputs()}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return
    locked = json.loads(LOCK.read_text()).get("locked_inputs") if LOCK.exists() else None
    if locked != lock_inputs():
        raise SystemExit("missing or stale operation-scope manifest lock")
    result = build()
    atomic_json(OUT, result)
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": result["checks"],
                      "summary": result["summary"]}, indent=2))
    if not all(result["checks"].values()):
        raise SystemExit("operation-scope manifest gates failed; result retained")


if __name__ == "__main__":
    main()
