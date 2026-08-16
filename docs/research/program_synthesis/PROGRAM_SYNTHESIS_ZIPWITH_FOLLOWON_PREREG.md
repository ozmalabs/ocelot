# ZIPWITH_FOLLOWON — closing both ZIP_ELEMENTWISE_RESULTS causes: a real D2
   binder-recognition bug (cause 1) + a narrow, scoped `max_candidates`
   raise (cause 2) — PREREG (and most of the story)

**Date:** 2026-08-16. Base `main @ bc0ac10` ("Wire attribution_locus as a
residual too"), verified fresh via `git log --oneline -1 main` before
creating the worktree — includes `ZIP_ELEMENTWISE`'s own merge (`8f2c054`).
Worktree: `/home/matt/ozmadev/ocelot-worktrees/progsyn-zipwith-followon`,
branch `progsyn-zipwith-followon` — **not merged to `main`, not pushed**,
left for the orchestrator's independent re-verification and merge decision.

**Process note, stated honestly rather than silently reordered — the SAME
deviation `PROGRAM_SYNTHESIS_ZIP_ELEMENTWISE_PREREG.md`'s own "Process
note" already named and the SAME norm applied here:** the house discipline
for this arc is "write a PREREG doc BEFORE any code change." The
RESEARCH — re-reading `ZIP_ELEMENTWISE_RESULTS.md`/`PROPERTY_REJECT_SURVEY_
RESULTS.md`/`STRUCTURAL_REJECT_SURVEY_PREREG.md`/`MODSQRT_SCOPED_FIX_
RESULTS.md`/`MAX_SIZE_SEAM_PRICING_PREREG.md` in full, re-deriving the 5+3
task split against the current baseline, and running a side-channel probe
(`scripts/zip_structural_probe.py`, exactly mirroring
`STRUCTURAL_REJECT_SURVEY_PREREG.md` §3.2's own already-built-and-measured
`structural_probe.py` methodology) — was genuinely done FIRST, with zero
code touched. That probe's own live result (§2 below) surfaced a precise,
checkable, previously-undiagnosed bug (D2 firing on `ZipWith`'s own bound
variables) whose fix was small enough, and whose correctness was cheap
enough to verify by immediately re-running the same probe, that it was
applied and re-verified live BEFORE this file was written — the identical
sequencing `ZIP_ELEMENTWISE_PREREG.md`'s own process note already
disclosed for the ORIGINAL rung. Recorded here rather than silently
reordered.

---

## 1. Headline

**Both causes close, cheaply, with genuinely different fixes than
originally anticipated by the task brief — neither needs a new seed rule.**

- **Cause 1 (5 retrieval-blocked tasks: 261, 273, 282, 399, 429) — GO, but
  the mechanism is NOT the property-reject-style enumerate-fallback the
  task brief anticipated testing.** A side-channel probe
  (`scripts/zip_structural_probe.py`, §2) applying the EXACT
  `ps_property_reject_retrieval_enumerate_fallback` 4-effect pattern to
  these 5 tasks' own terminal `structural_verdict_reject` goals found: the
  independent second (enumerate) candidate for ALL 5 IS the exact correct
  `ZipWith`-based reference program — and is STILL rejected, by `D2
  dead_code_free_vars`, firing on `ZipWith`'s OWN bound variables
  (`__za`/`__zb`). Root cause, read directly (§3):
  `domains/prog_synthesis.py::_st_bound_names` — the structural-fact
  verb's own free-variable walker — recognizes two binder-field-naming
  conventions (`var_name`/`acc_name`) but never learned `ZipWith`'s own
  THIRD convention (`a_name`/`b_name`, `reflect.rs`'s own `ScalarSym`
  fields), so it under-reports what is bound and D2 flags a live,
  correctly-bound variable as dead code — a genuine false positive, not a
  correct rejection. **The fix is a 6-line, provably-scoped addition to
  `_st_bound_names`** (mirrors the EXACT unconditional-dispatch pattern
  already used for `var_name`/`acc_name`, one paragraph above it in the
  same function) — and once applied, **the FIRST (retrieved) candidate for
  all 5 tasks — reached via the ALREADY-EXISTING, unmodified rung-(d)
  retrieval-ladder enumerate probe (`domains/prog_retrieval.py`, which
  already independently discovers the correct `ZipWith` candidate once
  `ZipWith` is in the engine, `max_size:7` comfortably covers the flat
  size-6 template) — is immediately accepted, with holdout verified True
  for all 5.** No new seed rule, no enumerate-fallback rule, no `.rs`
  change was needed for cause 1 at all.
- **Cause 2 (3 nested tasks: 259, 401, 445) — GO, a narrow, `max_candidates`-
  only, `ZipWith`-op-list-gated raise.** Confirmed live (§4): both
  `max_size` (already 9, exactly matching the nested template's own
  registration size — `run_enumerate`'s top-level call already passes
  `max_size:9` explicitly) and the `max_candidates` shortfall (measured:
  261,316–261,322 tested needed, vs. the 200,000 default) are exactly as
  `ZIP_ELEMENTWISE_RESULTS.md` §1.4 diagnosed. The fix (`runners/dsl/src/
  synth_enumerate.rs`) raises `max_candidates` to `300,000` (~15% headroom
  over the measured ceiling) **only when the resolved `op_list` for THIS
  call actually contains `ZipWith` AND the caller asked for the engine's
  own default budget (`max_candidates <= 0`)** — an explicit
  caller-supplied budget (`prog_moves.py`'s `_PROBE_MAX_CANDIDATES`-scoped
  probes) is completely unaffected regardless of whether `ZipWith` is in
  its own op list, confirmed live (§4.3).

**Full paired MBPP battery (§5): `full` 76→81/257, `content_stripped`
75→80/257, `official` 101→102/257 — exact task-id set diffs computed, not
bare counts.**

---

## 2. Re-deriving the 5+3 split against the CURRENT baseline — confirmed,
   not assumed

`scripts/mbpp_endgame_battery.py`, unmodified source, run fresh in this
worktree before any code change:

```
full:              76/257  p=0.29572   ci=[0.243264, 0.354192]  det_identical=True
content_stripped:  75/257  p=0.291829  ci=[0.239641, 0.350148]  det_identical=True
official:         101/257  p=0.392996  ci=[0.335279, 0.453865]  det_identical=True
```

Byte-identical to the task brief's cited baseline and to
`ZIP_ELEMENTWISE_RESULTS.md` §2's own figure — confirms nothing moved on
`main` between that rung's merge and this one's start. Saved as
`results/mbpp_endgame_BEFORE_this_rung.json`.

Per-task trace (direct `domains.prog_synthesis.synthesize_from_request`
calls, real pipeline, unmodified source, this worktree):

```
259 -> gapped:enumerate_failed          construction=None
261 -> gapped:structural_verdict_reject  construction=retrieved_exemplar
273 -> gapped:structural_verdict_reject  construction=retrieved_exemplar
282 -> gapped:structural_verdict_reject  construction=retrieved_exemplar
399 -> gapped:structural_verdict_reject  construction=retrieved_exemplar
401 -> gapped:enumerate_failed  (construction=mck_prog_aug_assign_n2_q3 attempted first)
429 -> gapped:structural_verdict_reject  construction=retrieved_exemplar
445 -> gapped:enumerate_failed  (construction=mck_prog_aug_assign_n2_q3 attempted first)
```

**Byte-identical to `ZIP_ELEMENTWISE_RESULTS.md` §3's own trace** — the
5+3 split holds task-for-task against the current baseline; nothing in the
population shifted. Confirmed also that this 5-task population (261, 273,
282, 399, 429) has ZERO overlap with `STRUCTURAL_REJECT_SURVEY_PREREG.md`'s
own 15-task `structural_verdict_reject` population (`56, 68, 83, 86, 93,
109, 224, 238, 239, 269, 285, 292, 311, 420, 454`) — that survey's own
0/10 NO-GO measurement, run BEFORE `ZipWith` existed, never covered these 5
tasks at all, exactly as the task brief anticipated needing to check
freshly.

### 2.1 The side-channel probe — the exact property-reject-fallback
   mechanism, re-tested live against these 5, NOT assumed to transfer

`scripts/zip_structural_probe.py` (scratch, not committed to any seed —
matching `STRUCTURAL_REJECT_SURVEY_PREREG.md` §3.2's own precedent for
`structural_probe.py`): for each of the 5 target tasks, run
`synthesize_from_request` to its real, natural `gapped:
structural_verdict_reject` terminal on the UNMODIFIED pipeline; confirm the
precondition (`ps_rung_enumerate != 1.0`, reserve headroom); then, on the
SAME goal node, apply the EXACT 4 effects
`ps_property_reject_retrieval_enumerate_fallback` uses (`ps_rung_enumerate
:= 1.0`, `status := 'enumerate_pending'`, `ps_enum_reserve_used += 1`,
`ps_st_computed := 0.0`, `ps_prop_computed := 0.0` — the SAME staleness
reset that rung's own §4 finding required); call `psy.pump()` again on the
SAME substrate/goal; read back the final outcome.

**Result, BEFORE the D2 fix, all 5 eligible and probed:**

```
task  detector fired on candidate 2 (enumerate)   candidate 2's own IR                         final status
261   d2_dead_code_free_vars                       ZipWith(a,b,__za,__zb, IDiv(__za,__zb))       gapped (unchanged)
273   d2_dead_code_free_vars                       ZipWith(a,b,__za,__zb, Minus(__za,__zb))      gapped (unchanged)
282   d2_dead_code_free_vars                       ZipWith(a,b,__za,__zb, Minus(__za,__zb))      gapped (unchanged)
399   d2_dead_code_free_vars                       ZipWith(a,b,__za,__zb, BitXor(__za,__zb))     gapped (unchanged)
429   d2_dead_code_free_vars                       ZipWith(a,b,__za,__zb, BitAnd(__za,__zb))     gapped (unchanged)
```

**All 5 second candidates ARE the exact correct reference program** (`261`:
`tuple(ele1 // ele2 for ele1,ele2 in zip(t1,t2))`; `273`/`282`: `- `;
`399`: `^`; `429`: `&` — every one an exact structural match to
`sanitized-mbpp.json`'s own reference `code`, confirmed by direct
comparison, not assumed from the op name alone) — **and all 5 are still
rejected**, `ps_st_fired_detectors: ['d2_dead_code_free_vars']`,
`ps_st_free_vars: ['__za', '__zb']` on every one. This is the EXACT
honest-NO-GO shape the task brief explicitly asked to be reported if
found ("the SAME D1/D2/D3 detector fires on the ZipWith-based enumerate
candidate too, for reasons unrelated to the primitive gap that's now
closed") — except, unlike a genuine information-theoretic wall
(`STRUCTURAL_REJECT_SURVEY_PREREG.md` §4's own diagnosis for its own
10-task population), this one traces to a mechanical, checkable, FIXABLE
bug rather than a property of the population's information content — see
§3.

---

## 3. The D2 bug, read directly, fixed, re-verified

`domains/prog_synthesis.py::_st_bound_names` (the free-variable-tracking
half of `compute_structural_facts`'s D2 detector) recognizes bound
variables via two channels: (1) a small enumerated list of Prog*-statement
binder TYPES (`_ST_BINDING_TERM_TYPES`), and (2) a generic,
TYPE-INDEPENDENT check for two specific attribute field names —
`var_name`/`acc_name` — the codebase's own documented "consistent naming
convention for a bound iteration variable" used by every plain-DSL
higher-order-function binder (`Filter`, `Sum`, `Fold`, `MapList`, …). The
function's own docstring already documents ONE prior instance of exactly
this bug class being found and fixed (a HOF-term `var_name`/`acc_name`
gap, `PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md` §2.1's "false-positive
discipline").

**`ZipWith` (`runners/dsl/src/reflect.rs:415-421`) introduces a THIRD
binder-field-naming convention — `a_name`/`b_name`** (`TermNode::ZipWith {
a, b, a_name, b_name, value }`, reflected as two `ScalarSym` attrs named
literally `a_name`/`b_name`, distinct from both existing conventions).
`_st_bound_names` was never updated to recognize it (confirmed: `grep -n
"a_name\|b_name" domains/prog_synthesis.py` before this rung's edit —
zero hits) — so every `ZipWith` candidate's own bound variables
(`__za`/`__zb` at the outer level, and, for the 3 nested tasks, `__zi`/
`__zj` at the inner level too) are UNDER-reported as bound, and D2's
`free_vars = var_refs - bound` computation includes them as spuriously
"free" — firing D2 on every single `ZipWith`-shaped candidate, regardless
of correctness.

**The fix** (`domains/prog_synthesis.py::_st_bound_names`, +11 lines
including comment): two more unconditional `attrs.get(...)` checks —
`a_name`/`b_name` — added immediately after the existing `var_name`/
`acc_name` pair, same unconditional (pre-`_ST_BINDING_TERM_TYPES`-gate)
dispatch discipline.

**Provably scoped, not just empirically safe**: `a_name`/`b_name` are
ScalarSym attribute names that appear on NO Term type in this engine other
than `ZipWith` (confirmed: `grep -n "a_name\|b_name" runners/dsl/src/
reflect.rs` — the only hits are `ZipWith`'s own arm). `ZipWith` did not
exist before `ZIP_ELEMENTWISE`'s own merge (`8f2c054`), so no candidate
anywhere in the corpus prior to that merge could ever have carried these
attrs. **The fix is a byte-identical no-op for every candidate that does
not use `ZipWith`** — not reasoned-about safety, a structural guarantee.

**Re-verified live, immediately, same probe re-run after the fix**: ALL 5
tasks now reach `status: accepted` on their FIRST attempt — before the
probe's own fallback-effects code path is ever reached (`eligible: False`
because the goal is no longer `gapped` at all) — **via the
ALREADY-EXISTING, UNMODIFIED rung-(d) retrieval-ladder masked-hole
`SynthEnumerate` probe** (`domains/prog_retrieval.py:602-618`,
`max_size:7, max_candidates:0`, no explicit `ops` — the SAME typed-default
op-list mechanism that already includes `ZipWith` whenever
`spec_has_two_zippable_list_vars` fires, landed by `ZIP_ELEMENTWISE`
itself). This rung's own `run_enumerate`/property-reject-style fallback
machinery was never needed — the correct candidate was ALREADY being
found by the pre-existing retrieval ladder; it was only ever being
wrongly rejected.

```
261 accepted retrieved_exemplar  holdout_all_ok=True  ir=ZipWith(a,b,__za,__zb, IDiv(__za,__zb))
273 accepted retrieved_exemplar  holdout_all_ok=True  ir=ZipWith(a,b,__za,__zb, Minus(__za,__zb))
282 accepted retrieved_exemplar  holdout_all_ok=True  ir=ZipWith(a,b,__za,__zb, Minus(__za,__zb))
399 accepted retrieved_exemplar  holdout_all_ok=True  ir=ZipWith(a,b,__za,__zb, BitXor(__za,__zb))
429 accepted retrieved_exemplar  holdout_all_ok=True  ir=ZipWith(a,b,__za,__zb, BitAnd(__za,__zb))
```

All 5 `rungs` (`codebook`/`lattice`/`descend`/`exact`/`enumerate`) read
`None` — confirming construction never reached the top-level `run_enumerate`
call at all; the retrieval ladder's own rung (d) resolved every one of
them.

**A related, NOT fixed, out-of-scope finding, named honestly**:
`_st_bound_names` has an ANALOGOUS, PRE-EXISTING gap for `IndexedMap`
(`item_name`/`index_name`, `reflect.rs:390` — a FOURTH binder-field-naming
convention, older than this rung, unrelated to `ZipWith`) — confirmed by
the same grep finding zero `item_name`/`index_name` references in
`domains/prog_synthesis.py`. This is a real, live, structurally-identical
bug (any `IndexedMap` candidate that reaches a `retrieved_exemplar`
structural-reject gate would ALSO be wrongly D2-rejected), but it is
outside this rung's own `ZipWith`-scoped population — confirmed no current
MBPP task's own structural-reject trace involves `IndexedMap` (§6) — and
is named, not fixed, per this arc's own single-variable-rung discipline.

---

## 4. Cause 2 — the narrow, `max_candidates`-only budget raise

### 4.1 Confirming the exact budget dimension, live (not re-assumed from
   the citation)

`ZIP_ELEMENTWISE_RESULTS.md` §1.4 measured 261,316-261,322 candidates
tested to solve the 3 nested tasks at their true size-9 candidate, under
the real op inventory, vs. the 200,000 default — a `max_candidates`
shortfall. Re-confirmed live in this worktree, isolated `SynthEnumerate`
call, no explicit `ops` (typed default), `max_size:9` (unchanged, already
matches the nested template's own registration size, §5 of
`ZIP_ELEMENTWISE_PREREG.md`), `max_candidates:400000` (headroom to
observe the true solving point):

```
259 (nested Max)   found=True  tested=261316  halt=solved  term=[[max(__zi,__zj) ...] ...]
401 (nested Plus)  found=True  tested=261320  halt=solved  term=[[(__zi+__zj) ...] ...]
445 (nested Times) found=True  tested=261322  halt=solved  term=[[(__zi*__zj) ...] ...]
```

`max_size` is NOT the bottleneck (already 9, exactly the nested template's
own registration size, per `ZIP_ELEMENTWISE_PREREG.md` §5's own size
accounting — confirmed unchanged in this worktree, `domains/
prog_synthesis.py::run_enumerate` still passes `"max_size": 9` explicitly).
**Only `max_candidates` needs raising** — a narrower, cheaper question than
`MAX_SIZE_SEAM_PRICING_PREREG.md`'s own already-NO-GO'd GLOBAL `max_size`
raise (a different budget dimension entirely, never re-litigated here).

### 4.2 The fix — `runners/dsl/src/synth_enumerate.rs`

A new constant, `ZIP_MAX_CANDIDATES: u64 = 300_000` (~15% headroom over
the measured 261,322 ceiling), applied via `eval_synth_enumerate`:

1. Captured BEFORE the existing `max_candidates <= 0 -> DEFAULT_
   MAX_CANDIDATES` fallback overwrites the caller's raw value:
   `caller_wants_default_candidates = max_candidates <= 0`.
2. After `op_list` fully resolves (typed default or explicit `ops`, post-
   `exclude_ops` filter — the SAME point `exclude_ops` itself already
   applies at, `MODSQRT_SCOPED_FIX_RESULTS.md`'s own precedent) and BEFORE
   `Search` is constructed: `zip_wanted_for_budget = op_list.iter().any(|
   (n,_)| n == "ZipWith")`; `max_candidates = if zip_wanted_for_budget &&
   caller_wants_default_candidates { max_candidates.max(ZIP_MAX_CANDIDATES)
   } else { max_candidates }`.
3. The pre-existing `zip_wanted` (used only for template-pool construction,
   `ZIP_ELEMENTWISE_PREREG.md` §5) is now DEFINED AS `zip_wanted_for_budget`
   rather than re-derived — the budget gate and the template-pool gate can
   never disagree about what one call's own resolved op list contains.

**Both conditions matter, independently:**

- `zip_wanted_for_budget` scopes the raise to calls whose OWN resolved op
  list contains `ZipWith` — which, per `ZIP_ELEMENTWISE_PREREG.md` §6's
  own `spec_has_two_zippable_list_vars` evidence gate, is itself narrow
  (two distinct, pairwise-equal-length list/tuple-shaped spec variables) —
  every other call's cost is untouched, by construction, not by measurement
  alone.
- `caller_wants_default_candidates` preserves every EXPLICIT caller budget
  exactly — a call that already asks for a smaller (or larger) specific
  ceiling (`prog_moves.py`'s `_PROBE_MAX_CANDIDATES`-bounded probes,
  §4.4) is completely unaffected, regardless of its own op list.

### 4.3 Live confirmation, both directions

```
259/401/445, max_candidates:0 (asking for default), op list includes ZipWith:
  -> tested 261,316-261,322, found=True, halt=solved   (would have been budget-halted at 200,000)

259, max_candidates:50000 (explicit, smaller), op list includes ZipWith:
  -> tested 50,000, found=False, halt=budget            (the RAISE never applies -- explicit budget respected exactly)

132 (string-shaped, ZipWith never in op list), max_candidates:0:
  -> found=True, halt=solved                             (zip_wanted_for_budget=False -> untouched)

11 (list-shaped but not zip-eligible), max_candidates:0:
  -> found=True, halt=solved                             (zip_wanted_for_budget=False -> untouched)
```

### 4.4 Cross-lane call-site audit — the SAME class of check
   `MODSQRT_SCOPED_FIX_RESULTS.md` had to do twice, done here once, up
   front

Every `SynthEnumerate` call site in the pipeline, read directly
(`grep -n "max_candidates" domains/prog_*.py`):

| call site | `max_size` | `max_candidates` | affected by this rung's raise? |
|---|---|---|---|
| `prog_synthesis.py::run_enumerate` (top-level, line ~1349) | 9 | 0 (default) | YES when `ZipWith` is in this call's own op list — this IS the call the 3 nested tasks need |
| `prog_synthesis.py` line ~1114 (small probe) | 1 | 0 (default) | `max_size:1` structurally cannot register ANY `ZipWith` template (min size 6 flat / 9 nested) — `zip_wanted_for_budget` may be true but the raise is moot, no candidate at that size regardless |
| `prog_synthesis.py::_solve_arm`/branch-arm (line ~2117) | 7 | 0 (default) | flat `ZipWith` (size 6) fits `max_size:7`, but none of this rung's target population routes through this lane (confirmed: 259/401/445 need the NESTED size-9 template, never reachable at `max_size:7`) |
| `prog_retrieval.py` rung (d) (line ~604) | 7 | 0 (default) | same as above — nested (size 9) never reachable; flat tasks 261/273/282/399/429 are ALREADY resolved by §3's D2 fix at this exact call site, so this raise is moot for them too (found on the FIRST candidate, well under 200,000 uncontested) |
| `prog_moves.py::_run_synth_enumerate` (all 5 call sites) | varies | `_PROBE_MAX_CANDIDATES` (explicit) or `0` (one call, `intermediate_factor`, single-scalar-var spec) | `_PROBE_MAX_CANDIDATES` calls: `caller_wants_default_candidates=False`, never affected regardless of op list. The one `max_candidates:0` call (`intermediate_factor`'s inner-factor probe, line 754): spec is single-scalar-variable (`{arg: r["vals"][idx]}` -> scalar), never 2-distinct-list-shaped, so `spec_has_two_zippable_list_vars` is false and `ZipWith` never enters this call's own op list — `zip_wanted_for_budget=False`, untouched |

**Net: the ONLY call site where this rung's raise actually changes
behaviour is `run_enumerate`'s own top-level call, for a spec whose op
list contains `ZipWith` and that also needed more than 200,000 candidates
— precisely the 3 nested target tasks, and (by the same mechanism) any
future MBPP task with the identical shape.** No cross-lane regression risk
of the `MODSQRT_SCOPED_FIX_RESULTS.md` class exists, because every OTHER
call site either cannot register a `ZipWith` template at its own `max_size`
ceiling, already resolves via a different mechanism (§3), or already
supplies an explicit budget this rung's gate is designed to leave alone.

---

## 5. Full paired MBPP battery — exact task-id set diffs, both fixes
   together

See the accompanying `PROGRAM_SYNTHESIS_ZIPWITH_FOLLOWON_RESULTS.md` for
the authoritative battery numbers, the full regression suite (including a
live isolation trace that confirmed one flagged test-pin drift is
PRE-EXISTING on unmodified `main`, unrelated to either fix here), and the
final GO/NO-GO.

---

## 6. What this document does NOT establish

1. Whether the `IndexedMap` `item_name`/`index_name` D2 gap (§3) affects
   any CURRENT MBPP task — checked against this rung's own target
   population only (no current structural-reject trace involves
   `IndexedMap`); a full corpus sweep for it was not performed, and it is
   not fixed here.
2. Whether `ZIP_MAX_CANDIDATES:300_000`'s own ~15% headroom is the RIGHT
   margin in general (vs. e.g. exactly 261,322, or a larger round number) —
   chosen for comfortable safety over the measured ceiling, not
   independently tuned or pressure-tested against a wider corpus of
   hypothetical larger `ZipWith` specs.
3. Whether any MBPP task OUTSIDE the original 8-task `ZIP_ELEMENTWISE`
   witness cluster is affected by either fix — the full 257-task battery
   (§5) is the authoritative population-wide check; no sampling was used.
4. Whether any of this reflects real human program-synthesis cognition
   remains exactly as open as every prior document in this arc left it.

## Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/progsyn-zipwith-followon
git log --oneline -1   # on top of main @ bc0ac10
```

The D2 fix (§3) and the budget raise (§4) can each be checked in isolation
by reverting the other file (`git diff` shows exactly 2 non-doc/non-script
files touched: `domains/prog_synthesis.py`, `runners/dsl/src/
synth_enumerate.rs`).

`scripts/zip_structural_probe.py` (scratch, not part of any seed) is the
probe from §2.1 — safe to re-run at any point (it only mutates a
freshly-booted, in-memory substrate per task, never persists).
