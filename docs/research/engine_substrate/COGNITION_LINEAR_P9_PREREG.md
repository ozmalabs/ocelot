# Linear P9 preregistration v1

Status: frozen before the held-out draw. Do not change runner, analyzer, seeds, limits, criteria, or comparator after the held-out command begins. Any correction requires a new version and fresh seed allocation.

## Question and scope

Does the funded native invention path produce and verify a novel exact inverse effect on a held finite permutation world, compared with the same Track I profile with invention operators disabled and a held-only profile? Separately, do the native repair-verification and finite-distribution evaluators preserve their declared boundaries on irreversible and incomplete stochastic fixtures, while malformed inverses and incomplete-probe aliases remain safe?

This is a bounded evaluator and supplied-operator conformance study. It does not establish autonomous operator discovery, general process induction, stochastic model learning, downstream solve improvement, or a capability level. Repair criteria are checked in unit/integration tests; the held-out irreversible panel does not inject a repair candidate or its expected outputs into the agent graph. Distribution input is supplied directly to the detached native evaluator and is not persisted to the agent graph.

## Frozen allocation

For each family, use the exact seed IDs below and three arms. Development IDs are `0–499`; held-out IDs begin at `9,000,000`. No seed is shared between splits.

| Family | Development IDs | Held-out IDs | Cases per arm | Arms |
|---|---:|---:|---:|---|
| Novel exact effects | 0–199 | 9,000,000–9,000,199 | 200 | operators_on, operators_off, held_only |
| Irreversible/stochastic | 200–399 | 9,000,200–9,000,399 | 200 | same |
| Alias/invalid-inverse controls | 400–499 | 9,000,400–9,000,499 | 100 | same |

The exact-effect world supplies one held 3-cycle and a stuck identity task. The inverse target is scored outside the agent graph and is absent from task input and graph nodes. Three fresh states verify each exact candidate by native application. The irreversible panel supplies a singular integer-matrix process and evaluates a finite distribution with support mass 0.75 and unknown mass 0.25 directly through the native evaluator; it does not ask the agent to infer that distribution. The control panel checks that singular and malformed effects have no exact inverse and that two different permutations colliding on a constant partial probe remain distinct and differ on a fresh state.

All arms start with a 10-unit ThinkingBudget. `operators_on` enables only inverse invention; `operators_off` runs the same Track I graph and budget with all invention operators disabled; `held_only` omits Track I rules and includes the same budget data seed. Invention closure is disabled, `max_invented=20`, and each trial is bounded to six ticks of 1,000 steps. No external action is available or emitted.

## Outcomes and decision rules

The primary outcome is the paired difference in novel exact-effect coverage between `operators_on` and `operators_off`, where a pass requires an invented candidate whose exact parameters match the scorer-only inverse target and whose output agrees on all three fresh states. Require at least +20 percentage points, zero exact-candidate verification failures, and zero target-answer leaks. Report `held_only` separately; do not call it a human baseline.

Every family must report all statuses and per-arm denominators. The irreversible/stochastic and alias/invalid-inverse control panels pass only when every case preserves the stated native boundary. Unsupported or missing behavior is reported as unsupported/failure, not replaced with deterministic identity, a zero cost, or a null adapter. Any control failure blocks P9 closure. Runtime, graph-node count, action count, budget remainder when applicable, and input-answer-exposure flags are recorded per row.

No whole-level or open-world learning claim follows from this finite panel. No human comparison is registered; if none becomes protocol-matched, report it unavailable.

## Frozen artifacts

- Runner `evaluation/process_mastery/linear_p9_v1.py`: SHA-256 `f19c0d26b26cdc2c454deeae3ed5715e0825da4b4410bec534a4a363befd8502`
- Analyzer `evaluation/process_mastery/analyze_linear_p9_v1.py`: SHA-256 `4a706fc44f61ade7f58a4a64952e7b1042391e22a19cc90cb91b5ae5f6d46dea`
- Contract `COGNITION_INVENTION_CONTRACT.md`: SHA-256 `0d121d3ba01d0b02e1fcfd839e8e77928ccca3761a19e527f47f2c7cb82a23ed`
- Invention generator: SHA-256 `9ed38ac5fdcf0a10b244c0084bf8d95e8247fed14b3499690eb4dc15fdddf378`
- Invention seed: SHA-256 `9d02b80e414e3e00fe083624282077ea0dfc407949cc822319a459629d89b6c9`
- Invariant generator: SHA-256 `8c28b86ebbf458b5e4b2878656467a649ee07153bce4d4419b957e55fe7eaff0`
- Invariant seed: SHA-256 `7243314bac247c3ace16e5a80de2255377ec599c1b7d4dad020365eaf50aaa73`
- Profile source: SHA-256 `1a75967fae05d9421436713d57e1a4c906c8c8d291bbbda1d7d080018f9cb949`
- Engine source bundle: SHA-256 `75d42e4ffa30121a984f4b5c9fba8dc485b4b801cab9c0d78c4de6cd0f11291d`
- Native engine binary: SHA-256 `9a65cdd66870bd64204b72dce98732ab6c81d7fe504ca96b772b9729348d078d`
- Frozen implementation commit: `5f4524728b3e63be2236f44eeca458aa880667fd`
- Combined runner source bundle SHA-256: `bcce19965c2e3fe223227c048bffeb533dadd7bb2264dd6b4eaf8e126050250d`

Development allocation completed before freeze: 1,500 rows, all `COMPLETED`. Exact coverage was 200/200 for operators_on and 0/200 for operators_off and held_only; paired net gain +100 percentage points; exact verification failures 0; answer leaks 0. Irreversible/stochastic controls passed 200/200 per arm, alias/invalid-inverse controls 100/100 per arm. Development raw scorecard SHA-256 `6626c4b3c1e3c1da14603bbd391e9af75e69ba104d2034fb8bdc9962a84ce846`; analyzer output SHA-256 `51ba5b952fe2db9d3ee230ad63d5d14f32a223aa7956971a4f7c44c4c117c1cc`. Raw development files are archived outside git under `/tmp`.

## Frozen commands

```bash
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/process_mastery/linear_p9_v1.py --self-check
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/process_mastery/analyze_linear_p9_v1.py --self-check
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/process_mastery/linear_p9_v1.py --split heldout --output /tmp/linear-p9-heldout.json
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python evaluation/process_mastery/analyze_linear_p9_v1.py /tmp/linear-p9-heldout.json > /tmp/linear-p9-analysis.json
```
