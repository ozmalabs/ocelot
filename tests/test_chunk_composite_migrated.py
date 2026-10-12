"""CHUNKING — a recognised composite becomes a primitive (seeds/shape_decode_loop
v1.11.0 `sd_chunk_composite` + `DimensionGenerator{kind:"composite"}` in
shape_decode.rs; RECURSIVE_SELF_IMPROVEMENT_PLAN_20261006.md WP5).

DimInfer's own search is length <= 2 and stays that way. What changes is the
codebook: a recognised length-2 composition is minted as one generator, so the
next observation one step deeper is again length 2. Pinned:
  * flag absent: nothing is chunked and a length-3 target mints a quantum;
  * flag on: L2 -> chunk; L3 recognised through the chunk; the L3 chunk is a
    chunk OF a chunk; L4 recognised;
  * a chunk minted on one base transfers to a DIFFERENT base;
  * controls: a length-1 observation and a scrambled observation chunk nothing.
"""
from __future__ import annotations

import json

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402

DT = ["pred", "coord:r", "coord:c", "val"]
BASE = [["cell", 0, 0, "red"], ["cell", 1, 0, "red"], ["cell", 2, 0, "red"],
        ["cell", 2, 1, "red"], ["cell", 0, 1, "blue"]]
OTHER = [["cell", 0, 0, "red"], ["cell", 0, 1, "red"], ["cell", 0, 2, "red"],
         ["cell", 1, 0, "blue"], ["cell", 2, 2, "red"]]


def norm(c):
    mr = min(x[1] for x in c); mc = min(x[2] for x in c)
    return [[p, r - mr, cc - mc, v] for p, r, cc, v in c]


def rot(c): return norm([[p, cc, -r, v] for p, r, cc, v in norm(c)])
def refl(c): return norm([[p, -r, cc, v] for p, r, cc, v in norm(c)])
def scale(c): return [[p, 2 * r, 2 * cc, v] for p, r, cc, v in norm(c)]


def boot(chunk, base=BASE, name="base"):
    s, ag = boot_core()
    n = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, n, ag)
    if chunk:
        s.set_attr(ag, "gen_chunk_enabled", 1)
    s.add_node("ShapeSignature", {"name": name, "signature": json.dumps(base), "kind": "faculty",
                                  "faculty": name, "dim_types": DT})
    return s, ag, n


def observe(s, ag, n, goal, key):
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    o = s.add_node("Observation", {"signature": goal, "key": [key], "status": "decoded",
                                   "residual": goal, "decoded_epoch": ep, "dim_types": DT})
    s.add_edge(ag, "observed", o)
    n.run_rules()
    return s.node(o)["attrs"].get("status")


def chunks(s):
    return [s.node(g)["attrs"] for g in s.nodes("DimensionGenerator")
            if s.node(g)["attrs"].get("kind") == "composite"]


def test_flag_absent_nothing_chunks_and_depth3_mints():
    s, ag, n = boot(False)
    assert observe(s, ag, n, scale(rot(BASE)), "l2") == "recognized_transformed"
    assert chunks(s) == []
    assert observe(s, ag, n, refl(scale(rot(BASE))), "l3") == "minted"


def test_chunks_compose_to_depth_four():
    s, ag, n = boot(True)
    assert observe(s, ag, n, scale(rot(BASE)), "l2") == "recognized_transformed"
    assert len(chunks(s)) == 1
    assert observe(s, ag, n, refl(scale(rot(BASE))), "l3") == "recognized_transformed"
    cs = chunks(s)
    assert len(cs) == 2
    assert any(any(str(st).startswith("chunk:") for st in c["steps"]) for c in cs), "a chunk of a chunk"
    assert observe(s, ag, n, scale(refl(scale(rot(BASE)))), "l4") == "recognized_transformed"
    for c in cs:
        assert list(c["minted_dim_types"]) == DT          # WP1 provenance on chunks


def test_chunk_transfers_to_a_different_base():
    s, ag, n = boot(True)
    observe(s, ag, n, scale(rot(BASE)), "l2")
    s.add_node("ShapeSignature", {"name": "other", "signature": json.dumps(OTHER), "kind": "faculty",
                                  "faculty": "other", "dim_types": DT})
    assert observe(s, ag, n, refl(scale(rot(OTHER))), "l3_other") == "recognized_transformed"


def test_controls_chunk_nothing():
    s, ag, n = boot(True)
    assert observe(s, ag, n, rot(BASE), "l1") == "recognized_transformed"
    assert observe(s, ag, n, [["cell", 0, 0, "red"], ["cell", 5, 1, "red"], ["cell", 3, 3, "blue"],
                              ["cell", 1, 4, "red"], ["cell", 2, 2, "red"]], "scrambled") == "minted"
    assert chunks(s) == []


# --- RETENTION (tranche 2, gate 3) -------------------------------------------

def _live(s):
    return [c for c in chunks(s) if c.get("retired") != 1]


def test_no_capacity_never_retires():
    s, ag, n = boot(True)
    observe(s, ag, n, scale(rot(BASE)), "a")
    observe(s, ag, n, scale(refl(BASE)), "b")
    assert len(_live(s)) == 2


def test_capacity_retires_least_used_and_keeps_used():
    s, ag, n = boot(True)
    s.set_attr(ag, "gen_chunk_capacity", 1)
    observe(s, ag, n, scale(rot(BASE)), "a")           # chunk A minted
    observe(s, ag, n, refl(scale(rot(BASE))), "a3")    # uses A (+ mints A3 -> over capacity)
    live = _live(s)
    assert len(live) == 1
    assert live[0]["uses"] >= 1


def test_retirement_removes_a_candidate_not_a_capability_built_on_live_chunks():
    s, ag, n = boot(True)
    observe(s, ag, n, scale(rot(BASE)), "a")           # chunk A (then used by a3 -> uses 1)
    observe(s, ag, n, refl(scale(rot(BASE))), "a3")    # chunk A3 = refl . A (uses 0)
    s.set_attr(ag, "gen_chunk_capacity", 1)
    n.run_rules()
    live = _live(s)
    assert len(live) == 1 and live[0]["uses"] == 1, "the least-used chunk (A3) is retired"
    retired = [c for c in chunks(s) if c.get("retired") == 1]
    assert len(retired) == 1 and any(str(st).startswith("chunk:") for st in retired[0]["steps"])
    # depth 3 is still reachable: A (live) + one primitive step
    assert observe(s, ag, n, refl(scale(rot(BASE))), "again") == "recognized_transformed"
