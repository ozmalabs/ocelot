# Decision Resilience Under Adversarial Manifold Perturbation

> **Agent-neutral, dual-use theory; defensive research draft — 2026-09-13.** The decision grammar in this document applies to any agent capable of carrying a represented decision frame: an individual, business, country, institution, coalition, or other collective. Understanding how a frame can be perturbed is inherently dual-use: the same account explains resilience and adversarial exposure. This document studies that exposure as a *risk model* and develops detection and resilience questions only. It is not a guide to covert influence, manipulation, espionage, surveillance, or operational targeting.

## Abstract

Decision systems do not decide over an externally complete world. They decide over their represented landscape. Where an agent represents a Seldon manifold—structured, frame-relative reachable future states or histories—an adversarial perturbation is decision-relevant only when it changes that represented geometry. The agent's standing Narrative can then continue through the changed manifold without its Narrative being directly rewritten.

This creates a defensive problem. A perturbation at an upstream represented relation can alter many later reachable continuations. If downstream branchings remain distinguishable and consequential, the resulting exposure can be combinatorial rather than merely linear. It is nevertheless bounded by aperture, admissibility, capacity, convergence, surprise, and meta-analysis. This paper proposes a defensive account of that exposure, distinguishes direct decision revision from implementation and outcome failure, and identifies resilience requirements: manifold provenance, aperture monitoring, surprise integrity, meta-analysis reserves, independent reconstruction, and target-shape protection.

The proposal is operationally useful only if it improves prediction or defensive decision quality relative to explicit baselines at an acceptable inference cost. It makes no claim that published defence, intelligence, decision-science, or cognitive-science literature establishes the GE/Seldon framework as operationally useful beyond a tested scope.

## 1. Scope and non-goals

The target problem is **adversarial perturbation of a represented decision landscape**, not generic disagreement, normal persuasion, or an attempt to model a complete actual environment. The framework concerns the conditions under which a target agent's represented reachable futures, boundaries, admissibility conditions, or target shapes are altered such that its own standing Narrative produces materially different downstream continuations.

This paper does not describe how to create those perturbations. Its **publication scope** is defensive: modelling exposure, detecting anomalous changes, preserving the integrity of decision review, and testing resilience. That scope does not make the underlying decision theory defensive-only. Any theory that explains how represented decision landscapes change can be read from either side of an adversarial interaction; restricting the paper from operationalising harmful tactics is a boundary on this document, not a claim that the mechanism itself works in only one direction. “Adversarial” denotes an interaction whose effects are misaligned with the target frame's active target or constraints; it does not imply that any particular actor, population, or state is an appropriate target.

Implementation remains separate from decision. A costly, delayed, or failed implementation does not itself show that a decision changed. Likewise, undesirable realised consequences are downstream evidence to be represented later; they were not a co-equal input to the original decision.

## 2. Core objects

Let the target agent's current decision frame be

\[
F=(A_F,L_F,S_F,\Gamma_F,N_F,V_F,R_F).
\]

- \(A_F\): aperture—the distinctions and candidate resolutions currently available to the frame.
- \(L_F\): represented landscape—the sole domain over which the decision is evaluated.
- \(S_F\): standing Narrative—the operative, history-bearing continuation selected without additional decision inference.
- \(\Gamma_F\): represented admissibility conditions.
- \(N_F\): Narrativium—frame-relative capacity for consequential deformation; a feasibility gate, not a cost or choice objective.
- \(V_F\): active comparison descriptions.
- \(R_F\): residual—represented non-admission/mismatch relevant to the operative structure.

When the frame represents a Seldon manifold, write

\[
\mathcal{S}_{h,\rho}(F)
\]

for its structured representation, at horizon \(h\) and resolution \(\rho\), of reachable future histories under represented admissible interventions and boundary conditions. A target is an acceptable shape

\[
\mathcal{T}_{F,h,\rho}\subseteq \mathcal{S}_{h,\rho}(F),
\]

not necessarily a point estimate with an error bar. The shape may contain several acceptable regions, histories, relations, or constraint patterns. Target-shape integrity is therefore not reducible to preserving one numerical target value.

### 2.1 Agent neutrality and collective scale

