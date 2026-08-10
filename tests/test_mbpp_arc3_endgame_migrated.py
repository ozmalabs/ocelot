"""tests/test_mbpp_arc3_endgame_migrated.py — Arc 3 R3: the POWERED MBPP
ENDGAME gate (HR1/HR2/HR3).

Companion to `scripts/mbpp_arc3_battery.py` (the measurement driver),
`results/mbpp_arc3_endgame.json` (the artifact this gate re-derives every
aggregate from), `PROGRAM_SYNTHESIS_ARC3_PREREG.md` (HR1/HR2/HR3, the bars
this phase judges against), `results/mbpp_endgame.json` (arc-2's FULL arm —
the paired continuity comparator, frozen, never re-run here),
`results/retrieval_oracle_ceiling.json` (R0's oracle ceiling, frozen).

Gates:
  1. Artifact schema — three arms present, protocol tags correct, OFFICIAL
     never enters a PRIMARY aggregate, aggregates re-derive from rows,
     determinism hashes identical per arm.
  2. The NO-RETRIEVAL off-switch — confirmed live (0 Exemplar nodes after
     that boot; a real MBPP-shaped request still completes via the
     codebook path).
  3. HR1 — paired task-id set shared, gains/losses subsets of paired
     changes, the registered ladder banding is internally consistent with
     the reported net_passes + CI-separation.
  4. HR2 — the covered/residual class partition sums to 24 (Q5's own
     gapped:exhausted count), covered-class-still-exhausted count matches
     the per-task table.
  5. Contamination — this phase's own scan + the shared gate run as a
     subprocess.
  6. 3-task LIVE re-verification per arm (9 total) — fresh boot, the SAME
     run_task path the script uses.
  7. Frozen-artifact hash checks — results/mbpp_endgame.json (arc-2 FULL
     continuity) and results/retrieval_oracle_ceiling.json (R0 ceiling
     continuity) are BYTE-UNTOUCHED by this phase.
  8. No-python-decision source audit of the runner (never reads
     task["code"]).

Runtime: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=. tests/test_mbpp_arc3_endgame_migrated.py
"""
from __future__ import annotations

import ast
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
import mbpp_arc3_battery as mab  # noqa: E402

ARTIFACT_PATH = os.path.join(ROOT, "results", "mbpp_arc3_endgame.json")
FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")
ARC2_ENDGAME_PATH = os.path.join(ROOT, "results", "mbpp_endgame.json")
R0_CEILING_PATH = os.path.join(ROOT, "results", "retrieval_oracle_ceiling.json")


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
#  1. artifact schema.
# --------------------------------------------------------------------------- #
def test_artifact_has_all_three_arms(artifact):
    assert set(artifact["arms"].keys()) == {"full_r3", "no_retrieval", "official_r3"}


@pytest.mark.parametrize("arm_name,protocol", [
    ("full_r3", "primary"), ("no_retrieval", "primary"), ("official_r3", "official"),
])
def test_every_row_carries_its_arms_protocol_tag(artifact, arm_name, protocol):
    arm = artifact["arms"][arm_name]
    for r in arm["runnable_rows"] + arm["excluded_rows"]:
        assert r["protocol"] == protocol, (arm_name, r["task_id"], r["protocol"])


@pytest.mark.parametrize("arm_name", ["full_r3", "no_retrieval", "official_r3"])
def test_aggregates_rederive_from_rows(artifact, arm_name):
    arm = artifact["arms"][arm_name]
    n_pass = sum(1 for r in arm["runnable_rows"] if r["outcome"] == "pass")
    n_runnable = len(arm["runnable_rows"])
    agg = arm["aggregates"]["pass_over_runnable"]
    assert agg["k"] == n_pass
    assert agg["n"] == n_runnable
    assert arm["aggregates"]["pass_over_all_test_257"]["k"] == n_pass
    assert arm["aggregates"]["pass_over_all_427_sanitized"]["k"] == n_pass
    assert arm["aggregates"]["pass_over_all_427_sanitized"]["n"] == 427


@pytest.mark.parametrize("arm_name", ["full_r3", "no_retrieval", "official_r3"])
def test_determinism_is_identical_per_arm(artifact, arm_name):
    det = artifact["arms"][arm_name]["determinism"]
    assert det["identical"] is True
    assert det["outcome_hash_run1"] == det["outcome_hash_run2"]
    assert isinstance(det["outcome_hash_run1"], str) and len(det["outcome_hash_run1"]) == 64


