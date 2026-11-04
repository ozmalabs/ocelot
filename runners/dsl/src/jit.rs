//! x86_64 JIT for kernel Term-trees: arithmetic + comparison + control
//! flow + graph access (TypeOf, Attr, Neighbours-count).
//!
//! Compiles a Term-tree to native x86_64 code at runtime. Produces a
//! `JittedFn` that owns an executable buffer and exposes `call_with_ctx`
//! / `call_pure` methods.
//!
//! **Calling convention** (SysV-64):
//! - `rdi` = `*const JitCtx` (or null for pure-arithmetic call sites)
//! - `rsi`, `rdx`, `rcx`, `r8`, `r9` = up to 5 i64 args (variable slots)
//! - `rax` = i64 return
//!
//! **Frame layout** (post-prologue):
//! - `[rbp-8]`  : ctx pointer (saved from rdi)
//! - `[rbp-16..-56]` : 5 arg slots (saved from rsi..r9)
//! - `[rbp-64..-320]`: temp slots, indexed by emit depth (32 levels)
//!
//! **Coverage** (i64-only):
//! - `Lit(Int)`, `Lit(Bool)` (Bool encoded as 0/1)
//! - `Var(name)` — name→arg-index map supplied by caller
//! - Arithmetic: `Plus` (2-ary), `Minus`, `Times` (2-ary), `Neg`, `Abs`
//! - Comparison: `Lt`, `Lte`, `Gt`, `Gte`, `Eq` (return 0/1)
//! - Boolean: `And`, `Or`, `Not` (return 0/1, short-circuit)
//! - Control: `IfThenElse`
//! - **Graph access** (require non-null ctx):
//!   - `TypeOf(Var)` — returns the node's type Sym as i64
//!   - `Attr(Var, key)` — returns i64 attr value (0 if absent / non-int)
//!   - `Count(Neighbours(Var, edge_type))` — returns count as i64
//!     (recognised as a fused pattern; non-fused Neighbours-with-Filter
//!      still falls through to the interpreter)
//!
//! Safety: the executable buffer is owned by `JittedFn`; calling
//! `call_*` transmutes the buffer pointer to a function pointer — sound
//! because the buffer's lifetime is tied to the `JittedFn`. Once the
//! `JittedFn` drops, the mmap pages are unmapped. The ctx pointer
//! passed to `call_with_ctx` must remain valid for the duration of the
//! call; the JIT'd code only dereferences it when the Term-tree uses
//! graph access (which the caller can determine via `needs_ctx`).

use crate::graph::{NodeID, TypedGraph};
use crate::sym::Sym;
use crate::term::{TermArena, TermIdx, TermNode};
use crate::value::Value;
use dynasm::dynasm;
use dynasmrt::{AssemblyOffset, DynasmApi, DynasmLabelApi, ExecutableBuffer};
use rustc_hash::FxHashMap;

/// Runtime context passed to JIT'd code as `rdi`. The thunks for graph
/// access (TypeOf, Attr, neighbour-count) dereference this to look up
/// graph state. The `graph` field is a raw pointer because we want to
/// allow `JitCtx` to be constructed without forcing a lifetime down the
/// JIT API; callers must ensure validity for the call duration.
#[repr(C)]
pub struct JitCtx {
    pub graph: *const TypedGraph,
}

impl JitCtx {
    /// Construct from a borrowed `TypedGraph`. Caller's responsibility
    /// to ensure the ctx isn't outlived by the JIT call.
    pub fn from_graph(g: &TypedGraph) -> Self {
        JitCtx {
            graph: g as *const TypedGraph,
        }
    }
}

/// Owns an executable buffer holding the JIT'd code for one Term-tree.
pub struct JittedFn {
    buf: ExecutableBuffer,
    entry: AssemblyOffset,
    arity: u32,
    needs_ctx: bool,
}

/// A JIT'd where-clause + the var order the matcher extracts args in.
/// `var_order[i]` is the Sym of the i-th positional argument the JIT
/// expects; the matcher resolves each Sym to its bound `NodeID.0` and
/// passes them in order to `jit.call_with_ctx`.
pub struct CompiledWhere {
    pub jit: JittedFn,
    pub var_order: Vec<Sym>,
}

impl CompiledWhere {
    /// Try to compile the where-clause of a rule. Returns `Some` if the
    /// JIT can handle every Term in the tree; `None` if any unsupported
    /// variant is reached (interpreter handles those).
    pub fn try_compile(
        arena: &TermArena,
        where_idx: TermIdx,
        binding_vars: &[Sym],
    ) -> Option<CompiledWhere> {
        if binding_vars.len() > 5 {
            // Beyond what our 5-arg SysV register layout handles.
            return None;
        }
        // Machine arithmetic wraps; Rust integer operators panic on overflow
        // in debug builds. Preserve interpreter behavior for constant cases.
        let mut overflow_budget = MAX_NODES;
        if known_overflow(arena, where_idx, 0, &mut overflow_budget) {
            return None;
        }
        let mut attr_budget = MAX_NODES;
        if subtree_has_attr(arena, where_idx, 0, &mut attr_budget)? {
            // Dynamic node attributes may be floats, nodes, strings, collections,
            // or missing (`Value::None`). Let the interpreter handle any rule
            // `where` clause that reads `Attr` so numeric coercion, truthiness,
            // and fallback-trace accounting remain exact.
            return None;
        }
        let var_indices: FxHashMap<Sym, u32> = binding_vars
            .iter()
            .enumerate()
            .map(|(i, s)| (*s, i as u32))
            .collect();
        let mut kind_budget = MAX_NODES;
        let root_kind = infer_kind(arena, where_idx, &var_indices, true, 0, &mut kind_budget)?;
        if !root_kind.is_condition_compatible() {
            return None;
        }
        let jit = compile_internal(arena, where_idx, &var_indices, true)?;
        Some(CompiledWhere {
            jit,
            var_order: binding_vars.to_vec(),
        })
    }
}

impl JittedFn {
    /// Call without graph context. Asserts the Term-tree didn't compile
    /// any graph-access ops (panics otherwise — would dereference a
    /// null pointer at runtime).
    pub fn call_pure(&self, args: &[i64]) -> i64 {
        assert!(
            !self.needs_ctx,
            "JittedFn needs ctx; use call_with_ctx instead"
        );
        self.call_with_ctx_raw(std::ptr::null(), args)
    }

    /// Call with graph context. `ctx` must remain valid for the duration
    /// of the call.
    pub fn call_with_ctx(&self, ctx: &JitCtx, args: &[i64]) -> i64 {
        self.call_with_ctx_raw(ctx as *const JitCtx, args)
    }

    fn call_with_ctx_raw(&self, ctx: *const JitCtx, args: &[i64]) -> i64 {
        assert!(
            args.len() <= 5,
            "JIT supports up to 5 var args; got {}",
            args.len()
        );
        let mut padded = [0i64; 5];
        for (i, v) in args.iter().enumerate() {
            padded[i] = *v;
        }
        let ptr = self.buf.ptr(self.entry);
        // Safety: buffer alive for `&self`'s lifetime; bytes produced by
        // dynasm-rs are valid x86_64; signature matches our emit
        // convention (extern "sysv64" with one ctx ptr + five i64s).
        let f: extern "sysv64" fn(*const JitCtx, i64, i64, i64, i64, i64) -> i64 =
            unsafe { std::mem::transmute(ptr) };
        f(ctx, padded[0], padded[1], padded[2], padded[3], padded[4])
    }

    pub fn arity(&self) -> u32 {
        self.arity
    }
    pub fn code_len(&self) -> usize {
        self.buf.len()
    }
    pub fn needs_ctx(&self) -> bool {
        self.needs_ctx
    }
}

// Satisfy the code_cache::CodeSize trait so `JittedFn` can be a
// cached payload in `CodeCache<Sym, EpochStamped<JittedFn>>`.
impl crate::code_cache::CodeSize for JittedFn {
    fn code_size_bytes(&self) -> usize {
        self.buf.len()
    }
}

// Safety: JittedFn's executable buffer (dynasmrt::ExecutableBuffer)
// owns mmap'd pages that are immutable after compile. `call_pure` /
// `call_with_ctx` only read the buffer (via fn-pointer transmute);
// no mutable state is shared across threads. For `call_with_ctx`,
// thread-safety with respect to the passed-in TypedGraph is the
// caller's responsibility, same as the single-threaded version.
unsafe impl Send for JittedFn {}
unsafe impl Sync for JittedFn {}

/// Compile a Term-tree to native code. Returns `None` if the tree
/// references variants the JIT doesn't yet handle.
///
/// `var_indices` maps each `Var(name)` to an arg position (0..5).
pub fn compile(
    arena: &TermArena,
    root: TermIdx,
    var_indices: &FxHashMap<Sym, u32>,
) -> Option<JittedFn> {
    compile_internal(arena, root, var_indices, false)
}

