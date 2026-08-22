# 16 · Preregistration as an Engineering Method

*Draft. Sources: the ~1,700 PREREG/RESULTS pairs under `docs/research/`;
`CLAUDE.md` § RUN 15 CORRECTION and the retracted optional-dep note;
`results/failure_baseline.json`; `docs/research/theory_convergence/`.*

---

At 10:53:25 on a morning in July, a preregistration was committed to git. At
10:53:31 — six seconds later — the run it described started.

Both timestamps are in the repository. Anyone can check them. That is the entire
point of the exercise: the prediction, the sample size, the analysis and the
failure condition were all fixed in a form nobody could edit afterwards, and
then the measurement was taken.

The document also declared which random seeds the run was allowed to use:
sixteen of them, numbered in advance, with the rest of the block explicitly
reserved and left clean.

**This chapter is about why an engineering project adopted the apparatus of
experimental science, what that apparatus caught, and what it cost.** The
preceding fifteen chapters report numbers. This one is about whether to believe
them.

---

## 16.1 The problem the discipline solves

Ordinary engineering has a truth-oracle that science does not: the thing either
works or it does not. Tests pass. The build is green. You do not need
preregistration to know whether a compiler compiles.

That oracle disappears the moment the work becomes *research*. When the question
is "does this mechanism produce the capability", there is no green build. There
is a measurement, and measurements can be arranged — not dishonestly, and
usually not even consciously. You run something, it looks promising, you tune,
it looks better, you write it up. Every step defensible. The result meaningless,
because the analysis was chosen after seeing the data.

Software engineering's usual defences do not help here. A test suite checks that
code does what it did yesterday. It cannot check whether the quantity you
measured means what you think it means, and — chapter 1's sixteen inert
instruments — it cannot even tell you whether your instrument was connected.

So the defence has to come from somewhere else, and the somewhere else is a
century old and belongs to experimental science.

---

## 16.2 What a preregistration fixes

The pairs behind this book are not informal notes. A preregistration in this
corpus fixes, before any measurement:

**The prediction, directionally.** Not "we will see what happens" but "this arm
will exceed that one".

**The sample size.** Declared, along with the specific seeds. A seed block is
treated as a consumable resource: once used confirmatorily it is spent, and the
unspent remainder is recorded as clean. This makes re-rolling until a result
appears visible rather than possible.

**The smallest effect worth caring about.** Stated up front, so that a
statistically detectable but meaningless difference cannot be reported as a
finding.

**The failure condition.** The most important field. What outcome would mean the
hypothesis is wrong — written before it is known which outcome will occur.

**Conjunctive gates, where a single number could be produced by an inert
measure.** Chapter 1's invariance result is the pattern: the log arm must fall
below threshold *and* the linear arm must rise above it. The second clause
exists purely to prove the instrument is alive. Without it the first is
unfalsifiable, because an instrument that reports zero for everything satisfies
it.

**Multiplicity corrections**, where several hypotheses share a run.

None of this is novel to science. All of it is novel *to this*, and the
gap between "obvious in a lab" and "unheard of in a repository" is roughly the
size of the problem.

---

## 16.3 The rules, and what each one cost to learn

Every standing rule in this project was minted by being violated. That is worth
stating plainly, because a list of methodological principles reads as pious
until you know what each one is a scar from.

### Power the gate before the endgame

The most expensive lesson in this work.

A capability arc ran for fifteen runs, improving. Each rung measured a change
and reported a delta: an architecture change worth several points, a scheduling
change worth about one, an appearance change worth two and a half. The
trajectory was real, the machinery was deterministic, and every number
reproduced.

Then somebody powered the gate properly — a larger evaluation set, and intervals
computed rather than assumed. **Every post-composition delta in the arc was
inside the noise.** Arms that had been reported as improvements sat inside each
other's intervals. One change that had been recorded as a *loser* was, at power,
numerically on top. And the headline figure moved by a factor of more than three,
because the small evaluation set had been an easy subset.

