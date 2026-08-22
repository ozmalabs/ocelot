# 10 · Emotion, and What It Is For

*Draft. Sources: `docs/features/psychology-affect.md`;
`docs/research/psychology_affect/` (≈114 documents), particularly
`EMOTION_FRAMEWORK_LITERATURE.md`, the mood and self-worth families,
`HARLOW_D1_RESULTS.md`, `MARSHMALLOW_DELAY_RESULTS.md`. Figures: EMO-1, EMO-2.*

---

**The posture first, because it governs everything after it.**

Every load-bearing idea in this chapter is canonical affective science, well
supported and not in dispute: emotions as evolved value-regulators; emotion as
the *enabler* of decision rather than its enemy; the distinction between
pleasure and flourishing; self-transcendence; multi-level selection;
learning-progress as a driver of curiosity; a state-and-mechanism-based taxonomy
of psychiatric conditions. Two of the seven have near-exact precedents in prior
AI work.

**This project is re-deriving known affective science on a new substrate, not
discovering it.** That sentence is in the framework's own literature review, and
it is repeated here because the interesting claim is narrower and more
defensible: the contribution is a *mechanistic, graph-native, knob-turnable
instantiation* — one where you can hold a cause fixed and vary another, and read
the result off a value economy rather than fit it.

What that buys is the subject of §10.3 and §10.4, where a simulation does two
things a study of people cannot.

---

## 10.1 Emotions are grown, not enumerated

The obvious way to build an emotion system is a list: a node type per emotion,
each with its triggers and effects. It is also the way that stops being
maintainable at about a dozen entries, and — chapter 3 — it is a system that can
only ever be extended by hand.

The emotions here are **couplings** between components that already exist:
arousal, appraisal, attribution, bond, the window of tolerance. Hate is not a
node type; it is a particular coupling of attribution, stability and threshold.
Contempt, envy, resentment, admiration, gratitude and the self-conscious
emotions are each a different arrangement of the same basis.

The hate family alone is seven documents of coupling work — attribution,
stability under arousal, threshold behaviour, resentment, reset, and the
interaction with the theory-of-mind machinery. Not seven emotions. Seven
measurements of how one coupling behaves.

Which is the admissibility argument of this book at psychological grain: a
taxonomy *generated* from a small basis, rather than a subsystem per feeling.
And it makes the same prediction the grammar argument makes — that the
interesting cases are the ones the basis produces which nobody enumerated.

**Two mechanisms in the basis are worth naming**, because they recur elsewhere
in this book.

*Mood is momentum plus set-point, not a scalar.* The intuitive move — "add mood
to the emotion core" — smuggles a premise: that mood is one thing, either a
running average or a slow set-point. The literature-checked answer is neither
alone. Mood is a slower layer with both momentum and a set-point, sitting over
the fast affect core and modulating it. A one-node addition was replaced by a
small structural correction, which is the recurring shape of this thread's
progress.

And it was measured with the strongest control in this chapter [C7]. Mood is
net-beneficial exactly where environmental returns *persist*: in a
regime-switching world the with-minus-without cumulative reward is **+0.564
[+0.266, +0.855]**, an interval clear of zero. In an i.i.d. world built from the
**same multiset of returns, permuted**, it is **−2.029 [−2.391, −1.660]** —
mood actively hurts.

That second arm is what makes the first one a result. The two worlds have
identical marginal distributions and differ only in whether returns persist, so
nothing about the reward landscape can explain the gap. And it is a *failable*
control that failed in the honest direction: a mechanism claimed to track trend
should be useless or harmful where there is no trend, and it is.

The same run makes the point a second way. The momentum signal rises on a good
run and falls on a bad one, separating by **+1.50**; feed it the **same values
shuffled** and the separation collapses to **+0.032**, with an interval
containing zero. Momentum is tracking the trend, not the values — which is what
distinguishes a momentum layer from a running average, and is exactly what the
structural correction above was claiming.

*Where you locate a cause is a residual.* Attribution — internal or external,
stable or transient — is modelled as what the current model could not absorb.
Which is this book's spine appearing inside a person: the same object that mints
a codebook entry in chapter 4 is, at this grain, the thing that decides whether
what went wrong was you.

And one retirement, kept: an arousal channel was removed rather than defended
when it stopped earning its place. A chapter about a growing system should be
able to point at something that was taken out.

---

## 10.2 What a simulation can do that a study cannot

Two experiments follow. Neither is a claim about people. Both are demonstrations
of a *capability*, and the capability is the thing worth having:

