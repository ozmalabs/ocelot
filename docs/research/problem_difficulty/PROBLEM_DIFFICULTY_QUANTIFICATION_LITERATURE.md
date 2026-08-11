# Can problem difficulty be quantified in advance? — a literature survey

**Purpose.** The project's creator posed a precise question, worth restating exactly
because the precision matters: *"the problem space grows at rate Z, the program space
for the same problem space should be supralinear, and possibly knowable as a rate (or
at least a trend), such that we can actually have meta confidence in tractability… start
another agent to research this, check the latest papers and see if we can actually
quantify this — which would allow us to give confidence intervals for solving a known
problem, based on known priors. The primary difference would be known solvable vs not
known. eg: human level insight is possible at low power because humans exist."*

This document is a literature survey answering that question as rigorously as the
evidence allows, in this project's own house style: **a clean, precise null is a
complete and valuable answer.** It is not a design document and proposes no repo
changes — it is citable input for whichever document (this one or a future synthesis)
needs the actual state of the science. Every citation below was verified via live web
search and, for the load-bearing ones, a direct fetch of the abstract/source — not
recalled from training data. Anything that could not be independently confirmed beyond
a search-result summary is labeled **[unverified beyond abstract]**; nothing below is
presented as more certain than it is.

**The verdict, stated up front so nothing below reads as a slow build to a foregone
conclusion:** there is no general, cross-domain, quantitative law relating
problem-space growth to required-program-space growth, and — more importantly — this
is not merely an unfilled research gap. Two independent formal results (No Free Lunch,
§1; an Arrow-style impossibility theorem for intelligence measures, §6) prove that no
fully general version of such a law *can* exist without restricting to a specific prior
over problems. What exists instead is a family of **rigorous-but-narrow** results (PAC
bounds within a fixed hypothesis class; Levin-search optimality with unusable
constants) and a family of **mature-but-domain-specific empirical** results (SAT
hardness prediction; ARC-AGI human-solve-rate calibration). The "known solvable vs. not
known solvable" existence-proof framing the creator offered as the sharpest cut *does*
have a real literature — but its most careful treatments exist mainly to show why the
naive version of the argument is a fallacy, and what it takes to repair it. See §9 for
the full synthesis and §10 for the honest path forward.

---

## 1. Occam learning / PAC-learnability — and why no rate generalizes across classes

**Blumer, A., Ehrenfeucht, A., Haussler, D., Warmuth, M.K. (1987). "Occam's Razor."
*Information Processing Letters* 24(6), 377–380.** DOI: 10.1016/0020-0190(87)90114-1.
The origin of "Occam learning" as a formal computational-learning-theory concept: a
polynomial-time algorithm that finds a hypothesis significantly *shorter* than the
sample and consistent with it is a polynomial-time PAC learner. This converts a
compression bound into a sample-complexity bound — but strictly **relative to a fixed
hypothesis representation/class**. It says nothing about how the required
hypothesis-space size scales *across* different problem classes.

**Blumer, A., Ehrenfeucht, A., Haussler, D., Warmuth, M.K. (1989). "Learnability and
the Vapnik-Chervonenkis Dimension." *Journal of the ACM* 36(4), 929–965.** DOI:
10.1145/76359.76371. Establishes finite VC dimension as necessary and sufficient for
distribution-free PAC-learnability, with sample complexity ~O(VCdim/ε·log(1/ε) +
1/ε·log(1/δ)). Still a property of a *fixed* concept class, not a cross-class law.

**Wolpert, D.H., Macready, W.G. (1997). "No Free Lunch Theorems for Optimization."
*IEEE Transactions on Evolutionary Computation* 1(1), 67–82.** This is the load-bearing
result for the whole thread, and it is a proof, not a gap: averaged uniformly over
*all* possible problems/objective functions, every optimization algorithm performs
identically. **No single problem-size-vs-hypothesis-size rate can hold universally
across unrestricted problem classes.** Any such rate is necessarily conditioned on a
restricted class of problems — a prior/structure assumption — which is exactly why VC
bounds are always stated relative to a fixed hypothesis class. This is the first of two
independent impossibility-shaped walls this survey found (the second is §6's Arrow
result for intelligence measures); the two are structurally the same finding arrived at
from different directions twenty-eight years apart.

**Goldblum, M., Finzi, M., Rowan, K., Wilson, A.G. (2024). "The No Free Lunch Theorem,
Kolmogorov Complexity, and the Role of Inductive Biases in Machine Learning." ICML 2024
Position Paper track, arXiv:2304.05366.** Argues NFL is technically true but
practically escapable, because real-world problems are **not** drawn uniformly from
problem-space — they disproportionately have low Kolmogorov complexity, and successful
architectures (CNNs, LLMs) share that same low-complexity inductive bias. This reframes
the difficulty question from "how does hypothesis-space size scale with problem-space
size in general" (provably answerless per NFL) to "what is the complexity of the
*actual* distribution of problems we care about" — which routes straight back to
Kolmogorov/Levin complexity (§2).

**Boopathy, A., Liu, K., Hwang, J., Ge, S., Mohammedsaleh, A., Fiete, I. (2023).
"Model-agnostic Measure of Generalization Difficulty." ICML 2023, pp. 2857–2884,
arXiv:2305.01034.** [Verified: ICML proceedings + arXiv abstract fetched directly.] The
single most direct hit in this entire survey on the creator's literal target — an
"inductive bias complexity" measure (information needed to generalize, minus
information the data supplies, via the fractional hypothesis-volume that both fits the
data and generalizes) that **does** produce a scaling relationship: difficulty scales
*exponentially* in the intrinsic dimensionality a model must generalize over, but only
*polynomially* in resolution per dimension. Validated empirically across vision
benchmarks and MDP observability (recovers intuitive orderings: MNIST < CIFAR10 <
ImageNet; fully-observable < partially-observable MDPs). This is real and current, but
it is one 2023 paper proposing a new measure, not a field-wide-established law on par
with VC-dimension bounds — treat it as the most promising empirical lead in this
thread, not as settled science.

**Thread verdict.** The field has not produced, and — per Wolpert & Macready — cannot
produce, a domain-independent law relating problem-space growth to hypothesis-space
growth that holds unconditionally. What's real is narrower: rigorous bounds *within* a
fixed class (Blumer et al.), a 2024 argument for why real problem distributions escape
the NFL wall by concentrating on low-complexity instances (Goldblum et al.), and one
concrete, promising, but young empirical scaling proposal (Boopathy et al. 2023).

---

## 2. Algorithmic information theory — Levin complexity, Levin search, Solomonoff induction

**Levin, L.A. (1973). "Universal Sequential Search Problems." *Problems of Information
Transmission* 9(3), 115–116.** The origin of Universal/Levin Search: interleave
execution of all candidate programs weighted by 2^(−length), so a program of length
l(p) solving a problem in time t is found within roughly 2^(l(p)+1)·t steps. Origin of
Kt ("Levin") complexity — time-bounded Kolmogorov complexity, combining description
length and log(runtime) into one cost.

