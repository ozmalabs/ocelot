# ENGINE INSTRUMENTATION — THE WINNER'S OWN VALUE — PRE-REGISTRATION

*Written and COMMITTED before any implementation or measurement (§3).*

**Branch:** `gamma-substrate/engine-winner-value`.
**Seed block:** **60000–60999** (allocated pre-launch; ledger high-water 59999,
a concurrent redundancy-audit rung holds 59000–59999). No other block is taken.
**Engine (§10):** built in THIS worktree only, by `scripts/engine_build.sh`.
Nothing is built in the canonical tree; every number below is reported with the
`.so` hash that produced it.

---

## 0. WHAT THIS IMPLEMENTS, AND WHY IT IS A GATE

`ENGINE_ARGMAX_DETERMINISM_RESULTS.md` (merged `fc95c326`) investigated 272
irreproducible rows in which one `Argmax` returned a single constant node for an
entire substrate while, in the *same rule application*, `MaxOver` and
`Count(Filter(Eq(·, xf_max)))` were **both correct on 272/272 rows**. It could
not reproduce the fault at 200× the original budget (1 088 000 probes, 0 foreign
wins), excluded six mechanisms on evidence, and declared the cause
**UNESTABLISHED with an honestly unbounded blast radius** (§5.3).

Its §6 actionable output is this rung:

> **Record the WINNER'S OWN VALUE, not just the extremum and the tie count.** A
> tie count proves the selection was unambiguous *according to the selector*. It
> cannot detect a selector that disagrees with its own value Term, because both
> numbers are then computed by the thing under suspicion.

The general principle, stated as the rule this rung is built to satisfy:

> **A diagnostic must not be computed by the component it checks.**

**Why it gates the next thing.** The creator intends to make the collapse loop
asynchronous — monotone (add-only) rungs parallelised on the theory that
asynchronous fixpoint iteration reaches the same least fixpoint regardless of
order, non-monotone rules (`del_edge`, retraction, status mutation) held behind a
barrier. **Concurrency cannot land while an unexplained nondeterminism is
outstanding**, because every subsequent anomaly would be permanently ambiguous
between "a new race" and "the thing we already could not explain". The current
clean deterministic baseline is spendable exactly once. So this instrument is
designed to be the race detector too, and **§6 below registers, in advance, the
class of race it will MISS** — that bound is part of the deliverable and is
written before the implementation so it cannot be trimmed to fit the result.

---

## 1. THE SELECTOR AUDIT — what exists, and what is in scope

Audited by reading `runners/dsl/src/term.rs` (not by grep count), plus a
structural count of the committed seeds. Two distinct selector classes exist.

### 1.1 IN SCOPE — binder selectors (a `source`, a bound `var_name`, a `value` Term)

| Term | returns | helper |
|---|---|---|
| `Argmax` | the winning **element** | `argmin_or_argmax_over` (`term.rs:7638`) |
| `Argmin` | the winning **element** | same, `want_min` |
| `MaxOver` | the winning **value** | `min_or_max_over` (`term.rs:7535`) |
| `MinOver` | the winning **value** | same, `want_min` |

This is the class that produced the anomaly. Both helpers fold with
`cmp_value`, take a new element only on a **strict** ordering (so first-encountered
wins every tie), and neither ever re-reads the winner.

Committed-seed usage (`seeds/*.json`): `Argmax` **41**, `Argmin` **66**,
`MaxOver` **101**, `MinOver` **59**. Python-side rule builders reference the four
spellings a further 127 / 47 / 51 / 46 times.

### 1.2 IN SCOPE — the index selector (`items`, no binder)

`ArgMax { items }` / `ArgMin { items }` (`numeric_argmax`, `term.rs:6414`) reduce
a **list of Term indices** to the *index* of the extremum. No binder, no value
Term — but the same check applies: re-evaluate `items[winner_idx]` and compare to
the recorded extremum. **0 occurrences in committed seeds**; built from Python
(`domains/dynamics_features.py` emits `{"type": "ArgMax", …}`). Covered because
it is cheap and it is a selector; its low usage is stated rather than used as an
excuse.

