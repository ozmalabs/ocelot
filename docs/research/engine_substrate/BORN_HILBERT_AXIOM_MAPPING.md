# Born and Hilbert from the substrate: an axiom-by-axiom mapping attempt

**Status: ATTEMPT, not a proof.** Dated 2026-08-27. This note checks, one axiom at a
time, whether the Graphic Equalisation substrate supplies the operational axioms from
which the informational reconstructions of quantum theory *derive* complex Hilbert space
and the Born rule. If the mapping holds, "Born + Hilbert" reduces to those cited theorems.
It does **not** here — the mapping is rated per axiom (SOLID / PLAUSIBLE / GAP), and the
residual is localised, not closed. Sizing follows the project rule: the components are the
cited theorems; the contribution is only the mapping, and it is partial.

The two reconstructions used:

- **Hardy (2001)**, *Quantum Theory From Five Reasonable Axioms* (arXiv:quant-ph/0101012).
  Five axioms; classical probability theory satisfies the first four and fails the fifth.
- **CDP (2011)** — Chiribella, D'Ariano, Perinotti, *Informational derivation of quantum
  theory*, Phys. Rev. A 84, 012311. Six principles single out quantum theory over real/
  quaternionic and classical.

Both live inside the **operational-probabilistic / generalized-probabilistic-theory
(OPT/GPT) framework**: states as vectors in a convex set, effects, transformations,
and a composition (tensor) rule. That framework is a *precondition* for either axiom set,
so the mapping has two levels.

---

## Level 0 — does the substrate instantiate an OPT at all?

Before any axiom applies, the graph substrate must be an OPT. The natural identification:

| OPT ingredient | substrate |
|---|---|
| state | a frame's **internal Narrative** — the vector of its current rule set |
| effect / measurement | a **cross-frame projection** — reading the Narrative in another rule set; outcomes are realised collapses |
| transformation | a **rule** (a write); the identity transformation is **free continuation** (empty rule set, no write) |
| convex mixture | a probabilistic **ensemble of realisations** |
| composition (tensor) | **subframe nesting** in a superframe |

This is a genre-match. It was originally the largest single caveat in this note; it is
**worked out in "Level 0, worked out" below** and now stands as *core-established, with only
technical GPT-hygiene conditions pending* — a real strengthening. Everything in Level 1 is
still conditional on that core, but the core is no longer a blank assertion.

---

## Level 1a — the Hardy five

