//! Memory faculty — the agent's MEMORY management, IN RUST.
//!
//! CLAUDE.md: "the agent is a graph running in Rust; Python is only the
//! world adapter." Memory management is a core agent function, so the
//! KEEP/FORGET/INDEX DECISION lives here, not in Python. The prior agent
//! authored the design in Python (`domains/memory_shape_faculty.py`,
//! `memory_self_management.py`, `long_term_memory.py`) as the SPEC; this
//! module ports the DECISION into Rust and COMPOSES the substrate's
//! existing storage-tier machinery rather than reinventing it.
//!
//! ## What this REUSES (the existing tier machinery — composition, not reinvention)
//!
//! - **`code_cache::CodeCache` semantics** — the bounded-by-BYTES LRU
//!   cache with per-entry `code_size_bytes` eviction is the WORKING-memory
//!   tier mechanism. We reuse its *pattern* (per-entry byte accounting +
//!   eviction-until-fits + Arc-deferred-free) but the eviction PRIORITY is
//!   keep_value-per-byte ascending instead of plain recency — see
//!   `forget_over_budget`. The byte-bound + eviction-loop shape is taken
//!   directly from `CodeCache::insert`.
//! - **`l2_adaptive::HotCounter`** — the per-kind access/firing counter is
//!   the hot/cold tracking for cluster prefetch + recency. We reuse it
//!   verbatim (`record` on cluster access, `count` for last-access) as the
//!   `adaptive_tiered_dispatch` Mt's hot tier. No re-implementation.
//! - **`persist::{graph_to_value, ...}`** — the durable disk tier. The
//!   long-term per-cluster page-out reuses the substrate's existing
//!   "mind is durable JSON" encoder (`encode_value`) so a paged-out
//!   cluster round-trips through the SAME wire format as a full save.
//! - **`l4_subsystem_boundaries::MetaShape::DelayedPersistence`** — the
//!   named subsystem (#449, "consolidation + replay") this faculty
//!   registers under. `register_subsystem` wires it in.
//!
//! ## What this NEWLY WRITES (the agent's DECISION — could not be reused)
//!
//! - **`keep_value`** — the agent's keep utility. salience(growth_shape)
//!   (= VARIANCE = MDL/surprise, the compression selector) + the order_n
//!   SATURATION read (order-1 finite-difference over the growth history,
//!   decelerating == condensing == keep) × miss_penalty × non_rebuildability.
//!   The Python `generator_salience.salience` is variance; `order_n_concepts.
//!   nth_order_terms` is finite-difference. There is no existing Rust home
//!   for these *as a memory decision*, so they are written here (variance +
//!   finite-difference, a dozen lines each — donkey-clean, no ML).
//! - **byte estimator** (`node_bytes` / `type_bytes`) — walks node attrs to
//!   estimate the real serialized footprint. The bug that broke the prior
//!   run was bounding by COUNT while AudioBuffer holds raw sample tuples
//!   (hundreds of KB/node). No existing Rust byte-estimator over node
//!   attrs, so written here (mirrors the Python `_attr_bytes`).
//! - **the order-N SHAPE index** (`shape_key` + `ShapeIndex`) — the index
//!   is a RULE bounded by #clusters, NOT a per-item map. Each cluster keyed
//!   by its relational-SHAPE ordinal-rank (the `relational_shape.rank` op:
//!   rank(i) = #bands strictly below band i — invariant to talker gain).
//!   Storage == retrieval key. Written here (rank + L1 descent).
//!
//! The TIERS themselves are the existing mechanisms; only the DECISION on
//! top of them is new.

use std::collections::{HashMap, HashSet, VecDeque};

use crate::graph::NodeID;
use crate::l2_adaptive::HotCounter;
use crate::l4_subsystem_boundaries::{MetaShape, SubsystemRegistry};
use crate::substrate::Substrate;
use crate::sym::Sym;
use crate::value::Value;

// =======================================================================
// Role tags — the resistor-drawer multipliers the keep_value utility reads.
// NOT a keep/forget decision: a per-type declaration of (miss_penalty,
// non_rebuildability). The DECISION is keep_value's. Ported from
// memory_self_management.ROLE.
//   miss_penalty       = latency-at-need (hot lexicon hit every step).
//   non_rebuildability = 1 - reacquirable-from-the-world (firehose is
//                        fully re-derivable from the source video -> ~0).
// =======================================================================

/// (miss_penalty, non_rebuildability, never_forget) for a node type.
fn role_for(t: &str) -> (f64, f64, bool) {
    match t {
        // learned store: high miss-penalty + not rebuildable -> keep.
        "AcousticLexicon" => (5.0, 1.0, true),
        "AcousticSign" => (5.0, 1.0, true),
        "Concept" => (4.0, 1.0, true),
        "Microtheory" => (4.0, 1.0, true),
        "Referent" => (3.0, 1.0, true),
        "VisualType" => (3.0, 1.0, true),
        "MemorySummary" => (2.0, 1.0, true),
        "Media" => (2.0, 1.0, true),
        "Series" => (2.0, 1.0, true),
        "Movie" => (2.0, 1.0, true),
        "JellyfinLibrary" => (2.0, 1.0, true),
        "MemoryRecord" => (3.0, 1.0, true),
        // the per-input firehose + per-chunk parse SCAFFOLDING: low miss-penalty
        // (not needed after the feature is read) + fully rebuildable from the
        // source -> disposable (the ring bounds them continuously, not just under
        // budget pressure). Utterance is consumed to make the AcousticSign (the
        // kept learning); the container/stream are re-opened per chunk.
        "AudioBuffer" => (1.0, 0.02, false),
        "AudioFrame" => (1.0, 0.05, false),
        "OpusPacketInfo" => (1.0, 0.05, false),
        "Frame" => (1.0, 0.05, false),
        "Utterance" => (1.0, 0.05, false),
        "AudioContainer" => (1.0, 0.05, false),
        "AudioStream" => (1.0, 0.05, false),
        // VISION sensory scratch: the downscaled per-frame percept, the V1 edge
        // maps it produces, and the per-frame edge-energy gist — iconic memory,
        // rebuildable by re-decoding the frame -> disposable (the ring bounds the
        // full-frame-rate firehose). The kept visual signal is the cross-modal
        // binding (consolidated) + (future) a visual lexicon.
        "Image" => (1.0, 0.05, false),
        "VisualScene" => (1.0, 0.05, false),
        _ => (1.0, 0.3, false),
    }
}

/// The memory TIER a node type lives in — the human sensory-register insight
/// (user, 2026-06-15: "a very low cost, low lifetime node ... would only ever
/// be in disposable cache"). Derived from the EXISTING role multipliers, not a
/// new hand-authored table:
///   "keep"       — never_forget: the learned store (lexicon / concepts);
///                  consolidated to long-term.
///   "working"    — bounded RAM; shed by keep_value-per-byte under budget
///                  (forget_over_budget).
///   "disposable" — the raw per-input perceptual FIREHOSE: very low
///                  miss-penalty AND almost fully rebuildable from the source
///                  (mp <= 1.0 && nr <= 0.1). This is the agent's echoic/iconic
///                  memory: read the feature, then GONE — never consolidated,
///                  dropped EAGERLY every tick rather than accumulated and
///                  bounded after the fact. (AudioBuffer / AudioFrame /
///                  OpusPacketInfo / Frame all land here.)
pub fn tier_for(t: &str) -> &'static str {
    let (mp, nr, never) = role_for(t);
    if never {
        return "keep";
    }
    if mp <= 1.0 && nr <= 0.1 {
        return "disposable";
    }
    "working"
}

