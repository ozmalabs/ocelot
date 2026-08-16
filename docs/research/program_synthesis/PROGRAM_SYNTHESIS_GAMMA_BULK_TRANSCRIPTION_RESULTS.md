# Γ bulk transcription: the remaining op-list evidence-gate sites — RESULTS

Prereg: `PROGRAM_SYNTHESIS_GAMMA_BULK_TRANSCRIPTION_PREREG.md`, same
worktree/branch. Base `main @ 50bde6c`, verified via `git log --oneline -1
main` before creating the worktree. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/progsyn-gamma-bulk-transcription`,
branch `progsyn-gamma-bulk-transcription` — **not merged to `main`, not
pushed**, left for the orchestrator to independently verify and merge.

**Headline: GO, exactly as scoped. 13 new Γ productions ported (11 of the
12 assigned sites, plus a necessary 13th bare-scalar `DEFAULT_OPS` baseline
found while verifying parity; 1 site found DEAD in current source and
correctly not ported), the `SynthOp` vocabulary widened from 52→57 to match
live `OP_TABLE`, one new `SynthSpecShape` flag (`output_is_dictlike`) added
for a correct exclusion. The rung's own full-corpus parity sweep (420 real
MBPP specs) additionally found and FIXED two real, corpus-confirmed parity
bugs in the two ALREADY-SHIPPED `SortBy` productions — both missing a
`¬output_is_setlike` exclusion the design doc's own precedent had not
needed to state explicitly. Final parity: 420/420 real specs fully
explained (261 exact zero-diff, 159 diff-but-documented-out-of-scope, 0
unexplained). MBPP battery: byte-identical to the pre-existing baseline —
76/257 full, 75/257 content_stripped, 101/257 official, EXACT task-id
set-diff empty on all three arms. Named 9-file suite + `test_opgrammar_
migrated.py`: exactly the 3 known pre-existing pin-drift failures, nothing
else; `test_opgrammar_migrated.py` itself 25/25 green. Zero `.rs` files
touched.**

---

## 1. What was built — re-verified against CURRENT source, not inherited

Re-read `runners/dsl/src/synth_enumerate.rs` in full before writing any
code (PREREG §1-§2). Confirmed live, programmatically:

- `OP_TABLE` (`synth_enumerate.rs:291-413`): **57 entries**, not SLICE1's
  own "52" — 5 more landed since (`IntersectAll`, `UnionAll`,
  `DictFromPairs`, `Mod`, `Sqrt`), all 5 added as static `SynthOp` nodes
  this rung (keeping the seed's own "one node per real `OP_TABLE` entry"
  invariant true).
- The op-list evidence-gate ladder has grown a new branch since the
  design doc was written: `spec_output_is_dictlike` → `DICT_DEFAULT_OPS`
  (`GroupCount`/`DictMerge`/`DictFromPairs`), inserted into the `if`/`else
  if` chain between the list-shaped branch and the bare-scalar fallback.
  **Deliberately out of Γ scope** (not one of the 14 named sites) — its
  only effect on this rung is that reaching the bare-scalar fallback now
  additionally requires `¬output_is_dictlike`, which the new 13th
  production encodes.

## 2. The 14-site table, re-derived from current source, cross-checked
   against the design doc's own count

| site | evidence | admits | this rung |
|---|---|---|---|
| A | `is_string_shaped` | `DEFAULT_STR_OPS` (13 ops) | **ported** |
| B | `is_list_shaped ∧ ¬setlike` | `DEFAULT_OPS ∪ LIST_EXTRA_OPS` (26 ops) | **ported** |
| C | `output_is_listlike ∧ ¬setlike` | `TupleOf` | **ported** |
| D | `output_is_listlike ∧ ¬setlike` | `Sort` | **ported** |
| E | `output_is_listlike ∧ has_string_value ∧ ¬setlike` | `Split` | **ported** |
| F | `output_is_setlike` | `SET_DEFAULT_OPS` (10 ops) | **ported** |
| G | `has_string_value`, bare-scalar branch | `Replace,Split,StrCount,Capitalize,Str,ParseInt` | **ported** |
| H | `has_float_value`, bare-scalar branch | `Round` | **ported** |
| I | `has_float_value ∧ is_list_shaped ∧ ¬setlike` | `Round` | **ported** |
| J | `has_dict_value` | `DictItems,SortBy,Reverse` | **`SortBy` already shipped (fixed, §6); `DictItems`/`Reverse` completed here** |
| K | `has_repeated_list_element`, bare-scalar branch | `IndexedMap` | **DEAD in current source — NOT ported, §3** |
| L | `has_repeated_list_element ∧ is_list_shaped ∧ ¬setlike` | `IndexedMap` | **ported** |
| M | `has_list_of_lists ∧ ¬has_dict_value` | `SortBy` | **already shipped (fixed, §6)** |
| N | `output_is_bare_int ∧ is_list_shaped ∧ ¬setlike ∧ ¬listlike ∧ ¬string ∧ ¬float` | `ParseInt` | **ported** |

14 sites, matching the design doc's own count exactly. 2 already shipped
(M fully, J's `SortBy` third only), 1 (K) confirmed dead, 11 newly ported +
1 completion (J's `DictItems`/`Reverse`) = the 12 the assessment doc names,
plus a necessary 13th (§4).

## 3. Site K confirmed dead in current source — traced, not assumed

`extra_evidence_ops` (`synth_enumerate.rs:2230-2239`) is populated
unconditionally on every call but read exactly once, at line 2393, **inside
the bare-scalar `else` branch** of the `if spec_is_string_shaped {...}
else if spec_output_is_setlike {...} else if spec_is_list_shaped {...}
else if spec_output_is_dictlike {...} else {...}` chain. Site K's own
guard (line 2237, `if spec_is_list_shaped && spec_has_repeated_list_element
{ extra_evidence_ops.push("IndexedMap") }`) requires `spec_is_list_shaped`
to be true — but the ONLY place that reads `extra_evidence_ops` is reached
exclusively when `spec_is_list_shaped` is false. **`IndexedMap` can never
be admitted via this specific push, for any spec, in current source.**
Verified two ways: (a) static control-flow tracing (above), (b) live — the
new test `test_site_l_list_shaped_repeated_element_indexedmap` asserts
`IndexedMap` is admitted with `is_list_shaped=True` and NOT admitted with
`is_list_shaped=False` (both `has_repeated_list_element=True`), and the
full-corpus parity sweep (§7) never once flags a real-vs-Γ disagreement
here across 420 real specs, because the oracle itself does not add
`IndexedMap` on that branch either (its own docstring names this
explicitly). Not ported — porting it would transcribe something the live
ladder never actually does.

## 4. A necessary 13th production: the bare-scalar `DEFAULT_OPS` baseline

`DEFAULT_OPS`'s 12 arithmetic ops are admitted via TWO Rust branches, not
one: the list-shaped branch (site B) AND the bare-scalar fallback
(`else`, line 2392, `DEFAULT_OPS.to_vec()` unconditionally). Without a
production for the second path, EVERY plain-arithmetic MBPP spec ("add two
numbers" — a large, common shape in the corpus) would show a Γ-vs-real
mismatch on all 12 names. Ported as its own production, gated on the real
branch-reachability condition: `¬is_string_shaped ∧ ¬output_is_setlike ∧
¬is_list_shaped ∧ ¬output_is_dictlike` — the last conjunct is why
`output_is_dictlike` (§5) had to be added; without it this production would
wrongly admit `DEFAULT_OPS` for a Dict-output-only spec (task 87's shape),
which the real ladder routes to `DICT_DEFAULT_OPS` instead (an entirely
different, non-overlapping op set).

## 5. `output_is_dictlike` — the eleventh `SynthSpecShape` flag

`_synth_spec_shape_flags` (`domains/prog_synthesis.py`) already computed
all ten of the design doc's named flags, **none a placeholder** — checked
directly before writing anything, confirmed by reading the function's own
body. This rung adds one more: `output_is_dictlike` (direct 1:1 port of
`spec_output_is_dictlike`, `synth_enumerate.rs:2164`,
`outputs.iter().all(is_dict_val)`), needed ONLY for §4's exclusion. It does
**not** admit any `DICT_DEFAULT_OPS`-bucket op — that stays out of scope.
Live-verified: `test_synth_spec_shape_flags_output_is_dictlike`.

## 6. Two real, corpus-confirmed bugs found in the ALREADY-SHIPPED `SortBy`
   productions, and fixed

The PREREG (§6) predicted, from static reasoning, that both shipped
productions (site J's `SortBy` third, site M) were missing exclusions their
Rust push sites structurally require (both live nested inside `else if
spec_is_list_shaped`, so both need `¬output_is_setlike`; site J additionally
needs `is_list_shaped` itself, since `has_dict_value` does not imply it).
**This is not theoretical — the full-corpus parity sweep confirmed it on
real MBPP tasks, run BEFORE the fix:**

| task(s) | flags (abridged) | wrong Γ verdict |
|---|---|---|
| 111, 140, 473 | `has_list_of_lists=True, output_is_setlike=True, is_list_shaped=True` | Γ admitted `SortBy`; real ladder takes `SET_DEFAULT_OPS` (Set-shaped output checked EARLIER in the chain), never reaches the `SortBy` push at all |
| 301, 464, 796 | `has_dict_value=True, is_list_shaped=False` | Γ admitted `SortBy` (and, before the flag/exclusion fix, `Mod`/`Sqrt` too — those are correctly out-of-scope, not a bug); real ladder falls to the bare-scalar branch, which never pushes `SortBy` |

6/420 real specs showed this. **Fixed in place** (the ONE deviation from
"don't touch the 2 shipped productions" — justified because (a) the bug is
corpus-confirmed, not speculative, (b) the fix is a straightforward,
narrowly-scoped exclusion add, exactly the idiom the shipped productions
already use elsewhere, (c) Γ verdicts are never consulted by production
code, so the fix is zero-risk to the MBPP score by construction, and (d)
leaving a known, diagnosed, evidence-confirmed parity bug in place while
reporting "GO" on parity would be dishonest). Both fixes:

- `sortby_dict_gate`: added `is_list_shaped=true` and `¬output_is_setlike`.
- `sortby_list_of_lists_gate`: added `is_list_shaped=true` and
  `¬output_is_setlike` (alongside its pre-existing `¬has_dict_value`).

Re-run after the fix: 0/420 mismatches (§7). The original live-
demonstration witnesses (tasks 64, 475, negative control 2) still pass —
`test_live_demonstration_gamma_matches_the_real_ladder` is unchanged and
green (§9).

## 7. The full-corpus parity sweep — exact numbers

`scripts/opgrammar_bulk_parity_sweep.py` (new, one-off diagnostic script,
`scripts/ceiling3_diag_sweep.py`'s family — not part of the named 9-file
suite, not wired into any agent path). For every real, runnable MBPP task
spec in `tests/fixtures/mbpp/sanitized-mbpp.json` (`primary` protocol):
computes the 11 evidence flags, a hand-traced Python oracle replica of the
**complete current** Rust ladder (including the deliberately-out-of-scope
`DICT_DEFAULT_OPS` branch and the unconditional `Mod`/`Sqrt` append, so
mismatches against those can be correctly classified as expected), and Γ's
admitted set via 57 `is_edge_admissible` calls. Diffs the two sets per
spec, classifying a difference as EXPECTED iff every differing name is one
of the 5 deliberately-out-of-scope ops (`GroupCount`, `DictMerge`,
`DictFromPairs`, `Mod`, `Sqrt`) OR the spec lands in the out-of-scope
`DICT_DEFAULT_OPS` branch entirely.

```
Checked 420 real, runnable MBPP task specs.
Exact set-agreement (Gamma == real, no diff at all): 261/420
Diff-but-fully-explained (out-of-scope ops or Dict branch): 159/420
Specs landing in the out-of-scope DICT_DEFAULT_OPS branch: 4
UNEXPECTED mismatches: 0

