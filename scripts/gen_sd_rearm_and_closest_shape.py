#!/usr/bin/env python3
"""Block 371000: sd-loop re-arm (D1) and ClosestShape rule sites (D2).

Edits `seeds/shape_decode_loop.json` (v1.17.0 -> v1.18.0) as data:

1. D2: in `sd_recognize.covered_by` and `sd_mint_quantum.closest_held_shape`,
   the inner `Argmax(NodesOfType ShapeSignature, sig, FixedCount(AntiUnify(
   SetT[goal, Attr(sig, "signature")])))` becomes `{"type": "ClosestShape",
   "goal": goal}`. The pattern must match exactly, or the script stops.
2. D1: inserts `sd_rerecognize_transformed` and `sd_rerecognize_dim` directly
   after `sd_recognize_dim`. Their where clauses and effects are deep copies
   of the matching parts of the existing rules, not retyped copies. They
   re-recognise a decoded observation that already has a `has_transform` edge
   and update that Transform node in place, so no second Transform is minted.

Idempotent: a second run finds the edits in place and writes nothing new.
Formatting is `json.dumps(indent=1)` plus a trailing newline. This reproduces
the seed byte for byte before any edit (checked when the script was written).

Block 372000 (SD_LOOP_GEN_REARM_AND_TIE_PARITY_PREREG.md, G1): sd_redecode also
clears `gen_checked` and `gen_explained` on re-arm (appended after the existing
`dim_explained` reset), and the seed moves v1.18.0 -> v1.19.0. A seed still at
v1.17.0 passes through v1.18.0 on its way to v1.19.0.

Not handled here: `seeds/prog_construction_loop.json`. Its three Argmax sites
(`pcon_recognize`, `pcon_mark_merge` x2) read a `Filter`ed source
(`kind == "prog_construction"`, and a `Covers` predicate in one rule), not the
bare `NodesOfType` that `ClosestShape` scans, so they do not match the pattern
this script asserts. See the block 371000 report.
"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "shape_decode_loop.json"
OLD_VERSION = "1.17.0"
NEW_VERSION = "1.18.0"
LATEST_VERSION = "1.19.0"
BLOCK = "block 371000"
GEN_BLOCK = "block 372000"
GEN_RESET_ANCHOR = ["set_attr", "obs", "dim_explained", 0]
GEN_RESETS = [
    ["set_attr", "obs", "gen_checked", 0],
    ["set_attr", "obs", "gen_explained", 0],
]

RERECOGNIZE_T = "sd_rerecognize_transformed"
RERECOGNIZE_D = "sd_rerecognize_dim"
T_ATTRS = ["dims", "transforms", "deltas", "base", "source"]
D_ATTRS = ["dim", "delta", "generator", "k", "dims", "transforms", "base",
           "generators", "ks", "source"]


def obs_sig():
    return {"type": "Attr", "node": {"type": "Var", "name": "obs"}, "key": "signature"}


def argmax_pattern(goal):
    """The inner Argmax exactly as it is written in the seed today."""
    return {
        "type": "Argmax",
        "source": {"type": "NodesOfType", "node_type": "ShapeSignature"},
        "var_name": "sig",
        "value": {
            "type": "FixedCount",
            "pattern": {
                "type": "AntiUnify",
                "values": {
                    "type": "SetT",
                    "items": [
                        goal,
                        {"type": "Attr", "node": {"type": "Var", "name": "sig"}, "key": "signature"},
                    ],
                },
            },
        },
        "default": None,
    }


def rule_named(rules, name):
    hits = [i for i, r in enumerate(rules) if r.get("name") == name]
    assert len(hits) == 1, f"expected exactly one rule named {name}, found {len(hits)}"
    return hits[0]


def get_path(obj, path):
    for step in path:
        obj = obj[step]
    return obj


def set_path(obj, path, value):
    parent = get_path(obj, path[:-1])
    parent[path[-1]] = value


def replace_sites(rules):
    """D2: swap the four-level Argmax for ClosestShape at the two shape_decode sites."""
    sites = [
        ("sd_recognize", ["effects", 1, 3, "__term__", "node"]),
        ("sd_mint_quantum", ["effects", 0, 3, "closest_held_shape", "__term__", "node"]),
    ]
    changed = []
    for rule_name, path in sites:
        rule = rules[rule_named(rules, rule_name)]
        node = get_path(rule, path)
        want_new = {"type": "ClosestShape", "goal": obs_sig()}
        if node == want_new:
            continue  # already replaced (idempotent re-run)
        if node != argmax_pattern(obs_sig()):
            raise SystemExit(
                f"{rule_name} at {path}: Argmax does not match the expected pattern; "
                f"stopping without writing. Found: {json.dumps(node)[:400]}"
            )
        set_path(rule, path, want_new)
        changed.append(rule_name)
    return changed


def build_guard_pieces(rules):
    """Copy the agnosia guard and the three equality checks from the existing rules."""
    rr_sr = rules[rule_named(rules, "sd_recognize")]
    rr_st = rules[rule_named(rules, "sd_recognize_transformed")]
    rr_sd = rules[rule_named(rules, "sd_recognize_dim")]

    guard = copy.deepcopy(rr_st["where"]["items"][0])
    assert guard["type"] == "Lt" and "AgnosiaParams" in json.dumps(guard), "agnosia guard moved"
    assert json.dumps(guard) == json.dumps(rr_sd["where"]["items"][0]), "guards differ"

    status_eq = copy.deepcopy(rr_sr["where"]["items"][1])
    assert status_eq["type"] == "Eq" and status_eq["a"]["key"] == "status"
    assert status_eq["b"] == {"type": "Lit", "value": "decoded"}

    te_eq = copy.deepcopy(rr_st["where"]["items"][1])
    assert te_eq["type"] == "Eq" and te_eq["a"]["key"] == "transform_explained"
    assert te_eq["b"] == {"type": "Lit", "value": 1}

    de_eq = copy.deepcopy(rr_sd["where"]["items"][1])
    assert de_eq["type"] == "Eq" and de_eq["a"]["key"] == "dim_explained"
    assert de_eq["b"] == {"type": "Lit", "value": 1}

    return rr_sr, rr_st, rr_sd, guard, status_eq, te_eq, de_eq


def build_rerecognize(rules):
    rr_sr, rr_st, rr_sd, guard, status_eq, te_eq, de_eq = build_guard_pieces(rules)

    # Effects for the transform path, copied from sd_recognize_transformed.
    st_fx = rr_st["effects"]
    assert st_fx[0][:3] == ["set_attr", "obs", "status"], st_fx[0]
    assert st_fx[1][:3] == ["set_attr", "obs", "covered_by"], st_fx[1]
    assert st_fx[2][:3] == ["add_node", "t", "Transform"], st_fx[2]
    t_attrs = st_fx[2][3]
    assert sorted(t_attrs) == sorted(T_ATTRS), sorted(t_attrs)

    t_fx = [copy.deepcopy(st_fx[0]), copy.deepcopy(st_fx[1])]
    # Amendment (SD_LOOP_REARM_AND_JSON_SIGNATURE_AMENDMENT.md): the Transform is the receipt of
    # the FIRST recognition and is not rewritten (sd_chunk_uses counts its generators).

    # Effects for the dimension path, copied from sd_recognize_dim.
    sd_fx = rr_sd["effects"]
    assert sd_fx[0][:3] == ["set_attr", "obs", "status"], sd_fx[0]
    assert sd_fx[1][:3] == ["set_attr", "obs", "covered_by"], sd_fx[1]
    assert sd_fx[2] == ["set_attr", "obs", "transform_explained", 1], sd_fx[2]
    assert sd_fx[3][:3] == ["add_node", "t", "Transform"], sd_fx[3]
    d_attrs = sd_fx[3][3]
    assert sorted(d_attrs) == sorted(D_ATTRS), sorted(d_attrs)

    d_fx = [copy.deepcopy(sd_fx[0]), copy.deepcopy(sd_fx[1]), copy.deepcopy(sd_fx[2])]
    # Amendment: the Transform receipt is left as minted (see above).

    rr_t = {
        "name": RERECOGNIZE_T,
        "comment": (
            f"{BLOCK} (D1). A decoded Observation that already has a has_transform edge, "
            "and whose TransformDecode check explains the residual (transform_explained == 1), "
            "is re-recognised as recognized_transformed. This happens after sd_redecode re-arms it "
            "on a codebook_epoch bump and a grown codebook now explains it. Only status and covered_by "
            "are set: the existing Transform stays the receipt of the first recognition (amendment, "
            "sd_chunk_uses counts Transform.generators as receipts), and no second Transform is minted. sd_recognize_transformed, which needs no has_transform "
            "edge, cannot fire on this observation, so without this rule it stayed decoded forever."
        ),
        "match_type": "Observation",
        "match": [["ag", "observed", "obs"], ["obs", "has_transform", "t"]],
        "where": {
            "type": "And",
            "items": [copy.deepcopy(guard), copy.deepcopy(status_eq), copy.deepcopy(te_eq)],
        },
        "effects": t_fx,
    }
    rr_d = {
        "name": RERECOGNIZE_D,
        "comment": (
            f"{BLOCK} (D1, dimension path). The same re-arm as {RERECOGNIZE_T}, for an "
            "observation explained by DimInfer (dim_explained == 1) that has not yet had its "
            "transform explained (transform_explained != 1). It sets the same fields that "
            "sd_recognize_dim sets on the observation (status, covered_by, transform_explained) and "
            "leaves the Transform receipt, the LatentDimension "
            "node and its edge as they are. Pre-fix behaviour: the observation stayed decoded."
        ),
        "match_type": "Observation",
        "match": [["ag", "observed", "obs"], ["obs", "has_transform", "t"]],
        "where": {
            "type": "And",
            "items": [
                copy.deepcopy(guard),
                copy.deepcopy(status_eq),
                copy.deepcopy(de_eq),
                {"type": "Not", "arg": copy.deepcopy(te_eq)},
            ],
        },
        "effects": d_fx,
    }
    return rr_t, rr_d


def insert_rerecognize(rules):
    names = [r.get("name") for r in rules]
    if RERECOGNIZE_T in names or RERECOGNIZE_D in names:
        assert RERECOGNIZE_T in names and RERECOGNIZE_D in names, "only one re-recognise rule present"
        return False
    rr_t, rr_d = build_rerecognize(rules)
    at = rule_named(rules, "sd_recognize_dim")
    rules.insert(at + 1, rr_t)
    rules.insert(at + 2, rr_d)
    return True


def bump_description(d):
    if d["version"] in (NEW_VERSION, LATEST_VERSION):
        return False
    assert d["version"] == OLD_VERSION, f"expected version {OLD_VERSION}, found {d['version']}"
    d["version"] = NEW_VERSION
    d["description"] = d["description"] + (
        f" v{NEW_VERSION} ({BLOCK}): D1, sd_rerecognize_transformed and sd_rerecognize_dim "
        "re-recognise a decoded observation that already has a has_transform edge once a grown "
        "codebook explains it (status and covered_by only; the Transform stays the first-recognition "
        "receipt and no second one is minted); D2, sd_recognize.covered_by and sd_mint_quantum.closest_held_shape score "
        "parts with the ClosestShape Term, so a JSON-string signature matches the same way a "
        "native-list signature does."
    )
    return True


def add_gen_resets(rules):
    """G1 (block 372000): sd_redecode also clears gen_checked and gen_explained on re-arm.

    Inserts the two resets directly after the existing dim_explained reset, and
    appends one sentence to the sd_redecode comment. Idempotent.
    """
    rule = rules[rule_named(rules, "sd_redecode")]
    fx = rule["effects"]
    assert GEN_RESET_ANCHOR in fx, f"sd_redecode has no {GEN_RESET_ANCHOR} effect to follow"
    changed = False
    pos = fx.index(GEN_RESET_ANCHOR) + 1
    for eff in GEN_RESETS:
        if eff in fx:
            continue
        fx.insert(pos, copy.deepcopy(eff))
        pos += 1
        changed = True
    if GEN_BLOCK not in rule["comment"]:
        rule["comment"] = rule["comment"] + (
            f" {GEN_BLOCK} (v1.19.0): sd_redecode also clears gen_checked and gen_explained, so the "
            "GenInfer guards take a fresh look at the grown codebook rather than reading a verdict "
            "made before the growth."
        )
        changed = True
    return changed


def bump_latest(d):
    """v1.18.0 -> v1.19.0 (block 372000). Returns True when the version moved."""
    if d["version"] == LATEST_VERSION:
        return False
    assert d["version"] == NEW_VERSION, f"expected version {NEW_VERSION}, found {d['version']}"
    d["version"] = LATEST_VERSION
    d["description"] = d["description"] + (
        f" v{LATEST_VERSION} ({GEN_BLOCK}): sd_redecode also sets gen_checked and gen_explained "
        "back to 0 on re-arm, alongside the transform and dimension flags. Before this, the eight "
        "GenInfer guards (sd_gen_check*, sd_mint_generator, sd_mint_quantum_generator, sd_mint_quantum, "
        "sd_dedup_existing, sd_recognize_at_grain, sd_mdl_outliers) could read a GenInfer verdict made "
        "against the codebook before the growth: a gen_checked observation with gen_explained not 1 "
        "skipped a fresh look, and a gen_explained observation could be recognised from the old "
        "verdict. The clears use the 0-is-falsy idiom of the other re-arm resets. Specified in "
        "SD_LOOP_GEN_REARM_AND_TIE_PARITY_PREREG.md, gap G1."
    )
    return True


def main():
    raw = SEED.read_text(encoding="utf-8")
    d = json.loads(raw)
    rules = d["rules"]
    changed = []
    changed += [f"ClosestShape:{n}" for n in replace_sites(rules)]
    if insert_rerecognize(rules):
        changed.append("insert:" + RERECOGNIZE_T + "," + RERECOGNIZE_D)
    if bump_description(d):
        changed.append("version")
    if add_gen_resets(rules):
        changed.append("sd_redecode:gen_checked,gen_explained")
    if bump_latest(d):
        changed.append("version-1.19.0")
    text = json.dumps(d, indent=1) + "\n"
    if text != raw:
        SEED.write_text(text, encoding="utf-8")
        print("wrote", SEED.relative_to(ROOT), "changes:", ", ".join(changed))
    else:
        print("no change:", SEED.relative_to(ROOT), "(already applied)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
