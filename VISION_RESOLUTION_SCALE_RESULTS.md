# SCALE THE EYE'S RESOLUTION — RESULTS

*Pre-registration: `VISION_RESOLUTION_SCALE_PREREG.md`, committed BEFORE any
headline number at **`1fa4fe6d7f44b69980ad198cbac439ea284446aa`** (base
**`6b50b97ab3ff49980de6a0704867b578aaac923d`**). Both endpoints pinned; no
range ends at `HEAD`.*

**Branch:** `worktree-agent-a894edf46d0235e74` — the intended
`gamma-substrate/resolution-scale` was **NOT provisioned**, and I report the
branch I actually see. **Sixth rung in a row under an auto-generated name.**

**Engine (§10):** **`d6097900e8b5`**, built with `scripts/engine_build.sh`
(never a bare `cargo build`). This tree's Rust source is byte-identical to
canonical (`diff -rq runners/dsl/src` reports only the untracked, uncompiled
`py.rs.selfmod.bak`). **This rung adds NO Rust, NO Term, NO seed rule and NO
constant** — `git diff 6b50b97a -- runners/dsl/src seeds` is empty.
**The provenance gate was run as its own step before any number:**
`test_engine_provenance_migrated.py` + `test_provenance_endpoint_guard_migrated.py`
→ **633 passed, exit 0**.
**Oracle:** `bash scripts/rung7_vision_bench.sh` → **222 passed, exit 0**, run
BOTH before the adapter fix and after it.
**Machine:** AMD Ryzen 5 9600X, 12 logical cores. **A concurrent rung ran
throughout**; load is reported beside every wall-clock number and the
load-independent counted cost is reported alongside.
**Selectors (§12):** `scripts/resolution_scale_measure.py` (confirmatory) ·
`scripts/resolution_scale_analyse.py` (the pre-registered decision rule,
applied mechanically — every published value below is printed by it) ·
`tests/test_resolution_scale_migrated.py` (9 gates, two positive-controlled).
**Raw:** `results/resolution_scale_all.json` + `results/resolution_scale_analysis_all.json`,
committed. The ten per-row files total 75 MB and are **NOT committed** (the two
S72 files are 21 MB each, over the 10 MB limit); **every row file's SHA256 is
recorded in `resolution_scale_all.json`**, following the verdict rung's
precedent.
**Seeds:** block **79000–79999** claimed. **Consumed, audited from the source
rather than asserted** (`SEED_BLOCK = 79000`; the draws are
`SEED_BLOCK+200+t`, `SEED_BLOCK+400+t`, and the two noise offsets
`SEED_BLOCK+700+t` / `SEED_BLOCK+800+t`, t = 0..49):

| consumed | what |
|---|---|
| **79200–79249** | per-base-frame probe seed |
| **79400–79449** | probe-selection RNG |
| **79700–79749** | G2c calibration-noise draw |
| **79800–79849** | G2t test-noise draw |

**Returned intact: 79000–79199, 79250–79399, 79450–79699, 79750–79799,
79850–79999.** The scoping pilot drew **70000 only**, already burned by
`VISION_VERDICT_RESULTS.md` (§3.3). The concurrent rung's **78000–78999 was not
touched.**

**A pre-registration error this audit caught:** prereg 2.1 sub-allocated
**79200–79399 to the K arm**, which **overlaps the 79200–79249 this rung
actually consumed.** The K arm was not run (§7), so nothing was double-drawn —
but had it run as allocated it would have reused 50 seeds. **The K arm must be
re-allocated to a clean sub-range before it is ever run.** My first statement of
this section claimed "79000–79199 consumed", which was wrong in both directions;
the table above is read off the source.

---

## 0. THE HEADLINE, IN ONE PARAGRAPH

