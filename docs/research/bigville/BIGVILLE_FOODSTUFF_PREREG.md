# PREREG — block 333000: the food lifecycle — storage, spoilage, preparation, quantization

Nutrition (332000) modelled *what* a food is; this rung models its *lifecycle*: food is
**stored** (a larder with capacity and cold), **spoils** over time at kind-specific rates,
must be **prepared** (raw → cooked; some foods inedible raw), and is **quantized** into
discrete integer **portions** — you hold 3 loaves, not 3.7. Quantization here is the
substrate's own invariant: *in-frame quantities are integer* (a counted stock is a
quantum count, not a continuum).

## The mechanism (`bigville_foodstuff.json`)

A `FoodItem{kind, state (raw|prepared|spoiled), freshness, portions}` (portions an integer)
held in a `Larder{cold}`; a `Kitchen{fuel}` prepares.

- **`fs_spoil`** — per epoch, `freshness −= spoil_rate · (cold ? cold_factor : 1)` (kind-
  specific: fish spoils fast, grain slowly, preserved/salted slowest; cold storage slows it).
- **`fs_rot`** — when `freshness` reaches ~0 the item becomes `spoiled` (inedible).
- **`fs_prepare`** — a **raw** item, given a Kitchen with **fuel**, becomes **prepared**:
  taste improves, freshness lifts, `fuel` is spent. Some foods (grain) are **inedible until
  prepared** (baked into bread).
- **`fs_eat`** — consume exactly **one portion** iff the item is **edible** (not spoiled, and
  prepared if it needs preparation); `portions −= 1`; the meal's value scales with freshness.
- **`fs_reject`** — otherwise (spoiled, raw-when-preparation-is-required, or empty) the meal
  is refused — no free nutrition from rotten or raw food.

## Gates (pass/fail, pre-registered)

1. **G-quantized-portions:** a stack holds an **integer** portion count; each eat consumes
   **exactly one**; an empty stack cannot be eaten (in-frame quantities are integer).
2. **G-spoilage-rates:** over the same epochs, a **fast-spoiling** food (fish) loses freshness
   faster than a **slow** one (grain); a **preserved** food (salt-fish) barely spoils.
3. **G-cold-storage-preserves:** the same food in a **cold** larder retains more freshness than
   one left warm.
4. **G-preparation (HEADLINE):** a food that requires preparation is **inedible raw** (eating
   it is rejected) and **edible once prepared**; preparation **improves its taste** and
   **spends kitchen fuel**.
5. **G-spoiled-is-inedible:** once an item spoils, eating it is **rejected** — no nutrition from
   rotten food.
6. **G-no-python-decision (source audit):** spoil/rot/prepare/eat/reject are the seed rules;
   the adapter mints items with their physical properties, pulses time, arms preparation and
   eating, and reads.

## Corrections (block 334000) — three user corrections folded in

The 333000 mechanism smuggled three assumptions; all three are now driven properly:

1. **Food is prepared by a COOK (an agent, with skill), not by a kitchen.** `fs_prepare`
   now requires a `cook -using-> kitchen` edge; the meal's **quality = the cook's
   `cook_skill`** (a skilled cook draws out more taste and lifts freshness more), the cook
   **spends energy/effort** and **learns by doing** (`cook_skill += learn_rate`, capped),
   and the meal records **who made it** (`prepared_by`). A kitchen with no cook does nothing
   — agency belongs to the agent, never the appliance.
2. **Agents quantize their own food (dynamic, re-quantizable).** A `Household{food, shares}`
   divides its food among its members — `hq_ration`: `per_member = food / max(1, shares)`.
   A poor family splitting **one loaf four ways** gets 0.25 each; the household can
   **re-quantize** (a guest arrives → `shares = 5` → 0.2 each). Quantization is the agent's
   own choice, not a fixed integer unit.
3. **Spoiled food does NOT disappear — it persists, grades badly, and sickens.** `fs_eat`
   no longer hard-rejects spoiled/raw food (`fs_reject` → `fs_nofood`, which fires only on an
   **empty** stock). A meal is **graded against an eater**: nutrition = `energy·freshness·
   (raw_penalty if uncooked)` → **less nutritious** as it spoils; pleasantness =
   `taste·freshness − disgust(if spoiled)` → **more unpleasant**; `illness += (1−freshness)·
   rot_illness (+ raw_illness)` → a **chance of illness**, accruing cumulatively. A desperate
   agent *can* eat rotten food — it just feeds them poorly, tastes foul, and may make them
   sick. Per-eater "hardiness" params make a hardy stomach differ from a delicate one.

## Correction (block 335000) — preparation needs an AGENT, not a kitchen

The 334000 `fs_prepare` still smuggled a kitchen (it required `cook -using-> kitchen`). Corrected:
**preparation requires an AGENT; a kitchen is never required.** Food is prepared *anywhere* —
`agent -preparing-> item`, `agent -using-> station`, where a `Station{heat, prep_power, fuel}` is
an **optional** surface: **bare hands / the ground** (heat 0, no bonus) is always available, a
**bench** adds prep_power without heat, a **fire or stove** adds heat (and burns fuel). Two prep
kinds:

- **`season`** (add spices) needs **no heat** — done on bare hands, the ground, anywhere; it lifts
  taste but does not cook (raw stays raw).
- **`cook`** needs a **heat source** (`station.heat >= 1`) — makes needs-prep food edible, lifts
  freshness, burns the station's fuel.

Quality = `cook_skill · (1 + station.prep_power)` (a better surface draws out a better meal:
stove > hearth > bench); the cook still spends energy and learns by doing. New gates:
prep-needs-an-agent-not-a-kitchen (season fish on bare hands), cooking-needs-heat (grain stays raw
on bare hands, cooks at a fire), a-better-station-helps (stove beats a plain hearth). The source
audit now asserts the match requires `[agent, preparing, item]` and mentions **no** kitchen.

## Scope / honesty
- Portions are a single integer per stack (a quantum count); modelling individual sub-item
  variation (each loaf its own freshness) is a refinement.
- Larder capacity is read/soft here (a `capacity` attr + load read-off); enforcing over-capacity
  → faster spoilage is a light coupling, flagged for the follow-on.
- Preparation is a single raw→prepared transition with a taste/freshness lift; multi-step recipes
  (grind → dough → bake) and fuel/skill grades are refinements.
- Composes with nutrition (332000): the `fs_eat` meal value (`energy · freshness`) is the input
  to `nu_eat`'s nutrition; the fold-in wires the two.
- Isolated demonstrator (`self_load_only`); no Rust; `.so` untouched (`a8a9012c`).