def test_official_arm_never_enters_hr1_or_hr2(artifact):
    """Mechanical separation check: HR1's delta is built ONLY from full_r3
    and no_retrieval (never official_r3)."""
    hr1 = artifact["hr1"]
    full_n = artifact["arms"]["full_r3"]["aggregates"]["pass_over_runnable"]["n"]
    noret_n = artifact["arms"]["no_retrieval"]["aggregates"]["pass_over_runnable"]["n"]
    delta = hr1["delta_full_r3_minus_no_retrieval"]
    assert abs(delta["per_episode_step"] - 1.0 / full_n) < 1e-6
    assert full_n == noret_n


def test_arm_row_counts_sum_to_scope(artifact):
    for arm_name in ("full_r3", "no_retrieval", "official_r3"):
        arm = artifact["arms"][arm_name]
        n_expected = arm["n_test_tasks_this_run"]
        assert len(arm["runnable_rows"]) + len(arm["excluded_rows"]) == n_expected


# --------------------------------------------------------------------------- #
#  2. the NO-RETRIEVAL off-switch, confirmed live.
# --------------------------------------------------------------------------- #
def test_no_retrieval_boot_installs_zero_exemplar_nodes():
    s, ag = mab.boot_no_retrieval()
    assert list(s.nodes("Exemplar")) == []


def test_no_retrieval_boot_still_solves_a_codebook_shaped_request():
    """The off-switch must be a true no-op fall-through, not a broken
    boot: a plain MBPP-shaped add-two-numbers request still completes via
    the UNCHANGED codebook/enumerate path."""
    from domains import prog_synthesis as psy
    s, ag = mab.boot_no_retrieval()
    r = psy.synthesize_from_request(
        s, ag, "Write a python function to add two numbers.",
        [{"inputs": {"a": 1, "b": 2}, "expected": 3},
         {"inputs": {"a": 5, "b": 7}, "expected": 12}])
    assert r["status"] == "accepted"
    assert (r.get("retrieval") or {}).get("rung_reached") in (None, "none")


def test_full_r3_boot_installs_the_90_exemplar_pool():
    s, ag = mab.boot_full_r3()
    assert len(list(s.nodes("Exemplar"))) == 90


# --------------------------------------------------------------------------- #
#  3. HR1 — the paired ladder.
# --------------------------------------------------------------------------- #
def test_hr1_paired_task_id_set_is_shared(artifact):
    hr1 = artifact["hr1"]
    assert hr1["same_paired_task_id_set"] is True
    assert hr1["n_common_runnable"] == 257


def test_hr1_gains_and_losses_are_subsets_of_paired_changes(artifact):
    hr1 = artifact["hr1"]
    changed_ids = {c["task_id"] for c in hr1["paired_changes"]}
    for c in (hr1["gains_full_r3_over_no_retrieval"]
              + hr1["losses_no_retrieval_over_full_r3"]):
        assert c["task_id"] in changed_ids


def test_hr1_net_passes_matches_gains_minus_losses(artifact):
    hr1 = artifact["hr1"]
    expected = (len(hr1["gains_full_r3_over_no_retrieval"])
               - len(hr1["losses_no_retrieval_over_full_r3"]))
    assert hr1["net_passes"] == expected


def test_hr1_verdict_band_matches_the_registered_ladder(artifact):
    hr1 = artifact["hr1"]
    delta = hr1["delta_full_r3_minus_no_retrieval"]
    ci_separated = delta["ci95"][0] > 0 or delta["ci95"][1] < 0
    net = hr1["net_passes"]
    if net >= 6 and ci_separated:
        expected = "strong_confirmation"
    elif 1 <= net <= 5 and ci_separated:
        expected = "weak_marginal_confirmation"
    else:
        expected = "null"
    assert hr1["verdict_band"] == expected


def test_hr1_every_gain_and_loss_carries_a_named_attribution(artifact):
    hr1 = artifact["hr1"]
    for c in (hr1["gains_full_r3_over_no_retrieval"]
              + hr1["losses_no_retrieval_over_full_r3"]):
        assert c["attribution"] and c["attribution"] != "unattributed"


