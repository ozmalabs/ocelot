# Two-novel-orbits gate, third grain (`prog_chunk_growth`) — RESULTS

**Prereg:** `TWO_NOVEL_ORBITS_THIRD_GRAIN_PREREG.md`, committed before the
test file was written. Worktree
`/home/matt/ocelot-two-novel-orbits-third-grain`, branch
`two-novel-orbits-third-grain`, from `main` at `3719b50`. Engine
`c086d83ad070` (`sha256sum runners/dsl/python/substrate_rs/_native.abi3.so`),
coherence-probed, `test_engine_provenance_migrated.py` green (10/10). No Rust
rebuild, no seed edit — a pure test-addition rung, confirmed below.

**Verdict: GO, confirmed-safe (no defect found, no fix needed) — the SAME
flavor of result as the primary gate's own AR5.** New file
`tests/test_two_novel_orbits_third_grain_migrated.py` (4 tests), all green.
The charter's own prediction held: `prog_chunk_growth`'s
`ckg_mint`/`ckg_recognize` naming and dedup law is content-keyed
(`Covers` over `chunk_rels`), not a coarse type-flag guard, so two
structurally-DIFFERENT-KIND novel chunks presented to one graph in one
session mint distinctly, no stall, bounded growth, correct dedup both
directions — exactly the shape a healthy grain should have.

---

## The one thing worth reading if you read nothing else

