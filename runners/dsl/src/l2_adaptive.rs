//! L2 adaptive — wires `l2_dispatch::Scheduler` + `code_cache::CodeCache`
//! together with hot-counter tracking, Γ-epoch invalidation, and tier-up
//! policy.
//!
//! ## What this realises
//!
//! Instantiates the implementable components of the
//! `adaptive_tiered_dispatch` Mt (commit e9b607a) on top of:
//!
//! - `l2_dispatch::Scheduler`     (the static EDF floor, commit 3c791f8)
//! - `code_cache::CodeCache`      (bounded LRU + Arc reclamation,
//!                                  commit f1f376f)
//!
//! Each piece of the Mt that's now real:
//!
//! - **`hot_counter_per_kind`** — `HotCounter` map Sym → AtomicU64.
//! - **`tier_up_policy_threshold`** — `TierUpPolicy { threshold }`.
//! - **`gamma_epoch_counter`** — `Epoch` atomic, bumped on Γ mutation.
//! - **`compiled_artefact_cache`** — `CodeCache<Sym, EpochStamped<T>>`,
//!   each artefact stamped with the epoch it was compiled against.
//! - **`per_thread_vs_shared_cache`** — shared, via Arc<CodeCache>.
//!
//! ## What's still deferred (named in the Mt)
//!
//! - `inline_cache_per_callsite` — needs callsite identity in the
//!   substrate's rule firing path.
//! - `tracing_vs_method_jit_choice`, `speculation_with_guards`,
//!   `deoptimisation_on_stack_replacement`, `patch_point_atomic_overwrite` —
//!   require JIT cooperation (L5).
//! - `deadline_inheritance_for_shared_rule_state` — needs shared rule
//!   state tracking.
//! - `anytime_degradation_under_overload` — needs overload monitoring.
//! - `second_order_scheduler_state_as_graph` — needs substrate integration
//!   (dispatcher state exposed AS graph data).
//!
//! ## Invariants verified (matching the Mt's named invariants)
//!
//! - **`axiom3_satisfied_via_gamma_epoch`** — test
//!   `gamma_bump_invalidates_cached_artefacts`.
//! - **`tier_up_fires_exactly_at_threshold`** (rule) — test
//!   `tier_up_signals_at_exact_threshold_then_quiet`.
//! - **`guard_failure_cools_speculation`** (rule) — test
//!   `cool_kind_resets_counter_and_evicts_cached`.
//!
//! - `correctness_via_interpreter_fallback`, `bounded_deopt_amortised_cost`,
//!   `osr_deopt_reconstructable` — depend on JIT integration (L5), deferred.
//! - `schedulability_under_dynamic_load` — needs load monitoring, deferred.
//! - `reflective_transparency_of_dispatcher` — needs substrate integration,
//!   deferred.

use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use crate::clock::Instant;

use crate::code_cache::{CodeCache, CodeCacheConfig, CodeSize};
use crate::l2_dispatch::{PriorityClass, Scheduler, Task};
use crate::sym::Sym;

// =======================================================================
// Epoch — `gamma_epoch_counter` component.
// =======================================================================

/// Monotonically-increasing counter bumped on every Γ mutation.
/// Compiled artefacts stamp themselves with the current epoch at
/// compile time; lookups compare; mismatch ⇒ artefact stale.
///
/// Cloneable so the same Epoch instance can be shared between the
/// dispatcher and the substrate's Γ-mutation surface.
#[derive(Clone)]
pub struct Epoch {
    n: Arc<AtomicU64>,
}

impl Epoch {
    pub fn new() -> Self {
        Self {
            n: Arc::new(AtomicU64::new(0)),
        }
    }

    /// Current epoch — Acquire so workers see the mutation that
    /// preceded the most recent bump.
    #[inline]
    pub fn current(&self) -> u64 {
        self.n.load(Ordering::Acquire)
    }

