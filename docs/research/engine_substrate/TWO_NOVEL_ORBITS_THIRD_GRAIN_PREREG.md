# Two-novel-orbits gate, third grain (`prog_chunk_growth`) — PREREG

**Status: PREREG. Registered before the test file was written.** Worktree
`/home/matt/ocelot-two-novel-orbits-third-grain`, branch
`two-novel-orbits-third-grain`, from `main` at `3719b50` (`Merge
gamma-collapse-algorithm: Type-1 residual capture + gated proposal, GO`,
verified with `git log --oneline -1 main` immediately before `git worktree
add`). Engine `c086d83ad070` (`sha256sum
runners/dsl/python/substrate_rs/_native.abi3.so`), coherence-probed
(list/tuple identity preserved and distinguishable) and
`test_engine_provenance_migrated.py` green (10/10) in this worktree before
any file was touched. Results go in
`TWO_NOVEL_ORBITS_THIRD_GRAIN_RESULTS.md`.

**Environment note (not a code change):** `results/prog_construction_scan.json`
and `results/prog_chunk_mine.json` are gitignored generated artifacts
(`.gitignore:25`, `results/*` with explicit carve-outs for exactly these two
paths) that exist on disk in the primary checkout but are not part of git
history, so a fresh worktree does not have them. `psy.ensure_program_synthesis`
/ `pcg.install_mined_chunks` read them at import/boot time.
`tests/test_prog_chunks_migrated.py` fails 9/11 without them (`FileNotFoundError`)
and passes 11/11 once they are copied in. Copied both files from
`/home/matt/ozmadev/ocelot/results/` into this worktree's `results/` verbatim
(no edits) before writing this document — this is data, not code, and every
existing gate in this file already depends on it being present.

