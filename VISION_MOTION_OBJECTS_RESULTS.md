# COMMON MOTION AS THE OBJECT CRITERION — RESULTS

Pre-registration `VISION_MOTION_OBJECTS_PREREG.md`, committed **55d46a09**
before any real-frame number. Mechanism **fc5f0e7c**, runner + §13 gate
**2515607d**, sensor diagnostic **49239a9b**, texture diagnostic **37bd018c**.

Branch **`worktree-agent-a20b81fdd2342139a`** — the intended
`gamma-substrate/motion-objects` name is not what this worktree was created
under; reporting what I actually see. Engine **25fa11652e83**, **no Rust
change**. Provenance gate run as its **own step before any number**: **640
passed**. Oracle `scripts/rung7_vision_bench.sh`: **212 passed, 10 skipped,
exit 0** — this tree has no `data/`, the documented no-corpus case (222 is the
*collected* count; the 10 skips are `BSDS300 corpus absent`).

Seeds **84000–84999**. Corpora pinned and asserted at run time: **C1** cartoon
`08630d4b…`, **C2** live-action `119eca43…`. Configuration: one 72×72 decode,
**whole-frame 18×18 motion lattice** (block 4), consecutive frames. 40 frame
pairs per corpus per arm; **0 runs discarded** by the settle check.

---

## THE HEADLINE, IN FIVE LINES

**Common motion did NOT deliver few-and-large. It delivered MORE objects than
the matched static-form control (3.95 vs 0.17 multi-cell per frame on C2) and
they are SMALL — median 2 cells on a 324-cell field.**

**The registered arbitrary-partition floor is FAILED, and decisively: a
size-matched random connected partition of the same cells persists BETTER than
the motion-defined groups (0.803 vs 0.187).** The incumbent passed this floor
at +0.671; this rung fails it at −0.781.

**What DID hold: cohesion is real and CI-separated (within 0.404 vs between
3.950, paired lower bound +2.863), and the self-derived tolerance is
load-bearing — it cuts fragmentation 3.8× against exact equality (3.95 vs 15.10
multi/frame).**

**Registered outcome 3 occurred: grouping is motion-driven, and the grouping
RULE is wrong.**

**And the "re-earn every floor" instruction paid for itself outright** — see §2.

---

## 0 — TWO THINGS THAT REFRAME THE RUNG, BOTH RECORDED BEFORE THE VERDICT

### 0.1 C1 IS A DE-FACTO STILLS CORPUS (commit `49239a9b`)

Share of cells carrying a **non-zero motion vector**, by frame stride:

| corpus | stride 1 | stride 2 | stride 4 | stride 8 | distinct vectors/field (stride 1) |
|---|---|---|---|---|---|
| **C1** cartoon | **0.8%** | 1.5% | 2.0% | 3.8% | **2.3** |
| **C2** live-action | **31.2%** | 57.3% | 75.7% | 94.9% | **23.3** |

**The corpus pair inherited from the incumbent is not a video/video pair for
MOTION purposes.** A cartoon is animated on twos and threes and then
downsampled to 72×72, so consecutive frames are very often *identical*.

A **static-form** criterion does not care, and the incumbent measured C1
happily. A **common-motion** criterion cannot be tested on it. **C1's decline is
correct behaviour for a still and is NOT evidence about video. C2 is the only
arm that tests the hypothesis.** This was not anticipated in the
pre-registration and is the single biggest thing I got wrong in advance.

### 0.2 THE SENSOR IS ~11% WRONG ON A STIMULUS WHOSE ANSWER IS KNOWN (`37bd018c`)

A whole frame translated by exactly one block: every block's true displacement
is the same known vector, so any deviation is a **sensor** error.

| | overall error | Q1 flattest | Q2 | Q3 | Q4 most textured | zero-texture blocks |
|---|---|---|---|---|---|---|
| C1 | **10.9%** | **20.1%** | 7.4% | 11.1% | 4.9% | 0.08% |
| C2 | **10.8%** | 7.6% | 11.6% | 16.5% | 7.6% | 0.0% |