// =======================================================================
// BYTE ESTIMATOR — newly written (no existing Rust byte-estimator over
// node attrs). Mirrors memory_shape_faculty._attr_bytes / node_bytes.
// This is the fix for the count-vs-bytes bug: AudioBuffer raw-sample
// tuples dominate the real footprint and must be measured by bytes.
// =======================================================================

fn attr_bytes(v: &Value) -> usize {
    match v {
        Value::Tuple(items) | Value::List(items) => 8 * items.len() + 8, // raw sample tuples dominate
        Value::Set(items) | Value::FrozenSet(items) => 8 * items.len() + 8,
        Value::Str(_) => 16, // interned; resolve len would need the interner
        Value::Bool(_) => 1,
        Value::Int(_) | Value::Float(_) => 8,
        Value::Rational(_, _) => 16, // two i64s
        Value::Node(_) => 8,
        Value::Dict(pairs) => {
            pairs.iter().map(|(_, v)| attr_bytes(v)).sum::<usize>() + 16 * pairs.len()
        }
        Value::Surface(_, bytes) => bytes.len() + 8,
        Value::None => 8,
    }
}

fn str_attr_bytes(v: &Value, s: &Substrate) -> usize {
    match v {
        Value::Str(sym) => s.interner.resolve(*sym).len() + 8,
        other => attr_bytes(other),
    }
}

/// Bytes held by one node (attrs + node overhead). Walks attrs so the
/// real serialized footprint is measured, not the count.
pub fn node_bytes(s: &Substrate, nid: NodeID) -> usize {
    if !s.graph.has_node(nid) {
        return 0;
    }
    let n = s.graph.node(nid);
    n.attrs
        .values()
        .map(|v| str_attr_bytes(v, s))
        .sum::<usize>()
        + 32
}

/// Estimated total bytes for all nodes of a type. Samples up to `sample`
/// nodes for the per-node mean and scales (matches the Python sampler so
/// the bound enforced is the same quantity).
pub fn type_bytes(s: &Substrate, type_sym: Sym, sample: usize) -> usize {
    let ids = s.graph.nodes_of_type(type_sym);
    let n = ids.len();
    if n == 0 {
        return 0;
    }
    let take = ids.len().min(sample);
    let mean: f64 = ids
        .iter()
        .take(take)
        .map(|&id| node_bytes(s, id) as f64)
        .sum::<f64>()
        / take as f64;
    (mean * n as f64) as usize
}

/// Total estimated bytes across all node types present.
pub fn total_bytes(s: &Substrate) -> usize {
    let mut by_type: HashMap<Sym, ()> = HashMap::new();
    for (_, nd) in s.graph.iter_nodes() {
        by_type.entry(nd.type_).or_insert(());
    }
    by_type.keys().map(|&t| type_bytes(s, t, 64)).sum()
}

// =======================================================================
// THE DECISION — newly written. salience = variance (the compression/MDL
// selector); saturation = order-1 finite-difference (the order_n operator).
// =======================================================================

/// salience(growth_shape) = VARIANCE of the per-round growth history.
/// A flat firehose grows ~constant -> ~0 variance -> low salience -> forget.
/// A condensing lexicon's growth varies -> high salience -> keep.
/// This is `generator_salience.salience` (output variance = surprise = bits).
/// NOTE: keep_value now uses `order_n_shape_salience` (the general operator,
/// which reads variance as its MAGNITUDE term); this bare-variance helper is
/// retained as the primitive the magnitude term derives from and is exercised
/// by the unit tests.
#[allow(dead_code)]
fn salience(history: &[i64]) -> f64 {
    let n = history.len();
    if n == 0 {
        return 0.0;
    }
    let mean: f64 = history.iter().map(|&h| h as f64).sum::<f64>() / n as f64;
    history
        .iter()
        .map(|&h| (h as f64 - mean).powi(2))
        .sum::<f64>()
        / n as f64
}

/// The order-1 finite-difference (velocity) of the growth history — the
/// agent's order_n operator (`order_n_concepts.nth_order_terms` order 1).
fn order1_velocities(history: &[i64]) -> Vec<f64> {
    if history.len() < 2 {
        return Vec::new();
    }
    (1..history.len())
        .map(|i| (history[i] - history[i - 1]) as f64)
        .collect()
}

/// SATURATION: is per-round growth DECELERATING? The order_n read of a
/// condensing store — later additions are smaller than earlier ones
/// (|last velocity| < |first velocity|). Replaces the hand-rolled ratio.
pub fn is_saturating(history: &[i64]) -> bool {
    let v = order1_velocities(history);
    if v.is_empty() {
        return false;
    }
    // Compare the RECENT velocity to the MEDIAN, not the FIRST. Comparing to the
    // first wrongly flags a steady firehose as "condensing" whenever the first
    // observation was a one-off spike (e.g. the catalog-ingest batch) — which
    // then protects that firehose from forget_over_budget and it grows unbounded.
    // A genuinely condensing store has its latest additions well below typical.
    let mut mags: Vec<f64> = v.iter().map(|x| x.abs() as f64).collect();
    mags.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    let median = mags[mags.len() / 2];
    let last = v.last().unwrap().abs() as f64;
    last < 0.5 * median
}

// =======================================================================
// ORDER-N SHAPE SALIENCE — the GENERAL operator (newly written, native).
//
// THE ONE OPERATOR for the salience of ANY trajectory's order-N SHAPE,
// whether the trajectory is a memory type's per-round GROWTH shape, an
// audio PITCH/RHYTHM contour, or a video MOTION path. The insight
// (validated on the StoryBots "tada"): salience lives in the order-N
// SHAPE — a DIRECTED, RESOLVING shape (pitch rising + beats tightening ->
// a peak = tension->release) is salient; a FLAT or RANDOM trajectory is
// not. This composes the agent's two HELD operators:
//
//   * order_n  (order_n_concepts.nth_order_terms) — the order-1 velocity
//     (direction) and order-2 curvature (the bend toward the peak) of the
//     trajectory, as finite differences. Already native here
//     (order1_velocities); order2 is the difference of that.
//   * relational_shape (relational_shape.rank / shape_key) — the
//     ordinal-rank read that makes the measure invariant-by-construction
//     to any positive-gain/level rescaling of the carrier (a louder tada
//     or a higher-voiced one is the SAME shape). Used for the resolution
//     term: WHERE in the trajectory's rank order does it end up / peak.
//
// A directed-resolving shape scores HIGH; flat/random scores LOW, via
// three native, donkey-clean terms (no ML, no weights fitted):
//
//   directedness  = |net order-1 drift| / total |order-1| movement.
//                   A monotone build = 1 (every step the same way); a
//                   random walk -> ~0 (steps cancel); flat -> 0.
//   resolution    = how distinctive the ENDPOINT/extreme is in the
//                   trajectory's own ORDINAL rank (relational_shape):
//                   ends at (or passes through) its rank-extreme = a peak
//                   reached = 1; ends mid-pack = ~0. Gain-invariant.
//   curvature_cue = does order-2 BEND consistently toward the resolution
//                   (a build that tightens into the peak, not a straight
//                   ramp that overshoots)? mean sign-agreement of order-2
//                   with the drift direction's deceleration near the end.
//
// salience = magnitude * directedness * (resolution + curvature_cue),
// where magnitude = sqrt(variance) so a flat (zero-variance) trajectory
// is zero regardless of the shape terms. Random has magnitude but
// directedness ~ 0 -> low. Directed-resolving has all three -> high.
// =======================================================================

