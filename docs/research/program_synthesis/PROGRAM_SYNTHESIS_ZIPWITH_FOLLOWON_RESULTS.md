# ZIPWITH_FOLLOWON — RESULTS: GO on both causes, all 8 original
   `ZIP_ELEMENTWISE` witness tasks convert, zero regressions

Prereg: `PROGRAM_SYNTHESIS_ZIPWITH_FOLLOWON_PREREG.md`, same worktree/
branch. Base `main @ bc0ac10`, verified fresh via `git log --oneline -1
main` before creating the worktree. Worktree: `/home/matt/ozmadev/ocelot-
worktrees/progsyn-zipwith-followon`, branch `progsyn-zipwith-followon` —
**not merged to `main`, not pushed**, left for the orchestrator to
independently verify and merge.

---

## Headline

**GO on both causes. Full paired MBPP battery: `full` 76→84/257,
`content_stripped` 75→83/257, `official` 101→109/257 — all THREE arms gain
the EXACT SAME 8 task ids (`259, 261, 273, 282, 399, 401, 429, 445` — the
complete original `ZIP_ELEMENTWISE` witness cluster, every one of the 8),
zero lost on any arm.** Two independent, narrowly-scoped fixes:

1. **Cause 1 (5 retrieval-blocked tasks) — a real bug, not a missing
   fallback mechanism.** The property-reject-style enumerate-fallback
   pattern this rung was asked to re-test WAS re-tested, live, against all
   5 target tasks (`scripts/zip_structural_probe.py`) — and surfaced a
   precise, checkable, previously-undiagnosed false positive: `D2
   dead_code_free_vars` fires on `ZipWith`'s OWN bound variables
   (`__za`/`__zb`), because `domains/prog_synthesis.py::_st_bound_names`
   never learned `ZipWith`'s binder-field-naming convention
   (`a_name`/`b_name`, a THIRD convention alongside the existing
   `var_name`/`acc_name`). **Fixed with an 11-line, provably-scoped
   addition to `_st_bound_names`** (the attribute names `a_name`/`b_name`
   appear on no other Term in the engine, so the fix is a byte-identical
   no-op for every non-`ZipWith` candidate). Once fixed, **no new seed
   rule was needed at all** — the ALREADY-EXISTING, unmodified rung-(d)
   retrieval-ladder masked-hole enumerate probe (`domains/prog_
   retrieval.py`) already finds the exact correct `ZipWith` candidate for
   all 5 tasks; it was only ever being wrongly rejected.
2. **Cause 2 (3 nested tasks) — a narrow, `max_candidates`-only, `ZipWith`-
   op-list-gated raise.** `runners/dsl/src/synth_enumerate.rs` gains a
   `ZIP_MAX_CANDIDATES: u64 = 300_000` constant, applied only when (a) the
   call's own resolved op list contains `ZipWith` AND (b) the caller asked
   for the engine's own default budget (never overriding an explicit
   caller-supplied ceiling). Confirmed live: the 3 nested tasks need
   261,316–261,322 candidates tested (vs. the 200,000 default); every
   OTHER `SynthEnumerate` call site in the pipeline is either structurally
   incapable of reaching a `ZipWith` template at its own `max_size`
   ceiling, already resolves via cause 1's fix, or already supplies an
   explicit budget the gate is designed to leave untouched — confirmed by
   a full call-site audit (PREREG §4.4), the same class of check
   `MODSQRT_SCOPED_FIX_RESULTS.md` needed twice, done here once, up front.

**Both fixes together net +8/+8/+8 with an exact, live-verified,
zero-regression task-id set diff on all three arms** — a substantially
larger and cleaner conversion than either the task brief's own framing
("even 1 real conversion is worth reporting") or `ZIP_ELEMENTWISE_
RESULTS.md`'s own honest NULL anticipated.

---

## 1. Re-deriving the population — confirmed against the current baseline

Fresh battery run, this worktree, before any code change:

```
full:              76/257  p=0.29572   ci=[0.243264, 0.354192]  det_identical=True
content_stripped:  75/257  p=0.291829  ci=[0.239641, 0.350148]  det_identical=True
official:         101/257  p=0.392996  ci=[0.335279, 0.453865]  det_identical=True
```

