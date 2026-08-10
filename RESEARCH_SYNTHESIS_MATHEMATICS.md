# Mathematics spike — the trap/under-determination wall, named and mapped

**Research spike, literature + source audit. No code changed. This document is the sole
artefact.** Scope: is "structure supplies constraint where data is exhausted" (the author's
claim) a real, nameable piece of mathematics, and if so, which piece, what does the engine
already have of it, and what is the cheapest next lever.

---

## 0. How to read this document

### 0.1 Evidence/maturity grading

Adapted from `RESEARCH_CODE_IN_THE_BRAIN.md` §0 to a literature-and-source-audit spike rather
than a neuroscience one. Every citation and every engine claim below is tagged:

| Grade | Meaning |
|---|---|
| **[S]** | Verified directly against THIS repo's source this session (file + line cited) — not a literature claim, a code fact. |
| **[A]** | Textbook/canonical result, independently re-confirmed this session via a primary or authoritative secondary source (fetched, not recalled). |
| **[B]** | Well-established result, confirmed this session via one authoritative secondary source (e.g. a maintained encyclopedia article), not cross-checked against a second independent source. |
| **[C]** | Citation reconstructed from the author's training knowledge and judged reliable (well-known, widely-taught result), but **not independently re-verified this session** — the session's `WebSearch` budget was exhausted (200/200) partway through this spike; `WebFetch` against several primary-source PDFs also failed to parse. Flagged as a citation-provenance gap, not asserted as certain. |
| **[D]** | A synthesis, analogy, or proposed extension original to this document — not a claim from the cited literature at all. Marked explicitly so it is never mistaken for an established result. |

**§11 standing rule applied**: no number is quoted below without the population/condition it was
measured under (per `RESEARCH_CODE_IN_THE_BRAIN.md` §11 and `CLAUDE.md`'s 2026-07-21
retraction). Every arc-4 figure below is repeated with its own population, never abbreviated to
a bare percentage.

### 0.2 What was verified this session and how

- **Source read directly**: `runners/dsl/src/term.rs` (the `AntiUnify`/`Unify`/`Covers`/
  `FixedCount`/`Substitute`/`AntiUnifyWitness`/`ShapeDecode`/`TransformDecode`/`DimInfer`/
  `SynthEnumerate` variant definitions and their doc comments), `runners/dsl/src/synth_enumerate.rs`
  (the observational-equivalence pruning implementation), `scripts/prog_synthesis_battery.py`
  (the CEGIS-shaped `repair_oracle` arm).
- **Project notes read directly**: `PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md`,
  `PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md`, `PROGRAM_SYNTHESIS_ARC4_S5.md`,
  `RESEARCH_CODE_IN_THE_BRAIN.md` §0/§11, and `CLAUDE.md`'s frame/continuum passage.
