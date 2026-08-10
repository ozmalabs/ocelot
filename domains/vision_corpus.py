"""vision_corpus — DEVELOPMENTAL VISION CORPUS PREP (Stage 2).

Mechanical data preparation for the vision curriculum: turn real external
material into on-disk frame chunks + text lesson manifests that
`curriculum_study.study_tick` can hand to the vision lesson processor.

ARCHITECTURE (CLAUDE.md). This module is a WORLD ADAPTER / data-prep step,
exactly the role `voice_curriculum.prepare_lesson_plan` plays for the voice
curriculum: read an external reference (a Jellyfin episode's pixels, a BSDS300
photo, an Omniglot motor file), write the frames to disk, and list them in a
lesson file. It decides NOTHING about graph state -- no conditionals over the
agent, no ranking of content by meaning. Which frames become which lesson is a
mechanical, deterministic function of the source ordering (the SAME positional
slicing `VisionWorld.ingest` does over an image, one level up).

THE SOURCES (all REAL data, donkey=0 -- no LLM, no synthetic stand-in where a
real one exists):

  * `jellyfin`  — real children's developmental television (Sesame Street, Ask
    the StoryBots, Frog and Toad, ...), streamed via the EXISTING
    `scripts/jellyfin_world.JellyfinWorld` adapter. This is the closest
    obtainable stand-in for the literature steer's child-perspective video
    (SAYCam/CVCL is gated behind a Databrary application and is NOT
    obtainable here -- recorded honestly, never faked). It is broadcast
    child-directed video, NOT egocentric: the ecological ordering and the
    head-mounted viewpoint are absent. Named, not papered over.
  * `bsds`      — BSDS300 natural photographs (real camera images). The
    classic natural-image-statistics setting (Olshausen & Field): the
    NON-CIRCULAR control for "does biological kernel structure emerge from
    natural statistics", because cartoon/broadcast frames have very different
    (flat-region + hard-edge) statistics from natural scenes.
  * `omniglot`  — real human pen trajectories (data/omniglot), rendered to
    rasters via the EXISTING `domains.scattering_feature.render_trace`. Used
    for the transform-invariance + composition levels, where the repo's own
    StrokeQuantize/TransformDecode arc is already proven and, crucially,
    where the transform applied is GROUND TRUTH (we rendered it), so the gate
    can measure zero-mint transform reads honestly.

FRAME FORMAT: a `.npy` float32 array in [0,1]. A single frame is (h, w); a
sequence chunk is (n, h, w). Greyscale -- the vision floor's `ChangeDetect`
Term convolves one channel (colour is not in the Stage-1 floor contract).

LESSON FORMAT: a text file (so `study_tick`'s `open(path).read()` is
unchanged), one record per line:

    <kind>\t<npy_path>\t<meta_json>

`meta_json` carries the mechanical provenance (source, episode id, frame
index, and for `invariance` the ground-truth transform applied). The lesson
processor reads the frames; it never re-derives meaning from this file.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

import numpy as np

_ROOT = __file__.rsplit("/domains/", 1)[0]
_DATA_DIR = os.path.join(_ROOT, "data", "vision_curriculum")
_FRAME_DIR = os.path.join(_DATA_DIR, "frames")
_LESSON_DIR = os.path.join(_DATA_DIR, "lessons")

# The whole-scene frame size the curriculum ingests. Chosen by MEASUREMENT
# (a 48x48 ingest + full rule fixpoint is instant; see the Stage-2 arc notes),
# not by taste: big enough to carry scene structure and motion, small enough
# that a study tick stays interactive.
FRAME = 64
# The native-resolution crop size for the babble level. A whole-frame
# downsample destroys the high-spatial-frequency statistics that kernel
# learning is ABOUT, so babble crops at native resolution instead of
# downsampling (the standard sparse-coding protocol).
CROP = 16


# --------------------------------------------------------------------------- #
#  MECHANICAL IMAGE OPS — plain array arithmetic, no decisions.
# --------------------------------------------------------------------------- #
def area_downsample(a: np.ndarray, out: int) -> np.ndarray:
    """Area-average `a` (h, w) down to (out, out). Mechanical resampling."""
    h, w = a.shape
    ch, cw = h // out, w // out
    if ch < 1 or cw < 1:
        raise ValueError(f"image {a.shape} smaller than target {out}")
    a = a[:ch * out, :cw * out]
    return a.reshape(out, ch, out, cw).mean(axis=(1, 3)).astype(np.float32)


def _save(arr: np.ndarray, path: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.save(path, np.ascontiguousarray(arr, dtype=np.float32))
    return path


def preprocess_patches(P: np.ndarray, *, min_std: float = 0.04) -> np.ndarray:
    """DC-REMOVE + CONTRAST-NORMALISE a batch of patches (n, k, k); drop the
    flat ones. Returns (m, k, k) with m <= n.

    This is the standard sparse-coding / receptive-field-learning protocol,
    and it is NOT a free parameter -- it is load-bearing in both directions,
    so it is named here rather than buried:

      * WHY IT IS NEEDED. Raw natural patches live in [0,1] and are dominated
        by their DC (mean) component: every patch correlates strongly with
        every other, so (a) a residual/novelty test can never fire -- nothing
        ever looks unexplained -- and (b) Oja's rule diverges, because
        y = w.x is large and eta*y^2 exceeds 1, which flips the decay term
        negative. Both were MEASURED on this corpus before this step existed
        (one kernel minted, weights -> NaN), not anticipated.
      * WHAT IT COSTS THE CLAIM. Mean removal is exactly what retinal centre-
        surround does, and contrast normalisation is retinal gain control. So
        this step MODELS the retina rather than growing it: any centre-
        surround structure that appears downstream cannot be credited to the
        learning rule alone, because the input has already been DC-removed.
        That is the honest boundary of the L0 result and must be reported
        with it. (Olshausen & Field's oriented receptive fields likewise
        emerge from WHITENED input; the un-whitened case yields low-frequency
        blobs.) The cortical claim that survives is about ORIENTED structure
        emerging above a retina-like front end -- not about rediscovering the
        retina itself.

    `min_std` drops patches with no structure (blank sky): a flat patch has
    no direction to teach, and after normalisation its unit vector would be
    pure quantisation noise.
    """
    P = np.asarray(P, np.float32)
    if len(P) == 0:                      # total on empty input: reshape(0, -1)
        return P                          # raises (numpy cannot infer -1 at size 0)
    flat = P.reshape(len(P), -1)
    keep = flat.std(axis=1) > min_std
    flat = flat[keep]
    if not len(flat):
        return np.zeros((0,) + P.shape[1:], np.float32)
    flat = flat - flat.mean(axis=1, keepdims=True)          # DC removal
    n = np.linalg.norm(flat, axis=1, keepdims=True)
    n[n == 0] = 1.0
    flat = flat / n                                          # unit contrast
    return flat.reshape((-1,) + P.shape[1:]).astype(np.float32)


# --------------------------------------------------------------------------- #
#  SOURCE: JELLYFIN — real children's developmental television.
# --------------------------------------------------------------------------- #
def _jellyfin():
    import sys
    sp = os.path.join(_ROOT, "scripts")
    if sp not in sys.path:
        sys.path.insert(0, sp)
    from jellyfin_world import JellyfinWorld  # noqa: E402
    return JellyfinWorld().connect()


def episode_frames(jf, item_id: str, *, n: int, every: int = 6,
                   start_s: int = 300, size: int = FRAME) -> np.ndarray:
    """Decode `n` frames from one episode, sampling every `every`-th decoded
    frame from `start_s` seconds in (past the title sequence), area-averaged
    to (size, size) greyscale in [0,1]. Pure I/O: PyAV/ffmpeg opens the
    Jellyfin stream URL over HTTP, no full download."""
    import av
    url = jf.stream_url(item_id)
    c = av.open(url, timeout=30)
    try:
        c.streams.video[0].thread_type = "AUTO"
        if start_s:
            c.seek(int(start_s) * 1_000_000)          # AV_TIME_BASE micros
        out = []
        for i, f in enumerate(c.decode(video=0)):
            if every > 1 and i % every:
                continue
            g = f.to_ndarray(format="gray").astype(np.float32) / 255.0
            out.append(area_downsample(g, size))
            if len(out) >= n:
                break
    finally:
        c.close()
    return np.stack(out) if out else np.zeros((0, size, size), np.float32)


def episode_crops(jf, item_id: str, *, n: int, every: int = 24,
                  start_s: int = 300, crop: int = CROP,
                  seed: int = 0) -> np.ndarray:
    """`n` NATIVE-RESOLUTION crops sampled from one episode -- the babble
    level's input. Crops (never a whole-frame downsample) so the high-
    spatial-frequency statistics kernel learning depends on survive. Crop
    positions come from a seeded RNG: deterministic, reproducible, and a
    positional choice, not a content decision."""
    import av
    rng = np.random.default_rng(seed)
    url = jf.stream_url(item_id)
    c = av.open(url, timeout=30)
    try:
        c.streams.video[0].thread_type = "AUTO"
        if start_s:
            c.seek(int(start_s) * 1_000_000)
        out = []
        for i, f in enumerate(c.decode(video=0)):
            if every > 1 and i % every:
                continue
            g = f.to_ndarray(format="gray").astype(np.float32) / 255.0
            h, w = g.shape
            r0 = int(rng.integers(0, max(1, h - crop)))
            c0 = int(rng.integers(0, max(1, w - crop)))
            out.append(g[r0:r0 + crop, c0:c0 + crop])
            if len(out) >= n:
                break
    finally:
        c.close()
    return np.stack(out) if out else np.zeros((0, crop, crop), np.float32)


# --------------------------------------------------------------------------- #
#  SOURCE: BSDS300 — real natural photographs (the statistics control).
# --------------------------------------------------------------------------- #
def bsds_paths(split: str = "train") -> list[str]:
    d = os.path.join(_DATA_DIR, "BSDS300", "images", split)
    if not os.path.isdir(d):
        return []
    return sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".jpg"))


def bsds_crops(*, n: int, crop: int = CROP, seed: int = 0,
               split: str = "train") -> np.ndarray:
    """`n` native-resolution crops from BSDS300 photographs -- the
    natural-image-statistics control for the babble level."""
    from PIL import Image
    rng = np.random.default_rng(seed)
    paths = bsds_paths(split)
    out: list[np.ndarray] = []
    if not paths:
        return np.zeros((0, crop, crop), np.float32)
    while len(out) < n:
        p = paths[int(rng.integers(0, len(paths)))]
        g = np.asarray(Image.open(p).convert("L"), np.float32) / 255.0
        h, w = g.shape
        r0 = int(rng.integers(0, max(1, h - crop)))
        c0 = int(rng.integers(0, max(1, w - crop)))
        out.append(g[r0:r0 + crop, c0:c0 + crop])
    return np.stack(out)


# --------------------------------------------------------------------------- #
#  SOURCE: OMNIGLOT — real human ink, rendered via the EXISTING renderer.
# --------------------------------------------------------------------------- #
def _fixed_frame_raster(strokes, *, size: int, mn: np.ndarray, span: np.ndarray,
                        thick: int = 1) -> np.ndarray:
    """Rasterise pen strokes through a FIXED coordinate mapping (`mn`/`span`
    supplied by the caller, NOT re-derived per image).

    Why this exists rather than reusing `scattering_feature.render_trace`:
    that renderer min/max-normalises EACH AXIS INDEPENDENTLY per image
    (`scattering_feature.py:160-162`), which is right for its own
    scale-invariant feature job but destroys transform staging --
    a translation and a uniform scale are normalised away entirely, and a
    rotation comes back as rotation PLUS an anisotropic stretch (the bbox
    changes, so the per-axis spans change). None of those are the similarity
    transform the invariance level must present. Fixing the frame ONCE from
    the base glyph and reusing it for every variant makes the staged
    transform exactly the transform applied. The line-fill below is the same
    mechanical segment walk `render_trace` does."""
    img = np.zeros((size, size), np.float32)
    for st in strokes:
        a = np.asarray(st, float)
        if len(a) < 2:
            continue
        g = ((a - mn) / span) * (size - 1 - 2 * thick) + thick
        gi = np.rint(g).astype(int)
        for i in range(len(gi) - 1):
            p0, p1 = gi[i], gi[i + 1]
            steps = int(max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1]), 1))
            for s in range(steps + 1):
                t = s / steps
                xx = int(round(p0[0] + t * (p1[0] - p0[0])))
                yy = int(round(p0[1] + t * (p1[1] - p0[1])))
                if 0 <= yy < size and 0 <= xx < size:
                    img[yy, xx] = 1.0
    return img


def _similarity(strokes, *, deg: float = 0.0, scale: float = 1.0,
                shift=(0.0, 0.0), centre: np.ndarray) -> list:
    """Apply ONE global similarity transform (rotate about `centre`, uniform
    scale about `centre`, then translate) to EVERY stroke of a character.

    Global is load-bearing: transforming each stroke about its OWN centroid
    deforms the glyph (it moves the strokes relative to one another) instead
    of posing it, which is not a pose quantum at all."""
    th = np.deg2rad(deg)
    r = np.array([[np.cos(th), -np.sin(th)],
                  [np.sin(th), np.cos(th)]])
    out = []
    for st in strokes:
        a = np.asarray(st, float)
        a = (a - centre) @ r.T * scale + centre + np.asarray(shift, float)
        out.append(a)
    return out


def omniglot_transformed(path: str, *, size: int = FRAME):
    """(base_raster, [(transform_name, param, raster), ...]) for one character.

    The transform is applied to the PEN POINTS and re-rendered through a
    coordinate frame FIXED by the base glyph, so the staged transform IS the
    transform applied -- ground truth. That is what makes the invariance gate
    honest: a rung-1 `TransformDecode` read must recognise the transformed
    glyph as a POSE QUANTUM of the held shape rather than minting a new one,
    and the gate can check that against the transform we know we applied.

    The frame is padded around the base glyph's bbox so a rotated/scaled/
    shifted variant still lands inside the raster instead of being clipped
    (clipping would be an uncontrolled second transform).
    """
    from domains import omniglot_world as ow
    strokes = ow.load_strokes(path)
    if not strokes:
        return None, []
    allpts = np.concatenate([np.asarray(s, float) for s in strokes if len(s)], axis=0)
    if len(allpts) < 2:
        return None, []
    centre = allpts.mean(axis=0)
    mn0, mx0 = allpts.min(0), allpts.max(0)
    span0 = np.where((mx0 - mn0) == 0, 1.0, (mx0 - mn0))
    # One ISOTROPIC span (max over axes) so the fixed frame does not stretch
    # the glyph anisotropically, + 45% padding for rotated/scaled variants.
    s0 = float(span0.max()) * 1.45
    ctr_box = (mn0 + mx0) / 2.0
    mn = ctr_box - s0 / 2.0
    span = np.array([s0, s0])

    base = _fixed_frame_raster(strokes, size=size, mn=mn, span=span)
    out = []
    for deg in (15.0, 30.0, 90.0):
        st = _similarity(strokes, deg=deg, centre=centre)
        out.append(("rotate", deg, _fixed_frame_raster(st, size=size, mn=mn, span=span)))
    for sc in (0.6, 1.4):
        st = _similarity(strokes, scale=sc, centre=centre)
        out.append(("scale", sc, _fixed_frame_raster(st, size=size, mn=mn, span=span)))
    for dx in (0.12, -0.12):
        st = _similarity(strokes, shift=(dx * s0, 0.0), centre=centre)
        out.append(("translate", dx, _fixed_frame_raster(st, size=size, mn=mn, span=span)))
    return base, out


__all__ = [
    "FRAME", "CROP", "area_downsample",
    "episode_frames", "episode_crops",
    "bsds_paths", "bsds_crops",
    "omniglot_transformed",
]
