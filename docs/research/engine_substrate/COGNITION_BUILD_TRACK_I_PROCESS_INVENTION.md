# Cognition build — Track I: process understanding and invention, to human level and beyond

Parent plan: `COGNITION_BUILD_PLAN_20261010.md`. The task template and tiering are defined in its §3, and the ground rules in its §1 apply here unchanged.

Track I runs alongside Phases 3–6. It does not replace them. It is the part of the plan aimed at matching, then exceeding, human ability to **understand how processes work and to build new ones**.

## 0. What "human and beyond" means here

"Theoretical capability" in this plan is a claim with two parts:

1. **Mechanism.** For every component of the process-mastery loop in §1, the substrate holds a graph-native mechanism. A Rust Term counts as a primitive; a seed rule counts as a decision.
2. **Evidence.** That mechanism passes a **held-out, pre-registered** test with a **human baseline** taken from published studies or collected for the purpose.

Passing a test with a hand-built fixture shows only that a mechanism exists. Phase 1's results (`COGNITION_BUILD_P1_RESULTS.md`, all measures 1.000 against 0.000) are tests of that kind. They are necessary, but they are not capability evidence. Every Track I gate therefore needs randomised, held-out instances.

"Beyond human" is defined only as specific measurable outcomes (§6, level L7). It is never a general claim. None of this is a claim of general intelligence. The known limits — open-world perception, breadth of embodiment, breadth of language and compute — are recorded in §8.

## 1. The process-mastery loop (what humans do, and what the substrate needs)

| Level | Human ability | Needed mechanism | Existing pieces | Gap |
|---|---|---|---|---|
| **L0 Execute** | Run a known procedure | Held processes | Program IR + ProgEval, CapabilityProgram, TransitionHypothesis, DimensionGenerator, motor programs, FamilyPrograms | Six unconnected representations |
| **L1 Understand** | Work out how a black box works; explain it; know whether you actually understand it | Lifted transition induction, latent-state invention, choice of experiments to discriminate hypotheses, an explain-and-rebuild check, invariants as laws | GWM transitions (flat), DimInfer/TimeInfer, `experimentation_core`, `remote_causal` do-contrast, `theorem_core`, `language_production` self-monitor round-trip | No lifted schemas, no hypothesis portfolio, no test of understanding |
| **L2 Invent** | Build a new procedure from known ones | Process algebra (inverse, compose, conjugate, commutator, power, root); walls explained by invariants | Probe `drafts/process_algebra/process_algebra_probe.py`; `needs_tool` → `self_extension` | Nothing graph-native |
| **L3 Accumulate** | Expertise: chunks, tricks, abstractions | Lift inventions to schemas; library learning by description length; a library of strategies | Codebook minting (`sd_mint_*`), `ps_accept` caching (stored per item, never refactored), `operator_authorship` | No compression or refactoring of solved work |
| **L4 Transfer** | "This is like that" | Conjugation across domains; structure mapping; recall by similarity | `analogy_search` (Python, single pass), P4 recall Term | No frame maps between domains |
| **L5 Invent for goals** | Design a tool for a purpose; choose a better representation | Goal regression over schemas; targeted invention ("find a process with effect E"); representation search scored by description length | P5.E4 planner (planned), order-3 reframe, aperture frames | No interface-driven invention |
| **L6 Acquire socially** | Learn from instruction and demonstration; teach others | Instruction → schema, demonstration → schema, explanation for others | `instruction_understanding`, P6.F3 (planned), production stack | No schema output |
| **L7 Beyond** | — | Inventing new invention operators; very large hypothesis portfolios; processes that ship with proofs; open-ended self-curriculum | `AreaParallel` cycle plan, `theorem_core`, prediction-world curricula, `adoption_safety` | All absent |

## 2. Evidence that started this track

The probe `drafts/process_algebra/process_algebra_probe.py` is a Python exploration, not agent code. It uses four invention operators that need only *compose* and *inverse*. Candidates are deduplicated **by effect**, and the cheapest expression for each effect is kept. Each candidate is scored on novelty, precision (how many cells it touches) and cost.

- **Loopover 3×3.**
  - 12 held moves gave 144 precise invented tools in one round.
  - Conjugating those by setup moves covered 168 of 168 possible 3-cycles.
  - Scrambled boards solved: 40/40 with the invented tools, against 8/40 for depth-5 search over primitives.
