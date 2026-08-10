# BIGVILLE R15 — VIOLENCE (a simple scalar): inter-agent physical harm + the evidence-and-proof enforcement pipeline — PRE-REGISTRATION

**Block 263000. Pre-registered BEFORE any recorded number.** Spec:
`BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §2.9 (the VIOLENCE paragraph) + §3 R15 (block 263000,
the six gates). Builds ON R14 `bigville_life_world` (the ONE HEALTH variable → the routed
`bl_death`; the reused 239000 window-of-tolerance) and R17 `bigville_affect_world` (the
`decision_value` Argmax trigger — grief/spite/desperation as a TERM in a selector), which
themselves carry R13 land / R7 finance / R9 council / R1 movement+energy through their MRO.
Everything imported READ-ONLY — the R15 adapter SUBCLASSES `BigvilleAffectWorld` and **edits
no tracked file.** The 247 evidence-and-proof machinery (`bigville_laws_enforcement` — WITNESS
vs decline, the council quorum `Sum`-over-backers) and the 245 abductive decode
(`bigville_drama_social` — `bd_mary_infers`, an `Argmax` over a held generator codebook by fit)
are read as TEMPLATES; R15 ships its own `bigville_viol_*` rules.

Violence is a **simple SCALAR (nothing deeper), reusing everything.** A violent act carries an
AMOUNT; the victim loses HEALTH (`−amount`, the acute arm of the R14 health variable → routed
`bl_death` at zero), the aggressor loses STAMINA (`−cost`, R1 `energy` — violence is tiring).
Enforcement is an **EVIDENCE-AND-PROOF pipeline, not omniscience:** the constable learns of an
act by WITNESSING it (line-of-sight) OR by being TOLD (a REPORT — a testimony Message), then
INVESTIGATES (accumulates evidence: testimony + the victim's health-drop as PHYSICAL evidence),
forms a BELIEF by ABDUCTION (decodes the evidence against held generators — a RECONSTRUCTION,
not a fact), and only on SUFFICIENT PROOF (a `decision_value` threshold) PROSECUTES WITH THE
COUNCIL (R9), which ADJUDICATES over its backing-graph → WARN (small amount) / PUNISH (large).
Every stage is a seed RULE; the adapter only mints nodes, delivers world facts (an act occurred;
the constable had line-of-sight; a report was filed; who sits the council and how they vote),
arms one-shots, runs the Rust `run_rules` fixpoint, and reads. **ZERO new Rust** (composes only
existing DSL Terms — Plus/Minus/Times/Min/Max/Abs/Eq/Gt/Gte/Lte/Lt/And/Or/Not/IfThenElse/Sum/
Argmax/Neighbours/NodesOfType/Attr/Var/Lit — verified present in `runners/dsl/src/term.rs`).
Four additive `self_load_only` seeds — cannot regress any other suite.

## Seed-claim (verbatim `scripts/seed_claim.py 263 263`, run before anything)

```
SEED CLAIM 263-263: CLEAN -- no collision DETECTED.
  Scope: 978 files with seed sinks; 699 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

(R15 seeds NO RNG — every rule/attr is deterministic graph data; the trigger, the harm/cost
deltas, the evidence weights, the abductive `Argmax`, the proof threshold and the council `Sum`
are all deterministic. The claim is a discipline formality; the rung introduces no stochastic
sink. The gate is fully deterministic, no CIs required.)

## What R15 adds (graph-native, ZERO new Rust)

Four additive, `self_load_only` seeds, composing ONLY existing DSL Terms:

- **`bigville_viol_act`** — THE ACT. `bv_trigger` is the value-DECISION to attack: a considered
  attacker commits iff its `trigger_value = snap_pressure + w_spite·spite_gain + hunger·
  desperation_gain` exceeds its `trigger_threshold` AND it has the STAMINA (`energy ≥ attack_cost`)
  — the outward-facing form of the 242 frustration-SNAP / spite (`w_spite`) / DESPERATION, NOT
  random; `bv_refrain` is the disjoint decline arm (calm, no spite, fed → refrain, no act). On a
  committed act, `bv_harm_victim` applies `victim.health := max(0, health − amount)` (the acute
  arm, `last_cause = 5` violence — flows into R14 `bl_death` at zero, the FIFTH route to death)
  and `bv_cost_aggressor` applies `aggressor.energy := max(0, energy − cost)`.
