# Humanoid successive-lifetime improvement results

## Verdict

The frozen four-lifetime comparison **CONFIRMS** safe, persistent behavioral
improvement from graph-native motor-program reuse.

| Lifetime | Accumulating progress (m) | Fresh progress (m) | Saved programs | Fall |
|---:|---:|---:|---:|:---:|
| 1 | 0.2357789727 | 0.2357789727 | 3 | no |
| 2 | 0.2910149112 | 0.2357789727 | 3 | no |
| 3 | 0.2910149112 | 0.2357789727 | 3 | no |
| 4 | 0.2910149112 | 0.2357789727 | 3 | no |

The final paired gain is 0.0552359385 m, or 23.4%. Mean accumulating
progress rises from 0.2633969420 m in lifetimes 1–2 to 0.2910149112 m in
lifetimes 3–4. Final absolute lateral drift improves by 0.0302515278 m.
Every arm remains upright. The four fresh controls are bit-identical on the
preregistered behavioral signature, while each warm lifetime recalls three
shape-indexed combined actions.

The authoritative machine-readable result is
`results/humanoid_lifelong_improvement_v1_verified.json`. Its exact bounded
slow store is
`results/humanoid_lifelong_motor_library_v1_verified.json`.

The final rules also pass the 600-action walking regression with a mid-run
force perturbation. The directed arm reaches 0.9516118546 m with 0.0782386739
m lateral drift, six aerial samples (limit ten), 194 support alternations,
and no familiarization or evaluation fall.

## What had been broken

The first frozen run was a clean **DEGRADE**: every accumulating and fresh
lifetime produced exactly 0.1308496205 m. The graph recognized the body
shape, but most reusable structure was excluded from persistence and recall.

Several apparently promising fixes were also falsified:

- broad singleton persistence produced negative transfer;
- allowing memory to act during familiarization caused a late fall at action
  195;
- one-shot compound storage retained lucky, irreproducible receipts;
- a safety-valid intermediate curve improved lifetime two but regressed
  thereafter;
- pruning combined actions by individual receipt destroyed a repertoire whose
  joint embodied trajectory was better;
- persisted episode-local consolidation sequence numbers made later
  boundaries look already processed;
- resetting receipt markers at the old episode boundary replayed old trials
  and re-inhibited restored programs.

The retained negative artifacts make those failures auditable:

- `results/humanoid_lifelong_improvement_v1.json`
- `results/humanoid_lifelong_improvement_v1_fixed.json`
- `results/humanoid_lifelong_improvement_v1_safe.json`

The lifetime-two gain alone was not accepted as evidence. The result became
confirmed only after lifetimes three and four independently reproduced it
against deterministic fresh controls and the long safety regression passed.

## Graph-native correction

The final mechanism is a two-timescale, repertoire-level motor memory:

1. Analysis by synthesis still creates arbitrary combined actions from the
   current actuator graph.
2. Exact mechanical receipts provide directed task value as
   `heading × (post_x - pre_x)`. Graph rules compute uncertainty, eligibility,
   ranking, and rollback.
3. Singleton habits remain lifetime-local. Only coordinated multi-actuator
   programs can enter the body-shape library.
4. Novel compounds are explored at a cadence derived from the sensory
   confirmation count. Unsafe surprise inhibits the specific program without
   exponentially suppressing every other combination.
5. A compound must have positive body-normalized value and model uncertainty
   below that value before it can be shape-indexed.
6. Warm priors cannot directly act during phase-model familiarization.
7. Fast working fields adapt within a lifetime; nineteen consolidated fields
   preserve the slow prior.
8. Individual chunks may be inhibited immediately, but boundary selection
   retains or rolls back the held repertoire according to whole-lifetime
   embodied progress. This preserves interactions whose value exists at the
   trajectory level.
9. Request and consolidation markers reset only when the program activates in
   a genuinely new episode. They are not reset while old receipt nodes remain
   reachable.
10. Mechanical support facts disambiguate contact from flight. Novel compound
    release requires at least one active support and reserves a
    support-sensor-derived share of the configured lateral safety envelope.

The serializer remains mechanical. It copies graph-selected
`shape --stores_humanoid_motor_program--> program` facts and signals an
episode boundary; it does not select actuators, score programs, or decide
retention.

## Remaining ceiling

The curve demonstrates transfer and stable reuse, not unbounded improvement:
after the exploration cost in lifetime one, the selected three-program
repertoire plateaus. The next experiment should add graph-native mutation and
competition among whole repertoires so a stable best can seed new variants
without being overwritten.

The Python/PyBullet validation harness is also slow because it repeatedly
settles full graph fixpoints and physics trials. That wall-clock runtime is
not the controller response-time floor, but indexing exact program/context
matches is still a worthwhile deployment optimization.
