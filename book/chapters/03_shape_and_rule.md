# 3 · Shape and Rule

*Draft. Sources: `docs/research/engine_substrate/RULES_AS_SHAPE_DESIGN_SPIKE.md`,
`RULE_SIGNATURE_SLICE_RESULTS.md`, `RULE_REFERENCE_LAYER_SIZING_RESULTS.md`,
`META_SHAPE_FIRST_CLASS_RESULTS.md`, `SHAPE_AUDIT.md`. Figure: SR-1.*

---

An agent in this substrate can improve itself. It can propose a change to one
of its own rules, run an experiment, judge the outcome, and adopt or discard the
change — all in graph data, all inspectable. That machinery works.

To use it, the agent must first answer a question: **which of my rules is the
one to change?**

It answered that question by counting how many words of the request appeared in
the rule's *name*.

Not in what the rule matches. Not in what it does. In the name — a string a
human typed when the rule was written. The rule's body, the entire structure of
what it recognises and how it responds, was opaque to the selection.

**This chapter is about the distinction that defect names.** A substrate has two
different capacities, and they are orthogonal: **Rule is how it acts on what it
already holds; Shape is how it decides something is new and adds it.** A system
with only the first can execute forever and never grow. That is a sharper claim
than "the selector was crude", and it is the one this chapter defends.

---

## 3.1 Two axes, not two candidates

The temptation is to read Rule and Shape as rival primitives — two ways of
building the same thing, one of which is better. They are not [SR-1].

**Rule** is match, condition, effect: given this configuration, do that. Rules
compose, fire to fixpoint, and are the entire execution layer. Everything the
substrate *does* is rules.

**Shape** is decode against a held codebook, measure what is left over, and mint
when the leftover recurs. Everything the substrate *learns* is shape.

Cross them and the interesting cell is not the empty one:

- **Neither**: inert. Holds nothing, does nothing.
- **Shape without rule**: a codebook nobody consults. It can recognise and
  cannot act.
- **Rule without shape**: executes correctly, forever, and **cannot extend
  itself**. New cases do not produce new rules. They produce failures, or
  silence, until a human decides by hand that this case deserves a rule and
  writes one.
- **Both**: a residual mints an entry, the next decode covers more, and the
  growth *is* the loop rather than a training phase attached to it.

The third cell is where the opening defect lives, and it is worth stating the
consequence precisely, because it is narrower and more testable than the usual
complaint about tidiness:

> **A substrate whose own execution layer has no shape cannot expand its own
> execution layer.**

Not "should be improved". Cannot. The rules can be edited — by someone outside
the system, reading bodies the system itself cannot compare.

---

## 3.2 The defect had been diagnosed before, in another vocabulary

The rule-selection defect is not novel. It is, verbatim, a failure this project
had already named in its analogical reasoning — and had not recognised in the
self-improvement path, because it does not present as an analogy problem. It
presents as *which file do I edit*.

The analogy literature separates two stages. A cheap, broad **retrieval** stage
finds candidates by surface features — the fast filter that gets you a shortlist
without deep work. Then a **verification** stage checks structural correspondence
and decides which candidate actually maps.

The failure mode is skipping the second stage: treating the surface filter's
output as the verdict. And that is exactly the rule selector — surface features
(name tokens) as the whole judgement, with nothing structural after it.

What makes this more than an embarrassment is what was already sitting in the
substrate at the time. The algebra needed for the second stage existed:
anti-unification retaining the witness rather than discarding it, substitution to
re-apply a witness elsewhere, unification, structural similarity, coverage. All
built. All available.

**The missing piece was never the mathematics. It was an addressable object for
the mathematics to operate on.** A rule body was JSON — a thing you could
execute or edit, but not a thing you could *compare structurally* to another
rule body, because nothing exposed its structure as something the algebra could
take. Two capabilities that had been built within a month of each other, in the
same substrate, and no path joined them.

That is a specific and repeatable kind of gap, and it is worth naming for reuse:
not a missing mechanism, but a missing *handle* on an existing one.

---

## 3.3 The two selectors carry different information, measured