**Charter, quoted precisely, from `TWO_NOVEL_ORBITS_GATE_RESULTS.md` §"Third
grain considered and set aside":** *"`prog_chunk_growth`'s
`code_write_construction` codebook (`ckg_mint`). Its naming law is a
strictly-increasing count discriminator (`ckt_<snake(head)>_q<count>`), not
content-derived, so it is not exposed to the SAME collision mechanism either
— but confirming that (or finding otherwise) would require constructing a
second genuinely-distinct `synthesize_from_request` fixture whose extracted
`chunk_rels` differ in KIND, which means reading the chunk-extraction walk
(`domains/prog_chunk_growth.py`'s `chunk_candidates`) closely enough to build
a second spine template — real fixture work, not a cheap reuse of
`_boot_selfteach`'s existing one-shape gate."* This rung does that reading
and that fixture construction, then runs the same four assertion classes
(AR1-AR4 shape) the primary/AR5 gates already use, mirroring
`tests/test_two_novel_orbits_gate_migrated.py`'s structure.

**Methodology gap being closed, restated, one grain over (from
`DEDUP_ADOPTION_SWEEP_RESULTS.md`, quoted in both prior PREREGs):** *"no
existing test in the tree presents two novel orbits to one graph."*
`tests/test_prog_chunks_migrated.py::test_self_teach_mints_exactly_one_then_dedups`
(`_boot_selfteach`, line 292) presents exactly ONE novel chunk shape (plus
its own repeat) to one graph — never a SECOND, structurally distinct novel
chunk in the same session. This rung is the missing case at this grain.

---

## Reading `chunk_candidates` — what it would take to get two DIFFERENT-KIND
fixtures (the task's own step 1)

`domains/prog_chunk_growth.py::chunk_candidates` (`:415-426`) walks every
statement block of a function IR (`_blocks`, `:366-382`, top level + nested,
`ProgSeq` flattened) and emits, per block:

* one `chunk_record` per contiguous WINDOW of 2, 3, or 4 statements
  (`_WINDOW_SIZES = (2, 3, 4)`, `:72`) — this is what `_boot_selfteach`'s
  `COMBINE_TMPL` produces: a flat 2-statement window
  (`ProgReturn` + `ProgAssignVar`), giving `chunk_record`
  `labels = ["ProgAssignVar", "ProgReturn"]` (order depends on the accepted
  IR's own statement order, decided by the write-codebook's bigram lattice,
  not authored order) and a `rels` list of flat `["ckstmt", i, label]` +
  `["ck", i, path, atom]` rows, `i` in `{0, 1}`.
* one `chunk_record([s])` per COMPOUND statement (`_is_compound`, `:384-388`
  — `s.type in ("ProgIfStmt", "ProgWhile", "ProgForEach", "ProgTryOr")` with
  a non-`None` block field) — a completely different code path through
  `chunk_record`: `labels = [<the one compound type>]`, `i == 0` only, and
  the `rels` walk descends INTO the compound's own block fields
  (`.cond`/`.then`/`.orelse` for `ProgIfStmt`) rather than across a flat
  statement sequence.

These two candidate SHAPES (`_WINDOW_SIZES` vs `_is_compound`) are the two
structurally distinct code paths `chunk_candidates` has; a fixture whose
extracted `chunk_rels` differ in KIND, not just content, is a fixture that
lands in different branches of this function — a multi-statement window vs a
single compound statement.

**Fixture 2 selected: a single `ProgIfStmt`.** A function whose entire
top-level body is one `ProgIfStmt` with non-empty `then`/`orelse` (each a
lone `ProgReturn`, not a `ProgSeq`) has EXACTLY one candidate chunk: the top
block has `n=1` statements, so no window of size ≥2 fits
(`range(0, n - w + 1)` is empty for every `w` in `(2,3,4)`); the one
statement IS compound, so `_is_compound` fires once; the nested `then`/
`orelse` blocks each have `n=1` and contain no compound statement, so no
further candidates are produced there either. This mirrors
`_boot_selfteach`'s own "exactly ONE candidate chunk" design bar with a
DIFFERENT-KIND chunk instead of a differently-CONTENTED one.

**Registered fixtures (exact JSON, reproduced from this document's own
pre-registration probe — `scripts/` not used; probe run directly against
this worktree before this document was written, per house discipline):**

```python
COMBINE_REQ = "write a function combine that yields the combine of a and b"
COMBINE_ROWS = [({"a": 1, "b": 2}, 3), ({"a": 4, "b": 5}, 9), ({"a": 0, "b": 0}, 0)]
COMBINE_TMPL = {   # UNCHANGED from tests/test_prog_chunks_migrated.py
    "desc": "returns a and b combined", "mode": "code_write_stmts",
    "args": ["a", "b"],
    "stmts": [{"type": "ProgReturn", "value": {"type": "Var", "name": "t"}},
              {"type": "ProgAssignVar", "name": "t",
               "value": {"type": "Plus", "items": [
                   {"type": "Var", "name": "a"}, {"type": "Var", "name": "b"}]}}]}

GUARD_REQ = "write a function guardpos that yields pos or nonpos for v"
GUARD_ROWS = [({"v": 5}, "pos"), ({"v": -1}, "nonpos"), ({"v": 0}, "nonpos")]
GUARD_TMPL = {     # NEW -- a single compound ProgIfStmt, not a window
    "desc": "returns pos or nonpos by sign", "mode": "code_write_stmts",
    "args": ["v"],
    "stmts": [{"type": "ProgIfStmt",
               "cond": {"type": "Gt", "a": {"type": "Var", "name": "v"},
                        "b": {"type": "Lit", "value": 0}},
               "then": {"type": "ProgReturn",
                        "value": {"type": "Lit", "value": "pos"}},
               "orelse": {"type": "ProgReturn",
                          "value": {"type": "Lit", "value": "nonpos"}}}]}
```

Boarded as two `ShapeSignature{kind:'code_write_construction'}` spine
templates on the SAME graph (`gate_combine_spine` / `gate_guard_spine`, each
its own unique `trigger_tokens` so `synthesize_from_request`'s rung-1
codebook match is unambiguous — the same discipline `_boot_selfteach` uses
for `COMBINE`).

**Already measured, off a fresh probe of exactly this fixture pair, before
this document was written (`chunk_candidates` applied to the REAL accepted
IR of each, not the authored template):**

```
COMBINE ir stmts (post rung-1 accept, bigram-ordered): AssignVar, Return
COMBINE n_candidates=1  labels=['ProgAssignVar', 'ProgReturn']  n_stmts=2

GUARD   ir stmts: one ProgIfStmt (cond=Gt(v,0), then=Return('pos'), orelse=Return('nonpos'))
GUARD   n_candidates=1  labels=['ProgIfStmt']  n_stmts=1
```

The two `chunk_key`/`chunk_rels` differ in KIND, not just content: COMBINE's
relation system has two `ckstmt` head rows (`i=0,1`, a flat sequence);
GUARD's has one `ckstmt` head row (`i=0`) whose leaf paths descend through
`.cond.a`/`.cond.b`/`.then.value`/`.orelse.value` (a nested compound), a
different shape of relation system entirely — not reachable by `Covers` in
either direction (`Covers` matches on the SAME `i`-indexed row set; COMBINE's
`i=1` row alone rules out any accidental subsumption).

---

## AR1 — the primary scenario, registered exactly

**Grain:** `ShapeSignature{kind:'code_write_construction'}` self-taught mint
(`ckg_mint`) + `Observation{kind:'prog_chunk'}` recognize (`ckg_recognize`),
`seeds/prog_chunk_growth.json`.

**Fixture:** the two fixtures above, presented **in sequence to the same
graph** (one `boot()` + `pcg.ensure_chunk_growth` + both spine templates
boarded once), each via its own `psy.synthesize_from_request(...)` accept +
`pcg.chunk_pump(...)` call — mirroring how a real session accepts one
program, then another, not one big batch:

```
A  = COMBINE (novel window chunk)
B  = GUARD   (novel compound chunk -- different KIND)
A2 = COMBINE (repeat)
B2 = GUARD   (repeat)
```

**Already measured (this document's own probe, reproduced below verbatim —
the RESULTS doc must match this exactly via the committed test):**

```
baseline write_codebook_epoch: 0.0
A_combine          dt=0.0036s entries=1 epoch=1.0 obs_statuses=['minted']
B_guard            dt=0.0031s entries=2 epoch=2.0 obs_statuses=['minted', 'minted']
A_combine_repeat   dt=0.0039s entries=2 epoch=2.0 obs_statuses=['minted', 'minted', 'recognized']
B_guard_repeat     dt=0.0035s entries=2 epoch=2.0 obs_statuses=['minted', 'minted', 'recognized', 'recognized']
total wall: 0.0144s

final entries (names, from a full run including the starter codebook so the
count discriminator's baseline is whatever ensure_write_codebook already
boarded -- the exact numeral is NOT pinned, only DISTINCTNESS is):
  ckt_prog_assign_var_q<N>   provenance=self_taught  chunk_key=<COMBINE's>
  ckt_prog_if_stmt_q<N+1>    provenance=self_taught  chunk_key=<GUARD's>
```

**This is the predicted shape, not a surprise: 2 entries, not 1 (no stall on
the second, differently-KINDED novel item) and not 3+ (no over-mint on
either repeat).** Consistent with the charter's own prediction that this
grain's naming law is not exposed to the collision mechanism the other two
grains were fixed for.

## AR2 — the stall assertion, registered exactly

**Bar:** after EACH of the four steps, the just-presented request's `status`
is `"accepted"` (`synthesize_from_request`'s own return, checked individually
— not deferred to the end) AND `pcg.chunk_pump` leaves that step's
observation at a terminal `pk_status` of `"minted"` (first-ever) or
`"recognized"` (repeat) — never left `"pending"` (the silent-drop shape: an
observation stuck pending, uncovered and unminted, IS this grain's stall).
Checked after every step, so a stall on step 2 (the tighter isolation test)
cannot hide behind step 3/4's success.

## AR3 — the loop assertion, registered exactly

**Bar:** a real, checked upper bound, in the same style as the primary
gate's AR3 (generous relative to measured, but tight enough that a real
regression to unbounded epoch/wall-clock growth cannot pass):

* `write_codebook_epoch` growth across all 4 steps: `<= baseline + 4`
  (measured: `+2`, one bump per genuine mint, zero for both repeats — 2× the
  measured value, matching the primary gate's own registered headroom
  convention).
* Each `chunk_pump` call: `< 3.0s` wall-clock (measured: all four `< 5ms`).
* Whole 4-step scenario: `< 10.0s` (measured: `~14ms`).

No engine-level loop defect is predicted at this grain (`ckg_mint`'s guard is
a real content-keyed `Not Exists ... Covers(...)` check, not a type-coarse
`kind == X` flag the way the pre-fix `DimensionGenerator` guard was — see AR5
reasoning below) — this bound exists as a regression guard per the same
standing rationale the primary gate registered for its own AR3, not because
a specific historical blowup is being reproduced here.

## AR4 — dedup-direction assertions

**Bar:**
* Exactly **2** `ShapeSignature{kind:'code_write_construction',
  provenance:'self_taught'}` entries exist after all 4 steps — not 1 (a
  stall on the second, different-kind chunk) and not 3+ (a repeat
  re-minting).
* The two entries' `chunk_key` attrs are exactly COMBINE's and GUARD's own
  recorded keys, each present exactly once.
* The two entries' `name` attrs are **distinct** — this is the direct
  regression check this rung exists to run: under the naming law
  `ckt_<snake(head)>_q<held-count>`, COMBINE's head (`ProgAssignVar` or
  `ProgReturn`, whichever the bigram lattice orders first) and GUARD's head
  (`ProgIfStmt`) are different strings AND the count discriminator is
  strictly increasing per substrate, so both the head-snake half and the
  count half of the name differ — two independent reasons the names cannot
  collide, unlike the `DimensionGenerator` bug where the pre-fix name was
  base-shape-derived and BOTH orbits shared the same base shape.
* Both repeat steps (`A2`, `B2`) recognize (`pk_status == "recognized"`,
  `covered_by` equal to the correct first mint's name) — not a re-mint, and
  not cross-covered (COMBINE's repeat must not be `covered_by` GUARD's
  entry or vice versa).

## AR5 — why this IS the right generalisation target, not a re-litigation of
`MetaShape`

Not re-investigating `MetaShape` here (already ruled out by both prior
documents, same Rust-field-scope reason). This rung is itself the
"third grain" the primary RESULTS doc named as a follow-on — there is no
further grain selection to make; `prog_chunk_growth` IS the registered
target.

**Structural reasoning for the predicted null, stated up front so a GO
result is not mistaken for an accidental pass:** `ckg_mint`'s own novelty
guard (`seeds/prog_chunk_growth.json`, the `ckg_mint` rule) is
`Not Exists ne: ne.kind == "code_write_construction" AND Covers(ne.chunk_rels,
obs.chunk_rels)` — a check over the SPECIFIC content of `chunk_rels`, not a
coarse `Not Exists ne: ne.kind == "code_write_construction"` flag the way the
pre-fix `DimensionGenerator` guard was (`Not Exists a DimensionGenerator with
kind == "linear"`, which capped the WHOLE graph at one generator regardless
of content). A second, content-different novel chunk is never blocked by the
first mint's mere existence at this grain — it is blocked only if the
first mint's `chunk_rels` actually `Covers` it, which two chunks of
different KIND (different `i`-row counts / different leaf paths) cannot.
This is the mechanical reason the charter's prediction is expected to hold;
the fixture pair above is built specifically to exercise it, not to dodge
it — GUARD's `chunk_rels` is content-different from a same-kind variant of
COMBINE, not merely a different literal value in the same shape (which
`Covers`'s own wildcard semantics might have folded).

## AR6 — no regression, both directions

**Bar 6.1 (current engine, GO required):** the new test file, run against
this worktree's engine and seed set, is 100% green.

**Bar 6.2 (pre-fix reproduction) — NOT APPLICABLE, stated up front.** Unlike
the primary/AR5 gates, there is no known pre-fix commit for THIS grain to
revert to — `prog_chunk_growth.json`'s `ckg_mint`/`ckg_recognize` have not
been identified as ever having had a coarse-guard defect; this rung is a
first-time construction of the missing test class, not a regression
reproduction of an already-diagnosed bug. If the committed test discovers a
REAL defect at this grain (contrary to the AR5 prediction), that defect and
its fix (if made) become this rung's own regression-catcher basis, reported
honestly as such rather than backfilled to look like a known-bug reproduction.

**Bar 6.3 (broader regression):** `tests/test_prog_chunks_migrated.py` (11
tests) and `tests/test_two_novel_orbits_gate_migrated.py` (4 tests) stay
green, unchanged, with the new file present.

---

## Explicitly out of scope (unchanged from the task's own charter)

1. Touching the existing primary-grain (`DimensionGenerator`) or
   `ShapeSignature`/`vq_grow_quantum`-grain tests/fixtures.
2. Any change to `prog_chunk_growth.py`'s naming law UNLESS a real defect is
   found (in which case: full fix, not a shrink).
3. A fourth-grain generalisation beyond `prog_chunk_growth`.
4. `MetaShape` (already ruled out, both prior documents).

## What would falsify this gate's predicted null

* If AR1/AR2's step-2 (`B_guard`, the SECOND novel item) does not resolve to
  `"minted"` — i.e. terminates `"pending"` — that is the stall this rung
  exists to check for, and it would mean the charter's own prediction was
  wrong: a REAL defect, to be fixed per the task's own instruction ("follow
  through on a real fix if you find one, don't just document it and stop").
* If AR4's two entries collide on `name` (contrary to the two-independent-
  reasons argument in AR5), that is the direct analogue of the
  `load_generators` shadowing bug at this grain.
* If AR3's bound is exceeded by orders of magnitude (not just jitter), that
  is the loop-class defect, structurally unexpected here (no
  `add_node_if_absent`/re-arm interaction analogous to the primary gate's
  fixed defect exists in `ckg_mint`/`ckg_recognize`) but checked anyway.
* If the probe numbers above do not reproduce byte-for-byte via the
  committed test, that is itself worth reporting precisely (a flake or a
  probe-vs-test discrepancy), not silently adjusted to match, per the
  primary PREREG's own standing rule.
