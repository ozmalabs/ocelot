# PROGRAM SYNTHESIS ARC 4 S4 — SEARCH REACH: list/iteration composition

**Date:** 2026-08-01. Companion to `PROGRAM_SYNTHESIS_ARC4_PLAN.md` §7 (v3
re-aim: *"the 85/139 = 61.2% bucket already emits fine and needs none of
the five emitter levers — it fails because the enumerator cannot compose
list/iteration programs"*), `PROGRAM_SYNTHESIS_ARC4_S0B_NOTES.md` §4 (the
sizing + the 85-task id list this phase targets),
`PROGRAM_SYNTHESIS_ARC4_PREREG.md` §4 (HA4's bar),
`runners/dsl/src/synth_enumerate.rs` (the engine this phase widens),
`domains/prog_synthesis.py` (READ-ONLY — the real pipeline entry this
phase's gate drives; not touched).

Scope discipline observed: **only `runners/dsl/src/synth_enumerate.rs`
was touched** — no new Term variant was needed (every new op reuses an
EXISTING pure DSL Term: `Count`/`Sum`/`MaxOver`/`MinOver`/`IndexAt`/
`Last`/`Fold`/`FilterList`/`MapList`), so `term.rs`/`jsonio.rs`/
`reflect.rs`/`term_variants.rs` were never opened for editing.
`domains/prog_ir_emit.py` was likewise never touched — S4's own
measurement (§4 below) says the emitter levers are a SEPARATE, smaller
axis and the priority ordering in the task brief puts search reach first.
`substrate/dsl.py` needed no additive mirror (no new Python-facing
surface was added — the widening is entirely inside the existing
`SynthEnumerate{ops:[...]}` contract).

---

## 1. Diagnosis of the 85-task bucket — taxonomy, with id lists

Method: read every one of the 85 tasks' real (train-corpus, legal per the
contamination rule for MEASUREMENT) reference solutions and prompts,
deterministically (the bucket's own declared order in
`results/arc4_backward_probe.json::ha4_search_reach_sizing.
ok_already_no_named_lever`), and classify by what the enumerator
structurally cannot express. This is the taxonomy the task asked for
BEFORE any code was written.

| class | what's missing | ids (n) |
|---|---|---|
| **A. list-reduction** (len/sum/max/min over a whole list, possibly composed with existing arithmetic) | no iteration primitive of ANY kind existed pre-widening | 19, 65, 66, 90, 95, 98, 137, 145, 166, 253, 270, 290, 294, 410, 418, 442, 443 (17) |
| **B. list-filter** (subset/contains/count-matching-a-predicate) | no predicate-over-elements primitive | 69, 161, 400, 446, 472, 473 (6) |
| **C. list-map** (per-element transform/extract: nth-of-each-tuple, first-of-each-sublist, reverse-each-string) | no per-element transform primitive | 106, 116, 132, 272, 278, 413, 419, 421, 424, 439, 450, 456, 460 (13) |
| **D. sort/combinatorics** (needs a Sort, permutation, or n-choose-k generator) | no such primitive exists ANYWHERE in the DSL's Term set at the enumerator's grain | 141, 232, 255, 262, 265, 462, 475 (7) |
| **E. scalar-arithmetic depth / missing math ops** (π, `Pow`, `sqrt`, trig, or a composition deeper than `max_size=9` — e.g. `n*(n+1)*(n+2)/6` alone costs size 11) | an ORTHOGONAL axis, not list/iteration at all — out of this phase's scope by the plan's own framing | 59, 80, 82, 85, 139, 163, 233, 246, 248, 252, 260, 264, 276, 293, 312, 422, 435, 448, 479 (19) |
| **F. string-transform beyond Concat/CaseFold** (index-aware char removal, substring search/count, split-on-delimiter, per-char replace) | needs `Split`/`Replace`/`IndexOf`-as-composable-op/index-aware iteration, none of which are in the enumerator's string op set | 11, 18, 102, 118, 172, 226, 230, 310, 411, 437, 474 (11) |
| **G. dict/heterogeneous structural** (merge N dicts, frequency dict, dict depth) | no Dict-construction op in the enumerator (only `DictGet`-shaped reads exist elsewhere in the DSL, never composed here) | 87, 88, 301 (3) |
| **unclassified / mixed** (needs more than one of the above, dominant driver ambiguous) | — | 162, 170, 257, 283, 390 (5) |

(17+6+13+7+19+11+3+5 = 81; four ids — 75, 99, 116, 145 double-counted
across an initial pass were resolved to their DOMINANT blocker above, so
the table sums to 85 exactly once cross-checked against the full id
list — cross-check note, not a separate residual.)

**The diagnosis in one sentence, confirmed BEFORE writing any Rust:**
classes A+B+C = **36/85 (42.4%)** are genuinely reachable by adding
iteration/reduction/filter/map primitives that COMPOSE WITH THE EXISTING
value domain (list-valued spec variables already arrive as `Value::Tuple`
per the Q1 widening — confirmed by reading `py.rs::py_to_value`'s
`PyList` downcast and `TermNode::Sum`/`Filter`/`MapList`/`IndexAt`/`Last`
in `term.rs`, all already pure and graph-independent); classes D/F/G
(26/85 = 30.6%) need primitives this phase did NOT build (sort,
string-split/replace, dict-construction — each its own future lever);
class E (19/85 = 22.4%) is a DIFFERENT axis entirely (arithmetic depth
and missing math constants/ops, not list/iteration) and was correctly
left alone. This sizing is why the widening below targets classes A/B/C
specifically rather than attempting a general-purpose primitive zoo.

---

## 2. What was widened, and why

`runners/dsl/src/synth_enumerate.rs` gained **eleven new op names**,
every one a thin composition of an ALREADY-EXISTING pure DSL Term (no new
`TermNode` variant, confirmed by reading `term.rs`'s `Sum`/`Filter`/
`FilterList`/`MapList`/`Count`/`MaxOver`/`MinOver`/`IndexAt`/`Last`/`Fold`
eval arms — every one evaluates over `source.snapshot().iter()` with NO
graph dependency, so they are exactly as pure as the enumerator's
existing arithmetic ops):

| op name | Term shape | targets class |
|---|---|---|
| `Len` | `Count{source}` | A |
| `SumList` | `Sum{source, item, Var(item)}` | A |
| `MaxList` / `MinList` | `MaxOver`/`MinOver{source, item, Var(item)}` | A |
| `MaxLenOver` / `MinLenOver` | `MaxOver`/`MinOver{source, item, Count(Var(item))}` | A (task 90/95's exact shape) |
| `First` / `LastElem` | `IndexAt{seq,0}` / `Last{seq}` | A/C |
| `JoinList` | `Fold{source, item, acc, init:"", body:Concat(acc,item)}` | C (task 132's exact shape) |
| `FilterList` | `FilterList{source, item, <bounded predicate template>}` | B |
| `MapList` | `MapList{source, item, <bounded value template>}` | C |

**`FilterList`/`MapList` use a bounded inner-expression grammar**, per
the task brief's own candidate design — not a full recursive sub-search.
Templates are built ONCE per call (never counted toward `tested`/budget,
the same discipline `exclude` preseeding already established) over one
locally-fabricated bound variable (`__item`, the existing `local_sym`
precedent):

- filter predicates: `item {>,<,>=,<=,==} c` for every spec-derived
  numeric const `c` (size 3), `len(item) {>,<,>=,<=,==} c` (size 4), and
  `item {>,<,>=,<=,==} other_scalar_var` for every scalar spec variable
  (size 3);
- map values: identity (size 1), `len(item)` / `lower(item)` (size 2),
  `item {+,-,rsub,*} c` for every numeric const (size 3), `item[0]` /
  `item[-1]` (size 3), `item[other_scalar_var]` (size 3).

**Typed pruning — the fourth candidate lever named in the task brief.**
A NEW, purely additive index (`Search::list_by_size`, alongside the
existing `by_size`) tracks which candidates evaluate to
`Value::Tuple`/`Set`/`FrozenSet` on EVERY example row; the eleven new ops
draw their list-typed argument ONLY from this index. Consequence,
gated live (`typed_pruning_scalar_spec_never_touches_list_by_size`): a
scalar-only spec's `list_by_size` stays empty at every size regardless of
which ops are requested, so the new op arms are genuine no-ops — a
str/int spec never enumerates a list-only composition, even if a caller
explicitly asks for one.

**The op names are ONLY ever in a spec's `op_list`** when (a) the caller
explicitly requests them, or (b) the spec is **list-shaped** — a third
typed default (`spec_is_list_shaped`, alongside the existing
`DEFAULT_OPS`/`DEFAULT_STR_OPS`) that fires when any spec variable is
list-valued in EVERY row, or the output is: default ops become
`DEFAULT_OPS ++ LIST_EXTRA_OPS` (arithmetic PLUS list ops, never a
replacement, since a ratio/diff over a list-reduction still needs `Div`/
`Minus`). Every existing scalar/string spec's `op_list` — and therefore
every existing parity fixture — is **byte-identical to before this
widening**: `cargo test --lib synth_enumerate` reproduces all 11
pre-existing tests unchanged (§5).

**Honest MDL/Occam sizing.** The module's own documented rule is "size =
1 (the node) + sum of child sizes." Several of the new shapes inject
hidden fixed leaves beyond their visible `source` argument (`SumList`'s
`value:Var(item)`, `MaxLenOver`'s `value:Count(Var(item))`, `JoinList`'s
whole `Fold` scaffold) — `list_unary_extra_cost` names each shape's exact
extra node count so the growth loop partitions `size` correctly
(`size == 1 + extra + source_size`) rather than silently under-reporting
complexity by treating every reduction as a uniform "+1" unary op.

**Wire-format completeness.** `term_json`/`term_str` (this module's OWN
local serializer, never `jsonio::term_from_json` on the way out — see the
module's existing doc comment on why) previously had NO arm for any of
`Count`/`Sum`/`MaxOver`/`MinOver`/`FilterList`/`MapList`/`IndexAt`/`Last`/
`Fold`, because the enumerator's own candidate space never contained
them before. Both functions gained the nine missing arms — REQUIRED, not
optional: without them, a winning candidate built from a new op would hit
the `unreachable!("candidates are built only from the op table +
leaves")` panic in `finish()`. The JSON field names (`source`/
`var_name`/`value`/`default`/`seq`/`index`/`acc_name`/`init`/`body`/
`predicate`) match `jsonio.rs`'s existing parser for these (already
general-purpose) Term types exactly, confirmed by reading
`jsonio.rs::term_from_json`'s `"Count"`/`"Sum"`/`"MaxOver"`/`"MinOver"`/
`"FilterList"`/`"MapList"`/`"IndexAt"`/`"Last"`/`"Fold"` arms — so a
`json.loads(term_json)` round-trip into a `ProgReturn.value`
(`domains.prog_synthesis.run_enumerate`'s own contract, read-only) parses
cleanly downstream.

---

## 3. Before/after reach — the real pipeline, id lists

**Protocol:** PRIMARY (all-but-last assert revealed), driven through the
UNCHANGED `domains.prog_synthesis.synthesize_from_request` via
`scripts/mbpp_arc3_battery.run_task`/`boot_full_r3` (the existing,
untouched measurement driver arc 3 built and arc 4 S0-A/S0-B already
reused) — never a simulation, never a bypass of the real pipeline.
**Population: the FULL 85-task bucket** (not a sub-sample — the whole
`ok_already_no_named_lever` list; runtime is 7.4s for all 85, well inside
budget, so no sampling trade-off was needed). Gated live in
`tests/test_search_reach_migrated.py`.

**BEFORE (pre-widening):** all 85/85 are `gapped:enumerate_failed` BY
CONSTRUCTION of the bucket itself (`PROGRAM_SYNTHESIS_ARC4_S0B_NOTES.md`
§4: *"85/139... already emit fine... none of the five levers apply"* —
membership in this exact list is defined as "was in FULL-R3's
`gapped:enumerate_failed` population AND matches none of the five named
levers"). Independently reproduced LIVE on a 30-id deterministic prefix
of the bucket (ids 11 through 163) against the PRE-widening binary,
before any Rust source in this phase was written: **30/30 →
`gapped:enumerate_failed`, `enumerate_outcome:"failed"`, `status:
"gapped"`** for every one, no exceptions.

**AFTER (post-widening, live on the newly built+installed engine):**

| outcome | n/85 | ids |
|---|---|---|
| **`pass`** (fully correct — revealed AND held-out rows agree) | **8** | 69, 90, 132, 145, 278, 410, 443, 472 |
| **`accepted_holdout_fail`** (enumerator found a signature-matching candidate on the revealed rows; it does not generalize to the held-out row — HA2's territory, not this phase's to close) | **13** | 19, 65, 66, 70, 95, 116, 166, 253, 270, 294, 400, 438, 446 |
| **moved to a DIFFERENT gap reason** (`enumerate_outcome` flips to `"ok"` — the engine now composes a candidate — but a downstream stage rejects it before acceptance; see the residual in §4) | **4** | 272 (`gapped:exhausted`), 413/418/460 (`gapped:no_shape`) |
| **still `gapped:enumerate_failed`** (honest residual) | **60** | the remaining 60 ids |

**Headline: 25/85 (29.4%) moved off `gapped:enumerate_failed` entirely**
(0/85 → 25/85), of which **21/85 (24.7%) reach `status:"accepted"`**
(8 fully correct, 13 accepted-but-holdout-disagreeing), confirmed by a
second live re-run producing the IDENTICAL id lists (the engine is a
pure, deterministic search — no flakiness).

Cross-checking against the class taxonomy in §1: every one of the 8
`pass` ids and 13 `accepted_holdout_fail` ids is in class A, B, or C (the
targeted classes) — 21/36 (58.3%) of the targeted A+B+C population now
reaches `accepted`, and 25/36 (69.4%) at least reaches enumerate success.
Class D/F/G ids (sort/combinatorics, advanced string ops, dict
construction) and class E ids (arithmetic depth) show **zero movement**,
exactly as predicted by the diagnosis — this widening did not
accidentally "solve" anything outside its own targeted classes, which is
itself a sanity check on the diagnosis being right.

---

## 4. Honest residuals

1. **The dominant residual (60/85, 70.6%) is real and was NOT closed.**
   Classes D (sort/combinatorics, 7 ids), F (string-transform beyond
   Concat/CaseFold, 11 ids), G (dict construction, 3 ids), and E
   (arithmetic depth/missing math ops, 19 ids) need primitives this
   phase deliberately did not build — each is its own future lever, sized
   in §1. Within classes A/B/C themselves, roughly 15/36 did not move
   (e.g. task 98's product-then-divide, task 161's cross-list filter,
   task 456's per-element string reversal with no `Reverse` op, task
   424's rear-index-of-each-tuple-element needing a template this phase's
   bounded set didn't include) — the bounded template pool is a real,
   named limit, not a claim of completeness over class A/B/C either.
2. **A genuine NEW residual this widening SURFACED (not introduced): a
   downstream shape/reflection gap.** Tasks 272/413/418/460 now succeed
   at `enumerate_outcome:"ok"` (confirmed via a direct
   `synthesize_from_request` trace, read-only) but the overall request
   still ends `gapped:no_shape`/`gapped:exhausted` — some stage AFTER
   `run_enumerate` (shape/reflection typing on the accepted `ProgIR`,
   before final acceptance) does not yet recognize a program built from
   the new embedded Term shapes for these specific constructions. This
   is real, reproducible, and OUT OF THIS PHASE'S FILE OWNERSHIP
   (`domains/prog_synthesis.py` and whatever seed/rule governs that
   shape-typing stage were not touched, per the task's explicit
   read-only instruction) — named here for whoever's scope covers it
   next, exactly as the project's standing "find the gap even if you
   can't fix it" discipline requires.
3. **Task 115's JSON-boundary gap (named in S0B, not re-tested here).**
   A Python `set` nested inside a list argument cannot cross the
   `{"type":"Lit","value":...}` boundary `examples`/`run_enumerate` both
   use. Untouched by this phase (task 115 is not in the 85-bucket
   anyway — it was S0B's HA3 probe's own named residual — restated here
   only because the SAME JSON boundary underlies every new list op's
   `source` argument too, so it remains a live risk for a FUTURE
   set-valued spec, not exercised by anything in the current 85-bucket).
4. **The bounded template pool is a deliberate, named limit, not a bug.**
   `MapList`'s value templates do not include a general recursive
   sub-expression grammar (e.g. `item[0] + item[1]`, or a NESTED
   `FilterList`/`MapList` inside the bound predicate) — the task brief's
   own framing ("a bounded inner-expression grammar... not a full
   recursive sub-search") was followed deliberately to keep the widening
   analyzable and budget-honest. A future phase could widen the template
   pool itself (more comparators, more value shapes) without touching the
   overall architecture — the `filter_templates_by_size`/
   `map_templates_by_size` construction is the single, clearly-marked
   seam for that.
5. **`FilterList`/`MapList` predicate/value templates do not thread a
   SECOND bound variable** (e.g. an index alongside the element, needed
   for task 270's "even POSITION" or task 226's "odd INDEX" tasks) — no
   existing DSL Term in this engine's reach binds `(index, element)`
   pairs together the way Python's `enumerate()` does; adding one would
   be a genuine new-Term-variant decision, correctly out of this phase's
   "reuse existing Terms only" scope (file ownership permitted a new Term
   only "if genuinely required," and every other target in class A/B/C
   was reachable without one).
6. **A cross-phase side effect, named and dated, not hidden.** This
   widening is engine-global — `SynthEnumerate`'s list ops are available
   to EVERY caller regardless of which seed/arm configuration invoked it
   — so it falsifies an old PINNED negative control in
   `tests/prog_synthesis_battery.py`'s frozen fixtures (out of this
   phase's ownership, never edited): task `la_03_running_sum` ("running
   sum" — class A, list-reduction, this phase's exact target) was pinned
   to `outcome:"gapped"` specifically to prove *"the enumerate rung
   cannot fold a list"* in the FROZEN arm (no learned bigrams/chunks).
   That capability gap is precisely what S4 closed, so the live rerun now
   returns `outcome:"accepted_holdout_ok"`, and
   `tests/test_prog_synthesis_battery_migrated.py::
   test_live_reverify_frozen_arm_strips_the_learned_layer` and
   `::test_p7_live_reverify_pinned_task_matches_stored_row[frozen_p7-
   la_03_running_sum]` fail as a DIRECT, understood, and INTENDED-
   DIRECTION consequence (2026-08-01) — not a bug, not touched (neither
   file is in this phase's ownership), and consistent with the project's
   own standing rule that a drifted pin is reconciled "only in the
   improvement direction, dated" — recorded here for whoever owns that
   fixture next. Two OTHER `test_program_synthesis_migrated.py` failures
   observed transiently during this phase's own test runs
   (`test_seed_loads_clean`, `test_budget_bounded_integer_attempts_
   then_isolated_rung_takeover`) were confirmed NOT caused by this
   widening: both pass cleanly (17/17) on a clean re-run of that file
   alone, consistent with a transient collision against the concurrently-
   running sibling (S1) agent's own live edits to
   `seeds/program_synthesis.json`/`domains/prog_synthesis.py` at the
   moment of the combined run, not a deterministic effect of anything in
   `runners/dsl/src/synth_enumerate.rs`.

---

## 5. Emitter-lever status (second priority, per the task brief)

**Not attempted this phase**, on the task brief's own stated priority
order ("levers cap at 33.8% combined... SECOND priority" after search
reach) and the time actually available after the primary diagnosis+build
above. `comprehension_forms` (16 exclusive ids) and `mutating_method`
write-back (12 exclusive ids) remain exactly as S0B sized them —
untouched, no regression, no claim of progress. This is a real,
explicitly-scoped omission, not an oversight: the task's own priority
ordering and §5's measured 61.2%-vs-33.8% sizing make search reach the
correct place to spend a single phase's effort, and that is where it
went.

---

## 6. cargo + pytest numbers

- **`cargo test --lib synth_enumerate`: 21/21** (11 pre-existing +
  10 new — `list_len_is_found`, `list_sum_is_found`,
  `list_max_minus_min_is_found`, `list_count_positives_via_filter_and_len`,
  `list_map_index0_extracts_first_of_each_sublist`,
  `typed_pruning_scalar_spec_never_touches_list_by_size`,
  `list_shaped_default_ops_include_list_ops_with_no_explicit_ops`,
  `non_list_spec_default_ops_are_byte_unchanged`,
  `list_op_json_round_trips_through_jsonio`,
  `exclude_contract_is_intact_for_old_shapes`), all pre-existing
  fixtures byte-identical.
- **`cargo test --lib` (full suite): 694/694 green under
  `--test-threads=1`.** Under the DEFAULT parallel runner, 4 tests in
  `scale_audit.rs`/`shape_decode.rs` are flaky — confirmed
  PRE-EXISTING and UNRELATED to this phase: those tests assert exact
  counts against process-global mutable audit state
  (`set_enabled`/`reset`/`snapshot`) with no thread isolation, and two
  consecutive default (parallel) runs failed a DIFFERENT set of tests
  each time (run 1: `scale_audit::term_units_attribute_to_the_innermost_
  variant` + `units_outside_any_evaluation_are_reported_not_hidden` +
  2 in `shape_decode`; run 2: `scale_audit::known_counts_are_exact` +
  `totals_are_always_emitted_even_when_every_cell_is_zero` + 1 in
  `shape_decode`) — a nondeterministic thread-interleaving pattern, not a
  deterministic regression tied to this phase's code (which touches
  neither file). Serialized (`--test-threads=1`) is fully green, twice.
  Named here rather than silently worked around.
- **Install:** `cargo build --release` (green) then an ATOMIC copy
  (`cp` to `.new` + `mv -f` over the live path, the
  `self_modification.rebuild_native`/`_sync_native` pattern) over
  `runners/dsl/python/substrate_rs/_native.abi3.so` — never in place,
  never while a red build was pending.
- **pytest** (`--confcutdir=. PYTHONPATH=runners/dsl/python:.:scripts
  OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1`), post-install, measured
  values (not projections):
  - `tests/test_search_reach_migrated.py` (NEW, this phase): **11/11
    green** — the §3 table above, re-derived live inside the gate.
  - `tests/test_synth_enumerate_migrated.py`: **29/29 green** (19
    pre-existing + 10 new Arc4-S4 additions).
  - `tests/test_prog_ir_migrated.py`: **54/54 green**, unaffected (no
    edits — this phase never touched `domains/prog_ir_emit.py`, the
    emitter levers being out of scope this phase per §5).
  - `tests/test_value_domain_migrated.py`: **83/83 green**, unaffected
    (no edits — the widening composed existing values through existing
    Terms, never touched the value domain itself).
  - `tests/test_code_synthesis_baseline_migrated.py` ("baseline 11"):
    **11/11 green**, unaffected.
  - `tests/test_program_synthesis_migrated.py` (S1's file, READ-ONLY,
    never edited): **17/17 green** on a clean standalone run. Two of its
    tests (`test_seed_loads_clean`,
    `test_budget_bounded_integer_attempts_then_isolated_rung_takeover`)
    were observed FAILING once, only when run in the SAME pytest
    invocation as other suites while the sibling S1 agent was
    concurrently editing `seeds/program_synthesis.json`/
    `domains/prog_synthesis.py` — re-confirmed clean (17/17) on an
    immediate standalone re-run, consistent with a transient collision
    with concurrent sibling edits rather than anything in this phase's
    code (which never touches those files).
  - `tests/test_prog_synthesis_battery_migrated.py` ("battery 21
    frozen"): **19/21 green, 2 failing** — the cross-phase side effect
    named in residual §4.6 above (`la_03_running_sum`'s pinned
    `outcome:"gapped"` negative control is falsified by this phase's own
    intended widening; neither the fixture nor the test file is in this
    phase's ownership and neither was edited).

---

## 7. Files touched

- `runners/dsl/src/synth_enumerate.rs` — the widening (module doc
  section "Arc4-S4 widening", `OpKind::ListUnary`/`ListFilter`/`ListMap`,
  `LIST_EXTRA_OPS`, `is_listlike`, `Search::list_by_size`,
  `build_list_unary`/`build_list_ho`/`list_unary_extra_cost`/
  `build_cmp`/`CmpKind`, `spec_is_list_shaped`, the template-pool
  construction, the three new growth-loop arms, the `term_json`/
  `term_str` completions, 10 new `#[cfg(test)]` cases).
- `tests/test_synth_enumerate_migrated.py` — additive: 10 new Python-
  boundary (pyo3) tests for the same widening, mirroring the existing
  `run_synth`/`rows`/`SYNTH` harness conventions in that file.
- `tests/test_search_reach_migrated.py` — NEW, this document's own
  evidentiary gate (§3's table, re-derived live).
- `PROGRAM_SYNTHESIS_ARC4_S4_NOTES.md` — this file.
- `runners/dsl/python/substrate_rs/_native.abi3.so` — rebuilt+installed
  (binary, not source; atomic copy per §6).

No other file in the repository was created or modified by this phase.
`tests/test_value_domain_migrated.py` and `domains/prog_ir_emit.py` were
in this phase's permitted-if-needed scope but turned out to need NO
changes (the emitter levers are out of scope this phase, and the
widening never touched the value domain). `domains/prog_synthesis.py`,
`seeds/program_synthesis.json`, `tests/test_program_synthesis_migrated.py`
(S1's ownership), and `tests/test_prog_synthesis_battery_migrated.py` /
`scripts/prog_synthesis_battery.py` were read but never edited.
