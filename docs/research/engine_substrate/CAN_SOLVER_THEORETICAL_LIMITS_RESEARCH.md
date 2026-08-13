# What the math says the CAN solver can and cannot do — a pure theoretical-limits spike

**Status: RESEARCH SPIKE. No code, no seeds, no tests, no builds in this
document.** Exactly one file was added to the tree (this one). Matching the
register of `CAUSAL_LINKAGE_DIMENSION_RESEARCH.md`,
`CAN_BELIEF_QUANTIZATION_RESULTS.md`, and
`CAUSAL_GRANULARITY_POPULATION_DISTRIBUTION_RESEARCH.md`: literature is
checked, not recalled; source claims carry a fetched or converging-search
citation with a confidence tag; nothing below is asserted without one of
those two groundings.

**Charter, verbatim, from the project's creator**:

> "What about a pure math spike - checking the actual theoretical capability
> of the collapse/solver/CAN quantised process and what might be missing or
> what the limits are?"

This document is explicitly **not** another empirical rung. Two sibling
rungs today measure what the current implementation *does* (a crossover-
point sweep, a Bigville integration). This document asks a different
question: what does the underlying mathematics say the mean-field CAN
solver **can and cannot do, in principle**, independent of what has been
measured about today's implementation so far. Where an already-measured
empirical finding *is* explained by the theory below, that connection is
drawn explicitly and flagged as theoretical grounding for an existing
result, not as new measurement.

