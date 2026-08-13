# ENGINE CORRECTNESS — `(Str,Str)` LEXICOGRAPHIC FOLLOW-ON — PRE-REGISTRATION

*Branch `cmp-value-lexicographic-followon`, worktree
`/home/matt/ocelot-cmp-value-lex-followon`, based on `main` @ `3719b50`. The
engine is built in THIS worktree (`scripts/engine_build.sh`), never in the
canonical tree.*

*Committed BEFORE any code is written (the call-site enumeration below is
read-only investigation, done to scope the bars — no `.rs` file has been
edited by this rung as of this commit).*

---

## 0. WHAT THIS RUNG IS

A bounded follow-on to `CMP_VALUE_SURFACE_FIX_RESULTS.md` (merged, branch
`cmp-value-surface-fix`), which fixed the `(Surface,Surface)` Ord/Eq
inconsistency and left `(Str,Str)` as a **registered, precisely-scoped
NO-GO** (§4 of that doc): `cmp_value`'s `(Str,Str)` arm
(`value.rs:369`, `x.0.cmp(&y.0)`) compares interned `Sym` IDs, which are
assigned in **boot-history-dependent order**, not byte/alphabetical order.
This is self-consistent (`PartialEq`/`Hash` agree with it — no data loss,
unlike the `Surface` defect) but **not lexicographic**, so `sorted`/`min`/
`max`/`Lt` over string literals return a boot-order-dependent answer, not an
alphabetical one.

That prior rung's own §4.4 named the scoped alternative to the rejected
project-wide interner-threading refactor: split call sites into
**canonicalisation-only** (needs a *consistent* order, doesn't care which —
leave `cmp_value` alone) and **reported-order** (the order a caller/test sees
as meaningful — needs real lexicographic order), and fix ONLY the second
class via a **separate, interner-aware comparator used at those specific call
sites**, since every reported-order site already has an `Interner` in scope.

This rung executes that follow-on. Deliverable is either:

- a **fix with a live before/after demonstration** (a real reported-order
  case that was boot-history-dependent before, byte-lexicographic after); or
- an honest NO-GO / smaller-than-expected result, if the call-site
  enumeration below turns out wrong on closer reading.

**Explicitly out of scope** (restated from the assigning brief): `cmp_value`'s
own signature or its `(Str,Str)` arm; any canonicalisation-only call site;
`PartialEq`/`Hash`; a project-wide interner-threading refactor.

---

## 1. THE CALL-SITE ENUMERATION (investigation done for this prereg)

Every `cmp_value` call site in `runners/dsl/src/*.rs` was read (113 matches
across 8 files: `value.rs`, `term.rs`, `prog_eval.rs`, `persist.rs`,
`synth_enumerate.rs`, `py.rs`, `shape_decode.rs`, `argmin_tie.rs`), classified
by what the comparison's RESULT is used for.

### 1.1 Canonicalisation-only (leave untouched — confirmed, not just assumed)

- **`persist.rs`** (`decode_value`, lines 203/210/246): `Set`/`FrozenSet`
  dedup-on-load and bare-object → `Dict` key sort. Internal storage order for
  round-tripping persisted data; membership is what a Set means, not
  position.
- **`term.rs`** dict/pairs `sort_by(cmp_value)` (lines 3375, 3451, 3614,
  4005, 4924, 5354, 6546, 7243): `MkDict`, anti-unification's shared-key
  iteration, dict construction. Canonical key order for a cmp-sorted-vec
  `Dict` representation — the prior rung's own §4.4 named "dict key sort" as
  canonicalisation explicitly.
- **`prog_eval.rs`** dict-pair `sort_by` (lines 817, 1063, 1695, 2127, 2142,
  2224, 2675) and the `Equal`-only lookups (804, 980, 1811): dict
  item-assign/construction/lookup. Same class as above; the `== Equal`
  lookups are unaffected by *which* consistent order is used at all.
- **`synth_enumerate.rs`** (1360, 2134, 2139, 2157, 2162) and **`py.rs`**
  (711): all `Dict` construction (synthesis-result dicts, Python→Value dict
  conversion). Same class.
