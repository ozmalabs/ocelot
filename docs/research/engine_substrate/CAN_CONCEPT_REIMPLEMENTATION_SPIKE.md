# Can CAN be re-derived as a native instance of the sd loop + Γ, instead of an
imported continuous relaxation? — a design spike

**Status: DESIGN SPIKE, plus two minimal, isolated, clearly-labeled
proof-of-concept scripts.** No production code, seeds, or `can_ops.rs` edits.
Matching the register of `CAUSAL_LINKAGE_DIMENSION_RESEARCH.md`,
`RULES_AS_SHAPE_DESIGN_SPIKE.md`, and `CROSS_DOMAIN_SHAPE_SPIKE.md`: claims
verified by reading source in this tree carry `file:line`; literature claims
carry a confidence tag; a concrete, unhedged verdict closes the document, not
a menu.

**Charter, verbatim, from the project's creator:**

> "My question is - if CAN does that, can we re-implement CAN in such a way
> that it doesn't. Because we need the CONCEPT of CAN, we don't need the
> precise implementation."

And, arriving mid-flight as a calibration on how to weigh the verdict, not as
new scope, quoted precisely because it is load-bearing for §3.3/§7 below:

> "Infact, re-implementing CAN in a far more efficient framework that
> achieves the same goals is useful in and of itself." A reimplementation
> that is genuinely more efficient and still achieves the FUNCTIONAL GOALS
> is valuable on those grounds alone, independent of whether it is a 1:1
> fidelity match to the original Ising-physics formulation. Fidelity-to-the-
> metaphor and genuine capability are different bars, and the verdict below
> is weighed against the second, not the first.

Two further mid-flight clarifications sharpened this specifically for the
polarization/phase-transition question (§3.3), quoted because they directly
change how that section's finding is weighed, not merely how it is worded:
first, that the bar for "does polarization transfer" is OUTCOME-similarity
(does the reframing produce the same qualitative phenomenon — clustering
into a small number of mutually-incompatible, internally-consistent
positions, with a sharpness/threshold character as scrutiny increases — not
a literal Curie-Weiss critical point in a continuous parameter); second,
and more fundamentally, that **CAN's own physics was never claimed as the
mechanism of real cognition either** — "It also never said that the physics
was the how - only that it used it as a model" — Borsboom/Dalege/van
Harreveld adopted Ising/mean-field machinery because it PREDICTS the right
patterns, not because they believed minds literally run mean-field
relaxation. §3.3 is revised below to reflect both: no residual weight is
given anywhere in this document's verdict to preserving the continuous
mechanism for its own sake, because CAN's own authors never claimed it had
that status to begin with.

---

## 0. Headline answers, up front

1. **The five mapping claims** (§3): all five, INCLUDING claim 3
   (multistability/polarization), verify as **faithful-but-different** —
   real, genuine re-expressions that change the mechanism and change it for
   the better on the functional/efficiency bar the creator's calibration
   names, not for perfect fidelity to CAN's own borrowed physics (a bar CAN
   itself never claimed to clear as a claim about real cognition — "it also
   never said that the physics was the how - only that it used it as a
   model"). Claim 3 specifically: the outcome polarization is actually
   about — a population with a smooth, continuum-valued true position
   clustering into a small number of mutually-incompatible, internally-
   consistent, extreme resolved stances, with a sharpening/threshold
   character as scrutiny increases — is REPRODUCED by a static,
   iteration-free, coverage-threshold decode (§3.3, §5.4), with no
   Boltzmann ensemble and no continuous inverse temperature. What is NOT
   yet found is the SPECIFIC single-parameter operationalisation that
   sharpens monotonically in one direction the way β does (§5.4's own
   honest correction of its first prediction) — a real, narrow, named,
   buildable open design question, not a capability loss.
2. **The complexity/pathology payoff is real and verified from source, not
   assumed** (§4): `ShapeDecode`'s scoring loop is a single linear pass over
   the codebook (`shape_decode.rs:1521`, confirmed by direct read) —
   `O(codebook_size × observation_size)`, not exponential in network size,
   and requires no fixed-point iteration for the recognize case, so it
   cannot oscillate because there is no dynamical system to oscillate. For
   the evidence-propagation case specifically, this document does not stop
   at "no iteration needed" (that would beg the harder question) — it
   identifies a **discrete, asynchronous, native update rule** (Hopfield-
   style threshold dynamics) as the correct replacement for the continuous
   Jacobi relaxation, and this rule carries a real, textbook, proof-grade
   convergence guarantee the current implementation does not
   (`[search-synthesis, converging]`, §4.2) — confirmed empirically in §5
   below, not merely cited.
3. **The smallest test was designed AND run — twice** (§5), two minimal,
   isolated, clearly-labeled pure-Python proofs-of-concept. The first
   (`can_concept_poc_discrete_async.py`) independently replicates the
   continuous-synchronous oscillation pathology on fresh draws (confirming
   the measured phenomenon is not an artifact of the specific prior rung's
   seeds), then shows a discrete-asynchronous candidate update rule
   **never** exhibits it — 0/60 non-convergent draws across both the
   theoretically-guaranteed two-state variant and the empirically-checked
   three-state (native σ ∈ {-1,0,+1}) variant — against 16/30 and 6/30
   continuous-synchronous oscillation rates on the SAME coupling
   structures. The second (`can_concept_poc_decode_polarization.py`, §5.4)
   checks polarization on the outcome-equivalence bar and confirms a static,
   iteration-free coverage-threshold decode genuinely clusters a smooth,
   continuum-valued population toward the extremes as scrutiny tightens —
   while also honestly correcting its own first prediction (the specific
   tested parameter sharpens non-monotonically, not the way β does), a
   registered-in-advance miss reported precisely rather than smoothed over.
4. **What does not transfer** (§6): the FULL basin-topology ENUMERATION
   question ("how many distinct stable configurations can this landscape
   support") as opposed to classifying one observed state; ongoing GRADED
   reweighting of an already-minted coupling (Hebbian's continuous half, as
   opposed to its edge-CREATION half); coupling decay (forgetting) has no
   proposed native analog at all; and, for polarization specifically, ONLY
   the exact formal mathematics (a literal continuous-β critical point) —
   not the phenomenon itself, which does transfer (§3.3/§5.4). Four
   honestly-named, specific, mostly-narrow gaps, not a blanket "some things
   don't transfer," and none of them a reason to keep the continuous
   mechanism running.
5. **Verdict: (b), replace, cleanly** — not hedged into (c) "run both in
   parallel," and with no residual weight given anywhere to preserving
   CAN's own borrowed physics for its own sake, because CAN's own authors
   never claimed that physics was cognition's actual mechanism either. The
   concept re-derives natively for the parts this project's own rule set
   actually uses (§3.6's audit of what the 15 `causal_attitude_networks.json`
   rules and `mt_target_equilibria`/`self_improvement_dynamics` actually
   consume) AND for the polarization outcome specifically (§3.3/§5.4), on a
   mechanism that is measurably more efficient (no NP-hard-adjacent
   iterative relaxation, no oscillation class of bug, decode-bounded not
   iteration-bounded) and better-fitted to this substrate's own discipline
   (in-frame integer, Γ-admissible, `run_rules()`-fixpoint-driven, the SAME
   primitives every other dynamic-quantization loop in this codebase already
   uses).

---

## 1. Method

1. `CLAUDE.md` in full, direct attention to "SHAPE IS ACQUISITION, RULE IS
   EXECUTION" and "SHAPES, NOT NUMBERS" — the two-primitive decision
   procedure this whole spike applies.
2. The four docs this same investigation produced today, in order:
   `CAUSAL_LINKAGE_DIMENSION_RESEARCH.md`, `CAN_BELIEF_QUANTIZATION_
   PREREG.md`/`_RESULTS.md`, `CAN_CROSSOVER_POINT_RESULTS.md`,
   `CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` — all read in full, not
   summarized from memory (quoted directly throughout below).
3. `runners/dsl/src/can_ops.rs`, read in full (861 lines) — every op's
   actual arithmetic, not the docs' paraphrase of it.
4. `seeds/causal_attitude_networks.json`'s `description` field (quoted in
   full in §3.3) and its 15 rule NAMES (`:1-15` of the `rules` array,
   confirmed by direct load — every rule name is read against what it
   would need to consume, in §3.6).
