"""Named connected-seed profiles for bounded substrate boot.

Profiles are explicit anchor sets, not a second manifest inventory: the
    content/dependency closure, source validation, ordering, and incomplete-closure
    behavior remain owned by :mod:`substrate.boot_all`'s cached pre-pass.
"""
from __future__ import annotations

import os

from substrate.boot_core import CORE_SEEDS


# Anchors used by the current eight-event conversational production profile.
# `CORE_SEEDS` is included by the helper; these IDs name the communication,
# comprehension, grounding, repair, and self-model faculties exercised by that
# profile. Closure providers are resolved from the live seed index, never
# copied into this list.
CONVERSATION_SEED_ANCHORS = frozenset({
    "communication_causal_retrieval",
    "communication_causal_identity_binding",
    "communication_causal_evidence_promotion",
    "communication_correction_reply",
    "communication_intent_arbitration",
    "communication_reported_content_recall",
    "communication_standalone_assertion_reply",
    "communication_social_reply",
    "comprehend_instruction",
    "composer_dispatch",
    "conversation_attachment_reply",
    "conversation_attachment_route",
    "conversation_capability_reply",
    "conversation_capability_route",
    "conversation_deliberation_phase4a",
    "conversation_elaborate",
    "conversation_grice",
    "conversation_honest_floor",
    "conversation_reply",
    "conversation_reply_flag",
    "conversation_self_concern",
    "conversation_self_reply",
    "conversation_steering",
    "conversation_topic_reply",
    "conversation_topic_route",
    "conversation_topic_span",
    "conversation_topic_tracking",
    "first_person_routing",
    "gap_awareness",
    "inference_affordances",
    "instruction_understanding",
    "interlocutor_shapes",
    "interlocutor_trust",
    "minting_recurrence_ledger",
    "conceptualizer",
    "self_processes",
    "speech_act_classify",
    "topic_search",
    "topic_search_verify",
    "topic_sync_ground",
    "wordnet_common_objects",
})

# SELF-IMPROVEMENT anchors (tranche 21). The production daemon boots this
# profile; without these the agent could file gaps but its own promotion, the
# variation repertoire, the experiment judges, the retry policy, the adoption
# regression veto and the integrity list were absent (reflective_faculty
# lazily loaded only some of them, and adoption_safety never). Endemic
# recursive self-improvement (tranche 20) must run in the profile production
# actually uses.
CONVERSATION_SELF_IMPROVEMENT_ANCHORS = frozenset({
    "improvement_integrity",
    "self_promotion",
    "variation_ops",
    "instruction_repair_retry",
    "adoption_safety",
    "self_optimisation",
    "conversation_experiment",
    # the agent's own comprehension self-observation (latency, recurring
    # shallow/deep-reader divergence): a natural concern supply
    "comprehension_health",
    # tranche 22: the agent's own recurring unanswered turns as concerns
    "unanswered_gap",
    # plan P2: the agent's own bad replies (production ReplyQuality, the
    # interlocutor's next-turn repair / rejection / repeat) as concerns
    "reply_feedback_gap",
    # plan P4: variation families as held Programs (VariationOp.builder_program)
    "family_programs",
    # plan P5: operator authorship (propose-only): the mutation grammar over
    # the held FamilyPrograms and the frozen qualification rule
    "operator_authorship",
    # plan P6: criterion proposals (human-only adoption)
    "criterion_proposals",
})
# 2026-10-10: the English vocabulary base the POS faculty types otherwise
# untyped tokens from (contractions, interjections; any word when the POS slab
# is absent) -- seeds/vocabulary_base_en.json
CONVERSATION_SEED_ANCHORS = CONVERSATION_SEED_ANCHORS | frozenset({"vocabulary_base_en"})
CONVERSATION_SEED_ANCHORS = CONVERSATION_SEED_ANCHORS | CONVERSATION_SELF_IMPROVEMENT_ANCHORS

