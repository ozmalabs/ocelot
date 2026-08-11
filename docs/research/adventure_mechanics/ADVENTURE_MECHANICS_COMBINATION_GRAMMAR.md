# THE COMBINATION GRAMMAR — admit/retract mechanics for "use X with Y" (design adjudication)

**Status: DESIGN ONLY. No code, no seeds, no runs, no PREREG amendment in this
document.** Per the creator's own framing this is explicitly **"basically
ungrounded experiment free thought"** — not a measured rung. The precedent
followed for structure and rigor-without-code is
`docs/research/bigville/BIGVILLE_ADMISSIBILITY_GRAMMAR.md`: real outside
research grounding a proposed mechanism, with an honest header stating the
status, and — where the "free thought" framing licenses it — more than one
candidate design weighed rather than forced to a single answer.

**The question, in the creator's own words.** Two things, asked to be
connected: (1) the classic adventure-game verb — given two held
concepts/objects, attempt *use X on Y* / *use X with Y* and have the world
decide whether it means anything; (2) opening the admissibility grammar (Γ)
to **admit** a genuinely novel production, and — the primitive that does not
exist anywhere in this codebase — **retract** one that turns out wrong. The
payoff phrase: **"searching the infinite finitely."** Two mid-task
corrections from the creator, addressed explicitly in Part 3 (§3.3–§3.5),
reshaped the design after the first draft of this section: the admit/retract
decision is not a bespoke plausibility heuristic, and it is not a sequential
order-0→order-1→order-N ladder — it is the SAME N-dimensional shape solve,
MDL-governed, that the sd loop and `DimInfer` already run elsewhere in this
tree, plus fuzz-verification before any mint is trusted.

---

# PART 1 — Prior work in this repo, surveyed honestly

## 1.1 The bigville tools PoC — built and gated, but a different (narrower) mechanic

