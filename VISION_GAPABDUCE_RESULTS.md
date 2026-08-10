# THE ENDPOINT-ABDUCED GENERATOR — RESULTS

Pre-registration `VISION_GAPABDUCE_PREREG.md`, committed **`8a5fd11c`** before
any number. Branch **`worktree-agent-a99c143f06b330681`** — the name I actually
see; no `gamma-substrate/gapabduce` name exists. Base SHA
**`77e932f12d6f64a735775b0083c137f9d5df532b`**.

Engine **`9931e144d19b`** (`own` build, `scripts/engine_build.sh`) — **THIS RUNG
ADDS RUST.** Provenance gate as its **own step before any number**:
`tests/test_engine_provenance_migrated.py` **7 passed** — and `provenance_line()`
is ALSO printed **from inside the measuring process** and compared against
`EXPECT_ENGINE`, **aborting on divergence**.

Oracle `scripts/rung7_vision_bench.sh`: **222 passed, 0 failed** — `data/`
symlinked (§10.2, the with-corpus case). **Re-run after all changes: 222 / 0,
unchanged.** Rust: `cargo test --lib -- --test-threads=1` **622 passed, 0
failed**, including `variant_table_covers_the_enum`.

Seeds **97000–97999**, `check_claim` recorded in the pre-registration.
**Measured with `scripts/seed_audit.py`: 900 resolved (97000–97899),
`unknown_sinks: 0`, `parse_errors: 0`, none outside the block.**

---

## THE HEADLINE, IN SIX LINES

**THE OPERATOR IS BUILT, IT CLOSES THE PHI TOPOLOGY EXACTLY — AND IT DOES NOT
BUY THE HUMAN ISI CURVE.** At `prefix_len = 1`, the one-pre-gap-sample topology
where `BlinkBridge` FREEZES with `correction = 32`, `GapAbduce` closes the gap
with **`correction = 0` in 31 of 31 divisible conditions**.

**The registered ISI discriminator returns FALSIFIED.** `R(0) = 1.000` is the
unique global maximum, `k* = 0`, **no tie**. The curve is a **DIVISOR COMB** —
non-monotone (`R(2) = 0.222 < R(3) = 0.667`) and maximal at zero. **I registered
that non-monotonicity is NOT an interior optimum before I measured, which is the
only reason this reads as a falsification instead of a confirmation.**

**And the deep result is the noise arm: the operator has NO DISCRIMINATIVE
POWER.** Independent random endpoints are accepted at the analytic rate
`≈1/steps` — 43%, 37%, 22%, 19% at k = 1..4 — because **any two same-shape
figures ARE rigid translates.** `TimeInfer` at N≥3 refuses ACCEL and SHUFFLE
18/18 because a third frame CONSTRAINS. **Two endpoints and one free generator
always fit. Interpolation is cheap for exactly the reason continuation is safe.**

**All seven registered predictions confirmed, including the one that says the
predecessor's named prediction is wrong.**

---

## 0 — THE WIRING CONTROL, RUN FIRST

*The phi rung nearly published a perfect fake null (`has_region` edges silently
refused ⇒ priors always empty ⇒ the same verdict at every separation). The
timephi rung's own trap gate was inert. Both controls were built here first.*

| control | result | |
|---|---|---|
| **A0-POS** dot +4 across gap 1 | abduced, `closes`, `offset=(0,2)`, `correction=0` | wiring **live** |
| **A0-NEG** stationary dot, same gap | refused, `reason="identity"` | reader **discriminates** |

**The codebook-liveness probe: 0 violations across every measured call.** It is
a **paired in-process POSITIVE probe** on a known-good abduction, not a read of
`coord_dims` off the measured call — that field is hardcoded empty by the
refusal constructor, so it is an **OUTPUT of the verdict** and made **167 false
accusations** for my predecessor. §1.1 is easier to quote than to obey, so this
rung did not read it at all.

---

## 1 — A1: THE CAPABILITY (P2) — THE PHI TOPOLOGY CLOSES

**`prefix_len = 1`. One pre-gap sample. This is what a phi stimulus IS.**
31 divisible conditions across the 9 × 8 grid.

