"""Phase 6.8 — binary-encoder Term heads + end-to-end ELF.

Validates the smallest correctness claims first:
  - Bytes is byte-typed; concatenating a text Surface is rejected.
  - U8 / U16LE / U32LE / U64LE / LEB128 encode integers as the spec'd bytes.
  - None-propagates the same way Cat does (one impasse, not many).
Then the big claim: assemble a real ELF64 header + program header + tiny
x86_64 code segment entirely out of Bytes / U8 / U32LE / U64LE Term-trees,
write it, execute it, the exit code matches what we encoded.
"""
from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from substrate import (Bytes, Cat, LEB128, Lit, Surface, U8, U16LE, U32LE,
                       U64LE)


# --------------------------------------------------------------------------
# integer encoders
# --------------------------------------------------------------------------

def _eval(term):
    return term.evaluate({}, None)


def test_u8_encodes_low_byte():
    assert _eval(U8(expr=Lit(0))) == {"kind": "bytes", "payload": b"\x00"}
    assert _eval(U8(expr=Lit(0x7F))) == {"kind": "bytes", "payload": b"\x7f"}
    # mask wraps
    assert _eval(U8(expr=Lit(0x1FF))) == {"kind": "bytes", "payload": b"\xff"}


def test_u16le_encodes_two_bytes_little_endian():
    assert _eval(U16LE(expr=Lit(0x1234))) == {
        "kind": "bytes", "payload": b"\x34\x12"}


def test_u32le_encodes_four_bytes_little_endian():
    assert _eval(U32LE(expr=Lit(0xDEADBEEF))) == {
        "kind": "bytes", "payload": b"\xef\xbe\xad\xde"}


def test_u64le_encodes_eight_bytes_little_endian():
    assert _eval(U64LE(expr=Lit(0x400078))) == {
        "kind": "bytes", "payload": b"\x78\x00\x40\x00\x00\x00\x00\x00"}


def test_leb128_unsigned():
    # canonical examples from DWARF / WASM
    assert _eval(LEB128(expr=Lit(0))) == {"kind": "bytes", "payload": b"\x00"}
    assert _eval(LEB128(expr=Lit(127))) == {
        "kind": "bytes", "payload": b"\x7f"}
    assert _eval(LEB128(expr=Lit(128))) == {
        "kind": "bytes", "payload": b"\x80\x01"}
    assert _eval(LEB128(expr=Lit(624485))) == {
        "kind": "bytes", "payload": b"\xe5\x8e\x26"}


# --------------------------------------------------------------------------
# Bytes
# --------------------------------------------------------------------------

def test_bytes_concatenates_byte_terms():
    out = _eval(Bytes(items=(
        U8(expr=Lit(0x7F)),
        U8(expr=Lit(ord("E"))),
        U16LE(expr=Lit(0x1234)),
    )))
    assert out == {"kind": "bytes", "payload": b"\x7fE\x34\x12"}


def test_bytes_accepts_raw_bytes_literal():
    out = _eval(Bytes(items=(Lit(b"\x90\x90"), U8(expr=Lit(0xC3)))))
    assert out == {"kind": "bytes", "payload": b"\x90\x90\xc3"}


def test_bytes_rejects_text_surface():
    # Cat is for text; Bytes refuses to silently coerce.
    with pytest.raises(ValueError):
        _eval(Bytes(items=(Surface(kind="text", payload="hi"),)))


def test_bytes_none_propagates_short_circuit():
    # Bytes(None, …) → None (same contract as Cat — no parallel impasses).
    out = _eval(Bytes(items=(Lit(None),)))
    assert out is None


# --------------------------------------------------------------------------
# end-to-end: a real ELF64 binary
# --------------------------------------------------------------------------

