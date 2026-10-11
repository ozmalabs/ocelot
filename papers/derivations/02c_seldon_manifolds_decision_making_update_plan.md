# Decision making paper: update plan

Target: `papers/formal/02c_seldon_manifolds_decision_making.tex`.
Status: corrected after adversarial review and implemented in Paper 02c revision 3. Review and completion checks: `02c_seldon_manifolds_decision_making_update_plan_review.md`.

## 1. Proposed thesis

**At a declared agent/action scale, a realised decision is the continuation of the operative system through its reachable future geometry. Deliberation is a present process that can change that geometry and thereby change the subsequent continuation. System 1 simply is the autonomous response organisation operating; System 2 is embedded hypothetical processing that can reorganise its conditions through modelling possible futures.**

The declared action scale distinguishes action-level decisions from arbitrary physical transitions. A represented commitment, a realised action, and its eventual outcome require separate names. System 1 does not name the entire operative system: System 2 also belongs to that system, and autonomous learning can also reorganise it.

Preserve the author's stronger identity claim throughout: action is the realised transition. Avoid substituting a claim that an independent chooser merely favours a cheap trajectory. The choosing machinery, if represented, belongs to the system whose continuation is being described.

The proposed account identifies realised decisions with movement to the lowest-energy reachable state in the operative frame. The update must make the meaning of energy, the comparison horizon, and the transition dynamics explicit so this has calculable content. The identity claim and a particular minimum-cost realisation have different argumentative burdens: neither a bare reachability set nor the identity alone proves a minimisation law.

Suggested subtitle: **Operative Continuation, Prospective Deliberation, and Manifold Revision**.

## 2. Why the existing paper needs a scope rewrite

The present abstract and scope explicitly describe a proposed decision grammar and exclude an ontological account or theory of physical execution. That conflicts with the new thesis. Rewrite the draft notice, abstract, scope, operational commitments, and limits together, rather than adding a paragraph while retaining the old exclusions.

Introduce three explicit levels of claim:

1. **Ontological interpretation:** decision and deliberation are transitions of the embedded system; deliberation changes conditions of subsequent continuation.
2. **Formal specification:** declared state, aperture, admissibility, costs, capacity, and transition rules make a finite instance implementable.
3. **Empirical hypothesis:** suitably grounded instances explain human persistence and revision, including autonomous and hypothetical processing. This requires independent measurements and comparisons.

Retain the current distinction between inference, carrying a policy, and realising an outcome. They become different processes within one causal system. A represented plan can persist while its implementation fails.

## 3. Operative organisation and represented landscape

Distinguish the actual organisation that generates transitions from an agent's representation of possible transitions. An agent can omit a consequence without eliminating that consequence from the actual system.

Retain the existing decision description

\[
D(F)=(A_F,L_F,S_F,\Gamma_F,N_F,V_F,R_F).
\]

Add a description of operative state and a grounded transition rule. Schematically:

\[
X_{t+1}=T(X_t,B_t),\qquad D(F_t)=\Pi_{F_t}(X_t,B_t),
\]

where state and boundary conditions are sufficient for the supplied deterministic instance and the projection is a description, not an extra selector. Insufficient observer descriptions require a declared relation or epistemic probability model. These symbols do not assume that a complete causal state is recoverable by an observer. An epistemic probability model does not change the series' underlying deterministic commitment; a genuinely stochastic extension would need a separately stated assumption. Strict minimum prediction cannot cover arbitrary nonminimum stochastic responses.

Use “operative manifold” for reachable geometry together with the fields, constraints, standing structure, and dynamics that determine continuation. Preserve Paper 02's statement that a represented set of reachable histories alone does not select a successor. Explicitly identify which extra structure the update supplies.

A causally complete state with all interventions and boundary conditions fixed has one continuation under the series' deterministic law. Nontrivial comparisons concern intervention-indexed alternatives or a partial operative description; minimum over that family is an additional structural hypothesis. Minimum over a singleton supplies no explanatory evidence. Do not represent unresolved inputs as a free chooser outside the system.

An environment change can alter actual admissibility or dynamics without entering the agent's representation. Therefore the existing surprise/meta-analysis taxonomy concerns represented reopening within its grammar, not every possible cause of changed behaviour.

## 4. Prospective deliberation and the two processing modes

Define active deliberation as a current process concerning continuations that have not yet been realised. Reviewing the past changes present representation and future continuation; it does not change the realised past. Immediate action still has a next causal step. Present deliberation itself is also a realised transition.

Map the user's System 1/System 2 language as follows:

| Term | Proposed interpretation | Qualification |
|---|---|---|
| System 1 | Autonomous response organisation continuing | Includes learned structure, affect, habit, and automatic discrimination; does not name the complete operative system or mean absence of processing or expenditure |
| System 2 | Present hypothetical modelling that can reorganise conditions of continuation | Runs within current organisation, has costs, can fail, and need not successfully change behaviour |

No separate controller stands outside the system. Deliberation, inhibition, preparation, and commitment are causal processes within it. The modes can overlap; avoid a compulsory sequence of “System 2 then System 1.”

Use Evans and Stanovich (2013) as the primary research anchor: their account distinguishes autonomous default processing from working-memory-dependent hypothetical processing and cautions against treating these as exactly two systems. This supports the interpretive connection, not the proposed identity or a universal energy law. Formal exposition should use Type 1/Type 2 where referring to that literature.

## 5. Give “lowest energy” a precise, non-circular specification

The principal formal task is to distinguish:

- Physical energy and resource expenditure.
- A state potential or declared decision score.
- Local transition cost \(c_F(x,y)\).
- Accumulated cost-to-reach \(C_F(y)\).
- Narrativium capacity and the rules converting costs into feasibility.

Do not interchange them. A multi-dimensional comparison needs a declared ordering or scalarisation; Pareto eligibility alone does not supply a unique continuation. Equal minima require a declared resolution rule, which is part of the operative instance.

Start with Paper 02's finite cheapest-successor construction:

\[
b_F(x)=\operatorname{Resolve}_F\!\left(
\arg\min_{y\in\operatorname{Succ}_F(x)} c_F(x,y)
\right).
\]

This is a supplied dynamics specification, not a theorem derived from reachability. It requires a nonempty candidate set and defined costs for every compared candidate. Missing costs remain undefined, and terminal states stop unless a self-loop is explicitly supplied. Ground costs and resolution rules before observing the trajectory; assigning each observed action the smallest cost afterwards explains nothing.

Then state exactly how the author's “lowest-energy reachable state” relates to it. Local successor minimisation is one candidate implementation. A lowest-potential destination or minimum accumulated-cost history over a declared horizon is a different specification and needs its own dynamics or planning process. Do not silently promote the local construction into a global optimum.

Include a small counterexample showing a cheap local step entering a basin while a more expensive step enables a cheaper eventual destination. This establishes the scale of the claim, including ridges, constraints, and horizon. Cycles in an admissible successor policy also prevent treating every instance as strict descent of a state potential.

Preserve Paper 03's equal-baseline condition: positive alteration cost alone does not make reuse globally cheaper when alternative baseline costs differ. Membership changes and unaffordability remain separate.

## 6. Deliberation as manifold revision