TOTAL EXPLAINED: 420/420 (ALL EXPLAINED, GO)
```

**420, not 257**: `sanitized-mbpp.json` carries the vendored corpus beyond
just the 257-task TEST split (per CLAUDE.md's own "all_427_sanitized"
denominator note); the sweep's own `split_rows(..., "primary")` runnability
filter (needs ≥2 parseable rows) is what selects 420 of those. This is a
BROADER, not narrower, sample than the 257-task TEST split alone — every
TEST-split task that is `primary`-runnable is included.

**Reproduce:**
```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-gamma-bulk-transcription
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/opgrammar_bulk_parity_sweep.py
```
The same check is ALSO gated as a real pytest assertion (not just a
standalone script), so future drift fails CI:
`tests/test_opgrammar_migrated.py::
test_full_corpus_parity_sweep_zero_unexplained_mismatches`.

## 8. Production design: `In` for bucket sites, not one production per op

`Production.tgt` matches by node TYPE only, never attrs (`grammar.rs:20-
26`) — op-specificity always lives in `where_`, whether via `Eq` (single
op) or `In` (member-of-a-literal-list, for a bucket). `TermNode::In`
(`term.rs:51`, evaluator `5029-5045`) is a real, already-shipped Term
already used exactly this way in `where` clauses across the live seed
corpus (`seeds/conversation_capability_route.json` and three siblings, read
directly) — an established idiom, not a novel mechanism introduced here.
`jsonio.rs::grammar_from_json` parses a production's `where_` via the same
generic `term_from_json` Rules use, so `In` is fully legal there; verified
live (§9, sites A/B/F/G/J-completion all use `In` and all pass). This kept
the total new-production count at 13 instead of the ~90 a
one-production-per-op transcription of a 26-op bucket (site B alone) would
require.

## 9. Regression discipline

**No `.rs` files touched** (`git status --porcelain` in the worktree shows
only `domains/prog_synthesis.py`, `seeds/program_synthesis_opgrammar.json`,
`tests/test_opgrammar_migrated.py` modified, plus two new files — this
PREREG/RESULTS pair and `scripts/opgrammar_bulk_parity_sweep.py`) — no Rust
rebuild performed, per the task's own scoping ("genuine from-source rebuild"
only required if `.rs` files are touched).

**`tests/test_opgrammar_migrated.py`: 25/25 passed** (was 13 in SLICE1; +12
new tests: seed-count update to 57, `DictItems`/`Reverse` completion +
its `is_list_shaped` requirement, the "never admits an out-of-scope op"
stress test [replacing the now-stale "only SortBy has productions" premise
— this rung legitimately widens which ops Γ admits under `is_list_shaped`,
so the old assertion that `Plus`/`Sort`/`DictItems` are never admitted is
no longer true and correctly updated, not merely re-asserted], the new
`output_is_dictlike` flag unit test, one test per newly-ported site [A, B
+its required exclusion, C/D/E, G +its list-shaped non-overlap, H/I, L
+confirming K's absence, N, and the 13th bare-scalar baseline +its
dictlike exclusion], and the full-corpus parity sweep as a real pytest
assertion).

**MBPP battery** (`scripts/mbpp_endgame_battery.py`, full run):

```
full:              76/257  p=0.29572   ci=[0.243264, 0.354192]  det_identical=True
content_stripped:  75/257  p=0.291829  ci=[0.239641, 0.350148]  det_identical=True
official:          101/257 p=0.392996  ci=[0.335279, 0.453865]  det_identical=True
```

**Byte-identical to the pre-existing baseline** (`main`'s own committed
`results/mbpp_endgame.json`, 76/75/101 — confirmed by copying it aside as
`results/mbpp_endgame_BEFORE.json` before running this worktree's own
battery). **Exact task-id set-diff, all three arms:**

```
full:              before=76  after=76  added=[]  removed=[]
content_stripped:  before=75  after=75  added=[]  removed=[]
official:          before=101 after=101 added=[]  removed=[]
```

Zero regressions, zero new passes, at the task-id grain — exactly the
expected, correct outcome (Γ verdicts are recorded facts only, never
consulted by `run_enumerate`'s real op-list construction, which is
byte-unchanged by this rung).

**Named 9-file suite + `test_opgrammar_migrated.py`** (sequential, not
concurrent with the battery — the SLICE1-documented shared-mutable-
output-path fragility):

```
3 failed, 266 passed in 188.57s
FAILED tests/test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live
FAILED tests/test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_drift
FAILED tests/test_exact_first_migrated.py::test_named_regression_sweep_only_known_pins_drift
```

**Exact match, same three test names**, to the already-documented
pre-existing pin-drift failures (named explicitly in this task's own
brief as the expected baseline) — none of `test_opgrammar_migrated.py`'s
25 tests appear in the failure list, and a standalone re-run of that file
alone confirms 25/25 green.

**Environment setup note (not a code defect, reported for the next
worker)**: this fresh worktree was missing several gitignored `results/*`
artifacts and the `data/` symlink that `main`'s working tree already has
locally (per CLAUDE.md's own documented "`data/` symlinked" gotcha, plus
several `results/*.json` reference artifacts these specific tests read:
`prog_construction_scan.json`, `mbpp_zero_shot_baseline.json`,
`prog_chunk_mine.json`, `mbpp_train_diet.json`, `mbpp_arc3_endgame.json`,
`arc4_structural_verdicts.json`, `prog_synthesis_battery.json`,
`code_synthesis_baseline.json`, `mbpp_blocker_histogram.json`). All are
small, pre-existing, static reference files (largest 1.4MB) copied
verbatim from `main`'s working tree — none newly generated, none touched
by this rung's own logic, and this worktree's own `results/mbpp_
endgame.json`/`mbpp_endgame_BEFORE.json` are the only two files this rung's
own commands actually WROTE. `results/` itself was NOT symlinked (unlike
`data/`) specifically to avoid a shared-mutable-output-path collision with
the primary tree while this worktree's own battery/test runs write to
`results/mbpp_endgame.json`.

---

## 10. What this document does NOT establish

1. **Does not claim the shipped-then-fixed `SortBy` productions were ever
   WRONG in production behavior** — Γ verdicts are recorded facts only,
   never consulted for `spec["ops"]` construction (confirmed unchanged,
   §9's battery result), so the bug found in §6 never affected any MBPP
   task outcome. It was a genuine Γ-layer parity bug, not a synthesis-
   capability regression.
2. **Does not claim the 420-spec sample is the full sanitized corpus** —
   420 is the `primary`-protocol-runnable subset of 427 vendored tasks
   (§7); a handful of unparseable/too-few-row specs are excluded by
   `split_rows`'s own runnability gate, the same gate the battery itself
   uses.
3. **Does not extend the mint-sweep harness** (assessment doc's
   recommendation #2, `OPLIST_ADMISSIBILITY_GRAMMAR_RESULTS.md` §6) — out
   of scope for this rung, unchanged.
4. **Does not wire Γ consultation into `run_enumerate`'s real op-list
   construction** — explicitly out of scope per the task brief (residual
   #41), confirmed unchanged: the `spec["ops"]` block in `run_enumerate` is
   untouched by this rung's diff.
5. **Does not port the §1.2 template-pool population**
   (`map_templates_by_size`/`indexed_map_templates_by_size`) — a
   structurally similar but separate population the design doc's own §1.2
   explicitly scoped out of the op-list Γ layer; unaddressed here too.
6. **Does not claim the environment-setup gaps found in §9 are specific to
   this worktree** — they are standing, gitignored, locally-generated
   artifacts every fresh worktree of this repo will be missing; noted here
   as a reproduction aid for whoever next creates a worktree touching this
   test population, not a defect this rung introduced or is responsible for
   fixing generally.
