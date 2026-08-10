# VALUE-FLOOD CONDITIONS — pre-registration

Seeds **81000–81999**. Engine pinned **d6097900e8b5**. Provenance gate run as
its own step before any number.

Target: `seeds/vision_border_ownership.json` rules `bo_bgflood`, `bo_label`,
`bo_mint_enclosed`, `bo_mint_gestalt`, `bo_own`. Prior:
`VISION_BLOB_NATIVE_RESULTS.md` (merged `c160f770`),
`VISION_VIDEO_PROBE_RESULTS.md`.

Proto-objects produce ZERO multi-cell protos on real frames, byte-identical
across three independent measurements. Resolution and sampling geometry are
both eliminated by measurement. The blob rung named the remaining suspect:
the failing gates are **value-flood conditions**. This rung measures them.

---

## §0 — WHAT THE MECHANISM ACTUALLY COMPARES (read before predicting)

Recorded from the seed, before any run, because it constrains every prediction
below and because two of the three candidate explanations are about it.

`bo_bgflood` floods `bg` from the frame inward across a neighbour pair iff
`Eq(m.val, R.val)` — **exact integer value equality**, zero tolerance.
`bo_label` groups components by the same `Eq(m.val, R.val)`. There is **no
value threshold anywhere in the seed**; every `Lit 0.5` in these rules is a
boolean discriminator over a 0/1 flag (`bown`, `bg`, `frame`, `owns`), not a
comparison against a luminance.

`val` is not raw luminance: the harness quantizes per frame to `k` levels
(`scripts/blob_proto_measure.py::quantize`, per-frame min/max). So exact
equality is **not** vacuous — `k` sets how many cells can be equal, and `k` is
therefore the mechanism's *de facto* tolerance. `k` lives in the adapter
(`K_LEVELS = (2, 4, 8, 16)`), hand-set. That is recorded here as a candidate
§13 finding to be confirmed or denied by measurement, not asserted.

`bo_mint_enclosed`'s gate 5 is a **conjunction of two independent tests** that
the prior rung's diagnostic did not separate:

- **G_figadj** (`f`/`n` clause): no figure cell of this component may have a
  neighbour that is a *different* component and also enclosed (`bg < 0.5`).
  I.e. the figure may not touch any other non-background region.
- **G_gnd2** (`g1`/`g2` clause): no two ground-side neighbours of the figure
  may carry different `glabel` — the figure is a hole in ONE surface.

`scripts/blob_proto_measure.py::gate_diagnostics` measures **G_gnd2 only** and
labels the result `n_singly_surrounded`. At C1/k=16 it reports 80 components
"singly surrounded" against **0** protos minted. That gap is unreconciled in
the prior rung and is the sharpest lead this rung has.

## §0.1 — CONFIGURATION NOTE (resolution rung, received before config was fixed)

The resolution rung recommends a 4×4 grid of 18×18 tiles and reports that
scale fails while grain works (region ICC rises 0.0251 → 0.1937 as regions
shrink). **That recommendation does not transfer to this stage.** The proto
stage never sees the region grid (blob rung §0.3, confirmed here by reading
`blob_proto_measure.py`: it boots a fresh substrate, loads only
`vision_border_ownership`, and consumes a raw `GRID = 16` quantized luminance
lattice). The variable the recommendation points at — **extent** — maps here
to the lattice side `L`, and is registered below as a **fourth explanation
(d)**, stated separately rather than folded into the three, per instruction.

Floors are **not inherited** across configurations. The positive control is
re-earned at every `L`.

---

## §1 — DESIGN

Corpora, both, reported per corpus, never pooled:

- **C1** cartoon, `episode_index 0`, pin `08630d4b…` (checked live, matches).
- **C2** live-action, `episode_index 3`, pin `119eca43…`.

Pins asserted at run time; **a mismatch VOIDs the run**. Decode parameters
inherited unchanged: `N_DECODE = 150`, `every = 2`, `start_s = 300`,
`FRAME_INDICES = (0, 25, 50, 75, 100, 125, 149)`.

Axes: `k ∈ {2, 4, 8, 16}` (value grain) × `L ∈ {16, 24, 32}` (extent).
`L = 16` reproduces the incumbent exactly. Seed **unchanged** throughout the
measurement phase — no mechanism edit before the discrimination is done.

---

## §2 — MEASUREMENTS

