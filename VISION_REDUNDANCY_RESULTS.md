# REDUNDANCY AUDIT — RESULTS

Pre-registration `VISION_REDUNDANCY_PREREG.md`, committed **BEFORE the run** at
**`a326519b`**. Branch `gamma-substrate/redundancy-audit`, base **`dd174b95`**.
Engine **`985fb252ce41`** (shared build from the canonical tree, Rust source
byte-identical — **NO new Rust, NO new seed installed**, §10.1 rule 4).
`data/` symlinked (§10.2), so the §9 baseline holds in its **`200/0 with data/`**
condition. Seed block **59000–59999**; **only 59000, 59001 (permutations) and
59002 (probe) consumed — 59003–59999 CLEAN.**

Runners: `scripts/redundancy_sweep.py`, `redundancy_ablate_plugin.py`,
`redundancy_arm5.py`, `redundancy_reflex_plugin.py`,
`redundancy_observability.py`. Analysis: `redundancy_analyse.py`,
`redundancy_matrix.py`, `redundancy_obs_analyse.py`. Pinned data:
`results/redundancy/` (135 configs), `results/redundancy_arm5/` (29),
`results/redundancy_obs/` (26), `results/redundancy_{analysis,matrix,observability}.json`.

---

## HEADLINE

**The vision arc CLIFFS. It does not degrade gracefully, and it does not say so.**

Every severity curve with any loss on it is **step-shaped, not graded**; the one
seed rich enough to show a gradient is **non-monotone** (removing an *extra*
rule *recovers* tests); and **not one** of the degradations left any trace in
the graph — observability **0/2**, with the marker inventory **empty in all 26
probe runs including baseline**.

**Equally important, and the reason most of this audit is uninformative about
redundancy: 15 of the 25 audited seeds NEVER FIRE A RULE on this panel.** Their
"no effect when ablated" is **inert-because-dead**, not resilience. Pooling those
with the real zeros would have produced a beautiful and completely false
redundancy result.

---

## ARM 0 — baseline determinism + concurrency gate: **PASS**

Three concurrent unablated runs: **200 / 200 / 200**, exit 0. The bench is
deterministic and safe to run in parallel.

## THE EMPIRICAL NULL (obtained free, and it matters)

Six target seeds declare **zero rules**, so "withhold all rules" is a genuine
no-op. Extending that to every config whose ablated seed has **no firing rule**
gives **41 null configs**:

| total passes | count |
|---|---|
| 200 | **40** |
| 199 | **1** |