fn compile_internal(
    arena: &TermArena,
    root: TermIdx,
    var_indices: &FxHashMap<Sym, u32>,
    var_is_node: bool,
) -> Option<JittedFn> {
    let mut kind_budget = MAX_NODES;
    infer_kind(arena, root, var_indices, var_is_node, 0, &mut kind_budget)?;

    let mut ctx_budget = MAX_NODES;
    let needs_ctx = scan_needs_ctx(arena, root, 0, &mut ctx_budget)?;

    let mut ops = dynasmrt::x64::Assembler::new().ok()?;
    let entry = ops.offset();

    // Frame-pointer prologue. Reserve 320 bytes:
    //   8   ctx slot     ([rbp-8])
    //   40  5 arg slots  ([rbp-16] .. [rbp-56])
    //   8   alignment padding to keep rsp 16-aligned across calls
    //   256 32 temp slots ([rbp-72] .. [rbp-320])
    // sub rsp, 320 keeps rsp 16-aligned (pushed rbp = 8; sub 320 = 0 mod 16).
    dynasm!(ops
        ; .arch x64
        ; push rbp
        ; mov rbp, rsp
        ; sub rsp, 320
        ; mov [rbp - 8], rdi
        ; mov [rbp - 16], rsi
        ; mov [rbp - 24], rdx
        ; mov [rbp - 32], rcx
        ; mov [rbp - 40], r8
        ; mov [rbp - 48], r9
    );

    let mut emit_budget = MAX_NODES;
    emit_term(&mut ops, arena, root, var_indices, 0, &mut emit_budget)?;

    dynasm!(ops
        ; .arch x64
        ; mov rsp, rbp
        ; pop rbp
        ; ret
    );

    let buf = ops.finalize().ok()?;
    Some(JittedFn {
        buf,
        entry,
        arity: var_indices.len() as u32,
        needs_ctx,
    })
}

/// Static value-kind taxonomy for the untagged i64 JIT.
///
/// Because the JIT represents every value in a raw 64-bit register, static
/// kind verification ensures:
/// 1. `Value::Node(NodeID(0))` (which is truthy in the interpreter) is never
///    tested as a boolean condition (`0i64` would be falsy) or compared/combined
///    with `Int`/`Bool`/`Str`.
/// 2. `Value::Str(Sym)` (from `TypeOf` or `Lit(Str)`) is only compared via `Eq`
///    against another `Str`, never ordered with `Lt`/`Lte`/`Gt`/`Gte` (which in
///    the interpreter uses lexicographic string order, not raw `Sym.0` order)
///    or tested as a boolean condition.
/// 3. `Eq` never compares incompatible value domains (`Int(1) == Bool(true)` or
///    `Node(NodeID(0)) == Int(0)`).
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum ValKind {
    Int,
    Bool,
    Str,
    Node,
    /// Unconstrained variable in standalone `compile` (may be passed as `Int`
    /// or `NodeID` by direct callers). In `CompiledWhere::try_compile`, pattern
    /// variables are always bound to graph nodes (`ValKind::Node`).
    VarAny,
}

impl ValKind {
    #[inline]
    fn is_int(self) -> bool {
        matches!(self, ValKind::Int | ValKind::VarAny)
    }

    #[inline]
    fn is_node(self) -> bool {
        matches!(self, ValKind::Node | ValKind::VarAny)
    }

    #[inline]
    fn is_condition_compatible(self) -> bool {
        matches!(self, ValKind::Int | ValKind::Bool | ValKind::VarAny)
    }

    #[inline]
    fn eq_compatible(self, other: Self) -> bool {
        match (self, other) {
            (ValKind::Int | ValKind::VarAny, ValKind::Int | ValKind::VarAny) => true,
            (ValKind::Bool, ValKind::Bool) => true,
            (ValKind::Str, ValKind::Str) => true,
            (ValKind::Node | ValKind::VarAny, ValKind::Node | ValKind::VarAny) => true,
            _ => false,
        }
    }

    #[inline]
    fn unify_branch(self, other: Self) -> Option<Self> {
        match (self, other) {
            (ValKind::Int, ValKind::Int)
            | (ValKind::Int, ValKind::VarAny)
            | (ValKind::VarAny, ValKind::Int) => Some(ValKind::Int),
            (ValKind::Bool, ValKind::Bool) => Some(ValKind::Bool),
            (ValKind::Str, ValKind::Str) => Some(ValKind::Str),
            (ValKind::Node, ValKind::Node)
            | (ValKind::Node, ValKind::VarAny)
            | (ValKind::VarAny, ValKind::Node) => Some(ValKind::Node),
            (ValKind::VarAny, ValKind::VarAny) => Some(ValKind::VarAny),
            _ => None,
        }
    }
}

fn step_budget(depth: i32, budget: &mut usize) -> Option<()> {
    if depth >= MAX_DEPTH || *budget == 0 {
        return None;
    }
    *budget -= 1;
    Some(())
}

fn constant_int(arena: &TermArena, idx: TermIdx, depth: i32, budget: &mut usize) -> Option<i64> {
    step_budget(depth, budget)?;
    match arena.get(idx) {
        TermNode::Lit { value: Value::Int(n) } => Some(*n),
        TermNode::Plus { items } if items.len() == 2 => constant_int(arena, items[0], depth + 1, budget)?.checked_add(constant_int(arena, items[1], depth + 1, budget)?),
        TermNode::Times { items } if items.len() == 2 => constant_int(arena, items[0], depth + 1, budget)?.checked_mul(constant_int(arena, items[1], depth + 1, budget)?),
        TermNode::Minus { a, b } => constant_int(arena, *a, depth + 1, budget)?.checked_sub(constant_int(arena, *b, depth + 1, budget)?),
        TermNode::Neg { arg } => constant_int(arena, *arg, depth + 1, budget)?.checked_neg(),
        TermNode::Abs { arg } => constant_int(arena, *arg, depth + 1, budget)?.checked_abs(),
        _ => None,
    }
}

fn known_overflow(arena: &TermArena, idx: TermIdx, depth: i32, budget: &mut usize) -> bool {
    // Exhaustion rejects compilation. The budget is shared with every nested
    // constant-fold attempt, so repeated visits through a shared Term DAG are
    // bounded by MAX_NODES in total, not once per recursive branch.
    if step_budget(depth, budget).is_none() { return true; }
    let arithmetic = matches!(arena.get(idx), TermNode::Plus { .. } | TermNode::Times { .. } | TermNode::Minus { .. } | TermNode::Neg { .. } | TermNode::Abs { .. });
    // A nonconstant integer source (notably Count(Neighbours)) can overflow
    // at runtime when combined with another integer. Its where predicate must
    // stay interpreted because the JIT has no checked-arithmetic panic path.
    let here = arithmetic && constant_int(arena, idx, 0, budget).is_none();
    if here { return true; }
    match arena.get(idx) {
        TermNode::Plus { items } | TermNode::Times { items } | TermNode::And { items } | TermNode::Or { items } => items.iter().any(|&i| known_overflow(arena, i, depth + 1, budget)),
        TermNode::Minus { a, b } | TermNode::Lt { a, b } | TermNode::Lte { a, b } | TermNode::Gt { a, b } | TermNode::Gte { a, b } | TermNode::Eq { a, b } => known_overflow(arena, *a, depth + 1, budget) || known_overflow(arena, *b, depth + 1, budget),
        TermNode::Neg { arg } | TermNode::Abs { arg } | TermNode::Not { arg } => known_overflow(arena, *arg, depth + 1, budget),
        TermNode::IfThenElse { cond, then, other } => known_overflow(arena, *cond, depth + 1, budget) || known_overflow(arena, *then, depth + 1, budget) || known_overflow(arena, *other, depth + 1, budget),
        _ => false,
    }
}