def _build_elf(exit_code: int) -> bytes:
    """Construct a minimal ELF64 executable that calls sys_exit(exit_code).
    The entire structure is a Bytes Term-tree — Python only triggers
    evaluation."""
    LOAD = 0x400000
    EHSIZE = 64
    PHSIZE = 56
    code_offset = EHSIZE + PHSIZE
    entry = LOAD + code_offset

    code = Bytes(items=(
        # mov rdi, imm32 (zero-extends): 48 c7 c7 <imm32>
        U8(expr=Lit(0x48)), U8(expr=Lit(0xC7)), U8(expr=Lit(0xC7)),
        U32LE(expr=Lit(exit_code)),
        # mov rax, 60: 48 c7 c0 3c 00 00 00
        U8(expr=Lit(0x48)), U8(expr=Lit(0xC7)), U8(expr=Lit(0xC0)),
        U32LE(expr=Lit(60)),
        # syscall: 0f 05
        U8(expr=Lit(0x0F)), U8(expr=Lit(0x05)),
    ))
    code_bytes = _eval(code)["payload"]
    filesz = code_offset + len(code_bytes)

    e_ident = Bytes(items=(
        U8(expr=Lit(0x7F)), U8(expr=Lit(ord("E"))),
        U8(expr=Lit(ord("L"))), U8(expr=Lit(ord("F"))),
        U8(expr=Lit(2)),     # ELFCLASS64
        U8(expr=Lit(1)),     # ELFDATA2LSB
        U8(expr=Lit(1)),     # EV_CURRENT
        U8(expr=Lit(0)),     # OSABI
        U8(expr=Lit(0)),     # ABIVERSION
        Lit(b"\0\0\0\0\0\0\0"),
    ))
    elf_header = Bytes(items=(
        e_ident,
        U16LE(expr=Lit(2)),               # ET_EXEC
        U16LE(expr=Lit(0x3E)),            # EM_X86_64
        U32LE(expr=Lit(1)),
        U64LE(expr=Lit(entry)),
        U64LE(expr=Lit(EHSIZE)),          # phoff
        U64LE(expr=Lit(0)),               # shoff
        U32LE(expr=Lit(0)),               # flags
        U16LE(expr=Lit(EHSIZE)),
        U16LE(expr=Lit(PHSIZE)),
        U16LE(expr=Lit(1)),
        U16LE(expr=Lit(0)),
        U16LE(expr=Lit(0)),
        U16LE(expr=Lit(0)),
    ))
    ph = Bytes(items=(
        U32LE(expr=Lit(1)),               # PT_LOAD
        U32LE(expr=Lit(5)),               # PF_R | PF_X
        U64LE(expr=Lit(0)),
        U64LE(expr=Lit(LOAD)),
        U64LE(expr=Lit(LOAD)),
        U64LE(expr=Lit(filesz)),
        U64LE(expr=Lit(filesz)),
        U64LE(expr=Lit(0x1000)),
    ))
    return _eval(Bytes(items=(elf_header, ph, code)))["payload"]


def test_elf_header_starts_with_magic():
    binary = _build_elf(exit_code=42)
    assert binary[:4] == b"\x7fELF"
    assert binary[4] == 2          # ELFCLASS64
    assert binary[5] == 1          # ELFDATA2LSB


def test_elf_header_size_matches_spec():
    binary = _build_elf(exit_code=42)
    # 64 (ELF header) + 56 (one PH) + 16 (code) = 136 bytes
    # code = (rex 1 + opcode 2 + imm32 4) × 2 movs + (syscall 2) = 16
    assert len(binary) == 64 + 56 + 16


@pytest.mark.skipif(sys.platform != "linux",
                    reason="ELF executes on Linux only")
def test_substrate_built_elf_runs_and_exits_with_encoded_value(tmp_path):
    # Compute factorial(5) here so the value flowing into the binary comes
    # from a fresh calculation, not a constant the test wrote down.
    def fact(n):
        return 1 if n == 0 else n * fact(n - 1)
    answer = fact(5)
    assert answer == 120

    binary = _build_elf(exit_code=answer)
    out = tmp_path / "factorial5"
    out.write_bytes(binary)
    os.chmod(out, stat.S_IRWXU)

    proc = subprocess.run([str(out)], capture_output=True)
    assert proc.returncode == answer, (
        f"binary returned {proc.returncode}, expected {answer}")