What survived was the one effect large enough to be visible anyway — a
compositional change worth twenty-one points, interval-separated — plus the
facts the arc had established about coverage and saturation. What did not
survive was five separately-reported deltas, each of which had been the
justification for a design decision.

The rule: **deltas within about three times the per-episode step are not
results.** They are the granularity of the measurement being mistaken for
signal.

It is a rule about *when*, not just how much. Power the gate before the endgame —
before the arc's conclusions start depending on the deltas — because
retrospective power costs you every decision you made on the way.

### A baseline is a list, never a count

The second rule is the one that reaches furthest outside this project.

A status line in the project's own working notes recorded that the only failures
anywhere in the test suite were some pre-existing optional-dependency errors.
True, when written, under the conditions it was written in.

It was then quoted for about ten days without those conditions. And the
conditions turned out to be load-bearing — in two separate ways, which is worth
keeping separate, because collapsing them is a smaller version of the same
mistake.

**The optional dependency governs collection.** With the package installed, the
suite collects 8,347 tests with **zero** collection errors. With it blocked,
8,208 tests and five errors — all five the same missing import.

**A data directory governs failures**, which are a different population
entirely. With the directory present: on the order of 53 red files and 144 red
test ids. Without it: **147 red files and 565 red test ids**, reproduced exactly
on a second sweep.

Both stand under their conditions. Neither is the number. And a later rung sized
a prediction from the first figure while measuring under the second, missing by
a factor of **3.4** — which is what a dropped condition costs when somebody
downstream believes the quote.

The deeper defect was not the missing condition, though. It was that the claim
*characterised* the failures instead of **enumerating** them. A characterisation
can be held while the thing it characterises grows: every subsequent rung could
honestly report that it had "held the baseline" while the actual set of failing
tests changed underneath. A count can be held the same way.

**A baseline is a list of test ids. Never a count, and never a characterisation.**
A count can be repeated from memory; a list has to be read. The baseline in this
project is now a committed file, gated by a test.

The original status line is retracted in place — with the measurement table that
retracts it — rather than corrected. A historical record is never rewritten; a
standing claim always is.

### An uncommitted runner means the result is not a result

An early result was retracted not because it was wrong but because the script
that produced it was never committed. The number could not be attributed to any
code that existed. Whether it was correct became unanswerable, which is a
stronger reason to discard it than being wrong.

### Ablate: the second step, pointed at code

The habit underneath several of these rules is one procedure with two steps.
First: *what assumptions are being made that aren't being said?* Second — and
this is the step that makes it a method rather than a list of caveats — *what
can be taken away, and what happens if it does?*

Applied to a claim, step 2 is a rewrite. Applied to a system, it is an
**ablation**, and it is why several results in this book are stated as removals
rather than additions:

- Chapter 1 removes the self-avoiding term from the eye's drift, and the
  long-lag crossover dies. So that term was carrying it.
- Chapter 3 *deletes* a tiebreak, and a residual appears where none had ever
  appeared. So the tiebreak had been destroying information rather than
  resolving it.
- Chapter 10 ablates a drive, and a preference falls to zero at zero interval
  width. So nothing else was quietly supplying that behaviour.
- Chapter 12 requires that every rung's mechanism already exist for another
  reason. Which is step 2 as a *precondition*: if the phenomenon needs a
  component built for it, the component was the result.

The connection worth making explicit: this is the same criterion the substrate
itself uses to decide whether an observation deserves a codebook entry — mint if
and only if it compresses. **Minimum description length, applied to a theory,
to a system, and to a sentence, is the same operation.** A claim that can be
removed with no observable loss was description length rather than content, and
a mechanism that can be removed with no measurable loss was never the mechanism.

### Positive-control the reader, not just the arm

The sixteen inert instruments. It is standard to include a control *arm* — a
condition that should show no effect. It is not standard to control the
*reader*: to check that the measurement apparatus reports a signal when one is
definitely present.