/// order-2 finite difference (curvature/acceleration) of a trajectory —
/// the agent's order_n operator at order 2 (difference of the order-1
/// velocities). order-1 = direction, order-2 = how the direction bends.
fn order2_curvatures(traj: &[f64]) -> Vec<f64> {
    let v: Vec<f64> = (1..traj.len()).map(|i| traj[i] - traj[i - 1]).collect();
    if v.len() < 2 {
        return Vec::new();
    }
    (1..v.len()).map(|i| v[i] - v[i - 1]).collect()
}

/// ordinal rank of a value within the trajectory = #points strictly below
/// it (the relational_shape.rank op). Gain/level-invariant by construction.
fn ordinal_rank(traj: &[f64], idx: usize) -> usize {
    traj.iter().filter(|&&x| x < traj[idx]).count()
}

/// THE GENERAL OPERATOR. salience of a trajectory's order-N SHAPE: high
/// for a DIRECTED, RESOLVING build-up->peak (the tada), low for flat or
/// random. General over growth / pitch / rhythm / motion trajectories.
/// Composes order_n (velocity + curvature) with relational_shape (ordinal
/// rank of the resolution). Native, no ML.
pub fn order_n_shape_salience(traj: &[f64]) -> f64 {
    let n = traj.len();
    if n < 3 {
        return 0.0;
    }
    // magnitude: sqrt-variance. A flat trajectory has zero -> zero salience
    // no matter how the (degenerate) shape terms read.
    let mean: f64 = traj.iter().sum::<f64>() / n as f64;
    let var: f64 = traj.iter().map(|&x| (x - mean).powi(2)).sum::<f64>() / n as f64;
    let magnitude = var.sqrt();
    if magnitude < 1e-9 {
        return 0.0;
    }

    // order-1 (direction/velocity): net drift vs total movement.
    let vel: Vec<f64> = (1..n).map(|i| traj[i] - traj[i - 1]).collect();
    let net_drift: f64 = vel.iter().sum::<f64>().abs();
    let total_move: f64 = vel.iter().map(|d| d.abs()).sum::<f64>();
    // directedness in [0,1]: 1 = monotone (every step same way), ~0 =
    // random walk (steps cancel) or flat. This is what separates a
    // DIRECTED build from a random wander of the same magnitude.
    let directedness = if total_move > 1e-12 {
        net_drift / total_move
    } else {
        0.0
    };

    // resolution (relational_shape): does the trajectory BUILD to and
    // RESOLVE at an extreme? Measure how distinctive the peak-of-the-drift
    // end region is in the trajectory's own ORDINAL rank. A rising build
    // ends near its max rank; a falling one near its min. Normalise so
    // reaching the extreme -> 1, ending mid-pack -> ~0. Gain-invariant.
    let rising = traj[n - 1] >= traj[0];
    // the resolution point = the global extreme in the drift direction.
    let res_idx = if rising {
        (0..n)
            .max_by(|&a, &b| traj[a].partial_cmp(&traj[b]).unwrap())
            .unwrap()
    } else {
        (0..n)
            .min_by(|&a, &b| traj[a].partial_cmp(&traj[b]).unwrap())
            .unwrap()
    };
    let rank = ordinal_rank(traj, res_idx) as f64; // 0..=n-1
    let res_rank = if rising { rank } else { (n - 1) as f64 - rank };
    // resolution also requires the peak to be LATE (a build->peak, not a
    // peak->decay): position of the extreme in the trajectory.
    let lateness = res_idx as f64 / (n - 1) as f64;
    let resolution = (res_rank / (n - 1) as f64) * (if rising { lateness } else { lateness });

    // curvature cue (order-2): near the resolution, does the velocity
    // DECELERATE (settle into the peak) rather than overshoot? A tada
    // tightens into its peak. mean order-2 sign opposing the drift over
    // the approach = a settling build. Bounded to [0,1].
    let curv = order2_curvatures(traj);
    let curvature_cue = if curv.is_empty() {
        0.0
    } else {
        let drift_sign = if rising { 1.0 } else { -1.0 };
        // a decelerating approach has order-2 opposite the drift sign.
        let agree =
            curv.iter().filter(|&&c| c * drift_sign < 0.0).count() as f64 / curv.len() as f64;
        agree // in [0,1]
    };

    magnitude * directedness * (resolution + curvature_cue)
}

/// keep_value = (salience + saturation_floor) × miss_penalty × non_rebuildability.
/// Size-INDEPENDENT: depends on the growth SHAPE + role, never on
/// fraction-of-peak (the bug). Ported from memory_shape_faculty.keep_value.
///
/// THE FOLD: the salience term is now `order_n_shape_salience` over the
/// growth-shape history — the SAME operator perceptual salience uses
/// (audio pitch/rhythm, video motion). A condensing store's growth shape
/// is a DIRECTED, RESOLVING build (big early additions decelerating to a
/// settle = the tada shape) -> salient -> keep. A flat firehose has no
/// directed-resolving shape -> low -> forget. One salience operator for
/// both memory tiering AND perception.
pub fn keep_value(history: &[i64], miss_penalty: f64, non_rebuildability: f64) -> f64 {
    if history.is_empty() {
        return 0.0;
    }
    let traj: Vec<f64> = history.iter().map(|&h| h as f64).collect();
    let sal = order_n_shape_salience(&traj);
    // a saturating type is structure that compresses -> floor its keep_value
    // so a momentary flat window cannot outvote the order_n saturation read.
    let sat = if is_saturating(history) { 1.0 } else { 0.0 };
    (sal + sat) * miss_penalty.max(1e-6) * non_rebuildability.max(1e-6)
}

// =======================================================================
// THE ORDER-N SHAPE INDEX — newly written. The index is a RULE bounded by
// #clusters, NOT a per-item map. Each cluster keyed by its relational-SHAPE
// ordinal-rank. STORAGE == RETRIEVAL KEY.
// =======================================================================

/// rank-shape key of a feature vector: rank(i) = #entries strictly below
/// entry i. The `relational_shape.rank` op — invariant to any
/// order-preserving (positive-gain) talker/scale transform by construction.
pub fn shape_key(vec: &[f64]) -> Vec<i64> {
    let n = vec.len();
    if n < 2 {
        return vec.iter().map(|&x| x as i64).collect();
    }
    (0..n)
        .map(|i| (0..n).filter(|&j| j != i && vec[i] > vec[j]).count() as i64)
        .collect()
}

/// L1 distance between two relational-shape (ordinal-rank) signatures.
/// This IS the shape-neighbour metric: two trajectories with the same
/// order-N relational SHAPE (an accelerando-crescendo -> climax) have the
/// same rank arrangement regardless of timbre / level, so their shape_key
/// signatures are close. Different lengths are incomparable (i64::MAX).
pub fn shape_distance(a: &[i64], b: &[i64]) -> i64 {
    if a.len() != b.len() {
        return i64::MAX;
    }
    a.iter().zip(b).map(|(x, y)| (x - y).abs()).sum()
}

/// The shape SIGNATURE of a trajectory = its relational-shape ordinal-rank
/// key (`shape_key`). Gain/level-invariant by construction, so two clips
/// that share the order-N SHAPE but differ in every surface way (timbre,
/// instrument, loudness) get NEIGHBOURING signatures. The world adapter
/// extracts the pitch/rhythm trajectory; the signature is computed here.
pub fn shape_signature(traj: &[f64]) -> Vec<i64> {
    shape_key(traj)
}

