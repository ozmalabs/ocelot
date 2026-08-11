# `TimeInfer` ON ≥3 FRAMES — RESULTS

Pre-registration `VISION_TIMEPHI_PREREG.md`, committed **`ddcf65958e90`**
before any number. Branch **`worktree-agent-aa916e5bf789dffcd`** — the name I
actually see; no `gamma-substrate/timephi` name exists. Base SHA
**`ee0a1af25ef5dea0e9bc8919f85ebe7e8e19f463`**.

Engine **`a1d350bbd23b`** (`own` build, `scripts/engine_build.sh`), **no Rust
change**. Provenance gate as its **own step before any number**:
`tests/test_engine_provenance_migrated.py` **7 passed** — and
`provenance_line()` is ALSO printed **from inside the measuring process** and
compared against `EXPECT_ENGINE`, **aborting on divergence** (a rung saw the
tree gate pass in the same minute a script resolved the wrong engine).

Oracle `scripts/rung7_vision_bench.sh`: **212 passed, 10 skipped, exit 0** —
this tree has no `data/`, the documented no-corpus case (222 is the collected
count). Re-run **after** all changes: **212 / 10, unchanged.**

Seeds **93000–93999**, `check_claim` recorded in the pre-registration.
**Measured with `scripts/seed_audit.py`: 400 resolved (93000–93399), 
`unknown_sinks: 0`, `parse_errors: 0`, none outside the block.**

---

## THE HEADLINE, IN SIX LINES

**`TimeInfer` at N ≥ 3 IS the arc's first correspondence mechanism with NO
PIXEL APERTURE — and it still does not do phi.** It corresponds at **every
separation tested, to S = 32 px**, which is **8× the largest aperture** at
which the three phi-rung mechanisms stopped exactly. **There is no cutoff.**

**But the aperture was never what phi was about.** The ISI curve is the phi
rung's, reproduced at the aperture-free mechanism: **explained at ISI = 0,
refused at every ISI ≥ 1, in 60 of 60 conditions.**

**The decisive arm is `BlinkBridge` with PREFIX LENGTH as the IV, and it
localises the deficit to one thing.** With **one** pre-gap sample (which is what
a phi stimulus *is*) the substrate FREEZES: confidence **0.00**, and on resume a
correction of **32 cells** — the dot's 16 cells absent from A *and* present at B.
**With two, the same gap is bridged perfectly: correction 0, at S = 4 and at
S = 16 alike.**

**So the registered null-reading is the one that applies: CONTINUATION, NEVER
INTERPOLATION.** The deficit is not aperture, not resolution, not gap-crossing,
and not motion sensing. **It is the absence of an ENDPOINT-ABDUCED generator.**

**All seven registered predictions confirmed; ONE PROVISO BROKE, and it broke
because a Term's own doc comment describes a design the engine no longer
implements.**

---

## 0 — THE WIRING CONTROL, RUN FIRST, AND WHY IT WAS REBUILT

*The phi rung nearly published a perfect fake null: `has_region` edges silently
refused on a bare `Substrate` made priors always empty, so the mechanism
reported the same verdict at every separation. It was caught by a control firing
on the WIRING, not the hypothesis. That control was built first here.*

| control | result | |
|---|---|---|
| **A0-POS** moving dot, N=3, S=4 | `time_inferred`, `kind=translate`, `offset=(0,4)` | wiring **live** |
| **A0-NEG** stationary dot, N=3 | `time_none` | reader **discriminates** |

### THE TRAP GATE I BUILT FIRST WAS ITSELF INERT — §1.1, IN MY OWN INSTRUMENT

I registered a per-call gate: `coord_dims` must be non-empty on every call,
because an unloaded codebook yields empty `coord_dims` and therefore a null at
every condition. **It fired on 167 calls, and every one was a false accusation.**

`eval_time_infer`'s `unexplained()` constructor **hardcodes
`coord_dims: Value::Tuple(empty)`**. So the field is empty on **every**
unexplained verdict *whatever the cause* — it is an **OUTPUT of the verdict**,
not a diagnosis of the codebook. **It cannot distinguish "no codebook" from "no
orbit."** That is §1.1's guarded-division disease exactly: *an absence off a
guarded path is evidence of a LOOKUP, not of a measurement.*