The obvious objection to §3.1 is that the criticism is aesthetic. Names are
descriptive; a well-named rule tells you what it does; perhaps name-keyword
selection is a perfectly good proxy and the structural version is elaboration for
its own sake.

That is an empirical claim, so it was measured — cheaply, before anything was
built.

A structural signature over a rule's condition clause, computed with zero writes
to the graph, was compared against the existing name-keyword selector on a
hand-verified oracle of forty rules. The pre-registered bar was a margin of five.

The two selectors differ, **in exactly the predicted direction on both sides of
the split**: 11/12 against 0/12 one way, 12/12 against 0/12 the other. Margins of
eleven and twelve against a floor of five.

The direction is the result. Structural selection finds rules whose *bodies* do
the relevant thing regardless of what they were called; name selection finds
rules whose *names* say the relevant thing regardless of what their bodies do.
Neither subsumes the other. Both carry real, non-redundant information the other
one misses.

Which retires the aesthetic reading, and also retires the overcorrection —
structural selection is not a replacement for names, it is the missing second
stage.

---

## 3.4 A recogniser that always answers can never grow

The deepest form of the chapter's claim is not about rules at all. It concerns
what a recogniser does when it is uncertain, and it was found in the one place
where it does the most damage.

The agent holds a small codebook of *meta-shapes* — abstract patterns like
"prediction minus observation" or "feedback control" — and files everything it
learns under whichever one it recognises. This is the faculty that decides what
kind of thing a new piece of knowledge *is*, and it feeds analogical transfer
directly.

Its recogniser scored candidates by counting raw substring hits over attribute
keys, and broke ties **alphabetically by the shape's own name**.

Measured across all fifty-five pairs of the eleven meta-shapes: **forty-four are
ties**. The alphabet decided 44 of 44 — eighty per cent of every contest this
faculty runs.

That is bad in the obvious way. It is worse in a way that took longer to see.

**A recogniser that always returns an answer can never produce a residual. And a
grain with no residual can never grow.**

Or more precisely, since chapter 14's standpoint axiom already guarantees the
residual exists: a recogniser that always answers has not eliminated its
residual, because it *cannot*. Every view is from somewhere, so every view is
partial, so something is always left out. What such a recogniser has destroyed
is its own **access** to a residual that is guaranteed to be there. The defect
was never an absent remainder. It was blindness to a certain one. The mint path for meta-shapes had been
absent the whole time, and it had been absent *invisibly*, because nothing ever
failed to be recognised. Every novel observation was confidently filed under
whichever held shape came first in the alphabet. The growth failure presented as
successful recognition.

So the fix that mattered was not adding the mint. It was **deleting the
tiebreak**. Score the item's own signature, rank by tiers of evidence, and when
the evidence does not separate two candidates, *return nothing*. That refusal is
what creates the residual, and the residual is what makes the mint reachable at
all.

The loop then closes as it should: a residual, a recurrence, exactly one mint,
the codebook grows, the epoch advances, the re-decode recognises — including a
near-variant never seen before. The growth ladder used is the full four-rung one
of chapter 4, not a shortcut, because the codebook loader turned out to already
be grain-agnostic. That was confirmed by reading it, not assumed.

The rung caught two of its own bugs via its own negative control, and reported
both rather than fixing them quietly.

---

## 3.5 Acquisition is transfer, not accumulation

If the codebook only ever grew by minting whatever did not fit, it would be an
inventory. What makes it an acquisition *mechanism* is that entries relate to
each other, and the relation can be applied.

Take three real rules from the corpus. They vary along two independent
dimensions, and three of the four corners of that two-by-two exist. The fourth
does not.

One anti-unification over two corners extracts the transform relating them —
retaining the witness rather than discarding it, which is the whole point of that
operation. Substitution applies the same transform to the third corner. The
result is a rule that **exists nowhere in the corpus of 2,851 recognisers**, and
which, installed, fires correctly on the case it was derived for.

That is not a compression result. Nothing was deduplicated. A rule that did not
exist was *derived* from rules that did, by an operation the substrate already
had.