- **Loopover 4×4.** Commutators gave 128 tools, which closed to 1120 of 1120 3-cycles. Solved: 20/20, against 0/20 for depth-4 primitive search.
- **Lifting.** `[R_i, C_j]` moves exactly 3 cells for every i, j and every size from 2 to 5. The invention is a schema, not an instance.
- **An invariant explained a wall and fixed it.** On 4×4 boards with odd-length scrambles, the invented 3-cycles solved 0/20. All of them have even parity, while a row shift is odd. Adding one odd held move first, chosen by that same invariant, solved 20/20.
- **The substrate's own generators.** rotation90, reflection_r and reflection_c closed to the full dihedral group: rot180, rot270, transpose and anti-transpose were all invented. Laws were found too: rot⁴ = I, reflections square to I, and conjugating a rotation by a reflection reverses it.

Caveats:
- These are toy, invertible domains.
- Commutators are a known human technique.
- The piece-placement strategy was hand-written.
- The primitive baseline was a shallow search.

Track I exists to remove each of these caveats in turn.

## 3. Design principles

1. **A process is known by its effect.** Two descriptions with the same effect are the same process, and the cheaper one is kept. Effects are compared through an **effect fingerprint**: the process's behaviour on a fixed battery of probe states. This is what makes deduplication, novelty and library learning possible across every representation.
2. **Invention operators are data.** Each operator is an `InventionOperator` node: an expression template over `Compose` and `Inverse`, with a yield record. That lets the agent count, select and eventually author its own operators (I7).
3. **Walls are explained before they are fought.** When a whole family of tools cannot reach a target, search for an invariant the family preserves, then add a held process that changes it.
4. **Irreversibility is the normal case.** Real processes rarely have an exact inverse. Where an inverse is missing, the operators substitute a **repair** (a held process returning to a state with the same fingerprint), or compute effects in **imagination** (the detached GWM).
5. **The graph decides; Rust supplies primitives; Python stays mechanical.** The probe is a specification, not an implementation.
6. **Every invention is budgeted and gated.** Invention rounds draw on `ThinkingBudget`. Any invented process that acts externally passes through the future-manifold commit boundary (`CLAUDE.md`, "Engine-wide decision and risk boundary"). Changes to the invention machinery itself go through `adoption_safety` and human-gated criterion proposals.

## 4. Phases

Each phase ends with a gate (§7). "Det." marks phases still to be detailed into tasks with the §3 template. The parent plan's practice applies: detail a phase only after the previous phase's results doc is written.

### I0 — Evaluation first, and a shared schema decision

| ID | Work item | Touch | Tier |
|---|---|---|---|
| I0.1 | **Process Mastery Battery (PMB) v1 spec.** Task families per level, each with a held-out split, randomised instance generators and a source for its human baseline. The families: (a) permutation puzzles (Loopover N×N, a 2×2×2 cube, sliding puzzles), where human macro lengths and solve rates are published; (b) black-box mechanism discovery (blicket-detector–style causal machines, rule-induction games), where developmental studies give baselines; (c) ARC-style grid transformations (ARC/LS20 already in the tree); (d) tool invention: composing held tools for a new goal in a gridworld; (e) program synthesis on held-out MBPP-style specs (existing); (f) explain-and-rebuild fidelity; (g) cross-domain transfer pairs; (h) law rediscovery from simulated data | `docs/research/engine_substrate/PMB_V1_SPEC.md`, `evaluation/process_mastery/` | T1 |
| I0.2 | **PMB harness skeleton.** Instance generators, held-out seeds, a scorecard writer and a human-baseline table with citations. Families (a) and (c) are implemented first | `evaluation/process_mastery/{generators,harness,scorecard}.py` | T2 |
| I0.3 | **Baseline scorecard of the current substrate**, with no Track I code. This is the starting line | results doc | T3 |
| I0.4 | **Shared `ProcessSchema` decision with the Phase 3 session.** P3's relax/re-admit executor and Track I both need one candidate-process representation. Agree on the node type and attributes (§I1.1) before either side builds on it | design note in this doc + P3 doc cross-reference | T1 |

### I1 — Process schema and effect fingerprints (foundation for everything later)

