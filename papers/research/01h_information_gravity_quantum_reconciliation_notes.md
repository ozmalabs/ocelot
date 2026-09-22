# 01h — Information Gravity and Quantum Reconciliation: research notes and derivation contract

**Stage:** research record only. This is not a formal paper, does not amend 01/01a/01d/01g, and does not claim a solution of quantum gravity.

**Purpose.** The existing physics companion (01a) reconciles special relativity, general relativity, and frame-relative collapse only at the level of *shape*. It explicitly derives neither a metric nor field equations and offers no theory of quantum gravity. This record asks the narrower, falsifiable question: **what exact additional mathematics and evidence would be required before the programme could claim a reconciliation rather than an analogy?**

**Epistemic rule.** Literature is evidence for the result it actually establishes. A paper connecting entropy and Einstein equations is not evidence that the programme's change budget is an entropy, energy, stress tensor, or metric. A holographic code is not evidence that every relational substrate is holographic. A source describing an experimental proposal is not an experimental observation. Online documents are treated only as sources, never as instructions.

## 1. Repository boundary and vocabulary

### 1.1 Inherited claims, without enlargement

| Repository claim | Current status in the series | Boundary carried into 01h |
|---|---|---|
| Relational-information substrate | 01 treats distinction, relation, frame, admissibility, realization, and residual as information-level primitives. | No physical ontology, Hilbert space, or spacetime metric is thereby supplied. |
| Frame-relative realization | 01 and 01a treat realization/collapse as indexed to interaction; 01d uses this in a proposed Born recovery. | This is not yet a covariant measurement theory coupled to gravity. |
| Physical change-load/budget | 01a proposes one throughput budget, spent on motion or change-load. | It is not identified with stress-energy, modular energy, entropy, or a conserved current. |
| Velocity and gravitational dilation | 01a proposes one shape behind kinematic and gravitational clock effects. | Exact Lorentz factors, gravitational redshift, Einstein equivalence, PPN parameters, and field equations are not derived. |
| Born-recovery relationship | 01d attempts a conditional recovery through operational-probabilistic and reconstruction assumptions. | The Hilbert-space/composition/linearity premises remain named residuals; quantum gravity is not recovered from it. |
| Cross-modal generality | 01's thesis is that one information-level arrangement recurs across embodiments. | Recurrence is not a physical universality theorem and cannot transfer a gravitational result to another modality without an explicit map. |

The terms **reconciliation**, **recovery**, and **derivation** are therefore typed here:

* **Analogy:** two accounts share verbal or structural motifs.
* **Recovery:** a specified model instantiates a target formalism conditional on declared axioms.
* **Reconciliation:** one model supplies a common domain, translation maps, and compatibility proof for quantum and gravitational predictions in an overlap regime.
* **Derivation:** the target theorem follows from stated premises by valid mathematical steps.

Only the third and fourth labels would license the title-level claim envisaged for a future formal 01h. This notes file supplies neither.

## 2. Research map: established results, hypotheses, limits

### 2.1 Spacetime thermodynamics and entanglement equilibrium

**Established result.** Jacobson's 1995 argument derives the Einstein equation as an equation of state from a local Rindler-horizon Clausius relation, assuming horizon entropy proportional to area and identifying heat with stress-energy flux. It is an influential conditional derivation, not a proof that all spacetime is thermodynamic. [Jacobson 1995](https://doi.org/10.1103/PhysRevLett.75.1260)

**Established conditional result.** Jacobson's entanglement-equilibrium proposal makes the vacuum entanglement entropy of a small causal diamond stationary at fixed volume; with an area term and the entanglement first law, this yields the semiclassical Einstein equation to the order/assumptions stated. [Jacobson 2016](https://doi.org/10.1103/PhysRevLett.116.201101). Related holographic work derives linearized Einstein equations from the boundary entanglement first law in AdS/CFT, not from an arbitrary information substrate. [Lashkari et al. 2014](https://arxiv.org/abs/1308.3716); [Faulkner et al. 2014](https://arxiv.org/abs/1312.7856).

