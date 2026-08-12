"""dimgen_p1_expressibility.py — AR-3 for
docs/research/engine_substrate/DIMGEN_PROGRAM_IR_PREREG.md.

MEASUREMENT CODE, not agent logic (same class as `domains/rule_ir.py`'s
"diagnostic data" precedent). For each of the five shipped
`DimensionGenerator` codebook nodes (`seeds/shape_decode_loop.json`,
verbatim in PREREG §2), writes ONE pointwise Python function computing the
SAME per-cell arithmetic as its Rust counterpart in
`runners/dsl/src/shape_decode.rs` (`rotate90_once` / `reflect_once` /
`scale_pow2_once` / `modular_step_once`) and runs it through the real,
unmodified `emit_prog_ir` harness
(`RULE_SIGNATURE_TO_RUST_RESULTS.md` §1's own instrument). Reports
ok/blockers per generator — no engine call, pure AST-walk, runs standalone.
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from domains.prog_ir_emit import emit_prog_ir  # noqa: E402


def rotation90_point(r, c, min_r, min_c, max_r0):
    """Mirrors `rotate90_once` (shape_decode.rs:605-622), per cell."""
    r0 = r - min_r
    c0 = c - min_c
    new_r = c0
    new_c = max_r0 - r0
    return (new_r, new_c)


def reflection_point(v, max_v):
    """Mirrors `reflect_once` (shape_decode.rs:629-637), per cell — used
    by BOTH reflection_r and reflection_c (same map, different axis)."""
    return max_v - v


def scale2_point(v, min_v):
    """Mirrors `scale_pow2_once` (shape_decode.rs:659-683), per cell."""
    return (v - min_v) * 2


def modular_point(v, modulus):
    """Mirrors `modular_step_once` (shape_decode.rs:713-735), per cell."""
    return (v + 1) % modulus


GENERATORS = [
    ("rotation90",   "kind:rotation90",   rotation90_point),
    ("reflection_r", "kind:reflection_r", reflection_point),
    ("reflection_c", "kind:reflection_c", reflection_point),
    ("scale2",       "kind:scale2",       scale2_point),
    ("cycle4",       "kind:modular",      modular_point),
]


def main() -> int:
    print(f"{'generator':<14} {'rust kind':<20} {'ok':<6} blockers")
    print("-" * 70)
    go_count = 0
    for name, kind, fn in GENERATORS:
        r = emit_prog_ir(inspect.getsource(fn))
        ok = bool(r.get("ok"))
        go_count += int(ok)
        print(f"{name:<14} {kind:<20} {str(ok):<6} {r.get('blockers')}")
    print("-" * 70)
    print(f"P1-expressible: {go_count}/5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
