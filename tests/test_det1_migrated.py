"""|det|=1 UNIMODULAR restriction on GenInfer — gate.

Pre-registered in `VISION_DET1_PREREG.md`, measured in
`scripts/det1_measure.py` -> `results/det1.json`. The seed guard restricts
discovered generators to the unimodular group GL(2,Z) (|det|=1) as GRAPH DATA
(the determinant of GenInfer's `matrix`, via Nth/Times/Minus/Abs Terms), gated
on a NEW flag `gen_unimodular`, OFF by default (§9).

OUTCOME 2 (PARTIAL): |det|=1 FIXES the det=0 universal-container collapse
(B1: collinear I no longer -> a full-rank object) but SHEARS (det=1) still
over-merge (a sheared pentomino aliases onto another) -> the identity-preserving
nuisance group is the SIMILARITY subgroup, NOT the full unimodular group.
"""
from __future__ import annotations

import json

import pytest

pytest.importorskip("substrate_rs")

from scripts.det1_measure import (
    OBJ, COLLINEAR, DET0, SCALE3, SHEARS, identify, lin, translate, det,
)


def _gen_infer_live() -> bool:
    from substrate.boot_core import boot_core
    s, ag = boot_core()
    try:
        s._inner.evaluate(
            {"type": "GenInfer",
             "goal": {"type": "Lit", "value": [["cell", 0, 0, "x"]]}}, {})
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _gen_infer_live():
    pytest.skip("GenInfer Term not yet landed in the installed substrate_rs wheel",
                allow_module_level=True)


# --- THE FIX: |det|=1 excludes det=0, so the collinear universal-container
#     leak (B1) is REFUSED under uni mode (was recognized_transformed -> L). ---
def test_B1_collinear_leak_refused_under_unimodular():
    _, cov, _ = identify(OBJ, COLLINEAR, gen_infer=True, uni=True)
    assert cov is None, "collinear I must be REFUSED under |det|=1 (det=0 excluded)"


# --- and it is a REAL fix: WITHOUT the restriction the leak is present ---
def test_B1_collinear_leaks_without_the_restriction():
    _, cov, _ = identify(OBJ, COLLINEAR, gen_infer=True, uni=False)
    assert cov is not None, "control: without |det|=1 the det=0 leak recognizes a full-rank object"


# --- FLOOR: a det=0 singular map and a non-held det=9 scale are BOTH refused ---
def test_det0_and_nonheld_scale_refused_under_unimodular():
    for src, cs in OBJ.items():
        _, c0, _ = identify(OBJ, translate(lin(cs, DET0), 3, 2), gen_infer=True, uni=True)
        assert c0 is None, f"det=0 map on {src} must be refused (|det|!=1)"
        _, c3, _ = identify(OBJ, translate(lin(cs, SCALE3), 3, 2), gen_infer=True, uni=True)
        assert c3 is None, f"non-held scale3 (det=9) on {src} must be refused"


# --- THE DEEPER FINDING (OUTCOME 2): shears (det=1) SURVIVE |det|=1 and still
#     over-merge — a sheared pentomino aliases onto ANOTHER identity. ---
def test_shear_over_merge_persists_under_unimodular():
    assert det(SHEARS["shearY"]) == 1 and det(SHEARS["shearX"]) == 1
    _, cov, _ = identify(OBJ, translate(lin(OBJ["F"], SHEARS["shearY"]), 3, 2),
                         gen_infer=True, uni=True)
    assert cov == "X", ("shearY(F) aliases onto X — a det=1 shear is admitted by "
                        "|det|=1 yet is identity-CHANGING (discrimination not exact-0)")


# --- held similarity is UNTOUCHED: scale2 (det=4) and rot90 (det=1) route via
#     the held DimInfer codebook BEFORE GenInfer, so uni mode preserves them. ---
def test_held_similarity_preserved_under_unimodular():
    _, c_s2, _ = identify(OBJ, translate(lin(OBJ["F"], [2, 0, 0, 2]), 3, 2),
                          gen_infer=True, uni=True)
    assert c_s2 == "F", "held scale2(F) preserved under uni (integer-scale NOT lost)"
    _, c_r, _ = identify(OBJ, translate(lin(OBJ["V"], [0, -1, 1, 0]), 3, 2),
                         gen_infer=True, uni=True)
    assert c_r == "V", "held rot90(V) preserved under uni"


# --- the seed-guard veto is FAITHFUL: every generator the DISCOVERY path mints
#     under uni mode is |det|=1 (no re-selection divergence). ---
def test_every_minted_generator_is_unimodular():
    minted = []
    for src, cs in OBJ.items():
        for xf, M in SHEARS.items():
            _, _, dets = identify(OBJ, translate(lin(cs, M), 3, 2), gen_infer=True, uni=True)
            minted.extend(dets)
    assert minted, "shears ARE discovered under uni (det=1 admitted) — sanity"
    assert all(abs(d) == 1 for d in minted), f"a non-unimodular gen was minted: {minted}"


# --- §9: gen_unimodular ABSENT is byte-identical to committed gen_infer ON.
#     A held-out shear still mints a generator; the B1 leak is still present. ---
def test_off_by_default_is_committed_behaviour():
    st, cov, dets = identify(OBJ, translate(lin(OBJ["F"], SHEARS["shearY"]), 3, 2),
                             gen_infer=True, uni=False)
    assert st in ("recognized", "recognized_transformed")
    _, covB1, _ = identify(OBJ, COLLINEAR, gen_infer=True, uni=False)
    assert covB1 is not None, "with uni OFF the committed Regime-B leak is unchanged (§9)"
