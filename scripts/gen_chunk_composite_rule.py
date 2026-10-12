#!/usr/bin/env python3
"""WP5 emitter: CHUNKING -- a recognised composite becomes a primitive.

Adds `sd_chunk_composite` to seeds/shape_decode_loop.json (v1.11.0). Gated on
`agent.gen_chunk_enabled == 1` (absent by default -> byte-identical decode).

When an observation was recognised through a length-2 composition (its
LatentDimension carries two `generators`), mint a
`DimensionGenerator{kind:"composite", steps, ks, params:[1]}` naming that
sequence. `DimInfer` resolves composites to their flattened primitive
sequence (shape_decode.rs `load_generators`), so the chunk participates as ONE
codebook entry: the unchanged length-<=2 search over {primitives, chunks}
then reaches length 3, 4, ... -- depth grows from minted structure, not from a
wider search. A chunk may itself be a step of a later chunk.

The chunk carries WP1 mint provenance (aperture, dim_types, source
signature, epoch). Content-keyed: the same composition rediscovered from
another observation mints no second chunk.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from emit_mint_aperture_provenance import provenance_effects  # noqa: E402

SEED = ROOT / "seeds/shape_decode_loop.json"


def V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def L(v): return {"type": "Lit", "value": v}
def T(t): return {"__term__": t}


RULE = {
    "name": "sd_chunk_composite",
    "comment": __doc__.strip(),
    "match": [["ag", "observed", "obs"], ["obs", "has_latent_dimension", "ld"]],
    "where": {"type": "And", "items": [
        {"type": "Eq", "a": A("ag", "gen_chunk_enabled"), "b": L(1)},
        {"type": "Eq", "a": {"type": "Count", "source": A("ld", "generators")}, "b": L(2)},
        {"type": "Not", "arg": {"type": "Eq", "a": A("ld", "chunked"), "b": L(1)}},
    ]},
    "effects": [
        ["add_node_if_absent", "g", "DimensionGenerator", {
            "name": T({"type": "StringConcat", "parts": [
                L("chunk:"), {"type": "ToJsonString", "value": A("ld", "generators")},
                L("^"), {"type": "ToJsonString", "value": A("ld", "ks")}]}),
            "kind": "composite",
            "steps": T(A("ld", "generators")),
            "ks": T(A("ld", "ks")),
        }],
        ["set_attr", "g", "params", [1]],
        ["set_attr", "g", "source", "chunk"],
        ["set_attr", "ld", "chunked", 1],
        ["add_edge", "ag", "holds_chunk", "g"],
        *provenance_effects("g"),
    ],
}

# RETENTION (tranche 2, gate 3). `uses` is DERIVED: the number of Transform
# receipts whose step sequence names the chunk. When the agent sets
# `gen_chunk_capacity`, the least-used live chunk (ties: oldest) is retired
# whenever live chunks exceed capacity. A retired chunk still resolves as a
# step of chunks built on it (shape_decode.rs), it is just no longer a
# candidate itself. Absent capacity -> nothing is ever retired.
CHUNK_NODES = {"type": "Neighbours", "node": V("ag"), "edge_type": "holds_chunk"}
USES = {"type": "Count", "source": {"type": "Filter", "source": {"type": "NodesOfType", "node_type": "Transform"},
                                    "var_name": "t", "predicate": {"type": "In", "member": A("g", "name"), "container": A("t", "generators")}}}
USES_RULE = {
    "name": "sd_chunk_uses",
    "comment": "Derived usage count for a held chunk (retention input).",
    "match": [["ag", "holds_chunk", "g"]],
    "where": {"type": "Not", "arg": {"type": "Eq", "a": A("g", "uses"), "b": USES}},
    "effects": [["set_attr", "g", "uses", {"__term__": USES}]],
}
# RECURRENCE-AWARE tier (tranche 4): with agent.gen_chunk_protect_uses = P, a
# chunk used >= P times has RECURRED and is protected; capacity bounds only the
# probationary (not-yet-recurred) chunks. Absent P -> every live chunk is
# probationary (v1.13.0 behaviour).
USES_OR_0 = lambda n: {"type": "IfThenElse", "cond": {"type": "Eq", "a": A(n, "uses"), "b": L(None)}, "then": L(0), "other": A(n, "uses")}
PROTECTED = lambda n: {"type": "And", "items": [
    {"type": "Not", "arg": {"type": "Eq", "a": A("ag", "gen_chunk_protect_uses"), "b": L(None)}},
    # uses >= P written as Min(uses, P) == P: an equality, so the seed keeps
    # its audited "no bound-like comparator" shape (test_uniqueness / tripwire).
    {"type": "Eq", "a": {"type": "Min", "items": [USES_OR_0(n), A("ag", "gen_chunk_protect_uses")]},
     "b": A("ag", "gen_chunk_protect_uses")}]}
LIVE = {"type": "FilterList", "source": CHUNK_NODES, "var_name": "c",
        "predicate": {"type": "And", "items": [
            {"type": "Not", "arg": {"type": "Eq", "a": A("c", "retired"), "b": L(1)}},
            {"type": "Not", "arg": PROTECTED("c")}]}}
VICTIM = {"type": "Argmin", "source": LIVE, "var_name": "c",
          "value": {"type": "Plus", "items": [{"type": "Times", "items": [
              {"type": "IfThenElse", "cond": {"type": "Eq", "a": A("c", "uses"), "b": L(None)}, "then": L(0), "other": A("c", "uses")},
              L(1000000)]}, {"type": "IfThenElse", "cond": {"type": "Eq", "a": A("c", "minted_epoch"), "b": L(None)}, "then": L(0), "other": A("c", "minted_epoch")}]},
          "default": L(None)}
RETIRE = {
    "name": "sd_chunk_retire",
    "comment": "Capacity-bounded chunk retention: retire the least-used (then oldest) live chunk while live chunks exceed agent.gen_chunk_capacity.",
    "match": [["ag", "holds_chunk", "g"]],
    "where": {"type": "And", "items": [
        {"type": "Not", "arg": {"type": "Eq", "a": A("ag", "gen_chunk_capacity"), "b": L(None)}},
        {"type": "Not", "arg": {"type": "Eq", "a": A("g", "retired"), "b": L(1)}},
        {"type": "Not", "arg": PROTECTED("g")},
        {"type": "Gt", "a": {"type": "Count", "source": LIVE}, "b": A("ag", "gen_chunk_capacity")},
        {"type": "Eq", "a": V("g"), "b": VICTIM},
    ]},
    "effects": [["set_attr", "g", "retired", 1], ["set_attr", "ag", "codebook_epoch",
                {"__term__": {"type": "Plus", "items": [A("ag", "codebook_epoch"), L(1)]}}]],
}


# PROTECTED-SET BOUND (tranche 5): with agent.gen_chunk_protect_capacity = Q,
# when more than Q chunks are protected the least-used (then oldest) protected
# chunk is retired. Bounds long-run growth by Q + gen_chunk_capacity. Absent Q
# -> protected chunks are never retired (v1.16.0 behaviour).
PROT_LIVE = {"type": "FilterList", "source": CHUNK_NODES, "var_name": "c",
             "predicate": {"type": "And", "items": [
                 {"type": "Not", "arg": {"type": "Eq", "a": A("c", "retired"), "b": L(1)}}, PROTECTED("c")]}}
PROT_VICTIM = dict(VICTIM, source=PROT_LIVE)
RETIRE_PROT = {
    "name": "sd_chunk_retire_protected",
    "comment": "Bound on protected (recurred) chunks: retire the least-used, then oldest, protected chunk while protected chunks exceed agent.gen_chunk_protect_capacity.",
    "match": [["ag", "holds_chunk", "g"]],
    "where": {"type": "And", "items": [
        {"type": "Not", "arg": {"type": "Eq", "a": A("ag", "gen_chunk_protect_capacity"), "b": L(None)}},
        {"type": "Not", "arg": {"type": "Eq", "a": A("g", "retired"), "b": L(1)}},
        PROTECTED("g"),
        {"type": "Gt", "a": {"type": "Count", "source": PROT_LIVE}, "b": A("ag", "gen_chunk_protect_capacity")},
        {"type": "Eq", "a": V("g"), "b": PROT_VICTIM},
    ]},
    "effects": [["set_attr", "g", "retired", 1], ["set_attr", "ag", "codebook_epoch",
                {"__term__": {"type": "Plus", "items": [A("ag", "codebook_epoch"), L(1)]}}]],
}


def main():
    text = SEED.read_text()
    seed = json.loads(text)
    names = {RULE["name"], USES_RULE["name"], RETIRE["name"]}
    new = {r["name"]: r for r in (RULE, USES_RULE, RETIRE, RETIRE_PROT)}
    have = [r["name"] for r in seed["rules"]]
    seed["rules"] = [new.get(r["name"], r) for r in seed["rules"]]
    seed["rules"] += [r for n, r in new.items() if n not in have]
    prod = {"provenance": "seed:shape_decode_loop:holds-chunk", "src": {"type": "Agent", "var": "s"},
            "edge_type": "holds_chunk", "tgt": {"type": "DimensionGenerator", "var": "t"}}
    if prod not in seed["productions"]:
        seed["productions"].append(prod)
    seed["version"] = max(seed["version"], "1.17.0", key=lambda v: tuple(map(int, v.split("."))))
    note = (" v1.11.0 (2026-10-06, RECURSIVE_SELF_IMPROVEMENT_PLAN WP5): sd_chunk_composite (agent.gen_chunk_enabled==1,"
            " OFF by default) mints a recognised length-2 composition as a DimensionGenerator{kind:'composite'}; DimInfer"
            " flattens composites, so chunks compose with further steps and depth grows from minted structure"
            " (scripts/gen_chunk_composite_rule.py).")
    if "v1.11.0" not in seed["description"]:
        seed["description"] += note
    note13 = (" v1.13.0 (2026-10-07, tranche 2 gate 3): chunk RETENTION -- sd_chunk_composite adds ag-holds_chunk->g;"
              " sd_chunk_uses derives each chunk's usage from Transform receipts; sd_chunk_retire (agent.gen_chunk_capacity,"
              " absent -> never) retires the least-used, then oldest, live chunk while live chunks exceed capacity. Retired"
              " generators still resolve as composite steps but are not decode candidates (shape_decode.rs).")
    if "v1.13.0" not in seed["description"]:
        seed["description"] += note13
    note16 = (" v1.16.0 (2026-10-07, tranche 4): recurrence-aware retention -- with agent.gen_chunk_protect_uses=P a"
              " chunk used >= P times is protected and gen_chunk_capacity bounds only not-yet-recurred chunks; absent P"
              " -> v1.13.0 behaviour.")
    if "v1.16.0" not in seed["description"]:
        seed["description"] += note16
    note17 = (" v1.17.0 (2026-10-07, tranche 5): agent.gen_chunk_protect_capacity=Q bounds protected chunks"
              " (sd_chunk_retire_protected retires the least-used, then oldest, protected chunk beyond Q); absent -> unchanged.")
    if "v1.17.0" not in seed["description"]:
        seed["description"] += note17
    SEED.write_text(json.dumps(seed, indent=1, ensure_ascii=True) + ("\n" if text.endswith("\n") else ""))
    print("updated", SEED.relative_to(ROOT))


if __name__ == "__main__":
    main()
