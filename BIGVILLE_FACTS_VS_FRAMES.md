# THE PASS — world-facts vs human-frames in bigville (2026-07)

Directive: *"the structure of the law is still forcing — we need to do a pass and
separate what are facts about the world, and what are overlaid human frames, and make
them all driven by humans. That is what will make the sim unique. If someone comes in
and murders John and declares themselves ruler, it would cause a lot of problems — but
there should be no reason it* can't *happen."*

This is that pass: an audit of the whole `seeds/bigville_*.json` corpus (90 seeds),
separating **world-facts** (the engine legitimately enforces) from **human-frames**
(only real because agents recognize them), and naming every place a frame is **forced
as physics**. The reframe primitive is built and gated at block 324000
(`bigville_recognition.json`, `BIGVILLE_RECOGNITION_PREREG.md`).

## The three categories (the decision procedure for every effect)

For every rule effect that mutates a body, coin, property, standing, or status, ask:

- **WORLD-FACT** — irreducible ground truth the substrate may enforce unconditionally:
  a body loses health and dies (`bl_death`); a struck body is harmed (`bv_harm_victim`);
  coin is conserved (`bigville_integ2_conserve`); a resource deposit has finite stock;
  a sound is heard within earshot; a bell physically rings; a tired body sleeps. The
  engine owns these. **Correct to force.**
- **HUMAN-FRAME** — a social construct that is true *for an agent only if that agent
  recognizes it*: a LAW's bindingness, a ROLE's authority, PROPERTY, MONEY-as-medium, a
  VERDICT, a CENSURE's sting, who is "on the council". These must be **agent-held and
  contestable** — gated on recognition and enacted by an agent, **never fired on a
  status attr alone.**
- **SMUGGLED** — a rule whose effect fires the moment a status attr is set, with no
  recognition, consent, reach, or enactment. This is a frame wearing physics' clothes.

## What the corpus is (90 seeds)

The **body / perception / affect / cognition / movement** core is overwhelmingly
world-fact and correctly built: `bigville_move_*`, `bigville_affect_*`,
`bigville_life_health` (`bl_death`), `bigville_viol_act`/`_kill` (a body can be harmed
and killed by any agent — including the mayor), `bigville_bells` (a bell rings, a body
wakes), `bigville_decision_core` (the one-collapse decision). **Death is a genuine
world-fact and nothing exempts a role-bearer** — the violence path has no guard on
`role`/`on_council`/office. So *murdering John is already permitted by the substrate.*

The **governance / legal / fiscal / property** cluster is where the frames are forced.
Every effect below fires on a node attr, with no agent in the loop.

## The smuggled assumptions, ranked (most load-bearing first)

Each is a rule whose effect **just fires** when a status attr is set — the money→body
or word→body coupling a legitimate substrate must not own. (Locations from the corpus
audit; the pattern is what matters.)

1. **`law_tax_charge`** (`bigville_legislature.json`) — for *every* resident,
   `coin -= law.value` because a `Law{land_tax}` node has `status="active"`. No
   collector, no reach, no recognition of the taxing authority. The purest smuggle.
2. **`ct_sentence`** (`bigville_court.json`) — a guilty verdict auto-deducts the fine +
   docks standing into the Treasury, regardless of whether anyone recognizes the court.
3. **`jl_imprison`** (`bigville_jail.json`) — the body is **seized and held** by fiat
   (no constable act, no reach, no recognition). Contrast `bigville_coll_evict`, which
   *requires a doer to reach the home* — the jail path was never de-magicalized.
4. **`ca_censure_effect`** (`bigville_legislature.json`) — a posted censure directly does
   `standing -= 1`. Standing is a *social* construct; a censure should bite only if the
   town recognizes the council's standing to censure.
5. **`bl_tax_forfeit` / `bl_land_tax`** (`bigville_land_tenure.json`) — **property (the
   `owns` edge) is transferred to the council** by engine fiat on a `tax_armed` flag.
6. **`fs_collect`** (`bigville_fisc_state.json`) — tax auto-collected from anyone the
   adapter wired a `taxes` edge to (same as #1, via a rate).
7. **`leg_pass`/`leg_amend`/`leg_enact`** (`bigville_legislature.json`) — the
   quorum/`threshold` is a hardcoded attr and the council's legislative output auto-applies
   through `law_tax_charge`. The *right to legislate* is an `on_council` edge + a number.
8. **`ct_verdict_guilty`** (`bigville_court.json`) — settles guilty on
   `Count(condemns) >= threshold` and `Count(heard) >= Count(on_council)`; both "who is on
   the council" and "how many = guilty" are engine facts. (The per-councillor *conclusion*
   `jc_conclude` is a genuine collapse — good; the *aggregation into a binding verdict* is
   hardcoded.)
9. **`sn_sentence`** (`bigville_sentence.json`) — the term is at least bounded by a
   *contestable* `SentenceLaw` (better), but still auto-writes and `jl_imprison`
   auto-executes it.
10. **`bv_council_convict`** (`bigville_viol_prosecute.json`) — conviction on a sum over
    `is_seated` members; the *seat* is a hardcoded edge.

