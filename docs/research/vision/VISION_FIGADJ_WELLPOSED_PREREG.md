# PRE-REGISTRATION — can the single-cell speckle false-mint be excluded by
# something that FALLS OUT?

Written and **committed before any confirmatory number**. Seeds **89000–89999**.
Engine **25fa11652e83** (no Rust change in this rung — the change is seed data).
Protocol §3.

---

## 0 — WHAT IS BEING FIXED, AND WHAT MAY NOT BE DONE TO FIX IT

`VISION_FIGADJ_REPLACEMENT_RESULTS.md` (merged `01099461`) records a **failed
registered negative control**: competitive border ownership (`bo_mint_owned`,
armed by `bown_own`) mints on **26/100** iid speckle fields at 18×18 / k=16,
where the incumbent `bo_mint_enclosed` mints **0/100**. Every false mint is a
**single cell** (`max_false_proto_size = 1`).

That rung **correctly refused** the obvious lever — a minimum-size threshold —
under §13, and recorded the tax as an unmitigated residual.

**This rung may not reinstate it.** Nor may it exclude small components: the
constraint is that **the same predicate keeps the synthetic gate at 9/9**, and a
genuine single-cell figure must still mint. Whatever is used must distinguish
**a single cell that is noise** from **a single cell that is a small figure**,
and must introduce **no literal** beyond the 0/1 flag discriminators already
present.

---

## 1 — PILOT (on ALREADY-BURNED seeds, per §3.3), and what it found

Run on RNG **83000+900** — the *original* control's own already-burned seeds,
never on this rung's block. Disclosed in full so nothing here is laundered as
confirmatory.

The pilot reproduces the published failure **exactly: 26/100, 31 false protos,
all of size 1**. It then profiles them:

| quantity | speckle false protos (n=31) | D1 12×12 figure | genuine 1-cell figure | two abutting figures |
|---|---|---|---|---|
| size | all **1** | 24 | **1** | 18 |
| `rim` | all **1** | 16 | 1 | 14 |
| distinct surrounding components | 2–4 | **1** | **1** | 2 |
| distinct surrounding **enclosed** components | **2, 3 or 4 — never ≤1** | 0 | **0** | **1** |

**Two facts fall out of this table.**

1. `rim = 1` is the **global minimum** of the perimeter statistic, so a singleton
   **wins every competition it enters, unconditionally**. The competition is
   degenerate at size 1. This is *why* the false mints are all single cells —
   not a coincidence to be thresholded away.
2. Every one of the 31 false protos faces **two or more distinct enclosed
   rivals**; the genuine single-cell figure faces **none**, and the case the
   replacement exists for — two abutting figures — faces exactly **one**.

## 2 — THE DERIVATION (what falls out, and from what)

`bo_mint_owned`'s own comment states the derivation it imports from
Zhou/Friedman/von der Heydt 2000:

> a shared border is ASSIGNED, not disqualifying; it goes to the side whose own
> perimeter it accounts for more of, and **since the shared length |B| is common
> to both sides**, |B|/perim(R) > |B|/perim(Q) ⟺ perim(R) < perim(Q).

**The cancellation of |B| is the whole derivation, and it is a TWO-PARTY
statement.** It presupposes that the border under assignment is *one* length,
shared by *two* sides, so that it drops out of both fractions.

**Where that presupposition fails, the comparison `perim(R) < perim(Q)` no
longer stands for anything.** It fails exactly when **a single contour cell of R
faces two different enclosed components at once**: that one cell is the whole of
R's shared border with *each* of them, so the same length is claimed in full by
two competitions simultaneously. The claimed fractions sum to more than one —
`|B|` is not a quantity that cancels, it is two different quantities wearing one
name. There is no well-posed competition there to win.

**So the rule declines — exactly as it already declines a tie.** `bo_mint_owned`
holds a tie open (`Not(Lt(R.rim, n.rim))` refuses on equality) and
`bo_mint_gestalt` holds a size tie open, both on the seed's stated
anti-confabulation posture. **An ill-posed competition is held open on the same
grounds a tied one is.** This is the ownership predicate's own tie structure,
extended to the case where the competition does not exist rather than the case
where it is drawn.

**It is not a size test.** It never mentions size, and it refuses a large
component whose contour cell is wedged between two rivals just as readily. That
it happens to eliminate the singleton false mints is a *consequence* of `rim=1`
being both minimal and maximally shared — the same degeneracy from the other
side.

**It introduces no literal.** It is structurally the twin of the conjunct
already present in all four mint rules — the single-ground closure test
(*"Not Exists two ground-side neighbours with different glabel"*, `G_gnd2`) —
generalised from the ground side to the rival side. Its only literals are the
`0.5` discriminators over the 0/1 `bg` flag, which is the existing kind.

### The conjunct, exactly

Refuse `R` if:

```
Exists f ∈ {Cell : f.glabel == R.glabel ∧ f.bg < 0.5}      (a member of R)
  Exists n1 ∈ Neighbours(f) : n1.bg < 0.5 ∧ n1.glabel ≠ R.glabel
    Exists n2 ∈ Neighbours(f) : n2.bg < 0.5 ∧ n2.glabel ≠ R.glabel
                                            ∧ n2.glabel ≠ n1.glabel
```