**This is a "checked, not at risk" confirmation, not a second
regression-catcher — stated plainly, matching AR5's own honesty convention
in the primary gate's RESULTS doc.** There is no known pre-fix commit for
this grain to revert to (unlike the primary `DimensionGenerator` grain,
which had a diagnosed, fixed, git-history-reproducible defect) — this rung
is the FIRST test of this class at this grain, not a regression check
against an already-found bug. The structural reason it was predicted safe
(`ckg_mint`'s guard is `Not Exists ne: kind==X AND Covers(ne.chunk_rels,
obs.chunk_rels)` — content-keyed, not `Not Exists ne: kind==X` alone) held
under direct measurement: two genuinely different-shaped chunks (a
multi-statement window vs a single compound statement) minted independently,
neither blocked the other, neither collided on name, and both repeats
recognized without re-minting.

---

## Step 1 — reading `chunk_candidates`, and what made a genuinely-different-
KIND second fixture

`domains/prog_chunk_growth.py::chunk_candidates` (`:415-426`) has exactly
two candidate-producing code paths per statement block (`_blocks`,
`:366-382`):

1. `_WINDOW_SIZES = (2, 3, 4)` (`:72`): every contiguous window of 2-4
   statements in the block becomes a `chunk_record`. This is what
   `tests/test_prog_chunks_migrated.py`'s `_boot_selfteach` (`:292-302`)
   already gates — `COMBINE_TMPL`, a flat `[ProgReturn, ProgAssignVar]`
   window.
2. `_is_compound` (`:384-388`): a lone statement of type `ProgIfStmt` /
   `ProgWhile` / `ProgForEach` / `ProgTryOr` with a non-`None` block field
   becomes its OWN `chunk_record([s])` — never gated by any existing test.

These are structurally different inputs to `chunk_record` (`:391-412`):
path 1 produces a `chunk_rels` relation system with one `["ckstmt", i,
label]` head row per window statement (`i` in `0..w-1`, flat, no nested
block walk); path 2 produces exactly one `["ckstmt", 0, label]` head row
whose leaf `["ck", 0, path, atom]` rows descend INTO the compound's own
`.cond`/`.then`/`.orelse` fields (`_flatten_rels`, `:136-159`, walking
`_abstract`'s output recursively). A fixture landing in path 2 is therefore
"differ in KIND, not merely count" by construction — not a probabilistic
argument, a structural one, confirmed by direct measurement below.

**Fixture 2 built: `GUARD_TMPL`**, a single top-level `ProgIfStmt`
(`cond=Gt(v,0)`, `then=Return("pos")`, `orelse=Return("nonpos")`) — designed,
per the same "exactly ONE candidate chunk" bar `_boot_selfteach`'s own
`COMBINE_TMPL` uses, so the top block has `n=1` (no window of size ≥2 fits)
and the lone statement IS compound (fires `_is_compound` exactly once); the
nested `then`/`orelse` blocks (each `n=1`, no compound inside) contribute
nothing further. Measured, off the REAL accepted IR (not the authored
template — `psy.synthesize_from_request` + `splice_binding`'s own statement
ordering, which for a single-part template is a no-op):

```
GUARD ir stmts: one ProgIfStmt (cond=Gt(v,0), then=Return('pos'), orelse=Return('nonpos'))
GUARD n_candidates=1  labels=['ProgIfStmt']  n_stmts=1
```

vs. `COMBINE`'s own (verbatim `_boot_selfteach` fixture, reused unmodified):

```
COMBINE ir stmts (bigram-ordered): AssignVar, Return
COMBINE n_candidates=1  labels=['ProgAssignVar', 'ProgReturn']  n_stmts=2
```

`test_fixtures_extract_genuinely_different_kind_of_chunk` (the new file's
first test) asserts this directly off the two fixtures' own
`chunk_candidates` output: COMBINE's `ckstmt` rows span `i ∈ {0,1}`, GUARD's
span only `i = 0`; COMBINE's leaf paths never carry a `cond`/`then`/`orelse`
prefix (a flat window structurally cannot), GUARD's do (the nested compound
walk). **GREEN.**

## Step 2 — the fixture, as built

`tests/test_two_novel_orbits_third_grain_migrated.py`, `_boot_two_orbit`
(mirrors `test_two_novel_orbits_gate_migrated.py`'s `_boot_gen` — ONE graph
for the whole scenario, deliberately not re-booted per orbit): one
`psy.ensure_program_synthesis` boot + `pcg.ensure_chunk_growth` + BOTH spine
templates boarded up front as `ShapeSignature{kind:'code_write_construction'}`
nodes (`gate_combine_spine` / `gate_guard_spine`, each its own unique
`trigger_tokens` — `COMBINE` / `GUARDPOS` — so `synthesize_from_request`'s
rung-1 codebook match is unambiguous, the same discipline `_boot_selfteach`
uses for its one template).

## Step 3/4 — the four assertion classes, run against the fixture

### AR1/AR2 — no stall, checked after every step

`test_two_novel_chunks_one_graph_no_stall_bounded_growth_correct_dedup`
presents `A_combine → B_guard → A_combine_repeat → B_guard_repeat` in
sequence to one graph, asserting after EACH step: `status == "accepted"`
(the synthesis itself succeeds) and `"pending" not in obs_statuses` (no
chunk observation left stuck uncovered-and-unminted — the silent-drop stall
shape at this grain, the direct analogue of the primary gate's
`status == "decoded"` check). Live, current engine:

```
A_combine          dt=0.0034s entries=1 epoch=1.0 obs_statuses=['minted']
B_guard            dt=0.0031s entries=2 epoch=2.0 obs_statuses=['minted', 'minted']
A_combine_repeat   dt=0.0041s entries=2 epoch=2.0 obs_statuses=['minted', 'minted', 'recognized']
B_guard_repeat     dt=0.0035s entries=2 epoch=2.0 obs_statuses=['minted', 'minted', 'recognized', 'recognized']
total wall: 0.0144s
```

Entry-count trajectory `[1, 2, 2, 2]`, asserted directly — the second,
DIFFERENT-KIND novel chunk (`B_guard`) mints its own entry immediately after
the first, no stall. Reproduced byte-identically on a second independent
probe run (`q13`/`q14` names identical run-to-run — deterministic, not a
flake). A tighter isolation,
`test_second_novel_chunk_does_not_stall_even_isolated` (no repeats, no
composition, just the two novel presents), reproduces the same result —
mirroring the primary gate's own two-tier isolation structure. **GREEN.**

### AR3 — bounded growth

* `write_codebook_epoch` growth across all 4 steps: measured `+2` (bound
  `<= baseline + 4`, 2× headroom, same convention as the primary gate's own
  AR3). One bump per genuine mint, zero for either repeat.
* Per-step `accept + chunk_pump`: measured all `< 5ms` (bound `< 3.0s`).
* Whole 4-step scenario: measured `~14ms` (bound `< 10.0s`).

No engine-level loop defect was predicted or found — `ckg_mint`'s guard is a
real content-keyed `Not Exists ... Covers(...)` check (see AR5 reasoning
below), structurally unlike the pre-fix `DimensionGenerator` guard that
caused the primary gate's own reproducible loop/stall pair. The bound is
retained as a forward-looking regression guard per the same standing
rationale the primary gate's own AR3 used, not because a historical blowup
was reproduced here. **GREEN.**

### AR4 — dedup-direction, both ways

* Exactly 2 `ShapeSignature{provenance:'self_taught'}` entries after all 4
  steps: `ckt_prog_assign_var_q13` (COMBINE's window chunk) and
  `ckt_prog_if_stmt_q14` (GUARD's compound chunk) — **names distinct**, the
  direct regression check this rung exists to run. (The `q13`/`q14` numerals
  themselves are an artifact of `ensure_write_codebook`'s starter-codebook
  size at boot time — the test does NOT pin the numeral, only distinctness,
  per the PREREG's own "not the exact numeral, only DISTINCTNESS" framing.)
* The two entries' `chunk_key` attrs are COMBINE's and GUARD's own recorded
  keys, each present exactly once — content-distinct, as constructed.
* Both repeat steps (`A_combine_repeat`, `B_guard_repeat`) resolve to
  `pk_status == "recognized"`, each `covered_by` its OWN chunk's mint name —
  never cross-covered (COMBINE's repeat is never `covered_by`
  `ckt_prog_if_stmt_q14` or vice versa), asserted directly via
  `name_by_chunk_key`.
* `test_repeat_chunk_after_two_mints_does_not_triple_mint` (isolated
  dedup-direction check, mirroring the primary gate's own) confirms
  independently: after both chunks mint, re-presenting either recognizes,
  entry count stays at 2, never 3.

**GREEN, on all counts.**

## AR5 — why this result was expected, and why the fixture wasn't built to
dodge it

`seeds/prog_chunk_growth.json`'s `ckg_mint` rule (`:249-625`) novelty guard
is:

```
Not Exists ne: ne.kind == "code_write_construction"
               AND Covers(ne.chunk_rels, obs.chunk_rels)