- **Web verification**: `WebSearch` was exhausted (200/200 calls used by this session before this
  spike's queries could run — shared session budget, not a per-task allocation) so all citation
  work after that point used `WebFetch` against specific pages. Several primary-source PDFs
  (Osera & Zdancewic, Solar-Lezama's thesis) returned binary/unparseable content; those citations
  are graded [C] rather than [A]/[B]. Where a `WebFetch` against an authoritative secondary source
  (Wikipedia, ACM DL, a university page) succeeded, the citation is graded [A]/[B] and the fetched
  fact is quoted, not paraphrased from memory.

---

## 1. The problem, stated mathematically

### 1.1 The setting

A spec is `(prompt, E)` where `E = {(x_1,y_1), …, (x_k,y_k)}`, k typically 2–4 revealed rows
[S: `PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md` throughout — "3 revealed rows", "2-4 revealed"].
Let `H` be the hypothesis space: all terms expressible in the DSL/IR up to a fuel/size bound
(the engine's own bound — `SynthEnumerate`'s `max_size`, default 9 [S: `term.rs:2121`],
`ProgEval`'s fuel bound, default 10,000 steps [S: `term.rs:2080`]). Define the **version space**

```
VS(E) = { h ∈ H : ∀i, h(x_i) = y_i }
```

This is exactly Mitchell's version space [A — see §3.1] restricted to a finite, fuel-bounded `H`.
A **trap** is any `h ∈ VS(E)` with `h ≠ t` (the true target relation) on some unseen input — by
definition indistinguishable from `t` using `E` alone. Arc-4 measured 104 such traps live in a
257-task MBPP run under the FULL-A4 boot-before-verdict-discrimination configuration
(`NO-STRUCTURAL`'s `accepted_holdout_fail` population) [S: `PROGRAM_SYNTHESIS_ARC4_S5.md` §0.1,
§2.1 — this is the "before" population, S1+S4 active, S2 off].

### 1.2 Why excluding a trap supplies (almost) no information — three convergent formalisations

**(a) Version-space arithmetic.** `VS(E)` is defined purely by `E` and `H`. Excluding a specific
member `h_bad` by NAME or by CONSTRUCTION (not by finding a new distinguishing input) produces
`VS(E) \ {h_bad}` — a one-element deletion from a space whose cardinality is generically governed
by the branching factor of the DSL grammar raised to the size bound, `|H_N| ~ b^N`, while `k`
(the example count) stays fixed. For fixed `k`, `|VS(E)|` grows with `N`; removing one named
element changes the searcher's belief about that ONE candidate and nothing else, unless other
candidates happen to be **observationally equivalent** to it over `E` (§1.4 below) — in which case
excluding it by signature, not by name, removes the whole equivalence class at once, which is
exactly what `SynthEnumerate`'s `exclude` parameter already does [S: `term.rs:2129-2140`].
This is precisely why the arc-4 measurement is a clean instance: of the 26 pre-accept structural
rejections, **12 find literally nothing else** (`enumerate_failed`/`no_shape`) [S:
`PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md` §2, "(b)/(c)" list] — `VS(E)` for those tasks, after removing
the trap, is empty at the searched size bound. Exclusion did not fail to find a better answer; it
correctly reported there is no other answer **at that information level**.

**(b) The Angluin L\* framing — a rejection without a counterexample is worth zero bits.**
Angluin's exact-learning framework [C — Angluin, "Learning Regular Sets from Queries and
Counterexamples," *Information and Computation* 75(2), 1987] treats "your hypothesis is wrong"
as an **equivalence query**, and the framework's central theorem is that an equivalence query is
only useful when its negative answer comes **with a counterexample** (a distinguishing input on
which the hypothesis and the target disagree) — a bare "no" without a witness cannot be converted
into a refinement step; the learner has no way to know which of its remaining consistent
hypotheses to prefer. **This is the exact shape of a structural rejection.** D1–D7
(`ARC4_STRUCTURAL_NOTES.md` §1) prove a candidate is wrong by INSPECTING its IR — never by
executing it on a new input — so a structural verdict is, in Angluin's terms, an equivalence
query answered "no" with **no counterexample**. It is sound (the candidate really is wrong) but
by the L\* theorem it cannot, by itself, discriminate among the remaining members of `VS(E)`.
This is the formal reason `PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md` §2's "(a) Repaired into a passing
accept: `[]` — zero" is not a bug: exclusion-without-a-counterexample is mathematically incapable
of producing that outcome unless the remaining version space happens to already contain only the
target.

**(c) Bayesian / MDL framing.** Put a size-biased prior `π(h) ∝ 2^{-size(h)}` (a standard
Solomonoff/MDL prior) over `H`. The posterior after conditioning on `E` is
`π(h|E) ∝ π(h)·[h ∈ VS(E)]`. Rejecting `h_bad` renormalises the posterior over
`VS(E) \ {h_bad}` — a proportional reallocation of the SAME mass, not new mass arriving from
outside. If the true target `t` and several decoys share the same size class, this reallocation
does not preferentially favour `t`. **The only two ways to genuinely shrink `VS(E)` are (i) a new
labelled example (more `E`) or (ii) a restriction of `H` itself, applied BEFORE intersecting with
`E`** — i.e. an inductive bias in Mitchell's own sense [C — Mitchell, "The Need for Biases in
Learning Generalizations," Rutgers CBM-TR-117, 1980: an unbiased learner (one whose hypothesis
space is "all functions consistent with the data") can never generalise past the data at all,
because every unseen point is equally consistent with some hypothesis in that space]. This is the
precise mathematical statement of the author's claim: **"structure supplies constraint" means
"structure restricts `H` before intersecting with `E`," and this is provably the ONLY lever
besides more data — exclusion is neither.**

### 1.3 A quantitative reason a symmetry-shaped structural fact is unusually strong

Route (ii) above is not just theoretically available — for a specific and identifiable shape
class it is nearly free. If a spec's target relation `t: X^n → Y` is conjectured invariant under
a group `G ≤ S_n` acting by argument permutation (`t(x) = t(σ·x)` for all `σ ∈ G`), then **each
revealed row manufactures up to `|G|−1` additional labelled rows at zero oracle cost**: permute
the row's inputs by any `σ ∈ G` and assign it the SAME output. This is not a heuristic — it
follows directly from the definition of invariance. Concretely, on `br_10_top_of_three`
[S: `PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md` §4], the revealed row `(1,9,3)→9` under a conjectured
full-`S_3` symmetry (justified lexically: "the largest of three numbers" is an N-ary superlative,
order-independent by definition of "largest") licenses the FREE row `(3,1,9)→9`. The trap
`max(a,b)` (reading positions `a,b` literally) evaluates `(3,1,9)` as `max(3,1)=3 ≠ 9` —
**falsified, using no new oracle query, from data the searcher already possessed.** This is
worked through as the concrete next experiment in §6; it is the mechanism, not merely the
citation, that answers "where does structure supply constraint the examples don't."

### 1.4 The quotient already in use, precisely

`SynthEnumerate` prunes by **observational equivalence**: two candidate terms `h1, h2` are
identified iff `h1(x_i) = h2(x_i)` for every example input `x_i` currently in scope [S:
`synth_enumerate.rs` — "Observational-equivalence signatures — generator.py's `_canon`", lines
~541-576; `pruned_equiv` counter, lines 1058-1059; `equivalence_pruning_is_counted` test,
line 1844]. This is a genuine equivalence relation (reflexive/symmetric/transitive) on the term
algebra, and it is the exact generalisation, to a finite example set instead of an infinite
suffix set, of the **Myhill–Nerode congruence** [C — Myhill 1957 / Nerode 1958, the equivalence
relation underlying DFA minimisation: two strings are equivalent iff every possible suffix yields
the same acceptance]. The engine already computes ONE quotient (by "agreement on `E`'s inputs");
§1.3/§2/§4 below argue the next available quotient is the SAME operation applied to the **input
labelling space** under a conjectured symmetry group — orbit equivalence, not term equivalence.

---

## 2. What the engine already has, named

### 2.1 Primitive → mathematics → citation → usage-strength table

| Engine primitive | Source | The mathematics | Citation | Using its full strength? |
|---|---|---|---|---|
| `AntiUnify` | `term.rs:791-799` | Least general generalisation (LGG) / anti-unification — the MEET in the θ-subsumption lattice over first-order terms | Plotkin, "A Note on Inductive Generalization," *Machine Intelligence* 5, 1970 [C] (independently, Reynolds 1970) | **Partial.** Used for `FixedCount`/MDL scoring and `ShapeDecode`'s `shape_fit`; not yet applied to program CANDIDATES themselves (e.g. generalising two rejected-but-close candidates into a repair template) — only to shape/relation patterns. |
| `Covers` | `term.rs:810-818` | θ-subsumption / the generality PREORDER dual to LGG — literally ILP's refinement-operator ordering | Plotkin 1970 (same); textbook treatment: Nienhuys-Cheng & de Wolf, *Foundations of Inductive Logic Programming*, LNAI 1228, Springer 1997 [C] | Used for shape-decode coverage checks (pattern ⊑ instance). Not yet used to build a subsumption LATTICE over synthesised program candidates (only over relation/shape patterns). |
| `FixedCount` | `term.rs:801-808` | A specificity count — informal MDL: how many leaf positions a pattern FIXES vs leaves WILD | Rissanen, "Modeling by shortest data description," *Automatica* 14, 1978 (MDL principle) [C] — used here as a heuristic count, not a two-part code length | **Partial** — a ranking heuristic, not a calibrated description-length bound (no encoding cost is assigned to the WILD positions themselves). |
| `Substitute` | `term.rs:831-840` | The constructive inverse of LGG's abstraction walk — lattice DESCENT / instantiation | (operational; the standard complement of Plotkin's LGG, not independently named in the literature) | Full for its stated role. |
| `AntiUnifyWitness` | `term.rs:820-829` | Anti-unification retaining the SUBSTITUTIONS ("X but with Y") — witness-retaining generalisation, close to analogical-mapping systems | Same Plotkin lineage; witness retention is standard in structure-mapping/analogy (Falkenhainer, Forbus & Gentner, "The structure-mapping engine," *Artificial Intelligence* 41, 1989) [C] | Partial — used in the shape/composition pipeline, not yet in program repair. |
| `Unify` | `term.rs:842-854` | Lattice JOIN — the constructive DUAL of `AntiUnify`; the source's own docs name it the Fauconnier–Turner conceptual BLEND / Ontañón–Plaza CBR AMALGAM over the same generic meet | Robinson, "A Machine-Oriented Logic Based on the Resolution Principle," *JACM* 12(1), 1965 [A — fetched] (unification proper); Fauconnier & Turner, "Conceptual Integration Networks," *Cognitive Science* 22(2), 1998 [C]; Ontañón & Plaza, "Amalgams: A Formal Approach for Combining Multiple Case Solutions," ICCBR 2010 [C] | Used for shape blending; not wired into program-synthesis repair at all. |
| `StructSim` | `term.rs:856-868` | Graded structural similarity — the SOFT-leaf relaxation of `AntiUnify`/`Covers`'s exact match | (engine-original relaxation of the above; no single canonical citation) [D] | Used in vision/handwriting recognition, not program synthesis. |
| `SynthEnumerate` | `term.rs:2114-2144`, `synth_enumerate.rs` | Bottom-up, size/MDL-ordered enumerative program synthesis with **observational-equivalence pruning** — a Myhill–Nerode-style quotient of the term algebra by "agrees on all current example inputs," saturation-halted | The pattern (bottom-up enumeration + observational-equivalence pruning) is central to the SyGuS-era enumerative-synthesis literature: Alur et al., "Syntax-Guided Synthesis," FMCAD 2013 [C]; Albarghouthi, Gulwani & Kincaid, "Recursive Program Synthesis," CAV 2013 [C]. *Exact coinage of "observational equivalence" in this literature not independently re-verified this session (search budget exhausted) — provenance gap flagged, not asserted.* | **Quotients by data only.** Does NOT additionally quotient by a conjectured SYMMETRY of the target relation — the gap this document's §4 recommendation closes. |
| `ShapeDecode` / `TransformDecode` / `DimInfer` | `term.rs:870-926`, `943-1010`, `1034-1119` | Codebook decoding (vector-quantisation / dictionary-learning framing) PLUS, for `TransformDecode`/`DimInfer`, decoding an observation as a held base shape plus a **group-generated delta** (rotation/reflection/translation as integer-lattice isometries; generator search = search over a finite named GENERATOR SET of a transformation group) | Vector quantisation: Gersho & Gray, *Vector Quantization and Signal Compression*, 1992 [C]. Group action / generator search: standard finite-group theory (e.g. Artin, *Algebra*) [C]. The RIGOROUS kernel specifically licensing "only 90°/180°/270° rotations are exact on an integer lattice" is the **crystallographic restriction theorem** (a 2-D or 3-D lattice's rotational symmetries can only have order 1, 2, 3, 4, or 6) [B — standard result, e.g. as presented in crystallography/discrete-geometry texts] | **This is already a group-theoretic invariance engine** — just applied to spatial/visual shape, never to a program's ARGUMENT-PERMUTATION symmetry. This is the single largest "already have the machinery, wrong target" finding of this spike (§4). |
| D1–D7 structural verdicts (`domains/prog_synthesis.py`-side, not a `term.rs` primitive but built from `ProgEval`/IR walks) | `ARC4_STRUCTURAL_NOTES.md` §1 | **Abstract interpretation** cast as a rejection oracle: each detector computes a decidable, SOUND over-approximation of the program's capability (e.g. "this variable is providably never read anywhere") and rejects when that abstraction proves the candidate CANNOT be correct, without executing on unseen data (except D7, a finite-domain full execution) | Cousot & Cousot, "Abstract Interpretation: A Unified Lattice Model...," POPL 1977 [A — fetched]. The "unread parameter ⇒ cannot depend on it ⇒ cannot be correct if the spec varies with it" bridging step is a light dependency/influence analysis, closest named to program slicing (Weiser, "Program Slicing," ICSE 1981 [C]) and non-interference (Goguen & Meseguer, "Security Policies and Security Models," IEEE S&P 1982 [C]) | **Already at genuine, measured strength**: 34/76 (44.7%) recall on the frozen 76-trap arc-3 population, 3/21 (14.3%) false-positive rate against the 21 correct-`pass` rows from the SAME population [S: `ARC4_STRUCTURAL_NOTES.md` §2], converting to **26/104 (self-detected wrongness against the LIVE, larger 104-trap population under S1+S4)** pre-accept rejections in the full arc-4 endgame [S: `ARC4_S5.md` §0.1 — the two population sizes, 76 vs 104, are DIFFERENT and are never merged into one ratio, per that document's own §0.2 caveat]. Genuinely under-used only in BREADTH of abstract domain (§3.5/§4). |

