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
        if cmp_reads_attr(arena, where_idx) {
            // A comparison reads an attr that may be a Float; the i64 JIT can't compare floats
            // correctly. Let the interpreter handle the whole where (numeric coercion).
            return None;
        }
        let var_indices: FxHashMap<Sym, u32> = binding_vars
            .iter()
            .enumerate()
            .map(|(i, s)| (*s, i as u32))
            .collect();
        let jit = compile(arena, where_idx, &var_indices)?;
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
    let needs_ctx = scan_needs_ctx(arena, root);

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

    emit_term(&mut ops, arena, root, var_indices, 0)?;

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

/// True iff the Term-tree references any graph state — used to decide
/// which `call_*` variant the caller must use.
fn scan_needs_ctx(arena: &TermArena, idx: TermIdx) -> bool {
    match arena.get(idx) {
        TermNode::TypeOf { .. } | TermNode::Attr { .. } => true,
        TermNode::Count { source } => {
            // Count(Neighbours(...)) uses ctx.
            matches!(arena.get(*source), TermNode::Neighbours { .. })
                || scan_needs_ctx(arena, *source)
        }
        TermNode::Plus { items }
        | TermNode::Times { items }
        | TermNode::And { items }
        | TermNode::Or { items } => items.iter().any(|i| scan_needs_ctx(arena, *i)),
        TermNode::Minus { a, b }
        | TermNode::Lt { a, b }
        | TermNode::Lte { a, b }
        | TermNode::Gt { a, b }
        | TermNode::Gte { a, b }
        | TermNode::Eq { a, b } => scan_needs_ctx(arena, *a) || scan_needs_ctx(arena, *b),
        TermNode::Neg { arg } | TermNode::Abs { arg } | TermNode::Not { arg } => {
            scan_needs_ctx(arena, *arg)
        }
        TermNode::IfThenElse { cond, then, other } => {
            scan_needs_ctx(arena, *cond)
                || scan_needs_ctx(arena, *then)
                || scan_needs_ctx(arena, *other)
        }
        _ => false,
    }
}

/// True iff the subtree contains an `Attr` (whose runtime value may be a Float).
fn subtree_has_attr(arena: &TermArena, idx: TermIdx) -> bool {
    match arena.get(idx) {
        TermNode::Attr { .. } => true,
        TermNode::Count { source } => subtree_has_attr(arena, *source),
        TermNode::Plus { items }
        | TermNode::Times { items }
        | TermNode::And { items }
        | TermNode::Or { items } => items.iter().any(|i| subtree_has_attr(arena, *i)),
        TermNode::Minus { a, b }
        | TermNode::Lt { a, b }
        | TermNode::Lte { a, b }
        | TermNode::Gt { a, b }
        | TermNode::Gte { a, b }
        | TermNode::Eq { a, b } => subtree_has_attr(arena, *a) || subtree_has_attr(arena, *b),
        TermNode::Neg { arg } | TermNode::Abs { arg } | TermNode::Not { arg } => {
            subtree_has_attr(arena, *arg)
        }
        TermNode::IfThenElse { cond, then, other } => {
            subtree_has_attr(arena, *cond)
                || subtree_has_attr(arena, *then)
                || subtree_has_attr(arena, *other)
        }
        _ => false,
    }
}

/// True iff any COMPARISON node (Eq / Lt / Lte / Gt / Gte) reads an `Attr` in its operands.
/// Such a comparison can compare FLOAT attrs, and the JIT compares in i64 (`cmp`), which is wrong
/// for floats (0.317 and 0.6 both truncate to 0). When this holds we refuse to JIT the whole where
/// and let the interpreter — which compares numerically with int/float coercion — handle it.
fn cmp_reads_attr(arena: &TermArena, idx: TermIdx) -> bool {
    match arena.get(idx) {
        TermNode::Eq { a, b }
        | TermNode::Lt { a, b }
        | TermNode::Lte { a, b }
        | TermNode::Gt { a, b }
        | TermNode::Gte { a, b } => {
            subtree_has_attr(arena, *a)
                || subtree_has_attr(arena, *b)
                || cmp_reads_attr(arena, *a)
                || cmp_reads_attr(arena, *b)
        }
        TermNode::And { items }
        | TermNode::Or { items }
        | TermNode::Plus { items }
        | TermNode::Times { items } => items.iter().any(|i| cmp_reads_attr(arena, *i)),
        TermNode::Minus { a, b } => cmp_reads_attr(arena, *a) || cmp_reads_attr(arena, *b),
        TermNode::Neg { arg } | TermNode::Abs { arg } | TermNode::Not { arg } => {
            cmp_reads_attr(arena, *arg)
        }
        TermNode::Count { source } => cmp_reads_attr(arena, *source),
        TermNode::IfThenElse { cond, then, other } => {
            cmp_reads_attr(arena, *cond)
                || cmp_reads_attr(arena, *then)
                || cmp_reads_attr(arena, *other)
        }
        _ => false,
    }
}

