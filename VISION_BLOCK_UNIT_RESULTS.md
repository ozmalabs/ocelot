# EVERY PUBLISHED VIDEO-LINE CONTRAST, RE-ANALYSED AT THE BLOCK UNIT — RESULTS

*Pre-registration: `VISION_BLOCK_UNIT_PREREG.md`, committed BEFORE any contrast
number at **`5c75bc392d6949d5b5ea84bc98cbbd4ac3da75f3`** (base
**`6b50b97ab3ff49980de6a0704867b578aaac923d`**). Both endpoints pinned; no range
ends at `HEAD`.*

**Branch:** `worktree-agent-ac3007010de9e265a` — the intended
`gamma-substrate/block-unit-reanalysis` was **NOT provisioned**, and I am
reporting the branch I actually see, as instructed. **Sixth rung in a row under
an auto-generated name.**

**Engine (§10):** `25fa11652e83` — and note this is **the very engine that
produced the data being re-analysed** (the `provenance` field of both raw files
reads `engine 25fa11652e83`); the K-scope rung ran against a different local
build. **This rung never executes the engine** — every number is arithmetic on
committed rows. This tree's Rust source is byte-identical to canonical
(`diff -rq runners/dsl/src` reports only an untracked, uncompiled
`py.rs.selfmod.bak`).

**This rung adds NO Rust, NO Term, NO seed rule and NO constant.**
`git diff 6b50b97a` touches **exactly four files, all new**: the
pre-registration, the selector, the gates, and one new raw file.
`git diff 6b50b97a -- runners/dsl/src` is **empty**; `-- seeds` is **empty**;
**no committed raw datum was altered.**
`tests/test_engine_provenance_migrated.py` + `test_provenance_endpoint_guard_migrated.py`
were run **as their own step before any number: 633 passed, exit 0.**
`data/` symlinked, so the oracle's condition is the **222/0** one.
**Machine:** AMD Ryzen 5 9600X, 12 logical cores.
**Selectors (§12):** `scripts/block_unit_analyse.py` (the pre-registered
decision rule, applied mechanically, with every published value read from a
constant block quoting the two committed docs) · `tests/test_block_unit_migrated.py`
(16 gates, three positive-controlled).
**Raw:** `results/block_unit.json` (new, committed).
**Seeds:** block **77000–77999 claimed and NOT CONSUMED — zero seeds burned.**
The only RNG is the bootstrap's own inherited `20260720`. **The block is
returned intact**, gated by an AST walk, positive-controlled.

---

## 0. THE HEADLINE, IN ONE PARAGRAPH

**The line's strongest claim SURVIVES, and the expectation that framed this
rung is refuted.** `GROWN − CUTMATCHED` — *"MDL tile-selection is real and
works everywhere"* — was predicted to dissolve like everything else. It does
not: **+0.0625 → `[+0.0467, +0.0742]` on C1 and +0.0475 → `[+0.0200, +0.0795]`
on C2, both CI-separated at the block unit, with all five episodes agreeing on
the sign on both corpora.** Of **30 published contrasts re-analysed, 12
SURVIVE, 7 are AMBIGUOUS and 11 fall BELOW RESOLUTION** — not the near-total
collapse the brief anticipated. **The reason the brief expected otherwise is
itself the methodological finding: the K-scope rung's ≈0.10 resolution floor is
a property of the VECTOR it was measured on, not a constant of the corpus.**
Measured per contrast, the floor ranges **0.015 to 0.130, an 8.7× spread**, and
**inheriting 0.10 globally would have buried every single surviving result** —
including the priority contrast, whose own floor is 0.020. **What separates the
survivors from the casualties is not effect size but whether the contrast holds
the frame distribution fixed:** `GROWN − CUTMATCHED` has a between-block sd of
**0.0177** against `GROWN − UNIFORM`'s **0.1025** at the same checkpoint — a 5.8×
reduction — because comparing two codebooks *on the same frames* cancels the
episode-level variance that dominates everything else. **The accumulation
rung's gate 1 is the casualty**: `GROWN − UNIFORM` at cp = 90 is below
resolution on both corpora, confirming K-scope's post-hoc finding and extending
it — but three of the ten gate-1 checkpoints do survive, so my own prediction
that all would fail is **refuted**. **And the forward-looking half is the most
reusable output: resolving δ = 0.03 needs ~94 episodes at gate-1 variance but
only ~5 at the priority contrast's. POWER COMES FROM MORE EPISODES, NOT MORE
FRAMES — and, equally, from PAIRING AGAINST A FRAME-MATCHED CONTROL, which is
worth roughly an order of magnitude in episodes.**