```

— a check over the SPECIFIC content of `chunk_rels`, never a coarse
`Not Exists ne: ne.kind == "code_write_construction"` flag the way the
pre-fix `DimensionGenerator` guard was (`DEDUP_ADOPTION_SWEEP_RESULTS.md`
§4.2.1: `Not Exists a DimensionGenerator with kind == "linear"`, which capped
the WHOLE graph at one generator for life regardless of content). A second,
content-different novel chunk is blocked only if the first mint's
`chunk_rels` actually `Covers` it — and GUARD's `chunk_rels` (one `ckstmt`
row, nested compound paths) structurally cannot be covered by, or cover,
COMBINE's (two `ckstmt` rows, flat window paths): `Covers` matches on the
SAME `i`-indexed row set, and the two fixtures don't share one. The naming
law (`ckt_<snake(chunk_head)>_q<held-count>`) independently avoids collision
two ways: the head half differs (`prog_assign_var` vs `prog_if_stmt`, since
the two chunks' first labels differ) AND the count half is a GLOBAL
strictly-increasing discriminator (never resets per head), so even two
same-headed chunks could not collide on name. This is the mechanical reason
the charter's prediction held — the fixture pair was built specifically to
exercise the guard's real behaviour (two genuinely different `chunk_rels`
shapes), not to avoid triggering it.

## AR6 — no regression

### 6.1 — current engine: GO

```
tests/test_two_novel_orbits_third_grain_migrated.py ....   [100%]
4 passed in 0.42s
```

### 6.2 — pre-fix reproduction: NOT APPLICABLE (as pre-registered)

No known pre-fix commit exists for this grain — `ckg_mint`/`ckg_recognize`
have never been diagnosed as carrying a coarse-guard defect the way
`DimensionGenerator`'s was. This rung is a first-time construction of the
missing test class, not a regression reproduction. Stated up front in the
PREREG so this is not silently glossed over; the AR3/AR4 bounds still stand
as forward-looking regression guards against a FUTURE coarsening of
`ckg_mint`'s guard (e.g. someone "simplifying" the `Covers(...)` check to a
bare `kind == X` existence check, which per the AR5 reasoning above is
exactly the shape that would reopen this class of defect at this grain).

### 6.3 — broader neighbouring suites: GO, unaffected

```
tests/test_two_novel_orbits_gate_migrated.py            .... [100%]  4 passed
tests/test_two_novel_orbits_third_grain_migrated.py      .... [100%]  4 passed
tests/test_prog_chunks_migrated.py                    ........... [100%] 11 passed
   -> 19 passed in 1.42s (combined run)

tests/test_gen_infer_migrated.py
tests/test_dimension_inference_migrated.py
tests/test_sdloop_vision_migrated.py
   -> 31 passed in 3.80s (unchanged from the primary gate's own AR6.3 set,
      minus the 4 tests of the file itself, which are run separately above)
