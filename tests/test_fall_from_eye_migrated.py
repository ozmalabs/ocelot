"""PHYSICS FROM OBSERVATION — the fall DISCOVERED by the eye (the gate).

Pre-registration: `PHYSICS_FALL_FROM_EYE_PREREG.md`. The low-res EYE watches an
object fall under ONE untuned constant gravity (g=1, semi-implicit Euler integer
physics). The world's ONLY output is pixels (a 0/1 cell field). The eye
(`Substrate::segment_and_track`) carves the falling blob as a persistent
`Region`; the generic order-N loop (`GENERIC_ORDER_N_RESULTS.md`, the generalized
`TimeInfer`) runs over that tracked object's PERCEIVED `cy` trajectory and mints
the ORDER-2 generator — un-seeded, no hand-set order. The substrate discovers,
from what it SAW, that the fall is uniformly accelerated.

Discriminator (registered before any number):
- untuned fall  -> order-2 minted from the perceived cy trajectory;
- constant velocity -> order-1 (NOT order-2);
- static -> nothing (no acceleration minted);
- noise / no coherent object -> nothing.

Every product is read FROM THE GRAPH: the Rust Term via `native.evaluate()`
(TUPLES) and the seeded `run_rules` fixpoint's minted
`LatentDimension.order` — never a process-pattern wait.

MEASURED verdict (2026-07-22): CONFIRM — the DEGRADE below is SUPERSEDED by the
velocity-predictive cross-frame association fix in `segment_and_track`.

The DEGRADE this file used to assert (kept here for the record): with untuned g=1
and a plain 3×3 blob (span 3, nearest-centroid `radius = span+2 = 5`) the eye
held ONE Region id for only the first K=6 frames; at frame 6 the fall's per-frame
displacement (6) exceeded span+2 (5), the eye lost identity (death+birth) and the
perceived trajectory FRAGMENTED. That was a bounded caveat, refused a tuning
rescue, and named its own fix: velocity-predictive association.

THE FIX (now built, `substrate.rs::segment_and_track`, Phase B): when the
existing overlap/last-centroid match would DIE, the eye matches a new region
against the prior's PREDICTED centroid (`prior.centroid + prior.per-frame
displacement`) instead of its last centroid. The quantity that must fall within
`span+2` is then no longer the object's full VELOCITY (which grows unboundedly)
but only its ACCELERATION — the residual a constant-velocity prediction leaves,
small and roughly constant for smooth motion. So a smoothly-accelerating object
STAYS associated. First-order (constant-velocity) prediction only; additive
(overlap + last-centroid paths byte-identical; predictive only rescues what would
otherwise birth); guarded against false association (no prediction for a
just-born/static prior; predicted match must beat birth; a disjoint newcomer is
not adopted).

MEASURED with the fix: the untuned g=1 fall now tracks the WHOLE in-field fall as
ONE Region (7/7 frames, no fragmentation — velocity reaches 6 > the old radius 5,
yet identity holds); a taller field falls 15/15 frames as one Region with
velocity reaching 14 ≫ radius 5 (reach bounded by acceleration, not velocity);
order-N mints order-2 with margin (7 samples vs the witness minimum of 4).
"""
import numpy as np
import pytest

from domains.engine_provenance import engine_preamble
engine_preamble()

from domains import falling_world as fw            # noqa: E402

# --- one plain, untuned world geometry, shared by every arm -----------------
H, W = 30, 18
K = 3               # a plain 3x3 blob  -> span 3, nearest-centroid radius 5
LEFT = 7
G = 1               # the untuned gravity (plainest discrete gravity)
NOISE_SEED = 138000  # inside the pre-registered block 138000-138999


def _perceive_run(pixel_frames):
    """Boot substrate, run the eye over the pixels, return (s, ag, native, game,
    cell_ids, track). The eye's carve is the ONLY thing that reaches the graph."""
    s, ag, native = fw.boot_falling()
    game, cell_ids = fw.setup_world(native, H, W)
    track = fw.perceive(native, game, cell_ids, H, W, pixel_frames)
    return s, ag, native, game, cell_ids, track