**The statistical motivation for scaling this eye is REFUTED, and the refutation
is mechanistic rather than merely null.** Scaling the region count 16 → 64 → 144
does **not** raise effective n on either corpus; on **C2 (live-action), the
corpus with room to vary, it FALLS monotonically — n_eff 16.69 → 12.67 →
11.17** at the frame level. Tested where the hypothesis actually lives, at the
**region** level, the result is sharper still: **9× the raw observations (784 →
7056) yields 43% of the effective information (n_eff 569.7 → 245.9)**, because
the region-level ICC **RISES** with scale (0.0251 → 0.1182 → **0.1937**).
**Adding regions does not add independent samples; it adds more samples that
share their frame's content, and they get MORE correlated as they get
smaller.** The representational side fails with it: on C2 recognition
**collapses −0.3581 [−0.4165, −0.2998]** at 144 regions, and it costs **42×**
the graph time to do it. **The other axis is the one that works.** Holding the
region count at 16 and making each region cover more image (GRAIN) **does not
degrade recognition on either corpus and improves it on both** (C1 **+0.0195
[+0.0032, +0.0359]**, C2 **+0.0102 [+0.0017, +0.0187]**, both CI-separated) for
**2.9×** the cost. **The two axes point in opposite directions, which is the
whole reason the pre-registration refused to let them be varied together.**
**Five things I got wrong or nearly did, all reported as findings.** (1) **G1
FAILED** — graph/reference agreement is 0.9997 on C1|S72, not the pre-registered
1.0000. (2) **My P2 and P4 are both REFUTED**, P4 in the direction I did not
consider. (3) **A latent read-back defect** in the shared adapter would have
silently corrupted every 144-region number, and it is invisible below 100
regions. (4) **I ran the confirmatory measurement twice concurrently by
accident** and had to discard it (§8.2). (5) **I mis-stated my own seed
consumption**, and auditing it from the source found that the
pre-registration's K-arm allocation **collides with seeds this rung consumed**
(§8.3).

---

## 1. WHAT WAS MEASURED

Five configurations, two axes sharing one origin, **never conflated**
(prereg 2.1). `GRID` is the size the corpus is decoded to, so a larger `GRID` is
genuinely more of the source video, not an upsample.

| id | GRID | REGION | n_regions | cells/region | chance | axis |
|---|---|---|---|---|---|---|
| **B** | 24 | 6 | 16 | 36 | 0.0625 | origin of both — the re-earned baseline |
| **S48** | 48 | 6 | 64 | 36 | 0.0156 | SCALE |
| **S72** | 72 | 6 | 144 | 36 | 0.0069 | SCALE |
| **G48** | 48 | 12 | 16 | 144 | 0.0625 | GRAIN |
| **G72** | 72 | 18 | 16 | 324 | 0.0625 | GRAIN |

**Corpora, reported per corpus and never pooled:** C1 cartoon (pin
`08630d4b…`), C2 live-action (pin `119eca43…`), both pin-checked at run time.
50 base frames each, 5 contiguous blocks of 10 (the K-scope block structure, so
the decomposition is directly comparable). Verdict fixed at **NCC**, ρ = 2,
K_LEVELS = 4 — all three **inherited and named as inherited**. Primary is
`true_achieves_max` on `A1|d1` non-cut trials, which is computed from the
reference and therefore **does not pass through the defective parser** of §8.1.

**Nothing was inherited that could move.** Motion, the Otsu cut partition and
the refusal floor were **re-measured at every configuration** (prereg 1.1). The
floor moved a great deal and is reported in §5.

---

## 2. G1 — THE PIPELINE RUNS. **FAILS ON ITS OWN THRESHOLD, AND THE FAILURE IS DIAGNOSED**

The pipeline runs retina → identity at **all five configurations on both
corpora** — 10/10 cells completed, 179,200 rows. But the gate was stated as
*graph/reference agreement = 1.0000*, and one cell misses it:

| | B | S48 | S72 | G48 | G72 |
|---|---|---|---|---|---|
| C1 | 1.0000 | 1.0000 | **0.9997** | 1.0000 | 1.0000 |
| C2 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

**G1 FAILS as written.** The cause, diagnosed rather than waved at: **14 rows
out of 50,400 (0.028%), all on C1|S72, all at an exact NCC score of 1.0.**
`graph_max` reads `1.0000000000000002` on 9 of the 14 — a **1-ulp difference
from summing the same `Dot` in a different order**, on candidates that are
*genuinely tied* at perfect correlation. The graph and the reference then break
that tie by different orders (seeded insertion vs index).

**This is NCC's declared affine invariance doing exactly what was declared.**
Two cel-shaded tiles differing only by gain and bias correlate at exactly 1.0,
so they are *the same thing* to this verdict. The rate of perfect-correlation
maxima rises with region count on C1 and is **zero everywhere on C2**:

| P(ref_max == 1.0) | B | S48 | S72 |
|---|---|---|---|
| C1 (cartoon) | 0.0039 | 0.0293 | **0.0728** |
| C2 (live-action) | 0.0000 | 0.0000 | 0.0000 |

**What breaks first, asked and answered:** at fine grain on cel-shaded content
the codebook starts containing **entries the verdict cannot distinguish even in
principle**. That is a property of the corpus × verdict pair, not a defect in
the engine. **It does not touch the primary** — `true_is_max` is 1.0 for both
members of a tie either way — and it is confined to 0.028% of one cell. **But
the gate said 1.0000, and it is reported FAILED rather than rounded.**

---

## 3. G2 — THE EFFECTIVE-N GATE. **REFUTED.** THIS IS THE RESULT

### 3.1 Frame level — the pre-registered decomposition

n_eff = n / (1 + (m−1)·ICC), n = 50, m = 10, 5 blocks.

| C1 | ICC | **n_eff** | spread ratio | sd | frac@ceiling |
|---|---|---|---|---|---|
| B (16) | 0.2930 | **13.20** | 5.13 | 0.0616 | 0.812 |
| S48 (64) | 0.2841 | **13.49** | 4.96 | 0.0504 | 0.396 |
| S72 (144) | 0.3806 | **10.85** | 7.13 | 0.0730 | 0.375 |
| G48 | 0.1662 | 19.23 | 2.99 | 0.0386 | 0.875 |
| G72 | 0.0839 | 27.35 | 1.91 | 0.0232 | 0.917 |

| C2 | ICC | **n_eff** | spread ratio | sd | frac@ceiling |
|---|---|---|---|---|---|
| B (16) | 0.2151 | **16.69** | 3.74 | 0.0295 | 0.878 |
| S48 (64) | 0.3187 | **12.67** | 5.68 | 0.1330 | 0.122 |
| S72 (144) | 0.3761 | **11.17** | 7.03 | 0.2158 | 0.000 |
| G48 | 0.1462 | 21.16 | 2.71 | 0.0295 | 0.878 |
| G72 | — | — | ∞ | 0.0000 | **1.000 SATURATED** |

**The pre-registered rule — "n_eff rises along the SCALE axis on BOTH corpora,
or the statistical motivation is REFUTED" — returns REFUTED.** C1 is
non-monotone (13.20 → 13.49 → 10.85); **C2 falls monotonically** (16.69 → 12.67
→ 11.17). **The rule is applied exactly as written and the verdict stands.**

**The C2 scale arm is the trustworthy one and it is the one that falls.** It is
the only scale arm free of the ceiling: sd rises 0.0295 → 0.2158 and
`frac@ceiling` falls 0.878 → **0.000**, so at S72 the measure has full room to
vary and still yields less effective n. C1's scale arm is partly ceiling-bound
(frac@ceiling 0.375–0.812) and I do not lean on it.

### 3.2 Region level — where the hypothesis actually lives. **THE MECHANISM**

The motivating claim is about *regions per frame*, so it is tested at the region
level, clustering on the frame (added to the committed analysis, not computed ad
hoc):

| C2 | regions/frame | N observations | ICC_region | n_eff total | **n_eff PER FRAME** |
|---|---|---|---|---|---|
| B | 16 | 784 | 0.0251 | 569.7 | **11.63** |
| S48 | 64 | 3136 | 0.1182 | 371.2 | **7.57** |
| S72 | 144 | 7056 | **0.1937** | **245.9** | **5.02** |

**This is the finding stated as sharply as the data allows: on C2, nine times
the observations carry 43% of the information.** The regions do not become
independent as they multiply — they become **more** correlated (ICC 0.0251 →
0.1937), because a smaller tile is less distinctive and its fate is
increasingly determined by the shot it sits in rather than by its own content.
**A 24×24 frame carrying 16 regions contributes more effective independent
information (11.63) than a 72×72 frame carrying 144 (5.02).**

C1 is non-monotone here too (6.70 → 11.58 → 7.86) — **the corpora disagree, for
the sixth time in this line**, and the disagreement is reported rather than
resolved by pooling.

### 3.3 What this does NOT license