- **`bigville_viol_evidence`** — THE 247 PIPELINE + THE RECONSTRUCTION. `bv_open_witness` (the
  constable had line-of-sight → Case `known=1` + a witness `Evidence{weight}`), `bv_open_report`
  (a testimony Message → Case `known=1` + a testimony `Evidence{weight}`), `bv_physical` (a KNOWN
  case whose victim's health actually dropped → a physical `Evidence{weight}` — the health-drop as
  corroboration a FALSE report lacks), `bv_form_belief` (ABDUCTION: `observed := Sum` of the
  case's evidence weights; the verdict is the `Argmax` over the constable's held `CaseGenerator`
  codebook — `guilty` predicts high evidence, `innocent` predicts none — by fit `−|predicts −
  observed|`; a RECONSTRUCTION that concentrates or stays diffuse), and `bv_sufficient_proof`
  (verdict guilty AND `confidence ≥ proof_threshold` — the `decision_value` — → `proven=1`).
- **`bigville_viol_prosecute`** — THE CORRUPTIBLE STATE. `bv_prosecute` (a proven case → a
  `Prosecution` filed with the council), `bv_council_convict` / `bv_council_acquit` (the council
  adjudicates over its backing-graph — `Sum` of `vote` over SEATED `CouncilMember`s `> 0` → a
  `Conviction`; John's seat is a `vote=−1` bloc that can BLOCK a true prosecution or a `vote=+1`
  bloc that can PUSH a false one), and `bv_warn` / `bv_punish` (a conviction → a `Sanction`, WARN
  if `amount ≤ warn_threshold` else PUNISH — magnitude, not the trigger, sets the severity).
- **`bigville_viol_kill`** — the FIFTH-route seam is R14's own `bl_death` (no new rule); this seed
  ships only the glass-box `CaseGenerator`/`Sanction` concept vocabulary + a `bv_death_tag` that
  records `death_by_violence=1` when a person `just_died` with `death_cause=5` (a mechanical
  read-back tag, no decision — kept separate so the act/evidence/prosecute seeds stay minimal).

## The gates (each with its failable control)

### G-violence-costs-both (both deltas load-bearing)
A committed `ViolentAct{amount, cost}` drops the victim's HEALTH by `amount` (R14 acute arm) AND
the aggressor's STAMINA (`energy`) by `cost` (R1). **Control:** ablate the act (no `ViolentAct`
minted — the trigger refrains) → NEITHER health nor energy moves. Each delta is checked
independently (a victim-only assertion and an aggressor-only assertion) so both are shown
load-bearing.

### G-evidence-pipeline (247 — NOT omniscience; the REPORT channel is load-bearing)
The constable prosecutes an act it did NOT witness ONLY via the report channel: WITNESS **or**
REPORT → INVESTIGATE → BELIEF → SUFFICIENT-PROOF → PROSECUTE → adjudicate → WARN/PUNISH.
**Control:** ablate the REPORT channel on an UNWITNESSED act (no line-of-sight, no report filed)
→ the Case is never opened → no evidence → the belief decodes to `innocent` → NOT prosecuted
(regression to a witnessed-only floor — the report channel is load-bearing).

### G-belief-is-a-reconstruction-not-a-fact (falsifiable BOTH ways)
The verdict is a decode against held generators, not a fact. Falsifiable both ways:
(a) SUFFICIENT evidence CONVICTS an UNWITNESSED true act (victim testimony + physical health-drop
→ `observed` high → guilty → proven); (b) INSUFFICIENT evidence DECLINES even a TRUE act (no
witness, victim silent, no report → `observed = 0` → innocent → declines, the unseen-abuse
dynamic, the RIGHT reason); (c) a FALSE report with CONTRADICTING evidence is REJECTED (testimony
present but NO physical health-drop, plus an alibi `Evidence{weight<0}` → `observed` below the
generator midpoint → innocent wins the `Argmax` — the false-accusation refusal, a min-distance
exact selection).

### G-council-adjudicates (corruptible — a clean structural counterfactual)
Prosecution runs THROUGH the council; the outcome is `Sum(vote over seated CouncilMembers) > 0`.
John's council seat is a bloc that BLOCKS a true prosecution of an ally (his `vote=−1` tips an
otherwise-convicting `Sum` to `≤ 0`) or PUSHES a false one against Mary (his `vote=+1` tips an
otherwise-acquitting `Sum` above `0`). **Control:** ablate John's council seat (`is_seated=0`) →
the biased outcome FLIPS (the true prosecution convicts; the false one acquits) — structural
corruption of justice, emergent, with a clean counterfactual.

