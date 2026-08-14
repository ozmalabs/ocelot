# AVX-512 PORTABILITY FIX — RESULTS

**Status: LANDED. GO.** Predictions from `AVX512_PORTABILITY_FIX_PREREG.md`
measured against a from-scratch worktree build+test on this machine. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/avx512-portability-fix`, branch
`avx512-portability-fix`, base `main@fecd35e`.

---

## 1. What was broken, confirmed by reading the compiler's own output

`cargo build --release` in `runners/dsl/` failed with **29 `error[E0658]`**
on this machine's `rustc 1.87.0 (17067e9ac 2025-05-09) (Homebrew)` (the only
toolchain `rustup toolchain list` shows installed — no nightly available).
Full log captured before any edit:
`/tmp/.../avx512_build_errors.txt` (631 lines; 29 `^error` lines, 0 other
error classes).

**Two files, not one.** The task brief named only `l1_hot_paths.rs`;
`l3_lqr.rs` carries the majority — **21 of 29 errors** — via its AVX-512
FP64 matmul (`mul_avx512`) and AVX-512-BF16 DARE/Kalman matmul paths
(`mul_bf16_inner`, `mul_bf16_pre_b_inner`). `l1_hot_paths.rs` accounts for
the remaining 4 real-site errors (`find_attr_sym_avx512`). (2 errors are a
duplicate crate-root diagnostic span artifact — see below — and 2 are the
`avx512bf16` half of two combined `#[target_feature]` attributes.)

**Two distinct tracking issues, each verified against the exact `note:`
line and cross-checked against the shipped stdarch source, not assumed:**