| S | abduced per-step offsets, by k |
|---|---|
| 1 | k=0:(0,1) |
| 2 | k=0:(0,2) k=1:(0,1) |
| 4 | k=0:(0,4) k=1:(0,2) k=3:(0,1) |
| 6 | k=0:(0,6) k=1:(0,3) k=2:(0,2) k=5:(0,1) |
| 8 | k=0:(0,8) k=1:(0,4) k=3:(0,2) k=7:(0,1) |
| 12 | k=0:(0,12) k=1:(0,6) k=2:(0,4) k=3:(0,3) k=5:(0,2) |
| 16 | k=0:(0,16) k=1:(0,8) k=3:(0,4) k=7:(0,2) |
| 20 | k=0:(0,20) k=1:(0,10) k=3:(0,5) k=4:(0,4) |
| 32 | k=0:(0,32) k=1:(0,16) k=3:(0,8) k=7:(0,4) |

**`correction = 0` in all 31. P2 confirmed.**

**THE CONTRAST, ON THE SAME STIMULUS, ASSERTED IN THE GATE:**

| operator at `prefix_len = 1`, S=4, k=1 | verdict |
|---|---|
| `BlinkBridge` (the incumbent) | `kind = "freeze"`, confidence 0.00, **correction 32** |
| **`GapAbduce`** | `kind = "translate"`, `offset (0,2)`, **correction 0** |

**32 is the dot's 16 cells counted twice — absent where the belief put them,
present where they actually are.** That quantity goes to zero. The timephi
rung's registered null-reading — *"CONTINUATION, NEVER INTERPOLATION … the
substrate has no operator of that shape"* — **is now false, and it is false
because the operator was built, not because the reading was wrong.**

---

## 2 — A2: THE DIVISIBILITY COMB (P3) AND THE LINEAR CLASS (P4)

The full 9 × 8 grid, 72 cells. `Y` = the gap closes.

```
      k=   0   1   2   3   4   5   6   7
  S=  1   Y   .   .   .   .   .   .   .
  S=  2   Y   Y   .   .   .   .   .   .
  S=  4   Y   Y   .   Y   .   .   .   .
  S=  6   Y   Y   Y   .   .   Y   .   .
  S=  8   Y   Y   .   Y   .   .   .   Y
  S= 12   Y   Y   Y   Y   .   Y   .   .
  S= 16   Y   Y   .   Y   .   .   .   Y
  S= 20   Y   Y   .   Y   Y   .   .   .
  S= 32   Y   Y   .   Y   .   .   .   Y
```

**P3 confirmed, 72/72: the gap closes EXACTLY IFF `(k+1)` divides `S`** — a
biconditional with no exception in either direction. **P4 confirmed: 0 cells
rescued by the linear class.** The `steps`-th-root enumeration runs (`checked`
non-zero on every indivisible cell) and finds nothing — so the refusals are
**FAILURES after a full search, not refusals at a guard**, which is what makes
this null diagnosable rather than a shrug.

A refusal also carries its measured endpoint displacement (`total = (0,5)` at
S=5) and a `reason` (`identity` / `indivisible` / `not_rigid` /
`no_gap_structure`). **An indivisible D is a NUMBER, not an absence.**

---

## 3 — A3: THE ISI CURVE, AND THE REGISTERED DISCRIMINATOR

| k | steps | R(k) | |
|---|---|---|---|
| **0** | 1 | **1.000** | `########################################` |
| 1 | 2 | 0.889 | `####################################` |
| 2 | 3 | 0.222 | `#########` |
| 3 | 4 | 0.667 | `###########################` |
| 4 | 5 | 0.111 | `####` |
| 5 | 6 | 0.222 | `#########` |
| 6 | 7 | 0.000 | |
| 7 | 8 | 0.333 | `#############` |

**`k* = 0`. `R(0) = 1.000`. No tie with any `k ≥ 1`.**

### THE REGISTERED VERDICT: **FALSIFIED**

