# VIDEO PROBE, RE-RUN — did the wall FALL, or did it MOVE?

*Pre-registration. Written and committed BEFORE any measurement (PROTOCOL §3).*

**Base SHA:** `c6c022f8fc2ab212b130ad3e34a761af6a20aaee`
**Branch:** `gamma-substrate/video-probe-rerun`
**Engine:** `4d451d8f6ed0` (sha256[:12]) / md5 `ab01c23ed643a9a406120c08be5fa4b3`
`@ .../agent-a0c149cb0a125ada7/.../runners/dsl/python/substrate_rs/_native.abi3.so`
— **built in THIS worktree** by `scripts/engine_build.sh` before this prereg was
written. **This rung ADDS NO RUST**; the build is nonetheless this tree's own, so
no number can be attributed to a binary I did not produce.

> **A PROVENANCE FACT WORTH RECORDING NOW, BEFORE IT CAN BE USED:** this build's
> md5 is **byte-identical to `VISION_BATCH_APPLY_RESULTS.md`'s `after` engine**
> (`4d451d8f6ed0` / `ab01c23ed643a9a406120c08be5fa4b3`). That is a *reproducible
> build* of the same Rust source — and it establishes, before any measurement,
> that **the Rust source has not moved since batch-apply**. Of the seven
> engine-touching commits named in the brief, everything after batch-apply
> (locality-index) added no Rust. This CONSTRAINS attribution (§A7) and is
> recorded here so it cannot be discovered later and presented as a finding.

**Machine:** AMD Ryzen 5 9600X, 12 logical cores. Load at prereg time
**1.15 / 1.27 / 1.27**. A `vllm-xpu` podman container started at 18:44 and is a
**standing system service on this box, not another agent** — it is named here in
advance so that its presence in any `ps` during a timing window is a known
constant rather than a discovery.
**Seed block claimed:** **65000–65999** (verified free: the ledger's highest
allocated block is 64000–64999; `65000` appears in no `*_PREREG.md` and nowhere
in `VISION_PROTOCOL.md`). **I am running SOLO — no concurrent rung** (the
supervisor states this; §11's serialisation caveat on the 54000 collision is
therefore satisfied by construction, not by a ledger read).

---

## 0. WHAT THIS RUNG IS

`VISION_VIDEO_PROBE_RESULTS.md` (merged `40318951`) produced this arc's failure
map. Its first hard blocker was **SCALE**: exponent **1.887** (r² 0.997),
real-time affording **18×18**, one 1080p frame extrapolating to **164 hours**.

Since then `VISION_BATCH_APPLY_RESULTS.md` (merged `81772f82`) took the drive
path's counted-op exponent **1.9549 → 0.9930** with byte-identity held over
235,200 values.

**This rung re-runs the probe to produce a directly comparable failure map, and
answers one question: did the wall FALL, or did it MOVE?**

**It is a MEASUREMENT rung.** It adds no Rust, no seed, no rule, no default. Its
deliverable is the *fidelity of the comparison*, not a nicer end state. **No
stage will be patched to reach one.** If most stages are still broken after a
155× op reduction, **that is the finding** (§7).

---

## 1. THE PINNED ORIGINALS — every delta below is against these

Copied from `VISION_VIDEO_PROBE_RESULTS.md` **before** re-measuring, so the
comparison cannot drift:

| stage | original value | original verdict |
|---|---|---|
| S1 retina | **46.64%** fire (cartoon), sd 6.85 / min 35.76 / max 64.93 | INDETERMINATE (25–50%) |
| S1 / D1 | **80.30%** fire (BSDS300) | corpus effect, not instrument |
| S2 | ρ=**0.2998**, CV=**0.2197**, n=**149**, cost mean **102.84 ms** | INDETERMINATE — **and contaminated by concurrent load** |
| S2 / D4 | ρ mean 0.351 ± 0.056 over 4 reps; clean-drift estimate **ρ≈0.18–0.26** | sign robust, magnitude not |
| S3 | **0 protos on 7/7** frames at k=16; 4/7 at k=8; reference components 10→128 | FAILS — k-unstable (ratio 4.0) |
| S4 | **6** ProtoObject files ∩ **60** identity files = **0** | STRUCTURAL ABSENCE |
| S5 | exponent **1.887** (r² 0.9971); 331.61 ms/tick at grid 32 | CONFIRMED quadratic |

---

## 2. CORPUS — IDENTICAL, no substitution

Same as the original, and this is the whole point of the rung:

| source | what |
|---|---|
| **Jellyfin** | *Middlemost Post* S2E1, episode id `08630d4b7b215c469df19b9c42d7b617`, **150 frames**, every 2nd decoded frame from **t=300 s**, area-averaged to **24×24** grey 0–255 |
| **BSDS300** | `data/vision_curriculum/BSDS300` via the §10.2 symlink; 12 centre-crops |

Selection is by **fixed positional index** (sorted series, sorted episodes) —
deterministic, no content decision, no seed drawn.

**If the episode id that comes back is not `08630d4b7b215c469df19b9c42d7b617`,
the corpus has moved and every S1/S2/S3/S5 delta is UNINTERPRETABLE as a delta.**
That is declared now and will be reported either way, never quietly absorbed.

**Scope (§8), unchanged and still binding:** ONE episode of ONE broadcast cartoon
series plus 12 BSDS crops. Not a survey of video.

---

## 3. ARMS

### A1–A5 — THE FIVE ORIGINAL STAGES, RE-RUN BY THE ORIGINAL INSTRUMENT

**Selector:** `scripts/video_probe_measure.py`, **UNCHANGED, byte-identical**, run
as a subprocess at its committed defaults (`--grid 24 --n-frames 150 --every 2
--start-s 300 --episode-index 0 --s3-grid 16 --s5-sizes 12,16,24,32`), writing
`results/video_probe_rerun.json`.

**Running the original instrument unmodified is the comparability guarantee.**
Any edit to it — even a "harmless" one — would make every delta a delta of two
things. If the script needs a change to run at all, that is reported as a finding
and the changed lines are enumerated; it is not made silently.

**Every stage keeps its ORIGINAL pre-registered decision rule verbatim**
(S1 dense>50% / sparse<25%; S2 FLAT iff ρ<0.3 AND CV<0.10, TRACKS iff ρ>0.5;
S3 `n_proto/n_cells`<0.05 AND k-ratio<3.0; S4 dataflow bridge; S5 exponent).
**No metric surgery (§5).** The rules are the originals *because* they are the
originals, not because I would choose them today.

**Every stage keeps its ORIGINAL positive controls**, and a stage whose control
fails is reported **UNINTERPRETABLE**, never as a null (§1 cl.4).

### A6 — THE DIAGNOSTICS, RE-RUN

**Selector:** `scripts/video_probe_diagnose.py`, **UNCHANGED**, defaults,
writing `results/video_probe_diagnose_rerun.json`. Supplies D1 (the BSDS 80.30%
comparison), D2 (ignite stratification), D3 (the 7-frames-spread S3 profile that
produced *0 protos on 7/7 at k=16*), D4 (ρ replication **with its drift
control**).

### A7 — S2 GETS THE CLEAN RUN IT NEVER HAD

The original's CV was the **only** half blocking a FLAT verdict (ρ=0.2998 cleared
its half by 0.0002; CV=0.2197 missed its by 2.2×), and its author correctly
declined to re-decide on contaminated data.

**This arm changes NOTHING about the measure or the rule.** It changes only the
machine state:

- `ps` + `/proc/loadavg` captured **immediately before and immediately after**
  the S2 window, and **reported alongside the number** — not as a caveat, as a
  field. A timing whose load state is absent is a rumour (§0.1 corollary).
- No other arm of this rung runs concurrently with the S2 window. The regression
  bench runs **after**, in its own step, never overlapping.
- The drift control `ρ(frame_index, cost)` is reported **from the start**, as the
  original's §5 recommendation 3 required — not fetched afterwards to explain a
  number.

**The verdict is whatever the unchanged rule returns.** **FLAT is a legitimate
outcome and will not be argued away**; nor will it be reached by rounding
(ρ=0.2998 is *below* 0.3 and the original said so without claiming it — the same
discipline applies here in whichever direction the number lands).

### A8 — **NEW ARM: THE sd/IDENTITY LAYER'S SCALE**

`VISION_SCALE_SPLIT_RESULTS.md`, `VISION_BATCH_APPLY_RESULTS.md` and
`VISION_LOCALITY_INDEX_RESULTS.md` **each** carry the identical bound: *"ONE
workload (the retina drive; the sd/identity layer is NOT measured)."* Three rungs
have now declared the same blind spot. This arm measures it.

**Workload.** The `§2.4b` seam probe, taken as given: a real Jellyfin frame
(same episode, same `start_s=300`, frame 0), quantized at **k=2**, hand-encoded
as `["cell", r, c, "v<k>"]` tuples for non-zero cells only, its own signature
**held** in the codebook as a `ShapeSignature`, presented as an `Observation`,
driven to fixpoint by `native.run_rules()`. **Literal self-identity — the easiest
recognition that exists.** If the layer is superlinear *here*, it is superlinear
everywhere above here.