```

No existing test edited; only the new file added.

---

## Environment note (data, not code — recorded for reproducibility)

`results/prog_construction_scan.json` and `results/prog_chunk_mine.json` are
gitignored generated artifacts (`.gitignore:25`) present in the primary
checkout's working directory but absent from git history, so a fresh
worktree does not have them; `psy.ensure_program_synthesis` /
`pcg.install_mined_chunks` read them. Both files were copied verbatim from
`/home/matt/ozmadev/ocelot/results/` into this worktree's `results/` before
any test ran — `tests/test_prog_chunks_migrated.py` (the existing suite this
rung extends) already depends on their presence identically; this is not a
new dependency this rung introduced, and no file content was altered.

---

## What this gate does NOT establish (CLAUDE.md: "synthetic-proven mechanism
≠ benchmark value, report both")

1. **No claim about production prevalence.** Same mechanism-level boundary
   every rung in this arc has drawn — how often a real session accepts two
   structurally distinct novel chunk shapes in one sitting is unmeasured.
2. **This is a "checked, not at risk" confirmation, not a regression-
   catcher** (see AR6.2) — there is no pre-fix commit this test reproduces a
   failure against, unlike the primary gate's own AR6.2. Stated plainly here
   rather than implied, matching the primary gate's own AR5 honesty
   convention.
3. **Only ONE second-fixture shape was built** (a single compound
   `ProgIfStmt`) — `chunk_candidates` has exactly two candidate-producing
   code paths (`_WINDOW_SIZES` vs `_is_compound`) and this rung exercises
   both, but within `_is_compound` there are three other statement types
   (`ProgWhile`/`ProgForEach`/`ProgTryOr`) not separately fixture-built; the
   PREREG's own structural argument (AR5) applies uniformly to all of them
   (the guard is `Covers` over `chunk_rels` regardless of which compound
   type produced it), so this is not expected to matter, but it was not
   separately measured.
4. **The exact `q<N>` numerals are boot-order-dependent** (they reflect
   `ensure_write_codebook`'s starter-codebook size at the time of first
   mint) — the test correctly asserts distinctness, not the specific
   numeral, and this document does not claim the numerals themselves are a
   stable fact of the codebase.
5. **No fourth grain** was investigated — out of scope per the task's own
   charter; this rung closes exactly the one follow-on the primary gate's
   RESULTS doc named.

## What a reviewer should look at first

1. **AR1/AR2's primary scenario**
   (`test_two_novel_chunks_one_graph_no_stall_bounded_growth_correct_dedup`)
   — the entry-count trajectory `[1, 2, 2, 2]` is the single clearest signal
   that the second, differently-KINDED chunk neither stalled nor collided.
2. **The `test_fixtures_extract_genuinely_different_kind_of_chunk` sanity
   test** — confirms the fixture construction itself meets the task's own
   bar ("differ in KIND, not merely count") before the dedup assertions are
   even relevant; without it, a reviewer would have to trust the PREREG's
   prose reading of `chunk_candidates` on faith.
3. **AR5's structural argument** — why the `Covers`-based guard is a
   different SHAPE of guard than the pre-fix `DimensionGenerator` one, which
   is the actual reason this grain was predicted (and confirmed) safe, not
   merely "we tried it and it happened to work."

---

## Reproduce

```bash
cd /home/matt/ocelot-two-novel-orbits-third-grain
git log --oneline -1                     # two-novel-orbits-third-grain, on top of 3719b50
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so   # c086d83ad070…
PYTHONPATH=runners/dsl/python:. python3 -c "
import substrate_rs as srs; s=srs.Substrate()
a=s.node(s.add_node('T',{'lst':[1,2,3],'tup':(1,2,3)}))['attrs']
print(a['lst'], a['tup'], a['lst']!=a['tup'])"          # coherence probe

# the new gate
PYTHONPATH=runners/dsl/python:. python3 -m pytest -q -p no:randomly \
  tests/test_two_novel_orbits_third_grain_migrated.py -v

# regression: primary gate + this gate + the existing prog_chunks suite
PYTHONPATH=runners/dsl/python:. python3 -m pytest -q -p no:randomly \
  tests/test_two_novel_orbits_gate_migrated.py \
  tests/test_two_novel_orbits_third_grain_migrated.py \
  tests/test_prog_chunks_migrated.py

# broader neighbouring suites
PYTHONPATH=runners/dsl/python:. python3 -m pytest -q -p no:randomly \
  tests/test_gen_infer_migrated.py tests/test_dimension_inference_migrated.py \
  tests/test_sdloop_vision_migrated.py
```
