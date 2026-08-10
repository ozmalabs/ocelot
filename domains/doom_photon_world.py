"""doom_photon_world — a PURE I/O world adapter: VizDoom frames -> photon flux.

The synthetic->real midpoint for the event-native photon eye (blocks 171-180).
This adapter does exactly two mechanical things and DECIDES NOTHING:

  INGEST: capture a real VizDoom E1M1 frame, area-mean DOWNSAMPLE its ITU-R 601
  luminance to the eye's az x el retina, and translate that luminance field into
  per-receptor Poisson PHOTON-COUNT packets (`{col,row,wavelength_nm,count}`) the
  photon eye ingests via `submit_photons_2d` — exactly as it ingests any light.
  The 8-bit luminance value IS the per-receptor photon-count MEAN; photon arrival
  is Poisson, so each tick draws shot noise around it.

  ORACLE (measurement only, NEVER fed to cognition): the same capture exposes the
  per-pixel DEPTH and LABELS buffers, area-mean downsampled to the retina grid.
  These are GROUND TRUTH for scoring the eye's reconstruction; the eye never sees
  them — no depth/labels node ever enters the substrate.

No RGB / Image / Patch node, no `native.segment` on pixels, no agent decision.
The eye's perception (transduce -> onset events -> held-surface EMA) is entirely
graph-native under `run_rules()`; this file only translates external I/O.
"""
from __future__ import annotations

import math
import os

import numpy as np
from substrate_rs import _native

DEFAULT_WAD = ("/home/matt/.local/share/Steam/steamapps/common/"
               "Ultimate Doom/base/DOOM.WAD")
ROD_NM = 498.0


# ---------------------------------------------------------------- downsample ---
def _block_mean(a, gh, gw):
    """Area-mean of a 2-D buffer into a (gh, gw) grid. Mechanical, no decision."""
    a = np.asarray(a, dtype=np.float64)
    H, W = a.shape
    bh, bw = H // gh, W // gw
    a = a[:gh * bh, :gw * bw].reshape(gh, bh, gw, bw)
    return a.mean(axis=(1, 3))


def luma_grid(rgb, n_el, n_az):
    """RGB (H,W,3) uint8 -> (n_el, n_az) luminance grid by area-mean.
    Luma = ITU-R 601 (0.299R + 0.587G + 0.114B)."""
    rgb = np.asarray(rgb)
    if rgb.ndim == 3 and rgb.shape[0] == 3:          # (3,H,W) -> (H,W,3)
        rgb = np.transpose(rgb, (1, 2, 0))
    luma = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1]
            + 0.114 * rgb[..., 2]).astype(np.float64)
    return _block_mean(luma, n_el, n_az)


def luma_layout(
        rgb, layout, n_el, n_az, *, fov_h_deg=90.0, fov_v_deg=60.0):
    """RGB -> one explicit receptor sheet in a single compiled batch call.

    `layout` is the mechanical optics contract from
    `photon_eye.receptor_layout_from_calibration`. Its row/column fields are
    storage addresses only; physical gaze and aperture determine exposure.
    """
    rgb = np.asarray(rgb)
    if rgb.ndim == 3 and rgb.shape[0] == 3:
        rgb = np.transpose(rgb, (1, 2, 0))
    if rgb.ndim != 3 or rgb.shape[2] < 3:
        raise ValueError("rgb must have shape (H,W,3) or (3,H,W)")
    layout = list(layout)
    if len(layout) != int(n_el) * int(n_az):
        raise ValueError("receptor layout size does not match output sheet")
    # The explicit uniform calibration is a compatibility spelling of the
    # existing apparatus. Keep its floating reduction order byte-for-byte too.
    if layout and str(layout[0].get("pathway", "")) == "uniform":
        return luma_grid(rgb, n_el, n_az)
    luma = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1]
            + 0.114 * rgb[..., 2]).astype(np.float64)
    values = _native.retinal_layout_sample(
        luma.reshape(-1).tolist(), int(luma.shape[0]), int(luma.shape[1]),
        [float(record["gaze_az"]) for record in layout],
        [float(record["gaze_el"]) for record in layout],
        [float(record["angular_width"]) for record in layout],
        [float(record["angular_height"]) for record in layout],
        math.radians(float(fov_h_deg)), math.radians(float(fov_v_deg)),
    )
    return np.asarray(values, dtype=np.float64).reshape(int(n_el), int(n_az))


def luma_grid_from_calibration(
        rgb, n_el, n_az, calibration, *, fov_h_deg=90.0, fov_v_deg=60.0):
    """Mechanical calibration entry point; returns `(luma, layout)`.

    The absent and explicit-uniform paths call the legacy block mean verbatim;
    foveated layouts use the compiled aperture sampler.
    """
    calibration = dict(calibration or {})
    if ("retinal_layout" not in calibration
            and "receptor_layout" not in calibration):
        return luma_grid(rgb, n_el, n_az), None
    from domains.photon_eye import receptor_layout_from_calibration
    layout = receptor_layout_from_calibration(
        calibration, n_az, n_el,
        fov_h_deg=fov_h_deg, fov_v_deg=fov_v_deg)
    return (
        luma_layout(
            rgb, layout, n_el, n_az,
            fov_h_deg=fov_h_deg, fov_v_deg=fov_v_deg),
        layout,
    )


def scalar_grid(buf, n_el, n_az):
    """A single-channel buffer (depth / labels) -> (n_el, n_az) grid by area-mean."""
    return _block_mean(buf, n_el, n_az)


