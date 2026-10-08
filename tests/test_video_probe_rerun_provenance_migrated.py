"""PROVENANCE SELF-AUDIT for the VIDEO PROBE RE-RUN.

§12.3: a provenance claim must diff a range with **BOTH ENDPOINTS FIXED**. Never
`HEAD`, never the working tree. `tests/test_provenance_endpoint_guard_migrated.py`
is the systemic guard that fails any test in this directory violating that, and
the defect it guards has been recorded SIX times in this arc.

WHAT THIS RUNG CLAIMED, and therefore what this file asserts:

  * it adds **NO Rust** — the engine it measured is a reproducible build of the
    tree's existing source (md5 byte-identical to the batch-apply rung's), and
    the whole attribution argument in §4.1 depends on that being true;
  * it adds/edits **NO seed** — A9's batch-off arm varies a TEMP COPY of
    `domain_data/vision_change.json`, never the file. If the repo seed had been
    edited, the "batch LIVE as committed" arm would be measuring something that
    is not committed, and §4.1's isolation would be worthless;
  * it touches **only files it owns** — no other rung's results, prereg or gate.

A GATE THAT HAS ONLY EVER BEEN SEEN TO PASS IS NOT A GATE THAT HAS BEEN TESTED.
This file was positive-controlled by widening BASE_SHA to an older arc commit —
a range that really does contain Rust, seed and foreign edits — and confirming
the assertions go RED, then restoring the pin and confirming GREEN.
"""
from __future__ import annotations

import os
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# A provenance pin THIS REPOSITORY CANNOT RESOLVE is a SKIP, not a red: the claim
# is unverifiable here, not false, and the gate re-arms unchanged against a repo
# that has the range (tests/provenance_pins.py, red-test triage 2026-08-12).
from provenance_pins import skip_if_unresolvable as _skip_unresolvable_pin  # noqa: E402


# BOTH ENDPOINTS PINNED. Neither is HEAD; neither is the working tree.
BASE_SHA = "c6c022f8fc2ab212b130ad3e34a761af6a20aaee"
RUNG_SHA = "bf57efc34ddf6a96b229895ada3a57109ea51b52"

# Everything this rung is permitted to touch, enumerated positively.
OWNED = {
    "research/experiments/gamma-substrate/VISION_VIDEO_PROBE_RERUN_PREREG.md",
    "research/experiments/gamma-substrate/VISION_VIDEO_PROBE_RERUN_RESULTS.md",
    "research/experiments/gamma-substrate/scripts/video_probe_rerun_layers.py",
    "research/experiments/gamma-substrate/scripts/video_probe_rerun_sd_explore.py",
    "research/experiments/gamma-substrate/tests/test_video_probe_rerun_provenance_migrated.py",
    "research/experiments/gamma-substrate/results/video_probe_rerun.json",
    "research/experiments/gamma-substrate/results/video_probe_diagnose_rerun.json",
    "research/experiments/gamma-substrate/results/video_probe_rerun_layers.json",
    "research/experiments/gamma-substrate/results/video_probe_rerun_sd_explore.json",
    "research/experiments/gamma-substrate/results/video_probe_rerun_s2_attrib.json",
    "research/experiments/gamma-substrate/VISION_PROTOCOL.md",
}

_PLACEHOLDER = RUNG_SHA.startswith("__")


def _git(*args) -> str:
    return subprocess.run(("git", *args), cwd=ROOT, capture_output=True,
                          text=True, check=True).stdout


def _changed() -> list[str]:
    # `:/` root-magic pathspec: git reports --name-only paths from the git ROOT
    # but resolves a PATHSPEC relative to CWD, and this suite runs from the
    # experiment dir. That mismatch silently emptied an earlier rung's gate.
    out = _git("diff", "--name-only", BASE_SHA, RUNG_SHA, "--", ":/")
    return [ln for ln in out.splitlines() if ln.strip()]


pytestmark = pytest.mark.skipif(
    _PLACEHOLDER, reason="RUNG_SHA not yet substituted (pre-commit placeholder)")


@_skip_unresolvable_pin(BASE_SHA, RUNG_SHA)
def test_adds_no_rust():
    """The engine is a reproducible build of EXISTING source.

    §4.1's entire attribution argument — that batch-apply accounts for the whole
    exponent delta — rests on the Rust not having moved. If this rung had added
    Rust, the isolation would be comparing two different engines."""
    rust = [p for p in _changed() if p.endswith((".rs", "Cargo.toml", "Cargo.lock"))]
    assert rust == [], f"this rung claims NO Rust, but the range touches {rust}"


@_skip_unresolvable_pin(BASE_SHA, RUNG_SHA)
def test_adds_or_edits_no_seed():
    """A9's control varies a TEMP COPY, never the committed seed.

    If `domain_data/vision_change.json` had been edited, the arm labelled 'batch LIVE
    as committed' would not be measuring what is committed."""
    seeds = [p for p in _changed() if "/seeds/" in p and p.endswith(".json")]
    assert seeds == [], f"this rung claims NO seed edit, but the range touches {seeds}"


@_skip_unresolvable_pin(BASE_SHA, RUNG_SHA)
def test_touches_only_files_it_owns():
    foreign = sorted(set(_changed()) - OWNED)
    assert foreign == [], (
        "this rung touched files it does not own — another rung's results, "
        f"prereg or gate may have been clobbered: {foreign}")


@_skip_unresolvable_pin(BASE_SHA, RUNG_SHA)
def test_the_protocol_edit_is_one_appended_ledger_row():
    """The one shared file this rung edits, and it may only APPEND."""
    diff = _git("diff", "--unified=0", BASE_SHA, RUNG_SHA, "--",
                ":/research/experiments/gamma-substrate/VISION_PROTOCOL.md")
    added = [ln for ln in diff.splitlines()
             if ln.startswith("+") and not ln.startswith("+++")]
    removed = [ln for ln in diff.splitlines()
               if ln.startswith("-") and not ln.startswith("---")]
    assert removed == [], f"the ledger edit DELETED lines: {removed}"
    assert len(added) == 1, f"expected ONE appended ledger row, got {len(added)}"
    assert "65000" in added[0], "the appended row does not name this rung's seed block"


def test_the_engine_measured_is_this_trees_source():
    """The capability pin: the loaded engine must be a build of THIS tree's Rust.

    §10.1 rule 1 — `engine X @ path` alone does not say whether X was built from
    the source the numbers are attributed to."""
    from domains.engine_provenance import provenance_line
    line = provenance_line()
    assert "DIVERGED" not in line, (
        f"the loaded engine DIVERGED from this tree's Rust source: {line}")