| ID | Work item | Touch | Tier |
|---|---|---|---|
| I1.1 | **`ProcessSchema` node.** It holds: `kind` (permutation, integer matrix, program, transition, capability, motor); `params`; `pre` / `post` as Terms; `invariants`; `cost`; `provenance` (held, invented_by:op, lifted, induced); `fingerprint`; and an edge `-realised_by->` to the native representation. Nothing is migrated. Each existing form gets a **view rule** that mints its schema | new `seeds/process_schema.json` + generator | T1 spec, T3 |
| I1.2 | **Rust primitives:** `ProcessCompose{a,b}`, `ProcessInverse{a}` (exact for permutations, unimodular matrices and declared-invertible programs; `None` otherwise), `ProcessApply{p, state}`, `EffectSupport{p}`, `EffectFingerprint{p, probes}`. They dispatch on the value kind: tuple permutation, matrix, Term-program through ProgEval, or transition lookup | `term.rs` + the full binder checklist (P2 plan §P2.C1) | T1 spec, T2 |
| I1.3 | **Probe battery per domain.** A fixed set of probe states held as graph data. For programs, these are example inputs; for transitions, observed states | seed data + generator | T3 |
| I1.4 | **Dedup by effect, keeping the cheapest.** A rule merges schemas with equal fingerprints and keeps the one with the lowest cost | `process_schema` rules | T3 |
| I1.5 | **Probe parity test.** Graph-native minting of the Loopover 3×3 primitives as schemas gives 12 schemas with distinct fingerprints. The same holds for the three shape-decode generators | tests | T3 |

### I2 — Graph-native invention algebra and invariant walls (L2)

| ID | Work item | Touch | Tier |
|---|---|---|---|
| I2.1 | **`InventionOperator` seed.** `inverse`, `compose`, `conjugate`, `commutator`, `power(k)` and `root(k)` (search the library for X with Xᵏ = A). Each is a template over I1.2 Terms and carries `yield_count`, `trial_count` and `mean_precision` | new `seeds/invention_operators.json` | T1 spec, T3 |
| I2.2 | **Invention round.** Over pairs of library schemas, apply each operator, compute the fingerprint, and mint the result when it is novel and meets the precision/cost thresholds held as Tolerance nodes (P2.C3). Provenance is `invented_by`. Runs as a stage of the offline consolidation cycle (P1.B1 `consolidation_scheduler`, P6.B2) and is debited from `ThinkingBudget` | new `seeds/invention_round.json` | T1 spec, T3 |
| I2.3 | **Conjugation closure.** Conjugate precise inventions by short held setups until the target effect class is covered, or the budget runs out. This is the probe's `three_cycle_closure`, done as rules | same seed | T3 |
| I2.4 | **Invariant miner.** A library of candidate homomorphism Terms: permutation parity, sums mod k, counts per attribute, determinant sign, conserved attributes. A rule records which invariants every member of a tool family preserves (`preserves_invariant` edges) | new `seeds/invariant_miner.json`; possibly a `PermParity` Term | T1 spec, T2/T3 |
| I2.5 | **Wall explanation and break.** When targeted invention (I5) or a solve fails, check which preserved invariant the target violates. Mint a `WallExplanation{invariant, family}`, then select the cheapest held process that changes that invariant. This is the probe's parity fix, as rules | same seed | T3 |
| I2.6 | **Irreversible and stochastic processes.** `inverse` falls back to `repair(p)`: the cheapest held process whose composition with `p` has an identity fingerprint on the probes. Where no repair exists, effects are evaluated in detached imagination (`imagination.py` machinery, GWM). For stochastic processes the fingerprint becomes a distribution over effects, and support becomes expected change | spec + Term extension | T1, T2 |
| I2.7 | **Graph-native reproduction of the probe.** Loopover 3×3/4×4 and the dihedral closure reproduce §2's numbers on held-out scrambles, including the odd-parity wall and its fix | tests + PMB family (a) | T3 |

### I3 — Lifting, libraries and strategies (L3)

| ID | Work item | Touch | Tier |
|---|---|---|---|
| I3.1 | **Anti-unification lifting.** Generalise families of invented schemas whose expressions differ only in their indices (for example `[R_i, C_j]`) into a parameterised schema. Verify it on held-out instantiations, including **unseen sizes** | Rust `AntiUnify{terms}` Term or seed rules; tests | T1 spec, T2 |
| I3.2 | **Library learning in sleep.** Across accepted `Program`s, settled `CapabilityProgram`s and successful plans, extract shared sub-processes. Score each by the total description-length drop and adopt the winners into the codebook, as `sd_mint_*` does for generators. Then rewrite the stored solutions to use them | new `seeds/library_learning.json` | T1 spec, T2/T3 |
| I3.3 | **Strategy library.** Record each `(problem fingerprint/qualia signature → operator or strategy → yield)` triple. Choose invention operators by expected yield; P2.C1 `SoftWeights` provides soft selection | `invention_operators` yield rules; P4 recall Term | T3 |
| I3.4 | **Agent-invented strategies.** The probe's hand-written placement strategy ("fix one piece at a time with tools that do not disturb fixed cells") becomes a schema the agent must find for itself: goal regression (I5.1) over invariants such as "these cells are fixed" | I5 dependency | T1 |

