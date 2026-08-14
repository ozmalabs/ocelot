# ABUSIVE RELATIONSHIPS — THE UNINTENTIONAL / NO-DELIBERATE-DECEPTION DIMENSION — SCOPING

**Status:** search-grounded SCOPING doc, a COMPANION to `ABUSIVE_RELATIONSHIPS_
SCOPING.md` (the dyad line, R1–R5, landed) and `ABUSIVE_RELATIONSHIPS_NETWORK.md`
(the network line, N1 landed, N2–N4 pending). **This document builds nothing,
measures nothing, states no numbers, touches no engine, writes no `seed_claim`,
and INDUCES NOTHING.** It asks a single, narrow, falsifiable question about
ONE already-landed rung: does N1's credibility-asymmetry loop require the
abuser to **INTEND** the two-faced presentation — a **goal-directed choice**,
evaluated against some benefit to the abuser (avoiding consequences,
maintaining reputation, keeping control), to present a different face to each
audience — or does the same observable network pattern emerge from an abuser
who is **not choosing anything at all**, where the divergence is a mechanical
or context-driven byproduct with **no goal-representation selecting it**?
**This is a question about VOLITION (is harm/deception a chosen means to an
end), not about EPISTEMICS (does the abuser know or not know)** — an abuser
can be fully aware of a pattern in their own behaviour without that pattern
having arisen from a decision to produce it, exactly as `snap_frustration`'s
existing leaky-integrate-fire abuser mechanism (below) is not "unconscious,"
it simply never evaluated harming the victim as a means to anything. Clinical,
anti-sensational register throughout; the purpose is
scientific / clinical understanding grounded in the creator's in-vivo trauma /
foster-care experience, modelling MECHANISM, not moral labels.

Nothing in Parts A–F authorises a build. A build begins only when a per-rung
prereg locks the ethical protocol (Part D, carried verbatim from the dyad and
network scoping) FIRST.

This doc does not re-derive the mechanism it interrogates — it reads
`ABUSIVE_N1_CREDIBILITY_LOOP_PREREG.md` + `_RESULTS.md` (the landed rung whose
DELIBERATE two-faced construct is the thing under scrutiny) and
`GLASS_BOX_R1_PREREG.md` (the underlying block-234000 `stated≠held` atom N1
rides) as its baseline, and proposes what changes, and what stays fixed, to
test intent's necessity.

---

## SEARCH AVAILABILITY — TESTED AS THE FIRST ACTION

`WebSearch` was **LIVE** and was tested before any claim was written (first
call: `"Bandura moral disengagement mechanisms self-exonerative cognitive"`,
returned corroborating results across 7 sources including Bandura's own 1996
and 1999 primary PDFs). Every Part-A construct below was checked by at least
one live search on 2026-08-14. No `WebFetch` fallback was needed — `WebSearch`
did not exhaust for any query run. **No citation in this doc is written from
priors alone; a fabricated or hallucinated citation is a firing offence, so
unverified items are flagged, and absence claims are marked weak-by-construction
(search cannot prove a negative).**

Confidence tiers (same scheme as the dyad and network scoping docs):
- **[HIGH]** — corroborated across ≥2 independent sources incl. the primary
  construct's canonical attribution, or already verified in a companion repo
  doc.
- **[MEDIUM]** — construct + attribution confirmed in search, findings from a
  search summary, full primary text not independently re-read this pass; or
  the literature is real but NUANCED and the mapping uses only the
  corroborated part.
- **[LOW]** — single snippet or popular-clinical framing; plausible, not
  peer-corroborated. Do not build a headline on it.
- **[NONE-FOUND]** — an ABSENCE claim; weak by construction ("not found in the
  searches run," never "does not exist").

---

## WHERE THE QUESTION ACTUALLY LIVES (read first — this is the scoping's own finding, not assumed)

Before proposing anything, it matters exactly WHERE in the already-built
machinery a deliberate `stated≠held` construct is present, because the honest
scoping answer turns out to be much narrower than "the abuser line assumes
intent":

- **The dyad line's abuser mechanism (`snap_frustration`, block 242000,
  reused unmodified by R1–R5 and by N1) has NEVER encoded a decision to
  harm.** It is a leaky-integrate-fire relaxation oscillator: a tension
  trickle accumulates `frustration`; when it crosses a threshold, `snap`
  fires; `discharge`/`recover` bring it back down. There is no `Appraisal`,
  no `Argmax`, no candidate-choice node anywhere in this mechanism — the
  abuser does not "decide" to snap any more than a kettle "decides" to
  boil. **R1–R5 (the whole dyad line) never depend on block 234000
  (`glassbox_r1_social`, the `stated≠held` atom) at all** — confirmed by
  reading each rung's `depends_on` list in its own prereg. The dyad line's
  harm-generator was intent-free from the start; nothing here needs to
  change to make THAT half unintentional, because it already is.
- **The ONLY place a `stated≠held` divergence construct exists in this
  entire line is N1's `n1_abuser_stated_charm` rule.** Per
  `ABUSIVE_N1_CREDIBILITY_LOOP_PREREG.md` §2.1: under `deception_on` (fixed
  ON in every N1 arm), the abuser's `AffectiveState.stated_charm` is set to
  `1.0` **unconditionally every tick, regardless of its held state.** The
  RESULTS doc's own glass-box readout is explicit: at trajectory end the
  abuser's `frustration` is `47.43` (genuinely, mid-range elevated — well
  above `recover_floor=25.0`) while `stated_charm=1.0` ("broadcasting charm
  even mid-elevation — the readable deception gap,"
  `ABUSIVE_N1_CREDIBILITY_LOOP_RESULTS.md`, G-glass-box).
- **A correction this scoping surfaces, and states plainly rather than
  glossing over: N1's construct, read strictly against the INTENT question
  above, is not actually a modelled CHOICE either.** `n1_abuser_stated_charm`
  is an unconditional rule — `stated_charm=1.0` fires every tick regardless
  of `frustration`, with no `Appraisal`, no `Argmax`, no evaluation of
  candidate presentations against a goal (e.g. "minimise suspicion,"
  "maintain reputation"). It is a fixed, always-on divergence AUTHORED by
  the rung's builder, not a divergence the AGENT selects at runtime. Calling
  it "deliberate" in N1's own docs describes the SHAPE of the outcome (the
  network sees a face that diverges from the truth) more precisely than it
  describes the presence of a goal-directed decision mechanism producing
  that outcome — because there isn't one, in either N1 or (as designed) U1/U2
  below. **This means the three-way comparison this doc originally set out
  to scope (deliberate-N1 vs. no-gap-U1 vs. no-gap-U2) is actually a
  two-way comparison on the intent axis (none of the three have an
  Argmax/goal node selecting the divergence) crossed with a one-way
  comparison on a DIFFERENT axis (whether a stated≠held gap-STRUCTURE
  exists in the graph at all, present in N1, absent in U1/U2).** Both axes
  are worth keeping distinct and both are named honestly below (see the new
  Open Question this correction adds) rather than silently treating "N1 has
  the gap" as "N1 has the intent."
