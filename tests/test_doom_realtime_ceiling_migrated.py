"""Gate for the Doom real-time rung (seed block 201000-201999).

VizDoom-free: exercises the IMPORTABLE, deterministic cores — the ceiling
interpolation / exponent helpers and the foveated-layout compute-model — on
constructed inputs. The wall-clock measurement itself is not gated (it is a
solo timing pass); these gate the arithmetic the headline reads off.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)


def test_measure_module_is_import_inert():
    # Importing must build no eye, capture no Doom, time nothing.
    import scripts.doom_realtime_ceiling_measure as M
    assert hasattr(M, "main") and hasattr(M, "run_grid")
    assert M.SWEEP[0] == (20, 15) and M.SWEEP[-1] == (160, 120)
    assert [a * b for (a, b) in M.SWEEP][0] == 300
    assert [a * b for (a, b) in M.SWEEP][-1] == 19200


def test_loglog_exponent_recovers_linear():
    from scripts.doom_realtime_ceiling_measure import _loglog_exponent
    cells = [300, 1200, 4800, 19200]
    linear = [3.0 * c for c in cells]          # exponent 1
    quad = [1e-4 * c * c for c in cells]       # exponent 2
    assert abs(_loglog_exponent(cells, linear)["exponent"] - 1.0) < 1e-6
    assert abs(_loglog_exponent(cells, quad)["exponent"] - 2.0) < 1e-6
    assert _loglog_exponent(cells, linear)["r2"] > 0.999


def test_ceiling_interpolates_budget_crossing():
    from scripts.doom_realtime_ceiling_measure import _ceiling
    # ms = 0.01 * cells (linear): budget 28.5ms -> 2850 cells exactly.
    cells = [300, 1200, 4800, 19200]
    ms = [0.01 * c for c in cells]
    c = _ceiling(cells, ms, 28.5)
    assert abs(c["cells_piecewise"] - 2850) <= 60
    assert abs(c["cells_powerfit"] - 2850) <= 60


def test_foveated_is_1to1_fits_budget_and_covers_frame():
    from scripts.foveated_layout_spec import foveated_layout, uniform_layout, R_MAX
    for budget in (1626, 1850, 13052, 14892):
        f = foveated_layout(budget)
        assert f["foveal_px_per_receptor"] == 1.0        # 1:1 fovea, no sub-pixel
        assert f["cells"] <= budget                       # fits the budget
        assert f["fits"] is True
        assert f["coverage_to_radius_px"] >= R_MAX - 1e-6 # periphery covers the corner
        u = uniform_layout(budget)
        assert u["central_px_per_cell"] > 1.0             # uniform is coarser at centre


def test_foveation_gain_equals_uniform_px_per_cell():
    from scripts.foveated_layout_spec import payoff
    p = payoff(1850)
    # gain = uniform px/cell / 1.0 (by construction) — largest at tight budgets.
    assert abs(p["central_acuity_gain_x"] - p["uniform"]["central_px_per_cell"]) < 0.05
    assert p["central_acuity_gain_x"] > 5.0               # ~6.4x at the graph budget
    p_big = payoff(14892)
    assert p_big["central_acuity_gain_x"] < p["central_acuity_gain_x"]  # shrinks as budget grows


def test_eye_is_uniform_only_build_gap_named():
    from scripts.foveated_layout_spec import build_gap
    g = build_gap()
    assert g["eye_supports_nonuniform"] is False
    assert len(g["live_build_needs"]) >= 2
