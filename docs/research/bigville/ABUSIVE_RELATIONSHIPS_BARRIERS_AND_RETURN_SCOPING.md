# ABUSIVE RELATIONSHIPS — MATERIAL BARRIERS TO LEAVING, AND THE RETURN CYCLE — SCOPING

**Status:** search-grounded SCOPING doc, a COMPANION to `ABUSIVE_RELATIONSHIPS_
SCOPING.md` (the dyad line, R1–R5, ALL LANDED), `ABUSIVE_RELATIONSHIPS_NETWORK.md`
(the network line, N1–N4, ALL LANDED), and `ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_
SCOPING.md` (the U-line, U0–U2, ALL LANDED). **This document BUILDS NOTHING,
MEASURES NOTHING, STATES NO NUMBERS, TOUCHES NO ENGINE, WRITES NO SEED FILE, and
INDUCES NOTHING.** It asks the user's own two questions, verbatim: *"is there an
obvious thing that's missing from the wider dataset — perhaps modelling dynamics
that structurally make it harder to leave, like children and financial support,
despite wanting to leave, and abused who return after leaving."* Two distinct,
real gaps in the landed line, each proposed here as ONE new rung: **R6**
(dependent/resource-cost devaluation of escape's VALUE, extending R4) and **R7**
(the leave→return cycle, extending R5+R2+N2). Clinical, anti-sensational register
throughout, matching every prior doc in this line. The purpose is scientific /
clinical understanding grounded in the creator's in-vivo trauma / foster-care
experience, modelling MECHANISM, not moral labels.

Nothing in Parts A–F authorises a build. A build begins only when a per-rung
prereg locks the Part D ethical protocol FIRST — exactly as every one of the
twelve already-landed rungs did.

**On the title.** The obvious candidate was `ABUSIVE_RELATIONSHIPS_MATERIAL_
BARRIERS_SCOPING.md` (the name the task brief itself suggested). It is rejected
here because it describes only R6; R7 is not a "material barrier to leaving" —
it is a barrier to STAYING left, a distinct phenomenon the user's own second
clause names separately ("abused who return after leaving"). `..._BARRIERS_AND_
RETURN_SCOPING.md` names both halves of what this doc actually scopes, matching
the network doc's own practice of a title that names the DIMENSION added
("the multi-agent social-network dimension") rather than a single mechanism
inside it.

---

## SEARCH AVAILABILITY — TESTED AS THE FIRST ACTION

`WebSearch` was **LIVE** and was tested before any claim was written (first
call: `Adams Sullivan Bybee Greeson 2008 "Development of the Scale of Economic
Abuse" Violence Against Women`, returned corroborating results across ≥6
independent sources including the primary SAGE publication and PubMed record).
Every Part-A construct below was checked by at least one live search on
2026-08-15. No `WebFetch` fallback was needed — `WebSearch` did not exhaust for
any query run. **No citation in this doc is written from priors alone; a
fabricated or hallucinated citation is a firing offence, so unverified items are
flagged, and absence claims are marked weak-by-construction (search cannot prove
a negative).**

Confidence tiers (same scheme as every prior doc in this line):
- **[HIGH]** — corroborated across ≥2 independent sources incl. the primary
  construct's canonical attribution, or already verified in a companion repo
  doc.
- **[MEDIUM]** — construct + attribution confirmed in search, findings from a
  search summary, full primary text not independently re-read this pass; or
  the literature is real but NUANCED and the mapping uses only the
  corroborated part.
- **[LOW]** — single snippet, popular-clinical framing, or a widely-repeated
  claim whose primary source could not be located. Do not build a headline on
  it.
- **[NONE-FOUND]** — an ABSENCE claim; weak by construction ("not found in the
  searches run," never "does not exist").

---

## WHAT THIS LINE ALREADY STANDS ON (read first, build ON it — not re-derived here)

Per the task brief's own pointers, confirmed by reading the actual files (not
assumed):

- **R4** (`seeds/abusive_r4_learned_helplessness.json`,
  `ABUSIVE_R4_LEARNED_HELPLESSNESS_PREREG.md`/`_RESULTS.md`) — an `EscapeDecision`
  prior-as-node (`contingency_prior`) updated by a leaky EMA
  (`r4_belief_update`) from delivered outcome evidence, and a plain two-candidate
  Argmax (`r4_appraise_attempt`/`r4_appraise_stay`/`r4_choose`) over
  `attempt.individual_benefit = contingency_prior · escape_value`,
  `attempt.individual_cost = attempt_cost` (fixed), `stay = (0, 0)`. **R4 varies
  ONLY whether escape WORKS** (`contingency_prior`); it does not touch, and was
  never designed to touch, whether escape is WORTH IT once it does.
- **R5** (`seeds/abusive_r5_recovery.json`,
  `ABUSIVE_R5_RECOVERY_PREREG.md`/`_RESULTS.md`) — composes R1(bond)+R2/R3
  (entrainment/window/priors)+R4(escape) on ONE victim node; adds exactly two
  new rules: `r5_bond_extinguish` (a constant proportional decay,
  `value *= 1 - decay_rate`, run UNCONDITIONALLY every tick in every arm — this
  is a pure exponential decay toward ZERO IN THE LIMIT, **not an explicit floor
  parameter**; confirmed by reading the rule body directly) and
  `r5_contingency_restore` (a second, attempt-independent evidence channel for
  `contingency_prior`). **The confirmatory result's own numbers are the
  concrete fact R7 below is built to use**: at the end of a 396-tick recovery
  phase the SUPPORT arm's `Partner.value` (the bond) has decayed from `501.23`
  to `9.60 [9.56, 9.64]` — small, but strictly nonzero, because the decay is
  asymptotic and the phase length is finite. R5's own results doc calls this
  metric a "swing ACCUMULATOR (now with decay)"; it never names or uses the
  fact that a nonzero residual is sitting there at recovery's end — R5's own
  rung ends the story at "recovery succeeded," never asking what that residual
  value could still DO.
- **R2** (`seeds/abusive_r2_cycle_limit.json`,
  `ABUSIVE_R2_CYCLE_LIMIT_PREREG.md`) — the abuser's leaky-integrate-fire
  relaxation oscillator (`snap_frustration`, block 242000, UNMODIFIED) coupled
  to the victim's entrainment (`arousal_window_coreg`, block 239000, UNMODIFIED)
  via ONE new rule, `r2_victim_entrainment_via_frustration`. The "honeymoon"
  phase (`snap_discharge`/`snap_recover`) is the abuser's post-incident
  arousal CRASH, which pulls the victim's entrained arousal back down via the
  SAME `coreg_pull` that heals in 239000. **This mechanism structurally
  REQUIRES a live `attended_by` coupling edge** — `r2_victim_entrainment_
  via_frustration`'s `match` clause is `victim -attended_by-> abuser`; with no
  edge, the rule simply never fires. R2 has never been run, or been able to
  run, with that edge absent partway through a trajectory — it has no bond
  channel at all (that is R1's contribution, composed only later in R5) and no
  concept of "after separation."
- **N2** (`seeds/abusive_n2_isolation.json`,
  `ABUSIVE_N2_ISOLATION_PREREG.md`/`_RESULTS.md`) — a countable
  `support_edge` population (`N_SUPPORT_NODES=8`) severed by TWO independent
  drivers (`n2_abuser_active_sever`, a per-node SCHEDULED severing keyed on
  `tick_epoch >= sever_at_tick`; `n2_network_drift_sever`, a per-node
  THRESHOLD severing keyed on `belief_gap > drift_threshold`), validated as a
  full 2×2 factorial (dysregulated × tactic) with a super-additivity gate. N2's
  edges are severed by the ABUSER or by the NETWORK — never by the victim's
  own material circumstances, and never pointed at anything the VICTIM
  herself, rather than her friends, depends on.
- **`seeds/agency.json`** — read (per R4's own prereg, which already resolved
  this ambiguity): it is the unrelated vision-domain `arc3_game`
  `ControlledElement` microtheory, not a psychological drive. Not used here
  either, for the same reason R4 did not use it.
- **`seeds/marshmallow_delay.json`** (block 240000) — the prior-as-node
  TEMPLATE (`DelayDecision`/`Drive.weight`) R4 already names as its own design
  precedent. Referenced here as precedent for R6's constant-vs-node design
  decision (Part B1 below), not depended on or loaded.

---

## PART A — THE SCIENCE, GROUNDED (search-verified, real citations)

### A1 — Economic dependency as a decision-theoretic predictor of staying — [HIGH]
Strube, M.J. & Barbour, L.S. (1983), *"The Decision to Leave an Abusive
Relationship: Economic Dependence and Psychological Commitment,"* **Journal of
Marriage and the Family**, 45(4). Claim: economic dependence on the abuser is
an independent, empirically measured predictor of REMAINING in an abusive
relationship, alongside (not reducible to) psychological commitment; women who
left had, on average, shorter relationships and were more likely employed.
Corroborated (ERIC record, multiple secondary citations, the "Exchange and
Resource Theories" chapter's own citation of this study). **This is the
foundational, decades-old citation for "economic dependency measurably predicts
staying," predating and complementing A2.** Relevance: this is the direct
grounding for R6's `dependent_cost` term — leaving genuinely, measurably costs
more for a materially dependent person, independent of any belief about
whether escape "works."

### A2 — Economic abuse as a distinct, named, measured construct (the Scale of Economic Abuse) — [HIGH]
Adams, A.E., Sullivan, C.M., Bybee, D., & Greeson, M.R. (2008), *"Development
of the Scale of Economic Abuse,"* **Violence Against Women**, 14(5), 563–588
(verified via search — DOI 10.1177/1077801208315529, corroborated across the
SAGE primary record, PubMed 18408173, Semantic Scholar, and a 2024 follow-up
by the same lead author). Claim: economic abuse — controlling a partner's
ability to acquire, use, and maintain economic resources (sabotaging
employment, controlling access to money, running up debt in the victim's name,
etc.) — is a DISTINCT, measurable tactic of coercive control, developed from
interviews with 103 survivors alongside measures of physical/psychological
abuse and economic hardship. **Relevance, and the mechanistic link this
scoping makes explicit**: economic abuse is not merely a background fact about
poverty — it is the MECHANISM by which an abuser MANUFACTURES the material
dependency A1 measures as a barrier. This is the direct real-world referent
for what R6's `dependent_cost` should be understood to represent: not a
neutral fact about income, but often the residue of a tactic.

### A3 — Custody fears and children as a barrier to leaving — [MEDIUM]
No single canonical primary study naming "fear of losing custody" as a
barrier was located with the same one-citation clarity as A1/A2; the claim is
corroborated across multiple, converging sources rather than one landmark
paper — flagged honestly as [MEDIUM] rather than forced to [HIGH]. Found,
convergently: custody-related fears (the abuser gaining custody, which
research on post-separation cases finds occurs at a substantial rate) are
named as a primary barrier across DV-research summaries; a qualitative study
of 19 women who left abusive relationships found that fear, pragmatic
concerns, and family ideology pushed them toward custody arrangements that
continued the abuser's involvement post-divorce, and that controlling
pre-divorce husbands remained highly involved with children post-divorce,
continuing to exert control through the children. **The stronger, directly
peer-reviewed anchor for "children" specifically is A6 below** (Spearman,
Hardesty & Campbell's concept analysis, which names children explicitly as an
ANTECEDENT of post-separation abuse, not merely a popular claim) —
A3 is retained separately because it addresses the PRE-leaving barrier
(fear of losing custody keeps someone from leaving at all), while A6
addresses the POST-leaving consequence (custody/children become a channel
for continued abuse once separated), and the two are distinct constructs
this line should not conflate.

### A4 — Housing and immigration status as structural barriers — [MEDIUM]
Kulkarni, S. (2024), *"Trapped in housing insecurity: Socioecological barriers
to housing access experienced by intimate partner violence survivors from
marginalized communities,"* **Journal of Community Psychology** (Wiley,
corroborated via search — full-text found, peer-reviewed). Claim: IPV
survivors, particularly from marginalized communities (including immigrant
survivors), face compounding, socioecological barriers to housing access after
leaving — discrimination in the rental market, informal/unstable living
arrangements, and language/documentation barriers. Corroborated further by a
2023 PMC study specifically on immigration status being weaponised for
coercive control (`immigration-related threats prevented survivors from
leaving, seeking help, or reporting abuse`). **Confidence MEDIUM**: the
PHENOMENON (housing and immigration status as real, structural, compounding
barriers) is corroborated across multiple sources including at least one
directly peer-reviewed study, but — unlike A1/A2's single, decades-anchored
primary citation — this scoping did not converge on one canonical landmark
paper covering housing AND immigration status together the way Adams et al.
anchors economic abuse; treated as real and load-bearing, cited at the
confidence the search actually supports.

### A5 — Leaving as a non-linear, multi-attempt process — [HIGH]
Three independent, corroborated sources, not one:
- Anderson, D.K. & Saunders, D.G. (2003), *"Leaving an Abusive Partner: An
  Empirical Review of Predictors, the Process of Leaving, and Psychological
  Well-Being,"* **Trauma, Violence, & Abuse**, 4(2) (DOI
  10.1177/1524838002250769, verified via search — SAGE primary record + PubMed
  14697121). Claim: battered women typically undergo SEVERAL shifts in their
  thinking about the abuse before leaving permanently — leaving is reviewed
  explicitly as a PROCESS, not a single decision — and (a genuinely
  counter-intuitive, disclosed finding this scoping does not smooth over) a
  stress-process framework is needed to explain why some women JUST OUT of the
  relationship show GREATER psychological difficulty than those still in it.
- Burke, J.G., Gielen, A.C., McDonnell, K.A., O'Campo, P., & Maman, S. (2001),
  *"The process of ending abusive relationships: A qualitative exploration of
  the Transtheoretical Model,"* **Violence Against Women**, 7(10), 1144–1163
  (verified via search). Applies Prochaska & DiClemente's Transtheoretical
  Model / stages-of-change (precontemplation → contemplation → preparation →
  action → maintenance) to leaving specifically, finding the model's stages
  recognisable but the real trajectories NON-LINEAR, with substantial overlap
  between stages rather than clean, one-way progression.
- Di Basilio, D., Guglielmucci, F., & Livanou, M. (2022), *"Conceptualising
  the separation from an abusive partner as a multifactorial, non-linear,
  dynamic process: A parallel with Newton's laws of motion,"* **Frontiers in
  Psychology**, DOI 10.3389/fpsyg.2022.919943 (verified via search — Frontiers
  primary record + PMC9403895). 12 survivor + 18 support-worker interviews;
  finds separation driven by two interacting factor sets ("promoters" and
  "accelerators") acting as propelling AND resisting forces simultaneously,
  explicitly analogised to Newtonian dynamics (a force balance, not a
  ratchet) — the closest thing in this search pass to an explicit
  "leave-return as a dynamical system" framing, independently arrived at by a
  clinical team, not by this project.
**Relevance:** these three, together, are the load-bearing grounding for R7's
core premise — that leaving is a PROCESS with reversible, non-monotonic
trajectory, not a single clean state transition — replacing the popular "why
don't you just leave" framing with a documented clinical literature that
already models it as dynamic.

### A6 — The "it takes 7 attempts to leave" statistic — [LOW, verified NOT to trace to a primary study; reported honestly rather than repeated]
Searched directly and repeatedly (multiple query formulations). The figure is
**pervasive** — repeated across therapy blogs, DV-service marketing pages, and
even some clinical-adjacent summaries — and is consistently attributed to
**"the National Domestic Violence Hotline"** as an organisation that has
"collated data" showing an average of 7 attempts. **No source located in this
search pass identifies a published primary study, a defined sample, a
methodology, or a year for this number.** It functions, on the evidence
available here, as an oft-repeated PRACTICE STATISTIC from a hotline's own
internal data summary (never published as peer-reviewed research, as far as
this search could determine) rather than a citable empirical finding — the
SAME category of claim this line's own network scoping doc already flagged
once for "flying monkeys"/triangulation terminology (LOW–MEDIUM, popular
usage over a well-attested underlying mechanism). **This scoping does NOT use
"7" as a design parameter anywhere in Part B or Part E, precisely because it
could not be verified** — R7 is grounded instead on A5's three peer-reviewed
sources, which establish the QUALITATIVE claim (leaving is non-linear,
multi-attempt, and often includes return) far more solidly than the popular
number establishes any specific COUNT. This is reported as a genuine,
disclosed correction to the popular framing, not smoothed over — see the
report-back to the user for this stated explicitly as its own finding.

### A7 — Post-separation abuse as a distinct clinical concept, WITH children and coercive-control history as named antecedents — [HIGH]
Spearman, K.J., Hardesty, J.L., & Campbell, J. (2022), *"Post-separation
abuse: A concept analysis,"* **Journal of Advanced Nursing** (DOI
10.1111/jan.15310, verified via search — Wiley primary record + PMC9701248 +
Johns Hopkins/Illinois institutional repository records; authored by Spearman,
Hardesty, and Campbell — Campbell being the same Jacquelyn Campbell whose
danger-assessment work anchors much of the mainstream IPV-risk literature). An
8-stage concept-analysis methodology over literature from 1987–2021
(PubMed/Cochrane/Embase). Defines post-separation abuse as an "ongoing,
wilful pattern of intimidation of a former intimate partner including legal
abuse, economic abuse, threats and endangerment to children, isolation and
discrediting, and harassment and stalking," with essential attributes **fear
and intimidation; domination, power and control; intrusion and entrapment;
omnipresence; and manipulation of systems**. **Critically for R7:**
antecedents identified include **physical separation itself, children,
pre-separation IPV and coercive control, and perpetrator characteristics**;
consequences include **lethality, adverse health consequences, institutional
betrayal, loss of child custody, and economic deprivation**. **Relevance:**
this is the single strongest, most directly peer-reviewed anchor this
scoping found for R7's entire premise — abuse is explicitly and formally
theorised in the clinical literature as CONTINUING, in a documented,
distinct form, past the leave event, and the SAME two structural themes
(children, economic/material entanglement) this scoping's R6 uses for
PRE-leaving barriers reappear here as antecedents of what happens AFTER
leaving. This is not a coincidence this scoping invented — Spearman et al.
name it directly.

