#!/usr/bin/env python3
"""WP3 emitter: SUBSTRATE-CHOSEN GRAIN for generator inference.

seeds/shape_decode_loop.json v1.12.0. `sd_gen_check` now asks GenInfer at
grains in agent.gen_grains (a list; absent -> [0], i.e. grain 0 only:
byte-identical decisions) and records the FIRST (finest) grain at which an
exact map exists as `obs.gen_grain`; `gen_explained` is true iff one exists.
Every other GenInfer Term in the seed reads `grain = obs.gen_grain`, so the
minted generator is the map found at that grain, and the generator records
`minted_map_grain`. Re-quantization is exact integer flooring of
origin-normalized coordinates (shape_decode.rs `requantize`); the finer
detail is not discarded, it is what remains unexplained at grain 0 -- the
same observation still carries its full-resolution signature, and a finer
mint later refines this one along the aperture axis (WP1).

The grain choice is a graph decision (MinOver over a held grain list), not a
caller parameter.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds/shape_decode_loop.json"
MAX_GRAIN = 6


def V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def L(v): return {"type": "Lit", "value": v}


def walk(o, fn):
    if isinstance(o, dict):
        fn(o)
        for v in o.values():
            walk(v, fn)
    elif isinstance(o, list):
        for v in o:
            walk(v, fn)


def main():
    text = SEED.read_text()
    seed = json.loads(text)
    rules = {r["name"]: r for r in seed["rules"]}
    chk = rules["sd_gen_check"]
    prior = next((e for e in chk["effects"] if e[0] == "set_attr" and e[2] == "gen_grain"), None)
    eff = [e for e in chk["effects"] if not (e[0] == "set_attr" and e[2] in ("gen_grain",))]
    gx = next(e for e in eff if e[0] == "set_attr" and e[2] == "gen_explained")
    if prior is not None:   # idempotent re-run: recover the original GenInfer probe
        items = prior[3]["__term__"]["source"]["predicate"]["items"]
        base_term = next(it["a"] for it in items if it.get("type") == "Eq" and isinstance(it.get("a"), dict) and it["a"].get("type") == "GenInfer")
        base_term = {k: v for k, v in base_term.items() if k != "grain"}
        base_term["field"] = "explained"
    else:
        base_term = gx[3]["__term__"]
    assert base_term["type"] == "GenInfer", base_term["type"]
    base_term = json.loads(json.dumps(base_term))
    base_term.pop("grain", None)
    probe = dict(base_term, grain=V("g"), field="explained")
    # At a COARSER grain (g > 0) the map must be invertible: re-quantization
    # can collapse a shape onto a line, and a singular matrix then "explains"
    # anything (the det=0 universal-container leak, VISION_DET1). Grain 0 keeps
    # the seed's existing semantics unchanged.
    mat = dict(base_term, grain=V("g"), field="matrix")
    nth = lambda i: {"type": "Nth", "items": mat, "index": i}
    det = {"type": "Minus", "a": {"type": "Times", "items": [nth(0), nth(3)]},
           "b": {"type": "Times", "items": [nth(1), nth(2)]}}
    invertible = {"type": "Or", "items": [{"type": "Eq", "a": V("g"), "b": L(0)},
                                          {"type": "Not", "arg": {"type": "Eq", "a": det, "b": L(0)}}]}
    # The grains to try are graph data: agent.gen_grains, a list (absent -> [0],
    # i.e. unchanged). Membership, not a numeric comparator, so the seed keeps
    # its audited "admission is exact equality" shape (no bound-like operand).
    grains = {"type": "IfThenElse", "cond": {"type": "Eq", "a": A("ag", "gen_grains"), "b": L(None)},
              "then": L([0]), "other": A("ag", "gen_grains")}
    grain_term = {"type": "MinOver",
                  "source": {"type": "FilterList", "source": grains, "var_name": "g",
                             "predicate": {"type": "And", "items": [{"type": "Eq", "a": probe, "b": L(True)}, invertible]}},
                  "var_name": "g", "value": V("g"), "default": L(None)}
    gx[3] = {"__term__": {"type": "Not", "arg": {"type": "Eq", "a": grain_term, "b": L(None)}}}
    eff.insert(eff.index(gx), ["set_attr", "obs", "gen_grain", {"__term__": grain_term}])
    chk["effects"] = eff

    def add_grain(d):
        if d.get("type") == "GenInfer" and "grain" not in d:
            d["grain"] = A("obs", "gen_grain")
    for r in seed["rules"]:
        if r["name"] == "sd_gen_check":
            continue
        walk(r, add_grain)
    for name in ("sd_mint_generator", "sd_mint_quadratic_generator"):
        r = rules[name]
        r["effects"] = [e for e in r["effects"] if not (e[0] == "set_attr" and e[2] == "minted_map_grain")]
        r["effects"].append(["set_attr", "g", "minted_map_grain", {"__term__": A("obs", "gen_grain")}])
    # An observation explained only at a COARSER grain is recognised AT that
    # grain (not silently left 'decoded'), and what the coarse map does not
    # account for -- the sub-grain detail -- is carried as its own quantum:
    # a CapabilityAxis holding the full-resolution signature with
    # minted_aperture = the frame's dim_types and coarse_grain = g. A later
    # finer explanation refines it; it never mints finer than it saw.
    gx_obs = dict(base_term, grain=A("obs", "gen_grain"))
    rec = {
        "name": "sd_recognize_at_grain",
        "comment": "RUNG-3 recognition at a substrate-chosen coarser grain (WP3): the minted generator explains the observation at obs.gen_grain > 0; the sub-grain residual is carried as a content-keyed CapabilityAxis{source:'grain_residual'}.",
        "match": [["ag", "observed", "obs"]],
        "where": {"type": "And", "items": [
            {"type": "Eq", "a": A("obs", "status"), "b": L("decoded")},
            {"type": "Eq", "a": A("obs", "gen_checked"), "b": L(1)},
            {"type": "Eq", "a": A("obs", "gen_explained"), "b": L(True)},
            {"type": "Not", "arg": {"type": "Eq", "a": A("obs", "gen_grain"), "b": L(0)}},
            {"type": "Exists", "source": {"type": "NodesOfType", "node_type": "DimensionGenerator"}, "var_name": "hg",
             "predicate": {"type": "And", "items": [
                 {"type": "Eq", "a": A("hg", "kind"), "b": L("linear")},
                 {"type": "Eq", "a": A("hg", "matrix"), "b": dict(gx_obs, field="matrix")}]}},
        ]},
        "effects": [
            ["set_attr", "obs", "status", "recognized_at_grain"],
            ["set_attr", "obs", "recognized_grain", {"__term__": A("obs", "gen_grain")}],
            ["set_attr", "obs", "covered_by", {"__term__": dict(gx_obs, field="base")}],
            ["set_attr", "obs", "recognized_matrix", {"__term__": dict(gx_obs, field="matrix")}],
            ["add_node_if_absent", "axis", "CapabilityAxis", {
                "source": "grain_residual",
                "minted_from_signature": {"__term__": A("obs", "signature")},
                "minted_aperture": {"__term__": A("obs", "dim_types")}}],
            ["set_attr", "axis", "is_axis", 1.0],
            ["set_attr", "axis", "coarse_grain", {"__term__": A("obs", "gen_grain")}],
            ["set_attr", "axis", "minted_dim_types", {"__term__": A("obs", "dim_types")}],
            ["add_edge", "obs", "minted", "axis"],
        ],
    }
    seed["rules"] = [r for r in seed["rules"] if r["name"] != rec["name"]] + [rec]
    seed["version"] = "1.12.0"
    note = (" v1.12.0 (2026-10-06, RECURSIVE_SELF_IMPROVEMENT_PLAN WP3): sd_gen_check chooses the finest grain"
            " in agent.gen_grains (list; absent -> [0], unchanged) at which GenInfer finds an exact map (obs.gen_grain);"
            " all other GenInfer Terms read that grain; minted generators record minted_map_grain"
            " (scripts/gen_geninfer_grain_ladder.py).")
    if "v1.12.0" not in seed["description"]:
        seed["description"] += note
    SEED.write_text(json.dumps(seed, indent=1, ensure_ascii=True) + ("\n" if text.endswith("\n") else ""))
    print("updated", SEED.relative_to(ROOT))


if __name__ == "__main__":
    main()