/// The shape-neighbour THRESHOLD for a signature of length `n`, derived
/// from the shape SCALE — NOT tuned to an answer. The rank of each point
/// ranges over 0..=n-1, so the maximum possible L1 distance between two
/// length-n rank signatures is on the order of n*(n-1)/2 (a full reversal).
/// A shape-NEIGHBOUR is one whose ranks agree to within a small fraction of
/// that scale: we admit signatures whose mean per-point rank disagreement is
/// below 1 rank position, i.e. total L1 < n. This is the "same arrangement,
/// minor local jitter" band, set from n, not fit to the tada/Grieg pair.
pub fn shape_neighbour_threshold(n: usize) -> i64 {
    n as i64
}

// --- PER-RELATION METRICS (affect: normalized L2; function: categorical) ----
//
// The ordinal-rank `shape_distance` above is the RIGHT metric for a
// TRAJECTORY (a shape — accelerando-crescendo), but WRONG for a heterogeneous
// feature vector (affect) or a category (function). Each relation needs the
// metric appropriate to what its signature MEANS:
//   - AFFECT  = a point in a continuous, heterogeneous-unit feature space
//     (onset-rate ~0.4 vs pitch ~100s Hz vs centroid ~1000s Hz). Ordinal rank
//     collapses the magnitudes; raw L2 is dominated by the big-unit features.
//     The right metric: PER-FEATURE NORMALIZE across the clip population, then
//     L2. Neighbours = close in normalised arousal/valence space.
//   - FUNCTION = a small CATEGORY (bucketed role flags), not a trajectory. The
//     right metric: CATEGORICAL match (Hamming distance on the bucket vector).
//     Neighbours = SAME structural role.

/// Fixed-point scale for the z-score normalised affect space. A signature
/// stored as `Vec<i64>` cannot hold floats, so the per-feature z-scores are
/// carried as milli-z (z * 1000). 1.0 std == 1000 units. This keeps the whole
/// pipeline integer (signatures, distances, thresholds) with no float attrs.
pub const Z_SCALE: f64 = 1000.0;

/// PER-FEATURE z-score normalisation of a population of affect vectors,
/// returned as fixed-point milli-z integers (`z * Z_SCALE`). Each column
/// (feature) is centred on its population mean and scaled by its population
/// std, so heterogeneous units (onset-rate vs Hz) become comparable and no
/// single big-magnitude feature dominates the L2. A feature with zero
/// population variance contributes 0 (it carries no discriminative signal).
///
/// This is the population normaliser the affect metric needs: the world
/// adapter hands the RAW heterogeneous vectors; normalisation happens HERE,
/// in the core, over the exact clip set being linked. Mechanical (mean/std),
/// no ML / fit / sweep.
pub fn affect_normalize(vectors: &[Vec<f64>]) -> Vec<Vec<i64>> {
    if vectors.is_empty() {
        return Vec::new();
    }
    let n_feat = vectors[0].len();
    let n = vectors.len() as f64;
    let mut means = vec![0.0_f64; n_feat];
    for v in vectors {
        for (k, &x) in v.iter().enumerate() {
            means[k] += x;
        }
    }
    for m in means.iter_mut() {
        *m /= n;
    }
    let mut stds = vec![0.0_f64; n_feat];
    for v in vectors {
        for (k, &x) in v.iter().enumerate() {
            let d = x - means[k];
            stds[k] += d * d;
        }
    }
    for s in stds.iter_mut() {
        *s = (*s / n).sqrt();
    }
    vectors
        .iter()
        .map(|v| {
            v.iter()
                .enumerate()
                .map(|(k, &x)| {
                    if stds[k] <= 1e-12 {
                        0
                    } else {
                        (((x - means[k]) / stds[k]) * Z_SCALE).round() as i64
                    }
                })
                .collect()
        })
        .collect()
}

/// L2 distance (Euclidean) between two normalised affect signatures, in the
/// fixed-point milli-z space. Returns the rounded integer distance. Different
/// lengths are incomparable (`i64::MAX`).
pub fn l2_distance(a: &[i64], b: &[i64]) -> i64 {
    if a.len() != b.len() {
        return i64::MAX;
    }
    let ss: f64 = a
        .iter()
        .zip(b)
        .map(|(&x, &y)| {
            let d = (x - y) as f64;
            d * d
        })
        .sum();
    ss.sqrt().round() as i64
}

/// The affect-neighbour THRESHOLD in the normalised (milli-z) space — derived
/// from the z-space SCALE, NOT tuned to an answer. Two clips are affect-
/// neighbours when they sit within ~1 std of each other PER FEATURE on
/// average. In milli-z, 1 std == Z_SCALE; an average per-feature gap of 1 std
/// over `n` features gives an L2 of `sqrt(n) * Z_SCALE`. This is the
/// "same region of arousal/valence space" band, set from the scale.
pub fn affect_neighbour_threshold(n: usize) -> i64 {
    ((n as f64).sqrt() * Z_SCALE).round() as i64
}

/// CATEGORICAL distance between two role/bucket signatures = HAMMING distance
/// (count of positions that differ). For a function relation the signature is
/// a small set of bucketed flags (is_rising, salience_bucket, span_bucket,
/// peak_late), not a trajectory — so "same role" means the bucket vectors
/// match. Different lengths are incomparable (`i64::MAX`).
pub fn categorical_distance(a: &[i64], b: &[i64]) -> i64 {
    if a.len() != b.len() {
        return i64::MAX;
    }
    a.iter().zip(b).filter(|(x, y)| x != y).count() as i64
}

/// The function-neighbour THRESHOLD for a categorical role vector: link when
/// the role CATEGORY matches to within ONE differing bucket (Hamming <= 1),
/// i.e. distance < 2. Same structural role, allowing a single bucket to slip
/// at a boundary. NOT tuned — it is the categorical-match rule (exact-or-one).
pub fn categorical_neighbour_threshold(_n: usize) -> i64 {
    2
}

/// One cluster (drawer) in the shape index: its category + leaf shape keys
/// plus the disk paths of its records. The index footprint == #clusters.
#[derive(Clone, Debug)]
pub struct ClusterEntry {
    pub cluster_id: String,
    pub cat_key: Vec<i64>,
    pub leaf_key: Vec<i64>,
    /// record key -> on-disk path.
    pub paths: HashMap<String, String>,
    /// record key -> resident NodeID (when paged in).
    pub node_ids: HashMap<String, NodeID>,
    pub resident: bool,
    pub last_round: i64,
}

/// The order-N shape hierarchy over clusters. `descent` is the order-N
/// retrieval: tier-1 match the CATEGORY shape, tier-2 match the LEAF shape.
#[derive(Default)]
pub struct ShapeIndex {
    pub clusters: HashMap<String, ClusterEntry>,
}

impl ShapeIndex {
    pub fn new() -> Self {
        Self {
            clusters: HashMap::new(),
        }
    }

    /// The drawer id a record belongs to = its coarse category SHAPE key.
    /// Records sharing a category arrangement share a cluster -> cluster
    /// count is bounded by #distinct category shapes, not #items.
    pub fn cluster_id(cat_vec: &[f64]) -> String {
        let key = shape_key(cat_vec);
        let parts: Vec<String> = key.iter().map(|x| x.to_string()).collect();
        format!("cat:{}", parts.join(","))
    }