# Runtime modules observed in the fixed production-shaped conversation profile.
# Importing this group at profile boot moves its one-time import cost out of the
# first user turn; these are runtime dependencies, not additional seed content.
# Optional code/curriculum self-account modules are intentionally absent unless
# their seed family is in the selected closure (boot_all handles that boundary).
CONVERSATION_RUNTIME_MODULES = (
    "domains.abs_learned_fusion",
    "domains.analysis_by_synthesis",
    "domains.ast_to_term",
    "domains.audience",
    "domains.audience_adaptation",
    "domains.audience_driven_production",
    "domains.audience_misjudgment",
    "domains.code_reading",
    "domains.code_write_growth",
    "domains.code_writing",
    "domains.collapse_model",
    "domains.commitment_gate",
    "domains.comprehend_question",
    "domains.comprehend_text",
    "domains.concept_graph",
    "domains.conceptualizer",
    "domains.context_collapse_plug",
    "domains.context_model",
    "domains.context_prior_speaker",
    "domains.conversation_action",
    "domains.conversation_deliberation",
    "domains.dataset_root",
    "domains.discourse_state",
    "domains.earned_augmentation",
    "domains.fetch_dispatch",
    "domains.forward_segmentation",
    "domains.frame",
    "domains.frozen_core",
    "domains.function_word_reference",
    "domains.future_option_risk",
    "domains.glyph_motor_world",
    "domains.imagination",
    "domains.information_commitment",
    "domains.instruction_reading",
    "domains.interlocutor_collapse_plug",
    "domains.interlocutor_model",
    "domains.language",
    "domains.language_world",
    "domains.language_faculty_ops",
    "domains.learning_safety",
    "domains.many_settings_recognizer",
    "domains.morphology_reference",
    "domains.native_fusion",
    "domains.omniglot_world",
    "domains.pragmatic_speaker",
    "domains.preposition_roles",
    "domains.production_gate",
    "domains.proposal_install",
    "domains.reading_collapse",
    "domains.reference_resolution",
    "domains.reference_slab",
    "domains.runtime_design",
    "domains.scattering_feature",
    "domains.seed_registry",
    "domains.self_extend",
    "domains.self_extend_rust",
    "domains.self_modification",
    "domains.self_organisation_reader",
    "domains.sense_of_reference",
    "domains.shape_tube",
    "domains.system_model",
    "domains.teach",
    "domains.topic_grounding",
    "domains.upload_text_read",
    "domains.wiktionary_reference",
    "domains.wordnet_membership",
    "domains.wordplay",
)


def _prewarm_conversation_runtime() -> tuple[str, ...]:
    """Load the profile's connected runtime module group before its first turn."""
    from importlib import import_module

    for module_name in CONVERSATION_RUNTIME_MODULES:
        import_module(module_name)
    return CONVERSATION_RUNTIME_MODULES