**The grain axis appears to raise n_eff (C1 13.20 → 19.23 → 27.35; region level
6.70 → 8.65 → 12.03) and I am NOT claiming it.** Those configurations are at or
near the ceiling — C1|G72 has 91.7% of frames at exactly 1.0 and C2|G72 is
**fully saturated** — so their per-frame variance is nearly degenerate and their
ICC is compression, not independence. **The saturation diagnostic was committed
at `ab3b7a9e` BEFORE these numbers existed**, precisely so this reading could
not be made post hoc. **The honest statement is that the grain axis's effect on
effective n is UNMEASURED here, because the primary has no room to move.**

---

## 4. G3 — RECOGNITION. **THE GRAIN AXIS PASSES; THE SCALE AXIS FAILS ON C2**

Paired per-frame deltas against the **re-earned** B baseline measured in this
same run under this same engine.

**GRAIN — n_regions fixed at 16, chance fixed, raw directly comparable. This is
where the verdict is binding (prereg 3).**

| | primary | paired Δ vs B | verdict |
|---|---|---|---|
| C1 G48 | 0.9870 | **+0.0130 [+0.0032, +0.0229]** | no degrade |
| C1 G72 | 0.9935 | **+0.0195 [+0.0032, +0.0359]** | no degrade |
| C2 G48 | 0.9898 | +0.0000 [−0.0052, +0.0052] | not separated |
| C2 G72 | 1.0000 | **+0.0102 [+0.0017, +0.0187]** | no degrade |

**G3 PASSES on the binding axis, and three of four contrasts IMPROVE with
CI separation.** Making each region cover more image helps.

**SCALE — the candidate set grows 16 → 64 → 144, so a raw fall is expected from
task difficulty alone. This comparison is NOT apples-to-apples and is labelled
so (prereg 3); no pass is claimed from the chance-corrected number.**

| | primary | chance | paired Δ vs B | verdict |
|---|---|---|---|---|
| C1 S48 | 0.9697 | 0.0156 | −0.0042 [−0.0159, +0.0075] | not separated |
| C1 S72 | 0.9563 | 0.0069 | **−0.0177 [−0.0307, −0.0046]** | DEGRADES |
| C2 S48 | 0.8412 | 0.0156 | **−0.1486 [−0.1821, −0.1151]** | DEGRADES |
| C2 S72 | 0.6317 | 0.0069 | **−0.3581 [−0.4165, −0.2998]** | DEGRADES |

**On C2 the collapse is enormous and cannot be explained away by chance
correction** — the chance-corrected primary falls 0.9891 → 0.6291 while chance
itself falls 9×, so the arm is losing real discriminability, not merely facing a
larger field. **The corpora disagree in magnitude by 20×** (C1 −0.0177 vs C2
−0.3581): cartoon tiles stay separable at fine grain, photographic ones do not.

---

## 5. THE FLOOR MOVED, EXACTLY AS THE PRE-REGISTRATION INSISTED IT WOULD

Nothing was inherited. The re-measured refusal floor is **not close to constant
across resolution** — it varies by **3.6×** across the five configurations:

| floor | B | S48 | S72 | G48 | G72 |
|---|---|---|---|---|---|
| C1 | 0.6728 | 0.7119 | 0.7622 | 0.3289 | **0.2125** |
| C2 | 0.6368 | 0.7141 | 0.7447 | 0.3293 | **0.2135** |

**The two axes move it in OPPOSITE directions**: more regions raises the floor
(more codebook entries → a better chance that noise correlates with one of
them), while bigger regions **lower it sharply** (a 324-cell tile is far harder
for noise to match). **Any rung that had inherited the 24×24 floor to a grain
configuration would have been wrong by a factor of three.** The refusal control
holds throughout — G2t refusal is 0.93–0.99 everywhere and A1 refusal stays
≤0.025 — so the abstention is functioning at every resolution.

---

## 6. G4 — COST. **BOTH AXES ARE SUB-POLYNOMIAL, AND THEY ARE NOT CLOSE**

Counted cost (`n_regions² × 25 × cells`, load-independent) beside measured graph
time. C1 and C2 agree to within 3%, as geometry-determined cost should.

| cfg | regions | cells | cell-comparisons/probe | graph ms/frame | × B |
|---|---|---|---|---|---|
| B | 16 | 36 | 230,400 | 33.3 / 32.0 | 1.0 |
| S48 | 64 | 36 | 3,686,400 | 307.8 / 303.3 | **9.2 / 9.5** |
| S72 | 144 | 36 | 18,662,400 | 1368.9 / 1351.8 | **41.1 / 42.3** |
| G48 | 16 | 144 | 921,600 | 56.7 / 59.0 | **1.7 / 1.8** |
| G72 | 16 | 324 | 2,073,600 | 97.3 / 91.4 | **2.9 / 2.9** |

