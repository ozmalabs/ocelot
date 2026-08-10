"""tests/test_arc4_endgame_migrated.py — Arc 4 S5: THE POWERED ENDGAME.

Companion docs: `PROGRAM_SYNTHESIS_ARC4_S5.md` (the full write-up),
`PROGRAM_SYNTHESIS_ARC4_PREREG.md` (**especially the §AMENDMENT** — A1
corrects HA2's ceiling to 40/76; A2 withdraws HA3; A3 registers the
honest-score clause; A4 fixes the reporting order), `scripts/
arc4_endgame_battery.py` (the driver this file gates — imported, never
re-implemented).

This gate does NOT re-run the full 257-task battery three times (that is
`scripts/arc4_endgame_battery.py`'s own ~110s job, already run to produce
`results/arc4_endgame.json`). It instead:

  1. Verifies the artifact's own internal derivation (rows are the
     baseline; every total/CI/hash is re-derivable from `runnable_rows`,
     never a hand-typed number).
  2. Hash-checks every FROZEN artifact this phase cites is byte-untouched
     (arc-2 endgame, arc-3 endgame, R0 ceiling, failure anatomy,
     structural verdicts).
  3. Live re-verifies exactly 3 tasks per arm (9 single-task synthesis
     calls total, not 3*257) — enough to prove the seed-swap mechanism
     genuinely drives the real pipeline, not a canned number.
  4. Re-runs the standing contamination suite and asserts it is reported.
  5. Asserts the A3 three-way honest-score accounting exists and that
     every genuine-defect-rejection id carries a witness input.
  6. A no-python-decision source audit on the battery's own classifier
     functions (they must only READ recorded facts, never call the
     Python rule engine).

Run:
  PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 \
    OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=. \
    tests/test_arc4_endgame_migrated.py -q
"""
from __future__ import annotations

import hashlib
import inspect
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import arc4_endgame_battery as aeb  # noqa: E402  (the driver, read-only)
from domains import mbpp_spec as ms  # noqa: E402

ARTIFACT_PATH = os.path.join(ROOT, "results", "arc4_endgame.json")

# --------------------------------------------------------------------------- #
#  Frozen artifact hashes — measured once (sha256sum), pinned here. A
#  mismatch means the cited artifact drifted after this phase measured it.
# --------------------------------------------------------------------------- #
_FROZEN_HASHES = {
    "mbpp_endgame_arc2": (
        "results/mbpp_endgame.json",
        "2632c7496ea5f78f73a13019c8dc41a77b65c8701e5c75a0e22cfa2bc6cea10a"),
    "mbpp_arc3_endgame": (
        "results/mbpp_arc3_endgame.json",
        "94e4392f6d986e7d275f66247d1ed576c2f75b66585e8717a7b64d9f67370dc5"),
    "retrieval_oracle_ceiling_r0": (
        "results/retrieval_oracle_ceiling.json",
        "cd47e08d35390a6a56a1dc6ea68f415cd9b47c13296fc7f89fa2b9a25438f487"),
    "arc4_failure_anatomy": (
        "results/arc4_failure_anatomy.json",
        "eac9f75a419704b2e6370d4c0ffa8d35441a3d08dc8a67cdffc2767cbf549811"),
    "arc4_structural_verdicts": (
        "results/arc4_structural_verdicts.json",
        "d8aa355900151aa0073b1c9ff2eb6d855f6bd5bac82dccbc7efdb7f64623896c"),
}