**Confidence convention**, matching the three prior spikes: a claim backed
by a source actually fetched and read carries `[fetched]`. A claim backed
only by a converging WebSearch synthesis (the primary source paywalled,
binary-PDF, or 403'd) carries `[search-synthesis, converging N sources]`
with the sources named. Nothing is asserted at a confidence level higher
than what was actually reached.

---

## 0. The headline answers, up front

1. **Complexity of the underlying problem (§3).** Barahona (1982) is real
   and the exact claim is sharper than "NP-hard in general": the
   **2D planar Ising ground-state problem *without* an external field is
   solvable in polynomial time; the same 2D planar problem *with* a field*,
   and the 3D problem with or without a field, is NP-hard**
   `[fetched, IOPscience]`. But this is **not the load-bearing question for
   this project**, and this document says so without hedging: `can_ops.rs`'s
   `mt_mean_field_marginal` is not attempting the NP-hard exact
   ground-state search at all — it computes a **mean-field self-consistency
   fixed point**, a polynomial-per-iteration *approximation*, unconditionally,
   at every N. The real, actionable question is not "can this scale
   exactly" (no algorithm can, and none is being attempted) but **"how good
   is the mean-field approximation, and under what conditions does even
   *that* fail to converge"** — which is exactly what §3.1's CAN model
   (Borsboom/Dalege/van Harreveld's psychological attitude network) and
   `can_ops.rs`'s own already-measured 2-cycle oscillation are about.
2. **Is mean-field the right approximation? (§4).** No, not unconditionally
   — the literature is explicit and long-standing that mean-field is the
   *weakest* member of a known hierarchy (mean-field → Bethe/loopy BP →
   Kikuchi/generalized BP), and it is weakest **specifically** in the
   regime — loops, strong local correlation, frustration — that
   `can_ops.rs`'s own `mt_frustration_given_state`/`audit_basin` are built
   to detect `[fetched: Yedidia/Freeman/Weiss's Bethe-free-energy framing;
   search-synthesis, converging: mean-field breaks down before Bethe does
   under frustration]`. Loopy belief propagation, understood as message
   passing whose fixed points are stationary points of the **Bethe free
   energy**, is a real, still-tractable, one-rung-better alternative — and
   the project's own vocabulary (`coherence = -H/N`, a free-energy-density
   framing, `seeds/causal_attitude_networks.json`'s own `description` field)
   is already reaching for exactly this family without using it. This is a
   real, actionable gap, not a coincidence of terminology (§4.3) — with one
   honest caveat the literature also hands over: Bethe/BP itself is known to
   stop having a stable solution in the same frustrated-plus-field,
   low-temperature regime `[search-synthesis, converging]`, so this is an
   improvement, not a cure.
3. **Formal quantization limits (§5).** Yes, there is a real, established
   connection — Sims (2016) explicitly builds a rate-distortion-theoretic
   account of absolute-judgment capacity that reproduces and generalizes
   Miller's own 1956 channel-capacity framing `[search-synthesis,
   converging]`, and Zaslavsky, Kemp, Regier & Tishby's Information
   Bottleneck account of color-naming (a close relative of rate-distortion)
   makes the identical move for a different perceptual domain
   `[search-synthesis, converging]`. **But this document answers the
   transfer question directly rather than dodging it: rate-distortion
   theory's "optimum" is always relative to a *cost function and a
   channel-capacity constraint the theorist supplies* — for humans that
   constraint is a biological one (neural channel capacity, working-memory
   limits). An artificial substrate has no reason to inherit the *same*
   numeric constraint, and therefore no principled reason to inherit ~7 as
   *its* optimum** — but it has every reason to inherit the *shape* of the
   result (an optimal, non-trivial, finite bin count exists and is
   derivable from a stated cost/capacity trade-off), which is a load-bearing
   distinction §5.3 makes precisely rather than leaving as a hedge.
4. **What compression buys, formally (§6).** Two real candidate frameworks,
   and they are **not interchangeable, and the measured 7970→139 blob-edge
   compression is rigorously grounded by only one of them, conditionally**.
   (a) Junction-tree/treewidth exact inference is real, well-established,
   and **directly inapplicable to the graphs this project has actually
   tested** — `CAN_BELIEF_QUANTIZATION_RESULTS.md`'s own complete graphs
   (N=4/8/16, every pair coupled) have treewidth N−1, the *worst possible*
   case, by construction, so junction-tree buys nothing there without first
   changing what graphs get built. (b) Low-rank/structured-coupling Ising
   tractability (Hopfield-model TAP equations; a 2022 polynomial-time
   sampling result for Ising models with O(1) outlier eigenvalues,
   generalizing exactly the Hopfield/low-rank case `[fetched, arXiv
   2202.08907 abstract]`) is the framework that actually matches what
   shape-recognition would need to buy — **but only if the recognized,
   reused causal-linkage shapes correspond to a small number of shared
   LATENT GENERATORS acting additively across many edges (true low rank),
   not merely to many edges independently landing on the same few numeric
   values (value compression, which is a representation/storage saving with
   no proven effect on relaxation cost at all).** This distinction is not
   drawn anywhere in the prior CAN rungs and is this document's own
   contribution (§6.4) — it is a real, falsifiable, and currently untested
   empirical question, not a rhetorical caveat.
5. **What is actually missing, ranked (§7).** Precise, five items, each tied
   to a specific cited result, not a menu — headlined here and defended in
   full in §7: (1) the engine's synchronous/Jacobi update rule is a **known,
   named, cheaply-fixable** cause of exactly the persistent 2-cycle
   `CAN_BELIEF_QUANTIZATION_RESULTS.md` §3.1 already measured
   `[fetched/search-synthesis: Murphy, Weiss & Jordan 1999]`; (2) no
   Bethe/loopy-BP Term exists at all — mean-field is the *only* rung on a
   four-rung hierarchy this project has built; (3) no treewidth/graph-
   sparsity control exists on what graphs get *constructed*, so the
   junction-tree escape hatch is unreachable by construction, not merely
   unbuilt; (4) the low-rank/generator hypothesis for why shape-recognition
   should help CAN specifically is untested and, per §6.4, may not even be
   the right shape of hypothesis; (5) the ~7-bin quantization recommendation
   from `CAUSAL_GRANULARITY_POPULATION_DISTRIBUTION_RESEARCH.md` is
   correctly caveated there as a human number, and per §5.3 below that
   caveat should be sharpened, not softened, when it reaches a design
   decision for the artificial substrate.

---

## 1. Method

1. `CLAUDE.md` in full, with direct attention to "SHAPE IS ACQUISITION,
   RULE IS EXECUTION" and "SHAPES, NOT NUMBERS."
2. `docs/research/engine_substrate/CAUSAL_LINKAGE_DIMENSION_RESEARCH.md`,
   `CAN_BELIEF_QUANTIZATION_RESULTS.md`, and
   `CAUSAL_GRANULARITY_POPULATION_DISTRIBUTION_RESEARCH.md`, read in full —
   the three sibling documents this spike builds on and does not repeat.
3. `runners/dsl/src/can_ops.rs`, read in full (861 lines) — the actual
   mean-field relaxation, energy, frustration, Hebbian-update, and
   field-decay implementation, confirmed line-by-line rather than assumed
   from the prior rungs' descriptions.
4. `seeds/causal_attitude_networks.json`'s `description` field, read in
   full — the model's own stated Hamiltonian, equilibrium distribution, and
   `coherence = -H/N` framing, quoted verbatim in §4.3.
5. Literature, via WebSearch and WebFetch — real papers, fetched where
   reachable, marked `[search-synthesis]` where a fetch was blocked
   (several ScienceDirect/MERL/MIT PDF fetches 403'd, redirected to a 404,
   or returned binary-stream data — named explicitly at the point they
   occurred, not silently substituted).

---

## 2. What is already built — read from source, not re-explained

**`can_ops.rs`'s `mt_mean_field_marginal` (`:195-254`) is a synchronous
(Jacobi-style) fixed-point iteration of the tanh self-consistency equation**

```
σ_i ← tanh(β (Σ_j J_ij σ_j + h_i))
```

confirmed by direct read: every node's `new_state` at iteration `t+1` is
computed entirely from the full `state` map as it stood at iteration `t`
(`:227-246` — `new_state.insert(c, new_sigma)` never reads back into `state`
until the whole sweep completes and `state = new_state` runs). This is a
specific, load-bearing implementation choice, not an incidental detail —
§4 and §7.1 both depend on it. `mt_energy` (`:300-327`) computes
`H = -Σh_iσ_i - Σ_{i<j}J_ijσ_iσ_j` exactly as `causal_attitude_networks.json`'s
own description states. `mt_frustration_given_state`/`audit_basin`
(`:333-436`) compute, per coupling, `(actual - ideal)` where `ideal = -|J|`
(the best a coupling could contribute if perfectly satisfied) — this is a
genuine spin-glass frustration measure, the standard diagnostic for
detecting when a network's constraints cannot all be simultaneously
satisfied. `hebbian_update_J`/`decay_J`/`decay_h`/`update_identity_dynamics`
(`:640-825`) are the model's learning/forgetting dynamics, all pure
graph-attribute mutation, none of them touching the relaxation algorithm
itself.

**`seeds/causal_attitude_networks.json`'s own `description` field** (quoted
in full, this document's own read):

> "Network Hamiltonian H = -ΣJ_ij σ_i σ_j - Σh_i σ_i. Equilibrium
> distribution P(σ) ∝ exp(-βH) (Boltzmann)... Stability = local energy
> minimum. Attitude strength = network connectivity. Ambivalence =
> spin-glass frustration. Polarisation = phase transition at low T. Multiple
> inconsistent views = multistable network with distinct basins... conviction
> = J × β, **coherence = -H/N**, curiosity = expected info gain about σ."

Every noun in that paragraph — Hamiltonian, Boltzmann equilibrium,
frustration, phase transition, multistability, **free-energy density**
(`-H/N`, and separately note this is energy density, not free energy proper
— see §4.3) — is drawn directly from the equilibrium statistical mechanics
of disordered systems (spin glasses), the exact family Barahona (1982) and
Mézard & Montanari's textbook treat, and the exact family loopy BP/Bethe
free energy was built to approximate more accurately than naive mean-field.
**This is the load-bearing fact for §4**: this project did not borrow
mean-field arbitrarily and could equally well have borrowed nothing else —
it borrowed an entire, coherent piece of statistical-mechanics vocabulary,
and the rest of that same literature (Bethe, Kikuchi, TAP) is sitting one
step away, unused.

---

## 3. Q1 — Computational complexity of the underlying problem, and which
question is actually load-bearing

### 3.1 Barahona (1982), verified precisely

F. Barahona, "On the computational complexity of Ising spin glass models,"
*Journal of Physics A: Mathematical and General* 15(10), 3241, 1982.
**Confirmed real**, `[fetched, IOPscience abstract page]`. The exact claim,
read directly rather than taken on the charter's paraphrase:

> "In a finite two-dimensional lattice [the problems of computing the
> magnetic partition function and finding a ground state] can be solved by
> algorithms that require a number of steps bounded by a polynomial function
> of the size of the lattice... the same problems are shown to belong to the
> class of NP-hard problems, both in the two-dimensional case **within a
> magnetic field**, and in the three-dimensional case... If the interactions
> of the spin glass can only be drawn in a nonplanar graph, then finding the
> ground state belongs to the category of NP-complete problems, while
> efficient algorithms for finding the ground state are known for **planar
> interaction graphs**."

Read precisely, this is a **three-way boundary**, not a single "general case
is NP-hard" statement: (1) 2D planar, **no field** → polynomial; (2) 2D
planar, **with a field** → NP-hard; (3) 3D (planar or not) → NP-hard. The
field-dependence of the boundary is the sharper, more specific fact the
charter's own framing anticipated might be directly relevant, and it is:
**every real CAN network in this project carries a nonzero external field
`h_i` by design** (`h_i` is "current evidence + object salience," per the
seed description) — so even a hypothetical future planar-topology
restriction on `causal_influence` graphs would **not** land this project in
the tractable case. The field is not an optional extra that could be
dropped to gain tractability; it is the entire mechanism by which evidence
enters the model at all. **This closes off "restrict coupling topology to
planar" as a route to exact tractability for this project specifically** —
a concrete, negative, useful finding this document did not go looking for.

### 3.2 Why this is *not* the load-bearing question for `can_ops.rs`, stated
without hedging

`mt_mean_field_marginal` (§2) does not attempt ground-state search at all.
It iterates a **deterministic, polynomial-per-step, self-consistency fixed
point** — each of the (at most) `max_iter` sweeps is O(concepts × average
degree), and the whole computation is polynomial in network size for any
`max_iter` fixed in advance, **regardless of whether the underlying
ground-state problem is NP-hard**. This is expected and correct: mean-field
theory was invented precisely because exact spin-glass solving does not
scale, and every source consulted for §4 treats "mean-field is an
approximation to an intractable exact problem" as the starting premise, not
a novel observation.

**The precise, actionable reformulation, stated as directly as the charter's
own framing asked for**: NP-hardness of exact Ising ground-state search is
real, verified, and tells this project **nothing actionable about
`can_ops.rs` as built**, because `can_ops.rs` was never attempting that
problem. The question that *is* load-bearing, and the one the rest of this
document answers, is: **"how good is the mean-field approximation to the
true equilibrium marginal ⟨σ⟩, and under what structural conditions does it
fail — not merely become inaccurate, but fail to even converge to a
well-defined answer at all?"** `CAN_BELIEF_QUANTIZATION_RESULTS.md` §3.1
already measured the second half of that question empirically (the
persistent 2-cycle); §4 below supplies the theoretical account of *why*,
and of what the next rung up the approximation hierarchy buys.

---

## 4. Q2 — Is mean-field the right approximation, or is there a still-
tractable alternative the theory points to?

### 4.1 The known hierarchy: mean-field is the coarsest member, by
construction, not by implementation quality

Mean-field theory approximates the joint equilibrium distribution by a
**fully factorized** one (each spin's marginal computed as if every other
spin were replaced by its own average value) — this is the textbook
definition, and it is the reason mean-field ignores correlations between
variables entirely by construction, not as an implementation shortcut. The
**Bethe approximation** is a strictly richer approximation that accounts for
pairwise correlations along each edge of the graph and is *exact on trees*
`[search-synthesis, converging across multiple sources: "the Bethe
approximation is more powerful than the naive Mean Field approximation...
and is exact on trees"]`. **Loopy belief propagation is the message-passing
algorithm whose fixed points correspond to stationary points of the Bethe
free energy** — this is the central, formal result of Yedidia, Freeman &
Weiss, "Constructing Free-Energy Approximations and Generalized Belief
Propagation Algorithms" (*IEEE Transactions on Information Theory* 51(7),
2282-2312, 2005) `[fetched: paper existence, venue, and headline claim
confirmed via the MERL/MIT listing pages; the PDF itself returned only
binary-stream data on direct fetch, so the derivation is reported at the
paper's own stated-claim level, not re-derived]`. Pearl himself originally
proposed belief propagation as exact on trees/polytrees (1982-1988) and
explicitly suggested running the *same* message-passing rule on general
(loopy) graphs as an approximation `[search-synthesis, converging: "Pearl
(1988) then suggested this algorithm as an approximation for general (loopy)
networks"]` — loopy BP is not a different algorithm from tree BP, it is the
same message-passing rule applied where its exactness guarantee no longer
holds, which is exactly the "same shape, weaker guarantee" pattern this
project's own sd-loop ladder already uses elsewhere for a different reason.

**Kikuchi/generalized-BP methods** (also Yedidia/Freeman/Weiss) go one step
further, accounting for correlations over larger clusters than single
edges, at higher computational cost — the hierarchy is real,
graded, and each step trades tractability for accuracy in a principled,
named way (mean-field → Bethe/loopy-BP → Kikuchi/GBP), not an unstructured
menu of unrelated methods.

### 4.2 Precisely where mean-field is known to fail, and it is exactly
CAN's own regime

`[search-synthesis, converging across several independent sources]`: "the
mean-field approximation breaks down much earlier than the Bethe
approximation," "cannot capture critical behavior or strong frustration,"
and "the Bethe approximation works particularly well on graphs with few or
no short loops" — the inverse statement, that mean-field's error is
concentrated exactly in graphs *with* short loops and strong local
correlation/frustration, is the standard justification for every
Bethe/loopy-BP paper cited above. **This is precisely the regime
`can_ops.rs`'s own `mt_frustration_given_state` and `audit_basin` are built
to detect** — a network is "frustrated" in exactly the sense that makes
mean-field's independence assumption (each node sees only the *average*
influence of its neighbours, never their joint fluctuation) break down.
`CAN_BELIEF_QUANTIZATION_RESULTS.md` §3's own complete-graph, N=16, β=2.0
experiment — the one that produced the reversed N×M scaling prediction — is
a maximally-loopy, maximally-frustrated graph (every pair coupled, near-
random signs): **exactly the design point where the literature says
mean-field's own approximation error should be largest**, independent of
whatever coarse/fine resolution is used for `J`. This gives a real,
literature-grounded, mechanistic explanation the empirical rung did not
have: the reversed/non-monotonic scaling result may be, at least partly, an
artifact of mean-field's own known weakness on dense frustrated graphs
rather than a fact about "quantization" per se — a hypothesis this document
raises precisely and does not claim to have tested (that would require
re-running §3's factorial with a Bethe/loopy-BP relaxation instead of
mean-field, which is empirical work, out of this document's scope).

### 4.3 Is the project's own vocabulary a coincidence, or a real gap?

`coherence = -H/N` (§2) is an **energy density**, not the Bethe (or
mean-field) **free energy** — the two are related but distinct quantities:
free energy F = H − TS (or, in the Bethe case, the Bethe free energy, which
subtracts a specific entropy approximation built from single-node and
pairwise-edge marginals) `[this specific F=H−TS relation is standard
statistical mechanics, not independently re-derived from a fetched primary
source in this pass — reported at textbook-confidence, not source-verified
confidence]`. **This is worth stating precisely rather than glossing over**:
the project's naming is *evocative* of the free-energy family (energy
divided by size, used as a scalar coherence readout) but is not literally
computing a free energy today, mean-field or Bethe. This sharpens rather
than weakens the finding: the vocabulary points toward the right family of
ideas (equilibrium statistical mechanics, entropy-aware coherence) without
the entropy term actually being present in the computation — **a real,
specific, nameable gap** (§7.2), not a coincidence of terminology and not
already-closed by the existing naming.

