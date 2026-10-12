#!/usr/bin/env python3
"""Adjudicate task-observed Python modules into capability-map groupings."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CROSSWALK = ROOT / "evaluation/reports/conversation_task_module_source_crosswalk_v1_20260928.json"
INVENTORY = ROOT / "evaluation/substrate_capability/python_source_coverage_audit_v1_1_20260928.json"
OUT = ROOT / "evaluation/reports/conversation_task_module_adjudication_v1_20260928.json"
RESULTS = ROOT / "docs/research/engine_substrate/SUBSTRATE_CONVERSATION_MODULE_SOURCE_ADJUDICATION_V1_RESULTS_20260928.md"

GROUPS = {
    "language_communication": {
        "modules": """domains.audience domains.audience_adaptation domains.audience_driven_production
domains.comparative_reference domains.comprehend_question domains.comprehend_text
domains.conceptualizer domains.construction_grammar domains.context_model
domains.conversation_deliberation domains.function_word_reference domains.instruction_reading
domains.interlocutor_model domains.interrogative_reference domains.language
domains.language_faculty_ops domains.language_production domains.language_world
domains.phase_composer_language_rules domains.preposition_roles domains.production_gate
domains.self_model domains.self_organisation_reader domains.sense_of_reference domains.wordplay""",
        "map_disposition": "Group under a proposed language, grounded reference, and communicative production capability area; keep lifecycle identity evidence in its existing row.",
        "rationale": "The locked task panel invokes these functions across comprehension, audience/interlocutor modelling, conceptualization, lexical/grammatical processing, self-report, and response production. This grouping describes a connected implementation surface, not one homogeneous capability score.",
    },
    "code_authoring": {
        "modules": "domains.code_write_growth domains.code_writing",
        "map_disposition": "Link as a distinct code-authoring subpath under the existing program synthesis/induction area, with graph-authored codebook growth kept separate from general synthesis results.",
        "rationale": "These modules author/write code and grow a write-codebook; source generation and codebook acquisition should not be conflated with the enumerative synthesis results already in that map row.",
    },
    "frame_context_representation": {
        "modules": "domains.concept_graph domains.context_collapse_plug domains.frame domains.interlocutor_collapse_plug",
        "map_disposition": "Create a separate graph-resident concept/frame/context representation area or link to a reviewed ontology row; do not count these as evidence that dependency cuts have low width.",
        "rationale": "These modules represent graph-resident dimensions, frames, and context-model plugs. Their presence does not establish that runtime rule dependencies factor at cheap cuts.",
    },
    "external_and_perceptual_adapters": {
        "modules": "domains.fetch_dispatch domains.upload_text_read",
        "map_disposition": "Link fetch dispatch to tools/external I/O and upload-text decoding to vision/perception; preserve their different effect boundaries.",
        "rationale": "The modules bridge host fetching and attached-text perception into runtime processing; they are adapters, not shared pure language operators.",
    },
    "lexical_reference_support": {
        "modules": "domains.reference_slab domains.seed_registry domains.wiktionary_reference domains.wordnet_membership",
        "map_disposition": "Link as lexical/reference data and loader support for the language area; do not create separate general capability scores for storage or seed registration.",
        "rationale": "These provide indexed reference storage, seed declarations, and lexical lookup data. They support observed routes but are not independently scored cognition in this panel.",
    },
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    crosswalk = json.loads(CROSSWALK.read_text())
    inventory = json.loads(INVENTORY.read_text())
    inventory_by_module = {row["module"]: row for row in inventory["files"]}
    rows_by_module = {row["module"]: row for row in crosswalk["module_rows"]}
    unlinked = {module for module, row in rows_by_module.items() if not row["capability_rows"]}
    assigned: dict[str, str] = {}
    for group, spec in GROUPS.items():
        for module in spec["modules"].split():
            if module in assigned:
                raise SystemExit(f"module assigned more than once: {module}")
            assigned[module] = group
    if set(assigned) != unlinked:
        raise SystemExit(f"adjudication mismatch: unassigned={sorted(unlinked-set(assigned))}; extra={sorted(set(assigned)-unlinked)}")

    module_rows = []
    current_source_drift = []
    for module in sorted(unlinked):
        cross = rows_by_module[module]
        source = inventory_by_module[module]
        source_path = ROOT / source["path"]
        current_hash = sha(source_path)
        drift = current_hash != source["sha256"]
        if drift:
            current_source_drift.append(source["path"])
        group = GROUPS[assigned[module]]
        module_rows.append({
            "module": module,
            "source_path": source["path"],
            "locked_source_sha256": source["sha256"],
            "current_source_sha256": current_hash,
            "current_source_matches_locked_inventory": not drift,
            "module_docstring_first_line_at_census": source["module_docstring_first_line"],
            "public_top_level_symbols_at_census": source["public_top_level_symbols"],
            "observed_conditions": cross["conditions"],
            "proposed_group": assigned[module],
            "map_disposition": group["map_disposition"],
            "rationale": group["rationale"],
        })

    checks = {
        "source_activation_crosswalk_passed": crosswalk["all_checks_pass"],
        "all_37_unlinked_modules_adjudicated_once": len(unlinked) == 37 and set(assigned) == unlinked,
        "all_adjudicated_paths_have_locked_source_hashes": all(row["locked_source_sha256"] for row in module_rows),
        "both_input_hashes_are_sha256": all(len(value) == 64 for value in
                                             (sha(CROSSWALK), sha(INVENTORY))),
    }
    output = {
        "schema_version": 1,
        "run_id": "conversation-task-module-adjudication-v1-20260928",
        "input_sha256": {"crosswalk": sha(CROSSWALK), "source_inventory": sha(INVENTORY)},
        "current_source_drift_paths": current_source_drift,
        "current_source_drift_count": len(current_source_drift),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "group_counts": {name: sum(row["proposed_group"] == name for row in module_rows)
                         for name in GROUPS},
        "module_rows": module_rows,
        "claim_boundary": "This is a source-use adjudication for modules observed in five authored conversation tasks. It proposes map groupings; it does not establish module necessity, capability quality, module independence, or workload prevalence. One source path has changed since the locked capture and requires current-source revalidation before direct map attribution.",
    }
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")

    lines = [
        "# Conversation module source adjudication v1",
        "",
        "Date: 2026-09-28  ",
        "Status: reviewed source-use grouping of the 37 task-observed Python modules that lacked direct capability-map links.",
        "",
        "## Outcome",
        "",
        "The crosswalk found 40 distinct called modules across five authored conversation tasks; three already had map links and 37 did not. All 37 were assigned once to a proposed map disposition using the locked source inventory's module docstring, symbol list, source hash, and task-condition footprint. The dispositions are conservative grouping decisions, not claims of causal necessity or independent capabilities.",
        "",
        "| Proposed grouping | Count | Proposed map action |",
        "|---|---:|---|",
    ]
    for name, spec in GROUPS.items():
        count = sum(row["proposed_group"] == name for row in module_rows)
        lines.append(f"| `{name}` | {count} | {spec['map_disposition']} |")
    lines += [
        "",
        f"Current-source comparison found {len(current_source_drift)} path changed since the locked inventory: "
        + (", ".join(f"`{p}`" for p in current_source_drift) if current_source_drift else "none")
        + ". Keep its locked-run observation, but refresh its current-source source-map adjudication before linking it as present-day behavior.",
        "",
        "The most important tractability boundary is explicit: concept/frame/context representation modules are not evidence of low dependency width or a cheap cut. Lexical slabs, seed registration, and lookup corpora are support surfaces and should not be counted as stand-alone reasoning capabilities. Code authoring and codebook growth remain distinct from enumerative program synthesis.",
        "",
        "## Evidence and reproducibility",
        "",
        "The machine record stores all 37 module paths, locked/current file hashes, observed condition sets, inventory docstrings/symbols, proposed group, and rationale. Its inputs are hash-linked to the [module activation crosswalk](../../../evaluation/reports/conversation_task_module_source_crosswalk_v1_20260928.json) and the [Python source census](../../../evaluation/substrate_capability/python_source_coverage_audit_v1_1_20260928.json). Reproduce with `python3 scripts/adjudicate_substrate_conversation_module_sources_v1.py`.",
        "",
        "Next: update capability rows from this adjudication only after current-source review of changed files; rerun the source-coverage census as a new version; then select fresh task families for activation profiling. The full trace remains limited to conversation tasks and does not support a general substrate capability distribution.",
        "",
    ]
    RESULTS.write_text("\n".join(lines))
    print(json.dumps({"all_checks_pass": output["all_checks_pass"],
                      "group_counts": output["group_counts"],
                      "current_source_drift_paths": current_source_drift,
                      "machine": str(OUT.relative_to(ROOT)),
                      "results": str(RESULTS.relative_to(ROOT))}, indent=2))
    if not output["all_checks_pass"]:
        raise SystemExit("module adjudication checks failed")


if __name__ == "__main__":
    main()