Let \(a\) denote any decision-making agent and write its current effective decision frame as \(F_a\). The grammar does not depend on whether \(a\) is an individual, business, country, military organisation, public institution, or coalition:

\[
F_a=(A_a,L_a,S_a,\Gamma_a,N_a,V_a,R_a).
\]

At collective scale, the terms need not be psychologically unitary. Aperture may be distributed across offices and information systems; Narrative may be carried by institutional memory, procedures, commitments, and standing plans; admissibility may be carried by authority, law, rules, and internal governance; Narrativium may be held as organisational capacity; and meta-analysis may require coordination across multiple decision rights. These are differences in representation and cost, not a different decision grammar.

A collective may contain compatible or incompatible partial frames, but this is a matter of **coupling**, not a difference in kind. Let \(\mathsf{C}_a\) denote the degree and structure of coupling among the partial frames \(\{F_i\}\) associated with collective \(a\). Coupling can be carried by shared representations, communication paths, common authority, binding procedures, institutional memory, mutual commitments, and coordinated capacity. As coupling increases, apertures, Narratives, admissibility conditions, targets, and meta-analysis can become more mutually constraining and action-guiding; as it decreases, they remain more independently variable and coordination becomes slower, partial, or contested.

A “group mind” is therefore the high-coupling end of the same distributed-frame continuum, not a separate ontological object. There is no sharp threshold at which multiple frames become a different kind of agent. For a given decision, an effective collective frame is a scale-dependent model of how strongly the relevant partial frames are coupled at that point; where coupling is weak, the decision must be modelled as interaction among partially independent frames rather than as a fully unified aggregate representation.

The same neutrality creates the dual-use property. A country can model a business, a business can model a country, and an individual can model an institution; each model remains a representation in the modeller's own frame, not direct access to the modelled agent's actual interior. The theory is therefore symmetrical as explanation even though this paper restricts itself to defensive evaluation.

## 3. Threat model: manifold perturbation without Narrative redirection

Let \(p\) be an adverse perturbation of the target's **represented** manifold:

\[
p:\mathcal{S}_{h,\rho}(F)\mapsto \mathcal{S}'_{h,\rho}(F').
\]

The notation does not imply that an external event automatically changes a decision. A change matters only insofar as it changes what the target frame represents. Nor does it imply that the target's Narrative is directly redirected. The standing Narrative may remain unchanged as a decision rule while it continues through altered represented geometry:

\[
S_F\text{ retained},\quad
\mathcal{S}_{h,\rho}(F)\neq\mathcal{S}'_{h,\rho}(F')
\quad\Longrightarrow\quad
\text{different downstream continuation may result.}
\]

This is the key defensive distinction. The exposure lies in a change to the represented manifold—such as its represented reachability, boundaries, target-shape relation, or resolution—not in assuming unilateral control over another agent's Narrative.

### 3.1 Compounding exposure

If a standing Narrative carries \(n\) later decision-relevant branchings and each has roughly \(b\) distinguishable consequential continuations, the represented future structure may scale schematically as

\[
|\mathcal{S}_{h,\rho}(F)|\sim b^n.
\]

An upstream perturbation can therefore propagate through a family of later continuations. This is a conditional combinatorial claim, not a universal exponential law. It weakens when branches are correlated, constrained, indistinguishable at operative resolution, convergent on the same outcome, capacity-infeasible, or interrupted by surprise and meta-analysis.

Narrative depth is consequently a mixed property. It can increase downstream consequence if a manifold change is traversed through many later dependencies. It can also increase inertia, constrain alternatives, and make the target frame less able to change course.

### 3.2 Decision reopening is not automatic

A standing decision is reopened by either represented surprise or a frame-triggered meta-analysis:

\[
\operatorname{Change}(F)
\Longrightarrow
\operatorname{Surprise}_F(\sigma_F)
\ \lor\
\operatorname{MetaAnalyse}_F(m_F).
\]

For direct surprise-route revision, a resolution must already be available within the target's current aperture and must cohere and be admissible in the current frame:

\[
\operatorname{SurpriseRevision}_F(\sigma_F,x)
\Longrightarrow
x\in L_F\text{ within }A_F
\ \land\
\Gamma_F(x)
\ \land\
\operatorname{Cohere}_F(\sigma_F,x).
\]