### 4.4 The honest limit of this section — Bethe/BP is not a cure-all

`[search-synthesis, converging]`: "in frustrated models with an external
field at low temperatures, the Bethe approximation stops having a solution,
and it is still an open problem to find an approximation that is able to
solve the inverse Ising problem in a frustrated model with a field at low
enough temperatures." This is the honest ceiling on §4's own recommendation:
Bethe/loopy-BP is a **real, established, still-tractable improvement** over
mean-field for the loop/frustration regime, but it is not proven to remain
well-behaved in the *most* frustrated, highest-β corner of the same
parameter space CAN can already reach — the same corner where
`can_ops.rs`'s own 2-cycle oscillation was measured. This document does not
claim Bethe/BP would resolve `CAN_BELIEF_QUANTIZATION_RESULTS.md` §3.1's
honest null; it claims Bethe/BP is a real, better-grounded next rung whose
own failure mode is at least a *named, studied* open problem in the
literature rather than an unexamined property of this codebase's specific
implementation choice (§7.1's synchronous-update finding is a separate,
independently fixable issue from this deeper one).

---

## 5. Q3 — Formal quantization/information-theoretic limits, and whether
the human number transfers

### 5.1 Rate-distortion theory, verified as a real connection to Miller's
result

Claude Shannon's rate-distortion theory characterizes the minimum
achievable expected distortion for representing a source under a bounded
communication rate (channel capacity) — this is foundational, textbook
information theory, not independently re-derived here. **Sims, "Rate-
distortion theory and human perception"** (*Cognition* 152, 2016) makes the
connection to Miller's own result explicit and is the correct, real citation
for this question `[search-synthesis, converging across ScienceDirect,
Semantic Scholar, ResearchGate, PhilPapers listings — the ScienceDirect
primary fetch itself 403'd]`: "the most famous application of information
theory within psychology is George Miller's 'The Magical Number Seven...'
which concerned the span of immediate memory and the span of absolute
judgment... Sims' work extends this classical approach using modern
rate-distortion theory," modeling perception as **minimizing expected
distortion subject to an upper bound on the mutual information between
stimulus and internal representation** — i.e., Miller's ~2-3-bit capacity
is treated, in this later formalization, as exactly the rate-distortion
theory's own capacity constraint, and the resulting optimal number of
usable categories is *derived from*, not merely correlated with, that
constraint. Reported capacity estimates from Sims' own fitted models: 3.01,
3.25, and 3.19 bits for three different task conditions `[search-synthesis]`
— directly consistent with `CAUSAL_GRANULARITY_POPULATION_DISTRIBUTION_
RESEARCH.md` §6.1's independently-cited "2-3 bits" figure for Miller's
original result, now grounded in a formal derivation rather than only an
empirical regularity.