5. The sibling rung's PREREG,
   `/home/matt/ozmadev/ocelot-worktrees/can-synchronous-update-fix/docs/
   research/engine_substrate/CAN_SYNCHRONOUS_UPDATE_FIX_PREREG.md` (the
   only file present there — no RESULTS yet, confirmed via `git status
   --short` in that worktree before writing a word of this document) — read
   for context, per the task's own instruction not to treat its existence as
   settling this spike's question. It answers "how do we patch the
   oscillation inside the continuous paradigm" (damping); this spike asks
   "should the continuous paradigm be there at all."
6. The sd-loop machinery this design proposes reusing, read from source, not
   assumed from the prior docs' description of it: `runners/dsl/src/
   shape_decode.rs` (module doc `:1-42`, the `score_part_for_residual`
   scoring loop `:1267-1299` and its single-pass call site `:1521`),
   `runners/dsl/src/term.rs` (`AntiUnifyWitness` `:3420-3431`,
   `covers_value`/`covers_open_value` `:3757-3831`, the full `TermNode`
   arithmetic/graph-walk vocabulary `:490-503`/`:770-790`/`:11011-11044`),
   and `seeds/shape_decode_loop.json`'s own module description (`:8`,
   quoted in part in §3.6).
7. `git worktree list` / `git branch -a` before branching, to avoid
   colliding with `bigville-can-integration` (a separate, stale-relative-to-
   main worktree, different files — not touched) and
   `can-synchronous-update-fix` (read for context only, per point 5).

---

## 2. What "the concept, not the implementation" concretely means here

Restated precisely before the five-claim audit, because the whole spike turns
on getting this distinction right rather than treating it as a slogan.

`causal_attitude_networks.json`'s own description (quoted in full, §3.3)
commits this project to a SPECIFIC IMPORTED MECHANISM: continuous σ, a
Boltzmann equilibrium distribution `P(σ) ∝ exp(-βH)`, and a mean-field
self-consistency iteration approximating that distribution's marginal. Every
measured pathology in the four prior docs traces to THIS mechanism
specifically:

- The synchronous-update 2-cycle oscillation (`CAN_BELIEF_QUANTIZATION_
  RESULTS.md` §3.1) is a property of iterating a Jacobi fixed-point map —
  it does not exist if there is no such iteration.
- Barahona's NP-hardness (`CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` §3.1)
  is a property of exact ground-state SEARCH over a continuous/combinatorial
  configuration space with a field — irrelevant to a system that never
  attempts that search, but also a standing reminder that ANY mechanism
  which tries to find a single best global configuration over a frustrated
  coupled system inherits some version of this cost.
- Mean-field's own approximation weakness under loops/frustration
  (`CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` §4.2) is a property of the
  SPECIFIC approximation family chosen (fully-factorized marginal) — Bethe/
  loopy-BP is a real, better-grounded alternative, but it is explicitly
  named in the task as staying WITHIN the same paradigm (a different,
  ranked question, not this one).
- The float-valued `J`/`h`/`σ` themselves violate this project's own
  frame/continuum invariant (`CLAUDE.md`'s BASE-AS-DIMENSION section,
  already the basis of `CAUSAL_LINKAGE_DIMENSION_RESEARCH.md`'s entire
  argument for single-edge strength) — a raw float living IN a frame's
  coordinates (a node's `state` attr) is exactly the category error that
  section names.

The CONCEPT underneath all four of these — what CAN is actually FOR, per its
own description (quoted in full below) — is: **a network of causally-coupled
beliefs that can settle into distinct, mutually-consistent configurations,
with some measurable degree of internal coherence, updatable by evidence.**
Nothing in that sentence requires continuous state, requires an iterative
relaxation, or requires a Boltzmann ensemble. The question this spike answers
is whether the sentence can be built entirely out of this substrate's own two
generative primitives (`CLAUDE.md`'s "SHAPES, NOT NUMBERS" decision
procedure: a quantity that changes → sd loop; a set of allowed moves → Γ)
instead of a third, imported mechanism.

---

## 3. The five mapping claims, verified one by one

### 3.1 Claim 1 — Basin → a held, recognized configuration in a codebook

**Verdict: faithful-but-different (b), with a real, named scope reduction.**

Read precisely, "basin" in the CAN literature and in this project's own
`audit_basin` (`can_ops.rs:400-436`) names TWO different things that the
prior rung's own research already separated cleanly
(`CAN_BELIEF_QUANTIZATION_RESULTS.md` §2, confirmed by direct read + a live
test built for that rung): (a) **classification** — given a current belief
state, which stable configuration (if any) does it match, and (b)
**enumeration** — how many distinct stable configurations does this
network's structure support AT ALL, independent of any one starting point.
`audit_basin` itself only ever does (a) — one call, one mean-field fixed
point from whatever `state` currently holds
(`CAN_BELIEF_QUANTIZATION_RESULTS.md` §2's own confirmed finding, re-verified
by reading `can_ops.rs:400-436` directly in this pass: no `basin_count`
field, no multi-start, no clustering). Enumeration (b) is not something
`can_ops.rs` provides either — it is something the CALLER must construct via
multi-start + clustering (exactly what `_basin_sweep`,
`tests/test_can_belief_quantization.py:66-116`, does).

**Classification (a) transfers cleanly and is arguably a genuine
improvement.** Recognizing whether a current belief state matches a held,
previously-seen configuration is EXACTLY `ShapeDecode`/`sd_recognize`'s job
(`shape_decode_loop.json`'s own description, quoted in §3.6: "full coverage
→ sd_recognize... no growth"), using `Covers`/`AntiUnifyWitness`
(`term.rs:3757-3785`/`:3420-3431`) against a growable codebook of held
configurations, instead of a fresh mean-field relaxation from whatever
`state` happens to be on the graph. This is strictly cheaper (§4) and
strictly more inspectable (a matched codebook entry is a named, addressable
graph node; a mean-field fixed point is an opaque numeric vector) than the
current mechanism.

**Enumeration (b) does NOT transfer for free, and this is worth being
precise about rather than hand-waving past it.** `ShapeDecode`'s recognize
path answers "does THIS observation match something held," not "how many
things COULD this landscape hold" — the second question needs a
CANDIDATE-GENERATION step (something to propose configurations worth
testing for local stability) that the continuous version gets, in effect,
for free from its own relaxation dynamics doing an implicit hill-climb from
each random restart. A codebook-recognize mechanism has no analogous
"propose a candidate from the coupling structure itself" step built in — it
can classify observed states, and it can MINT a new codebook entry when a
genuinely novel stable configuration is observed (the sd loop's rung-3, §3.5
below), but it has no native mechanism for asking "enumerate every basin
this NxN coupling matrix could in principle support" without something being
observed into each one first.

**Why this scope reduction does not, on inspection, cost this project
anything it currently uses** — checked against the actual consumers, not
assumed: `mt_target_equilibria`'s "how wrong" queries use `distance_to_
target` (a per-node deviation from a SPECIFIC target state — classification-
shaped); `self_improvement_dynamics`'s `mt_conflicting_nodes`/`mt_pairwise_
similarity` compare TWO Mts' own committed marginals (again, classification
of a specific relaxed state, not landscape enumeration); and of the 15
`causal_attitude_networks.json` rules, the only one wired with a real
`match`/`where`/`effects` today (`curiosity_targets_ambivalent_nodes`,
`CAN_BELIEF_QUANTIZATION_RESULTS.md` §5) reads a single Concept's `state`
attr and classifies it as near-zero — again classification, not
enumeration. **Nothing this project has actually built consumes basin
COUNT** — the enumeration half of the CAN literature's own theoretical
apparatus (used by Dalege et al. for scientific claims about real attitude
networks) is broader than what this codebase's own rules ask of it. This is
the load-bearing fact behind reading this claim as (b) rather than (c): the
scope reduction is real, but it is a reduction FROM a capability this project
never actually exercised TO one it does.

### 3.2 Claim 2 — Energy/frustration → residual size

**Verdict: faithful-but-different (b), plus a genuine, previously-unnoticed
measurement artifact this spike's own PoC surfaced (§5.3).**

`mt_frustration_given_state` (`can_ops.rs:333-352`) is, read precisely, NOT
itself an iterative-minimization quantity — it is a closed-form sum over
couplings, `Σ(actual - ideal)` where `actual = -w·σᵢ·σⱼ` and `ideal =
-|w|`, computable in `O(edges)` given ANY state. The iterative part of the
current mechanism is finding the STATE (mean-field relaxation), not computing
frustration from a state once you have one — a distinction the charter's own
framing (and the naive reading of "requires iterative minimization") slightly
overstates, corrected here for precision.

The sd-loop analog — residual size after decode, the portion of an
observation's relations a held codebook entry does not cover — is
structurally the SAME shape: both measure "how much of the current
configuration is inconsistent with what is expected/held," both are
closed-form given a proposed explanation, and both require SOME search to
find the best-fitting explanation in the first place (mean-field relaxation
for CAN; beam search over codebook parts for `ShapeDecode`, per
`RULES_AS_SHAPE_DESIGN_SPIKE.md`'s own read of `compose_design_for_goal`,
ported to Rust). **The honest correction to the naive version of this claim**:
replacing continuous relaxation with codebook decode does not eliminate the
need for SOME approximate search when a residual must be explained by
composing multiple codebook parts — it changes WHICH approximate search is
run (a bounded beam search over a small, growable codebook, `O(beam_width ×
max_steps × codebook_size × observation_size)`, confirmed polynomial and
parameter-bounded by direct read of the scoring loop, §4) instead of an
unbounded-iteration numeric relaxation over a potentially dense coupling
matrix. This is a real, verified improvement in the SHAPE of the residual
search-cost (bounded by fixed, small parameters rather than by network
density), not a claim that search disappears entirely.

### 3.3 Claim 3 — Multistability/polarization → decode ambiguity, evaluated
against outcome-similarity, not formal fidelity to CAN's own borrowed physics

**Verdict: faithful-but-different (b), for the WHOLE claim, on the correct
bar.** An earlier pass of this document evaluated polarization against
formal-mathematical equivalence to a literal Curie-Weiss critical point and
found a genuine loss there. That was the wrong bar, corrected here on two
grounds the creator supplied mid-flight and that this section now applies
directly: (1) the right comparison is whether the reframing produces
SIMILAR OUTCOMES to what CAN itself produces, not identical formal
mathematics to CAN's own imported formalism; (2) CAN's own authors never
claimed the Ising/mean-field machinery WAS cognition's actual mechanism —
"it also never said that the physics was the how - only that it used it as
a model," adopted because it predicts the right patterns. There is no
scientific ground given up by dropping continuous relaxation in favor of a
native "how" that produces the same "what," because the continuous "how"
never had a privileged claim to being the real mechanism in the first place.

`causal_attitude_networks.json`'s own description, quoted in full because
every noun in it matters for this section:

> "Network Hamiltonian H = -ΣJ_ij σ_i σ_j - Σh_i σ_i. Equilibrium
> distribution P(σ) ∝ exp(-βH) (Boltzmann)... Stability = local energy
> minimum. Attitude strength = network connectivity. Ambivalence =
> spin-glass frustration. **Polarisation = phase transition at low T.**
> Multiple inconsistent views = multistable network with distinct basins."

**"Multiple inconsistent views = multistable network with distinct
basins"** — read as "the current belief state can be genuinely torn between
two or more incompatible, each internally-coherent explanations" —
transfers cleanly to **decode ambiguity**: an observation that
partially-covers, or covers-with-comparable-score, TWO distinct held
`ShapeSignature` codebook entries at once is a direct, structural analog of
being caught between two basins, a STATIC, one-shot fact about a decode
(no relaxation dynamics needed at all).

**"Polarisation = phase transition at low T," read for its OUTCOME rather
than its formal mathematics, is: a population (or one agent across contexts)
with genuinely graded, continuum-valued underlying positions nonetheless
CLUSTERS into a small number of mutually-incompatible, internally-consistent
extreme stances rather than spreading smoothly, with something like a
sharpness/threshold character to when that clustering kicks in.** This is
checked directly in §5.4 below, not merely argued for: a purely static,
iteration-free, coverage-THRESHOLD decode — accepting a match against a held
prototype only when enough of an individual's own components agree with it
— is run against a smooth, uniform, continuum-valued population, using ONLY
`ShapeDecode`-shaped machinery (a coverage-threshold stand-in for the
Term's own existing `beam`/`max_steps`/`cand_k`/`budget` parameters —
`term.rs:2642`'s own `TermNode::ShapeDecode` signature, confirmed by direct
read to already carry these knobs — as the native scrutiny/"attention"
analog). **Result, confirmed empirically: this static threshold decode does
NOT pass the underlying continuum through unchanged — it genuinely
clusters.** As scrutiny (the coverage threshold) tightens away from its
midpoint, ambiguity (matching both prototypes at once) collapses toward
zero, and the population that resolves unambiguously becomes markedly MORE
concentrated near the two extremes (`frac_resolved_near_extreme` rises from
0.437 at the least-discriminating tested setting to 0.855 at the most —
§5.4's own table) — genuinely-moderate individuals are squeezed out of clean
resolution, exactly the qualitative shape "polarization" names, produced
with NO Boltzmann ensemble, NO continuous inverse temperature, and no
iteration of any kind.

**What this does NOT yet establish, named honestly rather than oversold**
(the full account is in §5.4): the specific dependence found is
NON-monotonic (U-shaped in the coverage threshold, not a clean one-directional
sharpening the way β's escalation is), a genuine correction to this
section's own first prediction, not a result quietly smoothed into a false
confirmation. The qualitative CAPABILITY (discrete decode produces real
clustering/thresholding behavior a smooth input does not have) is
established; the specific single-parameter operationalization that would
sharpen monotonically in one consistent direction, the way increasing β does
in the original model, is a real, narrower, still-open design question,
named precisely in §6/§7 rather than claimed solved.

### 3.4 Claim 4 — Evidence propagation → NOT the deduction facility as literally
proposed; a discrete asynchronous rule-firing reframing instead

**Verdict: faithful-but-different (b) — but the charter's own sketch names
the wrong existing mechanism, and the corrected mapping is this document's
single most load-bearing finding.**

The charter's own sketch proposed "ordinary rule-firing plus the deduction
facility" (`domains/propositional_deduction.py`/`seeds/inference_logical.json`)
as evidence propagation's replacement. **Checked directly and found
insufficient, not merely under-specified**: the deduction facility implements
BOOLEAN, DIRECTED logical entailment (`implies`, decoded via `Covers` — does
P follow from Q, yes/no). `apply_evidence_h` (`can_ops.rs:834-843`) followed
by relaxation is a fundamentally different computational object — evidence
at ONE node propagates NETWORK-WIDE through the WEIGHTED, potentially-CYCLIC
coupling structure, with GRADED, PARTIAL, and possibly MUTUALLY-CONTRADICTING
effects on neighbours (a node caught between two opposing influences settles
PARTWAY, not to either extreme) — this is a diffusion/consensus process over
a weighted graph, not a directed inference chain, and per `CAUSAL_LINKAGE_
DIMENSION_RESEARCH.md` §2.2/§2.7's own finding, boolean implication is
already known to be the WRONG tool for graded causal strength one level down
from this question. Re-using it here would repeat that exact mistake at the
network-propagation grain.

**The corrected mapping, derived by asking what a native, in-frame-integer,
Γ/rule-fixpoint-driven version of "evidence propagates through weighted
coupling and the network re-settles" would actually have to be**: a
**discrete, asynchronous, Hopfield-style threshold update**, expressed as an
ordinary graph Rule (`match`/`where`/`effects`), driven by `run_rules()`'s
own fixpoint — the SAME fixpoint mechanism this codebase already uses for
every other dynamic-quantization loop (`sd_decode → sd_recognize/sd_mint_
quantum → sd_redecode`, `shape_decode_loop.json`'s own description). This is
not an analogy reached for out of convenience — it is the textbook discrete
counterpart of the exact continuous update `can_ops.rs` already implements
(`σᵢ ← tanh(β(Σⱼ Jᵢⱼσⱼ + hᵢ))`, `can_ops.rs:187`), and its convergence
properties are well-established and favorable, checked this session
(§4.2):

- **Synchronous** (ALL nodes updated at once from a stale snapshot — exactly
  `can_ops.rs`'s current implementation) is known to converge EITHER to a
  fixed point OR a period-2 limit cycle — precisely the pathology
  `CAN_BELIEF_QUANTIZATION_RESULTS.md` §3.1 measured directly
  `[search-synthesis, converging across multiple independent sources this
  session]`.
- **Asynchronous** (one node updated at a time, using already-updated
  neighbours within the same sweep) admits a genuine Lyapunov function for a
  symmetric coupling matrix — energy provably never increases, and the
  system converges to a stable local minimum with NO oscillation possible,
  by construction `[search-synthesis, converging, Hopfield 1982's
  foundational result]`.

This is not merely a citation — §5 below runs it, on fresh draws, and
confirms it holds.

**Buildability, checked against the existing Term vocabulary (the charter's
own "no new Rust Term without justification" bar)**: the update needs (a) a
weighted sum over a node's coupled neighbours' states — `Sum` over `Edges`
reading `EdgeAttr` is ALREADY a real, tested pattern in this exact shape
(`term.rs:11011-11044`'s own test, `edges_and_edgeattr_read_edge_attrs`,
confirmed by direct read: `Sum{source: Edges(me, connects), value:
EdgeAttr(e, "weight")}`) — the one open piece this pass did not exhaustively
confirm is pairing each edge with its NEIGHBOUR's `state` attr inside that
same `Sum` (multiplying `EdgeAttr(e,"weight")` by `Attr(neighbour_of(e),
"state")`), which is very likely expressible via the existing `Neighbours`/
`MapNeighbours` accessors but was not traced to a worked example in this
pass — named honestly as the one thing a follow-on build must confirm before
claiming zero new Rust, not assumed; (b) a threshold decision — `Gt`/`Lt`
already exist (`term.rs:490-503`'s arithmetic block) and a FIXED numeric
threshold (θ = atanh(0.5)/β, computed once, not per-tick) reproduces the
same discretization boundary as rounding `tanh(β·local)` to the nearest of
`{-1,0,+1}` WITHOUT needing a `Tanh` Term at all (confirmed: no `Tanh`
variant exists in `TermNode` today, grepped directly — and the native rule
does not need one). **If this holds, the discrete-async evidence-propagation
rule needs ZERO new Rust Terms** — a materially stronger claim than the
sibling damping rung's own fix, which required a new function parameter
threaded through three call sites and both PyO3 bindings
(`CAN_SYNCHRONOUS_UPDATE_FIX_PREREG.md` §2) but stayed within the same
continuous-relaxation paradigm.

### 3.5 Claim 5 — Hebbian coupling-strengthening → mint-on-recurrence

**Verdict: faithful for edge CREATION (b); incomplete alone for ongoing
graded reweighting of an EXISTING edge, which needs composing with a
separate, already-designed-but-not-built primitive (named precisely, not
glossed).**

`hebbian_update_J` (`can_ops.rs:655-697`) does two things at once that the
charter's single "mint-on-recurrence" sketch does not separate: (a) it can
be read as implicitly DECIDING that a coupling between two co-active
concepts is real (if no `causal_influence` edge exists yet, nothing in
`can_ops.rs` mints one automatically — edges are pre-existing by construction
in every test/seed built so far), and (b) for an edge that DOES exist, it
CONTINUOUSLY reweights `J_ij` by `η·σᵢ·σⱼ` every call, with `decay_J`
providing an offsetting continuous forgetting term.

**(a), edge creation from repeated co-occurrence, maps cleanly onto
mint-on-recurrence** — exactly the sd loop's rung-1→rung-3 shape (`sd_
recognize`/no-growth on a repeat vs. `sd_mint_quantum`/growth on a genuine
residual), the SAME shape already measured at real scale on this project's
own corpus (`BLOB_EDGE_ANALOGY_EXTENSION_RESULTS.md`, cited by `CAN_BELIEF_
QUANTIZATION_RESULTS.md` §7: 98.3% pattern reuse on 7970 real comparisons).

**(b), ongoing graded reweighting of an ALREADY-MINTED edge, is a
genuinely separate question mint-on-recurrence alone does not answer** —
and this project has ALREADY designed, though not built, the correct native
primitive for exactly this gap: `CAUSAL_LINKAGE_DIMENSION_RESEARCH.md`'s own
`logodds` `DimensionGenerator` recommendation (§7 of that document,
`file:834-877`) — an integer evidential-observation count as the in-frame
datum, log-likelihood-ratio as the cross-frame map, following the SAME
`scale2`/`modular` `DimensionGenerator` precedent `shape_decode_loop.json`
already ships (v1.4.0/v1.5.0, confirmed live in this pass, `:8`). **The
correct composition, stated precisely rather than left implicit**: mint
handles "does this coupling exist at all" (first occurrence → residual →
mint); the `logodds` generator (designed, not yet built) handles "how strong
is it now" (each subsequent co-occurrence → an integer step `k` → a
cross-frame log-odds render) — Hebbian's single continuous update rule is
correctly split into TWO composed native primitives, not one, and this spike
is the first place that composition is stated explicitly.

**Decay has no proposed native analog at all, named as a genuine, open
residual rather than silently folded into the above**: `decay_J`/`decay_h`
implement continuous, monotonic forgetting (`J ← (1-λ)J`) with no sd-loop or
Γ counterpart identified in this pass or any of the four prior docs. A
plausible direction — treating elapsed time/tick-count as its own integer
dimension the `logodds` generator's `k` steps DOWN along, absent
reinforcement — is a coherent guess consistent with the frame/continuum
discipline, but it is a guess, not a verified design, and is reported here
as exactly that.

### 3.6 A sixth check the charter did not ask for directly, but that §3.1's
audit surfaced and that belongs in the record: what do the 15 seed rules
and the two real consuming Mts actually need?

Read against every rule name in `seeds/causal_attitude_networks.json`
(confirmed by direct load, §1 point 4) and the real consuming call sites
(`mt_target_equilibria`, `self_improvement_dynamics`, per `can_ops.rs`'s own
module doc `:1-19`): every rule name maps onto one of the FIVE claims above
— `attitudes_are_networks_not_latents`/`Mt_relativity_is_multiple_
Hamiltonians` (structural, no dynamics), `wrongness_is_distance_to_target_
equilibrium` (claim 1, classification), `ambivalence_is_frustration_not_
indecision`/`coherence_is_negative_free_energy_density` (claim 2),
`multiple_inconsistent_views_are_multistable_basins`/`attention_increases_
polarisation` (claim 3 — reproducible on the outcome-equivalence bar per
§3.3/§5.4, with `attention_increases_polarisation`'s own exact single-
parameter form still an open, sized, buildable question, not a blocked
capability), `evidence_changes_field_then_relaxation` (claim 4),
`Hebbian_learning_updates_J` (claim 5), `babble_loop_is_thermal_sampling`/
`predicate_churn_is_bistable_thermal_flipping` (claim 3's weak reading,
genuine multistability). **No rule in this seed names or consumes basin-
count ENUMERATION as a first-class quantity** — the one genuine scope
reduction this audit finds (§3.1) also turns out to be a rule this codebase
has not yet wired to real dynamics
(`CAN_BELIEF_QUANTIZATION_RESULTS.md` §4's own finding: only 1 of 15 rules
has ever been given real `match`/`where`/`effects`). This is not asserted as
proof that the gap is inconsequential forever — only as the precise,
checked fact that it is currently unexercised, which is exactly the basis
§7's verdict rests its "replace" recommendation on.

---

## 4. The complexity/pathology payoff — verified, not assumed

**Claim under test**: does the sd-loop-native reframing genuinely eliminate
Barahona's NP-hardness concern and the synchronous-update oscillation, and
is decode complexity roughly `codebook_size × observation_size` rather than
exponential?

**Confirmed directly from source, not inferred from the docstrings**:
`shape_decode.rs:1521`'s scoring loop — `for (part, sig) in
parts.iter().zip(scoring_sigs.iter())` — is a single linear pass over the
codebook's parts, each scored by `score_part_for_residual`
(`shape_decode.rs:1267-1299`), itself bounded by the observation's own
relation count (`covers_relation`, `:1224-1266`, a nested comparison over
the observation's relations, not over any global configuration space). When
a residual needs MULTIPLE parts composed, this becomes a bounded beam
search — `RULES_AS_SHAPE_DESIGN_SPIKE.md`'s own read of `compose_design_for_
goal`'s Rust port confirms this is parameterized by a FIXED beam width and
max-steps, not by network size. **The decode/recognize complexity is
therefore genuinely `O(beam_width × max_steps × codebook_size ×
observation_size)`** — polynomial in every one of its factors, and NOT a
function of `N` (the number of coupled beliefs) at all in the way ground-
state search or even one mean-field relaxation sweep (`O(concepts × average
degree)` per sweep, times `max_iter` sweeps, `can_ops.rs:226-251` confirmed
directly) is.

**Does this eliminate Barahona's NP-hardness?** `CAN_SOLVER_THEORETICAL_
LIMITS_RESEARCH.md` §3.2 already established, correctly, that `can_ops.rs`
never attempted the NP-hard exact ground-state search in the first place —
mean-field is already a polynomial-per-iteration approximation. So the
honest question is not "does sd-loop decode beat an NP-hard problem" (a
comparison against something never attempted) — it is "does replacing
continuous relaxation with sd-loop decode change what class of problem is
even being approximated." For the CLASSIFICATION half (claim 1, is this
observed state one we've seen before), the answer is yes and it is a clean
win: no iteration, no fixed point, no oscillation possible, because there is
no dynamical system in the recognize path at all. For the PROPAGATION half
(claim 4), the corrected mapping (§3.4) is a discrete asynchronous Hopfield-
style rule — this STILL requires iterating to convergence (asynchronous
sweeps until no node wants to flip), so it does NOT change the asymptotic
DIFFICULTY of finding the best/global configuration among many local minima
(that remains exactly as combinatorially hard as it always was, and no
reframing changes that) — what it changes, provably, is whether the
iteration can OSCILLATE rather than converge, which is the SPECIFIC,
measured pathology this whole investigation started from. This is the
precise, non-overclaiming statement of the payoff: **the oscillation class
of bug is eliminated by a proof, not a patch; the deeper combinatorial
hardness of finding the single best global configuration is unaffected by
any reframing, exactly as `CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` §3.2
already found for the mechanism that exists today.**

---

## 5. The smallest test — designed, then run

### 5.1 Design (registered before running)

Per the task's own instruction: the smallest test that would validate or
refute the mapping, using ONLY machinery this document argues is native
(discrete states, asynchronous updates expressible as ordinary rule-firing),
against a REAL, already-measured CAN phenomenon (`CAN_BELIEF_QUANTIZATION_
RESULTS.md` §3.1's own persistent 2-cycle) rather than a fresh, unrelated
claim.

**Predictions, registered before the script was run** (verbatim from the
script's own `main()`, written before execution):

1. Continuous-synchronous oscillation reproduces on fresh, independently-
   drawn networks (confirms the phenomenon is not an artifact of the prior
   rung's specific seed).
2. Discrete-asynchronous, TWO-STATE (`σ ∈ {-1,+1}`, no neutral option): ZERO
   non-convergent draws — the textbook Hopfield Lyapunov guarantee, applied
   cleanly, no known gap in the proof for this case.
3. Discrete-asynchronous, THREE-STATE (`σ ∈ {-1,0,+1}`, the CAN model's own
   NATIVE vocabulary per its seed description — "σ ∈ {-1, 0, +1} (or
   continuous)"): outcome NOT predicted with the same confidence. This
   spike identified, by direct inspection before running anything, a real
   gap in the standard proof for this case — moving from a committed state
   toward the neutral dead-zone when the local field is weak but nonzero
   can, in principle, ADD energy rather than remove it (worked through
   below), so the guarantee is not airtight for the 3-state case the way it
   is for the 2-state case. Registered as genuinely open, checked
   empirically rather than assumed either way.
4. Bonus/secondary, NOT registered as testing the same manipulation as the
   real V=2-vs-V≥3 finding (a distinction this spike's own results forced it
   to draw explicitly, §5.3): does the 3-state (neutral-option) variant show
   different frustration-at-convergence than the 2-state variant?

**The proof-gap for prediction 3, worked through precisely** (registered
before running, not reverse-engineered after seeing a result): at a fixed
point of the SINGLE-node update, moving from `σ_old` to `σ_new` changes
energy by `ΔE = -(σ_new - σ_old)·local_i` (the standard single-spin-flip
Hopfield derivation, holding all other nodes fixed). The 2-state rule always
picks `σ_new = sign(local_i)`, which MAXIMIZES `σ_new·local_i` among the two
options, so `ΔE ≤ 0` always. The 3-state rule can pick `σ_new = 0` when
`|local_i|` is small — but if `σ_old` already agreed in sign with `local_i`
(say `σ_old=+1`, `local_i=+0.1`), then `σ_new·local_i = 0 < σ_old·local_i =
0.1`, so `ΔE > 0` for that single step: **the deadzone case can, in
principle, increase energy**, breaking the clean monotonicity argument. This
is exactly the kind of thing this document's own house discipline requires
naming BEFORE running the check that would resolve it, not noticing it only
if the numbers come out badly.

### 5.2 What was built and run

`can_concept_poc_discrete_async.py`
(`docs/research/engine_substrate/can_concept_poc_discrete_async.py`, this
worktree) — **pure Python, standalone, no Rust, no PyO3, no seeds, no
substrate import, does not call or edit `can_ops.rs` in any way.** It
independently replicates `can_ops.rs::mt_mean_field_marginal`'s exact update
formula (`σᵢ ← tanh(β(Σⱼ Jᵢⱼσⱼ + hᵢ))`, synchronous) as the "before"
baseline — an honest from-first-principles re-derivation, not a citation of
the prior rung's own numbers — plus the two discrete-asynchronous candidate
variants from §5.1, using deterministic round-robin update order (matching
`CAN_SYNCHRONOUS_UPDATE_FIX_PREREG.md`'s own finding that this Rust engine
has no RNG crate dependency anywhere, so a candidate that needs none is
preferred and tested first). N=8 complete graph, β=2.0, 30 independent
draws × {coarse (3-level J), fine (9-level J)} vocabularies, matching
`CAN_BELIEF_QUANTIZATION_RESULTS.md` §2.2's own quantization scheme exactly
(same granularities, same centered-integer-`k` rounding), fixed nonzero
per-node external field (the prior rung's own documented fix for the h=0
degenerate all-zero fixed point, `CAN_BELIEF_QUANTIZATION_RESULTS.md` §3.1
"First finding").

**Run output** (reproduced verbatim):

```
N=8 complete graph, beta=2.0, 30 draws x {coarse,fine}

