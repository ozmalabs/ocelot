# BIGVILLE RUNG 1 of 3 — THE HELD BOND — PRE-REGISTRATION

**Block 277000. Pre-registered BEFORE any recorded number.** Design blueprint:
`BIGVILLE_SPEECH_SCIENCE.md` — Addendum 2 (§A1–A8 relationship as held
feeling+belief), Addendum 3 (§B1–B9 the social spectrum + small-community
gossip/reputation), Addendum 4 (§C1–C8 attraction as a signed approach–avoidance
slot). This is rung 1 of a 3-rung build (Bond → emergent speech → attraction-driven
movement/pairing). Rungs 2 and 3 will READ this Bond; its slots are shaped so they can.

## The problem this fixes (creator's directive)
> "the relationship system needs to move out of the sim as simple edges and into
> the agent graphs as complex feelings and held beliefs."

Today a relationship is a bare, **symmetric, static WORLD edge** (`A ─kin/hates→ B`).
It must become a **per-agent, DIRECTED, subjective, updatable HELD** representation
(§A5: A→B ≠ B→A; can diverge from reality and from B's bond).

## Seed-claim (verbatim `check_claim`, run before anything)

```
SEED CLAIM 277-277: CLEAN -- no collision DETECTED.
  Scope: 980 files with seed sinks; 699 UNRESOLVED sink sites tree-wide (counted, not discarded).
SEED CLAIM 277000-277999: CLEAN -- no collision DETECTED.
  Scope: 980 files with seed sinks; 699 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER ... measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN ... 'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## The representation (graph-native, ZERO new Rust)

A directed **`Bond`** node A HOLDS about each known B, minted by the adapter from the
kin/hates PRIOR (§A6.4, §B7.1: the bare edge is the *initial condition*, never the
representation). Edges: `A -holds_bond-> Bond`, `Bond -toward-> B`,
`Bond -has_gen-> DispositionGenerator` (per-bond ToM codebook), `Bond -has_event-> AppraisedEvent`
(the grounding trace — §A6.3), `Bond -has_gossip-> Gossip`. THREE dissociable slots
(§A4: cognitive vs affective ToM dissociate; §C3: approach–avoidance is a distinct layer):

1. **Belief slot (ToM disposition, §A4/§A6.1).** `belief_disposition` + `belief_trust`
   — A's running disposition-model of B, an ABDUCTIVE DECODE that **generalizes
   `bd_mary_infers`** ("Mary about John") to "any A about any known B": `bond_belief_infer`
   Argmaxes over the bond's held `DispositionGenerator` codebook by fit to B's observed
   harm signature (`-|predicts_harm_rate − observed_harm_rate|`) — the SAME held-codebook
   decode, now per-Bond. NOT ground truth (§A5).
2. **Relational-affect slot (§A2/§A6.2).** SIX signed relational emotions with action
   tendencies — `affect_trust`, `affect_gratitude`, `affect_resentment`, `affect_contempt`,
   `affect_affection`, `affect_fear` — NOT a single like/dislike scalar (Lazarus core
   relational themes; individuated by attributed agency).
3. **Attraction slot (§C3/§C6.1).** ONE signed approach–avoidance `attraction` valence
   (+ approach / − avoidance — repulsion is the NEGATIVE POLE of the one axis, NOT a
   separate mechanism; Rosenbaum's strong repulsion FAILED to replicate, §C2) with a
   dissociable `romantic` sub-value (Fisher's three systems, §C4). **Rung 3 reads
   `attraction` to drive movement/pairing.**

Plus **structure**: a continuous `tie_strength` + a bucketed `band_code`
(rival/stranger/consequential_stranger/acquaintance/friend/intimate — §B2 the graded
spectrum; MOST bonds are weak) from interaction frequency × closeness; and the
`has_event` edges ARE the grounding trace (why A feels this, §A6.3).

## The UPDATE dynamics ARE RULES — `seeds/bigville_bond_update.json` (self_load_only)

Every DECISION is a seed rule composing existing DSL Terms (Attr/Plus/Times/Minus/
Gt/Eq/And/IfThenElse/Abs/Argmax/Neighbours) — the exact palette of `af_choose_action`
and `bd_mary_infers`. The adapter ONLY ingests events, stamps proximity/similarity/
source-trust inputs, arms one-shots, ticks, and reads back.

- **`bond_belief_infer`** — the generalized ToM decode (above).
- **`bond_event_benefit`** (§A3 reciprocity) — a positive appraised event by B toward A
  (a kindness, a gift) raises gratitude/trust/affection/attraction/tie_strength by
  `update_gain·pos_weight·magnitude`.
- **`bond_event_betrayal`** (§A3 negativity bias, "bad is stronger than good") — a
  negative event (a loan default, an eviction) LOWERS trust+attraction by
  `update_gain·NEG_weight·magnitude` where **`neg_weight > pos_weight`**, raises
  resentment/contempt, drops belief_trust, and triggers a **global re-appraisal**
  (existing affection+gratitude scaled by `reappraise_factor<1`, not a single decrement).
  **The magnitudes are TUNABLE KNOBS — no magic ratio is hard-coded** (Gottman 5:1 is
  contested; only the *direction* of the asymmetry is encoded, §A7).
- **`bond_gossip_update`** (§B4 indirect reciprocity / §B7.3) — GENERALIZES the reputation
  loop (`bl_badmouth`/`bl_townsfolk_opinion`): C tells A about B; A revises Bond(A→B)'s
  belief/affect/attraction by `update_gain·content_valence·source_trust·gossip_weight`.
  `source_trust` = A's trust in C (read by the adapter off Bond(A→C) — a graph read, not a
  decision), so gossip is EVIDENCE WEIGHTED BY THE SOURCE, never ground truth. The INDIRECT
  path: A updates B WITHOUT directly experiencing B — the engine of a small community.
- **`bond_similarity_attraction`** (§C1 homophily, §C2 asymmetry) — attribute overlap
  raises `attraction`; dissimilarity lowers it weighing slightly more (`dissim_weight >
  sim_weight` — the *defensible residue* of the repulsion hypothesis, NOT its strong form).
- **`bond_proximity_familiarity`** (§C1 mere-exposure, §B7.1) — benign co-presence
  frequency drifts `tie_strength` and `attraction` up (with the familiarity-breeds-contempt
  caveat: exposure DEEPENS an already-negative attraction, Finkel 2015).
- **`bond_band_assign`** (§B2) — buckets `tie_strength`/`attraction` into `band_code`
  (rival if very avoidant, else the tie-strength ladder). A derived read.

The kin/hates edges are read ONCE by the adapter as the seed prior (kin → elevated
affection/attraction/tie_strength; hates → resentment/negative attraction/rival); the
RULES elaborate it. Kin is a PRIOR, not a guarantee (Hamilton, §A3) — it still updates.

## Pre-registered gates (`tests/test_bigville_bond_migrated.py`)

- **G-forms** — a Bond FORMS directed from a kin prior with all THREE slots populated and
  is ELABORATED (belief_disposition inferred by the decode; band assigned by the rule).
- **G-asymmetry** — after the SAME betrayal event by B toward A, Bond(A→B) ≠ Bond(B→A):
  A's trust/attraction toward B drop while B's bond toward A is unmoved (A→B ≠ B→A, §A5).
- **G-dynamic-asymmetric** — a betrayal of magnitude M drops trust+attraction HARDER than
  a kindness of the SAME magnitude M raises them (|Δ_betrayal| > |Δ_kindness|, negativity
  bias); before/after slot values reported.
- **G-third-party** — C's gossip about B shifts A's Bond(A→B) belief/attraction WITHOUT A
  directly experiencing B, weighted by A's trust in C (a distrusted source moves it less).
- **G-falsifier (the anti-"forced" control)** — with `update_gain=0` on every bond, NO
  event / gossip / similarity / proximity moves ANY slot: every Bond stays frozen at its
  static seed prior, reproducing the OLD bare-label behavior. The SAME events that move the
  bonds with the knob on leave them frozen with it off — proving the bonds are genuinely
  dynamic (mirrors `af_choose_action`'s `affect_gain` falsifier).
- **G-source-audit** — the decisions are RULES: the update seed holds ≥7 `bond_*` rules;
  the adapter contains no `graph_rewrite`/`gr.run`/`_match`/`_apply`/`make_rule` and no
  if/else over an agent's graph valuation that selects an update.
- **G-discipline** — base `b53bdacae0`; `git diff b53bdacae0 -- runners/dsl` EMPTY; no
  committed `.so`; `test_failure_baseline_migrated` green (fail-set ⊆
  `results/failure_baseline.json`); ZERO new reds; prereg hash + build hash recorded.

## Tunable knobs (declared config — the DIRECTION is the science, the magnitude is soft)
`update_gain=1` (falsifier→0), `pos_weight=1`, **`neg_weight=3`** (bad-is-stronger, §A3/§A7
CONTESTED magnitude — a knob, not a law), `reappraise_factor=0.5`, `gossip_weight=0.5`,
`sim_weight=1`, `dissim_weight=1.5` (§C2 residue), `exposure_weight=0.2`,
`rival_thresh=-1.5`. All are graph attrs read by the rules.

## Honest scope (pre-committed)
Synthetic mechanism demo (a focused 3–4 agent scene, NOT the full town) — mechanism-proven
≠ benchmark value. Rung 1 delivers the REPRESENTATION + its update dynamics; emergent speech
(rung 2) and attraction-driven movement/pairing (rung 3) READ it and are built later. The
romantic sub-value is carried as a slot but its courtship→pairing consumer is rung 3.
Additive only: new `seeds/bigville_bond_update.json`, `worlds/bigville_bond_world.py`,
`tools/author_bigville_bond_seeds.py`, `tests/test_bigville_bond_migrated.py`, this prereg,
results. NO tracked seed edited. ZERO new Rust.