def _sha256_file(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


@pytest.fixture(scope="module")
def artifact():
    with open(ARTIFACT_PATH) as f:
        return json.load(f)


# --------------------------------------------------------------------------- #
#  1. Frozen-artifact continuity.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("key", sorted(_FROZEN_HASHES))
def test_frozen_artifact_is_byte_unchanged(key):
    relpath, expected_sha = _FROZEN_HASHES[key]
    full = os.path.join(ROOT, relpath)
    assert os.path.exists(full), "missing frozen artifact: %s" % relpath
    got = _sha256_file(full)
    assert got == expected_sha, (
        "%s drifted since this phase measured it (expected %s, got %s) — "
        "a historical record must never be edited" % (relpath, expected_sha, got))


def test_artifact_records_the_same_hashes_it_measured(artifact):
    recorded = artifact["frozen_artifact_hashes"]
    for key, (relpath, expected_sha) in _FROZEN_HASHES.items():
        assert recorded[key]["sha256"] == expected_sha
        assert recorded[key]["path"] == relpath


# --------------------------------------------------------------------------- #
#  2. Schema / derivation — every total, CI, and hash must be re-derivable
#     from `runnable_rows`, never a hand-typed sibling number.
# --------------------------------------------------------------------------- #
ARM_NAMES = ("full_a4", "no_isolation", "no_structural")


@pytest.mark.parametrize("arm", ARM_NAMES)
def test_arm_present_with_expected_top_level_shape(artifact, arm):
    a = artifact["arms"][arm]
    assert a["arm"] == arm
    assert a["protocol"] == "primary"
    for key in ("runnable_rows", "excluded_rows", "determinism",
               "outcome_taxonomy", "aggregates"):
        assert key in a


@pytest.mark.parametrize("arm", ARM_NAMES)
def test_determinism_hashes_present_and_runs_identical(artifact, arm):
    det = artifact["arms"][arm]["determinism"]
    assert det["runs"] == 2
    assert det["identical"] is True
    assert det["outcome_hash_run1"] == det["outcome_hash_run2"]
    assert len(det["outcome_hash_run1"]) == 64  # sha256 hex


@pytest.mark.parametrize("arm", ARM_NAMES)
def test_pass_count_derives_from_rows_not_hand_typed(artifact, arm):
    a = artifact["arms"][arm]
    n_pass_rows = sum(1 for r in a["runnable_rows"] if r["outcome"] == "pass")
    assert n_pass_rows == a["aggregates"]["pass_over_runnable"]["k"]
    assert len(a["runnable_rows"]) == a["aggregates"]["pass_over_runnable"]["n"]
    # the taxonomy partitions runnable+excluded exactly
    tax_total = sum(v["n"] for v in a["outcome_taxonomy"].values())
    assert tax_total == len(a["runnable_rows"]) + len(a["excluded_rows"])


@pytest.mark.parametrize("arm", ARM_NAMES)
def test_wilson_ci_recomputes_byte_identical(artifact, arm):
    agg = artifact["arms"][arm]["aggregates"]["pass_over_runnable"]
    recomputed = aeb.arc3b.wilson(agg["k"], agg["n"])
    assert recomputed == agg


def test_arc_number_matches_full_a4_arm(artifact):
    assert artifact["arc_number"]["pass_over_runnable"] == \
        artifact["arms"]["full_a4"]["aggregates"]["pass_over_runnable"]
    traj = artifact["arc_number"]["trajectory_pct"]
    assert traj["q0a_stress_zero_shot"] == 0.42
    assert traj["arc2_q5_full_primary"] == 7.00
    assert traj["arc3_r3_full_r3_primary"] == 8.17
    n_pass = artifact["arms"]["full_a4"]["aggregates"]["pass_over_runnable"]["k"]
    n_run = artifact["arms"]["full_a4"]["aggregates"]["pass_over_runnable"]["n"]
    assert traj["arc4_s5_full_a4_primary"] == round(100.0 * n_pass / n_run, 2)


def test_ha3_does_not_appear_anywhere_in_the_verdict_set(artifact):
    """Prereg SAMENDMENT A2: HA3 is withdrawn as a hypothesis (an S0
    measured null) and MUST NOT appear in the S5 verdict set as a VERDICT
    KEY (a prose mention explaining that it is absent, e.g. in _README, is
    fine and expected — this checks structure, not text)."""
    top_and_nested_keys = []

    def _walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                top_and_nested_keys.append(k)
                _walk(v)
        elif isinstance(x, list):
            for v in x:
                _walk(v)

    _walk(artifact)
    assert not any(k.lower().startswith("ha3") for k in top_and_nested_keys)


# --------------------------------------------------------------------------- #
#  3. Rule-name disjointness — the seed-swap mechanism this whole phase
#     rests on. Verified against the LIVE current manifest + the two cited
#     historical git blobs, not merely asserted from prose.
# --------------------------------------------------------------------------- #
def test_s1_and_s2_touched_rule_name_sets_are_disjoint():
    assert aeb._S1_REPLACE_NAMES.isdisjoint(aeb._S2_REPLACE_NAMES)
    assert aeb._S1_REPLACE_NAMES.isdisjoint(aeb._S2_REMOVE_NAMES)
    assert aeb._S1_REMOVE_NAMES.isdisjoint(aeb._S2_REPLACE_NAMES)
    assert aeb._S1_REMOVE_NAMES.isdisjoint(aeb._S2_REMOVE_NAMES)


def test_ablation_manifests_only_differ_in_the_declared_rule_names():
    current = aeb._CURRENT_MANIFEST
    no_iso = aeb._NO_ISOLATION_MANIFEST
    no_struct = aeb._NO_STRUCTURAL_MANIFEST

    def names(m):
        return {r["name"] for r in m["rules"]}

    cur_names, iso_names, struct_names = names(current), names(no_iso), names(no_struct)
    # no_isolation: removed exactly ps_isolate_fallthrough, replaced (same
    # names) the 9 S1 rules — never touches any other name.
    assert cur_names - iso_names == aeb._S1_REMOVE_NAMES
    assert iso_names - cur_names == set()
    for name in aeb._S1_REPLACE_NAMES:
        assert next(r for r in no_iso["rules"] if r["name"] == name) != \
            next(r for r in current["rules"] if r["name"] == name)
    untouched = cur_names - aeb._S1_REPLACE_NAMES - aeb._S1_REMOVE_NAMES
    cur_by_name = {r["name"]: r for r in current["rules"]}
    iso_by_name = {r["name"]: r for r in no_iso["rules"]}
    for name in untouched:
        assert cur_by_name[name] == iso_by_name[name]

    # no_structural: removed exactly the 2 S2 rules, replaced ps_accept —
    # never touches any other name.
    assert cur_names - struct_names == aeb._S2_REMOVE_NAMES
    assert struct_names - cur_names == set()
    struct_by_name = {r["name"]: r for r in no_struct["rules"]}
    assert struct_by_name["ps_accept"] != cur_by_name["ps_accept"]
    untouched2 = cur_names - aeb._S2_REPLACE_NAMES - aeb._S2_REMOVE_NAMES
    for name in untouched2:
        assert cur_by_name[name] == struct_by_name[name]


def test_no_reach_arm_is_explicitly_omitted_with_reasoning(artifact):
    switches = artifact["condition"]["seed_switches"]
    assert switches["no_reach"]["status"] == "OMITTED"
    assert "reason" in switches["no_reach"] and len(switches["no_reach"]["reason"]) > 100
    ha4 = artifact["ha4_search_reach"]
    assert "OMITTED" in ha4["no_reach_arm"]
    assert ha4["s4_own_measured_85_bucket"]["n_bucket"] == 85
    assert ha4["s4_own_measured_85_bucket"]["n_moved_off_enumerate_failed"] == 25


# --------------------------------------------------------------------------- #
#  4. 3-task live re-verify per arm (9 single-task runs, not 3*257).
# --------------------------------------------------------------------------- #
FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")


@pytest.fixture(scope="module")
def test_split_by_id():
    with open(FIXTURE_PATH) as f:
        all_tasks = json.load(f)
    splits = aeb.arc3b.q0_split_tasks(all_tasks)
    return {t["task_id"]: t for t in splits["test"]}


def _live_outcome(task_id, boot_fn, test_split_by_id):
    task = test_split_by_id[task_id]
    parsed = ms.parse_asserts(task)
    spec = ms.split_rows(parsed["rows"], "primary")
    assert spec["runnable"], "task %s excluded under PRIMARY protocol" % task_id
    row = aeb.arc3b.run_task(task, spec, {}, boot_fn, "primary")
    return row["outcome"], row.get("gap_reason")


# (task_id, boot_fn_name, expected_outcome) — 3 ids per arm, chosen to
# 2026-08-01 (arc4 S6): a structural rejection no longer TERMINATES —
# for non-retrieval candidates it now excludes the defective candidate
# and re-proposes. Task 397 (a genuine defect) therefore lands on
# `gapped:enumerate_failed` (rejected, re-proposed, nothing found)
# rather than `gapped:structural_verdict_reject`. The load-bearing
# property is unchanged and still asserted: 397 NEVER accepts.
# exercise the DISJOINTNESS of the two ablations directly (task 397 is
# rejected under full_a4/no_isolation — S2 present in both — but reverts
# to `pass` under no_structural; task 108 is `gapped:enumerate_failed`
# under full_a4/no_structural — S1 present in both — but reverts to
# `gapped:exhausted` under no_isolation).
LIVE_REVERIFY_CASES = [
    ("full_a4", 397, "gapped:enumerate_failed"),
    ("full_a4", 108, "gapped:enumerate_failed"),
    ("full_a4", 296, "accepted_holdout_fail"),
    ("no_isolation", 108, "gapped:exhausted"),
    ("no_isolation", 397, "gapped:enumerate_failed"),
    ("no_isolation", 296, "accepted_holdout_fail"),
    ("no_structural", 397, "pass"),
    ("no_structural", 108, "gapped:enumerate_failed"),
    ("no_structural", 222, "gapped:exhausted"),
]
_BOOT_FN = {"full_a4": aeb.boot_full_a4, "no_isolation": aeb.boot_no_isolation,
           "no_structural": aeb.boot_no_structural}


@pytest.mark.parametrize("arm,task_id,expected", LIVE_REVERIFY_CASES)
def test_three_task_live_reverify_per_arm(arm, task_id, expected, test_split_by_id):
    outcome, gap_reason = _live_outcome(task_id, _BOOT_FN[arm], test_split_by_id)
    assert outcome == expected, (
        "arm=%s task=%s: expected %s, live got %s (gap_reason=%s)"
        % (arm, task_id, expected, outcome, gap_reason))


_S6_TERMINAL_LABEL_DRIFT = {("full_a4", 397), ("no_isolation", 397)}


@pytest.mark.parametrize("arm", ARM_NAMES)
def test_live_reverify_matches_the_frozen_artifact_row(artifact, arm, test_split_by_id):
    """The 3 ids for this arm above must ALSO match what's actually
    recorded in results/arc4_endgame.json's own runnable_rows — the live
    re-verify and the shipped artifact must agree."""
    rows_by_id = {r["task_id"]: r for r in artifact["arms"][arm]["runnable_rows"]}
    ids_this_arm = sorted({tid for a, tid, _ in LIVE_REVERIFY_CASES if a == arm})
    for tid in ids_this_arm:
        expected = next(
            exp for a, t, exp in LIVE_REVERIFY_CASES if a == arm and t == tid)
        frozen = rows_by_id[tid]["outcome"]
        if (arm, tid) in _S6_TERMINAL_LABEL_DRIFT:
            # 2026-08-01 (arc4 S6): the frozen artifact was measured at S5,
            # BEFORE rejections learned to reopen. Task 397's TERMINAL LABEL
            # moved (structural_verdict_reject -> enumerate_failed) while its
            # OUTCOME did not: it is rejected either way and never accepts.
            # The frozen artifact stays authoritative for its own run; the
            # live expectation carries the post-S6 label. Both are non-accept,
            # which is the property the A3 accounting actually rests on.
            assert frozen.startswith("gapped"), (arm, tid, frozen)
            assert expected.startswith("gapped"), (arm, tid, expected)
            continue
        assert frozen == expected


# --------------------------------------------------------------------------- #
#  5. Contamination suite — run and reported.
# --------------------------------------------------------------------------- #
def test_contamination_suite_is_run_and_reported(artifact):
    rep = artifact["condition"]["contamination_suite"]
    assert rep["passed"] is True
    assert rep["returncode"] == 0
    assert "passed" in rep["tail"]


def test_contamination_suite_reproduces_green_live():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--confcutdir=.",
         "tests/test_mbpp_contamination_migrated.py", "-q"],
        cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr


def test_no_code_field_leaks_into_the_test_split(test_split_by_id):
    for task in test_split_by_id.values():
        assert "code" not in task


# --------------------------------------------------------------------------- #
#  6. A3 three-way honest-score accounting — the load-bearing gate.
# --------------------------------------------------------------------------- #
def test_a3_accounting_fields_exist(artifact):
    a3 = artifact["ha2_verdict_discrimination"]["a3_honest_score_accounting"]
    for key in ("1_pass_rate_before_after",
               "2_genuine_defect_rejection_ids_with_witnesses",
               "genuine_defect_rejection_ids",
               "3_true_regression_ids_within_mbpp_257",
               "3b_true_regression_outside_mbpp_257_fixture_battery"):
        assert key in a3


def test_a3_genuine_defect_ids_carry_witness_inputs(artifact):
    a3 = artifact["ha2_verdict_discrimination"]["a3_honest_score_accounting"]
    witnessed = a3["2_genuine_defect_rejection_ids_with_witnesses"]
    assert set(a3["genuine_defect_rejection_ids"]) == {397, 404}
    for tid_str, w in witnessed.items():
        assert "witness_inputs" in w and isinstance(w["witness_inputs"], dict)
        assert "witness_expected_correct" in w
        assert "why_defective" in w and len(w["why_defective"]) > 10
        if int(tid_str) in a3["genuine_defect_rejection_ids"]:
            lv = w["live_witness_reverification"]
            assert lv is not None
            assert lv["matches_correct_answer"] is False, (
                "the witness must independently show the accepted "
                "program is WRONG — never a held-out row")