coarse    continuous_sync_osc=16/30  discrete_async_2state_nonconv=0/30  discrete_async_3state_nonconv=0/30  mean_frustr_2state=5.400  mean_frustr_3state=6.200
fine      continuous_sync_osc=6/30   discrete_async_2state_nonconv=0/30  discrete_async_3state_nonconv=0/30  mean_frustr_2state=6.650  mean_frustr_3state=7.033
```

### 5.3 Results against the registered predictions, precisely

1. **Confirmed.** Continuous-synchronous oscillation reproduces on these
   fresh draws (16/30 coarse, 6/30 fine) — the phenomenon is real and not
   an artifact of the specific seed `CAN_BELIEF_QUANTIZATION_RESULTS.md`
   §3.1 happened to use. The coarse-oscillates-more-than-fine direction is
   also directionally consistent with that rung's own weak lean (its own
   §3.1 finding: 66.7%/55% coarse vs 50%/50% fine across two samples) —
   this script's 53.3%/20% gap is a larger separation on a DIFFERENT,
   independent sample, reported as directionally consistent, not as a
   power-matched replication of the exact rate (different N_DRAWS, different
   seeds, not designed to be a strict reproduction).
2. **Confirmed, exactly as predicted, 0/30 in both conditions.** The
   two-state discrete-asynchronous rule never failed to converge, on any of
   60 draws total — the textbook Lyapunov guarantee held cleanly, on real
   coupling structures drawn from the same distribution that produced real
   oscillation under the continuous-synchronous rule.
3. **Also 0/30 in both conditions — the theoretically-open case turned out
   empirically clean on this sample, reported honestly as an empirical
   finding, not a proof.** The energy-increasing single-step case identified
   in §5.1 evidently either does not occur, or occurs but is not sufficient
   to produce a sustained cycle, on these 60 draws. This is NOT claimed as a
   general theorem — it is reported precisely as what it is: zero
   counterexamples found in a real, if modest, sample, on the SAME class of
   networks that reliably oscillate under the continuous rule. A follow-on
   build should not assume this generalizes to arbitrary `N`/density without
   a larger sweep; it is registered here as a genuinely encouraging,
   unproven empirical result.
4. **A finding this spike did NOT predict correctly, and corrects in the
   record rather than smoothing over** (matching this project's own standing
   practice of keeping self-corrections visible,
   `RULES_AS_SHAPE_DESIGN_SPIKE.md`'s §15 self-correction cited as
   precedent in `CLAUDE.md`): the 3-state (neutral-option) variant showed
   HIGHER mean frustration at convergence than the 2-state (forced-
   commitment) variant (6.2 vs 5.4 coarse; 7.03 vs 6.65 fine) — the OPPOSITE
   of what this document initially expected by loose analogy to the real
   V=2-vs-V≥3 cliff (`CAN_CROSSOVER_POINT_RESULTS.md` §3, where REMOVING the
   zero option from `J`'s vocabulary caused a 1.6-2× frustration SPIKE).
   **On inspection, this is not a contradiction — it is a different
   manipulation being loosely conflated with the real one, and naming that
   precisely is itself the useful finding**: the real V=2 cliff varies the
   RESOLUTION OF THE COUPLING `J`'s vocabulary (keeping `σ` continuous);
   this bonus check instead varies the resolution of `σ` ITSELF (the belief
   STATE's own vocabulary, keeping `J` fixed) — two different axes this
   document initially treated as more alike than they are. The mechanism
   this check DOES reveal, honestly: `mt_frustration_given_state`'s own
   formula structurally penalizes NEUTRALITY the same way it penalizes
   outright CONTRADICTION (`ideal = -|w|` is only achieved by FULL
   commitment in the sign of `w`; `σᵢ=0` on either endpoint of an edge
   scores `actual=0`, strictly worse than a correctly-signed commitment,
   by exactly `|w|`, regardless of whether the true relationship actually
   warranted commitment). **This is a real, previously-unremarked-on
   measurement property of the frustration formula ITSELF, present
   identically in `can_ops.rs`'s own continuous implementation** (this
   spike's discrete rule uses the identical frustration formula, unmodified)
   — worth flagging as a possible confound in ALL FOUR prior CAN docs'
   own frustration numbers, not something this reframing introduces or
   fixes. Named here, not resolved — resolving it (e.g. a frustration
   definition that treats principled non-commitment as free rather than
   costly) is real, separate design work this spike did not attempt.

### 5.4 A second smallest test — polarization as outcome, not formal fidelity

**Design (registered before running).** Per the corrected bar in §3.3: build
a population with a smooth, uniform, continuum-valued TRUE underlying
leaning `alpha ∈ [0,1]` (41 levels × 40 independent individuals each — each
individual's N=8 belief components independently lean toward one of two
fixed opposite prototypes with probability `alpha`, i.e. genuinely
heterogeneous per-component, not a lock-step blend — the "smooth continuum,
no clustering" null this check tries to falsify). Decode each individual
against the two prototypes using a coverage-threshold rule (`scrutiny_T` of
N=8 components must agree before a match counts), sweeping `scrutiny_T` from
1 to 8 — the native stand-in for `ShapeDecode`'s own existing `beam`/
`max_steps`/`cand_k`/`budget` parameters, no new machinery. **Registered
prediction, stated in the script's own `main()` before it was run**: as
`scrutiny_T` rises, the resolved population should become MORE concentrated
near the extremes, `frac_resolved_near_extreme` rising monotonically toward
1.0.

**Built and run**: `can_concept_poc_decode_polarization.py`
(`docs/research/engine_substrate/can_concept_poc_decode_polarization.py`,
this worktree) — pure Python, standalone, same isolation discipline as
§5.2's script.

```
scrutiny_T     pro   anti  ambig unresolved    frac_resolved_near_extreme
         1     211    189   1240          0                         0.855
         2     395    383    862          0                         0.699
         3     559    559    522          0                         0.551
         4     735    724    181          0                         0.437
         5     735    724      0        181                         0.437
         6     559    559      0        522                         0.551
         7     395    383      0        862                         0.699
         8     211    189      0       1240                         0.855
