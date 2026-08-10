# REFUSAL CAPACITY — RESULTS

Pre-registration `VISION_REFUSAL_CAPACITY_PREREG.md`, committed **`eac0bdd1`**
before any number.

- **branch (as observed):** `worktree-agent-a041ad6a5be1b42ae` — the name I
  actually see; no `gamma-substrate/refusal-capacity` name exists.
- **base SHA (as observed):** `91e367f0c332ae29793609c6816f5ba42971d6eb`
- **engine:** `9931e144d19b` (`own` build via `scripts/engine_build.sh`).
  **THIS RUNG ADDS NO RUST.**
- **provenance gate, its OWN step before any number:**
  `tests/test_engine_provenance_migrated.py` **7 passed** — and
  `provenance_line()` is ALSO printed from inside the measuring process and
  compared against `EXPECT_ENGINE`, **aborting on divergence**.
- **oracle:** `bash scripts/rung7_vision_bench.sh` → **222 passed, 0 failed** BEFORE and AFTER all changes,
  exit 0, `data/` symlinked (§10.2, the with-corpus case).
- **seeds:** 106000–106999 declared; **106000–106199 (Δ), 106200–106399
  (DepthInfer two-layer), 106400–106599 (BlinkBridge gap)** drawn in-block.
  `check_claim` recorded verbatim in the pre-registration with its
  **497 unresolved sinks** priced.
  **AND FIVE 200-WIDE RANGES DRAWN *OUTSIDE* THE BLOCK, BY MY ERROR — DISCLOSED,
  NOT BURIED (see §11.6): 600000–600199, 606000–606199, 706000–706199,
  806000–806199, 906000–906199.** `check_claim` run on all five AFTER the fact:
  **CLEAN, no collision detected, on every one.** They are recorded here as
  CONSUMED so no later rung takes them. `scripts/seed_audit.py` reports
  **8 unknown sinks** for this runner — the offset expressions are exactly what
  it cannot resolve, which is how the error stayed invisible.
- **no seed manifest, no default moved, no other rung's file edited.**

---

## THE HEADLINE, IN SIX LINES

**Refusal capacity is not one property of "the eye" — it splits FOUR ways, and
the split is almost perfectly predicted by ONE structural fact: whether the
mechanism's verdict is a COMPARISON or a SELECTION.**

**Fifteen mechanisms audited under 13 pre-registered predictions. Five refuse
for the right reason** — `TimeInfer`,
`TransformDecode`, `DimInfer`, `GenInfer`, `DepthInfer` (Δ = +1.0000, +0.9950,
+1.0000, +0.9900, +1.0000, every CI separated from 0). **Every one of them
decides by EXACT EQUALITY AGAINST A RECONSTRUCTION, and every one can therefore
FAIL.** Every mechanism that cannot refuse decides by **selecting a best from a
set** — and a selection has no false case.

**`GapAbduce` and `BlinkBridge` explained 200 of 200 stimuli in each arm,
true and false alike.** `BlinkBridge` across a real gap assigns the **IDENTICAL
confidence 0.6667** to a continuation that is right and one that is wrong, and
silently emits a **32-cell correction on 200 of 200** false continuations.

**The most useful finding is the cheapest fix in the tree: the substrate ALREADY
CONTAINS the pattern that fixes `Argmin`, and it was applied to CONFIG reads and
never to VERDICT reads.** `PickUnique` escalates on ambiguity; `Argmin` returned
a winner from **five identical candidates** — a set in which nothing is better
than anything else — and its null is reachable only on an EMPTY source.

**A structured refusal is ERASED at the field boundary (C1 confirmed):** the
same question — *did you explain it?* — returns `False` from one refusing
mechanism and bare `None` from another, and the two are indistinguishable to a
rule.

**And this rung's own instrument died once and was caught by its own
pre-registered positive control**, reporting a uniform, perfectly-formed,
entirely fake Δ = 0 across all eight Terms. §7 requires I lead with that.

### THE CLASSIFICATION, IN ONE TABLE

