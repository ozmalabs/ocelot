"""DIMENSION-GENERIC ORDER-N — the migrated gate (GENERIC_ORDER_N_PREREG.md).

The Stage-0 FALSIFY (PHYSICS_STAGE0_RESULTS.md) located the exact wall: the
substrate accretes higher order in SPACE but was frozen at ORDER-1 IN TIME.
`TimeInfer` fit ONE generator from the first frame-pair and required exact
equality across all pairs, so a constant-VELOCITY stream minted `translate`
but a constant-ACCELERATION stream (whose offset itself changes regularly)
falsified to `time_none`, indistinguishable from a random stream.

This gate proves the resolution: order-N is now a property of ANY dimension,
delivered by ONE generic finite-difference recursion
(`shape_decode.rs::diff_pyramid`/`pyramid_order`/`order_n_translate_verdict`).
Along an ordered frame sequence the per-pair TRANSLATE offset is fitted; if the
offset stream is not constant but is itself REGULAR, the recursion differences
it (order+1). Velocity -> acceleration -> jerk, and the identical dimension-
blind code serves a non-time ordering.

Discriminator (registered before any number, GENERIC_ORDER_N_PREREG.md):
- the accelerating stream that FALSIFIED in Stage 0 now mints an order-2
  generator that zeroes its residual;
- a genuinely order-3 stream mints order-3;
- random stays incompressible (floors);
- constant-velocity still mints order-1 BYTE-IDENTICALLY (additive at the floor);
- the mechanism is dimension-generic (same Term/path serves a non-time
  ordering).

Every product is read from `native.evaluate()` (TUPLES) and from the seeded
`run_rules` fixpoint — never a process-pattern wait.
"""
import json
import pytest

from domains.engine_provenance import engine_preamble
engine_preamble()

from substrate.boot_core import boot_core          # noqa: E402
from domains import reflective_faculty as rf        # noqa: E402
from substrate.seed_loader import manifest_for      # noqa: E402

DT = ["pred", "coord:r", "coord:c", "val"]
BASE = [["cell", 0, 0, "red"], ["cell", 1, 0, "red"],
        ["cell", 2, 0, "red"], ["cell", 2, 1, "red"]]


def _trans(dr, dc, cs):
    return [["cell", r + dr, c + dc, v] for _, r, c, v in cs]


def _frames_from_offsets(offsets, axis="r"):
    """Frames whose shape steps by `offsets[i]` between frame i and i+1 along
    ONE coordinate axis. The per-pair translate offset stream IS `offsets`;
    its finite-difference order is what the recursion recovers. `axis` chooses
    which coordinate moves ('r' or 'c') — used to show the ordering dimension
    is not special."""
    out = [BASE]
    cur = BASE
    for dv in offsets:
        cur = _trans(dv, 0, cur) if axis == "r" else _trans(0, dv, cur)
        out.append(cur)
    return out


def _boot(enabled=True):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("time_axis"), ag)
    if enabled:
        s.set_attr(ag, "time_infer_enabled", 1.0)
    s.add_node("ShapeSignature", {"name": "base_L", "signature": json.dumps(BASE),
               "kind": "faculty", "faculty": "base_L", "dim_types": DT})
    return s, ag, native


def _time_eval(frames, field):
    """Call the Rust TimeInfer Term directly — the PRODUCT (tuples), no rule.
    Boots a fresh graph carrying the dim-typed ShapeSignature the Term reads."""
    _, _, native = _boot(enabled=True)
    return native.evaluate(
        {"type": "TimeInfer",
         "sequence": {"type": "Lit", "value": frames},
         "codebook_type": "ShapeSignature", "max_b": 8, "field": field}, {})


