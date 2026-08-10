"""tests/test_mbpp_endgame_migrated.py — Arc 2 Q5: the POWERED MBPP ENDGAME
gate.

Companion to `scripts/mbpp_endgame_battery.py` (the measurement driver),
`results/mbpp_endgame.json` (the artifact this gate re-derives every
aggregate from), `PROGRAM_SYNTHESIS_ARC2_PREREG.md` (HQ3/HQ4, the
three-way PRIMARY/OFFICIAL/STRESS protocol §0).

Gates:
  1. Artifact schema — rows are the baseline (every aggregate re-derives
     from runnable_rows), determinism hashes present + identical per arm,
     protocol tags separate the arms (OFFICIAL never conflated into a
     PRIMARY aggregate).
  2. Contamination — this phase's own scan of results/mbpp_endgame.json
     (mirrors the Q0-A/Q3 own-scan precedent; reuses the shared gate's
     normalize+substring machinery read-only) + runs the SHARED gate
     (tests/test_mbpp_contamination_migrated.py) as a subprocess and
     reports it.
  3. 3-task LIVE re-verification per arm (9 total) — fresh boot, the
     SAME run_task path the script uses, never read from the frozen
     artifact.
  4. The Q0 continuity citation check — results/mbpp_zero_shot_
     baseline.json's sha256 + its own recorded outcome_hash_run1 must
     match what this phase's artifact cited (Q0-A's own file was never
     touched by this phase).

Runtime: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=. tests/test_mbpp_endgame_migrated.py
"""
from __future__ import annotations

import hashlib
import json
import os
import re
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

from domains import mbpp_spec as ms  # noqa: E402
import mbpp_endgame_battery as meb  # noqa: E402

ARTIFACT_PATH = os.path.join(ROOT, "results", "mbpp_endgame.json")
FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")
Q0_BASELINE_PATH = os.path.join(ROOT, "results", "mbpp_zero_shot_baseline.json")


