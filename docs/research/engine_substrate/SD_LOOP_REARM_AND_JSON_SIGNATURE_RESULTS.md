# SD LOOP — re-armed transforms and JSON-string signature scoring — RESULTS (block 371000)

**Pre-registration:** [`SD_LOOP_REARM_AND_JSON_SIGNATURE_PREREG.md`](SD_LOOP_REARM_AND_JSON_SIGNATURE_PREREG.md)
(start commit `1281a482`). **Amendment:**
[`SD_LOOP_REARM_AND_JSON_SIGNATURE_AMENDMENT.md`](SD_LOOP_REARM_AND_JSON_SIGNATURE_AMENDMENT.md)
(`f84951d4`, written after a partial G-6 run and before the final one).

**Outcome.** Both defects are fixed, and gates G-0 to G-5 pass.

G-6, the regression comparison, failed as first designed. It found that rewriting
`Transform` receipts in place changes chunk-retention accounting, so the D1 design was
amended. The final G-6 found three more pass→fail changes; each was localised and resolved
(§3).

D2 was not only a latent bug. It produced a wrong number in a committed research record:
`det1`'s shear-alias identities and its shear invariance count (§4).

## 1. What changed

- **D1, a re-armed transform is stuck at `decoded`.** Two new rules in
  `seeds/shape_decode_loop.json` v1.18.0: `sd_rerecognize_transformed` and
  `sd_rerecognize_dim`.
  - They fire on a decoded observation that already holds a `has_transform` edge and whose
    re-decode explains it again.
  - They set `status := recognized_transformed` and `covered_by`. The dimension path also
    sets `transform_explained := 1`.
  - They carry the agnosia `associative` guard, copied verbatim.
  - Per the amendment, the `Transform` stays the receipt of the first recognition and is
    not rewritten.
- **D2, rule-side scoring misread JSON-string signatures.** A new Rust Term,
  `ClosestShape { goal, codebook_type }`, does the same selection as
  `Argmax(NodesOfType, sig, FixedCount(AntiUnify(SetT[goal, sig.signature])))`.
  - It reads a JSON-string signature the way `load_parts` does.
  - It reports to the selector audit as `Argmax` did, and re-scores the returned node
    independently.
  - It replaces the `Argmax` in `sd_recognize.covered_by` and
    `sd_mint_quantum.closest_held_shape`.
  - Wiring: the variant is appended to `TermNode`, `term_variants.rs` is regenerated, and
    jsonio, reflect, `copy_subtree`, children, `rewrite.rs` attr-read and `shape.rs`
    children all handle it.
- **Engine:** `59a4898f34dc`, built with `scripts/engine_build.sh --lib-only`. The artifact
  is committed.
- **Seed generator:** `scripts/gen_sd_rearm_and_closest_shape.py`. It is idempotent, and
  each pattern is asserted before it is replaced.
- **Deviation from the prereg:** prereg §1 named four rule sites. The two
  `seeds/prog_construction_loop.json` sites score a filtered source
  (`kind == "prog_construction"`), and their parts are rule-minted copies of native
  observation signatures, so D2 cannot occur there. They were left unchanged, and the
  prereg's description of them was wrong.

## 2. Gates

| gate | result |
|---|---|
| G-0 engine | Rust `closest_shape` tests 4/4 (native = Argmax; JSON = native; empty → None; selector-audit firing plus the caught positive-control fault); `variant_table_covers_the_enum` passes; provenance `own` |
| G-1 covered_by, JSON | JSON parts → `zz_part_B` (pre-fix: `fractal`); native → `zz_part_B` |
| G-2 closest_held_shape | JSON and native both mint 1 axis with `closest_held_shape = zz_part_B` |
| G-3 affect codebook as JSON | 23/23 frames `covered_by = affect:<own tag>`, statuses and deltas equal to native, 0 mints |
| G-4 D1, transform path | 8 recognized / 15 recognized_transformed / 0 decoded (was 8/4/11); 15 Transform nodes, 1 per transformed frame |
| G-5 D1, dimension path | rotated tromino after unrelated growth: `recognized_transformed` (pre-fix control: `decoded`), receipt base `part_tromino`, `rotation90`, k=1, 1 Transform, 1 LatentDimension |

