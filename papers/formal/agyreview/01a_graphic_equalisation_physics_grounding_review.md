# Academic Peer Review: `01a_graphic_equalisation_physics_grounding.tex`
**Document:** `01a_graphic_equalisation_physics_grounding.tex`  
**Title:** The Law of Graphic Equalisation --- Physics Grounding  
**Draft / Revision:** `draft-2026-09-06.1` · document revision `r46`  
**Author:** Matthew Parslow (Independent Researcher)  
**Corpus Role:** Primary Physical Grounding (Mapping Relational Substrate to Fundamental Physics)  
**Dependencies:** Deeply coupled with `00_is` (`[IS-]`), `01` (`[GE-]`), `01d` (`[BN-]`), `03` (`[NM-]`), `04` (`[NV-]`).

---

## 1. Executive Summary

`01a_graphic_equalisation_physics_grounding.tex` undertakes one of the most audacious programs in contemporary theoretical physics: grounding relativistic mechanics, quantum measurement, entanglement, thermodynamics, and gauge conservation laws within the discrete, frame-relative relational substrate of Graphic Equalisation.

The paper proceeds not by postulating quantum fields or spacetime manifolds as fundamental primitives, but by treating physical phenomena as the *contingent rule-content and budget economics* of graph-based frames that run. Its central thesis is that physical spacetime, the speed of light $c$, Lorentz dilation, and gravitational curvature are joint consequences of a universal **change-budget**: a frame has a finite capacity for realised change, and spending that budget on spatial displacement necessarily reduces the budget available for local internal recurrence (time dilation).

The work is executed with rigorous technical clarity, consistently distinguishing what the substrate strictly *forces* from what it merely *recovers* via contingent, self-located parameter assignments. Nonetheless, critical challenges emerge regarding Lorentz covariance in discrete networks, the mathematical recovery of the Riemann tensor from discrete change budgets, and the formal justification of complex amplitudes over real ones.

---

## 2. Core Physical Architecture & Claims

### 2.1 The Speed of Light and the Change Budget
- **The Tripartite Definition (`def:three-c`):**
  1. $c$ as the maximum rate of graph change propagation.
  2. $c$ as the conversion constant between inferred duration and spatial displacement ($\Delta x / \Delta t$).
  3. $c$ as the local normalization constant ($c = 1$ in natural frame units).
- **Relativity Reconciled (`prop:sr-gr`):** Special Relativity (SR) and General Relativity (GR) are unified as a single change budget spent in two different ways:
  $$\Delta_{\text{total}}^2 = \Delta_{\text{motion}}^2 + \Delta_{\text{internal}}^2 + \Delta_{\text{field/load}}^2$$
  Motion through space (SR) and motion through a gravitational gradient (GR) both consume graph writes, directly yielding kinematic and gravitational time dilation without requiring an antecedent smooth Lorentzian metric.

### 2.2 Quantum Measurement & Entanglement
- **Frame-Relative Measurement (`prop:wigner`):** Resolves the Wigner’s Friend paradox by denying a global wave-function collapse. Collapse is an in-frame event $\operatorname{Coll}^W$: to the friend inside the lab, collapse is realised history; to Wigner outside, the lab remains in an unresolved possibility set until interaction across the lab boundary forces collapse in Wigner's frame.
- **Entanglement as Superframe Dimensionality (`prop:mixed`, `rem:light-switch`):** Entangled states are pure in the superframe $W$ that contains both particles, but appear mixed to the subframes $A$ and $B$ because the phase-correlation relation exists along an axis that subframe apertures cannot individually resolve. "Action at a distance" is an aperture artifact of mistaking a single superframe relation for two disconnected local states.

### 2.3 Thermodynamics and the Second Law
- **Entropy as Unresolved Distinction (`def:entropy`, `prop:second-law`):** Entropy is defined relationally as the volume of micro-structural differences that a given frame’s coarse-grained aperture does not distinguish.
- **The Arrow of Time:** The Second Law is derived as the cumulative consequence of the *no-copy principle* (Proposition `prop:second-law`): because destructive graph writes discard antecedent state without creating a global record, the path cannot be reversed from present local structure alone.

---

## 3. Rated Issues & Deficiencies

