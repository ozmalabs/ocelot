# Graphic Equalisation decision theory: represented landscapes, continuity, residual, and self

> **Research record only — 2026-09-11.** This note compares a proposed decision-level reading of Graphic Equalisation (GE) with relevant research. It does **not** amend the formal papers or specify an implementation mechanism. It does not use abstract truth as the framework criterion; the relevant question is whether the account is operationally useful under stated scope, comparison, and cost.

## Scope and epistemic discipline

The subject is a theory of **decision**, not the machinery that happens to realise a decision. An agent may make or retain a Narrative-based decision even where carrying it out is extremely costly. It therefore makes no claim about search procedures, neural activity, runners, writes, physical effort, motor control, or the real-world cost of executing an action. Those may cause, carry, constrain, or follow a decision, but they are not decision-theoretic inputs merely by existing. In particular, a high implementation cost does not itself oppose a standing Narrative or trigger a decision change.

A decision is evaluated only over the agent's **represented landscape**. A change in an external situation that does not alter what the agent represents need not change that agent's decision at all. Conversely, an agent can change its decision after a representational change without an external change. External circumstances matter to this theory only where they have become represented, or as a distinct downstream question about what follows a selected decision. They are not a second, co-equal landscape supplied to the choice rule.

The formal GE sources below establish vocabulary and constraints inside their own systems. The decision ledger and empirical consequences in this note are proposed extensions and must be treated as such.

## Operational usefulness criterion

The framework is useful only conditionally: for a specified decision population, frame class, horizon, target, baseline, and inference budget. Its relevant performance questions are:

1. **Predictive value:** Does it improve prediction of represented decision persistence, surprise, meta-analysis, revision, or downstream decision-relevant consequences relative to a stated baseline?
2. **Decision-altering value:** Does using the account change a planner's or agent's selection in a way that improves the stated target relative to that baseline?
3. **Cost and scope:** Are those gains worth the additional representation, meta-analysis, data, and organisational cost, and do they transfer only within the stated frame class?

A framework may be a deliberately incomplete or non-literal representation and still be useful on these measures. Conversely, a formally elegant account that does not improve prediction or alter decisions beneficially, net of its cost, has no established operational value. There is no frame-free success measure: both the target and the comparison are themselves stated in the operative frame.

## Canonical proposal

> A decision is evaluated over a frame's represented landscape only. The standing Narrative is the zero-*additional-decision-inference* default. A decision is reopened either by **represented surprise** — a represented departure from what the standing Narrative expects or admits — or by a frame-triggered **meta-analysis** of the decision. Meta-analysis is additional decision inference, with a cost and triggers that vary by frame; it is not implementation. Alternatives must be represented and admissible. Narrativium supplies a frame-relative feasibility/capacity condition; expected return and any further active criteria supply comparison dimensions. A Pareto frontier is not a full selection rule. Surprise does not automatically select a replacement: its residual must be decision-relevant and recurrent or unabsorbable, and it must admit a resolution available within the current aperture that coheres in the current frame before it licenses revision. An unresolved or frame-incoherent surprise may motivate meta-analysis, but cannot directly replace Narrative. A meta-analysis may independently reopen comparison and selection under its own current-frame criteria. The self is an agent inside this same structure: a current self may choose a represented transformation that alters the successor's decision landscape, but the successor cannot authorise the transition that creates it.

Here, “zero” is deliberately narrow. It means that continuing the standing Narrative requires no **additional inference for this decision** beyond treating that continuation as already standing. It does **not** mean that continuation has zero time, energy, opportunity cost, implementation cost, or real-world consequence. Implementation belongs to a separate stage: it can be expensive, difficult, delayed, or fail while the decision remains Narrative-based. Its magnitude alone is not a trigger. By contrast, a meta-analysis is an additional **decision-inference** step: undertaking it has a decision-level cost, and the reasons that trigger it vary with the current frame.

## A typed decision ledger

Let the current decision frame be

\[
F = (A_F, L_F, S_F, \Gamma_F, N_F, V_F, R_F).
\]

This is a bookkeeping device, not yet a derivation or a complete choice theorem.

