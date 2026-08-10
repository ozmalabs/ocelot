# PROGRAM SYNTHESIS ARC 2 Q2 — SPEC COMPREHENSION for benchmark prose

**Date:** 2026-08-01. Companion to `PROGRAM_SYNTHESIS_ARC2_PREREG.md` (the
three-way PRIMARY/SECONDARY-OFFICIAL/STRESS split protocol, §0; HQ2, §4 —
reframed as spec-EXTRACTION quality, since recognition already sat at
256/257 zero-shot), `PROGRAM_SYNTHESIS_ARC2_Q0_BASELINE.md` (the assert
parseability taxonomy this phase closes: `math_isclose` 13 tasks /
`set_wrapper` 3 / `set_literal_value` 2 = 17 test-split tasks), and
`PROGRAM_SYNTHESIS_ARC2_Q0_HISTOGRAM.md` (prompt-form counts, constraint
vocabulary — the source pool this phase mined against, TRAIN-only).

**Deliverables:** `domains/mbpp_spec.py` (the shared spec layer —
`classify_assert`/`parse_asserts`/`split_rows`/`signature_facts`/
`request_facts`), `seeds/mbpp_request_cues.json` v1.0.0 (50 Concepts, all
train-earned), `tests/test_mbpp_spec_migrated.py` (67 passed, 0.26s).

---

## 1. HQ2 headline — spec-extraction quality (the reframed bar)

Measured over the **TEST split (task_id in [11,510], n=257)**, the
population every later arc-2 phase is scored against:

| metric | n/257 | % | prereg bar | met? |
|---|---|---|---|---|
| **PRIMARY-runnable (>=2 parseable rows)** | **257/257** | **100.00%** | (the anti-overfit denominator §0 depends on) | — |
| signature facts complete (arity-consistent, arity>0) | 257/257 | 100.00% | — | — |
| arg-count matches reference function (measurement-only, reads `code`) | 257/257 | 100.00% | >=95% of PRIMARY-runnable | **YES** |
| request-recognized (write-request cue, unchanged mechanism) | 256/257 | 99.61% | >=90% of all 427 tasks | **YES** (already met at Q0, unchanged) |

**The 56.8% `accepted_holdout_fail` finding's fix depends on PRIMARY's
anti-overfit denominator being wide** (PREREG §0) — it now covers **100%**
of the test split, up from Q0-A's 240/257 (93.4%) under the STRESS-shaped
1-revealed-row rule. Every one of Q0-A's original 17
`assert_unparseable` test-split tasks (`82, 85, 98, 111, 124, 137, 139,
140, 163, 232, 233, 246, 248, 276, 300, 312, 473`) is now PRIMARY-runnable
— a byte-for-byte match against Q0-A's own named list, not a
coincidental overlap.

