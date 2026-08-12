# Red-test triage — RESULTS

Pre-registration: `RED_TEST_TRIAGE_PREREG.md`, committed at **`93d894a`** BEFORE the
first sweep ran. Branch `red-test-triage` in `/home/matt/ocelot-red-test-triage`,
detached from `main` @ **`d239b7c`**. Nothing pushed; `main` untouched.

---

## THE ONE THING WORTH READING IF YOU READ NOTHING ELSE

**The largest red class in this tree was a false accusation the tree made against
itself, and every worktree ever created re-made it.** `engine_provenance.build_is_stale`
compared **mtimes** — documented as *"meaningful here and only here: this is the working
tree where the build actually ran."* That premise is false for a tree **git** wrote.
`git worktree add` stamps every file it writes with the checkout time in whatever order
it happens to write them, so a brand-new worktree gets `.rs` files **2 milliseconds
newer** than a `.so` neither of them built. Measured at `d239b7c`: **85** falsely-stale
`.rs` in a fresh worktree, **5** in the canonical tree. Because `assert_measuring_engine`
*refuses to measure* on `stale_rust`, that produced **117 red node ids across 88 files
(36% of every red file in the tree)** — on an engine that was exactly the committed one,
including the provenance gate itself, which could not even **collect**.

The module already knew the general form of this fact. `rust_source_fingerprint`'s own
docstring, eleven lines above: *"Content, never mtime: a git checkout rewrites every
mtime, so mtimes are meaningless ACROSS trees."* The exception carved out for "the build
tree" simply did not survive the artifact becoming git-tracked, and nothing re-read it.

The second-largest class is its sibling in shape: **76 node ids across 25 files** that
say only *"opencv is not installed here."* Not a defect — an unmeasured capability
wearing a red's clothes, and 20+ rungs each re-diagnosed it by hand.

**None of the four classes closed here was a bug in what the tests are about.** All four
were the measuring apparatus mis-describing an environment. That is the same disease this
folder keeps finding — *an instrument mis-recording the very thing it exists to record* —
and the triage's own sweep tool turned out to have two more of them (§6).

---

## 0. Provenance

| | |
|---|---|
| worktree | `/home/matt/ocelot-red-test-triage`, branch `red-test-triage` |
| base | `main` @ `d239b7c` ("Merge shape-audit-pattern-c-fixes"), verified `git log --oneline -1 main` |
| engine | `runners/dsl/python/substrate_rs/_native.abi3.so`, sha256 `62e5cdc39a84fee548b9d373c9bbcd01f33c69f8ddab3dc518e78b0ef45ca56f` — **git-tracked, byte-identical to the canonical tree's**. `substrate_rs.__file__` resolves inside this worktree. |
| Rust rebuild | **NONE, and none was needed** — see §1, the fix is that the staleness *question* was being asked wrong, not that the binary was wrong. Zero new Rust in this rung. |
| coherence probe | `add_node("T", {"lst":[1,2,3],"tup":(1,2,3)})` → `[1,2,3]` (list) / `(1,2,3)` (tuple), distinct — PASS |
| CONDITION (stamped on every number below) | `data/` **SYMLINKED** to the canonical tree; `results/` per-entry symlinks to the canonical tree; `chess` **1.11.2 INSTALLED**; `cv2`/`matplotlib`/`scipy`/`av`/`pybullet`/`vizdoom`/`torch` **ABSENT**; `seeds/grounded_lexicon.json` + `seeds/acquired/` **ABSENT** (gitignored — absent in *every* worktree, see §7); 12 single-worker shards, per-file subprocess, `COLUMNS=250` |
| BEFORE sweep | 2026-08-12 19:53–21:01, `results/failure_baseline_sweep_BEFORE_triage.json` |
| AFTER sweep | 2026-08-12 23:10–2026-08-13 00:15, `results/failure_baseline_sweep_AFTER_triage.json` |

**The prior artifact was not comparable and could not be verified here, which is why AR1
demanded a fresh measurement.** `results/failure_baseline.json` as it stood was measured
2026-07-21 at head `0e61f60e` in the tree
`/home/matt/ozma/internal/.claude/worktrees/agent-abfda01548d24e7a1/research/experiments/gamma-substrate`.
**That commit does not exist in this repository and that tree no longer exists on this
box.** This repo's history begins at `26ca9ff` (2026-08-10, 96 commits). It also covered
**648** test files; there are now **1092**. Its condition line read *"no data/ symlink"* —
the worse of the two documented conditions.

