# SHAPE AUDIT SWEEP 2 — PREREG

Closing the still-open items from `SHAPE_AUDIT.md` §8 ("Ranked findings").
Findings #1 (meta-shape codebook mint path), #2 (`recognise_meta_shape`
substring+alphabetical tiebreak), #3/A1-A9 (`keywords_text` family — structural
fallback wired), and #5 (`CapabilityAxis` identity) are already landed on
`main` (verified by grep/read before starting — `seeds/meta_shape_growth.json`,
`shape_decode.rs` `MetaShapeMint`/rung-2-4 comments, `domains/rule_signature.py`
imports at `reflective_faculty.py:2832,3085,3774`, and
`reflective_faculty.py:1282-1344`'s sorted-untruncated `_key_component` key).
Also independently confirmed already landed: the "below-the-line" `find_analogies`
MAC-as-verdict item (§2.4) — `domains/analogical_thinking.py` now has a real FAC
stage (`_pair_witness`, `_compute_analogy` comments "This function is now the
MAC stage only", commits `5a484b0`/`14cb457`, both ancestors of `main` tip
`76b8aea`). No sibling-rung collision: `find_analogies` work is fully merged,
not in-flight on any open branch.

`main` tip at prereg time: `76b8aea` (`git log --oneline -1 main`).

## Commitments, in priority order (audit's own consequence×confidence÷cost rank)

1. **#4 — Γ bypass ground truth.** Trace `rewrite.rs`'s `Effect::AddEdge`
   apply path (~line 1499-1512) vs `Substrate::add_edge`
   (`substrate.rs:1533`) to determine whether a rule-effect `add_edge` goes
   through `checker.check_edge`. Read-only — no Rust edits for the trace
   itself. Report yes/no with the exact code path. Given the answer, SIZE a
   fix/follow-on for the 159 seeds (not a blind edit across 159 files) —
   author `RULE_EFFECT_ADMISSIBILITY_SIZING.md` findings inline in the
   results doc rather than attempting the engine change in this rung, unless
   tracing reveals a trivially-safe, narrowly-scoped fix.
2. **#8 — `composer_dispatch.json` priority = insertion index.** Cheapest
   verified item. Replace the hand-assigned ordinal with a derived ordering
   (specificity of the `relation_head` match set, mirroring
   `sd_recognize`'s `FixedCount(AntiUnify(...))` precedent) or, if a derived
   ordering is not cleanly expressible in one rung, a principled minimal fix
   (e.g. break the duplicate, document the remaining ordinal honestly) —
   decide after reading the file.
3. **#6 — `learn_recursive_concept` (`world_adapter.py:10113`) and
   `learn_word` (`world_adapter.py:9987`) duplicate-mint on re-teach.** Fix
   both using the `_ensure_concept` (`:4308-4315`) find-or-create pattern.
   `learn_recursive_concept`'s index also needs save/restore wiring
   (currently absent from `save()`/`load()` entirely) or a switch to reading
   the already-persisted `_concepts`/`_concept_by_name` state instead of a
   private index.
4. **#7 — `interlocutor_model.py:576-583` F-16 regress.** Read
   `tests/test_interlocutor_modeling_migrated.py:325,334` (the pinning
   assertions) first to understand the actual invariant needed, then fix per
   the standing rule — replace the hand-set `1/n` + `max(0.05,...)` floor
   with the module's own `decode_shape` competition output where tractable
   in scope, or a principled minimal fix if a full sd-loop replacement is out
   of scope this rung. Also fix the `decay_k` literal fallback contradicting
   the module's own "never a Python literal" discipline at the same site if
   in scope.
5. **#10 — meta-target enumeration, 4 copies, already drifted.** Consolidate
   to one source of truth: `seeds/question_targets.json` as the canonical
   store, `_META_LEXICON_FALLBACK` / `_SELF_MODEL_META_ENTRIES` /
   `_DISPATCH` reconciled against it (add the 2 missing handlers or route
   the 2 orphaned seed targets to `comprehend_first`; add the 8 orphaned
   handlers as seed rows or explicitly document them as Python-only
   extensions). Unify `comprehend_meta`'s first-match-wins with
   `_best_meta_entry`'s best-covered-wins semantics, or document why they
   must differ, whichever the code supports without destabilizing.
6. **#9 — `information_commitment` unweighted sum.** Investigate
   `scripts/build_information_commitment_seed.py`'s `COMMIT_VALUE` formula
   and the four call-site literal sets (`teach.py`, `voice_world.py`,
   `proposal_install.py`, `fetch_dispatch.py`). Fix if a real fix (shared
   unit / weighting) is tractable without destabilizing the `ic_*` rule
   scoring; otherwise size and name the gap clearly (this is flagged in the
   brief as possibly out-of-scope for a genuine fix).
7. **Below-the-line, name/size at minimum, fix only if cheap and safe:**
   - `find_analogies` MAC-as-verdict — ALREADY FIXED on main, verify only,
     no action.
   - `sd_recognize_dim` per-observation `LatentDimension` mint (§4.4) — 3
     test files assume current per-observation behavior
     (`test_stereo_infer_migrated.py:71`, `test_time_infer_migrated.py:61`,
     `test_depth_infer_migrated.py:66`). Read them first; fix only if the
     tests can be updated deliberately without breaking their actual intent,
     else size-not-done.
   - `wire_self_extension` no marker check (§4.6,
     `world_adapter.py:8125-8135`) — likely cheap (mirror
     `_installed_seed_ids` guard pattern); attempt fix.
   - `stroke_codebook.py:82` `DEFAULT_DTW_THRESHOLD=0.15` (§6.3) — size only
     per audit's own framing (a swept, empirically-calibrated, test-pinned
     scalar; replacing it is a real research rung, not a same-day fix).

## Process

- Isolated worktree: `git worktree add --detach <path> 76b8aea`, branch
  `shape-audit-sweep2`.
- No `git stash`, ever.
- Touch Rust only if #4's fix (not trace) turns out to be in scope and safe;
  otherwise Rust stays read-only this rung.
- Regression: run the migrated bench subset relevant to every touched file
  before/after, paired failing-node-id lists for any status change.
- Results doc: `docs/research/engine_substrate/SHAPE_AUDIT_SWEEP2_RESULTS.md`,
  one section per item, fixed/partial/sized-not-done honestly labelled, real
  file:line citations.
- Commit per logical unit in the worktree; do not merge to main.