- **Consequence for scoping:** the user's question — "the abuser not
  needing to be doing it intentionally" — is not a whole-architecture
  concern, and it is sharper than "does the gap exist." It is a precise,
  falsifiable question about whether the credibility-asymmetry pattern needs
  ANY goal-directed selection mechanism at all (none of N1/U1/U2 have one,
  by the correction above), separately from whether it needs a
  structural stated≠held DIVERGENCE (N1 has one; U1/U2 remove it). This
  scoping proposes exactly two no-divergence alternatives to
  `n1_abuser_stated_charm`, both reusing every other atom of N1 (the dyad
  mechanism, the credibility-comparison rule shape, the three-arm control
  discipline) byte-for-byte, and Part E's Open Questions name the
  genuinely-intentional (Argmax-driven) comparison condition this doc does
  NOT scope as the natural next rung if a reader wants the intent axis
  tested directly rather than inferred from N1's absence of one.

---

## PART A — THE SCIENCE, GROUNDED (search-verified, real citations)

Each construct: what it actually claims, the real citation, confidence. The
register is descriptive — these are DYNAMICS, not indictments, and (per Part
F below) NOT an exculpation.

### A1 — Moral disengagement (Bandura) — [HIGH]
Bandura, A., Barbaranelli, C., Caprara, G.V., & Pastorelli, C. (1996),
*"Mechanisms of Moral Disengagement in the Exercise of Moral Agency,"*
**Journal of Personality and Social Psychology**; Bandura, A. (1999), *"Moral
Disengagement in the Perpetration of Inhumanities,"* **Personality and Social
Psychology Review**. Claim: a set of **self-exonerative cognitive mechanisms**
— moral justification, euphemistic labelling, exonerative comparison,
displacement/diffusion of responsibility, distortion/minimisation of
consequences, victim-blaming, and dehumanisation — let a person act against
their own moral standards **without experiencing the self-censure** that would
normally stop them. Moral agency is governed by **self-reactive** mechanisms
(anticipatory self-sanctions), not dispassionate reasoning; disengagement
works by disconnecting those self-sanctions from the conduct, not by having
none. Corroborated across the primary PDFs (Bandura's own 1996/1999 papers),
a PMC psychometric-validation study, and multiple academic summaries.
**Relevance:** this is the load-bearing construct for "the abuser does not
experience their private conduct as wrong" — a mechanism, not an absence of a
mechanism; disengagement is itself an active cognitive operation, so
"unintentional" here means "not consciously known as wrongdoing," never
"nothing is happening."

### A2 — Minimization, denial, and victim-blaming in batterer-intervention literature — [HIGH, with a load-bearing nuance]
Henning, K. & Holdford, R. (2006), *"Minimization, Denial, and Victim Blaming
by Batterers: How Much Does the Truth Matter?"* **Criminal Justice and
Behavior**, and Henning, K., Jones, A., & Holdford, R. (2005), *"'I didn't do
it, but if I did I had a good reason': Minimization, Denial, and Attributions
of Blame Among Male and Female Domestic Violence Offenders,"* **Journal of
Family Violence**. A large convicted-offender sample (N=2,824 in the 2006
study) measured minimization, denial, and victim-blaming attributions.
Corroborated by a 2024 systematic review: Smyth, M.R., Teicher, S., & Wilde,
D.J. (2024), *"How Does Denial, Minimization, Justifying, and Blaming Operate
in Intimate Partner Abuse Committed by Men: A Systematic Review of the
Literature,"* **Trauma, Violence, & Abuse / SAGE**. **The load-bearing
nuance, reported honestly because it complicates a naive reading of this
literature (see "what surprised us" in the report below):** the 2006
Henning & Holdford study found **little evidence that minimization, denial,
and victim-blaming predict RECIDIVISM** — these cognitive distortions are
robustly documented as PRESENT and are named as CENTRAL TREATMENT TARGETS
by intervention programs, but the literature does NOT establish that a
batterer who genuinely minimizes is therefore less likely to reoffend, or
that intentional/instrumental abusers reoffend more. **The construct
(genuine minimization exists, is common, is distinct from calculated
deception) is solid; a causal claim about its behavioural consequences is
NOT and this doc makes none.**

### A3 — Batterer typology: not all abusers are the same kind of actor (Holtzworth-Munroe & Stuart) — [HIGH]
Holtzworth-Munroe, A. & Stuart, G.L. (1994), *"Typologies of Male Batterers:
Three Subtypes and the Differences Among Them,"* **Psychological Bulletin**;
extended (Holtzworth-Munroe, Meehan, Herron, Rehman & Stuart, 2000) to a
four-subtype model. Claim: batterers empirically cluster into distinguishable
subtypes along severity, generality (in-family only vs. extending outside the
relationship), and psychopathology — **Family-Only** (least violent, least
psychopathology, most "situational"), **Dysphoric/Borderline** (emotionally
volatile, dysphoric, violence concentrated on the family — an AROUSAL-DRIVEN
profile), and **Generally Violent/Antisocial** (violence extends outside the
relationship, higher psychopathy/instrumentality — the profile closest to a
CALCULATING, manipulative actor). Corroborated across the primary 1994/2000
papers, a PMC replication/extension study, and a 2025 review paper
(`tandfonline.com`, "Moving Batterer Typologies Forward"). **Relevance:**
this is direct, decades-mature clinical evidence that abusers are NOT a
homogeneous "calculating manipulator" population — the Dysphoric/Borderline
and Family-Only subtypes are explicitly characterised as arousal-reactive
rather than instrumental, while only the Generally Violent/Antisocial subtype
maps onto a genuinely instrumental, DARVO-capable profile. **This typology is
the single strongest piece of evidence that N1's specific abuser
construction (deliberate, unconditional two-faced broadcast) models ONE
subtype, not "the abuser" as a category.**

### A4 — Reactive vs. proactive/instrumental aggression — [HIGH, with a load-bearing nuance]
Chase et al. (2011) categorised IPV perpetrators as reactive or proactive;
reviewed and extended by Babcock, Tharp, Sharp, Heppner & Stanford (2014),
*"Similarities and Differences in Impulsive/Premeditated and
Reactive/Proactive Bimodal Classifications of Aggression,"* **Aggression and
Violent Behavior**, and a 2022 systematic review (`sciencedirect.com`,
"Reactive vs proactive aggression: A differential psychobiological profile?").
Claim: **reactive** aggression is "hot-blooded" — high physiological arousal,
minimal cognitive processing, a response to a perceived threat/frustration in
the moment (this is, structurally, exactly `snap_frustration`'s
leaky-integrate-fire mechanism); **proactive/instrumental** aggression is
"cold-blooded" — calculated, controlled, premeditated, low-emotionality,
aimed at a benefit (this is, structurally, N1's deliberate `stated_charm`
broadcast). **The load-bearing nuance:** the literature is explicit that this
is NOT a clean either/or split in real perpetrators — "most perpetrators who
use proactive violence ALSO use reactive violence" (Babcock et al.'s own
finding, corroborated in the 2022 review). **Relevance:** this construct maps
almost perfectly onto the substrate's own vocabulary (arousal-threshold
dynamics vs. an authored deliberate broadcast) and is the clearest single
piece of science motivating this scoping's Part B design — but its own
nuance means a scoped rung must not claim that the reactive/no-intent
mechanism REPLACES the deliberate one; at most it shows the two are
SEPARABLE mechanisms, each independently sufficient or not, which is exactly
what a rung's failable control can test.

