# PROGRAM SYNTHESIS P3 — the construction codebook + corpus statistics (results)

**Date:** 2026-07-31. Companion to `PROGRAM_SYNTHESIS_PLAN.md` §4-P3,
`PROGRAM_SYNTHESIS_PREREG.md` §5 (H3a/H3b), and this phase's own small prereg
`PROGRAM_SYNTHESIS_P3_PREREG.md` (written FIRST, per plan risk §6.6). Artifact:
`results/prog_construction_scan.json`. Gates:
`tests/test_prog_constructions_migrated.py` (10/10).

## 1. What landed

- **`seeds/prog_construction_loop.json` v1.0.0** — a PARALLEL sd loop for kind
  `prog_construction` (the `role_decode_loop` precedent: sibling loop, new
  kind; `seeds/shape_decode_loop.json` byte-untouched — FROZEN). Six rules,
  Occam-ordered in one `run_rules` fixpoint: `pcon_decode` (literal
  `ShapeDecode`) → `pcon_recognize` (empty residual) → `pcon_recognize_covered`
  (standalone `Covers` against wildcarded merged quanta) → `pcon_mark_merge`
  (**merge-at-mint**, the new piece) → `pcon_mint` (bounded Term-computed
  name, in-rule epoch bump) → `pcon_redecode` (re-arm on the DISTINCT
  `Agent.prog_codebook_epoch` — the voice_codebook_epoch Or-arm precedent, so
  the frozen seed is never touched). Isolation from the frozen loop is by
  construction: `pc_status`/`pcon_*` attrs (the frozen rules key on `status`,
  which these Observations never carry) and namespaced relation predicates
  (`pstmt`/`parg`/`pop`/`parity`/`pblock`) no other codebook shares, so
  literal cover cannot cross kinds.
- **`domains/prog_ir_signature.py`** — the FIXED extraction walk (no
  decisions): hub-IR Term-JSON → statement-grain relation-systems (depth-1,
  content-invariant: identifiers/literals/extern names never appear; blocks
  presence-only — the run-5 fragmentation lesson), function-grain label
  sequences (character-composition one level up), plus the mechanical seed
  loader / Observation ingest / read-back / `apply_marked_merge` /
  `prog_codebook` adapter verbs.
- **`scripts/prog_construction_scan.py`** — the "training run" driver: emit →
  dedup-ingest (identical signatures are ONE Observation with an occurrence
  tally — the distributional-stats precedent) → `run_rules` → apply marked
  merges one per round → tally → working-set GC; bigram counting with add-1
  smoothing; the P2 cross-frame triples through the SAME codebook; a full
  second run for determinism evidence.
- **No starter-shape seed.** The codebook grows from empty (the loop's
  empty-codebook bootstrap is explicit in `pcon_decode`, §4.3); a
  `seeds/prog_construction_codebook.json` was therefore not shipped.

## 2. Merge-at-mint (H3a) — the design, measured

Criterion (prereg §2, integer form, in-frame):
**join iff the candidate is an induced same-head quantum and
`3·FixedCount(AntiUnify({obs.sig, q.sig})) ≥ 2·FixedCount(obs.sig)`** — the
LGG must fix ≥ 2/3 of the observation's leaf positions; unequal relation
counts anti-unify to top-level WILD (FixedCount 0) and can never join. The
RULE marks the verdict (`merge_with` = Argmax by LGG FixedCount, `merge_lgg` =
the LGG); the DRIVER applies it mechanically (copy the LGG onto the survivor,
`provenance:"merged"`, `merged_count`+1, epoch bump) — the honest
decision-in-rules / application-in-adapter split the task card sanctions
(the engine cannot `add_edge` to a Term-found node — the `sd_dedup_existing`
limitation, same class). Recognition after a join is the standalone-`Covers`
branch (`pcon_recognize_covered`): a measured engine fact is that the literal
`ShapeDecode` cover can NEVER match a part-side WILD, so wildcarded quanta
would be invisible without it.

