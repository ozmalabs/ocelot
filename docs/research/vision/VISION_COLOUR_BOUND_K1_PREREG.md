# VISION — THE k=1 HOLE IN THE COLOUR REFUSAL BOUND (PRE-REGISTRATION)

*Written and COMMITTED BEFORE the confirmatory run (§3). Completes the rung recorded in
`VISION_COLOUR_BOUND_RESULTS.md` (base `main` HEAD **41a3158c**, verified ancestor, §11).
Branch `gamma-substrate/colour-bound-k1-t1`, worktree
`.claude/worktrees/agent-adae671bebdd47a2c`.*

*Runner `scripts/colour_bound_k1_measure.py`; gate `tests/test_colour_bound_k1_migrated.py`;
pinned raw `results/colour_bound_k1_measure.json`; results
`VISION_COLOUR_BOUND_K1_RESULTS.md`. Seed `seeds/vision_colour_identity.json` v1.2.0 →
**v1.3.0** via `tools/build_vision_colour_identity.py`.*

---

## 0. SEED LEDGER — WHAT I TAKE, AND A CORRECTION TO THE BRIEF

The commissioning brief said *"seeds 50100–50999 (50000–50099 consumed by the previous
rung)"*. **That is off by one block.** The committed ledger entry (`VISION_PROTOCOL.md`,
the 50000–50999 row) reads: *"E BOUNDARY EXACT (n=100, seeds 50000–50099) … F NOISE FLOOR
(n=100, seeds **50100–50199**) … **50000–50199 consumed; 50200–50999 CLEAN**."*

**I therefore take `50200–50299` (arm DISAGREE) and `50300–50399` (arm FLOOR),** and
declare `50400–50999` still clean. Seeds `50000–50099` are used ONLY as the §3.3
already-burned PILOT block (below) and for the re-derivation cross-check, never as a
confirmatory arm.

---

## 1. THE HOLE, AND WHAT PART A MUST DO

`ci_assign`'s admission bound is the minted codebook's PACKING RADIUS
`r_i = ½·min_{j≠i}‖c_i−c_j‖`. At **k=1** the minimum is over an empty set: the radius is
undefined, the composed guard `Not(Exists(o≠winner: …))` is vacuously TRUE, and **any
colour is admitted at any distance**. The fix is therefore INCOMPLETE — it guarantees
refusal for k≥2 and nothing for k=1 — and that inconsistency is why the default was not
flipped.

**PART A: derive a k=1 bound, or honestly conclude none exists.** It must FALL OUT (§13),
not be chosen. Rivals are rejected BY MEASUREMENT wherever a measurement can decide it.

**PART B: flip the default to `bound = 1.0`, but only under the decision rule in §5.**

---

## 2. THE §3.3 PILOT (already-burned material only — seeds 50000–50099 and the five
landed scenes)

Run BEFORE this pre-registration, on already-burned seeds and committed scenes only, to
fix n and to establish which arms can discriminate. Reported here in full so nothing is
retro-fitted (§4):

| pilot measurement | value |
|---|---|
| cluster extent (max member-to-prototype distance), all 5 landed scenes | **0.0** |
| `achromatopsia_SPLIT_CLEAN` | k=1, **n_distinct_obs = 1**, scene range **0.0** |
| `achromatopsia_FLOOR` | k=1, **n_distinct_obs = 1**, scene range **0.0** |
| `colour_identity_E` | k=3, n_distinct_obs = 3, scene range 20.0, packing **7.8102** |
| `achromatopsia_DISSOCIATION` | k=2, n_distinct_obs = 2, packing **10.0** |
| k=1 defect (SPLIT_CLEAN + far probe), flag **ON** | admitted, `sign_dist` **276.4797**, `ci_refused` 0 |
| packing radius under codebook growth | `{(0,0)}` → undefined; `+(100,0)` → **50.0**; `+(20,0)` → **10.0** |
| opponent coordinates integral, 100 burned probes | **100/100** |

n for the two random arms is fixed at **100**, matching the landed rung's own arms E and F
(same stimulus generator, same scene, same readout) so the arms are directly comparable.

