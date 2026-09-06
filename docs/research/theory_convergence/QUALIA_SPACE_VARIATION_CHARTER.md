# The qualia space varies between agents in two ways — aperture and dimensionality — and their trade-off is a Pareto *shape*, not a point

**Status: CONCEPTUAL CHARTER.** This document states a theory of how the qualia
space (`seeds/qualia_space.json`, `domains/analogy_search.concept_signature`,
`domains/qualia_schema.py`) varies across agents, why, and what the substrate can
and cannot currently represent of it. It is *theory + substrate-mechanism*, not a
measured result. The one falsifiable prediction it makes — **compensation** — is
carved off into a separate pre-registered experiment
(`docs/research/psychology_affect/QUALIA_DIMENSION_COMPENSATION_PREREG.md`), and
nothing here should be read as an empirical claim until that experiment reports.

The charter is grounded against observed human tails, cited inline.

## 0. The two axes of variation (and why they are different)

An agent's qualia space is a set of typed felt AXES (the `QualiaDimension`
codebook), and on each axis a `quantum` / `half_width` that sets how finely the
axis is resolved. Two agents can therefore differ in two structurally distinct
ways:

- **APERTURE** — same axes, different *resolution / range* along them. Coarse
  quantum ⇒ few resolvable felt states on that axis; fine quantum ⇒ many. This is
  a difference of *degree on shared dimensions*.
- **DIMENSIONALITY** — a felt axis *present* in one agent and *absent* in another.
  Not "felt weakly" — the axis is not in the codebook, so `concept_signature`
  emits no coordinate on it and the agent is **dark** on it (the schema's
  `dark_when_unrelaxed` invariant). This is a difference of *which dimensions
  exist at all*.

These are the substrate's own two knobs, already present per-axis: the `quantum`/
`half_width` fields on a `QualiaDimension` (aperture) and the presence/absence of
the `QualiaDimension` node itself (dimensionality). The phenomenal family is
declared `closed: false` and **grown from residual** (the `sd_mint_quantum` /
`CapabilityAxis` discipline), so per-agent dimensionality is representable in
principle: an axis minted in one agent's disposition/qualia Mt and never minted in
another's.

## 1. The observed human tails (this is not idle theory)

**Aperture has a real, graded population tail.** *Emotional granularity /
differentiation* (Feldman Barrett, Gross, Christensen & Benvenuto 2001; Barrett
lab) is a continuum: high-granularity people resolve fine distinctions (anxious vs.
apprehensive vs. dread), low-granularity people collapse toward undifferentiated
valence ("just bad"). It develops nonlinearly (low in adolescence; Nook et al.
2018) and predicts health outcomes. **Alexithymia** is the low tail of that
aperture — reduced ability to *distinguish* emotions, and even to distinguish
*evaluations* (Nature Sci. Rep. 2023). In substrate terms: a coarse quantum on the
affect axes. *(Sources rephrased for compliance.)*

**Dimensionality has a real tail too, near-binary at its extreme.** *Aphantasia*:
~1% of people generate **no** voluntary visual imagery at all — an entire felt
dimension *absent*, not merely weak (Nature Sci. Rep. 2020 frames it explicitly as
*absence* of imagery, not lack of awareness of it). *Hyperphantasia* (~3%) is the
opposite extreme (Cell/TICS 2024). So the "a feeling others cannot have" case is
observed, at the rare tail.

**The two axes are entangled at the low corner.** *Hypophantasia* (weak imagery)
associates with **higher** alexithymia than *core* aphantasia (almost none)
(PubMed 2026): partial dimensional loss without full compensation leaves a
granularity deficit. So aperture and dimensionality are not cleanly orthogonal in
humans — a faithful model must be able to represent both the orthogonal
idealization *and* the observed entanglement.

## 2. The Pareto claim — *optimal is a SHAPE, not a point*

Under a bounded representational capacity, dimensionality and aperture **trade
off**: at fixed capacity, more axes ⇒ coarser aperture each; fewer axes ⇒ finer
aperture on those that remain. The set of configurations that are not dominated
(cannot gain resolution on one axis, or an extra axis, without paying elsewhere)
is a **frontier** — a Pareto *surface*.

The charter's commitment is deliberately the **weak, honest** form:

> There is no globally optimal qualia-space configuration. "Pareto-optimal" names
> the **frontier itself** — a shape, not a privileged point. Agents scatter
> **along** the frontier (different, equally-valid optima: a many-axis/coarse
> temperament vs. a few-axis/fine one are *both* Pareto-optimal, differently
> specialised) and **inside** it (dominated configurations — worse on both axes at
> once; the entangled hypophantasia+alexithymia low corner is an interior point,
> not a frontier point).

This is why human variation in feeling is **not a ladder** from worse to better.
It is position on a trade-off surface: a felt capacity gained is (on the frontier)
a felt capacity paid for. High emotional granularity and rich multi-modal imagery
are not "more evolved" — they are one corner of a frontier whose other corners
trade breadth of felt dimensions for depth of resolution on fewer.

Substrate realisation of the frontier: a bounded **quantum budget** across an
agent's axes — capacity ≈ Σ_axes (range / quantum) is bounded — so dropping an
axis frees budget the remaining axes' apertures can absorb (their quantum shrinks,
resolution rises). Moving *along* the frontier = re-allocating a fixed budget;
moving *toward* it = using budget that was being wasted; interior points = budget
mis-allocated or simply less of it.