**Background texture IS load-bearing on C1** — the flattest quartile is 4×
more error-prone than the most textured, exactly as a cartoon's large flat
drawn regions predict. **On C2 there is no monotone texture relationship**, so
texture does not explain live-action sensor error. Neither corpus is
meaningfully untextured (≈0% zero-texture blocks), so the "flat background"
failure mode is **not** the dominant explanation here — it is a contributor on
C1 only.

**The bigger fact is the floor: ~11% of blocks get a wrong vector on a uniform
stimulus.** This bounds every count below, and it is the direct cause of the
registered global-pan failure (§5).

---

## 1 — M1: THE COUNT, REPORTED FIRST

**C2 (live-action — the only corpus that tests the hypothesis), n=40 pairs, 95% CI**

| arm | objects/frame | **MULTI-cell/frame** | multi size mean | **median** | max | tolerance |
|---|---|---|---|---|---|---|
| **motion, Otsu tolerance** | 16.30 [10.62, 21.98] | **3.95 [2.34, 5.56]** | 3.25 | **2** | 22 | 2.402 |
| **motion, exact equality** | 76.00 [61.89, 90.11] | **15.10 [12.88, 17.32]** | 3.14 | **2** | 23 | 0.0 |
| **INCUMBENT, matched lattice** | 2.33 | **0.17** | 2.57 | 2 | 4 | — |
| *incumbent, published G72* | *—* | *10–17* | *—* | *—* | *—* | *—* |

**C1 (de-facto stills), n=40 pairs**

| arm | objects/frame | MULTI-cell/frame | multi size mean | max |
|---|---|---|---|---|
| motion (Otsu ≡ exact here) | 1.60 [0.59, 2.61] | 0.25 [−0.06, 0.56] | 5.00 | 13 |
| INCUMBENT, matched lattice | 3.67 | **0.00** | — | 0 |

### The honest reading, which is not the flattering one

**NOT FEW.** Against the **matched** control — the incumbent's own best arm,
re-run on this rung's lattice, on the same frames — motion grouping produces
**3.95 multi-cell objects per frame against 0.17**, i.e. **23× MORE**, not
fewer.

**NOT LARGE.** Median multi-cell object size is **2 cells on a 324-cell
field**, identical to the matched incumbent's median of 2. The mean is 3.25 vs
2.57 and the max is 22 vs 4, so motion objects have a longer tail — but the
typical object is a **pair of cells**. These are fragments.

**The registered H1 — "fewer and larger" — is NOT supported.**

### §2's instruction paid for itself outright

**The matched incumbent yields 0.17 multi-cell protos per frame at this 18×18
whole-frame lattice, against its published 10–17 at G72.** That is a floor
movement of roughly **60–100×** from the configuration change alone.

**Had I compared my 3.95 to the published 10–17, I would have reported
"motion produces 3× FEWER objects — few and large, as predicted".** The matched
control says the opposite: I produce **23× more** than static form does under
identical conditions. That is precisely the phantom gain the brief warned
about, and the only thing that caught it was re-earning the floor.

**The cross-grain comparison to 10–17 is therefore reported as
uninterpretable, not as a result.**

### What the tolerance is worth, and it is real

Otsu-derived tolerance (2.402) against exact vector equality (0.0), same
frames, same everything else: **3.95 vs 15.10 multi-cell objects per frame, and
76.00 → 16.30 raw.** **The self-derived tolerance cuts fragmentation 3.8×.** It
is doing exactly what it was designed to do — it simply does not get the
mechanism to few-and-large. Exact equality reproduces roughly the incumbent's
*published* fragmentation level (15.1 vs 10–17), which is a tidy coincidence
and nothing more.

---

## 2 — M2: COHESION — **PASS**, and it is the clearest positive result here

Within-group vector dispersion against between-group, both **direct vector
reads** (dispersion of the vectors themselves, not an aggregate over pairwise
per-cell scalars).

| corpus \| arm | within | between | paired (between − within) lower bound | |
|---|---|---|---|---|
| C2 \| Otsu | **0.404** | **3.950** | **+2.863** | **PASS** |
| C2 \| exact | 0.000 | 2.258 | **+1.918** | PASS (trivially — exact equality forces within = 0) |
| C1 \| both | 0.000 | 2.034 | n/a (too few groups) | not evaluable |