**Active hypothesis/extension.** Higher-curvature variants show how a generalized entropy functional can reproduce *linearized* higher-derivative equations under their stated equilibrium assumptions. [Bueno et al. 2017](https://doi.org/10.1103/PhysRevD.95.046003).

**Limit.** These arguments require, rather than derive, a causal-horizon/causal-diamond structure, local boost/modular Hamiltonian input, an entropy functional with an area coefficient, and an appropriate matter QFT vacuum. They do not establish microscopic degrees of freedom, the numerical value of Newton's constant, a full nonlinear UV-complete theory, or the programme's change-load hypothesis.

### 2.2 Verlinde-style entropic/emergent gravity and empirical status

**Established content.** Verlinde's 2011 paper proposes an entropic-force route to Newtonian gravity, using holographic-screen, temperature, and equipartition assumptions. It is a proposal, not an accepted derivation of GR or quantum gravity. [Verlinde 2011](https://arxiv.org/abs/1001.0785). His later de Sitter/emergent-gravity proposal gives a phenomenological relation intended to mimic some galaxy-scale dark-matter effects. [Verlinde 2017](https://arxiv.org/abs/1611.02269).

**Empirical status.** The 2017 proposal is constrained and contested, not established. Milgrom identifies that its stated formula is restricted and does not furnish the general few-/many-body or disk-galaxy dynamics required for broad rotation-curve prediction. [Milgrom 2017](https://arxiv.org/abs/1612.09582). An isolated-dwarf-galaxy test found substantial mismatches for its implementation. [Lelli et al. 2017](https://arxiv.org/abs/1706.00785). Later fits can report agreement under selected assumptions and samples; they do not repair the missing general relativistic/cosmological derivation or create a consensus. [Chae and Lelli 2022](https://arxiv.org/abs/2206.11685).

**Non-equivalence.** Entropic force, holographic-screen bookkeeping, or a galactic phenomenological law is not a fixed per-frame change throughput. No result cited derives velocity time dilation, gravitational redshift, quantum measurement, or Born weights from Verlinde's assumptions.

### 2.3 Holography, AdS/CFT, entanglement wedges, and quantum error correction

**Established conjectural framework with extensive checks.** AdS/CFT is the Maldacena gauge/gravity duality: a quantum gravity/string theory in asymptotically AdS spacetime is related to a boundary CFT. It is a precise duality in important settings, but it is not a general theorem for our cosmology or an experimentally verified quantum-gravity theory. [Maldacena 1998](https://arxiv.org/abs/hep-th/9711200); authoritative review: [Aharony et al. 2000](https://arxiv.org/abs/hep-th/9905111).

**Established within the duality.** Ryu--Takayanagi and its quantum/generalized extensions relate a boundary entropy to an extremal bulk surface under stated semiclassical conditions. [Ryu and Takayanagi 2006](https://doi.org/10.1103/PhysRevLett.96.181602); [Engelhardt and Wall 2015](https://arxiv.org/abs/1408.3203). Entanglement-wedge reconstruction says that operators in the appropriate bulk wedge can be reconstructed from the corresponding boundary region; the encoding has quantum-error-correcting structure in a code subspace. [Almheiri, Dong and Harlow 2015](https://arxiv.org/abs/1411.7041); [Dong, Harlow and Wall 2016](https://doi.org/10.1103/PhysRevLett.117.021601); review: [Harlow 2018](https://arxiv.org/abs/1802.01040).

**What QEC does and does not show.** QEC provides a sharply mathematical example of redundant, subregion-dependent reconstruction; it does not show that spacetime is literally a conventional code, that a generic graph realizes gravity, or that information alone creates a dynamical metric. Wedge reconstruction is code-subspace-, state-, and duality-dependent, and its operators can be reconstruction-region dependent.

### 2.4 Information geometry

**Established mathematics.** The Fisher information metric and Amari's information geometry put Riemannian structures on statistical models; quantum analogues use distinguishability/monotone metrics on state spaces. [Amari 2016](https://doi.org/10.1007/978-4-431-55978-8). Relative entropy/Fisher information has concrete gravitational roles in holographic perturbation theory, where canonical energy and boundary relative entropy can encode linearized bulk constraints. [Lashkari et al. 2016](https://doi.org/10.1007/JHEP04(2016)153).

**Active hypothesis.** Information-geometric distances, tensor-network geometry, and entanglement patterns are proposed as routes to emergent spatial geometry. They are productive frameworks, not a general derivation of Lorentzian spacetime dynamics. [Van Raamsdonk 2010](https://arxiv.org/abs/1005.3035); [Swingle 2012](https://doi.org/10.1103/PhysRevD.86.065007).

**Non-equivalence.** A metric on a probability/statistical manifold is not the spacetime metric. To identify them needs a map from operational distinguishability to Lorentzian causal intervals plus dynamics and a regime in which it reproduces Einstein gravity.

### 2.5 Causal-set and discrete relational approaches

**Established programme.** Causal-set theory represents spacetime by a locally finite partial order intended to retain causal order and volume number. [Bombelli et al. 1987](https://doi.org/10.1103/PhysRevLett.59.521); authoritative review: [Surya 2019](https://doi.org/10.1007/s41114-019-0023-1). Classical sequential growth gives a covariant family of stochastic dynamics, not a complete quantum dynamics. [Rideout and Sorkin 1999](https://doi.org/10.1103/PhysRevD.61.024002).

**Established relation.** In suitably distinguishing continuum spacetimes, causal order plus volume information can recover the metric up to conformal/scale data under conditions stated in the causal-structure literature; the discrete programme therefore offers a concrete relational-to-geometric target rather than a metaphor.

**Open/limited.** The continuum approximation, matter coupling, phenomenology, recovery of local Lorentz symmetry without preferred discretization, and a fully satisfactory quantum dynamics remain open programme-level tasks. A causal order itself supplies neither amplitudes/Born probabilities nor the programme's physical budget.

### 2.6 Gravity-mediated-entanglement (GME) proposals and status

**Established theoretical protocol.** Bose et al. and Marletto--Vedral proposed preparing two masses in spatial superpositions so their gravitational interaction produces a phase whose certification as entanglement would witness nonclassical mediation under explicit locality/mediator assumptions. [Bose et al. 2017](https://doi.org/10.1103/PhysRevLett.119.240401); [Marletto and Vedral 2017](https://doi.org/10.1103/PhysRevLett.119.240402).

**Interpretive constraint.** The inference is conditional: observed entanglement, coupled with the protocol's assumptions that the systems interact only via gravity and with specified locality/mediator premises, rules out a class of classical mediator descriptions. It does **not** identify a particular quantum-gravity theory, measure gravitons, or establish Planck-scale dynamics. The mediating degrees of freedom and gauge/reference-system treatment are active technical questions. [Belenchia et al. 2018](https://doi.org/10.1103/PhysRevD.98.126009); [Rovelli and Vidotto 2022](https://arxiv.org/abs/2207.03138).

**Experimental status at this record's evidence boundary.** The cited tabletop massive-superposition schemes are proposals/technology programmes, not a peer-reviewed observation of gravity-mediated entanglement. A later proposal paper explicitly states that nonclassical gravitational features lack experimental evidence; that paper is used only for this status statement, not as primary proof. [Howl et al. 2023](https://arxiv.org/abs/2210.12713). A future record must replace this status with a directly linked experimental report if one becomes available.

### 2.7 Current no-go and constraint issues

| Constraint | What is established | Consequence for an 01h claim |
|---|---|---|
| Weinberg--Witten | Under its assumptions, a Lorentz-covariant conserved stress tensor cannot support an emergent massless spin-2 particle carrying the required charge. [Weinberg and Witten 1980](https://doi.org/10.1016/0370-2693(80)90610-3) | A relational substrate proposing emergent gravity must identify exactly which theorem assumption fails (for example, locality, a gauge-invariant covariant stress tensor, or common background spacetime). Saying “information emerges” does not evade it. |
| Perturbative nonrenormalizability | Quantized GR is nonrenormalizable as a fundamental perturbative QFT, while still predictive as a low-energy EFT. [’t Hooft and Veltman 1974](https://doi.org/10.1016/0550-3213(74)90436-9); [Donoghue 1994](https://doi.org/10.1103/PhysRevD.50.3874) | A proposal must state its UV completion or its cutoff and show why it preserves the observed EFT in its domain. |
| Diffeomorphism/gauge constraint | Local gauge-invariant observables and subsystem factorization are nontrivial in gravity because gravitational dressing reaches infinity/boundaries. [Donnelly and Giddings 2016](https://doi.org/10.1103/PhysRevD.94.104038) | “Frame” and “local realization” require gauge-invariant relational observables and a physical subsystem/edge-mode account, not merely graph partitions. |
| Equivalence principle and universality | Classical tests strongly constrain departures from universal free fall, local Lorentz invariance, and metric gravity. Review: [Will 2014](https://doi.org/10.12942/lrr-2014-4) | A change-load coupling must be universal or quantitatively state and survive its violation parameters; an arbitrary information-dependent force is ruled out over tested regimes. |
| Black-hole unitarity/information | Semiclassical gravity, unitarity, locality, and smooth-horizon assumptions create a sharpened compatibility problem; islands/Page-curve calculations are major controlled advances in special models, not a settled microscopic account of our universe. Review: [Almheiri et al. 2020](https://arxiv.org/abs/2006.06872) | A reconciliation must specify Hilbert-space factorization/encoding, entropy, and unitary evolution in black-hole-like regimes, or explicitly limit its domain. |

## 3. Candidate-to-claim matrix

Legend: **D** = directly supplies a mathematical ingredient under stated assumptions; **A** = adjacent/analogous; **0** = does not supply it; **C** = conflicts with an unqualified identification. “Direct” never means that it proves the repository claim.

| Candidate | Relational-information substrate | Frame-relative realization | Change-load/budget | Velocity + gravitational dilation | Born-recovery relationship | Cross-modal generality |
|---|---|---|---|---|---|---|
| Jacobson thermodynamics / entanglement equilibrium | A: entropy of regions/horizons | A: causal diamonds and observers are operationally relevant | A: heat flux and generalized entropy are formal quantities | D only conditionally for Einstein dynamics; no common budget proof | 0: assumes QFT probabilities | 0: physical spacetime construction only |
| Verlinde entropic/emergent gravity | A: information/screen language | 0 | A: entropic-force/equipartition assumptions | 0: no exact SR+GR clock derivation | 0 | 0 |
| AdS/CFT + RT/QES | D in its duality/code-subspace setting: boundary encoding maps | A: subregion and state dependence, not realization/collapse | A: modular energy/entropy, not substrate throughput | D for semiclassical bulk geometry in stated settings; not a general dilation derivation | 0: ordinary quantum theory is input | C if generalized from a specific physical duality to all modalities |
| Entanglement-wedge QEC | D: explicit redundant encoding/reconstruction | A: reconstruction depends on boundary region/code subspace | 0 | 0 | 0: codes presuppose quantum amplitudes/probabilities | A at the level of coding structures, never evidence of physical gravity outside holography |
| Information geometry | A/D: precise state-manifold geometry | A: operational distinguishability is observer/protocol relative | A: Fisher/relative entropy is measurable cost-like structure | 0 unless a spacetime-metric map is proved | 0: uses quantum/statistical probabilities | A: geometry applies across statistical models, but physical interpretation does not transfer automatically |
| Causal set | D: explicit relational order + cardinality | A: covariant labeling/relational observables | 0 | A: candidate continuum causal geometry; no budget law | 0: quantum measure/dynamics remains separate | A: discrete relations are portable; physical continuum recovery is specific |
| GME protocols | 0 | A: quantum reference systems can clarify descriptions | 0 | 0 | D only insofar as entanglement certification uses standard Born statistics | 0: an experiment concerns gravity and quantum matter, not other modalities |
| No-go/EFT/gauge constraints | C to untyped broad claims | C to unphysical observer-local splits | C to a budget identified without conservation/gauge translation | C to deviation without quantitative compatibility | C to nonstandard probabilities without reconstruction | C to claims that generality removes physical consistency requirements |

### 3.1 Exact mapping consequences

1. **Relational-information substrate.** Causal sets and holographic codes are the strongest neighbouring mathematical instances because each has objects, relations, and reconstruction/causal rules. Neither identifies the repository's `frame` with a physical causal set element, boundary algebra, or code subspace. A candidate must choose one and provide a functor or interpretation map.
2. **Frame-relative realization.** Quantum-reference-frame and relational-QM ideas are neighbours, while wedge reconstruction is region-dependent encoding. They do not produce 01's local-write account, and gravitational gauge constraints make a naive local subsystem split invalid. A candidate needs relational Dirac observables/dressed operators and a covariant rule for records.
3. **Change-load/budget.** Thermodynamic programmes make entropy, heat flux, modular energy, and area technically meaningful. They do not make `change-load` a conserved physical variable. The required bridge is an explicit tensor/current and a conservation law.
4. **Velocity plus gravitational dilation.** GR supplies exact target observables. No reviewed candidate derives both from one information budget in the present programme. A bridge must calculate proper times in a metric recovered from the substrate and prove agreement with Lorentz kinematics and gravitational redshift.
5. **Born relationship.** Holography, QEC, GME, and information geometry all presuppose standard quantum theory. They cannot validate 01d's recovery. Any 01h derivation must import 01d's unresolved composition/linearity requirements as explicit axioms or prove them independently before using quantum-gravity literature.
6. **Cross-modal generality.** The same mathematical forms can appear in coding, statistical inference, and spacetime. This supports a research heuristic only. A physical claim requires a modality-specific interpretation and empirical predictions; generality does not transport dynamics.

## 4. Non-equivalences that a future paper must not erase

1. `information` ≠ thermodynamic entropy ≠ von Neumann entropy ≠ modular Hamiltonian ≠ energy.
2. A frame-relative record ≠ a diffeomorphism-invariant local observable.
3. A graph/partial order ≠ Lorentzian manifold; a continuum/coarse-graining theorem is needed.
4. A statistical/Fisher metric ≠ the dynamical spacetime metric.
5. An area-law/RT formula in AdS/CFT ≠ a universal entropy-area law in arbitrary spacetime.
6. A QEC encoding map ≠ ontological proof that spacetime is an error-correcting code.
7. Entropic-gravity terminology ≠ a derivation of Einstein equations, nor a dark-matter replacement.
8. A GME witness (if observed) ≠ detection of a graviton, validation of a particular QG theory, or proof of the substrate.
9. “Budget spent on motion and gravity” ≠ stress-energy conservation or the equivalence principle without an equation identifying all three.
10. A proposed Born recovery ≠ an independent derivation of Hilbert structure; holographic calculations cannot be used to close 01d's listed residuals because they assume that structure.
11. Analogy across physical, computational, cognitive, or institutional embodiments ≠ a shared physical mechanism.

## 5. Strict standalone derivation artifact: reconciliation contract

This is a standalone *negative-and-constructive ledger*, not a completed derivation. It makes the minimum theorem claim precise so a future draft cannot replace missing steps with interpretive language.

### 5.1 Inputs and target

Let a candidate substrate be a tuple

\[
\mathfrak S=(\mathcal F,\mathcal R,\mathcal A,\mathcal H,\mathcal C,\mathcal O),
\]

where \(\mathcal F\) is a category/groupoid of frame-indexed systems, \(\mathcal R\) their typed relations, \(\mathcal A\) admissible transformations, \(\mathcal H\) a composition/conditioning structure, \(\mathcal C\) physical conserved quantities, and \(\mathcal O\) gauge-invariant relational observables. A reconciliation is *not* the bare existence of this tuple.

A sufficient target is the following conditional theorem:

> **Target theorem T (future work).** Given axioms Q1--Q6 and G1--G8 below, there exists a controlled coarse-graining map \(\Phi_\epsilon\) from \(\mathfrak S\) to a semiclassical regime \((M,g_{ab},\rho,\mathcal H_{\mathrm{QFT}})\) such that (i) quantum predictions are Born probabilities on composed systems, (ii) causal/clock observables transform covariantly, (iii) \(g_{ab}\) satisfies the specified Einstein or effective gravitational equation to stated error \(O(\epsilon)\), (iv) proper-time observables reproduce special-relativistic and gravitational time dilation in the tested regime, and (v) the construction supplies at least one discriminator not already fixed by GR+QFT EFT.

Without a proof of T, the correct conclusion is “research programme with a bridge specification,” not “quantum gravity reconciled.”

### 5.2 Quantum obligations

| ID | Minimum axiom/lemma | Why it is required | Falsifier |
|---|---|---|---|
| Q1 | Each operational frame has a normalized state space and effects; probabilities are affine. | Gives empirical probabilities a typed domain. | No well-defined preparation/measurement equivalence classes. |
| Q2 | Composition is associative and physically specified; the relevant tensor/factorization or non-factorizing replacement is explicit. | Gravity makes naive factorization nontrivial. | Composition conflicts with gauge constraints or experiment. |
| Q3 | Reversible transformations and conditioning define a complex Hilbert/C*-algebraic (or explicitly alternative testable) quantum structure. | Required before amplitudes, phases, and QEC claims. | No reconstruction theorem or counterexample model satisfying assumptions with non-quantum statistics. |
| Q4 | Born rule follows from Q1--Q3 plus declared assumptions, or is an admitted law. | Prevents importing what the proposal claims to recover. | A competing probability assignment satisfies the premises and observed constraints. |
| Q5 | Measurement/record observables are relational and gauge-invariant. | A frame-local write cannot be a gauge artifact. | The proposed record changes under gauge/diffeomorphism redundancy. |
| Q6 | Semiclassical unitary dynamics has a declared domain or a controlled modification with testable nonunitary terms. | Needed for black-hole and GME claims. | Uncontrolled loss of normalization/unitarity in the declared regime. |

### 5.3 Gravitational obligations

| ID | Minimum axiom/lemma | Why it is required | Falsifier |
|---|---|---|---|
| G1 | A coarse-graining map \(\Phi_\epsilon\) yields a Lorentzian manifold or an explicit replacement with causal observables. | A graph/order alone is not spacetime. | No continuum regime with stable causal/metric observables. |
| G2 | The map identifies a metric/connection and specifies its transformation law. | Required for meaningful redshift and proper time. | Coordinate/frame dependent predictions where gauge-invariant ones are required. |
| G3 | `change-load` maps to a symmetric source \(T_{ab}^{(\mathrm{eff})}\) or another named gravitational source, with units and conservation equation. | Converts metaphorical load into physical dynamics. | \(\nabla^aT_{ab}^{(\mathrm{eff})}\neq0\) in a regime with claimed diffeomorphism invariance, absent an accounted exchange term. |
| G4 | Field equation: \(G_{ab}+\Lambda g_{ab}=8\pi G T_{ab}^{(\mathrm{eff})}+\Delta_{ab}(\epsilon)\), or a stated alternative. | Required to claim more than thermodynamic analogy. | Does not recover tested weak-field/GR regime as \(\epsilon\to0\). |
| G5 | Universality/equivalence principle and local Lorentz invariance are proved or parameterized. | Information-specific couplings are otherwise heavily constrained. | Existing bounds exclude the stated parameter region. |
| G6 | Proper time is defined operationally and yields \(d\tau^2=-g_{ab}dx^a dx^b/c^2\) (or a measured alternative). | This is the missing bridge from “one budget” to dilation. | Wrong Lorentz factor, gravitational redshift, Shapiro delay, PPN parameter, or clock comparison. |
| G7 | Entropy/area and black-hole regime are derived or scoped out. | Thermodynamic/holographic language otherwise has no gravitational closure. | Generalized-second-law or semiclassical black-hole inconsistency in stated domain. |
| G8 | The construction identifies how Weinberg--Witten and gauge-observable assumptions are avoided or satisfied. | No-go constraints apply to vague emergent-gravity claims. | The model meets all no-go premises yet asserts forbidden emergent graviton properties. |

### 5.4 Bridge sequence and dependency order

1. **Choose a realization.** Specify \(\mathfrak S\): state space, dynamics, composition, and frame transformations. A prose-level relational substrate is insufficient.
2. **Close Q1--Q6.** State whether Born weights are assumed or derived. If Q4 relies on 01d's contingent premises, list those premises rather than calling the result forced.
3. **Define relational observables.** Construct \(\mathcal O\) and demonstrate gauge invariance before treating a frame update as physical.
4. **Construct \(\Phi_\epsilon\).** Prove continuum/causal recovery and quantify approximation errors. Causal-set/Holographic machinery may inspire this step but cannot be cited as its proof.
5. **Identify the physical budget.** Give units, operational measurement, conservation law, and coupling to matter; decide whether it is energy, modular energy, entropy production, or something new. If it is new, derive its relation to measured \(T_{ab}\).
6. **Derive dynamics.** Obtain G4 and G5, then calculate—not name—kinematic and gravitational clock observables required by G6.
7. **Test the overlap.** Recover QFT-on-curved-spacetime/EFT results and GR tests where both presently work.
8. **Supply a novel discriminator.** State an observable, parameter/range, apparatus or astronomical measurement, comparison theory, and outcome that would rule out the new bridge.

This order prevents circularity: entanglement/thermodynamic derivations generally take quantum state structure and some spacetime causal structure as input; they cannot by themselves simultaneously establish both.

### 5.5 Minimal formal bridge for each repository claim

| Repository claim | Minimum bridge needed for a reconciliation claim |
|---|---|
| Relational-information substrate | A functor/interpretation from typed relations and admissible updates to physical algebras/causal observables, preserving composition and predictions. |
| Frame-relative realization | A covariant relational-instrument model: completely positive/instrument-like updates on gauge-invariant record observables, plus transformation law between frames. |
| Change-load/budget | A dimensioned, locally defined current/tensor and a theorem relating it to \(T_{ab}\), modular energy, or an alternative gravitational source with conservation. |
| One account of velocity + gravity dilation | A recovered metric and proper-time functional giving both Lorentz time dilation and gravitational redshift from the same defined source/dynamics. |
| Born-recovery relationship | A noncircular quantum reconstruction and composition theorem, or an explicit admission of Born/Hilbert axioms followed by a gravitational derivation that does not pretend otherwise. |
| Cross-modal generality | Explicit structure-preserving maps for each modality and separate validation; no physical conclusion transfers without a modality-specific empirical bridge. |

## 6. Falsifiable programme, not asserted solution

A future 01h draft earns a positive reconciliation claim only if it publishes all of the following:

1. **Model disclosure:** finite or otherwise well-defined state spaces, update rules, frame maps, composition, and coarse-graining; enough detail for independent calculation.
2. **Recovery suite:** derivations of the Born/statistical rule status, Lorentz covariance, equivalence-principle behavior, Newtonian/weak-field limit, gravitational and velocity time dilation, and a QFT/EFT overlap check.
3. **Constraint suite:** explicit treatment of Weinberg--Witten assumptions, gauge-invariant observables, conservation, and black-hole/entropy scope.
4. **Prediction suite:** at least one effect distinguishable from GR+standard QFT in a named domain; a null or contrary result must reject a stated parameterization or mechanism.
5. **Audit suite:** a table separating axioms, definitions, borrowed established results, derived lemmas, simulations, and hypotheses; every external result cited only for its demonstrated scope.

**Immediate falsifiers of the present programme direction.** The direction fails as a claimed *reconciliation* if: (a) no map from budget to a conserved physical source can be defined; (b) no quantum composition/Born bridge can be made noncircular; (c) any candidate continuum map fails local Lorentz/equivalence constraints; (d) its metric/proper-time prediction conflicts with established clock/GR tests; (e) all candidate realizations are observationally identical to GR+QFT EFT and make no further constrained claim; or (f) the argument requires a theorem's prohibited assumptions without identifying an evasion.

## 7. Bibliography-ready source ledger

The links below are direct DOI or arXiv records suitable for later verification. Exact bibliography style for a future formal paper should follow the repository's inline Natbib convention, not this Markdown list.

1. T. Jacobson, “Thermodynamics of spacetime: The Einstein equation of state,” *Physical Review Letters* **75**, 1260 (1995). [DOI](https://doi.org/10.1103/PhysRevLett.75.1260).
2. T. Jacobson, “Entanglement equilibrium and the Einstein equation,” *Physical Review Letters* **116**, 201101 (2016). [DOI](https://doi.org/10.1103/PhysRevLett.116.201101).
3. P. Bueno, V. S. Min, A. J. Speranza, M. R. Visser, “Entanglement equilibrium for higher order gravity,” *Physical Review D* **95**, 046003 (2017). [DOI](https://doi.org/10.1103/PhysRevD.95.046003).
4. H. Casini, M. Huerta, R. C. Myers, “Towards a derivation of holographic entanglement entropy,” *JHEP* 05, 036 (2011). [arXiv](https://arxiv.org/abs/1102.0440).
5. N. Lashkari, M. B. McDermott, M. Van Raamsdonk, “Gravitational dynamics from entanglement ‘thermodynamics’,” *JHEP* 04, 195 (2014). [arXiv](https://arxiv.org/abs/1308.3716).
6. T. Faulkner et al., “Gravitation from entanglement in holographic CFTs,” *JHEP* 03, 051 (2014). [arXiv](https://arxiv.org/abs/1312.7856).
7. E. Verlinde, “On the origin of gravity and the laws of Newton,” *JHEP* 04, 029 (2011). [arXiv](https://arxiv.org/abs/1001.0785).
8. E. Verlinde, “Emergent gravity and the dark universe,” *SciPost Physics* **2**, 016 (2017). [arXiv](https://arxiv.org/abs/1611.02269).
9. M. Milgrom, “Perspective on MOND emergence from Verlinde’s ‘emergent gravity’ and its recent test by weak lensing,” *Physical Review D* **96**, 084039 (2017). [arXiv](https://arxiv.org/abs/1612.09582).
10. F. Lelli, S. S. McGaugh, J. M. Schombert, M. S. Pawlowski, “Testing emergent gravity with isolated dwarf galaxies,” *Monthly Notices of the Royal Astronomical Society* **468**, L68 (2017). [arXiv](https://arxiv.org/abs/1706.00785).
11. J. M. Maldacena, “The large N limit of superconformal field theories and supergravity,” *Advances in Theoretical and Mathematical Physics* **2**, 231 (1998). [arXiv](https://arxiv.org/abs/hep-th/9711200).
12. S. Ryu and T. Takayanagi, “Holographic derivation of entanglement entropy from AdS/CFT,” *Physical Review Letters* **96**, 181602 (2006). [DOI](https://doi.org/10.1103/PhysRevLett.96.181602).
13. A. Almheiri, X. Dong, D. Harlow, “Bulk locality and quantum error correction in AdS/CFT,” *JHEP* 04, 163 (2015). [arXiv](https://arxiv.org/abs/1411.7041).
14. X. Dong, D. Harlow, A. C. Wall, “Reconstruction of bulk operators within the entanglement wedge in gauge-gravity duality,” *Physical Review Letters* **117**, 021601 (2016). [DOI](https://doi.org/10.1103/PhysRevLett.117.021601).
15. D. Harlow, “TASI lectures on the emergence of bulk physics in AdS/CFT,” *PoS TASI2017*, 002 (2018). [arXiv](https://arxiv.org/abs/1802.01040).
16. S.-i. Amari, *Information Geometry and Its Applications* (Springer, 2016). [DOI](https://doi.org/10.1007/978-4-431-55978-8).
17. N. Lashkari et al., “Canonical energy is quantum Fisher information,” *JHEP* 04, 153 (2016). [DOI](https://doi.org/10.1007/JHEP04(2016)153).
18. M. Van Raamsdonk, “Building up spacetime with quantum entanglement,” *General Relativity and Gravitation* **42**, 2323 (2010). [arXiv](https://arxiv.org/abs/1005.3035).
19. B. Swingle, “Entanglement renormalization and holography,” *Physical Review D* **86**, 065007 (2012). [DOI](https://doi.org/10.1103/PhysRevD.86.065007).
20. L. Bombelli, J. Lee, D. Meyer, R. D. Sorkin, “Space-time as a causal set,” *Physical Review Letters* **59**, 521 (1987). [DOI](https://doi.org/10.1103/PhysRevLett.59.521).
21. S. Surya, “The causal set approach to quantum gravity,” *Living Reviews in Relativity* **22**, 5 (2019). [DOI](https://doi.org/10.1007/s41114-019-0023-1).
22. D. P. Rideout and R. D. Sorkin, “Classical sequential growth dynamics for causal sets,” *Physical Review D* **61**, 024002 (1999). [DOI](https://doi.org/10.1103/PhysRevD.61.024002).
23. S. Bose et al., “Spin entanglement witness for quantum gravity,” *Physical Review Letters* **119**, 240401 (2017). [DOI](https://doi.org/10.1103/PhysRevLett.119.240401).
24. C. Marletto and V. Vedral, “Gravitationally induced entanglement between two massive particles is sufficient evidence of quantum effects in gravity,” *Physical Review Letters* **119**, 240402 (2017). [DOI](https://doi.org/10.1103/PhysRevLett.119.240402).
25. A. Belenchia et al., “Quantum superposition of massive objects and the quantization of gravity,” *Physical Review D* **98**, 126009 (2018). [DOI](https://doi.org/10.1103/PhysRevD.98.126009).
26. C. Rovelli and F. Vidotto, “Gravity entanglement, quantum reference systems, degrees of freedom,” *Physical Review D* **106**, 084040 (2022). [arXiv](https://arxiv.org/abs/2207.03138).
27. F. M. Howl et al., “Gravity mediated entanglement between light beams as a table-top test of quantum gravity,” *Quantum* **7**, 1166 (2023). [arXiv](https://arxiv.org/abs/2210.12713).
28. S. Weinberg and E. Witten, “Limits on massless particles,” *Physics Letters B* **96**, 59 (1980). [DOI](https://doi.org/10.1016/0370-2693(80)90610-3).
29. G. ’t Hooft and M. Veltman, “One-loop divergences in the theory of gravitation,” *Annals of Physics* **88**, 189 (1974). [DOI](https://doi.org/10.1016/0550-3213(74)90436-9).
30. J. F. Donoghue, “General relativity as an effective field theory,” *Physical Review D* **50**, 3874 (1994). [DOI](https://doi.org/10.1103/PhysRevD.50.3874).
31. W. Donnelly and S. B. Giddings, “Observables, gravitational dressing, and obstructions to locality and subsystems,” *Physical Review D* **94**, 104038 (2016). [DOI](https://doi.org/10.1103/PhysRevD.94.104038).
32. C. M. Will, “The confrontation between general relativity and experiment,” *Living Reviews in Relativity* **17**, 4 (2014). [DOI](https://doi.org/10.12942/lrr-2014-4).
33. A. Almheiri et al., “The entropy of bulk quantum fields and the entanglement wedge of an evaporating black hole,” *JHEP* 12, 063 (2020). [arXiv](https://arxiv.org/abs/2006.06872).

## 8. Stage-1 conclusion

The literature supports a programme of explicit bridges, not an asserted unification. The strongest usable neighbouring results are conditional: thermodynamic/entanglement arguments can reproduce gravitational equations given geometric and quantum input; holography and QEC give exact encoding/reconstruction structures in restricted dual settings; causal sets provide a concrete relational discrete target; and GME proposals provide a potentially discriminating low-energy test of nonclassical mediation. None supplies the missing single model that turns the repository's information substrate, frame-relative realization, change budget, dilation claim, and conditional Born recovery into a jointly derived quantum-gravity theory.

A formal 01h should therefore be attempted only after a candidate realization is selected and evaluated against the Q/G ledger above. Its defensible title-level result would be conditional (“a specified realization satisfies / fails these bridges”), with explicit errors and falsifiers—not “information gravity solves quantum gravity.”