| branch | condition | outcome |
|---|---|---|
| INTERIOR OPTIMUM | `k* != 0` AND `R(k*) > R(0)` strictly | ❌ |
| **FALSIFIES** | `R(0) >= R(k)` for every k | ✅ |
| AMBIGUOUS | `R(0)` max but tied with some `k >= 1` | ❌ (no ties) |

**THE TRAP THIS DISCRIMINATOR EXISTS TO CLOSE, AND IT WOULD HAVE CAUGHT ME.**
The comb is **NON-MONOTONE**: `R(2) = 0.222 < R(3) = 0.667`. A rung that had
registered only *"is the ISI dependence monotone?"* — the natural question,
given that every mechanism in this arc so far produced a monotone inverted curve
— **would have measured non-monotonicity and scored it as CONFIRMING the interior
optimum, publishing the exact opposite of the truth.** The maximum's **LOCATION**
is the discriminator. The jaggedness is arithmetic.

### §13.1: THIS FALSIFICATION IS A DERIVATION, AND IT WAS DECLARED AS ONE

**`R(0) = 1.000` is FORCED BY THE MECHANISM** — every integer is divisible by 1
— and the pre-registration says so **before the run**, along with the reasoning
that kills the predecessor's prediction:

1. **The abduced generator is UNIQUE, not multiple.** For a translate `G` is
   `D/steps`: one candidate, fully determined by the endpoints and the gap.
   **There is no multiplicity for an MDL floor to refuse.** The predecessor's
   *"a longer gap admits more candidate generators"* does not hold for the class
   its own divisibility test is defined on. **Measured, not just argued: P4's
   linear enumeration found zero alternative generators at any gap.**
2. **At `gap = 0` the operator DEGENERATES into the vacuous N=2 case** the
   predecessor already measured at 9/9.
3. **MDL points the same way**: the motion explanation asserts `gap` unobserved
   frames, a cost that GROWS with the gap while the two-event alternative's is
   flat. Cheapest at zero.

**So I claim nothing here as an empirical discovery. This is a correction to a
named prediction, confirmed by measurement that the implementation matches the
derivation.** What was genuinely NOT forced — and is therefore where this rung's
evidential weight actually sits — is **A1 (the capability)**, **A2's P4 (does
the linear class rescue anything)**, and **A4 (the noise rate)**.

---

## 4 — A4: THE NOISE ARM — AND THE ANALYTIC EXPECTATION WAS COMPUTED FIRST

*The predecessor's noise control was not a noise control: three uniform draws
are equally spaced ~1/156 of the time, so a "spurious" accept was the mechanism
being CORRECT. **The same trap is present here in a far larger form**, and the
pre-registration computes it in advance rather than discovering it after.*

n = 100 per k, seeds 97000–97799. Endpoints drawn independently.

| k | steps | accepted | rate | **analytic expectation** |
|---|---|---|---|---|
| 0 | 1 | 100/100 | 1.000 | **0.994** |
| 1 | 2 | 43/100 | 0.430 | **0.494** |
| 2 | 3 | 37/100 | 0.370 | **0.327** |
| 3 | 4 | 22/100 | 0.220 | **0.244** |
| 4 | 5 | 19/100 | 0.190 | **0.194** |
| 5 | 6 | 15/100 | 0.150 | **0.160** |
| 6 | 7 | 14/100 | 0.140 | **0.137** |
| 7 | 8 | 11/100 | 0.110 | **0.119** |

**Every cell is within ~1.3 SE of its analytic expectation.** The formula
(`P((c₂−c₁) ≡ 0 mod steps) − P(c₂ = c₁)`) is computed exactly from the grid
inside the runner, registered in advance as a FORMULA rather than a remembered
approximation.

### P6 CONFIRMED — AND THIS IS THE RUNG'S DEEPEST RESULT

**The operator has NO DISCRIMINATIVE POWER ON THE TRANSLATE CLASS.** Any two
same-shape figures ARE rigid translates of one another, so divisibility is the
**only** constraint the abduction applies — and the acceptance rate on pure
noise is `1/steps`, **not zero**.

Set against the predecessor's headline:

| | constraint | noise acceptance |
|---|---|---|
| `TimeInfer`, N ≥ 3 (**continuation**) | a THIRD frame must lie on the orbit | **0/100** (ACCEL and SHUFFLE refused 18/18) |
| **`GapAbduce` (interpolation)** | divisibility, and nothing else | **~1/steps** |

**That is the honest price of the capability, and it is the structural reason
the substrate was continuation-only in the first place.** Continuation is
CONSTRAINED because verification across every consecutive pair can fail.
Interpolation is constrained by nothing, because **two points and one free
generator always fit.** The substrate did not lack this operator by oversight;
it lacked the operator that cannot refuse.

**The NON-TRANSLATE arm** (endpoints of different dot size): **0/100.**
**DECLARED FORCED in advance (§13.1)** — the cardinality check refuses at
source, so it could not have produced a positive and **carries no evidential
weight.** It is run only to confirm the source reading against the real engine,
which is the thing a doc comment failed at this week.

---

## 5 — §13: NO NUMBER ENTERED, AND THE NEWLY-NAMED HOLE IS CLOSED

**§13 is satisfied BY CONSTRUCTION, as the brief predicted it would be.** The
admissibility test is `D[i] % steps == 0` — exact integer arithmetic. **There is
no tolerance in it and nowhere to put one.** This is the strongest §13 outcome
available: not a number that falls out, but **no number at all**. `steps` is
`gap + 1`, a COUNT that falls out of the sequence's own length.

**I did not need a tolerance at any point, so there is nothing to report under
the brief's "if you find yourself needing one, that is a finding" clause.**

### THE §13 HOLE NAMED THIS WEEK — CLOSED, AND PROVEN LOAD-BEARING

> *"closing a threshold BY NAMING IT went green on the walker. **A name bound to
> a literal is a literal.**"*

`tests/test_gapabduce_ast_migrated.py` — **8 passed.** A Python **AST walk**,
never a substring selector (this arc's record on those is 0–5, and the fifth
happened *inside the test written to warn about substring selectors*).

- verdict functions bound as `ast.FunctionDef` nodes **by name, read from the
  runner's OWN `VERDICTS` tuple** — the gate carries no copy, and a divergence
  is itself a failure (**non-vacuity**);
- **subscript indices PRUNED** by explicit recursive descent — *`ast.walk`
  CANNOT PRUNE*, which is why the phi rung's **fix** was also wrong;
- **MODULE-LEVEL NAME BINDINGS RESOLVED TO THEIR LITERALS** — the new clause;
- **no ORDERING comparison against a non-zero literal, inline or named.** This
  is the sharp form: an ordering against a constant is a threshold **because you
  can slide it to adjust sensitivity**. An equality is not tunable — moving
  `== 1` to `== 2` tests a different proposition. Orderings are admitted only
  between two MEASURED quantities, or against the sentinel `0`;
- swept axes (`S_GRID`, `K_GRID`) **iterated, never compared against**;
- the dead-instrument arms **ABORT** (`return 2` engine divergence, `return 3`
  wiring control), never warn.

**POSITIVE-CONTROLLED THREE WAYS, and the poisoned source was read by hand from
the parser's own view** (§12.3 — the supervisor's first verification of a
similar gate landed on the wrong node and passed):

| injection | result |
|---|---|
| inline `v["checked"] < 2400` | **RED** — `ordering-threshold:v_a2_p4:2400.0` |
| **named** `CHECK_TOL = 2400` … `< CHECK_TOL` | **RED** — same finding, one indirection away |
| axis `v["steps"] > max(K_GRID)` | **RED** — `axis-compared:v_a2_p4:K_GRID` |
| unmodified source | **GREEN**, asserted in the same test |

**AND THE NEW CLAUSE WAS VACUITY-GATED AGAINST ITSELF (§13.2).** With the name
resolver blinded, the named injection scans to **`[]`** — it walks straight
through. **So the clause is LOAD-BEARING, not decorative**, and the hole named
this week was real in this gate before it was closed.

**Declared residuals, labelled CONFIGURATION and nothing stronger:** `DOT=4`,
`FIELD_H/W`, `BG`, `FG`, `ROW` (stimulus construction, inherited from the
phi/timephi rungs); **`max_b = 8`** is a compute cap on the linear enumeration,
inherited unchanged. **The claim made about all of these is the weak one — bound
once, never a verdict threshold — not that they fell out.**

