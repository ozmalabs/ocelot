#!/usr/bin/env python3
"""Tranche 2 gate 5 emitter: MDL witness routed through the sd loop.

shape_decode_loop.json v1.15.0. Every GenInfer Term reads
`mdl_enabled = agent.gen_mdl_enabled` (absent -> false, unchanged; the MDL
path also needs the `geninfer_grain_mdl` Cargo feature). When GenInfer
explains an observation by MDL, the existing sd_mint_generator mints the map,
and `sd_mdl_outliers` records the rows the map does NOT explain:
  * obs.status = 'recognized_with_outliers', covered_by = base,
    recognized_matrix, mdl_outliers = those rows;
  * a content-keyed CapabilityAxis{source:'mdl_outlier'} holding exactly the
    unexplained rows (WP1 provenance) -- the outliers become their own
    residual quantum instead of vetoing the map.
"""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds/shape_decode_loop.json"

def V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def L(v): return {"type": "Lit", "value": v}

def walk(o, fn):
    if isinstance(o, dict):
        fn(o); [walk(v, fn) for v in o.values()]
    elif isinstance(o, list):
        [walk(v, fn) for v in o]

def main():
    text = SEED.read_text(); seed = json.loads(text)
    def add(d):
        if d.get("type") == "GenInfer" and "mdl_enabled" not in d:
            d["mdl_enabled"] = A("ag", "gen_mdl_enabled")
    walk(seed["rules"], add)
    chk = next(r for r in seed["rules"] if r["name"] == "sd_gen_check")
    probe = chk["effects"][1][3]["__term__"]["source"]["predicate"]["items"][0]["a"]
    gi = {k: v for k, v in probe.items() if k != "grain"}
    gi["grain"] = A("obs", "gen_grain")
    f = lambda field: dict(gi, field=field)
    rule = {
        "name": "sd_mdl_outliers",
        "comment": __doc__.strip(),
        "match": [["ag", "observed", "obs"]],
        "where": {"type": "And", "items": [
            {"type": "Eq", "a": A("ag", "gen_mdl_enabled"), "b": L(1)},
            {"type": "Eq", "a": A("obs", "gen_explained"), "b": L(True)},
            {"type": "Eq", "a": f("witness"), "b": L("mdl")},
            {"type": "Eq", "a": A("obs", "mdl_outliers"), "b": L(None)},
        ]},
        "effects": [
            ["set_attr", "obs", "mdl_outliers", {"__term__": f("outliers")}],
            ["set_attr", "obs", "status", "recognized_with_outliers"],
            ["set_attr", "obs", "covered_by", {"__term__": f("base")}],
            ["set_attr", "obs", "recognized_matrix", {"__term__": f("matrix")}],
            ["add_node_if_absent", "axis", "CapabilityAxis", {
                "source": "mdl_outlier",
                "minted_from_signature": {"__term__": f("outliers")},
                "minted_aperture": {"__term__": A("obs", "dim_types")}}],
            ["set_attr", "axis", "is_axis", 1.0],
            ["set_attr", "axis", "minted_dim_types", {"__term__": A("obs", "dim_types")}],
            ["set_attr", "axis", "mdl_bits", {"__term__": f("mdl_bits")}],
            ["add_edge", "obs", "minted", "axis"],
        ],
    }
    seed["rules"] = [r for r in seed["rules"] if r["name"] != rule["name"]] + [rule]
    seed["version"] = max(seed["version"], "1.15.0", key=lambda v: tuple(map(int, v.split("."))))
    note = (" v1.15.0 (2026-10-07, tranche 2 gate 5): GenInfer Terms read mdl_enabled=agent.gen_mdl_enabled (absent ->"
            " unchanged; needs feature geninfer_grain_mdl); sd_mdl_outliers marks an MDL-explained observation"
            " recognized_with_outliers and carries the unexplained rows as a CapabilityAxis{source:'mdl_outlier'}"
            " (scripts/gen_mdl_outlier_rule.py).")
    if "v1.15.0" not in seed["description"]:
        seed["description"] += note
    SEED.write_text(json.dumps(seed, indent=1, ensure_ascii=True) + ("\n" if text.endswith("\n") else ""))
    print("updated")

main()