**Sweep.** Frame side ∈ **{4, 6, 8, 10, 12, 14, 16}**. **N is the number of cells
actually emitted**, recorded per point, never assumed from the side length.

**Statistic.** **Counted operations** from `Substrate.scale_audit_snapshot()` —
load-independent, reproducible to the integer — fitted log–log against N.
Wall-clock is recorded **once, with its load state, and enters no share and no
exponent** (the `62fadd1a` precedent: two verdict-identical runs 1.66× apart on
load alone).

**GATES, declared now, run BEFORE any number is read** (this arc has caught
**eleven inert instruments**, and the scale-split rung's own counter module was
**half-inert on its first build**):

| gate | requirement |
|---|---|
| **G1 zero-when-off** | with `scale_audit_set_enabled(False)`, every counter reads **0** on a LIVE sd workload |
| **G2 liveness** | with the audit on, counted ops **> 0** AND the observation reaches `recognized` / `recognized_transformed` at **every** point. *A frozen or erroring loop is infinitely fast and scales beautifully — that is the exact failure this arc keeps catching.* |
| **G3 determinism** | two independent runs **byte-identical** on every counter |
| **G4 N varies** | the emitted-cell count must span **≥ 4×** across the sweep, or the fit is meaningless and the arm is UNINTERPRETABLE |

**If any gate fails, no exponent is claimed and the arm is reported
UNINTERPRETABLE — not as a null.**

**Decision rule, fixed now.** Let `e_sd` be this arm's counted-op exponent and
`e_drive` the drive path's, **measured in the same session on the same engine**
(A9), not quoted from a prior rung:

- **`e_sd ≥ e_drive + 0.3`** ⇒ **the sd/identity layer IS the new binding term.
  The wall MOVED.**
- **`e_sd ≤ e_drive + 0.1`** ⇒ **it is NOT binding. The wall FELL** and the next
  blocker is elsewhere.
- otherwise ⇒ **INDETERMINATE**, reported as such.

**Reported regardless of which branch fires** — because the locality-index rung's
standing lesson is that *neither a share nor an exponent decides alone, the PAIR
does*: the sd:drive counted-op ratio at the largest measured N, and the projected
ops at a common target N. **A term can be asymptotically innocent and still
dominate at the sizes that matter, and the converse.** Both go in the results.

### A9 — ATTRIBUTION, ISOLATED WHERE POSSIBLE AND BOUNDED WHERE NOT

**The brief's warning is correct and I am not permitted to attribute the whole
delta to batch-apply.** Seven engine-touching commits landed. But the isolation
is cheap here, so it will be done rather than hedged:

On the **SAME engine** (`4d451d8f6ed0`), the video probe's **S5 real-frame scale
arm** is run **twice**:

1. **batch LIVE** — the seed exactly as committed (`vision_change` v1.1.0);
2. **batch STRIPPED** — `wave_world._CHANGE_SEED` pointed at a temp copy of
   `seeds/vision_change.json` with the `batch` key removed from every rule.
   **This is the batch-apply rung's own `off_new` control mechanism, reused
   verbatim: the flag is graph DATA, so the control varies the data, not the
   code path.**

**What this does and does not establish, declared now:**

- **(1) minus (2) is batch-apply's contribution, ISOLATED** — one engine, one
  corpus, one session, one machine state; the only difference is five booleans in
  a seed.
- **(2) versus the original 1.887 is AGGREGATE** — it carries the other six
  commits, plus any machine, PyAV, numpy or corpus difference between July 2026
  and now. **It will be reported as aggregate and the confound named**, never
  decomposed further by argument.
- The engine md5 identity recorded in the header already bounds this: **the Rust
  has not moved since batch-apply**, so the residual confound is
  seed/adapter/machine, not engine.

`e_drive` for A8's decision rule is taken from **arm (1)**, the committed
configuration.

---

## 4. PREDICTIONS — stated in advance, in the knowledge they may be wrong

Made **before** any measurement. I have read the batch-apply results but not
re-run anything.

