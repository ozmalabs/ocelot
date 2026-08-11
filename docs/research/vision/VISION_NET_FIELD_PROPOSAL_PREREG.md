# PRE-REGISTRATION — A SMALL NET AS THE PER-CELL FIELD PROPOSAL, UNDER A REFUSABLE VERDICT

*Block 133000–133999. Written and COMMITTED before any number (§3). Extends the
scale arc (131000 `VISION_SCALE_WALL_PUSH`, 132000 `VISION_SCALE_BULK_INGEST`) and
the refusal arc (129000 useful-wedge, 130000 `VISION_REFUSAL_NATURAL`).*

## 0. THE QUESTION (one, coherent)

The scale bottleneck named by 132000 is the **77% irreducible Rust per-cell field
compute** (batched drive 26% + wave relaxation 51%). The design under test — the
project's own net-economy / neurosymbolic-collapse, applied to the field — is:

- a **small conv net PROPOSES** the per-cell field update fast (the cheap primal
  path), self-supervised on the world's own dynamics ("learns by watching");
- the **substrate REFUSES on the RESIDUAL** — where the net is wrong, the exact
  engine recomputes;
- so exact (expensive) compute runs **only where surprise is high**
  (compute-∝-surprise), and the final field is correct.

**IS the substrate's per-cell field compute cheaply NET-PREDICTABLE, with a residual
that (a) CONCENTRATES, (b) is a CALIBRATED refusal/surprise gate, such that
exact-on-surprise REPRODUCES the exact field at a measured net speedup that grows
with scale — AND the residual beats net-confidence at flagging the net's own
errors?**

## 1. WHAT THE PER-CELL FIELD IS (measured, not assumed)

The "wave relaxation" (51% of the tick) is the **RetinaCell STATE field** evolving
under `seeds/vision_waves.json`: `wv_propagate` / `wv_refract` / `wv_recover`. Read
off the seed and VERIFIED against the engine (scratch positive control, 9 configs ×
60 steps byte-identical): the state field is a **radius-1, deterministic cellular
automaton** on `(state ∈ {rested,active,recruited,refractory}, activated_at,
fired_at)`, PLUS two exogenous inputs the adapter injects each step:

- **commit** (recruited→active), deterministic from the field;
- **ignition** (random rested→active, k=1 every 5 steps), EXOGENOUS entropy.

The `driven`/`lum`/`change` machinery (the 26% batched drive) does NOT enter the
state transitions — it feeds `bursting`→Unit learning, a separate channel. So the
STATE field's per-cell update is: `S_{t+1} = CA( commit+ignite( S_t ) )`, a local
deterministic rule + sparse exogenous ignition.

## 2. HYPOTHESES (two-sided; predicted directions have been wrong 4× in this arc)

- **H1 (predictability).** A small conv net (≤ ~5k params, ≤3 conv layers, ≥5×5
  effective RF) predicts `S_{t+1}` per-cell from `S_t`. Two-sided on ACCURACY and on
  RESIDUAL CONCENTRATION (errors sparse-and-structured vs diffuse).
- **H2 (compute-∝-surprise / speed & soundness).** Two-sided: (i) net-forward is
  cheaper per-cell than the engine tick and the advantage GROWS with grid size;
  (ii) a SOUND surprise gate (recompute exact where flagged → byte-identical field)
  yields a real speedup vs full-exact, OR it does not (byte-identity forces
  exact-nearly-everywhere). Reported against BOTH the engine AND a byte-identical
  vectorized-exact reimplementation (the "you did not need a net" control).
- **H3 (refusal wedge, the 129/130 way).** Two-sided: the substrate's residual (a
  COMPARISON — the net's proposal vs the held CA rule) flags the net's OWN errors
  BETTER / WORSE / SAME as net-confidence (a SELECTION — softmax margin), by paired
  bootstrap AUROC.

## 3. THE ARMS

Three implementations of the SAME state-field update, timed identically:

