#!/usr/bin/env python3
"""Tranche 2 gate 4 emitter: SUBSTRATE-CHOSEN GRAIN for HELD-generator inference.

seeds/shape_decode_loop.json v1.14.0. `sd_infer_dimension` asks DimInfer at
each grain in `agent.dim_grains` (a list; absent -> [0], i.e. unchanged) and
records the FINEST grain at which a held generator explains the observation
as `obs.dim_grain`. Every other DimInfer Term reads `grain = obs.dim_grain`.
The analysis that justified this (evaluation/reports/d4_grain_commutation_v1)
found held D4 maps discriminate jittered handwriting at grain 2 (71/160 vs
0/160 cross-character), unlike GenInfer's shear search.

`sd_dim_grain_residual`: an observation recognised at a coarser grain records
`recognized_grain` and carries its full-resolution signature as a
content-keyed CapabilityAxis{source:'grain_residual'} -- the sub-grain detail
is kept, never discarded.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds/shape_decode_loop.json"


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
    if not any(n.get("type") == "DimInferPolicy" for n in seed.get("nodes", [])):
        seed.setdefault("nodes", []).append({
            "local_id": 6,
            "type": "DimInferPolicy",
            "attrs": {
                "name": "default_dim_infer_policy",
                "dim_grains": [0],
            },
        })
    if not any(e.get("type") == "has_dim_infer_policy" for e in seed.get("edges", [])):
        seed.setdefault("edges", []).append({
            "src": {"role": "agent_root"},
            "type": "has_dim_infer_policy",
            "tgt": {"local": 6},
            "attrs": {},
        })
    if not any(p.get("edge_type") == "has_dim_infer_policy" for p in seed.get("productions", [])):
        seed.setdefault("productions", []).append({
            "provenance": "seed:shape_decode_loop:has-dim-infer-policy",
            "src": {"type": "Agent", "var": "s"},
            "edge_type": "has_dim_infer_policy",
            "tgt": {"type": "DimInferPolicy", "var": "t"},
        })
    rules = {r["name"]: r for r in seed["rules"]}
    rule = rules["sd_infer_dimension"]
    eff = [e for e in rule["effects"] if not (e[0] == "set_attr" and e[2] == "dim_grain")]
    ex = next(e for e in eff if e[0] == "set_attr" and e[2] == "dim_explained")
    probe = {"type": "DimInfer", "goal": A("obs", "signature"), "max_dims": 2, "field": "explained", "grain": V("g")}
    pol_grains = {"type": "Attr",
                  "node": {"type": "Pick",
                           "source": {"type": "Neighbours", "node": V("ag"), "edge_type": "has_dim_infer_policy"}},
                  "key": "dim_grains"}
    fallback_grains = {"type": "IfThenElse",
                       "cond": {"type": "Eq", "a": pol_grains, "b": L(None)},
                       "then": L([0]),
                       "other": pol_grains}
    grains = {"type": "IfThenElse", "cond": {"type": "Eq", "a": A("ag", "dim_grains"), "b": L(None)},
              "then": fallback_grains, "other": A("ag", "dim_grains")}
    grain_term = {"type": "MinOver", "source": {"type": "FilterList", "source": grains, "var_name": "g",
                                                "predicate": {"type": "Eq", "a": probe, "b": L(True)}},
                  "var_name": "g", "value": V("g"), "default": L(None)}
    ex[3] = {"__term__": {"type": "Not", "arg": {"type": "Eq", "a": grain_term, "b": L(None)}}}
    eff.insert(eff.index(ex), ["set_attr", "obs", "dim_grain", {"__term__": grain_term}])
    rule["effects"] = eff

    def add_grain(d):
        if d.get("type") == "DimInfer" and "grain" not in d:
            d["grain"] = A("obs", "dim_grain")
    for r in seed["rules"]:
        if r["name"] != "sd_infer_dimension":
            walk(r, add_grain)
    # sd_infer_dimension's own dim_infer attr reads the chosen grain too
    for e in rule["effects"]:
        if e[0] == "set_attr" and e[2] == "dim_infer":
            e[3]["__term__"]["grain"] = A("obs", "dim_grain")

    res = {
        "name": "sd_dim_grain_residual",
        "comment": "An observation recognised through a HELD generator at a coarser grain (obs.dim_grain not 0) records recognized_grain and carries its full-resolution signature as a content-keyed CapabilityAxis{source:'grain_residual'} (tranche 2 gate 4).",
        "match": [["ag", "observed", "obs"]],
        "where": {"type": "And", "items": [
            {"type": "Eq", "a": A("obs", "status"), "b": L("recognized_transformed")},
            {"type": "Not", "arg": {"type": "Eq", "a": A("obs", "dim_grain"), "b": L(None)}},
            {"type": "Not", "arg": {"type": "Eq", "a": A("obs", "dim_grain"), "b": L(0)}},
            {"type": "Eq", "a": A("obs", "recognized_grain"), "b": L(None)},
        ]},
        "effects": [
            ["set_attr", "obs", "recognized_grain", {"__term__": A("obs", "dim_grain")}],
            ["add_node_if_absent", "axis", "CapabilityAxis", {
                "source": "grain_residual",
                "minted_from_signature": {"__term__": A("obs", "signature")},
                "minted_aperture": {"__term__": A("obs", "dim_types")}}],
            ["set_attr", "axis", "is_axis", 1.0],
            ["set_attr", "axis", "coarse_grain", {"__term__": A("obs", "dim_grain")}],
            ["set_attr", "axis", "minted_dim_types", {"__term__": A("obs", "dim_types")}],
            ["add_edge", "obs", "minted", "axis"],
        ],
    }
    seed["rules"] = [res if r["name"] == res["name"] else r for r in seed["rules"]]
    if res["name"] not in rules:
        seed["rules"].append(res)
    seed["version"] = max(seed["version"], "1.14.0", key=lambda v: tuple(map(int, v.split("."))))
    note = (" v1.14.0 (2026-10-07, tranche 2 gate 4): sd_infer_dimension picks the finest grain in agent.dim_grains"
            " (list; absent -> [0], unchanged) at which a HELD generator explains the observation (obs.dim_grain); every"
            " DimInfer Term reads it; sd_dim_grain_residual records recognized_grain and carries the full-resolution"
            " signature as a grain_residual axis (scripts/gen_diminfer_grain.py).")
    if "v1.14.0" not in seed["description"]:
        seed["description"] += note
    SEED.write_text(json.dumps(seed, indent=1, ensure_ascii=True) + ("\n" if text.endswith("\n") else ""))
    print("updated", SEED.relative_to(ROOT))


if __name__ == "__main__":
    main()
