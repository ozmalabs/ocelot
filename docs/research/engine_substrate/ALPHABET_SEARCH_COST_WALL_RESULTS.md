# Alphabet-driven per-character constant pool — RESULTS

**Date:** 2026-08-17. Base `main @ 5494752` (verified fresh at the start of
this rung). Worktree: `/home/matt/ozmadev/ocelot-alphabet-search-cost-wall`,
branch `alphabet-search-cost-wall`. Companion:
`ALPHABET_SEARCH_COST_WALL_PREREG.md` (predictions and the
SHAPES-NOT-NUMBERS classification, both written and committed before any
Rust change ran). **Not merged to `main`, not pushed** — left for the
orchestrator's independent re-verification, per house discipline.

**HEADLINE: the fix lands GO, on both corpora, with `lost_pass` empty
everywhere it is measured — but only after the FIRST version regressed
MBPP (2 tasks, both whitespace-removal shapes) and was caught by this
rung's own paired battery, then repaired with one further, well-motivated
carve-out (Unicode whitespace stays cost 1, unconditionally) before
shipping. PBE corpus: `declared` 14→17/26, `declared+high_budget` 17→20/26,
`typed_default` UNCHANGED at 12/26, zero losses in any arm. MBPP: `full`
88→89/257, `content_stripped` 87→88/257, `official` 115→116/257, `lost_pass
= []` in all three arms (verified by exact task-id set diff against the
live 88/87/115 baseline artifact). Three of the four named wall-blocked
tasks (`pbe_015`, `pbe_024`, `pbe_026`) now converge; `pbe_012` remains
stuck (honest, not forced).**

---

## 0. What shipped

One file changed: `runners/dsl/src/synth_enumerate.rs` (+98/-9 lines —
`git diff --stat` against `main@5494752`). `literal_witness_cost` gains a
5th parameter (`alphabet_size: usize`) and, for single-character literals
only, prices them by `alphabet_char_cost(alphabet_size) =
ceil(log2(alphabet_size))` instead of the flat `1` every other rule in the
ladder still returns — EXCEPT for two protected categories, both checked
ahead of the new pricing and both unconditional (cost 1 regardless of
alphabet size): row-invariant characters (existing rule 2, unchanged in
spirit) and Unicode whitespace characters (NEW — added after the first
MBPP battery caught a real regression, see §3). Every multi-character
literal's pricing is byte-identical to `main@5494752`.

---

## 1. SHAPES-NOT-NUMBERS classification (from the PREREG, unchanged)

Checked directly against what each primitive IS in this codebase, not
assumed:

