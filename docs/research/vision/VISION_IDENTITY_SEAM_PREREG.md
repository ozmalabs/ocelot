# CONNECT PERCEPT TO IDENTITY — PRE-REGISTRATION

*Written and committed BEFORE any headline number. Seeds **72000–72999**.*

**Engine (§10):** `25fa11652e83` @
`runners/dsl/python/substrate_rs/_native.abi3.so` — a **shared build from the
canonical tree, Rust source verified byte-identical** (`shared` verdict via
`ensure_tree_engine()`). **This rung adds NO Rust and NO new Term.** Arm B is
composed entirely from Terms that already exist (`Dot`, `MaxOver`, `Argmax`,
`Filter`, `IfThenElse`, `Gt`, `IndexAt`). `tests/test_engine_provenance_migrated.py`
+ `tests/test_provenance_endpoint_guard_migrated.py` were run **as their own
step before any number**: **628 passed, exit 0**.
**`data/`** is symlinked (§10.2), so the oracle's condition is the **200/0** one.
**Machine:** AMD Ryzen 5 9600X, 12 logical cores. Load recorded per window.

---

## 1. THE GAP, AND WHAT IS ACTUALLY ABSENT

Two probes measured the seam identically: **6 ProtoObject files ∩ 98 identity
files = 0**. The percept side and the identity side have never been connected.

**But "absent" needs a sharper statement than the probes gave it, and this rung
must not repeat their framing uncritically.** The cross-frame rung
(`VISION_CROSSFRAME_IDENTITY_RESULTS.md`) *did* identify real video regions
against held `ShapeSignature`s — but against a **FIXED, PRE-LOADED codebook of
16 tiles cut from the base frame**. Nothing was ever minted; the codebook never
grew; no identity was ever *acquired* from video.

**So the absence is specifically this: no percept has ever CAUSED the identity
layer to grow.** That is what this rung wires, and it is why the mint gate is
the crux rather than a detail.

---

## 2. CORPORA — fixed in advance, never pooled

| id | source | episode id (pinned) | statistics |
|---|---|---|---|
| **C1 CARTOON** | Jellyfin, *Middlemost Post* S2E1, `episode_index=0` | **`08630d4b7b215c469df19b9c42d7b617`** | broadcast cartoon |
| **C2 LIVE-ACTION** | Jellyfin, *Secrets of the Zoo: Down Under* S3E15, `episode_index=3` | **`119eca433329b36b19e5d69fef84966e`** | natural photographic |

150 frames, every 2nd decoded frame from `t=300 s`, area-averaged to **24×24**
grey; **100 base frames**; **16 regions of 6×6**; **k=4** quantization on a
fixed absolute 0–255 scale. Identical protocol and identical loader
(`video_probe_measure.jellyfin_frames`) to the cross-frame and verdict rungs, so
the numbers are comparable to theirs.

**If either returned episode id differs from the pin above, every delta is
UNINTERPRETABLE and the run is void.**

**Toy resolution, stated (§8):** 24×24. The drive affords ~57×57 in real time;
the sd/identity layer affords ~10×10 at K=1. **24×24 is inside the drive's
budget and outside the identity layer's** — which is precisely why the identity
layer's cost is reported as a trajectory rather than assumed away. Resolution
does not creep anywhere in this rung.

**Scope (§8):** two episodes of two series plus BSDS300 crops for the novelty
probes. Not a survey of video.

---

## 3. CUT STRATIFICATION — parameter-free, and NOT this rung's invention

At short Δ the failure unit is the FRAME, not the region. A frame step `t→t+1`
is a **CUT** iff the per-step mean `|Δ|` (0–255 scale) exceeds **Otsu's
threshold** on that corpus's own per-step distribution — a split with **no free
parameter** (§13), determined by the data's own bimodality. This is the verdict
rung's rule, reused verbatim, and it was independently corroborated there
against a second rung's error-concentration analysis (both named C1 base frames
34 and 47).

