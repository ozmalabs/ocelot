"""symbol_motor_world — THE TRANSFER-GATE domain (run-24, f492c1b1's Branch-C verdict): a
NON-HANDWRITING drawn-shape world, built the SAME way `domains/glyph_motor_world.py` builds
letters — motor programs composed from the SAME two primitives (`line`/`arc`) that module's own
`_sample_stroke` already supports. No new primitive, no new Rust, no new decode/verdict code.

Per CLAUDE.md this file is ONLY a world adapter / data builder (mirrors `glyph_motor_world.py`'s
own role exactly): the 20 symbol classes are WORLD DATA (an ordered list of (prim, args) strokes,
unit-box convention, x right / y up — the identical convention `glyph_motor_world.GLYPHS` uses);
`write_hand_instance` is world SIMULATION (a different "hand" drawing the same shape, reusing
`glyph_motor_world.write_with_hand`'s own nuisance model VERBATIM — no new transform math is
written here, the whole hand array is concatenated, transformed by the existing function, and
re-split back into its original per-stroke boundaries); `write_motor_file`/`build_symbol_corpus`
are mechanical file I/O, writing the EXACT Omniglot online-handwriting motor-file text format
(`domains/omniglot_world.py`'s own documented format: START / "x,y,t" lines / BREAK between
strokes) so the UNCHANGED `omniglot_world.load_strokes`/`trajectory` parsers — and everything built
on them (`domains.abs_read.stage_parse_char`, `scripts.jabberwock_omniglot_dynamic_quantization.
decode_char_signature`) — read a synthetic symbol drawing exactly as they read a real Omniglot
character drawing, with ZERO code path divergence. This is what makes the transfer gate
(`scripts/jabberwock_transfer_gate.py`) a genuine "same stack, zero adaptation" test rather than a
parallel implementation: the SAME parser, the SAME verdict Term, a DIFFERENT drawn-shape domain.

The 20 classes (arrows, boxed/plain polygons, chevrons, a pentagram, an asterisk, circles/targets,
a tick-marked spiral, two circuit-like glyphs, a key) are deliberately NOT alphabet characters —
this is the domain-generality claim the creator's own framing names: "when we are done it won't be
a handwriting recogniser, it will be a generic and flexible drawn shape reproducer."
"""
from __future__ import annotations

import math
import os
from typing import Optional

import numpy as np

from domains import glyph_motor_world as gm

# --------------------------------------------------------------------------------------------- #
# THE MOTOR REPERTOIRE — 20 classes, each an ordered list of (prim, args) strokes in the unit box,
# using ONLY "line"/"arc" (`glyph_motor_world._sample_stroke`'s existing, unchanged primitive set).
# --------------------------------------------------------------------------------------------- #
_BOX_STROKES: list[tuple[str, list[float]]] = [
    ("line", [0.1, 0.1, 0.9, 0.1]), ("line", [0.9, 0.1, 0.9, 0.9]),
    ("line", [0.9, 0.9, 0.1, 0.9]), ("line", [0.1, 0.9, 0.1, 0.1]),
]

_STAR5_R = 0.42
_STAR5_PTS = [(0.5 + _STAR5_R * math.cos(math.radians(90 + 72 * k)),
               0.5 + _STAR5_R * math.sin(math.radians(90 + 72 * k))) for k in range(5)]
_STAR5_STROKES: list[tuple[str, list[float]]] = [
    ("line", [*_STAR5_PTS[i], *_STAR5_PTS[(i + 2) % 5]]) for i in range(5)]

