"""Tests for scripts/lint_orphan_signals.py (P0.H2)."""
from __future__ import annotations

import json
import time

from scripts.lint_orphan_signals import DEFAULT_ALLOWLIST, ROOT, scan_orphan_signals


def test_lint_orphan_signals_seed_and_full():
    t0 = time.time()
    orphans_seed_only = scan_orphan_signals(root=ROOT, allowlist_path=None, include_code_reads=False)
    assert "synthesis_requested" in orphans_seed_only
    assert "needs_decomposition" in orphans_seed_only
    assert "needs_tool" not in orphans_seed_only
    assert "has_memory_cycle" not in orphans_seed_only
    assert "obs_unassessable" not in orphans_seed_only

    orphans_full = scan_orphan_signals(root=ROOT, allowlist_path=DEFAULT_ALLOWLIST, include_code_reads=True)
    elapsed = time.time() - t0
    assert elapsed < 60.0, f"lint_orphan_signals took {elapsed:.1f}s (>= 60s limit)"

    # Known orphans must be flagged
    assert "synthesis_requested" in orphans_full
    assert "capability_collapse:cc_refuse_missing_or_ambiguous_outcome" in orphans_full["synthesis_requested"]["writers"]
    assert "needs_decomposition" in orphans_full
    assert any(w.startswith("impasse_escalation:") for w in orphans_full["needs_decomposition"]["writers"])
    assert any(w.startswith("repair_escalation:") for w in orphans_full["needs_decomposition"]["writers"])
    assert "obs_established" in orphans_full
    assert "reason" in orphans_full["obs_established"]

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