**Every arm-1 and arm-2 statistic is reported NON-CUT and CUT separately, never
merged.** Identity is not claimed to persist across a scene cut, and a failure
there is not counted as a failure of identity.

---

## 4. THE TWO ARMS — expressed as graph DATA, never as a Python code path (§0)

### ARM A — THE STOCK LOOP, UNMODIFIED

`shape_decode_loop` + `vision_sdloop`, **byte-unmodified**. The adapter writes an
`Observation` carrying exactly the attrs the loop already reads —
`signature` (36 `["cell", r, c, "v<q>"]` tuples in region-local coordinates),
`dim_types`, `key`, `status: "pending"` — plus `vq: 1`, the flag
`vq_grow_quantum` already uses to install a minted quantum as a held
`ShapeSignature` and bump `codebook_epoch`. **No new rule is added for arm A.**

- recognition: `sd_recognize`, which fires on `Count(residual) == 0` — exact
  coverage of all 36 cells by a **compositional** decode over the parts library;
- identity: `covered_by` = `Argmax(ShapeSignature, FixedCount(AntiUnify(...)))`;
- mint: `sd_mint_quantum` (residual non-empty AND all three explanation rungs
  ran and failed AND key-dedup) → `vq_grow_quantum` → `codebook_epoch += 1` →
  `sd_redecode`.

**`key` is unique per observation (`"<t>_<i>"`).** This is load-bearing and is
declared here so it cannot look like a choice made afterwards: a position-keyed
`key` (`"r03"`) would let `sd_mint_quantum`'s dedup clause suppress minting
**by position rather than by content**, manufacturing a low mint rate for a
reason that has nothing to do with recognition.

### ARM B — THE SAME TOPOLOGY, THE VERDICT REPLACED

`seeds/vision_identity_seam.json`, **shipping OFF** (`IdentitySeamParams.seam = 0.0`,
§9). Same loop topology — **decode → gate → mint → grow → epoch → re-decode** —
with exactly one thing changed: the recognition predicate is the **V3 continuous
verdict** (normalized cross-correlation) instead of exact compositional
coverage, and the accept/mint decision is made against a **MEASURED floor**.

This is the verdict rung's own design — *hold the proposal fixed, vary only the
verdict* — applied one level up, and it is named as such rather than presented
as a new mechanism.

**THE FLOOR IS MEASURED, NOT CHOSEN (§13).** An observation is accepted as a
held identity **iff its best score STRICTLY EXCEEDS the best score the same
comparator achieves, in the same substrate, against the same codebook, on
calibration noise probes (`probe_kind == "G2c"`)**. No numeric threshold appears
anywhere in the seed, and a gate asserts that (the verdict rung's
`test_..._writes_NO_constant`, ported). The floor is **re-armed on every
`codebook_epoch` bump**, so it tracks the growing codebook rather than freezing
at its initial value.

**Declared in advance as a known asymmetry, not discovered later:** arm B's
codebook starts **EMPTY** (`MaxOver` is scoped to signatures carrying
`seam_grown == 1.0`), so the first observation necessarily mints. Arm A's
codebook starts with the **17 `ShapeSignature`s `boot_core` already installs**,
which are not pixel-derived. The two arms therefore do **not** start from an
identical codebook, and no arm-A-vs-arm-B difference is attributed to the
verdict alone without saying so.

---

## 5. THE GATE IS A CONJUNCTION — all three, per corpus, cut-stratified

An arm PASSES only if **all three** clauses pass. Any failure is reported as a
failure (§7).

### Clause 1 — CROSS-FRAME IDENTITY PERSISTS

For each **non-cut** consecutive pair `(t, t+1)` and each region `i`:
`persist = 1` iff `identity(t+1, i) == identity(t, i)`, where `identity` is the
held-signature name the **graph** assigned (`covered_by` in arm A,
`identified_as` in arm B) and a minting observation takes its own new name.

