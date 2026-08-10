# THE SPECKLE FALSE-MINT — a discriminator that FALLS OUT. RESULTS

Pre-registration `VISION_FIGADJ_WELLPOSED_PREREG.md`, committed **a62ee54c**
before any confirmatory number. Implementation + gates committed **7e2c8025**,
also before the confirmatory run. Seeds **89000–89999**.

Engine **68860d0b0f78**, built by `scripts/engine_build.sh` in this worktree.
Provenance gate run as its own step **before** any number: **7 passed**.

Oracle `scripts/rung7_vision_bench.sh`: **212 passed, 10 skipped, exit 0** —
this tree has no `data/`, the documented no-corpus case (222 is the *collected*
count; the 10 skips are `BSDS300 corpus absent`). Reported with its condition.

Configuration **G72** (one 72×72 decode, 4×4 grid of 18×18 tiles), corpora
pinned and asserted at run time: **C1** cartoon `08630d4b…`, **C2** live-action
`119eca43…`.

---

## THE HEADLINE, IN THREE LINES

**A discriminator does fall out, and it is not about size.** The Zhou
cancellation of the shared border `|B|` is a **two-party** statement; where one
contour cell faces two different enclosed components it does not cancel, so
there is **no well-posed competition to win** and the rule holds it open —
exactly as it already holds a **tie** open.

**The registered negative control PASSES: 0/100** iid speckle fields mint under
the well-posed predicate, against **22/100** for the committed replacement on
the identical fields. **The synthetic gate stays 9/9**, and a genuine
**single-cell figure still mints** in all three arms — the false positive is
removed without buying a false negative.

**It costs real-frame yield, and the cost is stated, not buried:** multi-cell
protos/frame fall **10.0 → 7.1** (C1) and **17.1 → 14.4** (C2) against the
replacement — but stay **2.2×** and **1.3×** the **incumbent measured at the
same grain**.

---

## 0 — WHAT THE DERIVATION IS, AND WHY IT IS NOT A THRESHOLD

`bo_mint_owned` imports its assignment rule from Zhou/Friedman/von der Heydt
2000, and the whole content of that import is the **cancellation of `|B|`**:

> a shared border is ASSIGNED, not disqualifying; it goes to the side whose own
> perimeter it accounts for more of, and **since the shared length `|B|` is
> common to both sides**, `|B|/perim(R) > |B|/perim(Q) ⟺ perim(R) < perim(Q)`.

That is a **two-party** statement. It presupposes the border under assignment is
*one* length shared by *two* sides, so that it drops out of both fractions.

**It fails exactly when a single contour cell of `R` faces two different
enclosed components.** That one cell is the whole of `R`'s shared border with
*each* of them, so the same length is claimed in full by two competitions at
once and the claimed fractions sum to more than one. `|B|` is not a quantity
that cancels there — it is two different quantities wearing one name, and
`perim(R) < perim(Q)` has stopped standing for `|B|/perim(R) > |B|/perim(Q)`.

**So the rule declines.** `bo_mint_owned` already refuses on a tie
(`Not(Lt(R.rim, n.rim))`) and `bo_mint_gestalt` already holds a size tie open.
**An ill-posed competition is held open on the same grounds a drawn one is.**
This is the ownership predicate's own tie structure, extended from *the
competition is drawn* to *the competition does not exist*.

**Why it happens to kill the single-cell false mints — and why that is a
consequence, not the design.** The pilot (§1) establishes two facts that
together explain the whole failure mode: `rim = 1` is the **global minimum** of
the perimeter statistic, so **a singleton wins every competition it enters,
unconditionally**; and a singleton's one cell is **maximally shared** — it is
the entirety of its border with every rival at once. The same degeneracy, from
two sides. The conjunct addresses the second, and the first stops mattering.

**It is not a size test**, and this is checked rather than asserted (§4): it
never mentions size, contains **no `Count` node at all**, and refuses a large
component whose contour cell is wedged between two rivals just as readily —
which is precisely why it costs real-frame yield (§3).

---

## 1 — THE PILOT, ON ALREADY-BURNED SEEDS (§3.3), DISCLOSED IN FULL

Run on RNG **83900** — the original control's own burned seeds, never this
rung's block. It **reproduces the published failure exactly: 26/100, 31 false
protos, all of size 1.**

