"""SIMILARITY-SUBGROUP restriction on GenInfer — gate.

Pre-registered in `VISION_SIMILARITY_PREREG.md`, measured in
`scripts/similarity_measure.py` -> `results/similarity.json`. The seed guard
restricts discovered generators to the SIMILARITY subgroup (scaled-orthogonal
maps, M*M^T = lambda*I) as GRAPH DATA — three conditions on GenInfer's `matrix`
via Nth/Times/Plus/Minus/Eq Terms: ORTHOGONAL columns, EQUAL squared length,
NON-DEGENERATE det — gated on a NEW flag `gen_similarity`, OFF by default (§9).

OUTCOME 1 (FULL CROSSING on the crux): the shears (det=1, ortho=1) that
`|det|=1` admitted are now REFUSED at discovery, so a sheared pentomino no longer
aliases onto another identity and discrimination is EXACT-0 — the discovery path
matches Regime A. One reported residual (the identifiability limit): shearX(F) is
pixel-identical to refl_c(F), so it is recognized as F (its OWN identity) via the
HELD path — an alias, not a guard leak; discrimination stays exact-0.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from scripts.similarity_measure import (
    OBJ, COLLINEAR, DET0, SCALE3, SHEARS, identify, lin, translate, det,
    is_similarity, norm,
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


# --- the similarity CONDITION, verified by construction (§12.4): admits the
#     identity-preserving transforms, excludes the identity-changing ones. ---
def test_similarity_condition_by_construction():
    for M in ([0, -1, 1, 0], [-1, 0, 0, -1], [0, 1, -1, 0], [-1, 0, 0, 1],
              [1, 0, 0, -1], [1, 0, 0, 1], [2, 0, 0, 2], [3, 0, 0, 3]):
        assert is_similarity(M), f"{M} is an identity-preserving similarity"
    assert not is_similarity([1, 1, 0, 1]), "shearX excluded (orthogonality)"
    assert not is_similarity([1, 0, 1, 1]), "shearY excluded (orthogonality)"
    assert not is_similarity([1, 0, 1, 0]), "det=0 collapse excluded (equal-length)"
    assert not is_similarity([1, 1, 0, 0]), "det=0 excluded"
    assert not is_similarity([0, 0, 0, 0]), "zero/empty matrix excluded (non-degenerate)"


# --- THE CRUX (OUTCOME 1): the shears |det|=1 ADMITTED are now REFUSED at
#     discovery — shearY(F) no longer aliases onto X. ---
def test_shears_refused_no_longer_alias_onto_another_identity():
    # shearY(F) aliased onto X under |det|=1; under similarity it is REFUSED (NEW).
    _, covY, _ = identify(OBJ, translate(lin(OBJ["F"], SHEARS["shearY"]), 3, 2),
                          gen_infer=True, sim=True)
    assert covY != "X", "shearY(F) must NOT alias onto X under the similarity restriction"
    assert covY is None, "shearY(F) is a non-similarity shear -> REFUSED (NEW)"
    # shearX(T) aliased onto X under |det|=1; under similarity it is REFUSED.
    _, covX, _ = identify(OBJ, translate(lin(OBJ["T"], SHEARS["shearX"]), 3, 2),
                          gen_infer=True, sim=True)
    assert covX != "X", "shearX(T) must NOT alias onto X under the similarity restriction"
    assert covX is None, "shearX(T) is a non-similarity shear -> REFUSED (NEW)"


# --- and it is a REAL fix: WITHOUT the restriction the shears aliased. ---
def test_shears_aliased_without_the_restriction():
    _, covY, _ = identify(OBJ, translate(lin(OBJ["F"], SHEARS["shearY"]), 3, 2),
                          gen_infer=True, sim=False)
    assert covY == "X", "control: without the similarity restriction shearY(F) aliases onto X"


# --- DISCRIMINATION EXACT-0: B1 refused AND no shear aliases onto a DIFFERENT
#     identity (shear_wrong_id == 0). This is what |det|=1 could not achieve. ---
def test_discrimination_exact0_no_identity_change():
    # B1 collinear leak refused (det=0 excluded by equal-length).
    _, covB1, _ = identify(OBJ, COLLINEAR, gen_infer=True, sim=True)
    assert covB1 is None, "collinear I must be REFUSED (det=0 excluded)"
    # no shear view is recognized as a DIFFERENT object (wrong_id == 0).
    for src, cs in OBJ.items():
        for xf, M in SHEARS.items():
            _, cov, _ = identify(OBJ, translate(lin(cs, M), 3, 2), gen_infer=True, sim=True)
            assert cov in (None, src), (
                f"{xf}({src}) recognized as {cov} != {src}: a shear changed identity "
                "(discrimination not exact-0)")


# --- the one RESIDUAL is a held-path ALIAS, not a guard leak: shearX(F) is
#     pixel-identical to refl_c(F), so it is recognized as F (its OWN identity)
#     via the held generator BEFORE GenInfer — the identifiability limit. ---
def test_the_single_recognized_shear_is_a_held_alias_to_its_own_identity():
    shearXF = norm(lin(OBJ["F"], SHEARS["shearX"]))
    reflcF = norm(lin(OBJ["F"], [1, 0, 0, -1]))
    assert shearXF == reflcF, "shearX(F) is pixel-identical to refl_c(F) (the alias)"
    _, cov, mats = identify(OBJ, translate(lin(OBJ["F"], SHEARS["shearX"]), 3, 2),
                            gen_infer=True, sim=True)
    assert cov == "F", "shearX(F) recognized as its OWN identity F (a held-similarity alias)"
    assert not mats, "recognized via the HELD path — NO linear generator minted"


# --- FLOOR: det=0 singular map, non-rigid warp, and noise are refused. ---
def test_floors_refused_under_similarity():
    for src, cs in OBJ.items():
        _, c0, _ = identify(OBJ, translate(lin(cs, DET0), 3, 2), gen_infer=True, sim=True)
        assert c0 is None, f"det=0 map on {src} must be refused (not a similarity)"
        nn = norm(cs)[:]
        r, c = nn[-1]; nn[-1] = (r + 2, c + 2)
        _, cw, _ = identify(OBJ, nn, gen_infer=True, sim=True)
        assert cw is None, f"non-rigid warp on {src} must be refused"


# --- THE CONTRAST WITH |det|=1: uniform integer scale IS a similarity, so the
#     DISCOVERY path ADMITS scale3 (det=9) — where |det|=1 wrongly refused it.
#     Held similarity (scale2/rot90) preserved via the held path either way. ---
def test_scale3_admitted_and_held_similarity_preserved():
    # scale3 (det=9) is a similarity -> recognized as its own identity (discovery).
    for src, cs in OBJ.items():
        _, cov, _ = identify(OBJ, translate(lin(cs, SCALE3), 3, 2), gen_infer=True, sim=True)
        assert cov == src, (
            f"scale3({src}) is a uniform-scale similarity -> recognized as {src} "
            "(|det|=1 wrongly refused this)")
    # held scale2/rot90 route via DimInfer before GenInfer -> preserved.
    _, c_s2, _ = identify(OBJ, translate(lin(OBJ["F"], [2, 0, 0, 2]), 3, 2), gen_infer=True, sim=True)
    assert c_s2 == "F", "held scale2(F) preserved under sim mode"
    _, c_r, _ = identify(OBJ, translate(lin(OBJ["V"], [0, -1, 1, 0]), 3, 2), gen_infer=True, sim=True)
    assert c_r == "V", "held rot90(V) preserved under sim mode"


# --- INVARIANCE: the held discrete-similarity grid is 49/49 (untouched — the
#     restriction only affects the discovery rung, below the held path). ---
def test_held_invariance_49_of_49():
    ok = 0
    for src, cs in OBJ.items():
        for xf, M in {"identity": [1, 0, 0, 1], "rot90": [0, -1, 1, 0],
                      "rot180": [-1, 0, 0, -1], "rot270": [0, 1, -1, 0],
                      "refl_r": [-1, 0, 0, 1], "refl_c": [1, 0, 0, -1],
                      "scale2": [2, 0, 0, 2]}.items():
            _, cov, _ = identify(OBJ, translate(lin(cs, M), 3, 2), gen_infer=True, sim=True)
            if cov == src:
                ok += 1
    assert ok == 49, f"held similarity invariance must be 49/49, got {ok}"


# --- the seed-guard veto is FAITHFUL: every generator the DISCOVERY path mints
#     under sim mode is a similarity (no non-similarity minted). ---
def test_every_minted_generator_is_a_similarity():
    minted = []
    for src, cs in OBJ.items():
        for xf, M in {**{"rot90": [0, -1, 1, 0], "scale2": [2, 0, 0, 2],
                         "scale3": SCALE3}, **SHEARS}.items():
            _, _, mats = identify(OBJ, translate(lin(cs, M), 3, 2), gen_infer=True, sim=True)
            minted.extend(mats)
    assert all(is_similarity(m) for m in minted), (
        f"a non-similarity generator was minted: {[m for m in minted if not is_similarity(m)]}")


# --- §9: gen_similarity ABSENT is byte-identical to committed gen_infer / |det|=1
#     behaviour. A held-out shear still aliases onto X; B1 still leaks. ---
def test_off_by_default_is_committed_behaviour():
    st, cov, _ = identify(OBJ, translate(lin(OBJ["F"], SHEARS["shearY"]), 3, 2),
                          gen_infer=True, sim=False)
    assert st in ("recognized", "recognized_transformed") and cov == "X", (
        "with sim OFF the committed Regime-B shear alias is unchanged (§9)")
    _, covB1, _ = identify(OBJ, COLLINEAR, gen_infer=True, sim=False)
    assert covB1 is not None, "with sim OFF the committed det=0 leak is unchanged (§9)"
