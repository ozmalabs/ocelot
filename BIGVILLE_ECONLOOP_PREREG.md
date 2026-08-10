# PREREG — block 304000: the closed self-balancing loop, on the real cast (economy R5)

`PRODUCTION_ECONOMY_PLAN.md` R5 -- the grand fold-in. Compose resource supply +
emergent price (R3) + labour mobility (R4) into ONE closed loop, driven by the
seeded 100-resident cast's labour pool and per-resident `role_identity`.

## The loop (`bigville_econloop.json`)

Per tick: `ec_extract` (supply = min(stock, n_workers*yield); deposit regrows by
growback - supply, clamped) → `ec_price_glut`/`ec_price_scarce` (the good's market
price falls if supply>demand, rises if supply<demand) → `ec_wage` (wage =
price*yield - crowd*n_workers) → `ec_switch` (a worker moves to the best-paying
trade net of role_identity friction). The negative feedback: scarce good → high
price → high wage → labour IN → more supply → price DOWN → labour OUT →
equilibrium at supply ~ demand. `crowd` is the fast within-tick congestion damper;
`price` is the slow across-tick market signal.

## Gates (pass/fail, pre-registered) — stability is MEASURED, not dialed

1. **G-stable-equilibrium (HEADLINE):** starting from the cast's UNBALANCED labour
   (many in fishing, few in quarrying), the loop CONVERGES to a bounded steady
   state -- headcounts settle (small spread over the last ticks) and wages
   equalize within the crowd band. No explosion, no collapse.
2. **G-self-balances:** labour redistributes from the over-crowded trade toward
   the under-worked ones (the initial imbalance is corrected).
3. **G-shock-response (HEADLINE):** collapse one trade's resource at equilibrium →
   its good becomes scarce → its PRICE RISES and labour FLOWS INTO it (the full
   price → wage → mobility loop closes on a perturbation).
4. **G-material-bounded:** every deposit stays in [0, capacity] throughout (no
   negative stock, no overflow) -- material stays physical.
5. **G-crowd-is-load-bearing (falsifier):** with `crowd = 0` the same loop does
   NOT stabilise -- the whole mobile pool herds to one trade each tick and
   OSCILLATES (headcounts swing widely). This proves the crowding damper is what
   makes it converge, not luck.
6. **G-no-python-decision (source audit):** extract/price/wage/switch are the seed
   rules; the adapter only advances the tick, schedules one switch-turn per
   worker, and reads state.

## Scope / honesty
- This runs the closed loop at the TRADE-AGGREGATE level (extraction rate =
  n_workers*yield), driven by the real cast's role_identity. It does NOT run 100
  agents navigating the 52x40 map per tick -- that spatial/real-time layer (R1's
  walk-to-deposit x 100, the watchable townview) is a separate scale/perf concern
  (the "real-time scale ceiling" is an explicitly unproven axis). The DYNAMICS
  (stability, self-balance, shock response) are what R5 measures.
- The absolute wage/price levels are a function of the labour-vs-demand ratio
  (oversupplied labour floors prices; wages can go low). The GATE is on the
  dynamical behaviour (converges / self-balances / responds), never on a target
  number -- anti-tuning.
- Isolated demonstrator; no Rust; `.so` untouched.