| verdict | mechanisms | demonstrated by |
|---|---|---|
| **DOES REFUSE (earned)** | `TimeInfer`, `TransformDecode`, `DimInfer`, `GenInfer`, `DepthInfer` | Δ ≥ +0.99, CI-separated, on 200 matched pairs |
| **DOES NOT REFUSE** | `GapAbduce`, `BlinkBridge` (gap ≥ 1) | explained **400/400** and **400/400**; identical confidence on true and false |
| **DOES NOT REFUSE usefully** | `ShapeDecode` | Δ = +0.10 against a **76.5%** base refusal rate |
| **REFUSES VACUOUSLY** | `ChangeDetect`, `TemporalDiff`, `Foveate` | null on malformed arity, **0/400** on content |
| **CANNOT REFUSE** | `Argmin`, `EnclosedCount`, motion sensor | a winner from 5 identical candidates; `holes=0` for both zero and unmeasurable; 16/16 motion vectors on pure noise |
| **ESCALATES (neither)** | `PickUnique` | raises on 2 candidates |

---

## 0 — THE INSTRUMENT DIED FIRST, AND THE POSITIVE CONTROL IS WHY YOU ARE
##     READING NUMBERS AND NOT A FAKE NULL

*Reported first, not buried, because it is the single most transferable thing
this rung produced.*

The first confirmatory run returned this:

```
  TimeInfer        ACCEPTS=False   <-- DEAD on this family
  BlinkBridge      ACCEPTS=False   <-- DEAD on this family
  ...  (all 8)
  TimeInfer        null_U=200/200 null_E=200/200  D=+0.0000 [-0.0188,+0.0188]
  DepthInfer       null_U=200/200 null_E=200/200  D=+0.0000 [-0.0188,+0.0188]
  ...  (all 8)
```

**Every mechanism refused everything, and every Δ was exactly zero with a tight
CI.** That is a publishable-looking table. It is also completely false.

**The cause:** the engine returns a **Python `dict`** for a whole-verdict read
(`field=""`). My reader accepted only a list-of-pairs and returned `None` for a
dict, and `None` is *itself* one of the nulls this rung classifies — so a broken
reader was indistinguishable from a universal refusal **by construction of the
very quantity being measured.**

**Why I believed it:** my exploratory pilot printed what looked like parsed
dicts. It was printing its own **fallback branch** (`str(val)`), which renders a
dict identically to a parsed one. **I read a fallback as a success and carried
the misreading into the confirmatory runner.**

**What caught it:** arm A, the pre-registered positive control — *"a mechanism
you have not made ACCEPT is one whose refusals mean nothing"* — §1.1 pointed at
refusal instead of at a floor. Nothing else in the design would have. A refusal
audit is uniquely exposed to this failure, because **a dead reader and a perfect
refuser produce byte-identical output.** The runner now ABORTS if every
mechanism fails its own best case.

**The generalisation, offered upward:** §1.1 says *a dead arm scores a perfect
floor*. Its refusal-side twin is sharper — **A DEAD READER SCORES A PERFECT
REFUSAL ARM, and on this class of question the two are the same measurement.**
Any rung measuring abstention must positive-control acceptance FIRST, in the
same process, on the same reader.

---

## 1 — WHAT IS COUNTED (restated, because a runner that does not say what it
##     counts is a rumour)

**Δ_M = P(null | UNEXPLAINABLE) − P(null | EXPLAINABLE)** over `n = 200` matched
pairs identical in every guard-visible property (arity, frame count, cell count,
non-emptiness, types, values). Newcombe CIs from two Wilson intervals.

**A refusal RATE is a property of the stimulus distribution; Δ is a property of
the mechanism.** A mechanism refusing 90% of both arms scores 0; one refusing 2%
of `U` and 0% of `E` scores +2%.

**The engine's `checked` counter was pre-registered as NOT the classifier, and
the measurement vindicates that in both directions:**

- `TimeInfer` refuses with **`checked = 0`** and has **Δ = +1.0000**. Read as a
  classifier, `checked` would have called the arc's cleanest refuser vacuous.