fn infer_kind(
    arena: &TermArena,
    idx: TermIdx,
    vars: &FxHashMap<Sym, u32>,
    var_is_node: bool,
    depth: i32,
    budget: &mut usize,
) -> Option<ValKind> {
    step_budget(depth, budget)?;
    match arena.get(idx) {
        TermNode::Lit { value } => match value {
            Value::Int(_) => Some(ValKind::Int),
            Value::Bool(_) => Some(ValKind::Bool),
            Value::Str(_) => Some(ValKind::Str),
            Value::Node(_) => Some(ValKind::Node),
            _ => None,
        },
        TermNode::Var { name } => {
            let arg_idx = *vars.get(name)?;
            if arg_idx >= 5 {
                return None;
            }
            Some(if var_is_node {
                ValKind::Node
            } else {
                ValKind::VarAny
            })
        }
        TermNode::Plus { items } | TermNode::Times { items } if items.len() == 2 => {
            let ka = infer_kind(arena, items[0], vars, var_is_node, depth + 1, budget)?;
            let kb = infer_kind(arena, items[1], vars, var_is_node, depth + 1, budget)?;
            if ka.is_int() && kb.is_int() {
                Some(ValKind::Int)
            } else {
                None
            }
        }
        TermNode::Minus { a, b } => {
            let ka = infer_kind(arena, *a, vars, var_is_node, depth + 1, budget)?;
            let kb = infer_kind(arena, *b, vars, var_is_node, depth + 1, budget)?;
            if ka.is_int() && kb.is_int() {
                Some(ValKind::Int)
            } else {
                None
            }
        }
        TermNode::Neg { arg } | TermNode::Abs { arg } => {
            let k = infer_kind(arena, *arg, vars, var_is_node, depth + 1, budget)?;
            if k.is_int() {
                Some(ValKind::Int)
            } else {
                None
            }
        }
        TermNode::Lt { a, b }
        | TermNode::Lte { a, b }
        | TermNode::Gt { a, b }
        | TermNode::Gte { a, b } => {
            let ka = infer_kind(arena, *a, vars, var_is_node, depth + 1, budget)?;
            let kb = infer_kind(arena, *b, vars, var_is_node, depth + 1, budget)?;
            if ka.is_int() && kb.is_int() {
                Some(ValKind::Bool)
            } else {
                None
            }
        }
        TermNode::Eq { a, b } => {
            let ka = infer_kind(arena, *a, vars, var_is_node, depth + 1, budget)?;
            let kb = infer_kind(arena, *b, vars, var_is_node, depth + 1, budget)?;
            if ka.eq_compatible(kb) {
                Some(ValKind::Bool)
            } else {
                None
            }
        }
        TermNode::Not { arg } => {
            let k = infer_kind(arena, *arg, vars, var_is_node, depth + 1, budget)?;
            if k.is_condition_compatible() {
                Some(ValKind::Bool)
            } else {
                None
            }
        }
        TermNode::And { items } | TermNode::Or { items } => {
            for item in items {
                let k = infer_kind(arena, *item, vars, var_is_node, depth + 1, budget)?;
                if !k.is_condition_compatible() {
                    return None;
                }
            }
            Some(ValKind::Bool)
        }
        TermNode::IfThenElse { cond, then, other } => {
            let kc = infer_kind(arena, *cond, vars, var_is_node, depth + 1, budget)?;
            if !kc.is_condition_compatible() {
                return None;
            }
            let kt = infer_kind(arena, *then, vars, var_is_node, depth + 1, budget)?;
            let ko = infer_kind(arena, *other, vars, var_is_node, depth + 1, budget)?;
            kt.unify_branch(ko)
        }
        TermNode::TypeOf { node } => {
            let kn = infer_kind(arena, *node, vars, var_is_node, depth + 1, budget)?;
            if kn.is_node() {
                Some(ValKind::Str)
            } else {
                None
            }
        }
        TermNode::Attr { node, .. } => {
            let kn = infer_kind(arena, *node, vars, var_is_node, depth + 1, budget)?;
            if kn.is_node() {
                Some(ValKind::Int)
            } else {
                None
            }
        }
        TermNode::Count { source } => {
            if let TermNode::Neighbours { node, .. } = arena.get(*source) {
                let kn = infer_kind(arena, *node, vars, var_is_node, depth + 1, budget)?;
                if kn.is_node() {
                    Some(ValKind::Int)
                } else {
                    None
                }
            } else {
                None
            }
        }
        _ => None,
    }
}

/// True iff the Term-tree references any graph state — used to decide
/// which `call_*` variant the caller must use. Bounded by `MAX_DEPTH` and `budget`.
fn scan_needs_ctx(
    arena: &TermArena,
    idx: TermIdx,
    depth: i32,
    budget: &mut usize,
) -> Option<bool> {
    step_budget(depth, budget)?;
    match arena.get(idx) {
        TermNode::TypeOf { .. } | TermNode::Attr { .. } => Some(true),
        TermNode::Count { source } => {
            if let TermNode::Neighbours { node, .. } = arena.get(*source) {
                let _ = scan_needs_ctx(arena, *node, depth + 1, budget)?;
                Some(true)
            } else {
                None
            }
        }
        TermNode::Plus { items }
        | TermNode::Times { items }
        | TermNode::And { items }
        | TermNode::Or { items } => {
            let mut any = false;
            for i in items {
                any |= scan_needs_ctx(arena, *i, depth + 1, budget)?;
            }
            Some(any)
        }
        TermNode::Minus { a, b }
        | TermNode::Lt { a, b }
        | TermNode::Lte { a, b }
        | TermNode::Gt { a, b }
        | TermNode::Gte { a, b }
        | TermNode::Eq { a, b } => {
            let la = scan_needs_ctx(arena, *a, depth + 1, budget)?;
            let lb = scan_needs_ctx(arena, *b, depth + 1, budget)?;
            Some(la || lb)
        }
        TermNode::Neg { arg } | TermNode::Abs { arg } | TermNode::Not { arg } => {
            scan_needs_ctx(arena, *arg, depth + 1, budget)
        }
        TermNode::IfThenElse { cond, then, other } => {
            let lc = scan_needs_ctx(arena, *cond, depth + 1, budget)?;
            let lt = scan_needs_ctx(arena, *then, depth + 1, budget)?;
            let lo = scan_needs_ctx(arena, *other, depth + 1, budget)?;
            Some(lc || lt || lo)
        }
        TermNode::Lit { .. } | TermNode::Var { .. } => Some(false),
        _ => None,
    }
}

/// True iff the subtree contains an `Attr` within the JIT depth/node budget.
/// Returns `None` if the tree exceeds `MAX_DEPTH` or `budget` (which also forces
/// `CompiledWhere::try_compile` to fall back to the interpreter).
fn subtree_has_attr(
    arena: &TermArena,
    idx: TermIdx,
    depth: i32,
    budget: &mut usize,
) -> Option<bool> {
    step_budget(depth, budget)?;
    match arena.get(idx) {
        TermNode::Attr { .. } => Some(true),
        TermNode::Count { source } => {
            if let TermNode::Neighbours { node, .. } = arena.get(*source) {
                subtree_has_attr(arena, *node, depth + 1, budget)
            } else {
                None
            }
        }
        TermNode::Plus { items }
        | TermNode::Times { items }
        | TermNode::And { items }
        | TermNode::Or { items } => {
            for i in items {
                if subtree_has_attr(arena, *i, depth + 1, budget)? {
                    return Some(true);
                }
            }
            Some(false)
        }
        TermNode::Minus { a, b }
        | TermNode::Lt { a, b }
        | TermNode::Lte { a, b }
        | TermNode::Gt { a, b }
        | TermNode::Gte { a, b }
        | TermNode::Eq { a, b } => {
            if subtree_has_attr(arena, *a, depth + 1, budget)? {
                return Some(true);
            }
            subtree_has_attr(arena, *b, depth + 1, budget)
        }
        TermNode::Neg { arg } | TermNode::Abs { arg } | TermNode::Not { arg } => {
            subtree_has_attr(arena, *arg, depth + 1, budget)
        }
        TermNode::IfThenElse { cond, then, other } => {
            if subtree_has_attr(arena, *cond, depth + 1, budget)? {
                return Some(true);
            }
            if subtree_has_attr(arena, *then, depth + 1, budget)? {
                return Some(true);
            }
            subtree_has_attr(arena, *other, depth + 1, budget)
        }
        TermNode::TypeOf { node } => subtree_has_attr(arena, *node, depth + 1, budget),
        TermNode::Lit { .. } | TermNode::Var { .. } => Some(false),
        _ => None,
    }
}

const CTX_SLOT: i32 = -8;
const ARG_SLOT_BASE: i32 = -16;
const TEMP_SLOT_BASE: i32 = -72;
const MAX_DEPTH: i32 = 32;
const MAX_NODES: usize = 256;

#[inline]
fn temp_slot(depth: i32) -> i32 {
    TEMP_SLOT_BASE - 8 * depth
}

