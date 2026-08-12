"""PAINT-FROM-SAMPLE — the migrated gate (VISION_PAINT_PREREG.md, committed
BEFORE the run at e7f537d1).

Deterministic. Pins BOTH the positives and — deliberately, PROTOCOL §7 — THE
NEGATIVES, so that a later rung cannot quietly inherit the account as if it had
passed whole:

  ARM I  I1 neon spreading      PASS   (absent at baseline, present with paint)
         I2 watercolour         PASS   (and takes the INNER contour's sign — the
                                        rung's one genuinely RISKED prediction)
         I3 Cornsweet           FAIL   (appears, but with the WRONG SIGN)
         I4 blind-spot texture  FAIL   (baseline is NOT absent, and the paint
                                        carries LESS structure than the baseline)
  ARM R  R1/R2/R3/R4            PASS   (the mechanism knows when it is wrong)
  ARM K  k FALLS OUT; pquant is SCALE-INVARIANT; the mechanism is LOAD-BEARING
  ARM F  floors, §9 inertness, and the no-decision / no-Rust source gates

THE CONJUNCTION GATE THEREFORE FAILS, because ARM I requires all four. That
verdict is asserted here as a first-class fact, not left in prose.
"""
from domains.engine_provenance import engine_preamble
engine_preamble()

import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402

import numpy as np  # noqa: E402
import pytest  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import domains.seed_registry  # noqa: E402,F401
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import paint_world as pw  # noqa: E402

sys.path.insert(0, os.path.join(HERE, "scripts"))
import paint_measure as pm  # noqa: E402

# A provenance pin THIS REPOSITORY CANNOT RESOLVE is a SKIP, not a red: the claim
# is unverifiable here, not false, and the gate re-arms unchanged against a repo
# that has the range (tests/provenance_pins.py, red-test triage 2026-08-12).
from provenance_pins import skip_if_unresolvable as _skip_unresolvable_pin  # noqa: E402


# §12.3 — BOTH ENDPOINTS FIXED. `a67afe4f` is the base `main` HEAD this rung
# branched from; `368d0528` is this rung's final mechanism commit. Neither is
# HEAD, so the claim cannot rot by anyone else doing work afterwards. DECLARED
# BOUND: the range covers the MECHANISM (prereg, seed, adapter, runner, rows);
# this gate file itself necessarily lands after it, and adds no Rust.
BASE_SHA = "a67afe4f"
RUNG_END_SHA = "368d0528"


