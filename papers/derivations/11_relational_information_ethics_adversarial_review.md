# Paper 11: adversarial review

## Scope and assessment

Reviewed the argument plan, plan review, related-work record, finite reference functions, and complete formal manuscript. This is a scholarly and code inspection; no software tests were run. Literature comparisons use the recorded primary-source review, rather than a new systematic search.

The manuscript now makes a defensible conditional contribution: an attributed informational consequence account, finite calculation procedures, and a separately identified compression hypothesis. Its mathematics does not prove that this is the only possible conception of ethics. The paper explicitly identifies the ethical interpretation as its foundational proposition, which is essential to the argument's honesty.

## Actionable findings

### 1. Representation invariance needed stronger premises — high, corrected

The original proposition preserved resource incidence and units without explicitly preserving numerical expenditure. Keeping a payer and joule units fixed while changing expenditure from one joule to two is a counterexample to account equality. The repair proof also assumed preservation of restoration predicates and repair costs that its premises did not state.

The author has added preservation of numerical expenditures, access-price profiles, repair transitions, edge costs, and restoration predicates. With those premises, the stated proof is valid.

### 2. Reusable repair adjacency — medium, corrected

`least_repair` initially validated adjacency entries before traversing them. Generator-valued adjacency would be consumed by validation. The author now materialises each adjacency sequence before validation and search, resolving that implementation defect.

### 3. Access prices must retain their branch indices — medium, corrected

The access-price definition correctly uses `p_ir(y | x)`, but the complete-account tuple originally printed an unindexed `(p_ir)_r`. The author now retains both branch profiles explicitly. One profile alone would not record the comparative change. The contract's general unknown-versus-known distinction also applies here: an unavailable price must remain distinct from an infinite price for a proved-unreachable target.

### 4. Companion relations are not automatically distinct outcomes — medium, corrected

The companion example originally listed three continuing relations and then counted three lost outcomes. A single state can instantiate three concurrent relations without constituting three alternative outcomes under the single-valued outcome map. The author now explicitly stipulates three distinct reachable continuation outcomes, with baseline set `{r1, r2, r3}` and empty action set. That correction makes the count consistent with the outcome-map definition.

## Earlier concerns resolved in the manuscript

- **Possible reachability versus control:** nondeterministic graph support is distinguished from empowerment. The capacity theorem applies only to a deterministic channel with legal inputs attaining every counted output. Its proof is correct.
- **Observer independence versus contract independence:** passive evaluation leaves a fixed causal contrast unchanged; changed horizons, quotients, boundaries and interventions can change an account. The paper does not claim a unique numerical scalar invariant to those choices.
- **Hidden eligibility:** preferences, recognition, sentience and biological category are not entry conditions. Outcome quotients must be justified in affected dynamics; desirability weights belong in evaluation. `None` means no instantiated continuation, rather than an unwanted or disregarded continuation.
- **Unknown versus zero:** omitted dictionary keys have an explicit known-empty or measured-zero interpretation. Unknown inputs cannot legitimately be encoded through those omissions.
- **NPC endpoint versus path:** zero continuing loss is conditioned on exhausted roles and an aligned encounter boundary. Intermediate capabilities, player effects and resources remain accountable. Design purpose alone is not a proof. A thousand zero terminal losses do not erase positive path burdens.
- **Double counting:** shared physical expenditure, overlapping collective accounts, repair estimates and actual repair expenditure are distinguished. Count and capacity summaries are not added as independent losses.
- **Decision weights:** the dominance proposition restricts weights to a nonnegative class; it does not impose that class on every possible evaluator.
- **Compression:** the fibre criterion is correct for a fixed decision map. The uniform approximation bound yields regret at most `2 epsilon`; score preservation is distinguished from preservation of the full account. These results demonstrate feasibility rather than a recovered biological mechanism.
- **Worked values:** the protective scores are `-2` and `4`; the deterministic capacity changes are one bit lost and two gained; the restoration exposure is six capability-time units. These follow by direct inspection.
- **Prior work:** information ethics, empowerment-based robotic ethics, reachability penalties and executable moral-choice models receive substantive attribution. No priority claim for informational or computational ethics is made.

## Residual conceptual disputes