## 3. Axes are MINTED in development — hence a tail that never mints one

The felt axes are not innate-fixed. The substrate mints them: `phenomenal:
sharpness` was minted (the bouba/kiki rung); the **phasic-arousal** axis was split
out of a collapsed tonic scalar (`PHASIC_AROUSAL_DIMENSION_PREREG.md`) — a
dimension the substrate had *half-computed* and only later separated. Minting is a
developmental event (residual that the held axes cannot cover becomes a new axis).

**Consequence (the developmental origin of the dimensionality tail):** if an axis
is minted during development, there is a tail of agents in whom, for a given axis,
**the mint never fired** — the developmental account of aphantasia-type absence
(which indeed runs in families and tracks imagery development; Cell/TICS 2024).
The absent-axis agent is not damaged; its development simply did not crystallise
that dimension.

## 4. The compensation hypothesis (the falsifiable core — carved off to an experiment)

The sharp, testable claim, and the reason claims §2–§3 are more than elegant:

> When an axis is absent, the **aperture of the remaining axes expands to *mostly*
> compensate.** The dimension-lacking agent is behaviourally near-normal on most
> discriminations — because most are *reconstructable* from correlated structure
> on the axes it *does* have (finer aperture there, funded by the freed budget) —
> and the deficit surfaces **only in the very specific circumstances** that require
> a discrimination **orthogonal** to every remaining axis. On exactly those, no
> aperture can help: aperture cannot manufacture a dimension.

This is the aphantasia clinical shape: aphantasics are largely functional
(verbal/spatial/semantic compensation) and fail specifically on tasks that
*genuinely require* imagery. And it predicts the §1 entanglement: *partial* loss
without full compensation (hypophantasia) leaves a residual granularity deficit
(the alexithymia association).

**The falsifier:** if expanding the remaining axes' aperture *recovers* the
orthogonal discrimination, the theory is wrong — aperture would be substituting for
a dimension, and dimensionality would be illusory. The theory predicts an
**aperture-invariant residual deficit** confined to the orthogonal case. This is
tested in `QUALIA_DIMENSION_COMPENSATION_PREREG.md`: three agents (full-dimension;
absent-axis + compensated apertures; absent-axis + uncompensated) on a battery of
(a) reconstructable discriminations and (b) a *genuinely orthogonal* discrimination
constructed so the missing axis is the only separator. Prediction: the compensated
agent matches the full agent on (a), and **both** absent-axis agents fail (b)
identically **at any aperture**.

## 5. What the substrate CAN and CANNOT currently represent (honest ledger)

**CAN, as-is:**
- Aperture variation: `quantum`/`half_width` per `QualiaDimension` — already the
  granularity knob; a coarse-quantum agent is a low-granularity/alexithymic read.
- Dimensionality *presence/absence* at the signature level: `concept_signature`
  only emits a coordinate on an axis that exists and is lit (`dark_when_unrelaxed`);
  an agent lacking the axis is genuinely dark on it and cannot discriminate along
  it — the aphantasia mechanism.
- Minting as a developmental event: the phenomenal family is open/grown-from-
  residual; phasic-arousal and sharpness are worked precedents.

**CANNOT yet, or UNVERIFIED (the gaps this charter flags, to be settled by the
compensation experiment's investigation, not assumed):**
- **Per-agent axis codebook.** Whether the `QualiaDimension` codebook is genuinely
  *per-agent* (agent A has an axis agent B lacks) vs. a single global seed shared
  by all agents. If global, per-agent dimensionality is not representable without a
  substrate change, and the experiment must build the per-agent codebook honestly
  (not hand-tag). **Unverified — gates the experiment.**
- **A quantum *budget* constraint.** The Pareto frontier requires that aperture and
  dimensionality trade off against a *bounded* capacity. The substrate has per-axis
  quantum but **no enforced budget** coupling them. The frontier is therefore a
  *conceptual* commitment the substrate does not yet mechanically enforce; an
  experiment can *impose* a budget and show the trade-off, but the substrate does
  not spontaneously produce one. **Not represented; conceptual only.**
- **Compensatory aperture expansion as a dynamic.** That a missing axis *causes*
  the remaining apertures to sharpen is a developmental dynamic the substrate does
  not currently run (there is no rule that reallocates freed budget). The
  experiment tests the *consequence* (compensated vs. uncompensated agents,
  configured by hand) — it does not claim the substrate *performs* the
  reallocation. **Consequence testable; the dynamic itself not represented.**

## 6. Summary

Two axes of qualia variation, both with observed human tails: **aperture**
(granularity ↔ alexithymia, graded; = quantum) and **dimensionality** (imagery
vividness ↔ aphantasia, near-binary at the rare tail; = axis present/absent). They
trade off on a **Pareto shape** — optimality is the frontier, not a point, so
variation in feeling is specialisation, not rank. Axes are **minted in
development**, which predicts a tail in whom a given axis never minted. The
falsifiable payoff is **compensation**: remaining apertures expand to mostly cover
the loss, leaving an **aperture-invariant residual deficit** only on
discriminations orthogonal to every surviving axis — the aphantasia shape. The
substrate represents aperture and axis-absence as-is; the *budget*, the *frontier*,
and the *compensatory dynamic* are conceptual commitments it does not yet
mechanically enforce, flagged here honestly and tested (as consequences, by
hand-configured agents) in the companion experiment.