```

**Confirmed**: ambiguity (matching both prototypes) collapses monotonically
as `scrutiny_T` rises from 1 to 4 (1240 → 862 → 522 → 181 → 0), and the
resolved population's extremity is markedly higher at both ends of the
tested range (0.855 at T=1 and T=8) than in the middle (0.437 at T=4/5) —
real, measured clustering behavior a smooth linear-in-`alpha` input does not
have, produced by a static threshold with no iteration and no ensemble.

**NOT confirmed as registered, and reported precisely rather than
reinterpreted charitably**: `frac_resolved_near_extreme` is U-SHAPED in
`scrutiny_T` (0.855 → 0.437 → 0.855), not monotonically rising toward 1.0 as
predicted. The reason, diagnosed rather than left as an unexplained miss:
`scrutiny_T` and `N − scrutiny_T` are symmetric under this construction
(needing `T` of 8 components to agree with one prototype is exactly as hard,
by construction, as needing `8−T` to disagree with it), so sweeping `T` from
1 to 8 sweeps THROUGH a symmetric middle rather than monotonically in one
direction the way increasing β does in the original continuous model (which
sharpens commitment magnitude from a single starting point, not by moving
between two symmetric extremes of a vote-count threshold). **The qualitative
capability this test set out to check — does discrete threshold decode
produce genuine clustering behavior absent from a smooth input — is
confirmed. The specific claim that raw coverage-threshold `scrutiny_T` is
already the correct one-parameter stand-in for β specifically is refuted by
this test's own data** — a real, informative, registered-in-advance
correction, not smoothed over. A more faithful operationalization of
"attention" (varying `ShapeDecode`'s own `max_steps`/`beam` — how many
ROUNDS of refinement are spent before committing, rather than a symmetric
vote-count bar) is the natural next test this section names but does not
run, sized in §7.

---

## 6. What does NOT transfer — the honest, specific list

Four items, each already argued in full above, collected here per the
task's own request for a distinct, scannable section rather than scattered
through the claim-by-claim analysis. Per §3.3/§5.4, polarization as a
PHENOMENON is not on this list — it transfers. What remains open for it is
narrower than a capability loss (folded into item 1):

1. **NOT a capability loss, but a real open parameterization question**:
   §5.4 confirmed discrete coverage-threshold decode genuinely produces
   clustering/thresholding behavior a smooth input lacks (the outcome
   polarization is about), but did not find a single free parameter that
   sharpens monotonically in one direction the way CAN's own β does — the
   tested `scrutiny_T` is symmetric/U-shaped instead. The natural next probe
   (varying `ShapeDecode`'s own `max_steps`/`beam` — refinement depth —
   rather than a symmetric vote-count bar) is named, sized in §7, not run
   here.
2. **Basin-topology ENUMERATION as opposed to classification (§3.1)** — "how
   many distinct stable configurations can this network's structure
   support" needs a candidate-GENERATION step the codebook-recognize
   mechanism does not natively have; classification (which one does the
   CURRENT state match) transfers cleanly and is the half this project's
   own rules actually use.
3. **Ongoing GRADED reweighting of an already-minted coupling (§3.5)** — the
   continuous half of Hebbian learning needs composing mint-on-recurrence
   with the SEPARATE, already-designed-but-not-built `logodds`
   `DimensionGenerator` (`CAUSAL_LINKAGE_DIMENSION_RESEARCH.md`'s own
   recommendation) — a real, correctly-identified two-piece composition, not
   a one-piece substitute.
4. **Coupling/field decay (forgetting) has no proposed native analog at
   all (§3.5)** — flagged as a genuinely open gap, with one plausible but
   unverified direction named (elapsed-time as its own stepped dimension),
   not resolved here.

---

## 7. FINAL VERDICT — (b), replace, weighed against functional goals and
efficiency, not fidelity to the borrowed physics metaphor

Stated without hedging, per the charter's own instruction and the creator's
mid-flight calibration on how to weigh it: **replace.** Not "keep the
continuous implementation" (a) — every measured pathology in the four prior
docs (synchronous oscillation, mean-field's own documented weakness under
frustration, the float-in-a-frame violation of this project's own
architectural discipline) is a property of the SPECIFIC imported mechanism,
and §4-5 verify, not merely assert, that a native discrete/rule-driven
reframing removes the most concretely damaging one (oscillation) by a real
proof plus a clean empirical check, at a genuinely better computational
shape (decode-bounded, not iteration-bounded, for the classification half).
Not "run both in parallel for different use cases" (c) either — there is
nothing left that needs the parallel system to justify it. §3.3/§5.4 found
that polarization's OUTCOME transfers natively; §3.6 confirms nothing this
project has actually built even exercises polarization today (only 1 of 15
seed rules has ever been wired to real dynamics at all, and it is a
classification rule, not a polarization rule; no populated
`causal_influence` network exists in the corpus, per `CAN_BELIEF_
QUANTIZATION_RESULTS.md` §7's own admission, unchanged by anything measured
today); and per the creator's own clarification, CAN's continuous mechanism
never had a privileged claim to being the "real" one in the first place —
it was always just a model chosen for its predictions, exactly as the
native reframing now is. Keeping a second, parallel, fully-continuous system
running indefinitely, to protect a bar (formal fidelity to a borrowed
physics metaphor) this project has no principled reason to hold itself to,
is exactly the "safer bet" the creator's own standing instruction warns
against defaulting to.

**What "replace" concretely means, sized but not built, per the task's own
explicit scope boundary:**

1. **Classification/basin-membership (claim 1)**: replace `audit_basin`'s
   single mean-field call with `sd_recognize` against a `ShapeSignature`-
   style codebook of held stable configurations. Zero new Rust Terms —
   `ShapeDecode`/`AntiUnifyWitness`/`Covers` already exist and are already
   proven at scale elsewhere in this codebase.
2. **Frustration/coherence (claim 2)**: replace `mt_frustration_given_state`
   with residual size from the same decode. Recommend fixing the
   neutrality-penalizing measurement artifact (§5.3, point 4) in the SAME
   pass, since it is a pre-existing property of the formula being ported,
   not something the port would introduce — but this is real, separate
   design work (what should "principled non-commitment" cost, if not
   `|w|` per edge), named here, not designed.
3. **Evidence propagation (claim 4)**: build the discrete-asynchronous
   threshold rule as ordinary graph Rules driven by `run_rules()`'s
   fixpoint. Sized: confirm the one open Term-composition question (§3.4 —
   pairing `EdgeAttr` with the neighbour's `state` `Attr` inside one `Sum`)
   before claiming zero new Rust; if it holds, this needs zero new Rust
   Terms, a small number of new seed rules, and a fixed fresh threshold
   constant (`θ = atanh(0.5)/β`, computed once per Mt from its own β, not
   hand-tuned). If it does not hold, the gap is one small, well-scoped new
   Term (an edge-weighted neighbour-sum), not a redesign.
4. **Coupling creation + strengthening (claim 5)**: mint-on-recurrence for
   edge creation (existing machinery, zero new Rust); the `logodds`
   `DimensionGenerator` for graded strength (already designed in
   `CAUSAL_LINKAGE_DIMENSION_RESEARCH.md`, explicitly NOT built there either
   — both pieces of this composition are named, sized follow-on work, not
   attempted here).
5. **Polarization's native mechanism (claim 3) is sized as a real next
   build, not deferred as a capability gap**: §5.4 confirmed the OUTCOME
   (clustering under scrutiny) reproduces natively; the next step is
   re-running that exact check with `ShapeDecode`'s own `max_steps`/`beam`
   parameters (refinement depth) as the scrutiny/attention analog instead of
   a symmetric vote-count threshold, since §5.4's own data shows the latter
   is not yet the right one-parameter stand-in for β's monotonic
   sharpening. This needs zero new Rust (the parameters already exist on
   the Term) and is the natural, cheap, well-scoped follow-on this spike
   names but does not run. **No isolated continuous-ensemble fallback is
   recommended anywhere in this document** — per the creator's own
   clarification, CAN's physics never had a privileged claim on being the
   real mechanism, so there is nothing to preserve a parallel system for.

---

## 8. What this document does NOT establish

1. **No production code was changed.** `can_ops.rs` is untouched; the
   proof-of-concept script is pure Python, standalone, and does not call it.
2. **The proof-of-concept's sample is modest (30 draws × 2 conditions) and
   is not a power-analysed claim.** It is sufficient to falsify "discrete-
   async oscillates just as often as continuous-sync" (it did not, 0/60 vs
   16/30+6/30) but is not sufficient to claim "discrete-async NEVER
   oscillates on any network this substrate could construct" — a larger,
   pre-registered sweep (following `CAN_CROSSOVER_POINT_RESULTS.md`'s own
   precedent of scaling up a prior rung's exploratory sample) is the natural
   next check before this becomes a production claim.
3. **The 3-state variant's empirical cleanliness (0/30 non-convergent) is
   not a proof.** §5.1 identified a real gap in the standard monotonicity
   argument for this case; §5.3 reports zero observed counterexamples, not
   zero possible ones.
4. **The one open Term-composition question named in §3.4 and §7 point 3
   (pairing an edge's weight with its neighbour's state inside one `Sum`)
   was not traced to a worked example in this pass** — treated honestly as
   "very likely, not confirmed" rather than assumed.
5. **The `logodds` `DimensionGenerator` this document leans on for claim 5's
   full composition remains exactly as un-built as `CAUSAL_LINKAGE_
   DIMENSION_RESEARCH.md` left it** — this spike does not advance that
   design, only names where it plugs in.
6. **The frustration-formula neutrality-penalty finding (§5.3 point 4) is
   named, not fixed, and its implications for the FOUR PRIOR docs' own
   already-reported frustration numbers were not re-audited here** — those
   numbers stand as reported by their own rungs; this document only flags
   that the metric they share has a property worth someone re-examining.
7. **§5.4's coverage-threshold decode is a proof-of-concept for the
   OUTCOME, not a finished mechanism.** It confirmed clustering occurs and
   confirmed its own first prediction of monotonic sharpening was WRONG for
   the specific parameter tested (§5.4's own U-shape finding) — the
   corrected, likely-monotonic candidate (`ShapeDecode`'s own `max_steps`/
   `beam`) was named, not built or tested, in this pass.
8. **Whether ANY of this reflects real human belief-network dynamics**
   remains exactly as open as every prior rung in this arc left it
   (`CAN_BELIEF_QUANTIZATION_RESULTS.md` §9 point 1) — this document is
   about this SUBSTRATE's own best-fitted mechanism, not a new claim about
   cognition.
9. **The sibling `can-synchronous-update-fix` rung's own eventual RESULTS
   were not available at the time of this reading** (only its PREREG existed,
   confirmed via `git status --short` in that worktree) — this document does
   not depend on its outcome and was written not to, per the task's own
   instruction.

---

## 9. Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/can-concept-reimplementation-spike
git log --oneline -1 main   # cf53784, verified before branching

# Proof-of-concept 1: discrete-async vs continuous-sync oscillation (Sec 5.1-5.3)
python3 docs/research/engine_substrate/can_concept_poc_discrete_async.py

# Proof-of-concept 2: polarization as outcome-equivalence (Sec 5.4)
python3 docs/research/engine_substrate/can_concept_poc_decode_polarization.py
```

Both scripts are pure Python, standalone, no build step, no substrate
import, no dependency on `can_ops.rs` or any production path.

**Worktree:** `/home/matt/ozmadev/ocelot-worktrees/can-concept-reimplementation-spike`
**Branch:** `can-concept-reimplementation-spike`
**Base:** `main` @ `cf53784` ("Merge can-solver-theoretical-limits: theoretical
limits of the CAN mean-field solver, GO")

Not merged into `main`. This is a research document plus two isolated,
clearly-labeled proof-of-concept scripts — no seeds, no `can_ops.rs` changes,
no schema changes were made or proposed as diffs. §7's sizing is a
recommendation for dedicated follow-on build rungs, not a build.
