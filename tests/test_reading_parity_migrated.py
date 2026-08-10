"""test_reading_parity_migrated — the Phase-1 reading-migration PARITY GATE.

Re-runs the CURRENT reading core (domains.reading_collapse) over the frozen corpus
and asserts byte-parity against tests/fixtures/reading_parity/reading.json (dumped
by that fixture's capture.py BEFORE any slice rewrite). This is the SAME parity
method tests/test_composer_driver_migrated.py uses: the fixture is the ground truth
the graph-native rule-loop reimplementation of slices 1b–1f must match.

CROW / DEFN / CONSTRUCT groups must stay byte-identical through every slice (the
mechanical migrations 1b/1c/1f change representation, not output). The VALIDATE
group is captured as a documented BEFORE snapshot — slices 1d/1e change the bolder/
wretch parse ON PURPOSE, so its `event`/`decompose`/`read_clause` fields are NOT
asserted here (see the fixture's own note); its skeleton-level recognition is.

Regenerate the fixture (only when an intended behaviour change lands) with:
  PYTHONPATH=runners/dsl/python:.:scripts python3 \
      tests/fixtures/reading_parity/capture.py
"""
from __future__ import annotations

import importlib.util
import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "reading_parity", "reading.json")
CAPTURE_PY = os.path.join(ROOT, "tests", "fixtures", "reading_parity", "capture.py")


def _load_capture():
    spec = importlib.util.spec_from_file_location("reading_parity_capture", CAPTURE_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def frozen():
    with open(FIXTURE) as f:
        return json.load(f)["corpus"]


@pytest.fixture(scope="module")
def current():
    cap = _load_capture()
    from domains import dictionary_lexicon as dl
    dl.warm_wordnet("en")
    out: dict = {}
    for group, sentences in cap.CORPUS.items():
        ag = cap.fresh_agent()
        recs = []
        for s in sentences:
            if not s.strip():
                continue
            recs.append(cap.capture_sentence(ag, s))
        out[group] = recs
    return out


# fields that slices 1d/1e intentionally change for the VALIDATE group — excluded
# from the VALIDATE byte-parity assertion (recognition-level fields are still gated).
_VALIDATE_MUTABLE = {"event", "event_for_sentence", "decompose", "read_clause", "heads"}


@pytest.mark.parametrize("group", ["CROW", "DEFN", "CONSTRUCT"])
def test_reading_byte_parity_stable_groups(group, frozen, current):
    """CROW / DEFN / CONSTRUCT — byte-identical output through every slice."""
    assert current[group] == frozen[group], (
        f"reading parity drift in group {group!r} — a slice changed a mechanical "
        f"migration's output; re-run capture.py only if the change is intended")


def test_reading_validate_recognition_stable(frozen, current):
    """VALIDATE — the skeleton/recognition-level fields stay stable even while
    1d/1e change the grounded event/decompose (captured as a BEFORE snapshot)."""
    for cur_rec, fx_rec in zip(current["VALIDATE"], frozen["VALIDATE"]):
        for k in ("sentence", "recognised_words", "skeleton", "roles", "marker_seq"):
            assert cur_rec.get(k) == fx_rec.get(k), (cur_rec["sentence"], k)


def test_reading_corpus_byte_parity(frozen, current):
    """CORPUS — the WHOLE Aesop+Grimm event-grounding oracle. Every event/decompose/
    read_clause/heads field over real prose must stay byte-identical through the
    event-grounding migration (this is the safety net _event_predication's graph-
    native replacement is measured against). Skips when the corpus isn't cached."""
    frozen_corpus = frozen.get("CORPUS") or []
    current_corpus = current.get("CORPUS") or []
    if not frozen_corpus or not current_corpus:
        pytest.skip("Aesop+Grimm corpus not cached — CORPUS oracle unavailable")
    assert len(current_corpus) == len(frozen_corpus), (
        f"corpus sentence count drift: {len(current_corpus)} vs {len(frozen_corpus)}")
    for cur_rec, fx_rec in zip(current_corpus, frozen_corpus):
        assert cur_rec == fx_rec, (
            f"event-grounding drift on sentence: {fx_rec.get('sentence')!r}")