**Solomonoff, R.J. (1964). "A Formal Theory of Inductive Inference, Part I / Part II."
*Information and Control* 7(1):1–22 and 7(2):224–254.** Foundation of algorithmic
probability: the best predictive model is weighted toward the shortest program
generating the observed data. The universal prior is **provably incomputable**
(requires summing over all programs, which is undecidable per the halting problem) —
standard, well-established, though this survey did not locate one single "the
incomputability proof" citation distinct from the halting-problem argument itself;
treat as field-standard folklore rather than one paper's result.

**Hutter, M. (2002). "The Fastest and Shortest Algorithm for All Well-Defined
Problems." *International Journal of Foundations of Computer Science* 13(3), 431–443,
arXiv:cs/0206022.** "Hutter search" — provably within a factor of 5 (plus an
astronomically large, problem-independent additive constant) of the fastest algorithm
for any well-defined problem, via parallel proof-search over program-correctness
proofs. This is the canonical modern source of the honest caveat the creator's own
brief anticipated: Levin/Hutter search is **asymptotically/multiplicatively optimal but
the constants make it a "galactic algorithm"** — useless for any real-world time
budget. This caveat is not a footnote; it is the central practical limitation of the
entire AIT framework as a difficulty predictor.

**Orseau, L., Lelis, L., Lattimore, T., Weber, T. (2018). "Single-Agent Policy Tree
Search With Guarantees." NeurIPS 2018, arXiv:1811.10928.** [Verified via NeurIPS
proceedings + arXiv.] **Levin Tree Search (LevinTS)**: a modern, practically-run
realization of Levin's idea where the uniform/universal prior over programs is replaced
by a *learned* neural-network policy (trained via A3C), giving a search-node bound as a
function of policy quality. Validated on 1,000 generated Sokoban levels; competitive
with a domain-independent heuristic planner. This is the clearest evidence found that
the galactic-algorithm gap can be *narrowed in practice* — not by shrinking the
theoretical constant, but by swapping the universal prior for a problem-family-tuned
learned one. That is itself the key finding: **a usable Levin-style bound requires
already having learned a prior over a *related family* of instances** — it is not a
priors-from-nothing predictor for a genuinely novel problem.

**Li, M. (2026). "From Levin's Universal Search to Policy-Guided Tree Search."
*Entropy* 28(4), Article 434.** DOI: 10.3390/e28040434; indexed on PubMed
(42072559). **[Unverified beyond search-result summary — a direct fetch was blocked by
a 403.]** Reported as a 2026 survey/position piece tracing Levin's 1973 work through
Solomonoff induction to modern policy-guided tree search (LevinTS and successors).
Cited here as evidence the Levin-search line is an active thread as of 2026, not a dead
theoretical curiosity — but flagged because its content was not independently read.

**Hernández-Orallo, J. (2015). "Stochastic Tasks: Difficulty and Levin Search." In
*Artificial General Intelligence — 8th International Conference, AGI 2015*, Berlin,
Springer LNAI, pp. 90–100.** **[Bibliographically confirmed via Springer/ResearchGate;
content unverified beyond the search-result summary — full text was paywalled.]**
Reportedly defines task difficulty *as* the (log of the) number of steps a
Levin-Search-style universal procedure needs to find an acceptable policy for a
stochastic task — the single most directly on-point *definitional* match to the
creator's question found anywhere in this survey. Flagged prominently precisely because
it is so directly on-point and so thinly evidenced here: one AGI-workshop-tier paper,
content not independently confirmed. A reader who wants to build on this survey should
read this paper directly before leaning on it.

**Grau-Moya, J., Genewein, T., Hutter, M., Orseau, L., Delétang, G., Catt, E., Ruoss,
A., Wenliang, L.K., Mattern, C., Aitchison, M., Veness, J. (2024). "Learning Universal
Predictors." arXiv:2401.14953.** [Verified via direct arXiv fetch.] Meta-trains neural
sequence models (LSTMs, Transformers) on data generated by running random programs on
Universal Turing Machines, to amortize Solomonoff induction into a neural predictor.
Demonstrates feasibility and transfer empirically; **explicitly does not derive a new
formal scaling law** relating problem complexity to required model/data size — this is
architectural/empirical progress on tractability, not a new theorem.

**Thread verdict.** The core theoretical results (Levin-search asymptotic optimality;
Solomonoff incomputability) are solid and unchanged since the 1960s–80s. What's
genuinely new since 2018 is narrowing the galactic-algorithm gap by **learning a
problem-tuned prior within a task family** (LevinTS and its descendants) and by
**amortizing Solomonoff induction via meta-learned neural predictors** (2024) — both
real, both empirical/architectural, neither delivering a domain-general a priori
difficulty law. Hernández-Orallo (2015) is the one paper found that explicitly frames
"difficulty" as a Levin-search quantity; it deserves direct follow-up reading given how
squarely it targets the creator's question, but this survey could not deep-verify its
content.

---

## 3. Legg & Hutter's Universal Intelligence, and formal intelligence measures

**Legg, S., Hutter, M. (2007). "Universal Intelligence: A Definition of Machine
Intelligence." *Minds and Machines* 17(4), 391–444.** DOI: 10.1007/s11023-007-9079-x;
also arXiv:0712.3329. [Verified via Springer + arXiv.] Defines
Υ(π) = Σ_μ 2^(−K(μ)) V_μ^π — expected performance of agent π, summed over all computable
environments μ, weighted by their Solomonoff-prior-derived algorithmic simplicity
2^(−K(μ)). This is exactly the Solomonoff-prior-weighted formalization the creator's
question gestures at. It is, however, **provably incomputable** (K(μ) is not
computable) — a normative/definitional formalization of what intelligence would mean
if it could be computed, never a working predictive tool as it stands.

**Wang, X., Jiang, L., Hernández-Orallo, J., Stillwell, D., Sun, L., Luo, F., Xie, X.
(2023–2024). "Evaluating General-Purpose AI with Psychometrics." arXiv:2310.16379;
also *Communications of the ACM*, DOI 10.1145/3769688.** The single most important
honest field-internal admission found in this whole survey, from researchers working
directly in the Legg-Hutter tradition: current (task-benchmark-based) AI evaluation
methodology **"lacks a scientific foundation for predicting \[AI systems'] performance
on unforeseen tasks."** They propose moving from task-oriented to construct-oriented
(psychometric) evaluation as a remedy — a promising direction, explicitly **not** a
solved problem, and stated as such by people with every incentive to claim otherwise if
they could.

**Oswald, J.T., Ferguson, T.M., Bringsjord, S. (2025). "On the Arrowian Impossibility
of Machine Intelligence Measures." AGI 2025 (18th Intl. Conf. on Artificial General
Intelligence, Reykjavik), Springer LNCS vol. 16058, DOI:
10.1007/978-3-032-00800-8_3.** [Verified via Springer + independent search
corroboration of the abstract.] A 2025 formal *negative* result, structurally parallel
to Wolpert & Macready (§1): proves that **no** agent-environment-based machine
intelligence measure (MIM) can simultaneously satisfy Arrow's-Impossibility-Theorem-style
fairness axioms (Pareto efficiency, independence of irrelevant alternatives,
non-oligarchy) — and this explicitly includes **both** Legg-Hutter Intelligence and
Chollet's ARC-style intelligence measure (§4). This is the second independent
impossibility-shaped wall this survey found. Read together with NFL, the pattern is
consistent: every time a fully general, axiomatically well-behaved cross-environment
difficulty/intelligence measure is checked for existence, the answer is *no*.

