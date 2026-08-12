"""THE EDGE-ANCHORED DECAYING GRADIENT — the migrated gate
(VISION_DECAY_PREREG.md, committed BEFORE any implementation at `d5260a6f`).

Deterministic. Pins BOTH the positives and — deliberately, PROTOCOL §7 — THE
NEGATIVES and THE COSTS, so a later rung cannot inherit this as a free lunch:

  ARM V   vacuity            the mechanism is LOAD-BEARING (run FIRST, §13.2)
  ARM V2  byte-identity      with pdecay OFF, the paint rung reproduces EXACTLY
  ARM 1   Cornsweet sign     PASS  (+0.727273, at korder 2 — the ESCALATED order)
  ARM 2   the decline        PASS  — and the arm is POSITIVE-CONTROLLED: the
                             committed plane FAILS the same predicate
  ARM 3   the residual arm   PASS  (R1-R4 + F1 + F2, decay ON)
  ARM 3b  R5 bounded ramp    THE COST, PINNED AS A REGRESSION
  G2      cumulative         ABSENT, pinned — and NOT pooled with G1
  ARM B   bounds             three fixed widths
  §9      OFF by default, inert; source gates; no Rust
"""
from domains.engine_provenance import engine_preamble
engine_preamble()

import json  # noqa: E402
import os  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402

import pytest  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import domains.seed_registry  # noqa: E402,F401
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import decay_world as dw  # noqa: E402

sys.path.insert(0, os.path.join(HERE, "scripts"))
import decay_measure as dm  # noqa: E402

# A provenance pin THIS REPOSITORY CANNOT RESOLVE is a SKIP, not a red: the claim
# is unverifiable here, not false, and the gate re-arms unchanged against a repo
# that has the range (tests/provenance_pins.py, red-test triage 2026-08-12).
from provenance_pins import skip_if_unresolvable as _skip_unresolvable_pin  # noqa: E402


# §12.3 — BOTH ENDPOINTS FIXED, NEITHER IS `HEAD`. `51f5ecf9` is the base `main`
# HEAD this rung branched from; `740d3ac9` is the commit at which this rung's
# MECHANISM is complete (prereg + builder + seed + adapter + runner + gate +
# results). The claim each provenance test makes is about THIS RUNG'S OWN DIFF,
# so it is pinned to that diff and cannot rot by anyone else doing work
# afterwards — nor by this rung doing more work, which is why the end SHA was
# moved forward from the earlier `88ac3f81` once the mechanism files were
# touched again: a range that stops short of its own rung's last edit is a
# claim about a subset, dressed as a claim about the whole.
# DECLARED BOUND: the single commit that writes THIS comment lands after
# `740d3ac9` and edits only this file. It adds no Rust.
BASE_SHA = "51f5ecf9"
RUNG_END_SHA = "740d3ac9"