    /// Copy the current version into an independent counter. Experiment
    /// branches must not share Γ invalidation with their primary substrate.
    pub fn detached(&self) -> Self {
        Self {
            n: Arc::new(AtomicU64::new(self.current())),
        }
    }

    /// Bump after Γ mutation. Release ordering pairs with the
    /// Acquire reads on `current()`.
    pub fn bump(&self) -> u64 {
        self.n.fetch_add(1, Ordering::Release) + 1
    }
}

impl Default for Epoch {
    fn default() -> Self {
        Self::new()
    }
}

// =======================================================================
// HotCounter — `hot_counter_per_kind` component.
// =======================================================================

/// Per-kind atomic firing counter. Lookup is mutex-guarded (one-shot
/// per kind to create the AtomicU64); subsequent increments are
/// lock-free via the Arc<AtomicU64>.
pub struct HotCounter {
    counts: Mutex<HashMap<Sym, Arc<AtomicU64>>>,
}

impl HotCounter {
    pub fn new() -> Self {
        Self {
            counts: Mutex::new(HashMap::new()),
        }
    }

    /// Record a fire for `kind`; return the post-increment count.
    /// Allocates the counter on first fire.
    pub fn record(&self, kind: Sym) -> u64 {
        let counter = {
            let mut map = self.counts.lock().unwrap();
            map.entry(kind)
                .or_insert_with(|| Arc::new(AtomicU64::new(0)))
                .clone()
        };
        counter.fetch_add(1, Ordering::Relaxed) + 1
    }

    pub fn count(&self, kind: Sym) -> u64 {
        self.counts
            .lock()
            .unwrap()
            .get(&kind)
            .map(|c| c.load(Ordering::Relaxed))
            .unwrap_or(0)
    }

    /// Reset a kind's counter to zero. Called on `guard_failure_cools_
    /// speculation` (Mt rule) — a cooled kind starts fresh and must
    /// re-hot before tiering up again.
    pub fn reset(&self, kind: Sym) {
        if let Some(c) = self.counts.lock().unwrap().get(&kind) {
            c.store(0, Ordering::Relaxed);
        }
    }

    /// Snapshot (kind, count) pairs — for monitoring + cooling decisions.
    pub fn snapshot(&self) -> Vec<(Sym, u64)> {
        self.counts
            .lock()
            .unwrap()
            .iter()
            .map(|(k, v)| (*k, v.load(Ordering::Relaxed)))
            .collect()
    }
}

impl Default for HotCounter {
    fn default() -> Self {
        Self::new()
    }
}

// =======================================================================
// TierUpPolicy — `tier_up_policy_threshold` component.
// =======================================================================

#[derive(Debug, Clone, Copy)]
pub struct TierUpPolicy {
    /// Fires per kind above which the dispatcher signals `TierUp`.
    /// Default 100 — matches the substrate's typical "rare rule
    /// fires a few times, dominant rule fires thousands" distribution.
    pub threshold: u64,
    /// Consecutive guard failures (or epoch-stale hits) that cool
    /// a kind back to interpreted-only. Matches the Mt's
    /// `guard_failure_cools_speculation` rule.
    pub cooling_threshold: u32,
}

impl Default for TierUpPolicy {
    fn default() -> Self {
        Self {
            threshold: 100,
            cooling_threshold: 3,
        }
    }
}

// =======================================================================
// EpochStamped — bundles a compile-epoch with the artefact so we
// can detect staleness on read.
// =======================================================================

/// Wraps a compiled payload `T` with the Γ-epoch at which it was
/// compiled. Lookups check current epoch == stamp; mismatch ⇒
/// stale, treated as cache miss.
pub struct EpochStamped<T> {
    pub epoch_at_compile: u64,
    pub inner: T,
}

impl<T: CodeSize> CodeSize for EpochStamped<T> {
    fn code_size_bytes(&self) -> usize {
        self.inner.code_size_bytes()
    }
}