**Naming (the §1.2-4 fix):** `pc_<snake(head-variant)>_r<relations>_q<held-count>`,
computed by the mint rule's own Terms (`SnakeCase`/`StringConcat`/
`ToJsonString`/`Count`) — never a Python namer, never signature-content
concatenation. Every name ≤ 40 chars by construction and gated; `_q` is
strictly increasing per substrate, so names are unique; a merge keeps the
survivor's name. The curriculum run's 24-quanta
`learned_code_importfrom_importfrom_…` pile is dead by construction.

## 3. The scan (H3b) — measured, with its conditions

Corpus: the P2 4099-identity emittable list
(`scope_baseline_domains_toplevel.emittable.ids`), sorted, FULL (no cut).
Resolution against today's drifted tree: **0 unresolved, 0 no-longer-emittable,
1 lineno drift** (matched by (file, qualname) per the P2 rule). 24,778
statement instances → **205 distinct statement signatures** → through the loop
on one growing substrate in **~1.5 s per run**.

| measure | prereg prediction | measured | reading |
|---|---|---|---|
| codebook size | **40–220** | **16** (3 minted + 13 merged) | **BELOW BAND — prereg miss, reported as registered:** "below 40 = the merge criterion is over-eager at this grain". What actually happens: the 2/3 criterion at depth-1 grain collapses each statement-variant FAMILY to ~one quantum (e.g. every `ProgAssignVar` → one `[pstmt, AssignVar][parg value WILD]`), and once a family quantum is wildcarded, later distinct members are `recognized_merged` via `Covers` with NO further join events. The wild-flood floor HOLDS on every merged signature (gated: ≥ ⌈2L/3⌉ leaves fixed — at most the one varying slot per relation went wild). The codebook is degenerate-compact, not degenerate-wild. |
| merge events | ≥ 30 | **18** | below the registered minimum — same root cause: joins happen once per family; after the join, `Covers` absorbs the rest for free. The registered null-reading ("dedup did the work") is half the story; the measured story is **one join per family suffices**. |
| determinism | byte-identical twin | **byte-identical** (sha256 `82c042eb…` = run 2; also stable across engine sessions and across the rule-rename commit) | H3b holds. Scan order (sorted ids) recorded in the artifact per the P0 instrument fact. |
| saturation (null-reading check, prereg §6) | — | codebook stable at 16 from corpus position 1500 of 4099; distinct signatures still arriving (161→205) but ALL absorbed by recognize/Covers | the scan scales; the curve is flat over the final 2/3 of the corpus. |

Coverage curve (codebook size vs corpus position; full table in the artifact):
250→12, 500→15, 1500→16, 4099→16.

Codebook head (name / provenance / coverage over 24,778 instances):

| quantum | prov | coverage |
|---|---|---|
| pc_prog_assign_var_r2_q0 | merged | 7522 |
| pc_prog_return_r2_q3 | merged | 4686 |
| pc_prog_if_stmt_r3_q6 | merged | 3572 |
| pc_expr_stmt_r2_q2 | minted | 3570 |
| pc_prog_for_each_r3_q1 | merged | 1987 |
| pc_prog_tuple_unpack_r3_q4 | merged | 942 |
| … (16 total; full listing with signatures in the artifact) | | |

## 4. Transition statistics (the bigram table)

Top-level label sequences per function (params excluded, prereg §1), `<s>`/
`</s>` boundaries, add-1 smoothing over V = labels ∪ {`</s>`} (|V| = 16);
`trans_logp = ln((c+1)/(prev_total+|V|))`, `prev_total` carried per row so P4
rules can score unseen pairs. 131 `ConstructionBigram` rows (nodes on the scan
substrate + the artifact table). Head by count:

| prev → next | count | trans_logp |
|---|---|---|
| return → </s> | 2875 | −0.005 |
| assign → assign | 1821 | −0.965 |
| <s> → assign | 1601 | −0.943 |
| assign → for_each | 986 | −1.578 |
| expr_stmt → </s> | 970 | −0.451 |
| assign → if_stmt | 926 | −1.641 |
| for_each → return | 881 | −0.532 |
| assign → return | **390** | −2.504 |