Command:
`OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_sd_rearm_closest_shape_migrated.py …`.
With the eleven affected test files: 100 passed, 1 skipped, and 1 failed. The failure is
`test_agnosia::test_pinned_results_reproduce_the_committed_verdict`. It needs the gitignored
`results/agnosia_measure.json`, which a fresh worktree lacks, and it fails identically on
the start commit.

## 3. G-6: regression comparison by node id

**Set.** The 150 test files that mention the sd loop, codebook or `covered_by`
([`SD_LOOP_REARM_SCOPE.txt`](SD_LOOP_REARM_SCOPE.txt)). That collects 2054 ids. The 32 ids of
`test_humanoid_walking_migrated.py` were excluded: it is a heavy simulation that matched the
selection only by mentioning a codebook type, and it stalled both trees for over an hour.

**Runs.** The remaining 2022 ids ran in two detached worktrees, the start commit and the
fix, with the same id list (`pytest @ids`). Each produced 2006 outcome rows.
- Start commit: 207 failed, 1730 passed, 52 skipped, 33 errors.
- Fix (engine `a414005f`): 210 failed, 1727 passed, 52 skipped, 33 errors.
- The two trees match on every row except the three below.
- The shared failures come from the worktree environment (no `data/`, no gitignored
  `results/`) and are identical in both trees.

**First, partial pass (1070 ids).** It found four pass→fail changes:
- the agnosia guard enumeration;
- the det1 alias pin;
- chunk retention, which led to the D1 amendment;
- a variant gate that reads uncommitted `term.rs`.

These are in the amendment, and all four pass on the final fix.

**Final pass.** It found three more:

| test | cause | resolution |
|---|---|---|
| `test_selector_winner_value::test_the_invariant_holds_across_a_seed_booted_rule_fixpoint` | zero selector firings: `ClosestShape` had replaced the only `Argmax` that fixpoint exercised, so the audit lost coverage | `ClosestShape` now reports to the selector audit (engine `59a4898f34dc`); passes |
| `test_similarity::test_off_by_default_is_committed_behaviour`, `::test_shears_aliased_without_the_restriction` | the same as det1: the pinned alias `X` was the D2 tie artefact; the true closest part is `U` | pins updated to `U` with a comment; pass |

The audit hook adds code only under `selector_audit::enabled()`, which is off by default.
The full 2022-id comparison was not re-run on `59a4898f34dc`.

## 4. Consequence for committed research records

These are reported here; the records themselves are not edited.

**det1** (`scripts/det1_measure.py`, run on both trees):
- A2 shear invariance: **12/14 correct → 11/14**; wrong-id 2 → 3.
  - The wrong identities were (F→X, T→X) and are now (F→U, T→N, X→V).
  - On the start commit, the "correct" X-shear case was the tie artefact returning `X` for
    everything. It was right by accident.
- A3 `shear_wrong_id` 2 → 3, and A4 `orbit_wrong` 2 → 3.
- det1's OUTCOME 2, that shears still over-merge under |det|=1, holds and is slightly
  stronger. The specific alias identities and counts in `VISION_DET1_RESULTS.md` and
  `results/det1.json` come from the defect.

**similarity** (`scripts/similarity_measure.py`): output identical on both trees. Its
similarity-on gates are unaffected; only the sim-off controls in its test pinned the
artefact.

**Not checked:** any other consumer whose codebook stores JSON-string signatures and reads
`covered_by` from `sd_recognize` or `closest_held_shape` from a mint. That includes the
agnosia, identity_seam, stroke and composer codebooks, and the many scripts that read
`closest_held_shape`. Each is a candidate for the same re-measurement.

## 5. Gaps

- `sd_redecode` still leaves `gen_checked`/`gen_explained` set across a re-arm. This was
  stated in advance and is not fixed.
- `ClosestShape` does not reproduce `Argmax`'s `argmin_tie` or `refuse_all` instrument
  modes. Both are off by default.
- G-6 is a scoped slice in worktrees, not the full `-k migrated` sweep. The humanoid walking
  file was excluded.

## 6. Provenance

- Branch `sd-fix/v1`. Implementation by the `ocelot-substrate-executor` subagent. The
  amendment and the audit hook are by the supervisor.
- SHA-256 prefixes: engine artifact `59a4898f34dcd654`, seed `af77e11e02b7e731`, generator
  `cefb89efb073993a`, test `966e37dc0b34d5e5`.
- Logs: `/tmp/ocelot_sd_fix/logs/` (`base_g6.log`, `fix_g6.log`, `*_det1.log`,
  `*_similarity.log`).
