# REDUNDANCY AUDIT — pre-registration

**Written and committed BEFORE any dependent variable was measured (PROTOCOL §3).**

Branch `gamma-substrate/redundancy-audit`, base `dd174b95`.
Engine **`985fb252ce41`** (shared build from the canonical tree; Rust source
byte-identical — NO new Rust, §10.1 rule 4). `data/` symlinked to the canonical
tree (§10.2), so the §9 baseline is quoted in its **`200/0 with data/`** condition.

Seed block **59000–59999** (verified free: ledger high-water 52203; `59467857`
in the ledger is a commit SHA, not a seed claim).

---

## 0. THE PRINCIPLE UNDER TEST

The architecture claims: **lose a feature and the system DEGRADES; it does not
FAIL.** An ablated faculty should produce a characteristic degradation, not a
crash and not a confident wrong answer.

A known VIOLATION is already on record (merged `dd174b95`): on a scene cut the
invariant comparator fails on **all 16 regions simultaneously** while remaining
confident — a cliff. This rung asks, systematically: **which faculties degrade
and which cliff?**

---

## 1. WHAT IS PRE-MEASURED (structure), AND WHAT IS NOT (results)

Two things were computed BEFORE this document, deliberately, because the
selection rule has to be defined over them. **Both are STRUCTURAL facts about
the harness — knowable by reading the source — and neither is a dependent
variable:**

1. **The §9 baseline**: `scripts/rung7_vision_bench.sh` → **200 passed, exit 0**,
   128s (with `data/`).
2. **The seed→bench-file map** (`scripts/redundancy_trace_seeds.py` →
   `results/redundancy_seed_map.json`): which seeds each bench file actually
   installs, recorded by wrapping the three install paths.

**No ablation has been run. No pass-count under any ablation has been seen.**

### 1.1 The structural map, and the finding it forces BEFORE any ablation

15 of the 20 bench files install seeds at all. The other **5 install none**
(`test_vision_graph_eye`, `test_vision_kernels`,
`test_vision_hierarchy_and_learning`, `test_fb_vision`,
`test_engine_provenance_migrated`) — they are numpy/provenance tests, and **no
seed ablation can move them**. That is 5/20 files structurally inert, known in
advance, and it is part of the coverage bound, not a result.

Blast radius (number of bench files that install the seed):

| blast radius | seeds |
|---|---|
| **15 (all seed-loading files)** | the 11 `CORE_SEEDS`: `decision_core`, `epistemics_core`, `experimentation_core`, `goal_construction`, `learning_core`, `memory_core`, `motor_core`, `perception_core`, `reflex_core`, `self_monitoring`, `theorem_core` |
| **11** | `vision_waves` |
| **2–4** | `vision_onoff`(4), `vision_maps`(3), `vision_lateral`(3), `vision_floor`(3), `math_capability_shapes`(3), `self_design_axis`(3), `sensory_convolution`(3), `shape_decode_loop`(3), `vision_complex`(2), `vision_compose`(2), `vision_dorsal`(2), `vision_eye`(2), `vision_growth`(2) |
| **1** | **548 seeds** — every one of them reached only by `test_vision_curriculum_migrated.py`, which does a full 573-seed boot |

**⇒ A THIRD INERTNESS CATEGORY, dominant, and forced by construction.** The task
named two ("inert because dead" vs "inert because covered"). The map forces a
third and it is the majority case: **inert because NEVER CO-LOADED.** 548 of the
573 seeds the bench touches (95.6%) are installed by exactly ONE file, so a
cross-capability effect is **impossible by construction** — not redundant, not
dead, simply never in a position to matter on this panel.

**This is pre-registered as the expected dominant outcome so that it cannot be
reported later as a redundancy finding.** A cross-capability matrix over this
bench is near-diagonal *a priori*. The only cells where the question is even
askable are the ones in the table above with blast radius ≥ 2.

---

## 2. SELECTION RULE (fixed here, before any result)

**Target set T** = every seed with **blast radius ≥ 2** on the bench map. That is
**25 seeds** (11 core + 14 shared). The rule is purely structural: *a seed is
auditable for cross-capability effect iff at least two bench files install it.*
Nothing about its content or its measured behaviour enters the selection.

Excluded, with the reason logged, NOT silently truncated:

- **548 blast-radius-1 seeds** — cross-capability effect impossible by
  construction (§1.1). Reported as structurally out of scope.
- The rest of the ~575 seed files not touched by the bench at all.

**Coverage bound to be quoted with every claim: 25/573 seeds (4.4%) audited;
15/20 bench files structurally movable; 548/573 seeds structurally inert on this
panel.**

---

## 3. ARMS

### Arm 0 — BASELINE DETERMINISM + CONCURRENCY (gate, run first)

