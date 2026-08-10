#!/usr/bin/env python
"""arc6_valuelayer_patch — apply/revert the ARM-C (adapter) half of the
ARC6 value-layer rung, so the three arms differ by exactly one thing each.

The rung has TWO halves and they are measured separately (prereg A1.2):

  * the ENGINE half (`runners/dsl/src/*.rs`) — `Value::List`, the PyO3 and
    persistence boundaries, `ProgEval` type-faithfulness, and the two DSL
    list-comprehension Terms. Arm B is baseline Python on that engine.
  * the ADAPTER half, applied by THIS script — mechanical I/O only:
    (a) stop discarding a non-scalar `got`/`fu_got` before the verdict
        RULE can read it, and
    (b) encode a spec row's container types faithfully across the `Lit`
        JSON boundary (`_wire`), which JSON otherwise erases.

`seeds/program_synthesis.json` is NOT touched by either half. The verdict
rule `ps_row_pass` (`Eq(Attr(r,"got"), Attr(r,"expected"))`) is byte
unchanged; it was always the right decision, and it was always a Rule.

  python scripts/arc6_valuelayer_patch.py apply|revert|status
"""
from __future__ import annotations

import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PSY = os.path.join(ROOT, "domains", "prog_synthesis.py")
MOVES = os.path.join(ROOT, "domains", "prog_moves.py")
RETR = os.path.join(ROOT, "domains", "prog_retrieval.py")

_WIRE_DEF = '''
def _wire(v):
    """TYPE-FAITHFUL WIRE ENCODING of a spec value for the `Lit` boundary.
    Mechanical translation; no decision.

    `Substrate.evaluate()` serialises its Term dict with `json.dumps`, and
    JSON has ONE array type — so a Python `tuple` and a Python `list`
    arrive at `persist::decode_value` indistinguishable, and a BARE array
    decodes as `Value::Tuple`. That was harmless while list and tuple were
    one `Value::Tuple`. Under the ARC6 value layer it silently retypes
    every list-valued expected output as a TUPLE, and `SynthEnumerate`
    then rejects the correct list-producing candidate it just built —
    measured: 161/272/413/436/450/460 all evaluate to the exactly-correct
    LIST and were still reported `enumerate_failed`.

    The engine already has an exact tagged form for this
    (`__tuple__`/`__list__`/`__set__`/`__fset__`, `persist.rs`); this is
    its write side. A BARE array is deliberately left meaning `Tuple`, so
    every seed-resident `Lit` array literal is byte-unchanged.
    """
    if isinstance(v, tuple):
        return {"__tuple__": [_wire(x) for x in v]}
    if isinstance(v, list):
        return {"__list__": [_wire(x) for x in v]}
    if isinstance(v, frozenset):
        return {"__fset__": [_wire(x) for x in v]}
    if isinstance(v, set):
        return {"__set__": [_wire(x) for x in v]}
    if isinstance(v, dict):
        return {k: _wire(x) for k, x in v.items()}
    return v


def _wire_rows(rows):
    """`_wire` every value inside a SynthEnumerate example row, leaving the
    row list and the row dicts as plain JSON."""
    out = []
    for r in rows:
        row = dict(r)
        if isinstance(row.get("inputs"), dict):
            row["inputs"] = {k: _wire(v) for k, v in row["inputs"].items()}
        for k in ("output", "expected"):
            if k in row:
                row[k] = _wire(row[k])
        out.append(row)
    return out

'''

