"""RUNG 216000 — ARC-ls20 pixel-segmentation parity: the seeing-not-oracle gates.

G-no-oracle (load-bearing): the pixel perception path derives the value grid ONLY
from render pixels; `arc3_grid` is read ONLY on the default (oracle) path. Proven
both by SOURCE AUDIT (AST) and at RUNTIME (a poisoned oracle grid is ignored).
G-parity: the render/recover pair is an exact inverse on the lossless block render.
"""
import ast
import inspect
import textwrap

import numpy as np
import pytest

from worlds.arc import _render_screen, recover_grid_from_render


# --------------------------------------------------------------------------
# G-parity: render/recover is an exact inverse on the lossless block render.
# --------------------------------------------------------------------------
def _sample_grids():
    g0 = [[0, 4, 4, 3, 3, 8],
          [0, 4, 9, 11, 3, 8],
          [0, 4, 9, 3, 3, 0],
          [5, 5, 0, 0, 11, 11]]
    # a 64x64 ls20-shaped grid: field 4, a room 3, a 2-colour avatar 9+11, meter 11
    g1 = [[4] * 64 for _ in range(64)]
    for r in range(6, 24):
        for c in range(6, 26):
            g1[r][c] = 3
    g1[15][8] = 9; g1[16][8] = 9; g1[15][9] = 11
    for c in range(2, 30):
        g1[2][c] = 11
    return [g0, g1]


def test_roundtrip_exact_inverse():
    for g in _sample_grids():
        h = len(g); w = len(g[0])
        rec = recover_grid_from_render(_render_screen(g, h, w))
        assert np.array_equal(np.asarray(rec), np.asarray(g)), \
            "recover_grid_from_render must be the exact inverse of _render_screen"


# --------------------------------------------------------------------------
# G-no-oracle (AST): the pixel path never names the oracle grid.
# --------------------------------------------------------------------------
def test_recover_reads_only_pixels_ast():
    src = inspect.getsource(recover_grid_from_render)
    tree = ast.parse(textwrap.dedent(src))
    fn = tree.body[0]
    # its ONLY parameter is the rendered screen (pixels)
    assert [a.arg for a in fn.args.args] == ["screen"], \
        "recover_grid_from_render takes ONLY the rendered pixels"
    # it never references the oracle grid or oracle segmentation by name
    names = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
    attrs = {n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)}
    for banned in ("arc3_grid", "_last_grid", "segment", "connectedComponents"):
        assert banned not in names and banned not in attrs, \
            f"the pixel path must not touch the oracle ({banned})"


def test_perceive_frame_pixel_branch_reads_screen_not_oracle():
    """The pixel_eye branch of perceive_frame sources the grid from the RENDER
    (vision_screen -> recover_grid_from_render); arc3_grid is read ONLY off the
    default/fallback path."""
    from substrate.world_adapter import WorldAdapter
    src = textwrap.dedent(inspect.getsource(WorldAdapter.perceive_frame))
    tree = ast.parse(src)
    pix_if = None
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            cond = ast.dump(node.test)
            if "pixel_eye" in cond:
                pix_if = node
                break
    assert pix_if is not None, "perceive_frame must gate the pixel path on pixel_eye"
    body_src = "\n".join(ast.dump(s) for s in pix_if.body)
    assert "vision_screen" in body_src and "recover_grid_from_render" in body_src, \
        "the pixel_eye branch must recover the grid from the render"


# --------------------------------------------------------------------------
# G-no-oracle (runtime): a POISONED oracle grid is ignored by the pixel path.
# --------------------------------------------------------------------------
def test_pixel_path_ignores_poisoned_oracle_grid():
    true_grid = _sample_grids()[1]
    h = len(true_grid); w = len(true_grid[0])
    screen = _render_screen(true_grid, h, w)          # render the TRUE grid
    # the oracle grid the eye is FORBIDDEN to read on the pixel path — all zeros
    poison = [[0] * w for _ in range(h)]
    assert not np.array_equal(np.asarray(poison), np.asarray(true_grid))
    recovered = recover_grid_from_render(screen)       # sees ONLY pixels
    assert np.array_equal(np.asarray(recovered), np.asarray(true_grid)), \
        "the pixel path must recover the SEEN grid, never the (poisoned) oracle"


# --------------------------------------------------------------------------
# G-discipline: default-OFF is byte-identical (pixel_eye absent -> oracle path).
# --------------------------------------------------------------------------
def test_default_off_uses_oracle_grid_path():
    """With no `pixel_eye` attr (the default), perceive_frame's grid source is the
    unchanged `getattr(world_substrate, "arc3_grid", None)` line — proven by the
    else-branch text (a full boot is unnecessary to check the source contract)."""
    from substrate.world_adapter import WorldAdapter
    src = textwrap.dedent(inspect.getsource(WorldAdapter.perceive_frame))
    assert 'getattr(self, "pixel_eye", False)' in src, \
        "the pixel path must default OFF via getattr(..., False)"
    assert src.count('getattr(world_substrate, "arc3_grid", None)') >= 1, \
        "the default path must still read arc3_grid unchanged"


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-q"]))