| Term | Decision-level role | What it is not |
|---|---|---|
| \(A_F\), aperture | What the frame can presently represent or make available for consideration. | A claim that everything outside aperture is erroneous or directly residual. |
| \(L_F\), represented landscape | The represented candidates, their represented relations, projected consequences, and available comparison descriptions. It is the **whole domain of decision evaluation**. | A read-out of everything actual, or an additional external input to decision. |
| \(S_F\), standing Narrative | The operative, history-bearing continuation represented now. In the absence of a rule that displaces it, it supplies the default continuation. | The whole past, an implementation trace, or necessarily a self-model. |
| \(\Gamma_F\), admissibility | The represented constraints, rules, and qualification conditions that determine which candidates may be considered live. | Preference, utility, or a selection rule. |
| \(N_F\), Narrativium | The frame-relative measure of reachable consequential deformation for a specified configuration, frame, time, and deformation class. It can gate a represented transition as feasible. | Expenditure, energy, effort, a conserved balance, optionality in general, or “the cheapest option.” |
| \(V_F\), evaluation description | Stated comparison dimensions: e.g. represented expected return, risk, commitments, obligations, or other values. | A presumed universal scalar utility function. |
| \(R_F\), residual | A represented non-admission or mismatch relevant to the frame's operative structure. In the surprise route, it must resolve through a candidate available to the current aperture and coherent in the current frame. | A generic prediction error, an unrepresented omission, a raw count of discrepancies, or an automatically decision-changing error. |

A candidate \(x\) is eligible for deliberative comparison only if it is represented in \(L_F\) and admissible under \(\Gamma_F\). Where a transition from the current configuration \(\mathcal X\) to \(x\) has a represented cost and deformation class, the Narrativium paper supplies the same-configuration feasibility form

\[
c_{W:G}(G \xRightarrow[T]{} x) \preceq N_{W:G}(\mathcal X,T).
\]

This is a gate, not a balance equation and not a choice objective. In particular, a positive transition cost may produce a successor with more Narrativium; no general rule says \(N_{t+1}=N_t-c\).

A compact eligible set is therefore:

\[
E_F = \{x \in L_F \mid x\text{ is represented},\ \Gamma_F(x),\ \text{and any applicable capacity gate holds}\}.
\]

The ordinary continuation \(s_F\) is the represented candidate induced by \(S_F\), when it remains eligible. It is the default by its standing status, not because an empirical law says every agent always preserves a status quo. In this proposal, it remains selected unless represented surprise or a frame-triggered meta-analysis opens revision; the mere presence of other eligible candidates does not change the decision.

### Comparison, Pareto, and selection

Let \(v_F:E_F\to\mathbb R^k\) be an explicitly declared vector of comparison dimensions. It may include represented ROI, risk, commitments, or qualitative orderings where a vector is not appropriate. Its non-dominated subset is

\[
P_F=\{x\in E_F \mid \nexists y\in E_F:\ y\text{ dominates }x\text{ under }v_F\}.
\]

This distinguishes three questions that must not be collapsed:

1. **Feasibility:** Is \(x\) represented, admissible, and — when applicable — capacity-feasible?
2. **Comparison:** Is \(x\) dominated or non-dominated on the declared dimensions?
3. **Selection:** Which eligible, possibly non-dominated candidate is selected?

A Pareto frontier answers the second question only. It does not select one candidate. Selection requires a further, stated rule — but in this proposal that rule becomes decision-changing only after represented surprise **or a frame-triggered meta-analysis** has opened revision: for example a priority order, scalarisation, lexicographic constraint, or deliberative procedure may then select among candidates. **Absent represented surprise and absent meta-analysis, retain \(s_F\) where it remains eligible, regardless of other eligible or non-dominated candidates.** It does not claim that this is the only valid tie-breaker after either route has reopened decision.

### Target shapes, not points with error bars

A target is a **represented acceptable shape**, not necessarily a desired point estimate with uncertainty around it. Where a frame represents a Seldon manifold, write the target shape as

\[
\mathcal T_{F,h,\rho}\subseteq \mathcal{S}_{h,\rho}(F).
\]

