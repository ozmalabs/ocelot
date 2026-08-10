# VISION — CROWDING (eccentricity-scaled statistical pooling) — PRE-REGISTRATION

*Frontier rung T8. A VALIDATION gate for the eye's foveation / eccentricity-decay prior
(`VISION_VENTRAL_GROUNDING.md` failure-mode gate #4). Written and committed BEFORE the
run (PROTOCOL §3). Seed range **43000–43999**, flag **OFF by default** (§9).*

Engine at authoring: `7d5f50c18673 @ runners/dsl/python/substrate_rs/_native.abi3.so`
(shared build, Rust source identical — this rung adds **NO Rust**). Base commit
**d8955f47** (`git merge-base --is-ancestor d8955f47 HEAD` holds). Provenance line is
pasted into OUTCOME after the run (§10). Bench baseline before build: **190 passed, 10
skipped** (`scripts/rung7_vision_bench.sh`; 10 skipped = `data/`-gitignored corpus, §10.2).

---

## STEP 1 — AUDIT (§12.4, file:line)

**The phenomenon.** Crowding (Bouma 1970): a peripheral target that is trivially
identifiable in ISOLATION becomes JUMBLED / unidentifiable when flanked in clutter. The
pooling region grows with eccentricity, so the periphery reports a SUMMARY STATISTIC
(texture-like) over an eccentricity-scaled region and loses the target's identity. A
FOVEAL target with the same flankers is NOT crowded (the pooling radius is ~0 at the
fovea). Critical flanker spacing grows with eccentricity (Bouma's law: s\* ≈ b·ecc).

**What already EXISTS in the tree (composes):**

- **A foveation / eccentricity structure with an explicit CENTER.** The `Foveate` Rust
  primitive (`runners/dsl/src/vision_primitives.rs:113`) samples an image around a center
  `cy=(h-1)/2, cx=(w-1)/2` (`:124–126`): inside a foveal disc of radius `fov_r =
  fovea_radius_frac·min(h,w)/2` it keeps full resolution; OUTSIDE it decimates by
  `periphery_stride` (`:117–141`). The geometry is agent-revisable graph data
  (`SamplingGeometry.fovea_radius_frac / periphery_stride`, `seeds/vision_floor.json:16`,
  driven by `vf_foveate_observation`, `seeds/vision_floor.json:142`). **This is an
  eccentricity-dependent RESOLUTION with a well-defined origin (the fovea center) — the
  ungrounded fixation point** (memory: "the center is the ungrounded fixed point";
  grounding decays with eccentricity).
- **Ensemble / summary-statistic coding at the region grain.** `vf_summary_stat`
  (`seeds/vision_floor.json`, mechanism 5): *"a Region's interior is a summary stat, not
  per-pixel samples … 'grass texture' / average-crowd coding."* Regions carry a
  `grounding_label` (their recognized identity) and a mechanical center (`cy/cx`).
- **A LOCAL pooling fold, proven O(N).** `vision_ground.json`'s `gr_fill` and
  `vision_lateral`'s pool read a neighbourhood via `Neighbours`→`Filter`→`Count`/`Sum`→
  `Div` (mean). The blind-spot rung established this is the substrate's grounded-field
  pooling machinery, driven by the `run_rules` fixpoint.
- **Full arithmetic DSL** (`runners/dsl/src/term.rs`): `Times/Plus/Minus/Pow/Sqrt/Div/Abs/
  Count/Sum/Filter/Neighbours/IfThenElse/Gte/Lte` — enough to express distance², an
  eccentricity-scaled radius, and a pooled read with NO new Rust.

**What is NEEDED (does not yet compose):** the existing `Foveate` DECIMATES (drops
strided rows/cols); it does not POOL a summary that MIXES a target with its flankers.
Crowding requires a pooling READ whose region radius scales with eccentricity, over which
recognition returns the pooled (mixed) summary. So the audit verdict is:

> **The eccentricity STRUCTURE (a center + resolution that degrades with eccentricity)
> and the summary-stat CONCEPT both exist; what must be ADDED is the composition — a
> pooling read `pool(item) = {items within R(ecc) of item}`, with `R(ecc)` growing with
> eccentricity, and recognition = "does the pool contain only the target."** Expressible
> entirely as seed rules on the existing `Neighbours`/`Filter`/`Count` fold.

**Can crowding be expressed as the target task states?** Yes: recognition reads a pooled
summary over an eccentricity-scaled region; an isolated peripheral target survives
(`pool = {target}`) and a flanked one does not (`pool = target+flankers`, mixed).

### §13.1 honesty, declared IN ADVANCE (the forced vs risked split)

Choosing `R(ecc) = b·ecc` (monotone-increasing in eccentricity — the natural continuous
generalisation of the foveation prior's eccentricity-decay) makes **two of the arms
ARCHITECTURALLY ENTAILED, and I claim NO discovery credit for them** (the Troxler-arm-B /
Engbert-crossover discipline, §13.1):

- **ECCENTRICITY-SCALING** (critical spacing grows with ecc): `s\* = b·ecc` is monotone in
  `ecc` BY CONSTRUCTION. Reported as **calibration**, not as risked evidence.
- The *magnitude* `b` is a **free scale set as graph data**, NOT a biological constant. I
  deliberately use **b = 0.6** (NOT Bouma's 0.5) and additionally report an
  **invariance sweep** over `b ∈ {0.4, 0.6, 0.8}` (non-gated) to show every qualitative
  arm holds for ANY `b>0`. `b` does not "fall out" of the system — stated plainly (§13):
  it is a scale I choose to exercise the regime, and only the *numeric* crit-spacing
  values depend on it.

**What IS falsifiable / risked (the model COULD produce the opposite):**

1. **CLUTTER-dependence.** An ISOLATED peripheral target must be RECOGNIZED (`pool =
   {target}`). A model that jumbled everything peripheral (ignoring clutter) FAILS this.
2. **The matched-spacing DISSOCIATION (FOVEAL SPARING).** At the SAME flanker spacing, a
   foveal target is recognized while a peripheral one is crowded. A model whose pooling
   radius did NOT scale with eccentricity (constant `R`) would crowd the foveal target
   too and FAIL this — so foveal sparing is precisely the test that the pooling is
   *eccentricity-scaled*, and it can fail.

The rung is therefore a VALIDATION/consistency gate ("the foveation prior ENTAILS
crowding, and the model FAILS where it must" — the blind-spot discipline), never a claim
that crowding "emerged" as a surprise.

---

## STEP 2 — THE BUILD (pre-registered)

**Seed `seeds/vision_crowding.json`** (emitted by the builder `tools/build_crowding_seed.py`;
seed committed as data). Nodes/edges built by the world adapter `domains/crowding_world.py`
(mechanical I/O ONLY, §0). Flag OFF by default (§9).

**Representation.** A `CrowdField{gaze_row, gaze_col}` (the fixation = ungrounded origin).
`CrowdItem{irow, icol, ident, iid, is_target}` wired `field -has_item-> item`, and every
ordered pair of same-field items wired `item -co_item-> other` (mechanical 2-clique
scaffolding, exactly like border_ownership's 4-neighbour wiring — NOT an agent claim, so
NO global `NodesOfType` population grab; the pool is LOCAL over `co_item`). A
`CrowdParams{crowd, bouma}` config node (`crowd=0` OFF by default).

**Rules (all gated on `CrowdParams.crowd > 0.5`):**

- `cr_ecc` — for each item: `ecc2 = (irow−gaze_row)² + (icol−gaze_col)²`;
  `pool_radius2 = bouma²·ecc2`. Fires once (`ecc_done` guard). Pure geometry — the
  eccentricity of every item from the fixation.
- `cr_pool` — for each item (guarded on `ecc_done`, fires once via `pool_done`): pool =
  the item itself ∪ `{n ∈ Neighbours(item, co_item) : dist²(n,item) ≤ pool_radius2}`.
  Sets `pool_n = 1 + Count(flankers-in-pool)`; `pooled_ident = (own ident + Σ
  flanker idents-in-pool) / pool_n` (the SUMMARY STATISTIC — mixes when a flanker is
  pooled); `crowded = 1 iff pool_n ≥ 2`; `recognized = 1 iff pool_n < 1.5` (the pool
  contains ONLY the target ⇒ identity survives).

Recognition thus literally **reads the pooled summary**: `pool = {target}` ⇒ recognized;
`pool = target+flankers` ⇒ crowded and `pooled_ident` is jumbled. No Python decision — the
adapter only ingests items/edges, blind-writes the flag, ticks, and reads attrs back.

---

## STEP 3 — ARMS, STATISTICS, DECISION RULE

The mechanism is DETERMINISTIC geometry (no stochastic learning), so per-arm outcomes are
EXACT (the border-ownership / depth precedent); the only randomised arm is the noise floor
(n fixed in advance). All coordinates in-frame integers; the pooled mean and the radius are
cross-frame reads (frame/continuum invariant). Idents chosen so a pooled mean can NEVER
coincide with the target's (target ident **5**, flankers ident **9**).

**Fixed geometry:** gaze center at `(0,0)`; target at `(ecc, 0)` (radial); flanker(s) placed
radially outward at spacing `sF`: `(ecc+sF, 0)`. `bouma = 0.6`.

**Arm A — CROWDING (confirmatory, headline).** Peripheral target `ecc=10` (`R=6.0`).
- A1 flanked: one flanker at `sF=3` (`3 ≤ 6`) ⇒ `pool_n=2`, `recognized=0`, `pooled_ident=7≠5`.
- A2 isolated: no flanker ⇒ `pool_n=1`, `recognized=1`, `pooled_ident=5`.
- **PASS iff** A1 not recognized AND A2 recognized AND A1 `pooled_ident≠5` AND A2 `=5`.

**Arm B — FOVEAL SPARING (confirmatory, the risked dissociation).** SAME flanker spacing
`sF=3` at two eccentricities:
- B1 foveal target `ecc=2` (`R=1.2`), flanker at `sF=3` (`3 > 1.2`) ⇒ `recognized=1`.
- B2 peripheral target `ecc=10` (`R=6.0`), flanker at `sF=3` (`3 ≤ 6`) ⇒ `recognized=0`.
- **PASS iff** B1 recognized AND B2 not recognized (dissociation at identical spacing).

**Arm C — ECCENTRICITY-SCALING / Bouma (confirmatory, but ENTAILED — reported not banked,
§13.1).** For `ecc ∈ {4, 8, 12}` sweep integer `sF = 1…15`, define critical spacing
`s\*(ecc) = max sF with crowded=1`. Predicted `s\* = floor(bouma·ecc) = {2, 4, 7}`.
- **PASS iff** `s\*(4) < s\*(8) < s\*(12)` (strictly monotone). Also report `s\*/ecc`
  (≈ bouma, Bouma's constant-fraction law). *Declared forced by `R=b·ecc`; the PASS is a
  consistency check, not evidence of discovery.*

**Arm D — FLOOR / §1.1 (confirmatory; controls valid + recognizer ALIVE).**
- D1 isolated peripheral `ecc=10`, no flanker ⇒ recognized=1.
- D2 isolated foveal `ecc=2`, no flanker ⇒ recognized=1.
- D3 ALIVE: across arms both `recognized=1` (D1/D2/A2/B1) and `recognized=0` (A1/B2)
  states are reached — the recognizer is not a dead arm scoring a constant.
- **PASS iff** D1 AND D2 recognized AND D3 both states reached.

**Arm E — NOISE FLOOR (confirmatory; §1.1 dead-arm positive control; n=100 fixed,
seeds 43100–43199).** 100 random ISOLATED single-item fields (random `ecc ∈ [1,14]`,
random ident) — no flanker present. Expect `recognized=1` on ALL 100 (no false crowding
without clutter; the recognizer is not stuck at 0). **PASS iff** 0/100 false-crowded.

**Arm F — §9 OFF-DAY.** With `crowd=0` (the default), on Arm-A1 geometry: no
`crowded`/`recognized`/`pool_n` written (attrs absent or 0) ⇒ mechanism inert. **PASS iff**
inert AND: the vision bench reproduces **190 passed / 10 skipped**, the sd orbit law
`{2:1,3:2,4:2,6:2,12:4}` is unmoved, and sibling gates stay green.

**Non-gated (reported):** `b`-invariance sweep (`b ∈ {0.4,0.6,0.8}` — every qualitative
arm holds); scaling note.

**DECISION RULE.** All confirmatory arms (A,B,C,D,E,F) must PASS for the gate to pass. A
NULL in any — e.g. a foveal target ALSO crowded (B fails), an isolated target jumbled (A2/D
fail), or non-monotone crit spacing (C fails) — means eccentricity-scaled pooling does NOT
reproduce crowding as claimed, and is reported as a **clean negative** with diagnosis (§7).
A pass is reported with the §13.1 forced/risked split intact: the load-bearing evidence is
**B (foveal sparing at matched spacing)** and **A2/D/E (clutter-dependence)**; C is
consistency; the magnitude `b` is calibration.

---

## STEP 4 — PREDICTION (stated in advance, §3.7)

I predict **ALL confirmatory arms PASS**: a peripheral target loses its identity to the
pooled summary when flanked within `R=b·ecc` (A1 `recognized=0`, `pooled_ident=7`) but
survives in isolation (A2 `recognized=1`), a foveal target with the SAME flanker spacing is
SPARED (B1 recognized, B2 not — the dissociation), critical spacing grows with eccentricity
`s\* = {2,4,7}` for `ecc={4,8,12}` (C monotone), isolated and noise controls are all
recognized (D/E), and the flag OFF is byte-inert (F).

**Provisos that would teach me something if they break:**
- If B1 is CROWDED (foveal not spared) at `sF=3`, then `R(ecc=2)=1.2 < 3` failed to
  vanish enough at the fovea — the eccentricity-scaling is not steep enough near 0, or the
  radius²/distance² comparison is wrong. That would be a real negative for foveal sparing.
- If A2 (isolated) is NOT recognized, `pool_n` is counting the target itself as a flanker
  (a self-loop `co_item` bug) — a construction error, reported.
- If C is non-monotone, `pool_radius2 = bouma²·ecc2` is not being read per-item (a
  data-dependency/ordering bug between `cr_ecc` and `cr_pool`).
- The eccentricity-scaling MAGNITUDE matching `floor(b·ecc)` is NOT a risked prediction —
  it is entailed by the construction; only its qualitative monotonicity is a check that the
  build is wired correctly.

## Burned-seed ledger note (append on commit)

`43000–43999` — CROWDING (this rung). Confirmatory noise seeds **43100–43199** (Arm E);
`43000–43099` + `43200–43999` exploratory/clean.