3 unablated bench runs, executed concurrently. All three must give **200 passed**.
If they do not, the bench is flaky, every delta below is noise, and the rung
stops here and reports that.

### Arm 1 — RULE-FIRING CENSUS (the §1.1 dead-arm gate, run BEFORE any ablation)

Per rule, across a full instrumented bench run, the engine's own
`rule_costs_report()` triple `(micros, count_processed, progress)`. **`progress`
is incremented only when a rule application actually mutated the graph** — it is
the firing counter.

**Pre-registered classification, applied to every rule in T:**

- `progress > 0` → **LIVE**. Its ablation is interpretable.
- `progress == 0` → **DEAD ON THIS PANEL**. Its ablation is inert *because it
  never fired*, and is reported in a **separate table** from a rule that fired
  and was covered for. **These two must never be pooled** — they are opposite
  findings.

A seed all of whose rules are dead is a **dead seed** on this panel and every
"no effect" it produces is uninformative by construction.

### Arm 2 — WHOLE-SEED ABLATION MATRIX (the cross-capability measurement)

For each of the 25 seeds in T: install the seed **without any of its rules**,
run the full bench, record per-file pass/fail.

**The matrix reported is the OFF-DIAGONAL.** A seed's own gate failing proves
only that the ablation took effect (that is its purpose, and it is the positive
control, not the result). The redundancy question is what happens to the other
files.

### Arm 3 — SEVERITY CURVES (the curve, not the point)

A single before/after cannot distinguish graded loss from a step. For each seed
in T with **2 ≤ n ≤ 15** rules (12 seeds, 65 rule-removal points):

- Draw a random **permutation** of the seed's n rules using
  `random.Random(59000 + arm_index)`, seeds **59000–59001** for the two
  replicates (block 59000–59999).
- Ablate the **first k** of that permutation, for k = 1..n. The sets are
  **nested**, so the severity axis is monotone by construction and one curve is
  n runs rather than 2^n.
- **R = 2 independent permutations** (seeds 59000, 59001).

**Pre-registered here, before seeing anything:** the permutation, its RNG seed,
and the nesting are fixed now; there is no re-draw and no sweep over R.

Seeds with n > 15 (`vision_eye` n=27, `shape_decode_loop` n=17) and n = 1 get
**Arm 2's endpoint only** — a point, no curve. **Logged as a capped sweep**, not
dropped silently.

### Arm 4 — OBSERVABILITY (a SEPARATE measurement)

For each ablation in Arm 2 that produces a **degraded-but-non-crashing** result:
does anything in the graph RECORD that a fallback occurred?

Operationalised without inventing a vocabulary: the "problem-marking" node types
and attribute keys are **enumerated from the seeds themselves** (`SelfConcern`,
`Unknown`, and attributes matching `unresolved|gap|refus|ambig|residual|stale|
fallback|missing`). A degradation is **SELF-EVIDENT** iff the post-run graph of a
fixed probe world differs from baseline in at least one of those, and **SILENT**
otherwise.

**Reported statistic: the fraction of degradations that are self-evident from
graph state alone.** A silent fallback is a silent-failure generator; this arm
exists to count them.

### Arm 5 — LAYER DISSOCIATION (added at the coordinator's request, pre-registered here before measurement)

