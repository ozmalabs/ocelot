# 18 · Momentum, and What It Costs to Turn

*Draft. Part VII. The formal statements are Papers 03 and 04, merged here
because momentum is the dimension and narrativium is the budget for moving along
it. Figures: PAPER-03-1, PAPER-04-1.*

---

A worn path across a park is the whole of this chapter, and chapter 13 already
measured it.

Nobody planned it. No individual crossing intended it. Nothing about the past
crossings persists — not a record, not a memory, not a trace anyone consults.
What persists is a compacted strip of ground, which is easier to walk on, which
is why the next person walks there.

**That is momentum in the sense this chapter means: not history carried forward
through time, but a currently instantiated structural consequence of prior
change that constrains what happens next.** And it sets up the second half —
because you can walk somewhere else, and it costs something, and the amount it
costs is a quantity.

---

## 18.1 Momentum is present structure

The claim has to be stated in this form or it collapses into metaphor.

Chapter 14 establishes that history matters only where it survives as present
structure. There is no retained past for anything to be carried through; a frame
holds now, and what prior change left in it.

So **momentum is not the past pushing.** It is the shape the past left, standing
in the present, narrowing what the next collapse admits. The worn ground is
exactly and only that.

Which retires an objection this material usually attracts. *Narrative momentum*
sounds like a metaphor borrowed from mechanics — a poetic way of saying stories
have inertia. It is not a borrowing. **Ordinary momentum and narrative momentum
have the same form**: prior deformation leaves present structure that constrains
reachable continuation. They differ in *which relations carry the surviving
structure* — material in one case, represented in the other — and the second
difference is that a represented structure can be revised, which the rest of
this chapter is about.

---

## 18.2 The law

Where a frame carries a Narrative — history represented as a first-class
dimension rather than merely having happened — and the relations supporting that
Narrative remain materially unchanged across the next transition, then
**subsequent reachable geometry retains a directional component aligned with the
continuation that Narrative represents** [PAPER-03-1].

The recursion underneath it is one line:

> **history survives as structure ⇒ history enters the next possibility
> relation.**

And the clause that makes it a claim rather than a mood: **material redirection
requires an interaction that changes the relations carrying the operative
history.** Not an intention to go elsewhere. Not a decision. An interaction that
changes the carrying structure. You do not turn a desire path by wanting a
different route; you turn it by walking somewhere else often enough to wear a
different strip, or by putting a fence across the first one.

The law is deterministic. Where an observer does not represent every determining
dimension, an ensemble statistic across many cases can test directional
persistence — but that statistic measures *the observer's* population-level
evidence. It does not add stochasticity to the mechanism, per chapter 14.

---

## 18.3 What it costs to turn

Now the quantity, and it is the one Part VII exists for.

**Narrativium** is, for a frame, a deformation class and a target: a measure over
the *reachable consequential deformation*. Informally — how much you can
actually change, from here, of this kind of thing.

Four commitments make it a specific claim rather than a word for potential.

**It is not muchness.** Muchness is how much distinguishable future remains;
narrativium is how much consequential deformation is reachable. A frame can have
a great deal of remaining future and almost no ability to deform it, or the
reverse. Chapter 17's separation, one level down: the size of the reachable
region and control over it are different quantities, and the classical control
literature separated them first.

**Measurement is not expenditure.** Reading how much deformation is available is
not the same operation as spending it, and conflating them produces a quantity
that changes when you look at it.

**There is no cross-frame accounting.** Different frames and deformation classes
need not share a unit, an origin, or a scale. There is no universal currency of
narrativium and no meaningful sum across frames.

**And there is no path integration.** This is the sharpest of the four, because
it forbids the obvious implementation. A sequence of expenditures **cannot be
summed** to predict a later measurement. A running total of per-tick costs is not
an approximation of this quantity — it is a *different quantity*, and computing
it does not tell you what the definition says.

---

## 18.4 The horizon

Revision has a cost. Narrativium is what is available. The **narrative horizon**
is where those two meet [PAPER-04-1]:

> the horizon exists only where both the available deformation and the revision
> cost are instantiated **on a common comparison dimension**, and it is the
> equality between them.

Two things about that definition are doing work.

**It is an equality relation, not a stored budget.** Not a tank that depletes.
The horizon is the condition under which a revision is reachable at all.

**And its precondition is a precondition, not a formality.** Where the two
quantities are not instantiated on a common dimension, there is no horizon —
not "an unknown horizon", not "a horizon we cannot compute". The relation is
undefined, and asserting one anyway is the cross-frame accounting the previous
section forbids.

From this: **agility** is not a substrate-level ratio of narrativium to revision
cost, because no universal unit exists to take a ratio in. Where a grounding
supplies a common ordered dimension, agility is the *margin* between what is
available and what a revision requires — an ordinal quantity, in that grounding,
not a number that travels.

---

## 18.5 The one implementation, and what it does wrong

The only place the word *narrativium* appears anywhere in this substrate is a
demonstration script, and what that script computes is a **cumulative sum of a
per-tick term over ticks**.

Which is precisely the path integral §18.3 forbids.

Two things make this worth reporting rather than embarrassing. The script
disclaims itself honestly in its own comments — it says it is plain host
arithmetic rather than an audited quantity — so nothing is claiming compliance
that lacks it. And it is, for exactly that reason, **the single most likely
thing in this tree for a later reader to mistake for an implementation**, which
is why chapter 13 flags it too and why it is named here in the chapter that
defines the quantity.

The correct implementation does not exist. It cannot, yet, for chapter 17's
reason: narrativium is a measure over reachable deformation, and the reachable
deformation set is not expressible in this substrate until two existing halves
are composed.

---

## 18.6 What is measured, and what is not

**Measured, at population scale:** chapter 13's desire paths. Heterogeneous
route valuation plus load-sensitive terrain produces path formation, persistence
under traffic and reversion without it, with the accumulator interpolated so
that part-worn ground is already part-easier — which is what lets traffic
recruit traffic. That is momentum as present structure, with a falsifiable
prediction attached, and it is the only instance in this book where Part VII's
machinery touches a measurement.

**Not measured:** narrativium itself, agility, the horizon, revision cost as a
comparable quantity, and every claim in §18.3 and §18.4. They are definitions
with falsifiers, awaiting the composition of chapter 19.

That asymmetry is the honest state of Part VII, and it is why this chapter opens
with a park rather than an equation.

---

## 18.7 What would falsify this

- **Momentum as present structure.** If a case is found where prior change
  constrains continuation *without* having left present structure — where the
  past acts directly — §18.1 is wrong, and with it chapter 14's history
  principle.
- **The redirection clause.** If Narrative direction can be materially changed
  without changing the relations carrying the operative history, the law's
  sharpest claim fails. This is the most testable thing in the chapter and the
  desire-path setup can test it: fence one path, wear another, measure whether
  anything short of that redirects traffic.
- **No path integration.** If a summed per-tick expenditure reliably predicts a
  later narrativium measurement, then either the definition or the prohibition
  is wrong. Neither has been measured, because the second quantity cannot yet be
  computed.
- **The horizon's precondition.** If a usable horizon can be constructed where
  the two quantities are *not* on a common dimension, then the precondition is
  weaker than stated — which would be an improvement, and would need saying.

---

*Ends. Next: chapter 19, which is one composition long.*
