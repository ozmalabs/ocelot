"""GATES for the block-unit re-analysis (VISION_BLOCK_UNIT_PREREG.md @ 5c75bc39).

Every gate here is a stopping condition named in the pre-registration BEFORE
any contrast number existed. Two are positive-controlled.
"""
import ast
import json
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

RESULT = os.path.join(ROOT, "results", "block_unit.json")
SELECTOR = os.path.join(ROOT, "scripts", "block_unit_analyse.py")
KSCOPE = os.path.join(ROOT, "scripts", "k_scope_analyse.py")


@pytest.fixture(scope="module")
def R():
    with open(RESULT) as fh:
        return json.load(fh)


# ---------------------------------------------------------------- G1
def test_G1_every_published_endpoint_reproduces(R):
    """The re-analysis must reproduce what it re-analyses, or it is measuring
    something else and every verdict below it is void."""
    assert R["G1_all_reproduce"] is True
    checked = [e for e in R["contrasts"].values() if e["G1_reproduces"] is not None]
    assert len(checked) == 30, "all 30 in-scope contrasts must be checked"
    bad = [e["contrast"] for e in checked if not e["G1_reproduces"]]
    assert bad == [], f"did not reproduce: {bad}"


def test_G1_covers_the_priority_contrast_against_the_DOC_not_the_raw(R):
    """The line's strongest claim must be checked against the published doc
    value, not against a number the same pipeline stored."""
    for cid, mean in (("C1", 0.0625), ("C2", 0.0475)):
        e = R["contrasts"][f"accum|{cid}|GROWN-CUTMATCHED@90"]
        assert e["G1_source"] == "doc"
        assert e["G1_reproduces"] is True
        assert abs(e["G1_reference"][0] - mean) < 5e-5


# ---------------------------------------------------------------- G2
def test_G2_the_instrument_is_positive_controlled_on_every_vector(R):
    """PROTOCOL Section 1 clause 4: an instrument that has never been ABLE to
    separate is not an instrument. Here it must be shown able on EACH vector,
    not once globally."""
    assert R["G2_every_vector_has_a_floor"] is True
    for k, e in R["contrasts"].items():
        assert e["resolution_floor_delta_star"] is not None, k
        assert 0 < e["resolution_floor_delta_star"] <= 0.300, k


def test_G2_a_zero_mean_null_does_not_separate(R):
    """And it must correctly REFUSE a null, or it separates everything."""
    assert R["G2_no_null_separates"] is True
    assert len(R["G2_null_controls"]) >= 3
    for k, v in R["G2_null_controls"].items():
        assert v["separates"] is False, k


# ---------------------------------------------------------------- G3
def test_G3_the_correction_is_one_directional(R):
    """The block correction resamples whole blocks and can only WIDEN. If any
    bootstrap interval were narrower than its t-CI that would be an instrument
    fault, and it would mean a null could be 'rescued' by this re-analysis."""
    assert R["G3_correction_is_one_directional"] is True
    for k, e in R["contrasts"].items():
        assert e["boot_width"] >= e["t_width"], k
        assert e["width_ratio"] >= 1.0, k
        # width is derived at the call site, never added to the inherited fn
        assert "width" not in e["block_boot"], k


def test_G3_no_published_null_became_a_pass(R):
    """The direct consequence of G3, asserted on the actual table: nothing
    that failed at the frame unit may pass at the block unit."""
    for k, e in R["contrasts"].items():
        if not e["t_excludes_zero"]:
            assert e["CLASS"] != "SURVIVES", f"{k} was null and now survives"


# ---------------------------------------------------------------- G4
def _int_constants_in_executable_code(path):
    """AST walk. NEVER a substring scan -- a substring scan cannot tell a
    CONSUMED seed from a MENTIONED one, and in this arc it has now gone wrong
    three times, once going red on the docstring that declared the block."""
    with open(path) as fh:
        tree = ast.parse(fh.read())
    # strip docstrings: they are prose, not executable code
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                node.body = body[1:]
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, int) \
                and not isinstance(node.value, bool):
            out.append(node.value)
    return out


def test_G4_this_rung_consumes_no_seed_from_its_block():
    """Block 77000-77999 was ALLOCATED and must be returned INTACT."""
    for v in _int_constants_in_executable_code(SELECTOR):
        assert not (77000 <= v <= 77999), f"seed {v} appears in executable code"


def test_G4_the_seed_audit_is_ABLE_to_fail(tmp_path):
    """Positive control on the audit itself: a planted consumption must be
    caught, and the same literal in a DOCSTRING must be ignored."""
    planted = tmp_path / "planted.py"
    planted.write_text(
        '"""A docstring mentioning 77000, which must be IGNORED."""\n'
        "import numpy as np\n"
        "rng = np.random.RandomState(77123)\n")
    vals = _int_constants_in_executable_code(str(planted))
    assert any(77000 <= v <= 77999 for v in vals), "planted seed NOT caught"

    clean = tmp_path / "clean.py"
    clean.write_text('"""Block 77000-77999 declared and unused."""\nx = 1\n')
    vals = _int_constants_in_executable_code(str(clean))
    assert not any(77000 <= v <= 77999 for v in vals), "docstring literal caught"


