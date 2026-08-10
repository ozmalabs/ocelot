# VISION — APPERCEPTIVE / ASSOCIATIVE AGNOSIA (FRONTIER T9) — PRE-REGISTRATION

*Written and COMMITTED before the confirmatory run (§3). Failure-mode gate **#1** of
`VISION_VENTRAL_GROUNDING.md` — the FORM↔RECOGNITION seam, "the sharpest architectural
tell". The classic double dissociation: ablate the IDENTITY layer ⇒ the percept still
FORMS (the "copy" survives) but is not NAMED (**associative** agnosia); corrupt the
RENDER ⇒ the percept cannot form, so copy AND naming both fail (**apperceptive**
agnosia). Two ablations hitting DIFFERENT stages, with the COPY test discriminating,
is what proves the seam is real rather than one blob.*

**Seeds: 48000–48999** (noise floor 48000–48099). Allocated from the ledger's clean
range (`12000–48999 untouched` as of the T10 entry). Base `main` HEAD **b1c736a0**
(`git merge-base --is-ancestor b1c736a0 HEAD` = true, §11). Worktree
`.claude/worktrees/agent-a65a0ebcc1313b14b`.

---

## STEP 1 — AUDIT (§12.4, file:line): can these be clean FLAGS, and are COPY and NAME
## independently readable?

**VERDICT: YES for both, and the two stages live in TWO SEPARATE SEEDS with no
cross-read — which is exactly the structural precondition the dissociation tests.**

**The RENDER stage (percept formation) — `seeds/vision_ground.json` v1.0.0.**
`gr_label` (`:rules[0]`) marks a SENSED cell as a contour along its own axis
(constant along one axis, differs along the perpendicular — exact equality, no magic
number); `gr_fill` (`:rules[1]`) is the unified grounding fill that CONTINUES a
contour across a no-data span (and holds an ambiguous surround open); `gr_interp`
(`:rules[2]`) is the pre-existing blur/interpolation CONTROL. All three are gated on
`GroundParams.{ground,interp}` via `PickUnique(NodesOfType(GroundParams))`. The
adapter `domains/ground_world.py` is decision-free by construction (its docstring and
a source-grep gate enforce it): `add_grounded_field` (`:39`) lays out anatomy,
`present` (`:83`) states observations and calls `s.tick`, `belief_field` (`:130`) is a
pure query. **The percept is `gbel` — produced entirely by rules.**

**The RECOGNITION stage (identity) — `seeds/shape_decode_loop.json` v1.7.0.**
`sd_decode` decodes an `Observation` against the held `ShapeSignature` codebook;
`sd_recognize` (residual count == 0) sets `status=recognized` + `covered_by`;
`sd_recognize_transformed` (`transform_explained==1`) and `sd_recognize_dim`
(`dim_explained==1`) set `status=recognized_transformed` + `covered_by` via
`TransformDecode`/`DimInfer`; `sd_mint_quantum` is the fall-through that mints a NEW
quantum when nothing recognizes. **The three `sd_recognize*` rules are the entire
identity assignment** — they are the ONLY writers of `covered_by`. Confirmed by the
T10 audit: these rules run for any residual with NO flag (only `GenInfer` is
flag-gated).

**The two stages do not read each other.** No `vision_ground` rule mentions
`Observation`/`ShapeSignature`/`covered_by`; no `sd_*` rule mentions
`RetinaCell`/`gbel`/`GroundParams`. The percept→concept handoff is the adapter minting
one `Observation` whose `signature` is the percept's cell set (mechanical translation
of a graph read into a graph write — admissible adapter work, §0; the same idiom
`scripts/identity_untangling_measure.py:96` uses).

**COPY and NAME are therefore INDEPENDENTLY readable:**
- **COPY** = the rendered percept cell set `{(r,c) : |gbel[r,c] − 1.0| ≤ 1e−6}`
  (exact-value read on a binary/step field — the idiom of
  `scripts/illusion_measure.py:156–197`, NOT a tuned threshold) compared to the TRUE
  object cell set. `copy_ok ⟺ symmetric difference == 0`.
- **NAME** = `Observation.covered_by` when `status ∈ {recognized,
  recognized_transformed}`, else `None`. `name_ok ⟺ covered_by == the true object`.

**Both ablations can be clean FLAGS (achromatopsia template, §9 OFF by default):**
- **`AgnosiaParams.associative`** guards ONLY `sd_recognize`,
  `sd_recognize_transformed`, `sd_recognize_dim` — the identity assignment. `sd_decode`
  / `TransformDecode` / `sd_mint_quantum` stay live, so the ablated arm is a lesion on
  RUNNING machinery, not silence.
