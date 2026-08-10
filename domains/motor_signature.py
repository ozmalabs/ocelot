"""Motor signature — reverse-engineer HOW a stroke was made, separate from WHAT it is.

Recognising a glyph ('that's a d') is the cheap reflex — apparatus-invariant, which is
exactly why almost anyone can do it. Reverse-engineering the *generating apparatus* (a
draggy mouse on a grubby mat, a shaky vs steady hand) is the deep layer few do: it reads
the motor artifact the effector leaves behind. You don't need it to recognise the glyph,
but it deepens understanding and disambiguates the hard cases.

The artifact is a compound latent — hand biomechanics x mouse quality x surface friction
x user care, all deformed from the resting hand-on-surface basis — with measurable,
physically-grounded signatures. Two kinds:

RECOGNITION-FREE (readable from the raw motor trace alone):
  * STICK-SLIP: under friction the hand stalls into direction changes and accelerates on
    the straight drags, so speed dips at the corners (needs the timestamps).
  * SQUARING: a curve is produced as near-straight drags hinged at a few corners — a
    polygon, so between-corner segments are straight.
  * JITTER: an unsteady hand / cheap setup leaves a high-frequency tremor floor.
  * PAUSES / LIMITS: the hand rests on a surface with a bounded reach; a stroke that
    exceeds it forces RE-ANCHORING (clutch the mouse, re-plant the wrist) — a pause, a
    stationary dwell in the timing. The pauses are the observable of the workspace limit.

CONFOUNDED PER GLYPH, IDENTIFIABLE PER SESSION (a shared latent, NOT per-glyph AbS):
  * DISTORTION: the anisotropic pivot workspace shears the shape from its basis. In a single
    glyph it is confounded by that glyph's own shape. But it is a SHARED constant of the
    circumstances: across a batch of different glyphs written the same way the intended shapes
    average toward isotropic, so the common directional bias that survives the pool IS the
    deformation (`establish_deformation`). Establish it once and every other glyph snaps to it
    — no per-glyph analysis-by-synthesis needed.

`render_stroke` synthesises a stroke from an ideal path under a known regime (ground
truth); `motor_signature` recovers the signatures. Mechanical feature extraction over ink
+ timing — a world adapter, no agent decisions.
"""
from __future__ import annotations

import numpy as np


def _turning(xy):
    d = np.diff(xy, axis=0)
    a = np.arctan2(d[:, 1], d[:, 0])
    dt = np.diff(a)
    return np.abs((dt + np.pi) % (2 * np.pi) - np.pi)


def _smooth(xy, k):
    if k <= 0 or len(xy) <= 2 * k + 1:
        return xy.copy()
    pad = np.pad(xy, ((k, k), (0, 0)), mode="edge")
    ker = np.ones(2 * k + 1) / (2 * k + 1)
    return np.c_[np.convolve(pad[:, 0], ker, "valid"), np.convolve(pad[:, 1], ker, "valid")]


def render_stroke(ideal, *, friction, care, rng, base_ms=10.0, anisotropy=0.0, reach=None):
    """Synthesise a mouse-drawn stroke from an ideal smooth path under a motor regime.

    friction in [0,1]: 0 = frictionless glide that follows the curve; 1 = heavy stick-slip,
      a few long straight drags hinged at sharp corners (a polygon), stalling at each corner.
    care     in [0,1]: 1 = steady hand / clean high-sensitivity setup (no jitter); 0 = shaky.
    anisotropy in [0,1): DISTORTION — the hand rests on a surface and deforms from that basis,
      so its workspace is anisotropic around the wrist/forearm pivot (motion easier along one
      axis). Scales the ideal anisotropically before rendering.
    reach (fraction of stroke size, or None): the bounded WORKSPACE per anchor. When the hand
      wanders more than `reach` from its current anchor it must RE-ANCHOR — a PAUSE (the cursor
      dwells while the mouse is clutched/repositioned) — then continues from the new anchor.

    Returns (xy, t) — path + millisecond timestamps (speed stalls at corners; dwells at pauses).
    """
    ideal = np.asarray(ideal, float)
    # DISTORT: deform from the resting basis by an anisotropic (pivot) scaling.
    if anisotropy:
        c = ideal.mean(0)
        ideal = c + (ideal - c) * np.array([1.0 + anisotropy, 1.0 - anisotropy])
    n = len(ideal)
    scale = np.linalg.norm(ideal.max(0) - ideal.min(0)) + 1e-9
    # POLYGONISE by friction: fewer knots (longer straight drags) as friction rises.
    K = max(3, int(round(n * (1 - friction) + 4 * friction)))     # friction 0 -> ~n; 1 -> ~4
    knots = ideal[np.linspace(0, n - 1, K).round().astype(int)]
    step = np.linalg.norm(np.diff(ideal, axis=0), axis=1).mean() + 1e-9
    pts = []
    for a, b in zip(knots[:-1], knots[1:]):
        steps = max(2, int(np.linalg.norm(b - a) / step))
        for s in range(steps):
            pts.append(a + (b - a) * s / steps)
    pts.append(knots[-1])
    pts = np.array(pts)
    # JITTER by (1-care): a high-frequency tremor floor.
    pts = pts + rng.normal(0, (1 - care) * 0.02 * scale, pts.shape)
    # RE-ANCHOR at the workspace LIMIT: when the hand leaves `reach` of its anchor, insert a
    # pause (a duplicated point that dwells) and re-anchor.
    xy, extra = [], []
    anchor = pts[0]
    for p in pts:
        xy.append(p)
        extra.append(0.0)
        if reach is not None and np.linalg.norm(p - anchor) > reach * scale:
            xy.append(p)               # cursor holds still while the mouse is repositioned
            extra.append(6.0 * base_ms)
            anchor = p
    xy = np.array(xy)
    extra = np.array(extra)
    # TIMESTAMPS: near-uniform speed on drags, STALL at corners (stick-slip), DWELL at pauses.
    turn = np.concatenate([[0.0], _turning(xy)])                  # per vertex (len = len(xy)-1)
    dwell = 1.0 + friction * 4.0 * (turn / (turn.max() + 1e-9))
    seg = np.linalg.norm(np.diff(xy, axis=0), axis=1)
    dt = (seg / (seg.mean() + 1e-9)) * dwell * base_ms + extra[1:]
    t = np.concatenate([[0.0], np.cumsum(dt)])
    return xy, t


