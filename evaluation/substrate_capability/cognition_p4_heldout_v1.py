#!/usr/bin/env python3
"""P4 preregistered conformance/evaluation runner.

This first runner slice executes the registered D2/D3 native-versus-legacy
signature conformance family and collision controls. Families without an
executable producer remain explicitly absent for analysis; no synthetic
outcomes are substituted for them.
"""
from __future__ import annotations

import json
import hashlib
import os
import re
import random
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "capability" / "number_qualia" / "runners"))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))

from substrate_rs import _native
from number_runner import aperture_signature
from scripts.gen_qualia_shape_mint_seed import build_seed as build_shape_seed
from scripts.gen_cognition_signature_seed import build_seed as build_signature_seed
from scripts.gen_cognition_aperture_seed import build_seed as build_cognition_aperture_seed
from evaluation.substrate_capability.cognition_p4_instances_v1 import draw_panel
from substrate.seed_loader import manifest_for
from substrate.boot_core import CORE_SEEDS
from substrate.world_adapter import WorldAdapter
PROTOCOL = "cognition_p4_heldout_v1"
REGISTERED_END = 200
MAX_RULE_PASSES = 64
D2_SALT = 0x44324433
C5_SALT = 0x43355335
D1_SALT = 0x44315331
E1_SALT = 0x45314532
FROZEN_ARTIFACTS = (
    "evaluation/substrate_capability/cognition_p4_heldout_v1.py",
    "evaluation/substrate_capability/cognition_p4_analysis_v1.py",
    "evaluation/substrate_capability/cognition_p4_instances_v1.py",
    "tests/capability/number_qualia/runners/number_runner.py",
    "docs/research/engine_substrate/COGNITION_BUILD_P4_PREREG.md",
    "docs/research/engine_substrate/COGNITION_BUILD_P4_REPRESENTATION_PLAN.md",
    "docs/research/engine_substrate/COGNITION_SIGNATURE_CONTRACT.md",
    "docs/research/engine_substrate/COGNITION_APERTURE_ADAPTER_CONTRACT.md",
    "docs/research/engine_substrate/COGNITION_MANIFOLD_INTEGRATION_CONTRACT.md",
    "scripts/gen_qualia_shape_mint_seed.py",
    "scripts/gen_cognition_signature_seed.py",
    "scripts/gen_cognition_aperture_seed.py",
    "scripts/gen_aperture_frame_seed.py",
    "scripts/gen_similarity_recall_seed.py",
    "scripts/gen_cognition_manifold_seed.py",
    "scripts/gen_thought_manifold_seed.py",
    "seeds/qualia_shape_mint.json",
    "seeds/qualia_space.json",
    "seeds/cognition_signature.json",
    "seeds/cognition_aperture.json",
    "seeds/aperture_frame.json",
    "seeds/similarity_recall.json",
    "seeds/cognition_manifold.json",
    "seeds/thought_manifold.json",
    "seeds/generative_world_model.json",
    "seeds/aperture_frame.json",
    "seeds/observer_aperture.json",
    "seeds/thinking_budget.json",
    "scripts/gen_temporal_escalation_seed.py",
    "seeds/temporal_escalation.json",
    "seeds/time_axis.json",
    "substrate/world_adapter.py",
    "substrate/boot_core.py",
    "substrate/seed_loader.py",
    "runners/dsl/src/shape_decode.rs",
    "runners/dsl/src/memory.rs",
    "runners/dsl/src/future_manifold.rs",
    "runners/dsl/src/jsonio.rs",
    "runners/dsl/src/reflect.rs",
    "runners/dsl/src/rewrite.rs",
    "runners/dsl/src/shape.rs",
    "runners/dsl/src/term.rs",
    "runners/dsl/src/term_variants.rs",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
    "runners/dsl/python/substrate_rs/_native.build.json",
)
FROZEN_ARTIFACTS = tuple(dict.fromkeys((
    *FROZEN_ARTIFACTS,
    *(f"seeds/{seed_id}.json" for seed_id in CORE_SEEDS),
)))


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                           text=True, check=False)
    if result.returncode:
        raise ValueError(result.stderr.strip() or "git verification failed")
    return result.stdout.strip()


def _verify_registered_freeze(prereg_hash: str) -> None:
    head = _git("rev-parse", "HEAD")
    if prereg_hash.lower() != head.lower():
        raise ValueError("registered run requires the preregistration-only freeze commit at HEAD")
    if os.environ.get("COGNITION_PREREG_HASH", "").lower() != prereg_hash.lower():
        raise ValueError("COGNITION_PREREG_HASH must equal the frozen preregistration commit")
    for path in FROZEN_ARTIFACTS:
        _git("cat-file", "-e", f"{head}:{path}")
        if _git("status", "--porcelain", "--", path):
            raise ValueError(f"frozen artifact has local changes: {path}")


def _artifact_hashes() -> dict[str, str]:
    paths = (*FROZEN_ARTIFACTS,)
    return {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            for path in paths}


def _vector(seed: int, index: int) -> tuple[list[float], int]:
    import random
    rng = random.Random(seed + 7919 * index + D2_SALT)
    length = rng.randint(1, 24)
    coord = [float(rng.randint(-500, 500)) / rng.choice((1, 1, 2, 5))
             for _ in range(length)]
    return coord, rng.randint(0, min(length, 5))


def _native_signature(coord: list[float], order: int) -> list[int] | None:
    term = {"type": "ShapeRankSignature",
            "samples": {"type": "Var", "name": "samples"},
            "order": {"type": "Var", "name": "order"},
            "width": {"type": "Lit", "value": 8}}
    value = _native.Substrate().evaluate(term, {"samples": coord, "order": order})
    return list(value) if value is not None else None


def _record(key: str, signature: list[int], *, owner="owner-a", source="qualia_shape",
            frame="frame-a", dimension="numeric:shape_rank:2", epoch=7) -> dict:
    return {"record_key": key, "owner_id": owner, "source_id": source,
            "frame_id": frame, "schema_version": "1", "source_epoch": epoch,
            "live": True,
            "coordinates": [(dimension, "sequence_ref", signature, False, 0)]}