Runner-ups (same shape): `fc_tithe`/`fs_graft` move coin on `corrupt`/`devotion` flags;
`bf_accrue` grows a balance by interest as a law of the money frame; `bw_inn_stay` mints
coin from outside the conserved set (legitimately a *world boundary*, but it is the one
minting point — flag it).

## The core finding: authority is hardcoded everywhere; recognition does not exist

A tree-wide grep for `recogni|legitim|authority|defers_to|consent` returns **zero hits
in any bigville seed**. Authority is **always** a hardcoded edge/attr: `on_council`,
`has_member`, `is_seated`, `staffed_by`, `oversees_office`, or the `role` string. No
agent's recognition of a role or law gates the frame's effect — `law_tax_charge` fires
on the ignorant and informed alike (`knows_law` is decoupled from being bound).

**Roles are fixed data, not claimable status.** `role="mayor"` is a string attr in
`bigville_cast100.json`; `on_council` / `staffed_by` / `is_seated` are edges minted by
adapter code, never by a rule. **No seed rule claims, transfers, vacates, or contests a
governance office.** So the usurper can murder John's *body* (world-fact) but the
mayoralty — the `role` attr, the `on_council` edges, and the authority they confer —
is engine-held and non-transferable. Killing John leaves *a dead body with a dangling
`role="mayor"` attr and orphaned `on_council` edges*, because nothing reassigns office.
**The interesting usurpation — seize the office, have others recognize or refuse the new
ruler — is structurally impossible in the current seeds.** That impossibility is the
smuggle the directive names.

Two existing designs already gesture at the right shape and are the templates:
- **`bigville_laws_enforcement`** — enforcement is a constable *decision*
  (`bl_enforce` fires only if `duty_weight > loyalty_to_john`), and removal runs through
  a held removal-law + villager *backing* (`bl_council_removes` gates on a sum of
  electors who `back` the challenger). Recognition-adjacent, decision-gated. The
  governance cluster does **not** follow it.
- **`bigville_publisher_role`** — the publish role *follows a claimable affordance*
  (`pub_employ_afforder` moves the role when the `affords` edge moves). The one role that
  is claimable at runtime — but it is the newspaper, not a governance office.

## The reframe (built + gated, 324000) and the migration plan

`bigville_recognition.json` supplies the missing primitive, proven on the usurper case:
- a body dying is a world-fact any agent can cause (`rc_strike`);
- a role/authority is a **claim** + **recognition**: each agent *collapses* on whether to
  recognize a claim (`rc_recognize`, by fear/opportunism/loyalty), authority is
  `Count(recognizers)` (`rc_authority`, emergent, never a title), and a decree reaches
  **only recognizers** (`rc_decree_tribute`) — a rejecter is untouched.

Live: Mordred murders John, declares rule; the fearful and opportunist recognize
(authority 2), the loyal refuse; the tribute decree takes coin from the two recognizers
only, the rejecters untouched. **The substrate permits the usurpation; its reach is the
distribution of recognition, not an engine rule.**

**Migration — apply the primitive to the forced cluster, in priority order:**

1. **Make office claimable and contestable** (the enabling change). Replace the seeded
   `role`/`on_council`/`is_seated` facts with a **`Claim{office}` + `recognizes`** layer
   (the `rc_*` shape, following `publisher_role`'s claimable pattern). "Who is mayor / on
   the council" becomes the distribution of recognition, so a usurper *can* claim office
   and the town *can* recognize or refuse.
2. **Gate every forced effect (#1–#10) on recognition + an enactor.** A tax/fine/seizure/
   censure fires on an agent **only if** that agent recognizes the authority, **and** a
   recognizing enactor (collector/constable/gaoler) *reaches and acts* — exactly the
   `bigville_coll_evict` / `bl_enforce` template, generalized. `law_tax_charge`,
   `ct_sentence`, `jl_imprison`, `ca_censure_effect`, `bl_tax_forfeit`, `fs_collect` each
   become recognition-gated + enacted, never a status-attr drain.
3. **Make the legislative/verdict thresholds recognized, not hardcoded.** Quorum,
   "how many condemnations = guilty", and the right to legislate are themselves frames the
   council holds by recognition (a bylaw, per 322000) and the town grants — not engine
   constants.
4. **Leave the world-fact core alone.** Death, harm, conservation, resource stock,
   earshot, the bell, sleep — the engine keeps these. The boundary is the deliverable.

## The standing invariant this pass establishes

> For every rule effect that mutates a body, coin, property, standing, or office, decide:
> **world-fact or human-frame?** A world-fact (death, harm, conservation, physical reach)
> the engine may enforce. A human-frame (law, authority, property, money, verdict, office)
> must be **recognized by the affected agent and enacted by an agent** — gated on a
> `recognizes` edge + a reach/act, **never fired on a status attr alone.** A title is
> inert; recognition is authority; nothing the substrate does may make a frame
> un-contestable. *That is what makes the sim unique: no smuggled institutional facts.*