**Verified before the gate was touched (§12.3):** the 167 are exactly the
unexplained calls (A0-NEG 1 + A1 1 + A4 18 + A4n 99 + A5 48 = 167), and the
codebook demonstrably resolves — A0-POS returns `coord_dims=(1,2)` and every
A2/A3 call returns the TRUE offset.

**The rebuilt gate is a paired in-process POSITIVE PROBE:** in the *same booted
substrate* as each measured condition, evaluate the Term on a **known orbit** and
require *its* `coord_dims` non-empty. If the codebook were absent the probe would
be empty too. **Result: 0 violations across all 340 measured calls**,
`probe_coord_dims = (1, 2)` throughout.

The old reading is still recorded, and in the final run it flags **267** calls
(1 + 1 + 18 + 199 + 48 — again exactly the unexplained set, the noise arm having
grown to 200 draws) — **kept as a finding about the instrument, not as a gate.**

---

## 1 — A1: CAN THE TERM CONSUME RAW PIXELS AT ALL?

*The project's recorded lesson from the identity seam is "it was never broken —
nobody had handed it pixels." The brief asked whether it applies here. It does
not, and the reason is worth stating.*

**R-FIELD** — every pixel of a bounded 24×24 field, **576 cells per frame, no
segmentation whatsoever**, dot translating by S=4:

| | result |
|---|---|
| verdict | **`time_none`** |
| `checked` | **83 520** (it tried the full linear enumeration and failed) |

**P0 confirmed.** A translate applied to a **bounded** field moves edge cells off
the lattice, and `frames_equal` is exact. `infer_translate_offset` pairs the
sorted frames, reads offset `(0,0)` from the first background cell, and fails on
the dot cells.

**So: you CANNOT hand `TimeInfer` a bounded pixel field.** It is a **SHAPE-level
operator**. The identity-seam lesson does **not** transfer — that seam ingested
pixel-derived tuples directly; this Term requires a **figure**.

**Consequence, stated as a limitation and not buried: every positive result
below is CONDITIONAL on a figure/ground split the ADAPTER supplied** (cells whose
luminance differs from the frame's own modal value — an exact, data-derived
comparison, but a segmentation the graph did not make). **That is supplied
structure, and it is declared.** §0's paradigm-forcing rule is respected only in
the weaker sense that no *decision* is made in Python; the *representation* was
chosen by me.

---

## 2 — A2: THE VACUITY CLAIM, MEASURED RATHER THAN ASSUMED

*The phi rung ruled `TimeInfer` out on two frames because "translation is
group-closed." §3 requires that be tested. A rung this week found its own seed
comment about the engine was FALSE on the current engine.*

**N = 2, figure representation:**

| S | 1 | 2 | 4 | 6 | 8 | 12 | 16 | 20 | 32 |
|---|---|---|---|---|---|---|---|---|---|
| verdict | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `offset` | (0,1) | (0,2) | (0,4) | (0,6) | (0,8) | (0,12) | (0,16) | (0,20) | (0,32) |

**P1 confirmed, 9/9. Two frames explain EVERYTHING — the inherited vacuity
argument is correct, and is now measured rather than asserted.** `checked = 0`
throughout: the translate is read off by subtraction and no search is run.

---

## 3 — A3: H1 — THE FIRST CORRESPONDENCE WITH NO PIXEL APERTURE

**N ∈ {3, 5}, constant velocity:**

| S | 1 | 2 | 4 | 6 | 8 | 12 | 16 | 20 | 32 |
|---|---|---|---|---|---|---|---|---|---|
| **N = 3** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **N = 5** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

**Every one returns the TRUE offset `(0, S)`. P2 confirmed, 18/18.**

**Max S with correspondence: 32 at both N — the top of the grid. There is no
cutoff.** Set against the phi rung's table:

| mechanism | max S with correspondence | is it a pixel length? |
|---|---|---|
| L1 SAD block match | **4** | `radius = BLOCK = 4`, exactly |
| L2 `segment_and_track` | **6** | `span + 2 = 6`, exactly |
| L3 `track_identity` | whatever you ask | `radius`, verbatim |
| **`TimeInfer`, N ≥ 3** | **≥ 32 (no cutoff found)** | **NO** |

**This is the arc's first non-tautological correspondence range.** The three
prior mechanisms each returned their own aperture; this one returns the
displacement **the data actually contains**, because `infer_translate_offset`
reads the offset by **subtraction** and nothing bounds its magnitude. **The
`max_b = 8` cap in the seed bounds only the LINEAR fallback's enumeration and is
never reached on the translate path** (`checked = 0` in every A2/A3 condition —
measured, not argued).

---

## 4 — A4: WHAT MAKES A3 NON-VACUOUS

*A mechanism that says "explained" to everything has no aperture the way a
stopped clock has no error.*

| S | 1 | 2 | 4 | 6 | 8 | 12 | 16 | 20 | 32 |
|---|---|---|---|---|---|---|---|---|---|
| **ACCEL** (0, S, 3S) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| **SHUFFLE** (S, 0, 2S) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

**P3 confirmed, 18/18 refused.** So the third frame is doing real work: N = 2
accepts everything, N = 3 accepts **only** a genuine constant-velocity orbit —
**at any separation.** *The third frame does not extend the aperture; it adds
the CONSTRAINT that makes an unbounded aperture safe.*

### THE NOISE CONTROL PARTIALLY FAILED, AND THE FAILURE WAS MINE

**As registered** (seeds 93000–93099, three uniform random dot columns): **1 of
100 accepted.** That looks like a spurious mint. **It is not.**

Seed **93053** drew columns **[141, 144, 147]** — **equal spacing 3, a genuine
constant-velocity orbit.** Three uniform draws are equally spaced with
probability ≈ 1/(FIELD_W − DOT) = 1/156, so the **analytic expectation is 0.64
per 100.** Measured 1. **The mechanism did not hallucinate a generator; it
correctly recognised one my "noise" arm handed it.**

**My noise control was not a non-orbit condition** — §6, controls must
correspond to the actual experiment. Verified **before** the arm was touched
(§12.3), then re-run on draws that are genuinely not orbits:

| arm | n | accepted |
|---|---|---|
| **as registered** (93000–93099) | 100 | **1** — and it is a REAL orbit, confirmed by hand |
| **corrected** (93100–93199, non-orbit draws only) | 100 | **0** |

**Both numbers are reported.** The corrected arm is the floor the registration
meant to measure; the as-registered number is left standing because deleting it
would hide the design error.

---

## 5 — A5: THE ISI CURVE — CONFIRMED, AND ITS WEIGHT WAS DECLARED ZERO IN ADVANCE

`N_flash ∈ {2,3,5}`, `S ∈ {4,16}`, `k ∈ {0..4}` blank frames, two blank
encodings — **60 conditions.**

| encoding | k=0 | k=1 | k=2 | k=3 | k=4 |
|---|---|---|---|---|---|
| **BLANK-EMPTY** | ✓ | ✗ | ✗ | ✗ | ✗ |
| **BLANK-BG** | ✓ | ✗ | ✗ | ✗ | ✗ |

**P4 confirmed, 60/60. Maximal at ISI = 0, identically dead at every ISI ≥ 1 —
the phi rung's INVERTED curve, reproduced at the mechanism with no aperture.**
Human phi *requires* the gap and is worst at simultaneity.

**THE §13.1 DECLARATION MADE IN THE PRE-REGISTRATION STANDS, AND IT DISQUALIFIES
THIS ARM AS EVIDENCE.** I read both guards at source before running:
BLANK-EMPTY is refused by `frames.iter().any(|f| f.is_empty())` and BLANK-BG by
`infer_translate_offset`'s `f0.len() != f1.len()`. **Both nulls are FORCED BY
ARCHITECTURE — §13.1's third category, a mechanism whose construction forces the
signature you are measuring.** *This arm could not have produced a positive, so
reproducing the human-inverted curve here is a tautology with error bars, and it
is reported as one.*