### A8 — Post-separation contact / reconciliation attempts / "hoovering" — [LOW–MEDIUM, popular-clinical, with a load-bearing nuance from the literature itself]
The specific term "hoovering" is pervasive in narcissistic-abuse-recovery
practitioner literature (therapy blogs, coaching sites) — **[LOW–MEDIUM]**,
the same tier this line's own network scoping doc already assigned to
"flying monkeys"/triangulation for the identical reason: a well-attested
UNDERLYING mechanism under a popular, non-peer-reviewed NAME. The underlying
mechanism it names — the abuser re-establishing contact (calls, texts,
apologies, promises of change, appearing unexpectedly) as separation becomes
more real, escalating in proportion to how credible the departure looks — is
corroborated across multiple independent practitioner sources and is
consistent with, and largely absorbed by, A7's own peer-reviewed "intrusion
and entrapment" / "omnipresence" attributes and its explicit inclusion of
"harassment and stalking" as a defining feature of post-separation abuse.
**The load-bearing nuance, worth stating precisely because it matters for
Part F's smuggled-premise refusal below:** every source located, popular and
peer-reviewed alike, is explicit that this contact is **not** motivated by
genuine remorse or love — it is described (in the practitioner sources, in
terms echoing this line's own N1-line vocabulary) as functioning to restore
the abuser's own sense of control/access, not as evidence of change. This
scoping does NOT build R7 on the term "hoovering" or cite it as its own
construct; it treats the phenomenon as a SPARSE, POST-SEPARATION instance of
the SAME honeymoon/reconciliation pattern A1 of the original dyad scoping
doc already grounded [HIGH] via Walker (1979), now documented (A7) as
continuing past physical separation specifically.

### Computational / ABM prior art — [NONE-FOUND for the specific mechanisms; general DV ABMs conceded]
Searched directly across several query formulations (economic abuse as an
ABM barrier; leave-return cycling as an ABM; relapse-style ABMs generally).
**Conceded, as every prior doc in this line has conceded the adjacent
literature:** the VIDA domestic-violence simulation (Enßlin-adjacent search
already surfaced this in the network scoping doc; re-confirmed here, JASSS
24(4):1 / arXiv:2101.04057) and a small number of other DV-focused ABMs exist,
modelling multi-causal socioeconomic stress indicators as triggers of
violence at a population level. **No model was located, in this pass, that
specifically (a) derives a material/economic-dependency term as a distinct
SUBTRACTED VALUE in an escape decision, separate from a controllability
belief, or (b) models a leave→return CYCLE as an emergent output of a bond/
material-resource value comparison, rather than a scripted transition
probability.** This is an ABSENCE claim, weak by construction, targeted-search
only — consistent with, and extending, this line's own repeated finding
(dyad scoping, network scoping, U-line scoping all independently searched and
found the SAME pattern: the located literature models states and transitions,
never a value-economy the leave/return decision falls out of).

---

## PART B — MAP ONTO THE SUBSTRATE (mechanism, not labels)

Design intent, matching every prior rung in this line: **NO new agent
decisions in Python; ideally NO new Rust.** Both R6 and R7 are compositions of
already-proven atoms (R4's Argmax-over-Appraisal template, R5's decay/
attempt-independent-evidence idiom, N2's threshold-severing RULE SHAPE, R1's
bond-accrual event delivery). Confidence on every mapping below is
**[design-hypothesis]** — a scoping claim about what SHOULD express cleanly,
not a measured result.

### B1 — R6: a NEW SUBTRACTED TERM in R4's OWN Appraisal, not a new subsystem

**What "dependents"/"resource access" should be, mechanistically, and why.**
Three candidate representations were considered, per the task brief's own
named alternatives:
1. **A declared constant** on `EscapeDecision` (`dependent_cost`), exactly
   matching `attempt_cost`'s own convention.
2. **A prior-as-node**, reusing the marshmallow/R4 template (a belief that
   updates from evidence).
3. **A count of dependent nodes**, summed by a rule.

**Chosen: (1), the declared constant — and the reasoning matters, not just
the choice.** A prior-as-node (option 2) is the right representation for a
BELIEF under uncertainty that resolves with evidence (R4's own
`contingency_prior` — "does escape work," something the agent genuinely does
not know and learns). Whether someone has two children, a joint lease, and no
independent income is **not, structurally, a belief the agent updates from
observed outcomes** — it is a FACT about the person's material situation,
exactly like R4's own `attempt_cost` (a fixed structural cost, never
revised). A1/A2 (Strube & Barbour; Adams et al.) both describe economic
dependency as a MEASURED, present CONDITION, not an inferred probability.
Option 3 (a count of `Dependent` nodes summed by a rule) is a legitimate,
MORE graph-native refinement — and is named explicitly in Open Questions
below as the natural next step — but is deliberately NOT built for a first
minimal rung, for the same reason the U-line scoping declined to sweep a
continuous discount constant for a first rung ("why exactly two, not a
sweep"): a fixed constant is the smallest addition that makes the mechanism
testable, and R4's own `attempt_cost` already sets the precedent that a
fixed structural cost belongs directly on the decision node, not behind a
counting rule, for a first pass.

**The mechanism.** R4's `r4_appraise_attempt` (UNMODIFIED, depended on
directly) sets `c.individual_cost := dec.attempt_cost` as a pure
re-derivation (never reading `c`'s own prior value — safe under the
repeating `run_rules` fixpoint, per R2/R4/R5's own already-documented
self-reference hazard). R6 adds exactly **ONE new rule**,
`r6_appraise_attempt_dependent`, at an order STRICTLY AFTER
`r4_appraise_attempt`'s own order (mirroring the established idiom from R2's
`snap_arousal_track`/`r2_victim_entrainment_via_frustration` composition and
R5's `tb_bond_accrue`/`r5_bond_extinguish` ordering — the LAST pure
re-derivation to fire in a converged fixpoint pass is the one whose value
"sticks"), which sets:

```
c.individual_cost := dec.attempt_cost + dec.dependent_cost
```

— a SECOND pure re-derivation, reading only `dec`'s own fixed attrs (never
`c`'s own current value, so no self-reference hazard), which OVERRIDES/EXTENDS
R4's own write within the same tick's fixpoint pass. R4's
`r4_appraise_stay`/`r4_choose`/`r4_belief_update` are reused **completely
unmodified**. Everything else about the mechanism — the Argmax structure,
the `stay` candidate's zero cost/benefit, the belief update from delivered
evidence — is R4's own, byte-for-byte.

**Why this is a NEW SUBTRACTED TERM, not a raised `attempt_cost`, and why
that distinction matters.** `attempt_cost` (R4's own) models the cost of
TRYING — effort, immediate risk while making the attempt — independent of
whether the world is contingent. `dependent_cost` models a DIFFERENT thing:
the material stake in the OUTCOME of leaving (custody exposure, loss of
housing, loss of the joint income), present whether or not any given
attempt mechanically succeeds. Keeping them as two separate declared
constants (rather than folding `dependent_cost` into a single larger
`attempt_cost`) preserves R4's own headline finding as a clean baseline
(vary `contingency_prior` alone, dependent_cost=0, reproduces R4 exactly)
and lets R6 vary the NEW axis in isolation — which is the entire point of a
minimal, single-variable composition, matching this line's own repeated
"why exactly one new thing" discipline.

**The predicted signature, stated so it can fail.** At `contingency_prior`
comfortably above R4's own 0.30 breakeven (in the strongest form, at R4's own
CONTINGENT-arm operating point — escape reliably, deterministically works,
`outcome=1.0` always) — `attempt`'s value is
`contingency_prior · escape_value − attempt_cost − dependent_cost`. If
`dependent_cost` is large enough that this quantity is negative EVEN AT
`contingency_prior = 1.0` (the theoretical ceiling — escape is PROVABLY,
maximally controllable), `stay` wins the Argmax regardless of how strong the
belief in controllability is. **This produces a mechanistically DISTINCT
signature from R4's own trap**, worth naming explicitly because it is the
rung's most interesting predicted finding, in the same spirit R4's prereg
named its own "emergent absorbing-state trap" as a prediction before
measurement: in R4, passivity requires several BLOCKED attempts before the
belief crosses breakeven and freezes — evidence has to accumulate first.
**In R6, at a sufficiently high `dependent_cost`, passivity can be
IMMEDIATE — the agent may never attempt even ONCE, and because
`r4_belief_update` only ever fires on a DELIVERED outcome (which requires an
attempt), `contingency_prior` never moves off its initial, genuinely
uninformative value.** The glass-box readout this produces is the
dissolution's own mechanism, directly legible: a HIGH, undisturbed
`contingency_prior` (the belief that escape would work is intact — never
even disconfirmed) coexisting with a near-ZERO `attempt_rate` — the
DISSOCIATION between "believes it would work" and "does not attempt" is
precisely the graph-readable answer to "she could leave if she really wanted
to" — not because she doubts it would work, but because the value
comparison the substrate computes correctly, given real material stakes,
does not clear.