def _recall(records: list[dict], query: dict) -> tuple:
    sub = _native.Substrate()
    term = {"type": "RecallNearest", "records": {"type": "Var", "name": "records"},
            "query": {"type": "Var", "name": "query"}, "k": {"type": "Lit", "value": 8},
            "candidate_cap": {"type": "Lit", "value": 32}}
    return sub.evaluate(term, {"records": records, "query": query})


def _transfer_records_and_query(payload: dict) -> tuple[list[dict], dict]:
    """Mechanically adapt one source/frame and its target candidates to records."""
    family = payload["family"]
    source, target = payload["source_exposure"], payload["target_problem"]
    frame_map = payload["frame_map"]
    source_frame = source.get("frame_id", "source-frame")
    target_frame = target.get("frame_id", "target-frame")
    projected_frame = frame_map.get(source_frame, source_frame)
    owner, source_id, epoch = "transfer-agent", "cross-domain-transfer", 1
    if family == "graph_role":
        relation_ids = {node_id for role, node_id in source["nodes"] if role == "relation"}
        source_value = next((edge for src, edge, _dst in source["edges"]
                             if src in relation_ids), None)
        candidate_nodes = [node_id for role, node_id in target["nodes"]
                           if role == "candidate"]
        relation_nodes = {node_id for role, node_id in target["nodes"]
                          if role == "relation"}
        candidates = []
        for candidate in candidate_nodes:
            relation = next((edge for src, edge, dst in target["edges"]
                             if src in relation_nodes and dst == candidate), None)
            candidates.append((candidate, relation))
        dimension, value_kind = "graph:relation_role", "token"
        query_value = source_value
        candidate_values = candidates
    elif family == "numeric_sequence":
        if len(source.get("y", [])) < 2 or not target.get("candidates"):
            return [], {}
        query_value = _native.Substrate().evaluate(
            {"type": "Minus", "a": {"type": "Lit", "value": source["y"][-1]},
             "b": {"type": "Lit", "value": source["y"][-2]}}, {})
        dimension, value_kind = "numeric:sequence_delta", "finite_number"
        candidate_values = []
        last_target = target["y"][-1]
        for candidate in target["candidates"]:
            delta = _native.Substrate().evaluate(
                {"type": "Minus", "a": {"type": "Lit", "value": candidate["y"]},
                 "b": {"type": "Lit", "value": last_target}}, {})
            candidate_values.append((candidate["id"], delta))
    else:
        return [], {}
    query_coordinate = (dimension, value_kind, query_value, False, 1_000_000_000)
    query = {"record_key": "transfer-query", "owner_id": owner,
             "source_id": source_id, "frame_id": projected_frame,
             "schema_version": "1", "source_epoch": epoch, "live": True,
             "coordinates": [query_coordinate]}
    records = []
    for candidate_id, candidate_value in candidate_values:
        records.append({"record_key": candidate_id, "owner_id": owner,
                        "source_id": source_id, "frame_id": target_frame,
                        "schema_version": "1", "source_epoch": epoch,
                        "live": True,
                        "coordinates": [(dimension, value_kind, candidate_value,
                                         False, 1_000_000_000)]})
    return records, query


def _d5_native_arm(payload: dict, arm: str) -> dict:
    """Run candidate retrieval/scan as native Terms; return unscored agent output."""
    records, query = _transfer_records_and_query(payload)
    if not records or not query:
        return {"selected_candidate": None, "exact_candidate_checks": None,
                "timeout": False, "target_digest": payload.get("target_digest")}

    def lit(value): return {"type": "Lit", "value": value}
    def var(name): return {"type": "Var", "name": name}
    def get(mapping, key): return {"type": "DictGet", "dict": mapping, "key": lit(key)}
    def index(seq, i): return {"type": "IndexAt", "seq": seq, "index": lit(i)}
    if arm == "recall_off":
        matching = {"type": "FilterList", "source": lit(records),
                    "var_name": "record",
                    "predicate": {"type": "Eq",
                                  "a": get(var("record"), "coordinates"),
                                  "b": lit(query["coordinates"])}}
        selected = index({"type": "MapList", "source": matching,
                          "var_name": "match", "value": get(var("match"), "record_key")}, 0)
        checks = {"type": "Count", "source": lit(records)}
        output = {"type": "MkDict", "items": [lit("selected"), selected,
                    lit("checks"), checks, lit("scanned"), checks,
                    lit("complete"), lit(True)]}
    else:
        scan = {"type": "RecallNearest", "records": lit(records),
                "query": lit(query), "k": lit(1), "candidate_cap": lit(32)}
        ranked = index(scan, 0)
        first_row = index(ranked, 0)
        first_candidate = index(first_row, 0)
        distance = index(first_row, 1)
        selected = {"type": "IfThenElse",
                    "cond": {"type": "Eq", "a": distance, "b": lit(0)},
                    "then": first_candidate, "other": lit(None)}
        checks = {"type": "IfThenElse",
                  "cond": {"type": "Eq", "a": first_candidate, "b": lit(None)},
                  "then": lit(0), "other": lit(1)}
        output = {"type": "MkDict", "items": [lit("selected"), selected,
                    lit("checks"), checks, lit("scanned"), index(scan, 1),
                    lit("complete"), index(scan, 2)]}
    result = _native.Substrate().evaluate(output, {})
    if not isinstance(result, dict):
        return {"selected_candidate": None, "exact_candidate_checks": None,
                "timeout": False, "target_digest": payload.get("target_digest")}
    selected, checks = result.get("selected"), result.get("checks")
    scanned, complete = result.get("scanned"), result.get("complete")
    return {"selected_candidate": selected,
            "exact_candidate_checks": int(checks) if isinstance(checks, int) else None,
            "retrieval_candidates_scanned": int(scanned) if isinstance(scanned, int) else None,
            "retrieval_complete": bool(complete), "timeout": False,
            "target_digest": payload.get("target_digest")}


