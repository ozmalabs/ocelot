# SCALE WALL, SPLIT THREE WAYS — RESULTS

*Pre-registration: `VISION_SCALE_SPLIT_PREREG.md`, committed BEFORE any measurement at
`77290bcd1f4a83c0b7b51adba28c48f4e21ef018` (base `62fadd1a18edca2124aff57e85af4f47ae6f8b99`).*

**Engine (§10):** `276414fb0a95 @ .../agent-aac1f11329dca51a4/.../runners/dsl/python/substrate_rs/_native.abi3.so`
— **this rung's OWN build**, in this worktree. This rung **ADDS RUST**, so a shared
binary would have been invalid; the engine was built here, hashed at source and
destination (`7b4a2ee39f5932605d4134788a66f98a`), and every number below comes
from it.
**Machine:** AMD Ryzen 5 9600X, 12 logical cores. Load average 2.35 at start,
2.23 at end (§0.1 corollary: *check what else is running before you record a
wall-clock number* — recorded because a wall-clock cross-check appears in §1.5,
and **nowhere else**).
**Selector (§12):** `scripts/scale_split_measure.py` (confirmatory + the five
instrument gates). **Raw:** `results/scale_split.json`.
**Seeds:** block 61000–61999 claimed; **none consumed** (fully deterministic under
fixed indices — verified by the byte-identical determinism gate, §1.1).

---

## 0. THE HEADLINE, IN ONE PARAGRAPH

**The wall is ONE term, not three, and it is not the term either candidate tool
attacks.** On the workload that produced 1.887 and the 164-hour figure, the
counted-operation exponent is **1.955 (r² 0.99992)** — and of the three terms,
**only ONE is superlinear**: comparison/enumeration at exponent **1.980**, against
FFI at **0.998** and positional redundancy at **0.947**. **FFI is LINEAR, and
therefore cannot be the wall at any N** — it is **0.3%** of counted operations at
the largest grid and its share *falls* as N grows. But the dominant term is **not
genuine comparison either**: **99.95% of the candidates enumerated are enumerated
by a global scan whose survival rate is exactly 1/N** (slope **−0.9928**,
r² 1.0000), and **99.81% of all enumeration happens inside a re-scan loop that
re-derives a binding set an earlier call already had**. Reattributing that
cross-epoch redundancy — which the pre-registration required be counted and
reported separately — the split becomes **F 0.3% / C 33.3% / R 66.3%**. **So a
proposal net would be distilling an approximation of work that an index and a
batch-apply flag remove exactly, and an async Rust-resident collapse loop would
be optimising a linear term.** The measured ablation is decisive: with the re-scan
loop out of the path, **the exponent falls from 1.955 to 0.982** — quadratic to
linear, a **138,005×** reduction in projected counted operations at 1080p.

---

## 0.1 ⚠️ I MEASURED THE WRONG WORKLOAD FIRST — found before any share was reported

**My pre-registration §2 contains a contradiction, and it is mine.** It says the
drive is *"`WaveWorld.step()` on the committed `vision_waves` seed — the exact
object `VISION_VIDEO_PROBE_RESULTS.md` §S5 fitted"* AND that *"the confirmatory
counted sweep uses the committed no-frame schedule."* **Those are two different
objects,** because I wrote §2 from a misreading of `video_probe_measure.py`.

What §S5 actually does: it drives **every** tick with a **real frame**, through
`boot_eye`, which loads **`vision_waves` + `vision_lateral`** and turns the
change/sustain channels on. My first cut booted waves-only with no frames and
measured **10 ms/tick at 64²** where the video probe measured **331 ms/tick at
32²** — a ~100× discrepancy in the wrong direction.

**Caught by a cost sanity-check before any share was written, not after.** The
corrected primary arm reproduces the video probe's profile closely:

| grid | video probe §S5 ms/tick | this rung's primary arm |
|---|---|---|
| 12 | 7.76 | 8.6 |
| 16 | 28.28 | 24.2 |
| 24 | 114.53 | 113.8 |
| 32 | 331.61 | 352.0 |