Every one of the sixteen would have been caught by that check. None was caught
by a test suite, because in each case the code did exactly what it said.

Chapter 1's centre-surround run shows the discipline working: it includes an
analytic control split that must score exactly zero, and it scores 4.4 × 10⁻¹⁶.
The floor is measured before the result above it is believed.

### Synthetic-proven mechanism is not benchmark value

A mechanism demonstrated on constructed data has been shown to work. It has not
been shown to be worth anything on real data, and the two claims are reported
separately throughout this book. The failure mode this prevents is the one where
a system that provably does something clever is quietly assumed to do something
useful.

### Retract in place; keep the retraction

Corrections are made where the claim was made, with the measurement that forced
them, and the original is left visible. Chapter 1 carries five. Chapter 3
carries an audit that found two of its own reported findings to be wrong and
kept them in the record as its error rate — which is the number a reader should
weight most heavily when deciding what to make of the other thirty-eight.

---

## 16.4 The strongest use of the method: checking a theory against work that was not aiming at it

The rules above are defensive. The method has one offensive use, and it is the
most interesting thing in this chapter.

The theory in Part V makes a cross-domain claim: that a particular structure
governs any system meeting a few conditions, regardless of substrate. The
natural response to a claim like that is rejection as overreach, and *more
mathematics cannot answer it* — the theory's own related-work section already
concedes that most of its individual pieces reduce to known results.

The only evidence that could move it is showing that the same derived structure
turns up independently, in unrelated lines of engineering that were not applying
the theory. Which is checkable, and was checked — and the method for checking it
is the interesting part:

**The theory's own vocabulary was treated as a negative signal.** Searching the
corpus for the theory's terms would have found places where someone had read the
theory and applied it, which proves nothing. So the search was for the
*natural-language* vocabulary each structure would produce if it had been
rediscovered independently, in the idiom of whatever domain rediscovered it.

**Every hit was classified rather than counted** — read in context and sorted
into genuine independent convergence, explicit application, or coincidence.
Which is the baseline-is-a-list rule applied to evidence gathering: a count of
hits would have been meaningless and unfalsifiable.

That classification is what makes the resulting claim usable, and it is also
what bounds it. Not every hit was independent. The document says which were not,
which is precisely why the ones that were can be reported.

---

## 16.5 What the discipline costs

An honest accounting, since this chapter is otherwise an advertisement.

**It is slow.** Every rung carries two documents, and the first has to be
finished before the interesting part starts.

**It kills results you like.** The run-15 correction destroyed five reported
improvements and a headline number, in a project with one author who had no
external reason to run that check at all. That is the cost, and there is no
version of the discipline where it does not eventually land on something you
wanted to keep.

**It cannot catch everything.** Sixteen inert instruments were found in one line
of work, and the discipline did not find them — attention did. Preregistration
constrains what you may conclude from a measurement. It does not verify that the
measurement is connected to anything.

**It produces a corpus nobody can read.** Seventeen hundred documents is not a
literature; it is an archive. Much of this book's work has been finding what is
in it.

Against that: every number in the preceding chapters can be traced, and a
substantial fraction of the ones that would otherwise be in it were removed by
the discipline before they got here. That trade is the reason for the chapter.

---

## 16.6 What would falsify this chapter

- **The rules not generalising.** They were minted from this project's own
  failures. If a similar project adopting them finds they catch nothing it would
  not otherwise have caught, they are local folklore.
- **The convergence audit's classification.** If independent re-examination
  finds that hits classified as independent convergence were in fact
  applications, §16.4's claim fails — and it fails in the direction that matters,
  since the whole argument rests on the classification being conservative.
- **Preregistration not binding in practice.** If prereg documents in this corpus
  are systematically amended after runs begin, the timestamps are theatre. This
  is checkable in git history by anyone, which is the property that makes the
  claim worth making.

---

*Ends. The habit this chapter asks for is the one that caught all sixteen: when
a result is too clean, suspect the instrument before you enjoy the number.*
