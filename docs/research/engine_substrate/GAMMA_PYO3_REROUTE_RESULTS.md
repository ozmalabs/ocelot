# Γ PyO3 reroute — results

**Verdict: NO-GO.** The one-line-per-call reroute
(`PySubstrate::add_production` calling `inner.add_production(p)` instead of
`inner.checker.grammar.add(p)` directly) was built, and it does exactly what
it says: every PyO3-driven `add_production` call now mints a real
`GammaGrammar`/`GammaProduction`/`GammaNodePattern` graph mirror and fires
`gamma_epoch.bump()` (§3 below, live-demonstrated). But the empirical
regression sweep this PREREG committed to running BEFORE deciding surfaced
**two independent, genuine, non-benign regressions** — not literal-count
assertions needing an honest update, but real behavioural defects — and one
of them is **unbounded**: a `WorldAdapter` that periodically checkpoints and
resumes (the daemon's own live operating pattern) grows its graph by a fixed
increment **on every single reload, forever**, because
`WorldAdapter.load()`'s existing "replay Γ productions to restore
admissibility" step (`substrate/world_adapter.py:6171`) was written under
the — previously true, now false — assumption that replaying
`add_production` for productions the graph already holds is graph-inert.
Fixing that requires editing `world_adapter.py`, which is outside this
rung's file-scope (`py.rs` + test files only) and outside what this PREREG
registered as an acceptable in-flight scope change. Both of AR2's registered
NO-GO conditions are met, independently, with direct evidence: **(i) a
flagged test breaking in a way that is not a traceable honest count update**
(a real outlier-detector VERDICT flips, not just a count going up) and
**(ii) the fix requiring more than the PyO3 binding itself.**

**The one thing worth reading if you read nothing else:** of 5 genuinely new
test failures introduced by the reroute (out of 1320+388 test items run
across two paired baseline/changed sweeps), exactly 3 are honest,
traceable, "the mirror is real now, so a literal count needs bumping" cases
— predicted in advance in the PREREG (§0.5) and confirmed to be exactly
that on inspection. The other **2 are not** — they are root-caused,
independently, to two distinct mechanisms neither of which existed before
this rung's own investigation found them: **(a) unbounded compounding graph
growth on save/load** (§2.3, measured directly: +261 nodes per cycle,
5 cycles, no sign of convergence) and **(b) population-statistics
corruption in any subsystem that scans `substrate.nodes()` without a type
filter** (§2.4, root-caused to a 192-`add_production`-call test fixture
injecting ~960 zero-diversity mirror nodes into a graph an outlier detector
reads as "the whole population"). Both are real, both are outside this
rung's fixable scope, and this is why the verdict is NO-GO rather than a
forced-through GO with two "known issues."

---

## 0. Provenance

- Worktree: `/home/matt/ocelot-gamma-pyo3-reroute`, branch
  `gamma-pyo3-reroute`, detached from `main` at `aa6c939`.
- **Baseline** (unedited `aa6c939` source, this worktree's own rebuild)
  `.so` sha256: `f87f857cf54a19a3942bd8878093e533d6b4896c9ec397f6e13f530a76165916`
  (`source_match = "own"`, `stale_rust = []`). `aa6c939`'s checked-in
  binary hashes `d7acb906da8ffb2c02c6feccd3bf3ecc62241b956f6343c336479a0f5e363843`
  (the same hash `GAMMA_REFLECTION_WIRING_RESULTS.md` reports as ITS OWN
  final engine — that rung's work is already merged into `aa6c939`); this
  worktree's from-scratch rebuild differs only in the non-reproducible
  build-id/timestamp bytes the prior rung already documented, confirmed
  same-source via a clean `git diff` before rebuilding.
- **Changed** (this rung's one-line `py.rs` reroute) `.so` sha256:
  `f16265ed98b876733de51825eec08497f504a9b1ef51cc6aee008dba45b4751e`
  (`source_match = "own"`, `stale_rust = []`). Rebuilt twice from the
  identical final source (once before, once after a `git stash`/`pop` round
  trip used for a baseline confirmation check, §2.2) and got the **identical
  hash both times** — reproducible.
- Build: `maturin develop --release --skip-install` inside a local
  `.build-venv` (satisfies maturin's venv-detection requirement only;
  touches no system site-packages), `CARGO_BUILD_JOBS=2`, `~/.cargo/bin`
  (rustup 1.97.1) placed first on `PATH` ahead of Homebrew's older
  toolchain (same pre-existing environment gotcha the prior rung
  documented — Homebrew's `rustc` 1.87.0 doesn't support the
  `avx512f`/`avx512bf16` `target_feature` attributes this crate already
  uses). Every heavy command wrapped in `systemd-run --scope --user -p
  MemoryMax=8G -p MemoryHigh=7G --`, `free -h` checked first, one heavy
  process at a time — this box hosts live home infrastructure (security
  cameras, home automation, a media server) and a prior session's OOM is
  documented in the brief.
- Coherence probe (both engines): `add_node("T", {"lst":[1,2,3],
  "tup":(1,2,3)})` round-trips `{'lst': {'__list__': [1,2,3]}, 'tup':
  {'__tuple__': [1,2,3]}}` — list/tuple read back distinctly.
- PREREG: `docs/research/engine_substrate/GAMMA_PYO3_REROUTE_PREREG.md`,
  registered and committed before `py.rs` was touched.
- Diff, final: exactly two files changed —
  `runners/dsl/src/py.rs` (+12/-1, one `for` loop body) and the rebuilt
  `.so`. Nothing else in the repo was edited (confirmed: `git diff --stat`
  against `aa6c939` shows only these two paths).

---

## 1. AR1 — empirical baseline, measured before the change

27 files flagged (PREREG §0.4 — a superset of the brief's stale "18",
re-grepped fresh; union of (a) 17 files combining a literal `add_production(`
call with a type-filtered node-count assertion, and (b) 12 files anywhere
in `tests/*.py` using the raw, unfiltered `.node_count()`/`.edge_count()`
APIs — the genuinely highest-risk shape once §0.2's `load_seed_manifest`
finding is accounted for). Run against the **unmodified** `aa6c939` engine,
full width, no scoping:

```
1 failed, 378 passed, 9 skipped in 133.18s (0:02:13)
```

The one failure —
`tests/test_held_prediction_attention_migrated.py::test_20x15_projection_is_complete_epoch_bounded_and_behavioral`
— is `ModuleNotFoundError: No module named 'cv2'`, a pre-existing,
environment-only gap (optional `cv2` dependency not installed in this
worktree's Python), confirmed unrelated by inspection (the failure is in
`import cv2` inside `domains/vision_graph.py`, several frames before any
Γ/production code runs). This is the AR1 baseline this rung's AR2 diff is
measured against.

---

## 2. AR2 — the diff, and why the verdict is NO-GO

### 2.1 The 27-file re-run (changed engine)

```
5 failed, 374 passed, 9 skipped in 341.63s (0:05:41)
```

Diff against §1's baseline: **4 net-new reds** (the cv2 failure carries
over unchanged):

| Test | New? |
|---|---|
| `test_persistence_migrated.py::test_round_trip_is_faithful` | **new** |
| `test_photon_eye_held_prediction_migrated.py::test_opt_in_adds_exactly_one_graph_cell_per_receptor` | **new** |
| `test_rules_checkpoint.py::test_old_checkpoint_without_rules_key_loads_with_warning` | **new** |
| `test_rust_engine_parity.py::test_graph_round_trip_via_dict` | **new** |

### 2.2 The broader 96-file sweep (every file with a literal `add_production(`
call, not just the 27 flagged) — paired, both engines rebuilt for this
comparison

This was not in the PREREG's minimum bar but is exactly what AR4 calls for
("every `tests/*.py` file that touches `add_production` at all"), and it
matters: it caught a regression (§2.4) that the 27-file set alone did not
include, because the affected test doesn't call `add_production` directly
— it calls a Rust-internal helper (`_native.Substrate`, same PyO3 class,
different Python entry point) inside a nested loop.

**Baseline** (rebuilt via `git stash` of the `py.rs` edit + a fresh
`maturin develop`, sha256 `f87f857c...` — bit-identical source to §1's
baseline, independently re-verified via `engine_provenance()` before this
run):

```
10 failed, 1309 passed, 1 error in 741.69s (0:12:21)
```

**Changed** (sha256 `f16265ed...`):

```
13 failed, 1306 passed, 1 error in 902.11s (0:15:02)
```

The 1 error both sides (`tests/test_speech_semiotics.py`, `import av` →
`ModuleNotFoundError`) is another pre-existing, environment-only gap,
unrelated by inspection. **Diff, paired node-id sets (`comm`-style, exact):**
10 of the baseline's reds are identical strings in the changed run's red
list (unchanged — pre-existing, confirmed NOT caused by this rung, see
below) plus **exactly 3 net-new reds**:

```
FAILED tests/test_analogical_relative_ranking.py::test_same_count_flagged_or_not_depending_on_distribution
FAILED tests/test_rules_checkpoint.py::test_old_checkpoint_without_rules_key_loads_with_warning
FAILED tests/test_rust_engine_parity.py::test_graph_round_trip_via_dict
```

**A methodological correction made live, worth recording plainly because it
is exactly the kind of thing "measure, don't assume" exists to catch:** on
first read of the changed-engine-only run, the 8 `test_codec_graph_resident.py`
HEVC failures plus `test_rust_engine_ext_7c.py`'s step-count failure LOOKED
like reroute-caused regressions (one produces outright wrong decoded values
— `chroma_format_idc == 0` instead of `1`; the other a wrong `run_rules`
fixpoint step count, `2` instead of `>= 3`). Before writing that up as a
regression, they were checked directly against a freshly rebuilt **baseline**
engine — and **all of them fail identically on the baseline, unmodified
engine too.** They are pre-existing, unrelated failures (confirmed via a
targeted 4-test rerun against a clean baseline rebuild, sha256 matching
§1's exactly) — NOT evidence about this rung's change. Only the 3 listed
above are genuinely new. This correction is reported here rather than
silently fixed in an earlier draft, because it is itself informative: it is
easy to over-attribute a large, unrelated-but-superficially-similar-shaped
red block to a change under test, and the fix is always the same — pair
against a real baseline, not intuition.

Combining §2.1's and §2.2's diffs (union, deduped by test id): **5 distinct
net-new reds, total, across every file examined in this rung**:

1. `test_rust_engine_parity.py::test_graph_round_trip_via_dict`
2. `test_photon_eye_held_prediction_migrated.py::test_opt_in_adds_exactly_one_graph_cell_per_receptor`
3. `test_persistence_migrated.py::test_round_trip_is_faithful`
4. `test_rules_checkpoint.py::test_old_checkpoint_without_rules_key_loads_with_warning`
5. `test_analogical_relative_ranking.py::test_same_count_flagged_or_not_depending_on_distribution`

### 2.3 Classification 1/2 (honest count updates) — #1 and #2

**#1, `test_rust_engine_parity.py::test_graph_round_trip_via_dict`** — this
is the PREREG's own §0.5 PREDICTION, confirmed exactly:

```
assert s2.node_count() == 2
E   assert 7 == 2
```

`add_production` runs before `a`/`b` are created; the mirror mints 5 nodes
(1 `GammaGrammar` + 1 `GammaProduction` + 2 `GammaNodePattern` + 1
`Term.Lit` for the default weight — the exact shape
`GAMMA_REFLECTION_WIRING_RESULTS.md` §2.1 already live-demonstrated for the
Rust-inherent path); `graph_to_dict()`/`graph_from_dict()` faithfully
round-trip them, so `s2.node_count()` honestly reads 7. **Traceable, single
cause, exactly predicted — a correct test update, not a regression.**

**#2, `test_photon_eye_held_prediction_migrated.py`** — the test builds two
`GraphEye`s (`baseline`, `enabled={"held_prediction":"decay"}`) via seed
loading (not a direct `add_production(` call — this one flows entirely
through `load_seed_manifest`'s internal productions loop, §0.2) and asserts
`enabled.node_count() == baseline.node_count() + N + 1` for a literal `N`.
Because `enabled`'s boot path registers additional productions the
`baseline` path doesn't (the held-prediction machinery's own admissibility
declarations), and each extra production now costs ~5 mirror nodes, the two
paths' overhead no longer cancels in the difference the way it did when
`add_production` was graph-inert. **Traceable to the same root cause as
#1 — a correct test update (the formula needs a mirror-overhead term), not
a regression.**

### 2.4 Classification 3 (genuine regression, root-caused) — #5, population-statistics corruption

`test_analogical_relative_ranking.py::_substrate()` (line 41) calls
`s.add_production(...)` inside a **triple-nested loop**: `4 node types × 4
node types × 12 edge types = 192 productions`, unconditionally, every time
a test in this file builds a fresh substrate:

```python
def _substrate():
    s = _native.Substrate()
    for src_t in _NODE_TYPES:
        for tgt_t in _NODE_TYPES:
            for et in _EDGE_TYPES:
                s.add_production({...})
    return s
```

192 productions × ~5 mirror nodes each ≈ **960 extra graph nodes**, all of
type `GammaGrammar`/`GammaProduction`/`GammaNodePattern`/`Term.Lit`, none of
which carry any of the `common` structural edge types
(`domains/architecture_assessment.py::detect_god_object`'s diversity
vocabulary). `detect_god_object` computes its outlier cutoff from **every
node in the graph, unfiltered**:

```python
all_nodes = list(substrate.nodes())          # NOT type-filtered
divs = [diversity(n) for n in all_nodes]      # mirror nodes: diversity == 0
mean = sum(divs) / len(divs)
std = (sum((d - mean) ** 2 for d in divs) / len(divs)) ** 0.5
cutoff = mean + k * std
```

Injecting ~960 zero-diversity nodes into `divs` pulls `mean` toward 0 and
reshapes `std`, moving `cutoff` — which is exactly why the test's "dense
graph: subject should be unremarkable among equally-diverse peers" case now
flags the subject as an outlier when it previously (correctly) didn't. **This
is not a count assertion that needs bumping — it is a real, silent change
in the OUTPUT VERDICT of an entirely unrelated subsystem** (an architecture
smell detector) caused purely by the volume of mirror nodes a heavy
`add_production` caller now injects into the shared graph. Any subsystem in
this codebase that scans `substrate.nodes()`/`graph_to_dict()["nodes"]`
without a type filter to compute a population statistic is exposed to this
same class of corruption — `detect_god_object` is the one instance found,
not necessarily the only one that exists (a full audit of every
unfiltered-population scan in the codebase was not attempted; out of this
rung's scope and not needed to establish the NO-GO).

### 2.5 Classification 4 (genuine regression, root-caused, UNBOUNDED) — #3 and #4

`test_persistence_migrated.py::test_round_trip_is_faithful` and
`test_rules_checkpoint.py::test_old_checkpoint_without_rules_key_loads_with_warning`
both fail the same way — `loaded.s.node_count()` measurably higher than the
pre-save count, by an amount proportional to the number of productions the
booted world's seeds registered (261 nodes for a `WorldAdapter()`'s default
seed set; 393 for the `_boot_chat_adapter()` fixture). **Root cause, read
directly in `substrate/world_adapter.py`** (this rung did NOT edit this
file — reading it is how the mechanism was found):

```python
# WorldAdapter.load(), substrate/world_adapter.py:6171
s = srs.Substrate()
s.graph_from_dict(blob["graph"])           # restores the graph AS SAVED —
                                            # already includes the ORIGINAL
                                            # mirror nodes, since graph_to_dict()
                                            # dumped them too.
for p in blob["grammar"]["productions"]:
    try:
        s._inner.add_production(p)          # <-- replays EVERY production,
    except Exception:                        #     re-minting a SECOND mirror
        pass                                 #     set on top of the first.
```

`save()`'s `"grammar"` key is `self.s.grammar_to_json()` — `checker.grammar`'s
own productions, independent of the dumped graph. Before this rung, replaying
them via `add_production` on load was a pure `checker.grammar` mutation:
harmless to repeat, because it never touched `self.graph` — this is exactly
the design assumption the comment above `save()` documents ("replay the
saved Γ productions ... so lazily-admitted edge-types stay admissible after
a load"). **This rung's reroute makes that assumption false**: every
`load()` call now mints a brand-new mirror subgraph for every production in
`blob["grammar"]["productions"]`, ON TOP OF the mirror nodes already
restored from `blob["graph"]` (because `save()` dumped them too, the first
time). Live-demonstrated, not just reasoned about — 5 consecutive
save→load cycles on the same small seeded world:

```
cycle 0: nodes=1011 edges=1011
cycle 1: nodes=1272 edges=1271   (+261 / +260)
cycle 2: nodes=1533 edges=1531   (+261 / +260)
cycle 3: nodes=1794 edges=1791   (+261 / +260)
cycle 4: nodes=2055 edges=2051   (+261 / +260)
```

**Linear, constant-increment, no sign of convergence across 5 cycles** —
this is not a one-time step to a new (higher, honest) steady-state count; it
is unbounded compounding growth on every single reload. A long-running
process that checkpoints and resumes periodically (exactly the daemon's own
documented operating pattern — `scripts/jabberwock_daemon.py`'s
checkpoint/resume loop this whole codebase is built around) would see its
graph grow by a fixed spurious increment forever. **This is squarely AR2's
first registered NO-GO condition** ("the risk is genuinely unbounded") and
**its second** simultaneously ("the fix would require touching more than the
PyO3 binding itself" — the fix belongs in `WorldAdapter.load()`, outside
`py.rs`, outside this rung's file-scope, and not something to bundle into
this rung's own gate per the PREREG's own §5 commitment not to touch
`world_adapter.py`).

---

## 3. AR3 — the reroute's own correctness, live-demonstrated (independent of the NO-GO verdict — the mechanism itself works as designed)

The PREREG registered these as required evidence IF GO; they are reported
here because they were run and are true, and because they are what makes
§2's regressions a real trade-off rather than a broken build — the reroute
does exactly what it was built to do, the problem is entirely in what two
OTHER pieces of code assumed about the old, graph-inert behaviour.

**(a) Real graph mirror via the PyO3 path** (previously: none —
`GAMMA_REFLECTION_WIRING_RESULTS.md` §2.2 item 1 verified this negatively):

```python
s = srs.Substrate()
s.add_production({"src": {"type": "A", "var": "src"}, "edge_type": "e",
                   "tgt": {"type": "B", "var": "tgt"},
                   "provenance": "ar3_live_demo"})
d = s.graph_to_dict()
# node types present: ['GammaGrammar', 'GammaNodePattern', 'GammaProduction', 'Term.Lit']
```

**(b) `gamma_epoch.bump()` now fires through the PyO3 path** (previously
silently bypassed — the exact bug `GAMMA_REFLECTION_WIRING_RESULTS.md` §2.2
item 1 named and left unfixed, re-verified here through the Python binding
instead of the Rust inherent method):

```python
before = s._inner.jit_report()   # (compiled, rules, gamma_epoch) = (0, 0, 0)
s.add_production({...})
after = s._inner.jit_report()    # (0, 0, 1)
```

**(c) `ConsistencyChecker.grammar`/`check_edge` unchanged for every existing
caller** — an admissible edge added successfully, an inadmissible one
correctly rejected (`InadmissibleEdge`), `admissible_moves` returning the
expected weight, all on the SAME substrate that also has a real graph
mirror:

```python
s.add_production({...})               # A -e-> B admissible
a, b, c = s.add_node('A'), s.add_node('B'), s.add_node('C')
s.add_edge(a, 'e', b)                 # succeeds
s.add_edge(a, 'links_to', c)          # InadmissibleEdge — CONFIRMED
s.admissible_moves(a, 'e', [('B', None)])   # [('B', {}, 1.0)] — unchanged shape
```

`grammar_to_json`/`jsonio.rs` were not touched by this rung's diff (`git
diff` confirms zero changes outside `py.rs`), so byte-identical wire format
holds by construction, not just by spot-check.

---

## 4. AR4 — full regression

- **`cargo test --lib`** (debug, `--test-threads=1` per the prior rung's
  own documented flakiness-under-parallelism finding for this crate),
  changed source: **740 passed, 0 failed, 4 ignored** — identical to the
  prior rung's own final committed number for `aa6c939`. Not independently
  re-paired against a fresh baseline `cargo test` run in this rung: the
  `py.rs` edit is entirely inside a `#[pymethods]` impl block (PyO3
  bindings, invoked only through the Python extension module), which
  `cargo test --lib`'s Rust-only unit-test harness does not exercise at
  all — there is no code path by which this diff could change a
  `cargo test` outcome, so the paired-baseline run would be theatre, not
  evidence. (Contrast with the Python-level runs above, which are the
  actual traffic this reroute affects and were paired for real.)
- **The full 96-file / 129-call-site sweep** — §2.2, paired, both engines
  freshly built in this rung: baseline 10 failed / 1309 passed / 1 error,
  changed 13 failed / 1306 passed / 1 error, exactly 3 net-new reds, all
  individually root-caused (§2.3/§2.4).
- **The 27-file AR1 superset** (§1/§2.1) — the highest-risk-shaped set,
  paired: baseline 1 failed / 378 passed / 9 skipped, changed 5 failed /
  374 passed / 9 skipped, 4 net-new reds (2 overlap with the 96-file set's
  3; 2 are unique to this set — `test_persistence_migrated.py` and
  `test_photon_eye_held_prediction_migrated.py`, both seed-boot-driven
  rather than direct `add_production(` calls, confirming §0.2's prediction
  that the blast radius extends past the literal call-site count).
- **`boot_gamma_meta`/`grow_gamma`/`_append_production` (the third,
  disjoint mechanism named in the prior rung's §2.2 item 2)** — confirmed
  by READING the code (`substrate/world_adapter.py:7624-7643`), not
  assumed: `_append_production` calls `self.s.add_node("Production", ...)`
  and `self.inner.add_edge(...)` directly — it never calls `add_production`
  in any form (neither the PyO3 binding nor, transitively, the Rust
  inherent method). This rung's reroute cannot reach it. No test run was
  needed to falsify this beyond the reading, since there is no call edge
  for the reroute to affect; the broader 96-file and 27-file sweeps above
  incidentally exercise `boot_gamma_meta`-adjacent seed content anyway
  (many of the flagged files boot full seed sets) and show no reds
  attributable to that mechanism.
- **Methodology note, matching the prior rung's own §4b precedent for a
  multi-hour run on shared hardware**: a full, unscoped `pytest -k
  migrated` (the prior rung's own ~9800-outcome, 3+ hour run) was **not**
  re-run in this rung. Given (1) the reroute's blast radius was already
  measured directly and completely for the two highest-risk-shaped sets
  (96 files covering every literal call site; 27 files covering every
  count-API risk shape, a strict superset of what a broader sweep would
  additionally need to catch per §0.2's own reasoning about WHERE the risk
  concentrates), and (2) the verdict is NO-GO on independently sufficient
  evidence found within that scope (§2.4/§2.5 — a single genuinely
  unbounded regression is enough to decide, more red node ids elsewhere
  would not change the verdict, only its size), spending another
  3-hour/shared-box budget on a full unscoped sweep would not have changed
  the decision and was not a responsible use of the box for a NO-GO already
  independently established. This is the explicit methodology-naming this
  PREREG committed to providing rather than silently doing a smaller sweep.

---

## 5. What a future GO would require (named, not attempted — the reroute stays NO-GO here)

Both regression mechanisms found are fixable, but both fixes fall outside
this rung's registered scope:

1. **`WorldAdapter.load()`** (`substrate/world_adapter.py:6171`) needs to
   stop re-minting a mirror for productions the restored graph already
   contains a mirror for — e.g. skip the graph-mirror side effect on
   replay (a `add_production_no_mirror` inherent variant, or a flag), or
   have `load()` reconstruct `checker.grammar` from the graph's own mirror
   (`grammar_from_graph`, already built by the prior rung) instead of
   replaying `add_production` at all — which would also be a small step
   toward the "row 1 = row 2" unification `GAMMA_REFLECTION_WIRING_RESULTS.md`
   §7 named as future work.
2. **Any unfiltered `substrate.nodes()` population scan** (§2.4's
   `detect_god_object` is the one instance found, not audited to be the
   only one) needs either a type filter, or the mirror's own node types
   need to be excluded from "the graph" as such subsystems see it — a
   design question (should Γ's own admissibility bookkeeping be visible to
   agent-facing population statistics at all?) that is bigger than this
   rung's charter and deserves its own pre-registration if pursued.

A future rung revisiting this reroute should pre-register against BOTH of
these fixes explicitly, not just re-attempt the same one-line `py.rs`
change — the `py.rs` change itself is correct and complete (§3); the
blocking work is entirely in these two downstream consumers.

---

## 6. Reproduce

```bash
cd /home/matt/ocelot-gamma-pyo3-reroute/runners/dsl
export PATH="/home/matt/.cargo/bin:$PATH"          # rustup's cargo, NOT Homebrew's
export RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/lib -C link-arg=-lpython3.13"
export LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/lib:$LD_LIBRARY_PATH"
CARGO_BUILD_JOBS=2 systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  cargo test --lib -- --test-threads=1        # 740 passed, 0 failed, 4 ignored

cd /home/matt/ocelot-gamma-pyo3-reroute
python3 -m venv .build-venv && source .build-venv/bin/activate
export VIRTUAL_ENV=$PWD/.build-venv
cd runners/dsl
CARGO_BUILD_JOBS=2 systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  maturin develop --release --skip-install
```

Live demonstration of the unbounded-growth regression (Python, no test
harness needed):

```python
import sys, tempfile, os
sys.path.insert(0, "runners/dsl/python")
from substrate.world_adapter import WorldAdapter

wa = WorldAdapter()
a = wa.ensure_world_instance("Rock", "rock_1")
b = wa.ensure_world_instance("Rock", "rock_2")
wa.ensure_instance_edge_type("near")
wa.s.add_edge(a, "near", b)

tmp = tempfile.mkdtemp()
cur = wa
for i in range(4):
    path = os.path.join(tmp, f"ckpt_{i}.json")
    cur.save(path)
    cur = WorldAdapter.load(path)
    print(cur.s.node_count(), cur.s.edge_count())
# 1011,1011 -> 1272,1271 -> 1533,1531 -> 1794,1791 -> 2055,2051
# (unbounded: linear +261/+260 every cycle, confirmed with the CHANGED
# engine; with the baseline engine this sequence is flat.)
```

AR2's population-statistics-corruption regression:

```bash
python3 -m pytest tests/test_analogical_relative_ranking.py::test_same_count_flagged_or_not_depending_on_distribution -q
# changed engine: FAILED.  baseline engine: PASSED.
```
