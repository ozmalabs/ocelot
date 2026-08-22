# Introduction · How I Got Here

*Draft. First person, past tense, cool. Sources: `~/ozma` git history,
`~/ozmadev/internal/research/`. Figure: IN-1.*

---

I wanted to play games during a boring work meeting.

That is the actual beginning, and I have stopped trying to find a more dignified
one. The specific problem: keyboard and mouse driving the gaming machine while
the work laptop's video call kept running, with audio from both blended so that
nobody on the call could tell. The audio side was solvable — PipeWire will route
and mix whatever you ask it to. The rest was not.

Hardware KVM switches are clunky, handle audio badly, and do not scale past a
couple of machines. The software options were duct tape. So I started building
something better, which is a sentence that has ended worse for many people than
it did for me, and this book is what happened next.

---

## The chain

Every step below is a real artefact with a date, and the dates are in public git
history [IN-1]. I am going to state the chain flatly, because the interesting
thing is not any individual link — it is that every arrow is the same move made
at a larger scale.

**The router.** A software-defined KVMA fabric: keyboard, video, mouse and
*audio*, routed over a network, with a small node attached permanently to each
machine presenting itself as a keyboard, a mouse, an audio device and a network
card. Switching focus changes which node receives input. The USB cable never
moves. First commit, 1 April 2026.

**The problem kept getting bigger.** Routing a keyboard between machines turned
out to be the same *kind* of problem as routing video, which is the same kind as
routing audio, which is the same kind as routing network traffic, which is the
same kind as distributing electrical power through a building. Each is a signal
flowing from a thing to a thing through a connection. Once you see them that
way, you model them the same way — labelled things, labelled connections — and
what you end up with is one map that covers a single USB mouse and an entire
data centre. I wrote seventy-seven thousand words of specification for that map.

**The tooling bill.** I was building this with AI assistance, and it was
expensive — not because the models were weak, but because every time I wanted
two of them to work together I had to write bespoke glue. So I pulled that
thread: context compression, tiered benchmarks, brevity protocols, a set of
fine-tuned coder models.

**A protocol for models.** Then a common language for them to coordinate in — a
lead model delegating to specialists, with a shared knowledge base underneath.
The knowledge base was, once again, a map of labelled things and labelled
relations.

**The collision.** I put the two side by side and they were the same system. The
map that routes keyboard signals and the map that coordinates language models
are one map. Two unrelated problems, one answer, and I did not see it coming.

**Then the key turned out not to be the map.** It is **Γ** — the admissibility
grammar. What matters is not the structure but *what the structure is allowed to
become*: a finite, decidable, inspectable statement of which relations may exist
at all, with the map as the thing it governs. Everything after this point in the
book is a consequence of that inversion.

**Then the model became unnecessary.** If the grammar generates what is
admissible and the substrate realises one of those, the language model was
scaffolding rather than mechanism. That is the ancestor of a rule that governs
every capability chapter here: no borrowed model in the decision path.

**Then physics.** My own note, dated 25 April 2026: *this becomes a physics
paper masquerading as computer science; we need to look there for prior art.*
The tick was already possibility-then-realise. And quantum measurement is the
regime where the distinction between indexed possibility and realised history is
experimentally irreducible — where you cannot replace the alternatives with
ignorance about an already-real classical value.

**And collapse leaves residual** — the part the realised successor did not
absorb. Which is the spine of every chapter that follows.

Four months, meeting-avoidance hack to a theory of collapse. The substrate this
book is about was first imported into its own repository on 10 August 2026.

---

## The method, which is the only transferable part

The chain is *what* happened. This is *how*, and it is two steps:

> **1. What assumptions have been made that aren't being said?**
> **2. What can be taken away — and what happens if it does?**

Step 1 on its own produces a list of caveats. Step 2 is what makes it a
procedure: take the assumption out, and find out whether anything observable was
resting on it. If nothing was, the claim just got shorter for free. If something
was, you have located what the thing actually needs.

That is minimum description length, run on your own beliefs. And it is not an
analogy — it is the same criterion the system in this book uses to decide
whether an observation deserves a new entry in its codebook: *add it if and only
if it compresses.* The question "is this real, or am I seeing structure that
isn't there" has no observer-independent answer. The question "does removing it
cost anything" has a computable one.

So the method and the mechanism are one operation at different grains, and that
is the tightest connection this book contains between how the work was done and
what the work is.

### And the thing that generates the work

The two steps tell you whether a claim is carrying weight. They do not tell you
what to look at next, and for that there is a second habit, which is the one
that actually produced most of this book.

**Force everything through the substrate's own loop.** Then whatever resists is
one of exactly two things: **a limitation of the framework**, in which case fix
the framework; or **implemented the wrong way**, which almost always means it
was inherited — *that is just how it is done.*

The point is the triage rather than the constraint. Neither answer is "leave
it", so a vague sense that something is awkward turns into a question you have
to answer and a fix that follows from the answer.

