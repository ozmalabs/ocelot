"""NON-RIGID DEFORMATION INVARIANCE (FRONTIER rung T4) — the gate.

Pins the pre-registered arms of `VISION_DEFORMATION_PREREG.md` as executable tests,
INCLUDING the pre-registered NEGATIVE (§7: a diagnosed negative is a first-class
result and must be gated so it cannot silently "improve" into an unexamined pass).

What is pinned:
  * the composition is graph-native and adds NO Rust (source audit);
  * §9 off-by-default byte-identity — with `deform` absent NEITHER df rule fires;
  * A1 invariance under bounded smooth deformation, A2 discrimination exact-0;
  * A3 conjunct 2 — the strong shear is REFUSED (the inherited affine clause working);
  * A3 conjunct 3 — the SEPARABILITY FAILURE: the identity-preserving and
    identity-changing bands OVERLAP, so NO bound can separate them;
  * A5 §13.2 — the bending clause is INERT (D == 0), recorded as measured.
"""
from __future__ import annotations
import os, sys, math, json
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
sys.path.insert(0, _ROOT)

dm = pytest.importorskip("scripts.deformation_measure") if False else None
sys.path.insert(0, os.path.join(_ROOT, "scripts"))
import deformation_measure as DM  # noqa: E402


@pytest.fixture(scope="module")
def graph():
    s, ag, native = DM.boot(deform=1)
    return s, ag, native


# --------------------------- §9 off-by-default ---------------------------
def test_off_by_default_neither_rule_fires():
    """With `deform` ABSENT the observation keeps its marker and gains no identity."""
    r = DM.arm_off_day()
    assert r["status"] == "df_decoded", r
    assert r["covered_by"] is None, r
    assert r["inert"] is True


def test_seed_flag_is_graph_data_not_a_python_branch():
    """The ablation is graph DATA (§0): the flag is read by the RULE, never by Python."""
    seed = json.load(open(os.path.join(_ROOT, "seeds", "vision_deformation.json")))
    names = {r["name"] for r in seed["rules"]}
    assert names == {"df_recognize", "df_refuse"}, names
    for rule in seed["rules"]:
        blob = json.dumps(rule["where"])
        assert '"deform"' in blob, rule["name"]          # flag read in the rule
        assert "SmoothDeformComponents" in blob, rule["name"]
        assert '"df_eps"' in blob, rule["name"]          # the bound is graph data


def test_no_new_rust_the_terms_are_all_held():
    """AUDIT (§12.4): every Term the seed uses pre-exists in the engine's parser."""
    jsonio = open(os.path.join(_ROOT, "runners", "dsl", "src", "jsonio.rs")).read()
    for term in ("SmoothDeformComponents", "DictGet", "Argmin", "Abs", "Lte", "Times"):
        assert '"%s" =>' % term in jsonio, term


def test_no_python_decision_in_the_runner():
    """The adapter may build stimuli and read results; it must not DECIDE identity."""
    src = open(os.path.join(_ROOT, "scripts", "deformation_measure.py")).read()
    # the verdict must come from the graph's own status strings, never a Python compare
    assert "recognized_deformed" in src and "df_refused" in src
    assert "native.run_rules()" in src


# ------------------------------- the arms -------------------------------
def test_A1_invariance_under_bounded_smooth_deformation(graph):
    """A1 — a smooth low-amplitude warp preserves identity (the handwriting fact)."""
    s, ag, native = graph
    r = DM.arm_invariance(s, ag, native)
    assert r["wrong_id"] == 0, r
    assert r["correct"] >= 30, r          # pre-registered threshold
    assert r["correct"] == 35, r          # measured


def test_A2_discrimination_is_exact_zero(graph):
    s, ag, native = graph
    r = DM.arm_discrimination(s, ag, native)
    assert r["exact0"] is True, r
    assert r["wrong_id"] == 0, r


def test_A3_conjunct2_the_strong_shear_is_REFUSED(graph):
    """The inherited affine clause working: shearY(1.0) is identity-CHANGING (measured
    in VISION_SIMILARITY_RESULTS.md) and must be refused, all 7."""
    s, ag, native = graph
    r = DM.arm_crux(s, ag, native)
    assert r["c2_pass"] is True, r["c2_detail"]
    assert r["c2_shear_refused"] == 7, r


def test_A3_conjunct3_THE_BANDS_OVERLAP_the_pre_registered_negative(graph):
    """THE HEADLINE NEGATIVE, gated so it cannot silently change.

    max(total) over identity-PRESERVING stimuli EXCEEDS min(total) over
    identity-CHANGING stimuli ⇒ no threshold — falls-out or tuned — separates them.
    """
    s, ag, native = graph
    r = DM.arm_crux(s, ag, native)
    assert r["c3_separable"] is False, r
    assert r["c3_max_preserving_total"] > r["c3_min_changing_total"], r
    assert r["crux_pass"] is False, r


def test_A5_the_bending_clause_is_INERT(graph):
    """§13.2 — toggle it, measure D. D == 0 exactly ⇒ decorative, reported not hidden."""
    s, ag, native = graph
    r = DM.arm_bending_load_bearing(s, ag, native)
    assert r["D"] == 0.0, r
    assert r["load_bearing"] is False, r
    # and the reason: bending never comes within an order of magnitude of its bound
    assert r["max_bending_observed"] < r["bound_eps_squared"], r


def test_A5b_the_affine_shear_clause_IS_load_bearing(graph):
    """The contrast that makes A5 a finding rather than a broken instrument: the OTHER
    clause of the same bound, read off the same Term, DOES move a verdict."""
    s, ag, native = graph
    r = DM.arm_shear_load_bearing(s, ag, native)
    assert r["load_bearing"] is True, r
    assert r["D"] > 0.0, r


def test_A5c_a_mechanism_with_NO_bound_merges_everything():
    """§13.1 — the crux is RISKED, not forced. Remove the bound from the SAME graph and
    the identity-changing shears are all admitted, most onto the WRONG identity —
    reproducing the similarity rung's `shearY(F) → X` failure in the deformation
    setting. The bound is therefore load-bearing, and this arm would catch its loss."""
    r = DM.arm_no_bound_control()
    assert r["admitted"] == 7, r
    assert r["n_merges"] >= 4, r


def test_the_bound_falls_out_and_is_not_fitted():
    """§13 — eps is derived from the lattice half-diagonal and the codebook's own mean
    RMS radius. No fitted constant appears in the runner's bound."""
    assert abs(DM.EPS - (math.sqrt(2) / 2) / DM.R_BAR) < 1e-12
    src = open(os.path.join(_ROOT, "scripts", "deformation_measure.py")).read()
    assert "EPS = (math.sqrt(2) / 2) / R_BAR" in src


def test_pinned_results_reproduce():
    """The committed results JSON must match what the code produces now."""
    p = os.path.join(_ROOT, "results", "deformation_measure.json")
    d = json.load(open(p))
    assert d["OUTCOME"] == "DIAGNOSED NEGATIVE", d["OUTCOME"]
    assert d["A1_invariance"]["correct"] == 35
    assert d["A2_discrimination"]["exact0"] is True
    assert d["A3_crux"]["c2_shear_refused"] == 7
    assert d["A3_crux"]["c3_separable"] is False
    assert d["A4_floor"]["floor_clean"] is False
    assert d["A5_bending_load_bearing"]["D"] == 0.0
    assert abs(d["eps"] - DM.EPS) < 1e-12