    /// Index a record into its cluster (creating the cluster on first use).
    pub fn put(
        &mut self,
        key: &str,
        cat_vec: &[f64],
        leaf_vec: &[f64],
        path: &str,
        round: i64,
        resident: Option<NodeID>,
    ) -> String {
        let cid = Self::cluster_id(cat_vec);
        let cat_key = shape_key(cat_vec);
        let leaf_key = shape_key(leaf_vec);
        let cl = self
            .clusters
            .entry(cid.clone())
            .or_insert_with(|| ClusterEntry {
                cluster_id: cid.clone(),
                cat_key: cat_key.clone(),
                leaf_key: leaf_key.clone(),
                paths: HashMap::new(),
                node_ids: HashMap::new(),
                resident: false,
                last_round: round,
            });
        cl.paths.insert(key.to_string(), path.to_string());
        cl.last_round = cl.last_round.max(round);
        // keep the cluster's leaf key as the most-recent member's shape.
        cl.leaf_key = leaf_key;
        if let Some(nid) = resident {
            cl.node_ids.insert(key.to_string(), nid);
            cl.resident = true;
        }
        cid
    }

    /// Remove a key from all shape clusters. Used when disk recovery detects
    /// an ambiguous duplicate key and must refuse arbitrary recall.
    pub fn remove_key(&mut self, key: &str) {
        let mut empty = Vec::new();
        for (cid, cluster) in self.clusters.iter_mut() {
            cluster.paths.remove(key);
            cluster.node_ids.remove(key);
            if cluster.paths.is_empty() {
                empty.push(cid.clone());
            }
        }
        for cid in empty {
            self.clusters.remove(&cid);
        }
    }

    /// The order-N shape descent: tier-1 match the CATEGORY shape, then
    /// within the nearest category tier-2 match the LEAF shape. Returns the
    /// matched cluster id. Not a literal key map — a shape match.
    pub fn descent(&self, cat_vec: &[f64], leaf_vec: &[f64]) -> Option<String> {
        if self.clusters.is_empty() {
            return None;
        }
        let qcat = shape_key(cat_vec);
        let qleaf = shape_key(leaf_vec);
        // tier 1: clusters whose category shape is nearest the query's.
        let best_cat = self
            .clusters
            .values()
            .map(|c| shape_distance(&qcat, &c.cat_key))
            .min()
            .unwrap();
        let mut tier1: Vec<&ClusterEntry> = self
            .clusters
            .values()
            .filter(|c| shape_distance(&qcat, &c.cat_key) == best_cat)
            .collect();
        // tier 2: within that category, match the LEAF shape.
        tier1.sort_by_key(|c| shape_distance(&qleaf, &c.leaf_key));
        Some(tier1[0].cluster_id.clone())
    }

    pub fn size(&self) -> usize {
        self.clusters.len()
    }
}

// =======================================================================
// MemoryFaculty — composes the existing tiers + the new decision.
//   WORKING  = the resident graph, byte+count bounded by streaming forget
//              (CodeCache eviction-until-fits shape, keep_value-per-byte order).
//   HOT/COLD = HotCounter (cluster access recency).
//   LONG-TERM = ShapeIndex + per-cluster page-out via persist's encoder.
// Registered under MetaShape::DelayedPersistence.
// =======================================================================

pub struct MemoryFaculty {
    pub budget_nodes: usize,
    pub budget_bytes: usize,
    /// per-type per-round growth history (additions since last census).
    pub add_history: HashMap<Sym, Vec<i64>>,
    /// last census, to compute per-round additions.
    pub last_census: HashMap<Sym, i64>,
    pub round: i64,
    /// the long-term shape index (the RULE; bounded by #clusters).
    pub index: ShapeIndex,
    /// reused hot/cold tracker: records cluster accesses for recency.
    pub hot: HotCounter,
    /// how many rounds a cluster stays resident before shuffle evicts it.
    pub hot_window: i64,
    // --- the DISPOSABLE-tier CIRCULAR BUFFER (the sensory register) ---
    // Echoic/iconic memory is not an all-or-nothing tick flush — it is a
    // fixed-capacity ROLLING WINDOW of the most recent raw input, oldest
    // continuously overwritten, spanning the last few seconds ACROSS ticks.
    // The ring holds live disposable node ids oldest-at-front; admitting a
    // new one past capacity evicts the oldest (FIFO). Byte-bounded primarily
    // (a buffer has a size) with a node-count safety bound — byte-bounding
    // naturally keeps many cheap frames but only the freshest large decode
    // buffers, exactly the sensory register's shape.
    disposable_ring: VecDeque<NodeID>,
    disposable_tracked: HashSet<NodeID>,
    pub disposable_capacity_bytes: usize,
    pub disposable_capacity_nodes: usize,
}

impl Default for MemoryFaculty {
    fn default() -> Self {
        Self::new(5000, 64 * 1024 * 1024)
    }
}

impl MemoryFaculty {
    pub fn new(budget_nodes: usize, budget_bytes: usize) -> Self {
        Self {
            budget_nodes,
            budget_bytes,
            add_history: HashMap::new(),
            last_census: HashMap::new(),
            round: 0,
            index: ShapeIndex::new(),
            hot: HotCounter::new(),
            hot_window: 3,
            disposable_ring: VecDeque::new(),
            disposable_tracked: HashSet::new(),
            // ~the last few seconds of raw scratch: deep for tiny frames, only
            // the freshest one or two multi-MB decode buffers.
            disposable_capacity_bytes: 8 * 1024 * 1024,
            disposable_capacity_nodes: 1024,
        }
    }

    /// Register the faculty's operations under the DelayedPersistence
    /// subsystem (#449) in the L4 boundary registry.
    pub fn register_subsystem(reg: &mut SubsystemRegistry) {
        for op in [
            "memory_forget_over_budget",
            "memory_consolidate",
            "memory_shuffle",
            "memory_recall",
        ] {
            reg.register(op, MetaShape::DelayedPersistence);
        }
        // The GENERAL salience operator is a held capability used by BOTH
        // memory tiering and perception. Salience = attention/admissibility
        // filtering, so it registers under SelectiveGating (#1194), not the
        // persistence subsystem — it is not a memory-only op. keep_value
        // bridges from DelayedPersistence to this gating op.
        reg.register("order_n_shape_salience", MetaShape::SelectiveGating);
    }

    fn census(&self, s: &Substrate) -> HashMap<Sym, i64> {
        let mut out: HashMap<Sym, i64> = HashMap::new();
        for (_, nd) in s.graph.iter_nodes() {
            *out.entry(nd.type_).or_insert(0) += 1;
        }
        out
    }

    fn record_growth(&mut self, obs: &HashMap<Sym, i64>) {
        for (&t, &c) in obs {
            let add = c - self.last_census.get(&t).copied().unwrap_or(0);
            if add > 0 {
                self.add_history.entry(t).or_default().push(add);
            }
        }
    }

    /// Forget all instances of a type, leaving a tiny MemorySummary so the
    /// LEARNING (how much was seen) survives as compressed structure.
    fn forget_type(&mut self, s: &mut Substrate, t: Sym) -> usize {
        let ids = s.graph.nodes_of_type(t);
        if ids.is_empty() {
            return 0;
        }
        let n = ids.len();
        let type_name = s.interner.resolve(t).to_string();
        let summary_t = s.interner.intern("MemorySummary");
        let mut attrs = rustc_hash::FxHashMap::default();
        attrs.insert(s.interner.intern("of_type"), Value::Str(t));
        attrs.insert(s.interner.intern("n_forgotten"), Value::Int(n as i64));
        attrs.insert(s.interner.intern("round"), Value::Int(self.round));
        let note = s
            .interner
            .intern("raw perceptual scratch forgotten; structure kept");
        attrs.insert(s.interner.intern("note"), Value::Str(note));
        let _ = type_name;
        s.add_node(summary_t, attrs);
        for nid in ids {
            s.remove_node(nid);
        }
        n
    }

