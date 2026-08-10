"""RUNG 217000 — ARC-ls20 TRANSFORMATION RECOGNITION (LS20_TRANSFORM_PREREG.md).

The RECOGNITION half of ls20's core mechanic ("a symbol must go through
transformations to reach the goal"), built ON 216000's pixel eye. Given a symbol
Region and its goal-form Region SEEN by the pixel eye, the substrate recognises the
transformation via the GENERAL `TransformDecode`/`DimInfer` (the SAME op that serves
Omniglot / the dim_infer instrument / any domain), decoding the Transform
{dim, delta, generator, k}. Verdict = INTEGER-NATIVE EXACT SET EQUALITY (the engine
returns `recognized_transformed` only on an exact reconstruction; a partial residual
MINTS — a comparison that can be false). No Rust, no seed, no new Term: the only new
code is the mechanical eye->shape bridge (`cells_to_signature`/`region_signature`)
and the harness.

Gates: G-recognise (each named family from SEEN shapes), G-refuse (unrelated pairs
rejected), G-general (source-audit clean + the same op outside ls20), plus the
region-node bridge and the exact-equality verdict.
"""
import ast
import inspect
import textwrap

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core
from domains import reflective_faculty as rf
from worlds.arc import cells_to_signature, region_signature, SHAPE_DIM_TYPES
from scripts.arc_ls20_transform_measure import (
    CORPUS, RECOLOUR_MAP, render_and_see, decode_transform, classify_family,
    t_translate, t_recolour, t_rotate, t_reflect, _reposition, _is_chiral,
)


def _term_live() -> bool:
    s, _ = boot_core()
    try:
        s._inner.evaluate({"type": "TransformDecode",
                           "goal": {"type": "Lit", "value": [["a", "b"]]}}, {})
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _term_live():
    pytest.skip("TransformDecode Term not in the installed substrate_rs wheel",
                allow_module_level=True)


def _see_decode(base_cells, goal_cells):
    """render->SEE both (pixel eye)->signatures->general decode."""
    b = cells_to_signature(render_and_see(base_cells))
    g = cells_to_signature(render_and_see(goal_cells))
    return decode_transform(b, g)


# --------------------------------------------------------------------------
# G-recognise — each NAMED family, from PIXEL-EYE-seen shapes.
# --------------------------------------------------------------------------
def test_translate_recognised_from_seen_shapes():
    cells = CORPUS["F_blue"]
    res = _see_decode(_reposition(cells), t_translate(cells, (3, 4)))
    assert res["status"] == "recognized_transformed" and res["covered_by"] == "sym"
    assert classify_family(res) == "translate"
    # the decoded shift is a per-dimension quantum delta on the COORD dims (1,2)
    dims = set(res["transform"]["dims"])
    assert dims <= {1, 2} and res["transform"]["generator"] is None


def test_recolour_recognised_as_categorical_subst():
    cells = CORPUS["F_blue"]
    res = _see_decode(_reposition(cells), t_recolour(cells, RECOLOUR_MAP))
    assert res["status"] == "recognized_transformed" and res["covered_by"] == "sym"
    assert classify_family(res) == "recolour"
    kinds = {t.get("kind") for t in res["transform"]["transforms"]}
    assert "subst" in kinds, "recolour is a categorical substitution on the value dim, not a shift"


def test_rotate_recognised_via_rotation90_generator():
    cells = CORPUS["S_red"]
    assert _is_chiral(cells)
    for k in (1, 2, 3):
        res = _see_decode(_reposition(cells), t_rotate(cells, k))
        assert res["status"] == "recognized_transformed" and res["covered_by"] == "sym"
        assert classify_family(res) == "rotate"
        assert res["transform"]["generator"] == "rotation90"
        assert res["transform"]["k"] == k, f"rot90 k must be recovered (k={k})"


def test_reflect_recognised_via_reflection_generator():
    cells = CORPUS["Y_green"]
    assert _is_chiral(cells)
    for axis in ("c", "r"):
        res = _see_decode(_reposition(cells), t_reflect(cells, axis))
        assert res["status"] == "recognized_transformed" and res["covered_by"] == "sym"
        assert classify_family(res) == "reflect"
        assert res["transform"]["generator"] in ("reflection_r", "reflection_c")


# --------------------------------------------------------------------------
# G-refuse — a genuinely UNRELATED pair is rejected (no spurious Transform).
# --------------------------------------------------------------------------
def test_unrelated_shapes_are_refused_not_transformed():
    a = _reposition(CORPUS["F_blue"])
    b = _reposition(CORPUS["G_magenta"])
    res = _see_decode(a, b)
    assert res["status"] != "recognized_transformed", \
        "unrelated shapes must not be read as a transform of each other"
    assert res["transform"] is None and res["minted_axes"] >= 1, \
        "an unrelated observation MINTS (refusal), it does not mint a Transform"


def test_exact_equality_verdict_a_near_miss_is_refused():
    """The verdict is EXACT set equality: a goal that is the symbol PLUS one extra
    cell (not any single transform of it) is refused, not fuzzily matched."""
    cells = _reposition(CORPUS["L_yellow"])
    near = list(cells) + [(9, 9, 11)]      # one spurious extra cell
    res = _see_decode(cells, near)
    assert res["status"] != "recognized_transformed", \
        "exact-equality: an inexact (extra-cell) goal must not be recognised as a transform"