An unresolved or frame-incoherent surprise does not directly revise Narrative. It may instead motivate costly meta-analysis, which can reassess the aperture, manifold, target shape, or active comparison dimensions. This distinction matters defensively: a system can detect an anomaly yet remain unable to resolve it in time or within its current representational resources.

## 4. Resilience architecture

The following are defensive design requirements, not claims that every frame already possesses them.

| Defensive property | Decision-level purpose | Failure addressed |
|---|---|---|
| **Manifold provenance** | Preserve a record of which represented boundaries, assumptions, sources, and resolution choices generated the current future geometry. | A consequential manifold change cannot be located, reviewed, or attributed inside the frame. |
| **Independent reconstruction** | Permit a second authorised frame or model to reconstruct the represented manifold and target-shape relation from independently governed inputs. | A single corrupted or narrow representation silently determines continuation. |
| **Aperture monitoring** | Track decision-relevant omissions, resolution limits, and dimensions that may be absent rather than merely uncertain. | A frame treats a missing distinction as settled or treats undisclosed structure as undetermined. |
| **Surprise integrity** | Preserve represented mismatches long enough for review; do not automatically absorb, suppress, or force them into the standing Narrative. | Genuine anomaly is prematurely normalised without an aperture-available resolution. |
| **Meta-analysis reserve** | Reserve time, attention, authority, and capacity for costly re-evaluation when triggers arise. | The frame detects a relevant anomaly but cannot afford to reassess its manifold. |
| **Target-shape protection** | Make acceptable regions, boundaries, and constraint relations explicit rather than relying on a single apparent target point. | A locally plausible continuation drifts outside what is actually acceptable. |
| **Narrativium margin** | Maintain reachable consequential-deformation capacity for defensive transition, recovery, and safe reconfiguration. | A necessary response is represented but infeasible at the point it is needed. |
| **Decision/implementation separation** | Record whether a failure occurred in selection, execution, or realised downstream consequence. | A system "fixes" the wrong layer and corrupts future learning. |

These properties do not eliminate adversarial risk. They make the relevant manifold changes more representable, allow a frame to distinguish an unresolved surprise from a resolved one, and lower the chance that an altered geometry silently propagates through a long Narrative.

## 5. Relation to published strategic and intelligence accounts

Public defence and intelligence literature contains close structural neighbours, but not this full account.

### 5.1 Joint planning, branches, sequels, and assessment