    /// STREAMING bound: while OVER budget (BYTES or count), forget the type
    /// with the LOWEST keep_value-per-byte among the forgettable types.
    /// Called DURING ingest so one pathological episode cannot spike.
    ///
    /// This reuses the `CodeCache::insert` eviction shape — "while over the
    /// bound, evict the next victim, recompute, repeat" — but the victim is
    /// chosen by the agent's keep_value-per-byte (ascending), not by LRU.
    pub fn forget_over_budget(&mut self, s: &mut Substrate) -> HashMap<String, usize> {
        let mut forgot: HashMap<String, usize> = HashMap::new();
        loop {
            let over_count = s.graph.node_count() > self.budget_nodes;
            let over_bytes = total_bytes(s) > self.budget_bytes;
            if !over_count && !over_bytes {
                break;
            }
            let obs = self.census(s);
            self.record_growth(&obs);
            // rank FORGETTABLE types by keep_value-per-byte (ascending).
            let mut cands: Vec<(f64, Sym)> = Vec::new();
            for (&t, &c) in &obs {
                if c == 0 {
                    continue;
                }
                let tname = s.interner.resolve(t).to_string();
                let (mp, nr, never) = role_for(&tname);
                if never {
                    continue;
                }
                let hist = self.add_history.get(&t).cloned().unwrap_or_else(|| vec![c]);
                if is_saturating(&hist) {
                    continue; // condensing structure -> keep
                }
                let kv = keep_value(&hist, mp, nr);
                let cost = type_bytes(s, t, 64).max(1);
                let score = kv / cost as f64; // keep_value PER BYTE
                cands.push((score, t));
            }
            if cands.is_empty() {
                break; // nothing forgettable remains
            }
            cands.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
            let victim = cands[0].1;
            let vname = s.interner.resolve(victim).to_string();
            let n = self.forget_type(s, victim);
            if n == 0 {
                break;
            }
            *forgot.entry(vname).or_insert(0) += n;
        }
        forgot
    }

    /// End-of-round bound. Records growth, runs the streaming forget,
    /// snapshots the census. Returns (nodes_before, bytes_before,
    /// nodes_after, bytes_after, forgot).
    pub fn observe_and_bound(
        &mut self,
        s: &mut Substrate,
    ) -> (usize, usize, usize, usize, HashMap<String, usize>) {
        self.round += 1;
        let obs = self.census(s);
        self.record_growth(&obs);
        let nodes_before = s.graph.node_count();
        let bytes_before = total_bytes(s);
        let forgot = self.forget_over_budget(s);
        self.last_census = self.census(s);
        (
            nodes_before,
            bytes_before,
            s.graph.node_count(),
            total_bytes(s),
            forgot,
        )
    }

    /// Forget all nodes of a named type, leaving a compressed MemorySummary
    /// (how many were seen). Use at a CONSOLIDATION boundary (e.g. end of a
    /// title) to retire a working trace whose purpose is served — the per-frame
    /// CortexStamp timing anchors once their cross-modal binding is captured.
    /// Returns the number forgotten.
    pub fn forget_named(&mut self, s: &mut Substrate, type_name: &str) -> usize {
        let t = s.interner.intern(type_name);
        self.forget_type(s, t)
    }

    /// Set the disposable circular-buffer capacity (the sensory-register span).
    pub fn set_disposable_capacity(&mut self, bytes: usize, nodes: usize) {
        self.disposable_capacity_bytes = bytes;
        self.disposable_capacity_nodes = nodes;
    }

    /// Estimated bytes currently held in the disposable ring (live ids only).
    fn ring_bytes(&self, s: &Substrate) -> usize {
        self.disposable_ring
            .iter()
            .filter(|&&id| s.graph.has_node(id))
            .map(|&id| node_bytes(s, id))
            .sum()
    }

    /// ROLL THE SENSORY REGISTER — the disposable tier as a CIRCULAR BUFFER.
    /// Admit every newly-seen disposable-tier node to the ring (oldest at
    /// front), then evict oldest-first until back under capacity (bytes OR
    /// node count). This is echoic/iconic memory: a fixed-capacity rolling
    /// window of the most recent raw input that persists a few seconds ACROSS
    /// ticks and is continuously overwritten — NOT an all-or-nothing flush.
    /// Call every tick (after the feature has been read into the kept tier).
    /// Returns {type: n_evicted} for the nodes pushed out this roll.
    pub fn roll_disposable(&mut self, s: &mut Substrate) -> HashMap<String, usize> {
        // 1. ADMIT: discover disposable nodes not yet tracked, in id order
        //    (deterministic; the deque preserves FIFO recency across ticks).
        let mut fresh: Vec<NodeID> = Vec::new();
        for (id, nd) in s.graph.iter_nodes() {
            let tname = s.interner.resolve(nd.type_);
            if tier_for(tname) == "disposable" && !self.disposable_tracked.contains(&id) {
                fresh.push(id);
            }
        }
        fresh.sort();
        for id in fresh {
            self.disposable_tracked.insert(id);
            self.disposable_ring.push_back(id);
        }
        // 2. EVICT oldest-first until under capacity.
        let mut evicted: HashMap<String, usize> = HashMap::new();
        loop {
            // drop any ids the graph already freed (kept the ring honest).
            while let Some(&front) = self.disposable_ring.front() {
                if s.graph.has_node(front) {
                    break;
                }
                self.disposable_ring.pop_front();
                self.disposable_tracked.remove(&front);
            }
            let over = self.disposable_ring.len() > self.disposable_capacity_nodes
                || self.ring_bytes(s) > self.disposable_capacity_bytes;
            if !over {
                break;
            }
            let Some(victim) = self.disposable_ring.pop_front() else {
                break;
            };
            self.disposable_tracked.remove(&victim);
            if s.graph.has_node(victim) {
                let tname = s.interner.resolve(s.graph.node(victim).type_).to_string();
                if s.remove_node(victim) {
                    *evicted.entry(tname).or_insert(0) += 1;
                }
            }
        }
        evicted
    }

    /// EAGER SENSORY-CACHE FLUSH — drop every disposable-tier node NOW
    /// (echoic/iconic memory: the raw per-input firehose, gone every tick,
    /// never consolidated). Unlike `forget_over_budget` this is UNCONDITIONAL
    /// (not gated on budget pressure) and leaves NO MemorySummary: disposable
    /// scratch carries no learning to preserve — the feature was already read
    /// into the working tier (the AcousticSign). Call at tick end, after the
    /// feature extraction that consumes the firehose. Returns {type: n_dropped}.
    pub fn drop_disposable(&mut self, s: &mut Substrate) -> HashMap<String, usize> {
        let obs = self.census(s);
        let mut dropped: HashMap<String, usize> = HashMap::new();
        for &t in obs.keys() {
            let tname = s.interner.resolve(t).to_string();
            if tier_for(&tname) != "disposable" {
                continue;
            }
            let ids = s.graph.nodes_of_type(t);
            let n = ids.len();
            if n == 0 {
                continue;
            }
            for nid in ids {
                s.remove_node(nid);
            }
            dropped.insert(tname, n);
        }
        // the ring's ids are now stale — clear its bookkeeping.
        self.disposable_ring.clear();
        self.disposable_tracked.clear();
        dropped
    }