It can be a region of future states, a family of histories or paths, a relation among agents, a constraint structure, or a shape with boundaries, holes, and multiple disconnected acceptable components. The target exists only as represented in the current frame; it is not a hidden objectively privileged destination.

This is distinct from a point estimate with an error bar. \(\hat z\pm\epsilon\) says that the frame is uncertain about the value or location of one intended point. \(\mathcal T\) says that different configurations can be acceptable while some nearby configurations can be unacceptable; its geometry carries the acceptability relation. The two coincide only in the special case where the target is a small, simply connected tolerance region around a single point.

Selection therefore need not minimise distance to a point. After decision has been reopened, it can ask whether a represented, admissible, capacity-feasible transition reaches or remains within \(\mathcal T\), and then apply the stated selection relation among qualifying paths. Narrativium remains a capacity gate: it concerns whether a consequential deformation reaching the target shape is reachable, not how valuable one target point is relative to another. A target shape may intersect a Pareto frontier at several regions; the intersection does not eliminate the need for a selection rule.

Aperture determines how much of the target shape, its boundaries, and its relation to the represented manifold can be distinguished at current resolution. Surprise can occur when the standing projected continuation no longer fits the represented target shape, but direct surprise-route revision still requires an aperture-available, frame-coherent resolution. Meta-analysis may refine the target shape, the manifold resolution, or their represented relation; it does not imply that the target becomes a point estimate.

### Aperture, surprise, and meta-analytic revision

Aperture is prior to comparison: an alternative that is not represented is not silently evaluated and rejected. Its absence may be discovered only through metacognitive inference, deliberate expansion of aperture, or a newly represented alternative. This follows the self-model distinction in the GE source: aperture omissions are absent rather than direct residual. The mere availability of a newly represented alternative does not change a decision unless it creates represented surprise or the current frame undertakes a meta-analysis.

There are two routes by which the standing decision is reopened. Let \(\sigma_F\) denote represented surprise, and let \(m_F\) denote a current-frame meta-analysis of the decision. Then the proposed opening condition is

\[
\operatorname{Change}(F)\ \Longrightarrow\ \operatorname{Surprise}_F(\sigma_F)\ \lor\ \operatorname{MetaAnalyse}_F(m_F).
\]

For a surprise to license a direct decision revision, it must have a resolution \(x\) already available within the current aperture and represented landscape, and that resolution must cohere in the current frame:

\[
\operatorname{SurpriseRevision}_F(\sigma_F,x)\ \Longrightarrow\ x\in L_F\text{ within }A_F\ \land\ \Gamma_F(x)\ \land\ \operatorname{Cohere}_F(\sigma_F,x).
\]

“Coheres” is deliberately frame-relative: the proposed resolution must be intelligible under the current frame's represented relations, commitments, and admissibility conditions. It cannot borrow its warrant from a successor frame that has not yet been installed.

Meta-analysis is additional decision inference rather than implementation. It has a decision-level cost, and no fixed universal trigger: what occasions it varies with the current frame. It may reconsider the represented candidates, admissibility, comparison dimensions, aperture, or the standing Narrative itself. A high implementation cost, whether external or represented, is not an opening condition merely by being high. It can be decided upon and then encountered in implementation while the Narrative decision remains unchanged.

Surprise does not automatically select a replacement. Revision through the surprise route is licensed only under the stronger conjunctive condition that the surprise yields a residual \(r\in R_F\) which is (i) represented, (ii) relevant to a current decision or operative commitment, (iii) recurrent or unabsorbable within \(S_F\) and its admissible repair, (iv) resolved by a candidate \(x\) available within the current aperture, and (v) coherent and admissible in \(F\). A residual count alone neither establishes a better option nor selects one. A local mismatch that is absorbable, irrelevant, unresolved within aperture, or frame-incoherent gives no decision-level warrant for replacing Narrative. Such a surprise may motivate meta-analysis, including aperture expansion, but it cannot itself directly revise the decision.