def load_conversation_seed_profile(agent, seed_dir=None, *, content_keys=(),
                                   content_candidates=None,
                                   scoped_content_refs=None,
                                   content_prepass_manifest_digest=None,
                                   incremental_content_loading=True) -> dict:
    """Load the connected conversation profile onto an otherwise empty agent.

    This is an opt-in bounded profile, not a replacement for general full boot.
    Use ``WorldAdapter(seeds=())`` so core seeds are installed once through the
    same indexed loader. Optional ``content_candidates`` are lexical/content
    candidates supplied by an upstream evidence producer and resolved against
    the cached provider map in the loader pre-pass. Unknown candidates are
    recorded but do not invalidate the connected closure. Explicit
    ``content_keys`` remain strict exact keys. Only seeds
    explicitly marked ``selective_content_keys`` are sliced to those nodes.
    The report exposes the exact selected closure and any unresolved refs; an
    incomplete selection is rejected before graph mutation by ``load_all_seeds``.
    Set ``incremental_content_loading=False`` when ``content_candidates`` is a
    complete pre-boot candidate set: connected seed groups are loaded before
    the first turn, and later out-of-set terms are reported without loading
    additional manifests.
    """
    from substrate.boot_all import (
        _release_seed_selection_caches,
        load_all_seeds,
    )
    from substrate.seed_loader import SEED_DIR

    report = load_all_seeds(
        agent,
        seed_dir,
        seed_ids=set(CORE_SEEDS) | CONVERSATION_SEED_ANCHORS,
        content_keys=content_keys,
        content_candidates=content_candidates,
        scoped_content_refs=scoped_content_refs,
    )
    if report.get("selection_complete") and not report.get("failed"):
        report["runtime_modules_warmed"] = list(_prewarm_conversation_runtime())
        resolution = (report.get("selection") or {}).get(
            "content_candidate_resolution") or {}
        graph_provider_seed_ids_by_ref = {}
        for seed_id, slice_report in (
                report.get("content_slices") or {}).items():
            for ref in slice_report.get("requested_refs") or ():
                if not isinstance(ref, dict):
                    continue
                key = f"{ref.get('type')}:{ref.get('name')}"
                graph_provider_seed_ids_by_ref.setdefault(key, set()).add(
                    str(seed_id))
        agent._conversation_seed_profile_state = {
            "seed_dir": str(seed_dir or SEED_DIR),
            "loaded_seed_ids": set(report.get("loaded_seed_ids") or ()),
            "loaded_content_by_seed": {
                str(sid): set(keys)
                for sid, keys in (report.get(
                    "loaded_content_keys_by_seed") or {}).items()
            },
            "loaded_typed_content_by_seed": {
                str(sid): {
                    (str(ref.get("type")), str(ref.get("name")))
                    for ref in (slice_report.get("requested_refs") or ())
                    if isinstance(ref, dict)
                }
                for sid, slice_report in (
                    report.get("content_slices") or {}).items()
            },
            "loaded_content_keys": set(resolution.get("content_keys") or ())
            | {str(key) for key in content_keys},
            "known_unprovided_candidates": set(
                resolution.get("unresolved_candidates") or ()),
            "provider_seed_ids_by_key": {
                str(key): list(seed_ids)
                for key, seed_ids in resolution.get(
                    "provider_seed_ids_by_key", {}).items()
            },
            "graph_provider_seed_ids_by_ref": {
                key: sorted(seed_ids)
                for key, seed_ids in graph_provider_seed_ids_by_ref.items()
            },
            "selective_seed_ids": set(
                report.get("selective_seed_ids") or ())
            | set((report.get("content_slices") or {}).keys()),
            "incremental_content_loading": bool(
                incremental_content_loading),
            "content_prepass_manifest_digest": (
                str(content_prepass_manifest_digest)
                if content_prepass_manifest_digest else None),
            "prepass_reports": [],
        }
        route_seed_ids = {
            "comprehend_instruction", "conversation_self_concern",
            "conversation_self_reply",
        }
        # Selective slices retain instruction-route Concepts as runtime
        # vocabulary. The adapter's first-turn repair path need not reread
        # these manifests after a complete connected prepass.
        agent._conversation_route_concepts_preloaded = route_seed_ids.issubset(
            set(report.get("loaded_seed_ids") or ()))
        if not incremental_content_loading:
            _release_seed_selection_caches(str(seed_dir or SEED_DIR))
    return report


