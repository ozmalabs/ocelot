# VISION — COLOUR IDENTITY'S REFUSAL BOUND: the PACKING RADIUS of the minted codebook (RESULTS)

*Confirmatory run of `VISION_COLOUR_BOUND_PREREG.md`, authored and **committed BEFORE
the run** at **`01811a78`** (§3). Runner `scripts/colour_bound_measure.py`; seed
`seeds/vision_colour_identity.json` v1.1.0 → **v1.2.0** (builder
`tools/build_vision_colour_identity.py`); adapter `domains/colour_bound_world.py`;
gate `tests/test_colour_bound_migrated.py`; pinned raw
`results/colour_bound_measure.json`. Seeds **50000–50099** (boundary-exact),
**50100–50199** (noise floor). Base `main` HEAD **afc195b9**
(`git merge-base --is-ancestor afc195b9 HEAD` verified, §11). Branch
`gamma-substrate/colour-refusal-bound-t1`.*

*A DEFECT FIX for a LANDED rung. L1b (`VISION_UNIQUENESS_RESULTS.md`) audited every
merged codebook rung for the silent-`Argmin` hazard and found `ci_assign` to be **the
worst case in its table**: an `Argmin` over `ColourCategory` with **ZERO `Lte`** — no
admission bound of any kind. It could not refuse, ever.*

## Engine / bench / provenance (§10)

- **Engine `7d5f50c18673`** @ `runners/dsl/python/substrate_rs/_native.abi3.so` —
  **shared build, Rust source byte-identical** to canonical (`provenance_line()`
  reads *"shared build from … — Rust source identical"*). This rung adds **NO Rust**,
  so the shared build is legitimate (§10.1 rule 4). **No new engine hash — there is
  truly no `.rs` change**, gated by `test_this_rung_adds_NO_Rust` pinned to the
  rung's own diff (§12.3).
- `data/` symlinked to canonical (§10.2). **Baseline measured on this worktree BEFORE
  any file was added: 200 passed / 0 failed.** After the rung: **200 / 0**, unchanged.
- **NO new Rust, NO new seed, ONE seed edit** (`vision_colour_identity` 1.1.0 →
  1.2.0: a `bound` flag + one disjunct on `ci_assign` + the new `ci_refuse` rule).
  The flag ships at **`0.0` = OFF**, so §9 byte-identity holds by construction and is
  verified below.

---

# PART A — THE AUDIT and THE DERIVATION

**VERDICT: COMPOSE. NO new Rust. The bound is the codebook's own PACKING RADIUS.**

### The defect, confirmed in the source and reproduced

`ci_assign`'s `where` (`tools/build_vision_colour_identity.py:219`) contains the flag,
the lesion guard, `_all_op_done`, `Count(ColourCategory) > 0` and the epoch re-arm —
**and no predicate on the distance at all**. The `Argmin` ranks; nothing admits.
Reproduced here as arm A, matching L1b's pinned numbers term for term.

### Four candidate derivations — THREE REJECTED, and the rejection was MEASURED

