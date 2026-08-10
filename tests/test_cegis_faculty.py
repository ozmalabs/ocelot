"""test_cegis_faculty — the descriptor-grounding + CEGIS faculty invents BOTH
`dimension` (the maxface/cell form) AND the GENERAL `euler` (c0−c1+c2−c3+c4),
including the solid tetra giving χ=1.

The faculty (domains/cegis_faculty.py) is the permanent home of the loop proved in
scripts/jabberwock_closes_the_euler_tie.py and
scripts/jabberwock_lifts_the_euler_descriptor_ceiling.py. These tests drive the
faculty's two parts as-is:

  · the GENERAL CEGIS core (cegis_synthesize) — domain-agnostic over
    (descriptors, oracle, input-family);
  · the descriptor-grounding helper (ground_cell_count_descriptors) + the grounded
    χ oracle (ground_euler_oracle) — the simplicial-complex instance.

Both reuse native G+Γ (synthesize), Term.evaluate, compute_grounding, and the
grounded oracle. No Rust, no build, no _native beyond _native.Substrate().
"""

from __future__ import annotations

import itertools

import pytest

pytest.importorskip("substrate_rs")
from substrate_rs import _native

from domains import reason as _reason
from domains import compute_grounding as _cg
from domains.cegis_faculty import (
    cegis_synthesize,
    ground_cell_count,
    ground_euler_oracle,
    ground_cell_count_descriptors,
    closure,
    maxdim,
)


# ---------------------------------------------------------------------------
# Shared simplicial-complex world (maximal faces). Standard constructions; no χ
# or dimension encoded — just "more than a single simplex" so the descriptors come
# apart. Spans dim ≤ 4 so the general χ (needing the c3/c4 terms) is forced.
# ---------------------------------------------------------------------------

def _family_complexes():
    fam = []
    for k in (1, 2, 3):                      # disjoint copies of a k-simplex
        base = list(range(k + 1))
        for copies in (2, 3):
            faces, off = [], 0
            for _ in range(copies):
                faces.append([off + i for i in base])
                off += k + 1
            fam.append((f"{copies}x{k}-simplex", faces))
    fam.append(("hollow-triangle", [[0, 1], [1, 2], [0, 2]]))           # S^1, χ=0
    fam.append(("square-loop", [[0, 1], [1, 2], [2, 3], [3, 0]]))       # S^1, χ=0
    fam.append(("filled-square", [[0, 1, 2], [0, 2, 3]]))               # disk, χ=1
    fam.append(("two-tri-share-edge", [[0, 1, 2], [1, 2, 3]]))          # disk, χ=1
    fam.append(("hollow-tetra-S2",
                [list(c) for c in itertools.combinations(range(4), 3)]))  # S^2, χ=2
    fam.append(("two-edges-share-v", [[0, 1], [1, 2]]))                 # path, χ=1
    fam.append(("path-graph7", [[i, i + 1] for i in range(7)]))         # tree, χ=1
    fam.append(("star5", [[0, i] for i in range(1, 6)]))                # tree, χ=1
    fam.append(("triangle-with-tail", [[0, 1, 2], [2, 3]]))             # χ=1
    fam.append(("solid-tetra", [[0, 1, 2, 3]]))                         # B^3, χ=1
    fam.append(("two-solid-tetra-disjoint", [[0, 1, 2, 3], [4, 5, 6, 7]]))  # χ=2
    fam.append(("two-solid-tetra-share-face", [[0, 1, 2, 3], [1, 2, 3, 4]]))  # χ=1
    fam.append(("solid-4simplex", [[0, 1, 2, 3, 4]]))                   # B^4, χ=1
    fam.append(("hollow-4simplex-S3",
                [list(c) for c in itertools.combinations(range(5), 4)]))  # S^3, χ=0
    return fam


KNOWNS = [
    ("point",          [[0]]),
    ("edge",           [[0, 1]]),
    ("triangle",       [[0, 1, 2]]),
    ("tetra-solid",    [[0, 1, 2, 3]]),
    ("4simplex-solid", [[0, 1, 2, 3, 4]]),
]

ARITHMETIC_OPS = ("Plus", "Times", "Minus", "Div", "Min", "Max", "Abs", "Neg")


# ---------------------------------------------------------------------------
# Part 2 grounded pieces.
# ---------------------------------------------------------------------------

def _ground_dimension_oracle(substrate):
    """The agent's own slow `dimension` (max simplex_dim over the maximal faces),
    grounded from its held simplex_dim primitive. The maxface/cell oracle."""
    caps = dict(_reason.CAPABILITIES)
    res = _cg.ground_computation(
        substrate, "simplex_dimension",
        "simplex_dimension(face) = simplex_dim(face)", capabilities=caps)
    assert res.get("grounded") and res.get("installed"), res.get("reason")
    fn = caps["simplex_dimension"]

    def dimension(maximal_faces):
        return int(max(fn({"face": list(mf)}) for mf in maximal_faces))

    return dimension