# (path, before, after) — every pair exact in BOTH directions, so apply and
# revert are inverses and both are idempotent.
EDITS = [
    # --- (a) the two verdict lanes stop discarding a non-scalar result ---
    (PSY,
     '        sub.set_attr(r, "got", got if isinstance(got, _SCALARS) else None)\n',
     '        # ARC6 value layer: the non-scalar cast is GONE. `got` is now\n'
     '        # stored as-is, carrying its container type (list vs tuple), so\n'
     '        # `ps_row_pass`\'s own `Eq(got, expected)` is a type-faithful\n'
     '        # comparison. The RULE is byte-unchanged; only this mechanical\n'
     '        # record stopped discarding what the rule needs to decide on.\n'
     '        sub.set_attr(r, "got", got)\n'),
    (PSY,
     '        sub.set_attr(r, "fu_got", got if isinstance(got, _SCALARS) else None)\n',
     '        # ARC6 value layer, HV4: the FOLD-UP lane carried the identical\n'
     '        # scalar-only cast, and `ps_foldup_accept`/`ps_foldup_reject`\n'
     '        # have no `fu_cmp_ok` to fall back on. Fixed in the same motion,\n'
     '        # so "the non-scalar verdict is fixed" is not false here.\n'
     '        sub.set_attr(r, "fu_got", got)\n'),
    # --- (b) the Lit wire encoding ---------------------------------------
    (PSY,
     '\ndef _row_cmp_ok(got, expected, tol, unordered) -> float:',
     _WIRE_DEF + '\ndef _row_cmp_ok(got, expected, tol, unordered) -> float:'),
    (PSY,
     '        rows.append({"inputs": env, "output": rat.get("expected")})\n',
     '        rows.append({"inputs": {k: _wire(v) for k, v in env.items()},\n'
     '                     "output": _wire(rat.get("expected"))})\n'),
    (PSY,
     '    spec = {"type": "SynthEnumerate",\n'
     '            "examples": {"type": "Lit", "value": rows},\n'
     '            "max_size": 7, "max_candidates": 0, "saturate_k": 0, "field": ""}\n',
     '    spec = {"type": "SynthEnumerate",\n'
     '            "examples": {"type": "Lit", "value": _wire_rows(rows)},\n'
     '            "max_size": 7, "max_candidates": 0, "saturate_k": 0, "field": ""}\n'),
    (MOVES,
     '             "examples": {"type": "Lit", "value": spec_rows},\n',
     '             "examples": {"type": "Lit", "value": _wire_rows(spec_rows)},\n'),
    (MOVES,
     'def _run_synth_enumerate(sub, spec_rows: List[Dict[str, Any]], *,\n'
     '                          max_size: int, max_candidates: int) -> Dict[str, Any]:\n',
     'def _run_synth_enumerate(sub, spec_rows: List[Dict[str, Any]], *,\n'
     '                          max_size: int, max_candidates: int) -> Dict[str, Any]:\n'
     '    # ARC6 value layer: JSON erases list-vs-tuple at the `Lit` boundary.\n'
     '    # Function-local import — `prog_synthesis` imports THIS module.\n'
     '    from domains.prog_synthesis import _wire_rows\n'),
    (RETR,
     '        derived_rows.append({"inputs": env, "output": r["expected"]})\n',
     '        derived_rows.append({"inputs": psy._wire(env),\n'
     '                             "output": psy._wire(r["expected"])})\n'),
]


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


FILES = [PSY, MOVES, RETR]


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"
    if mode == "status":
        for p in FILES:
            src = open(p).read()
            mine = [e for e in EDITS if e[0] == p]
            applied = sum(1 for _, b, a in mine if a in src)
            clean = sum(1 for _, b, a in mine if b in src and a not in src)
            print(f"{os.path.relpath(p, ROOT):32s} applied={applied}/{len(mine)} "
                  f"clean={clean}/{len(mine)} sha256={sha256(p)}")
        return
    pairs = EDITS if mode == "apply" else [(p, a, b) for p, b, a in reversed(EDITS)]
    bufs = {p: open(p).read() for p in FILES}
    for path, before, after in pairs:
        src = bufs[path]
        if after in src and before not in src:
            continue  # already in the target state
        if src.count(before) != 1:
            raise SystemExit(f"{mode}: anchor count={src.count(before)} in "
                             f"{os.path.relpath(path, ROOT)}:\n{before!r}")
        bufs[path] = src.replace(before, after, 1)
    for p, src in bufs.items():
        with open(p, "w") as fh:
            fh.write(src)
    for p in FILES:
        print(f"{mode} {os.path.relpath(p, ROOT):32s} sha256={sha256(p)}")


if __name__ == "__main__":
    main()
