# REPLACING `G_figadj` — competitive border ownership. PRE-REGISTRATION

**Committed before any real-frame number.** Seeds **83000–83999**. Engine
**d6097900e8b5** (no Rust change; `scripts/engine_build.sh` run, provenance gate
run as its own step: `tests/test_engine_provenance_migrated.py` +
`tests/test_provenance_endpoint_guard_migrated.py`, **638 passed**).

This tree has **no `data/`**, so the oracle is **212 passed / 10 skipped**, not
222 — 222 is the collected count and the 10 skips are `BSDS300 corpus absent`.
Reported with its condition, per §10.2.

---

## 0 — WHAT IS BEING REPLACED, AND WHY

`VISION_VALUE_FLOOD_RESULTS.md` (merged `1cca265d`) measured that **`G_figadj`
refuses 93.4% of 12,319 enclosed components** on real frames and is the only
quantity that does not move when everything else does (93.4% under exact
equality, 84.0% at one level, 59.0% at two, 98–99.6% across a 4× change in
lattice size).

What it encodes, from the seed's own comment: *"the figure is a hole in ONE
surface."* A component is refused if **any** of its cells touches **any** cell of
**any** other non-background region.

**That is true of a synthetic raster and false of a photograph.** A natural
scene is a **partition**: objects abut objects, and a region whose neighbours are
all background is the exception. The gate encodes **ISOLATION, not OBJECTHOOD**,
and it was validated only on stimuli where the two coincide — which is why it
passes 9/9 synthetic and yields zero multi-cell protos on four independent
real-frame measurements.

It also contradicts this tree's own recorded principle worse than the flood does:
*"a circle with a bit out isn't a discontinuous circle."* `G_figadj` lets **one**
touching cell veto an **entire** component — the exact inversion.

---

## 1 — THE REPLACEMENT, AND ITS DERIVATION

From the seed's **own cited basis**, Zhou/Friedman/von der Heydt 2000: for a
BYTE-IDENTICAL local edge, ownership **FLIPS with the global figure**. Ownership
is **contextual and competitive**. `G_figadj` refuses precisely the case that
border ownership exists to **decide**.

> **A shared boundary is ASSIGNED, not disqualifying.** Where two enclosed
> regions abut, ownership of the shared border goes to the side better explained
> as owning it — the side whose **own perimeter** that border accounts for more
> of. The shared border length `|B|` is common to both sides, so
> `|B|/perim(R) > |B|/perim(Q)` ⟺ `perim(R) < perim(Q)`.
> **A TIE IS HELD OPEN** (no proto), reusing `bo_mint_gestalt`'s size-tie
> precedent.

A component mints iff it **wins every border it participates in** — i.e. it owns
its whole contour. Contact alone never vetoes; only a **lost competition** does.

### As built (seed `vision_border_ownership` **v1.1.0**)

Authored by `tools/author_border_ownership_v11.py`, which DERIVES the new rules
from the incumbent's own term trees by **structural location** — never a
substring edit, never a hand-retyped copy — and refuses to write if the incumbent
tree moved.

- **`bo_mint_owned`** = `bo_mint_enclosed`'s term tree with **ONE conjunct added**
  to `G_figadj`'s inner predicate: `Not(Lt(R.rim, n.rim))`. An abutting cell `n`
  of another enclosed component refuses `R` only if `R` does **not strictly win**.