# ─────────────────────────── the headline ──────────────────────────────────

def test_untuned_fall_is_discovered_as_order_2_from_the_perceived_cy():
    """The eye watches the untuned fall; order-N mints ORDER-2 from the
    PERCEIVED cy trajectory — read from the graph, un-seeded."""
    pix = fw.fall_pixels(H, W, K, G, left=LEFT)
    s, ag, native, game, cell_ids, track = _perceive_run(pix)

    run = fw.longest_continuous_run(track)
    # POST-FIX: the eye now holds ONE id for the WHOLE in-field fall — no
    # fragmentation — and comfortably past the order-2 witness minimum (margin).
    assert len(run) == len(track), "the whole fall must track as ONE continuous run"
    assert len(run) > fw.MIN_ORBIT, "order-2 with MARGIN, not just the bare witness"
    ids = {b["id"] for b in run}
    assert len(ids) == 1, "the continuous run must be ONE persistent Region id"

    cy = [b["cy"] for b in run]
    cx = [b["cx"] for b in run]
    # the perceived fall is monotone-accelerating (2nd difference constant = g)
    assert cy == sorted(cy) and cy[0] < cy[-1]
    d1 = [b - a for a, b in zip(cy, cy[1:])]
    d2 = [b - a for a, b in zip(d1, d1[1:])]
    assert all(abs(x - G) < 1e-9 for x in d2), f"2nd diff not constant g: {d2}"

    # PRODUCT first: the Rust Term's verdict on the perceived points (TUPLES).
    frames = [[["obj", int(round(y)), int(round(x)), "obj"]] for y, x in zip(cy, cx)]
    assert native.evaluate(
        {"type": "TimeInfer", "sequence": {"type": "Lit", "value": frames},
         "codebook_type": "ShapeSignature", "max_b": 8, "field": "explained"}, {}) is True
    assert native.evaluate(
        {"type": "TimeInfer", "sequence": {"type": "Lit", "value": frames},
         "codebook_type": "ShapeSignature", "max_b": 8, "field": "order"}, {}) == 2

    # GRAPH: the seeded run_rules fixpoint mints latent:time with order 2.
    status, mints = fw.discover_order(s, ag, native, cy, cx)
    assert status == "time_inferred"
    assert len(mints) == 1
    kind, order, coeffs, offset = mints[0]
    assert kind == "translate"
    assert order == 2, f"expected order-2 (uniform acceleration), got {order}"


def test_velocity_prediction_tracks_the_fall_through_without_fragmentation():
    """SUPERSEDES the old DEGRADE (`test_eye_fragments_..._deg_boundary`). With
    velocity-predictive association the untuned fall no longer fragments: the eye
    holds ONE Region id for the WHOLE in-field fall, even though the fall's
    per-frame displacement (velocity) grows past the old nearest-centroid radius
    (span+2 = 5). The proof the FIX is doing the work: the perceived velocity
    (drow) EXCEEDS span+2 somewhere inside the continuous run — the exact frame
    where the old last-centroid match would have died — yet identity held via
    the predicted centroid, whose residual is only the (small, constant)
    acceleration."""
    pix = fw.fall_pixels(H, W, K, G, left=LEFT)
    s, ag, native, game, cell_ids, track = _perceive_run(pix)

    ids = [b["id"] if b else None for b in track]
    run = fw.longest_continuous_run(track)
    span = K

    # ONE id, the whole fall — no death+birth anywhere in-field.
    assert len(run) == len(track), "the whole fall must track as ONE run (no fragmentation)"
    assert None not in ids
    assert len(set(ids)) == 1, "exactly ONE Region id across every frame of the fall"

    # The fix is doing real work: velocity outran the OLD radius inside the run.
    max_drow = max(b["drow"] for b in run)
    assert max_drow > span + 2, (
        "if velocity never exceeded span+2 the old matcher would have sufficed; "
        f"this scenario only proves the fix when velocity>{span+2} (got {max_drow})")
    # yet every step's velocity residual after constant-velocity prediction (the
    # perceived acceleration) stayed within span+2 — that is why identity held.
    drows = [b["drow"] for b in run]
    accel = [b - a for a, b in zip(drows, drows[1:])]
    assert all(abs(x) <= span + 2 for x in accel), \
        f"the acceleration residual (not velocity) must stay within span+2: {accel}"