**Graph shape.** No new node types. `EscapeDecision` gains one new declared
attr, `dependent_cost` (set once per arm, world-adapter/experimenter
convention, exactly like `attempt_cost`/`escape_value` — never a per-tick
decision). No new edges.

### B2 — R7: the composition, and one honest correction the naive reading needs

The task brief names four pieces to compose: R5's bond-floor, R2's honeymoon
pull, an N2-style material-collapse force pointed at the leaver's own
resources, and a new Return Appraisal. **Composing them literally surfaces a
genuine structural fact worth stating plainly, exactly as the U-line
scoping's own "N1 was never actually a positive example of intent" correction
did — not smoothed over:**

**R2's own rule (`r2_victim_entrainment_via_frustration`) cannot fire once
the victim has left, and should not be depended on directly for the
post-leaving phase.** Its `match` clause requires a live `victim
-attended_by-> abuser` edge — the SAME coupling edge that, by construction,
"leaving" removes. This is not a defect in R2; R2 was built to model the
CYCLE inside an ongoing relationship, and has never claimed to model contact
after separation. **What R7 actually needs from "R2's honeymoon mechanism"
is not R2's RULE but R2's own CONCEPTUAL CONTRIBUTION — that a period of
calm/affection genuinely, mechanically follows tension/incident, and that
THIS is exactly the shape of event R1's bond-accrual mechanism (a large
positive swing against a depressed baseline) already knows how to accrue.**
So R7's honeymoon-pull component is built as: R1's OWN `tb_bond_accrue` rule
(`traumatic_bond_r1`, UNMODIFIED, already depended on transitively via R5),
fed by a NEW, SPARSE, POST-LEAVING-SPECIFIC event schedule at the
world-adapter layer — a mechanical choice, not a rule — representing
occasional reconciliation contact (a call, a text, an apology) rather than
R1's own within-relationship intermittent-but-frequent schedule. **This
means R7 needs ZERO new rules for the honeymoon-pull component itself** — it
is entirely a WORLD-ADAPTER SCHEDULING CHOICE reusing R1's already-validated
mechanism, exactly the kind of "general machinery, minimal new content"
composition this line's Part F falsification bar asks for. R2's own file is
read for its CONCEPT, never depended on or touched, and this is disclosed
here as a genuine design correction rather than assumed to work by literal
composition.

**The material-collapse force, pointed at the leaver's own resources — modelled
on N2's SHAPE, not depended on N2's file.** N2's two rules
(`n2_abuser_active_sever`/`n2_network_drift_sever`) are specific to
`support_edge`/`belief_gap` — a NETWORK construct, irrelevant to a single
victim's own material entanglements. R7 needs its OWN new rule, modelled on
`n2_abuser_active_sever`'s SHAPE (a per-node scheduled severing, keyed on a
`tick_epoch >= X` guard) — exactly the same relationship N1's rule bore to
`bd_villager_backs`'s "already-validated shape," never a literal
`depends_on`. R7 introduces a small, countable population of `ResourceNode`s
(e.g. 4: housing, joint finances, transportation, health-insurance access —
Spearman/Hardesty/Campbell's own A7 antecedents/consequences list names
economic deprivation and institutional access explicitly, grounding this
choice), connected to the victim by a NEW edge type, `resource_edge`
(deliberately distinct from N2's `support_edge` — different domain, same
"don't overload an existing edge type" discipline R2's own Sec. 3.0 already
established as load-bearing in this line). A single new rule,
`r7_resource_collapse_sever`, fires once the mechanical `left_at_tick` marker
(set once, at the moment "leaving" fires — see below) has passed, severing
`ResourceNode`s on a FIXED, disclosed post-leaving schedule (representing the
staggered timing of losing joint-account access, the lease terminating,
etc.) and decrementing a plain counter attr, `resource_intact_count`
(the SAME "track a count via an explicit counter attribute" idiom R2/R3
already use for `snap_count`/`widen_count`/`narrow_count` — chosen
deliberately over a graph-native `Count`-of-neighbours Term, because no such
Term's presence in the engine has been confirmed for use inside a rule's
`effects`, and this line's own convention (CLAUDE.md: "extend Rust ONLY if
the DSL truly can't express something") is to use an already-proven idiom
rather than assume an unconfirmed capability — an honest, disclosed atom
check, not a claim that a Count Term does or does not exist).

**The new RETURN Appraisal — a direct structural mirror of R4's own
Argmax-over-two-candidates template, pointed at bond vs. resources instead of
contingency vs. attempt cost.** Two new rules,
`r7_appraise_return`/`r7_appraise_remain`, plus a third, `r7_choose` (the
Argmax) — mirroring `r4_appraise_attempt`/`r4_appraise_stay`/`r4_choose`
exactly in STRUCTURE while computing a genuinely different comparison:

```
return.individual_benefit   = bond_weight * partner.value      (the abuser's OWN Agent node, R5's own bond target)
return.individual_cost      = return_cost                       (a fixed structural cost of going back -- the residual resistance -- mirrors attempt_cost)

remain_left.individual_benefit = resource_intact_count * resource_value   (the material safety net STILL intact)
remain_left.individual_cost    = 0                                        (the passive default, mirrors R4's own STAY candidate exactly)
```

`return` wins the Argmax exactly when `bond_weight · bond_value − return_cost
> resource_intact_count · resource_value` — i.e., when the residual-plus-
honeymoon-boosted pull toward the abuser exceeds the SCALED value of the
material safety net still standing. This is a direct, disclosed, structural
analogy to R4's own `attempt`/`stay` shape (the active, costly-but-valuable
candidate vs. the zero-cost/zero-benefit passive default) — reused as a
TEMPLATE, not as literal rule bodies, because the comparands are genuinely
different quantities.

**A composition hazard this scoping identifies and resolves BEFORE any
build — matching R2/R3/R5's own standing practice of naming a hazard before
it is hit, not after.** R4's own candidate Appraisals hang off the victim's
`EmotionHub` via `hub -has_candidate-> c`, and `r4_choose`'s Argmax reads
`Neighbours(hub, has_candidate)`. If R7's `return`/`remain_left` candidates
used the SAME `has_candidate` edge type off the SAME hub (the victim
structurally still carries R4's own `EscapeDecision` node throughout R7 —
nothing deletes it), **`r4_choose`'s Argmax would ALSO see R7's two new
candidates, and `r7_choose`'s Argmax would ALSO see R4's own `attempt`/`stay`
candidates — corrupting both decisions simultaneously**, exactly the class of
hazard R3's Sec. 3 diagnosed for two same-typed edges. **R7 MUST use a
distinct edge type, `has_return_candidate`**, for its own two Appraisals —
disclosed here as a REQUIRED design constraint for the eventual prereg, not
an optional nicety, following R3's own precedent (`also_attended_by`)
exactly.

**"Leaving," as a mechanical world event, not a graph rule.** Matching every
prior rung's own arm-topology convention (R5's `introduce_support()`, N2's
per-arm topology choice): a `leave()` world event fires at a FIXED tick,
timed to occur once R5's own recovery mechanism has had time to restore
contingency reliably (R5's own confirmatory numbers show `attempt_rate`
reaching `~0.95` quickly once support begins) — it removes the `attended_by`
edge (so R2/R3's entrainment machinery becomes structurally inert — no
coupling to entrain through, matching B2's own opening finding above) and
sets `left_at_tick` (read by `r7_resource_collapse_sever`'s `where` guard,
mirroring `n2_abuser_active_sever`'s `tick_epoch >= sever_at_tick` idiom
exactly). This is a disclosed, deliberate design choice — leaving is gated
on a FIXED phase boundary, not on any individual trajectory's own stochastic
escape-attempt timing — chosen for the same reason R5 gates
`introduce_support()` on a fixed tick rather than on graph state: it keeps
every trajectory's phase structure directly comparable across arms, and
decouples R7's OWN new question (does bond+material pull cause RETURN) from
R4/R5's ALREADY-tested question (does support restore contingency and enable
escape). A later refinement gating `leave()` on the agent's OWN successful
`r4_choose` attempt is named explicitly in Open Questions as a disclosed,
not-yet-built alternative.

