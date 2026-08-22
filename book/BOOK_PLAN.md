# BOOK_PLAN — the plan of record

**Status: plan, not draft.** This is the structure the book is written to.
Companions: `BOOK_VOICE.md` (register, style contract, influences),
`BOOK_SOURCES.md` (where each chapter's evidence lives),
`BOOK_DOSSIERS.md` (per-chapter claim + evidence), `README.md` (index).

**Decision already taken and not to be relitigated without cause:** one book,
nineteen chapters plus an introduction, a prologue, one front-matter chapter,
and an epilogue. Narrative-led — the engineering leads, the formalism arrives
late. The five formal papers (`01`–`05` in this directory) remain the citable
preprints; chapters draft *by subtraction* from them and from the dossiers.

---

## Where the material stands

| # | title | kind | what it establishes |
|---|---|---|---|
| 01 | The Law of Graphic Equalisation | theory | `G=(g,r,Γ)`; `G_t → P(G_t) → C_t → G_{t+1}`; frame-relative identity; residual; **discrete sufficiency as an open hypothesis** |
| 02 | Seldon Manifolds | theory | reachable-future geometry, acceptable futures, control as manifold deformation |
| 03 | The Law of Narrative Momentum | theory | history as a first-class dimension; directional persistence; revision cost |
| 04 | Narrativium | theory | deformation budget; no cross-frame accounting; **no path integration** |
| 05 | A Constructive Realisation of Graphic Equalisation | implementation | one reference executor for 01 |

Evidence base not yet in any of them: ~1,700 PREREG/RESULTS documents under
`docs/research/` across 16 threads, ~29K lines of Rust primitives
(`shape_decode.rs` 8.9K, `term.rs` 16.7K, `space_quantize.rs`, `strokes.rs`,
`future_manifold.rs`), an 8,000+ test regression bench, and two external repos
(`~/ozma`, `~/ozmadev/internal`) holding the origin story and the theory drafts.

---

## The spine

A book needs one question running under every chapter, and this material
already has one. It is **residual**: the part of an observation that does not
fit what you already hold, and what a system does with it.

It is not a theme imposed on the chapters — it is literally the same object in
all of them. Paper 01 makes residual a primitive of the dynamics. Chapter 06
argues it is the *only* admissible channel for growth. The eye's depth
dimension **is** a temporal residual nothing flat explains. A minted quantum is
a residual that recurred. A `SelfConcern` is a residual the agent files about
itself. And the method chapters are the same idea turned on the author: a
retraction is a residual between what was claimed and what was measured, kept
rather than absorbed.

That gives the book its title candidates, in order of preference:

1. **What Doesn't Fit** — the spine, plainly. Subtitle: *A graph theory of
   cognition, and the machine built to test it.*
2. **Residual** — sharper, more austere, closer to the formal vocabulary.
3. **The Shape and the Number** — leads with the book's antagonist (below)
   rather than its subject.

## The antagonist

Good technical books have something to argue *against*, and this one's is
specific and measured rather than rhetorical: **a number standing where a shape
belonged.** It appears in the first chapter as a theoretical distinction, and
then keeps turning up as a *defect* — the learning-rate regress where each rate
needs its own rate; 60 count-divided learners across 8 embodied seeds, none of
them inside the faculties that match shapes; a recogniser breaking 44 of 55
contests alphabetically; an imported setpoint from a frame the system does not
have, killing cells in two layers.

The book's arc is therefore not "here is a theory, here are applications." It
is: *here is a distinction; here is what goes wrong wherever it is violated;
here is what becomes possible where it is honoured.*

## Narrative first — the paper's structure, inverted

A paper states its claim, then earns it: abstract, method, result. **A book
does the reverse — it earns the claim, then states it.** That inversion is not
a coat of paint on the prose; it changes the part order, because a theory
chapter placed before the reader has felt the problem is a chapter answering
questions nobody has asked yet.

So the material gets re-sequenced against how a paper would order it. The
engineering leads. The theory arrives as **resolution**, not premise.

**One guardrail, because this is the way narrative-first books usually fail:**
leading with narrative does *not* mean withholding the claim. Every chapter
still states what it establishes in its opening paragraph — the style contract
below is unchanged on that point. The narrative is *how the claim was earned*,
never a suspense device. Mystery-box structure is the failure mode here, and
it is avoidable by keeping claim-up-front at chapter grain while the *book*
level runs discovery-first.

## Introduction: how I got here

**The book opens in a boring work meeting.** Not as a hook — because it is
literally where the causal chain starts, and because every later step was the
same move made again at a larger scale. The introduction's job is to explain
why a book about an eye, a town, and a theory of collapse begins with a KVM
switch, and it does that by refusing to compress the chain.

The chain, each link a real artefact with a date — and every arrow in it is
the same question asked again (see below):

1. **A silly problem.** Play games during a dull meeting: keyboard and mouse
   driving the gaming PC while the work laptop's call keeps running, audio from
   both blended so nobody can tell. PipeWire does the audio. Nothing does the
   rest properly — hardware KVMs are clunky, don't handle audio, don't scale;
   the software options are duct tape.
2. **So build one.** Ozma: a software-defined **KVMA** router — keyboard,
   video, mouse, *audio* over a network, a node permanently attached to each
   machine presenting as HID + audio + NIC, and **the USB cable never moves**
   (`~/ozma`, first commit 2026-04-01).
3. **The problem kept getting bigger.** Routing a keyboard is the same *kind*
   of problem as routing video, which is the same kind as audio, as network
   traffic, as distributing power through a building. Things with labels,
   connections with labels. One typed map, from a single USB mouse to a data
   centre — and a 77,000-word specification saying so.
4. **The tooling bill.** Building it with LLM assistance was expensive, not
   because the models were weak but because every model-to-model connection
   needed bespoke glue. So: pull that thread too — context compression, tiered
   benchmarks, brevity and hint protocols, a stable of fine-tuned coder models
   (`internal/research/compressor.py`, `brevity.py`, `bench_tiered.py`,
   `token_counter.py`, `internal/models/ozma-coder-*`).
5. **A semiotic graph layer for models.** A protocol where a lead model
   delegates to specialists and the shared knowledge base is, again, a typed
   map of labelled things and labelled relations.
6. **The collision, unplanned.** The map that routes keyboard signals and the
   map that coordinates models **are the same map.** Two unrelated problems,
   one answer, arrived at by accident. That is the moment the project stops
   being about KVM switches.
7. **Then the key turns out not to be the graph.** It is **Γ** — the
   admissibility grammar. What matters is not the map but *what the map is
   allowed to become*: a finite, decidable, inspectable statement of which
   edges may exist at all, with the graph as the thing it governs. Everything
   downstream in this book is a consequence of that inversion.
8. **Then the LLM becomes unnecessary.** If the grammar generates the
   admissible moves and the substrate realises one of them, the model was
   scaffolding, not mechanism. This is the direct ancestor of the standing
   "no pretrained model in the decision path" discipline the capability
   chapters run under.
9. **Then physics.** *"This becomes a physics paper masquerading as computer
   science. We need to look there for prior art"* — the author's own note,
   dated 2026-04-25. The tick was already possibility-set-then-realise. Quantum
   measurement is the regime where the distinction between *indexed
   possibility* and *realised history* is experimentally irreducible — you
   cannot replace the alternatives with ignorance about an already-real
   classical value. So the conjecture: collapse is not exceptional in kind, it
   is the especially visible instance of the actualisation primitive every tick
   uses.
10. **And collapse leaves residual** — what the realised successor did not
    absorb. Which is the spine of everything after this page.

### The method, which is the introduction's real content

The chain above is *what* happened. **This is how**, and it is two steps, run
over and over:

> **1. What assumptions have been made that aren't being said?**
> **2. What can be taken away — and what happens if it does?**

Both steps matter and the second is the one usually skipped. Step 1 alone
produces a list of caveats. Step 2 is what makes it a procedure: take the
assumption out, and find out whether anything observable was resting on it.
If nothing was, the claim just got shorter at no cost. If something was, you have
located what the thing actually needs.

**This is minimum description length, run on your own beliefs.** Not as an
analogy — as the same criterion the substrate uses to decide whether an
observation is worth a new codebook entry (chapter 4: mint if and only if it
compresses; *noise does not exist, only signals you have not grounded*). The
question "is this real or am I imagining structure" has no observer-independent
answer. The question "does removing it cost anything" has a computable one.

Which means **the author's method and the substrate's growth mechanism are the
same operation**, and the introduction should say so plainly, because it is the
book's tightest single connection between how the work was done and what the
work is. Step 1 finds the residual — the part of a statement its words did not
cover. Step 2 tests whether the residual was load-bearing.

Not asked once per problem — asked repeatedly, of the answer, until the answer
stops changing. It is a fixpoint procedure run on one's own beliefs, and the
introduction should present it as exactly that, because the reader is about to
watch a `run_rules` fixpoint do the same thing to a graph for nineteen
chapters.

**The worked example, and it should be told at length: it took about ten
iterations to believe the word "everything."**

"Everything is a graph" is a sentence almost nobody means. *Everything* is
hyperbole by default — and the tell is that even the sincere uses are scoped
without noticing. "Everything in computing" names a boundary. "Everything on
the planet" names a boundary. Each qualifier is an unnamed assumption
smuggled in as ordinary English, and each one has to be found by asking the
question again of the sentence you just wrote. Ten passes, roughly, before the
claim was stated at the size it was actually meant: not everything-within-
some-scope, but **everything**.

This is the most transferable thing in the introduction, and it wants three
supports:

**It is the residual operation, applied to a sentence.** An unnamed assumption
is precisely what a statement did not absorb — the part of the claim's meaning
that the claim's words failed to cover. The book's spine appears here first,
before any graph, as a habit of reading one's own writing. Say so once, plainly,
and let the recurrences land later.

**Ten iterations is a mint, not a delay.** The residual recurred, and recurred,
and only after it kept recurring did the scope word finally change. That is the
sd loop's own growth condition — mint when the residual *recurs*, not when it
first appears — running in a person before it ran in code. The introduction
should not apologise for taking ten passes; it should point out that a system
that minted on the first pass would have hallucinated.

**And every scope word was a step-2 removal.** "Everything in computing" —
take the qualifier away; does anything observable break? No. "Everything on the
planet" — take it away; anything break? No. Ten times, each removal costing
nothing, until what remained was the claim that had been meant all along. The
word did not get bigger. The description got shorter.

**There is a second habit, and it is the one that generates work.** The two
steps evaluate a claim you already have. The forcing function produces claims:
*force everything through the substrate's own loop, and triage what resists.*
Whatever will not go through is either **(a)** a limitation of the framework —
fix the framework — or **(b)** implemented the wrong way, almost always because
it was inherited. Neither answer is "leave it", which is the whole value: a
vague awkwardness becomes a question with a fix attached.

The introduction should carry this alongside the two steps, and should use the
photon eye as its example, because category (b) is invisible from inside and RGB
is the case every reader already believes is neutral. It is also worth naming
that this project's architecture rule *is* the forcing function written down —
agent logic in graph rules and engine primitives, host language only for
translating the world in and out — so every refusal by that rule is a triage
question already asked.

**Step 2 is what the book calls an ablation.** Chapter 1 removes the
self-avoiding term from the drift and the long-lag crossover dies — so that term
was carrying it. Chapter 3 *deletes* a tiebreak and a residual appears where
there had been none — so the tiebreak had been destroying information. Chapter
10 ablates a drive and a preference goes to zero at zero interval width — so
nothing else was quietly supplying it. Those are not three techniques. They are
step 2, institutionalised, pointed at code instead of at sentences. The
introduction should name that, because it is what makes the method transferable
rather than a personal habit.

**And it is the book's antagonist, from the other side.** A number standing
where a shape belonged is *always* an unnamed assumption: `1/n` asserts
stationarity without saying so; a threshold asserts a scale; a fixed weight
asserts a comparison domain. Ch. 15 catalogues sixty of them across eight
seeds. Ch. 16's standing rules are the same question asked of measurement — a
baseline quoted as a count held an unnamed condition, and a status line was
reusable as an excuse for ten days precisely because its condition went
unnamed. **The introduction's method, the audit's finding and the method
chapter's rules are one thing seen at three grains**, and the introduction is
where the reader is handed the tool.

### The guardrail this claim needs, stated where the claim is made

A book whose introduction says *everything, and I mean everything* has to
disarm the obvious objection immediately, and the honest disarmament is
already in the record rather than newly invented for the occasion:

- **Universal in form, frame-relative in every instance.** Axiom −1 is that
  there is no operational view from nowhere: every distinction is made in some
  frame. So "everything is a graph" is not a claim to a frameless God's-eye
  description — it is the claim that the *form* holds wherever you stand, while
  every actual measurement remains indexed to a frame. That reading is
  stronger, and it is what the theory already says.
- **Falsifiers, per instance, stated by the author.** The QM bridge has one.
  The capability chapters have theirs. A universal claim that cannot be
  attacked anywhere is crankery; this one names where to attack it, chapter by
  chapter.
- **The convergence audit's own discipline.** When the project went looking
  for whether unrelated engineering had independently re-derived the theory's
  structures, it treated the theory's own jargon as a **negative** signal and
  classified every hit rather than counting it — because the failure mode of
  "everything is X" is finding X everywhere you look. The guard against
  universal claims is built into the method that supports them, and the
  introduction should say so before a reader has to ask.

### Three things the introduction must get right

**Register.** A press-style version of this story already exists
(`internal/research/docs/article_popular.md`, *"Everything Is Connected — And
One Guy Figured Out How"*) and it is useful raw material and the wrong voice.
Its framing — lone genius, sweeping claim, urgency — is exactly the register
the rest of the book disowns. Tell it first-person and cool: a plumber pulled a
thread and it did not stop coming.

**The QM step, stated as the source states it.** Not *"my graph explains
quantum mechanics."* The papers make a **conditional functional bridge**,
explicitly aligned with QBism (state and probability assignment frame-relative,
measurement an action, outcome a new event for that frame), and they state the
falsifier: **the bridge fails if the mapping cannot preserve quantum-instrument
composition, Born-rule and contextual probability constraints, and
sequential-measurement statistics without a second transition primitive** — and
they say outright that "a process can be described as selection and update" is
*not sufficient evidence*. Told with that falsifier attached, it is the most
interesting paragraph in the introduction. Told without it, it is the exact
failure ch. 15 spends a chapter cataloguing.

**The cost, named once and plainly.** The chain above was not free, and an
introduction that presents four months of it as clean intellectual momentum is
lying by omission. One or two sentences, in ordinary words, with no jargon and
no dramatisation: it took a serious toll. Then move on — **the account of what
it did belongs in the epilogue, not here**, for a reason that is structural
rather than squeamish (see the epilogue dossier).

**What to leave out.** The trilogy's governance, prediction-horizon and
AGI-trajectory arguments belong to a different book. The introduction's
strongest move is to *not* pitch: no speedup figures, no timelines, no
alignment thesis. Just the chain, and one sentence about what it cost.

### What the introduction sets up

- **The prologue that follows** — Life, chess, Doom — is now *the first trials
  of the thing the introduction just described*, which is what those three
  actually were.
- **The lineage, credited early.** The typed-map idea is restored, not
  invented: the Lisp-machine generation built graph-native hardware and the
  industry took a forty-year detour for economic reasons. Positioning as
  restorer rather than inventor is both accurate and disarming, and it belongs
  in the introduction rather than a defensive later section.
- **The ending.** The chain has no terminus by construction — every step was
  "pull the thread one more time." An introduction that is honest about
  starting with no destination is what earns the epilogue's *there is no
  natural ending*, and the two should be written as a pair.
- **The timeline, stated plainly because it is checkable.** KVMA router
  2026-04-01; the physics turn 2026-04-25; the substrate repo's own import
  2026-08-10; the theory paper rewritten 2026-08-12. Four months from a
  meeting-avoidance hack to a collapse theory with a falsifier, in public git
  history.

## Prologue: three toys

**Open where it actually started.** The first things the substrate ever ran
were Conway's Game of Life, then chess, then Doom — and those three, in that
order, teach the entire formalism without stating any of it. They are the
book's opening, and they replace the abstract "here are the definitions"
chapter a paper would need.

- **Life** (`domains/conway.py`) is a graph rewriting itself, with nothing
  added: no goals, no world, no cognition. And it is already the book's thesis
  in miniature, because **state is encoded structurally — as node type,
  `AliveCell` / `DeadCell` — not as a number in a field.** Γ decides which
  `transitions_to` edge is admissible; the transition never commits the edge,
  it asks the consistency checker as an *oracle* and then mutates atomically.
  A reader who follows Life has met `G=(g,r,Γ)`, admissible possibility,
  collapse, and shape-instead-of-number, without one of those words appearing.
- **Chess** (`domains/chess.py`) makes Γ visible as the thing it always was:
  **the legal-move relation.** Piece type encodes colour and kind so
  productions match the piece directly; admissibility enumerates the moves;
  choosing among them is a *separate* question. That distinction —
  *what may happen* versus *what does* — is the one the whole book runs on, and
  chess hands it over for free. It also sets the standing discipline at the
  origin: **python-chess is used as a FEN oracle, never as the substrate.**
- **Doom** adds the two things a board game cannot: a world that does not wait
  for you, and a body inside it. It also supplies the book's first honest null,
  which is why it belongs in the prologue rather than a later chapter — a
  "geometry" recognition channel measured **at chance, AUC 0.508**, retired and
  replaced by texture. The reader learns, on page fifteen, what this book does
  with a result that fails.

**The prologue's real argument is chronological honesty.** These three predate
the preregistration discipline that governs everything after them — there is no
PREREG/RESULTS pair for Life or chess; they live in code and git history. That
is the book's first turn: *the method in this book was not designed, it was
paid for* — and the reader is about to watch the bill arrive.

## The parts, in reading order

**Part I — The Eye** (ch. 1, incl. the physics coda). Build an organ. Discover that its constants
must fall out rather than go in; that it has to move to see; that its failure
modes are the only honest evidence its mechanisms are real; that the form-cortex
path dies for an arithmetic reason; and — the turn the whole book pivots on —
that **the dimensions of sight cannot be stored, only discovered from the
relations between frames.** The physics chapter follows immediately as the
eye's downstream: a law of motion minted from pixels with no seeded constant.

The reader ends Part I holding a question they arrived at themselves: *if time
and depth are not in any frame, where are they?*

**Part II — What the eye forced** (ch. 2, 3, 4). Now the theory, in the
order the question demands it: the frame invariant first (in-frame is integer;
the continuum lives in the map between frames — the answer to the question Part
I raised), then shape versus rule (execution is not growth; residual is the
only growth channel), then the loop in code. Note that 07 comes **before** 06
here, inverting the dossier order below — as a paper 06 is the parent, as a
chapter 07 is the one the reader is already reaching for.

**Part III — The same loop, everywhere else** (ch. 5–9).
Characters, speech, space, programs, bodies. These land differently once Part
II is in hand: the recurrences are recognitions rather than repetitions. **This
is the part that most needs the cross-references** — propose/decide in 10, 11
and 14; the frame invariant in 10, 12 and 14 — each named as a recurrence, each
pointing back to the eye.

**Part IV — Minds among minds** (ch. 10–13). Emotion, development, grounding
failure, coercive control, and a town. The largest single body of evidence in
the tree after vision — ~114 psychology documents and ~202 bigville documents —
and the part where the substrate stops being a perceiver and becomes a
*subject among other subjects*. It belongs after Part III and before the
formalism for a narrative reason: everything in it is the same machinery the
reader has already watched being built, pointed at people.

**Part V — The minimal statement** (ch. 14). The axioms, placed *late*,
where a paper would place them first: *here is the smallest thing all of that
was an instance of.* `G=(g,r,Γ)`, possibility and collapse, frame-relative
identity, residual as a primitive — and one executor that realises it. A reader
who has watched fourteen capabilities grow from one loop meets the formalism as
compression, which is the only way axioms are ever pleasant to read.

**Part VI — How to believe any of it** (ch. 15, 16). The audit, and the method.
The prologue's promise, paid in full.

**Part VII — The unbuilt frontier** (ch. 17, 18, 19). Reachable futures,
narrative momentum, narrativium, and the precise composition that would make
them measurable and does not exist yet.

### What Part V's lateness costs, and why the prologue covers it

A book cannot go a dozen chapters using `Γ` and "collapse" without saying what
they are — which is exactly the job the three toys do. Life gives state,
transformation and admissibility; chess gives the may/does distinction; Doom
gives a world and a body. **The prologue is the minimum viable formalism, taught
by construction rather than declaration**, and it needs no theorems, no proofs
and no axiom numbering to do it.

Part V is then the *complete* statement of something the reader has been using
informally for four hundred pages — which is the only way axioms are ever
pleasant to read. The one addition the front matter still owes is vocabulary:
a single page fixing `G=(g,r,Γ)`, residual, and Γ as terms, pointing back at
which toy demonstrated each.

### The reveal Part V can pull off, and its guardrail

There is a genuine structural gift in this material, and only the narrative-led
order can use it. The theory (papers 01–04) was written independently of most
of the engineering, and this project's own audit went looking for whether the
engineering re-derived the theory's structures **without aiming at them** —
grepping for the natural-language vocabulary each signature would produce if
independently rediscovered, treating the theory's own jargon as a *negative*
signal, and classifying every hit rather than counting it
(`THEORY_CONVERGENCE_AUDIT.md`, `RAVANA_CONVERGENCE_AUDIT.md`).

In a paper that audit is a curiosity. In a book where the reader has just
spent Parts I–IV inside the engineering, it is the turn: *the thing you have
watched being built by trial and retraction was independently predicted.*

**The guardrail is the audit's own classification**, and the chapter must carry
it: not every site was independent convergence — some were explicit
application, and the audit separates them precisely so this claim cannot be
overstated. Told with that separation intact, it is the strongest thing in the
book. Told without it, it is the exact defect the book spends Part VI arguing
against.

## One piece of front matter, non-negotiable

After the prologue, before Part I: three or four pages called **"How to read
the numbers in this book."** Every interval, every null, every retraction, and
the rule that a mechanism proven synthetically is not a benchmark result. A
compressed trailer for ch. 16, placed early because a reader who does not know
how the numbers were made has no reason to credit Parts I–IV. It also lets
every later chapter drop its methods boilerplate and simply report.

**It opens on the drift**, which is the single best argument for its own
existence. The eye's fixational drift reproduced Engbert's published
self-avoiding-walk signature to two decimal places — α_short 1.1553, α_long
0.7590 against a paper's 0.79±0.11 — and it **drove nothing**. Its only
consumer was the ruler that measured it. No test went red. It was caught
because someone noticed the result was too clean, and it was one of **sixteen
inert instruments found in a single arc, not one of them caught by a gate.**
Then: *the fix was to wire the drift into the image — and everything
downstream depended on it.*

## The trim — one book, nineteen chapters

**Decision: one book.** The spine only pays off if one reader meets every
recurrence, so the answer to length is *merging*, never dropping a thread.
Four merges take it from twenty-three chapters to nineteen, and each merge is
one a reader benefits from rather than tolerates:

| merge | why it is better merged than split |
|---|---|
| physics **into** the eye, as a coda | it *is* the eye's downstream; a law of motion minted from pixels reads as the eye's last act, not a separate capability |
| emotion **+** development | Harlow and the marshmallow test are the affect machinery *demonstrated*; separating them makes the emotion chapter abstract and the development chapter unmotivated |
| narrative momentum **+** narrativium | momentum is the dimension, narrativium the budget spent moving along it; neither is built yet, and two thin unbuilt chapters are worse than one honest one |
| the law **+** the executor | Part V's whole rhetorical move is *"here is the smallest thing all of that was an instance of"* — followed immediately by one machine that obeys it |

The resulting book, with each chapter's source dossier:

| ch. | title | from |
|---|---|---|
| — | **Introduction: how I got here** | `~/ozma`, `~/ozmadev/internal/research/` |
| — | **Prologue: three toys** | `domains/conway.py`, `domains/chess.py`, `docs/research/doom/` |
| — | **How to read the numbers in this book** | compressed ch. 16 |
| 1 | **The Eye** (+ physics coda) | dossiers 09, 13 |
| 2 | The frame invariant | 07 |
| 3 | Shape and Rule | 06 |
| 4 | Dynamic quantisation | 08 |
| 5 | One-shot characters | 10 |
| 6 | Speech and word meaning | 11 |
| 7 | Space as a belief | 12 |
| 8 | Constructions propose, execution decides | 14 |
| 9 | One sensorimotor core, six bodies | 15 |
| 10 | Emotion, and what it is for | 16, 17 |
| 11 | When grounding fails | 18 |
| 12 | Coercive control | 19 |
| 13 | The town | 20 |
| 14 | The law, and one machine that obeys it | 01, 05 |
| 15 | A number where a shape belonged | 21 |
| 16 | Preregistration as an engineering method | 22 |
| 17 | Seldon manifolds | 02 |
| 18 | Narrative momentum and narrativium | 03, 04 |
| 19 | The open problem | 23 |
| — | **Epilogue: there is no natural ending** | — |

The dossiers below keep their paper numbers, because they are the *source
artefacts* — the preprints stay citable and each chapter drafts by subtraction
from one or two of them. Chapter numbers are the book's; dossier numbers are
the record's.

**What stays uncut, at any length:** retractions, intervals, ch. 12's ethics
protocol, and the nulls. Trim mechanism description before evidence; trim
inventory before argument; never trim the parts that make the claims
believable.

## Epilogue: there is no natural ending

The search for a natural ending point for the substrate failed, and **that is a
finding, not a gap in the writing.** State it as the closing chapter, because
every part of the theory predicts it:

- **Termination is frame-relative** (paper 01). A graph does not finish. It
  stops being admitted by a containing frame — which is a fact about the
  frame, not a completion of the graph.
- **The extensive frontier is unbounded by construction.** Unknown is absence,
  first-class; there is always one more step outward, and it is never stored
  complete — you store the finite observed part *and the fact that it does not
  end.*
- **The loop mints while residual recurs.** Every fixpoint in this book is
  local. `run_rules` reaching fixpoint means *nothing further is admissible
  right now*, never *there is nothing further.*
- **And the project is goal-using, not goal-seeking** (`CLAUDE.md`). A
  benchmark is a target to aim at so the aim can be corrected — never the thing
  the work exists to reach. A book about competence that generalises has no
  last capability by construction; if it had one, the thesis would be false.

### The other thing that has no natural ending: the writer

The epilogue carries a second admission, and it is the one that cannot be
moved earlier: **the process rewrote the writer while it was being written.**
The author's own account — recatalogued, with *new entries in my grammar*, and
an understanding of infinity that was not there before.

**That sentence is written in the book's own vocabulary, which is exactly why
it belongs at the end.** In the introduction, "new entries in my grammar" is a
figure of speech a reader has no way to parse. After nineteen chapters, Γ is a
specific object, minting is a specific operation, and residual is a specific
thing — so the sentence stops being a metaphor and becomes a **literal
description in the terms the book spent four hundred pages defining.** A reader
who has watched a codebook grow by minting on recurring residual knows what is
being claimed about a person, precisely, without a word of explanation. Placed
early it is grandiose; placed here it is the last recurrence of the pattern —
and the reflexive case the theory always implied, since a graph that represents
its own Γ and can modify it is exactly what the reflective tower describes.

**The infinity claim gets a citation, not an assertion.** There is an artefact:
`internal/research/docs/infinity_paper.md` — infinity as a structural property
of reflective systems, the tower with no base case, potential versus actual
infinity as extendable versus completed tower, and its own epigraph, *"all that
is required to understand infinity is to understand recursion backwards."*
Point at the document and let the reader judge what is understood. That
converts an unverifiable interior state into something checkable, which is what
this book does with every other claim.

**Three guardrails, all of them already the project's own.**

1. **Testimony, not evidence.** Say it outright: this is n=1, uncontrolled,
   and it is *not* offered as support for anything in the preceding chapters.
   A book that spends ch. 11 refusing to call a mechanism a clinical claim, and
   ch. 16 insisting a mechanism proven synthetically is not a benchmark result,
   cannot then smuggle a self-report in as corroboration. It is reported
   because omitting it would misrepresent what the work cost — which is a
   different reason, and a sufficient one.
2. **The register already exists in this tree.** Ch. 12's line locked it:
   clinical, anti-sensational, grounded in the author's own experience,
   modelling mechanism rather than reaching for significance. Use that voice
   here. It was invented for precisely this problem and it works.
3. **Cost is stated, not performed.** What it took is said plainly and once;
   the epilogue does not dwell, does not seek sympathy, and does not offer the
   toll as a credential. The strongest version is flat: *this is what it cost,
   this is what changed, here is the document, make of it what you will.*

The two admissions then close together, and they are the same shape: **the
substrate has no natural ending, and neither did the person running it.** The
book stops at a chosen cut in both senses — which is the honest ending, and the
only one consistent with everything in front of it.

So the ending is a **cut, chosen and named** — not a conclusion. The honest
epilogue says where the cut was made, on what date, and what was live at that
moment: the effect-audit work in flight, a Stage A implementation built,
measured, and deliberately **left switched off** because its own measurement
said the semantic delta was a regression, and a desire-path probe running in a
sibling town. A book that ends *"here is what was still running the day I
stopped writing, and here is why I did not switch that flag on"* is stronger
than any summary — and it is the only ending consistent with everything the
preceding nineteen chapters argue.

## Reading order vs drafting order

**Reading order** (the book as bound, nineteen chapters):

```
introduction  How I got here — a meeting, a KVM switch, a grammar, a collapse
prologue      Three toys — Life, chess, Doom
front matter  How to read the numbers in this book
Part I        1 THE EYE (+ physics coda)
Part II       2 The frame invariant ── 3 Shape and Rule ── 4 Dynamic quantisation
Part III      5 characters ── 6 speech ── 7 space ── 8 programs ── 9 bodies
Part IV       10 emotion and what it is for ── 11 when grounding fails
              ── 12 coercive control ── 13 the town
Part V        14 The law, and one machine that obeys it
Part VI       15 A number where a shape belonged ── 16 Preregistration as method
Part VII      17 Seldon ── 18 Narrative momentum and narrativium ── 19 The open problem
epilogue      There is no natural ending
```

**Drafting order** (by how complete the evidence already is):

```
1 → 2 + 3 + 4 → 16 + front matter → 12 → 5, 6, 7 → 10, 11, 13 → rest → Part VII → introduction + prologue + epilogue last
```

Two placements worth explaining. **Ch. 12 drafts early** despite sitting late:
its line summary is already a synthesis document, and it is the chapter most
likely to be read on its own by people who never reach Part V — so it should be
written while the method chapter's discipline is fresh, not last when the
budget is thin. **The introduction, prologue and epilogue draft last** despite
being read first and last: the opening has to teach the formalism *and* set the
register, the introduction has to end where the book begins, and the epilogue
has to name the cut — all three are easier once you know exactly what they must
set up. Write the introduction and the epilogue as a pair; they are the same
claim (no destination was ever chosen) seen from each end.

Three things to hold onto while drafting, all already true of the material and
all easy to lose in a rewrite:

- **The recurrences are the argument.** Propose/decide appears in ch. 1
  (motion and stereo held additively), ch. 5 (bins propose, continuous
  decides), ch. 6 (perception by inverting your own production) and ch. 8
  (constructions propose, execution decides). The frame invariant appears in
  1, 5, 7 and 8. The **Argmax-over-Appraisals template** appears in ch. 10
  (marshmallow), ch. 12 (the intent control) and ch. 13 (resident decisions) —
  one rule doing developmental, clinical and civic work. And **Γ-as-legal-moves
  is introduced by chess in the prologue** and then cashed in by ch. 15's
  finding that 159 of 634 rule-carrying seeds mint edges through zero
  productions. Each chapter names its recurrence and points at the others;
  that cross-referencing is the thing a book can do that twenty papers cannot.
- **Part IV must not drift in register.** Ch. 11 and 12 are where overclaiming
  would do real harm, and both source lines already hold the right line in
  their own verdict text (*mechanism and plausibility, not a validated clinical
  claim*; *mechanism, not moral labels*). Carry that register across verbatim
  rather than reinventing it per chapter.
- **One build unblocks the ending.** Composing `Substrate::admissible_moves`
  with `future_manifold.rs` is small, and it is what turns Part VII from two
  theory chapters plus an admission into two theory chapters plus a result. If
  anything in this plan is worth doing before more writing, it is that.
