# ENGINE INSTRUMENTATION — THE WINNER'S OWN VALUE — RESULTS

*Pre-registration: `ENGINE_WINNER_VALUE_PREREG.md`, committed BEFORE any
implementation at **`13bb7eaf`**.*
*Implementation + gate: **`8bdba21a`**.*

**Engine (§10):** built in THIS worktree by `scripts/engine_build.sh` only.
Baseline (pre-change) **`e59484fe6b2e`**; instrumented **`11ee213dfd46`**.
Nothing was built in the canonical tree. The BSDS300 corpus was symlinked
READ-ONLY from the canonical tree — never written — so the bench reports its
full 200 rather than 190 + 10 dataset skips (§10.2).

**Seeds:** block **60000–60999** allocated; **none consumed** — the positive
control is deterministic fault injection, not a sampled experiment, so no seed
was burned. The block is returned unused.

**Concurrency state:** a concurrent rung was running throughout. **No wall-clock
number is a headline here** (see §3.3, which measures why).

---

## 0. THE HEADLINE, IN ONE PARAGRAPH

**The instrument is built, it is strictly additive, and — the part that matters
— it has been shown to FIRE where the pre-existing instrumentation is BLIND.**
Every `Argmax` / `Argmin` / `MaxOver` / `MinOver` / `ArgMax` / `ArgMin` firing
now re-evaluates the selector's own value Term **on the element the selector
returned**, so `winner_value != recorded_extremum` is a contradiction visible on
a single row. Across the full vision bench the invariant was **enforced** (strict
mode) over **60 253 656 selector firings** with **0 disagreements** and **0
firings skipped** — and the bench reported **200 passed, exit 0 in all three
configurations** (audit off, warn, strict), byte-identical to the pre-change
baseline. The decisive demonstration is not the null: it is the red-then-green
gate that reconstructs the §4.2 configuration and shows that with the fault
present **`MaxOver` still returns 9.0 and the tie count still returns 1 — both
correct, both blind** — while the winner's own value catches the wrong answer on
that same firing. **The registered cost prediction was WRONG and the real number
is the most useful finding after the instrument itself:** the overhead is
**81.41%** of selector-path evaluations, because the modal selector in this
corpus ranges over **1.23 candidates** — the instrument is most expensive exactly
where it has least diagnostic power, which is why it ships OFF.

---

## 1. WHAT WAS BUILT

`runners/dsl/src/selector_audit.rs` (new) + three edits in `term.rs`
(`min_or_max_over`, `argmin_or_argmax_over`, `numeric_argmax` / `numeric_argmin`)
+ four one-line PyO3 handoffs in `py.rs`.

After a fold selects `(best_value, best_element)`, the **evaluator** re-binds the
selector's own `var_name` to `best_element`, re-evaluates the selector's own
`value` Term, and compares with `cmp_value`. The two numbers are produced by
different things — the recorded extremum by the selector under suspicion, the
winner value by the evaluator re-running the seed author's own Term on the
returned node. That is the whole design, and it is the rule the determinism arc
earned:

> **A diagnostic must not be computed by the component it checks.**

### 1.1 Coverage is STRUCTURAL, not wired-up

The check lives **inside the two fold helpers and the two index reducers**, which
every firing must pass through. It is therefore not possible for a call site to
forget to enable it — which is the exact failure mode this project has been
bitten by repeatedly (§12.1's nine inert instruments; a provenance gate green for
51 commits because its trigger never arose).

This is also why the audit state is **process-global atomics and not an `EvalCtx`
field**, registered as a design decision in the prereg §2.2 rather than
discovered afterwards: `EvalCtx` is constructed at many sites, so an `EvalCtx`
field would have made coverage depend on remembering every one of them.

| class | covered | note |
|---|---|---|
| `Argmax`, `Argmin` | **yes** | the class that produced the 272 rows |
| `MaxOver`, `MinOver` | **yes** | winning ELEMENT tracked only while auditing |
| `ArgMax`/`ArgMin { items }` | **yes** | index selector; 0 seed occurrences, built from Python |
| `Pick` / `PickUnique` | **no, by construction** | no value Term ⇒ no extremum to disagree with. `PickUnique` carries its own §12.3 guard |
| `Count(Filter(Eq(·, max)))` | **no** | a count, not a selection. It is the quantity that was CORRECT while the `Argmax` was wrong — i.e. it is the other side of the cross-check |
| `ShapeDecode` internal plan search | **no, named** | selects internally without a selector Term; own scoring semantics; a separate job |

**The effectfulness skip, counted rather than silent.** A value subtree
containing `UseTool` (re-entrant into Python under the GIL) or `ReadFile` (host
I/O) is **not** replayed — doing so would double-fire a side effect, which is a
behaviour change §9 forbids. Those firings increment `skipped_effectful`.

