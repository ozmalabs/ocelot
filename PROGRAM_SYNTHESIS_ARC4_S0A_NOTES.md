# PROGRAM SYNTHESIS ARC 4 — S0 TRACK A: HA1/HA2 MEASUREMENT (before any build)

**Date:** 2026-08-01. Companion to `PROGRAM_SYNTHESIS_ARC4_PLAN.md` §1 (HA1/HA2) and
§2 (S0 — this phase's two bullets). Input: `PROGRAM_SYNTHESIS_ARC3_R3.md` +
`results/mbpp_arc3_endgame.json` (the FULL-R3 arm, RE-RUN live here rather than only
cited — hash-identical to the frozen artifact, proof below). Deliverables:
`scripts/arc4_failure_anatomy.py` (driver, imports `scripts/mbpp_arc3_battery.py`
verbatim, touches no synthesis/engine/seed/spec code), `results/arc4_failure_anatomy.json`
(the artifact — every number below re-derives from its rows), `tests/test_arc4_anatomy_
migrated.py` (27 passed, ~31s).

**Sibling track:** S0-B runs concurrently on `scripts/arc4_backward_probe.py` /
`results/arc4_backward_probe.json` / `PROGRAM_SYNTHESIS_ARC4_PREREG.md` (HA3's
data-dependency probe) — not touched by this track.

---

## 0. R3 continuity — this phase re-runs, not just cites

`scripts/arc4_failure_anatomy.py` re-runs the FULL-R3 arm end-to-end (twin-run,
`mbpp_arc3_battery.run_arm("full_r3", ...)`, imported not modified) rather than only
reading the frozen `results/mbpp_arc3_endgame.json`. The live outcome-hash is
**byte-identical** to the frozen artifact's own cited hash
(`7800ee24ac7650b7466ab6a8aa809d3a77889b30a2f2c7b50c511ea7ebb6213c`), and the frozen
file's own sha256 is unchanged (this phase only reads it) — both re-verified live by
`tests/test_arc4_anatomy_migrated.py`. Nothing drifted between R3 and this measurement.

---

## 1. Measurement 1 — the `gapped:exhausted` residual by class (HA1's target list)

17 tasks are `gapped:exhausted` under FULL-R3 (unchanged from R3's own count). Every
row's own recorded facts (`construction`, `rungs`, `retrieval.rung_reached`,
`screen.kills`) — never a live decision — classify it:

| class | n/17 | task ids |
|---|---|---|
| **(a) descend-applicable** | **7** | 286, 296, 415, 463, 468, 471, 476 |
| **(b) cued-but-screen-disengaged** | **10** | 108, 119, 222, 223, 229, 240, 245, 280, 394, 431 |
| (c) retrieval-consumed | **0** | — |
| (d) genuinely exhausted by the enumerator itself | **0** | — |
| (e) anything else | **0** | — |

(a) and (b) reproduce `PROGRAM_SYNTHESIS_ARC3_R3.md` §4's own already-published
partition (the 7 "starter-codebook-shape" residual ids and the 10 "screen never
engaged" covered-class ids) exactly — confirmed by direct id-list comparison, not
just a count. **Every one of the 17 rows falls into (a) or (b).**

### 1.1 Why (c) and (d) are empty — not luck, structural

Two independent lines of evidence, one architectural and one empirical:

- **Architectural.** `seeds/program_synthesis.json`'s own rule comments name the
  state-machine invariant: `ps_exhausted`/`ps_ce_exhausted` ("BUDGET HONESTY at the
  propose gate ... exhausted") fire **only** at the propose/codebook gate, before
  `SynthEnumerate` ever runs; a real enumerator failure is **always** classified
  `ps_enumerate_failed` (a different, mutually exclusive status). So "exhausted" is,
  by the pipeline's own construction, never attributable to the enumerator itself —
  class (d) cannot be populated under the current state machine, and finding it
  non-empty would itself be the anomaly. Likewise, retrieval's only `ps_attempts`-
  incrementing effect (`pr_ladder_accept`) fires only on an actual **accept**, which
  transitions the goal to `status:accepted`, never back through `gapped:exhausted` —
  so class (c) is also structurally unreachable while `rung_reached` stays `"none"`.
- **Empirical.** All 17 rows show `rungs.enumerate == null` (enumerator never ran)
  and `retrieval.rung_reached == "none"` (retrieval never attempted an accept),
  confirming the architectural prediction on the live re-run, per-row, with no
  exceptions.

### 1.2 HA1's honest ceiling

Per the plan's own S1 scope ("generalises R2.5's screen from 'engage when pool ≥
budget' to 'always isolate' — which also covers the 7 descend-applicable rows R2.5
honestly could not"), **S1 as scoped has no structural blind spot left in this
residual**: 17/17 rows fall in classes S1 is designed to fix, 0/17 in a class S1's
scope doesn't reach. The honest ceiling on HA1's "`gapped:exhausted` → 0 across all
classes" bar is **0 unaddressable rows**, contingent on S1 landing exactly as
described. If S1 lands and any row remains `gapped:exhausted`, that is a genuine miss
against *this measured target list* — not an already-known residual to wave at.

---

## 2. Measurement 2 — trap anatomy for `accepted_holdout_fail` (HA2's killable mass)

76 tasks are `accepted_holdout_fail` under FULL-R3 (matches R3's own 76-row count).
For every one, the ACCEPTED IR was probed with three owned, revealed-rows-only
signals (never held-out — the isolation gate is enforced mechanically, see §4).

| signal | measured on | n killable | task ids |
|---|---|---|---|
| **(a) cross-frame — python vs native `ProgEval`** | all 76 | **10** | 61, 62, 100, 129, 247, 267, 271, 287, 306, 461 |
| **(a) cross-frame — rust/lua/llvm toolchain** | 26-task deterministic subsample (stride 3) | **4** | 14, 103, 420, 430 |
| **(b) type/arity property violation** | all 76 | **9** | 68, 164, 228, 284, 285, 407, 414, 434, 454 |
| **(c) invariance/metamorphic catalogue (5 checks)** | all 76, per-check applicability gate | **1** | 306 |
| **(d) nothing available (honest residual)** | all 76 | **53** | (53 ids, see artifact) |

**Union killable by at least one owned signal: 23/76 (30.3%).** Overlap: task 306 is
caught by both (a)-python and (c)-invariance; (a) and (b) never overlap; (b) and (c)
never overlap. **Honest residual (d): 53/76 (69.7%)** — traps no owned signal can
kill using only revealed rows.

### 2.1 (a) cross-frame — two distinct, real findings, not noise

**Python-vs-native disagreement (10/76).** Inspected by hand (not just counted):
these are genuine defects, not sandbox artifacts (the exec sandbox exposes exactly
`domains.prog_ir_emit.NATIVE_ORACLES`' builtin surface — `len`/`range`/`math.*`/etc.
— never full Python builtins, after an initial pass with an *empty* sandbox produced
22 false positives from legitimate `len()`/`range()`/`math.sqrt()` calls; fixed
before this measurement's final run). The clearest example, task 267: the accepted
IR is `return (35 if (a - 2) else 10)` — a **hard-coded lookup table** memorizing the
two revealed rows (`a=2→10`, `a=3→35`) — preceded by dead-code statements
(`for x in range(1, n+1): acc += x`, `v2 = a + b`) that reference **free variables
`n` and `b`, never bound as parameters or locals anywhere in the program**. The
native `ProgEval` interpreter never surfaces this because the dead assignments'
results are never read on the path to the return value; a faithful Python render
executes them eagerly and raises `NameError` immediately. **This is a real,
revealed-rows-only, pre-accept-catchable defect class:** decoy/retrieved candidates
carrying orphaned, unsubstituted variable references from their donor context.

**Rust/lua/llvm toolchain disagreement (4/26 subsample).** All four
(14, 103, 420, 430) share **one root cause**: an `IfThenElse` gated on a raw numeric
condition (e.g. `if (b - c)`) rather than an explicit comparison. Rust's type system
rejects this at compile time (`compile_error`, not a semantic disagreement — Rust has
no implicit int→bool coercion). Lua's own truthiness convention (only `nil`/`false`
are falsy; the integer `0` is **truthy**) diverges from the DSL's own convention
(numeric `0` is falsy, matching Python/C) — the `render_rust_lua.py` Lua renderer
emits the raw condition without coercion, so Lua silently picks the "then" branch
where the DSL/LLVM path picks "else". The LLVM→x86 chain **agrees** with native
`ProgEval` on the same three tasks (a fourth, 420, hit an unrelated `chain_error`),
confirming this is a **Lua-renderer-specific coercion gap**, not four independent
findings — one fix (coerce a non-bool `IfThenElse` condition to an explicit `~= 0`
in the Lua render rule) would resolve all four. Full toolchain outcome mix on the
26-task subsample: rust `{compile_error: 8, agree: 4, render_gap: 14}`; lua
`{disagree: 4, agree: 6, render_gap: 11, runtime_error: 5}`; llvm
`{agree: 7, emit_refusal: 9, scope_out_non_int: 9, chain_error: 1}`. **This is the
first non-zero toolchain disagreement measured across arcs 1–4** (arcs 1–3's own
standing finding was zero); it required deliberately probing `accepted_holdout_fail`
(wrong) programs specifically, a population the earlier P5/P6 toolchain batteries
did not target the same way.

### 2.2 (b) type/arity — a real, non-tautological catch

Every one of the 9 hits is the SAME shape: `row%d_type_mismatch:got=numeric,
expected=bool` (task 407 on one revealed row, the other 8 on both). This is
**not** re-deriving what synthesis already checked: the pipeline's own internal
accept comparator (`domains.prog_synthesis._row_cmp_ok`, plain-equality branch) uses
Python's own type-loose `==` (`True == 1` is `True`), so a candidate returning an
`int` where the revealed row's own reference expects a `bool` is silently accepted
internally. The type/arity check, applying a **strict** type-family comparison
(the same bool-distinguished-from-numeric convention `mbpp_arc3_battery.agree`
already established for the artifact's own holdout scoring) to the SAME revealed
rows, independently catches all 9 — a defect class the accept path structurally
cannot see, using only data it already had.

### 2.3 (c) invariance/metamorphic — small, honest, mostly inapplicable by design

Five checks, each stating its own entailment (never semantic guessing — only what a
revealed row's own schema field, or arithmetic over its own values, entails):

| check | assumption | applicable/76 | violated |
|---|---|---|---|
| `det_repeat` | a revealed example entails the reference relation is a deterministic function; re-evaluating twice must agree | 76 | 0 |
| `unordered_set_permutation` | a revealed row's own `unordered=True` (set-compared assert) entails order-insensitivity for that call; reversing a list arg must not change the output SET | low | 0 |
| `swap_arity2_same_type_no_new_trap` | arity-2, same-typed args entail the swapped call is equally well-typed; must not newly trap (not a commutativity claim) | moderate | 0 |
| `tol_row_small_perturbation_no_trap` | a `tol`-flagged (isclose) row entails a real-valued formula defined nearby; +1 perturbation must not newly trap | moderate | 0 |
| `count_len_increment` | a row where `expected == len(some list arg)` structurally (arithmetically) entails a counting relation; appending one element must increase output by exactly 1 | low | **1 (task 306)** |

Only `count_len_increment` fired (task 306, which also shows a python cross-frame
disagreement — a list/int concatenation `TypeError`). The catalogue's low hit rate
is the honest finding, not a defect in the catalogue: most `accepted_holdout_fail`
tasks simply don't carry a revealed-row schema fact that entails any of these five
properties (MBPP's PRIMARY protocol reveals only 1–2 rows per task, rarely enough to
trigger a `tol`/`unordered` flag or a literal `len(...)`-shaped coincidence).

### 2.4 HA2's honest ceiling

**23/76 (30.3%)** of the `accepted_holdout_fail` trap population is killable
*before accept*, using *only revealed rows*, by signals this codebase already owns
(cross-frame rendering, a strict type check, five metamorphic checks) — zero new
content, zero held-out peeking. **53/76 (69.7%) is the honest residual**: traps
whose accepted IR renders and executes consistently everywhere, matches its own
revealed rows' types/arity, and violates none of the five invariance checks, yet
still fails to generalize. S2's ceiling on "reject-before-accept using owned
signals" is bounded at **30.3%** of the currently-measured trap population — real
and worth building, but the majority of the trap mass needs a genuinely different
signal (more revealed rows, a stronger property/verdict discriminator, or search
reach itself, per the plan's own §5 "clean, publishable negative" fallback).

---

## 3. What this implies for S1 / S2's achievable bars

- **S1 (budget isolation, HA1).** The measured target list is *complete*: 17/17
  `gapped:exhausted` rows are attributable to cued proposals consuming budget
  (7 descend-applicable + 10 screen-disengaged), 0/17 to retrieval or genuine
  enumerator exhaustion. S1's own stated scope ("always isolate", covering both
  sub-classes) has no known gap against this list — the registered HA1 bar
  (`gapped:exhausted` → 0) is achievable in full if S1 lands as scoped. A
  post-S1 residual on any of these 17 ids would be a genuine, reportable miss.
- **S2 (verdict discrimination, HA2).** The three owned signals *do* find real,
  non-tautological defects (a hard-coded-lookup-with-dead-free-variables pattern;
  bool/numeric type laxness the accept path structurally misses; one metamorphic
  catch; a genuine, previously-zero, now-measured Lua-renderer truthiness gap) —
  but they cover **less than a third** of the trap population. S2 should be scoped
  to its measured, honest ceiling (~30%) rather than an assumed "most traps are
  cross-frame-catchable" expectation; the plan's own §5 fallback (search reach,
  HA4) is the correct place for the remaining ~70% if S2 lands clean and the
  overall pass rate still doesn't move CI-separated.
- **A concrete, free side-finding for S2 to fold in:** the Lua renderer's
  non-bool-`IfThenElse`-condition truthiness gap (§2.1) is a renderer bug
  independent of any candidate's correctness — fixing it (coerce to `~= 0`) is a
  small, targeted Rust/render-rule change that would make the cross-frame signal
  strictly more trustworthy for S2, and costs nothing to identify further (the same
  4 ids, same root cause, already isolated).

---

## 4. Held-out isolation — proof, not assertion

Every trap-anatomy probe function (`_revealed_rows_for_task`, `type_arity_check`,
`invariance_probe` and its five checks, `python_cross_check`, `toolchain_cross_check`,
`_llvm_chain`) takes **only** `revealed_rows`, recomputed straight from the fixture
via `domains.mbpp_spec.split_rows(...)["revealed"]` — `spec["held_out"]` is never
bound to a name in any of them. Verified two ways: (1) a mechanical source-text audit
(`aa._held_out_isolation_audit`, asserted clean both inside the driver script itself
before it writes anything, and independently re-run live by the test suite), and
(2) a call-site proof that `_revealed_rows_for_task`'s own return value is byte-equal
to `split_rows(...)["revealed"]` and distinct from `["held_out"]` on a real task.

---

## 5. Determinism, environment, files

- **R3 re-run:** twin-run byte-identical (inherited from `mbpp_arc3_battery.run_arm`),
  and cross-checked hash-identical against the frozen `results/mbpp_arc3_endgame.json`
  citation.
- **Measurement 2 cheap signals** (python cross-check, type/arity, invariance —
  pure in-process computation): run twice end-to-end, hash-identical.
- **Measurement 2 toolchain subsample** (rust/lua/llvm, subprocess cost): run
  **once**, time-boxed, explicitly labelled not re-verified a second time in this
  phase (a pure function of already-twinned inputs through a fixed external
  toolchain — rustc 1.95.0, lua5.4 5.4.8, gcc 16.1.1 — not re-run for time-budget
  reasons).
- **Toolchain subsample rule:** sorted `accepted_holdout_fail` task ids, stride =
  `max(1, n // 20)` = 3, giving 26 ids — no silent cap, rule recorded in the
  artifact's `condition.toolchain_subsample` and re-derived by the test suite.
- **Total elapsed:** ~31s (well inside the ~25 min timebox).
- **Contamination:** unchanged discipline from `mbpp_arc3_battery.py` (`task["code"]`
  never read; every substrate fresh; no `domains.teach.teach` call) — gated by this
  phase's own scan plus the shared `tests/test_mbpp_contamination_migrated.py` gate,
  both green.

**Files:** `scripts/arc4_failure_anatomy.py` (driver), `results/arc4_failure_anatomy.json`
(artifact — per-task rows for both measurements, class id lists, totals derived from
rows, twin-run/cheap-signal determinism hashes, environment, contamination note),
`tests/test_arc4_anatomy_migrated.py` (27 passed, ~31s).