`docs/research/bigville/BIGVILLE_TOOLS_PREREG.md` ("PREREG — block 336000:
tools + inventory + ownership (adventure-game mechanics)") is real prior art
and does use the phrase *"the basic adventure-game verb — use X on Z... and
use X with Y."* It shipped as `seeds/bigville_tools.json` (1199 lines) +
`worlds/bigville_tools_world.py` (185 lines), gated by
`tests/test_tools_migrated.py` — **verified live in this session: 9/9 pass**
(`python3 -m pytest tests/test_tools_migrated.py -q` → `9 passed`).

**What it actually is, read from the code, not the prereg's prose:**

- `worlds/bigville_tools_world.py`'s `give_tool(agent, toolname, **fits)`
  mints a `Tool` node with `fit_for -> Fitness{verb, mult, effort}` children
  that the **caller supplies at authoring time** — e.g.
  `w.give_tool("Miner", "pick", mine=(1.0, 1.0))`. A knife is dual-use only
  because the test author wrote `give_tool("Cook", "knife", prep=(1.5,1.0),
  strike=(2.0,1.0))` — two fitnesses, one node, but both **pre-declared**.
  There is no path anywhere in this seed or adapter that asks "does verb V
  applied to tool T against target Z mean anything" for a **(T, V, Z)
  triple nobody has named a `Fitness` for.** The mechanic is a lookup over
  authored data, not a decision over an unbounded combination space.
- The seed declares **zero productions** (`"productions": []`, confirmed by
  loading the JSON directly) — exactly the same shape
  `BIGVILLE_ADMISSIBILITY_GRAMMAR.md` documents for the four violence seeds:
  a real subsystem with its own rules, entirely outside Γ. Every mutation in
  the adapter goes through `add_edge_unchecked` (`eng.add_edge_unchecked`,
  used throughout `bigville_tools_world.py`), never `add_edge` /
  `check_edge` — so **`use X on Z` in this PoC has never once been checked
  against the admissibility grammar.** "Is this combination admissible" is
  answered entirely by whether a `Fitness` node with a matching `verb`
  string exists on the held tool; a wrong pairing (`w.use("Bob", "mine",
  "vein", tool="rod")`) doesn't get refused by Γ, it just yields
  `last_yield == 0.0` because no `Fitness{verb:"mine"}` child exists on the
  rod. That is arithmetic, not admission.
- The PREREG's own honesty section says this outright: *"the recognition
  here is seeded by the adapter... isolated demonstrator (`self_load_only`);
  no Rust; `.so` untouched."*
- **No RESULTS document exists for this rung** (confirmed: `find docs -iname
  "*TOOL*RESULT*"` returns nothing). This is not because the work is
  unverified — the pytest gate is real and green — but because "RESULTS"
  in this project's convention is reserved for a **measured, powered
  claim against a preregistered bar** (cf. the `BIGVILLE_*_RESULTS.md`
  pattern elsewhere in the same folder, and the RUN-15/RUN-16 powered-gate
  discipline named in `CLAUDE.md`). This PoC is closer to the "self-load-only
  demonstrator" category the PREREG names itself: gate-passing, but never
  submitted to the aggregate-bar discipline the folder otherwise enforces,
  and the git history shows exactly one commit touching these three files
  (`26ca9ff`, the initial import) — it was authored, gated once, and never
  revisited.

**Honest verdict on A.1: this is real, working, gated prior art for
"tools multiply action outcomes" — it is NOT the general "propose an
arbitrary novel combination and let Γ decide" mechanic the creator is now
asking for, and conflating the two would be dishonest.** It answers "how
effective is this pre-declared combination," never "is this combination
meaningful at all." See §3.7 for how this design subsumes it.

## 1.2 The control-generalisation "adventure room" claim — design-note-only, unverified

`docs/research/agent_loop/jabberwock_control_concept_generalisation.md` and
`docs/research/agent_loop/jabberwock_control_reasons_first_design.md` are
short design notes (62 and 67 lines), dated 2026-06-26, quoting the creator:
*"it should also be able to play adventure games"* and describing a plan
where `control_effect` fits observed pre/post state to the held
`enact.json` `OperationPrimitive`s (`change_location` / `transform_attribute`
/ `exchange` / `put` / `combine` / `select` / `signal`), goals become a
standing-error on a `value_signal`, and — build-order step 5 — *"a tiny
adventure room solved by the same rules with no new code."*

**What actually landed, checked against the two notes' own "wired vs new"
tables:**

- `seeds/enact.json` genuinely has a `combine` `OperationPrimitive`
  (`"name": "combine", "postcondition": "combined(theme,co_theme)", "verbs":
  "combine,join,mix,merge,add"`) and `select_operator` exists
  (`substrate/world_adapter.py`, `seeds/enact.json`) — so the *vocabulary*
  the notes assume is real.
- `avatar_agency` (`seeds/avatar_agency.json`, `substrate/world_adapter.py`)
  is real — the locus-by-agency idea in note 1 has a landing spot.
- **A materially different, narrower piece actually got built and verified**
  by a **standalone script, not a pytest gate**:
  `scripts/verify_dynamic_control_kinds.py` (paired with
  `seeds/control_dynamic.json`, `domains/control_grounding.py`,
  `scripts/gen_control_kinds_seed.py`) — confirmed live-run-shaped (the
  script prints `PASS`/`PARTIAL` and returns exit code 0/1, the same
  discipline as the gated tests but outside `tests/`). It demonstrates a
  known control (`Push-button`) is *recognised* from a wiki-grounded prior
  and a novel control (`"Zorblatt"`, no wiki article) *mints its own*
  `ControlKind` from observation and *adjusts* it on a second observation —
  this is real, and it is the "reason first from grounded priors" thread of
  note 2, not the "combine/put/select adventure room" thread of note 1.
- **No evidence anywhere — no test file, no script, no results artifact, no
  git history — of an actual adventure-room task being solved.** Searched:
  `grep -ril "adventure_room\|control_effect\|tiny adventure"` across the
  whole tree (excluding the design notes themselves and unrelated
  `test_adaptive_control_core_migrated.py::test_..._control_effects`, a
  false positive on a different sense of "control effect" — statistical
  control, not `OperationPrimitive` fitting). `git log --all -i --grep
  "adventure"` / `--grep "combine"` return nothing beyond the docs reorg
  commit. `seeds/game_mechanics.json` was checked and is, as the task brief
  already suspected, a genre/mechanic **taxonomy read from Wikipedia**
  (verb-glossary data) — not a game-playing mechanism, and not evidence for
  this claim either way.

**Honest verdict on A.2: design-note-only.** The vocabulary it depends on
(`enact.json`'s `combine`, `avatar_agency`, `select_operator`) is real and
wired for OTHER purposes; the specific claim — *an adventure room gets
solved end-to-end by the existing goal/rollout machinery with no new code*
— was never run, gated, or reported on. It should be treated as an
**aspiration to test, not a verified precedent to build on.** §3.7 returns
to this.

## 1.3 Other search — nothing else found

`docs/CODE_MAP.md` and `docs/research/INDEX.md` were checked for adjacent
material; the only structural hit was the top-level description of the
substrate itself ("the admissibility grammar (Γ)"), already covered above.
No other seed, script, or design note references a general
propose-a-combination mechanic. `seeds/discourse.json` and
`scripts/self_extension_demo.py` / `scripts/self_extension_refinements.py`
reference `OperationPrimitive` but in the self-extension (authoring new DSL
primitives) sense, not combination search — noted for completeness, not
claimed as relevant.

---

# PART 2 — Outside literature

Real citations, web-verified this session unless flagged otherwise.
Consensus separated from contested. No fabrication — where a detail
wasn't independently re-checked it is marked.

## 2.1 Combinatorial creativity — Boden's taxonomy names exactly this mechanic

**Margaret A. Boden, *The Creative Mind: Myths and Mechanisms*
(Weidenfeld & Nicolson, 1990; 2nd ed. Routledge, 2004).** Boden's taxonomy
(web-verified this session via multiple secondary sources synthesizing the
book; not re-checked against the primary text page-by-page) distinguishes
three kinds of creativity, defined over a **conceptual space** — a
structured space of everything generable under a set of rules:

1. **Combinatorial creativity** — new ideas from unfamiliar combinations of
   familiar ones, within the *existing* conceptual space. **This is,
   definitionally, "try combining two known things."**
2. **Exploratory creativity** — traversing the existing conceptual space to
   find previously-unvisited but *reachable* points; the space's rules are
   unchanged, only the exploration is novel.
3. **Transformational creativity** — altering the *generative rules of the
   space itself*, so that points inconceivable under the old rules become
   reachable. Boden treats this as the deepest kind.

**Direct mapping (this document's own synthesis, flagged as such — Boden
does not discuss Γ or this codebase).** A `use X with Y` attempt that Γ
already admits (rung-0/1, exact recognize or a same-basis transform, §3.2)
is not creativity at all — it's recall. An attempt that Γ **generalizes to
by analogy** to an existing production (§3.3's structure-mapping rung) is
Boden's **combinatorial** case exactly: an unfamiliar pairing licensed by
an existing rule of the space. An attempt that forces `DimInfer` to mint a
genuinely new `LatentDimension` (§3.2) is closer to Boden's
**transformational** case: the conceptual space's own rule set (which
dimensions exist) is what changes, not just which point in it gets visited.
This gives the design a principled three-way split that is not arbitrary —
it is Boden's own taxonomy, read onto the machinery this repo already has.

## 2.2 Insight problem solving and functional fixedness — the *use X on Z* half, empirically

**Karl Duncker, "On problem-solving," *Psychological Monographs* 58(5)
(1945, German original 1935).** The candle problem: subjects fail to see a
tack-box as a candle-platform because it is functionally fixed in its
presented role (container). **Canonical, high-confidence.**

**N.R.F. Maier, "Reasoning in humans II," *Journal of Comparative
Psychology* (1931)** — the "two-string problem," the companion classic;
noted for completeness, not independently re-verified this session.

**R.E. Adamson, "Functional fixedness as related to problem-solving: a
repetition of three experiments," *Journal of Experimental Psychology*
44(4):288–291 (1952).** Web-verified this session. Replicated Duncker's
box/gimlet/paperclip problems with **preutilization** manipulations (using
the solution object in its ordinary function first, vs. not). Headline
finding, verified: **baseline solve rate on the box problem was only ~23%**
under standard instructions; when the object-word ("box") was visually cued
apart from its function-word ("box **of matches**"), solve rate rose to
~47–55%. **The finding is that novel-affordance discovery has a low
empirical base rate, and it is driven by how the object is REPRESENTED**
(lexically/perceptually), not by raw search over possible uses. Consensus,
frequently replicated in different forms since (a full independent
replication census wasn't run this session — treat the exact percentages as
this-session-verified but the broader "extensively replicated" claim as
high-confidence-not-re-verified).

**H.G. Birch & H.S. Rabinowitz, "The negative effect of previous experience
on productive thinking," *Journal of Experimental Psychology* 41(2):121–125
(1951).** Companion finding (high-confidence from established knowledge,
not independently re-verified this session): prior use of an object in one
function measurably **suppresses** discovery of an unrelated function later
needed — functional fixedness is not just "objects have a default use," it
is actively **primed by recent use**, an interference effect.

**Design consequence.** The empirical picture is not "given two objects,
people freely search the space of possible combinations and usually find
the useful one." It is: **discovery is representation-gated, low base
rate, and actively suppressed by recent conflicting use.** Mapped onto
this design: an agent should not brute-force `use X on Y` over a
combinatorial product of held objects — the trigger for even ATTEMPTING a
combination should be gated by the agent's own re-representation of X/Y
along dimensions Γ's existing productions already key on (the same move
`categorise_by_shape` already makes elsewhere in this codebase) — i.e., the
representation IS the search-space pruner, exactly as Adamson's word-cueing
manipulation was. This is an argument for the shape-projection design in
§3.2, from a different literature than the one the creator's steer named.

## 2.3 Analogical reasoning / structure-mapping — the mechanism for "admit by generalization"

**Dedre Gentner, "Structure-mapping: a theoretical framework for analogy,"
*Cognitive Science* 7(2):155–170 (1983).** Web-verified this session.
Core claims: analogy is a **structural alignment** between a base and a
target — relational commonalities (predicate-over-predicate structure), not
surface/attribute similarity, are what transfer; the **systematicity
principle** says a relation embedded in a larger mutually-connected
relational system is preferentially imported over an isolated one.
Consensus; Structure-Mapping Engine (SME) is the most-cited computational
model of analogy.

**Design consequence — this is the literal mechanism for "admit-by-analogy"
named in the creator's steer.** A novel `use knife on Z` where Γ already
holds `use knife with food -> quality*` is not blind trial: it is a
**relational** transfer — "tool T has fitness F for verb V" is the
predicate structure, and Gentner's systematicity principle says the
transfer is licensed exactly when the SAME relational schema
(`fit_for(T, V) -> multiplier`) applies to the new (T, V) pair, independent
of T and V's surface identity (knife vs. pick; food vs. ore). This is not a
new idea for the design to invent — it is what the existing `TransformDecode`
/ rung-2 machinery already computes structurally (§3.2): a one-parameter
delta over an existing schema is exactly a structure-mapping transfer with
the schema held fixed and the arguments varied.

## 2.4 Conceptual blending — what a newly-admitted production actually represents

**Gilles Fauconnier & Mark Turner, "Conceptual integration networks,"
*Cognitive Science* 22(2):133–187 (1998); *The Way We Think: Conceptual
Blending and the Mind's Hidden Complexities* (Basic Books, 2002).**
Web-verified this session. Blending composes two **input mental spaces**
through a **generic space** (their shared abstract structure) into a
**blend space** that can carry **emergent structure** absent from either
input — a genuinely new concept, not just a new relation between old ones.
Fauconnier & Turner treat blending as a basic cognitive operation on a par
with analogy and categorisation.

**Design consequence — an honest scope boundary, not a feature to build.**
Γ's `Production` is `(src-pattern, edge-type, tgt-pattern, where, weight)`
(`runners/dsl/src/grammar.rs`) — it can only ever license a **new edge**
between EXISTING node types. A structure-mapping-licensed `use X with Y`
(§2.3, §3.2 rung 2/3) stays inside this: X and Y keep their identities, a
new relation between them becomes admissible. That is Fauconnier & Turner's
simpler case (closer to what they'd call composition without much emergent
structure). A **genuine blend** — "torch used on ice" yields "steam," a
node that is neither a Torch nor Ice nor an edge between them, with
properties neither input has — is a different, larger primitive: it would
need the sd loop's existing node-minting machinery (`sd_mint_quantum`,
already used for shape quanta) composed WITH `add_production`, and that
composition is **not designed here**. Stating this boundary explicitly
matters because it is easy to conflate "Γ admits a new edge" with "the
agent invented a new concept" — they are not the same claim, and this
design only makes the former.

