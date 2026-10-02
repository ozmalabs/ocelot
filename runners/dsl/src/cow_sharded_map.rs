//! Experimental persistent hash map for high-cardinality graph indexes.
//!
//! A clone shares a root containing 64 shard references. A branch mutation
//! copies the root pointer array and only the selected shard map. This trades
//! an extra shard lookup/hash for bounded sparse-write copying; it is intended
//! for graph indexes with many independently addressed buckets.

use std::hash::Hash;
use std::sync::Arc;

use rustc_hash::FxHashMap;

const SHARD_COUNT: usize = 64;
const SHARD_MASK: usize = SHARD_COUNT - 1;

pub trait CowShardKey {
    fn cow_shard(&self) -> usize;
}

#[derive(Clone)]
pub struct CowShardedMap<K, V> {
    shards: Arc<Vec<Arc<FxHashMap<K, V>>>>,
    len: usize,
}

impl<K, V> Default for CowShardedMap<K, V> {
    fn default() -> Self {
        let empty: Arc<FxHashMap<K, V>> = Arc::new(FxHashMap::default());
        Self {
            shards: Arc::new((0..SHARD_COUNT).map(|_| Arc::clone(&empty)).collect()),
            len: 0,
        }
    }
}

impl<K, V> CowShardedMap<K, V>
where
    K: CowShardKey + Eq + Hash + Clone,
    V: Clone,
{
    #[inline]
    fn shard_for(key: &K) -> usize {
        key.cow_shard() & SHARD_MASK
    }

    #[inline]
    pub fn len(&self) -> usize { self.len }

    #[inline]
    pub fn is_empty(&self) -> bool { self.len == 0 }

    #[inline]
    pub fn get(&self, key: &K) -> Option<&V> {
        self.shards[Self::shard_for(key)].get(key)
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
        if old.is_none() { self.len += 1; }
        old
    }

    pub fn remove(&mut self, key: &K) -> Option<V> {
        let index = Self::shard_for(key);
        let shards = Arc::make_mut(&mut self.shards);
        let removed = Arc::make_mut(&mut shards[index]).remove(key);
        if removed.is_some() { self.len -= 1; }
        removed
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
