# τ-hierarchy axis map — PREREGISTRATION

**Date:** 2026-08-11
**Status:** REGISTERED. Written after reading `paper1.tex` in full (focus:
"Recursion hierarchy of phase transitions," §"Strict ordering"), after Part
A's historical check completed, after reading
`docs/research/engine_substrate/GAMMA_SEARCH_COMPLETENESS_CEILING.md` and
`docs/research/theory_convergence/THEORY_CONVERGENCE_AUDIT.md`, and after
locating the real mechanisms this rung builds on — **before** any measurement
below was run.
**Worktree:** `/home/matt/ocelot-tau-hierarchy`, branch `tau-hierarchy-review`,
base commit `80f353e` (verified == `main`'s tip at task start).
**Engine:** sha256
`c5e50801d48a170d3f16f2320f1e35eac355e0552a798faa9026d16bbbaaf567`
(`runners/dsl/python/substrate_rs/_native.abi3.so`, checked out with the
worktree, resolves from inside it). Coherence probe passed:
`add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` reads back `[1,2,3]` (list)
and `(1,2,3)` (tuple) distinctly. This is the same engine sha the most
recent landed rung (`PROGRAM_SYNTHESIS_ARC6_MG4_DECOMPOSE.md`) used — no
rebuild needed.

---

## 0. What changed the scope of this rung, mid-flight

The task began as a single question: does the paper's claimed strict order
τ3 ⇒ τ2 ⇒ τ1 ⇒ τ0 hold, or is it backwards for the τ2/τ3 pair (creator's own
flag: "the difference is the ability to meta model the law itself,
perhaps")? Two messages from the creator arrived while this document's
predecessor design was being drafted and are load-bearing for everything
below, quoted because the exact wording matters:

> "yes - t3 is weak. what i want to do is map axes and work out what should
> be correct. for example i have been operating at a t3 context more or less
> my entire life - i was only recently *aware* that i was doing so, and what
> the difference was... and also built this."

> "yes. my contention that this is a fundamental phase transition stands, i
> just want to be explicit about *what* is transitioning."

Two consequences, both binding on this document:

1. **The question is no longer "is the τ2/τ3 order reversed" alone.** It is
   "is the four-level LADDER the right shape at all, or does it conflate
   genuinely orthogonal axes" — with the creator's own anecdote naming the
   missing distinction directly: a long period of *functionally* operating
   according to a law, followed by a later, separate event of becoming
   *explicitly aware* of the law as an object one can inspect and reason
   about. §1 grounds this in the cognitive-science literature that already
   has a name for it (Karmiloff-Smith's representational redescription) and
   §2 states the corrected axis map this rung tests.
2. **The phase-transition claim is not in question and this document does
   not weaken it.** What is in question is precision: τ1 already states its
   order parameter as a crisp, boolean, graph-structural fact (the meta-Γ
   production subset is non-empty or it isn't — φ jumps). τ3 as written
   ("awareness of the graph law") describes the *effect*, not the *order
   parameter*, in that register. §2 states an order parameter for the
   corrected axes with the same crispness τ1 already has, and §3-§5
   register bars that test it mechanistically (via a perturbation test, not
   a description).

---

## 1. Grounding the implicit → explicit distinction (verified via search this
session, not asserted from recall)

- **Karmiloff-Smith, A. (1992). *Beyond Modularity: A Developmental
  Perspective on Cognitive Science*. MIT Press.** The Representational
  Redescription (RR) model. Core content, confirmed via search (multiple
  independent secondary sources, including the MIT Press book page and a
  2011 paper specifically on the implicit-explicit dimension of the model):
  development proceeds through levels **Implicit (I) → E1 → E2 → E3**.
  At level I, a procedure is successful — behaviourally mastered — but
  encapsulated: not accessible to other parts of the cognitive system, not
  available for verbal report, not flexibly re-usable outside the context
  it was acquired in. **Redescription** is the process by which that
  implicit procedural knowledge is re-represented in a progressively more
  explicit, more manipulable, eventually verbally reportable form (E3). The
  point load-bearing for this rung, stated directly in the secondary
  literature: *"the simple dichotomy between implicit and explicit
  knowledge fails to fully explain why children and adults can perform a
  task with increasing awareness and efficiency before they are able to
  completely understand and explain their success"* — i.e. successful
  performance (I-level competence) and the ability to explain/flexibly
  apply that performance (E-level redescription) are separable, and the
  separation is the whole point of the model, not an edge case of it.
- **Flavell, J.H. (1979). "Metacognition and cognitive monitoring: A new
  area of cognitive-developmental inquiry." *American Psychologist*, 34,
  906-911.** Confirmed via search (ERIC, SciRP, Semantic Scholar all agree
  on the citation). Distinguishes **metacognitive knowledge** (beliefs
  about oneself and others as cognitive processors, and about what
  influences a cognitive task) from the object-level cognitive strategy
  itself — a system can deploy a strategy effectively with zero
  metacognitive representation of having, or how it uses, that strategy.
- **Anderson, L.W. & Krathwohl, D.R. (eds., 2001). *A Taxonomy for
  Learning, Teaching, and Assessing: A Revision of Bloom's Taxonomy of
  Educational Objectives*. Longman.** Confirmed via search. Adds a
  **metacognitive knowledge** dimension explicitly separate from factual /
  conceptual / procedural knowledge — i.e. even mainstream educational
  taxonomy treats "knowing how to do X" and "knowing about, and being able
  to reason over, one's own strategy for X" as two different dimensions,
  not two levels of the same one.

All three sources converge on the same structural point: **implicit
competence and explicit, reasoned-over self-representation are separable,
and one can precede the other by a long margin** — exactly the creator's own
report. None of the three literatures collapse this into the *comparative*
(self-vs-other) axis at all; comparison to another agent/system is absent
from all three as a component of the implicit→explicit distinction. That
absence is itself evidence for treating comparison as an independent axis,
not a further rung on the same implicit→explicit ladder — tested directly in
§5/§6 below (TAU-ORTHO), not merely asserted from the literature.

---

## 2. The corrected axis map (stated in advance of measurement)

Four axes, replacing the paper's single four-level ladder. Each is given an
order parameter in the same register as τ1's own: **a boolean,
graph-structural (or graph-mechanistic) fact**, not a description of felt or
functional awareness.

| axis | question | order parameter (boolean, structural) |
|---|---|---|
| **Axis 0** (= paper's τ0, unchanged) | Do admissible operations compose transitively? | φ(Γ) = fractional giant-component size of the admissibility composition graph A(Γ); φ jumps at the percolation threshold p_c (paper's own definition, §"Phase transitions in Γ"). Not re-derived here — out of scope, uncontested by the creator's framing request, and `THEORY_CONVERGENCE_AUDIT.md` §5 already reports it as an honest null for independent corroboration (a prior finding, cited not repeated). |
| **Axis R(X)** ("Representable") | Does a subgraph representing content X exist, reachable by *some* Π operation (query/traversal)? | φ_R(X) = 1 iff ∃ a typed subgraph ℓ_X ⊆ G such that some Π-primitive can observe/query ℓ_X. This is Axiom 3's literal content, applied to a specific X. Necessary, not sufficient, for either of the paper's stated payoffs. |
| **Axis O(X)** ("Operative") | Does a decision-RULE actually read ℓ_X to compute its output, such that perturbing ℓ_X's content causes a corresponding, predictable change in the decision? | φ_O(X) = 1 iff ∃ a rule/Term evaluation r such that (a) r's computation reads ℓ_X's attrs as an input, and (b) a controlled edit to ℓ_X's content produces the predicted corresponding change in r's output (the causal/mechanistic test, not a coincidental correlation). This is the sharp threshold — it is what delivers τ2's stated payoff ("operable... target competitive parity") and τ3's stated payoff ("directed... search") respectively, when X = Γ_other or X = the law/bound-theorem content. |
| **Axis C** (= paper's τ2, "Comparative") | X = a foreign system's grammar Γ_other. | φ_R(Γ_other) and φ_O(Γ_other), tested independently in §3/TAU-C. |
| **Axis L** ("Nomological/Law", subsumes and sharpens the paper's τ3) | X = the system's own law/bound-theorem content (here: the sd-loop's real Occam/MDL growth discipline). | φ_R(law) and φ_O(law), tested independently in §4/TAU-L. |

**The corrected claim under test, stated before measuring:** the paper's
strict ladder τ3 ⇒ τ2 ⇒ τ1 ⇒ τ0 packs at least two independent distinctions
into one ordinal scale — (i) *which content* is represented (comparative,
Axis C, vs nomological, Axis L — plausibly orthogonal subject matter) and
(ii) *how deeply* that content is represented (merely queryable, Axis R, vs
causally wired into a decision, Axis O — plausibly orthogonal to which
content it is). If Axis C and Axis L can each be crossed (R and O) with
constructions that share no graph content and no code path, and Part A's
historical check shows no clean C-before-L or L-before-C ordering in this
repo's own history, that is a positive existence proof that the ladder shape
is wrong and a 2×2 (content × depth) shape fits the evidence better. The
phase-transition character itself (each crossing is a discontinuous,
boolean, first-order-style jump — R is either true or false for a given X,
O is either true or false for a given r) is NOT in question and is expected
to replicate on both axes; only the *ordering/nesting* claim is under test.

---

## 3. Historical check (Part A) — already run, reported here for reference

Run before this document, as orienting evidence. Using
`gh api repos/ozmalabs/internal/commits?path=research/experiments/gamma-substrate`
(paginated, ~800 commits, 2026-06-30 through 2026-08-10) plus local
`git log`: local `ocelot` history is a single squashed import
(`26ca9ff`, 2026-08-10) and gives no sub-commit chronology. The private
repo's granular history shows, by real commit date:

| date | SHA | shape |
|---|---|---|
| 07-02 | `284547822a`/`518706ed92`/`65f94b70c4` | Axis-L-shaped: sd-loop MDL/Occam growth ladder lands, "growth ladder is complete" |
| 07-06/07 | `d07827bda3`, `e967b4e60a`, `bd0d227e30` | Axis-C-shaped: character ToM (Sally-Anne belief/world split) |
| 07-08/12 | `c8119d387e`, `8a4e3094e5` | Axis-L-shaped (self-account/gap-awareness, a *different* nomological flavour than the growth ladder) |
| 07-28 | `f7e8088bfa`, `1a88dc753f` | Axis-C-shaped again: bigville "ShapeDecode-ToM" |

Reading, reported honestly: **L → C → L → C**, interleaved, not a clean
before/after in either direction. This is corroborating, not decisive
(local history cannot independently confirm the private repo's dates;
"character ToM" is a looser match to the paper's Γ_other than the MDL
ladder is to bound-theorem content). It is registered here as evidence
consistent with axis-orthogonality (interleaving is what independent axes
would produce; a strict ladder would produce a clean before/after), not as
its own gated bar.

---

## 4. TAU-C — the comparative axis (old τ2), operability

**Mechanism.** `domains/reflective_faculty.py::compose_design_for_goal`
(the real `ShapeDecode` Term, `runners/dsl/src/shape_decode.rs`) over
`ShapeSignature` codebook nodes — the same harness
`tests/test_transform_decode_migrated.py` and
`scripts/probe_beam_completeness.py` already use. Two disjoint codebooks are
installed as typed graph data in one substrate, tagged `owner="self"` /
`owner="other"` — this **is** the paper's own τ2 mechanism (Theorem C's
type-vocabulary extensibility applied to a foreign-Γ namespace), not a
metaphor for it. For a battery of synthetic goal instances, ρ_self(I) and
ρ_other(I) (the paper's own operational proxy, §Notation: `ρ(I) =
|G_Γ(I)|/|I|` — here, `len(ordered_parts)` from a real `compose_design_for_goal`
call restricted to each codebook via `exclude`, or a fixed penalty when
`residual` is non-empty) are computed **live**, not fabricated.

**The decision task, and why it is not trivially "read off the smaller
number."** Three actions are available per instance: (a) ENCODE-SELF
(cost = ρ_self, or a large no-coverage penalty), (b) ADOPT-OTHER (pay a
one-time adoption cost `A`, then use whichever codebook is cheaper), (c)
MINT (pay a one-time cost `M`, representing genuine self-directed growth —
no foreign content required at all). **`A` and `M` are drawn independently
of the ρ_self/ρ_other gap**, from a fixed, pre-registered distribution
(uniform over a range set so it straddles the typical gap size — stated
before generating instances, not tuned after). This is the operational
proxy for "content that says what the ratio *means* for capability"
(bound-theorem content) as distinct from "the ratio itself" (comparative
content) — explicitly labelled as a constructed proxy, not a claim to be
executing Theorems X/XI/XII literally (those are stated over abstract
Kolmogorov/compute quantities this codebase does not implement as a
callable module).

**TAU-C-a (the sharp bar).** Because `A`/`M` are independent of the
ρ-gap by construction, the *true* cost-minimising action is not a
deterministic function of the ratio alone. Compute, for a battery of
N ≥ 30 instances: (i) the TRUE optimal action (computed with full
knowledge of ρ_self, ρ_other, A, M — the "Axis-C-and-cost-informed"
decision-maker); (ii) the best possible ratio-only decision rule (any
threshold on `r = ρ_self/ρ_other`, calibrated with an oracle-optimal
threshold fit *on this same battery* — maximally steelmanned, not a weak
strawman). **CONFIRMS the suspected flaw** (bare comparative content is
representable but not operable for this decision) if the ratio-only rule's
match-rate to the true optimum is **no better than the best fixed-action
baseline** (always ENCODE-SELF) by more than a small margin (< 10
percentage points, chosen in advance as "not a real advantage" given
N≈30-50). **DISCONFIRMS it** (supports the paper's claim that τ2 alone is
operable) if the ratio-only rule matches the true optimum reliably better
than the fixed baseline (≥ 20 percentage points, chosen in advance as "a
real advantage"). **NULL** if the result falls in the 10-20 point gap, or
if `A`/`M`'s independence turns out not to actually decouple the ratio from
the optimal action (checked directly: correlation between `r` and the true
optimal action across the battery) — reported honestly as inconclusive, not
forced.

**TAU-C-b (control/witness — should succeed).** A second battery where `A`
and `M` are constructed to be *proportional* to the ρ-gap (a simple, known
relationship) rather than independent of it. Here the ratio-only rule
**should** match the true optimum well (≥ 80%) — this is the positive
control proving the harness and decision framework are sound (the finding
in TAU-C-a, if it lands, is about decoupled cost content specifically, not
an artifact of the battery or the decision framework being broken).

---

## 5. TAU-L — the nomological/law axis (old τ3), representable vs operative

**Mechanism, and why this exact one.** The sd-loop's rung-ordered growth
ladder (`recognize → transform → infer-dimension → mint`,
`seeds/shape_decode_loop.json`, Rust `shape_decode.rs`) is, per
`GAMMA_SEARCH_COMPLETENESS_CEILING.md` Probe 1 (already landed, read not
re-derived): **a genuine, provable, Occam-ordered causal DAG** — directed
search over Γ-modifications, cheap hypothesis classes tried before minting
new capability, with the soundness proof resting on monotonic guard flags
and fixpoint reachability. This is the cleanest real, already-gated instance
of τ3's stated payoff ("directed... search... without executing [the
modifications]") anywhere in the repo. Crucially, that same document (§3.5)
independently found: **the composer's actual ranking key is `(coverage
DESC, total_fit DESC)` — plan parsimony (fewest parts) is tracked
(`plan.len()`) but never used as a ranking key**, despite CLAUDE.md
repeatedly describing MDL/"as few as possible, but no fewer" as the
"governing pressure" behind codebook growth. This is a real, already-found,
unpatched gap — not invented for this rung — and it is exactly the
Axis-R-vs-Axis-O seam this rung needs: a law the system is *described* as
following, genuinely functions according to *in the cases the guard chain
covers* (mint-avoidance), but does not yet have a wired decision-rule for
in the one case checked here (parsimony tie-breaking).

**Verified before registering the bars (a fact, not a prediction):**
`seeds/self_processes.json` currently holds SelfProcess accounts for
`learning, perceiving, world_attachment, collapse, imagining, attending` —
**none for growth/minting/codebook-parsimony**. `domains/self_model.py::
find_self_process` does a real graph read over held `SelfProcess` nodes; a
query for `["grow","growth","mint","minting","codebook"]` against the
booted seed returns `None` (checked directly, this session, before any
bar below was set). This is the real, current, unmodified repo state: Axis L
for the growth law is at **φ_R = 0** today.

**TAU-L-1 (implicit competence without representation — witness that the
gap is real, not fabricated).** On the currently-booted, unmodified graph:
(a) confirm `find_self_process` returns `None` for the growth/minting
process (φ_R = 0, verified fact, not measured as a bar outcome — recorded
for completeness). (b) Run the SAME directed-vs-undirected battery Part-A's
mechanism supports: a constructed set of residuals mixing cheaply-explainable
(rung-1/rung-2 reachable) and genuinely-novel (mint-only) cases, comparing
the real seeded rung ladder against an undirected baseline (mint
immediately, no rung-checking). **PASS** = the real ladder mints strictly
fewer `CapabilityAxis` quanta than the undirected baseline on the same
battery (this is the paper's own stated τ3 falsifier, checked directly:
"a system... that exhibits no directional bias... compared to an undirected
baseline" — PASS here means that falsifier does NOT trigger). This
demonstrates real, functioning, directed self-improvement with **zero**
Axis-L representation (φ_R = 0) present anywhere in the graph — the
mechanistic form of the creator's own "operating at a τ3 context... without
being aware of it" anecdote.

**TAU-L-2 (representation without operative wiring — the sharp negative
half).** Add exactly one `SelfProcess` node (following the existing,
unmodified pattern byte-for-byte — same attrs shape as the six already
seeded) describing the growth/parsimony law in the agent's own terms, to
the **throwaway, in-memory probe substrate only** (no seed file touched).
Construct a tie-break battery: two `ShapeSignature`-covering plans with
equal coverage and equal `total_fit` but different part-counts (a direct
instantiation of the exact ranking key `GAMMA_SEARCH_COMPLETENESS_CEILING.md`
§3.5 names). **PASS (confirms the sharp distinction)** if (a)
`find_self_process`/`run_self_process` now answers a "how do you grow?"
query from the new node (φ_R crosses to 1 — verbal-report level, Flavell/
Karmiloff-Smith E1-ish), **AND** (b) the tie-break battery's outcome is
**unchanged** from TAU-L-1's implicit-only result — i.e. merely adding a
queryable representation does not, by itself, change what the real composer
selects (φ_O stays 0). **FAILS to confirm** if adding the node alone
somehow changes the composer's real output (would mean the representation
was already, coincidentally, wired — checked directly, not assumed either
way).

**TAU-L-3 (operative wiring — the sharp positive half, with a causal
perturbation test, not mere correlation).** Add a minimal decision-rule
that reads the SelfProcess node's `objective` attr (a machine-readable
field, e.g. `"min_parts"`) from the live graph and applies it as an
explicit tie-break over the real composer's output (a live graph read, not
a hardcoded Python constant — the closest honest analogue, in a read-only
probe script, of "a rule in Γ consulting ℓ_X"). **PASS** if (a) the same
tie-break battery now reliably (100% of constructed tie cases) selects the
fewer-parts plan, **AND** (b) the **perturbation test**: editing the node's
`objective` attr to `"max_parts"` (or deleting the node) flips/reverts the
selection correspondingly, on the same battery, with no other code change —
proving the decision is causally read from ℓ_X's content, not a
coincidental artifact of the node's mere presence. This is φ_O = 1 for
Axis L, in the same structural register as τ1's own boolean order
parameter.

**TAU-L control (should succeed under BOTH implicit-only and explicit
conditions — proves the axis isn't rigged to always favour "explicit").**
A non-tied battery (coverage/fit alone already determine a unique winner)
run through both TAU-L-1's implicit-only path and TAU-L-3's explicit-wired
path. **Expected, registered in advance:** identical output both ways — the
explicit parsimony rule is a no-op whenever there is no tie to break,
demonstrating the Axis-R/Axis-O distinction is not merely "explicit always
wins," only "explicit wins exactly where the implicit machinery was
genuinely silent."

---

## 6. TAU-ORTHO — structural independence of Axis C and Axis L

After TAU-C and TAU-L are both run: (a) grep/query the TAU-L probe's
constructed graph for any `owner="other"` / foreign-codebook content —
**expected: none** (Axis L's φ_R/φ_O crossings use zero Axis-C content).
(b) grep/query the TAU-C probe's constructed graph for any `SelfProcess` /
law-representation content — **expected: none** (Axis C's φ_R/φ_O crossings
use zero Axis-L content). This is a real existence proof, not a general
theorem: it shows the two axes **can** be crossed independently in this
substrate, directly falsifying "τ2 must be crossed before τ3 can be
attempted" and "τ3 must be crossed before τ2 is meaningful" as *structural
necessities* (either could still be true as a contingent, non-structural
fact about a *particular* system's development order — Part A's
interleaved history argues against that too, but only as corroborating,
not decisive, evidence).

---

## 7. What would make this a clean null instead of a verdict

Registered in advance, per house discipline: if TAU-C-a lands in the 10-20
point ambiguous band, or if TAU-L-2/TAU-L-3's perturbation test shows the
composer was already silently sensitive to node presence/absence for
reasons unrelated to the intended wiring (a confound, checked directly by
running the perturbation test against a control node with an unrelated
`objective` value), this document reports that honestly as "operability/
representability turned out not to cleanly separate this way for this
mechanism" rather than forcing a reversal or collapse verdict. A clean null
here is a complete, valuable result in this project's own terms, not a
failure to find what was expected.

---

## 7a. Amendment (registered before the FINAL measurement run, after a dry
run surfaced a scoring confound)

A dry run of the TAU-C harness surfaced two implementation issues, fixed
here before any number below is treated as final — both are scoring-code
fixes, not changes to the hypotheses, battery construction, or bars, and
both affect the ratio-only rule and the fixed baseline symmetrically:

1. **A match-scoring bug in the first draft** credited a `self` prediction
   as "matching" a true optimum of `mint` (since the ratio-only rule never
   proposes `mint` at all, this was a one-sided leniency, not a symmetric
   one). Fixed to strict equality: a predicted action counts as correct
   only if it equals the true optimal action exactly.
2. **A structural confound, not a bug**, surfaced once (1) was fixed: both
   the ratio-only rule and the fixed baseline can only ever propose
   `{self, adopt}` — `mint` is not representable in either decision
   procedure's action space at all (the bare cross-codebook ratio carries
   literally no information about a third, self-directed-growth option).
   Any battery instance whose true optimum is `mint` is therefore an
   automatic, symmetric miss for BOTH rules, capping full-battery accuracy
   at `1 - mint_fraction` regardless of how informative the ratio is for
   the self-vs-adopt sub-decision specifically. **Amendment: report both
   the full-battery accuracy (for transparency) and a RESTRICTED accuracy
   computed only over the subset of instances whose true optimum is `self`
   or `adopt`** — the subset where the ratio-only rule's action space
   actually overlaps the ground truth's. The registered bars (§4,
   TAU-C-a/b) are read off the RESTRICTED metric, since the full-battery
   number's cap is a shared artifact of the action-space choice, not a
   fact about comparative-ratio operability. This is disclosed here, with
   both numbers reported in the results document, not silently swapped.

## 7b. Post-measurement addendum — a sharper order parameter arrived after
TAU-L was run, folded in as citation evidence, not a re-measurement

After TAU-L-1/2/3 were run (§5), the creator sharpened the order parameter
further: not "does *some* rule read a representation" (Axis R/O, §5's own
framing) but **"where is a residual processed" — does it stay object-level
(absorbed locally, a weight/scalar adjusts, never becomes graph data Π
reasons over) or get promoted to a graph-resident object that can revise
the system's own representational vocabulary (mint a new dimension)?**
This is answered by CITING two already-existing, already-gated repo
mechanisms found by reading code after the fact (`ax_impotent`'s cached
verdict = object-level-only; the sd loop's rung-3 `DimInfer`/
`LatentDimension` mint = genuine promotion) rather than by running any new
measurement or re-rolling TAU-L's own battery. This is disclosed as an
addendum, not folded silently into §5's bars, because it arrived after
those bars were already read — see the results document §2a for the full
citation and reasoning, and §4 for how it supersedes the R/O framing as
the lead definition for Axis L while keeping R/O as a secondary,
coarser restatement.

## 8. Process discipline notes

- All measurement code lives in a single, throwaway, read-only probe script
  under `scripts/`, following `scripts/probe_beam_completeness.py`'s own
  precedent: an in-memory substrate built via `boot_core()`, no writes to
  `seeds/`, `domains/`, or `runners/`, nothing under `data/`, no
  multi-second live-measurement fixture, hence none of the
  `try/finally`-under-`SIGKILL` hazard `PROGRAM_SYNTHESIS_ARC6_WIRE_HANDS.md`
  §7.5 and `PROGRAM_SYNTHESIS_ARC6_IMPOTENCE_CAMPAIGN.md` §7.2 document —
  runtime is expected well under a few seconds, no timeout wrapper shorter
  than 60s will be used regardless.
- Any Python written for this rung is mechanical I/O over the real Rust
  `ShapeDecode`/`TransformDecode` Terms and real graph reads/writes
  (`add_node`, `node`, `nodes`) — no Python rule engine, no agent-decision
  logic reimplemented in Python outside the explicitly-labelled "decision
  rule" construct in TAU-L-3, which exists only to give the *probe* a
  causal-wiring analogue to test against, is not proposed as shippable
  agent code, and is stated as such in the results document.