| arm | what | exact? |
|---|---|---|
| **ENGINE** | the committed `s.tick()` wave relaxation (waves-only boot) | exact (the substrate) |
| **NUMPY-EXACT** | vectorized reimplementation of the CA (verified byte-identical) | exact (control) |
| **NET** | small conv forward pass predicting `S_{t+1}` | approximate |
| **NET+GATE(sound)** | NET proposal + exact recompute on rule-violating cells | exact iff gate sound |
| **NET+GATE(conf)** | NET proposal + exact recompute on low-confidence cells | bounded error |

Refusal signals compared (H3): **net-confidence** = 1 − softmax-max (SELECTION);
**substrate-residual** = disagreement of the net proposal with the held exact CA
rule applied locally (COMPARISON — the AbS analogue: the substrate reconstructs the
lawful next-state and refuses where the proposal diverges).

## 4. STATISTICS, n, DECISION RULE

- **H1 statistic.** Per-cell next-state accuracy on HELD-OUT worlds; split into
  DETERMINISTIC cells (non-ignition) vs EXOGENOUS-ignition cells. Residual
  concentration = fraction of grid cells that are errors (median over steps) and the
  fraction of errors attributable to ignition. n = 10 held-out worlds (confirmatory
  seeds 133100–133109), ≥200 steps each, at grid 32. Fixed here.
- **H2 statistic.** ms/tick (median + bootstrap 95% CI, ≥7 trials/grid, machine
  ALONE, loadavg recorded) for ENGINE / NUMPY-EXACT / NET at grids
  {16,24,32,48,64,96,128,192,256}; log-log exponent + CI. Speedup ratios per grid.
  SOUND-gate: fraction of cells the sound gate must recompute (median over steps) and
  the resulting NET+GATE(sound) cost vs full-exact. CONF-gate: at matched recompute
  fractions {0,1,2,5,10}%, the residual error rate and the gate MISS rate (net-wrong
  ∧ not-flagged). Byte-identity is the gold standard; if unreachable, the bound + miss
  rate is the honest result.
- **H3 statistic.** Paired bootstrap (2000×, SAME resampled cells) on the AUROC of
  each signal for the binary label "net error at this cell", pooled over held-out
  worlds/steps; reported for ALL errors, DETERMINISTIC-only errors, and
  IGNITION-only errors, separately. `SEP+`/`SEP−` = 95% CI of the paired AUROC
  difference entirely above / below 0.
- **Decision rule / VERDICT.**
  - **CONFIRM** = predictable (H1 high acc) + residual CONCENTRATES + a SOUND gate
    reproduces the field at a MEASURED net speedup that GROWS with scale AND beats
    NUMPY-EXACT + comparison beats net-confidence (H3 SEP+). Both frontiers hit.
  - **DEGRADE** = predictable but residual diffuse, OR byte-identity forces
    exact-nearly-everywhere, OR the net speedup is real but does not exceed the
    byte-identical NUMPY-EXACT (the net buys nothing a specialized exact kernel does
    not), OR modest. Name the limiting facet.
  - **FALSIFY (first-class)** = the field is NOT cheaply net-predictable, OR the
    residual is not a usable gate → the net-proposal design does not help this compute.
    Prove it and name what would change it.
- **A null means:** for DEGRADE/FALSIFY, the honest boundary is the result; I do NOT
  rescue by tuning the net, the gate threshold, or by quietly dropping byte-identity.

## 5. EXACTLY THESE TESTS. NO SWEEPS.

(1) H1 accuracy + concentration on 10 held-out worlds. (2) H2 timing sweep + the two
gates. (3) H3 paired-bootstrap AUROC. Net architecture, training length, and channel
encoding are FIXED in the instrument before the confirmatory run (pilot on training
worlds 133000–133003 only). The CONF-gate thresholds fall out of the in-distribution
residual distribution on TRAIN worlds (§13), never tuned on held-out worlds. A
further attempt needs a NEW prereg with a NEW mechanism-level hypothesis.

## 6. MY PREDICTION, IN ADVANCE (with provisos — §3.7)

I predict **DEGRADE**, shading toward a FALSIFY of the specific "small net attacks
the wave per-cell compute" premise, for these reasons:

