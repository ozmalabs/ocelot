"""glyph_motor_world — understand writing by knowing HOW TO WRITE (the motor forward model).

This is the MOTOR/pen complement to two existing pieces:
  - domains/writing_world.py renders glyphs from FONTS to pixels (reading by font-invariant
    vision — the printer's forward model);
  - scripts/cursive_analysis_by_synthesis.py reads cursive by inverting that FONT renderer.
    Its named residual is "the INDIVIDUAL HAND the forward model does not cover".

Here the forward model is the PEN, not the printer. A glyph is a MOTOR PROGRAM — an ordered set
of strokes composed from a tiny motor alphabet (line / arc). Knowing HOW TO WRITE a glyph means
holding that program; "writing" it SYNTHESISES a pen trajectory; recognising a mark is finding the
glyph whose written form best matches the observed SHAPE. That is the SAME graph-native analysis-
by-synthesis decision the speech recogniser uses — argmax over candidates of -DtwTo(observed,
synthesised) (domains/recognition_graph.predict_synth_term) — now over 2-D pen trajectories.

Why the motor view earns its keep: a parametric HAND (scale / slant / rotation / jitter) varies the
synthesis the way real hands vary, so the stroke TOPOLOGY (invariant) is what the match locks onto.
That is exactly the individual-hand variation a fixed font cannot produce — the residual the
font-based reader names, addressed by writing with a pen instead of stamping a typeface.

Per CLAUDE.md this file is ONLY a world adapter:
  - the glyph MOTOR PROGRAMS are GRAPH DATA (Glyph Concept --has_stroke--> Stroke nodes); the agent
    holds "how to write" in its graph. install_glyphs writes them in (mechanical).
  - SYNTHESIS (stroke program -> pen trajectory) is boundary I/O — sampling parametric curves read
    from the graph, exactly like piper TTS renders a word to audio for the speech AbS. No decisions.
  - the HAND (writing a mark with a different scale/slant/jitter) is world simulation.
  - the DECISION — which glyph a mark is — is NOT here; it is the graph Term predict_synth_term.

The motor alphabet is two primitives the whole repertoire composes from:
  line(x0,y0,x1,y1)          a straight stroke
  arc(cx,cy,r,a0deg,a1deg)   a circular arc (a0->a1, signed)
A glyph is an ordered list of (prim, args). Shared sub-strokes across glyphs (the bar of I in L and
T; the diagonals of V/X/A/N/Z; the crossbars of A/H) make recognition non-trivial.
"""
from __future__ import annotations

import math
from typing import Optional

import numpy as np

# ---- the motor repertoire: HOW TO WRITE each glyph (unit box, x right / y up) ----
# Each glyph is an ordered list of strokes; a stroke is (primitive, [args]).
GLYPHS: dict[str, list[tuple[str, list[float]]]] = {
    "I": [("line", [0.5, 0.0, 0.5, 1.0])],
    "L": [("line", [0.0, 1.0, 0.0, 0.0]), ("line", [0.0, 0.0, 1.0, 0.0])],
    "T": [("line", [0.0, 1.0, 1.0, 1.0]), ("line", [0.5, 1.0, 0.5, 0.0])],
    "V": [("line", [0.0, 1.0, 0.5, 0.0]), ("line", [0.5, 0.0, 1.0, 1.0])],
    "X": [("line", [0.0, 1.0, 1.0, 0.0]), ("line", [0.0, 0.0, 1.0, 1.0])],
    "Z": [("line", [0.0, 1.0, 1.0, 1.0]), ("line", [1.0, 1.0, 0.0, 0.0]),
          ("line", [0.0, 0.0, 1.0, 0.0])],
    "A": [("line", [0.0, 0.0, 0.5, 1.0]), ("line", [0.5, 1.0, 1.0, 0.0]),
          ("line", [0.25, 0.5, 0.75, 0.5])],
    "H": [("line", [0.0, 0.0, 0.0, 1.0]), ("line", [1.0, 0.0, 1.0, 1.0]),
          ("line", [0.0, 0.5, 1.0, 0.5])],
    "N": [("line", [0.0, 0.0, 0.0, 1.0]), ("line", [0.0, 1.0, 1.0, 0.0]),
          ("line", [1.0, 0.0, 1.0, 1.0])],
    "O": [("arc", [0.5, 0.5, 0.5, 90.0, 450.0])],
    "C": [("arc", [0.5, 0.5, 0.5, 300.0, 60.0])],
    "U": [("line", [0.0, 1.0, 0.0, 0.35]), ("arc", [0.5, 0.35, 0.5, 180.0, 360.0]),
          ("line", [1.0, 0.35, 1.0, 1.0])],
}

SYNTH_ATTR = "axs_synth_feat"      # the candidate glyph's written trajectory (synthesis)
MARK_ATTR = "axs_heard_feat"       # the observed mark's trajectory (perception)
WORD_ATTR = "is_word"              # marks a Concept as a recognition candidate (reused)
N_POINTS = 48                      # arc-length-resampled trajectory length


