# PREREG — block 302000: emergent scarcity prices (economy R3)

`PRODUCTION_ECONOMY_PLAN.md` R3. A shop's price stops being a fixed attr; it
EMERGES from local supply/demand imbalance -- the decentralized Gintis/Sugarscape
mechanism in posted-price form. This is the scarcity signal R4's labour mobility
will ride.

## Graph data + rules (`bigville_prices.json`)

- `pr_note_unmet`: a co-located customer who armed a sale but found the shop SOLD
  OUT (`output==0`) records `unmet` demand on the shop (mutually exclusive with
  `tf_sell`, which needs `output>0`).
- `pr_scarce_raise`: `unmet` this epoch → `price += price_step` (once per town
  epoch via a `price_epoch` gate), clear `unmet`.
- `pr_glut_lower`: output piled `≥ glut_threshold` → `price = max(min_price,
  price − price_step)`, once per epoch.

The adapter sets the adjustment rates + the town link; the price MOVES only via
these rules.

## Gates (pass/fail, pre-registered) — price is MEASURED to emerge, not set

1. **G-scarcity-raises (HEADLINE):** demand > supply (many customers, a slow
   supplier) → repeated unmet demand → the price RISES above its start.
2. **G-glut-lowers:** supply > demand (fast suppliers, few customers) → output
   piles → the price FALLS, floored at `min_price` (never below).
3. **G-bounded (settles, not diverges):** under scarcity the price CLIMBS then
   PLATEAUS at a bounded level (it finds a clearing level; it does not run away to
   infinity).
4. **G-price-emergent (source audit):** the adapter sets only rates/state; the
   price is written solely by the seed rules from `unmet`/glut. No `price =`
   decision in Python over demand.

## Scope / honesty
- R3 gives the shop-side scarcity price. It does NOT yet feed back into who
  becomes a fisher (that is R4's labour mobility -- a high fish price → high
  fishing wage → labour inflow → supply up → price down, the negative-feedback
  loop). And input (raw-material) prices / wages are not coupled to the output
  price here.
- The adjustment is a coarse fixed-step posted-price rule (not the full
  geometric-mean-of-MRS bilateral form) -- adequate for the scarcity SIGN and the
  R4 loop; a finer price kernel is a later refinement.
- Isolated demonstrator on R2; no Rust; `.so` untouched.
