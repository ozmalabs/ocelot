# PROGRAM SYNTHESIS P3 — PRE-REGISTRATION (merge-at-mint + the construction scan)

**Written BEFORE the scan runs and BEFORE the loop seed / signature module are
built** (plan §6.6: "the anti-unify merge gets its own small prereg BEFORE the
big scan"; PROGRAM_SYNTHESIS_PREREG.md §5 H3a/H3b). Companion to
`PROGRAM_SYNTHESIS_PLAN.md` §4-P3, `PROGRAM_SYNTHESIS_P1_NOTES.md` (the IR),
`PROGRAM_SYNTHESIS_P2_PYTHON.md` (the emitter + the 4099-identity corpus in
`results/prog_ir_python_coverage.json`). Everything below is registered before
measurement; deviations must be recorded in `PROGRAM_SYNTHESIS_P3.md`.

- **Corpus:** the 4099 `scope_baseline_domains_toplevel.emittable.ids` of
  `results/prog_ir_python_coverage.json`, re-emitted via
  `domains/prog_ir_emit.emit_prog_ir`, processed in SORTED id order (the P0
  instrument fact: scan order is part of every codebook claim). Tree drift
  since P2 is expected (sibling agents edit `domains/`); ids that no longer
  resolve or no longer emit are ENUMERATED in the artifact, never silently
  dropped.
- **Condition:** bare `substrate_rs.Substrate` + one Agent node + the
  `prog_construction_loop` seed (worktree engine, `--confcutdir=.`),
  `OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1`. No full seed boot: the loop
  is self-contained (kind-guarded), and the frozen `shape_decode_loop` seed
  is untouched and unloaded.

## §1 — The observation grain (fixed extraction, registered)

**Statement grain.** One signature per statement (params excluded — a
`ProgDefFnParam` is the signature row, not a body construction, and the rust
reader does not emit them). A signature is a relation-system (list of relation
tuples, native nested lists — the `code_constructions` convention at IR grain):

- head first: `["pstmt", <variant>]` (`ProgAssignVar`, …, or `ExprStmt` for a
  bare expression statement);
- one `["parg", <field>, <abskind>]` per expression field, **depth 1**:
  `abskind` = `VAR` | `LIT` | `EXTERN` (ProgCallExtern, name abstracted) |
  `NONE` | the node's `type`. Identifiers, literal values, extern names,
  attribute names are NEVER in a signature — shape, not content;
- `["pop", <op|kind>]` for structural enum scalars (AugAssign op, LoopCtl kind);
- `["parity", <field>, <n>]` for structural arities (TupleUnpack targets —
  in-frame integer);
- `["pblock", <field>]` PRESENCE-ONLY per non-empty block field (body/then/
  orelse/handler). Block contents are NOT in the parent's signature — the
  Omniglot run-5 lesson (finer base grain FRAGMENTS; detail lives one level
  down) applied to code. Nested statements are their own observations
  (recursive walk, bare `ProgSeq` desugar containers flattened).

Depth is 1, registered here; deepening is a future rung, not a scan-time knob.

**Function grain** (the character-composition precedent, one level up): the
ordered sequence of statement-grain construction LABELS of the top-level body
(params excluded, desugar `ProgSeq` flattened). This is the bigram corpus and
the P4 lattice's vocabulary; it is not itself decoded this phase.

**Mechanical dedup:** identical canonical-JSON signatures are ONE Observation
with an `occurrences` tally (frequency counting at the I/O boundary — the
distributional-stats precedent). The rules never see two identical pending
observations from the driver; the same-shape-twice gate exercises that case
explicitly without the driver.

## §2 — Merge-at-mint (the H3a design, exact)

At the mint point (decoded, non-empty residual, no covering quantum), the rule
set decides JOIN vs MINT against every existing **induced** (`induced == 1`)
`ShapeSignature{kind:'prog_construction'}` quantum:

- **Candidate filter:** head relation identical
  (`IndexAt(sig,0) == IndexAt(obs.signature,0)` — a merged quantum never
  crosses statement variants), and
- **MDL join criterion (integer form, in-frame):**
  `3 · FixedCount(AntiUnify({residual_sig, quantum_sig})) ≥ 2 · FixedCount(residual_sig)`
  — the least-general generalization must FIX at least 2/3 of the leaf
  positions of the (fully-concrete) observation. Unequal relation counts
  anti-unify to WILD (FixedCount 0) and therefore never join.
- **JOIN** (`pc_mark_merge`, a rule): the winner is `Argmax` by
  `FixedCount(AntiUnify(...))` over the qualifying quanta; the rule writes the
  verdict on the Observation (`merge_with` = winner's name, `merge_lgg` = the
  LGG, status `merge_marked`). The scan driver applies the marked merge
  MECHANICALLY — copy `merge_lgg` onto the winner's `signature`, stamp
  `provenance:"merged"`, increment `merged_count`, bump
  `Agent.prog_codebook_epoch` — **one marked merge per `run_rules` round, in
  ascending Observation-node order** (a second mark against the same quantum
  must re-decide against the WIDENED signature, so application is serialized;
  decision in rules, application in the adapter — the documented
  `sd_dedup_existing`-class split, task-card-sanctioned).
- **MINT** (`pc_mint`, a rule) only when no covering quantum exists AND no
  candidate passes the join criterion: the quantum is the observation's own
  signature, `induced: 1`, epoch bumped in-rule.
- **Recognition after a join:** a wildcarded (merged) signature is invisible
  to the literal `ShapeDecode` cover (WILD on the part side never matches —
  measured engine fact), so the loop carries the standalone-`Covers` branch
  `pc_recognize_covered`: `Covers(pattern = quantum.signature, instance =
  obs.signature)` (pattern-side WILD matches; most-specific covering quantum
  by `FixedCount` wins) → `recognized_merged`.

**Registered floor (wild-flood guard):** because every join is tested against
a fully-concrete observation of the same relation count, ANY surviving merged
signature fixes ≥ ⌈2L/3⌉ of its L leaf positions. A quantum below that floor
in the final codebook is a bug, gated (`test_merged_signatures_keep_the_floor`
condition folded into the merge gates).

## §3 — Naming (bounded, Term-computed)

`name = StringConcat("pc_", SnakeCase(<head variant>), "_r", <relation count>,
"_q", <count of held prog_construction quanta at mint>)` — computed by the
mint RULE's Terms (SnakeCase/StringConcat/ToJsonString/Count), never by a
Python namer. Properties, registered as gates:

- **Bounded:** every name matches `^pc_[a-z0-9_]+_r[0-9]+_q[0-9]+$` and
  `len(name) ≤ 40` — no name grows with signature size or scan length
  (the §1.2-4 unbounded-concatenation defect, killed by construction).
- **Unique:** the `_q<count>` discriminator is strictly increasing across
  mints on one substrate (the cold-path engine applies one mint per pass);
  a merge keeps the surviving quantum's name.

## §4 — Predictions (registered before the scan)

1. **Codebook size band for the 4099-id scan: 40–220 quanta.** Reasoning:
   23 statement variants × observed depth-1 expression kinds, cut by the
   2/3-join (which collapses same-variant families differing in one slot)
   and by multi-part composition cover. Below 40 = the merge criterion is
   over-eager (check the floor gate); above 220 = the depth-1 grain is
   fragmenting and the criterion is too strict — either way the number is
   reported against this band, not re-derived.
2. **Merges happen at corpus scale:** ≥ 30 join events (`merged_count` sum)
   across the scan. Null reading: < 30 means depth-1 signatures are already
   almost-always exact-duplicates — the dedup did the work and merge-at-mint
   was unnecessary at this grain; report, do not widen the criterion post hoc.
3. **Determinism:** two fresh scans over the same sorted corpus yield
   byte-identical codebook + bigram artifacts (timestamps excluded). This is
   H3b's "earned deterministically" and the P0 scan-order fact honored.
4. **Cross-language (the shared-hub law):** after the python scan, the P2
   sum-of-list-loop triple decodes into the SAME codebook: the rust read
   mints ZERO new quanta; the lua read mints ZERO new quanta (joins allowed
   — the documented `ipairs` counter desugar `k += 1` is a near-shape of the
   python accumulate); the python top-level label sequence (params stripped)
   EQUALS the rust one, and the lua sequence is the python one with the one
   extra assign-family label from the ipairs desugar (position and count
   named in the gate).
5. **Bigrams:** counts over consecutive top-level label pairs with `<s>`/`</s>`
   boundaries; add-α smoothing with **α = 1** over the observed label
   vocabulary V: `trans_logp(prev→next) = ln((c(prev,next)+1)/(c(prev,·)+|V|))`
   (each node also carries `prev_total` so P4 rules can score unseen pairs).
   Registered sanity: some assign-family → return-family pair has count > 0
   (the sequential-computation shape is corpus-dominant per P0).

## §5 — Gates (tests/test_prog_constructions_migrated.py)

1. seed loads via `load_seed_manifest` with `rules_skipped == []` and
   `reflexes_skipped == []`;
2. mint-dedup: the same shape observed twice → EXACTLY ONE quantum, second
   observation `recognized` with `covered_by` = the minted name (this is also
   the recognized-after-epoch law: mint → in-rule epoch bump → `pc_redecode`
   re-arm → literal re-decode covers — one `run_rules` fixpoint);
3. merge both directions: two NEAR shapes per §2 → one quantum, `provenance
   "merged"`, WILD exactly at the differing slot, second obs
   `recognized_merged`; two FAR shapes (different heads; same head with
   different relation counts) → two quanta;
4. name-boundedness per §3 on every quantum the gates + a 30-function
   mini-scan produce;
5. cross-language per §4.4 (skips honestly without tree_sitter_rust/lua);
6. bigram sanity per §4.5 (counts sum to sequence mass, logp finite);
7. neighbor suites stay green: `test_prog_ir_migrated`,
   `test_prog_read_python_migrated`, `test_prog_read_rust_lua_migrated`,
   `test_code_synthesis_baseline_migrated` (C-BATTERY/C-BENCH continuity).

## §6 — Scan protocol facts (registered)

Batched: emit → dedup-ingest (≤ 200 new distinct observations per batch) →
`run_rules` → apply marked merges one-per-round to quiescence → tally
(sig_key → label, occurrences, per-quantum coverage) → REMOVE the batch's
Observation nodes (mechanical working-set GC — the flow-retire precedent; the
codebook, the epoch, and the tallies persist). Coverage curve = codebook size
after each batch vs corpus position. If the full 4099 exceeds the time budget,
a documented deterministic PREFIX of ≥ 1000 sorted ids is taken and the cut is
recorded in the artifact (`scan_scope.cut`) — no silent caps. **Null reading
(prereg §5):** if dedup/merge cannot hold the codebook bounded under the full
corpus (mints still arriving at a constant rate in the final quartile of the
coverage curve), the scan does not scale to external corpora; the curve is the
result.