def load_conversation_content_candidates(agent, candidates) -> dict | None:
    """Incrementally load provider-backed candidates before a live turn.

    The existing message-boundary tokenizer supplies candidates. This helper
    only translates them into indexed seed providers and their declared
    dependency closure; it makes no referent, route, or response decision.
    Previously installed seeds are reused only when their graph-resident
    ``SeedSummary`` proves successful installation. Selective providers may be
    revisited with only the newly requested names.
    """
    from substrate.boot_all import (
        _CONVERSATION_INCREMENTAL_LOAD_TOKEN,
        _SEED_INDEX_SOURCE_DIGEST,
        _compact_incremental_seed_index,
        _release_seed_index_memory_cache,
        _seed_manifest_paths,
        _seed_sources_stat_snapshot,
        _read_seed_index,
        load_all_seeds,
        resolve_seed_content_candidates,
    )

    state = getattr(agent, "_conversation_seed_profile_state", None)
    if not isinstance(state, dict):
        return None
    requested_candidates = sorted({
        str(raw) for raw in candidates or () if str(raw)
    })
    if not state.get("incremental_content_loading", True):
        provider_map = state.get("provider_seed_ids_by_key") or {}
        loaded_by_seed = state.get("loaded_content_by_seed") or {}
        unavailable = [
            key for key in requested_candidates
            if key not in provider_map
            or any(key not in set(loaded_by_seed.get(str(seed_id), ()))
                   for seed_id in provider_map.get(key, ()))
        ]
        result = {
            "status": ("preload_only_unavailable" if unavailable
                       else "already_available"),
            "candidates": requested_candidates,
            "not_preloaded": unavailable,
            "seed_loading_performed": False,
        }
        state["prepass_reports"] = (
            state.get("prepass_reports", []) + [result])[-8:]
        return result
    known_unprovided = set(state.get("known_unprovided_candidates") or ())
    # Incremental profiles only need provider mappings for this turn. Keeping
    # every lexical candidate ever seen duplicates the process-wide validated
    # connectivity index and makes agent memory grow with conversation length.
    # Sealed profiles retain their complete map above because they cannot
    # resolve future candidates.
    provider_map = state.setdefault("provider_seed_ids_by_key", {})
    candidates_to_resolve = []
    for raw in candidates or ():
        key = str(raw)
        if (not key or key in known_unprovided
                or key in provider_map):
            continue
        candidates_to_resolve.append(key)
    seed_dir = str(state["seed_dir"])
    index = {}
    index_snapshot = state.get("seed_index_snapshot")
    if candidates_to_resolve:
        current_paths = _seed_manifest_paths(seed_dir)
        current_stat = _seed_sources_stat_snapshot(current_paths)
        cached_stat = state.get("seed_index_stat_snapshot")
        if (index_snapshot is None or current_stat is None
                or current_stat != cached_stat):
            index, paths = _read_seed_index(seed_dir)
            current_digest = _SEED_INDEX_SOURCE_DIGEST.get(
                os.path.realpath(seed_dir))
            index_snapshot = ((index, paths, current_digest)
                              if current_digest is not None else None)
            state["seed_index_snapshot"] = index_snapshot
            state["seed_index_stat_snapshot"] = (
                _seed_sources_stat_snapshot(_seed_manifest_paths(seed_dir))
                if index_snapshot is not None else None)
        else:
            index, paths, _digest = index_snapshot
        resolution = resolve_seed_content_candidates(
            index, candidates_to_resolve, seed_dir=seed_dir)
        state.setdefault("selective_seed_ids", set()).update(
            seed_id for seed_id, meta in index.items()
            if meta.get("selective_content_keys"))
        if index_snapshot is not None:
            compact_index = _compact_incremental_seed_index(index)
            index_snapshot = (compact_index, paths, index_snapshot[2])
            state["seed_index_snapshot"] = index_snapshot
            _release_seed_index_memory_cache(seed_dir)
    else:
        if index_snapshot is not None:
            index, paths, _digest = index_snapshot
        resolution = {
            "candidates": [], "content_keys": [],
            "unresolved_candidates": [], "provider_seed_ids": [],
            "provider_seed_ids_by_key": {},
        }
    known_unprovided.update(resolution["unresolved_candidates"])
    state["known_unprovided_candidates"] = known_unprovided
    provider_map.update(resolution.get("provider_seed_ids_by_key") or {})

    # Include cached provider mappings as well as newly resolved ones. Existing
    # graph concepts alone are insufficient: the full profile can legitimately
    # contain same-named content from multiple providers, all of which must be
    # loaded to preserve the profile's observable provider inventory.
    candidate_keys = sorted({
        str(raw) for raw in candidates or ()
        if str(raw) in provider_map and str(raw) not in known_unprovided
    })
    state["provider_seed_ids_by_key"] = {
        key: provider_map[key] for key in candidate_keys
    }
    loaded_by_seed = {
        str(sid): set(keys)
        for sid, keys in (state.get("loaded_content_by_seed") or {}).items()
    }
    pending = [
        key for key in candidate_keys
        if any(key not in loaded_by_seed.get(seed_id, set())
               for seed_id in provider_map[key])
    ]
    if not pending:
        state.setdefault("loaded_content_keys", set()).update(candidate_keys)
        unavailable = sorted(set(requested_candidates) & known_unprovided)
        return {
            "status": "unavailable" if unavailable else "already_available",
            "candidates": candidate_keys,
            "not_preloaded": unavailable,
            "seed_loading_performed": False,
        }
    loaded = set(state.get("loaded_seed_ids") or ())
    # A selective seed is intentionally re-opened for its newly requested
    # nodes. Other already installed seeds are skipped only through the
    # loader's verified-preload path, not the user-controlled `skip` argument.
    selective_seed_ids = set(state.get("selective_seed_ids") or ())
    reopen = {
        seed_id for key in pending for seed_id in provider_map[key]
        if key not in loaded_by_seed.get(seed_id, set())
        if seed_id in selective_seed_ids
    }
    preloaded = loaded - reopen
    report = load_all_seeds(
        agent,
        seed_dir,
        content_candidates=pending,
        _preloaded_seed_ids=preloaded,
        _profile_token=_CONVERSATION_INCREMENTAL_LOAD_TOKEN,
        **({"_seed_index_snapshot": index_snapshot}
           if index_snapshot is not None else {}),
    )
    result = {
        "status": ("loaded" if report.get("selection_complete")
                   and not report.get("failed") else "incomplete"),
        "candidate_resolution": resolution,
        "selected_seed_ids": (report.get("selection") or {}).get(
            "selected_seed_ids", []),
        "loaded_seed_ids": report.get("loaded_seed_ids", []),
        "selection_complete": report.get("selection_complete"),
        "failed": list(report.get("failed") or ()),
        "refused_skips": list(report.get("refused_skips") or ()),
    }
    if result["status"] == "loaded":
        state["loaded_seed_ids"].update(result["loaded_seed_ids"])
        for sid, keys in (report.get("loaded_content_keys_by_seed") or {}).items():
            loaded_by_seed.setdefault(str(sid), set()).update(keys)
        state["loaded_content_by_seed"] = loaded_by_seed
        loaded_typed = state.setdefault("loaded_typed_content_by_seed", {})
        for sid, slice_report in (report.get("content_slices") or {}).items():
            loaded_typed.setdefault(str(sid), set()).update(
                (str(ref.get("type")), str(ref.get("name")))
                for ref in (slice_report.get("requested_refs") or ())
                if isinstance(ref, dict))
        state.setdefault("loaded_content_keys", set()).update(pending)
        state.setdefault("selective_seed_ids", set()).update(
            (report.get("content_slices") or {}).keys())
    state["prepass_reports"] = (
        state.get("prepass_reports", []) + [result])[-8:]
    return result


