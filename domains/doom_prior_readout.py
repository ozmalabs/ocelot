"""Mechanical I/O and readout for graph-native Doom predictive priors.

No cognitive decision lives here. This module stamps the external frame epoch
onto already-ingested ObsCells, reads observed/predicted graph state, rasterises
it, and sends RGB frames to ffmpeg. Room/corridor inference, wall projection,
confirmation, and correction are rules in seeds/doom_predictive_priors.json.
"""
from __future__ import annotations

import os
import subprocess

import numpy as np

from domains import doom_map_ingest as dm

PANEL_W, PANEL_H = 320, 240
PRIOR_RGB = (35, 205, 225)       # cyan: top-down confabulation
OBS_FREE_RGB = (245, 185, 65)    # amber hue: grounded free
OBS_WALL_RGB = (155, 92, 24)     # amber hue, darker: grounded wall
SURPRISE_RGB = (255, 245, 245)   # correction pulse / prediction error
UNKNOWN_RGB = (14, 18, 24)


def stamp_observation_epoch(wa, game, epoch):
    """Mechanical timestamp: attach the external frame index to current ObsCells."""
    for o in wa.inner.neighbours(game, "observed"):
        wa.inner.set_attr(o, "obs_epoch", float(epoch))


def _box_attrs(S, nodes):
    out = []
    for n in nodes:
        a = S.node(n)["attrs"]
        out.append({
            "lo": tuple(int(v) for v in a["lo"]),
            "hi": tuple(int(v) for v in a["hi"]),
            "epoch": int(a.get("epoch", 0)),
            "schema": a.get("schema"),
            "role": a.get("role"),
            "value": float(a.get("value", 1.0)),
        })
    return out


def read_snapshot(wa, game, epoch):
    """Read observed and confabulated maps plus graph-resident prediction errors."""
    S, I = wa.s, wa.inner
    observed = dm.read_map(wa, game)
    hypotheses = []
    for h in I.neighbours(game, "has_hypothesis"):
        a = S.node(h)["attrs"]
        if int(a.get("epoch", 0)) == int(epoch):
            hypotheses.append({
                "schema": a.get("schema"),
                "lo": tuple(int(v) for v in a["lo"]),
                "hi": tuple(int(v) for v in a["hi"]),
                "epoch": int(a["epoch"]),
            })
    predictions = [
        p for p in _box_attrs(S, I.neighbours(game, "has_prediction"))
        if p["epoch"] == int(epoch)
    ]
    outcomes = []
    for x in I.neighbours(game, "has_prediction_outcome"):
        a = S.node(x)["attrs"]
        outcomes.append({
            "result": a.get("result"),
            "pose": tuple(int(v) for v in a["pose"]),
            "prediction_epoch": int(a.get("prediction_epoch", 0)),
            "observation_epoch": int(a.get("observation_epoch", 0)),
            "schema": a.get("schema"),
        })
    residuals = []
    for r in I.neighbours(game, "has_map_residual"):
        a = S.node(r)["attrs"]
        residuals.append({
            "pose": tuple(int(v) for v in a["pose"]),
            "observation_epoch": int(a.get("observation_epoch", 0)),
            "schema": a.get("schema"),
        })
    return {
        "epoch": int(epoch),
        "cells": observed["cells"],
        "quanta": observed["quanta"],
        "hypotheses": hypotheses,
        "predictions": predictions,
        "outcomes": outcomes,
        "residuals": residuals,
    }


def snapshot_bounds(snapshots, pad=1):
    """Fixed movie aperture over every observed and predicted coordinate."""
    pts = []
    for s in snapshots:
        pts.extend(s["cells"].keys())
        for p in s["predictions"]:
            pts.extend((p["lo"], p["hi"]))
    if not pts:
        return (-1, 1, -1, 1)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad


def _prediction_cells(predictions):
    cells = set()
    for p in predictions:
        (x0, y0), (x1, y1) = p["lo"], p["hi"]
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                cells.add((x, y))
    return cells