def test_a3_true_regressions_within_257_is_empty(artifact):
    """Both pass->reject transitions in the 257-task population (397,
    404) are witness-verified genuine defects, not true regressions —
    ZERO true regressions within the MBPP population, per S2's own
    landing measurement (PROGRAM_SYNTHESIS_ARC4_S2_NOTES.md §5)."""
    a3 = artifact["ha2_verdict_discrimination"]["a3_honest_score_accounting"]
    assert a3["3_true_regression_ids_within_mbpp_257"] == []


def test_a3_br10_true_regression_is_verified_and_reported(artifact):
    """The ONE named true regression, outside the 257-task population
    (the repair_oracle fixture battery) — must not be silently absent."""
    a3 = artifact["ha2_verdict_discrimination"]["a3_honest_score_accounting"]
    br10 = a3["3b_true_regression_outside_mbpp_257_fixture_battery"]
    assert br10["task_id"] == "br_10_top_of_three"
    assert br10["is_true_regression"] is True
    assert br10["live_gap_reason"] == "structural_verdict_reject"


def test_a3_br10_reproduces_live():
    """2026-08-01 (arc5 moves, reconciled): the FROZEN artifact
    (`test_a3_br10_true_regression_is_verified_and_reported` above, byte-
    unchanged) stays authoritative for the moment it measured — br_10 WAS
    a true regression there. The LIVE reproduction this test performs no
    longer matches it: arc5-moves' MOVE A (orbit augmentation,
    PROGRAM_SYNTHESIS_ARC5_MOVES.md) now finds the correct
    `Max(a, Max(b, c))` directly from the 3 revealed rows via symmetry,
    before enumerate ever proposes (or S6's reject/reopen ever needs to
    exclude) the `Max(a,b)` decoy this regression was about. `_check_br_
    10_true_regression`'s OWN `is_true_regression` computation (`scripts/
    arc4_endgame_battery.py`, outside this reconciliation's file-ownership
    boundary — untouched) already reflects this correctly: it requires
    `status == 'gapped'`, which is no longer true, so it now honestly
    reports `False`. This test is updated to check THAT — a real,
    verified, no-longer-a-regression — not weakened, and cross-checked
    against a witness beyond the fixture's own held-out rows (see
    tests/test_reject_informs_repair_migrated.py::
    test_br_10_root_caused_non_convergence for the SAME live convergence,
    verified independently there too)."""
    fresh = aeb._check_br_10_true_regression()
    assert fresh["is_true_regression"] is False, fresh
    assert fresh["live_status"] == "accepted", fresh
    assert fresh["live_outcome"] == "accepted_holdout_ok", fresh
    assert fresh["live_gap_reason"] is None
    assert fresh["live_oracle"]["rounds"] == 0, (
        "converged on the FIRST attempt -- the oracle-feedback lane was "
        "never reached, exactly like the pre-regression Q4 measurement")