## 2.5 Adaptive forgetting — the literature the retraction half needs

**Blake A. Richards & Paul W. Frankland, "The persistence and transience of
memory," *Neuron* 94(6):1071–1084 (2017).** Web-verified this session.
Central claim: forgetting is not (only) decay/failure — in a
**changing, noisy** environment, transience is **adaptive**: the goal of
memory is not maximum-fidelity storage but **optimizing future
decision-making**, so retaining only what remains useful, and shedding what
does not, is functionally correct, not a bug. Consensus-framing paper
(a synthesis/perspective, not a single experiment), influential.

**Mechanistic substrate — synaptic/engram-level, web-verified this
session via multiple 2023–2025 reviews** (`Nature Reviews Neuroscience`
2021 "Forgetting as a form of adaptive engram cell plasticity"; `Molecular
Psychiatry` 2023/2024 engram reviews; `Trends in Neurosciences` 2025 "The
cost of remembering: engram competition as a flexible mechanism of
forgetting"): forgetting is realized by (a) **synaptic remodeling /
pruning** that lowers reactivation probability of a specific engram
(activity-dependent — weak, rarely-reactivated traces are preferentially
pruned, often microglia-mediated), and (b) **engram competition /
retroactive interference** — new, overlapping memories compete for
consolidation resources and actively suppress older ones. Two distinct
mechanisms, both empirically supported, not fully reconciled in the
literature as of these reviews (flagged as an open area, not settled).

**Design consequence — two distinct retraction triggers, not one.** The
literature licenses (a) a **disuse** trigger (a production never
reactivated/never matched → prune, mirroring synaptic pruning of
under-used synapses) and (b) a **failure/interference** trigger (a
production whose predictions are repeatedly contradicted by later evidence
→ suppress, mirroring engram competition when a better-fitting alternative
exists). §3.4 designs both as separate signals, deliberately not collapsed
into one "confidence score," because the literature itself keeps them
separate mechanisms.

## 2.6 Curiosity / novelty — what should trigger an attempt in the first place, and the repo already has an answer

**C. Kidd & B.Y. Hayden, "The psychology and neuroscience of curiosity,"
*Neuron* 88(3):449–460 (2015).** Web-verified this session. Survey framing
curiosity as an intrinsic-motivation drive for information gain, tied to
dopaminergic circuitry and influential in decision-making.

**D.E. Berlyne (1960, foundational; "collative variables" —
novelty/complexity/uncertainty/conflict — drive an inverted-U, "Wundt
curve," preference-vs-novelty relationship: too-familiar and too-novel are
both under-preferred relative to a moderate-novelty optimum).**
Web-verified this session via secondary sources describing the Wundt-curve
lineage (Wundt 1874 → Berlyne 1960/1971); not independently checked against
Berlyne's primary text this session — flag as high-confidence-canonical,
not re-verified.

**J. Schmidhuber, "Formal theory of creativity, fun, and intrinsic
motivation," *IEEE TAMD* 2(3):230–247 (2010); P-Y. Oudeyer, F. Kaplan &
V.V. Hafner, "Intrinsic motivation systems for autonomous mental
development," *IEEE Trans. Evolutionary Computation* 11(2):265–286 (2007).**
Web-verified this session. The **learning-progress** reframe of curiosity:
what should be intrinsically rewarding is not novelty/surprise itself, nor
raw compressibility, but the **rate of improvement** in prediction/
compression — an agent that stays motionless in noise (maximally
surprising, permanently) gets zero reward under this model, because there
is no learning progress to be made there. This is explicitly presented in
the literature as **correcting** the naive novelty-maximization story
(the Wundt-curve account gets the *shape* right — an inverted U — but the
mechanistic account of *why* is progress-rate, not novelty-per-se).

**This is where Part B connects directly back to the codebase, as the task
brief asked.** `seeds/learning_progress_curiosity.json` **already
implements the Schmidhuber/Oudeyer account, by name, in its own
description**: *"Curiosity/attention gated by learning progress — the RATE
of surprise-reduction on a held item... NOT by raw surprise."* This is not
a coincidence to note in passing — it means **the literature does not
complicate the existing model, it validates it**, and it hands this design
a ready-made trigger: **a combination attempt should be gated by the SAME
learning-progress machinery already wired for curiosity elsewhere,** not by
a bespoke "is this combination novel enough" heuristic invented for this
mechanic alone. Concretely: a `use X with Y` pairing that is either (a)
already admitted (zero learning progress possible — recall, not discovery)
or (b) has zero structural overlap with anything Γ holds (no held schema to
make progress against, per §2.3's systematicity requirement) sits at the
two under-motivated ends of the Wundt curve; a pairing with **partial**
structural overlap — matches an existing schema on some but not all
predicate slots — is exactly the moderate-novelty zone where a rung-2/3
attempt (§3.2) both CAN make progress and SHOULD be attempted.

## 2.7 Category learning — what it means for Γ to "hold" a concept, and which model the design implies

**R.M. Nosofsky's Generalized Context Model (exemplar-based, 1986/1987)**
vs. **prototype models** vs. **F.G. Ashby et al.'s COVIS
("competition between verbal and implicit systems"), *Psychological
Review* 105(3):442–481 (1998)** — a dual-system account with an explicit
**rule-based** (hypothesis-testing, verbalizable) system and an implicit
**procedural** system. Web-verified this session (secondary sources
synthesizing the models; COVIS citation itself high-confidence-canonical,
not independently re-checked against the primary 1998 article this
session).

**Design consequence.** `Production` in this codebase is unambiguously
**rule-based** in the COVIS/category-learning sense: `(src-pattern,
edge-type, tgt-pattern, where-clause, weight)` is an explicit,
inspectable, verbalizable hypothesis about which triples are admissible —
not a similarity-weighted exemplar store. This matters for the admit
decision (§3.2): a newly-admitted production should be judged as a RULE
(does it generalize correctly across the *class* of (T, V) pairs its
where-clause covers?), not as a single exemplar (did it work once). This is
exactly why fuzz-verification (§3.3) is not optional polish — a rule-based
representation that is trusted on one exemplar is trusting the wrong unit
of evidence for its own representational kind, which is precisely the
"coincidental fit" failure mode named in §3.3.

## 2.8 Is there a known rate law for how minimal grammar/program size must grow as the problem space grows? (the creator's specific question)

The creator asks precisely: as a problem domain's instance space grows, how
does the minimal covering grammar/program size grow, and is that
relationship characterized well enough to give ADVANCE confidence in
tractability, rather than discovering it empirically each time. This is
real, established territory on both a theoretical and an empirical side.
The honest answer has three parts: a real theorem exists at the
qualitative/structural level; a real hardness result caps how far a rate
law can ever be turned into a practical advance-guarantee; and the closest
concrete empirical analogue found this session is a real sublinear power
law, but for a neighboring, not identical, problem.

**(a) The theorem that actually connects compression to tractability —
Occam learning.** A. Blumer, A. Ehrenfeucht, D. Haussler & M.K. Warmuth,
"Occam's Razor," *Information Processing Letters* 24(6):377–380 (1987);
expanded in "Learnability and the Vapnik–Chervonenkis Dimension," *Journal
of the ACM* 36(4):929–965 (1989). Web-verified this session. The formal
result (an **Occam algorithm**): if a learning algorithm can, for any m
labeled examples drawn from a concept class of description-length ≤ n,
always find a CONSISTENT hypothesis whose size is bounded by a polynomial
nᵅmᵝ with β < 1 — i.e., the hypothesis compresses, growing SUB-linearly in
the number of examples for fixed concept complexity n — then the concept
class is **PAC-learnable**, with sample complexity polynomial in n, 1/ε,
1/δ. **This is exactly a theorem-shaped answer to "is there research on
this."** It is not a heuristic claim that compression is good practice; it
is a formal guarantee that a compression RATE (hypothesis-size growth
sub-linear in instance count) directly IMPLIES a tractability guarantee
(efficient learnability with bounded samples). Confidence: high — citation
and core statement web-verified this session; the exact polynomial
exponents/constants in the original theorem were not independently
re-derived from the primary source.

**Honest limit on (a): the theorem is conditional, not universal.** It says
IF such a compressing algorithm exists for a concept class, THEN that class
is tractable — it does not say every concept class admits one, and it
gives no domain-independent formula for what β *should* be for a brand-new
domain (a `use X with Y` combination space, say). Whether Γ / the sd loop's
codebook growth IS an Occam algorithm for the space of "meaningful
combinations" is an empirical question about THAT specific space, not
something the theorem answers a priori. This mirrors exactly what P3→P7-C
already discovered the hard way (§3.2): the qualitative MDL principle held
throughout, but the correct compressing GRAIN was domain-specific and had
to be measured, not derived in advance.

**(b) MDL / Rissanen, and Solomonoff's ceiling — the same conditionality,
restated information-theoretically.** J. Rissanen's original MDL
formulation (1978) and P. Vitányi & M. Li's *An Introduction to Kolmogorov
Complexity and Its Applications* (the standard reference; not
independently re-checked against a specific edition this session)
formalize the same two-part-code tradeoff (model cost + data-given-model
cost) already underlying every MDL claim this repo makes (§3.2's P3/P7-C
precedent uses exactly this shape). **Solomonoff induction** (a universal
prior M(x) = Σ 2^−ℓ(p) over programs p consistent with x, web-verified this
session) gives an even stronger EXISTENCE result — Solomonoff's
completeness theorem guarantees convergence to the true generating program
for ANY computable environment, in the limit — but it is a limit/
asymptotic-optimality result, not a rate law: M itself is **not
computable** (it sums over an infinite, undecidable program space; every
practical approximation trades optimality for computability), and no
general closed-form rate at which the "effective" (weight-dominant) program
space must grow with a growing problem space is established for arbitrary
domains. The honest reading of what this session's search actually
surfaced: the QUALITATIVE principle (shorter/more general programs are
exponentially favored, and this is provably the correct prior in a
well-defined asymptotic sense) is settled theory; a domain-general
QUANTITATIVE rate is not, because it cannot be — it depends on the true
Kolmogorov complexity of the domain's actual generating structure, which is
domain-specific and, for any given domain, uncomputable to determine
exactly.

**(c) A hard ceiling on ever computing the true answer, even offline — the
Smallest Grammar Problem.** M. Charikar, E. Lehman, A. Lehman, D. Liu, R.
Panigrahy, M. Prabhakaran, A. Sahai & A. Shelat, "The Smallest Grammar
Problem," *IEEE Transactions on Information Theory* 51(7):2554–2576
(2005). Web-verified this session. Given a FIXED string, finding the
smallest context-free grammar that generates exactly it is **NP-hard to
approximate within a small constant factor** (proven inapproximable below
ratio 8569/8568 unless P=NP); the best known efficient algorithms achieve
only O(log³n) / O(log(n/m*)) approximation to the true minimum grammar
size m*. **This is directly relevant and sobering, not decorative:** even
in the STATIC, offline, already-easier case (one fixed corpus, not a
growing/online one; a context-free grammar, not this codebase's richer
weighted-admissibility Γ), computing the actual MDL-optimal grammar is
provably intractable in general. This is a strong, concrete reason this
project's own P3→P7-C had no choice but to MEASURE the right grain
empirically rather than derive it (§3.2) — and an equally strong reason no
closed-form advance-confidence rate law should be expected for Γ's
combination-space grammar either. **Meta-confidence in tractability,
honestly stated, cannot come from "solve for the optimal grammar size in
advance" — that sub-problem is itself intractable in general** — it can
only come from (a)'s conditional guarantee (IF sub-linear compression is
OBSERVED to hold, THEN tractability follows) applied empirically, per
domain, exactly as this repo already does it.

**(d) The closest concrete EMPIRICAL analogue found this session — Heaps'/
Herdan's law, and its honest limits as an analogue.** H.S. Heaps,
*Information Retrieval: Computational and Theoretical Aspects* (1978); G.
Herdan (1964, earlier). Web-verified this session. A well-established,
robust EMPIRICAL power law for a structurally related — not identical —
problem: as corpus size (token/instance count) N grows, VOCABULARY size
(distinct TYPES) V grows sub-linearly, **V(N) = k·Nᵝ with empirically
observed β typically 0.4–0.6** for natural-language corpora. This is a
genuine, precisely-stated growth-RATE law, of exactly the shape the
creator asks whether exists — **for a flat vocabulary (a type inventory),
not for a compositional GRAMMAR (hierarchical productions/rules).**
Flagged honestly: this is the closest thing found this session to "an
actual characterized rate," and it is directly suggestive — a growing
instance space robustly needs only a SUBLINEARLY growing distinct-thing
inventory to describe it, across languages and domains — but it is not a
proven analogue for Γ's production count or the sd loop's codebook size
specifically, and no search this session surfaced a grammar-specific
(rather than vocabulary-specific) version of Heaps' law with a comparably
established exponent. Presented as **suggestive corroboration, not a
load-bearing number** — transplanting β≈0.5 as a literal prediction for
Γ's growth rate would be exactly the kind of unverified numeric transplant
this project's own culture (the retracted-optional-dep-note discipline in
`CLAUDE.md`) warns against.

