#!/usr/bin/env python3
"""Emit seeds/problem_shape_growth.json programmatically -- avoids hand-
nested-brace JSON errors for the `ps_mint` rule's deeply-nested Term tree.
Mirrors the house convention `tools/build_meta_shape_growth_seed.py`
established: the seed is GENERATED, never hand-edited. See
QUESTION_DRIVER_RUNG3_PREREG.md / _RESULTS.md for the design this seed
implements.
"""
import json
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "seeds", "problem_shape_growth.json")


def var(name):
    return {"type": "Var", "name": name}


def attr(node, key):
    return {"type": "Attr", "node": var(node), "key": key}


def lit(value):
    return {"type": "Lit", "value": value}


def eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def and_(*items):
    return {"type": "And", "items": list(items)}


def or_(*items):
    return {"type": "Or", "items": list(items)}


def not_(arg):
    return {"type": "Not", "arg": arg}


def count(source):
    return {"type": "Count", "source": source}


def nodes_of_type(t):
    return {"type": "NodesOfType", "node_type": t}


def filter_(source, var_name, predicate):
    return {"type": "Filter", "source": source, "var_name": var_name, "predicate": predicate}


def neighbours(node, edge_type):
    return {"type": "Neighbours", "node": var(node), "edge_type": edge_type}


def exists(source, var_name, predicate):
    return {"type": "Exists", "source": source, "var_name": var_name, "predicate": predicate}


def argmin(source, var_name, value):
    return {"type": "Argmin", "source": source, "var_name": var_name, "value": value}


def argmax(source, var_name, value):
    return {"type": "Argmax", "source": source, "var_name": var_name, "value": value}


def in_(member, container):
    return {"type": "In", "member": member, "container": container}


def term(t):
    return {"__term__": t}


AXES = ["has_bound", "has_direction", "has_statement",
        "has_targets_correspondence", "has_targets_mt"]

DEDUCTION_SIG = sorted(
    [["has_bound", "-"], ["has_direction", "-"], ["has_statement", "yes"],
     ["has_targets_correspondence", "-"], ["has_targets_mt", "-"], ["is_a", "problem"]],
    key=lambda r: r[0])
CAN_SIG = sorted(
    [["has_bound", "-"], ["has_direction", "-"], ["has_statement", "-"],
     ["has_targets_correspondence", "-"], ["has_targets_mt", "yes"], ["is_a", "problem"]],
    key=lambda r: r[0])

DECODE_STATUSES = ["decoded", "residual", "minted"]

ps_decode = {
    "name": "ps_decode",
    "comment": ("RUNG 1, DEQUANTIZE at the problem-shape grain: a pending "
                "ProblemShapeObservation is decoded against the held ProblemShape "
                "codebook via the UNCHANGED ShapeDecode Term, pointed at "
                "codebook_type='ProblemShape'. Zero new Rust (load_parts is "
                "grain-agnostic, per META_SHAPE_FIRST_CLASS_RESULTS.md Sec3, "
                "re-confirmed for this codebook_type). Literal decode "
                "(wild_objects:false) is correct here -- no ProblemShape signature "
                "carries WILD (QUESTION_DRIVER_RUNG3_PREREG.md Sec4.1)."),
    "match_type": "ProblemShapeObservation",
    "match": [["ag", "observed_problem", "obs"]],
    "where": eq(attr("obs", "status"), lit("pending")),
    "effects": [
        ["set_attr", "obs", "residual", term({
            "type": "ShapeDecode", "goal": attr("obs", "signature"),
            "codebook_type": "ProblemShape", "beam": 3, "max_steps": 8, "cand_k": 3,
            "wild_objects": False, "field": "residual"})],
        ["set_attr", "obs", "covered_count", term({
            "type": "ShapeDecode", "goal": attr("obs", "signature"),
            "codebook_type": "ProblemShape", "beam": 3, "max_steps": 8, "cand_k": 3,
            "wild_objects": False, "field": "covered_count"})],
        ["set_attr", "obs", "decoded_epoch", term(attr("ag", "problem_codebook_epoch"))],
        ["set_attr", "obs", "status", "decoded"],
    ],
}

_covered_cond = eq(count(attr("obs", "residual")), lit(0))

ps_recognize = {
    "name": "ps_recognize",
    "comment": ("RUNG 1 HIT: an empty residual means the held ProblemShape codebook "
                "fully explains this observation's real structural facts -- "
                "recognized, no graph growth. covered_by is the SAME AntiUnify/"
                "FixedCount specificity metric sd_recognize uses, over ProblemShape "
                "instead of ShapeSignature (mirrors shape_decode_loop.json::"
                "sd_recognize's own literal-cover shape, not meta_shape_growth.json's "
                "Covers-based rung 1 -- see this seed's own description for why)."),
    "match_type": "ProblemShapeObservation",
    "match": [["ag", "observed_problem", "obs"]],
    "where": and_(eq(attr("obs", "status"), lit("decoded")), _covered_cond),
    "effects": [
        ["set_attr", "obs", "status", "recognized"],
        ["set_attr", "obs", "covered_by", term({
            "type": "Attr", "key": "name",
            "node": argmax(
                nodes_of_type("ProblemShape"), "sig",
                {"type": "FixedCount", "pattern": {
                    "type": "AntiUnify", "values": {"type": "SetT", "items": [
                        attr("obs", "signature"), attr("sig", "signature")]}}}),
        })],
    ],
}

