# Prologue · Three Toys

*Draft. Sources: `domains/conway.py`, `domains/chess.py`,
`docs/research/doom/`. This is the book's formalism, taught by construction.*

---

The first three things this substrate ever ran were Conway's Game of Life, then
chess, then Doom.

That order was not planned as a curriculum. It is simply what I reached for, in
the order I reached for it, and it turned out to teach the whole formalism
without stating any of it. Which is why these pages come before the theory
instead of being a footnote to it: by the end of this prologue you will have met
everything the next nineteen chapters need, and none of it will have been
defined.

---

## Life

Conway's Game of Life is a grid of cells that are alive or dead, updated in
lockstep by three rules about how many neighbours each has. It is the most
familiar toy in computing and it is the right first thing here, because it is a
system that changes and does nothing else. No goals. No world model. No
perception. No cognition. Just structure, and structure changing.

Two things about how it was built are worth more than the simulation.

**State is structural, not numeric.** A cell is not a number that happens to be
1 or 0. A living cell and a dead cell are *different kinds of thing* — different
node types — connected to their neighbours by typed relations. Nothing anywhere
holds a bit that means alive.

That sounds like a stylistic choice and it is the book's central argument in its
smallest form. The information is in what a thing *is* and what it is connected
to, rather than in a value stored at a coordinate. When chapter 15 catalogues
every place a number was put where a shape belonged, this is the shape it means.

**The rules do not decide; they ask.** The transition does not compute the next
state and write it. It asks whether a particular change is *admissible* — may
this cell become that kind of thing, given what it is and what surrounds it? —
and the thing it asks is a separate component whose only job is to answer that.
The change is committed only afterwards.

So the reader has now met, in a toy small enough to hold in one hand: state,
transformation, and a grammar of what is allowed. Chapter 14 will write those as
*g*, *r* and Γ, and will not be adding anything.

---

## Chess

Chess makes the grammar visible by giving it a name everyone already knows.

The admissibility grammar of chess is **the rules of chess**. Which moves are
legal, from this position, for this piece? That is not a metaphor for
admissibility; it *is* admissibility, and everyone reading this has an intuition
for it already.

And chess hands over the distinction the entire book runs on, for free, because
every chess player has it: **the legal moves and the move played are different
things.** A position admits many continuations. One happens. Nobody confuses
"this is a legal move" with "this is the move" — and yet, stated abstractly as
*possibility versus realisation*, the same distinction is easy to lose.

That is collapse, in a form nobody needs taught: the admissible set is large,
exactly one continuation is realised, and the candidates that were legal but
unplayed contribute nothing to what happens next. When chapter 14 draws that as
a figure, the unplayed candidates terminate in a small cross, and the reason
will be obvious because of this page.

One discipline started here too, and it lasted. A conventional chess library was
used — to check that positions were encoded correctly and to verify move
generation. **It was never used to decide anything.** It is an oracle for the
experiment, not a component of the system. That distinction, held from the
beginning, is what later lets a chapter about speech recognition claim that no
borrowed model sits in the decision path, and mean it.

---

## Doom

Doom adds the two things a board game cannot: a world that does not wait for
you, and a body inside it.

Life and chess both pause politely while the system thinks. Doom does not. The
consequences run through the whole book — an eye that has to decode within a
frame budget (chapter 1), a navigation belief that has to be usable before it is
complete (chapter 7), controllers whose sensors report a body state that is
already out of date by the time it arrives (chapter 9).

And Doom supplies the book's first honest null, which is why it belongs in the
prologue rather than in a chapter.

The system was asked to recognise doors and switches. The obvious channel is
geometry: doors are door-shaped. That channel was built, measured, and came back
**at chance** — an area under the curve of 0.508, where 0.5 is a coin flip. It
was retired and replaced with a texture-based channel, which worked.

There is a detail that makes it a real null rather than a shrug. The game
publishes depth and object labels, and those were used *only* to score the
result — never as input. It would have been easy, and unfalsifiable, to let
them leak.

So: page fifteen, and the reader has seen what this book does with something
that did not work. It gets a number, a reason, and a place in the record.

---

## What the toys do not have

There is one more thing worth noticing about these three, and it is
chronological rather than technical.

**There is no preregistration for Life or chess.** No prediction fixed in
advance, no declared sample, no failure condition written before the run. They
predate the discipline that governs every measurement in the rest of this book,
and they live in code and commit history rather than in the seventeen hundred
paired documents behind the later chapters.

That absence is the prologue's real argument. **The method in this book was not
designed. It was paid for.** Every rule in chapter 16 — power the gate before
the endgame, a baseline is a list and never a count, an uncommitted runner means
the result is not a result, positive-control the reader and not just the arm —
was minted by being violated, at a cost, later on.

The toys are what it looked like before that bill arrived.

---

*Three toys: a thing that changes, a thing with rules about what may change, and
a world that does not wait. What follows is an eye.*