- **sd loop**: ruled out. Nothing here is being learned or minted — every
  character in `str_consts` is already fully known (copied verbatim from
  the spec's own revealed rows). There is no residual, no codebook
  growth, no recognize/transform/infer ladder to run.
- **Γ admissibility grammar**: ruled out. `seeds/program_synthesis_opgrammar.json`
  is, in its own words, scoped to "the op-list boolean gate ladder…a real
  generated multi-production admissible-move SET," consulted ONCE, in
  Python, before the Rust search runs. `SynthOp` nodes denote OPERATORS,
  not constants — there is no precedent or natural node type for a
  per-character graph object, and the `declared` arm's fixed `PBE_OPS`
  always includes `Replace`/`Split` (verified: `scripts/pbe_string_battery.py:99-104`),
  so a coarse "gate the pool on whether a literal-consuming op is
  present" admissibility rule — the one form that WOULD map cleanly onto
  the existing precedent — would be a no-op for exactly the corpus this
  wall was measured on.
- **Conclusion, confirmed by what shipped**: an in-kind extension of
  `literal_witness_cost` itself, generalizing its own stated principle
  ("price a pooled STRING literal by its description length given its
  witnesses") along a second MDL axis — bits to select one symbol out of
  the spec's own observed alphabet — that rule 3's length-based pricing
  could never reach for a single character (a 1-character string's own
  length is always 1, so there is nothing left to compress). This is
  exactly what shipped; no Γ or sd-loop code was touched or added.

The PREREG's §2 also recorded, BEFORE any Rust code ran, a rejected
per-character SEMANTIC classifier (row-presence-pattern and
row-local-count-difference heuristics, tested against real fixture data
in Python) — both failed to discriminate at this corpus's realistic 2-3
row count and risked pruning `pbe_025`'s genuinely-needed `'p'` literal.
That negative result is why the shipped design prices ALL single
characters uniformly by alphabet size rather than trying to classify
which ones are individually useful.

---

## 2. Build and unit-test verification

Genuine from-source rebuilds throughout (every `cargo build`/`cargo test`
below followed a `touch runners/dsl/src/synth_enumerate.rs`, and none
finished in under a minute — no cached sub-second runs were mistaken for
real ones). `RUSTFLAGS`/`LD_LIBRARY_PATH` set together on the same
command per the house protocol.

- `cargo test --lib --release -- --test-threads=1` on the FINAL
  (whitespace-carve-out-included) patch: **778 passed; 0 failed; 4
  ignored** — identical to the 778 pre-fix baseline (no new Rust unit
  tests were added; the existing suite is untouched by this change).
- `bash scripts/engine_build.sh` + the two `python3` tail commands
  (`python: command not found` was the documented benign PATH quirk) —
  `tests/test_engine_provenance_migrated.py` 9 passed, 1 skipped, on
  every rebuild in this rung.
- Disk space checked before/after every rebuild: held steady at ~69G
  free throughout (`df -h /`), never approached the 10G stop threshold.

---

## 3. THE FIRST VERSION REGRESSED MBPP — caught, diagnosed, and fixed
     before shipping

The first cut of the fix (log2-alphabet pricing, no whitespace carve-out)
passed the PBE battery cleanly but, on the FIRST full paired MBPP battery,
regressed all three arms by exactly one task each:

| arm | baseline | v1 (no whitespace carve-out) | lost | gained |
|---|---|---|---|---|
| full | 88/257 | 87/257 | `[230, 451]` | `[242]` |
| content_stripped | 87/257 | 86/257 | `[230, 451]` | `[242]` |
| official | 115/257 | 114/257 | `[230, 451]` | `[242]` |

Diagnosed directly from the artifact (`runnable_rows` per-task detail),
not guessed: **task 451 is "remove all whitespaces from the given
string" and task 230 is "…replaces blank spaces in the string with the
character…" — the SAME shape as the PBE corpus's own `pbe_006`
(`remove_spaces`), which had already shown the identical mechanism in the
`typed_default` PBE arm** (12/26 baseline → 11/26 on the v1 patch, lost
`pbe_006`/`pbe_025`, gained `pbe_005`) — confirmed by directly reverting
to the pre-fix engine (temporary rebuild, `git diff`-captured and
restored, the `MDL_OCCAM_WITNESS_PRICING_RESULTS.md` precedent) and
diffing `tested`/`size`/`term_str` before and after: `pbe_006` moved from
found-at-size-5/153,563-tested (within the 200,000 default budget) to
found-at-size-8/1,061,836-tested (past it) purely because the space
character's cost rose from 1 to `alphabet_char_cost(16) = 4`. Both
regressed MBPP tasks and `pbe_006` recovered cleanly at a raised budget in
every case tried (`pbe_006` found at size 8 with 2,000,000 candidates) —
the SAME "surmountable via budget alone" signature `PBE_STRING_BENCHMARK_RESULTS.md`
already established for `pbe_010`/`pbe_013`/`pbe_021`, not a permanent
capability loss, but real inside the corpus's OWN default budget and
therefore a genuine regression under the task's own gate ("`lost_pass`
must be empty").

**The fix, added on top of the same mechanism, not a separate patch:** a
Unicode whitespace character is a universal token/word separator by
construction — Python's own `str.split()`/`str.strip()` default to it,
and this exact module already privileges it structurally (`PBE_CONSTS`'s
own `""` entry is documented as "Split's own documented whitespace-split
trigger," `scripts/pbe_string_battery.py:106-112`). `literal_witness_cost`
now checks `s.chars().next().is_some_and(|c| c.is_whitespace())` AHEAD of
the alphabet-size pricing (and ahead of row-invariance, though the two
never conflict) and returns cost 1 unconditionally when true — a
structural fact about the character itself (a Unicode category), not
evidence read from the spec's rows, so it sits beside row-invariance
(rule 2) as an evidence-independent protected category rather than a
tuned numeric threshold. Scoped to `char_count == 1` only; every
multi-character literal is untouched.

**Re-verified after the carve-out, both corpora, exact task-id diffs
(not just counts) — this is the number reported as the headline:**

| arm | baseline | v2 (final, whitespace carve-out) | lost | gained |
|---|---|---|---|---|
| full | 88/257 | **89/257** | `[]` | `[242]` |
| content_stripped | 87/257 | **88/257** | `[]` | `[242]` |
| official | 115/257 | **116/257** | `[]` | `[242]` |

`lost_pass` is empty in every arm. PBE re-run on the SAME (v2) engine:
`typed_default` returned to exactly 12/26 (byte-identical task-id set to
the pre-fix baseline — `pbe_006` recovered), `declared` improved further
to 17/26 (up from the v1 patch's own 16/26, since `pbe_006` is also part
of `declared`'s inventory), `declared+high_budget` 20/26. **No losses in
any PBE arm either, on the final shipped version.**

This negative-then-repaired result is reported in full, not smoothed
over: the fix as FIRST designed did not clear the MBPP gate, and would
have been a NO-GO without the whitespace carve-out. The carve-out is not
an ad hoc save — it is a second, independent, evidence-independent
protected category of the SAME kind rule 2 already is, discovered by
running the paired battery exactly as the task brief specified and
reading the failure precisely instead of assuming the design was
adequate.

---

## 4. PBE corpus — final numbers, both baseline and this rung's engine

| arm | baseline (main@5494752) | this rung (final) | delta |
|---|---|---|---|
| `typed_default` | 12/26 | 12/26 | 0 (byte-identical pass set) |
| `declared` | 14/26 | 17/26 | **+3** |
| `declared+high_budget` | 17/26 | 20/26 | **+3** |

`diff(declared − typed_default)`: `lost: [], gained: [pbe_010, pbe_011,
pbe_013, pbe_021, pbe_024]` (`pbe_024` — one of the four named
wall-blocked tasks — now passes in `declared` WITHOUT needing the
high-budget escalation at all, a stronger result than the task brief
asked for).

`diff(declared_high_budget − declared)`: `lost: [], gained: [pbe_015,
pbe_025, pbe_026]`.

### 4.1 The four named wall-blocked tasks, individually

| task | baseline | this rung | notes |
|---|---|---|---|
| `pbe_012` | not found (any budget) | **still not found** | `initials_concat`, needs `Split`+`MapList`+`JoinList` together — the doc's own §2.1 "deeper instance" prediction; this fix alone does not resolve it, reported honestly rather than forced |
| `pbe_015` | not found (any budget) | **passes at high budget** | `first_and_last_char` |
| `pbe_024` | not found (any budget) | **passes at DEFAULT budget** | `trap_capitalize_reverse_slice`, the doc's own PRIMARY memorization-wall probe |
| `pbe_026` | not found (any budget) | **passes at high budget** | `trap_slice_capitalize_reverse`, `pbe_024`'s mirror |

Three of four named tasks converge; `pbe_012` does not — consistent with
the PREREG's own framing (§3, "convergence isn't guaranteed by this fix
alone") and the doc's own §2.1 diagnosis that `pbe_012`'s remaining
difficulty is compounded by op-breadth (three chained ops), not alphabet
size alone.

---

## 5. MBPP — final paired battery, exact task-id sets

Baseline artifact: `/home/matt/ozmadev/ocelot/results/mbpp_endgame.json`
(head `9dbad6d`, measured 2026-08-17T00:57 — confirmed to match the task
brief's own cited 88/87/115 numbers exactly, and confirmed via
`git diff --stat 9dbad6d 5494752 -- runners/dsl/src/ domains/prog_synthesis.py
domains/mbpp_spec.py seeds/program_synthesis*.json` — EMPTY, so this
artifact is a valid same-engine-behavior reference for
`main@5494752`). This worktree needed `data/` symlinked to the canonical
tree (`ln -s /home/matt/ozmadev/ocelot/data data`, per CLAUDE.md's own
optional-dep note) plus four `results/*.json` reference artifacts
(`prog_construction_scan.json`, `prog_chunk_mine.json`,
`mbpp_zero_shot_baseline.json`, `mbpp_train_diet.json` — all gitignored,
copied read-only from the canonical tree, none touched by this rung's own
Rust or Python changes) before `scripts/mbpp_endgame_battery.py` could
run at all (its first two attempts failed outright with
`FileNotFoundError`, 0/257 runnable — reported here as an environment-setup
finding, not a code defect).

| arm | baseline | this rung | lost | gained |
|---|---|---|---|---|
| full | 88/257 | **89/257** | `[]` | `[242]` |
| content_stripped | 87/257 | **88/257** | `[]` | `[242]` |
| official | 115/257 | **116/257** | `[]` | `[242]` |

Task 242 ("count the total number of characters in a string") moved from
`gapped:enumerate_failed` to `pass` in every arm — a direct beneficiary of
the shrunk alphabet-driven leaf pool, the SAME class of task the PBE
corpus's `pbe_007`/similar counting shapes represent. **`lost_pass` is
empty in all three arms — the task's own hard gate is met.**

Both determinism checks (`det_identical`) reported `True` in every arm on
every run in this rung (two independent runs per arm, per the battery's
own built-in protocol) — the fix does not introduce nondeterminism.

---

## 6. Named 9-file regression suite

Run three times in this worktree: pre-fix (reverted engine, control),
v1 (no whitespace carve-out), and v2 (final, shipped). All three FIRST
required backfilling `results/prog_synthesis_battery.json`,
`results/mbpp_arc3_endgame.json`, and `results/arc4_structural_verdicts.json`
from the canonical tree (same gitignored-artifact situation as §5) before
any of the nine files' own frozen-artifact assertions could run at all.

**Top-level result on the shipped (v2) engine: 5 failed, 239 passed.**
The five: `test_prog_synthesis_battery_migrated.py::test_no_task_is_copied_from_the_p4_fixtures_or_the_frozen_battery`,
`::test_c_battery_continuity_no_ok_to_fail_regression`,
`test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live`,
`test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_drift`,
`test_exact_first_migrated.py::test_named_regression_sweep_only_known_pins_drift`
— more than the task brief's stated "3 known pins," reported precisely
rather than rounded down.

**This rung did not stop at the raw count — it ran the SAME 9-file suite
against the reverted (pre-fix) engine as a paired control, in this same
worktree, to separate "pre-existing environment drift" from "caused by
this patch."** Result: **byte-identical top-level failure set, all 5,** on
both engines. The two `test_named_regression_sweep_only_known_pins_drift`
tests each shell out to a WIDER subprocess sweep across many more test
files; extracting the exact `unexpected` node-id sets from both runs and
diffing them directly (not eyeballing the printed summary) gives **16
items on each side, 15 of which are IDENTICAL between pre-fix and
post-fix** (confirmed pre-existing, unrelated to this patch — most
plausibly the documented "a concurrent unrelated session lands work on
main throughout this whole arc" risk the task brief itself named, plus
this worktree's own artifact-backfill from a canonical tree that may be a
few commits ahead of `5494752`). **Exactly one item differs**: pre-fix,
`test_retrieval_migrated.py::test_ceiling_task_reproduces_measured_outcome_live[238]`
fails; post-fix, `[242]` fails instead of `[238]`. This is the SAME task
242 whose gap closed in the MBPP battery (§5) — `test_retrieval_migrated.py`
carries its own extensive, dated historical commentary specifically
about tasks 238/242 drifting together as retrieval/enumerate outcomes
shift (`grep 238\|242` in that file surfaces multiple prior
2026-08-01/2026-08-11/2026-08-16 entries already tracking exactly this
pair) — this is a well-precedented, directly-explained side effect of the
same improvement already verified in §5, not a new or surprising failure
mode, and `test_retrieval_migrated.py` is not one of the nine named
files.

**Conclusion: this patch's ENTIRE measured effect on the regression
suite, across all files reached by the 9 named files (directly or via
their own subprocess sweeps), is the single expected 238→242 swap.**
Everything else reported as "failing" was already failing on the
unmodified engine in this same worktree.

---

## 7. What this rung does NOT establish

1. `pbe_012` remains unresolved — this fix narrows the wall but does not
   close it for tasks that also need op-breadth (`Split`+`MapList`+`JoinList`
   together). Named, not fixed.
2. The exact magnitude of the alphabet-cost formula (`ceil(log2(N))`) was
   not swept against alternatives (a steeper or gentler curve) — this
   rung shipped the first well-motivated formula that cleared both
   corpora's gates, not a formula selected by comparing several.
3. The `Var(s)`-as-coerced-0 search-integrity residual
   (`PBE_STRING_BENCHMARK_RESULTS.md` §2.3) and the `pbe_004` rule-1
   scope gap (§2.4) are unrelated to this fix and remain open, exactly as
   that document left them.
4. This worktree's `results/*` artifact gaps (§5, §6) suggest the
   canonical tree and/or `main` have moved since the cited baseline
   artifacts were captured; this rung did not audit or reconcile that
   drift beyond what was needed to run its own paired comparisons
   correctly.
5. Whether other, larger-alphabet MBPP or PBE-shaped tasks exist where
   `ceil(log2(N))` is still too weak (or, conversely, too aggressive) was
   not swept beyond the specific tasks this rung's batteries already
   touch.

---

## 8. Recommendation

**GO — ship this rung's Rust change as-is; do not merge.** Both corpora
improve or hold steady with zero losses (`lost_pass` empty on MBPP in all
three arms, PBE zero losses in every arm), the SHAPES-NOT-NUMBERS
classification is stated and holds up against the actual code paths
checked, the regression suite's only patch-attributable delta is one
already-precedented, already-explained node swap outside the named nine
files, and the one real negative result found along the way (the v1
MBPP regression) was caught by this rung's OWN required battery, diagnosed
to its exact mechanism, and repaired with a second well-motivated,
evidence-independent protected category rather than papered over or
silently dropped. Left committed, unmerged, unpushed on
`alphabet-search-cost-wall` for the orchestrator's independent
re-verification.