// =======================================================================
// DispatchOutcome — the signal `submit_typed` returns so the caller
// can trigger compilation on tier-up.
// =======================================================================

/// What happened on `submit_typed`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DispatchOutcome {
    /// Task queued; kind hasn't reached the tier-up threshold yet.
    Queued { kind: Sym, count: u64 },
    /// Task queued AND this submit crossed the threshold — caller
    /// should trigger an async compile pass for `kind`. Subsequent
    /// submits stay `Queued` (or `Cached` once compile finishes)
    /// until the kind cools.
    TierUp { kind: Sym, count: u64 },
    /// Task queued AND a fresh-epoch artefact is in the cache —
    /// the caller's worker function can use it directly.
    Cached { kind: Sym, count: u64 },
}

// =======================================================================
// TypedTask — `Task` with a kind tag for hot tracking.
// =======================================================================

pub struct TypedTask {
    pub kind: Sym,
    pub deadline: Instant,
    pub class: PriorityClass,
    pub work: Box<dyn FnOnce() + Send + 'static>,
}

// =======================================================================
// AdaptiveDispatcher — the composed dispatcher.
// =======================================================================

pub struct AdaptiveDispatcher<T>
where
    T: CodeSize + Send + Sync + 'static,
{
    scheduler: Scheduler,
    hot: Arc<HotCounter>,
    epoch: Epoch,
    cache: Arc<CodeCache<Sym, EpochStamped<T>>>,
    policy: TierUpPolicy,
    /// Opt-in adjustable threshold. When `Some`, the dispatcher uses
    /// the atomic's load instead of `policy.threshold`. Installed via
    /// `install_threshold_knob()`; lets L6 cybernetic feedback adjust
    /// the tier-up threshold at runtime without locking.
    threshold_knob: Option<Arc<std::sync::atomic::AtomicU64>>,
    /// Per-kind consecutive guard-failure / epoch-stale count.
    /// When this reaches `policy.cooling_threshold`, the kind is
    /// cooled (counter reset + cache entry evicted).
    guard_failures: Mutex<HashMap<Sym, u32>>,
}