def _maxface_describe(maximal_faces):
    """The maxface descriptor a world adapter reads off a complex: #verts in the
    largest maximal face. The DSL Var leaf the dimension recipe (maxface − 1) reads.
    A mechanical measurement, NOT the answer (dimension = maxface − 1 must be
    invented)."""
    return {"maxface": max((len(mf) for mf in maximal_faces), default=0)}


# ===========================================================================
# THE TESTS.
# ===========================================================================

def test_cegis_invents_dimension():
    """CEGIS over a maxface descriptor + a grounded `dimension` oracle invents the
    maxface form: dimension = maxface − 1."""
    s = _native.Substrate()
    dim_oracle = _ground_dimension_oracle(s)

    def family():
        return _family_complexes()

    res = cegis_synthesize(
        s, _maxface_describe, dim_oracle, family, KNOWNS,
        ops=ARITHMETIC_OPS, max_size=5, timeout_s=120.0, max_rounds=12,
    )

    assert res.fits, "CEGIS failed to synthesize a fitting `dimension` recipe"
    # The maxface form: dimension = maxface − 1 (MDL-equivalent rendering as
    # `maxface + -1` via the −1 const is the same recipe).
    assert res.final_term_str in ("(maxface - 1)", "(maxface + -1)"), res.final_term_str
    # Agrees with the slow oracle on a held-out battery (never in spec).
    HELD = [
        ("hexagon-loop", [[i, (i + 1) % 6] for i in range(6)]),  # dim 1
        ("wedge-2-tri", [[0, 1, 2], [2, 3, 4]]),                 # dim 2
        ("solid-5simplex", [[0, 1, 2, 3, 4, 5]]),                # dim 5
    ]
    for nm, mf in HELD:
        got = res.evaluate(_maxface_describe, mf, s)
        assert abs(got - dim_oracle(mf)) < 1e-9, f"{nm}: dim recipe {got} != {dim_oracle(mf)}"


def test_cegis_invents_general_euler():
    """CEGIS over the self-grounded cell_count descriptors + the grounded χ oracle
    invents the GENERAL Euler characteristic (uses the c3 term; solid tetra → χ=1)."""
    s = _native.Substrate()

    all_complexes = ([mf for _, mf in KNOWNS]
                     + [mf for _, mf in _family_complexes()])
    describe, names = ground_cell_count_descriptors(s, all_complexes)
    chi_oracle = ground_euler_oracle(s)

    # The descriptor family ran k=0..maxdim and surfaced the 3-cell count c3 the
    # {V,E,F} set was missing.
    assert "c3" in names, names

    def family():
        return _family_complexes()

    res = cegis_synthesize(
        s, describe, chi_oracle, family, KNOWNS,
        ops=ARITHMETIC_OPS, max_size=9, timeout_s=240.0, max_rounds=16,
    )

    assert res.fits and res.converged, (res.fits, res.converged, res.final_term_str)
    # The lifted ceiling: the recipe USES the 3-cell descriptor (a pure-{V,E,F}
    # recipe physically cannot reach χ on the solid tetra).
    assert res.uses("c3"), f"recipe does not use c3: {res.final_term_str}"

    # The solid tetra: the {V,E,F} ceiling gave 2; the general χ gives 1.
    solid = [[0, 1, 2, 3]]
    assert abs(res.evaluate(describe, solid, s) - 1.0) < 1e-9, res.final_term_str

    # Agrees with the slow χ oracle on a held-out battery spanning dim ≤ 5.
    HELD = [
        ("4x2-simplex", [[3 * i, 3 * i + 1, 3 * i + 2] for i in range(4)]),  # χ=4
        ("pentagon-loop", [[i, (i + 1) % 5] for i in range(5)]),            # χ=0
        ("wedge-2-tri", [[0, 1, 2], [2, 3, 4]]),                            # χ=1
        ("three-solid-tetra",
         [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]]),                     # χ=3
        ("solid-4simplex", [[0, 1, 2, 3, 4]]),                              # χ=1
        ("two-4simplex-share-tetra", [[0, 1, 2, 3, 4], [1, 2, 3, 4, 5]]),   # χ=1
    ]
    for nm, mf in HELD:
        got = res.evaluate(describe, mf, s)
        assert abs(got - chi_oracle(mf)) < 1e-9, f"{nm}: χ recipe {got} != {chi_oracle(mf)}"


def test_cell_count_descriptors_are_grounded():
    """The cell_count family is grounded from held primitives (not hand-listed):
    {V,E,F} = k=0,1,2, and the solid tetra's c3 = 1 falls out of the same family."""
    s = _native.Substrate()
    cell_count = ground_cell_count(s)
    solid = [[0, 1, 2, 3]]
    assert [cell_count(solid, k) for k in range(4)] == [4, 6, 4, 1]
    # The closure/maxdim helpers are the shared structure.
    assert maxdim(solid) == 3
    assert len(closure(solid)) == 15        # 4 + 6 + 4 + 1 faces
