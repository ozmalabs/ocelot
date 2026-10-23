"""Fail-closed analyzer for P22 independent-goal checkpoint panels."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from evaluation.process_mastery.improvement_estimand import summarize_families

PHASE = "linear-p22-v1"
ARMS = ("unchanged", "adaptive_only", "invention_only", "full")
GENERATIONS = (1, 2, 3)
RESOURCE_FIELDS = (
    "primitive_work", "cumulative_primitive_work", "native_rule_steps",
    "native_rule_term_evaluations",
    "native_model_calls", "search_attempts", "training_data_exposures",
    "training_data_bytes", "retrieval_work", "proposal_work",
    "verification_work", "model_refinement_work", "definition_decode_work",
    "approval_cost", "rollback_work", "thinking_budget_spent",
    "serialized_graph_bytes", "native_graph_memory_bytes",
    "process_peak_rss_bytes", "wall_time_seconds",
)
MATCHED_RESOURCE_FIELDS = tuple(field for field in RESOURCE_FIELDS
                                if field != "wall_time_seconds")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_sha(value) -> str:
    return _sha(json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8"))


def _wilson(successes: int, n: int) -> list[float] | None:
    if n <= 0:
        return None
    z = 1.959963984540054
    p = successes / n
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    radius = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return [center - radius, center + radius]


def _mcnemar_exact(left_only: int, right_only: int) -> dict:
    discordant = left_only + right_only
    if discordant == 0:
        return {"left_only": 0, "right_only": 0, "p_two_sided": 1.0}
    tail = sum(math.comb(discordant, i)
               for i in range(min(left_only, right_only) + 1)) / (2 ** discordant)
    return {"left_only": left_only, "right_only": right_only,
            "p_two_sided": min(1.0, 2 * tail)}


def _bootstrap_mean_interval(values: list[float], *, seed: int,
                             draws: int = 10000) -> list[float] | None:
    if not values:
        return None
    rng = random.Random(seed)
    n = len(values)
    means = [sum(values[rng.randrange(n)] for _ in range(n)) / n
             for _ in range(draws)]
    means.sort()
    lower = max(0, math.ceil(0.025 * draws) - 1)
    upper = min(draws - 1, math.ceil(0.975 * draws) - 1)
    return [means[lower], means[upper]]


def _resource_value(row: dict, name: str):
    value = row.get(name)
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value < 0):
        return None
    return value


def _verify_preregistration(payload: dict, path: Path, failures: list[str]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
        try:
            prereg = json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r"^P22_FREEZE_JSON: (\{.*\})$", text, re.MULTILINE)
            if not match:
                raise
            prereg = json.loads(match.group(1))
    except (OSError, json.JSONDecodeError):
        failures.append("preregistration_unreadable")
        return
    recorded = payload.get("preregistration_sha256")
    actual = _sha(path.read_bytes())
    if recorded != actual:
        failures.append("preregistration_hash_mismatch")
    frozen = prereg.get("freeze", {})
    frozen_allocation = frozen.get("allocation_plan", frozen.get("allocation"))
    if payload.get("allocation_plan") != frozen_allocation:
        failures.append("frozen_allocation_mismatch")
    if payload.get("allocation_sha256") != frozen.get("allocation_sha256"):
        failures.append("allocation_hash_mismatch")
    if payload.get("freeze_commit") != frozen.get("freeze_commit"):
        failures.append("freeze_commit_mismatch")
    frozen_provenance = frozen.get("provenance")
    if (not isinstance(frozen_provenance, dict)
            or payload.get("provenance") != frozen_provenance):
        failures.append("frozen_provenance_mismatch")


def analyze(payload: dict, *, preregistration: str | Path | None = None) -> dict:
    """Validate every expected row, then report paired estimates without imputation."""
    failures: list[str] = []
    if not isinstance(payload, dict) or payload.get("phase") != PHASE:
        return {"phase": PHASE, "status": "NOT_ESTABLISHED",
                "failures": ["phase_or_payload_mismatch"]}
    split = payload.get("split")
    if split not in {"development", "heldout"}:
        failures.append("unknown_split")
    if split == "development" and payload.get("heldout_accessed") is not False:
        failures.append("development_holdout_access")
    if split == "heldout":
        if preregistration is None:
            failures.append("heldout_requires_preregistration")
        else:
            _verify_preregistration(payload, Path(preregistration), failures)
        attestation = payload.get("provenance", {}).get("runtime_attestation", {})
        if attestation.get("status") != "ATTESTED" or attestation.get("issues"):
            failures.append("runtime_not_attested")
        if payload.get("status") != "heldout_pending_analysis":
            failures.append("heldout_status_mismatch")
        if isinstance(plan := payload.get("allocation_plan"), dict):
            for family in plan.get("families", []):
                if len(plan.get("world_ids_by_family", {}).get(family, [])) < 200:
                    failures.append(f"heldout_world_panel_too_small:{family}")
                if len(plan.get("validation_world_ids_by_family", {}).get(family, [])) < 200:
                    failures.append(f"validation_world_panel_too_small:{family}")
                if len(plan.get("selection_world_ids_by_family", {}).get(family, [])) < 200:
                    failures.append(f"selection_world_panel_too_small:{family}")

    plan = payload.get("allocation_plan")
    if not isinstance(plan, dict):
        failures.append("allocation_missing")
        plan = {}
    families = plan.get("families")
    world_ids = plan.get("world_ids_by_family")
    generations = plan.get("generations")
    arms = plan.get("arms")
    if (not isinstance(families, list) or not families
            or len(families) != len(set(families))
            or not isinstance(world_ids, dict)
            or set(world_ids) != set(families)):
        failures.append("family_allocation_invalid")
        families = []
        world_ids = {}
    # Evaluation, validation, selection and training identities are distinct allocation
    # domains. Keep this check here as well as in the runner so a malformed
    # payload cannot make a reused development world look like fresh evidence.
    validation_ids = plan.get("validation_world_ids_by_family")
    selection_ids = plan.get("selection_world_ids_by_family")
    training_ids = plan.get("training_world_ids_by_family")
    seeds_by_split = plan.get("seeds_by_split_family")
    if (not isinstance(validation_ids, dict) or set(validation_ids) != set(families)
            or not isinstance(selection_ids, dict) or set(selection_ids) != set(families)
            or not isinstance(training_ids, dict) or set(training_ids) != set(families)
            or not isinstance(seeds_by_split, dict)
            or set(seeds_by_split) != {"training", "selection", "validation", "heldout"}):
        failures.append("training_selection_or_validation_allocation_invalid")
        validation_ids, selection_ids, training_ids = {}, {}, {}
        seeds_by_split = {}
    else:
        seen_allocation_ids = set()
        for family in families:
            eval_panel = world_ids.get(family)
            validation_panel = validation_ids.get(family)
            selection_panel = selection_ids.get(family)
            training_panel = training_ids.get(family)
            for label, panel in (("evaluation", eval_panel),
                                 ("validation", validation_panel),
                                 ("selection", selection_panel),
                                 ("training", training_panel)):
                if (not isinstance(panel, list) or len(panel) != len(set(panel))
                        or any(not isinstance(item, str) or not item for item in panel)):
                    failures.append(f"{label}_allocation_invalid:{family}")
                    continue
            if all(isinstance(panel, list) for panel in
                   (eval_panel, validation_panel, selection_panel, training_panel)):
                panels = [set(eval_panel), set(validation_panel),
                          set(selection_panel), set(training_panel)]
                if any(panels[left] & panels[right]
                       for left in range(len(panels))
                       for right in range(left + 1, len(panels))):
                    failures.append(f"split_identity_overlap:{family}")
                current_allocation_ids = set.union(*panels)
                if seen_allocation_ids & current_allocation_ids:
                    failures.append("allocation_identity_reused_across_families_or_splits")
                seen_allocation_ids.update(current_allocation_ids)
        concrete_seeds = set()
        for split_name, family_seeds in seeds_by_split.items():
            if not isinstance(family_seeds, dict) or set(family_seeds) != set(families):
                failures.append(f"seed_allocation_invalid:{split_name}")
                continue
            for family in families:
                values = family_seeds[family]
                expected_seed_count = len({
                    "heldout": world_ids,
                    "validation": validation_ids,
                    "selection": selection_ids,
                    "training": training_ids,
                }[split_name].get(family, []))
                if (not isinstance(values, list) or len(values) != expected_seed_count
                        or any(isinstance(seed, bool) or not isinstance(seed, int)
                               or seed < 0 for seed in values)
                        or len(values) != len(set(values))):
                    failures.append(f"seed_allocation_invalid:{split_name}:{family}")
                    continue
                if concrete_seeds.intersection(values):
                    failures.append("seed_reused_across_split_or_family")
                concrete_seeds.update(values)
            if split == "heldout" and isinstance(validation_panel, list):
                if len(validation_panel) < 200:
                    failures.append(f"validation_world_panel_too_small:{family}")
    if generations != list(GENERATIONS):
        failures.append("generation_allocation_invalid")
    if arms != list(ARMS):
        failures.append("arm_allocation_invalid")
    ancestor_digests = plan.get("ancestor_checkpoint_digests")
    expected_ancestor_keys = {f"{family}:{arm}" for family in families for arm in ARMS}
    if (not isinstance(ancestor_digests, dict)
            or set(ancestor_digests) != expected_ancestor_keys
            or any(not ancestor_digests.get(key) for key in expected_ancestor_keys)):
        failures.append("ancestor_checkpoint_roots_invalid")
        ancestor_digests = {}

    expected = set()
    for family in families:
        ids = world_ids.get(family)
        if (not isinstance(ids, list) or not ids or len(ids) != len(set(ids))
                or any(not isinstance(world_id, str) or not world_id for world_id in ids)):
            failures.append(f"world_allocation_invalid:{family}")
            continue
        expected.update((family, generation, world_id, arm)
            for generation in GENERATIONS for world_id in ids for arm in ARMS)

    rows = payload.get("checkpoint_rows")
    if not isinstance(rows, list):
        failures.append("checkpoint_rows_missing")
        rows = []
    indexed = {}
    checkpoint_ids = {}
    world_bindings = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            failures.append(f"malformed_row:{index}")
            continue
        key = (row.get("family"), row.get("generation"),
               row.get("world_id"), row.get("arm"))
        if key in indexed:
            failures.append(f"duplicate_row:{key}")
            continue
        indexed[key] = row
        world_binding_key = key[0], key[2]
        binding = (row.get("goal_digest"), row.get("world_digest"))
        if not all(binding):
            failures.append(f"world_binding_missing:{world_binding_key}")
        previous_binding = world_bindings.setdefault(world_binding_key, binding)
        if previous_binding != binding:
            failures.append(f"world_binding_changed_across_arms_or_generations:{world_binding_key}")
        if key not in expected:
            failures.append(f"unexpected_row:{key}")
        status = row.get("status")
        if status != "scored":
            failures.append(f"non_scored_outcome:{key}:{status}")
        learner_status = row.get("native_learner_status")
        if learner_status not in {
                "COMPLETED", "RULE_BUDGET_EXHAUSTED",
                "PRIMITIVE_BUDGET_OVERRUN", "RULE_PROGRESS_LIMIT_OVERRUN"}:
            failures.append(f"native_learner_outcome_missing_or_invalid:{key}")
        if row.get("native_task_status") not in {
                "solved", "stuck", "active", "not_dispatched"}:
            failures.append(f"native_task_outcome_missing_or_invalid:{key}")
        if row.get("primitive_budget_respected") is not True:
            failures.append(f"native_primitive_budget_violation:{key}")
        if row.get("rule_progress_limit_respected") is not True:
            failures.append(f"native_rule_progress_limit_violation:{key}")
        if row.get("approval_events_added") != 0:
            failures.append(f"heldout_approval_event_created:{key}")
        if row.get("world_receipts_added") != 0:
            failures.append(f"heldout_world_receipt_created:{key}")
        score = row.get("score")
        if (isinstance(score, bool) or not isinstance(score, (int, float))
                or not math.isfinite(score) or score not in (0, 1)):
            failures.append(f"invalid_or_missing_score:{key}")
        if row.get("unsafe_output") or row.get("unauthorized_transition"):
            failures.append(f"unsafe_or_unauthorized_output:{key}")
        if not row.get("checkpoint_digest"):
            failures.append(f"checkpoint_digest_missing:{key}")
        lineage_key = key[:2] + (key[3],)
        digest = row.get("checkpoint_digest")
        previous_digest = checkpoint_ids.setdefault(lineage_key, digest)
        if previous_digest != digest:
            failures.append(f"checkpoint_changed_within_panel:{lineage_key}")
        if key[3] in {"invention_only", "full"} and key[1] > 0:
            if not row.get("approval_id") or not row.get("verified_receipt_id"):
                failures.append(f"approved_lineage_evidence_missing:{key}")
        if key[1] == 1:
            root_digest = ancestor_digests.get(f"{key[0]}:{key[3]}")
            if root_digest and row.get("parent_digest") != root_digest:
                failures.append(f"checkpoint_root_mismatch:{key}")
        for field in RESOURCE_FIELDS:
            if _resource_value(row, field) is None:
                failures.append(f"resource_missing_or_invalid:{key}:{field}")
            measurements = row.get("resource_measurements")
            evidence = measurements.get(field) if isinstance(measurements, dict) else None
            if (not isinstance(evidence, dict)
                    or evidence.get("status") not in {
                        "MEASURED", "MEASURED_NODE_PAYLOAD_BYTES"}
                    or not isinstance(evidence.get("source"), str)
                    or not evidence["source"].strip()):
                failures.append(f"resource_measurement_unverified:{key}:{field}")
        ceilings = plan.get("resource_ceilings", {})
        for field, ceiling in ceilings.items():
            value = _resource_value(row, field)
            if (value is None or isinstance(ceiling, bool)
                    or not isinstance(ceiling, (int, float))
                    or not math.isfinite(ceiling) or ceiling < 0 or value > ceiling):
                failures.append(f"resource_ceiling_violation:{key}:{field}")

    for key, row in indexed.items():
        if key[1] > 1:
            parent_key = (key[0], key[1] - 1, key[3])
            parent_digest = checkpoint_ids.get(parent_key)
            if parent_digest is not None and row.get("parent_digest") != parent_digest:
                failures.append(f"checkpoint_parent_mismatch:{key}")

    missing = expected - set(indexed)
    extra = set(indexed) - expected
    if missing:
        failures.append(f"missing_rows:{len(missing)}")
    if extra:
        failures.append(f"extra_rows:{len(extra)}")

    controls = payload.get("structural_controls")
    expected_controls = plan.get("control_ids")
    if (not isinstance(controls, list) or not isinstance(expected_controls, list)
            or len(controls) != len(expected_controls)
            or {row.get("control_id") for row in controls if isinstance(row, dict)}
                != set(expected_controls)
            or any(not isinstance(row, dict) or row.get("status") != "PASS"
                   or row.get("unsafe_output") or row.get("label_leak")
                   or row.get("comparator_disagreement") for row in controls)):
        failures.append("structural_control_failure")

    arm_rates = {}
    paired_rows = []
    efficiency = {}
    mcnemar = {}
    for family in families:
        for generation in GENERATIONS:
            for arm in ARMS:
                group = [indexed.get((family, generation, world_id, arm))
                         for world_id in world_ids.get(family, [])]
                complete = all(row is not None and row.get("status") == "scored"
                               and row.get("score") in (0, 1) for row in group)
                success_count = sum(row["score"] for row in group
                                    if row is not None and row.get("score") in (0, 1))
                arm_rates[f"{family}:{generation}:{arm}"] = {
                    "successes": success_count, "n": len(group),
                    "rate": success_count / len(group) if group else None,
                    "wilson_95": _wilson(success_count, len(group)) if complete else None,
                    "complete": complete}
            for world_id in world_ids.get(family, []):
                group = {arm: indexed.get((family, generation, world_id, arm))
                         for arm in ARMS}
                if any(row is None or row.get("status") != "scored"
                       or row.get("score") not in (0, 1) for row in group.values()):
                    continue
                for arm, row in group.items():
                    paired_rows.append({"family": family, "generation": generation,
                        "world_id": world_id, "arm": arm, "score": row["score"]})
                resource_match = all(
                    len({_resource_value(row, field) for row in group.values()}) == 1
                    for field in MATCHED_RESOURCE_FIELDS)
                efficiency[f"{family}:{generation}:{world_id}"] = resource_match
            full_only = ancestor_only = 0
            paired_count = 0
            for world_id in world_ids.get(family, []):
                full = indexed.get((family, generation, world_id, "full"))
                ancestor = indexed.get((family, generation, world_id, "unchanged"))
                if (full is None or ancestor is None or full.get("status") != "scored"
                        or ancestor.get("status") != "scored"
                        or full.get("score") not in (0, 1)
                        or ancestor.get("score") not in (0, 1)):
                    continue
                paired_count += 1
                full_only += int(full["score"] == 1 and ancestor["score"] == 0)
                ancestor_only += int(full["score"] == 0 and ancestor["score"] == 1)
            mcnemar[f"{family}:{generation}:full_vs_unchanged"] = {
                **_mcnemar_exact(full_only, ancestor_only),
                "paired_worlds": paired_count}

    primary = None
    if families and not failures and all(len(world_ids.get(family, [])) >= 200
                                         for family in families):
        primary = summarize_families(paired_rows, families=families,
            bootstrap_draws=10000, seed=payload.get("bootstrap_seed", 0))
        score_criteria_pass = all(result.get("registered_criteria", {}).get("passed")
                           for result in primary["families"].values())
    else:
        primary = {"status": "NOT_ESTABLISHED",
                   "reason": "structural_failure_or_incomplete_primary_panel"}
        score_criteria_pass = False
    expected_resource_worlds = sum(len(world_ids.get(family, []))
        * len(GENERATIONS) for family in families)
    resource_match_pass = (len(efficiency) == expected_resource_worlds
                           and expected_resource_worlds > 0
                           and all(efficiency.values()))
    primary["score_criteria_pass"] = score_criteria_pass
    primary["resource_match_pass"] = resource_match_pass
    primary["registered_phase_pass"] = score_criteria_pass and resource_match_pass
    if split == "development":
        status = "DEVELOPMENT_ONLY"
        evidence_class = "DEVELOPMENT_ONLY"
    elif failures:
        status = "NOT_ESTABLISHED"
        evidence_class = "HELDOUT_INVALID"
    elif not resource_match_pass:
        status = "NOT_ESTABLISHED"
        evidence_class = "CAPABILITY_ONLY"
    elif primary.get("status") == "NOT_ESTABLISHED":
        status = "NOT_ESTABLISHED"
        evidence_class = "HELDOUT"
    else:
        status = "PASS" if score_criteria_pass else "FAIL"
        evidence_class = "HELDOUT"
    resource_differences = {}
    for family in families:
        for generation in GENERATIONS:
            for field_index, field in enumerate(RESOURCE_FIELDS):
                differences = []
                for world_id in world_ids.get(family, []):
                    full = indexed.get((family, generation, world_id, "full"))
                    ancestor = indexed.get((family, generation, world_id, "unchanged"))
                    if full is None or ancestor is None:
                        continue
                    full_value = _resource_value(full, field)
                    ancestor_value = _resource_value(ancestor, field)
                    if full_value is None or ancestor_value is None:
                        continue
                    differences.append(float(full_value - ancestor_value))
                resource_differences[f"{family}:{generation}:{field}"] = {
                    "paired_worlds": len(differences),
                    "mean_full_minus_unchanged": (
                        sum(differences) / len(differences) if differences else None),
                    "paired_bootstrap_95": _bootstrap_mean_interval(differences,
                        seed=payload.get("bootstrap_seed", 0) + 1000 * GENERATIONS.index(generation)
                            + 10 * families.index(family) + field_index)}

    return {"phase": PHASE, "split": split, "status": status,
        "evidence_class": evidence_class, "failures": failures,
        "provenance_status": (
            "DEVELOPMENT_ONLY" if split == "development" else
            ("ATTESTED" if not any(failure == "runtime_not_attested"
                                   for failure in failures) else "NOT_ESTABLISHED")),
        "counts": {"rows": len(rows), "expected_rows": len(expected),
                   "missing_rows": len(missing), "structural_controls": len(controls or [])},
        "arm_rates": arm_rates, "mcnemar": mcnemar, "paired_effects": primary,
        "resource_differences": resource_differences,
        "efficiency_comparable_worlds": sum(efficiency.values()),
        "efficiency_total_worlds": len(efficiency),
        "resource_match_by_world": efficiency,
        "all_rows_retained": True}


def _self_check_payload() -> dict:
    families = ["d4", "loopover"]
    plan = {"families": families, "world_ids_by_family": {
            family: [f"{family}-w0", f"{family}-w1"] for family in families},
        "validation_world_ids_by_family": {
            family: [f"{family}-v0", f"{family}-v1"] for family in families},
        "selection_world_ids_by_family": {
            family: [f"{family}-s0", f"{family}-s1"] for family in families},
        "training_world_ids_by_family": {
            family: [f"{family}-t0", f"{family}-t1"] for family in families},
        "seeds_by_split_family": {
            split: {family: [1000 * split_index + 10 * family_index,
                             1000 * split_index + 10 * family_index + 1]
                    for family_index, family in enumerate(families)}
            for split_index, split in enumerate(("training", "selection",
                                                  "validation", "heldout"))},
        "generations": list(GENERATIONS), "arms": list(ARMS),
        "ancestor_checkpoint_digests": {
            f"{family}:{arm}": "ancestor" for family in families for arm in ARMS},
        "control_ids": ["null", "timeout", "unsafe", "disagreement"],
        "resource_ceilings": {field: 1_000_000.0 for field in RESOURCE_FIELDS}}
    rows = []
    for family in families:
        for generation in GENERATIONS:
            for world_id in plan["world_ids_by_family"][family]:
                for arm in ARMS:
                    rows.append({"family": family, "generation": generation,
                        "world_id": world_id, "arm": arm, "status": "scored",
                        "native_learner_status": "COMPLETED",
                        "native_task_status": "solved",
                        "primitive_budget_respected": True,
                        "rule_progress_limit_respected": True,
                        "approval_events_added": 0,
                        "world_receipts_added": 0,
                        "goal_digest": f"goal-{family}-{world_id}",
                        "world_digest": f"world-{family}-{world_id}",
                        "score": 0, "checkpoint_digest": f"{family}-{generation}-{arm}",
                        "parent_digest": (f"{family}-{generation - 1}-{arm}"
                                          if generation > 1 else "ancestor"),
                        "approval_id": f"approval-{generation}" if arm in {
                            "invention_only", "full"} and generation > 0 else None,
                        "verified_receipt_id": f"receipt-{generation}" if arm in {
                            "invention_only", "full"} and generation > 0 else None,
                        "resource_measurements": {field: {
                            "status": ("MEASURED_NODE_PAYLOAD_BYTES"
                                       if field == "training_data_bytes" else "MEASURED"),
                            "source": f"self_check_fixture:{field}"}
                            for field in RESOURCE_FIELDS},
                        **{field: 0.0 for field in RESOURCE_FIELDS}})
    controls = [{"control_id": control, "status": "PASS"}
                for control in plan["control_ids"]]
    return {"phase": PHASE, "split": "development", "status": "DEVELOPMENT_ONLY",
        "heldout_accessed": False, "allocation_plan": plan,
        "checkpoint_rows": rows, "structural_controls": controls,
        "bootstrap_seed": 13}


def self_check() -> dict:
    payload = _self_check_payload()
    clean = analyze(payload)
    assert clean["status"] == "DEVELOPMENT_ONLY"
    assert clean["provenance_status"] == "DEVELOPMENT_ONLY"
    assert clean["failures"] == []
    assert clean["paired_effects"]["status"] == "NOT_ESTABLISHED"
    assert clean["paired_effects"]["resource_match_pass"] is True
    assert clean["paired_effects"]["registered_phase_pass"] is False

    cases = {}
    null = json.loads(json.dumps(payload))
    null["checkpoint_rows"][0]["score"] = None
    cases["null"] = (null, "invalid_or_missing_score")
    timeout = json.loads(json.dumps(payload))
    timeout["checkpoint_rows"][0].update(status="timeout", score=None)
    cases["timeout"] = (timeout, "non_scored_outcome")
    unsafe = json.loads(json.dumps(payload))
    unsafe["checkpoint_rows"][0]["unsafe_output"] = True
    cases["unsafe"] = (unsafe, "unsafe_or_unauthorized_output")
    disagreement = json.loads(json.dumps(payload))
    disagreement["structural_controls"][0]["comparator_disagreement"] = True
    cases["comparator_disagreement"] = (disagreement,
                                         "structural_control_failure")
    for label, (case_payload, expected) in cases.items():
        result = analyze(case_payload)
        assert any(expected in failure for failure in result["failures"]), label
    no_resource_source = json.loads(json.dumps(payload))
    no_resource_source["checkpoint_rows"][0].pop("resource_measurements")
    assert any(failure.startswith("resource_measurement_unverified:")
               for failure in analyze(no_resource_source)["failures"])
    partial_resource = json.loads(json.dumps(payload))
    partial_resource["checkpoint_rows"][0]["resource_measurements"][
        "retrieval_work"]["status"] = "PARTIAL_EVENT_COUNT"
    assert any(failure.endswith(":retrieval_work")
               for failure in analyze(partial_resource)["failures"]
               if failure.startswith("resource_measurement_unverified:"))
    resource_mismatch = json.loads(json.dumps(payload))
    resource_mismatch["checkpoint_rows"][0]["native_rule_steps"] = 1.0
    mismatch_result = analyze(resource_mismatch)
    assert mismatch_result["paired_effects"]["resource_match_pass"] is False
    assert mismatch_result["paired_effects"]["registered_phase_pass"] is False
    overlap = json.loads(json.dumps(payload))
    overlap["allocation_plan"]["training_world_ids_by_family"]["d4"][0] = "d4-w0"
    assert "split_identity_overlap:d4" in analyze(overlap)["failures"]
    selection_overlap = json.loads(json.dumps(payload))
    selection_overlap["allocation_plan"]["selection_world_ids_by_family"][
        "loopover"][0] = "d4-w0"
    assert "allocation_identity_reused_across_families_or_splits" in analyze(
        selection_overlap)["failures"]
    return {"status": "PASS", "cases": ["null", "timeout", "unsafe",
                                          "comparator_disagreement",
                                          "resource_source_missing",
                                          "partial_resource_measurement",
                                          "resource_mismatch",
                                          "selection_split_integrity",
                                          "complete_flat_panel"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", type=Path)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preregistration", type=Path)
    args = parser.parse_args()
    if args.self_check:
        result = self_check()
    elif args.input:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        result = analyze(payload, preregistration=args.preregistration)
    else:
        parser.error("provide an input report or --self-check")
    rendered = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if result.get("status") in {"PASS", "DEVELOPMENT_ONLY", "FAIL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