impl<T> AdaptiveDispatcher<T>
where
    T: CodeSize + Send + Sync + 'static,
{
    pub fn new(scheduler: Scheduler, policy: TierUpPolicy, cache_config: CodeCacheConfig) -> Self {
        Self::with_shared_epoch(scheduler, policy, cache_config, Epoch::new())
    }

    /// Construct the dispatcher using a pre-existing `Epoch`, e.g.
    /// one cloned from `Substrate::gamma_epoch`. Γ mutations on the
    /// substrate then propagate to this dispatcher's cache
    /// invalidation surface without extra wiring.
    pub fn with_shared_epoch(
        scheduler: Scheduler,
        policy: TierUpPolicy,
        cache_config: CodeCacheConfig,
        epoch: Epoch,
    ) -> Self {
        Self {
            scheduler,
            hot: Arc::new(HotCounter::new()),
            epoch,
            cache: Arc::new(CodeCache::new(cache_config)),
            policy,
            threshold_knob: None,
            guard_failures: Mutex::new(HashMap::new()),
        }
    }

    /// Install an adjustable threshold knob. Returns the `Arc<AtomicU64>`
    /// handle the caller can store (e.g. in an L6
    /// `RecommendationApplier`). Once installed, the dispatcher reads
    /// the threshold from the atomic on every submit instead of from
    /// `policy.threshold`. Allows L6 cybernetic feedback to adjust
    /// the tier-up threshold at runtime via the knob's `store`.
    pub fn install_threshold_knob(&mut self) -> Arc<std::sync::atomic::AtomicU64> {
        let knob = Arc::new(std::sync::atomic::AtomicU64::new(self.policy.threshold));
        self.threshold_knob = Some(Arc::clone(&knob));
        knob
    }

    /// Current effective threshold: the knob if installed, else
    /// `policy.threshold`.
    fn effective_threshold(&self) -> u64 {
        match &self.threshold_knob {
            Some(k) => k.load(std::sync::atomic::Ordering::Acquire),
            None => self.policy.threshold,
        }
    }

    /// Use the dispatcher's epoch (e.g. for sharing with the
    /// substrate's Γ-mutation surface).
    pub fn epoch(&self) -> Epoch {
        self.epoch.clone()
    }

    pub fn hot_counter(&self) -> Arc<HotCounter> {
        Arc::clone(&self.hot)
    }

    pub fn cache(&self) -> Arc<CodeCache<Sym, EpochStamped<T>>> {
        Arc::clone(&self.cache)
    }

    pub fn policy(&self) -> TierUpPolicy {
        self.policy
    }

    /// Submit a typed task. Records the fire, classifies the outcome,
    /// enqueues to the underlying EDF scheduler.
    ///
    /// Outcome semantics implement the Mt's
    /// `tier_up_fires_exactly_at_threshold` rule.
    pub fn submit(&self, task: TypedTask) -> DispatchOutcome {
        let kind = task.kind;
        let count = self.hot.record(kind);

        // Classify BEFORE submitting so the caller can take action
        // (e.g. trigger compile) in parallel with task execution.
        let outcome = if self.has_fresh_cached(kind) {
            DispatchOutcome::Cached { kind, count }
        } else if count == self.effective_threshold() {
            DispatchOutcome::TierUp { kind, count }
        } else {
            DispatchOutcome::Queued { kind, count }
        };

        self.scheduler.submit(Task {
            deadline: task.deadline,
            class: task.class,
            work: task.work,
        });

        outcome
    }

    /// True iff the cache holds an artefact for `kind` stamped with
    /// the current epoch (not stale).
    pub fn has_fresh_cached(&self, kind: Sym) -> bool {
        let current = self.epoch.current();
        self.cache
            .get(&kind)
            .map(|arc| arc.epoch_at_compile == current)
            .unwrap_or(false)
    }

    /// Fetch a fresh-epoch cached artefact, or None if absent / stale.
    /// Returns the inner Arc<EpochStamped<T>> so callers can hold it
    /// safely across cache eviction (Arc reclamation semantics).
    pub fn get_compiled(&self, kind: Sym) -> Option<Arc<EpochStamped<T>>> {
        let current = self.epoch.current();
        self.cache
            .get(&kind)
            .filter(|arc| arc.epoch_at_compile == current)
    }

    /// Install a freshly-compiled artefact. Stamped with the CURRENT
    /// epoch; if Γ mutates between compile-start and install, the
    /// artefact installs stale and will be re-detected as stale on
    /// next lookup. Caller can mitigate by snapshotting epoch at
    /// compile-start and refusing to install if it changed.
    ///
    /// Returns evicted artefacts (LRU bound) — their underlying
    /// memory frees when no clone holds them (Arc semantics).
    pub fn install_compiled(&self, kind: Sym, artefact: T) -> Vec<Arc<EpochStamped<T>>> {
        let stamped = EpochStamped {
            epoch_at_compile: self.epoch.current(),
            inner: artefact,
        };
        // On a successful install, reset the guard-failure count
        // for this kind: it's now compiled afresh, deserves the
        // benefit of the doubt.
        self.guard_failures.lock().unwrap().remove(&kind);
        self.cache.insert(kind, stamped)
    }

    /// Caller invokes this when:
    ///   · Γ has been mutated. ALL stamps become stale on next read.
    pub fn invalidate_gamma(&self) -> u64 {
        self.epoch.bump()
    }

    /// Report a guard failure or epoch-stale hit for `kind`. After
    /// `policy.cooling_threshold` consecutive failures, the kind is
    /// cooled: hot counter reset + cached artefact evicted.
    /// Implements the Mt's `guard_failure_cools_speculation` rule.
    pub fn report_guard_failure(&self, kind: Sym) -> GuardFailureOutcome {
        let mut fails = self.guard_failures.lock().unwrap();
        let n = fails.entry(kind).or_insert(0);
        *n += 1;
        let count = *n;
        if count >= self.policy.cooling_threshold {
            // Cool: reset, evict, drop the failure count too.
            fails.remove(&kind);
            drop(fails);
            self.hot.reset(kind);
            let _ = self.cache.remove(&kind);
            GuardFailureOutcome::Cooled {
                kind,
                consecutive: count,
            }
        } else {
            GuardFailureOutcome::Counted {
                kind,
                consecutive: count,
            }
        }
    }

    /// Drain queue + shut down workers.
    pub fn drain_and_shutdown(self) {
        self.scheduler.drain_and_shutdown();
    }

    pub fn shutdown(self) {
        self.scheduler.shutdown();
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum GuardFailureOutcome {
    Counted { kind: Sym, consecutive: u32 },
    Cooled { kind: Sym, consecutive: u32 },
}

// =======================================================================
// DispatcherSnapshot — `second_order_scheduler_state_as_graph` component
// of the adaptive_tiered_dispatch Mt. Pure-data view of the dispatcher's
// runtime state, materialisable into the substrate's typed graph by
// `l2_graph_bridge` so reflexes can introspect dispatcher behaviour.
// =======================================================================

/// One cached-artefact summary entry.
#[derive(Debug, Clone)]
pub struct CachedEntrySummary {
    pub kind: Sym,
    pub epoch_at_compile: u64,
    pub code_size_bytes: usize,
}

/// Snapshot of dispatcher state. Returned by
/// [`AdaptiveDispatcher::snapshot`]; consumed by
/// `l2_graph_bridge::install_snapshot_into_graph` to materialise as
/// graph nodes. Read-only — taking a snapshot doesn't mutate the
/// dispatcher.
#[derive(Debug, Clone)]
pub struct DispatcherSnapshot {
    pub epoch: u64,
    pub policy: TierUpPolicy,
    pub cache_max_bytes: usize,
    /// (kind, fire_count) pairs.
    pub hot_counters: Vec<(Sym, u64)>,
    pub cached: Vec<CachedEntrySummary>,
    pub total_cache_bytes: usize,
}

impl<T> AdaptiveDispatcher<T>
where
    T: CodeSize + Send + Sync + 'static,
{
    /// Pure-data snapshot of dispatcher state. Honours the
    /// `second_order_scheduler_state_as_graph` component of the
    /// adaptive_tiered_dispatch Mt (Axiom 3 at the L2 dispatcher
    /// layer — dispatcher is observable from within G).
    ///
    /// `cached` doesn't include the artefact `T` itself (cheap +
    /// avoids T: Clone bound); summary attrs only.
    pub fn snapshot(&self) -> DispatcherSnapshot {
        let hot_counters = self.hot.snapshot();
        let total_cache_bytes = self.cache.total_bytes();
        let cache_max_bytes = self.cache.config().max_bytes;
        // Gather cached entries' summaries. The cache stores
        // EpochStamped<T> behind Arc; iterating over keys requires
        // a small accessor — for v1 we use lru_order() + get() per
        // key (correct but O(n × lru) which is fine for hundreds
        // of entries).
        let mut cached = Vec::new();
        for k in self.cache.lru_order() {
            if let Some(arc) = self.cache.get(&k) {
                cached.push(CachedEntrySummary {
                    kind: k,
                    epoch_at_compile: arc.epoch_at_compile,
                    code_size_bytes: arc.code_size_bytes(),
                });
            }
        }
        DispatcherSnapshot {
            epoch: self.epoch.current(),
            policy: self.policy,
            cache_max_bytes,
            hot_counters,
            cached,
            total_cache_bytes,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::AtomicUsize;
    use std::time::Duration;

    use crate::sym::Interner;

    struct FakeJit {
        size: usize,
    }
    impl CodeSize for FakeJit {
        fn code_size_bytes(&self) -> usize {
            self.size
        }
    }

    fn dispatcher_with_threshold(t: u64) -> AdaptiveDispatcher<FakeJit> {
        AdaptiveDispatcher::new(
            Scheduler::new(1),
            TierUpPolicy {
                threshold: t,
                cooling_threshold: 3,
            },
            CodeCacheConfig { max_bytes: 4096 },
        )
    }

    /// Mt rule: tier_up_fires_exactly_at_threshold.
    #[test]
    fn tier_up_signals_at_exact_threshold_then_quiet() {
        let mut i = Interner::new();
        let kind = i.intern("hot_rule");
        let d = dispatcher_with_threshold(5);
        let counter = Arc::new(AtomicUsize::new(0));

        let mut outcomes = Vec::new();
        for _ in 0..10 {
            let c = Arc::clone(&counter);
            outcomes.push(d.submit(TypedTask {
                kind,
                deadline: Instant::now() + Duration::from_secs(60),
                class: PriorityClass::BestEffort,
                work: Box::new(move || {
                    c.fetch_add(1, Ordering::SeqCst);
                }),
            }));
        }

        // Submissions 1..4 → Queued; submission 5 → TierUp;
        // submissions 6..10 → Queued (caller hasn't installed
        // a compile yet).
        for (idx, o) in outcomes.iter().enumerate() {
            let n = idx + 1;
            match (n, *o) {
                (5, DispatchOutcome::TierUp { count, .. }) => {
                    assert_eq!(count, 5);
                }
                (_, DispatchOutcome::Queued { count, .. }) => {
                    assert_eq!(count, n as u64);
                }
                _ => panic!("submit {} unexpected: {:?}", n, o),
            }
        }

        // Wait for tasks to drain.
        std::thread::sleep(Duration::from_millis(50));
        assert_eq!(counter.load(Ordering::SeqCst), 10);
        d.drain_and_shutdown();
    }

    /// Mt invariant: axiom3_satisfied_via_gamma_epoch.
    /// Install an artefact; verify hits return Cached. Bump epoch
    /// (simulating Γ mutation); verify lookups now miss.
    #[test]
    fn gamma_bump_invalidates_cached_artefacts() {
        let mut i = Interner::new();
        let kind = i.intern("rule_a");
        let d = dispatcher_with_threshold(2);

        // Trigger tier-up, install compiled.
        let counter = Arc::new(AtomicUsize::new(0));
        for _ in 0..2 {
            let c = Arc::clone(&counter);
            d.submit(TypedTask {
                kind,
                deadline: Instant::now() + Duration::from_secs(60),
                class: PriorityClass::BestEffort,
                work: Box::new(move || {
                    c.fetch_add(1, Ordering::SeqCst);
                }),
            });
        }
        d.install_compiled(kind, FakeJit { size: 256 });
        assert!(d.has_fresh_cached(kind));

        // Subsequent submit gets Cached.
        let c = Arc::clone(&counter);
        let o = d.submit(TypedTask {
            kind,
            deadline: Instant::now() + Duration::from_secs(60),
            class: PriorityClass::BestEffort,
            work: Box::new(move || {
                c.fetch_add(1, Ordering::SeqCst);
            }),
        });
        assert!(matches!(o, DispatchOutcome::Cached { .. }));

        // Γ mutates.
        d.invalidate_gamma();

        // Artefact still in cache but stamp is stale ⇒ lookup misses.
        assert!(!d.has_fresh_cached(kind));
        assert!(d.get_compiled(kind).is_none());

        // Subsequent submit gets Queued (not Cached; below threshold
        // again — actually count is 4, threshold was 2, so it's
        // post-tier-up; outcome is Queued since cache is stale and
        // count != threshold).
        let c = Arc::clone(&counter);
        let o = d.submit(TypedTask {
            kind,
            deadline: Instant::now() + Duration::from_secs(60),
            class: PriorityClass::BestEffort,
            work: Box::new(move || {
                c.fetch_add(1, Ordering::SeqCst);
            }),
        });
        match o {
            DispatchOutcome::Queued { .. } => (),
            other => panic!("expected Queued after invalidate, got {:?}", other),
        }

        std::thread::sleep(Duration::from_millis(50));
        d.drain_and_shutdown();
    }

    /// Mt rule: guard_failure_cools_speculation.
    /// After `cooling_threshold` consecutive failures, kind cools:
    /// hot counter reset + cache entry removed.
    #[test]
    fn cool_kind_resets_counter_and_evicts_cached() {
        let mut i = Interner::new();
        let kind = i.intern("flaky_rule");
        let d = dispatcher_with_threshold(5);

        // Pump up hot counter + install a compiled artefact.
        for _ in 0..5 {
            d.hot.record(kind);
        }
        d.install_compiled(kind, FakeJit { size: 256 });
        assert!(d.has_fresh_cached(kind));
        assert_eq!(d.hot.count(kind), 5);

        // Report failures. cooling_threshold = 3.
        let o1 = d.report_guard_failure(kind);
        let o2 = d.report_guard_failure(kind);
        assert!(matches!(o1, GuardFailureOutcome::Counted { .. }));
        assert!(matches!(o2, GuardFailureOutcome::Counted { .. }));

        // Third failure → cool.
        let o3 = d.report_guard_failure(kind);
        match o3 {
            GuardFailureOutcome::Cooled { consecutive, .. } => {
                assert_eq!(consecutive, 3);
            }
            _ => panic!("expected Cooled"),
        }

        // Effects of cooling.
        assert_eq!(
            d.hot.count(kind),
            0,
            "cooled kind's hot counter should be reset"
        );
        assert!(
            !d.has_fresh_cached(kind),
            "cooled kind's compiled artefact should be evicted"
        );

        d.shutdown();
    }

    /// Successful install resets the guard-failure history — a
    /// freshly compiled artefact starts with a clean slate.
    #[test]
    fn install_resets_guard_failure_history() {
        let mut i = Interner::new();
        let kind = i.intern("rule_a");
        let d = dispatcher_with_threshold(5);

        // Compile + accumulate two failures (below cooling threshold).
        d.install_compiled(kind, FakeJit { size: 100 });
        d.report_guard_failure(kind);
        d.report_guard_failure(kind);

        // Re-compile (e.g. recompile with less speculation).
        d.install_compiled(kind, FakeJit { size: 100 });

        // Failure history reset — next failure starts at 1, not 3.
        let o = d.report_guard_failure(kind);
        match o {
            GuardFailureOutcome::Counted { consecutive, .. } => {
                assert_eq!(
                    consecutive, 1,
                    "install should have reset guard failure count"
                );
            }
            _ => panic!("expected Counted (1 of 3), got {:?}", o),
        }

        d.shutdown();
    }

    /// Epoch is shared — bumping via dispatcher.epoch() externally
    /// affects has_fresh_cached. Models the substrate's Γ-mutation
    /// surface bumping the same Epoch instance the dispatcher reads.
    #[test]
    fn shared_epoch_bumps_propagate() {
        let mut i = Interner::new();
        let kind = i.intern("rule_a");
        let d = dispatcher_with_threshold(2);
        d.install_compiled(kind, FakeJit { size: 100 });
        assert!(d.has_fresh_cached(kind));

        // Take a clone of the epoch (e.g. the substrate's Γ mutator
        // would hold this).
        let external_epoch = d.epoch();
        external_epoch.bump();

        assert!(
            !d.has_fresh_cached(kind),
            "bumping shared Epoch externally invalidates dispatcher cache"
        );
        d.shutdown();
    }
}
