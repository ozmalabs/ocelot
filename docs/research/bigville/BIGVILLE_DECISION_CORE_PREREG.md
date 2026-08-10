# BIGVILLE DECISION CORE — CONDUCT AS ONE COLLAPSE — PRE-REGISTRATION

**Block 279000. Pre-registered BEFORE any recorded number.** Design blueprint:
`BIGVILLE_DUAL_PROCESS_SCIENCE.md` — the validated verdict is *"ON TRACK on the
frame; build against MODEL-FREE / MODEL-BASED RL"* (§V.2.2), with three required
corrections (§V.3). This is a STANDALONE mechanism-demo (the way rung-1
`BigvilleBondWorld` proved the Bond in isolation) — it does NOT wire the full town.

## The capstone reframe this build is aimed at (creator's directive)
> "The missing piece that brings it all together is the collapse."

The conduct decision is NOT four separate mechanisms (net + arbiter + planner +
replay). It is the substrate's **ONE collapse** operation applied to conduct — the
same collapse the eye/perception and the sd loop already run — and the four are the
**faces of one collapse**, with **RESIDUAL as the depth-driver**:

- **Order-0 (net) = the shallow collapse** — the held conduct state settling in one
  fast pass (the connectionist-descent face).
- **The RESIDUAL *is* the arbiter** — no separate "should I escalate?" decision. A
  collapse that has not settled HAS residual; residual = surprise; surprise drives
  the collapse to continue. Un-settled ⇒ keep collapsing to higher order.
- **Order-N (planner) = the collapse continuing to higher order** — the
  symbolic-rewrite face, which runs ONLY BECAUSE the shallow pass left residual.
- **Replay / internalization = the collapse settling back into the held state** —
  the settled result becomes the new prior/net, so next time the shallow pass
  settles it directly. This is *learning is collapse at timescales*: fast collapse
  (per-decision) and slow collapse (over reps) are the SAME collapse at two rates.

"One principle, two implementations" because these are the two faces collapse
**always** has (connectionist descent AND symbolic rewrite in one loop), not two
systems of different kind. This lands the substrate on the winning side of the
fifteen-year dual-process debate (§V.2.1) and equals model-free / model-based RL
(§V.2.2).

## Seed-claim (verbatim `seed_claim.py 279 279`, run before anything)

