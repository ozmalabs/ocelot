# BLOB-NATIVE SAMPLING — results

Pre-registration `VISION_BLOB_NATIVE_PREREG.md`, committed **df0156a4** before
any number, corrected **58e43007** (§2.1). Seeds 80000–80999.
Engine **d6097900e8b5**. Provenance gate run as its own step (635 passed).
Oracle `scripts/rung7_vision_bench.sh`: **212 passed, 10 skipped, exit 0** — the
10 skips are all `BSDS300 corpus absent`, and are present before and after this
rung's changes. (The brief specified "222 passed"; 222 is the COLLECTED count.
This tree has no BSDS300, so 10 of them skip. Recorded rather than reported as
222.)

Corpora: **C1** cartoon (episode_index 0, pin `08630d4b…`) and **C2**
live-action (episode_index 3, pin `119eca43…`), pins checked, mismatch VOIDs.
**Reported per corpus, never pooled.**

---

## THE HEADLINE, IN ONE LINE

**Blobs are ~9× cheaper and proto-objects still fail — and the cost win is
bought by destroying the arrangement signal, which only the re-earned floors
revealed.** Two of the rung's three commissioning premises were false before any
code was written, and the third (the sharpest test) is a clean registered null.

---

## H3 — THE SHARPEST TEST: **NULL, exactly as registered**

**Does a blob decomposition make proto-objects work where the square grid did
not? No.**

The baseline reproduces the committed result exactly — **C1, k=16: 0 protos on
7/7 frames**. The instrument is alive: the positive control returns **1 proto,
24 members, 7 sweeps**, the committed synthetic answer.

Pre-registered metric (`n_protos`), and the post-hoc multi-cell breakdown that
interprets it — `members ≥ 2`, i.e. a proto made of more than a single sample,
labelled post-hoc because it was not pre-registered:

| corpus | k | arm | samples | protos (all) | protos (members ≥ 2) |
|---|---|---|---|---|---|
| C1 | 16 | square | 256 | 0 | **0** |
| C1 | 16 | blob κ=2 | 13 | 1 | **0** |
| C1 | 16 | blob κ=3 | 19 | 7 | **0** |
| C1 | 16 | blob κ=4 | 27 | 7 | **0** |
| C2 | 16 | square | 256 | 2 | 1 |
| C2 | 16 | blob κ=3 | 19 | 7 | **0** |
| C2 | 16 | blob κ=4 | 27 | 8 | **0** |
| C1 | 8 | blob κ=2,3,4 | 13/19/27 | 4/9/11 | **0 / 0 / 0** |
| C2 | 8 | blob κ=2,3,4 | 13/19/27 | 1/9/8 | **0 / 0 / 0** |

**At k=8 and k=16, every blob arm on both corpora produces ZERO multi-cell
protos.** The apparent "1 proto per frame" is a single-blob artifact: proto root
**0 — the foveal blob — mints in all 56 rows** at κ=3 and κ=4, with
`members = 1`. One sample is not an object.

**This is the major finding the brief anticipated: the obstruction is not the
sampling geometry.** §0.3 established why, before the run — the proto stage
never sees the region grid at all. It boots a fresh substrate, loads only
`vision_border_ownership`, and consumes the raw quantized luminance lattice; the
gates that must pass are **value-flood** conditions (`bg` floods inward from the
border along *equal-value* adjacency; single-ground closure refuses any figure
bordered by two differently-labelled ground cells), not tile-boundary
conditions. Changing the sampling geometry re-runs the same floods on a
different adjacency graph and does not touch either gate. **The proto-object
failure needs a different explanation entirely** — it is a property of the
figure/ground rules against natural luminance statistics, not of the percept's
sampling lattice.

The rung also converted §0.3's attribution from inference to measurement: the
per-frame diagnostics record `n_enclosed`, `n_enclosed_components`, and
`n_refused_by_ground_gate` for every run (`results/blob_proto.json`).

---

## H1 — COST: **graph time falls ~9×, and the read-back was never the cost**

Matched field (GRID=24), matched task (identify one of the same 16 region
footprints), `hamming`, k=4, 6 frames per corpus. Mean per frame:

| corpus | arm | samples | **graph** | parse | reference | accuracy |
|---|---|---|---|---|---|---|
| C1 | square | 576 | **117.9 ms** | 0.03 ms | 0.52 ms | 1.000 |
| C1 | blob κ=2.00 | 19 | **5.4 ms** | 0.02 ms | 0.05 ms | 0.625 |
| C1 | blob κ=4.00 | 40 | **8.8 ms** | 0.02 ms | 0.07 ms | 0.812 |
| C1 | blob κ=6.75 | 64 | **13.0 ms** | 0.02 ms | 0.08 ms | 1.000 |
| C2 | square | 576 | **124.2 ms** | 0.04 ms | 0.58 ms | 0.927 |
| C2 | blob κ=6.75 | 64 | **13.0 ms** | 0.02 ms | 0.08 ms | 1.000 |