**What it DID buy, and the reason it was run:** the `checked` column
distinguishes **REFUSAL** from **FAILURE**, and the two encodings separate
cleanly:

| encoding at k ≥ 1 | `checked` | what happened |
|---|---|---|
| **BLANK-EMPTY** | **0** | **REFUSED at the guard** — it never looked |
| **BLANK-BG** | **83 520** | **FAILED after the full linear enumeration** |

**So the source reading is confirmed on the real engine** (the thing a seed
comment failed at elsewhere this week), and the two nulls are shown to arise by
two *different* routes — which is what makes §7's reading decidable rather than
a shrug.

---

## 6 — A6: THE ARM THAT IS NOT FORCED, AND THE RESULT OF THE RUNG

`BlinkBridge`, `[P visible | k EMPTY | 1 resumed]`. **Prefix length is the IV.
`P = 1` IS the phi topology.** 32 conditions.

| S | P | k=1 | k=2 | k=3 | k=4 |
|---|---|---|---|---|---|
| **4** | **1** | **freeze, conf 0.00, div 2, corr 32** | freeze, 0.00, 3, **32** | freeze, 0.00, 4, **32** | freeze, 0.00, 5, **32** |
| 4 | 2 | translate, 0.50, −1, **0** | 0.33, −1, 0 | 0.25, −1, 0 | 0.20, −1, 0 |
| 4 | 3 | translate, 0.67, −1, 0 | 0.50, −1, 0 | 0.40, −1, 0 | 0.33, −1, 0 |
| 4 | 4 | translate, 0.75, −1, 0 | 0.60, −1, 0 | 0.50, −1, 0 | 0.43, −1, 0 |
| **16** | **1** | **freeze, conf 0.00, div 2, corr 32** | freeze, 0.00, 3, **32** | freeze, 0.00, 4, **32** | freeze, 0.00, 5, **32** |
| 16 | 2 | translate, 0.50, −1, **0** | 0.33, −1, 0 | 0.25, −1, 0 | 0.20, −1, 0 |
| 16 | 3 | translate, 0.67, −1, 0 | 0.50, −1, 0 | 0.40, −1, 0 | 0.33, −1, 0 |
| 16 | 4 | translate, 0.75, −1, 0 | 0.60, −1, 0 | 0.50, −1, 0 | 0.43, −1, 0 |

**P5 confirmed exactly (16/16).** At `P = 1` the belief across the gap is the
**last frame repeated** — persistence, not motion — and on resume the observation
diverges with `correction = 32`. **The dot is 4×4 = 16 cells; 32 is those cells
counted twice: absent where the belief put them, present where they actually
are.** *That is "one vanished, another appeared" — computed by the substrate, and
given a magnitude.* **It is identical at S = 4 and S = 16**, so it is not a
distance effect.

**P6 confirmed (16/16 bridge, with the TRUE offset `(0, S)`).** With **two**
visible pre-gap frames the *same* gap, at the *same* displacement, is bridged
**perfectly**: `diverged_at = −1`, `correction = 0`.

### THE PROVISO THAT BROKE — AND IT BROKE ON A STALE DOC COMMENT

**P6's registered proviso predicted a HORIZON**: bridging iff
`gap <= confirm_run`, so `P = 2` (confirm_run = 1) should **diverge** at k = 4.
**It does not. It bridges at every k. `A6b_boundary = False`.**

I took `gap <= confirm_run` from **`term.rs`'s own `BlinkBridge` doc**:

> *"the bridge/hold DECISION lives in the seed rule reading these fields
> (`gap <= confirm_run` = RELATIVE decay, no constant; `explained=false` = no
> consistent motion ⇒ held open)"*