**In-code verification of the walk's soundness (§12.4).** The skip test recurses
via `children()`, whose `match` over `TermNode` is **exhaustive with no catch-all
arm** — verified by reading `term.rs:7831`–`8073`, where the only `=> {}` arm is
the explicit leaf list. The compiler therefore enforces that a newly added
variant cannot hide a nested `UseTool` from this scan. This is exactly the
property `collect_term_reads` lacks, whose generic catch-all `rewrite.rs`
documents as "the only unsafe direction" and which the determinism rung reported
as its unfixed §5.2 defect.

---

## 2. THE POSITIVE CONTROL — red-then-green, and the blindness demonstrated

**A detector that has never fired has not been tested.** The gate
(`tests/test_selector_winner_value_migrated.py`, **11/11**) injects a synthetic
disagreement: the fold returns the **first candidate regardless of value**,
leaving the recorded extremum correct. That is precisely the §4.2 signature — a
constant winner (`fractal`, the lowest-id candidate and so the first the sorted
source yields) while the neighbouring compositions stayed correct.

### 2.1 The decisive test

`test_RED_THEN_GREEN_the_OLD_instrumentation_is_BLIND_to_the_same_fault`
reconstructs the pinned-row configuration on one substrate with scores
`[3.0, 9.0, 5.0]`:

| quantity | with the fault present | verdict |
|---|---|---|
| the `Argmax` winner | the node scoring **3.0** | **WRONG** |
| `MaxOver` (the recorded extremum) | **9.0** | **CORRECT** |
| `Count(Filter(Eq(·, 9.0)))` (the tie count) | **1** | **CORRECT** |
| **the winner's own value vs the extremum** | **3.0 ≠ 9.0** | **CONTRADICTION, caught** |

Rows 2 and 3 are the blindness, **measured rather than argued**: an instrument
reading only the extremum and the tie count sees a maximum of 9.0, unambiguously
attained by exactly one candidate, and reports nothing at all — while the
returned answer is wrong. That is the 272 rows in miniature, and it is why the
arc cost an arc.

Row 4 is the deliverable: **one row, no replay, no statistics, no second
substrate.**

### 2.2 The rest of the gate

- Fires for `Argmax`, `Argmin`, `MaxOver`, `MinOver`.
- `strict` mode raises, so the invariant can be **enforced**, not merely recorded.
- **Both defaults are OFF**, asserted — and because the injector is read *only
  inside the audit branch*, it is **unreachable while the audit is off**. There
  is no state in which a committed measurement can be perturbed by it.
