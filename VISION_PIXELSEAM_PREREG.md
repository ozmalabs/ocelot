# THE PIXEL SEAM FOR `TimeInfer` — PRE-REGISTRATION

*Written and committed BEFORE any confirmatory number (PROTOCOL §3). Seeds
**104000–104999**. Successor to `VISION_TIMEPHI_RESULTS.md` (93000–93999) and
`VISION_GAPABDUCE_RESULTS.md` (97000–97999).*

---

## §0 THE BOUND BEING REMOVED

The timephi rung's A1:

> **`TimeInfer` CANNOT CONSUME A BOUNDED PIXEL FIELD AT ALL.** Every positive is
> **conditional on a figure/ground split the rung supplied.**

Until a pixel seam exists, none of the motion line reaches video. The identity
seam's recorded lesson (*"it was never broken — nobody had handed it pixels"*)
was checked by the timephi rung and **declared NOT to transfer**: `TimeInfer` is
a SHAPE-level operator. So this is a build, not a wiring job, and this rung's
first job is to **establish what the operator actually requires** before
asserting anything about whether a seam is possible.

**This rung adds NO Rust and NO seed.** It is a measurement of an existing
operator against real pixels.

---

## §1 WHAT THE OPERATOR REQUIRES — READ FROM SOURCE, TO BE VERIFIED BY MEASUREMENT

Read from `runners/dsl/src/shape_decode.rs` (`eval_time_infer` +
`infer_translate_offset`) at engine `9931e144d19b`. **A source reading is a
CLAIM, not a fact — this arc has recorded FOUR comment-vs-engine divergences in
a week, one of them authored by the rung warning about it.** Every requirement
below is therefore RE-DERIVED INDEPENDENTLY IN THE RUNNER and compared against
the Term's verdict; a disagreement is itself a finding.

| | requirement | source site |
|---|---|---|
| **R1** | at least 2 frames | `frames.len() < 2` |
| **R2** | `coord_dims` non-empty (the codebook declares `coord:` slots) | `coord_dims.is_empty()` |
| **R3** | no frame empty | `frames.iter().any(\|f\| f.is_empty())` |
| **R4** | **equal cardinality** across frames | `f0.len() != f1.len()`; `frames_equal` |
| **R5** | one **uniform integer offset** on the coord slots, under a sort-then-pair | `infer_translate_offset`'s verify loop |
| **R6** | **every non-coord slot BYTE-IDENTICAL** between paired cells | same loop, `cmp_value(&ta[k], &tb[k]) != Equal` |
| **R7** | the offset is **non-zero** (identity excluded) | `if off.iter().all(\|&x\| x == 0) { None }` |

**R4+R5+R6 jointly say: the FRAME ITSELF — its support AND its content — must be
a rigid translate.** A camera's fixed boundary is exactly what violates that:
the support does not move with the scene.

**R6 is the clause this rung is really about.** Real pixels are never
byte-identical across frames. The only lever that can make them so is
**quantization coarseness `q`** — and coarsening `q` also destroys the change
you are trying to see, until R7 refuses the sequence as an identity.

> **THE SQUEEZE, stated as the rung's question:** *is there a quantization
> coarseness at which real video frames are BOTH still photometrically LIVE and
> ALSO byte-identical enough to satisfy R6?* Too fine ⇒ R6 fails. Too coarse ⇒
> R7 refuses "no motion". **Is the operating window non-empty?**

---

## §2 CORPUS, DECLARED AND DETERMINISTIC

- **REAL VIDEO.** Jellyfin, `episode_index=0` — the same **positional**
  (not content) pick the video-probe rung used; catalogue and episode counts are
  recorded in the artifact. 24 consecutive decoded frames at each of a FIXED
  start grid `START_GRID = [60, 180, 300, 420, 540, 660, 780, 900]` seconds,
  area-downsampled to 48×48 grey 0–255. Cached to `results/gapseam_starts.npz`.
  **No start time is selected for its motion content**; the grid is an axis and
  all eight are reported.