**The grain axis buys 9× the cells for 2.9× the time; the scale axis buys 9× the
regions for 42× the time.** Per unit of representation added, **grain is ~14×
cheaper than scale** — and it is the axis that also improves recognition.

**P4 is REFUTED in a direction I did not consider.** I predicted scale ≈
quadratic in region count and grain ≈ linear in cells. Both are **sub**: against
counted comparisons growing 81×, graph time grows 41× (exponent ≈ 0.85 in
comparisons); against 9×, grain grows 2.9× (exponent ≈ 0.48). **Cost per
comparison FALLS as the work per node grows**, which is the batch-apply
regime — the engine is more efficient the more it is given at once.

**The binding cost in this harness is NOT the graph.** At S72 the graph takes
68 s per corpus and the out-of-graph Python reference read-back takes **710 s —
10.4×**. That is a statement about **this harness's verification path**, not
about the identity layer: the reference recomputes every candidate score twice
in pure Python specifically so the graph cannot be trusted on its own word. **A
concurrent rung is anatomising the identity coefficient directly and its number,
not mine, is the authority on that layer.**

---

## 7. THE K ARM — BUILT, PRE-REGISTERED, **NOT RUN**

§4 of the pre-registration (perceived resolution as a function of the CODEBOOK
rather than the SENSOR) was designed with both known confounds controlled —
nested-prefix truncation of one growth run for *K is a draw*, and a fixed
criterion alongside the per-K floor for *a grown codebook raises its own floor*.
`scripts/resolution_k_arm.py` and `scripts/resolution_k_analyse.py` are
committed and the read-outs are defined. **It was not run.** Its pre-registered
seed range **79200–79399 collides with the 79200–79249 this rung consumed** and
must be re-allocated before any future run (see the provenance block). It is
named here as reachable-but-unreached
rather than quietly dropped. **Nothing in this document depends on it**, and the
firewall in prereg 4.3 stands: it would not have licensed any change to §3.

---

## 8. WHAT I GOT WRONG

### 8.1 A latent read-back defect that would have corrupted every 144-region number

`verdict_comparator_world.read()` parsed the region name with a **fixed 2-digit
field**. At 144 regions `r143` parsed as region **14**, and the *answer* parse
was worse — it required `len == 3` exactly, so **every** 3-digit answer returned
`None`, i.e. "no answer" for an entire run. **It is invisible below 100 regions
and no previous rung could have hit it.** Found in scoping, **declared in the
pre-registration before measuring**, fixed with a width that is a function of
codebook size — **byte-identical below 100 entries**, so no landed number can
move. Oracle re-run after the fix: **222 passed, exit 0**. The gate is
positive-controlled: it asserts the old parse was *wrong* on the same input the
new one gets right.

**And the gate then corrected the pre-registration.** The prose said the parse
breaks at "≥100 regions". It breaks at **>100** — a 100-region codebook is
indexed 0..99 and is safe. Recorded at `523806e5` rather than quietly amended.

### 8.2 I ran the confirmatory measurement twice, concurrently, by accident

My first launch used `nohup … &` inside a backgrounded call. The wrapper
returned **exit 0**, which I read as the child having died. **It had not** — it
kept running, and my relaunch put **two processes on the same output files**.
Caught by inspecting `ps`, not by the exit code. Both were killed, all partial
outputs deleted, and the run restarted as a single verified instance; **every
number in this document comes from that single clean run.** This is the standing
"a redirect target is not evidence that the command ran" lesson in its converse
form: **an exit code from a launcher is not evidence that the work stopped.** A
`pgrep` guard I then added **self-matched its own shell command line** and
refused to start — which is why it is not in the final launch path.

### 8.3 I mis-stated my own seed consumption, and the audit caught a collision

