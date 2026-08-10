"""tests/test_mbpp_contamination_migrated.py — Arc 2 Q0 THE LIST-GATE.

provenance.json's binding rule: test-split (task_id in [11,510]) prompt
text and reference code must never enter any codebook, cue vocabulary,
bigram table, or taught shape. This gate scans every codebook-bearing
seed + results artifact currently on disk for any (normalized) test-split
prompt substring or code-field line, and proves — via a self-test that
deliberately injects a test-split substring into a tmp file — that the
scan actually BITES rather than vacuously passing.

Scope note: `results/mbpp_zero_shot_baseline.json` (this track's own eval
log) and `results/mbpp_blocker_histogram.json` (the sibling Q0-B track's
artifact) are DELIBERATELY EXCLUDED from SCAN_TARGETS — an eval log
legitimately records which prompt was tested and what happened; that is
not a codebook, cue vocabulary, bigram table, or taught shape, and
recording it is the whole point of a baseline artifact. The contamination
rule targets the LEARNING path, not the measurement log (this file, and
this file reading the test-split `code` field to build the forbidden-
substring list, is the audit tool itself, not the runner the rule binds —
`tests/fixtures/mbpp/provenance.json`'s wording: "no LEARNING path" ever
reads test code; an audit script proving that is not a learning path).

Runtime: PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
OZMA_SEED_PERSIST_DISABLED=1 pytest --confcutdir=. tests/test_mbpp_contamination_migrated.py
"""
from __future__ import annotations

import json
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE_PATH = os.path.join(ROOT, "tests", "fixtures", "mbpp", "sanitized-mbpp.json")

# Every codebook-bearing seed / results artifact the write-request / synth
# pipeline actually reads INTO the agent's proposal machinery
# (ensure_program_synthesis, ensure_construction_bigrams, install_mined_
# chunks, ensure_write_codebook, the cue Concepts) — the surfaces
# provenance.json's rule protects. Paths that don't exist are skipped
# (recorded, never silently "passing" by omission — see
# test_every_scan_target_exists_or_is_explicitly_absent).
SCAN_TARGETS = (
    "seeds/code_write_constructions.json",
    "seeds/code_write_gap.json",
    "seeds/code_write_request_cues.json",
    "seeds/prog_chunk_growth.json",
    "seeds/program_synthesis.json",
    "seeds/compositional_chunking.json",
    "results/prog_chunk_mine.json",
    "results/prog_construction_scan.json",
    "results/code_synthesis_baseline.json",
)

_WS_RE = re.compile(r"\s+")
_MIN_PROMPT_LEN = 20      # avoid trivial short-substring false positives
_MIN_CODE_LINE_LEN = 15


def _normalize(s: str) -> str:
    return _WS_RE.sub(" ", s.strip().lower())


def _forbidden_substrings() -> list[str]:
    """Normalized test-split prompts (whole prompt, >= _MIN_PROMPT_LEN) +
    normalized individual code lines (>= _MIN_CODE_LINE_LEN) — the ONLY
    place in this repo's test suite that reads a test-split `code` field,
    and it does so as the AUDIT tool, never as a learning path."""
    with open(FIXTURE_PATH) as f:
        tasks = json.load(f)
    test_tasks = [t for t in tasks if 11 <= t["task_id"] <= 510]
    forbidden: list[str] = []
    for t in test_tasks:
        p = _normalize(t["prompt"])
        if len(p) >= _MIN_PROMPT_LEN:
            forbidden.append(p)
        for line in t["code"].splitlines():
            nl = _normalize(line)
            if len(nl) >= _MIN_CODE_LINE_LEN:
                forbidden.append(nl)
    return forbidden


def scan_for_contamination(paths: list[str], forbidden: list[str]) -> list[dict]:
    """Mechanical scan: for each existing path, normalize its raw text the
    same way, and report every forbidden substring found inside it. Pure
    function — no decision, just detection; returns a LIST of hits (a
    baseline is a list), empty when clean."""
    hits: list[dict] = []
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path, "r", errors="replace") as f:
            raw = f.read()
        norm = _normalize(raw)
        for sub in forbidden:
            if sub in norm:
                hits.append({"path": path, "substring": sub[:120]})
    return hits


@pytest.fixture(scope="module")
def forbidden():
    return _forbidden_substrings()


# --------------------------------------------------------------------------- #
#  the gate itself
# --------------------------------------------------------------------------- #
def test_forbidden_substring_list_is_nonempty(forbidden):
    # sanity: the detector has something to look for (257 test tasks).
    assert len(forbidden) > 200


def test_every_scan_target_exists_or_is_explicitly_absent():
    missing = [p for p in SCAN_TARGETS if not os.path.exists(os.path.join(ROOT, p))]
    present = [p for p in SCAN_TARGETS if os.path.exists(os.path.join(ROOT, p))]
    # at least the core write-codebook + chunk artifacts must be present —
    # an all-missing target list would make the gate vacuous.
    assert len(present) >= 6, (
        "too many scan targets missing (%r) — the gate would be nearly "
        "vacuous; update SCAN_TARGETS or investigate" % missing)


def test_no_test_split_contamination_in_codebook_bearing_artifacts(forbidden):
    paths = [os.path.join(ROOT, p) for p in SCAN_TARGETS]
    hits = scan_for_contamination(paths, forbidden)
    assert hits == [], (
        "MBPP test-split content found in a codebook-bearing seed/results "
        "artifact — contamination: %r" % hits[:10])


def test_own_eval_artifact_is_deliberately_excluded_from_scan_targets():
    """The eval log legitimately contains test-split prompts (that's the
    whole point of a per-task baseline row) — it must never be scanned as
    if it were a codebook. Documents the exclusion is deliberate, not an
    oversight."""
    assert "results/mbpp_zero_shot_baseline.json" not in SCAN_TARGETS
    assert "results/mbpp_blocker_histogram.json" not in SCAN_TARGETS


# --------------------------------------------------------------------------- #
#  the self-test — proves the gate BITES (never a vacuous pass).
# --------------------------------------------------------------------------- #
def test_gate_detects_an_injected_test_split_prompt(tmp_path, forbidden):
    injected = forbidden[0]
    fake_seed = tmp_path / "fake_codebook.json"
    fake_seed.write_text(json.dumps({
        "nodes": [{"type": "ShapeSignature",
                   "attrs": {"name": "leaked", "kind": "code_write_construction",
                             "trigger_note": "the quick brown fox " + injected}}]
    }))
    hits = scan_for_contamination([str(fake_seed)], forbidden)
    assert len(hits) >= 1
    assert hits[0]["path"] == str(fake_seed)


def test_gate_detects_an_injected_code_line(tmp_path, forbidden):
    with open(FIXTURE_PATH) as f:
        tasks = json.load(f)
    t = next(t for t in tasks if 11 <= t["task_id"] <= 510)
    line = next(ln for ln in t["code"].splitlines()
                if len(_normalize(ln)) >= _MIN_CODE_LINE_LEN)
    fake = tmp_path / "fake_taught_shape.json"
    fake.write_text("some header text\n" + line + "\nsome trailer text\n")
    hits = scan_for_contamination([str(fake)], forbidden)
    assert len(hits) >= 1


def test_gate_reports_clean_on_a_genuinely_unrelated_file(tmp_path, forbidden):
    clean = tmp_path / "unrelated.json"
    clean.write_text(json.dumps({"nodes": [{"type": "Concept", "attrs": {
        "name": "gratitude", "domain": "psychology"}}]}))
    hits = scan_for_contamination([str(clean)], forbidden)
    assert hits == []