At corpus scale: **318 such parallelograms** with a genuinely missing fourth
corner. Of 200 sampled transfers, **200 are algebraically lossless,
well-defined, and produce a rule absent from the corpus.**

Two honest qualifications, both of which the source document states about itself.
*Well-defined and novel* is not the same as *useful* — deciding which of the 318
is worth completing is the selection problem again, one level up. And the sizing
document originally led with compression numbers and had to correct itself: dedup
was never the reason to build any of this, and the corrected version says so in
place rather than being silently rewritten.

What the demonstration cost is also worth recording, because it is unusual:
**zero new engine primitives, zero graph mirroring, zero engine change.** The
capability was latent in what already existed.

---

## 3.6 What it would cost to make this permanent, and why it is not built

The demonstration ran on structure computed on demand. Making rule structure a
first-class, persistent thing the agent can query means writing it into the graph
— mirroring each rule body as nodes the algebra can walk.

Doing that unconditionally, on every rule installation, is a measured **no-go**:
190 files at risk, up to 51,769 mirror nodes for a single rule, and a checkpoint
reload that adds 2,557 nodes per cycle **with no convergence**. That last number
is the disqualifying one. It is not a large constant; it is unbounded growth, and
it is the same defect this project had already hit and fixed for the grammar
layer — at roughly ten times the rate, with no rule-side fix yet written.

So the answer is lazy mirroring: materialise structure for the rules being
compared, when they are compared. The right existing primitive was identified,
and — a detail worth keeping — the *first* primitive chosen was wrong, and the
correction happened inside the same rung rather than after it. The initial
candidate writes no graph nodes at all, which makes it the wrong precedent for a
mechanism whose entire question is what to write.

None of this is built. It is sized, with the sizing questions answered rather
than re-estimated, and the blocking prerequisite named: the rule-side analogue of
the grammar-layer reload fix has to exist before unconditional mirroring is safe.

---

## 3.7 The honest status of this chapter

The preceding sections are the strongest version of the argument. Here is the
weakest, which belongs in the body.

**What is landed:** the diagnosis; the measured slice showing the two selectors
carry different information; the sizing with its numbers; a codebase-wide audit;
and one full grain — meta-shape — with both its recogniser fixed and its growth
path closed and demonstrated end to end.

**What is not:** thirty-eight of the forty confirmed audit sites are unfixed.
That includes a live, silently-corrupting bug in which a capability axis's
identity is a truncated, order-dependent string join, so a genuinely novel
observation can be misrouted as a duplicate of something else — a growth failure
that presents, once again, as successful recognition. The rule-side mirroring
prerequisite is named and unbuilt. And 159 of 634 rule-carrying seed files mint
edges through zero grammar productions, which chapter 15 takes up properly.

The audit that produced those numbers examined about 150 candidate sites and
confirmed 40. Two of its own reported findings were checked, found **wrong**, and
kept in the record as the method's own error rate — which is the number a reader
should weight most heavily when deciding how much to trust the other thirty-eight.

So this chapter is not "shape is now everywhere in this substrate". It is: the
primitive works, on real data, in the one place that most directly gates
analogical transfer — and everywhere else it does not yet reach is enumerated
rather than characterised.

---

## 3.8 What would falsify this

- **The two-axis claim.** If a substrate with a purely rule-based execution
  layer can be shown to extend that layer without external authorship — new
  rules arising from its own operation — §3.1's central claim is wrong.
- **The independence result.** If a larger or differently-constructed oracle
  shows name-keyword selection subsuming structural selection (or vice versa),
  §3.3 collapses to a preference. The N=40 result is powered against its
  pre-registered floor and no further.
- **The residual claim.** If a grain with a total recogniser — one that always
  answers — can be shown to grow anyway, §3.4's mechanism is not the mechanism.
- **The transfer result.** If sampled parallelogram completions turn out to be
  well-defined but systematically vacuous — deriving rules that are novel only
  in the sense that nobody wanted them — then §3.5 demonstrates an operation
  rather than a capability. This one is *not* currently settled: novelty and
  well-definedness were measured, usefulness was not.

---

*Ends. Next: chapter 4, the loop itself — decode, residual, mint — in the code
that runs it.*
