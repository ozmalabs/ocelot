"""GATES for the K-SCOPE rung (Phase 1).

Pre-registration: VISION_K_SCOPE_PREREG.md @ 32e1d62b.

This rung re-analyses committed per-frame rows; it adds no Rust, no Term, no
seed rule and no constant, and it consumes NO seed from block 76000-76999.
The gates below lock (a) the instrument checks the pre-registration made
STOPPING conditions, (b) the positive control on the instrument that issues
every verdict, and (c) the verdict itself.
"""
import json
import os
import subprocess
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import k_scope_analyse as ks  # noqa: E402


@pytest.fixture(scope="module")
def R():
    path = os.path.join(ROOT, "results", "k_scope.json")
    if not os.path.exists(path):
        subprocess.run([sys.executable, os.path.join(ROOT, "scripts",
                                                     "k_scope_analyse.py")],
                       check=True, cwd=ROOT, capture_output=True)
    return json.load(open(path))


# --------------------------------------------------------------- gate G1
def test_G1_reanalysis_reproduces_both_published_contrasts(R):
    """If the re-analysis cannot reproduce the numbers it re-analyses, it is
    measuring something else. Pre-registered STOPPING condition."""
    assert R["G1_pass"] is True
    for cid in ("C1", "C2"):
        for name, (mine, published, ok) in R["corpora"][cid]["G1"]["checks"].items():
            assert ok, f"{cid} {name}: mine={mine} published={published}"


# --------------------------------------------------------------- gate G2
def test_G2_the_primary_readout_is_floor_independent_BY_SOURCE():
    """Both rungs CLAIM the primary read-out is floor-independent while also
    measuring that a grown codebook RAISES its own floor. The claim is
    verified here from the seed, not inherited: `is_max` must be written by
    `is_score` alone, with no floor term, and `is_decide` must only READ it.
    """
    seam = json.load(open(os.path.join(ROOT, "seeds",
                                       "vision_identity_seam.json")))
    writers = {}
    for rule in seam["rules"]:
        for eff in rule.get("effects", []):
            if eff[0] == "set_attr" and eff[2] == "is_max":
                writers[rule["name"]] = json.dumps(eff)
    assert set(writers) == {"is_score"}, (
        f"is_max must be written only by is_score, got {sorted(writers)}")
    term = writers["is_score"]
    assert "floor" not in term and "is_floor" not in term, (
        "the primary read-out's own term references the floor")
    decide = next(r for r in seam["rules"] if r["name"] == "is_decide")
    assert [e[2] for e in decide["effects"] if e[0] == "set_attr"] == [
        "is_floor", "identified_as", "status"], (
        "is_decide's write set changed; re-audit floor-independence")


def test_G2_the_measurement_collects_is_max_unconditionally():
    """`eval_pass` must append is_max for every region, NOT only for accepted
    ones -- otherwise the primary read-out would be floor-gated after all."""
    src = open(os.path.join(ROOT, "scripts",
                            "video_accum_measure.py")).read()
    body = src.split("def eval_pass", 1)[1].split("\ndef ", 1)[0]
    lines = [ln.strip() for ln in body.splitlines()]
    i_max = next(i for i, ln in enumerate(lines)
                 if ln.startswith('m.append(float(r["is_max"]))'))
    i_held = next(i for i, ln in enumerate(lines)
                  if ln.startswith("if held_ok:"))
    assert i_max < i_held, "is_max collection moved under the held_ok branch"


# ------------------------------ positive control on the deciding instrument
def test_the_block_bootstrap_IS_ABLE_to_separate(R):
    """PROTOCOL SS1 clause 4 pointed at the gate itself: the block bootstrap
    issues every NOT-DISTINGUISHABLE verdict in this rung, so it must be
    shown capable of the opposite verdict."""
    pc = R["block_bootstrap_positive_control"]
    assert pc["shift_0.2"]["separates"] is True
    assert pc["shift_0.1"]["separates"] is True
    assert pc["null_zero_mean"]["separates"] is False
    assert R["block_bootstrap_is_able_to_separate"] is True