A meta-analysis likewise does not guarantee replacement; it pays the additional decision-inference cost to reopen comparison and then applies its currently represented criteria. This makes revision a surprise-triggered **or** meta-analytically reopened proposal rather than an error-minimisation law: absent both routes, the frame retains its standing Narrative; after either route, it may retain it unless a decision-relevant alternative is represented, admissible, and selected.

## Decision quality is not decision validity or success

This proposal is **not** an ideal-decision theory. It permits ordinary, poor, carefully considered, and failed decisions without treating them as the same thing.

| Description | Decision-level account | What does not follow |
|---|---|---|
| **Normal / ordinary** | The standing Narrative is retained because neither surprise nor a frame-triggered meta-analysis reopens the decision. | That the decision is globally optimal, cheap to implement, or guaranteed to succeed. |
| **Frame-valid but poor** | The decision is eligible and coherent in the current frame, but its limited or miscalibrated aperture omits a relevant possibility, relation, or consequence. | That the decision was incoherent at the moment it was made, or that an omitted item was then directly residual. |
| **Well considered** | The agent pays the additional decision-inference cost of meta-analysis, perhaps checking commitments, comparing candidates, recalibrating representations, or expanding aperture. | That more thought guarantees a better decision, a wider aperture, or a successful outcome. Meta-analysis can be wasteful, mistaken, or itself constrained by the frame. |
| **Decision-invalid in frame** | A proposed change violates current admissibility or lacks a resolution that coheres within the current aperture and frame. | That it cannot later become thinkable through a different frame or a meta-analytic revision. |
| **Implementation failure** | A standing or selected decision cannot be carried out, is delayed, or is carried out imperfectly. | That the decision itself changed or was decision-invalid; implementation is a separate stage. |
| **Downstream outcome failure** | A decision may be implemented as selected but have undesirable realised consequences. | That those consequences were a co-equal input to the original decision, or that outcome failure alone proves a decision error. |

Aperture and meta-analysis account for much of this variation. **Aperture** determines which candidates, consequences, and resolutions are presently available to the decision; it therefore constrains both what can be good *in the frame* and what can later be recognised as missing. **Meta-analysis** determines whether the agent incurs additional decision inference to reassess that landscape, possibly including an aperture expansion. It is not a guarantee of improved quality; it is the costly, frame-variable opportunity to change the quality or scope of the decision process.

Thus two agents may share a standing Narrative and active values yet reach different decisions because one has a different aperture, or because one undertakes meta-analysis while the other does not. Conversely, two agents can make the same decision for very different reasons and with very different deliberative depth. A later bad outcome may reveal a limited aperture, a bad causal projection, or implementation failure, but it does not retrospectively make the actual landscape an input to the original decision.

This taxonomy is a proposed analytic distinction, not an empirical classification already established by decision science.

## Recursive self-decision

The theory applies recursively to the self **as an agent in its own represented landscape**. Let \(\tau\in L_F\) be a currently represented and admissible transformation whose represented successor is

\[
F' = \tau(F).
\]