**Noise floor `|Δ| = 1`** (rate 1/41 ≈ 2.4%), and the single deviation is
localised to `test_vision_curriculum_migrated.py` — the file that boots all 573
seeds. **Any effect of magnitude ≤ 1 in this report is inside the null.**
(`vision_maps`' own-gate loss of exactly 1 is therefore NOT claimed.)

---

## ARM 1 — the rule-firing census (the dead-arm gate)

Engine's own `rule_costs_report()` `progress` counter, which increments only when
a rule application actually mutated the graph.

**LIVE seeds** (rules that fire on the vision bench):

| seed | rules | LIVE | DEAD | fires |
|---|---|---|---|---|
| `vision_waves` | 15 | 11 | 4 | 123 235 |
| `vision_lateral` | 4 | 4 | 0 | 94 523 |
| `vision_onoff` | 8 | 8 | 0 | 88 329 |
| `vision_dorsal` | 4 | 4 | 0 | 22 711 |
| `vision_eye` | 27 | **12** | **15** | 10 144 |
| `vision_floor` | 11 | 10 | 1 | 1 478 |
| `vision_growth` | 2 | 2 | 0 | 824 |
| `vision_complex` | 3 | 3 | 0 | 720 |
| `vision_maps` | 1 | 1 | 0 | 81 |
| `sensory_convolution` | 1 | 1 | 0 | 4 |

**DEAD seeds — 15 of 25 (60%), zero fires:** `decision_core`(1 rule),
`experimentation_core`(1), `goal_construction`(4), `learning_core`(4),
`memory_core`(3), `reflex_core`(2), `self_monitoring`(5), `self_design_axis`(1),
**`shape_decode_loop`(17)**, plus `epistemics_core`, `math_capability_shapes`,
`motor_core`, `perception_core`, `theorem_core`, `vision_compose` (no rules at
all).

**38 rules are installed into every vision-bench substrate and never fire once.**
`shape_decode_loop` — 17 rules, blast radius 3 — is entirely dormant here. The
whole decision/goal/memory/monitoring core is loaded because `boot_core` loads
it, not because the vision gates drive it. **Prediction 2 confirmed.**

---

## ARM 2 — the cross-capability matrix

**The first cut of this matrix was wrong and would have been vacuous.** I
defined the diagonal as "every file that installs the ablated seed", which
absorbed the entire effect and printed a zero off-diagonal for all 25 seeds. The
question needs three cells:

- **OWN** — the seed's own gate file. The **positive control** that the ablation
  took effect, never the result.
- **CO-LOADED** — files that *install* the seed but are not its gate. **This is
  the cross-capability question.**
- **UNRELATED** — files that never install it. Structurally forced to zero.

| seed | n | live | loaders | OWN | **CO-LOADED** | UNREL | where |
|---|---|---|---|---|---|---|---|
| `vision_waves` | 15 | 11 | 11 | 3 | **14** | 0 | complex −3, compose −1, lateral −6, maps −2, onoff −1, setpoint −1 |
| `vision_floor` | 11 | 10 | 3 | 3 | **6** | 0 | curriculum −2, growth −4 |
| `vision_eye` | 27 | 12 | 2 | 0 | **3** | 0 | setpoint −3 |
| `sensory_convolution` | 1 | 1 | 3 | 0 | **2** | 0 | floor −2 |
| `vision_growth` | 2 | 2 | 2 | 4 | **2** | 0 | curriculum −2 |
| `vision_lateral` | 4 | 4 | 3 | 9 | **2** | 0 | compose −2 |
| `vision_onoff` | 8 | 8 | 4 | 7 | **2** | 0 | compose −2 |
| `vision_dorsal` | 4 | 4 | 2 | 4 | 0 | 0 | — |
| `vision_maps` | 1 | 1 | 3 | 1 | 0 | 0 | (own loss = noise floor) |
| **`vision_complex`** | 3 | **3** | 2 | **0** | **0** | 0 | **nothing, anywhere** |
| 15 dead seeds | — | 0 | 2–15 | 0 | 0 | 0 | — |
| `epistemics_core` | 0 | 0 | 15 | 0 | 1 | 0 | the flake (no-op ablation) |

**UNRELATED is 0 for all 25 seeds** — no leakage, and the structural isolation of
PREREG §1.1 is confirmed exactly as pre-registered.

**Real cross-capability propagation exists and is confined to the vision-arc
shared seeds.** `vision_waves` is the hub, as predicted: ablating it costs 14
tests across **six other capabilities**. **Prediction 1 and 3 confirmed.**

### The three inertness categories, kept strictly apart

1. **INERT BECAUSE NEVER CO-LOADED** — 548/573 seeds (95.6%), blast radius 1.
   Impossible by construction. Pre-registered; not a redundancy finding.
2. **INERT BECAUSE DEAD** — 15/25 audited seeds, 38 never-firing rules. Their
   zeros mean nothing about redundancy.
3. **INERT BECAUSE COVERED** — exactly **ONE** seed qualifies: **`vision_complex`.
   3 rules, all LIVE, 720 firings, and withholding every one of them costs zero
   tests — including its own gate.** That is §13.2's FM-0 disease (*"works" and
   "is load-bearing" are different properties*) caught by ablation rather than by
   a vacuity toggle. It is either genuine redundancy or decoration; **this rung
   cannot distinguish those two**, and says so.