SYMBOLS: dict[str, list[tuple[str, list[float]]]] = {
    "ARROW_R": [("line", [0.05, 0.5, 0.85, 0.5]), ("line", [0.85, 0.5, 0.55, 0.8]),
                ("line", [0.85, 0.5, 0.55, 0.2])],
    "ARROW_L": [("line", [0.95, 0.5, 0.15, 0.5]), ("line", [0.15, 0.5, 0.45, 0.8]),
                ("line", [0.15, 0.5, 0.45, 0.2])],
    "ARROW_U": [("line", [0.5, 0.05, 0.5, 0.85]), ("line", [0.5, 0.85, 0.2, 0.55]),
                ("line", [0.5, 0.85, 0.8, 0.55])],
    "ARROW_D": [("line", [0.5, 0.95, 0.5, 0.15]), ("line", [0.5, 0.15, 0.2, 0.45]),
                ("line", [0.5, 0.15, 0.8, 0.45])],
    "PLUS_SIGN": [("line", [0.1, 0.5, 0.9, 0.5]), ("line", [0.5, 0.1, 0.5, 0.9])],
    "BOX": list(_BOX_STROKES),
    "BOXED_CROSS": list(_BOX_STROKES) + [("line", [0.1, 0.1, 0.9, 0.9]),
                                          ("line", [0.1, 0.9, 0.9, 0.1])],
    "TRIANGLE": [("line", [0.1, 0.1, 0.5, 0.9]), ("line", [0.5, 0.9, 0.9, 0.1]),
                 ("line", [0.9, 0.1, 0.1, 0.1])],
    "DIAMOND": [("line", [0.5, 0.9, 0.9, 0.5]), ("line", [0.9, 0.5, 0.5, 0.1]),
                ("line", [0.5, 0.1, 0.1, 0.5]), ("line", [0.1, 0.5, 0.5, 0.9])],
    "HOURGLASS": [("line", [0.1, 0.1, 0.9, 0.1]), ("line", [0.9, 0.1, 0.1, 0.9]),
                  ("line", [0.1, 0.9, 0.9, 0.9]), ("line", [0.9, 0.9, 0.1, 0.1])],
    "CHEVRON_UP": [("line", [0.15, 0.25, 0.5, 0.85]), ("line", [0.5, 0.85, 0.85, 0.25])],
    "CHEVRON_DOWN": [("line", [0.15, 0.75, 0.5, 0.15]), ("line", [0.5, 0.15, 0.85, 0.75])],
    "STAR5": list(_STAR5_STROKES),
    "ASTERISK": [("line", [0.1, 0.5, 0.9, 0.5]), ("line", [0.5, 0.1, 0.5, 0.9]),
                 ("line", [0.18, 0.18, 0.82, 0.82]), ("line", [0.18, 0.82, 0.82, 0.18])],
    "CIRCLE": [("arc", [0.5, 0.5, 0.4, 0.0, 360.0])],
    "TARGET": [("arc", [0.5, 0.5, 0.4, 0.0, 360.0]), ("arc", [0.5, 0.5, 0.2, 0.0, 360.0])],
    "SPIRAL_TICK": [("arc", [0.5, 0.5, 0.10, 0.0, 180.0]), ("arc", [0.5, 0.5, 0.22, 180.0, 360.0]),
                     ("arc", [0.5, 0.5, 0.34, 360.0, 540.0]), ("line", [0.5, 0.84, 0.62, 0.90])],
    "CIRCUIT_AND": [("line", [0.10, 0.15, 0.10, 0.85]), ("line", [0.10, 0.85, 0.45, 0.85]),
                     ("arc", [0.45, 0.5, 0.35, -90.0, 90.0]), ("line", [0.45, 0.15, 0.10, 0.15]),
                     ("line", [0.80, 0.5, 0.95, 0.5])],
    "CIRCUIT_RESISTOR": [("line", [0.05, 0.5, 0.25, 0.5]), ("line", [0.25, 0.5, 0.375, 0.8]),
                          ("line", [0.375, 0.8, 0.5, 0.2]), ("line", [0.5, 0.2, 0.625, 0.8]),
                          ("line", [0.625, 0.8, 0.75, 0.5]), ("line", [0.75, 0.5, 0.95, 0.5])],
    "KEY": [("arc", [0.28, 0.5, 0.18, 0.0, 360.0]), ("line", [0.46, 0.5, 0.92, 0.5]),
            ("line", [0.80, 0.5, 0.80, 0.32])],
}
assert len(SYMBOLS) == 20, f"expected exactly 20 symbol classes, got {len(SYMBOLS)}"

N_PER_STROKE = 24     # matches glyph_motor_world.synthesize's own per_stroke default