**Three things I got wrong, all reported as findings.** (1) **P3 and P5 are
REFUTED** — I predicted every `GROWN − UNIFORM` and both accept-rate contrasts
would fail; three gate-1 checkpoints and four accept contrasts survive. (2)
**P2 is half wrong** — `C-D` is AMBIGUOUS on both corpora, not surviving, and
it misses by a hair (`[−0.0006, +0.0285]`). (3) **My own "inherited verbatim"
gate caught ME on its first firing** — I had added a convenience key to the
K-scope bootstrap's return dict (§5.2).

---

## 1. THE PRIORITY CONTRAST, FIRST AND PROMINENTLY

`GROWN − CUTMATCHED` is the accumulation rung's decomposition: the grown
codebook against a control **matched to its own frame distribution** (one entry
per grown mint, same frame, random region). It is the entire basis for *"MDL
tile-selection is real and works everywhere"*, it was CI-separated on **both**
corpora at the frame unit, and the K-scope rung explicitly flagged it as
un-re-analysed and told a successor to check it before quoting it again.

| corpus | published t-CI (n=50) | **block bootstrap (5 episodes)** | block means | **verdict** |
|---|---|---|---|---|
| **C1** | +0.0625 [+0.0575, +0.0675] ✅ | **[+0.0467, +0.0742]** ✅ | +0.0662, +0.0796, +0.0728, +0.0335, +0.0604 | **SURVIVES** |
| **C2** | +0.0475 [+0.0369, +0.0580] ✅ | **[+0.0200, +0.0795]** ✅ | +0.0261, +0.0707, +0.1035, +0.0209, +0.0160 | **SURVIVES** |

**All ten block means, across both corpora, are positive.** That is what
"survives at the block unit" means here and it is the honest reading: the
effect holds its sign in **every one of the five genuinely distinct episodes**
on **both** corpora. Contrast the same rung's gate 1 at the same checkpoint,
whose block means are **−0.0019, +0.1795, +0.1031, −0.0326, −0.0679** — three
of five the wrong way.

**This is the one clause of the video line that the unit correction does not
touch.** It is also the one the K-scope rung was careful to exclude from its
null, and that caution is now vindicated.

### 1.1 WHY IT SURVIVES, AND THE DESIGN LESSON THAT FALLS OUT

Not because it is bigger — `GROWN − UNIFORM` at cp = 65 is **larger**
(+0.0802) and barely scrapes through. It survives because its **between-block
sd is 0.0177 against gate 1's 0.1025 at the same checkpoint, a 5.8× reduction.**

The mechanism is structural: `RAND-CUTMATCHED` draws from **the grown arm's own
frames**. Episode-to-episode difficulty — which is what the block-level
variance *is* — therefore enters both arms identically and **cancels in the
pairing**. `RAND-UNIFORM` draws from everything seen so far, reintroducing it.

The tendency holds across the table, with named exceptions. Every
frame-matched-or-near-identical-codebook contrast has σ_b ≤ 0.0435
(`GROWN − CUTMATCHED` 0.0177/0.0382, `C-B` 0.0242/0.0204, `C-D` 0.0192/0.0221,
accept `ABSTAIN − NOABSTAIN_SUB` 0.0342/0.0435), while contrasts against an
independently drawn UNIFORM control run 0.0449–0.1742 — **though four
UNIFORM-control contrasts also land low** (accept C2 0.0156, `GROWN−UNIFORM@10`
C2 0.0199, `CUTMATCHED−UNIFORM` C2 0.0201, `GROWN−UNIFORM@90` C2 0.0281), so
this is a **measured tendency, not a law**, and it is labelled post-hoc.

**The design consequence is concrete and is quantified in §4: pairing against a
frame-matched control is worth roughly an order of magnitude in required
episodes.**