# --------------------------------------------------------------------------- #
#  4. HR2 — the gapped:exhausted taxonomy vs Q5.
# --------------------------------------------------------------------------- #
def test_hr2_covered_plus_residual_equals_q5_24(artifact):
    hr2 = artifact["hr2"]
    assert (hr2["q5_baseline"]["n_covered_class"]
           + hr2["q5_baseline"]["n_residual_class"]) == hr2["q5_baseline"]["n_gapped_exhausted"]
    assert hr2["q5_baseline"]["n_gapped_exhausted"] == 24


def test_hr2_still_exhausted_counts_match_the_per_task_tables(artifact):
    hr2 = artifact["hr2"]
    covered_still = [tid for tid, out in hr2["covered_class_now"].items()
                     if out == "gapped:exhausted"]
    assert len(covered_still) == hr2["n_covered_class_still_gapped_exhausted"]
    residual_still = [tid for tid, out in hr2["residual_class_now"].items()
                      if out == "gapped:exhausted"]
    assert len(residual_still) == hr2["n_residual_class_still_gapped_exhausted"]


def test_hr2_residual_class_is_entirely_unchanged(artifact):
    """The 7-row starter-codebook-shape class is out of the R2.5 screen's
    scope BY DESIGN (DESCEND_APPLICABLE) — every one of the 7 must still
    be gapped:exhausted (byte-identical outcome class to Q5)."""
    hr2 = artifact["hr2"]
    assert hr2["n_residual_class_still_gapped_exhausted"] == hr2["q5_baseline"]["n_residual_class"]


def test_hr2_covered_class_mechanism_attribution_sums(artifact):
    hr2 = artifact["hr2"]
    counts = hr2["covered_class_mechanism_counts"]
    assert sum(counts.values()) == hr2["q5_baseline"]["n_covered_class"]


# --------------------------------------------------------------------------- #
#  5. contamination.
# --------------------------------------------------------------------------- #
_WS_RE = re.compile(r"\s+")
_MIN_PROMPT_LEN = 20
_MIN_CODE_LINE_LEN = 15


def _normalize(s: str) -> str:
    return _WS_RE.sub(" ", s.strip().lower())


def _own_forbidden_substrings(fixture_tasks):
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


def test_own_contamination_scan_of_the_arc3_endgame_artifact_is_clean(fixture_tasks):
    """This phase's own equivalent of the Q0-A/Q5 scan — the artifact is
    an eval log (legitimately contains every test prompt), but no VERBATIM
    reference-code line should ever leak in (this runner never reads
    task['code'])."""
    forbidden = _own_forbidden_substrings(fixture_tasks)
    assert len(forbidden) > 200
    with open(ARTIFACT_PATH, "r", errors="replace") as f:
        raw = f.read()
    norm = _normalize(raw)
    code_lines = [f for f in forbidden if f not in
                  {_normalize(t["prompt"]) for t in fixture_tasks}]
    hits = [line for line in code_lines if line in norm]
    assert hits == [], "reference code line(s) leaked into the arc3 endgame artifact: %r" % hits[:5]