**(e) Program-synthesis / DSL-scaling literature, and grammar-induction-by-
compression algorithms — searched, honest null on a general curve.** The
FlashFill/FlashMeta/Polozov lineage (Gulwani et al.; O. Polozov's
dissertation "A Framework for Mass-Market Inductive Program Synthesis") and
FlashFill++ (POPL 2023) were searched specifically for an empirical
grammar-size-vs-benchmark-coverage curve. **None was found this session** —
the literature discusses DSL scaling qualitatively (larger DSLs needed for
broader coverage; search-space blow-up as an engineering cost) but no
quantitative growth-rate curve analogous to Heaps' law surfaced. Stated as
an honest gap in what this session's search found, not as evidence the
literature lacks one. Grammar-induction-by-compression algorithms — Sequitur
(Nevill-Manning & Witten) and ADIOS (Y. Solan, D. Horn, E. Ruppin & S.
Edelman, "Unsupervised learning of natural languages," *PNAS*
102(33):11629–11634, 2005, web-verified this session) — directly
instantiate "grow a minimal grammar from a growing corpus" and are
evaluated on real corpora, but the results surfaced this session report
grammar-size bounds RELATIVE TO OTHER COMPRESSORS (e.g., Sequitur's output
size bounded relative to an LZ-style factorization baseline), not a general
grammar-size-vs-corpus-size asymptotic curve.