### 2.2 A unifying observation [D]

`AntiUnify`/`Unify` (meet/join of the subsumption lattice), `Covers` (the lattice's preorder),
Mitchell's `S`/`G` version-space boundaries (§3.1), and abstract interpretation's `α`/`γ`
Galois connection (§2.1's D1–D7 row) are not four unrelated ideas — they are four instances of
**lattice theory and Galois connections**, the same order-theoretic substrate. This is worth
stating explicitly because it means the engine's existing primitives are not a grab-bag: they are
already positioned inside the one mathematical framework (order theory over structured terms)
that the candidate formalisms in §3 also live in. Extending toward symmetry (§3.2) or a richer
abstract domain (§3.5) is extending WITHIN this framework, not importing a foreign one.

### 2.3 The frame/continuum invariant, assessed rigorously

`CLAUDE.md`'s claim: *"in-frame is INTEGER; non-integer math is CROSS-FRAME; the continuum sits
in `Hom(frame, frame)`, not in any object."*

**What it is claiming, precisely.** Read as a categorical statement — objects (`Frame`s, i.e.
grounded/observed graph structures over `Z^n`) are discrete; morphisms between them (a rotation,
a scale, a rendering, a comparator) may carry real-valued parameters. Read this way it is a
**modelling discipline**, not a theorem: nothing in category theory forces `Hom(A,B)` to be
"more continuous" than `A`/`B` — the discipline is a CHOICE about which structures the
implementer allows to be continuous, applied consistently.

**Where it has a genuinely rigorous kernel.** The specific instance actually implemented —
`DimInfer`'s rotation/reflection generators are restricted to 90°-based turns, never an arbitrary
real angle [S: `term.rs:1034-1093`, "`kind` selects the built-in primitive (`"rotation90"`,
`"reflection_r"`, `"reflection_c"`)... integer lattice only"] — is licensed EXACTLY by the
**crystallographic restriction theorem** [B]: a 2-D (or 3-D) lattice can only be preserved by
rotations of order 1, 2, 3, 4, or 6 (i.e. 360°/n for those n); any other rotation angle maps
lattice points off the lattice. This is a real, provable, narrow fact, and it is precisely why
the engine's own rotation generator is forced to be one of a small enumerable set rather than a
continuous parameter — the code already embodies the theorem's content without naming it.

**Where it is a looser generalisation, honestly.** The BROADER claim — that ALL real-valued
structure (π, Fourier, log, DTW/SC+TPS verdict metrics) must live in maps, never in observed
coordinates — is not a corollary of the crystallographic theorem; it is a much more sweeping
methodological principle. Its best rigorous analogue is **constructive/computable analysis**
[C — Bishop, *Foundations of Constructive Analysis*, 1967; Weihrauch, *Computable Analysis*,
2000]: a real number is only ever given INTENSIONALLY, as a rule/algorithm (a Cauchy-sequence
generator), never as a completed object; any FINITE, OBSERVED representation of it is necessarily
a rational/finite-precision approximation. `CLAUDE.md`'s "Continuity is INTENSIONAL only" is
essentially restating this constructive-analysis discipline in the project's own vocabulary
("a continuous quantity is a RULE you APPLY... never an observed datum"). Under that reading the
invariant is COHERENT and non-vacuous — it correctly predicts, for instance, that a future
`SpaceQuantum.depth` refinement axis must NOT be implemented as a `DimensionGenerator` (which
would smuggle a continuous ratio into an in-frame integer count) — a prediction the codebase's
own `DYADIC_DEPTH_DESIGN.md` reached independently and is cited in `CLAUDE.md` as a "deferred for
review" consequence of exactly this invariant. That is a genuine self-consistency check the
invariant PASSED.

**Verdict.** Coherent as a modelling discipline with a real, narrow, provable kernel
(crystallographic restriction on lattice-preserving isometries) and a defensible, well-precedented
looser form (the constructive-analysis intensional/extensional distinction). It is **not** itself
a theorem that "non-integer math is cross-frame" in full generality — that is a design commitment
the project has chosen to enforce everywhere, correctly motivated by, but not strictly entailed
by, the narrow kernel. §5 below names the falsifier: any technique (including this document's own
§4 recommendation) that would need to store a real-valued parameter ON a graph node rather than
in a generator/comparator violates the discipline and should be caught by the same review that
caught the dyadic-depth case.

---

## 3. The candidate formalisms

Each entry: what it gives, what it costs, whether the substrate can express it, and a maturity
grade using the §0.1 scale (grade applies to the CITATION/literature maturity, separately from
the FIT judgement, which is stated in prose).

### 3.1 Version-space / candidate-elimination (Mitchell)

**Citation** [C]: T. Mitchell, "Generalization as Search," *Artificial Intelligence* 18(2), 1982,
203–226 [B — fetched, confirms `S`-set/`G`-set boundary structure and the 1982 citation]; later
textbook form in Mitchell, *Machine Learning*, 1997.

**What it gives.** The exact vocabulary for §1: `VS(E)`, the `S`-boundary (most specific
consistent hypotheses) and `G`-boundary (most general). **What it does NOT give**: a new pruning
mechanism. It is a DESCRIPTIVE formalism for the wall, not a cure — the engine's `SynthEnumerate`
already effectively enumerates (a fuel-bounded slice of) `VS(E)`'s members; adopting explicit
S/G-boundary maintenance would be an EFFICIENCY improvement (representing the space compactly)
without changing WHAT is prunable, because — per §1.2(c) — the only two things that shrink
`VS(E)` are more data or a restriction of `H`, and version-space algebra concerns neither by
itself.

**Cost / expressibility.** Cheap to adopt as vocabulary (already implicit); adopting S/G-boundary
MAINTENANCE as an actual algorithm would be a moderate Rust addition with unclear payoff given the
above.

**Grade: [B] maturity, LOW standalone fit.** Adopt as the frame for talking about the problem
(§1 already does this); do not expect it to be a lever on its own. It is the correct diagnosis,
not the treatment — Mitchell's OWN follow-up work (§1.2c, the 1980 inductive-bias paper) says the
treatment is bias, which is §3.2/§3.3 below.

### 3.2 Group theory / invariance and symmetry reduction

**Citations**: symmetry-breaking predicates in CSP/SAT — Crawford, Ginsberg, Luks & Roy,
"Symmetry-Breaking Predicates for Search Problems," KR 1996 [C — full text fetch 403'd this
session, cited from established knowledge]; canonical-form / orbit-representative enumeration —
McKay & Piperno, "Practical graph isomorphism, II," *J. Symbolic Computation* 60, 2014 [B —
fetched, confirms citation and nauty's role]. Underlying theory: finite group actions on a set,
orbit-stabiliser, quotient by group action — standard finite group theory [C].

**What it gives — the sharpest fit found in this spike.** A conjectured symmetry group `G ≤ S_n`
on a spec's arguments does two things simultaneously, both cheap and both already buildable from
primitives the engine owns:

1. **Manufactures free examples** (§1.3): saturate `E` under `G` before search — for arity-`n`
   rows and `|G|` group elements, up to `k·(|G|-1)` new labelled rows at zero oracle cost.
2. **Filters candidates by an EXECUTABLE invariance check**, in exactly the style D7 already
   uses: execute the SAME accepted-or-candidate program on `σ(x)` for `σ ∈ G` (never a held-out
   oracle value) and reject if the output is not invariant. This is not a new kind of primitive —
   it is `ProgEval` called on permuted inputs, the same "prove a property by executing the
   candidate against itself" discipline D7 already uses [S: `ARC4_STRUCTURAL_NOTES.md` §1, D7
   row] — extended from a closed BOOLEAN domain to a closed PERMUTATION orbit.

**Cost / expressibility.** The mechanism (saturate + filter) is a small, well-scoped Rust addition
(a `symmetry: Option<Vec<Perm>>` argument on `SynthEnumerate`, or a standalone
`SymmetryCheck`/`OrbitSaturate` Term, consistent with the existing Term-primitive style). The
**hard part is not the math — it's the detection**: deciding WHICH group to conjecture from a
natural-language prompt ("the largest of three numbers" → full `S_3`; "the difference of two
numbers" → no symmetry) is a lexical/semantic-shape classification problem, not a mathematical
one, and must be gated conservatively (§5) to avoid wrongly rejecting a correct-but-asymmetric
target.

**Grade: [C]/[B] literature maturity (this IS the standard machinery of symmetry-breaking search),
HIGH fit, HIGH implementability.** This is the top-ranked recommendation (§4).

### 3.3 Parametricity / "theorems for free" (Wadler 1989)

**Citation** [A — fetched]: P. Wadler, "Theorems for Free!," *4th International Conference on
Functional Programming and Computer Architecture*, London, September 1989. Underlying theory:
relational parametricity, Reynolds, "Types, Abstraction and Parametric Polymorphism," IFIP
Congress 1983 [C].

**Honest reach for a monomorphic int/list DSL.** Free theorems are derived from a POLYMORPHIC
type alone — Wadler's headline case, `id :: ∀a. a → a`, is forced BY PARAMETRICITY ALONE to be
the identity, and `∀a. a → a → a` is forced to be one of exactly the two projections (the
function cannot inspect or combine values of a fully abstract `a`, so it can only discard one).
**Our target programs are almost all MONOMORPHIC over concrete types** (`int`, `str`,
`list[int]`) — nothing stops a monomorphic `int → int → int` function from comparing, adding, or
branching on its arguments, so the LITERAL free-theorem machinery yields **nothing beyond what
arity/type checking already gives** (D6, already free [S: `ARC4_STRUCTURAL_NOTES.md` §1, D6 row]).

**Where it becomes useful — only via an ad hoc constraint reframing [D].** If a spec's shape is
ANNOTATED (from a lexical cue, not derived automatically) as `Ord a ⇒ a → a → a → a` rather than
`int → int → int → int`, relational parametricity DOES yield a testable consequence: `f` must be
EQUIVARIANT under any order-automorphism `φ` of the domain (`f(φ(a),φ(b),φ(c)) = φ(f(a,b,c))`),
which forces `f` to be expressible purely from comparisons — no arithmetic. This is executable
exactly like D7/§3.2's symmetry check (apply a random monotonic relabelling, check the output
relabels correspondingly, no oracle needed), and it would correctly reject any candidate that
sneaks in `+`/`-`/`*` for a comparison-only spec. It would **not** have caught the actual median-
of-three defect (task 397: `max(a,b)` ignoring `c`) — `max` is itself order-equivariant, so this
check is orthogonal to, not a replacement for, D3's unread-parameter detection.

**Cost / expressibility.** Cheap to add as a spinoff detector (`D8: order_equivariance_violation`)
riding on the SAME executable-invariance machinery §3.2 needs; expensive/impossible to get
"for free" in the literal Wadler sense for a monomorphic language, honestly stated.

**Grade: [A] literature maturity, LOW-MODERATE fit.** Elegant, narrow yield, best framed as a
cheap bonus detector once §3.2's execution-under-a-conjectured-relation machinery exists, not as
a standalone lever.

### 3.4 Type-and-example-directed synthesis (Myth, Synquid) and CEGIS (Sketch)

**Citations**: Osera & Zdancewic, "Type-and-Example-Directed Program Synthesis," PLDI 2015 [C —
PDF fetch returned unparseable binary content this session; venue/year from established
knowledge, not independently re-verified]. Polikarpova, Kuraj & Solar-Lezama, "Program Synthesis
from Polymorphic Refinement Types," arXiv:1510.08419 (Synquid) [B — fetched, confirms authors and
the search-space-decomposition argument]. Solar-Lezama, *Program Synthesis by Sketching*, UC
Berkeley PhD thesis, 2008 [B — fetched, confirms CEGIS loop structure and citation].

**What each does when examples run out — the direct answer to the brief's question.** None of
them face our exact wall, because all three assume an input richer than ours:

- **Myth** uses the DECLARED ALGEBRAIC-DATATYPE structure (sum-type coverage, pattern-match
  exhaustiveness) as its extra constraint — i.e. its "beyond the examples" leverage IS a
  structural/type fact, but one the USER supplies as a formal type, not one mined from a natural-
  language prompt.
- **Synquid** goes further: refinement types can encode the FULL spec directly ("returns a sorted
  permutation of the input"), often needing few or zero examples, and Polikarpova's own argument
  is that type-based specs DECOMPOSE combinatorially, "causing the synthesizer to consider fewer
  component combinations" [B — fetched, direct quote]. Again: the leverage is a formal spec the
  user must write, not something inferred from 2-4 rows and a sentence.
- **CEGIS/Sketch**'s answer to "examples exhausted" is structurally the OPPOSITE of a structural
  approach: get a bigger checkable spec (an SMT-decidable assertion or a reference implementation)
  and MINE counterexamples from it. This is exactly what this codebase's own `repair_oracle` arm
  does [S: `scripts/prog_synthesis_battery.py:752-776`, `run_task_p7`: one verifier-revealed
  counterexample fed via `ingest_counterexample`, gated on `pre["outcome"] == "accepted_holdout_fail"`]
  — and it is exactly the mechanism `ARC4_S5.md` §2.1(3) documents as STALLED for `br_10`: S2's
  structural rejection now intercepts BEFORE a candidate is ever accepted, so
  `run_task_p7`'s gate (which only fires AFTER an accept) never sees the case, `oracle.rounds == 0`
  [S: same section]. **CEGIS's whole mechanism requires an oracle that our 2-4-row protocol does
  not have at the point the wall bites** — this is not a limitation of CEGIS as math, it is a
  mismatch between what CEGIS assumes is available and what this benchmark protocol provides.

**Honest conclusion.** None of Myth/Synquid/CEGIS solves our problem directly, because all three
presuppose an input (a formal type, or an oracle) that a 2-4-example MBPP-style spec does not
supply. Their transferable METHODOLOGICAL lesson: **when examples run out, the fix in this
literature is always "get a formal constraint from somewhere else"** — never "search harder" or
"propose better." Applied honestly to our setting, "somewhere else" can only be **mined from the
prompt's own grammatical shape** (superlative → extremum/symmetric; "sum of" → associative-
commutative fold; "reverse" → involution) — i.e. an implicit, NL-mined refinement predicate,
which is a genuinely novel-to-us position relative to this literature (they assume the type is
GIVEN; we would be INFERRING it), and is the same move as §3.2's lexical-cue-gated symmetry
conjecture.

**Grade: [B]/[C] literature maturity, LOW direct-reuse fit (their assumed inputs are absent
here), MODERATE fit for the borrowed PRINCIPLE** (spec-mining as bias) already exploited by §3.2.
Per the ranking rule in §4: this family is fundamentally a PROPOSAL/search-guidance technology
(type-directed enumeration), and the project's own standing finding is that proposal-side
improvements have nulled four times running [S: `ARC4_S5.md` §4, "the proposal-content line —
arc 1 H6/H7c, arc 2 HQ3, arc 3 HR1, and now arc 4 HA5 — nulls a fourth time... CONCLUSIVE for
this architecture at this scale"] — ranked low accordingly.

### 3.5 Abstract interpretation (Cousot & Cousot)

Already covered in §2.1's D1–D7 row as "what we have." The candidate-formalism question here is
narrower: **what's the next abstract domain?** D1–D7's domains are syntactic (dead-code, unread-
param, vacuous-guard, arity) plus one finite-domain full-execution case (D7). None of them reason
about NUMERIC VALUE RANGES. `ARC4_S5.md` §7 names "S4's class E — arithmetic depth / missing math
ops (19 ids)" and the 36/76 (47.4%) honest residual [S: `ARC4_STRUCTURAL_NOTES.md` §3 — "genuine
arithmetic/logic errors... no structural or behavioural red flag"] as exactly the population an
INTERVAL or SIGN abstract domain [A — Cousot & Cousot 1977, fetched] could partially address:
e.g. proving a candidate's output range is provably disjoint from the revealed rows' output range
on some INPUT RANGE the rows don't cover, without executing on that input.

**Cost / expressibility.** A small interval/sign abstract interpreter over the existing fueled
`ProgEval` IR is a moderate, well-precedented Rust addition (interval analysis is one of the
oldest, best-understood abstract domains). It is a NATURAL EXTENSION of an already-landed,
already-measured mechanism, not a new architecture.

**Grade: [A] literature maturity, HIGH fit, MODERATE-HIGH implementability.** Second-ranked
recommendation (§4) — extends a proven mechanism into the exact residual class named as the
"single largest honest unknown in the arc" [S: `ARC4_S5.md` §7, rank 1].

### 3.6 Inductive logic programming (ILP)

Already substantially present: `AntiUnify` = LGG, `Covers` = θ-subsumption — these ARE ILP's
refinement-operator lattice [C — Nienhuys-Cheng & de Wolf 1997]. Muggleton's inverse entailment
and MODE DECLARATIONS [B — fetched, Muggleton 1995 Progol, confirmed via Wikipedia's ILP summary]
are the classical answer to "how do you supply BIAS to an otherwise combinatorially explosive
hypothesis space" — mode declarations say which argument positions are input/output and which
predicates may combine. `SynthEnumerate`'s `ops`/`consts` parameters [S: `term.rs:2141-2144`] are
already a crude mode/bias declaration (which operators and literals are admissible per task).
**What ILP's mode-declaration tradition does NOT yet give us that §3.2 would**: an explicit
declaration that certain argument POSITIONS are mutually substitutable (symmetric) — this is a
natural EXTENSION of the mode-declaration idea, not a separate formalism, and is folded into the
§3.2/§4 recommendation rather than ranked separately.

**Grade: [C]/[B] maturity, mostly already present; its one missing piece is subsumed by §3.2.**

### 3.7 Observational equivalence, congruence, and the next quotient

Covered in §1.4. The engine's existing quotient is by DATA (agreement on `E`'s inputs). The next
available quotient, made concrete by §3.2, is by SYMMETRY (agreement up to a conjectured group
action on the input labelling) — literally the same "collapse behaviourally-identical members"
idea, applied one level up (to inputs, not just to candidate terms). No new mathematics is needed
here beyond §3.2; this section exists to make explicit that §3.2 is not a foreign import but the
NEXT INSTANCE of a pattern the engine already implements.

### 3.8 Bird–Meertens formalism / Dijkstra-Gries refinement calculus

**Citations**: R. Bird, "Algebraic Identities for Program Calculation," *Computer Journal*, 1989
[C]; the formalism's popular name "Squiggol" and its map/fold ("catamorphism") algebra confirmed
via Wikipedia [B — fetched]. The sharpest single result in this family for "shape supplies the
program with zero extra data": the **Third Homomorphism Theorem** [C — Gibbons, "The Third
Homomorphism Theorem," *J. Functional Programming* 6(4), 1996]: if a function on lists is
expressible BOTH as a left-fold and as a right-fold, it is NECESSARILY expressible as an
associative reduce (a list homomorphism) — a strictly stronger structural fact derived from two
WEAKER pieces of evidence, no additional data required. This is, structurally, the single closest
published analogue to the author's exact claim ("structure supplies constraint where data is
exhausted") found in this spike.

**Honest fit.** BMF/refinement-calculus derivations assume a TOTAL, FORMAL specification is
already at hand (an equational law like "prefix-max is a scan of max") and are typically
semi-manual derivations, not automatic search over an NL-prompt-plus-few-rows spec. The gap
between "BMF exists and is beautiful" and "BMF runs automatically on an MBPP task" is large:
finding WHICH algebraic law applies is itself a search problem at least as hard as synthesis.

**Grade: [C] literature maturity (well-established but assessed here from established knowledge,
not independently re-verified this session), LOW near-term implementability, HIGH conceptual
value.** Named as the field's best existence proof that the author's claim is not merely
plausible but has a fully rigorous instance (the Third Homomorphism Theorem) — a "north star,"
not a next sprint. Ranked lowest for implementation in §4 precisely because it is proposal/
derivation-shaped (you still have to FIND the applicable law) rather than constraint-shaped.

---

## 4. The ranked recommendation

**Governing rule, taken directly from the project's own four-times-replicated null** [S:
`ARC4_S5.md` §4]: mechanisms that only improve PROPOSAL (search guidance, better candidate
generation, type-directed enumeration) have measured as worth ~nothing here, four separate times
across four arcs. Mechanisms that add CONSTRAINT (prune the space, reject provably-wrong
candidates before accept) are the ONLY family that has moved a real number — D1–D7's structural
verdicts converted 26/104 of the arc-4 endgame's own live wrongness pre-accept [S: `ARC4_S5.md`
§0.1, population = `NO-STRUCTURAL`'s 104 `accepted_holdout_fail` traps under the S1+S4-active,
S2-off boot]. Every item below is ranked by (constraint vs proposal) FIRST, expected pruning
power SECOND, implementation cost THIRD.

