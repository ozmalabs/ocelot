# AVX-512 PORTABILITY FIX — PREREG

**Status: PREREG. Investigation done, fix not yet written past this file.**
Registering the root cause and the chosen fix mechanism before editing
`runners/dsl/src/l1_hot_paths.rs` / `l3_lqr.rs` / `Cargo.toml`, per house
discipline.

**Base:** `main` at `fecd35e` (`Merge progsyn-rung1-tier1: 10 Tier-1 stdlib
Term ports, MBPP 49->54 measured`), verified with `git log --oneline -1 main`
immediately before branching. Worktree:
`/home/matt/ozmadev/ocelot-worktrees/avx512-portability-fix`, detached at
`fecd35e`, branch to be created at commit time:
`avx512-portability-fix`. `data/` symlinked
(`ln -s /home/matt/ozmadev/ocelot/data data`) — no pre-existing partial
`data/` directory was present in the fresh worktree (`git ls-files | grep
'^data/'` → 0 entries), so the documented nesting gotcha does not apply here.

**What prompted this rung.** `cargo build --release` in `runners/dsl/` fails
with 29 `E0658` compile errors on this machine's default toolchain
(`rustc 1.87.0 (17067e9ac 2025-05-09) (Homebrew)`, confirmed via
`rustc --version`; `rustup toolchain list` shows only this one stable
toolchain installed, no nightly). This blocked a merge-time from-source
verification step earlier today
(`docs/research/program_synthesis/PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_RUNG1_RESULTS.md`
/ `PROGRAM_SYNTHESIS_ARC6_WIRE_HANDS.md` §SS6, which worked around it by
installing a separate `rustup` stable toolchain — `rustc 1.97.1` — in an
ephemeral cloud sandbox rather than fixing the crate). Confirmed today
(2026-08-14) as genuinely pre-existing: the errors reproduce identically on
a from-scratch detached worktree at `fecd35e` with zero other changes, and
the file's own history traces to "Initial import of ocelot project"
(`26ca9ff`, 2026-08-10).

---

## 1. Root cause, read from the actual compiler output

Full log: `cargo build --release` (wrapped in `systemd-run --scope --user -p
MemoryMax=16G -p MemoryHigh=14G --`, respecting `.cargo/config.toml`'s
`jobs = 4` cap) → 29 `error[E0658]`, 0 other errors, in exactly two files:
`src/l1_hot_paths.rs` and `src/l3_lqr.rs` (the task brief named only
`l1_hot_paths.rs`; **`l3_lqr.rs` turns out to carry the majority of the
errors — 21 of 29 — via its AVX-512 FP64 matmul and AVX-512-BF16 DARE/Kalman
paths**, not previously called out). A third file, `src/h264_dct.rs`, uses
`#[target_feature(enable = "avx2")]` (stable, zero errors) and is unrelated.

**Two distinct tracking issues, confirmed by reading each error's `note:`
line, not assumed:**