My first draft of the provenance block claimed "79000–79199 consumed,
79200–79999 returned intact". **Both halves were wrong.** Read off the source,
the draws are four scattered sub-ranges (**79200–79249, 79400–79449,
79700–79749, 79800–79849**) and 79000–79199 was never touched. **The audit also
found that the pre-registration allocated 79200–79399 to the K arm — overlapping
seeds this rung actually consumed.** The K arm was not run so nothing was
double-drawn, but the allocation was latently broken from the moment it was
written. **Seed ranges must be audited from the source, not from the constant at
the top of the file** — `SEED_BLOCK + 700 + t` does not live in the range a
reader assumes from `SEED_BLOCK = 79000`.

### 8.4 My predictions

* **P1 (pipeline runs at all five) — HELD**, with G1's 0.028% tie caveat (§2).
* **P2 (n_eff rises on the scale axis) — REFUTED.** This was the rung's
  motivating hypothesis and it is dead in the direction opposite to the one
  predicted (§3).
* **P3 (raw falls on scale, not on grain) — HELD**, and stronger than predicted:
  grain does not merely hold, it improves with CI separation (§4).
* **P4 (scale ≈ quadratic, grain ≈ linear) — REFUTED**, both sub-polynomial
  (§6).
* **P5 (K arm) — NOT TESTED** (§7).

### 8.5 A correction I received and did NOT act on, deliberately

Mid-run I was told the identity-layer cost figure that motivated the brief
(698 µs/cell) is **stale — the anatomy rung measures ~94 µs/cell, ~7× cheaper**.
It arrived after the ladder was fixed and measurement had started, so per §3/§5
**I did not re-scope**, and I record it here instead. **It would not have
changed the ladder:** I scoped 24/48/72 from my own pilot, which already showed
the graph cheap at 144 regions (0.18 s) and the **Python reference read-back**
binding. The honest consequence is in §9 — resolutions above 72 were reachable
and I did not reach them, and what stopped me was my verification path, not the
engine.

---

## 9. BOUNDS

* **Two corpora, both video, both from one Jellyfin catalogue.** No photo
  corpus, no third domain. **They disagreed again** — by 20× on the scale-axis
  recognition collapse and in sign on region-level n_eff. Nothing is pooled.
* **`GRID` reached 72 and no further.** 1080p was out of scope and remains
  untouched. **Resolutions above 72 were reachable and were not reached**; the
  binding constraint was this harness's O(n_regions²) pure-Python reference
  read-back (710 s at S72), **not** the graph (68 s) and not the engine.
* **ρ = 2 was held in PIXELS across both axes**, declared in advance as a
  limitation of the grain arm: at REGION = 18 the orbit covers a much smaller
  fraction of the tile than at REGION = 6. **The grain axis's advantage is
  therefore measured under a translation tolerance that is relatively tighter
  for it**, which if anything understates it.
* **The verdict was fixed at NCC.** No verdict × resolution interaction was
  measured and none is claimed — though §2 shows NCC's affine invariance
  starting to bind on cartoon at 144 regions, so that interaction is real and
  unmeasured.
* **n_eff is estimated from 5 blocks.** Five is few and the estimate is coarse;
  this was stated in advance rather than discovered afterwards.
* **The grain axis's effect on effective n is UNMEASURED** because the primary
  saturates there (§3.3). Testing it needs a harder read-out, not a finer grid.
* **Proto-objects and object-level salience remain named-not-built.** This rung
  measured whether the grain to express them is affordable — it is, at 2.9× —
  but it did not look for them.

---

## 10. WHAT THIS LINE SHOULD DO NEXT

Stated as a consequence of the measurement, not as a plan this rung is
authorised to execute.

1. **Stop buying resolution by adding regions.** It costs 42×, degrades
   recognition up to −0.36, and *reduces* effective n. The scale axis is
   measured and it is a dead end on this corpus pair.
2. **The grain axis is the affordable one** — 2.9× for 9× the cells, with
   recognition improving. The salience re-score's binding complaint was that a
   4×4 grid of 6×6 tiles cannot express object-level salience; **a 4×4 grid of
   18×18 tiles is now known to cost 2.9× and to lose nothing**, which is the
   configuration a proto-object probe should use.
3. **The frame is the unit, and 5 effective frames is the budget.** Every
   future CI on this corpus pair should be block-bootstrapped; the region count
   does not rescue it, and at 144 regions it makes it worse.
4. **A harder read-out is needed before the grain axis can be pushed further.**
   The primary saturates at G72, so the next grain rung must raise task
   difficulty rather than resolution, or it will measure nothing.