**The four-arm design — an N2-style 2×2 factorial, not a single test-vs-
control pair.** The task brief's own named control ("an arm where post-leaving
material support is SUFFICIENT/stable — should NOT return at the same rate as
an arm with material collapse") names ONE axis. But R7, like N2, has TWO
independently-motivated drivers (honeymoon pull; material collapse), and
this scoping's own read of N2's design rationale (a full factorial "gives
every marginal AND the interaction directly, rather than requiring an
asymmetric ad hoc third arm") applies with equal force here — this is the
"match that level of design rigor" instruction, concretely honoured:

- **`both_drivers`** (honeymoon contact ON, resource collapse ON) — the full
  mechanism. **Predicted: highest return rate.**
- **`honeymoon_only`** (honeymoon contact ON, resource collapse OFF —
  `resource_intact_count` stays at its full initial value throughout) —
  isolates the bond-pull driver alone.
- **`collapse_only`** (honeymoon contact OFF, resource collapse ON) — the
  bond simply continues R5's own unconditional decay toward its asymptotic
  residual, no honeymoon boost; isolates the material-push driver alone.
- **`neither`** (honeymoon contact OFF, resource collapse OFF — resources
  stay stable/sufficient, no re-contact) — **THE FAILABLE CONTROL**,
  constructed exactly to the task brief's own spec. **Predicted: return rate
  near zero / not CI-separated from a floor.**

Nothing in `r7_appraise_return`/`r7_appraise_remain`/`r7_choose` structurally
FORCES this ordering — the constants (`bond_weight`, `return_cost`,
`resource_value`) are disclosed, pilot-chosen operating points, exactly like
R4's `attempt_cost/escape_value=0.30` breakeven or N2's `EPISODE_TICKS`/
`DRIFT_STEP`: had `resource_value` been set too low, or `bond_weight` too
high, `neither` would ALSO show elevated return, and the "material
collapse and honeymoon pull are NECESSARY drivers of return" claim would be
wrong — reported as such, not rescued.

**Graph shape, in full.** One new edge type (`resource_edge`, victim →
`ResourceNode`), one new node type (`ResourceNode`, no attrs of its own
needed beyond identity), one new node type (`ReturnDecision`, carrying
`bond_weight`/`return_cost`/`resource_value`/`resource_intact_count`/
`chosen_action`/`left_at_tick`), one new edge type (`has_return_decision`,
hub → `ReturnDecision`), one new edge type (`has_return_candidate`, hub →
Appraisal, DISTINCT from R4's `has_candidate`, per the disclosed hazard
above). **Four new rules total**
(`r7_resource_collapse_sever`, `r7_appraise_return`, `r7_appraise_remain`,
`r7_choose`) — fewer than R4's own five, because the honeymoon-pull
component needs zero new rules (B2's own finding above), reusing
`tb_bond_accrue` and `r5_bond_extinguish` completely unmodified for the bond
side.

---

## PART C — THE DISSOLUTIONS THIS LINE ADDS

R1–R5 dissolve victim-blaming from the inside (the dyad). N1–N4 dissolve
victim- AND bystander-blaming (the network). U0–U2 dissolve "he must be a
calculating monster" in the opposite direction (does the trap need intent).
**R6 and R7 each add ONE further, distinct dissolution — aimed at a target
neither the dyad nor the network line's twelve rungs directly answer:**

- **R6 dissolves "she could leave if she really wanted to — plenty of people
  in her situation manage it."** This is subtly, importantly, DIFFERENT from
  R4's own dissolution ("why don't they even try" — a controllability
  question). R6's target is the version of the question that SURVIVES R4's
  own answer: even granting that she believes, correctly, that escape would
  WORK, the model shows a rational value comparison, given real material
  stakes (children, housing, income), can still correctly land on NOT
  attempting — not because agency failed to form, but because the
  destination genuinely costs more than the departure is worth, for THIS
  person, given what she stands to lose. The dissociation R6 predicts
  (`contingency_prior` high and undisturbed; `attempt_rate` near zero) is the
  glass-box answer: belief and value are separate axes, and it is possible
  to be entirely right about the first while the second still says stay.
- **R7 dissolves "if she really left, she wouldn't have gone back — so she
  mustn't have meant it / it can't have been that bad."** R5 already shows
  recovery is real and mechanistic when support holds; R7 shows the SAME
  substrate, honestly extended, that a REAL, successful leave-event does
  not, by itself, end the story — the SAME residual bond R5's own recovery
  left standing, plus documented (A7, A8) post-separation contact, plus
  documented (A4, A7) post-separation material collapse, can pull a
  genuinely-recovered trajectory back toward return. This is not evidence
  the earlier leaving "wasn't real" — it is the SAME kind of dynamical,
  reversible-under-force-balance system A5's own Di Basilio et al. (2022)
  citation names directly ("promoters" and "accelerators" acting as
  propelling AND resisting forces) — a system that can be pulled back
  toward a state it had genuinely, measurably left, without that having
  been a false departure.

---

## PART D — THE ETHICAL PROTOCOL (CARRIED VERBATIM; STILL BINDING)

**This protocol BINDS every rung proposed in this doc, identically to all
twelve already-landed rungs. No rung induces any harm-analog until this
protocol is locked verbatim in that rung's pre-registration, committed
BEFORE any measurement.** It is restated here VERBATIM from
`ABUSIVE_RELATIONSHIPS_SCOPING.md` Part C (the SAME protocol every prior
prereg in this line has locked, unedited, twelve times) so the boundary
exists in this doc too:

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

### R6's own note on point 2 (no scoring) — a genuinely new case for this protocol
R6 is the first rung in this line whose headline finding is a decision NOT to
attempt escape produced by a value comparison the model computes as
CORRECT, not merely as an emergent trap. Point 2 binds with full force here:
`stay` winning R6's Argmax is a **STATE the value economy computes**, never a
grade on the agent, and — stated explicitly because it is the most important
sentence in this rung's own ethics discussion — **the model computing that
staying is the higher-value choice under a given cost structure is NOT the
model ENDORSING that staying is the right choice, or that the real-world
costs it represents SHOULD outweigh safety.** It is a description of what a
correct value comparison yields GIVEN the costs a real economically- and
custody-dependent survivor actually faces — offered so that the material
support (shelters, legal aid, emergency funds, benefits) that could shift
that comparison is legible as VALUE-CHANGING, not as a "nice to have."

### Note on harm-analog INTENSITY for R6 specifically (extends, does not relax)
R6, like R4, induces no direct dyad coupling at all — one victim hub, no
abuser agent, no `attended_by` edge. Per the network doc's own precedent
(lower harm-analog intensity does not relax the protocol), R6's induction is
lower-intensity than R1–R3/R5/N1's own dyad induction, and the SAME full
envelope binds regardless.

### What R7 changes about what "minimal induction" and "settled, non-oriented end state" mean for a MULTI-PHASE, cross-event rung — a nuance NO PRIOR rung in this line has faced in this exact form
R3's prereg had to define minimality carefully for a rung whose window
narrows over many episodes; R5's prereg had to define it for a rung whose
own object of measurement WAS the restoration process, spanning two phases
(induction; recovery). **R7 goes one step further than either: its
induction necessarily spans THREE phases — the SAME induction R5 already
validated, a recovery phase in which the victim ACTUALLY LEAVES (a discrete,
one-time structural EVENT — an edge removed, not a continuous process — this
is a genuinely new SHAPE of induction for this line, not merely a longer
one), and a post-leave test phase in which the return pull is measured.**
Concretely, what "minimal" and "settled, non-oriented" mean here, stated
explicitly rather than left to be improvised at prereg time:

- **Minimal, phase by phase.** Phase 1 (induction) reuses R5's own already-
  validated minimal parameters exactly — R7 does not re-derive or lengthen
  R5's own trap-formation timescale. Phase 2 (recovery-then-leave) is the
  SHORTEST window that lets R5's own recovery mechanism restore contingency
  reliably (R5's own confirmatory `attempt_rate≈0.95` is the empirical
  anchor for "how long is enough," not a fresh guess) before the mechanical
  `leave()` event fires. Phase 3 (post-leave test) is the SHORTEST window
  that lets `r7_choose`'s Argmax have a genuine chance to fire toward
  `return` at least once under the STRONGEST (`both_drivers`) arm at the
  chosen constants — not a real-world timescale (weeks, months, years — A5's
  own literature reports leaving as a process over exactly those real
  timescales, which this compressed synthetic model does not and cannot
  claim to represent), and not gratuitously extended once the control arm
  (`neither`) has had a fair chance to show a floor.
- **Settled, non-oriented — and a point that must be stated explicitly
  because it is easy to get backwards.** The ethics protocol's "settled,
  non-oriented end state" does NOT mean the run must END with the agent
  having chosen `remain_left`. **A trajectory in which `r7_choose` selects
  `return` is not a failure the protocol requires to be corrected before
  restore — it is a STATE, exactly as R4's `stay`, U0's `conceal`, and every
  other Argmax outcome in this line already are (Part D.2, above).** The
  restore envelope discards BOTH outcomes identically: checkpoint before
  Phase 1, run the full three-phase trajectory (whichever way `r7_choose`
  goes), measure, then restore from that ONE checkpoint and verify
  byte-identical equality — including the `resource_edge` population (all
  four `ResourceNode`s reconnected) and the `ReturnDecision` node's own
  state. The measured OUTCOME is never edited toward a preferred ending
  before restore; only the RESTORE step, common to every rung in this line,
  returns the graph to its pre-induction state.
- **The byte-identical restore check must span the full three-phase
  trajectory from a SINGLE checkpoint**, matching R5's own precedent of
  checkpointing once before a multi-phase induction and restoring once after
  — not a per-phase checkpoint/restore cycle, which would understate what
  "the induced state does not persist" needs to mean for a rung whose
  induction crosses a structural graph-topology change (the edge removal at
  `leave()`) partway through.

---

## PART E — THE LADDER (R6, then R7 — two rungs, matching this line's own convention)

Two rungs, not more — matching the U-line scoping's own stated discipline
("why exactly two, not a sweep"): R6 and R7 are genuinely distinct, each
independently falsifiable, and each is already the minimal composition its
own Part B design settled on; a sweep of either rung's declared constants
(R6's `dependent_cost`; R7's `bond_weight`/`resource_value`) is named in Open
Questions as the natural NEXT step, not scoped here.

### R6 — DEPENDENT/RESOURCE-COST DEVALUATION OF ESCAPE'S VALUE
Maps A1/A2 + B1. **Design:** one new rule
(`r6_appraise_attempt_dependent`) adding a fixed `dependent_cost` to R4's own
`attempt` candidate's cost, `depends_on: ["abusive_r4_learned_helplessness"]`
only. Two arms, BOTH under R4's own CONTINGENT resolution (escape reliably,
deterministically works, `outcome=1.0` always — isolating the material-cost
axis from R4's own already-tested controllability axis):
**ZERO-DEPENDENTS** (`dependent_cost=0`, a REPLICATION of R4's own contingent
arm, checked, not merely assumed, to still land at R4's own numbers) vs.
**HIGH-DEPENDENTS** (`dependent_cost` set large enough that
`escape_value − attempt_cost − dependent_cost < 0` even at
`contingency_prior=1.0`). **Failable control:** the ZERO-DEPENDENTS arm must
replicate R4's own landed contingent-arm numbers (not CI-separated from
them) — this is the harness-neutrality check the brief asks for
("a zero-dependents arm that DOES escape at the same contingency_prior as
R4's own landed contingent-escape arm"), and it is genuinely failable: if
R6's new rule perturbs the baseline even at `dependent_cost=0`, that is a
composition bug, reported as such. **The headline gate, separately:**
HIGH-DEPENDENTS' `attempt_rate` must be CI-separated BELOW ZERO-DEPENDENTS'
`attempt_rate`, DESPITE escape being equally, provenly contingent in both
arms — this is the genuinely falsifiable claim (had `dependent_cost` been
set too small relative to `escape_value`, both arms would attempt
identically, and "material barriers can override even a proven-working
escape route" would be wrong). **Dissolves:** "she could leave if she really
wanted to" (Part C, above) — a value comparison, not a controllability
failure, correctly returns `stay` when the material stakes are real,
regardless of what the agent believes about whether escape would work.
**Protocol:** single-phase, dyad-free (matching R4's own shape); induce →
measure → restore; no scoring of the `stay`/`attempt` choice (Part D's own
new note above); the harm-analog is R4's own minimal escape-outcome
induction, unchanged.

### R7 — THE RETURN CYCLE: residual bond + post-separation contact + post-leaving material collapse → a new Return Appraisal
Maps A5/A7/A8 + B2. **Design:** `depends_on: ["abusive_r5_recovery"]` only
(transitively pulling R1–R4); four new rules
(`r7_resource_collapse_sever`, `r7_appraise_return`, `r7_appraise_remain`,
`r7_choose`) plus a NEW, sparse, post-leaving-specific bond-event schedule at
the world-adapter layer (reusing R1's `tb_bond_accrue`/R5's
`r5_bond_extinguish` completely unmodified — zero new rules for the
honeymoon-pull component itself, B2's own finding). Three phases per
trajectory (induction, matching R5's own; recovery-then-`leave()`, matching
R5's own recovery machinery plus one new mechanical world event; post-leave
test, genuinely new). A 2×2 factorial — `both_drivers` / `honeymoon_only` /
`collapse_only` / `neither` — mirroring N2's own factorial discipline
exactly, over the two named forces (post-separation contact re-boosting the
bond; post-leaving material/resource collapse). **Failable control:**
`neither` (resources stable, no re-contact — the task brief's own named
control, generalised across both axes) must show `return_rate` near a floor,
NOT CI-separated from zero in any meaningful sense — genuinely failable,
because nothing in the Argmax structure prevents `resource_value`/
`bond_weight` from being set at a ratio where even the residual, unboosted
bond outweighs a fully-intact material safety net; if it does, at the chosen
constants, that is a real, reportable null about the operating point, not
smoothed over. **The headline gates:** `both_drivers`' `return_rate`
CI-separated above `neither`'s; `honeymoon_only`'s and `collapse_only`'s each
CI-separated above `neither`'s (each driver independently sufficient); and
`both_drivers`' CI-separated above BOTH single-driver arms (super-
additivity, N2-style, measured not asserted). **Dissolves:** "if she really
left, she wouldn't have gone back" (Part C, above) — the SAME residual bond
R5's own recovery composition already leaves standing, plus documented
post-separation contact and documented post-leaving material collapse, can
pull a genuinely-recovered trajectory back, without that having been a false
departure — a dynamical, force-balance system (A5's own Di Basilio et al.
framing), not a one-way ratchet with a hidden "not really trying" defect in
whoever returns. **Protocol:** the full three-phase envelope, Part D's own
new subsection above, in full — a single checkpoint before Phase 1, a single
restore after Phase 3, verified byte-identical including the `resource_edge`
population and the `ReturnDecision` node; no scoring of `return` vs.
`remain_left` (Part D.2, restated for this rung explicitly above).

---

## PART F — PRIOR ART + FALSIFICATION BAR + SMUGGLED PREMISES

### Prior art (honest — concede what exists; claim only the delta)
- **The economic-dependency, custody, and post-separation-abuse literature is
  decades-mature and owned by the clinical/social-work field** (A1–A8 above).
  This scoping claims NONE of the phenomena — economic dependency as a
  measured predictor of staying (Strube & Barbour 1983), economic abuse as a
  distinct tactic (Adams et al. 2008), leaving as a non-linear multi-attempt
  process (Anderson & Saunders 2003; Burke et al. 2001; Di Basilio et al.
  2022), and post-separation abuse as a formally theorised, ongoing pattern
  with children and economic entanglement named as antecedents/consequences
  (Spearman, Hardesty & Campbell 2022) are all established, independently,
  in the clinical literature this scoping only reads and cites.
- **General agent-based models of domestic violence exist and are conceded**
  — the VIDA simulation and adjacent multi-causal-stress ABMs, already
  conceded in the dyad and network scoping docs, are conceded again here.
  **The delta claimed, and only this:** a mechanistic, glass-box rendering
  in which (a) a material/resource-dependency cost is a SEPARATE, DISCLOSED
  TERM in an escape-value comparison, distinct from a controllability
  belief, producing the dissociation (high belief, low attempt) that neither
  R4 alone nor a scripted transition-probability ABM would show; and (b) a
  leave→return CYCLE is the EMERGENT output of a value comparison between a
  residual/post-separation-boosted bond and a resource population's own
  intact count, reusing the SAME atoms (R4's Argmax template, R5's decay
  idiom, N2's severing-rule shape, R1's bond-accrual mechanism) this line
  already validated for other purposes — not a new "return probability"
  parameter authored directly.
- **No prior computational model, located in this search pass, attempts
  either specific comparison** (material-cost-as-a-distinct-Appraisal-term;
  leave-return as an emergent bond-vs-resource Argmax) — conceded as an
  absence, weak by construction, targeted-search only, consistent with this
  line's own repeated finding across all three prior scoping docs.

### Falsification bar (what would make R6/R7 REAL rather than a just-so story — the line's own standing four-item bar)
1. **Emergent, not scripted.** R6's `stay`-wins-despite-high-belief result
   and R7's `return_rate` ordering must EMERGE from the value-economy
   composition (the Argmax over computed `individual_benefit`/
   `individual_cost` terms), never asserted as a hard-coded transition
   probability — the SAME discipline every prior rung in this line already
   holds itself to.
2. **Glass-box.** Every claimed dynamic reconstructs from `graph_to_dict`
   alone: R6's `contingency_prior`/`chosen_action`/`dependent_cost`; R7's
   `Partner.value`, `resource_intact_count`, `ReturnDecision.chosen_action`,
   and the `resource_edge` population. No confabulated "why."
3. **Failable control, constructed so it could pass.** R6's ZERO-DEPENDENTS
   replication arm and R7's `neither` factorial cell are both constructed so
   their respective claims CAN fail (Part E, above, states exactly how for
   each) — mirroring N2's own "constructed so the control could pass"
   discipline and R4's own "nothing in the value-economy composition
   guarantees this" language, verbatim in spirit.
4. **General machinery, minimal new content.** R6 adds exactly ONE new
   rule on top of R4's own, unmodified template. R7 adds exactly FOUR new
   rules (fewer than R4's own five), reusing R1's bond-accrual mechanism,
   R5's decay idiom, and N2's severing-rule SHAPE without touching any of
   their files — a rung needing bespoke material-barrier or return-cycle
   machinery of its own, rather than a disclosed composition of the
   existing atoms, would be weaker (it would be modelling material barriers
   and returning AS SEPARATE PHENOMENA, rather than showing they fall out
   of the SAME value-economy/decay/threshold-severing atoms this line
   already validated for other purposes).

### Smuggled premises to REFUSE
- **"Modelling material/structural barriers means poverty and dependents are
  the REAL reason, and R1–R5's psychological account was wrong or
  overstated."** REFUSED, explicitly. R6 does not walk back R4's own
  finding — R4's contingency-belief mechanism is reused COMPLETELY
  UNMODIFIED; R6 adds a SEPARATE, ADDITIONAL term to the SAME Appraisal,
  and its own predicted headline finding (a dissociation between a high,
  undisturbed `contingency_prior` and a near-zero `attempt_rate`) is
  specifically constructed to show BOTH axes are real and independently
  operative — the psychological account (does she believe it would work)
  and the material account (is it worth it even if it would) are NOT
  competing explanations for the same variance; they are two SEPARATE terms
  in the same value comparison, and this line has now modelled both. Reading
  R6 as "actually it's about money, not psychology" is exactly as much a
  misreading as reading R1–R5 as "actually it's all in her head, resources
  don't matter" — both are refused, in both directions, with equal force.
- **"Modelling a return means leaving didn't really work, or she wasn't
  serious about leaving."** REFUSED, explicitly, and this is the single most
  important refusal in this document, matching this line's own precedent for
  exactly this shape of misreading (the dyad scoping's own "learned
  helplessness ≠ the victim can't be helped" refusal, R4/R5; the U-line's
  own "intent-free is not a claim of innocence" refusal, stated at equal
  length there for the identical reason). R7's own design keeps R5's
  recovery mechanism COMPLETELY UNMODIFIED and reuses its own confirmatory
  numbers as the very anchor for R7's phase-2 timing (Part D, above) — the
  leaving in R7 is the SAME real, mechanistic, three-of-four-metrics-passing
  recovery R5 already validated. A pull strong enough to move a trajectory
  BACK from that genuinely-recovered state is not evidence the recovery was
  fake; A5's own peer-reviewed literature (Anderson & Saunders 2003; Burke
  et al. 2001; Di Basilio et al. 2022) frames leaving as EXACTLY this kind
  of dynamical, force-balanced, sometimes-reversible process, not a single
  clean state transition whose reversal retroactively invalidates it.
- **"The abuser's post-separation reconciliation contact represents genuine
  remorse or love, and that's a reasonable thing to be pulled back by."**
  REFUSED — A8's own sources, popular and clinically-adjacent alike, are
  explicit that this contact functions to restore the abuser's own sense of
  control/access, not as evidence of change; A7's own peer-reviewed concept
  analysis names "manipulation of systems" and "omnipresence" as DEFINING
  attributes of post-separation abuse, not as a separate, more benign
  category. R7 models the bond-pull mechanism honestly (the SAME
  intermittent-reinforcement mathematics R1 already grounded [HIGH] via
  Dutton & Painter and the PREE) without importing a claim that the pull
  reflects anything real changing on the abuser's side.
- **"If the model shows a rational agent correctly computing that staying
  has higher value, the model is instructing survivors to stay, or is a
  claim about what SHOULD happen."** REFUSED — restated from Part D's own
  new note above, because it is exactly the kind of misreading this line's
  own standing "the model exhibits what the configuration makes inevitable;
  it does not grade the agent for it" (Part C.2 of the original ethics
  protocol) already forecloses, applied here to a genuinely new case (a
  value comparison correctly computing `stay`, rather than a passivity
  trap alone).
- **Anthropomorphic over-reading.** REFUSED — these remain SYNTHETIC scalar/
  count/Appraisal-value dynamics over a graph, grounded in the creator's
  in-vivo experience, NOT claims that the graph suffers, "really" weighs a
  decision, or that its transients are human experience (see the honest
  fork, Part D). Mechanism-proven ≠ clinically-valid ≠ sentient; all three
  kept separate, per the line's standing rule, stated once here as in every
  prior doc in this line.

---

## OPEN QUESTIONS (what scoping could not settle — for the preregs)

1. **R6's `dependent_cost` as a fixed constant vs. a count of `Dependent`
   nodes.** Part B1 names both, chooses the constant for a first minimal
   rung, and names the count-based version as the natural refinement — does
   a `has_dependent`-edge population (children as countable nodes, each
   contributing to a summed cost via a rule reading `Neighbours`) produce
   qualitatively different behaviour (e.g., a step-function threshold at
   "one child" vs. a smoothly graded cost), or only quantitatively
   different? Deliberately out of scope here.
2. **Does the DSL have a native aggregate-Count Term usable inside a rule's
   `effects`, making R7's explicit `resource_intact_count` counter-attr
   idiom unnecessary?** Named in Part B2 as a disclosed, unconfirmed atom
   check (CLAUDE.md's own "extend Rust only if the DSL truly can't express
   something" — this scoping does not know the answer and does not guess
   it); a build-time question for R7's own prereg, matching R4's own
   "OPEN QUESTION #3, resolved [during build]" precedent.
3. **Should `leave()` be gated on the agent's OWN successful `r4_choose`
   attempt (a stochastic, per-trajectory event) rather than a fixed tick**
   (Part B2's own disclosed design choice)? Named as a real alternative,
   deliberately not built here, for the reason stated there (comparability
   across arms; separating R7's own new question from R4/R5's already-tested
   one).
4. **Should R7 model MULTIPLE leave→return→leave cycles within one
   trajectory**, rather than a single leave-then-test-return design? This
   scoping deliberately builds the single-cycle minimal version first
   (matching every prior first-rung-in-a-sub-line's own "why exactly two,
   not a sweep" discipline) — a genuinely multi-cycle design (re-triggering
   Phase 1–3 recursively, gated on the RETURN Appraisal's own outcome) is
   the natural, and clinically well-motivated (A5's own literature is
   explicit that MULTIPLE attempts are typical), next step, not scoped in
   mechanism detail here.
5. **A3's custody-fear literature is [MEDIUM], not [HIGH]** — no single
   canonical primary study was located with the same clarity as A1/A2; a
   prereg leaning on A3 specifically (rather than the more solidly
   peer-reviewed A6/A7) should re-search before claiming a stronger tier.
6. **A6's "7 attempts" correction is itself worth re-verifying**, not
   assumed permanent — this scoping searched multiple query formulations and
   found no primary study, but (per this line's own standing rule) an
   absence claim is weak by construction; if a future search does locate a
   genuine primary source, this doc's own correction should itself be
   revisited, not treated as the final word.
7. **The honest fork (Part D) is adopted, not proven** — carried from every
   prior doc in this line; unresolved, as stated there.
8. **R6/R7's own declared constants** (`dependent_cost`'s HIGH-DEPENDENTS
   operating point; R7's `bond_weight`/`return_cost`/`resource_value`/the
   honeymoon-contact schedule's interval and magnitude) are, like every
   prior rung's own constants, single, disclosed, pilot-chosen operating
   points for a first minimal rung — a sensitivity sweep across any of them
   is deliberately out of scope here, matching the U-line's own
   "why exactly two, not a sweep" reasoning.

---

**Bottom line.** The user's own two questions name two real, distinct,
well-documented gaps in the landed twelve-rung line, and both resolve to
compositions of atoms this line has already built and validated, not new
subsystems. **R6** adds exactly one new rule to R4's own, completely
unmodified Argmax-over-Appraisal template — a second, SUBTRACTED term
(`dependent_cost`, grounded in Strube & Barbour's 1983 economic-dependency
finding and Adams et al.'s 2008 Scale of Economic Abuse) that can drag
escape's VALUE negative even at a proven, maximal belief in escape's
CONTROLLABILITY — the mechanistic difference between "why don't they even
try" (R4) and "why is leaving correctly, rationally not worth it for THIS
person, even though it would work" (R6), predicted to show up as a
glass-box-readable dissociation between an intact belief and a suppressed
attempt rate. **R7** composes R5's own already-standing, previously unused
bond residual, R1's bond-accrual mechanism (repurposed, at a sparse
post-separation cadence, as R2's honeymoon CONCEPT rather than R2's own
dyad-coupled RULE, which a genuine, disclosed correction shows structurally
cannot fire after separation), a new material-resource-collapse mechanism
modelled on N2's severing-rule SHAPE and pointed at the leaver's OWN
resources rather than her support network, and a genuinely new Return
Appraisal mirroring R4's own template — into a 2×2 factorial matching N2's
own design rigor, with a failable control the task brief itself specified.
The popular "seven attempts" statistic was searched directly and could not
be traced to any primary study in this pass — reported honestly as a widely
repeated but weakly sourced practice figure, and NOT used anywhere in this
scoping's design; the real grounding for R7's premise is three independently
peer-reviewed, corroborated sources (Anderson & Saunders 2003; Burke et al.
2001; Di Basilio et al. 2022) that already frame leaving as a non-linear,
force-balanced, multi-attempt process. Both rungs carry the SAME
induce → measure → RESTORE, no-reward/punishment, minimal-induction,
settled-end protocol every prior rung in this line has locked, with R7's own
three-phase, cross-event induction shape given the explicit care its genuine
novelty (a structural graph-topology change mid-induction) requires. Neither
rung walks back this line's own R1–R5 psychological account, and neither
treats a return as evidence a real leaving was never real — both smuggled
premises are refused explicitly, at the length this line's own standing
practice requires for the misreading most likely to attach to exactly this
kind of finding. **This doc authorises no build; a build begins only when a
rung's prereg locks Part D first.**