**Unit of analysis = the BASE FRAME (§4), never the region** — the 16 regions of
one frame share an input and compete over one codebook, so they are not
independent. Statistic = mean over the 16 regions, per frame; `n` = number of
non-cut base frames; 95% paired t-CI.

**FLOOR: SHUFFLED-FRAME.** The same statistic with `t+1`'s regions drawn from a
frame chosen uniformly at random from the corpus (seeded, block 72000–72999),
excluding `|t' − t| ≤ 5`. **PASS iff the persistence CI lies strictly above the
shuffled-frame floor CI.**

### Clause 2 — DISTINCT THINGS STAY DISTINCT

*The arm that most easily goes unmeasured, and the one an identity layer that
merges everything scores perfectly on clause 1 by failing.*

`collapse = P(identity(t, i) == identity(t, j))` for `i ≠ j` within one frame.

**"Genuinely different" is defined by a statistic the comparator under test does
NOT compute** — **mean absolute RAW-GREY pixel difference** between the two
tiles, computed in numpy outside the graph. (NCC is the comparator under test;
using NCC to decide which pairs are genuinely different would be exactly the
self-check this arc has been bitten by three times.) Pairs are split at the
corpus's own **median** pixel difference: `DIFFERENT` above, `SIMILAR` below.

**PASS iff `collapse(DIFFERENT)` is CI-separated BELOW `collapse(SIMILAR)`.** A
relative contrast, not an absolute rate — so no threshold goes in (§13).
Also reported: `n_distinct_identities` in use per frame (a layer that merges
everything reads 1).

### Clause 3 — REFUSAL SURVIVES

After the codebook is built from the corpus's 100 frames, present three
genuinely-novel probe classes:

