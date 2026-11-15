from __future__ import annotations

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from scripts import ocelot_research_provenance as provenance  # noqa: E402


def test_seed_claim_is_rechecked_and_caveat_is_preserved(monkeypatch):
    from scripts import seed_claim
    monkeypatch.setattr(seed_claim, "claim_report", lambda lo, hi, **kwargs: {
        "range": [lo, hi], "clean": True, "unresolved_sinks_in_tree": 12,
    })
    result = provenance.verify_seed_claim("SEED CLAIM 10-20: CLEAN")
    assert result["verified"]
    assert result["status"] == "current_match"
    assert "cannot establish historical" in result["limitation"]


def test_seed_claim_missing_conflicting_and_duplicate_verdicts(monkeypatch):
    assert provenance.verify_seed_claim("no claim")["status"] == "missing"
    duplicate = provenance.verify_seed_claim("SEED CLAIM 1-2: CLEAN\nSEED CLAIM 3-4: CLEAN")
    assert duplicate["status"] == "ambiguous"
    from scripts import seed_claim
    monkeypatch.setattr(seed_claim, "claim_report", lambda lo, hi, **kwargs: {"clean": False})
    conflict = provenance.verify_seed_claim("SEED CLAIM 1-2: CLEAN")
    assert conflict["status"] == "stale_or_conflict"
    assert not conflict["verified"]


def test_prereg_inspection_rejects_path_escape(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("SEED CLAIM 1-2: CLEAN", encoding="utf-8")
    result = provenance.verify_prereg(outside, repo_root=root)
    assert result["status"] == "unsafe_path"
    assert not result["verified"]


def test_engine_check_separates_current_verification_from_recorded_match(monkeypatch):
    from domains import engine_provenance
    current = {"sha256": "abc", "source_match": "shared", "stale_rust": [],
               "native_path": "/native.so"}
    monkeypatch.setattr(engine_provenance, "engine_provenance", lambda tree: current)
    good = provenance.verify_engine_provenance({"sha256": "abc", "source_match": "shared"})
    assert good["verified"] and good["matches_recorded"]
    changed = provenance.verify_engine_provenance({"sha256": "old", "source_match": "shared"})
    assert changed["verified"] and not changed["matches_recorded"]
    assert "past run" in changed["limitation"]
    missing = provenance.verify_engine_provenance({"source_match": "shared"})
    assert not missing["matches_recorded"]


def test_unverifiable_engine_does_not_pass(monkeypatch):
    from domains import engine_provenance
    monkeypatch.setattr(engine_provenance, "engine_provenance", lambda tree: {
        "source_match": "unknown", "stale_rust": [], "sha256": "x"})
    result = provenance.verify_engine_provenance()
    assert result["status"] == "unverified"
    assert not result["verified"]


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def test_prereg_git_verifies_committed_blob_and_reports_worktree_state(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "Test")
    prereg = repo / "docs" / "trial.md"
    prereg.parent.mkdir()
    prereg.write_bytes(b"prospective protocol\n")
    _git(repo, "add", "docs/trial.md")
    _git(repo, "commit", "-q", "-m", "preregister")
    oid = _git(repo, "rev-parse", "HEAD")

    result = provenance.verify_prereg_git(repo, oid, "docs/trial.md")
    assert result["status"] == "current_matches_commit"
    assert result["verified"] and result["working_matches_commit"]
    assert len(result["committed_sha256"]) == 64
    assert result["timestamp_is_assertion"]

    prereg.write_bytes(b"edited after registration\n")
    changed = provenance.verify_prereg_git(repo, oid, "docs/trial.md")
    assert changed["status"] == "working_copy_differs"
    assert changed["verified"] and not changed["working_matches_commit"]


def test_prereg_git_rejects_injected_or_short_identifiers(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    short = provenance.verify_prereg_git(repo, "deadbeef", "docs/trial.md")
    assert short["status"] == "invalid_commit"
    option = provenance.verify_prereg_git(repo, "a" * 40, "--upload-pack=evil")
    assert option["status"] == "invalid_path"
    traversal = provenance.verify_prereg_git(repo, "a" * 40, "../secret")
    assert traversal["status"] == "invalid_path"
