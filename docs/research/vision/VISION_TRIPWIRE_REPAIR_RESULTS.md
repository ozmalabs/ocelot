# TRIPWIRE REPAIR — L1b's STRUCTURAL AUDITS BECOME AST-BASED (RESULTS)

*Confirmatory run of `VISION_TRIPWIRE_REPAIR_PREREG.md`, authored and **committed BEFORE
the run** at **`7c920c42`** (§3). Detector `tools/term_ast_audit.py`; runner
`scripts/tripwire_repair_measure.py`; gate `tests/test_tripwire_repair_migrated.py`;
pinned raw `results/tripwire_repair.json`. **NO seeds consumed** — 53000–53999 remain
CLEAN. Base `main` HEAD **b7c3eaeb** (`git merge-base --is-ancestor b7c3eaeb HEAD`
verified, §11). Branch `gamma-substrate/tripwire-repair-l1b-ast`, worktree
`.claude/worktrees/agent-a01b4ee2230f638d2`.*

*Repairs the defect found by the k=1 rung (`VISION_COLOUR_BOUND_K1_RESULTS.md`, PART C):
**L1b's own "if a bound was added, re-run the audit" tripwire is blind to the very fix
that answered L1b's own finding.***

## Engine / bench / provenance (§10)

- **Engine `7d5f50c18673`** @ `runners/dsl/python/substrate_rs/_native.abi3.so` —
  shared build, Rust source byte-identical to canonical. **This rung adds NO Rust**, so
  the shared build is legitimate (§10.1 rule 4).
- `data/` symlinked to canonical (§10.2). **Baseline measured on this worktree BEFORE
  any file was added: 200 passed / 0 failed**; L1b gate **21/21**; colour siblings **72
  passed** in one process.
- **NO Rust, NO seed, NO rule, NO new constant, NO agent code.** This rung changes
  **instruments only**.

## CHARTER — the §11 rule 4 waiver, declared in the prereg before the run

§11 rule 4 forbids editing another rung's tests. **This rung's charter IS to repair
L1b's instruments**, so it edits `tests/test_uniqueness_migrated.py` and
`scripts/uniqueness_measure.py` by commission. **L1b's `VISION_UNIQUENESS_RESULTS.md`
and its committed `results/uniqueness_measure.json` are NOT rewritten** — the one verdict
that moves is reported below as a **CORRECTION**, not edited into L1b's history (§7).

---

# PART A — THE INVENTORY (the deliverable the k=1 rung asked for)

**Question: is the substring-matching weakness ISOLATED or SYSTEMIC?**

**ANSWER: SYSTEMIC — within a sharply bounded class, and the class is exactly
"assertions about the PRESENCE OR ABSENCE OF A TERM TYPE". All five such assertions in
L1b are substring-based and all five are evadable. Every other structural assertion in
L1b is already AST- or value-based and is unaffected.**

| # | site (`file:line` @ `b7c3eaeb`) | intends to detect | EVASION by equivalent composition |
|---|---|---|---|
| **S1** | `tests/test_uniqueness_migrated.py:342` | *"`ci_assign` has no admission bound"* | **CONFIRMED BLIND.** Any bound spelled `Lt`/`Gt`/`Gte`, or nested under `Not`/`Exists`/`And`/`Or`, evades. The landed seed uses `Lt(Sqrt, Times)` inside `Not(Exists(…))` |
| **S2** | `tests/test_uniqueness_migrated.py:351-352` | *"the similarity path has no verdict bound"* | Same class. **The seed contains 19 comparators** (`Lt`×4, `Gt`×15), so the assertion's premise was never what its prose claimed |
| **S3** | `tests/test_uniqueness_migrated.py:208-209` | *"the flag read is absence-tolerant"* | **POSITIONAL blindness.** `MaxOver` present *anywhere* satisfies it; it never checks that the **flag read itself** is the tolerant one |
| **S4** | `scripts/uniqueness_measure.py:328-330` | similarity audit row counts | Same class. Reports **`Lte`=0, `Gte`=0** while 19 comparators are present, and the row's verdict rested on those zeros |
| **S5** | `scripts/uniqueness_measure.py:349-352` | deformation audit row counts | Same class. Correct only by luck — the bound happens to be spelled `Lte`; re-spelling to `Lt` silently zeroes the row |