# --------------------------------------------------------------------------------------------- #
# SYNTHESIS — pure geometry, reuses glyph_motor_world._sample_stroke verbatim (no new primitive).
# --------------------------------------------------------------------------------------------- #
def sample_symbol_strokes(name: str, per_stroke: int = N_PER_STROKE) -> list[np.ndarray]:
    """A symbol's canonical (unit-box) per-stroke point arrays — "writing" its motor program,
    exactly `glyph_motor_world.synthesize` does for a GLYPHS entry, but keeping strokes SEPARATE
    (not concatenated+resampled) so pen lifts stay real BREAKs in the motor file."""
    program = SYMBOLS[name]
    return [gm._sample_stroke(prim, args, per_stroke) for prim, args in program]


# --------------------------------------------------------------------------------------------- #
# THE HAND — reuses glyph_motor_world.write_with_hand's OWN transform VERBATIM (concatenate every
# stroke, let the existing function shear/rotate/scale/jitter/renormalize the whole figure exactly
# as it already does for a GLYPHS letter, then re-split at the original per-stroke boundaries so
# strokes stay separate motor-file segments). No new nuisance math anywhere in this module.
# --------------------------------------------------------------------------------------------- #
def write_hand_instance(name: str, rng: np.random.Generator, *, per_stroke: int = N_PER_STROKE,
                         scale_px: float = 300.0, slant: float = 0.25, rot_deg: float = 12.0,
                         scale: float = 0.2, jitter: float = 0.04) -> list[np.ndarray]:
    """ONE simulated hand drawing symbol `name` — a list of per-stroke (per_stroke x 2) point
    arrays in pixel-like coordinates (`scale_px`, cosmetic only: everything downstream
    re-normalizes). `rng` decides the hand (deterministic given a seed) — the drawer analog."""
    canonical = sample_symbol_strokes(name, per_stroke=per_stroke)
    lens = [len(s) for s in canonical]
    concat = np.concatenate(canonical, axis=0)
    varied = gm.write_with_hand(concat, rng, slant=slant, rot_deg=rot_deg, scale=scale,
                                 jitter=jitter)
    out, i = [], 0
    for length in lens:
        out.append(varied[i:i + length] * scale_px)
        i += length
    return out


# --------------------------------------------------------------------------------------------- #
# MOTOR-FILE I/O — the EXACT Omniglot format `domains/omniglot_world.py` parses (its own
# docstring: "START / x,y,t / BREAK"). Mechanical world-adapter I/O only.
# --------------------------------------------------------------------------------------------- #
def write_motor_file(path: str, strokes: list) -> None:
    lines = ["START"]
    for stroke in strokes:
        pts = np.asarray(stroke, dtype=float).reshape(-1, 2)
        for t, (x, y) in enumerate(pts):
            lines.append(f"{x:.4f},{y:.4f},{t}")
        lines.append("BREAK")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")


def build_symbol_corpus(root: str, *, n_hands: int = 20, seed: int = 20260724,
                         per_stroke: int = N_PER_STROKE,
                         scale_px: float = 300.0) -> dict[str, dict[int, str]]:
    """Write the whole hermetic corpus to disk under `root`: `<root>/<CLASS>/<CLASS>_<hand:02d>.
    txt`, `n_hands` simulated hands per class, deterministic (`seed`). Returns
    `{class_name: {hand_idx: path}}` — the SAME shape `omniglot_world.drawings`-derived path
    tables already have (a plain per-drawer file map), so gate scripts index it identically."""
    paths: dict[str, dict[int, str]] = {}
    for ci, name in enumerate(sorted(SYMBOLS)):
        paths[name] = {}
        for h in range(n_hands):
            rng = np.random.default_rng(seed + ci * 10007 + h)
            strokes = write_hand_instance(name, rng, per_stroke=per_stroke, scale_px=scale_px)
            p = os.path.join(root, name, f"{name}_{h:02d}.txt")
            write_motor_file(p, strokes)
            paths[name][h] = p
    return paths


__all__ = ["SYMBOLS", "N_PER_STROKE", "sample_symbol_strokes", "write_hand_instance",
           "write_motor_file", "build_symbol_corpus"]