### [CRITICAL] Issue 01a-1: Recovery of Local Lorentz Covariance $SO(3,1)$ on a Discrete Lattice
- **Location:** Section 2 (`sec:c-rate`), lines 130–165; Section 4 (`sec:sr-gr`), lines 471–495.
- **Description:** The paper claims that Lorentz invariance and the invariant interval $ds^2 = c^2 dt^2 - dx^2$ are recovered from discrete change budgets on the integer lattice $\mathbb{Z}^D$. However, a well-known theorem in lattice field theory (and causal dynamical triangulations) states that a regular discrete lattice breaks continuous rotational and boost invariance ($SO(3,1)$) down to a discrete subgroup, introducing preferred-frame anisotropy at high energies (the "checkerboard problem"). If the substrate is discrete, how is exact Lorentz symmetry restored at macroscopic scales without introducing unobserved Lorentz-invariance violation (LIV) constrained by gamma-ray burst time-lag observations (e.g., Fermi-LAT bounds)?
- **Proposed Remediation:** Formally address LIV constraints. Either:
  1. Prove that random graph topologies (Poisson sprinkling as in Causal Sets) suppress anisotropy; or
  2. State explicitly as an empirical falsifier that the theory predicts high-energy dispersion $\Delta t \sim (E/M_{\text{Planck}})^n$, citing current observational bounds from astroparticle physics.

### [MAJOR] Issue 01a-2: Mathematical Derivation of the Einstein Field Equations
- **Location:** Section 4 (`sec:sr-gr`), lines 471–498.
- **Description:** Proposition `prop:sr-gr` asserts that GR curvature is the change budget allocated to gravitational potential load. While conceptually brilliant (mirroring Jacobson’s thermodynamic derivation of Einstein equations), the paper fails to write down the explicit mathematical mapping from graph change load $\Delta_{\text{load}}$ to the Einstein tensor $G_{\mu\nu} = 8\pi G T_{\mu\nu}$. Stating that "GR is the budget spent on load" is a physical analogy until a derivation demonstrates that the vanishing divergence $\nabla^\mu G_{\mu\nu} = 0$ follows from local graph-rewrite conservation.
- **Proposed Remediation:** Clearly label the connection to full General Relativity as a *conjecture / research target* rather than an established proposition, referencing companion paper `01i` which explicitly provides the required cautionary ledger.

### [MAJOR] Issue 01a-3: The Complex Amplitude Selection Problem
- **Location:** Section 8 (`sec:amplitudes`), lines 662–685 (`prop:born`).
- **Description:** The paper derives the Born rule $P_i = |\psi_i|^2$ by invoking closure and conjugate pairs. However, it relies on the selection of the complex field $\mathbb{C}$ over the real numbers $\mathbb{R}$ or quaternions $\mathbb{H}$ as an admitted contingent rule-content. The paper notes that this selection is "self-located," but does not formally prove why a real Hilbert space fails to cohere under the substrate's own composability criteria (such as local tomography in CDP 2011).
- **Proposed Remediation:** Explicitly incorporate the local tomography theorem (Chiribella et al., 2011), showing that local tomography forces complex Hilbert spaces over real ones within the substrate’s compositional framework.

### [MINOR] Issue 01a-4: Decay Phase Retention
- **Location:** Section 14 (`sec:decay`), lines 1224–1235 (`prop:decay`).
- **Description:** Proposition `prop:decay` states that exponential decay is what an unretained phase looks like. The proof sketch assumes a Poisson distribution over unobserved phase cycles, but does not provide the explicit measure under which the exponential distribution is uniquely forced over sub-exponential power laws (e.g., in quantum Zeno regimes).

---

## 4. Strengths & Durable Contributions

1. **Resolution of Wigner's Friend via Relational Collapse:** Proposition `prop:wigner` resolves measurement paradoxes cleanly without many-worlds branching or ad-hoc non-linear collapses, aligning with relational quantum mechanics (Rovelli 1996) while grounding it in concrete graph boundaries.
2. **Structural Derivation of Thermodynamic Arrow:** Deriving the Second Law from the no-copy postulate of graph overwrites (`prop:second-law`) provides a beautiful mechanistic foundation for macroscopic irreversibility.
3. **Dimensional vs. Dimensionless Constants:** Proposition `prop:dim-boundary` provides a deeply illuminating analysis demonstrating that dimensional constants ($c, \hbar, G$) are mere frame conversion factors, whereas dimensionless ratios (like the fine-structure constant $\alpha$) represent irreducible, contingent graph-grammar couplings.

---

## 5. Academic Verdict

**Verdict:** **ACCEPT WITH MAJOR REVISIONS**  
The paper represents a groundbreaking conceptual tour-de-force. However, to meet the highest standards of formal academic physics, it must resolve the Lorentz-invariance-violation challenge on discrete graphs (Issue 01a-1) and replace the hand-waving derivation of Einstein curvature with the rigorous bridge ledger specified in Paper 01h/01i (Issue 01a-2).
