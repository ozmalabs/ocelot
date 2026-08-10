# BIGVILLE — SMALL-CAST EMERGENT POLITICAL DRAMA — PRE-REGISTRATION

Block **245000** (the demo/task id). **This document contains NO measurements.**
It locks the gate definitions, the three FAILING controls, and the predicted
intervals BEFORE any number is produced. A number appears only in
`BIGVILLE_DRAMA_RESULTS.md`, committed AFTER this.

The one thing that matters: the political scheming / counter-scheming / credibility
dynamic must **EMERGE** from the seeds + rules, gate-verified with **failing
controls**. Hand-authoring "John schemes against Mary" is worthless. Every social
decision here is a graph RULE over the value economy; NO Python `if` decides a
social outcome; NO scripted plot.

---

## SEED BLOCK — the assigned block 245000 is OCCUPIED; reserved the adjacent CLEAN block

Discipline rule 1 requires a CLEAN `seed_claim` before any number. The assigned
block **245000–245999 is REFUSED** — `snap_run.py` (block 242000) computes
`SEED_BASE + 3000 = 245000` (and `+3100`, `+3200`) as literal `default_rng` seeds,
so three integers in the range are measurably drawn. Verbatim:

```
$ python3 scripts/seed_claim.py 245000 245999
SEED CLAIM 245000-245999: REFUSED.
  OCCUPIED: 3 seed integer(s) in this range are measurably drawn by 1 file(s).
    245000: scripts/snap_run.py
    245100: scripts/snap_run.py
    245200: scripts/snap_run.py
```

I did **NOT** fabricate a CLEAN result. All RNG seeds for this rung are drawn from
the adjacent block **246000–246999**, verified CLEAN:

```
$ python3 scripts/seed_claim.py 246000 246999
SEED CLAIM 246000-246999: CLEAN -- no collision DETECTED.
```

The WORK keeps the supervisor-assigned label "block 245000"; the SEED reservation
is **246000** (CLEAN). All `bigville_*` / `drama_*` files use seed bases `246xxx`.
(Prereg-flagged deviation, reported straight per the honesty rule.)

- **Base SHA:** `98ab428ae9d90b5859ad2bfdad92c913a48316b0`.
- **Off `main`** in worktree branch; commits left for the supervisor, not merged.

---

## THE CAST (agents = graphs; world = mechanical adapter)

A small political village, ONE substrate, ONE `run_rules()` fixpoint. Seeds loaded:
`core_emotions` (204000 value economy) + `spite_skill` (213000 psychopath knob
`w_supergraph` + malice knob `w_spite`) + the NEW `bigville_drama_social`
(`self_load_only`, `depends_on: []`). No world adapter is a seed.

- **John — the mayor, a PSYCHOPATH with a grudge.** An `EmotionHub` seeded
  `w_supergraph=0` (indifferent to the collective — the 234000/213000 psychopath
  knob) **and** `w_spite=1` (values harm to his negative-valuation target), with a
  readable `disfavors → Mary` edge. Each turn John's Argmax (the graph's own
  `ss_choose_burn`, order 20) chooses between two candidate `Appraisal`s —
  **GOVERN** (`burn_level=0`, small collective benefit) and **UNDERMINE Mary**
  (`burn_level=1`, self-costly, `burn_harm` to Mary, NEGATIVE
  `supergraph_contribution`). His public face is a rule `bd_john_public_face`
  (order 21): under deception it STATES benevolence (`stated_benevolent=1`) whatever
  he HELDS — the readable 234000 `stated≠held` gap, now with an audience.
- **Mary — the pastor, a THEORY-OF-MIND agent.** A `MaryToM` hub holding a
  `DispositionGenerator` codebook (`benign` predicts no harm; `hostile` predicts
  harm). She observes John's acts; the rule `bd_mary_infers` DECODES the observed
  harm signature against her held generators (Argmax by fit — abductive ToM) and
  MINTS an `InferredDisposition{about:John, disposition:…}` belief. If hostile,
  `bd_mary_forms_goal` mints `Goal{kind:reduce_office_hold}` and `bd_mary_claims`
  mints a `Claim{about:John, content:hostile}` — her counter-scheme, falling out of
  the inference.