**In a person, causes arrive together.** A child's temperament and their learned
expectations about whether adults keep promises are entangled from before either
can be measured. You cannot randomise a childhood.

**In this substrate, they can be held apart** — one fixed, the other varied,
with the same machinery running underneath and everything else identical.

That is the offer. It is not evidence about children. It is the ability to ask
what a mechanism *implies*, cleanly, and then go and look at whether people do
that.

---

## 10.3 Harlow, on equal drive weights

The classic result: an infant macaque, given a wire mother that feeds and a
cloth mother that does not, prefers contact.

Rebuilt here, the infant is not a bespoke attachment model. It rides the real
drive system — contact, hunger, distress — the real regulator, and the real
appraisal selection. Nothing was built for this experiment.

**The drive weights are equal: one and one.** That is the design decision the
whole result rests on. The preference is not a thumb on the scale.

Measured across 200 infants per condition: time at the contact mother
**79.7% [79.2, 80.3]** [EMO-2].

Contact wins for a structural reason rather than a weighted one. It is needed
*continuously*, where feeding is periodic; and it alone buffers the threat
channel. Given equal weights, those two facts are sufficient.

The control is the part that makes it a result. Ablate the contact drive and the
preference does not shrink — it goes to **0.0%, with zero interval width.** The
behaviour was carried by that drive and nothing else was quietly supplying it.

---

## 10.4 The marshmallow test, dissolved

The delay-of-gratification paradigm is famous for a longitudinal correlation and
notorious for what the correlation might mean. One reading is temperament: some
children can wait. Another is rational: a child who has learned that promises
are not kept is *correct* to take the marshmallow now.

In people these cannot be separated. Temperament and learned reliability are
entangled, and no ethical study can randomise either.

Here they can be, and the headline is not that the agent waits. It is that
**the substrate separates temperament from the reliability prior — the causally
clean dissolution the human experiment cannot run** [EMO-1]. The wait-or-take
choice is one rule: a selection between two appraisals by total value.

**Both main effects are present and interval-separated.** Holding the prior
distribution fixed and varying only temperament: 12.05 against 4.13. Holding
temperament fixed and varying only the prior: 2.92 against 13.23.

**Both null controls behaved as pre-registered.** Hold the varying cause
constant and the intervals overlap — which is the check that says the machinery
is not generating differences on its own.

**And the confound is exhibited in both directions**, which is the part worth
carrying out of this chapter:

- *Identical temperament, three reliability priors* → wait times 3, 8, 13. A
  naive score reads these as three different levels of self-control. The
  temperament is the same in all three. Only the world changed.
- *Temperaments differing fourfold, with compensating priors* → all three wait
  **exactly the same**. A naive score reads them as identical children.

There is a second result underneath: a **patient** temperament held fixed waits
5.1 under an unreliable prior and 23.8 under a reliable one. Impatience as the
correct output of a correctly-functioning appraisal — not a deficit.

The bound is the one the source document states in bold and this chapter repeats:
**this is a capability demonstration, not an empirical claim about real
children.** What has been shown is that the two causes can be separated over one
value economy, and what that separation implies. Whether children's behaviour
decomposes the same way is a question for people who study children.

One structural note that pays off later: the appraisal template used here — a
selection between candidate appraisals by total value — is the same one chapter
12 reuses, unmodified, as its control for whether concealment requires intent.
The mechanism that models a child waiting is the mechanism that models a person
choosing to conceal. That is not an analogy; it is the same rule.

---

## 10.5 What would falsify this

- **The basis claim.** If some emotion in the taxonomy requires a component that
  exists only for it, §10.1's generative argument weakens to a partial one.
- **Harlow's equal weights.** The result rests on the claim that no weighting
  favours contact. A hidden asymmetry elsewhere in the drive machinery would
  falsify it, and the audit is mechanical.
- **The dissolution.** If the two causes turn out to interact in the model in a
  way the factorial design cannot separate, §10.4 demonstrates less than it
  claims. The null controls are the current evidence against that, and they are
  the thing to attack.
- **Mood's persistence dependence.** The claim rests on two worlds with
  identical marginals differing only in persistence. If a third world with
  matched marginals *and* matched persistence shows the same benefit gap, the
  mechanism is responding to something the two arms happen to differ in rather
  than to persistence.
- **The posture.** If any of the seven load-bearing ideas turns out to be
  contested rather than canonical, the chapter's framing — re-deriving, not
  discovering — needs revising in the direction of *more* caution, not less.

---

*Ends. Next: chapter 11, where the same machinery is run in a regime where it
does not work — because a substrate that only ever works is unfalsifiable as a
model of anything.*