- `TransformDecode` runs **`checked = 19` on an EMPTY goal** — a full search on
  nothing — and also `19` on every accept and every refuse. Its search EXTENT is
  stimulus-independent while its OUTCOME is not.

**`checked` counts CODEBOOK candidates. It measures COST, never DECISION.** This
was declared in advance and is the concrete instance of the arc's recorded
failure mode — the right discriminator measured on the wrong quantity.

---

## 2 — ARM G: THE GUARD ARM (deterministic, 0 seeds)

Every mechanism, on a degenerate input.

| mechanism | null? | `checked` | reason |
|---|---|---|---|
| `TimeInfer` | yes | **0** | — |
| `DepthInfer` | yes | **0** | `insufficient_frames` |
| `BlinkBridge` | yes | **0** | — |
| `GapAbduce` | yes | **0** | `no_gap_structure` |
| `ShapeDecode` | yes | **absent** | `no goal signature to compose toward` |
| `TransformDecode` | yes | **19** | — (none exists) |
| `DimInfer` | yes | **294** | — (none exists) |
| `GenInfer` | yes | **3024** | — (none exists) |

**Two facts fall out of this table that no source reading would have given:**

1. **The goal-driven family has NO GUARD AT ALL.** `TransformDecode`, `DimInfer`
   and `GenInfer` run their full search on an **empty goal** — 19, 294 and 3024
   candidates examined to conclude that nothing explains nothing. They cannot
   refuse cheaply. That is the opposite of the vacuous-refusal failure mode and
   it costs real compute on every malformed input.
2. **`ShapeDecode`'s refusal carries no `checked` field at all**, because its
   wall is a 2-key dict (`authored`, `reason`) rather than the family's 8-key
   verdict. **Its refusals are structurally uninstrumented** — you cannot tell
   from the verdict whether it looked.

---

## 3 — ARM A: THE POSITIVE CONTROL (deterministic, 0 seeds)

**All 9 mechanisms in the verdict family ACCEPT their own best case.** None is
dead. The one at genuine risk was P2:

> **`DepthInfer` two-layer probe → `explained=True`, `reason='minted'`,
> `n_layers=2`, `checked=4`.**

**P2 CONFIRMED, and it mattered.** `DepthInfer` refused all six pilot stimuli
and all 400 single-surface sequence stimuli with `single_velocity` /
`non_constant_velocity`. **Read without arm A, that is "DepthInfer refuses
everything" — a mechanism apparently DEAD, whose five named reasons are
decoration.** It is not: it is a mechanism whose competence is *two or more
surfaces*, correctly refusing a family that contains one. **The refusals were
about the STIMULUS, and only the acceptance arm can tell you that.**

---

## 4 — ARM Δ: THE CLASSIFICATION, EACH DEMONSTRATED BY CONSTRUCTION

`n = 200` matched pairs, seeds 106000–106199.

| mechanism | null_U | null_E | **Δ** | 95% CI | verdict |
|---|---|---|---|---|---|
| `TimeInfer` | 200/200 | 0/200 | **+1.0000** | [+0.9733, +1.0000] | **DOES REFUSE (earned)** |
| `TransformDecode` | 200/200 | 1/200 | **+0.9950** | [+0.9654, +0.9991] | **DOES REFUSE (earned)** |
| `DimInfer` | 200/200 | 0/200 | **+1.0000** | [+0.9733, +1.0000] | **DOES REFUSE (earned)** |
| `GenInfer` | 198/200 | 0/200 | **+0.9900** | [+0.9581, +0.9973] | **DOES REFUSE (earned)** |
| `BlinkBridge` (gap = 0) | 200/200 | 0/200 | **+1.0000** | [+0.9733, +1.0000] | earned **at gap 0 only** — see §5 |
| `ShapeDecode` | 173/200 | 153/200 | **+0.1000** | [+0.0238, +0.1753] | **DOES NOT REFUSE (usefully)** — see §6 |
| `GapAbduce` | **0/200** | **0/200** | **+0.0000** | [−0.0188, +0.0188] | **DOES NOT REFUSE** |
| `DepthInfer` (1-surface) | 200/200 | 200/200 | +0.0000 | [−0.0188, +0.0188] | **arm saturated — VOID**, see §4.1 |
| **`DepthInfer` (2-layer, its live family)** | **200/200** | **0/200** | **+1.0000** | **[+0.9733, +1.0000]** | **DOES REFUSE (earned)** |
| `ChangeDetect` | 0/200 | 0/200 | **+0.0000** | [−0.0188, +0.0188] | **REFUSES VACUOUSLY** |
| `TemporalDiff` | 0/200 | 0/200 | **+0.0000** | [−0.0188, +0.0188] | **REFUSES VACUOUSLY** |
| `Foveate` | 0/200 | 0/200 | **+0.0000** | [−0.0188, +0.0188] | **REFUSES VACUOUSLY** |

