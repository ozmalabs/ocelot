"""spatiotemporal_feature — an EARNED TIMING-AWARE perceptual feature (earn-not-borrow).

THE LOOP-CLOSE: the writer-physics motor model (eae5048b) is correct, but the 2D scattering
feature is TIMING-BLIND (raster+pool discards timing/dynamics), so motor realism did NOT convert
to a 2D recognition lift. This feature can SEE what the right generator produces: it renders the
trajectory's TEMPORAL/DYNAMIC structure (velocity, direction-of-motion, time-order) into SPATIAL
CHANNELS, so the strong 2D scattering now sees timing AND keeps its spatial strength.

THE MOTION-ENCODED IMAGE (5 channels, each rasterised at the pen positions):
  ch0 ink           — the static shape (what timing-blind 2D sees)
  ch1 velocity-mag  — speed at each point (the two-thirds law lives here)
  ch2 heading-sin   — direction-of-motion (sin)
  ch3 heading-cos   — direction-of-motion (cos)
  ch4 time-phase    — stroke order / temporal index
Each channel is scattered (fixed wavelets, bb287bad) and concatenated → a high-dim feature that
is BOTH spatially strong (ch0) AND timing-aware (ch1-4). A pure raster shows only ch0 — so two
trajectories with the SAME shape but different speed/heading/order are IDENTICAL to the raster but
DISTINCT here (the discriminative control).

EARN-NOT-BORROW: fixed scattering wavelets (closed-form) + (optional) a from-scratch learned head
on held data. NO pretrained net, NO borrowed weights. numpy = raster/scatter adapter math (flagged);
no learned/borrowed weights in the feature itself.
"""
from __future__ import annotations
import numpy as _np                 # ADAPTER: motion-raster + scatter adapter math
import domains.omniglot_world as _ow
import domains.scattering_feature as _sf


def motion_raster(strokes, size=32):
    """Render a trace into 5 motion-encoded channels (ink, velocity, heading sin/cos, time-phase).
    Timing/dynamics become SPATIAL channels the 2D scattering can see."""
    parts = [_np.asarray(st, float) for st in strokes if len(st) >= 1]
    if not parts:
        return None
    full = _np.concatenate(parts, 0)
    if len(full) < 2:
        return None
    v = _np.diff(full, axis=0, prepend=full[:1])
    spd = _np.linalg.norm(v, axis=1)
    head = _np.arctan2(v[:, 1], v[:, 0])
    t = _np.linspace(0.0, 1.0, len(full))
    mn = full.min(0); mx = full.max(0); span = mx - mn; span[span == 0] = 1.0
    g = ((full - mn) / span) * (size - 3) + 1
    gi = g.astype(int)
    ch = _np.zeros((5, size, size))
    smax = spd.max() + 1e-6
    for i in range(len(gi)):
        x = int(_np.clip(gi[i, 0], 0, size - 1)); y = int(_np.clip(gi[i, 1], 0, size - 1))
        ch[0, y, x] = 1.0
        ch[1, y, x] = spd[i] / smax
        ch[2, y, x] = 0.5 + 0.5 * _np.sin(head[i])
        ch[3, y, x] = 0.5 + 0.5 * _np.cos(head[i])
        ch[4, y, x] = t[i]
    return ch


def spatiotemporal_scatter(strokes, size=32, J=3, n_theta=4, pool=4, channels=None):
    """The EARNED timing-aware feature = fixed-scattering of each motion channel, concatenated.
    channels=None -> all 5 (ink + timing); channels=[0] -> ink-only (== the timing-blind control)."""
    mr = motion_raster(strokes, size=size)
    if mr is None:
        return None
    chs = channels if channels is not None else list(range(mr.shape[0]))
    feats = []
    for c in chs:
        f = _sf.scatter_image(mr[c], J=J, n_theta=n_theta, pool=pool)
        if f is None:
            return None
        feats.append(f)
    return _np.concatenate(feats)


def st_feature(path, **kw):
    """Spatio-temporal feature of an Omniglot drawing (world-adapter convenience)."""
    return spatiotemporal_scatter(_ow.load_strokes(path), **kw)


# ---- timing-only feature (ink channel DROPPED) — for the discriminative control ----
def timing_only_scatter(path, **kw):
    """The timing/dynamics channels ONLY (velocity, heading, phase — NO ink). A pure-shape raster
    is blind to these; this isolates the timing information the loop-close adds."""
    return spatiotemporal_scatter(_ow.load_strokes(path), channels=[1, 2, 3, 4], **kw)
