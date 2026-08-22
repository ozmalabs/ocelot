//! `substrate_rs` — Rust runtime for the (G, Γ) substrate DSL.
//!
//! Drop-in replacement for the Python `substrate/` package (Paper I,
//! Axioms 1–3). Memory model is tuned for the substrate's actual workload:
//! mutation-heavy graph with small per-node out-degrees, deep Term trees
//! evaluated repeatedly, and a Γ that lives as a subgraph of G.
//!
//! Module map:
//! - [`sym`]  — string interner; every type / edge_type / attr key / var name
//!              is reduced to a `Sym(u32)` so hot-path comparisons are u32
//!              equality.
//! - [`value`] — tagged runtime Value enum (Int / Float / Bool / Str / None /
//!              NodeID / Tuple / Set / FrozenSet / Dict) returned from Term
//!              evaluation.
//! - [`graph`] — `TypedGraph`: arena-allocated nodes + edges, adjacency in
//!              SmallVec (cache-friendly), indexed by type and by
//!              (node, edge_type) for the O(|Γ|) admissibility bound the
//!              paper's Theorem XI requires.
//! - [`term`]  — Term arena + ~50 DSL variants + `evaluate`.
//! - [`grammar`] — NodePattern / Production (weighted by default per Paper §1)
//!              / Grammar with the (src_type, edge_type, tgt_type) index.
//! - [`checker`] — Consistency checker C; the only path through which a
//!              prospective edge is admitted.
//! - [`substrate`] — Π: the public mutation surface, plus Transaction.
//! - [`reflect`] — term ↔ G-subgraph round-trip (Axiom 3).
//! - [`persist`] — graph ↔ dict serialisation (Python-compatible wire format).
//! - [`jsonio`] — Term ↔ JSON (compat with `substrate/jsonio.py`).
//!
//! ## AVX-512 fast paths — opt-in only
//!
//! `l1_hot_paths.rs` (`find_attr_sym_avx512`) and `l3_lqr.rs` (`mul_avx512`,
//! `mul_bf16_inner`, `mul_bf16_pre_b_inner`) contain AVX-512 fast paths
//! gated behind the `avx512` Cargo feature (default OFF — see
//! `Cargo.toml`). The two unstable compiler features those paths need
//! (`stdarch_x86_avx512`, rust-lang/rust#111137; `avx512_target_feature`,
//! rust-lang/rust#44839) are opted into HERE, but only when the `avx512`
//! feature is enabled — so the default build never asks a stable
//! toolchain to accept an unstable crate attribute. Building with
//! `--features avx512` still requires a toolchain where both gates are
//! satisfied (nightly, or a stable release new enough to have stabilized
//! them — confirmed present by rustc 1.97.1, confirmed absent through
//! 1.87.0; see `AVX512_PORTABILITY_FIX_RESULTS.md`) — that is intentional,
//! matching how the rest of the ecosystem gates genuinely
//! platform-specific SIMD code.
#![cfg_attr(feature = "avx512", feature(stdarch_x86_avx512, avx512_target_feature))]