Byte-identical to the task brief's cited baseline and to `ZIP_ELEMENTWISE_
RESULTS.md` §2's own figure — nothing moved on `main` between that rung's
merge (`8f2c054`) and this one's start, at `bc0ac10`. Per-task trace
confirmed the 5+3 split holds task-for-task against the CURRENT baseline,
byte-identical to `ZIP_ELEMENTWISE_RESULTS.md` §3's own trace (PREREG §2).

---

## 2. Cause 1 — the D2 binder-recognition bug, found live, fixed,
   re-verified

Full mechanism, the probe's own before/after evidence, and the exact fix
are in `PROGRAM_SYNTHESIS_ZIPWITH_FOLLOWON_PREREG.md` §2-§3 — not
duplicated here. Summary of what was independently verified:

- **Before the fix**: `scripts/zip_structural_probe.py`, mirroring
  `STRUCTURAL_REJECT_SURVEY_PREREG.md` §3.2's own already-built-and-
  measured `structural_probe.py` methodology exactly (same 4 effects
  `ps_property_reject_retrieval_enumerate_fallback` uses, same staleness
  reset), against all 5 target tasks: the independent second (enumerate)
  candidate for ALL 5 IS the exact correct `ZipWith`-based reference
  program, byte-for-byte — and is STILL rejected, `ps_st_fired_detectors:
  ['d2_dead_code_free_vars']` on every one.
- **Root cause, read directly**: `_st_bound_names` recognizes
  `var_name`/`acc_name` as generic binder-field names (used by every
  plain-DSL HOF binder) but was never extended for `ZipWith`'s own THIRD
  convention, `a_name`/`b_name` (`reflect.rs:415-421`). Confirmed by grep
  (zero pre-fix hits for `a_name`/`b_name` in `domains/prog_synthesis.py`)
  and by direct comparison against the reflected Term's own attrs.
- **The fix**: two more unconditional `attrs.get(...)` checks, mirroring
  the existing `var_name`/`acc_name` pair exactly. Provably scoped (not
  just empirically): `a_name`/`b_name` appear on no Term type in this
  engine other than `ZipWith`, and `ZipWith` did not exist before its own
  merge — no candidate anywhere in the corpus prior to that merge could
  ever carry these attrs, so the fix is a structural no-op for every
  non-`ZipWith` candidate.
- **After the fix**: re-running the SAME probe shows all 5 tasks reach
  `status: accepted` on their FIRST attempt (`eligible: False` in the
  probe's own output — the fallback-effects code path is never reached
  because the goal is no longer `gapped` at all), via the **already-
  existing, unmodified rung-(d) retrieval-ladder** (`domains/prog_
  retrieval.py:602-618`, `max_size:7, max_candidates:0`, no explicit
  `ops`). Holdout verified `True` for all 5, exact reference-matching
  `ZipWith` term for each. **No new seed rule was built — cause 1 needed
  ONLY the 11-line Python bug fix.**
- **A related, NOT fixed, out-of-scope finding**: `_st_bound_names` has an
  analogous, PRE-EXISTING gap for `IndexedMap` (`item_name`/`index_name`,
  a FOURTH binder-field convention, older than this rung). Confirmed no
  current MBPP structural-reject trace involves `IndexedMap`; named, not
  fixed, per this arc's single-variable-rung discipline.

---

## 3. Cause 2 — the narrow `max_candidates` raise, confirmed both
   directions

Full design and the cross-lane call-site audit are in the PREREG §4 — not
duplicated here. Summary:

- `max_size` is NOT the bottleneck (already `9`, exactly matching the
  nested template's own registration size). Only `max_candidates` needs
  raising — confirmed live: 261,316–261,322 tested to solve, vs. the
  200,000 default.
- The fix (`ZIP_MAX_CANDIDATES: u64 = 300_000`, ~15% headroom) applies
  ONLY when the call's own resolved `op_list` contains `ZipWith` AND the
  caller passed `max_candidates <= 0` ("give me the engine default").
- **Confirmed live, both directions**: the 3 nested tasks solve at
  261,316-261,322 tested under `max_candidates:0` (would have been
  budget-halted at 200,000 before this fix); an EXPLICIT smaller budget
  (`max_candidates:50000`) on the SAME `ZipWith`-eligible spec (task 259)
  is honoured exactly (`found=False, halt=budget` at 50,000) — the raise
  never overrides a caller's own explicit choice; two non-`ZipWith`
  canaries (tasks 132, 11 — string-shaped and list-shaped-but-not-
  zip-eligible respectively) are unaffected (`zip_wanted_for_budget=
  False`).
- **Cross-lane audit** (PREREG §4.4): every `SynthEnumerate` call site in
  the pipeline read directly. The ONLY call site this raise actually
  changes behaviour for is `run_enumerate`'s own top-level call — every
  other call site either cannot register a `ZipWith` template at its own
  `max_size` ceiling (`prog_retrieval.py` rung (d) and `prog_synthesis.py`
  `_solve_arm`, both `max_size:7` — flat-only, and the flat tasks are
  already resolved by cause 1's fix at those exact call sites well under
  200,000), already supplies an explicit budget (`prog_moves.py`'s
  `_PROBE_MAX_CANDIDATES`-scoped probes), or has a spec shape that
  structurally cannot satisfy `spec_has_two_zippable_list_vars`
  (`prog_moves.py`'s `intermediate_factor` inner probe — single scalar
  var). No cross-lane regression risk of the `MODSQRT_SCOPED_FIX` class
  exists.

---

## 4. Full paired MBPP battery — exact task-id set diffs

Method: `results/mbpp_endgame_BEFORE_this_rung.json` (captured on
unmodified `main @ bc0ac10`, this worktree, before any code change) vs.
`results/mbpp_endgame.json` (both fixes applied), both via `scripts/
mbpp_endgame_battery.py`, unmodified. Reproduced twice (once immediately
after both fixes landed, once again as the final authoritative run after
an isolation-testing detour — see §5.2) — byte-identical both times.

```
                    before (k/n)         after (k/n)          det_identical