- **`AgnosiaParams.apperceptive`** guards ONLY `gr_fill` — percept COMPLETION. `gr_label`
  stays live (contours are still labelled), so this arm too is a lesion on running
  machinery, not a dead seed.
- The guard form is **absence-tolerant**: `Count(Filter(NodesOfType(AgnosiaParams), ap,
  ap.<flag> > 0.5)) < 1`. A graph that never loads `seeds/vision_agnosia.json` has no
  `AgnosiaParams` node ⇒ count 0 ⇒ **intact**. This is deliberately NOT the
  `PickUnique` idiom, which would return `None` on an absent node and silently kill
  recognition everywhere (§12.3).
- An ablation is a FLAG on a params node, never a Python branch (§0/CLAUDE.md).

**What each readout actually measures (stated plainly, §8).** COPY measures whether the
render RECONSTRUCTS the form across a no-data span — the occluded on-form cells carry
NO sensor data (`raw_sensor` is NaN there), so a passing copy is a genuine
reconstruction, not a pass-through of the stimulus. NAME measures same-orbit membership
in the held codebook, decided in one `run_rules` fixpoint. Neither reads the other.

---

## Stimuli, arms, and the exact statistics

**Stimuli.** Six stroke-composed forms on a 20×20 retina (`T L I H U E`), each built
from straight runs so `gr_label` can carry a contour axis. Each is presented ONCE with
a disc occluder (`blind_radius=1.0` ⇒ 5 no-data cells, **3 of them on the form**)
placed mid-segment, away from every stroke end and junction. The occluded on-form cells
have no sensor data in ANY arm. Codebook = the six TRUE (unoccluded) cell sets as
`ShapeSignature`s; the 17 pre-seeded symbolic signatures are removed so only these six
are candidate identities (the isolation `identity_untangling_measure.py:74` uses).

**n is FIXED IN ADVANCE at 6 objects per arm** (deterministic geometry — every
confirmatory arm below is exact and seed-free; the only seeded arm is the noise FLOOR,
n=100, seeds 48000–48099). No power analysis applies to a deterministic all-or-none
geometric decision; the decision rule is 6/6 (see below). A pilot on this geometry was
run to CALIBRATE the stimuli (§1: does the instrument work at all) — it is not
confirmatory and consumed no seeds.

| arm | flags | statistic | decision rule |
|---|---|---|---|
| **A INTACT** (control validity, §1.1) | both 0 | `(copy_ok, name_ok)` per object | PASS iff **6/6 copy_ok AND 6/6 name_ok** with `covered_by` == the object's OWN name (no cross-naming) |
| **B ASSOCIATIVE** (headline) | `associative=1` | `(copy_ok, name_ok)` | PASS iff **6/6 copy_ok AND 0/6 name_ok** |
| **C APPERCEPTIVE** (headline) | `apperceptive=1` | `(copy_ok, name_ok)` | PASS iff **0/6 copy_ok AND 0/6 name_ok** |
| **C2 APPERCEPTIVE-B** (second render corruption, pre-registered here so it is not a post-hoc arm) | `GroundParams.interp=1` | `(copy_ok, name_ok)` | PASS iff **0/6 copy_ok AND 0/6 name_ok** |
| **D DOUBLE DISSOCIATION** (the seam) | — | `(copy_B, copy_C)` | PASS iff **copy survives in B (6/6) and fails in C (0/6) while naming fails in BOTH** — i.e. the two ablations hit DIFFERENT stages and COPY is what discriminates |
| **E COPY-ALIVE** (§1.1, the arm that stops B being a trivial pass) | `associative=1` | `render_cells_B`, `copy_identical_to_A` | PASS iff for every object the **3 occluded on-form cells are in the percept** (rendered from no data) AND the percept is **set-identical to arm A's** |
| **F LESION-ALIVE** (§1.1, the arm that stops C being a dead seed) | per arm | `percept_nonempty`, `sd_status` | PASS iff arm C's percept is **non-empty** (the render machinery ran, it is the COMPLETION that is destroyed) AND the recognition layer **still ran** on it (`status` reaches a terminal sd state, e.g. `minted`) |
| **G FLOOR** (noise, seeds 48000–48099) | both 0 | false names over 100 random stimuli | PASS iff **0/100** are named, in **every** arm (intact, associative, apperceptive) — noise is not a confound for either lesion |
| **H FLAG LOAD-BEARING** (§13.2) | toggle | `max\|on − off\|` on `covered_by`/percept | PASS iff `associative` moves NAME and not COPY, and `apperceptive` moves COPY (and hence NAME) — `D == 0` on the claimed target ⇒ decorative ⇒ STOP |
| **X OFF-DAY** (§9) | both 0 | committed contracts | PASS iff bench **200/0 with `data/`**, sd orbit law `{2:1,3:2,4:2,6:2,12:4}` unmoved, sibling gates green |

