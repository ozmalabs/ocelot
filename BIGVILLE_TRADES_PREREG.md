# PREREG — block 301000: production consumes raw material + tradesmen (economy R2)

`PRODUCTION_ECONOMY_PLAN.md` R2. Production stops conjuring goods from labour; it
CONSUMES the raw material R1 delivers, and tradesmen TRANSFORM raw → other goods.
The headline: **the fishmonger can't sell fish nobody caught.**

## Graph data + rules (`bigville_trades.json`)

- `Shop{trade, input_kind, output_kind, recipe_in, recipe_out, price, open, coin}`
  with an input `Stock` (raw, filled by R1's `rx_deliver` — the shop plays the
  store role) and an output `Stock` (goods). A `Customer{coin, bought}`.
- `tf_transform`: an open shop with `input.amount ≥ recipe_in` consumes
  `recipe_in` raw and stocks `recipe_out` goods (carpenter lumber→furniture, mason
  stone→blocks, fishmonger fish→fish_ready). Gated by input availability.
- `tf_sell`: a co-located customer with coin buys ONE output good iff
  `output.amount > 0`; coin moves customer→shop (conserved). If output is 0 (no
  raw ever arrived) the sale CANNOT fire.

The adapter (on the R1 nav+extraction world) mints shops/customers, routes each
labourer to its shop, arms the sale act, reads state. No decision in Python.

## Gates (pass/fail, pre-registered)

1. **G-chain-sells:** fish extracted → delivered → transformed → sold; the
   fishmonger earns coin and customers receive goods (the full chain runs).
2. **G-no-fish-no-sale (HEADLINE):** cut the fish supply → input stays 0 → no
   transform → no output → NO SALE; shop coin 0, customers keep their coin. The
   supply dependency is real, not decorative.
3. **G-transform-general:** the carpenter (lumber→furniture) transforms and sells
   too — transform is a general raw→good op, not fish-specific.
4. **G-coin-conserved:** the shop's take equals the customers' total spend; every
   unit sold cost exactly `price`. No coin minted.
5. **G-no-python-decision (source audit):** the adapter runs no rule engine and
   holds no if/else deciding transform/sale; those are the seed rules; the sale is
   gated on output availability (the coupling).

## Scope / honesty
- R2 couples raw→good→sale. Prices are FIXED here (`price` attr); EMERGENT
  scarcity prices are R3, and labour mobility (who becomes a fisher when fish is
  scarce/dear) is R4. Shop `open` is set true to isolate the MATERIAL coupling
  (the keeper/business-hours coupling already exists in `econ_production`).
- Isolated demonstrator on R1; no Rust; `.so` untouched.