```
SEED CLAIM 279-279: CLEAN -- no collision DETECTED.
  Scope: 981 files with seed sinks; 704 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from one generator ... measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots; unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS 'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## The mechanism (graph-native, ZERO new Rust) — `seeds/bigville_decision_core.json`

ONE collapse loop, five rules, ONE `run_rules()` fixpoint per decision. The
substrate's EXISTING collapse machinery is the spine — the native `NetForward`
(the connectionist forward pass) and `net_collapse` (the weight-settling op, the
same op `reflex_net.json`'s self-training uses), composed with the `af_choose_action`
Argmax family. **No new Rust primitive was required** (report below).

A held **`ConductState`** (`m`) collapses over a scene of **`DecAction`** options.
Each option carries `impulse` (fast appeal — the situation's pull), `plan_value`
(the world's grounded consequence/model value), and `is_transgressive`. The order-0
net is a `NetworkAssemblage` (identity readout: `NetForward(input_vec) = ReLU(x) = x`
initially, so the cached fast value IS the appeal) wrapped in a `ReflexNet` so
`net_collapse` can retrain it.

- **`dc_collapse_pass`** — THE SHALLOW COLLAPSE (order-0). The cached `NetForward`
  value over the availability-filtered consideration set picks the fast candidate;
  the **residual = |cached value − grounded model value|** (surprise) is read off
  the same pass. Pruning (the consideration set — correction #3) lives here as a
  raw-appeal availability filter. Sets `order=0`.
- **`dc_collapse_settle`** — SETTLED SHALLOW. The residual IS the arbiter: a
  collapse whose residual is within `settle_tol` HAS settled → commit the held
  candidate directly (`order0`, `deepened=0`). Also settles here when depth is
  capped (`deepen_enabled=0`). The impulsive / automatic path.
- **`dc_collapse_deepen`** — THE COLLAPSE CONTINUES to higher order (order-N),
  and runs ONLY BECAUSE residual exceeded `settle_tol`. A model-based Argmax over
  the consideration set by `plan_value + rationalise_gain·impulse`. `rationalise_gain=0`
  → corrects (override); high → settles BACK on the impulse with a justification
  (motivated reasoning rides UP — correction #2). Arms the settle-back.
- **`dc_collapse_writeback`** — INTERNALIZATION. `net_collapse` writes the settled
  order-N result into the order-0 net toward the model-value target, so the shallow
  pass settles it directly next time — the automation curve (MB→MF replay).
- **`dc_collapse_no_writeback`** — the frozen-internalization complement (falsifier).

Two coupled knobs (correction #1): **depth** (`order`) × **precision** (`settle_tol`,
the collapse tolerance). Residual — not a bolted-on threshold — drives depth; the
scalar residual is logged (not a bit); **no depletable-willpower term** (ego
depletion failed replication — §V.1.4). The arbitration rule is a swappable measured
knob per Kool et al. / Daw et al. (§V.2.2), not a hardcoded threshold.

## The adapter — `worlds/bigville_decision_world.py` (mechanical I/O only)
Mints the net / held-state / options, provides the world's appeal (`input_vec`) and
consequence model (`target_vec`) as config (exactly as `af_choose_action`'s
`base_value`/`grief_affinity` are Action config), arms, ticks, reads. No Python rule
engine; no if/else over an agent's graph valuation; conditionals are over
world/config state only (source-audited by the test).

## Pre-registered gates (`tests/test_bigville_decision_migrated.py`)

- **SIGNATURE 1 — "yes… wait… no!" as ONE collapse trace.** Shallow settle picks
  the tempting transgressive `strike` (yes); its residual exceeds `settle_tol`
  (wait, not settled); order-N overrides to `walk_away` (no). The three stages + the
  driving residual are all in the trace.
- **SIGNATURE 2 — the AUTOMATION curve.** Repeat the same situation; the settle-back
  writes the order-N result into the net; residual shrinks and order-N engagements
  decay to zero; the corrected answer is finally given directly by the shallow
  order-0 pass. Residual monotone non-increasing.
- **SIGNATURE 3 — impulsive vs planned trace-distinguishable.** An impulsive act
  (collapse never deepened) and a planned act (deepened) are both representable and
  distinguished by `deepened`/`order`/`s2_choice`.
- **SIGNATURE 4 — the collapse tolerance is a KNOB.** `settle_tol` up → settles
  shallow every time (impulsive/habitual, order-N quiescent); down → deepens.
- **SIGNATURE 5 — bias rides UP.** `rationalise_gain` high → the deeper collapse
  settles BACK on the impulse with a justification (order-N FIRED yet chose
  `strike`) — not the virtuous override.
- **SIGNATURE 6 — FALSIFIER controls.** Freezing the settle-back (`replay_gain=0`)
  → flat automation curve (residual constant, deepens forever). Disabling the
  deepen face (`deepen_enabled=0`) → pure order-0 (impulsive every time). Each
  coupling proven to do work.
- **Violence on both faces** — `strike` reachable impulsively (reactive, shallow)
  AND as a rare planned/rationalised option (proactive, deep); considering and doing
  decoupled.
- **G-source-audit** — the decisions are RULES: the seed holds the five `dc_collapse_*`
  rules + `NetForward`/`net_collapse`/`Argmax`; the adapter has no rule engine and
  no Python argmax/min/max/sorted selecting a conduct (AST-checked).
- **G-discipline** — base `6013df22ef`; `git diff 6013df22ef -- runners/dsl` EMPTY;
  native `_native.abi3.so` md5 == `fd82dc2978dbb055496dd82390ac2ebe`; no committed
  `.so`; `test_failure_baseline_migrated` green; rung-1 bond + rung-2 speech green.

## Tunable knobs (declared config — the DIRECTION is the science, the magnitude is soft)
`consideration_threshold=0.05` (availability prune), `settle_tol=0.15` (collapse
tolerance / precision knob), `deepen_enabled=1` (falsifier→0), `rationalise_gain=0`
(correction #2, ≥0), `replay_gain=1` (falsifier→0), `replay_eta=0.35` (settle-back
rate). All are graph attrs read by the rules.

## Honest scope (pre-committed)
Synthetic mechanism demo (a single conduct scene of 4 contenders + 1 pruned
throwaway, NOT the full town) — mechanism-proven ≠ benchmark value. This is the
DECISION CORE that speech / attraction / violence will later be re-expressed as
collapses on; the three faces (order-0 net, residual-driven depth, order-N + settle
back) are kept clean and composable. Additive only: new
`seeds/bigville_decision_core.json`, `worlds/bigville_decision_world.py`,
`tests/test_bigville_decision_migrated.py`, this prereg,
`BIGVILLE_DECISION_CORE_RESULTS.md`. NO tracked file edited. ZERO new Rust.
