# BIGVILLE R15 — VIOLENCE (a simple scalar) + the evidence-and-proof enforcement pipeline — RESULTS

**Block 263000.** Measured AFTER the pre-registration (`BIGVILLE_VIOL_PREREG.md`, committed
first). Deterministic (no RNG) — every number is a fixed graph readout, no CIs required.
Glass-box readout: `results/bigville_viol/summary.json` (`python scripts/bigville_viol_measure.py`).

Four additive `self_load_only` seeds (`bigville_viol_act` / `_evidence` / `_prosecute` / `_kill`,
15 rules), one world adapter (`worlds/bigville_viol_world.py`, subclassing `BigvilleAffectWorld`
read-only), one test suite (`tests/test_bigville_viol_migrated.py`, **20/20 green**). **ZERO new
Rust** (`git diff <base> -- runners/dsl` empty; canonical `.so` md5 unchanged
`fd82dc2978dbb055496dd82390ac2ebe`; engine provenance `source_match = shared`).

## Gates (all PASS)

### G-violence-costs-both — a scalar act costs BOTH, both load-bearing
A `ViolentAct{amount=15, cost=8}`: victim HEALTH `100 → 85` (`−amount`, the R14 acute arm) AND
aggressor STAMINA `energy 100 → 92` (`−cost`, R1). **Control (ablate the act):** a calm aggressor
refrains, 0 acts minted → victim health unchanged (100), aggressor energy unchanged (100). Each
delta checked independently — both load-bearing.

### G-evidence-pipeline (247) — the report channel is load-bearing
| case | known | confidence | prosecuted | convicted | sanction |
|---|---|---|---|---|---|
| WITNESSED (line-of-sight) | ✓ | 9.0 (witness 6 + physical 3) | ✓ | ✓ | WARN |
| UNWITNESSED + REPORT | ✓ | 6.0 (testimony 3 + physical 3) | ✓ | ✓ | — |
| **ablate REPORT (unwitnessed, unreported)** | ✗ | — (no belief) | ✗ | — | — |

The constable prosecutes an unwitnessed act ONLY through the report channel; remove it and the
case is never opened (regression to a witnessed-only floor). The report channel is load-bearing.

### G-belief-is-a-reconstruction-not-a-fact — falsifiable BOTH ways
The verdict is the abductive `Argmax` over the constable's held `{guilty:8, innocent:0}` codebook
by fit to the observed evidence weight — a reconstruction, not a fact.
- **(a) convicts an UNWITNESSED true act:** victim testimony (3) + physical health-drop (3) = 6 →
  guilty → convicted.
- **(b) declines a TRUE act (unseen abuse):** a real act, silent victim, no witness → observed 0 →
  never known → **declines, the RIGHT reason** (genuine insufficient proof, never the victim's fault).
- **(c) rejects a FALSE report:** testimony (3) + contradicting alibi (−3) = 0, victim never
  actually harmed (no physical) → the `Argmax` lands on **innocent** → rejected. The physical
  health-drop is the discriminator a false report lacks (testimony-only = 3, below the generator
  midpoint 4 → declines even without the alibi).

### G-council-adjudicates — corruptible, a clean structural counterfactual
Outcome = `Sum(vote over seated CouncilMembers) > 0`.
| scenario | with John | ablate John's seat |
|---|---|---|
| BLOCK a true prosecution (honest +1, John −1) | ACQUIT | **CONVICT** |
| PUSH a conviction (a +1, b −1, John +1 pivotal) | CONVICT | **ACQUIT** |

John's seat flips the verdict in BOTH directions — structural corruption of justice, emergent from
the backing graph, with a clean counterfactual.

### G-violence-can-kill — the FIFTH route to death (R14 reused)
A large act (amount 150) drives victim health `→ 0` → R14 `bl_death` fires in the same fixpoint:
`dead=1`, `death_cause=5` (violence), `death_by_violence=1`. **Control:** a small act (15) harms
(health 85) but does NOT kill. No new death machinery — the R14 acute arm at magnitude.

### G-trigger-is-a-decision — not random, the trigger is load-bearing
| trigger | attacked |
|---|---|
| snap_pressure (242 frustration-SNAP) | ✓ |
| w_spite (malice) | ✓ |
| hunger (desperation) | ✓ |
| **ablate (calm, no spite, fed)** | ✗ (refrained) |

Violence is the outward form of the 242 snap / spite / desperation — a value-decision. Ablate the
trigger and the aggressor refrains, no act. (Also: a pressured aggressor with `energy < attack_cost`
refrains — violence is tiring and can't be committed without the stamina to pay for it.)

### ETHICS — induce → measure → RESTORE, NO reward/punishment
A violent act induces a health-drop (30 → health 70); the R14 care arm (`treat` → `bl_recover`)
RESTORES the SAME variable to 100. Harm is a STATE reversed by care; a `Sanction` is a graph record
(a censure), never a badness token — verified by the source-audit (no `reward`/`penalty` token in
any rule logic; the seeds' prose may name the warn/punish legal vocabulary, the RULE LOGIC carries
none).

## Discipline

- **Gates green:** `test_bigville_viol_migrated` 20/20; `test_failure_baseline_migrated` 11/11;
  `test_engine_provenance_migrated` 7/7 (`source_match = shared`).
- **Additive-only:** one prefix `bigville_viol_`; NO tracked file edited; four seeds `self_load_only`
  with no seed deps (reuse R14/R17/R7/R9/R1 by import).
- **NO Rust:** `git diff <base> -- runners/dsl` empty; the seeds compose only known DSL Terms
  (audited in the test); canonical `.so` md5 START==END unchanged.
- **Adapter decision-free:** source-audit passes — no Python rule engine, no `if` on any decision
  parameter; every violence decision is a seed RULE.
- The ~43-min `per_area_settlement_regression.sh` / `rung7_vision_bench.sh` oracles were **NOT run**
  (per the 2026-07-29 directive: an additive `self_load_only` rung cannot regress other suites).

## Honest residuals

- **Line-of-sight / occlusion is a delivered world fact** (`witnessed=1`), not re-derived — exactly
  as `bigville_laws_enforcement` delivers `witnessed_act`. The sim's geometric occlusion query is
  the base movement world's job; R15 measures the pipeline given the witness bit.
- **The council backing-graph** (who sits, how each votes, John's sway over allies) is a world fact
  the adapter sets, as `bigville_drama_social` sets `backs_mary`. R15 measures the ADJUDICATION
  mechanism given a backing graph; it does not re-derive how John captures a councillor (the
  245/247 drama's job, reused conceptually).
- **The abductive codebook is two generators** (guilty/innocent) with fixed `predicts_evidence`;
  a richer generator manifold (multiple attack hypotheses, graded confidence) is deferred — the
  scalar spec asks only for the concentrate-vs-diffuse reconstruction, which two generators show.
- **Sustained violence (a beating over many ticks)** is modelled as the acute-arm magnitude at one
  or a few acts; tick-by-tick attrition is the R14 health arm, not re-implemented here.
- **The prosecution/adjudication are distinct bars:** a case that passes the constable's
  `proof_threshold` can still be acquitted (or a weak case convicted) by the council — the "push"
  corruption models the council overriding, not fabricated evidence passing the constable's proof.
  A framing that fabricates evidence to cross proof is not separately modelled.
- All numbers are DETERMINISTIC synthetic-mechanism readouts (a glass-box MODEL of the
  harm/evidence/justice mechanism), NOT a claim about real violence or real justice, and NOT new
  social science.