### 4.1 `DepthInfer` — THE ARM THAT WOULD HAVE BEEN READ BACKWARDS

**On the single-surface family: Δ = 0.0000, refusing 200/200 in BOTH arms.**
Read alone, that is a mechanism with no discriminative power — indistinguishable
in the table from `GapAbduce`'s 0/200-both, one saturated at the top and one at
the bottom.

**On the two-layer family — the family it is FOR — Δ = +1.0000 [+0.9733,
+1.0000], and all 200 refusals name `non_constant_velocity`.** It refuses a
non-rigid second surface with perfect separation from a rigid one, at
`checked = 4`.

> **A saturated Δ is not a classification, it is a report that you measured on
> the wrong family.** Both saturation directions look like "Δ ≈ 0, no capacity",
> and only arm A distinguishes them. This is the same defect the margin rung
> recorded — *a disagreement arm must be drawn from the regime where the
> instrument is LIVE* — arriving independently from the refusal side.

Each of the three shrug-class primitives returns its null on a **malformed**
input (`guard(malformed) → null = True`) and **never once on image content**,
across 200 structured-vs-noise pairs. Their null is an arity check, not a
verdict.

---

## 5 — `GapAbduce` AND `BlinkBridge`: THE MECHANISMS THAT CANNOT SAY NO

**`GapAbduce` explained 200 of 200 unexplainable stimuli and 200 of 200
explainable ones.** Not a single refusal in 400 calls. Its only null in the
whole rung is `no_gap_structure`, which fires on a degenerate input at
`checked = 0`. **This independently reproduces its own rung's finding — "the
substrate did not lack this operator by oversight; it lacked the operator that
cannot refuse" — by construction rather than by rate**, and it does so on a
completely different stimulus family.

**`BlinkBridge` is the sharper case, because it looks like a refuser at gap 0
and stops being one exactly where it is used.**

| arm | null_U | null_E | Δ | confidence E | confidence U | correction on U |
|---|---|---|---|---|---|---|
| gap = 0 | 200/200 | 0/200 | +1.0000 | — | — | — |
| **gap ≥ 1 (the regime it exists for)** | **0/200** | **0/200** | **+0.0000** | **0.6667** | **0.6667** | **32 cells, 200/200** |

**The confidence is IDENTICAL to four decimal places on a continuation that is
right and one that is wrong.** The mechanism emits a well-formed bridge, a
number that reads as moderate confidence, and a 32-cell correction on every
single false continuation — the dot's 16 cells absent where the belief put them
and present where they actually are.

**P3 CONFIRMED. And the measurement adds something its predecessor did not
have:** the timephi rung established confabulate-always from the confidence
DECAY (`support/(support+gap)`). This shows the confidence does not just decay —
**it does not vary with truth at all.** A downstream consumer reading
`confidence` is reading the gap length, not the evidence.

**This is why `kind = "freeze"` is not a refusal.** The guard arm emits `freeze`
at `checked = 0` on empty input, and the gap-0 arm emits `freeze` after a failed
search. **One symbol, two meanings, no way to tell them apart from the verdict.**

