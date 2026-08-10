#!/usr/bin/env python3
"""arc6_goal_residuals_report — write `results/arc6_goal_residuals.json`.

Records what was ingested (paired id lists, never a bare count), what was
DELIBERATELY left out for lacking a measured source, the engine this ran on,
and the four GR bars measured LIVE in this process — the collapse flip, the
look-alike non-fire, the not-a-veto direction, and the condition lapse.

  OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python scripts/arc6_goal_residuals_report.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

from domains.engine_provenance import engine_preamble, provenance_stamp  # noqa: E402
engine_preamble(strict=False)

import substrate_rs as srs  # noqa: E402
from domains import goal_residual_ingest as gri  # noqa: E402
from substrate.seed_loader import manifest_for  # noqa: E402

OUT = os.path.join(ROOT, "results", "arc6_goal_residuals.json")
SEED_PATH = os.path.join(ROOT, "seeds", "goal_residuals.json")
SYNTH_SEED = os.path.join(ROOT, "seeds", "program_synthesis.json")
_BASE = {"refuted": 0.0, "arity_gap": 0.0, "mdl_bits": 1.0}
_W = {"ps_move_w_gap": 1.0, "ps_move_w_arity": 3.0, "ps_move_w_mdl": 0.5,
      "ps_move_w_residual": 1.0}


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def _boot(residuals=True):
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    cls = s.add_node("Agent", {"is_class": True})
    s._inner.add_edge_unchecked(ag, "is_a", cls)
    s._inner.load_seed_manifest(manifest_for("program_synthesis"), ag)
    if residuals:
        s._inner.load_seed_manifest(manifest_for("goal_residuals"), ag)
        s._inner.load_seed_manifest(manifest_for("math_capability_shapes"), ag)
        gri.install_facts(s, gri.probe_facts(s))
    return s, ag


def _scene(s, ag, cands):
    g = s.add_node("Goal", dict(_W, kind="synth_program", status="moves_scan",
                                ps_moves_scan_done=1.0))
    s._inner.add_edge_unchecked(ag, "has_goal", g)
    for c in cands:
        mc = s.add_node("MoveCandidate", dict(c))
        s._inner.add_edge_unchecked(g, "has_move_candidate", mc)
    return g


def _read(s, g):
    pens = {s.node(n)["attrs"]["key"]: s.node(n)["attrs"].get("residual_penalty")
            for n in s.nodes() if s.node(n)["type"] == "MoveCandidate"}
    return {"winner": s.node(g)["attrs"].get("ps_move_sel_key"),
            "winner_charged": s.node(g)["attrs"].get("ps_move_sel_residual_penalty"),
            "candidate_penalties": pens}


def _stale(s):
    return {s.node(n)["attrs"]["rid"]: s.node(n)["attrs"]["stale"]
            for n in s.nodes() if s.node(n)["type"] == "GoalResidual"}


A = dict(_BASE, move="orbit_augment", key="A", gap=100.0,
         sig_seam="enum_op_table", sig_lever="proposal",
         sig_target="mbpp_s4_residual_60")
B = dict(_BASE, move="intermediate_factor", key="B", gap=60.0,
         sig_seam="enum_op_table", sig_lever="proposal",
         sig_target="mbpp_arc4_104")


def gr1():
    out = {}
    s, ag = _boot(residuals=False)
    g = _scene(s, ag, [A, B])
    s._inner.run_rules()
    out["control_no_residual_held"] = _read(s, g)

    s, ag = _boot()
    g = _scene(s, ag, [A, B])
    s._inner.run_rules()
    out["residual_held"] = _read(s, g)

    s, ag = _boot()
    g = _scene(s, ag, [dict(A, gap=200.0), B])
    s._inner.run_rules()
    out["not_a_veto_gap_200"] = _read(s, g)

    s, ag = _boot()
    g = _scene(s, ag, [{k: v for k, v in A.items() if not k.startswith("sig_")},
                       {k: v for k, v in B.items() if not k.startswith("sig_")}])
    s._inner.run_rules()
    out["unsignatured_candidates"] = _read(s, g)
    return out


def gr2():
    out = {}
    s, _ag = _boot()
    s._inner.run_rules()
    out["as_shipped"] = _stale(s)
    s.add_node("ShapeSignature", {"kind": "math", "name": "report_fixture",
                                  "signature": "[]"})
    s._inner.run_rules()
    out["after_adding_one_math_shape"] = _stale(s)

    # 2026-08-03 (COHERENCE RECONCILIATION): on the coherent tree the measured
    # fact is "0" and the row-verdict residual is ALREADY stale, so the old
    # one-way "flip it to 0" demo would have been a no-op.  Both directions are
    # now recorded, from whatever the fact actually measures.
    s, _ag = _boot()
    s._inner.run_rules()
    fact = next(n for n in s.nodes() if s.node(n)["type"] == "ResidualFact"
                and s.node(n)["attrs"]["name"] == "value_layer_list_eq_tuple")
    out["value_layer_fact_as_measured"] = s.node(fact)["attrs"]["value"]
    for value in ("0", "1", "0"):
        s.set_attr(fact, "value", value)
        s._inner.run_rules()
        out["with_value_layer_fact_%s" % value] = _stale(s)
    out["value_layer_fact_reading"] = (
        "the fact is MEASURED live by probe_facts on this process's engine, not "
        "asserted.  '0' means list and tuple read back DISTINCTLY, which "
        "falsifies the row-verdict residual's condition and lapses it.  Both "
        "directions are exercised above; a one-way lapse would itself be an "
        "unrevisable claim.")
    return out


# --------------------------------------------------------------------------- #
#  2026-08-03 — THE SUPERSEDED CONDITION, KEPT VISIBLE.
#
#  This artifact was first written on engine `48da7257f35d` — arm A's binary —
#  with the value-layer adapter edits reverted out of the working tree.  That
#  tree's binary did not match its own committed source (prereg A1.1's
#  registered hazard, realised).  The numbers below are what was measured then.
#  They are NOT deleted and NOT silently overwritten: they are the reading under
#  a condition that no longer holds, and the difference between them and the
#  live section is itself the result.  See
#  `PROGRAM_SYNTHESIS_ARC6_COHERENCE.md`.
# --------------------------------------------------------------------------- #
SUPERSEDED = {
    "why_superseded":
        "measured on engine 48da7257f35d (arm A's binary) with the value-layer "
        "adapter reverted out of the working tree -- a tree whose binary did "
        "not match its own committed source.  Re-measured on the coherent tree "
        "(engine 8311d4356082 + the matching adapter).  Kept for comparison, "
        "not for use.",
    "engine_sha256":
        "48da7257f35d3046e9bd18952b817a51d9f7ffbc19b08f52965bc07c5c429929",
    "measured_at": "2026-08-03T10:08:44+1000",
    "seed_sha256_program_synthesis":
        "4e866340eb509ed59c6ebdfbf06a7710ddeb99dc88a0bd39ed4dd777b2ee71c5",
    "seed_sha256_goal_residuals":
        "199a90a48b645a739c452c55e04f3659ef43d936d3c431046b60b7a09f2b4148",
    "GR1_collapse_live": {
        "control_no_residual_held": {
            "winner": "A", "winner_charged": None,
            "candidate_penalties": {"A": None, "B": None}},
        "residual_held": {
            "winner": "B", "winner_charged": 0.0,
            "candidate_penalties": {"A": 63.0, "B": 0.0}},
        "not_a_veto_gap_200": {
            "winner": "A", "winner_charged": 63.0,
            "candidate_penalties": {"A": 63.0, "B": 0.0}},
        "unsignatured_candidates": {
            "winner": "A", "winner_charged": 0.0,
            "candidate_penalties": {"A": 0.0, "B": 0.0}},
    },
    "GR2_condition_lapse_live": {
        "as_shipped": {
            "arc6.seam_a.import_oracle": 0.0,
            "arc6.seam_b.ir_retarget": 0.0,
            "arc6.seam_c.shape_codebook": 0.0,
            "arc6.seam_d.property_atom": 0.0,
            "arc6.structural.enum_op_table": 0.0,
            "arc6.verdict.row_verdict_seed_only": 0.0,
        },
        "after_adding_one_math_shape": {
            "arc6.seam_a.import_oracle": 0.0,
            "arc6.seam_b.ir_retarget": 0.0,
            "arc6.seam_c.shape_codebook": 1.0,
            "arc6.seam_d.property_atom": 0.0,
            "arc6.structural.enum_op_table": 0.0,
            "arc6.verdict.row_verdict_seed_only": 0.0,
        },
        "value_layer_fact_as_measured": "1",
        "after_flipping_the_value_layer_fact": {
            "arc6.seam_a.import_oracle": 0.0,
            "arc6.seam_b.ir_retarget": 0.0,
            "arc6.seam_c.shape_codebook": 0.0,
            "arc6.seam_d.property_atom": 0.0,
            "arc6.structural.enum_op_table": 0.0,
            "arc6.verdict.row_verdict_seed_only": 1.0,
        },
    },
    "GR4_live_mbpp": {
        "pre_patch_pass_ids": [
            16, 20, 58, 59, 69, 82, 84, 85, 89, 90, 120, 127, 132, 135, 138,
            139, 142, 145, 227, 233, 234, 266, 276, 278, 281, 309, 312, 394,
            404, 406, 410, 433, 443, 458, 472, 477],
        "patched_pass_ids": [
            16, 20, 58, 59, 69, 82, 84, 85, 89, 90, 120, 127, 132, 135, 138,
            139, 142, 145, 227, 233, 234, 266, 276, 278, 281, 309, 312, 394,
            404, 406, 410, 433, 443, 458, 472, 477],
        "lost": [], "gained": [],
        "artifact": "results/arc6_verdict_gr_baseline.json (pre) / "
                    "results/arc6_verdict_gr4_gate.json (post, since "
                    "regenerated on the coherent engine)",
    },
}


def _gr4():
    """GR4's no-regression evidence, read back off the two battery artifacts.

    2026-08-03: "unchanged" is measured PRE-PATCH vs POST-PATCH on the SAME
    engine.  The pre-patch arm is `arc6_verdict_gr_baseline_8311d435.json` (the
    v1.11.0 seed rerun on the coherent engine for this reconciliation); the
    post-patch arm is the gate's own `arc6_verdict_gr4_gate.json`.
    """
    out = {}
    for key, fname in (("pre_patch", "arc6_verdict_gr_baseline_8311d435.json"),
                       ("patched", "arc6_verdict_gr4_gate.json")):
        p = os.path.join(ROOT, "results", fname)
        if not os.path.exists(p):
            out[key] = {"artifact": fname, "present": False}
            continue
        d = json.load(open(p))
        out[key] = {"artifact": fname,
                    "engine_sha256": d["engine_provenance"]["sha256"],
                    "seed_sha256": d["seed_sha256"],
                    "pass_ids": sorted(d["pass_ids"]),
                    "accepted_ids": sorted(d["accepted_ids"])}
    if "pass_ids" in out.get("pre_patch", {}) and "pass_ids" in out.get("patched", {}):
        a, b = set(out["pre_patch"]["pass_ids"]), set(out["patched"]["pass_ids"])
        out["patched_minus_pre_patch"] = {
            "pass_gained": sorted(b - a), "pass_lost": sorted(a - b),
            "reading": "EMPTY BOTH WAYS is the bar.  The residual patch is "
                       "inert on every candidate the live pipeline mints, "
                       "because none of them carries a signature.",
        }
    out["superseded_pin"] = {
        "pass_ids_on_48da7257": SUPERSEDED["GR4_live_mbpp"]["pre_patch_pass_ids"],
        "difference_is": "results/arc6_valuelayer.json -> "
                         "arms.C_minus_B.pass_gained, i.e. the VALUE LAYER's "
                         "own 12 gains, not anything this rung did",
    }
    return out


def main() -> int:
    ing = gri.build_residuals()
    rec = {
        "_README":
            "MEASURED CEILINGS, GRAPH-RESIDENT.  Arc 6's five ceilings and three "
            "killed seams existed only in markdown; they are now GoalResidual "
            "graph data, each with the CONDITION under which it holds, "
            "contributing a strong NEGATIVE WEIGHT (never a veto) to the "
            "existing ps_move_select collapse.  PAIRED ID LISTS, never a bare "
            "count.  Every number below was resolved from a dotted path into a "
            "results artifact; nothing was transcribed from prose (see "
            "deliberately_not_ingested).  "
            "2026-08-03 COHERENCE CORRECTION: this artifact was FIRST written on "
            "engine 48da7257f35d with the value-layer adapter reverted out of "
            "the working tree -- a tree whose binary did not match its own "
            "committed source.  It is re-measured here on the COHERENT tree "
            "(engine 8311d4356082 + the matching adapter).  The prior reading is "
            "kept verbatim under `superseded_measurement_48da7257`, not "
            "overwritten.  HEADLINE OF THE RE-MEASUREMENT: the row-verdict "
            "residual is now STALE AS SHIPPED -- its condition (list and tuple "
            "collapse in the value layer) was falsified by the restoration and "
            "GR2 lapsed it live and unprompted.  That is the mechanism working.",
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "engine_provenance": provenance_stamp(),
        "engine_sha256": provenance_stamp()["sha256"],
        "engine_archived_out_of_tree":
            "~/ozma-engine-archive/_native.abi3.so.FINAL_8311d4356082acf4f70fab"
            "61a6e943d3dcecbd404d6e90c4f72ccc9486936df0 (prereg A1.1)",
        "seeds": {
            "goal_residuals": {"path": "seeds/goal_residuals.json",
                               "sha256": _sha(SEED_PATH)},
            "program_synthesis": {"path": "seeds/program_synthesis.json",
                                  "sha256": _sha(SYNTH_SEED),
                                  "version": json.load(open(SYNTH_SEED))["version"]},
        },
        "hooked_into": {
            "rule": "ps_move_select (seeds/program_synthesis.json)",
            "why": "this project's canonical WEIGHTED COLLAPSE -- an Argmax whose "
                   "coefficients are graph data on the goal, and which already "
                   "separates POOL MEMBERSHIP (refutation, the gap>0 "
                   "earns-its-keep gate) from WEIGHT.  A held residual goes on "
                   "the weight side and nowhere else.",
            "changed": ["ps_move_mark: +ps_move_w_residual (coefficient, graph data)",
                        "ps_move_select: weight -= ps_move_w_residual * PENALTY(mc), "
                        "substituted in all five Argmax expressions"],
            "not_changed": ["ps_move_select.where", "ps_move_select.match",
                            "the Argmax SOURCE (the candidate pool)"],
        },
        "signature_matching": {
            "dimensions": ["sig_seam", "sig_lever", "sig_target"],
            "rule": "a residual matches a candidate iff, for every dimension the "
                    "RESIDUAL declares, the candidate agrees; an undeclared "
                    "dimension on the residual is a WILDCARD, and an absent "
                    "dimension on the CANDIDATE is disagreement (only the "
                    "residual may wildcard)",
            "vocabulary_is_closed": True,
            "vocabulary": ing["signature_vocab"],
            "aggregation": "max over matching non-stale residuals",
            "residual_scale": ing["residual_scale"],
            "reach_class_factor": ing["reach_class_factor"],
        },
        "residuals": ing["residuals"],
        "not_ingested_path_misses": ing["not_ingested"],
        "deliberately_not_ingested": [dict(d) for d in
                                      gri.DELIBERATELY_NOT_INGESTED],
        "artifacts_read": ing["artifacts"],
        "GR1_collapse_live": gr1(),
        "GR2_condition_lapse_live": gr2(),
        "GR4_no_regression": _gr4(),
        "superseded_measurement_48da7257": SUPERSEDED,
    }
    with open(OUT, "w") as fh:
        json.dump(rec, fh, indent=1)
        fh.write("\n")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
