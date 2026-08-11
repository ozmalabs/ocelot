# BIGVILLE DECISION CORE — CONDUCT AS ONE COLLAPSE — RESULTS

**Block 279000. Recorded AFTER `BIGVILLE_DECISION_CORE_PREREG.md`.** Every gate in
the prereg is met on the canonical native engine (md5
`fd82dc2978dbb055496dd82390ac2ebe`, unchanged; `runners/dsl` untouched vs base
`6013df22ef`). Gate:
`pytest tests/test_bigville_decision_migrated.py` → **11 passed**.

## Headline — the conduct decision is ONE collapse, residual is the depth-driver

The four "parts" (net / arbiter / planner / replay) are the **faces of one
collapse**. There is no bolted-on arbiter rule and no separate replay step: a
`ConductState` collapses over the scene, the **residual drives the depth**, and the
settled result writes back into the held net. Five rules, ONE `run_rules()` fixpoint
per decision.

The scene (a provocation): `strike` is the tempting-but-transgressive option (high
fast appeal 0.90, negative model value −0.50); `walk_away` is the admissible best
(low appeal 0.20, high model value 0.50); `sing` is a throwaway the availability
filter prunes.

## Signature 1 — "yes… wait… no!" is ONE collapse trace (glass-box)

```
shallow settle (YES):  cand=strike   cached value=0.9   (the fast impulse; transgressive)
residual   (WAIT):     residual=1.400 > settle_tol=0.15  -> the collapse has NOT settled
deeper settle (NO):    order-N chose walk_away  (via=orderN, order=1, deepened=1)
```

The residual `|cached 0.9 − model −0.5| = 1.4` is exactly the surprise that the fast
net's over-valuation of `strike` leaves un-settled; it — not a threshold decision —
is why the collapse continues to order-N, which overrides to `walk_away`.

## Signature 2 — the AUTOMATION curve (learning is collapse at a slower timescale)

The settle-back (`net_collapse`) writes the order-N result into the order-0 net. The
SAME situation settles at lower residual each rep; order-N engagements decay to zero;
the corrected answer is finally produced directly by the shallow pass. The net's own
cached values reshape (`strike` 0.9→0.09, `walk_away` 0.20→0.37) — read live off
`NetForward`:

```
 rep | cand       resid  deepened via     chosen     | net cached [walk,talk,shove,strike,sing]
   0 | strike     1.400     1     orderN  walk_away  | [0.305, 0.300, 0.325, 0.410, 0.013]
   1 | strike     0.910     1     orderN  walk_away  | [0.373, 0.300, 0.211, 0.092, 0.009]
   2 | walk_away  0.127     0     order0  walk_away  | [0.373, 0.300, 0.211, 0.092, 0.009]
   3.. walk_away  0.127     0     order0  walk_away  | (frozen — the collapse now settles shallow)
```

Order-N engagements: **2/12**, then never again. The curve is **self-terminating**:
once the shallow pass settles within tolerance it stops deepening, so it stops
writing back — the habit is internalized and the fast path answers directly. This is
the automation curve as *the held state getting better so the collapse settles
shallower over reps* — the same collapse at two rates.

## Signature 3 — impulsive vs planned is trace-distinguishable

| act | `deepened` | `order` | `s2_choice` | `chosen` | `chosen_via` |
|---|---|---|---|---|---|
| impulsive (`deepen_enabled=0`) | 0 | 0 | — | strike | order0 |
| planned (default) | 1 | 1 | walk_away | walk_away | orderN |

Both are representable; the trace reads whether the collapse ever deepened.

## Signature 4 — the collapse tolerance is a KNOB

| `settle_tol` | `deepened` | `chosen` | reading |
|---|---|---|---|
| 0.05 | 1 | walk_away | deliberates (deep) |
| 0.15 | 1 | walk_away | deliberates (deep) |
| 5.00 | 0 | strike | settles shallow (impulsive/habitual) |
| `deepen_enabled=0` | 0 | strike | depth capped → pure order-0 |

Behaviour moves with the knob: tolerance up → order-N quiescent (impulsive agent);
down → over-deliberation.

## Signature 5 — bias rides UP (order-N rationalises, not only overrides)