*(Wall-clock, therefore contaminable — used ONLY to establish that the two rungs
are running the same object, never as a share.)*

**Why this matters more than the correction itself.** The pre-registered
waves-only arm has a counted-op exponent of **0.972** — it is **LINEAR**. It is
not the wall at all. Had I reported it as pre-registered, the headline would have
read **F 33.9% / C 60.8% / R 5.2%** and would have named **FFI as a third of the
wall**. **That is exactly the expensive mistake this rung was commissioned to
prevent**, and it was one sanity-check away from being made.

**Both arms are reported below** — the primary because it is the object the claim
is about, the pre-registered arm because it is what I pre-registered. Recorded,
not silently substituted (§5).

---

## 1. THE INSTRUMENT WAS GATED BEFORE THE AGENT (PROTOCOL §1)

**This arc has caught eleven inert instruments.** Five gates, all pre-declared,
all run before any share.

| gate | result |
|---|---|
| **§6.1 zero-when-off** — every counter reads 0 with the audit off, on a LIVE world | **PASS** (no counter moved) |
| **§6.2 known-count** — `wv_refract`/`wv_recover` match `[r, has_cell, c]` both-unbound, and there are EXACTLY h·w `has_cell` edges, so every scan enumeration must be an exact multiple of h·w | **PASS** — 2304 scan candidates at 16², **exactly 9× the 256 `has_cell` edges** |
| **§6.3 determinism** — two independent runs must be BYTE-IDENTICAL | **PASS** (zero differing counters) |
| **§6.4 conservation** — `first+repeat == total` and `scan+local+hinted == total`, asserted per point | **PASS** at every grid, both regimes, all arms |
| **§6.5 audit does not move the exponent** | **PASS** — 0.924 off vs 0.979 on (Δ 0.055 < 0.15). *Wall-clock by necessity, therefore contaminable; reported as a gate, never as a share.* |

### 1.1 AND THE GATES CAUGHT A REAL DEFECT — the instrument was HALF-INERT

**The first build of this instrument reported `rule_enumerations = 0` while
108,110 candidates were enumerated.** The epoch hook was on
`rewrite::run_rules_opts`; the seed-installed rules run through
**`Substrate::run_rules_opts`**, a *different* fixpoint with a semi-naive
incremental matcher. With the hook on the wrong store, **every candidate was
classified as a FIRST enumeration and R was structurally pinned at 0%** — a
clean, plausible, entirely wrong headline.

**It was caught by the conservation check, not by inspection.** A counter reading
zero next to a counter reading 108,110 is only visible if you look at both, which
is what §6.4 forces. This is §12.1's lesson in its own terms: *the instrument is
the highest-risk component,* and an instrument that reports a plausible number
from a path that never runs is the failure mode this project keeps meeting.

### 1.2 WHERE THE RUST-LEVEL GATES COULD NOT RUN — declared, not hidden

`runners/dsl/Cargo.toml` sets pyo3's `extension-module` **unconditionally**, so
`cargo test` cannot link this crate: the `#[cfg(test)]` tests in `scale_audit.rs`
are **unrunnable in this tree**. This is **PRE-EXISTING**, not introduced here.
The gates therefore run in the harness against the **shipped engine** — which is
the stronger place for them, since it tests the binary that actually produced the
numbers (the §10 two-binary hazard is exactly a case where source and artifact
disagreed and both agents reported green). The Rust tests are kept as executable
documentation for whoever adds a no-`extension-module` feature.

### 1.5 THE ONE CONTAMINABLE NUMBER, ISOLATED

Every share, exponent and verdict in this document is a **count**. The only
wall-clock numbers appear in §0.1's workload-identity table and §6.5's gate, both
labelled, both excluded from every share, both recorded with the machine's load
state (2.35 / 2.23 on 12 cores, 3 candidate concurrent processes seen by `ps`).
The counted decomposition **reproduces the wall's scaling independently**:
counted-op exponent **1.955** against the video probe's wall-clock **1.887**, on
the same object. That agreement is the evidence that counting was not a dodge.