def test_taller_field_shows_reach_bounded_by_acceleration_not_velocity():
    """REACH characterization (same untuned physics g=1, plain 3×3 blob — only a
    taller arena, which makes the fall LONGER and FASTER, the OPPOSITE of the
    forbidden 'keep it sub-span' tuning cheat). The fall runs many frames; the
    eye tracks ALL of them as ONE Region while the velocity grows far beyond the
    radius — because the predicted-centroid residual it must absorb is the
    constant acceleration (g=1), not the growing velocity. Order-N still mints
    order-2 from the long perceived trajectory."""
    TALL_H = 120
    pix = fw.fall_pixels(TALL_H, W, K, G, left=LEFT)
    s, ag, native = fw.boot_falling()
    game, cell_ids = fw.setup_world(native, TALL_H, W)
    track = fw.perceive(native, game, cell_ids, TALL_H, W, pix)

    run = fw.longest_continuous_run(track)
    assert len(run) == len(track) and len(track) > 10, \
        f"a tall fall must track many frames as one run (got {len(run)}/{len(track)})"
    assert len({b["id"] for b in run}) == 1
    # velocity reaches FAR beyond the radius (span+2 = 5) yet identity holds.
    assert max(b["drow"] for b in run) > 2 * (K + 2), \
        "velocity must vastly exceed the radius — proving reach is not velocity-bounded"

    cy = [b["cy"] for b in run]
    cx = [b["cx"] for b in run]
    d1 = [b - a for a, b in zip(cy, cy[1:])]
    d2 = [b - a for a, b in zip(d1, d1[1:])]
    assert all(abs(x - G) < 1e-9 for x in d2), f"2nd diff not constant g: {d2}"
    status, mints = fw.discover_order(s, ag, native, cy, cx)
    assert status == "time_inferred"
    assert len(mints) == 1 and mints[0][1] == 2, "the long fall still mints order-2"


# ─────────────── false-association controls (the fix must not over-reach) ────

def _blob_frame(top, left):
    """A single 3×3 blob at (top,left) on the shared H×W field — pure pixels."""
    return fw.render_blob(H, W, top, left, K)


def test_predictive_does_not_adopt_a_disjoint_newcomer():
    """GUARD: extending the match reach must NOT let a dead object's prediction
    swallow an unrelated new object. A blob establishes a rightward velocity,
    then DISAPPEARS while a brand-new blob appears far from where the mover was
    predicted to continue. The mover's Region must DIE (its id gone) and the
    newcomer must be a fresh BIRTH — never inherit the mover's identity."""
    frames = [
        _blob_frame(5, 2),    # mover
        _blob_frame(5, 4),    # mover +2 col
        _blob_frame(5, 6),    # mover +2 col  -> velocity (dcol≈+2) established
        _blob_frame(20, 2),   # mover GONE; newcomer far below-left (away from the
                              #   predicted continuation, which is further RIGHT)
    ]
    s, ag, native, game, cell_ids, track = _perceive_run(frames)
    ids = [b["id"] if b else None for b in track]
    mover_id = ids[0]
    assert ids[0] == ids[1] == ids[2] == mover_id, "the mover must track while present"
    newcomer_id = ids[3]
    assert newcomer_id is not None and newcomer_id != mover_id, \
        "the disjoint newcomer must be a fresh BIRTH, not the mover's identity"
    # the mover's Region truly died — no live Region still carries its id.
    live_ids = {b["id"] for b in fw.read_regions(native, game)}
    assert mover_id not in live_ids, "the vanished mover's Region must be reaped (death)"