**The groups genuinely move as one, and genuinely differ from each other.** On
the Otsu arm this is non-trivial: the tolerance admits within-group variation
(0.404) and the groups are still an order of magnitude more separated from each
other (3.950) than they are internally, with the paired CI far clear of zero.

The exact arm's within = 0 is **true by construction** and is reported as such
rather than as a stronger result.

---

## 3 — M3: CONTINUITY — **FAILED against the arbitrary-partition floor**

C2, paired 95% CI over consecutive pairs. Multi-cell groups only.

| arm | persist | FLOOR-A shuffle | **FLOOR-B arbitrary partition** | vs A (lo) | **vs B (lo)** | |
|---|---|---|---|---|---|---|
| Otsu | 0.187 | 0.033 | **0.803** | **+0.028** | **−0.781** | **FAIL** |
| exact | 0.316 | 0.177 | **0.665** | **+0.099** | **−0.402** | **FAIL** |

**A size-matched, BFS-connected, entirely arbitrary partition of the same cells
persists FOUR TIMES BETTER than the motion-defined groups (0.803 vs 0.187).**

Both arms clear the temporal-shuffle floor with the CI lower bound above zero,
so the groups are not *nothing* — they carry some frame-to-frame identity. But
**FLOOR-B is the floor that matters, and it is the one the incumbent passed at
+0.671 while this rung fails it at −0.781.**

**The mechanism of the failure is legible and follows directly from §1: the
groups are tiny.** At a median size of 2 cells, a random connected pair drawn
from the same cell set coincides with a real pair often enough to beat it. Small
fragments make FLOOR-B easy to clear and hard to beat.

**This is the arm that a persistence test alone would have certified.** Against
the shuffle floor only, this rung looks like a pass. Against an arbitrary
partition of the identical field it is a clear negative, and that is the honest
verdict on continuity.

---

## 4 — M4: BACKGROUND — the rule refuses it, the INDEPENDENT measure does not corroborate

The mint rule refuses a group whose motion matches the scene's dominant motion,
so by construction no background group is minted, and the **D3** control
confirms it (0 objects moving with the dominant vector).

But the registered check was deliberately on a quantity **the rule never
reads** — mean absolute *luminance* change over each minted object's support,
against the field mean:

| corpus \| arm | object Δlum | field Δlum | share of objects QUIETER than the field | |
|---|---|---|---|---|
| C1 \| both | **7.984** | 0.104 | **0.000** | correct direction, emphatically |
| C2 \| Otsu | **0.723** | 0.927 | **0.759** | **WRONG DIRECTION** |
| C2 \| exact | 1.152 | 0.927 | 0.692 | wrong direction |

**On C1 the result is exactly as predicted** — the few things that move in a
cartoon are genuinely high-change regions, 8× the field mean, and not one
minted object sits in a quiet region.

**On C2 it inverts: 76% of minted objects sit in regions with BELOW-average
luminance change**, and the object mean (0.723) is below the field mean
(0.927). The minted regions are not, on this independent measure, the parts of
the scene that are visibly changing.

**I read this as the ~11% sensor error floor (§0.2) surfacing in the count:**
spurious vectors in quiet regions differ from the dominant vector, so they pass
the contrast test and mint. **The registered prediction for M4 was ≈0 background
mints and I recorded it as a PASS-by-construction; the independent measure does
not support that reading on C2, and I am reporting the independent measure.**

---

## 5 — M5: STILLS — **frozen PASSES, global pan FAILS**

| arm | objects | multi-cell | | |
|---|---|---|---|---|
| **frozen frame** (V ≡ 0) | **0** | **0** | **PASS** | declared weak in advance — arithmetically forced |
| **global pan** (one still translated by a constant vector) | **26** | **5** | **FAIL** | registered PASS was ≈0 |

BSDS300 is **absent** from this tree, so this is the frozen-frame + global-pan
substitute, declared in the pre-registration rather than worked around.

