"""Tests for scripts/lint_orphan_signals.py (P0.H2)."""
from __future__ import annotations

import json
import time

from scripts.lint_orphan_signals import DEFAULT_ALLOWLIST, ROOT, scan_orphan_signals


def test_lint_orphan_signals_seed_and_full():
    t0 = time.time()
    p1_bridges = {"capability_synthesis_bridge", "decomposition_consumer"}
    orphans_seed_only = scan_orphan_signals(
        root=ROOT,
        allowlist_path=None,
        include_code_reads=False,
        exclude_seeds=p1_bridges,
    )
    assert "synthesis_requested" in orphans_seed_only
    assert "needs_decomposition" in orphans_seed_only
    assert "needs_tool" not in orphans_seed_only
    assert "has_memory_cycle" not in orphans_seed_only
    assert "obs_unassessable" not in orphans_seed_only

    orphans_pre_p1 = scan_orphan_signals(
        root=ROOT,
        allowlist_path=DEFAULT_ALLOWLIST,
        include_code_reads=True,
        exclude_seeds=p1_bridges,
    )
    elapsed = time.time() - t0
    assert elapsed < 60.0, f"lint_orphan_signals took {elapsed:.1f}s (>= 60s limit)"

    # Pre-P1 orphans must be flagged when P1 bridge seeds are excluded
    assert "synthesis_requested" in orphans_pre_p1
    assert "capability_collapse:cc_refuse_missing_or_ambiguous_outcome" in orphans_pre_p1["synthesis_requested"]["writers"]
    assert "needs_decomposition" in orphans_pre_p1
    assert any(w.startswith("impasse_escalation:") for w in orphans_pre_p1["needs_decomposition"]["writers"])
    assert any(w.startswith("repair_escalation:") for w in orphans_pre_p1["needs_decomposition"]["writers"])
    assert "obs_established" in orphans_pre_p1
    assert "reason" in orphans_pre_p1["obs_established"]

    t0 = time.time()
    orphans_full = scan_orphan_signals(root=ROOT, allowlist_path=DEFAULT_ALLOWLIST, include_code_reads=True)
    elapsed = time.time() - t0
    assert elapsed < 60.0, f"lint_orphan_signals took {elapsed:.1f}s (>= 60s limit)"
    assert "synthesis_requested" not in orphans_full
    assert "needs_decomposition" in orphans_full
    assert orphans_full["needs_decomposition"]["kind"] == "attr"
    assert orphans_full["needs_decomposition"]["writers"] == ["repair_escalation:repair_rung_order3_reframe"]
    assert "reason" in orphans_full["needs_decomposition"]

    # Signals that are read in seeds must not be flagged
    assert "needs_tool" not in orphans_full
    assert "has_memory_cycle" not in orphans_full
    assert "obs_unassessable" not in orphans_full

    # Allowlist discipline: every entry must have a non-empty reason
    allowlist = json.loads(DEFAULT_ALLOWLIST.read_text(encoding="utf-8"))
    assert isinstance(allowlist, dict) and allowlist
    for name, reason in allowlist.items():
        assert isinstance(reason, str) and reason.strip(), f"empty reason for {name}"

    # Determinism check: running twice produces identical output
    orphans_second = scan_orphan_signals(root=ROOT, allowlist_path=DEFAULT_ALLOWLIST, include_code_reads=True)
    assert list(orphans_full.items()) == list(orphans_second.items())