**Axiom 1 (Probabilities).** Operational probabilities exist as limiting relative
frequencies over ensembles. *Substrate:* realisation is collapse, a local write; over an
ensemble of realisations from one Poss, outcome frequencies exist and are the weights.
**Rating: SOLID** (modulo Level 0's ensemble/convexity assumption).

**Axiom 2 (Simplicity).** For a given number `N` of distinguishable states, the number of
degrees of freedom `K` takes the least value consistent with the other axioms (`K = N^r`,
`r` minimal). *Substrate:* the whole programme is MDL/Occam — the sd loop mints a quantum
only when the residual will not fit, the growth ladder is Occam-ordered, descriptions are
minimal by construction. "K minimal" is native. **Rating: PLAUSIBLE** — a genre-match
(the substrate prefers minimal descriptions) rather than a proof that the specific `K–N`
minimisation Hardy needs is the one the substrate enforces.

**Axiom 3 (Subspaces).** A system confined to an `M`-dimensional subspace of an `N`-state
system behaves exactly as an `M`-state system. *Substrate:* a **sub-frame is a frame**
(self-similarity, runner-recursion); foveated restriction to a subset of distinctions
behaves as a smaller frame (the aperture / `space_quantize` foveation). **Rating:
PLAUSIBLE** — the substrate has subframe-as-frame consistency; that it matches Hardy's
exact subspace closure is not shown.

**Axiom 4 (Composite systems).** `N_AB = N_A · N_B` and `K_AB = K_A · K_B`. The second
equality is **local tomography** — a composite state is fixed by local (product)
measurement statistics. *Substrate:* subframe nesting gives `N` multiplication for
independent subframes; `K` multiplication (local tomography) is the subtle one.
**This is the crux, and the concentrated residual.** Local tomography is precisely the
axiom that selects **complex** Hilbert space over **real** (real QM violates it) — so the
substrate must be shown to be local-tomographic, not real-QM-like. What the substrate has
in its favour: the **phase is genuine** (from "phase = position on the closure cycle,"
U(1) — a real-amplitude theory has no phase and no interference), so the substrate is
already committed to complex at the *single-system* level. What is **not** shown: that this
complex-ness propagates to composites as `K_AB = K_A K_B` rather than the real alternative
— i.e. that subframe composition preserves the phase structure jointly. **Rating: GAP
(the decisive one).** Note also the tension to watch: entanglement-as-a-superframe-dimension
must be the *local-tomographic* kind of global correlation (captured by joint local
statistics), not extra non-tomographic global information — complex QM is local-tomographic
*and* has entanglement, so there is no contradiction, but the substrate's composition has to
land on that side and that is unproven here.

**Axiom 5 (Continuity).** There is a **continuous reversible transformation between any two
pure states.** This is *the* quantum-selecting axiom: classical probability theory satisfies
1–4 and fails exactly this (classical pure states are discrete; no continuous reversible
path between them), and it is what forces `K = N²` (quantum) over `K = N` (classical).
*Substrate:* **free continuation.** A free continuation is a **no-write**, hence reversible
(a write is the only irreversible operation); and it is **continuous** — the phase is
position on the cycle, a continuous U(1), so free evolution continuously rotates the
Narrative-vector between pure states. The substrate's most native object — persistence as
the free default — *is* Hardy's continuous reversible transformation. **Rating: SOLID**,
and it is the crux axiom. This is the strongest single result of the mapping: the substrate
supplies the very axiom that distinguishes quantum from classical, from its own first-law
(free continuation) machinery, with no added assumption.

**Hardy tally:** SOLID ×2 (Axioms 1 and 5 — including the quantum-selecting crux),
PLAUSIBLE ×2 (2, 3), GAP ×1 (4, local tomography / complex-vs-real).

---

## Level 1b — the CDP six (cross-check)

**Causality.** No signalling from the future; preparation marginals are independent of the
later measurement choice. *Substrate:* in-frame ordering; collapse is a local write; no
cross-frame write into the past (`prop:run-record`, delayed-choice without retrocausality).
**Rating: SOLID.**

**Perfect distinguishability.** Every state not completely mixed is perfectly
distinguishable from some other. *Substrate:* distinctions are first-class (Axiom −1: a
difference that makes a difference); a non-mixed state carries a distinction, hence is
distinguishable. **Rating: PLAUSIBLE.**

**Ideal compression.** Every source has a lossless minimal encoding, recoverable
reversibly. *Substrate:* native MDL/compression; the sd loop's minimal codebook.
**Rating: PLAUSIBLE→SOLID** (compression is a core commitment).

**Local distinguishability (local tomography).** Same content as Hardy Axiom 4, and the
**same GAP** — the complex-vs-real crux. **Rating: GAP.**

**Pure conditioning (atomicity).** An atomic measurement on a pure state leaves pure
conditional states. *Substrate:* collapse of a pure Narrative yields a definite (pure)
realised outcome. **Rating: PLAUSIBLE.**

**Purification.** Every state has a purification, essentially unique. *Substrate:*
**entanglement as a superframe dimension** — a mixed subframe state is the restriction of a
pure superframe state (`rem:mixed`/`sec:entanglement` in the physics paper). This is
*literally* purification. CDP identify purification as the most characteristically quantum
principle (it fails classically). **Rating: SOLID.**

**CDP tally:** SOLID ×2 (causality, purification — including CDP's quantum-crux),
PLAUSIBLE ×3, GAP ×1 (local tomography).

---

## The convergence, and the concentrated residual

Two independent reconstructions, two *different* "most quantum" axioms — Hardy's
**continuity** of reversible transformations, CDP's **purification** — and the substrate
supplies **each natively from a different one of its own principles**: continuity from
**free continuation** (the first law), purification from **entanglement-as-superframe**.
That two separate reconstructions' crux axioms are both already-present substrate structure
is the substantive positive finding.

Everything else rates PLAUSIBLE (probability, simplicity/compression, subspaces,
distinguishability, pure-conditioning) — genre-matches to native commitments, not proofs —
**except one axiom that is both non-trivial and unmet: local tomography** (Hardy 4 / CDP 4),
which is exactly the axiom that selects **complex** Hilbert space over real. The residual is
therefore *concentrated*, not diffuse:

1. **Level 0:** show the substrate instantiates an OPT (convex state space, effects,
   transformations, tensor) — the precondition, only sketched.
2. **Local tomography:** show subframe composition gives `K_AB = K_A K_B` (complex), i.e.
   that the single-system closure-phase propagates to composites — the complex-vs-real
   decider, and the one clear GAP.

If both are discharged, the PLAUSIBLE axioms would still need tightening from genre-match to
statement-match, and then Hardy's or CDP's theorem delivers complex Hilbert space and the
Born rule.

---

## What this note does and does not establish

- **Does:** locate the reconstruction axioms against substrate principles; show the two
  crux ("most quantum") axioms are supplied natively; reduce the open problem from "posit
  Hilbert + unitarity" to **two named, checkable items** (OPT-instantiation and local
  tomography) plus the tightening of the plausible axioms.
- **Does not:** prove any mapping rigorously; establish the OPT structure; decide complex
  vs real (that *is* the local-tomography GAP); or re-derive the reconstruction theorems
  (they are cited).
- **Honest headline:** the frontier is now **one GAP (local tomography) and one
  precondition (OPT-instantiation)**, with the distinctively-quantum axioms already met.
  That is the smallest and most localised the Born/Hilbert residual has been in this
  programme — and it is still open.

## The two-subframe calculation (attempted)

**Honest flag: this computes the *natural* substrate composition and reads off the
dimension; the result turns on that composition being the right reading of self-similarity,
which is argued, not forced. It is not an independent proof that the substrate is complex.**

Hardy's `K` (fiducial degrees of freedom, including normalisation) for a two-state system
(`N=2`) and its self-composite (`N=4`):

| theory | `K` at `N=2` | `K` at `N=4` | `K_A·K_B` | local tomography |
|---|---|---|---|---|
| classical | 2 | 4 | 4 | holds (but fails continuity) |
| real (rebit) | 3 | **10** | 9 | **FAILS** (10 > 9) |
| complex (qubit) | 4 | **16** | 16 | **holds** |
| quaternionic | 6 | 28 | 36 | fails |

Continuity (Hardy 5) excludes classical; **local tomography excludes real** — its composite
carries 10 parameters, one more than the 9 any product measurement can read. Complex is the
theory satisfying both. So the decisive number is the substrate composite's `K`: **16
(complex) or 10 (real)**.

**Single system.** The substrate's phase is position on the closure cycle, a continuous
`U(1)`; amplitudes are `(a_0,a_1) ∈ ℂ²`, quotiented by global phase (no-privilege) and norm
→ the Bloch **sphere**, `K = 4`. Not the real disk (`K = 3`, no phase), not the classical
segment (`K = 2`). **The substrate is already complex at one system** — the closure-phase is
the complex commitment, and this part is solid.

**Composite.** A superframe is a frame (self-similarity, runner-recursion), so its state is
the same object: a complex closure-phase directional Narrative over its outcome set. The
composite outcome set is the product `{00,01,10,11}` (`N_AB = N_A·N_B`), so the joint state
is `(a_{00},a_{01},a_{10},a_{11}) ∈ ℂ⁴`, quotiented by one global phase and norm →
`K_AB = N_AB² = 16 = 4·4 = K_A·K_B`. **Local tomography holds, and the substrate composite is
the complex qubit pair, not the rebit pair.**

**Why real is excluded, in substrate terms.** Real QM's extra global parameter (10 vs 9) is
the one a product measurement cannot see. It exists only if the composite amplitudes are
**real** — phase-less. But self-similarity says every frame, the superframe included, carries
the closure-phase. A real composite would be a superframe that is *not* a closure-phase frame
like its subframes: **real QM requires breaking self-similarity at composition.** The
substrate's self-similarity therefore selects complex over real.

**Honest residual.** Under the natural composition — superframe = complex closure-phase frame
over the product outcome set — the answer is unambiguous: `K_AB = 16`, complex,
local-tomographic. What is *not* forced from a lower primitive is that self-similarity **must**
be read this way rather than permitting a real or exotic composite; and Level 0 (that the
substrate is an OPT at all) still stands. So the local-tomography gap is **not closed, but it
now has a direction and a reason**: the substrate points at complex, and real would cost
self-similarity. The residual has shrunk from "which theory?" to the sharp, bounded question
**"does self-similarity force the composite to be a complex frame over product outcomes?"** —
plus the OPT precondition.

## Level 0, worked out

**Result: the core OPT structure is established from the substrate's own machinery; only
technical GPT-hygiene conditions remain. Rating: core SOLID, conditions pending.**

The key that makes Level 0 tractable is seeing what the OPT convex structure *is*. The
convexity of the state space and the **affinity** of effects are the **classical-probability
backbone** — total probability over ordered branchings — **distinct from, and prior to, the
quantum superposition linearity** that Level 1 worries about. Every probabilistic theory has
this backbone. The substrate has it by construction, because realisations carry weights,
compose in order, and depend only on the present.

Ingredient by ingredient:

- **Systems.** A system is a frame type (a subgraph with an outcome set). Solid.
- **States are well-defined equivalence classes.** A GPT state is an equivalence class of
  preparations with identical statistics — which requires that statistics depend only on the
  prepared state, not on how it was prepared (no preparation-memory, Markov). The substrate
  supplies exactly this: **history is optional and the present structure is what acts** (the
  momentum paper's first law — a Narrative carries only its current structure forward, and a
  delta is a write to *that*). Future statistics depend only on the current Narrative, so
  operational equivalence holds and states are well-defined. Solid, and native.
- **Convex state space.** The mixture `λP + (1−λ)Q` is the preparation "realise a
  `λ`-weighted coin; on one branch prepare `P`, on the other `Q`." The substrate has weighted
  realisations (collapse with a weight) and ordered composition, so this preparation exists
  and its statistics are the `λ`-mixture. The state space is closed under probabilistic
  mixture. Solid.
- **Affine effects (the crux).** An effect `e` gives an outcome probability. By total
  probability over the coin-branching,
  `e(λP + (1−λ)Q) = λ·e(P) + (1−λ)·e(Q)` — effects are affine on the convex state space. This
  is the law of total probability applied to ordered realisations, nothing quantum. Solid,
  and it is the classical backbone, *not* the superposition linearity of Level 1.
- **Transformations.** Rules (writes) map states to states and compose (ordered); free
  continuation (the empty rule set, a no-write) is the identity and is reversible. A
  transformation monoid with reversibles. Solid.
- **Composition.** Subframe nesting composes systems; a joint preparation lives over the
  product outcome set. *Existence* of composition is Level 0 and solid; whether it is the
  complex/local-tomographic one is the **contingent** Level-1 layer, handled above, not a
  Level-0 requirement.
- **Probabilities.** The pairing ⟨effect, state⟩ is the realisation weight, in `[0,1]`,
  normalised over a complete measurement. Solid.

So the substrate **is** an operational-probabilistic theory at the core: convex states, affine
effects, a transformation monoid with reversibles, composition, and normalised probabilities —
each supplied by the substrate's weighted, ordered realisations and its history-optional,
present-structure-acts first law, resting on the classical total-probability backbone rather
than on any quantum assumption.

**Honest residuals (technical, not core):** finite/tomographic dimension (that a state is fixed
by finitely many fiducial effects — plausible for finite frames via the aperture, unproven in
general); topological hygiene (closed/compact convex state space); the full OPT
composition axioms (associativity of sequential and parallel composition, the interchange law
— should follow from the ordering and nesting of realisations, but each needs checking); and
the no-restriction/effect-realisability niceties. None of these is the "does it convex-linearise
at all" worry that Level 0 originally named; that worry is resolved. What remains is
GPT-hygiene, plausible for finite frames and not yet all proven.

**Two-layer picture this yields.** The substrate is a GPT *necessarily* (the classical
total-probability backbone, from realisation-with-weights + present-structure-acts); quantum
theory is the *contingent* GPT selected on top of it by the quantum axioms (complex closure-
phase, free-continuation continuity, entanglement-purification, self-similar composition).
Level 0 is the necessary layer; Level 1 is the contingent selection — cleanly separated.

## Correction: complex QM is contingent, not forced

The framing above — "does self-similarity **force** the complex composite?" as an open gap —
was a **misframing**, and the correction matters more than the calculation. **Self-similarity
is not required. Almost everything in a graph substrate is optional.** The compulsory core is
only structure, rules, subgraph-hood, and an admissibility grammar (`prop:minimal-universe`);
everything else — self-similarity, complex-over-real, `N=3`, the gauge group — is contingent
rule-content.

So the substrate does not, and should not, **force** complex quantum theory. It **admits**
complex QM as one admissible configuration (the self-similar complex composition), and our
universe's selection of it is **self-location**, exactly as with the number of spatial
dimensions or the gauge group. Real QM is another admissible configuration; the substrate
admits both and forces neither. Trying to force complex over real would **contradict the
framework's own stance** that it never forces contingent physics.

This dissolves the "local-tomography gap." It was never a gap to be closed by a forcing
argument — it is the **signature of a contingent selection**. The two-subframe calculation
above is then read correctly not as "the substrate proves complex" but as "**the admissible
complex configuration yields `K_AB = 16`; the admissible real one yields `10`; our universe is
the former, self-located**" — the same status as every other contingent constant in the
programme.

Given the contingent choice, the Born rule and Hilbert structure follow via the mapping and
the cited reconstructions — which is how the framework treats **all** physics: shapes follow
from contingent rule-content, the rule-content itself never forced.

## Overall status (corrected)

The Born/Hilbert result stands as: the substrate **admits** the structures from which quantum
theory follows — an OPT of Narratives/projections/continuations/nesting (Level 0, now
**core-established**: convex states, affine effects, composing transformations, composition,
from the substrate's weighted ordered realisations and history-optional first law; only
technical GPT-hygiene conditions pending), complex closure-phase amplitudes, free-continuation
continuity, entanglement-purification, and self-similar complex composition — and **complex QM
is the contingent, self-located selection among them**, not a forced consequence. The two distinctively-quantum axioms (continuity,
purification) are supplied natively; complex-at-one-system is solid; and given the contingent
composition, `K_AB = 16` (Born + complex Hilbert) follows.

What is **not** claimed: that the substrate forces QM (it forces almost nothing — that is the
point); nor that Level 0 is established (the OPT instantiation is sketched). What **is**
claimed: QM is an admissible, self-located configuration whose distinctive content the
substrate supplies natively and whose shapes then follow — the same honest status as `N=3` and
the gauge group, no stronger and no weaker.

**The precise verb: the framework *recovers* Born, it does not *derive* it per se.** Derivation
(per se) would force Born as a unique necessity from primitives; recovery reproduces the known
rule within the framework, given its admitted structures and contingent selections. That is
what happened: some steps are forced *given the premises* (the squared modulus, from
no-privilege + decohered additivity), while the premises themselves are admitted and contingent
(complex, linear, self-similar). Recovery is the honest verb and the correct one — a contingent
law can only be recovered given its rule-content, never derived as compelled. Every use of
"derive" for the overall Born rule in earlier drafts should be read as "recover."