## 2. THE FULL TABLE — 30 CONTRASTS, CLASSIFIED

Classification rule fixed in `VISION_BLOCK_UNIT_PREREG.md` §4 **before any
number**: **SURVIVES** = block-bootstrap CI excludes zero; **AMBIGUOUS** = CI
includes zero but `|mean| ≥ 0.5·δ*`; **BELOW RESOLUTION** = CI includes zero and
`|mean| < 0.5·δ*`. `δ*` is the **per-vector** resolution floor (§3). `signs` =
how many of the five episode means share the mean's sign.

### 2.1 ACCUMULATION RUNG

| § | corpus | contrast | published t-CI | **block bootstrap** | δ* | σ_b | signs | **class** |
|---|---|---|---|---|---|---|---|---|
| 3.2 | C1 | **GROWN − CUTMATCHED** | +0.0625 [+0.0575, +0.0675] ✅ | **[+0.0467, +0.0742]** ✅ | 0.020 | 0.0177 | 5/5 | **SURVIVES** |
| 3.2 | C2 | **GROWN − CUTMATCHED** | +0.0475 [+0.0369, +0.0580] ✅ | **[+0.0200, +0.0795]** ✅ | 0.030 | 0.0382 | 5/5 | **SURVIVES** |
| 3.2 | C1 | CUTMATCHED − UNIFORM | −0.0265 [−0.0513, −0.0017] ✅ | [−0.0918, +0.0524] | 0.070 | 0.0906 | 3/5 | BELOW RESOLUTION |
| 3.2 | C2 | CUTMATCHED − UNIFORM | −0.0420 [−0.0552, −0.0288] ✅ | **[−0.0583, −0.0286]** ✅ | 0.020 | 0.0201 | 5/5 | **SURVIVES** |
| 3.1 | C1 | GROWN − UNIFORM @10 | +0.0742 [+0.0611, +0.0873] ✅ | **[+0.0359, +0.1125]** ✅ | 0.040 | 0.0499 | 5/5 | **SURVIVES** |
| 3.1 | C2 | GROWN − UNIFORM @10 | +0.0535 [+0.0457, +0.0613] ✅ | **[+0.0414, +0.0710]** ✅ | 0.015 | 0.0199 | 5/5 | **SURVIVES** |
| 3.1 | C1 | GROWN − UNIFORM @25 | +0.0450 [+0.0111, +0.0789] ✅ | [−0.0453, +0.1461] | 0.095 | 0.1167 | 4/5 | BELOW RESOLUTION |
| 3.1 | C2 | GROWN − UNIFORM @25 | −0.0321 [−0.0523, −0.0119] ✅ | [−0.0816, +0.0146] | 0.050 | 0.0604 | 4/5 | AMBIGUOUS |
| 3.1 | C1 | GROWN − UNIFORM @45 | +0.0268 [−0.0003, +0.0539] ❌ | [−0.0528, +0.1100] | 0.080 | 0.0972 | 4/5 | BELOW RESOLUTION |
| 3.1 | C2 | GROWN − UNIFORM @45 | +0.0076 [−0.0062, +0.0214] ❌ | [−0.0276, +0.0428] | 0.040 | 0.0449 | 3/5 | BELOW RESOLUTION |
| 3.1 | C1 | GROWN − UNIFORM @65 | +0.0802 [+0.0586, +0.1018] ✅ | **[+0.0094, +0.1352]** ✅ | 0.075 | 0.0794 | 4/5 | **SURVIVES** |
| 3.1 | C2 | GROWN − UNIFORM @65 | −0.0008 [−0.0212, +0.0196] ❌ | [−0.0532, +0.0516] | 0.055 | 0.0674 | 3/5 | BELOW RESOLUTION |
| **3.1** | **C1** | **GROWN − UNIFORM @90 (gate 1)** | **+0.0360 [+0.0086, +0.0635]** ✅ | **[−0.0406, +0.1218]** ❌ | 0.080 | 0.1025 | 3/5 | **BELOW RESOLUTION** |
| **3.1** | **C2** | **GROWN − UNIFORM @90 (gate 1)** | +0.0054 [−0.0062, +0.0171] ❌ | [−0.0167, +0.0276] | 0.025 | 0.0281 | 3/5 | **BELOW RESOLUTION** |
| 3.3 | C1 | accept GROWN − UNIFORM | +0.1000 [+0.0683, +0.1317] ✅ | **[+0.0125, +0.1875]** ✅ | 0.090 | 0.1135 | 4/5 | **SURVIVES** |
| 3.3 | C2 | accept GROWN − UNIFORM | −0.0138 [−0.0212, −0.0063] ✅ | **[−0.0262, −0.0025]** ✅ | 0.015 | 0.0156 | 5/5 | **SURVIVES** |
| 8 | C1 | shuffled − in-order | +0.0228 [+0.0078, +0.0378] ✅ | [−0.0213, +0.0697] | 0.045 | 0.0583 | 3/5 | AMBIGUOUS |
| 8 | C2 | shuffled − in-order | −0.0090 [−0.0307, +0.0128] ❌ | [−0.0670, +0.0491] | 0.060 | 0.0752 | 3/5 | BELOW RESOLUTION |