| class | what | n |
|---|---|---|
| **BSDS** | BSDS300 photograph tiles — a different corpus entirely | 64 |
| **NOISE** | uniform random tiles at the same k | 64 |
| **SHUFFLE** | corpus tiles with the cell VALUES permuted over the cell POSITIONS — multiset preserved exactly, arrangement destroyed (the cross-frame rung's own arrangement floor) | 64 |

`novel_handled = 1` iff the probe MINTS a new identity **or** is REFUSED
(arm B's `"novel"`), and `0` iff it is force-matched to a held identity.

**PASS iff `novel_handled` on each of the three classes is CI-separated ABOVE
`novel_handled` on a matched control set of 64 GENUINE held regions
re-presented from the corpus.** Unit = probe. **A relative contrast again** —
the control set supplies the base rate, so no absolute bar is set.

---

## 6. THE MINT-RATE TRAJECTORY — reported regardless of outcome

**Both failure modes look like success, so the rate is reported as a CURVE, not
a final count:** mints per frame index and cumulative `K`, per corpus, per arm.

- **mint rate sustained near 1.0** ⇒ a codebook growing without bound;
  recognition never improves. **That is logging, not learning.**
- **mint rate → 0 while clause 3 fails** ⇒ everything is recognised as something
  already held. **That looks like perfect stability and is a vacuous gate.**

Both readings are stated here so neither can be presented as a success later.

**Reported with it:** wall-clock per observation against `K`, because the
identity layer's cost is `N × K` and a growing codebook is the axis nobody has
measured.

---

## 7. DISCLOSURE — I AM NOT BLIND ON ARM A / C1 (§4, forking paths)

**Two pilots ran on already-burned seeds (block 55000, the cross-frame rung's)
BEFORE this pre-registration was written, and they showed me arm A's behaviour
on C1 — including its clause-3 outcome.** This is disclosed here, at commit
time, not retrospectively. The pilots are committed alongside this file
(`scripts/identity_seam_pilot.py`, `identity_seam_pilot2.py`,
`results/identity_seam_pilot*.json`) so exactly what I saw is auditable.

**No metric, arm, stratification or decision rule was chosen after seeing them**
— clauses 1–3 and the shuffled/median/control-set floors are the brief's, and
the cut rule and the measured-floor construction are prior rungs'.

**Blind:** arm A on **C2**, and **both corpora on arm B**. **Not blind:** arm A
on **C1**. Every table below is labelled accordingly. C1/arm A is therefore a
**replication of a seen effect on fresh seeds**, and is not counted as a
discovery.

**What the pilots showed, stated in advance so it cannot be re-told as a
finding:** on 96 C1 observations the stock loop minted 12 and then essentially
stopped; on the novelty probes it minted **8/32 BSDS, 1/8 NOISE, 0/8 SHUFFLE**,
force-matching the rest to held video identities.

---

## 8. PREDICTIONS, WITH PROVISOS (§3.7)

| # | prediction |
|---|---|
| **P1** | **ARM A passes clause 1** — persistence well above the shuffled floor on both corpora. |
| **P2** | **ARM A FAILS clause 3**, driven by SHUFFLE (predicted lowest `novel_handled` of the three classes). *Not blind on C1; blind on C2.* |
| **P3** | ARM A's mint trajectory **decays to ≈0 within ~20 frames**, and the decay is **not** learning — it is the parts library becoming compositionally complete, so `Count(residual)==0` is satisfiable by anything. |
| **P4** | **ARM B passes clause 3** on all three novelty classes. |
| **P5** | ARM B's persistence is **LOWER than ARM A's on C1 (cartoon)** and **comparable or higher on C2 (live-action)** — the verdict rung measured V3 as CI-negative on cartoon and +18pp on live-action. |
| **P6** | **The corpora disagree in sign on at least one clause** — the fifth reproduction of the no-pooling rule. |
| **P7** | ARM B's mint trajectory decays but **plateaus at a non-zero rate**, where arm A's goes to zero. |
| **P8** | ARM A passes clause 2 (its identity assignment is Hamming-NN, which is content-sensitive even when its *gate* is not). |

**The proviso I expect to break:** P5's C1 half assumes the verdict rung's
cartoon negative transfers from a fixed 16-way choice to a growing codebook. It
may not — a growing codebook changes what "the alternatives" are.

---

## 9. n, POWER, AND THE ABORT RULE

**n = 100 base frames per corpus per arm** (1,600 observations), matching the
cross-frame rung's n for direct comparability. Fixed by a cost pilot on burned
seeds: 30 C2 frames ran in **8.8 s** with `K` reaching 45, so 100 frames is
affordable in both arms. Clause 3 uses **64 probes per class** and a 64-probe
control.

**ABORT RULE, declared in advance:** if any single `(corpus, arm)` run exceeds
**20 minutes** wall-clock, it is aborted and the **partial trajectory plus the
cost curve are reported as the finding** — the `N × K` wall is a legitimate
result, not a failed run.

**Seeds:** block **72000–72999**, for the shuffled-frame floor draws, the noise
probes, the value-shuffle draws, and the codebook insertion-order permutation.
The 55000 block (already burned) was used for the pilots **only**.

---

## 10. WHAT A NULL MEANS

**A clean negative is a full result.** If percept and identity cannot be
connected without one of the three clauses collapsing, that is a structural
finding about the substrate and is reported as the headline. Specifically:

- **arm A failing clause 3 while passing clauses 1 and 2** would establish that
  the stock loop's mint gate is **vacuous on real pixels** — that
  `Count(residual) == 0` over a compositional decode is satisfied by anything
  once the parts library is large enough, so the loop *cannot* refuse and its
  decaying mint rate means nothing;
- **both arms failing clause 2** would establish that the seam collapses;
- **arm B failing clause 1 while passing clause 3** would establish a real
  trade — refusal bought at the cost of persistence — and the trade would be
  quoted with both numbers.

**No result is reported without its engine hash, its commit, its selector, its
corpus, and its cut stratum.**
