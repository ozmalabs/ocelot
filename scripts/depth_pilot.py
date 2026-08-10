#!/usr/bin/env python3
"""EXPLORATORY pilot (NOT confirmatory) — does a MULTI-DEPTH scene produce the
RESIDUAL that depth-from-motion needs, on the EXISTING TimeInfer machinery?

The premise of the depth rung: a scene with real (discrete) depth, translated
past a moving eye, produces a 2D image transformation that NO SINGLE flat
generator can explain (near layers sweep faster than far — motion parallax).
This pilot checks that premise BEFORE any Rust is written:

  - a FLAT scene (one integer velocity everywhere) must be EXPLAINED by a single
    TimeInfer generator (residual ZERO);
  - a MULTI-DEPTH scene (>=2 layers at different integer velocities, overlapping
    the SAME coordinate range so no position-gradient/shear can fake it) must be
    NOT explained by any single generator (the residual that IS the depth signal).

Deterministic. Runs on the current engine, no new Term:

    PYTHONPATH=runners/dsl/python:. python scripts/depth_pilot.py
"""
from __future__ import annotations
import json

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from substrate.boot_core import boot_core           # noqa: E402
from domains import reflective_faculty as rf         # noqa: E402
from substrate.seed_loader import manifest_for       # noqa: E402

DT = ["pred", "coord:r", "coord:c", "val"]
# Two surfaces sharing the SAME coordinate span (r in 0..2, c in 0..1), so a
# single linear/shear map cannot separate them by position — only their COLOUR
# (a non-coord slot) distinguishes them. This is the interleaved-depth case.
RED = [["cell", 0, 0, "red"], ["cell", 1, 0, "red"], ["cell", 2, 1, "red"]]
BLU = [["cell", 0, 1, "blue"], ["cell", 1, 1, "blue"], ["cell", 2, 0, "blue"]]


def trans(dv, cs):
    return [["cell", r + dv[0], c + dv[1], v] for _, r, c, v in cs]


def scene(vred, vblue, n=6):
    """n frames of RED translating at vred and BLU at vblue, merged per tick."""
    out = []
    r, b = RED, BLU
    for _ in range(n):
        out.append([list(x) for x in (r + b)])
        r = trans(vred, r)
        b = trans(vblue, b)
    return out


def boot():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("time_axis"), ag)
    s.set_attr(ag, "time_infer_enabled", 1.0)
    s.add_node("ShapeSignature", {"name": "base", "signature": json.dumps(RED + BLU),
               "kind": "faculty", "faculty": "base", "dim_types": DT})
    return s, ag, native


def time_explains(frames):
    """Does a SINGLE TimeInfer generator carry the whole scene?"""
    s, ag, native = boot()
    o = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                   "status": "motion_seq", "key": ["motion"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    at = s.node(o)["attrs"]
    lds = [a for n in s.nodes("LatentDimension")
           if (a := s.node(n)["attrs"]).get("name") == "latent:time"]
    return at.get("status"), bool(lds), [(l.get("generator_kind"), tuple(l.get("offset") or ())) for l in lds]


print("ENGINE:", provenance_line())

print("\n=== FLAT (both surfaces at velocity (2,0)) — expect SINGLE generator explains ===")
st, minted, lds = time_explains(scene((2, 0), (2, 0)))
print(f"  status={st}  time_minted={minted}  lds={lds}")
print(f"  premise A (flat is explained by ONE generator): {minted}")

print("\n=== MULTI-DEPTH (red (2,0), blue (1,0), same coord span) — expect NO single generator ===")
st, minted, lds = time_explains(scene((2, 0), (1, 0)))
print(f"  status={st}  time_minted={minted}  lds={lds}")
print(f"  premise B (multi-depth NOT explained by any single generator): {not minted}")

print("\n=== control: MULTI-COLOUR but SAME velocity (2,0) — must ALSO be single-generator ===")
st, minted, lds = time_explains(scene((2, 0), (2, 0)))
print(f"  status={st}  time_minted={minted}  -> two colours, one velocity => no residual: {minted}")