**Fuller, K.J., Sawyer, D.R., Oswald, J.T., Ferguson, T.M. (2025). "Resource-Relativized
Legg-Hutter Intelligence." AGI 2025, Springer, DOI: 10.1007/978-3-032-00686-8_15.**
**[Bibliographic details confirmed via search; content per search summary only.]**
Reportedly proposes a resource-bounded version of Legg-Hutter intelligence that credits
agents for gains achievable via extra compute — an attempt to make the framework more
realistic, still theoretical.

**Oswald, J.T., Ferguson, T.M., Bringsjord, S. (2024). "A Universal Intelligence
Measure for Arithmetical Uncomputable Environments." AGI 2024, Springer, DOI:
10.1007/978-3-031-65572-2_15.** **[Bibliographic details confirmed; content per search
summary only.]** Extends Legg-Hutter intelligence to environments *higher* on the
arithmetical hierarchy than merely computable ones — a pure theoretical extension
moving further from, not toward, computability.

**Thread verdict.** Legg & Hutter (2007) is exactly what the creator described — and
exactly as incomputable as one would expect from a Solomonoff-prior construction. The
2020–2026 literature response is consistent and, again, an honest field-internal
signal: nobody has turned it into a practical predictor; instead the field has borrowed
its *evaluation criteria* rather than its measure, explicitly stated no predictive
foundation for unforeseen-task performance currently exists (Wang et al. 2023/CACM),
and produced a formal impossibility theorem (Oswald/Ferguson/Bringsjord 2025) that a
fully general, fair, cross-environment version cannot exist at all.

---

## 4. SAT/CSP instance-hardness prediction — the closest existing empirical machinery

**Foundational (phase transition), briefly.** Cheeseman, Kanefsky & Taylor, "Where the
Really Hard Problems Are," IJCAI-91, pp. 331–340 — established that NP-complete problem
families have an order parameter (e.g. clause/variable ratio) whose critical value
marks a phase transition where hardness concentrates. Mitchell, Selman & Levesque,
"Hard and Easy Distributions of SAT Problems," AAAI-92, pp. 459–465 — confirms this at
a *distributional*, not per-instance, level. Crawford & Auton, "Experimental results on
the crossover point in random 3-SAT," *Artificial Intelligence* 81(1–2), 31–57 (1996) —
refines the ≈4.27 clause/variable crossover for random 3-SAT. These establish *where*
hardness concentrates for a specific, randomly-generated problem family; they do not
give a per-instance confidence interval and do not generalize past that family's
generative model.

**The empirical hardness models (EHM) program — the closest analogue anywhere in this
survey to "priors → confidence interval":**

- Leyton-Brown, K., Nudelman, E., Shoham, Y. (2002). "Learning the Empirical Hardness
  of Optimization Problems: The Case of Combinatorial Auctions." CP 2002. Founding
  paper: regress runtime on cheaply-computable instance features.
- Xu, L., Hutter, F., Hoos, H.H., Leyton-Brown, K. (2008). "SATzilla: Portfolio-based
  Algorithm Selection for SAT." *JAIR* 32, 565–606 (arXiv:1111.2249). [Verified via
  direct arXiv fetch.] Builds a per-instance solver portfolio driven by EHMs predicting
  runtime/score per candidate solver; SATzilla07 won 3 gold/1 silver/1 bronze at SAT
  Competition 2007 — a genuine, competition-validated demonstration that instance
  features plus ML give a real predictor. It predicts *relative solver performance*
  across a fixed portfolio, not an absolute, theoretically-derived difficulty interval.
- Hutter, F., Xu, L., Hoos, H.H., Leyton-Brown, K. (2014). "Algorithm Runtime
  Prediction: Methods & Evaluation." *Artificial Intelligence* 206, 79–111. The named
  capstone of the "empirical hardness models" research program, surveying/extending EHM
  techniques (ridge regression, random forests, Gaussian processes) across SAT, MIP,
  and TSP — the most authoritative pre-deep-learning reference for
  runtime/difficulty prediction from instance features.
- Xu, L., Hoos, H.H., Leyton-Brown, K. (2007). "Hierarchical Hardness Models for SAT."
  CP 2007. Mixture-of-experts hardness models (classify SAT/UNSAT first, then condition
  the runtime regressor) beat unconditional models. **A frequently-repeated "~86%
  accuracy at the phase transition" figure could not be verified against the primary
  source and is deliberately omitted here rather than reported as fact** — flagged so
  a future reader does not accidentally re-introduce it as verified.

**Current (2024) ML/GNN-based successor:** Zhang, Z., Chetelat, D., Cotnareanu, J.,
Ghose, A., Xiao, W., Zhen, H.-L., Zhang, Y., Hao, J., Coates, M., Yuan, M. (2024).
"GraSS: Combining Graph Neural Networks with Expert Knowledge for SAT Solver
Selection." KDD 2024, DOI: 10.1145/3637528.3671627, arXiv:2405.11024. [Verified via
ACM DL + arXiv.] Represents CNF instances as tripartite literal-clause graphs with a
heterogeneous GNN plus a runtime-sensitive loss, reported to outperform SATzilla and
SUNNY on an industrial circuit-design benchmark and SAT Competition 2022's Anniversary
Track. Current state of the art in the SATzilla lineage — the field is still active and
improving as of 2024, not stagnant, but every method in this lineage (SATzilla through
GraSS) depends on hand- or graph-derived features **specific to CNF/SAT structure**.

**Cross-domain generalization — not found.** No confirmed transplant of SAT/CSP
hardness-prediction machinery to general reasoning, program synthesis, or theorem
proving as a difficulty predictor was located. The nearest architectural cousin —
Zhao, B., Kapusuzoglu, B., Balasubramaniam, K., Sahu, S., Chakraborty, S., Winata, G.I.
"Optimizing Reasoning Efficiency through Prompt Difficulty Prediction." NeurIPS 2025
Workshop on Efficient Reasoning, arXiv:2511.03808 — trains lightweight predictors of
per-prompt LLM difficulty/correctness to route reasoning problems to the smallest
sufficient model. Structurally the *same idea* (predict per-instance difficulty,
route/select accordingly) applied outside SAT, but it does not cite or build on the
SAT-hardness/EHM literature — an apparent independent reinvention rather than a
demonstrated generalization of that machinery. This absence of citation linkage is
itself informative: three decades of SAT-hardness-prediction work has not propagated
as a recognized toolkit into general-reasoning-difficulty prediction.

**SAT competitions and hardness prediction as a formal track:** competitions use
hardness-informed scoring to curate benchmark instances and schedule parallel/portfolio
tracks, but **no dedicated, standalone "hardness-prediction" competition track**
(distinct from portfolio/solver competitions) was found.

