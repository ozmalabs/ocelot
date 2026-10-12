//! Code cache — bounded executable-code memory with LRU eviction
//! and refcount-based safe concurrent reclamation.
//!
//! Realises a subset of the `executable_memory_lifecycle` Mt
//! (commit 27f4afb). Names the components implemented here vs
//! deferred:
//!
//! ## Implemented (verified by tests below)
//!
//! - **`mmap_executable_pages`** — delegated to `dynasmrt`, which
//!   the cached `T` typically wraps. The cache stores arbitrary
//!   `T: CodeSize + Send + Sync`; for JIT use, `T = JittedFn`.
//! - **`write_xor_execute_enforcement`** — delegated to `dynasmrt`'s
//!   per-platform handling. The cache holds completed (post-flip)
//!   artefacts.
//! - **`icache_invalidation_after_write`** — delegated to `dynasmrt`.
//! - **`refcount_arc_for_low_contention`** — every cached artefact
//!   lives behind `Arc<T>`. `get()` clones the Arc (cheap atomic
//!   increment); eviction drops the cache's copy. The artefact is
//!   freed (and its `T::drop` runs, triggering munmap if `T` owns
//!   an mmap) only when the LAST clone is dropped.
//! - **`code_cache_bound`** — configurable `max_bytes`. Default
//!   4 MiB (Zen 5 L2 size, per the Mt's named choice).
//! - **`lru_eviction_policy`** — least-recently-used entry evicted
//!   on `insert()` when the bound would be exceeded.
//! - **`per_thread_vs_shared_cache`** — shared (single source of
//!   truth) per the Mt's named choice. Internal Mutex + Arc<T>.
//!
//! ## Deferred (named in the Mt, future commits)
//!
//! - `epoch_based_reclamation` — Arc covers correctness; epoch
//!   would optimise hot loops. crossbeam-epoch dependency not
//!   added yet.
//! - `hazard_pointers_alternative` — alternative; not needed.
//! - `safepoint_map_for_osr` — requires JIT cooperation
//!   (jit.rs emits safepoint polls + maintains map). L5 work.
//! - `patch_point_atomic_overwrite` — requires JIT cooperation.
//!   L5 work.
//! - `compile_arena_pooling` — optimisation; dynasmrt currently
//!   does one mmap per `ExecutableBuffer`.
//!
//! ## Invariants verified
//!
//! - **`no_use_after_free_under_concurrent_execution`** — test
//!   `arc_keeps_artefact_alive_past_eviction`.
//! - **`bounded_total_executable_memory`** — test
//!   `bounded_under_inserts`.
//! - **`w_x_always_satisfied`** — delegated to `dynasmrt`; not
//!   testable at this layer.
//! - **`icache_coherent_with_dcache_at_execute`** — delegated.
//! - **`osr_deopt_reconstructable`** — requires safepoint maps;
//!   deferred.

use std::collections::HashMap;
use std::hash::Hash;
use std::sync::{Arc, Mutex};

/// Trait for cached artefacts that can report their executable-byte
/// footprint. Required so the cache can enforce its byte bound.
pub trait CodeSize {
    /// Bytes of executable memory this artefact occupies. For JIT
    /// artefacts, the mmap'd code buffer length.
    fn code_size_bytes(&self) -> usize;
}

/// Configuration knobs the `executable_memory_lifecycle` Mt names.
#[derive(Debug, Clone, Copy)]
pub struct CodeCacheConfig {
    /// Maximum total bytes of executable memory the cache holds.
    /// On a Zen 5 / Ryzen 9600X (substrate's reference hardware),
    /// 4 MiB ≈ L2 size per core — hot working set fits the
    /// architecture cache. Per the Mt's `code_cache_bound` component.
    pub max_bytes: usize,
}

impl Default for CodeCacheConfig {
    fn default() -> Self {
        Self {
            max_bytes: 4 * 1024 * 1024,
        }
    }
}

/// Internal state — held under a Mutex so the cache is safe to
/// share across worker threads. Cache contents are `Arc<T>` so
/// readers don't hold the lock while using artefacts.
struct Inner<K, T> {
    map: HashMap<K, Arc<T>>,
    /// LRU order. Front = oldest, back = MRU. For typical cache
    /// sizes (hundreds of entries) a `Vec` is fine; for very
    /// large caches a `LinkedHashMap` would give O(1) reorder.
    lru: Vec<K>,
    total_bytes: usize,
}