---

## 1. Per-bar verdict

| bar | verdict | evidence |
|---|---|---|
| **AR1** fresh, enumerated, environment-stamped baseline | **PASS** | 1092 files swept per-file at `d239b7c`; **458 red node ids / 246 red files** BEFORE. Artifact list-shaped by its own checker; coverage block declares 25 `NOT_ESTABLISHED`. |
| **AR2** every node id bucketed with evidence | **PASS** | §2. Four batches by *proven* shared root cause (root cause demonstrated once, then every member listed); the residual long tail enumerated per file. |
| **AR3** fixes applied, before/after | **PASS** | §3. 261 node ids fixed across four classes + two path/shape drifts, each re-measured. |
| **AR4** retirements with justification | **PASS, vacuously — ZERO TESTS RETIRED** | §4. Nothing met the pre-registered bar ("a named superseding artifact"). Reported as the honest outcome it is, not padded. |
| **AR5** regenerated, re-gated baseline | **PASS** | `results/failure_baseline.json` rebuilt from the AFTER sweep, **216 node ids / 133 files**; `tests/test_failure_baseline_migrated.py` **11 passed**, including all six positive controls. |
| **AR6** no regression beyond the baseline's own change | **PASS, with two named exceptions, both controlled** | §5. 19 node ids are red AFTER and not BEFORE; **17 were MASKED before** (their whole file was a single collection ERROR, or was `NOT_ESTABLISHED`, or was dropped by the sweep's own regex). The 2 genuinely new were both proven **not caused by this rung** by reverting the only change in their path. |

---

## 2. AR2 — the categorisation

**458 node ids, every one assigned.** Batching was allowed by the PREREG only *by shared
root cause proven once and shown to apply*; each batch below names the root cause, the
evidence, and its members (the members are in the committed sweep artifacts, node id by
node id).

| bucket | node ids | files | what |
|---|---|---|---|
| **(a) genuine fixable bug** | **117** | 88 | mtime-based staleness check (§3.1) |
| **(a) genuine fixable bug** | **18** | 10 | moved-doc paths + the one LIST-rooted file in `seeds/` (§3.4, §3.5) |
| **(b) environment / optional-dependency gap** | **76** | 25 | declared-optional dependency, unguarded (§3.2) |
| **(b) absent artifact** | **30** | 8 | §12.3 provenance pins whose commits are not in this repository (§3.3) |
| **(c) stale / no longer relevant** | **0** | 0 | **nothing met the bar** (§4) |
| **(a) too large for this rung / (d) ambiguous** | **217** | ~131 | the residual long tail (§8), plus 2 explicitly (d) |

**The four batches are 241 of 458 (53%), and not one of them is about what its tests
test.** Each is a single environmental fact, mis-rendered as dozens of independent
failures.

---

## 3. AR3 — the fixes, with before/after

### 3.1 Engine staleness is CONTENT, not mtime — 117 node ids / 88 files
`ce1867b`. Root cause and measurement: see the callout above. The fix answers the
question three ways, **none of which manufactures a red from an absence**:

1. a **build record** (`record_build`, new, written by `scripts/engine_build.sh`) names,
   by content hash, the source the artifact was built from → stale is exactly what moved;
2. no record but git can answer → a `.rs`/`Cargo.toml` that **differs from HEAD** while
   the committed artifact does **not** is a forgotten rebuild, by content;
3. neither → **UNKNOWN, which returns `[]`**.

**Before:** `tests/test_engine_provenance_migrated.py` → *1 collection ERROR* (the gate
could not run at all). **After:** **10 passed**, including three new tests,
positive-controlled in both directions per protocol 12.3 — a clean checkout is NOT stale;
edited Rust after a recorded build IS caught; a file merely `touch`ed (content unchanged)
is NOT stale.

The real catch the mtime check existed for is **preserved, and tested**.

### 3.2 Optional dependencies are SKIPS with named reasons — 76 node ids / 25 files
`469f72a`. `cv2` is declared in `requirements-arc.txt` (`opencv-python-headless`),
`pybullet` in `requirements-robot.txt`; `matplotlib`/`scipy`/`av`/`vizdoom` are optional
adapter dependencies. `domains/vision_graph.py` hard-imports `cv2` and is reached lazily
from `world_adapter.perceive_upload_image`, so the failure surfaces per test, not at
import — which is exactly why it read as 45 separate `cv2` reds.