def _rung_diff_names():
    out = subprocess.run(["git", "diff", "--name-only",
                          f"{BASE_SHA}..{RUNG_END_SHA}"],
                         cwd=HERE, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    return [f for f in out.stdout.split() if f]


def _seed():
    return json.load(open(os.path.join(HERE, "seeds", "vision_paint.json")))


# =========================================================================== #
#  ARM V — §13.2 VACUITY. FIRST: a decorative mechanism proves nothing.
# =========================================================================== #
def test_V_the_decay_is_LOAD_BEARING_not_decorative():
    d = dm.arm_V()
    assert d["ALL_ZERO_would_be_decorative"] is False
    for k in ("ppaint_lum", "presid_lum", "pdist", "panchor"):
        assert d[k] > 0.0, f"{k} did not move when pdecay was toggled"
    assert d["plam_off"] == 0.0 and d["plam_on"] == 4.5
    # And it moves NOTHING it must not: the region structure and the ORDER are
    # untouched, because the decay renders the order-2 code and never decides it.
    assert d["pregion"] == 0.0
    assert d["korder"] == 0.0


# =========================================================================== #
#  ARM V2 — §9. The committed rung reproduces EXACTLY with the flag off.
# =========================================================================== #
def test_V2_a_fresh_boot_ships_pdecay_OFF():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_paint"])
    p = list(s.nodes("PaintParams"))[0]
    assert float(s.node(p)["attrs"]["pdecay"]) == 0.0
    assert float(s.node(p)["attrs"]["paint"]) == 0.0


@pytest.mark.slow
def test_V2_with_the_flag_OFF_the_paint_rung_reproduces_BYTE_IDENTICALLY():
    """§9. Every arm of `results/paint_measure.json` is re-run in-process
    against the v1.1.0 seed and compared key for key. `wgt` is folded into each
    slope term rather than around their sum precisely so that this holds down to
    the last ULP rather than by luck."""
    d = dm.arm_V2_byte_identity()
    assert d["shipped_pdecay_default"] == 0.0
    assert d["mismatched_arms"] == []
    assert d["IDENTICAL"] is True


# =========================================================================== #
#  G1 / ARM 1 — Cornsweet appears with the CORRECT SIGN at the ESCALATED order
# =========================================================================== #
def test_ARM1_cornsweet_sign_is_CORRECTED_at_the_order_the_residual_REACHES():
    """The paint rung's I3 negative, overturned. Two physically identical flat
    far-fields are painted +0.727273 apart in the direction of the cusp
    polarity, at korder 2 — the order the ladder actually reaches. The verdict
    is NOT read at an intermediate k=1 state; that would be §5 surgery."""
    d = dm.arm_1_and_2()["ARM1"]
    assert d["difference_off"] == pytest.approx(-1.8181818181818, abs=1e-9)
    assert d["difference_on"] == pytest.approx(+0.7272727272727, abs=1e-9)
    assert d["SIGN_CORRECT"] is True
    assert d["korder_left"] == 2.0 and d["korder_right"] == 2.0
    assert d["ESCALATED"] is True
    assert d["PASS"] is True


def test_ARM1_the_decay_LENGTH_fell_out_and_its_closed_form_is_ONE_THIRD():
    """§13. `plam` is the region's own mean geodesic depth — geometry, no
    tuning. For a region anchored on ONE side `pdist` is uniform on 0..d_max, so
    plam = d_max/2 EXACTLY and the far-edge weight is 1/3 INDEPENDENT of width.
    Nothing was chosen to make that 1/3; it is what a uniform depth
    distribution gives, and it is what fixes the sign: the plane's far-field
    excursion (1.909) is cut to 0.636, which no longer clears the region mean's
    own offset from the physical value (1.000)."""
    d = dm.arm_1_and_2()["CLOSED_FORM"]
    assert d["plam"] == 4.5
    assert d["d_max"] == 9.0
    assert d["far_weight"] == pytest.approx(1.0 / 3.0, abs=1e-12)
    assert d["far_excursion_undamped"] == pytest.approx(1.9090909090909, abs=1e-9)
    assert d["mean_minus_physical"] == pytest.approx(1.0, abs=1e-12)
    # the inversion criterion, stated as a MARGIN rather than a pass
    assert d["far_excursion_undamped"] > d["mean_minus_physical"]      # plane inverts
    assert d["far_excursion_undamped"] / 3.0 < d["mean_minus_physical"]  # decay does not


def test_ARM1_the_ANCHOR_SET_is_the_CUSP_and_not_the_field_border():
    """The pre-registration's named proviso, measured rather than assumed: if
    the field border anchored, or the far side of the cusp did, every number
    above would be wrong. The anchors are EXACTLY the two columns flanking the
    cusp."""
    d = dm.arm_1_and_2()["decay_pdecay_on"]
    assert d["panchor_row3"] == [0.0] * 9 + [1.0, 1.0] + [0.0] * 9
    assert d["pdist_row3"] == [9, 8, 7, 6, 5, 4, 3, 2, 1, 0,
                               0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


# =========================================================================== #
#  G1 / ARM 2 — the Blakeslee & McCourt decline, AND ITS POSITIVE CONTROL
# =========================================================================== #
def test_ARM2_induction_DECLINES_with_distance_on_BOTH_far_fields():
    """Measured only on the PHYSICALLY UNIFORM far fields, against the
    STIMULUS's own distance from the cusp — never against `pdist`, because a
    diagnostic must not be computed by the component it checks."""
    d = dm.arm_1_and_2()["ARM2"]
    for side in ("decay_left", "decay_right"):
        assert d[side]["distances"] == [4, 5, 6, 7, 8, 9]
        assert d[side]["abs_by_distance"] == [
            pytest.approx(v, abs=1e-6) for v in
            [1.112299, 0.899522, 0.727273, 0.584980, 0.465455, 0.363636]]
        assert d[side]["strictly_declining"] is True
        assert d[side]["no_sign_change"] is True
    assert d["PASS"] is True


def test_ARM2_IS_POSITIVE_CONTROLLED_the_committed_plane_FAILS_it():
    """§12.3's standard applied to the arm itself: a gate you have only ever
    seen pass is not a gate you have tested. The SAME predicate, on the SAME
    cells, run against the committed order-2 plane: it is NOT monotone and it
    DOES change sign — it declines, overshoots THROUGH the null, and comes back
    up inverted. That is the failure mode this rung exists to fix, and the arm
    detects it."""
    d = dm.arm_1_and_2()["ARM2"]
    assert d["baseline_left"]["strictly_declining"] is False
    assert d["baseline_left"]["no_sign_change"] is False
    assert d["BASELINE_PASS"] is False
    assert d["baseline_left"]["abs_by_distance"] == [
        pytest.approx(v, abs=1e-6) for v in
        [1.212121, 0.787879, 0.363636, 0.060606, 0.484848, 0.909091]]


def test_ARM2s_direction_is_FORCED_by_the_construction_and_is_declared_so():
    """§13.1's third category, asserted rather than narrated. The FORM of the
    falloff went in as architecture, so the DIRECTION of ARM 2 could not have
    come out the other way; what the arm actually risks is STRICTNESS of the
    TOTAL induction (a product whose deviation factor CHANGES SIGN inside the
    left far field) and the absence of a sign change. This test pins the
    declaration itself: the mechanism's own seed comment says the weight is
    monotone by construction."""
    rules = {r["name"]: r for r in _seed()["rules"]}
    assert "STRICTLY DECREASING" in rules["pt_paint"]["comment"]
    assert "ARCHITECTURE" in rules["pt_paint"]["comment"]
    assert "cannot fail to appear" in rules["pt_paint"]["comment"]
    # commit 3f9d7c3 moved 1105 root/docs markdown files into docs/research/<topic>/
    prereg = open(os.path.join(HERE, "docs", "research", "vision",
                               "VISION_DECAY_PREREG.md")).read()
    assert "FORCED by the" in prereg and "§13.1's third category" in prereg


# =========================================================================== #
#  ARM 3 — THE RESIDUAL ARM MUST STILL PASS
# =========================================================================== #
def test_ARM3_the_mechanism_STILL_KNOWS_WHEN_IT_IS_WRONG():
    d = dm.arm_3()
    u, g, t = d["R1_uniform"], d["R2_gradient"], d["R3_texture"]
    assert u["n_regions"] == 1 and u["largest_korder"] == 1.0
    assert u["any_region_refuted"] is False and u["mean_cell_residual"] == 0.0
    assert g["n_regions"] == 1 and g["largest_korder"] == 2.0
    assert g["any_region_refuted"] is False and g["mean_cell_residual"] == 0.0
    assert g["largest_slope_c"] == pytest.approx(3.0)      # the true slope, exactly
    assert t["largest_korder"] == 2.0 and t["any_region_refuted"] is True
    assert t["refuted_area_fraction"] > 0.9
    assert t["mean_cell_residual"] >= 0.5
    assert t["n_regions"] < 10
    assert t["mean_cell_residual"] > u["mean_cell_residual"]
    assert d["PASS"] is True


def test_ARM3_R1_and_R2_are_UNTOUCHED_because_NO_EDGE_MEANS_NO_ANCHOR():
    """Not luck — the invariant. A uniform field and a linear ramp have NO
    strict-|Δ| maximum anywhere, so they have no boundary, so `panch_n` is 0,
    so the weight is the literal 1.0 and the render is v1.0.0's. This is what
    keeps the ramp's exact slope recovery alive under a code that is, by
    construction, not a faithful gradient code."""
    d = dm.arm_3()
    assert d["R1_uniform"]["largest_panch_n"] == 0.0
    assert d["R2_gradient"]["largest_panch_n"] == 0.0
    # `plam` in an UNANCHORED region is meaningless and SATURATES at the cap
    # (the field's own cell count, 12x12 = 144) — the flood has nothing to
    # measure from, so it climbs until the terminator stops it. It is `panch_n`
    # that is load-bearing, not `plam`: with no anchor the weight takes the
    # literal 1.0 and `plam` is never read. Pinned so the saturation is a
    # declared fact rather than a surprise to a successor.
    assert d["R1_uniform"]["largest_plam"] == 144.0
    assert d["R2_gradient"]["largest_plam"] == 144.0


@pytest.mark.slow
def test_ARM3_F1_noise_floor_never_invents_appearance_from_none():
    d = dm.arm_3_F1()
    assert d["n_fields_inventing_appearance"] == 0
    assert d["max_abs_painted_app"] == 0.0
    assert d["PASS"] is True


@pytest.mark.slow
def test_ARM3_F2_texture_floor_at_power():
    d = dm.arm_3_F2()
    assert d["fraction_any_region_refuted"] > 0.9
    assert d["mean_n_regions"] < 10
    assert d["PASS"] is True


# =========================================================================== #
#  ARM 3b — R5, THE COST. PINNED AS A REGRESSION (§7).
# =========================================================================== #
def test_ARM3b_R5_the_COST_a_REAL_bounded_ramp_is_UNDER_RENDERED_negative():
    """THE PRICE, PINNED. A genuine linear ramp inside a BOUNDED compartment
    (two steps that ARE strict-|Δ| maxima) is fitted perfectly — `pt_fit2` is
    untouched, so the slope is still recovered as EXACTLY 3.0 — and then
    RENDERED wrong, because the decay suppresses the very extrapolation that
    made the render exact. The region goes from not-refuted to REFUTED.

    This is not a bug to be fixed later. The mechanism CANNOT distinguish a
    genuine bounded ramp from a Cornsweet shoulder, because THEY ARE THE SAME
    SIGNAL: a gradient running up to an edge. The suppression that corrects one
    necessarily breaks the other. Pinned here so no successor can inherit ARM 1
    without inheriting this."""
    d = dm.arm_3b_R5()
    assert d["FIT_UNCHANGED"] is True
    assert d["pdecay_off"]["ramp_region"]["pslope_c_plum"] == pytest.approx(3.0)
    assert d["pdecay_on"]["ramp_region"]["pslope_c_plum"] == pytest.approx(3.0)
    assert d["pdecay_off"]["ramp_region"]["presid_mean"] == 0.0
    assert d["pdecay_on"]["ramp_region"]["presid_mean"] > 0.0
    assert d["REFUTED_off_on"] == [0.0, 1.0]
    assert d["RENDERING_DAMPED"] is True
    assert d["REGRESSES"] is True
    # and the mechanism SAYS SO — it does not silently mis-render
    assert d["pdecay_on"]["ramp_region"]["prefuted"] == 1.0


# =========================================================================== #
#  G2 — the CUMULATIVE geometry, measured SEPARATELY and NOT POOLED
# =========================================================================== #
def test_G2_cumulative_cornsweet_is_ABSENT_not_inverted_negative():
    """Cavanagh & Anstis 2018 report a cumulative human percept OPPOSING the
    local gradients, so inversion under this geometry would not be proof of a
    bug. Our mechanism produces neither: it produces NOTHING. Every interior
    unit is a translate of every other, and cusps are region boundaries, so the
    steps cannot accumulate — regions do not communicate.

    THE SAME FIELD SEGMENTATION THAT FIXES SINGLE-EDGE CORNSWEET FORBIDS
    CUMULATIVE CORNSWEET. Reported and pinned; never pooled with G1."""
    d = dm.arm_G2()
    assert len(d["plateau_cells"]) == 3
    assert all(v == 100.0 for v in d["physical_at_plateaus"])
    for tag in ("pdecay_off", "pdecay_on"):
        assert d[tag]["ALL_EQUAL"] is True
        assert d[tag]["monotone_decreasing"] is False
        assert d[tag]["monotone_increasing"] is False
    # AND THE ABSENCE IS NOT THIS RUNG'S DOING — it is already v1.0.0's
    # behaviour, because it follows from the REGION SEGMENTATION, which this
    # rung did not change. The decay only shifts the common value.
    assert d["pdecay_off"]["painted_at_plateaus"] == [pytest.approx(99.685315)] * 3
    assert d["pdecay_on"]["painted_at_plateaus"] == [pytest.approx(99.895105)] * 3
    assert d["pdecay_off"]["region_means"] == d["pdecay_on"]["region_means"]


# =========================================================================== #
#  ARM B — BOUNDS (§8). Reported; does not move the verdict.
# =========================================================================== #
def test_ARM_B_the_sign_holds_at_three_widths_and_the_baseline_inverts_at_all_three():
    d = dm.arm_B()
    for k in ("flat_3", "flat_6", "flat_12"):
        assert d[k]["sign_correct_on"] is True, k
        assert d[k]["sign_correct_off"] is False, k
        assert d[k]["far_weight"] == pytest.approx(1.0 / 3.0, abs=1e-12), k
    assert d["ALL_WIDTHS_CORRECT_SIGN_ON"] is True
    assert d["ALL_WIDTHS_INVERTED_OFF"] is True
    # the magnitude SHRINKS with width — declared as a bound, not a result
    assert (d["flat_3"]["difference_on"] > d["flat_6"]["difference_on"]
            > d["flat_12"]["difference_on"] > 0.0)


# =========================================================================== #
#  ARM P — the paint rung's own positives survive
# =========================================================================== #
def test_ARM_P_the_paint_rungs_positives_are_NOT_destroyed_by_the_decay():
    """I1's slopes are zero by the stimulus's own symmetry, so the weight
    multiplies a zero and neon spreading is UNMOVED. I2's read cell sits at the
    region centroid, where the plane IS the mean, so watercolour still takes the
    INNER contour. Neither is a new result; both are checked because a
    successor must not silently lose them."""
    d = dm.arm_P()
    assert d["I1_PRESERVED"] is True
    assert d["I2_STILL_INNER"] is True


# =========================================================================== #
#  §9 / SOURCE GATES — no decision in Python, no Rust, no foreign files
# =========================================================================== #
def test_korder_is_STILL_assigned_by_ONE_SEED_RULE_and_the_decay_never_touches_it():
    """The structural invariant the whole rung rests on: the decay renders the
    order-2 code, it does not DECIDE the order. `pt_escalate` is still the only
    writer of `korder` anywhere in the seed, and none of the three new rules
    writes it."""
    seed = _seed()
    writers = [r["name"] for r in seed["rules"]
               if any(e[0].startswith("set_attr") and e[2] == "korder"
                      for e in r["effects"])]
    assert writers == ["pt_escalate"], writers
    new = {"pt_anchor", "pt_dist", "pt_decay"}
    assert new <= {r["name"] for r in seed["rules"]}
    for r in seed["rules"]:
        if r["name"] in new:
            assert all(e[2] != "korder" for e in r["effects"])


def test_the_decay_attributes_are_written_ONLY_by_the_decay_rules():
    """§12 — a selector that matches by substring is not a selector. Enumerated
    positively: exactly which rule writes each new attribute."""
    seed = _seed()
    by_attr = {}
    for r in seed["rules"]:
        for e in r["effects"]:
            if e[0].startswith("set_attr"):
                by_attr.setdefault(e[2], []).append(r["name"])
    assert by_attr["panchor"] == ["pt_anchor"]
    assert by_attr["panchor_done"] == ["pt_anchor"]
    assert by_attr["pdist"] == ["pt_dist"]
    assert by_attr["plam"] == ["pt_decay"]
    assert by_attr["panch_n"] == ["pt_decay"]


def test_the_decay_adapter_makes_NO_DECISION_over_graph_state():
    """CLAUDE.md / §0, by AST rather than by grep — the same standard the paint
    rung's adapter is held to. Every conditional and comprehension-guard in
    `decay_world.py` is collected and none may mention any attribute the
    mechanism computes."""
    import ast as _ast
    src = open(os.path.join(HERE, "domains", "decay_world.py")).read()
    tree = _ast.parse(src)
    decided = {"panchor", "pdist", "plam", "panch_n", "pregion", "korder",
               "prefuted", "prefuted_cell", "pblk_e", "pblk_s", "ppaint_lum",
               "ppaint_app", "presid_lum", "presid_app", "pmean_lum",
               "pmean_app", "paint", "pdecay", "pd_e", "pd_s", "presid_mean"}
    tests = []
    for node in _ast.walk(tree):
        if isinstance(node, (_ast.If, _ast.IfExp)):
            tests.append(node.test)
        elif isinstance(node, _ast.comprehension):
            tests.extend(node.ifs)
    for t in tests:
        names = {n.value for n in _ast.walk(t)
                 if isinstance(n, _ast.Constant) and isinstance(n.value, str)}
        names |= {n.id for n in _ast.walk(t) if isinstance(n, _ast.Name)}
        names |= {n.attr for n in _ast.walk(t) if isinstance(n, _ast.Attribute)}
        leaked = names & decided
        assert not leaked, f"the adapter branches on graph state: {leaked}"


@_skip_unresolvable_pin(BASE_SHA, RUNG_END_SHA)
def test_the_paint_rungs_OWN_files_are_NOT_EDITED_by_this_rung():
    """§11 rule 4, and the reason `decay_world.py` exists at all: the paint
    rung's gate reads its adapter's LIVE source and asserts its only `set_attr`
    write is `paint`. That result is not this rung's to disturb."""
    changed = [f.split("gamma-substrate/")[-1] for f in _rung_diff_names()]
    for f in ("domains/paint_world.py", "scripts/paint_measure.py",
              "tests/test_paint_migrated.py"):
        assert f not in changed, f


@_skip_unresolvable_pin(BASE_SHA, RUNG_END_SHA)
def test_this_rung_adds_NO_Rust():
    changed = _rung_diff_names()
    assert changed, "expected a non-empty rung diff"
    rs = [f for f in changed if f.endswith(".rs")]
    assert rs == [], f"this rung claims NO new Rust but touched: {rs}"


@_skip_unresolvable_pin(BASE_SHA, RUNG_END_SHA)
def test_this_rung_edits_NO_OTHER_RUNGS_SEED_OR_ADAPTER():
    changed = [f.split("gamma-substrate/")[-1] for f in _rung_diff_names()]
    allowed = {
        "VISION_DECAY_PREREG.md", "VISION_DECAY_RESULTS.md",
        "tools/build_vision_paint.py", "seeds/vision_paint.json",
        "domains/decay_world.py", "scripts/decay_measure.py",
        "results/decay_measure.json",
        "tests/test_decay_gradient_migrated.py",
    }
    assert set(changed) <= allowed, \
        f"foreign files in this rung's diff: {set(changed) - allowed}"


def test_the_runner_and_the_gate_write_NO_graph_attribute():
    import re as _re
    runner = open(os.path.join(HERE, "scripts", "decay_measure.py")).read()
    assert _re.findall(r"\.set_attr\(", runner) == []
    gate = open(os.path.abspath(__file__)).read()
    assert _re.findall(r"\.set_attr\(", gate) == []
    # the adapter's ONLY attr writes are the flag blind-write and the
    # clean-zero initialisation — never a computed value
    adapter = open(os.path.join(HERE, "domains", "decay_world.py")).read()
    writes = _re.findall(r"\.set_attr\([^,]+,\s*(k|\"[a-z_]+\")", adapter)
    assert sorted(set(writes)) == ['"pdecay"', "k"], writes
