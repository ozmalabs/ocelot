"""nested_event_tree — parse a spoken word into its DISCRETE NESTED ORDER-N EVENT
TREE and recognise the TREE, not the wave.

THE REFRAME (the deepest lever of the session)
----------------------------------------------
Communication is DISCRETE admissible structure (G, Gamma) serialized through a
lossy continuous channel.  The acoustic "wave" (cochlea / gammatone bands) is NOT
real — it is the un-parsed APPEARANCE of a NESTED HIERARCHY OF DISCRETE ORDER-N
EVENTS.  It only LOOKS continuous because we lacked the structure to resolve the
discreteness (binary admissibility: WITH the grammar -> a discrete nested event
tree; WITHOUT it -> a wave).  Every cross-speaker lever this session nulled because
it operated IN THE WAVE (bands, warps, speaker-norm, matched-filter, even RELATIONS
over the continuous bands — relational_shape).  The fix: PARSE the signal into its
discrete nested order-N event structure and recognise THAT.

WHY THIS IS NOT THE KNOWN FAILURES
----------------------------------
  * NOT surface band-trajectory DtwTo (the wave baseline, arm A).
  * NOT per-frame order-N DESCRIPTORS bolted onto the continuous trajectory
    (iter-11 frame-level curvature/ratios DILUTED; relational_shape's ordinal ranks
    are still a CONTINUOUS per-frame trajectory — the half-step still in the wave).
The NEW thing: DISCRETE LOCATED events as graph NODES + a NESTED TREE (nesting
edges) + a STRUCTURAL match of the tree.

WHAT A NESTED ORDER-N EVENT IS  (the agent owns order_n_concepts: order-0 = value,
order-1 = velocity, order-2 = curvature, recursive finite differences)
----------------------------------------------------------------------------------
At EACH order N there is a DISCRETE EVENT SERIES — the LOCATED points where that
order's structure changes (the extrema of the order-N derivative of the word's
energy contour):

  order 0  (the contour itself)        : its maxima  = SYLLABLE NUCLEI  (slow, the
                                         parents — the loud sonorant peaks).
  order 1  (velocity of the contour)   : its extrema = GESTURE on/off-sets (faster
                                         — where energy is rising/falling hardest:
                                         consonant releases, closures).
  order 2  (curvature / acceleration)  : its extrema = fast TRANSIENTS / bursts
                                         (the fastest located structure here).

Higher order = FASTER structure, located inside the span of the slower lower-order
events.  The events are DISCRETE (located nodes, not a curve) and NESTED: each
order-N event is a CHILD of the order-(N-1) event whose time-span contains it ->
a discrete event TREE  (nodes = events {order, time, type, magnitude}; edges =
nesting).  The superposition of all the order-N event series IS the "wave"; the
TREE is the structure under it.

SPEAKER-INVARIANCE FALLS OUT (the claim under test)
---------------------------------------------------
A new talker changes the continuous REALIZATION — the exact magnitudes, the exact
timing — but the discrete event STRUCTURE (how many events at each order, their
TYPES, their ORDER, their NESTING, their relative ordering) is the MESSAGE.  We
encode each event by its ORDER, the SIGN of its extremum (a max vs a min — a
relation, gain-invariant), its RELATIVE time (position in the word, 0..1 — invariant
to absolute duration), its RELATIVE depth in the tree, and the LOG of its magnitude
normalised within the word (a within-unit ratio, so a global gain cancels).  No
absolute band coordinate enters the match — by construction it lives OUTSIDE the
wave.

DISCIPLINE
----------
numpy appears ONLY at the I/O boundary: laying out the band matrix and LOCATING the
extrema (finding extrema is signal-processing I/O, the same category as the
gammatone front end).  The event TREE is materialised as graph NODES + nesting edges
the agent owns; the recognition MATCH is the agent's NATIVE DtwTo Term over the
serialized event sequence (substrate.evaluate) — the discrete monotone alignment of
two event series IS the structural tree match (it admits insertion/deletion of an
event = a structural edit).  Counts not nets; no .fit, no learned weight.
"""
from __future__ import annotations

import numpy as np

# ---------------------------------------------------------------------------
# I/O BOUNDARY ONLY — locate the discrete order-N events of a word.
#
# The agent's order_n operator is the recursive finite difference (order_n_concepts.
# nth_order_terms); over a 1-D contour that is exactly np.diff applied N times.  We
# compute the contour + its order-N finite differences + the LOCATED extrema here at
# the boundary (signal-processing I/O), then hand the discrete located events to the
# substrate as graph structure.  No recognition decision happens in numpy.
# ---------------------------------------------------------------------------