`tests/optional_deps.py` is an **allowlist, not a catch-all**: `requires('foo')` **raises**
on an undeclared module, because a marker that can excuse anything is the count-shaped
defect one level up. Deliberately **not** a `conftest.py` exception hook — converting any
`ModuleNotFoundError` into a skip would hide the real ones too.

Applied at the right granularity: module-level `importorskip` only where **every** test in
the file needs it (7 files); a per-test marker everywhere else (18 files), so a test that
does not need the dependency is never over-skipped. Verified: `test_vision_migrated.py`
6 skipped / 1 **passed** — the one test that does not touch `cv2` still runs.

### 3.3 A provenance pin this repository cannot resolve is a SKIP — 30 node ids / 8 files
`2a10fbc`. Eight files carry §12.3 rung-provenance gates (`git diff BASE_SHA RUNG_SHA` →
this rung added no Rust / touched only what it owns / appended exactly one ledger row).
**Their pinned commits are not in this repository:** `git cat-file -e 212212e3` →
`fatal: Not a valid object name`; the pins' own pinned paths still read
`research/experiments/gamma-substrate/...`, the pre-export layout.

Not a failing claim (each was verified when its rung landed); not fixable code (there is
no defect); an **absent artifact**, the same shape as `data/` not being symlinked — and it
**self-heals**: point a checkout at a repo that has the history and every gate arms again,
unchanged. **That is why they were not retired.**

**The precedent is the files' own**: they already carried
`_UNPINNED = RUNG_SHA.startswith("RUNG_SHA")` with a `skipif` — a pin that cannot be used
*yet* was already a skip; a pin that cannot be used *any more* is the same fact from the
other end. `tests/provenance_pins.py` asks git exactly one question — *is this object in
this repository* — so a **reachable** pin returns `False`, the gate runs, and it can still
fail. It is not a way to skip a provenance gate.

### 3.4 Moved documentation paths — 5 node ids / 2 files (+1 later, §3.6)
Commit `3f9d7c3` *"reorganize 1105 root/docs markdown files into docs/research/<topic>/"*
moved the docs; five gates still pointed at the pre-move paths. Every target verified
present under `docs/research/humanoid/` and `docs/research/program_synthesis/`.
`test_embodied_adaptation_migrated` → 4 red → **0**; `test_retrieval_ceiling_migrated`
→ 3 red → **0** (19 passed).

### 3.5 The one LIST-rooted file in `seeds/` — 13 node ids / 8 files + 2 readers
`5f90396`, **corrected in `3316880`**. `seeds/_recovered_f16_rules.json` is git-tracked and
its JSON root is a bare list of 12 rule objects, not a manifest. Eight copies of a
`seeds/*.json` scan idiom, plus `domains/morpheme_decomposition.corpus_morpheme_code`,
`domains/guard_coalesce_lint.scan_seeds` and `scripts/growth_pipeline_sampler.known_node_types`,
called `.get` on it.

**SELF-CORRECTION, left in the record.** The first fix read the bare list **as rules**,
arguing that skipping it would create a blind spot. Measured consequence: `guard_coalesce_lint`
then reported **509 NEW** coalesced guard reads out of a file the agent never boots with.
`boot_all._read_seeds` **skips** every non-dict manifest — so that file ships nothing and
there was never anything there for a seed gate to find. **The rule is MATCH THE LOADER:
what a gate over `seeds/` means is what the loader loads.** All eleven sites now skip it
exactly as the loader does. (The 509 count is unchanged either way — see §8, it is
independent lint-baseline drift.)

### 3.6 The same three classes again, once the engine refusal stopped masking them
`3316880`. Fixing §3.1 let 10 files **collect** for the first time, revealing per-test
failures that had been standing behind one collection ERROR each. Four of those files were
more §12.3 pins (`decay_gradient`, `paint`, `colour_bound`, `colour_bound_k1`,
`lighting_l4`), one more was a moved doc (`VISION_DECAY_PREREG.md`), two more were the
LIST-rooted scan. All fixed by the same three mechanisms. Re-measured:
`paint` / `colour_bound` / `colour_bound_k1` / `lighting_l4` / `instrument_node_type_guard`
→ **GREEN**.

---

## 4. AR4 — retirements: ZERO, and that is the finding

**Not one test was retired.** The PREREG's bar was explicit: *"A node may enter (c) only
with a named superseding artifact. 'I could not work out why it fails' is (d), never (c)."*

