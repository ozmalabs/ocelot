# VISION — THE k=1 HOLE IN THE COLOUR REFUSAL BOUND: A DERIVED NEGATIVE, AND THE FLIP (RESULTS)

*Confirmatory run of `VISION_COLOUR_BOUND_K1_PREREG.md`, authored and **committed BEFORE
the run** at **`d27ba21a`** (§3). Runner `scripts/colour_bound_k1_measure.py`; gate
`tests/test_colour_bound_k1_migrated.py`; pinned raw `results/colour_bound_k1_measure.json`;
seed `seeds/vision_colour_identity.json` **v1.2.0 → v1.3.0** (builder
`tools/build_vision_colour_identity.py`). Seeds **50200–50299** (DISAGREE),
**50300–50399** (FLOOR). Base `main` HEAD **41a3158c**
(`git merge-base --is-ancestor 41a3158c HEAD` verified, §11). Branch
`gamma-substrate/colour-bound-k1-t1`, worktree
`.claude/worktrees/agent-adae671bebdd47a2c`.*

*Completes the rung recorded in `VISION_COLOUR_BOUND_RESULTS.md`, which fixed `ci_assign`'s
missing admission bound for **k ≥ 2** and left the default OFF because the packing radius is
undefined at **k = 1**.*

## Engine / bench / provenance (§10)

- **Engine `7d5f50c18673`** @ `runners/dsl/python/substrate_rs/_native.abi3.so` —
  **shared build, Rust source byte-identical** to canonical (`provenance_line()` reads
  *"shared build from … — Rust source identical"*). This rung adds **NO Rust**, so the
  shared build is legitimate (§10.1 rule 4), gated by `test_this_rung_adds_NO_Rust`
  pinned to the rung's own diff.
- `data/` symlinked to canonical (§10.2). **Baseline measured on this worktree BEFORE any
  file was added: 200 passed / 0 failed.**
- **NO new Rust, NO new seed, NO new RULE.** PART A is a negative, so there was nothing to
  build: the *entire* seed change is **one attribute default**. Every rule's `match`,
  `where` and `effects` is verified BYTE-EQUAL to v1.2.0 against git
  (`test_this_rung_adds_NO_new_RULE_and_changes_no_rule_body`).

## SEED LEDGER CORRECTION (recorded in the prereg, before the run)

The commissioning brief said *"seeds 50100–50999 (50000–50099 consumed)"*. **Off by one
block:** the committed ledger reads *"50000–50199 consumed; 50200–50999 CLEAN"* — the
landed rung's noise floor took 50100–50199. This rung therefore took **50200–50299** and
**50300–50399**; **50400–50999 remain clean**. 50000–50099 was used only as the §3.3
already-burned pilot / cross-check block.

---

# PART A — THE DERIVATION

**VERDICT: NO k=1 BOUND EXISTS — and, more strongly, NONE CAN. The vacuity at k=1 is not
a missing derivation; it is the landed derivation's OWN LIMIT.**

This is a **first-class negative (§7)**, predicted in advance, and it is a *derived* one
rather than a failure to find something.

### The derivation — MONOTONICITY

The packing radius is `r_i(S) = ½·min_{j≠i}‖c_i−c_j‖` over a codebook `S`. Because **a
minimum over a superset cannot increase**, for `S ⊆ S′`:

  **`r_i(S′) ≤ r_i(S)`** — the admission radius is **NON-INCREASING under codebook
  growth.**

This is the right property for a dequantizer: more quanta ⇒ a finer partition ⇒ tighter
cells. It is measured, not asserted — along the growth chain
`{(0,0)} ⊂ {(0,0),(100,0)} ⊂ {(0,0),(100,0),(20,0)}` the radius of `(0,0)` runs
**undefined → 50.0 → 10.0**.

The k=1 radius must therefore **upper-bound every radius reachable by growth** from
`{c₁}`. That supremum is **UNBOUNDED**: place `c₂` at distance `D` and the radius is
`D/2`, for arbitrary `D`. Hence

  **`r(k=1) = +∞` — admit everything.**

**Any FINITE k=1 candidate `r₀` is refuted by exhibition**, and the gate does the
exhibiting: place a second prototype at `4·r₀+1` and the packing radius becomes
`2·r₀+0.5 > r₀`. Measured for all four rival values:

| candidate `r₀` | extension placed at | resulting radius | exceeds `r₀`? |
|---|---|---|---|
| 0.0 | 1.0 | 0.5 | **yes** |
| 0.7071 (`√2/2`) | 3.8284 | 1.9142 | **yes** |
| 1.0 | 5.0 | 2.5 | **yes** |
| 138.24 | 553.96 | 276.98 | **yes** |

**And the GRAPH shows the shrink, not merely the algebra** (§1 clause 5 / §13.2): the
**same** far probe is **admitted at k=1** and **refused at k=3** by the seed's own rules.

### The structural root — the mint has ZERO INTRINSIC EXTENT

`ci_mint_category` clusters by **EXACT value**, so every member of a quantum sits at
distance 0 from it. **Measured: cluster extent = 0.0 on all five landed scenes.**

⇒ **Every length scale in this seed lives BETWEEN prototypes. At k=1 there is no
"between", and the seed contains no other length scale.** That is *why* no k=1 bound
falls out, and it names the precise unblocking change: **a mint with INTRINSIC EXTENT —
colour identity's own already-NAMED FRONTIER, perceptual NEARNESS in minting.** Recorded
in the seed description so it cannot be lost.

### The five rivals — THREE REJECTED BY MEASUREMENT

| # | rival | measurement | verdict |
|---|---|---|---|
| **R1** | the mint's **cluster extent** | **≡ 0.0** on all 5 landed scenes (ENTAILED by exact-value minting — declared unrisked in advance, §13.1). Gives `r(1)=0`, maximally violating monotonicity; the previous rung injected it and measured it REGRESS at k≥2 | **REJECT** |
| **R1′** | the **`√2/2` observational-resolution floor** (covering radius of ℤ²) | **100/100 observed opponent coordinates are INTEGERS**, so no probe can lie in `(0, √2/2)` — it is **observationally indistinguishable from R1**, not an independent candidate. Also an absolute constant: a view from nowhere (§13 corollary) | **REJECT — not independent** |
| **R2** | the **lattice step 1.0** | inherited measurement (previous rung's injected control 4 turned arm C red); absolute constant; violates monotonicity | **REJECT** |
| **R3** | the **scene's measured dynamic range** (T3's anchor idiom, *"the frame's own measured ceiling"*) — **the strongest rival**: finite, non-zero, defined at k=1, and it *does* refuse the defect probe | **TWO measured rejections.** (a) It is **0.0 in BOTH landed k=1 scenes** (`n_distinct_obs = 1`) — it degenerates to R1 exactly where the hole is. (b) **NON-LOCALITY:** same codebook `{(0,0)}`, same observation `(30,0)` — **refused** (bound 15.0) in a bare scene, **ADMITTED** (bound 200.0) once an **unrelated patch at (400,0)** is added elsewhere in the field. **The verdict of a probe flips because of a patch it has nothing to do with** | **REJECT — measured** |
| **R4** | **observed-separation**: ½·min over distinct OBSERVED colour values (minted or not), excluding the observation's own | **0 disagreements** with the packing predicate across 100 already-burned probes — the **ONLY rival CONSISTENT with the landed bound** — and **UNDEFINED at k=1 in all three cases tested**, including the defect scene, where the only competitor **is the winner itself** | **REJECT — consistent but undefined** |
| **R5** | **hypothetical self-mint** (packing radius computed with a quantum hypothetically minted AT the observation) | the competitor sits at exactly `d`, so `2d ≤ d ⟺ d ≤ 0`: collapses to R1 | **REJECT** |

**THE CRUX, pre-registered verbatim and confirmed:** *the rivals that are **DEFINED** at
k=1 are **INCONSISTENT** with the landed k≥2 bound; the one rival that is **CONSISTENT**
is **UNDEFINED** at k=1.*

---

# PART B — THE FLIP

**VERDICT: FLIPPED. `ColourIdentityParams.bound` 0.0 → 1.0, seed v1.3.0.**

All three pre-registered conditions (prereg §5) were met:

1. **PART A returned a POSITIVE, MEASURED argument** that no finite k=1 bound is
   consistent with the landed bound (monotonicity + four exhibited refutations + three
   measured rival rejections) — not a bare *"I looked and didn't find one"*, which the
   prereg declared insufficient to license the flip.
2. **DELTA-ON-FLIPPED is EMPTY** — **zero changed fields across all five landed scenes.**
3. **The k=1 regime is BYTE-IDENTICAL ON vs OFF** — scene stats and the far probe are
   equal field-for-field.