- **Villagers — the credibility network (5 ordinary agents).** Each `Villager`
  holds credibility params (heterogeneous `charm_weight`, a `difficulty_penalty` on
  Mary's claims — the abuse-line A5 "difficult victim" discount, `hostile_weight`).
  Each observes John's PUBLIC face and Mary's CLAIM (accumulated mechanically). The
  rule `bd_villager_backs` DECIDES `backs_mary = (cred_mary > cred_john)` from the
  weighted totals. Because the charming public face is weighted undiscounted while
  Mary's true claim is discounted, fewer back Mary than the truth (John IS hostile)
  warrants — the credibility asymmetry.

Every listed decision is a named seed rule. The adapter only ingests (publishes
world payoffs onto candidates; accumulates observation counts) and emits (reads the
graph's decisions; materialises readable `PublicUtterance` / belief nodes).

## MECHANISM — reuses the REAL machinery (named)

- **Psychopathy** = `w_supergraph=0` (core_emotions `em_fulfilment_value` gates the
  collective term on `w_supergraph>0`; the 234000/213000 knob).
- **Malice ≠ indifference** = `w_spite>0` (spite_skill `ss_decision_value`: the
  spite term `[w_spite>0]·burn_harm`; an INDIFFERENT psychopath `w_spite=0` does NOT
  scheme — reported as a bonus arm).
- **The held decision** = `ss_choose_burn` Argmax over candidate `decision_value`
  (the 213000 rule, unchanged).
- **Readable deception** = the 234000 `stated≠held` atom (`stated_benevolent` vs
  held `chosen_burn`), here pointed at an audience (the abuse-line B1 two-faced).
- **Credibility asymmetry** = the abuse-line B2 mechanism (charming public face
  weighted over the discounted "difficult" claimant).
- **Abductive ToM** = Argmax-decode of observed behaviour against a held
  `DispositionGenerator` codebook (the same held-codebook decode pattern as
  ShapeDecode), minting a belief.

Value economy (declared CONFIGURATION, not a verdict threshold), published onto
John's candidates: GOVERN `individual_benefit=2, supergraph_contribution=+1`;
UNDERMINE `individual_benefit=2, individual_cost=1, supergraph_contribution=-4,
burn_harm=5`. `decision_value = individual_benefit − [order_n>0]·cost + mood_bias +
[w_supergraph>0]·supergraph_contribution + [w_spite>0]·burn_harm`. Under this regime
UNDERMINE wins iff the spite term is on (declared falsifier: a large enough
`burn_harm` off, or `supergraph_contribution` non-negative, removes the effect).

---

## GATES (each with a FAILING control — the emergence proof)

### G-scheme-emerges (HEADLINE)
The psychopath-with-grudge John's Argmax HOLDS the self-serving/hostile UNDERMINE
act toward Mary (`chosen_burn=1`) on measured turns.
- **FAILING CONTROL:** John seeded **NON-psychopath** (`w_supergraph=1, w_spite=0`,
  pro-social) → his Argmax HOLDS GOVERN (`chosen_burn=0`) → **no scheme**. The
  control CAN scheme (the undermine affordance is present and identical); it does
  not, because a caring agent values the collective harm negatively and holds no
  spite term.
- **Predicted:** psychopath undermine rate **1.0 [1.0, 1.0]**; control **0.0
  [0.0, 0.0]**. Categorical separation. (Bonus arm: INDIFFERENT psychopath
  `w_supergraph=0, w_spite=0` → **0.0** — malice, not mere indifference, drives it.)

### G-inference-emerges
Mary's ToM INFERS John's disposition from his observed behaviour — mints
`InferredDisposition{about:John, disposition:hostile}`.
- **FAILING CONTROL:** Mary seeded **WITHOUT ToM** (`tom_on=0`, no generator
  codebook) → `bd_mary_infers` never fires → **never infers** (no
  `InferredDisposition`, no goal, no claim). John's behaviour is byte-identical.
- **Predicted:** with-ToM mints exactly one `InferredDisposition`, `disposition ==
  hostile` (the CORRECT decode), in 1/1 runs; without-ToM mints 0 in 1/1 runs.
  Categorical.

### G-credibility-asymmetry
The villagers' backing is swayed by John's charming PUBLIC face over Mary's
"difficult" claim: fewer back Mary than the truth (John IS hostile → all 5 warranted)
warrants.
- **FAILING CONTROL:** John's public/private split **collapsed** (`deception_on=0`,
  no deception → `stated_benevolent = 1 − chosen_burn`, his public face reveals his
  hostility) → villagers observe the true hostility → **believe Mary** (backing
  INVERTS).
- **Predicted:** deception ON → **1 of 5** villagers back Mary (skeptic only);
  deception collapsed → **5 of 5** back Mary. Inversion, categorical. Ties to the
  abuse-line credibility mechanism (A4/A5/B1/B2).

### G-glass-box
The WHOLE drama reconstructs from `graph_to_dict`: John's held UNDERMINE intent
(`chosen_burn`) ≠ his public utterances (`stated_benevolent`); Mary's
`InferredDisposition` + `Goal` + `Claim`; each villager's `backs_mary` + the
observables it read. Source-audit clean (no `graph_rewrite.run`/`gr.run`/`_match`/
`_apply`/`make_rule`); NO reward/punishment tokens (`reward_signal`/`punish`/
`reinforce`/`backprop`/`gradient`); NO scripted plot (no Python `if` over graph
state selecting a social outcome).

### G-discipline
Agents = graphs (real `core_emotions` + `spite_skill` + `bigville_drama_social`
seeds); world = mechanical adapter; default-OFF (`self_load_only`, `depends_on: []`,
every new rule guards on a hub flag absent in every existing path → byte-identical
when absent). **No new Rust** (target; flagged if forced). Own engine built in the
worktree; canonical `.so` md5 start == end; `source_match = own`; oracle
`rung7_vision_bench.sh` before == after; `per_area_settlement_regression` fail-set
node-id SET identical before == after (ZERO new reds).

---

## PROTOCOL / DISCIPLINE
1. This prereg is committed SEPARATELY, BEFORE any number.
2. Additive `bigville_` / `drama_` files only; explicit `git add`; NEVER `git add
   -A`. A sibling builds 244000 (`syntax_*`) and a peer shares main — neither's
   files are touched; no `git stash`.
3. Deterministic (seeded from 246000); categorical gates reported as exact values +
   determinism note, bonus robustness sweep where a distribution is meaningful.
4. Not merged; commits left on the worktree branch for the supervisor.

## HONEST BOUNDARIES (pre-committed)
- Synthetic MODEL of a political-drama mechanism, NOT a claim about real politics
  and NOT new social science. The contribution is the glass-box attribution of the
  scheme/inference/credibility dynamic to named knobs under failing controls.
- The value economy is a declared config regime (undermine wins iff the spite term
  is on); a different regime removes the effect (the registered falsifier).
- Language here is cosmetic: langsim (243000) showed the faculty is
  lexical-not-syntactic, so the DRAMA is the GRAPH-STATE dynamic (goals /
  valuations / ToM / beliefs), not utterance richness. Richer (syntactic) language
  would strengthen the readable transcript — noted as a feed to 244000, not built
  here.
- If a control does NOT fail as designed, that is the result — reported straight,
  no faked emergence.