1. **Identification versus necessity.** A critic can call the construction an informational impact ledger and reject its identification with ethics. The structural proofs cannot settle that dispute. The manuscript exposes this commitment and can defend it through explanatory and practical usefulness without introducing a moral eligibility gate.
2. **Grounding and completeness.** Counterfactual transitions, affected partitions, continuity and consequential distinctions must be grounded. The functions compute supplied finite models; they do not infer a correct model of an arbitrary system. A coarse zero cannot certify that the actual system is costless. No general completeness theorem is established.
3. **Compression adequacy.** Animal helping, intuition, mind attribution and dietary patterns support motivation for the hypothesis, not identification of its mechanism. Independently fixed information, compression and weights are needed for discriminating behavioural predictions. Neural recovery is not a prerequisite for the formal construction's value.
4. **Novelty is integrative.** The closest predecessors already calculate informational control and reachability-based impacts, sometimes for robotic ethics. The new contribution must rest on the particular attributed account, observer-independent interpretation, handling of burdens and histories, and compression bridge. The manuscript presently states that narrower contribution.

## Recommendation

All actionable findings above have been corrected. No further mathematical blocker was found under the manuscript's stated finite and comparison assumptions. Retain the explicit separation between the foundational ethical lens, proved properties of the account, and the biological hypothesis. The substantive limitations above remain research and philosophical boundaries, rather than unresolved implementation defects.

## Revision review: whole-system accounting and moral injury

This review concerns the subsequent manuscript titled **Relational Information Accounting**, following the author's clarification that the foundational object is whole-system accounting and ethics is an application. It supersedes the initial review's discussion of identifying the account itself with ethics.

### Consistency assessment

- The abstract, foundational proposition, derivation boundary, and conclusion consistently present general informational consequences as the foundational construction. No remaining proposition equates ethics itself with the account. References to ethical cost in the game application remain application language rather than a moral eligibility condition.
- The causal boundary now explicitly includes the actor, witnesses, dependants, and institutions. This extends attribution without changing the calculation functions or adding units together.
- Internal expectations and commitments are treated as actual causal organisation. Their role in a particular person's response does not introduce an externally imposed moral axiom into general accounting.
- Awareness that changes a person's state is distinguished from passive evaluation. Learning about an event can create additional consequences without retrospectively constituting the original recipient's loss. False beliefs can have real effects in their bearer without instantiating the falsely represented external injury.
- The expanded toy example is arithmetically consistent: the actor's three-to-one outcome restriction gives two lost outcomes, and two additional resource units contribute `2 alpha_P + 2 gamma_P,r` to the declared score. Selecting the action does not erase either entry.

### Primary-source check