pub mod sym;
pub mod value;
pub mod graph;
/// Explicit native phase plans for the historically distinct tick paths.
pub mod cognitive_cycle;
/// Semantic areas plus dependency-derived scheduling components.
pub mod area_scheduler;
/// Pure native workers for graph-requested epoch-stamped cognitive tasks.
pub mod cognitive_tasks;
/// Native order-0 reflex scheduling with host effect boundaries.
pub mod reflex_runtime;
/// L1 foundation hot paths — hardware-accelerated typed iteration +
/// SIMD attr scan for the `typed_graph_arena_layout` composition
/// pattern. See module docs for L1 component correspondence.
pub mod l1_hot_paths;
/// L2 dispatch — work-stealing EDF scheduler with CPU pinning,
/// realising Jabberwock's L2 design layer (RT scheduling primitive
/// from Mt realtime_systems).
pub mod l2_dispatch;
/// L2 work-stealing scheduler — FIFO throughput-optimised alternative
/// to the single-Mutex EDF scheduler. Closes the bench-2 gap from
/// commit fe93761.
pub mod l2_dispatch_work_stealing;
/// Bounded code cache with LRU eviction + Arc-based safe concurrent
/// reclamation. Realises the implementable components of the
/// `executable_memory_lifecycle` Mt. Shared infrastructure for L2
/// dynamic dispatch + future L5 JIT integration.
pub mod code_cache;
/// L2 adaptive — wires Scheduler + CodeCache together with hot-counter
/// tracking, Γ-epoch invalidation, tier-up policy + cooling.
/// Realises the implementable components of the
/// `adaptive_tiered_dispatch` Mt.
pub mod l2_adaptive;
/// L2 ↔ Graph bridge — materialises DispatcherSnapshot into the
/// substrate's typed graph (Axiom 3 at the L2 layer; realises the
/// `second_order_scheduler_state_as_graph` Mt component).
pub mod l2_graph_bridge;
/// L2 ↔ JIT integration — end-to-end tests of the dispatch → TierUp →
/// JIT compile → install → Cached → call loop. x86_64 Linux only
/// (matches jit.rs's cfg gate).
#[cfg(all(target_arch = "x86_64", target_os = "linux"))]
mod l2_jit_integration;
/// L3 drives — PID + Kalman + multi-drive composition. Realises the
/// implementable subset of the `drives_estimation_control` Mt.
pub mod l3_drives;
/// L3 ↔ L2 bridge — gain scheduling driven by L2's per-kind hot
/// counters. Realises the `gain_scheduling_per_context` component
/// of the `drives_estimation_control` Mt + the L2↔L3 bridge.
pub mod l3_gain_scheduling;
/// L3 LQR — Linear Quadratic Regulator with iterative DARE solver.
/// Realises the `lqr_optimal_when_linear_quadratic` component of the
/// `drives_estimation_control` Mt.
pub mod l3_lqr;
/// L3 MPC — Model Predictive Control with box-constrained QP solver.
/// Realises the `mpc_constrained_lookahead` component of the
/// `drives_estimation_control` Mt.
pub mod l3_mpc;
/// L3 multi-dimensional Kalman filter — addresses Bench 3's
/// ≤64-dim prediction. The 1D KalmanFilter1D in l3_drives.rs
/// covers the scalar case.
pub mod l3_kalman_nd;
/// L6 essential variable monitoring — the four substrate-viability
/// variables + breach detection + degraded-mode response. Realises
/// the `essential_variables_with_viability_bounds` +
/// `viability_envelope_as_design_constraint` components of the
/// `universal_coordination` Mt.
pub mod l6_essential_variables;
/// L6 cybernetic feedback at system scale — channels that observe
/// essential variables + emit named recommendations for lower-layer
/// policy adjustments. Realises the
/// `cybernetic_feedback_at_system_scale` component of the
/// `universal_coordination` Mt; the L2↔L3 bridge (commit 148c339)
/// already closes one of the named cross-layer loops, this commit
/// closes the L6↔(L1, L2, L3) loops.
pub mod l6_cybernetic_feedback;
/// L6 Ashby variety check — counts regulator channels vs disturbance
/// sources at the substrate scale; verifies V(R) ≥ V(D).
pub mod l6_ashby_variety;
/// L4 subsystem boundary registry — the 7 meta-shape subsystems
/// + named bridges + enforce cross-subsystem calls.
pub mod l4_subsystem_boundaries;
/// Context-aware EFFORT DIAL — composes EDF deadlines + thread mode +
/// CPU/memory pressure + shape-salience surprise into one effort knob
/// (register_knob_u64) that scales order-N analysis passes + the
/// salience threshold. Real-time fits the deadline; offline goes deep.
pub mod effort_dial;
/// Full-stack integration tests — wire every layer's realised
/// pieces into a coherent substrate runtime + verify cross-layer
/// signals close their loops. x86_64 Linux only (matches jit.rs).
#[cfg(all(target_arch = "x86_64", target_os = "linux"))]
mod full_stack_integration;
pub mod term;
/// Native Enigma crib admissibility kernel used by graph-resident solver rules.
pub mod enigma;
/// `term_variants` — GENERATED variant table for `TermNode`
/// (`tools/gen_term_variants.py`). Backs the per-variant Term-evaluation
/// counter; `NUM_TERM_VARIANTS` is the enum's own arity.
pub mod term_variants;
/// `selector_audit` — the winner's-own-value instrument.
/// `ENGINE_ARGMAX_DETERMINISM_RESULTS.md` §6: a tie count is computed by the
/// selector under suspicion, so it cannot detect a selector disagreeing with its
/// own value Term. Records the winner's OWN value so that disagreement is a
/// LOCAL, SINGLE-ROW contradiction. Default OFF (VISION_PROTOCOL §9).
pub mod selector_audit;
pub mod argmin_tie;
/// `effect_audit` — the failed-effect instrument. `apply_rule_full` discarded
/// the result of `insert_edge`, so an insert that failed on a missing endpoint
/// was silent AND credited false progress to the fixpoint. Counting is
/// unconditional; the behavioural correction is opt-in and default OFF
/// (VISION_PROTOCOL §9).
pub mod effect_audit;
pub mod stage_a;
/// `scale_audit` — the three-way scale-wall decomposition instrument.
/// `VISION_VIDEO_PROBE_RESULTS.md` measured the wall (exponent 1.887, 164 h per
/// 1080p frame) and named it "PyO3 then O(N²)" — two causes, with a plausible
/// third. Counts F (FFI boundary) / C (genuine comparison) / R (redundant
/// recomputation) in LOAD-INDEPENDENT INTEGERS, because wall-clock on this
/// machine swings 1.66× on concurrent load alone (`ENGINE_WINNER_VALUE_RESULTS.md`).
/// Default OFF (VISION_PROTOCOL §9).
pub mod scale_audit;
/// `g5` — the RESPONSIVENESS gate: does a counter MOVE WITH the thing being
/// varied? The gate the A8 blindness (`VISION_VIDEO_PROBE_RERUN_RESULTS.md`
/// §3.1) needed and no existing gate supplied.
pub mod g5;
/// `ShapeDecode` — the dequantization primitive (beam-search shape
/// composer). Native twin of
/// `domains/reflective_faculty.py::compose_design_for_goal`. Kept out of
/// `term.rs`'s already-huge evaluator match arm body per the project's
/// "primitive in Rust, composition in graph" split.
pub mod shape_decode;
/// `motor_compose` — the embodied motor composer's search selection as one
/// pure native function (same split as `shape_decode`): the Term answers
/// membership; seed rules own when to compose and how to assemble.
pub mod motor_compose;
/// Modality-independent future-manifold projection over graph-resident
/// time-indexed shape slices. Domain-specific projectors may remain as
/// adapters, but the audit/gate contract lives here.
pub mod future_manifold;