fn emit_term(
    ops: &mut dynasmrt::x64::Assembler,
    arena: &TermArena,
    idx: TermIdx,
    vars: &FxHashMap<Sym, u32>,
    depth: i32,
    budget: &mut usize,
) -> Option<()> {
    step_budget(depth, budget)?;
    match arena.get(idx) {
        TermNode::Lit { value } => emit_lit(ops, value),
        TermNode::Var { name } => emit_var(ops, vars, *name),

        TermNode::Plus { items } if items.len() == 2 => {
            emit_binop(ops, arena, items[0], items[1], vars, depth, budget, |o| {
                dynasm!(o; .arch x64; add rax, [rbp + temp_slot(depth)]);
            })
        }
        TermNode::Times { items } if items.len() == 2 => {
            emit_binop(ops, arena, items[0], items[1], vars, depth, budget, |o| {
                dynasm!(o; .arch x64; imul rax, [rbp + temp_slot(depth)]);
            })
        }
        TermNode::Minus { a, b } => {
            // Need a - b. Compute a at depth + 1, save to temp_slot(depth);
            // compute b at depth + 1; subtract b from saved a.
            emit_term(ops, arena, *a, vars, depth + 1, budget)?;
            dynasm!(ops; .arch x64; mov [rbp + temp_slot(depth)], rax);
            emit_term(ops, arena, *b, vars, depth + 1, budget)?;
            dynasm!(ops; .arch x64
                ; mov r10, rax
                ; mov rax, [rbp + temp_slot(depth)]
                ; sub rax, r10
            );
            Some(())
        }
        TermNode::Neg { arg } => {
            emit_term(ops, arena, *arg, vars, depth + 1, budget)?;
            dynasm!(ops; .arch x64; neg rax);
            Some(())
        }
        TermNode::Abs { arg } => {
            emit_term(ops, arena, *arg, vars, depth + 1, budget)?;
            dynasm!(ops; .arch x64
                ; mov r10, rax
                ; sar r10, 63
                ; xor rax, r10
                ; sub rax, r10
            );
            Some(())
        }

        TermNode::Lt { a, b } => emit_cmp(ops, arena, *a, *b, vars, depth, budget, CmpKind::Lt),
        TermNode::Lte { a, b } => emit_cmp(ops, arena, *a, *b, vars, depth, budget, CmpKind::Lte),
        TermNode::Gt { a, b } => emit_cmp(ops, arena, *a, *b, vars, depth, budget, CmpKind::Gt),
        TermNode::Gte { a, b } => emit_cmp(ops, arena, *a, *b, vars, depth, budget, CmpKind::Gte),
        TermNode::Eq { a, b } => emit_cmp(ops, arena, *a, *b, vars, depth, budget, CmpKind::Eq),

        TermNode::Not { arg } => {
            emit_term(ops, arena, *arg, vars, depth + 1, budget)?;
            dynasm!(ops; .arch x64
                ; test rax, rax
                ; sete al
                ; movzx rax, al
            );
            Some(())
        }
        TermNode::And { items } => {
            emit_short_circuit(ops, arena, items, vars, depth, budget, /*want_true=*/ false)
        }
        TermNode::Or { items } => {
            emit_short_circuit(ops, arena, items, vars, depth, budget, /*want_true=*/ true)
        }

        TermNode::IfThenElse { cond, then, other } => {
            emit_term(ops, arena, *cond, vars, depth + 1, budget)?;
            let else_lbl = ops.new_dynamic_label();
            let end_lbl = ops.new_dynamic_label();
            dynasm!(ops; .arch x64
                ; test rax, rax
                ; jz =>else_lbl
            );
            emit_term(ops, arena, *then, vars, depth + 1, budget)?;
            dynasm!(ops; .arch x64
                ; jmp =>end_lbl
                ; =>else_lbl
            );
            emit_term(ops, arena, *other, vars, depth + 1, budget)?;
            dynasm!(ops; .arch x64; =>end_lbl);
            Some(())
        }

        // --- graph access ---
        TermNode::TypeOf { node } => {
            emit_term(ops, arena, *node, vars, depth + 1, budget)?;
            // rax = node-id (as i64). Call thunk_type_of(ctx, node).
            let thunk_addr = thunk_type_of as *const () as usize as i64;
            dynasm!(ops; .arch x64
                ; mov rsi, rax
                ; mov rdi, [rbp + CTX_SLOT]
                ; mov rax, QWORD thunk_addr
                ; call rax
            );
            Some(())
        }
        TermNode::Attr { node, key } => {
            emit_term(ops, arena, *node, vars, depth + 1, budget)?;
            let key_int = key.0 as i64;
            let thunk_addr = thunk_attr_int as *const () as usize as i64;
            dynasm!(ops; .arch x64
                ; mov rsi, rax
                ; mov rdx, QWORD key_int
                ; mov rdi, [rbp + CTX_SLOT]
                ; mov rax, QWORD thunk_addr
                ; call rax
            );
            Some(())
        }
        // Fused pattern: Count(Neighbours(node, edge_type)).
        TermNode::Count { source } => {
            if let TermNode::Neighbours {
                node,
                edge_type,
                any_type,
            } = arena.get(*source)
            {
                emit_term(ops, arena, *node, vars, depth + 1, budget)?;
                let et: i64 = if *any_type { 0 } else { edge_type.0 as i64 };
                let thunk_addr = thunk_neighbour_count as *const () as usize as i64;
                dynasm!(ops; .arch x64
                    ; mov rsi, rax
                    ; mov rdx, QWORD et
                    ; mov rdi, [rbp + CTX_SLOT]
                    ; mov rax, QWORD thunk_addr
                    ; call rax
                );
                Some(())
            } else {
                None // unfused Count — let interpreter handle
            }
        }

        _ => None,
    }
}

fn emit_binop<F>(
    ops: &mut dynasmrt::x64::Assembler,
    arena: &TermArena,
    a: TermIdx,
    b: TermIdx,
    vars: &FxHashMap<Sym, u32>,
    depth: i32,
    budget: &mut usize,
    combine: F,
) -> Option<()>
where
    F: FnOnce(&mut dynasmrt::x64::Assembler),
{
    emit_term(ops, arena, a, vars, depth + 1, budget)?;
    dynasm!(ops; .arch x64; mov [rbp + temp_slot(depth)], rax);
    emit_term(ops, arena, b, vars, depth + 1, budget)?;
    combine(ops);
    Some(())
}

#[inline]
fn emit_lit(ops: &mut dynasmrt::x64::Assembler, value: &Value) -> Option<()> {
    match value {
        Value::Int(n) => {
            dynasm!(ops; .arch x64; mov rax, QWORD *n);
            Some(())
        }
        Value::Bool(b) => {
            let v: i64 = if *b { 1 } else { 0 };
            dynasm!(ops; .arch x64; mov rax, QWORD v);
            Some(())
        }
        // Strings (interned Syms) compile to their Sym value as i64 — so
        // `Eq(TypeOf(x), Lit("AliveCell"))` works after both sides
        // resolve to interned u32 Syms.
        Value::Str(s) => {
            let v: i64 = s.0 as i64;
            dynasm!(ops; .arch x64; mov rax, QWORD v);
            Some(())
        }
        // Node literal — store the slab index as i64.
        Value::Node(nid) => {
            let v: i64 = nid.0 as i64;
            dynasm!(ops; .arch x64; mov rax, QWORD v);
            Some(())
        }
        _ => None,
    }
}

#[inline]
fn emit_var(
    ops: &mut dynasmrt::x64::Assembler,
    vars: &FxHashMap<Sym, u32>,
    name: Sym,
) -> Option<()> {
    let arg_idx = *vars.get(&name)? as i32;
    if arg_idx >= 5 {
        return None;
    }
    let slot = ARG_SLOT_BASE - 8 * arg_idx;
    dynasm!(ops; .arch x64; mov rax, [rbp + slot]);
    Some(())
}

enum CmpKind {
    Lt,
    Lte,
    Gt,
    Gte,
    Eq,
}

#[inline]
fn emit_cmp(
    ops: &mut dynasmrt::x64::Assembler,
    arena: &TermArena,
    a: TermIdx,
    b: TermIdx,
    vars: &FxHashMap<Sym, u32>,
    depth: i32,
    budget: &mut usize,
    kind: CmpKind,
) -> Option<()> {
    emit_term(ops, arena, a, vars, depth + 1, budget)?;
    dynasm!(ops; .arch x64; mov [rbp + temp_slot(depth)], rax);
    emit_term(ops, arena, b, vars, depth + 1, budget)?;
    dynasm!(ops; .arch x64
        ; mov r10, rax
        ; mov rax, [rbp + temp_slot(depth)]
        ; cmp rax, r10
    );
    match kind {
        CmpKind::Lt => dynasm!(ops; .arch x64; setl al),
        CmpKind::Lte => dynasm!(ops; .arch x64; setle al),
        CmpKind::Gt => dynasm!(ops; .arch x64; setg al),
        CmpKind::Gte => dynasm!(ops; .arch x64; setge al),
        CmpKind::Eq => dynasm!(ops; .arch x64; sete al),
    }
    dynasm!(ops; .arch x64; movzx rax, al);
    Some(())
}

#[inline]
fn emit_short_circuit(
    ops: &mut dynasmrt::x64::Assembler,
    arena: &TermArena,
    items: &[TermIdx],
    vars: &FxHashMap<Sym, u32>,
    depth: i32,
    budget: &mut usize,
    want_true: bool,
) -> Option<()> {
    if items.is_empty() {
        let v: i64 = if want_true { 0 } else { 1 };
        dynasm!(ops; .arch x64; mov rax, QWORD v);
        return Some(());
    }
    let end_lbl = ops.new_dynamic_label();
    for (i, item) in items.iter().enumerate() {
        emit_term(ops, arena, *item, vars, depth + 1, budget)?;
        dynasm!(ops; .arch x64; test rax, rax);
        if i < items.len() - 1 {
            if want_true {
                dynasm!(ops; .arch x64; jnz =>end_lbl);
            } else {
                dynasm!(ops; .arch x64; jz =>end_lbl);
            }
        }
    }
    dynasm!(ops; .arch x64
        ; =>end_lbl
        ; setne al
        ; movzx rax, al
    );
    Some(())
}

// --- thunks ---------------------------------------------------------------
//
// SysV-64 callees. Called from JIT'd code via mov rax,thunk_addr; call rax.
// The JIT'd code is itself extern "sysv64", so caller-saved regs (rax,
// rcx, rdx, rsi, rdi, r8-r11) are clobbered by the call — which is
// fine because emit_term's convention is "result in rax" and we don't
// keep state in caller-saved regs across emits (we use [rbp + slot]).

unsafe extern "sysv64" fn thunk_type_of(ctx: *const JitCtx, node: i64) -> i64 {
    if ctx.is_null() {
        return -1;
    }
    let graph = (*ctx).graph;
    if graph.is_null() {
        return -1;
    }
    let Ok(raw) = u32::try_from(node) else {
        return -1;
    };
    let nid = NodeID(raw);
    if !(*graph).has_node(nid) {
        return -1;
    }
    let type_sym = (*graph).node(nid).type_;
    crate::access_trace::note(13, nid.0, type_sym.0, crate::access_trace::NO_ID);
    type_sym.0 as i64
}

