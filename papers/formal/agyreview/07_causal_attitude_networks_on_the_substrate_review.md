# Academic Peer Review: `07_causal_attitude_networks_on_the_substrate.tex`
**Document:** `07_causal_attitude_networks_on_the_substrate.tex`  
**Title:** Causal Attitude Networks on the Substrate: What Moved, What Did Not, and What the Mean Field Costs  
**Draft / Revision:** `draft-2026-09-06.1` · document revision `r3`  
**Author:** Matthew Parslow (Independent Researcher)  
**Corpus Role:** Applied Psychological Network & Computational Architecture Audit  
**Dependencies:** Links to `01_law_of_graphic_equalisation_theory_referenced` (`[GE-]`).

---

## 1. Executive Summary

`07_causal_attitude_networks_on_the_substrate.tex` is an empirical and architectural case study analyzing the implementation of **Causal Attitude Networks (CAN)** (Dalege et al., 2016)—a psychological framework that models human attitudes, beliefs, and cognitive consistency as an Ising spin network of mutually influencing nodes.

The paper’s core intellectual value lies in its rigorous distinction between **hosting a model** and **natively moving a model** onto the Graphic Equalisation substrate:
- A *hosted* model merely invokes an external compiled solver (e.g., a synchronous mean-field matrix solver written in C or Python) and writes the resulting vector back to the graph. The intermediate states, relaxations, and energy conflicts remain opaque black boxes outside the graph grammar.
- A *native* model decomposes the dynamics into discrete, local, asynchronous graph-rewrite rules, exposing every intermediate state, threshold crossing, and energy descent step to internal inspection, mutation, and audit.

The paper honestly documents the engineering history of this migration, recording where initial theoretical expectations failed, where engine capabilities had to be extended (scoped rule execution), and reporting that two of its original five falsifiability commitments fired against the experimental record.

---

## 2. Core Formal Claims & Engineering Architecture

### 2.1 The Native Discrete Dynamics
- **State Representation:** Each attitude node takes a value $s_i \in \{-1, 0, +1\}$ (a three-state discrete Potts/Ising variant with an explicit neutral band).
- **Local Field Equation:** The net field acting on node $i$ is:
  $$h_i = b_i + \sum_{j \in \mathcal{N}(i)} w_{ji} s_j$$
  where $b_i$ represents baseline/identity bias and $w_{ji}$ represents directed causal influence.
- **Rule Commitments:** The update is executed natively via five graph rules and four admissibility productions:
  - If $h_i > \theta$, commit $s_i \leftarrow +1$.
  - If $h_i < -\theta$, commit $s_i \leftarrow -1$.
  - If $|h_i| \le \theta$, commit $s_i \leftarrow 0$.
- **Asynchronous Execution:** Unlike standard synchronous mean-field iterations, the native substrate applies updates sequentially in place. Each committed node immediately alters the local fields of its neighbors, eliminating artificial limit-cycle oscillations caused by simultaneous parallel updates.

### 2.2 The Convergence Proof Boundary
- The paper explicitly notes that while the **binary 2-state Ising model** guarantees monotonic Lyapunov energy descent ($H = -\frac{1}{2}\sum w_{ij} s_i s_j - \sum b_i s_i$), **three-state discrete networks with asymmetric directed weights** ($w_{ij} \neq w_{ji}$) do *not* guarantee convergence to a unique fixed point.
- The paper refrains from asserting a false convergence theorem, properly categorizing three-state settling as an open operational commitment.

---

## 3. Rated Issues & Deficiencies

### [MAJOR] Issue 07-1: Limit Cycles in Asymmetric Directed Networks
- **Location:** Section 3 (`sec:convergence`), lines 180–230.
- **Description:** In social psychology and cognitive networks, causal influences are rarely symmetric ($w_{ij} \neq w_{ji}$; e.g., belief in climate change influences voting preference much more strongly than voting preference influences belief in physics). In an asynchronous discrete system with directed asymmetric edges and a neutral band ($\{-1, 0, +1\}$), the system can easily enter deterministic cyclic attractors (limit cycles) rather than fixed points. The paper does not provide an explicit cycle-detection or damping grammar for native execution.
- **Proposed Remediation:** Incorporate an explicit cycle-detection rule or momentum-weighted threshold adaptation (linking to Paper 03, Narrative Momentum) to guarantee terminal fixed-point settling in directed networks.

### [MINOR] Issue 07-2: Parity-on-Credit vs. Reproducibility
- **Location:** Section 1 (`sec:moved`), lines 83–93.
- **Description:** The paper relies heavily on "parity-on-credit," citing an uncirculated pre-registered implementation record with specific commit hashes and dates. While this transparently states the evidential status, external peer reviewers cannot independently execute the test harness.
- **Proposed Remediation:** In alignment with the mandatory non-proliferation embargo ([`SUBSTRATE_IMPACT_ANALYSIS_SEPT2026.md`](file:///home/matt/ozmadev/ocelot/docs/research/psychology_affect/SUBSTRATE_IMPACT_ANALYSIS_SEPT2026.md)), satisfy academic verification by publishing **static, step-by-step state-transition trace logs and matrix evaluation tables** for the five rewrite rules over the 10-node test fixture, verifying convergence behavior without distributing an executable rewrite runner.

---

## 4. Strengths & Durable Contributions

1. **Exemplary Epistemic Candor:** Openly reporting that two of its original falsifiability commitments fired against experimental measurements and retracting premature claims about engine capabilities demonstrates the highest standard of scientific integrity.
2. **The Hosted vs. Native Distinction:** Defining the exact ontological difference between running compiled subroutines versus native graph rewrites provides an essential architectural principle for cognitive computing and neuro-symbolic AI.
3. **Asynchronous Energy Dynamics:** Replacing synchronous matrix updates with discrete, progress-preserving local rewrites solves well-known ping-pong oscillation artifacts in classical Hopfield and Ising networks.

---

## 5. Academic Verdict

**Verdict:** **ACCEPT WITH MINOR REVISIONS**  
A superb, methodologically rigorous case study that grounds high-level cognitive psychology in concrete graph-rewrite semantics. Addressing directed limit cycles (Issue 07-1) will finalize its theoretical completeness.