def test_two_crossing_objects_keep_distinct_ids():
    """GUARD: two same-value objects on different rows crossing in column (never
    sharing a row, so they never merge into one component) are each tracked by
    overlap in Phase A — the predictive fallback never fires — and keep TWO
    stable, distinct ids throughout. Proves the change does not disturb ordinary
    multi-object tracking (additivity under crossing)."""
    frames = []
    for t in range(8):
        g = [0] * (H * W)
        for r in range(3, 3 + K):               # object 1: row 3, drifting right
            for c in range(2 + t, 2 + t + K):
                if 0 <= c < W:
                    g[r * W + c] = 1
        for r in range(12, 12 + K):             # object 2: row 12, drifting left
            for c in range(12 - t, 12 - t + K):
                if 0 <= c < W:
                    g[r * W + c] = 1
        frames.append(g)

    s, ag, native = fw.boot_falling()
    game, cell_ids = fw.setup_world(native, H, W)
    per_frame = []
    for fi, vals in enumerate(frames):
        native.set_attr(game, "frame", float(fi))
        native.segment(game, H, W, vals, cell_ids)
        ng = sorted(r["id"] for r in fw.read_regions(native, game) if r["is_ground"] == 0.0)
        per_frame.append(ng)

    assert all(len(fr) == 2 for fr in per_frame), "two objects present every frame"
    all_ids = {i for fr in per_frame for i in fr}
    assert len(all_ids) == 2, f"exactly TWO stable ids across the crossing, got {all_ids}"


# ─────────────────────────────── controls ──────────────────────────────────

def test_constant_velocity_is_discovered_as_order_1_not_order_2():
    """A blob crossing the field at CONSTANT velocity is tracked continuously
    (no fragmentation — displacement stays within span+2) and order-N mints
    ORDER-1, never order-2."""
    pix = fw.fall_pixels(H, W, K, g=0, left=LEFT, v0=2)   # g=0 -> constant velocity
    s, ag, native, game, cell_ids, track = _perceive_run(pix)

    run = fw.longest_continuous_run(track)
    assert len(run) == len(track), "constant velocity must track continuously"
    assert len({b["id"] for b in run}) == 1
    cy = [b["cy"] for b in run]
    cx = [b["cx"] for b in run]
    d1 = [b - a for a, b in zip(cy, cy[1:])]
    assert all(x == d1[0] and x != 0 for x in d1)          # constant nonzero velocity

    assert native.evaluate(
        {"type": "TimeInfer", "sequence": {"type": "Lit",
         "value": [[["obj", int(round(y)), int(round(x)), "obj"]]
                   for y, x in zip(cy, cx)]},
         "codebook_type": "ShapeSignature", "max_b": 8, "field": "order"}, {}) == 1

    status, mints = fw.discover_order(s, ag, native, cy, cx)
    assert status == "time_inferred"
    assert len(mints) == 1 and mints[0][1] == 1            # order 1, not 2


def test_static_object_mints_no_acceleration():
    """A STATIC blob: tracked continuously, perceived cy constant, order-N mints
    NOTHING (the all-zero offset stream is the honest floor -> time_none)."""
    pix = fw.static_pixels(H, W, K, top=5, left=LEFT, n=8)
    s, ag, native, game, cell_ids, track = _perceive_run(pix)

    run = fw.longest_continuous_run(track)
    assert len(run) == len(track) and len({b["id"] for b in run}) == 1
    cy = [b["cy"] for b in run]
    cx = [b["cx"] for b in run]
    assert len(set(cy)) == 1, "static object must have constant perceived cy"

    status, mints = fw.discover_order(s, ag, native, cy, cx)
    assert mints == [], "a static object must mint NO acceleration"
    assert status == "time_none"