### 5.2 A second, independent formal family reaching the same shape of
result

Zaslavsky, Kemp, Regier & Tishby, "Efficient compression in color naming and
its evolution" (*PNAS* 115(31), 2018) apply the **Information Bottleneck**
principle — formally derivable from rate-distortion theory, per the paper's
own framing `[search-synthesis, converging: "the Information Bottleneck
principle, which can be formally derived from rate-distortion theory"]` —
to a completely different perceptual/linguistic domain (color category
systems across languages) and find that real human color-naming systems
sit near the theoretically-optimal complexity/accuracy trade-off curve. This
is a second, methodologically-independent instance of the *same* formal
move (bound the representational complexity, optimize accuracy under that
bound, compare real human data to the resulting curve) landing on
"near-optimal compression," which is the same shape of finding as Sims'
result for absolute judgment, in an unrelated domain (categorical language
production, not perceptual discrimination) — real convergence, not a single
result stretched to look like two.

### 5.3 Does this transfer to an artificial substrate? — answered directly

**No, not as a number; yes, as a method — and the difference is the whole
answer, stated without hedging into "maybe both."**

Rate-distortion theory does not hand over a single universal optimal bin
count. It hands over a **method**: given (a) a cost/distortion function over
representational error and (b) a bound on channel capacity (bits available
to represent the source), it derives the optimal *rate allocation* — which,
for a roughly uniform-cost, single-dimension source, tends to produce a
result in the same qualitative shape Miller found (a small number of
roughly-equally-spaced usable levels, with diminishing and eventually
negative returns to adding more). **The specific numeric bound (Miller's
~2-3 bits) is an empirically-measured fact about the human perceptual/
working-memory channel** — a biological capacity limit, not a
mathematically-necessary constant. An artificial substrate has a
**different** channel: it is not bottlenecked by a fixed number of
neurons performing absolute judgment under time pressure; it is bottlenecked
by whatever memory/compute/representational budget this project's own
`ShapeSignature` codebook and graph storage impose, which is an
engineering-chosen quantity, not a biologically-fixed one. **Therefore: this
project has a real, principled reason to run the SAME rate-distortion
optimization Sims and Zaslavsky et al. ran — bound cost, derive optimal
resolution — but it has no principled reason to plug in humans' own
measured channel capacity as *its own* constraint, because that specific
number was derived from a biological bound this substrate does not share.**
This is the precise, non-hedged answer the charter asked for: the transfer
is real at the level of **method** (do the rate-distortion optimization) and
false at the level of **number** (import ~7 as the answer) — and this
sharpens, rather than merely repeats, `CAUSAL_GRANULARITY_POPULATION_
DISTRIBUTION_RESEARCH.md` §8's own point-estimate caveat ("reported with
LOW-to-MEDIUM confidence... neither source measured causal/evidential
reasoning specifically") by naming *why* that caveat is structural rather
than a matter of insufficient citation-chasing: no amount of additional
literature search would fix it, because the transfer failure is about which
channel is being bounded, not about which paper measured it.