---

## 6 — `ShapeDecode`: MY STRONGEST PREDICTION BROKE, AND THE TRUTH IS WORSE
##     THAN THE PREDICTION IN A DIFFERENT WAY

**P5 predicted Δ ≤ 0 — that `ShapeDecode` refuses the true thing more often than
the false one.** Measured **Δ = +0.1000 [+0.0238, +0.1753]**, CI excluding 0 in
the direction I predicted against. **P5 IS FALSIFIED and is pinned at its
measured value.**

The pilot observation that drove P5 — it authored a plan for an alien cell set
and refused a pure translate — **is real but is not the dominant behaviour.**
What the powered arm shows instead:

> **`ShapeDecode` refuses 153 of 200 stimuli it should explain (76.5%), and 173
> of 200 it should not (86.5%).** It has a Δ, and the Δ is real, and it is
> **+0.10 against a base refusal rate of 76.5%.**

**This is exactly the case the pre-registration's unit was built to separate,
and it is the best justification for that unit in the rung.** On a refusal RATE
`ShapeDecode` looks like the most cautious mechanism measured — 86.5% refusal on
bad input, higher than several of the earned refusers. On Δ it is nearly
indiscriminate: **91% of its refusals would have happened anyway.**

Compounding it, from §2: its wall carries no `checked`, so **you cannot tell
which of those 153 refusals searched.**

---

## 7 — THE SELECTORS, WHERE THE SEED LAYER'S GUARDS ARE BUILT FROM

This is the part with a cheap, named, already-precedented fix.

**`Argmin` — CANNOT REFUSE, confirmed by construction (P10).** Given five
candidates with **identical values** — a set in which nothing is better than
anything else, so there is nothing to decide — `Argmin` **returned node `#727`,
not a null**, on all 200 draws. Its null is reachable only on an EMPTY source
(`guard(EMPTY) → null = True`). There is no threshold in it, and no place to put
one.

**`PickUnique` — ESCALATES rather than refusing (P11), verbatim from the
engine:**

```
0 candidates -> null=True    1 -> value=True    2 -> ESCALATED: PanicException

thread '<unnamed>' panicked at src/term.rs:4663:17:
PickUnique: AMBIGUOUS selection — 2 candidates where exactly one was required.
A config read found more than one node and `Pick` would have silently returned
an arbitrary one of them, leaving the rest inert (VISION_PROTOCOL §1.1).
```

It is the only mechanism measured here that treats ambiguity as an error instead
of swallowing it — **and its own panic message states the disease it was built to
cure, in the words of the rung that built it.**

**And that is the finding:** the substrate already contains the exact pattern
that `Argmin` lacks, built by this arc, for this reason. **It was bound to 185
CONFIGURATION reads and to zero VERDICT reads.** So:

> **The seed layer's CONFIGURATION reads hard-fail on ambiguity; its PERCEPTUAL
> verdicts soft-fail.** A rule of the form `Eq(R, Argmin{…})` — which appears in
> border-ownership and quanta-navigation guards — is satisfiable by an arbitrary
> tie-break, and the rule cannot tell a decided winner from a coin flip.

**`EnclosedCount` — CANNOT REFUSE (P12), with the sentinel hazard demonstrated
rather than argued:**

| input | `holes` | `grid_w` | null? |
|---|---|---|---|
| a closed loop | **1.0** | 11.0 | no |
| an open scribble | **0.0** | 5.0 | no |
| **DEGENERATE (empty)** | **0.0** | **0.0** | **no** |

**The degenerate row and the open-scribble row report the SAME `holes = 0.0`.**
"Measured zero holes" and "could not measure" are the same number, and only
`grid_w` separates them. A caller reading `holes` alone — which is what the field
is named for — **cannot tell a measurement from an absence.**

**The motion sensor — CANNOT REFUSE (P13), by output type.** On 200 pairs of
INDEPENDENT noise fields — where no motion exists to find — it emitted **16
well-formed vectors every time, 0/200 with any NaN, and 0 of 16 exactly zero.**
It did not merely fail to abstain: **on pure noise it reported motion in every
single block.** There is no value in its codomain that means *I don't know*.

