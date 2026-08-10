"""EYE RESOLUTION vs the free-fall acceleration signal — the migrated gate
(block 147000-147999, VISION_EYE_RESOLUTION_PREREG/RESULTS).

What the rung MEASURED (and what this gate pins, reading the minted
LatentDimension straight from the GRAPH — never a Python re-derivation of the
verdict):

  * The ROBUST/MDL witness (146000, `status=='motion_seq_robust'`,
    `time_infer_enabled==1`) reads ORDER-2 from the integer-centroid free-fall at
    EVERY resolution on the ladder {64..1024}, INCLUDING the bottom R=64. The MDL
    witness keys on the ABSOLUTE residual bit-cost about the median 2nd
    difference (0-2 cells everywhere), NOT the SNR ratio — so its floor sits at
    or below R=64 and there is NO lower rung that floors. R* <= 64 (MEASURED, not
    a constant). This FALSIFIES the SNR-threshold form of H1 while confirming its
    signal law (below).
  * The recovered acceleration (the minted generator's coeff, read from the
    graph) GROWS with resolution — |curv| ~ R — the confirmed signal law.
  * The EXACT witness (`status=='motion_seq'`) mints NOTHING from these
    quantized free-fall centroids at ANY resolution, including the highest (H2):
    the +/-1 integer-rounding floor is resolution-INDEPENDENT, so 146000's robust
    witness is NECESSARY, not a crutch.
  * const-velocity -> order-1 (exact ramp), NOT order-2; rendered const-velocity
    (sub-cell jitter) does not confabulate order-2; random -> floor; static ->
    floor. The robust witness is a strict order->=2 capability that does not
    confabulate.

NO Rust, NO seed change: the order-N DECISION is the seed rule; the gate only
renders / ingests the cy sequence and reads the minted LatentDimension back out.
Engine is `shared` (asserted via source_match, never a pinned hash).
"""
import numpy as np
import pytest

from domains.engine_provenance import engine_preamble, provenance_stamp
engine_preamble()

from domains import falling_world as fw          # noqa: E402

LADDER = [64, 128, 256, 512, 1024]
DISC_FRAC, DROP_FRAC, N_FRAMES = 0.03, 0.90, 12
DT = ["pred", "coord:r", "coord:c", "val"]


def test_engine_is_own_or_shared():
    """PROTOCOL section 10: a number without a provenanced engine is not a
    result. This rung builds no Rust, so the engine must be the shared canonical
    (byte-identical Rust source), never DIVERGED / unknown."""
    assert provenance_stamp()["source_match"] in ("own", "shared")