ps_residual = {
    "name": "ps_residual",
    "comment": ("THE RESIDUAL: a decoded observation the held codebook did NOT fully "
                "explain (non-empty residual) -- this is where a genuinely novel "
                "problem structure becomes a mint CANDIDATE, mirroring "
                "seeds/meta_shape_growth.json::msg_residual's own terminal-status "
                "role (there reached only after rungs 1-3 + the keyword prior all "
                "failed; here reached directly after rung 1, since rungs 2/3 are not "
                "wired at this grain -- Sec4.1 of the prereg)."),
    "match_type": "ProblemShapeObservation",
    "match": [["ag", "observed_problem", "obs"]],
    "where": and_(eq(attr("obs", "status"), lit("decoded")), not_(_covered_cond)),
    "effects": [["set_attr", "obs", "status", "residual"]],
}

_recurrence_filter = filter_(
    nodes_of_type("ProblemShapeObservation"), "y",
    and_(eq(attr("y", "key"), attr("obs", "key")),
         in_(attr("y", "status"), lit(DECODE_STATUSES))))

_canonical_minter_filter = filter_(
    nodes_of_type("ProblemShapeObservation"), "z",
    and_(eq(attr("z", "key"), attr("obs", "key")),
         eq(attr("z", "status"), lit("residual"))))

_support_count = count(filter_(
    nodes_of_type("ProblemShapeObservation"), "y",
    eq(attr("y", "key"), attr("obs", "key"))))

ps_mint = {
    "name": "ps_mint",
    "comment": ("RUNG 4 -- DYNAMIC QUANTIZATION at the problem-shape grain, built "
                "from ONLY existing generic Terms (QUESTION_DRIVER_RUNG3_PREREG.md "
                "Sec4.2 -- no bespoke Rust mint Term, unlike MetaShapeMint). Fires "
                "only when: this observation stayed a genuine residual (rung 1 could "
                "not explain it); at least one OTHER decoded/residual/minted "
                "observation shares this observation's key (recurrence -- support>=2, "
                "the same floor META_SHAPE_FIRST_CLASS_RESULTS.md Sec4.1 established); "
                "this observation is the group's canonical minter (lowest node id -- "
                "the SAME Argmin idiom seeds/gap_awareness.json::retire_duplicate_gap "
                "already uses for its own canonical-survivor pick, so a group mints "
                "ONCE per pass, not N times); and no ProblemShape already carries this "
                "key as its name (mint-once guard). Bumps problem_codebook_epoch to "
                "re-arm ps_redecode."),
    "match_type": "ProblemShapeObservation",
    "match": [["ag", "observed_problem", "obs"]],
    "where": and_(
        eq(attr("obs", "status"), lit("residual")),
        eq(count(neighbours("obs", "minted_problem_shape")), lit(0)),
        gt(count(_recurrence_filter), lit(1)),
        eq(var("obs"), argmin(_canonical_minter_filter, "z", var("z"))),
        not_(exists(nodes_of_type("ProblemShape"), "ems",
                     eq(attr("ems", "name"), attr("obs", "key")))),
    ),
    "effects": [
        ["add_node", "ps", "ProblemShape", {
            "name": term(attr("obs", "key")),
            "signature": term(attr("obs", "signature")),
            "support": term(_support_count),
            "minted": 1.0,
            "source": "problem_shape_growth",
        }],
        ["add_edge", "obs", "minted_problem_shape", "ps"],
        ["set_attr", "obs", "status", "minted"],
        ["set_attr", "ag", "problem_codebook_epoch", term({
            "type": "Plus", "items": [attr("ag", "problem_codebook_epoch"), lit(1)]})],
    ],
}

ps_redecode = {
    "name": "ps_redecode",
    "comment": ("CODEBOOK GROWTH CLOSES THE LOOP: any recognized/minted/residual "
                "observation last decoded under an OLDER problem_codebook_epoch "
                "re-arms to pending, so ps_decode re-runs it against the GROWN "
                "codebook -- mint -> re-decode -> recognize, run_rules-fixpoint-"
                "driven, no Python iteration. Mirrors sd_redecode/msg_redecode "
                "exactly (minus transform/dim flag resets -- those rungs are not "
                "wired at this grain)."),
    "match_type": "ProblemShapeObservation",
    "match": [["ag", "observed_problem", "obs"]],
    "where": and_(
        or_(eq(attr("obs", "status"), lit("recognized")),
            eq(attr("obs", "status"), lit("residual")),
            eq(attr("obs", "status"), lit("minted"))),
        lt(attr("obs", "decoded_epoch"), attr("ag", "problem_codebook_epoch")),
    ),
    "effects": [
        ["set_attr", "obs", "status", "pending"],
        ["set_attr", "obs", "decoded_epoch", term(attr("ag", "problem_codebook_epoch"))],
    ],
}

