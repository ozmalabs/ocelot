# PROGRAM SYNTHESIS ARC 2 Q3 — THE PAIRED DIET

**Date:** 2026-08-01. Companion to `PROGRAM_SYNTHESIS_ARC2_PLAN.md` sec2
Q3, `PROGRAM_SYNTHESIS_ARC2_PREREG.md` (HQ3 is decided at Q5 on the MBPP
**test** split; this phase builds the content and measures trigger
coverage + a train-side transfer probe only — never a benchmark accept
rate), `PROGRAM_SYNTHESIS_P7C.md` (the arc-1 chunk machinery this phase
reuses unchanged, and the 2/15-cueable trigger-poverty finding this phase
exists to fix).

**Deliverables:** `scripts/mbpp_train_diet.py` (the miner),
`results/mbpp_train_diet.json` (the artifact — every aggregate below
derives from its per-row arrays), `seeds/mbpp_train_diet.json` v1.0.0 (45
nodes: 15 chunks + 30 bigrams + 0 affinity rows — an installable,
node-only seed manifest, no rules), two additive functions + one additive
installer in `domains/prog_chunk_growth.py` (`abstract_expr`,
`mbpp_chunk_entry_name`, `ensure_mbpp_train_diet` — zero edits to existing
bodies), `tests/test_mbpp_diet_migrated.py` (18 passed, 1.5s).

**Scope, absolute:** every learning path in this phase reads ONLY the 120
MBPP **train**-split tasks (`task_id >= 601`, per
`tests/fixtures/mbpp/provenance.json`'s canonical split). Validation
[511,600] and test [11,510] are never read anywhere in this script. Every
minted node carries `source_task_ids` (all >= 601) for the list-gate.

---

## 1. Program-side: the train-split emit rate (gates everything downstream)

| metric | n / 120 | % |
|---|---|---|
| **emit_prog_ir ok** (whole-function, real emitter) | **90** | **75.0%** |
| blocked (`emit_blocked`) | 30 | 25.0% |
| entry-resolution failure | 0 | 0.0% |

This is close to Q0's full-427-corpus figure (74.0%) — the train split is
not systematically easier or harder to emit than the corpus as a whole.

**Residual handling, checked per the task brief's instruction:**
`emit_prog_ir` (`domains/prog_ir_emit.py`) is an all-or-nothing,
FUNCTION-LEVEL translator — there is no statement-level partial-IR mode.
The arc-1 miner (`scripts/prog_chunk_mine.py::extract`) never attempts one
either (`if not r.get("ok"): ... continue`). This script mirrors that
scope exactly: **a function with ANY blocker contributes ZERO chunks and
ZERO bigram statements**, not a truncated prefix. This is a real, honestly
reported ceiling on this phase's mined mass (30/120 train programs
contribute nothing), not a Q3 defect — closing it would be an
`emit_prog_ir` design change (a Q1-class phase), out of this phase's
file-ownership scope.

## 2. Chunks — mined at the P7-C idiom grain, unchanged extraction walk

| metric | value |
|---|---|
| candidate chunk instances | 412 |
| distinct chunk types | 393 |
| recurring types (support >= 2) | 16 |
| support-threshold `s*` | 2 (the EXISTING P7-C floor fired: quantile target = ceil(1%*16) = 1, which would keep only the single highest-support type; the floor raises coverage back up to the largest `s` keeping >= 8 types — here that IS `s=2`, keeping all 16) |
| corpus-too-small fallback (registered addition, this phase) | **not engaged** (16 recurring >= 8 — the existing P7-C floor already handled a corpus this size; the extra fallback is verified present in the code and tested, but the 120-task train split turned out large enough not to need it) |
| kept pre-dedup | 16 |
| AntiUnify dedup, 2/3 vs 5/6 | 1 join each → 15 survivors either way |
| family-collapse check | 1 multi-member (>=3) family pre-join, median post-join count = 4 (not 1) → **adopts 2/3**, same as P7-C |
| **chunks minted** | **15** |
| support range | 2–5 |
| grain distribution | `window_2` ×10, `compound_1` ×2, `window_3` ×3 |