---

## 2. THE SPLIT

### 2.1 PRIMARY ARM — assembled eye, frame-driven (the object behind 1.887 and 164 h)

Six grids, 144 → 4096 cells (a **28×** range; the video probe fitted 4 points over
7.1×). 20 ticks after 5 warm-up, liveness gated per point.

| cells | counted ops | **F** | **C** | **R** | scan share | survival |
|---|---|---|---|---|---|---|
| 144 | 1,958,347 | 7.5% | 91.3% | 1.2% | 98.6% | 0.01959 |
| 256 | 5,702,007 | 4.6% | 94.6% | 0.8% | 99.2% | 0.01133 |
| 576 | 27,813,451 | 2.1% | 97.6% | 0.3% | 99.7% | 0.00502 |
| 1024 | 86,509,200 | 1.2% | 98.6% | 0.2% | 99.8% | 0.00283 |
| 2304 | 427,255,115 | 0.5% | 99.4% | 0.1% | 99.9% | 0.00126 |
| **4096** | **1,341,314,626** | **0.3%** | **99.6%** | **0.0%** | **100.0%** | **0.00071** |

### 2.2 THE EXPONENTS ARE THE RESULT — not the shares

A share is a snapshot at one N. **The exponent says what happens as N grows, and
it is the number that selects a tool.**

| term | exponent vs cells | r² |
|---|---|---|
| **total counted ops** | **1.955** | 0.99992 |
| **C — comparison/enumeration** | **1.980** | 0.99998 |
| **F — FFI boundary** | **0.998** | 1.00000 |
| **R — redundancy (positional)** | **0.947** | 0.99713 |
| candidate enumerations | 1.984 | 0.99999 |

**ONLY ONE TERM IS SUPERLINEAR.** F is linear to five decimal places of fit
quality. **This is a bound, not a share: an FFI term at exponent 0.998 cannot
produce a wall at exponent 1.955 at any N.** Removing FFI entirely — a perfect
async Rust-resident collapse loop, the tool that attacks term 1 — would move the
1080p projection by **0.3%** and would not move the exponent at all.

### 2.3 THE POSITIONAL R IS ZERO, AND THAT IS AN HONEST ZERO

The pre-registration predicted R would be the largest term, on the reasoning that
`rewrite::run_rules_opts`'s cold path enumerates every binding, applies one, and
re-enumerates. **That mechanism is real but is NOT on this path.** The
seed-installed rules run through `Substrate::run_rules_opts`, whose **semi-naive
incremental matcher drains every admissible binding in one pass under snapshot
semantics**. Within-epoch re-enumeration is **1.4%** of rule enumerations. **The
engine already does the incremental-reuse job I predicted was missing.**

### 2.4 BUT THE REDUNDANCY IS REAL — it is CROSS-EPOCH, and the prereg required it be found

The pre-registration fixed R as a **positional, within-epoch, deliberately
conservative LOWER BOUND**, and required that cross-epoch re-enumeration be
**counted and reported separately** rather than folded in. That report is the
headline of this section.

`WaveWorld._drive_phase()` runs, per drive rule:

```python
while nat.apply_rule_once(idx):
    pass
```

Each `apply_rule_once` is a fresh Python→Rust entry that **re-derives the binding
set from scratch**. To apply M bindings it performs **M full enumerations**.

| cells | `apply_rule_once` calls (20 ticks) | irreducible floor | redundant fraction | share of ALL enumeration |
|---|---|---|---|---|
| 144 | 7,739 | 100 | 98.708% | 94.93% |
| 256 | 13,517 | 100 | 99.260% | 96.93% |
| 576 | 30,964 | 100 | 99.677% | 98.70% |
| 1024 | 55,049 | 100 | 99.818% | 99.27% |
| 2304 | 122,425 | 100 | 99.918% | 99.67% |
| **4096** | **217,213** | **100** | **99.954%** | **99.81%** |

