"""Block 214000 — GENUINE texture recognition (pattern + colour-as-sign).

Gates the graph-native mechanism that replaces the 209000 edge-density SCALAR with a richer
INTEGER texture descriptor: COLOUR-as-a-sign (chroma contrast from the ambient wall) and
PATTERN-as-arrangement (horizontal-gradient share = vertical image contours). The real-E1M1
numbers (faint-door door-vs-wall AUC 0.94 vs the scalar's 0.69; graph faint recovery 0.60 vs
0.10 at wall-FP 0.13 vs 0.30) live in scripts/texture_signature_measure.py +
results/pattern_eye/texture_signature.json + TEXTURE_RECOGNITION_RESULTS.md. Here we gate the
descriptor + held-concept match on synthetic integer pixels (no VizDoom needed):

- faint door recovered by ARRANGEMENT; a busy wall (high energy, wall arrangement) rejected
  (the 209000 false-positive the scalar makes on energy alone);
- COLOUR recognises a region differing from its wall ONLY in colour, INVISIBLE to the luma scalar;
- PATTERN carries signal beyond energy (equal total energy, different arrangement -> different level);
- integer-native descriptors; default-OFF byte-identity; the no-oracle source audit of the eye.
"""
import ast
import inspect
import json
import os

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = os.path.join(ROOT, "seeds", "pattern_texture_signature.json")


def _fresh():
    from substrate.world_adapter import WorldAdapter
    wa = WorldAdapter(seeds=())
    wa.inner.load_seed_manifest(json.load(open(SEED)), None)
    return wa


def _scene(regions, *, enable=True, floor=2):
    """regions: {name: (tex_level, colour_level, pattern_level)}. Returns per-region readout."""
    import domains.doom_pattern_eye as eye
    wa = _fresh(); S, I = wa.s, wa.inner
    game = S.add_node("WorldInstance", {"world_type": "Game", "map_mode": "doom"})
    if enable:
        eye.install_texture(wa, game, salience_floor=floor)
    rids = {}
    for name, (t, c, p) in regions.items():
        rids[name] = eye.ingest_texture_region(wa, game, t, c, p)
    out = eye.recognise_texture(wa, list(rids.values()))
    return {name: out[r] for name, r in rids.items()}


# --------------------------------------------------------------------------- seed + graph gates
def test_seed_loads_with_richer_prototypes():
    wa = _fresh()
    protos = {wa.s.node(c)["attrs"]["name"]: wa.s.node(c)["attrs"] for c in wa.inner.nodes("TexturePrototype")}
    assert {"background", "door"} <= set(protos)
    d = protos["door"]
    assert "pattern_sig" in d and "colour_sig" in d and "tex_sig" in d      # a RICHER signature


def test_faint_door_recovered_by_arrangement():
    # The 209000 residual: a texture-FAINT door reads low ENERGY (tex 2) yet has a door-like
    # ARRANGEMENT (pattern 7). The energy scalar misses it; the arrangement match recovers it.
    out = _scene({"faint_door": (2, 0, 7), "plain_wall": (0, 0, 3), "busy_wall": (8, 0, 3)})
    assert out["faint_door"]["recognised_as"] == "door"
    assert out["faint_door"]["recog_via"] == "arrangement"
    assert out["plain_wall"]["recognised_as"] is None                        # not salient
    # the busy wall is the 209000 FALSE POSITIVE (high energy) — the arrangement REJECTS it:
    assert out["busy_wall"]["recognised_as"] is None


def test_colour_only_door_recognised_and_independent_of_luma():
    # A region matching the wall in luma-gradient (tex 0) and arrangement (pattern 3), differing
    # ONLY in COLOUR (colour 6): the luma-only scalar is blind to it; the colour sign recognises it.
    out = _scene({"colour_door": (0, 6, 3), "grey_wall": (0, 0, 3)})
    assert out["colour_door"]["recognised_as"] == "door"
    assert out["colour_door"]["recog_via"] == "colour"                       # the INDEPENDENT sign
    assert out["grey_wall"]["recognised_as"] is None


def test_default_off_is_byte_identical():
    out = _scene({"door": (2, 0, 7), "wall": (0, 0, 3)}, enable=False)
    for a in out.values():
        assert a["recognised_as"] is None and a["tex_salient"] is None       # no rule fired


def test_descriptor_levels_and_salience_are_integer():
    out = _scene({"door": (2, 0, 7)})
    assert out["door"]["recognised_as"] == "door"
    assert isinstance(out["door"]["tex_salience"], int)                      # L1 of integers is integer