- **`#[E0658] use of unstable library feature 'stdarch_x86_avx512'` (issue
  [#111137](https://github.com/rust-lang/rust/issues/111137)).** Fires on
  every *call site* of an AVX-512 intrinsic function
  (`_mm512_set1_epi32`, `_mm512_loadu_si512`, `_mm512_cmpeq_epi32_mask`,
  `_mm512_i32gather_epi32`, `_mm512_setzero_ps`, `_mm512_dpbf16_ps`,
  `_mm512_storeu_ps`, `_mm512_set1_pd`, `_mm512_loadu_pd`,
  `_mm512_fmadd_pd`, `_mm512_storeu_pd`) and on the `__m512bh` type used in
  a `std::mem::transmute`. Verified directly against the shipped
  `rust-src` component
  (`$(rustc --print sysroot)/lib/rustlib/src/rust/library/stdarch/crates/core_arch/src/x86/avx512f.rs`):
  every one of these functions carries
  `#[unstable(feature = "stdarch_x86_avx512", issue = "111137")]` directly
  on the `fn` item in this rustc's shipped stdarch source — this is a
  **library-stability gate on the function itself**, independent of
  whether the caller ever executes the call at runtime. 23 of the 29 errors
  are this kind (22 real call sites + 1 error attributed to the crate
  root span `src/lib.rs:1:1`–`192` covering `pub mod sigma_lognormal;`,
  which is a diagnostic-span artifact of the crate-level stability check,
  not a distinct AVX-512 usage — `sigma_lognormal.rs` itself has zero
  `_mm512`/`avx512`/`target_feature` hits, confirmed by grep).
- **`#[E0658] the target feature 'avx512f'/'avx512bf16' is currently
  unstable` (issue
  [#44839](https://github.com/rust-lang/rust/issues/44839), the
  `avx512_target_feature` gate).** Fires on the `#[target_feature(enable =
  "avx512f")]` / `#[target_feature(enable = "avx512f,avx512bf16")]`
  attributes themselves (`l1_hot_paths.rs:170`, `l3_lqr.rs:257`, `:367`,
  `:423` — 6 errors, one per feature name per attribute site). This is a
  **language-level gate on writing the attribute at all** on this
  toolchain, independent of the library-function gate above — confirmed
  distinct because it fires even on functions that only manipulate
  `__m512i`/`__m512d`/`f64` (`mul_avx512`) with no BF16 involvement.

**Both gates are satisfied simultaneously on a sufficiently new stable
rustc** — this is not a nightly-only feature that was later removed; it is
being incrementally stabilized. Corroborating evidence already in this
repo's own research record: `PROGRAM_SYNTHESIS_ARC6_WIRE_HANDS.md` §SS6
installed `rustc 1.97.1` via `rustup` in a *different* environment and
reports the crate compiled clean there with **zero source changes** — i.e.
some stable release between 1.87.0 (this machine, 2025-05) and 1.97.1
(2025-era later release) stabilized both `stdarch_x86_avx512` and
`avx512_target_feature` for the specific intrinsics this file uses. This
machine's toolchain is the constraint, not the code being permanently
broken.

---

## 2. Stable substitution — checked, does not apply on THIS machine's toolchain

Per the task brief's instruction to check for stable equivalents before
feature-gating: there is **no substitute available in `rustc 1.87.0`'s own
`core::arch::x86_64`** for any of the 11 distinct intrinsics used — I
confirmed this by reading the `#[unstable(...)]` attribute directly on each
function's definition in this rustc's shipped `stdarch` source (§1 above),
not by inference. AVX-512 stabilization on this specific toolchain is
categorically absent for the gather/mask/BF16-dot-product/FMA operations
this file needs; there is no "use the stable name instead" fix available
at 1.87.0 — the fix at this toolchain vintage is binary: upgrade the
toolchain, or don't compile this code path on it.

**This machine has no nightly toolchain installed**
(`rustup toolchain list` → one entry, `stable-x86_64-unknown-linux-gnu`,
active/default) and the task specifies fixing this "on this current
development machine['s]... default stable toolchain" without silently
routing around that by installing a newer toolchain as the load-bearing
fix (the ARC6 doc already recorded that path as a one-off environment
workaround in a *different*, ephemeral sandbox — not a fix to the crate
itself, and not repeatable on every future stable-1.87-pinned box this
crate might need to build on, e.g. CI).

**Decision: feature-gate, not substitute.** Per the task's own §3
guidance, this is exactly the "no clean stable substitution exists" case:
gate the fast paths behind an explicit, default-OFF Cargo feature (`avx512`),
matching the crate's existing pattern for platform/hardware-conditional
code (`cabac_baseline`, `gpu_me` — both already `[features]` entries in
`Cargo.toml`, off by default).

---

## 3. The fix, registered before writing it

1. **`Cargo.toml`**: add `avx512 = []` under `[features]`, default off, with
   a doc comment stating the exact opt-in requirement — a nightly (or a
   stable ≥ whatever release stabilizes `stdarch_x86_avx512` +
   `avx512_target_feature`, empirically ≤ 1.97.1 per §1) toolchain, built
   with `cargo build --release --features avx512`, on AVX-512F(+BF16)
   hardware (e.g. the original 9600X / Zen 5 box named in the module's own
   doc comment).
2. **`src/lib.rs`**: add `#![cfg_attr(feature = "avx512", feature(stdarch_x86_avx512, avx512_target_feature))]`
   near the crate root, guarded so it is a no-op (nothing emitted) when
   the `avx512` feature is off — the default build never asks the stable
   compiler to accept an unstable crate attribute. When the feature IS
   turned on under a toolchain that doesn't support `#![feature(...)]` at
   all (i.e. this machine's own stable 1.87 with `--features avx512`
   passed anyway), the build still correctly fails — that failure mode is
   *intended*: turning the feature on is a promise the caller is on a
   supporting toolchain, exactly like any other platform-specific SIMD
   crate feature in the ecosystem.
3. **`src/l1_hot_paths.rs`**: gate `find_attr_sym_avx512`'s definition and
   the dispatch block in `find_attr_sym` under
   `#[cfg(all(target_arch = "x86_64", feature = "avx512"))]` (currently
   only `#[cfg(target_arch = "x86_64")]`). The scalar fallback
   (`attrs.0.iter().position(...)`) is untouched and becomes the only
   compiled path when the feature is off.
4. **`src/l3_lqr.rs`**: three unsafe intrinsic-bodied functions
   (`mul_avx512`, `mul_bf16_inner`, `mul_bf16_pre_b_inner`) gain
   `#[cfg(all(target_arch = "x86_64", feature = "avx512"))]` (currently
   `#[cfg(target_arch = "x86_64")]` alone, or nothing). Their PUBLIC
   dispatcher callers (`mul`, `mul_bf16`, `mul_bf16_pre_b`) are **NOT**
   removed or feature-gated — they are called unconditionally elsewhere in
   the crate (`src/l3_kalman_nd.rs`, confirmed by grep: `mul_bf16`,
   `mul_bf16_pre_b`, `pack_for_bf16_b` all called outside any cfg guard).
   Each dispatcher's SIMD-taking branch is wrapped in
   `#[cfg(feature = "avx512")] { if <dims ok> && is_x86_feature_detected!(...) { return unsafe {...}; } }`,
   falling through to the existing scalar path
   (`self.mul_scalar`/`self.mul`) when the feature is off. `pack_for_bf16_b`,
   `Bf16PackedB`, `to_f64_mat`, `fp64_to_bf16`, `bf16_to_fp64` use no
   intrinsics (confirmed by reading each — pure bit manipulation) and are
   untouched.
5. **Runtime gate stays correct.** `is_x86_feature_detected!("avx512f"/"avx512bf16")`
   calls themselves are stable already on 1.87.0 (confirmed: none of the 29
   errors are attributed to any `is_x86_feature_detected!` call site) — only
   the intrinsic *functions* and the `#[target_feature]` *attribute* are
   gated. So the runtime probe is preserved verbatim; it is simply now
   nested inside a compile-time `#[cfg(feature = "avx512")]` block, meaning
   it only executes (and only can be true) in a build that opted in. No
   runtime check is left guarding code that cannot exist — the default
   build contains no AVX-512 codegen at all to guard.
6. **Tests.** `avx512_matches_scalar_across_dimensions` and
   `bf16_matmul_within_precision_tolerance` (`l3_lqr.rs`) currently skip on
   `!is_x86_feature_detected!(...)` alone; add `!cfg!(feature = "avx512")`
   to that skip condition so the skip message honestly says "AVX-512
   feature not enabled" rather than silently exercising a same-scalar
   comparison that always trivially passes (rel-err 0) once the SIMD
   branch is compiled out. `find_attr_sym`'s own three tests
   (`l1_hot_paths.rs`) call the trait method only — no direct reference to
   the `_avx512` fn — so they need no change; they are the correctness
   gate for prediction P2 below.

---

## 4. Predictions, registered before running the build

- **P1 (primary).** `cargo build --release` (default features, no
  `--features avx512`) succeeds with **zero errors** on this machine's
  `rustc 1.87.0`. Falsifiable: any remaining `E0658` or new error class
  would falsify this.
- **P2 (correctness).** `find_attr_sym`'s three existing tests
  (`find_attr_sym_empty`, `find_attr_sym_scalar_path`,
  `find_attr_sym_simd_path`) and `l3_lqr.rs`'s `mat_multiplication_identity_is_self`,
  `avx512_matches_scalar_across_dimensions`, `bf16_matmul_within_precision_tolerance`
  pass unchanged (the last two via the new explicit `cfg!(feature =
  "avx512")` skip, not via silent trivial pass) — scalar-path output is
  byte/bit-identical to before this change, since the scalar bodies are not
  touched at all, only reached unconditionally instead of conditionally.
- **P3 (suite-wide).** `cargo test` (debug profile, the project's own
  documented memory-safe default) runs to completion and the pass/fail set
  is either 100% green, or every red is independently traceable to a cause
  unrelated to this change (recorded honestly either way — this is a
  from-scratch first build on this machine, so there is no prior green
  baseline on THIS toolchain to diff against; "unrelated" will be argued
  per-failure from the failure's own content, e.g. a missing optional dep
  or an environment gap, not asserted by fiat).
- **P4 (feature gate honesty).** `cargo build --release --features avx512`
  on this machine's stable 1.87.0 (no nightly available) still fails to
  compile — but with a *different* error class than before (an unresolved
  `#![feature(...)]` / "attribute is only accepted on nightly" class of
  error, not `E0658` on individual intrinsics), demonstrating the gate is
  live and the feature genuinely still requires a supporting toolchain
  rather than silently doing nothing.

Results, the literal build/test transcripts, and GO/NO-GO go in
`AVX512_PORTABILITY_FIX_RESULTS.md`.