| quantity | speckle false protos (n=31) | D1 12×12 figure | genuine 1-cell figure | two abutting figures |
|---|---|---|---|---|
| size | all **1** | 24 | **1** | 18 |
| `rim` | all **1** | 16 | 1 | 14 |
| distinct surrounding components | 2–4 | 1 | 1 | 2 |
| distinct surrounding **enclosed** components | **2, 3 or 4 — never ≤1** | 0 | **0** | **1** |

The last row is the discriminator, and it is the one the brief demanded: **a
noise single cell faces two or more enclosed rivals; a genuine single-cell
figure faces none.** The case the replacement exists for — two abutting figures
— faces exactly one, and survives.

---

## 2 — M-E, M-A, AND THE CONTROLS

### M-E — the vacuity gate, run FIRST (§1 fifth clause / FM-0)

**`D = max|wp=1 − wp=0| = 2`, LIVE** (20 fields, seed 89800). A conjunct that
moved nothing would be decorative and its statistics meaningless; the run was
written to abort at `D == 0` and did not have to.

### §9 — the committed results reproduce byte-identically

Checked before anything else was believed. On the burned 83900 fields the
replacement arm returns **26/100**, the published figure to the field. On real
frames (§3) the incumbent and replacement rows reproduce the predecessor's
published means **exactly** — 7.7/3.3, 49.0/10.0, 24.6/10.7, 69.6/17.1. The new
flag defaults to 0.0 and the `Or` short-circuits.

### M-A — the registered negative control, on FRESH seeds (89900)

All three arms on the **same** 100 iid fields, 18×18, k=16.

| arm | fields minting | max false proto size | registered control |
|---|---|---|---|
| incumbent | **0/100** | 0 | passes (as it always did) |
| replacement (committed v1.1.0) | **22/100** | 1 | **FAILS** — the inherited failure, on a fresh draw |
| **well-posed (this rung)** | **0/100** | 0 | **PASSES** |

The replacement's 22/100 against the pilot's 26/100 is a different draw of the
same rate; the prereg predicted "the same neighbourhood" and did not condition
the decision rule on it.

### The constraint that made this non-trivial — checked directly

A minimum-size threshold would have passed M-A and destroyed this row. It is
therefore measured as its own control, not inferred:

| arm | genuine single-cell figure on blank |
|---|---|
| incumbent | **mints** (1 proto, 1 member) |
| replacement | **mints** |
| **well-posed** | **mints** |

**A single cell that is noise is refused; a single cell that is a figure is
minted.** That is the discrimination the brief said the fix had to achieve, and
it is achieved without the predicate ever reading a size.

### Dead-instrument controls — they ACTUALLY FIRE

| control | incumbent | replacement | well-posed |
|---|---|---|---|
| **D1** committed 12×12 figure | reproduces | reproduces | reproduces |
| **D2b** uniform field, frame stripped (the vacuous-mint trap) | **fired** | **fired** | **fired** |

The run aborts if D1 fails to reproduce or D2b fails to fire. Neither happened.

---

## 3 — M-C: THE REAL-FRAME COST, MEASURED AT THE SAME GRAIN

**The baseline is the incumbent at G72, never the retired whole-frame zero.**
Comparing to the whole-frame figure produced a phantom 3× in one predecessor and
a phantom "few and large" reading in the next; all three arms were re-measured
here and nothing was inherited.

Mean per frame over 7 sampled frames × 16 tiles, k=16.

| corpus | arm | components | protos | **MULTI-cell** | held open as ill-posed |
|---|---|---|---|---|---|
| C1 | incumbent | 721.0 | 7.7 | **3.3** | — |
| C1 | replacement | 721.0 | 49.0 | **10.0** | — |
| C1 | **well-posed** | 721.0 | **21.7** | **7.1** | ~21–34 / frame |
| C2 | incumbent | 568.3 | 24.6 | **10.7** | — |
| C2 | replacement | 568.3 | 69.6 | **17.1** | — |
| C2 | **well-posed** | 568.3 | **42.7** | **14.4** | ~10–54 / frame |

**Read honestly, in both directions.**

- **Against the replacement, this is a real cost**: multi-cell protos fall
  **−29%** (C1) and **−16%** (C2), and total protos roughly halve. The conjunct
  bites hard on photographs, which is exactly what §5 of the prereg predicted —
  a scene is a partition and three-way junctions where one cell abuts two rivals
  are common in it. Every one of those is now held open, **including genuine
  ones**. That is the price of the derivation being about well-posedness rather
  than about noise.