---

## 6 — §9: DEFAULTS PRESERVE COMMITTED RESULTS

- The Rust is **ADDITIVE**: one new `TermNode` variant appended at the **END** of
  the enum (index **175**), so `term_variants.rs` regenerates with **3
  insertions and 1 deletion** and **every existing variant index is unmoved**.
  No existing Term, evaluator, or seed is touched.
- `seeds/gap_abduce.json` is **flag-gated on `gap_abduce_enabled`, absent by
  default**, and additionally matches only `status == "gap_seq"`. Asserted:
  with the flag off the Observation's status is **unchanged**.
- **Oracle 222/0 before and after. `cargo test --lib` 622/0.**

---

## 7 — WHAT IS NOT SHOWN (§8)

- **Nothing about human phi's mechanism.** Human phi enters only as the
  parameter dependence compared against. No human data was measured.
- **EVERY POSITIVE RESULT IS CONDITIONAL ON A SUPPLIED FIGURE/GROUND SPLIT.**
  `GapAbduce` reuses `infer_translate_offset`, so the timephi rung's A1 bound
  applies UNCHANGED: **it cannot consume a bounded pixel field at all.** The
  segmentation is the adapter's, not the graph's. **I did not attempt to fix
  ingestion — it is scoped to a concurrent successor and I would have collided.**
- **The ISI falsification is a DERIVATION confirmed, not an empirical
  discovery** (§3 above). It is reported as one.
- **The NON-TRANSLATE null is FORCED** and carries no evidential weight.
- **This does NOT show the substrate now "sees phi."** It shows one named
  missing operator exists and closes the topology. **The operator that closes it
  cannot refuse anything**, which is a scope limit on the capability, not a
  footnote to it.
- **One dot, one shape, one size, horizontal only, uniform background.** The
  phi/timephi scope limits are inherited unchanged. **A textured background was
  NOT run.**
- **`R(k)` is a marginal over `S_GRID`**, and the choice of grid sets its
  values. The full 9 × 8 matrix is reported so the marginal can be recomputed.
- **No timing claim of any kind.** Every quantity is exact or counted.
- **The linear class was searched only within `max_b = 8`.** "No linear rescue"
  is bounded by that cap.

---

## 8 — WHAT I GOT WRONG

1. **MY OWN TERM'S DOC COMMENT DIVERGED FROM MY OWN ENGINE WITHIN THE HOUR —
   while I was writing a pre-registration section about exactly that failure
   mode.** The doc said `gap == 0` is admissible (the degenerate ISI=0 case, and
   my prereg registered `R(0)` as a grid point); the code returned
   `no_gap_structure`, because the prefix scan consumed *all* leading visible
   frames and left no resume bank. **Caught by the smoke test, before any
   hypothesis number.** Fixed to match the registered spec. **This is the fourth
   comment-vs-engine divergence recorded in a week and the first one that was
   the author's own, in the same session as the warning.**
2. **`refused()` calls `finish()`, which SELECTS the field — so my patch that
   restored `total` on a refusal silently did nothing** on every call that asked
   for `total`. It read `()` where it should have read `(0,5)`. **Caught by the
   mechanism test, not by inspection**, and it is precisely the shape this arc
   keeps finding: a value that is an *output of the constructor* rather than a
   measurement. Fixed at source; the re-run differs from the pre-fix run in
   **exactly 42 `total` fields and the engine hash, with every verdict, the ISI
   curve, and the noise arm identical** (verified by structural diff).
3. **I wrote an ordering against a non-zero literal into a verdict** —
   `kstar >= 1` — in the same file whose gate forbids exactly that. It states
   the same proposition as `kstar != 0` on a grid starting at 0, so the gate did
   not fire on the *registered* discriminator, but it was a threshold's shape.
   Tightened after the run and before the write-up (§1.1 permits making a
   measure stricter against yourself; §5 forbids only loosening one), and the
   re-run asserted **byte-identical**.
