# Cognition Is Physics — an honest literature situating

**Purpose.** Situate the project's "cognition is the same process as physics, in a
different frame" unification against the established literature. The project's
standing rule is *understand and situate honestly, never overclaim novelty* — so
the goal here is to find where each piece is ALREADY established, name the key
references, and pin exactly what (if anything) is distinctive in the specific
combination. The short version, stated up front so nothing below reads as a
novelty pitch: **the core identity we re-derive is one of the most thoroughly
established results in 20th–21st-century mathematical science.** It has a 1984
image-restoration precedent that is almost line-for-line our "dissipation is
inference," a 2024 Physics Nobel, and a large active-inference / statistical-
physics-of-inference literature. We are re-deriving a known identity on a new
substrate, not discovering it.

---

## 1. The unification, stated precisely (no strawman)

The claim, as the project holds it, in four landed pieces:

1. **Dissipation IS inference (built + gated).** ONE integer relaxation dynamics
   — red–black (checkerboard) coordinate descent minimising
   `E = λ·Σ(xᵢ − obsᵢ)² + Σ_edges(xᵢ − x_j)²` — is, read one way, a second-law
   dissipative relaxation (a free-energy / Lyapunov functional monotonically
   decreasing to a fixed point, entropy up); and read another way — a *pure
   relabel of the identical trajectory* — MAP inference over a Gaussian /
   quadratic ("TV-L2"–style) Markov Random Field (denoising toward the closed-form
   MAP). The Gibbs energy IS the negative-log-posterior. A "break-one-breaks-both"
   falsifier was confirmed: making the update anti-dissipative (ascending E)
   destroys the perception. One process, two readings.

2. **Decay = the second law.** Implemented as an integer-exact half-life atom
   (`×2⁻ᵏ`, the `scale2` base-as-dimension generator). Holding structure against
   this decay = spending negentropy (Landauer). The substrate is therefore a
   dissipative structure / free-energy minimiser: it persists by continually
   paying to resist its own relaxation to the uniform state.

3. **The integer / frame ontology.** In-frame quantities are integers (reality,
   as observed, is stepped — sampling/quantisation is what grounding IS). The
   continuum lives ONLY in the cross-frame MAP (rotations by real angles, real
   ratios, π, Fourier, the continuous verdict metrics). "Randomness" is a
   *description* of data (Kolmogorov incompressibility), not a *process* — it is
   the coarse-grained residual of frame-local determinate dynamics, read from N
   frames above. The "global clock" is rejected: ticks are async and per-frame;
   determinism is in-frame; apparent randomness is cross-frame misalignment.

4. **The instantiation.** All of the above runs on a typed graph-rewrite
   substrate — `(G, Γ)`: a typed graph plus productions — whose settlement /
   `run_rules` fixpoint IS the physical relaxation. The agent is that relaxation.

The unification headline binding 1–4: *cognition and physics are the same
process; they differ only by which frame you read the trajectory in.*

---

## 2. Prior-art map — where each piece is already established

For each field: the key references and EXACTLY what it already establishes.
The consistent finding is that the **core identities are textbook-established**;
our pieces re-derive them.

### 2.1 Geman & Geman (1984) — the near-exact precedent for piece 1