| rank | formalism | type | expected pruning power | cost | verdict |
|---|---|---|---|---|---|
| **1** | Group-theoretic symmetry (§3.2): example-saturation + executable invariance filter, gated on a lexical superlative/aggregate cue | **CONSTRAINT** (+ manufactures free DATA, the other legitimate lever per §1.2c) | HIGH — directly targets `br_10_top_of_three`, the arc's own named clearest residual and its ONE true regression [S: `ARC4_S5.md` §2.1(3), §7 rank 2] | LOW-MODERATE: one Rust Term/`SynthEnumerate` extension + a conservative lexical gate | **Implement first.** |
| **2** | Extend abstract interpretation with an interval/sign numeric domain (§3.5) | **CONSTRAINT** | MODERATE-HIGH against the 36/76 (47.4%) honest residual population [S: `ARC4_STRUCTURAL_NOTES.md` §3] — a proven mechanism extended into its next natural domain | MODERATE: interval analysis is well-understood but is new Rust IR-walking code | **Implement second**, as a natural sequel to a mechanism already measured strong. |
| **3** | Executable order-equivariance check (§3.3), a `D8` riding on rank-1's execute-under-a-relation machinery | **CONSTRAINT**, narrow scope | LOW-MODERATE — only fires for comparison-only spec shapes, and provably CANNOT catch unread-parameter defects (orthogonal to D3) | LOW once rank 1 exists (shares the executable-invariance infrastructure) | Cheap bonus once rank 1 lands; not worth sequencing before it. |
| 4 | Version-space formalisation (§3.1) as explicit vocabulary/reporting | Neither — DESCRIPTIVE | N/A (diagnostic, not curative) | ~zero (already implicit) | Adopt as language for future write-ups (this document does); do not budget engineering time. |
| 5 | Myth/Synquid/CEGIS-style techniques (§3.4) | **PROPOSAL**-shaped (type/oracle-directed search), AND assumes inputs (formal types, an oracle) this protocol lacks | LOW — the project's own four-arc null applies, doubly so since the assumed inputs are absent | Would require inventing a formal-type-mining layer from NL first | **Rank low deliberately.** Borrow only the "mine an implicit type/refinement predicate from the prompt" principle, which IS what rank-1's lexical gate already does. |
| 6 | ILP mode declarations beyond current `ops`/`consts` (§3.6) | CONSTRAINT, but its one missing piece (argument-symmetry declaration) is exactly rank 1 | Subsumed | Subsumed | Fold into rank 1; do not implement separately. |
| 7 | BMF / refinement calculus (§3.8) | Largely PROPOSAL-shaped in practice (finding the applicable law is itself search) despite being conceptually the deepest match to the author's claim | Unknown, likely LOW near-term (no automatic law-discovery procedure exists here) | HIGH (would need an algebraic-law-matching engine built from nothing) | Cite as validating the author's claim in principle; do not schedule. |