**The floor is not chosen — it falls out (§13):** one enumeration per drive rule
per tick, i.e. `len(vision_change.rules) × ticks = 5 × 20 = 100`, read from the
seed file. The engine **already has the mechanism that delivers that floor** —
`batch_apply_rule`, selected by a rule's `batch` flag — and **none of the five
`vision_change` rules sets it**.

**The call count grows ∝ N and each call scans ∝ N. N × N is the wall.**
At 4096 cells: 217,213 calls ≈ 2.65·N per tick, each enumerating ≈ N candidates.

### 2.5 THE REATTRIBUTED SPLIT

Moving the cross-epoch redundancy from C to R — **not a re-definition of the
buckets after seeing the numbers (§5, forbidden), but the second report the
pre-registration explicitly required**:

| cells | **F** | **C** | **R** |
|---|---|---|---|
| 144 | 7.5% | 35.1% | 57.4% |
| 1024 | 1.2% | 33.6% | 65.2% |
| **4096** | **0.3%** | **33.3%** | **66.3%** |

**Both splits are reported and neither is hidden.** Positional (as
pre-registered): F 0.3 / C 99.6 / R 0.0. Reattributed (also as pre-registered):
**F 0.3 / C 33.3 / R 66.3**.

### 2.6 THE PRE-REGISTERED ARM — reported in full, and it is a different question

| arm | counted-op exponent | F | C | R (at 4096 cells) |
|---|---|---|---|---|
| **primary: eye, frame-driven** | **1.955** | 0.3% | 99.6% | 0.0% |
| pre-registered: waves-only, `constant`, no frames | **0.972** | 33.9% | 60.8% | 5.2% |
| pre-registered: waves-only, `density`, no frames | **1.028** | 28.4% | 51.3% | 20.3% |
| waves-only, frame-driven | 1.851 | 1.4% | 98.5% | 0.0% |

The waves-only no-frame arms are **linear**. They are not the wall. The
frame-driven waves-only arm recovers most of it (1.851), which localises the
quadratic to **the frame drive path**, not to the lateral seed.

---

## 3. HYPOTHESIS (a) — IS THE O(N²) CENTRALIZATION RATHER THAN COMPARISON?

Pre-registered decision rule, unchanged: **ARCHITECTURAL** iff scan share ≥ 0.50
at the largest grid AND the survival log-slope < −0.5; **COMPUTATIONAL** iff scan
< 0.50 OR slope > −0.2; else INDETERMINATE.

| arm | scan share @ largest grid | survival log-slope | r² | **verdict** |
|---|---|---|---|---|
| **primary (eye, frame-driven)** | **0.9995** | **−0.9928** | 1.0000 | **ARCHITECTURAL** |
| pre-registered (waves-only, no frames) | 0.9787 | −0.3787 | 0.9968 | **INDETERMINATE** |

**Both verdicts are reported. The primary arm is the one the 164-hour claim is
about; the pre-registered arm lands INDETERMINATE and is not rounded into the
convenient answer (§5).**

**The slope is −0.9928, which is −1 to within 0.7%, and NOBODY SET IT.** A slope
of exactly −1 means: **the number of surviving candidates is CONSTANT while the
number enumerated grows ∝ N.** That is the precise signature of
*global-by-construction*. At 4096 cells the survival rate is **0.00071** — **99.93%
of every candidate enumerated could never plausibly have won**, and the fraction
that could gets *smaller* with every added cell.

**The mechanism, read off the rules rather than inferred:** `wv_refract`,
`wv_recover` and the five `ch_*` drive rules all match `[r, has_cell, c]` with
**both variables unbound**. `extend_each`'s `(None, None)` arm therefore falls to
a **full scan of every `has_cell` edge** — all N of them — to find the handful of
cells in the matching state. There is exactly one `Retina` hub, so `has_cell` is
a **star**: every rule that starts from it starts from the whole field.

