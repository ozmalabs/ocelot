"""tests/test_arc4_anatomy_migrated.py — Arc 4 S0 track A gate.

Companion to `scripts/arc4_failure_anatomy.py` (the measurement driver)
and `results/arc4_failure_anatomy.json` (the artifact this gate re-derives
every aggregate from). See `PROGRAM_SYNTHESIS_ARC4_PLAN.md` §2 (S0) for
what this phase measures: (1) the `gapped:exhausted` residual-by-class
target list for HA1, (2) the `accepted_holdout_fail` trap anatomy for
HA2's killable mass.

Gates:
  1. Artifact schema — top-level keys, both measurement blocks present.
  2. Measurement 1 — class ids sum to the 17-row total; class (a)/(b) ids
     match PROGRAM_SYNTHESIS_ARC3_R3.md's own already-published sets
     EXACTLY (the residual 7 / covered-unchanged 10); classes (c)/(d)/(e)
     are empty, as the state-machine's own ps_exhausted/ps_enumerate_failed
     mutual exclusion predicts.
  3. R3 continuity — the frozen `results/mbpp_arc3_endgame.json` artifact
     is BYTE-UNTOUCHED by this phase (hash re-verified live) and this
     phase's own live re-run of FULL-R3 reproduces its cited outcome hash.
  4. HELD-OUT ISOLATION GATE — no trap-anatomy probe function's source
     contains the literal substring "held_out" (mechanical source-text
     audit, re-run live here independent of the artifact's own recorded
     copy of the same audit).
  5. Measurement 2 — the per-task classification independently re-derives
     the same class partition + totals the artifact reports; determinism
     of the cheap (python/type/invariance) in-process signals holds.
  6. 3 pinned per-task classifications RE-VERIFIED LIVE (a fresh boot,
     the same code path the script uses): one measurement-1 class-(a) id,
     one measurement-1 class-(b) id, one measurement-2 cross-frame id.
  7. Toolchain subsample rule — deterministic stride, no silent cap.
  8. No-python-decision source audit (never reads task["code"]).
  9. Shared contamination gate passes.

Runtime: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=. tests/test_arc4_anatomy_migrated.py
"""
from __future__ import annotations

import ast
import hashlib
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

import arc4_failure_anatomy as aa  # noqa: E402
import mbpp_arc3_battery as bat  # noqa: E402

ARTIFACT_PATH = os.path.join(ROOT, "results", "arc4_failure_anatomy.json")
FROZEN_R3_PATH = os.path.join(ROOT, "results", "mbpp_arc3_endgame.json")
FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")

# PROGRAM_SYNTHESIS_ARC3_R3.md §4 — already-published, human-verified sets.
_R3_RESIDUAL_STARTER_SHAPE_IDS = [286, 296, 415, 463, 468, 471, 476]
_R3_COVERED_UNCHANGED_IDS = [108, 119, 222, 223, 229, 240, 245, 280, 394, 431]


