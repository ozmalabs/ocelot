# Fixpoint fix vs revert — does the CONFIRMATORY identity seam move like the pilot?

**Block 123000–123999. Prereg: `VISION_FIXPOINT_IDSEAM_PREREG.md` (committed `3e7b182cc2`, before any confirmatory number).**

> **Supervisor-completed.** The measuring agent built both engines, ran C1/C2 under
> each, and produced the arm data + the mechanical comparator, then stalled (repeated
> re-parking under concurrent load) before writing this doc. The supervisor read the
> produced artifacts directly and finished the write-up + comparison. Every number
> below is read off the committed artifacts, not the run.

## The question

The fixpoint-coverage rung (`VISION_FIXPOINT_RERUN_RESULTS.md`) fixed a genuine engine
bug — `run_rules` returned over unsettled state because a `dirty_by_writeset` early-out
skipped the post-mint re-decode (`sd_redecode`) — and measured that the fix MOVES a
landed number on the **pilot**: `identity_seam_pilot` went **89 recognized / 7 minted
under the defect → 96 / 0 under the fix** (7 spurious identities the engine
manufactured). Its explicit, un-discharged liability: **the CONFIRMATORY
`identity_seam_C1`/`C2` were NOT re-run, and no estimate was made.** Their state was
therefore *unknown, not unchanged*. This rung closes that.

## Method

Both engines built in-tree from source:

| arm | engine sha (`_native.abi3.so`) | source |
|---|---|---|
| **fix** | `7041d2e6a7dd…` (== canonical) | current tree |
| **revert** | `5ccaa2ea4bed…` (distinct) | the `dirty_by_writeset` early-out re-added — one line, labelled a deliberate defect |

The revert line was removed and the fix restored after measurement (working tree back to
`7041d2e6`; the branch merges NO Rust change — this is a measurement). C1 (cartoon,
*Middlemost Post* S2E1) and C2 (live-action, *Secrets of the Zoo*) each ran **1600
trials per (arm, Δ)** on both the **stock** and **ncc** comparators, under both engines.
`scripts/idseam_compare.py` is a mechanical field-by-field diff (wall-clock / provenance
leaves excluded as noise per the prereg) plus a per-observation status tally.

**Oracle on the fix engine: 222 passed / 0 failed** (`var/oracle_fix.log`).

## Result — the confirmatory DOES move like the pilot, but ONLY on the discounted arm

Per-observation status, fix vs revert, n=1600 per corpus (main trajectory):

| corpus / comparator | FIX | REVERT (defect) | flips | exposed? |
|---|---|---|---|---|
| **C1 / stock** | 1600 recognized | **20 minted** + 1580 recognized | **20** | YES |
| **C1 / ncc** | 23 minted, 1577 held | 23 minted, 1577 held | **0** | **NO — identical** |
| **C2 / stock** | 1598 recognized, 2 transformed | **24 minted** + 1574 recognized, 2 transformed | **24** | YES |
| **C2 / ncc** | 23 minted, 1577 held | 23 minted, 1577 held | **0** | **NO — identical** |

Summary-document diff (statistics, not per-trial status): **0 non-noise movers on both
C1 and C2**; `n_cut = 3` and `otsu = 11.085…` unchanged across arms.

**The finding, stated loudly as the prereg required:** on the **stock** comparator the
defect manufactured **20 (C1) and 24 (C2) spurious identities per 1600 trials** — exactly
the pilot's failure mode (what should resolve to a held identity minted a new one because
the defect ate `sd_redecode`). The fix eliminates all of them (0 minted).

**But the landed CONFIRMATORY conclusion SURVIVES, and the reason is precise.** The
identity-seam / cross-frame result rests on the **ncc** arm by its own construction —
`VISION_IDENTITY_SEAM_RESULTS.md` (§ "the NCC arm fixes exactly that"): the **stock mint
gate is vacuous on real pixels**, so its raw mints were already discounted; the **ncc**
(shuffle-control-corrected) arm is the load-bearing one. That arm is **byte-identical
fix-vs-revert (23 mints / 1600 = 1.44% on both C1 and C2, 0 flips)** — it is **not exposed
to the defect at all.** So the engine bug's reach into the confirmatory is confined
entirely to the arm the doc had already set aside; the arm the conclusion depends on is
provably defect-free.

**Net:** the fix does not overturn the confirmatory conclusion — it *strengthens* the
doc's existing judgment, by showing the stock arm's apparent mints were partly an engine
artefact (20/24 of them), while the real signal (ncc) never moved.

## What is unknown / not claimed

- The published "mint rate 1.4–1.9%" is consistent with the **ncc** floor (23/1600 =
  1.44%, unchanged) at its low end; the "16 of 1600 (1.0%)" figure in the cross-frame doc
  is a *transform-recognition cost*, a different quantity, not re-derived here. No
  cross-frame headline number is restated as changed.
- Trigger-exposure is now measured rather than estimated: the stock arm IS exposed
  (20/24 `sd_redecode`-path flips); the ncc arm is NOT (0). The prereg's fallback ("count
  the redecode triggers before reporting a null") is discharged — the ncc null is not
  vacuous, it is an *unexposed workload*, and the stock movement proves the workload class
  can move.

## Ledger row (for the supervisor to insert into `VISION_PROTOCOL.md`)

| range | used for |
|---|---|
| **123000–123999 (fix-vs-revert measurement; NO Rust merged — the revert line was transient; both engines built in-tree, fix `7041d2e6` == canonical, revert `5ccaa2ea`)** | **THE CONFIRMATORY IDENTITY SEAM *DOES* MOVE LIKE THE PILOT — BUT ONLY ON THE ARM ALREADY DISCOUNTED, SO THE LANDED CONCLUSION SURVIVES ON DEFECT-FREE GROUND.** The fixpoint bug (`dirty_by_writeset` early-out ate the post-mint `sd_redecode`) manufactured **20 (C1) / 24 (C2) spurious minted identities per 1600 trials on the STOCK comparator** — the pilot's exact failure mode (89/7→96/0), now confirmed to reach the confirmatory. The fix eliminates all of them (stock: 0 minted). **The NCC arm — the identity seam's OWN load-bearing, shuffle-control-corrected comparator (its doc: "the stock mint gate is vacuous on real pixels; the NCC arm fixes exactly that") — is BYTE-IDENTICAL fix-vs-revert (23 mints/1600 = 1.44%, 0 flips on both corpora): NOT EXPOSED to the defect.** Summary statistics 0 non-noise movers; `n_cut=3` unchanged. So the defect's reach into the confirmatory is confined to the arm the conclusion never rested on; the fix STRENGTHENS the doc's existing judgment (the stock arm's apparent mints were 20/24 an engine artefact) rather than overturning it. Prereg's null-fallback discharged: the ncc null is an UNEXPOSED workload (0 redecode-path flips), not a vacuous one, and the stock movement proves the class can move. Oracle on fix **222 passed / 0 failed**. Supervisor-completed: the agent produced both engines + arm data + the mechanical comparator, then stalled under concurrent load; the write-up is read off the committed artifacts. |
