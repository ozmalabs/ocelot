"""Tests for scripts/report_seed_boot_status.py (P0.H3)."""
from __future__ import annotations

import time

from scripts.report_seed_boot_status import ROOT, build_seed_boot_report


def test_report_seed_boot_status_classifications_and_broken_deps():
    t0 = time.time()
    report = build_seed_boot_report(ROOT)
    elapsed = time.time() - t0
    assert elapsed < 30.0, f"report_seed_boot_status took {elapsed:.1f}s (>= 30s limit)"

    assert report["episodic_working_memory_core"]["class"] == "C"
    assert report["dual_process_core"]["class"] == "OPT"
    assert report["self_account_reply"]["class"] == "Prof"
    assert report["core_emotions"]["class"] == "SLO"
    assert report["compositional_plan"]["class"] == "Bulk"
    assert report["llvm_passes"]["broken_deps"] == []
    assert "core" in report["observer_aperture"]["broken_deps"]