### 1.3 OUT OF SCOPE, NAMED (§8 — do not silently skip a class)

- **`Pick` / `PickUnique`** (96 / 260 seed occurrences). These have **no value
  Term**: there is no extremum to disagree with, so the invariant is not
  expressible. `PickUnique` already carries its own §12.3 ambiguity guard, which
  is the correct instrument for that class. **Not covered, by construction.**
- **`Count(Filter(Eq(·, max)))`** — the tie-count idiom. This is a *count*, not a
  selection; it returns no winner. It is the quantity the determinism rung showed
  was CORRECT while the `Argmax` was wrong, i.e. it is already the independent
  cross-check on the other side. **Not covered; not a selector.**
- **`ShapeDecode`'s internal plan search** (`shape_decode.rs`). It selects a plan
  internally without going through a selector Term. Instrumenting it is a
  different, larger job with its own scoring semantics. **Named, not covered.**
- **Value subtrees containing an effectful / re-entrant Term** — `UseTool`
  (dispatches to a Python handler under the GIL, re-entrant into the substrate)
  and `ReadFile` (host I/O). Re-evaluating these would **double-fire a side
  effect**, which is a behaviour change, which §9 forbids. These firings are
  **skipped and counted separately** as `skipped_effectful`, so the coverage gap
  is a reported number and not a silence. Predicted count: **0** in the bench
  (no seed puts `UseTool` inside a selector's value Term) — registered in advance
  so a non-zero count is a finding.

**Coverage claim to be checked, not assumed:** every `Argmax` / `Argmin` /
`MaxOver` / `MinOver` / `ArgMax` / `ArgMin` firing is audited except those whose
value subtree is effectful. This is claimed at the level of the **evaluator**, not
of a call-site list — the check lives inside the two fold helpers and
`numeric_argmax`, which every firing must pass through, so coverage does not
depend on remembering to wire anything up.

---

## 2. THE MECHANISM

### 2.1 The check

After the fold selects `(best_value, best_element)`, re-bind `var_name` to
`best_element`, **re-evaluate the selector's own `value` Term**, and compare the
result to `best_value` with the same `cmp_value` the fold used. Any ordering
other than `Equal` is a **contradiction recorded on that single firing**.

For `MaxOver` / `MinOver` the winning element is not currently tracked (only the
value is). It will be tracked **only when the audit is enabled**, so the disabled
path keeps its exact allocation behaviour.

For `ArgMax { items }` / `ArgMin { items }` the same check re-evaluates
`items[winner_idx]`.

This satisfies the governing principle: the re-evaluation is performed by the
**evaluator**, on the element the **selector** returned, using the value Term the
**seed author** wrote — the recorded extremum plays no part in producing it.

### 2.2 The switch, and the default (§9)

Default **OFF**. When off, the only added work is one relaxed atomic load per
selector firing; no element is cloned, no Term is re-evaluated, and no branch is
taken. Committed results therefore reproduce exactly, and that is measured in §4,
not asserted.

State lives in process-global atomics (`selector_audit`), not in `EvalCtx`.
**Reason, stated in advance:** `EvalCtx` is constructed at many call sites, so an
`EvalCtx` field would make coverage depend on every site opting in — the exact
"instrument that was never wired up" failure this project has been bitten by. A
global is audited at the *evaluator*, so coverage is structural. Atomics also
remain correct under the asynchronous plan this rung gates.

Three modes:
- `off` (default) — no check.
- `warn` — check, count, retain the first contradiction verbatim, keep going.
- `strict` — check, and **panic on the first contradiction** with the full row.

Enabled from Python (`selector_audit_enable` / `_stats` / `_reset`) and from the
environment (`OZMA_SELECTOR_AUDIT=warn|strict`), so the bench can be run under
audit without editing a single test.

### 2.3 The positive control — a detector that has never fired is untested

This project has been bitten repeatedly by instruments that could not fire,
including a provenance gate that sat green for **51 commits** because its trigger
condition never arose (§12/§12.1). Therefore:

A **fault injector** (`selector_fault_inject_first`) makes the fold return the
**first element encountered regardless of its value** — which is *exactly* the
§4.2 anomaly's measured signature (a constant winner, `fractal`, the lowest-id
candidate, while the neighbouring compositions stayed correct). The instrument
must catch it **in one row**.

