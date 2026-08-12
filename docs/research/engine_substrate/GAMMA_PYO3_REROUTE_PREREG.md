# Γ PyO3 reroute — pre-registration

**Posture:** MEASURE-THEN-BUILD, exactly as `GAMMA_REFLECTION_WIRING_RESULTS.md`
§7 recommended for this exact follow-up: *"if a future rung wants full
unification, it should be pre-registered and gated exactly like this one,
with the PyO3-reroute risk measured empirically (run the flagged Python test
files first, in isolation, before touching the shared binding) rather than
assumed."* This doc registers the GO/NO-GO bars **before** editing `py.rs`,
per this folder's own house discipline.

**Charter.** Reroute `PySubstrate::add_production`
(`runners/dsl/src/py.rs:7803-7820`) from `inner.checker.grammar.add(p)`
(direct) to `inner.add_production(p)` (the Rust inherent method the prior
rung made graph-resident, mirroring every production into a real
`GammaGrammar`/`GammaProduction`/`GammaNodePattern` subgraph and firing
`gamma_epoch.bump()`). This is the "row 1 = row 2" unification named but not
built in `GAMMA_REFLECTION_WIRING_RESULTS.md` §2.2/§7 — specifically the
**PyO3-reroute half** of it, not the "graph becomes the source of truth for
`check_edge`" half (that remains out of scope, per §7's own second, larger
and separately-risked item).

**Engine baseline (unchanged source, `main` tip `aa6c939`).**
`runners/dsl/python/substrate_rs/_native.abi3.so` sha256 (rebuilt fresh in
this worktree from unmodified `aa6c939` source, `CARGO_BUILD_JOBS=2`, memory
capped): `f87f857cf54a19a3942bd8878093e533d6b4896c9ec397f6e13f530a76165916`
(`domains.engine_provenance.engine_provenance()`: `source_match = "own"`,
`stale_rust = []`). Note: `aa6c939`'s *committed* `.so` hashes
`d7acb906da8ffb2c02c6feccd3bf3ecc62241b956f6343c336479a0f5e363843` — the
same hash `GAMMA_REFLECTION_WIRING_RESULTS.md` reports as its own "final
engine WITH changes" (that rung's work is already merged into `main`, so
`aa6c939`'s checked-in binary already contains `grammar_reflect.rs` +
`Substrate::add_production`'s Rust-inherent mirror). The rebuilt hash here
differs only because the release profile is not bit-reproducible across
separate `cargo build` invocations on this box (same non-determinism the
prior rung already documented) — confirmed same-source via `git status`/`git
diff` showing a clean worktree before the rebuild.

Worktree: `/home/matt/ocelot-gamma-pyo3-reroute`, branch to be created
`gamma-pyo3-reroute`, detached from `main` at `aa6c939`.

Coherence probe (passed): `add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})`
round-trips `{'lst': {'__list__': [1,2,3]}, 'tup': {'__tuple__': [1,2,3]}}` —
list/tuple read back distinctly.

---

## 0. Investigation findings (re-grepped fresh, not trusting the prior rung's stale count)

**0.1 The call-site count is confirmed unchanged.** `grep -ro "add_production("
tests/*.py | wc -l` → **129** call sites, across **96** files — identical to
`GAMMA_REFLECTION_WIRING_RESULTS.md` §2.2's figure. `substrate/world_adapter.py`
has **5** additional call sites (lines 6101, 6171, 7580, 9585, 9885) via
`self.inner.add_production(...)` / `s._inner.add_production(p)` /
`self.s.add_production(...)` — all going through the same PyO3 binding.

**0.2 A materially larger blast radius than "129 call sites," found during
this rung's own investigation, not anticipated by the brief.**
`PySubstrate::load_seed_manifest` (`py.rs:1469-1568`) has its OWN internal
productions loop:

```rust
// 3) Productions: re-use the existing add_production path. ...
if let Some(J::Array(prods)) = m.get("productions") {
    for p in prods {
        let py_prod = json_to_pyobj(py, p)?;
        let _ = self.add_production(py, &py_prod);   // the exact PyO3 method this rung reroutes
        productions_added += 1;
    }
}
```

This means **every seed manifest with a `"productions"` key, loaded via
`load_seed_manifest` (the standard seed-boot path essentially every
migrated-suite test that boots an agent goes through), will mint mirror
graph nodes per production once this reroute lands** — not just the 129
literal `add_production(` call sites in test bodies. Measured:
**591 of 892 seed manifests under `seeds/*.json` contain a `"productions"`
key** (`grep -rl '"productions"' seeds/*.json | wc -l`). The true blast
radius of this reroute is therefore closer to "every seed-booted test," not
"129 test call sites" — this is the single most important thing AR1's
measurement below has to account for, and it is why AR4 (full regression)
carries more evidential weight here than AR1's targeted file list, not less.