- **`bo_rim`** materialises `perim` as a cell attribute: the number of enclosed
  cells sharing this cell's `glabel` that have at least one neighbour of a
  different `glabel` — the region's own contour, in cells. Gated on the floods
  being **SETTLED** (the incumbent's own settled sub-term, reused verbatim) so
  `glabel` is final before any count is taken; re-fires to a fixpoint like
  `bo_label`. Materialised rather than computed in-gate because in-gate is O(N)
  per abutting pair per root.
- **`bo_mint_enclosed`** keeps its tree **exactly**, gaining only the
  mutual-exclusion guard `Lt(bown_own, 0.5)`.
- **`BorderOwnParams.bown_own`** arms the replacement, **0.0 by default** — so
  every existing caller runs the incumbent unchanged (**§9**).

**Monotonicity.** Before `bo_rim` fires every `rim` is 0, so `Lt(0,0)` is false
and the gate REFUSES. Rims can only turn a refusal into a mint, never a mint into
a regret; the `Not Exists ProtoObject at this root` guard is never asked to
retract.

**§13 — no new threshold.** The only new comparison is `Lt` between two
**measured counts**; the tie is **equality**. Audited by AST walk, not text:
`tests/test_figadj_replacement_ast_migrated.py` (**7 passed** at time of
pre-registration).

**Relation to the "more permissive is not the direction" warning.** That finding
(protos 234 → 78 → 68) was about relaxing the **FLOOD**, which merges components
and lets the background **swallow the figures** (enclosed components collapsed
12,319 → 427). **This rung does not touch the flood.** Component structure is
byte-identical; only the gate changes. The named failure mode is nevertheless
measured directly (M4 below) and would falsify the change.

---

## 2 — CONFIGURATION

Per `VISION_RESOLUTION_SCALE_RESULTS.md` §10: **a 4×4 grid of 18×18 tiles is
known to cost 2.9× and to lose nothing, and is the configuration a proto-object
probe should use.** Adopted: `jellyfin_frames(..., size=72)`, tiled row-major
into 16 non-overlapping 18×18 tiles (`region_origins`, the incumbent tiling).
Each tile is one border-ownership field (324 cells).

That rung also warns its **primary read-out saturates** at this grain. That
warning does not bind here: this rung's read-outs are proto counts and
cross-frame proto persistence, neither of which is the saturating identity
primary. The persistence read-out has its own floors and is not at ceiling by
construction.

Corpora and pins are the value-flood rung's, asserted at run time:
**C1** cartoon `08630d4b…`, **C2** live-action `119eca43…`,
`jellyfin_frames(every=2, start_s=300)`. **A pin mismatch VOIDS the run.**

**Floors are re-earned at this configuration, not inherited** — floors have moved
3.6× and in opposite directions across configs in this tree. Every incumbent
number quoted below is re-measured at G72 within this rung.

Measured cost pilot (18×18, before registration): incumbent ~49 ms/tile,
replacement ~97 ms/tile.

---

## 3 — THE GATE: A FOUR-ARM CONJUNCTION

All four must hold. Any one failing is a reported negative (§7).

### ARM 1 — multi-cell protos appear on real frames

**M1.** 2 corpora × 4 `k` ∈ {2,4,8,16} × 7 sampled frames × 16 tiles × **both
predicates** = 1792 tile-runs. Read out per tile: `n_protos`,
`n_protos_multicell`, `max_members`, and the gate attribution
(`G_settled` / `G_figadj` / `G_own_lost` / `G_gnd2` / `G_pass`).

**Registered prediction P1:** under the replacement, **multi-cell protos per
frame > 0** on both corpora at `k=16`; under the incumbent at the SAME config
they remain at or near zero (re-earning the four-times-reproduced floor).

**Attribution must RECONCILE:** `G_pass == n_protos` on every row, under **each**
predicate separately. The prior rung's counterfactual simulation was validated
`168/168` **under the incumbent predicate only** and therefore **cannot score the
replacement** — so the replacement is run **through the substrate itself**, and
its read-out is re-validated against the rules' own minted output rather than
reused on faith. A row that does not reconcile is not claimed.

### ARM 2 — the protos CORRESPOND to something (the hard one)

There are no object labels. The handle: **real proto-objects should PERSIST
ACROSS FRAMES better than an arbitrary partition of the same field.**

**M2.** 2 corpora × **40 consecutive frames** × 16 tiles, `k=16`, both
predicates. Persistence of proto supports, per tile position (a tile is a fixed
image region across frames):

- For each proto `p` at `(t, i)`, `best-IoU(p)` over protos at `(t+1, i)`;
  `score(t,i)` = mean over `p`. Tiles with no proto at `t` are excluded.
- **FLOOR-A — temporal shuffle.** Same computation against protos at `(u, i)`
  with `|u − t| > 5`, `u` drawn from the same corpus. This is the identity-seam
  floor construction (`seeds/vision_identity_seam.json` /
  `scripts/identity_seam_measure.py` CLAUSE 1), reused deliberately.
- **FLOOR-B — arbitrary partition.** Same computation against a **size-matched
  random partition** of frame `t+1`'s own enclosed cells: the multiset of proto
  sizes at `(t+1,i)` is held FIXED and that many connected regions are grown by
  BFS from random enclosed seed cells. The field, the proto count and the size
  distribution are all held fixed; **only the mechanism's specific grouping is
  destroyed.**

FLOOR-B is the decisive one. Nearby frames are similar, so a random partition of
a stable field would also beat FLOOR-A; only FLOOR-B isolates whether the
GROUPING is doing work rather than the field's stability.

**Registered prediction P2:** the replacement's persistence beats **BOTH** floors,
paired 95% CI (unit of analysis: the frame pair, aggregated over tiles;
`ci95`/`paired_ci95` as in the identity-seam rung) with **lo > 0** against each.

**PASS requires beating both.** Beating FLOOR-A but not FLOOR-B is the
**"arbitrary partition"** outcome — protos appear but do not correspond — and
will be reported as such, as a negative for the mechanism.

### ARM 3 — the synthetic gate stays 9/9

Not trivially, by the flag being off. **Every one of the nine synthetic arms is
re-run with `bo_mint_owned` armed** and must return the SAME verdict:
`tests/test_border_ownership_owned_migrated.py` alongside the incumbent
`tests/test_border_ownership_migrated.py` → **18 passed**.

Why it must hold: on a figure-on-blank stimulus the figure has no abutting
enclosed component, so the competitive conjunct is never reached and the two
trees evaluate identically. **The replacement is a strict weakening** — it agrees
with the incumbent wherever a component touches nothing.

The load-bearing arm is `arm_floor_noise` (100 iid fields, seeds **36000–36099**
— the incumbent arm's OWN range, reused deliberately so both predicates see the
byte-identical fields; not an allocation from this rung's block). A more
permissive gate is exactly the change that starts minting on speckle.

### ARM 4 — no new hand-set threshold (§13)

AST walk over every rule's term tree, `where` and effects, recording every
comparison node's literal operand and what it is compared against. Asserted both
ways round: every literal in a comparison is a 0/1 flag discriminator; and no
literal is compared against `val`, `rim`, `glabel`, `cid`, `members` or `root`.
Plus: the ownership comparison is located **structurally** and asserted to be
`Attr(rim)` vs `Attr(rim)` under exactly one `Not`, with no literal.

---

## 4 — DEAD-INSTRUMENT CONTROLS (must ACTUALLY FIRE, not merely be able to)

The trap this thread has been caught by three times: **a proto mechanism that
mints vacuously looks like success.**

- **D1 — positive control.** The committed 12×12 figure must reproduce
  `1 proto / 24 members` under **both** predicates. If it does not, **no
  real-frame number is claimed.**
- **D2b — the value-flood rung's working trap, re-run.** Uniform field, frame
  flags stripped → the flood cannot seed → `1 proto` with `144` "members" on a
  field containing no figure. Must fire under both predicates.
- **D2a — a NEW trap instance specific to the replacement, registered as a
  PREDICTION.** The 12×12 *figure* field with frame flags stripped produced **no**
  vacuous mint under the incumbent (`G_figadj` refused both mutually-adjacent
  components — the prediction the value-flood rung recorded as WRONG).
  **The replacement is weaker, so I predict it DOES mint here: the
  smaller-perimeter side wins the competition and mints on an unseeded flood.**
  This is registered as an expected FIRING of the trap, not as a defect —
  a control that fires is a control that works. Separated from every live run by
  `n_frame = 0` and `reach = 0`.
- **NEGATIVE control.** iid noise at 18×18, `k=16`, must mint **nothing** under
  the replacement — the speckle refusal must survive the weakening.

---

## 5 — M4: THE FAILURE MODE THE PRIOR RUNG NAMED

"Loose admissibility lets the background **swallow the figures**." Read out
`max_members / 324` per tile. **If the replacement's protos are predominantly
near-tile-sized, the mechanism has swallowed the field and ARM 1 is satisfied
vacuously** — reported as a failure regardless of the raw proto count.

---

## 6 — HONEST OUTCOMES, ALL PUBLISHABLE

1. **The replacement works** — multi-cell protos appear AND persist above both
   floors. `G_figadj` was the blocker and the derived replacement is right.
2. **Protos appear but do not persist** above FLOOR-B — the mechanism mints an
   **arbitrary partition** and is **wrong**, notwithstanding that it removed the
   blocker.
3. **Protos still do not appear** — `G_figadj` was **not the whole blocker**, and
   the value-flood rung's attribution needs revisiting.

Whichever occurs is reported. No metric is chosen after looking (§5); the
decision rules above are the ones applied.

---

## 7 — WHAT IS NOT TOUCHED

- **`bo_mint_gestalt` is not modified.** It is unreachable on real frames (it
  needs a 2-component bipartition; enclosed components number 4.7–294.9 per
  frame). No claim depends on it.
- **The flood is not modified.** No change of statistic, tolerance or extent.
- **`k` remains a hand-set adapter magic number** (§13), inherited and unfixed —
  recorded as a standing residual, not addressed here.
- `VISION_PROTOCOL.md` is not edited (§11).

## 8 — SEED ACCOUNTING

Declared block **83000–83999**. Consumption will be **MEASURED**, not asserted,
with `scripts/seed_audit.py --check 83000 83999` run against this rung's own
runner, and the measured draw reported — including any draw outside the block and
why. 34 runs in this tree drew outside their declared block; declaring is not
measuring.