### 2.2 CUT-MINT POLICY RUNG

| § | corpus | contrast | published t-CI | **block bootstrap** | δ* | σ_b | signs | **class** |
|---|---|---|---|---|---|---|---|---|
| 3 | C1 | C-A ABSTAIN − UNIFORM | +0.0272 [+0.0049, +0.0494] ✅ | [−0.0164, +0.0921] | 0.045 | 0.0708 | 4/5 | AMBIGUOUS |
| 3 | C2 | C-A ABSTAIN − UNIFORM | +0.0001 [−0.0340, +0.0341] ❌ | [−0.1030, +0.0973] | 0.105 | 0.1278 | 3/5 | BELOW RESOLUTION |
| **3** | **C1** | **C-B ABSTAIN − NOABSTAIN_SUB** | **+0.0507 [+0.0444, +0.0569]** ✅ | **[+0.0339, +0.0720]** ✅ | 0.020 | 0.0242 | 5/5 | **SURVIVES** |
| **3** | **C2** | **C-B ABSTAIN − NOABSTAIN_SUB** | **+0.0236 [+0.0171, +0.0300]** ✅ | **[+0.0071, +0.0391]** ✅ | 0.020 | 0.0204 | 4/5 | **SURVIVES** |
| 3 | C1 | C-C NOABSTAIN_SUB − UNIFORM | −0.0235 [−0.0498, +0.0028] ❌ | [−0.0875, +0.0544] | 0.065 | 0.0885 | 4/5 | BELOW RESOLUTION |
| 3 | C2 | C-C NOABSTAIN_SUB − UNIFORM | −0.0235 [−0.0606, +0.0135] ❌ | [−0.1333, +0.0863] | 0.110 | 0.1403 | 3/5 | BELOW RESOLUTION |
| **3** | **C1** | **C-D ABSTAIN − NOABSTAIN_PRE** | **+0.0138 [+0.0088, +0.0187]** ✅ | **[−0.0006, +0.0285]** ❌ | 0.015 | 0.0192 | 4/5 | **AMBIGUOUS** |
| **3** | **C2** | **C-D ABSTAIN − NOABSTAIN_PRE** | **+0.0127 [+0.0060, +0.0194]** ✅ | **[−0.0010, +0.0329]** ❌ | 0.015 | 0.0221 | 3/5 | **AMBIGUOUS** |
| 3.4 | C1 | accept ABSTAIN − UNIFORM | +0.0450 [+0.0244, +0.0656] ✅ | [−0.0100, +0.0800] | 0.055 | 0.0610 | 4/5 | AMBIGUOUS |
| 3.4 | C2 | accept ABSTAIN − UNIFORM | +0.1200 [+0.0731, +0.1669] ✅ | [−0.0100, +0.2525] | 0.130 | 0.1742 | 3/5 | AMBIGUOUS |
| raw | C1 | accept ABSTAIN − NOABSTAIN_SUB | +0.0875 [+0.0780, +0.0970] ✅ | **[+0.0625, +0.1125]** ✅ | 0.025 | 0.0342 | 5/5 | **SURVIVES** |
| raw | C2 | accept ABSTAIN − NOABSTAIN_SUB | +0.0500 [+0.0336, +0.0664] ✅ | **[+0.0175, +0.0825]** ✅ | 0.035 | 0.0435 | 4/5 | **SURVIVES** |

