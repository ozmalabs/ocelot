"""Block 348000 — the train of thought as a TRAJECTORY THROUGH A THOUGHT-MANIFOLD.

The user's closure of the arc: a train of thought IS a trajectory through a manifold —
"like it always was". Every piece built in 341-347 is a facet of that one geometric fact:

  · each THOUGHT is a point on the manifold (a concept, at an aperture);
  · the SUCCESSION of thoughts is the TRAJECTORY (the path traced);
  · attention_width (block 347) is the TANGENT BREADTH — how wide a neighbourhood the
    trajectory may step into at each point, expressed as DISCRETE QUANTA (integer
    shells k at a configurable grain): k=0 = geodesic along the is-a spine; the
    widest shell = roam the tangent space associatively;
  · the SET-POINT is the REQUIRED TUBE the trajectory is steered to stay within;
  · the feedback loop is TRAJECTORY CONTROL: the RESIDUAL (deviation from the tube)
    drives the width to steer back;
  · block-347's novelty_stalled is the trajectory reaching the manifold BOUNDARY.

HONEST NAMING (the discipline that made attention_width a *sibling* of aperture, and the
set-point *literally* an observer_aperture): this ThoughtManifold is a SIBLING of
future_option_risk.FutureManifold — it shares the tube / projection / deviation STRUCTURE
but lives over the CONCEPT graph, not action/world-state ShapeSlice cells. It does NOT
reuse FutureManifold's action_count / intervention_magnitude / ShapeSlice / commit-wait-
refine machinery (all action-specific); it shares only tube = admissible region,
deviation = departure from it, boundary = termination.

THE TUBE — two forms, selected by which set-point is passed (additive):

  · CONCEPT-REGION tube (block 348, the DEFAULT / backward-compatible path). The
    set-point is a REGION of admissible concepts, and deviation = the INTEGER
    COUNT of the trajectory's reached concepts that fall OUTSIDE the region (a
    discrete quantum — a count of concepts, not a float fraction). Honestly
    demonstrable on the plain is-a seed. Used when `setpoint_observer` is None.

  · APERTURE-GRAIN tube (block 349, the CONFIRMED-LITERAL form). The set-point is
    an observer_aperture whose GRAIN sets the tube width: vague (coarse) grain =
    wide tube/freeform, sharp (fine) grain = narrow tube/focus. deviation = the
    DISCRETE-QUANTA integer count of the trajectory's concept_signature tuples
    (read through the observer aperture) that fall OUTSIDE the set-point's
    admitted tuple set (a frozenset difference; one tuple = one quantum, grain
    being the quantum). Its vague<->sharp dial bites for real ONLY when the
    concepts carry the dynamical/qualia dimensions grain acts on — which the
    plain is-a seed lacks, so block 349 SEEDS them (install seeds/qualia_space.json
    + set the CAN field attrs state/identity_field on the concepts). Selected by
    passing `setpoint_observer` (with an optional `setpoint_topic` anchor).

Both are valid ThoughtManifold tubes over the same control law (the width is
steered by an integer deviation regardless of how deviation is computed). The
concept-region path is byte-identical when `setpoint_observer` is None.

Additive: wraps train_of_thought.run_inner_conversation (the trajectory generator) + its
attention_width axis; teacher-free at loop time; never edits a protected file or the .so,
never touches conceptualizer.py.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable, Optional

from domains import analogy_search as asr
from domains import self_dialogue as sd
from domains import train_of_thought as tot


# --------------------------------------------------------------------------- #
#  THE TUBE — a region of admissible concepts (this block). A future block
#  upgrades this to an aperture-grain tube over concept signatures.
# --------------------------------------------------------------------------- #
def _region_from_topic(wa, topic: str, radius: int = 2) -> set:
    """A concept-region tube around `topic`: the topic + its is-a cone
    (transitive ancestors) — the region a focused train about `topic` should
    stay within. `radius` is advisory (the cone is the whole ancestry here).
    Teacher-free graph read. This is the DEFAULT set-point when the caller does
    not supply an explicit region."""
    region = {topic}
    try:
        region |= set(tot.transitive_ancestors(wa, topic))
    except Exception:
        pass
    return region


def _trajectory_deviation(reached: Iterable[str], tube_region: set) -> int:
    """The trajectory's DEVIATION from the tube = the INTEGER COUNT of concepts it
    has reached that fall OUTSIDE the admissible region. This is a discrete
    quantum — a count of reached concepts, not a float fraction. 0 = the whole
    trajectory stayed inside the tube (converged/focused); a larger integer = more
    of it left the region (wandered off). This is the ThoughtManifold sibling
    analogue of future_option_risk._residual's escape measure — over a concept
    set, counted in whole concepts (the natural quantum of the concept graph),
    not ShapeSlice cells and not a continuum fraction."""
    return sum(1 for c in reached if c and c not in tube_region)


# --------------------------------------------------------------------------- #
#  THE APERTURE-GRAIN TUBE (block 349) — the CONFIRMED-LITERAL form. The
#  set-point is an OBSERVER whose per-dimension GRAIN sets the tube WIDTH:
#  a vague (coarse) grain admits a WIDE band of signatures (freeform); a sharp
#  (fine) grain admits a NARROW band (focus). Grain bites for real because it
#  coarsens a MULTI-AXIS concept_signature — but ONLY when the concepts carry
#  the dynamical/qualia dimensions grain acts on (seed the qualia substrate:
#  install seeds/qualia_space.json + set the CAN field attrs state/
#  identity_field on the concepts). Selected by passing `setpoint_observer`;
#  the concept-region path above stays intact and is used when it is None.
# --------------------------------------------------------------------------- #
def _admitted_signature(wa, setpoint_topic: str, observer) -> frozenset:
    """The APERTURE-PROJECTED signature the set-point admits: the frozenset of
    `(dimension, predicate, k)` tuples of the set-point concept read THROUGH the
    observer's aperture (its `resolves` existence gate + per-dimension `grain`
    quantum). This is the tube: the set of signature quanta the observer, at its
    grain, will accept. Coarse grain collapses many raw field values to the same
    (or a dropped-zero) integer step, so the admitted set changes with grain —
    that is the tube WIDTH dial. Teacher-free graph read via
    analogy_search.concept_signature(observer=...)."""
    sub = sd._sub(wa)
    node = sd._find_concept(sub, setpoint_topic)
    if node is None:
        return frozenset()
    return asr.concept_signature(sub, node, observer=observer)


def _signature_projection_inputs(wa, topic: str) -> tuple[list, list]:
    """Return static coordinates and raw codebook fields for graph projection."""
    sub = sd._sub(wa)
    node = sd._find_concept(sub, topic)
    if node is None:
        return [], []
    static = [coordinate for coordinate in asr.concept_signature(
        sub, node, observer=None) if not str(coordinate[0]).startswith("dynamical:")]
    attrs = sub.node(node).get("attrs", {})
    raw = []
    for dimension, attr, quantum, half_width, overlay in asr._qualia_schema(sub)["field_axes"]:
        if overlay or attrs.get(attr) is None:
            continue
        raw.append({"dimension": dimension, "predicate": "field",
                    "raw_value": attrs[attr], "global_quantum": quantum,
                    "half_width": half_width, "projection_status": "pending"})
    return static, raw


def _add_signature_input(sub, manifold, segment, topic, observer, setpoint_topic,
                         *, setpoint=False):
    static, raw_values = _signature_projection_inputs(sub, topic)
    signature = sub.add_node("ThoughtTopicSignature", {
        "topic": topic, "coordinates": sorted(static, key=repr),
        "observer_id": str(observer), "setpoint_topic": setpoint_topic,
        "provenance_kind": "measured_signature_input"})
    if setpoint:
        sub.add_edge(manifold, "has_setpoint_signature", signature)
    else:
        sub.add_edge(segment, "has_topic_signature", signature)
    for raw_value in raw_values:
        raw = sub.add_node("ThoughtRawSignatureCoordinate", raw_value)
        sub.add_edge(signature, "has_raw_coordinate", raw)
        sub.add_edge(manifold, "has_raw_signature_coordinate", raw)
    return signature


# --------------------------------------------------------------------------- #
#  THE CONTROLLER — trajectory control: deviation steers the width.
# --------------------------------------------------------------------------- #
def _native_controller_graph(wa):
    """Resolve graph and agent root, installing the opt-in controller on demand."""
    sub = sd._sub(wa)
    native = getattr(sub, "_inner", sub)
    agents = sub.nodes("Agent")
    if not agents:
        raise TypeError("regulated thought requires an Agent graph root")
    agent = agents[0]
    policies = sub.nodes("ThoughtManifoldPolicy")
    if not policies:
        from substrate.seed_loader import manifest_for
        installed = {sub.node(seed)["attrs"].get("id") for seed in sub.nodes("Seed")}
        resolving = set()
        def install(seed_id):
            if seed_id == "core" or seed_id in installed:
                return
            if seed_id in resolving:
                raise ValueError(f"cyclic seed dependency involving {seed_id!r}")
            resolving.add(seed_id)
            manifest = manifest_for(seed_id)
            for dependency in manifest.get("depends_on", ()):
                install(str(dependency))
            native.load_seed_manifest(manifest, agent)
            resolving.remove(seed_id)
            installed.add(seed_id)
        install("thought_manifold")
        policies = sub.nodes("ThoughtManifoldPolicy")
    return sub, native, agent, policies[0]


def run_regulated_train_of_thought(
        wa, *, topic: Optional[str] = None,
        tube_region: Optional[set] = None,
        setpoint_observer: Optional[Any] = None,
        setpoint_topic: Optional[str] = None,
        width0: int = 1, widen_step: int = 1, narrow_step: int = 1,
        deviation_wide_quanta: int = 2,
        deviation_converge_quanta: int = 0,
        turns_per_segment: int = 3, max_segments: int = 6,
        on_unknown: str = "return",
        ask_fn: Optional[Callable[[str], Any]] = None) -> dict[str, Any]:
    """Run the public thought trajectory through the graph controller.

    Python supplies the initial topic, measured signature inputs and each generated
    candidate segment. The graph computes either concept-region or aperture-grain
    deviation, steers width, selects the next frontier and terminates the run.
    Returned topics remain candidate imagery; this adapter emits no grounding.
    """
    start = topic or sd.select_curiosity_topic(wa)
    if not start:
        return {"segments": [], "width_trace": [], "deviation_trace": [],
                "recovered_total": [], "stop_reason": "no_topic",
                "tube_region": sorted(tube_region or [])}
    use_aperture = setpoint_observer is not None
    sp_topic = setpoint_topic or start
    admitted = frozenset()
    sub, native, agent, policy = _native_controller_graph(wa)
    anchor_node = sd._find_concept(sub, start)
    old_enabled = sub.node(policy)["attrs"].get("enabled", 0.0)
    sub.set_attr(policy, "enabled", 1.0)
    manifold = sub.add_node("ThoughtManifold", {
        "status": "running" if use_aperture else "pending",
        "topic": start if use_aperture else None, "candidate_topics": [start],
        "anchor_topic": start, "anchor_node": anchor_node,
        "controller_mode": "aperture_grain" if use_aperture else "concept_region",
        "admitted_signature": [], "admitted_signature_ready": not use_aperture,
        "setpoint_topic": sp_topic if use_aperture else None,
        "region_explicit": tube_region is not None,
        "tube_region": sorted(tube_region) if tube_region is not None else [],
        "width": tot.snap_width_to_quanta(width0),
        "widen_step": max(1, int(widen_step)),
        "narrow_step": max(1, int(narrow_step)),
        "deviation_wide_quanta": int(deviation_wide_quanta),
        "deviation_converge_quanta": int(deviation_converge_quanta),
        "segment_index": 0, "max_segments": max(0, int(max_segments)),
        "seen_topics": [], "detached_buffer": [],
        "detached_buffer_capacity": 64,
        "funding_required": True, "segment_cost": 1.0,
        "provenance_kind": "candidate_imagery",
    })
    sub.set_attr(manifold, "run_key", str(manifold))
    sub.add_edge(agent, "has_thought_manifold", manifold)
    if use_aperture:
        sub.add_edge(manifold, "uses_aperture_observer", setpoint_observer)
        _add_signature_input(sub, manifold, None, sp_topic, setpoint_observer,
                             sp_topic, setpoint=True)
    try:
        native.run_rules(1000)
        segments, width_trace, deviation_trace = [], [], []
        recovered_total = set()
        stop_reason = "max_segments"
        while sub.node(manifold)["attrs"].get("status") == "running":
            state = sub.node(manifold)["attrs"]
            request = next((request for request in sub.neighbours(
                manifold, "has_segment_request")
                if sub.node(request)["attrs"].get("segment_index") ==
                state.get("segment_index")), None)
            if request is None:
                native.run_rules(1000)
                state = sub.node(manifold)["attrs"]
                request = next((request for request in sub.neighbours(
                    manifold, "has_segment_request")
                    if sub.node(request)["attrs"].get("segment_index") ==
                    state.get("segment_index")), None)
            if request is None or sub.node(request)["attrs"].get("status") != "approved":
                stop_reason = str(sub.node(manifold)["attrs"].get(
                    "stop_reason", "funding_unavailable"))
                break
            mode = next(iter(sub.neighbours(agent, "has_network_mode_state")), None)
            if mode is None or sub.node(request)["attrs"].get("debited_epoch") != \
                    sub.node(mode)["attrs"].get("epoch"):
                stop_reason = "stale_funding"
                break
            cur_topic = state.get("topic")
            width = int(state.get("width", 0))
            seg = tot.run_inner_conversation(
                wa, topic=cur_topic, max_turns=turns_per_segment, width=width,
                novelty_window=turns_per_segment, on_unknown=on_unknown, ask_fn=ask_fn)
            reached = list(seg.get("topics_thought") or [])
            recovered_total.update(seg.get("recovered_total") or [])
            segment_node = sub.add_node("ThoughtSegmentInput", {
                "status": "ready", "topics_thought": reached,
                "stop_reason": seg.get("stop_reason", "continue"),
                "recovered_total": list(seg.get("recovered_total") or []),
                "provenance_kind": "candidate_imagery",
            })
            sub.add_edge(manifold, "has_pending_thought_segment", segment_node)
            sub.add_edge(segment_node, "has_segment_generation_funding", request)
            if use_aperture:
                for reached_topic in dict.fromkeys(topic for topic in reached if topic):
                    _add_signature_input(sub, manifold, segment_node, reached_topic,
                                         setpoint_observer, sp_topic)
            native.run_rules(1000)
            steps = [step for step in sub.neighbours(
                manifold, "has_thought_manifold_step")
                     if sub.node(step)["attrs"].get("index") == state.get("segment_index")]
            if not steps:
                terminal_reason = sub.node(manifold)["attrs"].get("stop_reason")
                if terminal_reason in {"budget_disabled", "budget_denied", "stale_funding"}:
                    stop_reason = str(terminal_reason)
                    break
                raise RuntimeError("ThoughtManifold failed to account for an ingested segment")
            trace = sub.node(steps[-1])["attrs"]
            if segment_node not in sub.neighbours(steps[-1], "ingests_thought_segment"):
                raise RuntimeError("ThoughtManifold trace lost its source segment link")
            segments.append({"topic": cur_topic, "width": int(trace["width"]),
                             "deviation": int(trace["deviation"]),
                             "reached": reached, "seg_stop": trace["segment_stop"]})
            width_trace.append(int(trace["width"]))
            deviation_trace.append(int(trace["deviation"]))
            stop_reason = str(trace["segment_stop"])
            if sub.node(manifold)["attrs"].get("status") == "complete":
                if stop_reason not in ("novelty_stalled", "no_topic"):
                    completed = sub.node(manifold)["attrs"]
                    if int(completed.get("segment_index", 0)) >= int(
                            completed.get("max_segments", 0)):
                        stop_reason = "max_segments"
                    else:
                        stop_reason = "converged"
                break
        if not segments:
            stop_reason = str(sub.node(manifold)["attrs"].get(
                "stop_reason", stop_reason))
        return {"segments": segments, "width_trace": width_trace,
                "deviation_trace": deviation_trace,
                "recovered_total": sorted(recovered_total),
                "stop_reason": stop_reason,
                "tube_region": sorted(sub.node(manifold)["attrs"].get("tube_region") or []),
                "setpoint_topic": sp_topic if use_aperture else None,
                "admitted_size": len(sub.node(manifold)["attrs"].get(
                    "admitted_signature", [])) if use_aperture else None}
    finally:
        sub.set_attr(policy, "enabled", old_enabled)