**Safety property, registered in advance:** the fault injector is read **only
inside the audit branch**, so it is unreachable when the audit is off. A test
asserts both defaults are off. It is not reachable from any seed or Term.

---

## 3. THE STATISTICS, EXACTLY

1. **Byte-identity (§9).** `bash scripts/rung7_vision_bench.sh` → **200 passed,
   exit 0**, pre-change and post-change, same worktree, engine hash recorded for
   each. The sd orbit law `{2:1, 3:2, 4:2, 6:2, 12:4}` unmoved. The landed
   `results/*.json` artifacts named in §4.3 re-run identical modulo elapsed time.
2. **Detection (positive control).** With `strict` + fault injection, the first
   selector firing over a source with ≥2 distinct values **panics**, and the
   panic message names the winner, the winner's re-evaluated value, and the
   recorded extremum. Red-then-green: the same test with injection off passes.
3. **Live invariant.** Full bench under `warn`: report `firings`,
   `disagreements`, `skipped_effectful`. **Predicted `disagreements = 0`.**
4. **Cost, as an exact counted fraction — NOT wall-clock.** A concurrent rung is
   running, so wall-clock is confounded and is not the headline (operational
   rule). The audit's cost is exactly **one extra `value` evaluation per audited
   firing**, so the overhead of the instrument on the selector path is

   ```
   overhead = audited_firings / candidate_evaluations
   ```

   i.e. **1/N for a selector over N candidates**, aggregated over the bench. This
   is deterministic, load-independent, and **falls out of the candidate-set sizes
   the seeds actually produce** (§13) — no threshold is set here, the number is
   reported and the switchability decision is stated against it.

---

## 4. DECISION RULE

- **Any verdict moves ⇒ STOP and report it as a finding.** A behaviour change in
  an instrumentation rung is not a bug to be fixed quietly; it means the "strictly
  additive" premise was false and that is the result.
- **`disagreements > 0` on the bench with injection OFF ⇒ a LIVE reproduction of
  the anomaly class.** Report immediately, with the row, before anything else.
  This is registered as the *unexpected* outcome.
- **`disagreements = 0` ⇒ the registered NULL**, and it is a null about *this
  bench on this machine at this budget*, not about the engine. It bounds nothing
  about a different workload. Registered in advance precisely so it cannot later
  be dressed up as evidence of correctness.
- **The positive control failing to fire ⇒ the rung has shipped nothing**, and
  that is the honest report. Requirement 2 is not satisfiable by argument.

### 4.3 The artifacts whose byte-identity is checked

`results/blink_measure.json`, `results/depth_measure.json`,
`results/genmint_measure.json`, `results/ground_measure.json`,
`results/shape_selfsee.json`, `results/stereo_measure.json`,
`results/time_measure.json` — re-run and diffed field-by-field excluding
elapsed-time fields. Any other field differing is a §4 STOP.

---

## 5. MY PREDICTIONS, STATED IN ADVANCE (§3.7)

