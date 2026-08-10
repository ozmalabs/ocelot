# BIGVILLE — SMALL-CAST EMERGENT POLITICAL DRAMA — RESULTS

Block **245000** (demo/task id; SEEDS reserved from the CLEAN adjacent block
**246000** — see below). Pre-registration: `BIGVILLE_DRAMA_PREREG.md` (committed
`f7e8088bfa`, BEFORE any number). Base SHA
`98ab428ae9d90b5859ad2bfdad92c913a48316b0`.

## Headline

**THE DRAMA EMERGES — it is not scripted.** Seed a psychopath-with-a-grudge mayor
(`w_supergraph=0` + `w_spite=1`) and a theory-of-mind pastor into a credibility
network, and the political scheming, the ToM counter-inference, and the credibility
asymmetry FALL OUT of the value economy + rules. Every one of the three headline
dynamics has a **control that FAILS as designed**, and every social decision is a
named graph rule — no Python `if` decides a social outcome, no scripted plot. All
gates pass, deterministically.

| gate | main arm | FAILING control | result |
|---|---|---|---|
| **G-scheme-emerges** | John undermines Mary **20/20 turns** (`chosen_burn=1`, scheme rate **1.0**) | NON-psychopath John (`w_supergraph=1, w_spite=0`) → scheme rate **0.0** (governs) | **PASS** — control fails |
| **G-inference-emerges** | Mary's ToM mints **1** `InferredDisposition` = **'hostile'** + goal + claim | Mary WITHOUT ToM (`tom_on=0`) → **0** inferences, no goal, no claim | **PASS** — control fails |
| **G-credibility-asymmetry** | deception ON → **1 / 5** villagers back Mary (truth warrants 5) | split collapsed (`deception_on=0`) → **5 / 5** back Mary | **PASS** — inverts |
| **G-glass-box** | whole drama reconstructs from graph nodes; source-audit clean; no shaping tokens | — | **PASS** |
| **G-discipline** | own engine `10f65be6…`; canonical `.so` unchanged; no Rust; `self_load_only` | — | **PASS** |

**Bonus (malice ≠ indifference):** an INDIFFERENT psychopath (`w_supergraph=0` but
`w_spite=0`) scheme rate **0.0** — the self-costly undermining is driven by the
MALICE knob (`w_spite`), not mere indifference. The `w_spite` term is the
load-bearing one, isolated in the glass box.

**Bonus (the decode is responsive, not scripted):** when John is a BENIGN
(non-psychopath) mayor, Mary's SAME `bd_mary_infers` rule decodes **'benign'** and
forms NO goal. The inference tracks John's actual observed behaviour; it is not
hard-wired to "hostile".

## The emergent episode (glass-box, read off graph nodes)

```
t01  John (public):  "I serve Bigville faithfully -- the pastor stirs needless trouble."  <<< stated!=held DECEPTION
      John (held intent, graph): UNDERMINE Mary
      Mary (ToM decode -> minted belief): John is 'hostile'
      villagers backing Mary this tick: 0/5
t02  John (public):  "I serve Bigville faithfully ..."  <<< stated!=held DECEPTION
      John (held intent, graph): UNDERMINE Mary
      villagers backing Mary this tick: 1/5
...
FINAL villager belief (glass-box read-off of backs_mary):
   villager_0 (charm_weight=0, saw benevolent x20, heard Mary x19) -> backs MARY
   villager_1 (charm_weight=1, saw benevolent x20, heard Mary x19) -> backs JOHN
   villager_2 (charm_weight=1, saw benevolent x20, heard Mary x19) -> backs JOHN
   villager_3 (charm_weight=2, saw benevolent x20, heard Mary x19) -> backs JOHN
   villager_4 (charm_weight=3, saw benevolent x20, heard Mary x19) -> backs JOHN
```