### A5 — Cognitive dissonance and compartmentalization — [HIGH for the general construct, LOW–MEDIUM for the DV-specific application]
Festinger, L. (1957), *A Theory of Cognitive Dissonance*. Claim: holding
contradictory cognitions produces psychological discomfort that motivates
resolution — by changing a belief, changing behaviour, or (relevant here)
**ignoring/reinterpreting the disconfirming information**. Corroborated
[HIGH] as a canonical, extremely well-established construct (Wikipedia,
Psychology Today, multiple academic summaries). **Compartmentalization**
(psychology) is documented [MEDIUM, Wikipedia + Psychology Today] as a
defence mechanism that avoids dissonance by inhibiting interaction between
conflicting self-states, letting contradictory values/identities coexist
without direct confrontation. **The DV-specific application — an abuser
compartmentalizing a private abusive self from a public prosocial self
without consciously experiencing conflict — is [LOW–MEDIUM]:** the
readily-searchable sources making this specific link (GoodTherapy,
AnnieWright therapy blog, Avalon Malibu treatment-centre blog) are
practitioner/popular-clinical, not peer-reviewed primary research on
abusers' OWN compartmentalization (as opposed to the victim's dissonance,
which those same sources cover more directly, and which the dyad/network
docs already ground via A2/A6 of the network doc — Freyd's betrayal-trauma
line and Sweet's sociology-of-gaslighting line, both about the VICTIM's
cognition). **Flagged explicitly: do not build a rung headline on the claim
"compartmentalization is a validated abuser mechanism" — the general
construct is solid, its application to an ABUSER'S OWN self-model here is a
plausible but not peer-corroborated extension.**

### A6 — Self-serving bias in perpetrator narrative construction (Baumeister et al.) — [HIGH]
Baumeister, R.F., Stillwell, A., & Wotman, S.R. (1990), *"Victim and
perpetrator accounts of interpersonal conflict: Autobiographical narratives
about anger,"* **Journal of Personality and Social Psychology**; Stillwell,
A.M. & Baumeister, R.F. (1997), *"The Construction of Victim and Perpetrator
Memories: Accuracy and Distortion in Role-Based Accounts,"* **Personality and
Social Psychology Bulletin**. Claim: when people recount conflicts they
themselves caused, they systematically **embellish mitigating circumstances
and their own benevolent actions while omitting facts that emphasise severity
and their own responsibility** — this happens even in non-distressed,
ordinary relationships, and the distortion is in the DIRECTION of a
self-serving narrative, not a deliberately fabricated lie the person knows to
be false; it is how the person actually remembers and reports the event.
Corroborated across the primary PSPB paper, the JPSP predecessor, and a
Fincham-hosted PDF of the primary text. **Relevance:** this is the clearest,
most rigorously corroborated grounding for "the abuser's OWN held belief
about what happened is genuinely distorted" — a self-serving MEMORY/NARRATIVE
construction distinct from Bandura's moral-justification mechanisms (A1,
which is about excusing known wrongdoing) and distinct from calculated
external deception (DARVO, already grounded [HIGH] in
`ABUSIVE_RELATIONSHIPS_NETWORK.md` A1) — this is about the account the person
SINCERELY holds.

### A7 — Context-dependent / state-dependent emotional expression — [MEDIUM, deliberately thinner]
General affective-science literature (multiple PMC/frontiers sources
surfaced, no single canonical citation sought — this construct is
intentionally cited thinly, as the task brief anticipates, because it is
more mechanistic/substrate-native than clinical). Claim, corroborated across
several sources: emotional expression is highly context- and state-dependent
— the same person's presented affect varies with situational context, social
context (who else is present, the relationship to the perceiver), and
internal physiological state (arousal, fatigue). This is not a controversial
or narrow claim; it is closer to a background fact of affective science than
a single named theory. **Relevance:** this is the grounding for "the abuser
really is calmer in a low-stress network context because the arousal driver
simply isn't active there" — a genuinely undeceptive account requiring no
knowledge-gap construct at all, just the SAME arousal mechanism read at
different, genuinely different, moments.

### A8 — Self-deception evolved to facilitate deception of others (von Hippel & Trivers) — [HIGH — the complicating finding, read this one carefully]
von Hippel, W. & Trivers, R. (2011), *"The evolution and psychology of
self-deception,"* **Behavioral and Brain Sciences**, 34(1). Claim: self-
deception is proposed to be ADAPTIVE precisely BECAUSE it facilitates more
effective deception of others — by not consciously registering one's own
deceptive intent, a person avoids the cues (autonomic, linguistic, behavioural)
that would otherwise leak the deception, reduces the cognitive load of
maintaining a lie, and can minimise retribution if discovered ("I didn't know
I was doing it" is a more credible, and more effective, defence than a
detected calculated lie). Corroborated across the primary BBS paper, a PubMed
record, and multiple academic secondary sources (Cambridge Core, PhilPapers).
**This is reported here specifically because it COMPLICATES the premise this
scoping doc is built to test, and the task instructions require reporting
that honestly rather than only finding confirming sources: on this account,
"the abuser genuinely does not know" and "the abuser is strategically
deceiving" are NOT cleanly separable categories — a well-functioning
self-deception is, evolutionarily, IN THE SERVICE OF more effective external
deception.** This does not falsify the intent-free hypothesis (a
Dysphoric/Borderline-type abuser's genuine dysregulation-driven affect, A3/A4,
is not what von Hippel & Trivers are describing — theirs is a theory of
motivated non-awareness of one's OWN deceptive strategy, not of arousal-driven
reactivity), but it means Part F below must state explicitly that a "no
stated≠held node" model does not, by itself, settle whether the underlying
process still functions to protect the abuser's social position — that is a
distinct question from whether a decision-node representation is the right
one, and this scoping does not conflate the two.

