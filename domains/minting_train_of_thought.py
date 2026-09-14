"""minting_train_of_thought — block 351 — GATED DIMENSION-MINTING.

The last facet of "a train of thought is a trajectory through a manifold". Blocks
348/349 steer the trajectory to stay within a TUBE (a set-point) by measuring its
DEVIATION — the residual signature tuples the set-point never admitted — and
turning that residual into WIDTH. But the residual is thrown away each segment
(only its integer COUNT is kept, to steer the width). This block KEEPS it.

The reframe (the user's): the inner conversation keeps reaching thoughts whose
signature has NO held axis to place them on. A SINGLE such miss is noise — the
trajectory brushed a boundary once. But when the SAME uncoverable structure RECURS
across segments — a PERSISTENT residual — the manifold itself is too small: it has
no dimension for a thing the thinker keeps thinking. So it COINS one. This is
ACCOMMODATION (grow the space), not gap-fill (patch one miss).

WHAT THIS IS (honest naming, the discipline of the whole arc):

  · It does NOT invent minting machinery. Minting already exists: the DECISION is
    made by the seeded shape-decode loop (seeds/shape_decode_loop.json) via
    reflective_faculty.induce_concern — you hand it a relation-system, the RULES
    decide `recognized` (held codebook covers it -> no mint, the null),
    `recognized_duplicate` (an induced axis with this same key already exists ->
    no mint, the over-minting guard that stops unbounded axis growth), or
    `minted` (nothing covers it -> coin a CapabilityAxis from the residual). This
    block only feeds that gate the PERSISTENT residual and reads the verdict back.

  · The RESIDUAL is the block-349 aperture-grain residual: the frozenset of the
    trajectory's `(dimension, predicate, k)` concept_signature tuples (read
    through the set-point observer's aperture) that fall OUTSIDE the set-point's
    admitted tuple set. regulated_train_of_thought._aperture_deviation already
    computes exactly this set and discards all but its len(); here we compute the
    SET and accumulate it.

  · The GATE is PERSISTENCE, counted in DISCRETE QUANTA (integers, the substrate's
    premise — no floats, no continuum): each residual PREDICATE that recurs in a
    segment advances an integer counter by +1; a predicate that does not recur
    this segment does not advance (a transient miss never reaches threshold). When
    a predicate's persistence reaches `mint_after_quanta` (an integer count of
    segments), its residual is handed to the mint gate. So minting is gated on
    ACCUMULATED persistent residual, exactly as designed.

Additive: WRAPS train_of_thought.run_inner_conversation (the trajectory generator)
and reuses regulated_train_of_thought's tube/deviation structure and
reflective_faculty.induce_concern's mint gate. Never edits a protected file or the
.so, never touches conceptualizer.py. Teacher-free at loop time: the persistence
gate and the sd-loop are pure graph reads; no LLM decides anything.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable, Optional

from domains import analogy_search as asr
from domains import reflective_faculty as rf
from domains import regulated_train_of_thought as rtot
from domains import self_dialogue as sd
from domains import train_of_thought as tot


# --------------------------------------------------------------------------- #
#  THE RESIDUAL SET — the block-349 aperture residual, kept as a SET (not just
#  its count). The trajectory's aperture-projected signature tuples that fall
#  OUTSIDE the set-point's admitted set: frozenset(traj) - admitted. This is the
#  SAME quantity regulated_train_of_thought._aperture_deviation reduces to an
#  integer via len(); here we return the set so its structure can accumulate.
# --------------------------------------------------------------------------- #
def _residual_tuples(wa, reached: Iterable[str], admitted: frozenset,
                     observer) -> frozenset:
    """The residual signature tuples of `reached` against the set-point's
    `admitted` tuple set, read through `observer`'s aperture. A frozenset of
    `(dimension, predicate, k)` tuples — one tuple is one discrete quantum, the
    grain being the quantum (identical convention to _aperture_deviation, whose
    integer deviation is exactly len() of this set). Teacher-free graph read via
    analogy_search.concept_signature(observer=...)."""
    sub = sd._sub(wa)
    traj: set = set()
    for c in reached:
        if not c:
            continue
        node = sd._find_concept(sub, c)
        if node is None:
            continue
        traj |= set(asr.concept_signature(sub, node, observer=observer))
    return frozenset(traj) - admitted


def _residual_predicates(residual: frozenset) -> list[str]:
    """The PREDICATE slot of each residual signature tuple `(dimension,
    predicate, k)` — the mint gate keys on predicates (induce_concern names the
    CapabilityAxis from the observation's own predicates, sorted). Sorted, deduped
    to a stable multiset-free list: a recurring predicate is counted by the
    persistence ledger below, not by repetition within one segment."""
    preds = set()
    for t in residual:
        if isinstance(t, tuple) and len(t) >= 2 and isinstance(t[1], str):
            preds.add(t[1])
    return sorted(preds)


# --------------------------------------------------------------------------- #
#  THE MINTING LOOP — a regulated train of thought that also ACCUMULATES the
#  residual and mints a new axis when it PERSISTS.
# --------------------------------------------------------------------------- #
def run_minting_train_of_thought(
        wa, *, setpoint_observer: Any,
        topic: Optional[str] = None,
        setpoint_topic: Optional[str] = None,
        width0: int = 1, widen_step: int = 1, narrow_step: int = 1,
        deviation_wide_quanta: int = 2,
        deviation_converge_quanta: int = 0,
        turns_per_segment: int = 3, max_segments: int = 6,
        mint_after_quanta: int = 3,
        on_unknown: str = "return",
        ask_fn: Optional[Callable[[str], Any]] = None) -> dict[str, Any]:
    """Steer a train of thought as a manifold TRAJECTORY within an APERTURE-GRAIN
    tube (block 349) AND grow the manifold when the trajectory keeps escaping it:
    mint a new concept-signature axis when a residual PERSISTS.

    Runs the SAME segment loop as regulated_train_of_thought's aperture-grain path
    (the trajectory is generated by train_of_thought.run_inner_conversation at the
    current integer attention_width; the width is steered by the integer aperture
    deviation), and ADDITIONALLY, each segment:

      1. computes the residual SET (frozenset(traj) - admitted) — the block-349
         residual kept as structure, not reduced to its count;
      2. advances an integer PERSISTENCE counter (`residual_persistence`) by +1
         for every residual PREDICATE present THIS segment; predicates absent this
         segment do not advance (a transient miss decays to irrelevance — only
         RECURRENCE accumulates);
      3. once a predicate's persistence reaches `mint_after_quanta` (an integer
         count of segments) AND it has not already been offered to the mint gate,
         hands the persistent predicates to reflective_faculty.induce_concern — the
         seeded shape-decode loop then DECIDES: `recognized`/`recognized_duplicate`
         -> no mint (a held or already-induced axis covers it — the over-minting
         guard), `minted` -> coin a CapabilityAxis from the residual. This block
         only reads the verdict; the mint decision is the rules'.

    Everything is DISCRETE QUANTA: width0/steps/thresholds and `mint_after_quanta`
    are integer quanta; persistence counts are integers; the residual tuples carry
    the integer step `k` from analogy_search._round_to_vocab. No floats, no
    continuum, teacher-free at loop time.

    `setpoint_observer` is REQUIRED — the aperture-grain tube is the only tube over
    which a signature RESIDUAL (the mint surface) is defined; the concept-region
    tube (block 348) has no signature residual to mint from.

    Returns the regulated-train dict PLUS:
      · residual_persistence: {predicate -> int}   the persistence ledger,
      · residual_trace: [sorted list per segment]  the residual predicates seen,
      · mint_events: [induce_concern result dict]   every gate invocation + verdict,
      · minted_axes: [axis_id]                      the CapabilityAxis ids coined.
    (segments, width_trace, deviation_trace, recovered_total, stop_reason,
    setpoint_topic, admitted_size are as run_regulated_train_of_thought returns.)"""
    start = topic or sd.select_curiosity_topic(wa)
    if not start:
        return {"segments": [], "width_trace": [], "deviation_trace": [],
                "recovered_total": [], "stop_reason": "no_topic",
                "setpoint_topic": None, "admitted_size": None,
                "residual_persistence": {}, "residual_trace": [],
                "mint_events": [], "minted_axes": []}

    sp_topic = setpoint_topic or start
    admitted = rtot._admitted_signature(wa, sp_topic, setpoint_observer)

    # width is an INTEGER number of breadth quanta (shells), snapped/clamped the
    # substrate's native way — never a float. (Same discipline as the regulated
    # loop; this block adds the residual ledger on top, it does not change the
    # width control law.)
    max_shell = tot.WIDTH_MAX_SHELL
    width = tot.snap_width_to_quanta(width0)
    widen_step = max(1, int(widen_step))
    narrow_step = max(1, int(narrow_step))
    mint_after_quanta = max(1, int(mint_after_quanta))
    cur_topic = start
    seen_total: set = set()
    recovered_total: set = set()
    segments: list[dict] = []
    width_trace: list[int] = []
    deviation_trace: list[int] = []
    stop_reason = "max_segments"

    # THE PERSISTENCE LEDGER — integer count of segments each residual predicate
    # has recurred in. The gate: a predicate mints only once its count reaches
    # mint_after_quanta. `offered` records predicates already handed to the mint
    # gate, so we ask the sd-loop about a persistent residual exactly once (the
    # sd-loop's own recognized_duplicate guard also protects against re-mint, but
    # we do not re-invoke it every subsequent segment — one persistent residual is
    # one accommodation event).
    residual_persistence: dict[str, int] = {}
    residual_trace: list[list[str]] = []
    offered: set = set()
    mint_events: list[dict] = []
    minted_axes: list[str] = []

    for _ in range(int(max_segments)):
        seg = tot.run_inner_conversation(
            wa, topic=cur_topic, max_turns=turns_per_segment, width=width,
            novelty_window=turns_per_segment, on_unknown=on_unknown, ask_fn=ask_fn)
        reached = list(seg.get("topics_thought") or [])
        seen_total |= set(reached)
        recovered_total |= set(seg.get("recovered_total") or [])

        # THE RESIDUAL SET this segment (block-349 aperture residual, kept whole).
        residual = _residual_tuples(wa, reached, admitted, setpoint_observer)
        dev = len(residual)               # identical to _aperture_deviation's int
        seg_preds = _residual_predicates(residual)
        residual_trace.append(seg_preds)
        deviation_trace.append(dev)
        width_trace.append(width)

        # ADVANCE the persistence ledger: +1 quantum for every predicate present
        # THIS segment. Predicates absent this segment are simply not touched — a
        # transient miss never advances, only RECURRENCE accumulates. Integer only.
        for p in seg_preds:
            residual_persistence[p] = residual_persistence.get(p, 0) + 1

        # THE MINT GATE: any predicate whose persistence has reached the integer
        # threshold and has not yet been offered. Hand the sd-loop the persistent
        # residual as a relation-system (a list of [predicate] lists); the RULES
        # decide recognized / recognized_duplicate / minted. Teacher-free.
        due = sorted(p for p, k in residual_persistence.items()
                     if k >= mint_after_quanta and p not in offered)
        for p in due:
            offered.add(p)
            observation = [[p]]           # the persistent residual predicate
            res = rf.induce_concern(wa, observation,
                                    name_hint="minted_" + rf._key_component(p))
            res = dict(res)
            res["predicate"] = p
            res["persistence"] = residual_persistence[p]
            mint_events.append(res)
            if res.get("minted") and res.get("axis_id"):
                minted_axes.append(res["axis_id"])

        segments.append({"topic": cur_topic, "width": width,
                         "deviation": dev, "reached": reached,
                         "residual_predicates": seg_preds,
                         "seg_stop": seg.get("stop_reason")})

        # BOUNDARY: the segment ran out of reachable manifold -> the train ends.
        if seg.get("stop_reason") in ("novelty_stalled", "no_topic") \
                or not reached:
            stop_reason = seg.get("stop_reason") or "converged"
            break

        # STEER the width by the deviation (the SAME feedback law as the regulated
        # loop), in QUANTA. The minting ledger above does not alter this — width
        # control and manifold growth are orthogonal facets of the same trajectory.
        if dev >= deviation_wide_quanta:
            width = min(max_shell, width + widen_step)
        elif dev <= deviation_converge_quanta:
            width = max(0, width - narrow_step)

        # next segment starts from a fresh frontier concept, STEERING INTO the tube
        # (prefer a fresh reached concept whose aperture signature shares tuples
        # with the set-point's admitted set), identical to the regulated loop's
        # aperture-grain frontier selection. Reuses the SAME observer aperture.
        fresh = [c for c in reached if c and c not in {cur_topic}]
        in_tube, off_tube = [], []
        for c in fresh:
            sig = rtot._admitted_signature(wa, c, setpoint_observer)
            (in_tube if (sig & admitted) else off_tube).append(c)
        frontier = ([c for c in in_tube if c not in seen_total] or in_tube
                    or off_tube)
        nxt = frontier[0] if frontier else None
        if nxt is None:
            stop_reason = "converged"
            break
        cur_topic = nxt

    return {"segments": segments, "width_trace": width_trace,
            "deviation_trace": deviation_trace,
            "recovered_total": sorted(recovered_total),
            "stop_reason": stop_reason,
            "setpoint_topic": sp_topic,
            "admitted_size": len(admitted),
            "residual_persistence": dict(residual_persistence),
            "residual_trace": residual_trace,
            "mint_events": mint_events,
            "minted_axes": minted_axes}
