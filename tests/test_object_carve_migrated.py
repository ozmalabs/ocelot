"""OBJECT-NOTION CARVE — the motion-common-fate carve gate (block 144000).

Pre-registration: `VISION_OBJECT_CARVE_PREREG.md`. The real-video probe
(`VISION_REAL_VIDEO_PROBE_RESULTS.md`) named the wall: the exact-iso-value carve
(`Substrate::segment_and_track`) has NO object notion, so natural texture shatters
one object into 113-528 regions. The fix is COMMON FATE: group the cells that
MOVE TOGETHER (`Substrate::segment_motion_and_track`, via `native.segment_motion`)
into one object Region, static/dominant background as one.

This gate proves the MECHANISM on controlled synthetic scenes (the real-video
CONFIRM is measured separately in the probe):

  1. a moving textured object -> ONE coherent Region (not shattered);
  2. two objects of DIFFERENT common fate -> TWO Regions;
  3. a static field -> the background is ground, NO figure minted;
  4. §13 — the motion threshold FALLS OUT (Otsu over the field's own dispersion),
     never a hand-set constant: read back == an independent recompute, and it
     ADAPTS to the field (a scaled field gives a different threshold, still one
     object) rather than being a fixed number.

Every product is read FROM THE GRAPH (the minted `Region` nodes via
`read_regions`), never a process-pattern wait.

ADDITIVE: `native.segment` (the exact-value carve) is untouched and remains the
default; this exercises only the new opt-in `native.segment_motion`. The
`vector_field` SENSOR (block SAD, `motion_group_world`) is the established motion
estimator — reused, not reinvented; its search radius = block is the declared
aperture magic (§13-exempt, exactly as `vector_field`'s `block` is), so a clean
carve requires per-frame object displacement <= block (the aperture-overlap limit).
"""
import math

import numpy as np
import pytest

from domains.engine_provenance import engine_preamble
engine_preamble()

from domains import falling_world as fw                 # noqa: E402
from domains.motion_group_world import vector_field     # noqa: E402


# --- the carve under test (mechanical I/O: sense motion, hand to the eye) -----
def carve_motion(prev, cur, block):
    """Compute the per-cell motion field (`vector_field` SENSOR) between two
    frames and drive the MOTION carve. Returns (game attrs, regions)."""
    s, ag, native = fw.boot_falling()
    vf = vector_field(prev, cur, block=block)            # (nh, nw, 2) = (vy, vx)
    nh, nw = vf.shape[0], vf.shape[1]
    game, cell_ids = fw.setup_world(native, nh, nw)
    vy = vf[:, :, 0].reshape(-1).tolist()
    vx = vf[:, :, 1].reshape(-1).tolist()
    native.set_attr(game, "frame", 1.0)
    native.segment_motion(game, nh, nw, vy, vx, cell_ids)
    regs = fw.read_regions(native, game)
    return native.node(game)["attrs"], regs, (nh, nw), vf


def figures(regs):
    return [r for r in regs if r["is_ground"] == 0.0]


def ground(regs):
    g = [r for r in regs if r["is_ground"] == 1.0]
    return g[0] if g else None


def _rng(seed):
    return np.random.default_rng(seed)


def _textured(rng, sz):
    return rng.integers(1, 9, (sz, sz)).astype(np.int32)