---

## 8 — ARM C1: **THE STRUCTURED REFUSAL IS ERASED AT THE FIELD BOUNDARY.
##     C1 CONFIRMED.**

Read from the engine, same process, same call shape:

| Term, refusing | `field=` | returns |
|---|---|---|
| **WALLED `ShapeDecode`** | `authored` | `False` |
| **WALLED `ShapeDecode`** | `reason` | `'no goal signature to compose toward'` |
| **WALLED `ShapeDecode`** | **`explained`** | **`None`** |
| **WALLED `ShapeDecode`** | **`checked`** | **`None`** |
| **WALLED `ShapeDecode`** | **`plan`** | **`None`** |
| REFUSED `TransformDecode` | `explained` | **`False`** |
| REFUSED `TransformDecode` | `checked` | `19` |

**The same question — "did you explain it?" — returns `False` from one refusing
mechanism and `None` from another.** `ShapeDecode`'s wall is a 2-key dict, so
every field outside `{authored, reason}` collapses to a bare `Value::None` — the
same value a shrug returns, and the same value my own broken reader produced in
§0.

**Why this is load-bearing and not a curiosity.** The seed layer's refusal
idiom is a floor rule whose `where` reads the Term's verdict field
(`time_axis`'s `time_infer_floor` tests
`NOT(Eq(TimeInfer{…, field:"explained"}, true))`). Against a WALLED
`ShapeDecode` that field is `None`, not `False`:

> **A rule written to fire on a refusal fires differently — or not at all —
> depending on WHICH KIND of refusal it received, and the two are
> indistinguishable at the field it reads.** Refusal capacity present at the
> Term boundary is **not** refusal capacity available to the graph.

**Scope, stated rather than implied:** I measured the ERASURE, not a
misfiring rule. No seed rule reads `ShapeDecode{field:"explained"}` today, so
this is a **latent** defect, not an active one — which is exactly the state
`PickUnique`'s hazard was in before it bit. It is reported, not patched (§5:
this rung did not pre-register a repair).

---

## 8.5 — WHAT A REFUSAL ALREADY COSTS (mean `checked`, both arms)

| mechanism | `checked` on ACCEPT | `checked` on REFUSE | refusal / accept |
|---|---|---|---|
| `TimeInfer` | 0 | **0** | **free** |
| `BlinkBridge` | 0 | 0 | free |
| `GapAbduce` | 0 | 0 | free (it never refuses) |
| `DepthInfer` | 2 | 2 | 1× |
| `TransformDecode` | 19 | 19 | 1× |
| `DimInfer` | 294 | 294 | 1× |
| **`GenInfer`** | **11 178** | **131 198** | **11.7×** |

**Two things this says that the classification does not.**

1. **An earned refusal is not intrinsically expensive.** `TimeInfer` refuses
   with perfect separation at **zero** codebook candidates, because its verdict
   is a frame-to-frame comparison that never needs the codebook. **Refusal
   capacity and search cost are independent axes** — which is the second reason
   `checked` could not have been the classifier.
2. **Where refusal IS expensive, it is expensive ASYMMETRICALLY.** `GenInfer`
   pays **11.7× more to say no than to say yes**, because a refusal is the only
   verdict that requires exhausting the search. **That asymmetry is the real
   price of "cannot refuse" being cheap** — and it is the honest reason a
   confabulating mechanism is tempting to build.

---

## 9 — WHAT WOULD EACH COST TO MAKE REFUSABLE?

The three classes need three different fixes, and only one of them is cheap.

### 9.1 CANNOT REFUSE ⇒ a REPRESENTATION change (the codomain must gain a null)