⇒ **The flip is a STRICT improvement: refusal gained at k ≥ 2, nothing lost at k = 1.**

## THE CAVEAT — stated, not implied away

**The guarantee is `k ≥ 2` ONLY.** A single-quantum codebook still admits any colour at
any distance. This is not a residual bug awaiting a patch — PART A shows it is the
correct limit of the bound's own derivation (a lone quantum owns all of space). It is
recorded in **three** places and **asserted** in one: the seed's own `description`, this
results file, the ledger, and
`test_PART_A_IS_A_NEGATIVE_and_names_its_own_unblocking_change` /
`test_the_flag_now_ships_ARMED_with_its_caveat_recorded`, which fail if the seed stops
saying so.

## §9 — the byte-identity claim SHIFTS, and here is the full enumeration

The flip deliberately changes the default, so the claim moves from *"unchanged"* to
**"changed, measured, and ENUMERATED"**. Exactly these moved:

| # | file | change | outcome |
|---|---|---|---|
| 1 | `seeds/vision_colour_identity.json` + builder | `bound` **0.0 → 1.0**; version **1.2.0 → 1.3.0**; description records the null + caveat | **the flip.** Seed diff is exactly **3 lines**; no rule body moved (verified vs git) |
| 2 | `tests/…colour_bound_migrated.py::test_the_flag_ships_OFF_in_the_seed` | retargeted → `test_the_flag_now_ships_ARMED_with_its_caveat_recorded` | asserts the new default **and** the caveat text |
| 3 | same file, `test_X_offday_*` | title/docstring corrected ("OFF by default" → "at ZERO") | **behaviour unchanged** — the arm writes `bound=0.0` explicitly |
| 4 | same file, `test_this_rung_touches_no_other_rungs_files` | `owned` set gains this rung's artifacts | its diff is vs the same base, so it now spans both rungs |
| 5 | `scripts/uniqueness_measure.py::audit_colour_identity` | pins `bound=0.0` explicitly | the declared carve-out — see below |
| 6 | `VISION_PROTOCOL.md` | ledger + ladder append | §10 provenance |

**`test_this_rung_adds_NO_Rust` and `test_this_rung_edits_exactly_ONE_committed_seed`
stayed GREEN UNCHANGED**, as predicted.

**MEASURED, not assumed — every landed results artifact re-runs IDENTICAL** (modulo
`elapsed_s`) with the default ARMED: `colour_identity_measure.json`,
`achromatopsia_measure.json`, `colour_bound_measure.json`, **and
`uniqueness_measure.json`**.

---

# PART C — WHAT I PREDICTED, AND WHAT I GOT WRONG (§3 item 7 / §7)

I predicted **PART A null, the flip proceeding, and every arm passing** — all confirmed,
with provisos 1, 2 and 4 holding exactly.

**PROVISO 3 HELD, and that is itself the finding.** The previous rung's `Times`-trap
prediction BROKE because it changed the composition after pre-registering. I pre-declared
that **this rung changes NO composition**, so the trap's signature should be inherited
unchanged and redden the previous gate's **B, D and E**. Measured: it reddened
**exactly B, D and E** (plus this rung's DISAGREE and MONO). *The earlier prediction
failed for the reason that rung diagnosed, and holding the composition fixed made it
hold.*

**WHAT I GOT WRONG — I predicted L1b's gate would go RED. It did not, and the reason is
worse than the prediction.**

The prereg predicted (§5, §7) that flipping would break `test_uniqueness_migrated.py`,
because L1b's audit pins the far probe assigned at 269.5199. **L1b's audit VALUES did
change** — both probes went to `refused: 1`, `sign_dist: −1.0` — **but its gate stayed
green (21/21)**, because the assertion is *structural*:

```python
assert '"type": "Lte"' not in blob, "if a bound was added, re-run the audit"
```

**A bound WAS added — and it was composed with `Lt` inside `Not(Exists(…))`, not `Lte`.
So L1b's own "if a bound was added, re-run the audit" tripwire is BLIND to the very fix
that answered it.** The landed rung's declared composition deviation (`Not(Exists)` in
place of `Lte`/`MinOver`) is exactly what slipped past it.

