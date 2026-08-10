"""doom_pattern_eye — a GENERIC pattern-recognition EYE, wired to Doom as one world.

We are building an eye that HAPPENS to work in Doom, not a Doom-playing eye. This module
is mechanical I/O only: it turns rendered pixels (and SEEN depth-from-motion) into an
INTEGER pattern descriptor per perceived region, writes PerceivedRegion nodes, runs the
generic graph rules (seed `pattern_recognition.json`: novelty-salience -> nearest-prototype
recognition -> affordance investigation), and reads the recognition back. Every decision is
a rule; the eye only quantises and translates.

DESCRIPTOR (integer, 0..K per dimension) = [geometry_level, texture_level]:
  * texture_level — quantised SEEN VERTICAL-gradient energy of the column's rendered luma
    (a marked/detailed surface reads high; a plain wall reads ~0). RGB PIXELS ONLY: no
    texture NAME, no labels buffer (161000/203000 discipline; audited).
  * geometry_level — quantised SEEN STRUCTURAL horizontal-edge energy ABOVE the frame's
    ambient (texture) baseline (block 211000). A door's "differing geometry" is a
    framed/recessed sector — a DEPTH DISCONTINUITY, which is an OCCLUDING CONTOUR: a
    VERTICAL edge in the image (depth steps left→right along a column). Its SEEN signature
    is the HORIZONTAL luma gradient — the ORTHOGONAL twin of the texture channel's vertical
    gradient. A door frame / recess boundary / corner reads high; a flat wall reads ~0. To
    strip the pervasive texture floor (every Doom wall carries horizontal detail), the
    ambient horizontal-gradient MEDIAN across the frame's columns is subtracted, so only a
    LOCAL structural edge that stands out from its surface survives. RGB PIXELS ONLY —
    single frame, NO motion, NO depth buffer, NO sectors, NO labels (audited). The VizDoom
    depth buffer / sectors are a SCORING ORACLE only (block 211000 measured this feature at
    AUC 0.78 vs a depth-EDGE oracle over ~169k real columns, vs 209000's motion baseline
    0.508; ROBUST_GEOMETRY_RESULTS.md). This SUPERSEDES 209000's depth-from-motion geometry
    (chance on real frames): geometry-from-SEEN-luma-edges beats geometry-from-motion.

Quantisation (eye I/O, integer): luma uses the integer ITU-R BT.601 approximation
(77R+150G+29B)>>8; both channels are integer sums of |Δluma| (texture: vertical; geometry:
horizontal, minus the integer ambient median, clipped at 0); the level is integer division
of that sum. In-frame observations are integer by construction — NO float reaches the graph.
"""
from __future__ import annotations
import json, os

GH, GW, BLOCK = 240, 320, 16
K = 8                         # descriptor levels 0..K
TEX_DIV = 100                 # texture-energy sum per level (calibrated on real E1M1 pixels)
GEO_DIV = 100                 # structural-edge energy (above ambient) per geometry level (211000)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_PATH = os.path.join(ROOT, "seeds", "pattern_recognition.json")


# --------------------------------------------------------- the eye (SEEN, integer)
def _luma_int(rgb):
    """Integer luma (ITU-R BT.601 approx) of a rendered RGB frame. Pixels are integers in,
    integer out. NO depth, NO labels, NO texture name."""
    import numpy as np
    a = np.asarray(rgb)
    if a.ndim == 3 and a.shape[0] == 3:
        a = np.transpose(a, (1, 2, 0))
    a = a.astype(np.int32)
    return (77 * a[..., 0] + 150 * a[..., 1] + 29 * a[..., 2]) >> 8