| # | arm | prediction |
|---|---|---|
| P1 | S1 | **unchanged to within rounding** — 46.6% cartoon, 80.3% BSDS. Batch-apply held byte-identity; S1 is deterministic. A *moved* S1 would mean byte-identity did not hold on this path and is the more interesting result. |
| P2 | S2 ρ/CV | cost mean falls **hard** (≥5×, from 102.84 ms). ρ falls **below** its original 0.2998 — batch-apply removed a re-derivation loop whose call count tracked the number of firing (i.e. content-dependent) bindings, so the mechanism most likely to have produced the weak positive ρ is *gone*. **ρ 0.05–0.30.** CV I genuinely cannot call: a smaller absolute cost is relatively noisier, so **CV 0.10–0.30**, and I predict the FLAT verdict is **still blocked by CV**, i.e. **INDETERMINATE again.** |
| P3 | S3 | **unchanged — 0 protos on 7/7 at k=16.** Border-ownership loads `vision_border_ownership`, not `vision_change`; no batched rule is in its path. **The 155× op reduction should not have touched this stage at all, and if it has, my model of what batching did is wrong.** |
| P4 | S4 | **still 0 bridges.** Nothing in the intervening seven commits built a segmenter. File counts may drift upward as the tree grew. |
| P5 | S5 | exponent **0.9–1.3** (from 1.887); grid-32 ms/tick **< 60** (from 331.61). |
| P6 | A8 sd | **`e_sd` ≥ 1.5, and the sd/identity layer becomes the binding term. I predict THE WALL MOVED, not fell.** Reasoning stated so it can be judged: `ShapeDecode` decodes an N-cell observation against a codebook whose held entry is also N cells, and the sd loop re-decodes on `codebook_epoch` bumps — a shape with an N×N flavour and a fixpoint on top of it. |
| P7 | A9 | batch-STRIPPED reproduces the original within fit error (**1.75–2.00**); batch-LIVE ≈1.0. **Attribution to batch-apply is essentially total.** |

**P6 is the prediction this rung exists to test, and P2 is the one I most expect
to get wrong.**

---

## 5. WHAT WOULD MAKE THIS RUNG'S HEADLINE FALSE

- **The wall FELL** if S5's exponent falls to ~1 **and** A8's `e_sd` fails its
  `+0.3` bar **and** no other stage's cost profile is superlinear. Then the
  correct headline is "the first blocker is now representational, not
  arithmetic", and the new first blocker is S3 or S4.
- **The wall MOVED** if A8 clears its bar. Then the 155× is real *and* the
  ceiling did not rise proportionally, and **saying so plainly is this rung's
  most important output**.
- **The wall did BOTH** — fell in the drive, moved to sd — is the outcome I
  predict, and it is not a hedge: the two clauses are separately falsifiable by
  the rules above.

---

## 6. ANALYSIS RULES BINDING THIS RUNG

- **Unit of analysis:** the FRAME for S2, the (frame, k) cell for S3, the
  **sweep point** for A8/A9 (§4).
- **Exactly the arms above.** No sweep beyond the declared k-sweep, grid list and
  side list. **No re-runs to get a better number** — a re-run for a *declared*
  determinism gate (G3) is not that, and is the only re-run permitted.
- **Every number carries its engine hash, its commit, its selector, AND — new
  since the original — its machine state** (§10, §12, §0.1 corollary).
- **No metric surgery (§5).** A measure that looks wrong after it fails is a new
  pre-registration.
- **Negatives are the result (§7).** "Still broken after 155×" is a finding.
- **§13:** no magic numbers. A8's N is *read from the emitted signature*, not set;
  `e_drive` is *measured in-session*, not quoted.
- **§9:** nothing ships on by default; no default is touched. A9's batch-off arm
  is a temp file the process throws away, never a repo edit.

## 7. THE REGRESSION ORACLE (must be unmoved)

- `bash scripts/rung7_vision_bench.sh` → **200 passed, exit 0** with `data/`
  symlinked (**190/10 without** — which condition applies **will be recorded**,
  per §10.2's rule that the number is quoted with its condition);
- the sd orbit law `{2:1, 3:2, 4:2, 6:2, 12:4}` unmoved;
- **run as its OWN step, exit code captured, never piped into `tail` inside an
  `&&`**, and **never overlapping the A7 timing window**.

## 8. PROVENANCE SELF-AUDIT

A test pins **BOTH endpoints** — `git diff BASE_SHA RUNG_SHA` — **never `HEAD`,
never the working tree**. `tests/test_provenance_endpoint_guard_migrated.py`
fails any provenance assertion whose range ends at `HEAD`, and this defect has
occurred **four times** in this arc. The gate asserts this rung's commit range
adds no Rust, adds/edits no seed, and touches only files it owns, and is
**positive-controlled red-then-green** — *a gate that has only ever been seen to
pass is not a gate that has been tested.*