Litz and colleagues' descriptions include perpetration, failure to prevent, witnessing, and learning about events that conflict with deeply held commitments; their proposed model concerns possible persistent consequences rather than an inevitable injury after every exposure. The manuscript's event descriptions and treatment of internal commitments are consistent with that source. [Litz et al. (2009), primary article hosted by the US Department of Veterans Affairs](https://www.ptsd.va.gov/professional/articles/article-pdf/id33165.pdf).

Shay distinguishes betrayal involving legitimate authority from the self-perpetration formulation and explicitly discusses impaired capacity for trust. The manuscript correctly attributes its authority-and-trust description without presenting it as the only formulation. [Shay (2014), primary article](https://www.penncerl.org/wp-content/uploads/2022/01/4602-moralinjuryshayexcerptpdf.pdf).

### Remaining interpretive boundaries

1. The moral-injury section proposes a structural interpretation; the general accounting results do not validate a clinical causal mechanism. Its explicit distinction between a clinical construct and a capability count, and its statement that the toy example supplies no diagnosis, preserve that boundary.
2. Not every morally distressing event necessarily closes a reachable outcome. Some changes could concern reliability, access expenditure, affect, or a temporary course while leaving the terminal support set unchanged. Those dimensions require their own grounding; a zero finite support-set loss cannot rule out the phenomenon.
3. “Whole-system” is a causal-coverage aim, not a proof of exhaustive observation. The manuscript explicitly retains finite boundaries, unresolved effects, and collective overlap.

No new actionable mathematical defect or stale foundational ethics-identification claim was found in this revision. The revised framing is broader than an ethical impact ledger and accommodates moral injury without claiming that observer independence excludes causally active interpretation or awareness. No tests were run for this review.

## Final clarification: ethics as an accounting frame

The final revision strengthens the previous “ethics as application” formulation. Its proposal is that narrower operational accounts omit affected bearers, enabling relations, and continuing burdens; ethical considerations appear as extra requirements because those accounts exclude consequences already instantiated under the relational ontology. Ethics becomes an accounting frame that makes those effects and their incidence legible. This formulation now agrees across the introduction, derivation boundary, account definition, and conclusion.

The interpretation remains coherent with the mathematical results. Broader causal coverage changes what a measurement contains; it does not make an evaluator create the previously omitted consequences. Relative weights still guide decisions after accounting. The manuscript correctly distinguishes this structural explanation from an empirical chronology of moral language or practices, so it makes no unsupported historical-origin claim.

The moral-injury section now expressly states that unchanged support can conceal changed reliability, burden, or experienced effects. Grounded transition probabilities, control channels, and additional affective or physiological dimensions must supplement the finite support calculation where instantiated. This addresses the preceding review's remaining support-set limitation without claiming that the printed finite functions provide clinical validation or implement every such additional dimension.

No new conceptual inconsistency or actionable defect was found in this final clarification. It supersedes the earlier review's weaker application wording; grounding, coverage, and empirical compression remain the substantive boundaries. No tests were run.

## Third revision: operative valuation and rejected self-description

Reviewed the new operative-valuation section and `shadow_price_bounds`, `policy_distance`, and `valuation_gap` by inspection. The section correctly separates the derived consequence account, the actor's operative evaluation, what the self-model admits or rejects about that evaluation, and the consequences of confronting or revising the self-description. A written monetary conversion is not presented as an intrinsic scalar cost of a life.

### Findings and corrections

1. **Nonnegative conversion — medium, corrected.** The interval implementation starts its lower bound at zero and therefore assumes `lambda >= 0`. The author has made that assumption explicit in the conditional decision model and function documentation.
2. **Finite numerical threshold — medium, corrected.** Finite positive loss and finite resource inputs can overflow a floating-point quotient. The function now rejects an overflowed threshold, avoiding an infinite recovered conversion or falsely consistent `[infinity, infinity]` interval.
3. **Writing is not necessarily admission — medium, corrected.** The condition `e_v` denotes confronting or writing a number, which need not mean accepting it as descriptive. The author now expressly identifies its account as exposure or expression and adds a distinct acknowledgement condition, requiring a separately grounded change in admission or the self-model. This preserves the carrying-versus-admitting distinction.

### Results that check out

- Under a fixed scalar score and matched effects, accepted choices give lower bounds and rejected choices give upper bounds, with ties admitted. The three-to-five example yields an interval, not proof that four is the actor's unique value. Inconsistent bounds reject the scalar model.
- Empty evidence provides no identified finite price. Empty operative candidates produce an undefined gap, not evidence of self-model rejection. Unprobed admission status must remain unknown; the function explicitly requires fully classified operative candidates.
- The exclusion set, disjointness indicator and rejection fraction are correct for a fixed finite grid. Grid sampling affects the fraction; it is neither discomfort intensity nor an invariant psychological quantity.
- Total variation is an appropriate finite action-distribution difference under matched conditions. It measures behaviour, without certifying self-model change or the absence of additional costs.
- Paper 01b's realisation distinction supplies the intended internal dependency: changed modelling is distinct from newly occurring historical facts, while the modelling itself remains part of the self and can alter later actions.
- Taboo trade-offs and motivated reasoning are attributed as relevant predecessors and alternatives. The specific discomfort-driven rejection explanation remains a hypothesis, with audience, incentives, misunderstanding and decision conditions named as competing explanations.

### Remaining interpretation boundary

Observed finite choices alone do not prove that a self knowingly carries a stable numerical price, nor that a refusal to describe choices is caused by discomfort. They can constrain a declared model, and the finite gap can quantify disagreement with its descriptive candidates. Independent evidence is still needed for the proposed self-model mechanism. Acknowledgement can have gains, losses or no detected change; it is not automatically moral injury. The manuscript retains those distinctions. All actionable findings in this revision were corrected and inspected; no further mathematical blocker was found under the stated conditions. No tests were run.

## Fourth revision: revealed choices and elicitation through play

The compatible-weight construction in `eq:revealed-self` is correct under its stated stable linear model, aligned features, known available alternatives, and tie allowance. Adding observations while preserving that model intersects the candidate family with further constraints and therefore cannot enlarge it. Empty and multiple-model results receive the correct interpretations; actor-relative beliefs are distinguished from actual affected consequences. Recovering an operative disposition does not establish that it ought to be retained.

The play subsection also preserves the essential distinction: an answer to “fuck, marry, kill” or “would you rather” is an actual speech choice but hypothetical evidence about the imagined acts. It is not their enactment, proof of self-model admission, or validation of the proposed discomfort mechanism. Audience, humour, imposed options, refusal, and elicitation changing the actor are expressly included.

Two minor clarifications were recommended and incorporated:

- The candidate-family description now excludes the zero vector for informative reconstruction and explicitly notes positive-rescaling equivalence and the need for a declared scale convention.
- The play example now explicitly compares relation assignments, without implying a single total ranking of people across distinct relation types.

The further local-collapse construction is also coherent. Restricting previously open self-descriptions `D_M` to `D_M intersection D(q)` is a valid conditional update when an answer is admitted under its declared reading. A proper nonempty subset records resolved ambiguity; an empty intersection exposes a conflict, rather than identifying a coherent recovered self. Crucially, the manuscript distinguishes pressure to supply an explicit comparison from demonstrated psychological admission. Refusal, humour, and rejection of the literal reading can resist the attempted collapse. The equation does not itself prove that every game answer forces internal admission or uncovers a disposition unchanged by elicitation.

No material mathematical blocker or conflation between elicited and consequential behaviour was found. The proposed role of self-versus-self-model in ethical inquiry remains an explanatory hypothesis, rather than a proof that every ethical inquiry recovers a stable hidden utility or that finite observations recover the entire self. No tests were run.

## Fifth revision: omitted harmful continuations and unlikely events

The new crime-programme example correctly distinguishes a harmful continuation omitted from an actor model from one represented and assigned low probability. Under an aligned comparison contract, membership in `R_theta` but absence from the admitted model set establishes omission. It does not establish motivated refusal, a real probability of zero, willingness, or equal propensity across people. The manuscript explicitly requires additional evidence for motivation and recognises reasonable surprise, ignorance, and condemnation as alternatives.

Recognition is also treated consistently: admitting an already feasible continuation into a model need not create its feasibility in the original event, while the information can change the observer's later conduct and relationships. An ordinary-looking person's conduct can challenge a shared self-description without proving that every other person's capabilities or constraints are identical. Conditional access, resources, circumstances, and independently grounded feasibility remain explicit.

One wording correction was recommended and incorporated: resistance at admission is now attributed to the specific protective-self-model hypothesis, with an explicit statement that compression alone need not resist updating. This avoids deriving resistance from the general compression hypothesis. Bandura is appropriately presented as adjacent self-regulation work, rather than proof of this observer mechanism or universal criminal reachability.

The attribution correction was inspected; no remaining new conceptual or mathematical defect was found. The example remains an explanatory hypothesis about some responses, not a diagnosis based on a television remark. No tests were run.

### Fifth-revision addendum: dehumanisation and represented exclusion

The new subsection correctly places the illustrative exclusion gate in the actor's represented account, rather than in the framework's eligibility conditions. Exclusion, changed weights, and changed beliefs are distinguished; the actual affected person's losses remain attributable. A reduction in perpetrator self-censure or sanctions is a possible real consequence, without cancelling victim, witness, or institutional losses.

Two precision corrections were recommended, incorporated, and inspected: the product `e_i,M * L_i` now requires a finite grounded loss, avoiding an undefined zero-times-infinity case; and unchanged capabilities and continuations explicitly concern the victim's loss rather than every whole-system state. Changing the actor's representation can itself cause real consequences and requires its own accounting, which the revised paragraph expressly retains.

The cited experimental comparison is supported by the primary article: it distinguishes instrumental-harm responses from harm regarded as deserved, using attitude surveys and hypothetical vignettes. The manuscript correctly avoids treating those findings as a causal demonstration of genocide or claiming that every atrocity requires dehumanisation. Recognition of humanity can coexist with a justification for harming the recognised victim. [Rai, Valdesolo and Graham (2017), primary article](https://pmc.ncbi.nlm.nih.gov/articles/PMC5559031/).

No further material issue was found. This remains a proposed informational interpretation of represented exclusion and its causal consequences, rather than a universal account of mass violence. No tests were run.

## Sixth revision: energy states, decision fields, and reclassification routes

The manifold formulation is consistent with Paper 02's operational definition: it represents reachable states or histories and need not be a smooth differential-geometric manifold. The new `Phi_M` equation supplies a conditional scalar decision field only after declaring feature conversions and a minimising policy. It does not identify a decision score with physical energy, force motion through an unspecified gradient, or add energy and capacity without conversion. Capacity loss remains separately typed.

Comparing “act” with “change the model, then act” correctly retains the transition price of propaganda, coordination, or internal revision. A lower later score does not establish that the complete course is cheaper for the actor, much less that affected victims lose fewer futures. The proposed compressed regulation remains an explanatory hypothesis, without a recovered neural energy model.

The opening of the dehumanisation subsection now clearly distinguishes retained represented loss with a favourable justification from reduced represented loss following reclassification. These routes can coexist. Neither the equation nor the cited studies establishes their distribution among perpetrators or a majority prevalence.

The restricted Kelman summary is supported by the primary abstract: his account concerns sanctioned massacres and authorisation, routinisation, and dehumanisation weakening restraint. It is a theoretical account, not an experimental prevalence estimate. [Kelman (1973), publisher abstract](https://spssi.onlinelibrary.wiley.com/doi/10.1111/j.1540-4560.1973.tb00102.x).

Landry and colleagues' language analysis supports the stated pre-onset decrease in experiential attribution. The manuscript correctly limits this to propaganda, notes missing archival data, and does not infer individuals' mechanisms or causal sufficiency. The article also reports increased agentic attribution after onset, interpreted as possible demonisation. That optional nuance was recommended because it illustrates multidimensional and coexisting routes; the current pre-onset claim remains accurate without it. [Landry, Orr and Mere (2022), primary article](https://pmc.ncbi.nlm.nih.gov/articles/PMC9645591/).

No material new mathematical or conceptual defect was found under the declared grounding and policy assumptions. No tests were run.

### Sixth-revision addendum: population margins and ambivalence

The decision-margin signs and normal-response formulas are correct. Under the declared minimising policy, positive margins favour the comparison action; a common nonnegative reduction recruits actors whose original margins lie below the shift. Normality gives the stated standard-normal CDF, and the symmetric near-zero probability is the difference between the two boundary CDF values. With positive mean, the baseline proportion is below one half and a shift greater than the mean raises it above one half.

The manuscript properly makes common calibrated score units, normality, uniform shifts, fixed opportunities, and the chosen ambivalence width explicit assumptions. Neither normality nor the informational foundations establishes an ambivalent majority. A small net margin can combine strong opposing commitments, so the band is not automatically psychological indifference or an intrinsic character measure. The Granovetter comparison also preserves the distinction between an exogenous shift here and participation-dependent thresholds in his social model.

The initial `normal_response` implementation followed the formulas at ordinary numerical scales and returned an undefined band summary when no width was supplied. The author has incorporated overflow-aware standardisation before the standard-normal CDF, with a divided-input fallback when subtraction overflows; the correction was inspected. Even robust floating-point CDFs remain approximations rather than validation of the population parameters.

The author also incorporated the optional interpretation clarification: the symmetric near-zero band measures broader threshold proximity, while newly recruited actors have original margins between zero and delta and proportion `p_h(delta) - p_h(0)`. The implementation now returns that separate recruitment fraction. Sensitivity at the mean is expressly scoped to an admissible positive mean.

No material mathematical defect in the stated population model was found. The model quantifies a declared hypothesis rather than establishing population prevalence or making ordinary actors necessarily participate. No tests were run.

## Seventh revision: empirical support and distributional limits

The new evidence subsection accurately supports context-sensitive conduct without presenting the evidence as validation of Gaussian ethical margins or an ambivalent majority. The general response formula is now correctly stated for a continuous CDF: shifting margins by delta gives response `F(delta)` and recruitment `F(delta) - F(0)`. The manuscript expressly requires one-sided probabilities and a tie rule for distributions with atoms. The threshold mechanism therefore survives without normality; the finite normal function remains a conditional specialisation.

### Source strengths and limits

- Dana, Weber and Kuang experimentally changed choice–outcome transparency in a dictator game and observed reduced generosity. This supports information-conditioned choice, without uniquely recovering a self-model mechanism. [Primary author-hosted article](https://www.scheller.gatech.edu/directory/research/accounting/kuang/pdf/dwk_2007.pdf).
- Vu and colleagues' primary abstract supports the manuscript's 6,531 participants, 56 treatment effects, approximately 40% information avoidance, and 15.6-percentage-point behavioural contrast. These are pooled experimental results, not an estimate that most people possess a stable ambivalent trait. Avoiding unknown outcome information is correctly distinguished from refusing to admit an already operative valuation. [Authors' institutional record](https://research.tilburguniversity.edu/en/publications/ignorance-by-choice-a-meta-analytic-review-of-the-underlying-moti/).
- Luft's 2015 interviews support behavioural crossing among killing, desistance, and saving, without establishing a population proportion or proving that stable weights rather than circumstances changed. [Primary institutional record](https://escholarship.org/uc/item/5744x91r).
- Luft's 2023 retrospective analysis supports an examined trajectory of violence, habituation, and subsequent diminished social meaning. It neither proves universal causal ordering nor specifically validates conscious reclassify-first decisions. The manuscript correctly includes implicit change, action-to-field feedback, triangulation, and limits of generalisation. [Primary publisher article](https://journals.sagepub.com/doi/10.1177/07352751231203716).
- Asch's observed conformity-error counts are explicitly non-normal in the original report. Those counts concern a different task and observed variable; they neither verify nor falsify normal latent ethical margins. The manuscript retains that distinction.

One source precision correction was recommended and incorporated: Luft 2023 screened for respondents who had never killed another human, rather than demonstrating absence of every earlier violent act. The manuscript now correctly says “selected first-time killers.”

The section presents supported phenomena for the theory to explain, not unique empirical identification of its compression or protective-self-model mechanism. No additional mathematical blocker was found. No tests were run.

### Seventh-revision addendum: implicit adaptation and adverse identity admission

The added paragraph consistently separates changed operative conduct, awareness of acts or consequences, and admission that one's own disposition has deteriorated under retained standards. Its claim is conditional on standards that condemn the change; conscious reinterpretation can instead justify conduct and preserve a favourable self-description. Consciousness therefore does not automatically imply self-condemnation.

The proposed avoidance of an identity-conflict burden is properly marked as a self-model hypothesis, rather than inferred from habituation alone or reported as Luft's demonstrated causal mechanism. Bandura receives adjacent attribution without becoming proof that every actor adapts unconsciously to avoid admitting deterioration. Any claimed benefit of avoiding confrontation needs independent grounding in the particular trajectory, as the paragraph states.

No new material inconsistency was found. The sample-description correction was also inspected. No tests were run.

## Eighth revision: full manuscript and implementation review

Scope: inspected the current complete manuscript, mathematical arguments, worked cases, self/self-model and population sections, and the finite reference functions. This was a scholarly and code-inspection pass; no software tests or benchmarks were run. The following newly identified issues were corrected by the author and the corrections were inspected.

| Initial severity | Location | Finding and inspected correction |
| --- | --- | --- |
| High | `reachable`; finite-realisation subsection | Revisited states could consume generator-valued adjacency a second time and silently lose transitions. Adjacency is now materialised once, preserving the supplied finite transition relation. Complexity includes materialisation. |
| High | `least_repair`; finite-realisation subsection | A finite floating-point path sum could overflow to infinity and be mistaken for an unreachable repair. Explored path-cost overflow now raises an explicit error; returned infinity retains the meaning unreachable. |
| Medium | `compare_futures`, interval profiles, `evaluate` | Finite inputs alone did not ensure finite aggregate masses, exposures, or scores. `_finite_result` now rejects out-of-range computed results, including nonfinite scores, instead of reporting them as measured consequences. The finite-arithmetic limitation is stated. |
| Medium | Effects along the course; `eq:account`; `eq:decision` | The former account retained temporary losses but omitted temporary gains absent at the terminal boundary. It now retains both path profiles, separately grounded gain exposure, an optional converted gain-exposure decision term, and a temporary-gain worked example. `gain_profile` shares the aligned interval calculation with `loss_profile`. |
| Medium | Informational consequence account; moral-injury subsection; invariance hypotheses | Unchanged support can hide changes in outcome reliability or control. The account now explicitly retains grounded stochastic-transition or control-channel records where applicable, with corresponding preservation conditions in the invariance propositions. The finite support implementation is expressly a specialisation rather than machinery for every stochastic channel. |

The inspected definitions and proofs are consistent under their declared assumptions. Set differences retain substitution, extinction does not become a logarithm of zero, deterministic channel capacity requires controllable outputs, course exposures retain their distinct units, and repair estimates are separated from incurred expenditure. The observer proposition fixes causal relations and the contract; it does not claim that causally effective learning has no consequences. Decision weights are separate from grounded measures, and no additional species, sentience, preference, or evaluative-recognition eligibility condition has appeared.

The extended self/self-model argument also preserves its inference boundaries. Revealed-choice reconstruction is conditional on known alternatives, aligned belief-relative features and a stable decision family; it need not identify a unique weight or the entire self. Elicited speech, literal commitment, admitted self-description and consequential action are distinguished. The discomfort and adverse-identity explanations require independent evidence, including retained condemning standards; habituation does not itself establish those mechanisms. The general continuous-CDF shift calculation, Gaussian specialisation, recruitment fraction and near-zero-margin probability are mathematically correct under their stated common-unit and fixed-comparison conditions. Normality and a psychologically ambivalent majority remain hypotheses.

Nuanced empirical claims were rechecked against the primary [Luft 2023 article](https://journals.sagepub.com/doi/10.1177/07352751231203716) and [Landry et al. 2022 article](https://pmc.ncbi.nlm.nih.gov/articles/PMC9645591/). The manuscript correctly treats retrospective killing/habituation trajectories as evidence permitting action-to-model feedback, without asserting universal causal order or demonstrated identity-protection motivation. Its propaganda claim concerns measured experience language and acknowledges archival missingness; it does not infer individual mechanism prevalence or causal sufficiency. Earlier source checks on information avoidance, heterogeneous behavioural crossing and conformity remain applicable: none validates Gaussian ethical margins or a majority near zero.

### Remaining substantive limitations

- The informational construction is a consequence account under inherited relational foundations and explicit accounting definitions. The thesis that ethics functions as a frame for otherwise omitted consequences is a structural explanatory proposal; the proofs do not independently establish an exhaustive theory of every moral concept or a historical origin of morality.
- Compression, protective self-modelling, classification-induced field shifts, and population ambivalence require discriminating empirical assessment. Matching the cited phenomena does not uniquely identify these mechanisms. The current manuscript states these boundaries and requires fixed predictive specifications rather than refitting every observation.
- Implementation requires supplied causal graphs, outcome identity, incidence, grounded units and completeness conditions. Finite support functions do not recover an unknown world, a brain mechanism, arbitrary experienced burdens, or stochastic channel capacity. Overflow is now reported honestly but can interrupt a repair search even if another in-range route exists; the documented routine is a finite-arithmetic reference, not an arbitrary-precision solver.
- A minor precision clarification was also incorporated and inspected: `policy_distance` documents its `1e-12` normalisation tolerance and floating-point error, while the manuscript calls its result an approximation and scopes the exact range bound to exactly normalised distributions. This is an acknowledged numerical limit rather than an outstanding defect.

**Full-pass verdict:** all newly identified material corrections were incorporated and inspected. No remaining material mathematical inconsistency, hidden moral eligibility gate, or unsupported empirical claim requiring a further manuscript change was found. This verdict concerns the stated conditional construction, not empirical validation of its open psychological and population hypotheses.

## Ninth revision: trolley outcomes and the operator's state

The trolley subsection was inspected for attribution, counterfactual alignment and numerical scope. No material correction is required. `eq:trolley-operator` selects the operator's attributed component of the existing account; it does not create a separate clinical guilt function or identify internal cost with the casualty count. Initial organisation and branch-specific continuations can produce different operator entries while the explicitly stipulated external branches remain fixed. This is a conditional comparison, not a claim that varying the operator never changes real external outcomes.

The manuscript expressly distinguishes attribution from causal isolation: information about the casualties can affect the operator's internal transition. It also retains the possibility that declining to act has internal costs, so a difference relative to inaction is not a claim that inaction has no consequence. Actor, witness and institutional entries require their declared incidence and overlap treatment. Fixed external losses cannot be erased by the operator feeling justified, and an internal burden cannot be inferred from the numbers alone.

The toy arithmetic is correct: baseline `{u,v,w}` versus `{u}` loses two outcomes; two additional resource units give incremental burden two. Preserving the three outcomes with unchanged expenditure gives zero in those specified dimensions, with other dimensions explicitly left for investigation. These are supplied finite inputs, not measured psychological magnitudes or evidence that every operator's actual cost is currently recoverable. No universal answer to the trolley dilemma is derived from the account.

The attribution to [Thomson's 1985 primary text](https://studylib.net/doc/18464277/the-trolley-problem) was independently checked. The article discusses the driver and bystander, differences in responsibility, and discomfort about intervention. The manuscript appropriately acknowledges this established interpretation and claims separately calculable consequences rather than inventing the operator-state distinction. No software tests were run.

## Tenth revision: psychopathic traits and ethical aperture

The new subsection keeps three routes distinct: processing available information into represented features, evaluating those features, and undergoing actual state-dependent internal consequences. The notation `Q_j(o_j)` followed by `w_j · zhat_j` is a coherent conditional model, while behaviour alone need not identify the processing/weighting decomposition. Attention, impulsivity, learning and policy instability are expressly allowed to require richer models. Victim losses do not diminish with an actor's reduced concern; the actor's own aversion or identity conflict can differ where independently grounded. No uniform trait profile, clinical diagnosis, zero-empathy assertion, or additional moral-eligibility exception is derived.

Two precision recommendations arose:

- **Minor editorial:** remove reference to “the user's” comparison from the scholarly manuscript. This correction was incorporated and inspected; the text now speaks directly of measured profiles and labels that do not specify accounting inputs.
- **Minor source precision:** describe Hauser's findings as associations rather than distinct effects, and acknowledge the study's different, nonrandomised dilemmas across emotion-processing conditions. That design limits causal attribution of condition differences to processing alone. Both refinements were incorporated and inspected.

The [Tassy 2013 primary abstract](https://pubmed.ncbi.nlm.nih.gov/23761743/) supports the stated 102-student sample, self-report trait measurement and association with hypothetical sacrificial choices rather than acceptability judgements. It does not establish enacted behaviour or framework-specific weights. The [Hauser 2021 primary full text](https://onlinelibrary.wiley.com/doi/full/10.1002/bsl.2547) verifies the 60-male-offender sample and heterogeneous facet/condition associations, including differing directions; its explicit design limitation motivates the recommendation above. These studies support separating judgement, processing and hypothetical choice without uniquely identifying the proposed aperture mechanism or actual internal burdens. No software tests were run.

## Eleventh revision: inherited aperture and ethical flexibility

The revised definition was checked directly against Paper 01's `def:aperture` and Paper 02's `rem:aperture` and `rem:aperture-shape`. It preserves the input gate, represented dimensions, grain and extent, rather than replacing the inherited aperture with a scalar sensitivity or a decision weight. The further ethical-region predicate is explicitly distinct from that input gate and subsequent priorities. Under a fixed represented manifold, relaxing a predicate can admit more continuations; contextual or readily revised conditions can describe flexibility without implying a globally wider aperture.

`eq:ethical-region` is a valid subset construction. The effective no-restriction case equals the represented feasible manifold on the specified domain; it does not require an explicit ethical predicate, remove nonethical feasibility constraints, or establish the absence of every ethical response. Absent represented dimensions remain undefined rather than numerical zero. Low weights, sparse conditions and absence of dimensions are distinct cases, while affected victims remain in the actual consequence account.

One minor inheritance clarification was recommended, incorporated and inspected: the paragraph predicting little scrutiny for comfortable fit and refinement near a boundary now explicitly names and references the inherited fit/adaptive-resolution hypothesis. Paper 02's shape remark links that allocation to `hyp:adaptive-resolution`; attention allocation is not a theorem of the region predicate or dimensions alone. The paragraph also distinguishes structural possibilities and predictions from established global flexibility.

The source qualifications remain accurate: the studies distinguish judgement, hypothetical choice, facets and processing contexts, but do not establish absent ethics, quantify aperture geometry or recover acceptability predicates. No new material mathematical or eligibility inconsistency was found. No software tests were run.