**THE VERDICT: the wall is ARCHITECTURAL, not computational.** The comparisons
being counted are not comparisons anyone needs; they are the cost of reaching
every candidate through one global hub. **A proposal net would be learning to
approximate a filter that a locality index computes exactly.**

---

## 4. HYPOTHESIS (b) — IS 164 h A UNIFORM-GRID NUMBER?

Pre-registered decision rule, unchanged: **CHANGES** iff the counted-op exponent
at `fovea_radius=4` is ≥ 0.30 below the `radius=0` exponent with both r² ≥ 0.95;
**DOES NOT CHANGE** iff |difference| < 0.15; else INDETERMINATE.

| arm | counted-op exponent | r² | ops @ 4096 cells |
|---|---|---|---|
| `fovea_radius=0` | **1.9549** | 0.99992 | 1,341,314,626 |
| `fovea_radius=4` | **0.9820** | 0.99992 | 4,103,028 |
| `fovea_radius=8` | 0.9761 | 0.99991 | 4,109,969 |

**Drop = 0.973. Pre-registered verdict: FOVEATION CHANGES THE SCALING.**
**My prediction was WRONG**, and I predicted the null branch with a declared
structural reason.

### 4.1 BUT THE MECHANISM IS NOT FOVEAL ALLOCATION — and the arm's own control proves it

**The verdict is right by the pre-registered rule and wrong about why, and saying
so is the finding.** Two measurements make this unambiguous:

1. **`radius=4` and `radius=8` enumerate a BYTE-IDENTICAL number of candidates** —
   109,694 (16²), 234,830 (24²), 416,472 (32²) — despite the aperture having **4×
   the area**. If the saving came from looking at a smaller region, quadrupling
   the region would cost more. It costs **0.2% more**.
2. **Epochs per tick collapse from 2,753 to exactly 1.0** at 32².

The cause is structural, in `wave_world.py::drive()`: the `rad <= 0` branch writes
`lum_raw`/`lum_prev`/`lum_seen` per cell and then calls `self._drive_phase()`; the
`rad > 0` branch writes **only** `driven` and **never calls `_drive_phase()` at
all**. **The fovea arm is not a narrower aperture — it is a different code path
that skips the entire drive-phase re-scan loop.**

So this arm does **not** test salience-weighted allocation. **It is an
unintentional but valid ABLATION CONTROL for §2.4**, and as that it is the
strongest evidence in this document:

> **Remove the `while apply_rule_once` re-scan loop and the counted-op exponent
> falls from 1.955 to 0.982 — quadratic to linear. Measured, not projected.**

**The honest status of hypothesis (b): NOT TESTED.** Whether foveal allocation
changes the scaling remains open, because the tree contains no implementation of
it that leaves the drive phase intact. **The architecture's own commitment —
foveation, grounding that decays with eccentricity, compute ∝ surprise — is not
wired into the term that scales.** That is a named gap between what the
architecture says and what the code does, and it is the correct output of this
arm.

### 4.2 THE RE-PROJECTION — labelled COUNTERFACTUAL throughout

Projected **counted operations** (not seconds), from the two measured fits:

| field | cells | uniform (exp 1.955) | drive-phase ablated (exp 0.982) | ratio |
|---|---|---|---|---|
| 64×64 *(measured)* | 4,096 | 1.316×10⁹ | 4.077×10⁶ | 323× |
| 320×240 QVGA | 76,800 | 4.052×10¹¹ | 7.251×10⁷ | 5,589× |
| **1920×1080** | **2,073,600** | **2.546×10¹⁴** | **1.845×10⁹** | **138,005×** |

**Every caveat that applied to the 164-hour figure applies here and one more.**
The 1080p row is **3 orders of magnitude beyond the measured range** (144–4096
cells) and assumes the exponent holds. **And the ratio is in COUNTED OPERATIONS,
not time** — translating 164 h ÷ 138,005 ≈ **4.3 s** assumes operations cost
uniform time, which **is not measured here and is not true in general** (a PyO3
crossing and a where-evaluation are both "one operation" and cost wildly
different amounts). Quote the ratio; do not quote the seconds without this
sentence attached.