SEED = {
    "id": "problem_shape_growth",
    "version": "1.0.0",
    "depends_on": ["solver_dispatch"],
    "description": (
        "QUESTION_DRIVER_RUNG3_PREREG.md / _RESULTS.md: a ProblemShape codebook "
        "recognizing the STRUCTURAL SHAPE of an already-minted solve_* Goal "
        "(domains/solver_dispatch.py) from its own real attrs/edges (never from "
        "its kind string), via the UNCHANGED ShapeDecode Term pointed at "
        "codebook_type='ProblemShape' (load_parts is grain-agnostic -- confirmed "
        "at runners/dsl/src/shape_decode.rs, re-confirmed here). ProblemShape is "
        "a NEW node type (not a ShapeSignature{kind:...}), mirroring the "
        "DirectionalCorrespondence precedent (analogical_thinking.py:672-687): "
        "ShapeDecode's live decode pool does not partition on kind, so a "
        "kind-tagged ShapeSignature would silently compete for "
        "inference_generation.resolve_implication_gap's real decode slot. Two "
        "shapes (deduction_shape, can_shape) are SEEDED, grounded in >=5 real "
        "recurring dispatch instances each (QUESTION_DRIVER_RUNG3_PREREG.md "
        "Sec1.1); a third (decompose_shape) is DELIBERATELY left unseeded to "
        "mint live from real recurrence (2 real solve_decompose instances -- the "
        "same support=2 floor META_SHAPE_FIRST_CLASS_RESULTS.md Sec4.1 already "
        "established as 'the smallest cardinality at which recurs is defined'). "
        "Rung 1 uses literal ShapeDecode (Count(residual)==0), NOT Covers -- "
        "every signature here is fully concrete, no WILD, unlike meta-shape's "
        "anti-unified lgg codebook (Sec4.1 of the prereg explains why Covers is "
        "unneeded here). Mint (rung 4) uses ONLY existing generic Terms "
        "(Eq/Exists/Argmin/Count/Plus -- the SAME canonical-minter idiom "
        "seeds/gap_awareness.json::retire_duplicate_gap already uses), not a "
        "bespoke Rust Term: every real solve_decompose observation produces the "
        "IDENTICAL literal signature, so anti-unifying two of them is a no-op "
        "and minting directly from the observation's own signature is correct. "
        "Rungs 2/3 (TransformDecode/DimInfer) are NOT wired -- a graceful, "
        "deliberate no-op (every axis here is a categorical presence/value "
        "string, never an integer coordinate; QUESTION_DRIVER_RUNG3_PREREG.md "
        "Sec4.1), mirroring META_SHAPE_FIRST_CLASS_RESULTS.md Sec3's own rung-3 "
        "no-op. The hold-open multi-candidate layer and pre-mint auto-dispatch "
        "are explicitly OUT of scope this rung (QUESTION_DRIVER_RUNG3_PREREG.md "
        "Sec5) -- no real case of genuine candidate competition, and no real "
        "raw-problem corpus, exists yet to ground either."),
    "microtheory": {
        "name": "problem_shape_growth",
        "description": ("the ProblemShape codebook recognizes a solve_* Goal's real "
                         "structural facts and grows on genuine recurrence"),
    },
    "nodes": [
        {"local_id": 1, "type": "ProblemShape", "attrs": {
            "name": "ps_has_statement=yes", "signature": DEDUCTION_SIG,
            "support": 10.0, "minted": 0.0, "source": "problem_shape_growth:seeded"}},
        {"local_id": 2, "type": "ProblemShape", "attrs": {
            "name": "ps_has_targets_mt=yes", "signature": CAN_SIG,
            "support": 5.0, "minted": 0.0, "source": "problem_shape_growth:seeded"}},
    ],
    "edges": [],
    "productions": [
        {"provenance": "problem_shape_growth:observed_problem",
         "src": {"type": "Agent", "var": "ag"}, "edge_type": "observed_problem",
         "tgt": {"type": "ProblemShapeObservation", "var": "obs"}},
        {"provenance": "problem_shape_growth:about_goal",
         "src": {"type": "ProblemShapeObservation", "var": "obs"}, "edge_type": "about_goal",
         "tgt": {"type": "Goal", "var": "g"}},
        {"provenance": "problem_shape_growth:minted_problem_shape",
         "src": {"type": "ProblemShapeObservation", "var": "obs"}, "edge_type": "minted_problem_shape",
         "tgt": {"type": "ProblemShape", "var": "ps"}},
    ],
    "rules": [ps_decode, ps_recognize, ps_residual, ps_mint, ps_redecode],
}

if __name__ == "__main__":
    with open(OUT, "w") as f:
        json.dump(SEED, f, indent=1)
        f.write("\n")
    print("wrote", OUT)