4. **My first instinct for the k=0 fix was to special-case the two-frame
   sequence in the RUNNER** rather than in the Term. That would have spliced a
   different code path into one end of the ISI curve — the curve's zero point
   would not have been the same operator as the rest of it, and the
   discriminator would have been comparing two mechanisms. Caught before
   writing it.
5. **I under-estimated how much of this rung would be forced.** The
   pre-registration treats P3/P5 as substantive arms; on reflection *while
   writing it* both are derivable, and only P2/P4/P6 carry weight. I registered
   that honestly rather than discovering it afterwards — but the first draft of
   the prereg did not, and the §13.1 declaration was added on a second pass.

---

## 9 — NAMED NEXT LEVERS, EACH NEEDING ITS OWN PRE-REGISTRATION

1. **A CONSTRAINT ON THE ABDUCTION — the lever this rung earns.** The operator
   accepts noise at `1/steps` because divisibility is its only test. The obvious
   candidate constraint is **the abduced intermediates themselves**: they are
   emitted (`bridged`) and currently checked against nothing. In a scene with
   *any* other content, `G^t(f_before)` makes a falsifiable prediction at every
   gap tick. **That would make interpolation refusable — and it would be the
   first mechanism here whose ISI curve could have an interior optimum, because
   a longer gap means MORE predictions to violate.** *The predecessor's
   intuition may be right about the curve and wrong about which quantity
   supplies it.*
2. **THE ISI CURVE IS STILL UNEXPLAINED, AND IT HAS NOW SURVIVED A MECHANISM
   BUILT SPECIFICALLY TO FIX IT.** Four mechanisms, one shape: maximal at
   ISI = 0. That is now a robust negative about this substrate, not a gap in one
   operator.
3. **A textured background at `prefix_len = 1`.** The figure split is the
   load-bearing assumption of this rung and its two predecessors, and is still
   untested against texture.
