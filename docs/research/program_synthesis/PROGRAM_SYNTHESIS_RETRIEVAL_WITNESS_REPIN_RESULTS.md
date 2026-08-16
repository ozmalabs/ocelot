# Retrieval witness re-pin (412 → 440) — RESULTS: DONE

Prereg: `PROGRAM_SYNTHESIS_RETRIEVAL_WITNESS_REPIN_PREREG.md`, same
worktree/branch. Base `main @ aed1d12` ("Build hate attribution: outward
attribution-locus residual + stability gate"), verified fresh via `git log
--oneline -1 main` before creating the worktree. Worktree:
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/272b6058-8f21-4012-b852-d8348df69ff4/scratchpad/progsyn-retrieval-witness-repin`,
branch `progsyn-retrieval-witness-repin` — **not merged to `main`, not
pushed**, left for the orchestrator to independently verify and merge.

---

## Headline

**`tests/test_retrieval_migrated.py::test_ladder_gap_spends_no_attempt_when_
retrieval_finds_nothing` re-pinned from task 412 to task 440 ("find the
first adverb and their positions in a given sentence"), confirmed LIVE
(`status == "gapped"`, `rung == "none"`, `attempts == 0.0`, 3 repeated runs,
byte-identical). Full test file re-run after the edit: 32 passed, 1 failed
— the one failure is `test_ceiling_task_reproduces_measured_outcome_live
[238]`, independently re-confirmed as the SAME pre-existing, unrelated
drift already found by three prior rungs, byte-identical failure mode, on
the current tip before any edit. No production code touched. No Rust
rebuild. No MBPP battery run.**

---

## 1. Setup — gitignored artifacts copied from the canonical tree

`results/` is gitignored except for the explicitly whitelisted baseline
files, so a fresh worktree needs its own copy of every result artifact the
code under test reads at import/boot time. Copied from
`/home/matt/ozmadev/ocelot/results/` before running anything:

- `arc4_structural_verdicts.json`
- `mbpp_endgame.json` (head `aed1d12f9782217a80c7345a01848703d28eed1c` —
  byte-identical to this worktree's own `git log --oneline -1 main`,
  confirming it is a genuine fresh-tip measurement, not stale)
- `mbpp_zero_shot_baseline.json`
- `prog_construction_scan.json`
- `prog_chunk_mine.json` (needed by `scripts/ceiling3_diag_sweep.py`'s own
  `boot_full()`, not by the test file's own plain `boot()`)

`substrate_rs`'s compiled `_native.abi3.so` (`runners/dsl/python/
substrate_rs/_native.abi3.so`) is tracked in git — confirmed via `git
ls-files`, so no Rust rebuild was needed at any point in this rung, per
the task brief's own expectation.

---

## 2. Confirming the pre-edit state

`tests/test_retrieval_migrated.py`, unmodified, run fresh in this worktree:

```
2 failed, 31 passed
  FAILED test_ladder_gap_spends_no_attempt_when_retrieval_finds_nothing
  FAILED test_ceiling_task_reproduces_measured_outcome_live[238]
```

The first failure is `out["status"] == "accepted"` vs the pinned
`"gapped"` for task 412 — exactly the confirmed, understood, pre-existing
drift the task brief describes (`_KNOWN_CEILING_REASSESSMENT_5_DRIFT[412]`,
already in the file). The second is investigated in §5.

---

## 3. Search — 47 live-confirmed `rung: none` / `attempts: 0.0` candidates

`scripts/ceiling3_diag_sweep.py` (unmodified, its own gitignored
`prog_chunk_mine.json` dependency copied in) re-run fresh: 171 rows over
every currently-failing `full`-arm runnable task. 68 have `gap_reason ==
'enumerate_failed'` and `retrieval.rung_reached == 'none'` under the diag
sweep's own (heavier) `boot_full()`.

Every one of those 68, plus the `no_shape`/`exhausted` categories (7
sampled: 77, 126, 164, 222, 228, 256, 295), was independently re-verified
using the TEST FILE'S OWN `boot()` (plain `ensure_program_synthesis`, no
mined chunks, no train diet — genuinely different from `boot_full()`) and
its own `_run_task_live` logic, run as a standalone script during this
rung. Result:

- **`no_shape`/`exhausted` REJECTED as a class** — every sample spends
  `attempts` of 2.0 or 4.0 under the plain `boot()`, which directly
  disqualifies them (this test's own `attempts == 0.0` assertion, HR2).
- **47 of the 68 `enumerate_failed` candidates confirmed**: `status ==
  "gapped"`, `rung == "none"`, `attempts == 0.0` under the test's own
  `boot()`. (21 of the 68 diverge between the two boot paths — the
  heavier `boot_full()` changes which codebook constructions are
  eligible, so some tasks that read `rung: none`/`attempts: 0` under
  `boot_full()` do NOT under the test's own lighter `boot()`, and vice
  versa. This divergence is exactly why the task brief's own instruction
  to confirm LIVE against `_run_task_live`, not the diag sweep, matters.)

Confirmed candidate task ids (47): 18, 75, 97, 99, 102, 108, 117, 128, 137,
160, 163, 226, 229, 240, 251, 252, 255, 262, 265, 277, 280, 293, 297, 299,
301, 305, 307, 308, 310, 390, 391, 395, 408, 411, 417, 421, 427, 437, 439,
**440**, 442, 447, 459, 462, 465, 470, 478.

---

## 4. Choice — task 440, with the robustness reasoning named explicitly

Task 440's own reference implementation
(`tests/fixtures/mbpp/sanitized-mbpp.json`) is:

```python
import re
def find_adverb_position(text):
 for m in re.finditer(r"\w+ly", text):
    return (m.start(), m.end(), m.group(0))
```

Chosen over the other 46 confirmed candidates because its blocker is a
DIFFERENT KIND of gap than every prior witness this test has stood on.
394 (tuple/list concat) and 412 (a mod-2 filter predicate) were both
closed by adding a new COMPOSITION inside the DSL's existing arithmetic/
list Term algebra — `Fold`+`Append`, `Mod`+`Eq`+`Not` — the exact class of
widening this arc has landed repeatedly (`ConcatList`, `tmpl:item_mod_eq`,
and earlier `IntersectAll`/`UnionAll`/`DictFromPairs`/`ZipWith`, all same
shape). Task 440 needs regex match-object search — grep-confirmed absent
from `OP_TABLE` in `runners/dsl/src/synth_enumerate.rs` (arithmetic,
comparison, `Str`/`Split`/`Replace`/`Slice`/`CaseFold`, list/`Fold`/
`Filter`, `Mod`/`Sqrt` — nothing pattern-search-shaped).

This is not a fresh guess. This project's own prior population research
has already looked at exactly this gap, twice, independently:

- `PROGRAM_SYNTHESIS_ARC2_Q0_HISTOGRAM.md` names `regex` as the single
  LARGEST unrestricted-curve capability family in the whole MBPP
  population (26 tasks, tied for the #1 step) and explicitly excludes it:
  *"regex is a genuinely new object model (match objects, `re.Match`
  methods), explicitly out of the arc's scope (plan §1, risk #5)."*
- `PROGRAM_SYNTHESIS_OPERATOR_SHAPE_WITNESS_CHECK_PREREG.md` (the
  same-day predecessor to the rung that converted 412) independently
  buckets task 440 into the same excluded family from a different
  angle — its own residual-population list groups 440 among tasks that
  "each need a genuinely different missing primitive or composition
  (groupby-aggregate, `Range`/iteration, **regex**, trig functions,
  recursion, dict-depth, format-string application, sliding-window,
  combinations, etc.)."

**Stated explicitly, per the task brief's own request, and NOT provable
with certainty:** every widening actually landed in this arc has stayed
inside one Term family (arithmetic/list/string composition); regex needs a
genuinely different value type and search semantics that this project's
own research has twice classified as architecturally out of the current
scope. That is a materially stronger claim than "this specific op
combination happens not to exist yet" (which was true of 394/106/412
right up until it wasn't). No witness is provably permanent — the
docstring says so explicitly, again, for whoever moves this next.

Other candidates considered and set aside as LESS durable (still valid
candidates, just weaker robustness arguments): 99 (decimal→binary, needs
unbounded iteration — a shape gap, not a new object model), 301 (dict
depth, needs recursion over nested structure), 255/462 (combinatorial
generation, needs exponential/backtracking construction), 308 (top-k over
a cross product — plausibly just a cross-product-then-sort-then-take
template away, the same shape as the `tmpl:item_mod_eq` fix that just
landed).

---

## 5. Live confirmation

Standalone script mirroring `_run_task_live` verbatim, run 3 times in this
worktree:

```
revealed: [{'inputs': {'a': 'clearly!! we can see the sky'}, 'expected': (0, 7, 'clearly')},
           {'inputs': {'a': 'seriously!! there are many roses'}, 'expected': (0, 9, 'seriously')}]
held_out: [{'inputs': {'a': 'unfortunately!! sita is going to home'}, 'expected': (0, 13, 'unfortunately')}]

run 0: status=gapped gap_reason=enumerate_failed attempts=0.0
       retrieval={'rung_reached': 'none', 'n_candidates': 5.0, 'accept_task_id': None,
                  'accept_perm': None, 'accept_edit': None}
run 1: identical
run 2: identical
```

Deterministic. Retrieval scored 5 candidates into its pool but accepted
none at any rung; enumerate independently exhausted its full 200000-
candidate search budget without a fit (per `results/ceiling3_diag_
sweep.json`'s own row for task 440: `tested: 200000, distinct: 5365`). Both
sides of the ladder genuinely find nothing, not merely an empty pool — the
strongest form of "finds nothing" available in this engine.

---

## 6. Task 238 — confirmed still the same pre-existing, unrelated drift

Re-run fresh in this worktree, on `main @ aed1d12`, before any edit:

```
FAILED test_ceiling_task_reproduces_measured_outcome_live[238]
  AssertionError: assert 'enumerate_failed' == 'structural_verdict_reject'
```

Byte-identical assertion, byte-identical field (`gap_reason`), byte-
identical values, to the failure `PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_
5_RESULTS.md` §6.5 already confirmed pre-existing and unrelated on `main @
84cd082` (itself citing `PROGRAM_SYNTHESIS_ZIPWITH_FOLLOWON_RESULTS.md`
§5.2 confirming it one rung earlier still, on `main @ bc0ac10`) —
i.e. confirmed unchanged across at least four rungs now, on the current
tip, one commit further (`aed1d12` vs `84cd082`) than the last check. Per
the task brief, this is out of scope for this rung and was NOT touched.

---

## 7. The change

`tests/test_retrieval_migrated.py`, one function:
`test_ladder_gap_spends_no_attempt_when_retrieval_finds_nothing` — the
`_run_task_live(by_id[412])` call re-pointed to `by_id[440]`, and the
docstring rewritten following the exact discipline of the 394→106 and
106→412 updates already in the file (why the old witness stopped working,
live confirmation of the new one, the robustness reasoning from §4, the
same "confirm LIVE, never inherit" warning for the next mover). No other
test, no seed, no production code changed.

---

## 8. Verification

```
PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 -m pytest --confcutdir=. tests/test_retrieval_migrated.py -q

1 failed, 32 passed
  FAILED test_ceiling_task_reproduces_measured_outcome_live[238]  (pre-existing, §6, out of scope)
```

Exactly the expected outcome per the task brief: fully green except task
238's own confirmed-pre-existing failure, nothing else new, nothing else
broken.

**Not run in this rung (deliberately out of scope):** the "named 9-file
suite" that invokes this file as a subprocess
(`tests/test_exact_first_migrated.py`, `tests/test_prog_moves_migrated.py`,
`tests/test_prog_property_migrated.py`) — those meta-tests already carry
task 238's failure as one of their own "known pre-existing" counts (per
`PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_5_RESULTS.md` §6.5's "3 failed /
241 passed" line), and this rung's edit does not change that count (238's
failure mode is identical before and after; 412's own failure — previously
one of the 2 "new, intended" failures that rung reported — is now clean).
No Rust rebuild, no MBPP battery run, per the task brief's own expectation
that this task needs neither.

---

## 9. What is NOT established

- Task 440's `rung: none` status is not provably permanent — no witness in
  this test's history has been. The reasoning in §4 is the best available
  evidence in this codebase (two independent prior research documents
  naming regex as architecturally out of scope), not a proof.
- The other 46 live-confirmed candidates were not exhaustively ranked
  against each other beyond the qualitative "same Term family vs.
  different object model" split in §4 — a more rigorous ranking (e.g. by
  estimated engineering distance from `OP_TABLE`) was not attempted and
  was not needed to pick a defensible witness.
- Whether `boot_full()`'s divergence from the test's own `boot()` (21 of
  68 `enumerate_failed` candidates disagree between the two) indicates a
  bug or an intentional difference in what the two boot paths install was
  not investigated — out of scope for this rung, noted for whoever next
  works on `ceiling3_diag_sweep.py` or the mined-chunk/train-diet install.