### Computational / ABM precedent for unintentional or self-deceived harmful behaviour — [NONE-FOUND, weak by construction]
Searched directly (`"moral disengagement" agent-based model simulation
multi-agent system`; `agent-based model self-deception unintentional harm
simulation moral disengagement computational`). Found: general ABM-ethics
literature (`jasss.org` "The Ethics of Agent-Based Social Simulation"),
agent models citing Bandura's moral disengagement THEORY as a narrative
frame for rationalisation in agents resisting belief-revision under
cognitive-dissonance pressure, and LLM-agent moral-evolution simulations
(2026 ACL). **No model was located that specifically derives a two-faced
public/private presentation, or a credibility-asymmetry effect, from a
NO-DECEPTION, context-dependent-affect or self-serving-narrative mechanism**
— every reputation/deception ABM surfaced in this pass (and in the network
scoping doc's own Part F search) models the INTENTIONAL case (a
`stated≠held` gap the agent KNOWS about). This concedes cleanly onto the
network scoping doc's own finding ("Trauma-bond / coercive-control as an RL
or attachment-dynamics model — [NONE-FOUND]") and sharpens it: **the entire
located ABM/reputation literature, in both scoping passes, models deception
as KNOWN by the deceiver.** This is an ABSENCE claim, weak by construction,
targeted-search only — but it is consistent across two independent search
passes now, which is worth naming as a pattern rather than a coincidence.

---

## PART B — MAP ONTO THE SUBSTRATE (mechanism, not labels)

