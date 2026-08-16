# MDL/Occam witness-priced literals — PREREG (Proposal 1, Slice 1 of
   `DESIGN_REVIEW_CAPABILITY_EXPANSION_PREREG.md`)

**Date:** 2026-08-16. Base `main @ f4394fd` ("Add fable design review:
witness-priced literals for the Occam-ordering wall, plus two
capability-expansion proposals"), verified fresh via `git log --oneline -1
main` before creating the worktree. Worktree:
`/home/matt/ocelot-mdl-occam-witness-pricing`, branch
`mdl-occam-witness-pricing` — **not merged to `main`, not pushed**, left
for the orchestrator to independently re-verify and merge.

This document is written in the exact sequence house discipline requires:
mechanism first (below), THEN the gates are run and their real
(not-predicted) results are appended to the companion RESULTS doc — this
PREREG is committed before gate (1) (the load-bearing known-safe-fact
check) is executed.

---

## 0. Headline (mechanism, stated before any gate has run)

`SynthEnumerate`'s constant pool (`runners/dsl/src/synth_enumerate.rs`)
priced every pooled literal — a delimiter character, a genuine task
constant, AND a whole memorized output row quoted verbatim — at the same
leaf cost, 1. `DESIGN_REVIEW_CAPABILITY_EXPANSION_PREREG.md §2` names this
as the mechanical cause of the measured Occam-ordering wall
(`CEILING_REASSESSMENT_7_PREREG.md §5`: 5/5 spurious literal-lookup
`IfThenElse` accepts on the string-shaped probe set, all wrong on
held-out). This rung implements the prescribed fix: **a witness census on
each pooled STRING literal, computed from data already in scope (`envs`,
`outputs`), that reprices a single-witness output quote (the memorization
signature) to its own description length, and leaves every data-derived or
row-invariant literal at cost 1, byte-unchanged.** Everything downstream
(`by_size`, the growth loop, budgets, pruning, evaluation) is untouched —
this changes only which size class a literal registers into, the same
mechanism `list_unary_extra_cost`/`list_binary_extra_cost`
(`synth_enumerate.rs:854,968`) already use to price a derived construct's
hidden node count honestly.

Integer-valued auto-appended outputs (`synth_enumerate.rs:2767-2778` at
the pre-change line numbering) are **deliberately excluded from this
slice**, per the design doc's own §7 item 6 scoping — strings only.

---

## 1. Mechanism, precisely (as implemented, current line numbers)

Read directly in `runners/dsl/src/synth_enumerate.rs` on this worktree's
tip:

- `value_str` (`:1396-1402`, unchanged) — the existing helper that reads a
  `Value::Str`/`Value::Surface(Text, _)` out as an owned `String`.
- **New**: `literal_witness_cost(s, envs, outputs, interner) -> usize`
  (`:1404-1463`), placed immediately after `value_str` as its natural
  home. Priority order, first match wins, computed ONLY from `envs`
  (`&[Env]`) and `outputs` (`&[Value]`), both already in scope at the
  const-pool construction site — no new inputs, matching the design doc's
  own framing:
  1. **Data-derived**: the literal `s` occurs as a substring of ANY row's
     input variable value (`row.iter().any(|(_, v)| value_str(v,
     interner).is_some_and(|sv| sv.contains(s)))`) → cost 1. Substring
     (not exact-match) so a single delimiter character is correctly
     caught as data-derived when it recurs inside a longer input string —
     the design doc's own `"_"` example.
  2. **Row-invariant**: `s` occurs (substring) in EVERY row's output →
     cost 1. A literal that recurs identically across all revealed rows
     is a genuine task constant, not a memorized per-row answer — and
     this rule fires BEFORE the single-witness rule below, so a 1-example
     spec (where "every output" and "exactly one output" coincide) always
     resolves to row-invariant, cost 1, never accidentally repriced.
  3. **Single-witness output quote**: `s` occurs (substring) in EXACTLY
     ONE row's output and satisfies neither rule above → priced at
     `s.chars().count().max(1)` — the memorization signature the design
     doc names.
  4. Otherwise (partial multi-row output coverage, no input witness — not
     named as a case in the design doc) → cost 1, unchanged. This is the
     conservative default: slice 1's scope is the one named signature,
     not every shade of partial coverage.
- **Registration site** (`run_enumerate`, was `synth_enumerate.rs:2744-
  2809` at the design doc's citation, now the equivalent block after the
  above insertion): `str_consts` (the existing SPEC-DERIVED-ONLY pool —
  every whole input/output string plus every character of each) is now
  registered SEPARATELY from `const_set` (the requested/default numeric
  consts `0,1,2,-1` plus auto-appended integer outputs, entirely
  UNCHANGED, still all cost 1) instead of being `extend`-ed into it. Each
  `str_consts` entry is registered at `literal_witness_cost(...)`; an
  entry priced ABOVE `max_size` is skipped entirely (not registered at
  all — indexing `by_size[size]` at a size beyond the Vec's `max_size+1`
  length would panic, and a candidate this expensive could never be
  reached by the growth loop regardless, which is the fix's whole point).

**Byte-preservation claim, precisely scoped:** for every literal that
keeps cost 1 (data-derived, row-invariant, or the conservative-default
case), registration order and size are IDENTICAL to before this change —
same relative order within `by_size[1]` (const_set's ints first, then the
`str_consts` cost-1 subset in their original iteration order), same
signature-dedup behaviour. Only the single-witness subset moves to a
different (higher, or entirely absent-if-over-budget) size class. This is
a claim about the MECHANISM as read from source, not yet a measured fact
about which of the 88/87/113 currently-passing tasks it touches — that is
gate (1), below, and its real result is recorded in the companion RESULTS
doc, not predicted here.

---

## 2. Gates, in the exact order the design doc specifies

1. **Known-safe fact first.** The full MBPP battery (`scripts/
   mbpp_endgame_battery.py`, `tests/test_mbpp_endgame_migrated.py`) must
   re-find the CURRENT 88/87/113 (full/content_stripped/official) with an
   EMPTY `lost_pass` task-id-set diff against the pre-change baseline. If
   any currently-passing task's accepted program legitimately quotes a
   single-witness output literal, it regresses under this repricing — the
   honest, reportable outcome per the design doc, not something to patch
   around.
2. **The 5-task spurious probe re-swept**: tasks `102, 396, 427, 437, 478`
   at `max_candidates=2,000,000`, `ops` omitted (typed-default op
   selection — `CEILING_REASSESSMENT_7_PREREG.md §5.1`'s exact method,
   direct `SynthEnumerate` evaluate call, no graph pipeline). Prediction:
   zero of the five return a literal-lookup `IfThenElse` shape. Reported
   as measured, not assumed.
3. **Tasks 102/411 re-swept at the DEFAULT budget** via the real pipeline
   (`domains.prog_synthesis.synthesize_from_request`, `max_size=20`,
   `max_candidates=0` → engine default `200,000`, matching
   `CEILING_REASSESSMENT_7`'s own "the real pipeline's own typed-default
   search, at the CURRENT `max_size=20`/`max_candidates=200,000`"
   framing). If the genuine `Fold(MapList(Split(...),...,Capitalize(...)),
   ...)` composition is found and passes held-out, that is +2 MBPP ids.
   If not found, that is still a decisive, reportable finding (the wall
   was not literal-pricing alone) per the design doc's own explicit
   instruction not to treat "no conversion" as this rung's failure.

## 3. What this document does NOT establish

1. Whether gate (1) passes clean is not yet known as this PREREG is
   committed — it is the very first thing run after this doc lands, and
   its real result (task-id-set diff, not a bare count) is the RESULTS
   doc's own §1, not asserted here.
2. Gates (2) and (3)'s actual outcomes are not predicted beyond quoting
   the design doc's own falsifiable prediction (zero of five) — the
   RESULTS doc reports what was measured, including if it disagrees.
3. The Γ flip (design doc §2 slice 2) and the negative-codebook variant
   (§2 slice 3) are explicitly out of scope for this rung — Slice 1 only.
4. Rebuild/regression-suite verification (the 9-file named suite, the
   778-baseline `cargo test --lib --release` count) has not yet been run
   as this doc is committed; both are run and reported in RESULTS.