**The one-line ranking justification**: rank 1 is the only candidate that is simultaneously (a) a
CONSTRAINT mechanism, matching the project's own governing empirical finding, (b) directly aimed
at the exact named residual (`br_10`) the project has already root-caused and left open, and
(c) buildable from primitives the engine ALREADY OWNS at genuine strength (`ProgEval`-execute-and-
compare, the exact discipline D7 uses) — it requires porting an existing capability to a new
target, not inventing a new capability.

---

## 5. Falsifiers and honest limits

- **Symmetry (rank 1) — wrong-group risk.** If the lexical gate mis-conjectures a group for a
  spec that is actually NOT invariant (e.g. mistaking "the difference of two numbers" for
  symmetric), the saturation step would inject FALSE labelled rows and could wrongly reject the
  TRUE target — a genuine regression, not a null. Mitigation, already precedented in this
  codebase: require the SAME witness-verification discipline `ARC4_S5.md` §2.1(2) used for 397/
  404 (hand-constructed witness inputs, independently re-verified, never touching held-out data)
  before trusting a conjectured group on any given spec-shape family, and restrict the initial
  gate to spec shapes with STRONG, unambiguous lexical evidence (explicit superlative/aggregate
  words), exactly mirroring how D1–D7 were only trusted after their own false-positive audit
  [S: `ARC4_STRUCTURAL_NOTES.md` §2.1].
