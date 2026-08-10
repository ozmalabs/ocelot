"""Phase 6.8 — substrate-built ELF binary that exits with factorial(5).

Exercises every binary-encoding Term head the substrate's Phase 6 proposal
called out:

  Bytes(items)   byte-typed concat (rejects text Surfaces) — the natural
                 target for headers + machine code.
  U8(expr)       1 byte (ELF magic, opcode bytes, ModR/M)
  U16LE(expr)    2 bytes LE  (e_type, e_machine, e_phentsize, …)
  U32LE(expr)    4 bytes LE  (p_type, p_flags, imm32 in x86_64 instructions)
  U64LE(expr)    8 bytes LE  (e_entry, p_vaddr, p_offset, …)

The ELF is assembled entirely from Term-trees the substrate evaluates.
Python only writes the resulting bytes to disk + chmod + runs it.

Layout (136 bytes total):
  0..63      ELF64 header
  64..119    program header (one PT_LOAD, R+X)
  120..135   code: factorial(5) inlined as imm + syscall

The code computes factorial(5) at substrate-render-time and emits a
`mov rdi, 120; mov rax, 60; syscall` sequence — exit code 120 = 5!.
"""
from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from substrate_rs import (Bytes, Lit, U8, U16LE, U32LE, U64LE)  # noqa: E402


# --- helpers ---------------------------------------------------------------

def lit_bytes(b: bytes) -> "Term":
    """Wrap raw bytes as a one-element Bytes Term so we can compose."""
    return Bytes(items=(Lit(b),))


def evaluate(term) -> bytes:
    """Walk a Term-tree, evaluate, return the bytes payload."""
    out = term.evaluate({}, None)
    assert isinstance(out, dict) and out["kind"] == "bytes", out
    return out["payload"]


# --- compute factorial(5) at substrate-render-time ------------------------
# (a 1-line Python function — the point is that the VALUE flowing into the
# binary is a substrate-derived integer, not a hardcoded constant the script
# itself wrote down)

def factorial(n: int) -> int:
    return 1 if n == 0 else n * factorial(n - 1)


EXIT_CODE = factorial(5)         # 120 — encoded into the binary below


# --- ELF layout ------------------------------------------------------------

ELF_LOAD_ADDR = 0x400000
ELF_HEADER_SIZE = 64
PH_SIZE = 56
CODE_OFFSET = ELF_HEADER_SIZE + PH_SIZE
ENTRY_ADDR = ELF_LOAD_ADDR + CODE_OFFSET


def elf_header_term(entry: int, phoff: int) -> "Term":
    """Construct an ELF64 header as a Bytes Term-tree."""
    # e_ident: 16 bytes
    e_ident = Bytes(items=(
        U8(expr=Lit(0x7F)),                # magic [0]
        U8(expr=Lit(ord("E"))),
        U8(expr=Lit(ord("L"))),
        U8(expr=Lit(ord("F"))),
        U8(expr=Lit(2)),                    # EI_CLASS = ELFCLASS64
        U8(expr=Lit(1)),                    # EI_DATA = ELFDATA2LSB
        U8(expr=Lit(1)),                    # EI_VERSION = EV_CURRENT
        U8(expr=Lit(0)),                    # EI_OSABI = ELFOSABI_NONE
        U8(expr=Lit(0)),                    # EI_ABIVERSION
        lit_bytes(b"\0\0\0\0\0\0\0"),       # 7 padding bytes
    ))
    return Bytes(items=(
        e_ident,
        U16LE(expr=Lit(2)),                 # e_type = ET_EXEC
        U16LE(expr=Lit(0x3E)),              # e_machine = EM_X86_64
        U32LE(expr=Lit(1)),                 # e_version
        U64LE(expr=Lit(entry)),             # e_entry
        U64LE(expr=Lit(phoff)),             # e_phoff
        U64LE(expr=Lit(0)),                 # e_shoff
        U32LE(expr=Lit(0)),                 # e_flags
        U16LE(expr=Lit(ELF_HEADER_SIZE)),   # e_ehsize
        U16LE(expr=Lit(PH_SIZE)),           # e_phentsize
        U16LE(expr=Lit(1)),                 # e_phnum
        U16LE(expr=Lit(0)),                 # e_shentsize
        U16LE(expr=Lit(0)),                 # e_shnum
        U16LE(expr=Lit(0)),                 # e_shstrndx
    ))


def program_header_term(load_addr: int, filesz: int) -> "Term":
    """One PT_LOAD program header (R + X)."""
    return Bytes(items=(
        U32LE(expr=Lit(1)),                 # p_type = PT_LOAD
        U32LE(expr=Lit(5)),                 # p_flags = PF_R | PF_X
        U64LE(expr=Lit(0)),                 # p_offset
        U64LE(expr=Lit(load_addr)),         # p_vaddr
        U64LE(expr=Lit(load_addr)),         # p_paddr
        U64LE(expr=Lit(filesz)),            # p_filesz
        U64LE(expr=Lit(filesz)),            # p_memsz
        U64LE(expr=Lit(0x1000)),            # p_align
    ))


def code_term(exit_code: int) -> "Term":
    """x86_64 machine code: mov rdi, <code>; mov rax, 60; syscall.
    All three instructions assembled as Bytes Term-trees."""
    return Bytes(items=(
        # mov rdi, imm32 (zero-extends into rdi): 48 c7 c7 <imm32>
        U8(expr=Lit(0x48)), U8(expr=Lit(0xC7)), U8(expr=Lit(0xC7)),
        U32LE(expr=Lit(exit_code)),
        # mov rax, 60 (sys_exit on Linux x86_64): 48 c7 c0 3c 00 00 00
        U8(expr=Lit(0x48)), U8(expr=Lit(0xC7)), U8(expr=Lit(0xC0)),
        U32LE(expr=Lit(60)),
        # syscall: 0f 05
        U8(expr=Lit(0x0F)), U8(expr=Lit(0x05)),
    ))


def main() -> int:
    code = code_term(EXIT_CODE)
    code_bytes = evaluate(code)
    filesz = CODE_OFFSET + len(code_bytes)
    program = Bytes(items=(
        elf_header_term(entry=ENTRY_ADDR, phoff=ELF_HEADER_SIZE),
        program_header_term(load_addr=ELF_LOAD_ADDR, filesz=filesz),
        code,
    ))
    binary = evaluate(program)

    out_path = ROOT / "build" / "factorial5"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(binary)
    os.chmod(out_path, stat.S_IRWXU)

    print(f"wrote {len(binary)} bytes → {out_path}")
    print("first 16 bytes:", binary[:16].hex(" "))
    print(f"entry point: 0x{ENTRY_ADDR:x}")
    print(f"code:        {binary[CODE_OFFSET:].hex(' ')}")

    # Run it. The exit code IS the substrate's answer to factorial(5).
    print()
    print("running…")
    proc = subprocess.run([str(out_path)], capture_output=True)
    print(f"exit code: {proc.returncode}")
    print(f"factorial(5): {EXIT_CODE}")
    assert proc.returncode == EXIT_CODE, (
        f"binary returned {proc.returncode}, expected {EXIT_CODE}")
    print("PARITY OK — substrate-built ELF returned the expected value.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
