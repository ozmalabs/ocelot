# Academic Peer Review: `02c_seldon_manifolds_decision_making.tex`
**Document:** `02c_seldon_manifolds_decision_making.tex`  
**Title:** Seldon Manifolds --- Decision Making: Narrative Continuation, Target Shapes, Surprise, and Meta-analysis  
**Draft / Revision:** `draft-2026-09-06.1` · document revision `r1`  
**Author:** Matthew Parslow (Independent Researcher)  
**Corpus Role:** Formal Decision Grammar & Policy Selection over Seldon Manifolds  
**Dependencies:** Connects with `02` (`[SM-]`), `01` (`[GE-]`), `03` (`[NM-]`), `04` (`[NV-]`).

---

## 1. Executive Summary

`02c_seldon_manifolds_decision_making.tex` supplies the missing action-selection engine for the Seldon Manifold framework. While Paper `02` constructs the geometric landscape of reachable futures ($\mathcal{S}_{h,\rho}$), it deliberately refrains from specifying how an embedded agent selects an action among reachable branches. Paper 02c resolves this by formalizing an **agent-neutral decision grammar**.

The paper’s core insight is economic and bounded: decision-making is not continuous, exhaustive expected-utility maximization. Instead:
1. **The Default is Free Continuation:** The standing Narrative $\mathcal{N}$ represents the default continuation requiring **zero additional decision inference**. An agent continues executing its standing policy without cognitive cost.
2. **Reopening Conditions:** A decision is reopened only under two specific triggers:
   - *Represented Surprise:* An environmental observation that falls outside the frame’s acceptable target region.
   - *Costly Meta-Analysis:* A deliberate, resource-intensive evaluation triggered when Narrativium capacity falls below a stability threshold.
3. **Target Shapes vs. Point Targets:** Goals are formalized as multi-dimensional *acceptable shapes* (regions of viable state space) rather than scalar optimization points with error bars.

---

## 2. Formal Decision Grammar & Analysis

### 2.1 The Invariance of Standing Narrative
- The paper solves the computational cost of continuous decision-making in real-time environments: executing an existing plan pays execution costs, but pays zero *deliberation cost*.
- A decision is treated as an installed graph structure that persists via Narrative Momentum (Paper 03).

### 2.2 Reopening Triggers: Surprise vs. Meta-Analysis
- **Surprise ($\operatorname{Surprise}$):** Occurs when incoming observation $x$ violates the expectation boundary $\mathcal{B}_{\text{target}}$. If an alternative resolution is already held in aperture, direct low-cost revision occurs; otherwise, surprise triggers higher-order meta-analysis.
- **Meta-Analysis ($\operatorname{MetaAnalyse}$):** An explicit, paid operation that pauses reactive execution, expands aperture, re-evaluates the Seldon manifold at deeper horizon $h' > h$, and searches for new target shapes.

### 2.3 The Non-Self-Authorisation Constraint
- **Core Proposition:** *No future self can authorise the transition that first installs it.*
- An agent contemplating a radical preference change (e.g., Ulysses binding himself to the mast, addiction recovery, or transformative experience; Paul 2014) cannot evaluate the transition using the future self’s utility function, because that utility function exists only as a consequence of the transition. The decision must be justified entirely under the present frame's grammar and Narrative.

---

## 3. Rated Issues & Deficiencies

### [MAJOR] Issue 02c-1: Formalization of the Choice Operator Under Pareto Incomparability
- **Location:** Section 3 (`sec:target-shapes`), lines 210–270.
- **Description:** The paper correctly notes that "Pareto comparison does not supply selection" when multiple non-dominated acceptable target shapes exist in the manifold. However, it fails to specify the symmetry-breaking mechanism that ultimately selects a unique branch. In standard decision theory, if two target shapes $T_1, T_2$ are Pareto-incomparable and both lie within the acceptable set, an agent will stall in deadlock (Buridan's principle) unless an explicit tie-breaking rule, lexicographic ordering, or randomized choice operator is defined.
- **Proposed Remediation:** Formally introduce a tie-breaking rule: when Pareto comparison leaves multiple eligible target shapes, selection defaults to the candidate minimizing total graph-alteration cost relative to standing Narrative:
  $$\tau^* = \arg\min_{\tau \in \mathcal{P}_{\text{eligible}}} C_{\text{alter}}(\tau \mid \mathcal{N}).$$

### [MINOR] Issue 02c-2: Mathematical Quantification of Surprise
- **Location:** Section 2 (`sec:reopening`), lines 130–185.
- **Description:** The paper defines surprise qualitatively as an observation leaving the acceptable region. In Bayesian cognitive science and predictive processing (Friston, 2010), surprise is quantified rigorously as negative log-evidence or Kullback-Leibler divergence between prior and posterior:
  $$\mathcal{S}(y) = -\ln p(y \mid m).$$
  The paper should explicitly define the relation between Graphic Equalisation's discrete topological boundary crossing and information-theoretic Shannon surprise.

---

## 4. Strengths & Durable Contributions

1. **The Non-Self-Authorisation Principle:** Proving that future selves cannot authorize their own installation provides a vital formal solution to the problem of transformative choice in philosophical decision theory.
2. **Target Shapes over Point Optimization:** Replacing fragile scalar optimization (which is vulnerable to Goodhart’s Law and specification gaming) with robust topological target shapes reflects cutting-edge insights in AI alignment and viability theory.
3. **Cognitive Economics of Inaction:** Formalizing the standing Narrative as zero-deliberation-cost continuation provides a realistic, mathematically sound explanation for institutional and individual inertia.

---

## 5. Academic Verdict

**Verdict:** **ACCEPT WITH MINOR REVISIONS**  
An exceptional, rigorous formalization of bounded decision theory. Resolving the Pareto tie-breaking mechanism (Issue 02c-1) will complete its mathematical specification.