def test_noise_has_no_coherent_object_and_mints_nothing():
    """NOISE: incoherent random pixels carve no persistent object — the eye
    holds no Region id for the order-2 witness minimum, so there is no
    trajectory to feed and nothing is minted."""
    rng = np.random.default_rng(NOISE_SEED)
    pix = fw.noise_pixels(H, W, rng, n=8)
    s, ag, native, game, cell_ids, track = _perceive_run(pix)

    run = fw.longest_continuous_run(track)
    # no id persists for the order-2 witness minimum -> no coherent object
    assert len(run) < fw.MIN_ORBIT, f"noise unexpectedly held an object: {len(run)}"
    # and there is no single-object trajectory to discover a law from
    if len(run) >= 2:
        # even the coincidental short run must not mint an ACCELERATION
        status, mints = fw.discover_order(s, ag, native,
                                          [b["cy"] for b in run],
                                          [b["cx"] for b in run])
        assert all(m[1] != 2 for m in mints), "noise must never mint order-2"


# ───────────────────── no published kinematics (the genuine bar) ────────────

_FORBIDDEN_KINEMATIC_KEYS = {
    "position", "pos", "velocity", "vel", "vy", "vx", "speed",
    "acceleration", "accel", "accy", "gravity", "mass",
    "on_ground", "grounded", "regime", "y", "v", "g",
}


def test_world_publishes_no_kinematics_only_pixels_and_perception():
    """The genuine bar: the WORLD graph carries only pixels + the eye's own
    Region perception. It NEVER publishes the object's ground-truth position,
    velocity, acceleration, mass, or an on_ground/regime flag.

    The world graph is exactly: the `game` hub, the grid `Cell` nodes, and the
    `Region` nodes the EYE carved (reachable via `has_region`). Scan all three:
      * the hub carries only `frame` (a tick counter, not object state);
      * every grid cell carries NO attribute at all (no coordinate is published —
        `segment_and_track` addresses cells positionally, so the object's row/col
        never becomes a node attr);
      * no forbidden kinematic key appears anywhere in the world graph;
      * the ONLY object-state present is the eye's perceived carve (Region.cy/cx/
        drow) — which is the eye's, not a world-published truth (the blob's true
        y/v/g exist only as Python locals inside `fall_pixels`).
    """
    pix = fw.fall_pixels(H, W, K, G, left=LEFT)
    s, ag, native, game, cell_ids, track = _perceive_run(pix)

    # the hub: only a frame counter
    hub_attrs = native.node(game)["attrs"]
    assert set(hub_attrs.keys()) <= {"frame"}, f"hub leaked non-frame attrs: {hub_attrs}"

    # every grid cell: NO attributes at all (no published coordinate)
    cell_set = set(cell_ids)
    cell_nodes = [n for n in native.nodes("WorldInstance")
                  if int(str(n).lstrip("#")) in cell_set]
    assert len(cell_nodes) == len(cell_ids)
    for n in cell_nodes:
        assert native.node(n)["attrs"] == {}, \
            "grid cells must carry NO coordinate/kinematic attribute"

    # the eye's Region carve — the only object-state in the world graph
    region_nodes = list(native.neighbours(game, "has_region"))
    world_keys = set(hub_attrs.keys())
    for n in region_nodes:
        world_keys |= set(native.node(n)["attrs"].keys())
    leaked = world_keys & _FORBIDDEN_KINEMATIC_KEYS
    assert not leaked, f"world graph leaked kinematic attribute(s): {leaked}"

    # the Region carries the eye's perceived centroid (cy) — proof the object's
    # state is PERCEIVED, never published: no world node other than a Region has
    # any numeric object coordinate.
    assert any("cy" in native.node(n)["attrs"] for n in region_nodes)