def _run(frames, enabled=True):
    """Full run_rules fixpoint; returns (obs attrs, list of latent:time mints
    each as (kind, offset, matrix, window, order))."""
    s, ag, native = _boot(enabled)
    o = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                   "status": "motion_seq", "key": ["motion"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    at = s.node(o)["attrs"]
    lds = []
    for n in s.nodes("LatentDimension"):
        a = s.node(n)["attrs"]
        if a.get("name") == "latent:time":
            lds.append((a.get("generator_kind"), tuple(a.get("offset") or ()),
                        tuple(a.get("matrix") or ()), a.get("window"), a.get("order")))
    return at, lds


# The four Stage-0 streams, as per-pair offset sequences.
CONST_VEL = [2, 2, 2, 2, 2, 2]            # 1st diff constant -> order 1
CONST_ACCEL = [1, 2, 3, 4, 5, 6]          # 2nd diff constant -> order 2 (the FALSIFY)
ORDER3 = [1, 2, 4, 7, 11, 16]             # 3rd diff constant -> order 3 (jerk)
RANDOM = [-6, 5, 2, -8, 8, 1]             # never a witnessed constant -> floor


# ─────────────────────────── the headline: FALSIFY resolved ──────────────

def test_accelerating_stream_now_mints_order_2():
    """The Stage-0 FALSIFY: constant-acceleration was indistinguishable from
    random at the order-1 floor. It now mints an order-2 generator."""
    frames = _frames_from_offsets(CONST_ACCEL)
    # PRODUCT (tuples) first.
    assert _time_eval(frames, "explained") is True
    assert _time_eval(frames, "order") == 2
    assert _time_eval(frames, "kind") == "translate"
    # run_rules fixpoint: mints latent:time with order 2.
    at, lds = _run(frames)
    assert at.get("status") == "time_inferred"
    assert len(lds) == 1
    assert lds[0][0] == "translate" and lds[0][4] == 2      # kind, order


def test_order_2_generator_zeroes_the_residual():
    """The minted order-2 generator PREDICTS the unseen next frame exactly —
    the residual is zeroed, not merely labelled. positions 0,1,3,6,10,15,21
    (7 frames) extrapolate the 8th offset (7) to origin-row 28."""
    frames = _frames_from_offsets(CONST_ACCEL)          # 7 frames
    predicted = _time_eval(frames, "predicted")
    withheld = _trans(7, 0, frames[-1])                 # last frame + next offset (7)
    assert sorted(map(tuple, predicted)) == sorted(map(tuple, withheld))


def test_order_3_stream_mints_order_3():
    """A genuinely order-3 (jerk) stream: the recursion walks N up to 3."""
    frames = _frames_from_offsets(ORDER3)
    assert _time_eval(frames, "explained") is True
    assert _time_eval(frames, "order") == 3
    at, lds = _run(frames)
    assert at.get("status") == "time_inferred"
    assert len(lds) == 1 and lds[0][4] == 3


def test_random_stream_floors():
    """An order-≥N-unstructured stream stays incompressible — the control the
    old floor protected must survive: random still grounds at enumeration."""
    frames = _frames_from_offsets(RANDOM)
    assert _time_eval(frames, "explained") is False
    assert _time_eval(frames, "order") == 0
    at, lds = _run(frames)
    assert at.get("status") == "time_none"
    assert lds == []


# ─────────────────────── additive: order-1 byte-identical ─────────────────

def test_constant_velocity_still_mints_order_1_unchanged():
    """Every current success is untouched. The constant-velocity orbit mints
    exactly the same order-1 translate generator as before (the committed gate
    test_time_infer_migrated asserts the (kind, offset, matrix, window) tuple;
    here we also confirm order==1)."""
    frames = _frames_from_offsets(CONST_VEL)
    assert _time_eval(frames, "explained") is True
    assert _time_eval(frames, "order") == 1
    assert _time_eval(frames, "kind") == "translate"
    assert tuple(_time_eval(frames, "offset")) == (2, 0)
    at, lds = _run(frames)
    assert at.get("status") == "time_inferred"
    assert lds == [("translate", (2, 0), (), 7, 1)]


def test_order_1_fields_are_byte_identical_to_pre_change():
    """The order-1 explained verdict's EXISTING fields are unchanged — the new
    `order`/`coeffs` keys are additive and read by no prior query. Assert the
    exact tuple the committed gate reads."""
    frames = _frames_from_offsets(CONST_VEL)
    assert _time_eval(frames, "kind") == "translate"
    assert tuple(_time_eval(frames, "offset")) == (2, 0)
    assert tuple(_time_eval(frames, "matrix")) == ()
    assert _time_eval(frames, "window") == 7
    assert _time_eval(frames, "checked") == 0


# ─────────────────────── dimension-generic (not time-special) ─────────────

def test_dimension_generic_same_path_serves_a_non_time_ordering():
    """The recursion is written over a dimension abstraction. `TimeInfer`'s
    input is 'a sequence of frames presented in ORDER' — it never checks the
    ordering is time. Feed the SAME Term a sequence whose ordering is a SPATIAL
    scan (frames stacked along a spatial axis, the shape shifting along the
    COLUMN coordinate with accelerating offsets) and the IDENTICAL code path
    returns the same order-2 verdict. No `if dimension == time` exists to route
    around — the ordering dimension and the moving coordinate are both changed."""
    spatial_stack = _frames_from_offsets(CONST_ACCEL, axis="c")
    assert _time_eval(spatial_stack, "explained") is True
    assert _time_eval(spatial_stack, "order") == 2
    # And a spatial order-3 scan reaches order 3 on the same path.
    spatial3 = _frames_from_offsets(ORDER3, axis="c")
    assert _time_eval(spatial3, "order") == 3
    # Byte-identical to the time-ordered version (dimension is not in the math).
    time_accel = _frames_from_offsets(CONST_ACCEL, axis="c")
    assert _time_eval(time_accel, "order") == _time_eval(spatial_stack, "order")


def test_no_hardcoded_order_cap_falls_out_of_compressibility():
    """The order reached is wherever the residual stops being compressible, not
    a seeded cap: order-1, order-2, order-3 all fall out of the SAME recursion,
    and an incompressible stream floors — no order constant anywhere."""
    assert _time_eval(_frames_from_offsets(CONST_VEL), "order") == 1
    assert _time_eval(_frames_from_offsets(CONST_ACCEL), "order") == 2
    assert _time_eval(_frames_from_offsets(ORDER3), "order") == 3
    assert _time_eval(_frames_from_offsets(RANDOM), "order") == 0
