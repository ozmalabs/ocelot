//! Experimental persistent paged vector for substrate snapshot branches.
//!
//! A fork clones one `Arc` root. A write makes the radix path private and
//! clones only the touched leaf page. This is a storage primitive, not yet a
//! replacement for all graph indexes. `TypedGraph` uses it for node/edge
//! records and the top-level per-node adjacency lists; the hash-based query
//! indexes and most `Substrate` fields still use eager cloning.

use std::sync::Arc;
use std::ops::{Index, IndexMut};

const PAGE_BITS: u32 = 6;
const PAGE_LEN: usize = 1 << PAGE_BITS;
const BRANCH_BITS: u32 = 5;
const BRANCH_LEN: usize = 1 << BRANCH_BITS;
const RADIX_LEVELS: u32 = 6;

#[derive(Clone)]
enum TrieNode<T: Clone> {
    Branch(Box<[Option<Arc<TrieNode<T>>>; BRANCH_LEN]>),
    Leaf(Box<[Option<T>; PAGE_LEN]>),
}

impl<T: Clone> TrieNode<T> {
    fn branch() -> Self {
        Self::Branch(Box::new(std::array::from_fn(|_| None)))
    }

    fn leaf() -> Self {
        Self::Leaf(Box::new(std::array::from_fn(|_| None)))
    }
}

/// Clone-cheap indexed storage with stable positional identity.
///
/// Cloning a vector creates a branch sharing the root. `push` and `get_mut`
/// copy at most one fixed-size page and six small radix nodes when storage is
/// shared. Deletions should be represented in `T` itself (for example,
/// `Option<NodeData>`) so slab positions and IDs remain stable.
#[derive(Clone)]
pub struct CowPagedVec<T: Clone> {
    root: Arc<TrieNode<T>>,
    len: usize,
}

pub struct CowPagedVecIter<'a, T: Clone> {
    vector: &'a CowPagedVec<T>,
    next: usize,
}

impl<'a, T: Clone> Iterator for CowPagedVecIter<'a, T> {
    type Item = &'a T;

    fn next(&mut self) -> Option<Self::Item> {
        let value = self.vector.get(self.next)?;
        self.next += 1;
        Some(value)
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        let remaining = self.vector.len - self.next;
        (remaining, Some(remaining))
    }
}

impl<T: Clone> ExactSizeIterator for CowPagedVecIter<'_, T> {}

impl<'a, T: Clone> IntoIterator for &'a CowPagedVec<T> {
    type Item = &'a T;
    type IntoIter = CowPagedVecIter<'a, T>;

    fn into_iter(self) -> Self::IntoIter { self.iter() }
}

impl<T: Clone> Index<usize> for CowPagedVec<T> {
    type Output = T;

    fn index(&self, index: usize) -> &Self::Output {
        self.get(index).expect("CowPagedVec index out of bounds or vacant")
    }
}

impl<T: Clone> IndexMut<usize> for CowPagedVec<T> {
    fn index_mut(&mut self, index: usize) -> &mut Self::Output {
        self.get_mut(index).expect("CowPagedVec index out of bounds or vacant")
    }
}

impl<T: Clone> Default for CowPagedVec<T> {
    fn default() -> Self {
        Self::new()
    }
}

impl<T: Clone> CowPagedVec<T> {
    pub fn new() -> Self {
        Self {
            root: Arc::new(TrieNode::branch()),
            len: 0,
        }
    }

    pub fn from_vec(values: Vec<T>) -> Self {
        let mut result = Self::new();
        for value in values {
            result.push(value);
        }
        result
    }

    #[inline]
    pub fn len(&self) -> usize {
        self.len
    }

    #[inline]
    pub fn is_empty(&self) -> bool {
        self.len == 0
    }