---

## 5. WHAT TOOL THE EVIDENCE SELECTS

The rung was commissioned to answer exactly this, and the answer is lopsided —
**which the pre-registration named as the most actionable possible outcome (§7).**

| tool | term it attacks | **verdict** |
|---|---|---|
| async Rust-resident collapse loop | **F** | **DO NOT BUILD FOR SCALE.** F is 0.3% of ops and **exponent 0.998 — linear**. Perfect removal moves the 1080p projection by 0.3% and moves the exponent by nothing. *(It may still be worth building for latency or concurrency; this rung says only that it is not the wall.)* |
| **proposal net / distillation** | **C** | **DO NOT BUILD YET.** C is 99.6% positional — but 99.95% of it is global-scan enumeration at 1/N survival (§3), and 99.81% is cross-epoch re-scan (§2.4). **A net would be distilling an approximation of work that an index and a flag remove exactly.** |
| **batch-apply the drive rules** | **R** | **BUILD FIRST.** The engine already has `batch_apply_rule`; the five `vision_change` rules do not set `batch`. The ablation measures the payoff: **exponent 1.955 → 0.982**. |
| **a locality index on the star-scan path** | **C, exactly** | **BUILD SECOND.** Survival is 1/N; the `R10 IndexJoinHint` machinery exists and is used **0%** on this path (`cand_enum_hinted = 0` at every grid). |

**The expensive mistake the rung existed to prevent is confirmed as a live risk
and avoided:** the tool the evidence rejects most strongly (distillation) is the
one the largest raw share (C = 99.6%) appears to endorse, and it takes the
survival slope and the cross-epoch counter to see that it should not.

---

## 6. MY PREDICTIONS, SCORED (PROTOCOL §3.7)

