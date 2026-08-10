# TRIPWIRE REPAIR — L1b's STRUCTURAL AUDITS BECOME AST-BASED (PRE-REGISTRATION)

*Written and committed **BEFORE the run** (§3). Base `main` HEAD **b7c3eaeb**
(`git merge-base --is-ancestor b7c3eaeb HEAD` verified, §11). Branch
`gamma-substrate/tripwire-repair-l1b-ast`, worktree
`.claude/worktrees/agent-a01b4ee2230f638d2`. Engine `7d5f50c18673` (shared build,
Rust source byte-identical — this rung adds **NO Rust**, §10.1 rule 4).
`data/` symlinked to canonical (§10.2); **baseline measured on this worktree BEFORE
any file was added: 200 passed / 0 failed** (with `data/`), L1b gate **21/21**,
colour siblings **72 passed** in one process.*

## CHARTER — this rung MAY edit another rung's files (§11 rule 4 waiver)

§11 rule 4 forbids editing another rung's tests. **This rung's entire charter is to
repair L1b's instruments**, so it edits `tests/test_uniqueness_migrated.py` and
`scripts/uniqueness_measure.py` **by commission**. Stated here so the waiver is on the
record before the run, and repeated in the ledger.

**What is NOT permitted, and is not done:** L1b's `VISION_UNIQUENESS_RESULTS.md` and its
committed numbers (`results/uniqueness_measure.json`) are **not rewritten**. If a verdict
changes, it is reported as a **CORRECTION in this rung's own results file**, not edited
into L1b's history (§7).

## SEEDS — NONE CONSUMED

Block **53000–53999** was allocated to this rung. **It is not needed and is not
touched.** Every arm is deterministic static analysis of committed seed JSON plus
synthetic Term trees constructed in the runner; there is no sampling, so there is no
noise floor to draw and no seed to burn. **53000–53999 remain CLEAN.** Recorded rather
than silently skipped, so the ledger does not lose a block.

---

# THE DEFECT (established by the k=1 rung, `VISION_COLOUR_BOUND_K1_RESULTS.md`)

L1b's audit asserts

```python
assert '"type": "Lte"' not in blob, "if a bound was added, re-run the audit"
```

The colour refusal bound was composed as **`Lt` inside `Not(Exists(…))`** — semantically
an admission bound, structurally invisible to a scan for the literal string `"type":
"Lte"`. **L1b's own tripwire is blind to the fix that answered L1b's own finding.**

