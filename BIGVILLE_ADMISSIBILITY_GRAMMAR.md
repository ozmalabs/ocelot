# BIGVILLE — THE ADMISSIBILITY GRAMMAR OF A SOCIETY (design adjudication)

**Status: DESIGN ONLY. No code, no seeds, no runs in this document.** This
adjudication grounds a foundational refactor of bigville's conduct rules under a
governing **admissibility grammar (Γ)**. It does not implement it.

## The diagnosis being grounded

The creator's complaint, verbatim in spirit: *"the fact that we spend so long
considering violence is indicative that the rules have drifted too far and we
need admissibility grammar."*

The measurement backs the complaint. Violence in bigville is **15 rules across 4
seeds** (`bigville_viol_act` / `_evidence` / `_prosecute` / `_kill`) — a full
subsystem with its own value-decision trigger, evidence accumulation, abductive
belief, council prosecution, adjudication, and a "fifth route to death"
(`BIGVILLE_VIOL_PREREG.md`, `BIGVILLE_VIOL_RESULTS.md`). It rivals the economy in
engineering weight. Meanwhile **none of the four violence seeds declares a single
grammar production** (measured: `"productions": []` in all four). Violence is not
governed by Γ at all — it is a richly-modelled *behaviour*, fired by rules that
bypass the admissibility checker entirely.

**The reframe.** Violence should not be a richly-modelled behaviour. It should be
an **inadmissibility** — the rare, marked residual that appears when the
norm-grammar (Γ) fails to admit an act. Admissible conduct (greet / trade / help
/ gossip / court) is what Γ *generates by default*; violence / theft / betrayal
are inadmissible-by-default, and when they occur they are **marked as violations**
that trigger sanction / shame / reputation-damage / enforcement. Part 1 shows the
social-science literature says almost exactly this. Part 2 shows the substrate
already *has* the machinery to express it, and that bigville simply routes around
it.

---

# PART 1 — The admissibility grammar of a society (literature)

Real citations. Consensus is separated from contested. Confidence flags are
explicit; where a detail was not re-verified against a primary source it is
marked so. No fabrication.

## 1. Social norms as generative constraints on conduct

**Cristina Bicchieri, *The Grammar of Society: The Nature and Dynamics of Social
Norms* (Cambridge University Press, 2006).** The title's "grammar" is not
decoration and is directly load-bearing for this project: Bicchieri treats norms
not as a list of prohibitions but as a *generative* system — a small set of
expectation-dependent conditional rules that produce a wide range of
context-appropriate behaviour, the way a grammar generates sentences. Her account
(the dominant operationalisation in the empirical norms literature — **consensus**):

- A social norm is a **behavioural rule** a person prefers to conform to
  *conditionally*, when two expectation conditions hold: **empirical
  expectations** (I believe enough of the reference group *does* conform) and
  **normative expectations** (I believe enough of them *think I ought* to conform,
  and may **sanction** deviation).