def col_texture_level(rgb, tex_div=TEX_DIV, k=K):
    """Per-column INTEGER texture level 0..K = quantised SEEN vertical-gradient energy of the
    rendered luma column band. Plain wall -> ~0; marked/detailed surface -> high. Pixels only."""
    import numpy as np
    lum = _luma_int(rgb)
    band = lum[GH // 4: 3 * GH // 4]
    energy = np.abs(np.diff(band, axis=0)).sum(0).astype(np.int64)   # integer sum of |Δluma|
    return np.minimum(k, energy // tex_div).astype(np.int64), energy


def col_structural_level(rgb, geo_div=GEO_DIV, k=K):
    """Per-column INTEGER geometry level 0..K = quantised SEEN STRUCTURAL horizontal-edge energy
    ABOVE the frame's ambient (texture) baseline. A depth discontinuity (door frame / recess
    boundary / corner) is an OCCLUDING CONTOUR — a vertical edge in the image — whose SEEN
    signature is the HORIZONTAL luma gradient (orthogonal to the texture channel). The integer
    ambient MEDIAN of that gradient across columns is subtracted so the pervasive texture floor
    drops out and only a LOCAL structural edge survives. Single frame, RGB PIXELS ONLY: NO
    motion, NO depth/labels buffer, NO sectors, NO texture name. Returns (levels[GW] int, energy)."""
    import numpy as np
    lum = _luma_int(rgb).astype(np.int64)
    hg = np.abs(np.diff(lum, axis=1))                 # SEEN horizontal gradient |Δluma| (H, W-1)
    band = hg[GH // 4: 3 * GH // 4]
    energy = np.zeros(GW, dtype=np.int64)
    energy[1:] = band.sum(0)                          # per-column horizontal-gradient energy (integer)
    ambient = int(np.median(energy))                 # ambient (texture) baseline, integer
    structural = np.maximum(0, energy - ambient)     # LOCAL structural edge above ambient (integer)
    return np.minimum(k, structural // geo_div).astype(np.int64), energy


def col_geometry_level(frames, fi, geo_div=GEO_DIV, k=K):
    """Per-column INTEGER geometry level 0..K from the SEEN structural horizontal-edge feature
    (block 211000, supersedes 209000's depth-from-motion). Single frame — reads only frames[fi]'s
    rendered RGB. Returns (levels[GW] int, diag). Kept (frames, fi)-shaped for its callers."""
    import numpy as np
    rgb = frames[fi]["rgb"] if (frames is not None and fi is not None) else None
    if rgb is None:
        return np.zeros(GW, dtype=np.int64), {"why": "no_frame"}
    lvl, energy = col_structural_level(rgb, geo_div, k)
    return lvl, {"why": "ok", "ambient": int(np.median(energy))}


def region_descriptor(rgb, frames=None, fi=None):
    """Per-column INTEGER descriptor (geom_level, tex_level). Mechanical eye quantisation — both
    channels are SEEN, single-frame, integer (texture = vertical gradient; geometry = structural
    horizontal edge above ambient). `frames`/`fi` are accepted for backward compat but unused now
    that geometry needs no motion."""
    import numpy as np
    tex, energy = col_texture_level(rgb)
    geo, gen = col_structural_level(rgb)
    return geo, tex, {"energy": energy, "geo_ambient": int(np.median(gen))}


# ============================================================ block 214000: GENUINE texture
# The 209000 texture channel is a single ENERGY scalar (col_texture_level). It gets edge-DENSE
# doors but MISSES texture-FAINT ones (sec83/sec85 read level ~2 -> unrecognised, 0 opens) and
# is COLOUR-BLIND. These add two richer, still-INTEGER, RGB-only descriptor dimensions matched
# against the held door concept: COLOUR-as-a-sign (chroma contrast from the ambient wall) and
# PATTERN-as-arrangement (orientation of the gradient, not just its magnitude). MEASURED on real
# E1M1 (TEXTURE_RECOGNITION_RESULTS.md): the arrangement dimension RECOVERS the faint doors the
# energy scalar throws away (faint-door door-vs-wall AUC 0.94 vs the scalar's 0.69). RGB PIXELS
# ONLY: rgb[...,0/1/2] are colour channels, NOT a depth/labels/sectors buffer, NO texture NAME.
COL_DIV = 8                   # chroma-contrast sum per colour level (calibrated on real E1M1)
PAT_DIV = 40                  # horizontal-edge share (per-mille) per pattern level


def _mean_rgb_band(rgb):
    """Per-column integer mean (R,G,B) over the central band. RGB channels only."""
    import numpy as np
    a = np.asarray(rgb)
    if a.ndim == 3 and a.shape[0] == 3:
        a = np.transpose(a, (1, 2, 0))
    a = a.astype(np.int64)[GH // 4: 3 * GH // 4]
    return a[..., 0].mean(0), a[..., 1].mean(0), a[..., 2].mean(0)


def col_colour_level(rgb, col_div=COL_DIV, k=K):
    """Per-column INTEGER COLOUR-as-a-sign = quantised chroma contrast from the frame's ambient
    wall. Per column: mean (R,G,B) -> integer luma m -> chroma vector (R-m,G-m,B-m); ambient =
    per-channel MEDIAN chroma across columns (the surrounding wall); level = min(k, L1(chroma -
    ambient)//col_div). A region whose MATERIAL/HUE differs from its wall reads high EVEN at
    matched luma-gradient (the thing the luma-only channel throws away); a plain wall IS the
    ambient -> ~0. RGB channels only: NO depth, NO labels, NO texture name. Returns (levels, diag)."""
    import numpy as np
    mr, mg, mb = _mean_rgb_band(rgb)
    m = (77 * mr + 150 * mg + 29 * mb) // 256                     # per-column integer luma
    cr, cg, cb = mr - m, mg - m, mb - m                           # per-column chroma vector
    ar, ag, ab = int(np.median(cr)), int(np.median(cg)), int(np.median(cb))   # ambient wall chroma
    l1 = (np.abs(cr - ar) + np.abs(cg - ag) + np.abs(cb - ab)).astype(np.int64)
    return np.minimum(k, l1 // col_div).astype(np.int64), l1


def col_orientation_hist(rgb):
    """Per-column INTEGER 4-bin orientation histogram of the SEEN luma gradient over the central
    band. Bins by the gradient's DIRECTION: [0]=horizontal-gradient-dominant (|gx|>|gy|, i.e. a
    VERTICAL image contour — a door jamb / panel edge); [1]=vertical-gradient-dominant (|gy|>=|gx|,
    a HORIZONTAL contour — a wall course / mortar line); [2],[3]=diagonal signs. Each bin = summed
    |gradient| magnitude. Captures the ARRANGEMENT of edges (a door's vertical frame/panel
    structure vs a wall's horizontal-course/isotropic busy-ness), not just their total magnitude.
    RGB luma only. Returns hist[4, GW]."""
    import numpy as np
    lum = _luma_int(rgb).astype(np.int64)[GH // 4: 3 * GH // 4]
    gy = np.zeros_like(lum); gx = np.zeros_like(lum)
    gy[1:, :] = np.diff(lum, axis=0)                              # vertical gradient (Δ down rows)
    gx[:, 1:] = np.diff(lum, axis=1)                              # horizontal gradient (Δ across cols)
    mag = np.abs(gx) + np.abs(gy)
    hgrad = np.abs(gx) > np.abs(gy)                               # horizontal-gradient => vertical contour
    diagp = gx * gy > 0
    h = np.zeros((4, lum.shape[1]), np.int64)
    h[0] = (mag * hgrad).sum(0); h[1] = (mag * (~hgrad)).sum(0)
    h[2] = (mag * (diagp & hgrad)).sum(0); h[3] = (mag * ((~diagp) & hgrad)).sum(0)
    return h


def col_pattern_level(rgb, pat_div=PAT_DIV, k=K):
    """Per-column INTEGER PATTERN-as-arrangement level = quantised HORIZONTAL-GRADIENT share
    (per-mille) of the column's gradient energy — the fraction of edge energy that forms VERTICAL
    image contours (door jambs / panel lines). A door's framed/panelled structure devotes a larger
    SHARE of its edges to vertical contours than a wall's horizontal-course/isotropic texture — a
    RATIO that normalises out total energy, so it separates a texture-FAINT door from a busy wall
    where the raw energy scalar cannot (MEASURED: door ~30% share vs wall ~13%; faint-door
    door-vs-wall AUC 0.94 vs the energy scalar's 0.69). RGB luma only. Returns (levels, share)."""
    import numpy as np
    h = col_orientation_hist(rgb)
    total = h.sum(0)
    share = np.where(total > 0, (h[0] * 1000) // np.maximum(total, 1), 0).astype(np.int64)
    return np.minimum(k, share // pat_div).astype(np.int64), share


def texture_descriptor(rgb):
    """The RICHER per-column INTEGER texture descriptor (tex_level, colour_level, pattern_level).
    tex_level = 209000 vertical-gradient ENERGY (magnitude); colour_level = chroma contrast from
    the ambient wall (the COLOUR sign); pattern_level = horizontal-edge share (the ARRANGEMENT).
    All SEEN, single-frame, integer, RGB pixels only. Returns (tex, colour, pattern, diag)."""
    import numpy as np
    tex, energy = col_texture_level(rgb)
    colour, l1 = col_colour_level(rgb)
    pattern, share = col_pattern_level(rgb)
    return tex, colour, pattern, {"colour_l1": l1, "pattern_share": share}


# --------------------------------------------------------------- graph hand-off
def install(wa, game, *, salience_floor=2):
    """Opt-in: create the PatternParams gate (OFF by default absent this) + link the held
    library to this game. Mechanical."""
    S, I = wa.s, wa.inner
    p = S.add_node("PatternParams", {"enabled": 1.0, "salience_floor": int(salience_floor)})
    I.add_edge_unchecked(game, "has_pattern_params", p)
    libs = list(I.nodes("PatternLibrary"))
    if libs:
        I.add_edge_unchecked(game, "has_pattern_library", libs[0])
    return p


def ingest_region(wa, game, geom_level, tex_level, meta=None):
    """Write ONE PerceivedRegion carrying its INTEGER descriptor. Mechanical."""
    S, I = wa.s, wa.inner
    attrs = {"geom_level": int(geom_level), "tex_level": int(tex_level), "near": 0.0}
    if meta:
        attrs.update(meta)
    r = S.add_node("PerceivedRegion", attrs)
    I.add_edge_unchecked(game, "has_perceived_region", r)
    return r


def recognise(wa, region_ids):
    """Run the generic rules and read back what the graph recognised. Mechanical read."""
    S, I = wa.s, wa.inner
    I.run_rules(50000)
    out = {}
    for r in region_ids:
        a = S.node(r)["attrs"]
        out[r] = {"salience": a.get("salience"), "salient": a.get("salient"),
                  "family": a.get("recognised_family"), "recognised_as": a.get("recognised_as"),
                  "affordance": a.get("recog_affordance")}
    return out


def read_investigations(wa):
    S, I = wa.s, wa.inner
    return [{"kind": S.node(i)["attrs"].get("kind"), "target": S.node(i)["attrs"].get("target_concept"),
             "action": S.node(i)["attrs"].get("action"), "locality": S.node(i)["attrs"].get("locality")}
            for i in I.nodes("Investigation")]


def fresh_adapter():
    from substrate.world_adapter import WorldAdapter
    wa = WorldAdapter(seeds=())
    wa.inner.load_seed_manifest(json.load(open(SEED_PATH)), None)
    return wa


# ------------------------------------------- block 214000: richer-texture graph hand-off (mechanical)
TEXTURE_SEED_PATH = os.path.join(ROOT, "seeds", "pattern_texture_signature.json")


def fresh_texture_adapter():
    """Boot a WorldAdapter carrying ONLY the richer-texture seed. Mechanical."""
    from substrate.world_adapter import WorldAdapter
    wa = WorldAdapter(seeds=())
    wa.inner.load_seed_manifest(json.load(open(TEXTURE_SEED_PATH)), None)
    return wa


def install_texture(wa, game, *, salience_floor=2):
    """Opt-in: create the TextureParams gate (OFF by default absent this) + link the held
    TextureLibrary to this game. Mechanical."""
    S, I = wa.s, wa.inner
    p = S.add_node("TextureParams", {"enabled": 1.0, "salience_floor": int(salience_floor)})
    I.add_edge_unchecked(game, "has_texture_params", p)
    libs = list(I.nodes("TextureLibrary"))
    if libs:
        I.add_edge_unchecked(game, "has_texture_library", libs[0])
    return p


def ingest_texture_region(wa, game, tex_level, colour_level, pattern_level, meta=None):
    """Write ONE PerceivedRegion carrying its RICHER INTEGER texture descriptor
    (tex_level = energy, colour_level = chroma-contrast sign, pattern_level = arrangement).
    Mechanical eye-to-graph translation; no decision."""
    S, I = wa.s, wa.inner
    attrs = {"tex_level": int(tex_level), "colour_level": int(colour_level),
             "pattern_level": int(pattern_level)}
    if meta:
        attrs.update(meta)
    r = S.add_node("PerceivedRegion", attrs)
    I.add_edge_unchecked(game, "has_perceived_region", r)
    return r


def recognise_texture(wa, region_ids):
    """Run the generic rules and read back the richer-texture recognition. Mechanical read."""
    S, I = wa.s, wa.inner
    I.run_rules(50000)
    out = {}
    for r in region_ids:
        a = S.node(r)["attrs"]
        out[r] = {"tex_salience": a.get("tex_salience"), "tex_salient": a.get("tex_salient"),
                  "recognised_as": a.get("recognised_as"), "recog_via": a.get("recog_via"),
                  "affordance": a.get("recog_affordance")}
    return out
