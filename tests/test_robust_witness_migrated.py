"""ROBUST / MDL ORDER-N WITNESS — the migrated gate (ROBUST_ORDER_N_WITNESS_PREREG.md).

The real-video FALSIFY (PHYSICS_FALL_REAL_VIDEO_RESULTS.md): the generic order-N
loop FLOORS on a REAL falling ball because the perceived second difference is
*approximately* constant (a run of exact 3s plus ±1–2 glitch cells) but the
exact witness (`diff_pyramid`/`pyramid_order`) requires it to be EXACTLY
constant. Even an ideal bright-blob oracle floors — so the wall is the WITNESS.

This gate proves the fix: a ROBUST/MDL witness (`shape_decode.rs::robust_order`)
that decides order-k by DESCRIPTION LENGTH on the SAME pyramid ("bins propose,
continuous decides") — order-k is witnessed iff modeling difference-level k as a
robust constant (per-component median) + its residual COMPRESSES the stream
below its raw description length. The tolerance FALLS OUT of the integer
bit-costs — no threshold constant.

The witness is OPT-IN (`TimeInfer.robust`), because the exact witness answers a
DIFFERENT question than the robust one — the frame/continuum invariant:

  * EXACT (default) = the IN-FRAME question: "is there an INTEGER order-N
    generator carrying every pair by exact equality?" A fractional (continuous)
    acceleration is NOT expressible in-frame, so the exact witness FLOORS it —
    correctly, which is what mass-recovery / galileo NEED (they invert the
    integer generator). Default behaviour is BYTE-IDENTICAL.
  * ROBUST (opt-in) = the CROSS-FRAME question: "is this the STEPPED observation
    of a continuous order-N parabola (constant to within its own dispersion)?"
    — for real (noisy-integer) perception.

Discriminator (registered before any number):
- a NOISY parabola (exact witness floors) mints ORDER-2 under the robust witness;
- the REAL bright-blob oracle trajectory (the FALSIFY's own d2) mints ORDER-2;
- RANDOM floors under BOTH witnesses (soundness — never mint on noise);
- the exact/synthetic cases are UNCHANGED (default byte-identical; exact order-N
  still fires first for everyone);
- the tolerance falls out (same noise: curvature present -> order-2, absent ->
  floor — no magic number).

Products read from `native.evaluate()` (TUPLES) and the seeded `run_rules`
fixpoint's minted `latent:time` LatentDimension — never a process-pattern wait.
"""
import json
import pytest

from domains.engine_provenance import engine_preamble
engine_preamble()

from substrate.boot_core import boot_core          # noqa: E402
from domains import reflective_faculty as rf        # noqa: E402
from substrate.seed_loader import manifest_for      # noqa: E402

DT = ["pred", "coord:r", "coord:c", "val"]
BASE = [["cell", 0, 0, "red"]]


def _frames_from_offsets(offsets):
    """Frames whose single cell steps along row `r` by `offsets[i]` between
    frame i and i+1 — so the per-pair translate offset stream IS `offsets`
    (the "velocity"), and its finite-difference structure is what the witness
    recovers."""
    out = [[["cell", 0, 0, "red"]]]
    r = 0
    for dv in offsets:
        r += dv
        out.append([["cell", r, 0, "red"]])
    return out


def _frames_from_positions(cy):
    """Frames whose single cell sits at row cy[i] — a raw perceived trajectory
    (the per-pair offset stream is its first difference / velocity)."""
    return [[["cell", int(round(y)), 0, "red"]] for y in cy]


def _boot():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("time_axis"), ag)
    s.set_attr(ag, "time_infer_enabled", 1.0)
    s.add_node("ShapeSignature", {"name": "base_L", "signature": json.dumps(BASE),
               "kind": "faculty", "faculty": "base_L", "dim_types": DT})
    return s, ag, native


def _eval(frames, field, *, robust):
    _, _, native = _boot()
    return native.evaluate(
        {"type": "TimeInfer", "sequence": {"type": "Lit", "value": frames},
         "codebook_type": "ShapeSignature", "max_b": 8, "field": field,
         "robust": robust}, {})