**Thread verdict.** This is the most empirically mature and best-validated body of
work in the entire survey — real accuracy numbers exist (SATzilla's competition
medals; GraSS's reported gains over SATzilla), the research program has a name
(empirical hardness models) and three decades of continuous development through 2024.
But it is **domain-specific feature engineering throughout**, with no evidenced
transfer outside SAT/CSP/combinatorial-optimization territory.

---

## 5. Algorithm selection and meta-learning — the most mature general framing, and its rigorous edge

**Rice, J.R. (1976). "The Algorithm Selection Problem." *Advances in Computers* 15,
65–118.** The foundational framing underlying nearly everything in §4 and §5: given
instance features, predict which algorithm from a portfolio performs best. Direct
ancestor of SATzilla and everything downstream of it.

**Kerschke, P., Hoos, H.H., Neumann, F., Trautmann, H. (2019). "Automated Algorithm
Selection: Survey and Perspectives." *Evolutionary Computation* 27(1), 3–45,
arXiv:1811.11597.** [Verified via arXiv + MIT Press journal record.] The standard
modern survey; frames "predicting performance/difficulty from features" as the field's
core mechanism across SAT, planning, and black-box optimization.

**Smith-Miles, K., Muñoz, M.A. (2023). "Instance Space Analysis for Algorithm Testing:
Methodology and Software Tools." *ACM Computing Surveys* 55(12), Article 255.** The
most directly on-point Thread-5 finding: Instance Space Analysis (ISA) projects
instance-feature space into two dimensions where algorithm "footprints" (regions of
good/poor performance) are visualized and measured — the closest existing methodology
to "given known structural priors, state a region/confidence footprint for how
hard/solvable an instance is." Genuinely domain-agnostic *as a methodology*: applied to
TSP, black-box continuous optimization, vehicle routing, timetabling, scheduling, and
even quantum optimization (QAOA). It still requires a hand-built, domain-specific
feature set per application — it generalizes the *method*, not the *features*.
Toolkit: MATILDA / InstanceSpace (open source).

**The rigorous edge — PAC-style sample-complexity bounds for algorithm selection
itself:**

- Gupta, R., Roughgarden, T. (2016/2017). "A PAC Approach to Application-Specific
  Algorithm Selection." ITCS 2016; *SIAM J. Computing* 46(3), 992–1017 (2017),
  arXiv:1511.07147. [Verified via direct arXiv fetch.] Adapts PAC-learning theory
  (VC-dimension-style complexity measures) to algorithm selection: how much *data* is
  needed before an empirically-selected algorithm/parameter is guaranteed, with stated
  confidence, to generalize. This is the single most rigorous result in the whole
  algorithm-selection thread — but it bounds the *sample complexity of the selection
  process*, not a direct per-instance difficulty interval for a specific new problem.
- Balcan, M.-F. (2020). "Data-Driven Algorithm Design." *Communications of the ACM*
  63(6), 67–73 (longer version in *Beyond Worst-Case Analysis*, CUP). Generalizes
  Gupta-Roughgarden to a broad theory of learning algorithm configurations (clustering,
  greedy algorithms, mechanism design, cut selection) with formal generalization
  guarantees.
- Balcan, M.-F. et al. "How Much Data Is Sufficient to Learn High-Performing
  Algorithms? Generalization Guarantees for Data-Driven Algorithm Design." STOC 2021.
  A literal confidence/sample-size result — for training-data sufficiency of a learned
  *selection rule*, not for the difficulty of an individual instance.

**Recent surveys (2024–2025), bibliographically confirmed, content not deep-verified:**
"An experimental survey and Perspective View on Meta-Learning for Automated Algorithms
Selection and Parametrization," arXiv:2504.06207 (2025); "A Survey of Meta-features
Used for Automated Selection of Algorithms for Black-box Single-objective Continuous
Optimization," arXiv:2406.06629 (2024) — both confirm the field is still actively
consolidating as of 2024–2025, still mostly within combinatorial/continuous
optimization.

**Cross-domain generalization.** Confirmed extensions beyond SAT/CSP: AutoML /
hyperparameter selection (a mature adjacent application — see Hutter, Kotthoff,
Vanschoren, eds., *Automated Machine Learning: Methods, Systems, Challenges*, Springer
2019), recommender systems, vehicle routing/scheduling. **No confirmed application to
general program synthesis, formal reasoning, or theorem-proving as a difficulty
predictor** — the same absence found in §4.

**Thread verdict.** This is the most mature *general* machinery in the survey — a
named 50-year-old problem framing, active current surveys, a genuine domain-agnostic
methodology (ISA), and a real rigorous edge (PAC-style sample-complexity bounds for the
selection process). It is also the clearest illustration of the gap between "mature
empirical toolkit" and "the creator's actual ask": ISA gives a footprint of *where a
known algorithm portfolio does well*, not a difficulty interval for a genuinely novel
problem with no algorithm portfolio yet built for it; the PAC results bound the
*learning process's* reliability, not the target instance's difficulty.

---

## 6. Chollet's "On the Measure of Intelligence" and ARC-AGI difficulty grading (2024–2026)

**Chollet, F. (2019). "On the Measure of Intelligence." arXiv:1911.01547.** [Verified:
exact arXiv ID confirmed.] Core claim, stated in the paper's own words: *"The
intelligence of a system is a measure of its skill-acquisition efficiency over a scope
of tasks, with respect to priors, experience, and generalization difficulty."* Skill at
a task is explicitly rejected as an intelligence measure, because unlimited priors or
training experience let an experimenter "buy" arbitrary skill, masking real
generalization power. The framing draws on algorithmic information theory and
distinguishes generalization by "distance" from the training distribution (local/broad/
extreme). **This is a definitional/conceptual framework, not a predictive-difficulty
procedure** — it does not give a computable difficulty score for an unseen task from
task structure alone. (This paper's precise formal equation, per the source agent, did
not survive the web-rendered text extraction cleanly; the prose claim above is
confirmed, the exact typeset equation is not independently re-derived here.) ARC (the
benchmark) is proposed in this same paper to operationalize the definition.

**Chollet, F., Knoop, M., Kamradt, G., Landers, B., Pinkard, H. (2025). "ARC-AGI-2: A
New Challenge for Frontier AI Reasoning Systems." arXiv:2505.11831.** [Verified via
direct arXiv fetch.] ARC-AGI-2's difficulty calibration is **empirical and
after-the-fact, not structural/a-priori**: a live human study (400+ participants, three
sessions, Nov 2024–May 2025) required every task to be solved by ≥2 humans in ≤2
attempts before inclusion, and eval splits were curated to match human-solvability and
perceived-difficulty distributions. This is difficulty *calibration via testing*, not
difficulty *prediction from structure*.

**"ARC Prize 2025: Technical Report," arXiv:2601.10904.** Reports the 2025 Kaggle
competition (1,455 teams; top private-eval score 24.03% on ARC-AGI-2, won by NVARC via
test-time training + synthetic data); identifies the "refinement loop" (iterative
per-task program optimization with feedback) as the year's defining technique. No
difficulty-*prediction* methodology — purely solve-rate-as-outcome reporting, matching
the pattern this survey's brief anticipated as likely.

**"ARC-AGI-3: A New Challenge for Frontier Agentic Intelligence," ARC Prize Foundation,
arXiv:2603.24621.** Extends the paradigm to interactive/agentic environments; again
calibrated via human baselines (reported ~100% human solve rate vs. <1% for frontier AI
as of March 2026), not a priori structural scoring.