def motor_signature(xy, t=None, *, n_corners=4):
    """Reverse-engineer the motor regime from a stroke. Returns a dict with the three raw
    signatures and (friction, care) estimates in [0,1]. `t` (ms timestamps) unlocks the
    stick-slip term; without it, friction rests on squaring alone."""
    xy = np.asarray(xy, float)
    n = len(xy)
    scale = np.linalg.norm(xy.max(0) - xy.min(0)) + 1e-9
    turn = _turning(xy)
    corners = np.argsort(turn)[-n_corners:] if len(turn) >= n_corners else np.arange(len(turn))

    # stick-slip: how much slower the hand is at the corners than overall (needs timing).
    stick = 0.0
    if t is not None:
        t = np.asarray(t, float)
        dt = np.diff(t)
        if np.all(dt > 0):
            speed = np.linalg.norm(np.diff(xy, axis=0), axis=1) / dt
            sp_v = (speed[:-1] + speed[1:]) / 2
            if len(sp_v) == len(turn) and sp_v.mean() > 0:
                stick = max(0.0, 1.0 - sp_v[corners].mean() / sp_v.mean())

    # squaring: between-corner drags are straight (chord/arclength -> 1 for a polygon).
    knots = np.sort(corners) + 1
    straight = []
    for s in np.split(np.arange(n), knots):
        if len(s) >= 4:
            p = xy[s]
            arclen = np.linalg.norm(np.diff(p, axis=0), axis=1).sum() + 1e-9
            straight.append(np.linalg.norm(p[-1] - p[0]) / arclen)
    straightness = float(np.mean(straight)) if straight else 1.0

    # jitter floor: high-frequency residual after light smoothing, as a fraction of size.
    jitter = float(np.linalg.norm(xy - _smooth(xy, 2), axis=1).mean() / scale)

    # PAUSES (re-anchor / clutch events): the cursor holds ~still (disp << typical) while a
    # long dwell passes (dt >> typical) — the hand hitting its reach limit and repositioning.
    # Distinct from a stick-slip corner (a brief slow, not a stationary dwell).
    pauses, pause_frac = 0, 0.0
    if t is not None and len(xy) > 3:
        dtv = np.diff(np.asarray(t, float))
        disp = np.linalg.norm(np.diff(xy, axis=0), axis=1)
        md = np.median(disp[disp > 1e-12]) if np.any(disp > 1e-12) else 1.0
        mt = np.median(dtv[dtv > 0]) if np.any(dtv > 0) else 1.0
        held = (disp < 0.25 * md) & (dtv > 3.0 * mt)          # stationary AND dwelling
        pauses = int(np.count_nonzero(held & ~np.r_[False, held[:-1]]))   # count runs
        total = (t[-1] - t[0]) if t[-1] > t[0] else 1.0
        pause_frac = float(dtv[held].sum() / total)

    # ANISOTROPY (distortion from the resting basis): the workspace around the wrist/forearm
    # pivot is directional, so the motion is deformed toward one axis. Aspect of the
    # displacement-vector covariance (0 = isotropic; ->1 = one preferred axis).
    anisotropy = 0.0
    v = np.diff(xy, axis=0)
    v = v[np.linalg.norm(v, axis=1) > 1e-9]
    if len(v) > 4:
        w = np.sort(np.linalg.eigvalsh(np.cov(v.T)))
        anisotropy = float(1.0 - w[0] / (w[1] + 1e-12))

    friction = float(np.clip(0.6 * min(stick / 0.3, 1.0)
                             + 0.4 * np.clip((straightness - 0.85) / 0.13, 0, 1), 0, 1))
    care = float(np.clip(1.0 - jitter / 0.02, 0, 1))
    return {"stick_slip": float(stick), "straightness": straightness, "jitter": jitter,
            "friction": friction, "care": care, "pauses": pauses,
            "pause_frac": pause_frac, "anisotropy": anisotropy}


