# `ArgminUnique` — RESULTS

Pre-registration `VISION_ARGMIN_UNIQUE_PREREG.md`, committed **`64e3ec0dc650`**
before any number.

- **branch (as observed):** `worktree-agent-a846557d10087d8f6` — the name I
  actually see.
- **base SHA (as observed):** `8f41cc2ab277e6be4265ccf7d0dc632e2575f4cd`
- **engines.** THIS RUNG ADDS RUST, so it built its own, twice:
  - `d657468d9e1f` — this tree's build of the **UNCHANGED** source, for the
    pre-change oracle.
  - **`cb88b677bc42`** — this tree's build of the changed source (`own`);
    every number below is from it.
- **provenance, its OWN step before any number:**
  `tests/test_engine_provenance_migrated.py` **7 passed** before, and
  **7 passed again AFTER** all long measurements, with
  `provenance_line()` re-read: `engine cb88b677bc42 @ …/runners/dsl/python/
  substrate_rs/_native.abi3.so`. Each measuring script also compares
  `provenance_line()` against `EXPECT_ENGINE` **inside the measuring process**
  and aborts on divergence.
- **oracle:** `bash scripts/rung7_vision_bench.sh` → **222 passed, 0 failed**,
  exit 0, `data/` symlinked (§10.2, the with-corpus case) — on the pre-change
  engine, on the post-change engine, and in **every** instrument mode.
- **seeds:** **110000–110199** (control replicate) and **110200–110207**
  (load-bearing probe), all **LITERAL elements of the declared block** — no
  `base + K` offset expression anywhere (the refusal rung's §11.6 lesson,
  applied). `check_claim` verbatim in the pre-registration, **506 unresolved
  sinks tree-wide** priced. **My own files carry 2 unknown sinks**
  (`scripts/seed_audit.py`): the `default_rng(sd)` / `default_rng(seed)`
  loop-variable forms, which the static tool cannot resolve. Disclosed, not
  buried — the values ARE in-block, but the ledger cannot see that.
  `scripts/argmin_unique_landed.py` also uses **seed 3**, which is not a draw:
  it is the committed test's own seed, re-used to REPRODUCE a landed readout.
- **loadavg** is recorded in every artifact JSON. Never more than **2**
  concurrent workers; peak observed load **6.68** on 12 cores. **No wall-clock
  cutoff was used as a verdict.**
- **no seed manifest shipped, no default moved, no other rung's file edited.**

---

## THE HEADLINE

**The named fix is BUILT, and the measurement says it is pointed at the wrong
selector.**

**All 201 ties on the entire 222-test vision bench are `Argmax`. `Argmin` tied
ZERO times in 443,322 selector firings.** `refuse_min` — every `Argmin`
behaving as `ArgminUnique`, tree-wide — produced **0 refusals**. The
refusal-capacity rung measured `Argmin`'s inability to refuse on a synthetic
five-identical-candidate set; on the bench the confabulation-by-tie-break is
happening at **`Argmax`, in two winner-take-all rules**, and `ArgminUnique` by
name does not cover it.

**ZERO LANDED NUMBERS MOVED** — and that is a measured result, not a dead arm.
222/222 gates unchanged under `refuse_all`; four committed readouts
(`dsi_ideal` 0.5999996800000661, `dsi_untrained_floor` 0.1407423591394234,
`onoff_no_threshold_osi` 0.0003940381693654998, `compose_ideal_osi` 0.128962908…)
**bit-identical to 16 digits** with **188 refusals actually exercised**.

**But the tie-break IS load-bearing.** Per-step, on the configuration that
guarantees ties (four IDENTICAL dorsal units), `D = max|off − refuse_all| =
1003.0` on `last_burst`, with **145 attribute-cells differing** across 38 steps
and 12 refusals. **So an arbitrary winner has been propagating into the sheet's
per-step state all along, and washing out of every published readout.** The
exposure is real; the committed numbers are safe.