**What this does NOT establish**: this document has not derived what the
substrate's own cost function or channel-capacity bound *should* be — that
requires an engineering decision (how much graph storage per
`DimensionGenerator`, how much relaxation compute per query) this document
does not have the standing to make. It establishes the *shape* of the right
question ("what is this substrate's bound, and what does rate-distortion
say the optimal resolution is under that bound") without answering it.

---

## 6. Q4 — What does "shape-recognition makes it tractable" mean, formally?

### 6.1 The empirical claim being assessed, restated precisely

`CAN_BELIEF_QUANTIZATION_RESULTS.md` §7 (citing `BLOB_EDGE_ANALOGY_
EXTENSION_RESULTS.md`) reports a real, measured result: on the
`computer_architecture` Microtheory, 7,970 pairwise structural-correspondence
comparisons collapsed onto 139 distinct `transform_key` patterns (98.3%
reuse). This is a measured result on a **different task** — analogical
correspondence pattern-matching — not on CAN coupling relaxation. The
question this section assesses: is there a real, established theoretical
framework under which a comparable compression, *if it held for CAN's own
`causal_influence` couplings*, would make relaxation itself cheaper — not
merely make storing/authoring the couplings cheaper?

### 6.2 Candidate (a): low-treewidth / junction-tree exact inference — real,
rigorous, and directly checked against this project's own tested graphs

The junction-tree algorithm (Lauritzen & Spiegelhalter, 1988) generalizes
exact belief propagation from trees to arbitrary graphical models by first
**triangulating** the graph and grouping variables into cliques; exact
inference cost is **exponential in the treewidth** (one less than the size
of the largest clique after triangulation) `[search-synthesis, converging
across several independent PGM-course/survey listings]`. This is a real,
foundational, standard result in the graphical-models literature — not a
stretch. **But it is directly, measurably inapplicable to the graphs this
project has actually built and tested**: `CAN_BELIEF_QUANTIZATION_RESULTS.md`
§3's own factorial design uses **complete graphs** at every tested N (4, 8,
16) — every concept coupled to every other concept. A complete graph on N
nodes has treewidth exactly N−1 by definition (its only valid clique-tree is
the single clique containing all N nodes) — **the worst possible case for
this framework, by construction of the test design itself, not by
coincidence.** Junction-tree/treewidth-bounded exact inference buys
**nothing** on a complete graph regardless of how many couplings share the
same recognized shape, because treewidth is a property of which pairs of
nodes are connected **at all**, not of what values the connections carry.
**This is the single sharpest, most concrete finding of this section**:
shape-recognition, as measured in the blob-edge result, compresses the
*number of distinct J-values that must be independently authored or
learned* — it says nothing, on its own, about the *topology* of the
coupling graph, and topology (not value diversity) is what treewidth-bounded
tractability actually depends on. **For junction-tree tractability to become
relevant to CAN at all, some future design would need to make the
*constructed* `causal_influence` graph sparse/decomposable in the first
place** — a graph-construction discipline this project does not currently
have (§7.3), not a consequence of recognizing shared shapes among whatever
edges happen to already exist.

