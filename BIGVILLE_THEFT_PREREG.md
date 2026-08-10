# PREREG — block 337000: theft as a meaningful action and law

Ownership (block 336000) is a recognized frame, not a world fact. This rung **wires it in**:
now that property is recognized, **theft** becomes a meaningful action — and it feeds the
**law**. The user: *"wire this in — and we can now actually have theft as a meaningful action
and law."*

The whole point rests on the fact/frame split:

- **Taking is a WORLD-FACT.** `th_take`: any agent can physically take what another holds —
  possession transfers, the substrate never forbids it (exactly like `rc_strike` lets anyone
  kill). A thief *can* take the mayor's cloak.
- **Theft is a RECOGNIZED FRAME.** A taking is theft only to the extent the town **recognizes**
  it as such — and it can only recognize it as theft if it first recognizes the owner's
  property. Theft is therefore parasitic on recognized ownership; unrecognized property cannot
  be stolen.

## The mechanism (`bigville_theft.json`)

- **`own_recognition`** — ownership = `Count(recognizers)` (carried from 336000; owner is never
  a fact).
- **`th_take`** — WORLD-FACT possession transfer; marks the taking for the town to judge.
- **`th_recognize_theft`** (the WIRE to the recognition faculty) — each alive witness who
  **recognizes the owner's claim** collapses `{theft, innocent}` valued by `lawfulness −
  alliance_to_taker` (`Argmax` over `TheftStance`, the same collapse shape as `rc_recognize`):
  the lawful see theft, the thief's allies do not — **agents diverge**. Fires only when the
  taker is **not** the recognized owner and there was **no consent**.
- **`th_standing`** — recognized theft = `Count(sees_theft)` (like authority).
- **`th_charge`** — a taking with `standing ≥ court.quorum` becomes a chargeable `Offense`
  (offender, victim = owner, over the item). Below quorum → no crime.
- **`th_vote` / `th_cast_guilty` / `th_verdict`** — a panel of jurors each collapses
  `{guilty, acquit}` valued by `lawfulness · theft_standing − doubt`; the verdict is the
  **majority** of collapses (`2·guilty > total`). Guilt is recognized, not asserted.
- **`th_restitution`** — a guilty verdict is **enacted**: possession returns to the recognized
  owner (a world-fact reversal). Custodial sentencing composes with `bigville_jail` /
  `bigville_sentence`.

## Gates (pass/fail, pre-registered)

1. **G-take-is-a-world-fact:** with nobody recognizing ownership, a take still physically
   succeeds — the substrate never forbids it.
2. **G-recognized-theft-charged-tried-restituted (HEADLINE):** taking a recognized owner's
   property is recognized as theft by the lawful witnesses (`standing = 3`), charged, found
   guilty by the juror collapse, and **restituted** — the item returns to the owner.
3. **G-unrecognized-property-no-theft (HEADLINE / falsifier):** the *same physical taking* of
   property nobody recognizes yields `standing 0`, no charge, no crime — the taking simply
   stands.
4. **G-agents-diverge:** the lawful recognize the theft; the thief's allies collapse
   'innocent' (`standing` = the lawful count only).
5. **G-own-property-is-not-theft:** the owner reclaiming his own recognized property is not
   theft.
6. **G-consent-is-not-theft:** a taking the owner consented to is not theft.
7. **G-acquittal-no-restitution:** a jury with overwhelming reasonable doubt acquits even a
   charged theft, and nothing is restituted — the verdict is a genuine collapse, not automatic.
8. **G-no-python-decision (source audit):** take/recognize/charge/verdict/restitution are the
   seed rules; no `owns` edge; theft is an `Argmax` collapse; recognized theft is
   `Count(sees_theft)`.

## Extension (block 338000) — ownership recognition emerges, and theft carries fines

Two threads the user asked to finish: *"do the fines and the recognition now."*

**Ownership recognition is now a DECISION, not seeded.** `own_decide` — each alive resident
collapses `{recognize, reject}` an `OwnershipClaim`, valued by `legitimacy · deference −
prop_skepticism` (`Argmax` over `OwnStance`, the same shape as `rc_recognize`); `own_grant`
grants the recognition edge; `own_recognition` tallies `Count`. A **legitimate** claim (high
provenance) gathers broad recognition from the law-abiding → the owner emerges; a **usurper's**
low-legitimacy grab gathers ~none → not really owner. Ownership is now emergent, and theft rests
on it — the whole chain (recognise ownership → recognise theft → charge → verdict → restitution)
is now collapses end to end. (`legitimacy = 0` recognises no one, so the older gates that force
recognition explicitly via `recognize_ownership` are unchanged.)

**A guilty verdict now carries damages + a fine, beyond return-of-goods.** `th_penalty` —
`damages = item.value` (to the victim), `fine = value · court.fine_rate` (to the court), imposed
on top of restitution. **Coin is conserved**: the offender pays damages-first then fine, **capped
at what they hold** (no coin invented); the uncollected remainder is recorded as `debt`. Verified:
a thief with means pays 8 + 4 = 12 (victim +8, court +4, sum 0, item returned); a pauper with 3
pays 3 (damages-first), debt 9, conservation holds.

New gates: G-ownership-emerges-from-recognition (legitimate vs usurper), G-emergent-theft (theft
on emergent ownership), G-fine-and-damages (coin conserved), G-fine-bounded-by-means (debt, no
coin invented). 12/12 total.

## Extension (block 339000) — debt collection is the Constable's job

*"The Constable's job would be to collect it."* Collection is not an automatic effect — it is an
office-holder's action, so it carries the whole fact/frame apparatus:

- **`th_penalty`** now splits the unpaid remainder into `debt_damages` (owed the victim) +
  `debt_fine` (owed the court).
- **`con_office`** — the constable's authority = `Count(recognizers)` (a recognized office, not a
  title), mirroring `rc_authority`.
- **`con_duty`** — the constable collapses `{enforce, forbear}` valued by `duty − warmth`, where
  **warmth is how he FEELS about this debtor, read from his first-class held `Bond(A→B)`**
  (`con -holds_bond-> bond -toward-> debtor`, `warmth = affect_affection − affect_resentment` — the
  same quantity `bigville_fast_bond` reads). He forbears for a brother he loves beyond his duty; he
  enforces on a stranger, or on someone he resents. *(Correction folded in: this was first written
  as a flat `loyalty_to_debtor` scalar, then an ad-hoc `Regard{affinity}` node — both wrong. Feeling
  about others is already first-class: the `Bond` with its six relational emotions
  (`bigville_bond_update`, block 277000), evolved by benefit/betrayal/gossip dynamics. `con_duty`
  reads that, and composes with it.)*
- **`th_collect`** — a **recognized** (authority ≥ quorum), **enforcing** constable collects the
  outstanding debt: victim's damages first, then the court's fine, capped at what the debtor now
  holds, repeating as they earn until cleared. A world-fact transfer made *lawful* by the recognized
  office + recognized judgment. (Effect order stores the collected amounts on the offense first,
  then transfers against those stable values — the C6 sequential-effects gotcha, or the take terms
  re-read `debt_damages` after it mutates and corrupt the tally.)

New gates: G-constable-collects-debt (damages-first, over time, coin conserved),
G-fond-constable-forbears (Bond warmth > duty; the same constable enforces on someone he resents),
G-unrecognized-constable-cannot-collect. 15/15 total.

## Scope / honesty
- `standing` counts **third-party** witnesses: the engine won't bind the victim (`owner`) also
  as a neutral witness (`w`), so the owner's own certainty isn't double-counted — the town
  corroborates the claim. A theft with recognized ownership but no third-party witness therefore
  needs `quorum ≤ 1` to charge; witness reach/earshot is a refinement (composes with the bell/
  perception layer).
- Recognition here (of ownership and of alliance) is **seeded** by the adapter; in the live town
  the per-agent recognition **decision** is `rc_recognize`'s collapse — this seed reuses its
  *shape* and composes with it.
- The verdict panel is a compact re-use of the collapse-verdict pattern (`bigville_court`);
  custodial sentence + jail compose with `bigville_jail` / `bigville_sentence`. Fines/damages
  beyond return-of-goods are a refinement.
- One claim + one offense per item in the demonstrator (keeps clear of the two-incoming-edge
  engine gotcha); disputed-ownership takings compose with the tools seed's `disputed` path.
- Isolated demonstrator (`self_load_only`); no Rust; `.so` untouched (`a8a9012c`).