def _fit(bounds):
    x0, x1, y0, y1 = bounds
    gw, gh = max(1, x1 - x0 + 1), max(1, y1 - y0 + 1)
    scale = max(1, min((PANEL_W - 20) // gw, (PANEL_H - 34) // gh))
    ox = PANEL_W // 2 - (gw * scale) // 2
    oy = 25 + (PANEL_H - 30) // 2 - (gh * scale) // 2
    return x0, y0, scale, ox, oy


def _paint_cell(img, pose, colour, geom, *, outline=False):
    x0, y0, scale, ox, oy = geom
    x, y = pose
    px, py = ox + (x - x0) * scale, oy + (y - y0) * scale
    if px + scale <= 0 or py + scale <= 0 or px >= PANEL_W or py >= PANEL_H:
        return
    if outline and scale >= 3:
        img[max(0, py):min(PANEL_H, py + scale), max(0, px):min(PANEL_W, px + scale)] = colour
        inset = max(1, scale // 4)
        img[max(0, py + inset):min(PANEL_H, py + scale - inset),
            max(0, px + inset):min(PANEL_W, px + scale - inset)] = UNKNOWN_RGB
    else:
        img[max(0, py):min(PANEL_H, py + scale),
            max(0, px):min(PANEL_W, px + scale)] = colour


def render_map_panel(snapshot, bounds):
    """Rasterise graph state: cyan prior, amber observation, white correction pulse."""
    img = np.full((PANEL_H, PANEL_W, 3), UNKNOWN_RGB, np.uint8)
    geom = _fit(bounds)
    observed = snapshot["cells"]
    for p in _prediction_cells(snapshot["predictions"]):
        if p not in observed:
            _paint_cell(img, p, PRIOR_RGB, geom)
    for p, value in observed.items():
        _paint_cell(img, p, OBS_WALL_RGB if value == 1.0 else OBS_FREE_RGB, geom)
    now = snapshot["epoch"]
    for r in snapshot["residuals"]:
        if r["observation_epoch"] == now:
            _paint_cell(img, r["pose"], SURPRISE_RGB, geom, outline=True)
    _label(img, "TOP-DOWN CYAN  |  OBSERVED AMBER", (5, 5))
    return img


def _label(img, text, xy):
    try:
        from PIL import Image, ImageDraw
        pil = Image.fromarray(img, "RGB")
        ImageDraw.Draw(pil).text(xy, text, fill=(235, 238, 242))
        img[:] = np.asarray(pil)
    except Exception:
        pass


def compose_frame(rgb, snapshot, bounds):
    """Return one fixed 640x240 two-panel RGB frame."""
    left = np.asarray(rgb, np.uint8)
    if left.shape[:2] != (PANEL_H, PANEL_W):
        from PIL import Image
        left = np.asarray(Image.fromarray(left, "RGB").resize((PANEL_W, PANEL_H)))
    else:
        left = left.copy()
    _label(left, "DOOM  |  BOTTOM-UP VIEW", (5, 5))
    return np.concatenate([left, render_map_panel(snapshot, bounds)], axis=1)


def encode_video(rgb_frames, snapshots, path, *, fps=10):
    """Encode offline-computed graph snapshots at a fixed watchable playback rate."""
    if len(rgb_frames) != len(snapshots):
        raise ValueError("RGB/snapshot frame count mismatch")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bounds = snapshot_bounds(snapshots)
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "640x240",
         "-r", str(fps), "-i", "-", "-an", "-c:v", "libx264",
         "-pix_fmt", "yuv420p", "-crf", "20", path],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        for rgb, snap in zip(rgb_frames, snapshots):
            frame = compose_frame(rgb, snap, bounds)
            proc.stdin.write(np.ascontiguousarray(frame).tobytes())
        proc.stdin.close()
        err = proc.stderr.read().decode("utf-8", "replace")
        code = proc.wait()
    except Exception:
        proc.kill()
        proc.wait()
        raise
    if code:
        raise RuntimeError(f"ffmpeg failed ({code}): {err}")
    return {
        "path": path, "width": 640, "height": 240, "fps": int(fps),
        "frames": len(snapshots), "bounds": list(bounds),
    }