- **`shape_decode.rs`** (23 sites): read in full. Every one sorts two
  relation-tuple frames by the SAME order before pairing them element-wise
  for correspondence/equality/offset-inference (`build_candidate`,
  `infer_translate_offset`, `frames_equal`, `frames_symdiff`,
  `frame_value_stream`) — any consistent total order works because both
  sides are sorted by it identically; the order is never itself read as
  "alphabetical." One near-miss inspected closely: `shape_decode.rs:5124-5129`
  breaks a velocity tie by `keys[a]` vs `keys[b]` (`cmp_value`) to produce a
  depth RANK that becomes an output field — closer to reported-order in
  spirit, but the keys compared there are coordinate/predicate tuples from a
  spatial domain (not literal strings in the corpus), the tie only fires on
  an exact velocity collision, and changing it would re-canonicalise a
  depth-ordering scheme with no test asserting alphabetical intent. Recorded
  here as an examined-and-excluded edge case, not silently skipped.

### 1.2 Reported-order sites (the fix target)

Everywhere `cmp_value`'s outcome IS the thing a caller/test observes —
a returned extremum, a returned index, or a returned boolean truth value:

| # | site | file:line | TermNode / builtin | interner already in scope? |
|---|---|---|---|---|
| 1 | `cmp_bool` | `term.rs:7787-7805` (call at `:7798`) | `Lt`/`Lte`/`Gt`/`Gte` (dispatch `:5439-5450`) | yes, `ctx: &mut EvalCtx` |
| 2 | `numeric_minmax` | `term.rs:7974-8001` (call at `:7987`) | `Min`/`Max` (`:7209-7210`) | yes, `ctx` |
| 3 | `numeric_argmin` | `term.rs:7958-7973` (call at `:7966`) | `ArgMin` (`:7211`) | yes, `ctx` |
| 4 | `numeric_argmax` | `term.rs:8003-8030` (call at `:8020`) | `ArgMax` (`:7212`) | yes, `ctx` |
| 5 | `min_or_max_over` | `term.rs:9243-9317` (call at `:9277`) | `MinOver`/`MaxOver` (`:5776,5779`) | yes, `ctx` |
| 6 | `argmin_or_argmax_over` | `term.rs:9381-...` (calls at `:9439,:9453`) | `ArgminOver`/`ArgmaxOver`/`ArgminUnique` (`:5821-5835`) | yes, `ctx` |
| 7 | `"min"`/`"max"` extern | `prog_eval.rs:1376-1398` (call at `:1387`) | Python `min()`/`max()` builtin | yes, `interner` param |
| 8 | `"sorted"` extern | `prog_eval.rs:1527-1536` (call at `:1535`) | Python `sorted()` builtin | yes, `interner` param |

Two AUDIT-ONLY `cmp_value` calls were found and EXCLUDED deliberately:
`audit_index_selector` (`term.rs:8055`) and `audit_binder_selector`
(`term.rs:9232`) both compare a re-evaluated winner to the recorded one for
**exact equality** (disagreement detection, `selector_audit`/
`argmin_tie` instrumentation, default OFF). `Sym == Sym` equality does not
depend on which consistent order is used, so these need no change — they are
correctly excluded, not overlooked.

**Scope note, stated honestly:** the assigning brief's own examples
(`sorted`, `min`, `max`, `Lt`/`Gt`/`Lte`/`Gte`) are rows 1, 2, 7, 8 above.
Rows 3-6 (`ArgMin`/`ArgMax`/`MinOver`/`MaxOver`/`ArgminOver`/`ArgmaxOver`) are
this rung's own addition, found while reading the enumeration: they are the
Rust-native `Term` equivalent of the exact same operation as row 7
(`extern:min`/`max`) — an extremum selection over `Value`s that returns the
winning value or element to the caller. Leaving them on `cmp_value` while
fixing `extern:min`/`max` would leave the SAME semantic operation
inconsistently fixed depending only on which of two surfaces (Python-style
builtin vs native `Term`) a rule author used. They are included on that
basis; if measurement shows this to be wrong (e.g. a call site turns out to
also serve a canonicalisation role), it will be reported and reverted from
the fix set, not forced in.