def test_a3_rule_is_stated_verbatim(artifact):
    a3 = artifact["ha2_verdict_discrimination"]["a3_honest_score_accounting"]
    assert "NOT a regression" in a3["rule"]
    assert "PASS for this arc" in a3["rule"]


# --------------------------------------------------------------------------- #
#  7. HA1/HA2/HA4/HA5 self-consistency.
# --------------------------------------------------------------------------- #
def test_ha1_self_consistent(artifact):
    ha1 = artifact["ha1_budget_isolation"]
    assert ha1["n_arc3_full_r3_gapped_exhausted"] == 17
    assert len(ha1["escaped_under_full_a4_ids"]) == ha1["n_escaped"]
    assert set(ha1["escaped_under_full_a4_ids"]) | \
        set(ha1["still_gapped_exhausted_under_full_a4_ids"]) == \
        set(ha1["arc3_full_r3_gapped_exhausted_ids"])
    assert ha1["n_escaped"] == 16
    assert ha1["still_gapped_exhausted_under_full_a4_ids"] == [222]
    assert ha1["verdict"] == "STRONG_WITH_NAMED_EXCEPTIONS"
    for tid, facts in ha1["remaining_gapped_exhausted_classified"].items():
        assert facts["is_propose_lane_starvation"] is False, (
            "task %s remains gapped:exhausted for a DIFFERENT, "
            "independently-verified reason, never budget starvation" % tid)