### 2.3 TALLY, AND WHAT MOVED

**12 SURVIVE · 7 AMBIGUOUS · 11 BELOW RESOLUTION.**

Of the **24 contrasts published as CI-separated** at the frame unit, **12
survive, 7 become ambiguous and 5 fall below resolution.** The six published as
null all stay null (§2.4). **The single most consequential change is the
accumulation rung's gate 1** — the clause the whole "does watching video change
the codebook usefully" question was scored on — which is **below resolution on
both corpora**. This confirms and extends the K-scope rung's post-hoc finding.

### 2.4 A STRUCTURAL FACT, PRE-REGISTERED AND CONFIRMED — THE CORRECTION IS ONE-DIRECTIONAL

The block bootstrap **only ever widens** (gate **G3**: bootstrap width ≥ t-CI
width on all 30 vectors, ratios 1.13–3.05). So **no published null can be
rescued here, and none was** — gated directly
(`test_G3_no_published_null_became_a_pass`). This was stated in the
pre-registration so that the six unchanged nulls are not misread as a finding
of this rung. **Everything this re-analysis can do, it does in one direction.**

## 3. THE METHODOLOGICAL FINDING: THE ≈0.10 FLOOR IS NOT A CORPUS CONSTANT

The K-scope rung measured the block bootstrap's resolution floor at **≈0.10**
and observed, correctly and with a gate, that **every quantity in its own
dispute sat below it.** The brief for this rung carried that number forward as
a corpus-level property — *"the bootstrap's resolution floor is ~0.10, above
every quantity in the dispute, so the likely outcome is that most of the line
falls below resolution."*

**Measured per vector, the floor ranges 0.015 to 0.130 — an 8.7× spread.**

| floor δ* | contrasts |
|---|---|
| 0.015–0.030 | `GROWN−CUTMATCHED` (both), `C-B` (both), `C-D` (both), accept `GROWN−UNIFORM` C2, `GROWN−UNIFORM@10` C2, `CUTMATCHED−UNIFORM` C2, `GROWN−UNIFORM@90` C2, accept `ABSTAIN−NOABSTAIN` C1 |
| 0.035–0.075 | `GROWN−UNIFORM@10/@45/@65`, `C-A` C1, `C-C` C1, shuffled arms, accept `ABSTAIN−UNIFORM` C1 |
| 0.080–0.130 | `GROWN−UNIFORM@25/@45/@90` C1, accept `GROWN−UNIFORM` C1, `C-A` C2, `C-C` C2, accept `ABSTAIN−UNIFORM` C2 |

**Had this rung inherited 0.10 as a global constant, it would have classified
every one of the twelve survivors as "below resolution"** — including the
priority contrast, whose own floor is **0.020**, five times lower. The floor is
set by a vector's **between-block variance**, and that varies by an order of
magnitude across contrasts for the structural reason in §1.1.

**K-scope's number was right about K-scope's vector.** What is corrected here
is its **generalisation**, which this rung's brief made and which the K-scope
rung itself did not (it scoped its floor claim to "the disputed magnitudes").
**P4 confirmed, and it is the reason the headline came out the way it did.**

## 4. THE EPISODE-COUNT DESIGN SPEC — THE MOST REUSABLE OUTPUT

**A DESIGN PROJECTION, NOT A MEASUREMENT.** Two-sided, 80% power, **unit = the
episode**:

> `B` such that `δ ≥ (t(0.975, B−1) + t(0.80, B−1)) · σ_b / √B`