**The disease had already been diagnosed once INSIDE THIS VERY FILE, and not carried
across.** `test_no_python_decision_in_the_adapter` (`:255-292`) parses Python to an AST
*specifically because a substring scan failed*, and its own comment records the miss:
*"a substring scan is NOT a selector here (§12): `->` in a type annotation contains
`>`"*. The Python half was fixed; the seed-JSON half was not. **Three sound assertions
are unaffected** and are listed in the prereg (`..._NO_new_constant`,
`..._never_writes_an_L1_attribute`, `..._no_python_decision_in_the_adapter`).

---

# PART B — THE DETECTOR

`tools/term_ast_audit.py` parses Term trees (walking `dict`/`list`, reaching `match`,
`where`, `effects` and every nesting) and classifies comparators **by operand shape**.
**Two tiers, both reported**, because each ALONE is a degenerate gate:

- **T0 ANY-COMPARATOR** — every `{Lt,Lte,Gt,Gte}` at any depth/position/polarity. The
  strictly-stronger drop-in for the string test; **has false positives by construction**.
- **T1 BOUND-LIKE** — a T0 node where **neither** operand is `Count`-rooted **and at
  least one** is DERIVED (a computed expression, `ATOMIC = {Lit,Const,Attr,Var}`).

**Both exclusions are L1b's OWN published semantics applied structurally**, not
conveniences: L1b's similarity row itself calls `Count(residual)==0` *"exact equality"*
and **not** a verdict bound; and `Gt(Attr(identity), Lit(0.0))` is a config gate that
cannot refuse a candidate on distance. What survives both is a comparison **against a
computed magnitude** — which is what a bound structurally is. `ATOMIC` is defined by its
small closed complement so an **unrecognised Term counts as DERIVED**: for a tripwire a
false positive costs a re-run, a false negative costs a wrong landed verdict.

---

# PART C — THE ARMS

| arm | statistic | result | vs prereg |
|---|---|---|---|
| **BLIND** *(ENTAILED — declared, NOT banked)* | current string test vs the current colour seed | **PASSES** (fails to trip). `Lte`=0, `Gte`=0 — **doubly blind** — while `Lt`=4, `Gt`=2 are present | reproduces ✓ |
| **SEES** *(RISKED-weak)* | T1 count in `ci_assign` | **1 bound**, `not_depth=1` (**negated**), operands `Sqrt` vs `Times`, at `where.items[5].items[1].arg.predicate.items[1]` | ≥1 ✓ |
| **EVADE** *(the RISKED arm)* | 7 equivalent bound compositions | **AST 7/7. Old string test 1/7 — it catches ONLY `E1_plain_Lte` and MISSES 6** | 7/7 and ≥1 missed ✓ |
| **FP** *(the CONJUNCTION)* | synthetic non-bounds + a real unbounded seed | **0/3 synthetic false positives**; `shape_decode_loop` **T0=19, T1=0** | 0 and 0 ✓ |
| **TABLE** *(RISKED)* | L1b's audit table re-run | **exactly ONE verdict changes** — colour identity | as predicted ✓ |
| **X — OFF-DAY (§9)** | bench, L1b gate, orbit law | 200/0, 21/21, law unmoved | ✓ |

## THE EVASION BATTERY — every row

Seven spellings of **one** predicate ("the distance lies within the packing radius").

| case | composition | AST | **old string test** |
|---|---|---|---|
| `E1_plain_Lte` | `Lte(Sqrt, Times)` — the spelling the old test was written for | ✓ | **✓ (the positive control: the old test is not simply broken)** |
| `E2_strict_Lt` | re-spelled `Lt` — **the landed colour composition** | ✓ | **MISS** |
| `E3_Lt_inside_Not_Exists` | **the actual k=1 shape**, `not_depth=1` | ✓ | **MISS** |
| `E4_reversed_Gte` | operands swapped, comparator mirrored | ✓ | **MISS** |
| `E5_reversed_Gt` | swapped and strict | ✓ | **MISS** |
| `E6_double_negation` | two `Not`s inside an `And`, `not_depth=2` | ✓ | **MISS** |
| `E7_in_a_where_clause` | relocated into a `where` clause | ✓ | **MISS** |