def test_ha2_self_consistent(artifact):
    ha2 = artifact["ha2_verdict_discrimination"]
    assert ha2["n_converted"] == len(ha2["converted_pre_accept_reject_ids"])
    assert ha2["n_full_a4_accepted_holdout_fail"] == \
        ha2["n_no_structural_accepted_holdout_fail"] - ha2["n_converted"]
    assert ha2["verdict_band"] == "STRONG"
    assert ha2["n_converted"] >= 20  # half the CORRECTED 40-ceiling


def test_ha4_self_consistent(artifact):
    ha4 = artifact["ha4_search_reach"]
    diff = ha4["full_a4_vs_arc3_full_r3_gapped_enumerate_failed"]
    assert set(diff["escaped_ids"]) | set(diff["still_gapped_enumerate_failed_ids"]) == \
        set(diff["arc3_full_r3_ids"])
    assert diff["n_full_a4"] == diff["n_still"] + diff["n_newly"]


def test_ha5_self_consistent(artifact):
    ha5 = artifact["ha5_cost_instrument"]
    assert ha5["verdict_band"] in ("STRONG", "WEAK_MARGINAL", "NULL")
    if ha5["verdict_band"] == "NULL":
        assert "TRIGGERED" in ha5["fourth_null_rule_status"]


def test_self_detected_wrongness_headline_derives_from_ha2(artifact):
    headline = artifact["self_detected_wrongness_headline"]
    ha2 = artifact["ha2_verdict_discrimination"]
    assert headline["n_now_self_detected_pre_accept"] == ha2["n_converted"]
    assert headline["n_would_have_been_wrong_accepts"] == \
        ha2["n_no_structural_accepted_holdout_fail"]


def test_migration_matrix_arithmetic(artifact):
    mm = artifact["migration_matrix_vs_arc3_full_r3"]
    a4 = artifact["arms"]["full_a4"]["aggregates"]["pass_over_runnable"]["k"]
    net = mm["n_regressions"]
    gains = len(mm["gains_over_arc3_full_r3"])
    losses = mm["n_regressions"]
    assert a4 - 21 == gains - losses  # arc-3 full_r3 pass was 21/257


# --------------------------------------------------------------------------- #
#  8. No-python-decision source audit.
# --------------------------------------------------------------------------- #
FORBIDDEN_TOKENS = ("gr._match", "gr._apply", "graph_rewrite.run")


@pytest.mark.parametrize("fn", [
    aeb.ha1_block, aeb.ha2_block, aeb.ha4_block, aeb.ha5_block,
    aeb.migration_matrix_vs_arc3, aeb.self_detected_wrongness_headline,
    aeb._build_seed_variant, aeb._patched_manifest_for,
])
def test_no_forbidden_decision_tokens(fn):
    src = inspect.getsource(fn)
    for token in FORBIDDEN_TOKENS:
        assert token not in src