---

## 3. PART A — THE CANDIDATE AUDIT (hypotheses, two-sided)

**H_A0 (the derivation I expect to survive):** the packing radius is **NON-INCREASING
under codebook growth** — `r_i(S′) ≤ r_i(S)` for `S ⊆ S′`, because a minimum over a
superset cannot increase. The k=1 radius is therefore an upper bound on every radius
reachable by growth from `{c₁}`, and that supremum is **unbounded** (place `c₂` at
distance `D`, get `r = D/2`, `D` arbitrary). Hence **r(k=1) = +∞: admit everything.**
**The vacuity is ENTAILED by the same monotonicity that makes the k≥2 bound a bound at
all** — it is not a missing derivation, it is this derivation's own limit. Two-sided: if
monotonicity fails to hold in the built seed, H_A0 is dead and a finite k=1 bound is back
on the table.

**H_A1 (the structural root):** every length scale in this seed lives **BETWEEN**
prototypes, because `ci_mint_category` clusters by EXACT value, so a quantum has **zero
intrinsic extent**. With one prototype there is no "between", and the seed contains no
other length scale. Predicted consequence: no finite k=1 bound can fall out of THIS
mint; unblocking it requires the colour-identity rung's own NAMED FRONTIER (perceptual
NEARNESS in minting), which would give a quantum an extent.

### The five rivals, and how each is decided

| # | rival k=1 bound | how it is decided | predicted verdict |
|---|---|---|---|
| **R1** | the mint's own **cluster extent** | measure it on all 5 landed scenes | ≡ **0** (ENTAILED by exact-value minting — declared NOT risked, §13.1); ⇒ "exact match only"; violates H_A0 monotonicity; already measured by the previous rung to REGRESS at k≥2 | **REJECT** |
| **R1′** | the **observational-resolution floor** `√2/2` (covering radius of ℤ²) | measure integrality of every observed opponent coordinate | indistinguishable from R1 on an integer lattice (no probe can lie in `(0, √2/2)`); and it is an ABSOLUTE constant — a view from nowhere (§13 corollary) | **REJECT — not an independent candidate** |
| **R2** | the **lattice step 1.0** | inherited measurement (previous rung, injected control 4: turned arm C red) | REGRESSES at k≥2; absolute constant; violates monotonicity | **REJECT** |
| **R3** | the **scene's measured dynamic range** (T3's anchor idiom, "the frame's own measured ceiling"), `½ · max pairwise distance among distinct observed values` | (a) evaluate on the two landed k=1 scenes; (b) **NON-LOCALITY probe** — same codebook, same observation, add an UNRELATED patch elsewhere in the field and re-decide | (a) **0.0** in both landed k=1 scenes ⇒ degenerates to R1 and does not close the hole where it matters; (b) verdict **FLIPS** refused→admitted because of a patch the observation has nothing to do with | **REJECT — measured** |
| **R4** | **observed-separation**: `½ · min` over distinct OBSERVED colour values (minted or not), excluding the observation's own | (a) agreement with packing at k≥2 over the 100 burned probes; (b) definedness at k=1 | (a) **0 disagreements** — the ONLY rival consistent with the landed bound; (b) **UNDEFINED** at k=1 (n_distinct_obs = 1 measured in both landed k=1 scenes; in the defect scene the only competitor IS the winner) | **REJECT — consistent but undefined** |
| **R5** | **hypothetical self-mint** — the packing radius computed with a quantum hypothetically minted AT the observation | algebra: competitor sits at exactly `d`, so `2d ≤ d ⟺ d ≤ 0` | collapses to R1 | **REJECT** |

**THE CRUX SENTENCE, pre-registered:** *the rivals that are DEFINED at k=1 are
INCONSISTENT with the landed k≥2 bound; the one rival that is CONSISTENT is UNDEFINED at
k=1.*

### PART A's decision rule

- If a candidate is defined at k=1, consistent with the landed k≥2 bound (0 disagreements
  on the burned probes), local, and monotone ⇒ **it is the k=1 bound; build it.**
