# PREREG — block 294000: townspeople GO TO the publisher to report (Rung B)

`NEWSPAPER_WRITER_PLAN.md` **Rung B**. The town gains the second faculty: a
resident with something salient it holds goes and REPORTS it — via GENERAL
directed conduct + the nav flood — to whoever affords making-things-known. "Know
to go to him" is not a hardcode.

## What this delivers (graph data + rules, built on the real nav)

Built on `BigvilleMoveWorld`, in the SAME substrate as the nav, so "go to him" is
the REAL flood (blocks 291000/292000):

- `rep_form_report_goal`: a Mover holding a SALIENT, not-yet-reported `Fact` sets
  its own `seeks` edge to the cell of whoever `affords makes_known`, and marks
  `report_intent`. The target is chosen by the AFFORDANCE ("find who affords
  making-things-known"), never a reporter identity. The `seeks` edge IS the nav
  goal — the unchanged flood then routes the mover there.
- `rep_deliver_on_arrival`: when the reporter and the afforder are co-located
  (both `is_at` the same cell), the afforder `received` the Fact and it is marked
  reported. Directed, proximity-bound conduct — it cannot fire at a distance.

The adapter mints movers/facts/affordance and ticks movement + rules; every
decision (who reports, to whom, when to deliver) is a rule.

## Gates (pass/fail, pre-registered)

1. **G-report-delivered (HEADLINE):** a reporter far from the publisher forms the
   report goal, WALKS to the publisher's cell (position changes from start toward
   the afforder), and on arrival delivers — the publisher `received` the fact.
   The fact travelled the map to reach him.
2. **G-no-afforder (target-bound):** ablate the `makes_known` affordance → no
   afforder to target → no report goal is formed, the reporter does not move, and
   nothing is delivered. Reports need somewhere to go.
3. **G-travel-bound:** with movement ablated, the reporter still forms the intent
   (it WANTS the thing known) but never reaches the publisher → no delivery.
   Delivery depends on actually travelling there — proximity-bound like every
   other conduct.
4. **G-two-reporters (generality):** two residents, each holding a salient fact,
   both walk to the same publisher and both deliver — nothing is special-cased to
   one reporter.
5. **G-no-python-decision (source audit):** the adapter contains no rule-engine
   call and no `if` over graph state deciding who reports / when to deliver; the
   report goal + delivery come only from the seed rules.

## Scope / honesty

- Rung B DELIVERS the fact to the publisher (the publisher `received` it). Turning
  that received fact into the publisher's HELD BELIEF (testimony-bound,
  anti-confabulation) is Rung C; rendering it as prose is Rung D. This rung stops
  at delivery.
- Isolated demonstrator + seed + test; no Rust; `.so` untouched. The live integ3
  weekly f-string is not touched by this rung.
- The reporter's fact carries a `desc` string (e.g. "a foreclosure on Elm
  Street") purely so later rungs (C hold, D render) have real content to hold and
  write — Rung B does not read or render it, only carries and delivers it.