- **Whole-field arms** use the fixed top-left 24×24 crop.
- **Patch arms** use an 8×8 patch at a seeded location, pasted into a 24×48
  field at columns `4 + k·S`, `S = 4`, `k ∈ {0,1,2}` — all three positions
  strictly inside the field.

**Quantization:** `quant(x, q) = (int(clip(x,0,255)) * q) // 256`, levels
`0 .. q−1`. `Q_GRID = [2, 4, 8, 16, 32, 64, 128, 256]` — **an axis, iterated,
never compared against.**

**Figure/ground split (where used):** cells whose quantized luminance differs
from **the frame's OWN modal quantized luminance**. Data-derived, no constant —
and **declared as SUPPLIED STRUCTURE**, exactly as its two predecessors declared
it.

---

## §3 ARMS

**A0 — THE WIRING CONTROL, RUN FIRST AND ABORTING.** *The phi rung nearly
published a perfect fake null (`has_region` silently refused ⇒ priors always
empty ⇒ the same verdict at every input). The timephi rung's own trap gate was
INERT.*

| control | required |
|---|---|
| **A0-POS** synthetic moving dot, N=3, S=4 | `time_inferred`, `kind=translate`, `offset=(0,4)` |
| **A0-NEG** synthetic stationary dot | `time_none` |
| **A0-PROBE** codebook liveness | a **paired in-process POSITIVE probe** on a KNOWN orbit in the SAME booted substrate, `coord_dims` non-empty. **`coord_dims` is NEVER read off a measured call** — the `unexplained()` constructor hardcodes it empty, so it is an OUTPUT of the verdict and made 167 false accusations for my predecessor. |

A failed wiring control **aborts the run** (`return 3`); an engine divergence
aborts (`return 2`). Neither warns.

**THE ENCODING LADDER.** N = 3 throughout. Every condition also gets an
**independent requirement diagnosis** (R3/R4/R5/R6/R7, first failure) computed
in the runner from the encoded frames — *a diagnostic must not be computed by
the component it checks.*

| arm | pixels | motion | support | `val` slot |
|---|---|---|---|---|
| **E0 RAW-FIELD** | real video, 24×24 | whatever the scene does | every cell | yes |
| **E1 SPARSE** | real video, 24×24 | whatever the scene does | non-modal cells | yes |
| **E2 RIGID-ROLL** | real video frame, 24×24 | **exact** toroidal roll by S | every cell | yes |
| **E3 RIGID-PATCH-STATIC** | real texture, ONE frame | exact paste-translate | non-modal cells | yes |
| **E4t RIGID-PATCH-REAL** | real texture, THREE consecutive frames | exact paste-translate | non-modal cells | yes |
| **E4g … GT support** | as E4t | as E4t | **the patch rectangle** (ground truth) | yes |
| **E4s … GT support, no val** | as E4t | as E4t | the patch rectangle | **no** |

E0/E1/E2: 8 starts × 8 q. E3/E4t/E4g/E4s: `N_DRAW` seeded draws × 8 q,
**PAIRED** — the same draw index gives the same (start, t0, r0, c0) in all four
arms, so the arms differ only in the encoding.

**LIVENESS STRATIFICATION (§1 clause 4 — the arms must be alive).** For every
condition, `live(q)` = the QUANTIZED content is not identical across the three
frames (exact array inequality; no tolerance). **Every rate is reported
separately for live and dead conditions.** A cell with fewer than `MIN_LIVE`
live conditions is reported **UNDERPOWERED and carries no weight** — a
threshold on POWER, declared in advance, never on an outcome.

*The pilot on burned seeds (93000/93100 blocks) found E4t explained at 4/4
sampled q with **0/4 live** — i.e. the naive arm was DEAD, and would have been
reported as a success of the seam. That is why the stratification exists.*

---

## §4 PREDICTIONS, STATED IN ADVANCE (§3 clause 7)

