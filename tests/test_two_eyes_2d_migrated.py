"""BLOCK 177000 — TWO EYES SUPER-RESOLVE ON THE REAL 2-D az×el RETINA.

The gate for `VISION_TWO_EYES_2D_PREREG.md`. Closes Rung 5's largest remaining
caveat (`VISION_TWO_EYES_REGISTRATION_RESULTS.md` §6: "a 2-D flat wall is the
same estimator per elevation row (separable), noted not run"). Two low-res 2-D
photon eyes, eye B offset from eye A by a real sub-receptor AZIMUTH amount the
kernel is NOT told, view ONE flat 2-D textured wall; per elevation row the offset
is ESTIMATED (Rung-5b cross-frame phase) and the row is FUSED (Rung-5
`multilook_superres`). NO Rust built, NO new Term/kind — a loop over the proven
1-D pieces.

Pinned here:
  1. H1 — every row's estimate ≈ the true offset.
  2. SEPARABILITY (the real claim) — the per-row estimates AGREE (bounded spread):
     the 2-D problem decomposes into independent rows.
  3. H2 — 2-D super-res HOLDS under the estimate (aggregate + every row beats
     single by >4×; k0 resolved fused, aliased single).
  4. C1 — a perturbed (wrong) offset degrades every row (load-bearing).
  5. C2 — zero true offset → every row's estimate collapses, no gain (the Rung-5
     falsifier, in 2-D).
  6. C4 — a no-texture (flat) row fabricates NO detail (honest null).
  7. THE REUSE PREMISE — the 2-D retina's transduced activation is byte-identical
     to the 1-D `transduce` model (the fusion/registration reuse is exact).
  8. BYTE-IDENTITY / PROVENANCE — the Rung-5 fuser OFF gate still silent; the
     number came from this tree's own (or source-identical shared) engine.
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

pytest.importorskip("substrate_rs")
np = pytest.importorskip("numpy")

from domains.engine_provenance import engine_provenance  # noqa: E402
from domains.two_eye_superres import SuperResFuser  # noqa: E402
from domains.two_eye_superres_2d import sample_eye_2d  # noqa: E402
from scripts.two_eye_superres_2d_measure import (  # noqa: E402
    BLOCK, N, K0, make_texture_2d, separability_arm, zero_offset_arm)
from scripts.two_eye_superres_measure import transduce  # noqa: E402

_REG = separability_arm(np.random.default_rng(BLOCK))
_ZERO = zero_offset_arm(np.random.default_rng(BLOCK + 1))
_FLAT = next(r for r in _REG["rows"] if r["is_flat"])
_TEX = [r for r in _REG["rows"] if not r["is_flat"]]


# ── H1: every row's offset ESTIMATED from data ≈ the true offset ─────────────
def test_h1_every_row_registration_accurate():
    assert _REG["reg_err_max"] <= 0.05, _REG["delta_est_per_row"]
    for r in _TEX:
        assert abs(r["delta_est"] - _REG["true_delta"]) <= 0.05, r


# ── SEPARABILITY: the per-row estimates AGREE (the 2-D problem decomposes) ────
def test_separability_per_row_offsets_agree():
    assert _REG["separability_spread"] <= 0.05, _REG["delta_est_per_row"]
    assert _REG["separability_std"] <= 0.03, _REG["delta_est_per_row"]
    # genuinely independent problems: each textured row carries its OWN phases.
    assert len(_TEX) == _REG["n_textured"] >= 3


# ── H2: 2-D super-resolution HOLDS under the estimated offset ─────────────────
def test_h2_superres_holds_in_2d_under_estimate():
    assert _REG["aggregate_gain"] > 4.0, _REG["aggregate_gain"]
    assert _REG["per_row_gain_min"] > 4.0, [r["gain_est_over_single"] for r in _TEX]
    assert _REG["k0_relerr_fused_max"] < 0.25, _REG      # k0 resolved by fusion
    assert _REG["k0_relerr_single_min"] > 0.60, _REG     # k0 aliases in one eye
    # the offset turns N distinct azimuth positions into 2N (supra-Nyquist).
    assert _REG["single_nyquist_harmonic"] < K0 < _REG["fused_nyquist_harmonic"]


# ── C1: a PERTURBED (wrong) offset degrades EVERY row — estimate is load-bearing
def test_c1_perturbed_offset_degrades_every_row():
    assert _REG["pert_min_over_est"] >= 2.0, _REG["pert_min_over_est"]
    for r in _TEX:
        assert r["pert_hi_over_est"] >= 2.0 and r["pert_lo_over_est"] >= 2.0, r


# ── C2: zero true offset → every row's estimate collapses, no gain (2-D) ──────
def test_c2_zero_offset_falsifier_holds_in_2d():
    assert _ZERO["abs_delta_est_max"] <= 0.02, _ZERO
    assert 0.8 <= _ZERO["gain_min"] and _ZERO["gain_max"] <= 1.25, _ZERO


# ── C4: a no-texture (flat) row fabricates NO detail (honest null) ────────────
def test_c4_flat_row_fabricates_no_detail():
    assert _FLAT["fused_ac_std"] <= 1e-4, _FLAT
    assert _FLAT["delta_est"] == 0.0, _FLAT           # dead bins → no phase read


# ── The reuse premise: the 2-D retina transduces byte-identically to the model ─
def test_2d_retina_transduction_byte_matches_1d_model():
    tex, _P, _flat = make_texture_2d(np.random.default_rng(BLOCK))
    n_el = _flat + 1
    posA, actA = sample_eye_2d(tex, n_az=N, n_el=n_el, offset=0.0)
    # each cell's graph-transduced activation == transduce(round(luminance)).
    maxerr = 0.0
    for row in range(n_el):
        for col in range(N):
            count = int(round(max(0.0, tex(posA[col], row))))
            maxerr = max(maxerr, abs(actA[row][col] - float(transduce(count))))
    assert maxerr == 0.0, maxerr


# ── Byte-identity: the Rung-5 fuser is unchanged; its OFF gate still silent ───
def test_rung5_fuser_off_gate_still_silent():
    import math
    P = 8.0
    xa = [float(i) for i in range(N)]
    ya = [0.5 + 0.4 * math.cos(2 * math.pi * 6 * x / P) for x in xa]
    off = SuperResFuser(enabled=False)
    assert off.fuse(xa, ya, n_fine=32, period=P, ridge=1e-6, k_max=4) is None
    assert not list(off.substrate.nodes("SuperResolvedField"))


# ── Provenance ───────────────────────────────────────────────────────────────
def test_engine_provenance_is_own_or_shared():
    p = engine_provenance()
    assert p["source_match"] in ("own", "shared"), p