| σ_b (source) | δ=0.01 | δ=0.02 | **δ=0.03** | **δ=0.05** | **δ=0.10** | δ=0.15 | δ=0.20 |
|---|---|---|---|---|---|---|---|
| **0.1025** — gate 1 `GROWN−UNIFORM@90` C1 | 827 | 209 | **94** | **35** | **11** | 6 | 5 |
| **0.1100** — worst observed (typical high) | 952 | 240 | **108** | **40** | **12** | 7 | 5 |
| **0.0800** — typical mid | 505 | 128 | **58** | **23** | **8** | 5 | 4 |
| **0.0382** — priority `GROWN−CUTMATCHED` C2 | 117 | 31 | **15** | **7** | **4** | 3 | 3 |
| **0.0242** — policy `C-B` C1 | 49 | 14 | **8** | **5** | **3** | 3 | 3 |
| **0.0177** — priority `GROWN−CUTMATCHED` C1 | 27 | 9 | **5** | **4** | **3** | 2 | 2 |

**Read the two ends against each other.** To resolve **δ = 0.03** — roughly the
size of the accumulation rung's gate-1 effect — you need **~94 episodes** at
gate-1 variance, or **~5** at the priority contrast's. **The corpus has FIVE.**
That is the whole story of this line in one comparison: it was never
under-powered in general, it was under-powered *for the contrasts it scored its
gates on*.

**Two design rules follow, and they are independent:**

1. **POWER COMES FROM MORE EPISODES, NOT MORE FRAMES.** Within-block sd is
   0.004–0.014 against between-block 0.081–0.113 in the worst cases. Adding
   frames inside an episode buys almost nothing; the frame-unit t-CI's
   apparent precision is the artifact. **Any future video rung must sample
   episodes, not frames, and must state its n in blocks.**
2. **PAIR AGAINST A FRAME-MATCHED CONTROL.** Worth ~94 → ~5 episodes at
   δ = 0.03 in this corpus (§1.1) — **an order of magnitude cheaper than buying
   the same power with episodes.** Do both.

**Assumptions, stated as such:** future episodes are exchangeable with these
five and share σ_b; **σ_b is itself estimated from FIVE blocks** and is
correspondingly uncertain, so these `B` are order-of-magnitude design guidance,
not commitments. Two episodes from two series is a thin basis for projecting
episode-level variance in general.

## 5. GATES, AND THE TWO THAT BIT

All four pre-registered gates pass. **G1: all 30 published endpoints reproduce
from raw rows** (28 against doc constants, 2 against the rung's own stored
contrast, marked `raw` in §2.2). **G2: positive-controlled per vector** — every
one of the 30 has a measured floor on the grid, and three zero-mean nulls of
matched sd correctly fail to separate. **G3: one-directional** (§2.4).
**G4: seeds 77000–77999 unconsumed**, AST walk, positive-controlled against a
planted `RandomState(77123)` with a docstring literal correctly ignored.

### 5.1 EVERYTHING PUBLISHED WAS RECOMPUTABLE — WHICH IS ITSELF THE FINDING

**Nothing in scope failed G1, and nothing in scope was lost.** Both rungs stored
the per-held-out-frame primary read-out (`max_rows`) **and** the accept-rate
read-out (`acc_rows`) for **every arm at every checkpoint**, plus identical
`held`/`train` frame lists. That is why a complete re-analysis was possible at
zero measurement cost, and it is worth recording as a **positive** result about
those rungs' data hygiene: **had they stored only summary CIs, this rung could
not exist.**

### 5.2 MY "INHERITED VERBATIM" GATE CAUGHT ME ON ITS FIRST FIRING

`test_the_block_bootstrap_is_INHERITED_VERBATIM_not_re_derived` AST-compares
this rung's `block_bootstrap_ci` against `scripts/k_scope_analyse.py`'s. It went
**red on its first run — on my own code.** I had added a `"width"` key to the
inherited function's return dict for convenience.

The computation was untouched and every interval would have been identical. But
the gate exists because **§5 forbids re-deriving the verdict instrument**, and
"I only added a field" is exactly the sort of edit that erodes an inherited
instrument one convenience at a time. **The selector was fixed (width is now
derived at the call site) rather than the gate weakened**, and a further
assertion now checks the key is absent from the stored bootstrap dict.

This is the arc's recurring lesson landing in the good direction for once: a
gate that had never been able to fail **was able**, and it fired immediately.

### 5.3 THE FLOOR IS COMPUTED PER VECTOR — AND THAT WAS A PRE-REGISTERED CHOICE, NOT A RESCUE

