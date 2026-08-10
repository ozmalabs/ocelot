# PREREG — the visiting market trader (bigville R29)

The outbound twin of the inn: a visiting merchant sets up a **stall** of wares,
sells into the town, and departs when sold out. It is the inn's mirror — the inn
brings external coin IN (lodging); the trader takes coin OUT (residents buy).

## v1 → v2 CORRECTION (block 318000)

v1 (block 317000) had the trader sell a **locally-priced** good and **undercut**
it. **Corrected** per the user: *the remote seller sells DIFFERENT goods that are
not locally available.* A remote merchant's value is **exotic** wares the town
cannot make itself — there is no local price to undercut. So the model is now:
the trader deals **only in goods with no local producer**, he is the **sole
source**, and the town **gains access to a good it otherwise could not have**. The
undercut rule is retired (a good with no local substitute has nothing to undercut).

## The mechanism (`bigville_market_trader.json` v2)

The town `produces` a set of `LocalGood`s (fish, lumber, stone, …). A `Trader`
(external agent) sets up a `Stall{good, stock, ask_price}`. Rules:

- **`mt_open`** — a stall opens for trade **iff its good is NOT locally produced**
  (no `LocalGood` of that name). Exotic ⇒ open.
- **`mt_refuse_local`** — a stall whose good IS locally produced is **refused** (it
  never opens) — the remote seller does not deal in what the town already makes.
- **`mt_grant_access`** — an open (exotic) stall gives the town **import-access**:
  the good is recorded as an `ImportedGood` the town now holds (once) — the town's
  available-goods set GROWS by import, disjoint from what it produces.
- **`mt_buy`** — a resident armed to buy, who **wants** the good and can **afford**
  the ask, buys one unit from an **open** stall with stock: coin leaves the
  resident to the external trader, holding +1, stock −1, want −1, and
  `town.external_outflux` LOGS the boundary crossing (the mirror of the inn's
  influx). One unit per arming; the adapter serialises buyers so stock never races
  negative. The visiting trader is the **only** way to obtain the good.
- **`mt_depart`** — a sold-out stall is struck and the trader departs (remembered).

## Gates (pass/fail, pre-registered)

1. **G-sells-exotic (HEADLINE):** a stall of a good with no local producer opens and
   sells; buyers acquire a good they could not otherwise get; coin leaves to the
   trader.
2. **G-refuses-local (HEADLINE):** a stall of a locally-produced good never opens
   and makes no sale — the remote seller deals only in what is unavailable locally.
3. **G-sole-source:** the town has no local producer of the exotic good and no buyer
   held it before; the only way to obtain it is the visiting trader.
4. **G-grows-available-goods:** the town's imported-goods set gains the exotic good
   (readable: `produces` vs `imports_good`, disjoint; the import is new).
5. **G-coin-leaves-the-town (boundary):** the coin buyers pay equals `external_outflux`
   equals the trader's take — the closed economy leaks exactly the sales.
6. **G-sells-out-and-departs:** an exhausted stall is struck and the trader departs;
   stock never goes negative (no overselling — the race gate).
7. **G-no-python-decision (source audit):** open/refuse/grant/buy/depart are the
   seed rules; the adapter mints goods/trader/stall, serialises buyer turns, ticks,
   and reads.

## Scope / honesty
- Buying from the sole visiting stall is an affordance reflex; choosing **among
  competing sellers** (rival traders of the same exotic good undercutting each
  other) would be a decision-by-collapse — the natural extension, deferred.
- The exotic good's price is the trader's ask (scarcity/no local substitute); a
  dynamic scarcity premium is deferred.
- Isolated demonstrator (`self_load_only`); composes conceptually with the
  production economy; no Rust; `.so` untouched (`a8a9012c`).