The much smaller, more homogeneous train corpus (90 emittable functions
vs P7-C's 4099) naturally produces a much smaller idiom population —
393 distinct types vs 30,177 — but the SAME registered rules (threshold,
AntiUnify criterion, family-collapse adoption test) apply unmodified and
land on a sane, non-degenerate 15-chunk codebook, exactly the P7-C
target band's floor (8).

## 3. Triggers — THE HEADLINE: paired-prompt co-occurrence vs code-derived words

**6/15 chunks (40.0%) carry >=1 nonzero-scored trigger token, vs arc-1's
2/15 (13.3%)** — a 3x improvement, gated
(`test_trigger_coverage_headline_is_derived_from_rows`,
`test_trigger_coverage_headline_is_derived_from_rows` asserts the fraction
strictly exceeds 2/15, re-derived from the artifact's own per-chunk rows,
never quoted bare).

| chunk | support | n_stmts | cueable? | trigger tokens (top-5, uppercase) |
|---|---|---|---|---|
| `mck_prog_assign_var_n2_q0` | 5 | 2 | no (duplicate labels) | — |
| `mck_prog_if_stmt_n1_q1` | 2 | 1 | **yes** | AMOUNT, FORM, JUMPS, LOSS, ORIGIN |
| `mck_prog_if_stmt_n1_q2` | 2 | 1 | **yes** | EXPECT, FORM, JUMPS, ORIGIN, PLANE |
| `mck_prog_aug_assign_n2_q3` | 2 | 2 | **yes** | ADD, MOVE, END, TUPLE, ALL |
| `mck_prog_aug_assign_n2_q4` | 2 | 2 | **yes** | ARRAY, SORTED, OCCURRENCE, LAST, POSITION |
| `mck_prog_assign_var_n3_q5` | 2 | 3 | no (duplicate labels) | — |
| `mck_prog_assign_var_n2_q6` | 2 | 2 | **yes** | ARRAY, SORTED, OCCURRENCE, LAST, POSITION |
| `mck_prog_assign_var_n2_q7` | 2 | 2 | no (duplicate labels) | — |
| `mck_prog_assign_var_n2_q8` | 2 | 2 | no (duplicate labels) | — |
| `mck_prog_assign_var_n2_q9` | 2 | 2 | **yes** | MEDIAN, SIZE, SAME, SORTED, LISTS |
| `mck_prog_assign_var_n2_q10` | 2 | 2 | no (bare loop control) | — |
| `mck_prog_assign_var_n3_q11` | 2 | 3 | no (duplicate labels) | — |
| `mck_prog_assign_var_n2_q12` | 4 | 2 | no (duplicate labels) | — |
| `mck_prog_assign_var_n3_q13` | 2 | 3 | no (duplicate labels) | — |
| `mck_prog_assign_var_n2_q14` | 2 | 2 | no (extern outside NATIVE_ORACLES) | — |

**Cueability gating is the UNCHANGED P7-C structural rule**
(`cue_exclusion_reason`): 9/15 excluded — 8 by duplicate-label (the
`ProgAssignVar`+`ProgAssignVar` window, this corpus's dominant idiom, has
the same lattice-contract problem P7-C found), 1 by bare loop control
(`break`/`continue` outside a loop within the window), 1 by an extern
outside `NATIVE_ORACLES`. These are hole-fill-only chunks regardless of
trigger source — the cueability CEILING is a structural fact of the idiom
population, not something a better trigger source can move.

**Method (registered in the task brief, arithmetic not NLP):** for each
chunk, `score(token) = (fraction of the chunk's own co-occurring train
tasks whose prompt mentions the token) * ln(N_train / global_document_
frequency(token))` — a plain tf-idf-style ratio over
`domains.mbpp_spec.request_facts(prompt)["request_body"]` (Q2's
verb-frame-stripped normalization, so "write"/"function"/"to" boilerplate
never becomes a candidate token). Top-5 per chunk kept, uppercased to
match the goal-token case convention `ps_propose`'s Argmax match already
reads (`domains.code_writing._content_tokens` also emits UPPERCASE).

**Honest residual — small-n trigger noise.** Every cueable chunk here has
support exactly 2 (2 co-occurring train tasks). With only 2 documents,
tf-idf's numerator (`local_df/chunk_task_count`) is either 0.5 or 1.0 for
every candidate word, so the ranking is driven almost entirely by the IDF
term — i.e. by which words happen to be RARE across the 120-prompt
population, not by genuine topical relevance. This is why the trigger
lists above read as somewhat arbitrary content words (AMOUNT, JUMPS,
ORIGIN, PLANE) rather than obviously on-topic ones: **the mechanism is
sound and reproducible, but at n=2 per chunk it is intrinsically noisy.**
This is a real, structural improvement over arc-1's 2/15 (triggers now
come from the RIGHT source — prompts, not code — and MORE chunks are
cueable), but it is not yet a mature cue vocabulary; a larger paired
corpus would sharpen it further. Reported honestly, not smoothed over.