unsafe extern "sysv64" fn thunk_attr_int(ctx: *const JitCtx, node: i64, key_sym: i64) -> i64 {
    crate::fallback_trace::note_attr_eval();
    if ctx.is_null() {
        return 0;
    }
    let graph = (*ctx).graph;
    if graph.is_null() {
        return 0;
    }
    let Ok(raw_node) = u32::try_from(node) else {
        return 0;
    };
    let Ok(raw_key) = u32::try_from(key_sym) else {
        return 0;
    };
    let nid = NodeID(raw_node);
    if !(*graph).has_node(nid) {
        return 0;
    }
    let key = Sym(raw_key);
    crate::access_trace::note(12, nid.0, key.0, crate::access_trace::NO_ID);
    match (*graph).node(nid).attrs.get(&key) {
        Some(Value::Int(n)) => *n,
        Some(Value::Bool(b)) => {
            if *b {
                1
            } else {
                0
            }
        }
        // Admit only finite, integer-valued floats (such as 1.0 or 2.0 flags)
        // when invoked via standalone `jit::compile`. Fractional floats are not
        // truncated to 0; rule `where` clauses containing `Attr` fall back to
        // the interpreter via `CompiledWhere::try_compile`.
        Some(Value::Float(f)) if f.is_finite() && f.fract() == 0.0 => *f as i64,
        // Str values resolve to their Sym so JIT'd comparison sees the
        // same i64 the interpreter would.
        Some(Value::Str(s)) => s.0 as i64,
        Some(Value::Node(n)) => n.0 as i64,
        None => {
            crate::fallback_trace::note_defaulted_read(key);
            0
        }
        _ => 0,
    }
}

unsafe extern "sysv64" fn thunk_neighbour_count(
    ctx: *const JitCtx,
    node: i64,
    edge_type_sym: i64,
) -> i64 {
    if ctx.is_null() {
        return 0;
    }
    let graph = (*ctx).graph;
    if graph.is_null() {
        return 0;
    }
    let Ok(raw_node) = u32::try_from(node) else {
        return 0;
    };
    let nid = NodeID(raw_node);
    if !(*graph).has_node(nid) {
        return 0;
    }
    let et = if edge_type_sym == 0 {
        None
    } else {
        let Ok(raw_et) = u32::try_from(edge_type_sym) else {
            return 0;
        };
        Some(Sym(raw_et))
    };
    let edges = (*graph).out_edges_slice(nid, et);
    crate::access_trace::note_out_edges(&*graph, nid, et);
    edges.len() as i64
}

