# THE ENDPOINT-ABDUCED GENERATOR — PRE-REGISTRATION

*Written and committed BEFORE any number (PROTOCOL §3). Successor to the
timephi rung (93000–93999), which named this operator as the one thing the
substrate lacks.*

**Branch `worktree-agent-a99c143f06b330681`** — the name I actually see; no
`gamma-substrate/gapabduce` name exists. **Base SHA `77e932f12d6f64a735775b0083c137f9d5df532b`.**

**Seed block: 97000–97999.**

**Engine at pre-registration time: `a1d350bbd23b`** (`own` build via
`scripts/engine_build.sh`, baseline — this rung ADDS RUST, so the engine will
be REBUILT and the results file will carry the NEW hash, not this one).
Provenance gate as its own step: `tests/test_engine_provenance_migrated.py`
**7 passed**. Oracle `scripts/rung7_vision_bench.sh`: **222 passed, 0 failed**
(`data/` symlinked per §10.2 — the with-corpus case).

---

## §3 clause 8 — THE VERBATIM `check_claim` OUTPUT

```
SEED CLAIM 97000-97999: CLEAN -- no collision DETECTED.
  Scope: 805 files with seed sinks; 497 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

**Unresolved sink count: 497 tree-wide.** The silence is priced: this is a
"no collision DETECTED" claim, never "no collision exists". My own runner's
sinks will be re-audited with `scripts/seed_audit.py` and the resolved count +
`unknown_sinks` reported in the results — the predecessor's first audit left one
unknown sink and would have verified nothing.

---

## 1 — THE MECHANISM UNDER TEST

The timephi rung localised the deficit to the absence of one operator and
specified it:

> Solve `G^(k+1)(f_before) = f_after` for `G` — **a DIVISIBILITY TEST, NO
> THRESHOLD.**

**`GapAbduce`** (new Rust Term, additive). Input `sequence` =
`[prefix…(visible), gap…(EMPTY), suffix…(visible)]`, exactly `BlinkBridge`'s
input shape. Unlike every existing temporal mechanism it uses **ONLY THE TWO
ENDPOINTS** — `f_before` = the last visible frame before the gap, `f_after` =
the first visible frame after it. That is what makes it INTERPOLATION rather
than CONTINUATION, and it is why it works at `prefix_len == 1`, the phi
topology, where `BlinkBridge` freezes.

1. Split into prefix / gap-run / suffix. Exactly one gap run; both ends
   non-empty. Otherwise unexplained.
2. `steps = gap + 1`.
3. Total displacement `D` from `infer_translate_offset(f_before, f_after)` —
   the EXISTING helper, unmodified: it requires equal cardinality, a uniform
   integer coordinate shift, and byte-identical non-coord slots. `None` ⇒
   `reason = "not_rigid"`.
4. **THE DIVISIBILITY TEST:** `D[i] % steps == 0` on every coordinate slot.
   Integer arithmetic, exact. **There is no tolerance and no place to put
   one.** Failure ⇒ `reason = "indivisible"`.
5. `D == 0` ⇒ identity ⇒ refused (`reason = "identity"`), matching
   `TimeInfer`'s existing exclusion of the still pattern.
6. `offset = D / steps`. Emit the abduced intermediates `G^t(f_before)`,
   `t = 1..gap`, and `closes` = (`G^steps(f_before)` equals `f_after` exactly).
7. **LINEAR FALLBACK**, the analogue of `TimeInfer`'s: enumerate integer 2×2
   `M` within the data-derived bound (capped by the caller's `max_b`, the
   inherited declared residual) and accept the first `M` with
   `M^steps(f_before) == f_after` exactly. `checked` counts the enumeration.

**§13 by construction, and the newly-named hole is closed too.** Every verdict
is an exact integer equality or a `%`-remainder equality against `0`. **The
brief names a §13 hole found this week — "closing a threshold BY NAMING IT went
green on the walker; a name bound to a literal is a literal."** My AST gate
therefore **RESOLVES module-level `Name` bindings to their literal values** and
treats a Name bound to a number as a literal at the comparison site. That is a
strictly stronger gate than the predecessor's, and it is positive-controlled
against **both** an inline threshold and a NAMED one.

---

## 2 — INHERITED BOUNDS, STATED BEFORE THE RUN

- **`TimeInfer` CANNOT CONSUME A BOUNDED PIXEL FIELD AT ALL** (the timephi
  rung's A1: 576 cells, `time_none`, `checked` 83 520). `GapAbduce` reuses the
  SAME `infer_translate_offset` and is therefore subject to the SAME bound.
  **Every positive result in this rung is CONDITIONAL on a figure/ground split
  the ADAPTER supplies**, exactly as the predecessor's were. **I do not attempt
  to fix ingestion — it is scoped to a concurrent successor and I would
  collide.**
- **The `~11%` per-block motion-sensor error is not consumed here** — this rung
  does not touch the block-match sensor.
- **`has_region` edges are admissibility-checked and silently refused on a bare
  `Substrate`.** This rung uses `boot_core`, not a bare `Substrate`, and the
  wiring control (A0) runs FIRST regardless.
- **`segment_and_track`'s Region node ids are non-deterministic across
  processes.** Nothing here keys on a Region id.
- **VERIFY BEHAVIOUR AGAINST THE ENGINE, NEVER AGAINST A COMMENT.** `term.rs`'s
  `BlinkBridge` doc promises a `gap <= confirm_run` horizon the engine does not
  implement (it confabulates always, with `support/(support+gap)` confidence).
  That is the third comment-vs-engine divergence in a week. **Every claim I make
  about existing behaviour is read off a measurement, not a doc block.**

---

## 3 — THE STIMULUS GRID (independent variables: iterated, never compared against)

Inherited from the predecessor for comparability, `K_GRID` extended.

```
DOT = 4, FIELD_H = 24, FIELD_W = 160, BG = 0, FG = 255, ROW = 8
S_GRID = [1, 2, 4, 6, 8, 12, 16, 20, 32]        (n = 9)
K_GRID = [0, 1, 2, 3, 4, 5, 6, 7]               (n = 8)
```

**`K_GRID` is extended past the predecessor's `0..4` deliberately: an interior
optimum must be given room to appear.** Truncating at 4 would make the
discriminator unable to find the thing it is looking for, which is §12.2's
blind-by-construction defect in the time domain.

`n` is the grid, fixed in advance and exhaustive; every verdict is an exact
integer equality, so there is no sampling and no power analysis to do — except
on the ONE random arm, below.

---

## 4 — PREDICTIONS, STATED IN ADVANCE (§3 clause 7)

### P1 — WIRING CONTROL, RUN FIRST (nothing else is interpretable without it)

- **A0-POS:** a dot displaced by `S = 4` across a `gap = 1` (steps 2, 2 | 4)
  ⇒ CLOSED, `kind == "translate"`, `offset == (0, 2)`, `closes == True`.
- **A0-NEG:** a STATIONARY dot across the same gap ⇒ REFUSED,
  `reason == "identity"`.

**Built and run BEFORE any hypothesis arm** — the phi rung nearly published a
perfect fake null off unwired priors, and the timephi rung's own trap gate was
inert. If either fails the run ABORTS with a distinct exit code and no arm is
read.

### P2 — THE CAPABILITY: DOES THE PHI TOPOLOGY NOW CLOSE?

At `prefix_len == 1` — **the phi topology, one pre-gap sample** — with
`(gap+1) | S`, the gap CLOSES: `closes == True`, `correction == 0`,
`offset == (0, S/(gap+1))`.

**This is the arm that is NOT forced by the ISI arithmetic, and it is the
capability claim of the rung.** The predecessor measured, at the identical
topology, `BlinkBridge` FREEZING: confidence 0.00, `correction = 32` (the dot's
16 cells counted twice), identical at S=4 and S=16. **Two-sided: if the gap does
not close here, the operator is not built and the rung's headline is a null.**

### P3 — THE DIVISIBILITY COMB

Over the full 9 × 8 grid, `A(S,k) == 1` **exactly iff `(k+1) | S`** — no
exception in either direction, except where the linear class rescues a cell
(P4). Predicted acceptance, computed in advance:

| k | steps | S accepted | R(k) |
|---|---|---|---|
| 0 | 1 | all 9 | **1.000** |
| 1 | 2 | 2,4,6,8,12,16,20,32 | 0.889 |
| 2 | 3 | 6,12 | 0.222 |
| 3 | 4 | 4,8,12,16,20,32 | 0.667 |
| 4 | 5 | 20 | 0.111 |
| 5 | 6 | 6,12 | 0.222 |
| 6 | 7 | — | 0.000 |
| 7 | 8 | 8,16,32 | 0.333 |

### P4 — LINEAR RESCUE (genuinely open; I am not confident)

I predict the linear class rescues **ZERO** non-divisible cells: a pure lateral
translation of a block is not the `steps`-th power of any non-identity integer
2×2 linear map acting about the origin on this configuration. **Two-sided.** If
it rescues cells, the comb is not the curve and P3/P5 are read off the MEASURED
matrix, not the predicted one.

### P5 — THE ISI CURVE SHAPE: I PREDICT THE PREDECESSOR'S NAMED PREDICTION IS **FALSIFIED**

The timephi rung named this operator and predicted it *"also predicts an
INTERIOR ISI OPTIMUM — the shape of the human psychophysical curve … because a
longer gap admits more candidate generators and the MDL floor should refuse the
over-explained ones."*

**I predict that is WRONG, and I say so before measuring.** The reasoning, in
full, so that it can be checked against the measurement:

1. **The abduced generator is UNIQUE, not multiple.** For a translate, `G` is
   `D/steps` — one candidate, fully determined by the endpoints and the gap.
   There is no multiplicity for an MDL floor to refuse. The predecessor's
   "more candidate generators at longer gaps" does not hold for the class its
   own divisibility test is defined on.
2. **`R(0) = 1` is a THEOREM, not a measurement:** every integer is divisible
   by 1, so at `gap = 0` the abduction accepts every displacement. At `gap = 0`
   the operator DEGENERATES INTO THE VACUOUS N=2 CASE the predecessor already
   measured at 9/9.
3. **MDL points the same way.** Explaining the observation by motion asserts
   `gap` unobserved intermediate frames; that cost GROWS with the gap while the
   two-event alternative's cost is flat. The motion explanation is therefore
   CHEAPEST at `gap = 0`. Monotone, maximal at zero.

**⇒ maximal at ISI = 0, no interior optimum. The arc's inverted curve is not
fixed by this operator.**

### P6 — THERE IS NO MDL REFUSAL TO BE HAD (the noise arm, with its analytic expectation computed FIRST)

**The predecessor's noise control was not a noise control** — three uniform
draws are equally spaced ~1/156 of the time, so a "spurious" accept was the
mechanism being correct. **The same trap is present here in a MUCH larger
form, and I compute it in advance rather than discover it after.**

Any two same-shape dots are related by a rigid translate. So on independent
random endpoints the abduction accepts iff the difference is divisible and
non-zero:

> **P(accept | steps `d`) = P((c₂ − c₁) ≡ 0 mod `d`) − P(c₂ = c₁) ≈ 1/d − 1/H**,
> with `H = FIELD_W − DOT = 156`.

Approximately **0.99, 0.49, 0.33, 0.24, 0.19, 0.16, 0.14, 0.12** for k = 0..7.
**The exact expectation is computed from the grid inside the runner and
compared against the measurement.** The registered reading:

- **the measured rate MATCHES the analytic expectation** ⇒ **P6 CONFIRMED: the
  operator has NO discriminative power on the translate class.** Endpoint
  abduction with one pre-gap sample is UNCONSTRAINED — this is the deep
  contrast with `TimeInfer` at N≥3, which refused ACCEL and SHUFFLE 18/18
  because the third frame CONSTRAINS. **Interpolation is cheap precisely
  because two points and one free generator always fit.**
- **the measured rate is ~0** ⇒ P6 refuted, and something is refusing that I
  have not modelled — which would be the most interesting outcome in the rung
  and would require diagnosis before any other claim is read.

A **second, genuinely-null arm** (`NON-TRANSLATE`): endpoints that are not
rigid translates of each other (a dot of a DIFFERENT SIZE). Predicted
acceptance **0**. **Declared FORCED (§13.1): `infer_translate_offset` refuses
unequal cardinality at source, so this arm cannot produce a positive and
carries no evidential weight** — it is run only to confirm the source reading
against the real engine, which is exactly the thing a doc comment failed at
this week.

n = **100 draws per k** (seeds 97000–97799, 100 per k for k = 0..7) and **100**
for the non-translate arm (97800–97899). At p = 0.125 (the tightest case,
k = 7) SE = 0.033, so 1/8 is separated from 0 by ~3.8 SE: **n is fixed in
advance by that calculation and is not revisited.**

### P7 — §13, AND THE NEWLY-NAMED HOLE

No threshold enters. The AST gate goes **RED** on an injected inline threshold
**AND** on a threshold NAMED by a module-level constant (`a name bound to a
literal is a literal`), and the unmodified source is asserted green in the same
test. **A gate I have only ever seen pass is not a gate I have tested.**

---

## 5 — THE REGISTERED ISI DISCRIMINATOR (decided in advance, not after)

Let `R(k)` = the fraction of `S_GRID` at which the gap closes, and
`k* = argmax_k R(k)` (**lowest k on a tie**).

| verdict | condition | meaning |
|---|---|---|
| **INTERIOR OPTIMUM — CONFIRMS** | `k* >= 1` **AND** `R(k*) > R(0)` **strictly** | the operator acquires the human curve's shape |
| **FALSIFIES** | `R(0) >= R(k)` for **every** k — i.e. `R(0)` is a global maximum | the operator does NOT fix the arc's inverted curve |
| **AMBIGUOUS** | `R(0)` is a global maximum but **TIED** with some `k >= 1` | no interior optimum claimed; reported as a tie |

**THE TRAP THIS DISCRIMINATOR EXISTS TO CLOSE, NAMED IN ADVANCE:** the divisor
comb is **JAGGED** — `R(2) = 0.222 < R(3) = 0.667` — so the curve is
**NON-MONOTONE**. **NON-MONOTONICITY IS NOT AN INTERIOR OPTIMUM AND MUST NOT
BE READ AS ONE.** A rung that registered only "is it monotone?" would score
this comb as CONFIRMING the interior optimum and publish the opposite of the
truth. The maximum's LOCATION is the discriminator; the jaggedness is
arithmetic.

**AND THE §13.1 DECLARATION, MADE BEFORE THE RUN:** `R(0) = 1.000` is **FORCED
BY THE MECHANISM** — divisibility by 1 is universal. **So the falsification is
a DERIVATION, and the measurement's job is to confirm that the implementation
matches the derivation** (i.e. that I built what I described), plus to measure
the parts that are genuinely NOT forced: **P2** (does the phi topology close at
all — the capability), **P4** (does the linear class rescue anything), and
**P6** (the noise rate). **I will not claim the ISI shape as an empirical
discovery. It is a correction to a named prediction, and it is reported as
one.**

---

## 6 — WHAT A NULL MEANS (§3 clause 5)

- **P2 fails** ⇒ the operator is not built; the rung is a null and the
  timephi rung's "the substrate has no operator of that shape" stands
  unchanged. Everything downstream is uninterpretable and is not reported as
  a result.
- **P5 falsified as predicted** ⇒ **endpoint abduction is NOT the missing piece
  of the ISI curve.** It closes the phi topology (a real capability) without
  buying the human parameter dependence. The arc's inverted ISI curve survives
  a mechanism built specifically to fix it, and the next lever must come from
  somewhere else.
- **P5 confirmed** ⇒ the predecessor was right and I was wrong, and the
  reasoning in P5 above says exactly which step of mine to distrust.
- **P6 confirmed** ⇒ the operator is unconstrained, which is a scope limit on
  P2's capability claim and must be stated in the same breath as it.

---

## 7 — EXACTLY THESE ARMS. NO SWEEPS. NO RE-RUNS.

A0 (wiring) · A1 (P2, the capability at prefix_len 1) · A2 (P3/P4, the full
S×k matrix) · A3 (P5, the ISI curve + discriminator) · A4 (P6, both noise arms)
· A5 (§13 AST gate + its two injections).

A further attempt needs a NEW pre-registration with a NEW mechanism-level
hypothesis — never a parameter search.

**§9: the new Term is ADDITIVE and the new seed is flag-gated OFF by default.
Every committed result must reproduce exactly; the oracle is re-run after all
changes and must still read 222/0.**

**I will report what I got wrong.**
