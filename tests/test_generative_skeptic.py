"""Tests for domains/generative_skeptic.py and seeds/generative_skeptic.json (P1.H7.3)."""
from __future__ import annotations

import json
from pathlib import Path

from domains.generative_skeptic import (
    generate_probe,
    harvest_failure_shapes,
    match_failure_shapes,
)
from substrate_rs import Substrate

ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "seeds" / "generative_skeptic.json"


def _install_failure_lessons(s: Substrate) -> int:
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    mt = s.add_node(
        "Microtheory",
        {"name": seed["microtheory"]["name"], "origin": "generative_skeptic"},
    )
    try:
        s.add_production(
            {
                "src": {"type": "Microtheory", "var": "a"},
                "edge_type": "has_lesson",
                "tgt": {"type": "FailureLesson", "var": "b"},
                "provenance": "generative_skeptic:has_lesson",
            }
        )
    except Exception:
        pass
    count = 0
    for c in seed.get("concepts", ()):
        attrs = {k: v for k, v in c.items() if k != "node_type"}
        attrs["origin"] = "generative_skeptic"
        nid = s.add_node("FailureLesson", attrs)
        try:
            s.add_edge(mt, "has_lesson", nid)
        except Exception:
            pass
        count += 1
    return count


def test_generative_skeptic_harvest_match_and_novel_residual():
    s = Substrate()
    installed = _install_failure_lessons(s)
    assert installed == 6

    shapes = harvest_failure_shapes(s)
    assert len(shapes) == 6

    matched = match_failure_shapes(shapes, "fusion matches OLD baseline")
    matched_names = {sh["failure_shape"] for sh in matched}
    assert any("baseline" in name or "old" in name for name in matched_names)

    probe = generate_probe(
        s,
        "The Dvorak keyboard layout reduces finger travel distance for English text relative to QWERTY by rearranging the home row.",
    )
    assert probe["matched"] is False
    assert probe["residual"] == "novel_failure_no_matching_shape"