| candidate | derivable? | verdict |
|---|---|---|
| **mint cluster extent** | yes, but **degenerate ≡ 0** (`ci_mint_category` clusters by EXACT value, `:127-131`, so every member sits at distance 0) | **REJECTED — REGRESSES** |
| **lattice step `1.0`** (L1's own falls-out bound) | yes | **REJECTED — REGRESSES** |
| **MDL radius from `m_min`/`d`** | **NO.** `m_min=3` is a **COUNT** gate (`m > d/(d−1)`); the cost model `k·d + N` charges 1 per label and treats the residual as free. It constrains how MANY members a category needs and **never how far one may lie** — there is no radius in the accounting. | **REJECTED — NOT DERIVABLE** |
| **PACKING RADIUS** `r_i = ½·min_{j≠i}‖c_i−c_j‖` | **yes** | **ACCEPTED** |

**The two "REGRESSES" verdicts are not arguments — they are measurements.** Control 4
below injects the lattice-step bound into the real build and **turns arm C RED**: the
landed dist-4 probe is refused. The audit's rejection is empirical.

### THE DERIVATION — why the bound falls out (§13)

`ci_assign` is a **dequantizer**. For a codebook `{c_i}`, the largest ball around a
prototype guaranteed to lie inside its own Voronoi cell — the radius at which the
codebook's quanta **do not overlap** — is the **packing radius** `r_i = ½·min_{j≠i}
‖c_i−c_j‖`. Two balls of radius `r` around prototypes separated by `D` are disjoint
iff `2r ≤ D`. So admission is

  **`2 · dist(R, winner) ≤ min_{c≠winner} dist(winner, c)`**

**It falls out rather than going in, and this is measured, not asserted:**

1. **It is a function of the codebook, not a literal.** Measured: **7.8102** on colour
   identity's 3-category codebook, **10.0** on achromatopsia's 2-category codebook,
   **undefined** at k=1. *I chose none of these values.* A tuned threshold is one
   number written once; this is an expression that yields whatever the codebook
   implies. Gated by `test_the_bound_introduces_no_tuned_constant`, which asserts the
   derived values appear in **no executable term** — only, at most, in the rules'
   documentation prose.
2. **It reuses the distance `ci_assign` already computes** (`_dist`, `:211-214`),
   applied prototype-to-prototype. No new metric, no new frame — coordinates stay
   integer, the continuous stays in the cross-frame comparison (the frame/continuum
   invariant, preserved).
3. **The only literal added is `2`** — the non-overlap factor of `2r ≤ D`, i.e. the
   *definition* of a packing radius. The seed's whole literal set is now
   `{0.0, 0.5, 1.0, 2.0, 3.0}`, gated.

### Composition — held Terms only, and ONE deviation from the prereg, declared

| needed | held Term | where |
|---|---|---|
| the complement test | `Not` + `Exists` | `jsonio.rs:1266`, `:1152` |
| "a different prototype" | `Eq` on `Value::Node` (by id) | the `retire_duplicate_gap` precedent |
| the gap and the residual | `Lt`, `Times`, `Sqrt`, `Minus`, `Plus` | already in this seed |
| the winner | `Argmin` | already in `ci_assign` (`:217`), reused verbatim |
| the flag | `Gt`/`Lt` on `ColourIdentityParams` | the idiom `identity`/`achromatopsia` use |

**DEVIATION, DECLARED (§3 item 6 / §5).** The prereg named the composition
`Or([Lt(Count(others),1), Lte(Times([2, d]), MinOver(others, …))])`. **The shipped form
is the logically equivalent `Not(Exists(o: o≠winner ∧ dist(winner,o) < 2·d))`.** Same
predicate, same bound, same derivation — but absence-tolerance at **k=1 falls out
STRUCTURALLY** (`Exists` over an empty source is false, so `Not(Exists)` is true) and
the separate `Count` guard and the `MinOver` default both disappear. The change
*removes* a guard rather than rescuing a result, and it was made before any arm was
run. **It is not free of consequence and I report the consequence in PART C: it
inverts the direction of the `Times`-trap control, and my pre-registered prediction
about which arms that control would redden was WRONG.**

---

# PART B — THE ARMS

**VERDICT: all seven gated arms PASS; DELTA_ON is EMPTY.**

| arm | statistic | result | vs prereg |
|---|---|---|---|
| **A DEFECT REPRODUCED** *(premise; RISKED)* | flag OFF: far probe assigned? margin? | **assigned, `sign_dist = 269.5199`, refused 0**; equidistant assigned at `10.0`, **margin exactly `0.000000`** | reproduces L1b term-for-term ✓ |
| **B BOUND REFUSES** *(RISKED)* | flag ON: far probe | **`ci_refused = 1`, `sign_dist = −1.0`** (never assigned), `ci_refused_dist = 269.5199`; bound **7.8102** | refused ✓ |
| **C NO REGRESSION** *(THE CONJUNCTION; RISKED)* | flag ON: every landed assignment | **(a) 36/36 assigned, 0 refused, all `dist 0`; (b) the dist-4 probe STILL assigned to (10,0); (c) seen colour recognized, `n_cats` 3→3** | all three ✓ |
| **D AMBIGUITY** *(RISKED)* | the 0.0000-margin probe | **REFUSED**, `winner_dist 10.0` vs bound `7.8102`, **2 tied candidates, tie-independent** | refused, no special case ✓ |
| **E BOUNDARY EXACT** *(RISKED, n=100, 50000–50099)* | graph decision vs re-derived predicate | **0 disagreements / 100**, **7 admitted / 93 refused** (non-degenerate BOTH ways) | 0 ✓ |
| **F NOISE FLOOR** *(RISKED, n=100, 50100–50199)* | fields minting or signing | **0/100 mint, 0/100 sign** | 0 ✓ |
| **X OFF-DAY** *(§9; ENTAILED)* | flag at default 0 | `max ci_refused = 0`, far probe assigned exactly as before | inert ✓ |

## The headline — the bound refuses BOTH of L1b's exposing probes and costs NOTHING

**L1b's two pathological probes are now refused, and not one landed assignment moved.**

- The **far probe at opponent distance 269.52** — 34× outside the 7.8102 packing
  radius — is refused, and says so (`ci_refused`), rather than silently receiving a
  category sign.
- The **0.0000-margin equidistant probe** is refused **by the same bound, with no tie
  rule and no special case**: it sits at distance 10.0 from *both* tied candidates,
  and both exceed 7.8102, so the `Argmin`'s arbitrary tie-break cannot change the
  verdict. **Tie-independence is measured, not argued** (`n_tied = 2`,
  `tie_independent = True`).
- **Arm E is what makes the bound load-bearing (§13.2):** across 100 random probes the
  seed's admit/refuse decision agrees **pointwise** with the independently re-derived
  packing predicate — **0 disagreements** — with **7 admitted and 93 refused**, so
  neither a refuse-everything nor an admit-everything build can pass it.

## THE MEASURED CONFOUND CHECK — arm E's shared scene

Arm E adds its 100 probes to ONE settled scene, so probe regions accumulate and could
in principle grow the codebook mid-arm and invalidate the comparison against the
codebook captured at the start. **Checked, not assumed:** the codebook did **not**
grow (`k` 3 → 3 across all 100 probes), and a **fresh-scene-per-probe re-run gives
IDENTICAL numbers** (0 disagreements, 7 admitted, 93 refused). Reported because it
was a real hazard, and because "it passed" is not the same as "it could not have been
corrupted".

---

# PART C — WHAT I PREDICTED, AND WHAT I GOT WRONG (§3 item 7 / §7)

I predicted **A–F and X all PASS and DELTA_ON EMPTY** — confirmed on every arm, and
all four provisos held: no landed observation lay outside its packing ball; the two
k=1 achromatopsia scenes were unchanged **for the reason stated in advance** (radius
undefined, not a lucky loose bound); `ci_refuse` terminated; the refusal was
tie-independent.

**WHAT I GOT WRONG — the `Times`-trap control's predicted signature.** The prereg
stated the `Times` a/b trap (empty product = 1) *"would silently turn the bound into
the constant 1.0 and refuse arm A(b)"*, i.e. **redden arm C**. That reasoning was
correct **for the `Lte`/`MinOver` composition the prereg named**. In the shipped
`Not(Exists(… < 2·d))` form the same defect makes the comparand the constant `1.0`,
and since prototypes are ≥ 15.6 apart **no** prototype satisfies `dist < 1.0` — so the
build **admits everything** and reddens **B, D and E** instead. Measured:

> `times_ab_trap: 3 failed` — `test_B…`, `test_D…`, `test_E…`. **Arm C stayed green.**

The trap is still caught, loudly, by three tests. But **my predicted failure mode was
wrong, and it was wrong because I changed the composition after pre-registering it.**
Recorded here rather than quietly re-described (§3 item 7, §5), and it is the concrete
argument for why arm E — a pointwise agreement test, red under **all four** injected
defects — is worth more than any single-probe arm.

---

# PART D — THE DELTA-ON MEASUREMENT (§9) — reported, not gated

**The question the parent asked: with the flag ON, does any landed result change?**

**ANSWER: NO. Zero changed fields across all five landed scenes.**

| landed scene | k | packing radius | assigned OFF → ON | refused OFF → ON | **changed** |
|---|---|---|---|---|---|
| colour identity **E** (3 clusters) | 3 | **7.8102** | 36 → 36 | 0 → 0 | **{}** |
| colour identity **G** (36-shade gradient) | 0 | — (no codebook) | 0 → 0 | 0 → 0 | **{}** |
| achromatopsia **DISSOCIATION** | 2 | **10.0** | 36 → 36 | 0 → 0 | **{}** |
| achromatopsia **SPLIT_CLEAN** | 1 | **undefined** | 36 → 36 | 0 → 0 | **{}** |
| achromatopsia **FLOOR** | 1 | **undefined** | 36 → 36 | 0 → 0 | **{}** |

Every landed assignment sits at **distance 0** (exact recognition) or **distance 4**
(colour identity's off-prototype probe) against bounds of **7.8102 / 10.0 /
undefined**. Nothing is near the boundary; nothing moves. `n_categories`,
`categories`, per-cell `signs`, `max_sign_dist` and `epoch` are identical in both arms
for every scene.

**Two of those five are unchanged for an HONEST reason, not a flattering one.**
`SPLIT_CLEAN` and `FLOOR` are **k=1**: the packing radius is undefined, the bound is
**vacuous**, and `ci_assign` there still cannot refuse anything at any distance. This
is pinned as a fact of the build by `test_the_k1_hole_is_REAL_and_is_reported_not_hidden`,
which asserts the k=1 predicate admits a probe 14,000 units away. **The defect is
fixed for k ≥ 2 and is NOT fixed at k = 1.**

## RECOMMENDATION on flipping the default — the parent's call, left UNFLIPPED

**The measurement supports flipping, and I have not flipped it.** The case for:
DELTA_ON is empty, so flipping costs zero measured recall on every landed scene; the
bound refuses both of L1b's pathological probes; arm E shows it is exactly the derived
predicate, not an approximation; and unlike L1b's own uniqueness gate — which *"buys
honesty with recall"* and refuses correct-but-ambiguous rows from g=0.1 downward —
**this bound has no measured cost at all.**

The case for caution, which is why I left it OFF: (1) the k=1 hole means flipping
delivers an *inconsistent* guarantee — refusal for k ≥ 2, none for a single quantum —
and a partial guarantee that looks total is its own hazard; (2) DELTA_ON covers the
**five landed scenes**, not every future stimulus, and 93/100 random probes are
refused, so any downstream consumer that assumed a sign always exists **will now meet
`sign_dist = −1.0`**; no such consumer exists today, but `ci_assign` is a published
surface. (3) §9's discipline is that the flip is a separate, deliberate decision with
its own justification — not a side effect of the rung that measured it.

---

## THE POSITIVE CONTROLS (§12.3 / process rules 4 and 5) — measured, not asserted

Four defects injected into the real builder; each regenerates the seed, runs the gate,
then reverts. **After revert the seed is BYTE-EQUAL to the committed one and the gate
is 20/20** (verified by JSON compare, not by eye).

| injected defect | tests RED | what it proves |
|---|---|---|
| **1. `Times` a/b trap** (empty product = 1) | **3** — B, D, E | process rule 4. Caught loudly — though **not** on the arm I predicted (PART C). |
| **2. REFUSE EVERYTHING** (`_bound_ok ≡ false`) | **5** — **both C tests**, DELTA_ON, E, constants | **process rule 5, the crux.** **B, D and F stay GREEN** — a build that refuses everything scores a PERFECT FLOOR on the refusal arm, the ambiguity arm and the noise floor. **Neither a floor arm nor a discrimination arm is a gate; the CONJUNCTION is.** |
| **3. VACUOUS bound** (`_bound_ok ≡ true`, the pre-fix behaviour) | **4** — B, D, E, constants | **C stays GREEN** — the mirror image of control 2, confirming C and B/D/E test opposite failure directions. |
| **4. LATTICE-STEP bound** (the REJECTED rival derivation, radius 1.0) | **5** — **both C tests**, E, held-terms, constants | **converts the audit's "REGRESSES" from an argument into a measurement** — the rejected candidate really does refuse the landed dist-4 probe. |

**Arm E is red under all four.** Arm C is red under exactly the two builds that
over-refuse. That pairing is the gate.

## §13.1 — ENTAILED vs RISKED, declared BEFORE the run, honoured here

**ENTAILED, reported as consistency and NOT banked:** arm **X** — the flag ships at 0
and every new clause is a vacuously-true disjunct at that value, so inertness is
entailed by construction.

**RISKED — this is the result:** **A** (the premise could have failed to reproduce),
**B**, **C** (the discriminating arm), **D**, **E**, **F**.

**Each risked arm's failure input was stated in advance and is IN RANGE — verified by
injected defect, not asserted.** The sharpest is **C**: its probe sits at **distance
4.0** against a bound of **7.8102** — a margin of **3.81**, genuinely inside the region
where a tighter bound bites — and controls 2 and 4 **drove it red on real injected
defects**. No arm passed while sitting outside the region where it could fail.

---

## §9 — defaults preserve committed results

- **Rung-7 named vision bench `scripts/rung7_vision_bench.sh`: 200 passed / 0 failed**
  with `data/` symlinked — identical to the baseline measured on this worktree
  **before any file was added**. Its no-python-thresholds scan reports *"(none — every
  knob is graph data)"*. **The bench file itself is NOT edited** (the colour rungs'
  gates were never in that list; this rung follows their sibling-gate precedent).
- **The landed results file re-runs BYTE-IDENTICAL.** Re-running
  `scripts/colour_identity_measure.py` against the edited seed reproduces
  `results/colour_identity_measure.json` with **the only diff being `elapsed_s`** —
  every measured value unchanged.
- **Sibling gates: 89 passed in one process** — colour-identity **6/6**,
  colour-salience **6/6**, achromatopsia **5/5**, **L1b uniqueness 21/21**,
  sdloop-vision, dimension-inference, engine-provenance, and the new gate **20/20**.
- **The sd orbit law `{2:1,3:2,4:2,6:2,12:4}` is UNMOVED**
  (`test_orbit_law_arithmetic_matches_the_measured_mint_counts` passed).
- **New gate `tests/test_colour_bound_migrated.py`: 20 passed**, and **verified to
  fail on four independently injected defects** (3, 5, 4 and 5 red respectively).
- The seed's diff vs v1.1.0 is exactly: the `bound` attr, ONE added disjunct on
  `ci_assign`'s `where`, the new `ci_refuse` rule, and version/description.
  **`ci_opponent` and `ci_mint_category` are BYTE-IDENTICAL; no rule's `effects`
  changed** (verified by JSON compare).

## BOUNDS (§8) — what this rung does NOT do

- **A REFUSAL BOUND for `ci_assign` ONLY.** It cannot widen any invariance class — no
  colour refused before is assigned now; the bound can only turn an assignment into a
  refusal. It fires only where `ci_assign` already claimed.
- **THE k=1 HOLE IS NOT FIXED.** With one minted quantum the packing radius is
  undefined, the bound is vacuous, and `ci_assign` still cannot refuse at any
  distance. Correct vector-quantization semantics (a lone quantum owns all of space),
  **stated in the prereg before the run, pinned in a test, and repeated here.** A k=1
  bound would need a different derivation — there is no second prototype to derive
  one from — and is **NAMED, NOT BUILT**.
- **It is a CODEBOOK-GEOMETRY bound.** It says nothing about whether the minted
  categories are the RIGHT ones; the mint's MDL gate is untouched.
- **NOT a margin gate.** L1b named **L1c (the margin instrument)** and left it; this
  rung does not build it either. The packing radius is a DISTANCE bound: arm D refuses
  the 0-margin probe because it is far from **both** candidates, not because they are
  close to **each other**. A probe *near* two adjacent prototypes is still decided by
  the `Argmin`'s ranking.
- **DELTA_ON covers the five LANDED scenes**, not the space of all stimuli. The
  measured claim is "no committed result changes", not "nothing can ever change".
- **The other rungs L1b flagged are UNTOUCHED**: `df_recognize` (flagged
  structurally, never measured) and **T1 continuous pose's near-vacuous bound** — where
  L1b measured ≥2 candidates in bound in 63/63 trials — remain exactly as L1b left
  them. This rung fixes `ci_assign`, nothing else.
- Inherited from colour identity, unchanged: abstract cone-triple grain, exact-value
  minting, the 2-D opponent subspace, no colour constancy, no bound object. The
  **perceptual-nearness frontier in MINTING** remains unreached.
- **The default is NOT flipped.** That decision is the parent's; this rung supplies
  the measurement and a recommendation, and leaves the flag at `0.0`.

## Why this is believed

Because it fails where it must, and because the two things that would have made it
worthless were tested rather than assumed. **A build that refuses everything scores a
perfect floor on B, D and F** — so those arms were never the gate; control 2 shows the
conjunction catching it on C and E. **The bound could have been a magic number in
disguise** — so arm E checks the graph's decision against the re-derived predicate
pointwise across 100 probes, the derived values are gated out of every executable
term, and the same expression yields 7.8102, 10.0 and undefined on three different
codebooks with none of them chosen. The rejected rival derivation was **injected and
measured to regress**, not merely argued against. The one prediction that broke — the
`Times` control's failure signature, inverted by a composition change I made after
pre-registering — is reported with the reason, and the k=1 hole is stated three times
rather than buried once.