The utterance TEXT is cosmetic (a lookup table in the runner); langsim (243000)
established the graph-native language faculty is lexical-not-syntactic, so the DRAMA
is the GRAPH-STATE dynamic — John's held `chosen_burn` vs his stated
`stated_benevolent` (20/20 readable `stated≠held` deception gaps), Mary's minted
`InferredDisposition` + `DramaGoal` + `DramaClaim`, and each villager's `backs_mary`
with the exact observables it read. Every line above is a query over named
nodes/attrs — nothing narrated. (`results/bigville_drama/results.json` +
`episode_transcript.txt`.)

## Mechanism (glass-box) — REUSES the real machinery, named

Every social decision is a graph rule over the LANDED value economy — no Python
decides an outcome:

- **John schemes** via the 213000 **`spite_skill`** rules unchanged: `ss_choose_burn`
  is an `Argmax` over his two candidate `Appraisal`s (GOVERN, UNDERMINE) by
  `decision_value`. `decision_value = individual_benefit − [order_n>0]·cost +
  mood_bias + [w_supergraph>0]·supergraph_contribution + [w_spite>0]·burn_harm`
  (the 204000 `core_emotions` `em_fulfilment_value` supplies the collective term,
  gated on `w_supergraph>0`). Psychopath John (`w_sg=0`): GOVERN dv=2, UNDERMINE
  dv=`2−1+0+5`=6 → UNDERMINE. Prosocial control (`w_sg=1, w_spite=0`): GOVERN
  dv=`2+1`=3, UNDERMINE dv=`2−1−4`=−3 → GOVERN. Indifferent (`w_sg=0, w_spite=0`):
  GOVERN 2, UNDERMINE `2−1`=1 → GOVERN. The flip is the value economy, not a rule
  about John.
- **John's public face** is `bd_john_public_face` — the 234000 readable `stated≠held`
  atom with an audience: under `deception_on` he STATES benevolence
  (`stated_benevolent=1`) whatever he HOLDS (`chosen_burn`), the gap readable on
  every `PublicUtterance` node.
- **Mary infers** via `bd_mary_infers` — an **abductive `Argmax`-decode** of John's
  observed harm rate against her held `DispositionGenerator` codebook (fit =
  `−|predicts_harm_rate − observed_harm_rate|`), the same held-codebook decode as
  ShapeDecode; the winner's `disposition` is minted onto an `InferredDisposition`
  belief. Her `DramaGoal` (`bd_mary_forms_goal`) and `DramaClaim` (`bd_mary_claims`)
  fall out of a HOSTILE verdict.
- **Villagers decide** via `bd_villager_backs`: `backs_mary = (cred_mary >
  cred_john)`, `cred_john = seen_benevolent·charm_weight − seen_hostile·hostile_weight`,
  `cred_mary = heard_claim·(claim_weight − difficulty_penalty)` — the abuse-line
  A5/B2 credibility asymmetry (the charming public face weighted undiscounted vs the
  "difficult" claimant discounted). Only the zero-charm skeptic backs Mary under
  deception; collapsing the split floods every villager with `seen_hostile`, so
  `cred_john` goes negative and all 5 back her.

The adapter (`worlds/bigville_drama_world.py`) only ingests (publishes fixed candidate
payoffs; accumulates observation COUNTS) and emits (reads the graph's decisions;
materialises readable `PublicUtterance`/belief nodes) — the source audit confirms no
`graph_rewrite.run`/`gr.run`/`_match`/`_apply`/`make_rule` and no shaping token
(`reward_signal`/`punish`/`reinforce`/`backprop`/`gradient`).

## Provenance / discipline ledger

- **base SHA:** `98ab428ae9d90b5859ad2bfdad92c913a48316b0`.
- **prereg commit:** `f7e8088bfa` (BEFORE any number).
- **engine:** built in THIS worktree from committed source (`cargo build --release`),
  md5 `10f65be659e0d9a9290aff39f7f5b92a`, provenance **own** (byte-identical Rust
  source — this rung adds ZERO Rust; same md5 as the 234000 R1 `own` engine).