## THE AUDIT TABLE RE-RUN — **ONE VERDICT CHANGES**

| rung | L1b recorded | old test | T0 | T1 | **verdict** |
|---|---|---|---|---|---|
| **colour identity** `ci_assign` | *"NONE — zero `Lte` nodes"* | says "no bound" | 6 | **1** (negated) | **CHANGES — a bound IS present** |
| **similarity** `shape_decode_loop` | *"NONE — zero `Lte`/`Gte` in the whole seed"* | says "no bound" | **19** | **0** | **HOLDS under T1** (would FLIP under T0) |
| **deformation** `df_recognize` | *"3× `Lte`"* | sees it | 3 | 3 | unchanged |
| **T2 category** `cat_recognize` | *"box containment + exact `Eq`"* | sees `Lte` | 9 | 0 | unchanged — **but see the residual below** |
| **L1b's own gate** `vision_uniqueness` | *"`Lte` 1.0"* | sees it | 10 | 6 | unchanged |

### THE ONE CORRECTION, stated precisely

**L1b recorded: *"`ci_assign` contains ZERO `Lte` nodes, so it can NEVER refuse."*
Since the colour-bound rungs landed, that is FALSE.** A bound is present, composed
`Lt(Sqrt, Times)` inside `Not(Exists(…))`.

**This corrects a STRUCTURAL claim, not a measured number.** L1b's audit numbers
reproduce **exactly**, because the k=1 rung had already pinned `bound=0.0` explicitly in
`audit_colour_identity` — so that row measures the **unbounded** behaviour its prose
always claimed. **Nothing in `VISION_UNIQUENESS_RESULTS.md` is rewritten** (§7).

**The similarity row HOLDING is also a result, not a formality.** A naive
any-comparator detector flips it the **wrong** way on 19 comparators. It survives
precisely because `Count`-rooted comparisons are excluded — L1b's own semantics. Prereg
proviso 1 held.

---

# THE POSITIVE CONTROLS (§12.3 / process rules 4, 5, 6) — measured, not asserted

Defects injected into the **real** detector, gates run, then reverted with a sha256
byte-equality check (**verified identical; gates back to 42/42**).

| injected defect | RED | what stayed GREEN | what it proves |
|---|---|---|---|
| **DETECT-NOTHING** (`classify` → `False`) | **12** — `SEES`, all 7 `EVADE` cases, the old-test comparison, both `TABLE` rows, **and L1b's repaired colour assertion** | **the entire `FP` arm, 4/4** | **process rule 5, exactly. A detector that detects NOTHING scores a PERFECT false-positive arm.** The FP arm alone is not a gate |
| **DETECT-EVERYTHING** (`classify` → `True`) | **9** — all 3 `FP` synthetics, the real-seed FP test, the two-tier test, both `TABLE` rows, **and L1b's repaired similarity assertion** | **the entire `EVADE` arm** | the mirror image. **The EVADE arm alone is not a gate either** |
| **`Times` a/b trap** (process rule 4) | **0 — INERT** | everything (42/42) | **reported, not hidden — see below** |

**THE CONJUNCTION IS THE GATE.** `EVADE` and `FP` pull in opposite directions; each is
scored perfectly by a degenerate build that the other catches. This is L1b's own
*"floors are not a gate"* lesson (§1.1), instantiated for a detector.

**The `Times` trap is INERT for this rung, and that is the honest finding.** Process
rule 4 is about **evaluation** semantics — the `a`/`b` form is an empty product = 1 when
a Term is *evaluated*. **This rung never evaluates a Term; it only inspects structure**,
so the trap cannot bite. Note the detector's answer is *correct* rather than lucky:
`Lt(Sqrt(d), Times_empty)` is `Lt(d, 1)`, still structurally a bound, and it is still
detected. **A control that cannot fire is reported as inert rather than counted as a
pass.**

---

# §9 — DEFAULTS PRESERVE COMMITTED RESULTS

- **Vision bench `scripts/rung7_vision_bench.sh`: 200 passed / 0 failed** with `data/` —
  identical to the baseline measured on this worktree **before any file was added**.
- **L1b's gate: 21/21 before the repair and 21/21 after** (0.38s → 0.37s). The
  **assertion count is unchanged**; one assertion's **polarity inverts** to match
  measured reality.