- **The universal-tie case is a deliberate no-op** and that is CORRECT, not a
  miss: where every candidate compares equal the first element *is* a legitimate
  winner. Registered in advance (prereg §5, prediction 2's proviso) — and it
  matters, because §4.1 measured that a universal tie is the one way the native
  fold *can* legitimately return a non-maximal node.

### 2.3 Two defects my own gate found in itself — reported, not quietly fixed

Both were found because the assertions were written to be discriminating, and
both are instances of the rules this protocol already carries:

1. **The `MinOver` injection was a no-op** on scores `[3, 9, 5]`, because the
   first candidate *was* the minimum — so the injected "wrong" winner was the
   right one. The gate failed and said so. Fixed by choosing `[5, 9, 3]`, where
   the first candidate is neither extremum. **A positive control needs its own
   control.**
2. **The first version of the real-workload test was VACUOUS.** It booted a bare
   `WorldAdapter`, which loads no rules, so **zero selectors fired** and the
   "invariant holds" assertion passed on an empty measurement. It was caught only
   by the `assert st["firings"] > 0` line written specifically to catch it. This
   is §12.1 happening to me, in the very rung whose subject is instruments that
   cannot fire. The test now boots the real seed corpus (`vision_sdloop`) and runs
   a `run_rules` fixpoint.

---

## 3. STRICTLY ADDITIVE — the byte-identity evidence

### 3.1 The bench, four ways

| configuration | engine | result |
|---|---|---|
| **baseline, pre-change** | `e59484fe6b2e` | **200 passed, exit 0** |
| instrumented, audit **off** (the default) | `11ee213dfd46` | **200 passed, exit 0** |
| instrumented, audit **warn** | `11ee213dfd46` | **200 passed, exit 0** |
| instrumented, audit **strict** (enforcing) | `11ee213dfd46` | **200 passed, exit 0** |

`bash scripts/rung7_vision_bench.sh` — the named 20-file selector (§12), never
`-k`. **No verdict moved**, including with the invariant actively enforced.

**sd orbit law `{2:1, 3:2, 4:2, 6:2, 12:4}` — UNMOVED**
(`test_the_sd_orbit_law_is_UNMOVED` + `test_orbit_law_arithmetic_...`, 2 passed).

### 3.2 The landed artifacts, re-run and diffed field-by-field

Per prereg §4.3. Two of the seven were re-run in full; the other five were **not**
(stated as a deviation, §7).

| artifact | fields differing | verdict |
|---|---|---|
| `results/time_measure.json` | **`engine` only** — the provenance string, which by design records which binary produced it | **IDENTICAL** |
| `results/blink_measure.json` | `engine`, and `scaling.times_ms` (wall-clock) | **IDENTICAL** |

Every substantive field — every verdict, every measured quantity — reproduced
exactly. Both files were then **reverted**, so no landed artifact's provenance
line was overwritten by this worktree.

### 3.3 Why no wall-clock number is a headline — measured, not asserted

The operational rule for this rung forbids wall-clock measurement under
concurrent load. The bench's own numbers show exactly why:

| run | verdicts | wall clock |
|---|---|---|
| baseline, audit off | 200 passed | **214.72 s** |
| instrumented, audit off | 200 passed | **129.32 s** |
| instrumented, audit warn | 200 passed | **179.76 s** |
| instrumented, audit strict | 200 passed | **179.67 s** |

The two **verdict-identical, functionally-identical** off runs differ by **85
seconds (1.66×)** purely from machine load. Any overhead inferred from these
numbers would be an artifact of the concurrent rung. **This is reported as the
reason the cost is measured by counting instead.**

---

## 4. THE COST — counted, and the prediction was WRONG

Over the full bench under audit (identical to the last count in both the `warn`
and the `strict` run — **bit-for-bit reproducible**, itself a small determinism
datum):

| quantity | value |
|---|---|
| selector firings audited | **60 253 656** |
| candidate value evaluations | **74 015 366** |
| **overhead = firings / candidates** | **0.814070 → 81.41 %** |
| **mean candidates per selector firing** | **1.2284** |
| `skipped_effectful` | **0** |
| `empty` (fold saw no candidates) | 17 |
| **`disagreements`** | **0** |

**The instrument costs 81.41% extra evaluations on the selector path** — one
extra evaluation per firing, over a corpus whose selectors range over an average
of **1.23 candidates**. I predicted 5–40% (prereg §5, prediction 4) and was
badly wrong, in the informative direction: **the modal selector in this corpus is
effectively a singleton.**

**This is a §13 number: it FELL OUT of the candidate-set sizes the committed
seeds actually produce.** No threshold was set in advance, and none is set now.
It is reported, and the design consequence is stated against it: 81% is
unambiguously material, so the instrument **ships OFF by default** (§9), with
`warn` / `strict` selectable per-process by `OZMA_SELECTOR_AUDIT` or
`selector_audit_enable(...)`.

**The observation worth more than the number.** A selector over **one** candidate
is self-consistent almost by construction — there is nothing for the winner to
disagree with except a nondeterministic value evaluation. So the cost is
concentrated precisely where the diagnostic power is lowest, and skipping `N = 1`
would cut the overhead by most of its bulk while losing only the
value-determinism check. **That optimisation is NOT implemented here**: it is a
new design decision, it was not pre-registered, and adding it post-hoc to make a
number look better is the shape of the thing §5 forbids. It is named as the
obvious next lever for whoever wants the audit on by default.

---

## 5. WHERE THE INVARIANT RUNS, AND WHAT IT COSTS TO RUN IT

| site | mode | what it costs |
|---|---|---|
| every process, always | `off` | one relaxed atomic load per selector firing |
| `tests/test_selector_winner_value_migrated.py` | `strict` | 11 tests, 0.17 s |
| any bench / script, opt-in | `OZMA_SELECTOR_AUDIT=strict` | +81.41% selector-path evaluations |
| the full vision bench, demonstrated | `strict` | 200 passed; the invariant enforced over 60.25 M firings |

The recommended standing use, stated plainly: **run the bench under
`OZMA_SELECTOR_AUDIT=strict` before landing any engine change that touches
evaluation order, caching, or the fold helpers** — and, per §6, before and after
the concurrency work.

---

## 6. THE RACE-DETECTION BOUND — as registered, unchanged

Reported exactly as pre-registered in §6 of the prereg, because the value of a
bound written in advance is that it is not trimmed to fit the result.

### 6.1 What it WOULD catch

- **A corruption of the fold's own `best` state** — the observed §4.2 signature.
  Demonstrated, not argued (§2.1).
- **A torn read of a value the fold consumed**, where the re-read differs.
- **A mid-fold graph mutation that changes the winner's value** — caught, but see
  §6.3.

### 6.2 What it would MISS

1. **A stable corruption of the value Term's inputs.** If a race leaves the graph
   in a state where the value Term consistently returns a wrong number, the fold
   and the re-check **agree, and both are wrong**. The instrument checks
   *self-consistency*, not *truth*. **This is the largest miss and it is
   structural.**
2. **A race in the SOURCE set** — a missing node, a stale `NodesOfType` snapshot.
   The selector then correctly picks the extremum *of the wrong set*. Undetected.
3. **A race after the fold returns** — the result being clobbered between
   selection and use is entirely outside this instrument.
4. **Any race in a non-selector Term** — `Count`, `Sum`, `Filter`, `ShapeDecode`'s
   internal search, and every arithmetic Term are uninstrumented.
5. **Firings skipped for effectfulness** (0 on this bench, but not 0 by
   construction).
6. **A race producing a legitimate-looking tie** — where all candidates compare
   equal, any element is admissible and the check passes by construction.

### 6.3 The false-positive class the async plan must handle — the part to read

Under **monotone (add-only) parallelism**, a value Term reading a **growing** set
— `Count(Neighbours(...))`, a running maximum — can legitimately change between
the fold and the re-check. The instrument would then report a contradiction that
is **not a bug**.

> **The invariant as implemented is sound only under a QUIESCENT graph.** That is
> what the current single-threaded `run_rules` guarantees. For this detector to
> remain meaningful *during* a parallel monotone phase, the re-check must be taken
> **under the same graph snapshot as the fold**.

That is a design constraint on the concurrency work, derived before it lands
rather than after. Stated as a recommendation: **snapshot the fold's graph view
and re-check against the snapshot**, or accept that the audit is a
barrier-phase-only instrument.

---

## 7. MY PREDICTIONS, SCORED (§3.7)

| # | prediction | outcome |
|---|---|---|
| 1 | `disagreements = 0` across the bench | **CORRECT** — 0 in 60 253 656 firings. Registered in advance as a predicted NULL precisely so it could not be presented afterwards as evidence of correctness. It is not: it is a null about this bench, this machine, this budget (§8) |
| 2 | the positive control fires on the first firing with ≥2 distinct values | **CORRECT**, including the proviso — the universal-tie case is a no-op and that is correct behaviour, gated explicitly |
| 3 | `skipped_effectful = 0` | **CORRECT** — no seed puts `UseTool`/`ReadFile` inside a selector's value Term |
| 4 | overhead lands between 5% and 40% | **WRONG — 81.41%.** And wrong for a reason I did not know: the mean selector ranges over **1.23** candidates. I had assumed selectors range over meaningful candidate sets; in this corpus they overwhelmingly do not. The prediction was a test of whether I understood the workload, and it says clearly that I did not |
| 5 | the instrument will not catch a stable corruption of the value Term's inputs | **STANDS** — registered in advance as the structural miss, and nothing measured here changes it |

**One of five wrong, and it was the quantitative one.** The three structural
predictions — what the instrument would catch, what it would skip, what it would
miss — held. The one that failed was the one that required knowing what the seed
corpus actually *does*, which is the kind of claim that has to be measured rather
than reasoned to.

---

## 8. SCOPE (§8) — what this does NOT show

- **It does not explain the §4.2 anomaly.** The cause remains **UNESTABLISHED**
  and its blast radius remains as `ENGINE_ARGMAX_DETERMINISM_RESULTS.md` §5.3 left
  it. This rung makes a recurrence **diagnosable in one row**; it does not make it
  less likely, and it is not evidence that it will not recur.
- **A null from an instrument is not a proof of correctness.** 0 disagreements
  says the selectors were self-consistent on the paths the vision bench exercises,
  on this machine, on this engine build. It says nothing about paths not
  exercised — and per §6.2 it would not have caught several whole classes of fault
  even on the paths it did exercise.
- **`ShapeDecode`'s internal plan search is uninstrumented**, and it is the
  component the 272 rows' value Term actually called. The audit checks the
  *selector* around it, not the decode inside it.
- **The 81.41% cost is a property of this seed corpus.** A corpus with larger
  candidate sets would pay proportionally less.
- **Two of the seven registered artifacts were re-run, not all seven** — a
  deviation from prereg §4.3, recorded here rather than papered over. The two that
  were re-run were verdict-identical, and the bench's 200/200 in three
  configurations is the broader evidence.

## 9. AN OPERATIONAL NOTE EARNED EN ROUTE

Copying a `.so` back into place by hand — even the *correct* binary, with the
same `engine_build.sh` hash — **tripped
`test_loaded_engine_is_a_build_of_THIS_TREES_rust_source`** and cost one bench
run (199 passed / 1 failed). A clean `scripts/engine_build.sh` restored it, same
engine hash `11ee213dfd46`, provenance 7/7 green, and the bench then reported
200 / exit 0. **The provenance gate did its job on a genuinely harmless case,
which is the correct behaviour for a gate.** Recorded so the next agent doing a
stash-and-rebuild comparison does not read it as a real divergence — and so that
nobody is tempted to route around it.
