# PREREG — block 300000: resource base + extraction (production economy R1)

`PRODUCTION_ECONOMY_PLAN.md` R1. Ground the economy in materials: fish / lumber /
stone deposits on the map that a labourer walks to (the nav flood), extracts from,
and delivers to a store. Borrows Sugarscape **growback** as the supply balance.

## Graph data + rules (`bigville_resource_extract.json`)

- `Deposit{kind, stock, growback, capacity, grow_epoch}` at a cell; single kind,
  scalar stock. `Stock{kind, amount}` nodes hang off a `Store` (one per kind).
  A `Labourer` is a Mover (reuses the nav) with `carrying`/`carry_kind`/`yield`.
- `rx_growback`: a deposit with `stock < capacity` regenerates once per town epoch
  → `stock = min(capacity, stock + growback)` (Sugarscape growback).
- `rx_extract`: a labourer co-located with a deposit (`is_at` the same cell),
  armed and empty-handed, with `stock ≥ yield` → `stock -= yield`,
  `carrying = yield`, `carry_kind = deposit.kind`. Proximity-gated act.
- `rx_deliver`: a labourer co-located with a store, `carrying > 0`, matching the
  store's `Stock` node of that kind → `amount += carrying`, `carrying = 0`.

Every decision is a rule; the adapter navigates labourers deposit↔store (nav),
arms extract/deliver at co-location, bumps the epoch. Mechanical I/O only.

## Gates (pass/fail, pre-registered) — ANTI-TUNING: rates are SET, outcomes MEASURED

1. **G-extract-delivers (foundation):** a labourer walks to a deposit, extracts,
   walks to the store, delivers — the store's matching Stock grows and the deposit
   depletes by the extracted amount. Material is conserved (deposit loss = carried
   = store gain, no coin/material minted).
2. **G-growback-regenerates:** with no extraction, a drawn-down deposit refills
   toward `capacity` at `growback`/epoch and stops at `capacity` (never exceeds).
3. **G-sustainable-steady (HEADLINE):** when aggregate extraction/epoch ≤ growback,
   the deposit stock reaches a bounded steady state (does not trend to 0) over a
   long run — measured, not tuned.
4. **G-overextraction-depletes (the falsifier of "it always balances"):** when
   aggregate extraction/epoch > growback, the deposit stock trends to 0 and
   extraction stalls (nothing to take). The balance is a REAL constraint, not
   decorative — over-draw genuinely exhausts the resource.
5. **G-per-kind:** fish / lumber / stone flow to their own Stock buckets; a fish
   labourer never fills the lumber stock (kind-matched delivery).
6. **G-no-python-decision (source audit):** the adapter runs no rule engine and
   holds no if/else deciding extract/deliver/growback; those are the seed rules.

## Scope / honesty
- R1 delivers RAW MATERIAL to stores. Production CONSUMING it (the fishmonger
  needing fish), the transform/tradesman layer, prices, and labour mobility are
  R2–R4. Coin/wages are not yet coupled here (extraction is unpaid in R1; the wage
  loop lands with labour mobility in R4).
- Isolated demonstrator on the nav (`BigvilleMoveWorld`); no Rust; `.so` untouched.
- The growback/yield rates are demonstrator inputs; the GATE reports the steady
  state / depletion that FALLS OUT of them (sustainable vs over-draw), never a
  balance dialed to a target.