- **Conditional preference**: the preference to conform is *contingent* on those
  expectations. Change the expectations and behaviour flips. This is the
  empirically load-bearing claim (robust across her lab and others').

This directly answers the modelling question: **yes — a norm is well-modelled as
a conditional admissibility constraint on action, enforced by mutual expectation
(empirical + normative), not by the act's intrinsic payoff.** The crucial
subtlety for a substrate: the constraint is **state-dependent**, parameterised by
a population's beliefs — not a fixed edge. A norm can collapse suddenly in a
belief cascade even when no one's underlying values changed.

**Contrast — Edna Ullmann-Margalit, *The Emergence of Norms* (Oxford, 1977).** An
early game-theoretic account: norms as *solutions* to recurrent strategic
problems, sorted by the game that generates them — (a) PD-norms (rescue
cooperation from a defection trap), (b) coordination norms (select one of many
equilibria), (c) **norms of partiality/inequality** (stabilise an unequal status
quo). Category (c) matters for §4 (the dark side). **Consensus** as a foundational
treatment.

**The "norms as equilibria" view** — Lewis, *Convention* (1969); Ullmann-Margalit
(1977); Sugden, *The Economics of Rights, Co-operation and Welfare* (1986); H.
Peyton Young, "The Evolution of Conventions," *Econometrica* (1993). A norm *is*
a (often repeated-game) equilibrium: self-enforcing because each person's
conformity is a best reply to everyone else's, sustained by self-fulfilling
expectations. (Lineage verified via Stanford Encyclopedia of Philosophy, "Social
Norms.")

**The live debate (contested).** Pure equilibrium accounts (Young / Sugden) say
people conform because it is a *best reply* — no preference change needed.
Bicchieri argues the *normative* expectation reshapes preferences (a "norm-based
utility" that transforms the payoff matrix), so norm-following is more than any
Nash equilibrium. **Equilibrium-selection vs. preference-transformation is a
genuine open dispute**, not settled.

**Bicchieri, *Norms in the Wild* (Oxford, 2017)** sharpens the taxonomy —
distinguishes **social norms** (conditional on *both* empirical and normative
expectations) from **descriptive norms** (empirical only), **customs**
(unconditional), and **moral/legal norms**. Useful for a model: "everyone does X"
and "X is required" are *different constraint types with different collapse
dynamics*, and only the social-norm type carries the sanction-backed normative
expectation. (Taxonomy high-confidence; year/publisher verified via a review, not
the book.)

## 1a. Restricted option-spaces — people do not deliberate non-options (the generative core)

This subsection is the literature backbone for the reframe's *sharpest* claim (see
Synthesis): a norm-grammar's real work is to **emit a small candidate set**, so
that pathological acts are *never considered*, not scored-low-and-rejected.

- **Bounded rationality / satisficing — Herbert Simon (bounded rationality 1947;
  satisficing 1956).** Any choice model requiring inspection of *all* alternatives
  is, in Simon's words, "highly implausible in practice." Real decision-makers work
  over a **restricted set of alternatives examined one at a time** against an
  aspiration level, and stop — they never enumerate the full option space. **The
  consideration set is generated/pruned upstream of evaluation, not exhaustively
  scored.** (Consensus in decision theory; verified this session via SEP "Bounded
  Rationality." Related downstream: Klein's recognition-primed decision — experts
  often generate a single workable option rather than compare a menu.)
- **Sacred/protected values and taboo trade-offs — Philip Tetlock, Kristel, Elson,
  Green & Lerner, "The psychology of the unthinkable: taboo trade-offs, forbidden
  base rates, and heretical counterfactuals," *Journal of Personality and Social
  Psychology* 78(5):853–870 (2000); Alan Fiske & Philip Tetlock, "Taboo
  Trade-offs," *Political Psychology* 18 (1997); Baron & Spranca, "Protected
  values," *OBHDP* 70 (1997).** Sacred values are treated as possessing
  significance that **precludes comparison or trade-off** — they do *not enter the
  trade-off space at all*. The decisive detail for this project: **merely
  contemplating** a taboo trade-off (pricing a sacred value) evokes **moral outrage
  and moral cleansing** — the *act of considering* the option is itself
  transgressive. "Unthinkable" is not a low-scored option but a **non-option that
  is a violation to even evaluate**. (Tetlock 2000 verified this session; Fiske &
  Tetlock 1997 and Baron & Spranca 1997 high-confidence from established knowledge,
  endorsed by the coordinator — check primary source before quoting pages.)

**Consequence for modelling (load-bearing).** For a normal agent in a normal
context, harming a neighbour is not a down-weighted candidate — it is **absent from
the option-space**; it costs *zero deliberation* because it is never generated. A
norm-grammar that merely *scores* violence low still pays the cost of ranking it
every tick, and still models an agent who *considers* harming everyone around them
constantly. That is precisely the phenomenon the creator flags as drift. The
literature says the option-space is **restricted at generation, not pruned at
evaluation**.

## 2. How societies make violence EXCEPTIONAL

**Max Weber, "Politics as a Vocation" (1919).** The state "(successfully) claims
the **monopoly of the legitimate use of physical force** within a given
territory." Two points to carry forward: (1) it is *legitimate* force —
**legitimacy, not raw coercion, is the operative concept** (the §4 legitimacy
dimension appears already at the foundational level); (2) Weber framed it as a
*historically contingent* achievement (feudalism permitted private warfare; the
modern state expropriated the means of violence). **Consensus** as the standard
definition of the state.

**Norbert Elias, *The Civilizing Process* (German 1939; English 1978/82).**
State formation monopolised violence → suppressed private feud + lengthened
chains of interdependence → drove internalisation of *self-restraint*
(external constraint *Fremdzwang* → self-constraint *Selbstzwang*). The long-run
internalisation of restraint is the through-line. **Framework respected;
the monotonic-decline directional claim is contested** (Eurocentric / teleological
critiques), and is entangled with the Pinker debate below.

**Ernst Fehr & Simon Gächter, "Altruistic punishment in humans," *Nature*
415:137–140 (2002).** In anonymous one-shot public-goods games, cooperation
*collapses* without punishment and is *sustained* when players pay a cost to
punish free-riders (pay 1 to impose 3). Punishment yields no material return —
"altruistic"; the proximate driver is negative emotion toward defectors.
**Consensus that the phenomenon is real and robust in the lab.** *Contested:* the
"strong reciprocity" evolutionary interpretation; and cross-cultural work
(Herrmann, Thöni & Gächter, *Science* 2008) found **antisocial punishment**
(punishing cooperators) in some societies, complicating any clean story.

**Ernst Fehr & Urs Fischbacher, "Third-party punishment and social norms,"
*Evolution and Human Behavior* 25:63–87 (2004).** *Unaffected third parties* pay
to punish norm violators (~2/3 punished distribution-norm violations; ~60%
cooperation-norm violations). This is the experimental basis for treating
norm-enforcement as **impersonal/disinterested**, not just victim retaliation —
the second-party vs. third-party axis of §3, established here. **Consensus** (lab);
magnitude/origin debated.

**Christopher Boehm, *Hierarchy in the Forest* (Harvard, 1999).** Nomadic
hunter-gatherer bands enforce egalitarianism by a **"reverse dominance
hierarchy"** — the rank-and-file coalesce to suppress would-be dominators using
ridicule, criticism, disobedience, **ostracism**, and at the limit execution.
Violence/domination held rare *from below*, by a coalition of subordinates, not a
central authority. **Ethnographic leveling pattern well-attested; the deep
evolutionary story is a strong hypothesis.**

**Steven Pinker, *The Better Angels of Our Nature* (Viking, 2011).** Long-run
decline of violence, driven by Leviathan (explicitly building on Weber/Elias),
commerce, expanding empathy, feminisation, reason. **This is genuinely contested —
do not present as consensus.** Serious critiques, even-handedly:
- **Fat tails — Cirillo & Taleb, *Physica A* 452:29–45 (2016).** War-casualty
  distributions are extremely fat-tailed; long quiet stretches are *expected*
  under such distributions and cannot establish a structural change. "The Long
  Peace" is statistically hard to distinguish from noise. Pinker replied; the
  exchange is **unresolved**.
- **Archaeology — R. Brian Ferguson, Douglas P. Fry.** Prehistoric war-mortality
  estimates rest on non-representative sites; clear skeletal evidence of organised
  war is largely post ~8000 BCE, inflating the "violent past" baseline.
  **Anthropologists genuinely split.**
- **Comparability / conceptual — John Gray.** The thesis is an Enlightenment
  progress narrative; "per capita" hides absolute suffering; categories of
  "violence" aren't commensurable across eras.
- **Even-handed bottom line:** the *European interpersonal-homicide* decline over
  centuries (Eisner's homicide series) is the strongest, fairly robust leg; the
  grand unified "all violence declined" claim is contested on data quality,
  comparability, prehistoric baselines, and the statistics of rare catastrophic
  war.

**What keeps violence rare in SMALL communities specifically** — the mechanism
that works *without* a Leviathan, and the one bigville actually needs:
- **Robert C. Ellickson, *Order Without Law: How Neighbors Settle Disputes*
  (Harvard, 1991).** Shasta County ranchers resolve disputes through informal
  norms of "neighborliness," truthful negative **gossip**, and reciprocal
  self-help — *not* courts, often in defiance of formal entitlements. Informal
  order arises specifically among **"close-knit" groups** (dense, continuing,
  reciprocal ties, good information flow) because **reputation is a working
  currency** there. **Consensus (landmark).**
- **Elinor Ostrom, *Governing the Commons* (Cambridge, 1990).** Durable community
  self-governance rests on **monitoring** (by the users themselves) and
  **graduated sanctions** (punishment scales with severity/repetition — a gossip
  reminder first, escalating only as needed). Graduated sanctions are the template
  for keeping enforcement cheap, proportionate, and *non-escalatory* — the
  opposite of feud. **Consensus (Nobel 2009).**

**Through-line for §2:** violence is made rare by **two substitutable-but-
complementary regimes** — (a) a *vertical* one, the state's monopoly on legitimate
force (Weber/Elias/Pinker's Leviathan); (b) a *horizontal/decentralised* one,
informal sanction by reputation, gossip, ostracism, graduated peer punishment in
close-knit groups (Boehm/Ellickson/Ostrom/Fehr). **Small communities lean on (b).**
This dovetails with the repo's own §B (`BIGVILLE_SPEECH_SCIENCE.md` §B3–B5:
Gemeinschaft/Tönnies, network closure/Coleman 1988, gossip-as-control/Gluckman
1963 & Merry 1984, indirect reciprocity/Nowak & Sigmund 1998/2005, Ellickson,
Ostrom) — bigville already has a reputation loop; §B4 is the enforcement layer.

## 3. Violation, marking, and repair

**Second-party vs. third-party punishment** — established experimentally by Fehr &
Gächter (2002, second-party) and Fehr & Fischbacher (2004, third-party). The
theoretical significance: third-party punishment is what makes a sanction a
*norm* enforcement (impersonal) rather than private retaliation. **Consensus** (lab).

**Moral emotions — shame vs. guilt.** The folk/Benedict "shame culture vs. guilt
culture" (Ruth Benedict, *The Chrysanthemum and the Sword*, 1946) as
public-vs-private is now regarded as an **oversimplification**. The dominant
empirical psychology (June Price Tangney; Tangney & Dearing, *Shame and Guilt*,
2002; Tangney, Stuewig & Mashek, *Annual Review of Psychology* 2007): the
distinction is **self-vs-behaviour** — **shame** = negative evaluation of the
*whole self* ("I am bad") → withdrawal, defensiveness, sometimes aggression;
**guilt** = negative evaluation of a *specific act* ("I did a bad thing") →
reparative, prosocial action (apology, restitution). **Consensus** on the
self/behaviour distinction and its divergent consequences. **Model consequence:
the same violation routes to *repair* (guilt) or to *withdrawal/counter-
aggression* (shame) depending on which emotion the marking triggers** — a
first-class fork for a refounding.

**Reputation, gossip, ostracism, exclusion** — Boehm (ostracism/execution as
leveling); Ellickson (gossip as the actual enforcement mechanism); indirect
reciprocity / reputation (Nowak & Sigmund, *Nature* 2005 — canonical, from
established knowledge). Ostracism/exclusion is the terminal informal sanction
short of violence.

**Restorative justice — John Braithwaite, *Crime, Shame and Reintegration*
(Cambridge, 1989).** Crime is *lower* where shaming is **reintegrative**
(disapproval of the act within continued respect for the person — "good person,
bad deed," with rituals to restore membership) and *higher* where shaming is
**stigmatising** (disrespect, permanent mark → pushes offenders into deviant
subcultures). **The distinction is widely accepted; the causal recidivism claim is
empirically mixed.**

**Stigma — Erving Goffman, *Stigma* (1963)** — the durable-marking pole (a
discrediting attribute "spoils" identity), opposite to reintegration. **Taboo —
Mary Douglas, *Purity and Danger* (1966)** — taboo as categorical (not
cost-benefit) prohibition; violation triggers pollution/disgust rather than
graduated sanction. (Goffman/Douglas high-confidence-canonical; not re-verified
this session.)

**Jonathan Haidt — Moral Foundations Theory** (Haidt & Joseph 2004; *The
Righteous Mind*, 2012): a small set of putatively innate foundations —
Care/harm, Fairness/cheating, Loyalty/betrayal, Authority/subversion,
Sanctity/degradation (+ later Liberty/oppression). **Contested, flag it:** the
five-factor structure **fails to replicate** cleanly in many samples (Iurino &
Saucier, 27-country, 2020 — a two-factor individualising-vs-binding solution
often fits better); innateness/modularity critiqued (Suhler & Churchland 2011);
partial rehabilitation via MFQ-2 (Atari et al. 2023). Present as influential but
unsettled — useful as a *taxonomy of what gets marked*, not as settled cognitive
architecture.

## 4. Honest bounds — admissible ≠ moral; the legitimacy dimension is required

This is the most important corrective for the refactor, and the literature is
strong on every point.

**Norms coordinate on bad equilibria and enable oppression.** Ullmann-Margalit's
**norms of partiality** (1977) exist precisely to entrench inequality — stable
because deviation is individually costly, even when the equilibrium is unjust. The
equilibrium view (Lewis/Young/Sugden) is explicitly *value-neutral*: a norm is
self-enforcing whether benign (drive-on-the-right) or harmful (foot-binding, honor
killing, caste avoidance). Bicchieri (*Norms in the Wild*, 2017) makes it
operational — FGM, child marriage persist as genuine *social norms* held by
empirical + normative expectations. **Consensus: "everyone conforms and expects
conformity" is orthogonal to whether the practice is good.** So **admissible ≠
moral is a structural fact, not a caveat.** (This matches the repo's own §B6 dark
side — Portes 1998 "dark side of social capital": closure produces surveillance,
enforced conformity, exclusion, downward levelling.)

**Violence is often normatively SANCTIONED / legitimate.** The key design point:
a binary permit/forbid over "violence" is *wrong*, because many societies'
norms don't forbid violence — they *prescribe* it in specified circumstances and
*forbid* it in others. The same physical act (killing a person) is murder,
execution, self-defence, honor-restoration, blood-feud obligation, or war
depending on the *normative frame*.
- **Weber (1919)** already encodes it: the state claims *legitimate* violence —
  punishment and war are normatively *authorised* violence. Legitimacy is the
  discriminator, not the physical act.
- **Culture of honor — Richard Nisbett & Dov Cohen, *Culture of Honor* (1996).**
  In an honor culture, violence in response to *insult / threat to reputation* is
  **normatively legitimate and expected**, not deviant (elevated argument/honor —
  not felony — homicide in the U.S. South; lab: insulted Southern students showed
  larger cortisol/testosterone rises and more dominant responses). **The honor-
  psychology finding is solid; the herding-origin causal story is more contested.**
  General point — some cultures make retaliatory violence *obligatory*, so
  *failing* to be violent is the norm violation — is well-established.
- **Feud / blood-vengeance** — the clearest ordered-violence case: killing carries
  an *obligation* to retaliate, bounded by rules (legitimate targets, termination,
  wergild/compensation as an off-ramp). Norm-governed, not norm-breaking.

**Design implication the literature forces:** conduct-norms cannot be a
one-dimensional `permit / forbid` mask. You need a **legitimacy dimension**
orthogonal to the physical-act type: a per-act, per-context authorisation status
(**forbidden / permitted / obligatory**), plus **who** is an authorised agent
(state vs. private — Weber), **against whom** (legitimate target), **under what
triggering condition** (insult, prior offence, defence, sanctioned punishment).
The same violence primitive is routed through a *legitimacy predicate*. This is
exactly what distinguishes murder from execution from self-defence in every
framework above — and it is why Bicchieri's *normative expectation* ("others think
I ought") does more work than a prohibition: for feud/honor/punishment the
normative expectation can *require* the violence.

### Consensus vs. contested — ledger

| Claim | Holder(s), year | Status |
|---|---|---|
| Decisions run over a restricted, generated consideration set (not full enumeration) | Simon 1947/1956 | Consensus (decision theory) |
| Sacred/protected values are non-options; even *considering* the trade-off is transgressive | Tetlock et al. 2000; Fiske & Tetlock 1997; Baron & Spranca 1997 | Consensus (finding robust); mechanism debated |
| Norms = conditional preference on empirical + normative expectations | Bicchieri 2006, 2017 | Consensus |
| Manipulating expectations flips conforming behaviour | Bicchieri; exp. econ | Consensus (lab) |
| Norms as game-theoretic equilibria / conventions | Lewis 1969; Ullmann-Margalit 1977; Sugden 1986; Young 1993 | Consensus (framework) |
| Equilibrium-selection **vs.** preference-transformation | Young/Sugden vs. Bicchieri | **Contested** |
| State = monopoly on *legitimate* force | Weber 1919 | Consensus (definitional) |
| Long-run internalisation of restraint via state formation | Elias 1939 | Framework respected; direction **contested** |
| Costly 2nd-party punishment sustains lab cooperation | Fehr & Gächter 2002 | Consensus (phenomenon); evo story **contested** |
| Disinterested 3rd-party punishment exists | Fehr & Fischbacher 2004 | Consensus (lab) |
| Egalitarian order via reverse-dominance leveling | Boehm 1999 | Pattern attested; evo story a hypothesis |
| Long-run decline of violence | Pinker 2011 | **Contested** (Cirillo-Taleb 2016; Ferguson/Fry; Gray) |
| Informal norms > law in close-knit groups | Ellickson 1991 | Consensus (landmark) |
| Monitoring + graduated sanctions sustain commons | Ostrom 1990 | Consensus (Nobel) |
| Shame (self) vs. guilt (act), divergent consequences | Tangney 2002/2007 | Consensus (supersedes Benedict 1946) |
| Reintegrative vs. stigmatising shaming | Braithwaite 1989 | Distinction accepted; recidivism effect **mixed** |
| Moral Foundations Theory (5–6 innate foundations) | Haidt 2004–2012 | **Contested** (factor structure; innateness) |
| Honor cultures make retaliatory violence legitimate/obligatory | Nisbett & Cohen 1996 | Finding solid; herding-origin **contested** |
| Norms can be harmful / entrench oppression (admissible ≠ moral) | Ullmann-Margalit 1977; Bicchieri 2017 | Consensus |

**Confidence.** Web-verified this session (author/year/venue/core claim):
Bicchieri 2006; Ullmann-Margalit 1977; Lewis/Sugden/Young lineage; Weber 1919;
Elias 1939; Fehr & Gächter 2002 (*Nature* 415:137–140); Fehr & Fischbacher 2004
(*EHB* 25:63–87); Boehm 1999; Pinker 2011 + Cirillo & Taleb 2016 (*Physica A*) +
Ferguson/Fry; Ellickson 1991; Ostrom 1990; Braithwaite 1989; Nisbett & Cohen
1996; Tangney (shame/guilt); Haidt MFT replication debate. High-confidence from
established knowledge but **not re-verified this session** (check primary source
before quoting page/edition): Bicchieri *Norms in the Wild* 2017; Goffman 1963;
Benedict 1946; Douglas 1966; Nowak & Sigmund 2005; Herrmann/Thöni/Gächter 2008;
Eisner homicide series; Suhler & Churchland 2011; Atari et al. 2023 (MFQ-2). No
citation was fabricated.

---

# PART 2 — The substrate's OWN admissibility-grammar machinery (code)

**Headline finding: the substrate already contains a complete weighted
admissibility grammar with a two-mode inadmissibility checker — and it is exactly
the "inadmissible-by-default, marked when unadmitted" machinery the reframe wants.
Bigville's conduct rules route around it in two independent ways.**

## 2.1 What Γ is, in this codebase

`runners/dsl/src/grammar.rs` — **Γ is a weighted admissibility grammar** (its own
header: "Γ — weighted admissibility grammar (Paper §1, Definition 2)").
- A **`Production`** (`grammar.rs:31-39`) is `(src-pattern, edge_type, tgt-pattern,
  where-clause, weight, provenance)`. A production says: *an edge of this type,
  from a node of this type to a node of this type, satisfying this where-clause, is
  admissible* — with a real-valued **weight** (`grammar.rs:5-8`: selection over
  admitted candidates ∝ exp(w); binary admit/deny is the `w > −∞` degenerate case).
- The **`Grammar`** (`grammar.rs:48-57`) holds the productions, an index
  `(src_type, edge_type, tgt_type) → productions`, and the **type vocabulary**
  (`node_types`, `edge_types` — "N ∪ E in paper notation").
- `candidates(src, edge, tgt)` (`grammar.rs:91-96`) returns the productions that
  could admit a triple; `knows_node_type` / `knows_edge_type`
  (`grammar.rs:100-106`) test vocabulary membership.

`runners/dsl/src/checker.rs` — **C, the consistency checker: "the only path
through which Π learns whether a prospective edge is admissible under Γ"**
(`checker.rs:1-3`). Its two-mode outcome (`checker.rs:22-33`, `check_edge` at
`53-103`) is precisely the marking the reframe needs:
- **`Type2VocabAbsent`** — a constituent type isn't even in N ∪ E; the operation
  "can't even be formed" (`checker.rs:10-11, 68-76`).
- **`Type1NoProduction`** — **all three types are in-vocabulary but no production
  admits the triple** (no candidate, or every candidate's where-clause is false)
  (`checker.rs:25-30, 78-99`).
- **`Admitted(prods)`** otherwise, carrying the admitting productions for
  explanation (`checker.rs:23-24, 100-102`).

**`Type1NoProduction` IS "violence-as-inadmissibility."** An act whose edge type
is known vocabulary but which no production admits is, by construction, the rare
marked residual: in-frame, recognisable, but *not generated by the norm-grammar*.
That is the exact shape the creator is asking for, already implemented.

## 2.2 The checker DOES gate the direct mutation API…

`runners/dsl/src/substrate.rs:1293-1345` — **`add_edge` runs every prospective
edge through `checker.check_edge` first.** On `Admitted` it inserts and records
which productions admitted (`1310-1320`); on `Type1NoProduction` it **rejects**
and charges a reject to each failed candidate (`1322-1339`); on `Type2VocabAbsent`
it rejects (`1340-1343`). The probe surface is rich and already exposed to
adapters:
- `is_edge_admissible` (`substrate.rs:1540-1600`; Python `substrate_rs/__init__.py:904`)
  — would this edge be admitted?
- `admissible_edges_from` (`substrate.rs:1604-1626`) — filter candidate targets to
  the admissible ones.
- `admissible_moves` (`substrate.rs:1638-1686`) — enumerate admitted
  (tgt_type, attrs, **weight**) candidates; weights add per Paper §1.2 Definition 2;
  the caller softmaxes for Boltzmann selection.
- Γ can **grow**: `add_production` (`substrate.rs:736-743`) adds a production and
  bumps `gamma_epoch`; the meta-Γ growth path turns a discovered relation into a
  new admitting production (`tests/test_gamma_growth_migrated.py`: "a discovered
  relation grows a production... lands in the grammar... idempotent on
  rediscovery"). So the grammar of admissible conduct is itself *dynamic and
  self-extensible* — the same dynamic-quantization move used everywhere else in
  this tree.

## 2.3 …but rule effects BYPASS the checker entirely

`runners/dsl/src/rewrite.rs:11-16` (verbatim): *"Per the paper's Axiom 3 + the
user's 'Π is the only mutation surface' principle, rewrite operations could flow
through Π / C for admissibility gating. **The Python version bypasses this (rules
are 'presumed admissible by construction'); we match that posture here** so
existing rule sets work unmodified. A `gated: bool` flag on `apply_rule` is
reserved for future opt-in admissibility checks."*

Confirmed at the applier: `Effect::AddEdge` writes via **`graph.insert_edge`**
directly — the raw graph mutation, **not** `substrate.add_edge` — at
`rewrite.rs:1351` and `rewrite.rs:1786`. **No `check_edge` call is on the rule-
effect path.** So every edge a Rule writes lands unconditionally, whatever Γ says.
The `gated` flag that would close this is *reserved but unbuilt*.

**This is the load-bearing bypass.** All of bigville's conduct is Rules. Therefore
all of bigville's conduct — greeting, trading, and *violence alike* — is written
into the graph without ever consulting the admissibility grammar.

## 2.4 Where bigville specifically routes around Γ

Measured across all 62 `bigville_*` seeds (production-count / rule-count per seed):
- **Only two seeds declare ANY productions:** `bigville_laws_enforcement.json`
  (12 productions / 5 rules) and `bigville_drama_social.json` (7 productions / 7
  rules). **Every other bigville seed declares `"productions": []`.**
- **All four violence seeds declare zero productions:** `bigville_viol_act`
  (0 prod / 4 rules), `bigville_viol_evidence` (0/5), `bigville_viol_prosecute`
  (0/5), `bigville_viol_kill` (0/1). Violence is **15 pure Rules, no Γ.**

And the two seeds that *do* declare productions do **not** use Γ as a conduct
constraint — they use it as a bare **vocabulary declaration**. Every production in
`bigville_laws_enforcement.json` is an unconditional `(src_type, edge_type,
tgt_type)` triple with **no where-clause** — e.g. `Constable -knows_law-> Law`,
`Constable -detected_violation-> Violation`, `Council -enacted-> RemovalOutcome`.
Their only effect is to add those edge types to N ∪ E so the enforcement rules'
edges don't trip `Type2VocabAbsent`. Same in `bigville_drama_social.json`
(`MaryTom -made_claim-> DramaClaim`, etc.). **This is Γ used to make edges *legal*,
which is the exact opposite of using Γ to mark violence *inadmissible*.**

Net: bigville has (i) rule effects that bypass the checker by construction, and
(ii) a violence subsystem with no productions at all — so nothing about violence
is ever checked against a norm-grammar. Violence is a first-class *behaviour*
fired by a value-decision trigger (`bigville_viol_act`'s `bv_trigger`:
`trigger_value = snap_pressure + w_spite·spite_gain + hunger·desperation_gain vs
threshold`), exactly the "richly-modelled behaviour" the creator says has drifted.

**And note the *shape* of that trigger — it is evaluate-then-suppress in the seed
data.** `bv_trigger` computes `trigger_value` vs a threshold for the considering
agent, and `bv_refrain` is its **disjoint "considered-but-declined" arm** (from the
seed's own description: "bv_refrain is the disjoint decline arm — ablate the
trigger → refrain, no act"). So the current design has every armed agent *consider*
violence each tick and usually refrain. That is the **gate model realised in the
seeds**: the violence option is permanently on the menu, ranked and suppressed —
the exact pattern the Synthesis argues must be replaced by *not generating the
candidate at all*. This is the concrete self-indictment: we put the option on the
menu.

## 2.5 The enforcement layer bigville already has (order without law)

The horizontal regime of Part 1 §2 is partly built already, as Rules:
- `bigville_loop_reputation.json` — `bl_badmouth` (a soured creditor badmouths a
  defaulter; a `Badmouth` node minted; `debtor.badmouthed` rises),
  `bl_townsfolk_opinion` (reputation as a townsfolk-level aggregate). This is the
  gossip/indirect-reciprocity channel (Nowak & Sigmund; Gluckman; Ellickson).
- `bigville_bond_update.json` — directed, subjective, updatable `Bond(A→B)` with
  dissociable belief / affect / ToM slots; `bond_event_betrayal`,
  `bond_gossip_update`, etc. This is the reputation-fed **indirect update path**
  (`BIGVILLE_SPEECH_SCIENCE.md` §B4-B5).
- `bigville_laws_enforcement.json` / `bigville_viol_prosecute.json` — the
  *vertical* regime (Weber's Leviathan): witnessing, evidence, council
  prosecution, warn/punish.

**The pieces of both regimes exist. What is missing is the Γ that would make
violence the marked residual those regimes respond to, rather than a free
behaviour that fires alongside them.**

---

# SYNTHESIS + design implications (design only)

## The primary framing — GENERATE a small pro-social candidate set, don't score-and-suppress

The deepest design point, and the one that decides between the two shapes below:
**the secret is that most people spend very little time considering violence.** A
normal person in a normal context does not rank "hit my neighbour" low and reject
it — the option is **never on the menu**. The admissibility grammar's job is to
**emit the candidate action-set**, and for a normal agent that set *simply does not
contain* violence. The Argmax never sees it, spends zero cycles on it, and never
"considers" it. This is the difference between two architectures that look similar
and are not:

- **Gate model (evaluate-then-suppress).** Violence is in the Argmax menu every
  tick, ranked, and down-weighted or vetoed by a Γ-gate. The agent still *spends
  cycles considering it*. A Γ-LAYER-over-the-existing-pile reaches this, at best.
- **Grammar model (never emit).** Γ *generates* the candidate set; for a normal
  agent that set **does not contain violence at all**. It is not scored, because it
  is not generated. Violence becomes generable **only under rare generative
  conditions** — a norm already broken, an extreme threat, or a *legitimated role*
  (the legitimacy axis below) — and is marked + costly even then. Only a **from-Γ
  refounding** reaches this.

The literature is unambiguous that human decision works the second way, not the
first (Part 1 §1a): Simon's bounded rationality — choice runs over a **restricted,
generated consideration set**, never a full enumeration; Tetlock's taboo
trade-offs / protected values — pathological acts are **non-options whose very
*consideration* is a violation**, not low-utility options that lost a comparison.
"Unthinkable" is a statement about the *option-space*, not about a *score*. So the
correct model **restricts the option-space at generation**, and pathological acts
are **ungenerated, not penalised**.

**Convergence with this project's OWN efficiency discipline — the empty-match-set
proof.** The substrate already made exactly this move for computation, one level
down. Blocks 189000+ (`VISION_PROTOCOL.md` 189000, `EMPTY_MATCH_PROOF_RESULTS.md`;
`Substrate::empty_match_proof`): *a rule with ≥1 match edge is provably empty iff
some match edge's edge_type has zero live edges* — and such a rule is **skipped
entirely** (a rule that could never fire cost 99.93% of the tick; proving its match
set empty gave 176×, byte-identical). Apply that discipline to **conduct**: if a
normal agent has no `considers_violence` edge in its generated option-set, the
violence rule's match set is **empty**, and the whole apparatus (trigger value,
threshold, refrain arm) is **never enumerated** — the match set is empty, the cost
is zero, the act is un-considered. *Not-generating the violence candidate is the
empty-match-set proof applied to behaviour.* The grammar model is not just more
faithful to the social science — it is the same efficiency principle the project
already proved and shipped, lifted from rule-scheduling to conduct.

## The load-bearing model

A **social admissibility grammar** = a Γ over *conduct* in which:
1. **Admissible acts are generated/permitted by default.** Greet, trade, help,
   gossip, court are productions of Γ — the norm-grammar generates the ordinary
   texture of village life (Bicchieri's generative "grammar of society"). Most
   conduct is admissible *by construction*, so it is cheap and unmarked.
2. **Inadmissible acts (violence / theft / betrayal) are rare because they are
   UNGENERATED, not because they are down-scored.** They are *not* productions, so
   for a normal agent in a normal context `admissible_moves` **never emits them**
   — they are absent from the candidate set the Argmax ranks (Part 1 §1a: restricted
   option-space; taboo as non-consideration). Rarity is *structural at generation*,
   not a tuned probability or a low weight. Only when a rare generative condition
   holds (a norm already broken / extreme threat / a legitimated role — the
   legitimacy axis, point 5) does a harm act become *generable at all*; even then it
   is marked and costly. The `Type1NoProduction` outcome (Part 2) is the **safety
   floor** for the case where an act nonetheless reaches the checker — it catches
   and marks it — but the primary win is that the act is never generated, so the
   checker is rarely even consulted.
3. **Inadmissible acts are MARKED as violations when they occur.** The checker's
   `Type1NoProduction` outcome *is* the mark. A committed inadmissible act mints a
   first-class `Violation` (the type already exists in
   `bigville_laws_enforcement`), carrying who/what/against-whom.
4. **Marking triggers graph-legible consequences** — sanction / shame / reputation
   / enforcement — via the machinery bigville already has: the reputation loop
   (badmouth → reputation drop → indirect bond update: Ellickson/Ostrom/Nowak-
   Sigmund horizontal regime) and the constable/council pipeline (Weber vertical
   regime). Graduated sanctions (Ostrom) map onto the existing warn/punish rungs.
   The shame-vs-guilt fork (Tangney) is a first-class branch: guilt → restitution/
   repair (Braithwaite reintegrative), shame → withdrawal/escalation.
5. **A legitimacy axis, not a binary.** Some violence is *sanctioned* — punishment,
   self-defence, feud, war (Weber; Nisbett & Cohen). So an act is not just
   admitted/rejected: it carries **forbidden / permitted / obligatory** under a
   *legitimacy predicate* keyed on authorised-agent, legitimate-target, and
   triggering-condition. The constable's punitive force must itself be **admitted**
   by a legitimacy production (else the enforcer is just another aggressor); a
   feud/honor context can flip an otherwise-inadmissible act to permitted or even
   obligatory. This is a **production with a where-clause over the legitimacy
   frame**, not a new behaviour.

**This orders the drifted rules rather than adding more.** Instead of 15 violence
rules that model an act, its cost, its evidence, its prosecution, and its lethal
route as first-class machinery, violence becomes: *the residual the norm-grammar
refuses to admit* + *a mark* + *the enforcement rules already present*. The
"spending so long considering violence" collapses into the general
admit/mark/sanction loop that also handles theft and betrayal — one mechanism, not
a bespoke subsystem per transgression.

## Two refounding shapes (both presented; choose later)

### Shape (i) — a Γ LAYER over the existing rules (lighter, faster)

Keep the existing conduct rules. Add an **admissibility grammar as a governing
gate** and reclassify violence as a marked inadmissibility, without regenerating
the conduct rules from productions.

- Declare the **admissible conduct** productions (greet/trade/help/gossip/court)
  and the **legitimacy** productions in Γ, so the type vocabulary and the
  norm-grammar exist as data.
- Flip the reserved **`gated: bool`** on the violence/transgression rules
  (`rewrite.rs:15-16`) so *their* effects flow through `check_edge` (or, less
  invasively, have the conduct rules call `is_edge_admissible` /`admissible_moves`
  in their where-clause before firing). An unadmitted act → `Type1NoProduction`
  → the rule mints a `Violation` mark instead of the raw act, and the existing
  reputation + enforcement rules fire on the mark.
- **Where it lands on the generate/gate axis (decisive).** This is the **gate
  model**. The violence rules still *exist and still match every tick* — their
  effects are merely vetoed at the checker. Violence stays **on the menu**: it is
  considered-then-suppressed, cycles are spent, and the model still depicts an agent
  who evaluates harming its neighbours each tick and refrains. It **cannot reach
  "not a candidate."** It is a real safety improvement (unsanctioned harm no longer
  lands) but it does **not** deliver the primary framing above.
- **Trade-offs.** *Pros:* minimal churn; the 15 violence rules mostly survive as
  the *consequence* machinery hanging off the mark; fast to land; low regression
  surface (bigville seeds are `self_load_only`). *Cons:* the gate is *bolted on*,
  not intrinsic — ordinary conduct is still Rules that bypass Γ, so the grammar
  governs only the transgression path; two sources of truth (productions for
  violence-admissibility, rules for everything else); the "admissible acts are
  *generated* by Γ" claim is only half-honoured; **the drift the creator named —
  time spent considering violence — survives, because the option is still
  enumerated and scored**; risk of the gate being another reusable-excuse layer
  (cf. the retracted optional-dep note in `CLAUDE.md` — a governing claim must be
  enumerable, not characterisable).

### Shape (ii) — a from-Γ REFOUNDING (deeper, more faithful to (G,Γ))

Regenerate the conduct layer as **productions of an explicit admissibility
grammar**. Admissible conduct is *what Γ generates*; the rules become the
consequence/dynamics layer only.

- Every ordinary act (greet/trade/help/gossip/court) is a **weighted production**;
  `admissible_moves` **generates** the candidate set an agent *may* do next, and the
  weight is the Boltzmann propensity (Bicchieri's conditional preference becomes the
  weight Term, parameterised by the agent's *empirical + normative expectations*
  read from the graph — reputation, bond state, who-is-watching). Conduct selection
  is the existing weighted-admissibility machinery, not bespoke rules.
- **Violence/theft/betrayal are ABSENT FROM Γ, so they are never generated** — for
  a normal agent `admissible_moves` emits a set that *does not contain them*, the
  Argmax never ranks them, zero cycles are spent, and the violence rule's match set
  is **empty** (the empty-match-set proof applied to conduct — the machinery is
  never enumerated). This is the **grammar model**: pathological acts are
  ungenerated, not scored-and-suppressed. The legitimacy productions
  (punishment/defence/feud) are the *only* productions that admit a harm move, and
  only under their where-clause (authorised role / broken norm / extreme threat) —
  so a harm act is **generable exactly when the rare generative condition holds**,
  and is `Type1NoProduction`-marked + costly if attempted outside it. This makes
  Weber's "legitimate force" literally a production and everything else ungenerable
  by construction.
- Enforcement, reputation, shame/guilt, restitution remain Rules that fire on the
  mark (consequence dynamics are genuinely temporal/stateful — correctly Rules,
  not Γ).
- Uses the **meta-Γ growth** path (`test_gamma_growth_migrated`, `add_production`):
  new norms can be *grown* as productions from observed regularities, and a norm
  can *collapse* (Bicchieri's belief cascade) by a production's where-clause
  (over empirical/normative expectations) going false — norm dynamics fall out of
  Γ being state-dependent, exactly as §1 requires.
- **Where it lands on the generate/gate axis (decisive).** This is the **only shape
  that reaches "not a candidate."** Violence is un-considered because it is
  un-generated — the primary framing above is delivered literally, and it coincides
  with the project's own empty-match-set efficiency win. This is the deciding
  difference between the two shapes.
- **Trade-offs.** *Pros:* faithful to (G,Γ) — conduct is generated, not scripted;
  one mechanism (admit/mark/sanction) subsumes all transgressions; norm emergence
  and collapse are native; **violence is ungenerated for normal agents (zero
  deliberation), not merely down-scored**; the legitimacy axis is first-class.
  *Cons:* larger rewrite of the conduct seeds;
  requires the weight Terms to encode conditional preference well (non-trivial);
  must not regress the measured bigville laws; more upfront design of the
  production set and legitimacy predicate; the conduct-selection loop must be shown
  byte-equivalent or better than the current rule-driven one before the old rules
  retire.

**The decisive argument, stated plainly.** On the axis the creator named — *does
the agent spend cycles considering violence?* — the two shapes are **not
equivalent**. Shape (i) can only ever reach *considered-then-suppressed*: violence
stays in the menu, ranked and vetoed. Shape (ii) is the *only* one that reaches
*not a candidate*: violence is ungenerated, so it is never ranked and never
considered. Because the creator's whole diagnosis is that *time spent considering
violence is itself the drift*, **the from-Γ refounding (ii) is the shape that
actually answers the diagnosis; the Γ-layer (i) mitigates the symptom without
removing it.** This is a genuine argument for (ii), not a toss-up.

**A pragmatic reading (still not the creator's decision to pre-empt):** (i) and
(ii) are the two ends of one path — (i) can be a *first rung* (declare Γ, gate the
transgression path, prove the mark+sanction loop and the enforcement wiring) on the
way to (ii) the *endpoint* (migrate ordinary conduct into productions so violence
becomes ungenerated). That staging mirrors the project's own
"do-it-properly-then-droppable-mirror" and "measure-first / power-the-gate"
standing rules. But (i) is a *stepping stone toward* (ii), **not a substitute for
it** — stopping at (i) leaves the named drift in place. The choice of how far to go
is the creator's.

## Honest cautions (binding on either shape)

- **Do not conflate admissible with moral.** §4 is a structural fact: a Γ can
  admit an oppressive norm (Ullmann-Margalit's norms of partiality; Portes'
  dark-side closure). "Admissible under this village's Γ" means *this society
  generates it*, not *it is good*. Keep the observer's glass-box view able to see
  admitted-but-harmful conduct (surveillance, downward levelling, exclusion) — do
  not let "admissible" read as "fine."
- **Keep the legitimacy dimension.** A binary permit/forbid is refuted by the
  literature. Model forbidden/permitted/obligatory + authorised-agent +
  legitimate-target + triggering-condition. The enforcer's own force must be
  admitted by a legitimacy production, or the model reproduces the very ownerless
  harm the project forbids (`MEMORY.md` "no ownerless harm": every injury owned by
  a decider) — sanctioned violence is still *owned*, just legitimate.
- **Un-default violence; do NOT delete it.** The reframe removes violence from the
  *default* option-set — it does not remove it from the world. It must stay
  **generable** under the rare generative conditions (a norm already broken, extreme
  threat, a legitimated role), or the model can't study when order fails, feud,
  honor-violence, or the state's monopoly breaking down. Rare + marked + generable,
  never impossible. Ablating the norm-grammar (or dropping its expectations below
  threshold) must still let violence through — that is the falsifier that proves Γ
  is load-bearing rather than a hard wall. "Not on the menu for a normal agent in a
  normal context" is the target; "cannot happen" is a bug.
- **Record the self-indictment honestly — WE put violence on the menu.** The drift
  is not abstract: `bigville_viol_act`'s `bv_trigger` computes a `trigger_value`
  (snap-pressure + spite + desperation) against a threshold *for the considering
  agent every tick*, with `bv_refrain` as the disjoint "considered-but-declined"
  arm. That is **evaluate-then-suppress in the seed data itself** — the current
  design literally has every armed agent *consider* violence and then usually
  refrain. The option is permanently on the menu because we placed it there; that
  IS the drift the creator named, and it is why the mere existence of the violence
  subsystem (15 rules, its own trigger calculus) is the symptom. The refounding's
  job is to make `bv_trigger` (and its kin) have an **empty match set for normal
  agents** — not to tune its threshold.
- **Flag the contested literature in the build.** Pinker's decline thesis
  (Cirillo-Taleb fat tails; Ferguson/Fry baselines), MFT's factor structure,
  equilibrium-vs-preference-transformation, and honor-culture origins are all
  contested. Do not encode any of them as ground truth; where a mechanism rests on
  a contested claim, make it a *sweepable parameter*, not a constant (cf. the
  bigville anti-tuning / pre-registration discipline in `MEMORY.md`).
- **A governing claim must be enumerable.** Per the retracted optional-dep note in
  `CLAUDE.md`: if "violence is rare under Γ" becomes a status line, it must be a
  *measured list of admitted vs. marked acts over a run*, never a characterisation
  or a single rate that can be held without being read.
