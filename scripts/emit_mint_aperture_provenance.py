#!/usr/bin/env python3
"""WP1 emitter: add mint-site aperture provenance to seeds/shape_decode_loop.json.

Idempotent: re-running replaces the provenance effects rather than
duplicating them. The shared idiom (`provenance_effects`) is the single place
that decides what a mint records, so further mint sites adopt it by calling
the same function (RECURSIVE_SELF_IMPROVEMENT_PLAN_20261006.md, WP1).

Recorded on the minted node, first mint wins (a dedup'd rediscovery keeps the
original provenance):
  minted_aperture  -- the dimensions the minting observation resolved: its
                      `aperture` attr when an observer projected it, else its
                      own `dim_types` (full resolution of that frame).
  minted_grain     -- the observation's per-dimension `grain` map, if any.
  minted_dim_types -- the frame's slot typing.
  minted_from_signature -- the relations the mint was formed from.
  minted_epoch     -- the agent's codebook_epoch at mint time.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds/shape_decode_loop.json"
PROV_KEYS = ("minted_aperture", "minted_grain", "minted_dim_types", "minted_from_signature", "minted_epoch")


def V(name):
    return {"type": "Var", "name": name}


def A(node, key):
    return {"type": "Attr", "node": V(node), "key": key}


def keep_first(node, key, value):
    """IfThenElse(node.key is None, value, node.key) -- first mint wins."""
    return {"__term__": {"type": "IfThenElse",
                         "cond": {"type": "Eq", "a": A(node, key), "b": {"type": "Lit", "value": None}},
                         "then": value, "other": A(node, key)}}


def provenance_effects(minted: str, obs: str = "obs", agent: str = "ag", signature_key: str = "signature",
                       epoch_key: str = "codebook_epoch"):
    aperture = {"type": "IfThenElse",
                "cond": {"type": "Eq", "a": A(obs, "aperture"), "b": {"type": "Lit", "value": None}},
                "then": A(obs, "dim_types"), "other": A(obs, "aperture")}
    return [
        ["set_attr", minted, "minted_aperture", keep_first(minted, "minted_aperture", aperture)],
        ["set_attr", minted, "minted_grain", keep_first(minted, "minted_grain", A(obs, "grain"))],
        ["set_attr", minted, "minted_dim_types", keep_first(minted, "minted_dim_types", A(obs, "dim_types"))],
        ["set_attr", minted, "minted_from_signature", keep_first(minted, "minted_from_signature", A(obs, signature_key))],
        ["set_attr", minted, "minted_epoch", keep_first(minted, "minted_epoch", A(agent, epoch_key))],
    ]


SITES = {  # rule name -> (minted var, signature key on obs)
    "sd_mint_quantum": ("axis", "residual"),
    "sd_mint_generator": ("g", "signature"),
    "sd_mint_quadratic_generator": ("g", "signature"),
    "sd_recognize_dim": ("ld", "signature"),
}


# Mint sites outside the sd loop (tranche 2 gate 6): seed -> rule -> (minted var, signature key, epoch key).
OTHER_SITES = {
    "meta_shape_growth": {"msg_mint_shape": ("ms", "signature", "meta_codebook_epoch")},
    "problem_shape_growth": {"ps_mint": ("ps", "signature", "problem_codebook_epoch")},
}


def apply_other_sites() -> None:
    for seed_id, sites in OTHER_SITES.items():
        path = ROOT / "seeds" / f"{seed_id}.json"
        text = path.read_text()
        seed = json.loads(text)
        for rule in seed["rules"]:
            if rule["name"] not in sites:
                continue
            var, sig, ep = sites[rule["name"]]
            if {e[2] for e in rule["effects"] if e[0] == "set_attr" and e[1] == var} >= set(PROV_KEYS):
                continue
            rule["effects"] = [e for e in rule["effects"]
                               if not (e[0] == "set_attr" and e[1] == var and e[2] in PROV_KEYS)]
            rule["effects"].extend(provenance_effects(var, signature_key=sig, epoch_key=ep))
        out = json.dumps(seed, indent=1, ensure_ascii=True)
        path.write_text(out + ("\n" if text.endswith("\n") else ""))
        print("updated", path.relative_to(ROOT))


def main() -> int:
    apply_other_sites()
    text = SEED.read_text()
    seed = json.loads(text)
    for rule in seed["rules"]:
        if rule["name"] not in SITES:
            continue
        var, sig = SITES[rule["name"]]
        if {e[2] for e in rule["effects"] if e[0] == "set_attr" and e[1] == var} >= set(PROV_KEYS):
            continue                     # already applied: leave effect order untouched
        rule["effects"] = [e for e in rule["effects"]
                           if not (e[0] == "set_attr" and e[1] == var and e[2] in PROV_KEYS)]
        rule["effects"].extend(provenance_effects(var, signature_key=sig))
    note = (" v1.10.0 (2026-10-06, RECURSIVE_SELF_IMPROVEMENT_PLAN WP1, MINTING_AT_APERTURE.md): every"
            " sd-loop mint (CapabilityAxis, linear/quadratic DimensionGenerator, LatentDimension) records the"
            " aperture it was minted at -- minted_aperture (the observation's projected `aperture` if an observer"
            " set one, else its own dim_types), minted_grain, minted_dim_types, minted_from_signature,"
            " minted_epoch -- via the shared idiom in scripts/emit_mint_aperture_provenance.py. First mint wins"
            " (IfThenElse on the existing value), so dedup keys and dedup'd rediscovery are unchanged; no guard"
            " reads these attrs, so recognition/mint decisions are byte-identical.")
    if "v1.10.0" not in seed["description"]:
        seed["description"] += note
    seed["version"] = max(seed["version"], "1.10.0", key=lambda v: tuple(map(int, v.split("."))))
    out = json.dumps(seed, indent=1, ensure_ascii=True)
    if text.endswith("\n"):
        out += "\n"
    SEED.write_text(out)
    print("updated", SEED.relative_to(ROOT), "sites:", ", ".join(SITES))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