| gate | issue | what it covers | error count | evidence |
|---|---|---|---|---|
| `stdarch_x86_avx512` | [#111137](https://github.com/rust-lang/rust/issues/111137) | calling an AVX-512 intrinsic *function* (`_mm512_set1_epi32`, `_mm512_loadu_si512`, `_mm512_cmpeq_epi32_mask`, `_mm512_i32gather_epi32`, `_mm512_setzero_ps`, `_mm512_dpbf16_ps`, `_mm512_storeu_ps`, `_mm512_set1_pd`, `_mm512_loadu_pd`, `_mm512_fmadd_pd`, `_mm512_storeu_pd`) or naming the `__m512bh` type | 23 | Every one of these functions carries `#[unstable(feature = "stdarch_x86_avx512", issue = "111137")]` directly on the `fn` item in this rustc's own shipped `stdarch` source, confirmed by grep against `$(rustc --print sysroot)/lib/rustlib/src/rust/library/stdarch/crates/core_arch/src/x86/avx512f.rs` |
| `avx512_target_feature` | [#44839](https://github.com/rust-lang/rust/issues/44839) | writing `#[target_feature(enable = "avx512f")]` / `"avx512f,avx512bf16"` at all | 6 | `l1_hot_paths.rs:170`, `l3_lqr.rs:257,367,423` — fires on the attribute itself, independent of #111137 (confirmed distinct: it fires even on `mul_avx512`, which touches no BF16 type) |

The 23rd `stdarch_x86_avx512` error was attributed to `src/lib.rs:1:1`–`192`
(the entire crate-root doc comment through `pub mod sigma_lognormal;`) — a
diagnostic-span artifact of the crate-level stability check, not a distinct
AVX-512 site (`sigma_lognormal.rs` itself: 0 hits for
`_mm512`/`avx512`/`target_feature`, confirmed by grep). It did not require
separate handling; fixing the real sites made it disappear too (confirmed
in the after-build).

A third file, `h264_dct.rs`, uses `#[target_feature(enable = "avx2")]`
(stable already, 0 errors) — unrelated, untouched.

**Both gates are already stabilized on a sufficiently new stable rustc.**
`docs/research/program_synthesis/PROGRAM_SYNTHESIS_ARC6_WIRE_HANDS.md` §SS6
(this repo's own prior research, same day) independently installed
`rustc 1.97.1` via `rustup` in a different sandbox and reports the crate
compiling clean there with **zero source changes** — this machine's
toolchain, not the code, is the binding constraint.

## 2. Stable substitution: checked, does not exist on this toolchain

Confirmed by reading, not inferred: every one of the 11 intrinsics this
file needs carries `#[unstable(...)]` directly on its definition in this
rustc's own shipped `stdarch` source. There is no "use the stable name"
fix available at 1.87.0 for the gather/mask/BF16-dot-product/FMA operations
this code needs — the fix at this toolchain vintage is binary: upgrade the
toolchain, or don't compile the AVX-512 path on it. This machine has no
nightly installed, and the task specifies fixing this "on this machine's
default stable toolchain" — so the toolchain-upgrade path (which the ARC6
doc already used as a one-off workaround in an ephemeral, different sandbox)
was not treated as the fix here; it doesn't generalise to every future
stable-1.87-pinned box (e.g. CI) this crate might need to build on.

**Decision (unchanged from PREREG): feature-gate**, matching this crate's
existing pattern for platform/hardware-conditional code (`cabac_baseline`,
`gpu_me`).

## 3. The fix, as landed

1. **`runners/dsl/Cargo.toml`**: added `avx512 = []` under `[features]`
   (default OFF), with a doc comment stating the exact opt-in requirement
   — a nightly toolchain (or a stable release new enough to have
   stabilized both gates, empirically confirmed present at 1.97.1 and
   absent at 1.87.0) plus AVX-512F(+BF16) hardware, built with
   `cargo build --release --features avx512`.
2. **`runners/dsl/src/lib.rs`**: added, at the crate root (before any
   item, after the existing module-map doc comment):
   ```rust
   #![cfg_attr(feature = "avx512", feature(stdarch_x86_avx512, avx512_target_feature))]
   ```
   No-op (nothing emitted) when the feature is off — the default build
   never asks the stable compiler to accept an unstable crate attribute.
3. **`runners/dsl/src/l1_hot_paths.rs`**: `find_attr_sym_avx512`'s
   definition and the dispatch block inside `find_attr_sym` (trait method
   on `TypedGraph`) changed from `#[cfg(target_arch = "x86_64")]` to
   `#[cfg(all(target_arch = "x86_64", feature = "avx512"))]`. Scalar
   fallback (`attrs.0.iter().position(...)`) untouched, now the only
   compiled path by default.
4. **`runners/dsl/src/l3_lqr.rs`**: three unsafe intrinsic-bodied
   functions (`mul_avx512`, `mul_bf16_inner`, `mul_bf16_pre_b_inner`)
   gained `#[cfg(all(target_arch = "x86_64", feature = "avx512"))]`. Their
   PUBLIC dispatcher callers (`mul`, `mul_bf16`, `mul_bf16_pre_b`) were
   **not** removed or gated — `src/l3_kalman_nd.rs` calls `mul_bf16`,
   `mul_bf16_pre_b`, and `pack_for_bf16_b` unconditionally outside any cfg
   guard (confirmed by grep), so removing these dispatchers would have
   broken that caller's compile on a default (feature-off) build. Instead
   each dispatcher's SIMD-taking branch is now wrapped in
   `#[cfg(feature = "avx512")] { if <dims ok> && is_x86_feature_detected!(...) { return unsafe {...}; } }`,
   falling through unconditionally to the pre-existing scalar path
   (`self.mul_scalar` / `self.mul`) when the feature is off.
   `pack_for_bf16_b`, `Bf16PackedB`, `to_f64_mat`, `fp64_to_bf16`,
   `bf16_to_fp64` use no intrinsics (confirmed by reading each — pure bit
   manipulation) and are untouched; `mul_bf16`'s default fallback is now
   exact FP64 `mul` rather than a BF16 approximation — strictly *more*
   precise than the path it replaces, not less.
5. **Runtime gate stays correct.** `is_x86_feature_detected!("avx512f"/"avx512bf16")`
   calls are already stable on 1.87.0 (none of the 29 original errors were
   attributed to any such call site) — only the intrinsic functions and
   the `#[target_feature]` attribute needed gating. The runtime probe is
   preserved verbatim, simply nested inside `#[cfg(feature = "avx512")]`;
   with the feature off, there is no AVX-512 codegen left in the binary
   for a runtime check to guard, so nothing is left "guarding code that
   can't run."
6. **Tests.** `avx512_matches_scalar_across_dimensions` and
   `bf16_matmul_within_precision_tolerance` (`l3_lqr.rs`) gained an
   explicit `!cfg!(feature = "avx512")` term in their skip condition, so
   the skip is honest about *why* (feature off, not just "hardware
   lacks it") rather than silently exercising a same-scalar comparison
   that would trivially pass once the SIMD branch is compiled out.
   `find_attr_sym`'s three tests needed no change (they call the trait
   method only, never the `_avx512` fn directly).

---

## 4. Predictions vs. measured — P1 through P4

### P1 — `cargo build --release` (default features), zero errors

```
cd runners/dsl && systemd-run --scope --user -p MemoryMax=16G -p MemoryHigh=14G \
  -- cargo build --release
```

**Result: `Finished \`release\` profile [optimized] target(s) in 3m 44s`.
0 errors. 42 pre-existing style warnings (unused imports, snake_case
naming, unnecessary parens — none new, none touching the files this fix
changed beyond what was already there before). `--check-cfg` output
confirms `avx512` is registered as a known feature and NOT enabled:
`--cfg feature="default" ... --check-cfg cfg(feature, values("avx512",
"cabac_baseline", "default", "gpu_me"))`.**

**P1: CONFIRMED.**

### P4 — `--features avx512` still fails, but with a DIFFERENT error class

```
cargo build --features avx512
```

**Result: fails — but with exactly ONE `error[E0554]: #![feature] may not
be used on the stable release channel`** (not 29 scattered `E0658`s). This
is precisely the intended behaviour: turning the feature on is a promise
the caller is on a supporting toolchain (nightly, or a stable release ≥
whatever stabilized both gates); on this machine's plain stable 1.87 it
is refused cleanly and immediately, rather than silently doing nothing or
reproducing the original 29-error wall.

**P4: CONFIRMED.**

### P2/P3 — correctness + suite-wide, `cargo test --lib`

**A build note that is not optional** (already documented in this repo's
own prior research, `META_SHAPE_FIRST_CLASS_RESULTS.md` §7.1): `Cargo.toml`
pins `pyo3 = { features = ["extension-module", ...] }` unconditionally, so
a plain `cargo test --lib` cannot LINK a test binary on Linux (undefined
`PyErr_*`/`PyBytes_*`/`PyObject_Call`/... — pyo3's extension-module mode
deliberately doesn't link libpython, since normally Python provides those
symbols at `dlopen` time; a standalone test binary has no Python process
supplying them). This is **pre-existing and unrelated to this fix** — it
reproduces identically on an unmodified tree. The documented workaround
(same doc, verified still correct on this machine, `python3 --version` =
3.13.5, `sysconfig.LIBDIR` = `/home/linuxbrew/.linuxbrew/opt/python@3.13/lib`,
matching `libpython3.13`):

```
RUSTFLAGS="-C link-arg=-L$(python3 -c 'import sysconfig;print(sysconfig.get_config_var("LIBDIR"))') -C link-arg=-lpython3.13" \
LD_LIBRARY_PATH=/home/linuxbrew/.linuxbrew/lib cargo test --lib -- --test-threads=1
```

**First run:** `773 passed; 1 failed; 4 ignored` — the one failure was
`framebuffer::tests::seqlock_read_races_writer_and_stays_honest`, a test
whose own ~25-line doc comment names it as an accepted, load-sensitive,
non-deterministic hazard ("a busy-spin loop over a fixed wall-clock
window... even a vanishingly small per-attempt probability accumulates to
a near-certain hit... does not claim to make the theoretical gap
impossible; it makes an accidental hit during an ordinary CI run
negligible") — unrelated to AVX-512/`find_attr_sym`/matrix multiply by
subject matter (shared-memory framebuffer seqlock reader/writer race).
Verified flaky, not a regression: reran in isolation 3× → **3/3 pass**;
reran the FULL suite a second time → **774 passed, 0 failed, 4 ignored**,
finishing in 2.02s.

**Test count: 774 passed + 4 ignored = 778 total, matching the task
brief's "~774 tests as of today" exactly on the passing count.** This is
the first clean from-source Rust build+test baseline measured on this
machine.

**AVX-512-touched tests specifically, all green in the clean run:**

```
l1_hot_paths::tests::find_attr_sym_empty ... ok
l1_hot_paths::tests::find_attr_sym_scalar_path ... ok
l1_hot_paths::tests::find_attr_sym_simd_path ... ok
l3_lqr::tests::avx512_matches_scalar_across_dimensions ... ok
l3_lqr::tests::bf16_matmul_within_precision_tolerance ... ok
l3_lqr::tests::mat_multiplication_identity_is_self ... ok
(+ 6 more l3_lqr:: DARE/LQR tests, all ok)
```

`find_attr_sym_simd_path` (20 keys — exceeds the 16-wide SIMD block plus a
tail) exercises exactly the code path that used to dispatch to
`find_attr_sym_avx512`; it now runs the scalar body unconditionally and
still asserts every position correctly — scalar output is byte-identical
to before this change (the scalar bodies were never touched, only reached
unconditionally instead of conditionally).

**P2: CONFIRMED** (scalar-path correctness unchanged). **P3: CONFIRMED**
(774/774 clean; the single non-deterministic red is independently
verified pre-existing and unrelated, not asserted by fiat).

### Python-facing regression surface

Searched for any Python code or test referencing `find_attr_sym`/
`attr_sym`: **zero hits**, in both `tests/*.py` and the full tree
(`grep -rln "find_attr_sym" --include="*.py"`). `find_attr_sym` is
Rust-internal infrastructure with unit-test coverage only — it is not yet
wired into any Python-visible attribute-lookup call path, so there is no
Python-facing regression surface for this specific function to check. As
a broader sanity check, the freshly built engine was installed via this
repo's own sanctioned `scripts/engine_build.sh` (which — as its own
in-tree comment already documents — errors on its last `python` line on
this box, since only `python3` is on PATH; the `.so` copy had already
completed by then, per the same documented gotcha
`PROGRAM_SYNTHESIS_ARC6_WIRE_HANDS.md` names). Ran the two remaining
provenance-record steps directly with `python3`, then:

```
PYTHONPATH=runners/dsl/python:. python3 -c "
import substrate_rs as srs
s = srs.Substrate()
nid = s.add_node('T', {'lst':[1,2,3]})
print(s.node(nid)['attrs'])
"
# -> {'lst': [1, 2, 3]}  (smoke import + basic graph op, OK)

python3 -m pytest tests/test_engine_provenance_migrated.py -q
# -> 9 passed, 1 skipped
```

Engine hash `723d95b78a3b40c421bdfb1e06603338a532fef3f31d81c2adc4ce9581a5d0dd`,
provenance clean (`build_is_stale() == []`) against this branch's Rust
source.

---

## 5. GO / NO-GO

**GO.** All four preregistered predictions confirmed:

- P1: `cargo build --release` (default), 0 errors, was 29.
- P2: scalar-path correctness unchanged (byte-identical bodies, same test
  assertions pass).
- P3: `cargo test --lib` 774/774 clean (the one non-deterministic red is
  independently confirmed pre-existing/unrelated, not asserted by fiat).
- P4: `--features avx512` on this stable toolchain still fails, but with
  a single, clean, correctly-attributed `E0554` — the gate is live, not a
  silent no-op.

**What this does NOT establish:**

- The `avx512` feature path was never actually exercised end-to-end on
  this machine (no nightly toolchain and no AVX-512F hardware confirmed
  present here) — P4 only demonstrates the gate correctly REFUSES on an
  unsupported toolchain, not that it correctly SUCCEEDS on a supporting
  one. That would need either installing a nightly toolchain here or
  testing on the original 9600X-class box; out of scope for this rung.
- The exact stable release that stabilized both `stdarch_x86_avx512` and
  `avx512_target_feature` for these specific intrinsics is bounded (≤
  1.97.1, per the ARC6 doc's own successful build) but not pinned exactly
  — nailing the precise minimum stable version was not attempted here and
  is not needed for the fix to be correct (the feature doc comment states
  the bound as measured, not as an exact version).
- This fix does not change the crate's general Linux `cargo test --lib`
  linking gap against `pyo3`'s `extension-module` feature (undefined
  `PyErr_*`/etc. without the documented `RUSTFLAGS`/`LD_LIBRARY_PATH`
  workaround) — that is a separate, already-documented, pre-existing
  condition of this crate's `Cargo.toml`, reproduced and worked around
  here exactly as prior research already prescribes, not newly fixed.
- Performance of the scalar fallback vs. the (now default-off) AVX-512
  path was not benchmarked in this rung — this was a portability/
  correctness fix, not a performance rung. The original module doc's
  "3-8x faster" claim for the SIMD path is unverified either way here.

## 6. Worktree / commit

- Worktree: `/home/matt/ozmadev/ocelot-worktrees/avx512-portability-fix`
- Branch: `avx512-portability-fix`
- Base: `main@fecd35e`
- Files changed: `runners/dsl/Cargo.toml`, `runners/dsl/src/lib.rs`,
  `runners/dsl/src/l1_hot_paths.rs`, `runners/dsl/src/l3_lqr.rs`,
  `runners/dsl/python/substrate_rs/_native.abi3.so` +
  `_native.build.json` (rebuilt engine artifact + provenance record, per
  this repo's own `scripts/engine_build.sh` protocol), plus this PREREG/
  RESULTS pair.
- Not merged into `main` — commit left on the branch per task instruction.