- If every candidate fails at least one of those four ⇒ **NO k=1 BOUND EXISTS**, reported
  as a first-class negative (§7) with the measured rejection of each rival and the named
  unblocking change.
- **A null here is a RESULT, not a failure**, and it does not by itself veto PART B (§5).

### DECLARED DEVIATION FROM THE BRIEF (§3 item 6)

The brief pre-supposed a k=1 bound would be found and named an arm *"k=1 BOUND REFUSES
it"*. **If PART A returns the predicted null, that arm is VOID** — there is no bound to
refuse with — and it is replaced by the derivation arms **MONO**, **NONLOCAL** and
**CONSISTENT-BUT-UNDEFINED**, which are what the null is made of. Declared here, in
advance, rather than reported as a substitution afterwards.

**Consequence for the build: if PART A is null, this rung adds NO new rule and NO new
Term — the ONLY seed change is the default flip.** No new guard is written, so process
rule 3 (absence-tolerant, never `PickUnique` on a params node) is satisfied vacuously,
and the existing `Not(Exists(…))` guard — which is already absence-tolerant by
construction — is untouched.

---

## 4. THE ARMS

Every RISKED arm names the input that would make it fail, and that input is confirmed to
lie in the tested range (process rule 6).

| arm | statistic | PASS iff | RISKED? | what would fail it |
|---|---|---|---|---|
| **A — k=1 DEFECT REPRODUCED** | far probe vs the single-quantum codebook, flag **ON** | admitted, `ci_refused = 0`, `sign_dist ≈ 276.4797` | **RISKED** | the probe being refused at k=1 — i.e. the hole not being real. In range: the probe sits at 276.48, and the bound is armed. |
| **MONO — the derivation** | packing radius along a growth chain `{c₁} ⊂ {c₁,c₂} ⊂ {c₁,c₂,c₃}` | radii non-increasing, AND for every finite candidate `r₀ ∈ {0, √2/2, 1.0, 138.24}` an extension exists whose radius **exceeds** `r₀` | **RISKED** | a non-monotone radius, or a finite `r₀` no extension can exceed. In range: extensions are constructed at `4·r₀+1`, so the exhibited radius is `2·r₀+0.5 > r₀` for every `r₀ ≥ 0`. |
| **NONLOCAL — R3 rejected** | R3's verdict on one fixed observation vs one fixed codebook, with/without an unrelated far patch | the verdict **FLIPS** (refused → admitted) | **RISKED** | the verdict NOT flipping ⇒ R3 is local and survives as a candidate. In range: probe (30,0), patch (400,0). |
| **UNDEF — R4 rejected** | (a) R4 vs packing over 100 burned probes; (b) R4's definedness in the two landed k=1 scenes | (a) 0 disagreements; (b) undefined in both | **RISKED** | R4 disagreeing at k≥2 (not the consistent rival) or being DEFINED at k=1 (then it closes the hole and PART A is positive). |
| **EXTENT — R1 characterised** | cluster extent over all 5 landed scenes | ≡ 0.0 | **ENTAILED (§13.1) — reported, NOT banked** | nothing: exact-value minting forces it. Declared unrisked in advance. |
| **NOREG — NO REGRESSION (THE CONJUNCTION)** | with the flag ON **by default**: (a) the 36-cell k=3 field; (b) the landed dist-4 off-prototype probe; (c) recognize-not-re-mint; **(d) the k=1 field** | (a) 36/36 assigned at dist 0, 0 refused; (b) still assigned to (10,0) at dist 4; (c) `n_cats` 3→3; (d) 36/36 assigned at k=1, 0 refused | **RISKED** | **a refuse-everything build MUST fail here** — this is the arm that catches it (process rule 5). In range: (b) sits at 4.0 against a bound of 7.8102, margin 3.81. |
| **DISAGREE** | graph decision vs the independently re-derived packing predicate, n=100, **seeds 50200–50299**, at k=1 AND k≥2 | **0 disagreements**, and non-degenerate BOTH ways at k≥2 (≥1 admitted, ≥1 refused) | **RISKED** | any pointwise disagreement; a degenerate all-admit or all-refuse split. Previous rung measured 7/93 on its own block, so both outcomes are reachable. |
| **FLOOR** | iid colour-noise fields, n=100, **seeds 50300–50399** | 0/100 mint, 0/100 sign | **RISKED** | any field minting a category. |
| **DELTA-ON-FLIPPED** | every changed field across the five landed scenes with the default **FLIPPED**, plus the enumerated blast radius | target **EMPTY** on the landed percept scenes | **RISKED** | any changed percept field ⇒ **DO NOT FLIP** (§5). |
| **GATES** | committed suites | colour-identity 6/6, achromatopsia 5/5, colour-bound 20/20 (as amended, §6), **L1b uniqueness 21/21**, sd orbit law `{2:1,3:2,4:2,6:2,12:4}` unmoved, bench **200/0** with `data/` | **RISKED** | any red. Baseline measured on this worktree BEFORE any file was added: **200 passed / 0 failed**. |