def run_d5_panel(prereg_hash: str, first: int, end: int, *,
                 development: bool = False) -> list[dict]:
    """Execute paired D5 inputs; keep scorer oracle outside each arm payload."""
    rows = []
    for case in draw_panel(prereg_hash, first, end, development=development):
        outcomes = {arm: _d5_native_arm(inputs, arm)
                    for arm, inputs in case["arms"].items()}
        rows.append({"family": case["family"], "case_kind": case["case_kind"],
                     "paired_id": case["paired_id"], "draw_index": case["draw_index"],
                     "agent_inputs": case["arms"],
                     "scoring_oracle": case["scoring_oracle"], "arms": outcomes})
    return rows


def _stream(seed: int, index: int) -> dict:
    coord, order = _vector(seed, index)
    native = _native_signature(coord, order)
    legacy = aperture_signature(coord, order,
                                SimpleNamespace(shape_signature=_native.Substrate.shape_signature))
    substrate = _native.Substrate()
    agent = substrate.add_node("Agent", {})
    shape_loaded = substrate.load_seed_manifest(build_shape_seed(), agent)
    signature_loaded = substrate.load_seed_manifest(build_signature_seed(), agent)
    qsm_policy = substrate.nodes("QualiaShapeMintPolicy")[0]
    signature_policy = substrate.nodes("CognitionSignaturePolicy")[0]
    substrate.set_attr(qsm_policy, "enabled", 1.0)
    substrate.set_attr(signature_policy, "enabled", 1.0)
    obs = substrate.add_node("ShapeObservation", {
        "key": f"p4-d23-{index}", "outcome_status": "verified",
        "outcome_id": f"verified-outcome-{index}", "coordinate": coord,
        "order": order, "owner_id": "owner-a", "frame_id": f"frame-{index}",
        "source_epoch": index + 1, "valence": 1.0,
        "reading": f"verified-reading-{index}",
    })
    substrate.add_edge(agent, "observed", obs)
    converged = False
    for _ in range(MAX_RULE_PASSES):
        if not substrate.run_rules(1000):
            converged = True
            break
    shapes = substrate.nodes("QualiaShape")
    shape_ok = len(shapes) == 1 and tuple(
        substrate.node(shapes[0])["attrs"].get("signature") or ()) == tuple(native or ())
    observation_sources = [source for source in substrate.neighbours(obs, "has_signature_source")
                           if substrate.node(source)["attrs"].get("source_id") == "qualia_shape"]
    stored_sources = ([source for source in substrate.neighbours(shapes[0], "has_signature_source")
                       if substrate.node(source)["attrs"].get("source_id") == "qualia_shape"]
                      if shapes else [])
    descriptors = substrate.neighbours(agent, "has_cognition_signature")
    def descriptor_for(source):
        return next((node for node in descriptors
                     if substrate.neighbours(node, "projects_signature_source") == [source]), None)
    query_descriptor = descriptor_for(observation_sources[0]) if observation_sources else None
    stored_descriptor = descriptor_for(stored_sources[0]) if stored_sources else None
    expected_coordinate = ("numeric:shape_rank:%d" % order, "sequence_ref",
                           tuple(native or ()), False, 0)
    graph_readback = bool(shape_ok and query_descriptor is not None and stored_descriptor is not None
        and substrate.node(query_descriptor)["attrs"].get("coordinates") == (expected_coordinate,)
        and substrate.node(stored_descriptor)["attrs"].get("coordinates") == (expected_coordinate,)
        and substrate.node(query_descriptor)["attrs"].get("owner_id") == "owner-a"
        and substrate.node(query_descriptor)["attrs"].get("frame_id") == f"frame-{index}"
        and substrate.node(query_descriptor)["attrs"].get("source_epoch") == index + 1
        and substrate.node(query_descriptor)["attrs"].get("evidence_status") == "observed")
    return {"draw_index": index, "outcome_id": f"verified-outcome-{index}",
            "owner_id": "owner-a", "frame_id": f"frame-{index}",
            "source_epoch": index + 1, "coordinate": coord, "order": order,
            "native_signature": native, "legacy_signature": legacy,
            "seed_load_ok": not shape_loaded.get("rules_skipped")
                and not signature_loaded.get("rules_skipped"),
            "graph_shape_parity": shape_ok, "graph_descriptor_parity": graph_readback,
            "timeout": not converged,
            "parity": native == legacy and native is not None and graph_readback}


def _collision_control(seed: int, index: int) -> dict:
    coord, order = _vector(seed ^ 0xC0111DE, index)
    sig = _native_signature(coord, order)
    dimension = f"numeric:shape_rank:{order}"
    query = _record("query", sig, dimension=dimension, frame=f"frame-{index}", epoch=index + 1)
    exact = _record("exact", sig, dimension=dimension, frame=f"frame-{index}", epoch=index + 1)
    controls = [
        _record("other-frame", sig, dimension=dimension, frame=f"other-{index}", epoch=index + 1),
        _record("other-dimension", sig, dimension=f"other:{order}",
                frame=f"frame-{index}", epoch=index + 1),
        _record("other-owner", sig, dimension=dimension, frame=f"frame-{index}",
                owner="owner-b", epoch=index + 1),
        _record("other-epoch", sig, dimension=dimension, frame=f"frame-{index}",
                epoch=index + 2),
    ]
    candidates, checked, complete = _recall([exact, *controls], query)
    return {"draw_index": index, "source_epoch": index + 1,
            "candidate_keys": [candidate[0] for candidate in candidates],
            "checked": checked, "complete": complete,
            "zero_incompatible_merge": len(candidates) == 1 and
                candidates[0][0] == "exact" and candidates[0][1] == 0,
            "incompatible_records": len(controls)}