Reassuringly: `nodes_added`/`edges_added` (the counters `load_seed_manifest`
returns in its `summary` dict, read by e.g.
`test_prog_read_llvm_migrated.py:206`'s `assert summary["nodes"] ==
len(manifest["nodes"])`) are accumulated in step 1's node-insertion loop
ONLY, before step 3's productions loop runs — so `summary["nodes"]` is NOT
itself affected by the mirror's extra node inserts. That specific assertion
shape is therefore safe by construction. But anything that calls
`s.node_count()` (the RAW graph total) on a substrate that booted a seed
with productions, and compares it to a literal or to a value captured before
seed boot, is exactly the risk class.

**0.3 The third mechanism (`substrate/world_adapter.py`'s
`_append_production`/`grow_gamma`/`boot_gamma_meta`) is confirmed, by
reading the code (not assumed), to NOT call `add_production` at all — the
PyO3 binding or, transitively, the Rust inherent method:**

```python
def _append_production(self, production) -> object:
    ...
    pid = self.s.add_node("Production", attrs)          # generic add_node, not add_production
    src = self.s.add_node("NodePattern", {...})
    tgt = self.s.add_node("NodePattern", {...})
    ...
    self.inner.add_edge(self.gamma_root, "production", pid, {"index": n})
    self.inner.add_edge(pid, "pattern.src", src)
    self.inner.add_edge(pid, "pattern.tgt", tgt)
    return pid
```

It builds `Production`/`NodePattern`-typed nodes directly via generic
`add_node`/`add_edge` calls — never touches `checker.grammar`, never calls
`add_production` in any form. **This rung's reroute cannot affect it**, and
this is verified by reading, not by re-running the file (AR4 still runs the
relevant migrated tests as a check, not because this reading is in doubt).

**0.4 Files flagged for AR1 — re-grepped, not the prior rung's stale "18."**
Two searches, unioned:

1. Files combining a literal `add_production(` call with a TYPE-FILTERED
   node-count assertion in the same file (`grep -E
   "len\([^)]*node|graph_to_dict\(\)\[.nodes.\]|node_count|len\(.*\.nodes\(\)|assert.*len\(.*nodes"`):
   **17 files** (differs from the prior rung's "18" — expected, since the
   prior rung's count was itself a `grep` estimate over a codebase that has
   moved; not investigated further since this rung does its own independent
   count rather than trying to reproduce the stale one).
2. Files anywhere in `tests/*.py` calling the **raw, unfiltered** `.node_count()`
   or `.edge_count()` APIs (the actual highest-risk shape, per §0.2's
   seed-manifest finding — a type-filtered `s.nodes("SomeType")` count is
   immune to the mirror's `GammaGrammar`/`GammaProduction`/`GammaNodePattern`/
   `Term.*` nodes, since those are a disjoint type vocabulary by design; a
   raw total is not): **12 files**.

Union: **27 files** (list below), superseding the brief's "18" as the AR1
target set. `tests/test_substrate.py` is included in the union but is worth
flagging as likely-lower-risk on inspection — it primarily exercises the
**Python** `substrate.Substrate`/`TypedGraph` (the world-adapter-facing
class CLAUDE.md documents as separate from the Rust runtime), not
necessarily `substrate_rs.Substrate` — confirmed empirically in AR1's run
below rather than assumed away here.

```
tests/test_allocentric_retinal_prior_migrated.py
tests/test_architecture_cortex.py
tests/test_autonomous_agent.py
tests/test_concept_expansions.py
tests/test_cost_model.py
tests/test_fixpoint_settle_migrated.py
tests/test_foveated_photon_layout_migrated.py
tests/test_held_prediction_attention_migrated.py
tests/test_identity_dynamics.py
tests/test_insight_detection.py
tests/test_install_streak_filters.py
tests/test_llvm_ir_cfg.py
tests/test_llvm_ir_io.py
tests/test_neural_networks_seed.py
tests/test_persistence_migrated.py
tests/test_photon_eye_held_prediction_migrated.py
tests/test_prog_read_llvm_migrated.py
tests/test_real_pybullet_natural_language_embodied_autonomy_migrated.py
tests/test_reflex_net_migrated.py
tests/test_remove_rule_graph_diff.py
tests/test_rule_inference.py
tests/test_rules_checkpoint.py
tests/test_runtime_discovery.py
tests/test_rust_engine_parity.py
tests/test_substrate.py
tests/test_value_domain_migrated.py
tests/test_video_format_parse.py
```

**0.5 Manual read of the highest-risk single case, done in advance because
it is the clearest predictable break.** `tests/test_rust_engine_parity.py::
test_graph_round_trip_via_dict` (lines 133-152):

```python
def test_graph_round_trip_via_dict(s):
    s.add_production(srs.Production(
        src=srs.NodePattern(type="X", var="src"), edge_type="e",
        tgt=srs.NodePattern(type="X", var="tgt"),
        where=None, weight=None, provenance="test:x_e_x",
    ))
    a = s.add_node("X", {"label": "alpha"})
    b = s.add_node("X", {"label": "beta"})
    s.add_edge(a, "e", b)
    dump = s.graph_to_dict()
    s2 = srs.Substrate()
    s2.graph_from_dict(dump)
    assert s2.node_count() == 2      # <-- literal, pre-mirror count
    assert s2.edge_count() == 1      # <-- literal, pre-mirror count
```

`add_production` runs BEFORE `a`/`b` are created, on a fresh `Substrate()`.
Post-reroute, that call will mint the mirror subgraph (per
`GAMMA_REFLECTION_WIRING_RESULTS.md` §2.1's live-verified count for a single
production with no `where`-clause: 1 `GammaGrammar` + 1 `GammaProduction` +
2 `GammaNodePattern` + 1 `Term.Lit` (default weight) = **5** extra nodes,
plus the edges wiring them). `dump = s.graph_to_dict()` will include those 5
extra nodes, so `s2.node_count()` will read **7**, not 2, and `s2.edge_count()`
will similarly be higher than 1. **This is registered here, in advance of
building, as the predicted single clearest "honest count update" case** —
AR2 must show this is exactly what happens (not something stranger) before
treating it as a correct update rather than an unexplained regression.

The file's other two `node_count()` uses (lines 188/198,
`test_transaction_rollback_on_exception`) capture `n_before` AFTER its own
`add_production` call (line 181) and compare it to the SAME substrate's
count after a rolled-back transaction — self-relative, not a literal —
predicted safe.

---

## 1. AR1 — empirical risk measurement BEFORE touching the binding

**Method:** run the 27 flagged files (§0.4) against the **unmodified**
`aa6c939` engine (sha256 `f87f857c...`, this doc's own header), full run, no
scoping, `-n 4` under a `systemd-run --scope --user -p MemoryMax=8G -p
MemoryHigh=7G` ceiling. Capture the complete PASS/FAIL/SKIP node-id
accounting (not a bare count) as the baseline this rung's AR2 diff is
measured against.

**Threshold for AR1 to be "done":** every flagged file collects and runs
(no collection errors caused by this rung's own environment setup — a
pre-existing, unrelated environment gap such as a missing optional
dependency is recorded and excluded from the diff, not silently dropped);
the full baseline red/skip list is written down as a paired artifact before
any `py.rs` edit is made.

---

## 2. AR2 — GO/NO-GO on the reroute, registered before making the change

**GO** iff, after making the one-line-per-call reroute and re-running the
SAME 27-file set (plus AR4's broader sweep):

(a) every newly-red node id is EITHER (i) unaffected — same verdict as
    baseline — or (ii) breaks in a way that is a **correct, honest update**:
    the test was asserting a node/edge count that predates the mirror
    becoming real, and the new (higher) count is the mirror's own nodes
    showing up where they provably should (traced to specific `add_production`
    call(s) in that test, per §0.5's methodology) — not an unexplained
    value, not a crash, not wrong data;

(b) `ConsistencyChecker.grammar`/`check_edge` behaviour is BYTE-IDENTICAL
    for every existing caller — same admissibility verdicts, same
    `grammar_to_json` output shape for the same productions, before and
    after. This is checked directly (not inferred from passing tests alone),
    because it is the single highest-risk correctness bar: the reroute must
    add a mirror, not change what is admissible;

(c) `gamma_epoch.bump()` now demonstrably fires through the PyO3 path (this
    is not a risk to gate against — it is the documented bug being fixed —
    but its fix must be shown live, not just asserted, and must not itself
    destabilize any L2-dispatcher-consuming test, checked as part of AR4).

**NO-GO**, precisely characterized rather than forced through, iff: (i) any
flagged test breaks in a way that is NOT a traceable, honest count update —
e.g. wrong VALUES (not just higher counts), a crash unrelated to node
counting, or a change to what edges are admissible; or (ii) AR4's full
regression surfaces new reds outside the flagged-file/seed-manifest blast
radius already named in §0, indicating the risk was not actually bounded by
the count-shaped-assertion model this PREREG used to scope AR1.

A NO-GO is a complete, acceptable result per this project's standing
culture — this file commits, in advance, to reporting one plainly if AR2's
evidence says the reroute isn't safe yet, rather than editing this
threshold after seeing results.

---

## 3. AR3 — the reroute itself, if GO

`py.rs:7803-7820`'s `PySubstrate::add_production`, changing:

```rust
for p in parsed.productions {
    inner.checker.grammar.add(p);
}
```

to:

```rust
for p in parsed.productions {
    inner.add_production(p);
}
```

(`inner.add_production` returns a `ProdIdx` per `substrate.rs:832-852`; the
binding currently discards the return value of `.add()` too, so discarding
`.add_production()`'s return preserves the existing `-> PyResult<()>`
signature — no API-shape change.)

Live evidence required, mirroring the prior rung's own §2.1/§8
demonstrations, this time through the Python binding instead of the Rust
inherent method directly:

- (a) `s.add_production({...})` via the **PyO3** path now produces a real
  `GammaProduction`-typed node reachable via `graph_to_dict()`, matching the
  prior rung's `declare_shares_shape()` demonstration shape (1 `GammaGrammar`
  + 1 `GammaProduction` + 2 `GammaNodePattern` + N `Term.*` for weight/where).
- (b) `gamma_epoch.bump()` fires on a PyO3-driven `add_production` call —
  re-run the prior rung's own live epoch-bypass demonstration (§2.2 item 1:
  "add via PyO3, inspect `graph_to_dict()`, confirm no mirror node exists")
  and confirm the OPPOSITE result now holds (mirror node exists, epoch
  value changes across the call).
- (c) `ConsistencyChecker.grammar`/`check_edge` unchanged for every existing
  caller — `admissible_moves`/`InadmissibleEdge` behaviour identical before
  and after for a fixed sequence of `add_production` + `add_edge` calls.

---

## 4. AR4 — full regression, matching the prior rung's own scope

1. `cargo test --lib` (debug, `--test-threads=1` per the prior rung's own
   documented flakiness-under-parallelism finding for this crate), paired
   before/after.
2. **Every** `tests/*.py` file that touches `add_production` at all — the
   full 96-file/129-call-site set named in §0.1, not just the 27 flagged in
   §0.4 — run in full, paired failing-node-id lists.
3. `pytest -k migrated`, at minimum the seed-boot/`world_adapter` paths that
   call `boot_gamma_meta`/`grow_gamma` (to confirm §0.3's by-reading
   conclusion empirically, expected to be a clean pass-through given it's
   read to never call `add_production`), scaled up to the full migrated
   suite if the time/memory budget on this shared box allows within a
   single session — following the prior rung's own §4b precedent for how to
   handle a multi-hour run responsibly: **a full paired baseline-vs-changed
   run at equal width is the ideal but not always affordable in one
   sitting; where it isn't, the substitute is a full changed-engine run
   plus a TARGETED re-run of every flagged red node id against a freshly
   rebuilt baseline engine — the same regression question asked directly,
   named explicitly as the method used, not silently substituted.**
4. Every command that could be memory-heavy wrapped in `systemd-run --scope
   --user -p MemoryMax=8G -p MemoryHigh=7G --`, `free -h` checked first,
   one heavy process at a time — per this box's live home-infrastructure
   constraint (this rung's own explicit brief, not just the prior rung's
   precedent).

---

## 5. What this rung does NOT touch (explicit, matching the brief's file-scope constraint)

- `runners/dsl/src/grammar_reflect.rs` and the Rust inherent
  `Substrate::add_production` — both already correct, built by the prior
  rung. This rung only reroutes the PyO3 binding to call the existing
  method.
- `substrate/grammar.py`, `substrate/world_adapter.py`'s `boot_gamma_meta`/
  `grow_gamma`/`_append_production` — confirmed in §0.3 to be a disjoint
  mechanism this reroute cannot reach.
- `domains/`, `seeds/`, program-synthesis files — untouched, except any
  Python TEST file AR2's investigation determines needs an honest,
  traceable count-literal update (not a workaround), which will be named
  explicitly in the RESULTS doc if it happens.

---

## 6. Reporting commitment

The RESULTS doc will report, in this order: AR1's measured baseline (paired
node-id list, not a count); the GO/NO-GO call against §2's registered bars,
with each broken test's classification (honest update vs. regression) shown
explicitly rather than summarized as a single pass/fail count; AR3's live
evidence if GO; AR4's full regression; and — matching this folder's own
recurring discipline — every environmental gotcha hit along the way, even if
unrelated to this rung's own code, because a future rung on this same box
will hit the same wall otherwise.