const CTX_SLOT: i32 = -8;
const ARG_SLOT_BASE: i32 = -16;
const TEMP_SLOT_BASE: i32 = -72;
const MAX_DEPTH: i32 = 32;

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
) -> Option<()> {
    if depth >= MAX_DEPTH {
        return None;
    }
    match arena.get(idx) {
        TermNode::Lit { value } => emit_lit(ops, value),
        TermNode::Var { name } => emit_var(ops, vars, *name),

        TermNode::Plus { items } if items.len() == 2 => {
            emit_binop(ops, arena, items[0], items[1], vars, depth, |o| {
                dynasm!(o; .arch x64; add rax, [rbp + (TEMP_SLOT_BASE - 8 * depth)]);
            })
        }
        TermNode::Times { items } if items.len() == 2 => {
            emit_binop(ops, arena, items[0], items[1], vars, depth, |o| {
                dynasm!(o; .arch x64; imul rax, [rbp + (TEMP_SLOT_BASE - 8 * depth)]);
            })
        }
        TermNode::Minus { a, b } => {
            // Need a - b. Compute a, save; compute b; rax holds b; subtract a's slot from b.
            // a - b = -(b - a) = neg(b - rax-of-a) ... simpler: compute b, sub from saved a.
            emit_term(ops, arena, *a, vars, depth)?;
            dynasm!(ops; .arch x64; mov [rbp + temp_slot(depth)], rax);
            emit_term(ops, arena, *b, vars, depth + 1)?;
            dynasm!(ops; .arch x64
                ; mov r10, rax
                ; mov rax, [rbp + temp_slot(depth)]
                ; sub rax, r10
            );
            Some(())
        }
        TermNode::Neg { arg } => {
            emit_term(ops, arena, *arg, vars, depth)?;
            dynasm!(ops; .arch x64; neg rax);
            Some(())
        }
        TermNode::Abs { arg } => {
            emit_term(ops, arena, *arg, vars, depth)?;
            dynasm!(ops; .arch x64
                ; mov r10, rax
                ; sar r10, 63
                ; xor rax, r10
                ; sub rax, r10
            );
            Some(())
        }

        TermNode::Lt { a, b } => emit_cmp(ops, arena, *a, *b, vars, depth, CmpKind::Lt),
        TermNode::Lte { a, b } => emit_cmp(ops, arena, *a, *b, vars, depth, CmpKind::Lte),
        TermNode::Gt { a, b } => emit_cmp(ops, arena, *a, *b, vars, depth, CmpKind::Gt),
        TermNode::Gte { a, b } => emit_cmp(ops, arena, *a, *b, vars, depth, CmpKind::Gte),
        TermNode::Eq { a, b } => emit_cmp(ops, arena, *a, *b, vars, depth, CmpKind::Eq),

        TermNode::Not { arg } => {
            emit_term(ops, arena, *arg, vars, depth)?;
            dynasm!(ops; .arch x64
                ; test rax, rax
                ; sete al
                ; movzx rax, al
            );
            Some(())
        }
        TermNode::And { items } => {
            emit_short_circuit(ops, arena, items, vars, depth, /*want_true=*/ false)
        }
        TermNode::Or { items } => {
            emit_short_circuit(ops, arena, items, vars, depth, /*want_true=*/ true)
        }

        TermNode::IfThenElse { cond, then, other } => {
            emit_term(ops, arena, *cond, vars, depth)?;
            let else_lbl = ops.new_dynamic_label();
            let end_lbl = ops.new_dynamic_label();
            dynasm!(ops; .arch x64
                ; test rax, rax
                ; jz =>else_lbl
            );
            emit_term(ops, arena, *then, vars, depth)?;
            dynasm!(ops; .arch x64
                ; jmp =>end_lbl
                ; =>else_lbl
            );
            emit_term(ops, arena, *other, vars, depth)?;
            dynasm!(ops; .arch x64; =>end_lbl);
            Some(())
        }

        // --- graph access ---
        TermNode::TypeOf { node } => {
            emit_term(ops, arena, *node, vars, depth)?;
            // rax = node-id (as i64). Call thunk_type_of(ctx, node).
            let thunk_addr = thunk_type_of as usize as i64;
            dynasm!(ops; .arch x64
                ; mov rsi, rax
                ; mov rdi, [rbp + CTX_SLOT]
                ; mov rax, QWORD thunk_addr
                ; call rax
            );
            Some(())
        }
        TermNode::Attr { node, key } => {
            emit_term(ops, arena, *node, vars, depth)?;
            let key_int = key.0 as i64;
            let thunk_addr = thunk_attr_int as usize as i64;
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
                emit_term(ops, arena, *node, vars, depth)?;
                let et: i64 = if *any_type { 0 } else { edge_type.0 as i64 };
                let thunk_addr = thunk_neighbour_count as usize as i64;
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
    combine: F,
) -> Option<()>
where
    F: FnOnce(&mut dynasmrt::x64::Assembler),
{
    emit_term(ops, arena, a, vars, depth)?;
    dynasm!(ops; .arch x64; mov [rbp + temp_slot(depth)], rax);
    emit_term(ops, arena, b, vars, depth + 1)?;
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
    kind: CmpKind,
) -> Option<()> {
    emit_term(ops, arena, a, vars, depth)?;
    dynasm!(ops; .arch x64; mov [rbp + temp_slot(depth)], rax);
    emit_term(ops, arena, b, vars, depth + 1)?;
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
    want_true: bool,
) -> Option<()> {
    if items.is_empty() {
        let v: i64 = if want_true { 0 } else { 1 };
        dynasm!(ops; .arch x64; mov rax, QWORD v);
        return Some(());
    }
    let end_lbl = ops.new_dynamic_label();
    for (i, item) in items.iter().enumerate() {
        emit_term(ops, arena, *item, vars, depth)?;
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
        ; setne al
        ; movzx rax, al
        ; =>end_lbl
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
        return 0;
    }
    let graph = (*ctx).graph;
    if graph.is_null() {
        return 0;
    }
    let nid = NodeID(node as u32);
    if !(*graph).has_node(nid) {
        return 0;
    }
    (*graph).node(nid).type_.0 as i64
}

unsafe extern "sysv64" fn thunk_attr_int(ctx: *const JitCtx, node: i64, key_sym: i64) -> i64 {
    if ctx.is_null() {
        return 0;
    }
    let graph = (*ctx).graph;
    if graph.is_null() {
        return 0;
    }
    let nid = NodeID(node as u32);
    if !(*graph).has_node(nid) {
        return 0;
    }
    let key = Sym(key_sym as u32);
    match (*graph).node(nid).attrs.get(&key) {
        Some(Value::Int(n)) => *n,
        Some(Value::Bool(b)) => {
            if *b {
                1
            } else {
                0
            }
        }
        // Float attrs: the JIT compares in i64, so read the integer part — a
        // flag stored as 1.0 must read as 1 (else `Eq(Attr,1)` silently fails).
        // JIT'd wheres only ever compare against INTEGER Lits (a Float Lit makes
        // emit_lit bail to the interpreter), so integer-valued floats — the
        // realistic case (flags, counts) — compare exactly; the interpreter
        // handles any fractional-threshold where (it has a Float Lit and isn't
        // JIT'd). Without this case a Float fell through `_ => 0`.
        Some(Value::Float(f)) => *f as i64,
        // Str values resolve to their Sym so JIT'd comparison sees the
        // same i64 the interpreter would.
        Some(Value::Str(s)) => s.0 as i64,
        Some(Value::Node(n)) => n.0 as i64,
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
    let nid = NodeID(node as u32);
    let et = if edge_type_sym == 0 {
        None
    } else {
        Some(Sym(edge_type_sym as u32))
    };
    (*graph).out_edges_slice(nid, et).len() as i64
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
}
