#!/usr/bin/env python3
"""Construct the GEN-MINT rules IN-PLACE in `seeds/shape_decode_loop.json`
(deterministic, idempotent).

The gen-mint machinery is gated on a GRAPH-DATA agent flag
`gen_infer_enabled` (default ABSENT ⇒ OFF), exactly like §9's `bcm=0` /
`oja=0` — an ablation expressed as data on the agent, never a Python code
path or a separately-loaded seed (a separate seed loads at a LOWER priority
tier, so the default-tier `sd_mint_quantum` would mint the quantum before it
ran — the race this design avoids). All rules live in ONE tier so guards,
not load order, decide.

Edits:
  - `sd_mint_quantum` / `sd_dedup_existing` gain `gen_checked == 1` AND
    `gen_explained != 1`: the novelty path waits for the generator rung and
    only mints a flat quantum when generator inference was CHECKED and
    FAILED (or is OFF — then `gen_explained` is absent, `!= 1` holds).
  - `sd_gen_check_mark` (flag OFF, Term-free): sets `gen_checked = 1` at the
    gap so `sd_mint_quantum` stays satisfiable and byte-identical when
    gen-mint is off (the exact mirror of `sd_dim_check_mark`).
  - `sd_gen_check` (flag ON): runs the `GenInfer` Term, setting
    `gen_checked = 1` AND `gen_explained` — atomically, one rule, same tier,
    so there is never a state where `gen_checked == 1` but the look hasn't
    happened (the invariant `sd_infer_dimension` keeps for the dim rung).
  - `sd_mint_generator` (flag ON): on `gen_explained == 1` and no linear
    generator yet, MINTS `DimensionGenerator{kind:"linear", matrix,
    coord_dims}` from GenInfer's inferred matrix and bumps `codebook_epoch`,
    so `sd_redecode` re-arms and the orbit re-decodes THROUGH the minted
    generator — collapse to one generator instead of N quanta.
"""
from __future__ import annotations
import json, os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SD = os.path.join(HERE, "seeds", "shape_decode_loop.json")


def A(key, node="obs"):
    return {"type": "Attr", "node": {"type": "Var", "name": node}, "key": key}


def eq(key, val, node="obs"):
    return {"type": "Eq", "a": A(key, node), "b": {"type": "Lit", "value": val}}


def neq(key, val, node="obs"):
    return {"type": "Not", "arg": eq(key, val, node)}


def count_gt0(key):
    return {"type": "Gt", "a": {"type": "Count", "source": A(key)},
            "b": {"type": "Lit", "value": 0}}


def neighbours_count0(edge):
    return {"type": "Eq",
            "a": {"type": "Count", "source": {"type": "Neighbours",
                  "node": {"type": "Var", "name": "obs"}, "edge_type": edge}},
            "b": {"type": "Lit", "value": 0}}


# The gap: held rungs 1 and 2 have both had their look and FAILED.
GAP = lambda: [eq("status", "decoded"), count_gt0("residual"),
               eq("transform_checked", 1), neq("transform_explained", 1),
               eq("dim_checked", 1), neq("dim_explained", 1)]


def geninfer(field):
    return {"type": "GenInfer", "goal": A("signature"), "max_dims": 2, "field": field}


NEW_RULE_NAMES = ("sd_gen_check_mark", "sd_gen_check", "sd_mint_generator")


def _is_gen_guard(c):
    def key_of(cond):
        try:
            if cond.get("type") == "Eq":
                return cond["a"].get("key")
            if cond.get("type") == "Not":
                return cond["arg"]["a"].get("key")
        except Exception:
            return None
    return key_of(c) in ("gen_checked", "gen_explained")


