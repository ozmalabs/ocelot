"""goal_residual_ingest — MECHANICAL ingest of measured arc-6 ceilings into
`GoalResidual` graph data.

WHAT THIS IS.  Arc 6 measured five ceilings and killed three seams.  Every one
of those results existed only in markdown, which is precisely the blind spot
`CLAUDE.md` names ("the agent can self-repair exactly where its cognition is
graph-native ... it CANNOT edit the Python front end, because that is not graph
it can see or vary").  A goal-selection collapse that cannot READ a refutation
will re-propose a killed seam, confidently, forever.  This module translates the
measured JSON artifacts into graph data the collapse can read.

WHAT THIS IS NOT.  It is not a decision layer.  Every number it emits is
resolved from a DOTTED PATH into a results artifact; every prose string it
emits is a VERBATIM copy of a string at a dotted path.  Nothing is
paraphrased, rounded, or inferred.  A path that does not resolve produces an
entry in `not_ingested` with the path that failed — never a substituted
number.  This is the direct application of the arc-6 measurement protocol
("read the JSON artifacts, not the markdown ... if a number you need exists
only in prose, say so and leave it out").

THE ONE ARITHMETIC STEP, stated openly.  `weight` — the strength of the
down-weight a held residual contributes to the collapse — is computed as

    weight = RESIDUAL_SCALE * REACH_CLASS_FACTOR[reach_class] * (1 - honest_n / denominator_n)

`RESIDUAL_SCALE` and `REACH_CLASS_FACTOR` are AUTHORED constants (declared
here, mirrored into the seed as graph data, tunable without touching code).
The third factor is MEASURED: the fraction of the residual's own denominator
that the honest ceiling failed to reach.  A residual that reached everything
weighs nothing.  This is the same shape as `ps_move_select`'s existing
`ps_move_w_gap` / `ps_move_w_arity` / `ps_move_w_mdl` coefficients — weights
are graph data, and the collapse reads them.

THE SIGNATURE VOCABULARY IS CLOSED.  `sig_seam` / `sig_lever` / `sig_target`
draw from `SIGNATURE_VOCAB` below, which is written from the seam table in
`PROGRAM_SYNTHESIS_ARC6_PREREG.md` §1 and from the LAYER names the prereg
itself uses — never from a task.  `tests/test_goal_residual_migrated.py`
audits both halves of that claim mechanically (membership, and the seam-D
`verbatim_prompt_substring_of_len_ge_12` instrument turned on this module's
own vocabulary).
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")

# --------------------------------------------------------------------------- #
#  The CLOSED signature vocabulary.  Authored from the prereg's seam table and
#  its layer names; audited by the test suite against the MBPP prompts.
# --------------------------------------------------------------------------- #
SIGNATURE_VOCAB: Dict[str, Tuple[str, ...]] = {
    # WHAT MECHANISM the goal proposes to build.
    "sig_seam": (
        "import_oracle",     # seam A -- a library registered as a ProgEval oracle
        "ir_retarget",       # seam B -- extract_function retargeted to the hub IR
        "shape_codebook",    # seam C -- ShapeSignature recognition over prose
        "property_atom",     # seam D -- theorem-derived RequiredProperty atoms
        "enum_op_table",     # structural -- SynthEnumerate op/template widening
        "row_verdict",       # the row acceptance comparator
    ),
    # WHICH LAYER of the pipeline the goal changes.
    "sig_lever": (
        "proposal",          # what the enumerator can OFFER
        "execution",         # what ProgEval can RUN
        "verdict",           # what the row rules ACCEPT
        "detection",         # what the agent RECOGNISES a task as
        "representation",    # the value/dimension layer underneath all three
    ),
    # OVER WHICH POPULATION the ceiling was measured.
    "sig_target": (
        "mbpp_test_257",
        "mbpp_live_unreached_53",
        "mbpp_s4_residual_60",
        "mbpp_residual_36",
        "mbpp_arc4_104",
    ),
}

# Authored, declared, tunable.  NOT measured — see the module docstring.
RESIDUAL_SCALE = 100.0
REACH_CLASS_FACTOR: Dict[str, float] = {
    # unreachable at ANY search size -- arc 5 closed six pi-geometry tasks by
    # minting a dimension, so this class is the one a build genuinely cannot
    # route around without adding a dimension.
    "missing_dimension": 1.0,
    # a general operator would reach it; the gap is inventory, not frame.
    "operator_blocked": 0.7,
    # every primitive exists; the composition is deeper than the budget.
    "budget": 0.4,
}

# --------------------------------------------------------------------------- #
#  THE SPEC.  One entry per residual.  Every `*_path` is a dotted path into the
#  named artifact.  Prose fields are paths too -- the string is copied
#  verbatim, never retyped.
# --------------------------------------------------------------------------- #
SPEC: Tuple[Dict[str, Any], ...] = (
    {
        "rid": "arc6.seam_a.import_oracle",
        "artifact": "arc6_a_ceiling.json",
        "sig_seam": "import_oracle",
        "sig_lever": "execution",
        "sig_target": "mbpp_live_unreached_53",
        "honest_ids_path": "ceilings.STRICT_kernel_verified_AND_nothing_else_blocks.strong_families_only_ids",
        "cherry_ids_path": "ceilings.cherry_picked_concept.ids",
        "reductio_ids_path": "ceilings.cherry_picked_reductio.ids",
        "denominator_path": "ceilings.honest_all_families.denominator_live_unreached",
        "reach_class": "operator_blocked",
        "reach_counts_path": "blocker_split.counts_over_live_unreached",
        "mechanism_path": "ceilings._definition.cherry_picked_concept",
        "engine_sha_path": "engine_provenance.stamp.sha256",
        "engine_line_path": "engine_provenance.stamp.line",
        "conditions": (
            {"ckind": "fact_equals", "filter_value": "arc6_a_ceiling_present",
             "expected_str": "1",
             "why": "the measurement artifact this residual quotes is still on disk "
                    "with the content sha it was ingested at; a re-measurement "
                    "replaces it and this residual must be re-read, not re-used."},
        ),
    },
    {
        "rid": "arc6.seam_b.ir_retarget",
        "artifact": "arc6_bc_ceiling.json",
        "sig_seam": "ir_retarget",
        "sig_lever": "proposal",
        "sig_target": "mbpp_test_257",
        "honest_ids_path": "ceiling_b_extract_function.ceilings_honest_vs_cherry_picked."
                           "level_0_honest_parses_today_and_verified.ids",
        "cherry_ids_path": "ceiling_b_extract_function.ceilings_honest_vs_cherry_picked."
                           "level_3_cherry_picked_cue_word_present.ids",
        "denominator_path": "n_test_tasks",
        "reach_class": "operator_blocked",
        "mechanism_path": "ceiling_b_extract_function.ceilings_honest_vs_cherry_picked."
                          "level_3_cherry_picked_cue_word_present.why_this_is_not_a_ceiling",
        "engine_sha_path": "engine_provenance.sha256",
        "engine_line_path": "engine_provenance.line",
        "extra_paths": {
            "level_1_retarget_ids": "ceiling_b_extract_function.ceilings_honest_vs_cherry_picked."
                                    "level_1_honest_after_mechanical_retarget_and_verified.ids",
            "level_1b_two_seed_edits_ids": "ceiling_b_extract_function.ceilings_honest_vs_cherry_picked."
                                           "level_1b_after_two_blind_seed_additions.ids",
            "level_2b_language_ceiling_ids": "ceiling_b_extract_function.ceilings_honest_vs_cherry_picked."
                                             "level_2b_language_ceiling_witness_verified.ids",
            "refuted_as_coincidental_fit": "ceiling_b_extract_function.ceilings_honest_vs_cherry_picked."
                                           "level_2b_language_ceiling_witness_verified.refuted_as_coincidental_fit",
            "vocabulary_acquired_at_import": "ceiling_b_extract_function.vocabulary.acquired_at_import",
        },
        "conditions": (
            {"ckind": "fact_equals", "filter_value": "arc6_bc_ceiling_present",
             "expected_str": "1",
             "why": "as above -- the artifact is the evidence; if it changes the "
                    "ceiling must be re-read."},
        ),
    },
    {
        "rid": "arc6.seam_c.shape_codebook",
        "artifact": "arc6_bc_ceiling.json",
        "sig_seam": "shape_codebook",
        "sig_lever": "detection",
        "sig_target": "mbpp_test_257",
        "honest_ids_path": "ceiling_c_math_shape_codebook.genuine_recognition_ids",
        "cherry_ids_path": "ceiling_c_math_shape_codebook.semantic_cherry_picked_ceiling."
                           "hand_audited_genuine_ids",
        "denominator_path": "n_test_tasks",
        "reach_class": "operator_blocked",
        "mechanism_path": "ceiling_c_math_shape_codebook.semantic_cherry_picked_ceiling."
                          "actionability_note",
        "engine_sha_path": "engine_provenance.sha256",
        "engine_line_path": "engine_provenance.line",
        "extra_paths": {
            "direct_load_n_recognised": "ceiling_c_math_shape_codebook."
                                        "direct_load_literal_reading.n_recognised",
            "direct_load_seed_nodes": "ceiling_c_math_shape_codebook."
                                      "direct_load_literal_reading.seed_load.nodes",
            "direct_load_seed_edges": "ceiling_c_math_shape_codebook."
                                      "direct_load_literal_reading.seed_load.edges",
            "verdict_counts": "ceiling_c_math_shape_codebook.verdict_counts",
            "codebook_counts_by_kind": "ceiling_c_math_shape_codebook.codebook.counts_by_kind",
            "codebook_attr_keys": "ceiling_c_math_shape_codebook.semantic_cherry_picked_ceiling."
                                  "codebook_attr_keys",
            "codebook_carries_a_synthesis_payload":
                "ceiling_c_math_shape_codebook.semantic_cherry_picked_ceiling."
                "codebook_carries_a_synthesis_payload",
            "positive_control_fires": "ceiling_c_math_shape_codebook.positive_control.control_fires",
        },
        # THE LOAD-BEARING CONDITION.  Seam C's null is CONDITIONAL: it nulled
        # because the math codebook is 6 `math` ShapeSignatures, 0 edges, and
        # NO synthesis payload (the shapes carry name/kind/concept/faculty/
        # signature and nothing else -- `codebook_attr_keys`).  Populate the
        # file and the null no longer holds.
        "conditions": (
            {"ckind": "shape_count", "filter_value": "math", "expected": 6.0,
             "why": "the codebook this ceiling was measured against holds exactly six "
                    "`kind=math` ShapeSignature nodes "
                    "(ceiling_c_math_shape_codebook.codebook.counts_by_kind). "
                    "Add or remove one and the measurement no longer describes the "
                    "codebook -- re-measure."},
            {"ckind": "payload_count", "filter_value": "math", "expected": 0.0,
             "why": "not one of those shapes carries a `keywords` payload "
                    "(codebook_carries_a_synthesis_payload = false; a genuine "
                    "recognition would supply only a LABEL). Give any math shape a "
                    "keyword payload and the null's own mechanism is gone."},
        ),
    },
    {
        "rid": "arc6.seam_d.property_atom",
        "artifact": "arc6_d_loo.json",
        "sig_seam": "property_atom",
        "sig_lever": "verdict",
        "sig_target": "mbpp_residual_36",
        "honest_ids_path": "m1_leave_one_out.survivor_ids",
        "honest_ids_fallback_path": "headline.loo_survivor_ids",
        "cherry_ids_path": "residual_36",
        "denominator_path": "n_atoms",
        "reach_class": "operator_blocked",
        "mechanism_path": "_README",
        "engine_sha_path": "engine.sha256",
        "extra_paths": {
            "loo_lost_ids": "headline.loo_lost_ids",
            "widened_false_refutations": "headline.widened_false_refutations_on_the_35_arc5_pass",
            "cross_task_foreign_applicable_ids": "headline.cross_task_foreign_applicable_ids",
            "n_tasks_with_a_FOREIGN_cue_match": "m3_cross_task_firing.n_tasks_with_a_FOREIGN_cue_match",
            "tasks_with_a_FOREIGN_cue_match_ids": "m3_cross_task_firing.tasks_with_a_FOREIGN_cue_match_ids",
            "arc4_denominator_authored": "headline.arc4_denominator_authored",
            "arc4_denominator_leave_one_out": "headline.arc4_denominator_leave_one_out",
        },
        "conditions": (
            {"ckind": "fact_equals", "filter_value": "arc6_d_loo_present",
             "expected_str": "1",
             "why": "the LOO measurement is the evidence; a re-authored atom set "
                    "replaces it."},
        ),
    },
    {
        "rid": "arc6.structural.enum_op_table",
        "artifact": "arc6_structural_ceiling.json",
        "sig_seam": "enum_op_table",
        "sig_lever": "proposal",
        "sig_target": "mbpp_s4_residual_60",
        "honest_ids_path": "strict_reach.witness_and_in_budget_ids",
        "cherry_ids_path": "ceilings.cherry_picked_per_task.ids",
        "denominator_path": "population.s4_residual_60_n",
        "reach_class": "operator_blocked",
        "mechanism_path": "inventory_ceiling_is_not_reach.claim",
        "engine_sha_path": "engine_provenance.sha256",
        "engine_line_path": "engine_provenance.line",
        "extra_paths": {
            "honest_B0_zero_new_termnode_ids": "ceilings.honest_B0_zero_new_termnode.ids",
            "inventory_ceiling_B3_ids": "ceilings.inventory_ceiling_B3_everything.ids",
            "inflation_B0_to_B3": "ceilings.inflation_B0_to_B3",
            "missing_dimension_ids": "dimension_vs_operator.missing_dimension_ids",
            "missing_dimension_n": "dimension_vs_operator.n",
            "dimension_finding": "dimension_vs_operator.finding",
            "s4_reach_vs_conversion_prior": "s4_reach_vs_conversion_prior",
            "witness_but_over_budget_ids": "strict_reach.witness_but_over_budget_ids",
            "refuted_ids": "refuted_ids",
        },
        "conditions": (
            {"ckind": "fact_equals", "filter_value": "arc6_structural_ceiling_present",
             "expected_str": "1",
             "why": "the op-table inventory is the evidence; widening the enumerator "
                    "changes the inventory and this ceiling must be re-measured."},
        ),
    },
    {
        "rid": "arc6.verdict.row_verdict_seed_only",
        "artifact": "arc6_verdict_pricing.json",
        "sig_seam": "row_verdict",
        "sig_lever": "verdict",
        "sig_target": "mbpp_test_257",
        "honest_ids_path": "bars.bar_1_three_of_five_known_convert_with_witnesses."
                           "converted_with_constructed_witness",
        "cherry_ids_path": "paired_diff.newly_accepted",
        "denominator_path": "paired_diff.newly_accepted",
        "reach_class": "operator_blocked",
        "mechanism_path": "type_collapse.mechanism",
        "engine_sha_path": "engine_provenance.sha256",
        "engine_line_path": "engine_provenance.line",
        "extra_paths": {
            "go_no_go": "go_no_go",
            "false_accepts_ids": "bars.bar_2_zero_false_accepts_from_list_tuple_collapse."
                                 "false_accepts_fail_the_corpus_own_assert_semantics",
            "also_wrong_in_general_coincidental_fits":
                "bars.bar_2_zero_false_accepts_from_list_tuple_collapse."
                "also_wrong_in_general_coincidental_fits",
            "baseline_pass_ids_with_a_non_scalar_expected":
                "baseline_36_are_all_scalar_output.baseline_pass_ids_with_a_non_scalar_expected",
        },
        # THE MECHANISM-SHAPED CONDITION.  This residual refutes the SEED-ONLY
        # comparator fix, and it refutes it BECAUSE list and tuple are the same
        # `Value::Tuple` (`type_collapse.mechanism`, verified live in that
        # artifact).  That is a property of the engine's value layer, and it is
        # checkable live -- so the residual lapses the moment the value layer
        # distinguishes them.  A residual that cannot lapse is a lie with a
        # long half-life.
        "conditions": (
            {"ckind": "fact_equals", "filter_value": "value_layer_list_eq_tuple",
             "expected_str": "1",
             "why": "`type_collapse.mechanism`: a node attr set to [1,2,3] reads back "
                    "as (1,2,3).  The 12 false accepts are a consequence of that and "
                    "of nothing else.  Distinguish List from Tuple in the value layer "
                    "and this refutation no longer applies -- which is exactly what "
                    "arc C of results/arc6_valuelayer.json did on engine "
                    "8311d4356082 (NOT the engine in this tree)."},
        ),
    },
)


# --------------------------------------------------------------------------- #
#  DELIBERATELY LEFT OUT.  Each of these is a figure the arc-6 write-ups state
#  in PROSE and that no artifact in `results/` carries at any path.  The
#  protocol says to say so and leave it out rather than transcribe it, so this
#  list is data and ships in the results artifact.
# --------------------------------------------------------------------------- #
DELIBERATELY_NOT_INGESTED: Tuple[Dict[str, str], ...] = (
    {"claim": "only 39/257 tasks have the f(int)->int signature seam B's "
              "grammar can emit; 218 (85%) are excluded before semantics apply",
     "stated_in": "PROGRAM_SYNTHESIS_ARC6_PREREG.md §1",
     "searched": "results/arc6_bc_ceiling.json",
     "why_left_out": "no path in the artifact carries either 39 or 218 as a "
                     "signature count; the artifact's own B levels (0/1/3/5/4/83) "
                     "are ingested instead"},
    {"claim": "35 of 36 seam-D atoms carried a verbatim prompt substring and "
              "cue-matched only their own task",
     "stated_in": "the arc-6 hand-off note",
     "searched": "results/arc6_d_loo.json",
     "why_left_out": "the artifact carries NO `verbatim` key at any path. What "
                     "it does carry -- LOO 0/36, exactly one FOREIGN cue match "
                     "(task 266), zero foreign applicable atoms -- is ingested "
                     "and says the same thing from measurement"},
    {"claim": "HS1 failed 0 of 10 converted (tier 0)",
     "stated_in": "PROGRAM_SYNTHESIS_ARC6_PREREG.md amendment A2",
     "searched": "the six artifacts named for this rung",
     "why_left_out": "results/arc6_tier0.json was not in the ingest set for "
                     "this rung; the structural residual is ingested from "
                     "arc6_structural_ceiling.json (strict reach 6, inventory "
                     "42) and carries no conversion claim it cannot source"},
    {"claim": "the row-verdict null is superseded -- arm C converted 12 more ids",
     "stated_in": "results/arc6_valuelayer.json",
     "searched": "n/a -- this artifact is real and was read",
     "why_left_out": "it is a SUCCESS, not a refutation, so it mints no "
                     "residual. It is used the other way round: it is the "
                     "evidence that the row-verdict residual's condition CAN "
                     "lapse. Measured in this tree, that condition still HOLDS "
                     "(engine 48da7257f35d, list and tuple still collapse), so "
                     "the residual is live and is NOT claimed stale"},
)


# --------------------------------------------------------------------------- #
#  Mechanical helpers.  No conditionals over graph state; no decisions.
# --------------------------------------------------------------------------- #
def _at(obj: Any, path: str) -> Any:
    """Resolve a dotted path.  Returns `None` when any step is absent — the
    caller records the miss, it never substitutes a value."""
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _n(ids: Any) -> Optional[int]:
    return len(ids) if isinstance(ids, list) else None


def load_artifacts(results_dir: str = RESULTS) -> Dict[str, Any]:
    out = {}
    for entry in SPEC:
        name = entry["artifact"]
        if name in out:
            continue
        p = os.path.join(results_dir, name)
        with open(p) as fh:
            out[name] = {"doc": json.load(fh), "path": p,
                         "sha256": _sha256_file(p)}
    return out


def build_residuals(results_dir: str = RESULTS) -> Dict[str, Any]:
    """Translate every SPEC entry into a residual record + its conditions.

    Returns `{"residuals": [...], "not_ingested": [...], "artifacts": {...}}`.
    A field whose path does not resolve is OMITTED and listed in
    `not_ingested` with the exact path that failed.
    """
    arts = load_artifacts(results_dir)
    residuals: List[Dict[str, Any]] = []
    misses: List[Dict[str, str]] = []

    for entry in SPEC:
        art = arts[entry["artifact"]]
        doc = art["doc"]
        rid = entry["rid"]

        def grab(key: str, required: bool = True) -> Any:
            path = entry.get(key)
            if path is None:
                return None
            val = _at(doc, path)
            if val is None:
                fb = entry.get(key.replace("_path", "_fallback_path"))
                if fb:
                    val = _at(doc, fb)
                    path = "%s (fallback %s)" % (path, fb)
            if val is None and required:
                misses.append({"rid": rid, "field": key, "path": path,
                               "artifact": entry["artifact"],
                               "reason": "path did not resolve; field omitted "
                                         "rather than transcribed"})
            return val

        honest_ids = grab("honest_ids_path")
        cherry_ids = grab("cherry_ids_path")
        denom = grab("denominator_path")
        mechanism = grab("mechanism_path")
        engine_sha = grab("engine_sha_path", required=False)
        engine_line = grab("engine_line_path", required=False)

        honest_n = _n(honest_ids)
        cherry_n = _n(cherry_ids)
        # a denominator path may name the POPULATION LIST rather than its
        # size; taking its length is arithmetic on the artifact, not a choice.
        if isinstance(denom, list):
            denom_n = float(len(denom))
        elif isinstance(denom, (int, float)):
            denom_n = float(denom)
        else:
            denom_n = None

        reach_class = entry["reach_class"]
        factor = REACH_CLASS_FACTOR[reach_class]
        if honest_n is not None and denom_n:
            unreached = 1.0 - (float(honest_n) / denom_n)
        else:
            unreached = None
        weight = (round(RESIDUAL_SCALE * factor * unreached, 6)
                  if unreached is not None else None)
        if weight is None:
            misses.append({"rid": rid, "field": "weight", "path": "(derived)",
                           "artifact": entry["artifact"],
                           "reason": "honest_n or denominator missing; no weight "
                                     "invented"})

        extra = {}
        for k, path in (entry.get("extra_paths") or {}).items():
            v = _at(doc, path)
            if v is None:
                misses.append({"rid": rid, "field": "extra:" + k, "path": path,
                               "artifact": entry["artifact"],
                               "reason": "path did not resolve; field omitted"})
            else:
                extra[k] = v

        rec: Dict[str, Any] = {
            "rid": rid,
            "sig_seam": entry["sig_seam"],
            "sig_lever": entry.get("sig_lever"),
            "sig_target": entry.get("sig_target"),
            "reach_class": reach_class,
            "reach_class_factor": factor,
            "ceiling_honest_n": honest_n,
            "ceiling_honest_ids": honest_ids,
            "ceiling_cherry_n": cherry_n,
            "ceiling_cherry_ids": cherry_ids,
            "denominator_n": denom_n,
            "mechanism": mechanism,
            "mechanism_source_path": entry.get("mechanism_path"),
            "weight": weight,
            "weight_formula": "RESIDUAL_SCALE(%g) * reach_class_factor(%g) * "
                              "(1 - honest_n/denominator_n)" % (RESIDUAL_SCALE, factor),
            "evidence_artifact": "results/" + entry["artifact"],
            "evidence_artifact_sha256": art["sha256"],
            "evidence_engine_sha256": engine_sha,
            "evidence_engine_line": engine_line,
            "extra": extra,
            "conditions": [dict(c) for c in entry["conditions"]],
        }
        if entry.get("reductio_ids_path"):
            r = _at(doc, entry["reductio_ids_path"])
            if r is not None:
                rec["ceiling_reductio_n"] = len(r)
                rec["ceiling_reductio_ids"] = r
        if entry.get("reach_counts_path"):
            rc = _at(doc, entry["reach_counts_path"])
            if rc is not None:
                rec["reach_class_counts"] = rc
        residuals.append(rec)

    return {"residuals": residuals, "not_ingested": misses,
            "artifacts": {k: {"path": os.path.relpath(v["path"], ROOT),
                              "sha256": v["sha256"]} for k, v in arts.items()},
            "residual_scale": RESIDUAL_SCALE,
            "reach_class_factor": dict(REACH_CLASS_FACTOR),
            "signature_vocab": {k: list(v) for k, v in SIGNATURE_VOCAB.items()}}


# --------------------------------------------------------------------------- #
#  LIVE FACT STAMPING.  A `ResidualFact{name,value}` node is a MEASURED datum
#  about the world the residual's condition reads.  Probing the substrate and
#  writing the answer down is mechanical I/O -- the rule decides whether the
#  condition still holds, this only reports what is true.
# --------------------------------------------------------------------------- #
FACT_ARTIFACTS = (
    ("arc6_a_ceiling_present", "arc6_a_ceiling.json"),
    ("arc6_bc_ceiling_present", "arc6_bc_ceiling.json"),
    ("arc6_d_loo_present", "arc6_d_loo.json"),
    ("arc6_structural_ceiling_present", "arc6_structural_ceiling.json"),
    ("arc6_verdict_pricing_present", "arc6_verdict_pricing.json"),
)


def probe_facts(sub, results_dir: str = RESULTS,
                expected_shas: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Measure the facts residual conditions read.  Pure measurement.

    * `value_layer_list_eq_tuple` — write a list and a tuple attr, read them
      back, report whether the value layer collapsed them.  This is the
      `type_collapse.mechanism` probe, run live, in this process, on this
      engine.
    * `<artifact>_present` — the evidence file is on disk with the content sha
      the residual was ingested at.
    """
    facts: Dict[str, str] = {}
    n = sub.add_node("ResidualProbe", {"lst": [1, 2, 3], "tup": (1, 2, 3)})
    at = sub.node(n)["attrs"]
    facts["value_layer_list_eq_tuple"] = "1" if at["lst"] == at["tup"] else "0"
    expected_shas = expected_shas or {}
    for name, fname in FACT_ARTIFACTS:
        p = os.path.join(results_dir, fname)
        ok = os.path.exists(p)
        if ok and fname in expected_shas:
            ok = _sha256_file(p) == expected_shas[fname]
        facts[name] = "1" if ok else "0"
    return facts


def install_facts(sub, facts: Dict[str, str]) -> List[Any]:
    """Write the measured facts into the graph as `ResidualFact` nodes."""
    return [sub.add_node("ResidualFact", {"name": k, "value": v})
            for k, v in sorted(facts.items())]
