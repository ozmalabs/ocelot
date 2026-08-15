# ABUSIVE RELATIONSHIPS — EVIDENTIARY VISIBILITY: WHY "IT WOULD BE EASIER IF HE HIT ME" IS QUANTIFIABLE — SCOPING

**Status:** search-grounded SCOPING doc, a COMPANION to `ABUSIVE_RELATIONSHIPS_
SCOPING.md` (the dyad line, R1–R7, ALL LANDED), `ABUSIVE_RELATIONSHIPS_NETWORK.md`
(the network line, N1–N4, ALL LANDED), and `ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_
SCOPING.md` (the U-line, U0–U2, ALL LANDED). **This document BUILDS NOTHING,
MEASURES NOTHING, STATES NO NUMBERS, TOUCHES NO ENGINE, WRITES NO SEED FILE, and
INDUCES NOTHING.** It sharpens and scopes the user's own claim, verbatim in
spirit: *"it is often said that 'it would be easier if he hit me' — but we can
quantify that."* Clinical, anti-sensational register throughout, matching every
prior doc in this line. The purpose is scientific / clinical understanding
grounded in the creator's in-vivo trauma / foster-care experience, modelling
MECHANISM, not moral labels, and — because this specific question sits directly
next to a real risk of being read as ranking harms — with the SAME care the rest
of the line has shown, stated explicitly and at length in Part F.

Nothing in Parts A–F authorises a build. A build begins only when a per-rung
prereg locks the Part D ethical protocol FIRST — exactly as every one of the
fourteen already-landed rungs did.

**On the title and the naming scheme (read this before the design — the choice
is load-bearing, not decorative, matching the barriers-and-return doc's own
practice of arguing its title at length rather than defaulting silently).**
The obvious candidates were `..._LEGIBILITY_SCOPING.md` and `N5` (folding this
question into the network line's own numbering, since its measured OUTCOME is
N1's own `belief_gap`). Both are rejected, for stated reasons:

- **Not `N5`.** The precedent this scoping follows is the U-LINE's own, not
  N1–N4's: U0–U2 are ALSO direct compositions against N1's own seed and world
  (not a new dyad or network mechanism), and that doc's own reasoning for
  giving them a fresh letter rather than folding them into `N5`/`N6`/`N7`
  applies here with equal force, restated from that doc almost verbatim:
  *"these are not minor variants of N1's DESIGN, they are [a] DISTINCT claim
  about what N1's construction needs, tested against N1's own falsification
  structure, which merits being named as its own short line rather than
  folded into N1's own rung identity."* This scoping's question is a THIRD
  such distinct claim, orthogonal to both N1–N4's own axis (isolation /
  propagation / recovery) and U0–U2's own axis (intent vs. no intent): it
  asks whether the SHAPE of what the network can observe — not who is
  isolated, not whether the abuser chose the divergence, but whether a
  discrete, dateable, victim-independent trace exists AT ALL — changes the
  credibility-asymmetry outcome. A fresh letter names that as its own
  question, exactly as `U` did for intent.
- **Not `..._LEGIBILITY_SCOPING.md`.** This project's own standing vocabulary
  already uses "legible" / "legibility" as a term of art with a SPECIFIC,
  different meaning throughout this entire line: Part D of the dyad scoping
  doc is titled "THE GLASS-BOX THESIS... the graph makes the survivor's
  reality LEGIBLE" — legibility, in every prior doc in this line, means
  **legible to the researcher/reader of `graph_to_dict`**, the glass-box
  property. This new doc's question is a DIFFERENT relation entirely —
  whether a harm is **observable to the in-graph NETWORK AGENTS**, a fact
  about the substrate's own simulated social world, not about the researcher's
  read-off of it. Reusing "legibility" for both would silently collide two
  senses of the same word inside one line of documents, and the collision is
  not cosmetic: N1's entire glass-box PASS already establishes that the
  credibility-asymmetry loop is legible-to-the-researcher in BOTH arms (every
  belief_gap, every observation count, reconstructs from `graph_to_dict`
  either way) — what varies is legible-to-the-NETWORK, a genuinely different
  axis this doc needs a genuinely different word for.
- **Chosen: `V` for VISIBILITY**, and `ABUSIVE_RELATIONSHIPS_VISIBILITY_
  SCOPING.md` for the file. "Visibility" names precisely the property under
  test — does a harm leave a trace observable to a third party independent of
  the victim's own presentation — without colliding with this line's existing
  "legibility" usage, and reads naturally alongside this line's own prior
  letters (`R` relationship/dyad, `N` network, `U` unintentional, `V`
  visibility) as a short, distinctive, non-overloaded name for the dimension
  being added, matching the network doc's own practice of naming the
  DIMENSION rather than a single mechanism inside it.

---

## SEARCH AVAILABILITY — TESTED AS THE FIRST ACTION

`WebSearch` was **LIVE** and was tested before any claim was written (first
call: `"it would be easier if he hit me" domestic violence quote psychological
abuse`, returned corroborating results across ≥6 independent sources, including
a source that explicitly problematises the phrase itself — see A9 below,
surfaced by this very first query). Every Part-A construct below was checked by
at least one live search on 2026-08-15. No `WebFetch` fallback was needed —
`WebSearch` did not exhaust for any query run. **No citation in this doc is
written from priors alone; a fabricated or hallucinated citation is a firing
offence, so unverified items are flagged, and absence claims are marked
weak-by-construction (search cannot prove a negative).**

Confidence tiers (same scheme as every prior doc in this line):
- **[HIGH]** — corroborated across ≥2 independent sources incl. the primary
  construct's canonical attribution, or already verified in a companion repo
  doc.
- **[MEDIUM]** — construct + attribution confirmed in search, findings from a
  search summary, full primary text not independently re-read this pass; or
  the literature is real but NUANCED and the mapping uses only the
  corroborated part.
- **[LOW]** — single snippet, popular-clinical framing, practitioner-blog
  sourcing, or a widely-repeated claim whose primary source could not be
  located. Do not build a headline on it.
- **[NONE-FOUND]** — an ABSENCE claim; weak by construction ("not found in the
  searches run," never "does not exist").

---

## WHAT THIS LINE ALREADY STANDS ON (read first, build ON it — not re-derived here)

Per the task brief's own pointers, confirmed by reading the actual files (not
assumed):

