# PROGRAM SYNTHESIS P7 — track C: the IDIOM-GRAIN chunk codebook (results)

**Date:** 2026-07-31. Companion to `PROGRAM_SYNTHESIS_PLAN.md`,
`PROGRAM_SYNTHESIS_P3.md` (saturation-at-16: the 2/3 join at depth-1 grain is
FAMILY-COLLAPSING — residual 1: "the codebook is coarse — variant-grain, not
idiom-grain"), and `PROGRAM_SYNTHESIS_P6_BATTERY.md` (H6 null: the learned
layer paid nothing CI-separated; rung mass sits on the enumerator). Track C
supplies the missing LAYER between statement-variant and whole-function:
chunks mined from the corpus + self-taught from the agent's own accepted
programs, minted as PROPOSABLE write-codebook entries. Track D owns the H7c
frozen-delta verdict on the full battery — this document reports the layer,
not the battery verdict.

Deliverables: `scripts/prog_chunk_mine.py` (the miner),
`results/prog_chunk_mine.json` (the artifact — per-chunk rows are the
baseline; every aggregate derives from them), `domains/prog_chunk_growth.py`
(mechanical adapter rim: fixed extraction walk, install, scan/pump),
`seeds/prog_chunk_growth.json` (the self-teach rules),
`tests/test_prog_chunks_migrated.py` (gates).

