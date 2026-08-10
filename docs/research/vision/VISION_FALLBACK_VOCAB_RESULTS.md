# FALLBACK VOCABULARY — RESULTS

Pre-registration `VISION_FALLBACK_VOCAB_PREREG.md`, committed **BEFORE the run**
at **`9fed48e4`**. Branch `gamma-substrate/fallback-vocabulary`, base
**`0257eef6`**. Engine **`ab9458e4b9bd`**, `own` build in this worktree (this
rung ADDS Rust, so a shared canonical build would have been refused, §10.1).
`data/` symlinked (§10.2) so the §9 baseline holds in its **`200/0 with data/`**
condition. Seed block **62000–62999**; **only 62002 (probe RNG) consumed —
62000, 62001 and 62003–62999 CLEAN.**

Runners: `scripts/fallback_probe.py`, `scripts/fallback_sweep.py`. Vocabulary:
`seeds/fallback_vocabulary.json`, `domains/fallback_readout.py`. Engine:
`runners/dsl/src/fallback_trace.rs`. Gates:
`tests/test_fallback_vocabulary_migrated.py` (16/16). Pinned data:
`results/fallback/` (26 arms).

---

## HEADLINE

**The vocabulary is BUILT and one of its two distinctions works. The
pre-registered conjunction gate FAILED, on BOTH hypotheses, and the reason is a
finding about the architecture rather than about the instrument:**

> **Ablation in the vision arc does not leave state ABSENT. It leaves state
> STALE.** Every attribute a withheld rule would have written **still exists**,
> holding the value the adapter initialised it to at wiring time. A stale read
> is a `.get()` **HIT**. Both pre-registered hypotheses are built on absence,
> and **absence never occurs here — it was destroyed before the rules ever
> ran.**

So the audit's unexplained `channels_on` **51.976 → 0.000** is **not** a
defaulted read. It is a **stale read of an initialised zero**, and no
absence-based marker can see it.

**What DID land: the silent-vs-healthy split**, which is the distinction the
audit's Arm 5 could not make and the one the layering claim actually rests on.

**Every one of my five pre-registered predictions was wrong.** That is reported
in full in *WHAT I GOT WRONG*, and it means I did not understand the state model
going in.

---

## THE CONJUNCTION GATE — the 2×2, never pooled

| hypothesis | (a) FIRES on `vision_lateral` | (a) FIRES on `vision_waves` | (b) silent on baseline | verdict |
|---|---|---|---|---|
| **H1 defaulted-read** | **NO** (0 markers) | **NO** (0 markers) | YES (0 markers) | **FAIL** |
| **H2 absence-branch** | **NO** (0 markers) | **NO** (0 markers) | YES (0 markers) | **FAIL** |

