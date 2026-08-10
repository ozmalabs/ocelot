"""face_inversion_lib — stimulus builders + sd-loop driver for the FACE-INVERSION /
THATCHER validation gate (VISION_FACE_INVERSION_PREREG.md).

Mechanical I/O + geometry ONLY (CLAUDE.md / PROTOCOL §0): this file BUILDS cell-set
signatures (configural arrangements of parts, and part-based objects) and DRIVES the
existing shape-decode loop (seeds/shape_decode_loop.json over runners/dsl/src/shape_decode
.rs). It makes NO recognition decision -- status / covered_by are read straight off the
Observation after run_rules(). Same driver shape as scripts/identity_untangling_measure.py.

Two representations, both plain cell-sets fed to the SAME sd loop:
  * CONFIGURAL  -- identity carried by the ARRANGEMENT: the SAME asymmetric part atom
    placed at several anchor positions. Whose "face" it is = where the parts are.
  * PART-BASED  -- identity carried by WHICH atoms are present, at a FIXED arrangement:
    distinct atom shapes at the same anchors. Whose object it is = which parts.

The point of the gate is to MEASURE, on the real sd loop, whether inversion (a uniform
180-degree = rotation90 k=2, and a LOCAL part flip = Thatcher) disrupts the arrangement
code more than the part code. No new Rust; no new seed rule.
"""
from __future__ import annotations
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
sys.path.insert(0, _ROOT)

from domains.engine_provenance import engine_preamble  # noqa: E402
engine_preamble()

import json  # noqa: E402
from substrate.boot_core import boot_core  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402

DT = ["pred", "coord:r", "coord:c", "val"]

# ---- cell-set geometry (integer, in-frame; PROTOCOL frame/continuum invariant) -------

def norm(cells):
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def sig(cells):
    return [["cell", r, c, "red"] for r, c in norm(cells)]


def rot180(cells):
    """Point inversion about the shape's own bbox (= rotation90 twice)."""
    n = norm(cells)
    mr = max(r for r, _ in n)
    mc = max(c for _, c in n)
    return norm([(mr - r, mc - c) for r, c in n])


def translate(cells, dr, dc):
    return [(r + dr, c + dc) for r, c in cells]


# ---- part atoms (asymmetric under 180 so orientation is a real feature) --------------
# L-tromino: rot180 gives a DIFFERENT cell set relative to bbox -> orientation matters.
ATOM_L = [(0, 0), (0, 1), (1, 0)]
ATOM_J = [(0, 0), (0, 1), (1, 1)]   # a distinct tromino (mirror corner)
ATOM_S = [(0, 1), (1, 0), (1, 1)]   # a third distinct tromino
ATOM_T = [(0, 0), (0, 1), (0, 2)]   # a bar (distinct shape/type)


def place(atom, ar, ac):
    return [(ar + dr, ac + dc) for dr, dc in atom]


def local_flip(atom):
    """Rotate an atom 180 about its OWN bbox (a Thatcher local part inversion)."""
    return rot180(atom)


# ---- configural arrangements: SAME atom at anchors; identity = the anchor pattern -----
# Anchors are well separated so parts never overlap and each part is a recoverable blob.
def configural(anchors, atom=ATOM_L, flip_idx=None):
    """Build a configural face: `atom` placed at each (ar,ac) in `anchors`.
    If flip_idx is not None, that ONE part is locally 180-flipped in place (Thatcher)."""
    cells = []
    for i, (ar, ac) in enumerate(anchors):
        a = local_flip(atom) if (flip_idx is not None and i == flip_idx) else atom
        cells += place(a, ar, ac)
    return norm(cells)


# ---- part-based objects: DISTINCT atoms at a FIXED arrangement; identity = the atoms ---
def part_based(atoms, anchors, flip_idx=None):
    cells = []
    for i, (atom, (ar, ac)) in enumerate(zip(atoms, anchors)):
        a = local_flip(atom) if (flip_idx is not None and i == flip_idx) else atom
        cells += place(a, ar, ac)
    return norm(cells)


# ---- the sd-loop driver (identical shape to identity_untangling_measure.identify) ------
def _boot(codebook, gen_infer=False):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    for n in list(s.nodes("ShapeSignature")):   # isolate the codebook under test
        s.remove_node(n)
    if gen_infer:
        s.set_attr(ag, "gen_infer_enabled", 1.0)
    for nm, cells in codebook.items():
        s.add_node("ShapeSignature", {"name": nm, "signature": json.dumps(sig(cells)),
                                      "kind": "faculty", "faculty": nm, "dim_types": DT})
    return s, ag, native


def identify(codebook, view_cells, gen_infer=False):
    """Present a view against a held codebook; return (status, covered_by_or_None).

    The verdict is READ, never decided here: status in {recognized (literal, frame-
    EXACT), recognized_transformed (via a held generator -- frame-INVARIANT), else
    None (residual survives -> not recognized)}; covered_by = the identity a transform
    maps FROM.
    """
    s, ag, native = _boot(codebook, gen_infer)
    goal = sig(view_cells)
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    obs = s.add_node("Observation", {"signature": goal, "key": ["probe"],
                     "status": "decoded", "residual": goal, "decoded_epoch": ep,
                     "dim_types": DT})
    s.add_edge(ag, "observed", obs)
    native.run_rules()
    at = s.node(obs)["attrs"]
    st = at.get("status")
    cov = at.get("covered_by") if st in ("recognized", "recognized_transformed") else None
    return st, cov