def _c5_episode(seed: int, *, adapter_on: bool, forced: bool = False) -> dict:
    """One generated hidden-residual/forced-frame episode through graph rules."""
    import random
    rng = random.Random(seed)
    substrate = _native.Substrate()
    agent = substrate.add_node("Agent", {})
    loaded = set()

    def load(seed_id: str, explicit=None):
        if seed_id == "core" or seed_id in loaded:
            return
        manifest = explicit if explicit is not None else manifest_for(seed_id)
        for dependency in manifest.get("depends_on", ()):
            load(str(dependency))
        summary = substrate.load_seed_manifest(manifest, agent)
        if summary.get("rules_skipped"):
            raise RuntimeError(f"malformed C5 dependency {seed_id}: {summary['rules_skipped']}")
        loaded.add(seed_id)

    load("cognition_aperture", build_cognition_aperture_seed())
    policy = substrate.nodes("CognitionAperturePolicy")[0]
    substrate.set_attr(policy, "enabled", 1.0 if adapter_on else 0.0)
    budget = substrate.nodes("ThinkingBudget")[0]
    for key, value in {"enabled": 1.0, "capacity": 1.0, "remaining": 1.0,
                       "refill_per_epoch": 0.0, "last_refill_epoch": 1.0}.items():
        substrate.set_attr(budget, key, value)
    modes = substrate.neighbours(agent, "has_network_mode_state")
    if modes:
        mode = modes[0]
    else:
        mode = substrate.add_node("NetworkModeState", {"epoch": 1.0, "mode": "awake"})
        substrate.add_edge(agent, "has_network_mode_state", mode)
    substrate.set_attr(mode, "epoch", 1.0)

    full = ["pred", "val", "obj"]
    observer_name = f"observer-{seed}"
    observer = substrate.add_node("Observer", {"name": observer_name,
        "resolves": list(full), "ap_full": list(full), "ap_scope_n": 0.0,
        "af_n": -1.0, "ap_gen": 0.0})
    max_aperture = substrate.add_node("ApertureConfig", {})
    substrate.add_edge(observer, "holds_aperture_max", max_aperture)
    aperture = substrate.add_node("Aperture", {"name": "narrow", "resolves": ["pred", "val"]})
    substrate.add_edge(observer, "forced_aperture" if forced else "chose_aperture", aperture)
    dim_types = ["pred", "val", "obj"]
    world = {
        "barometer": [["reads", "me", "pressure_trace"], ["yields", "me", "forecast"]],
        "tea_leaves": [["reads", "me", "leaf_pattern"], ["yields", "me", "forecast"]],
        "omen": [["senses", "me", "dream_image"], ["yields", "me", "forecast"]],
    }
    def part(name):
        return substrate.add_node("ShapeSignature", {"name": name, "kind": "world",
            "signature": world[name], "dim_types": dim_types})
    substrate.add_edge(observer, "holds_part", part("barometer"))
    substrate.add_edge(observer, "perceives", part("tea_leaves" if rng.randrange(2) else "omen"))
    source = substrate.add_node("CognitionApertureSource", {
        "adapter_id": "reading", "source_key": f"reading:{seed}",
        "owner_id": observer_name, "frame_id": f"frame:{observer_name}",
        "source_epoch": seed + 1, "value_kind": "integer", "value": rng.randrange(4),
        "missing": False, "tolerance": 0,
        "authority": "forced" if forced else "chosen",
        "voi_status": "unknown" if forced else "positive",
        "voi_evidence_id": None if forced else f"voi:{seed}",
        "dimension_id": "observer:reading"})
    substrate.add_edge(agent, "has_cognition_aperture_source", source)
    substrate.add_edge(source, "applies_to_observer", observer)
    converged = False
    for _ in range(MAX_RULE_PASSES):
        if not substrate.run_rules(1000):
            converged = True
            break
    requests = [node for node in substrate.nodes("ThinkingBudgetRequest")
                if substrate.node(node)["attrs"].get("requester_kind") == "cognition_aperture_probe"]
    probe = bool(substrate.neighbours(observer, "probe_projected"))
    request_states = [substrate.node(node)["attrs"].get("status") for node in requests]
    attrs = substrate.node(observer)["attrs"]
    return {"resolved_hidden_residual": probe and set(attrs.get("resolves") or ()) == set(full),
            "probe_projected": probe, "request_count": len(requests),
            "request_states": request_states,
            "unfunded_probe": probe and not any(state == "consumed" for state in request_states),
            "forced_frame_changed": forced and (probe
                or bool(substrate.neighbours(observer, "chose_aperture"))
                or bool(substrate.neighbours(observer, "negotiated_aperture"))
                or not bool(substrate.neighbours(observer, "forced_aperture"))),
            "funded_epoch": attrs.get("ap_question_funded_epoch"),
            "source_epoch": seed + 1,
            "same_epoch_debit": any(substrate.node(node)["attrs"].get("debited_epoch") ==
                substrate.node(mode)["attrs"].get("epoch") for node in requests),
            "timeout": not converged}


def _orbit_frames(rng, count=6):
    row0, col0 = rng.randint(10, 60), rng.randint(-20, 20)
    drow, dcol = rng.randint(1, 3), rng.randint(-2, 2)
    base = [["cell", row0 + dr, col0 + dc, "red"]
            for dr, dc in ((0, 0), (1, 0), (2, 0), (2, 1))]
    frames = [[ [item[0], item[1] + ix * drow, item[2] + ix * dcol, item[3]]
                for item in base] for ix in range(count)]
    return frames