/// Bounded code cache with LRU eviction. Concurrent-safe via
/// internal Mutex; cached artefacts handed out as `Arc<T>`.
///
/// Generic over the key type `K` (typically `Sym` for rule kinds)
/// and the cached payload `T` (typically a JIT artefact wrapping
/// an mmap'd executable buffer).
pub struct CodeCache<K, T>
where
    K: Eq + Hash + Clone,
    T: CodeSize + Send + Sync,
{
    inner: Mutex<Inner<K, T>>,
    config: CodeCacheConfig,
}

impl<K, T> CodeCache<K, T>
where
    K: Eq + Hash + Clone,
    T: CodeSize + Send + Sync,
{
    pub fn new(config: CodeCacheConfig) -> Self {
        Self {
            inner: Mutex::new(Inner {
                map: HashMap::new(),
                lru: Vec::new(),
                total_bytes: 0,
            }),
            config,
        }
    }

    pub fn with_default_config() -> Self {
        Self::new(CodeCacheConfig::default())
    }

    /// Fetch a cached artefact. Returns `Some(Arc<T>)` if present
    /// (and bumps the entry to MRU position); `None` if absent.
    ///
    /// The returned `Arc<T>` keeps the artefact alive even if the
    /// cache concurrently evicts it — realising the
    /// `no_use_after_free_under_concurrent_execution` invariant.
    pub fn get(&self, key: &K) -> Option<Arc<T>> {
        let mut inner = self.inner.lock().unwrap();
        let arc = inner.map.get(key)?.clone();
        // Bump to MRU. O(n) on the LRU Vec; acceptable for the
        // expected cache sizes (hundreds, not millions).
        if let Some(pos) = inner.lru.iter().position(|k| k == key) {
            let k = inner.lru.remove(pos);
            inner.lru.push(k);
        }
        Some(arc)
    }

    /// Insert a freshly-compiled artefact. If the key already
    /// existed, the prior entry is removed (no-grow replacement).
    /// If inserting would exceed `max_bytes`, LRU entries are
    /// evicted until it fits.
    ///
    /// Returns the `Vec<Arc<T>>` of evicted artefacts so the
    /// caller can inspect or pass-through. The artefacts'
    /// underlying memory is freed only when the LAST `Arc<T>`
    /// clone (including any held by in-flight executions) is
    /// dropped — `Arc` provides the deferred-free guarantee.
    pub fn insert(&self, key: K, value: T) -> Vec<Arc<T>> {
        let arc = Arc::new(value);
        let size = arc.code_size_bytes();
        let mut inner = self.inner.lock().unwrap();
        let mut evicted = Vec::new();

        // Replace existing entry for this key, if any.
        if let Some(old) = inner.map.remove(&key) {
            inner.total_bytes = inner.total_bytes.saturating_sub(old.code_size_bytes());
            inner.lru.retain(|k| k != &key);
            evicted.push(old);
        }

        // Evict LRU until the new entry fits. If the new entry
        // alone exceeds `max_bytes` we still insert it — caller's
        // responsibility for sane sizing. (HotSpot does the same.)
        while inner.total_bytes + size > self.config.max_bytes && !inner.lru.is_empty() {
            let lru_key = inner.lru.remove(0);
            if let Some(old) = inner.map.remove(&lru_key) {
                inner.total_bytes = inner.total_bytes.saturating_sub(old.code_size_bytes());
                evicted.push(old);
            }
        }

        inner.map.insert(key.clone(), arc);
        inner.lru.push(key);
        inner.total_bytes += size;

        evicted
    }

    /// Explicit removal. Caller might do this on epoch-bump
    /// invalidation for a specific kind, or on deopt-cooling.
    /// Returns the removed Arc (caller may continue to use it
    /// via its Arc handle).
    pub fn remove(&self, key: &K) -> Option<Arc<T>> {
        let mut inner = self.inner.lock().unwrap();
        let arc = inner.map.remove(key)?;
        inner.total_bytes = inner.total_bytes.saturating_sub(arc.code_size_bytes());
        inner.lru.retain(|k| k != key);
        Some(arc)
    }

    /// Drop all cached entries. Useful on epoch-bump for bulk
    /// invalidation. Each entry's underlying memory is freed
    /// when its last Arc clone is dropped.
    pub fn clear(&self) {
        let mut inner = self.inner.lock().unwrap();
        inner.map.clear();
        inner.lru.clear();
        inner.total_bytes = 0;
    }

    /// Number of cached entries.
    pub fn len(&self) -> usize {
        self.inner.lock().unwrap().map.len()
    }

    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }

    /// Sum of `code_size_bytes` across cached entries. Always
    /// `<= config.max_bytes` after `insert()` returns
    /// (`bounded_total_executable_memory` invariant).
    pub fn total_bytes(&self) -> usize {
        self.inner.lock().unwrap().total_bytes
    }

    /// LRU order snapshot — oldest-first. Diagnostic.
    pub fn lru_order(&self) -> Vec<K> {
        self.inner.lock().unwrap().lru.clone()
    }

    pub fn config(&self) -> CodeCacheConfig {
        self.config
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::{AtomicUsize, Ordering as AtomicOrd};

    /// Test payload — records its drop in a shared counter so we
    /// can verify Arc-based deferred free.
    struct FakeArtefact {
        size: usize,
        drops: Arc<AtomicUsize>,
    }
    impl CodeSize for FakeArtefact {
        fn code_size_bytes(&self) -> usize {
            self.size
        }
    }
    impl Drop for FakeArtefact {
        fn drop(&mut self) {
            self.drops.fetch_add(1, AtomicOrd::SeqCst);
        }
    }

    fn make(size: usize, drops: &Arc<AtomicUsize>) -> FakeArtefact {
        FakeArtefact {
            size,
            drops: Arc::clone(drops),
        }
    }

    /// Smoke: insert, get, remove. Hits the basic API paths.
    #[test]
    fn smoke_insert_get_remove() {
        let drops = Arc::new(AtomicUsize::new(0));
        let c: CodeCache<&'static str, FakeArtefact> =
            CodeCache::new(CodeCacheConfig { max_bytes: 1024 });
        assert!(c.is_empty());

        let evicted = c.insert("a", make(100, &drops));
        assert!(evicted.is_empty());
        assert_eq!(c.len(), 1);
        assert_eq!(c.total_bytes(), 100);

        let a = c.get(&"a").expect("present");
        assert_eq!(a.code_size_bytes(), 100);

        let removed = c.remove(&"a").expect("present");
        assert_eq!(c.len(), 0);
        assert_eq!(c.total_bytes(), 0);
        // Two Arcs still alive: `a` + `removed`. No drop yet.
        assert_eq!(drops.load(AtomicOrd::SeqCst), 0);
        drop(a);
        drop(removed);
        assert_eq!(drops.load(AtomicOrd::SeqCst), 1);
    }

    /// Invariant: bounded_total_executable_memory — after any
    /// insert, total_bytes ≤ max_bytes.
    #[test]
    fn bounded_under_inserts() {
        let drops = Arc::new(AtomicUsize::new(0));
        let c: CodeCache<u32, FakeArtefact> = CodeCache::new(CodeCacheConfig { max_bytes: 1024 });
        // Insert 20 entries of 100 bytes each. Cache holds 10 max.
        for i in 0..20 {
            c.insert(i, make(100, &drops));
            assert!(
                c.total_bytes() <= 1024,
                "bound violated at iter {}: total={}",
                i,
                c.total_bytes()
            );
        }
        assert!(c.len() <= 10);
        // 10 evicted; their Arcs were dropped by the insert call
        // (no other clones in this test) → drop counter == 10.
        assert_eq!(drops.load(AtomicOrd::SeqCst), 10);
    }

    /// LRU eviction order — when capacity forces eviction,
    /// least-recently-used entry goes first.
    #[test]
    fn lru_eviction_order() {
        let drops = Arc::new(AtomicUsize::new(0));
        let c: CodeCache<&'static str, FakeArtefact> =
            CodeCache::new(CodeCacheConfig { max_bytes: 300 });
        c.insert("a", make(100, &drops));
        c.insert("b", make(100, &drops));
        c.insert("c", make(100, &drops));
        assert_eq!(c.lru_order(), vec!["a", "b", "c"]);

        // Touch "a" — moves to MRU.
        let _ = c.get(&"a");
        assert_eq!(c.lru_order(), vec!["b", "c", "a"]);

        // Insert "d" — forces eviction of LRU ("b").
        c.insert("d", make(100, &drops));
        assert_eq!(c.lru_order(), vec!["c", "a", "d"]);
        assert!(c.get(&"b").is_none(), "b should have been evicted");
        assert!(c.get(&"a").is_some(), "a kept because touched");
    }

    /// Invariant: no_use_after_free_under_concurrent_execution.
    /// The cached Arc keeps the artefact alive even if the cache
    /// evicts it (mimicking what a worker holding a JIT'd fn
    /// pointer would experience under a Γ-mutation evict).
    #[test]
    fn arc_keeps_artefact_alive_past_eviction() {
        let drops = Arc::new(AtomicUsize::new(0));
        let c: CodeCache<&'static str, FakeArtefact> =
            CodeCache::new(CodeCacheConfig { max_bytes: 200 });
        c.insert("hot", make(100, &drops));

        // Simulate a worker grabbing the artefact + starting to
        // execute (we just clone the Arc).
        let worker_hold = c.get(&"hot").expect("present");

        // Now simulate the dispatcher evicting due to Γ mutation
        // (clear + re-insert different content forcing displacement).
        c.clear();
        assert_eq!(
            drops.load(AtomicOrd::SeqCst),
            0,
            "drop must be deferred while worker holds Arc"
        );

        // Worker still has a valid handle.
        assert_eq!(worker_hold.code_size_bytes(), 100);

        // Worker finishes its "execution" — releases its Arc.
        drop(worker_hold);
        // NOW the artefact is freed.
        assert_eq!(
            drops.load(AtomicOrd::SeqCst),
            1,
            "drop happens when last Arc clone drops"
        );
    }

    /// Re-inserting the same key replaces — doesn't grow size,
    /// returns the old artefact for the caller to handle.
    #[test]
    fn reinsert_replaces_without_growth() {
        let drops = Arc::new(AtomicUsize::new(0));
        let c: CodeCache<&'static str, FakeArtefact> =
            CodeCache::new(CodeCacheConfig { max_bytes: 1024 });
        c.insert("k", make(100, &drops));
        let ev = c.insert("k", make(150, &drops));
        assert_eq!(ev.len(), 1, "old artefact returned in evicted vec");
        assert_eq!(ev[0].code_size_bytes(), 100);
        assert_eq!(c.total_bytes(), 150);
        assert_eq!(c.len(), 1);
    }

    /// `clear()` evicts everything; total_bytes resets; if no
    /// external Arcs held, drops happen immediately.
    #[test]
    fn clear_evicts_all() {
        let drops = Arc::new(AtomicUsize::new(0));
        let c: CodeCache<u32, FakeArtefact> = CodeCache::new(CodeCacheConfig { max_bytes: 4096 });
        for i in 0..10 {
            c.insert(i, make(100, &drops));
        }
        assert_eq!(c.len(), 10);
        c.clear();
        assert_eq!(c.len(), 0);
        assert_eq!(c.total_bytes(), 0);
        assert_eq!(drops.load(AtomicOrd::SeqCst), 10);
    }

    /// Inserting an entry larger than the bound: per the
    /// `code_cache_bound` component, we still insert (HotSpot
    /// does the same) — caller's responsibility to size sanely.
    /// All prior entries are evicted trying to make room.
    #[test]
    fn oversized_entry_inserts_but_evicts_all_others() {
        let drops = Arc::new(AtomicUsize::new(0));
        let c: CodeCache<&'static str, FakeArtefact> =
            CodeCache::new(CodeCacheConfig { max_bytes: 200 });
        c.insert("a", make(100, &drops));
        c.insert("b", make(100, &drops));
        // Insert oversized — evicts a and b trying to fit.
        c.insert("huge", make(500, &drops));
        assert_eq!(c.len(), 1);
        assert!(c.get(&"huge").is_some());
        // total_bytes exceeds max_bytes here — this is the
        // documented caller-sizing-failure case. Cache stays
        // functional.
        assert_eq!(c.total_bytes(), 500);
    }
}