# --------------------------------------------- Section 4.1, the discipline
def test_below_resolution_is_never_reported_as_absence(R):
    """THE GATE THIS RUNG EXISTS TO PROTECT.

    'Below resolution' is a fact about the MEASUREMENT DESIGN, not about the
    mechanism. No successor may quietly upgrade it into a demonstration that
    the effect is zero."""
    banned = ("zero", "absent", "no effect", "null effect", "refut",
              "disproved", "does not exist")
    for k, e in R["contrasts"].items():
        if e["CLASS"] == "BELOW RESOLUTION":
            assert e["reading"] is not None, k
            assert "NOT" in e["reading"] and "either direction" in e["reading"].lower(), k
        else:
            assert e["reading"] is None, k
    # and the class name itself must not assert absence
    for e in R["contrasts"].values():
        assert e["CLASS"] in ("SURVIVES", "AMBIGUOUS", "BELOW RESOLUTION")
        assert not any(b in e["CLASS"].lower() for b in banned)


def test_the_classification_boundary_is_the_pre_registered_one(R):
    """0.5 * delta-star was fixed in the prereg and must not have moved."""
    assert R["ambiguous_fraction"] == 0.5
    for k, e in R["contrasts"].items():
        m, floor = abs(e["t_ci"]["mean"]), e["resolution_floor_delta_star"]
        if e["CLASS"] == "SURVIVES":
            assert e["boot_excludes_zero"] is True, k
        elif e["CLASS"] == "AMBIGUOUS":
            assert e["boot_excludes_zero"] is False and m >= 0.5 * floor, k
        else:
            assert e["boot_excludes_zero"] is False and m < 0.5 * floor, k


# ------------------------------------- no metric surgery on the instrument
def _func_ast(path, name):
    with open(path) as fh:
        tree = ast.parse(fh.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                node.body = body[1:]          # docstrings differ; code must not
            return ast.dump(node)
    raise AssertionError(f"{name} not found in {path}")


def test_the_block_bootstrap_is_INHERITED_VERBATIM_not_re_derived():
    """PROTOCOL Section 5. The verdict instrument is the one the K-scope rung
    pre-registered. Re-deriving or re-tuning it for this rung would be metric
    surgery, so the two function bodies must be AST-identical."""
    assert _func_ast(SELECTOR, "block_bootstrap_ci") == \
           _func_ast(KSCOPE, "block_bootstrap_ci")


def test_the_bootstrap_seed_and_reps_are_the_inherited_ones(R):
    assert R["boot_seed"] == 20260720
    assert R["boot_reps"] == 10000
    assert R["blocks"] == 5


def test_the_bootstrap_is_deterministic():
    """Same seed, same endpoints -- or none of the above is reproducible."""
    import block_unit_analyse as bu
    d = np.linspace(-0.05, 0.09, 50)
    a, b = bu.block_bootstrap_ci(d), bu.block_bootstrap_ci(d)
    assert (a["lo"], a["hi"]) == (b["lo"], b["hi"])


# ----------------------------------------------- the headline, gated
def test_the_priority_contrast_survives_on_both_corpora(R):
    """GROWN - CUTMATCHED is the line's strongest claim and the basis for
    'MDL selection works everywhere'. Recording its block-unit outcome so a
    successor cannot re-litigate it silently."""
    for cid in ("C1", "C2"):
        e = R["contrasts"][f"accum|{cid}|GROWN-CUTMATCHED@90"]
        assert e["CLASS"] == "SURVIVES"
        assert e["block_boot"]["lo"] > 0.0
        # all five episodes agree on the sign -- that is WHY it survives
        assert all(x > 0 for x in e["block_stats"]["block_means"])


def test_the_resolution_floor_is_NOT_a_corpus_constant(R):
    """The inherited '~0.10' is a property of the VECTOR it was measured on.
    Treating it as a corpus constant would bury every surviving result."""
    floors = [e["resolution_floor_delta_star"] for e in R["contrasts"].values()]
    assert max(floors) / min(floors) >= 5.0
    # concretely: the priority contrast's own floor is far below 0.10, so a
    # global 0.10 would have mis-classified it as below resolution.
    assert R["contrasts"]["accum|C1|GROWN-CUTMATCHED@90"][
        "resolution_floor_delta_star"] < 0.10


def test_the_episode_design_spec_is_labelled_a_projection(R):
    spec = R["EPISODE_DESIGN_SPEC"]
    assert "PROJECTION" in spec["LABEL"].upper()
    assert "exchangeable" in spec["assumption"]
    assert spec["table"]["typical_0.11"]["episodes_needed"]["0.03"] > 50