def _e1e2_worlds(prereg_hash: str, first: int, end: int, *, development: bool) -> list[dict]:
    """Generate paired model-world inputs; outcomes remain empty until measured.

    Registered allocation is fixed at 80 feasible, 60 infeasible and 60
    missing-model worlds, shuffled by the preregistration-derived seed. The
    disjoint developer allocation uses the same proportions across indices
    1000..1199.
    """
    lo, hi = (1000, 1200) if development else (0, REGISTERED_END)
    count = hi - lo
    feasible_n = count * 2 // 5
    infeasible_n = count * 3 // 10
    kinds = (['feasible'] * feasible_n + ['infeasible'] * infeasible_n
             + ['missing_model'] * (count - feasible_n - infeasible_n))
    base = int(prereg_hash[:8], 16)
    random.Random(base + E1_SALT + lo).shuffle(kinds)
    worlds = []
    for index in range(first, end):
        kind = kinds[index - lo]
        rng = random.Random(base + E1_SALT + 7919 * index)
        start = rng.randint(10, 20)
        target = [[float(start + step)] for step in range(1, 4)]
        path = [[float(cell[0])] for cell in target]
        bounds = [[0.0] for _ in path]
        if kind == "infeasible":
            path = [[cell[0] + 100.0] for cell in path]
        opaque = hashlib.sha256(
            f"{prereg_hash}:e1e2:model:{index}".encode("utf-8")).hexdigest()[:16]
        model = None if kind == "missing_model" else {
            "model_id": f"model-{opaque}", "model_epoch": 1,
            "transition_id": f"transition-{opaque}",
            "values": path, "times": [1, 2, 3],
            "widths": [[0.0] for _ in path], "effort": [0.0, 0.0, 0.0],
        }
        paired_id = hashlib.sha256(
            f"{prereg_hash}:e1e2:{index}".encode("utf-8")).hexdigest()[:24]
        worlds.append({
            "paired_id": paired_id, "draw_index": index, "world_kind": kind,
            "model_input": model,
            "target": target,
            "bounds": bounds,
            "arms": {"bridge_on": None, "bridge_off": None,
                     "supplied_path_parity": None},
            "scoring_oracle": {"model_supports_path": model is not None,
                               "feasible": kind == "feasible"},
        })
    return worlds


def _e1e2_arm(world: dict, arm: str) -> dict:
    """Run one generated world through the native GWM/manifold graph path."""
    adapter = WorldAdapter(seeds=CORE_SEEDS + (
        "generative_world_model", "thinking_budget", "cognition_manifold"))
    try:
        sub, root = adapter.s, adapter.agent
        policy = sub.nodes("CognitionManifoldPolicy")[0]
        episode = sub.nodes("CognitionManifoldEpisode")[0]
        budget = sub.nodes("ThinkingBudget")[0]
        mode = sub.nodes("NetworkModeState")[0]
        sub.set_attr(policy, "enabled", 1.0 if arm != "bridge_off" else 0.0)
        sub.set_attr(policy, "future_manifold_projection_budget", 3.0)
        sub.set_attr(policy, "future_manifold_physical_horizon", 3.0)
        sub.set_attr(episode, "future_manifold_target", world["target"])
        sub.set_attr(episode, "future_manifold_bounds", world["bounds"])
        sub.set_attr(budget, "enabled", 1.0)
        sub.set_attr(budget, "remaining", 3.0)
        sub.set_attr(budget, "refill_per_epoch", 0.0)
        sub.set_attr(budget, "last_refill_epoch", 1.0)
        sub.set_attr(mode, "epoch", 1.0)

        model = world.get("model_input")
        if model is not None and arm == "supplied_path_parity":
            request = sub.add_node("SimulationRequest", {
                "status": "completed", "horizon": 3.0,
                "observation_status": "not_observed",
                "request_kind": "supplied_path_parity"})
            sub.add_edge(root, "has_simulation_request", request)
            sub.add_edge(episode, "has_gwm_request", request)
            transition = sub.add_node("TransitionHypothesis", {
                "future_manifold_supported": True,
                "transition_id": model["transition_id"],
                "model_id": model["model_id"], "model_epoch": model["model_epoch"],
                "future_manifold_values": model["values"],
                "future_manifold_times": model["times"],
                "future_manifold_widths": model["widths"],
                "future_manifold_effort": model["effort"],
                "refinement_requested": False,
            })
            candidate = sub.add_node("CognitionManifoldCandidate", {
                "status": "unprojected", "candidate_kind": "supplied_path",
                "transition_id": model["transition_id"], "model_id": model["model_id"],
                "model_epoch": model["model_epoch"], "owner_id": "agent-root",
                "frame_id": "default", "horizon": 3.0, "uncertainty": 0.0,
                "future_manifold_values": model["values"],
                "future_manifold_times": model["times"],
                "future_manifold_widths": model["widths"],
                "future_manifold_effort": model["effort"],
                "refinement_requested": False, "projection_version": 1,
            })
            sub.add_edge(episode, "has_cognition_manifold_candidate", candidate)
            sub.add_edge(candidate, "projects_transition", transition)
        elif model is not None and arm != "bridge_off":
            request = sub.add_node("SimulationRequest", {"status": "completed",
                "horizon": 3.0, "observation_status": "not_observed"})
            trajectory = sub.add_node("PredictionTrajectory", {})
            state = sub.add_node("PredictedBeliefState", {"uncertainty": 0.0})
            transition = sub.add_node("TransitionHypothesis", {
                "future_manifold_supported": True,
                "transition_id": model["transition_id"],
                "model_id": model["model_id"], "model_epoch": model["model_epoch"],
                "future_manifold_values": model["values"],
                "future_manifold_times": model["times"],
                "future_manifold_widths": model["widths"],
                "future_manifold_effort": model["effort"],
                "refinement_requested": False,
            })
            sub.add_edge(root, "has_simulation_request", request)
            sub.add_edge(request, "has_prediction_trajectory", trajectory)
            sub.add_edge(trajectory, "has_predicted_belief_state", state)
            sub.add_edge(state, "generated_by_transition", transition)

        converged = False
        for _ in range(MAX_RULE_PASSES):
            if not adapter.inner.run_rules(10000):
                converged = True
                break
        candidate_ids = list(sub.neighbours(episode, "has_cognition_manifold_candidate"))
        candidates = [sub.node(n)["attrs"] for n in candidate_ids]
        receipts = []
        false_certified_escape = False
        invalid_receipts = 0
        seen_receipt_ids = set()
        for candidate_id in candidate_ids:
            candidate_attrs = sub.node(candidate_id)["attrs"]
            for receipt_id in sub.neighbours(candidate_id, "has_feasibility_receipt"):
                seen_receipt_ids.add(receipt_id)
                receipt = sub.node(receipt_id)["attrs"]
                transition_ids = list(sub.neighbours(receipt_id, "verifies_transition"))
                valid = (receipt.get("status") == "verified"
                        and receipt.get("verifier_kind") == "native_future_manifold_projection"
                        and candidate_attrs.get("status") == "audited"
                        and candidate_attrs.get("projection_support") == 1.0
                        and candidate_attrs.get("projection_resolved") == 1.0
                        and candidate_attrs.get("projection_loss") == 0.0
                        and candidate_attrs.get("projection_information_loss") == 0.0
                        and candidate_attrs.get("projection_horizon") == candidate_attrs.get("horizon")
                        and receipt.get("model_id") == candidate_attrs.get("model_id")
                        and receipt.get("model_epoch") == candidate_attrs.get("model_epoch")
                        and receipt.get("candidate_version") == candidate_attrs.get("projection_version")
                        and receipt.get("projection_version") == candidate_attrs.get("projection_version")
                        and receipt.get("horizon") == candidate_attrs.get("horizon")
                        and receipt.get("projection_loss") == 0.0
                        and receipt.get("projection_information_loss") == 0.0
                        and candidate_id in sub.neighbours(receipt_id, "verifies_candidate")
                        and receipt_id in sub.neighbours(episode, "has_feasibility_receipt")
                        and len(transition_ids) == 1
                        and sub.node(transition_ids[0])["attrs"].get("future_manifold_supported") is True
                        and sub.node(transition_ids[0])["attrs"].get("model_id") == receipt.get("model_id")
                        and sub.node(transition_ids[0])["attrs"].get("model_epoch") == receipt.get("model_epoch")
                        and sub.node(transition_ids[0])["attrs"].get("transition_id") == receipt.get("transition_id"))
                if valid:
                    receipts.append(receipt)
                    false_certified_escape = false_certified_escape or bool(
                        candidate_attrs.get("projection_loss", 0.0) > 0
                        or candidate_attrs.get("projection_information_loss", 0.0) > 0)
                else:
                    invalid_receipts += 1
        episode_receipt_ids = set(sub.neighbours(episode, "has_feasibility_receipt"))
        invalid_receipts += len(episode_receipt_ids - seen_receipt_ids)
        shapes = [candidate.get("projection_shape") for candidate in candidates]
        requests = [sub.node(n)["attrs"] for n in sub.nodes("ThinkingBudgetRequest")
                    if sub.node(n)["attrs"].get("requester_kind")
                    == "cognition_manifold_refinement"]
        return {"candidate_found": bool(candidates),
                "candidate_count": len(candidates),
                "resolved_candidate_count": sum(
                    candidate.get("projection_resolved") == 1.0 for candidate in candidates),
                "candidate_statuses": [candidate.get("status") for candidate in candidates],
                "projection_shapes": shapes,
                "refinement_request_count": len(requests),
                "funded_refinement_count": sum(request.get("status")
                                                in {"approved", "consumed"}
                                                and request.get("debited_epoch") == 1.0
                                                for request in requests),
                "remaining_budget": sub.node(budget)["attrs"].get("remaining"),
                "episode_status": sub.node(episode)["attrs"].get("status"),
                "feasibility_receipt_count": len(receipts),
                "invalid_feasibility_receipt_count": invalid_receipts,
                "verified_feasible_candidate": None if invalid_receipts else bool(receipts),
                "false_certified_escape": false_certified_escape,
                "timeout": not converged}
    finally:
        adapter.close()