def test_shared_contamination_gate_passes():
    res = subprocess.run(
        [sys.executable, "-m", "pytest", "--confcutdir=.",
         "tests/test_mbpp_contamination_migrated.py", "-q"],
        cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert res.returncode == 0, (
        "shared contamination gate failed:\nstdout:\n%s\nstderr:\n%s"
        % (res.stdout, res.stderr))


# --------------------------------------------------------------------------- #
#  6. 3-task LIVE re-verification per arm (9 total).
# --------------------------------------------------------------------------- #
# 2026-08-01 (arc4 S1): tasks freed by budget isolation — they can no
# longer end `gapped:exhausted` live. See the drift branch in
# test_pinned_task_reverifies_live below.
_ARC4_S1_FREED = {108, 142}

_PINNED = {
    "full_r3": [(16, "pass"), (108, "gapped:exhausted"), (142, "pass")],
    "no_retrieval": [(16, "pass"), (108, "gapped:exhausted"), (142, "gapped:exhausted")],
    "official_r3": [(16, "pass"), (108, "gapped:exhausted"), (237, "runner_exception:TypeError")],
}


@pytest.mark.parametrize("arm_name,task_id,expected_outcome", [
    (arm, tid, out) for arm, rows in _PINNED.items() for tid, out in rows
])
def test_pinned_task_reverifies_live(fixture_tasks, arm_name, task_id, expected_outcome):
    task = _task_by_id(fixture_tasks, task_id)
    task.pop("code", None)
    parsed = ms.parse_asserts(task)
    rows = parsed["rows"]
    report = {
        "n_test_list": len(task.get("test_list", [])),
        "n_parseable": len(rows),
        "n_unparseable": len(parsed["unparseable"]),
        "unparseable_reasons": [u["form"] for u in parsed["unparseable"]],
    }
    protocol = mab.ARM_PROTOCOL[arm_name]
    spec = ms.split_rows(rows, protocol)
    assert spec["runnable"], "pinned task %d unexpectedly non-runnable under %s" % (
        task_id, protocol)
    row = mab.run_task(task, spec, report, mab.ARM_BOOT[arm_name], protocol)
    if expected_outcome == "gapped:exhausted" and task_id in _ARC4_S1_FREED:
        # 2026-08-01 (arc4 S1): budget isolation gave starved goals their
        # reserved enumerator turn. Tasks 108 and 142 were on S1's own
        # target list (142 was its documented bonus fix), so neither can
        # still end `gapped:exhausted` — asserting they do would now be
        # asserting that arc 4 did nothing. The FROZEN artifact remains
        # authoritative for its own run (hash-checked below); the live leg
        # asserts the improvement instead, and still bites if S1 regresses.
        assert expected_outcome == "gapped:exhausted"
        assert row["outcome"] != "gapped:exhausted", (
            "arc4 S1 should have freed task %d under arm %s, got %s"
            % (task_id, arm_name, row["outcome"]))
        return
    assert row["outcome"] == expected_outcome, (
        "live reverify drift: arm=%s task=%d got=%s expected=%s"
        % (arm_name, task_id, row["outcome"], expected_outcome))


# --------------------------------------------------------------------------- #
#  7. frozen-artifact hash checks — arc-2 FULL continuity + R0 ceiling.
# --------------------------------------------------------------------------- #
def test_arc2_endgame_artifact_hash_is_unchanged(artifact):
    with open(ARC2_ENDGAME_PATH, "rb") as f:
        raw = f.read()
    live_sha256 = hashlib.sha256(raw).hexdigest()
    assert artifact["arc2_full_continuity"]["sha256"] == live_sha256, (
        "results/mbpp_endgame.json changed underneath this phase's "
        "citation — arc-2's frozen artifact must stay untouched")
    live = json.loads(raw)
    assert (artifact["arc2_full_continuity"]["cited_outcome_hash_run1"]
            == live["arms"]["full"]["determinism"]["outcome_hash_run1"])


def test_arc2_full_headline_number_unchanged():
    """The 18/257 = 7.00% arc-2 FULL headline this phase cites but never
    re-runs (PROGRAM_SYNTHESIS_ARC2_Q5.md §1)."""
    with open(ARC2_ENDGAME_PATH) as f:
        q5 = json.load(f)
    agg = q5["arms"]["full"]["aggregates"]["pass_over_runnable"]
    assert agg["k"] == 18 and agg["n"] == 257


def test_r0_ceiling_artifact_hash_is_unchanged(artifact):
    with open(R0_CEILING_PATH, "rb") as f:
        raw = f.read()
    live_sha256 = hashlib.sha256(raw).hexdigest()
    assert artifact["r0_ceiling_continuity"]["sha256"] == live_sha256, (
        "results/retrieval_oracle_ceiling.json changed underneath this "
        "phase's citation — R0's frozen artifact must stay untouched")


def test_r0_ceiling_headline_number_unchanged():
    """The 12/257 = 4.67% held-out-honest ceiling HR1's bar derives from
    (PROGRAM_SYNTHESIS_ARC3_R0_NOTES.md §2)."""
    with open(R0_CEILING_PATH) as f:
        r0 = json.load(f)
    ac = r0["ceiling"]["heldout_pass_cumulative_a_to_c"]["c"]
    assert ac["k"] == 12 and ac["n"] == 257


# --------------------------------------------------------------------------- #
#  8. no-python-decision source audit — the runner never reads task['code'].
# --------------------------------------------------------------------------- #
def test_runner_source_never_reads_code_field():
    src_path = os.path.join(ROOT, "scripts", "mbpp_arc3_battery.py")
    with open(src_path) as f:
        tree = ast.parse(f.read())
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            key = node.slice
            if isinstance(key, ast.Constant) and key.value == "code":
                hits.append(node.lineno)
    assert hits == [], "task['code'] indexing found at lines: %r" % hits