4. **The stale `BlinkBridge` doc comment in `term.rs`** — reported by the
   predecessor, **still unedited** (not this rung's file), and now joined by a
   fourth instance that was my own. **A comment-vs-engine gate is worth building.**

---

## 10 — LEDGER ROW (for the supervisor to merge into `VISION_PROTOCOL.md`)

*Written here, not there — `VISION_PROTOCOL.md` is not this rung's file.*

| range | used for |
|---|---|
| **97000–97999 (900 seeds resolved, unknown_sinks 0, parse_errors 0, none outside block)** | **THE ENDPOINT-ABDUCED GENERATOR IS BUILT AND CLOSES THE PHI TOPOLOGY — AND THE INTERIOR-ISI-OPTIMUM PREDICTION IT WAS NAMED TO TEST IS FALSIFIED.** New Rust Term **`GapAbduce`** (ADDITIVE, appended at enum index 175 so every existing variant index is UNMOVED; seed flag-gated OFF by default): solves `G^(gap+1)(f_before) = f_after` from **THE TWO ENDPOINTS ALONE** — INTERPOLATION, where every incumbent (`TimeInfer`/`DepthInfer`/`BlinkBridge`) infers `G` from a consecutive VISIBLE PAIR and EXTRAPOLATES. **P2 CONFIRMED 31/31: at `prefix_len=1` (THE PHI TOPOLOGY) the gap closes with `correction = 0`, where `BlinkBridge` on the IDENTICAL stimulus reports `kind='freeze'`, confidence 0.00, `correction = 32` — asserted as a paired contrast in the gate.** **P3 CONFIRMED 72/72: closes EXACTLY IFF `(gap+1) | S`, a biconditional with no exception either way. P4 CONFIRMED: 0 linear rescues — the `steps`-th-root enumeration RUNS and finds nothing, so refusals are FAILURES after a full search, not refusals at a guard.** **THE REGISTERED ISI DISCRIMINATOR RETURNS `FALSIFIED`: `R(0)=1.000` is the UNIQUE global max, `k*=0`, no tie. THE CURVE IS A DIVISOR COMB AND IS NON-MONOTONE (`R(2)=0.222 < R(3)=0.667`) — AND THE PRE-REGISTRATION REGISTERED, BEFORE MEASURING, THAT NON-MONOTONICITY IS NOT AN INTERIOR OPTIMUM: a rung that had asked only "is it monotone?" (the natural question, since every prior mechanism gave a monotone inverted curve) WOULD HAVE SCORED THIS COMB AS CONFIRMING AND PUBLISHED THE OPPOSITE OF THE TRUTH. The maximum's LOCATION is the discriminator; the jaggedness is arithmetic.** **§13.1 DECLARED IN ADVANCE: `R(0)=1` is FORCED (every integer divides by 1), so the falsification is a DERIVATION confirmed — claimed as a correction to a named prediction, NOT as an empirical discovery; the weight sits on P2/P4/P6, which are not forced.** **P6 IS THE DEEPEST RESULT — THE OPERATOR HAS NO DISCRIMINATIVE POWER: independent random endpoints accept at the ANALYTIC rate `~1/steps` (43/37/22/19% at k=1..4, every cell within ~1.3 SE of an expectation COMPUTED FROM A REGISTERED FORMULA BEFORE THE ARM WAS READ — the predecessor's noise-control lesson applied prospectively), because ANY TWO SAME-SHAPE FIGURES ARE RIGID TRANSLATES. `TimeInfer` at N≥3 refuses ACCEL/SHUFFLE 18/18 because a THIRD FRAME CONSTRAINS; two endpoints and one free generator ALWAYS FIT. THE SUBSTRATE DID NOT LACK THIS OPERATOR BY OVERSIGHT — IT LACKED THE OPERATOR THAT CANNOT REFUSE.** **§13 SATISFIED BY CONSTRUCTION (`D[i] % steps == 0`, exact integer arithmetic — no tolerance and nowhere to put one; NO NUMBER AT ALL, not merely one that falls out); NO tolerance was needed at any point. THE §13 HOLE NAMED THIS WEEK IS CLOSED AND PROVEN LOAD-BEARING: the AST gate RESOLVES MODULE-LEVEL NAME BINDINGS TO THEIR LITERALS, forbids ORDERING against any non-zero literal (inline OR named) while admitting EQUALITY (an ordering is slidable, an equality is not), prunes subscript indices by EXPLICIT DESCENT because `ast.walk` CANNOT PRUNE, and is POSITIVE-CONTROLLED THREE WAYS with the poisoned source read by hand from the parser's own view — AND WITH THE NAME RESOLVER BLINDED THE NAMED INJECTION SCANS TO `[]`, i.e. the new clause is LOAD-BEARING, not decorative.** **WHAT IT GOT WRONG: (1) MY OWN TERM'S DOC COMMENT DIVERGED FROM MY OWN ENGINE WITHIN THE HOUR, WHILE I WAS WRITING THE PREREG SECTION ABOUT THAT EXACT FAILURE MODE — the doc said `gap==0` admissible, the code returned `no_gap_structure`; caught by the smoke test BEFORE any hypothesis number (FOURTH comment-vs-engine divergence in a week, first one authored by the warner); (2) `refused()` calls `finish()`, WHICH SELECTS THE FIELD, so my patch restoring `total` on a refusal SILENTLY DID NOTHING — an output of the constructor masquerading as a measurement, the shape this arc keeps finding; caught by the MECHANISM TEST, fixed at source, re-run differs in EXACTLY 42 `total` fields + the engine hash with every verdict/curve/noise number IDENTICAL; (3) I wrote `kstar >= 1` — an ordering against a non-zero literal — into the very file whose gate forbids them; tightened to `kstar != 0` (identical proposition, §1.1 permits stricter-against-self) with the re-run asserted BYTE-IDENTICAL; (4) my first instinct for the k=0 fix was to special-case it in the RUNNER, which would have made the curve's zero point a DIFFERENT MECHANISM from the rest of it.** Oracle **222/0 with `data/` before AND after**; `cargo test --lib --test-threads=1` **622/0** incl. `variant_table_covers_the_enum`; provenance gate its OWN step (7 passed) AND re-verified from inside the measuring process with abort-on-divergence; engine `9931e144d19b` **`own` — THIS RUNG ADDS RUST.** |