**Pendharkar, A. (2026). "Structural Grid Descriptors Predict Within-Task Solver
Success on ARC-AGI." arXiv:2606.09026.** [Verified via arXiv abstract + search
corroboration of methodology.] The one genuine difficulty/success-prediction paper
found in the ARC literature — but it answers a different question than the creator's:
hand-crafted grid-structure descriptors (dominated by a single grid-complexity axis,
`n_components_final`) measured **at 50% trajectory completion during solving** predict
which in-progress solver attempts on a *given* task will succeed (mean within-task
best-feature AUC 0.885 across 44,800 runs, two solver architectures, 400 tasks; feature
frozen on one solver architecture transfers to the other at AUC 0.747–0.762). This is
mid-solve, conditioned on the task, not a-priori/pre-solve prediction of how hard an
unseen task will be — genuinely useful (reported 33.6% compute savings via early
stopping) but a distinct problem from the one the creator is asking about.

**Krsteski, S., Meyer, C. (2026). "Predicting Task Difficulty Without Rollouts."
arXiv:2608.05797.** [Verified via direct arXiv fetch.] The clearest genuine ex-ante
(before any solve attempt) difficulty predictor found anywhere in this survey: forecasts
agent success likelihood directly from a task *description*, before running any costly
rollout, across 17 agentic benchmarks (coding, math, ML, web navigation, function
calling). Uses token-level entropy of the task description as the predictive signal,
with residual analysis used to expose benchmark contamination/infeasibility flaws. This
is real, current (Aug 2026, essentially brand-new at time of writing), and squarely
"ex-ante difficulty prediction" — but it is general-agentic-benchmark work, not
ARC/program-synthesis-specific, and its signal (NLP entropy of a description) is a
*proxy*, not derived from any problem-space/program-space-size relationship. It has not
had time to be peer-reviewed or replicated as of this survey.

**Adjacent comparator:** "4OPS: Structural Difficulty Modeling in Integer Arithmetic
Puzzles," arXiv:2603.25356 — reportedly shows solver-independent surface features fail
to predict difficulty, but features derived from *minimal-solution witnesses* (i.e.
requiring the problem to already be solved once, by an exact solver) predict difficulty
near-perfectly. This is an important negative/positive pairing: it suggests, at least
in this domain, that genuinely a-priori (pre-solve) structural difficulty prediction is
hard precisely *because* the useful signal lives in the solution, not the problem
statement — which is a substantive, if narrow, piece of evidence against the creator's
hoped-for general rate existing in an easily-extractable form.

**Thread verdict.** This is the thread the survey's brief correctly anticipated might
be thin, and it is: the ARC-AGI community's difficulty handling is almost entirely
**empirical calibration via large-scale human testing**, not prediction from structure.
The one true ARC-specific "predict success" paper operates mid-solve. The nearest true
ex-ante predictor (Krsteski & Meyer, Aug 2026) is real, current, and directly on-point
in *spirit*, but general-purpose, proxy-based, and not yet establishing anything like a
program-space-size-derived law. **No paper was found, anywhere, that scores ARC or
general program-synthesis task difficulty in advance from a problem-space/program-space
size relationship.** If it existed as an established result, the breadth of search
conducted here (ARC Prize's own three technical reports, Chollet's foundational paper,
and multiple explicit "difficulty prediction" search sweeps) would very likely have
surfaced it.

---

## 7. Bayesian program induction and human-level insight via program-space search

**Lake, B.M., Salakhutdinov, R., Tenenbaum, J.B. (2015). "Human-level concept learning
through probabilistic program induction." *Science* 350(6266), 1332–1338.** DOI:
10.1126/science.aab3050. [Verified via Science DOI.] Introduces Bayesian Program
Learning (BPL): concepts as stochastic motor programs inferred via a Bayesian
criterion, evaluated on Omniglot one-shot classification/generation, matching human
performance and passing visual-Turing-test discrimination. Establishes
program-induction-with-strong-priors as a working, validated model of human one-shot
concept acquisition. Its "difficulty" content is about **sample efficiency** (learning
from one example rather than thousands) — it does not offer a formula for how
search/inference cost grows with task complexity that would ground a general
confidence interval.

**DreamCoder — Ellis, K., Wong, C., Nye, M., Sablé-Meyer, M., Cary, L., Morales, L.,
Hewitt, L., Solar-Lezama, A., Tenenbaum, J.B. (2021). "DreamCoder: Bootstrapping
Inductive Program Synthesis with Wake-Sleep Library Learning." PLDI 2021, pp. 835–850,
DOI 10.1145/3453483.3454080** (journal version: *Phil. Trans. Royal Society A*, 2023,
also arXiv:2006.08381). Bootstraps a growing library of reusable abstractions plus a
learned neural search policy via wake-sleep, across 8+ domains. Demonstrates that
library learning **reduces search cost over time** as compositional structure
accumulates — an empirically real and important effect — but does not give a general
quantitative law relating program-space search cost to an a-priori-measurable problem
complexity, transferable to an unseen domain as a difficulty predictor.

**2023–2025 follow-on lineage (LLM-integrated library learning):**
- Bowers, M. et al. "Top-Down Synthesis for Library Learning." PACMPL 2023 (Stitch).
- Grand, G., Wong, L., Bowers, M., Olausson, T.X., Liu, M., Tenenbaum, J.B., Andreas,
  J. "LILO: Learning Interpretable Libraries by Compressing and Documenting Code." ICLR
  2024, arXiv:2310.19791. Combines DreamCoder-style wake-sleep library growth with an
  LLM (auto-documentation + code compression via Stitch); Tenenbaum's continued
  involvement directly links this to the founding lineage.
- "AbstractBeam: Enhancing Bottom-Up Program Synthesis Using Library Learning,"
  arXiv:2405.17514 (2024) — DreamCoder-inspired library learning with LambdaBeam
  search.
- Lake, B.M., Baroni, M. (2023). "Human-like systematic generalization through a
  meta-learning neural network." *Nature* 623, 115–121. A related but architecturally
  distinct Lake-lab thread (meta-learning for compositional generalization rather than
  explicit symbolic program induction) — transformer-based systems achieving
  human-like compositional generalization on instruction-following tasks.

None of these 2023–2025 follow-ups was found to make a quantitative claim about how
program-space search cost *scales* with problem complexity in a form usable for an
a-priori confidence interval — they report empirical solve-rate/efficiency gains from
library growth relative to baselines, not a general scaling law.

**Thread verdict.** This lineage is the closest existing body of work to "human-level
insight via program-space search with known priors," and it is genuinely strong on that
exact framing — strong priors (a probabilistic generative model of how motor programs
compose) plus efficient search really do reproduce human one-shot performance on a
matched task. But nothing in the lineage converts this into a general, a-priori,
quantitative difficulty-scaling law. It demonstrates the *mechanism* the creator is
gesturing at (priors shrink effective program-space, search cost drops accordingly) far
more concretely than any other thread in this survey, without ever formalizing it as a
predictive rate.

---

## 8. "Known solvable via existence proof" — does this argument have a name and a literature?

This is the creator's sharpest sub-question, restated: does merely knowing that *some*
bounded-resource system (a human brain, ~20W, finite working memory, one lifetime of
practice) already performs a capability constitute a rigorous upper bound on the
resources needed to engineer that capability elsewhere?

