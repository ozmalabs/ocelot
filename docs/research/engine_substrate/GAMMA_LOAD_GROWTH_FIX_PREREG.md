# Γ load-growth fix — pre-registration

**Posture:** MEASURE-THEN-BUILD, per this folder's own house discipline and
per `GAMMA_PYO3_REROUTE_RESULTS.md` §5's own explicit charter for a future
rung: *"a future rung revisiting this reroute should pre-register against
BOTH of these fixes explicitly."* This doc registers the GO/NO-GO bars, and
records the root-cause investigation, **before** any `py.rs` or
`world_adapter.py` edit is made.

**Charter.** Size, and if small enough build, the fix for
`WorldAdapter.load()`'s Γ-replay-on-load behaviour
(`substrate/world_adapter.py:6169-6173`) — the mechanism
`GAMMA_PYO3_REROUTE_RESULTS.md` §2.5 found causes **unbounded compounding
graph growth** (+261 nodes/cycle, measured over 5 cycles, no convergence)
once `PySubstrate::add_production` is rerouted through the now-graph-resident
Rust inherent method. Also size and, if small, fix §2.4's
`detect_god_object` population-statistics corruption. If both land clean,
re-attempt the PyO3 reroute itself (`GAMMA_PYO3_REROUTE_PREREG.md`'s AR3) and
re-run its empirical sweep to confirm both regressions are actually gone.

**Note on the actual reroute code:** the `py.rs` diff that produced the
NO-GO findings is not on `main` — it was judged unsafe and left out of the
merge (`GAMMA_PYO3_REROUTE_RESULTS.md` §0's diff description: `py.rs`
+12/-1, one `for`-loop body, rerouting `inner.checker.grammar.add(p)` to
`inner.add_production(p)`). This rung reconstructs it fresh (identical
change, per that doc's §6 reproduce section) only for AR4, on top of AR2/AR3's
fixes, gated the same way.

---

## 0. Root-cause investigation (done before registering the bars below)

**0.1 What `WorldAdapter.load()`'s replay is actually for.** Read in full
(`substrate/world_adapter.py:6119-6223`). `save()` writes TWO independent
representations of Γ into the checkpoint blob:

- `"graph"`: `self.s.graph_to_dict()` — the full `TypedGraph` node/edge dump.
  This is where any `GammaGrammar`/`GammaProduction`/`GammaNodePattern`
  mirror nodes live, IF any exist (today, on unrerouted `main`, none do,
  because the PyO3 `add_production` binding doesn't mint them — see 0.2).
- `"grammar"`: `self.s.grammar_to_json()` — `checker.grammar` (the actual
  `Vec<Production>` `check_edge` reads), a SEPARATE Rust struct that lives
  outside the `TypedGraph` entirely and is serialised via `jsonio.rs`'s own
  plain-JSON round-trip, independent of `graph_to_dict`/`graph_from_dict`.

`load()` calls `s.graph_from_dict(blob["graph"])` first — this restores
`inner.graph` (node ids preserved) but does **not** touch `inner.checker` at
all (confirmed by reading `py.rs:7923-7930`: `graph_from_dict` only
reassigns `inner.graph = g`). So after that call, `checker.grammar` is
whatever a fresh `srs.Substrate()` starts with — empty. The `for p in
blob["grammar"]["productions"]: s._inner.add_production(p)` loop is the
**only** mechanism that repopulates `checker.grammar`, i.e. the only thing
that makes `check_edge` actually gate correctly again after a load. This
answers the brief's question directly: **the replay is re-deriving
productions from the SEPARATE `grammar_to_json`/`jsonio.rs` persistence path
that exists independently of the graph dump — not re-walking seed
manifests** (no seed loading happens anywhere in `load()`) **and not
redundant with anything the graph dump alone restores** (the graph dump
restores mirror bookkeeping nodes if present; it does not and cannot restore
`checker.grammar`, a plain Rust struct, by itself). The replay is load-bearing
and necessary; it cannot simply be deleted.

**0.2 Why this is graph-inert on `main` today, and why it stops being
inert under the reroute.** `PySubstrate::add_production`
(`py.rs:7803-7820`, current `main`) is:

```rust
for p in parsed.productions {
    inner.checker.grammar.add(p);
}
```

— `checker.grammar` mutation ONLY, no call into the Rust inherent
`Substrate::add_production` (`substrate.rs:832-858`), so no
`grammar_reflect::production_to_subgraph` mirror write, no `gamma_epoch`
bump. This is exactly why `GAMMA_PYO3_REROUTE_RESULTS.md` §2.5 found the
growth bug ONLY manifests under a rerouted engine: today, replaying
`add_production` N times is a pure `checker.grammar.add` no-op-shaped
operation (each replay call re-adds the same `Production` values to the
`Vec`, which is itself wasteful — duplicate entries accumulate in
`checker.grammar` on every load — but this pre-existing, harmless-to-`graph`
duplication is out of THIS rung's charter; it does not touch `self.graph`
and was not what either prior rung measured or flagged). Once
`PySubstrate::add_production` is rerouted to `inner.add_production(p)`
(the mirroring method), the SAME replay loop starts minting 5 new graph
nodes per production, EVERY load, on top of the mirror nodes the graph dump
already restored (since `save()`'s `"graph"` key would, from that point on,
include the mirror from the ORIGINAL `add_production` calls too) — this is
§2.5's measured +261/cycle.

**0.3 Two persistence-shaped candidate fixes, evaluated, plus a third found
during investigation.**

- **(a) Stop replaying via `add_production`; reconstruct `checker.grammar`
  from the restored graph's `GammaGrammar` mirror via `grammar_from_graph`.**
  Evaluated and **rejected for this rung**: `grammar_from_graph`
  (`grammar_reflect.rs:246`) is not PyO3-exposed at all today (`grep` over
  `py.rs` confirms zero references), so this requires a NEW PyO3 binding —
  itself fine — but more importantly it is **only correct once the reroute
  has ALREADY landed and every production a saved world holds was minted
  through the mirroring path**. On the CURRENT (unrerouted) engine, no
  mirror exists in the graph at all for any of today's checkpoints or any
  checkpoint saved before a future reroute — building fix (a) alone, without
  the reroute landing atomically alongside it, would silently restore an
  EMPTY `checker.grammar` on every load (total loss of admissibility
  gating), which is categorically worse than the bug it replaces. Fix (a)
  is architecturally the more "the graph is authoritative" answer, but it is
  NOT safe to build or land independently of the reroute — it would need
  its own migration story for pre-reroute checkpoints (detect no mirror
  root present → fall back to replaying `"grammar"` — solvable, but a
  second code path, sized in §5 below, not attempted here).
- **(b) Keep replay, make `add_production` (or a variant) content-dedup
  before minting a mirror** — the `seeds/gap_awareness.json` dedup-guard
  precedent CLAUDE.md documents. Evaluated and **rejected as more complex
  than necessary**: content-equality dedup on a `GammaProduction` would need
  to walk the existing mirror (via `grammar_from_graph`, itself not exposed)
  and compare every replayed production against it — real design and Rust
  work, for a case where the ACTUAL invariant needed is much simpler (0.4).
- **(c) (found during investigation, not named in the brief, selected) Give
  `load()`'s replay a dedicated PyO3 method that restores `checker.grammar`
  WITHOUT touching the graph at all** — i.e., literally the CURRENT
  `add_production` body (`inner.checker.grammar.add(p)` only), moved to a
  new name (`add_production_no_mirror`) so it is decoupled from whatever the
  general `add_production` binding does. `load()`'s replay switches to call
  this instead. This is correct **today** (byte-identical behaviour to what
  `main` already does, since it doesn't exist yet — this rung is CREATING
  the decoupling, not changing current semantics) and stays correct after a
  future reroute of the general binding, because the general binding's
  mirror-writing behaviour becomes irrelevant to `load()`'s replay by
  construction. This requires **zero changes to `substrate.rs` or
  `grammar_reflect.rs`** (both explicitly out of this rung's file-scope) —
  it is a pure `py.rs` addition (one new `#[pymethods]` fn, ~15 lines,
  structurally identical to the existing `add_production` body) plus a
  one-line change in `world_adapter.py`'s `load()`.

**0.4 Selected: candidate (c).** It is strictly smaller than (a), does not
require exposing `grammar_from_graph` or touching `grammar_reflect.rs`/
`substrate.rs`, does not change `checker.grammar`'s restored CONTENT in any
way (still the exact same `Vec<Production>` from `blob["grammar"]
["productions"]`, same order, same values — verified as the correctness bar
in AR3 below), and is provably safe regardless of whether AR4's reroute
lands in this same rung or a future one (it does not depend on the reroute
landing atomically, unlike (a)).

**0.5 A residual named honestly, not fixed in this rung.** `Substrate`'s
`gamma_graph_root` field (`substrate.rs:135`, lazily created on first
mirrored `add_production` call) is **not** restored by `graph_from_dict` —
after a `load()`, a freshly-constructed `srs.Substrate()`'s
`gamma_graph_root` is `None` even though the restored `self.graph` may
already contain a `GammaGrammar` node (once the reroute lands and saves
start including one). If, post-load, a NEW production is added via the
(rerouted) general `add_production` binding — e.g.
`ensure_instance_edge_type` (`world_adapter.py:6092-6108`), a normal,
expected, at-runtime call — the mirror-writing path will lazily mint a
**second, disconnected** `GammaGrammar` root rather than reusing the
restored one. This does NOT reproduce the measured growth bug (that bug is
about REPLAYING already-persisted productions on every load; this is about
one genuinely NEW production, post-load, correctly costing ~5 mirror nodes
once — expected, bounded growth) and does NOT currently affect any live
code path (`grammar_from_graph`/`gamma_graph_root()` are not called from any
production Python code today — the mirror is write-only bookkeeping per
`GAMMA_REFLECTION_WIRING_RESULTS.md` §2's own honest boundary). Fixing it
would need a `substrate.rs` change (a `reconcile_gamma_graph_root`-shaped
method scanning for an existing `GammaGrammar` node on `graph_from_dict`),
which is outside this rung's file-scope. **Named here, sized, and left
alone** — see §5 (sizing) for what a future rung closing this would need.

---

## 1. AR1 — root-cause investigation (this section IS the deliverable; §0 above)

**Bar:** the root cause of the replay-on-load behaviour is identified by
reading the actual code (not inferred), candidates (a)/(b)/(c) are each
evaluated against what was found, and a choice is made with reasons, before
any code is edited. **Status: done, see §0. Verdict: proceed to AR2-AR5 —
the fix (candidate c) is small, self-contained, and does not require the
reroute to land atomically alongside it.**

---

## 2. AR2 — `detect_god_object` fix (`domains/architecture_assessment.py:478-529`)

**Root cause, confirmed by reading:** `all_nodes = list(substrate.nodes())`
is an UNFILTERED scan of every node in the graph, feeding
`diversity(n) = sum(1 for et in common if substrate.neighbours(n, et))` for
every one — a Γ-mirror node (`GammaGrammar`/`GammaProduction`/
`GammaNodePattern`/`Term.*`) has diversity 0 against this vocabulary
(`common` lists structural edge types like `has_reflex`/`owns_microtheory`;
mirror nodes never emit these), so injecting hundreds of them pulls `mean`
toward 0 and reshapes `std`, moving `cutoff` — a real verdict flip, not a
count assertion (§2.4 of the reroute results doc).

**Precedent found in `substrate/world_adapter.py`** (multiple sites, e.g.
line 6949: `if wn.type.startswith("Term.")` — "Term.* are graph machinery,
never instanced (no id)"): this codebase's existing convention for excluding
graph-machinery/administrative node types from population-facing logic is a
plain type-string check, not a new abstraction. No prior exclusion of
`Gamma*` types was found anywhere (`grep` over `domains/*.py` for
`GammaGrammar`/`GammaProduction`/`GammaNodePattern` returns nothing) — this
rung is the first to need it, consistent with the mirror being new.

**Fix, sized:** a small module-level tuple of excluded type strings +
one filter clause on `all_nodes`. ~5 lines, one function, no new
abstraction, no behaviour change for any graph that has never called
`add_production` (the excluded types never previously appeared in any
graph `detect_god_object` was run against — pre-reroute, they don't exist;
post-reroute, this is exactly what makes the smell-detector's population
correct again).

**Bar:** `test_analogical_relative_ranking.py::
test_same_count_flagged_or_not_depending_on_distribution` passes against
BOTH the current (unrerouted) engine (byte-identical behaviour — the filter
is a no-op when no Gamma/Term nodes exist) AND a rerouted engine (AR4) with
192-production `_substrate()` fixture's ~960 mirror nodes present.

---

## 3. AR3 — the load-growth fix (candidate (c) from §0.4)

**Build:**

1. `runners/dsl/src/py.rs`: new `#[pymethods] fn add_production_no_mirror`
   on `PySubstrate`, sibling to the existing `add_production`
   (`py.rs:7803-7820`) — identical body (`grammar_from_json` →
   `inner.checker.grammar.add(p)` per parsed production), diverging only in
   that it never calls `inner.add_production(p)` (the mirroring inherent
   method) and never will, regardless of what the general binding does.
2. `substrate/world_adapter.py:6171`: `s._inner.add_production(p)` →
   `s._inner.add_production_no_mirror(p)`. One line.

**Bars (GO iff all hold):**

- **B1 — content-fidelity.** `checker.grammar` after `load()` is
  content-identical (same productions, same order, same `where`/`weight`)
  to `checker.grammar` before `save()` — verified via `grammar_to_json()`
  equality before/after a save→load round trip, both on the unrerouted
  engine (regression check — must be byte-identical to today's behaviour)
  and, if AR4 proceeds, on the rerouted engine.
- **B2 — zero redundant growth.** 5+ consecutive save/load cycles on the
  same world (mirroring `GAMMA_PYO3_REROUTE_RESULTS.md` §2.5's own
  reproduce script) show **zero** node/edge growth on the UNREROUTED engine
  (already true today — this is the "did I break anything that works"
  check) and, once AR4's reroute is reapplied on top, likewise **zero**
  growth from replay alone (a world that adds no NEW productions between
  saves shows a flat node/edge count across all 5 cycles). Distinguish
  explicitly from growth caused by genuinely NEW productions added between
  saves (architecturally correct, not in scope to eliminate — not exercised
  by the flat-world reproduce script, called out if a different scenario is
  also measured).
- **B3 — admissibility unchanged.** A production restored via
  `add_production_no_mirror` gates `check_edge`/`admissible_moves`
  identically to one restored via the old path (same `InadmissibleEdge`
  behaviour for the same graph).

---

## 4. AR4 — re-attempt the PyO3 reroute, conditional on AR2/AR3 landing clean

If AR2 and AR3 both pass their bars: reconstruct
`GAMMA_PYO3_REROUTE_PREREG.md` §3's exact one-line-per-call `py.rs` change
(`PySubstrate::add_production`'s general binding, `inner.checker.grammar.add
(p)` → `inner.add_production(p)`), on top of AR2+AR3's fixes, and re-run:

- The same 27-file AR1 set and the 96-file/129-call-site sweep
  `GAMMA_PYO3_REROUTE_RESULTS.md` §1/§2.2 ran, paired failing-node-id lists
  against a freshly rebuilt baseline of THIS rung's own pre-reroute tree
  (i.e. AR2+AR3 applied, reroute not yet applied) — isolating exactly the
  reroute's own marginal effect, on top of an already-fixed foundation.
- `test_analogical_relative_ranking.py::
  test_same_count_flagged_or_not_depending_on_distribution` (§2.4's
  regression) — expect PASS.
- `test_persistence_migrated.py::test_round_trip_is_faithful` and
  `test_rules_checkpoint.py::test_old_checkpoint_without_rules_key_loads_with_warning`
  (§2.5's regression) — expect PASS (or, if either asserts a LITERAL count
  that predates the mirror, the SAME honest-count-update classification the
  prior rung already gave `test_rust_engine_parity.py`/
  `test_photon_eye_held_prediction_migrated.py` — distinguished explicitly,
  not silently reclassified).
- `test_rust_engine_parity.py::test_graph_round_trip_via_dict` and
  `test_photon_eye_held_prediction_migrated.py::
  test_opt_in_adds_exactly_one_graph_cell_per_receptor` — **expected to
  remain red**, unchanged from the prior rung's own finding (§2.3: honest
  count updates the mirror correctly requires, needing literal test-file
  edits this rung's file-scope excludes touching). Reported as
  pre-classified expected reds, not conflated with genuine regressions.

**GO for AR4** iff no NEW regression class appears beyond the two
pre-classified "honest count update" tests already known and named above.
**NO-GO for AR4 alone** does not retract AR2/AR3 — the load-growth and
`detect_god_object` fixes stand on their own merits regardless of whether
the broader reroute is re-attempted successfully.

---

## 5. AR5 — full regression

- `cargo test --lib` (debug, `--test-threads=1`), paired before/after AR2+AR3
  (the `py.rs` addition is a new sibling method — no existing Rust test
  should be affected; confirmed by running, not assumed).
- Every `add_production` call site across `tests/*.py` (129, per the prior
  rung's own grep) plus `substrate/world_adapter.py`'s 5 sites — paired
  failing-node-id lists, not counts, against the unrerouted engine first
  (AR2+AR3 alone, no reroute — must be a clean, zero-diff regression since
  candidate (c) changes nothing observable pre-reroute) and then, if AR4
  proceeds, against the rerouted engine per §4's bars.
- Every `WorldAdapter.load()`/checkpoint-related test
  (`grep -l "WorldAdapter.load\|\.load(path\|test_persistence\|checkpoint"`)
  run explicitly, paired.

---

## 6. What would make this bigger than one rung (stated in advance, not found yet)

Per the brief's own instruction: if AR1's investigation had found the
seed-reinstall-on-load behaviour load-bearing for a reason unrelated to
restoring checkpoint state, or found candidate (a)/(b) required to be safe,
this would stop here as an AR1-only sizing/NO-GO. **§0 found neither** —
candidate (c) is self-contained, needs no `substrate.rs`/
`grammar_reflect.rs` changes, and does not require the reroute to land
atomically. The one item genuinely sized-but-deferred is §0.5's
`gamma_graph_root` post-load fragmentation — real, but inert on every
existing live code path today, and requiring a `substrate.rs` change outside
this rung's file-scope; a future rung closing it would need: a
`Substrate::reconcile_gamma_graph_root(&mut self)` (or equivalent) that
scans `self.graph.nodes_of_type(GAMMA_GRAMMAR_NODE)` post-`graph_from_dict`
and sets `self.gamma_graph_root` to the (expected-unique) existing root
rather than leaving it `None`, PyO3-exposed, called from
`WorldAdapter.load()` after `graph_from_dict`. Estimated small (~20-30
Rust lines + 1 Python line) but explicitly not this rung's file-scope and
not required for AR2/AR3/AR4's own bars to pass.

---

## 7. Provenance (to be filled in RESULTS)

Worktree: `/home/matt/ocelot-gamma-load-growth-fix`, branch
`gamma-load-growth-fix`, detached from `main` at `3e3daa5` (verified at
worktree-creation time). Engine sha256s, build commands, and coherence-probe
output recorded in the RESULTS doc per this folder's standing template.