**H1 holds on graph cost: 9.1× (C1) and 9.6× (C2) at equal-or-better raw
accuracy**, carrying 64 samples instead of 576. Both corpora agree.

**Read-back is not a cost here and never was.** Split as pre-registered: the
graph-answer parse is **0.02–0.04 ms**, i.e. ~0.02% of graph time, and the
outside reference is 0.05–0.58 ms. This is the §0.2 finding confirmed in the
arm: **the raster was not the read-back cost.** The rung pre-committed to not
claiming that saving, and does not claim it.

### §0.2, restated because it corrects the commissioning premise

The "~10× read-back" reproduces exactly — but it is a property of the **arm**,
not the representation. Under `ncc` the graph score is a single `Dot` (0.042 s
at 64 regions) while `read()` recomputes **two** Python references per group,
including a fixed `hamming` V0 tie diagnostic that is **97% of read-back**.
Under `hamming` the ratio inverts: read-back is 0.5–1.8% of graph and *falls*
with scale. The name parse is ~1e-4 of read-back in every configuration
measured. **Removing the named grid cannot reduce read-back.**

---

## H2 — RECOGNITION: **FAILS. The cost win is bought by destroying arrangement.**

This is the result that the pre-registered requirement to **re-earn every floor**
exists to catch, and it inverts the reading of H1.

| corpus | arm | samples | accuracy | **A3 floor** (arrangement destroyed) | G2c floor | **margin over A3** |
|---|---|---|---|---|---|---|
| C1 | square | 576 | 1.000 | **0.177** | 0.042 | **0.823** |
| C1 | blob κ=2.00 | 19 | 0.625 | 0.604 | 0.302 | **0.021** |
| C1 | blob κ=4.00 | 40 | 0.812 | 0.792 | 0.469 | **0.020** |
| C1 | blob κ=6.75 | 64 | 1.000 | **0.927** | 0.573 | **0.073** |
| C2 | square | 576 | 0.927 | **0.177** | 0.052 | **0.750** |
| C2 | blob κ=2.00 | 19 | 0.625 | 0.594 | 0.250 | **0.031** |
| C2 | blob κ=4.00 | 40 | 0.812 | 0.760 | 0.417 | **0.052** |
| C2 | blob κ=6.75 | 64 | 1.000 | **0.927** | 0.656 | **0.073** |

The A3 floor destroys the arrangement while preserving the value multiset
**exactly**. The square arm collapses under it (1.000 → 0.177): its accuracy is
carried by arrangement. **The blob arm barely moves (1.000 → 0.927): its
accuracy is carried by the value multiset.**

**The margin over the arrangement floor falls from 0.823 to 0.073 — better than
an order of magnitude — and it is ~0.02–0.07 at EVERY blob count tested, on BOTH
corpora.** Raw accuracy rises with blob count (0.625 → 0.812 → 1.000) but so
does the floor (0.604 → 0.792 → 0.927); the *signal* never appears. At no
resolution tested does the blob representation show a real arrangement signal.

**Mechanism**: at κ=6.75, 64 blobs over 16 footprints is ~4 samples per
footprint, and 4 values almost always identify a footprint by multiset alone.
The representation has drifted toward the invariant comparator's own declared
**zero-discrimination anchor** — the position-free value histogram, whose floor
equals its arm by construction.

**So the honest reading of H1+H2 together: the 9× is largely the cheapness of
carrying less information, not of carrying the same information better.** Had
the square arm's floors been transferred instead of re-earned, this rung would
have reported a 9× cost win at no accuracy cost — a completely false headline,
off by an order of magnitude in the quantity that matters.

---

## Gate 3 — the parser defect is gone BY CONSTRUCTION

A blob is identified by its **integer index**; the signature is
`["blob", i, "v<q>"]`. There is **no fixed-width name field to overflow**. The
`r143`→`14` defect (a 2-digit name field, plus an answer parse requiring exactly
3 characters so every 3-digit answer returned `None`) cannot occur in a
representation with no name string. Read-back answers were checked in range with
**`n_answer_none` = 0 across every arm and every frame**.

The square baseline retains a name, but read with the **full remaining field**
(`nm[1:]`), not a fixed slice — so the baseline is correct at any N.

---

## The density profile, and what actually falls out (§13)

**Falls out** — the profile's SHAPE, all three forced by self-similarity
(`r(e) = e/κ`, the only scale-free choice) plus isotropy, with the foveal radius
pinned at the one-pixel sampling limit:
geometric ring spacing `e_{n+1} = e_n(1 + 2/κ)`; constant per-ring count
`N_θ = πκ`; `r ∝ e`. Alternate rings are staggered by a half-step (the only
offset treating both neighbours alike) so the layout acquires no preferred axis.