**Unit of analysis is the OBJECT (arms A–F) and the SEED (arm G)** — §4.

---

## Hypothesis (two-sided) and PREDICTION (§3.7)

**H1 (two-sided).** The render and the identity layer are SEPARABLE stages: an
identity-layer ablation leaves the percept intact, and a render ablation destroys both.
**The two-sided alternative that would falsify it:** ablating recognition ALSO degrades
the percept (`copy_B ≠ copy_A`) — the stages are one blob and the "seam" is an
artifact of how I read it; OR the render ablation leaves naming intact — recognition is
NOT downstream of the render (it reads the stimulus, not the percept), and the whole
pipeline is a fiction.

**I predict all arms PASS — a clean double dissociation — with these provisos, stated
in advance:**
1. **Arm B's copy will be BYTE-IDENTICAL to arm A's**, not merely "also correct": the
   two seeds share no attribute, so the identity guard cannot leak into `gbel`. If it
   is merely-correct-but-different, I have mis-audited the coupling.
2. **Arm A's status will read `recognized_transformed`, not `recognized`** (the pilot
   showed this on the identical construction). The percept is origin-normalized to the
   same cell set as the codebook entry, so the LITERAL rung should fire; that the
   TRANSFORM rung reports first is a rule-ordering fact about the sd loop, not a
   failure. **Both are `covered_by`-bearing recognition states and both count.** I flag
   it here so it cannot be read as a post-hoc reinterpretation.
3. **Arm C and C2 will fail copy by exactly the 3 occluded on-form cells** (symmetric
   difference 3 per object) — the lesion removes completion, nothing else. A larger
   difference would mean the flag leaked beyond `gr_fill`.
4. **Arm C's naming will fail by falling through to `minted`**, not by erroring or by
   silence — the identity layer is intact in C and processes the corrupted percept.
   This is what makes C a FORM failure rather than a second identity lesion.
5. **The floor will be 0/100 in every arm.** A random stimulus has no held identity;
   if the intact arm names noise, the naming readout is a lookup, not a measurement.
6. **`apperceptive=1` will NOT be byte-identical to `ground=0`** in the graph (that
   arm keeps `gr_label` live, so `gcont`/`gcax` are still written) even though the
   PERCEPT is expected to coincide. If they coincide bit-for-bit everywhere, my
   "lesion on live machinery" claim is decorative and I must say so.

**What a NULL means (§3.5).** If `copy_B ≠ copy_A`, the finding is *"the stages are
NOT separable in this build"* — reported as the result, diagnosed to the coupling that
caused it, NOT rescued by re-scoping the copy measure (§5). If arm C names correctly,
the finding is *"recognition is not downstream of the render here"* — equally a result,
and it would retire the pipeline claim rather than the arm.

---

## Build (§0/§9) — exactly what changes

- **NO new Rust.** Composition only, over the existing render (`vision_ground`) and
  identity (`shape_decode_loop`) machinery.
- **ONE new seed** `seeds/vision_agnosia.json` — carries ONLY the `AgnosiaParams` node
  (`associative=0`, `apperceptive=0`).
- **TWO guard-clause edits, both OFF by default:** `seeds/shape_decode_loop.json`
  1.7.0 → 1.8.0 (the absence-tolerant `associative` guard on the three `sd_recognize*`
  rules) and `seeds/vision_ground.json` 1.0.0 → 1.1.0 (the `apperceptive` guard on
  `gr_fill`). Nothing else moves; §9 byte-identity holds by construction and is
  verified by arm X.
- **Adapter** `domains/agnosia_world.py` (occluder layout + params write + percept
  read-back — mechanical I/O only), **runner** `scripts/agnosia_measure.py`, **gate**
  `tests/test_agnosia_migrated.py`, **results** `VISION_AGNOSIA_RESULTS.md` +
  `results/agnosia_measure.json`.

**Exactly the arms listed. No sweeps. No re-runs (§3.6).** A further attempt needs a
new pre-registration with a new mechanism-level hypothesis.

## BOUNDS (§8) — stated before the run

This is a **VALIDATION gate for the form↔recognition seam**, nothing more. It does NOT
show: object recognition at natural-image scale; that the render is the only percept
stage; that the sd loop is the only identity stage; anything about WHICH cortical locus
realises either agnosia (the clinical double dissociation is the behavioural target, not
a circuit claim). Bounded to the **discrete/integer, in-frame, binary luminance-contour
class** the render is already bounded to (`VISION_ILLUSION_RESULTS.md` §8) and to the
**held invertible discrete-similarity nuisance class** the identity layer is already
bounded to (`VISION_IDENTITY_UNTANGLING_RESULTS.md` REGIME A). **NAMED FRONTIER:** the
generator-track extensions — lighting, deformation, style.