§3.1 of the pre-registration fixed per-vector floors **before any number
existed**, with the reasoning given there (published half-widths already spanned
7×, so a global floor was known in advance to be wrong-in-the-conservative-
direction). **This matters because per-vector floors are what let twelve
contrasts survive**, and choosing them after seeing that a global floor killed
everything would have been §5 metric surgery of the plainest kind. It was
committed at `5c75bc39`, before `results/block_unit.json` existed.

## 6. MY PREDICTIONS, SCORED (§3.7)

| # | prediction | outcome |
|---|---|---|
| **P1** | `GROWN − CUTMATCHED` **SURVIVES on both corpora** | **RIGHT**, and it was the prediction I flagged as most weakly held relative to its importance. Both corpora, all ten block means positive. |
| **P2** | `C-B` survives both; `C-D` survives at least C1 | **HALF RIGHT.** `C-B` survives both. **`C-D` is AMBIGUOUS on both** — and misses by a hair on C1 (`[−0.0006, +0.0285]`), the narrowest near-miss in the table. |
| **P3** | **every** `GROWN − UNIFORM` gate-1 contrast fails | **REFUTED.** Three of ten survive (@10 both corpora, @65 C1). The final-checkpoint one — the one that scores the gate — does fail, on both. |
| **P4** | the per-vector floor spans **> an order of magnitude**; "≈0.10" is not a corpus constant | **RIGHT**, 8.7× (0.015–0.130) — just under my "order of magnitude", and the substantive claim holds decisively (§3). |
| **P5** | both accept-rate contrasts fail | **REFUTED.** Four of six accept contrasts survive, including accept `GROWN − UNIFORM` on **both** corpora. |
| **P6** | δ = 0.03 at gate-1 σ_b needs **B in the high tens to low hundreds** | **RIGHT** — 94 episodes. |

**3 right, 1 half, 2 refuted.** **P3 and P5 are the useful misses**: I expected
the correction to be near-total because I had absorbed the brief's global-floor
framing, and **both refutations are the same error** — assuming episode-level
variance is a property of the corpus rather than of the contrast. **Being wrong
about that twice is what located §3, which is the rung's methodological
result.**

## 7. WHAT THIS RUNG DOES **NOT** SHOW (§8)

- **It does not show the below-resolution effects are zero or absent.** Eleven
  contrasts land there and the correct reading for **every one of them** is
  *this corpus, at five effective units, cannot resolve an effect of this size
  in either direction.* That is a fact about the **measurement design**, not
  about the mechanism. **Gated** (`test_below_resolution_is_never_reported_as_absence`)
  so no successor can quietly upgrade it into a demonstration of absence.
- **It does not vindicate the accumulation rung's gate 1.** That clause is
  below resolution on both corpora. The conjunction the rung reported as FAILED
  remains failed, and its one positive clause is now unresolvable.
- **"MDL selection works everywhere" survives at the block unit — but
  "everywhere" still means two episodes of two series at 24×24.** What survives
  is that on **these** five held-out episodes per corpus, selection beats a
  frame-matched control with consistent sign. That is a real, CI-separated
  result and it is **not** a claim about video in general.
- **SURVIVES is not "large".** With five blocks the bootstrap's percentile
  endpoints are estimated from five units and the resample space is only
  5⁵ = 3,125 combinations. In practice "survives" here is close to *"all five
  episodes agree on the sign with margin"* — informative, and coarse.
- **AMBIGUOUS is a real third class, not a soft null.** Seven contrasts sit
  between; `C-D` on C1 misses by 0.0006. Successors should treat these as
  **unresolved and worth powering**, not as failures.
- **The out-of-scope contrasts got no verdict, and that is not a clean bill.**
  Gate 2 (mint rate, unit = training frame), gate 3 (refusal, unit = probe,
  n = 64 unpaired), §7a/§7b (unit = codebook entry) and the cut-mint
  false-positive counts (unit = step) have **different units**, so this
  instrument does not apply. Where they were already null at their own unit
  (gate 2, §7b), §2.4 means they stay null. **Their exposure to
  episode-level variance is untested, not cleared.**