The two populations that *looked* like retirement candidates both failed that bar on
inspection, and both failed it in the same instructive way:

- **the 30 provenance-pin nodes** — the obvious read is "these verify a commit range that
  no longer exists, delete them." But the claims are not false and the gates are not
  broken: they are unverifiable *here*, and they re-arm unchanged against a repository
  that has the history. Deleting them would destroy a working gate to make a number
  smaller. **Skipped with the reason named, not retired.**
- **`tests/test_graph_rewrite.py`** — two tests hand a `TypedGraph()` to
  `linear_algebra.make_matrix`, which calls `graph.add_node`; `TypedGraph` has no public
  `add_node`, and the green sibling `tests/test_linear_algebra.py` uses `la.new_graph()`
  (a native `Substrate`). It is genuinely arguable that the Python search layer these two
  tests cover is superseded. **It is equally arguable that it is not, and that is a
  creator's call, so it is filed (d)** — `AMBIGUOUS_NEEDS_THE_CREATOR` in the baseline,
  with both sides written down.

---

## 5. AR6 — no regression, with both exceptions controlled

| | BEFORE | AFTER |
|---|---|---|
| red node ids | **458** | **216** |
| red files | **246** | **133** |
| green files | 807 | **912** |
| `NOT_ESTABLISHED` | 25 | 26 |
| `NONZERO_NO_NODES` | 14 | **0** |
| `ALL_SKIPPED` (new status, §6) | — | 21 |

**FIXED 261 · HELD 197 · NEW 19.** The 19 are accounted for individually, and **17 are
not new failures at all**:

- **13** in 5 files whose entire BEFORE verdict was **one collection ERROR** — the engine
  refusal aborted collection, so the file contributed a single file-level node instead of
  its real per-test reds (`dim_infer_args` 6, `guard_coalesce_lint` 2, `decay_gradient` 1,
  `refusal_representable` 1, `reference_overfire` 3). **This is an information gain**: 5
  anonymous file-level entries became 13 enumerable node ids.
- **2** (`speech_act_parity`) were `NOT_ESTABLISHED` before — a 420 s timeout, never
  measured, correctly never counted red.
- **1** (`deep_comprehension`) was **dropped by the sweep's own regex** (§6.1) — it was
  red all along and could not be enumerated.
- **1** (`arc_magnitude`) is **sweep self-contamination**: running the suite mutates
  git-tracked files (`seeds/metonymy_patterns.json`,
  `tests/fixtures/comprehension_divergence/divergence.json` were modified after every full
  sweep), and this test is a byte-identity gate over `seeds/`. **Re-run on a restored tree:
  PASSES.** `tests/conftest.py`'s session-wide `OZMA_SEED_PERSIST_DISABLED` guard does not
  cover those writers. Named, not fixed — see §8.

**The 2 genuinely new, both controlled, neither caused by this rung:**

- `test_prog_moves_migrated::test_named_regression_sweep_only_known_pins_drift`. It spawns
  a **nested multi-file pytest run** and fails on
  `test_reject_informs_repair_migrated.py::test_no_wrong_accept_regression_vs_v1_7_0_baseline`,
  which is green run alone — cross-file state leakage inside the nested sweep. **Control:
  the only change of this rung plausibly in its path (`domains/morpheme_decomposition.py`)
  was reverted and the failure reproduced unchanged, twice.**
- `test_rust_engine_ext_7b::test_attr_index_perf_beats_linear`. Asserts a **≥3× speedup**
  and measures **2.7–2.8×**, reproducibly, at low load as well as high. A hard-coded ratio
  sitting ~7% from its own boundary is a scalar knob where a shape belongs (CLAUDE.md,
  *SHAPES NOT NUMBERS*). **Deliberately not relaxed** — moving a bar to make a number green
  is the thing this tree forbids.

**Same-condition caveat, declared:** `results/` is symlinked to the canonical tree, which
other agents write to. `test_reference_overfire`'s grounding-memo-dependent assertions are
therefore not perfectly isolated between sweeps. Its 3 unmasked reds reproduce on a clean
tree with the original `morpheme_decomposition.py` restored, so they are not this rung's,
but they are not proven stable either.

---

## 6. Everything that broke — including the instrument

