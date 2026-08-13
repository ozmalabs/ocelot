"""SHAPE_AUDIT.md §7 finding #10: the meta-target enumeration used to live in
four copies (seeds/question_targets.json's `meta_targets`, the Python
`_META_LEXICON_FALLBACK`, the Python `_SELF_MODEL_META_ENTRIES`, and
`reflective_faculty._DISPATCH`) with nothing enforcing agreement between them
-- and it had already drifted (measured: 2 "orphaned seed targets", 8
"orphaned handlers", by a STATIC grep over `reflective_faculty.py` alone).

Two things landed for this rung:

1. `_SELF_MODEL_META_ENTRIES` was moved INTO seeds/question_targets.json
   (tools/consolidate_self_model_meta_entries.py) -- one fewer copy.
2. This test replaces the audit's static grep with the LIVE `_DISPATCH`
   (after the same module-import chain `substrate/boot_all.py` performs),
   because the static grep undercounted: `code_capabilities` and
   `emitter_roadmap` (the audit's "2 orphaned seed targets") in fact DO have
   real handlers -- registered via `.setdefault()` calls in
   `domains/code_curriculum.py` / `domains/curriculum_study.py` at import
   time, invisible to a regex over `reflective_faculty.py`'s own dict
   literal + local `.setdefault` calls. That was a measurement artifact of
   the audit's OWN method (a "grep-shaped blind spot", per SHAPE_AUDIT.md
   §9.3), not real drift -- confirmed here by actually importing the chain
   and reading `_DISPATCH`, not by grepping source text.

This test is the "make one copy the source and derive the others" fix
§7 itself names: every seed `meta_target` MUST have a live `_DISPATCH`
handler (a real drift-guard -- a seed row with no handler means a real
question could match and land on `reflect()`'s honest-unwired floor
instead of a working faculty), and the SET of handlers with no seed row is
pinned EXACTLY to the ones already known to be reachable some other way, so
a newly-added handler that forgets its seed row (or its documented
alternate route) fails this test instead of silently drifting further.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _live_dispatch_keys() -> set[str]:
    # Import the modules that register handlers into _DISPATCH via
    # module-level .setdefault() calls, mirroring what substrate/boot_all.py
    # pulls in during a real boot -- the same reason the audit's static grep
    # (source text only, no imports) missed them.
    import domains.reflective_faculty as rf
    import domains.code_curriculum       # noqa: F401 -- registers code_capabilities
    import domains.curriculum_study      # noqa: F401 -- registers emitter_roadmap
    import domains.self_model            # noqa: F401 -- registers self_model_*
    return set(rf._DISPATCH.keys())


def _seed_meta_targets() -> set[str]:
    seed_path = Path(__file__).resolve().parent.parent / "seeds" / "question_targets.json"
    data = json.loads(seed_path.read_text())
    return {e["meta_target"] for e in data["meta_targets"]}


# Handlers reachable via a route OTHER than seeds/question_targets.json's
# `meta_targets` lexicon, each with its own cited alternate route -- named
# explicitly (SHAPE_AUDIT.md's own "named, not silently tolerated" standard)
# rather than left as an unexplained gap a future reader has to re-derive:
#
#   self_kind         -- substrate/world_adapter.py sets meta_target="self_kind"
#                         directly (a dedicated non-lexicon dispatch path).
#   self_process       -- domains/comprehend_text.py:~1131 sets
#                         meta_target="self_process" directly (operational
#                         self-introspection, a held SelfProcess account).
#   self_modification  -- reachable via domains/conversation_action.py's
#                         imperative-mood `_SELF_TARGET_KW` route (a genuinely
#                         different grammatical mood: "describe your
#                         modifications" vs a question), not the question
#                         lexicon. Also called directly from scripts/tests.
#   reading_trace       -- Phase-1 introspection slice (see
#                         tests/test_reading_introspection_migrated.py's own
#                         docstring): a real, tested faculty with NO current
#                         NL question route. A named residual, not fixed here
#                         -- inventing a trigger phrase risks colliding with
#                         an existing target and was judged out of this
#                         rung's scope.
#   referent_trace      -- same shape as reading_trace (see
#                         scripts/ask_jabberwock_wretch.py's direct
#                         rf.reflect("referent_trace", ...) usage).
_HANDLERS_WITHOUT_SEED_ROW = {
    "self_kind", "self_process", "self_modification",
    "reading_trace", "referent_trace",
}


def test_every_seed_meta_target_has_a_live_dispatch_handler():
    """No seed row should route a real question to reflect()'s honest-unwired
    floor. This is the direction that actually matters (a phrase a user can
    type resolving to 'not wired' instead of an answer) -- the audit's
    'orphaned seed target' claim, corrected: zero today, pinned here."""
    seed_targets = _seed_meta_targets()
    dispatch_keys = _live_dispatch_keys()
    missing = seed_targets - dispatch_keys
    assert not missing, (
        f"seed meta_target(s) with no live _DISPATCH handler: {sorted(missing)} "
        "-- a real question could match this seed row and land on reflect()'s "
        "honest-unwired floor instead of a working faculty.")


def test_handlers_without_a_seed_row_are_exactly_the_documented_set():
    """A handler with no seed row is not itself wrong (self_kind/self_process
    are intentionally routed outside the lexicon; the trace faculties are a
    named Phase-1 gap) -- but a NEW one appearing without a seed row OR an
    entry in the documented allowlist above is exactly how this drifted the
    first time. Pins today's set exactly, both directions."""
    seed_targets = _seed_meta_targets()
    dispatch_keys = _live_dispatch_keys()
    orphaned = dispatch_keys - seed_targets
    assert orphaned == _HANDLERS_WITHOUT_SEED_ROW, (
        f"handlers without a seed row changed: now {sorted(orphaned)}, "
        f"documented set is {sorted(_HANDLERS_WITHOUT_SEED_ROW)}. "
        "If you added a new meta_target handler, either add its seed row to "
        "seeds/question_targets.json OR add it to _HANDLERS_WITHOUT_SEED_ROW "
        "above with a cited alternate route -- don't let it drift silently.")


def test_self_model_meta_entries_are_seed_resident_not_a_python_copy():
    """SHAPE_AUDIT.md §7 instance 1: self_model_rule/topic/touches used to be
    a Python list ALWAYS appended in domains/comprehend_question.py. Now they
    are ordinary rows in the one seed file, alongside the other 79."""
    import domains.comprehend_question as cq
    assert not hasattr(cq, "_SELF_MODEL_META_ENTRIES"), (
        "the Python self-model meta-entries list should be gone -- moved "
        "into seeds/question_targets.json")
    seed_targets = _seed_meta_targets()
    for tgt in ("self_model_rule", "self_model_topic", "self_model_touches"):
        assert tgt in seed_targets, f"{tgt} missing from seeds/question_targets.json"


def test_comprehend_meta_and_best_meta_entry_share_one_scorer():
    """SHAPE_AUDIT.md §7 instance 3: `_score_meta_entry`/`_best_meta_entry`
    used to be duplicated byte-for-byte in domains/comprehend_text.py. Now
    comprehend_text re-exports comprehend_question's implementation -- one
    copy, not two kept in sync by hand. (The two SELECTION semantics,
    first-match vs best-covered, are deliberately left unmerged -- see the
    docstring on comprehend_question._best_meta_entry for why.)"""
    import domains.comprehend_question as cq
    import domains.comprehend_text as ct
    assert ct._score_meta_entry is cq._score_meta_entry
    assert ct._best_meta_entry is cq._best_meta_entry


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