### I4 — Understanding: induce, explain, test (L1)

| ID | Work item | Touch | Tier |
|---|---|---|---|
| I4.1 | **Lifted transition-schema induction.** Extend the GWM from a flat `state_kind × action_kind` table to object-centric parameterised schemas with preconditions and effects over relations, induced from observed traces. The result is a `ProcessSchema` of kind `transition` | GWM extension seed; possibly an `InduceSchema` Term | T1 spec, T2 |
| I4.2 | **Latent-state invention.** When a residual prediction error persists, run DimInfer/TimeInfer on the residual stream. If a dimension explains the error, mint a latent variable and re-induce | bridges to `shape_decode_loop`, `time_axis` | T1, T3 |
| I4.3 | **Hypothesis portfolio and expected information gain.** Keep the set of process hypotheses consistent with the data. Choose the intervention that maximises expected information gain, computed in imagination. This is also the VOI source that `ThinkingBudget` funding lacked (P2 plan, finding on A5) | new `seeds/experiment_design.json`; uses the `remote_causal` do-contrast | T1 spec, T2/T3 |
| I4.4 | **Explain and rebuild.** Produce an explanation of a process using the production stack. In a detached imagination run, rebuild a schema from **the explanation alone**, then compare fingerprints. Understanding counts only when the rebuilt fingerprint equals the original on held-out probes | bridge seed; `language_production` round-trip pattern | T1 spec, T2 |
| I4.5 | **Laws with proofs.** Promote invariants found by I2.4 to stated laws, and attach `theorem_core` proofs where the domain admits them (for example, parity preservation) | `theorem_core` bridge | T1, T2 |

### I5 — Invention for goals, and representation invention (L4–L5)

| ID | Work item | Touch | Tier |
|---|---|---|---|
| I5.1 | **Goal regression over schemas.** Chain schemas backwards through `pre`/`post` to a goal. A sub-goal with no covering schema becomes an **interface spec** (the required effect fingerprint), which feeds targeted invention (I5.2), then `needs_tool` → `self_extension`, then synthesis | extends P5.E4 | T1 spec, T2/T3 |
| I5.2 | **Targeted invention.** "Find a process whose effect matches E": search the invention algebra with a fingerprint-distance heuristic, under budget. This is the generative source P3's executor needs | `invention_round` targeted mode | T3 |
| I5.3 | **Representation invention.** Propose changes of basis, grain or aperture (DimInfer latent dimensions, P4.C5 Observer frames). Re-describe the active processes in each and adopt the representation that shortens the total description of the battery family. This gives the order-3 reframe rung real content | new `seeds/representation_search.json` | T1 spec, T2 |
| I5.4 | **Analogy as conjugation across domains.** Find a frame map S (a schema from domain A's states to B's) under which a schema from A, conjugated by S, solves B's task. Search S by structure mapping between schema graphs, seeded by P4 recall | new seed; P4.D4 dependency | T1 spec, T2 |

### I6 — Social acquisition (L6)

| ID | Work item | Touch | Tier |
|---|---|---|---|
| I6.1 | **Instruction to schema.** Map `instruction_understanding` output into `ProcessSchema` nodes, then verify each by rollout | bridge seed | T1, T3 |
| I6.2 | **Demonstration to schema.** P6.F3 (imitation) outputs a schema; then lift it (I3.1) and generalise | extends P6.F3 | T2 |
| I6.3 | **Teaching.** Explain an invented process to another agent instance and measure that instance's rebuild fidelity (the I4.4 check across two agents) | harness | T2 |

### I7 — Beyond human (L7)

| ID | Work item | Touch | Tier |
|---|---|---|---|
| I7.1 | **Meta-invention.** `operator_authorship` proposes new `InventionOperator` templates (new combinators over Compose/Inverse/Power). They are adopted by measured yield on the PMB training split, through `adoption_safety` and human-gated criterion proposals. The agent then invents ways of inventing | `operator_authorship`, `criterion_proposals` | T1 |
| I7.2 | **Very large hypothesis portfolios.** Run many hypotheses and invention rounds in parallel under the `AreaParallel` cycle plan, with deterministic folding | cycle-plan configuration + budget | T2 |
| I7.3 | **Processes that ship with proofs.** Every adopted invented process carries its invariants and, where possible, a proof. Adoption fails closed without one in domains that admit proofs | `theorem_core`, adoption rule | T1, T2 |
| I7.4 | **Open-ended self-curriculum.** Generate new tasks at the frontier by novelty search in effect-fingerprint space, building on the prediction-world curricula. Learning progress (`learning_progress_curiosity`) selects which tasks to keep | new seed | T1, T3 |
| I7.5 | **Recursive improvement of the invention loop.** I7.1 together with I3.3, under the safety gates in §3.6. Measure the trend of PMB score against compute over generations (the trend judge from prediction-world v9/v10) | evaluation | T1 |

