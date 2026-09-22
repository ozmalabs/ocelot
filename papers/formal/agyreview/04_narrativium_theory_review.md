# Academic Peer Review: `04_narrativium_theory_referenced.tex`
**Document:** `04_narrativium_theory_referenced.tex`  
**Title:** Narrativium --- Theory: Frame-Relative Capacity for Consequential Deformation  
**Draft / Revision:** `draft-2026-09-06.1` · document revision `r22`  
**Author:** Matthew Parslow (Independent Researcher)  
**Corpus Role:** Formal Theory of Capacity, Controllability, and Revision Horizons  
**Dependencies:** Connected with `01` (`[GE-]`), `02` (`[SM-]`), `03` (`[NM-]`), `01a` (`[PH-]`), `01b` (`[MS-]`).

---

## 1. Executive Summary

`04_narrativium_theory_referenced.tex` introduces and formalizes the second half of the dynamic pair begun in Paper 03: while Paper 03 formalizes *Narrative Momentum* ($\mathcal{N}$, the persistence of carried history), Paper 04 formalizes **Narrativium ($N$)**—defined as a frame’s **capacity for consequential deformation**.

The author transparently acknowledges the literary provenance of the term: *Narrativium* is borrowed from Terry Pratchett, Ian Stewart, and Jack Cohen (*The Science of Discworld*, 1999), where it denotes the mythical element ensuring that stories unfold according to dramatic necessity. In Parslow’s formalization, the concept is entirely naturalized and mathematical: Narrativium is the frame-relative metric of *how much directed deformation an agent or frame can execute within a specified class of actions before exhausting its control budget*.

The paper makes fundamental contributions: rigorously separating state measurements (capacity $N$) from flow expenditures (cost $c$); formalizing cross-frame conversion relations ($\kappa$); and establishing the concept of the **Revision Horizon** ($H_{\text{rev}}$), the precise boundary where an agent's available capacity is exhausted by the minimum cost required to alter its standing Narrative.

---

## 2. Core Formal Architecture & Theoretical Claims

### 2.1 The Definition of Narrativium
- **Core Question:** Given a frame $\mathcal{F}$, a configuration $G$, and a target deformation class $\mathcal{X}$:
  $$\text{What consequential deformation is reachable from this configuration, in this frame, for this deformation class?}$$
- **State vs. Flow (The Measurement/Expenditure Separation):**
  - Narrativium $N$ is a *state measurement* (the capacity currently available).
  - Cost $c$ is a *flow* paid during a realised transition.
  - Spending cost $c$ does *not* fix the sign of $\Delta N$: spending capacity can leave a frame with less capacity (exhaustion), equal capacity (steady-state flow), or *more* capacity (investment that unlocks new actions).

### 2.2 Cross-Frame Accounting and the Conversion Relation ($\kappa$)
- By Axiom -1 (`GE-ax:no-view`) and Proposition `NV-prop:no-sum`, there is no frame-free total of Narrativium across the universe. Two distinct frames $F_1, F_2$ cannot sum their capacities directly.
- Cross-frame aggregation is admissible only when an explicit, instantiated **conversion relation $\kappa$** exists between them (e.g., currency exchange rates, standardized contracts, translation dictionaries).
- **The Invariance Test:** A cross-frame theoretical claim is valid only if it is invariant under all admissible choices of $\kappa$.

### 2.3 The Revision Horizon ($H_{\text{rev}}$)
- **Definition (`NV-def:horizon`):** The revision horizon occurs where the frame's Narrativium capacity equals the minimal cost required to revise its standing Narrative:
  $$H_{\text{rev}} = \inf \left\{ t \mid N(t) < C_{\text{min\_alter}}(\mathcal{N}(t)) \right\}$$
- Beyond the revision horizon, the system is **locked in**: it no longer possesses sufficient capacity to alter its trajectory, and must continue executing its historical momentum until failure or external container rescue.

---

## 3. Rated Issues & Deficiencies

### [MAJOR] Issue 04-1: Mathematical Alignment with Control Theory Controllability Gramians
- **Location:** Section 1 (`sec:dependencies`), lines 80–90; Section 2 (`sec:deformation-class`).
- **Description:** The paper cites Kalman’s controllability (1960) and Aubin’s viability theory (1991) as nearest mathematical neighbors, but does not formally map Narrativium onto standard control-theoretic objects. In linear and non-linear control theory, the capacity to deform a state vector $x$ under bounded control input $\|u(t)\| \le U$ is measured by the **Controllability Gramian**:
  $$W_c(t) = \int_0^t e^{A\tau} B B^T e^{A^T\tau} d\tau$$
  or the volume of the reachable set $\operatorname{Vol}(\mathcal{R}_t)$. Because Narrativium is scalar-valued in many of the paper's examples, it collapses a multi-dimensional ellipsoidal capacity into a single number without specifying the projection norm.
- **Proposed Remediation:** Formally define scalar Narrativium $N_\mathcal{X}$ as the normalized volume or minimum singular value of the reachable deformation ellipsoid under grammar $\Gamma$:
  $$N_\mathcal{X}(G) = \sigma_{\text{min}}\left(\mathcal{R}_\mathcal{X}(G)\right) \quad \text{or} \quad \operatorname{Vol}\left(\mathcal{R}_\mathcal{X}(G)\right).$$

### [MINOR] Issue 04-2: The Pratchett Homage vs. Academic Perception
- **Location:** Title, Abstract, and Section 1, lines 78–82.
- **Description:** While borrowing "Narrativium" from Terry Pratchett is an affectionate and memorable literary homage, it poses a severe perceptual hazard in academic peer review. Conventional physicists, computer scientists, and economists are prone to dismiss any paper featuring "Narrativium" in its title as whimsical satire rather than formal mathematics.
- **Proposed Remediation:** Subtitle the paper prominently: *"Capacity for Consequential Deformation,"* and explicitly emphasize in the abstract that the paper formalizes bounded controllability and viability theory in discrete relational networks.

---

## 4. Strengths & Durable Contributions

1. **The Separation of Capacity ($N$) from Expenditure ($c$):** Decoupling state capacity from transition cost is a profound conceptual clarification that resolves common paradoxes in economics and energetics (e.g., spending capital to increase productive capacity).
2. **The Revision Horizon Formulation:** Defining the exact point of agency loss ($N < C_{\text{alter}}$) provides a rigorous, highly applicable model for organizational bankruptcy, technical debt accumulation, psychological burnout, and geopolitical lock-in.
3. **The Invariance Test for Cross-Frame Conversions:** Mandating that cross-frame claims survive variations in $\kappa$ provides an ironclad guard against false aggregation and currency-illusion fallacies in macroeconomics and sociology.

---

## 5. Academic Verdict

**Verdict:** **ACCEPT WITH MINOR REVISIONS**  
A deeply original, mathematically powerful framework for capacity and controllability. Aligning the capacity metric with control-theoretic reachable set volumes (Issue 04-1) will solidify its academic authority.