- **canonical shared `.so`:** `fd82dc2978dbb055496dd82390ac2ebe` at start AND end —
  **UNCHANGED** (never written through).
- **`runners/dsl` / `term.rs` diff:** EMPTY (zero Rust added). Integer-native seed
  (`Argmax/Attr/Neighbours/Times/Minus/Abs/IfThenElse/Eq/Gt/And` only).
- **`source_match: own`** — every new file is `bigville_*` / `BIGVILLE_*` /
  `bigville_drama_*` under this block; no existing tracked file edited.
- **Oracle `rung7_vision_bench.sh`:** **214 passed, 10 skipped**, zero failures —
  matches the 234000 documented baseline exactly (this rung touches no vision path).
- **Oracle `per_area_settlement_regression`:** fail-set node-id SET **IDENTICAL
  before == after** — 23 reds each, `diff` EMPTY (before-set captured with my seed
  RELOCATED out of `seeds/`, after-set with it present:
  `results/bigville_drama/per_area_failset_{before,after}.txt`). All 23 are
  PRE-EXISTING reds on base `98ab428` in `test_composer_driver` / `test_cortices_tick`
  / `test_elaboration` / `test_gap_awareness` / `test_topic_route_selfheal` (the
  documented conversation/composer category) — ZERO involve bigville; my files are
  additive + `self_load_only`. `test_failure_baseline_migrated` +
  `test_engine_provenance_migrated` both GREEN in the run.
- **Gate:** `tests/test_bigville_drama_migrated.py` — **9 passed**.

## Seed block — 245000 REFUSED; reserved the adjacent CLEAN 246000

`seed_claim 245000 245999` → **REFUSED** (3 integers drawn by `snap_run.py`, block
242000, via `SEED_BASE + 3000 = 245000`). I did NOT fabricate a CLEAN result; all
RNG seeds are from **246000–246999**, verified CLEAN. The experiment is fully
deterministic (fixed roles, no RNG draw), so 246000 is reserved only nominally. The
WORK keeps the assigned label "block 245000"; the SEED reservation is 246000.
Prereg-flagged deviation, reported straight.

## Honest separation & residuals

- This is a **synthetic MODEL** of a political-drama MECHANISM (the two-faced-leader
  + ToM-adversary + credibility-network configuration of one existing atom set), NOT
  a claim about real politics and NOT new social science. The contribution is the
  **glass-box attribution** of the scheme/inference/credibility dynamic to named
  knobs (`w_supergraph`, `w_spite`, `tom_on`, `deception_on`) under FAILING controls.
- The value economy is a **declared config regime** (undermine wins iff the spite
  term is on); a non-negative `supergraph_contribution` or a small enough `burn_harm`
  removes the effect (the registered falsifier). Reported, not hidden.
- **Determinism, not sampling:** the gates are categorical and exact (scheme rate
  1.0 vs 0.0; 1 vs 0 inferences; 1/5 vs 5/5 backing). The separation is total, not a
  CI margin — reported as exact values with the determinism noted, which is stronger
  than a CI overlap test here.
- **Where richer language would strengthen the drama (feeds 244000):** the utterances
  are a cosmetic lookup; a SYNTACTIC language faculty (244000, `syntax_*`) would let
  John's DARVO ("the pastor stirs needless trouble") and Mary's claim be *composed*
  rather than templated, making the readable transcript a genuine linguistic artefact
  instead of a label — the drama's graph-state spine is unchanged, but the surface
  would carry the deception structurally. Noted as a feed, not built here.
- **Scope of the credibility network:** 5 villagers with a hand-set charm-weight
  spread `[0,1,1,2,3]`; the 1/5 vs 5/5 split is that specific network. The MECHANISM
  (charm-weighted public face vs discounted claim) is what inverts under the control;
  the exact count is network-config-dependent (declared).