| # | prediction | outcome |
|---|---|---|
| 1 | **R is the largest term, > 50%** | **HALF WRONG.** Positional R = **0.0%** — WRONG, and my named mechanism (`rewrite::run_rules_opts`'s cold path) is **not on this path**; the semi-naive matcher already does the within-epoch job. Reattributed R = **66.3%** — right, but by a mechanism I had excluded from R *by my own conservative choice*. My stated proviso ("if the fixpoint terminates in few passes, R stays small and the quadratic comes from somewhere I have not identified") is **exactly what happened**, and the "somewhere" was the adapter loop. |
| 2 | **F smallest at large N, < 20%** | **RIGHT**, and by far — **0.3%**, exponent 0.998. **But its proviso is WRONG**: I predicted F would be *materially larger* frame-driven. Frame-driven is where F is **smallest**, because the drive phase multiplies the non-FFI terms. |
| 3 | **(a) ARCHITECTURAL, scan > 0.9** | **RIGHT** on the primary arm (0.9995, slope −0.9928). **INDETERMINATE** on the pre-registered arm, reported as such. |
| 4 | **(b) FOVEATION DOES NOT CHANGE THE SCALING** | **WRONG** by the pre-registered rule (drop 0.973). My declared structural reason (node count unchanged ⇒ enumeration unchanged) was **right about node count and wrong about the conclusion**, because I had not seen that `rad > 0` takes a different code path. |
| 5 | **Tool = foveated/incremental, not distillation** | **RIGHT on the conclusion, wrong on the parts.** "Not distillation" holds. But "incremental" already exists in the engine, and what is actually missing is **batch-apply + a locality index**. |

**Three of five wrong or half-wrong.** The two that mattered most for the
decision — F is not the wall, distillation is not the tool — were right.

---

## 7. BOUNDS ON EVERYTHING ABOVE (§8)

- **ONE workload.** The retina drive (`WaveWorld.step` on `vision_waves` +
  `vision_lateral`). **The identity / sd-loop layer is NOT measured** — it is a
  different workload with a different profile, and nothing here generalises to it.
  The 164-hour figure came from the retina drive, so the retina drive is what was
  split.
- **Synthetic frames, not video.** The drive uses a smooth drifting random field,
  not decoded video. Per-cell cost is content-independent on this path (the video
  probe established this), but that is an inherited claim, not one re-measured
  here.
- **The projections are extrapolations,** 3 orders of magnitude beyond the
  measured 144–4096 cell range, and they are in **counted operations, not
  seconds** (§4.2). The measured range is what is measured.
- **Hypothesis (b) is NOT TESTED.** Its arm is a code-path ablation, not a
  foveation test (§4.1). No claim is made here about salience-weighted allocation.
- **R is a LOWER BOUND positionally and the reattribution is a SEPARATE report,**
  exactly as pre-registered. The reattribution charges only **candidate
  enumeration** in `apply_rule_once` epochs — not the where-evaluations in those
  epochs — so it too understates R. The direction is consistent throughout.
- **Operation counts are not interchangeable units of time,** and no share here
  should be read as a share of seconds. The only evidence that the counted
  decomposition tracks time is the exponent agreement (1.955 counted vs 1.887
  wall) — which is agreement in *scaling*, not in *cost per operation*.
- **`cand_enum_hinted = 0` everywhere** means the R10 index path was never
  exercised; the "indexed" share is an untested branch of the (a) statistic, not a
  measured zero-benefit finding.
- **The known-count gate proves the scan counter exact; it does not prove the FFI
  counters exact.** F's per-object counts (`2 + attrs.len()` for `node()`) are
  a MODEL of marshalling cost, declared in the prereg, not a measurement of it.
  F's *exponent* is robust to that model; F's *share* is not, to within a small
  constant factor. Since F is 0.3%, no plausible constant changes the verdict.
- **§9:** no default moved, no seed edited, no rule added. The Rust added is an
  instrument, **DEFAULT OFF**, asserted against the shipped binary by the
  provenance gate.

---

## 8. THE REGRESSION ORACLE

| selector | result | exit |
|---|---|---|
| `bash scripts/rung7_vision_bench.sh` (with `data/` symlinked, §10.2) | **200 passed, 0 failed, 0 skipped** in 139 s | **0** |
| the same, **without** `data/` — recorded because it is the trap | 190 passed, 10 skipped | 0 |
| `tests/test_sdloop_vision_migrated.py` — the **sd orbit law** `{2:1, 3:2, 4:2, 6:2, 12:4}` | **8 passed**, law **unmoved** | **0** |

The 200/0 figure confirms the `data/` symlink is live and the 10 BSDS-gated tests
actually ran rather than silently skipping — §10.2's "5% vacuous and does not
know it" defect, checked rather than assumed.

**This is the load-bearing §9 check for this rung specifically**, because unlike
every recent instrument rung **this one ships Rust into the engine every other
rung runs on**. 200/0 on an engine carrying the audit — with the audit off — is
the evidence that the default is genuinely inert.

---

## 9. WHAT THE NEXT RUNG SHOULD DO

**This is a BUILD TASK, not a hypothesis.** The standing directive is that engine
limits are build tasks; this rung's job was to say *which* build, and the evidence
names it without ambiguity.

1. **Set `batch: true` on the five `vision_change` rules and re-measure.** The
   mechanism exists (`batch_apply_rule`), the ablation predicts **exponent
   1.955 → ~0.98**, and the prediction is falsifiable in one sweep. **Note the
   §9 hazard: `batch` changes firing order, so byte-identity of committed results
   must be checked, not assumed** — that check is the actual work.
2. **Give the star-scan path a locality index.** Survival is 1/N; the
   `IndexJoinHint` machinery exists and is unused here (`cand_enum_hinted = 0`).
3. **Do NOT distil a proposal net for this wall,** and do not build an async
   collapse loop *for scale*. Both remain open for other reasons; neither is this
   term.
4. **Wire foveation to the drive phase, then re-run hypothesis (b) properly.**
   Right now `fovea_radius > 0` bypasses the change channels entirely, so the
   architecture's salience commitment is untestable on this path.