**The global-pan failure is the SENSOR's, not the criterion's, and §0.2 says so
with ground truth.** On a uniform translation the mechanism should see one group
and refuse it. It does find the right dominant vector — `dom_v = (4.0, 4.0)`,
exactly the true displacement — but ~11% of blocks are estimated wrongly, those
wrong vectors differ from the dominant one, and adjacent wrong blocks group into
5 multi-cell false objects.

**The criterion behaves correctly given its input; the input is 11% wrong.** I
am not claiming this rescues the arm — the arm failed as registered, and a
mechanism is entitled to no better sensor than it has.

---

## 6 — M0: THE CONTROLS, AND THE DEAD-INSTRUMENT ARM ACTUALLY FIRED

**This thread has produced a vacuous mint reading as success three times. The
dead-instrument control here is not merely capable of firing — it fires.**

| control | result | |
|---|---|---|
| **D1** 6×4-cell rectangle translating (0,+1) on a static background | **1 multi-cell object, 18 members** (+6 single-cell) | positive control |
| **D2 disarmed** uniform field translating, contrast OFF | **1 object, 323 "members" on a field containing NO figure** | **THE TRAP, FIRED** |
| **D2 armed** identical field, contrast ON | **0 objects** | separated by graph data alone |
| **D3** large static textured background beside a moving figure | **0** objects moving with the dominant vector | background refused |
| **NOISE** iid random *vector* field | 15 objects, **2 multi-cell**, largest 14 | **REGISTERED CONTROL PARTIALLY FAILED** |

**D2 is the known-good shape the brief specified** — *uniform field, unseeded,
one proto with 144 "members" on a field containing no figure* — reproduced at
this rung's 324-cell lattice as **323 members**. The two arms differ **only** in
the `mcontrast` flag, which is graph data, not a Python code path. The run
aborts if it does not fire.

### The registered negative control that PARTIALLY FAILED

§5 registered: *"iid random vector field → must mint no multi-cell object."*
**It mints 2, the largest covering 14 of 324 cells.**

This is the **inherited Otsu limit, pre-registered as a limit rather than
discovered afterwards**: *Otsu has no null hypothesis — it returns a split on
any distribution, including one with no structure in it.* On a structureless
field it still returns a tolerance, and that tolerance groups a few cells by
chance.

It is a real cost and is not reframed away. It is smaller than the incumbent's
comparable failure (26% single-cell false mints on speckle) but it is not zero,
and the obvious fix — a minimum group size — is a hand-set threshold and is
**refused under §13**.

### The registered D1 prediction that was WRONG

§5 registered *"exactly 1 object, 24 members"*. The actual result is **1
multi-cell object of 18 members plus 6 single-cell objects**. Both discrepancies
are the **sensor**: a figure translating by exactly one block still mixes figure
and background within the blocks at its leading and trailing edges; and the 6
singletons are block-match noise, the same single-cell tax the incumbent's
replacement carries.

**The honest headline quantity is therefore MULTI-CELL objects** — which is also
exactly the quantity the incumbent reported (its 10–17 are *multi-cell*). Not
metric surgery: it matches the incumbent's own statistic, and the raw count is
reported alongside it everywhere.

---

## 7 — §13: NO MOTION-AGREEMENT CONSTANT ENTERED, AND THE GATE WAS PROVEN TO BITE

`tests/test_motion_objects_ast_migrated.py` — **8 passed**. A **term-tree AST
walk**, never a substring selector.

The tolerance **is not a number in any file**. It is Otsu's split of the field's
own adjacent-pair vector-difference distribution, and **the candidates are the
observed `pd` values themselves** — the tolerance is the `pd` of a cell the
graph picked (measured: **2.402** on C2, **0.0** on C1, both emergent from the
data). The reference frame is likewise an **Argmax over member count**, not a
size constant. A **median split was refused** as 50%-by-construction (the defect
`ch_drive_median` already carries in this tree).

Asserted both ways round, so a hole in one cannot satisfy the other:
- every `Lit` in a comparison is compared against a **0/1 flag** (`marm`,
  `mcontrast`, `mtol_exact`, `mflood`, `pd_done`, `mtol_done`, `dom_done`);