# --------------------------- parametric stroke sampling ---------------------------
def _sample_stroke(prim: str, args: list[float], k: int) -> np.ndarray:
    t = np.linspace(0.0, 1.0, k)
    if prim == "line":
        x0, y0, x1, y1 = args
        return np.stack([x0 + (x1 - x0) * t, y0 + (y1 - y0) * t], axis=1)
    if prim == "arc":
        cx, cy, r, a0, a1 = args
        a = math.radians(a0) + (math.radians(a1) - math.radians(a0)) * t
        return np.stack([cx + r * np.cos(a), cy + r * np.sin(a)], axis=1)
    raise ValueError(f"unknown stroke primitive {prim!r}")


def _resample_arclen(pts: np.ndarray, n: int) -> np.ndarray:
    """Resample a polyline to n points uniformly by arc length — so dense arcs and
    sparse lines contribute SHAPE, not sample-count, to the trajectory match."""
    d = np.sqrt(((np.diff(pts, axis=0)) ** 2).sum(axis=1))
    s = np.concatenate([[0.0], np.cumsum(d)])
    if s[-1] <= 1e-9:
        return np.repeat(pts[:1], n, axis=0)
    u = np.linspace(0.0, s[-1], n)
    return np.stack([np.interp(u, s, pts[:, 0]), np.interp(u, s, pts[:, 1])], axis=1)


def _normalize(pts: np.ndarray) -> np.ndarray:
    """Translation + scale invariance: centre to centroid, scale to unit RMS radius.
    Slant / rotation / jitter survive — that is the residual a 'hand' imposes."""
    c = pts - pts.mean(axis=0, keepdims=True)
    rms = float(np.sqrt((c ** 2).sum(axis=1).mean()))
    return c / rms if rms > 1e-9 else c


def to_trajectory(points, n: int = N_POINTS, *, denoise: bool = False,
                   denoise_kwargs: Optional[dict] = None) -> np.ndarray:
    """Raw pen points (x,y[,t...]) -> a normalized (n x 2) trajectory: take the xy columns,
    arc-length resample to n, centre+scale. The SAME conditioning the synthetic pen uses, so a
    REAL online-handwriting drawing (e.g. an Omniglot motor file) feeds the same AbS recogniser.

    RUN 34 (`denoise=False` default — every pre-existing caller/test is byte-identical):
    when `True`, the raw points are passed through `mouse_model.denoise_path` BEFORE arc-length
    resampling — the mouse observation model's inverse (latent-path reconstruction), so the
    trajectory the recogniser sees has the browser's pixel-lattice/event-rate quantization
    removed instead of resampled straight through. `denoise_kwargs` forwards optional overrides
    (e.g. a fixed `tol` for a reproducibility check) to `denoise_path`."""
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[0] < 2:
        return np.zeros((n, 2))
    xy = pts[:, :2]
    if denoise:
        from domains import mouse_model as mm
        xy = mm.denoise_path(xy, **(denoise_kwargs or {}))
    return _normalize(_resample_arclen(xy, n))


def to_trajectory_strokes(strokes, n: int = N_POINTS, *, denoise: bool = False,
                           denoise_kwargs: Optional[dict] = None) -> np.ndarray:
    """Like to_trajectory but conditions PER STROKE: each stroke gets a share of the n points
    proportional to its arc length and is resampled on its OWN length, then strokes are
    concatenated (the pen-up lift between strokes is ONE step, not an arc-length-consuming drawn
    segment). This removes the spurious inter-stroke jump geometry that hurts cross-writer matching
    when drawers vary stroke count/order. Normalised over the whole figure.

    RUN 34 (`denoise=False` default, byte-identical otherwise): when `True`, EACH stroke is
    passed through `mouse_model.denoise_path` (per-stroke — the browser's mouse-move sampling
    artifact is per-drag, not per-figure) before its own arc-length resampling."""
    segs = [np.asarray(st, dtype=float)[:, :2] for st in strokes
            if np.asarray(st).shape[0] >= 2]
    if denoise and segs:
        from domains import mouse_model as mm
        segs = [mm.denoise_path(s, **(denoise_kwargs or {})) for s in segs]
    if not segs:
        return np.zeros((n, 2))
    lens = np.array([float(np.sqrt((np.diff(s, axis=0) ** 2).sum(1)).sum()) for s in segs])
    if lens.sum() <= 1e-9:
        return _normalize(_resample_arclen(np.concatenate(segs), n))
    ks = np.maximum(2, np.round(n * lens / lens.sum()).astype(int))
    out = np.concatenate([_resample_arclen(s, k) for s, k in zip(segs, ks)], axis=0)
    return _normalize(out)


# ------------------------------ install: how-to-write -----------------------------
def install_glyphs(s, glyphs: Optional[dict] = None) -> dict[str, int]:
    """Write the motor programs into the graph as the agent's own knowledge:
    Glyph Concept --has_stroke--> Stroke{order, prim, args}. Marks each Concept
    is_word=1 so the recognition Term ranges over it. Returns {name: node}. Mechanical."""
    glyphs = glyphs or GLYPHS
    out: dict[str, int] = {}
    for name, strokes in glyphs.items():
        g = s.add_node("Concept", {"name": name, WORD_ATTR: 1.0, "is_glyph": 1.0})
        for i, (prim, args) in enumerate(strokes):
            st = s.add_node("Stroke", {"order": float(i), "prim": prim,
                                       "args": [float(a) for a in args]})
            s.add_edge_unchecked(g, "has_stroke", st)   # bare substrate has no Γ vocabulary
        out[name] = g
    return out