Motivation (the creator's): the octopus keeps ~2/3 of its neurons in the arms,
each solving its own kinematics under a central GOAL rather than a central
command; spinal reflexes persist through cortical damage, which is what makes
them a **layer** and not a subroutine. The vision-relevant case is VOR — ~10ms,
fixed circuit, adaptable gain, survives loss of everything above it.

**SCOPE, stated honestly and up front:** this substrate's `Reflex` node type has
**14 instances across 10 seeds, and NOT ONE of them is in a vision seed** — they
are all reading/question-driving reflexes (`question_pursue`, `dwell_advance`,
`reform_reflex`, the 5 `reading_cortices`, …). **There is no VOR here to
measure.** The arm therefore runs on the **reading** panel
(`tests/test_reflexes_migrated.py` and the reflex-bearing reading gates), and
**no claim transfers to vision.**

- **Dead-arm guard (MORE dangerous here, per the coordinator):** each `Reflex`
  node carries a graph-resident `fire_count`. **Baseline `fire_count` per reflex
  is measured FIRST.** A reflex with baseline `fire_count == 0` "survives" every
  ablation perfectly and is **excluded from the dissociation claim** and reported
  separately as inert.
- **Direction 1 (higher → lower):** ablate the higher-layer rule/goal machinery
  (`goal_construction`, `decision_core`, `self_monitoring`, and the driving
  seed's own rules). Do the LIVE reflexes still fire, with correct `fire_count`?
- **Direction 2 (lower → higher):** ablate the reflex; does the higher layer
  still reach its outcome?

**Both directions are measured**, because a one-way dependency is the
interesting case.

---

## 4. THE SHAPE CRITERION — cliff vs degradation, WITHOUT a hand-set constant (§13)

**No "cliff = >X% drop" constant will be introduced.** The discriminator is the
SHAPE of the loss curve, and both of its reference points are ANALYTIC —
determined by the seed's own rule count n, not by the answer wanted.

For a nested severity curve, let `p(k)` = bench passes with k rules removed, the
per-step loss increment `d_k = p(k−1) − p(k)`, and total loss `L = p(0) − p(n)`.

Two scale-free statistics, each with both endpoints fixed by n:

| statistic | pure STEP (all loss at one k) | perfectly GRADED (loss spread evenly over n) |
|---|---|---|
| `maxfrac = max_k d_k / L` | **1** | **1/n** |
| `H(d)/log n` (normalised entropy of the increments) | **0** | **1** |

Both endpoints **fall out of n**, which the seed already has. A curve is
reported against its own two analytic endpoints; the distribution over the 12
swept seeds is reported, and **the raw curves are reported regardless** so the
reader can see the shape without trusting either statistic (§13 fallback,
explicitly permitted by the task).

**If the two statistics disagree, or if the curves do not separate into two
populations, that is reported as "shape not separable without a hand-set
constant" — which the task explicitly allows and §5 requires over metric
surgery.**

`L = 0` (no loss at all) is **not** a shape; it is Arm 1's inertness question and
is routed there, never given a shape verdict.

### Crash handling (§ "a crash is a result")

An ablation that **raises** — collection error, exception, engine abort — is the
rawest possible cliff. It is recorded as its own outcome class **with its
traceback**, counted in the crash list, and **NOT fixed**. No ablation result is
repaired and re-run.

---

## 5. PREDICTIONS, STATED IN ADVANCE (§3.7)

1. **The matrix will be near-diagonal, and mostly for the structural reason in
   §1.1, not for a redundancy reason.** I predict off-diagonal effects appear
   almost exclusively in the 11 blast-radius-15 core seeds and in `vision_waves`.
   *Proviso that would break it:* substantial off-diagonal loss from a
   blast-radius-2 seed would mean the closure is coupling more than the map shows.
2. **Most core-seed rules will be DEAD on this panel** (`progress == 0`). The
   vision gates exercise vision rules; the decision/goal/memory core is loaded
   because `boot_core` loads it, not because the vision tests drive it. If so,
   most core ablations are inert-because-dead and prove nothing about redundancy.
3. **`vision_waves` is the one seed where a real cross-capability curve is
   likely**, being installed by 11 files and carrying 15 rules.
4. **Shape: I predict STEP, not graded**, for the vision seeds — each rule in
   these seeds does one distinct job in a pipeline, so removing the load-bearing
   one should drop its dependents at a single k. I expect `maxfrac` near 1.
   *Proviso that would break it:* a graded curve would mean genuine rule-level
   redundancy, which would be a stronger positive result than I expect.
5. **Observability: I predict a LOW self-evident fraction.** A missing rule
   produces a missing node, and absence is not self-announcing. If most
   degradations are silent, that is a negative about the architecture's
   introspection and must be reported as loudly as any positive.
6. **Arm 5: I predict the reflexes are SUBROUTINES, not a layer** — that they
   depend on the higher machinery and stop firing when it is ablated. The
   substrate's reflexes are seed-loaded stimulus Terms evaluated inside
   `fire_reflexes`, which runs in the same adapter loop as everything else;
   there is no independent low-latency path. *Proviso that would break it:* if
   they keep firing, the layer claim is real and worth stating.

**A finding that most of the system CLIFFS is a major negative and will be
reported as prominently as the reverse (§7).**

---

## 6. DECISION RULES

- **Arm 0 not 200/200/200** ⇒ stop; report bench flakiness; no deltas claimed.
- **A seed whose rules are all DEAD** ⇒ its inertness is reported in the
  dead-arm table only, never as evidence of redundancy.
- **Null (no off-diagonal effect anywhere)** ⇒ reported as a null, and attributed
  between the three inertness causes explicitly. A null that is fully explained
  by §1.1's structural isolation is **not** a redundancy result and will be
  labelled as such.
- **No re-runs, no re-draws, no metric changes to rescue any arm (§5).** A
  failure suggesting the readout is wrong is a NEW pre-registration.

## 7. STATE RESTORATION

Ablation is performed by an **in-process manifest filter** selected by an
environment variable, so **no seed file on disk is ever modified**. The
restoration check is therefore exact and total: `git status` clean over `seeds/`
and the engine hash unchanged, verified after the sweep. An audit that corrupts
the tree it is auditing is worthless.
