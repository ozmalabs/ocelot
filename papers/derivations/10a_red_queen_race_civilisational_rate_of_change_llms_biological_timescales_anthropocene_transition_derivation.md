# 10a — Conditional cost-floor compression, the AI wedge, and civilisational transition: Stage-2 derivation ledger

**Status:** Stage 2 derivation/audit ledger for unreleased Paper 10a. It promotes only typed definitions, accounting conventions, and conditional consequences from the Stage-1 research record. It does not establish a universal floor, a realised GE implementation, a civilisational forecast, a geological assertion, or a policy instruction.

## 1. Claim classes

- **Definition:** a declared term, unit, boundary, or classification.
- **Accounting convention:** an explicit ledger relation whose inputs have to be measured.
- **Conditional proposition:** a result that follows only from listed premises.
- **Empirical hypothesis:** a claim requiring source-dated data and a measurement protocol.
- **Non-claim:** an inference the ledger does not license.

No occurrence of *floor*, *cost*, *AI*, *collapse*, *successor*, *civilisation*, *narrative*, *narrativium*, *Anthropocene*, or *transition* crosses these classes by metaphor alone.

## 2. Scope and level discipline

A named ledger instance is

`L = (u, o, q, θ, P, I, M, A_b)`,

where `u` is the unit, `o` the outcome, `q` the task configuration, `θ` the outcome/reliability/access threshold, `P` the population, `I` the interval, `M` the measurement protocol, and `A_b` the allocation boundary (payer, place, time, externality and uncertainty rule).

A cost term is not comparable across instances until the outcome and `A_b` are declared. The relevant levels are task, organisation, population, market/institution, physical system, and regime. A lower cost at one level does not entail a lower cost at another.

## 3. Cost and backlog conventions

### D1 — Audited task cost

**Definition.** For ledger `L`,

`C_aud = C_I + C_Q + C_B + C_V + C_G + C_E`,

where `C_I` is information/inference, `C_Q` coordination, `C_B` embodied material/energy, `C_V` verification/repair, `C_G` governance/authorisation, and `C_E` allocated externality cost.

**Boundary.** A vendor tariff, benchmark, labour-hour series, or local cash price is not `C_aud` unless the omitted terms are measured or explicitly bounded. A reduction in one component is not a net social saving by definition.

### D2 — Feasible lower envelope

**Definition.** `F_(u,o,i)` is the lowest observed, boundary-harmonised `C_aud` among feasible configurations meeting the declared outcome, reliability, access, and externality conditions in interval `i`.

**Boundary.** `F` is an empirical comparative envelope. It is not zero, a universal floor, a thermodynamic lower bound, or a claim that all social/physical costs converge to one value.

### D2a — Grammar-relative shapes, floors, and MDL correspondence

**Definition.** An outcome `o` is a declared shape or shape trajectory, not an invariant. A grammar `γ` is a declared repertoire of generative relations/operations, making a shape space `Σ_γ` and grammar-relative lower envelope `F^γ_(u,o,i)`. A new grammar `γ'` can change both. A floor step is recorded through a declared shape comparison map `Π_(γ→γ')` when `F^γ'_(u,Π(o),i) < F^γ_(u,o,i)`; it changes what shape can be generated and at what audited cost.

MDL selects a sufficient account by minimising `L(M) + L(D|M)`, a model description plus a residual data description. Under the GE reading, MDL pressure and cost-floor pressure are the same compression pressure at account and realised-transformation levels. MDL concerns an account and its generative grammar; `C_aud` concerns the information, coordination, embodied, verification, authorisation, and externality transformations through which shapes are realised.

**Boundary.** This is not an identity `C_aud = L(M) + L(D|M)`. It requires a declared descriptive-to-realised grammar map and remains frame-, boundary-, and substrate-relative. MDL does not establish an observed cost decline, a physical floor, a total social cost, a grammar step, `G(R0)`, or a transition outcome. Its agreement with the GE account is a consistency condition, not independent empirical evidence.

### P1 — Cost-floor pressure is an empirical hypothesis

**Premise.** Repeated measurements on a stable outcome scale show

`C_aud,i(q) − F_(u,o,i) ↓ 0`.