| mechanism | the change | cost | §13 risk |
|---|---|---|---|
| **`Argmin`** | **an `ArgminUnique` sibling: return the null when the extremum is not unique.** The pattern EXISTS (`PickUnique`); uniqueness is exact equality, so there is **no constant and nowhere to put one**. | one Rust variant + a rebind of the *verdict-side* `Argmin` sites only. Config sites untouched. | **none** — this is the strongest §13 shape available: not a number that falls out, but no number at all. |
| **motion sensor** | emit the **SAD margin** (best vs second-best) alongside the vector, so "no unique minimum" becomes representable. | one extra reduction over the offset scan, no new parameter. | **HIGH the moment anyone thresholds the margin.** The margin is a BOUND, and the arc has a worked derivation for one (the colour rung's packing radius). *Do not tune it.* |
| **`EnclosedCount`** | make degeneracy a distinct value rather than a sentinel pair. | trivial. | none |

**Priced by the standing rule, not by hope:** *a hard gate is priced by the
feature's ERROR RATE, not its effect size.* An `ArgminUnique` gate would refuse
exactly when the extremum ties, and its error rate is therefore the tie rate — a
quantity that must be measured on real scenes before it is armed anywhere. **This
rung does not arm it; it establishes that the null is currently unrepresentable,
which is the prerequisite.**

### 9.2 DOES NOT REFUSE ⇒ a CONSTRAINT THE SEARCH CAN FAIL

Both offenders emit intermediates and check them against nothing.

- **`GapAbduce`** — its own rung named the fix (check the abduced intermediates
  against the scene) and **a concurrent rung is testing it. Not duplicated
  here.** Used as the worked example of what a good answer looks like.
- **`BlinkBridge`** — **structurally identical and NOT currently owned.** It
  emits `bridged` frames across the gap and compares them to nothing. The same
  constraint applies verbatim, and this rung's measurement supplies the quantity
  that would become falsifiable: a bridge that predicts the resume frame and is
  wrong by 32 cells currently reports confidence 0.6667. **That 32 is already
  computed and already reported. Nothing reads it.**
- **`ShapeDecode`** — a different fix: it RANKS by coverage and returns the best
  plan whatever its quality. It needs an **admission bound**, and the arc has one
  worked derivation (the colour rung's packing radius) plus one measured negative
  (the margin rung: no margin threshold falls out). **Its Δ = +0.10 against a
  76.5% base rate says the bound would have to buy a great deal to be worth the
  recall it costs.**

### 9.3 REFUSES VACUOUSLY ⇒ **nothing should be built, and that is the answer to
###     the brief's third question**

`ChangeDetect`, `TemporalDiff` and `Foveate` are **pure functions**. A
convolution has no truth to decline. **A refusal is not admissible in them at
all** — their arity guard is the correct and complete behaviour, and adding a
content-sensitive null would be inventing a verdict where there is no
proposition.

> **Where is a refusal even admissible? Exactly where the mechanism ASSERTS
> something that could be false.** The shrug class asserts nothing; it
> transforms. The measurement makes this crisp rather than definitional: their
> Δ is **0.0000 exactly**, not approximately, on 200 pairs each.

---

## 10 — THE STRUCTURAL LAW THE TABLE OBEYS

The classification is not a list. **Every earned refuser decides by EXACT
EQUALITY against a RECONSTRUCTION; every mechanism that cannot refuse decides by
SELECTING A BEST from a set.**

| | verdict is… | can fail? |
|---|---|---|
| `TimeInfer`, `TransformDecode`, `DimInfer`, `GenInfer`, `DepthInfer` | *does the reconstruction EQUAL the observation?* | **yes** — the comparison has a false case |
| `Argmin`, `ShapeDecode`, the motion sensor | *which candidate is BEST?* | **no** — "best" is always defined on a non-empty set |
| `ChangeDetect`, `TemporalDiff`, `Foveate` | *nothing — they TRANSFORM* | **not applicable** — no proposition to be false |
| `GapAbduce`, `BlinkBridge` | *fit a generator to the endpoints* | **no** — two points and one free generator always fit |

**A comparison can be false. A selection cannot.** That is the whole table, and
it says the fix is never "make it more careful" — it is **give the mechanism
something to be wrong ABOUT.** `GapAbduce`'s named fix (check the intermediates)
is precisely a conversion of a selection into a comparison, which is why it is
the right shape.

---

## 11 — WHAT I GOT WRONG

1. **THE INSTRUMENT DIED AND I ALMOST PUBLISHED IT** (§0). A `dict`-vs-pairs
   reader bug made every mechanism read as a universal refuser with a tight CI.
   Caught by my own pre-registered positive control, not by inspection.
2. **I MISREAD MY OWN PILOT'S FALLBACK BRANCH AS ITS SUCCESS BRANCH.** The
   pilot's printer rendered an unparsed dict identically to a parsed one, and I
   carried the misreading into the confirmatory runner. **A printer that cannot
   fail is a printer that cannot inform.**
3. **P5 (`ShapeDecode` anti-correlated) IS FALSIFIED.** I predicted Δ ≤ 0 from a
   single vivid pilot observation; measured **+0.10, CI excluding 0 in the
   direction I predicted against.** The pilot observation was real and
   unrepresentative. **n = 1 is a hypothesis generator, never a direction.**
4. **THREE ARGUMENT-NAME ERRORS AGAINST THE ENGINE** (`image` vs `image_vals`,
   `type` vs `node_type`, `Attr(var=,name=)` vs `Attr(node=,key=)`), each of
   which raised loudly rather than silently — which is the only reason they cost
   minutes instead of a result. Noted because the four comment-vs-engine
   divergences recorded this week were the SILENT kind.
6. **I DREW 1000 SEEDS OUTSIDE MY OWN BLOCK, AND THE LEDGER TOOL COULD NOT SEE
   IT.** The goal-family and primitive arms seed with `default_rng(sd + 500_000)`
   and four sibling offsets, so a run declared as 106000–106999 actually consumed
   **600000–600199, 606000–606199, 706000–706199, 806000–806199 and
   906000–906199.** I checked all five after the fact and every one is CLEAN — so
   **no result of mine or anyone else's is affected — but that is LUCK, not
   discipline**, and the check that should have caught it structurally could not:
   `seed_audit` reports **8 unknown sinks** for this file, because a `sd + K`
   expression is precisely the shape it cannot resolve.
   **The rule this earns: an OFFSET seed expression defeats the static ledger as
   completely as a CLI value does.** The block-discipline habit is "seed from a
   named base"; the habit that is actually safe is **"every generator's argument
   must be an element of the declared range, not a function of one."** The five
   ranges are recorded above as consumed rather than quietly re-run in-block,
   because re-running to make the record tidy would change the numbers after
   seeing them (§5).
7. **A `pkill -f` matching my own patch process** killed an in-flight edit and
   reported a patch as applied when it was not; caught by a `grep -c` on the
   result. **Verify the patch landed, do not trust the exit code of the thing
   that wrote it.**

---

## 12 — SCOPE: WHAT IS *NOT* SHOWN

- **These are TERM-level mechanisms.** The seed-rule layer (`bo_mint_*`,
  `ci_assign`/`ci_refuse`, `uq_admit`/`uq_refuse_ambiguous`, `l3_corroborate`)
  is **NOT measured here**; it is a different unit (non-firing) needing its own
  pre-registration. What this rung establishes is a **lower bound** on it: a rule
  can be no more refusable than the Terms it is built from.
- **Stimuli are synthetic** cell sets and dot sequences, not natural images. A
  mechanism that refuses correctly here may not on natural input.
- **`DepthInfer`'s single-surface Δ arm is VOID** (saturated at 200/200 both
  sides). Its capacity rests on arm A and the two-layer arm.
- **No claim is made about `GapAbduce`'s named fix** — a concurrent rung owns it.
- **Nothing here is armed.** No default moved, no seed shipped, no Rust added.
  `ArgminUnique` is **NAMED, NOT BUILT.**
- **Δ is bounded to ~±1.9pp at the extremes by n = 200**; a true |Δ| below that
  is not resolvable by this rung.
