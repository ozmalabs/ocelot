# A grounded, self-balancing production economy for bigville

The town has people, money, speech, governance, and a press — but no **stuff**.
Production conjures goods from labour; there is no natural-resource base, no
raw→good transformation, and roles are fixed Python labels. This ladder grounds
the economy in materials and lets it **balance itself**, borrowing the canonical
resource-ABM references rather than hand-tuning.

## The balancing principle (borrowed, not tuned)

From **Sugarscape** (Epstein & Axtell 1996) + **Gintis, "Emergence of a Price
System from Decentralized Bilateral Exchange"** (Mesa's `sugarscape_g1mt` is a
clean Python reference): balance is NOT a set of dialed numbers — it EMERGES from
three local mechanisms (which is this project's anti-tuning rule):

1. **Resource growback** — deposits regenerate at a rate; extraction ≤ growback →
   steady state, extraction > growback → depletion. The supply balance, measured.
2. **Emergent prices** — price = scarcity signal from decentralized exchange
   (Gintis: converges toward competitive equilibrium); scarce good → high price,
   automatically, no auctioneer.
3. **Labour mobility = the balancing loop** (Roy occupational choice) — a worker
   moves to the highest expected-wage job net of a SWITCHING FRICTION.
   **role-identity strength IS that friction**: high for owners (sticky), low for
   labourers (mobile). Closes the negative feedback: scarce fish → high price →
   high fishing wage → labour flows into fishing → supply rises → price falls →
   steady state. Nobody tunes it.

## Build ON what exists (dormant/ungrounded, not missing)

`bigville_coll_collect` (proximity-gated collect→deliver→pay-wage — the act
pattern), `econ_production`/`supply`/`exchange`/`debt` (the monetary loop, coin
conserved via WagePool), `land_market`/`land_tenure`. The affordance vocabulary
already has `extract_resource` and `transform`.

## Rungs (each: prereg → demonstrator seed+world+gate → measure → commit)

- **R1 (300000) — Resource base + extraction.** `Deposit{kind: fish/lumber/stone,
  stock, growback, capacity}` on the map; a labourer walks to a deposit (the nav
  flood) and extracts; delivers to a store. GATE: sustainable rate → steady state,
  over-extraction → depletion — the rates are set and the OUTCOME measured (not
  tuned to a target).
- **R2 (301000) — Production consumes raw material (`transform`, tradesmen).**
  `be_produce` requires the delivered input; carpenter lumber→furniture, mason
  stone→blocks, fishmonger sells delivered fish. GATE: cut the fish supply → the
  fishmonger's sales stop (the dependency is real, not decorative).
- **R3 (302000) — Emergent prices.** Price from scarcity (stock/MRS), not hand-set.
  GATE: a supply shock raises the good's price.
- **R4 (303000) — Labour mobility + role-identity friction (Roy).** Roles seeded
  but switchable; `role_identity_strength` = the switching friction (owners high,
  labourers low); a worker switches to the higher-net-wage job. GATE: a wage gap
  pulls labourers across jobs but an owner stays put; over-supply of a trade
  self-corrects to steady state (the negative-feedback loop closes).
- **R5 (304000) — Balance + fold into the live town.** The whole loop runs
  coin-conserved, reaches a MEASURED untuned steady state (no explode/collapse),
  wired into integ.

## Discipline
Graph-native (deposits/materials are nodes; extract/growback/transform/price/
switch are rules); measure-first; ANTI-TUNING ABSOLUTE (report the steady state
that FALLS OUT of the borrowed mechanisms — a dialed-in balance is worthless, per
the bigville-laws memory); demonstrator-first then fold-in; no Rust unless the DSL
truly can't express it.

Sources: Sugarscape (Epstein & Axtell 1996, *Growing Artificial Societies*);
Gintis, *The Emergence of a Price System from Decentralized Bilateral Exchange*;
Mesa reference impl `sugarscape_g1mt`.
