"""Low-residency lemma membership matches NLTK's WordNet morphology."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from domains import wordnet_membership as membership


def _write_wordnet_fixture(root: Path) -> None:
    for name in membership._INDEX_FILES:
        (root / name).write_text("", encoding="utf-8")
    for name in membership._EXCEPTION_FILES:
        (root / name).write_text("", encoding="utf-8")
    (root / "index.noun").write_text(
        "dog n 1 1 @ 1 1 00000001\n"
        "mouse n 1 1 @ 1 1 00000002\n",
        encoding="utf-8",
    )
    (root / "index.verb").write_text(
        "walk v 1 1 @ 1 1 00000003\n"
        "report v 1 1 @ 1 1 00000004\n",
        encoding="utf-8",
    )
    (root / "noun.exc").write_text("mice mouse\n", encoding="utf-8")


def test_wordnet_membership_preserves_nltk_suffix_and_exception_rules(
        tmp_path: Path, monkeypatch) -> None:
    corpus = tmp_path / "wordnet"
    corpus.mkdir()
    _write_wordnet_fixture(corpus)
    monkeypatch.setattr(membership, "_find_corpus", lambda: (corpus, False))
    monkeypatch.setattr(membership.tempfile, "gettempdir", lambda: str(tmp_path))
    membership._CONNECTIONS.clear()

    assert membership.has_synset("dog") is True
    assert membership.has_synset("dogs") is True
    assert membership.has_synset("mice") is True
    assert membership.has_synset("walked") is True
    assert membership.has_synset("xwalked") is False
    assert membership.lemmas("walked", "v") == ("walk",)
    assert membership.lemmas("reports", "v") == ("report",)
    assert membership.lemmas("mice", "n") == ("mouse",)
    assert membership.lemmas("xwalked", "v") == ()

    for connection in membership._CONNECTIONS.values():
        connection.close()
    membership._CONNECTIONS.clear()


def test_live_membership_does_not_import_nltk_package() -> None:
    code = (
        "import sys; from domains.wordnet_membership import has_synset; "
        "has_synset('weather'); assert 'nltk' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", code], check=True, cwd=Path.cwd())


def test_wordnet_membership_matches_nltk_on_live_english_forms() -> None:
    import pytest

    pytest.importorskip("nltk")
    from nltk.corpus import wordnet as wn

    try:
        wn.ensure_loaded()
    except LookupError:
        pytest.skip("NLTK WordNet corpus is not installed")

    words = """what relation seed dependency dogs dog went go better good
        kindly please pray prithee areyou weather pitcher pebbles is are was
        were running run ran children child mice mouse geese goose axes ax
        boxes box happier happy quickly qzxv can do open focus compare focused
        studies study studying studied leaves leaf knives knife teeth tooth
        looked look made make saw see fish fishes best faster fastest unknown""".split()
    assert [membership.has_synset(word) for word in words] == [
        bool(wn.synsets(word)) for word in words
    ]