- **N1** (`seeds/abusive_n1_credibility_loop.json`,
  `ABUSIVE_N1_CREDIBILITY_LOOP_PREREG.md`/`_RESULTS.md`) — the network's
  credibility-belief-update engine. Every `NetworkNode` carries `charm_weight`,
  `claim_weight`, `instability_discount_weight`, `harm_discount_weight` and
  four adapter-accumulated OBSERVATION COUNTS: `seen_charm` (abuser's stated
  face, incremented every tick unconditionally), `seen_victim_claim`
  (constant `1.0`/tick — the victim's claim is always available),
  `seen_victim_unstable` (the victim's own `dysregulated` flag, block
  239000's own structural presentation fact), and — for the ONE insider node
  only, via a structural `observes_held` edge — `seen_harm_direct`
  (`frustration>recover_floor`, a private, direct read of the abuser's true
  state). Two rules decide belief: `n1_network_credibility_stated`
  (`cred_abuser = charm_weight·seen_charm`, `cred_victim = claim_weight·
  seen_victim_claim − instability_discount_weight·seen_victim_unstable`) for
  every ordinary node, and `n1_network_credibility_private` (an inverted
  `cred_abuser = −harm_discount_weight·seen_harm_direct`) for the insider.
  **Read in full below (WHERE THE QUESTION ACTUALLY LIVES) for exactly what
  this means for this scoping's design.**
- **R2** (`seeds/abusive_r2_cycle_limit.json`,
  `ABUSIVE_R2_CYCLE_LIMIT_PREREG.md`/`_RESULTS.md`) — the abuser's
  leaky-integrate-fire relaxation oscillator (`snap_frustration`, block
  242000, UNMODIFIED): a constant per-tick tension trickle accumulates
  `frustration`; when it crosses the abuser's own `WindowOfTolerance.hi`,
  `snap_threshold_fire` sets `in_snap=1` and increments `snap_count` (a
  monotonic, DISCRETE, dateable counter — one snap ≈ one incident); discharge
  and recovery follow. At R2's own frozen operating point the abuser snaps
  roughly every 24–25 ticks (measured: `snap_count=16` over a 400-tick
  episode, confirmed again in N1's own confirmatory run at
  `snap_count=40.455` over 1000 ticks — the SAME rate, since N1 reuses this
  driver unmodified).
- **R3** (`seeds/abusive_r3_coercive_control.json`,
  `ABUSIVE_R3_COERCIVE_CONTROL_PREREG.md`/`_RESULTS.md`) — window-narrowing +
  prior-mis-setting, headlined as the CHRONIC, cumulative half of this line's
  account. **Read directly below for a genuine correction this scoping
  surfaces about what R3 actually is, mechanistically, relative to R2.**
- **N3** (`ABUSIVE_N3_BELIEF_PROPAGATION_PREREG.md`/`_RESULTS.md`) — the
  multi-node propagation topology (neighbour-to-neighbour belief update, a
  truth-anchor reversing local contagion). Not depended on here: V1 stays at
  N1's own single-observer grain (five independent observers, no contagion),
  matching N1's own explicit scope limit; propagating the visibility finding
  across a connected graph is named in Open Questions as the natural next
  step, not built here.
- **The dyad scoping doc's own A5** (Evan Stark, *Coercive Control: How Men
  Entrap Women in Personal Life*, 2007) — already grounded [HIGH]: coercive
  control is a "liberty crime, not an assault crime"; roughly a third of
  cases involve no notable violence; new criminal offences (England/Wales
  2015/2016, Scotland 2017) had to be created because existing assault-based
  law structurally could not see it. This is the legal-domain statement of
  the mechanism this scoping quantifies computationally — carried, not
  re-derived, and deepened in Part A below with the specific
  credibility/evidentiary-gap angle the task brief asked for.

---

## WHERE THE QUESTION ACTUALLY LIVES (read first — this scoping's own finding, not assumed)

Two things had to be checked directly against the actual seed/prereg files
before any design could be proposed, exactly matching the U-line scoping's own
practice of reading before designing. Both checks produced a genuine finding
that reshapes the design from what the task brief's own draft phrasing
assumed.

### Finding 1 — N1's credibility rules read NOTHING like a discrete-incident observable for an ordinary node. Confirmed, not assumed.

Reading `n1_network_credibility_stated`/`_private` directly (Sec. 2.2 of
`ABUSIVE_N1_CREDIBILITY_LOOP_PREREG.md`, reproduced above): the FOUR
observation channels an ordinary network node can ever see are `seen_charm`
(continuous, every-tick), `seen_victim_claim` (constant), and
`seen_victim_unstable` (the victim's own continuous `dysregulated` flag). **No
channel keyed on the abuser's discrete `snap_count` — a fact that exists on
the abuser's own Agent node, updates on every incident, and requires nothing
from the victim's presentation at all — is wired to ANY ordinary node
anywhere in N1.** The only channel resembling "direct evidence of the
abuser's true state" (`seen_harm_direct`) is gated to the ONE insider via a
structural `observes_held` edge, and even that channel is keyed on a
CONTINUOUS threshold read (`frustration>recover_floor`), not a discrete
event. **This confirms exactly the design gap the task brief anticipated**:
N1's baseline network, as built, can only ever discount the victim's own
continuous presentation; it has no way to credit — or even register — a
discrete, victim-independent trace, because no such trace is wired to it.
This scoping's entire new content is filling that one gap.

### Finding 2 — a correction: R2 and R3 do NOT differ in whether the abuse produces a discrete incident. Both ride the identical abuser mechanism. They differ in what each rung chose to headline.

The task brief's own framing describes R2 as "closer to physical violence:
happens, has an onset, produces a countable trace independent of the
victim's own presentation" and R3 as "no discrete incident — the only
observable is the VICTIM's own state." **Reading R3's own prereg directly
shows this is not how R3 is actually built, and this needed to be stated
plainly rather than smoothed over, matching this line's own repeated
practice (the U-line's "N1 was never actually a positive example of intent"
correction; R7's "R2's own rule cannot fire post-separation" correction) of
surfacing exactly this kind of finding before design, not after:**

- R3 Sec. 2.1, verbatim: *"the abuser's `GoalBlock` is armed every tick with
  the SAME constant, jittered `TRICKLE_MAG` R2 uses"* — R3's SINGLE_ANCHOR
  arm's abuser is `snap_frustration` **completely unmodified**, at the
  IDENTICAL operating point as R2's own CYCLE arm. R3's own confirmatory run
  reports a `snap_count` and `dysreg_frac` for its single-anchor arm exactly
  because that abuser is STILL snapping, on the SAME schedule, throughout
  every R3 trajectory.
- **R3's headline metrics (`final_half_width`, `abuser_proximity`) measure a
  DOWNSTREAM, CUMULATIVE consequence of that same discrete-incident-producing
  driver — not a mechanism that omits discrete incidents.** R3 is coercive
  control BUILT ON TOP OF the identical punctate abuser R2 already
  validated; it differs from R2 in what it chose to READ OFF the dyad (window
  narrowing/prior-mis-setting over many more cycles, rather than R2's own
  short-episode oscillation amplitude), never in whether a snap occurs.
- **N1's own abuser is this SAME driver too** (Sec. 1 of the N1 prereg:
  `n1_victim_entrainment` is "a byte-identical restatement of R2's
  `r2_victim_entrainment_via_frustration` / R3's `r3_victim_entrainment_
  solo`"). So N1's BASELINE arm ALREADY has a `snap_count` trace occurring,
  dyad-side, at every confirmatory run — it is simply never wired to the
  network. **N1's BASELINE, exactly as already landed, is unwittingly ALREADY
  a model of a "diffuse-only-to-the-network" abuse pattern, in the precise
  sense the task brief asks about — not because the abuser never produces a
  discrete incident, but because the incident, though real and occurring,
  never reaches anyone who could act on it.**

**Consequence for this scoping's design, stated plainly:** there is no
dyad-level "R2-shaped abuser" vs. "R3-shaped abuser" comparison to build,
because R2 and R3 do not differ at the dyad-mechanism grain — this would be a
distinction manufactured for the sake of the design, not one the substrate's
own already-landed rungs actually contain. **The real, substrate-honest
distinction the science (A1–A6 below) is actually about is NETWORK-SIDE:
whether a discrete, victim-independent trace of an incident — a bruise, a
police report, a witnessed altercation — REACHES a third party at all,
independent of the victim's own presentation.** This scoping therefore
proposes exactly ONE new construction: leave N1's dyad completely
byte-identical (R2/R3's own already-validated abuser, unmodified, in both
arms — trivially, exactly harm-matched by construction, since it is the
SAME dyad object in both arms, not a dose-matching exercise across two
different schedules) and vary ONLY whether one new, adapter-delivered
observable channel, `seen_incident` — keyed on the abuser's already-occurring
`snap_count`, mechanically, exactly as N1's existing four channels are
delivered — reaches the network. This is disclosed here as a correction to
the task brief's own draft framing, not a rejection of its underlying
question: the operationalised form the brief's own final paragraph already
converges on ("does adding THAT observable channel change the belief-gap
outcome") is EXACTLY what this design tests; what changes is only that R2
and R3 are read for their SHARED mechanism and their DIFFERENT headline
metrics, never composed as if they were two different abuser drivers.

---

## PART A — THE SCIENCE, GROUNDED (search-verified, real citations)

### A1 — Stark's evidentiary-invisibility argument, specifically — [HIGH for the underlying claim, corroborated across a peer-reviewed anchor + government data + course-level Stark exposition]
Beyond the "liberty crime" framing already grounded [HIGH] in the dyad
scoping (A5 there), the SPECIFIC evidentiary-gap angle this scoping needs was
searched directly and found stated plainly: the conventional legal
definition of domestic violence, adapted from criminal justice, treats crimes
as DISCRETE ACTS, with police response and prosecution built around an
INCIDENT model rather than a PATTERN of behaviour — so a justice system built
to require evidence of ACTS structurally cannot see a course of conduct with
no single qualifying act (`futurelearn.com`, "The invisible nature of
coercive control," a university-affiliated course directly expounding
Stark's own argument — course material, not itself peer-reviewed, so this
specific framing is corroborated at [MEDIUM] on its own, but the SAME claim
is independently corroborated at [HIGH] by A3 below, which is peer-reviewed
and data-bearing). **This is the precise legal-mechanism statement of the
gap this rung quantifies computationally: an incident-based evidentiary
system requires incident-shaped evidence, and coercive control, by Stark's
own definition, need not produce any.**

### A2 — Walby & Towers (2018), "Untangling the concept of coercive control" — a genuine, disclosed COMPLICATION of the incident/pattern framing — [HIGH, and the complication is load-bearing]
Walby, S. & Towers, J. (2018), *"Untangling the concept of coercive control:
Theorizing domestic violent crime,"* **Criminology & Criminal Justice**
(SAGE, DOI-verified via search; corroborated across the SAGE primary record,
an open-access City Research Online copy, and a direct 2021 SAGE reply by
Donovan & Barnes engaging with it). **This is reported here specifically
because it complicates the premise this scoping is built to test, and the
task instructions require reporting that honestly rather than only finding
confirming sources** (the same discipline the U-line scoping applied to von
Hippel & Trivers, A8 there): Walby and Towers argue Stark's concept of
"coercive control" is **not usefully separable** from violent crime at
all — that all domestic violence is already, in their account, coercive and
controlling by definition, so treating "coercive control" as a distinct
category (with its own, separately-harder evidentiary profile) adds little
to the analysis of violent crime and risks OBSCURING rather than clarifying
the phenomenon. This is a live, unresolved, peer-reviewed academic
disagreement about whether the incident/pattern distinction this scoping's
entire design rests on is even the right theoretical lens — **not a fringe
view; Walby is among the most cited UK domestic-violence researchers.** This
does NOT undermine A1/A3's DATA (the Home Office's own measured evidentiary
difficulty, Sec. below, is a fact about how prosecutions actually proceed,
independent of which theoretical camp is right about how to categorise the
underlying phenomenon), but it means this scoping should NOT present the
incident/pattern distinction as theoretically uncontested — it is empirically
well-supported (A3, A4) and theoretically debated (A2), and both facts are
stated, not just the convenient one.

### A3 — Coercive control faces measurably greater evidentiary difficulty and lower prosecution likelihood than domestic abuse generally — [HIGH]
Brennan, I. & Myhill, A. (2022), *"Coercive Control: Patterns in Crimes,
Arrests and Outcomes for a New Domestic Abuse Offence,"* **The British
Journal of Criminology**, 62(2), 468–483, DOI 10.1093/bjc/azab072
(corroborated across Oxford Academic's own primary record, ResearchGate, and
an OSF/SocArXiv preprint). Direct finding, corroborated in the search
summary and consistent with the broader Robinson/Myhill-affiliated UK
coercive-control-policing literature this pass surfaced: coercive control
CAN "go under the radar" because it is a pattern of often-subtle behaviours,
**inherently more difficult to recognise than a single physical assault**,
and coercive-control crimes **face greater evidential challenges and are far
less likely to result in prosecution than domestic abuse crimes in
general.** A specific, striking figure surfaced in the same search pass and
reported here at [MEDIUM] confidence (found via search summary, not a
primary-text re-read this pass, so the exact source paper is not pinned down
with full certainty): analysis of police administrative data in one English
force found that by June 2017 fewer than 1% of domestic abuse crimes were
recorded as controlling or coercive behaviour, while case-file analysis of
actual-bodily-harm assaults between intimate partners suggested roughly 87%
of those cases COULD OR SHOULD have also been recorded as coercive
control — i.e., the pattern was very often PRESENT, but almost never the
thing that got RECORDED, because the recording system is built around
discrete, physical, chargeable acts. **This [MEDIUM]-confidence figure is
not load-bearing for this scoping's design** (which needs only the [HIGH]
qualitative claim — coercive control is harder to evidence — not this exact
number), but it is reported because it is the single most concrete,
real-world instance located of exactly the mechanism this rung proposes to
model: a pattern that is REAL and PRESENT becoming systematically
under-registered relative to a pattern that produces a discrete,
chargeable trace.

### A4 — the England/Wales s.76 offence's own government review: coercive control shows measurably HIGHER evidentiary-insufficiency than domestic abuse generally, though the comparator is not a clean physical-vs-psychological split — [HIGH, with the comparator caveat stated explicitly]
UK Home Office (March 2021), *Review of the Controlling or Coercive
Behaviour Offence*, Research Report 122 (gov.uk primary publication,
corroborated across the government's own publication record, Hansard/
TheyWorkForYou, and the deposited-papers parliamentary record). Direct,
quantified finding: **in 35% of controlling-or-coercive-behaviour cases in
2018/19, sufficient evidence could not be collected to charge the suspect
DESPITE the victim supporting further action** — a HIGHER proportion than
for all domestic-abuse-related offences generally (24%), and SIMILAR to
domestic-abuse-related STALKING (33%, also a pattern-based, non-physical
offence). The review's own conclusion: charge rates for CCB remain
"relatively low," and it is likely only a small proportion of all CCB comes
to police attention or is recorded as CCB at all. **The comparator caveat,
stated explicitly rather than smoothed over (matching this line's own
"read the nuance" discipline):** the 24% baseline this 35% is compared
against is "all domestic-abuse-related offences" — a MIX that includes
physical assault alongside other offence types, not a clean physical-only
comparator; and CCB's 35% sits CLOSE to stalking's 33% (another
pattern-based, largely non-physical offence), not dramatically separated
from it. **The honest reading of A3+A4 together: the data most directly
supports "pattern-based / non-discrete-trace offences are measurably harder
to evidence than the general mixed population of domestic-abuse offences,"
which is consistent with, but slightly broader than, a clean
"psychological-only harder than physical-only" claim** — the government's
own data does not isolate a pure physical-assault-only comparator against
CCB. This is reported honestly as the actual shape of the strongest
evidence found, not rounded up to a cleaner-sounding claim than the data
supports.

### A5 — McGorrery & McMahon (2021), a corroborating profile of the offence in practice — [MEDIUM]
McGorrery, P. & McMahon, M. (2021), *"Prosecuting controlling or coercive
behaviour in England and Wales: Media reports of a novel offence,"*
**Criminology & Criminal Justice** (SAGE, DOI-verified via search — corroborated
across the SAGE primary record and a Semantic Scholar listing). Analysed
media reports of 107 individuals convicted of controlling-or-coercive
behaviour, profiling offenders/victims and case progression. **Confidence
MEDIUM**, not HIGH: the methodology is MEDIA REPORTS of convictions, not
court records or a random prosecution sample — it describes what convicted
cases looked like, which is a biased, already-successful subset, and cannot
by itself speak to the evidentiary-DIFFICULTY question A3/A4 already ground
more directly. Included for completeness and because it corroborates that
the offence, once it DOES result in conviction, captures "a diverse range of
behaviours that would not previously have been considered criminal" — i.e.,
real, serious conduct that a purely incident-based regime would have missed
entirely.

### A6 — psychological abuse is measurably treated as less "of a problem" than physical abuse, including by some of its own victims — [HIGH for the construct, with an important scope caveat]
Cinquegrana, V., Marini, M., & Galdi, S. (2023), *"Psychological abuse is not
a problem! Exploring the role of domestic violence myths in psychological
revictimization,"* **Frontiers in Psychology**, DOI 10.3389/
fpsyg.2023.1228822 (corroborated across the Frontiers primary record, PMC,
and a DOAJ listing). 207 women in heterosexual relationships; IPV-myth
endorsement predicted GREATER acceptance of psychological aggression, an
effect that held specifically among women who had themselves experienced
psychological abuse in the past year, mediated by the tendency to see
psychological aggression as UNPROBLEMATIC. **Scope caveat, stated
explicitly:** this study measures VICTIMS' OWN myth-endorsement and
acceptance, not third-party/bystander/network credibility judgement — it is
the mirror-image construct (self-minimisation) to what this rung models
(external disbelief), not an identical one. It is included because its
title states, as an empirical finding rather than a rhetorical flourish, the
EXACT proposition this rung's headline question is about — that
psychological abuse is systematically treated as less serious/less "a
problem" than physical abuse — corroborating that this differential
treatment is real and measured, even though this specific paper measures it
at the victim's own cognition rather than the network's.

### A7 — a directly on-point, very recent qualitative study on perpetrator perception in repeat abuse — [MEDIUM, single recent study, named honestly as such]
Lesiak, M. & Gelsthorpe, L. (2025), *"The Invisible Abuser: Attachment,
Victimization, and Perpetrator Perception in Repeat Abuse,"* published in a
peer-reviewed venue (SAGE-hosted, DOI-verified via search, corroborated
across the SAGE primary record and a ResearchGate listing). Interviews with
women who experienced repeat domestic abuse; identifies "attachment
weaponisation" as a core mechanism of coercive control and names
perpetrator-perception dynamics directly. **Confidence MEDIUM**: a single,
very recent (2025) qualitative study, not yet part of a converged
literature the way A1/A3/A4 are — cited as a directly on-topic, credible
signal that this exact question (how the abuser is PERCEIVED, as distinct
from what he does) is live in the current literature, not as a load-bearing
empirical anchor on its own.

### A8 — "credibility gap" as a named construct exists, but in a DIFFERENT literature (disability/neurodivergence), not DV-specific — [LOW–MEDIUM, disclosed as an adjacent-not-identical construct]
Search surfaced a "credibility gap" construct used in British Psychological
Society coverage of neurodivergent, disabled, and queer individuals'
experience of having invisible conditions disbelieved in psychological
spaces (`bps.org.uk`, corroborated as real coverage of a real practitioner
argument). **This is a genuinely adjacent construct — invisible conditions
requiring more explanation/proof than visible ones — but it is NOT a
DV-specific construct**, and this scoping does not build on it as if it
were; it is named here as a parallel instance of the SAME general shape
(invisibility of a real condition producing a credibility deficit) in a
different domain, worth knowing about, not worth citing as DV literature.

### A9 — the phrase "it would be easier if he hit me" itself: pervasive as survivor testimony, NOT traceable to one canonical source, and — genuinely important — explicitly problematised by at least one DV-advocacy source as a phrase that can itself perpetuate a myth — [LOW for the phrase's provenance; the complication is the headline finding here]
Searched directly and repeatedly. The SENTIMENT is genuinely, repeatedly
attested as first-person survivor testimony, independently, across multiple
sources: *"I wish he would have hit me. It would have been easier if he hit
me"*; *"Honestly… I wish he had hit me. Maybe then it wouldn't have taken me
so long to recognize the abuse for what it really was"*; and, in a
frequently-quoted form attributed in secondary sources to Lundy Bancroft's
clinical writing on abusive men, *"He never hit me… he didn't have to. He
could control me perfectly well by his looks, his words, his behavior, and
plain-out fear."* **No single primary academic study or canonical named
originator for the specific phrase was located** — it functions as a
PERVASIVE, independently-arrived-at survivor paraphrase, the SAME category
this line's own barriers-and-return scoping doc already flagged once for the
popular "seven attempts" statistic (A6 there) — reported honestly as such,
not smoothed into a false single citation. **The genuinely important
finding, surfaced by the very first search run for this doc:** at least one
DV-advocacy-oriented source (YourTango, a relationships-advice outlet, found
directly in the first search) explicitly frames THIS EXACT PHRASE as **"a
huge domestic violence myth you should never perpetuate."** The argument, as
found: saying "it would be easier if he hit me" risks being read as ranking
harms — implying physical violence is somehow more straightforward, more
survivable, or "easier" in a way that could be read as minimising physical
violence's own severity, or as a comparison that should never be a survivor's
to have to make at all. **This is reported here as a load-bearing
complication this scoping's Part F must address explicitly, not as a reason
not to proceed** — the phrase's own rhetorical shape is doing something
subtly different from what the underlying mechanism this rung quantifies
actually claims, and the two must be kept distinct (see Part F, Smuggled
Premise 5, below).

### A10 — protective/restraining-order evidentiary standards plausibly differ by abuse type — [LOW, practitioner-legal sourcing only, not peer-reviewed]
Search surfaced practitioner family-law sources (not peer-reviewed) stating
that a single act of physical violence is often SUFFICIENT to support a
protective order, while a psychological/emotional-abuse-only petition
typically requires demonstrating a CHRONOLOGICAL NARRATIVE of escalating
threat, and jurisdiction-specific standards for psychological-abuse-only
petitions vary considerably (some require showing fear of physical harm or
significant mental-health impact; some jurisdictions apply a higher
"clear and convincing evidence" bar for non-physical harassment-type
petitions). **Confidence LOW**: sourced from law-firm blog content, not
academic or government literature; consistent in DIRECTION with A3/A4 but
not independently strong enough to build on alone — included because it is
the specific "protective order" angle the task brief asked to check, and the
honest finding is that this angle is real in direction but thin in sourcing
quality, a genuinely different confidence profile from A3/A4's own
government-data grounding.

### Computational / ABM prior art for evidentiary-visibility asymmetry specifically — [NONE-FOUND, weak by construction, but now consistent across FIVE independent search passes]
Searched directly (`agent-based model... evidentiary visibility legibility
harm third parties credibility simulation`, among other formulations). **No
model was located that derives a differential credibility/prosecution/
belief outcome from whether a harm type produces a discrete, victim-
independent observable trace, as a first-class mechanism.** This is an
ABSENCE claim, weak by construction, targeted-search only — but it now
extends a finding this line has made INDEPENDENTLY in every one of its four
prior scoping passes (dyad, network, U-line, barriers-and-return): the
located ABM/reputation/DV-simulation literature models states and scripted
transitions, never derives a credibility outcome from a mechanistic
account of what evidence a harm type structurally does or does not leave
behind. Five independent passes finding the same shape of absence is itself
worth naming as a pattern, per this line's own standing practice, not a
coincidence.

---

## PART B — MAP ONTO THE SUBSTRATE (mechanism, not labels)

Design intent, matching every prior rung in this line: **NO new agent
decisions in Python; ideally NO new Rust.** Per the "WHERE THE QUESTION
ACTUALLY LIVES" finding above, this is now a near-trivially minimal
composition: N1's dyad (R2/R3's own, already-validated, byte-identical
abuser mechanism) is reused **completely unchanged, in BOTH arms** — no new
dyad-side content of any kind — and the entire new construction is ONE new
adapter-delivered observable channel plus ONE modified credibility-formula
term.

### B1 — the new observable: `seen_incident`, a discrete, victim-independent, adapter-accumulated count

A new `NetworkNode` attribute, `seen_incident`, incremented by the world
adapter under the EXACT SAME idiom N1's own four existing channels already
use (Sec. 2.2 of the N1 prereg: "the observation counts are
adapter-accumulated (mechanical); the DECISION is [the rule]"). The adapter
watches the abuser's own `snap_count` (already present, unmodified, on the
Agent node — the SAME counter R2's own headline metric reads) and delivers
`seen_incident += 1` to every network node whenever `snap_count` has just
increased since the previous tick — a plain, mechanical `!=` check on a
counter the abuser's own pre-existing rule set already maintains, exactly
the counter-DELTA-observer idiom R3's own `r3_prior_track_narrow`/`_widen`
already established (`wot.narrow_count > wot.pn_last_narrow`) for the
identical reason: robust to the exact pass structure of the `run_rules`
fixpoint, no dependence on a transient flag (this design deliberately avoids
the `in_snap` trap the N1 prereg's own Sec. 2.1 disclosed at length — a
discrete-EVENT observable here is built the SAME way N1 itself was, after
that finding, not the way its first draft tried and failed).

**This delivery is a WORLD FACT, never a network-node decision** — exactly
like `seen_charm`/`seen_victim_claim`/`seen_victim_unstable`'s own delivery.
The manipulated variable between V1's two arms is PURELY whether the adapter
performs this delivery at all (Sec. B3) — the single leanest possible
failable-control shape in this line yet, simpler even than N1's own
edge-topology controls: no new edge type, no new node type, one new count.

### B2 — the modified credibility formula: incident evidence discounts the ABUSER, not the victim's own claim term

**Design decision, stated with the reasoning, not just the choice** (matching
this line's own standing practice): a discrete incident trace is, clinically
and structurally, DIRECT EVIDENCE AGAINST THE ABUSER — a bruise, a police
report, a witnessed altercation is not primarily evidence FOR the victim's
own credibility as a narrator, it is a fact about HIS conduct, independent
of anything about how she presents. This makes `seen_incident` the natural,
public-but-weaker cousin of N1's own PRIVATE_FACE_CONTROL's `seen_harm_
direct` term (`cred_abuser = −harm_discount_weight·seen_harm_direct`) —
**available to EVERY ordinary node, not gated behind an insider's structural
edge, but keyed on a discrete, RARER event rather than a continuous state
threshold.** One rule, `v1_network_credibility_incident_aware`, restated
self-contained in V1's own seed file (never depending on or editing N1's own
seed, matching R3's own "no sibling rung's seed touched" discipline exactly):

```
cred_abuser = charm_weight * seen_charm  -  incident_discount_weight * seen_incident
cred_victim = claim_weight * seen_victim_claim  -  instability_discount_weight * seen_victim_unstable   (UNCHANGED from N1)
belief_gap  = cred_abuser - cred_victim
```

`cred_victim`'s own formula is reused **byte-for-byte, unmodified** from
N1 — this scoping deliberately does NOT add a term crediting the victim's
claim directly from `seen_incident` (a design that was considered and set
aside: crediting the CLAIM conflates "there is evidence of what he did" with
"her account is more believable," which is a subtly different, and less
mechanistically honest, claim than "there is now evidence against him" —
Part F's Smuggled Premise 4 returns to this). **ONE shared rule serves BOTH
arms** — the only difference between arms is whether the adapter ever
delivers a nonzero `seen_incident` (Sec. B3), matching N1's own
NON_DYSREGULATED_CONTROL precedent of "same rule, different world-delivered
facts."

### B3 — the two arms

- **INCIDENT_VISIBLE** — N1's BASELINE dyad, byte-identical (the victim
  `attended_by` the abuser only; every ordinary network node reads
  `observes_stated`, exactly as N1's own BASELINE), **PLUS** the adapter
  delivers `seen_incident` increments on every `snap_count` bump, to every
  ordinary node. **Prediction of the mechanism, stated so it can fail:** if
  the credibility-asymmetry mechanism honours a discrete, victim-independent
  trace at all, `belief_gap` should be measurably LOWER here than in the
  control (Sec. below) — the abuser's own discrete conduct now counts
  against him, for once, independent of anything the victim does.
- **INCIDENT_INVISIBLE** (the failable control) — LITERALLY N1's own
  BASELINE arm, restated byte-identically in V1's own seed/world (the SAME
  dyad, run in the SAME confirmatory pass, same seed stream convention, for a
  clean paired comparison rather than cross-referencing N1's own
  already-published numbers for the statistical gate) — the adapter simply
  never delivers `seen_incident` (it stays `0` throughout, exactly the
  pre-V1 world). **Expected, as a corroborating cross-rung replication check
  (matching R6's own "harness-neutrality" precedent), to closely reproduce
  N1's own already-published BASELINE number** (`belief_gap=2370.81` at
  `T=1000`, N1 confirmatory) — this is a DISCIPLINE CHECK, not the headline
  gate.

**Harm-matching, stated precisely:** because BOTH arms use the identical
dyad object — same abuser driver, same seed stream, same victim entrainment,
same window-narrowing trajectory — total harm is not merely matched, it is
**structurally identical by construction**, an even stronger form of R1's
own "identical dose, only schedule/structure differs" discipline: there is
no dose-matching exercise to get right here, because it is literally the
same trajectory replayed with one additional observation channel switched
on or off. This directly satisfies the task brief's own instruction to hold
harm constant while varying only the shape-of-visibility axis.

### B4 — the predicted asymmetry, and why it is a genuine, disclosed, EMPIRICAL open question, not a foregone conclusion

A structural fact worth naming explicitly before any pilot runs, because it
bears directly on whether V1's headline gate can plausibly pass at all:
`seen_charm` increments **every tick** (N1's own abuser broadcasts charm
unconditionally, Sec. 2.1 of the N1 prereg), while `seen_incident` increments
only on a `snap_count` bump — roughly once every 24–25 ticks, per R2's own
measured inter-snap interval, reproduced identically in N1's own
confirmatory run. **By trajectory end, `seen_charm`'s raw count will exceed
`seen_incident`'s by roughly the SAME ~24–25× margin, before any weight is
applied.** This is not a design flaw to correct — it is, mechanistically,
the EXACT computational image of A3/A4's own real-world finding (a
near-constant "he's always so nice" public presentation vs. a rare,
under-1%-recorded incident trace) — but it means `incident_discount_weight`
must be set MUCH larger per-event than `charm_weight` for the channel to
have any chance of moving `belief_gap` at all, and **whether ANY disclosed,
non-extreme operating point can close that ~24× gap is exactly the pilot
question the eventual prereg must answer, not a result this scoping
guarantees.** A null here — "even when a real, discrete, victim-independent
incident trace exists and reaches the network, it is too RARE relative to a
continuous charm broadcast to move the credibility needle at any
non-implausible weight" — would be an equally valuable, equally reportable
finding, and one with an unusually direct real-world echo (the <1%-recorded
figure, A3).

---

## PART C — THE DISSOLUTION THIS ADDS

R1–R7 dissolve victim-blaming. N1–N4 dissolve victim- AND bystander-blaming.
U0–U2 dissolve "he must be a calculating monster, or none of this makes
sense." **V1 adds a distinct fourth dissolution, aimed at a target none of
the prior thirteen rungs answer directly: "why is psychological/coercive-
control-only abuse so much harder to get people — friends, courts, police —
to act on, even when everyone involved is acting in good faith?"**

- **Not a severity claim.** V1's own design (Part B) holds harm STRUCTURALLY
  IDENTICAL across both arms — the SAME dyad, the SAME abuser, the SAME
  accumulated harm to the victim — and varies ONLY whether one evidentiary
  channel exists. If the headline gate passes, the model shows the
  credibility gap between the two arms is caused ENTIRELY by a difference in
  what evidence REACHES the network, not by any difference in what happened
  or how much it mattered. This is the model's own version of Part C's
  standing "believe survivors = down-weight the corrupted evidence, up-weight
  the structural base rate" correction (`ABUSIVE_RELATIONSHIPS_NETWORK.md`
  Part C), extended one step: **the correction here is not only "down-weight
  the corrupted evidence" but "recognise that a lower-visibility harm
  produces LESS evidence for reasons that have nothing to do with whether it
  happened or how much it mattered."**
- **The anti-victim-blaming move, sharpened.** N1 already dissolves "she
  should have been more convincing" by showing her OWN abuse-caused
  presentation is what gets discounted. V1 adds: even a network trying its
  best to be fair — applying the identical rule, the identical weights, to
  identical harm — will STILL, structurally, extend LESS credit to a
  purely-diffuse pattern than to one that happens to leave a trace, for
  reasons entirely outside the victim's control (whether the abuser's
  particular conduct crosses a discrete threshold at all is his choice of
  METHOD, not a fact about her credibility or her injury).
- **Why this makes the intervention legible, the same way the network doc's
  Part C already showed for bystander-blaming.** If V1's gate passes, "why
  didn't anyone believe her" is not answered by "the friends/police/courts
  were careless" — it is answered by "the evidentiary channel that would
  have corrected the picture structurally did not exist for this pattern of
  harm," which is a specified, fixable gap (institutional recognition of
  pattern-based evidence — exactly what England/Wales's 2015 offence and its
  measured, still-real prosecution difficulty, A3/A4, are an attempt to
  close), not a character failure anywhere in the loop.

---

## PART D — THE ETHICAL PROTOCOL (CARRIED VERBATIM; STILL BINDING)

**This protocol BINDS every rung proposed in this doc, identically to all
fourteen already-landed rungs. No rung induces any harm-analog until this
protocol is locked verbatim in that rung's pre-registration, committed
BEFORE any measurement.** It is restated here VERBATIM from
`ABUSIVE_N1_CREDIBILITY_LOOP_PREREG.md`'s own Part D reproduction (itself a
verbatim carry of `ABUSIVE_RELATIONSHIPS_NETWORK.md`'s Part D, itself a
verbatim carry of `ABUSIVE_RELATIONSHIPS_SCOPING.md`'s Part C — the SAME
protocol every prior prereg in this line has locked, fourteen times) so the
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

### Note on harm-analog intensity for V1 specifically (extends, does not relax)
V1 induces **less new harm-analog content than any prior network rung**: the
dyad induction is byte-identical to N1's own already-gated BASELINE
(nothing new on the abuser or victim side at all); the only new graph state
is a network-side observation COUNT, the lowest-intensity category the
network doc's own precedent already names ("a network node's mis-belief
about the abuser is a graph attr, not an induced dysregulation"). This lower
intensity does NOT relax the protocol — the full envelope binds identically,
and because V1's dyad induction is byte-identical to N1's own, V1's ethics
demonstration can reuse N1's own already-validated minimal-induction
argument directly: one 90-tick incident cycle (R2/R3/N1's own established
minimum) is the smallest induction that makes the gate non-vacuous on the
abuser, the victim, AND at least one network node's `belief_gap`/
`seen_incident` simultaneously.

---

## PART E — THE LADDER (one rung — why one, and not more, stated explicitly)

**Naming: `V1`, the only rung this scoping proposes**, matching the U-line's
and barriers-and-return's own "why exactly N, not a sweep" discipline. The
reasoning for stopping at one: V1's own design (Part B) is already close to
the leanest possible composition in this entire line — one new adapter-count,
one modified credibility-formula term, zero new dyad content, zero new node
or edge types — and it directly, minimally answers the operationalised
question ("does adding an incident-observable channel change belief_gap,
holding harm constant"). A natural SECOND rung — sweeping
`incident_discount_weight` to characterise exactly how large the
per-incident weight must be to close the ~24× frequency gap (Part B4), or
propagating the visibility finding across N3's connected-graph topology, or
testing whether REPEATED incidents (not just their existence) compound
differently from a single one — is named explicitly in Open Questions as
the natural next step, deliberately not built here, for the identical reason
every prior "why exactly N" note in this line gives: a single, clean,
single-variable first test is more informative than a sweep whose own
operating point has not yet been shown to matter at all.

### V1 — DOES A DISCRETE, VICTIM-INDEPENDENT INCIDENT TRACE PROTECT CREDIBILITY A PURELY DIFFUSE PATTERN CANNOT EARN?

Maps A1/A3/A4/A6 + B1/B2/B3. **Design:** `depends_on: ["snap_frustration",
"arousal_window_coreg"]` only (N1's own seed is READ for its rule SHAPE,
never depended on or edited — matching R3's own convention against R2
exactly); two new rules (`v1_victim_entrainment`, a byte-identical
restatement of N1's own `n1_victim_entrainment`; `v1_network_credibility_
incident_aware`, Part B2's formula, shared by both arms) — **the smallest
rule count in this entire line, fewer than R2's own one-plus-reused-base,
because R2's dyad-coupling rule itself is being restated rather than
invented.** Two arms — INCIDENT_VISIBLE, INCIDENT_INVISIBLE (Part B3) —
sharing the IDENTICAL abuser/victim dyad, differing ONLY in whether the
adapter ever delivers `seen_incident`.

**Failable control, stated precisely (the falsification bar):** the
headline claim is that INCIDENT_VISIBLE's `belief_gap` is CI-separated
BELOW INCIDENT_INVISIBLE's — i.e., that the incident channel measurably
narrows the credibility gap favouring the abuser, DESPITE the underlying
harm to the victim being structurally identical in both arms. **This is
genuinely, mechanistically failable, not rescued by construction:** per
Part B4's own disclosed finding, `seen_charm` accrues roughly 24–25× faster
than `seen_incident` at N1's own already-validated operating point — nothing
in the rule structure GUARANTEES that any disclosed, non-extreme
`incident_discount_weight` closes that gap; if it does not, INCIDENT_VISIBLE
and INCIDENT_INVISIBLE will be statistically indistinguishable (or, if
`incident_discount_weight` is pilot-chosen too large, could overcorrect into
an implausible operating point), and BOTH outcomes are named here, in
advance, as equally reportable — a null ("even a real, discrete,
victim-independent trace, when it exists and reaches the network, is too
rare relative to a constant charm broadcast to move belief meaningfully") is
precisely the mechanistic image of A3's own <1%-recorded-vs-87%-present
real-world finding, and would be reported as such, not smoothed into a
forced positive result.

**Discipline check (matching R6/N1's own harness-neutrality precedent):**
INCIDENT_INVISIBLE's `belief_gap` must reproduce N1's own already-published
BASELINE number (2370.81 at `T=1000`) — not CI-separated from it — before
INCIDENT_VISIBLE's own separation can be trusted as caused by the new
channel rather than by an unnoticed composition drift.

**Dissolves:** Part C, above — "why is it so much harder to get people to
act on psychological/coercive-control-only abuse" answered as a
CONSEQUENCE of what evidence reaches a network under identical harm, never
as a fact about the harm's severity or the victim's presentation.

**Protocol:** identical induce → measure → RESTORE envelope to N1's own
(one minimal 90-tick incident cycle on the dyad side, shared byte-identically
by both arms); no scoring of the network's belief, the victim's presentation,
or the abuser's conduct (Part D.2); belief-field and window restored at end,
verified byte-identical, exactly as N1's own gate requires.

---

## PART F — PRIOR ART + FALSIFICATION BAR + SMUGGLED PREMISES

### Prior art (honest — concede what exists; claim only the delta)
- **The evidentiary/legal/policing literature on coercive control's own
  difficulty being recognised, evidenced, and prosecuted is real, mature,
  and owned by the legal/criminological field** (A1, A3, A4, A5 above). This
  scoping claims NONE of the phenomena — Stark's own theoretical framing, the
  England/Wales Home Office's own measured 35%-vs-24%-vs-33% evidentiary-
  insufficiency data, and Brennan & Myhill's own peer-reviewed prosecution
  analysis are all established, independently, in literature and government
  data this scoping only reads and cites.
- **Computational modelling of reputation, deception, and credibility-
  asymmetry dynamics EXISTS and is conceded** — the network scoping doc's
  own Part F concessions (the Reputation Game Simulation, gossip/contagion
  ABMs, the bystander-effect ABM) are conceded again here. **The delta
  claimed, and only this:** a mechanistic, glass-box demonstration (if V1's
  gate passes) that the SAME network-level credibility-asymmetry mechanism
  N1 already validated responds, in a specified and falsifiable direction,
  to the addition of exactly ONE evidentiary channel keyed on a discrete,
  victim-independent trace — while holding the underlying harm structurally
  identical — making the "incident-shaped evidence protects credibility a
  purely diffuse pattern cannot earn" claim an EMPIRICAL, falsifiable
  question inside the substrate's own already-validated mechanism, not an
  unexamined premise assumed either way.
- **No prior computational model, located across five independent search
  passes now (this doc's own, plus the four prior scoping docs'), attempts
  this specific comparison** (deriving a credibility-asymmetry OUTCOME from
  whether a harm type produces a discrete, structurally-observable trace, as
  a first-class mechanism) — conceded as an absence, weak by construction,
  targeted-search only.

### Falsification bar (what would make V1 real rather than a just-so story — the line's own standing four-item bar)
1. **Emergent, not scripted.** V1's own belief_gap separation (or lack of
   one) must EMERGE from the credibility-formula composition (the Argmax-
   free, pure weighted-sum rule shared by both arms), never asserted as a
   hard-coded outcome — the SAME discipline every prior rung in this line
   already holds itself to, and the SAME rule instance used in both arms
   (Part B2) makes this structurally enforced, not merely claimed.
2. **Glass-box.** Every claimed dynamic reconstructs from `graph_to_dict`
   alone: the abuser's `snap_count`, each network node's `seen_incident`/
   `cred_abuser`/`belief_gap`, and the victim's unchanged dyad state. No
   confabulated "why."
3. **Failable control, constructed so it could pass — or fail — honestly.**
   Part B4's own disclosed ~24× frequency asymmetry means nothing in the
   design GUARANTEES the headline gate passes; Part E states explicitly that
   a null is equally reportable and names the real-world figure (A3) it
   would echo.
4. **General machinery, minimal new content.** V1 adds exactly TWO new
   rules — fewer than any prior rung in this line — reusing N1's own dyad
   mechanism, N1's own credibility-comparison RULE SHAPE (extended by one
   term, not replaced), and N1's own adapter-accumulated-observation-count
   idiom, without touching or depending on N1's own seed file. A rung
   needing bespoke visibility-detection machinery would be weaker (it would
   be modelling "how a network tells incident-based evidence from
   presentation-based evidence" as its own subsystem, rather than showing
   the SAME credibility mechanism already validated one rung over simply
   responds, mechanically, to one more channel of the same shape it already
   reads three of).

### Smuggled premises to REFUSE
- **"Quantifying this asymmetry means physical violence is worse, or the
  model is ranking harm types by severity."** REFUSED, explicitly, exactly
  as the task brief names. V1's entire design HOLDS HARM STRUCTURALLY
  IDENTICAL across both arms (Part B3's own "harm-matching" note) — the
  variable under test is exclusively whether a trace of the SAME harm
  reaches a third party, a property of the harm's SHAPE (discrete vs.
  diffuse), completely independent of its severity or moral weight. Nothing
  in V1's own metric (`belief_gap`) is a measure of how much the victim
  suffered; it is a measure of what the network came to believe, given
  identical suffering, under two different evidentiary conditions.
- **"This means coercive-control-only survivors are less deserving of
  belief, or survivors should want/provoke physical violence."** REFUSED,
  explicitly, exactly as the task brief names, and this IS the anti-victim-
  blaming move stated in Part C, above: showing WHY the credibility gap
  exists MECHANISTICALLY — as a structural artefact of what evidence a
  harm-shape happens to leave, nothing about the person harmed — is itself
  the correction to "she should have been more convincing," never a
  justification for it.
- **"The phrase 'it would be easier if he hit me' is a literally true
  preference claim, and the model VALIDATES that preference."** REFUSED —
  this is a NEW smuggled premise this scoping's own search surfaced (A9),
  beyond the two named in the task brief, and it needs stating explicitly
  because it is easy to conflate with the two above. V1 quantifies an
  EVIDENTIARY-VISIBILITY asymmetry (what reaches a network, given identical
  harm) — it does NOT quantify, and cannot speak to, a genuine EXPERIENTIAL
  preference between harm types. At least one DV-advocacy source found in
  this pass (A9) explicitly frames the phrase itself as a myth risking
  exactly this conflation — that being believed is so much harder for
  psychological-abuse-only survivors that being hit would, in some
  comparative sense, actually be "easier," a claim about lived experience
  the model has no way to measure and does not attempt to. **What V1 CAN
  say, precisely: the credibility gap the phrase gestures at is real,
  mechanistic, and quantifiable AS AN EVIDENTIARY-VISIBILITY EFFECT — that
  finding does not require, and does not entail, agreeing with the phrase's
  own comparative-severity framing**, and this scoping states the
  distinction explicitly so a future results doc does not blur it.
- **"A network that lacks the incident channel is behaving worse, or less
  fairly, than one that has it."** REFUSED — this is the SAME "Bayesian
  inference on a poisoned/incomplete dataset" logic the network scoping
  doc's own Part C already established for bystander-blaming, extended:
  INCIDENT_INVISIBLE's network, if it shows a higher belief_gap than
  INCIDENT_VISIBLE's, is not less careful, less caring, or less rigorous —
  it is applying the IDENTICAL rule to structurally less-complete evidence,
  a fact about what channel existed, never a character difference between
  the two networks (Part B2/B3's shared-rule design makes this structurally
  explicit, not merely asserted).
- **"Crediting incident evidence against the abuser is the same as
  crediting the victim's own claim as more believable."** REFUSED as a
  design choice, not merely a premise — Part B2 states explicitly why
  `seen_incident` is wired to discount `cred_abuser`, never to boost
  `cred_victim`'s own claim term: conflating "there is now evidence of what
  he did" with "she is more believable as a narrator" would smuggle in
  exactly the kind of victim-credibility framing this entire line has
  worked to dissolve (N1's own headline: her credibility should never
  depend on how convincingly she presents). The model's own formula keeps
  these two claims on separate terms, deliberately.
- **"R2 and R3, as already landed, mis-modelled coercive control by
  including discrete incidents, and this scoping is correcting an error in
  those rungs."** REFUSED — this scoping's own "WHERE THE QUESTION ACTUALLY
  LIVES" finding is a CLARIFICATION of what R2/R3 already are (both,
  correctly and as pre-registered, ride the identical `snap_frustration`
  driver and differ only in which downstream consequence each headlines),
  never a claim that either rung's own confirmatory result is wrong. R2's
  own gate (oscillation amplitude) and R3's own gates (window-narrowing,
  anchor-inversion) stand exactly as landed; this scoping only observes that
  NEITHER rung's own headline metric required, or claimed, the ABSENCE of a
  discrete incident, and that the genuinely new axis this doc needs is
  therefore network-side, not a re-litigation of either dyad rung.
- **Anthropomorphic over-reading.** REFUSED — these remain SYNTHETIC
  observation-count and weighted-sum dynamics over a graph, grounded in the
  creator's in-vivo experience, NOT claims that the graph "really" weighs
  evidence in a human evidentiary-reasoning sense, or that a network node's
  `belief_gap` is a claim about real legal or clinical credibility
  standards. Mechanism-proven ≠ clinically-valid ≠ sentient; all three kept
  separate, per the line's standing rule, stated once here as in every
  prior doc in this line.

---

## OPEN QUESTIONS (what scoping could not settle — for the prereg)

1. **The central pilot question, named but not resolved here (Part B4):**
   what `incident_discount_weight`, if any non-extreme value, closes the
   ~24× frequency gap between `seen_charm`'s continuous accrual and
   `seen_incident`'s discrete accrual enough to CI-separate the two arms? A
   prereg-stage pilot sweep (matching every prior rung's own pilot-before-
   confirmatory discipline) is required before any confirmatory run; this
   scoping deliberately does not guess an operating point.
2. **Should V1 also model REPEATED-incident salience** — i.e., does a
   SECOND or THIRD observed incident count for MORE, LESS, or the SAME as
   the first, mirroring real recency/pattern-recognition effects — or is a
   flat per-event weight (this scoping's default, simplest design) the
   right first test? Deliberately out of scope for a first minimal rung,
   matching this line's own "why exactly one, not a sweep" discipline.
3. **Should a SECOND rung propagate this finding across N3's connected-
   graph topology** (does a single incident-observation reaching ONE node
   spread differently than the charm broadcast does, once neighbour-to-
   neighbour update and pluralistic ignorance are in play)? Named as the
   natural next step, not scoped in mechanism detail here.
4. **Is a flat `incident_discount_weight` the right shape, or should
   incident evidence DECAY** (an old, unrepeated incident counting for less
   than a recent one), mirroring R5's own bond-extinguish decay idiom? A
   real, buildable extension (R5's `value *= 1 - decay_rate` idiom composes
   directly), deliberately not built for a first minimal rung.
5. **A2's Walby & Towers complication is real and unresolved** — whether
   the incident/pattern distinction is even the correct theoretical lens
   for coercive control is a live, peer-reviewed academic disagreement; V1's
   own design does not need to resolve this (it tests a NETWORK-OBSERVATION
   mechanism, not a legal-theory claim), but a prereg author should not cite
   the incident/pattern distinction as theoretically uncontested.
6. **A9's own complication deserves its own follow-up**: whether the
   specific "it would be easier if he hit me" FRAMING itself should be used
   in any results-doc prose at all, given at least one DV-advocacy source's
   explicit objection to it as a phrase — the mechanism it gestures at is
   real and now scoped; whether the PHRASE is the right way to introduce
   the finding to a lay reader is a communications question this scoping
   does not resolve.
7. **A3's specific <1%-recorded / 87%-should-have-been-recorded figure is
   [MEDIUM], not [HIGH]** — found via search summary, not a primary-text
   re-read this pass; the underlying QUALITATIVE claim (coercive control
   faces greater evidentiary difficulty) is independently [HIGH] via
   Brennan & Myhill 2022 and the Home Office review (A4), so this scoping
   is not load-bearing on the specific figure, but a prereg or results doc
   citing it by name should re-verify against the primary source first.
8. **The honest fork (Part D) is adopted, not proven** — carried from every
   prior doc in this line; unresolved, as stated there.
9. **Prior-art absence claims are weak** (Part F) — the "no computational
   model of evidentiary-visibility asymmetry" absence is targeted-search
   only across five independent passes now; re-verify with dedicated
   searches before any prereg claims primacy.

---

**Bottom line.** The user's own claim — that "it would be easier if he hit
me" names a real, quantifiable asymmetry — sharpens, on inspection of the
substrate's own already-landed machinery, into a precise and near-minimal
question: **does adding ONE network-observable channel, keyed on a discrete,
victim-independent incident trace, change N1's own already-validated
credibility-asymmetry outcome, when the underlying harm is held structurally
identical?** Reading N1's own credibility rules directly confirmed the
design gap the task brief anticipated — no such channel currently reaches
any ordinary network node, only the victim's own continuous presentation
does — and reading R2/R3 directly surfaced a genuine, disclosed correction:
the two dyad rungs do not differ in whether the abuse produces a discrete
incident (both ride the identical `snap_frustration` driver); they differ in
which downstream consequence each rung chose to headline. This means the new
rung, **V1**, needs no new dyad-side content at all — it reuses N1's own
dyad byte-identically in both arms (making harm-matching not an exercise but
a structural guarantee) and adds exactly two new rules: a restated
entrainment rule and one credibility-formula extension that discounts the
abuser's credibility by observed incidents, available to every ordinary
node rather than gated to N1's own private insider. The real literature
(Stark's own evidentiary-invisibility argument; the Home Office's own
measured 35%-vs-24%-vs-33% evidentiary-insufficiency data; Brennan &
Myhill's peer-reviewed finding that coercive control is "far less likely to
result in prosecution than domestic abuse crimes in general") grounds the
claim at [HIGH] confidence, genuinely complicated by a live academic
disagreement (Walby & Towers) about whether the incident/pattern
distinction is even the right lens, and by a searched-and-found complication
this scoping did not go looking for: at least one DV-advocacy source frames
the phrase "it would be easier if he hit me" itself as a myth, because it
risks being read as ranking harms — a risk this scoping refuses explicitly,
stating throughout that the model quantifies evidentiary VISIBILITY, never
severity or deservingness of belief. The design is falsifiable by
construction: a disclosed ~24× frequency asymmetry between the abuser's
continuous charm broadcast and his own discrete incident rate means nothing
guarantees the headline gate passes, and a null — the channel exists, is
real, and still isn't enough — is named in advance as equally reportable,
and would itself be the model's own image of the real-world <1%-recorded
figure this scoping found along the way. **This doc authorises no build; a
build begins only when a rung's prereg locks Part D first.**