**Answering the creator's question directly, in one paragraph.** Yes —
there is real research on this, and it resolves cleanly into exactly the
shape this project's own culture prefers: a **clean qualitative theorem
exists** (Occam learning: compression ⟹ tractability, conditionally) and a
**clean hardness result caps how far it can be made into an
advance-computable guarantee** (the Smallest Grammar Problem is NP-hard to
approximate even offline, for the easier static case) — so **meta-
confidence in tractability cannot be obtained by computing or deriving the
rate in advance for a new domain; it can only be obtained the way this
project already obtains it, empirically, per domain, by observing whether
the compressing property (Occam's precondition) actually holds** — which is
exactly what P3's failure and P7-C's fix (§3.2) already did: measured, not
derived. The one genuinely characterized SUBLINEAR growth rate found this
session (Heaps' law, β≈0.4–0.6) is real and precisely citable, but for a
neighboring, simpler problem (flat vocabulary) than Γ's (compositional
grammar) — offered as suggestive corroboration that "growing instance
spaces need only sublinearly-growing description spaces" is a broadly
observed empirical pattern, not as a transplantable number for this
codebase.

---

# PART 3 — The design

## 3.1 The generalized mechanic, stated once

A world adapter (any of them — bigville, an adventure-room world, a doom or
walker world) observes an agent attempt **`use(X, verb, Y)`** where the
triple `(type(X), verb-as-edge-type, type(Y))` is **not currently admitted**
by Γ (`checker.check_edge` returns `Type1NoProduction`, both types already
in-vocabulary — this is deliberately scoped to Type-1, not Type-2; a
completely unknown node/edge type is a different, prior problem, namely
vocabulary acquisition, not combination admission). The question this
design answers: **what decides whether Γ should admit a new production for
this triple, and what decides when an admitted-but-wrong production should
be retracted?**

Both halves are designed as **the same primitive already proven elsewhere
in this codebase for a different surface (shape/vision quanta, program
synthesis, transform inference)**, not as new inventions. §3.2 states the
core correction from the creator's two steers: this is not a sequential
ladder, it is an **N-dimensional shape solve** governed by **MDL**, verified
by **fuzzing** before any admission is trusted.

## 3.2 Admission is an N-dimensional shape solve, MDL-governed — not a sequential ladder

**The corrected framing, in the creator's own words:** *"solving problems is
an N dimensional shape solver with arbitrary inputs. MDL means we want as
few as possible (but no fewer), and that they abstract to solve different
problems because problem shapes are typically bounded well below
infinite."* An earlier draft of this document described admission as a
sequential ladder (try exact match, then try one dimension, then try
another, then mint). That framing is retracted here in place, not kept
alongside — it does not match how this repo's own machinery actually works,
and the creator corrected it directly.

**What actually happens elsewhere in this codebase, and what a combination
attempt should reuse:**

- **`DimInfer` / `LatentDimension` minting** (CLAUDE.md, "BASE-AS-DIMENSION
  + the frame/continuum invariant"; `runners/dsl/src/shape_decode.rs`,
  `dim_infer` and the surrounding `rung 2` code, confirmed present —
  `grep`'d live: `coord_ints`, `DimensionGenerator`, `rotation90`/
  `reflections`/`scale2`/`modular` generators). The worked example CLAUDE.md
  gives is exact: *"rotating a flat 2D rectangle in Z gives an XY change you
  can't replicate without Z"* — the residual is **coupled across the
  observed X and Y dimensions simultaneously**, and that cross-dimensional
  coupling PATTERN is the signal a new dimension (Z) is needed. It is not
  "try X alone, then try Y alone, then give up and mint" — the solver looks
  at the coupling across however many dimensions the input actually
  implicates, arbitrary in number and identity, in one shot.
- **Quanta navigation** (CLAUDE.md, "Quanta navigation LANDED") is
  explicitly **N-dimensional with per-dimension resolution and
  per-dimension residual splits**, decoded together (foveated, incremental
  reuse) — again, multiple axes carrying their own grain simultaneously,
  not resolved one at a time.
- **A `use X with Y` proposal is a point in exactly this kind of space.**
  The "dimensions" a combination attempt implicates are not fixed in
  number or identity per attempt: a knife-on-food attempt implicates (tool
  material, tool sharpness class, target edibility, verb-class); a
  key-on-lock attempt implicates (shape-fit, material, verb-class) — a
  different, possibly larger or smaller, dimension set. **Admission is:
  does the (X, verb, Y) triple decode against the CURRENTLY HELD dimension
  set — possibly crossing several of Γ's existing `Production`
  where-clause predicates and `Fitness`-style schemas at once — or does the
  residual (the part of the observed/hypothesized outcome the held
  dimensions can't account for) COUPLE ACROSS dimensions in a way that
  demands a genuinely new one?** The former is Gentner's structure-mapping
  transfer (§2.3) read at whatever dimension-count the triple actually
  needs, not "rung 2" as a fixed single-delta case. The latter is a mint,
  exactly as `DimInfer` mints a `LatentDimension` today for shape residuals
  — generalized here to a `LatentDimension` over the **combination space**
  itself (e.g., a genuinely new axis like "requires liquid contact,"
  observed the first time water is combined with something and no held
  dimension explains the effect).
- **The order-0/order-1/order-N ladder named in the F-16/motor material**
  (CLAUDE.md's "SHAPES, NOT NUMBERS" section: *"the order-0/order-1/order-N
  viability ladder (reflex / held-ratio / search) that the F-16 arc built
  directly inside `shape_decode.rs`"*) is worth citing as **one domain's
  instance** of the same generative primitive (a flight-control system
  choosing reflex vs. held-ratio vs. search per situation) — but it is not
  the template to copy structurally. It is evidence the SAME underlying sd
  loop machinery already generalizes across a very different domain, which
  is exactly the argument for reusing it here rather than building a
  bespoke adventure-mechanics heuristic.

**MDL is the actual governing pressure, not a threshold to tune by hand —
and this repo has a MEASURED prior failure that names the exact hazard.**
`docs/research/program_synthesis/PROGRAM_SYNTHESIS_ARC_SUMMARY.md` §3 (P3):
the sd loop's merge-at-mint step, applied at **depth-1 grain**, produced
**16 construction quanta against a registered [40, 220] band** — the MDL
join was **family-collapsing**: too aggressive a merge conflated distinct
constructions into one over-general quantum. The fix, measured at P7-C, was
**not** abandoning MDL — it was finding the right GRAIN for it to operate
at (**idiom-grain** chunk mining, 2–4-statement recurring idioms, escaped
the depth-1 collapse and mined 15 survivors). The summary's own words:
*"the band was wrong about GRAIN, not about MDL."*

**This is exactly the two-sided failure mode the creator's "as few as
possible, but no fewer" names, and it is a MEASURED precedent in this exact
codebase, not a hypothetical:**

- **Over-compress (too few productions, family-collapse).** A newly-minted
  combination production written at too coarse a grain (e.g., a single
  `Tool -uses_on-> Target` production with a where-clause so loose it
  admits "knife on ice," "knife on stone," and "knife on person" as the
  identical case) reproduces P3's exact failure: distinct problem-shapes get
  conflated, and the production's predictions become wrong for most of the
  class it was over-generalized to cover.
- **Under-compress (too many productions, never abstracts).** A production
  minted per-instance (one production per literal `(knife, prep, stew)`
  triple, never generalizing to `(knife, prep, ANY food)`) fails the "no
  fewer" side — it never earns its keep across a family of structurally
  similar combinations, which is precisely what makes the combination space
  finitely searchable in the first place (see below).
- **The right grain is an open, re-measurable question, exactly as it was
  for P3→P7-C — this design does not claim to know it in advance,** and
  says so rather than picking an arbitrary depth. A future measured rung
  (explicitly out of scope here — this document is design-only) would need
  to do for combination-grain what P7-C did for idiom-grain: try a grain,
  measure over- vs. under-generalization against a held-out set of
  combination attempts, and re-grain if the band is missed, the same
  discipline, not a new one.

**The payoff claim, stated explicitly (this is the mechanistic answer to
"searching the infinite finitely").** The reason a finite Γ can search an
unbounded `every-concept × every-concept` combination space is **not**
that most combinations are simply never attempted (that would just be
pruning, not search). It is that **MDL pressure, applied at the right
grain, forces a minted production to be GENERAL** — to abstract across a
*family* of structurally similar combinations, not just the one instance
that triggered the mint — **because the real space of problem-SHAPES
(as opposed to problem-INSTANCES) is empirically bounded well below
infinite.** A production minted to license "knife with food" should, if
MDL is doing its job at the right grain, already cover "cleaver with meat"
and "paring-knife with fruit" without a fresh mint for each — the same way
CLAUDE.md's transform-decode rung means a **rotated tromino needs zero new
mints**, because rotation was already a held dimension, not a new problem.
The combination space is searchable finitely exactly to the extent the
agent's held dimension set (Γ's productions + the sd loop's
`LatentDimension`s) has been MDL-compressed to the true shape-count of the
domain, not the instance-count.

## 3.3 Fuzz-verification — the trust gate before any admission is believed, reusing the ARC6 constructed-witness methodology

**The failure mode this closes, named precisely in this repo's own
measurements.** `docs/research/program_synthesis/PROGRAM_SYNTHESIS_ARC6_VERDICT.md`
and `PROGRAM_SYNTHESIS_ARC6_TIER0.md` repeatedly demonstrate that a proposal
can satisfy the ONE case tried — the accepted program computes the right
answer on every REVEALED row — while being wrong in general. The
VERDICT document's own term for this is **"coincidental fit"**: of 15 newly
accepted program-synthesis candidates in that rung, **7 were coincidental
fits**, refuted only once **constructed** (type-driven-mutation-generated)
probe inputs were run against them — e.g. id `290`'s accepted program
`(len(a[-1]), a[-1])` passed the revealed rows by returning the **last**
sublist instead of the **longest**, caught by 12/20 constructed probes
disagreeing. TIER0's HS1 bar registered **"zero coincidental fits"** as a
precondition for trusting a conversion, generated **18–24 constructed
probes per candidate** by type-driven mutation of the row schema, and
**discarded any generated input equal to a revealed or held-out row** (so
the fuzz set is genuinely novel, not a relabeling of what was already
checked).

**This is precisely the risk a newly-minted combination production carries,
and for the identical structural reason.** A `use knife with Y` production
admitted (or minted) on the strength of ONE successful attempt (knife +
this specific stew) is exactly as unverified as a program accepted on one
revealed row — it might be a coincidental fit (the production's
where-clause happens to be satisfied by this stew's specific attributes,
not because the relational schema genuinely holds for the class of foods
it will now be checked against). **Design: before a newly admitted-or-minted
production is trusted (moved from "provisional" to a normal, weight-bearing
member of Γ), it must survive a fuzz sweep** — constructed variations of X
and Y generated by type-driven mutation of THEIR attribute schema (vary the
tool's material/sharpness/size within its type; vary the target's
edibility/hardness/state within its type), each checked against the
production's where-clause and, where a ground-truth oracle is available
(a simulated outcome, a teacher, or a held verdict Term), against the
predicted outcome. The same discard-if-duplicate-of-a-real-attempt
discipline applies, and the same **18–24-probe order of magnitude** is a
reasonable starting point precisely because it is the number this repo
already measured as sufficient to catch 7/15 coincidental fits in a
structurally analogous setting — not picked freshly for this design.

**Where fuzzing sits relative to the N-dimensional solve (§3.2): fuzzing is
orthogonal to it, not sequential with it, and answers a different
question.** §3.2 decides WHETHER a production should be admitted/minted at
all (does the observed effect decode against held dimensions, or does the
coupling demand a new one). §3.3 decides whether a production, once
admitted, is TRUSTWORTHY — i.e., whether the grain and generalization
claimed in §3.2 actually holds up under variation, which is exactly the
question a single successful use cannot answer. A production can be
correctly-derived by the shape solve and still be a coincidental fit if the
solve itself over-fit the one observation (the family-collapse failure
mode of §3.2, discovered here rather than at mint time) — fuzzing is the
independent check that catches that case specifically.

## 3.4 The missing Rust primitive — production retraction (design only)

**Confirmed absent, this session:** `grep -rn "remove_production\|
retract_production\|del_production\|drop_production"` across `runners/`,
`substrate/`, `domains/`, `seeds/` returns nothing. `add_production`
(`runners/dsl/src/substrate.rs:809-815`) exists:

```rust
pub fn add_production(
    &mut self,
    p: crate::grammar::Production,
) -> crate::grammar::ProdIdx {
    let idx = self.checker.grammar.add(p);
    self.gamma_epoch.bump();
    idx
}
```

`Grammar::add` (`runners/dsl/src/grammar.rs`) pushes onto a dense
`productions: Vec<Production>` and records the new `ProdIdx(u32)` (its
positional index) into an `index: FxHashMap<(src_type, edge_type,
tgt_type), SmallVec<[ProdIdx; 2]>>`. `ConsistencyChecker::check_edge`
(`runners/dsl/src/checker.rs`) looks up candidates via this index and then
directly indexes `self.grammar.productions[pi.0 as usize]` — **`ProdIdx`
values are load-bearing positional handles**, referenced both inside the
index and (per `CheckOutcome::Admitted(SmallVec<[ProdIdx;2]>)`) returned out
to callers for "explain" purposes.

**Structural consequence: `remove_production` cannot be a `Vec::remove` /
`swap_remove`.** Either would shift or repoint another production's
`ProdIdx`, silently corrupting the index and any caller holding a stale
handle (a stored "this edge was admitted by productions [3, 7]" record
would now point at the wrong productions). **The design that matches both
the structural constraint and this codebase's own existing idiom for
"gone but the identity is preserved" is a tombstone, not a deletion** — the
same pattern already used elsewhere (CLAUDE.md's `retire_duplicate_gap`:
`status='retired'` + edge removal, never a hard delete of the node).
Proposed shape (design only, not Rust to write here):

- Add a `retracted: bool` (or `status: ProductionStatus` if a richer state
  machine is wanted — see §3.5's graduated case) field to `Production`.
  `ProdIdx` positions are **never reused or shifted**.
- `Grammar::remove(&mut self, idx: ProdIdx)` sets `productions[idx.0].retracted
  = true`. It does **not** remove the entry from `index` (the (src, edge,
  tgt) → ProdIdx map) — instead, `candidates()` or (more likely, to keep
  `candidates()`'s hot-path signature unchanged) `check_edge`'s scan over
  `cand` skips a retracted production the same way it already skips a
  production whose where-clause evaluates false. This is a **one-line
  change to the existing loop** in `checker.rs` (`if
  self.grammar.productions[pi.0 as usize].retracted { continue; }` before
  the `production_admits` call), not a new index structure.
- `Substrate::remove_production(&mut self, idx: ProdIdx)` bumps
  `gamma_epoch` exactly as `add_production` does — **this is the same
  signal the meta-Γ growth path already listens to** (CLAUDE.md:
  `add_production` bumps `gamma_epoch`; `codebook_epoch` / the sd loop's
  re-decode machinery is gated on epoch bumps elsewhere). A retraction
  should invalidate exactly the same downstream caches an admission does —
  **Γ shrinking is not structurally different from Γ growing**, and the
  epoch mechanism already generalizes to both without new machinery,
  provided retraction bumps it identically.
- A `Type1NoProduction` outcome on a triple that WAS admitted before its
  admitting production(s) were retracted is then indistinguishable, at the
  checker level, from a triple that was never admitted — which is the
  **correct** behavior: retraction should make the checker forget the
  production was ever special, not leave a residual "used to be OK" bias.
  Anything that wants a record of "this was once admitted, then retracted"
  (for the retraction-policy bookkeeping in §3.5, or for an agent-facing
  explanation) needs to keep that as **graph data** (a `RetractedProduction`
  node or similar, minted alongside the `retracted=true` flip) — the same
  split this codebase already draws everywhere else between "what Γ/C
  decide" and "what the graph remembers about the decision."

**What this primitive does NOT attempt to solve here (explicitly out of
scope for this design):** rule effects bypass the checker entirely today
(`BIGVILLE_ADMISSIBILITY_GRAMMAR.md` §2.3: `rewrite.rs`'s `Effect::AddEdge`
writes via `graph.insert_edge` directly, not `checker.check_edge`). A
retracted production has **zero effect on Rule-authored edges** under the
current architecture — only on edges attempted via `Substrate::add_edge` /
the `is_edge_admissible` / `admissible_moves` probe surface. This is the
same bypass `BIGVILLE_ADMISSIBILITY_GRAMMAR.md` already names as the
load-bearing gap in that document; nothing in this design closes it, and a
combination-attempt world adapter that wants retraction to matter must
route `use X with Y` attempts through the gated `add_edge` path (or the
`gated: bool` flag reserved on `apply_rule`), not through raw rule effects
— worth flagging explicitly so a future implementer does not assume
retraction "just works" against rule-authored mutations.

## 3.5 Retraction policy — informed by the adaptive-forgetting literature, tradeoffs stated explicitly

Per §2.5, the literature keeps two mechanisms distinct rather than
collapsing them into one score, and this design keeps them distinct too:

**(a) Disuse-based retraction (synaptic-pruning analogue).** A production
minted for a combination class that is never matched again within some
window is a candidate for retraction — mirroring activity-dependent pruning
of under-reactivated engrams (§2.5). *Tradeoff:* this requires a
usage-window parameter (how long is "never matched again" long enough) that
is exactly the kind of scalar-knob-instead-of-shape this codebase's own
"SHAPES, NOT NUMBERS" rule (CLAUDE.md) warns against inventing freshly.
The honest answer is that this should be the SAME staleness mechanism
already built for other graph-resident structures in this tree (CLAUDE.md
names "stale/retire lifecycles as rules" for `SpaceQuantum`s in the quanta-
navigation work) — reuse that lifecycle rule shape rather than invent a new
timeout for productions specifically. Flagged here as a real design
decision this document does NOT resolve: which existing staleness rule
generalizes, and at what grain (the same open-grain caveat as §3.2).

**(b) Failure/interference-based retraction (engram-competition analogue).**
A production that predicted an outcome (via its weight/where-clause, or via
the fuzz sweep of §3.3 initially passing) and is then **contradicted by
later evidence** — either a real subsequent use that fails, or a later,
broader fuzz sweep that a narrower one at mint time would have missed — is
a stronger, more direct retraction signal than disuse. This is the failure
mode named as first-class in the creator's steer: **"a production that was
fuzz-verified once but then fails a later fuzz-check, or that only ever
survived on a coincidental fit that a broader fuzz sweep would have caught
at admission time"** is exactly ARC6's coincidental-fit failure mode
(§3.3), just discovered post-hoc instead of at mint time. Design: a
retracted-on-failure production should be tombstoned with a `RetractedProduction`
record (§3.4) carrying **which fuzz probe or real use refuted it** —
mirroring the ARC6 verdict document's own discipline of recording the
refuting evidence (constructed inputs, paired id lists), not just a boolean
"this was wrong."

**Graduated response, not a binary — explicit tradeoff.** Ostrom's
graduated sanctions (already cited in `BIGVILLE_ADMISSIBILITY_GRAMMAR.md`
§2, not re-derived here) argue enforcement should scale with severity/
repetition rather than jump straight to the harshest sanction. Mapped onto
retraction: a single fuzz-probe failure on an otherwise-useful production
might better be handled as a **weight down-adjustment** (Γ's own weighted-
admissibility machinery, `Production.weight`, already exists for exactly
this — a lower weight makes the production less likely to be SELECTED among
several admitting candidates, per `admissible_moves`'s softmax-over-weight
semantics) rather than an immediate tombstone; only **repeated** failure
(a threshold the same open-grain question as (a) applies to) escalates to
retraction. *Tradeoff, stated plainly:* down-weighting-then-retracting is
gentler and matches the graduated-sanctions literature, but it means a
production can sit in Γ, admitting SOME triples correctly, while accruing
failures on others — the same production instance is not uniformly right
or wrong, which is only coherent if the fuzz/failure bookkeeping is scoped
per matched-triple-class, not per production as a whole. This is a real
design complexity this document surfaces rather than resolves: **is the
unit of retraction the production, or a class of triples within its
where-clause's coverage?** If MDL grain (§3.2) is right, a
correctly-grained production's coverage class IS the natural retraction
unit and the two questions collapse; if the grain is wrong (family-collapse,
§3.2's P3 precedent), they do not, and partial retraction (narrowing a
where-clause rather than retracting the whole production) may be the
correct move — which this primitive does not design (it would need a
`narrow_production` sibling to `remove_production`, not attempted here).

## 3.6 Meta-confidence in tractability — why the shape-solve approach should be EXPECTED to keep scaling, not merely observed to have

§2.8 answers the creator's question — *"is there a known rate at which the
minimal grammar must grow, such that we can have meta-confidence in
tractability"* — as honestly as the literature allows: **a real theorem
(Occam learning, §2.8a) connects compression to tractability, but
conditionally; a real hardness result (the Smallest Grammar Problem,
§2.8c) proves the rate itself cannot be computed in advance, even offline;
the closest characterized EMPIRICAL rate found (Heaps' law, §2.8d) is real
but for a neighboring, not identical, problem.** What follows from this for
the design, stated precisely rather than hopefully:

**Meta-confidence here is conditional, not unconditional — and this
codebase already has the right EMPIRICAL habit for exactly this
conditionality.** §3.2's P3→P7-C precedent (measure the grain, don't
derive it; re-measure when the band is missed) is not a workaround for the
absence of a general theorem — it is the CORRECT response to what §2.8
establishes: the Occam-learning theorem's precondition (does a compressing
hypothesis exist for THIS space) is an empirical property of the specific
combination space, not a fact derivable from first principles for an
arbitrary domain, and the Smallest Grammar Problem's hardness result says
it can never be replaced by a closed-form computation even in the easiest
static case. So "does the combination-space Γ keep scaling as it's pointed
at a new domain" is not knowable in advance by calculation — but it IS
testable, cheaply, per domain: does minted-production count grow
sub-linearly against attempted-combination count, the same measurement
shape as Heaps' law's V(N) = k·Nᵝ, just substituting "distinct admitted
production classes" for "distinct vocabulary types" and "combination
attempts" for "corpus tokens". **This is a concrete, cheap, reusable
diagnostic this design should carry forward as a standing measurement, not
a one-off**: whenever a combination-space Γ is pointed at a new world
(bigville tools, a future adventure-room adapter, any other domain), the
FIRST thing to check is whether its own production-count-vs-attempt-count
curve is sub-linear (β < 1, Occam's precondition, empirically) — if it is
not, the domain does not compress under this Γ shape and no amount of
further engineering the admit/retract mechanics will make it tractable;
that would be the "clean honest null" this project's culture rewards
(CLAUDE.md: *"the arc succeeds if it establishes [X], whether the answer is
no, provided the answer is clean"*), not a failure of the design.

**The empirical corroboration this design can honestly point to, sourced
from what is actually in this repo's own record (not asserted beyond it).**
`CLAUDE.md`'s own "SHAPES, NOT NUMBERS" section states, of its own
authority, that the same two generative primitives (the sd loop and Γ)
were independently rediscovered as the right tool **"in two different
embodiments, in the same week"** — the F-16 flight-control arc and the
humanoid arc — and that the finding *"generalises past both."* A third,
earlier instance is traceable in the same document under a different name:
the Omniglot/AbS handwriting arc ("GENERATION AND READING ARE ONE MODEL")
and the quanta-navigation vision work both apply the identical sd-loop/Γ
shape to a THIRD, unrelated domain (visual stroke recognition and spatial
navigation, respectively), landing before the F-16/humanoid retrospectives
that named the pattern explicitly. Three independent domains (vision,
flight control, humanoid motor control) converging on the same finite
generative machinery is real empirical evidence FOR the expectation that a
fourth domain (combination-space Γ) will behave the same way — but per
§2.8, it is evidence, not a proof, and the honest framing is: **expect it
to keep working because the pattern has held three times and the
theoretical precondition (Occam-learnability) is a testable, not
assumable, property — not because a rate law guarantees it in advance.**

## 3.7 Honest scoping note

**Is the bigville tools PoC (§1.1) subsumed, a dead end, or orthogonal?**
**Subsumed as a special case, with one caveat.** The PoC's `Fitness{verb,
mult, effort}` data is exactly the shape a rung-1/rung-2 admission (§3.2)
would recognize-or-transform against, once tool-use triples are routed
through `add_edge`/`check_edge` instead of `add_edge_unchecked` — a
pre-declared `(knife, prep, food)` `Fitness` is a **held exemplar of the
schema** a genuinely novel `(knife, prep, Y)` attempt would structure-map
against. The caveat: subsuming it requires the bigville tools world adapter
to be rewired onto the checker path, which this design does not do (design
only) and which `BIGVILLE_ADMISSIBILITY_GRAMMAR.md` already flags as a
broader, pre-existing gap (rule effects bypass the checker generally). It
is not a dead end — it is real, correct data at the wrong layer (arithmetic
instead of admission), and this design's payoff is specifically making that
layer real.

**Is the control-generalisation adventure-room claim (§1.2) evidence FOR
this direction, or an unverified aspiration to treat skeptically?**
**Treated skeptically, per the survey's own finding: it is unverified.**
Nothing in §1.2 constitutes evidence either for or against this design —
there is no run, gate, or artifact to weigh. What IS usable from that
thread is the **vocabulary** (`combine`/`select`/`signal` as
`OperationPrimitive`s, `avatar_agency`) as a plausible landing spot for a
FUTURE adventure-room world adapter that exercises this design once built —
but the specific claim that the existing goal/rollout machinery already
solves such a room "with no new code" should not be assumed true when
scoping that future work; it should be re-tested, honestly, the same way
every other claim in this codebase earns its RESULTS document.

## 3.8 Two genuinely different candidate shapes, weighed (free-thought framing)

Following `BIGVILLE_ADMISSIBILITY_GRAMMAR.md`'s own precedent of presenting
more than one shape rather than forcing an answer:

### Shape (i) — admission-only, retraction deferred (lighter)

Build §3.2 (N-dimensional shape-solve admission) and §3.3 (fuzz-verification
before trust) fully; leave §3.4/§3.5 (the retraction primitive and policy)
as a follow-on. *Pros:* smaller first build; a fuzz-gated admission is
already most of the safety value (a coincidental fit that fails 18–24
constructed probes is refused BEFORE it ever pollutes Γ, so retraction's
job shrinks to "handle drift after the world changes," a rarer case than
"handle a bad mint," per §2.5's two distinct mechanisms). *Cons:* Γ can
still only grow — the "searching the infinite finitely" claim is
incomplete without a way to shed a production that was fuzz-clean at mint
time but is wrong under a LATER, broader fuzz sweep or a changed world
(exactly the failure mode the creator's steer named as first-class); this
shape leaves that named failure mode formally unhandled, not merely
deferred in convenience.

### Shape (ii) — admission + retraction as one MDL loop (the shape this document recommends, heavier)

Build §3.2–§3.5 together, so that admission and retraction are two
directions of the SAME MDL pressure (§3.2's "as few as possible, but no
fewer") rather than a growth mechanism plus a separately-bolted-on cleanup
pass. *Pros:* matches the creator's own framing most literally — MDL is
symmetric (both family-collapse and never-abstracts are failures), so a
mechanism that only grows is only half of MDL; retraction-on-repeated-
fuzz-failure (§3.5b) is the SAME check as admission-time fuzzing (§3.3),
just re-run periodically, so there is genuinely one mechanism, not two.
*Cons:* larger design surface before any of it is real (the open-grain
question of §3.2/§3.5 is unresolved either way, but shape (ii) has more
places it bites — admission grain AND retraction-unit granularity, per
§3.5's unresolved production-vs-triple-class question); a periodic re-fuzz
of every live production is a real cost this document does not size.

**No forced choice.** Shape (i) is the honest minimum that delivers new
capability; shape (ii) is the honest complete answer to the creator's own
framing. Which to build first is explicitly left open, consistent with the
"free thought" instruction for this task — but if a first rung is chosen,
it should be committed to being followed by the other, not treated as a
substitute (the same staging caution `BIGVILLE_ADMISSIBILITY_GRAMMAR.md`
states for its own two shapes).

## 3.9 What this design does not resolve (stated, not hidden)

- **The MDL grain for combination productions** is named as an open,
  re-measurable question (§3.2), by direct analogy to P3→P7-C, not answered
  here — resolving it needs a measured rung of its own.
- **The retraction unit** (whole production vs. triple-class within its
  where-clause) is surfaced as unresolved in §3.5, with a plausible
  follow-on primitive (`narrow_production`) named but not designed.
- **Genuine conceptual blending** (a new emergent NODE, not just a new
  edge between held nodes) is explicitly out of scope (§2.4) — this design
  covers Fauconnier & Turner's simpler composition case, not their full
  emergent-structure case.
- **Rule-effect bypass of the checker** (§3.4's closing note) is a
  pre-existing, larger gap this design does not close — retraction (like
  admission) only binds on the `add_edge`/checker path.
- **Sizing the fuzz-probe count and the "later, broader sweep" cadence**
  for retraction (§3.5b) borrows the 18–24-probe order of magnitude from
  ARC6 as a reasonable starting point, not a derived-for-this-purpose
  number — it has not been re-measured for the combination-space domain.