**Yes, it has an informal name and a real literature — but the literature's own best
work exists mainly to show the naive version is a fallacy.**

**Bostrom, N., Shulman, C. (2012). "How Hard Is Artificial Intelligence? Evolutionary
Arguments and Selection Effects." *Journal of Consciousness Studies* 19(7–8),
103–130.** [Peer-reviewed.] The closest thing to a *formalized* version of the
creator's move, applied to evolution rather than the brain's power budget directly.
Structure: (1) evolution produced human intelligence via blind, undirected search; (2)
this seems to show the feat is "non-hard" for a search process with evolution's
resource budget; (3) therefore engineered (directed, presumably more efficient)
intelligence is at most that hard. **Their actual contribution is showing this naive
argument is invalid as stated**, because of an observation-selection effect: any
observer capable of asking the question necessarily finds themselves on a planet where
intelligence *did* evolve, regardless of how astronomically rare that outcome is
elsewhere in the universe — so "it happened here" carries little evidential weight
about difficulty on its own. They then do the harder work of repairing the argument
using anthropic reasoning and convergent-evolution evidence. **This is the single most
important source for the creator to read before leaning on the existence-proof
argument** — it is not a green light, it is a careful demonstration of exactly how the
naive form fails and what a defensible version requires.

**Pagel, A. (2023). "The Limits of the Existence Proof Argument for General
Intelligence." LessWrong, Sept 19, 2023.** [Informal/blog-level, not peer-reviewed.]
The sharpest published statement that the naive move is a non-sequitur: existence of a
capability in one substrate (biological neurons) does not prove a different substrate
(silicon/software) can replicate it — illustrated with a chaotic double pendulum, far
simpler than a brain, that resists faithful digital simulation over time despite being
fully classical and well-understood physics. Names and directly critiques the exact
argument pattern the creator described.

**Cotra, A. (2020). "Forecasting TAI with Biological Anchors." Open Philanthropy draft
report.** [Serious quantitative forecasting effort; internally and externally
red-teamed but never published in an academic venue.] Uses brain size/compute as a
*quantitative anchor* for how large a trained model would need to be, then extrapolates
historical compute-cost trends to estimate *when* training a brain-sized model becomes
affordable (headline: ~10% chance of transformative AI by 2031, ~50% by 2052, per
Holden Karnofsky's public "in a nutshell" summary). Crucially, **it does not itself
argue existence proves tractability** — it's a hardware-cost-trend forecasting tool
built on a compute anchor, one input among several.

**Carlsmith, J. (2020). "How Much Computational Power Does It Take to Match the Human
Brain?" Open Philanthropy report.** [Serious quantitative effort; ~30 experts
consulted, four independent estimation methods; not peer-reviewed.] Concludes it is
more likely than not that ~10^15 FLOP/s is *sufficient* to match brain task-performance
— **"given the right software, which may be very hard to create."** This explicit hedge
is the single most load-bearing caveat for the creator's argument in this whole survey:
Carlsmith's own report treats the brain as a bound on *hardware*, and says nothing
about whether the *algorithm* achieving that capability at that hardware budget is
findable. An existence proof of a capability at a given resource level does not, by
itself, bound the difficulty of *discovering how* to achieve it at that level.

**Criticism of Biological Anchors, verified:** Scott Alexander, "What Happened With Bio
Anchors?", Astral Codex Ten (Substack), Feb 12, 2026 — [informal/blog-level, but
substantive] reports Cotra's headline forecast underestimated real-world compute-growth
rate by roughly 6.7×; also Epoch AI's published retrospectives and critique
(epoch.ai). These are evidence the framework was directionally sound but not tightly
calibrated in practice — a useful, honest data point on how well this class of argument
actually performs when checked against outcomes.

