"""LLVM IR knowledge as a static lookup teacher.

Same callable shape as ``DictionaryTeacher`` / ``WikiTeacher`` / the LLM
self-teacher: a ``(question_text) -> payload`` callable the agent's
impasse-resolver spawns and learns from. Returns ``learn_from_teacher``-
shaped payloads when asked about an LLVM concept it knows, ``None``
otherwise.

The role in the chain: dictionary → wiki → **llvm** → LLM. Place after
wiki (Wikipedia covers some LLVM terms but spottily) and before the LLM
fallback (LLM costs money; this is free + faster + authoritative for
the concepts it covers).

This is Phase 1 of the LLVM ingestion curriculum (see LLVM_LEARNING.md
at the gamma-substrate root): ~25 foundational concepts covering IR
structure (Module / Function / BasicBlock / Instruction / Value / Type)
and a handful of canonical instructions (add / mul / load / store /
icmp / br / phi / alloca / getelementptr). Each payload teaches the
agent one Frame in the ``llvm_ir`` Microtheory under ``compiler_ir``.

Each entry's description is concise and authoritative — the source is
the LLVM Language Reference. The agent absorbs them once; on every
subsequent question of the same shape, the agent's own Frame layer
answers without re-teaching.

Phases 2-7 (full instruction set, optimization passes, ISA descriptions,
codegen) follow the same pattern with larger knowledge bases.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .wiki_teacher import extract_subject       # share subject extraction


# ----------------------------------------------------------------------------
# data shape
# ----------------------------------------------------------------------------

@dataclass(frozen=True)
class LLVMEntry:
    """One LLVM concept the teacher knows.

    ``phrase`` is the canonical trigger; aliases route to the same entry
    via ``_ALIASES``. ``binding_pattern`` is one of the agent's three
    standard Frame shapes (see ``learn_from_teacher`` doc on
    ``CuriousAgent``):

      - ``predicate_of_subject``   : "X is a Y"           (most concepts)
      - ``function_of_subject``    : "f(X)"               (unary ops)
      - ``function_of_two_subjects``: "f(X, Y)"           (binary ops)
    """
    phrase: str
    description: str
    binding_pattern: str
    microtheory: str = "llvm_ir"
    genl_mt: str = "compiler_ir"


# ----------------------------------------------------------------------------
# the knowledge base — Phase 1 foundational concepts
# ----------------------------------------------------------------------------
#
# Source: LLVM Language Reference (https://llvm.org/docs/LangRef.html).
# Descriptions are deliberately tight — the agent learns the canonical
# definition; nuance can be elaborated by later Frames that depend on
# these.

_ENTRIES: list[LLVMEntry] = [
    # --- IR structure ---
    LLVMEntry(
        phrase="llvm ir",
        description="LLVM Intermediate Representation: a typed, SSA-form, "
                    "RISC-like virtual instruction set used as the common "
                    "language for LLVM's analyses, transformations, and "
                    "code generators.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="llvm module",
        description="The top-level container in LLVM IR. Holds global "
                    "variables, function declarations and definitions, "
                    "type definitions, target triple, and metadata.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="llvm function",
        description="A named code unit in an LLVM Module with a return "
                    "type, parameter list, calling convention, and a body "
                    "of basic blocks. May be declared (external) or "
                    "defined (with body).",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="basic block",
        description="A maximal straight-line sequence of LLVM instructions "
                    "ending in exactly one terminator. Has a label and is "
                    "the unit of control-flow target. The entry block of "
                    "a function has no predecessors.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="llvm instruction",
        description="A single operation in LLVM IR. Has an opcode, "
                    "operands (Values), and possibly a result Value with "
                    "a Type. Instructions are organised into Basic Blocks.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="llvm value",
        description="Any first-class entity in LLVM IR that produces a "
                    "result: a constant, a function argument, the output "
                    "of an instruction, a global variable, or a basic "
                    "block (when used as a branch target).",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="llvm type",
        description="The classification of an LLVM Value's data. Every "
                    "Value has a Type known at compile time. Categories: "
                    "integer (iN), floating-point, pointer, vector, array, "
                    "struct, function, void, label, metadata, token.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="ssa",
        description="Static Single Assignment: a code form where every "
                    "variable is assigned exactly once and defined before "
                    "use. Makes def-use chains explicit; LLVM IR is in "
                    "SSA form. Multiple control-flow paths producing a "
                    "value join via phi instructions.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="terminator",
        description="The last instruction of a basic block. Determines "
                    "where control flow goes next: ret, br, switch, "
                    "indirectbr, invoke, callbr, resume, catchswitch, "
                    "catchret, cleanupret, or unreachable.",
        binding_pattern="predicate_of_subject",
    ),

    # --- Types ---
    LLVMEntry(
        phrase="integer type",
        description="A scalar integer of an arbitrary bit width N, "
                    "written iN (e.g. i1 boolean, i8 byte, i32, i64). "
                    "Bit width is part of the type; the interpretation "
                    "as signed or unsigned depends on the operation.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="floating point type",
        description="IEEE-754 floating-point types: half (16-bit), bfloat, "
                    "float (32-bit), double (64-bit), fp128 (128-bit), "
                    "x86_fp80, ppc_fp128. Distinct from integer types.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="pointer type",
        description="An address in some address space, written ptr "
                    "(opaque, since LLVM 15) or T* (typed, deprecated). "
                    "Pointers carry an address space (default 0).",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="function type",
        description="The type of a function value: return type, parameter "
                    "types, and a varargs flag. Written like "
                    "<ret>(<params>) — e.g. i32(i32, ptr).",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="void type",
        description="The empty return type — used for functions that "
                    "produce no value. Cannot appear as a value's type "
                    "(no SSA register holds it).",
        binding_pattern="predicate_of_subject",
    ),

    # --- Canonical instructions ---
    LLVMEntry(
        phrase="add",
        description="LLVM integer addition. add iN X, Y returns X + Y. "
                    "Optional flags nsw/nuw mark signed/unsigned overflow "
                    "as undefined behaviour (poison value).",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="sub",
        description="LLVM integer subtraction. sub iN X, Y returns "
                    "X - Y. Optional nsw/nuw mark signed/unsigned "
                    "overflow as undefined behaviour (poison value).",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="mul",
        description="LLVM integer multiplication. mul iN X, Y returns "
                    "X * Y (modulo 2^N). Optional nsw/nuw flags mark "
                    "signed/unsigned overflow as undefined.",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="udiv",
        description="LLVM unsigned integer division. udiv iN X, Y "
                    "returns X / Y treating both as unsigned. Division "
                    "by zero is undefined behaviour. exact flag marks "
                    "remainder-of-zero division for the optimiser.",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="sdiv",
        description="LLVM signed integer division. sdiv iN X, Y returns "
                    "X / Y truncating toward zero, treating both as "
                    "two's-complement signed. Division by zero and "
                    "INT_MIN/-1 are undefined.",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="urem",
        description="LLVM unsigned integer remainder. urem iN X, Y "
                    "returns X mod Y treating both as unsigned. "
                    "Division by zero is undefined.",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="srem",
        description="LLVM signed integer remainder. srem iN X, Y "
                    "returns X mod Y where (X/Y)*Y + (X%Y) = X using "
                    "truncated division. Sign of result follows X.",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="fneg",
        description="LLVM floating-point negation. fneg F X returns -X. "
                    "Optional fast-math flags (nnan/ninf/nsz/arcp/...) "
                    "permit relaxed IEEE-754 semantics.",
        binding_pattern="function_of_subject",
    ),
    LLVMEntry(
        phrase="fadd",
        description="LLVM floating-point addition. fadd F X, Y returns "
                    "X + Y per IEEE-754. Optional fast-math flags "
                    "permit reassociation, NaN/inf assumptions, "
                    "reciprocal approximations.",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="fsub",
        description="LLVM floating-point subtraction. fsub F X, Y "
                    "returns X - Y per IEEE-754. Fast-math flags apply.",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="fmul",
        description="LLVM floating-point multiplication. fmul F X, Y "
                    "returns X * Y per IEEE-754. Fast-math flags apply.",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="fdiv",
        description="LLVM floating-point division. fdiv F X, Y returns "
                    "X / Y per IEEE-754. Fast-math flag arcp permits "
                    "X * (1/Y) substitution.",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="frem",
        description="LLVM floating-point remainder. frem F X, Y returns "
                    "the remainder of X / Y. Semantics match libm's "
                    "fmod (not IEEE-754 remainder).",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="load",
        description="Read a value of a given Type from a memory address. "
                    "load T, ptr P returns the value of type T at address "
                    "P. May carry alignment, volatile, and atomicity "
                    "annotations.",
        binding_pattern="function_of_subject",
    ),
    LLVMEntry(
        phrase="store",
        description="Write a Value to a memory address. store V, ptr P "
                    "writes V at address P. May carry alignment, "
                    "volatile, and atomicity annotations. No result.",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="icmp",
        description="Integer compare. icmp <pred> iN X, Y returns i1. "
                    "Predicates: eq, ne, ugt, uge, ult, ule, sgt, sge, "
                    "slt, sle (signed/unsigned variants for ordering).",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="br",
        description="Branch — the simplest control-flow terminator. "
                    "Conditional: br i1 cond, label %then, label %else. "
                    "Unconditional: br label %target. Targets must be "
                    "basic blocks within the same function.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="phi",
        description="The SSA merge instruction. phi T [v1, %bb1], "
                    "[v2, %bb2], ... selects the value corresponding to "
                    "the predecessor block control entered from. Must "
                    "appear at the start of its basic block.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="alloca",
        description="Stack-allocate space for a value. alloca T returns "
                    "a pointer (in alloca address space, default 0) to "
                    "freshly-allocated stack memory of size sizeof(T). "
                    "Lifetime ends at function return.",
        binding_pattern="function_of_subject",
    ),
    LLVMEntry(
        phrase="getelementptr",
        description="Compute an address from a base pointer and a sequence "
                    "of indices, navigating the pointee's type structure. "
                    "Pure address arithmetic — does not read memory. "
                    "Abbreviated GEP. The most common cause of confusion "
                    "in LLVM IR.",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="ret",
        description="Function return — a terminator. ret T V returns "
                    "value V of type T; ret void returns from a void "
                    "function. The function's return type must match.",
        binding_pattern="function_of_subject",
    ),

    # --- Bitwise instructions ---
    LLVMEntry(
        phrase="and",
        description="LLVM bitwise AND. and iN X, Y returns the bitwise "
                    "conjunction of X and Y. Operates on integer types "
                    "and vectors of integers.",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="or",
        description="LLVM bitwise OR. or iN X, Y returns the bitwise "
                    "disjunction of X and Y.",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="xor",
        description="LLVM bitwise XOR. xor iN X, Y returns the bitwise "
                    "exclusive-or of X and Y. xor X, -1 inverts (logical "
                    "NOT).",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="shl",
        description="LLVM logical shift left. shl iN X, Y returns X "
                    "shifted left by Y bits. Optional nsw/nuw mark "
                    "signed/unsigned overflow as undefined.",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="lshr",
        description="LLVM logical shift right. lshr iN X, Y returns X "
                    "shifted right by Y bits, filling with zeros. "
                    "Unsigned semantics.",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="ashr",
        description="LLVM arithmetic shift right. ashr iN X, Y returns "
                    "X shifted right by Y bits, sign-extending. Preserves "
                    "the sign of two's-complement integers.",
        binding_pattern="function_of_two_subjects",
    ),

    # --- Atomic memory ---
    LLVMEntry(
        phrase="atomicrmw",
        description="Atomic read-modify-write. atomicrmw <op> ptr P, V "
                    "atomically performs a binop on *P with V and "
                    "returns the OLD value at P. Ops: xchg, add, sub, "
                    "and, nand, or, xor, max, min, umax, umin, fadd, "
                    "fsub, fmax, fmin. Requires an ordering.",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="cmpxchg",
        description="Atomic compare-and-swap. cmpxchg ptr P, V_cmp, "
                    "V_new atomically: if *P == V_cmp store V_new. "
                    "Returns { value_at_P, success_bool }. Requires "
                    "success and failure memory orderings. Foundation "
                    "of lock-free algorithms.",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="fence",
        description="Memory ordering barrier. fence <ordering> enforces "
                    "the given memory ordering between atomic operations "
                    "in this thread (and across threads for sequentially "
                    "consistent fences). No data motion; pure ordering "
                    "constraint.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="memory ordering",
        description="The synchronisation guarantee on an atomic op. "
                    "Kinds (weakest to strongest): unordered, monotonic, "
                    "acquire, release, acq_rel, seq_cst. Determines what "
                    "other ops can be reordered around this one.",
        binding_pattern="predicate_of_subject",
    ),

    # --- Conversion instructions ---
    LLVMEntry(
        phrase="trunc",
        description="Truncate an integer to a smaller integer type. "
                    "trunc iN X to iM drops the high bits. M < N.",
        binding_pattern="function_of_subject",
    ),
    LLVMEntry(
        phrase="zext",
        description="Zero-extend an integer to a larger integer type. "
                    "zext iN X to iM pads high bits with zeros. M > N.",
        binding_pattern="function_of_subject",
    ),
    LLVMEntry(
        phrase="sext",
        description="Sign-extend an integer to a larger integer type. "
                    "sext iN X to iM pads high bits with the sign bit. "
                    "M > N.",
        binding_pattern="function_of_subject",
    ),
    LLVMEntry(
        phrase="bitcast",
        description="Reinterpret a value's bits as a different type "
                    "without changing the bits. bitcast T1 X to T2. T1 "
                    "and T2 must have the same size. Used heavily for "
                    "pointer-type punning before opaque pointers.",
        binding_pattern="function_of_subject",
    ),
    LLVMEntry(
        phrase="ptrtoint",
        description="Convert a pointer to an integer. ptrtoint ptr X to "
                    "iN. The integer is the address; size depends on "
                    "the data layout.",
        binding_pattern="function_of_subject",
    ),
    LLVMEntry(
        phrase="inttoptr",
        description="Convert an integer to a pointer. inttoptr iN X to "
                    "ptr. Treats the integer as an address.",
        binding_pattern="function_of_subject",
    ),
    LLVMEntry(
        phrase="sitofp",
        description="Convert a signed integer to a floating-point value. "
                    "sitofp iN X to F. Rounds per the target FP "
                    "environment.",
        binding_pattern="function_of_subject",
    ),
    LLVMEntry(
        phrase="uitofp",
        description="Convert an unsigned integer to a floating-point "
                    "value. uitofp iN X to F. Rounds per the target FP "
                    "environment.",
        binding_pattern="function_of_subject",
    ),
    LLVMEntry(
        phrase="fptosi",
        description="Convert a floating-point value to a signed integer. "
                    "fptosi F X to iN. Truncates toward zero. Out-of-"
                    "range values produce poison.",
        binding_pattern="function_of_subject",
    ),
    LLVMEntry(
        phrase="fptoui",
        description="Convert a floating-point value to an unsigned "
                    "integer. fptoui F X to iN. Truncates toward zero. "
                    "Out-of-range values produce poison.",
        binding_pattern="function_of_subject",
    ),
    LLVMEntry(
        phrase="fptrunc",
        description="Convert a floating-point value to a smaller FP "
                    "type. fptrunc F1 X to F2 with F1 wider than F2. "
                    "Rounds per the target FP environment.",
        binding_pattern="function_of_subject",
    ),
    LLVMEntry(
        phrase="fpext",
        description="Extend a floating-point value to a wider FP type. "
                    "fpext F1 X to F2 with F2 wider than F1. Exact — "
                    "wider types representable supersets of narrower.",
        binding_pattern="function_of_subject",
    ),
    LLVMEntry(
        phrase="addrspacecast",
        description="Cast a pointer between address spaces. "
                    "addrspacecast ptr addrspace(N) X to ptr "
                    "addrspace(M). Semantics target-defined; on most "
                    "targets the address bit pattern may differ.",
        binding_pattern="function_of_subject",
    ),
    LLVMEntry(
        phrase="freeze",
        description="Stop poison/undef propagation. freeze T X returns "
                    "an arbitrary fixed concrete value when X is poison "
                    "or undef, X otherwise. Useful when a use needs a "
                    "well-defined value but the producer might be "
                    "undefined.",
        binding_pattern="function_of_subject",
    ),

    # --- More instructions ---
    LLVMEntry(
        phrase="fcmp",
        description="Floating-point compare. fcmp <pred> F X, Y returns "
                    "i1. Predicates: oeq, ogt, oge, olt, ole, one, ord "
                    "(ordered: neither is NaN); ueq, ugt, uge, ult, ule, "
                    "une, uno (unordered: either is NaN). Plus true/false.",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="select",
        description="Three-way value select. select i1 cond, T A, T B "
                    "returns A if cond is true, else B. Branchless "
                    "conditional value.",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="call",
        description="Call a function. call ret_type @fn(args) invokes "
                    "the named function with the given arguments and "
                    "returns its result. May carry calling convention, "
                    "fast-math flags, and function attributes.",
        binding_pattern="function_of_subject",
    ),
    LLVMEntry(
        phrase="invoke",
        description="Call a function with exception-aware control flow. "
                    "invoke ret_type @fn(args) to label %normal unwind "
                    "label %unwind. Returns normally to %normal; an "
                    "uncaught exception jumps to %unwind. Acts as a "
                    "terminator.",
        binding_pattern="function_of_subject",
    ),
    LLVMEntry(
        phrase="switch",
        description="Multi-way branch — a terminator. switch iN val, "
                    "label %default [iN c1, label %b1 ; iN c2, "
                    "label %b2 ; ...]. Dispatches on val against each "
                    "case; falls to %default on no match.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="unreachable",
        description="A terminator indicating control flow cannot reach "
                    "this point. The optimizer may treat reaching it as "
                    "undefined behaviour. Common after explicit "
                    "exhaustive dispatch.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="extractvalue",
        description="Read a field from an aggregate value (struct or "
                    "array). extractvalue T agg, idx0, idx1, ... walks "
                    "the type structure. Result is the typed field.",
        binding_pattern="function_of_subject",
    ),
    LLVMEntry(
        phrase="insertvalue",
        description="Produce a new aggregate value with one field "
                    "replaced. insertvalue T agg, ET v, idx0, idx1, ... "
                    "returns a new aggregate of type T identical to agg "
                    "except at the indexed field.",
        binding_pattern="function_of_two_subjects",
    ),

    # --- Vector instructions ---
    LLVMEntry(
        phrase="extractelement",
        description="Read one lane from a vector. extractelement <N x T> "
                    "V, iM idx returns the element at index idx. "
                    "Out-of-range index is undefined.",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="insertelement",
        description="Produce a new vector with one lane replaced. "
                    "insertelement <N x T> V, T elt, iM idx returns a "
                    "new vector identical to V except at lane idx, "
                    "which holds elt. Out-of-range index is undefined.",
        binding_pattern="function_of_two_subjects",
    ),
    LLVMEntry(
        phrase="shufflevector",
        description="Permute lanes across two vectors. shufflevector "
                    "<N x T> A, <N x T> B, <M x i32> mask returns an "
                    "M-element vector whose i-th lane is A[mask[i]] if "
                    "mask[i] < N, B[mask[i]-N] if < 2N, undef if -1.",
        binding_pattern="function_of_two_subjects",
    ),

    # --- More control flow ---
    LLVMEntry(
        phrase="indirectbr",
        description="Indirect branch — a terminator. indirectbr ptr "
                    "addr, [label %b1, label %b2, ...] jumps to the "
                    "block whose address equals addr. addr must be a "
                    "blockaddress of one of the listed blocks. Used "
                    "for computed goto.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="callbr",
        description="Call that can branch to multiple targets — a "
                    "terminator. callbr ret @fn(args) to label %normal "
                    "[label %other1, label %other2, ...]. Used for "
                    "inline asm with multiple outputs / labels.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="resume",
        description="Resume propagation of a caught exception — a "
                    "terminator. resume T excval transfers control to "
                    "the caller's exception handler, continuing the "
                    "unwind started by an invoke.",
        binding_pattern="predicate_of_subject",
    ),

    # --- Exception handling ---
    LLVMEntry(
        phrase="landingpad",
        description="The first instruction of an invoke's unwind block. "
                    "landingpad T <clauses> describes the personality "
                    "function's catch/filter clauses and produces the "
                    "exception value(s). Required at the entry of an "
                    "unwind handler.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="catchpad",
        description="Begin a catch handler in Windows SEH-style "
                    "exception handling. catchpad within %parent "
                    "[<args>] sets up a token used by catchret to "
                    "transfer control. Counterpart to landingpad for "
                    "the funclet personality.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="cleanuppad",
        description="Begin a cleanup handler in Windows SEH-style "
                    "exception handling. cleanuppad within %parent "
                    "[<args>] sets up a token used by cleanupret to "
                    "transfer control after finally-style cleanup runs.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="catchret",
        description="Terminator that exits a catch handler back to "
                    "normal control flow. catchret from %catchpad to "
                    "label %target. Counterpart to catchpad.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="cleanupret",
        description="Terminator that exits a cleanup handler. "
                    "cleanupret from %cleanuppad unwind [to caller | "
                    "label %target]. Resumes unwinding after finally-"
                    "style cleanup runs.",
        binding_pattern="predicate_of_subject",
    ),

    # --- Aggregate types ---
    LLVMEntry(
        phrase="struct type",
        description="A heterogeneous, fixed-layout aggregate. { T1, T2, "
                    "... } enumerates field types in order. May be "
                    "literal or named (identified by name). Fields are "
                    "accessed by getelementptr / extractvalue.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="array type",
        description="A homogeneous, fixed-length sequence of one type. "
                    "[N x T] is an array of N elements of type T. "
                    "Accessed by getelementptr / extractvalue.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="vector type",
        description="A SIMD-style fixed-length sequence of a scalar "
                    "type. <N x T> for N elements of T. Operations on "
                    "vectors apply element-wise. Used for "
                    "vectorisation and SIMD codegen.",
        binding_pattern="predicate_of_subject",
    ),

    # --- Constants & globals ---
    LLVMEntry(
        phrase="constant",
        description="An LLVM Value whose contents are fixed at compile "
                    "time. Includes literal integers / floats / strings, "
                    "named constants, undef, poison, null, and "
                    "constant expressions built from other constants.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="null",
        description="The null pointer constant — `null` (or "
                    "`@G = ... = ptr null`). Has type ptr (pointer in "
                    "address space 0); addrspacecast'able to other "
                    "spaces. Dereferencing is undefined.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="undef",
        description="An unspecified value of any type — the compiler "
                    "may choose any bit pattern at its discretion (and "
                    "may choose different ones at different uses). "
                    "Distinct from poison (less constrained than undef).",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="zeroinitializer",
        description="A constant of any type whose bytes are all zero. "
                    "Convenience for aggregate / vector / pointer zero "
                    "values. Written `zeroinitializer`.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="global variable",
        description="A module-scope Value allocated for the lifetime of "
                    "the program. Has linkage, an optional initialiser, "
                    "address space, alignment, and attributes. Accessed "
                    "by name (@G).",
        binding_pattern="predicate_of_subject",
    ),

    # --- Calling convention & linkage ---
    LLVMEntry(
        phrase="calling convention",
        description="The ABI rule for passing arguments, receiving "
                    "results, and saving/restoring registers across a "
                    "call. LLVM-named conventions: ccc (C, default), "
                    "fastcc, coldcc, tailcc, anyregcc, and many "
                    "target-specific variants.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="linkage",
        description="How a symbol's name resolves across translation "
                    "units. Common kinds: external (visible across TUs), "
                    "internal (TU-local), private (named-but-local), "
                    "weak (overridable), common (uninitialized weak), "
                    "available_externally.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="function attribute",
        description="A flag or value attached to a function or call "
                    "that informs analyses and codegen. Examples: "
                    "noinline, alwaysinline, readnone, readonly, "
                    "norecurse, nounwind, nofree, willreturn, cold, "
                    "hot, optsize.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="address space",
        description="A numbered address namespace for pointers. Space 0 "
                    "is the default (target's normal flat space); other "
                    "spaces have target-specific semantics (e.g. shared, "
                    "constant, private on GPUs). Pointer types carry "
                    "their address space.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="metadata",
        description="Non-semantic annotations attached to instructions, "
                    "modules, and globals. Carries debug info, "
                    "optimization hints, type info, range constraints. "
                    "Written !name. Stripped does not change behaviour.",
        binding_pattern="predicate_of_subject",
    ),

    # --- Concepts ---
    LLVMEntry(
        phrase="def use chain",
        description="The graph linking each Value's definition (the "
                    "instruction that produced it) to every Use (the "
                    "operand slot referencing it). LLVM IR makes def-use "
                    "chains explicit and traversable in O(1) per step.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="poison value",
        description="A result that came from an operation with undefined "
                    "behaviour (e.g. signed overflow under nsw). "
                    "Propagates: any operation consuming poison produces "
                    "poison. Distinct from undef (less constrained).",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="dominator",
        description="In a control-flow graph, a block A dominates B "
                    "iff every path from entry to B passes through A. "
                    "The dominator relation underpins SSA construction, "
                    "Mem2Reg, LICM, and most code-motion passes.",
        binding_pattern="predicate_of_subject",
    ),
    LLVMEntry(
        phrase="optimization pass",
        description="A traversal of LLVM IR that analyses or transforms "
                    "it. Categories: analysis passes (compute "
                    "information), transformation passes (rewrite IR), "
                    "and utility passes. Composed into pipelines; "
                    "ordering matters.",
        binding_pattern="predicate_of_subject",
    ),
]


# Phrase aliases — multiple ways the agent might ask about the same
# concept all route to the same canonical entry. The lookup canonicalises
# before reading _ENTRIES_BY_PHRASE.
_ALIASES: dict[str, str] = {
    "llvm intermediate representation": "llvm ir",
    "module": "llvm module",
    "function": "llvm function",
    "instruction": "llvm instruction",
    "value": "llvm value",
    "type": "llvm type",
    "static single assignment": "ssa",
    "i1": "integer type",
    "i8": "integer type",
    "i32": "integer type",
    "i64": "integer type",
    "iN": "integer type",
    "float": "floating point type",
    "double": "floating point type",
    "ptr": "pointer type",
    "pointer": "pointer type",
    "void": "void type",
    "addition": "add",
    "multiplication": "mul",
    "integer add": "add",
    "integer multiply": "mul",
    "memory load": "load",
    "memory store": "store",
    "integer compare": "icmp",
    "compare": "icmp",
    "branch": "br",
    "conditional branch": "br",
    "phi node": "phi",
    "phi instruction": "phi",
    "stack allocation": "alloca",
    "gep": "getelementptr",
    "address computation": "getelementptr",
    "return": "ret",
    "definition use chain": "def use chain",
    "ssa form": "ssa",
    "poison": "poison value",
    "undefined value": "poison value",
    # bitwise
    "bitwise and": "and",
    "bitwise or": "or",
    "bitwise xor": "xor",
    "shift left": "shl",
    "logical shift right": "lshr",
    "arithmetic shift right": "ashr",
    # conversion
    "truncate": "trunc",
    "zero extend": "zext",
    "sign extend": "sext",
    "pointer to integer": "ptrtoint",
    "integer to pointer": "inttoptr",
    "signed int to float": "sitofp",
    "unsigned int to float": "uitofp",
    "float to signed int": "fptosi",
    "float to unsigned int": "fptoui",
    # other ops
    "float compare": "fcmp",
    "floating point compare": "fcmp",
    "function call": "call",
    "tail call": "call",
    "exception call": "invoke",
    "multi-way branch": "switch",
    "extract field": "extractvalue",
    "insert field": "insertvalue",
    # types
    "struct": "struct type",
    "array": "array type",
    "vector": "vector type",
    "fixed vector": "vector type",
    # constants & globals
    "constant value": "constant",
    "null pointer": "null",
    "zero initializer": "zeroinitializer",
    "global": "global variable",
    "global constant": "global variable",
    # calling convention & linkage
    "ccc": "calling convention",
    "fastcc": "calling convention",
    "external linkage": "linkage",
    "internal linkage": "linkage",
    "weak linkage": "linkage",
    "attribute": "function attribute",
    "noinline": "function attribute",
    "addrspace": "address space",
    "named metadata": "metadata",
    "debug metadata": "metadata",
    # concepts
    "dominator tree": "dominator",
    "dominance": "dominator",
    "pass": "optimization pass",
    "analysis pass": "optimization pass",
    "transformation pass": "optimization pass",
    # arithmetic
    "subtract": "sub",
    "integer sub": "sub",
    "unsigned div": "udiv",
    "unsigned divide": "udiv",
    "signed div": "sdiv",
    "signed divide": "sdiv",
    "unsigned mod": "urem",
    "unsigned remainder": "urem",
    "signed mod": "srem",
    "signed remainder": "srem",
    "fp negate": "fneg",
    "float negate": "fneg",
    "fp add": "fadd",
    "float add": "fadd",
    "fp sub": "fsub",
    "float subtract": "fsub",
    "fp mul": "fmul",
    "float multiply": "fmul",
    "fp div": "fdiv",
    "float divide": "fdiv",
    "fp rem": "frem",
    "float remainder": "frem",
    # atomic
    "atomic rmw": "atomicrmw",
    "atomic read modify write": "atomicrmw",
    "compare exchange": "cmpxchg",
    "compare and swap": "cmpxchg",
    "cas": "cmpxchg",
    "memory barrier": "fence",
    "memory fence": "fence",
    "atomic ordering": "memory ordering",
    "ordering": "memory ordering",
    # conversion
    "fp trunc": "fptrunc",
    "float truncate": "fptrunc",
    "fp ext": "fpext",
    "float extend": "fpext",
    "address space cast": "addrspacecast",
    "stop poison": "freeze",
    # vector
    "extract lane": "extractelement",
    "extract vector element": "extractelement",
    "insert lane": "insertelement",
    "insert vector element": "insertelement",
    "shuffle": "shufflevector",
    "vector permute": "shufflevector",
    # control flow
    "indirect branch": "indirectbr",
    "computed goto": "indirectbr",
    "callbr branch": "callbr",
    "resume unwind": "resume",
    # exception handling
    "landing pad": "landingpad",
    "catch pad": "catchpad",
    "cleanup pad": "cleanuppad",
    "catch return": "catchret",
    "cleanup return": "cleanupret",
}


# Normalise alias keys to lowercase so capital-letter aliases (iN, GEP)
# match `_canonicalise`'s lowercased query.
_ALIASES = {k.lower(): v for k, v in _ALIASES.items()}

_ENTRIES_BY_PHRASE: dict[str, LLVMEntry] = {e.phrase: e for e in _ENTRIES}


# ----------------------------------------------------------------------------
# lookup
# ----------------------------------------------------------------------------

_SUFFIX_NOISE = (" instruction", " type", " op", " operation")


def _canonicalise(phrase: str) -> str:
    """Normalise a phrase for lookup. Trims whitespace, lowercases,
    routes aliases to their canonical form, and strips common qualifier
    suffixes ("X instruction", "X type") that would otherwise miss."""
    norm = phrase.strip().lower()
    if norm in _ALIASES:
        return _ALIASES[norm]
    for suffix in _SUFFIX_NOISE:
        if norm.endswith(suffix):
            stripped = norm[: -len(suffix)].strip()
            if stripped in _ALIASES:
                return _ALIASES[stripped]
            # Defer to lookup() which will also try direct entry match.
            return stripped
    return norm


def lookup(phrase: str) -> LLVMEntry | None:
    """Find an entry by phrase. Returns None on miss."""
    key = _canonicalise(phrase)
    if key in _ENTRIES_BY_PHRASE:
        return _ENTRIES_BY_PHRASE[key]
    # One more chance: try the un-canonicalised form against the raw
    # entry phrases (some entries' phrases happen to match aliases).
    raw = phrase.strip().lower()
    if raw in _ENTRIES_BY_PHRASE:
        return _ENTRIES_BY_PHRASE[raw]
    return None


# ----------------------------------------------------------------------------
# payload construction
# ----------------------------------------------------------------------------

def entry_to_answer(entry: LLVMEntry) -> str:
    """Plain-text rendering for the ``answer`` field of the payload —
    what the agent memoises and what a downstream caller / human sees."""
    return entry.description


def entry_to_payload(entry: LLVMEntry, subject: str) -> dict:
    """``learn_from_teacher``-shaped payload installing the concept as a
    Frame in the ``llvm_ir`` Microtheory under ``compiler_ir``.

    The agent will: install the Mt if absent, create a sign for the
    phrase in its lexicon, build a Frame using ``binding_pattern``, and
    realise it with a generated ``taught_<phrase>`` concept whose
    capability is the description. On the next question of the same
    shape, the agent answers from its own Frame layer — no re-teach.
    """
    answer = entry_to_answer(entry)
    phrase = subject.lower().strip()
    return {
        "answer": answer,
        "learn": [{
            "phrase": phrase,
            "microtheory": entry.microtheory,
            "genl_mt": entry.genl_mt,
            "description": f"llvm:{entry.phrase}",
            "binding_pattern": entry.binding_pattern,
            "slot_name": "of",
            "source": "llvm_langref",
        }],
    }


# ----------------------------------------------------------------------------
# the callable
# ----------------------------------------------------------------------------

@dataclass
class LLVMTeacher:
    """Static LLVM IR knowledge teacher.

    Chain placement: dictionary → wiki → **llvm** → LLM. Place this
    after the generic teachers so it only fires on questions the
    generic chain didn't resolve. Cheap: in-memory hash lookup, no
    network, no API cost.

    Knobs:
      - ``microtheory`` — override the Mt new phrases land in.
      - ``fallback`` — optional next-in-chain callable when this teacher
        doesn't know a phrase.
    """
    microtheory: str = "llvm_ir"
    genl_mt: str = "compiler_ir"
    fallback: Callable[[str], Any] | None = None
    # diagnostics
    hits: int = field(default=0, init=False)
    misses: int = field(default=0, init=False)
    last_subject: str | None = field(default=None, init=False)
    last_entry: LLVMEntry | None = field(default=None, init=False)

    def lookup(self, phrase: str) -> LLVMEntry | None:
        return lookup(phrase)

    def __call__(self, question_text: str) -> Any:
        subject = extract_subject(question_text)
        self.last_subject = subject
        entry = self.lookup(subject)
        if entry is None:
            self.misses += 1
            self.last_entry = None
            if self.fallback is not None:
                return self.fallback(question_text)
            return None
        self.hits += 1
        self.last_entry = entry
        return entry_to_payload(entry, subject=subject)


__all__ = [
    "LLVMTeacher",
    "LLVMEntry",
    "entry_to_answer",
    "entry_to_payload",
    "lookup",
]
