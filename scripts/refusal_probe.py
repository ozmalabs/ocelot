#!/usr/bin/env python3
"""EXPLORATORY PROBE -- field vocabulary of the decode/infer Term family.

NOT a confirmatory measurement.  No seeds are drawn: every stimulus here is
DETERMINISTIC.  Its only job is to discover, FROM THE ENGINE, what fields each
Term emits and what a refusal looks like, so the confirmatory runner can be
written against the engine rather than against a doc comment.

    PYTHONPATH=runners/dsl/python:. python3 scripts/refusal_probe.py
"""
from __future__ import annotations
import json

import numpy as np

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from substrate.boot_core import boot_core            # noqa: E402
from domains import reflective_faculty as rf          # noqa: E402
import substrate_rs as srs                            # noqa: E402

print(provenance_line())

DOT, H, W, ROW, BG, FG = 4, 24, 160, 8, 0, 255
DT = ["pred", "coord:r", "coord:c", "val"]
# The gen-mint gate's own fixture: an asymmetric L-tetromino.
BASE = [["cell", 0, 0, "red"], ["cell", 1, 0, "red"],
        ["cell", 2, 0, "red"], ["cell", 2, 1, "red"]]


def lin(M, base=BASE):
    rs = [c[1] for c in base]; cs = [c[2] for c in base]
    mr, mc = min(rs), min(cs); out = []
    for _, r, c, v in base:
        r0, c0 = r - mr, c - mc
        out.append(["cell", M[0] * r0 + M[1] * c0, M[2] * r0 + M[3] * c0, v])
    return out


def shift(d, base=BASE):
    return [["cell", r + d, c + d, v] for _, r, c, v in base]


def render(col):
    f = np.full((H, W), BG, dtype=np.uint8)
    if col is not None:
        f[ROW:ROW + DOT, col:col + DOT] = FG
    return f


def cells_fig(frame):
    vals, counts = np.unique(frame, return_counts=True)
    modal = int(vals[int(np.argmax(counts))])
    rs, cs = np.nonzero(frame != modal)
    return [["px", int(r), int(c), int(frame[r, c])] for r, c in zip(rs, cs)]


def seq(cols):
    return [([] if c is None else cells_fig(render(c))) for c in cols]


def boot():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    s.set_attr(ag, "gen_infer_enabled", 1.0)
    s.add_node("ShapeSignature",
               {"name": "px_base", "signature": json.dumps(cells_fig(render(0))),
                "kind": "faculty", "faculty": "px_base", "dim_types": DT})
    s.add_node("ShapeSignature",
               {"name": "base_L", "signature": json.dumps(BASE),
                "kind": "faculty", "faculty": "base_L", "dim_types": DT})
    return s, ag, native


def show(tag, val):
    if isinstance(val, (list, tuple)):
        try:
            d = {k: v for k, v in val}
            keep = {k: v for k, v in d.items()
                    if k in ("explained", "authored", "kind", "reason",
                             "checked", "identity", "base", "generator",
                             "confidence", "closes", "divisible", "offset",
                             "n_layers", "matrix", "transforms", "dims")}
            print(f"  {tag:22s} {keep}")
            return
        except Exception:
            pass
    print(f"  {tag:22s} {str(val)[:200]}")


s, ag, native = boot()

# ---- sequence-driven family -------------------------------------------------
CASES_SEQ = [
    ("ACCEPT const-vel", seq([0, 4, 8])),
    ("ACCEPT const-vel 8", seq([0, 8, 16])),
    ("REFUSE accel", seq([0, 4, 12])),
    ("REFUSE shuffle", seq([0, 37, 5])),
    ("REFUSE 2-frame", seq([0, 37])),
    ("GUARD empty", seq([None, None, None])),
]
for term in ("TimeInfer", "DepthInfer", "BlinkBridge", "GapAbduce"):
    print(f"\n=== {term} ===")
    for tag, frames in CASES_SEQ:
        t = srs.Term(term, sequence=srs.Lit(frames),
                     codebook_type="ShapeSignature", max_b=8, field="")
        show(tag, s.evaluate(t, {}))

# ---- goal-driven family -----------------------------------------------------
ROT90 = lin([0, -1, 1, 0])
SHEAR = lin([1, 0, 1, 1])
ALIEN = [["cell", 0, 0, "red"], ["cell", 0, 5, "red"],
         ["cell", 7, 1, "red"], ["cell", 3, 9, "red"]]
CASES_GOAL = [
    ("ACCEPT exact", BASE),
    ("ACCEPT shift+3", shift(3)),
    ("ACCEPT rot90", ROT90),
    ("ACCEPT shear", SHEAR),
    ("REFUSE alien", ALIEN),
]
for term, kw in (("ShapeDecode", dict(beam=4, max_steps=4, cand_k=4,
                                      wild="?", wild_objects=False)),
                 ("TransformDecode", dict(max_dims=4)),
                 ("DimInfer", dict(generator_type="DimensionGenerator",
                                   max_dims=4)),
                 ("GenInfer", dict(max_dims=4))):
    print(f"\n=== {term} ===")
    for tag, g in CASES_GOAL:
        try:
            t = srs.Term(term, goal=srs.Lit(g),
                         codebook_type="ShapeSignature", field="", **kw)
            show(tag, s.evaluate(t, {}))
        except Exception as e:
            print(f"  {tag:22s} RAISED {type(e).__name__}: {str(e)[:160]}")
