"""Block 209000 — GENERIC integer pattern-recognition eye (door/switch are library data).

Gates the graph-native mechanism: novelty-salience, nearest-prototype recognition (coarse
family FAR / fine members NEAR), affordance-driven investigation, the concept-scramble
control, the false-positive control, integer-native descriptors, default-OFF byte-identity,
and the no-oracle source audit of the eye. Doom pixels are not needed for these (the eye's
graph hand-off is exercised with synthetic integer descriptors); the real-E1M1 numbers live
in scripts/doom_pattern_eye_run.py + results/pattern_eye/gates.json.
"""
import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = os.path.join(ROOT, "seeds", "pattern_recognition.json")


def _fresh():
    from substrate.world_adapter import WorldAdapter
    wa = WorldAdapter(seeds=())
    wa.inner.load_seed_manifest(json.load(open(SEED)), None)
    return wa


def _scene(regions, *, enable=True, floor=2, scramble=None):
    """regions: {name: (geom_level, tex_level, near)}. Returns per-region readout + investigations."""
    wa = _fresh(); S, I = wa.s, wa.inner
    game = S.add_node("WorldInstance", {"world_type": "Game", "map_mode": "doom"})
    if enable:
        p = S.add_node("PatternParams", {"enabled": 1.0, "salience_floor": int(floor)})
        I.add_edge_unchecked(game, "has_pattern_params", p)
        I.add_edge_unchecked(game, "has_pattern_library", list(I.nodes("PatternLibrary"))[0])
    if scramble:
        for c in I.nodes("PatternPrototype"):
            if S.node(c)["attrs"].get("name") == scramble:
                S.set_attr(c, "geom_sig", 0); S.set_attr(c, "tex_sig", 0)
    rids = {}
    for name, (g, t, near) in regions.items():
        r = S.add_node("PerceivedRegion", {"geom_level": int(g), "tex_level": int(t), "near": float(near)})
        I.add_edge_unchecked(game, "has_perceived_region", r); rids[name] = r
    I.run_rules(50000)
    out = {name: dict(S.node(r)["attrs"]) for name, r in rids.items()}
    invs = [dict(S.node(i)["attrs"]) for i in I.nodes("Investigation")]
    return out, invs


def test_seed_loads_with_held_prototypes():
    wa = _fresh()
    names = {wa.s.node(c)["attrs"]["name"] for c in wa.inner.nodes("PatternPrototype")}
    assert {"background", "operable_feature", "door", "switch"} <= names


def test_generic_recognition_of_held_patterns():
    out, _ = _scene({"door": (4, 6, 1), "switch": (0, 7, 1), "plain": (0, 0, 1)})
    assert out["door"].get("recognised_as") == "door"
    assert out["switch"].get("recognised_as") == "switch"
    assert out["plain"].get("recognised_as") is None


def test_false_positive_control_plain_not_salient():
    out, _ = _scene({"plain": (0, 0, 1), "faint": (0, 1, 1), "distinct": (0, 6, 1)})
    assert out["plain"].get("salient") in (0.0, None)
    assert out["faint"].get("salient") in (0.0, None)        # below floor
    assert out["distinct"].get("salient") == 1.0


def test_coarse_far_fine_near():
    # FAR (near=0): only the coarse family; NEAR (near=1): the fine prototype resolves.
    out, _ = _scene({"far": (4, 6, 0), "near": (4, 6, 1)})
    assert out["far"].get("recognised_family") == "operable_feature"
    assert out["far"].get("recognised_as") is None           # not named far
    assert out["near"].get("recognised_as") == "door"        # named up close


def test_concept_scramble_breaks_fine_keeps_coarse():
    base, _ = _scene({"door": (4, 6, 1)})
    assert base["door"].get("recognised_as") == "door"
    scr, _ = _scene({"door": (4, 6, 1)}, scramble="door")
    assert scr["door"].get("recognised_as") is None          # held pattern corrupted -> no fine match
    assert scr["door"].get("recognised_family") == "operable_feature"   # coarse detection robust


def test_investigation_minted_from_affordance():
    _, invs = _scene({"switch": (0, 7, 1)})
    kinds = {(i.get("kind"), i.get("target_concept")) for i in invs}
    assert ("approach_to_resolve", "operable_feature") in kinds
    assert ("operate", "switch") in kinds


def test_default_off_is_byte_identical():
    # No PatternParams -> no rule fires; regions carry no salience/recognition attrs.
    out, invs = _scene({"door": (4, 6, 1), "plain": (0, 0, 1)}, enable=False)
    assert invs == []
    for a in out.values():
        assert "salient" not in a and "recognised_as" not in a and "recognised_family" not in a


def test_descriptors_and_salience_are_integer():
    out, _ = _scene({"door": (4, 6, 1)})
    a = out["door"]
    assert isinstance(a["geom_level"], int) and isinstance(a["tex_level"], int)
    assert isinstance(a["salience"], int)                    # L1 of integers is integer


def test_eye_reads_only_rendered_pixels_source_audit():
    import inspect, ast
    import domains.doom_pattern_eye as eye
    src = "\n".join(inspect.getsource(f) for f in (eye._luma_int, eye.col_texture_level))
    tree = ast.parse(src)
    bad_attrs = {"depth_buffer", "labels_buffer", "labels", "sectors"}
    bad_subs = {"depth", "label", "texture", "linedef"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr not in bad_attrs
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
            assert node.slice.value not in bad_subs


def test_integer_texture_level_from_synthetic_pixels():
    # A flat (uniform) surface -> texture level 0; a high-contrast striped surface -> high.
    import numpy as np
    import domains.doom_pattern_eye as eye
    flat = np.full((240, 320, 3), 90, np.uint8)
    lvl_flat, _ = eye.col_texture_level(flat)
    assert int(lvl_flat.max()) == 0
    stripes = np.zeros((240, 320, 3), np.uint8)
    stripes[::2] = 200                                        # strong vertical alternation
    lvl_str, _ = eye.col_texture_level(stripes)
    assert int(np.median(lvl_str)) >= 4
