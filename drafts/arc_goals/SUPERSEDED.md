# `drafts/arc_goals/` — SUPERSEDED 2026-08-04, phase 2 landed

Phase 1 (design only, nothing wired) scaffolded the seed and the gate here
deliberately, because `substrate/boot_all.py::_read_seeds` **globs
`seeds/*.json`** and installs every match at boot.

Phase 2 has landed and the two files are **removed rather than left behind**:

| phase 1 draft | phase 2 |
|---|---|
| `arc_goals.draft.json` | `seeds/arc_goals.json` — **emitted** by `tools/build_arc_goals_seed.py`, gated byte-identical, and still `self_load_only` so it is not globbed into every agent in the tree |
| `test_arc_goals_draft.py` | `tests/test_arc_goals_migrated.py` — 37 live gates, no module skip, no xfails |

**Why removed and not kept as a record.**  The shipped seed DIVERGED from the
draft during the build (the selector was split into a guard chain; `ag_revocab`
gained a null coalesce after a measured engine hazard; two mint sources and
five rules were added).  An inert, divergent copy of a live seed is exactly the
thing that misleads a later reader into editing the wrong file — and it
carries `self_load_only`, so nothing would tell them.  The design record lives
in `PROGRAM_SYNTHESIS_ARC6_ARC_GOALS_DESIGN.md`; the results and everything
that broke live in `PROGRAM_SYNTHESIS_ARC6_ARC_GOALS.md`.