1. **Predictability will be HIGH — but this is FORCED (§13.1), not a risky win.** A
   radius-1 deterministic CA is expressible by a 3×3 conv by construction; a local
   net predicting a local rule is a tautology with error bars. The residual will
   CONCENTRATE — also forced, because the only unpredictable input (ignition) is
   spatially sparse by construction. I will NOT claim these as evidence for the
   design; I will name them as forced.
2. **The net will be DOMINATED by NUMPY-EXACT.** The CA is a KNOWN rule; a
   vectorized-exact kernel is byte-identical AND (I predict) at least as cheap as a
   conv forward pass, needing no training, no gate, no error. The net-proposal
   design's payoff requires an UNKNOWN/complex per-cell update; the wave CA is not
   one. **Proviso that would break this:** if at large scale the conv net's fused
   kernels are measurably cheaper per-cell than numpy's boolean-array temporaries,
   the net could beat NUMPY-EXACT on raw speed (it would still be approximate).
3. **The SOUND gate will give ~no speedup.** For a cheap local CA the rule-violation
   CHECK costs about as much as the exact COMPUTE (both are the same 3×3 local op),
   so "flag then recompute" ≈ "recompute everywhere". **Proviso:** if the check is
   materially cheaper than the full relaxation, a sound speedup is possible.
4. **The refusal wedge (H3) will REPRODUCE 129/130 (comparison ≫ selection) but
   DEGENERATELY**, because the substrate holds the EXACT generator, so its comparison
   is ground truth and flags deterministic errors ~perfectly while confidence is
   confidently-wrong. The honest floor: EXOGENOUS ignition is unrefusable by BOTH
   (a random draw violates no rule) — you can refuse a rule-violation, not an
   unpredictable draw.
5. **The representation frontier is UNTESTED here** — the wave state field has no
   rich learned representation, so this rung speaks to SCALE and to the mechanism,
   not to the representation deficit 130000 named.

If instead the net beats NUMPY-EXACT at scale AND a sound gate gives a growing
speedup AND H3 is SEP+, that is CONFIRM and my prediction was wrong — reported as such.

## 7. DISCIPLINE

- The net is a MEASURED host-side proposal mechanism (torch), admissible like
  130000's CNN baselines — NOT agent logic. The surprise-GATE decision is a
  COMPARISON the substrate makes; productionizing it is a seeded surprise-gate rule +
  net-as-graph-data ([[net_economy]] precedent, `seeds/net_economy.json` /
  `seeds/reflex_net.json`), NOT built here. The EXACT engine path stays UNCHANGED and
  default (§9). No agent DECISION in Python.
- Likely NO Rust, NO seed (a measurement). Provenance is its own step; engine built
  with `scripts/engine_build.sh`; `provenance_line()` printed from inside the
  measuring process; `source_match ∈ {own,shared}` asserted (never a literal hash).
  Oracle `rung7_vision_bench.sh` 222/0 BEFORE and AFTER.
- Timing rigor: run ALONE; loadavg start/end; ≥7 trials; median+CI; governor stated;
  net train cost recorded as DATA, not a verdict. torch threads pinned. Verify on the
  product (`native.evaluate()` returns TUPLES). Block seeds recorded.

## 8. `check_claim` OUTPUT (§3 clause 8 — verbatim)

```
$ python3 scripts/seed_claim.py 133000 133999
SEED CLAIM 133000-133999: CLEAN -- no collision DETECTED.
  Scope: 840 files with seed sinks; 561 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

unresolved sinks = **561**, priced. Block seeds planned: train worlds 133000–133003;
CONFIRMATORY held-out worlds 133100–133109 (never used for training/tuning); net
weight init 133500; bootstrap RNG 133600.

## 9. PROVENANCE (this run)

- branch: `worktree-agent-ab81112c9046769e5`; base HEAD `cf6c95f360`.
- engine: built `scripts/engine_build.sh` → `own` `7c2aaa41748f` (asserted in-process;
  re-verified after the run). No Rust change intended.
- oracle BEFORE: `rung7_vision_bench.sh` **222 passed, 0 failed**
  (`var/oracle_before_133000.log`), `data/` symlinked.
