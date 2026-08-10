# PREREG — block 310000: the legislature + the council's routine acts (bigville R23)

The council held only *numbers* (blocs, standings). This rung gives it what a
council is FOR: it sets the actual policy the town runs on, and it makes the
day-to-day proclamations. Two frequencies, per the design:

- **THE NORM (every meeting).** The council issues `CouncilAct{kind:
  decision|statement|censure}` that get **posted** to the noticeboard and read
  into the paper. Decisions and statements are content; a **censure** naming a
  person has a real effect — `ca_censure_effect` lowers that person's standing.
- **THE RARE ACT.** Changing a **law**. Laws are named, valued, first-class
  objects in a `LawBook` (`Law{name, value, status}`). A `Bill{action:
  enact|amend|repeal, target, new_value}` is **voted** on by councillors by bloc
  interest, **passes** at a threshold, and is **applied** to the book. Laws have
  **real effects**: an active `land_tax` law's `value` is what the treasury
  charges each resident; repeal it and no tax is taken; amend it and the take
  changes.

## The rules (`bigville_legislature.json`) — every decision is a rule

`leg_vote` (a councillor votes FOR a pending bill iff `c.bloc == bill.aids_bloc`,
one vote each) → `leg_tally` (`votes_for = Count(InNeighbours votes_for)`) →
`leg_pass` (`votes_for >= threshold` → passed) → `leg_amend` / `leg_repeal` /
`leg_enact` (apply the passed bill to the book) ; `law_tax_charge` (the effect —
armed treasury, each resident pays the active land_tax value once) ;
`ca_censure_effect` (a posted censure lowers its target's standing once).

## Gates (pass/fail, pre-registered)

1. **G-vote-by-bloc (HEADLINE):** a tax-relief bill (`aids_bloc=poor`) collects
   exactly the poor-bloc councillors' votes and no others; a bill that reaches
   its threshold PASSES, one below it stays pending.
2. **G-amend-changes-the-take (HEADLINE):** with a `land_tax` law active, amend
   its value via a passed bill → the treasury's per-resident take changes to the
   new value on the next collection. The law is real.
3. **G-repeal-stops-the-effect:** repeal the `land_tax` law via a passed bill →
   the next collection takes **zero**. Removing the law removes its effect.
4. **G-enact-adds-a-law:** a passed enact bill mints a new named law into the
   book (idempotent on name — no duplicate).
5. **G-censure-bites:** a posted `censure` naming a person lowers that person's
   standing exactly once; a `decision`/`statement` posts content and changes no
   standing.
6. **G-below-threshold-no-change (falsifier):** a bill that does NOT reach its
   threshold leaves the law-book byte-unchanged — policy only moves when the vote
   carries.
7. **G-no-python-decision (source audit):** vote/tally/pass/apply/censure are the
   seed rules; the adapter only mints council/laws/bills/acts, arms a collection,
   ticks the fixpoint, and reads state (no rule engine, no `if/else` over graph
   state deciding an outcome).

## Scope / honesty
- Bloc voting is deliberately simple self-interest (`bloc == aids_bloc`); it is
  the mechanism, not a model of real deliberation. The point is that policy is
  graph-resident, valued, voted, applied, and consequential — not a Python knob.
- Isolated demonstrator (`self_load_only`); no Rust; `.so` untouched (`a8a9012c`).
