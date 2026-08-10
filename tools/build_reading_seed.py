"""build_reading_seed — EMIT seeds/literary_analysis_driving.json.

A one-off authoring tool (tools/*, deletable, NOT agent runtime): it constructs
the goal-driven reading/analysis pipeline as GRAPH DATA — one dispatch RULE per
comprehension/production stage (fired by run_rules on each stage's OWN graph
precondition) plus ONE `analysis_advance` Reflex (fires whenever a stage is
dispatched). The SEQUENCING that domains/comprehension_reader.read_and_comprehend
used to impose as a Python list of 10 hand-ordered faculty calls now lives here,
as the where-clauses of these rules: each faculty stage becomes eligible the
moment its data-dependency is satisfied on the graph, and `run_rules` sequences
them for free (the same way seeds/shape_decode_loop.json's sd_* rules ARE the
decode->grow->re-decode loop and seeds/question_driving.json IS the goal pump).

The DATA-DEPENDENCY triggers (node-existence, the task's headline shape):
  · infer_goal / discourse / monitoring  fire when SmEntity nodes exist
  · infer_causal                         fires when DiscourseEvent nodes exist
  · narrative                            fires when SmEvent nodes exist
  · trope                                fires when NarrativeRole nodes exist
  · produce_frames                       fires when Trope nodes exist
Where a stage's input is not a countable node type (an `enables`/`causes` edge
set, or a Python-view a prior stage stashed), the precondition instead reads the
producing stage's own `status == done` (still graph-resident data, still fired by
run_rules) — the honest residual recorded in the task ledger.

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 tools/build_reading_seed.py
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SEED_PATH = os.path.join(os.path.dirname(HERE), "seeds", "literary_analysis_driving.json")


# --- Term constructors (the DSL the engine evaluates) ---------------------- #
def var(n):            return {"type": "Var", "name": n}
def attr(n, k):        return {"type": "Attr", "node": var(n), "key": k}
def lit(v):            return {"type": "Lit", "value": v}
def eq(a, b):          return {"type": "Eq", "a": a, "b": b}
def gt(a, b):          return {"type": "Gt", "a": a, "b": b}
def and_(items):       return {"type": "And", "items": items}
def nodes_of(t):       return {"type": "NodesOfType", "node_type": t}
def count(src):        return {"type": "Count", "source": src}
def count_type(t):     return count(nodes_of(t))
def filt(src, v, pred): return {"type": "Filter", "source": src, "var_name": v, "predicate": pred}


def exists(t, v, pred):
    return {"type": "Exists", "source": nodes_of(t), "var_name": v, "predicate": pred}


# --- reusable precondition fragments --------------------------------------- #
def count_gt0(t):
    """DATA-DEPENDENCY trigger: >=1 node of type `t` exists on the graph."""
    return gt(count_type(t), lit(0))


def goal_reading_present():
    """A reading Goal (read_and_comprehend OR produce_analysis) has been minted."""
    return exists("Goal", "grd", eq(attr("grd", "reading_report"), lit(1.0)))


def goal_produce_present():
    """A produce-analysis Goal (not a bare comprehend goal) has been minted."""
    return exists("Goal", "gpd", eq(attr("gpd", "produce_report"), lit(1.0)))


_DONE_VAR = [0]


def stage_done(name):
    """The AnalysisStage named `name` has finished (status == done). A
    graph-resident dependency for a stage whose input is a prior stage's stashed
    Python view / edge-set rather than a countable node type."""
    _DONE_VAR[0] += 1
    v = "sd%d" % _DONE_VAR[0]
    return exists("AnalysisStage", v,
                  and_([eq(attr(v, "name"), lit(name)),
                        eq(attr(v, "status"), lit("done"))]))


# --- the stage table: (stage-name, [extra precondition terms]) ------------- #
# name==pending + these terms => the stage dispatches. The order below is only
# documentation; the RUNTIME order emerges from the preconditions in run_rules.
STAGES = [
    # comprehension faculties (read_and_comprehend's old steps 1..9)
    ("spine",         [goal_reading_present(), count_gt0("Source")]),
    ("infer_goal",    [count_gt0("SmEntity")]),
    ("discourse",     [count_gt0("SmEntity")]),
    ("infer_causal",  [count_gt0("DiscourseEvent")]),
    ("enabling",      [count_gt0("DiscourseEvent"), stage_done("infer_goal"),
                       stage_done("infer_causal")]),
    ("centrality",    [stage_done("enabling")]),
    ("monitoring",    [count_gt0("SmEntity")]),
    ("tom",           [count_gt0("Source"), stage_done("spine")]),
    ("narrative",     [count_gt0("SmEvent"), stage_done("enabling"),
                       stage_done("centrality"), stage_done("discourse"),
                       stage_done("infer_goal")]),
    ("trope",         [count_gt0("NarrativeRole"), stage_done("narrative")]),
    # production faculty (produce_analysis's old section marshalling) — each
    # SECTION is its own stage, fired independently (there is NO imposed order
    # between the four; read-out assembles section order mechanically).
    # produce_frames fires purely on Trope-node existence (the task's "produce
    # when trope/theme exists") — so it also drives the graph= path (produce
    # over an already-comprehended graph, test_summit) with no comprehension
    # stages present.
    ("produce_frames",    [goal_produce_present(), count_gt0("Trope")]),
    ("produce_summary",   [goal_produce_present(), stage_done("produce_frames")]),
    ("produce_structure", [goal_produce_present(), stage_done("produce_frames")]),
    ("produce_technique", [goal_produce_present(), stage_done("produce_frames")]),
    ("produce_theme",     [goal_produce_present(), stage_done("produce_frames")]),
]


def dispatch_rule(name, extra):
    where_items = [eq(attr("stage", "name"), lit(name)),
                   eq(attr("stage", "status"), lit("pending"))] + list(extra)
    return {
        "name": "la_dispatch_%s" % name,
        "comment": ("Fire the '%s' faculty stage when its graph precondition holds "
                    "(see build_reading_seed.py). The DECISION-to-fire + the ORDER "
                    "are this where-clause, evaluated by run_rules — never a Python "
                    "faculty sequence." % name),
        "match_type": "AnalysisStage",
        "match": [["ag", "has_analysis_stage", "stage"]],
        "where": and_(where_items),
        "effects": [["set_attr", "stage", "status", "dispatched"]],
    }


REFLEX = {
    "name": "analysis_advance",
    "stimulus": {
        "type": "Gte",
        "a": count(filt(nodes_of("AnalysisStage"), "x",
                        eq(attr("x", "status"), lit("dispatched")))),
        "b": lit(1),
    },
    "response": "analysis_advance",
    "refractory_ticks": 0,
}


def build():
    return {
        "id": "literary_analysis_driving",
        "version": "1.0.0",
        "depends_on": [],
        "description": (
            "The comprehension->analysis process as a GOAL-DRIVEN GRAPH FIXPOINT. "
            "read_and_comprehend's ~10 hand-sequenced Python faculty calls + "
            "produce_analysis's section marshalling are DELETED; each faculty is a "
            "STAGE fired by its OWN graph precondition (this seed's la_dispatch_* "
            "rules), and the run_rules fixpoint sequences them by data-dependency. "
            "The analysis_advance Reflex (a dispatched AnalysisStage exists) runs the "
            "stage's thin non-branching Python executor (domains/reading_drive.py's "
            "_advance_dispatched_stage), exactly the _question_pursue_advance "
            "precedent. Stages, the report Goal + the Source are minted per-drive by "
            "the thin adapter (reading_drive.run_reading_flow); the rules/reflex are "
            "the static graph-resident sequencer."),
        "microtheory": {
            "name": "literary_analysis_driving",
            "description": ("Source + report-Goal -> comprehension/production stages "
                            "fire on their data-dependencies -> analysis emerges as "
                            "graph state (Claim nodes), tick/rule-driven."),
        },
        "nodes": [],
        "edges": [],
        "productions": [
            {"provenance": "seed:literary_analysis_driving:has_analysis_stage-0",
             "src": {"type": "Agent", "var": "s"}, "edge_type": "has_analysis_stage",
             "tgt": {"type": "AnalysisStage", "var": "t"}},
            {"provenance": "seed:literary_analysis_driving:has_claim-1",
             "src": {"type": "Agent", "var": "s"}, "edge_type": "has_claim",
             "tgt": {"type": "Claim", "var": "t"}},
            {"provenance": "seed:literary_analysis_driving:reads_source-2",
             "src": {"type": "Goal", "var": "s"}, "edge_type": "reads_source",
             "tgt": {"type": "Source", "var": "t"}},
        ],
        "rules": [dispatch_rule(n, extra) for n, extra in STAGES],
        "reflexes": [REFLEX],
    }


def main():
    seed = build()
    with open(SEED_PATH, "w") as fh:
        json.dump(seed, fh, indent=2)
        fh.write("\n")
    print("wrote %s (%d dispatch rules, 1 reflex)" % (SEED_PATH, len(seed["rules"])))


if __name__ == "__main__":
    main()