def _energy_contour(M: np.ndarray) -> np.ndarray:
    """The word's scalar energy/loudness contour = sum over bands per frame.  This is
    the 1-D signal whose nested order-N events we parse.  (Summing bands is the
    boundary collapse of the band matrix to the loudness wave — pure I/O.)"""
    M = np.asarray(M, dtype=np.float64)
    c = M.sum(axis=1)
    # light smoothing so the located extrema are the structural ones, not sample
    # jitter — a 3-tap moving average (mechanical I/O, no learned parameter).
    if len(c) >= 3:
        k = np.array([0.25, 0.5, 0.25])
        c = np.convolve(c, k, mode="same")
    return c


def _order_n_diff(contour: np.ndarray, order: int) -> np.ndarray:
    """The order-N finite difference of the contour — the agent's order_n operator
    (nth_order_terms) specialised to a 1-D sample list (np.diff is the same recursive
    Minus).  order 0 returns the contour itself."""
    d = np.asarray(contour, dtype=np.float64)
    for _ in range(order):
        d = np.diff(d)
    return d


def _extrema(sig: np.ndarray):
    """The DISCRETE located events of a 1-D signal = its interior local extrema.
    Returns [(index, sign, magnitude)] where sign = +1 for a local max, -1 for a
    local min, magnitude = |value| at the extremum.  This is the LOCATION step — pure
    signal-processing I/O at the boundary."""
    out = []
    n = len(sig)
    if n < 3:
        return out
    for i in range(1, n - 1):
        a, b, c = sig[i - 1], sig[i], sig[i + 1]
        if b > a and b >= c:
            out.append((i, +1, abs(b)))
        elif b < a and b <= c:
            out.append((i, -1, abs(b)))
    return out


# the orders we parse: 0 = contour (syllable nuclei), 1 = velocity (gesture
# on/off-sets), 2 = curvature (fast transients).  Read off the phonology above, NOT
# tuned to a target.  Each higher order locates FASTER structure nested in the slower.
_ORDERS = (0, 1, 2)


def locate_events(M: np.ndarray):
    """Parse the band matrix into its multi-order DISCRETE event series.

    Returns a list of events, each a dict
        {order, frame, rel_time, sign, magnitude}
    located at the I/O boundary (extrema of the order-N derivative of the energy
    contour).  rel_time = frame / (n_frames-1) in [0,1] (relative position — duration
    invariant).  An order-N event's `frame` is mapped back to the contour's frame
    index (the n-th difference shifts the axis by n/2; we re-centre so the located
    frame indexes the ORIGINAL contour, which the nesting rule needs)."""
    M = np.asarray(M, dtype=np.float64)
    n_frames = M.shape[0]
    if n_frames < 3:
        return []
    contour = _energy_contour(M)
    events = []
    for order in _ORDERS:
        d = _order_n_diff(contour, order)
        if len(d) < 3:
            continue
        # the n-th finite difference is defined on a grid shifted by order/2 frames
        # relative to the original contour; re-centre so `frame` indexes the contour.
        shift = order / 2.0
        for idx, sign, mag in _extrema(d):
            frame = idx + shift
            events.append({
                "order": order,
                "frame": float(frame),
                "rel_time": float(frame / max(n_frames - 1, 1)),
                "sign": int(sign),
                "magnitude": float(mag),
            })
    return events


def _span_of(parent_events, child_frame):
    """The nesting rule: a child (faster, higher-order) event belongs to the SLOWER
    lower-order event whose time-span CONTAINS it — operationalised as the nearest
    lower-order event in time (its span is the interval to its lower-order
    neighbours).  Returns the index into parent_events of the containing parent, or
    None."""
    if not parent_events:
        return None
    best, bd = None, 1e18
    for j, p in enumerate(parent_events):
        d = abs(p["frame"] - child_frame)
        if d < bd:
            bd, best = d, j
    return best


# ---------------------------------------------------------------------------
# Materialise the DISCRETE NESTED EVENT TREE as graph NODES + nesting edges the
# agent owns, then serialise it (depth-first, order-major) into the event-vector
# sequence the native DtwTo matches.  The substrate holds the tree; numpy never
# touches the match.
# ---------------------------------------------------------------------------

def _add_nest_edge(substrate, child, parent):
    """Add a child -> parent `nested_in` edge.  These edges encode the agent's OWN
    event-tree nesting (authorised by the event-tree parse itself, not by the live
    conversational grammar), so they go in via add_edge_unchecked — the same path the
    seed loader uses for edges a composition authorises itself.  Falls back to the
    checked add_edge if the unchecked path is unavailable."""
    try:
        substrate.add_edge_unchecked(child, "nested_in", parent)
    except Exception:
        substrate.add_edge(child, "nested_in", parent)