**So the redundancy question, honestly scoped, has a sample size of ONE.**

---

## ARM 3 — severity curves: the shape is a STEP

Both statistics against their **analytic** endpoints (step: `maxfrac`=1, `H`=0;
graded: `maxfrac`=1/n, `H`=1). **No threshold applied.**

| seed | n | L | maxfrac (graded floor) | H |
|---|---|---|---|---|
| `vision_dorsal` | 4 | 4 | **1.000** / 1.000 (0.250) | 0.000 / 0.000 |
| `vision_growth` | 2 | 6 | **1.000** / 1.000 (0.500) | 0.000 / 0.000 |
| `vision_lateral` | 4 | 11 | 0.545 / **1.000** (0.250) | 0.497 / 0.000 |
| `vision_floor` | 11 | 9 | 0.778 / 0.778 (0.091) | 0.285 / 0.285 |
| `vision_onoff` | 8 | 9 | 0.444 / 0.778 (0.125) | 0.510 / 0.255 |
| `vision_waves` | 15 | 17 | 0.824 / 0.471 (0.067) | 0.296 / 0.451 |

**Every curve sits far above its graded floor and far below H=1.** Four of twelve
are **pure steps** (`maxfrac`=1.000, `H`=0.000). **Prediction 4 confirmed: the
architecture cliffs, it does not degrade.**

Consistency check that came out right: **`L` is permutation-invariant** for all
six seeds (both permutations end at the same total loss, as they must).
`maxfrac` is *not* permutation-invariant — it depends on where the load-bearing
rule falls in the nested order — so it measures *concentration of loss*, not
*which* rule matters. Reported as such.

### The sharpest single result: degradation is NON-MONOTONE

`vision_waves`, **on both independent permutations**, recovers tests when *more*
rules are removed:

```
p59000  [200,200,200,200,198,184,184,184,184,187,187,187,183,183,183,183]
                                   k=8 -> 9 :  184 -> 187   (+3)
p59001  [200,199,199,194,186,186,186,188,183,183,183,183,183,183,183,183]
                                   k=6 -> 7 :  186 -> 188   (+2)
```

The ablation sets are **nested**, so this is not noise in the design: a
**partially** ablated pipeline is *worse* than a **more** ablated one. Some rule
does **active harm** once its collaborators are gone — it keeps firing into a
pipeline that can no longer support it. This is the opposite of a graceful
fallback, and it is invisible to any single before/after measurement. **It is
also, structurally, the same failure as the known scene-cut violation**: a
component that stays confident after its preconditions have vanished.

---

## ARM 4 — observability: **0/2, and the vocabulary is entirely absent**

Fixed probe world (wave/lateral/on-off, RNG 59002), 25 whole-seed ablations.

| | |
|---|---|
| degraded, non-crashing | **2** |
| self-evident from graph state | **0** |
| **observability fraction** | **0.000** |

- `vision_lateral` ablated → `channels_on` sum **51.976 → 0.000**, `channels_off`
  **0.481 → 0.000**, all learned gains → **0.0**. Markers: **none**.
- `vision_waves` ablated → `channels_on` **51.976 → 8.000**. Markers: **none**.

**The marker inventory was EMPTY in all 26 runs, baseline included.** There is no
active fallback-recording vocabulary in this subsystem at all — so the finding is
not "the markers didn't fire", it is "there are none to fire". The system returns
a confident, well-formed, numerically clean **zero** and leaves no evidence.
**Prediction 5 confirmed.** This is a silent-failure generator of exactly the
shape §10.2 warns about.

**Honest bound: the denominator is 2.** The probe exercises one pipeline; 23 of
the 25 ablations did not move it. The *qualitative* claim (no marker vocabulary
is live anywhere in the probe) is solid; the *fraction* rests on two points.

---

