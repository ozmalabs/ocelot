#!/usr/bin/env python3
"""scripts/rule_signature_measure.py — the AR4 measurement, per
docs/research/engine_substrate/RULE_SIGNATURE_SLICE_PREREG.md.

MEASUREMENT SCRIPT ONLY (host tooling, not agent runtime): boots a full
agent (`substrate.boot_all.load_all_seeds`, the same pattern
`tests/test_gap_awareness_migrated.py` / `tests/test_self_concern_promote_
migrated.py` already use), reads the REAL, seed-sourced `RuleSummary`
population, runs every registered probe through BOTH rankings —

  * production (UNCHANGED): `domains.reflective_faculty._pick_acting_rule`
    / `_pick_reply_rule`
  * structural (NEW, additive, never called by production):
    `domains.rule_signature.pick_acting_rule_structural` /
    `pick_reply_rule_structural`

— and reports the AR1/AR2 comparison. Writes a machine-readable
`rule_signature_measurement_results.json` next to this script for the
RESULTS doc to cite exact numbers from, and prints a human-readable report
to stdout.

Nothing in this script is agent decision logic — it is a fixed, pre-
registered probe table (built in `RULE_SIGNATURE_SLICE_PREREG.md`'s AR1/AR2
BEFORE this script's numbers were looked at) run once through two READ-ONLY
ranking functions.
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from domains.engine_provenance import engine_preamble  # noqa: E402
engine_preamble(strict=False)

from substrate.boot_core import boot_core  # noqa: E402
from substrate.boot_all import load_all_seeds  # noqa: E402
import domains.reflective_faculty as rf  # noqa: E402
import domains.rule_signature as rsig  # noqa: E402


class _Agent:
    """Minimal duck-typed wrapper — identical shape to
    tests/test_acting_variant.py's own `_Agent` (harness glue only, not
    agent logic)."""
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


# ---------------------------------------------------------------------------
# AR1/AR2 — the pre-registered probe table.
#
# Class A ("where-native"): a literal atom present in the TARGET rule's own
# `where`-signature, absent from the target's NAME, and — verified by
# `scratch_investigate/discover_probes2.py` (a mechanical set-difference
# scan over the real 46-rule pool, not a guess) — absent from every OTHER
# candidate's name AND every other candidate's where-signature, so the
# ground truth is unambiguous. Prediction (pre-registered): structural
# finds it, name-keyword misses it.
#
# Class B ("name-native"): a word present in the TARGET rule's own NAME,
# absent from the target's own where-clause content, and absent from every
# OTHER candidate's where-clause content (same discovery scan). Ground
# truth is still the target (the word names it) — but the info that proves
# it lives outside the where-only signature's scope. Prediction
# (pre-registered): name-keyword finds it, structural (where-only, by
# §11.2's own scope decision) misses it or scores it 0 — a scope-correct
# null, not a defect, named in advance.
#
# Class C ("fixture-neutral"): real, distinct `residual_predicates` arrays
# lifted verbatim from existing test fixtures (test_acting_variant.py,
# test_adoption.py, test_self_improvement_visibility_migrated.py,
# test_dialect_experiment_terms.py, test_frozen_core_invariant.py,
# test_experiment_composer.py, test_structural_variant.py,
# test_composers_graph.py, test_self_delta.py) — every DISTINCT array found
# by `grep -n '"residual_predicates":'` across those files. NOT an
# independent oracle (see PREREG AR1) — reported as raw agreement rate
# only, never as a correctness claim.
# ---------------------------------------------------------------------------

CLASS_A_ACTING = [
    ("af_choose_action", "armed"),
    ("bc_want_food", "wants"),
    ("pursue_active_goal", "move"),
    ("hop_descend_gradient", "cell"),
    ("mm_choose", "enabled"),
    ("qf_hop_route", "portal"),
    ("choose_action", "salient"),
    ("enact_forced_action", "babble"),
]

CLASS_A_REPLY = [
    ("instruction_world_action_floor", "episode"),
    ("reply_attachment_from_decoded_text", "upload"),
    ("elaboration_exhausted", "detailchunk"),
    ("reply_topic_repeat_known", "believed"),
    ("reply_honest_floor", "comprehends"),
    ("reply_self_account_miss", "path"),
    ("reply_topic_unresolved", "query"),
    ("eig_propose_order_n_humanoid_goal_from_locally_verified_instruction", "simulator"),
    ("note_reported_gap", "broken"),
    ("note_unhandled_instruction_gap", "outcome"),
    ("iu_acknowledge_pending_instruction_hypothesis", "dictionary"),
    ("iu_hold_ambiguous_interpretation", "alternative"),
]

CLASS_B_ACTING = [
    ("bc_do_rest", "rest"),
    ("pursue_active_goal", "pursue"),
    ("hop_descend_gradient", "gradient"),
    ("qf_hop_route", "route"),
    ("qf_hop_direct", "direct"),
    ("seek_to_target", "target"),
    ("choose_safe_action", "safe"),
    ("enact_forced_action", "forced"),
]

CLASS_B_REPLY = [
    ("elaboration_exhausted", "exhausted"),
    ("reply_attachment_from_document", "document"),
    ("reply_held_capability", "held"),
    ("reply_to_adjacency_pair", "pair"),
    ("mint_reply_flag_concern", "mint"),
    ("mint_self_improvement_concern_confident", "confident"),
    ("ask_clarification_self_improvement", "clarification"),
    ("reply_self_kind_denial", "denial"),
    ("steer_clarify_no_match", "clarify"),
    ("eig_propose_order_n_humanoid_goal_from_locally_verified_instruction", "humanoid"),
    ("eig_abstain_when_no_ready_embodied_developmental_capability_exists", "abstain"),
    ("note_reported_gap", "reported"),
]

CLASS_C_PROBES = [
    ["test", "send", "judge", "gradient"],
    ["adopt"],
    ["test", "vary", "moon"],
    ["comprehend", "reply"],
    ["language", "syntax"],
    ["test", "vary", "send", "judge", "embed"],
    ["test", "vary", "send", "judge", "embed", "gradient"],
    ["test", "vary", "send", "judge"],
    ["test"],
    ["judge"],
    ["test", "send", "judge", "structure", "gradient", "drop"],
    ["test", "send", "judge", "structure", "flip"],
    ["test", "send", "judge", "structure", "gradient", "flip"],
    ["test", "send", "judge", "structure", "gradient", "swap"],
    ["vary", "send", "judge"],
    ["vary", "send"],
]

AR2_MIN_N_TOTAL = 30
AR2_MIN_N_PER_CLASS = 8
AR2_MIN_WIN_MARGIN = 5


def _boot_full_agent():
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    rep = load_all_seeds(ag)
    return ag, rep


def _run_class(ag, probes, kind: str, oracle: bool):
    """kind: 'acting' or 'reply'. oracle: True for A/B (ground truth is the
    probe's own target), False for C (agreement-rate only)."""
    pick_prod = rf._pick_acting_rule if kind == "acting" else rf._pick_reply_rule
    pick_struct = rsig.pick_acting_rule_structural if kind == "acting" else rsig.pick_reply_rule_structural
    results = []
    for target, word in probes:
        prod = pick_prod(ag, [word])
        struct = pick_struct(ag.s, ag.inner, [word])
        row = {
            "target": target, "word": word, "kind": kind,
            "production_pick": prod.get("name"),
            "structural_pick": struct.get("name"),
            "structural_score": struct.get("score"),
        }
        if oracle:
            row["oracle"] = target
            row["production_correct"] = (prod.get("name") == target)
            row["structural_correct"] = (struct.get("name") == target)
        else:
            row["agree"] = (prod.get("name") == struct.get("name"))
        results.append(row)
    return results


def _run_class_c(ag, probes):
    results = []
    for preds in probes:
        for kind, pick_prod, pick_struct in (
            ("acting", rf._pick_acting_rule, rsig.pick_acting_rule_structural),
            ("reply", rf._pick_reply_rule, rsig.pick_reply_rule_structural),
        ):
            prod = pick_prod(ag, preds)
            struct = pick_struct(ag.s, ag.inner, preds)
            results.append({
                "predicates": preds, "kind": kind,
                "production_pick": prod.get("name"),
                "structural_pick": struct.get("name"),
                "agree": (prod.get("name") == struct.get("name")),
            })
    return results


def _class_summary(rows):
    n = len(rows)
    struct_correct = sum(1 for r in rows if r["structural_correct"])
    prod_correct = sum(1 for r in rows if r["production_correct"])
    both = sum(1 for r in rows if r["structural_correct"] and r["production_correct"])
    neither = sum(1 for r in rows if not r["structural_correct"] and not r["production_correct"])
    struct_only = sum(1 for r in rows if r["structural_correct"] and not r["production_correct"])
    prod_only = sum(1 for r in rows if r["production_correct"] and not r["structural_correct"])
    margin = abs(struct_correct - prod_correct)
    powered = n >= AR2_MIN_N_PER_CLASS
    directional = powered and margin >= AR2_MIN_WIN_MARGIN
    return {
        "n": n, "structural_correct": struct_correct, "production_correct": prod_correct,
        "both_correct": both, "neither_correct": neither,
        "structural_only": struct_only, "production_only": prod_only,
        "margin": margin, "powered_per_class": powered,
        "directional_claim_allowed": directional,
        "winner": ("structural" if struct_correct > prod_correct
                    else "production" if prod_correct > struct_correct else "tie")
                    if directional else "underpowered_no_claim",
    }


def main():
    print("Booting full agent (load_all_seeds) ...", flush=True)
    ag, boot_rep = _boot_full_agent()
    print(f"  loaded {boot_rep['loaded']}/{boot_rep['total']} seeds, "
          f"{len(boot_rep['failed'])} concept-level failures (pre-existing, unrelated)", flush=True)

    print("Ensuring production provenance (UNCHANGED functions) ...", flush=True)
    rf._ensure_acting_rule_provenance(ag.s, ag.inner)
    rf._ensure_reply_rule_provenance(ag.s, ag.inner)
    n_acting = sum(1 for n in ag.s.nodes("RuleSummary") if ag.s.node(n)["attrs"].get("writes_chosen_action") == 1.0)
    n_reply = sum(1 for n in ag.s.nodes("RuleSummary") if ag.s.node(n)["attrs"].get("writes_reply") == 1.0)
    print(f"  RuleSummary population: {n_acting} acting-eligible, {n_reply} reply-eligible", flush=True)

    print("Minting where_signature_json (NEW, additive attr) ...", flush=True)
    touched = rsig.ensure_where_signature(ag.s)
    print(f"  where_signature_json minted on {touched} RuleSummary nodes", flush=True)

    print("Running Class A (where-native, oracle) ...", flush=True)
    class_a = (_run_class(ag, CLASS_A_ACTING, "acting", oracle=True)
               + _run_class(ag, CLASS_A_REPLY, "reply", oracle=True))
    print("Running Class B (name-native, oracle) ...", flush=True)
    class_b = (_run_class(ag, CLASS_B_ACTING, "acting", oracle=True)
               + _run_class(ag, CLASS_B_REPLY, "reply", oracle=True))
    print("Running Class C (fixture-neutral, non-oracle) ...", flush=True)
    class_c = _run_class_c(ag, CLASS_C_PROBES)

    summary_a = _class_summary(class_a)
    summary_b = _class_summary(class_b)
    n_total = len(class_a) + len(class_b)
    agree_c = sum(1 for r in class_c if r["agree"])

    out = {
        "boot": {"loaded": boot_rep["loaded"], "total": boot_rep["total"],
                 "failed": len(boot_rep["failed"])},
        "rule_summary_population": {"acting_eligible": n_acting, "reply_eligible": n_reply,
                                     "where_signature_minted": touched},
        "ar2_floor": {"min_n_total": AR2_MIN_N_TOTAL, "min_n_per_class": AR2_MIN_N_PER_CLASS,
                      "min_win_margin": AR2_MIN_WIN_MARGIN,
                      "n_total_reached": n_total, "floor_met": n_total >= AR2_MIN_N_TOTAL
                      and len(class_a) >= AR2_MIN_N_PER_CLASS and len(class_b) >= AR2_MIN_N_PER_CLASS},
        "class_a": {"rows": class_a, "summary": summary_a},
        "class_b": {"rows": class_b, "summary": summary_b},
        "class_c": {"rows": class_c, "n": len(class_c), "agree_count": agree_c,
                     "agree_rate": agree_c / len(class_c) if class_c else None},
    }

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "rule_signature_measurement_results.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)

    print("\n=== SUMMARY ===")
    print(f"N total (A+B): {n_total}  (AR2 floor: {AR2_MIN_N_TOTAL}, per-class floor: {AR2_MIN_N_PER_CLASS})")
    print(f"Class A (where-native, n={summary_a['n']}): structural_correct={summary_a['structural_correct']} "
          f"production_correct={summary_a['production_correct']} margin={summary_a['margin']} "
          f"winner={summary_a['winner']}")
    print(f"Class B (name-native,  n={summary_b['n']}): structural_correct={summary_b['structural_correct']} "
          f"production_correct={summary_b['production_correct']} margin={summary_b['margin']} "
          f"winner={summary_b['winner']}")
    print(f"Class C (fixture-neutral, non-oracle, n={len(class_c)}): agree_rate={out['class_c']['agree_rate']:.3f}")
    print(f"\nResults written to {out_path}")
    return out


if __name__ == "__main__":
    main()