## 4. Cue → starter-construction affinity — a clean, informative null

**0/8 starter constructions matched any train task, by exact
role/slot-abstracted structural equality** (`starters_checked: 8`,
`starters_matched: 0`, `affinity_rows: []`).

Diagnostic (not part of the shipped artifact, run for this note):
25/90 train functions have a single-statement `return <expr>` body (the
ONLY shape eligible to compare against a starter's expression-grain
template), but their term-type distribution is `ProgCallExtern` x19 (a
one-line call to a native-oracle builtin, e.g. `sorted(...)`/`sum(...)`
directly — structurally nothing like any starter's hand-authored
arithmetic term), `Plus` x3, `IfThenElse` x1, `Minus` x1,
`ProgComprehensionList` x1. The 3 `Plus`-shaped and 1 `IfThenElse`-shaped
candidates are the closest analogues to `sum_of_two`/`max_of_two`'s own
grammar, yet **none matched exactly** — the real emitter's `Plus`/
`IfThenElse` nodes evidently differ in operand shape (e.g. non-`Var`
operands, or 3+ addends) or comparison operator from the starters' own
hand-authored 2-`Var` templates. `total_of_list`/`count_of_list` (the two
`Fold`-based starters) can NEVER match real emitted code at all —
`domains/prog_ir_emit.py` has no source pattern that emits a `Fold` term
(confirmed by grep: zero occurrences); `Fold` is purely a
synthesis-side/hand-authored construct. **This is a genuine, informative
null**, not a mining bug: real MBPP one-liners essentially never
literally coincide with the 8 starter shapes' exact hand-authored
grammar, so the "does a train prompt cue an EXISTING starter" question is
answered honestly as "not observed at this corpus size" rather than
forced.

## 5. Bigrams — head grain, additive alongside the arc-1 corpus population

30 `ConstructionBigram` rows, `provenance:'mbpp_train'`,
`source:'mbpp_train_diet.json'`, vocab size 10 (9 statement-type heads +
`</s>`), mined from the SAME 90 emit-ok train functions' top-level
statement sequences, using `prog_ir_signature.statement_signature(s)[0][1]`
— the identical "head" projection
`domains.prog_synthesis.ensure_construction_bigrams` already boards the
P3-corpus statistics at, and the identical add-1-smoothed formula
(`ln((c+1)/(prev_total+|V|))`). No sd-loop merge/mint pass was re-run —
at head grain, that projection collapses to the raw statement-type label
directly, so this script mines it in one pass (verified: `mbpp_train`
provenance rows install ALONGSIDE, never replacing, the arc-1
`prog_construction_scan.json`-sourced rows —
`test_ensure_mbpp_train_diet_boards_bigrams_additively_alongside_arc1`).

**Documented consumption residual (out of this phase's file-ownership
scope to fix):** `domains/prog_synthesis.py`'s `_bigram_tables()` reads
ALL `ConstructionBigram` nodes into one `(prev,next) -> trans_logp` dict
by plain iteration — on an EXACT key collision between an arc-1 row and
an `mbpp_train` row, whichever seed's rows were loaded into the graph
LAST wins outright; the two populations are never blended/interpolated.
This is additive in the sense the task required (neither population is
deleted or rewritten), but a future phase that wants a genuine blend
(e.g. weighted by corpus size) would need to change `_bigram_tables`
itself — `domains/prog_synthesis.py` is Q4-owned and untouched here.