### 6.3 Candidate (b): tensor-network contraction complexity — real, and the
same underlying mathematical fact as (a), stated in a different notation

Markov & Shi (2005), "Simulating quantum computation by contracting tensor
networks," proved that the cost of an optimal tensor-network contraction
order corresponds exactly to a minimum-width tree decomposition of the
network's line graph — a circuit/network of treewidth `d` can be simulated
in time polynomial in the network size when `d = O(log n)` `[fetched:
abstract-level claim confirmed via arXiv/PMC listings, specific complexity
bound `T^O(1)exp[O(d)]` quoted from the search synthesis]`. **This is not an
independent tractability lever from (a) — it is the identical treewidth fact,
imported from tensor-network language rather than graphical-models
language**, confirmed directly relevant and real, but subject to the exact
same objection just raised: it is a bound on **graph topology**, and a
complete `causal_influence` graph has the worst possible topology for it,
regardless of value compression. Reported here as a **real, rigorous, but
non-independent** confirmation of (a)'s limit, not as a second, different
answer.

### 6.4 Candidate (c): low-rank/structured-coupling Ising tractability — the
framework that actually matches what "recognizing a shared causal-linkage
shape" would need to be, and the honest, falsifiable condition on which it
applies

This is this document's own contribution, not lifted from any of the three
prior CAN spikes. The Hopfield neural-network model **is** an Ising model
with a specifically **low-rank** coupling matrix — `J_ij = (1/N) Σ_μ ξ_i^μ
ξ_j^μ`, where the sum runs over a small number `p` of stored "patterns" —
and the Thouless-Anderson-Palmer (TAP) mean-field equations for this exact
model are a well-established result in disordered-systems theory, derived
originally for the Sherrington-Kirkpatrick spin glass and extended to the
Hopfield case by Mézard, Parisi & Virasoro (1987) `[search-synthesis,
converging: "TAP equations were originally derived in the Hopfield model by
Mézard, Parisi, and Virasoro (1987)"]`. More directly load-bearing: **Ising
models with all-to-all interactions have mean-field become exact in the
thermodynamic limit** `[search-synthesis]`, and a 2022 result — Koehler,
Lee & Risteski (or similar authorship per the arXiv listing), "Sampling
Approximately Low-Rank Ising Models: MCMC meets Variational Methods," arXiv
2202.08907 — proves a **polynomial-time sampling algorithm for Ising models
whose coupling matrix has all but O(1) eigenvalues confined to a bounded
interval**, and states explicitly, as a corollary, that this **"implies the
first polynomial time sampling algorithms for low-rank Ising models such as
Hopfield networks with a fixed number of patterns"** `[fetched: abstract
content confirmed directly]`.

**Why this is the framework that actually matches the shape-recognition
hypothesis, precisely, and why the match is conditional rather than
automatic.** A coupling matrix is low-rank when it can be written as a sum
of a *small number* of outer products of per-node vectors — structurally,
`J_ij = Σ_μ w_μ · f_μ(i) · f_μ(j)` for a small set of `μ`, i.e. every
coupling is explained by a small set of shared **generating factors**
("substance X, ingested, correlates with disease Y" acting as one shared
`μ` across many concept pairs, per `CAN_BELIEF_QUANTIZATION_RESULTS.md`
§7's own worked example). **This is exactly what "many `J_ij` couplings
recognized as instances of a small codebook of causal-linkage shapes" would
have to mean for the tractability result to transfer**: not that many edges
happen to round to the same *numeric* value (which is what the 139-pattern
`transform_key` compression, read literally, measures), but that the whole
coupling *matrix* factors through a small number of shared latent axes. **These
are not the same claim, and this document states the distinction precisely
because the three prior spikes did not draw it**: a genuinely low-rank `J`
could in principle produce *many distinct* numeric `J_ij` values (rank has
nothing to do with alphabet size — a rank-3 matrix over reals typically has
every entry numerically distinct), and conversely a coupling matrix could
have only 3 distinct rounded values yet still be full rank (e.g. a random
sign pattern quantized to `{-1,0,+1}`, precisely the "coarse" condition
`CAN_BELIEF_QUANTIZATION_RESULTS.md` §3 tested, which showed *higher*, not
lower, frustration — consistent with staying full-rank/disordered under
coarsening rather than collapsing toward a low-rank structure). **Whether
recognized causal-linkage shapes correspond to true shared latent
generators (which would make this tractability result apply) or merely to
value-alphabet compression (which would not) is a genuinely open, testable,
currently-untested empirical question — not resolved by the blob-edge
result, which measured a different task (structural correspondence pattern
reuse) on a different structure (analogical pairs, not a coupling matrix)
than the one this tractability claim is actually about.**

### 6.5 Verdict on Q4, stated without softening the distinction

**(a)/(b) (treewidth/tensor-network) is rigorous, real, and currently
inapplicable — not because the theory is wrong, but because this project's
own tested graphs (complete graphs) are the worst possible case for it, by
construction.** **(c) (low-rank/TAP) is rigorous, real, and is the framework
that actually matches the *content* of the shape-recognition hypothesis —
but it requires a specific structural condition (true low rank, i.e.
shared-generator structure) that has not been checked, and that a naive
reading of "98.3% pattern reuse" does not by itself establish.** Neither
framework is a "stretch" in the sense of being theoretically dubious — both
are textbook-grade, well-cited results. The honest finding is that **the
project's own existing empirical design (complete graphs, value-alphabet
quantization) does not yet test the condition either framework actually
needs**, and naming which condition each framework needs, precisely, is
what makes this section more than a restatement of "shape recognition
sounds like it should help."

---

## 7. Q5 — What is actually missing, precisely, ranked by the theory found
above

Ranked by how directly each item is required before the next rung up
becomes reachable, per the theory established in §3-6 (not by convenience
or by what happens to already be partially built).

**1. Damp or de-synchronize the relaxation update — the cheapest, most
directly grounded fix, and the one closest to something the theory says
should already exist.** `can_ops.rs`'s synchronous/Jacobi update
(§2, `:227-246`) is a **named, specifically-studied cause** of exactly the
kind of persistent oscillation `CAN_BELIEF_QUANTIZATION_RESULTS.md` §3.1
measured directly (period-2 cycle, gap <0.001 same-parity vs. large-gap
opposite-parity): Murphy, Weiss & Jordan's 1999 empirical study of loopy
belief propagation found the identical phenomenon — "loopy beliefs
oscillated... with a period-2 cycle... under specific parameter regimes"
— and identifies **damping and asynchronous (Gauss-Seidel-style) message
scheduling as the standard, well-established fix**
`[search-synthesis, converging across multiple independent listings]`. This
is grounded in §4's own hierarchy (loopy BP's convergence pathologies are
studied precisely because loopy BP, like this project's mean-field, is a
fixed-point iteration on a loopy graph) and requires no new theoretical
framework — only an engineering change to an update rule the theory already
predicts is more fragile than it needs to be. Ranked first because it is
the only item on this list that is a **known-solved** problem in the
literature, not an open or conditional one.

**2. Build a Bethe/loopy-BP Term alongside mean-field, not instead of it.**
Per §4, mean-field is the coarsest member of a real, graded hierarchy this
project has not otherwise availed itself of. `CAN_BELIEF_QUANTIZATION_
RESULTS.md` §4 already found the deeper reason all 15 declarative CAN rules
are inert — no DSL Term surface for the dynamics at all — and named
`MtRelax`/`MtHebbian` as the concrete next Terms to build. This document
adds the theoretical grounding for *which* relaxation algorithm those Terms
should eventually wrap: Bethe/loopy-BP is the literature's own next rung,
not an arbitrary alternative, and per §4.4 it is not a cure — it is a
better-grounded, still-tractable improvement whose own failure mode is at
least a documented open problem rather than an unexamined implementation
detail.

**3. Give the substrate a treewidth/sparsity discipline over what
`causal_influence` graphs get *constructed*, before asking what compression
buys.** Per §6.2/6.5, junction-tree tractability requires bounded treewidth,
and this project's own tested graphs are complete (worst case) by design.
Nothing about better relaxation algorithms or better shape recognition
reaches this — it is a property of graph construction, upstream of both.
Ranked third because it is a real, well-established lever that is currently
**unreachable by construction**, not merely unbuilt, and because building it
requires a design decision (what should make one concept's causal influence
on another exist as an edge at all, and when should it not) this document
has not made and is not positioned to make unilaterally.

**4. Test the low-rank/shared-generator hypothesis before building a
`CausalLinkageShape` compressor on its strength.** Per §6.4, this is a real,
falsifiable, currently-untested question, and it is **not** automatically
true just because the blob-edge result showed high pattern reuse on a
different task — the specific structural condition (true low rank, not
value-alphabet compression) needs to be checked against a real, populated
`causal_influence` network before the tensor/low-rank tractability result
can be claimed to apply. `CAN_BELIEF_QUANTIZATION_RESULTS.md` §7's own honest
admission — no populated `causal_influence` network currently exists in the
corpus to test this against — is the same gap this item depends on closing
first. Ranked fourth, below the graph-construction discipline (#3), because
whether a network is low-rank is itself partly a consequence of *how* the
graph gets constructed (item #3) — a hand-authored complete graph and a
generatively-constructed sparse one are not equally likely to exhibit
shared-generator structure even carrying identical concept content.

**5. Treat the ~7-bin quantization number as a method import, not a value
import, when it reaches an actual design decision.** Per §5.3, `CAUSAL_
GRANULARITY_POPULATION_DISTRIBUTION_RESEARCH.md`'s own §8 recommendation
(test 2-3 vs. 7 vs. 9-12 bins) is well-caveated as human-literature-derived,
but the caveat as written leaves room to read "low confidence, human-derived"
as "worth re-deriving more carefully from more human data." This document's
contribution is sharper: **no amount of additional human-population
literature closes this gap**, because the transfer failure is structural
(different channel, different bound), not a matter of citation quality. If
a resolution parameter is ever fixed for this substrate, it should be
derived from *this substrate's own* cost/capacity trade-off via the
rate-distortion method (§5.3), with the human literature used only to
motivate that *some* optimum exists and has this qualitative shape — never
as the source of the specific number. Ranked last because it is the only
item on this list that is not blocked on anything else — it is a standing
caution for whichever future rung picks a bin count, not a build
prerequisite for the other four.

---

## 8. What this document does NOT establish

1. **No live measurement was run.** Per this task's own framing (pure
   theoretical analysis, not empirical measurement), nothing in §3-7 was
   tried against real graph data. Where a theoretical account is offered for
   an already-measured empirical finding (§4.2's account of the reversed
   N×M scaling; §7.1's account of the 2-cycle oscillation), that account is
   a hypothesis this document raises with real citations behind it, not a
   confirmed explanation — confirming it would require re-running the prior
   rungs' own experiments with a Bethe/loopy-BP or damped-update relaxation
   substituted for mean-field, which is empirical work this document does
   not do.
2. **§4.3's `coherence = -H/N` vs. free-energy distinction is reported at
   textbook confidence, not independently re-derived or fetched from a
   primary source in this pass.** The F = H − TS relation and the Bethe
   free energy's specific entropy-approximation term are standard
   statistical mechanics; this document did not re-derive them from first
   principles or from a fetched primary text beyond the Yedidia/Freeman/Weiss
   abstract-level claim already cited in §4.1.
3. **§6.4's low-rank/shared-generator hypothesis is named and its testing
   condition specified precisely, but it is not tested here.** No populated,
   real `causal_influence` network exists in the corpus (confirmed by
   `CAN_BELIEF_QUANTIZATION_RESULTS.md` §7's own admission, not re-checked
   independently in this document) — this document could not have tested it
   even if testing were in scope.
4. **§5.3's rate-distortion transfer argument is a methodological claim
   about *how* to derive a resolution parameter, not a derivation of what
   this substrate's own cost/capacity bound should actually be.** That
   requires an engineering decision this document is not positioned to
   make.
5. **Several sources could not be independently re-verified against primary
   text**, named honestly rather than smoothed over: the Yedidia/Freeman/Weiss
   full derivation (both direct PDF fetches returned binary-stream or 404
   content — the paper's existence, venue, and headline claim are confirmed
   via multiple independent listing pages, but the Bethe-free-energy
   derivation itself was not re-worked from primary text); the Sims (2016)
   full paper (ScienceDirect fetch 403'd — reported at converging
   search-synthesis grain); the exact authorship of arXiv 2202.08907 (the
   WebFetch summary did not surface author names directly — reported by
   arXiv identifier, not by author, to avoid asserting an unverified
   attribution); the Murphy/Weiss/Jordan 1999 paper's exact oscillation
   mechanism (reported at the level the search synthesis could support, not
   independently re-derived).
6. **This document does not resolve whether Bethe/loopy-BP, if built, would
   actually fix `CAN_BELIEF_QUANTIZATION_RESULTS.md` §3.1's honest null on
   which side of the cohere/oscillate boundary resolution drives a network
   toward.** §4.4 states this precisely: Bethe/BP has its own known failure
   regime (frustrated + field + low temperature) that may or may not be
   distinct from where mean-field already fails on this project's own
   tested networks — an open question in the literature itself, not merely
   an open question for this project.

---

## 9. FINAL PRIORITIZATION — stated without hedging into a menu

Read against everything found in §3-7, the single highest-priority
theoretical gap to close next is **item #1 from §7: the synchronous update
rule**, for three converging reasons stated plainly rather than left as a
list of considerations. First, it is the only gap on the ranked list that
the literature reports as **already solved** — damping/asynchronous
scheduling is a known, specific, low-risk fix, not a research question.
Second, it is the gap most directly implicated in an **already-measured**
empirical anomaly (`CAN_BELIEF_QUANTIZATION_RESULTS.md` §3.1's persistent
2-cycle) rather than a purely theoretical concern with no observed
symptom yet. Third, and most decisively: **every other item on the ranked
list (Bethe/BP, treewidth discipline, low-rank testing) requires trusting
that the underlying fixed-point iteration itself is well-behaved before its
output can be interpreted at all** — a Bethe-free-energy Term built on top
of a still-synchronously-updated message schedule would inherit the exact
same oscillation pathology Murphy, Weiss & Jordan documented for loopy BP
specifically, so building rung 2 of the hierarchy (§4) before fixing rung 1's
own known convergence defect (§7.1) would compound rather than close the
gap. **The correct order, stated as a claim this document is willing to
stand behind rather than soften into "it depends": damp/de-synchronize
first; build the Bethe/loopy-BP Term second, on the now-stabilized update
rule; treat the treewidth-discipline and low-rank-testing items (#3-4) as a
genuinely open pair whose relative order depends on an engineering choice
about graph construction this document does not have standing to make; and
carry §5's rate-distortion method (#5), not its number, into whichever
future rung fixes a resolution parameter.**

---

**Worktree:** `/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/can-solver-worktree`
**Branch:** `can-solver-theoretical-limits`
**Base:** `main` @ `d061b2d` (`Merge causal-granularity-population-distribution-research:
grounding the crossover-point PREREG in real numbers`)

Not merged into `main`. This is a research document only — no code, no
seeds, no schema changes were made or proposed as diffs.