**Argument-value correctness** (the HQ2 bar's clause (b): "every revealed
row's argument VALUES match the corresponding literal AST nodes exactly")
holds **by construction**: every row's `inputs`/`expected` values ARE the
`ast.literal_eval` result of the assert's own literal sub-nodes — there is
no intermediate re-encoding step that could drift a value. `tests/
test_mbpp_spec_migrated.py::test_parse_asserts_never_reads_code_field` and
the equivalence-on-overlap test are the executable proof this holds
row-for-row against an independent parser.

**Null reading (not triggered):** extraction quality is nowhere near <90%
— recognition, arity, and value-match are all at or above their bars.
There is no residual routed to "cue vocabulary needs re-tuning"; the
prereg's own prediction (recognition was never the bottleneck) holds.

## 2. The three Q1/Q2-boundary forms — landed

`domains/mbpp_spec.py`'s `classify_assert` is a strict superset of
`scripts/mbpp_zero_shot_baseline.classify_assert` (gated:
`test_equivalence_on_overlap_with_q0a_parser_whole_corpus` — 0 cases where
the baseline accepts and this module rejects, exact row match on every
overlap, verified against all 1324 asserts in the 427-task vendored
corpus). Three named forms move from unsupported to parseable:

| form | asserts (427-corpus) | tasks | row shape |
|---|---|---|---|
| `math.isclose(f(args), expected, rel_tol=tol)` | 39 | 13 | float row + explicit `tol` field |
| `set(f(args)) == set(literal)` | 15 | — | `unordered: True` row, `expected` re-typed `frozenset` |
| raw `set`/`frozenset` literal (arg or top-level expected) | 6 | — | set values carried through natively; `unordered: True` only when the TOP-LEVEL `expected` is itself a set |
| **total newly parseable** | **60** | — | — |

**Verdict-layer semantics, stated explicitly (per the task brief's "document
which"):** `unordered: True` rows compare as **SETS** — order-insensitive
AND duplicate-insensitive (multiple copies of one element collapse to
one) — exactly Python's own `set(...) == set(...)` idiom, never
multiset/bag equality. A `tol` field, if unread by a consumer, silently
falls back to EXACT float equality on that row — an honest, named
default, not a hidden approximation (no consumer currently reads `tol`;
this is Q1's hook to wire a tolerance comparator).

**Residual named honestly (task 124, `angle_complex`):** this task's
asserts are now fully PARSEABLE (`math.isclose` extension), but one
argument is a genuine Python `complex` literal (`1j`). Complex numbers are
NOT in the plan's registered value-domain scope (`PROGRAM_SYNTHESIS_ARC2_
PREREG.md` §2's fixed 7-type target: int/list[int]/str/bool/float/none/
dict) — **parseable is not the same claim as synthesizable**. This is a
residual for Q1 to accept or explicitly re-exclude, not a Q2 defect; Q2's
job was honest extraction, which is what happened.

**Residual unparseable, corpus-wide (427 tasks, per-assert):**

| reason | n asserts | task ids | band |
|---|---|---|---|
| `boolean_expression:bare_call` | 12 | 737, 781, 787, 794, 803, 804 | ALL train |
| `boolean_expression:unaryop` | 10 | 737, 781, 787, 794, 803, 804 | ALL train |
| `multi_call` | 3 | 596 | validation (`sys.getsizeof`, environment-dependent, uncomparable by construction — matches `PROGRAM_SYNTHESIS_ARC2_PREREG.md` §1's own naming) |

**Zero residual unparseable asserts fall in the TEST split** — every one
of the remaining 25 unparseable asserts (7 tasks: 596 validation, six
`737/781/787/794/803/804` train) lives outside the population HQ2/HQ3 are
measured against. Per-split PRIMARY-runnable rate: TEST 257/257 (100.0%),
TRAIN 114/120 (95.0%, the 6 bare-call/unaryop tasks), FULL-427 420/427
(98.4%).

**Not attempted (explicit scope boundary, not silently dropped):** bare
boolean-expression asserts (`assert f(x)`, `assert not f(x)`) ARE
mechanically parseable in principle (the call + an implicit `== True`/
`== False`) — the task brief named three specific forms to land
(math_isclose / set_wrapper / raw set literals), and this phase stays
inside that boundary. All six affected tasks are TRAIN-split only, so
this residual has zero effect on any HQ2/HQ3 test-split measurement;
named here for whoever scopes a future phase.

## 3. Cue seed — `seeds/mbpp_request_cues.json` v1.0.0, train-only provenance

**Recognition was already met at Q0 (256/257 zero-shot)** — this seed
does not change recognition; `code_writing.looks_like_write_request`'s
existing `write`/`function` cues already satisfy MBPP's own phrasing.
This seed adds FINER-GRAINED facts (`domains.mbpp_spec.request_facts`:
which exact verb-frame variant, which constraint words are present) for a
future cue rule to consume — additive, no decision made here.

**Provenance discipline (the binding contamination requirement — "earned
from TRAIN-split prompts + the existing generic cues ONLY, list-gated"):**
every one of the seed's 50 Concepts was independently verified to occur
in the 120 TRAIN prompts (`task_id >= 601`) before inclusion; the seed's
own `train_count` field is cross-checked against a FRESH mining pass in
`tests/test_mbpp_spec_migrated.py::test_train_only_provenance_list_gate`
(not merely trusted from the seed's own bookkeeping).

**Verb frames (6, vs Q0-B's original 4 fixed prefixes):**

| frame | train_count/120 |
|---|---|
| `write a function to` | 70 |
| `write a python function to` | 32 |
| `write a function that` | 7 |
| `write a function which` | 3 |
| `write a python function which` | 2 |
| `write function to` | 1 |
| **covered** | **115/120 (95.8%)** |

Two variants (`write a python function which`, `write function to`) are
NEW beyond the histogram's original 4 — genuinely earned from train
mining. **Honestly excluded:** `write a python function that` has **zero**
train occurrences despite being a plausible sibling of the other five —
left OUT (falls to `verb_frame: "other"`) rather than added on pattern
symmetry alone. 5/120 train prompts match no frame at all (irregular
phrasing, e.g. "The input is given as ... Write a function to ...").

**Constraint words (44, filtered from the existing 55-word generic
vocabulary in `scripts/mbpp_blocker_histogram.CONSTRAINT_VOCAB`):** that
generic list was mined from the FULL 427-task corpus (test included), so
it is **not itself a valid contamination-safe source** — every word was
re-verified against TRAIN ONLY before inclusion. **12 of the 56 generic
words have ZERO train occurrences and are correctly EXCLUDED:**
`armstrong, camel, duplicate, factorial, frequency, kth, negative,
palindrome, positive, snake, substring, unique` (gated:
`test_generic_vocab_words_absent_from_train_are_correctly_excluded`).
Highest-frequency included words: `tuple` (17/120), `sum` (15/120),
`count` (11/120), `index`/`length`/`sorted` (7/120 each).

**Parity:** `domains.mbpp_spec._MBPP_VERB_FRAMES_FALLBACK` /
`_MBPP_CONSTRAINT_WORDS_FALLBACK` are byte-identical to the seed's
Concept vocabulary (gated: `test_module_fallback_sets_match_seed_exactly`)
— a minimal boot without this seed classifies identically (the
`code_write_request_cues` parity precedent). The seed loads clean via
`load_seed_manifest` (0 `rules_skipped`, 0 `reflexes_skipped`, 50 nodes).

## 4. Contamination

- **The existing gate, run standalone, is fully green:**
  `tests/test_mbpp_contamination_migrated.py` — **7 passed** (unmodified;
  this seed is deliberately not added to its `SCAN_TARGETS` — that list
  is owned by the sibling Q0-A track and was not touched here).
- **This module's own equivalent scan against its own new artifact**
  (`test_mbpp_request_cues_seed_has_no_test_split_contamination`, same
  normalization + forbidden-substring construction as the existing gate,
  applied directly to `seeds/mbpp_request_cues.json`): **zero hits**.
- `domains/mbpp_spec.py`'s `parse_asserts`/`signature_facts` never read
  `task["code"]` (gated: `test_parse_asserts_never_reads_code_field`,
  `test_signature_facts_never_reads_code_field`) — safe to call against a
  live test-split task at synthesis run time, not just offline.
- The one place this phase DOES read `task["code"]` is the HQ2
  arg-count-matches-reference measurement (§1, both in this document and
  in `test_signature_facts_arg_count_matches_reference_function_sample`)
  — sanctioned explicitly by `tests/fixtures/mbpp/provenance.json`'s
  `contamination_rule` ("test-split ... code ... MAY be read for
  MEASUREMENT ... they may NEVER enter any codebook entry, cue-vocabulary
  token, bigram row, or taught shape"). No value from that read enters
  `mbpp_spec.py`, the seed, or any codebook — it is a read-check-discard
  measurement, exactly Q0-B's own histogram's status.

## 5. Environment note (not this phase's regression)

`tests/test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_
live` and `tests/test_mbpp_histogram_migrated.py::
test_frozen_artifact_reproducible_from_full_corpus` /
`test_known_task_2_bitand_is_set_intersection_not_bitwise` are RED on this
worktree at the time of this phase's work — reproduced BEFORE and
independent of any file this phase touched, traced to the sibling Q1.5
track's concurrent in-flight edit of `domains/prog_ir_emit.py` (`git
status`: modified, not part of this phase's file-ownership list). Named
here per the standing "a baseline is a list, never absorbed silently"
rule — not fixed by this phase (out of file-ownership scope), not caused
by it (confirmed: the same three tests fail identically with `tests/
test_mbpp_spec_migrated.py` excluded from the run entirely).

## 6. Test suite

`tests/test_mbpp_spec_migrated.py` — **67 passed, 0.26s** (well under the
~60s budget). Six gate classes: per-form parser units (12 supported-form
tests including the three new boundary forms + 16 named-refusal
parametrized cases), protocol-split units (8 tests, all three protocols,
pinned examples, official flagged `protocol_distinct`), corpus-wide
equivalence-on-overlap + residual-taxonomy gates (imports `mbpp_zero_shot_
baseline` read-only), signature-facts units (7 tests incl. a real
arg-count-vs-reference spot check), request-facts + cue-seed gates (13
tests: closed-fallback behaviour, seed shape, clean load, parity, the
train-only provenance list-gate, the generic-vocab-exclusion gate, this
module's own contamination scan), determinism (3 tests).

## 7. Files

- `domains/mbpp_spec.py` — the shared spec layer (new).
- `seeds/mbpp_request_cues.json` v1.0.0 — 50 Concepts, train-only
  provenance (new).
- `tests/test_mbpp_spec_migrated.py` — 67 passed, 0.26s (new).
- `PROGRAM_SYNTHESIS_ARC2_Q2_NOTES.md` — this document (new).