- **Symmetry — combinatorial cost.** `|G|` can be `n!` for full symmetric groups; saturation and
  per-generator invariance checks must be gated by an explicit INTEGER budget (consistent with
  the project's own "in-frame is integer, budgets are integers" discipline threaded through every
  arc-4 phase [S: `ARC4_S6_NOTES.md` §5, "Termination... gated by a pre-existing INTEGER budget"]).
- **Abstract interpretation extension (rank 2) — Rice's theorem, precisely.** Rice's theorem [B —
  fetched: Rice 1953, *Trans. AMS* 74(2)] states every non-trivial SEMANTIC property of an
  arbitrary Turing-complete program is undecidable over the UNBOUNDED input space. This does
  **not** block an interval/sign abstract interpreter here, for exactly the reason
  `ARC4_STRUCTURAL_NOTES.md` §6 already argues for D1–D7 and this document extends to the new
  domain: `ProgEval` is FUELED (bounded steps) [S: `term.rs:2080`], and an interval/sign analysis
  is a SYNTACTIC, finite-tree-walk abstraction (like D1-D6) or, where it needs to execute, does so
  only over a domain small enough to be exhaustively checked (like D7) — no proposed check in this
  document decides an unbounded semantic property. Rice's theorem is never evaded by luck here; it
  simply does not apply to the class of properties in scope, by construction. **The false claim
  to avoid**: asserting an interval domain will "solve" the 36/76 (47.4%) residual — it will only
  ever be ANOTHER sound, INCOMPLETE abstraction with its own recall ceiling, exactly like D1–D7.