full:               76/257  p=0.29572    84/257  p=0.326848    True / True
content_stripped:   75/257  p=0.291829   83/257  p=0.322957    True / True
official:          101/257  p=0.392996  109/257  p=0.424125    True / True
```

**Exact task-id set diff, all three arms, direct set computation (never
bare counts):**

| arm | gained | lost |
|---|---|---|
| `full` | `{259, 261, 273, 282, 399, 401, 429, 445}` | `{}` |
| `content_stripped` | `{259, 261, 273, 282, 399, 401, 429, 445}` | `{}` |
| `official` | `{259, 261, 273, 282, 399, 401, 429, 445}` | `{}` |

**All 8 of the original `ZIP_ELEMENTWISE` witness cluster's own target
tasks convert, on all three arms, with an EMPTY lost-set on every arm** —
a genuine, clean +8/+8/+8, not churn. The `official` arm gaining the
IDENTICAL 8-task set as `full`/`content_stripped` (rather than a different
subset, which `MODSQRT_SCOPED_FIX_RESULTS.md`/`PROPERTY_REJECT_SURVEY_
RESULTS.md` both measured for their own rungs) is itself notable — both
fixes here are structural/budget corrections to an EXISTING, already-
correct candidate-discovery mechanism rather than a change to WHICH
candidates get discovered in the first place, so the `official` arm's own
documented protocol difference (revealing all parseable asserts) does not
change which of these 8 tasks' candidates clear the fixed checks.

---

## 5. Regression discipline

### 5.1 Rust suite

```
RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/opt/python@3.13/lib -lpython3.13" \
LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/opt/python@3.13/lib:$LD_LIBRARY_PATH" \
cargo test --lib --release -- --test-threads=1
```

**778 passed; 0 failed; 4 ignored** — byte-identical to the documented
778-baseline. Genuine from-source rebuild confirmed non-cached (`touch`ed
`synth_enumerate.rs`, 2m06s-2m17s across 4 separate genuine rebuilds this
rung, see §5.2). `bash scripts/engine_build.sh` installed; `record_build()`
+ `pytest tests/test_engine_provenance_migrated.py` both green each time.

### 5.2 An isolation trace, run live, that found and cleared ONE
   pre-existing, unrelated test-pin drift — reported in full

The named 9-file suite's own wider internal sweep (`test_exact_first_
migrated.py::test_named_regression_sweep_only_known_pins_drift`'s own
body, the SAME "shared mutable output path" fragility `CEILING_
REASSESSMENT_3_RESULTS.md` §6 and every subsequent rung in this arc has
re-confirmed present on clean `main`) flagged `tests/test_retrieval_
migrated.py::test_ceiling_task_reproduces_measured_outcome_live[238]` — a
hardcoded pin (`_KNOWN_ARC6_PROPERTY_REJECT_DRIFT[238]`, set by
`PROPERTY_REJECT_SURVEY_RESULTS.md` at `gap_reason: 'structural_verdict_
reject'`) now reading `gap_reason: 'enumerate_failed'` live.