The [Joint Chiefs 5-0 Planning Series](https://www.jcs.mil/Doctrine/Joint-Doctrine-Pubs/5-0-Planning-Series/) and public Joint Staff material on [Commander’s Critical Information Requirements](https://www.jcs.mil/Portals/36/Documents/Doctrine/fp/ccir_fp4th_ed.pdf?ver=2020-01-13-083331-097) organise planning around courses of action, assumptions, branches, sequels, assessment, information requirements, and decision points.

**Convergence:** branches and sequels are close to represented counterfactual continuations; information requirements can function as institutionally declared conditions for reassessment; and routine assessment is analogous to a scheduled meta-analysis.

**Difference:** doctrine is organisational planning machinery. It does not by itself specify why a represented branch is selectable by another agent, whether the other agent can resolve a surprise within its aperture, or how that agent's standing Narrative persists through changed represented geometry.

### 5.2 Strategic warning

Cynthia Grabo's *Anticipating Surprise: Analysis for Strategic Warning* and the CIA's public [*Strategic Warning: The Problem of Timing*](https://www.cia.gov/resources/csi/static/Strategic-Warning.pdf) examine indicators, interpretation, timing, and failures in warning before adversary action becomes imminent.

**Convergence:** the warning tradition shows that evidence can be present yet not become decision-changing because of interpretation, timing, organisational uptake, or competing explanations. This is adjacent to aperture, surprise, and the cost of re-analysis.

**Difference:** strategic-warning work does not require that a surprise have an aperture-available, frame-coherent resolution before directly revising a decision. It also does not treat target shapes, Narrativium, and represented manifold geometry as one decision account.

### 5.3 Adversary modelling

Davis's [*Modeling Adversaries and Related Cognitive Biases*](https://www.rand.org/pubs/reprints/RP1084.html) discusses adversary modelling partly as a response to mirror-imaging and related cognitive biases.

**Convergence:** alternative models of an adversary's goals, beliefs, capabilities, and possible responses are close to modelling other agents' future geometry.

**Difference:** standard adversary models commonly focus on attributed preferences and response functions. The present account adds the agent-relative aperture, standing Narrative, surprise route, meta-analysis cost, target shape, and capacity gate. It therefore models why an externally obvious response may not be represented, coherent, feasible, or selected by the other actor.

These sources do not demonstrate that the GE/Seldon account improves defensive outcomes. They identify adjacent established practices against which the account can be comparatively tested.

## 6. Operational research programme

The relevant criterion is operational usefulness, not abstract truth. For a stated frame class, target shape, horizon, baseline, and inference budget, test:

1. **Predictive value:** Does the model improve prediction of decision persistence, surprise, re-analysis, revision, or relevant downstream decision consequences?
2. **Detection value:** Does the model identify decision-relevant manifold drift earlier or with fewer false alarms than baseline monitoring?
3. **Decision value:** Does using the model improve defensive selection—such as preserving target-shape membership or recovery capacity—relative to baseline procedures?
4. **Cost:** Are any gains worth the representational, data, authority, and meta-analysis burden?
5. **Robustness:** Do benefits transfer across frame classes, horizons, and aperture limitations, or only within a narrow scenario family?

Safe experiments should use synthetic or authorised simulations, benign organisational cases, and transparent decision logs. They should compare the proposed model against scenario planning, structured analytic techniques, and resource-rational metareasoning baselines. The experiment should not require modelling or manipulating real persons without authorisation.

## 7. Limits

- A Seldon manifold is a representation, not an actual future and not an entitlement to infer another actor's internal state.
- A larger represented future geometry can increase defensive exposure, but it does not imply literal exponential growth in every system.
- A low-surprise continuation can be benign, defensive, or harmful depending on the active frame; this paper supplies no independent ethical or legal authorisation.
- Meta-analysis is optional and costly. A system may fail because it never reopens a decision, or because it reopens decisions too often.
- The target shape and the resilience criteria are themselves represented objects that can be incomplete or miscalibrated.
- The explanatory grammar is agent-neutral and inherently dual-use. The defensive restriction in this paper governs what is operationalised here, not which agents the theory can describe.
- None of the cited strategic or intelligence sources establishes GE/Seldon as operationally useful beyond a tested scope. The question is comparative usefulness in bounded applications.

## Source ledger

### GE/Seldon sources

- [Seldon Manifolds — Theory](../formal/02_seldon_manifolds_theory_referenced.tex)
- [Law of Narrative Momentum](../formal/03_law_of_narrative_momentum_theory_referenced.tex)
- [Narrativium](../formal/04_narrativium_theory_referenced.tex)
- [Graphic Equalisation: mind and self grounding](../formal/01b_graphic_equalisation_mind_and_self_grounding.tex)
- [Law of Graphic Equalisation](../formal/01_law_of_graphic_equalisation_theory_referenced.tex)

### Public strategic and intelligence neighbours

- Joint Chiefs of Staff. [Joint Doctrine Publications: 5-0 Planning Series](https://www.jcs.mil/Doctrine/Joint-Doctrine-Pubs/5-0-Planning-Series/).
- Joint Staff J7 (2020). [Commander’s Critical Information Requirements, 4th ed.](https://www.jcs.mil/Portals/36/Documents/Doctrine/fp/ccir_fp4th_ed.pdf?ver=2020-01-13-083331-097).
- Grabo, C. M. (2002). *Anticipating Surprise: Analysis for Strategic Warning*. [Public record](https://archive.org/details/anticipatingsurp0000grab).
- Central Intelligence Agency. [*Strategic Warning: The Problem of Timing*](https://www.cia.gov/resources/csi/static/Strategic-Warning.pdf).
- Davis, P. K. [*Modeling Adversaries and Related Cognitive Biases*](https://www.rand.org/pubs/reprints/RP1084.html).

## Status

This is an agent-neutral, inherently dual-use decision theory presented in a defensively scoped research draft. It models adversarial manifold perturbation as an exposure to detect and contain; it does not provide a procedure to produce effects in another agent. Its formal propositions and operational claims require bounded comparative testing.