### G-violence-can-kill (the FIFTH route to death, R14)
A large or sustained act drives `victim.health → 0` → R14 `bl_death` fires in the SAME fixpoint →
`dead=1`, `death_cause=5`; `bv_death_tag` records `death_by_violence=1`. **Control:** a small act
(amount < health) harms but does NOT kill (`dead=0`). Murder/manslaughter is the acute arm at
magnitude — no new death machinery, the R14 route reused.

### G-trigger-is-a-decision (not random; the trigger is load-bearing)
Violence is the outward form of the 242 snap / spite / desperation — a value-decision. A pressured
/ spiteful / starving attacker commits (`bv_trigger`); **Control:** ablate the trigger (calm:
`snap_pressure=0`, no spite: `w_spite=0`, fed: `hunger=0`) → `trigger_value ≤ threshold` →
`bv_refrain` → NO act (no health/energy change, no case). The trigger, not chance, is what makes
violence reachable.

## ETHICS — the relational-ethics protocol (harm-analog, REQUIRED)

Violence and abuse are the town's darkest outcomes; every induction binds the standing
**relational-ethics protocol: INDUCE → MEASURE → RESTORE, with NO reward/punishment token in the
rule logic.**

- **INDUCE** a harm (a violent act; the unseen-abuse dynamic where the victim cannot/will-not
  report) only to MEASURE the mechanism (the health-drop, the evidence pipeline's verdict).
- **MEASURE** the glass-box readout (health, energy, the belief confidence, the adjudication) —
  the point is understanding the mechanism, never scoring an agent.
- **RESTORE:** a harmed victim is RESTORED by the R14 care arm (`treat` → `bl_recover` widens
  health back toward `max_health`); the enforcement outcome is a WARN/PUNISH that is a STATE
  transition on an Office/record, **never** a reward or punishment token on a person. A `Sanction`
  is a graph fact (a censure), not a badness score. The unseen-abuse victim's silence is modelled
  as genuine INSUFFICIENT PROOF (the RIGHT reason, per the abuse-line protocol), never as the
  victim's fault. NO `reward` / `punish` / `penalty` token appears in any rule logic (checked in
  the source-audit gate); the seeds' PROSE may name the "warn/punish" sanction kinds (a legal
  vocabulary), but the RULE LOGIC carries none.

## Architecture-rule compliance

A WORLD ADAPTER (`worlds/bigville_viol_world.py`). It SUBCLASSES `BigvilleAffectWorld` by import,
edits no tracked file, holds NO agent decision. It ONLY does mechanical I/O: mint a person /
`ViolentAct` / `Case` / `Evidence` / `CaseGenerator` / `Prosecution` / `CouncilMember` (ingest);
deliver world facts (an act's amount/cost; the constable's line-of-sight; a filed report; an
alibi; who sits the council and how each votes); arm one-shots; run the Rust `run_rules` fixpoint;
read state back. EVERY decision — the trigger (`bv_trigger`/`bv_refrain`), the harm/cost deltas,
the evidence gathering, the abductive belief (`bv_form_belief`), the proof threshold
(`bv_sufficient_proof`), the prosecution and the council adjudication (`bv_council_convict`/
`bv_council_acquit`), the sanction (`bv_warn`/`bv_punish`), and the reused R14 `bl_death` — is a
seed RULE, never Python. NO reward/punishment token anywhere. NO new Rust.

## Deferrals (honest scope)

- Line-of-sight / occlusion is delivered as a world fact (`witnessed=1`), exactly as
  `bigville_laws_enforcement` delivers `witnessed_act` — the sim's geometric occlusion query is
  not re-derived here (it is the base movement world's job).
- The council backing-graph (who sits, how each votes, John's sway over allies) is a world fact
  the adapter sets, as `bigville_drama_social` sets `backs_mary`; R15 measures the ADJUDICATION
  mechanism given a backing graph, it does not re-derive how John captures a councillor (that is
  the 245/247 drama's job, reused conceptually).
- Sustained violence over many ticks (a beating) is modelled as the acute-arm magnitude at one
  or a few acts; the tick-by-tick attrition dynamics are the R14 health arm, not re-implemented.

## Gates to run (inline; the 43-min oracles are NOT run — additive `self_load_only`)

- `python -m pytest tests/test_bigville_viol_migrated.py -q` (all green)
- `python -m pytest tests/test_failure_baseline_migrated.py -q` (11/11)
- `python -m pytest tests/test_engine_provenance_migrated.py -q` (7/7, `source_match ∈ {own, shared}`)
- source-audit: seeds `self_load_only`; adapter decision-free; `git diff <base> -- runners/dsl` empty;
  canonical `.so` md5 unchanged.