def _d1_episode(seed: int, *, bridge_on: bool, control: str | None = None) -> dict:
    """Run one measured event window through WorldAdapter and funded TimeInfer."""
    import random
    rng = random.Random(seed)
    agent = WorldAdapter(seeds=CORE_SEEDS + ("thinking_budget", "time_axis",
                                              "temporal_escalation"))
    substrate = agent.s
    policy = substrate.nodes("TemporalEscalationPolicy")[0]
    budget = substrate.nodes("ThinkingBudget")[0]
    substrate.set_attr(policy, "enabled", 1.0 if bridge_on else 0.0)
    for key, value in {"enabled": 1.0, "capacity": 4.0, "remaining": 4.0,
                       "refill_per_epoch": 0.0, "last_refill_epoch": 1.0}.items():
        substrate.set_attr(budget, key, value)
    substrate.set_attr(agent.agent, "time_infer_enabled", 0.0)
    for mode in substrate.nodes("NetworkModeState"):
        substrate.set_attr(mode, "epoch", 2.0)
    modes = substrate.nodes("NetworkModeState")
    if not modes:
        mode = substrate.add_node("NetworkModeState", {"epoch": 2.0, "mode": "awake"})
        agent.inner.add_edge_unchecked(agent.agent, "has_network_mode_state", mode)
    frames = _orbit_frames(rng, 7)
    measured_frames = frames[:-1]
    source = substrate.add_node("Observation", {
        "key": f"p4-d1-source:{seed}", "status": "decoded", "dim_checked": 1,
        "dim_explained": 0, "decoded_epoch": 2.0, "dim_types": ["pred", "coord:r", "coord:c", "val"]})
    agent.inner.add_edge_unchecked(agent.agent, "observed", source)
    base_attrs = {"name": f"orbit-base-{seed}", "signature": json.dumps(frames[0]),
                  "kind": "faculty", "faculty": f"orbit-base-{seed}",
                  "dim_types": ["pred", "coord:r", "coord:c", "val"]}
    substrate.add_node("ShapeSignature", base_attrs)
    window_id = f"p4-d1-window-{seed}"
    if control == "no_frame":
        events_added = 0
    else:
        measured = measured_frames
        if control == "shuffled":
            measured = [measured_frames[ix] for ix in (0, 2, 1, 4, 3, 5)]
        for index, frame in enumerate(measured):
            timestamp = index * 10.0
            if control == "irregular" and index == 3:
                timestamp += 3.0
            agent.ingest_temporal_frame_event(
                source, window_id=window_id, event_id=f"{window_id}:event:{index}",
                sequence_index=index, timestamp=timestamp, frame=frame,
                dim_types=["pred", "coord:r", "coord:c", "val"], source_epoch=2.0,
                close_window=index == len(measured) - 1,
                expected_frame_count=len(measured) if index == len(measured) - 1 else None)
            events_added = index + 1
    converged = False
    for _ in range(MAX_RULE_PASSES):
        if not agent.inner.run_rules(10000):
            converged = True
            break
    windows = [node for node in substrate.nodes("TemporalSequenceWindow")
               if substrate.node(node)["attrs"].get("window_id") == window_id]
    requests = [node for node in substrate.nodes("ThinkingBudgetRequest")
                if substrate.node(node)["attrs"].get("requester_kind") == "temporal_escalation"]
    bridges = [node for node in substrate.nodes("Observation")
               if substrate.node(node)["attrs"].get("temporal_bridge")]
    prediction = substrate.node(bridges[0])["attrs"].get("predicted") if bridges else None
    if isinstance(prediction, str):
        try:
            prediction = json.loads(prediction)
        except json.JSONDecodeError:
            pass
    if isinstance(prediction, tuple):
        prediction = list(prediction)
    expected = frames[-1] if control is None else None
    exact = prediction == expected if expected is not None else False
    window_status = substrate.node(windows[0])["attrs"].get("status") if windows else None
    request_states = [substrate.node(node)["attrs"].get("status") for node in requests]
    debited = [substrate.node(node)["attrs"].get("debited_epoch") for node in requests]
    result = {"bridge_enabled": bridge_on, "control": control,
        "window_count": len(windows), "window_status": window_status,
        "events_added": events_added, "bridge_count": len(bridges),
        "prediction": prediction, "expected_next_frame": expected,
        "exact_continuation": exact, "request_count": len(requests),
        "request_states": request_states, "debited_epochs": debited,
        "funded_steps": sum(status == "consumed" for status in request_states),
        "all_debits_epoch_2": all(epoch == 2.0 for epoch in debited),
        "unsupported_exact_claim": control is not None and exact,
        "time_infer_restored": substrate.node(agent.agent)["attrs"].get("time_infer_enabled") == 0.0,
        "timeout": not converged}
    agent.close()
    return result