**Investigated directly rather than assumed either "caused by this rung"
or "pre-existing" — both fixes were isolated one at a time, live, in this
SAME worktree** (matching `MODSQRT_SCOPED_FIX_RESULTS.md`/`PROPERTY_
REJECT_SURVEY_RESULTS.md`'s own precedent for exactly this class of
check):

```
BOTH fixes present:                        task 238 -> gap_reason=enumerate_failed
Rust fix present, Python fix reverted:      task 238 -> gap_reason=enumerate_failed  (unchanged)
Rust fix reverted, Python fix present:      task 238 -> gap_reason=enumerate_failed  (unchanged)
NEITHER fix present (byte-identical main):  task 238 -> gap_reason=enumerate_failed  (unchanged)
```

**Task 238's drift is confirmed PRE-EXISTING on unmodified `main @
bc0ac10` itself, reproduced identically in all four configurations —
neither fix in this rung touches it.** (Mechanistically plausible: task
238's own spec has exactly ONE declared variable — a string — so it
cannot satisfy `spec_has_two_zippable_list_vars`'s own ≥2-distinct-vars
requirement, and no `ZipWith` node appears anywhere in its candidate
trace, confirmed by a full `SynthEnumerate`-call-logging trace showing all
3 calls use `ops: None` i.e. the typed default, none reachable via either
fix's own gate.) This test pin was already stale before this rung began —
some other change on `main` between `PROPERTY_REJECT_SURVEY`'s merge and
`bc0ac10` shifted task 238's own outcome, and this specific file's pin was
never refreshed. **Not fixed here** (out of this rung's own scope — an
unrelated, pre-existing pin, the SAME "confirmed pre-existing, unrelated"
disposition `MODSQRT_SCOPED_FIX_RESULTS.md` §5.2/`PROPERTY_REJECT_SURVEY_
RESULTS.md` §7 both reached for their own analogous drift, reported
honestly rather than silently absorbed or force-fixed).

**Named 9-file regression suite — top-level result, reproduced twice,
byte-identical both times:**

```
3 failed, 241 passed in ~278-296s
FAILED tests/test_mbpp_baseline_migrated.py::test_three_runnable_tasks_reverify_live
FAILED tests/test_prog_moves_migrated.py::test_named_regression_sweep_only_known_pins_drift
FAILED tests/test_exact_first_migrated.py::test_named_regression_sweep_only_known_pins_drift
```

**Exactly the 3 known pre-existing pin-drift failures named in the task
brief — nothing new.** (The wider internal sweep's own 14-item detail list
surfaces INSIDE the third of these 3 failures' own assertion output, as
diagnostic context, not as separate top-level failures — matching every
prior rung in this arc's own handling of this same fragility, per §5.2's
own spot-check above.)

### 5.3 `tests/test_retrieval_migrated.py` and `tests/test_reject_
   informs_repair_migrated.py`

Run per the task brief's own instruction (touches the retrieval-adjacent
structural-fact machinery), reproduced twice, byte-identical both times:

```
tests/test_retrieval_migrated.py:            49 passed, 1 failed
  FAILED test_ceiling_task_reproduces_measured_outcome_live[238]   -- confirmed PRE-EXISTING, §5.2
tests/test_reject_informs_repair_migrated.py: exactly its 4 known pre-existing failures
  FAILED test_retrieval_sourced_ids_gap_directly_never_reopen
  FAILED test_reopened_ids_genuinely_tried_and_still_gapped_honestly
  FAILED test_disposition_a_repaired_to_pass_is_empty
  FAILED test_no_wrong_accept_regression_vs_v1_7_0_baseline