## ARM 5 — layer dissociation (reading panel; **there is no vision reflex**)

Baseline panel: **70 passed / 3 failed**. **The 3 failures are PRE-EXISTING at
`dd174b95`** — reproduced without the instrument — and are not ablation effects.

14 seed reflexes: **10 LIVE, 4 DEAD** (`language_cortex`, `question_pursue`,
`reform_ingest_reflex`, `upload_text_read_advance`), excluded from the
dissociation claim per pre-registration. Note `language_cortex` never fires while
its four identically-shaped sibling cortices all do.

### Direction 1 — ablate the higher layer

Ablating `decision_core` / `goal_construction` / `learning_core` / `memory_core` /
`self_monitoring` / `experimentation_core` / `reflex_core`: **all 10 live reflexes
keep firing, zero test loss.**

**This is NOT a dissociation, and reporting it as one would have been the rung's
biggest error.** Measured on the reading panel: **those seven seeds' 20 rules fire
ZERO times there too.** The reflexes survived the removal of machinery that was
never running. **The dead-arm trap, caught by running the census on the second
panel rather than assuming the first one transferred.**

Where the higher layer is genuinely live — a reflex's **own driving seed** — the
result is a **cliff**:

| ablated driver | passes | Δ | live reflexes stopped |
|---|---|---|---|
| `literary_analysis_driving` | 57 | **−13** | **6 of 10 at once** (analysis_advance, executive/narrative/situation/social_cortex, reform_reflex) |
| `predictive_reading` | 66 | −4 | predictive_read_advance |
| `reading_dwell` | 68 | −2 | dwell_advance |
| `literary_analysis_unit_driving` | 68 | −2 | unit_analysis_advance |

One seed's rules are load-bearing for **three other seeds'** reflexes — real
cross-seed coupling, and it fails all at once.

### Direction 2 — ablate the reflex (positive control verified per reflex)

| reflexes withheld | passes | Δ | firing after |
|---|---|---|---|
| ALL | 46 | **−24** | 0 |
| `reading_cortices` (4 live) | 59 | **−11** | 0 |
| `predictive_reading` | 66 | −4 | 0 |
| `issue_reopen` | 67 | −3 | 0 |
| `reading_dwell` | 68 | −2 | 0 |
| `literary_analysis_unit_driving` | 68 | −2 | 0 |
| **`literary_analysis_driving`** | **70** | **0** | 0 (186 → 0 fires) |
| **`reading_reform_reflex`** | **70** | **0** | 0 (15 → 0 fires) |

**VERDICT: the reflexes are SUBROUTINES, not a layer. Prediction 6 confirmed** —
and for a sharper reason than predicted. The only apparent layer-independence was
against dead machinery; against their real drivers the dependency is
**bidirectional** and **cliff-shaped**. There is no VOR here: no low-latency path
that survives the loss of what is above it.

**Two more decorations found:** `analysis_advance` fires **186** times and
`reform_reflex` **15**, and withholding either costs **zero** tests — live, and
load-bearing on nothing. (Both ablations positive-controlled per reflex: fire
counts go to 0.)

---

## NAMED, NOT BUILT — the RECOVERY / SELF-STABILIZATION arm

**Requested by the coordinator AFTER this rung's headlines were already
measured. Per §3/§5 and the request's own instruction, it is recorded here as
named-not-built rather than retrofitted.** Retrofitting it would be forking
paths (§4) wearing a pre-registration's costume, and a thin version would be
worse than none — it would read as evidence for a property the system may not
have.

**The reframe is right and it makes this rung's framing only half the
property.** The architecture does not claim knowable outcomes in all
situations — that is trivially false of any real system. It claims **EVENTUAL
STABILITY**, in Dijkstra's precise sense of **self-stabilization**: from *any*
state, including an arbitrarily corrupted one, the system converges to a
legitimate state in finite steps and stays there (closure). **Γ, the
admissibility grammar, IS the legitimacy predicate, and the `run_rules` fixpoint
IS the convergence mechanism.** That is not an analogy — it is the same
structure, and it means "does it cliff?" and "does it recover?" are different
questions. **This rung measured only the first.**

