from pathlib import Path

import pytest

from scripts.ocelot_research_sources import (
    RootManifest, SourceError, build_index, open_locator, retrieve,
)


def _repo(tmp_path: Path, root_id: str, filename: str, content: str) -> Path:
    root = tmp_path / root_id
    root.mkdir()
    (root / filename).parent.mkdir(parents=True, exist_ok=True)
    (root / filename).write_text(content, encoding="utf-8")
    return root


def test_two_explicit_roots_index_and_retrieve_citations(tmp_path):
    a = _repo(tmp_path, "ocelot", "guide.md", "# Science\nIndependent controls matter.\n")
    b = _repo(tmp_path, "ge", "ledger.md", "# Claims\nResidual CNF is hard.\n")
    idx = build_index([
        RootManifest("ocelot", a, ["guide.md"]),
        RootManifest("ge", b, ["ledger.md"]),
    ])
    answer = retrieve(idx, "residual CNF", limit=4)
    assert len(answer["results"]) == 1
    result = answer["results"][0]
    assert result["citation"]["root_id"] == "ge"
    assert result["citation"]["path"] == "ledger.md"
    assert result["support_edges"] == []
    assert result["freshness"] == "current"
    assert open_locator(idx, result["citation"])["text"].startswith("# Claims")


def test_dirty_and_changed_source_are_reported_stale(tmp_path):
    root = _repo(tmp_path, "repo", "note.md", "# Finding\nA bounded finding.\n")
    idx = build_index([RootManifest("r", root, ["note.md"])])
    locator = idx["passages"][0]
    (root / "note.md").write_text("# Finding\nA changed finding.\n", encoding="utf-8")
    assert open_locator(idx, locator)["status"] == "stale"
    result = retrieve(idx, "bounded finding")
    assert result["results"][0]["freshness"] == "stale"


def test_missing_files_are_coverage_gaps_and_reopen_unavailable(tmp_path):
    root = _repo(tmp_path, "repo", "present.md", "# Present\nText.\n")
    idx = build_index([RootManifest("r", root, ["present.md", "moved.md"])])
    assert idx["coverage"][-1] == {"root_id": "r", "path": "moved.md", "status": "missing"}
    (root / "present.md").unlink()
    assert open_locator(idx, idx["passages"][0])["status"] == "unavailable"


@pytest.mark.parametrize("bad", ["../outside.md", "/etc/passwd"])
def test_rejects_traversal_and_absolute_paths(tmp_path, bad):
    root = _repo(tmp_path, "repo", "ok.md", "# ok\n")
    with pytest.raises(SourceError):
        build_index([RootManifest("r", root, [bad])])


def test_rejects_symlink_escape_for_index_and_locator(tmp_path):
    root = _repo(tmp_path, "repo", "ok.md", "# ok\n")
    outside = _repo(tmp_path, "outside", "secret.md", "# secret\n")
    (root / "escape.md").symlink_to(outside / "secret.md")
    with pytest.raises(SourceError):
        build_index([RootManifest("r", root, ["escape.md"])])


def test_no_selected_match_has_reason_and_empty_results(tmp_path):
    root = _repo(tmp_path, "repo", "ok.md", "# Local\nResearch guide.\n")
    result = retrieve(build_index([RootManifest("r", root, ["ok.md"])]), "quantum")
    assert not result["results"]
    assert result["reason"]



def test_locator_cannot_read_unselected_file_and_hashes_exact_bytes(tmp_path):
    import hashlib
    from scripts.ocelot_research_sources import build_index, retrieve, open_locator
    (tmp_path / 'selected.md').write_bytes(b'# Heading\r\nEvidence\r\n')
    (tmp_path / 'private.md').write_text('secret', encoding='utf-8')
    index = build_index([{'root_id': 'r', 'path': str(tmp_path), 'files': ['selected.md']}])
    locator = retrieve(index, 'evidence')['results'][0]['citation']
    assert locator['sha256'] == hashlib.sha256(b'# Heading\r\nEvidence\r\n').hexdigest()
    assert open_locator(index, {**locator, 'path': 'private.md'})['status'] == 'unavailable'