    /// VALUE-FOR-COMPUTE CENSUS (read-only). For every node type currently
    /// resident, surface the agent's OWN keep verdict — the same quantities
    /// `forget_over_budget` ranks victims by, nothing new: count, estimated
    /// bytes, the role multipliers (miss_penalty, non_rebuildability,
    /// never_forget), whether its growth shape is saturating (condensing
    /// structure), its `keep_value`, and `keep_value`-PER-BYTE. The last is
    /// the agent's value-for-compute score: the bytes are the storage cost a
    /// stage's output imposes; keep_value is what that output is worth to keep;
    /// low keep_value-per-byte == the agent paid compute/store for structure it
    /// would shed first. The world adapter pairs this with per-STAGE wall-time
    /// to read "value returned per unit compute spent." No decision is taken
    /// here — this only REPORTS the operators' existing output.
    #[allow(clippy::type_complexity)]
    pub fn value_report(
        &self,
        s: &Substrate,
    ) -> Vec<(String, usize, usize, f64, f64, f64, f64, bool, bool, String)> {
        let obs = self.census(s);
        let mut rows: Vec<(String, usize, usize, f64, f64, f64, f64, bool, bool, String)> =
            Vec::new();
        for (&t, &c) in &obs {
            if c == 0 {
                continue;
            }
            let tname = s.interner.resolve(t).to_string();
            let (mp, nr, never) = role_for(&tname);
            let tier = tier_for(&tname).to_string();
            // use the recorded growth history if we have it, else treat the
            // current count as a single observation (same fallback the forget
            // path uses) so a report works even before any round boundary.
            let hist = self
                .add_history
                .get(&t)
                .cloned()
                .unwrap_or_else(|| vec![c as i64]);
            let sat = is_saturating(&hist);
            let kv = keep_value(&hist, mp, nr);
            let bytes = type_bytes(s, t, 64);
            let kv_per_byte = kv / bytes.max(1) as f64;
            rows.push((
                tname,
                c as usize,
                bytes,
                kv,
                kv_per_byte,
                mp,
                nr,
                never,
                sat,
                tier,
            ));
        }
        // ascending keep_value-per-byte == the agent's forget order: the head
        // of the list is what it would discard first (lowest value-for-compute).
        rows.sort_by(|a, b| a.4.partial_cmp(&b.4).unwrap_or(std::cmp::Ordering::Equal));
        rows
    }

    // ---- LONG-TERM: consolidate / shuffle / recall (reuse persist + HotCounter) ----

    /// Consolidate a freshly-learned record to durable disk + index it into
    /// its order-N shape cluster + mark the cluster hot (HotCounter record).
    /// Reuses `persist::encode_value` for the durable JSON.
    pub fn consolidate(
        &mut self,
        s: &mut Substrate,
        store_dir: &str,
        key: &str,
        nid: NodeID,
        round: i64,
        cat_vec: &[f64],
        leaf_vec: &[f64],
    ) -> std::io::Result<String> {
        std::fs::create_dir_all(store_dir)?;
        let safe: String = key
            .chars()
            .map(|c| {
                if c.is_alphanumeric() || "-_.".contains(c) {
                    c
                } else {
                    '_'
                }
            })
            .collect();
        let path = format!("{}/{}.json", store_dir, safe);
        // Reuse the substrate's durable wire format: encode the node's attrs
        // through persist::encode_value so a cluster round-trips identically
        // to a full save.
        let nd = s.graph.node(nid);
        let mut attrs_json = serde_json::Map::new();
        for (k, v) in nd.attrs.iter() {
            attrs_json.insert(
                s.interner.resolve(*k).to_string(),
                crate::persist::encode_value(v, &s.interner),
            );
        }
        let rec = serde_json::json!({
            "key": key,
            "round": round,
            "type": s.interner.resolve(nd.type_),
            "attrs": serde_json::Value::Object(attrs_json),
        });
        std::fs::write(&path, serde_json::to_string(&rec)?)?;
        let cid = self
            .index
            .put(key, cat_vec, leaf_vec, &path, round, Some(nid));
        // reuse HotCounter as the hot/cold tracker: a consolidate is an access.
        let cid_sym = s.interner.intern(&cid);
        self.hot.record(cid_sym);
        Ok(cid)
    }

    /// Rebuild one non-resident ShapeIndex entry from an existing durable
    /// record. The host adapter validates/decodes the record header and
    /// supplies its already-projected shape vectors; this method owns the
    /// index insertion and rejects paths which no longer exist.
    pub fn index_disk_record(
        &mut self,
        key: &str,
        path: &str,
        round: i64,
        cat_vec: &[f64],
        leaf_vec: &[f64],
    ) -> std::io::Result<String> {
        if !std::path::Path::new(path).is_file() {
            return Err(std::io::Error::new(
                std::io::ErrorKind::NotFound,
                format!("memory record not found: {}", path),
            ));
        }
        Ok(self.index.put(key, cat_vec, leaf_vec, path, round, None))
    }

    /// Remove an ambiguous disk key from the native index during recovery.
    pub fn unindex_disk_record(&mut self, key: &str) {
        self.index.remove_key(key);
    }

    /// SHUFFLE: evict cold CLUSTERS from RAM (disk copy persists). A cluster
    /// not accessed within hot_window rounds is cold -> page the drawer out
    /// as a unit. Returns the evicted cluster ids.
    pub fn shuffle(&mut self, s: &mut Substrate, round: i64) -> Vec<String> {
        let mut evicted = Vec::new();
        let cold: Vec<String> = self
            .index
            .clusters
            .values()
            .filter(|c| c.resident && round - c.last_round > self.hot_window)
            .map(|c| c.cluster_id.clone())
            .collect();
        for cid in cold {
            if let Some(cl) = self.index.clusters.get_mut(&cid) {
                let nids: Vec<NodeID> = cl.node_ids.values().copied().collect();
                for nid in nids {
                    s.remove_node(nid);
                }
                cl.node_ids.clear();
                cl.resident = false;
                evicted.push(cid);
            }
        }
        evicted
    }

    /// PREFETCH the whole drawer hot (cache-line + spreading-activation):
    /// page in every record of the cluster as a unit, via the persist decoder.
    fn page_in_cluster(&mut self, s: &mut Substrate, cid: &str, round: i64) -> usize {
        let paths: Vec<(String, String)> = match self.index.clusters.get(cid) {
            Some(cl) => cl
                .paths
                .iter()
                .filter(|(k, _)| !cl.node_ids.contains_key(*k))
                .map(|(k, p)| (k.clone(), p.clone()))
                .collect(),
            None => return 0,
        };
        let mut paged = 0;
        for (key, path) in paths {
            let Ok(text) = std::fs::read_to_string(&path) else {
                continue;
            };
            let Ok(rec): Result<serde_json::Value, _> = serde_json::from_str(&text) else {
                continue;
            };
            let type_str = rec
                .get("type")
                .and_then(|t| t.as_str())
                .unwrap_or("MemoryRecord");
            let type_sym = s.interner.intern(type_str);
            let mut attrs = rustc_hash::FxHashMap::default();
            if let Some(amap) = rec.get("attrs").and_then(|a| a.as_object()) {
                for (k, av) in amap {
                    let ksym = s.interner.intern(k);
                    let v = crate::persist::decode_value(av, &mut s.interner);
                    attrs.insert(ksym, v);
                }
            }
            let nid = s.add_node(type_sym, attrs);
            if let Some(cl) = self.index.clusters.get_mut(cid) {
                cl.node_ids.insert(key, nid);
            }
            paged += 1;
        }
        if let Some(cl) = self.index.clusters.get_mut(cid) {
            cl.resident = true;
            cl.last_round = round;
        }
        paged
    }

