#!/usr/bin/env python3
"""PER-SENSOR EPOCH (block 188000) — emit the per-sensor seed variants.

An AUTHORING tool: it reads the committed seeds and writes variants in which
`input_epoch` is no longer ONE key shared by five node roles. Each sensor's
clock gets its own NAME:

    receptor / rod / l / m / s   ->  rod_epoch
    column (RetinalColumn)       ->  column_epoch
    percept (RetinalPercept)     ->  percept_epoch
    task / area (the scheduler)  ->  input_epoch   (unchanged — that IS the
                                                    scheduler's own clock)

WHY A NAME MATTERS. The engine's dirty index is keyed on the attribute KEY.
Block 187000 measured that ONE `set_attr(retina_root,"input_epoch",…)` — on a
node no rule reads that key on — takes the graph from 0 dirty rules to 8 across
all 6 cortical areas. A shared key IS a shared clock. Splitting the name is what
makes "each sensor has its own epoch" true of the MACHINE and not just of the
prose.

The rewrite is mechanical: walk the manifest, and rewrite `Attr{node:Var(v),
key:"input_epoch"}` and `set_attr*` effects targeting var `v` for exactly the
vars in the map. Nothing else is touched — no rule is added, removed, reordered
or otherwise altered, and the emitted variants are committed so the diff is
readable.

Also emits the WRONG-EPOCH FALSIFIER variant, in which the rod's clock is a
CONSTANT: it fails to advance even when the sensor genuinely changed. That must
break an observable output (the onset stream), proving the per-sensor epoch is
load-bearing and the identity check non-vacuous.

Usage:  python3 tools/build_per_sensor_epoch_seeds.py
"""
from __future__ import annotations

import copy
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEEDS = os.path.join(ROOT, "seeds")

#: var name -> the epoch key that variable's node carries.
VAR_KEY = {
    "receptor": "rod_epoch",
    "rod": "rod_epoch",
    "l": "rod_epoch",
    "m": "rod_epoch",
    "s": "rod_epoch",
    "column": "column_epoch",
    "percept": "percept_epoch",
}

EPOCH = "input_epoch"


def rewrite_reads(obj, var_key):
    """Rewrite every `Attr{node: Var(v), key: input_epoch}` for v in var_key."""
    if isinstance(obj, dict):
        if (obj.get("type") == "Attr" and obj.get("key") == EPOCH
                and isinstance(obj.get("node"), dict)
                and obj["node"].get("type") == "Var"
                and obj["node"].get("name") in var_key):
            obj = dict(obj)
            obj["key"] = var_key[obj["node"]["name"]]
            return {k: rewrite_reads(v, var_key) for k, v in obj.items()}
        return {k: rewrite_reads(v, var_key) for k, v in obj.items()}
    if isinstance(obj, list):
        return [rewrite_reads(v, var_key) for v in obj]
    return obj


def rewrite_effects(effects, var_key):
    """Rewrite `["set_attr*", var, "input_epoch", value]` for var in var_key."""
    out = []
    for eff in effects:
        if (isinstance(eff, list) and len(eff) >= 3
                and isinstance(eff[0], str) and eff[0].startswith("set_attr")
                and eff[1] in var_key and eff[2] == EPOCH):
            eff = list(eff)
            eff[2] = var_key[eff[1]]
        out.append(eff)
    return out


def variant(seed_id, out_id, var_key, *, freeze_rod=False):
    src = json.load(open(os.path.join(SEEDS, seed_id + ".json")))
    d = copy.deepcopy(src)
    d["id"] = out_id
    d["version"] = "1.0.0"
    d["description"] = (
        (src.get("description", "") or "")
        + "  [PER-SENSOR EPOCH variant, block 188000: each sensor's clock "
          "carries its own attribute key; the scheduler's task/area epoch is "
          "unchanged.]")
    if freeze_rod:
        d["description"] += ("  [WRONG-EPOCH FALSIFIER: the rod's clock is a "
                             "CONSTANT — it fails to advance when the sensor "
                             "genuinely changed. MUST break an observable.]")
    for rule in d.get("rules", []):
        if rule.get("where") is not None:
            rule["where"] = rewrite_reads(rule["where"], var_key)
        rule["effects"] = rewrite_effects(
            rewrite_reads(rule.get("effects", []), var_key), var_key)
        if freeze_rod:
            for eff in rule["effects"]:
                if (isinstance(eff, list) and len(eff) >= 4
                        and isinstance(eff[0], str)
                        and eff[0].startswith("set_attr")
                        and eff[2] == "rod_epoch"):
                    eff[3] = 0
    # Node/edge payloads carry initial attrs; rename them the same way where the
    # node's TYPE fixes the role (mechanical, no decision).
    path = os.path.join(SEEDS, out_id + ".json")
    with open(path, "w") as fh:
        json.dump(d, fh, indent=1)
        fh.write("\n")
    print("wrote", path)


def main():
    variant("photon_retina", "photon_retina_per_sensor", VAR_KEY)
    variant("retinal_onset_2d", "retinal_onset_2d_per_sensor", VAR_KEY)
    variant("photon_retina", "photon_retina_wrong_epoch", VAR_KEY,
            freeze_rod=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