## 6. The leave-N-out transfer probe (train-side MECHANISM, NOT the HQ3 verdict)

**Protocol:** mine on the first 100 train tasks (by `task_id`); probe the
PRIMARY-protocol pipeline behaviour on the remaining 20 holdout train
tasks. **Every holdout task is run under a PROTECTED CONTROL** (starter
codebook + arc-1 corpus bigrams only, `ensure_program_synthesis`, no
diet) **and a DIET arm** (+ the 100-task-mined manifest, loaded directly)
on independent fresh substrates — "diet content used" is claimed ONLY
when the outcome could not have come from CONTROL alone (a mined `mck_`
chunk was the accepted/gapped construction, OR the two arms' (status,
construction, spine_labels) triple diverges). This mirrors the codebase's
standing protected-control discipline (the H6/H7c `C-CODEBOOK-FROZEN`
precedent) — an earlier draft of this probe naively counted "spine_labels
non-empty" as usage and was WRONG (the arc-1 bigrams are always present
via `ensure_program_synthesis`, so a lattice decode can succeed from that
population alone; the corrected version below is what shipped).

**Headline: 11/20 (55.0%) holdout tasks show diet content used**, split
two ways:

- **5/20 — a mined chunk (`mck_...`) is the accepted/gapped construction**
  the control arm could never produce (task ids 788, 791, 793, 799, 800 —
  all `gapped`, i.e. the mechanism engaged but the held-out row didn't
  verify; a mechanism fact, not a capability claim, per the standing
  distinction);
- **6/20 — the SAME starter construction is found by BOTH arms (via the
  codebook rung), but the DIET arm's lattice rung succeeds
  (`ps_rung_lattice: 1.0`, a real `spine_labels` ordering) where CONTROL's
  fails (`ps_rung_lattice: None`, empty `spine_labels`)** — task ids 792,
  796, 797, 802, 805, 809. This is genuine evidence the mined
  `mbpp_train` bigram rows carry USABLE transition mass the P3-corpus
  bigrams alone did not supply for these specific statement-head
  sequences (e.g. `ProgAugAssign -> ProgReturn`).
- **9/20 — not used** (3 `protocol_excluded:no_parseable_rows`, the
  known bare-call/unaryop train residual named in
  `PROGRAM_SYNTHESIS_ARC2_Q2_NOTES.md`; 6 genuine nulls where CONTROL and
  DIET produce byte-identical outcomes).

Three pinned tasks re-verify LIVE in `tests/test_mbpp_diet_migrated.py`
(re-run the full 100/20 probe from scratch each test run, not read from
the frozen artifact):

- **788** — mined-chunk-used exemplar (`used_mined_chunk`, control
  produces no construction at all);
- **809** — bigram-without-chunk exemplar (`min_of_two` in both arms;
  control's lattice fails, diet's succeeds);
- **798** — an honest not-used null (control and diet produce IDENTICAL
  outcomes — the probe correctly reports non-usage, not vacuous "yes").

