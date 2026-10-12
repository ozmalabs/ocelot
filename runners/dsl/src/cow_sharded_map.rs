//! Experimental persistent hash map for high-cardinality graph indexes.
//!
//! A clone shares a root containing a configurable power-of-two number of
//! shard references (64 by default). A branch mutation
//! copies the root pointer array and only the selected shard map. This trades
//! an extra shard lookup/hash for bounded sparse-write copying; it is intended
//! for graph indexes with many independently addressed buckets.

use std::hash::Hash;
use std::sync::Arc;

use rustc_hash::FxHashMap;

#[cfg(any(
    all(feature = "cow_shards_128", feature = "cow_shards_256"),
    all(feature = "cow_shards_128", feature = "cow_shards_512"),
    all(feature = "cow_shards_256", feature = "cow_shards_512")
))]
compile_error!("select only one cow_shards_* feature");

#[cfg(feature = "cow_shards_128")]
const DEFAULT_SHARD_COUNT: usize = 128;
#[cfg(feature = "cow_shards_256")]
const DEFAULT_SHARD_COUNT: usize = 256;
#[cfg(feature = "cow_shards_512")]
const DEFAULT_SHARD_COUNT: usize = 512;
#[cfg(not(any(
    feature = "cow_shards_128",
    feature = "cow_shards_256",
    feature = "cow_shards_512"
)))]
const DEFAULT_SHARD_COUNT: usize = 64;

pub trait CowShardKey {
    fn cow_shard(&self) -> usize;
}

#[derive(Clone)]
pub struct CowShardedMap<K, V, const SHARD_COUNT: usize = DEFAULT_SHARD_COUNT> {
    shards: Arc<Vec<Arc<FxHashMap<K, V>>>>,
    len: usize,
}

impl<K, V, const SHARD_COUNT: usize> Default for CowShardedMap<K, V, SHARD_COUNT> {
    fn default() -> Self {
        assert!(SHARD_COUNT.is_power_of_two(), "CowShardedMap shard count must be a power of two");
        let empty: Arc<FxHashMap<K, V>> = Arc::new(FxHashMap::default());
        Self {
            shards: Arc::new((0..SHARD_COUNT).map(|_| Arc::clone(&empty)).collect()),
            len: 0,
        }
    }
}

impl<K, V, const SHARD_COUNT: usize> CowShardedMap<K, V, SHARD_COUNT>
where
    K: CowShardKey + Eq + Hash + Clone,
    V: Clone,
{
    #[inline]
    fn shard_for(key: &K) -> usize {
        key.cow_shard() & (SHARD_COUNT - 1)
    }

    #[inline]
    pub fn len(&self) -> usize {
        self.len
    }

    #[inline]
    pub fn is_empty(&self) -> bool {
        self.len == 0
    }

    #[inline]
    pub fn get(&self, key: &K) -> Option<&V> {
        self.shards[Self::shard_for(key)].get(key)
    }

    /// Estimate copy work for the first branch-local mutable access to `key`.
    /// The tuple is (root references copied, selected shard entries cloned).
    /// This is a structural estimate, not an allocator-byte measurement.
    #[doc(hidden)]
    pub fn shared_write_copy_estimate(&self, key: &K) -> (usize, usize) {
        let root_shared = Arc::strong_count(&self.shards) > 1;
        let index = Self::shard_for(key);
        let shard_shared = Arc::strong_count(&self.shards[index]) > 1;
        let root_refs = if root_shared { SHARD_COUNT } else { 0 };
        let entries = if root_shared || shard_shared { self.shards[index].len() } else { 0 };
        (root_refs, entries)
    }

    /// Entry counts per shard for workload-distribution and copy-amplification
    /// diagnostics. It intentionally allocates a compact vector of counts.
    #[doc(hidden)]
    pub fn shard_lengths(&self) -> Vec<usize> {
        self.shards.iter().map(|shard| shard.len()).collect()
    }

    #[inline]
    pub fn contains_key(&self, key: &K) -> bool {
        self.get(key).is_some()
    }

    #[inline]
    pub fn get_mut(&mut self, key: &K) -> Option<&mut V> {
        let index = Self::shard_for(key);
        let shards = Arc::make_mut(&mut self.shards);
        Arc::make_mut(&mut shards[index]).get_mut(key)
    }

    pub fn get_or_default_mut(&mut self, key: K) -> &mut V
    where
        V: Default,
    {
        if self.get(&key).is_none() {
            self.insert(key.clone(), V::default());
        }
        self.get_mut(&key).expect("inserted CowShardedMap entry")
    }

    pub fn insert(&mut self, key: K, value: V) -> Option<V> {
        let index = Self::shard_for(&key);
        let shards = Arc::make_mut(&mut self.shards);
        let old = Arc::make_mut(&mut shards[index]).insert(key, value);
        if old.is_none() {
            self.len += 1;
        }
        old
    }

    pub fn remove(&mut self, key: &K) -> Option<V> {
        let index = Self::shard_for(key);
        let shards = Arc::make_mut(&mut self.shards);
        let removed = Arc::make_mut(&mut shards[index]).remove(key);
        if removed.is_some() {
            self.len -= 1;
        }
        removed
    }

    pub fn retain<F>(&mut self, mut keep: F)
    where
        F: FnMut(&K, &mut V) -> bool,
    {
        let shards = Arc::make_mut(&mut self.shards);
        let mut removed = 0usize;
        for shard in shards.iter_mut() {
            let map = Arc::make_mut(shard);
            let before = map.len();
            map.retain(|key, value| keep(key, value));
            removed += before - map.len();
        }
        self.len -= removed;
    }

    pub fn values(&self) -> impl Iterator<Item = &V> {
        self.shards.iter().flat_map(|shard| shard.values())
    }

    pub fn iter(&self) -> impl Iterator<Item = (&K, &V)> {
        self.shards.iter().flat_map(|shard| shard.iter())
    }

    pub fn deep_copy(&self) -> Self {
        let mut copy = Self::default();
        for (key, value) in self.iter() {
            copy.insert(key.clone(), value.clone());
        }
        copy
    }
}
