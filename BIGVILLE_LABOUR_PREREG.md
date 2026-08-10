# PREREG — block 303000: labour mobility + role-identity friction (economy R4)

`PRODUCTION_ECONOMY_PLAN.md` R4 -- the self-balancing loop, and the rung the whole
economy was building toward. Roles are seeded but NOT fixed: a worker switches to
a better-paying job, resisted by how strongly it HOLDS its role (the Roy
occupational-choice model; role_identity = the switching friction).

## Graph data + rules (`bigville_labour.json`)

- `Job{trade, revenue, crowd, wage, n_workers}`. `Worker{role, role_identity,
  can_switch}` with `works_as -> Job`, `in_town -> Town{friction_scale}`.
- `lm_wage`: `wage = revenue - crowd * n_workers` (n_workers = Count of incoming
  `works_as`). Crowding LOWERS the per-worker wage -- the balancing term.
- `lm_switch`: a worker switches to the BEST-paying job iff
  `best_wage - current_wage > role_identity * friction_scale`. Owners (high
  role_identity) are sticky; labourers (low) are mobile. Gated on a per-worker
  `can_switch` turn token so the adapter serialises one move at a time (wages
  recompute between moves) -- without it, many workers flip on the same wages and
  oscillate (a concurrent-switch race). The DECISION is the rule; the adapter
  only schedules turns and reads state (no wage comparison in Python).

## Gates (pass/fail, pre-registered) — the balance EMERGES, untuned

1. **G-self-balancing (HEADLINE):** start everyone in one over-supplied trade
   (equal revenues) → labour redistributes and the trades' wages EQUALIZE within
   the friction band. The over-supply self-corrects to steady state.
2. **G-owner-sticky:** with a moderate wage gap (above a labourer's friction,
   below an owner's), a low-role_identity labourer SWITCHES to the better job
   while a high-role_identity owner STAYS. Role-identity is the friction.
3. **G-wage-gap-pulls:** labourers in a low-wage trade move toward a higher-wage
   trade.
4. **G-market-clears:** settle CONVERGES (a sweep with zero moves) -- at
   equilibrium no worker can improve by more than its friction. It does not
   oscillate forever.
5. **G-proportional:** more labour ends up in the higher-revenue trade (labour
   concentrates where the return is higher, until wages equalize within friction).
6. **G-no-python-decision (source audit):** the adapter contains no wage
   comparison / switch decision; it only sets the `can_switch` turn token, runs
   the fixpoint, and reads roles. The switch is the seed rule.

## Scope / honesty
- R4 demonstrates the labour-market clearing on abstract `Job{revenue}` nodes.
  Coupling `revenue` to the LIVE economy (a trade's revenue = its emergent price
  x throughput from R2/R3, so scarce fish → high fish price → high fishing
  revenue → labour inflow) is the fold-in (R5) into the 100-resident town, using
  the cast's per-resident `role_identity`.
- Standalone demonstrator (no map -- mobility is not spatial); no Rust; `.so`
  untouched. friction_scale / crowd / revenue are inputs; the equilibrium split
  and equalized wages are what FALL OUT.