**Process rule 5 is honoured explicitly.** The previous rung MEASURED that a
refuse-everything build leaves arms B, D and F **green** — floors are not a gate. This
rung therefore carries **NOREG** (the no-regression conjunction, now including the k=1
field) and **DISAGREE** (pointwise agreement), and both will be positive-controlled
against an injected refuse-everything build.

---

## 5. PART B — THE FLIP: THE DECISION RULE, FIXED IN ADVANCE

**FLIP `ColourIdentityParams.bound` 0.0 → 1.0 iff ALL THREE hold:**

1. **PART A returns either a finite k=1 bound that falls out, OR a POSITIVE, MEASURED
   argument that no finite k=1 bound is consistent with the landed bound** (H_A0's
   monotonicity, with every rival rejected by measurement). A bare *"I looked and did not
   find one"* is **NOT** sufficient and does not license the flip.
2. **DELTA-ON-FLIPPED is EMPTY on the landed PERCEPT scenes** (colour identity E and G;
   achromatopsia DISSOCIATION, SPLIT_CLEAN, FLOOR) — zero changed fields.
3. **At k=1 the flag ON is byte-identical to the flag OFF**, so the flip cannot regress
   the dead zone: it is a STRICT improvement (refusal gained at k≥2, nothing lost at
   k=1), never a total guarantee.

**If any of the three fails: DO NOT FLIP.** Report the delta and leave the flag at 0.0.

### THE CARVE-OUT, DECLARED IN ADVANCE (not discovered afterwards)

A strict *"any delta anywhere ⇒ no flip"* rule is **incoherent here**, and I say so before
running rather than after: **L1b's `audit_colour_identity`
(`scripts/uniqueness_measure.py`) is a RECORD OF THE DEFECT** — it asserts
`has_admission_bound: False` and pins the far probe assigned at 269.52 with margin
0.0000. Under a strict rule the defect could never be fixed by default, because the gate
that FOUND it asserts it still exists.

**PREDICTED (§3.7), and it is a risked prediction:** the delta will be **EMPTY** on
colour-identity and achromatopsia (the previous rung measured zero changed fields on
exactly those scenes) and **NON-EMPTY on L1b**, whose audit deliberately presents the two
probes the bound exists to refuse.

**The resolution is to make L1b's implicit assumption EXPLICIT, not to weaken it:**
`audit_colour_identity` will set `bound = 0.0` explicitly, so its claim becomes *"without
an admission bound, ci_assign does this"* — which is what its own text already says it is
auditing, and which stays TRUE forever regardless of the default. This is a
meaning-PRESERVING one-line edit, enumerated in §6, and **I will measure and report
whether L1b's gate would have gone red without it** rather than quietly preventing it.

If instead the delta touches any colour-identity or achromatopsia PERCEPT value, the
carve-out does not apply and the flip is off.

---

## 6. §9 — THE BYTE-IDENTITY CLAIM SHIFTS, AND HERE IS THE FULL ENUMERATION

Flipping deliberately changes the default, so the claim moves from *"unchanged"* to
**"changed, measured, and enumerated"**. Exactly these things move, and nothing else:

| # | file | change | why |
|---|---|---|---|
| 1 | `seeds/vision_colour_identity.json` + its builder | `ColourIdentityParams.bound` **0.0 → 1.0**; version **1.2.0 → 1.3.0**; description records the k=1 null and the caveat | **the flip itself** |
| 2 | `tests/test_colour_bound_migrated.py::test_the_flag_ships_OFF_in_the_seed` | retargeted to assert the flipped default + the recorded caveat | it asserts `bound == 0.0`; the flip is deliberate |
| 3 | `tests/test_colour_bound_migrated.py::test_X_offday_*` docstring | says "OFF by default"; the arm itself sets `bound=0.0` EXPLICITLY and is unchanged in behaviour | a now-false sentence about the default; the test still checks "flag at 0 ⇒ inert" |
| 4 | `tests/test_colour_bound_migrated.py::test_this_rung_touches_no_other_rungs_files` | `owned` set gains this rung's four artifacts | its diff is computed vs `afc195b9`, so it now legitimately spans both rungs |
| 5 | `scripts/uniqueness_measure.py::audit_colour_identity` | sets `bound = 0.0` explicitly | §5 carve-out — makes the defect record's assumption explicit and permanent |
| 6 | `VISION_PROTOCOL.md` | ledger + ladder append | §10 provenance |

`test_this_rung_adds_NO_Rust` and `test_this_rung_edits_exactly_ONE_committed_seed` are
predicted to stay **GREEN UNCHANGED**: this rung adds no Rust and touches the same single
seed. **No rule's `match`, `where` or `effects` changes** — if PART A is null, the only
seed edit is one attribute default.

---

## 7. WHAT I PREDICT, WITH PROVISOS (§3 item 7)

**I predict PART A is NULL** — no finite k=1 bound falls out — with H_A0 and H_A1 both
holding, all five rivals rejected as tabled, and the crux sentence surviving verbatim. **I
predict the flip PROCEEDS**: all three §5 conditions met, DELTA-ON-FLIPPED empty on the
five landed percept scenes, L1b the only non-empty entry and handled by the declared
carve-out. **I predict every arm passes.**

**Provisos — the things I expect to hold, so that a break tells me what I did not
understand:**

1. **Monotonicity holds in the BUILT seed, not merely in the algebra** — the graph's
   decision, not my Python re-derivation, must show the radius shrinking as the codebook
   grows.
2. **The k=1 landed scenes stay at 36/36 assigned** under the flip — if the bound somehow
   bites at k=1, H_A0 is wrong and the flip is off.
3. **`Times` is used in the ITEMS-LIST form everywhere it appears.** The previous rung's
   prediction about WHERE the `a`/`b` empty-product trap would bite BROKE because the
   composition changed after pre-registration. **This rung changes NO composition**, so
   the trap's signature is inherited unchanged, and I predict the injected trap reddens
   **B, D and E of the previous gate** exactly as that rung measured — plus **DISAGREE**
   here. If it reddens a different set, my understanding of the inherited guard is wrong
   and I will say so.
4. **The refuse-everything control reddens NOREG and DISAGREE and leaves the floors
   green** — the previous rung's finding, re-measured on this rung's arms.

**What a null means (§3 item 5):** if PART A returns a bound after all, the rung builds it
and the brief's original arm list applies. If the flip is blocked by condition 2 or 3, the
rung ships the k=1 derivation as a documented negative and **leaves the flag OFF** — that
is a complete, reportable outcome, not a failure.

---

## 8. BOUNDS — WHAT THIS RUNG WILL NOT DO (§8)

- It will **not** widen any invariance class, build a margin gate (L1c remains NAMED, NOT
  BUILT), touch `df_recognize` or T1's near-vacuous bound, or alter the mint.
- It will **not** claim the k=1 regime is fixed. If PART A is null, the flip ships with an
  **explicit documented caveat**: refusal is guaranteed for **k ≥ 2 only**, and a
  single-quantum codebook admits everything — recorded in the seed description, the
  results file, and a test that PINS the caveat.
- **DELTA-ON covers the five landed scenes and the enumerated blast radius**, not the
  space of all stimuli.