// --- tests ---------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use crate::sym::Interner;

    fn compile_pure(arena: &TermArena, root: TermIdx, args: &[i64]) -> i64 {
        let vars: FxHashMap<Sym, u32> = FxHashMap::default();
        let f = compile(arena, root, &vars).expect("compile");
        assert!(!f.needs_ctx());
        f.call_pure(args)
    }

    fn compile_with(
        arena: &TermArena,
        root: TermIdx,
        vars: &FxHashMap<Sym, u32>,
        args: &[i64],
    ) -> i64 {
        let f = compile(arena, root, vars).expect("compile");
        assert!(!f.needs_ctx());
        f.call_pure(args)
    }

    #[test]
    fn jit_literal_int() {
        let mut a = TermArena::new();
        let lit = a.add(TermNode::Lit {
            value: Value::Int(42),
        });
        assert_eq!(compile_pure(&a, lit, &[]), 42);
    }

    #[test]
    fn jit_literal_bool() {
        let mut a = TermArena::new();
        let t = a.add(TermNode::Lit {
            value: Value::Bool(true),
        });
        let f = a.add(TermNode::Lit {
            value: Value::Bool(false),
        });
        assert_eq!(compile_pure(&a, t, &[]), 1);
        assert_eq!(compile_pure(&a, f, &[]), 0);
    }

    #[test]
    fn jit_plus_minus_times_neg_abs() {
        let mut a = TermArena::new();
        let two = a.add(TermNode::Lit {
            value: Value::Int(2),
        });
        let three = a.add(TermNode::Lit {
            value: Value::Int(3),
        });
        let five = a.add(TermNode::Lit {
            value: Value::Int(5),
        });
        let plus = a.add(TermNode::Plus {
            items: vec![two, three],
        });
        assert_eq!(compile_pure(&a, plus, &[]), 5);
        let minus = a.add(TermNode::Minus { a: five, b: two });
        assert_eq!(compile_pure(&a, minus, &[]), 3);
        let times = a.add(TermNode::Times {
            items: vec![two, three],
        });
        assert_eq!(compile_pure(&a, times, &[]), 6);
        let neg = a.add(TermNode::Neg { arg: five });
        assert_eq!(compile_pure(&a, neg, &[]), -5);
        let neg5 = a.add(TermNode::Lit {
            value: Value::Int(-5),
        });
        let abs = a.add(TermNode::Abs { arg: neg5 });
        assert_eq!(compile_pure(&a, abs, &[]), 5);
    }

    #[test]
    fn jit_comparisons_return_0_or_1() {
        let mut a = TermArena::new();
        let three = a.add(TermNode::Lit {
            value: Value::Int(3),
        });
        let five = a.add(TermNode::Lit {
            value: Value::Int(5),
        });
        let lt = a.add(TermNode::Lt { a: three, b: five });
        let lt_eq = a.add(TermNode::Lt { a: three, b: three });
        let lte = a.add(TermNode::Lte { a: three, b: three });
        let gt = a.add(TermNode::Gt { a: five, b: three });
        let gte = a.add(TermNode::Gte { a: three, b: three });
        let eq = a.add(TermNode::Eq { a: three, b: three });
        let eq_no = a.add(TermNode::Eq { a: three, b: five });
        assert_eq!(compile_pure(&a, lt, &[]), 1);
        assert_eq!(compile_pure(&a, lt_eq, &[]), 0);
        assert_eq!(compile_pure(&a, lte, &[]), 1);
        assert_eq!(compile_pure(&a, gt, &[]), 1);
        assert_eq!(compile_pure(&a, gte, &[]), 1);
        assert_eq!(compile_pure(&a, eq, &[]), 1);
        assert_eq!(compile_pure(&a, eq_no, &[]), 0);
    }

    #[test]
    fn jit_var_takes_arg_position() {
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let x = ir.intern("x");
        let y = ir.intern("y");
        let x_var = a.add(TermNode::Var { name: x });
        let y_var = a.add(TermNode::Var { name: y });
        let sum = a.add(TermNode::Plus {
            items: vec![x_var, y_var],
        });
        let mut vars: FxHashMap<Sym, u32> = FxHashMap::default();
        vars.insert(x, 0);
        vars.insert(y, 1);
        assert_eq!(compile_with(&a, sum, &vars, &[10, 20]), 30);
        assert_eq!(compile_with(&a, sum, &vars, &[-5, 5]), 0);
    }

    #[test]
    fn jit_if_then_else_picks_branch() {
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let x = ir.intern("x");
        let x_var = a.add(TermNode::Var { name: x });
        let ten = a.add(TermNode::Lit {
            value: Value::Int(10),
        });
        let hundred = a.add(TermNode::Lit {
            value: Value::Int(100),
        });
        let two = a.add(TermNode::Lit {
            value: Value::Int(2),
        });
        let lt = a.add(TermNode::Lt { a: x_var, b: ten });
        let times2 = a.add(TermNode::Times {
            items: vec![x_var, two],
        });
        let ite = a.add(TermNode::IfThenElse {
            cond: lt,
            then: hundred,
            other: times2,
        });
        let mut vars: FxHashMap<Sym, u32> = FxHashMap::default();
        vars.insert(x, 0);
        assert_eq!(compile_with(&a, ite, &vars, &[5]), 100);
        assert_eq!(compile_with(&a, ite, &vars, &[20]), 40);
    }

    #[test]
    fn jit_and_or_short_circuit() {
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let x = ir.intern("x");
        let y = ir.intern("y");
        let x_var = a.add(TermNode::Var { name: x });
        let y_var = a.add(TermNode::Var { name: y });
        let zero = a.add(TermNode::Lit {
            value: Value::Int(0),
        });
        let gt_x = a.add(TermNode::Gt { a: x_var, b: zero });
        let gt_y = a.add(TermNode::Gt { a: y_var, b: zero });
        let and = a.add(TermNode::And {
            items: vec![gt_x, gt_y],
        });
        let or = a.add(TermNode::Or {
            items: vec![gt_x, gt_y],
        });
        let mut vars: FxHashMap<Sym, u32> = FxHashMap::default();
        vars.insert(x, 0);
        vars.insert(y, 1);
        assert_eq!(compile_with(&a, and, &vars, &[1, 1]), 1);
        assert_eq!(compile_with(&a, and, &vars, &[1, 0]), 0);
        assert_eq!(compile_with(&a, and, &vars, &[0, 1]), 0);
        assert_eq!(compile_with(&a, or, &vars, &[1, 0]), 1);
        assert_eq!(compile_with(&a, or, &vars, &[0, 1]), 1);
        assert_eq!(compile_with(&a, or, &vars, &[0, 0]), 0);
    }

    #[test]
    fn jit_returns_none_on_unsupported_term() {
        let mut a = TermArena::new();
        let f = a.add(TermNode::Lit {
            value: Value::Float(3.14),
        });
        let vars = FxHashMap::default();
        assert!(compile(&a, f, &vars).is_none());
    }

    #[test]
    fn jit_matches_interpreter() {
        use crate::graph::TypedGraph;
        use crate::term::{evaluate, Env, EvalCtx};
        use smallvec::SmallVec;

        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let x = ir.intern("x");
        let y = ir.intern("y");
        let g = TypedGraph::new();
        let x_var = a.add(TermNode::Var { name: x });
        let y_var = a.add(TermNode::Var { name: y });
        let zero = a.add(TermNode::Lit {
            value: Value::Int(0),
        });
        let ten = a.add(TermNode::Lit {
            value: Value::Int(10),
        });
        let one = a.add(TermNode::Lit {
            value: Value::Int(1),
        });
        let neg_one = a.add(TermNode::Lit {
            value: Value::Int(-1),
        });
        let gt = a.add(TermNode::Gt { a: x_var, b: zero });
        let lt = a.add(TermNode::Lt { a: y_var, b: ten });
        let and = a.add(TermNode::And {
            items: vec![gt, lt],
        });
        let prod = a.add(TermNode::Times {
            items: vec![x_var, y_var],
        });
        let prod_plus = a.add(TermNode::Plus {
            items: vec![prod, one],
        });
        let ite = a.add(TermNode::IfThenElse {
            cond: and,
            then: prod_plus,
            other: neg_one,
        });
        let mut vars: FxHashMap<Sym, u32> = FxHashMap::default();
        vars.insert(x, 0);
        vars.insert(y, 1);
        let jit_fn = compile(&a, ite, &vars).expect("compile");

        for &(xv, yv) in &[(5i64, 3i64), (-1, 5), (5, 15), (0, 5), (7, 9)] {
            let mut env: Env = SmallVec::new();
            env.push((x, Value::Int(xv)));
            env.push((y, Value::Int(yv)));
            let mut ctx = EvalCtx::new(&g, &ir);
            let interp = match evaluate(&a, ite, &mut env, &mut ctx) {
                Value::Int(n) => n,
                Value::Bool(b) => {
                    if b {
                        1
                    } else {
                        0
                    }
                }
                other => panic!("unexpected interp result: {:?}", other),
            };
            let jit = jit_fn.call_pure(&[xv, yv]);
            assert_eq!(
                jit, interp,
                "x={}, y={}: jit={} interp={}",
                xv, yv, jit, interp
            );
        }
    }

    // --- graph access ---

    #[test]
    fn jit_typeof_returns_node_type_sym() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let alive = ir.intern("AliveCell");
        let dead = ir.intern("DeadCell");
        let a_node = g.insert_node(alive, rustc_hash::FxHashMap::default());
        let d_node = g.insert_node(dead, rustc_hash::FxHashMap::default());

        let mut arena = TermArena::new();
        let n = ir.intern("n");
        let n_var = arena.add(TermNode::Var { name: n });
        let tof = arena.add(TermNode::TypeOf { node: n_var });
        let mut vars: FxHashMap<Sym, u32> = FxHashMap::default();
        vars.insert(n, 0);
        let f = compile(&arena, tof, &vars).expect("compile");
        assert!(f.needs_ctx(), "TypeOf requires ctx");
        let ctx = JitCtx::from_graph(&g);
        assert_eq!(f.call_with_ctx(&ctx, &[a_node.0 as i64]), alive.0 as i64);
        assert_eq!(f.call_with_ctx(&ctx, &[d_node.0 as i64]), dead.0 as i64);
    }

    #[test]
    fn jit_attr_returns_int_value() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let cell = ir.intern("Cell");
        let count_key = ir.intern("count");
        let mut attrs: rustc_hash::FxHashMap<Sym, Value> = Default::default();
        attrs.insert(count_key, Value::Int(42));
        let n = g.insert_node(cell, attrs);

        let mut arena = TermArena::new();
        let n_sym = ir.intern("n");
        let n_var = arena.add(TermNode::Var { name: n_sym });
        let attr = arena.add(TermNode::Attr {
            node: n_var,
            key: count_key,
        });
        let mut vars: FxHashMap<Sym, u32> = FxHashMap::default();
        vars.insert(n_sym, 0);
        let f = compile(&arena, attr, &vars).expect("compile");
        let ctx = JitCtx::from_graph(&g);
        assert_eq!(f.call_with_ctx(&ctx, &[n.0 as i64]), 42);
    }

    #[test]
    fn jit_attr_float_flag_compares_equal_to_int_lit() {
        // Regression: a flag stored as Float(1.0) must satisfy a JIT'd `Eq(Attr,1)`.
        // Before the Float case in thunk_attr_int it fell through to 0, so the where
        // silently evaluated false and the rule never fired (the set_attr-rule quirk).
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let op = ir.intern("Operator");
        let composed = ir.intern("composed");
        let mut attrs: rustc_hash::FxHashMap<Sym, Value> = Default::default();
        attrs.insert(composed, Value::Float(1.0));
        let n = g.insert_node(op, attrs);

        let mut arena = TermArena::new();
        let v_sym = ir.intern("o");
        let v = arena.add(TermNode::Var { name: v_sym });
        let attr = arena.add(TermNode::Attr {
            node: v,
            key: composed,
        });
        let one = arena.add(TermNode::Lit {
            value: Value::Int(1),
        });
        let eq = arena.add(TermNode::Eq { a: attr, b: one });
        let mut vars: FxHashMap<Sym, u32> = FxHashMap::default();
        vars.insert(v_sym, 0);
        let f = compile(&arena, eq, &vars).expect("compile");
        let ctx = JitCtx::from_graph(&g);
        assert_eq!(
            f.call_with_ctx(&ctx, &[n.0 as i64]),
            1,
            "Eq(Float(1.0), 1) must be true under the JIT"
        );
        // and the integer part is read for a non-unit float flag
        let mut attrs2: rustc_hash::FxHashMap<Sym, Value> = Default::default();
        attrs2.insert(composed, Value::Float(2.0));
        let n2 = g.insert_node(op, attrs2);
        assert_eq!(
            f.call_with_ctx(&ctx, &[n2.0 as i64]),
            0,
            "Eq(Float(2.0), 1) must be false"
        );
    }

    #[test]
    fn jit_count_neighbours() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let cell = ir.intern("Cell");
        let adj = ir.intern("adjacent_to");
        let a_node = g.insert_node(cell, rustc_hash::FxHashMap::default());
        for _ in 0..7 {
            let b = g.insert_node(cell, rustc_hash::FxHashMap::default());
            g.insert_edge(a_node, adj, b, rustc_hash::FxHashMap::default())
                .unwrap();
        }

        let mut arena = TermArena::new();
        let me = ir.intern("me");
        let me_var = arena.add(TermNode::Var { name: me });
        let nbrs = arena.add(TermNode::Neighbours {
            node: me_var,
            edge_type: adj,
            any_type: false,
        });
        let cnt = arena.add(TermNode::Count { source: nbrs });
        let mut vars: FxHashMap<Sym, u32> = FxHashMap::default();
        vars.insert(me, 0);
        let f = compile(&arena, cnt, &vars).expect("compile");
        let ctx = JitCtx::from_graph(&g);
        assert_eq!(f.call_with_ctx(&ctx, &[a_node.0 as i64]), 7);
    }

    #[test]
    fn jit_typeof_eq_pattern() {
        // The dominant where-clause shape: TypeOf(x) == LitStr("Alive").
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let alive = ir.intern("AliveCell");
        let dead = ir.intern("DeadCell");
        let a1 = g.insert_node(alive, rustc_hash::FxHashMap::default());
        let d1 = g.insert_node(dead, rustc_hash::FxHashMap::default());

        let mut arena = TermArena::new();
        let n_sym = ir.intern("n");
        let n_var = arena.add(TermNode::Var { name: n_sym });
        let tof = arena.add(TermNode::TypeOf { node: n_var });
        let alive_lit = arena.add(TermNode::Lit {
            value: Value::Str(alive),
        });
        let eq = arena.add(TermNode::Eq {
            a: tof,
            b: alive_lit,
        });
        let mut vars: FxHashMap<Sym, u32> = FxHashMap::default();
        vars.insert(n_sym, 0);
        let f = compile(&arena, eq, &vars).expect("compile");
        let ctx = JitCtx::from_graph(&g);
        assert_eq!(f.call_with_ctx(&ctx, &[a1.0 as i64]), 1);
        assert_eq!(f.call_with_ctx(&ctx, &[d1.0 as i64]), 0);
    }

    #[test]
    fn jit_needs_ctx_panics_on_call_pure() {
        let mut ir = Interner::new();
        let mut arena = TermArena::new();
        let n_sym = ir.intern("n");
        let n_var = arena.add(TermNode::Var { name: n_sym });
        let tof = arena.add(TermNode::TypeOf { node: n_var });
        let mut vars: FxHashMap<Sym, u32> = FxHashMap::default();
        vars.insert(n_sym, 0);
        let f = compile(&arena, tof, &vars).expect("compile");
        assert!(f.needs_ctx());
        let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            f.call_pure(&[0]);
        }));
        assert!(result.is_err(), "call_pure on ctx-needing JIT must panic");
    }

    /// Microbench: same as before but for the most common real-rule shape:
    /// `If (TypeOf(x) == AliveCell) and (Count(Neighbours(x, adj)) >= 2)
    ///   then 1 else 0`.
    /// Run with `cargo test --release --lib jit::tests::bench_jit_graph_access -- --nocapture --ignored`.
    #[test]
    #[ignore]
    fn bench_jit_graph_access() {
        use crate::graph::TypedGraph;
        use crate::term::{evaluate, Env, EvalCtx};
        use smallvec::SmallVec;
        use std::time::Instant;

        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let alive = ir.intern("AliveCell");
        let dead = ir.intern("DeadCell");
        let adj = ir.intern("adjacent_to");

        // 100×100 Conway-ish grid; alternating alive/dead, 4-neighbour
        // edges. We'll bench evaluating a where-clause on each cell.
        let n = 100usize;
        let mut grid: Vec<Vec<NodeID>> = Vec::with_capacity(n);
        for i in 0..n {
            let mut row = Vec::with_capacity(n);
            for j in 0..n {
                let ty = if (i + j) % 2 == 0 { alive } else { dead };
                row.push(g.insert_node(ty, rustc_hash::FxHashMap::default()));
            }
            grid.push(row);
        }
        for i in 0..n {
            for j in 0..n {
                let me = grid[i][j];
                for (di, dj) in [(-1i32, 0), (1, 0), (0, -1), (0, 1)] {
                    let ni = ((i as i32 + di).rem_euclid(n as i32)) as usize;
                    let nj = ((j as i32 + dj).rem_euclid(n as i32)) as usize;
                    let _ = g.insert_edge(me, adj, grid[ni][nj], rustc_hash::FxHashMap::default());
                }
            }
        }

        // Build the where-clause Term: (TypeOf(x) == alive) AND (Count(Neighbours(x, adj)) >= 2)
        let mut arena = TermArena::new();
        let x_sym = ir.intern("x");
        let x_var = arena.add(TermNode::Var { name: x_sym });
        let tof = arena.add(TermNode::TypeOf { node: x_var });
        let alive_lit = arena.add(TermNode::Lit {
            value: Value::Str(alive),
        });
        let eq = arena.add(TermNode::Eq {
            a: tof,
            b: alive_lit,
        });
        let nbrs = arena.add(TermNode::Neighbours {
            node: x_var,
            edge_type: adj,
            any_type: false,
        });
        let cnt = arena.add(TermNode::Count { source: nbrs });
        let two = arena.add(TermNode::Lit {
            value: Value::Int(2),
        });
        let ge = arena.add(TermNode::Gte { a: cnt, b: two });
        let where_t = arena.add(TermNode::And {
            items: vec![eq, ge],
        });

        let mut vars: FxHashMap<Sym, u32> = FxHashMap::default();
        vars.insert(x_sym, 0);
        let t_compile = Instant::now();
        let jit_fn = compile(&arena, where_t, &vars).expect("compile");
        let dt_compile = t_compile.elapsed();

        let ctx = JitCtx::from_graph(&g);
        let all_cells: Vec<NodeID> = (0..n * n).map(|i| NodeID(i as u32)).collect();

        // JIT loop: evaluate the where-clause on every cell, 10 times.
        let t_jit = Instant::now();
        let mut jit_true: u64 = 0;
        for _ in 0..10 {
            for &c in &all_cells {
                jit_true += jit_fn.call_with_ctx(&ctx, &[c.0 as i64]) as u64;
            }
        }
        let dt_jit = t_jit.elapsed();

        // Interpreter loop.
        let t_interp = Instant::now();
        let mut interp_true: u64 = 0;
        for _ in 0..10 {
            for &c in &all_cells {
                let mut env: Env = SmallVec::new();
                env.push((x_sym, Value::Node(c)));
                let mut ectx = EvalCtx::new(&g, &ir);
                if evaluate(&arena, where_t, &mut env, &mut ectx).truthy() {
                    interp_true += 1;
                }
            }
        }
        let dt_interp = t_interp.elapsed();

        eprintln!(
            "\n=== JIT (graph access) vs interpreter (10×{} cells = {} evals) ===",
            n * n,
            10 * n * n
        );
        eprintln!("Compile once:       {:?}", dt_compile);
        eprintln!("JIT bytes:          {} bytes", jit_fn.code_len());
        eprintln!(
            "JIT total:          {:?} ({:?}/call)",
            dt_jit,
            dt_jit / (10 * n * n) as u32
        );
        eprintln!(
            "Interpreter total:  {:?} ({:?}/call)",
            dt_interp,
            dt_interp / (10 * n * n) as u32
        );
        let speedup = dt_interp.as_nanos() as f64 / dt_jit.as_nanos() as f64;
        eprintln!("JIT speedup:        {:.2}×", speedup);
        eprintln!(
            "Matches:            jit={} interp={}",
            jit_true, interp_true
        );
        assert_eq!(jit_true, interp_true);
    }

    /// Pure arithmetic bench, kept from the previous JIT iteration.
    #[test]
    #[ignore]
    fn bench_jit_vs_interpret() {
        use crate::graph::TypedGraph;
        use crate::term::{evaluate, Env, EvalCtx};
        use smallvec::SmallVec;
        use std::time::Instant;

        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let x = ir.intern("x");
        let y = ir.intern("y");
        let g = TypedGraph::new();
        let x_var = a.add(TermNode::Var { name: x });
        let y_var = a.add(TermNode::Var { name: y });
        let zero = a.add(TermNode::Lit {
            value: Value::Int(0),
        });
        let ten = a.add(TermNode::Lit {
            value: Value::Int(10),
        });
        let one = a.add(TermNode::Lit {
            value: Value::Int(1),
        });
        let neg_one = a.add(TermNode::Lit {
            value: Value::Int(-1),
        });
        let gt = a.add(TermNode::Gt { a: x_var, b: zero });
        let lt = a.add(TermNode::Lt { a: y_var, b: ten });
        let and = a.add(TermNode::And {
            items: vec![gt, lt],
        });
        let prod = a.add(TermNode::Times {
            items: vec![x_var, y_var],
        });
        let prod_plus = a.add(TermNode::Plus {
            items: vec![prod, one],
        });
        let ite = a.add(TermNode::IfThenElse {
            cond: and,
            then: prod_plus,
            other: neg_one,
        });

        let mut vars: FxHashMap<Sym, u32> = FxHashMap::default();
        vars.insert(x, 0);
        vars.insert(y, 1);

        let t_compile = Instant::now();
        let jit_fn = compile(&a, ite, &vars).expect("compile");
        let dt_compile = t_compile.elapsed();

        const N: u32 = 1_000_000;

        let t_jit = Instant::now();
        let mut acc: i64 = 0;
        for i in 0..N {
            acc = acc.wrapping_add(jit_fn.call_pure(&[i as i64 % 13, i as i64 % 7]));
        }
        let dt_jit = t_jit.elapsed();

        let t_interp = Instant::now();
        let mut acc2: i64 = 0;
        for i in 0..N {
            let mut env: Env = SmallVec::new();
            env.push((x, Value::Int((i % 13) as i64)));
            env.push((y, Value::Int((i % 7) as i64)));
            let mut ctx = EvalCtx::new(&g, &ir);
            let v = evaluate(&a, ite, &mut env, &mut ctx);
            let n = match v {
                Value::Int(n) => n,
                Value::Bool(b) => b as i64,
                _ => 0,
            };
            acc2 = acc2.wrapping_add(n);
        }
        let dt_interp = t_interp.elapsed();

        eprintln!(
            "\n=== JIT (pure arith) vs interpreter ({} iterations) ===",
            N
        );
        eprintln!("Compile once:       {:?}", dt_compile);
        eprintln!("JIT bytes:          {} bytes", jit_fn.code_len());
        eprintln!("JIT total:          {:?} ({:?}/call)", dt_jit, dt_jit / N);
        eprintln!(
            "Interpreter total:  {:?} ({:?}/call)",
            dt_interp,
            dt_interp / N
        );
        let speedup = dt_interp.as_nanos() as f64 / dt_jit.as_nanos() as f64;
        eprintln!("JIT speedup:        {:.2}×", speedup);
        assert_eq!(acc, acc2);
    }

    #[test]
    fn jit_enforces_max_depth_and_budget_on_unary_left_binary_and_nested_eq_trees() {
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let x = ir.intern("x");

        // 1. Deep unary Not chain (> MAX_DEPTH) must return None cleanly.
        let mut cur_not = a.add(TermNode::Lit {
            value: Value::Bool(true),
        });
        for _ in 0..40 {
            cur_not = a.add(TermNode::Not { arg: cur_not });
        }
        let vars = FxHashMap::default();
        assert!(compile(&a, cur_not, &vars).is_none());
        assert!(CompiledWhere::try_compile(&a, cur_not, &[x]).is_none());

        // 2. Deep left-associated Plus chain (> MAX_DEPTH) must return None cleanly,
        // while a moderate left-associated Plus chain (depth 8) compiles and matches.
        let one = a.add(TermNode::Lit {
            value: Value::Int(1),
        });
        let mut shallow_plus = one;
        for _ in 0..8 {
            shallow_plus = a.add(TermNode::Plus {
                items: vec![shallow_plus, one],
            });
        }
        assert_eq!(compile_pure(&a, shallow_plus, &[]), 9);

        let mut deep_plus = one;
        for _ in 0..40 {
            deep_plus = a.add(TermNode::Plus {
                items: vec![deep_plus, one],
            });
        }
        assert!(compile(&a, deep_plus, &vars).is_none());

        // 3. Deep nested Eq chain (which previously triggered O(2^d) blowup in cmp_reads_attr)
        // must bail out immediately within MAX_DEPTH / MAX_NODES.
        let mut deep_eq = a.add(TermNode::Lit {
            value: Value::Bool(true),
        });
        let true_lit = deep_eq;
        for _ in 0..40 {
            deep_eq = a.add(TermNode::Eq {
                a: deep_eq,
                b: true_lit,
            });
        }
        assert!(CompiledWhere::try_compile(&a, deep_eq, &[x]).is_none());
    }

    #[test]
    fn jit_or_short_circuit_normalizes_non_unit_truthy_values_to_one() {
        let mut a = TermArena::new();
        let two = a.add(TermNode::Lit {
            value: Value::Int(2),
        });
        let three = a.add(TermNode::Lit {
            value: Value::Int(3),
        });
        let zero = a.add(TermNode::Lit {
            value: Value::Int(0),
        });
        let or_short = a.add(TermNode::Or {
            items: vec![two, zero],
        });
        let and_full = a.add(TermNode::And {
            items: vec![two, three],
        });
        assert_eq!(
            compile_pure(&a, or_short, &[]),
            1,
            "Or short-circuiting on 2 must normalize result to 1"
        );
        assert_eq!(
            compile_pure(&a, and_full, &[]),
            1,
            "And ending on 3 must normalize result to 1"
        );
    }

    #[test]
    fn jit_compiled_where_rejects_type_confusion_and_attr_reads() {
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let x = ir.intern("x");
        let alive = ir.intern("Alive");
        let adj = ir.intern("adj");
        let flag = ir.intern("flag");

        let x_var = a.add(TermNode::Var { name: x });
        let zero = a.add(TermNode::Lit {
            value: Value::Int(0),
        });
        let one = a.add(TermNode::Lit {
            value: Value::Int(1),
        });
        let alive_lit = a.add(TermNode::Lit {
            value: Value::Str(alive),
        });

        // Node variable used directly as condition or inside Not must fall back
        // (NodeID(0) is truthy in interpreter, falsy as raw 0i64).
        assert!(CompiledWhere::try_compile(&a, x_var, &[x]).is_none());
        let not_x = a.add(TermNode::Not { arg: x_var });
        assert!(CompiledWhere::try_compile(&a, not_x, &[x]).is_none());

        // Cross-type Eq(Node, Int) and Eq(Int, Bool) must fall back.
        let eq_node_int = a.add(TermNode::Eq { a: x_var, b: zero });
        assert!(CompiledWhere::try_compile(&a, eq_node_int, &[x]).is_none());
        let true_lit = a.add(TermNode::Lit {
            value: Value::Bool(true),
        });
        let eq_int_bool = a.add(TermNode::Eq {
            a: one,
            b: true_lit,
        });
        assert!(compile(&a, eq_int_bool, &FxHashMap::default()).is_none());

        // Ordering comparison on Str (TypeOf(x) < "Alive") must fall back to lexicographic interpreter.
        let tof = a.add(TermNode::TypeOf { node: x_var });
        let lt_str = a.add(TermNode::Lt {
            a: tof,
            b: alive_lit,
        });
        assert!(CompiledWhere::try_compile(&a, lt_str, &[x]).is_none());

        // Attr reads inside or outside comparisons in CompiledWhere must fall back to interpreter.
        let attr = a.add(TermNode::Attr {
            node: x_var,
            key: flag,
        });
        assert!(CompiledWhere::try_compile(&a, attr, &[x]).is_none());
        let not_attr = a.add(TermNode::Not { arg: attr });
        assert!(CompiledWhere::try_compile(&a, not_attr, &[x]).is_none());
        let eq_attr = a.add(TermNode::Eq { a: attr, b: one });
        assert!(CompiledWhere::try_compile(&a, eq_attr, &[x]).is_none());

        // Well-typed graph predicates compile cleanly in CompiledWhere.
        let eq_type = a.add(TermNode::Eq {
            a: tof,
            b: alive_lit,
        });
        let nbrs = a.add(TermNode::Neighbours {
            node: x_var,
            edge_type: adj,
            any_type: false,
        });
        let cnt = a.add(TermNode::Count { source: nbrs });
        let gte_cnt = a.add(TermNode::Gte { a: cnt, b: one });
        let conj = a.add(TermNode::And {
            items: vec![eq_type, gte_cnt],
        });
        assert!(CompiledWhere::try_compile(&a, conj, &[x]).is_some());
    }

    #[test]
    fn phase63_compiled_where_falls_back_for_debug_overflow_constants() {
        let mut arena = TermArena::new();
        let max = arena.add(TermNode::Lit { value: Value::Int(i64::MAX) });
        let one = arena.add(TermNode::Lit { value: Value::Int(1) });
        let min = arena.add(TermNode::Lit { value: Value::Int(i64::MIN) });

        // Positive control: ordinary safe constant arithmetic still compiles.
        let two = arena.add(TermNode::Lit { value: Value::Int(2) });
        let three = arena.add(TermNode::Lit { value: Value::Int(3) });
        let five = arena.add(TermNode::Lit { value: Value::Int(5) });
        let safe_sum = arena.add(TermNode::Plus { items: vec![two, three] });
        let safe_eq = arena.add(TermNode::Eq { a: safe_sum, b: five });
        assert!(CompiledWhere::try_compile(&arena, safe_eq, &[]).is_some(),
            "safe constant arithmetic must remain JIT eligible");

        // Positive control: a standard TypeOf graph predicate has no integer
        // arithmetic and must remain on the graph-access JIT path.
        let mut ir = Interner::new();
        let x = ir.intern("x");
        let alive = ir.intern("Alive");
        let x_var = arena.add(TermNode::Var { name: x });
        let type_of = arena.add(TermNode::TypeOf { node: x_var });
        let alive_lit = arena.add(TermNode::Lit { value: Value::Str(alive) });
        let graph_eq = arena.add(TermNode::Eq { a: type_of, b: alive_lit });
        assert!(CompiledWhere::try_compile(&arena, graph_eq, &[x]).is_some(),
            "ordinary graph where predicates must remain JIT eligible");

        let sum = arena.add(TermNode::Plus { items: vec![max, one] });
        let eq = arena.add(TermNode::Eq { a: sum, b: min });
        assert!(CompiledWhere::try_compile(&arena, eq, &[]).is_none(),
            "overflowing constant predicates must use interpreter semantics");
        // Standalone JIT keeps its established machine-wrap semantics; the
        // rule-where adapter is the boundary that must preserve interpreter parity.
        let f = compile(&arena, eq, &FxHashMap::default()).expect("standalone JIT remains supported");
        assert_eq!(f.call_pure(&[]), 1);

        // Count(Neighbours(x)) is a runtime integer. Arithmetic involving it
        // can overflow even when the other operand is a literal, so it too
        // must remain on the interpreter path.
        let edge = ir.intern("edge");
        let x_var = arena.add(TermNode::Var { name: x });
        let neighbours = arena.add(TermNode::Neighbours { node: x_var, edge_type: edge, any_type: false });
        let count = arena.add(TermNode::Count { source: neighbours });
        let dynamic_sum = arena.add(TermNode::Plus { items: vec![count, max] });
        let zero = arena.add(TermNode::Lit { value: Value::Int(0) });
        let dynamic_predicate = arena.add(TermNode::Gt { a: dynamic_sum, b: zero });
        assert!(CompiledWhere::try_compile(&arena, dynamic_predicate, &[x]).is_none());

        // A depth-31 shared DAG has only 32 distinct nodes but exponentially
        // many root-to-leaf walks if the overflow scanner revisits each edge.
        // Its single shared budget must exhaust and conservatively decline.
        let truth = arena.add(TermNode::Lit { value: Value::Bool(true) });
        let mut shared = truth;
        for _ in 0..31 {
            shared = arena.add(TermNode::And { items: vec![shared, shared] });
        }
        let mut budget = MAX_NODES;
        assert!(known_overflow(&arena, shared, 0, &mut budget));
        assert_eq!(budget, 0, "shared DAG scan must stop at the shared node budget");
        assert!(CompiledWhere::try_compile(&arena, shared, &[]).is_none());
    }

    #[test]
    fn jit_thunks_reject_missing_and_out_of_range_node_ids() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let cell = ir.intern("Cell");
        let adj = ir.intern("adj");
        let score = ir.intern("score");
        let mut attrs: rustc_hash::FxHashMap<Sym, Value> = Default::default();
        attrs.insert(score, Value::Float(0.5));
        let n0 = g.insert_node(cell, attrs);

        let mut a = TermArena::new();
        let x = ir.intern("x");
        let x_var = a.add(TermNode::Var { name: x });
        let tof = a.add(TermNode::TypeOf { node: x_var });
        let attr = a.add(TermNode::Attr {
            node: x_var,
            key: score,
        });
        let nbrs = a.add(TermNode::Neighbours {
            node: x_var,
            edge_type: adj,
            any_type: false,
        });
        let cnt = a.add(TermNode::Count { source: nbrs });

        let mut vars = FxHashMap::default();
        vars.insert(x, 0);
        let f_tof = compile(&a, tof, &vars).expect("compile TypeOf");
        let f_attr = compile(&a, attr, &vars).expect("compile Attr");
        let f_cnt = compile(&a, cnt, &vars).expect("compile Count(Neighbours)");

        let ctx = JitCtx::from_graph(&g);
        // Out-of-range and missing NodeIDs return -1 for TypeOf (never colliding with Sym(0))
        // and 0 for Attr / Count(Neighbours) without panicking or truncating to u32(0).
        for bad_id in [-1i64, 999i64, (u32::MAX as i64) + 1 + (n0.0 as i64)] {
            assert_eq!(f_tof.call_with_ctx(&ctx, &[bad_id]), -1);
            assert_eq!(f_attr.call_with_ctx(&ctx, &[bad_id]), 0);
            assert_eq!(f_cnt.call_with_ctx(&ctx, &[bad_id]), 0);
        }
        // Fractional float 0.5 is not coerced to integer 1.
        assert_eq!(f_attr.call_with_ctx(&ctx, &[n0.0 as i64]), 0);
    }
}