What a future rung must pre-register and run:

1. **Perturb, then continue.** After each ablation, RESTORE the seed and keep
   ticking. Report the **recovery curve**, not merely the degraded level. This
   rung's harness cannot answer it: every config is a **fresh process**, so
   restoration is by construction and nothing is ever "continued".
2. **Corrupt STATE directly, not only rules.** Self-stabilization is about
   arbitrary starting states. Inject a graph state violating something Γ
   requires and measure whether the fixpoint **repairs**, **leaves**, or
   **propagates** it.
3. **Three outcomes, never pooled:** *recovers* (converges to admissible),
   *persists* (stable but illegitimate — Γ tolerating what it should not),
   *diverges* (the perturbation spreads). **"Persists" is the quiet one** and
   the one most easily mistaken for health.
4. **Recovery TIME is first-class.** Passes-to-recovery, not just whether.
   Finite-but-huge and finite-and-fast are materially different properties and
   only the second is useful.
5. **The dead-arm hazard is SHARPER here**, and this rung supplies the reason it
   would have bitten: **15 of 25 audited seeds never fire a rule**, and a
   component nothing depends on **"recovers" perfectly from every
   perturbation**. The census in Arm 1 is the prerequisite instrument, and any
   recovery claim must exclude the inert.

**Two findings here bear on it and are flagged as observations, NOT as a
recovery result.** (a) The **crash list is empty** — no perturbation in 190
configs made the system fall over, which is consistent with closure but does not
test it. (b) **`vision_waves`' non-monotone curve** — a partially ablated
pipeline scoring *worse* than a more deeply ablated one — is the signature of a
component that **keeps running after its preconditions are gone**. That is what
a *persists* outcome would look like from outside, and it is the single most
promising place for the recovery arm to start.

## CRASH LIST

**None.** No ablation raised, hung, or aborted — across 135 bench configs, 29
reading configs and 26 probes. The rawest cliff class is **empty**: the system
fails by returning wrong answers, never by falling over.

---

## PREDICTIONS (§3.7) — 6 stated in advance, 6 held

1. Near-diagonal for structural reasons — **held**, with the correction that the
   first matrix cut had to be redefined before the question was even askable.
2. Most core rules dead — **held** (38 rules, 0 fires).
3. `vision_waves` the one real cross-capability curve — **held** (14 co-loaded).
4. Step, not graded — **held** (every curve; four pure steps).
5. Low observability — **held**, and stronger than predicted (0/2, no vocabulary).
6. Reflexes are subroutines — **held**, via a route I did not anticipate.

## WHAT I GOT WRONG

1. **The first cross-capability matrix was vacuous by construction** — diagonal
   defined as "any file installing the seed" absorbed every effect and printed
   zero off-diagonal for all 25 seeds. Recut into OWN / CO-LOADED / UNRELATED.
2. **The observability probe shipped a DEAD READER** — `channels(w, anat)` and
   `gains(w, anat)` take the *bipolar* and *hcell* sub-maps; passing the whole
   `anat` dict iterates its two keys and returns an empty readout. Caught by the
   §1 smoke test before any verdict was taken off it.
3. **The marker regex matched the seeds' own documentation prose**, so every run
   would have scored SELF-EVIDENT — inverting Arm 4's result. Fixed by excluding
   documentation keys and requiring a value to be a single status token.
4. **The census crashed at the last hook** on `PanicException` (a poisoned Rust
   mutex), which is **not** an `Exception` subclass, so `except Exception` lost
   the whole census after all 200 tests had passed.
5. **My first Direction-2 summary counted every reflex instead of the targeted
   one** and reported "10 live" where the ablation had in fact worked. The
   per-reflex check corrected it; the table above is the corrected one.