| | prediction | weight |
|---|---|---|
| **P0** | **E0 refuses** at every (start, q) | LOW — replicates A1 on real pixels |
| **P1** | **E1 refuses** at every (start, q) | LOW |
| **P2** | **E2 refuses** at every (start, q)** — exact rigid CONTENT motion is not enough on a bounded field.** Proviso: a toroidal roll preserves cardinality EXACTLY, so R4 holds and **R5 must be the diagnosed failure**, on the wrapped cells. | MEDIUM — the proviso is the risky part |
| **P3** | **E3 explains with `offset == (0,4)` at every q and every draw.** THE SEAM POSITIVE CONTROL. | GATE — if this fails the rung is uninterpretable and stops |
| **P4** | **H1: `P(E4t explained \| live) == 0` at every q, while `P(E4t explained \| dead) == 1`.** *The seam succeeds exactly where it sees nothing changing.* | **HIGH — the rung's evidential weight** |
| **P5** | E4g explains wherever E4t does. **If E4g explains where E4t does NOT, the deficit is R4 (support instability), not R6 (appearance).** | HIGH |
| **P6** | **E4s explains at every q and every draw** (ground-truth support, no `val` slot ⇒ R6 vacuous, geometry rigid by construction). **If this fails, my source reading of the operator is WRONG** and that is the finding. | HIGH |
| **P7** | the live fraction is **monotone non-decreasing in q** | LOW |

**Two-sided on P4:** the alternative is that some q admits **live AND
explained** — which would mean real photometric change survives quantization
*rigidly*, and the seam WORKS. I do not predict it, and I will report it if it
happens.

---

## §5 DECISION RULE — INCLUDING WHAT A NULL MEANS

*Registered in advance, because the brief requires it: "TimeInfer still can't
take pixels" is three different statements and they license different
successors.*

| observed | the null is ABOUT | licensed successor |
|---|---|---|
| **P3 fails** (E3 refuses) | **my SEAM, or my source reading** — a FAKE NULL | stop; diagnose; nothing else is interpretable |
| **P6 fails** (E4s refuses) | **the operator's requirements are not what §1 says** | re-derive R1–R7 from the engine; the source reading is the bug |
| P3 ✅, P6 ✅, **no q is both live and explained** | **THE REPRESENTATION `TimeInfer` DEMANDS.** R6 (exact appearance byte-identity) is unsatisfiable on real photometry; the rigidity CORE is sound | an **appearance-tolerant pairing** in Rust (drop / relax the non-coord slot comparison), or carry appearance outside the signature |
| P3 ✅, P6 ✅, **E4g explains where E4t does not** | **THE LAYER THAT SUPPLIES THE SUPPORT.** The threshold split's cardinality is unstable under photometry | upstream: a support that does not re-decide membership per frame |
| **some q is both live and explained** | nothing — **the seam WORKS** | report q, its cost in support degeneracy, and wire it |

**And the scope statement that is registered, not discovered:** E0/E1 refusing
is **NOT** a deficit of `TimeInfer`. A real scene is not a rigid translate of
itself. Their value is entirely in the DIAGNOSIS (which requirement fails, and
whether the refusal came **after a full search** or **at a guard** — a gate that
refuses at a guard before searching is a §13 negative, not a result).

---

## §6 n, FIXED IN ADVANCE

Pilot on **already-burned** seeds (93000, 93100 — the timephi block), reported
in §3: E3 5/5 explained; E4t 4/4 explained at 0/4 live; E2 refused with
`checked = 83520` (search RAN); E0/E1 refused with `checked = 0` (identity, R7).

The statistic is a **proportion**. `N_DRAW = 200` paired draws. By the rule of
three, an observed 0/200 bounds the true rate below **1.5%** at 95%; that is the
resolution the P4/P6 claims are made at, and it is fixed here. `MIN_LIVE = 3`
(a power floor, declared before the run; cells below it are reported as
UNDERPOWERED, never as a result).

**Seeds: 104000–104199**, one per draw index, each producing
`(start, t0, r0, c0)`. **Materialised ONCE from a single sink bound to an
explicit `range`** so `scripts/seed_audit.py` can RESOLVE every seed statically
— my predecessor's first audit left an unknown sink and *"would have let me
publish an accounting that had verified nothing."* Seeds 104200–104999 remain
unburned.

### §3 clause 8 — VERBATIM `check_claim` OUTPUT