def build():
    d = json.load(open(SD))
    rules = {r.get("name"): r for r in d["rules"]}

    # (1) gate the two novelty rules on the generator rung.
    for nm in ("sd_mint_quantum", "sd_dedup_existing"):
        items = rules[nm]["where"]["items"]
        items[:] = [c for c in items if not _is_gen_guard(c)]
        items.append(eq("gen_checked", 1))
        items.append(neq("gen_explained", 1))

    # (2) the three gen rules (idempotent: drop any prior copies first).
    d["rules"] = [r for r in d["rules"] if r.get("name") not in NEW_RULE_NAMES]

    mark = {
        "name": "sd_gen_check_mark",
        "comment": (
            "RESILIENCE MARKER for the generator rung, flag OFF — the twin of "
            "sd_dim_check_mark one rung deeper. Gated on agent.gen_infer_"
            "enabled != 1 (the DEFAULT: the flag is absent), it sets "
            "gen_checked=1 at the gap so sd_mint_quantum's new guard stays "
            "satisfiable while gen_explained stays ABSENT (!=1) — so the "
            "quantum mints EXACTLY as before gen-mint existed (§9). "
            "Mutually exclusive with sd_gen_check by the flag, so neither "
            "preempts the other."),
        "match_type": "Observation",
        "match": [["ag", "observed", "obs"]],
        "where": {"type": "And", "items": [
            *GAP(), neq("gen_infer_enabled", 1, node="ag"), neq("gen_checked", 1)]},
        "effects": [["set_attr", "obs", "gen_checked", 1]],
    }
    check = {
        "name": "sd_gen_check",
        "comment": (
            "THE GENERATOR-INFERENCE LOOK, flag ON (agent.gen_infer_enabled==1). "
            "The DELTA on DimInfer: at the gap where the held DimensionGenerator "
            "codebook is exhausted WITHOUT a match, run the GenInfer Term — "
            "DimInfer-native generate-and-test over the PARAMETERIZED FAMILY of "
            "integer 2x2 linear maps within a DATA-DERIVED entry bound, applied "
            "via the SAME apply_linear_once a minted generator uses and verified "
            "via the SAME build_candidate check DimInfer runs. Sets gen_checked=1 "
            "AND gen_explained ATOMICALLY (one rule, one tier) so sd_mint_quantum "
            "never sees gen_checked==1 without the look having happened."),
        "match_type": "Observation",
        "match": [["ag", "observed", "obs"]],
        "where": {"type": "And", "items": [
            *GAP(), eq("gen_infer_enabled", 1, node="ag"), neq("gen_checked", 1)]},
        "effects": [
            ["set_attr", "obs", "gen_checked", 1],
            ["set_attr", "obs", "gen_explained", {"__term__": geninfer("explained")}],
        ],
    }
    mint = {
        "name": "sd_mint_generator",
        "comment": (
            "MINT A NEW GENERATOR FROM THE ORBIT (flag ON) — the operation the "
            "arc's negative said the sd loop lacks ('composes what it holds; "
            "does not discover what it lacks'). On gen_explained==1 (GenInfer "
            "found a NEW integer-linear map no held generator explains) and no "
            "linear generator minted yet, add DimensionGenerator{kind:'linear', "
            "matrix, coord_dims} carrying GenInfer's inferred matrix as GRAPH "
            "DATA (apply_linear_once reads it — no new Rust dispatch arm per "
            "discovered map) and bump codebook_epoch so sd_redecode re-arms the "
            "observation; it re-decodes THROUGH the minted generator "
            "(recognized_transformed, NOT a quantum) — the orbit collapses to "
            "one generator. Dedup: one linear generator per boot (a fuller "
            "matrix-keyed dedup for multiple coexisting discovered generators "
            "is a documented scope limit)."),
        "match_type": "Observation",
        "match": [["ag", "observed", "obs"]],
        "where": {"type": "And", "items": [
            eq("status", "decoded"), count_gt0("residual"),
            neighbours_count0("minted"),
            eq("transform_checked", 1), neq("transform_explained", 1),
            eq("dim_checked", 1), neq("dim_explained", 1),
            eq("gen_infer_enabled", 1, node="ag"),
            eq("gen_checked", 1), eq("gen_explained", 1),
            {"type": "Not", "arg": {
                "type": "Exists",
                "source": {"type": "NodesOfType", "node_type": "DimensionGenerator"},
                "var_name": "g", "predicate": eq("kind", "linear", node="g")}},
        ]},
        "effects": [
            ["add_node", "g", "DimensionGenerator", {
                "name": {"__term__": {"type": "StringConcat", "parts": [
                    {"type": "Lit", "value": "genlin_"}, geninfer("base")]}},
                "kind": {"__term__": {"type": "Lit", "value": "linear"}},
                "coord_dims": {"__term__": geninfer("coord_dims")},
                "matrix": {"__term__": geninfer("matrix")},
                "params": {"__term__": {"type": "Lit", "value": [1, 2, 3, 4, 5, 6]}},
                "minted_from_orbit": {"__term__": {"type": "Lit", "value": 1.0}},
            }],
            ["add_edge", "obs", "gen_minted", "g"],
            ["set_attr", "ag", "codebook_epoch", {"__term__": {
                "type": "Plus", "items": [A("codebook_epoch", "ag"),
                                          {"type": "Lit", "value": 1}]}}],
            # Re-arm via the EXACT quantum-growth path: status 'minted' +
            # decoded_epoch behind the bumped codebook_epoch makes sd_redecode
            # re-arm this observation to 'pending', so it re-decodes THROUGH
            # the freshly-minted generator (DimInfer now matches it) and lands
            # on recognized_transformed — collapse, no quantum. The 'minted'
            # label is transient (final status is recognized_transformed) and
            # reuses the committed growth loop rather than duplicating it.
            ["set_attr", "obs", "status", "minted"],
        ],
    }

    # place the gen rules right after sd_dim_check_mark for readability
    out = []
    for r in d["rules"]:
        out.append(r)
        if r.get("name") == "sd_dim_check_mark":
            out.extend([mark, check, mint])
    d["rules"] = out
    d["version"] = "1.7.0"
    json.dump(d, open(SD, "w"), indent=1)
    print(f"wrote {SD} (version {d['version']}, {len(d['rules'])} rules)")
    print("rules:", [r["name"] for r in d["rules"]])


if __name__ == "__main__":
    build()