- **no** literal is compared against `v`, `pd`, `mtol`, `mlabel`, `cid`,
  `members`, `disp`, `contrast` or `dom_v`;
- the tolerance test is located **structurally** as
  `Magnitude(VecSub(whole vector, whole vector))` against an *attribute*;
- **no rule reads a scalar motion component** (`vy`/`vx`) — the vector-matrix
  representation was not flattened back into per-cell numbers.

**POSITIVE-CONTROLLED (§12.3) — a gate only ever seen pass is not a gate that
has been tested.** A hand-set tolerance of `2.5` injected into `mo_flood` turns
**two** tests RED; reverting turns them green, and the restored seed is
byte-identical to the builder's output. The one allowance (`dom_v` counts as a
whole vector) is **corroborated by its own test** asserting the seed assigns it
`Attr(R,"v")` verbatim and the adapter initialises it as `[0.0, 0.0]` — verified
*before* the gate was widened, never the reverse.

**What §13 does NOT cover, stated rather than hidden:** the sensor's aperture
`BLOCK` is a **declared magic-number residual**, exactly as `k` is. Its search
radius `R = BLOCK` **does** fall out (beyond its own extent a block shares no
pixels with its source, so the match is unconstrained rather than merely
coarse), but `BLOCK` itself does not.

---

## 8 — TWO ENGINE FACTS FOUND EN ROUTE, BOTH RECORDED

**1. `run_rules` reported a genuine fixpoint over a demonstrably unsettled
flood.** When a guard reads an attribute written mid-fixpoint on a node outside
its own match neighbourhood (`field.mtol`, written by `mo_tol_otsu`), bindings
evaluated before that write are not fully re-examined. The engine returned **0
further sweeps** while **6 cells, all in column 0, still had an admissible
neighbour carrying a smaller label** — and the guard evaluated `True` when
applied to exactly those cells by hand.

Broadcasting the tolerance onto the cells did **not** fix it. Only having the
tolerance present *before the first flood binding was evaluated* did (7 sweeps,
fully settled). Hence the explicit `mflood` phase flag — graph data; the adapter
only raises it and advances time.

**My seed comment claiming "the fixpoint orders the layers with no adapter
sequencing" was FALSE ON THIS ENGINE**, and is corrected in place rather than
left standing as a docstring doing a gate's job.

**2. The instrument check earned its place on its first firing.**
`assert_settled` recomputes the flood's fixpoint and the tolerance broadcast
**independently, in the reader**, from the settled graph. It is what caught the
above. A partially-flooded field is **indistinguishable by eye from a
legitimately fragmented one — and it inflates the object count, which is this
rung's headline.** Over the reported run it discarded **0 of 160** runs, so no
reported number rests on an unsettled flood.

---

## 9 — SEED ACCOUNTING: MEASURED, NOT ASSERTED

Declared **84000–84999**. Measured with `scripts/seed_audit.py` on this rung's
own runner:

```
resolved:       [84200, 84300, 84301, 84400, 84401, 84900, 84901, 84902]
unknown_sinks:  0
outside block:  []
```

**8 resolved seeds, ZERO unknown sinks.** Seeds are drawn from explicit literal
tuples so every draw is statically resolvable — *a `--check` that passes while
leaving sinks UNKNOWN has verified nothing*, which is why the corpus loop is an
explicit `(("C1", …), ("C2", …))` tuple sequence and not a dict subscript.

Both diagnostics (`motion_field_diagnostic.py`, `motion_texture_diagnostic.py`)
draw **no seeds** — pure numpy over the vector field.

---

## 10 — WHICH REGISTERED OUTCOME OCCURRED

§6 registered three. **The answer is outcome 3, with the warning attached to
outcome 2 realised.**

3. **Motion-driven but wrongly grouped.** ✅ Objects appear on video and are
   absent on a frozen still; cohesion is real and CI-separated; **but the
   grouping is fragmented (median 2 cells), fails the arbitrary-partition
   floor, and the background arm does not corroborate on an independent
   measure.** Grouping is motion-driven; **the grouping RULE is wrong.**