**Shared-prereg reconciliation:** the task card says P7-A writes the shared
`PROGRAM_SYNTHESIS_P7_PREREG.md`. At the time this track's decision rules had
to be fixed (before its own mine ran) that file did not exist yet, so the
rules below are registered HERE, in §1, written before the mine ran.
RECONCILED after the shared prereg landed (same day): its H7c registers only
the BATTERY-level hypothesis (codebook-frozen delta CI-separated on the P7
re-run, with the registered null "the learned layer is a RECOGNITION asset,
not a GENERATION asset, at this grain") and assigns the measurement to track
D — it does not constrain the mining rules, so §1 stands unmodified as the
track-C mining registration; no divergence. §5 below states what this
track's own measurements already imply for the H7c null reading.

## 1. REGISTERED BEFORE THE MINE RAN (decision rules, exact)

Everything in this section was written before `scripts/prog_chunk_mine.py`
was executed against the corpus. Deviations must be reported in §2+.

### 1.1 Corpus + condition

- Corpus: the P2/P3 4099-identity emittable list
  (`results/prog_ir_python_coverage.json`,
  `scope_baseline_domains_toplevel.emittable.ids`), SORTED, full (no cut
  unless the timebox forces a documented deterministic prefix — the P3
  prereg §6 rule; no silent caps). Re-emitted via
  `domains/prog_ir_emit.emit_prog_ir`, resolved by the P3 scan's own
  `_FileCache`/`parse_id` (imported, not copied). Unresolved /
  no-longer-emittable ids are enumerated in the artifact.
- Condition: `PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1
  OZMA_SEED_PERSIST_DISABLED=1`; worktree engine; a bare
  `substrate_rs.Substrate` is used ONLY to evaluate engine Terms
  (AntiUnify / FixedCount / Covers / StringConcat-SnakeCase naming) — the
  dedup criterion and the names are engine-computed, not Python-computed.

### 1.2 The chunk grain (fixed extraction walk, registered)

A CANDIDATE CHUNK is, per function IR and per statement block (top-level
body AND every nested block, `ProgSeq` desugar containers flattened, params
excluded — the P3 walk's own block enumeration):

- every CONTIGUOUS WINDOW of 2–4 statements of that block, and
- every single COMPOUND statement (a statement with at least one non-empty
  block field: `ProgIfStmt`/`ProgWhile`/`ProgForEach`/`ProgTryOr`) WITH its
  full body subtree — the "one level between statement and function".

Role abstraction (what makes recurrence STRUCTURAL — the grain is
DISCOVERED from what recurs, not imposed):

- variable names (binder + use: `Var.name`, `ProgAssignVar.name`,
  `ProgAugAssign.name`, `ProgForEach.var`, `ProgTupleUnpack.targets[*]`,
  `ProgTryOr.exc_var`, `Fold.var_name`/`acc_name`) → positional roles
  `v0, v1, …` by first occurrence in a deterministic walk;
- literal values (`Lit.value`) → slot tokens `slot0, slot1, …` by walk
  order (per-occurrence values are RECORDED; the minted template fills each
  slot with the corpus-MODAL joint value tuple for that chunk — a
  data-derived fill, ties broken by smallest canonical JSON, so the
  template stays spliceable/evaluable while the chunk IDENTITY stays
  slot-abstracted);
- extern names (`ProgCallExtern.name`), attribute names, enum ops, import
  modules stay CONCRETE — they are idiom identity (`len`, `append`,
  `items`), exactly what depth-1 P3 signatures erased.

Chunk identity = canonical JSON of the role/slot-abstracted statement list
(`chunk_key`). Support = total occurrence count over the corpus. The flat
relation-system form (`chunk_rels`: `["ckstmt", i, label]` head rows +
`["ck", i, path, atom]` leaf rows, sorted-key walk) is the AntiUnify/Covers
representation — positional, equal-shape-aligned, the same engine semantics
P3's loop used.

### 1.3 Support threshold (distribution-derived, registered rule)

No magic support constant. The rule, fixed here before the distribution was
seen:

- only RECURRING chunk types (support ≥ 2) are ever eligible (recurrence is
  the definition of idiom);
- **s\* = the smallest support s such that the surviving chunk-TYPE count is
  ≤ ⌈1% of the distinct recurring chunk-type count⌉** — a QUANTILE of the
  type distribution (keep the heavy tail), justified by the proposability
  constraint: every minted entry joins `ps_propose`'s per-goal Argmax scan
  of the write codebook, so the layer must stay small RELATIVE TO the chunk
  population, whatever that population turns out to be;
- floor: if that quantile keeps fewer than 8 types (the starter codebook's
  own size), s\* is lowered to the largest s keeping ≥ 8 — reported as
  "floor engaged" if it fires;
- the FULL support→type-count curve is in the artifact; the gate re-derives
  s\* from the curve (threshold honesty is testable, not quotable).

### 1.4 AntiUnify dedup (measured, not blindly re-imposed)

P3 measured that the 2/3 MDL join at depth-1 grain collapses each
statement-variant family to ~one quantum. The registered treatment here:

- candidate joins are computed ONLY within groups of identical label
  sequence AND identical relation count (unequal counts anti-unify to WILD
  — the P3 fact; label-sequence identity is this grain's head filter);
- join criterion measured at BOTH 2/3 (`3·FixedCount(AntiUnify) ≥
  2·FixedCount(concrete)`) and 5/6 (`6·FixedCount(AntiUnify) ≥
  5·FixedCount(concrete)`), greedy by descending support (survivor keeps
  its concrete template; LGG becomes the entry's `chunk_rels`; supports
  sum), the engine's own AntiUnify/FixedCount via `evaluate`;
- **adoption rule:** adopt 2/3 UNLESS it reproduces the P3 collapse
  signature at this grain — i.e. unless among label-sequence families with
  ≥ 3 kept members pre-join, the MEDIAN post-join member count under 2/3
  is 1. If it is, adopt 5/6 and report both columns. Either way both join
  counts and per-family pre/post counts are in the artifact.

### 1.5 Minting + proposability (the entry contract)

Each surviving chunk → `ShapeSignature{kind:'code_write_construction'}`
(the ONLY kind `ps_propose` reads — measured in
`seeds/program_synthesis.json`: eligibility = kind + a `trigger_tokens`
member ∈ goal tokens; winner = Argmax by the entry's trigger-token count),
with: `provenance:'chunk_mined'`, `chunk_key`, `chunk_rels`,
`ground_template` (mode `code_write_stmts`, role-named stmts, modal slot
fills, args = the chunk's FREE roles in first-read order), `spine: 1.0`
(routes through the P4-B lattice), `support`, and a bounded ENGINE-computed
name `ck_<snake(first label)>_n<stmts>_q<idx>` (StringConcat/SnakeCase/
ToJsonString via `evaluate` — the P3 naming law; regex + ≤ 40 gated).

Trigger vocabulary (registered, honesty clause): derived mechanically from
the chunk's own structure — statement-head words (strip `Prog`, camel-split,
uppercase), extern-name words, AugAssign op words — minus tokens that
`code_writing._STOPWORDS` makes unmatchable. There is NO NL-request corpus
paired with the code corpus, so corpus co-occurring request tokens are NOT
available; this derivation is therefore expected to be WEAK as NL cueing
(a chunk that can't be cued still serves descent's hole-fill — the task
card's own honesty clause). Chunks whose label sequence contains DUPLICATE
labels get `trigger_tokens: []` (not cueable): the P4-B ordering lattice
connects only DISTINCT labels (`_decode_order`'s documented contract), so a
duplicate-label spine cannot decode its own order — minted for hole-fill,
excluded from cueing by construction, documented residual.

### 1.6 Self-teach (the refactor tier, graph-decided)

`seeds/prog_chunk_growth.json` — the decisions are rules; the fixed
extraction walk is the adapter (the P3 decision-in-rules /
application-in-adapter split, task-card-sanctioned):

- `ckg_mark_scan` (RULE): an accepted `Program{provenance:
  'program_synthesis'}` (matched via its goal's `accepted_program` edge) is
  marked for chunk scan, once (`ck_scan_marked`);
- adapter (`scan_marked_programs`): for each marked Program, the SAME fixed
  extraction walk of §1.2 over its IR → `Observation{kind:'prog_chunk',
  pk_status:'pending'}` rows (deduped by `chunk_key` at the I/O boundary,
  occurrences tallied), then `ck_chunks_scanned` stamped — mechanical;
- `ckg_recognize` (RULE): a pending chunk observation COVERED by a held
  entry (`Covers(entry.chunk_rels, obs.chunk_rels)` — pattern-side WILD
  matches, so AntiUnify-merged entries recognize their variants) →
  `recognized`, `covered_by` = most-specific coverer (Argmax by
  FixedCount);
- `ckg_mint` (RULE): pending + NOT-Exists cover + the `pcon_mint`
  Argmin-survivor serializer (the snapshot-drain engine fact) → mints the
  entry IN-RULE (name Term-computed `ckt_<snake(head)>_q<n>`; attrs copied
  off the observation's own recorded facts), `provenance:'self_taught'`,
  and bumps `Agent.write_codebook_epoch` in-rule (the established
  three-line epoch move, `code_write_growth`'s counter).

No edit to `seeds/program_synthesis.json` / `domains/prog_synthesis.py`
(P7-A's files): the rule only READS the Program nodes that seed's rules
produce.

### 1.7 Gates (registered)

Mining determinism (twin-run byte-identical artifact); threshold honesty
(s\* re-derived from the artifact's own curve); install dedup (install twice
→ no duplicate entries); seed loads clean; PROPOSABILITY end-to-end (a
synthetic request built from a high-support chunk's own trigger tokens +
ProgEval-derived example rows: starter-codebook control does NOT accept at
rung 1, chunk-installed arm accepts at rung 1 — through
`domains/prog_synthesis.py`'s public entry, synthesis seed unmodified);
SELF-TEACH end-to-end (a 2-statement accepted program with exactly ONE
candidate chunk → exactly one `self_taught` entry, deduped on a second
identical accept, epoch bumped); name boundedness; no-Python-decision
source audit. Neighbor suites re-run: prog_constructions (10),
program_synthesis (as it stands under P7-A's concurrent edits — reported as
seen), battery gate (11), baseline (11). Budget ≤ ~120 s.

---

*(§2+ below this line were written AFTER the mine ran.)*

## 2. The mine — measured (artifact: `results/prog_chunk_mine.json`)

### 2.1 Scope + the support distribution

4099/4099 ids resolved and emitted (0 unresolved, 0 no-longer-emittable, 4
lineno drifts — the (file, qualname) rule absorbed them). **35,267 candidate
chunk instances → 30,177 distinct chunk types** (role/slot-abstracted), of
which **2,096 recur** (support ≥ 2) — the population is overwhelmingly
singleton, exactly the heavy-tail shape the §1.3 quantile rule anticipated.
Registered rule applied: target = ⌈1% · 2096⌉ = 21; **s\* = 24** (smallest s
keeping ≤ 21 types; keeps 19); floor NOT engaged. Full curve in the
artifact; the gate re-derives s\* from it.

**Determinism:** twin full runs byte-identical (sha256 `6f2dee2a…` both).
Lesson recorded en route: the first twin run differed ONLY in a wall-clock
`elapsed_s` field accidentally inside the canonical blob — moved out of the
determinism claim (the P3 `date` rule); no chunk content ever differed.

### 2.2 Dedup (§1.4 applied) + the family-collapse reconciliation

19 kept types → AntiUnify (engine Term via evaluate) within identical
label-sequence + relation-count groups: **2/3 criterion: 4 joins → 15
survivors; 5/6: 3 joins → 16.** Multi-member (≥3) families pre-join: 2
(`ProgIfStmt` ×9, `ProgAssignVar + ProgAssignVar` ×4); median post-join
member count under 2/3 = **4.5, not 1** → the registered adoption rule
adopts **2/3**, and the P3 collapse signature does NOT reproduce.

**The headline reconciliation vs P3:** at depth-1 grain the 2/3 join
collapsed every statement-variant family to ~one quantum (`ProgIfStmt` → the
single `pc_prog_if_stmt_r3_q6`). At idiom grain the SAME criterion keeps
**6 distinct `ProgIfStmt` single-compound chunks** (None-guard-return,
not-guard-return, guard-continue ×2, membership-continue, guard-assign) and
**3 distinct `assign+assign` window chunks** — the deep structure
(condition kind, body statement, extern identity) is exactly what depth-1
signatures erased, and it carries the discrimination. Idiom grain ESCAPES
the family collapse, measured: chunks per first-statement variant =
`ProgAssignVar` 8, `ProgIfStmt` 7 (P3: 1 per variant).

### 2.3 What survived (15 chunks) + the cueability amendment (deviation)

Grain distribution: compound_1 ×6, window_2 ×6, window_3 ×2, window_4 ×1
(the discovered grain is real — both window and compound forms survive; no
window_4 dominance, no compound monopoly). Support range 24–166. The top
chunks are THIS corpus's true idioms: `if v0 is None: return None` (166),
`if not v0: return None` (142), `v = <x>; break` (72), paired
`getattr(...)`-resolve assigns (62/56), `sub.node(n)["attrs"]` reads (24) —
adapter-code guard/resolve idioms, because the corpus IS adapter code.

**Registered-rule amendment (recorded as a deviation, made after seeing the
mine):** §1.5 registered trigger derivation with the duplicate-label
exclusion only. The mine surfaced two further classes that can NEVER verify
as whole-function proposals — templates calling externs outside
`NATIVE_ORACLES` (`getattr`, `sub.node`, … trap on every row) and templates
with a bare top-level `break`/`continue` (traps outside a loop). Cueing
those is pure decoy mass (they consume CEGIS attempts and can never
accept), so cueability gained two more FIXED structural checks
(`cue_exclusion_reason`: `extern_outside_native_oracles`,
`bare_loop_control`). This narrows CUEING only — all 15 chunks are minted
and hold their `derived_tokens` in the artifact (honesty: the reader sees
what the triggers would have been); non-cueable chunks are hole-fill data
for descent. Result: **2/15 cueable** (`ck_prog_if_stmt_n1_q0`,
`ck_prog_if_stmt_n1_q1`, both triggered {IF, STMT}). The §1.5 honesty
clause was the prediction; 2/15 is its measurement: with no NL-request
corpus paired to the code corpus, structural trigger derivation is weak —
the chunk layer's cueing surface is thin, its hole-fill surface is the 15.

## 3. Proposability + self-teach — the end-to-end gates, measured

- **Proposability (headline):** request `"write a function guard_none that
  yields nothing if the input is missing"` (token IF; no starter/spine
  trigger) + 3 ProgEval-consistent rows. CONTROL (starter codebook only):
  **gapped**, `enumerate_failed`, rung-1 never reached (no trigger match;
  the enumerator cannot produce the None-typed rows). CHUNK ARM
  (`install_mined_chunks` then the SAME public entry
  `synthesize_from_request`, synthesis seed unmodified): **accepted,
  attempt 1, rung 1** (`ps_rung_codebook=1.0`, lattice 1.0, enumerate
  never), construction `ck_prog_if_stmt_n1_q0` (support 166), held-out
  rows correct via the reflected subgraph. Honest scope: the guard idiom's
  whole-function behaviour is constantly None, so the rows cannot
  discriminate among the two cueable chunks (both would verify) — this is
  a MECHANISM gate (propose → lattice → splice → verify at rung 1 where
  the starter gapped), per the standing synthetic-mechanism ≠ benchmark
  rule; the capability question is track D's.
- **Self-teach:** a 2-statement accepted program (`t = a + b; return t`,
  via a gate spine template — chosen because its IR has EXACTLY ONE
  candidate chunk) → `ckg_mark_scan` marks, the adapter scans, `ckg_mint`
  mints **exactly one** entry: `ckt_prog_assign_var_q10`, provenance
  `self_taught`, bounded name, `write_codebook_epoch` 0→1 in-rule. A second
  identical accept: observation **recognized** (`covered_by` = the minted
  name), zero new entries, zero epoch bump. Foreign Programs (provenance ≠
  `program_synthesis`) never enter the flow (gated).

## 4. Gates + neighbor suites (all at this commit, worktree engine)

`tests/test_prog_chunks_migrated.py` — **11 passed, 0.17 s**: seed loads
clean (3 rules, 0 skipped); twin-run determinism recorded; totals derive
from rows; threshold honesty (s\* re-derived from the curve); dedup
adoption rule re-applied + the family-collapse assertion; install
idempotent + names bounded (`^ck_…_n\\d+_q\\d+$` ≤ 40;
`^ckt_…_q\\d+$` ≤ 40); proposability control + chunk arms; self-teach
mint-exactly-one + dedup + foreign-program guard; no-Python-decision source
audit. Full-boot glob smoke: the seed parses + topo-orders in
`boot_all._read_seeds` (634 seeds).

Neighbor suites, same engine, same moment (final joint rerun — 59 passed,
1.7 s total): `test_prog_constructions_migrated` **10 passed**;
`test_program_synthesis_migrated` **16 passed** (as it stood under P7-A's
concurrent edits — the suite grew 15→16 during this track's build and its
`read_goal` already carries a `descend` rung; reported as seen);
`test_prog_synthesis_battery_migrated` **11 passed**;
`test_code_synthesis_baseline_migrated` **11 passed**. This track's
footprint is exactly its six owned files (P7-A's
`domains/prog_synthesis.py` / `seeds/program_synthesis.json` / descent
tests untouched by this track).

## 5. What this already says about H7c (track D owns the verdict)

The layer exists and is proposable, but its cueing surface on the 125-task
battery is predictably near-zero: the two cueable chunks trigger on
{IF, STMT}, and the battery's integer-arithmetic requests rarely carry
those tokens (and where they do, the guard idioms' semantics won't verify
against arithmetic rows). The mined mass (13/15 non-cueable chunks — the
getattr-resolve and guard fragments) is HOLE-FILL content for track A's
descent, not whole-goal proposals. Expectation to carry into the H7c
re-run, stated before track D measures: **at THIS corpus↔battery domain
pairing, the chunk layer should move the battery mainly through descent's
hole-fill (if at all), not through rung-1 cueing** — if the delta stays
null, the registered H7c null reading applies with a sharper cause: the
corpus's idioms (graph-adapter guards) and the battery's domain (integer
arithmetic) barely overlap; chunk mining transfers idioms, not domains.

## 6. Honest residuals

1. **Trigger derivation is weak by construction** (2/15 cueable; head-word
   grain). A paired NL-request↔code corpus would let triggers come from
   co-occurrence; none exists here. Recorded, not patched.
2. **Corpus↔battery domain mismatch** (§5): the mined idioms are
   None-guards and getattr-resolve chains, not arithmetic spines. The
   layer's generation value at this pairing rides on descent hole-fill.
3. **Spine order is the lattice's, not the chunk's:** an accepted chunk
   proposal is spliced in the corpus-bigram order `vit` decodes, not the
   chunk's stored statement order. For the surviving cueable chunks (single
   statements) this is vacuous; a multi-statement chunk whose internal
   order contradicts global bigram statistics would splice wrong — the
   duplicate-label exclusion catches the worst case, the general case is a
   known residual of reusing the P4-B lattice unmodified.
4. **The proposability gate's rows are non-discriminating** (constant-None
   idiom): mechanism proven, capability not claimed (§3, standing rule).
5. **Slot fills are corpus-modal joint tuples** — a proposed template
   carries the modal literals; per-slot hole-fill under descent (using the
   slot identity retained in `chunk_key`/`chunk_rels`) is track A's seam,
   not exercised here.
6. **Support counts overlapping windows:** a 3-window's support also feeds
   its 2-sub-windows' counts; the threshold is applied per type, so nested
   chunks can co-survive (window_3 survivors alongside their window_2
   parts). MDL-style containment discounting is a future rung, reported
   not silently applied.
7. **Self-taught entries inherit the observation's occurrence count as
   `support`** (1 for a single accept) — commensurate with mined supports
   only in units, not in scale; consumers should read provenance.
8. **`ckg_recognize`'s Covers is positional** (equal relation counts): a
   self-taught near-variant of a held chunk with a DIFFERENT shape mints
   its own entry rather than joining — merge-at-mint at chunk grain (the
   P3 H3a move) was deliberately NOT re-imposed here; §1.4's measurement
   showed only 4 joins at corpus scale, so the added rule mass isn't yet
   paid for. Revisit if self-taught entries proliferate.