- **Against the incumbent at the same grain, it is still a large gain**: **2.2×**
  the multi-cell protos on C1 and **1.3×** on C2. The well-posed arm sits between
  the two, which is what a strict tightening of a strict weakening should do.
- **The prereg predicted the direction but not the landing point**, and said so:
  *"the well-posed arm falls BELOW the replacement and I do not predict which
  side of the incumbent it lands on. If it falls below the incumbent, the
  discriminator is a bad trade and I will report it as one."* It landed above,
  on both corpora. Had it landed below I would be reporting the opposite.

**`n_components` is identical across all three arms on every row** (721.0 /
568.3) — the flood was not touched, as §7 of the prereg required.

**The read-out reconciles under all three predicates**: `G_pass == n_protos` on
**every** M-C row, including the well-posed ones. A read-out calibrated to one
predicate cannot score another, so the well-posedness gate was replicated
explicitly in the read-out and reconciled separately per arm.

---

## 4 — M-D: NO LITERAL ENTERED (§13)

`tests/test_figadj_wellposed_ast_migrated.py` (**8**) +
`tests/test_figadj_replacement_ast_migrated.py` (**7**) = **15 passed**. A
**term-tree AST walk**, never a substring selector. The conjunct is located
**structurally** — the unique top-level `Or` whose first item reads the
`bown_wp` flag — never by name or text.

- the conjunct is a **negated existential** (`Not(Exists member: Exists rival:
  Exists other rival)`) — it REFUSES, it does not assert;
- **it contains ZERO `Count` nodes.** This is the load-bearing assertion. The
  refused fix for this control was a minimum-**size** threshold, and no size
  test can be written without bounding a count. Zero counts ⇒ **provably not a
  size threshold in disguise**;
- every `Lit` inside it is `0.5` against a 0/1 flag (`bg`, `bown_wp`); asserted
  **both ways round**, so a hole in one cannot satisfy the other;
- every `glabel` comparison in it is `Attr` vs `Attr` with **no literal on
  either side**;
- the literal **inventory is unchanged in KIND** — no third kind was added;
- the **incumbent predicate never reads `bown_wp`** (§9), and the new test
  asserts the flag's 0.0 default explicitly;
- the conjunct is **confined to enclosed rivals**; the ground side keeps its own
  pre-existing closure test, so this rung is not silently re-tightening the
  incumbent's ground criterion (§8).

---

## 5 — M-B: THE SYNTHETIC GATE STAYS 9/9

**27 passed** — nine arms under the incumbent
(`tests/test_border_ownership_migrated.py`), the same nine with `bown_own` armed
(`tests/test_border_ownership_owned_migrated.py`), and the same nine again with
`bown_wp` armed (`tests/test_border_ownership_wellposed_migrated.py`, new).

This is the constraint tested **substantively**, not satisfied by the flag's
0.0 default. The Zhou contextual-flip headline, the figure-ground mint, the
recurrence fixpoint, the gestalt size-tracking, the open-contour floor, the
ambiguous-split hold-open, and the 100-field iid noise floor (seeds
**36000–36099**, the incumbent arm's own range, reused so all three predicates
see byte-identical fields) all return identical verdicts.

**The 100-field synthetic noise floor stays 0/100 under the well-posed
predicate too** — so the conjunct is not merely relocating the failure to a
different speckle regime.

---

## 6 — WHICH REGISTERED OUTCOME OCCURRED

§6 of the prereg registered three. **The answer is outcome 1, with the cost of
outcome 3 attached and quantified.**

1. **A derivable discriminator exists and the control passes** — 0/100, with the
   synthetic gate at 9/9 and a genuine single-cell figure still minting. ✅
3. **It costs.** Real-frame multi-cell yield falls 29% (C1) / 16% (C2) against
   the replacement. **Reported, not traded away.** It remains 2.2× / 1.3× the
   incumbent at the same grain, which is why this is outcome 1 rather than a
   wash — but a reader who values the replacement's raw yield over a clean
   negative control has the numbers to disagree, and the flag to act on it. ✅

Outcome 2 (no derivable discriminator; accept the bound) **did not occur**.

---

## 7 — SEEDS AND ORACLE: MEASURED, NOT ASSERTED

Declared **89000–89999**. Measured with `scripts/seed_audit.py` over all four of
this rung's files:

```
{"declared": [89000, 89999], "ok": true, "outside": []}
```

**2 resolved seeds — 89800 (M-E vacuity) and 89900 (M-A speckle). ZERO unknown
sinks.**

**Disclosed draws outside the block**, neither an allocation:
`tests/test_border_ownership_wellposed_migrated.py` drives `arm_floor_noise`,
which draws **36000–36099** — the incumbent arm's own range, reused deliberately
so all three predicates see byte-identical fields. The §1 pilot draws **83900**,
the *previous* rung's burned noise seeds, reused deliberately so the published
failure could be reproduced before anything was changed.

Oracle: **212 passed, 10 skipped, exit 0** (`var/oracle.log`), the documented
no-`data/` case. Its own `no-python-thresholds` scan reports **"(none — every
knob is graph data)"**, which is independent corroboration of §4 from an
instrument this rung did not write.

---

## 8 — WHAT I GOT WRONG

- **I ran the vacuity gate and the §9 byte-identity check on an engine that was
  not mine, and the provenance line caught it.** Mid-session, a concurrent rung
  rebuilt the shared canonical binary underneath this worktree; the engine hash
  moved `25fa11652e83 → ed399ddae26d` and the line flipped to **WRONG ENGINE**.
  I had run the provenance gate at the start and it passed — **a provenance
  check is not a property of the session, it is a property of the moment**. Every
  number produced before `scripts/engine_build.sh` gave this tree its own engine
  (**68860d0b0f78**) was discarded and re-run. Nothing from before that point
  appears in this document.
- **My first diagnostic imported `engine_preamble` and never called it**, so it
  silently loaded the canonical tree's engine while printing a provenance line
  that said so — and I read past it once. The banner did its job; I did not, for
  one iteration.
- **My first hypothesis was wrong, and the data killed it in one measurement.**
  I first believed the false mints were vacuous passes of the single-ground
  closure test (a component with **zero** adjacent ground surfaces, where
  "not *two* different grounds" is vacuously true). It is a real hole — but it
  accounts for only **16 of 31** false protos; the other 15 have exactly one
  ground surface and are properly closed. Had I stopped at the plausible
  diagnosis I would have shipped a fix that halved the failure and claimed it
  closed it.
- **I launched the run with `nohup … &` followed by `echo`, and the harness
  reported "completed, exit 0" for the `echo`.** The run had barely started. This
  is the same shape as the predecessor's `pgrep` guard — a completion signal that
  is not about the thing it appears to be about. I switched to waiting on the
  results file with a stall deadline on log mtime.
- **The real-frame cost is larger than I expected.** I predicted the well-posed
  arm would fall below the replacement, and it does — but by 29% of multi-cell
  protos on C1, more than I had in mind when writing "below". The prediction was
  right in direction and vague in magnitude, and vagueness is not a hit.

## 9 — RESIDUALS (not fixed here)

- **The conjunct holds open genuine three-way junctions.** A component whose
  contour cell abuts two real objects is refused for the same reason a noise cell
  is, and photographs are full of them. This is the honest cost in §3 and it is
  **not** a defect of the derivation — it is the derivation's scope. Assigning a
  border at a genuine three-way junction needs a competition the current
  mechanism cannot express (three parties, not two), and that is a mechanism gap,
  not a constant to be tuned.
- **The tiling still injects a "window edge is ground" prior per tile**,
  inherited and unmodified. A whole-frame 72×72 decode with true image-border
  framing remains the clean comparison and was not run.
- **`k` remains a hand-set adapter magic number** (§13), inherited and unfixed.
- **Persistence (ARM 2 of the predecessor) was not re-measured** for the
  well-posed arm. This rung claims nothing about whether its protos correspond to
  scene structure better or worse than the replacement's — only that there are
  fewer of them and that they exclude the speckle tax. **A yield number is not a
  correspondence number**, and the predecessor's ARM 2 would have to be re-run
  in full, with its tiling-shift control, to say anything there.
- **`bo_mint_gestalt` was not modified**, and remains reachable at tile grain
  with k=2 per the predecessor's finding. All rows here are k=16, where it does
  not fire and every row reconciles.
- **No CI is claimed on any per-frame mean.** M-C is 7 sampled frames per corpus,
  inherited from the incumbent's sampling; the load-bearing quantities are the
  0/100 control and the 9/9 gate, both counted.