- **Order-equivariance (rank 3) — wrong-typeclass risk.** Assuming `Ord a ⇒` for a spec that
  secretly needs `Num a` (arithmetic, not just comparison) would wrongly reject correct programs;
  needs the same lexical-gate discipline as symmetry, and is doubly narrow (§3.3 already shows it
  cannot catch the unread-parameter class, D3's exclusive territory).
- **Myth/Synquid/CEGIS (rank 5) — an applicability limit, not a mathematical one.** These fail
  here because the assumed INPUT (a formal type, an oracle) is absent at the point our wall bites,
  not because the underlying math is wrong. `run_task_p7`'s stalled gate [S:
  `ARC4_S5.md` §2.1(3)] is the concrete, already-measured instance of this mismatch.
- **BMF (rank 7) — no automatic law-discovery.** The theorem (Third Homomorphism Theorem) is
  real and rigorous; automating "which algebraic law applies to this spec" is unsolved here and
  would be at least as hard as the synthesis problem it's meant to shortcut.
- **The frame/continuum invariant (§2.3) — where a proposed technique would violate it.** Any
  implementation of rank 1's symmetry generators that stored a REAL-VALUED rotation angle (rather
  than a small enumerable set of exact integer-lattice generators, mirroring `DimInfer`'s existing
  `rotation90`) as a literal float attribute on a graph node would violate the discipline exactly
  as the deferred dyadic-depth case did [S: `CLAUDE.md`, "BASE-AS-DIMENSION" section] — the
  correct home for any such continuous parameter is a generator/comparator (a map), never a node
  attribute (a frame coordinate). Flagged explicitly as an implementation guardrail for §6.