def _fall_centroids(R, n=N_FRAMES):
    """Ideal oracle: a constant-physical-size hard disc falling under real
    Galileo physics, quantized to R rows, integer region centroid per frame
    (the eye reports integer cy). The cross-frame render; in-frame integer cy."""
    W = max(8, R // 5)
    cx = W / 2.0
    rad = DISC_FRAC * R
    ts = np.arange(n, dtype=float)
    g = 2.0 * DROP_FRAC / (n - 1) ** 2
    cy_real = (0.5 * g * ts ** 2) * R + rad + 1
    rr, cc = np.mgrid[0:R, 0:W]
    out = []
    for yc in cy_real:
        mask = (rr - yc) ** 2 + (cc - cx) ** 2 <= rad ** 2
        if mask.sum():
            out.append(int(round(rr[mask].mean())))
    return out


def _mint(cy, status):
    """Ingest cy as a motion Observation, run the seeded run_rules fixpoint, and
    read the minted latent:time LatentDimension(s) straight from the graph.
    Returns (obs_status, [(order, coeffs), ...]). The DECISION is the seed rule."""
    s, ag, native = fw.boot_falling()
    frames = [[["obj", int(round(y)), 0, "obj"]] for y in cy]
    o = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                   "status": status, "key": ["motion"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    st = s.node(o)["attrs"].get("status")
    mints = []
    for n in s.nodes("LatentDimension"):
        a = s.node(n)["attrs"]
        if a.get("name") == "latent:time":
            mints.append((a.get("order"), a.get("coeffs")))
    return st, mints


def _accel_coeff(coeffs):
    """The recovered acceleration = the deepest (order-2) Newton coefficient,
    read from the minted generator. coeffs is a list of per-level leading
    vectors; the last one is the constant 2nd difference (the acceleration)."""
    last = coeffs[-1]
    return abs(last[0] if isinstance(last, (list, tuple)) else last)


# ─────────────── the robust witness mints order-2 across the ladder ───────────

@pytest.mark.parametrize("R", [64, 1024])
def test_robust_mints_order2_at_both_ends_of_the_ladder(R):
    """R* <= 64: the robust witness reads order-2 from the free-fall at the
    BOTTOM (R=64, SNR~0.5) and the TOP (R=1024) of the ladder. Read from the
    graph. Able to fail: if the witness floored at R=64 the mint list would be
    empty and status would be time_none."""
    st, mints = _mint(_fall_centroids(R), "motion_seq_robust")
    assert st == "time_inferred"
    assert [m[0] for m in mints] == [2]


def test_recovered_acceleration_grows_with_resolution():
    """The SIGNAL LAW, read from the GRAPH: the minted generator's recovered
    acceleration (2nd-difference constant) at R=1024 is strictly larger than at
    R=64 — |curv| ~ R. Not a Python re-derivation of the verdict: the number is
    the coeff the seed rule minted."""
    _, m64 = _mint(_fall_centroids(64), "motion_seq_robust")
    _, m1024 = _mint(_fall_centroids(1024), "motion_seq_robust")
    a64 = _accel_coeff(m64[0][1])
    a1024 = _accel_coeff(m1024[0][1])
    assert a1024 > a64, f"acceleration must grow with R: {a64} -> {a1024}"
    assert a1024 >= 8 * a64 - 2      # ~R-proportional (1024/64 = 16x); loose, graph-read


# ─────────────── H2: the exact witness NEVER mints on the free-fall ───────────

@pytest.mark.parametrize("R", LADDER)
def test_exact_witness_never_mints_on_quantized_freefall(R):
    """H2 — resolution and robustness are COMPLEMENTARY, not substitutes. The
    EXACT witness (`motion_seq`) floors the same quantized free-fall cy at EVERY
    resolution including the highest, because the +/-1 integer-rounding floor is
    resolution-INDEPENDENT. Confirms the robust witness is NECESSARY."""
    st, mints = _mint(_fall_centroids(R), "motion_seq")
    assert st == "time_none"
    assert mints == []


# ─────────────────────────────── controls ────────────────────────────────────

@pytest.mark.parametrize("R", LADDER)
def test_const_velocity_exact_ramp_mints_order1_not_order2(R):
    """Control: a rigid disc stepping an EXACT integer v cells/frame is order-1,
    NOT order-2 — the exact-first path mints order-1 even under the robust
    status. The witness must not read acceleration into constant velocity."""
    v = max(1, R // 64)
    cy = list(range(0, v * N_FRAMES, v))
    st, mints = _mint(cy, "motion_seq_robust")
    assert st == "time_inferred"
    assert [m[0] for m in mints] == [1]


@pytest.mark.parametrize("R", LADDER)
def test_random_floors_under_robust_witness(R):
    """Soundness: a genuine-noise centroid walk mints NOTHING even under the
    tolerant witness — differencing amplifies its spread, no order compresses
    below raw. A witness that minted here would be confabulating."""
    rng = np.random.default_rng(147000 + R)
    cy = np.cumsum(rng.integers(-6, 7, size=N_FRAMES)).tolist()
    st, mints = _mint(cy, "motion_seq_robust")
    assert st == "time_none"
    assert mints == []


def test_static_mints_nothing():
    """Control: a motionless object (constant cy) mints no time dimension."""
    st, mints = _mint([10] * N_FRAMES, "motion_seq_robust")
    assert st == "time_none"
    assert mints == []
