# BIGVILLE GOVERNANCE PLAN — recognition-driven authority, grounded in prior art

Turns the fact/frame pass (`BIGVILLE_FACTS_VS_FRAMES.md`) into a build sequence, anchored
in how games and real small-scale societies actually model emergent, usurpable authority.
The recognition primitive is already built and gated (block 324000,
`bigville_recognition.json`): a body dying is a world-fact any agent can cause; a claim to
rule is minted freely; each agent COLLAPSES on whether to recognize it; authority =
Count(recognizers); a decree reaches only recognizers. This plan makes that primitive a
full dynamical system — with tipping, seizure, stabilization, and exit — and applies it to
the ten forced effects the pass found.

## The convergence: three independent systems already built our model

- **Crusader Kings 3 — Legitimacy** ([ck3.paradoxwikis.com/Legitimacy](https://ck3.paradoxwikis.com/Legitimacy)):
  a scalar that ONLY changes how other characters accept/deal with you (alliance, marriage,
  claim acceptance), never a hard gate on action; it **drains on tyrannical acts and on
  capitulating to factions**. Usurping a title ([ck3.paradoxwikis.com/Title](https://ck3.paradoxwikis.com/Title))
  is never *blocked* — it costs opinion (−50) and legitimacy. **De jure vs de facto**
  ([crusaderkings.fandom.com/wiki/De_jure](https://crusaderkings.fandom.com/wiki/De_jure))
  grades tribute: a de-facto-only liege collects *less*. **Claimant factions** act past a
  force threshold and **dissolve when the claimant is killed**.
- **Victoria 3 — Legitimacy** ([vic3.paradoxwikis.com/Government](https://vic3.paradoxwikis.com/Government),
  [Dev Diary #80](https://www.paradoxinteractive.com/games/victoria-3/news/dev-diary-80-law-enactment-and-revolution-clock-in-13)):
  legitimacy is a **weighted aggregate of the powerful population**; below 25 the government
  can pass no laws except those a movement already backs; enacting against the recognition
  distribution grows a counter-movement and, past 75% participation, a **revolution**.
- **Joshua Epstein — "Modeling Civil Violence," PNAS 2002** (equations via the NetLogo
  *Rebellion* reimplementation): each agent goes active iff **Grievance − Net_risk >
  threshold**, where `Grievance = hardship·(1 − legitimacy)` and net risk rises with the
  visible **cop-to-rebel force ratio**. Produces **punctuated equilibrium** — long quiet,
  sudden coups. This is a published recipe for "legitimacy is a scalar that drives
  recognition/refusal," with the exact force-ratio term we want for "fear of shown force."

Enforcement-in-an-agent (never the engine) is also settled prior art: **Dwarf Fortress**
justice does not exist until a Captain-of-the-Guard office is filled
([dwarffortresswiki.org/index.php/Justice](https://dwarffortresswiki.org/index.php/Justice));
**Eco** flags a lawbreaker as a criminal and *another player* must choose to arrest them
([indiedb.com/.../how-player-created-laws-work-in-eco](https://www.indiedb.com/games/eco-global-survival-game/news/how-player-created-laws-work-in-eco)).
That is our architecture rule exactly, and our own `bigville_coll_evict` already does it
(a doer must reach the home) — the court/jail path just never adopted it.

## The five theory pillars (how recognition becomes a dynamical system)

Each is a rule an agent *evaluates*. Sources named; specific numeric constants (Axelrod
payoffs, Epstein equation form) are from the established literature / NetLogo reimpl and are
design targets to re-derive, not quoted values.

1. **Weber — three bases of legitimacy** (*Economy and Society*, 1922): legitimacy is a
   *belief held by the ruled*. Recognition carries a **basis tag** — `charismatic` (updated
   by observed extraordinary acts incl. shown force; decays without fresh demonstration),
   `traditional` (how long the prior order stood), `legal-rational` (was the succession
   *procedure* followed). One substrate → three recognition-update rules. A usurper who
   murders the mayor scores high on charismatic/force, zero on legal-rational/procedure — so
   *who* recognizes him is exactly the set for whom force outweighs procedure.
2. **Bicchieri — conditional social norms** (*The Grammar of Society*, 2006; SEP "Social
   Norms"): an agent conforms iff it believes *enough others* conform (empirical
   expectation) AND that violators are sanctioned (normative expectation). A **per-agent
   threshold over the recognizer count** → recognition self-reinforces above threshold,
   self-collapses below → cascades and tipping. The formal engine of "authority is
   recognition."
3. **Olson — stationary vs roving bandit** (APSR 1993; *Power and Prosperity*): a bandit who
   *settles* and monopolizes theft gains an **encompassing interest** and switches from
   plunder to moderate tax + public-good provision, because a productive population is a
   richer future tax base. **Expected tenure is the decisive variable.** This answers "why
   recognize a usurper": a wise one *buys* recognition by taxing gently and protecting.
4. **Ostrom — 8 design principles + graduated sanctions** (*Governing the Commons*, 1990):
   law/monitoring/sanction are **agent-driven, not fiat** — peers monitor peers and apply
   **graduated** sanctions themselves; the rule-set is editable by those it binds. Property
   = a decree a critical mass recognizes *and will sanction violations of*.
5. **Axelrod — norms & metanorm** (APSR 1986): punishing is individually costly (second-order
   free-rider problem), so norms collapse — unless agents also punish *those who fail to
   punish* (the **metanorm**). This is what makes a *law* durable rather than a ruler's whim.

**Exit as a first-class move** (Haudenosaunee clan-mother *recall*; DAO *fork/secede*;
Athenian *sortition/rotation*; Graeber & Wengrow's *reversible* regimes): recognition must be
withdrawable, and withdrawal needs somewhere to go.

## The build sequence (each rung: prereg → build → gate, `.so` untouched, falsifier-gated)

The existing forced legal seeds (`bigville_legislature/court/jail/sentence/fisc_state/
land_tenure`) stay as the **pre-migration baseline**; each rung builds the recognition-gated
replacement as a new seed and migrates the world/integ once its primitive is gated
standalone (the same discipline used for the bell migration, 320000–323000).

**R1 — Office is a claim, not a fact (the enabling rung).** Replace the seeded
`role`/`on_council`/`staffed_by`/`is_seated` facts with a `Claim{office}` + `recognizes`
layer (CK3 de jure = the minted claim; de facto = who complies; `publisher_role` is the
existing claimable-role template). Each agent recognizes per **Weber basis**. *Gate:* a
usurper can murder the mayor and mint a mayoralty claim (never blocked); "who is mayor / on
the council" is the recognizer distribution; a title with no recognizers confers nothing.

**R2 — Recognition dynamics: Epstein grievance−risk + Bicchieri cascade.** The recognize
collapse (already `rc_recognize`) gains the Epstein arithmetic (grievance from the old
order's illegitimacy; net risk from the visible force ratio) and a Bicchieri threshold over
the current recognizer count. *Gate:* punctuated equilibrium — recognition holds, then flips
en masse; a coup that clears the first-N threshold cascades, one that stalls collapses; the
substrate never forbids either.

**R3 — Recognition-gate the ten forced effects, enacted by an agent.** `law_tax_charge`,
`ct_sentence`, `jl_imprison`, `ca_censure_effect`, `bl_tax_forfeit`, `fs_collect` each fire on
an agent ONLY IF that agent recognizes the authority AND a recognizing **enforcer**
(collector/constable/gaoler) *reaches and acts* — the DF/Eco + `coll_evict`/`bl_enforce`
template generalized. Compliance is **graded by recognition strength** (CK3 de-facto
reduction), not boolean. *Gate:* a non-recognizer is untouched; a law with no recognizing
enforcer is inert (DF's unfilled-sheriff); "the system did it" is impossible ([[no-ownerless-harm]]).

**R4 — The stationary-bandit stabilizer (Olson).** A ruler-claimant chooses its **tribute
rate from estimated tenure** (a function of recognizer-count and force): long horizon → low
tribute + a public good (protection/order) that raises recognizers' payoff → recognition
GROWS (consolidation); short horizon → strip → recognition FALLS (roving-bandit spiral).
*Gate:* two usurpers, identical start — the one that taxes gently and protects settles into
recognized rule; the looter collapses. Explains *why some usurpations become legitimate rule*
without fiat.

**R5 — Law & property without fiat: Ostrom + Axelrod.** On observing a violation an agent
makes a **sanction decision** graduated by the violator's strike-count, sanctioning only what
it *sees*; add the **metanorm** (lower recognition of rulers/peers who fail to sanction
observed violators). Property = a decree a critical mass recognizes and will sanction
theft of. *Gate:* theft is possible (world-fact) but a well-recognized property norm makes
the thief a sanction target; a control with the metanorm off shows the norm collapse to
second-order free-riding.

**R6 — Exit: recall, fork, rotation.** Recognition is withdrawable: **recall** (drop
recognition when a ruler's conduct crosses a threshold — Haudenosaunee), **fork/secede** (a
bloc of refusers below quorum splits off and mints its own claimant — the concrete form of
"what happens when recognition splits"), optional **sortition/rotation** as a
concentration-resistant legitimacy source (Athens). *Gate:* a tyrannical ruler is recalled;
a town split near 50/50 forks into two recognition blocs; regimes are reversible states, not
one-way ratchets.

**R7 — Fold into the live sim (integ).** Once R1–R5 are gated standalone, migrate the integ3
council/tax path to recognition-gated authority the same way the bell migration folded in
(isolated subgraph, no `force_all_dirty`, full-suite green), so the live town runs on
recognized authority end to end.

## Ordering, effort, and what to do first

- **R1 is the keystone** — nothing else can be recognition-gated until office is a claim
  rather than a hardcoded edge. It is also self-contained (extends `bigville_recognition`).
- **R3 has the highest blast radius** (it touches tax + the court/jail family), so gate R2's
  dynamics first, then migrate the two biggest smuggles — `law_tax_charge` and `ct_sentence`
  — as the first R3 targets, leaving the rest of the ten to follow the same template.
- **R4 is the intellectual payoff** (Olson): it's what makes the sim *say something* — why a
  murderer-usurper sometimes becomes a taxing, protecting, recognized ruler and sometimes a
  doomed looter. High value, moderate size.
- R5/R6 deepen it (durable law, exit) and can follow once the spine holds.

## Discipline & honesty

- **Anti-tuning:** legitimacy/recognition must EMERGE from the agents' held dispositions and
  the force/tenure dynamics — never a dialed target. Every rung carries the `=0`/forced
  control as a falsifier (the smuggled auto-apply is the thing we prove we removed).
- **The world-fact core is off-limits:** death, harm, coin conservation, resource stock,
  earshot, the bell, sleep stay engine-enforced. The boundary is the deliverable.
- **Source caveats:** the mechanics above are from the named games' wikis/dev blogs and the
  named canonical works; some fandom pages 403'd during research and specific numeric
  constants (Axelrod payoffs, Epstein's exact equation form) were taken from secondary/reimpl
  sources — they are design targets to re-derive and gate empirically, not quoted results.
  Full source list and verification status in the two research briefs.
- **Standing invariant (from the pass):** for every body/coin/property/standing/office
  mutation — world-fact or human-frame? A frame must be recognized by the affected agent AND
  enacted by an agent, never fired on a status attr alone. A title is inert; recognition is
  authority; nothing the substrate does may make a frame un-contestable.