def _rung_diff_names():
    out = subprocess.run(
        ["git", "diff", "--name-only", f"{BASE_SHA}..{RUNG_END_SHA}"],
        cwd=HERE, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    return [f for f in out.stdout.split() if f]


def _run(lum, app=None, sensed=None, *, paint=1.0, q=1.0):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_paint"])
    return s, pw.run(s, lum, app, sensed, paint=paint, pquant=q)


# =========================================================================== #
#  ARM K2 — §13.2 VACUITY. Run FIRST: a decorative mechanism proves nothing.
# =========================================================================== #
def test_K2_the_mechanism_is_LOAD_BEARING_not_decorative():
    d = pm.arm_K2()
    assert d["ALL_ZERO_would_be_decorative"] is False
    # it must move the things the rung actually CLAIMS it moves
    for k in ("pregion", "ppaint_lum", "ppaint_app", "prefuted_cell", "prefuted"):
        assert d[k] > 0.0, f"{k} did not move when paint was toggled"


# =========================================================================== #
#  THE CRUX — the baseline, measured, before any illusion is credited
# =========================================================================== #
def test_baseline_nothing_spreads_into_a_SENSED_cell():
    """The only filling mechanism that existed before this rung (vision_ground's
    gr_fill) fires on UNSENSED cells. On a fully-sensed field the belief equals
    the observation EXACTLY — so I1/I2's spreading has a genuine zero baseline."""
    d = pm.baseline_no_spreading_into_sensed_cells()
    assert d["max_abs_belief_minus_obs"] == 0.0
    assert d["belief_at_far_cell"] == d["obs_at_far_cell"]


def test_baseline_blindspot_fill_is_NOT_flat_so_I4_is_UNINFORMATIVE():
    """THE CRUX RULE FIRING AGAINST THE RUNG. The pre-registration predicted
    gr_fill's blind-spot fill would be FLAT 'by construction' (mean of
    neighbours). It is NOT: applied iteratively, different hole cells get
    different neighbour means, so the baseline already carries ~7% of the true
    surround variance. An illusion present at baseline is UNINFORMATIVE."""
    d = pm.baseline_blindspot_fill_is_flat(__import__("random").Random(66500))
    assert d["fill_var"] > 0.0, "the pre-registered 'flat by construction' baseline"
    assert d["fill_var"] / d["true_var"] > 0.05


# =========================================================================== #
#  ARM I — the illusion battery. POSITIVES *and* NEGATIVES pinned.
# =========================================================================== #
def test_I1_neon_spreading_FALLS_OUT():
    """Appearance appears at a cell whose OBSERVED appearance is zero, inside a
    contour-bounded region, because the region's sample is a mean over its own
    cells. Weak (60 * 4/36), which is the right magnitude for neon spreading."""
    d = pm.arm_I1()
    assert d["baseline_paint_off"]["ppaint_app_at_far_cell"] == 0.0
    assert d["paint"]["observed_app_at_far_cell"] == 0.0
    assert d["paint"]["ppaint_app_at_far_cell"] == pytest.approx(60.0 * 4 / 36)
    assert d["ILLUSION"] is True


def test_I2_watercolour_FALLS_OUT_AND_TAKES_THE_INNER_CONTOUR():
    """THE RUNG'S ONE GENUINELY RISKED PREDICTION, and it held. The STRONG dark
    outer contour IS a strict-|Δ| maximum, so it is a boundary and is EXCLUDED
    from the region; the WEAK inner contour is iso-luminant, so it is NOT a
    boundary, joins the region, and its chroma enters the sample. The tint
    therefore takes the INNER contour's sign (+60) and not the OUTER's (−60) —
    the actual asymmetry of the illusion, from a mechanism with nothing about
    watercolour written anywhere in it."""
    d = pm.arm_I2()
    assert d["baseline_paint_off"]["ppaint_app_at_interior"] == 0.0
    assert d["takes_INNER_sign"] is True
    assert d["takes_OUTER_sign"] is False
    assert d["paint"]["ppaint_app_at_interior"] > 0.0
    assert d["ILLUSION"] is True


def test_I3_cornsweet_APPEARS_BUT_WITH_THE_WRONG_SIGN_negative():
    """A NEGATIVE, PINNED (§7). Two physically-identical flat far-fields ARE
    painted differently — so something happens — but the difference has the
    WRONG SIGN. The k=1 region mean would have given the correct +2 (the flat
    region keeps its bright shoulder); the ladder ESCALATES past it to k=2
    because the ramp refutes the flat code, and the order-2 plane, fitted to
    flat-plus-ramp and extrapolated across the far field, TILTS IT THE OTHER
    WAY. The escalation that ARM R needs is the same escalation that destroys
    this illusion."""
    d = pm.arm_I3()
    assert d["physical_left"] == d["physical_right"]          # physically equal
    assert d["baseline_paint_off"]["difference"] == 0.0       # absent at baseline
    assert d["paint"]["difference"] != 0.0                    # something happens
    assert d["paint"]["difference"] < 0.0                     # ... and it is WRONG
    assert d["SIGN_MATCHES_CUSP_POLARITY"] is False
    assert d["paint"]["hub_left"]["korder"] == 2.0            # the ladder escalated
    assert d["paint"]["hub_right"]["korder"] == 2.0


def test_I4_blindspot_texture_FAILS_and_is_UNINFORMATIVE_negative():
    """A NEGATIVE, PINNED (§7), and it fails TWICE. (a) The baseline is not
    absent, so the pre-registered absent-vs-present comparison is uninformative
    by the rung's own crux rule. (b) On the only comparable statistic — fill
    variance as a FRACTION of the true surround variance — the paint carries
    LESS structure than the baseline it was supposed to beat (0.2% vs 7.3%),
    because the hole is painted by a smooth order-2 plane, not a texture."""
    d = pm.arm_I4()
    assert d["ILLUSION"] is False
    assert d["DIAG_paint_carries_more_structure_than_baseline"] is False
    assert d["DIAG_paint_fill_var_over_true_var"] < d["DIAG_baseline_fill_var_over_true_var"]


def test_ARM_I_FAILS_as_a_whole_and_therefore_so_does_the_CONJUNCTION_GATE():
    """The pre-registered gate is a CONJUNCTION and ARM I requires ALL FOUR
    illusions. Two fell out, one has the wrong sign, one is uninformative. The
    rung's verdict is FAIL, asserted rather than narrated."""
    assert pm.arm_I1()["ILLUSION"] is True
    assert pm.arm_I2()["ILLUSION"] is True
    assert pm.arm_I3()["SIGN_MATCHES_CUSP_POLARITY"] is False
    assert pm.arm_I4()["ILLUSION"] is False


# =========================================================================== #
#  ARM R — the residual contrast arm. THIS ONE PASSES.
# =========================================================================== #
def test_R_the_mechanism_KNOWS_WHEN_IT_IS_WRONG():
    d = pm.arm_R()
    u, g, t = d["R1_uniform"], d["R2_gradient"], d["R3_texture"]
    # R1 — a flat surface stops at the bottom of the ladder, residual zero
    assert u["n_regions"] == 1 and u["largest_korder"] == 1.0
    assert u["any_region_refuted"] is False and u["mean_cell_residual"] == 0.0
    # R2 — a linear ramp is ONE region (no strict-max boundary anywhere) and the
    # order ESCALATES to 2, where the plane describes it exactly
    assert g["n_regions"] == 1 and g["largest_korder"] == 2.0
    assert g["any_region_refuted"] is False and g["mean_cell_residual"] == 0.0
    # R3 — the ladder EXHAUSTS on texture and the residual STAYS large
    assert t["largest_korder"] == 2.0 and t["any_region_refuted"] is True
    assert t["largest_prefuted"] == 1.0
    assert t["refuted_area_fraction"] > 0.9
    assert t["mean_cell_residual"] >= d["half_quantum"]
    # R4 — the CONTRAST, which is the whole point of the arm
    assert t["mean_cell_residual"] > u["mean_cell_residual"]


def test_R3_texture_did_NOT_fragment_refuting_the_rungs_OWN_prediction():
    """PROTOCOL §3.7 / §7. The pre-registration named over-segmentation as the
    outcome MOST LIKELY TO KILL THE RUNG: threshold-free non-maximum suppression
    on a texture 'should FRAGMENT into micro-regions', each painted perfectly,
    collapsing the residual. It does not. A random field's |Δ| are rarely STRICT
    local maxima, so the flood merges nearly everything: ~5 regions over 144
    cells, not 144."""
    d = pm.arm_R()["R3_texture"]
    assert d["n_regions"] < 10
    assert d["largest_region_cells"] > 100


# =========================================================================== #
#  ARM K — k FALLS OUT, and pquant is a RESOLUTION not a magic number
# =========================================================================== #
def test_K1_the_three_ladder_outcomes_are_each_REACHED_by_the_residual_alone():
    d = pm.arm_R()
    assert (d["R1_uniform"]["largest_korder"], d["R1_uniform"]["largest_prefuted"]) == (1.0, 0.0)
    assert (d["R2_gradient"]["largest_korder"], d["R2_gradient"]["largest_prefuted"]) == (2.0, 0.0)
    assert (d["R3_texture"]["largest_korder"], d["R3_texture"]["largest_prefuted"]) == (2.0, 1.0)


def test_K1_korder_is_assigned_by_ONE_SEED_RULE_and_nowhere_in_python():
    """§0 — k must FALL OUT, so nothing outside the graph may set it. The adapter
    initialises the BOTTOM of the ladder once (korder=1.0 at cell creation) and
    never writes it again; `pt_escalate` is the only other writer anywhere."""
    seed = json.load(open(os.path.join(HERE, "seeds", "vision_paint.json")))
    writers = [r["name"] for r in seed["rules"]
               if any(e[0].startswith("set_attr") and e[2] == "korder" for e in r["effects"])]
    assert writers == ["pt_escalate"], writers
    # The adapter ASSIGNS korder exactly once — the initialisation to the BOTTOM
    # of the ladder at cell creation. Every other mention is a read-back key.
    src = open(os.path.join(HERE, "domains", "paint_world.py")).read()
    assert len(re.findall(r'"korder":\s', src)) == 1, "the adapter assigns korder twice"
    # The adapter's ONLY attr write is the flag blind-write; it never writes
    # korder, and neither does the confirmatory runner.
    writes = re.findall(r"\.set_attr\(([^,]+),\s*\"([a-z_]+)\"", src)
    assert [w[1] for w in writes] == ["paint"], writes
    runner = open(os.path.join(HERE, "scripts", "paint_measure.py")).read()
    assert re.findall(r"\.set_attr\(", runner) == [], "the runner writes graph attrs"


def test_K3_pquant_is_SCALE_INVARIANT_so_it_is_a_RESOLUTION_not_a_magic_number():
    """§13. Re-run the whole battery at a ×4 alphabet with pquant=4: every
    qualitative verdict is unchanged and every magnitude scales EXACTLY ×4. A
    number that had been tuned against the answer would not survive this."""
    one, four = pm.arm_I1(), pm.arm_I1(scale=4, q=4.0)
    assert four["paint"]["ppaint_app_at_far_cell"] == pytest.approx(
        4 * one["paint"]["ppaint_app_at_far_cell"])
    i2a, i2b = pm.arm_I2(), pm.arm_I2(scale=4, q=4.0)
    assert i2b["takes_INNER_sign"] == i2a["takes_INNER_sign"] is True
    assert i2b["paint"]["ppaint_app_at_interior"] == pytest.approx(
        4 * i2a["paint"]["ppaint_app_at_interior"])
    i3a, i3b = pm.arm_I3(), pm.arm_I3(scale=4, q=4.0)
    assert i3b["paint"]["difference"] == pytest.approx(4 * i3a["paint"]["difference"])
    ra, rb = pm.arm_R(), pm.arm_R(scale=4, q=4.0)
    for k in ("R1_uniform", "R2_gradient", "R3_texture"):
        assert rb[k]["largest_korder"] == ra[k]["largest_korder"]
        assert rb[k]["any_region_refuted"] == ra[k]["any_region_refuted"]
        assert rb[k]["n_regions"] == ra[k]["n_regions"]


def test_K1_a_linear_ramp_has_NO_boundary_anywhere_no_threshold_was_used():
    """The boundary criterion's load-bearing consequence: a ramp's |Δ| are all
    EQUAL, so none is a STRICT local maximum, so a ramp is ONE region. Any
    magnitude threshold would have cut it into pieces."""
    n = 12
    grad = np.tile(np.arange(n, dtype=float) * 3.0 + 50.0, (n, 1))
    s, h = _run(grad)
    assert len(pw.hubs(s, h)) == 1
    assert float(np.max(pw.field_of(s, h, "pblk_e"))) == 0.0
    assert float(np.max(pw.field_of(s, h, "pblk_s"))) == 0.0
    hub = pw.region_report(s, h)[0]
    assert hub["korder"] == 2.0
    assert hub["pslope_c_plum"] == pytest.approx(3.0)   # the true slope, exactly


def test_K1_a_step_splits_and_each_side_stops_at_k1():
    lum = np.full((8, 8), 50.0)
    lum[:, 4:] = 90.0
    s, h = _run(lum)
    rows = pw.region_report(s, h)
    assert len(rows) == 2
    assert sorted(r["pmean_lum"] for r in rows) == [50.0, 90.0]
    assert all(r["korder"] == 1.0 and r["prefuted"] == 0.0 for r in rows)


# =========================================================================== #
#  ARM F — floors and §9
# =========================================================================== #
@pytest.mark.slow
def test_F1_noise_floor_never_invents_appearance_from_none():
    d = pm.arm_F1()
    assert d["n_fields_inventing_appearance"] == 0
    assert d["max_abs_painted_app"] == 0.0


@pytest.mark.slow
def test_F2_texture_floor_at_power():
    d = pm.arm_F2()
    assert d["fraction_any_region_refuted"] > 0.9
    assert d["mean_n_regions"] < 10          # it does NOT fragment, at power


def test_F3_off_by_default_and_inert():
    d = pm.arm_F3()
    assert d["default_flag"] == 0.0
    assert all(v == 0.0 for v in d["max_abs_when_off"].values())


def test_F3_a_fresh_boot_ships_the_flag_OFF():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_paint"])
    p = list(s.nodes("PaintParams"))[0]
    assert float(s.node(p)["attrs"]["paint"]) == 0.0


# =========================================================================== #
#  SOURCE GATES — §0 (no decision in Python) and §10 (no Rust)
# =========================================================================== #
def test_the_adapter_makes_NO_DECISION_over_graph_state():
    """CLAUDE.md / §0. The adapter may translate and read; it may NOT branch on
    what the graph holds. Checked by AST rather than by substring: every
    conditional and comprehension-guard in paint_world.py is collected, and none
    may mention any attribute this mechanism computes. (A substring scan flagged
    `if app is None` — a default-argument fill — which is why this is an AST
    check and not a grep.)"""
    import ast as _ast
    src = open(os.path.join(HERE, "domains", "paint_world.py")).read()
    tree = _ast.parse(src)
    decided = {"pregion", "korder", "prefuted", "prefuted_cell", "pblk_e",
               "pblk_s", "ppaint_lum", "ppaint_app", "presid_lum", "presid_app",
               "pmean_lum", "pmean_app", "paint", "pd_e", "pd_s", "presid_mean"}
    tests = []
    for node in _ast.walk(tree):
        if isinstance(node, (_ast.If, _ast.IfExp)):
            tests.append(node.test)
        elif isinstance(node, _ast.comprehension):
            tests.extend(node.ifs)
    for t in tests:
        names = {n.value for n in _ast.walk(t) if isinstance(n, _ast.Constant)
                 and isinstance(n.value, str)}
        names |= {n.id for n in _ast.walk(t) if isinstance(n, _ast.Name)}
        names |= {n.attr for n in _ast.walk(t) if isinstance(n, _ast.Attribute)}
        leaked = names & decided
        assert not leaked, f"the adapter branches on graph state: {leaked}"
    # And it never COMPUTES the boundary criterion: no |Δ|, no comparison of one
    # cell's luminance against another's, anywhere outside a docstring. (The
    # docstrings DO name the rules — that is description, not implementation,
    # which is why this checks executable code and the AST walk above is the
    # real gate.)
    code = "\n".join(ln for ln in src.splitlines()
                     if not ln.strip().startswith("#"))
    tree2 = _ast.parse(code)
    strings = {n.value for n in _ast.walk(tree2) if isinstance(n, _ast.Constant)
               and isinstance(n.value, str)}
    for node in _ast.walk(tree2):
        if isinstance(node, _ast.Compare):
            seg = _ast.get_source_segment(code, node) or ""
            assert "plum" not in seg and "papp" not in seg, seg


@_skip_unresolvable_pin(BASE_SHA, RUNG_END_SHA)
def test_this_rung_adds_NO_Rust():
    changed = _rung_diff_names()
    assert changed, "expected a non-empty rung diff"
    rs = [f for f in changed if f.endswith(".rs")]
    assert rs == [], f"this rung claims NO new Rust but touched: {rs}"


@_skip_unresolvable_pin(BASE_SHA, RUNG_END_SHA)
def test_this_rung_edits_NO_OTHER_RUNGS_SEED_OR_ADAPTER():
    """§11 rule 4. The only shared file touched is the seed REGISTRY, and only
    to register this rung's own seed."""
    changed = [f.split("gamma-substrate/")[-1] for f in _rung_diff_names()]
    allowed = {
        "VISION_PAINT_PREREG.md", "tools/build_vision_paint.py",
        "seeds/vision_paint.json", "domains/paint_world.py",
        "scripts/paint_measure.py", "results/paint_measure.json",
        "domains/seed_registry.py",
    }
    assert set(changed) <= allowed, f"foreign files in this rung's diff: {set(changed) - allowed}"
    diff = subprocess.run(
        ["git", "diff", f"{BASE_SHA}..{RUNG_END_SHA}", "--",
         "domains/seed_registry.py"],
        cwd=HERE, capture_output=True, text=True).stdout
    removed = [ln for ln in diff.splitlines()
               if ln.startswith("-") and not ln.startswith("---")]
    assert removed == [], f"the registry edit is not purely additive: {removed}"
    assert "vision_paint" in diff
