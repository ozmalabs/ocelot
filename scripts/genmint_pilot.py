#!/usr/bin/env python3
"""GEN-MINT pre-build PILOT (deterministic, no RNG, burns no seed).

Establishes, on the CURRENT engine, the two facts the whole rung rests on:

  (A) THE GAP: a held-out SHEAR orbit falls through to `sd_mint_quantum`
      today (a flat quantum), while a HELD rotation is SELECTED
      (recognized_transformed) and a SCRAMBLED goal also mints a quantum.
      This is the "select / mint" discrimination the brief locates in the
      seed rules, measured rather than assumed.

  (B) THE REPRESENTATION WALL: minting a generator AS GRAPH DATA is inert
      in the current engine. Add a DimensionGenerator{kind:"linear",
      params:<shear matrix>} node by hand (simulating a successful "mint")
      and re-run DimInfer on the sheared goal: it is STILL not explained,
      because `apply_generator_once` dispatches `kind` to a hardcoded Rust
      function and has no "linear" arm -> the graph-data generator is
      inapplicable. The transform is CODE, not DATA.

Run: python scripts/genmint_pilot.py   (from the gamma-substrate dir)
"""
from __future__ import annotations

import json

from domains.engine_provenance import engine_preamble, provenance_line
engine_preamble()

from substrate.boot_core import boot_core          # noqa: E402
from domains import reflective_faculty as rf        # noqa: E402

DIM_TYPES = ["pred", "coord:r", "coord:c", "val"]


def boot():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    return s, ag, native


def add_part(s, name, sig):
    return s.add_node("ShapeSignature", {
        "name": name, "signature": json.dumps(sig), "kind": "faculty",
        "faculty": name, "dim_types": list(DIM_TYPES)})


def observe(s, ag, sig):
    epoch = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    obs = s.add_node("Observation", {
        "signature": sig, "key": ["probe"], "status": "decoded",
        "residual": sig, "decoded_epoch": epoch, "dim_types": list(DIM_TYPES)})
    s.add_edge(ag, "observed", obs)
    return obs


def axes(s):
    return len(list(s.nodes("CapabilityAxis")))


def cell(r, c, v="red"):
    return ["cell", r, c, v]


# --- base shape: a tall L-tetromino (asymmetric; its shear image lands on a
#     unit-slope diagonal that no rotation/reflection/scale/cycle image or
#     rung-1 uniform delta can reach). ---
BASE = [cell(0, 0), cell(1, 0), cell(2, 0), cell(2, 1)]

# horizontal shear S:(r,c)->(r, c+r), origin already at (0,0):
#   (0,0)->(0,0) (1,0)->(1,1) (2,0)->(2,2) (2,1)->(2,3)
SHEAR_GOAL = [cell(0, 0), cell(1, 1), cell(2, 2), cell(2, 3)]

# rotation90 image of BASE (r,c)->(c, maxr-r), maxr=2:
#   (0,0)->(0,2) (1,0)->(0,1) (2,0)->(0,0) (2,1)->(1,0)
ROT_GOAL = [cell(0, 2), cell(0, 1), cell(0, 0), cell(1, 0)]

# scrambled: same coords as BASE, three distinct colours -> no coherent map
SCRAMBLED_GOAL = [cell(0, 0, "blue"), cell(1, 0, "green"),
                  cell(2, 0, "yellow"), cell(2, 1, "purple")]


def run_case(label, goal_sig, extra_generator=None):
    s, ag, native = boot()
    add_part(s, "base_L", BASE)
    if extra_generator is not None:
        s.add_node("DimensionGenerator", extra_generator)
    base_axes = axes(s)
    obs = observe(s, ag, goal_sig)
    native.run_rules()
    at = s.node(obs)["attrs"]
    minted = axes(s) - base_axes
    print(f"[{label}]")
    print(f"    status            = {at.get('status')!r}")
    print(f"    transform_checked = {at.get('transform_checked')}")
    print(f"    dim_checked       = {at.get('dim_checked')}")
    print(f"    dim_explained     = {at.get('dim_explained')}")
    print(f"    CapabilityAxis minted = {minted}")
    return at, minted


def diminfer_explained(goal_sig, extra_generator=None):
    """Direct DimInfer call: does the (optionally-extended) generator
    codebook explain the goal? Mirrors the seed's own field='explained'."""
    s, ag, native = boot()
    add_part(s, "base_L", BASE)
    if extra_generator is not None:
        s.add_node("DimensionGenerator", extra_generator)
    return native.evaluate(
        {"type": "DimInfer",
         "goal": {"type": "Lit", "value": goal_sig},
         "max_dims": 2, "field": "explained"}, {})


def main():
    print("ENGINE:", provenance_line())
    print("=" * 68)
    print("(A) THE GAP — select vs mint on the current engine")
    print("=" * 68)
    rot, rot_m = run_case("HELD rotation  -> expect SELECT (recognized_transformed, 0 mint)", ROT_GOAL)
    shr, shr_m = run_case("HELD-OUT shear -> expect MINT QUANTUM (flat novelty)", SHEAR_GOAL)
    scr, scr_m = run_case("SCRAMBLED      -> expect MINT QUANTUM (floor)", SCRAMBLED_GOAL)

    print()
    print("=" * 68)
    print("(B) THE REPRESENTATION WALL — mint a generator AS GRAPH DATA, inert?")
    print("=" * 68)
    lin_gen = {"name": "shearX", "kind": "linear", "coord_dims": [1, 2],
               "params": [1, 1, 0, 1]}   # the exact shear matrix, as data
    print("Added DimensionGenerator{name:shearX, kind:'linear', params:[1,1,0,1]}")
    exp_before = diminfer_explained(SHEAR_GOAL)
    exp_after = diminfer_explained(SHEAR_GOAL, extra_generator=lin_gen)
    print(f"    DimInfer(shear goal) explained WITHOUT data-generator = {exp_before}")
    print(f"    DimInfer(shear goal) explained WITH    data-generator = {exp_after}")
    shr2, shr2_m = run_case(
        "HELD-OUT shear WITH the data-'linear' generator present -> still MINT?",
        SHEAR_GOAL, extra_generator=lin_gen)

    print()
    print("=" * 68)
    print("VERDICT")
    print("=" * 68)
    gap_ok = (rot.get("status") == "recognized_transformed" and rot_m == 0
              and shr.get("status") == "minted" and shr_m == 1
              and scr.get("status") == "minted" and scr_m == 1)
    wall_ok = (exp_before is False and exp_after is False
               and shr2.get("status") == "minted")
    print(f"(A) GAP present (held->select, held-out shear->quantum, scrambled->quantum): {gap_ok}")
    print(f"(B) WALL present (data-'linear' generator INERT; shear still mints):        {wall_ok}")


if __name__ == "__main__":
    main()