    /// RECALL BY SHAPE: the order-N shape descent locates the cluster; page
    /// the whole drawer hot. Returns (cluster_id, n_paged_in).
    pub fn recall_by_shape(
        &mut self,
        s: &mut Substrate,
        cat_vec: &[f64],
        leaf_vec: &[f64],
        round: i64,
    ) -> Option<(String, usize)> {
        let cid = self.index.descent(cat_vec, leaf_vec)?;
        // reuse HotCounter: a recall is an access to this cluster's kind.
        let cid_sym = s.interner.intern(&cid);
        self.hot.record(cid_sym);
        let paged = self.page_in_cluster(s, &cid, round);
        Some((cid, paged))
    }

    /// Exact-key recall after the host adapter has rebuilt disk index entries.
    /// Pages the matched cluster using the same whole-drawer policy as shape
    /// recall, then returns the resident NodeID for the requested key.
    pub fn recall_by_key(&mut self, s: &mut Substrate, key: &str, round: i64) -> Option<NodeID> {
        let cid = self
            .index
            .clusters
            .values()
            .find(|cluster| cluster.paths.contains_key(key))
            .map(|cluster| cluster.cluster_id.clone())?;
        let cid_sym = s.interner.intern(&cid);
        self.hot.record(cid_sym);
        self.page_in_cluster(s, &cid, round);
        self.index
            .clusters
            .get(&cid)
            .and_then(|cluster| cluster.node_ids.get(key).copied())
    }

    pub fn findable_clusters(&self) -> usize {
        self.index.size()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn salience_flat_is_zero_varied_is_high() {
        // a flat firehose: ~constant growth -> ~0 salience -> forget.
        assert!(salience(&[1000, 1000, 1000, 1000]) < 1.0);
        // a varied/condensing growth -> high salience -> keep.
        assert!(salience(&[100, 50, 20, 5]) > 100.0);
    }

    #[test]
    fn saturation_detects_deceleration() {
        // condensing lexicon: later additions smaller -> saturating.
        assert!(is_saturating(&[100, 40, 10, 2]));
        // flat firehose: constant additions -> not saturating.
        assert!(!is_saturating(&[1000, 1000, 1000]));
        // accelerating: not saturating.
        assert!(!is_saturating(&[2, 10, 40, 100]));
    }

    #[test]
    fn shape_salience_tada_high_flat_low_random_low() {
        // a tada: a directed RISING build that resolves at a late peak.
        let tada: Vec<f64> = vec![0.0, 0.3, 0.7, 1.2, 1.8, 2.5, 3.3, 4.0];
        // flat: no variation -> magnitude 0 -> salience 0.
        let flat: Vec<f64> = vec![2.0; 8];
        // random: same magnitude as the build but no consistent direction.
        let random: Vec<f64> = vec![2.0, -1.5, 1.8, -2.0, 1.0, -1.2, 2.2, -1.8];
        let s_tada = order_n_shape_salience(&tada);
        let s_flat = order_n_shape_salience(&flat);
        let s_rand = order_n_shape_salience(&random);
        assert!(s_tada > s_flat, "tada {} flat {}", s_tada, s_flat);
        assert!(s_tada > s_rand, "tada {} random {}", s_tada, s_rand);
        assert!(s_flat < 1e-9, "flat should be ~0, got {}", s_flat);
    }

    #[test]
    fn shape_salience_falling_resolution_also_salient() {
        // beats TIGHTENING = inter-onset interval FALLING to a settled low.
        let tighten: Vec<f64> = vec![1.0, 0.85, 0.7, 0.5, 0.35, 0.22, 0.15, 0.12];
        let flat: Vec<f64> = vec![0.5; 8];
        let s_t = order_n_shape_salience(&tighten);
        let s_f = order_n_shape_salience(&flat);
        assert!(s_t > s_f, "tightening {} flat {}", s_t, s_f);
        assert!(s_t > 0.0);
    }

    #[test]
    fn keep_value_forgets_firehose_keeps_lexicon() {
        // firehose: flat growth, low miss-penalty, rebuildable -> low kv.
        let firehose = keep_value(&[1000, 1000, 1000], 1.0, 0.02);
        // lexicon: condensing growth, high miss-penalty, not rebuildable.
        let lexicon = keep_value(&[100, 40, 10, 2], 5.0, 1.0);
        assert!(
            lexicon > firehose,
            "lexicon {} firehose {}",
            lexicon,
            firehose
        );
    }

    #[test]
    fn shape_key_is_rank_and_gain_invariant() {
        let a = shape_key(&[1.0, 3.0, 2.0]);
        // gain-scaled + level-shifted: same ordinal arrangement -> same key.
        let b = shape_key(&[10.0 + 1.0, 10.0 + 9.0, 10.0 + 6.0]);
        assert_eq!(a, b);
        assert_eq!(a, vec![0, 2, 1]);
    }

    #[test]
    fn shape_index_descent_finds_matching_cluster() {
        let mut idx = ShapeIndex::new();
        idx.put(
            "rec_a",
            &[1.0, 3.0, 2.0],
            &[1.0, 2.0, 3.0],
            "/tmp/a.json",
            1,
            None,
        );
        idx.put(
            "rec_b",
            &[5.0, 1.0, 2.0],
            &[3.0, 2.0, 1.0],
            "/tmp/b.json",
            1,
            None,
        );
        // query whose category shape matches rec_a's arrangement.
        let hit = idx.descent(&[2.0, 6.0, 4.0], &[1.0, 2.0, 3.0]).unwrap();
        assert_eq!(hit, ShapeIndex::cluster_id(&[1.0, 3.0, 2.0]));
        // index footprint == #clusters (a RULE), not #items.
        assert_eq!(idx.size(), 2);
    }

    #[test]
    fn shape_signature_links_same_shape_across_surface_difference() {
        // Two accelerando-crescendo -> climax build-ups that differ in EVERY
        // surface way (level + gain): a quiet cartoon-scale build and a loud
        // orchestra-scale build. Same order-N SHAPE -> NEIGHBOURING signatures.
        let cartoon: Vec<f64> = (0..12).map(|i| 0.05 * i as f64).collect();
        let orchestra: Vec<f64> = (0..12).map(|i| 100.0 + 9.0 * i as f64).collect();
        let sig_c = shape_signature(&cartoon);
        let sig_o = shape_signature(&orchestra);
        let thr = shape_neighbour_threshold(12);
        assert_eq!(sig_c, sig_o, "same shape -> identical rank signature");
        assert!(shape_distance(&sig_c, &sig_o) < thr, "shape-neighbours");

        // A FLAT control + a non-monotone control are NOT shape-neighbours.
        let flat: Vec<f64> = vec![0.5; 12];
        let zigzag: Vec<f64> = (0..12)
            .map(|i| if i % 2 == 0 { 0.0 } else { 1.0 })
            .collect();
        assert!(
            shape_distance(&sig_c, &shape_signature(&flat)) >= thr,
            "flat is not a build-neighbour"
        );
        assert!(
            shape_distance(&sig_c, &shape_signature(&zigzag)) >= thr,
            "zigzag is not a build-neighbour"
        );
    }
}