**Reading, honestly:** diet content DOES get used mechanically at this
train-internal scale — both through direct chunk proposals and through
bigram-enabled spine ordering. This is exactly the kind of signal HQ3
needs to be decidable at Q5 (on MBPP test, with FULL vs CONTENT-STRIPPED
arms) — it is NOT itself the HQ3 verdict (this probe is entirely
train-internal, with no held-out generalization claim beyond "the
mechanism engages on unseen-at-mine-time train tasks"), and every
`gapped` outcome above is a mechanism fact, not a pass.

## 7. Gates

`tests/test_mbpp_diet_migrated.py` — **18 passed, 1.5s**: scope sanity
(120 train tasks, all >=601); mining determinism (twin-run byte-identical
`mine_diet`, and the shipped artifact's own recorded twin-run checked);
provenance completeness (every seed node carries `source_task_ids`, every
id >=601 — a list-gate, not a count; node-type counts match the results
rows 1:1); seed loads clean via `load_seed_manifest` (0 skipped) +
idempotent install (`ensure_mbpp_train_diet` returns 0 on a second call,
no duplicate names) + additive-alongside-arc-1 bigram check; chunk names
use a distinct `mck_` namespace (never `ck_`/`ckt_`), bounded <=40 chars;
trigger-coverage headline re-derived from rows and asserted to beat
arc-1's 2/15; every chunk carries `derived_prompt_tokens` honestly
regardless of cueability; the leave-N-out probe's 3 pinned tasks re-verify
live under the protected control; this phase's own contamination scan of
its 3 new artifacts (results/seed/script) against the full test-split
forbidden-substring list (>200 entries) is clean.

**Neighbor suites, same engine, same moment** (a clean working-tree
moment — no sibling Q4 in-flight edits observed via `git status` at
measurement time):

| suite | result |
|---|---|
| `tests/test_mbpp_contamination_migrated.py` (the shared list-gate) | **7 passed** |
| `tests/test_prog_chunks_migrated.py` (arc-1 chunk suite) | **11 passed** — untouched; this phase's `domains/prog_chunk_growth.py` changes are strictly additive (2 new functions + 1 new installer, 0 edits to existing bodies) |
| `tests/test_program_synthesis_migrated.py` | 17 passed |
| `tests/test_mbpp_spec_migrated.py` | 67 passed |
| `tests/test_prog_synthesis_battery_migrated.py` | 21 passed |
| `tests/test_code_synthesis_baseline_migrated.py` | 11 passed |
| **combined** | **152 passed in 4.0s** — well under the ~120s budget |

**Note on the shared contamination gate's `SCAN_TARGETS`:** per the Q2
precedent, this phase's new files (`seeds/mbpp_train_diet.json`,
`results/mbpp_train_diet.json`) are NOT added to
`tests/test_mbpp_contamination_migrated.py`'s `SCAN_TARGETS` list — that
list is owned by the sibling Q0-A track and was not touched here. This
phase's OWN equivalent scan (`test_own_contamination_scan_of_new_
artifacts_is_clean`, same normalize+substring logic, applied to all 3 new
artifacts) covers the gap the shared list doesn't yet reach.

## 8. Honest residuals

1. **Trigger vocabulary is noisy at n=2 per chunk** (sec3) — real, sound
   mechanism; immature vocabulary. A larger paired train corpus (were one
   available) would sharpen it.
2. **Cueability ceiling is structural, not trigger-source-dependent**:
   9/15 chunks are hole-fill-only regardless of where triggers come from
   (duplicate-label / bare-loop / non-native-extern — the SAME P7-C
   structural checks). Better triggers cannot make an uncueable chunk
   cueable.
3. **Zero starter-shape affinity matches** (sec4) — a clean null, not a
   defect: real MBPP one-liners essentially never coincide exactly with
   the 8 hand-authored starter templates' grammar, and `Fold`-based
   starters (`total_of_list`/`count_of_list`) can never match emitted
   code at all (the Python emitter never produces `Fold`).
4. **Bigram consumption is last-loaded-wins on exact-key collision**
   (sec5) — additive at the graph level (nothing is deleted/rewritten),
   but not a genuine statistical blend; fixing that is a
   `domains/prog_synthesis.py` change, out of this phase's ownership.
5. **The leave-N-out probe is entirely train-internal** (sec6) — real
   mechanism evidence, explicitly NOT the HQ3 verdict (that is Q5, on
   MBPP test, FULL vs CONTENT-STRIPPED, with Wilson/Newcombe CIs).
6. **30/120 train programs contribute nothing** (sec1) — the emitter's
   all-or-nothing scope, unchanged from arc-1, not attempted to be
   widened here (a Q1-class change, out of ownership).
7. **Support-threshold small-corpus fallback verified present but not
   exercised** (sec2) — this train corpus's 16 recurring types happened
   to clear the existing P7-C floor's own >=8 requirement; the new
   fallback code path (`corpus_too_small_fallback`) is implemented and
   would fire on a smaller/sparser corpus, but this run reports
   `False` honestly rather than claiming credit for a mechanism that
   didn't need to engage.