def build_tree(substrate, M, root_attrs=None):
    """Build the discrete nested order-N event tree for one word IN THE SUBSTRATE.

    nodes  = Event {order, sign, rel_time, magnitude, depth}      (discrete, located)
    edges  = nested_in  child -> parent   (an order-N event nested in the order-(N-1)
             event whose span contains it; order-0 events nest in the word ROOT).

    Returns (root_id, [event_ids]).  This is the agent's graph structure — the TREE
    under the wave.  Within-word magnitude is converted to a LOG RATIO against the
    word's own max so a global talker gain cancels (a within-unit relation)."""
    events = locate_events(M)
    root = substrate.add_node("WordEventTree", dict(root_attrs or {}))
    if not events:
        return root, []
    # within-unit magnitude normaliser (the word's own loudest event) -> ratios,
    # cancelling any global talker gain.  A within-unit relation, not a fitted scale.
    maxmag = max(e["magnitude"] for e in events) or 1.0

    by_order = {o: [e for e in events if e["order"] == o] for o in _ORDERS}
    for o in by_order:
        by_order[o].sort(key=lambda e: e["frame"])

    ids = {}
    event_ids = []
    for o in _ORDERS:
        parents = by_order.get(o - 1, []) if o > 0 else None
        for e in by_order[o]:
            nid = substrate.add_node("Event", {
                "order": e["order"],
                "sign": e["sign"],
                "rel_time": e["rel_time"],
                # log magnitude ratio within the unit (gain-invariant); +1 keeps it
                # finite and non-negative.
                "log_mag": float(np.log1p(e["magnitude"] / maxmag)),
                "depth": e["order"],   # depth in the tree == order here (0 at root)
            })
            ids[id(e)] = nid
            event_ids.append(nid)
            if o == 0:
                _add_nest_edge(substrate, nid, root)
            else:
                pj = _span_of(parents, e["frame"])
                if pj is not None:
                    _add_nest_edge(substrate, nid, ids[id(parents[pj])])
                else:
                    _add_nest_edge(substrate, nid, root)
    return root, event_ids


def serialize_tree(substrate, event_ids):
    """Serialise the discrete event tree into the EVENT-VECTOR SEQUENCE the native
    DtwTo aligns.  Order-major then time-ordered (a depth-first, order-major
    traversal of the nested tree): all the slow order-0 nuclei, then their nested
    order-1 gestures, then the order-2 transients — so the monotone DtwTo alignment
    matches nuclei-to-nuclei, gestures-to-gestures, structurally.

    Each event becomes the vector
        [ order , sign , rel_time , log_mag , depth ]
    NONE of which is an absolute band coordinate:
        order, depth  — WHICH order/level of the hierarchy (the structure)
        sign          — max vs min, a gain-invariant relation
        rel_time      — relative position in the word (duration-invariant)
        log_mag       — within-unit magnitude ratio (global-gain-invariant)
    So the match is over the discrete nested event STRUCTURE, outside the wave."""
    rows = []
    metas = []
    for nid in event_ids:
        a = substrate.node(nid)["attrs"]
        metas.append((a["order"], a["rel_time"]))
    # order-major, then time-ordered within an order
    order_idx = sorted(range(len(event_ids)), key=lambda k: metas[k])
    # FIXED field scales so each component of the event vector contributes
    # comparably to the native (Euclidean) DtwTo cost — the STRUCTURAL fields
    # (order/sign/depth) must not be swamped by, nor swamp, rel_time/log_mag.  These
    # are fixed boundary scales chosen so every field spans ~[0,2], NOT fitted or
    # swept to a target (order/depth already in {0,1,2}; sign in {-1,1} -> *1;
    # rel_time in [0,1] -> *2; log_mag ~[0,0.7] -> *3 to reach ~[0,2]).
    S_ORDER, S_SIGN, S_TIME, S_MAG, S_DEPTH = 1.0, 1.0, 2.0, 3.0, 1.0
    for k in order_idx:
        a = substrate.node(event_ids[k])["attrs"]
        rows.append([
            S_ORDER * float(a["order"]),
            S_SIGN * float(a["sign"]),
            S_TIME * float(a["rel_time"]),
            S_MAG * float(a["log_mag"]),
            S_DEPTH * float(a["depth"]),
        ])
    return rows


def event_sequence(substrate, M):
    """Convenience: band matrix -> discrete nested event tree (in the substrate) ->
    serialized event-vector sequence (the rep the native DtwTo matches).  Returns the
    list-of-vectors; the tree nodes remain in the substrate as the agent's
    structure."""
    _root, eids = build_tree(substrate, M)
    return serialize_tree(substrate, eids)


__all__ = ["locate_events", "build_tree", "serialize_tree", "event_sequence",
           "_ORDERS"]