def load_conversation_graph_content_refs(agent, graph_evidence) -> dict | None:
    """Load providers for already graph-resolved typed content references.

    ``graph_evidence`` supplies ``refs`` and direct ``graph_connections``
    already read from the live graph. This is not a surface-token API: refs
    and edges are checked against graph state, and ambiguous or unprovided
    references fail before seed mutation.
    """
    from collections.abc import Mapping
    from substrate.boot_all import (
        _CONVERSATION_INCREMENTAL_LOAD_TOKEN,
        _SEED_INDEX_SOURCE_DIGEST,
        _compact_incremental_seed_index,
        _release_seed_index_memory_cache,
        _seed_manifest_paths,
        _seed_sources_stat_snapshot,
        _read_seed_index,
        load_all_seeds,
        resolve_graph_content_refs,
    )

    state = getattr(agent, "_conversation_seed_profile_state", None)
    if not isinstance(state, dict):
        return None
    if not isinstance(graph_evidence, Mapping):
        raise TypeError("graph content evidence must be a mapping")
    graph_refs = graph_evidence.get("refs") or ()
    if not isinstance(graph_refs, (list, tuple)):
        raise TypeError("graph content refs must be a sequence")
    # Treat the supplied mapping as a requested readback, not authority. Every
    # typed ref and connection must already exist in the live graph before it
    # can scope seed selection.
    graph_nodes = {}
    missing_graph_refs = []
    for row in graph_refs:
        if not isinstance(row, Mapping):
            missing_graph_refs.append({"ref": row})
            continue
        node_type, name = row.get("type"), row.get("name")
        matches = [node for node in agent.s.nodes(str(node_type or ""))
                   if agent.s.node(node)["attrs"].get("name") == name]
        if not isinstance(node_type, str) or not isinstance(name, str) or not matches:
            missing_graph_refs.append({"ref": dict(row)})
            continue
        graph_nodes[(node_type, name)] = matches
    verified_connections = []
    for row in graph_evidence.get("graph_connections") or ():
        if not isinstance(row, Mapping):
            missing_graph_refs.append({"connection": row})
            continue
        source, target, edge_type = row.get("src"), row.get("tgt"), row.get("edge")
        if not isinstance(source, Mapping) or not isinstance(target, Mapping):
            missing_graph_refs.append({"connection": dict(row)})
            continue
        source_signature = (source.get("type"), source.get("name"))
        target_signature = (target.get("type"), target.get("name"))
        if (not all(isinstance(value, str) and value
                    for value in source_signature + target_signature)
                or not isinstance(edge_type, str) or not edge_type):
            missing_graph_refs.append({"connection": dict(row)})
            continue
        source_nodes = graph_nodes.get(source_signature, ())
        target_nodes = set(graph_nodes.get(target_signature, ()))
        if not any(target_node in agent.inner.neighbours(source_node, edge_type)
                   for source_node in source_nodes
                   for target_node in target_nodes):
            missing_graph_refs.append({"connection": dict(row)})
            continue
        verified_connections.append(dict(row))
    if missing_graph_refs:
        result = {
            "status": "graph_refs_unresolved",
            "graph_content_resolution": {
                "missing_graph_refs": missing_graph_refs,
                "ambiguous_graph_refs": [],
                "invalid_graph_providers": [],
                "unprovided_graph_refs": [],
            },
            "loaded_seed_ids": [],
            "seed_loading_performed": False,
        }
        state["prepass_reports"] = (
            state.get("prepass_reports", []) + [result])[-8:]
        return result
    seed_dir = str(state["seed_dir"])
    loaded = set(state.get("loaded_seed_ids") or ())
    loaded_by_seed = {
        str(seed_id): set(names)
        for seed_id, names in (state.get("loaded_content_by_seed") or {}).items()
    }
    selective_seed_ids = set(state.get("selective_seed_ids") or ())
    loaded_typed_by_seed = {
        str(seed_id): set(tuple(ref) for ref in refs)
        for seed_id, refs in (
            state.get("loaded_typed_content_by_seed") or {}).items()
    }

    if not state.get("incremental_content_loading", True):
        graph_provider_map = state.get("graph_provider_seed_ids_by_ref") or {}
        lexical_provider_map = state.get("provider_seed_ids_by_key") or {}
        unresolved = []
        for row in graph_refs:
            if not isinstance(row, Mapping):
                unresolved.append(row)
                continue
            node_type, name = str(row.get("type")), str(row.get("name"))
            providers = (set(graph_provider_map.get(
                f"{node_type}:{name}", ()))
                | set(lexical_provider_map.get(name, ()))
            )
            available = any(
                seed_id in loaded
                and name in loaded_by_seed.get(seed_id, set())
                and (seed_id not in selective_seed_ids
                     or (node_type, name) in loaded_typed_by_seed.get(
                         seed_id, set()))
                for seed_id in providers)
            if not available:
                unresolved.append(row)
        result = {
            "status": ("preload_only_unavailable" if unresolved
                       else "already_available"),
            "refs": list(graph_refs), "not_preloaded": unresolved,
            "seed_loading_performed": False,
        }
        state["prepass_reports"] = (
            state.get("prepass_reports", []) + [result])[-8:]
        return result

    index_snapshot = state.get("seed_index_snapshot")
    current_paths = _seed_manifest_paths(seed_dir)
    current_stat = _seed_sources_stat_snapshot(current_paths)
    cached_stat = state.get("seed_index_stat_snapshot")
    if (index_snapshot is None or current_stat is None
            or current_stat != cached_stat):
        index, paths = _read_seed_index(seed_dir)
        current_digest = _SEED_INDEX_SOURCE_DIGEST.get(
            os.path.realpath(seed_dir))
        index_snapshot = ((index, paths, current_digest)
                          if current_digest is not None else None)
        state["seed_index_snapshot"] = index_snapshot
        state["seed_index_stat_snapshot"] = (
            _seed_sources_stat_snapshot(_seed_manifest_paths(seed_dir))
            if index_snapshot is not None else None)
    else:
        index, paths, _digest = index_snapshot

    if graph_evidence.get("derive_declared_connections"):
        refs_by_signature = {
            (str(row["type"]), str(row["name"]))
            for row in graph_refs if isinstance(row, Mapping)
            and isinstance(row.get("type"), str)
            and isinstance(row.get("name"), str)
        }
        declared_connections = set()
        for seed_meta in index.values():
            for connection in seed_meta.get("content_connections", ()):
                if not isinstance(connection, Mapping):
                    continue
                source, target = connection.get("src"), connection.get("tgt")
                edge_type = connection.get("edge")
                if not isinstance(source, Mapping) or not isinstance(target, Mapping):
                    continue
                source_sig = (source.get("type"), source.get("name"))
                target_sig = (target.get("type"), target.get("name"))
                if (source_sig not in refs_by_signature
                        or target_sig not in refs_by_signature
                        or not isinstance(edge_type, str)):
                    continue
                source_nodes = graph_nodes.get(source_sig, ())
                target_nodes = set(graph_nodes.get(target_sig, ()))
                if any(target_node in agent.inner.neighbours(source_node, edge_type)
                       for source_node in source_nodes
                       for target_node in target_nodes):
                    declared_connections.add((source_sig, edge_type, target_sig))
        verified_connections.extend({
            "src": {"type": source[0], "name": source[1]},
            "edge": edge_type,
            "tgt": {"type": target[0], "name": target[1]},
        } for source, edge_type, target in sorted(declared_connections))

    scoped, unresolved = resolve_graph_content_refs(
        graph_refs,
        seed_index=index,
        graph_connections=verified_connections,
    )
    if any(unresolved.values()):
        result = {
            "status": "graph_refs_unresolved",
            "graph_content_resolution": unresolved,
            "loaded_seed_ids": [],
            "seed_loading_performed": False,
        }
        state["prepass_reports"] = (
            state.get("prepass_reports", []) + [result])[-8:]
        return result

    loaded_refs = {
        str(seed_id): [
            dict(ref) for ref in refs
            if (ref.get("name") not in loaded_by_seed.get(
                    str(seed_id), set())
                or (str(seed_id) in selective_seed_ids
                    and (str(ref.get("type")), str(ref.get("name")))
                    not in loaded_typed_by_seed.get(str(seed_id), set())))
        ]
        for seed_id, refs in scoped.items()
    }
    loaded_refs = {seed_id: refs for seed_id, refs in loaded_refs.items() if refs}
    if not loaded_refs:
        result = {
            "status": "already_available", "scoped_content_refs": scoped,
            "selected_seed_ids": [], "loaded_seed_ids": [],
            "seed_loading_performed": False,
        }
    else:
        reopen = {
            seed_id for seed_id in loaded_refs
            if seed_id in selective_seed_ids
        }
        report = load_all_seeds(
            agent, seed_dir, scoped_content_refs=loaded_refs,
            _preloaded_seed_ids=loaded - reopen,
            _profile_token=_CONVERSATION_INCREMENTAL_LOAD_TOKEN,
            **({"_seed_index_snapshot": index_snapshot}
               if index_snapshot is not None else {}),
        )
        result = {
            "status": ("loaded" if report.get("selection_complete")
                       and not report.get("failed") else "incomplete"),
            "graph_content_resolution": unresolved,
            "scoped_content_refs": scoped,
            "selected_seed_ids": (report.get("selection") or {}).get(
                "selected_seed_ids", []),
            "loaded_seed_ids": report.get("loaded_seed_ids", []),
            "selection_complete": report.get("selection_complete"),
            "failed": list(report.get("failed") or ()),
            "refused_skips": list(report.get("refused_skips") or ()),
            "seed_loading_performed": bool(report.get("loaded")),
        }
        if result["status"] == "loaded":
            loaded.update(result["loaded_seed_ids"])
            for seed_id, names in (report.get(
                    "loaded_content_keys_by_seed") or {}).items():
                loaded_by_seed.setdefault(str(seed_id), set()).update(names)
            state["loaded_seed_ids"] = loaded
            state["loaded_content_by_seed"] = loaded_by_seed
            loaded_typed = state.setdefault("loaded_typed_content_by_seed", {})
            for seed_id, slice_report in (
                    report.get("content_slices") or {}).items():
                loaded_typed.setdefault(str(seed_id), set()).update(
                    (str(ref.get("type")), str(ref.get("name")))
                    for ref in (slice_report.get("requested_refs") or ())
                    if isinstance(ref, dict))
            state.setdefault("selective_seed_ids", set()).update(
                (report.get("content_slices") or {}).keys())
        if index_snapshot is not None:
            index_snapshot = (
                _compact_incremental_seed_index(index), paths,
                index_snapshot[2])
            state["seed_index_snapshot"] = index_snapshot
            _release_seed_index_memory_cache(seed_dir)

    if result["status"] in {"loaded", "already_available"}:
        graph_provider_map = state.setdefault(
            "graph_provider_seed_ids_by_ref", {})
        for seed_id, refs in scoped.items():
            for ref in refs:
                key = f"{ref['type']}:{ref['name']}"
                graph_provider_map[key] = sorted(
                    set(graph_provider_map.get(key, ())) | {seed_id})
    state["prepass_reports"] = (
        state.get("prepass_reports", []) + [result])[-8:]
    return result


def prepass_conversation_turn(
        agent, text: str, *, graph_content_evidence=None) -> dict | None:
    """Resolve turn content before parsing through the connected seed index.

    A supplied graph readback takes precedence over token matching. Without it,
    the legacy lexical candidate path remains available. This is mechanical
    preparation only and is a no-op for full-profile agents.
    """
    if not isinstance(
            getattr(agent, "_conversation_seed_profile_state", None), dict):
        return None
    if graph_content_evidence is not None:
        return load_conversation_graph_content_refs(
            agent, graph_content_evidence)
    candidates = agent.lexical_candidates(str(text or ""))
    return load_conversation_content_candidates(agent, candidates)


__all__ = ["CONVERSATION_RUNTIME_MODULES", "CONVERSATION_SEED_ANCHORS",
           "load_conversation_content_candidates",
           "load_conversation_graph_content_refs",
           "load_conversation_seed_profile", "prepass_conversation_turn"]
