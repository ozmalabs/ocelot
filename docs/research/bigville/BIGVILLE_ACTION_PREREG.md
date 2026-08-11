# PREREG — block 330000: the cost & impact of action (C6)

The cognitive core's actions are still *free* — satisfying a drive is a bare `set_level`,
work produces nothing. The missing capability is the **thermodynamics of agency: every
action expends a resource and produces an effect, and both are conserved. Nothing is free;
work changes the world.** This closes C1's drive loop — working *costs energy*, which
depletes, so the agent must *eat*, which *consumes food someone had to produce* — with no
creation from nothing. It grounds the abstract drives in real expenditure and output, and
extends the substrate's standing conservation (Σ-coin, resource stock) to cognition.

## The mechanism (`bigville_action.json`)

- **`ac_work`** — a working agent with enough `energy` extracts from a `Deposit`
  (partial-take `output = min(yield, stock)`, so it can't over-extract) → **spends
  `work_cost` energy** and **deposits `output` into the food `Store`**. Work has a **cost**
  (energy falls) and an **impact** (store rises); the output is **conserved** from the
  deposit (deposit falls by exactly `output`); an empty deposit yields nothing, and an
  agent with `energy < work_cost` cannot work.
- **`ac_eat`** — a hungry agent with food available **consumes one unit** (`store.stock −=
  1`), reducing `hunger` and restoring some `energy`. **Recovering the drive costs a real
  resource** that must exist — you cannot satisfy hunger for free, and the food is conserved
  (the store falls by exactly what is eaten).
- **`ac_rest`** — restores `energy` (capped) — recovery still takes an act.
- **`ac_metabolize`** — per metabolic epoch, `energy` drains and `hunger` rises: the **cost
  of merely living**, which forces the work→eat loop (an idle agent runs down).

## Gates (pass/fail, pre-registered)

1. **G-work-costs-energy (HEADLINE):** working deducts `work_cost` from the actor's energy;
   an agent with `energy < work_cost` **cannot work** (energy unchanged, no output).
2. **G-work-has-impact (HEADLINE):** working **produces output** — the food store rises,
   drawn (conserved) from the deposit; an **empty deposit yields nothing** (no input → no
   output).
3. **G-recovering-costs (HEADLINE):** eating reduces hunger but **consumes a food unit**
   (the store falls); with **no food, hunger cannot be reduced** — no free recovery.
4. **G-conservation:** the amount extracted equals the deposit's decrease equals the store's
   increase (no creation from nothing); food eaten equals the store's decrease.
5. **G-the-loop-is-not-free (falsifier):** with metabolism ON, an idle agent's energy runs
   to zero and hunger climbs — it **must** work and eat to sustain; with metabolism OFF it
   coasts, showing the cost is what forces the loop.
6. **G-no-python-decision (source audit):** work/eat/rest/metabolize are the seed rules; the
   adapter arms actions, pulses metabolism, and reads.

## Scope / honesty
- This is a self-contained action-economy demonstrator; wiring it so that C1's *drive* mints
  the goal that *chooses* the action (work vs eat vs rest) and C2's *focus* multiplies the
  work output is the integration fold-in.
- Extraction uses the partial-take `min(yield, stock)` (the R1 conservation fix); the deposit
  regenerating over time is the existing `resource_extract` faculty, not re-implemented here.
- Energy/food are conserved across the cost/impact; "energy → food-stock → energy" is an
  efficiency loop, not a free multiplier (the net depends on the recipe, which is data).
- Isolated demonstrator (`self_load_only`); no Rust; `.so` untouched (`a8a9012c`).