def run(prereg_hash: str, first: int, end: int, *, development: bool = False) -> dict:
    if not re.fullmatch(r"[0-9a-fA-F]{40,64}", prereg_hash):
        raise ValueError("prereg_hash must be a full 40-64 digit hexadecimal hash")
    first, end = int(first), int(end)
    lo, hi = (1000, 1200) if development else (0, REGISTERED_END)
    if first < lo or end < first or end > hi:
        raise ValueError(f"draw range must satisfy {lo} <= first <= end <= {hi}")
    if not development:
        _verify_registered_freeze(prereg_hash)
    seed = int(prereg_hash[:8], 16)
    parity_rows, control_rows, c5_rows, c5_forced_controls = [], [], [], []
    d1_rows, d1_controls = [], []
    for index in range(first, end):
        # Development streams use their actual 1000+ index in deterministic
        # seed derivation; they never alias registered index 0..199.
        draw_seed_index = index
        parity_rows.append(_stream(seed, draw_seed_index) | {"draw_index": index})
        if (index - first < 100 if development else index < 100):
            control_rows.append(_collision_control(seed, draw_seed_index) |
                                {"draw_index": index})
            c5_forced_controls.append({"draw_index": index,
                "adapter_on": _c5_episode(seed + C5_SALT + index, adapter_on=True,
                                           forced=True),
                "adapter_off": _c5_episode(seed + C5_SALT + index, adapter_on=False,
                                            forced=True)})
        c5_rows.append({"draw_index": index,
            "adapter_on": _c5_episode(seed + C5_SALT + index, adapter_on=True),
            "adapter_off": _c5_episode(seed + C5_SALT + index, adapter_on=False)})
        d1_rows.append({"draw_index": index,
            "bridge_on": _d1_episode(seed + D1_SALT + index, bridge_on=True),
            "bridge_off": _d1_episode(seed + D1_SALT + index, bridge_on=False)})
        if (index - first < 100 if development else index < 100):
            control_kind = ("shuffled", "no_frame", "irregular")[(index - first if development
                                                                   else index) % 3]
            d1_controls.append({"draw_index": index, "control_kind": control_kind,
                "bridge_on": _d1_episode(seed + D1_SALT + index, bridge_on=True,
                                          control=control_kind),
                "bridge_off": _d1_episode(seed + D1_SALT + index, bridge_on=False,
                                           control=control_kind)})
    d5_rows = run_d5_panel(prereg_hash, first, end, development=development)
    e1e2_rows = _e1e2_worlds(prereg_hash, first, end, development=development)
    for row in e1e2_rows:
        row["arms"]["bridge_on"] = _e1e2_arm(row, "bridge_on")
        row["arms"]["bridge_off"] = _e1e2_arm(row, "bridge_off")
        if row.get("model_input") is not None:
            supplied = _e1e2_arm(row, "supplied_path_parity")
            bridge_shapes = row["arms"]["bridge_on"]["projection_shapes"]
            row["arms"]["supplied_path_parity"] = {
                "projection_equal": bool(bridge_shapes)
                    and bridge_shapes == supplied["projection_shapes"],
                "supplied_projection_shapes": supplied["projection_shapes"],
                "bridge_projection_shapes": bridge_shapes,
            }
    d2d3 = {
        "parity_streams": parity_rows,
        "collision_controls": control_rows,
        "summary": {
            "parity_n": len(parity_rows),
            "parity_passes": sum(bool(row["parity"]) for row in parity_rows),
            "collision_n": len(control_rows),
            "collision_passes": sum(bool(row["zero_incompatible_merge"])
                                     for row in control_rows),
            "epochs_auditable": all(row.get("source_epoch") is not None
                                     and row.get("outcome_id") for row in parity_rows),
        },
    }
    return {"protocol": PROTOCOL, "prereg_hash": prereg_hash.lower(),
            "first": first, "end": end, "development_only": development,
            "artifact_sha256": _artifact_hashes(),
            "d2_d3": d2d3,
            "c5": {"hidden_residual_episodes": c5_rows,
                   "forced_frame_controls": c5_forced_controls},
            "d1": {"orbit_sequences": d1_rows, "unsupported_controls": d1_controls},
            "e1_e2": {"model_worlds": e1e2_rows},
            "rows": d5_rows,
            "unestablished_families": {}}


