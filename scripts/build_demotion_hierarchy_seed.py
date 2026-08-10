#!/usr/bin/env python3
"""AUTHORING SCRIPT — emits seeds/demotion_hierarchy.json (seed block 198000).

Not agent runtime. Constructs the DEMOTION HIERARCHY seed on top of 196000's
staleness_decay atom: freshness-thresholded tiers (FRESH/GIST/LATENT), a demote
atom that COARSENS the stored representation (integer bit-plane shed) and NEVER
deletes, a promote-on-refresh rule (reversible recall), and — as a SEPARATE,
high-order, bottom-tier-gated faculty with its own flag — the ONLY rule that
deletes. All Terms integer-native (Ashr / Shl / IDiv / IfThenElse / Gte / Eq).
No Rust, no new Term. Prereg: VISION_DEMOTION_HIERARCHY_PREREG.md.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


# --- Term constructors (integer-native) ------------------------------------
def V(name):
    return {"type": "Var", "name": name}


def A(var, key):
    return {"type": "Attr", "node": V(var), "key": key}


def L(x):
    return {"type": "Lit", "value": float(x)}


def Ashr(a, b):
    return {"type": "Ashr", "a": a, "b": b}


def Shl(a, b):
    return {"type": "Shl", "a": a, "b": b}


def IDiv(a, b):
    return {"type": "IDiv", "a": a, "b": b}


def Minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def Gte(a, b):
    return {"type": "Gte", "a": a, "b": b}


def Gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def And(*items):
    return {"type": "And", "items": list(items)}


def Ite(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def sattr(var, key, term):
    return ["set_attr", var, key, {"__term__": term}]


ENABLED = Eq(A("tp", "enabled"), L(1.0))

# match skeleton shared by the tier/demote/promote/freshness rules
MATCH = [
    ["retina", "has_hier_tier_params", "tp"],
    ["retina", "has_hier_trace", "tr"],
]


def freshness_term():
    # freshness = Ashr(c0, IDiv(now_epoch - last_refresh_epoch, half_life))
    # byte-structurally identical to staleness_decay's sd_freshness_generic.
    return Ashr(
        A("tp", "c0"),
        IDiv(Minus(A("tr", "now_epoch"), A("tr", "last_refresh_epoch")),
             A("tr", "half_life")),
    )


def tier_term():
    # tier = ite(freshness>=T_FRESH, 2, ite(freshness>=T_GIST, 1, 0))
    return Ite(
        Gte(A("tr", "freshness"), A("tp", "t_fresh")),
        L(2.0),
        Ite(Gte(A("tr", "freshness"), A("tp", "t_gist")), L(1.0), L(0.0)),
    )


def stored_term():
    # FRESH -> detail (full); GIST -> Ashr(detail, k_gist) (LOD shed); LATENT -> 0
    return Ite(
        Eq(A("tr", "tier"), L(2.0)),
        A("tr", "detail"),
        Ite(Eq(A("tr", "tier"), L(1.0)),
            Ashr(A("tr", "detail"), A("tp", "k_gist")),
            L(0.0)),
    )


def bits_term():
    # storage cost per tier (integer bits)
    return Ite(
        Eq(A("tr", "tier"), L(2.0)),
        A("tp", "bits_full"),
        Ite(Eq(A("tr", "tier"), L(1.0)), A("tp", "bits_gist"),
            A("tp", "bits_latent")),
    )


def recon_term():
    # cross-frame LOD reconstruction (approximate): GIST -> Shl(stored, k_gist).
    # in-frame integer; the ONLY value that crosses frames. FRESH exact, LATENT 0.
    return Ite(
        Eq(A("tr", "tier"), L(2.0)),
        A("tr", "stored"),
        Ite(Eq(A("tr", "tier"), L(1.0)),
            Shl(A("tr", "stored"), A("tp", "k_gist")),
            L(0.0)),
    )


def build():
    rules = [
        # --- THE DECAY / DEMOTE ATOM (contains NO del_node) --------------
        {
            "name": "dh_freshness", "area": "retina", "order": 2,
            "latency_class": "hard_realtime", "match": MATCH, "where": ENABLED,
            "effects": [sattr("tr", "freshness", freshness_term())],
        },
        {
            "name": "dh_tier", "area": "retina", "order": 3,
            "latency_class": "hard_realtime", "match": MATCH, "where": ENABLED,
            "effects": [sattr("tr", "tier", tier_term())],
        },
        {
            "name": "dh_demote", "area": "retina", "order": 4,
            "latency_class": "hard_realtime", "match": MATCH, "where": ENABLED,
            "effects": [
                sattr("tr", "stored", stored_term()),
                sattr("tr", "bits", bits_term()),
                sattr("tr", "recon", recon_term()),
                # present is ALWAYS 1 — the demote atom NEVER deletes.
                sattr("tr", "present", L(1.0)),
            ],
        },
        # --- PROMOTE (the refresh — reversible recall) ------------------
        {
            "name": "dh_promote", "area": "retina", "order": 1,
            "latency_class": "hard_realtime", "match": MATCH,
            "where": And(ENABLED,
                         Gt(A("tr", "obs_epoch"), A("tr", "last_refresh_epoch"))),
            "effects": [
                sattr("tr", "last_refresh_epoch", A("tr", "obs_epoch")),
                sattr("tr", "detail", A("tr", "obs_detail")),
            ],
        },
        # --- THE SEPARATE ORDER-N DELETION FACULTY ----------------------
        # The ONLY rule with del_node. Own flag (delete_enabled), own high
        # order (9), gated at the BOTTOM (LATENT) tier only + eviction age.
        # NOT part of the decay atom. Deletion is the fall off the bottom.
        {
            "name": "dh_delete_latent", "area": "retina", "order": 9,
            "latency_class": "background", "match": MATCH,
            "where": And(
                ENABLED,
                Eq(A("tp", "delete_enabled"), L(1.0)),
                Eq(A("tr", "tier"), L(0.0)),
                Gt(Minus(A("tr", "now_epoch"), A("tr", "last_refresh_epoch")),
                   A("tp", "evict_age")),
            ),
            "effects": [["del_node", "tr"]],
        },
    ]

    seed = {
        "id": "demotion_hierarchy",
        "version": "1.0.0",
        "self_load_only": True,
        "depends_on": ["staleness_decay"],
        "area": "retina",
        "description": (
            "DEMOTION HIERARCHY (block 198000) on top of 196000's staleness_decay "
            "atom. A held trace carries integer freshness = Ashr(C0, IDiv(dEpoch, "
            "half_life)); freshness-thresholded TIERS (FRESH>=t_fresh / GIST>=t_gist "
            "/ LATENT) drive a DEMOTE atom (dh_tier + dh_demote) that COARSENS the "
            "stored representation as freshness decays WITHOUT refresh: FRESH keeps "
            "full detail, GIST sheds it to Ashr(detail,k_gist) (an integer bit-plane "
            "LOD summary), LATENT keeps only a presence marker (stored=0, present=1). "
            "THE DEMOTE ATOM ONLY EVER DEMOTES -- freshness->0 leaves a LATENT trace, "
            "NEVER an empty cell; it contains no del_node. dh_promote resets the "
            "innovation clock on a new observation so the trace climbs back to FRESH "
            "and RECOVERS full detail from the incoming data (reversible recall / "
            "DRAM-refresh). Deletion is a SEPARATE, high-order (9), bottom-tier-gated "
            "faculty (dh_delete_latent) behind its own delete_enabled flag -- the "
            "ONLY rule that deletes, never wired into decay. Integer-native (Ashr / "
            "Shl / IDiv / IfThenElse / Gte / Eq); only the cross-frame recon uses a "
            "shift. OFF by default: rules need a HeldTierParams node the adapter "
            "creates only on opt-in; absent it every existing path is byte-identical. "
            "NO Rust, NO new Term."),
        "microtheory": {
            "name": "demotion_hierarchy",
            "description": (
                "Decay DEMOTES, it does not DELETE. Freshness-thresholded tiers "
                "coarsen a trace's representation (registers->L1->disk / episodic->"
                "semantic gist / cache eviction); re-observation promotes it back; "
                "deletion is a separate bottom-tier faculty."),
        },
        "nodes": [],
        "edges": [],
        "productions": [
            {
                "provenance": "seed:demotion_hierarchy:retina-tier-params",
                "src": {"type": "Retina", "var": "retina"},
                "edge_type": "has_hier_tier_params",
                "tgt": {"type": "HeldTierParams", "var": "tp"},
            },
            {
                "provenance": "seed:demotion_hierarchy:retina-hier-trace",
                "src": {"type": "Retina", "var": "retina"},
                "edge_type": "has_hier_trace",
                "tgt": {"type": "HierTrace", "var": "tr"},
            },
        ],
        "rules": rules,
    }
    return seed


def main():
    seed = build()
    path = os.path.join(ROOT, "seeds", "demotion_hierarchy.json")
    with open(path, "w") as fh:
        json.dump(seed, fh, indent=1)
        fh.write("\n")
    print("wrote", path, "rules:", [r["name"] for r in seed["rules"]])


if __name__ == "__main__":
    main()
