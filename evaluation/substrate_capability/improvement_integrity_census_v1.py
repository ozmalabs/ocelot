#!/usr/bin/env python3
"""Tranche 19: IMPROVEMENT-INTEGRITY census v1 -- can the self-improvement
loop's variation families edit the self-improvement loop itself?

Boots a full agent, mirrors rule provenance the way the composers do
(_ensure_acting/_reply/_where_literal/_general_rule_provenance), then for every
active rule records: its seed, SeedSummary.skippable, which families' candidate
sets it is in (writes_chosen_action -> threshold_shift/structural_edit,
writes_reply -> reply_ablation, writes_where_literal -> rule_literal_edit),
whether the adoption gate (_rule_denylisted) would allow replacing it, and
whether it is MACHINERY: its rule JSON names a node type of the improvement
loop (the loop's own records and policies, listed below) -- a structural read.

Writes evaluation/reports/improvement_integrity_census_v1_<label>_20261010.json.
Usage: OZMA_SEED_PERSIST_DISABLED=1 python <this> <label>
"""
import json, os, sys, time
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts")]

# The improvement loop's own record and policy node types (census definition;
# tranche 19 moves the canonical list into graph data).
LOOP_TYPES = ["SelfConcern", "StandingConcern", "CapabilityAxis", "Experiment", "SeedDelta",
              "VariationOp", "VariationPolicy", "VariationCredit", "Adoption",
              "InstructionRetryPolicy", "QualiaAperture", "RuleSummary", "SeedSummary"]


def names_loop_type(rule) -> list:
    s = json.dumps(rule)
    return [t for t in LOOP_TYPES if ('"%s"' % t) in s]


def main():
    label = sys.argv[1]
    out = ROOT / f"evaluation/reports/improvement_integrity_census_v1_{label}_20261010.json"
    if out.exists():
        raise SystemExit("refusing to overwrite")
    import domains.reflective_faculty as rf
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    t0 = time.time()
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    rf._ensure_seed_chain(a.s, a.inner, a.agent, ("variation_ops", "variation_credit", "instruction_repair_retry"))
    for fn in ("_ensure_acting_rule_provenance", "_ensure_reply_rule_provenance",
               "_ensure_where_literal_rule_provenance", "_ensure_general_rule_provenance"):
        getattr(rf, fn)(a.s, a.inner)
    summ = {}
    for n in a.s.nodes("RuleSummary"):
        at = a.s.node(n)["attrs"]
        summ.setdefault(at.get("name"), at)
    rows = []
    for r in a.inner.export_rules():
        if not isinstance(r, dict) or not r.get("active", True):
            continue
        nm = r.get("name")
        at = summ.get(nm) or {}
        fams = []
        if at.get("writes_chosen_action") == 1.0:
            fams += ["threshold_shift", "structural_edit"]
        if at.get("writes_reply") == 1.0:
            fams.append("reply_ablation")
        if at.get("writes_where_literal") == 1.0:
            fams.append("rule_literal_edit")
        if any(at.get(k) == 1.0 for k in ("applicable_flip_comparison", "applicable_swap_term_leaf",
                                          "applicable_drop_match_edge", "applicable_add_match_guard")):
            fams.append("structural_edit_all_rules")
        if at.get("skippable") != 1.0:
            fams = []          # every family's candidate filter requires skippable == 1
        denied, _why = rf._rule_denylisted(a.s, nm)
        rows.append({"rule": nm, "seed": at.get("from_seed") or "", "skippable": at.get("skippable"),
                     "families": fams, "adoptable": not denied, "loop_types": names_loop_type(r),
                     **({"protected": at.get("improvement_machinery")} if "improvement_machinery" in at else {})})
    mach = [x for x in rows if x["loop_types"]]
    exposed = [x for x in mach if x["families"] and x["adoptable"]]
    report = {
        "schema": "ImprovementIntegrityCensusV1", "label": label, "elapsed_s": round(time.time() - t0, 1),
        "active_rules": len(rows), "machinery_rules": len(mach),
        "machinery_seeds": sorted({x["seed"] for x in mach if x["seed"]}),
        "family_candidates": {f: sum(1 for x in rows if f in x["families"]) for f in
                              ("threshold_shift", "structural_edit", "reply_ablation", "rule_literal_edit", "structural_edit_all_rules")},
        "machinery_family_candidates": {f: sum(1 for x in mach if f in x["families"]) for f in
                                        ("threshold_shift", "structural_edit", "reply_ablation", "rule_literal_edit", "structural_edit_all_rules")},
        "exposed_machinery_rules": len(exposed),
        "machinery_denied_at_adoption": sum(1 for x in mach if not x["adoptable"]),
        "loop_types_source": "census constant LOOP_TYPES",
        "exposed": sorted(({"rule": x["rule"], "seed": x["seed"], "families": x["families"],
                            "loop_types": x["loop_types"]} for x in exposed), key=lambda x: (x["seed"], x["rule"])),
        "rows": rows,
    }
    out.write_text(json.dumps(report, indent=1, sort_keys=True, default=str) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("rows", "exposed")}, indent=1))
    for x in report["exposed"][:60]:
        print("EXPOSED", x["seed"], x["rule"], x["families"], x["loop_types"])


if __name__ == "__main__":
    main()