---

## 2. REGISTERED BARS

**AR1 — the enumeration is accurate against current `main`.**
Every row in §1.2's table is re-verified by direct `Read` of the cited
lines at the point the fix is written (not trusted from this prereg's own
earlier read), and any drift from what is stated here is reported, not
silently absorbed.

**AR2 — the fix, `cmp_value_lex(a, b, interner)`.**
A new function in `value.rs`, structurally mirroring `cmp_value`'s match
(so nested Tuples/Lists/Sets containing strings compare correctly, not just
top-level `Str` values), differing ONLY in the `(Str,Str)` arm: resolve both
`Sym`s via `interner.resolve` and compare the resulting `&str` (byte/UTF-8
order). `cmp_value` itself is not edited — MET iff `git diff` shows zero
changed lines inside the existing `cmp_value` function body.

**AR3 — every §1.2 call site switched, and ONLY those.**
Each of the 8 rows calls `cmp_value_lex(..., interner)` instead of
`cmp_value` at exactly the cited call site. MET iff a `git diff` review shows
no edit inside any §1.1 (canonicalisation) function.

**AR4 — live before/after demonstration.**
At least one real reported-order case, run on the engine AS BUILT before this
fix and after, showing the order was boot-history-dependent before (i.e.
provably NOT alphabetical, by interning strings in an order chosen to make
alphabetical and boot order disagree) and is byte-lexicographic after. MET
iff the transcript is captured both sides, not asserted.

**AR5 — regression, `cargo test --release --lib -- --test-threads=1`,**
full run, before/after as PAIRED FAILING-TEST-NAME LISTS (never bare counts,
per this crate's own documented parallel-test noise in the prior rung's
§6.1). MET iff the after-list is a subset of (or equal to) the before-list.

**AR6 — coherence probe.**
`add_node("T", {"lst":[1,2,3], "tup":(1,2,3)})` → list and tuple stay
distinct (the standing regression probe named in the assigning brief). MET
iff it passes post-fix.

**AR7 — honest "what this does NOT establish" section in the results doc.**
Required regardless of GO/NO-GO outcome.

---

## 3. WHAT WOULD FALSIFY THE FIX / TURN IT NO-GO

1. **§1.2's table doesn't hold up on re-verification** (AR1) — a cited line
   has moved, or the site turns out to also serve canonicalisation. Reported
   precisely, fix scope narrowed to what's real.
2. **`cmp_value_lex` can't be written without changing `cmp_value`'s own
   signature or duplicating so much that the "separate comparator" framing
   breaks down.** Not expected (the match is self-contained, ~115 lines) but
   checked, not assumed.
3. **Any call site outside §1.2 needs to change to keep the fixed sites
   correct** (e.g. a Dict's key sort silently depended on being the same
   order `Lt` uses). Then the "clean split" claim is wrong and this is
   reported as a scope failure, not patched over.
4. **AR5's after-list is not a subset of the before-list.**

---

## 4. WHAT THIS RUNG WILL NOT DO

- Will not touch `cmp_value`'s signature, its `(Str,Str)` arm, `PartialEq`,
  or `Hash`.
- Will not touch any §1.1 canonicalisation-only call site, including the
  `shape_decode.rs:5124-5129` near-miss named and excluded above.
- Will not attempt the project-wide interner-threading refactor the prior
  rung rejected.
- Will not touch `main` or the canonical tree; engine built and committed in
  this worktree only.

---

## 5. PROTOCOL

```
export PATH="/home/matt/.cargo/bin:$PATH"
export RUSTFLAGS="-L /home/linuxbrew/.linuxbrew/lib -C link-arg=-lpython3.13"
export LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/lib:$LD_LIBRARY_PATH"
systemd-run --scope --user -p MemoryMax=16G -p MemoryHigh=14G -- \
    bash scripts/engine_build.sh
```

`--release`, `.so` never `cp`'d directly (the build script owns placement),
sha256 recorded for pre-fix and post-fix artifacts. Regression run under
`cargo test --release --lib -- --test-threads=1` (single-threaded — the
prior rung's own §6.1 finding that this crate's parallel run is noisy).
