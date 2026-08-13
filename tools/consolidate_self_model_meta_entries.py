"""One-shot migration: move `domains/comprehend_question._SELF_MODEL_META_ENTRIES`
(3 hand-written Python rows) INTO `seeds/question_targets.json`'s `meta_targets`
list, where the other 76 meta-target rows already live.

SHAPE_AUDIT.md §7 finding #10 / instance 1: this Python list existed ONLY
because, at the time it was added, `seeds/question_targets.json` was declared
"outside this task's editable-file set" -- a scoping constraint, not a
structural one. That constraint no longer applies. Moving the data removes
one of the enumeration's four copies outright (comprehend_question.py no
longer special-cases a Python-appended tail in `load_meta_lexicon`), rather
than leaving the seed and the Python list to drift against each other by
hand.

Content is copied VERBATIM (same meta_target/faculty/match/self_cue_optional/
arg_between values) -- this is a location move, not a data change, so
`comprehend_meta`'s behaviour for these three shapes is unchanged.
"""
from __future__ import annotations

import json
from pathlib import Path

SEED_PATH = Path(__file__).resolve().parent.parent / "seeds" / "question_targets.json"

# Copied verbatim from the (now-deleted) domains/comprehend_question.py
# `_SELF_MODEL_META_ENTRIES`.
_SELF_MODEL_ROWS = [
    {"meta_target": "self_model_rule", "faculty": "self_model",
     "match": ["what", "does", "do"], "self_cue_optional": True,
     "arg_between": {"start": ["does"], "end": ["do"]}},
    {"meta_target": "self_model_topic", "faculty": "self_model",
     "match": ["which", "rules", "about"], "arg_after": ["about"]},
    {"meta_target": "self_model_touches", "faculty": "self_model",
     "match": ["which", "parts", "touch"], "arg_after": ["touch"]},
]


def main() -> None:
    data = json.loads(SEED_PATH.read_text())
    existing = {(e["meta_target"], tuple(e.get("match") or [])) for e in data["meta_targets"]}
    added = 0
    for row in _SELF_MODEL_ROWS:
        key = (row["meta_target"], tuple(row.get("match") or []))
        if key in existing:
            continue
        data["meta_targets"].append(row)
        added += 1
    text = json.dumps(data, indent=1, ensure_ascii=True)
    SEED_PATH.write_text(text + "\n")
    print(f"Added {added} self-model meta-target rows to {SEED_PATH} "
          f"(now {len(data['meta_targets'])} total).")


if __name__ == "__main__":
    main()