Stuart Geman & Donald Geman, *"Stochastic Relaxation, Gibbs Distributions, and
the Bayesian Restoration of Images,"* IEEE TPAMI PAMI-6(6):721–741, 1984.
(<https://pubmed.ncbi.nlm.nih.gov/22499653/>)

This is the single closest prior art to "dissipation is inference," and it is 42
years old. Geman & Geman **explicitly** make the analogy between an image and a
statistical-mechanics system: pixel gray-levels and edges are "states of atoms
or molecules in a lattice-like physical system," the image prior is a Gibbs /
Markov-Random-Field distribution `P(x) ∝ exp(−E(x)/T)`, Bayesian restoration is
MAP inference over that field, and the inference is carried out by a **stochastic
relaxation** (the Gibbs sampler) with **simulated annealing** — literally cooling
a physical system to its minimum-energy (= maximum-posterior) state. Their
energy is our `E`; their MAP-by-relaxation is our MAP-by-coordinate-descent. The
only differences are (i) they anneal a stochastic sampler where we run a
deterministic (integer, red–black) descent to the mode, and (ii) they were doing
image restoration, not framing it as "cognition." **The identity
"physical relaxation over a Gibbs field = Bayesian image inference" is theirs, in
full, from 1984.** Our piece 1 is a re-derivation of Geman & Geman on the `(G, Γ)`
substrate.

Companion, exact on the deterministic side: TV-L2 / Rudin–Osher–Fatemi denoising
is MAP estimation under a smooth MRF prior whose convex energy is minimised by
**gradient descent = anisotropic-diffusion flow** — i.e. a physical diffusion IS
the MAP denoiser. (ROF 1992; Huber/TV gradient-descent-flow reviews,
<https://www.ipol.im/pub/art/2012/g-tvd/article_lr.pdf>.) Our quadratic energy is
the Gaussian-MRF special case of exactly this. Modern score-based **diffusion
models** are the same statement again — the score is `∇ log p`, and sampling is a
relaxation down the log-posterior (<https://fanpu.io/blog/2023/score-based-diffusion-models/>).

### 2.2 Jaynes / Gibbs = posterior; energy = −log p (the substrate of piece 1 & 2)

E. T. Jaynes, *"Information Theory and Statistical Mechanics,"* Phys. Rev. 106,
1957. Jaynes established that the Gibbs canonical distribution IS the
maximum-entropy posterior given mean-energy constraints, and that **statistical
mechanics is a special case of Bayesian/inferential reasoning** — "energy = −log
probability" and "Gibbs distribution = Bayesian posterior" are his. The modern
restatement is the **Gibbs posterior / energy-based-model** identity: choosing
the loss to be the negative log-likelihood recovers the Gibbs posterior
(<https://andrewcharlesjones.github.io/journal/ebms.html>). Our claim "the Gibbs
energy IS the negative-log-posterior" is this identity verbatim; we did not
invent it and should not imply we did.

### 2.3 Hopfield / Boltzmann — energy minimisation = memory/inference (2024 Nobel)

Hopfield (1982) associative memory and Hinton & Sejnowski's Boltzmann machine
(1985) are the canonical "same process, different frame": a physical
energy-minimising dynamics IS content-addressable memory / probabilistic
inference. This was recognised with the **2024 Nobel Prize in Physics** to
Hopfield and Hinton "for foundational discoveries … that enable machine learning
with artificial neural networks" — explicitly citing statistical physics as the
tool (<https://www.nobelprize.org/prizes/physics/2024/press-release/>). The
proposition "energy minimisation = inference/recall" is not merely established;
it is now Nobel-canonised. Our piece 1 sits squarely inside this tradition.

### 2.4 Free Energy Principle / active inference — the direct prior art for the headline

Karl Friston's Free Energy Principle (FEP) and active inference are THE most
direct prior art for "cognition = physics = inference = free-energy
minimisation." FEP holds that any self-organising system that maintains a
separation from its environment (a Markov blanket) resists disorder by
**minimising variational free energy** — a single quantity that is
simultaneously a thermodynamic-style free energy AND a variational bound on
Bayesian surprise. Perception minimises it by updating beliefs; action minimises
it by changing the world. (Friston 2010, *Nat. Rev. Neurosci.*; overview:
<https://direct.mit.edu/neco/article/36/5/963/119791/An-Overview-of-the-Free-Energy-Principle-and>;
tutorial: <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5341759/>.) This is our
headline claim — "cognition is a physical system minimising a free energy that is
also an inference objective" — stated as a general principle 15+ years ago, with
a large literature. **Any honest situating must lead with FEP:** our pieces 1–2
are a concrete, integer, graph-native instance of the FEP thesis, not a departure
from it.

Predictive coding is FEP's process theory: Rao & Ballard (1999) cortical
predictive coding, shown by Friston to be gradient descent on variational free
energy, and shown (Millidge et al.) to optimise the **same Bayesian objective as
Kalman filtering** in the linear-Gaussian case (strictly, PC ≈ but ≠ Kalman;
<https://arxiv.org/abs/2102.10021>, <https://arxiv.org/pdf/2107.12979>). "Neural
relaxation = filtering = physical relaxation minimising prediction error" is
fully worked out here.

### 2.5 Spin glasses ↔ optimisation/inference (piece 1, the hard/random case)

The statistical mechanics of inference and optimisation: Mézard & Montanari,
*Information, Physics, and Computation* (OUP, 2009,
<https://global.oup.com/academic/product/information-physics-and-computation-9780198570837>);
Zdeborová & Krzakala, *"Statistical physics of inference: thresholds and
algorithms,"* Adv. Phys. 2016 (<https://arxiv.org/pdf/1511.02476>); Parisi's spin-
glass work (2021 Physics Nobel). This field IS the mature science of "an
inference/optimisation problem is a physical system; its energy landscape,
phase transitions, and relaxation dynamics are literally those of a disordered
magnet." Belief propagation, the cavity method, and message passing are graph-
native relaxation algorithms over exactly the kind of factor graph our `(G, Γ)`
substrate is a typed instance of. Our piece 1 is the convex (Gaussian) corner of
this landscape; the field owns the general case.

### 2.6 Thermodynamics of computation / prediction (piece 2)

- **Landauer (1961) / Bennett (1982):** erasing a bit costs `kT ln 2`; logically
  irreversible computation dissipates. "Holding/erasing structure has a
  thermodynamic price" — our negentropy claim — is Landauer's.
- **Still, Sivak, Bell & Crooks, *"The Thermodynamics of Prediction,"* PRL 109,
  120604 (2012)** (<https://arxiv.org/abs/1203.3271>): a system coupled to a
  driving signal implicitly models it; **model inefficiency = thermodynamic
  dissipation**, and any maximally energy-efficient memory must be *predictive*.
  This is "dissipation is inference" as a theorem of stochastic thermodynamics.
- **England (2013), dissipation-driven adaptation:** driven matter self-organises
  toward states that dissipate more work — physics selects for adaptive
  structure without any inference module.
- **Wolpert, *"The stochastic thermodynamics of computation,"* J. Phys. A 52
  (2019)** (<https://arxiv.org/abs/1905.05669>): the modern, general framework
  tying computation to non-equilibrium statistical physics.

Together these establish piece 2 — decay/dissipation as the second law, holding
structure as spending negentropy, the substrate as a dissipative structure
(Prigogine) — as settled physics.

### 2.7 Information geometry (piece 1, the "relaxation is geometry" reading)

Amari, *"Natural Gradient Works Efficiently in Learning"* (1998): inference/
learning is descent on a Riemannian manifold whose metric is Fisher information;
the natural gradient is the "physical" steepest-descent relaxation on the
statistical manifold. This is the geometric face of "inference = relaxation."

### 2.8 The frame / discreteness pieces (piece 3)

- **Relational QM (Rovelli, 1996):** physical quantities are relative to a
  reference system; there is no observer-independent state, only relations
  between systems. This is the physics precedent for "quantities are in-frame;
  the state is frame-relative." (<https://philsci-archive.pitt.edu/18108/>)
- **'t Hooft, *The Cellular Automaton Interpretation of QM* (2014,
  <https://arxiv.org/pdf/1405.1548>):** the world is a deterministic discrete
  automaton; quantum indeterminacy is our coarse-grained description of an
  underlying determinate ontology. This is precisely piece 3's "determinism is
  in-frame; apparent randomness is cross-frame." (Superdeterminism is the
  contested part; the determinate-substrate-with-emergent-randomness thesis is
  the shared structure.)
- **Kolmogorov / Chaitin algorithmic information:** randomness = incompressibility
  = a *property of a description*, not a stochastic process. Our "randomness is a
  description not a process" is the algorithmic-information-theory definition of
  randomness, verbatim (<http://www.scholarpedia.org/article/Algorithmic_complexity>).
- **Digital physics / it-from-bit:** Wheeler ("it from bit"), Zuse, Wolfram
  (*A New Kind of Science*, 2002), Fredkin — reality as a discrete computational
  substrate. Our discrete-substrate framing lives in this lineage.
- **MDL / Rissanen:** the identifiability guard ("pin a continuous parameter only
  to observational resolution") is the Minimum Description Length principle.

### 2.9 Closest whole-package prior art — "physics itself is inference/learning"

Two lines go furthest toward the *entire* "physics and cognition are one process
differing by frame" package, and both predate us:

- **Ariel Caticha, Entropic Dynamics** (<https://arxiv.org/pdf/gr-qc/0109068>,
  and 2019 quantum version): the explicit thesis that *the laws of physics are
  laws of inference* — dynamics (including quantum mechanics and GR-like
  covariance) derived from maximum entropy on a statistical manifold. This is our
  headline "physics = inference" as a research programme in foundations of
  physics.
- **Vitaly Vanchurin, *The World as a Neural Network,* Entropy 22(11):1210
  (2020)** (<https://www.mdpi.com/1099-4300/22/11/1210>): the universe at its most
  fundamental level is a neural network whose *learning dynamics* reproduce both
  quantum mechanics and general relativity; he even states "first and second laws
  of learning" (entropy decreases during learning to equilibrium). This is
  "cognition/learning and physics are the same process" as a physics paper.

These two are the honest ceiling: the grand unification we are gesturing at has
already been proposed, in physics, by named authors. We are not first to
"physics = inference/learning."

---

## 3. Honest novelty assessment — what, if anything, is distinctive

Evaluated critically, discounting where not actually novel.

**(a) Frame-relativity of cognition/physics tied to no-global-clock / relational QM.**
*Mostly re-packaging.* The pieces exist separately and prominently: FEP already
says cognition is a physical free-energy relaxation; RQM already says physical
quantities are frame-relative with no global state; 't Hooft already says a
determinate discrete substrate looks random when coarse-grained. Binding "the
inference reading and the physics reading are the *same trajectory in different
frames*" into one sentence is a clean framing, and I found no single source that
states it in exactly those words — but each conjunct is established, and Caticha/
Vanchurin already assert the strong form ("physics IS inference/learning").
Verdict: a crisp synthesis, not a new claim. Do not call it novel.

**(b) Integer / discrete ontology — continuum only in the cross-frame map;
integer-exact `scale2` decay.**
*The most genuinely distinctive framing, and still with heavy precedent.* Digital
physics, 't Hooft's CA, and lattice statistical mechanics are all discrete; MRF
image models (Geman & Geman) are literally integer-lattice. What I did **not**
find stated elsewhere in this sharp form is the specific ontological *rule*:
"**in-frame quantities are integers; every real-valued/continuous quantity — π,
rotations, Fourier, the verdict metric — lives only in `Hom(frame, frame)`, never
in an object; continuity is intensional (a rule you apply) never an observed
datum.**" That is a usefully sharp discipline and I have not seen it drawn exactly
that way. But it is a *design discipline / bookkeeping stance*, not a new physical
or mathematical result — it is a particular, principled way of organising known
facts (discrete observation + continuous transformations). Verdict: distinctive as
a *stance*, not as a theorem; honestly, "sharp packaging of digital-physics + MDL."

**(c) The typed graph-rewrite `(G, Γ)` instantiation as the shared physical process.**
*Instantiation, not identity.* The identity (relaxation = inference) is old; doing
it as *typed graph rewriting with productions*, where the rule-engine fixpoint IS
the relaxation, is an unusual concrete substrate. But factor graphs + message
passing (Mézard–Montanari) already run inference-as-relaxation over graphs;
Geman & Geman already run it over a lattice graph; graph neural networks run
relaxation over typed graphs. The typed-production / rewrite-grammar flavour
(`Γ` as an admissibility grammar) is a real engineering distinctive, but it is a
*choice of machine*, not a new scientific claim. Verdict: a distinctive
implementation of a known identity.

**(d) The byte-identical, gated, break-one-breaks-both DEMONSTRATION as an artifact.**
*This is the most defensible distinctive contribution — and it is an artifact,
not a theory.* The literature above *proves* the identities analytically. What
the project adds is a *running, gated demonstration* in which the SAME integer
trajectory is exhibited under two readings (dissipation and MAP inference) with a
**byte-identical** trace, plus a **falsifier** (invert the dynamics → the
perception provably breaks) that ties the two readings together empirically
rather than by appeal to the math. That is pedagogically and engineering-wise
valuable, and I am not aware of a prior artifact that stages exactly this
equivalence as a break-one-breaks-both integer trace on a cognitive substrate.
But it must be reported for what it is: a *demonstration of a known theorem*, not
evidence of a new one. Its value is conviction and reuse, not discovery.

---

## 4. Honest verdict

**Our unification is a re-derivation of a well-established identity, delivered on a
distinctive substrate with a sharp ontological framing and a genuinely useful
gated artifact — it is not a new theoretical result, and must not be presented as
one.** The core claim "inference = free-energy minimisation = physical
relaxation; the Gibbs energy is the negative-log-posterior; a dissipative
relaxation over a Gibbs/MRF field IS Bayesian inference" is among the most
thoroughly established results in the field: it is Geman & Geman (1984) almost
line-for-line for the perception case, it is Jaynes for the Gibbs=posterior
substrate, it is Hopfield/Hinton (2024 Physics Nobel) for energy=inference, it is
Friston's Free Energy Principle for the cognition-is-physics headline, Still–
Sivak–Crooks for "dissipation is prediction," and Caticha/Vanchurin already
assert the strong "physics IS inference/learning" form. We are re-deriving, not
inventing — and the project's own standard demands we say exactly that.

Where the contribution actually is, stated without flattery: **(1)** a specific,
integer-exact, discrete-frame *ontological discipline* (in-frame is integer; the
continuum lives only in the cross-frame map; continuity is intensional) that
sharpens — but does not overturn — digital-physics + MDL; **(2)** the `(G, Γ)`
typed graph-rewrite *instantiation*, in which a single rule-engine fixpoint serves
as both the relaxation and the inference, an uncommon engineering realisation of
a common identity; and **(3)** a *byte-identical, break-one-breaks-both gated
artifact* that stages the relaxation ⇄ inference equivalence empirically on a
cognitive substrate. All three are contributions of *packaging, instantiation,
and demonstration*, not of the underlying science. The correct posture toward the
grand headline ("cognition is physics in a different frame") is the humble one:
it is true, it is important, and it was established by others — our job was to
build a substrate on which it is *manifestly, checkably* true, and to that narrow
end the artifact is real.