- **Siblings green in one process: 114 passed** — L1b uniqueness 21/21, colour-bound,
  colour-bound-k1, colour-identity, colour-salience, sdloop-vision, engine-provenance,
  and the new gate **21/21**.
- **sd orbit law `{2:1,3:2,4:2,6:2,12:4}` UNMOVED** (6 passed).
- **`results/uniqueness_measure.json` re-ran STRICTLY ADDITIVE** — enumerated by a
  field-by-field diff: **6 keys ADDED** (`AST_T0_any_comparator` /
  `AST_T1_bound_like` / `AST_has_bound` on the similarity and deformation rows),
  **0 pre-existing values changed** (modulo `elapsed_s`). **The committed artifact was
  then RESTORED from git**, as pre-registered — L1b's numbers stand untouched.

---

# BOUNDS (§8) — what this rung does NOT do, including a residual it FOUND

**It repairs INSTRUMENTS. It measures nothing about vision, widens no invariance class,
adds no capability.** Specifically NOT shown:

- **THE DETECTOR READS STRUCTURE, NOT SEMANTICS. It cannot tell a load-bearing bound
  from a VACUOUS one.** `Lt(d, Lit(1e9))` is structurally a bound and admits everything.
  This is exactly the failure L1b itself found for T1 continuous pose (*"the bound is
  near-vacuous; the ranking does the work"*), and **no instrument here would have caught
  it**. Bound-presence is not bound-efficacy (§13.2).
- **NAMED RESIDUAL — T1 HAS ITS OWN FALSE-NEGATIVE CLASS, FOUND BY THIS RUN AND
  REPORTED RATHER THAN PATCHED.** A bound whose **threshold is a STORED ATTRIBUTE**
  rather than a computed expression — `Lt(Attr(dist), Attr(bound))` — is **atomic vs
  atomic**, so T1 classifies it as a flag/epoch read and **MISSES it. Measured: the
  probe returns `False`.** This is not hypothetical: **T2 category's box containment is
  four `Lte(Attr, Attr)` comparisons**, which T1 reports as non-bounds. **T0 catches
  every one of them (T2: T0=9)** — which is precisely why both tiers are reported and
  why the repaired assertions read T0 as well. **The fix is NAMED, NOT BUILT:** a third
  tier separating "stored threshold" from "flag/epoch" needs to know which attributes
  are *params* and which are *measurements* — semantics not available structurally — so
  it needs its own pre-registration. **It is NOT tuned in here**: no arm failed, and
  changing the instrument after seeing the results to make a nicer number is precisely
  what §5 forbids.
- **S3's repair is narrower than S1/S2's.** It checks the `uniqueness` flag read
  specifically; it does not prove absence-tolerance in general.
- **The five repaired sites are L1b's. Other rungs' gates were not audited** for the
  same weakness. The inventory's method transfers; the finding is scoped to L1b.
- **No claim that the seven evasion compositions are exhaustive.** They are the classes
  the k=1 rung named plus operand reversal, double negation and relocation. A
  composition outside all seven could still evade T1.
- **Nothing here revisits** T1's near-vacuous bound, `df_recognize` (still structural,
  still unmeasured), the similarity path's exact-`Argmax`-tie hazard, or **L1c the
  margin instrument — still NAMED, NOT BUILT.**

## Why this is believed

Because the repair is **measured against the instrument it replaces, in both
directions**. The old test is not strawmanned — it is given its own positive control
(`E1`), which it passes, and then misses six equivalent spellings the AST detector
catches. The new detector is not allowed to win by being eager: a **detect-everything**
build passes the entire evasion arm and is caught only by the false-positive arm, and a
**detect-nothing** build scores a **perfect false-positive arm** and is caught only by
the evasion arm — **both were injected and both reddened L1b's own repaired assertions**,
so the conjunction is demonstrated rather than argued. The one verdict that changes is
reported as a correction to a structural claim with its measured numbers explicitly
shown to be unaffected, and L1b's committed artifact is restored rather than rewritten.
The control that could not fire is reported **inert** instead of banked, and the
false-negative class this run discovered in its own detector is stated, measured, and
**left unfixed** rather than quietly tuned away.