Handled as pre-registered: `audit_colour_identity` now pins `bound=0.0` **explicitly**, so
its claim becomes *"with NO admission bound in force, `ci_assign` does this"* — what its
own text always said it was auditing — and its committed numbers reproduce exactly. **I
did NOT repair L1b's assertion** (another rung's file, outside this charter); it is
**NAMED as a residual for the supervisor** below and in the ledger.

---

# PART D — THE ARMS

| arm | statistic | result | vs prereg |
|---|---|---|---|
| **A — k=1 DEFECT REPRODUCED** *(RISKED)* | far probe vs a single-quantum codebook, bound **ARMED** | **admitted**, `ci_refused = 0`, dist **276.4797**, packing radius **undefined** | reproduces ✓ |
| **MONO — the derivation** *(RISKED)* | radius along a growth chain; refutation of every finite candidate; the graph's own shrink | radii **undefined → 50.0 → 10.0** (non-increasing); **4/4 finite candidates exceeded**; graph **admits at k=1, refuses at k=3** | ✓ |
| **NONLOCAL — R3 rejected** *(RISKED)* | R3 on the landed k=1 scenes; the non-locality probe | **0.0** in both k=1 scenes; verdict **FLIPS** refused→admitted (bound 15.0 → 200.0) on an unrelated patch | ✓ |
| **UNDEF — R4 rejected** *(RISKED)* | agreement at k≥2; definedness at k=1 | **0 disagreements / 100**; **undefined in 3/3** k=1 cases; **100/100** integer coords | ✓ |
| **EXTENT — R1** *(ENTAILED, not banked)* | cluster extent, 5 landed scenes | **0.0** | ✓ |
| **NOREG — THE CONJUNCTION** *(RISKED)* | on the **flipped default**: k=3 field, the dist-4 probe, recognize-not-re-mint, **the k=1 field** | **36/36** assigned at dist 0; dist-4 probe **still assigned** to (10,0); `n_cats` 3→3; **k=1 field 36/36 assigned, 0 refused** | ✓ |
| **DISAGREE** *(RISKED, n=100, 50200–50299)* | graph vs re-derived predicate, at k≥2 AND k=1 | **0 disagreements** in both; k=3 **8 admitted / 92 refused** (non-degenerate both ways); k=1 **100 admitted / 0 refused** | ✓ |
| **FLOOR** *(RISKED, n=100, 50300–50399)* | noise minting / signing | **0/100** mint, **0/100** sign | ✓ |
| **DELTA-ON-FLIPPED** *(RISKED)* | changed fields across 5 landed scenes; k=1 ON vs OFF | **0 changed fields**; k=1 **byte-identical** | ✓ |

## THE k=1 DEAD ZONE IS REPORTED, NOT HIDDEN

**DISAGREE at k=1 is 100 admitted / 0 refused** — a degenerate split. It is recorded as
the **finding**, not smuggled through as a passing floor: the bound reaches k ≥ 2 only,
and the arm that says so is pinned
(`test_DISAGREE_the_k1_DEAD_ZONE_is_reported_not_hidden`).

---

# THE POSITIVE CONTROLS (§12.3 / process rules 4, 5, 6) — measured, not asserted

Four defects injected into the **real** builder; each regenerates the seed, runs both
gates, then reverts. **After revert the seed is verified BYTE-EQUAL by sha256 and both
gates are 45/45.**

| injected defect | RED | what it proves |
|---|---|---|
| **`Times` a/b trap** (empty product = 1) | **8** — incl. the previous gate's **B, D, E** and this rung's **DISAGREE**, **MONO-graph** | process rule 4, and **proviso 3 held**: unchanged composition ⇒ the inherited signature, exactly as predicted |
| **REFUSE EVERYTHING** | **17** — incl. **all three NOREG tests**, **DISAGREE**, **DELTA**, and the previous gate's both C tests | **process rule 5, the crux.** `test_FLOOR_noise` and the previous gate's B, D, F stay **GREEN** — a build that refuses everything scores a **perfect floor**. **Floors are not a gate; the CONJUNCTION is.** |
| **VACUOUS bound** (the pre-fix behaviour) | **8** — DISAGREE, MONO-graph, previous B/D/E | the mirror image: **NOREG stays GREEN**, confirming NOREG and DISAGREE test opposite failure directions |
| **k=1 EXACT-MATCH-ONLY** *(new, k=1-specific)* | **9** — **A**, **DISAGREE (both)**, **DELTA (both)**, **MONO** | **THE control that makes the negative worth believing: it installs a finite k=1 bound (the R1 candidate) and the k=1 arms SEE it.** A negative whose instruments could not detect the positive would be worthless. |

