"""Phase 1 measurement for communication-event intent arbitration.

This module reads the frozen comprehension-divergence fixture and classifies
kind disagreements as evidence. It does not select a winner or change runtime
dispatch. Arbitration policy is intentionally deferred until the disagreement
classes have been measured.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import json


FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / \
    "comprehension_divergence" / "divergence.json"


def load_fixture(path: Path = FIXTURE) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return [row for row in payload.get("rows", [])
            if str(row.get("text", "")).strip()]


def disagreement_class(row: dict) -> str:
    """Classify only the shape of a kind disagreement, not its meaning."""
    comp = row.get("comp_kind")
    shadow = row.get("shadow_speech_act")
    if comp == "question" and shadow == "instruction":
        return "question_promoted_from_instruction"
    if comp == "question" and shadow == "statement":
        return "question_promoted_from_statement"
    if comp == "instruction" and shadow == "statement":
        return "instruction_promoted_from_statement"
    return f"{comp or 'missing'}_vs_{shadow or 'missing'}"


def measure(rows: list[dict] | None = None) -> dict:
    rows = load_fixture() if rows is None else list(rows)
    kind_disagreements = [row for row in rows if not row.get("agree_kind")]
    n = len(rows)
    agree = n - len(kind_disagreements)
    return {
        "rows": n,
        "kind_agree": agree,
        "kind_disagree": len(kind_disagreements),
        "kind_agreement_rate": (agree / n) if n else 0.0,
        "predicate_disagree": sum(not row.get("agree_predicate") for row in rows),
        "topic_disagree": sum(not row.get("agree_topic") for row in rows),
        "disagreement_classes": dict(Counter(
            disagreement_class(row) for row in kind_disagreements)),
        "kind_disagreement_examples": [
            {"text": row.get("text"), "class": disagreement_class(row),
             "comprehension": row.get("comp_kind"),
             "shadow": row.get("shadow_speech_act")}
            for row in kind_disagreements
        ],
    }


def markdown_report(measurement: dict | None = None) -> str:
    m = measure() if measurement is None else measurement
    lines = [
        "# Phase 1 Intent Arbitration Measurement",
        "",
        "Source: `tests/fixtures/comprehension_divergence/divergence.json`.",
        "This is an evidence report; it does not promote a winner between classifiers.",
        "",
        f"- Rows measured: **{m['rows']}**",
        f"- Kind agreement: **{m['kind_agree']}/{m['rows']} ({m['kind_agreement_rate']:.1%})**",
        f"- Kind disagreement: **{m['kind_disagree']}**",
        f"- Predicate disagreement: **{m['predicate_disagree']}**",
        f"- Topic disagreement: **{m['topic_disagree']}**",
        "",
        "## Kind disagreement classes",
        "",
    ]
    for key, value in sorted(m["disagreement_classes"].items()):
        lines.append(f"- `{key}`: {value}")
    lines += ["", "## Interpretation", "",
              "The existing corpus measures 93.8% kind agreement, below the "
              "Phase 1 target of 95%. The disagreement set must therefore be "
              "classified and resolved by cognitive policy before Phase 1 can "
              "be accepted. Predicate/topic divergence is a separate parse "
              "problem and must not be hidden inside kind arbitration."]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print(markdown_report(), end="")
