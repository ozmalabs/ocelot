"""Episode-scoped aperture residual ingestion for graph-native minting recurrence.

Python computes the trajectory's residual evidence and reads the result.  The graph
owns candidate identity, accumulated predicate counts, threshold comparison, the
once-only offer, terminal record, and the only path that can mint an axis.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable, Optional

from domains import analogy_search as asr
from domains import reflective_faculty as rf
from domains import regulated_train_of_thought as rtot
from domains import self_dialogue as sd
from domains import train_of_thought as tot


def _residual_tuples(wa, reached: Iterable[str], admitted: frozenset, observer) -> frozenset:
    """Read the aperture residual as immutable `(dimension, predicate, k)` evidence."""
    sub = sd._sub(wa)
    traj: set = set()
    for concept in reached:
        if concept:
            node = sd._find_concept(sub, concept)
            if node is not None:
                traj |= set(asr.concept_signature(sub, node, observer=observer))
    return frozenset(traj) - admitted


def _residual_predicates(residual: frozenset) -> list[str]:
    """Project one segment's tuple evidence to the locked predicate-only identity."""
    return sorted({t[1] for t in residual
                   if isinstance(t, tuple) and len(t) >= 2 and isinstance(t[1], str)})


def _open_episode(wa, *, mint_after_quanta: int, setpoint_observer, topic: str):
    """Mechanically create one graph-resident recurrence scope for this invocation."""
    sub, native, agent = rf._resolve_agent(wa)
    rf._ensure_shape_decode_loop(sub, native, agent)
    episode = sub.add_node("MintingRecurrenceEpisode", {
        "mint_after_quanta": max(1, int(mint_after_quanta)),
        "integer_native": 1,
        "setpoint_topic": topic,
        "setpoint_observer": str(setpoint_observer),
    })
    if agent is not None:
        sub.add_edge(agent, "has_minting_recurrence_episode", episode)
    return sub, native, episode


def _post_segment_evidence(sub, episode, *, ordinal: int, predicates: list[str],
                           residual: frozenset, reached: list[str], topic: str,
                           setpoint_observer) -> None:
    """Ingest one immutable evidence fact for each distinct projected predicate.

    This is deliberately only world/trajectory adaptation: no counter, due decision,
    Observation creation, or mint verdict is retained in Python.
    """
    witnesses_by_pred = {
        predicate: sorted([list(t) for t in residual if isinstance(t, tuple)
                           and len(t) >= 2 and t[1] == predicate], key=repr)
        for predicate in predicates
    }
    for predicate in predicates:
        evidence = sub.add_node("ResidualSegmentEvidence", {
            "predicate": predicate,
            "recurrence_key": predicate,
            "structural_signature": [[predicate]],
            "capability_key": "minted_" + rf._key_component(predicate),
            "segment_ordinal": int(ordinal),
            "tuple_witnesses": witnesses_by_pred[predicate],
            "reached_topics": list(reached),
            "setpoint_topic": topic,
            "setpoint_observer": str(setpoint_observer),
            "integer_native": 1,
        })
        sub.add_edge(episode, "has_residual_segment_evidence", evidence)


def _episode_result(sub, episode, *, segment_count: int) -> tuple[dict[str, int], list[list[str]], list[dict], list[str]]:
    """Read the native ledger and offers back into the historical return shape."""
    evidence = list(sub.neighbours(episode, "has_residual_segment_evidence"))
    trace_by_ordinal: dict[int, list[str]] = {}
    for node in evidence:
        attrs = sub.node(node)["attrs"]
        trace_by_ordinal.setdefault(int(attrs.get("segment_ordinal", 0)), []).append(attrs["predicate"])
    trace = [sorted(trace_by_ordinal.get(i, [])) for i in range(segment_count)]

    candidates = list(sub.neighbours(episode, "has_predicate_recurrence_candidate"))
    persistence = {sub.node(c)["attrs"]["predicate"]: int(sub.node(c)["attrs"].get("persistence", 0))
                   for c in candidates}
    events, axes = [], []
    for candidate in sorted(candidates, key=lambda n: sub.node(n)["attrs"]["predicate"]):
        candidate_attrs = sub.node(candidate)["attrs"]
        predicate = candidate_attrs["predicate"]
        for offer in sub.neighbours(candidate, "has_mint_offer"):
            attrs = sub.node(offer)["attrs"]
            status = attrs.get("offer_status", attrs.get("status"))
            event = {"predicate": predicate,
                     "persistence": int(attrs.get("offered_at_persistence", candidate_attrs.get("persistence", 0))),
                     "minted": status == "minted",
                     "capability_key": candidate_attrs.get("capability_key"),
                     "status": status,
                     "offered_at_segment": int(attrs.get("offered_at_segment", -1))}
            minted = list(sub.neighbours(offer, "minted"))
            if minted:
                event["axis_id"] = str(minted[0])
                axes.append(str(minted[0]))
            elif status == "recognized_duplicate":
                key = candidate_attrs.get("capability_key")
                for axis in sub.nodes("CapabilityAxis"):
                    axis_attrs = sub.node(axis)["attrs"]
                    if axis_attrs.get("induced") and list(axis_attrs.get("capability_keys") or []) == [key]:
                        event["covered_by_existing_axis"] = str(axis)
                        break
            events.append(event)
    return persistence, trace, events, axes


