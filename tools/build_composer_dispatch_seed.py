"""Regenerate seeds/composer_dispatch.json's ComposerCue priorities from an
EXPLICIT, DECLARED composer ladder instead of raw per-row insertion order.

SHAPE_AUDIT.md §2.3 / §8 #8: the held `priority` on each ComposerCue row was
the literal insertion index (1..23, one duplicate, no gaps) -- "the priority
is the order the rows were added." Read carefully, the row-level scheme was
worse than that headline: a single composer's OWN relation_head family was
interleaved with unrelated composers as they accreted (`experiment`'s rows
sit at priorities 8, 9, 10, 11, 13, 15, 16 -- 'browse' and 'attention' were
inserted in between), so a concern that grounds two different verbs of the
SAME composer could resolve to two DIFFERENT effective ranks depending on
which verb happened to fire, even though externally it is the same composer
decision either way. That is the accidental inconsistency this script
removes.

THE FIX: `priority` is derived, not asserted -- it is one plus the index of
the row's `composer` in the explicit `_COMPOSER_LADDER` list below. Every
row belonging to the same composer now gets the SAME priority (ties between
them are behaviourally inert: Argmin's `Attr(key="composer", ...)` reads the
same `composer` string off whichever tied row wins). Cross-composer ordering
is UNCHANGED from today's behaviour for every case that matters: each
composer's ladder position is exactly the rank of that composer's OWN
best (lowest) existing per-row priority -- which was already monotonically
increasing in row-accretion order, so this script reproduces every existing
pairwise composer-vs-composer decision. The only cases it changes are the
buggy verb-dependent ones described above (now deterministic per composer,
as they always should have been).

Adding a new VERB to an EXISTING composer no longer needs a manual "next
integer" (it inherits the composer's ladder position for free). Adding a
genuinely NEW composer still requires one explicit decision: where does it
go in `_COMPOSER_LADDER`. That is the real, irreducible content of "which
composer wins a tie" -- CLAUDE.md's own `escalation_rungs.json` precedent
(a declared ladder with a frame, not an asserted ordinal) is the shape this
now matches, one grain over.
"""
from __future__ import annotations

import json
from pathlib import Path

SEED_PATH = Path(__file__).resolve().parent.parent / "seeds" / "composer_dispatch.json"

# The declared ladder, in the SAME order the composers first accreted (see
# the seed's own `description` field for the per-extension narrative this
# preserves). Position in this list IS the composer's priority rank
# (1-indexed) -- the single place a future composer addition is decided.
_COMPOSER_LADDER = [
    "comprehension",
    "decision",
    "grouping",
    "control",
    "communicate",
    "construction",
    "distributional",
    "experiment",
    "browse",
    "attention",
    "grounding_guard",
    "escalation_gate",
    "imagination",
    "collapse_watch",
    "self_correct",
    "system_model",
    "audience_produce",
]


def derive_priorities(data: dict) -> dict:
    ladder_rank = {name: i + 1 for i, name in enumerate(_COMPOSER_LADDER)}
    seen_composers = set()
    for node in data["nodes"]:
        if node["type"] != "ComposerCue":
            continue
        composer = node["attrs"]["composer"]
        seen_composers.add(composer)
        if composer not in ladder_rank:
            raise ValueError(
                f"ComposerCue composer {composer!r} is not in _COMPOSER_LADDER -- "
                "add it explicitly (a real decision, not an auto-incremented int)."
            )
        node["attrs"]["priority"] = ladder_rank[composer]
    missing = set(_COMPOSER_LADDER) - seen_composers
    if missing:
        raise ValueError(f"_COMPOSER_LADDER names composers absent from the seed: {missing}")
    return data


def main() -> None:
    data = json.loads(SEED_PATH.read_text())
    data = derive_priorities(data)
    # Preserve the file's existing formatting convention: 1-space indent,
    # UTF-8 (non-ASCII passthrough), trailing newline.
    text = json.dumps(data, indent=1, ensure_ascii=False)
    SEED_PATH.write_text(text + "\n")
    print(f"Wrote derived priorities for {len(_COMPOSER_LADDER)} composers to {SEED_PATH}")


if __name__ == "__main__":
    main()