**A finding from control 4, worth stating plainly: `NOREG` is BLIND at k=1.** Every landed
k=1 observation sits at distance **0**, so *any* bound ≥ 0 passes it. The arms that carry
the k=1 claim are **A** and **DISAGREE-k1**. This is the k=1 analogue of the previous
rung's "floors are not a gate" lesson, and it is why both were pre-registered.

## §13.1 — ENTAILED vs RISKED, declared BEFORE the run

**ENTAILED, reported and NOT banked:** **EXTENT** (exact-value minting forces extent 0).
**RISKED:** A, MONO, NONLOCAL, UNDEF, NOREG, DISAGREE, FLOOR, DELTA-ON-FLIPPED — each with
its failing input named in advance and **confirmed in range by an injected defect**, never
asserted.

## §9 — gates and bench

- **Rung-7 named vision bench: 200 passed / 0 failed** with `data/` — identical to the
  baseline measured on this worktree **before any file was added**.
- **Siblings green in one process: 83 passed** — colour-identity 6/6, colour-salience 6/6,
  achromatopsia 5/5, **L1b uniqueness 21/21**, colour-bound 20/20 (as amended), and the
  new gate **25/25**.
- **The sd orbit law `{2:1,3:2,4:2,6:2,12:4}` is UNMOVED.**
- **Every landed results artifact re-runs IDENTICAL** (modulo `elapsed_s`), including
  `uniqueness_measure.json`.

---

# BOUNDS (§8) — what this rung does NOT do

- **THE k=1 REGIME IS STILL NOT REFUSABLE.** That is now a *derived* fact rather than an
  open gap, but it is the same fact: **the armed bound guarantees refusal for k ≥ 2 ONLY.**
  Do **not** describe `ci_assign` as "able to refuse" without that qualifier.
- **It builds NOTHING.** No Rust, no seed, no rule, no Term — PART A is a negative and the
  only change is one default. Nothing here widens any invariance class.
- **The unblocking change is NAMED, NOT BUILT:** a mint with intrinsic extent (perceptual
  NEARNESS in minting). Whether a k=1 bound falls out of *that* mint is untested — the
  claim here is only that it cannot fall out of *this* one.
- **NOT a margin gate.** L1c remains NAMED, NOT BUILT.
- **DELTA-ON-FLIPPED covers the five landed scenes and the enumerated blast radius**, not
  the space of all stimuli. Any downstream consumer assuming a sign always exists will now
  meet `sign_dist = −1.0` at k ≥ 2; none exists today, but `ci_assign` is a published
  surface and the default is now armed.
- **NAMED RESIDUAL FOR THE SUPERVISOR — L1b's tripwire is blind.**
  `test_AUDIT_colour_identity_has_NO_admission_bound_at_all` asserts `'"type": "Lte"' not
  in blob` with the instruction *"if a bound was added, re-run the audit"*. A bound was
  added, composed with `Lt`; the tripwire does not trip. **Not repaired here** (another
  rung's assertion). The same pattern-matching weakness plausibly affects L1b's other
  structural audits.
- **T1's near-vacuous bound and `df_recognize` remain exactly as L1b left them.**
- Inherited unchanged from colour identity: abstract cone-triple grain, exact-value
  minting, the 2-D opponent subspace, no colour constancy, no bound object.

## Why this is believed

Because the negative is **derived and instrumented**, not merely unfound. Monotonicity is
measured on a growth chain and **shown in the graph's own decisions**, not just in my
algebra; every finite candidate is refuted **by exhibition**; the strongest rival is
killed by a **non-locality measurement** rather than an argument; and the one rival that
survives consistency is measured **undefined** at exactly the point of interest. The
instruments are proven able to see the opposite result — **control 4 installs a finite k=1
bound and the k=1 arms go red** — and proven not to be floors: a refuse-everything build
leaves `FLOOR` green and is caught only by the conjunction. The flip is gated on a
**measured empty delta** and on the k=1 regime being **byte-identical**, so it is a strict
improvement with an explicit, asserted caveat rather than an implied total guarantee. The
one prediction that broke — L1b going red — is reported with its cause, and the cause
(**a tripwire blind to the fix that answered it**) is more useful than the prediction
would have been.