def run_minting_train_of_thought(
        wa, *, setpoint_observer: Any, topic: Optional[str] = None,
        setpoint_topic: Optional[str] = None, width0: int = 1, widen_step: int = 1,
        narrow_step: int = 1, deviation_wide_quanta: int = 2,
        deviation_converge_quanta: int = 0, turns_per_segment: int = 3,
        max_segments: int = 6, mint_after_quanta: int = 3,
        on_unknown: str = "return", ask_fn: Optional[Callable[[str], Any]] = None) -> dict[str, Any]:
    """Run the regulated trajectory while the graph owns recurrence and offering.

    Policy remains locked: one episode per invocation; predicate-only candidate
    identity; episode-wide accumulated occurrences (absence does not reset); integer
    threshold; and exactly one native offer per candidate regardless of terminal
    decode/mint status.
    """
    start = topic or sd.select_curiosity_topic(wa)
    if not start:
        return {"segments": [], "width_trace": [], "deviation_trace": [],
                "recovered_total": [], "stop_reason": "no_topic", "setpoint_topic": None,
                "admitted_size": None, "residual_persistence": {}, "residual_trace": [],
                "mint_events": [], "minted_axes": []}

    sp_topic = setpoint_topic or start
    admitted = rtot._admitted_signature(wa, sp_topic, setpoint_observer)
    sub, native, episode = _open_episode(
        wa, mint_after_quanta=mint_after_quanta, setpoint_observer=setpoint_observer,
        topic=sp_topic)
    max_shell, width = tot.WIDTH_MAX_SHELL, tot.snap_width_to_quanta(width0)
    widen_step, narrow_step = max(1, int(widen_step)), max(1, int(narrow_step))
    cur_topic, stop_reason = start, "max_segments"
    seen_total: set = set()
    recovered_total: set = set()
    segments: list[dict] = []
    width_trace: list[int] = []
    deviation_trace: list[int] = []

    for ordinal in range(int(max_segments)):
        seg = tot.run_inner_conversation(
            wa, topic=cur_topic, max_turns=turns_per_segment, width=width,
            novelty_window=turns_per_segment, on_unknown=on_unknown, ask_fn=ask_fn)
        reached = list(seg.get("topics_thought") or [])
        seen_total |= set(reached)
        recovered_total |= set(seg.get("recovered_total") or [])
        residual = _residual_tuples(wa, reached, admitted, setpoint_observer)
        predicates = _residual_predicates(residual)
        deviation = len(residual)
        _post_segment_evidence(sub, episode, ordinal=ordinal, predicates=predicates,
                               residual=residual, reached=reached, topic=sp_topic,
                               setpoint_observer=setpoint_observer)
        native_steps = native.run_rules()
        sub.add_node("NativeMintingTrainReceipt", {
            "schema": "native_minting_train_receipt.v1",
            "cluster": "minting_train_of_thought.segment_settlement",
            "provenance": "native_rule_readback:minting_train",
            "native_rule": "minting_train_native_rules",
            "native_steps": int(native_steps),
            "segment_ordinal": int(ordinal),
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        })
        deviation_trace.append(deviation)
        width_trace.append(width)
        segments.append({"topic": cur_topic, "width": width, "deviation": deviation,
                         "reached": reached, "residual_predicates": predicates,
                         "seg_stop": seg.get("stop_reason")})
        if seg.get("stop_reason") in ("novelty_stalled", "no_topic") or not reached:
            stop_reason = seg.get("stop_reason") or "converged"
            break
        if deviation >= deviation_wide_quanta:
            width = min(max_shell, width + widen_step)
        elif deviation <= deviation_converge_quanta:
            width = max(0, width - narrow_step)
        fresh = [concept for concept in reached if concept and concept != cur_topic]
        in_tube, off_tube = [], []
        for concept in fresh:
            signature = rtot._admitted_signature(wa, concept, setpoint_observer)
            (in_tube if signature & admitted else off_tube).append(concept)
        frontier = [concept for concept in in_tube if concept not in seen_total] or in_tube or off_tube
        if not frontier:
            stop_reason = "converged"
            break
        cur_topic = frontier[0]

    persistence, trace, events, axes = _episode_result(sub, episode, segment_count=len(segments))
    return {"segments": segments, "width_trace": width_trace, "deviation_trace": deviation_trace,
            "recovered_total": sorted(recovered_total), "stop_reason": stop_reason,
            "setpoint_topic": sp_topic, "admitted_size": len(admitted),
            "residual_persistence": persistence, "residual_trace": trace,
            "mint_events": events, "minted_axes": axes,
            "minting_recurrence_episode": str(episode)}