def test_the_block_bootstrap_cannot_resolve_the_disputed_magnitudes(R):
    """The honest scope of the null: the instrument's floor sits ABOVE every
    effect in the dispute (+0.0360, -0.0235, and their +0.0595 difference),
    so 'not distinguishable' means 'below resolution', never 'zero'."""
    pc = R["block_bootstrap_positive_control"]
    assert pc["shift_0.05"]["separates"] is False, (
        "if the bootstrap resolved 0.05 the null would mean something "
        "stronger than this rung claims")


# ------------------------------------------------- the unit-of-analysis fact
def test_the_block_not_the_frame_is_the_unit(R):
    """Both rungs quote CIs over 50 frames while stating in their own bounds
    that n=50 overstates the effective n. This gate makes the size of that
    error explicit: block means vary far more than independent frames could
    produce."""
    for cid in ("C1", "C2"):
        e = R["POSTHOC_effective_n"][cid]
        assert e["block_effect_inflation"] > 1.5
        assert e["block_is_the_right_unit"] is True
    assert R["POSTHOC_effective_n"]["C1"]["block_effect_inflation"] > 5.0


# ------------------------------------------------------------- the verdict
def test_the_two_rungs_are_NOT_distinguishable_on_either_corpus(R):
    for cid in ("C1", "C2"):
        ent = R["corpora"][cid]
        assert ent["VERDICT"] is False
        assert ent["size_matches_agree"] is True, (
            "the two pre-registered size-matches disagree; the "
            "pre-registration requires the conservative reading and a "
            "report of both")
    assert R["n_corpora_distinguishable"] == 0
    assert R["PHASE2_AUTHORISED"] is False


def test_the_accumulation_headline_does_not_survive_the_block_bootstrap(R):
    """POST-HOC, labelled: the +0.0360 C1 PASS that the video line rests on
    is a frame-unit result and does not survive the block unit."""
    ph = R["POSTHOC_inputs_under_block_bootstrap"]["C1"]["accum_GROWN_minus_UNIFORM"]
    assert ph["t_excludes_zero"] is True
    assert ph["boot_excludes_zero"] is False


# ------------------------------------------------- determinism of the rung
def test_the_bootstrap_is_seeded_and_reproducible():
    d = np.arange(50, dtype=float) / 50.0
    a = ks.block_bootstrap_ci(d)
    b = ks.block_bootstrap_ci(d)
    assert a["lo"] == b["lo"] and a["hi"] == b["hi"]


def test_this_rung_consumes_no_seed_from_its_block():
    """Phase 1 draws no calibration seed. The only RNG is the bootstrap's own
    (20260720), which is not a substrate seed and is outside 76000-76999.

    AST-walked, not substring-matched: a substring scan matches this rung's
    OWN PROSE (the docstrings that declare the block) and so cannot tell a
    consumed seed from a mentioned one -- the exact defect the accumulation
    rung found in its adapter audit by mutating it.
    """
    import ast
    src = open(os.path.join(ROOT, "scripts", "k_scope_analyse.py")).read()
    tree = ast.parse(src)

    # every integer literal that reaches executable code (docstrings and
    # comments are not in the AST as constants we walk into)
    literals = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            literals.append(node.value)
    offenders = [v for v in literals if 76000 <= v <= 76999]
    assert not offenders, f"seed-block literals in executable code: {offenders}"

    # and the RNGs are exactly the two declared bootstrap streams
    seeds_used = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            name = getattr(fn, "attr", getattr(fn, "id", ""))
            if name in ("RandomState", "seed", "default_rng"):
                seeds_used.append(ast.unparse(node.args[0]) if node.args else None)
    assert seeds_used, "no RNG found; the audit would be vacuous"
    for s in seeds_used:
        assert s in ("seed", "BOOT_SEED + 1"), f"unexpected RNG seed: {s}"


def test_the_seed_block_audit_is_ABLE_to_fail(tmp_path):
    """A gate that has never been able to fail has not been tested. Plant a
    seed-block literal in executable code and require the audit to catch it
    -- and confirm the same literal in a DOCSTRING is correctly ignored."""
    import ast

    def offenders(src):
        return [v for v in
                (n.value for n in ast.walk(ast.parse(src))
                 if isinstance(n, ast.Constant) and isinstance(n.value, int))
                if 76000 <= v <= 76999]

    assert offenders("x = np.random.RandomState(76000)") == [76000]
    assert offenders('"""uses block 76000-76999."""\nx = 1') == []