@pytest.fixture(scope="module")
def artifact():
    with open(ARTIFACT_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def fixture_tasks():
    with open(FIXTURE_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def live_arm_full(fixture_tasks):
    """ONE live re-run of FULL-R3 (twin-run internally), shared across the
    live-reverify tests in this module — the same `bat.run_arm` path
    `scripts/arc4_failure_anatomy.py` itself calls."""
    splits = bat.q0_split_tasks(fixture_tasks)
    test_tasks = splits["test"]
    for t in test_tasks:
        assert "code" not in t
    return bat.run_arm("full_r3", test_tasks), {t["task_id"]: t for t in test_tasks}


# --------------------------------------------------------------------------- #
#  1. artifact schema.
# --------------------------------------------------------------------------- #
def test_artifact_top_level_schema(artifact):
    for key in ("_README", "head", "measured_at", "provenance", "frozen_r3_continuity",
               "held_out_isolation_audit", "condition",
               "measurement1_gapped_exhausted_anatomy",
               "measurement2_trap_anatomy", "environment", "elapsed_seconds"):
        assert key in artifact, "missing top-level key: %s" % key


# --------------------------------------------------------------------------- #
#  2. measurement 1 — class ids.
# --------------------------------------------------------------------------- #
def test_measurement1_classes_sum_to_total(artifact):
    m1 = artifact["measurement1_gapped_exhausted_anatomy"]
    classes = m1["classes"]
    total = sum(c["n"] for c in classes.values())
    assert total == m1["n_gapped_exhausted"]
    all_ids = sorted(tid for c in classes.values() for tid in c["task_ids"])
    assert all_ids == sorted(m1["task_ids"])
    # every id appears in EXACTLY one class (a true partition).
    assert len(all_ids) == len(set(all_ids))


def test_measurement1_class_a_matches_r3_residual(artifact):
    m1 = artifact["measurement1_gapped_exhausted_anatomy"]
    assert (m1["classes"]["a_descend_applicable"]["task_ids"]
           == sorted(_R3_RESIDUAL_STARTER_SHAPE_IDS))


def test_measurement1_class_b_matches_r3_covered_unchanged(artifact):
    m1 = artifact["measurement1_gapped_exhausted_anatomy"]
    assert (m1["classes"]["b_cued_screen_disengaged"]["task_ids"]
           == sorted(_R3_COVERED_UNCHANGED_IDS))


def test_measurement1_classes_c_d_e_are_empty(artifact):
    m1 = artifact["measurement1_gapped_exhausted_anatomy"]
    for cls in ("c_retrieval_consumed", "d_genuine_enumerator_exhaustion",
               "e_other_enumerate_ran_but_exhausted", "e_other_unclassified"):
        assert m1["classes"][cls]["n"] == 0, (
            "class %s unexpectedly non-empty: %r"
            % (cls, m1["classes"][cls]["task_ids"]))
    assert m1["n_anomaly_classes_e"] == 0


def test_measurement1_n_gapped_exhausted_is_17(artifact):
    # Pinned to Arc-3 R3's own measured number (PROGRAM_SYNTHESIS_ARC3_R3.md
    # §6): a drift here means the underlying FULL-R3 stack changed, which
    # this phase's own scope forbids (no synthesis/engine/seed/spec code
    # touched).
    m1 = artifact["measurement1_gapped_exhausted_anatomy"]
    assert m1["n_gapped_exhausted"] == 17


def test_measurement1_class_definitions_cover_every_class(artifact):
    m1 = artifact["measurement1_gapped_exhausted_anatomy"]
    assert set(m1["class_definitions"]) == set(m1["classes"])


def test_measurement1_ha1_honest_ceiling_present(artifact):
    ceiling = artifact["measurement1_gapped_exhausted_anatomy"]["ha1_honest_ceiling"]
    assert ceiling["n_of_17"] == 17
    assert ceiling["n_addressable_by_s1_as_scoped"] == 17


# --------------------------------------------------------------------------- #
#  3. R3 continuity — frozen artifact byte-untouched + live hash match.
# --------------------------------------------------------------------------- #
def test_frozen_r3_artifact_hash_unchanged(artifact):
    with open(FROZEN_R3_PATH, "rb") as f:
        live_sha = hashlib.sha256(f.read()).hexdigest()
    assert live_sha == artifact["frozen_r3_continuity"]["sha256"], (
        "results/mbpp_arc3_endgame.json changed since this phase ran — "
        "it must stay frozen (this phase only READS it)")


def test_r3_live_rerun_hash_matches_frozen_citation(artifact):
    rc = artifact["frozen_r3_continuity"]["r3_consistency"]
    assert rc["identical"] is True
    assert rc["frozen_outcome_hash"] == rc["live_outcome_hash"]


def test_r3_consistency_reverifies_live(live_arm_full, artifact):
    """S0-A's live arm reproduced the frozen arc-3 hash EXACTLY when it ran.

    RETIRED AS A HASH-EQUALITY ASSERTION, 2026-08-01 (arc4 S1 + S4), and the
    reason is the phases working: S1 (budget isolation) and S4 (enumerator
    list ops) both deliberately changed live outcomes on this population —
    S1 freed 16/17 starved goals, S4 moved 25/85 off enumerate-failure. A
    live hash identical to the arc-3 frozen hash would now mean arc 4 did
    NOTHING. What the test can still honestly prove is INTERNAL determinism
    (the twin-run agreement), which is the property it shares with every
    other artifact gate here. The frozen arc-3 artifact stays authoritative
    for its own run and is asserted unchanged below."""
    arm_full, _ = live_arm_full
    with open(FROZEN_R3_PATH) as f:
        frozen_r3 = json.load(f)
    # The frozen artifact is untouched and still records the pre-arc-4 world.
    frozen_hash = frozen_r3["arms"]["full_r3"]["determinism"]["outcome_hash_run1"]
    assert isinstance(frozen_hash, str) and len(frozen_hash) >= 16
    assert frozen_r3["arms"]["full_r3"]["determinism"]["identical"] is True
    # The live arm must still be internally deterministic (twin-run identical).
    assert arm_full["determinism"]["identical"] is True


# --------------------------------------------------------------------------- #
#  4. HELD-OUT ISOLATION GATE.
# --------------------------------------------------------------------------- #
def test_probe_functions_never_reference_held_out_rows():
    """The load-bearing isolation gate: every trap-anatomy probe function
    takes ONLY revealed_rows. Mechanical source-text audit, run LIVE here
    (independent of the artifact's own recorded copy of the same audit —
    tested separately below)."""
    audit = aa._held_out_isolation_audit()
    assert audit["any_hit"] is False, "held-out isolation violated: %r" % audit["hits"]
    # every probe function this phase defines must actually be checked —
    # a shrinking list here would silently narrow the gate's own scope.
    expected = {"_revealed_rows_for_task", "type_arity_check", "invariance_probe",
               "check_det_repeat", "check_unordered_permutation",
               "check_swap_arity2", "check_tol_perturbation",
               "check_count_len_increment", "python_cross_check",
               "toolchain_cross_check", "_llvm_chain"}
    assert expected.issubset(set(audit["functions_checked"]))


def test_artifacts_own_recorded_isolation_audit_is_clean(artifact):
    assert artifact["held_out_isolation_audit"]["any_hit"] is False


def test_split_rows_revealed_helper_never_touches_held_out(fixture_tasks):
    """A second, independent proof at the CALL-SITE grain: for a real
    task, `_revealed_rows_for_task` returns exactly `split_rows(...)
    ["revealed"]` and the caller never had `held_out` in scope to leak."""
    tasks_by_id = {t["task_id"]: dict(t) for t in fixture_tasks}
    for t in tasks_by_id.values():
        t.pop("code", None)
    # task 14 is a known accepted_holdout_fail PRIMARY-runnable task.
    from domains import mbpp_spec as ms
    task = tasks_by_id[14]
    parsed = ms.parse_asserts(task)
    spec = ms.split_rows(parsed["rows"], "primary")
    got = aa._revealed_rows_for_task(14, tasks_by_id)
    assert got == spec["revealed"]
    assert got != spec["held_out"]


# --------------------------------------------------------------------------- #
#  5. measurement 2 — class partition + determinism.
# --------------------------------------------------------------------------- #
def test_measurement2_classes_partition_matches_per_task(artifact):
    m2 = artifact["measurement2_trap_anatomy"]
    per_task = m2["per_task"]
    killable = [int(tid) for tid, row in per_task.items()
               if row["killable_by_any_owned_signal"]]
    nothing = [int(tid) for tid, row in per_task.items()
              if not row["killable_by_any_owned_signal"]]
    assert set(killable) | set(nothing) == {int(k) for k in per_task}
    assert set(killable) & set(nothing) == set()
    assert sorted(nothing) == m2["classes"]["d_nothing_available"]["task_ids"]
    assert len(nothing) == m2["classes"]["d_nothing_available"]["n"]


def test_measurement2_ahf_count_matches_per_task(artifact):
    m2 = artifact["measurement2_trap_anatomy"]
    assert m2["n_ahf"] == len(m2["per_task"])
    assert sorted(int(k) for k in m2["per_task"]) == m2["ahf_task_ids"]


def test_measurement2_class_union_and_residual_sum_to_ahf(artifact):
    m2 = artifact["measurement2_trap_anatomy"]
    c = m2["classes"]
    union = (set(c["a_cross_frame_disagreement"]["python_ids"])
            | set(c["a_cross_frame_disagreement"]["toolchain_ids_subsample_only"])
            | set(c["b_type_arity_violation"]["task_ids"])
            | set(c["c_invariance_violation"]["task_ids"]))
    nothing = set(c["d_nothing_available"]["task_ids"])
    assert union & nothing == set()
    assert len(union) + len(nothing) == m2["n_ahf"]


def test_measurement2_type_arity_violations_are_bool_numeric_laxness(artifact):
    """Sanity-check the (b) signal's own honesty claim: every violation
    this run found is a bool-vs-numeric strict-type mismatch (the class
    the pipeline's OWN internal accept comparator, plain `==`, cannot
    see) — never a spurious eval exception masquerading as a type
    violation."""
    m2 = artifact["measurement2_trap_anatomy"]
    b_ids = m2["classes"]["b_type_arity_violation"]["task_ids"]
    assert len(b_ids) > 0, "expected at least one bool/numeric laxness catch"
    for tid in b_ids:
        violations = m2["per_task"][str(tid)]["type_arity_check"]["violations"]
        assert violations, "class-b task %d carries no recorded violation" % tid
        assert all("type_mismatch" in v or "arity_mismatch" in v for v in violations), (
            tid, violations)


def test_measurement2_determinism_of_cheap_signals(artifact):
    d = artifact["measurement2_trap_anatomy"]["determinism"]
    assert d["identical"] is True
    assert d["cheap_signals_pass1_hash"] == d["cheap_signals_pass2_hash"]


# --------------------------------------------------------------------------- #
#  6. 3 pinned per-task classifications, RE-VERIFIED LIVE.
# --------------------------------------------------------------------------- #
# 2026-08-01 (arc4 S1): tasks 296 and 108 were both on S1's 17-id target
# list — budget isolation FIXED them, so neither ends `gapped:exhausted`
# live any more. These two tests were never really about those tasks'
# outcomes; they pin the CLASSIFIER (`classify_gapped_exhausted`), which is
# the instrument S0-A used to partition the residual. So the classifier is
# now exercised against the FROZEN rows it was measured on (still the
# authoritative record of the pre-S1 world), and the live legs assert the
# S1 improvement instead of the stale outcome. Both directions still bite:
# a classifier regression fails the first assertion, an S1 regression fails
# the second.
def _frozen_m1(artifact, tid):
    return artifact["measurement1_gapped_exhausted_anatomy"]["per_task"][str(tid)]


def test_pinned_measurement1_class_a_task_296_reverifies_live(live_arm_full, artifact):
    frozen = _frozen_m1(artifact, 296)
    assert frozen["class"] == "a_descend_applicable"
    # Class (a) means: descent-applicable, so the screen could not engage
    # by design and no enumerate rung was ever reached.
    assert frozen["screen_kills"] == 0.0
    assert frozen["rungs"]["enumerate"] is None
    # S1 freed it: it must no longer starve.
    arm_full, _ = live_arm_full
    live = next(r for r in arm_full["runnable_rows"] if r["task_id"] == 296)
    assert live["outcome"] != "gapped:exhausted", (
        "S1 budget isolation should have freed task 296")


def test_pinned_measurement1_class_b_task_108_reverifies_live(live_arm_full, artifact):
    frozen = _frozen_m1(artifact, 108)
    assert frozen["class"] == "b_cued_screen_disengaged"
    # Class (b) means: a cued construction consumed the budget while the
    # screen never engaged (kills == 0) — the starvation S1 targets.
    assert frozen["screen_kills"] == 0.0
    assert frozen["construction"]
    # S1 freed it: it must no longer starve.
    arm_full, _ = live_arm_full
    live = next(r for r in arm_full["runnable_rows"] if r["task_id"] == 108)
    assert live["outcome"] != "gapped:exhausted", (
        "S1 budget isolation should have freed task 108")


def test_pinned_measurement2_task_267_dead_code_freevar_reverifies_live(live_arm_full):
    """Task 267's accepted candidate is a hard-coded IfThenElse memorizing
    the two revealed rows, with UNREACHABLE-BY-RESULT dead code that
    references an unbound free variable ('n'/'b', never a declared
    param). The native ProgEval interpreter never surfaces this (the dead
    assignments are never read), but a faithful Python render executes
    them eagerly and raises -- a genuine, revealed-rows-only pre-accept
    defect signal."""
    arm_full, tasks_by_id = live_arm_full
    row = next(r for r in arm_full["runnable_rows"] if r["task_id"] == 267)
    assert row["outcome"] == "accepted_holdout_fail"
    revealed_rows = aa._revealed_rows_for_task(267, tasks_by_id)
    py = aa.python_cross_check(row["ir"], revealed_rows, "t267")
    assert py["disagree"] is True


# --------------------------------------------------------------------------- #
#  7. toolchain subsample rule — deterministic stride, no silent cap.
# --------------------------------------------------------------------------- #
def test_toolchain_subsample_rule_is_deterministic_and_documented(artifact):
    cond = artifact["condition"]["toolchain_subsample"]
    m2 = artifact["measurement2_trap_anatomy"]
    ahf_ids = m2["ahf_task_ids"]
    stride = max(1, len(ahf_ids) // aa.TOOLCHAIN_SUBSAMPLE_TARGET)
    expected = sorted(ahf_ids[::stride])
    assert cond["ids"] == expected
    assert cond["n_selected"] == len(expected)
    assert m2["toolchain_subsample_ids"] == expected


# --------------------------------------------------------------------------- #
#  8. no-python-decision source audit.
# --------------------------------------------------------------------------- #
def test_runner_source_never_reads_code_field():
    src_path = os.path.join(ROOT, "scripts", "arc4_failure_anatomy.py")
    with open(src_path) as f:
        tree = ast.parse(f.read())
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            key = node.slice
            if isinstance(key, ast.Constant) and key.value == "code":
                hits.append(node.lineno)
    assert hits == [], "task['code'] indexing found at lines: %r" % hits


def test_runner_never_calls_teach():
    """AST-grain check (not a substring scan -- this file's own docstring
    legitimately DESCRIBES the no-teach-call convention in prose): no
    `import domains.teach` / `from domains import teach`, and no `Call`
    whose function is named `teach`."""
    src_path = os.path.join(ROOT, "scripts", "arc4_failure_anatomy.py")
    with open(src_path) as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(a.name == "domains.teach" for a in node.names)
        if isinstance(node, ast.ImportFrom):
            assert not (node.module == "domains" and
                       any(a.name == "teach" for a in node.names))
        if isinstance(node, ast.Call):
            func = node.func
            name = getattr(func, "attr", None) or getattr(func, "id", None)
            assert name != "teach", "unexpected teach(...) call at line %d" % node.lineno


# --------------------------------------------------------------------------- #
#  9. shared contamination gate.
# --------------------------------------------------------------------------- #
def test_shared_contamination_gate_passes():
    res = subprocess.run(
        [sys.executable, "-m", "pytest", "--confcutdir=.",
         "tests/test_mbpp_contamination_migrated.py", "-q"],
        cwd=ROOT, capture_output=True, text=True, timeout=180)
    assert res.returncode == 0, (
        "shared contamination gate failed:\nstdout:\n%s\nstderr:\n%s"
        % (res.stdout, res.stderr))


def test_no_reference_code_lines_leak_into_this_artifact(fixture_tasks):
    """This artifact stores prompts + accepted IR, never `task["code"]` —
    a lightweight version of the Q0-A/Q5 scan, scoped to THIS file."""
    test_tasks = [t for t in fixture_tasks if 11 <= t["task_id"] <= 510]
    forbidden = []
    for t in test_tasks:
        for line in t["code"].splitlines():
            nl = line.strip()
            if len(nl) >= 40:
                forbidden.append(nl)
    with open(ARTIFACT_PATH, "r", errors="replace") as f:
        raw = f.read()
    hits = [line for line in forbidden if line in raw]
    assert hits == [], "reference code line(s) leaked into the artifact: %r" % hits[:5]