# ---------------------------------------------------------------- flux ---------
def photon_packets(luma, rng=None, gain=1.0):
    """Luminance grid -> per-receptor Poisson photon packets (mechanical I/O).

    The 8-bit luminance value IS the per-receptor photon-count mean (times
    `gain`, default 1.0 — no invented scale). With `rng` the count carries
    Poisson SHOT NOISE around that mean; without it the count is the noiseless
    mean (used to read the true field once)."""
    n_el, n_az = luma.shape
    out = []
    for r in range(n_el):
        for c in range(n_az):
            mean = float(luma[r, c]) * gain
            cnt = int(rng.poisson(mean)) if rng is not None else int(round(mean))
            if cnt > 0:
                out.append({"col": c, "row": r,
                            "wavelength_nm": ROD_NM, "count": cnt})
    return out


# ------------------------------------------------- event-native sensor (185000) -
# A dirty-index eye needs the SENSOR to say which cells changed. These three
# helpers are the mechanical, vectorized form of exactly that: a count grid, a
# change report, and packets for a SUBSET of cells. No decision, no agent state.
def photon_counts(luma, rng=None, gain=1.0):
    """Luminance grid -> per-receptor photon COUNT grid (the vectorized twin of
    `photon_packets`). With `rng` the counts carry Poisson SHOT NOISE — which
    means EVERY cell's count changes EVERY tick, so a photon-counting sensor
    reports the whole sheet as changed. Without `rng` this is the noiseless
    "read the true field" mode and a held frame is bit-repeatable."""
    mean = np.asarray(luma, dtype=np.float64) * gain
    if rng is not None:
        return rng.poisson(mean).astype(np.int64)
    return np.rint(mean).astype(np.int64)


def changed_cells(counts, last_counts, delta=0):
    """Flat indices whose photon count moved by MORE than `delta` from the last
    reported value. `delta=0` is the EXACT change report (bit-repeatable input ⇒
    no report); `delta>0` is a dead-band that SHEDS sub-δ movement — a semantic
    choice the caller makes and owns."""
    counts = np.asarray(counts)
    if last_counts is None:
        return np.arange(counts.size, dtype=np.int64)
    d = np.abs(counts.reshape(-1) - np.asarray(last_counts).reshape(-1))
    return np.flatnonzero(d > delta).astype(np.int64)


def packets_from_counts(counts, cells=None):
    """Count grid -> `{col,row,wavelength_nm,count}` packets, restricted to the
    given flat cell indices (the whole grid when `cells` is None). Building
    packets ONLY for the changed cells is what keeps the world side O(surprise)
    too."""
    counts = np.asarray(counts)
    n_el, n_az = counts.shape
    flat = counts.reshape(-1)
    idx = range(flat.size) if cells is None else cells
    out = []
    for f in idx:
        cnt = int(flat[f])
        if cnt > 0:
            r, c = divmod(int(f), n_az)
            out.append({"col": c, "row": r,
                        "wavelength_nm": ROD_NM, "count": cnt})
    return out


# ---------------------------------------------------------------- capture ------
def capture_e1m1(actions, skip=4, seed=181000, wad=DEFAULT_WAD,
                 doom_map="E1M1", res=(320, 240)):
    """Drive E1M1 headless with a fixed per-frame action; capture frame-aligned
    (rgb, depth_buffer, labels_buffer, labels-list). Pure world-adapter I/O.

    `actions` is a list of action names ("forward"/"turn_left"/"turn_right"/
    "attack"/"noop"); one frame is captured per entry, then the sim advances
    `skip` tics. Returns a list of frame dicts. Raises if VizDoom is unavailable."""
    import vizdoom as vzd
    g = vzd.DoomGame()
    g.set_doom_game_path(wad)
    g.set_doom_scenario_path(wad)
    g.set_doom_map(doom_map)
    g.set_screen_resolution(vzd.ScreenResolution.RES_320X240)
    g.set_screen_format(vzd.ScreenFormat.RGB24)
    g.set_depth_buffer_enabled(True)
    g.set_labels_buffer_enabled(True)
    g.set_render_hud(False)
    g.set_render_weapon(False)
    g.set_window_visible(False)
    g.set_mode(vzd.Mode.PLAYER)
    g.set_seed(int(seed))
    order = ["forward", "turn_left", "turn_right", "attack"]
    btns = {"forward": vzd.Button.MOVE_FORWARD, "turn_left": vzd.Button.TURN_LEFT,
            "turn_right": vzd.Button.TURN_RIGHT, "attack": vzd.Button.ATTACK}
    for name in order:
        g.add_available_button(btns[name])
    g.init()
    g.new_episode()

    def mkact(name):
        a = [0] * len(order)
        if name in order:
            a[order.index(name)] = 1
        return a

    frames = []
    for name in actions:
        if g.is_episode_finished() or g.is_player_dead():
            break
        st = g.get_state()
        if st is None:
            break
        frames.append({
            "rgb": np.array(st.screen_buffer, copy=True),
            "depth": np.array(st.depth_buffer, copy=True),
            "labels_buf": np.array(st.labels_buffer, copy=True),
            "labels": [{"object_id": int(l.object_id), "name": l.object_name,
                        "value": int(l.value)} for l in st.labels],
        })
        g.make_action(mkact(name), int(skip))
    g.close()
    return frames


def vizdoom_available(wad=DEFAULT_WAD):
    try:
        import vizdoom  # noqa: F401
    except Exception:
        return False
    return os.path.exists(wad)