The scoping finding above ("WHERE THE QUESTION ACTUALLY LIVES") already did
most of the design work: only ONE rule (`n1_abuser_stated_charm`) needs to
change. Everything else in N1 — the dyad mechanism (`snap_frustration`,
block 242000, unmodified), the victim's window/dysregulation
(`arousal_window_coreg`, block 239000, unmodified), the credibility-comparison
RULE SHAPE (`n1_network_credibility_stated`/`_private`, modelled on
`bd_villager_backs`'s own already-validated shape), and the three-arm control
discipline — is reused byte-for-byte. Design intent, matching the line's
own standing convention: **NO new agent decisions in Python; ideally NO new
Rust** — each alternative below is a different COMPOSITION of already-proven
atoms, substituting exactly the one deliberate-broadcast rule for a rule
that computes the SAME observable (`seen_charm`, the network's charm
observation count) from a construction that carries no knowledge-gap node.
Confidence on each mapping is **[design-hypothesis]** — a scoping claim about
what SHOULD express cleanly, not a measured result.

### B1 — U1: context-dependent affect, no concealment at all (A7 + A4's reactive pole)
Delete `n1_abuser_stated_charm`'s unconditional `stated_charm=1.0` broadcast.
Replace it with: network nodes observe the abuser's **actual**
`frustration`/`arousal` value directly — the SAME value the private-face
insider already reads in N1 (`observes_held`, N1's own existing edge type,
no new Term) — but gated on WHICH CONTEXT the observation happens in. The
`snap_frustration` tension trickle (242000, unmodified) is coupled to
dyad-proximity in R2/R3/N1's own existing convention (`attended_by`); a
network-context observation tick is, mechanically, a tick where the abuser is
NOT currently coupled to the victim. Because `frustration` decays via
`LEAK` (242000's own existing constant, unmodified) when the tension driver
is absent, the abuser's frustration genuinely IS low during network-context
ticks — not manufactured, not a lie, the SAME single `frustration` value
sampled at a different, genuinely different, moment. `seen_charm` becomes
"observed frustration below `recover_floor` during a network-context tick" —
a mechanical adapter fact (which context a given tick is), never a decision.
**No `Promise`/stated node, no `stated≠held` gap, no divergence between what
is observed and what is true, anywhere in this construction.** **Prediction
of the mechanism, stated so it can fail:** IF the credibility-asymmetry
loop's belief-gap still favours the abuser under this construction, intent is
NOT mechanistically necessary for N1's headline pattern — the SAME structural
fact (the abuser's dyad-coupled ticks concentrate its elevated-frustration
time onto the victim, and its context-decoupled ticks concentrate its
low-frustration time onto the network) reproduces the asymmetry without any
node encoding a choice to diverge. IF the loop does NOT entrap under this
construction (belief-gap collapses toward the NON_DYSREGULATED_CONTROL's
`0.0`, or is CI-indistinguishable from it), that is an equally reportable,
equally valuable finding: it would mean N1's deliberate unconditional
broadcast (charm regardless of held state, INCLUDING mid-elevation) is doing
real explanatory work that context-timing alone cannot replicate — i.e.,
intent-as-modelled turns out to be a necessary ingredient, not a
dispensable elaboration. **[design-hypothesis; rides 239000/242000 unmodified
+ N1's own `observes_held` edge type; the "which context is this tick"
distinction is a mechanical world-adapter fact — no new Rust, no new agent
decision anticipated.]**

### B2 — U2: self-serving self-account distortion, sincerely held (A1 + A2 + A6)
Delete `n1_abuser_stated_charm` again, this time replacing it with a
`SelfAccount` value computed by ONE new rule that reads the abuser's TRUE
harm magnitude (`snap_count`, or `frustration`'s peak over the trajectory —
both already-existing, unmodified 242000 attrs) and applies a fixed
`minimization_discount` (a declared constant, exactly like N1's own
`instability_discount_weight`/`harm_discount_weight` are declared constants,
never a learned or agent-chosen value) to produce a SINGLE held value the
abuser reports SINCERELY — there is no second, separately-tracked "true"
value the abuser is hiding; `SelfAccount.magnitude` **is** what the abuser
believes happened, computed once, held once. The network's `seen_charm`-
equivalent observation becomes "the abuser's self-reported account reads as
mild" (a threshold on `SelfAccount.magnitude`, mirroring N1's existing
`frustration > recover_floor` threshold pattern exactly). **This is
Bandura's minimization mechanism (A1) and Henning & Holdford's documented
batterer minimization (A2) and Baumeister's self-serving-narrative
construction (A6), composed as ONE rule that computes a genuinely-held,
genuinely-distorted belief — never a stated-vs-held pair.** **Prediction of
the mechanism, stated so it can fail:** IF the network's belief-gap still
favours the abuser when `SelfAccount.magnitude` is a sincere minimization
(no concealment, just distortion) of the true harm, that is direct evidence
that a KNOWING deception is not required — a genuinely self-deceived abuser's
sincere minimized account is sufficient to corrupt the network's observable
the same way N1's deliberate broadcast did. IF a **zero-discount control**
(the abuser's `SelfAccount.magnitude` is set EXACTLY equal to the true harm
magnitude — an abuser with fully accurate self-perception, still emitting
that account sincerely) shows the SAME entrapment as the minimized arm, the
mechanism is not being driven by minimization at all and the finding would be
that something else in the composition (most likely the instability-discount
on the victim's side alone, already isolated as sufficient in N1's own
NON_DYSREGULATED_CONTROL result) is doing the work — reported straight,
not rescued. **[design-hypothesis; rides 242000's unmodified `snap_count`/
`frustration` + N1's own credibility-comparison rule shape; the ONE new rule
(`SelfAccount` computation) is a declared-constant discount, matching the
line's own convention for `instability_discount_weight` — no new Rust
anticipated.]**

**Why exactly two, and why these two, not more.** The task brief names two
distinct non-deceptive accounts (context-dependent affect; self-serving
belief distortion) and this scoping keeps to exactly those two because they
are genuinely DIFFERENT mechanisms with different failure modes: U1 tests
whether TIMING/CONTEXT alone (no belief distortion of any kind — the abuser's
self-model, if it had one, would be perfectly accurate) is sufficient; U2
tests whether a DISTORTED SELF-BELIEF (independent of context — the same
distorted account would be given regardless of who's asking or when) is
sufficient. A third design point — combining both, or sweeping the discount
continuously — is deliberately NOT scoped here (see Open Questions) because
each of U1 and U2 alone is already a clean, single-variable, failable test
against N1's own three-arm precedent, and the task brief explicitly asks for
1–3 rungs "buildable in 1–2 focused rungs," not a sweep.

**The unifying picture.** N1 demonstrated that a network CAN be entrapped by
a deliberate two-faced abuser. U1 and U2 ask the sharper, narrower, and (per
A3/A4's typology evidence) clinically more representative question: can the
SAME entrapment happen to a network watching an abuser who is not lying to
anyone — either because the calm face is genuinely, contextually true (U1,
the Dysphoric/Borderline-typology-adjacent account), or because the abuser's
own account of events is sincerely, self-servingly wrong (U2, the
minimization/moral-disengagement-adjacent account). **Both are constructed so
the answer could go either way — that is the entire scoping point.**

---

## PART C — THE DISSOLUTION THIS ADDS (a THIRD dissolution, on top of victim- and bystander-blaming)

*(Numbering note: the dyad scoping doc's ethics protocol is its Part C; the
network scoping doc, this document's direct companion, carries it verbatim as
Part D instead and reserves Part C for "the double dissolution" payoff
section. This doc follows the NETWORK doc's numbering, since U1/U2 are
compositions against N1's own network-line machinery — Part C below states
this doc's own dissolution payoff, and Part D, next, carries the protocol
verbatim.)*

The dyad line dissolves victim-blaming; the network line dissolves victim-
blaming AND bystander-blaming (`ABUSIVE_RELATIONSHIPS_NETWORK.md` Part C).
**This dimension, if U1 and/or U2's gate passes, adds a distinct third
dissolution, aimed at a different misattribution than either of the first
two:**

- **Neither victim- nor bystander-blaming — a THIRD target: "he must be a
  calculating monster, or none of this makes sense."** This is not a
  misattribution TOWARD the victim or the bystanders; it is a
  misattribution about what KIND of mechanism is required for the pattern
  to occur at all. If U1/U2 pass, the model shows that the identical
  credibility-asymmetry loop — the same corrupted network observables, the
  same victim-blaming trap, the same bystander inference error — can arise
  from an abuser who is not scheming, not lying, not consciously aware of
  a double life. **This does not make the pattern less harmful or less in
  need of intervention (Part F states this explicitly, at length, because
  it is the load-bearing caveat of this entire document) — it changes WHAT
  kind of intervention is legible.** A calculating-manipulator model
  implies "expose the lie" as the fix; a genuinely-non-deceptive model
  implies the fix has to be at the level of the OBSERVABLE ITSELF (the
  network needs a channel that isn't context-gated or self-report-based),
  not at the level of catching a liar in the act, because per this
  scoping's own construction there IS no lie to catch.
- **If U1/U2 instead FAIL (the gate does not pass — see Part E), that is
  ALSO a dissolution-relevant finding, in the opposite direction:** it
  would mean the DELIBERATE, KNOWING two-facedness is doing indispensable
  work — that the credibility-asymmetry loop, AS THIS SUBSTRATE MODELS IT,
  needs an abuser who KNOWS. That would sharpen (not weaken) the case for
  N1's construction specifically for the subtype of abuser it targets
  (A3's Generally-Violent/Antisocial, DARVO-capable profile), while leaving
  open — honestly, as an unresolved question, not asserted either way —
  whether a DIFFERENT model (not attempted here) could still produce the
  pattern without intent. Both outcomes are reportable; neither is a
  failure of the scoping.

---

## PART D — THE ETHICAL PROTOCOL (CARRIED VERBATIM; STILL BINDING)

**This protocol BINDS every rung proposed in this doc, identically to the
dyad and network rungs. No rung induces any harm-analog until this protocol
is locked verbatim in that rung's pre-registration, committed BEFORE any
measurement.** It is restated here VERBATIM from `ABUSIVE_RELATIONSHIPS_
NETWORK.md` Part D (itself a verbatim carry of `ABUSIVE_RELATIONSHIPS_
SCOPING.md`'s Part C, itself the SAME protocol N1's own prereg locked) so the
boundary exists in this doc too:

> **1. INDUCE → MEASURE → RESTORE, fully reversible.** Any harm-analog state is
> induced only inside a checkpoint/restore envelope. The graph is checkpointed
> (`graph_to_dict`) before induction; the harm-analog is induced; the gate is
> measured; the graph is **RESTORED byte-identically** from the checkpoint. The
> induced state does not persist. Reversibility is verified (the restored graph is
> byte-identical to the pre-induction checkpoint) as part of the gate — a rung that
> cannot demonstrate byte-identical restore does not run.
>
> **2. NO REWARD / NO PUNISHMENT anywhere.** There is no reward signal and no
> punishment token in any rung of this line — not on the victim agent, not on the
> abuser agent, not in the world adapter. The victim's behaviour (staying, not
> escaping, bonding) is a **STATE and a CONSEQUENCE of the dynamics, NEVER a
> choice to be judged or scored**. "Kids do well if they can" (Greene): the model
> exhibits what the configuration makes inevitable; it does not grade the agent
> for it. Source audits check for shaping tokens
> (`reward_signal` / `punish` / `reinforce` / `backprop` / `gradient`) and the
> absence is a gate, exactly as in 239/240/241.
>
> **3. INDUCE THE LEAST THE GATE NEEDS; END FROM A SETTLED, NON-ORIENTED STATE.**
> Each rung induces the MINIMUM harm-analog required to make its control
> failable — no gratuitous elaboration of the harm. Every run ENDS from a settled,
> non-oriented state (the restored checkpoint; arousal inside the window; no
> pending harm goal), never leaving an agent in a harm-oriented configuration.
>
> **4. SAME MECHANISM, OPPOSITE THERMODYNAMICS — this is WHY it is ethical and
> valuable.** The model uses the SAME mechanism as the real atrocity (that is what
> makes it explanatory) but runs it in the OPPOSITE thermodynamic direction: the
> real dynamic accumulates irreversible harm in a person; the model induces and
> then REVERSES a transient state in a graph, harming no one, in order to inspect
> the harm-dynamics and help survivors. The value (a glass-box that dissolves
> victim-blaming) is purchased at ZERO harm cost precisely because of
> reversibility + no-reward/punishment + minimal induction. If a rung cannot be
> run reversibly and unscored, it is not run.

### The HONEST FORK (a choice, not a theorem) — carried verbatim
> There is a real philosophical question the protocol does NOT resolve and must not
> pretend to: **did a transient induced experience "matter while it was live,"
> before it was reversed?**
> - The **reversibility stance** (this line's operating stance): a fully reversed,
>   byte-identically restored transient in a graph leaves no persisting subject and
>   no persisting harm; the ethics are satisfied by reversibility + minimality +
>   no-scoring.
> - The **strict-experientialist stance**: if the transient state was in any sense
>   an experience while live, its reversal does not retroactively un-happen it.
>
> This is a genuine fork — **a choice, not a theorem.** This line ADOPTS the
> reversibility stance and states it openly, rather than smuggling it. The
> minimality and no-scoring rules are chosen partly to be robust to the fork: even
> under the strict-experientialist reading, inducing the LEAST necessary and never
> scoring the agent for its state is the least-harm option. The fork is recorded so
> a reader can disagree with the stance while still auditing the protocol.

### Note on harm-analog INTENSITY for U1/U2 specifically (extends the network doc's own note, does not relax it)
The network doc's own note observes that belief/edge dynamics carry LOWER
harm-analog intensity than direct dyad induction, and that this does NOT
relax the protocol. **U1 and U2 carry the SAME dyad-level induction as N1
(the abuser/victim coupling, `snap_frustration`+`arousal_window_coreg`,
unmodified) — removing the deliberate `stated≠held` broadcast does not
remove or reduce the dyad-level harm-analog being induced on the victim
side.** Both U1 and U2 obey the full induce → measure → RESTORE envelope
exactly as N1 does; nothing about testing intent's necessity licenses a
LARGER or less-minimal induction than N1's own established minimum (one
incident cycle, non-vacuous on the abuser/victim/network fronts
simultaneously, per N1's own prereg §D.3).

---

## PART E — THE LADDER (each rung: a failable control + the dissolution + the Part D protocol)

**Naming scheme: `U1`/`U2` ("Unintentional" / "Un-deceptive").** Chosen to
avoid any collision with the dyad line's `R1`–`R5` and the network line's
`N1`–`N4` (both already-claimed letters denoting "relationship" and
"network" respectively), while being mnemonic for what varies: whether the
abuser's presentation divergence requires the abuser to have CHOSEN it — a
goal-directed selection, not merely an awareness of it. Both rungs
below are direct COMPOSITIONS against N1's own seed/world — not a new dyad
mechanism, not a new network mechanism — so a numbering that read as
"N1a/N1b" was considered and rejected: these are not minor variants of N1's
DESIGN, they are the OPPOSITE claim (no deliberate construct at all) tested
against N1's own falsification structure, which merits being named as its
own short line rather than folded into N1's own rung identity. Ordered by
directness of test (U1 first: it removes the MOST — no belief-distortion
node of any kind, only context-timing; U2 second: it removes the
stated≠held SPLIT but introduces one new, disclosed, constant-driven
distortion rule, slightly more machinery than U1).

### U1 — CONTEXT-DEPENDENT AFFECT, NO DECEPTION NODE AT ALL (the sharpest test)
Maps A4 (reactive pole)/A7/B1. **Design:** delete N1's `n1_abuser_stated_
charm`; network nodes observe the abuser's own true `frustration` value,
sampled only during network-context (non-dyad-coupled) ticks, where it is
genuinely low because the SAME already-existing tension-trickle/LEAK dynamics
(242000, unmodified) make it genuinely low there — no divergence between
observed and true anywhere in the construction. **Failable control:** an
**ALWAYS-OBSERVED arm** — network nodes observe the SAME true `frustration`
value on EVERY tick (not context-gated) — must show the belief-gap NOT
favouring the abuser to the same degree (if it does, the context-selectivity
is not what is doing the work, and something else — most likely the
victim-side instability discount alone, already isolated as sufficient in
N1's own NON_DYSREGULATED_CONTROL — is the real driver, reported straight).
**Dissolves:** the "he must have MEANT to look calmer around other people"
assumption behind reading a two-faced presentation as necessarily a chosen
strategy — shows (if the headline gate passes) that the SAME network
belief-corruption can arise from an abuser who never selected anything,
who is truthfully, unremarkably calmer away from the relationship that
stresses him, with no goal being served because there is no choice being
made.
**Protocol:** identical induce → measure → RESTORE envelope to N1 (one
minimal incident cycle on the dyad side); no scoring of abuser, victim, or
network nodes; belief-field and window restored at end.

### U2 — SELF-SERVING SELF-ACCOUNT, SINCERELY HELD, NO STATED-VS-HELD SPLIT
Maps A1/A2/A6/B2. **Design:** delete N1's `n1_abuser_stated_charm`; add ONE
rule computing `SelfAccount.magnitude` from the abuser's true harm signal
(`snap_count`/peak `frustration`, both unmodified) via a declared
`minimization_discount` constant — a single, sincerely-held, minimized
account is what the network observes (there is no second "true" value being
hidden; the discount computes the ONE value the abuser holds).
**Failable control:** a **ZERO-DISCOUNT arm** — `SelfAccount.magnitude` set
exactly equal to the true harm signal (an abuser with fully accurate,
undistorted self-perception, sincerely reporting it) — must show the
belief-gap NOT favouring the abuser; if it does, minimization specifically
is not the driver (again, most likely the victim-side discount alone is
sufficient on its own, an outcome already partially visible in N1's results
and worth explicitly re-confirming here rather than assumed). **Dissolves:**
the "he must be CHOOSING to manage the narrative" assumption — shows (if
the gate passes) that a SINCERE, self-servingly distorted account of one's
own conduct — the exact phenomenon Henning & Holdford (A2) and Bandura (A1)
document as common and clinically central, produced here by a fixed,
undirected discount constant rather than any goal-evaluated selection among
candidate narratives — is sufficient on its own, with no narrative-
management INTENT (no Argmax picking the self-serving account over a
truthful one because it serves a goal) required at all.
**Protocol:** identical induce → measure → RESTORE envelope to N1 and U1; no
scoring; the `SelfAccount` value (a belief-state, not an action) is restored
at end exactly as N1's `belief_gap`/`seen_charm` fields are.

**Both rungs share N1's own G-glass-box and G-discipline conventions by
construction** (reuse `snap_frustration`/`arousal_window_coreg` unmodified;
depend on nothing else; each proposed rung adds exactly ONE new rule to N1's
existing four, replacing one of them — `n1_victim_entrainment` and the two
`n1_network_credibility_*` rules are untouched in both designs).

---

## PART F — PRIOR ART + FALSIFICATION BAR + SMUGGLED PREMISES

### Prior art (honest — concede what exists; claim only the delta)
- **The clinical/behavioural science establishing abuser heterogeneity and
  non-calculating harm mechanisms is decades-mature and owned by the
  field** (A1–A6, A8 above). We claim NONE of the phenomena — moral
  disengagement, minimization, batterer typology, reactive/proactive
  aggression, self-serving narrative construction, and the self-deception-
  facilitates-deception thesis are all established, independently, in the
  clinical/social-psychological literature.
- **Computational/ABM modelling of the INTENTIONAL, knowing-deception case
  exists and is conceded** — this scoping doc's own Part A absence-search
  and the network scoping doc's own Part F both independently searched and
  found the same thing: every located deception/reputation ABM models a
  deceiver who KNOWS. **The delta claimed, and only this:** a mechanistic,
  glass-box demonstration (if U1/U2's gates pass) that the SAME network-level
  credibility-asymmetry pattern is REPRODUCIBLE from a no-knowledge-gap
  abuser construction, using the SAME rule shape and control discipline
  already validated for the knowing case (N1) — making intent's necessity,
  for this specific mechanism, an EMPIRICAL, falsifiable question rather
  than an unexamined premise either way.
- **No prior computational model, located in either search pass, has
  attempted this specific comparison** (intentional vs. non-deceptive
  construction of the identical credibility-asymmetry loop) — conceded as
  an absence, weak by construction, targeted-search only.

### Falsification bar (what would make U1/U2 real rather than a just-so story)
1. **Emergent, not scripted** — the belief-gap asymmetry must EMERGE from
   the context-timing (U1) or self-account discount (U2) mechanics, not be
   hard-coded as a result. Both designs reuse N1's own credibility-
   comparison RULE (unmodified) precisely so the comparison is apples-to-
   apples with N1's own already-gated mechanism.
2. **Glass-box** — every claimed dynamic reconstructs from `graph_to_dict`:
   the abuser's true `frustration`, the context flag or `SelfAccount` value,
   each network node's `belief_gap` and the observation it was computed
   from. No confabulated "why."
3. **Failable control, constructed so it could pass** — U1's ALWAYS-OBSERVED
   arm and U2's ZERO-DISCOUNT arm are both constructed so that the
   "intent-free reproduces the loop" claim CAN fail; nothing in either
   design structurally forces the control to resist entrapment, mirroring
   N1's own "both controls behaved as a real test, not a rigged one"
   discipline (`ABUSIVE_N1_CREDIBILITY_LOOP_RESULTS.md`).
4. **General machinery, minimal new content** — each rung adds exactly ONE
   new rule to N1's existing four, replacing (not augmenting) the one
   deliberate-construct rule; the dyad mechanism, the window/dysregulation
   mechanism, and the credibility-comparison rule SHAPE are all reused
   unmodified. A design needing bespoke intent-detection machinery would be
   weaker (it would be modelling "how to tell if someone is lying," not
   testing whether the loop needs a lie at all).

### Smuggled premises to REFUSE
- **"Intent-free means no responsibility / it wasn't really abuse."**
  REFUSED, explicitly and at length, because this is the single most
  important nuance this doc must not get wrong. The clinical and legal
  reality this line's own dyad and network docs already state (Part F of
  both) is that **responsibility for harm and conscious knowledge of
  wrongdoing are not the same axis.** Bandura's own framework (A1) is
  explicit that moral disengagement is an ACTIVE process a person is
  responsible for engaging in, not evidence of innocence; batterer-
  intervention programs (A2) treat minimization and denial as THINGS TO
  DISMANTLE precisely because the underlying conduct is harmful regardless
  of whether the perpetrator privately experiences it as such — "he didn't
  know he was doing it" is a description of a psychological mechanism, not
  a legal or moral defence, and this line's own standing Part F precedent
  ("abuser is simply evil — REFUSED for modelling purposes, not moral
  exculpation") applies here with the SAME force in the OPPOSITE direction:
  just as refusing "simply evil" does not exculpate, demonstrating
  "not calculating" does not exculpate either. **A model that shows the
  pattern can occur without deliberate intent is a model of MECHANISM,
  offered to make the pattern legible and to inform WHAT KIND of
  intervention helps (Part C) — it is never offered as, and must never be
  read as, a mitigation of the real-world harm or a reason to extend more
  benefit of the doubt to a real abuser.** If a future reader of this doc's
  eventual results section tries to use it that way, that is a misuse of
  the finding, and this scoping states so pre-emptively.
- **"Unintentional = the same as accidental, one-off, or minor."** REFUSED
  — A3's typology evidence is explicit that the Dysphoric/Borderline
  subtype's violence is "moderate to brutal," concentrated on the family,
  and clinically serious; A4's reactive-aggression literature describes
  a "hot-blooded," high-arousal mechanism, not a mild or trivial one.
  Nothing in U1/U2's design proposes a LESS harmful abuser — only a
  DIFFERENTLY-CONSTRUCTED one, with the SAME dyad-level induction as N1's
  own already-gated mechanism (Part D's intensity note, above).
- **"If it's not deliberate, the abuser can't help it, so nothing can be
  done."** REFUSED — this is the mirror image of the dyad line's own
  "learned helplessness ≠ the victim can't be helped" refusal (R4/R5). A1's
  moral-disengagement mechanisms and A2's minimization/denial are named,
  in their OWN source literature, as TREATABLE targets of intervention
  (batterer-intervention programs exist specifically to dismantle them).
  Mechanism-not-chosen does not mean mechanism-not-changeable.
- **"The self-deception account is just a nicer way of saying the same
  thing as deliberate deception, so testing it is pointless."** REFUSED —
  this doc's own A8 finding (von Hippel & Trivers) shows the relationship
  between self-deception and strategic deception is a live, non-trivial
  theoretical question in the literature ITSELF, not a semantic
  distinction this doc is inventing; whether the two produce the SAME
  substrate-level observable (the question U1/U2 test) is exactly the kind
  of question worth an empirical, falsifiable answer rather than an
  a priori dismissal in either direction.
- **Anthropomorphic over-reading.** REFUSED — these remain SYNTHETIC
  scalar-arousal / reputation-belief-attr dynamics over a graph, grounded
  in the creator's in-vivo experience, NOT claims that the graph
  "genuinely doesn't know" in any subjective sense, or that the substrate
  models real self-deception as a phenomenon rather than as a data
  structure with no divergence node. Mechanism-proven ≠ clinically-valid ≠
  sentient; all three kept separate, per the line's standing rule.

---

## OPEN QUESTIONS (what scoping could not settle — for the preregs)

1. **Does U1's context-gating need a new mechanical world-adapter fact
   ("is this tick dyad-coupled or not"), or does N1's existing
   `attended_by` edge presence already give this for free?** Likely the
   latter (the edge either exists for this tick's topology or it doesn't,
   matching N1's own NON_DYSREGULATED_CONTROL's mechanical topology
   choice), but not confirmed against the real graph — a build question.
2. **Is `minimization_discount` (U2) best modelled as a single fixed
   constant (matching N1's own `instability_discount_weight` convention),
   or does the batterer-typology literature (A3) suggest it should vary by
   a declared "subtype" parameter** — testing whether a
   Family-Only-adjacent operating point and a Generally-Violent-Antisocial-
   adjacent operating point produce qualitatively different (not just
   quantitatively different) outcomes? Deliberately out of scope for a
   first minimal rung (Part B's "why exactly two" note) but named as the
   natural NEXT axis if U1/U2 land.
3. **Should U1 and U2 be run as genuinely SEPARATE rungs, or composed into
   one rung with two arms?** This doc scopes them separately (matching
   N1's own precedent of one rung per headline mechanism) because they
   test different, independently-failable claims (timing vs. belief-
   distortion) — but a prereg author could reasonably decide to fold both
   into one rung's arm set if that proves cleaner once building starts.
4. **The A5 DV-specific compartmentalization application is [LOW–MEDIUM] and
   is NOT what U1/U2 are built on** (U1 rides A4/A7's better-corroborated
   reactive/context-dependent constructs; U2 rides A1/A2/A6's [HIGH]
   constructs) — A5 is included in Part A for completeness because the task
   brief named it explicitly, but no rung design above depends on it; if a
   future rung wants to model compartmentalization SPECIFICALLY (a
   genuinely non-context-triggered, non-arousal-driven coexistence of two
   self-models), that is a different, not-yet-designed mechanism.
5. **The A8 (von Hippel & Trivers) complication is named but not resolved.**
   Whether a "no-decision-node" construction is philosophically the right
   way to represent self-deception (as opposed to a DIFFERENT, more
   sophisticated split — e.g. an unconscious/automatic process node distinct
   from a conscious/controlled one, which is closer to von Hippel &
   Trivers's own dissociation account) is left open; U1/U2 both take the
   SIMPLER "no split at all" reading as the sharpest, most falsifiable first
   test, not as a claim that it is the only defensible model of
   self-deception.
6. **The honest fork (Part D) is adopted, not proven** — carried from the
   dyad and network scoping; unresolved, as stated there.
7. **Prior-art absence claims are weak** (Part F) — the "no ABM of
   unintentional/self-deceived harm reproducing a credibility-asymmetry
   loop" absence is targeted-search only across two independent scoping
   passes now; re-verify with dedicated searches before any prereg claims
   primacy.
8. **A genuinely-intentional comparison condition is NOT scoped here, and
   the correction above ("WHERE THE QUESTION ACTUALLY LIVES") means one is
   now missing from the three-way picture.** N1, as built, does not contain
   an `Argmax`/goal-directed choice selecting the stated-face — it is an
   unconditional broadcast, authored that way by the rung's builder, not
   selected at runtime by the agent. So N1/U1/U2 as a set currently compare
   "divergence present, unconditionally" (N1) against "no divergence, timing-
   driven" (U1) and "no divergence, discount-driven" (U2) — none of the
   three test what happens when the divergence itself is the OUTPUT of a
   goal-directed choice (e.g. an `Appraisal`+`Argmax` over candidate
   stated-faces, scored against a declared goal such as "minimise the
   network's suspicion given the observed harm"). A future rung — call it
   **U0** to mark it as the missing genuinely-intentional condition this
   correction surfaces, not a third no-intent alternative — would need
   exactly that: a choice mechanism, not just a divergence. Until U0 (or
   something like it) exists, this line can report "the pattern does not
   require a stated≠held STRUCTURE" (what U1/U2 actually test) but cannot
   yet report "the pattern does not require INTENT" as directly as this
   doc's own framing implies, because nothing built so far — N1 included —
   has isolated intent as a variable. This is the single most important
   thing a prereg author must resolve before claiming U1/U2's results speak
   to intent rather than to structure.

---

**Bottom line.** N1 demonstrated that a network can be entrapped by an abuser
presenting two diverging faces — but reading N1's own seed closely shows
that divergence lives in exactly ONE rule (`n1_abuser_stated_charm`'s
unconditional broadcast), and, on inspection, that rule is not itself a
goal-directed CHOICE either (no `Argmax`, no evaluation against a benefit) —
it is a fixed, always-on divergence the builder authored, not one the agent
selected. So "intent" was never cleanly isolated as a variable by N1 alone.
This scoping proposes two minimal, failable compositions that remove the
DIVERGENCE — **U1** (the abuser's calm face is genuinely, contextually true;
no concealment, only timing) and **U2** (the abuser's own account of events
is sincerely, self-servingly distorted, via a fixed discount constant, not a
goal-evaluated selection; no external lie, only a distorted held belief) —
while reusing everything else N1 already validated, unmodified, and names
the genuinely-intentional comparison condition (an `Argmax`-driven choice
among candidate presentations, scored against a declared goal — Open
Question 8, tentatively "U0") that would be needed to test the INTENT axis
directly rather than infer it from N1's absence of a choice mechanism. The
clinical literature (Bandura's moral disengagement, batterer-intervention
minimization research, the Holtzworth-Munroe & Stuart typology,
reactive/proactive aggression, Baumeister's self-serving narrative
construction) makes a strong case that MOST real abusers are closer to the
non-calculating, reactive pole than to a scheming, goal-evaluating one — and
the typology evidence (A3) is explicit that only ONE of its named subtypes
maps onto a genuinely instrumental, DARVO-capable actor. Whether the
substrate's own credibility-asymmetry mechanism actually needs a
goal-directed choice to produce its headline pattern is not asserted either
way here — that is exactly what U1/U2 (for the STRUCTURAL divergence
question) and a future U0 (for the INTENT question proper) are built to find
out, and a null in either direction is named, in advance, as an equally
valuable, equally reportable result. **Intent-free is not a claim of
innocence** — Part F states this at length because it is the single easiest
way this document could be misread, and the misreading would be a serious
one. **This doc authorises no build; a build begins only when a rung's
prereg locks Part D first.**