def establish_deformation(strokes):
    """Recover the SHARED deformation (the anisotropic distortion from the resting basis)
    common to a batch of glyphs written in the SAME circumstances.

    It is confounded in any single glyph by that glyph's own shape — but IDENTIFIABLE across
    the batch, and NOT by per-glyph analysis-by-synthesis. Different characters point in
    different directions, so their intended motion averages toward isotropic; the systematic
    directional bias that survives the pool IS the apparatus deformation. Established once, it
    is a shared parameter every other glyph in the session snaps to.

    Returns {anisotropy, axis} — how squashed, and the easy (major) direction.
    """
    V = []
    for xy in strokes:
        xy = np.asarray(xy, float)
        v = np.diff(xy, axis=0)
        v = v[np.linalg.norm(v, axis=1) > 1e-9]
        if len(v) > 2:
            V.append(v / (np.linalg.norm(v, axis=1).mean() + 1e-9))   # scale-normalise per glyph
    if not V:
        return {"anisotropy": 0.0, "axis": [1.0, 0.0]}
    C = np.cov(np.vstack(V).T)
    w, vec = np.linalg.eigh(C)                                        # ascending eigenvalues
    return {"anisotropy": float(1.0 - w[0] / (w[1] + 1e-12)), "axis": vec[:, 1].tolist()}


def canonicalize(xy, deformation):
    """Undo a known shared deformation on a glyph — whiten the anisotropy along its axis so
    the glyph snaps back toward its canonical shape. Establishing the shared session
    deformation once (`establish_deformation`) and canonicalising every glyph raises
    recognition accuracy against canonical templates — the more so the stronger the
    deformation (a per-session nuisance transform, removed once for the whole batch)."""
    xy = np.asarray(xy, float)
    A = deformation["anisotropy"]
    ax = np.asarray(deformation["axis"], float)
    ax = ax / (np.linalg.norm(ax) + 1e-9)
    R = np.array([ax, [-ax[1], ax[0]]])
    c = xy.mean(0)
    p = (xy - c) @ R.T
    p[:, 0] *= np.sqrt(max(1e-3, 1.0 - A))               # whiten the amplified (major) axis
    return c + p @ R


def infer_environment(sig):
    """Abduce the generating ENVIRONMENT from a SINGLE glyph's motor signature. One artifact
    is enough to place a posterior over apparatus + surface + engagement + context — that is
    the payoff of reading the motor layer. Defeasible and probabilistic (one sample, not a
    proof), and it sharpens with more glyphs, but it is recoverable from one.
    """
    fr, ca, ss, ji = sig["friction"], sig["care"], sig["stick_slip"], sig["jitter"]
    surface = ("high-friction — worn or no mousepad" if fr > 0.35
               else "slick — a good mousepad" if fr < 0.15 else "an ordinary surface")
    device = ("a budget/sticky pointer, low sensitivity" if fr > 0.35 and ca < 0.6
              else "a decent mouse, well set up" if fr < 0.2 and ca > 0.8
              else "a consumer mouse")
    engagement = ("casual / hurried — didn't care about precision" if ca < 0.5
                  else "careful, precise" if ca > 0.85 else "ordinary care")
    context = ("crowd-work / casual home PC — cheap kit, low stakes" if fr > 0.3 and ca < 0.7
               else "deliberate work on a good setup" if fr < 0.2 and ca > 0.8
               else "ordinary desktop use")
    notes = []
    if fr > 0.35 and ss > 0.12:
        notes.append("stick-slip: dragging against friction, not gliding")
    if ji > 0.012:
        notes.append("shaky input: unsteady hand or a poor sensor")
    if sig.get("pauses", 0) > 0:
        notes.append("re-anchored mid-stroke: cramped mousing area / low sensitivity")
    return {"surface": surface, "device": device, "engagement": engagement,
            "context": context, "notes": notes}