2. **"The criterion did not help"** — partially realised, and in a form the
   registration did not anticipate: it did not reproduce static form's
   fragmentation, it produced **its own, worse** one. Against the matched
   control it makes **23× more** objects, not fewer.

1. **The developmental case is REFUTED for this mechanism at this
   configuration.** Not few, not large, and continuity fails its floor.

**A null on M1 does not license tuning `BLOCK`, the radius or the tolerance
(§3.6, §5).** No parameter was swept in this rung, and the named next levers
below require a new pre-registration with a new mechanism-level hypothesis.

---

## 11 — A FRAMING CORRECTION TO THE PREMISE, RECORDED NOT EDITED

The brief's developmental premise was adjudicated against the literature while
this rung was running. **The premise is sound and on stronger footing than
claimed — common-motion segmentation is well-replicated and, per Scholl's BBS
commentary, is a mid-level vision mechanism confirmed in ADULTS by independent
methods, not merely an inference from infant looking-time studies.**

**But "long before" / innate is WRONG.** Newborns fail at it; it emerges around
**2–4 months**, and Franz & Triesch showed a **learning model reproduces the
developmental trajectory**.

**This pre-registration did not assert innateness** — it says common fate comes
*"before boundary or appearance"*, which is the ORDERING claim and is supported.
So there is nothing to retract, and per §3/§5 the wording is corrected here
rather than edited in the registered file, and no measurement was re-scoped over
it.

Worth recording because it cuts *toward* this substrate's framing: a grouping
competence that is **learned rather than innate** is what a tolerance derived
from the observation's own distribution is — the mechanism here has no built-in
agreement constant and reads one off the field it is looking at. That is a
consonance, not evidence, and it is not claimed as a result.

---

## 12 — WHAT IS NOT SHOWN (§8), AND THE NAMED NEXT LEVERS

**Not shown:**

- **No claim about codec-native motion vectors.** The path is **measurably
  unavailable on this corpus**: it is **HEVC/H.265 at 1920×1080**, and ffmpeg's
  HEVC decoder does not implement `export_mvs` — probed over 8 consecutive
  frames spanning I, P and B pictures, `MOTION_VECTORS` side data **absent on
  every one**, though PyAV 17.0.1 exposes the side-data type and accepts
  `flags2=+export_mvs`. **Every cost number here is for COMPUTED flow; a
  codec-native path would not pay it.**
- **No claim that the block-match flow is a good flow estimator** — it is
  measured at **~11% wrong per block** on a known-answer stimulus, and that
  bounds every result above.
- **`BLOCK` is a declared magic-number residual**; `k` remains one, inherited.
- **The 18×18 whole-frame lattice is coarser in cell count** than the
  incumbent's published G72 (16 tiles × 324). The matched control exists so one
  comparison is exactly like-for-like; **the published-10–17 comparison is
  across grains and is reported as uninterpretable.**
- **BSDS300 absent**, so the stills arm is frozen-frame + global-pan.
- **`ms_per_run` was measured under concurrent load** (a diagnostic ran
  alongside) and is not a clean timing number. No timing claim is made.
- **C1 supports no conclusion about video** (§0.1). Every C1 number is a stills
  result.

**Named next levers, each needing its own pre-registration:**

1. **SYNCHRONOUS CHANGE rather than motion** — pre-specified by the standing
   literature note as the alternative predicate: what binds a group may be
   *simultaneous change*, which is broader than translation and includes
   appearance, disappearance and correlated value change. **It is named here as
   the next hypothesis, NOT run**, because its registered trigger was "if the
   motion predicate UNDER-groups" and this rung's predicate **over**-groups
   (23× the matched control). Running it now would be a post-hoc rescue of a
   different failure than the one it was specified for.
2. **A better sensor before a better criterion.** At an 11% per-block error
   floor the criterion cannot be evaluated cleanly. The frame stride is the
   obvious lever (C2 goes 31% → 76% non-zero cells from stride 1 → 4) and is
   **deliberately not swept here** (§3.6).
3. **The fragment size is the mechanism's real defect** — median 2 cells is
   what fails FLOOR-B. Whatever comes next has to make groups *bigger*, and it
   must do so without a hand-set minimum size (§13).