**And the escalation is ADMISSIBLE NOWHERE.** At the 16 `Eq(node, Argmin{…})`
sites — the WTA idiom, and the only shape that ties on this bench — a refusal
evaluates to **`False`**, which is byte-identical to *"you are not the winner"*
**and** to *"the source was empty"*. At the 85 `Attr(Argmin{…}, key)` sites it
is a bare **`None`**, byte-identical to the empty-source null. **C1's field-
boundary erasure reproduces exactly, one level down: `ArgminUnique` can refuse,
and no caller in the seed layer can hear it.**

---

## 0 — THE POSITIVE CONTROL, IN BOTH DIRECTIONS, RUN BEFORE ANY Δ

*The trap this rung was briefed on: a rung last wave built a refusal instrument
whose reader died first, and **a dead reader and a perfect refuser produce
byte-identical output.***

`Argmin` **already** returns `Value::None` on an empty source. A tie-refusal
returns `Value::None`. Downstream, they are the same bytes. So the instrument
counts `TIES`, `EMPTIES` and `REFUSALS` **separately in the Rust fold**, and the
control asserts both directions in one process on one reader
(`scripts/argmin_unique_control.py` → `results/argmin_unique_control.json`):

| check | result |
|---|---|
| baseline: `Argmin` on 5 identical returns a winner (the fact this rung exists for) | **pass** |
| **P-A** tie ⇒ null, `ties`+1, `empties`+0, `refusals`+1 | **pass** |
| **P-B** unique min ⇒ **the same node `Argmin` returns**, `ties`+0 | **pass** |
| **P-C** empty ⇒ null, `empties`+1, **`ties`+0** | **pass** |
| **P-D** the reader reports a NON-null in the same process | **pass** |
| **P-A vs P-C: same output bytes, DIFFERENT counters** | **pass** |
| `refuse_min` refuses a tied `Argmin` / passes a unique one | **pass / pass** |
| `refuse_min` does **NOT** touch `Argmax`; `refuse_all` does | **pass / pass** |
| `count` mode does not change behaviour | **pass** |
| randomised replicate, seeds 110000–110199 | **100/100 ties refused, 100/100 uniques passed** |

**18/18 checks and 200/200 draws.** A reader that returned `None` universally
fails P-B and P-D; a mechanism that refuses everything fails P-B; one that
refuses nothing fails P-A. The runner **aborts and reports no Δ** if any fails.

---

## 1 — WHAT WAS BUILT

**`TermNode::ArgminUnique`** — one Term variant, **APPENDED**. `GapAbduce`
stays **175**, `GapVerify` stays **176**, `ArgminUnique` is **177**,
`NUM_TERM_VARIANTS` **177 → 178** (regenerated by
`tools/gen_term_variants.py`, so `variant_table_covers_the_enum` holds by
construction). Identical fold to `Argmin`; returns `default` (or
`Value::None`) when the extremum is not unique.

**§13 satisfied BY CONSTRUCTION.** Uniqueness is `cmp_value == Equal` — exact
equality. **There is no constant in the variant and nowhere to put one.** No
site in the measurement wanted a tolerance: every tie observed was an exact
float equality arising from *structurally identical* units, not from two nearly
equal values. **Had one wanted an epsilon I would report that and pick no
number; none did.**

**§9 by non-existence.** No seed binds the Term (`unique_term_firings = 0` on
every bench run). The instrument that coerces existing selectors ships **OFF**;
`count` mode is measured to be behaviourally identical to `off`.

**`Argmax` is NOT fixed.** `EnclosedCount`'s zero/unmeasurable conflation and
the motion sensor's SAD argmin are likewise **named and left** — separate rungs.

---

## 2 — ARM T: THE TIE CENSUS (`count` mode, behaviour unchanged)

`scripts/rung7_vision_bench.sh` under `count`, engine `cb88b677bc42`:

| | value |
|---|---|
| selector firings | **443 322** |
| **ties (non-unique extremum)** | **201** |
| empties (the null `Argmin` could already produce) | 9 |
| refusals | 0 (count mode does not refuse) |
| **tie rate** | **0.0453 %** |
| bench outcome | **222 passed / 0 failed — identical to `off`, test for test** |