def _run(frames, status):
    """run_rules fixpoint; returns (obs status, list of latent:time mints as
    (kind, order, coeffs, window)). status 'motion_seq' = default (exact) rule;
    'motion_seq_robust' = the robust-witness rule."""
    s, ag, native = _boot()
    o = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                   "status": status, "key": ["motion"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    st = s.node(o)["attrs"].get("status")
    lds = []
    for n in s.nodes("LatentDimension"):
        a = s.node(n)["attrs"]
        if a.get("name") == "latent:time":
            lds.append((a.get("generator_kind"), a.get("order"),
                        tuple(a.get("coeffs") or ()), a.get("window")))
    return st, lds


# per-pair offset (velocity) streams
NOISY_PARABOLA = [3, 7, 8, 12, 16, 17, 21, 25, 27]   # accel ~3 with jitter — exact floors
RANDOM = [-6, 5, 2, -8, 8, 1, -3, 7, 4]              # no structure at any order
CONST_ACCEL = [1, 2, 3, 4, 5, 6]                     # exact order-2 (integer Euler)
CONST_VEL = [2, 2, 2, 2, 2, 2]                       # exact order-1
ORDER3 = [1, 2, 4, 7, 11, 16]                        # exact order-3

# the REAL bright-blob oracle second difference (PHYSICS_FALL_REAL_VIDEO_RESULTS.md
# §3, N=14): five exact-3s plus ±glitch outliers — approximately, not exactly,
# constant. Reconstruct a perceived cy from it (v0 arbitrary; the order is
# invariant to the integration constants).
ORACLE_D2 = [5, 4, 3, 3, 3, 3, 3, -13, 9, 6, 3, -4]


def _cy_from_d2(d2, v0=10, cy0=0):
    vel = [v0]
    for a in d2:
        vel.append(vel[-1] + a)
    cy = [cy0]
    for v in vel:
        cy.append(cy[-1] + v)
    return cy


# ───────────────────────── headline: the noisy parabola mints order-2 ─────────

def test_noisy_parabola_mints_order_2_under_robust_witness():
    """A near-constant-acceleration velocity stream with quantization jitter:
    the EXACT witness floors (no all-equal difference level), the ROBUST witness
    sees the acceleration is constant to within its dispersion and mints
    ORDER-2. PRODUCT first (tuples)."""
    frames = _frames_from_offsets(NOISY_PARABOLA)
    assert _eval(frames, "explained", robust=False) is False       # exact floors
    assert _eval(frames, "explained", robust=True) is True         # robust mints
    assert _eval(frames, "order", robust=True) == 2
    assert _eval(frames, "kind", robust=True) == "translate"
    # GRAPH: the robust run_rules rule mints latent:time order-2.
    st, lds = _run(frames, "motion_seq_robust")
    assert st == "time_inferred"
    assert len(lds) == 1 and lds[0][0] == "translate" and lds[0][1] == 2


def test_real_bright_blob_oracle_trajectory_mints_order_2():
    """THE FALSIFY, RESOLVED. The cleanest real perception of the falling ball —
    the bright-blob oracle whose second difference is the FALSIFY doc's own
    [5,4,3,3,3,3,3,-13,9,6,3,-4] (five exact-3s + ±glitch outliers) — FLOORED
    under the exact witness (PHYSICS_FALL_REAL_VIDEO_RESULTS.md). Under the
    robust witness it mints ORDER-2, the median cutting through the glitch
    outliers. Physics from real perceived video, read from the graph."""
    cy = _cy_from_d2(ORACLE_D2)
    frames = _frames_from_positions(cy)
    assert _eval(frames, "explained", robust=False) is False       # the FALSIFY
    assert _eval(frames, "order", robust=True) == 2                # RESOLVED
    st, lds = _run(frames, "motion_seq_robust")
    assert st == "time_inferred"
    assert len(lds) == 1 and lds[0][1] == 2                        # order 2, from the graph
    # the recovered acceleration is the robust (median) constant, ~3 cells.
    coeffs = lds[0][2]
    assert coeffs[1][0] == 3, f"acceleration coeff should be the median 3, got {coeffs}"


# ───────────────────────── soundness: random must FLOOR ───────────────────────

def test_random_floors_under_both_witnesses():
    """The load-bearing soundness bar: a genuine-noise stream mints NOTHING even
    with the tolerant witness — differencing amplifies its spread, so no order
    compresses below raw. A witness loose enough to accept it would be WRONG."""
    frames = _frames_from_offsets(RANDOM)
    assert _eval(frames, "explained", robust=False) is False
    assert _eval(frames, "explained", robust=True) is False        # still floors
    assert _eval(frames, "order", robust=True) == 0
    st, lds = _run(frames, "motion_seq_robust")
    assert st == "time_none" and lds == []


def test_several_random_streams_all_floor():
    """Multiple independent noise streams — none may mint at any order."""
    randoms = [
        [-6, 5, 2, -8, 8, 1, -3, 7],
        [4, -9, 3, 6, -2, 10, -7, 1],
        [0, 11, -4, 5, -6, 2, 9, -8],
        [13, -2, 7, -11, 4, 6, -9, 3],
    ]
    for r in randoms:
        frames = _frames_from_offsets(r)
        assert _eval(frames, "explained", robust=True) is False, f"{r} must floor"


# ───────────────────── additive: exact / synthetic cases UNCHANGED ────────────

def test_exact_cases_are_unchanged_default_byte_identical():
    """The exact witness fires FIRST for everyone; the default (exact) verdict is
    byte-identical. Integer-Euler order-1/2/3 mint exactly as before, under BOTH
    the default and the robust flag (robust never suppresses an exact mint)."""
    for offs, want in [(CONST_VEL, 1), (CONST_ACCEL, 2), (ORDER3, 3)]:
        frames = _frames_from_offsets(offs)
        assert _eval(frames, "order", robust=False) == want
        assert _eval(frames, "order", robust=True) == want          # exact still fires first
        assert _eval(frames, "explained", robust=False) is True
    # const_accel's exact order-1 offset tuple is unchanged.
    fa = _frames_from_offsets(CONST_ACCEL)
    assert _eval(fa, "kind", robust=False) == "translate"


def test_default_witness_floors_the_noisy_parabola_byte_identical():
    """The OPT-IN guarantee: without the robust flag the noisy parabola floors
    exactly as it always did — so every existing consumer (mass recovery /
    galileo, which need the exact integer generator) is byte-unchanged. The
    robust mint exists only for a caller that explicitly asks the cross-frame
    question."""
    frames = _frames_from_offsets(NOISY_PARABOLA)
    assert _eval(frames, "explained", robust=False) is False
    assert _eval(frames, "order", robust=False) == 0
    # and the default run_rules rule floors it (time_none), not time_inferred.
    st, lds = _run(frames, "motion_seq")
    assert st == "time_none" and lds == []


# ─────────────────── §13: the tolerance FALLS OUT (no magic number) ───────────

def test_tolerance_falls_out_no_magic_number():
    """With the SAME fixed noise pattern, whether order-2 mints is decided by
    whether the CURVATURE rises above the noise — the crossover is set by the
    data's own description length, NOT a threshold constant. Curvature present
    -> order-2; the SAME noise with NO curvature (constant velocity) -> floors.
    There is no numeric tolerance anywhere in the witness to point at."""
    noise = [1, -1, 1, 0, -1, 1, 0, -1]
    # curvature present (accel 4 >> noise): compresses -> order-2.
    curved, v = [], 2
    for n in noise:
        curved.append(v); v += 4 + n
    assert _eval(_frames_from_offsets(curved), "order", robust=True) == 2
    # curvature absent (accel 0, SAME noise): near-constant velocity, no second
    # order structure -> the robust witness declines order-2 (floors).
    flat, v = [], 2
    for n in noise:
        flat.append(v); v += n
    assert _eval(_frames_from_offsets(flat), "explained", robust=True) is False