The second category is the one worth hunting, because it is invisible from the
inside: an inherited convention does not present as a decision, it presents as
the obvious way. RGB pixels are the clearest example in this book. Nobody
argued for a rectangular array of colour values updated frame by frame; it is
how cameras work, and everything downstream exists to recover the structure that
format threw away. Forced through the native loop, none of it survived — what
came out was photons, receptor populations, and a signal that reports change
rather than a picture. That is chapter 1, and I would never have found it by
improving the old eye.

### What it cost me to believe one word

It took about ten passes to mean "everything".

"Everything is a graph" is a sentence almost nobody means. *Everything* is
hyperbole by default, and the tell is that even the sincere uses are quietly
scoped. "Everything in computing" names a boundary. "Everything on the planet"
names a boundary. Each qualifier is an assumption smuggled in as ordinary
English, and each has to be found by running step 1 on the sentence you just
wrote.

Then step 2, ten times: take the qualifier away — does anything observable
break? No. Again. No. The word never got bigger. **The description got shorter.**

And ten passes is not slowness. It is the same growth condition the loop in
chapter 4 uses: mint when the residual *recurs*, not when it first appears. A
system that minted on the first pass would have hallucinated.

### The version of the claim I actually hold

Since the strong reading is available and I do not hold it: this is not the
claim that reality is fundamentally graph-shaped. The theory declines to
specify what underlies relational structure at all, and begins where
distinguishable relational structure is representable. *Where* there is such
structure, it admits graph representation and the dynamics govern it. That is
weaker than it sounds at first and stronger than it sounds at second.

---

## On the quantum step, with its falsifier attached

The step from "my tick is possibility-then-realise" to "so is measurement" is
the one most likely to make a reader close the book, so here is exactly what is
claimed.

It is a **conditional functional bridge**, aligned with the relational readings
of quantum mechanics in which state assignments are agent-relative, measurement
is an action, and an outcome is a new event *for that agent*. The conjecture is
that collapse is not exceptional in kind — that it is the especially visible
instance of an actualisation primitive every tick uses.

And the falsifier is stated in the paper: the bridge fails if the mapping cannot
preserve quantum-instrument composition, Born-rule and contextual probability
constraints, and sequential-measurement statistics, without a second transition
primitive. The papers also say, in as many words, that the generic observation
that a process "can be described as selection and update" is **not sufficient
evidence** for the bridge.

I find it interesting. I do not find it established, and the difference is
written into the document that makes it.

---

## What I am, and what that is worth

I am a systems administrator. That is not modesty and it is not a disclaimer
against criticism — it is where the method came from, and saying so is the
strongest version of the fact.

A sysadmin's core competence is exactly step 1. Debugging production is
assumption-elimination against a system that is lying to you: the monitoring is
green, the config is obviously right, the change was unrelated. The habits that
produces are the ones this book's method chapter formalises — distrust the
reported state, positive-control the instrument before believing the reading, a
green dashboard is not evidence the service is up. The sixteen dead instruments
in chapter 1 were caught by that reflex, not by a test suite.

The lineage matters more than my job title, and it is a restoration rather than
an invention. The people who built graph-native machines in the 1960s, 70s and
80s got there first — machines where every datum carried its type and memory was
a connected structure of labelled objects. That architecture lost to cheap,
fast, untyped chips for economic reasons rather than technical ones, and a good
deal of what has been rebuilt since is a partial reconstruction of what was
given up. I am plumbing an old architecture back in and measuring what the
detour cost.

Four names run through this work more than the citations show. **Asimov**, whose
psychohistory is the distinction between predicting a population and predicting
a person, and whose Three Laws are the first popular statement of an
admissibility grammar. **Pratchett**, from whom I took narrativium and the
lesson that rigorous thinking is *more* effective when it stays warm. **Carroll**,
a logician writing nonsense, which is the exact posture of a book about what a
grammar admits — and after whom the agent in these pages is named. **Sagan**, for
the register: explain the hard thing without diluting it, and let the wonder be
earned by the rigour rather than asserted over it. **Heinlein** belongs with
them, since this project's stated measure of success is his competent man.

They got there first. Much of this is bookkeeping.

---

## What this cost

It took a serious toll on me. I will come back to that at the end, when the
vocabulary exists to say what I mean, and it will be one page rather than a
theme.

---

## How to read what follows

The book is arranged the way the work happened rather than the way a paper is
arranged. An eye comes first, then the theory that eye forced, then the same
loop in eight more places, then the people, and only then the smallest statement
of what all of it was an instance of. The axioms are in Part V, near the end, and
they are there deliberately: after fourteen capabilities have grown out of one
loop, a formalism reads as compression rather than as homework.

Three things before you start. Every number here has a preregistration behind it
and an interval attached. Every retraction is in the body of the chapter where
the claim was made, not in an appendix. And every chapter ends by saying what
would have to be true for it to be wrong.

The next few pages are three toys.