**Does NOT fall out** — the SCALE, κ. §2.1 of the prereg records this as a
correction to my own pre-registration, which had claimed κ was "consumed by the
matched-sample-count constraint". That was **wrong by arithmetic**: the square
arm is a complete pixel partition (16 × 36 = 576 = 24²), so matching sample count
means one blob per pixel — the uniform sampling the rung exists to remove.
Coverage cannot pin κ either (radial and tangential spacing touch by construction
at every κ). **κ is the blob arm's resolution parameter exactly as
`(GRID, REGION)` is the square arm's**: declared, swept, matched. Claiming
otherwise would be a magic number wearing a derivation.

**No cost table entered the derivation.** The coordinator supplied measured
scaling (scale ≈ n_regions^1.7, grain ≈ cells^0.4, C1 only, unconfirmed on C2).
It is consistent with spending resolution centrally and coarseness peripherally,
and it is recorded here separately and after the fact. The profile would be
unchanged had it said the opposite.

---

## What I got wrong, and what caught it

1. **My own pre-registration's κ claim was wrong by arithmetic** (§2.1).
   Committed, then corrected in a follow-up commit rather than silently edited.
2. **My first proto harness did not reproduce the baseline** — grid=24,
   consecutive frames, k∈{4,16}, giving 1–2 protos where the incumbent had 0.
   The incumbent runs **grid=16, frames spread 0…149, k∈{2,4,8,16}**, and the
   "0 on 7/7" is the **k=16 row only**. Caught by checking reproduction before
   drawing any comparison; no number from that run is reported.
3. **A silent-absence defect in my own arm.** The blob border was flagged by a
   threshold, `hypot(dy,dx) + r ≥ R`, which at κ ∈ {1,2,3} matched **nothing**.
   With no frame cell the `bg` flood has no seed, every blob keeps its initial
   `bg=0`, every component reads as enclosed, and the mint fires **vacuously** —
   producing exactly 1 proto on every frame of both corpora at every k. That is
   what a layout artifact looks like when mistaken for a percept, and it briefly
   read as H3 succeeding. Fixed structurally (the outermost ring **is** the
   border) and **asserted** — `blob_field` now raises if zero blobs are flagged,
   because the whole failure mode is that an unseeded field looks like a normal
   one.
4. **My gate diagnostic contradicted the rule it measured.** It counted a
   component with *zero* ground neighbours as refused, while the rule's
   `Not Exists two ground cells with different glabel` is vacuously TRUE there —
   so it reported 43 refusals beside 43 minted protos. Fixed; the vacuous case
   is now counted and reported separately (`n_vacuously_single`).
5. **I hit the `pgrep`-self-match footgun my own brief warned about.** To wait
   for the oracle I ran `until ! ps aux | grep -q "[r]ung7_vision_bench"; do
   sleep 5; done` — and the shell running that loop has
   `rung7_vision_bench` **in its own command line**, so it matched itself and
   would never have exited. It reported "still running" for a job that had
   already finished. The `[r]` bracket trick defeats `grep` matching itself but
   not the *wrapper* matching itself. Caught by inspecting `ps` output directly
   instead of trusting the count; the oracle result was read from its own output
   file and exit status.
6. **The branch name is not the one specified.** I am on
   `worktree-agent-a38f471c69575cea7`, not `gamma-substrate/blob-native` — the
   seventh consecutive rung under an auto-generated name.

## Bounds

- Blob counts **7–64**; κ ∈ {1,2,3,4} (proto) and {2, 4, 6.75} (cost/recognition).
- Fields **GRID=16** (proto, matched to the incumbent) and **GRID=24** (cost).
- **6 frames × 2 corpora** (cost), **7 frames × 2 corpora × 4 k** (proto). Small
  n: the cost ratio (9×) and the floor collapse (0.02–0.07 margin) are both far
  larger than the between-frame spread, but no CI is claimed, and the powered-gate
  standing rule applies to anything finer.
- One field size for the cost claim — **the 9× is not shown to hold as GRID
  scales**, and the concurrent rung's n^1.7 scaling means it should be re-measured
  before being carried anywhere.
- `hamming` only for the recognition claim. Under `ncc` the fixed-length `Dot`
  cannot express variable-length blob groups at all.
- BSDS300 absent; no BSDS claim.
- **Not done:** the proto and cost arms use different field sizes, so H3 and
  H1/H2 are not the same configuration; a matched-information comparison (equal
  arrangement content, unequal sample count) was not run and is the obvious
  next lever on H2.