/// `ProgEval` — the pure fueled interpreter over the Program IR
/// (PROGRAM_SYNTHESIS_PLAN.md §3.2). Module-per-engine precedent.
pub mod prog_eval;
/// `SynthEnumerate` — the bottom-up enumerative synthesizer (the
/// faithful Rust port of `domains/generator.py::synthesize`, unguided
/// path; PROGRAM_SYNTHESIS_PLAN.md §4-P4). Module-per-engine precedent.
pub mod synth_enumerate;
/// `space_quantize` — the N-dim, body-conditional, foveated dequantization
/// primitive over an observation belief (FLOOD_DESIGN.md Part A). Kept out
/// of `py.rs` for the same reason as `shape_decode`: the algorithm belongs
/// in a core module, not the PyO3 binding layer (`py.rs`'s `space_quantize`
/// method is a one-line handoff into this module — the fix for the
/// documented `slide_flood` binding-layer violation, not a repeat of it).
pub mod space_quantize;
/// `wave_stencil` — the engine's admissible vectorized application of a regular
/// local stencil (block 134000). For a KNOWN uniform radius-r cell rule, the
/// scale lever is EXACT VECTORIZATION of the rule the substrate already holds
/// (byte-identical), not a net — gated by Γ-admissibility (structural AST match
/// of the stencil), with the general per-cell path unchanged as the default.
pub mod wave_stencil;
/// `NetForward` — native forward pass of a graph-resident authored net
/// (the Rust twin of `code_writing_cortex.forward`), so a constructed
/// net can be evaluated inside a Rule at native speed (the reflex-net
/// "cheap default path").
pub mod net_forward;
/// `StrokeQuantize` — the handwriting instance of the same dequantization
/// primitive family: quantizes raw stroke GEOMETRY (arc-length-resampled
/// turn/length + pose) into a `ShapeSignature`-compatible relation-system
/// so `ShapeDecode`/`TransformDecode`/`DimInfer` apply unchanged to ink
/// (`HANDWRITING_DESIGN.md`). Kept out of `shape_decode.rs` (self-
/// contained module, additive-only edits) and out of `py.rs` (pure Term,
/// no PySubstrate method — rules/Python invoke it via `evaluate`).
pub mod strokes;
/// `SigmaLognormalGenerate` — Plamondon's Kinematic Theory (sigma-
/// lognormal): the CONTINUOUS motor-planning generator, contrast
/// `strokes`'s DISCRETIZED shape codebook. Self-contained, additive-only
/// module (see its own doc) — `strokes.rs`/`shape_decode.rs` untouched.
pub mod sigma_lognormal;
/// `SmoothDeformComponents` — RUN 44 PHASE 2's background-learned deformation metric: decomposes
/// `SmoothDeformDist`'s own FFD field into an affine part (rotation/shear/log-scale/translation)
/// and the non-affine bending residual. Self-contained, additive-only module (see its own doc)
/// — `term.rs`'s existing `smooth_deform_dist` is untouched.
pub mod deform_metric;
pub mod ink_topology;
pub mod shape;
pub mod grammar;
pub mod grammar_reflect;
pub mod checker;
pub mod substrate;
/// The engine's record of when it operated on ABSENCE — defaulted attribute
/// reads (H1) and absence-branch guard firings (H2). Write-only from the
/// evaluator; never read by a Term, so it cannot move a verdict (§9).
pub mod fallback_trace;
pub mod reflect;
pub mod persist;
pub mod jsonio;
pub mod ext;
pub mod rewrite;
pub mod graph_rules;
#[cfg(all(target_arch = "x86_64", target_os = "linux"))]
pub mod jit;
pub mod codec;
pub mod cabac;
pub mod h264_slice_header;
pub mod h264_dct;
/// Real-bitstream CABAC macroblock decoder for H.264 I-slices —
/// the agent's own decoder for arbitrary (x264/ffmpeg) macroblocks:
/// full I-slice mb_type tree + residual syntax + decoder-side intra
/// prediction + DC Hadamard transforms -> real pixels.
pub mod h264_cabac_mb;
/// In-loop deblocking filter (ITU-T H.264 §8.7) for the agent's own
/// I-slice decoder — luma + chroma boundary-strength + edge filters.
pub mod h264_deblock;
/// Vendored from OxideAV/oxideav-h264 (MIT) — sub-pel interpolation
/// + weighted-pred. See the file header and NOTICES.md.
pub mod h264_inter_pred;
/// H.265 intra-prediction mode remap — first primitive of the
/// H.264→H.265 transcoder. Implements stage 2 (intra_prediction_mode)
/// per the substrate-grounded design from commit 486f65e.
pub mod h265_intra_mode;
/// H.265 slice-segment header emitter — stage 6 (structure) of the
/// H.264→H.265 transcoder. Scalar bit-writer; substrate-named
/// negligible bottleneck.
pub mod h265_slice_header;
/// H.265 forward integer DCT — stage 3 (transform_kind) of the
/// H.264→H.265 transcoder. 4×4 and 8×8 forward DCT-II per
/// clause 8.6.4.2; substrate-named compute_bound.
pub mod h265_dct;
/// H.265 CTU quadtree — stage 1 (block_structure) of the
/// H.264→H.265 transcoder. MB → CTU rewrite with same-mode merge.
pub mod h265_ctu_quadtree;
/// H.265 in-loop filter — stage 5 (in_loop_filter) of the
/// H.264→H.265 transcoder. Deblocking + SAO.
pub mod h265_in_loop_filter;
/// H.265 CABAC encoder — stage 4 (cabac_mechanism) of the
/// H.264→H.265 transcoder. Binary arithmetic coder per clause 9.3.4.
pub mod h265_cabac;
/// H.264 → H.265 transcode driver. Composes the 6 stages into an
/// end-to-end pipeline. Each MB descriptor flows through stages 1-6
/// in the substrate-grounded order.
pub mod h265_transcode_driver;
/// H.264 macroblock iterator. Walks the entropy-coded MB data inside
/// an H.264 slice + produces `H264MbDescriptor` records the transcode
/// driver consumes. Closes the input-side gap named at end of df75e14.
pub mod h264_mb_iterator;
pub mod cochlear_nucleus;
pub mod inferior_colliculus;
pub mod auditory_cortex;
pub mod audio_primitives;
pub mod apc;
pub mod pipeline_runtime;
pub mod memory;
pub mod can_ops;
#[cfg(feature = "gpu_me")]
pub mod gpu_me;
/// Shared-memory framebuffer vision primitive — a POSIX-shm reader
/// (seqlock discipline) + downsample/quantize, feeding the SAME
/// segmentation + cross-frame identity machinery `segment` uses. The
/// writer side (a browser CDP-screencast thread) is out of scope here;
/// this is the Rust-runtime reader half of the "live vision on shared
/// memory" design (CLAUDE.md).
pub mod framebuffer;
/// Pure-Rust vision primitives (convolve / temporal_diff / foveate)
/// backing the `ChangeDetect` / `TemporalDiff` / `Foveate` DSL Terms.
/// Pure numeric — no graph state; the Terms compose them with `Attr`.
pub mod vision_primitives;
/// Tool-dispatch boundary — the global Python-handler registry + the
/// `call_tool` dispatcher the `UseTool` evaluator arm calls. Kept out of
/// py.rs (concurrently edited) and wired into `_native` here.
pub mod tools;

mod py;

use pyo3::prelude::*;

/// Top-level PyO3 module. The Python wrapper at
/// `python/substrate_rs/__init__.py` re-exports the symbols as `Filter`,
/// `Lit`, `Substrate`, etc. so callers can `from substrate_rs import Filter`
/// exactly as they do for the Python `substrate` package.
#[pymodule]
fn _native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    py::register(m)?;
    tools::register_tools(m)
}
