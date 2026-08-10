"""Block 211000 — a SEEN geometry channel for the door/switch eye (attacks the 209000 null).

209000's geometry channel (SEEN depth-from-motion) was CHANCE on real frames (AUC 0.508). This
block ships `col_structural_level` — a SEEN STRUCTURAL horizontal-edge feature (the orthogonal
twin of the vertical-gradient texture channel), an occluding-contour detector for a door's
framed/recessed geometry. Real-E1M1 AUC numbers live in scripts/robust_geometry_measure.py +
results/pattern_eye/robust_geometry.json (AUC ~0.69 shipped / ~0.73 continuous vs a depth-EDGE
oracle over ~169k columns). These tests gate the mechanism: integer-native, no-oracle source
audit, the feature FIRES on a synthetic vertical edge and STAYS 0 on a flat/uniform surface,
default-OFF byte-identity, and the geometry-only recognition at MATCHED texture that 209000
could not do.
"""
import json
import os

import numpy as np

import domains.doom_pattern_eye as eye

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = os.path.join(ROOT, "seeds", "pattern_recognition.json")


def _fresh():
    from substrate.world_adapter import WorldAdapter
    wa = WorldAdapter(seeds=())
    wa.inner.load_seed_manifest(json.load(open(SEED)), None)
    return wa


def _scene(regions, *, enable=True, floor=2):
    wa = _fresh(); S, I = wa.s, wa.inner
    game = S.add_node("WorldInstance", {"world_type": "Game", "map_mode": "doom"})
    if enable:
        p = S.add_node("PatternParams", {"enabled": 1.0, "salience_floor": int(floor)})
        I.add_edge_unchecked(game, "has_pattern_params", p)
        I.add_edge_unchecked(game, "has_pattern_library", list(I.nodes("PatternLibrary"))[0])
    rids = {}
    for name, (g, t, near) in regions.items():
        r = S.add_node("PerceivedRegion", {"geom_level": int(g), "tex_level": int(t), "near": float(near)})
        I.add_edge_unchecked(game, "has_perceived_region", r); rids[name] = r
    I.run_rules(50000)
    return {name: dict(S.node(r)["attrs"]) for name, r in rids.items()}


# ---------------------------------------------------------------- the SEEN feature (pixels only)
def test_geometry_level_is_integer():
    frame = np.zeros((240, 320, 3), np.uint8)
    frame[:, 160:] = 200                                  # one vertical luma step
    lvl, energy = eye.col_structural_level(frame)
    assert lvl.dtype == np.int64 and energy.dtype == np.int64
    assert all(isinstance(int(v), int) for v in lvl)


def test_flat_surface_reads_zero_geometry():
    # a uniform wall (no structural edge) -> geometry level 0 everywhere (clean floor for recognition)
    flat = np.full((240, 320, 3), 90, np.uint8)
    lvl, _ = eye.col_structural_level(flat)
    assert int(lvl.max()) == 0


def test_vertical_structural_edge_fires_geometry():
    # a single strong VERTICAL edge (an occluding-contour / door-frame proxy) -> high geometry AT
    # the edge column, ~0 away from it. Ambient-median subtraction leaves only the local edge.
    frame = np.full((240, 320, 3), 60, np.uint8)
    frame[:, 160:] = 210                                  # vertical luma step at column 160
    lvl, _ = eye.col_structural_level(frame)
    assert int(lvl[160]) >= 4                             # structural edge saturates high
    assert int(np.median(lvl)) == 0                       # everywhere else flat -> 0


def test_texture_is_not_geometry_orthogonal_directions():
    # a HORIZONTALLY-striped surface (vertical alternation) is pure TEXTURE (vertical gradient),
    # NOT a vertical structural edge -> texture high, geometry ~0 (the channels are orthogonal).
    stripes = np.zeros((240, 320, 3), np.uint8)
    stripes[::2] = 200                                    # alternate ROWS -> vertical gradient only
    tex, _ = eye.col_texture_level(stripes)
    geo, _ = eye.col_structural_level(stripes)
    assert int(np.median(tex)) >= 4                       # strong texture
    assert int(geo.max()) == 0                            # no horizontal structural edge


def test_no_oracle_source_audit_geometry_eye():
    # G-no-oracle: the geometry eye reads ONLY rendered pixels (integer luma) — never the depth /
    # labels / sectors buffers or a texture NAME.
    import inspect, ast
    funcs = (eye._luma_int, eye.col_structural_level, eye.col_geometry_level, eye.region_descriptor)
    src = "\n".join(inspect.getsource(f) for f in funcs)
    tree = ast.parse(src)
    bad_attrs = {"depth_buffer", "labels_buffer", "labels", "sectors"}
    bad_subs = {"depth", "label", "texture", "linedef", "sectors"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr not in bad_attrs, f"geometry eye accesses .{node.attr}"
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
            assert node.slice.value not in bad_subs, f"geometry eye indexes [{node.slice.value!r}]"


def test_region_descriptor_single_frame_no_motion():
    # geometry now needs NO motion — region_descriptor works on ONE rgb frame (a strict improvement
    # over 209000, which returned 0 unless the previous action was forward).
    frame = np.full((240, 320, 3), 60, np.uint8)
    frame[:, 200:] = 200
    geo, tex, meta = eye.region_descriptor(frame)         # no frames/fi passed
    assert int(geo[200]) >= 1 and "geo_ambient" in meta


# ---------------------------------------------------------------- G-both-channels (recognition)
def test_geometry_only_difference_shifts_recognition_matched_texture():
    # THE THING 209000 COULD NOT DO: at IDENTICAL texture, a geometry difference changes recognition.
    # framed door (geom high) vs flush switch (geom 0), both marked (tex 6). With a REAL geometry
    # channel the door resolves to `door`, the flush surface to `switch` — geometry disambiguates.
    out = _scene({"framed": (4, 6, 1), "flush": (0, 6, 1)})
    assert out["framed"].get("recognised_as") == "door"
    assert out["flush"].get("recognised_as") != "door"     # geometry, not texture, separates them


def test_geometry_only_region_is_salient():
    # a geometry-only region (structural edge, NO texture marking) is still salient — the channel
    # contributes on its own (a bare recess/frame is a "different kind of thing").
    out = _scene({"geom_only": (5, 0, 1), "plain": (0, 0, 1)})
    assert out["geom_only"].get("salient") == 1.0
    assert out["plain"].get("salient") in (0.0, None)


def test_default_off_is_byte_identical():
    # no PatternParams -> the geometry channel is inert; regions carry no salience/recognition attrs.
    out = _scene({"framed": (4, 6, 1), "plain": (0, 0, 1)}, enable=False)
    for a in out.values():
        assert "salient" not in a and "recognised_as" not in a and "recognised_family" not in a
