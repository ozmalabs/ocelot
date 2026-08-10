# LS20 OBSERVE-AND-GROUND remote causality — PRE-REGISTRATION (block 229000)

Committed **ALONE**, BEFORE any code or number. Block `229000-229999` claimed CLEAN.

## THE CORRECTION THIS BLOCK MAKES (owner)

Block 228000 proved remote causation, but it established the causal link by running a
**probe WORLD-MODEL** to SIMULATE the act-vs-no-op counterfactual — `eff_act`/`eff_noop`
came from re-running a deterministic world under (do) vs (no-op). That is **model-based**,
and it works only offline where you can REWIND. **On the real game there is NO rewind**, so
228's live path ran the model-probe, got `eff_act=0`, and grounded NOTHING
(`LS20_REMOTE_RESULTS.md` §G-live).

Owner: *"What it needs to do is OBSERVE the causality and ADD that grounded understanding
to the graph in the context, so it KNOWS that the cross causes rotation."*

So the causal link must be **GROUNDED FROM REAL OBSERVATION**, not simulated:

- The agent interacts with the salient object (the cross) FOR REAL, **OBSERVES the actual
  before→after in the real frames** (perception — the 216/217 pixel eye / real-frame onset
  stream), and **if the remote thing (its shape) rotated, MINTS a persistent grounded causal
  fact `causes(cross, rotation)` into the graph.**
- The no-op / negative evidence comes from the **NATURAL TIMELINE** — real timesteps where
  the agent did NOT interact with the cross AND the remote thing did NOT change — NOT a
  simulated counterfactual. This is what refutes coincidence (a remote thing that changes on
  its own, even without interaction, is NOT grounded).
- Once grounded, the fact **PERSISTS** and the agent **KNOWS** it — and acts on knowing
  (reads `causes(cross,rotation)` → route to the cross → operate → obtain rotation → pass).

Every decision is a rule; the grounding is mechanical perception → graph write (mint the
`CausalFact` FROM the observed effect). No hardcoded `cross→rotation`.

## MECHANISM (graph-native; no Rust, reuses 216/217 perception + 228 remote + 227 posit + 220 nav)

- The adapter writes, PER REAL STEP, an `Observation{interact, remote_changed, cause_id,
  effect_kind}` node (edge `g -has_obs-> obs`). `interact` and `remote_changed` are OBSERVED
  (real before→after distal-change perception), never simulated. The stream of Observations
  IS the natural timeline as first-class graph data.
- **The GROUNDING RULE (`rcg_ground`)**: an Observation where `interact==1 AND
  remote_changed==1` (a real interact→distal-change), AND **no Observation in the natural
  timeline where `interact==0 AND remote_changed==1`** (nothing changed spontaneously — the
  natural-timeline no-op / negative evidence), AND no `CausalFact` yet for this cause→effect
  → MINT `CausalFact{cause, effect, status:"grounded", source:"observation"}` + edge
  `g -has_causal_fact-> cf` + `causes` edge from the cause object to the fact. The fact
  PERSISTS (it is a node + edges; a `Not Exists` guard makes it mint-once).
- **KNOWS-AND-ACTS (`rcg_knows_and_acts` → `rcg_pass`)**: with a grounded `CausalFact` for
  the cause object and not-yet-matching, the agent reads the fact, seeks the cause object,
  operates it (obtains the effect), and passes. Without a grounded fact it cannot.

## ARMS (offline powered ablation, on before/after observation streams)

- **observe** (the real path): grounds iff a real interact→change is OBSERVED AND the natural
  timeline shows no spontaneous change. Correct on BOTH Family A (ground) and Family B
  (refuse).
- **no_natural_timeline** (control): grounds on any co-observed interact→change, IGNORING the
  natural-timeline no-op → false-positive on Family B (coincidence).
- **blind** (control that never observes the effect): its Observations always have
  `remote_changed==0` → never grounds → misses Family A.
- **sim_probe** (the 228 correction contrast): the 228 model-probe path (reads `eff_act`/
  `eff_noop` from a simulated rewind). Live it grounds nothing (reproduces `eff_act=0`).

Family A = the cross truly controls the remote thing (change ONLY on interact steps).
Family B = the remote thing changes SPONTANEOUSLY (changes on interact AND no-interact steps
— coincidence). N pairs per config, Wilson 95% CIs.

## GATES (pre-registered)

- **G-observe-and-ground (HEADLINE)**: after a REAL interaction where the remote change is
  OBSERVED (Family A, natural timeline clean), the agent MINTS a persistent grounded
  `causes(cross,rotation)` fact — absent before, present after, and it PERSISTS. CI-separated
  from the `blind` control (never observes the effect → never grounds).
- **G-grounded-from-observation-not-simulation (the correction, source-audited)**: the fact
  is grounded from the ACTUAL observed before→after (Observation.remote_changed + the
  natural-timeline no-op via `Not Exists`), NOT from a probe world-model counterfactual.
  Source-audit: the live grounding path reads the OBSERVED effect; the no-op evidence is
  drawn from the natural timeline, not a simulated rewind. Contrast: the 228 `sim_probe` path
  grounds nothing live (reproduce its `eff_act=0` null); the observation path grounds it.
- **G-knows-and-acts**: with `causes(cross,rotation)` grounded, the agent reads it and acts
  (route → operate → pass) — vs without it (no knowledge → cannot). The grounded fact is
  USABLE by the rules.
- **G-live (THE real test, honest)**: on real ARC-AGI-3 ls20 — when the agent interacts with
  the cross, DOES the real frame show an observable remote rotation, and does the agent GROUND
  it? Reported STRAIGHT either way: (a) real cross-interaction → OBSERVABLE remote change →
  ground it (owner's expectation confirmed); OR (b) real interaction → NO observable remote
  change in budget → report the NULL straight + exactly what was observed (did the interaction
  register? did anything change anywhere?). MEASURE, do not assume. Fresh-API vs replay stated.
- **G-graph-native**: grounding = mechanical perception → graph write (mint the CausalFact
  FROM the observed effect); the act-on-knowledge is rules; adapter mechanical. Source-audit:
  no hardcoded `cross→rotation`; the fact is minted FROM observation.
- **G-discipline**: integer-native; default-OFF byte-identical (every rule guarded on
  `game.ground_on==1`); canonical `.so` md5 `793ce09ed498a749abb79aeaea44b92e` UNCHANGED;
  `term.rs` + whole `runners/dsl` tracked diff EMPTY; oracle `rung7_vision_bench`
  BEFORE==AFTER; 34-file `per_area_settlement_regression` failing-node-id SET identical
  BEFORE==AFTER; `source_match` reported for the seed round-trip.

## FALSIFICATION BAR

The causal fact is GROUNDED FROM REAL OBSERVATION (not a simulated counterfactual — that is
the whole correction); it PERSISTS in the graph and is USABLE; and whether the real ls20
interaction yields an observable groundable rotation is MEASURED, reported straight either
way.

## VERBATIM `check_claim` (recorded here, NOT a permanent pytest)

```
$ python3 scripts/seed_claim.py 229000 229999
SEED CLAIM 229000-229999: CLEAN -- no collision DETECTED.
  Scope: 940 files with seed sinks; 643 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```
