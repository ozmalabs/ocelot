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

THE TUBE, this block — a CONCEPT-REGION tube. The set-point is a REGION of admissible
concepts (a legitimate ThoughtManifold tube), and deviation = the INTEGER COUNT of the
trajectory's reached concepts that fall OUTSIDE the region (a discrete quantum — a count
of concepts, not a float fraction; the substrate's premise is discrete quanta, never a
continuum). This is honestly demonstrable on the plain is-a seed. The richer APERTURE-GRAIN tube (a set-point
observer_aperture whose grain sets tube width: vague grain = wide tube/freeform, sharp =
narrow tube/focus) is the confirmed-literal form but its vague<->sharp dial only bites when
concepts carry the dynamical/qualia dimensions grain acts on — which the plain is-a seed
lacks. That upgrade is block 349 (seed the qualia substrate). Both are valid tubes; this
block names + builds the concept-region one and leaves the aperture-grain hook ready.

Additive: wraps train_of_thought.run_inner_conversation (the trajectory generator) + its
attention_width axis; teacher-free at loop time; never edits a protected file or the .so,
never touches conceptualizer.py.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable, Optional

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
#  THE CONTROLLER — trajectory control: deviation steers the width.
# --------------------------------------------------------------------------- #
def run_regulated_train_of_thought(
        wa, *, topic: Optional[str] = None,
        tube_region: Optional[set] = None,
        width0: int = 1, widen_step: int = 1, narrow_step: int = 1,
        deviation_wide_quanta: int = 2,
        deviation_converge_quanta: int = 0,
        turns_per_segment: int = 3, max_segments: int = 6,
        on_unknown: str = "return",
        ask_fn: Optional[Callable[[str], Any]] = None) -> dict[str, Any]:
    """Steer a train of thought as a TRAJECTORY held within a TUBE — everything in
    DISCRETE QUANTA (the substrate's premise: no floats, no continuum).

    The trajectory is generated segment-by-segment by
    train_of_thought.run_inner_conversation at the current attention_width — an
    INTEGER number of breadth QUANTA (shells k, the block-347 quantized axis; the
    trajectory's tangent breadth). After each segment the trajectory's DEVIATION
    from the tube — the INTEGER COUNT of the segment's reached concepts outside the
    admissible region (where the trajectory IS now) — is measured and STEERS the
    width for the next segment, compared in QUANTA (not float thresholds):
      · deviation >= deviation_wide_quanta  -> the trajectory is leaving the tube /
        not converging: WIDEN by +1 quantum (explore more of the manifold to find
        the region);
      · deviation <= deviation_converge_quanta -> it is inside/converging: NARROW by
        -1 quantum (tighten toward the geodesic — focus);
      · in between: hold width.
    So a NARROW tube (small region) pulls the width DOWN toward focus; a WIDE tube
    (large region) lets it ROAM. The width is the quantized tangent breadth (347);
    the tube is the required region; the integer deviation is the steering residual.

    All quantities are quanta: width0 / widen_step / narrow_step are integer quanta
    of breadth (clamped to [0, tot.WIDTH_MAX_SHELL]); deviation is a count of
    concepts; the thresholds are counts (quanta) too. widen/narrow = +/-1 quantum.

    Termination (the manifold BOUNDARY): a segment's own novelty_stalled /
    converged propagates up; or max_segments. Teacher-free on the held path
    (on_unknown='return'); the external ASK floor stays a choosable option.

    Returns {segments:[{topic,width,deviation,reached,stop_reason}...],
    width_trace, deviation_trace, recovered_total, stop_reason, tube_region} — the
    width_trace and deviation_trace are INTEGER quanta traces."""
    start = topic or sd.select_curiosity_topic(wa)
    if not start:
        return {"segments": [], "width_trace": [], "deviation_trace": [],
                "recovered_total": [], "stop_reason": "no_topic",
                "tube_region": sorted(tube_region or [])}
    if tube_region is None:
        tube_region = _region_from_topic(wa, start)

    # width is an INTEGER number of breadth quanta (shells), snapped/clamped the
    # substrate's native way — never a float.
    max_shell = tot.WIDTH_MAX_SHELL
    width = tot.snap_width_to_quanta(width0)
    widen_step = max(1, int(widen_step))
    narrow_step = max(1, int(narrow_step))
    cur_topic = start
    seen_total: set = set()
    recovered_total: set = set()
    segments: list[dict] = []
    width_trace: list[int] = []
    deviation_trace: list[int] = []
    stop_reason = "max_segments"

    for _ in range(int(max_segments)):
        seg = tot.run_inner_conversation(
            wa, topic=cur_topic, max_turns=turns_per_segment, width=width,
            novelty_window=turns_per_segment, on_unknown=on_unknown, ask_fn=ask_fn)
        reached = list(seg.get("topics_thought") or [])
        seen_total |= set(reached)
        recovered_total |= set(seg.get("recovered_total") or [])

        # DEVIATION of the trajectory's CURRENT position from the tube (steering
        # residual) — an integer count of THIS segment's reached concepts that fall
        # outside the region. Measured on the current reach (where the trajectory IS
        # now), not the cumulative history, so the control law can observe the
        # deviation FALL as widening steers the trajectory into the tube.
        dev = _trajectory_deviation(reached, tube_region)
        deviation_trace.append(dev)
        width_trace.append(width)
        segments.append({"topic": cur_topic, "width": width,
                         "deviation": dev, "reached": reached,
                         "seg_stop": seg.get("stop_reason")})

        # BOUNDARY: the segment ran out of reachable manifold -> the train ends.
        if seg.get("stop_reason") in ("novelty_stalled", "no_topic") \
                or not reached:
            stop_reason = seg.get("stop_reason") or "converged"
            break

        # STEER the width by the deviation (the feedback law), in QUANTA: compare
        # the integer deviation count against the quantum thresholds and step the
        # width by +/-1 quantum, clamped to [0, max_shell].
        if dev >= deviation_wide_quanta:
            width = min(max_shell, width + widen_step)     # leaving tube -> explore
        elif dev <= deviation_converge_quanta:
            width = max(0, width - narrow_step)            # inside -> focus
        # else: hold.

        # next segment starts from a not-yet-thought frontier topic (residual of
        # the tube first — pursue the admissible region — else any fresh reached).
        frontier = [c for c in tube_region if c not in seen_total] or \
                   [c for c in reached if c not in {cur_topic}]
        nxt = None
        for c in frontier:
            if c not in seen_total or c in tube_region:
                nxt = c
                break
        if nxt is None:
            stop_reason = "converged"
            break
        cur_topic = nxt

    return {"segments": segments, "width_trace": width_trace,
            "deviation_trace": deviation_trace,
            "recovered_total": sorted(recovered_total),
            "stop_reason": stop_reason, "tube_region": sorted(tube_region)}
