"""Assemble and execute x86-64 ASM produced by the agent's codegen.

Given the AT&T-syntax assembly text `domains/llvm_ir_to_asm.py` emits,
this module:

  1. Writes the ASM to a temp file
  2. Runs `gcc -shared -nostartfiles -fPIC` to assemble + link into
     a position-independent shared library
  3. Loads the library via ctypes
  4. Returns the exported function as a Python callable

End-to-end this lets us prove the agent's compiler-theory beliefs
*all the way down to machine code*: pick random inputs, interpret the
LLVM IR for the expected value, call the assembled function with the
same inputs, assert the answers match. The "correctness by construction"
claim in the codegen module becomes a tested invariant.

Tools used (all stock on Linux): `gcc` (8.0+), `ctypes`. No external
Python packages beyond stdlib.

Per the architecture rule this is a world-adapter: text bytes (ASM) in,
machine bytes (shared object) out, then concrete function calls. No
graph-state decisions, no compiler-theory reasoning here — those live
inside the substrate where they belong.
"""
from __future__ import annotations

import ctypes
import os
import subprocess
import tempfile


def assemble_and_load(asm_text: str, function_name: str,
                      n_args: int = 1,
                      arg_type: type = ctypes.c_int32,
                      ret_type: type = ctypes.c_int32):
    """Assemble `asm_text` (AT&T syntax x86-64), load the resulting
    shared library, and return the exported `function_name` as a
    Python callable.

    Args:
      asm_text: AT&T-syntax x86-64 assembly. Must declare the function
        global (e.g. `.globl foo`) and end with `ret`.
      function_name: exported symbol to bind.
      n_args: number of i32 args the function takes.
      arg_type / ret_type: ctypes types for args / return. Default
        `c_int32` matches the codegen's `i32` ABI.

    Returns: a ctypes function pointer with signature
      (arg_type, …) → ret_type. Call it with Python ints.

    Lifecycle: the underlying .so is kept in a temp directory that
    leaks at process exit (fine for tests). The library is kept alive
    via a closure reference on the returned callable.
    """
    tmpdir = tempfile.mkdtemp(prefix="ozma_x86_64_")
    asm_path = os.path.join(tmpdir, "code.s")
    so_path = os.path.join(tmpdir, "code.so")

    with open(asm_path, "w") as f:
        f.write(asm_text)
        f.write("\n")
        # GNU note marking the stack as non-executable. Without this,
        # modern Linux refuses to load the .so for code that didn't
        # opt-out of the executable stack explicitly.
        f.write('.section .note.GNU-stack,"",@progbits\n')

    # `-nostartfiles` skips crt; `-shared -fPIC` makes a position-
    # independent shared object. `-x assembler` tells gcc the input
    # is assembly text regardless of extension.
    cmd = [
        "gcc", "-shared", "-fPIC", "-nostartfiles",
        "-o", so_path, "-x", "assembler", asm_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"gcc failed to assemble:\n"
            f"  cmd: {' '.join(cmd)}\n"
            f"  stderr:\n{result.stderr}\n"
            f"  asm:\n{asm_text}"
        )

    lib = ctypes.CDLL(so_path)
    fn = getattr(lib, function_name)
    fn.argtypes = (arg_type,) * n_args
    fn.restype = ret_type

    # Keep the library object alive through the closure — ctypes
    # function pointers can become invalid if the lib is GC'd.
    fn._owning_lib = lib  # type: ignore[attr-defined]
    return fn


__all__ = ["assemble_and_load"]