5 failed, 50 passed in ~75s
```

**`test_reject_informs_repair_migrated.py` matches the task brief's
expectation exactly (its 4 known pre-existing failures, nothing new).
`test_retrieval_migrated.py`'s single failure is confirmed, live, in §5.2
above, to be PRE-EXISTING drift unrelated to either fix in this rung** —
the task brief's own "expect fully green" framing was written before this
unrelated drift had accumulated on `main` (the task brief itself warns
"a concurrent unrelated session lands work on main throughout this whole
arc," which is exactly the kind of drift source this isolation trace
rules in/out mechanically rather than assumes).

---

## 6. What this document does NOT establish

Carried forward from the PREREG §6, unchanged by the battery/regression
results above:

1. Whether the `IndexedMap` `item_name`/`index_name` D2 gap (§2 above)
   affects any CURRENT MBPP task beyond this rung's own checked absence —
   not fixed, not further swept.
2. Whether `ZIP_MAX_CANDIDATES:300_000`'s own ~15% headroom is the RIGHT
   margin in general — chosen for comfortable safety over the measured
   ceiling, not independently tuned.
3. Whether any MBPP task OUTSIDE the original 8-task `ZIP_ELEMENTWISE`
   witness cluster is affected by either fix — the full 257-task battery
   (§4) is the authoritative, population-wide, unsampled check, and found
   none.
4. What OTHER, unrelated pin drift may exist on `main` at `bc0ac10` beyond
   the ONE instance (task 238) this rung's own regression discipline
   happened to surface and isolate — no broader audit of test-pin
   staleness was performed.
5. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

---

## 7. GO/NO-GO

**GO on both causes.** Cause 1 needed a real bug fix (`_st_bound_names`
gains `ZipWith`'s own `a_name`/`b_name` binder recognition, 11 lines,
provably scoped) and, once fixed, no new seed rule at all — the
already-existing retrieval ladder already finds the correct candidate.
Cause 2 needed a narrow, `ZipWith`-op-list-gated, caller-default-only
`max_candidates` raise (Rust, one constant + one gated override, 50
lines including comments) — confirmed via a full call-site audit to
carry zero cross-lane regression risk of the `MODSQRT_SCOPED_FIX` class.
**Measured result: `full` 76→84/257, `content_stripped` 75→83/257,
`official` 101→109/257, all three arms gaining the IDENTICAL 8-task set
(`259, 261, 273, 282, 399, 401, 429, 445` — the complete original
`ZIP_ELEMENTWISE` witness cluster) with an empty lost-set on every arm.**
Rust suite 778/0/4 (byte-identical to baseline). Named 9-file suite 3
failed/241 passed (exactly the 3 known pre-existing pin-drift failures).
`test_reject_informs_repair_migrated.py` shows exactly its 4 known
pre-existing failures. `test_retrieval_migrated.py`'s single failure was
investigated live, not assumed, and confirmed PRE-EXISTING on unmodified
`main`, reproduced identically across all 4 fix-combinations tested,
unrelated to either fix in this rung.

**State left in the worktree**: both source diffs
(`domains/prog_synthesis.py`, `runners/dsl/src/synth_enumerate.rs`)
committed; `results/mbpp_endgame.json` reflects the AFTER state;
`results/mbpp_endgame_BEFORE_this_rung.json` preserved for the diff;
`scripts/zip_structural_probe.py` (the live probe from PREREG §2.1)
committed for reproducibility; engine `.so` in `runners/dsl/python/
substrate_rs/` reflects the final build.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-zipwith-followon
git log --oneline -1   # on top of main @ bc0ac10
```

```bash
bash scripts/engine_build.sh
python3 -c "import sys; sys.path.insert(0, '.'); from domains.engine_provenance import record_build; print(record_build())"
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 scripts/mbpp_endgame_battery.py
RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/opt/python@3.13/lib -lpython3.13" \
  LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/opt/python@3.13/lib:$LD_LIBRARY_PATH" \
  cargo test --lib --release -- --test-threads=1
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 -m pytest tests/test_prog_synthesis_battery_migrated.py tests/test_mbpp_baseline_migrated.py \
  tests/test_mbpp_endgame_migrated.py tests/test_mbpp_contamination_migrated.py tests/test_mbpp_diet_migrated.py \
  tests/test_program_synthesis_migrated.py tests/test_prog_moves_migrated.py tests/test_prog_property_migrated.py \
  tests/test_exact_first_migrated.py -q --tb=line -rf
PYTHONPATH="runners/dsl/python:.:scripts" OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 \
  python3 -m pytest tests/test_retrieval_migrated.py tests/test_reject_informs_repair_migrated.py -q --tb=line -rf
```

The task-238 isolation trace (§5.2) is reproducible by swapping
`domains/prog_synthesis.py`/`runners/dsl/src/synth_enumerate.rs` for
`git show HEAD~1:...`-style originals one at a time (rebuilding the
engine between Rust swaps) and re-running the single-task probe inline in
this document's own §5.2.
