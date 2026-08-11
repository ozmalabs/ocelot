# Γ search-completeness ceiling — three probes on the sd loop, Γ's weight, and the composer's beam

**Status: DESIGN-ONLY CEILING PROBE. No code, seed, domain, or runner file was
modified.** Continues `docs/research/problem_difficulty/
PROBLEM_DIFFICULTY_QUANTIFICATION_LITERATURE.md`'s **CORRECTION** section
(2026-08-11), which found a real, rigorous, non-impossible framing for
"meta-confidence in tractability" — a bound *derived from search progress over
a committed, cost-ordered space* (A*/branch-and-bound/cost-ordered enumerative
synthesis), as opposed to the impossible a-priori version the rest of that
document surveys — and then audited this repo's own `(G, Γ)` + sd-loop
machinery against it, finding it **partial**: three named, unaudited gaps.
This document does the audit. It is read-only over `runners/`, `domains/`,
`seeds/`; the one artifact it adds is a standalone, non-mutating probe script
(`scripts/probe_beam_completeness.py`) used for Probe 3(c), plus this
document. Companion reading: `docs/research/adventure_mechanics/
ADVENTURE_MECHANICS_COMBINATION_GRAMMAR.md`, the sibling design doc proposing
admit/retract mechanics on top of Γ — §5 below checks this probe's findings
against that document's own assumptions about Γ and finds them consistent.

Per this project's own house style (`PROGRAM_SYNTHESIS_ARC6_A_CEILING.md`,
`PROGRAM_SYNTHESIS_ARC6_STRUCTURAL_CEILING.md`): a clean null is a complete
result; a "GO" finding names what would need building, without building it.
Nothing below recommends building anything. All three probes conclude in this
document.

---

## Verdict, up front

| Probe | Finding | Classification |
|---|---|---|
| **1 — sd loop rung ladder** | The guard-chain *is* a real, provable ordering — not merely "usually checks cheap things first" — but the proof rests on three separate load-bearing facts, one of which (composition-depth bound) is a scoped, not unconditional, completeness claim. | **(b) sound, but conditional — the conditions are worth stating once, not re-proving per rung.** |
| **2 — Γ's `weight` as a path-cost** | The creator's correction is right: there is no absolute cost to bolt on. Γ's `weight` is *already* a log-domain quantity (`selection ∝ exp(w)`), and the raw (pre-normalization) per-production `w` composes validly along a path under the standard log/tropical-semiring identity — **but nothing in this repo currently composes it that way.** The one existing multi-hop consumer (`substrate/weighted.py`'s `weighted_walk`) locally re-normalizes at every hop, which is exactly the shape the CRF literature calls the *label bias* problem — a real, checkable, and currently-real failure mode, not a hypothetical one, if that pattern were reused for a completeness bound. | **(b) possible, with a real design decision (global vs. local normalization) — not (a), because the natural-looking implementation is the wrong one.** |
| **3 — composer's beam search** | The gap is real and cheaply, deterministically reproducible (verified live, §4.3): a 5-part, 4-relation, 2-step construction where `beam=1` returns an incomplete plan flagged `authored: true` and `beam≥2` finds the complete one, using the exact production evaluator. This repo has *already* made the opposite choice (exhaustive, size/MDL-ordered, budget-bounded search over a fixed-width beam) for the sibling program-synthesis enumerator, and named the beam "dead weight." | **(b) a real design decision with a named in-repo precedent for the alternative — not free, but not speculative either.** |

None of the three is a clean "not worth it" null. None is "just wire it up," either — Probe 2 in particular is **not** what it looked like before this document's own framing was corrected mid-investigation (see §3.0).

---

## 1. Probe 1 — does the sd loop's rung ladder actually guarantee cost-ordered escalation?

### 1.1 The question, restated sharply

The correction section asked: does `recognize → transform → infer-dimension →
mint` try cheaper hypothesis classes before more expensive ones **in a way
that supports a real lower-bound claim** ("rung 1 and rung 2 both failed ⟹
true cost > rung 2's ceiling"), or does it just *happen* to usually check
cheap things first, with no provable ordering? The sharpest version of the
worry: `run_rules`'s own fixed-point loop (`runners/dsl/src/rewrite.rs:2103-2115`)
documents itself as walking the rule list **in order**, applying "the first
matching rule whose effect actually changes the graph," one binding per pass
for non-batch rules, restarting the pass from rule 0 on every progressing
step — this is a real, deterministic order, but ARC6's own documents
(`PROGRAM_SYNTHESIS_ARC6_ARC_GOALS.md:495`, `PROGRAM_SYNTHESIS_ARC6_MAGNITUDE.md:515`)
repeatedly warn **"this engine has no rule ordering, so a dependency has to
be a guard chain anyway."** Those two facts look like they contradict each
other. They don't, and the reconciliation is the actual finding.

### 1.2 What "no rule ordering" actually means, read against the code

`run_rules_opts` (`rewrite.rs:2140-2228`) *does* have a real, deterministic
execution order at the implementation level (rule-list position, one
progressing cold-path binding per pass, full-batch application per pass). But
that order is a property of **seed load order** — itself the output of a
topological walk over `depends_on` edges across independently-authored seed
files (CLAUDE.md, "Seeds are modular with dependencies") — and of
same-pass interaction hazards the design explicitly works around rather than
relies on: `seeds/shape_decode_loop.json`'s own comment on `sd_recognize_dim`
(§1.3 below) documents a rule that sets `transform_explained=1` in the SAME
pass another rule (`sd_recognize_transformed`) reads it, and is careful to
note the reader "reads the PRE-effect value" so it cannot double-fire —
exactly the class of same-pass race the "no rule ordering" caution exists to
warn a seed author away from leaning on. **The engine's execution order is
real but not a contract; the "no rule ordering" caution means "do not encode
a dependency as 'my rule runs after yours happens to run' — encode it as a
data precondition,"** which is what the sd loop actually does.

### 1.3 The guard chain is a genuine DAG on monotonic flags, and *that* is what makes the ordering provable

Read directly from `seeds/shape_decode_loop.json`'s rule comments (verified
against the JSON, not just prose): `sd_mint_quantum`'s guard requires
`transform_checked==1 AND transform_explained!=1 AND dim_checked==1 AND
dim_explained!=1` — mint is gated on **both prior rungs having concluded and
failed**, not on any assumption about which rule ran when. `sd_infer_dimension`'s
own comment states the mechanism explicitly: *"Occam order across rungs
… is enforced purely by this guard: only a rung-1 FAILURE … reaches this
rule at all … verified independent of whether the Term is live."* This is not
a hopeful description — it is checkable as a plain fact about the guard
predicates:

- `transform_checked`, `dim_checked` are **monotonic** — nothing in the seed
  ever resets them to 0 except `sd_redecode` on a genuine codebook-growth
  re-arm (`shape_decode_loop.json`, `sd_redecode`'s comment: clears
  `transform_checked`/`transform_explained`/`dim_checked`/`dim_explained`
  together, atomically, as one re-arm event — never independently).
- Every path that could satisfy `dim_checked==1` requires
  `transform_checked==1 AND transform_explained!=1` to have already held
  (either `sd_infer_dimension` itself, or `sd_dim_check_mark`, the
  "resilience marker" that sets `dim_checked=1` when the real `DimInfer` Term
  isn't installed yet — the documented "graceful skip: unavailable is treated
  as tried-and-failed").
- `run_rules` runs to a **fixed point** within one call (`rewrite.rs:2158-2226`,
  `while steps < max_steps { … if !any_progress { return steps } }`) — so
  **given enough steps to reach fixpoint**, any rule whose guard is
  satisfiable *will* fire before the loop returns, regardless of rule-list
  position, because an unfired, satisfiable rule is by definition "progress"
  that keeps the `while` loop going.

Put together: **the guard chain is not "usually checks cheap things first" —
it is a genuine, provable causal DAG, sound under (a) monotonic flags, (b)
fixpoint actually being reached within `max_steps`, and (c) the resilience
markers correctly treating "rung unavailable" as "rung tried and failed."**
This is a *stronger*, more precise finding than the correction section's own
hedge ("pending an audit not performed here") — the audit was performable
from the seed's own guard predicates and the engine's fixpoint contract, and
it comes out sound, not merely plausible.

### 1.4 Where the certificate is honest, and where it is scoped, not merely provisional

The correction section's other caveat — *"provided each rung's own internal
check is itself exhaustive/decidable for its hypothesis class"* — is the
piece that needed reading the Rust, not the seed:

- **Rung 1 (`eval_transform_decode`, `runners/dsl/src/shape_decode.rs:1769-1879`)**
  is exhaustive over its class by construction: `candidates` is built by
  mapping `build_candidate` over **every** held part (`parts.iter().filter_map(...)`,
  line 1799-1801) — no early exit, no truncation. If rung 1 reports
  `explained: false`, that is a genuine "no held shape explains this residual
  as identity + a consistent per-dimension delta," not a sampled negative.
- **Rung 2 (`eval_dim_infer`, `shape_decode.rs:1995-…`)** is *also* exhaustive
  over its declared class — but the declared class is narrower than "every
  possible dimension inference." It tries every `(part, generator)` pair at
  composition length 1, then every `(part, ordered pair of distinct
  generators)` at length 2 (confirmed by direct read: two `for part in &parts`
  loops, each nested with `generators.iter()`, no `.take()`/beam truncation
  anywhere in the function) — and **stops at length 2 by design**
  (`COMPOSITION_DESIGN.md`, cited in the seed's own v1.6.0 changelog:
  "Composition LENGTH is the strict-primary Occam key… a length-2 composite
  can never beat a length-1"). A residual that genuinely requires a
  length-3 composition of held generators is exhaustively *absent* from
  rung 2's search, not merely missed by an accident of pruning — it falls
  through to mint, indistinguishable at the certificate level from genuine
  novelty. **This is a real, honest, currently-real scope limit, not a bug**
  — it is the same Occam-ordering discipline the whole ladder is built on
  (a length-3 composite is, by the ladder's own logic, no cheaper to accept
  on faith than a fresh mint) — but it means the ladder's certificate is
  precisely: *"cost class ≤ 2-generator-composition was exhausted and
  failed,"* not *"every explanation expressible in Γ's generative closure was
  tried."* Anyone citing this ladder as a completeness bound for a
  downstream claim needs the "≤2" clause attached, not dropped.

### 1.5 Verdict

**(b) — sound, not merely plausible, and the soundness is provable from three
stated facts (monotonic flags, fixpoint reachability, graceful-skip
equivalence) plus one honest, scoped exhaustiveness bound (composition depth
≤ 2 at rung 2).** No rewrite is warranted; the value here is that this
document, not the correction section, is now the citable source for *why*
the ladder is trustworthy, with the depth-2 caveat attached so a future
consumer does not silently over-claim it.

---

## 2. Probe 2 — does Γ's `weight` already carry the completeness guarantee, once read as a ratio rather than an absolute cost?

### 2.0 Course correction, stated in the open

The brief for this probe originally asked "what would it cost to bolt an
absolute, admissible, additive cost field onto `Production`, alongside its
existing softmax `weight`." **That framing was wrong, and it was caught
mid-investigation** — restated here because getting this wrong once is
exactly the failure mode this section exists to name. The creator's
correction: *"cost is absolute. a view from nowhere that doesn't exist. there
is only relative weight and exchange. a number means nothing, a ratio means
everything."* This is not a rhetorical objection — it is the **same
invariant** `CLAUDE.md`'s own "BASE-AS-DIMENSION" section states formally
("non-integer math is CROSS-FRAME, never IN-FRAME… the continuum sits in
`Hom(frame, frame)`, not in any object") and the same one its "SHAPES, NOT
NUMBERS" section (2026-08-06/07) found *empirically*, independently, twice in
one week: **60 count-divided (`1/n`) learners across 8 embodied seeds, and
not one of them inside the sd-loop/shape-codebook/spatial-quanta faculties —
"a scalar knob is not a simplification of this — it is the unpaid debt."** An
absolute per-production cost field would have been exactly one more scalar
knob standing in for a shape. §2.1-§2.3 below re-run the probe correctly:
not "what absolute quantity is missing," but "does Γ's existing *relative*
weight structure already deliver the guarantee, once read the right way."

### 2.1 What Γ's `weight` already is, read precisely

`grammar.rs`'s own header (lines 1-8) is exact about this: *"selection over
admitted candidates is `∝ exp(w)`."* That is a statement about a
**log-domain quantity** — `w` is not a probability, it is a log-weight, and
`exp(w)` is only ever meaningful *relative to* the other `exp(w')` at the
same choice point (a softmax has no absolute scale; multiplying every
`exp(w)` by a constant changes nothing after normalization). `checker.rs`'s
`evaluate_weight` (lines 132-155) and `substrate.rs`'s `admissible_moves`
(lines 1740-1788) confirm this is exactly how it is computed: for a
single `(src, edge_type)` choice point, every admitting production's `w` is
evaluated and **summed additively** across productions admitting the *same*
candidate (`total += evaluate_weight(...)`, line 1771) — the comment at
1735-1739 states this matches "Paper §1.2 Definition 2" and explicitly defers
normalization to the caller: *"The caller picks via softmax over these
weights if it wants the Boltzmann selection of Theorem D."* **`admissible_moves`
never normalizes.** It returns raw, summed log-weights per candidate, at
exactly ONE choice point (a single hop) — the caller-supplied `candidates`
argument is not itself a multi-hop structure.

This is directly confirmed as a live pattern elsewhere in the repo, not a
hypothetical reading: `domains/fovea_bridge.py`'s header (lines 21-24) states
the MAP reading explicitly — *"Gamma is the WEIGHTED ADMISSIBILITY grammar;
'selection over admitted candidates is proportional to exp(w)'. The MAP
reading of that is `argmax_w over admissible candidates` = `ArgminUnique(admissible,
Neg(w))`"* — and `fovea_resolve`'s actual selection Term is
`ArgminUnique(Neg(Log(salience)+goal_logweight))`: an **additive sum of two
log-quantities**, then argmin of the negation. This is exactly the Viterbi/
tropical-semiring move (see §2.2), already live in this codebase, for a
**single** decision.

### 2.2 The semiring identity that actually resolves the tension, and where it currently is *not* applied

The creator's ratio-purity point and the A*/Dijkstra additive-cost
requirement are not in conflict, because Dijkstra/A* do not actually require
an absolute cost as a metaphysical category — they require a **commutative
semiring** with the right monotonicity (the algebraic path problem: **Carré,
B.A. (1971), "An Algebra for Network Routing Problems," IMA Journal of
Applied Mathematics 7(3), 273–294**, DOI 10.1093/imamat/7.3.273 — web-verified
this session; **Mohri, M. (2002), "Semiring Frameworks and Algorithms for
Shortest-Distance Problems," Journal of Automata, Languages and Combinatorics
7(3), 321-350** — web-verified this session, correcting the coordinator's
initial venue attribution to *Computational Linguistics*, which is Mohri's
1997 FST paper, a different work). The probability semiring (`×`, then
normalize) and the tropical/shortest-distance semiring (`+`, `min`) are
related by `log`: **maximizing a product of per-step Boltzmann factors
`∏ exp(w_i)` is exactly minimizing a sum `Σ(-w_i)`** — this is the same
identity Viterbi decoding runs on every HMM. Under this reading, Γ's raw,
un-normalized, per-production `w` (exactly what `admissible_moves` already
returns, exactly what `fovea_bridge.py` already sums across two terms for one
decision) **is already the correct log-domain building block for a global,
best-path (A*/Viterbi-shaped) search across a *chain* of admissible edges —
no new field needed, no absolute quantity invented.** `Grammar`/`checker.rs`
would not need to change at all; the change (if made) belongs entirely to
whatever *chains* multiple `admissible_moves` calls into a path.

**Nothing in this repo currently does that chaining.** `load_parts`
(`shape_decode.rs:239-…`) — the sd loop's own codebook reader — pulls its
`ShapeSignature` parts straight from `ctx.graph.nodes_of_type(codebook_type)`,
entirely independent of `Grammar.productions`/`Grammar.index`. **Γ and the sd
loop are architecturally disjoint subsystems in this codebase today**: Γ
governs single-edge admissibility on the live `TypedGraph`; the sd loop
decodes/composes over graph-resident codebook nodes that were never
`Production`s and never pass through `checker.rs` at all. The correction
section's framing — "Γ is the right kind of object to be 'the space' … not
yet unified with the sd loop's own cost-shaped scoring" — is accurate but
undersells the gap: it is not a missing field, it is that **the one
subsystem that actually does multi-step composition (the sd loop / composer)
never calls Γ's checker or `admissible_moves` at all.** Unifying them would
be a real architectural decision (represent sd-loop parts as Γ productions,
or keep them separate and give the sd loop its own admissible cost — see
§2.4), not a one-line field addition.

The **one** existing multi-hop consumer of Γ-admissible structure,
`substrate/weighted.py`'s `weighted_walk` (the "Theorem D weighted-traversal
sampler," `docs/meta/SPEC.md:61`), does the **wrong-for-this-purpose** thing,
though it is not wrong *for its own purpose*: at every step it calls
`rng.choices(keys, weights=weights, k=1)` (`weighted.py`, the `for _ in
range(walk_length)` loop) — a **per-step, LOCALLY renormalized** categorical
draw. This is structurally an MEMM (maximum-entropy Markov model), not a
CRF, in the vocabulary of **Lafferty, J., McCallum, A., Pereira, F. (2001),
"Conditional Random Fields: Probabilistic Models for Segmenting and Labeling
Sequence Data," ICML 2001** (web-verified this session) — and that paper's
own headline finding is the *label bias problem*, first identified by
**Bottou, L. (1991)** (cited within Lafferty et al.; not independently
re-verified this session beyond that secondary citation): locally-normalized
per-step models are **structurally biased toward states with fewer competing
alternatives**, independent of how good those alternatives actually are,
because each step's probability mass is forced to sum to 1 regardless of
branching factor — so summing `-log(p_local)` across steps does **not**
yield a valid, comparable global path score the way summing raw,
un-normalized `-w` does. `weighted_walk` is not *broken* for its actual job
(it is an honest random-walk/coverage sampler, not a best-path finder, and
per-step proportional sampling is exactly correct for that) — but it is the
wrong template to copy if anyone builds a Dijkstra/A*-shaped multi-hop search
over Γ later, and it is currently the *only* precedent in the repo for what
"chaining weight across hops" looks like.

### 2.3 Sharp, checkable answer to the reframed question

*"Does the existing relative weight already deliver this via the standard
log-space semiring map, and does local vs. global normalization decide
whether it actually works?"* — **Yes, and yes, in that order.** The raw
per-production `w` (already what `evaluate_weight`/`admissible_moves` expose,
already summed additively across co-admitting productions for one candidate,
already read this way for one decision in `fovea_bridge.py`) is the correct
quantity, and **it must stay un-normalized (or be normalized exactly once,
globally, over complete paths — a CRF-shaped partition function) to remain
composable across a multi-hop path.** The natural-looking
implementation — chain per-step local softmax draws and treat their
log-probabilities as additive, the `weighted_walk` shape — is precisely the
one the label-bias literature rules out. There is no absolute-vs-relative
conflict to resolve by invention; there is an existing relative quantity
(`w`) that is already correctly shaped, and one architectural decision not
yet made anywhere in this codebase: **build the multi-hop consumer as a
Viterbi/best-first accumulator over raw `w` (sound), not as a chain of
locally-renormalized draws (label-biased, and currently the only precedent
that exists).**

### 2.4 Connective tissue, named plainly per this project's own convention

This is the **third** independent restatement of one thesis this repo already
holds, not a new one: `docs/research/engine_substrate/
COGNITION_IS_PHYSICS_LITERATURE.md` §4's own verdict ("cognition and physics
are the same process, differing only by frame… a re-derivation of Geman &
Geman, Jaynes, the Free Energy Principle, Still–Sivak–Crooks — a
demonstrated instantiation, not a discovered theorem"), the
`PROBLEM_DIFFICULTY_QUANTIFICATION_LITERATURE.md` correction's own framing
("the continuum sits in `Hom(frame, frame)`, not in any object"), and
`CLAUDE.md`'s "SHAPES, NOT NUMBERS" empirical finding (three independent
embodiments, same week, same failure: a bare scalar standing in for a shape)
are the same claim in three vocabularies: **physics/frame-relativity,
in-frame-integer/cross-frame-real, and shape-not-number.** This probe adds a
fourth: **search/ratio-relativity** — a path "cost" is not an absolute
quantity Γ is missing, it is a *cross-frame comparison* (a log-ratio between
alternative continuations), and the semiring identity in §2.2 is the formal
shape that makes "in-frame is a relative preference, cross-frame composition
is where the additive structure lives" precise rather than metaphorical.

### 2.5 A named tension, and one already-measured instance of each side, in this exact repo

Ratio-purity has a real, structural cost the creator named directly:
*"ratios also mean that hysteresis becomes almost impossible."* This is
true, precisely: hysteresis (a response depending on history, not only
current state) needs *something* to persist as an anchor across the
comparison; if every decision is a **fresh** ratio against current state
with nothing stored, two moments with an identical current ratio must
produce an identical response, and the "stickiness" that defines hysteresis
has nowhere to live.

**This repo has already measured both the accidental and the deliberate
version of this exact tension, on the F-16 embodiment line — the accidental
case is the sharper, primary citation.**
`docs/research/flight_control/HANDOFF_embodied_adaptation.md:111-117`
(standing rules "learned the hard way," written as a retrospective after the
line's blocks accumulated) states it almost verbatim as a diagnosis, not a
hypothesis:

> *"5. Hysteresis is a sign you scaled wrong. A budget suppressing a trigger
> that fires 93% of the time is hysteresis. Fix the scale, delete the budget.
> 6. A fixed absolute constant against a multi-scale quantity is the
> recurring bug… Ratios and log buckets, not constants."*

Read plainly: this project's own prior, hard-won experience is that
**hysteresis, when it shows up as a budget/threshold suppressing an
absolute-constant-vs-multi-scale-signal mismatch, is a code smell — the fix
measured every time was to correct the scale (make the trigger fire at the
right rate on its own) and delete the hysteresis machinery entirely, not to
tune the hysteresis better.** This is a stronger claim than "hysteresis is in
tension with ratio-purity" — it is "in this repo's own measured experience,
the accidental kind of hysteresis was never the right fix."

A second, independently-discovered instance of the *identical* mechanism
lives in `docs/research/program_synthesis/PROGRAM_SYNTHESIS_ARC6_IMPOTENCE_CAMPAIGN.md`
§8 ("THE DISCOVERED, UNREGISTERED FINDING: THE STORED VERDICT FREEZES AT
MINT," lines 344-401): `ax_impotent`'s `AgendaVerdict.nearest_unroutable_kind`
is computed once, at mint, and **never re-derived** as the live pool ranking
continues to drift under a constant pool signature — measured directly, both
collapses, reproduced twice: the *live* winner moves
(`supply_blocker → supply_blocker → source_claim → source_claim → source_claim`)
while the *stored* verdict stays frozen at `supply_blocker` throughout. This
is the SAME shape as the F-16 lesson — an absolute value cached from a
ratio/comparison and never rechecked against the thing it was a snapshot of —
found independently, in a different subsystem, and it is exactly what rule 5
above diagnoses: not a legitimate hysteresis mechanism, a scale/staleness
bug wearing hysteresis's clothes.

**The other side of the tension is also real, and this repo has a
deliberately-built instance, not just a hypothetical one — worth checking
plainly whether it agrees or conflicts with the HANDOFF lesson, rather than
assuming either way.** `docs/research/flight_control/
regime_pareto_frontier_prereg.md`, "Block X2 — hysteresis on the stop (f16
v8.47.0)," lines 2192-2201, is an **intentionally asymmetric** activate/
deactivate latch: *"the stop now reads how long quorum has HELD … and
activates only past the loop's own `regime_evidence_horizon_actions`. A
separate `f16_release_probe_stop` clears the flag on a single action of the
condition not holding — deliberately asymmetric activation and deactivation
energy, because nothing is permanent: a jammed effector can free itself."*
Its threshold is not an arbitrary absolute constant plucked from nowhere — it
is set against a **measured, sharply bimodal** separation ("quorum holds for
1 action at most under a damaged wing … and 882 contiguous under a jammed
rudder," an ~880× gap), and `seeds/arc_executor.json`'s `ax_rearm` rule (the
same lineage's own anti-oscillation latch, checked directly against the
seed) has the identical shape: its guard is `stale==1` (a **live**,
freshly-re-derived condition, never a cached snapshot) **AND**
`retired_epoch != <live current epoch, fetched via a fresh Argmin over
ResidualFact each evaluation>` — a *stored timestamp compared relationally
against a live counter*, never a stored value substituted for live truth.

**Reading both together, honestly, rather than forcing one verdict:** Block
X2 was authored at v8.47.0, the HANDOFF's "standing rules" are a later,
distilled retrospective covering the whole line (it references blocks up to
at least v8.51.0) — so this is not a case of an earlier lesson being ignored
by a later mechanism; if anything, Block X2 predates the rule that would
indict *naive* hysteresis, and it does not fit that rule's own target
pattern. **The two citations do not conflict, because they are not the same
shape of hysteresis:** rule 5/6's target is a hysteresis mechanism built from
an **absolute constant compared against a raw, multi-scale, badly-scaled
signal** (the F-16 line's repeated, measured bug); Block X2's stop and
`ax_rearm`'s re-arm are both **a stored reference *anchor* (a duration held,
an epoch retired-at) compared relationally against a live-recomputed
counterpart** — the stored quantity is never presented as current truth on
its own, it only ever means something as one side of an ongoing live
comparison. This is functionally the ratio-native resolution the creator's
own follow-up question gestured at ("comparing a current ratio … against a
ratio involving the system's own recent trajectory") without needing an
exponential-moving-average construction specifically: **the anchor doesn't
have to be "the truth," it has to be "the state at a boundary crossing,"
checked live every time, not cached and trusted.**

**Honest verdict on this named tension:** it is real, and it is not fully
resolved by this document, but it is not a hopeless structural cost either.
The distinguishing, checkable test this repo's own two examples supply for
free: *does the stored quantity ever get compared against a live-recomputed
counterpart (relational — hysteresis-compatible, `ax_rearm`'s shape), or does
it get read back and presented as current truth with no live check ever
performed (absolute-snapshot — hysteresis-incompatible, `ax_impotent`'s
bug)?* A future Γ-weight-chaining implementation (§2.2-§2.3) that wants
deliberate stickiness (e.g., not re-litigating a committed partial path every
tick) should be checked against this test before being built, not designed
from a fresh absolute threshold.

---

## 3. Probe 3 — the composer's beam search, specifically

### 3.1 Locating and correcting the pointer

The correction section pointed at *"roughly lines 1240-1340"* in
`shape_decode.rs` for `BeamState`/the composer loop and flagged that file
paths/line ranges shift. Corrected, read directly: `struct BeamState` is
declared at `shape_decode.rs:1016-1024`; the full `eval_shape_decode`
function (the `ShapeDecode` Term evaluator — this **is** the composer, not a
wrapper around it; `domains/reflective_faculty.py::compose_design_for_goal`,
lines 7129-7138, is a **thin shim** that builds the Term JSON and evaluates
it once, explicitly documented as carrying "NO Python decision over the
composition") spans lines 1202-1369. The per-state candidate truncation is
`.take(cand_w)` at line 1286; the cross-state beam prune is lines 1317-1336,
specifically the `if pruned.len() >= beam_w { break; }` at line 1332, after a
`sort_by` on `(coverage DESC, total_fit DESC)` (lines 1319-1323). **Two
separate truncation points exist, not one**: `cand_k` bounds how many
children a single state may spawn per step; `beam_w` bounds how many states
survive across the whole frontier per step. Either can discard a state that
would have led to the optimal (or the only) covering plan; §3.3's
construction exercises the `beam_w` one specifically, since it is the one
named in the correction section.

### 3.2 Why beam, not best-first — searched for a measured reason, found an honest null plus a real counter-precedent

No design doc, commit message, or code comment in this repo states a
measured reason `compose_design_for_goal`'s beam width was chosen over an
unbounded or best-first search **for this specific composer**. The repo's
git history is shallow (17 commits on this checkout — a squashed/re-based
history, not archaeologically useful) and a targeted search
(`git log --all -i --grep beam`, and a full-text search of every
`docs/research/program_synthesis/*.md` for "beam") surfaces no
composer-specific rationale. `beam=3, max_steps=8, cand_k=3` in
`compose_design_for_goal`'s signature (`reflective_faculty.py:7129-7130`) read
as inherited defaults from the pre-migration Python implementation, not as
numbers derived from a measured search-space-blowup finding.

**What *is* found, and it argues in the opposite direction:** this exact
codebase, facing the identical beam-vs-more-complete-search tradeoff for a
sibling problem, chose the other side. `docs/research/program_synthesis/
PROGRAM_SYNTHESIS_P4A_NOTES.md`'s port-fidelity table (§2, "beam (legacy
unguided width cap)") records, for the `SynthEnumerate` program-synthesis
enumerator: **`NO — dropped`, "dead weight the guided path superseded."**
`SynthEnumerate` (`runners/dsl/src/synth_enumerate.rs`) instead runs
**exhaustive, size/MDL-ordered bottom-up enumeration with
observational-equivalence pruning and a count budget** (`max_candidates`,
default 200,000) in place of a width cap — explicitly because "wall clocks
are not in-frame integers" (the same integer/frame discipline as §2.4) and
because a fixed beam is "legacy" relative to the exhaustive-plus-pruning
shape. **There is no evidence this tradeoff was ever measured specifically
for the composer** — but there is direct, in-repo evidence that when the
project *did* measure it (for the neighboring enumerative-synthesis problem),
it moved away from beam-width capping, not toward it.

### 3.3 A minimal, constructed, live-verified demonstration that the gap is real

Per the task's read-only discipline, a standalone, non-mutating probe script
(`scripts/probe_beam_completeness.py`) was written and run — it touches
nothing under `seeds/`/`domains/`/`runners/`, builds a throwaway in-memory
substrate via the same `boot_core()` + hand-built `ShapeSignature` harness
`tests/test_transform_decode_migrated.py` already uses, and calls the real
`compose_design_for_goal` (hence the real `ShapeDecode` Term, the real
`eval_shape_decode`) three times at different beam widths. Runtime: well
under one second.

**Construction** — a miniaturized transplant of the classic
greedy-set-cover adversarial example (Johnson 1974 shape) onto the beam:
four relations `g1, g2, g3, g4`; an **optimal** 2-part, 2-step cover
(`part_A = {g1,g2}`, `part_B = {g3,g4}`, disjoint); and a **greedy** part
(`part_C = {g1,g3}`) that ties `part_A`/`part_B` on coverage (`ncov=2`) at
step 1 and wins the fit tie-break by construction (its signature is
position-aligned with the residual — exactly `shape_fit`'s own
position-aligned-anti-unification rule, `shape_decode.rs:1026-1045`), then
needs two more single-relation steps to finish (no part covers `{g2,g4}`
together). At `max_steps=2` (the optimal's own step count):

```
beam=1:  ordered_parts=[part_C, part_B]   covered=3/4  residual=[g2]   "authored": true
beam=2:  ordered_parts=[part_A, part_B]   covered=4/4  residual=[]     "authored": true
beam=3:  ordered_parts=[part_A, part_B]   covered=4/4  residual=[]     "authored": true
```

**Verified live, this session.** `beam=1` silently returns an *incomplete*
covering plan, flagged `"authored": true` with no signal distinguishing it
from a certified result — the exact failure mode the correction section
named, reproduced deterministically from five hand-authored `ShapeSignature`
nodes and two lines of goal construction, not a contrived edge case
requiring an adversarial search. This does not measure how often the gap
bites on organic, seed-grown codebooks (a materially harder, much larger
question the task explicitly scoped out as "not a battery") — it measures
that the gap is **trivially, cheaply, deterministically constructible**,
which bears directly on how much weight "it hasn't come up" should be given
if it hasn't been looked for.

### 3.4 Is a wider or adaptive-width beam a realistic middle ground, or does this need a genuine rewrite?

Given §3.2's in-repo precedent, the realistic middle ground is not "beam,
just wider" — width alone does not change the *kind* of guarantee available,
only the probability of tripping over the failure mode in practice (and
`max_candidates`-style budgeting already has a working, named precedent in
this exact codebase for the sibling problem). Three concretely different
options, not collapsed into one:

1. **Wider fixed beam.** Cheap, zero design risk, does not change the
   guarantee's *kind* — `beam_w` large enough to be "effectively exhaustive"
   for the goal sizes actually encountered trades away exactly the
   tractability the architecture exists to buy (correction section's own
   language), and §3.3's construction generalizes to arbitrarily wide beams
   with proportionally larger adversarial instances (the classic
   greedy-set-cover gap is `Θ(log n)`, not bounded by a constant).
2. **`SynthEnumerate`'s shape, transplanted: exhaustive size/MDL-ordered
   search + observational-equivalence-style pruning + a count budget.** This
   has a real, working precedent in this exact codebase for a structurally
   similar composition problem, and would turn "nothing found" back into a
   genuine certificate (§1's rung-1/rung-2 shape) rather than a
   width-dependent heuristic result. Cost: a real rewrite of
   `eval_shape_decode`'s search loop, not a parameter change, and the
   "observational-equivalence" half needs its own definition for shape
   composition (what makes two partial covering-plans equivalent enough to
   dedupe) — not automatically inherited from the program-synthesis case.
3. **True best-first, admissible-heuristic-driven (Ameen & Lelis's
   shape, already cited by the correction section).** The
   theoretically clean answer, and the one that would let Probe 1's
   rung-ladder-style certificate extend to the composer — but it needs an
   actual admissible heuristic over partial covering-plans (a lower bound on
   remaining cost-to-full-coverage), which does not currently exist anywhere
   in this codebase and is not free to invent (§2's finding: the natural
   candidate quantities — `shape_fit`, `weight` — are reward-shaped, not
   cost-shaped, by construction; see §3.5).

### 3.5 A related finding, worth flagging even though it wasn't explicitly asked for

`eval_shape_decode`'s own objective (`(coverage DESC, total_fit DESC)`,
lines 1319-1323, 1308) optimizes coverage then **greedy per-step fit** — it
does **not** optimize plan parsimony (fewest parts) at all. `plan.len()` is
tracked (it is literally the `step` counter on each `PlanStep`) but never
used as a ranking key. This means CLAUDE.md's own "as few as possible, but no
fewer" MDL principle — stated repeatedly as the governing pressure behind the
sd loop's codebook growth — is **not currently an objective the composer's
own search optimizes for**; a full best-first rewrite (option 3 above) that
reused the *current* scoring key verbatim would still not deliver an
MDL-parsimonious plan, only a maximum-coverage, greedy-fit one. This is a
distinct gap from the beam-completeness one (it is about *what* is being
optimized, not *whether* the optimum is reliably found) and is named here
because any future work on this search should not assume fixing beam-width
completeness also fixes MDL-parsimony — they are orthogonal.

### 3.6 Verdict

**(b) — a real design decision, not a free win and not speculative.** The
gap is real (proven constructively, §3.3), this exact codebase has already
made the opposite tradeoff for a sibling problem and called the beam-capped
version "dead weight" (§3.2), and a genuine best-first fix needs a currently
nonexistent admissible heuristic (§3.4, option 3) while the cheaper
`SynthEnumerate`-shaped alternative (option 2) is a real rewrite, not a
parameter tune. No measurement exists of how often this bites organically
grown codebooks — that would be the natural next rung, not attempted here.

---

## 4. Consistency check against `ADVENTURE_MECHANICS_COMBINATION_GRAMMAR.md`

That document's own §3.2 already states, independently, the same
architectural fact this probe found the hard way in §2.2: it describes
admission as "an N-dimensional shape solve… not a sequential ladder," reads
Γ's `Production` as "(src-pattern, edge-type, tgt-pattern, where, weight)"
(§2.4, quoting `grammar.rs` directly), and never assumes `weight` is or
should become an absolute cost — its own MDL discussion (§3.2, citing this
repo's P3→P7-C precedent) treats compression pressure as something measured
per-domain, not derived from a stored absolute quantity, which is the same
posture this document arrives at in §2.3. **No tension found.** One place
this probe sharpens that document rather than merely agreeing with it:
§3.4's proposed production-retraction primitive (tombstone + `gamma_epoch`
bump) would, if built, be exactly the kind of stored-anchor-compared-live
pattern §2.5 above identifies as hysteresis-compatible — a retracted
production's tombstone is a boundary-crossing record, not a cached verdict,
provided (per that document's own §3.5 open question) the retraction unit is
scoped correctly. Worth a forward-reference if that document is picked up
for a build.

---

## 5. What this document does not resolve

- **How often Probe 3's beam gap bites organically-grown, seed-produced
  codebooks** (as opposed to the constructed adversarial case) — not
  measured; would need a real rung against live fixture data, explicitly out
  of scope here per the task's own "probe, not a battery" instruction.
- **Whether a Γ-chained multi-hop best-path search (§2.3) is worth building
  at all** — this document establishes it would be *sound* if built the
  right way (global/un-normalized log-domain accumulation), not that
  anything currently needs it; no consumer in this codebase currently wants
  a multi-hop admissible path search over Γ.
- **The MDL-parsimony gap named incidentally in §3.5** — flagged, not
  designed.
- **A general admissible heuristic for partial shape-covering plans** (§3.4
  option 3's prerequisite) — named as the actual missing piece for a true
  best-first composer rewrite, not designed here.
- **The retraction-unit question `ADVENTURE_MECHANICS_COMBINATION_GRAMMAR.md`
  §3.5 already leaves open** — this document's §4 only checks consistency,
  it does not resolve that document's own open question.

---

## Bibliography

- Alur, R. et al. (2013). "Syntax-Guided Synthesis." FMCAD 2013. (via the
  correction section; not re-verified independently this session.)
- Ameen, S., Lelis, L.H.S. (2023/2024). "Program Synthesis with Best-First
  Bottom-Up Search." *JAIR*; AAAI 2024 abstract reprint, arXiv:2310.04327.
  (via the correction section.)
- Bottou, L. (1991). Doctoral thesis (label bias problem, original source).
  Cited within Lafferty et al. 2001; not independently re-verified beyond
  that secondary citation this session.
- Carré, B.A. (1971). "An Algebra for Network Routing Problems." *IMA
  Journal of Applied Mathematics* 7(3), 273-294. DOI: 10.1093/imamat/7.3.273.
  Web-verified this session (title, venue, volume/issue/pages, DOI all
  confirmed via search).
- Hart, P.E., Nilsson, N.J., Raphael, B. (1968). "A Formal Basis for the
  Heuristic Determination of Minimum Cost Paths." *IEEE Trans. Systems
  Science and Cybernetics* 4(2), 100-107. (via the correction section.)
- Johnson, D.S. (1974). "Approximation Algorithms for Combinatorial
  Problems." (Greedy set-cover approximation ratio; canonical, not
  independently re-verified this session — the adversarial construction used
  in §3.3 is this document's own miniaturization of the well-known shape,
  not a transcription of Johnson's specific example.)
- Lafferty, J., McCallum, A., Pereira, F. (2001). "Conditional Random
  Fields: Probabilistic Models for Segmenting and Labeling Sequence Data."
  ICML 2001. Web-verified this session (title, authors, venue, and the
  label-bias-problem attribution to MEMMs vs. CRFs all confirmed via
  search).
- Mohri, M. (2002). "Semiring Frameworks and Algorithms for Shortest-Distance
  Problems." *Journal of Automata, Languages and Combinatorics* 7(3),
  321-350. Web-verified this session, correcting the coordinator's initial
  attribution to *Computational Linguistics* (that is Mohri's 1997 FST
  paper, a related but distinct work).

**In-repo sources cited directly** (file paths and line numbers given inline
throughout, not repeated here): `runners/dsl/src/grammar.rs`,
`runners/dsl/src/checker.rs`, `runners/dsl/src/substrate.rs`,
`runners/dsl/src/shape_decode.rs`, `runners/dsl/src/rewrite.rs`,
`runners/dsl/src/synth_enumerate.rs`, `substrate/weighted.py`,
`domains/fovea_bridge.py`, `domains/reflective_faculty.py`,
`seeds/shape_decode_loop.json`, `seeds/arc_executor.json`, `docs/meta/SPEC.md`,
`CLAUDE.md` ("SHAPES, NOT NUMBERS," "BASE-AS-DIMENSION"),
`docs/research/engine_substrate/COGNITION_IS_PHYSICS_LITERATURE.md`,
`docs/research/problem_difficulty/PROBLEM_DIFFICULTY_QUANTIFICATION_LITERATURE.md`,
`docs/research/adventure_mechanics/ADVENTURE_MECHANICS_COMBINATION_GRAMMAR.md`,
`docs/research/program_synthesis/PROGRAM_SYNTHESIS_P4A_NOTES.md`,
`docs/research/program_synthesis/PROGRAM_SYNTHESIS_ARC6_ARC_GOALS.md`,
`docs/research/program_synthesis/PROGRAM_SYNTHESIS_ARC6_MAGNITUDE.md`,
`docs/research/program_synthesis/PROGRAM_SYNTHESIS_ARC6_IMPOTENCE_CAMPAIGN.md`,
`docs/research/flight_control/HANDOFF_embodied_adaptation.md`,
`docs/research/flight_control/regime_pareto_frontier_prereg.md`.
