#!/usr/bin/env python3
"""EXPLORATORY pilot 2 (NOT confirmatory) — exercise the new DepthInfer Term
through the depth_axis seed. Validates the mint/floor DECISION and the
downstream prediction before the prereg is committed.

    PYTHONPATH=runners/dsl/python:. python scripts/depth_pilot2.py
"""
from __future__ import annotations
import json

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from substrate.boot_core import boot_core           # noqa: E402
from domains import reflective_faculty as rf         # noqa: E402
from substrate.seed_loader import manifest_for       # noqa: E402

DT = ["pred", "coord:r", "coord:c", "val"]
RED = [["cell", 0, 0, "red"], ["cell", 1, 0, "red"], ["cell", 2, 1, "red"]]
BLU = [["cell", 0, 1, "blue"], ["cell", 1, 1, "blue"], ["cell", 2, 0, "blue"]]
GRN = [["cell", 3, 0, "green"], ["cell", 4, 1, "green"]]


def trans(dv, cs):
    return [["cell", r + dv[0], c + dv[1], v] for _, r, c, v in cs]


def scene(specs, n=6):
    """specs: list of (base, velocity). n frames merged per tick."""
    surfs = [list(b) for b, _ in specs]
    out = []
    for _ in range(n):
        frame = []
        for s in surfs:
            frame += [list(x) for x in s]
        out.append(frame)
        surfs = [trans(v, s) for s, (_, v) in zip(surfs, specs)]
    return out


def boot(enabled=True):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    native.load_seed_manifest(manifest_for("depth_axis"), ag)
    if enabled:
        s.set_attr(ag, "depth_infer_enabled", 1.0)
    s.add_node("ShapeSignature", {"name": "base", "signature": json.dumps(RED + BLU),
               "kind": "faculty", "faculty": "base", "dim_types": DT})
    return s, ag, native


def run(frames, enabled=True):
    s, ag, native = boot(enabled)
    o = s.add_node("Observation", {"frames": frames, "dim_types": DT,
                   "status": "depth_seq", "key": ["depth"]})
    s.add_edge(ag, "observed", o)
    native.run_rules()
    at = s.node(o)["attrs"]
    lds = []
    for n in s.nodes("LatentDimension"):
        a = s.node(n)["attrs"]
        if a.get("name") == "latent:depth":
            lds.append(dict(n_layers=a.get("n_layers"), velocities=a.get("velocities"),
                            ordering=a.get("ordering"), window=a.get("window")))
    return dict(status=at.get("status"), n_layers=at.get("n_layers"),
                predicted=at.get("predicted"), lds=lds)


print("ENGINE:", provenance_line())

print("\n=== FLAT (both at (2,0)) — expect depth_none, NO mint ===")
print(" ", run(scene([(RED, (2, 0)), (BLU, (2, 0))])))

print("\n=== MULTI-DEPTH (red (2,0), blue (1,0)) — expect depth_inferred, 2 layers ===")
r = run(scene([(RED, (2, 0)), (BLU, (1, 0))]))
print(" ", {k: v for k, v in r.items() if k != "predicted"})

print("\n=== 3-LAYER (red (3,0), blue (2,0), green (1,0)) — expect 3 layers ===")
r = run(scene([(RED, (3, 0)), (BLU, (2, 0)), (GRN, (1, 0))]))
print(" ", {k: v for k, v in r.items() if k != "predicted"})

print("\n=== DIFFERENT ORDERING (red (1,0), blue (3,0)) — blue now nearer ===")
r = run(scene([(RED, (1, 0)), (BLU, (3, 0))]))
print("  ordering near->far:", r["lds"][0]["ordering"] if r["lds"] else None)

print("\n=== DEDUP (red (3,0), blue (3,0), green (1,0)) — 3 surfaces, 2 velocities ===")
r = run(scene([(RED, (3, 0)), (BLU, (3, 0)), (GRN, (1, 0))]))
print(" ", {k: v for k, v in r.items() if k != "predicted"})

print("\n=== DOWNSTREAM: predict unseen view, compare to withheld frame K ===")
specs = [(RED, (2, 0)), (BLU, (1, 0))]
frames = scene(specs, 6)          # f0..f5 seen (K=6)
withheld = []
for b, v in specs:
    withheld += [list(x) for x in trans((v[0] * 6, v[1] * 6), b)]
withheld = sorted(tuple(x) for x in withheld)
r = run(frames)
pred = sorted(tuple(x) for x in (r["predicted"] or []))
print("  predicted==withheld view at K=6:", pred == withheld)

print("\n=== OFF (flag off) — inert ===")
print(" ", run(scene([(RED, (2, 0)), (BLU, (1, 0))]), enabled=False))