@pytest.fixture(scope="module")
def artifact():
    with open(ARTIFACT_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def fixture_tasks():
    with open(FIXTURE_PATH) as f:
        return json.load(f)


def _task_by_id(tasks, tid):
    for t in tasks:
        if t["task_id"] == tid:
            return dict(t)  # copy — never mutate the shared fixture list
    raise KeyError(tid)


# --------------------------------------------------------------------------- #
#  1. artifact schema — rows are the baseline, aggregates re-derive.
# --------------------------------------------------------------------------- #
def test_artifact_has_all_three_arms(artifact):
    assert set(artifact["arms"].keys()) == {"full", "content_stripped", "official"}


@pytest.mark.parametrize("arm_name,protocol", [
    ("full", "primary"), ("content_stripped", "primary"), ("official", "official"),
])
def test_every_row_carries_its_arms_protocol_tag(artifact, arm_name, protocol):
    arm = artifact["arms"][arm_name]
    for r in arm["runnable_rows"] + arm["excluded_rows"]:
        assert r["protocol"] == protocol, (arm_name, r["task_id"], r["protocol"])


@pytest.mark.parametrize("arm_name", ["full", "content_stripped", "official"])
def test_aggregates_rederive_from_rows(artifact, arm_name):
    arm = artifact["arms"][arm_name]
    n_pass = sum(1 for r in arm["runnable_rows"] if r["outcome"] == "pass")
    n_runnable = len(arm["runnable_rows"])
    agg = arm["aggregates"]["pass_over_runnable"]
    assert agg["k"] == n_pass
    assert agg["n"] == n_runnable
    # both wider-coverage denominators use the SAME k (only n differs)
    assert arm["aggregates"]["pass_over_all_test_257"]["k"] == n_pass
    assert arm["aggregates"]["pass_over_all_427_sanitized"]["k"] == n_pass
    assert arm["aggregates"]["pass_over_all_427_sanitized"]["n"] == 427


@pytest.mark.parametrize("arm_name", ["full", "content_stripped", "official"])
def test_determinism_is_identical_per_arm(artifact, arm_name):
    det = artifact["arms"][arm_name]["determinism"]
    assert det["identical"] is True
    assert det["outcome_hash_run1"] == det["outcome_hash_run2"]
    assert isinstance(det["outcome_hash_run1"], str) and len(det["outcome_hash_run1"]) == 64


def test_official_arm_never_enters_a_primary_aggregate(artifact):
    """Mechanical separation check: the HQ3 delta block reads ONLY the full
    and content_stripped arms (never official) — the REPAIR-ORACLE /
    frozen_p7 precedent, checked by construction here."""
    hq3 = artifact["hq3"]
    delta = hq3["delta_full_minus_content_stripped"]
    full_n = artifact["arms"]["full"]["aggregates"]["pass_over_runnable"]["n"]
    stripped_n = artifact["arms"]["content_stripped"]["aggregates"]["pass_over_runnable"]["n"]
    assert delta["ci95"] is not None
    # the delta's per-episode step must derive from the FULL arm's n, not
    # a mixture with official's (a mixed-arm n would not equal either
    # arm's own runnable count)
    assert abs(delta["per_episode_step"] - 1.0 / full_n) < 1e-6
    assert full_n == stripped_n  # the SAME paired task-id set, by construction


def test_hq3_paired_task_id_set_is_shared(artifact):
    hq3 = artifact["hq3"]
    assert hq3["same_paired_task_id_set"] is True
    assert hq3["full_task_ids"] == hq3["content_stripped_task_ids"]


def test_hq3_gains_and_losses_are_subsets_of_paired_changes(artifact):
    hq3 = artifact["hq3"]
    changed_ids = {c["task_id"] for c in hq3["paired_changes"]}
    for c in hq3["gains_full_over_stripped"] + hq3["losses_stripped_over_full"]:
        assert c["task_id"] in changed_ids


def test_migration_matrix_covers_every_q0_class(artifact):
    with open(Q0_BASELINE_PATH) as f:
        q0 = json.load(f)
    q0_classes = set(q0["outcome_taxonomy"].keys())
    matrix_classes = set(artifact["migration_matrix_vs_q0"].keys())
    assert q0_classes <= matrix_classes


def test_migration_matrix_task_ids_match_q0_taxonomy_counts(artifact):
    with open(Q0_BASELINE_PATH) as f:
        q0 = json.load(f)
    for cls, entry in q0["outcome_taxonomy"].items():
        assert len(artifact["migration_matrix_vs_q0"][cls]["task_ids"]) == entry["n"]


def test_arm_row_counts_sum_to_scope(artifact):
    for arm_name in ("full", "content_stripped", "official"):
        arm = artifact["arms"][arm_name]
        n_expected = arm["n_test_tasks_this_run"]
        assert len(arm["runnable_rows"]) + len(arm["excluded_rows"]) == n_expected


# --------------------------------------------------------------------------- #
#  2. contamination.
# --------------------------------------------------------------------------- #
_WS_RE = re.compile(r"\s+")
_MIN_PROMPT_LEN = 20
_MIN_CODE_LINE_LEN = 15


def _normalize(s: str) -> str:
    return _WS_RE.sub(" ", s.strip().lower())


def _own_forbidden_substrings(fixture_tasks) -> list:
    test_tasks = [t for t in fixture_tasks if 11 <= t["task_id"] <= 510]
    forbidden = []
    for t in test_tasks:
        p = _normalize(t["prompt"])
        if len(p) >= _MIN_PROMPT_LEN:
            forbidden.append(p)
        for line in t["code"].splitlines():
            nl = _normalize(line)
            if len(nl) >= _MIN_CODE_LINE_LEN:
                forbidden.append(nl)
    return forbidden


def test_own_contamination_scan_of_the_endgame_artifact_is_clean(fixture_tasks):
    """This phase's own equivalent of the Q0-A/Q3 scan, applied to its own
    NEW artifact — results/mbpp_endgame.json is an eval log (like Q0-A's
    own), never a codebook, but this scan proves it is clean anyway (no
    prompt substring should ever appear as part of a MINTED codebook
    entry name/trigger — this artifact carries no such entries at all,
    only per-task outcome rows)."""
    forbidden = _own_forbidden_substrings(fixture_tasks)
    assert len(forbidden) > 200
    with open(ARTIFACT_PATH, "r", errors="replace") as f:
        raw = f.read()
    norm = _normalize(raw)
    # the artifact legitimately CONTAINS every test-split prompt (it is an
    # eval log — the same status as results/mbpp_zero_shot_baseline.json,
    # explicitly excluded from the shared gate's SCAN_TARGETS). What this
    # scan actually protects against is a full VERBATIM reference-code
    # LINE leaking in (this runner never reads task["code"] at all, so
    # none should ever appear).
    code_lines = [f for f in forbidden if f not in
                  {_normalize(t["prompt"]) for t in fixture_tasks}]
    hits = [line for line in code_lines if line in norm]
    assert hits == [], "reference code line(s) leaked into the endgame artifact: %r" % hits[:5]


def test_shared_contamination_gate_passes():
    """Runs tests/test_mbpp_contamination_migrated.py (Q0-A-owned, not
    modified by this phase) as a subprocess and reports the result — the
    task brief's explicit instruction to run and report it."""
    res = subprocess.run(
        [sys.executable, "-m", "pytest", "--confcutdir=.",
         "tests/test_mbpp_contamination_migrated.py", "-q"],
        cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert res.returncode == 0, (
        "shared contamination gate failed:\nstdout:\n%s\nstderr:\n%s"
        % (res.stdout, res.stderr))


# --------------------------------------------------------------------------- #
#  3. 3-task LIVE re-verification per arm (9 total; never read from the
#     frozen artifact — fresh boot, the SAME run_task path the script
#     itself uses).
# --------------------------------------------------------------------------- #
# 2026-08-01 (arc4 S1): freed by budget isolation — can no longer starve.
_ARC4_S1_FREED = {108, 142}

# 2026-08-01 (arc5 cross-phase reconciliation, PROGRAM_SYNTHESIS_ARC5_
# FINAL.md): task 464's "content_stripped" pin ('pass') has genuinely
# drifted to 'accepted_holdout_fail'. This is a PRE-EXISTING coincidental
# fit being CORRECTLY exposed, not a new defect this reconciliation
# introduces: the frozen 'pass' program is `Gt(b, 10)`, which never reads
# the dict parameter `a` at all (an unread-parameter defect) and only
# coincidentally agreed with this task's own 3 rows because they happen
# to straddle b=10 — independently reconstructed and proven wrong via a
# constructed witness in tests/test_reject_informs_repair_migrated.py::
# test_task_92_and_464_frozen_passes_were_already_coincidental_fits. The
# live engine now finds a DIFFERENT wrong candidate here (arc5's rational-
# domain landing, 72ed5096a5, widened SynthEnumerate's literal search
# space, changing candidate discovery ORDER corpus-wide, not just for the
# exact-family rung) that happens to fail its OWN held-out row instead of
# passing by luck — an improvement (the held-out check now catches the
# defect), not a regression. See PROGRAM_SYNTHESIS_ARC5_FINAL.md's
# discrepancy-explanation section for the full account.
_PINNED = {
    "full": [(16, "pass"), (108, "gapped:exhausted"), (237, "runner_exception:TypeError")],
    "content_stripped": [(16, "pass"), (464, "accepted_holdout_fail"),
                         (108, "gapped:enumerate_failed")],
    "official": [(16, "pass"), (108, "gapped:exhausted"), (237, "runner_exception:TypeError")],
}


@pytest.mark.parametrize("arm_name,task_id,expected_outcome", [
    (arm, tid, out) for arm, rows in _PINNED.items() for tid, out in rows
])
def test_pinned_task_reverifies_live(fixture_tasks, arm_name, task_id, expected_outcome):
    task = _task_by_id(fixture_tasks, task_id)
    task.pop("code", None)  # the same contamination enforcement point every runner uses
    parsed = ms.parse_asserts(task)
    rows = parsed["rows"]
    report = {
        "n_test_list": len(task.get("test_list", [])),
        "n_parseable": len(rows),
        "n_unparseable": len(parsed["unparseable"]),
        "unparseable_reasons": [u["form"] for u in parsed["unparseable"]],
    }
    protocol = meb.ARM_PROTOCOL[arm_name]
    spec = ms.split_rows(rows, protocol)
    assert spec["runnable"], "pinned task %d unexpectedly non-runnable under %s" % (
        task_id, protocol)
    row = meb.run_task(task, spec, report, meb.ARM_BOOT[arm_name], protocol)
    if expected_outcome == "gapped:exhausted" and task_id in _ARC4_S1_FREED:
        # 2026-08-01 (arc4 S1): budget isolation freed task 108 (it was on
        # S1's own 17-id target list), so it can no longer starve. The
        # FROZEN arc-2 artifact stays authoritative for its own run and is
        # hash-checked elsewhere in this module; the live leg asserts the
        # improvement and still bites if S1 regresses.
        assert row["outcome"] != "gapped:exhausted", (
            "arc4 S1 should have freed task %d under arm %s, got %s"
            % (task_id, arm_name, row["outcome"]))
        return
    assert row["outcome"] == expected_outcome, (
        "live reverify drift: arm=%s task=%d got=%s expected=%s"
        % (arm_name, task_id, row["outcome"], expected_outcome))


# --------------------------------------------------------------------------- #
#  4. the Q0 continuity citation check.
# --------------------------------------------------------------------------- #
def test_q0_baseline_artifact_hash_is_unchanged(artifact):
    with open(Q0_BASELINE_PATH, "rb") as f:
        raw = f.read()
    live_sha256 = hashlib.sha256(raw).hexdigest()
    assert artifact["q0_continuity"]["sha256"] == live_sha256, (
        "results/mbpp_zero_shot_baseline.json changed underneath this "
        "phase's citation — Q0-A's frozen artifact must stay untouched")
    live = json.loads(raw)
    assert (artifact["q0_continuity"]["cited_outcome_hash_run1"]
            == live["determinism"]["outcome_hash_run1"])


def test_q0_baseline_headline_number_unchanged():
    """The 1/240 = 0.42% zero-shot/STRESS headline this phase cites but
    never re-runs (PROGRAM_SYNTHESIS_ARC2_Q0_BASELINE.md §3)."""
    with open(Q0_BASELINE_PATH) as f:
        q0 = json.load(f)
    agg = q0["aggregates"]["pass_over_runnable"]
    assert agg["k"] == 1 and agg["n"] == 240


# --------------------------------------------------------------------------- #
#  contamination — this runner never reads a test-split task's code field
#  (source-level audit, the standing no-Python-decision-source-audit class).
# --------------------------------------------------------------------------- #
def test_runner_source_never_reads_code_field():
    """AST-based scan (never a text/docstring false-positive): no
    Subscript node anywhere in the runner indexes a `"code"` key."""
    import ast
    src_path = os.path.join(ROOT, "scripts", "mbpp_endgame_battery.py")
    with open(src_path) as f:
        tree = ast.parse(f.read())
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            key = node.slice
            if isinstance(key, ast.Constant) and key.value == "code":
                hits.append(node.lineno)
    assert hits == [], "task['code'] indexing found at lines: %r" % hits
