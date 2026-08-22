# 8 · Constructions Propose, Execution Decides

*Draft. Sources: `docs/features/program-synthesis.md`;
`docs/research/program_synthesis/` (≈179 documents). Register per
`BOOK_VOICE.md`.*

---

Everything in this book so far has had a soft verdict. Whether a stroke matched,
whether a scene had depth, whether a word meant something: all decided by a
comparison, a threshold, a metric someone had to choose and defend.

Programs are different. A program either produces the required output on the
held-out rows or it does not. **The verdict is execution, and execution does not
negotiate.**

**This chapter applies the loop of chapter 4 at the grain of program
constructions, and it is where the propose/decide split of chapter 2 is least
arguable** — because one side of it is an interpreter.

*(Naming, because it collides: the phase labels in this thread's documents run
"ARC 0" through "ARC 6", which is this project's own numbering for the
program-synthesis arc. It is unrelated to ARC-AGI, the spatial benchmark of
chapter 7. A filename saying `PROGRAM_SYNTHESIS_ARC6` means phase six.)*

---

## 8.1 The design in one sentence

**Constructions propose; execution decides; and every step between them is a
rule.**

The proposal side is a graph-resident codebook of *construction quanta* — shapes
of code — grown by the unchanged sd loop, plus corpus statistics over how those
shapes follow one another. The decision side is a pure, fuelled interpreter and
a set of held-out rows.

Nothing in the loop between them is host-language control flow. Propose, order,
splice, evaluate, refine, enumerate, accept-or-file-a-gap: each is a seed rule,
matched and fired in the same fixpoint as everything else in this substrate.

---

## 8.2 One hub, five frames

Code arrives in a language. There are five here — Python, Rust, Lua, x86-64 via
an LLVM chain, and LLVM IR itself — and each reads into **one hub statement
representation** and can be written back out from it.

Chapter 2's invariant is the reason that is not merely convenient, and it
applies here in its literal form: *is this value in a frame, or between frames?*
A language is a frame. The hub is a frame. The readers and writers are the maps
between them — so everything language-specific lives in a map, and nothing
language-specific is allowed into either side's own structure. So the codebook of §8.3 is learned once, over the hub, rather than
five times over five syntaxes — and a construction learned from Python is
available when the target is Lua, because what was learned was a shape in the
hub rather than a pattern in a language.

The interpreter that runs the hub form is deliberately austere:

- **Pure.** No ambient state, no hidden channel.
- **Fuelled**, with the fuel budget an integer and — the important part —
  **uncatchable**. A candidate cannot trap its own exhaustion and pretend to
  succeed. Non-termination is a verdict, not a hang.
- **Honest traps.** A failure is reported as the failure it was.
- **Oracles are declared.** Anything reaching outside is named in advance, so
  what a candidate is allowed to depend on is a property of the setup rather
  than a discovery at run time.

Those four properties are what make execution usable as a verdict. A verdict
layer that can be gamed by the proposal layer is not a verdict layer.

---

## 8.3 Learning the shapes of code

The training run is the sd loop, unmodified, pointed at a corpus.

The corpus is real code, read through Python's own parser — tens of thousands of
statement instances. The loop decodes them against a codebook that starts small,
leaves residuals, mints when residuals recur, and re-decodes with the larger
codebook, exactly as chapter 4 describes for pixels and strokes.

What comes out is a **small** codebook of construction quanta plus transition
statistics — which pairs of constructions follow one another. Which is the same
result shape as chapter 5's: a small alphabet of parts, with the information
concentrated in how they are arranged.

The claim worth extracting is that nothing about this was language-specific. The
loop that learned depth from a moving scene learned code from a corpus, at a
different grain, with the representation choice doing the domain-specific work.

---

## 8.4 The loop, as rules

Given a request and some input/output rows:

**Propose.** Rank the codebook by fit and take the best — a selection over
graph-resident scores.

**Order.** Candidate constructions have to be sequenced, and the transition
statistics make that a lattice decode: the most probable ordering under the
learned bigrams. The same Viterbi machinery chapter 6 uses on speech and
chapter 1's ink work uses on strokes, at the grain of statements.

**Splice.** Assemble the ordered constructions into a candidate program.

**Evaluate.** Run it, fuelled, against the rows.

**Refine, on failure.** A failing row becomes a counter-example node in the
graph, and an excluded candidate becomes an exclusion node. The next proposal
sees both. This is counterexample-guided refinement expressed as graph data
rather than as a loop in a host language, which means the state of the search is
inspectable at every step rather than living in a call stack.

**Enumerate**, where proposal has run out of ideas, within a bounded budget.

**Accept, or file a gap.** An accepted program is reflected back into the graph
as structure. A failure that the loop cannot close files a concern — which is
the same human-gated self-improvement seam chapter 3 describes, reached here
from a different direction. The system's response to "I could not write this
program" is a durable, surfaceable record that it could not, rather than a
silent return.

**Recursive descent** sits over all of it: where the codebook covers a request
only partially, the partial cover is treated as a *skeleton*, and the parts it
does not cover become explicit holes — sub-goals, each re-entering the same loop.
Which is the residual of chapter 3 given a name and a work queue.

---

## 8.5 The impotence term

One result from this thread is worth the space because it is a negative
capability, and those are rare.

A synthesis loop with a pool of goals it cannot route has two options. It can
keep trying — which looks like activity and produces nothing — or it can
determine that the *whole pool* is unroutable and say so.

The second was built: a verdict the agent reaches about its own agenda, minted
when nothing in the pool can be advanced. The measurement campaign around it was
pre-registered and came back a **clean no-go** on the design it was testing,
which is reported as such.

The reason this matters beyond its own thread: a system that cannot represent
"there is nothing I can do here" will always represent it as "I am still
working". Chapter 3's argument was that a recogniser which always answers cannot
grow. This is the same defect one level up — a planner that always has a next
action cannot notice that it is stuck.

---

## 8.6 Honest status

The pipeline is built and runs. Two things should be said next to that.

**Part of this thread's own test suite is red on the current engine state.** Five
of six tests in one of the executor's gate files fail as the tree stands — a
pre-existing condition, discovered while a neighbouring rung was measuring
something else, not caused by that rung and not fixed by it. It is recorded
where it was found rather than filed as someone else's problem, and it is the
kind of fact that chapter 16's baseline rule exists to keep visible: the number
of red tests in a tree is a list, not a vibe.

**No benchmark comparison is claimed.** This chapter reports a mechanism —
constructions learned from a corpus, sequenced by learned statistics, decided by
execution — running end to end. It does not report performance against
program-synthesis systems built for the task, and chapter 5's second standing
rule says not to infer any.

---

## 8.7 What would falsify this

- **Language-independence.** The claim that the codebook is over the hub rather
  than over Python is checkable: constructions learned from one frame should be
  usable when the target is another. If transfer across frames turns out to
  require per-language adaptation, §8.2's argument fails and the five frames are
  five codebooks wearing one name.
- **The verdict's integrity.** If a candidate can influence its own evaluation —
  catch its fuel exhaustion, reach an undeclared oracle, or survive a trap — then
  execution is not a verdict and the chapter's central split collapses.
- **The rules claim.** If any decision in the loop is found to be made in the
  host language rather than by a rule, the "no host-language decisions" property
  is weaker than stated. This is mechanically checkable by source audit.
- **The impotence term.** If a pool declared unroutable can be routed by a
  method the agent holds, the verdict is premature rather than honest — which is
  a worse failure than not having it.

---

*Ends. Next: chapter 9, where the same core is asked to control six different
bodies — and where two failures in two of them turn out to be the same missing
capability, seen from opposite sides.*