6. **The first sweep ran with unpinned BLAS threads.** Rather than mix
   environments across configs, the whole sweep was discarded and re-run with the
   thread count pinned — an instrument that varies between configs is not one
   instrument.

## SCOPE — what is NOT shown (§8)

- **Coverage: 25 of 573 seeds (4.4%)**, selected by blast radius ≥ 2. 548 seeds
  (95.6%) are blast-radius-1 and structurally unauditable on this panel; ~575
  seed files exist in total.
- **15/20 bench files are seed-movable**; 5 install no seeds and no ablation can
  touch them.
- **The redundancy question has n = 1** (`vision_complex`). Everything else that
  showed no effect was dead or never co-loaded.
- **This rung cannot distinguish "genuinely redundant" from "decorative"** for
  `vision_complex`, `analysis_advance` or `reform_reflex`. That needs a vacuity
  toggle (§13.2), not an ablation.
- **Observability fraction rests on 2 degraded points.**
- **Arm 5 is the reading panel only.** This substrate has no vision reflex, so
  **nothing in Arm 5 transfers to vision or to VOR.**
- **Severity curves cover 6 seeds**; `vision_eye` (27 rules) and
  `shape_decode_loop` (17) got endpoints only — **capped sweep, logged here, not
  silently dropped**.
- Rule-firing counts are **panel-relative**: "dead" means dead *on this bench*,
  never dead in the agent.

## §9 / RESTORATION

Ablation is an **in-process manifest filter**; **no file under `seeds/` was ever
modified**, so restoration is exact rather than best-effort.

| check | result |
|---|---|
| `git status` over `seeds/` | **clean** |
| oracle `scripts/rung7_vision_bench.sh` | **200 passed, exit 0** |
| sd orbit law `{2:1,3:2,4:2,6:2,12:4}` | **unmoved** (`test_orbit_law_arithmetic_matches_the_measured_mint_counts` + `test_the_sd_orbit_law_is_UNMOVED`) |
| seed block | 59000/59001/59002 consumed; **59003–59999 CLEAN** |

### THE ENGINE MOVED UNDER ME MID-RUNG — §10/§11 caught it, exactly as designed

At the restoration check the shared engine read **`dce954bc788f` — "WRONG ENGINE,
built from DIFFERENT Rust source than this tree"**. A **concurrent agent rebuilt
the canonical tree's binary**, and this worktree's `_native.abi3.so` is a
*symlink into the canonical tree* (`ensure_tree_engine`, §10.1), so it changed
underneath me. My own tree added **no Rust** — `git diff dd174b95 -- runners/dsl/src
runners/dsl/Cargo.toml` is **empty**.

**No result is affected, and this is provable rather than assumed:** every result
file records `provenance_line()` at session end, and **all 190 of them
(135 + 29 + 26) report engine `985fb252ce41`.** The rebuild landed *after* the
last measurement. **This is precisely the hazard §10 exists to catch, and the
per-result provenance stamp is what turned "your numbers may be from two
engines" into a checkable fact.** Had I only checked the engine at the start and
the end, I could have concluded nothing.

Restored by **building this worktree's own engine from its own source** rather
than re-pointing at a foreign binary: **`e59484fe6b2e`**, provenance clean, in
this tree. The oracle above was re-verified on it. (A different *hash* from
`985fb252ce41` at identical *source* is expected — builds are not bit-reproducible
— and §10.1's invariant is **content, not location**: the check that matters is
`rust_source_fingerprint`, which passes.)

**Recorded for the supervisor, not actioned here (§11.4):** a worktree that
symlinks the canonical engine is exposed to any concurrent rebuild of it, silently
and at any moment. The per-result stamp makes it *detectable*; it does not make it
*safe*. A rung that started before such a rebuild and finished after it would have
straddled two engines with nothing but the stamps to reveal it.
