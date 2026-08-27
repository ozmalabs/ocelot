# Recovering the Born rule from an information substrate

**An axiom-by-axiom note.** Matthew Parslow, 27 August 2026. Companion to *The Law of Graphic
Equalisation* (Theory; Physics Grounding; Mind and Self Grounding).

**Status: a draft attempt, not a peer-reviewed result.** Each step is rated (solid / plausible
/ gap); the residuals are named, not hidden. The honest verb throughout is *recover*, not
*derive* — see §2. This note is self-contained; the papers carry the surrounding framework.

---

## 1. The substrate, in one paragraph

Reality is modelled as typed graphs plus **admissibility rules** (a grammar of which edges may
exist). A **frame** is a subgraph that runs; its **state** is an internal "Narrative" — a
directional quantity over the frame's outcomes, carrying a magnitude and a **phase** that is
position on a **closure cycle** (a loop that a realisation must close), so amplitudes are
complex, `r·e^{iθ}`. A **realisation** is a collapse: a local write that picks one outcome from
the admissible set, with a weight. Realisations are strictly ordered (no in-frame concurrency).
Nothing is privileged: there is no god's-eye frame, and no privileged phase origin or
measurement basis. When no rule fires, a frame's Narrative simply carries forward — **free
continuation**, the reversible default; a rule (a write) is the only priced, irreversible step.
The invariant speed `c` is the frame's own change-throughput unit, `1` by construction. Frames
compose by **nesting** (a subframe in a superframe); a correlation invisible in each subframe is
a dimension of the superframe.

## 2. The claim, honestly sized

The substrate **recovers** the Born rule — reproduces it within its own structures, given its
admitted primitives and a contingent, self-located selection — rather than **deriving** it as a
forced necessity. Derivation-per-se would compel Born from primitives; the framework forces
almost nothing (that is the point of a graph substrate: the compulsory core is only structure,
rules, subgraph-hood, and an admissibility grammar — everything else is contingent rule-content,
as with the number of spatial dimensions or the gauge group). Every distinctively-quantum
ingredient is supplied by a substrate principle; the **cited reconstruction theorems**
(Gleason 1957; Hardy 2001; Chiribella–D'Ariano–Perinotti 2011) supply the uniqueness. The only
real claim is the **arrangement** — each component is individually known.

## 3. Level 0 — the substrate is an operational-probabilistic theory (core-established)

The convex/affine structure of an OPT is the **classical total-probability backbone**, distinct
from and prior to the quantum superposition linearity. The substrate has it by construction:

| OPT requirement | supplied by | rating |
|---|---|---|
| systems | frame types (subgraph + outcome set) | solid |
| states are well-defined equivalence classes | statistics depend only on the current Narrative (history-optional / present-structure-acts = Markov, no preparation-memory) | solid |
| convex state space | mixing two preparations via a weighted coin-realisation | solid |
| **affine effects** | total probability over the coin→prepare→measure branching: `e(λP+(1−λ)Q)=λe(P)+(1−λ)e(Q)` | solid |
| transformations (monoid, reversibles) | rules compose (ordered); free continuation = reversible identity | solid |
| composition | subframe nesting (existence; the complex-specific tomography is the contingent layer, §5) | solid |
| probabilities | realisation weights in `[0,1]`, normalised | solid |

**Residuals (technical GPT-hygiene, not the core):** finite/tomographic dimension (a state fixed
by finitely many fiducial effects — plausible for finite frames, unproven in general);
topological closure/compactness of the state space; the full composition axioms (associativity,
interchange); no-restriction/effect-realisability. None is the "does it convex-linearise at all"
worry, which is resolved.

## 4. The distinctively-quantum axioms, mapped

Two independent reconstructions; the substrate supplies each one's **most-quantum** axiom
natively, from a *different* principle.

- **Continuity of reversible transformations** (Hardy's quantum-selecting axiom; classical
  theory fails exactly this) ← **free continuation** is a no-write, hence reversible, and its
  phase is a continuous `U(1)`, so it moves continuously between pure states. **SOLID.**
- **Purification** (CDP's characteristically-quantum principle; fails classically) ← a mixed
  subframe state is the restriction of a pure superframe state — **entanglement as a larger-frame
  dimension**. **SOLID.**
- **Phase- and context-independence** ← **no privileged phase origin / no privileged frame**:
  probability is invariant under global phase and the same across measurement bases. **Earned.**
- Probability, simplicity/compression, subspaces, distinguishability, pure-conditioning ←
  native commitments (weighted realisations; minimum-description-length; subframe-as-frame).
  **Plausible** (genre-matches, not statement-matches).

**The squared modulus** is then *forced given* complex, linear amplitudes and no privileged
phase: decohered alternatives are classically exclusive, so their probabilities add, and
averaging the combined modulus over the relative phase,
`⟨f(|a·e^{iθ}+b|)⟩_θ = f(|a|)+f(|b|)` (the cross-term averages to zero), whose unique natural
solution is `f(x)∝x²`. Two supporting identifications: the **inner product** is the cross-frame
projection (one frame's Narrative read in another's basis); **unitarity** is that a free
continuation is a no-write (it preserves the Narrative and every projection of it).

## 5. Complex over real — contingent, not forced

For two two-state systems (Hardy's `K` = fiducial degrees of freedom incl. normalisation):

| theory | `K` single | `K` composite | `K_A·K_B` | local tomography |
|---|---|---|---|---|
| classical | 2 | 4 | 4 | holds (but fails continuity) |
| real (rebit) | 3 | 10 | 9 | **fails** (10 > 9) |
| complex (qubit) | 4 | 16 | 16 | **holds** |

The substrate is already complex at one system (the closure-phase gives the Bloch sphere,
`K=4`, not the real disk's `K=3`). A superframe, being a frame, is a complex closure-phase
Narrative over the product outcome set, giving `K_AB = 16` — local-tomographic, complex. But the
framework forces almost nothing: **complex-over-real is contingent rule-content, self-located**,
exactly as the number of spatial dimensions is. So local tomography is not a gap to be closed by
a forcing argument — it is the signature of a contingent selection, and a real-amplitude
composition (`K_AB=10`) is another admissible configuration. Our universe is the complex one,
self-located.

## 6. What this reconciles

On one substrate, quantum theory and relativity are not rivals: **collapse** is an in-frame
*event* (a local write, discrete), **relativity** a cross-frame *map* (continuous), joined at
`c`. Special and general relativity reconcile as one change-budget (with `c`-invariance a
theorem — that part is *proof*); the quantum–relativity reconciliation is *structural* (one
substrate, the event/map seam) with Born *recovered*. This is emphatically **not** a quantum
theory of gravity: no field is quantised, no metric derived, no dimensionless constant fixed.
What is reconciled is the *conflict*, at the level of shape.

## 7. Where I'd value your read

One specific question: **is the mapping sound, or where does it break?** The suspects I'd point
you at:

1. **Level 0 hygiene** — does "present-structure-acts" genuinely deliver operational equivalence
   (states as equivalence classes), and do the full OPT composition axioms hold under the
   ordering/nesting of realisations?
2. **The squaring argument** — is the phase-average uniqueness (`f∝x²`) tight enough, or does it
   need the full Gleason content?
3. **Composition** — under the natural reading the composite is local-tomographic (complex); is
   that reading forced, permitted, or wrong?

Honest boundaries restated: draft, not peer-reviewed; shape-level, not quantitative; the claim
is the arrangement; *recover*, not *derive*.