# --------------------------------------------------------------------------
# The eye->shape BRIDGE reads REAL Region nodes (the pixel eye's output shape).
# --------------------------------------------------------------------------
def _add_region(s, cells_with_val):
    """Build the node shape _perceive_regions emits: one Region per value +
    WorldInstance Cell{row,col} nodes wired cell -within-> region."""
    regions = {}
    for (r, c, v) in cells_with_val:
        if v not in regions:
            regions[v] = s.add_node("Region", {"rvalue": float(v), "count": 0.0})
        cid = s.add_node("WorldInstance", {"world_type": "Cell", "row": r, "col": c,
                                           "value": v})
        s.add_edge_unchecked(cid, "within", regions[v])
    return regions


def test_region_signature_reads_cells_from_region_nodes():
    s, _ = boot_core()
    cells = [(3, 3, 9), (4, 3, 9), (5, 3, 9), (5, 4, 9)]     # an L in blue-9
    regions = _add_region(s, cells)
    sig = region_signature(s, list(regions.values()))
    got = sorted((r, c, v) for _, r, c, v in sig)
    want = sorted((r, c, "v9") for (r, c, _v) in cells)
    assert got == want, "region_signature must read (row,col,colour) back off the Region's within-cells"


def test_region_signature_groups_a_multicolour_avatar():
    """A two-colour avatar shatters into two Regions (216000 residual); passing both
    ids GROUPS them into one shape the decode can transform."""
    s, _ = boot_core()
    cells = [(2, 2, 9), (3, 2, 9), (4, 2, 9), (4, 3, 11), (2, 3, 9)]   # blue + yellow marker
    regions = _add_region(s, cells)
    assert len(regions) == 2, "a two-colour avatar is two monochrome Regions"
    sig = region_signature(s, list(regions.values()))
    assert len(sig) == len(cells), "grouping unions the cell sets of all given Regions"
    colours = {rel[3] for rel in sig}
    assert colours == {"v9", "v11"}, "each cell keeps its own Region's colour sign"


def test_region_signatures_decode_to_the_transform():
    """End to end from Region nodes: build a symbol Region + a ROTATED goal Region,
    extract both via the bridge, and the general decode recognises the rotation."""
    s, _ = boot_core()
    base_cells = [(r, c, 8) for (r, c, _v) in _reposition(CORPUS["S_red"])]
    goal_cells = [(r, c, 8) for (r, c, _v) in t_rotate(CORPUS["S_red"], 1)]
    br = _add_region(s, base_cells)
    gr = _add_region(s, goal_cells)
    base_sig = region_signature(s, list(br.values()))
    goal_sig = region_signature(s, list(gr.values()))
    res = decode_transform(base_sig, goal_sig)
    assert res["status"] == "recognized_transformed"
    assert classify_family(res) == "rotate" and res["transform"]["generator"] == "rotation90"


# --------------------------------------------------------------------------
# G-general — the SAME op outside ls20, and a source audit for an ls20 hack.
# --------------------------------------------------------------------------
def test_same_op_recognises_transforms_outside_ls20():
    """The IDENTICAL decode on a NON-ls20 corpus (F-pentomino, plain string colours,
    no palette, no render) — the op is domain/dimension-arbitrary."""
    F = [(0, 1, "red"), (0, 2, "red"), (1, 0, "red"), (1, 1, "red"), (2, 1, "red")]
    base = cells_to_signature(_reposition(F))
    rot = decode_transform(base, cells_to_signature(t_rotate(F, 1)))
    assert rot["status"] == "recognized_transformed"
    assert rot["transform"]["generator"] == "rotation90"
    refl = decode_transform(base, cells_to_signature(t_reflect(F, "c")))
    assert refl["status"] == "recognized_transformed"
    assert refl["transform"]["generator"] in ("reflection_r", "reflection_c")
    tr = decode_transform(base, cells_to_signature(t_translate(F, (4, 2))))
    assert classify_family(tr) == "translate"


def test_decode_uses_the_general_machinery_no_ls20_hack_ast():
    """Source audit: `decode_transform` recognises via the GENERAL machinery — it
    constructs a ShapeSignature + a decoded Observation + run_rules() (the SAME
    construction as scripts/dim_infer_args.point_S), and it does NOT branch on a
    per-family transform table, does NOT name a specific generator, and does NOT
    hardcode which transform relates the pair. The transform is DISCOVERED by decode."""
    src = textwrap.dedent(inspect.getsource(decode_transform))
    tree = ast.parse(src)
    strings = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant)
               and isinstance(n.value, str)}
    # it must drive the general loop
    for needed in ("ShapeSignature", "Observation"):
        assert needed in strings, f"decode must use the general {needed} construction"
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert "run_rules" not in src or "native.run_rules" in src
    # NO transform is hardcoded / selected by name inside the decode
    for banned in ("rotation90", "reflection_r", "reflection_c", "rotate", "reflect",
                   "recolour", "translate", "ls20"):
        assert banned not in strings, \
            f"the decode must DISCOVER the transform, never name {banned!r} to select it"


def test_cells_to_signature_has_no_ls20_special_casing():
    """The bridge is a mechanical (row,col,colour)->relation translation with no
    transform logic and no ls20 branching."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(cells_to_signature)))
    fn = tree.body[0]
    if (fn.body and isinstance(fn.body[0], ast.Expr)
            and isinstance(fn.body[0].value, ast.Constant)):
        fn.body = fn.body[1:]          # drop the (explanatory) docstring; audit CODE only
    code = ast.unparse(fn)
    for banned in ("rotation90", "reflection", "rotate", "reflect", "TransformDecode",
                   "DimInfer", "ls20", "arc3"):
        assert banned not in code, f"the signature bridge CODE must not mention {banned!r}"


def test_dim_types_are_the_general_ones():
    """The signature's dim_types are the general instrument's (pred/coord:r/coord:c/
    val), NOT an ls20-specific schema."""
    assert SHAPE_DIM_TYPES == ["pred", "coord:r", "coord:c", "val"]


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