### 6.1 The sweep's own short-summary regex was DROPPING REDS
`_SUMMARY = re.compile(r"^(FAILED|ERROR)\s+(\S+)(?:\s+-\s+(.*))?$")`. **A parametrized test
id can contain a space** — `test_generalises_protagonists_animal_and_tracked[OLD SULTAN-leads0]`,
real, in `tests/test_deep_comprehension.py`. `\S+` stops at that space, the ` - `
alternation then fails, and **the whole line is discarded**: exit 1, zero node ids, filed
`NONZERO_NO_NODES` — a red that a *list* cannot enumerate, in the tool whose entire purpose
is enumerating reds. Exactly the disease its own docstring records about `COLUMNS=80`.
Fixed (non-greedy to the first ` - `), and every file the mis-parse could have touched was
re-measured.

### 6.2 Exit code 5 is "no tests ran", which is what an ALL-SKIPPED file returns
Filed as `NONZERO_NO_NODES`, so every honest (b)-class guard this rung added made the
sweep look like it had grown a new anomaly. Now its own status, **`ALL_SKIPPED`**, recorded
in the coverage block: **guarded, not measured, and never silently green.** This also
correctly re-labels 11 pre-existing files (jsbsim, pybullet, tree-sitter, …).

### 6.3 The baseline lived in exactly one tree, and its gate was inert everywhere else
`results/` is gitignored, so `results/failure_baseline.json` was **untracked** — it existed
only in the canonical tree. `tests/test_failure_baseline_migrated.py` **skips when the file
is absent**. So the gate that exists to stop a baseline from silently drifting has been
**silently inert in every worktree every rung has ever created.** `.gitignore` now negates
that one path (plus the two sweeps behind it), and the artifact is committed.

### 6.4 `--condition` was hard-coded
The builder stamped *"no data/ symlink; own engine build"* — the condition of the first
sweep that ever ran — into **every** artifact it would ever write. CLAUDE.md measures this
same tree at 144–145 red node ids with `data/` symlinked and 565 without: a 3.9× spread on
one engine at one commit. A baseline that cannot state its own condition is a rumour. Now a
parameter.

### 6.5 One misplaced insertion, caught by re-measuring
The scripted decorator insertion put an import inside a multi-line `from ... import (` in
`test_colour_bound_k1_migrated.py` → `SyntaxError`, whole file red. Caught by the targeted
re-run, fixed, re-measured green (23 passed, 2 skipped). Recorded because a patch script
that is not re-measured is a guess.

---

## 7. A condition nobody had stamped: `seeds/grounded_lexicon.json`

`.gitignore` excludes `seeds/grounded_lexicon.json` (110 MB, 2501 grounded Concepts with
`meaning_vec`) and `seeds/acquired/` (71 files). `boot_all._read_seeds` globs
`seeds/*.json`, so **the canonical tree boots the agent with a grounded lexicon and every
worktree boots it without one** — and **145 test files call `load_all_seeds`**. Neither the
prior baseline's condition line nor any status line in CLAUDE.md mentions it.

**This rung did NOT measure the size of that effect** — it was found late, and adding the
symlink mid-sweep would have destroyed the one-tree-state property the measurement depends
on. It is named here as the **next measurement**, precisely because a condition that has
never been stamped is exactly how a 3.9× spread went unnoticed before.

---

## 8. What remains — 216 node ids, and why they are out of this rung's scope

Ten files hold 55 of them; the other 161 are spread over 123 files at 1–4 each. That shape
is the finding: **after four environmental classes are removed, what is left is a long tail
of individually-diagnosable behavioural defects, not another batch.**

Diagnosed and annotated in the artifact (the class travels with the node id):

| file | n | class |
|---|---|---|
| `test_codec_graph_resident.py` | 8 | `HEVC_GRAMMAR_INCOMPLETE_SECOND_CAUSE` — **re-read**: the artifact's inherited paragraph describes the *dead-install* bug, which was FIXED in rung 121000-121999. Today's messages (`cannot convert NoneType to bytes` ×4, `assert 4 == 128`, …) are the second cause that fix unmasked. The old text is kept verbatim as the historical record it is; the actionable line is the new one. |
| `test_seed_claim_migrated.py` | 8 | `GATE_KILLED_BY_ITS_OWN_FIX` — the gate **says so itself**: *"the ledger-blindness this gate documents has been FIXED"*, *"baseline entries no longer measured"*. The type specimen `test_failure_baseline_migrated.py`'s docstring already names. Action: re-read the §11 ledger rows and update the gate's baseline — a judgement about the seed ledger, not a triage call. |
| `test_guard_coalesce_lint_migrated.py` | 2 | `LINT_BASELINE_DRIFT` — 509 new coalesced guard reads + 6 baseline entries that no longer exist. Confirmed **not** the LIST-rooted file (count unchanged when it is skipped). Action: deliberately re-baseline accepted debt. |
| `test_arc_magnitude_migrated.py` | 1 | `SWEEP_SELF_CONTAMINATION` — §5. A byte-identity gate in a suite that mutates tracked files is measuring the run, not the tree. |
| `test_graph_rewrite.py` | 2 | `AMBIGUOUS_NEEDS_THE_CREATOR` — §4. |
| `test_prog_moves_migrated.py` | 1 | `NEW_AT_THIS_HEAD_NOT_CAUSED_BY_THE_TRIAGE_RUNG` — §5. |
| `test_rust_engine_ext_7b.py` | 1 | `PERF_THRESHOLD_AT_THE_BOUNDARY` — §5. |

