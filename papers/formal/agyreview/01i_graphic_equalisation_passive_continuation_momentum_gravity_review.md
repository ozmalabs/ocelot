# Academic Peer Review: `01i_graphic_equalisation_passive_continuation_momentum_gravity.tex`
**Document:** `01i_graphic_equalisation_passive_continuation_momentum_gravity.tex`  
**Title:** The Law of Graphic Equalisation --- Passive Continuation Grounding: Momentum, Gravity, and the Cost of Alteration  
**Draft / Revision:** `draft-2026-09-06.1` · document revision `r11`  
**Author:** Matthew Parslow (Independent Researcher)  
**Corpus Role:** Mechanics & Gravitational Research Ledger (Fail-Closed Unreleased Set)  
**Dependencies:** Links to `01` (`[GE-]`), `01a` (`[PH-]`), `01g` (`[TP-]`), `01h` (`[IG-]`), `03` (`[NM-]`).

---

## 1. Executive Summary

`01i_graphic_equalisation_passive_continuation_momentum_gravity.tex` investigates one of the deepest conceptual questions in the foundation of physics: the relationship between **inertial momentum** (Newton’s First Law / flat four-momentum conservation) and **gravitational free fall** (Einstein’s Equivalence Principle / geodesic motion in curved spacetime).

Following the rigorous methodological precedent established in Paper 01h, Paper 01i avoids premature physical assertions. It defines **passive continuation** as the *admissible reuse of presently operative structure with zero additional alteration cost in a declared grounding class*. It then asks whether inertial transport in flat spacetime ($dp^\mu / d\tau = 0$) and geodesic propagation in curved spacetime ($u^\nu \nabla_\nu u^\mu = 0$) can be understood as two distinct physical manifestations of a single, unified passive-continuation law.

The paper constructs a meticulous four-way derivation ledger (Inherited, Hypothesized, Owed Bridge, Experimentally Constrained) and concludes that while the conceptual unification is deeply appealing, the mathematical and operational bridges required to derive the Levi-Civita connection and the stress-energy tensor from graph rewrites remain undischarged.

---

## 2. Core Formal Concepts & Derivation Ledger

### 2.1 The Declared Continuation Situation
$$\mathfrak{C}_t^W = (W, G_t, \Gamma_t, \mathcal{P}_t, S_t, \mathcal{A}, \kappa, \mathcal{R}_t, \mathcal{O}_t)$$
where $S_t$ is operative carried structure, $\mathcal{A}$ is a declared alteration class, $\kappa$ is an ordered cost domain, and $\mathcal{R}_t$ is support infrastructure.

### 2.2 Passive Continuation Defined
- **Core Proposition:** Reusing declared carried structure incurs zero *additional* alteration cost ($\Delta \kappa = 0$).
- Passive continuation is explicitly distinguished from:
  - "Doing nothing" or static rest (a clock or moving particle is actively running).
  - Absence of time or absence of interaction at fine grains.
  - Zero support cost in containing superframe environments.

### 2.3 The Duality: Flat Inertia vs. Curved Geodesics
- **Flat Regime:** When background metric curvature is negligible, passive continuation manifests as classical inertial momentum: persistent rectilinear motion with conserved momentum $p^\mu$.
- **Load-Shaped Regime:** When graph boundary interactions impose a change load, the unforced path follows the geodesic equation $u^\nu \nabla_\nu u^\mu = 0$, where proper acceleration $a^\mu = 0$.
- **The Core Finding:** Momentum is not a force, and free fall in GR is not a locally felt force. Both represent unforced, zero-alteration-cost trajectories through their respective background structures.

---

## 3. Rated Issues & Technical Deficiencies

### [MAJOR] Issue 01i-1: The Source Problem (Deriving $T_{\mu\nu}$ from Alteration Costs)
- **Location:** Section 3 (`sec:bridges`), lines 310–380.
- **Description:** In general relativity, geodesic motion ($u^\nu \nabla_\nu u^\mu = 0$) is intimately coupled to spacetime curvature via the Einstein field equations, which are sourced by the stress-energy tensor $T_{\mu\nu}$. The paper posits that "alteration cost" in graph rewriting generates the curvature load. However, alteration cost $\kappa$ in Graphic Equalisation is a scalar flow, whereas $T_{\mu\nu}$ is a symmetric, divergence-free rank-2 tensor in $3+1$ dimensions ($10$ independent components). The paper provides no mathematical mechanism for promoting a scalar rewrite cost into a conserved rank-2 tensor.
- **Proposed Remediation:** Formally identify the tensorial promotion of alteration cost as an open mathematical barrier in the ledger, explicitly citing Lovelock's theorem and the contracted Bianchi identities ($\nabla^\mu G_{\mu\nu} = 0$).

### [MINOR] Issue 01i-2: Equivalence Principle Vulnerability at High Energy
- **Location:** Section 4 (`sec:constraints`), lines 520–580.
- **Description:** The Weak Equivalence Principle (universality of free fall, tested to $10^{-15}$ by the MICROSCOPE satellite) requires that all test bodies fall with identical acceleration regardless of composition. If passive continuation is sensitive to the internal graph structure $S_t$ of a test body, different graph topologies could in principle couple differently to background change load, violating the Equivalence Principle.
- **Proposed Remediation:** State explicitly as a falsifier that any composition-dependent alteration cost in the vacuum geodesic limit falsifies the proposed passive-continuation grounding of gravity.

---

## 4. Strengths & Durable Contributions

1. **Brilliant Conceptual Unification of Inertia and Free Fall:** Identifying Newton's First Law and Einstein's geodesic equation as two realizations of zero-additional-cost structure reuse is a profound conceptual synthesis.
2. **Exemplary Ledger Methodology:** The four-way classification table (Inherited vs. Hypothesized vs. Owed vs. Constrained) prevents any obfuscation or premature claiming of solved physics.
3. **Rigorous Preservation of the Non-Force Character of Gravity:** Correctly honoring the geometric nature of general relativity (gravity as spacetime curvature, not an exchange force) safeguards the framework from the pitfalls of naive graviton-exchange models.

---

## 5. Academic Verdict

**Verdict:** **ACCEPT AS A RESEARCH SPECIFICATION**  
An outstanding foundational paper that cleanly articulates the exact mathematical requirements for a relational theory of inertia and gravitation. It rightly remains in the fail-closed research tier until the rank-2 tensor bridge (Issue 01i-1) is constructed.