def _read_program(s, glyph_node) -> list[tuple[str, list[float]]]:
    """Read a glyph's ordered stroke program back OUT of the graph (mechanical query)."""
    strokes = []
    for st in s.neighbours(glyph_node, "has_stroke"):
        a = s.node(st)["attrs"]
        strokes.append((float(a.get("order", 0.0)), str(a.get("prim")),
                        [float(x) for x in a.get("args", [])]))
    strokes.sort(key=lambda t: t[0])
    return [(p, ar) for (_o, p, ar) in strokes]


# ------------------------------ synthesis: write it -------------------------------
def synthesize(s, glyph_node, n: int = N_POINTS, per_stroke: int = 24) -> np.ndarray:
    """Execute a glyph's stroke program -> a normalized pen trajectory (n x 2). This is
    the agent 'writing' the glyph — the forward model the AbS recogniser inverts. Reads
    the program from the graph; pure rendering (the pen for the writing world)."""
    program = _read_program(s, glyph_node)
    segs = [_sample_stroke(prim, args, per_stroke) for (prim, args) in program]
    pts = np.concatenate(segs, axis=0) if segs else np.zeros((n, 2))
    return _normalize(_resample_arclen(pts, n))


def attach_syntheses(s, glyph_nodes: dict[str, int], n: int = N_POINTS) -> None:
    """Write each candidate glyph's synthesized trajectory onto its Concept (axs_synth_feat),
    so the graph recogniser can DtwTo against it. Mechanical boundary write."""
    for _name, g in glyph_nodes.items():
        s.set_attr(g, SYNTH_ATTR, synthesize(s, g, n).tolist())


def rotate_traj(traj: np.ndarray, deg: float) -> np.ndarray:
    """Rotate a (normalized) trajectory by `deg` and re-normalize. Used to WRITE a candidate
    at a given orientation — the forward model with a rotation nuisance parameter."""
    th = math.radians(deg)
    R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    return _normalize(traj @ R.T)


def install_oriented_candidates(s, angles, glyphs: Optional[dict] = None,
                                n: int = N_POINTS) -> dict[str, int]:
    """Close the rotation residual by FOLDING rotation into the forward model: for each glyph
    the agent considers WRITING it at several orientations, so recognition can absorb the
    hand's rotation as a nuisance (the same move the speech AbS makes for voice). Each
    (glyph, angle) becomes a candidate Concept{name=glyph, is_word=1, orient=angle} carrying
    the rotated synthesis; predict_synth_term then ranges over all of them and the winner's
    NAME is the glyph (the orientation is the absorbed nuisance). The base Glyph nodes hold the
    motor programs but are NOT candidates (is_word=0). Returns {name: base_glyph_node}."""
    base = install_glyphs(s, glyphs)
    for nm, g in base.items():
        s.set_attr(g, WORD_ATTR, 0.0)                 # base holds the program, not a candidate
        canon = synthesize(s, g, n)
        for ang in angles:
            v = s.add_node("Concept", {"name": nm, WORD_ATTR: 1.0, "orient": float(ang),
                                       "is_glyph": 1.0})
            s.set_attr(v, SYNTH_ATTR, rotate_traj(canon, ang).tolist())
    return base


# ------------------------------ the hand: write a mark ----------------------------
def write_with_hand(traj: np.ndarray, rng: np.random.Generator, *,
                    slant: float = 0.25, rot_deg: float = 12.0,
                    scale: float = 0.2, jitter: float = 0.04) -> np.ndarray:
    """Simulate a DIFFERENT HAND writing the same shape: random slant (shear), rotation,
    anisotropic scale and per-point jitter. Translation/scale wash out under normalization;
    slant + rotation + jitter are the residual variation the recogniser must see through."""
    p = traj.copy()
    sh = rng.uniform(-slant, slant)
    p[:, 0] = p[:, 0] + sh * p[:, 1]                       # horizontal shear (slant)
    th = math.radians(rng.uniform(-rot_deg, rot_deg))
    R = np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    p = p @ R.T
    p = p * np.array([1.0 + rng.uniform(-scale, scale), 1.0 + rng.uniform(-scale, scale)])
    p = p + rng.normal(0.0, jitter, size=p.shape)
    return _normalize(p)


def attach_mark(s, traj: np.ndarray) -> int:
    """Add an observed Mark node carrying its trajectory (axs_heard_feat). Mechanical."""
    return s.add_node("Mark", {MARK_ATTR: traj.tolist()})


__all__ = ["GLYPHS", "SYNTH_ATTR", "MARK_ATTR", "WORD_ATTR", "N_POINTS",
           "install_glyphs", "synthesize", "attach_syntheses",
           "rotate_traj", "install_oriented_candidates",
           "write_with_hand", "attach_mark"]
