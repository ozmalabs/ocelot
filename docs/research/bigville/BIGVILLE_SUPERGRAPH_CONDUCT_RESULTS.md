# RESULTS — Supergraph conduct valuation (block 282000-a)

All seven signatures reproduce. **`test_bigville_supergraph_conduct_migrated.py`
9/9 + 281000 conduct 7/7 (parity source) + affordances 10 + decision core 11 +
baseline 11 = 48/48 on the canonical engine `fd82dc2978dbb055496dd82390ac2ebe`**.
`runners/dsl` diff EMPTY — ZERO new Rust. Prereg `BIGVILLE_SUPERGRAPH_CONDUCT_PREREG.md`;
design `TOWN_SUPERGRAPH_BRIDGE_DESIGN.md`.

## What landed

- `seeds/bigville_supergraph_conduct.json` — ONE rule `conduct_supergraph_value`
  replacing the three `conduct_couple_*` rules (281000):
  `plan_value = plan_base + (ep.w_supergraph · bond_w) · target_effect`,
  `bond_w = altruism_bias + k·affect_affection − k·affect_resentment`. Term shape =
  `bigville_coll_evict.json` `bc_pick_cheapest_hands` (the only existing
  multiplicative `w_supergraph·magnitude`). `self_load_only`.
- `worlds/bigville_conduct_world.py` — a `valuation` switch ("couple" [281000
  default] vs "supergraph"); the supergraph path publishes `target_effect` per
  directed DecAction and mints an `EmotionParams(w_supergraph)` node (the
  psychopathy knob) on the actor.

## The measured signatures

| # | signature | measured |
|---|---|---|
| 1 | byte parity on harm | supergraph == couple: harm→Rival **1.6**, harm→Friend **−1.9** (identical to 281000) |
| 2 | chosen-action parity | rival+friend → **help→Friend** (not harm); provoked rival → **harm→Foe, deepened=1**; neutral → **help** |
| 3 | directedness | harm→Rival > harm→Friend; help→Friend > help→Rival |
| 4 | psychopathy knob (NEW) | `w_supergraph=0` → every directed plan = plan_base (harm −0.40 == , help 0.60 ==); weights no one |
| 5 | altruism_bias revived (NEW) | kin prior 0.3, zero affect → help→Kin **0.9** > base 0.6 (care without liking) |
| 6 | spite = signed per-pair weight | resented foe → harm scored **above** its −0.40 base |
| 7 | FALSIFIER | `k=0 ∧ altruism_bias=0` → harm→R −0.40 == harm→F −0.40 (no directedness) |

## What this establishes

**Conduct now routes through the supergraph form, and it earns its keep.** The
three hand-tuned coupling rules collapse into ONE valuation that is the same shape
the emotion framework already uses for weighted collective cost
(`bc_pick_cheapest_hands`). Two capabilities the per-pair form unlocks that the
281000 coupling could not express:
- **the psychopathy knob** — a single per-agent `w_supergraph` that, at 0, removes
  ALL per-pair care regardless of any Bond (intact machinery, absent valuation —
  the documented `w_supergraph=0` phenotype, now reachable in conduct);
- **the revived `altruism_bias` slot** — a per-pair care prior dissociable from
  affect, so kinship/duty can weight a target you neither like nor resent ("you do
  not need to LIKE your kin"), and blood-kin's seeded 0.3 finally does work.

And **spite stops being a separate knob** — a resented rival simply has a negative
per-pair weight, which times a negative harm-effect scores harming them up. One
signed weight subsumes care and spite.

## Honest residuals (NOT patched)

- **NOT byte-identical to 281000 everywhere — it sharpens.** The harm values and
  every chosen action match exactly, but `help→rival` is MORE negative under the
  unified form (the single `bond_w` subtracts resentment from help too, where the
  281000 help rule used affection only). This changes no chosen action in any
  tested scene; it is arguably more correct (you help a resented rival even less).
  This is a reformulation, not a byte-mirror, and is reported as such.
- **`target_effect` is a stipulated action magnitude, not the target's real
  fulfilment readout.** Per the design doc (sec 6 gap 2), the adapter publishes a
  fixed per-action-type effect (harm −1.0 / help +1.0 / transfer +0.8); grounding
  it in the target's actual `em_fulfilment` response is a later rung.
- **The scoping half is deferred (282000-b).** This block is the pure-additive
  VALUATION reframe. "The town is ONE supergraph, each resident deciding at its own
  reference frame" is the per-actor scoping swap (`NodesOfType("DecAction")` →
  `Neighbours(m,"in_scene")`), which is the ONLY change that touches the gated
  279000 decision core — quarantined to its own version-bumped, byte-parity-gated
  step.
- **Still standalone.** Live integ5/town wiring + player viz remain deferred.