**P1 IS FALSIFIED.** I predicted **> 5 %**; measured **0.045 %**, two orders of
magnitude low. My reasoning — *"many vision scores are small integers or counts,
so ties should be common"* — was wrong about this bench: the selectors run over
**floats produced by accumulation**, which almost never collide exactly.

**Ties are not spread. They are in exactly TWO SITES and THREE TESTS**, read off
the firing itself (`argmin_tie_sites` renders the selector's own `value` Term),
never grepped:

| selector | site (value Term) | ties | seed rule |
|---|---|---|---|
| **`Argmax`** | `Attr(u2, "dact")` | **151** | `dv_burst_winner` (`vision_dorsal.json`) |
| **`Argmax`** | `Attr(u2, "rate")` | **50** | `oo_sunit_burst_winner` (`vision_onoff.json`) |
| `Argmin` | — | **0** | — |

| test | ties |
|---|---|
| `test_vision_dorsal_migrated.py::test_the_dsi_scores_an_ideal_direction_selective_unit_high` | 151 |
| `test_vision_compose_migrated.py::test_NOT_CLAIMED_the_probe_is_blind_on_the_composed_pathway` | 44 |
| `test_vision_onoff_migrated.py::test_WITHOUT_the_threshold_even_a_perfect_cell_reads_as_unoriented` | 6 |

**Both tying sites are WINNER-TAKE-ALL competition rules, and the ties are
STRUCTURAL, not numerical coincidence:** all three tests install **identical
ideal units** and then ask which one wins. *A calibration gate that hands the
population the same perfect cell N times over produces an N-way tie by
construction* — and the WTA elects one of them by iteration order.

---

## 3 — ARM M: HOW MANY LANDED NUMBERS MOVE

### 3.1 The gate level — 222 tests, three modes

| mode | firings | ties | refusals | bench | tests whose outcome changed |
|---|---|---|---|---|---|
| `off` | — | — | — | **222 / 0** | — (baseline) |
| `count` | 443 322 | 201 | 0 | **222 / 0** | **0** |
| **`refuse_min`** | 443 322 | 201 | **0** | **222 / 0** | **0** |
| **`refuse_all`** | 443 241 | 120 | **120** | **222 / 0** | **0** |

**`refuse_min` refused NOTHING while 201 ties were in flight.** That single row
is the rung's main structural finding: **every tie is on `Argmax`.**

*(`refuse_all` shows 120 ties where `count` shows 201, and 81 fewer firings:
refusing changes the trajectory, so later tie opportunities differ. The counters
separate `ties` from `refusals` precisely so this is a measured fact and not an
assumed identity.)*

### 3.2 The VALUE level — because a test can pass while a number moves

`scripts/argmin_unique_landed.py` reproduces the three tying tests' committed
readouts under `off` / `count` / `refuse_all`. **The arms differ only in what
the engine's selector does with a tie — there is no Python branch on the mode.**

| landed number | `off` | `refuse_all` | Δ | refusals exercised |
|---|---|---|---|---|
| dorsal `dsi_ideal` (committed "0.600") | 0.5999996800000661 | 0.5999996800000661 | **0.0** | 92 |
| dorsal `dsi_untrained_floor` | 0.1407423591394234 | 0.1407423591394234 | **0.0** | 92 |
| on/off no-threshold OSI (committed "~0.0006") | 0.0003940381693654998 | 0.0003940381693654998 | **0.0** | 4 |
| composed-pathway ideal OSI (committed "~0.13") | 0.12896290890820553 | 0.12896290890820553 | **0.0** | **0 — DEAD ARM** |

**0 of 4 moved.** `count` mode is bit-identical to `off` on all four (the
instrument's own passivity control).

**SCOPE, STATED NOT IMPLIED:** the compose row exercised **zero refusals** in my
reproduction — I reproduced only the `lateral` arm, and that test's 44 ties are
in the part I did not reproduce. **That row supports nothing**, in either
direction, and is reported as dead rather than counted as a null.

### 3.3 So is the tie-break INERT? **No — and reading it that way was my error.**

§1 clause 5 / FM-0: toggle it, and measure `max|on − off|` on what you claim it
affects.

**My first vacuity probe reported `tie_break_is_load_bearing: false` — and it
was a DEAD ARM.** It ran 8 free-running wave seeds (110200–110207, n_units 10)
that **never tied once**, so `D = 0.0` meant *the mechanism never fired*, not
*the mechanism does nothing*. **A gate that has never been ABLE to fire has not
been tested.** It was caught by requiring `refusals > 0` next to every `D`, and
the probe now names the configuration the census proved ties instead of one I
guessed.

**Re-run on the live configuration** (four identical dorsal units — a guaranteed
tie — driven by the DSI sweep, `results/argmin_unique_perstep.json`):

| | value |
|---|---|
| attributes compared | 32 per step × 38 steps |
| ties seen (`count`) / refusals (`refuse_all`) | 3 / **12** — **the arm is ALIVE** |
| **`D = max|off − refuse_all|`, PER STEP** | **1003.0** (`step3.u1.last_burst`) |
| attribute-cells differing | **145** |
| `D` for `count` vs `off` (must be 0) | **0.0** |

**A second error, recorded: my end-state `D` read 0.0 on 4 896 attributes and
was PHASE-DEPENDENT.** Sampling only the final state of a per-step competition
washes the difference out — the same disease as §2.1 rule 3 (*a residual read
off a single snapshot is phase-dependent and will lie to you*), in the
attribute domain. **Tick one at a time and watch, or do not claim.**

> **THE RESOLUTION, and it is the honest form of (a): the arbitrary tie-break IS
> load-bearing on the substrate's per-step state, and NOT ONE published number
> depends on it.** The confabulated winner is real, it propagates, and every
> committed readout integrates it away.

---

## 4 — ARM C: PER-SITE ADMISSIBILITY — *is the escalation ADMISSIBLE, or merely POSSIBLE?*

**117** `Argmin`/`Argmax` occurrences across `seeds/*.json`. Enclosing context,
counted by reading the JSON structure (§12.1: a claim about what code selects is
not established by counting the tokens that select it — so the tie ATTRIBUTION
above is read off the firing, and this static table is only about SHAPE):

| immediate parent | sites | region |
|---|---|---|
| `Attr(sel, key)` | **85** | 61 in `effects`, 45 in `where` (all regions pooled) |
| `Eq(x, sel)` | **16** | |
| `Let` | 12 | |
| `definition` / `Neighbours` | 4 | |

**What each shape DOES with a refusal — MEASURED, not argued**
(`results/argmin_unique_admissibility.json`), on a tie / a unique extremum / an
empty source:

| caller shape | `Argmin` on tie | `ArgminUnique` on tie | vs a normal answer | **vs an EMPTY source** | class |
|---|---|---|---|---|---|
| bare selector | `#0` (a winner) | `None` | distinguishable | **NO** | **ERASED (into the empty null)** |
| `Attr(sel,"score")` — **85 sites** | `7.0` | `None` | distinguishable | **NO** | **ERASED (into the empty null)** |
| `Eq(node, sel)` — **16 sites**, the WTA idiom | `True` | **`False`** | **NO** | **NO** | **FULLY ERASED** |
| `Eq(Attr(sel),Lit)` — the where-clause idiom | `True` | **`False`** | **NO** | **NO** | **FULLY ERASED** |

**P4 CONFIRMED, and more sharply than predicted.** I predicted the majority of
verdict sites would be ERASED. Measured: **every shape in the seed layer erases
it**, and the two `Eq` shapes — *the only shape that actually ties on this
bench* — erase it **completely**: a refusal is `False`, exactly like *"you are
not the winner"* and exactly like *"there was nothing to choose from"*.

> **This is C1 one level down.** The refusal-capacity rung measured a structured
> refusal being erased at the FIELD boundary (`False` from `TransformDecode`,
> bare `None` from a walled `ShapeDecode`). Here the erasure happens at the
> **caller's OPERATOR** — and `Eq` is not a field selector, it is the seed
> layer's universal comparison. **A refusal the caller cannot represent is not a
> refusal.** `ArgminUnique` can refuse; today **no rule in this tree can hear
> it**.

**Therefore `ArgminUnique` is a PREREQUISITE, not a fix.** Arming it at a site
requires that site to gain a way to say *"ambiguous"* distinct from *"false"* —
which is a rule-layer change, not a Term-layer one, and is not this rung's.

---

## 5 — WHAT THIS COSTS, AND WHY IT IS NOT ARMED

*Priced by the standing rule: a hard gate is priced by the feature's ERROR RATE,
not its effect size.*

The tie rate on this bench is **0.0453 %** — and it is **not** a natural-scene
statistic. **201 of 201 ties come from calibration gates that install IDENTICAL
ideal cells on purpose.** So the number that would price an armed
`ArgminUnique` — *how often does a real scene tie?* — **is not measured here and
this rung does not claim it.** What is established: the null is currently
unrepresentable at every caller, which is the prerequisite the previous rung
said had to come first.

---

## 6 — WHAT I GOT WRONG

1. **P1: I predicted a tie rate > 5 %; it is 0.045 %.** My model — "small
   integer scores collide often" — was wrong about a bench whose selectors range
   over accumulated floats. **Two orders of magnitude, in the direction that
   makes my own build less urgent.**
2. **I BUILT THE FIX FOR THE SELECTOR THAT DOES NOT TIE.** `refuse_min` refused
   **0** of 201 ties. The brief's named target (`Argmin`) is, on this bench,
   the one selector with no tie exposure at all; the exposure is entirely
   `Argmax`, in two WTA rules. I did not predict this, and the instrument only
   caught it because it was built broader than the mechanism.
3. **MY FIRST VACUITY PROBE WAS A DEAD ARM AND I NEARLY REPORTED ITS NULL.** It
   printed `tie_break_is_load_bearing: false` from **8 seeds that never tied
   once**. Caught by the rule that a `D` may only be read next to a non-zero
   refusal count — the same rule §1.1 states for floors, pointed at refusals.
4. **MY END-STATE `D` WAS PHASE-DEPENDENT.** `D = 0.0` over 4 896 attributes
   sampled at the END of the probe; `D = 1003.0` when sampled per step on the
   same scenario. A single snapshot of a per-step competition is a coin flip
   (§2.1 rule 3, in a new domain).
5. **MY FIRST ADMISSIBILITY PROBE NEVER FIRED.** I wrote rules with an empty
   `match` list, which binds no variable, so the harness ran `run_rules()` → 0
   and every cell of the table read identically — **another table that looks
   publishable and is made of nothing.** Caught by positive-controlling the
   harness with a literal effect before reading one cell. The table above is
   Term-level evaluation instead, which needs no rule to fire.
6. **TWO UNKNOWN SEED SINKS IN MY OWN FILES.** `default_rng(sd)` inside a loop
   is exactly the shape `seed_audit` cannot resolve. The values are in-block and
   literal; **the ledger cannot see that they are**, which is the same class of
   blind spot the last rung recorded for offset expressions.

---

## 7 — SCOPE: WHAT IS *NOT* SHOWN

- **The bench is the unit.** "Zero landed numbers moved" means the 222 named
  vision-bench gates plus the four readouts in §3.2. Numbers in
  `results/*.json` produced by long rung scripts were **not** re-run.
- **`Argmax` is not fixed**, and nor are `EnclosedCount` or the motion sensor.
- **The tie rate is a property of THIS bench's stimulus distribution**, and that
  distribution is dominated by deliberate identical-unit calibration gates. It
  is **not** an estimate of the tie rate on natural scenes.
- **The compose readout row is dead** (0 refusals) and supports nothing.
- **Nothing is armed.** No seed binds `ArgminUnique`; the instrument defaults
  off; `count` mode is measured behaviourally identical to `off`.
- **The load-bearing `D = 1003.0` is measured on ONE scenario** (the dorsal DSI
  configuration). It proves the tie-break is not decorative; it does not
  quantify its effect anywhere else.