- **The cut-mint policy effect still rests on ONE burst at ONE frame per
  corpus.** `C-B` surviving at the block unit says the *held-out consequence*
  of that one relocation holds its sign across episodes. It does **not** turn
  n = 1 event into a sample, and the rung's own §7 bound stands unchanged.
- **The design spec is a projection** with σ_b estimated from five blocks
  (§4).
- **Two corpora, 150 frames each, 24×24 grey, 6×6 regions, k = 4.** Regions are
  an adapter-chosen grid; **no object label exists anywhere in the
  measurement**; "recognition" means region identity against a held codebook.
- **No p-value is quoted anywhere.** CIs only.
- **§9:** no default moved, no committed seed was edited, no Rust was touched,
  **no committed raw datum was altered** — `git diff 6b50b97a` touches four new
  files only.

## 8. VERIFICATION

| check | result | exit |
|---|---|---|
| `tests/test_engine_provenance_migrated.py` + endpoint guard, **own step, before any number** | **633 passed** | **0** |
| `bash scripts/rung7_vision_bench.sh` **before** the rung | **222 passed** (151.6 s) | **0** |
| `bash scripts/rung7_vision_bench.sh` **after** the rung | **222 passed** (156.2 s) | **0** |
| `tests/test_block_unit_migrated.py` | **16 passed** | 0 |
| G1: 30/30 published endpoints reproduced from raw rows | **all reproduce** | — |
| G2: per-vector floor exists on all 30; 3 zero-mean nulls refuse to separate | **alive, and refuses** | — |
| G3: bootstrap width ≥ t-CI width on all 30 (ratios 1.13–3.05) | **one-directional** | — |
| G4: seed-block audit (AST walk), positive-controlled | **planted `RandomState(77123)` caught; docstring literal ignored** | — |
| bootstrap inherited VERBATIM from `k_scope_analyse.py` (AST-identical) | **identical — after it caught my own edit (§5.2)** | — |
| bootstrap determinism (same seed → same endpoints) | **identical** | — |
| `git diff 6b50b97a -- runners/dsl/src` / `-- seeds` | **both empty** | — |
| pre-existing files in `results/` altered | **none** | — |

## 9. WHAT THE NEXT RUNG SHOULD PRE-REGISTER AGAINST

Ranked by what this evidence supports.

1. **BUILD THE NEXT VIDEO CORPUS FROM §4'S TABLE.** The design constraint is
   now a number, not a caveat: **~94 episodes to resolve δ = 0.03 against an
   independent control, ~5–15 against a frame-matched one.** Any successor
   should pre-register **n in episodes**, pick its target δ from §4, and
   **pair against a frame-matched control by construction**. This is the
   cheapest large win available to this line and it needs no new mechanism.
2. **RE-RUN THE ACCUMULATION GATES WITH THE FRAME-MATCHED CONTROL AS PRIMARY.**
   §1.1 shows `RAND-CUTMATCHED` is the low-variance comparator and
   `RAND-UNIFORM` the high-variance one; gate 1 was scored on the latter and is
   unresolvable, while the decomposition on the former survives on both
   corpora. **The pre-registered primary was the noisier of two controls the
   rung already had.** Note the trade honestly: the frame-matched control
   answers a *narrower* question (selection **given** the frame distribution),
   which is why the rung kept both — but it is the one this corpus can resolve.
3. **THE `C-D` NEAR-MISS IS THE CHEAPEST OPEN QUESTION.** `[−0.0006, +0.0285]`
   on C1 and `[−0.0010, +0.0329]` on C2, both ambiguous by a hair, both the
   *conservative* size-match of a mechanism whose primary size-match survives.
   §4 says **~8–15 episodes** would settle it.
4. **THE OUT-OF-SCOPE UNITS ARE UNTESTED, NOT CLEARED** (§7). Gate 3's refusal
   probes and gate 2's mint rates have never been examined for episode-level
   variance. Gate 2 is already null and cannot be rescued; **gate 3 passed on
   both corpora and has not been checked at all** — and it is the one gate the
   accumulation rung passed everywhere.

**What should NOT be pre-registered:** anything treating the eleven
below-resolution rows as **demonstrated absences**. They are unresolved. The
distinction is gated in the raw file and in the test suite, and it is the whole
point of the classification.