| # | prediction | proviso that would break it |
|---|---|---|
| 1 | **`disagreements = 0`** across the full bench under `warn`. | A non-zero count means the anomaly class is live in the vision workload — which the determinism rung's 1 088 000-probe null makes unlikely, but it is the outcome I would most want to be wrong about. |
| 2 | The positive control fires on the **first** firing whose source has ≥2 distinct values. | It would not fire on a source of size ≤1, or on an all-tie source — in an all-tie fold the first element **is** a legitimate winner, so injection is a no-op there. That is correct behaviour, not a miss. |
| 3 | `skipped_effectful = 0` on the bench. | A non-zero count means a seed puts `UseTool`/`ReadFile` inside a selector's value Term, which is itself worth knowing. |
| 4 | The aggregate overhead fraction lands **between 5% and 40%** of selector-path evaluations, because seed selectors mostly range over small sets (1/N with small N is a large fraction). | If it lands below 5%, sources are much larger than I think; above 40% means the modal selector ranges over ~2 candidates. Either way the number is reported as measured — the prediction is a test of whether I understand the workload, not a target. |
| 5 | The instrument will **not** catch a race that corrupts the value Term's *inputs* stably, because the re-evaluation reproduces the same wrong value. | See §6 — this is registered as a MISS in advance so the coverage claim cannot be inflated afterwards. |

---

## 6. THE RACE-DETECTION BOUND — registered BEFORE the implementation

This is the part that gates concurrency, so it is written first and will be
reported unchanged.

### 6.1 What it WOULD catch

- **A corruption of the fold's own `best` state** — the observed §4.2 signature.
  The winner is returned; its own value disagrees with the recorded extremum;
  detected on that firing.
- **A torn read of a value the fold consumed**, provided the re-read differs.
- **A mid-fold graph mutation that changes the winner's value** — detected, *but*
  see §6.3: under concurrency this is also the instrument's false-positive class.

### 6.2 What it would MISS — stated plainly

1. **A stable corruption of the value Term's inputs.** If a race leaves the graph
   in a state where the value Term consistently returns a wrong number, the fold
   and the re-check **agree**, and both are wrong. The instrument checks
   *self-consistency*, not *truth*. This is the largest miss and it is
   structural.
2. **A race in the SOURCE set.** If the source is wrong — a node missing, a stale
   `NodesOfType` snapshot — the selector correctly picks the extremum *of the
   wrong set*. Winner and value agree. Undetected.
3. **A race after the fold returns.** The selector's result being clobbered by a
   concurrent effect between selection and use is entirely outside this
   instrument.
4. **Any race in a non-selector Term.** `Count`, `Sum`, `Filter`, `ShapeDecode`'s
   internal search, and every arithmetic Term are uninstrumented here.
5. **Firings skipped for effectfulness** (§1.3).
6. **A race that produces a legitimate-looking tie.** Where all candidates
   compare equal, any element is an admissible winner and the check passes by
   construction — which is exactly how the §4.1 all-tie probe behaved.

### 6.3 The false-positive class the async plan must handle

Under monotone (add-only) parallelism, a value Term that reads a **growing** set —
`Count(Neighbours(...))`, a running maximum — can legitimately increase between
the fold and the re-check. The instrument would report a contradiction that is
**not** a bug. Therefore:

> The invariant as implemented is **sound only under a quiescent graph** — which
> is what the current single-threaded `run_rules` guarantees and what the
> proposed non-monotone barrier would have to extend to the monotone phase for
> this detector to stay meaningful during it.

Registering this in advance matters more than the detector itself: it says the
instrument is a *baseline* verifier for the deterministic engine, and that using
it as a live race detector inside a parallel monotone phase would require the
re-check to be taken under the same snapshot as the fold. That is a design
constraint on the concurrency work, discovered here rather than after it lands.

---

## 7. SCOPE (§8)

One engine, one worktree, one machine, one bench. This rung establishes an
*instrument*, not a correctness proof: a null from it says the selectors were
self-consistent on the paths the vision bench exercises, and says nothing about
paths it does not exercise, about a different engine build, or about the
unreproduced §4.2 anomaly, whose cause remains **UNESTABLISHED** and whose blast
radius remains as §5.3 left it. The instrument makes a recurrence *diagnosable*;
it does not make it *less likely*.