The k=1 rung declined to repair it (another rung's file) and named the suspicion that
**the same weakness affects L1b's other structural audits**. STEP 1 below confirms or
refutes that by enumeration.

---

# STEP 1 — THE INVENTORY (deliverable in its own right)

Every assertion in L1b's gate and runner that pattern-matches a **serialized** blob,
with what it intends and how an equivalent composition evades it. Cited `file:line`
against base `b7c3eaeb`.

| # | site | intends to detect | EVASION by equivalent composition |
|---|---|---|---|
| **S1** | `tests/test_uniqueness_migrated.py:342` | *"`ci_assign` has no admission bound"* — `'"type": "Lte"' not in blob` | **CONFIRMED BLIND (the k=1 finding).** Any bound spelled `Lt`, `Gt`, `Gte`, or any of them nested under `Not`/`Exists`/`And`/`Or`, evades. The landed seed uses `Lt(Sqrt(dist), Times([0.5, sep]))` inside `Not(Exists(…))` |
| **S2** | `tests/test_uniqueness_migrated.py:351-352` | *"the similarity path has no verdict bound"* — `Lte` and `Gte` both absent from `shape_decode_loop.json` | Same class: a bound spelled `Lt`/`Gt` evades entirely. **This seed does contain `Lt` and `Gt` nodes**, so the assertion's premise is not what its prose claims |
| **S3** | `tests/test_uniqueness_migrated.py:208-209` | *"the flag read is absence-tolerant, not a `PickUnique`"* — `PickUnique` absent **and** `MaxOver` present anywhere in the seed | **POSITIONAL blindness.** `MaxOver` present *anywhere* satisfies it; the assertion never checks that the **flag read itself** is the `MaxOver`. A seed reading its flag some other tolerant-looking way, with an unrelated `MaxOver` elsewhere, passes |
| **S4** | `scripts/uniqueness_measure.py:328-330` | audit row for similarity — reports `Lte_nodes`, `Gte_nodes`, `Argmax_nodes` by `blob.count(...)` | Same class as S2. Reports **0/0** while `Lt`/`Gt` nodes are present, and the row's verdict (`EXPOSED: False`, *"no verdict bound exists"*) rests on those zeros |
| **S5** | `scripts/uniqueness_measure.py:349-352` | audit row for deformation — `Argmin_nodes`, `Lte_nodes`, `Count_nodes`, `Filter_nodes` by `blob.count(...)` | Same class. Detects this seed's bound only because it happens to be spelled `Lte`; a re-spelling to `Lt` silently zeroes the row |

**Systemic or isolated — the answer, by enumeration:** the weakness is **systemic within
a sharply bounded class, and that class is exactly "assertions about the PRESENCE OR
ABSENCE OF A TERM TYPE"**. All five such assertions in L1b are substring-based and all
five are evadable. **Every other structural assertion in L1b is already AST-based or
value-based and is NOT affected**, and one of them says so in its own docstring:

- `test_this_rung_adds_NO_new_constant` (`:234-252`) — already walks the parsed JSON
  collecting `Lit` values. Not evadable by re-spelling.
- `test_the_gate_never_writes_an_L1_attribute` (`:224-231`) — reads rule `effects`
  positionally. Not evadable.
- `test_no_python_decision_in_the_adapter` (`:255-292`) — **already parses Python to an
  AST specifically because a substring scan failed**, and its comment records the miss
  (*"a substring scan is NOT a selector here (§12): `->` in a type annotation contains
  `>`"*). **The disease was already diagnosed once inside this very file, in the Python
  half, and not carried across to the seed-JSON half.**

So the k=1 rung's suspicion is **CONFIRMED, and narrowed**: 5 sites, one failure mode,
one repair.

---

# STEP 2 — THE DETECTOR, SPECIFIED BEFORE IT IS WRITTEN (§3, §5)

New module `tools/term_ast_audit.py`. It **parses** seed Term trees (recursively walking
`dict`/`list`, so it reaches `match`, `where`, `effects`, and every nesting under
`Not`/`Exists`/`And`/`Or`/`Filter`) and classifies each comparator **by the SHAPE OF ITS
OPERANDS**, never by the serialized text.

**COMPARATORS** = `{Lt, Lte, Gt, Gte}`.

**ATOMIC operand roots** = `{Lit, Const, Attr, Var}` — a stored value or a literal.
Anything else is **DERIVED** (a computed expression). The set is defined by its small
closed complement so that an **unrecognised Term counts as DERIVED** — the conservative
direction for a tripwire, where a false positive costs a re-run and a false negative
costs a wrong landed verdict.

Two tiers are reported, **both**, because they answer different questions:

- **T0 — ANY-COMPARATOR.** Every node with `type ∈ COMPARATORS`, at any depth, in any
  position, under any number of `Not`s. This is the strictly-stronger drop-in
  replacement for the string test. Maximally sensitive; **has false positives by
  construction**, and the false-positive arm below measures them rather than hiding them.
- **T1 — BOUND-LIKE.** A T0 node such that **neither** operand is rooted at `Count`
  **and at least one** operand is DERIVED.

**The two exclusions in T1 are declared semantics, not conveniences, and each matches a
verdict L1b already published:**

- **`Count`-rooted ⇒ cardinality, not a bound.** L1b's own row for the similarity path
  states its admission is *"exact equality (`Count(residual)==0`)"* and classifies that as
  **NOT a verdict bound**. Excluding `Count` is L1b's stated semantics applied
  structurally.
- **atomic-vs-atomic ⇒ a flag or epoch read, not a bound.** `Gt(Attr(identity),
  Lit(0.0))` is a config gate; `Lt(Attr(epoch), Attr(codebook_epoch))` is a scheduling
  comparison. Neither can refuse a candidate on how far it sits from the codebook.

A bound, structurally, is a comparison **against a computed magnitude** — which is
exactly what survives both exclusions.

**Reported per comparator:** the enclosing rule, the JSON path, the operand root types,
the tier, and the **`Not`-nesting depth** (polarity), so a negated bound is visible *as*
negated rather than merely counted.

**Scope fix (S3/S1):** the detector scans the **whole seed and attributes per rule**, so
a bound relocated into a sibling rule cannot evade a rule-scoped assertion.

---

# THE ARMS — hypotheses, statistics, and predictions stated in advance (§3 items 1,2,5,7)

| arm | statistic | decision rule | **prediction** | §13.1 |
|---|---|---|---|---|
| **BLIND** — blindness reproduced | run the *current* string test S1 against the *current* `vision_colour_identity.json` | passes ⇒ blindness reproduced | **PASSES** (i.e. the tripwire fails to trip) | **ENTAILED — declared, NOT banked.** I inspected the seed during STEP 1 and measured `ci_assign`: `Lte 0, Lt 4, Gt 2`. It cannot now surprise me and I do not claim it as a risked result |
| **SEES** — the repaired detector sees it | T1 count in `ci_assign` | `≥ 1` | **≥1**, specifically the `Lt(Sqrt, Times)` at `Not`-depth ≥1 | RISKED-but-weak (operand roots inspected at audit time; the classifier is written after) |
| **EVADE** — the evasion battery *(the RISKED arm)* | 7 synthetic rules, each semantically the SAME distance bound. Statistic: T1 detections and old-string-test detections | **T1 catches 7/7 AND the old test misses ≥1** | T1 **7/7**; old test catches **only E1**, misses **E2–E7** | **RISKED** |
| **FP** — no false positives *(the CONJUNCTION)* | T1 count on (a) real `shape_decode_loop.json`, (b) 3 synthetic non-bounds (flag / cardinality / epoch) | (a) **== 0** and (b) **0/3** | (a) **0**, (b) **0/3**; T0 flags all of them, which is the point of reporting both tiers | **RISKED** |
| **TABLE** — L1b audit table re-run | every row's verdict recomputed with the AST detector | report any change | **the colour-identity row's STRUCTURAL claim CHANGES** (a bound now exists); the similarity row **HOLDS under T1** and **would flip under T0**; L1/T1/T2/deformation rows unchanged | **RISKED** |
| **X — OFF-DAY (§9)** | L1b gate after repair; vision bench; sd orbit law | 21/21, 200/0, law unmoved | all hold | ENTAILED |

## EACH RISKED ARM'S FAILING INPUT, NAMED IN ADVANCE (process rule 6)

A gate I have only seen pass is not a gate (§12.3). Before running, the input that makes
each risked arm go RED:

- **EVADE fails** if the classifier's DERIVED test is wrong — e.g. if it treated
  `Times`/`Sqrt` as atomic, E1–E7 would all read as flag comparisons and T1 would return
  **0/7**. **In range:** the classifier has not been written yet, and this is precisely
  the mistake it could make.
- **FP fails** if the classifier flags cardinality or flag comparisons — a
  "flag-everything" detector returns **19/19** on `shape_decode_loop` and **3/3** on the
  synthetic non-bounds. **In range:** T0 *does* exactly this, and is reported alongside,
  so the failure mode is not hypothetical — it is measured on the same run.
- **EVADE and FP are opposed.** A detector cannot pass both by being lax or by being
  eager. **This is the conjunction** (process rule 5): as with L1b's own
  refuse-everything control, a "detect nothing" build scores a **perfect FP arm**, and a
  "detect everything" build scores a **perfect EVADE arm**. **Neither arm alone is a
  gate.**
- **TABLE fails** if a row's recomputed verdict contradicts a *measured* L1b number
  (as opposed to a structural claim). That would mean the detector is wrong, not that
  L1b is.

## POSITIVE CONTROLS, declared in advance (§12.3 / process rules 4, 5)

Two defects injected into the **real** detector, each run against the full gate, then
reverted with a byte-equality check:

1. **`Times` a/b trap** (process rule 4) — the empty-product defect, injected into the
   detector's own synthetic battery construction. Must redden EVADE.
2. **DETECT-NOTHING** (process rule 5) — the T1 classifier returns `False` always.
   **Prediction: the FP arm stays GREEN and only EVADE/SEES/TABLE go RED.** If FP were
   the whole gate, this build would ship.
3. **DETECT-EVERYTHING** — T1 ≡ T0. **Prediction: EVADE stays GREEN, FP goes RED.** The
   mirror image, confirming the two arms test opposite directions.

## §9 — WHAT MOVES, ENUMERATED IN ADVANCE

The repair changes **instruments, not results**. Enumerated:

| file | change | outcome |
|---|---|---|
| `tests/test_uniqueness_migrated.py` | S1/S2/S3 assertions → AST-based | **S1's assertion INVERTS** — it must now assert the bound IS present, because it is. That is the reported correction |
| `scripts/uniqueness_measure.py` | S4/S5 gain **ADDITIVE** AST fields | **every pre-existing key must remain byte-identical**; verified by re-running and diffing against the committed `results/uniqueness_measure.json` on the old keys only |
| `results/uniqueness_measure.json` | **NOT REWRITTEN** | L1b's committed numbers stand |

**Prediction:** L1b's gate stays **21/21** after repair (the assertion count is
unchanged; one assertion's polarity flips to match measured reality), and the vision
bench stays **200/0**.

## WHAT A NULL MEANS (§3 item 5)

If the inventory had found the string tests **unevadable**, or the AST detector had found
**no bound** in `ci_assign`, the k=1 rung's report would be wrong and this rung would
close as a **negative**: *"the tripwire is blind in one place only, and it is not
systemic."* STEP 1 has already decided this against the null — five sites, one failure
mode — and the remaining risk is carried by **EVADE** and **FP**.

## MY PREDICTION, WITH ITS PROVISOS (§3 item 7)

I predict every arm passes as tabled, and specifically that **exactly one L1b verdict
changes**: colour identity's *structural* claim (*"zero `Lte` nodes ⇒ no bound"*) becomes
*"a bound is present, composed `Lt` under `Not(Exists)`"*. **Its MEASURED numbers do not
change**, because the k=1 rung already pinned `bound=0.0` in `audit_colour_identity`, so
the row still measures what its prose always claimed.

**Provisos I expect to hold, flagged so a break is informative:**

1. The similarity row **holds under T1 and flips under T0**. If T1 flips it too, my
   `Count`-exclusion is wrong and the row needs re-deriving, not the detector re-tuning.
2. The deformation row is **unchanged** — its bound is spelled `Lte` and both instruments
   see it.
3. **T0 on `shape_decode_loop` is non-zero** (I measured 19 comparators at audit time),
   which is what makes the FP arm non-vacuous. If T0 were 0 there, the FP arm would be
   passing on an empty set and would prove nothing.