# ------------------------------------------------------- descriptor gates (synthetic real pixels)
def _luma_grating(period, amp, axis, base=20):
    """A synthetic RGB frame with a square-wave luma grating (integer). axis=0 -> HORIZONTAL
    contours (luma varies down rows); axis=1 -> VERTICAL contours (varies across columns).
    Both gratings share amplitude+period -> equal total |Δluma| energy, only orientation differs."""
    idx = (np.arange(240)[:, None] if axis == 0 else np.arange(320)[None, :])
    patt = np.where((idx // period) % 2 == 0, base, base + amp)
    img = np.broadcast_to(patt, (240, 320)).astype(np.uint8)
    return np.repeat(img[:, :, None], 3, axis=2)


def test_pattern_carries_signal_beyond_energy():
    # G-pattern: ENERGY and ARRANGEMENT are DECOUPLED. A HIGH-energy horizontal grating (wall-like
    # courses) has LOWER pattern_level than a LOW-energy vertical grating (door-jamb-like contours).
    # If energy alone drove recognition the ordering would reverse — so pattern is independent signal.
    import domains.doom_pattern_eye as eye
    vert_lo = _luma_grating(1, 20, axis=1)     # LOW-energy vertical contours (door-jamb-like arrangement)
    horiz_hi = _luma_grating(1, 220, axis=0)   # HIGH-energy horizontal contours (wall-course-like)
    e_vert = int(eye.col_orientation_hist(vert_lo).sum())
    e_horiz = int(eye.col_orientation_hist(horiz_hi).sum())
    pv = int(np.median(eye.col_pattern_level(vert_lo)[0]))
    ph = int(np.median(eye.col_pattern_level(horiz_hi)[0]))
    assert e_horiz > e_vert                                # the wall-like grating has MORE total energy
    assert pv > ph                                         # yet the door-like ARRANGEMENT reads higher
    # and the arrangement level is a RATIO -> invariant to energy scale (raising amplitude unchanged):
    assert int(np.median(eye.col_pattern_level(_luma_grating(1, 60, axis=1))[0])) == \
        int(np.median(eye.col_pattern_level(_luma_grating(1, 220, axis=1))[0]))


def test_colour_sign_sees_what_luma_cannot():
    # G-colour: a central colour patch matched in LUMA to the surround (same luma-gradient) but
    # different HUE. The luma texture channel is ~unchanged; the colour channel lights up.
    import domains.doom_pattern_eye as eye
    base = np.full((240, 320, 3), 60, np.uint8)                    # uniform grey wall
    # central columns: red-tinted but LUMA-matched (boost R, drop G/B so 77R+150G+29B ~ const)
    tinted = base.copy()
    tinted[:, 120:200, 0] = 120      # R up
    tinted[:, 120:200, 1] = 34       # G down (keeps luma ~ (77*120+150*34+29*29)>>8 ~ 60)
    tinted[:, 120:200, 2] = 29
    ttex_base = int(np.median(eye.col_texture_level(base)[0][120:200]))
    ttex_tint = int(np.median(eye.col_texture_level(tinted)[0][120:200]))
    ccol_base = int(np.median(eye.col_colour_level(base)[0][120:200]))
    ccol_tint = int(np.median(eye.col_colour_level(tinted)[0][120:200]))
    assert ttex_tint <= ttex_base + 1                              # luma texture blind to the hue
    assert ccol_tint >= ccol_base + 4                              # colour sign SEES it


def test_new_descriptor_reads_only_rendered_pixels_source_audit():
    # G-no-oracle: the new descriptor functions read ONLY rendered RGB (luma + colour channels
    # 0/1/2). No depth/labels/sectors buffer, no texture NAME.
    import domains.doom_pattern_eye as eye
    src = "\n".join(inspect.getsource(f) for f in (
        eye._mean_rgb_band, eye.col_colour_level, eye.col_orientation_hist, eye.col_pattern_level))
    tree = ast.parse(src)
    bad_attrs = {"depth_buffer", "labels_buffer", "labels", "sectors"}
    bad_subs = {"depth", "label", "texture", "linedef"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr not in bad_attrs, f"eye accesses .{node.attr}"
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
            assert node.slice.value not in bad_subs, f"eye indexes [{node.slice.value!r}]"


def test_integer_descriptors_from_synthetic_pixels():
    import domains.doom_pattern_eye as eye
    flat = np.full((240, 320, 3), 90, np.uint8)
    for fn in (eye.col_texture_level, eye.col_colour_level, eye.col_pattern_level):
        lvl, _ = fn(flat)
        assert lvl.dtype.kind in "iu"                             # integer array
        assert int(lvl.max()) == 0                                # a flat surface -> level 0 everywhere
