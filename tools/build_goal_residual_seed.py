#!/usr/bin/env python3
"""build_goal_residual_seed — EMIT `seeds/goal_residuals.json`.

A one-off authoring script under `tools/` (the sanctioned home for scripts
that EMIT seed manifests — `CLAUDE.md`, "What still exists in Python").  It is
not agent runtime: nothing imports it at boot, and deleting it leaves the seed
in place.

It writes three things into one manifest:

  1. `SignatureVocab{dim, token}` — the CLOSED goal-signature vocabulary, as
     graph data, so the audit reads the graph and not a Python constant.
  2. `GoalResidual` + `ResidualCondition` nodes — mechanically ingested from
     the measured arc-6 results artifacts by `domains.goal_residual_ingest`.
  3. The `gr_*` rules — staleness (a condition that no longer holds makes its
     residual stale) and the penalty stamp (a matched candidate carries the
     strongest held residual's weight, for audit).

Deterministic: re-running it must reproduce the file byte for byte, which
`tests/test_goal_residual_migrated.py` gates.

  PYTHONPATH=runners/dsl/python:. python tools/build_goal_residual_seed.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from domains import goal_residual_ingest as gri  # noqa: E402

OUT = os.path.join(ROOT, "seeds", "goal_residuals.json")
VERSION = "1.0.0"


# --------------------------------------------------------------------------- #
#  Term constructors — plain dicts, the same JSON the engine evaluates.
# --------------------------------------------------------------------------- #
def V(n):
    return {"type": "Var", "name": n}


def A(n, k):
    return {"type": "Attr", "node": V(n), "key": k}


def L(v):
    return {"type": "Lit", "value": v}


def EQ(a, b):
    return {"type": "Eq", "a": a, "b": b}


def NOT(x):
    return {"type": "Not", "arg": x}


def AND(*xs):
    return {"type": "And", "items": list(xs)}


def OR(*xs):
    return {"type": "Or", "items": list(xs)}


def COUNT(src):
    return {"type": "Count", "source": src}


def FILTER(src, var, pred):
    return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}


def NODES(t):
    return {"type": "NodesOfType", "node_type": t}


def EXISTS(src, var, pred):
    return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}


def ITE(c, t, o):
    return {"type": "IfThenElse", "cond": c, "then": t, "other": o}


def NEIGH(n, et):
    return {"type": "Neighbours", "node": V(n), "edge_type": et, "any_type": False}


def PICK(src):
    return {"type": "Pick", "source": src}


# --------------------------------------------------------------------------- #
#  THE SIGNATURE MATCH.  The crux of the design.
#
#  A residual matches a candidate iff, for EVERY signature dimension the
#  residual DECLARES, the candidate agrees; a dimension the residual leaves
#  unset is a WILDCARD.  Specificity is therefore an authored, auditable
#  property (how many dimensions a residual pins), not an emergent property of
#  string overlap.
#
#  Two guards that make this neither seam-D nor a blunderbuss:
#    * a candidate with NO `sig_seam` is never matched, so an all-wildcard
#      residual cannot suppress an unsignatured goal (and every existing
#      MoveCandidate in the synthesis pipeline is unsignatured — the reason
#      this change is inert on the regression bench);
#    * a STALE residual is out of the pool entirely.
# --------------------------------------------------------------------------- #
SIG_DIMS = ("sig_seam", "sig_lever", "sig_target")


def MATCH(r, c):
    """`r` matches candidate `c` — the conjunction over declared dimensions."""
    items = [
        NOT(EQ(A(r, "stale"), L(1.0))),
        NOT(EQ(A(c, "sig_seam"), L(None))),
    ]
    for dim in SIG_DIMS:
        items.append(OR(EQ(A(r, dim), L(None)), EQ(A(r, dim), A(c, dim))))
    return AND(*items)


def PENALTY(c):
    """The down-weight candidate `c` carries: the STRONGEST held residual that
    matches it, or 0.0 when none does.

    MAX, not sum: near-duplicate residuals describing one refutation must not
    compound into a de-facto veto, and the strongest held refutation is the
    honest statement of how much is already known.  Zero when nothing matches,
    so the term is identically absent for every candidate the mechanism does
    not speak to.
    """
    pool = FILTER(NODES("GoalResidual"), "grr", MATCH("grr", c))
    return ITE(
        EXISTS(NODES("GoalResidual"), "grr", MATCH("grr", c)),
        {"type": "Attr", "key": "weight",
         "node": {"type": "Argmax", "source": pool, "var_name": "grw",
                  "value": A("grw", "weight"), "default": None}},
        L(0.0))


# --------------------------------------------------------------------------- #
#  THE CONDITION MISMATCH.  A closed set of condition kinds, each a live count
#  or a live fact — the graph checking whether its own residual still applies.
# --------------------------------------------------------------------------- #
def _shape_count(c, with_payload):
    pred = EQ(A("grs", "kind"), A(c, "filter_value"))
    if with_payload:
        pred = AND(pred, NOT(EQ(A("grs", "keywords"), L(None))))
    return COUNT(FILTER(NODES("ShapeSignature"), "grs", pred))


def MISMATCH(c):
    return OR(
        # (1) the codebook population the ceiling was measured against
        AND(EQ(A(c, "ckind"), L("shape_count")),
            NOT(EQ(_shape_count(c, False), A(c, "expected")))),
        # (2) the codebook's PAYLOAD — seam C's null holds because the shapes
        #     carry no keywords; give them one and the null's mechanism is gone
        AND(EQ(A(c, "ckind"), L("payload_count")),
            NOT(EQ(_shape_count(c, True), A(c, "expected")))),
        # (3) a named measured fact about the substrate or the evidence
        AND(EQ(A(c, "ckind"), L("fact_equals")),
            NOT(EQ(COUNT(FILTER(NODES("ResidualFact"), "grf",
                                AND(EQ(A("grf", "name"), A(c, "filter_value")),
                                    EQ(A("grf", "value"), A(c, "expected_str"))))),
                   L(1.0)))),
    )


# --------------------------------------------------------------------------- #
#  Rules.
# --------------------------------------------------------------------------- #
def rules():
    return [
        {
            "name": "gr_condition_lapse",
            "comment":
                "A RESIDUAL WHOSE CONDITION NO LONGER HOLDS GOES STALE.  A "
                "residual without its condition is precisely the failure "
                "CLAUDE.md retracts -- a claim quoted without its condition, "
                "which stood false for ten days.  Every GoalResidual carries at "
                "least one ResidualCondition (holds_under); this rule reads the "
                "LIVE graph for each and marks the residual stale the moment any "
                "one of them mismatches.  Staleness is not falsity: it means the "
                "measurement no longer describes the world and must be re-made "
                "before it may be used again.  Idempotent (guarded on stale!=1) "
                "and reversible (gr_condition_hold is the other direction, so a "
                "condition that comes back restores the residual -- a latch would "
                "be a second un-lapsable claim).",
            "batch": True,
            "match": [["r", "holds_under", "c"]],
            "where": AND(NOT(EQ(A("r", "stale"), L(1.0))), MISMATCH("c")),
            "effects": [["set_attr", "r", "stale", 1.0]],
        },
        {
            "name": "gr_condition_hold",
            "comment":
                "The reverse direction, and it is not decoration: a one-way lapse "
                "would itself be a claim that cannot be revised.  A stale residual "
                "whose conditions ALL hold again is restored to the pool.  "
                "Mutually exclusive with gr_condition_lapse by construction "
                "(Exists mismatch vs Not Exists mismatch), so the two never "
                "contend for the same node in one pass.",
            "batch": True,
            "match": [["r", "holds_under", "c"]],
            "where": AND(EQ(A("r", "stale"), L(1.0)),
                         NOT(EXISTS(NEIGH("r", "holds_under"), "c2", MISMATCH("c2")))),
            "effects": [["set_attr", "r", "stale", 0.0]],
        },
        {
            "name": "gr_move_penalty",
            "comment":
                "AUDIT STAMP.  Writes onto the candidate the weight the strongest "
                "matching held residual contributes -- the same auditability "
                "ps_move_sel_kind/ps_move_sel_gap already provide for the other "
                "terms.  The COLLAPSE does not depend on this attr: "
                "ps_move_select computes the same penalty INLINE inside its "
                "Argmax, so the selection can never be wrong because a stamp had "
                "not been written yet in the fixpoint.  Self-extinguishing (it "
                "declines to rewrite a value already equal).",
            "batch": True,
            "match": [["g", "has_move_candidate", "mc"]],
            "where": AND(NOT(EQ(A("mc", "sig_seam"), L(None))),
                         EXISTS(NODES("GoalResidual"), "grr", MATCH("grr", "mc")),
                         NOT(EQ(A("mc", "residual_penalty"), PENALTY("mc")))),
            "effects": [["set_attr", "mc", "residual_penalty",
                         {"__term__": PENALTY("mc")}]],
        },
        {
            "name": "gr_move_penalty_clear",
            "comment":
                "The other direction of the same stamp: a candidate no held "
                "residual speaks to carries an explicit ZERO, so 'no penalty' is "
                "a written fact rather than an absent attr.  This is the "
                "both-directions discipline -- a stamp that only ever writes "
                "non-zero cannot be distinguished from a stamp that never fires.",
            "batch": True,
            "match": [["g", "has_move_candidate", "mc"]],
            "where": AND(NOT(EXISTS(NODES("GoalResidual"), "grr", MATCH("grr", "mc"))),
                         NOT(EQ(A("mc", "residual_penalty"), L(0.0)))),
            "effects": [["set_attr", "mc", "residual_penalty", 0.0]],
        },
        {
            "name": "gr_move_sel_audit",
            "comment":
                "WHAT THE WINNER WAS CHARGED.  ps_move_select computes the "
                "residual penalty INLINE (so the collapse never depends on stamp "
                "ordering) and therefore does not write it down; this rule reads "
                "the selected candidate back by its own ps_move_sel_key and "
                "copies its residual_penalty onto the goal, giving the residual "
                "term the same audit trail ps_move_sel_gap / ps_move_sel_mdl "
                "already have.  A selection you cannot read is a selection you "
                "cannot check.",
            "batch": True,
            "match": [["ag", "has_goal", "g"]],
            "where": AND(
                NOT(EQ(A("g", "ps_move_sel_key"), L(None))),
                NOT(EQ(A("g", "ps_move_sel_residual_penalty"),
                       {"type": "Attr", "key": "residual_penalty",
                        "node": PICK(FILTER(NEIGH("g", "has_move_candidate"), "mcs",
                                            EQ(A("mcs", "key"),
                                               A("g", "ps_move_sel_key"))))})),
            ),
            "effects": [["set_attr", "g", "ps_move_sel_residual_penalty",
                         {"__term__": {
                             "type": "Attr", "key": "residual_penalty",
                             "node": PICK(FILTER(NEIGH("g", "has_move_candidate"),
                                                 "mcs",
                                                 EQ(A("mcs", "key"),
                                                    A("g", "ps_move_sel_key"))))}}]],
        },
    ]


# --------------------------------------------------------------------------- #
def build():
    ing = gri.build_residuals()
    nodes, edges = [], []

    # --- the closed vocabulary, as graph data (local_id 0..) ---------------
    lid = 0
    for dim in gri.SIGNATURE_VOCAB:
        for token in gri.SIGNATURE_VOCAB[dim]:
            nodes.append({"local_id": lid, "type": "SignatureVocab",
                          "attrs": {"dim": dim, "token": token}})
            lid += 1
    # --- the reach classes and the scale, as graph data --------------------
    for name in sorted(gri.REACH_CLASS_FACTOR):
        nodes.append({"local_id": lid, "type": "ReachClass",
                      "attrs": {"name": name,
                                "factor": gri.REACH_CLASS_FACTOR[name]}})
        lid += 1
    nodes.append({"local_id": lid, "type": "ResidualPolicy",
                  "attrs": {"name": "goal_residual",
                            "residual_scale": gri.RESIDUAL_SCALE,
                            "weight_formula":
                                "residual_scale * reach_class_factor * "
                                "(1 - honest_n / denominator_n)",
                            "aggregation": "max",
                            "is_a_veto": 0.0}})
    lid += 1

    # --- the ingested residuals (local_id 1000..) --------------------------
    lid = 1000
    for rec in ing["residuals"]:
        rid_local = lid
        attrs = {
            "rid": rec["rid"],
            "sig_seam": rec["sig_seam"],
            "sig_lever": rec["sig_lever"],
            "sig_target": rec["sig_target"],
            "reach_class": rec["reach_class"],
            "reach_class_factor": rec["reach_class_factor"],
            "ceiling_honest_n": float(rec["ceiling_honest_n"]),
            "ceiling_honest_ids": rec["ceiling_honest_ids"],
            "ceiling_cherry_n": float(rec["ceiling_cherry_n"]),
            "ceiling_cherry_ids": rec["ceiling_cherry_ids"],
            "denominator_n": rec["denominator_n"],
            "mechanism": rec["mechanism"],
            "mechanism_source_path": rec["mechanism_source_path"],
            "weight": rec["weight"],
            "weight_formula": rec["weight_formula"],
            "evidence_artifact": rec["evidence_artifact"],
            "evidence_artifact_sha256": rec["evidence_artifact_sha256"],
            "stale": 0.0,
        }
        if rec.get("evidence_engine_sha256"):
            attrs["evidence_engine_sha256"] = rec["evidence_engine_sha256"]
        if rec.get("evidence_engine_line"):
            attrs["evidence_engine_line"] = rec["evidence_engine_line"]
        if rec.get("ceiling_reductio_n") is not None:
            attrs["ceiling_reductio_n"] = float(rec["ceiling_reductio_n"])
            attrs["ceiling_reductio_ids"] = rec["ceiling_reductio_ids"]
        if rec.get("reach_class_counts") is not None:
            attrs["reach_class_counts"] = json.dumps(
                rec["reach_class_counts"], sort_keys=True)
        nodes.append({"local_id": rid_local, "type": "GoalResidual",
                      "attrs": attrs})
        lid += 1
        for cond in rec["conditions"]:
            cattrs = {"rid": rec["rid"], "ckind": cond["ckind"],
                      "filter_value": cond["filter_value"], "why": cond["why"]}
            if "expected" in cond:
                cattrs["expected"] = float(cond["expected"])
            if "expected_str" in cond:
                cattrs["expected_str"] = cond["expected_str"]
            nodes.append({"local_id": lid, "type": "ResidualCondition",
                          "attrs": cattrs})
            edges.append({"src": {"local": rid_local}, "tgt": {"local": lid},
                          "type": "holds_under", "attrs": {}})
            lid += 1

    manifest = {
        "id": "goal_residuals",
        "version": VERSION,
        "depends_on": [],
        "description":
            "MEASURED CEILINGS, GRAPH-RESIDENT.  Arc 6 measured five ceilings and "
            "killed three seams; every one of those results existed only in "
            "markdown the agent cannot read, so a goal-selection collapse would "
            "re-propose a refuted seam with no memory.  This seed holds each "
            "refutation as a GoalResidual{goal signature, honest AND "
            "cherry-picked ceiling, refutation mechanism, reachability class, "
            "evidence pointer + engine sha} together with the CONDITION under "
            "which it holds (ResidualCondition, holds_under) -- because a "
            "residual that cannot lapse is a lie with a long half-life.  A held "
            "residual contributes a strong NEGATIVE WEIGHT to the existing "
            "ps_move_select Argmax; it is never a veto.  Pursuing an unreachable "
            "goal is legitimate -- that is how residuals get made; being wrong "
            "where the residual is already held is not.  Every node below is "
            "emitted mechanically from results/arc6_*.json by "
            "tools/build_goal_residual_seed.py over "
            "domains/goal_residual_ingest.py -- no number is transcribed from "
            "prose.",
        "microtheory": {
            "name": "goal_residuals",
            "description":
                "held refutations of goals, with their conditions, as a weight in "
                "the goal collapse.",
        },
        "nodes": nodes,
        "edges": edges,
        "productions": [
            {"provenance": "seed:goal_residuals:holds_under-0",
             "src": {"type": "GoalResidual", "var": "s"},
             "edge_type": "holds_under",
             "tgt": {"type": "ResidualCondition", "var": "t"}},
        ],
        "rules": rules(),
    }
    return manifest, ing


def main() -> int:
    manifest, _ing = build()
    with open(OUT, "w") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=False)
        fh.write("\n")
    print("wrote %s  (%d nodes, %d edges, %d rules)"
          % (OUT, len(manifest["nodes"]), len(manifest["edges"]),
             len(manifest["rules"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