    pub fn iter(&self) -> CowPagedVecIter<'_, T> {
        CowPagedVecIter { vector: self, next: 0 }
    }

    #[inline]
    pub fn fork(&self) -> Self {
        self.clone()
    }

    /// Materialize every slot into a separate radix tree as an eager-copy
    /// control. The shared-root clone remains the branch fast path.
    pub fn deep_copy(&self) -> Self {
        Self::from_vec(self.iter().cloned().collect())
    }

    pub fn get(&self, index: usize) -> Option<&T> {
        if index >= self.len || index > u32::MAX as usize {
            return None;
        }
        let page = (index as u32) >> PAGE_BITS;
        let offset = index & (PAGE_LEN - 1);
        Self::get_page(&self.root, page, RADIX_LEVELS)?.get(offset)?.as_ref()
    }

    pub fn get_mut(&mut self, index: usize) -> Option<&mut T> {
        if index >= self.len || index > u32::MAX as usize {
            return None;
        }
        let page = (index as u32) >> PAGE_BITS;
        let offset = index & (PAGE_LEN - 1);
        Self::get_page_mut(&mut self.root, page, RADIX_LEVELS)?
            .get_mut(offset)?
            .as_mut()
    }

    pub fn push(&mut self, value: T) {
        assert!(self.len <= u32::MAX as usize, "CowPagedVec index space exhausted");
        let index = self.len;
        let page = (index as u32) >> PAGE_BITS;
        let offset = index & (PAGE_LEN - 1);
        Self::set_page(&mut self.root, page, RADIX_LEVELS, offset, value);
        self.len += 1;
    }

    /// Replace one existing slot, returning its former value.
    pub fn set(&mut self, index: usize, value: T) -> Option<T> {
        if index >= self.len || index > u32::MAX as usize {
            return None;
        }
        let slot = Self::get_page_mut(
            &mut self.root,
            (index as u32) >> PAGE_BITS,
            RADIX_LEVELS,
        )?
        .get_mut(index & (PAGE_LEN - 1))?;
        slot.replace(value)
    }

    /// True when the two vectors still refer to the same allocated leaf page.
    /// This exposes sharing for allocation probes without exposing page layout.
    pub fn shares_page_with(&self, other: &Self, index: usize) -> bool {
        if index >= self.len || index >= other.len || index > u32::MAX as usize {
            return false;
        }
        let page = (index as u32) >> PAGE_BITS;
        match (
            Self::page_arc(&self.root, page, RADIX_LEVELS),
            Self::page_arc(&other.root, page, RADIX_LEVELS),
        ) {
            (Some(a), Some(b)) => Arc::ptr_eq(a, b),
            _ => false,
        }
    }

    fn page_arc(node: &Arc<TrieNode<T>>, page: u32, levels: u32) -> Option<&Arc<TrieNode<T>>> {
        if levels == 0 {
            return None;
        }
        let shift = (levels - 1) * BRANCH_BITS;
        let slot = ((page >> shift) as usize) & (BRANCH_LEN - 1);
        match node.as_ref() {
            TrieNode::Branch(children) => {
                let child = children[slot].as_ref()?;
                if levels == 1 {
                    Some(child)
                } else {
                    Self::page_arc(child, page, levels - 1)
                }
            }
            TrieNode::Leaf(_) => None,
        }
    }

    fn get_page(
        node: &Arc<TrieNode<T>>,
        page: u32,
        levels: u32,
    ) -> Option<&[Option<T>; PAGE_LEN]> {
        let leaf = Self::page_arc(node, page, levels)?;
        match leaf.as_ref() {
            TrieNode::Leaf(values) => Some(values),
            TrieNode::Branch(_) => None,
        }
    }

    fn get_page_mut(
        node: &mut Arc<TrieNode<T>>,
        page: u32,
        levels: u32,
    ) -> Option<&mut [Option<T>; PAGE_LEN]> {
        if levels == 0 {
            return None;
        }
        let shift = (levels - 1) * BRANCH_BITS;
        let slot = ((page >> shift) as usize) & (BRANCH_LEN - 1);
        match Arc::make_mut(node) {
            TrieNode::Branch(children) => {
                let child = children[slot].as_mut()?;
                if levels == 1 {
                    match Arc::make_mut(child) {
                        TrieNode::Leaf(values) => Some(values),
                        TrieNode::Branch(_) => None,
                    }
                } else {
                    Self::get_page_mut(child, page, levels - 1)
                }
            }
            TrieNode::Leaf(_) => None,
        }
    }

    fn set_page(
        node: &mut Arc<TrieNode<T>>,
        page: u32,
        levels: u32,
        offset: usize,
        value: T,
    ) {
        let shift = (levels - 1) * BRANCH_BITS;
        let slot = ((page >> shift) as usize) & (BRANCH_LEN - 1);
        let TrieNode::Branch(children) = Arc::make_mut(node) else {
            unreachable!("radix path ended before leaf")
        };
        if levels == 1 {
            let leaf = children[slot].get_or_insert_with(|| Arc::new(TrieNode::leaf()));
            let TrieNode::Leaf(values) = Arc::make_mut(leaf) else {
                unreachable!("radix leaf has branch node")
            };
            debug_assert!(values[offset].is_none());
            values[offset] = Some(value);
            return;
        }
        let child = children[slot].get_or_insert_with(|| Arc::new(TrieNode::branch()));
        Self::set_page(child, page, levels - 1, offset, value);
    }
}