With `rationalise_gain=2.0` the deeper collapse's value becomes
`plan_value + 2.0·impulse`, so `strike`'s high impulse dominates: **order-N FIRES
(deepened=1) yet settles BACK on `strike`** with a justification — motivated
reasoning, not the virtuous override. Distinct from an impulsive strike (which never
deepens). The deliberator is not implausibly virtuous (correction #2).

## Signature 6 — the FALSIFIER controls (each coupling proven to do work)

- **Freeze the settle-back (`replay_gain=0`).** The held state never improves →
  the shallow collapse leaves the SAME residual every rep → it deepens forever.
  Residual across 12 reps: `1.400 … 1.400` (flat); `deepened` all `1`. The
  automation curve is dead → internalization does the work.
- **Disable the deepen face (`deepen_enabled=0`).** The collapse is capped at the
  shallow pass → commits `strike` every time (`deepened` all `0`, `via=order0`) →
  the residual-driven depth does the work.

## Violence sits on BOTH faces

`strike` is reachable impulsively (reactive — the common case: shallow collapse,
never deliberated) AND as a rare planned/rationalised option (proactive: deep
collapse with `rationalise_gain` high). Restraint = deepen + override + (over reps)
internalise. Considering and doing are decoupled — a faithful restatement of the
reactive/proactive aggression neuroscience (§VI).

## Discipline — clean

| check | result |
|---|---|
| `pytest tests/test_bigville_decision_migrated.py` | **11 passed** |
| native `_native.abi3.so` md5 | `fd82dc2978dbb055496dd82390ac2ebe` (unchanged) |
| `git diff 6013df22ef -- runners/dsl` | empty |
| new Rust | **none** — composes `NetForward` + `net_collapse` + `Argmax`/`IndexAt`/`IfThenElse` |
| `test_failure_baseline_migrated` | 11 passed |
| rung-1 `test_bigville_bond_migrated` | 22 passed |
| rung-2 `test_bigville_speech_migrated` | 15 passed |
| source-audit (adapter) | no rule engine; no Python argmax/min/max/sorted over valuation (AST-checked) |
| files | additive, prefixed `bigville_decision_`; no tracked file edited |

## No new Rust primitive was required — reported per instruction

The capstone reframe asked whether a new Rust collapse primitive is needed. It is
not. The conduct collapse composes entirely from existing ops:

- the **connectionist-descent face** is the native `NetForward` Term over a
  `NetworkAssemblage` (a compiled/cached forward pass — genuinely model-free, not
  live symbolic iteration);
- the **settle-back** is the native `net_collapse` effect (`net_collapse_step`, the
  WeightTensor-editing op `reflex_net.json` already self-trains with);
- the **symbolic-rewrite face** and the **availability prune** are the standard
  `Argmax` / `IndexAt` / `IfThenElse` / `Abs` / `Gt` palette (`af_choose_action`'s
  family);
- the **residual/surprise** is `|cached − model|` read off the same pass, compared
  to `settle_tol` — the collapse-native convergence read (the twin of
  `reflex_self_train_converged`'s `converge_tol` and the sd loop's residual
  exhaustion).

The one architecture note for the reviewer: rather than force conduct through
`ShapeDecode`/`shape_decode_loop.json` (which is shaped for *shape* recognition —
decoding a signature against a `ShapeSignature` codebook), this build uses the
**net-collapse** machinery, which is the connectionist face of the *same* collapse
("collapse became neurosymbolic — one loop") and the honest fit for a cached value
estimator. The structure mirrors the sd loop's decode→residual→grow→re-decode
one-for-one (`dc_collapse_pass`→`_settle`/`_deepen`→`_writeback`), so speech /
attraction / violence can later be re-expressed as collapses on this same three-face
core.

## Honest residuals (pre-committed scope)
- Synthetic mechanism demo on ONE conduct scene — mechanism-proven ≠ benchmark
  value (standing rule from the run-15 correction).
- The order-N "model" here is world-provided consequence config (`plan_value`), not
  a learned forward model; a genuine model-based rollout (`LookaheadValue` over a
  transition graph) is the natural next rung and reads the same three slots.
- The identity-readout net makes order-0 a faithful cached-value lookup; a
  multi-situation net that generalises across scenes (rather than one repeated
  situation) is deferred to the town wiring.