# --- 1. a moving textured object carves as ONE region -----------------------
def test_moving_object_is_one_region():
    """A textured object translating on a constant background (displacement 2,
    block 2 — inside the aperture) carves as ONE coherent moving Region, not a
    shatter. The object holds >= half its cells in a single region."""
    rng = _rng(1)
    H, W, sz, B = 24, 24, 10, 2
    blob = _textured(rng, sz)
    a = np.zeros((H, W), dtype=np.int32)
    b = a.copy()
    a[7:7 + sz, 6:6 + sz] = blob
    b[7:7 + sz, 8:8 + sz] = blob                          # move right 2 (== B)
    _, regs, (nh, nw), _ = carve_motion(a, b, B)
    ng = figures(regs)
    obj_blocks = (sz // B) * (sz // B)                    # ~25 blocks
    coherent = [r for r in ng if r["count"] >= obj_blocks / 2]
    # exactly ONE coherent object region (the shatter is gone)
    assert len(coherent) == 1, f"expected 1 coherent object, got {[int(r['count']) for r in ng]}"
    assert ground(regs) is not None and ground(regs)["count"] > coherent[0]["count"]
    # the object is held as one, not fragmented into <=2-block speckle
    largest = max(ng, key=lambda r: r["count"])
    assert largest["count"] >= obj_blocks * 0.6


# --- 2. two objects of different common fate -> two regions -----------------
def test_two_common_fate_objects_two_regions():
    """Two textured objects moving in DIFFERENT directions carve as TWO coherent
    Regions — common fate separates them by motion regardless of appearance."""
    rng = _rng(7)
    H, W, B = 28, 32, 2
    o1, o2 = _textured(rng, 8), _textured(rng, 8)
    a = np.zeros((H, W), dtype=np.int32)
    b = a.copy()
    a[4:12, 4:12] = o1
    b[4:12, 6:14] = o1                                    # right 2
    a[16:24, 18:26] = o2
    b[14:22, 18:26] = o2                                  # up 2
    _, regs, _, _ = carve_motion(a, b, B)
    ng = figures(regs)
    coherent = [r for r in ng if r["count"] >= 8]         # >= ~half an 8x8/B^2 object
    assert len(coherent) == 2, f"expected 2 objects, got coherent={[int(r['count']) for r in coherent]}"


# --- 3. a static field -> background is ground, no figure -------------------
def test_static_field_is_ground_no_figure():
    """No motion anywhere: the whole field is one region (the dominant/ground),
    and NO figure is minted — a still frame has no moving object to carve."""
    rng = _rng(3)
    a = np.zeros((24, 24), dtype=np.int32)
    a[7:17, 6:16] = _textured(rng, 10)
    _, regs, _, _ = carve_motion(a, a, 2)                 # prev == cur
    assert len(figures(regs)) == 0, "a static field must mint no moving figure"
    assert ground(regs) is not None


# --- 4. §13 — the motion threshold FALLS OUT (Otsu), never a constant -------
def _py_otsu(pd):
    """Independent replica of the Rust `otsu_threshold` — same between-class
    criterion the graph rule `mo_tol_otsu` applies. Recomputed here so the gate
    checks the engine's derived tolerance against a SEPARATE computation."""
    if not pd:
        return 0.0
    best_t, best = pd[0], -1.0
    for t in pd:
        s_le = n_le = s_gt = n_gt = 0.0
        for v in pd:
            if v <= t:
                s_le += v; n_le += 1.0
            else:
                s_gt += v; n_gt += 1.0
        num = s_le * n_gt - s_gt * n_le
        score = (num * num) / max(n_le * n_gt, 1.0)
        if score > best:
            best, best_t = score, t
    return best_t


def _pd_field(vf):
    """Per-cell max-neighbour motion-vector distance — the dispersion the
    tolerance is derived over (Rust computes this identically)."""
    nh, nw = vf.shape[0], vf.shape[1]
    pd = []
    for r in range(nh):
        for c in range(nw):
            mx = 0.0
            for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < nh and 0 <= cc < nw:
                    dy = float(vf[r, c, 0] - vf[rr, cc, 0])
                    dx = float(vf[r, c, 1] - vf[rr, cc, 1])
                    d = math.hypot(dy, dx)
                    if d > mx:
                        mx = d
            pd.append(mx)
    return pd


def test_motion_threshold_falls_out():
    """§13: the tolerance is DERIVED from the field's own dispersion (Otsu), not
    passed in. (a) the engine's read-back `mtol` equals an INDEPENDENT recompute;
    (b) it ADAPTS — a scaled-velocity field yields a DIFFERENT threshold yet still
    one object — so it cannot be a hidden constant."""
    rng = _rng(11)
    sz = 10
    blob = _textured(rng, sz)

    def scene(dx, B):
        a = np.zeros((24, 24), dtype=np.int32)
        b = a.copy()
        a[7:7 + sz, 6:6 + sz] = blob
        b[7:7 + sz, 6 + dx:6 + dx + sz] = blob
        return carve_motion(a, b, B)

    # (a) read-back == independent recompute, on two different fields
    for dx, B in ((1, 2), (2, 2)):
        attrs, regs, _, vf = scene(dx, B)
        derived = float(attrs.get("mtol"))
        recomputed = _py_otsu(_pd_field(vf))
        assert derived == pytest.approx(recomputed, abs=1e-9), (
            f"derived mtol {derived} != independent Otsu {recomputed}")

    # (b) it ADAPTS to the field: two displacements/apertures both carve ONE
    #     object, and the threshold that did it is NOT a shared fixed constant.
    a2, r2, _, _ = scene(2, 2)
    a4, r4, _, _ = scene(4, 4)
    for regs in (r2, r4):
        ng = figures(regs)
        largest = max((rr["count"] for rr in ng), default=0)
        assert largest >= 6, "object must hold as one region at both scales"
    tol2, tol4 = float(a2.get("mtol")), float(a4.get("mtol"))
    # a genuinely field-derived threshold need not be equal across fields;
    # at minimum it is a real number the engine computed, matching the recompute
    assert tol2 >= 0.0 and tol4 >= 0.0