**Sample-efficiency literature (human vs. model), as quantitative grounding:**
Lake, B.M., Ullman, T.D., Tenenbaum, J.B., Gershman, S.J. (2017). "Building Machines
That Learn and Think Like People." *Behavioral and Brain Sciences* 40, e253 (also
arXiv:1604.00289, 2016). [Peer-reviewed, highly cited.] Uses the human sample-efficiency
gap as a **diagnostic of missing ingredients** (compositionality, intuitive physics,
learning-to-learn), not as a direct resource bound on achievability — a more modest and
more defensible use of the human-existence datapoint than the creator's framing.
Also: the BabyLM Challenge line (e.g. "Findings of the BabyLM Challenge: Sample-Efficient
Pretraining on Developmentally Plausible Corpora," arXiv:2504.08165, 2025) quantifies the
actual gap concretely — children see ~10^8 words by age 13 vs. 10^11–10^12 tokens for
GPT-3/Chinchilla-era models, a 4–5 order-of-magnitude difference — real and verified,
but again used as an engineering target, not a philosophical tractability bound. A
pointed informal counter-argument circulating in the same discourse ("Dissolving the
Deep Learning Sample Efficiency Gap") argues much of the apparent gap is an artifact of
comparing a *pretrained* human (carrying priors from evolution plus years of multimodal
experience) against a from-scratch network — direct pushback against reading "human
uses less data" as "therefore an equivalent system needs less."

**Brain-compute estimates as a resource envelope — how crisp is "20 watts"?** AI
Impacts' "Brain performance in FLOPS" compilation (aiimpacts.org) aggregates
independent estimates spanning **up to ~7 orders of magnitude** (Moravec/Drexler's
sub-petaFLOPS "functional" estimates vs. Sandberg & Bostrom's whole-brain-emulation
roadmap range of 10^18–10^25 FLOPS depending on simulation grain). This spread is
itself an important, concrete finding: **"the brain's resource envelope" is not a
crisp, agreed-upon number** even among careful estimators — the wattage figure (~20W)
is real and precise, but the *computational* content of what that wattage buys is
disputed by many orders of magnitude, which weakens any argument that leans on brain
compute as a tight bound.

**Formal (complexity-theoretic) treatment — searched for, not found.** Non-constructive
existence proofs are a well-defined general category in mathematics (proving a solution
exists without exhibiting it), but no formal complexity-theoretic or
computability-theoretic treatment was found of the *specific* cross-substrate move:
"one physical instantiation of a capability under bounded resources R implies an upper
bound of ~R on the resources needed to engineer that capability in a different
substrate." This does not reduce cleanly to a standard complexity-class argument
(it concerns transferring a resource cost across physically different substrates, which
complexity theory as such does not address). The best formalization found (Bostrom &
Shulman 2012) is philosophical/Bayesian (observation-selection theory), not
complexity-theoretic, and its conclusion is that the naive move requires substantial
correction to carry any evidential weight at all.

**Thread verdict.** The creator's framing is a recognized argument pattern with a
genuine, substantial literature behind it — not an invented-on-the-spot heuristic — but
it is weaker and more contested than the creator's phrasing implies. Its most careful
peer-reviewed treatment (Bostrom & Shulman) exists specifically to demonstrate the
naive form is an observation-selection fallacy; its best-known applied version
(Biological Anchors) is explicitly a hardware-cost-trend forecast with an
express "modulo an unknown, possibly very hard to find, algorithm" hedge built in by
its own authors (Carlsmith); and even the brain's resource envelope, precise in watts,
is uncertain by up to seven orders of magnitude in the computational currency that
would actually matter for a tractability argument. **A defensible version of the
argument exists — "a demonstrated existence proof at resource level R rules out the
claim that the capability is impossible at any resource level, and gives a real, if
substrate-uncertain, target to aim compute/engineering effort at" — but the stronger
claim the creator's phrasing suggests ("therefore achievable at low power, full stop")
is exactly the move the field's own most careful authors warn against.**

---

## 9. Synthesis — what's actually established vs. open vs. not a coherent question at this rigor

**Is there a general, cross-domain, quantitative rate/law relating problem-space growth
to required-program-space growth?** No — and this is a proven "no," not merely an
unfilled gap. Two independent formal impossibility results were found, arrived at from
different directions and 28 years apart: Wolpert & Macready's No Free Lunch theorem
(1997, §1) for optimization/learning, and Oswald, Ferguson & Bringsjord's Arrow-style
impossibility theorem for intelligence measures (2025, §3), which explicitly names both
Legg-Hutter Intelligence and Chollet's measure as casualties. Both say the same thing in
different vocabularies: **no fully general, axiomatically well-behaved, cross-domain
difficulty/intelligence law can exist without restricting to a specific, non-uniform
prior over problems.** Any usable "rate" is necessarily a rate *within* a restricted
class or a restricted prior — which is exactly the shape every concrete, rigorous
result in this survey actually takes (VC-dimension bounds within a fixed hypothesis
class; Legg-Hutter's Υ for a fixed environment weighting; PAC-selection bounds for a
fixed algorithm portfolio).

Within that restriction, real quantitative results exist and recur across every thread
around the **same underlying object**: Kolmogorov/Levin complexity and the Solomonoff
prior. Occam learning's compression bound (§1), Levin search's Kt-complexity (§2),
Legg-Hutter's 2^(−K(μ)) weighting (§3) are three entry points into one literature, not
three independent ones. The recurring finding is that **the compressibility of the
specific problem distribution, not problem-space "size" in the abstract, is what
actually governs difficulty** — which is real and load-bearing, but pushes the hard
question down one level: predicting the Kolmogorov/Levin complexity of a *not-yet-solved*
problem is itself uncomputable/intractable in general (Solomonoff's prior is
incomputable; Levin/Hutter search is only optimal up to unusably large constants). "Predict
difficulty from problem-space size" resolves, at the deepest formal level available, to
"you would need to already know something equivalent to the answer" — a structural
circularity, not a research gap more effort straightforwardly closes.

**Is the "known solvable vs. not known solvable" existence-proof distinction a
recognized, useful framing anywhere in the literature, or a folk heuristic?** It is
recognized, and it is contested at exactly the point of rigor the creator wants. Its
peer-reviewed formalization (Bostrom & Shulman 2012, §8) exists specifically to show the
naive form is an observation-selection fallacy and to demonstrate what repair it needs.
Its best applied instantiation (Biological Anchors / Carlsmith's brain-FLOPS report,
§8) is a real, serious, widely-cited quantitative forecasting effort — but its own
authors built in the exact hedge that undercuts using it as a tractability *proof*
("given the right software, which may be very hard to create"), and independent
retrospectives (Scott Alexander 2026; Epoch AI) show it was directionally right but
substantially miscalibrated when checked against real outcomes. **Verdict: this is a
real, load-bearing, defensible-in-a-weaker-form argument — "an existence proof rules
out impossibility and gives a concrete target" — not the strong form the creator's
phrasing suggested ("therefore tractable at that resource level, full stop"), which the
literature's own best authors treat as a known failure mode.**

**What is the most credible path toward the creator's actual goal — a confidence
interval for a new problem's difficulty, given known priors?** Ranked honestly, from
what's actually usable today to what's most theoretically apt but least operational:

1. **SAT/CSP-style empirical hardness models, generalized beyond SAT (§4–§5).** This is
   the only thread in the survey with real, competition-validated accuracy numbers
   (SATzilla's medals; GraSS's 2024 gains) and an explicitly domain-agnostic
   *methodology* already proven across multiple combinatorial domains (Instance Space
   Analysis, §5). The catch: every strong result still depends on hand- or
   graph-engineered features specific to its domain, and no confirmed transplant to
   general reasoning/program synthesis exists yet — the nearest attempt (LLM
   prompt-difficulty routing, §4) reinvented the idea independently rather than
   building on this literature. **This is the most promising near-term engineering
   path**, precisely because it does not require solving the deeper impossibility
   results first — it only needs a feature set for the target domain.
2. **ARC-AGI-style empirical difficulty scoring via human-solve-rate or model-solve-rate
   as a proxy (§6).** Mature as a *calibration* tool (this is literally how ARC-AGI-2's
   difficulty spectrum was built) but not, currently, a prediction tool usable before
   any solve attempts exist — the one genuine ex-ante predictor found in this space
   (Krsteski & Meyer, Aug 2026, §6) is brand new, general-purpose, and uses an NLP-entropy
   proxy rather than anything derived from problem-space/program-space structure.
3. **PAC-learning-style sample-complexity bounds, if the target problem can be cast
   into a genuinely fixed hypothesis class (§1, §5).** Real, rigorous, and gives an
   actual confidence interval in the formal statistical sense — but only inside a
   pre-specified hypothesis class, which means casting a *novel* problem into such a
   class is itself the hard, unsolved part of the exercise.
4. **Bayesian program induction / DreamCoder-lineage priors (§7)** as the best
   *mechanistic* account available of why strong priors shrink effective program-space
   and cut search cost — genuinely the closest existing thing to "human-level insight
   via program-space search with known priors" as a working, validated system — but it
   has never been converted into a general predictive scaling law, only demonstrated as
   an empirical effect within specific domains (Omniglot, DreamCoder's 8 program-synthesis
   domains).
5. **Levin/Solomonoff-style a-priori complexity (§2, §3)** is the deepest and most
   theoretically satisfying grounding for *why* difficulty should be predictable from
   priors at all — and it is exactly this framework that the "compressibility governs
   difficulty" finding above traces back to — but it is the least operational: usable
   constants require having already learned a prior over a related task family
   (LevinTS, §2), and the base quantities (K, Kt) are uncomputable/intractable in
   general.

**What could not be found, stated plainly rather than papered over:** no paper anywhere
in this survey formalizes "problem-space grows at rate Z ⟹ program-space grows at a
knowable supralinear rate" as a cross-domain law — the two proven impossibility results
(§1, §3) suggest strongly that no such law can exist in fully general form, only within
a restricted prior. No paper was found giving an a-priori (pre-solve), structural,
program-space-size-derived difficulty score for ARC-AGI or general program synthesis —
the ARC community's difficulty machinery is entirely empirical/human-calibration-based,
and the one true ex-ante predictor found anywhere near this space (§6) uses a natural-
language proxy, not a program-space-theoretic quantity. No formal (as opposed to
philosophical/anthropic) treatment of the existence-proof-as-tractability-bound argument
was found (§8). Several individually-flagged citations (Hernández-Orallo 2015 on
Levin-search-as-difficulty, §2; the Li 2026 Entropy survey, §2; two additional Oswald/
Ferguson/Bringsjord AGI papers, §3) were bibliographically confirmed but their content
was not independently deep-verified beyond search summaries or abstracts — a future
reader building further on this survey should read those primary sources directly
before relying on the specific claims attributed to them here.

---

## Bibliography (alphabetical by first author)

- Blumer, Ehrenfeucht, Haussler, Warmuth (1987). "Occam's Razor." *IPL* 24(6), 377–380.
- Blumer, Ehrenfeucht, Haussler, Warmuth (1989). "Learnability and the VC Dimension."
  *JACM* 36(4), 929–965.
- Boopathy, Liu, Hwang, Ge, Mohammedsaleh, Fiete (2023). "Model-agnostic Measure of
  Generalization Difficulty." ICML 2023, arXiv:2305.01034.
- Bostrom, Shulman (2012). "How Hard Is Artificial Intelligence? Evolutionary Arguments
  and Selection Effects." *J. Consciousness Studies* 19(7–8), 103–130.
- Carlsmith (2020). "How Much Computational Power Does It Take to Match the Human
  Brain?" Open Philanthropy.
- Cheeseman, Kanefsky, Taylor (1991). "Where the Really Hard Problems Are." IJCAI-91.
- Chollet (2019). "On the Measure of Intelligence." arXiv:1911.01547.
- Chollet, Knoop, Kamradt, Landers, Pinkard (2025). "ARC-AGI-2." arXiv:2505.11831.
- ARC Prize Foundation (2026). "ARC Prize 2025: Technical Report." arXiv:2601.10904.
- ARC Prize Foundation (2026). "ARC-AGI-3." arXiv:2603.24621.
- Cotra (2020). "Forecasting TAI with Biological Anchors." Open Philanthropy.
- Crawford, Auton (1996). "Experimental results on the crossover point in random
  3-SAT." *Artificial Intelligence* 81(1–2), 31–57.
- Ellis, Wong, Nye, Sablé-Meyer, Cary, Morales, Hewitt, Solar-Lezama, Tenenbaum (2021).
  "DreamCoder." PLDI 2021; journal version *Phil. Trans. R. Soc. A* (2023).
- Fuller, Sawyer, Oswald, Ferguson (2025). "Resource-Relativized Legg-Hutter
  Intelligence." AGI 2025.
- Goldblum, Finzi, Rowan, Wilson (2024). "The No Free Lunch Theorem, Kolmogorov
  Complexity, and the Role of Inductive Biases in ML." ICML 2024, arXiv:2304.05366.
- Grand, Wong, Bowers, Olausson, Liu, Tenenbaum, Andreas (2024). "LILO." ICLR 2024,
  arXiv:2310.19791.
- Grau-Moya, Genewein, Hutter, Orseau, Delétang, Catt, Ruoss, Wenliang, Mattern,
  Aitchison, Veness (2024). "Learning Universal Predictors." arXiv:2401.14953.
- Gupta, Roughgarden (2016/2017). "A PAC Approach to Application-Specific Algorithm
  Selection." ITCS 2016 / *SIAM J. Computing* 46(3), arXiv:1511.07147.
- Hernández-Orallo (2015). "Stochastic Tasks: Difficulty and Levin Search." AGI 2015,
  Springer LNAI, pp. 90–100. [content unverified beyond abstract]
- Hutter (2002). "The Fastest and Shortest Algorithm for All Well-Defined Problems."
  *IJFCS* 13(3), 431–443, arXiv:cs/0206022.
- Hutter, Xu, Hoos, Leyton-Brown (2014). "Algorithm Runtime Prediction: Methods &
  Evaluation." *Artificial Intelligence* 206, 79–111.
- Kerschke, Hoos, Neumann, Trautmann (2019). "Automated Algorithm Selection: Survey and
  Perspectives." *Evolutionary Computation* 27(1), 3–45, arXiv:1811.11597.
- Krsteski, Meyer (2026). "Predicting Task Difficulty Without Rollouts."
  arXiv:2608.05797.
- Lake, Salakhutdinov, Tenenbaum (2015). "Human-level concept learning through
  probabilistic program induction." *Science* 350(6266), 1332–1338.
- Lake, Ullman, Tenenbaum, Gershman (2017). "Building Machines That Learn and Think
  Like People." *BBS* 40, e253, arXiv:1604.00289.
- Lake, Baroni (2023). "Human-like systematic generalization through a meta-learning
  neural network." *Nature* 623, 115–121.
- Legg, Hutter (2007). "Universal Intelligence: A Definition of Machine Intelligence."
  *Minds and Machines* 17(4), 391–444, arXiv:0712.3329.
- Leyton-Brown, Nudelman, Shoham (2002). "Learning the Empirical Hardness of
  Optimization Problems." CP 2002.
- Levin (1973). "Universal Sequential Search Problems." *Problems of Information
  Transmission* 9(3), 115–116.
- Li (2026). "From Levin's Universal Search to Policy-Guided Tree Search." *Entropy*
  28(4), Article 434. [content unverified beyond abstract]
- Mitchell, Selman, Levesque (1992). "Hard and Easy Distributions of SAT Problems."
  AAAI-92, 459–465.
- Orseau, Lelis, Lattimore, Weber (2018). "Single-Agent Policy Tree Search With
  Guarantees." NeurIPS 2018, arXiv:1811.10928.
- Oswald, Ferguson, Bringsjord (2024). "A Universal Intelligence Measure for
  Arithmetical Uncomputable Environments." AGI 2024.
- Oswald, Ferguson, Bringsjord (2025). "On the Arrowian Impossibility of Machine
  Intelligence Measures." AGI 2025, Springer LNCS 16058.
- Pagel (2023). "The Limits of the Existence Proof Argument for General Intelligence."
  LessWrong.
- Pendharkar (2026). "Structural Grid Descriptors Predict Within-Task Solver Success on
  ARC-AGI." arXiv:2606.09026.
- Rice (1976). "The Algorithm Selection Problem." *Advances in Computers* 15, 65–118.
- Smith-Miles, Muñoz (2023). "Instance Space Analysis for Algorithm Testing." *ACM
  Computing Surveys* 55(12), Article 255.
- Solomonoff (1964). "A Formal Theory of Inductive Inference." *Information and
  Control* 7(1):1–22, 7(2):224–254.
- Wang, Jiang, Hernández-Orallo, Stillwell, Sun, Luo, Xie (2023/2024). "Evaluating
  General-Purpose AI with Psychometrics." arXiv:2310.16379; *CACM*.
- Wolpert, Macready (1997). "No Free Lunch Theorems for Optimization." *IEEE Trans.
  Evolutionary Computation* 1(1), 67–82.
- Xu, Hoos, Leyton-Brown (2007). "Hierarchical Hardness Models for SAT." CP 2007.
- Xu, Hutter, Hoos, Leyton-Brown (2008). "SATzilla." *JAIR* 32, 565–606,
  arXiv:1111.2249.
- Zhang, Chetelat, Cotnareanu, Ghose, Xiao, Zhen, Zhang, Hao, Coates, Yuan (2024).
  "GraSS." KDD 2024, arXiv:2405.11024.
- Zhao, Kapusuzoglu, Balasubramaniam, Sahu, Chakraborty, Winata (2025). "Optimizing
  Reasoning Efficiency through Prompt Difficulty Prediction." NeurIPS 2025 Workshop,
  arXiv:2511.03808.