The registered sanity pair (assign-family → return-family) is present with
count 390 (gated).

## 5. Cross-language (the shared-hub law) — prereg §4.4, all predictions hit

The three P2 triples, read by the REAL frames (`prog_ir_emit` /
`prog_ir_rust` / `prog_ir_lua` + tree-sitter), decoded on the SAME post-scan
codebook:

- **sum_list:** python = rust = `[assign, for_each, return]` (identical label
  sequences); lua = the same with exactly ONE extra `assign` label — the
  documented ipairs-counter desugar, position and count as registered.
  **Zero new quanta minted by rust; zero by lua.**
- **max_of_two:** python = rust = lua = `[if_stmt, return]`. Zero mints.
- **count_matching:** python = rust = lua = `[assign, for_each, return]`.
  Zero mints — note lua's numeric-`for` reads as `ForEach{iter: EXTERN range}`
  vs python's `iter: VAR`, and BOTH land on the merged
  `pc_prog_for_each_r3_q1` (iter slot wilded): the merged codebook is exactly
  what makes the cross-frame identity robust at this grain.

The IR is the hub; the construction codebook is frame-blind, measured.

## 6. Gates (all green at this commit)

`tests/test_prog_constructions_migrated.py` — **10 passed, 0.14 s** (well
under the 120 s budget; `--confcutdir=.` worktree-engine discipline):
seed-loads-clean (0 skipped rules/reflexes); mint-dedup with CO-PENDING
identical observations (the engine's worst case) → exactly one quantum + both
recognized in ONE fixpoint (the recognized-after-epoch law); third-observation
recognize; near-join (LGG, WILD exactly at the differing slot, provenance
merged, floor) / far-mint both directions (different head; same head different
relation count); name-boundedness on gate quanta AND a real 30-function
mini-scan; cross-language sum_list live on one codebook; bigram sums/logp/
assign→return; artifact consistency + determinism.

Neighbor suites re-run alongside on the same engine: **208 passed** total
(`test_prog_ir_migrated` 54, `test_prog_read_python_migrated` 52,
`test_prog_read_rust_lua_migrated`, `test_prog_read_llvm_migrated`,
`test_code_synthesis_baseline_migrated` 11 — C-BATTERY/C-BENCH continuity, and
this phase touched no shared file). Full-boot check: `load_all_seeds` installs
the new seed with zero skipped rules and the `failed` seed list is
byte-identical with and without it (the 8 `local_id` failures pre-exist this
phase).

## 7. Operational facts recorded en route (honesty ledger)

1. **The engine's non-batch attempt path is SNAPSHOT-DRAIN**
   (`substrate.rs::attempt_one_rule`: collect every binding once, apply each
   WITHOUT re-checking the where). Measured here: two novel observations in
   one pass BOTH minted before either saw the other's quantum — the cold-path
   one-per-pass semantics documented in `rewrite.rs::run_rules` does NOT
   govern the seed-rule fixpoint. Fix, in-rule: `pcon_mint` carries the
   `retire_duplicate_gap` Argmin-survivor guard (the observation must BE the
   Argmin over the mint-eligible snapshot; `Eq` compares `Value::Node` by id)
   — exactly one mint per pass, by construction. Gate:
   `test_same_shape_twice_mints_exactly_one_quantum` ingests both BEFORE
   `run_rules`.
2. **Empty-codebook ShapeDecode returns `{authored: False}` and a None
   residual** (measured), which `Count()`s to 0 — indistinguishable from full
   cover. `pcon_decode`'s residual effect carries an explicit bootstrap
   fallback (`IfThenElse` over `Count(NodesOfType ShapeSignature)`): with no
   parts at all, the residual is the whole signature, so the first observation
   ever seen mints instead of fake-recognizing.
3. **Rule-name namespace:** the seed's rules are `pcon_*`, not the task card's
   suggested `pc_*` — `seeds/ls20_percell.json` already owns a rule literally
   named `pc_mint`, and a name collision with rule-name-keyed machinery (the
   daemon's per-name refresh) is avoided by construction. Minted QUANTA keep
   the `pc_` prefix (node names — a different namespace). Recorded as a
   deviation from the prereg's rule spellings; no criterion changed.
4. **Prereg misses, reported not repaired:** codebook 16 < band floor 40;
   merges 18 < 30. Both trace to one measured phenomenon the prereg §4.1
   registered as the below-band reading: the 2/3 join at depth-1 grain is
   family-collapsing (one join wildcards the family; `Covers` then absorbs
   every later member with no further join event). The criterion was NOT
   loosened/tightened post hoc.

## 8. Honest residuals

1. **The codebook is coarse — variant-grain, not idiom-grain.** 16 quanta ≈
   the statement-variant inventory; the depth-1 + 2/3-join combination erases
   most sub-variant structure (e.g. `assign-from-EXTERN` vs `assign-from-Plus`
   are one quantum). The bigram table therefore carries variant-level, not
   idiom-level, statistics. If P4's lattice needs finer proposal classes, the
   registered knobs are depth (a NEW prereg, per §1's "deepening is a future
   rung") or a stricter join threshold — either is a new measurement, not a
   retro-tweak.
2. **`recognized` via multi-part composition labels by best single part**
   (`covered_by` = Argmax by LGG fit) — a composed cover's full plan is not
   read back into the label; at this grain compositions are rare (heads are
   unique per statement), but it is an approximation, noted.
3. **Merge application is adapter-mechanical** (`apply_marked_merge`), per the
   documented engine limitation. If a future engine grows an
   add-edge-to-Term-found-node (or set-attr-on-Term-found-node) effect, the
   whole merge becomes one rule — the marked-verdict shape was chosen so that
   migration is a deletion, not a redesign.
4. **`ConstructionBigram` nodes live on the scan substrate + artifact**, not
   in a shipped seed — P4 (`ps_lattice_build`) owns deciding how they board
   the agent (seed vs re-earned at boot); premature seeding would freeze
   corpus statistics that should track the corpus.
5. **The lua ipairs counter desugar is visible at function grain** (one extra
   assign label) — a faithful reading of the desugar the P2 lua frame emits,
   registered and gated, but a place where frame-specific desugar leaks into
   the sequence statistics.
6. **Argmin-survivor serialization relies on deterministic tie-break** over a
   constant-valued snapshot (the documented `retire_duplicate_gap` semantics).
   Under the opt-in `argmin_tie` refuse-all INSTRUMENT (default OFF,
   process-global), every selector returns None and minting would halt — the
   same exposure every existing Argmin-guarded seed rule has; noted, not
   special-cased.

**P4-B addendum (2026-07-31, append-only): residual 4 CONSUMED.** The bigram
boarding decision this residual reserved for P4 is made and landed:
`domains/prog_synthesis.ensure_construction_bigrams` boards the artifact's 131
`ConstructionBigram` rows onto the agent substrate AT ENSURE TIME (not as a
shipped seed — corpus statistics keep tracking the corpus), aggregated to
statement-HEAD grain (the quantum-name → head projection is the artifact
codebook's own `signature[0][1]`; counts summed; the SAME registered add-1
formula recomputed, |V| = 14 at head grain). The P4 lattice
(`seeds/program_synthesis.json` rung 1.5, vit_step/vit_backtrace unchanged)
scores spine orderings from these rows; unseen pairs use the carried
`prev_total` exactly as §4 registered. Gate:
`tests/test_program_synthesis_migrated.py::test_boarded_bigrams_match_the_artifact_head_aggregation`
(byte-agreement with a re-derivation from the artifact). See
`PROGRAM_SYNTHESIS_P4B.md` §3. Residual 1 (variant-grain codebook) stands —
P4-B works at head grain, which the variant-grain table supports; idiom-grain
statistics remain a future prereg.
