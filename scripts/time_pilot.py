#!/usr/bin/env python3
"""EXPLORATORY pilot (NOT confirmatory) — is TIME inferable as the exponent of a
transition generator, and is a translation orbit in the current linear class?

Deterministic; the one RNG arm (shuffle) uses burned seed 0. Decides the
design question before any prereg / Rust change.

    PYTHONPATH=runners/dsl/python:. python scripts/time_pilot.py
"""
from __future__ import annotations
import json, random

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from substrate.boot_core import boot_core          # noqa: E402
from domains import reflective_faculty as rf        # noqa: E402

DT = ["pred", "coord:r", "coord:c", "val"]
BASE = [["cell", 0, 0, "red"], ["cell", 1, 0, "red"],
        ["cell", 2, 0, "red"], ["cell", 2, 1, "red"]]


def lin_step(M, cells):
    rs = [c[1] for c in cells]; cs = [c[2] for c in cells]
    mr, mc = min(rs), min(cs); out = []
    for _, r, c, v in cells:
        r0, c0 = r - mr, c - mc
        out.append(["cell", M[0]*r0 + M[1]*c0, M[2]*r0 + M[3]*c0, v])
    return out


def trans_step(dv, cells):
    dr, dc = dv
    return [["cell", r+dr, c+dc, v] for _, r, c, v in cells]


def boot(enabled):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    if enabled:
        s.set_attr(ag, "gen_infer_enabled", 1.0)
    s.add_node("ShapeSignature", {"name": "base_L", "signature": json.dumps(BASE),
               "kind": "faculty", "faculty": "base_L", "dim_types": DT})
    return s, ag, native


def observe(s, ag, goal):
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    obs = s.add_node("Observation", {"signature": goal, "key": ["probe"],
                     "status": "decoded", "residual": goal, "decoded_epoch": ep,
                     "dim_types": DT})
    s.add_edge(ag, "observed", obs)
    return obs


def lingens(s):
    return [tuple(s.node(n)["attrs"].get("matrix"))
            for n in s.nodes("DimensionGenerator")
            if s.node(n)["attrs"].get("kind") == "linear"]


def decode_one(enabled, goal):
    """Decode a single goal against the fixed held base; report full read-off."""
    s, ag, native = boot(enabled)
    ax0 = len(list(s.nodes("CapabilityAxis")))
    obs = observe(s, ag, goal)
    native.run_rules()
    at = s.node(obs)["attrs"]
    return dict(status=at.get("status"),
                quanta=len(list(s.nodes("CapabilityAxis"))) - ax0,
                lingens=lingens(s),
                k=at.get("dim_k"), gen=at.get("dim_generator"),
                latent=at.get("dim_latent_name"),
                keys=[kk for kk in at.keys() if kk.startswith("dim") or kk.startswith("transform")])


def orbit_readoff(enabled, members):
    """Present an ORDERED orbit; read status+k off each member in turn."""
    s, ag, native = boot(enabled)
    ax0 = len(list(s.nodes("CapabilityAxis")))
    out = []
    for g in members:
        obs = observe(s, ag, g)
        native.run_rules()
        at = s.node(obs)["attrs"]
        out.append((at.get("status"), at.get("dim_k"), at.get("transform_delta")))
    return out, len(list(s.nodes("CapabilityAxis"))) - ax0, lingens(s)


print("ENGINE:", provenance_line())

print("\n=== Q1: pure TRANSLATION orbit, velocity (2,0) — member1 = base+(2,0) ===")
t1 = trans_step((2, 0), BASE)
print("  member1:", t1)
print("  ON :", decode_one(True, t1))
print("  OFF:", decode_one(False, t1))

print("\n=== Q2: TRANSLATION velocity (1,1) — does held `modular` cover it? ===")
t11 = trans_step((1, 1), BASE)
print("  ON :", decode_one(True, t11))

print("\n=== Q3: ROTATE-per-tick orbit (rotation90^k) — held generator, k=time ===")
rot = [BASE]
for _ in range(3):
    rot.append(lin_step([0, -1, 1, 0], rot[-1]))  # rotation90 as linear (r,c)->(-c,r)
for k, m in enumerate(rot):
    print(f"  k={k}:", decode_one(True, m))

print("\n=== Q4: SCALE-per-tick orbit (scale2^k) — held generator ===")
sc = [BASE]
for _ in range(2):
    sc.append(lin_step([2, 0, 0, 2], sc[-1]))
for k, m in enumerate(sc):
    print(f"  k={k}:", decode_one(True, m))

print("\n=== Q5: SHEAR-per-tick orbit (shearA=[1,0,1,1])^k — GenInfer mints, then powers ===")
M = [1, 0, 1, 1]
sh = []
cur = BASE
for _ in range(4):
    cur = lin_step(M, cur); sh.append(cur)
ro, q, lg = orbit_readoff(True, sh)
for k, r in enumerate(ro, 1):
    print(f"  presented#{k}: status={r[0]} k={r[1]}")
print("  quanta:", q, "lingens:", lg)

print("\n=== Q6: ORDERED vs SHUFFLED shear orbit — k-consecutiveness (the control) ===")
random.seed(0)
sh6 = []
cur = BASE
for _ in range(6):
    cur = lin_step(M, cur); sh6.append(cur)
ro_ord, q_ord, lg_ord = orbit_readoff(True, sh6)
print("  ORDERED  k-seq:", [r[1] for r in ro_ord], "statuses:", [r[0] for r in ro_ord])
shuf = sh6[:]
random.shuffle(shuf)
ro_shf, q_shf, lg_shf = orbit_readoff(True, shuf)
print("  SHUFFLED k-seq:", [r[1] for r in ro_shf], "statuses:", [r[0] for r in ro_shf])
print("  ordered quanta:", q_ord, "shuffled quanta:", q_shf)