**Consequence.** The named task configuration experiences cost-floor pressure under the declared boundary.

**Boundary.** The premise does not show that a sector, economy, or civilisation shares this pressure, or that the lower envelope will remain stable after volume, regulation, energy use, or task mix changes.

### D3 — Backlog convention

**Definition.**

`B_(i+1) = max{0, B_i + ΔD_i − A_i + H_i}`,

where `D` is outcome-scaled demand, `A` verified delivered adaptation, and `H` induced demand/residual harm.

**Boundary.** Cost appears in the determination of `A` and `H`; it is not silently substituted for either one.

### P2 — Technical cost decline does not identify adaptation

**Premise.** A component cost (for example `C_I`) declines while all other terms and outcome conditions are not yet fully observed.

**Consequence.** Both an adaptation-improving case and a harm/induced-demand case remain admissible. The sign of `ΔD − A + H` is unidentified.

**Proof.** Hold the observed component decline fixed. In one allowed completion it enables reliable, accessible delivery and raises `A`. In another, deployment, errors, exclusion, rebound, or repair raises `ΔD` or `H`. Since these completions share the observation but differ in ledger sign, the observation alone cannot identify the sign. ∎

**Boundary.** This does not say cost declines are useless; it specifies the measurements needed to establish their net effect.

### C1 — Conditional backlog growth

**Premise.** On a stable common outcome scale,

`ΔD_i − A_i + H_i ≥ ε > 0`

for every interval, with no unrecorded reserve, substitution, or threshold change.

**Consequence.** `B_n ≥ B_0 + nε` after `n` intervals.

**Proof.** The stated increment implies `B_(i+1) ≥ B_i + ε`; iterate. ∎

**Boundary.** C1 does not establish its antecedent for any real unit. It does not establish collapse, a biological ceiling, an LLM cause, or an economic-system result.

### C2 — Conditional recovery/catch-up

**Premise.** While `B_i > 0`,

`A_i − ΔD_i − H_i ≥ ε > 0`.

**Consequence.** `B_(i+1) ≤ max{0, B_i − ε}`. Backlog falls by at least `min{ε,B_i}` in that interval and reaches zero within at most `ceil(B_i/ε)` intervals if the premise persists.

**Boundary.** Cost-floor pressure does not remove the possibility that coordination, resourcing, distributional repair, substitution, learning, or safe technical use produces this premise.

## 4. Economic-system and transition premises

### P3 — Distribution/legitimacy is an optional measured outcome condition

**Premise.** A declared cost transformation changes tasks or productive capacity. If the named outcome or viability vector includes access, income security, ownership, demand, competition, agency, legitimacy, or due process, those variables are observed separately for population `P`.

**Consequence.** The ledger may test whether lower task cost corresponds to the declared quality of distributed outcome delivery rather than merely aggregate output.

**Boundary.** These variables are not prerequisites for a regime to exist. A regime can persist through extraction, coercion, exclusion, or externalisation, and a successor can be viable under a narrow declared vector while harmful or unacceptable. Neither an AI exposure estimate nor a labour-share trend identifies a causal effect of a named model, proves system destruction, or implies a specific redistribution policy.

### D4 — GE transition premise and branch definitions

**Definition.** Let `R0` be a present regime represented by reproduction arrangements `I0` and a minimum viability vector `v`. `G(R0)` is the additional premise that, under declared cost-floor pressure, `R0` cannot continue indefinitely while retaining every arrangement in `I0`.

A trajectory has **terminal discontinuity** when it fails `v`. It has a **successor regime** when it satisfies `v` but is no longer isomorphic to `I0` on the declared identity test.

**Boundary.** This ledger does not derive `G(R0)` from current data, prove that `R0` is civilisation as a whole, provide a date, choose a successor, or rank outcomes morally.

### P4 — Conditional terminal/successor partition

**Premise.** `G(R0)` holds and the trajectory classification is exhaustive and mutually exclusive: it either fails `v` or satisfies `v`.

**Consequence.** Every classified post-transition trajectory is terminal discontinuity or a successor regime.