Extend the existing self-decision transformation \(F'=\tau(F)\). Give explicit examples of transformations of:

- Aperture dimensions, resolution, and horizon.
- Acceptable target regions and represented consequences.
- Comparison weights, cost conversions, or valuation descriptions.
- Standing Narrative and the structures implementing it.
- Admissibility, capacity, and coupling to other systems.

Distinguish changed representation from changed operative organisation. Imagining an alternative is a real process, but does not necessarily install the structure that would realise it. A represented revision only redirects action when it changes causally relevant conditions.

Account for the cost of revision itself. No future self authorises its own installation; the present organisation generates the transition that makes that future self reachable. Retain the existing antecedent-state constraint without claiming to solve every problem of transformative preference.

Rewrite surprise and expected nonoccurrence as ways that incoming evidence changes current organisation or prompts further modelling. Keep the useful distinction between an already represented resolution and a resolution requiring additional inference. Preserve zero *additional decision inference* for an installed continuation; do not equate it with zero execution, maintenance, or monitoring cost.

## 7. Planned manuscript structure

| Section | Update |
|---|---|
| Abstract and scope | State identity, prospective deliberation, and the distinction between interpretation, specification, and empirical hypothesis |
| Operative state and decision frame | Separate actual organisation from represented landscape; define the supplied dynamics |
| Continuation and cost geometry | Define energy/cost types, horizon, minima, tie resolution, basins, and conditional claims |
| Prospective deliberation | Explain current processing of unrealised futures; integrate Type 1/Type 2 interpretation |
| Surprise and reopening | Retain current examples while limiting the taxonomy to represented reopening |
| Target shapes and feasibility | Retain regions, Narrativium, Pareto incomparability, and declared comparison rules |
| Self-decision and revision | Expand frame transformation into changes of represented and operative organisation |
| Worked finite examples | Demonstrate continuation, revision, failed revision, and local/global distinction |
| Decision quality and consequences | Preserve inference/execution/outcome distinctions; connect whole-system accounting |
| Related work and empirical commitments | Position the contribution and specify independently measurable claims |
| Limits | State what the ontology commits to, what the finite construction establishes, and what remains unverified |

## 8. Worked examples to prepare

1. **Habit:** installed continuation incurs execution cost and no additional decision inference.
2. **Expanded aperture:** a previously omitted future consequence enters representation, changes operative comparison, and changes continuation.
3. **Reappraisal:** the available actions remain the same while their operative ordering changes.
4. **Ineffective intention:** a represented alternative fails to alter the structures implementing the standing continuation.
5. **Constraint or capacity change:** an action becomes inadmissible or unaffordable; distinguish the two.
6. **Local versus global cost:** demonstrate a basin and an escape ridge; declare which minimisation the instance actually implements.

Give costs, boundaries, horizons, state transitions, and revision charges explicitly. Describe actual consequences separately from the agent's represented weights. Paper 11 supplies the relevant whole-system accounting distinction: an actor's aperture or valuation does not erase omitted consequences. Ethical burdens can become inputs to subsequent deliberation without making external consequences identical to an internal decision score.

## 9. Related work and verification

Verified primary anchor:

- Evans, J. St. B. T., and Stanovich, K. E. (2013). *Dual-Process Theories of Higher Cognition: Advancing the Debate*. Perspectives on Psychological Science 8(3), 223–241. [DOI](https://doi.org/10.1177/1745691612460685), [original article](https://www.krigolsonlab.com/uploads/4/3/8/4/43848243/evans_and_stanovich_2013.pdf). Use for autonomous defaults, hypothetical processing, and terminology; avoid inferring an energy law from it.

Revisit the manuscript's existing primary metareasoning and active-inference sources when drafting. Verify the exact propositions used, distinguish resource-rational computation from a literal thermodynamic minimum, and keep Graphic Equalisation residual distinct from variational free energy. Retain defaults and belief revision as neighbours. Additional control/planning or habit research should be added only where it supports a specific claim.

Position the contribution as integrating operative continuation, represented futures, and paid restructuring within the series. Do not claim priority over dual-process cognition, planning, metareasoning, or landscape models.

For empirical proposals, specify state variables and costs independently of held-out actions. Compare a fixed frame with controlled changes to aperture, comparison, or admissibility. Distinguish a wrong transition hypothesis from insufficient observation; an unrestricted unseen field must not rescue every result. Exact neural recovery is not required for proposing the principle, but evidence for a human application must constrain possible groundings.

## 10. Review findings to preserve

The existing 02c review overstates several conclusions: it describes costless cognition, supplies a Narrativium threshold that the current grammar does not establish, and treats future-self constraints as a complete solution to transformative choice. Do not import those claims into the update.

Its proposed alteration-cost tie breaker is a possible declared policy, not a derived universal rule. Its proposed identification of boundary violation with Shannon surprise also needs additional probabilistic assumptions. Preserve the earlier corrections recorded in `papers/REVIEW_FAB51_RESPONSE.md`.

## 11. Completion criteria for the later manuscript update

- Identity language is consistent across abstract, definitions, examples, and limits.
- Every minimum claim names its quantity, domain, horizon, and dynamics.
- The paper never derives unique action from a bare reachable set or a Pareto set.
- Deliberation and its initiation are within current dynamics, with declared costs.
- Representation, operative organisation, and actual consequences remain distinguishable.
- Existing conditional claims in Papers 02 and 03 remain intact.
- Research supports only the propositions actually attributed to it.
- After implementation, increment only the document revision, preserve the series draft identifier/date, build the manuscript, and inspect cross-references and metadata consistency.

## 12. Adversarial review resolution

The review's warranted corrections are incorporated into the implementation requirements:

- Define realised decision at a declared agent/action scale; distinguish represented commitment and outcome.
- Scope System 1 to autonomous response organisation. Both processing types are operative, and autonomous adaptation can also revise the manifold.
- State causal sufficiency, counterfactual comparison domain, and deterministic singleton limits explicitly.
- Define the enriched manifold; changed weights over the same reachable set change its field, not its membership.
- Give minimum policies defined-cost/nonempty-domain/terminal/tie conditions. Preserve local/global distinctions, including the proposed 1+10 versus 2+0 example.
- Restrict the inherited Narrative retention rule to unchanged operative conditions in the declared grammar.
- Give a predeclared field manipulation and held-out failure criterion; prohibit unrestricted hidden-field rescue.

No software tests were run in the planning or review passes. The manuscript update follows this corrected plan.