Named but **not** individually diagnosed (each is its own rung): `test_dim_infer_args` (6),
`test_action_migrated` (5, `BigvilleActionWorld.__init__` no longer takes `deposit_stock`),
`test_adaptive_control_core` (5, `KeyError: 'adaptive_learning_rate'`),
`test_control_regime_escalation` (5), `test_conversation_loop` (5),
`test_editop_dialect_terms` (5), `test_chess` (3, `unsupported operand & : float and int`),
`test_frozen_core_invariant` (3, manifest ↔ live-constant drift), and the comprehension /
reading tail. **193 entries remain `UNCLASSIFIED`, which the artifact's own README defines
correctly as *"an entry nobody has diagnosed"* — labelled, never defaulted.**

**Blocked, concurrent thread owns the file:** none. No red in the remaining list required
editing `domains/analogical_thinking.py`, `domains/reflective_faculty.py`,
`domains/rule_signature.py`, `runners/dsl/src/py.rs`, or `world_adapter`'s checkpoint-load
region. All five were left untouched.

---

## 9. Remaining uncertainties

1. **The grounded-lexicon condition (§7) is unmeasured.** Up to 145 files boot differently
   in a worktree than in the canonical tree, and nothing says so.
2. **`test_reference_overfire`'s 3 unmasked reds are not proven stable** — its grounding
   memo lives under the symlinked `results/`, shared with a tree other agents write to.
3. **The suite mutates two git-tracked files** on every full run. Every byte-identity gate
   over `seeds/` is therefore order-dependent. Root cause not chased here.
4. **`NOT_ESTABLISHED` is 26 files** at a 420 s per-file budget under 12-way sharding. Those
   files are neither green nor red, by design. Under a serial sweep some would complete.
5. **Nothing was retired**, so the list carries no deletions to re-examine — but §4's two
   near-misses should be revisited if the pre-export history is ever restored (the pins
   would arm) or the Python search layer is formally retired (`test_graph_rewrite`).

---

## 10. Reproduce

```bash
git worktree add --detach /tmp/tri d239b7c && cd /tmp/tri
git checkout -b red-test-triage && git merge --ff-only <this branch>
ln -s <canonical>/data data                       # the stamped condition
python3 -c "import chess"                         # 1.11.2

# 12 interleaved single-worker shards (see scripts/failure_baseline_merge.py for why)
python3 - <<'PY'
import pathlib, glob
f = sorted(glob.glob('tests/test_*.py'))
for i in range(12):
    pathlib.Path(f'/tmp/shard_{i:02d}.txt').write_text("\n".join(f[i::12]) + "\n")
PY
for i in $(seq -w 0 11); do
  systemd-run --scope --user -p MemoryMax=28G -- nice -n 5 \
    python3 scripts/failure_baseline_sweep.py --workers 1 --timeout 420 \
      --files-from /tmp/shard_$i.txt --out results/sweep_$i.json &
done; wait

python3 scripts/failure_baseline_merge.py 'results/sweep_*.json' results/raw.json
python3 scripts/failure_baseline.py build --raw results/raw.json \
    --condition '<your condition, stated>'
python3 -m pytest tests/test_failure_baseline_migrated.py -q     # 11 passed
python3 -m pytest tests/test_engine_provenance_migrated.py -q     # 10 passed
```

Never `pytest -n auto`. The BEFORE and AFTER sweeps are committed
(`results/failure_baseline_sweep_BEFORE_triage.json`, `..._AFTER_triage.json`), so the
node-id accounting in §5 is checkable without re-running anything.