**Proof.** Failure of `v` meets the first definition. Satisfaction of `v`, combined with `G(R0)`, excludes indefinite retention of all `I0` and meets the second. The categories are exclusive by premise. ∎

**Boundary.** P4 is a classification consequence, not an empirical forecast, probability, singularity claim, or proof that a successor has a larger measurable state space. “More possibilities” means only that it is not required to preserve every current arrangement.

### D5 — Analytical manifold and continuance interpretation

**Definition.** `M(R0)` is the declared analytical state space of regime `R0`'s reproduction arrangements, ledger variables, and measured constraints. “Manifold” is classificatory rather than a claim of a differentiable physical manifold. Under `G(R0)`, `M(R0)` maps the terminal/successor possibility set without ordering its members.

The **continuance lens** `L_C` is a separately declared interpretation that orders a trajectory satisfying the collective viability condition above terminal discontinuity. Conditional on continuance, `L_C` orders trajectories by lower measured human suffering `S^H` under a declared protocol and continued human participation `P^H` in the system.

**Consequence.** Given `L_C`, continuance is the best outcome under that lens; within continuance, lower `S^H` and continued `P^H` specify its ideal direction.

**Boundary.** `L_C` is not derived from `G(R0)`, the cost ledger, or P4. It requires declared meanings and measurements for civilisation, humanity, suffering, participation, population, horizon, and threshold. A different interpretive lens changes the ordering but not the analytical classification.

### P5 — GE substrate is a separate scenario

**Premise.** A realised, independently reproducible GE graph-substrate implementation lowers `C_aud` for the same pre-registered task/outcome/reliability/access/externality boundary.

**Consequence.** It may be added as a measured technical contributor to `A` or a changed cost condition.

**Boundary.** Until the premise is satisfied, GE substrate efficiency is unmeasured. Even if satisfied, it does not establish `G(R0)`, a net positive ledger sign, terminal discontinuity, or a successor regime.

### P6 — Anthropocene transition/end is an analytical umbrella

**Premise.** A use of “Anthropocene transition/end” identifies whether it means an informal Earth-system/environmental-history descriptor, a coupled human–planet analytical frame, a cultural/political diagnosis, or a proposed unratified stratigraphic interval. When it names the transition question, it declares observable conditions, scale, and horizon.

**Consequence.** “Singularity,” “Lyapunov-horizon collapse,” and “phase change/transition” can be used as alternative analytical descriptions without silently converting them to geology or physics.

**Boundary.** The ledger does not assert a ratified Anthropocene Epoch, known endpoint/date, settled or single mechanism, collapse, inevitability, an end of human influence, or an end of geology.

## 5. Evidence and falsification obligations

A credible named case requires: (1) repeated outcome-normalised costs and a documented `A_b`; (2) model/version/task/tariff/cache/tool/oversight data where AI is involved; (3) reliability, repair, access, and appeal data; (4) energy/material/water/local-burden accounting; (5) distribution, ownership, income/demand, competition, and legitimacy indicators where an economic claim is made; (6) a declared regime identity test and viability vector where P4 is invoked; and (7) a comparable counterfactual configuration.

The following observations defeat or narrow the proposed claims:

- no decline in boundary-harmonised `C_aud`, or an alternative configuration has lower audited cost;
- a purported saving is transferred to an omitted population, payer, time, or environmental sink;
- outcome delivery, access, or repair worsens or does not improve under the declared change;
- the relevant economic access, income security, agency, demand, and legitimacy measures remain adequate, falsifying a local necessary-exclusion claim;
- `G(R0)`, the identity test, or viability classification is missing, making P4 inapplicable;
- a claimed GE substrate gain fails independent replication or the same-boundary test.

## 6. Final ledger boundary

The ledger establishes conditional accounting and classification results. It does not establish that all tasks approach a floor, that AI destroys an economic system, that the current regime must terminate, that humans cannot adapt, or that GE implementation exists. An action rule or evaluation criterion may be coupled to the ledger only as a separately declared input with an outcome, population, horizon, and threshold. Its strongest defensible conclusion is: when outcome-normalised audited cost changes rapidly, the allocation, verification, physical-boundary, and reproduction conditions of the relevant regime must be measured rather than assumed stable.