## 5. Dependencies

```
I0 (PMB + schema decision with P3) ─► I1 ─► I2 ─► I3
                                       │      └──► I5.2 ◄── P3 executor consumes targeted invention
                                       └─► I4 (I4.3 needs P2.A5 budget; I4.4 needs production + imagination)
I3 + I4 ─► I5 (I5.3 needs P4.C5; I5.4 needs P4.D4)
I5 + P6.F3 ─► I6
I3 + I5 + I6 ─► I7
Consolidation hooks: I2.2 and I3.2 run inside the P1.B1 / P6.B2 offline cycle
```

## 6. Capability ladder and the criteria for "beyond"

| Level | Pass condition (held-out, pre-registered) |
|---|---|
| L1 Understand | PMB (b): mechanism-identification accuracy ≥ the human baseline, using ≤ the human number of interventions. PMB (f): explain-and-rebuild fidelity ≥ the threshold set at pre-registration |
| L2 Invent | PMB (a): solve rate ≥ the human baseline on held-out scrambles, with no hand-written strategy (I3.4) |
| L3 Accumulate | Solve cost on later battery tasks falls significantly after library learning. Lifted schemas generalise to unseen sizes |
| L4 Transfer | PMB (g): learning in domain B is faster with A-experience than from scratch, by a pre-registered margin |
| L5 Invent for goals | PMB (d): tool-invention success ≥ the human baseline. Representation switches shorten descriptions on PMB (h) |
| L6 Acquire | Accuracy learning from instruction or demonstration ≥ accuracy learning from reward alone, at equal data |
| **L7 Beyond** | At least one of the following, each pre-registered with its comparison: (i) on a domain with published human records, the invented processes are **shorter or cheaper** than the best published human ones (for example, macro length on a permutation puzzle); (ii) the human-baseline accuracy is reached with **≤ ¼ of the human data or interactions**; (iii) **100% of adopted processes ship with machine-checked invariants** in proof-admitting domains, where humans are unverified; (iv) PMB score keeps a positive trend across ≥ 3 generations of self-authored invention operators (I7.1) with no human-authored operator changes |

Report each level's result plainly, including failures. Phase 1's pattern of perfect scores on deterministic fixtures must not be read as capability.

## 7. Track gates

| Gate | Required |
|---|---|
| Every task | Its acceptance tests. The diff stays within its `Touch` list. Parent-plan rules §1 |
| End of I0 | PMB v1 spec and harness committed; baseline scorecard committed; schema decision recorded in both this doc and P3's |
| End of I1 | All view rules mint schemas for the six existing forms; fingerprint deduplication passes; Rust gates per the parent plan §5 (P2 row) |
| End of I2 | §2's probe numbers reproduced graph-natively on held-out instances, including the parity wall; no hand-written solver |
| End of I3–I7 | The level's §6 pass condition is pre-registered, run and reported. The assessment doc is updated with the new maturity labels and the scorecard |

## 8. Risks and honest limits

- **Toy-domain capture.** Invertible permutation domains are easy for algebra. Mitigations: I2.6 (irreversible and stochastic processes), and ordering PMB so that families (b), (d) and (h) gate L1, L5 and L7.
- **Combinatorial blow-up.** Pairwise operators over a growing library are O(n²) per round. Mitigations: precision and novelty thresholds; I3.3 yield-guided operator selection; `ThinkingBudget`; running in sleep.
- **Fingerprint aliasing.** Different processes can agree on a finite probe battery. Mitigations: held-out probes at adoption, and growing the battery from observed states; I4.4 rebuild checks use fresh probes.
- **Hidden decisions in Python.** The probe's solver is Python. Track I gates require graph-native reproduction, and I3.4 removes the hand-written strategy.
- **Self-modification.** I7.1 and I7.5 change the invention machinery. They require `adoption_safety`, human-gated criterion proposals and the future-manifold commit boundary for anything acting externally.
- **What this plan cannot deliver on its own.** Open-world perception breadth, physical embodiment, breadth of natural language, and the compute to match human-scale experience. The ladder's claims are restricted to the PMB domains plus the domains already in the tree.