**That describes a superseded design.** `shape_decode.rs::eval_blink_bridge`
carries the correction in the same file — *"CONFABULATE BY DEFAULT (the
creator's correction) … There is NO 'hold open'"* — and `blink_bridge.json`
implements confabulate-always. **The two doc blocks contradict each other, and
the behaviour follows the second.**

**What is actually there is better than what I predicted**: the bridge has **no
horizon**, it has a **CONFIDENCE that decays** — 0.75 → 0.60 → 0.50 → 0.43 at
P=4, monotonically in the gap, `support/(support+gap)`. **That is a §13 number
that falls OUT of support, with no constant anywhere.** The bridge never stops
guessing; it stops being *confident*.

**Recorded, not edited (`term.rs` is not this rung's file): the `BlinkBridge`
doc comment is stale relative to the shipped behaviour on engine
`a1d350bbd23b`.** This is the third instance in a week of a comment describing an
engine that no longer exists. **Registering the proviso in advance is the only
reason it was findable.**

---

## 7 — WHICH REGISTERED READING APPLIES

§5 of the pre-registration fixed the decision table before the run.

| A6a (P=1) | A6b (P≥2) | reading |
|---|---|---|
| **does not bridge** ✅ | **bridges** ✅ | **CONTINUATION-ONLY — the registered null-reading** |

> **THE SUBSTRATE'S TEMPORAL CORRESPONDENCE IS CONTINUATION, NEVER
> INTERPOLATION.** Every temporal mechanism in this tree — `TimeInfer`,
> `BlinkBridge`, `DepthInfer` — infers its generator `G` from a **consecutive
> VISIBLE pair** and then **extrapolates**. **A phi stimulus supplies exactly ONE
> pre-gap sample**, so there is no pair from which to infer `G`. The generator
> that would explain phi must be **ABDUCED FROM THE GAP'S TWO ENDPOINTS** —
> solve `G^(k+1)(f_before) = f_after` for `G` — which is **INTERPOLATION**.
> **The substrate has no operator of that shape.**

**This is a strictly sharper statement than either alternative on the table**,
and it is the one the measurements force:

- **NOT "the substrate cannot do phi"** — too coarse. It does everything phi
  needs *except* one inference, and it does the hard-looking parts (unbounded
  correspondence range, gap-crossing, orbit verification) already.
- **NOT "there is no gap-crossing mechanism at all"** — **refuted by A6b.** The
  same gap, the same displacement, bridged perfectly with `correction = 0`, at
  8× the largest pixel aperture. **What the substrate lacks is not the bridge.
  It is the ability to build a bridge from the two banks alone.**

**The three phi-rung mechanisms stop at a pixel length. This one does not stop
at a length at all — it stops at a COUNT: it needs two samples before the gap,
and phi gives it one.**

### PREDICTIONS: 7 CONFIRMED, 1 PROVISO BROKEN

| | prediction | outcome |
|---|---|---|
| **P0** | R-FIELD unexplained at every S | ✅ `time_none`, `checked` 83 520 |
| **P1** | N=2 explained at all 9 S — vacuous | ✅ **9/9**, true offset each |
| **P2** | N≥3 explained at all 9 S — **no cutoff** | ✅ **18/18**, true offset each, max S = 32 = grid top |
| **P3** | ACCEL and SHUFFLE refused | ✅ **18/18** |
| **P4** | ISI: true at k=0, false at every k≥1 | ✅ **60/60** — *and declared weightless in advance (forced)* |
| **P5** | A6a (P=1): freeze, conf 0.0, correction 32 | ✅ **16/16**, exactly 32, S-invariant |
| **P6** | A6b (P≥2): bridges with the true offset | ✅ **16/16** |
| **P6's proviso** | bridges **iff** `gap <= confirm_run` | ❌ **BROKEN** — bridges at every k; the horizon does not exist (§6) |

**The §8 proviso I flagged in advance as most likely to break — the non-coord
byte-identity clause on the pixel-derived `lum` slot — held**, as predicted, on
hard-edged rendering. **The one I did not flag is the one that broke.**

---

## 8 — §13: NO MAGIC NUMBER ENTERED, AND THE GATE WAS PROVEN TO BITE

`tests/test_timephi_ast_migrated.py` — **9 passed.** A Python **AST walk**,
never a substring selector.

Every verdict is an **exact equality** on a logical or integer quantity:
`status == 'time_inferred'`, `offset == (0, S)`, `correction == 0`,
`diverged_at == -1`, `kind == 'freeze'`, `confidence == 0.0`. Asserted
structurally:

- the verdict functions are bound **as `ast.FunctionDef` nodes by name**, read
  from the runner's **own** `VERDICTS` tuple — the gate carries no copy, and a
  divergence between the two is itself a failure (**non-vacuity**);
- **subscript indices are PRUNED** by an explicit recursive descent — an index
  is addressing, not a threshold. *The phi rung's first gate counted three array
  indices as thresholds, and its first fix was also wrong because **`ast.walk`
  cannot prune**. This gate does not use `ast.walk` for that reason;*
- no non-zero constant is compared against a measured quantity, **admitted only
  against a cardinality (`len(...)`)**;
- verdicts decide by **equality**, never ordering (partial credit is forbidden);
  the only admitted orderings are a sign test against the sentinel `0`
  (`diverged_at >= 0`) and `gap <= confirm`, which compares **two measured
  quantities to each other** — no constant enters;
- the declared residuals are **bound exactly once** and never appear inside a
  verdict comparison — except `2 * DOT * DOT`, which is the dot's **own cell
  count**, a cardinality derived from the stimulus, on the constant side of an
  equality;
- the swept axes (`S_GRID`, `K_GRID`, `P_GRID`, `ISI_S`) are **iterated, never
  compared against**;
- the dead-instrument arms **abort** (`return 2` on engine divergence,
  `return 3` on a failed wiring control), not warn.

**POSITIVE-CONTROLLED (§12.3), and the control was inspected rather than
trusted.** Injecting `abs(offset[1] - S) < 2.5` into the aperture verdict turns
the walk RED on **both** counts (`const:v_a3_p2`, `ordering:v_a3_p2`); injecting
`correction > 12` into the phi verdict fires too; the unmodified source is
asserted **green** in the same test. **The poisoned source was printed and read
by hand to confirm the injection lands inside the intended function** rather than
the gate passing on a mangled string.

**Declared residuals, labelled as CONFIGURATION and nothing stronger:** `DOT=4`
(inherited from the phi rung, `DOT = BLOCK`), `FIELD_H/W`, `RAW_N`, `BG`, `FG`,
`ROW` — stimulus construction. **`max_b = 8`** is a compute cap on an
enumerative fallback the translate path never reads (`checked = 0` on every
translate verdict — **measured**). **The claim made about all of these is the
weak one — bound once, never a verdict threshold — not that they fell out.**

---

## 9 — SEED ACCOUNTING: MEASURED, NOT ASSERTED

```
scripts/timephi_measure.py   resolved: 400 seeds, 93000-93399
                             unknown_sinks: 0     parse_errors: 0
                             outside 93000-93999: []
```

**400 resolved, ZERO unknown sinks, none outside the block.** *A `--check` that
passes while leaving sinks UNKNOWN has verified nothing.* The first revision
reported **`unknown_sinks: 1`** — the RNG was constructed inside a helper taking
a parameter, which no static walk can resolve. Rather than explain it away, the
draws were **materialised once from a single sink bound to an explicit
`range`**, so the audit reports the truth instead of a defensible silence.

---

## 10 — WHAT IS NOT SHOWN (§8)

- **Nothing about human phi's mechanism.** Human phi enters only as the
  parameter dependence compared against. No human data was measured.
- **Every positive result is CONDITIONAL ON A SUPPLIED FIGURE/GROUND SPLIT.**
  A1 shows `TimeInfer` cannot consume a bounded pixel field at all. The
  segmentation is the adapter's, not the graph's (§1).
- **A5's null is ARCHITECTURAL, not empirical** — declared in advance, and it
  carries no evidential weight.
- **The ~11% per-block motion-sensor error does NOT bound these numbers**, and
  that is a deliberate scope statement rather than a claim of superiority: **this
  rung does not consume the block-match sensor at all.** It bounds any comparison
  drawn to the phi rung's tables, and those comparisons are marked where they
  occur (§3's table). A concurrent rung is gating the sensor; nothing here
  assumes its outcome.
- **One dot, one shape, one size, horizontal only, uniform background.** The phi
  rung's scope limits are inherited unchanged. **A textured background was NOT
  run** — the figure representation would ingest the texture as figure cells, and
  what that does is unmeasured.
- **`DepthInfer` was NOT run.** It is named in §7's claim on the strength of a
  SOURCE READING (it applies the same rigidity test per surface), **not a
  measurement.** That clause is the weakest in this document.
- **No timing claim of any kind.** Every quantity is exact or counted.
- **`data/` and BSDS300 absent**, so the oracle is the 212/10 case.
- **N ≥ 5 was tested; N ≥ 6 was not**, and no claim is made about longer windows.

---

## 11 — WHAT I GOT WRONG

1. **My trap gate was inert by construction** — the exact defect it existed to
   catch, one level up. `coord_dims` off an unexplained call is an **output of
   the verdict**, hardcoded empty by `unexplained()`, so it cannot diagnose the
   codebook. It made **167 false accusations**. Rebuilt as a paired in-process
   positive probe (§0). *§1.1 is easier to quote than to obey.*
2. **My noise control was not a noise control.** Three uniform draws are equally
   spaced ~1/156 of the time, so the arm handed the mechanism a **real orbit**
   and I initially read its correct acceptance as a spurious mint. Both arms are
   reported (§4).
3. **P6's proviso broke, and I had read it off a stale doc comment.**
   `term.rs` says the bridge has a `gap <= confirm_run` horizon; the engine
   implements confabulate-always with a decaying confidence. **I predicted a
   cutoff that the code deleted.** The correction is more interesting than the
   prediction (§6).
4. **My first seed-audit run left an unknown sink** and would have let me publish
   an accounting that had verified nothing (§9).
5. **I under-anticipated how much the representation choice would carry.** The
   pre-registration treated R-FIELD vs R-FIG as one arm among several; A1 shows
   it is a **precondition for the entire rung**, and every positive number here
   sits on top of a segmentation I supplied.

---

## 12 — NAMED NEXT LEVERS, EACH NEEDING ITS OWN PRE-REGISTRATION

1. **AN ENDPOINT-ABDUCED GENERATOR — the lever this rung earns.** Solve
   `G^(k+1)(f_before) = f_after` for `G` given the gap length. It is a
   **well-posed integer problem** (for a translate: the offset is the endpoint
   difference divided by `k+1`, admissible iff it divides exactly — a divisibility
   test, **no threshold**), it is exactly what phi is, and it is the ONE operator
   the substrate lacks. **The `k+1` divisor also predicts an INTERIOR ISI
   OPTIMUM** — the human curve's shape — because a longer gap admits more
   candidate generators and the MDL floor should refuse the over-explained ones.
   *That is a genuinely risky prediction, and it is the reason to build it.*
2. **A textured background at N ≥ 3.** The figure split is the load-bearing
   assumption of this whole rung and is untested against texture.
3. **`DepthInfer` measured rather than read.** §7's claim rests on a source
   reading for that mechanism; it should be measured or the clause narrowed.
4. **The stale `BlinkBridge` doc comment in `term.rs`** — reported, not edited
   (not this rung's file). Third comment-vs-engine divergence in a week; the
   pattern is worth a gate of its own.

---

## 13 — LEDGER ROW (for the supervisor to merge into `VISION_PROTOCOL.md`)

*Written here, not there — `VISION_PROTOCOL.md` is not this rung's file.*

| range | used for |
|---|---|
| **93000–93999 (400 seeds resolved, unknown_sinks 0, none outside block)** | **`TimeInfer` AT N≥3 IS THE ARC'S FIRST CORRESPONDENCE MECHANISM WITH NO PIXEL APERTURE — AND IT STILL DOES NOT DO PHI, BECAUSE THE APERTURE WAS NEVER THE PROBLEM.** Correspondence at **every S to 32 px, 8× the largest phi-rung aperture, with the TRUE offset, 18/18 — NO CUTOFF** (L1 stopped at 4 = radius = BLOCK, L2 at 6 = span+2, L3 at `radius` verbatim). **NON-VACUOUS: N=2 explains EVERYTHING (9/9 — the inherited group-closure argument MEASURED, not assumed), N=3 refuses ACCEL and SHUFFLE 18/18 — the third frame does not extend the aperture, it adds the CONSTRAINT that makes an unbounded one safe.** ISI 60/60 inverted (max at 0, dead at every k≥1) **BUT ITS EVIDENTIAL WEIGHT WAS DECLARED ZERO IN ADVANCE — both nulls are FORCED (an `is_empty` guard; a cardinality check), §13.1's third category, reported as a tautology with error bars; what it bought is `checked` separating REFUSAL (0) from FAILURE (83 520), confirming the source reading on the real engine.** **THE DECISIVE ARM IS `BlinkBridge` WITH PREFIX LENGTH AS THE IV, AND IT IS NOT FORCED: P=1 (THE PHI TOPOLOGY) FREEZES — confidence 0.00, resume `correction = 32` = the dot's 16 cells counted twice, IDENTICAL at S=4 and S=16; P≥2 BRIDGES THE SAME GAP PERFECTLY (correction 0, true offset, 16/16).** **⇒ THE REGISTERED NULL-READING APPLIES: CONTINUATION, NEVER INTERPOLATION. Every temporal mechanism infers `G` from a consecutive VISIBLE pair and EXTRAPOLATES; phi supplies ONE pre-gap sample. The deficit is not aperture, not resolution, not gap-crossing (REFUTED BY A6b), not motion sensing (C-RIGID) — it is THE ABSENCE OF AN ENDPOINT-ABDUCED GENERATOR. This mechanism stops at a COUNT, not a length.** **A1: `TimeInfer` CANNOT CONSUME A BOUNDED PIXEL FIELD AT ALL (576 cells, `time_none`, checked 83 520) — it is a SHAPE-level operator, so the identity seam's "nobody had handed it pixels" does NOT transfer, and EVERY POSITIVE HERE IS CONDITIONAL ON A FIGURE/GROUND SPLIT THE ADAPTER SUPPLIED.** **WHAT IT GOT WRONG: (1) THE TRAP GATE WAS ITSELF INERT — `coord_dims` off an unexplained call is an OUTPUT hardcoded empty by `unexplained()`, so it cannot tell "no codebook" from "no orbit"; it made 167 FALSE ACCUSATIONS and was rebuilt as a paired in-process positive probe (§1.1 in my own instrument); (2) THE NOISE CONTROL WAS NOT A NOISE CONTROL — 3 uniform draws are equally spaced ~1/156, so seed 93053 drew a REAL orbit [141,144,147] and its correct acceptance read as a spurious mint; BOTH arms reported (1/100 as-registered, 0/100 corrected); (3) **P6's PROVISO BROKE ON A STALE DOC COMMENT** — `term.rs` promises a `gap <= confirm_run` HORIZON, the engine implements CONFABULATE-ALWAYS with a confidence that DECAYS 0.75→0.43 (`support/(support+gap)`, a §13 number that falls OUT); the bridge never stops guessing, it stops being confident — THIRD comment-vs-engine divergence in a week, RECORDED not edited; (4) the first seed audit left `unknown_sinks: 1` and would have verified nothing.** §13: every verdict an EXACT EQUALITY; AST gate 9/9 located BY SHAPE from the runner's OWN `VERDICTS` tuple, **subscript indices PRUNED by explicit descent because `ast.walk` CANNOT prune**, POSITIVE-CONTROLLED with two injected thresholds and the poisoned source read by hand. No Rust, no seed, no default moved; provenance gate its OWN step (7 passed) AND re-verified from inside the measuring process; oracle 212/10 before and after. |