---

## 6. The concrete next experiment

**Hypothesis.** A lexically-gated, executable group-invariance constraint (§3.2/§4 rank 1)
converts `br_10_top_of_three` — the arc's own single named true regression [S: `ARC4_S5.md`
§2.1(3), §7 rank 2] — from a stalled non-convergence into a passing accept, using ONLY the 3
already-revealed rows (no new oracle query), and does so with zero new true regressions across
the existing 397/404/433 D3 population and the 257-task MBPP population.

**Mechanism to implement** (Rust, consistent with the existing Term-primitive style):

1. A lexical gate (adapter-side, mechanical: detect superlative/aggregate cue words — "largest
   of", "smallest of", "biggest", "sum of", "total of", "average of" — over a small fixed tuple
   of same-typed arguments) that CONJECTURES a full symmetric group `S_n` on those arguments. This
   is the one place a judgment call (which specs get a group conjectured) is made, and per §5 it
   must be conservative: only fire on strong, unambiguous lexical evidence.
2. `SynthEnumerate` (or a new `OrbitSaturate` Term feeding it) saturates `E` under the conjectured
   group: for each revealed row and each `σ ∈ G`, add `(σ(x), y)` if not already present.
3. Re-run the EXISTING enumerator, unchanged, over the saturated row set at the SAME size bound
   the arc already used (≤5) [S: `ARC4_S6_NOTES.md` §4].

**Worked mechanism, checked by hand against the actual `br_10` rows** [S:
`ARC4_S6_NOTES.md` §4: rows `(1,9,3)→9`, `(7,2,5)→7`, `(4,4,4)→4`]: under conjectured `S_3`,
`(1,9,3)→9` licenses the free row `(3,1,9)→9`. The trap `max(a,b)` (reading positions literally)
evaluates `(3,1,9)` as `max(3,1)=3 ≠ 9` — **falsified without any new oracle query**, using
exactly the information the searcher already had, arranged by the conjectured invariance. This is
the precise mechanism (not just the citation) by which "structure supplies constraint where data
is exhausted" cashes out on this codebase's own named example.

**Preregistered bar** (mirroring the arc's own A3 three-way honest-score accounting discipline
[S: `ARC4_S5.md` §2.1]):

1. **Primary**: `br_10_top_of_three` converges to `max(max(a,b),c)` or a behaviourally-equivalent
   symmetric extremum, re-using the EXISTING regression test
   `test_br_10_exhaustive_reenumeration_finds_nothing_from_revealed_rows_alone` [S:
   `ARC4_S6_NOTES.md` §6] as the "before" control and the SAME search with saturation enabled as
   the "after" measurement — a clean, already-instrumented before/after pair.
2. **Zero-regression, with witnesses**: re-run the SAME live witness checks arc-4 used for 397/
   404/433 [S: `ARC4_STRUCTURAL_NOTES.md` §2.2] — median-of-three and min-of-two are THEMSELVES
   genuinely `S_n`-symmetric specs (median/min are order-independent), so they should ALSO
   saturate and ALSO still correctly reject their respective decoys (`max(a,b)`, bare `a`) for the
   SAME reason `br_10`'s decoy falls — consistency check, not a separate mechanism.
3. **False-positive audit** on the SAME discipline D1–D7 received [S: `ARC4_STRUCTURAL_NOTES.md`
   §2]: run the lexical gate + saturation check over the 21 known-correct `pass` tasks from the
   frozen population and confirm zero wrongly-rejected correct programs; separately confirm a
   genuinely NON-symmetric spec shape ("difference of two numbers", "quotient of a divided by b")
   receives NO group conjecture (gate correctly silent).
4. **Population bar**: STRONG if the mechanism, applied across the full 257-task MBPP population
   under FULL-A4, converts `br_10`'s class (structural-reject-then-reopen tasks whose target
   relation is genuinely symmetric) into passing accepts with **zero new true regressions**,
   using the SAME "genuine-defect-rejection is not a regression" accounting rule the arc already
   registered [S: `ARC4_S5.md` §2.1, "Rule, stated verbatim"]. Even a SMALL net MBPP-population
   gain is a genuine result here, because the primary target (closing the arc's own explicitly
   named clearest residual, `br_10`) is a bar independent of the MBPP count.

**What would falsify the hypothesis, stated in advance**: the saturated search still finds
nothing (would mean the size-≤5 bound, not the information content, is the true bottleneck — a
different, still-useful finding); OR the lexical gate fires on a spec whose "symmetric-sounding"
phrasing hides a genuinely asymmetric relation, producing a witness-confirmed true regression
(would mean the gate needs tightening, not that the mathematics is wrong).

---

## 7. Files consulted (verification trail)

- `runners/dsl/src/term.rs` (lines 780–1180, 2080–2145, 2460–2500, 5960–6070, 9139–9143) —
  `AntiUnify`/`FixedCount`/`Covers`/`AntiUnifyWitness`/`Substitute`/`Unify`/`StructSim`/
  `ShapeDecode`/`TransformDecode`/`DimInfer`/`GenInfer`/`TimeInfer`/`SynthEnumerate`/`ProgEval`
  variant definitions and doc comments.
- `runners/dsl/src/synth_enumerate.rs` (lines 1–130, 440–580, 1000–1130, 1330–1660, 1840–1900) —
  observational-equivalence signature/pruning implementation, saturation halt, `exclude` pre-
  seeding.
- `scripts/prog_synthesis_battery.py` (lines 150–350, 710–780, 970–1045) — `run_task_p7`'s
  `repair_oracle` CEGIS-shaped arm and its `accepted_holdout_fail`-gated counterexample feed.
- `PROGRAM_SYNTHESIS_ARC4_S6_NOTES.md`, `PROGRAM_SYNTHESIS_ARC4_STRUCTURAL_NOTES.md`,
  `PROGRAM_SYNTHESIS_ARC4_S5.md` — the measured trap/wall/residual population this document
  formalises.
- `RESEARCH_CODE_IN_THE_BRAIN.md` §0 (grading scale), §11 (never-quote-without-condition standing
  rule).
- `CLAUDE.md` — the frame/continuum invariant passage assessed in §2.3.