**Both hypotheses pass half (b) VACUOUSLY — by never firing at all.** That is
precisely the failure mode the rung was warned about ("a marker that always
fires and a marker that never fires both score perfectly on one half"), and it
is why half (b) alone is worth nothing. Recording it as a pass would have been
the eighth instance of this project's most-repeated error.

### The ablation itself demonstrably bit (the control that makes the null mean something)

| arm | live rules | rule firings | `channels_on` sum |
|---|---|---|---|
| BASELINE | **7** / 52 | 274 | **97.057** |
| `vision_lateral` ablated | **3** | 114 | **0.000** |
| `vision_waves` ablated | **4** | 160 | **7.999** |

The audit's cliff reproduces exactly. **"No marker fired" is measured against a
pipeline that provably degraded**, not against a no-op.

### Both instruments are ALIVE (the control that makes the null a measurement)

§1.1: *a dead arm scores a perfect floor.* Neither zero above is a silent
instrument:

- **H1**: the baseline run pushes **1 038 808 `Attr` evaluations** through the
  instrumented branch. On a hand-built rule that genuinely reads an unwritten
  attribute the engine records `('gate_reads_absent', 'never_written', 1)` —
  naming both the rule and the key.
- **H2**: on a hand-built `Not(Exists(..))` over an empty source the engine
  records `('gate_absence_branch', 1)`.

Both positive controls are committed gates, not one-off scripts.

---

## THE DIAGNOSIS — measured, not inferred

Attribute **key sets** on the affected nodes, baseline vs ablated:

| node | baseline keys | after `vision_lateral` ablated |
|---|---|---|
| `HCell` | `col g1 g2 gain_step h1 h2 n_nb1 n_nb2 pool_step resid resid_step row` | **identical** |
| `RetinaCell` | `activated_at bursting col … last_burst … state` (20 keys) | **identical** |

**`h1`, `h2`, `resid`, `g1`, `g2` all still exist after the rules that write
them have been withheld.** `add_lateral_retina` and `WaveWorld` initialise every
attribute at wiring time, so removing a producer changes a value, never a key.

**This is the architecture violating its own principle.** `unknown = absence,
first-class` is the substrate's stated foundation; the vision adapter's eager
initialisation overwrites absence with zero before any rule runs. **The silent
cliff and the unobservability are the same fact**: there is nothing absent to
observe.

### Why whole-seed ablation could not have worked anyway

A second, independent reason, worth separating: **a seed's readers and its
writers are co-resident.** `lat_pool` writes `h1`/`h2`; `lat_residual` reads
them; both live in `vision_lateral`. Withholding the seed removes the reader
along with the writer, so **no surviving rule is left to record the miss**. Even
with honest absence, whole-seed ablation is the wrong granularity for H1 — it
would need a **cross-seed** consumer, or rule-granular ablation.

Both causes are real and either alone is sufficient. I report them separately
because fixing only one would not move the result.

---

## WHAT DID LAND — the separability split

The vocabulary classifies every rule into three states that an ablation harness
sees as one undifferentiated "no test loss". On the healthy baseline probe:

| status | decided by | count |
|---|---|---|
| **healthy** — ran on real inputs | `fv_status_healthy` | **7** |
| **degraded** — ran on values nobody wrote | `fv_status_degraded` | **0** |
| **silent** — nothing ran | `fv_status_silent` | **48** |

**48 of 52 rules are `silent` on this panel.** That is the audit's "inert
because dead" category — 15 of 25 audited seeds, 38 never-firing rules — now a
**word in the graph** instead of an inference from a separate census.

### The separability question, answered honestly

The deliverable asked whether this distinguishes *"layer B genuinely operates
without A"* from *"nothing in B was running"*.

- **YES for the second half.** `silent` vs `healthy` is exactly that
  distinction, it is graph-resident, and it is decided by a rule. The audit's
  Arm 5 verdict (*"the reflexes are subroutines, not a layer"*) rested on
  discovering, via a separate hand-run census on a second panel, that the
  "independent" reflexes had been tested against machinery that never ran. **A
  substrate carrying this vocabulary announces that in its own state.** That is
  a real advance on the audit and it is the honest core of this rung.
- **NO for the first half, on real ablations.** Distinguishing *ran on real
  inputs* from *ran on defaults* requires the `degraded` class, and **no vision
  ablation reaches it**, for the stale-not-absent reason above. `fv_status_degraded`
  is positive-controlled on a hand-built case and is therefore known to work —
  but it is **unreached by the panel this rung measured**, and I do not claim
  otherwise.

**So: the dead/alive boundary is now observable. The healthy/degraded boundary
is not.** The second is where `vision_waves`' non-monotone curve lives, and it
remains unobservable.

---

## OVERHEAD (§5, counted — requirement 2)

| quantity | value |
|---|---|
| `Attr` evaluations, healthy probe | **1 038 808** |
| of those, defaulted (the instrument's entire dynamic cost) | **0** |
| **miss fraction `N_default / N_attr`** | **0.000** |
| rule firings | 274 |

**The always-on instrument performs ZERO increments on a healthy vision
workload.** Its cost is one branch that the engine already took: the hit arm is
`Some(v) => v.clone()`, byte-for-byte the work `unwrap_or` already did.

Compare `ENGINE_WINNER_VALUE_RESULTS.md`, whose instrument came in at **81.41%
overhead and therefore ships OFF**, making it useless as always-on
observability. **This one is cheap enough to leave on, and it is on.**

**The honest caveat, and it is not small: the cost is zero BECAUSE the marker
never fires.** "Cheap" and "found nothing" are the same measurement here. Cost
scales with the number of fallbacks recorded — the right shape (compute ∝
surprise), but a panel where H1 fired constantly would pay proportionally, and
this rung has not measured that regime.

**Wall-clock, reported only with its load state** (§ precedent: 1.66× variation
from load alone). Hit-path denominator OFF vs ON, 5 runs each, median of 5,
**under concurrent load average 2.47 with a bench running**:

| | median | min | max |
|---|---|---|---|
| totals OFF (shipped default) | 70.8 ms | 67.2 | 78.6 |
| totals ON (measurement only) | 71.5 ms | 59.8 | 94.0 |

The 0.7 ms difference is **inside the spread** and is not resolvable. **Not a
headline; the counted number is.**

---

## §9 BYTE-IDENTITY — nothing moved

| check | result |
|---|---|
| `scripts/rung7_vision_bench.sh` **before** any change (engine `11ee213dfd46`) | **200 passed, exit 0** |
| `scripts/rung7_vision_bench.sh` **after** the Rust + seed (engine `ab9458e4b9bd`) | **200 passed, exit 0** |
| sd orbit law `{2:1,3:2,4:2,6:2,12:4}` | **unmoved** (3 passed) |
| `tests/test_fallback_vocabulary_migrated.py` | **16 passed** |
| Rust unit tests `fallback_trace` | **5 passed** |
| `seeds/` git status | clean apart from the ONE new seed file |

**Byte-identity here is structural, not merely tested.** Nothing in
`fallback_trace` is ever read by a `Term`: the tallies are write-only from the
evaluator's perspective and are drained by an explicit report call. There is no
path from a counter back into `evaluate`, so the instrument is **incapable** of
changing a match, an effect, or a value. The bench confirms what the data flow
already guarantees.

The seed **ships INERT** — it installs one documentation node and no
`RuleActivity`, so its three rules have nothing to match until a reader
explicitly mints a report. Minting adds nodes and therefore moves
`node_count()`, so it can never be implicit (§9).

---

## PREDICTIONS (§3.7) — 5 stated in advance, **5 wrong**

1. **"H2 FAILS half (b) loudly — the clock barriers false-positive."** **WRONG,
   and informatively so.** H2 does not false-positive at all. The instrument
   discriminates *empty source* from *predicate never matched*, and the vision
   seeds' barriers have **non-empty** sources (there ARE presynaptic bipolars;
   they are simply not behind the clock). My stated proviso — *"I predict they
   are empty, because a barrier's whole purpose is to wait for an empty
   behind-the-clock set"* — is exactly what broke, and it broke because I
   confused "the predicate is false for every element" with "there are no
   elements".
2. **"H1 passes half (a) on both named seeds."** **WRONG.** Zero on both.
3. **"H1's half (b) is at risk; I predict RELATIVE, not STRICT."** **WRONG.**
   `FP_D == 0` exactly — the STRICT form — but vacuously, which is worse than
   the RELATIVE pass I predicted.
4. **"The separability split is non-degenerate; a rule appears in the degraded
   row."** **HALF WRONG.** The split is non-degenerate (7 healthy / 48 silent)
   but the **degraded row is empty on every real ablation**.
5. **"Overhead between 1% and 20%."** **WRONG.** 0.000%. Stating the range in
   advance is what makes landing outside it informative rather than absorbable.

**Five for five. I did not understand the state model, and the pre-registration
is what makes that legible instead of invisible.**

---

## WHAT I GOT WRONG (beyond the predictions)

1. **The first smoke test silently loaded the CANONICAL engine.** I ran a bare
   `python -c` with `sys.path.insert(0, '.')` and no `engine_preamble()`, so the
   absolute `site-packages/*.pth` resolved another tree's binary — §10.1 rule 3,
   exactly as documented. **It failed LOUDLY only because my change added new
   Python-visible methods** (`AttributeError`). Had this rung added only a
   counter with no new API, it would have measured the wrong engine **in
   silence**. The probe scripts now call `engine_preamble()` themselves and say
   why.
2. **The seed's first draft declared its productions over node type `Unit`**,
   copied from `vision_maps` where `Unit` is the real type. Γ rejected the edges
   (`Type-2: not in vocabulary`) — the admissibility grammar catching a
   vocabulary error that would otherwise have surfaced as a rule mysteriously
   never matching.
3. **My first gate suite asserted the hoped-for outcome and went red.** I
   rewrote the tests to assert the **measured** outcome, with the diagnosis in
   the docstrings and a guard telling a future reader to re-open this file
   rather than flip the assertion. That is §7, not §5: the measurement was
   verified first and the gate was changed to record it, never to rescue it.
4. **I nearly reported the miss fraction of 0.000 as a clean win.** It is a real
   number and it does answer requirement 2, but it is the same fact as the
   negative — the instrument is free because it never fires. Reporting the
   overhead without that sentence would have been misleading.

---

## SCOPE — what is NOT shown (§8)

- **Coverage: 25 of 573 seeds (4.4%)**, selection rule fixed in advance
  (§6: the redundancy audit's own `TARGETS`, blast radius ≥ 2). The `TARGETS`
  list is copied verbatim from `scripts/redundancy_sweep.py`, not re-derived.
- **The FIRES half rests on 2 degraded points** — the same denominator the audit
  had. It did not grow and this rung does not pretend otherwise.
- **One probe pipeline** (`vision_waves` + `vision_lateral` + `vision_onoff`,
  16×16, 40 steps, RNG 62002). 23 of the 25 ablations do not move it at all —
  identical readouts to baseline in every arm — so they contribute nothing but a
  no-op control.
- **The `degraded` class is positive-controlled but UNREACHED by any real
  ablation.** It is not demonstrated on live vision machinery.
- **"Stale, not absent" is established for the vision arc only.** Other
  subsystems may leave genuine absence; this rung did not look. `gap_awareness`'
  mint-if-not-exists idiom suggests the cognitive seeds may differ.
- **No claim that H1 is wrong in general.** It is *blind here*, for two
  identified structural reasons. On a subsystem that does not pre-initialise, or
  under rule-granular ablation with a cross-seed consumer, it may well fire —
  untested.
- **Rule-firing counts are panel-relative**: "silent" means silent *on this
  probe*, never dead in the agent.
- **No self-stabilization claim.** Every arm is a fresh process; nothing is
  perturbed-then-continued, so *recovers* / *persists* / *diverges* remain
  unmeasured.

---

## NAMED, NOT BUILT — what this rung's negative points at

Recorded rather than retrofitted (§3/§5). Each follows from the diagnosis and is
**not** a parameter search on a failed gate — each needs its own
pre-registration with its own mechanism-level hypothesis.

1. **RULE-GRANULAR ABLATION WITH A SURVIVING CONSUMER.** Withhold `lat_pool`
   (the writer) while keeping `lat_residual` (the reader). This is the smallest
   change that could make H1 fire, and it isolates the co-residency cause from
   the initialisation cause.
2. **STOP EAGERLY INITIALISING, or make staleness first-class.** The deeper
   finding is that the adapter overwrites the architecture's own first-class
   absence. Two candidate repairs, and they are **not** equivalent: (a) let the
   adapter wire structure without values, so an unwritten attribute is genuinely
   absent and `unknown = absence` holds in the vision arc as it does elsewhere;
   or (b) keep initialisation and mark **staleness** instead — a per-attribute
   write-epoch, so "written at step 3, read at step 40" is a recordable fact.
   **(b) is the one that would catch `vision_waves`' non-monotone curve**, since
   a component firing on its collaborators' last-known values is reading stale,
   not absent. (a) is more faithful to the architecture; (b) covers the observed
   failure. Neither is built here.
3. **A STALENESS MARKER IS THE ACTUAL MISSING VOCABULARY.** This rung built the
   absence vocabulary and measured that absence is the wrong predicate for this
   subsystem. The honest successor is a staleness vocabulary, gated by the same
   conjunction — and it should be pre-registered with the prediction that it
   FIRES on `vision_waves`' non-monotone region, which is the sharpest available
   test.
4. **CHECK WHETHER THE COGNITIVE SEEDS DIFFER.** `gap_awareness`,
   `comprehension_health` and `perception_frontiers` mint markers on
   `Not(Exists(..))` over `NodesOfType`. If those sources are genuinely empty in
   degraded operation, H2 may be live *there* while dead in vision — which would
   make "is a fallback structurally identifiable?" a **per-subsystem** question
   rather than an architectural one. This rung's answer is scoped to vision and
   should not be generalised.

---

## THE ANSWER TO THE QUESTION ASKED

**Are fallbacks structurally identifiable in this architecture?**

**In the vision arc: NO — because there are no fallbacks to identify.** The
system does not fall back. It **carries on with stale values**, and it does so
because its state was initialised eagerly enough that the absence of a producer
is unrepresentable. A vocabulary of absence has nothing to bind to.

**The offered absence-branch hypothesis (H2) does not hold**, and it fails for a
sharper reason than the one I predicted: the `Not(Exists(..))` sites in this
subsystem are **clock barriers over non-empty sources**, so the shape is neither
a false-positive generator nor a fallback detector — it is simply orthogonal.
**Deriving markers from rule structure is sound in principle** (both instruments
are structural, hand-annotation-free, and positive-controlled) **and finds
nothing here, because the thing it detects does not occur.**

**What IS now identifiable, and was not before: the dead/alive boundary.** A
substrate carrying this vocabulary says, in its own graph state, which of its
rules ran and which did not — so *"layer B is independent of A"* can finally be
told apart from *"nothing in B was running"*. **That is one of the two halves of
separability, it is the half the audit's Arm 5 got wrong, and it is real.** The
other half needs staleness, not absence, and this rung is the measurement that
says so.