\(F'\) may contain a changed aperture, Narrative, admissibility structure, evaluation dimensions, self-model, or a changed set of reachable transformations. The current frame may select \(\tau\) only through what it can represent and order **now**, and only when represented surprise or a frame-triggered meta-analysis has opened revision of the standing decision. The candidate successor is a candidate decision landscape, not an authority located outside the present decision.

This yields an antecedent-state constraint:

\[
\operatorname{Admissible}_F(\tau)\ \text{is evaluated in }F,\quad\text{not retrospectively by }F'.
\]

A value, identity, or order that exists only in \(F'\) cannot authorise the transition that first installs it. This does not make self-change impossible: it makes it direct but gated from the predecessor frame. Nor does it establish a descriptive claim about how humans or AI systems in fact self-modify. It is a structural constraint proposed by the GE formalism.

## Relation to the formal GE sources

- [Narrative / law of narrative momentum](../formal/03_law_of_narrative_momentum_theory_referenced.tex) defines Narrative as an operative, history-bearing present structure, not the whole past, and defines free continuation as persistence when no rule writes against the standing structure. This note translates that narrowly into a decision default. It does **not** identify the formal paper's write cost with the implementation cost of deciding.
- [Narrativium](../formal/04_narrativium_theory_referenced.tex) defines frame-relative capacity for consequential deformation, \(N_{W:G}(\mathcal X,T)=\mu_{\mathcal X}(\mathcal R_{W:G}^T(\mathcal X))\), and explicitly separates measurement from expenditure. This note imports the feasibility role only; it adds no universal decision metric or interpersonal accounting.
- [Seldon Manifolds](../formal/02_seldon_manifolds_theory_referenced.tex) defines a frame-, horizon-, and resolution-relative representation of reachable future states or histories under represented counterfactual interventions and future boundary conditions. This note treats a target as an acceptable represented shape within that geometry, not as a point forecast or a probabilistic error bar.
- [Mind and self grounding](../formal/01b_graphic_equalisation_mind_and_self_grounding.tex) supplies the aperture/residual distinction and treats incomplete self-models and metacognition as structural/capability questions. It does not establish the empirical revision rule proposed here.
- [Law of Graphic Equalisation](../formal/01_law_of_graphic_equalisation_theory_referenced.tex) supplies antecedent-state admissibility, reflective graphs, and the no-future-self-authorisation corollary. This note presents their decision-theoretic reading; it does not claim an independently validated behavioural model.

## Literature comparison ledger

The table identifies what a source actually supports, where it converges with the proposal, and what remains unestablished. “Convergence” means a useful structural neighbour, never by itself evidence that GE improves prediction or decision under any stated scope.

| Research area and verified source | Established result relevant here | Convergence with this note | Difference / unsupported leap |
|---|---|---|---|
| Resource-rational metareasoning — [Godara, Alemán & Yu (2024)](https://arxiv.org/abs/2408.01253) | Models the choice of reasoning processes under time, energy, and capacity costs; extends meta-level planning to uncertain transition/reward distributions and offers task-specific predictions. | Makes it legitimate to distinguish a base choice from deliberation about whether/how to reason further. | It models computation and its costs; it does not establish Narrative, a zero-additional-inference continuation, GE admissibility, or the represented-landscape-only thesis. This note deliberately does not turn its implementation/cost model into a claim about decision implementation. |
| Defaults and status quo — [Jachimowicz et al. (2019)](https://doi.org/10.1017/bpp.2018.43) | A meta-analysis of 58 datasets (pooled \(n=73{,}675\)) found a substantial but highly heterogeneous default effect; endorsement and endowment partly accounted for variation. | Empirical defaults and status-quo labelling are adjacent to a standing continuation. They motivate testing whether a represented default has decision effects. | A pre-selected choice in an experiment is not a general, history-bearing GE Narrative. The literature supplies neither the zero-additional-*decision-inference* account nor a universal persistence law. It also warns that default effects vary and can be absent or negative. |
| Active inference — [Da Costa et al. (2024)](https://arxiv.org/abs/2401.12917) | Gives a normative Bayesian model of agency using prediction and preference models; expected free energy combines risk/ambiguity and addresses exploration–exploitation. | Both accounts require an agent-relative model and make revision/selection depend on represented descriptions rather than direct access to a total world. | Expected free energy, variational free energy, prediction error, and Bayesian surprise are specific mathematical quantities. GE residual is non-admission/non-coherence, not automatically any of them or a common numeric signal. The paper expressly does not model agents' representations; it therefore cannot establish GE's represented-landscape thesis, aperture, or residual condition. |
| Belief revision — [Alchourrón, Gärdenfors & Makinson (1985)](https://doi.org/10.2307/2274239) | Supplies a formal family of postulates for changing belief sets while retaining as much as possible under logical constraints. | Offers a rigorous neighbour for asking when represented commitments should be retained or revised. | Narrative includes operative historical structure, candidates, and admissibility, not merely a belief set. The residual condition is not AGM inconsistency, and this note does not assert AGM revision. |
| Multiobjective optimisation — [Pajasmaa, Miettinen & Silvennoinen (2025; published 2024)](https://doi.org/10.1007/s10726-024-09915-8) | Pareto-optimal solutions encode trade-offs; practical selection generally requires preference information, an aggregation rule, or another final-selection procedure. | Directly supports the narrow claim that non-dominance is not a complete choice rule. | It does not privilege Narrative continuation, define Narrativium, or provide a universal rule for an individual agent. GE's selection proposal must state its own tie-breaker. |
| Self-referential AI agents — [Yin et al., *Gödel Agent* (2025 revision of 2024 preprint)](https://arxiv.org/abs/2410.04444) | Presents an engineered framework that iteratively modifies and evaluates parts of an artificial agent, with reported task-benchmark gains. | Shows that a system can represent and alter parts of its future decision machinery. | It is an implementation and benchmark result, not a decision theory or evidence for antecedent-state authorisation. It does not establish that successor preferences cannot authorise their own installation; that is the GE structural constraint to be formalised and tested separately. |

### Additional neighbours already present in GE sources

The formal Narrativium paper already situates reachability and viability as mathematical neighbours. They support the limited analogy between Narrativium and a frame-specified reachable set, but do not yield subjective preference, a cost accounting, or a selection rule. The formal self-model paper cites metacognition and self-model research as structural/empirical neighbours; it already warns that its “sudden realisation” account is a prediction, not an established result. Those limits remain in force here.

## What is presently supported, convergent, and open

**Established prior art.** Decision research supports bounded and meta-level reasoning, default effects with substantial heterogeneity, formal belief revision, multiobjective non-dominance, and model-based policy selection. Contemporary engineering work demonstrates limited, designed forms of self-modification in artificial agents.

**Convergence.** The literature supports the usefulness of distinguishing feasibility, evaluation, and final selection; it also supplies examples in which a represented model, default, or preference structure affects choice. The multiobjective result is especially direct: a Pareto set does not by itself select a final option.

**GE differences.** GE insists on a single decision domain — the represented landscape — rather than treating a represented model and an “actual landscape” as co-equal decision inputs. It specifies Narrative as a history-bearing default in decision inference, **represented surprise or a costly, frame-triggered meta-analysis as routes that reopen decision**, Narrativium as capacity rather than cost, residual as non-admission rather than a generic numerical error, and successor-self authority as constrained by the antecedent state.

**Unestablished operational claims.** No source here directly shows that using Narrative, Narrativium, GE residuals, the proposed conjunctive revision condition, or antecedent-state authorisation improves prediction or changes decisions beneficially in a specified setting. The draft is not entitled to present them as established laws of psychology or as consequences of active inference, default research, reachability, or Pareto theory.

## Operational testing and next research requirements

The proposal becomes operationally assessable only when its decision-level terms are measured without reducing them to a specific implementation, and when it is compared against stated baselines at stated inference costs. Useful discriminating work includes:

1. **Representational, implementation-cost, and meta-analysis intervention.** Hold an agent's represented landscape fixed while changing an unrepresented external condition or the realised implementation cost; the model predicts no immediate decision change attributable to either condition alone. Separately introduce represented surprise or initiate a meta-analysis while holding other represented content fixed. This tests the represented-landscape boundary, the separation of decision from implementation, and the distinct meta-analytic route.
2. **Narrative-default, surprise, and meta-analysis test.** Define measurable standing continuation, added-decision-inference, represented-surprise, and meta-analysis measures. Test whether continuity is retained even when implementation is costly, provided neither surprise nor meta-analysis occurs; then test whether either route can reopen decision and whether meta-analysis triggers vary with the frame. Compare this with explicit opt-in/opt-out defaults, rather than assuming the constructs are identical.
3. **Capacity versus preference.** Independently manipulate a represented reachability/capacity gate and represented ROI or other values. The account predicts that added capacity enlarges eligible options but neither selects a particular option nor revises Narrative by itself absent surprise or meta-analysis; a frontier still needs a choice rule.
4. **Surprise, residual, coherence, and meta-analysis qualification.** Contrast an absorbable or decision-irrelevant surprise with a recurrent, unabsorbable surprise whose resolution is either available and coherent within the current aperture/frame or unavailable/incoherent. Contrast meta-analysis with no meta-analysis at matched surprise levels. The strong proposal predicts direct surprise-route revision pressure only in the available-and-coherent case; an unresolved surprise may instead motivate costly meta-analysis. Demonstrating direct surprise-route change without an aperture-available, frame-coherent resolution, or that raw mismatch alone reliably causes revision, would count against this formulation.
5. **Aperture expansion.** Introduce a previously unavailable alternative without changing existing candidate values. Test whether a surprise changes the decision only when its resolution is already available within aperture and coherent in the current frame; test aperture expansion as a possible meta-analytic response rather than a direct surprise-route revision.
6. **Recursive self-decision.** In computational models and carefully designed human tasks, record the predecessor representation, criteria, and gate that select a successor transformation. A satisfactory test must distinguish “the future state would endorse this” from “the present state represented a reason to install it.” A system that reliably improves a stated target by relying on an entirely unrepresented successor-only criterion would delimit the operational usefulness of the antecedent-state formulation.
7. **Cross-frame comparison.** Any claim comparing Narrativium across frames, agents, or deformation classes must state and validate a conversion relation. Without one, no aggregate total or interpersonal trade is licensed.

Before a formal paper or applied adoption, the programme needs: explicit measurement models for aperture, Narrative, admissibility, residual, capacity, and meta-analysis cost; preregistered rival hypotheses drawn from default effects, resource rationality, active inference, and belief revision; comparison baselines; and examples where GE yields better prediction or better target-directed decisions at an acceptable cost.

## Source ledger

### GE-internal sources

- [Law of Narrative Momentum (formal source)](../formal/03_law_of_narrative_momentum_theory_referenced.tex)
- [Narrativium (formal source)](../formal/04_narrativium_theory_referenced.tex)
- [Seldon Manifolds (formal source)](../formal/02_seldon_manifolds_theory_referenced.tex)
- [Graphic Equalisation: mind and self grounding (formal source)](../formal/01b_graphic_equalisation_mind_and_self_grounding.tex)
- [Law of Graphic Equalisation (formal source)](../formal/01_law_of_graphic_equalisation_theory_referenced.tex)

### External research inspected for this record

- Godara, P., Alemán, T. D., & Yu, A. J. (2024). *Metareasoning in uncertain environments: a meta-BAMDP framework*. arXiv:2408.01253. [Abstract and paper](https://arxiv.org/abs/2408.01253).
- Jachimowicz, J. M., Duncan, S., Weber, E. U., & Johnson, E. J. (2019). *When and why defaults influence decisions: a meta-analysis of default effects*. *Behavioural Public Policy*, 3(2), 159–186. [DOI](https://doi.org/10.1017/bpp.2018.43).
- Da Costa, L., Tenka, S., Zhao, D., & Sajid, N. (2024). *Active Inference as a Model of Agency*. arXiv:2401.12917. [Abstract and paper](https://arxiv.org/abs/2401.12917).
- Alchourrón, C. E., Gärdenfors, P., & Makinson, D. (1985). *On the logic of theory change: Partial meet contraction and revision functions*. *Journal of Symbolic Logic*, 50(2), 510–530. [DOI](https://doi.org/10.2307/2274239) (the publisher record is the authoritative bibliographic target; the earlier DOI form sometimes indexed for this work should not be relied on here).
- Pajasmaa, J., Miettinen, K., & Silvennoinen, J. (2025). *Group Decision Making in Multiobjective Optimization: A Systematic Literature Review*. *Group Decision and Negotiation*, 34, 329–371. Published online 2024. [DOI](https://doi.org/10.1007/s10726-024-09915-8).
- Yin, X., Wang, X., Pan, L., Lin, L., Wan, X., & Wang, W. Y. (2025 revision; initial preprint 2024). *Gödel Agent: A Self-Referential Agent Framework for Recursively Self-Improvement*. arXiv:2410.04444. [Abstract and paper](https://arxiv.org/abs/2410.04444).

## Status

This is a constrained research record. Its central decision statement, typed ledger, and operational-testing programme are proposals. The literature comparisons are intentionally asymmetric: sources are cited for their own results and limits, never as confirmation that GE has operational usefulness beyond a tested scope.