```
SEED CLAIM 104000-104999: CLEAN -- no collision DETECTED.
  Scope: 807 files with seed sinks; 497 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

**497 unresolved sink sites tree-wide.** The claim is CLEAN *given that
silence*, and the silence is priced here rather than omitted.

---

## §7 BOUNDS THIS RUNG INHERITS — TO BE MEASURED, NOT QUOTED

- **The motion sensor** (`domains.motion_group_world.vector_field`): 10.67%
  [10.60, 10.75] confidently-wrong at the operating point, >99% confidently
  wrong beyond 1.5× aperture, and **indistinguishable downstream from a true
  vector**. **NO ARM IN THIS RUNG CONSUMES IT** — every motion in every arm is
  either ground-truth-by-construction or the scene's own. `scripts/motion_sensor_gate.py`
  is run and its verdict reported as an inherited fact, not re-derived.
- **The proto-object / component layer**: median member ONE cell, max 66 on a
  324-cell tile. **NO ARM CONSUMES IT EITHER.** The component-size distribution
  on THIS rung's own frames is measured and reported, so the statement *"the
  object layer cannot currently supply the support E4g was handed"* is made with
  numbers from these frames rather than borrowed ones.
- A concurrent rung is working upstream of the object layer. Nothing here
  assumes its outcome.

---

## §8 §13 — WHERE A NUMBER COULD SNEAK IN

- Every verdict is an **exact equality** on a logical or integer quantity
  (`status == 'time_inferred'`, `offset == (0, S)`, `checked == 0`,
  a count `== 0`). **No ordering against a non-zero literal decides anything.**
- `q` and `S` and `START_GRID` are **AXES — iterated, never compared against**.
- The figure split uses the frame's **own modal value**: data-derived, no
  constant, and it is the SAME split the two predecessor rungs used.
- **Liveness is an exact array inequality.** There is no tolerance in it and
  nowhere to put one.
- `MIN_LIVE = 3` is a **POWER floor on how many observations a cell must have
  before it is reported at all** — declared in advance, applied identically to
  every cell, and never compared against an outcome.
- Declared residuals, **CONFIGURATION and nothing stronger** (bound once, never
  a verdict threshold): `DOT = 4`, `PATCH = 8`, `FIELD_H/W`, `CROP = 24`,
  `S = 4`, `BG`, `FG`, `ROW`, and `max_b = 8` (a compute cap on the linear
  enumeration, inherited unchanged from the phi/timephi/gapabduce rungs).
- Gated by `tests/test_pixelseam_ast_migrated.py` — a Python **AST walk**, never
  a substring selector; verdict functions bound as `ast.FunctionDef` nodes by
  name **read from the runner's OWN `VERDICTS` tuple**; subscript indices
  **PRUNED by explicit recursive descent** (`ast.walk` CANNOT prune); module
  level name bindings **resolved to their literals**; and
  **POSITIVE-CONTROLLED** by injecting both an inline and a named threshold and
  requiring the gate to turn RED, with the unmodified source asserted GREEN in
  the same test.

---

## §9 §9 — DEFAULTS

**No Rust. No seed. No default moved.** Oracle `scripts/rung7_vision_bench.sh`
is recorded before and after and must be unchanged (**222 passed / 0 failed**,
`data/` symlinked — the with-corpus case).

---

## §10 WHAT THIS CANNOT SHOW (§8)

- Nothing about human phi, and no human data.
- **One shape of motion (pure translation), one N (=3), one S (=4), one dot /
  patch size, horizontal only.** The predecessors' scope limits are inherited.
- **One video source, one episode, 8 start times.** A cartoon at 48×48 is not a
  claim about all video, and the corpus's own motion statistics are reported so
  the reader can price that.
- Whether an appearance-tolerant `TimeInfer` would be CORRECT — only whether the
  current one's requirement is satisfiable on real pixels.
- **No timing claim of any kind** beyond a recorded wall-clock cost, and the
  machine's concurrent load is recorded with it (the video-probe rung's
  correction: *a contended timing is a rumour in the same way a stale binary is*).