**M1 — where the flood stops.** Per frame at fixpoint: `n_frame` (seed count),
`bg_frac`, `sweeps`, and `reach = bg_cells − n_frame` (cells the flood
actually gained beyond its seed). Plus the **frontier value gap**: over every
adjacent pair with `bg_i = 1, bg_j = 0`, the distribution of `|val_i − val_j|`.
That distribution is the literal answer to "at what value difference does the
flood halt".

*A flood that halts immediately and a flood that never seeds look identical
from outside.* They are separated here by `n_frame` and `reach` jointly:
never-seeded is `n_frame = 0`; halts-immediately is `n_frame > 0, reach ≈ 0`.

**M2 — gate attribution, reconciled.** For every enclosed component, classify
independently in the read-out which gate of `bo_mint_enclosed` fails first:
`G_figadj`, `G_gnd2`, `G_settled`, or `G_pass`. **Registered consistency
requirement: `n_G_pass` must equal `n_protos` as minted by the rules.** If it
does not reconcile, the diagnostic is measuring something other than the rule
and **no attribution is claimed** — this is the check whose absence left the
prior rung's 80-vs-0 gap standing.

**M3 — value distributions (the evidence (c) requires).** Per frame per `k`:
the full distribution of `|Δval|` over adjacent pairs; the fraction with
`Δval = 0` (the flood's admissible edges); and equality-component size stats
(count, mean, max). Plus the counterfactual, computed offline in numpy with
**no seed change**: connected-component sizes under a gradient criterion
`|Δval| ≤ 1` (adjacent-level) on the identical lattices.

---

## §3 — DEAD-INSTRUMENT CONTROL, DEMONSTRATED FAILING

Not a control that could fail — one that **does**, in this rung's output.

- **D1 positive.** Synthetic 12×12 figure → exactly 1 proto, 24 members. Must
  reproduce at every `L`.
- **D2 dead-instrument, MUST fire.** The same synthetic field with every
  `frame` flag cleared. The flood is then unseeded, every cell reads enclosed,
  and the mint fires **vacuously** — the exact trap that briefly read as
  success in the blob rung. Registered expectation: D2 yields `n_frame = 0`,
  `reach = 0`, and a **non-zero vacuous proto count**, and M1 separates it from
  every live run. **If D2's reported statistics do not differ from a live run,
  the instrument is blind and NO real-frame number is claimed.**

---

## §4 — REGISTERED PREDICTIONS

- **P1.** The flood seeds and runs on real frames: `n_frame = 4L − 4 > 0` and
  `bg_frac > 0.3` at every `k`. (Failure-to-seed is NOT the explanation.)
- **P2.** At `k ≥ 8` the dominant failing gate is **G_figadj**, not `G_gnd2`.
- **P3.** Multi-cell protos (`members ≥ 2`) remain **0** at `k = 16` on both
  corpora at `L = 16` — the incumbent null reproduces.
- **P4 (the discriminator).** Equality-component max size falls with `k`;
  gradient (`|Δ| ≤ 1`) components at the same `k` are substantially larger.

P4 is what separates (b) from (c) and it is registered in the direction that
would **refute (c)**.

---

## §5 — HOW EACH EXPLANATION WOULD BE SUPPORTED

- **(a) threshold too strict.** Supported iff a hand-set *value* threshold
  exists in the mechanism and relaxing it changes the outcome. §0 already
  records that the seed holds none; if that survives the AST-walk audit, (a)
  is refuted **as stated** and the tolerance is instead `k`, an adapter magic
  number (§13).
- **(b) statistic wrong.** Supported iff gradient/affinity components are
  large where equality components are not, at the same `k` and lattice.
- **(c) structural.** Supported **only** by value distributions showing that
  no criterion at this grain yields extended regions — i.e. gradient flooding
  fragments too. **Not to be reached by elimination**; if concluded, the
  forcing distributions are shown.
- **(d) extent** *(fourth, from §0.1)*. Supported iff raising `L` at fixed `k`
  makes multi-cell protos appear. Reported as its own explanation, never
  folded into (a)–(c).

Metrics are the incumbents (`n_protos`, `members ≥ 2`). No metric surgery
(§5). Negatives reported (§7). Any threshold introduced later must FALL OUT
(§13); the synthetic border-ownership gate (8/8) must not regress.

**A clean negative — including "value flooding cannot work on natural images
and the mechanism needs replacing" — is a full result.**