def _self_check() -> None:
    prereg = "1234567890abcdef" * 2 + "12345678"
    report = run(prereg, 1000, 1003, development=True)
    assert report["development_only"] is True
    assert report["first"] == 1000 and report["end"] == 1003
    assert report["d2_d3"]["summary"]["parity_n"] == 3
    assert report["d2_d3"]["summary"]["parity_passes"] == 3
    assert report["d2_d3"]["parity_streams"][0]["outcome_id"] == "verified-outcome-1000"
    assert report["d2_d3"]["summary"]["collision_n"] == 3
    assert report["d2_d3"]["summary"]["collision_passes"] == 3
    assert not any(row.get("timeout") for row in report["d2_d3"]["parity_streams"])
    assert len(report["c5"]["hidden_residual_episodes"]) == 3
    assert all((row["adapter_on"]["same_epoch_debit"]
                if row["adapter_on"]["probe_projected"] else True)
               and not row["adapter_on"]["unfunded_probe"]
               and not row["adapter_on"]["timeout"]
               for row in report["c5"]["hidden_residual_episodes"])
    assert len(report["c5"]["forced_frame_controls"]) == 3
    assert not any(row[arm]["forced_frame_changed"]
                   for row in report["c5"]["forced_frame_controls"]
                   for arm in ("adapter_on", "adapter_off"))
    assert len(report["d1"]["orbit_sequences"]) == 3
    assert all(row["bridge_on"]["exact_continuation"]
               and row["bridge_on"]["funded_steps"] == 1
               and row["bridge_on"]["time_infer_restored"]
               and not row["bridge_on"]["timeout"]
               for row in report["d1"]["orbit_sequences"])
    assert len(report["d1"]["unsupported_controls"]) == 3
    assert {row["control_kind"] for row in report["d1"]["unsupported_controls"]} == {
        "shuffled", "no_frame", "irregular"}
    assert all(not row[arm]["unsupported_exact_claim"]
               for row in report["d1"]["unsupported_controls"]
               for arm in ("bridge_on", "bridge_off"))
    d5_targets = [row for row in report["rows"] if row["case_kind"] == "target"]
    assert d5_targets and all(row["arms"]["recall_on"]["selected_candidate"]
                              for row in d5_targets)
    assert all(row["arms"]["recall_on"]["exact_candidate_checks"] == 1
               and row["arms"]["recall_off"]["exact_candidate_checks"] == 2
               for row in d5_targets)
    assert all(row["arms"]["mismatched_source"]["selected_candidate"] is None
               for row in d5_targets)
    assert len(report["rows"]) == 12
    assert all(all(isinstance(value, dict) for value in row["arms"].values())
               for row in report["rows"])
    assert all(row["arms"]["recall_on"]["selected_candidate"] is None
               for row in report["rows"] if row["case_kind"] == "incompatible_decoy")
    assert len(report["e1_e2"]["model_worlds"]) == 3
    assert all(isinstance(row["arms"]["bridge_on"], dict)
               and isinstance(row["arms"]["bridge_off"], dict)
               for row in report["e1_e2"]["model_worlds"])
    assert all((row["arms"]["supplied_path_parity"] is None)
               == (row["model_input"] is None)
               for row in report["e1_e2"]["model_worlds"])
    assert all(row["arms"]["bridge_on"]["resolved_candidate_count"]
               == int(row["model_input"] is not None)
               and not row["arms"]["bridge_on"]["timeout"]
               and (row["arms"]["supplied_path_parity"] is None
                    or row["arms"]["supplied_path_parity"]["projection_equal"])
               for row in report["e1_e2"]["model_worlds"])
    development_worlds = _e1e2_worlds(prereg, 1000, 1200, development=True)
    assert {kind: sum(w["world_kind"] == kind for w in development_worlds)
            for kind in ("feasible", "infeasible", "missing_model")} == {
                "feasible": 80, "infeasible": 60, "missing_model": 60}
    missing = next(world for world in development_worlds
                   if world["world_kind"] == "missing_model")
    assert _e1e2_arm(missing, "bridge_on")["candidate_count"] == 0
    infeasible = next(world for world in development_worlds
                      if world["world_kind"] == "infeasible")
    infeasible_result = _e1e2_arm(infeasible, "bridge_on")
    assert infeasible_result["candidate_found"]
    assert infeasible_result["verified_feasible_candidate"] is False
    assert infeasible_result["feasibility_receipt_count"] == 0
    assert infeasible_result["false_certified_escape"] is False
    assert report["unestablished_families"] == {}
    assert all(isinstance(outcome, dict) for row in report["rows"]
               for outcome in row["arms"].values())
    try:
        _verify_registered_freeze("0" * 40)
    except ValueError:
        pass
    else:
        raise AssertionError("registered freeze guard accepted an unfrozen commit")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--self-check"]:
        _self_check()
        print("cognition_p4_heldout_v1 self-check passed (development-only)")
        return
    if len(argv) != 3:
        raise SystemExit("usage: cognition_p4_heldout_v1.py <prereg_hash> <first> <end> | --self-check")
    prereg_hash, first, end = argv[0], int(argv[1]), int(argv[2])
    report = run(prereg_hash, first, end)
    out_dir = ROOT / "evaluation" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"cognition_p4_heldout_v1_{prereg_hash[:8]}_d{first}-{end}.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
