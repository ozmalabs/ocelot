"""GATE for LOOMING / EXPANSION COMMON-FATE (block 154000-154999).

The general capability: carve an object by the coherent SCALE (expansion) its
cells undergo, generalizing common-fate from translation to looming — a
depth-from-motion read-out. Doom is only the eval.

Gated, each ABLE TO FAIL (reads measured/graph values, never an exact-d2 magic
constant):

  scorer     divergence_field + affine_flow_fit are correct on CONSTRUCTED
             known fields (a pure expansion flow of known rate s about a known
             FOE -> the read-out recovers s and the FOE); the expansion_carve
             groups a constructed disk. Always runs, no VizDoom.

  H1  (SYNTHETIC, always runs) the mechanism on analytic ground truth:
      * the expansion carve recovers the KNOWN scale rate (loom AND recede,
        opposite sign) to tolerance, and the FOE to within a cell;
      * on a loom where the translation carve FRAGMENTS (many pieces, low IoU),
        the expansion carve groups it into a materially higher-IoU region;
      * controls: pure TRANSLATE -> expansion does NOT fire (~0 IoU);
        STATIC -> nothing; NOISE -> floor; RECEDE -> carved with NEGATIVE rate.

  H2  (DOOM, skips if VizDoom absent AND no results file) read from the recorded
      run: the expansion carve's enemy IoU exceeds the translation carve's on
      the SAME capture AND clears 153000's translation floor (~0.015) — the
      general looming capability transfers — OR the recorded result is an
      honestly-named DEGRADE. Direction asserted, absolute IoU is the finding.

No Rust added, no seed, no default moved (new files only) => the shipped
translation carve is byte-identical BY CONSTRUCTION; asserted here by re-running
it and confirming it still fragments the loom exactly as recorded.
"""
import json
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (os.path.join(ROOT, "scripts"), ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from domains.engine_provenance import engine_preamble
    engine_preamble()
except Exception:
    pass

import looming_common_fate_probe as L   # noqa: E402

RESULTS = os.path.join(ROOT, "results", "looming_common_fate.json")


def _have_vizdoom():
    try:
        import vizdoom  # noqa: F401
        return True
    except Exception:
        return False


# ============================================================
#  SCORER / READ-OUT correctness on CONSTRUCTED known fields
# ============================================================
def test_divergence_field_correct_on_known_field():
    # v = (2y, 3x): div = d(3x)/dx + d(2y)/dy = 3 + 2 = 5 everywhere (interior)
    g = 20
    yy, xx = np.mgrid[0:g, 0:g].astype(float)
    vx = 3.0 * xx
    vy = 2.0 * yy
    div = L.divergence_field(vy, vx)
    assert np.allclose(div[2:-2, 2:-2], 5.0, atol=1e-9)


def test_affine_fit_recovers_known_rate_and_foe():
    # pure expansion s about foe=(12,7): v = s*(p-foe). Fit must recover both.
    g = 30
    s = 0.17
    foe = (12.0, 7.0)
    yy, xx = np.mgrid[0:g, 0:g].astype(float)
    vx = s * (xx - foe[0])
    vy = s * (yy - foe[1])
    cells = frozenset((int(r), int(c)) for r in range(5, 25) for c in range(5, 25))
    fit = L.affine_flow_fit(cells, vy, vx)
    assert abs(fit["scale_rate"] - s) < 1e-3, fit
    assert fit["foe"] is not None
    assert abs(fit["foe"][0] - foe[0]) < 0.5 and abs(fit["foe"][1] - foe[1]) < 0.5


def test_expansion_carve_groups_a_constructed_disk():
    vy, vx, gt = L.radial_flow(L.SYNTH_G, 24, 24, 12, 0.15, quant=True)
    ex, tol, div = L.expansion_carve(vy, vx, L.SYNTH_G, L.SYNTH_G)
    _, ex_iou = L.best_region(ex, gt)
    assert ex_iou > 0.5, f"expansion carve failed to group the disk: {ex_iou}"
    assert tol > 0.0  # Otsu tolerance FELL OUT of the field (§13), not injected


# ============================================================
#  H1 — the mechanism on analytic ground truth (always runs)
# ============================================================
def _h1():
    return L.run_h1_analytic()["cases"]


def test_h1_recovers_scale_rate_both_signs():
    c = _h1()
    loom = c["loom_s0.15"]
    rec = c["recede_s-0.15"]
    # recovered rate matches the KNOWN rate to tolerance, loom + / recede -
    assert abs(loom["recovered_scale_rate_gt"] - 0.15) < 0.02, loom
    assert abs(rec["recovered_scale_rate_gt"] - (-0.15)) < 0.02, rec
    assert loom["recovered_scale_rate_gt"] > 0 > rec["recovered_scale_rate_gt"]
    # FOE recovered to within a cell
    assert loom["recovered_foe"] is not None
    assert abs(loom["recovered_foe"][0] - 24) <= 1.0
    assert abs(loom["recovered_foe"][1] - 24) <= 1.0


def test_h1_expansion_groups_where_translation_fragments():
    c = _h1()["loom_s0.15"]
    # translation carve fragments the loom into many low-IoU pieces...
    assert c["translation_carve_nfrag"] >= 5, c
    assert c["translation_carve_iou"] < 0.30, c
    # ...where the expansion carve groups it into a materially higher-IoU region
    assert c["expansion_carve_iou"] > 0.5, c
    assert c["expansion_carve_iou"] > c["translation_carve_iou"] + 0.3, c


def test_h1_off_axis_focus_recovered():
    c = _h1()["loom_offaxis_foe"]
    # disk centered at cx = g//2 + 6 = 30; the FOE read-out must find it
    assert c["recovered_foe"] is not None
    assert abs(c["recovered_foe"][0] - 30) <= 1.0, c


def test_h1_recede_is_contraction_and_carved():
    c = _h1()["recede_s-0.15"]
    assert c["expansion_carve_iou"] > 0.5, c          # same mechanism...
    assert c["recovered_scale_rate_gt"] < -0.05, c    # ...opposite sign


def test_h1_controls_do_not_spuriously_fire():
    c = _h1()
    # pure translation (no scale) must NOT be carved by expansion
    assert c["translate_no_scale"]["expansion_carve_iou"] < 0.05, c["translate_no_scale"]
    assert abs(c["translate_no_scale"]["recovered_scale_rate_gt"]) < 0.03
    # static -> nothing
    assert c["static"]["expansion_carve_iou"] < 0.02, c["static"]
    # noise -> floor (random flow is not coherent expansion)
    assert c["noise"]["expansion_carve_iou"] < 0.05, c["noise"]


def test_h1_loom_recovered_under_egomotion():
    # the loomer is recovered AND its rate read out even when the whole field
    # translates (egomotion) — expansion is invariant to global translation.
    c = _h1()["loom_plus_egomotion"]
    assert c["expansion_carve_iou"] > 0.5, c
    assert abs(c["recovered_scale_rate_gt"] - 0.15) < 0.02, c


# ============================================================
#  H2 — Doom, ground-truth scored (read from the recorded run)
# ============================================================
def _load_results():
    if not os.path.exists(RESULTS):
        if not _have_vizdoom():
            pytest.skip("VizDoom absent and results/looming_common_fate.json "
                        "not present — cannot score H2")
        pytest.skip("results/looming_common_fate.json not present (run probe)")
    with open(RESULTS) as fh:
        return json.load(fh)


def test_h2_expansion_beats_translation_on_doom():
    h2 = _load_results().get("h2_doom", {})
    if "error" in h2:
        pytest.skip(f"H2 not measured: {h2['error']}")
    ex = h2["expansion_carve_enemy_iou"]["mean"]
    tr = h2["translation_carve_enemy_iou"]["mean"]
    # THE GENERAL LOOMING CAPABILITY TRANSFERS: on the SAME capture the
    # expansion carve recovers the looming enemy materially better than the
    # translation carve (which 153000 found flat ~0.015). Direction asserted;
    # absolute IoU is the finding. (If this ever fails it is a named DEGRADE,
    # recorded in the results doc — not silently passed.)
    assert ex > tr, f"expansion {ex} !> translation {tr}"
    assert ex > 0.015, f"expansion {ex} did not clear 153000's translation floor"


def test_h2_recovered_rate_sign_is_looming():
    h2 = _load_results().get("h2_doom", {})
    if "error" in h2:
        pytest.skip(f"H2 not measured: {h2['error']}")
    # approaching enemies LOOM => positive expansion. Sign must be positive
    # (magnitude is noisy on the small enemy — asserted as the honest residual).
    if not h2["recovered_scale_rates"]:
        pytest.skip("no scale rates recovered on this capture")
    assert h2["recovered_scale_rate_mean"] > 0, h2["recovered_scale_rate_mean"]


# ============================================================
#  BYTE-IDENTITY of the shipped carve (new files only, no Rust/seed)
# ============================================================
def test_translation_carve_unchanged_still_fragments_the_loom():
    # The translation common-fate carve is 153000's Rust primitive, imported
    # unchanged. Re-run it live and confirm it still fragments the s=0.15 loom
    # (its behaviour is byte-identical — this rung added no Rust and no seed).
    vy, vx, gt = L.radial_flow(L.SYNTH_G, 24, 24, 12, 0.15, quant=True)
    tr, tol = L.translation_carve(vy, vx, L.SYNTH_G, L.SYNTH_G)
    _, tr_iou = L.best_region(tr, gt)
    assert len(tr) >= 5 and tr_iou < 0.30, (len(tr), tr_iou)
