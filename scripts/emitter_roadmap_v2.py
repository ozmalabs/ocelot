"""emitter_roadmap_v2 — WHOLE-CURRICULUM WAVE 2, PART A.2: the FEATURE-GRAIN
demand roadmap.

Wave 1's `emitter_roadmap` (domains/curriculum_study.py) ranks open
`code_write`/`code_read` `SelfConcern` gaps VERBATIM -- one row per distinct
un-resolved request sentence, ranked by how many lessons it blocked. That is
the right INSTANCE-grain signal (it drove the classifier fix in part A.1),
but it does not say WHICH EMITTER CAPABILITY would close the most demand at
once. This script re-aggregates the SAME held gaps at FEATURE grain: for
every gap whose content is a genuine exercise request (`code_writing.
looks_like_write_request`'s WAVE-2 tightened classifier -- prose-bullet false
positives are excluded mechanically, not by re-litigating each one by hand),
a FIXED, mechanical keyword scan tags which code FEATURE(S) the request
requires (branching-return, recursion, calls a previously-read user
function, a string operation, a loop/accumulate, a list operation, or one of
the OUT-OF-SCOPE-EXTERNAL world-I/O features: turtle/drawing, interactive
input, file I/O) -- never a semantic decision about what the function DOES,
only a text-shape scan over its OWN request sentence (the same status
`code_reading._root_marker` / `ast_to_term`'s fixed AST-node-type map already
have: one fixed table, applied uniformly, not a per-exercise judgement call).

This is a ONE-OFF ANALYSIS / REPORTING TOOL (CLAUDE.md's `tools/*` carve-out:
"one-off authoring/capture scripts that EMIT ... manifests; deletable; not
agent runtime") -- it reads a checkpoint, ranks a report, and writes a JSON
file. It makes no agent decision and is never imported by agent runtime code.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 \
     scripts/emitter_roadmap_v2.py [--ckpt-path results/curriculum_study/checkpoint.json] \
     [--out results/curriculum_study/emitter_roadmap_v2.json]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

from domains import code_writing as cw          # noqa: E402


# --------------------------------------------------------------------------- #
#  FEATURE DETECTORS — a FIXED keyword table, the same status as
#  code_reading._root_marker's AST-node-class map: one row per feature, a
#  mechanical substring scan (lowercased), never a judgement about what the
#  exercise ACTUALLY needs beyond what its own request sentence names.
# --------------------------------------------------------------------------- #
_EMITTABLE_FEATURES = [
    ("branching_return", (
        "true if", "false otherwise", "true or false", "or false if",
        "true if and false", "or false the", "boolean function",
        "returns true", "chronologically",
    )),
    ("recursion", ("recursive", "recursively", "ackermann", "infinite recursion")),
    ("call_to_user_function", (
        "uses check_fermat", "uses mul_time", "using check_fermat",
        "using the list method", "uses the standard", "calling polygon",
        "calls the given function", "use it to write", "using this formula",
    )),
    ("string_op", (
        "string", "letter", "word", "anagram", "palindrome", "backward",
        "rotated", "vowel", "alphabetical",
    )),
    ("loop_accumulate", (
        "cumulative", "iteratively", "for each letter", "n times",
        "each stage",
    )),
    ("list_op", ("list", "duplicates", "sorted")),
    ("numeric_math", (
        "greatest common divisor", "power of", "estimate", "hypotenuse",
        "fermat", "prime",
    )),
]
_OUT_OF_SCOPE_EXTERNAL_FEATURES = [
    ("turtle_external", ("turtle", "draws", "grid", "circle", "rectangle", "polygon")),
    ("input_io", ("prompts the user", "input", "interactive")),
    ("file_io", ("file", ".txt", "filenames", "reads the")),
]
_ALL_FEATURES = _EMITTABLE_FEATURES + _OUT_OF_SCOPE_EXTERNAL_FEATURES
_OUT_OF_SCOPE_NAMES = {name for name, _ in _OUT_OF_SCOPE_EXTERNAL_FEATURES}


def tag_features(text: str) -> list[str]:
    """Mechanical keyword scan (lowercased substring match) -- returns every
    feature name whose keyword list has a hit in `text`. A request can (and
    usually does) name more than one feature."""
    low = text.lower()
    out = []
    for name, keywords in _ALL_FEATURES:
        if any(kw in low for kw in keywords):
            out.append(name)
    return out


def genuine_gap_reasons(report: dict, *, agent=None) -> tuple[list[dict], list[dict]]:
    """Split `report['emitter_roadmap']['reasons']` (Wave 1's verbatim gap
    rows) into (genuine, prose_fp) via the WAVE-2 tightened classifier.
    Never re-decides anything the classifier doesn't already decide."""
    reasons = report.get("emitter_roadmap", {}).get("reasons", [])
    genuine, prose_fp = [], []
    for r in reasons:
        if cw.looks_like_write_request(r["reason"], agent):
            genuine.append(r)
        else:
            prose_fp.append(r)
    return genuine, prose_fp


def build_roadmap_v2(report: dict, *, agent=None) -> dict:
    genuine, prose_fp = genuine_gap_reasons(report, agent=agent)
    feature_rows: dict[str, dict] = {}
    untagged: list[str] = []
    for r in genuine:
        feats = tag_features(r["reason"])
        if not feats:
            untagged.append(r["reason"])
            continue
        for f in feats:
            row = feature_rows.setdefault(f, {
                "feature": f,
                "scope": "out_of_scope_external" if f in _OUT_OF_SCOPE_NAMES else "emittable",
                "exercises_naming_it": 0,
                "lessons_blocked": 0,
                "examples": [],
            })
            row["exercises_naming_it"] += 1
            row["lessons_blocked"] += int(r.get("lessons_blocked", 0) or 0)
            if len(row["examples"]) < 3:
                row["examples"].append(r["reason"])
    ranked = sorted(feature_rows.values(),
                    key=lambda row: (-row["exercises_naming_it"], row["feature"]))
    return {
        "n_total_gap_reasons": len(genuine) + len(prose_fp),
        "n_genuine_exercises": len(genuine),
        "n_prose_false_positives": len(prose_fp),
        "n_genuine_untagged": len(untagged),
        "untagged_examples": untagged,
        "features": ranked,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default=os.path.join(
        ROOT, "results", "curriculum_study", "curriculum_study_report.json"))
    ap.add_argument("--out", default=os.path.join(
        ROOT, "results", "curriculum_study", "emitter_roadmap_v2.json"))
    args = ap.parse_args()

    with open(args.report) as f:
        report = json.load(f)
    roadmap_v2 = build_roadmap_v2(report, agent=None)
    with open(args.out, "w") as f:
        json.dump(roadmap_v2, f, indent=1)
    print(json.dumps(roadmap_v2, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