Armed by a new `BorderOwnParams.bown_wp`, **default 0.0**, so both the incumbent
and the committed v1.1.0 replacement reproduce **byte-identically** (§9). Written
as `Or(bown_wp < 0.5, <well-posed>)` inside `bo_mint_owned`, so there is one
rule and one mint path.

---

## 3 — ARMS

Three, all through the substrate (§ the prior rung's instrument discipline — a
read-out calibrated to one predicate cannot score another):

| arm | `bown` | `bown_own` | `bown_wp` |
|---|---|---|---|
| **incumbent** | 1 | 0 | 0 |
| **replacement** (committed v1.1.0) | 1 | 1 | 0 |
| **well-posed** (this rung) | 1 | 1 | 1 |

---

## 4 — MEASUREMENTS, STATISTICS, n FIXED IN ADVANCE

**M-A — the speckle control, re-run.** 100 iid uniform fields, 18×18, k=16,
RNG **89900** (this rung's block; the pilot's 83900 fields are NOT reused for
the confirmatory number). Statistic: **number of fields minting ≥1 proto**, and
`max_false_proto_size`. All three arms on the **same** fields.
**Decision rule: the control PASSES for the well-posed arm iff it is 0/100.**
Anything above 0 is a failure and is reported as one. n=100 is fixed here and
not revisited.

**M-B — the synthetic gate.** `tests/test_border_ownership_migrated.py` (9,
incumbent) + `tests/test_border_ownership_owned_migrated.py` (9, replacement) +
the same 9 re-run with `bown_wp` armed. **Decision rule: 9/9 in the well-posed
arm, or the discriminator has bought the control with false negatives and the
trade is reported rather than a side picked.**

**M-C — real-frame yield, AT THE SAME GRAIN.** Configuration **G72** (one 72×72
decode, 4×4 grid of 18×18 tiles), corpora **C1** `08630d4b…` / **C2**
`119eca43…`, pinned and asserted at run time, k=16, the incumbent's own 7
sampled frames. Statistic: **mean protos/frame** and **mean MULTI-cell
protos/frame**, all three arms.
**This is a COST measurement, not a headline.** The baseline is the
**incumbent at G72** (3.3–14.1 multi-cell protos/frame), never the retired
whole-frame zero. **No direction is claimed and no improvement will be claimed
from it.** Deterministic decode; no seed drawn.

**M-D — §13 / AST.** A term-tree AST walk (never a substring selector) over the
new conjunct, asserted both ways round: every `Lit` in a comparison is against a
0/1 flag (`bown`, `bown_own`, `bown_wp`, `bg`, `frame`, `owns`) or is the
pre-existing `2` against `Count(roots)`; **no** literal is compared against
`val`, `rim`, `glabel`, `cid`, `members` or `root`; the literal inventory is
unchanged in **kind**; the new conjunct contains **no literal on either side of
any glabel comparison**.

**M-E — vacuity gate FIRST (§1 fifth clause / FM-0).** The new conjunct must be
shown to **move something**: `max|wp=1 − wp=0|` on proto count must be non-zero
on a field where it is expected to bite. **If D == 0 exactly, the conjunct is
decorative — STOP and claim nothing.** Run before M-A/M-C.

**Dead-instrument controls, which must ACTUALLY FIRE:** D1 (committed 12×12
figure reproduces, all three arms), D2b (uniform field, frame stripped — the
vacuous-mint trap). Reused verbatim from the prior rung. The run aborts if D1
does not reproduce or D2b does not fire.

---

## 5 — PREDICTION, STATED IN ADVANCE (§3.7)

1. **M-A: 0/100 in the well-posed arm**, 26/100 in the replacement arm on the
   pilot's seeds and **some rate in the same neighbourhood on 89900**.
   *Proviso that would break it:* a speckle singleton whose four neighbours
   happen to be **one** enclosed component would survive. The pilot saw none in
   31, but 89900 is a different draw and a non-zero count is possible; the
   decision rule above is unmoved by my expectation.
2. **M-B: 9/9.** The synthetic stimuli are figure-on-blank, so no member faces
   two enclosed rivals and the conjunct is vacuously satisfied.
3. **M-C: the well-posed arm falls BELOW the replacement and I do not predict
   which side of the incumbent it lands on.** A photograph is a partition;
   three-way junctions where one cell abuts two rivals are common in it, and
   each one is now held open. **If it falls below the incumbent at G72, the
   discriminator is a bad trade and I will report it as one** — buying a clean
   negative control with real-frame yield is not obviously a good purchase, and
   this rung will not decide that by preferring the number it likes.
4. **M-E: D > 0**, from the speckle fields.

## 6 — THE THREE OUTCOMES THIS RUNG CAN HAVE

1. **A derivable discriminator exists and the control passes** with the synthetic
   gate intact and an acceptable real-frame cost.
2. **No derivable discriminator exists** — the conjunct fails M-A or M-B — and
   the single-cell false mint is an **accepted standing bound of the mechanism**,
   reported as a limitation, not hidden.
3. **The discriminator works but costs** — M-A passes, M-B or M-C degrades. Then
   **the trade is reported and no side is picked.**

## 7 — WHAT THIS RUNG DOES NOT TOUCH

`bo_mint_enclosed` (the incumbent path), `bo_mint_gestalt`, `bo_bgflood`,
`bo_label`, `bo_rim`, `bo_own`, and any Rust. The flood is not touched, so
component structure must remain byte-identical across all three arms — that is
itself checked (`n_components` equal per row).
