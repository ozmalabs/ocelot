#!/usr/bin/env python3
"""EXPLORATORY pilot 2 — CONSECUTIVE-PAIR transition ("carries frame(t)->frame(t+1)").
Decode each frame against the PREVIOUS frame (base-swap), not a fixed base.
Ordered orbit -> ONE transition generator carries every pair. Shuffled -> not.
Burned seed 0 for the shuffle. NOT confirmatory.
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


def lin(M, cs):
    rs = [c[1] for c in cs]; cc = [c[2] for c in cs]; mr, mc = min(rs), min(cc)
    return [["cell", M[0]*(r-mr)+M[1]*(c-mc), M[2]*(r-mr)+M[3]*(c-mc), v] for _, r, c, v in cs]


def boot():
    s, ag = boot_core(); nat = rf._native_eval2(s); rf._ensure_shape_decode_loop(s, nat, ag)
    s.set_attr(ag, "gen_infer_enabled", 1.0)
    return s, ag, nat


def lingens(s):
    return [tuple(s.node(n)["attrs"].get("matrix"))
            for n in s.nodes("DimensionGenerator") if s.node(n)["attrs"].get("kind") == "linear"]


def run_consecutive(members):
    """members[0] is f0; decode f1..fK each against the immediately-previous frame."""
    s, ag, nat = boot()
    prev_sig_node = None
    statuses = []
    ax0 = len(list(s.nodes("CapabilityAxis")))
    for i, f in enumerate(members):
        if i == 0:
            prev_sig_node = s.add_node("ShapeSignature", {"name": "prev", "signature": json.dumps(f),
                                       "kind": "faculty", "faculty": "prev", "dim_types": DT})
            continue
        ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
        o = s.add_node("Observation", {"signature": f, "key": ["probe"], "status": "decoded",
                       "residual": f, "decoded_epoch": ep, "dim_types": DT})
        s.add_edge(ag, "observed", o)
        nat.run_rules()
        statuses.append(s.node(o)["attrs"].get("status"))
        # swap base -> current frame becomes prev for next pair
        s.set_attr(prev_sig_node, "signature", json.dumps(f))
    quanta = len(list(s.nodes("CapabilityAxis"))) - ax0
    return statuses, quanta, lingens(s)


print("ENGINE:", provenance_line())
M = [1, 0, 1, 1]
orbit = []
cur = BASE
for _ in range(6):
    cur = lin(M, cur); orbit.append(cur)
# f0..f6: 7 frames (base + 6 steps)
seq = [BASE] + orbit

print("\n--- ORDERED shear orbit (consecutive-pair) ---")
st, q, lg = run_consecutive(seq)
print("  statuses:", st)
print("  quanta:", q, "lingens minted:", lg)

print("\n--- SHUFFLED (consecutive-pair) ---")
random.seed(0)
sh = seq[:]; random.shuffle(sh)
st, q, lg = run_consecutive(sh)
print("  statuses:", st)
print("  quanta:", q, "lingens minted:", lg)
