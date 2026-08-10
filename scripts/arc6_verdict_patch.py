#!/usr/bin/env python
"""arc6_verdict_patch — apply / revert the NON-SCALAR ROW VERDICT candidate.

THE CANDIDATE, stated exactly (and it is a SEED edit only — zero Python,
zero Rust, so no engine rebuild and no three-arm requirement):

  ps_row_pass:  Eq(Attr(r,"got"), Attr(r,"expected"))
             -> Eq(Attr(r,"cmp_ok"), 1.0)
  ps_row_fail:  Not(Eq(Attr(r,"got"), Attr(r,"expected")))
             -> Eq(Attr(r,"cmp_ok"), 0.0)

i.e. the plain row rules read the comparison fact THAT IS ALREADY COMPUTED
and already correct (`domains/prog_synthesis.py::_row_cmp_ok`, recorded by
`eval_and_record` off the RAW result before the `_SCALARS` cast), instead
of the `got` attribute the adapter sets to `None` for anything outside
int/float/str/bool.  Nothing new is invented: this is exactly the
comparison `ps_row_pass_special` / `ps_row_fail_special` already make on
tol/unordered rows, and exactly the one `holdout_verdict`'s `agree()`
already makes on held-out rows.

Usage:  python scripts/arc6_verdict_patch.py apply|revert|status
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_PATH = os.path.join(ROOT, "seeds", "program_synthesis.json")


def _attr(var: str, key: str) -> dict:
    return {"type": "Attr", "node": {"type": "Var", "name": var}, "key": key}


GOT_EQ_EXPECTED = {"type": "Eq", "a": _attr("r", "got"), "b": _attr("r", "expected")}
NOT_GOT_EQ_EXPECTED = {"type": "Not", "arg": GOT_EQ_EXPECTED}
CMP_OK_PASS = {"type": "Eq", "a": _attr("r", "cmp_ok"), "b": {"type": "Lit", "value": 1.0}}
CMP_OK_FAIL = {"type": "Eq", "a": _attr("r", "cmp_ok"), "b": {"type": "Lit", "value": 0.0}}


def _swap(node, old, new):
    """Structural replace of `old` by `new` anywhere inside `node`."""
    if node == old:
        return json.loads(json.dumps(new)), 1
    n = 0
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            out[k], c = _swap(v, old, new)
            n += c
        return out, n
    if isinstance(node, list):
        out = []
        for v in node:
            r, c = _swap(v, old, new)
            out.append(r)
            n += c
        return out, n
    return node, 0


def _rule(d, name):
    for r in d["rules"]:
        if r["name"] == name:
            return r
    raise KeyError(name)


def status(d) -> str:
    p = json.dumps(_rule(d, "ps_row_pass")["where"])
    if '"cmp_ok"' in p:
        return "patched"
    if '"got"' in p:
        return "baseline"
    return "unknown"


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"
    with open(SEED_PATH) as f:
        d = json.load(f)
    st = status(d)
    if mode == "status":
        print(st)
        return
    if mode == "apply":
        assert st == "baseline", "already %s" % st
        rp = _rule(d, "ps_row_pass")
        rf = _rule(d, "ps_row_fail")
        rp["where"], n1 = _swap(rp["where"], GOT_EQ_EXPECTED, CMP_OK_PASS)
        rf["where"], n2 = _swap(rf["where"], NOT_GOT_EQ_EXPECTED, CMP_OK_FAIL)
        assert (n1, n2) == (1, 1), "swap count %r" % ((n1, n2),)
    elif mode == "revert":
        assert st == "patched", "already %s" % st
        rp = _rule(d, "ps_row_pass")
        rf = _rule(d, "ps_row_fail")
        rp["where"], n1 = _swap(rp["where"], CMP_OK_PASS, GOT_EQ_EXPECTED)
        rf["where"], n2 = _swap(rf["where"], CMP_OK_FAIL, NOT_GOT_EQ_EXPECTED)
        assert (n1, n2) == (1, 1), "swap count %r" % ((n1, n2),)
    else:
        raise SystemExit("usage: apply|revert|status")
    with open(SEED_PATH, "w") as f:
        json.dump(d, f, indent=2)
        f.write("\n")
    print(mode, "->", status(json.load(open(SEED_PATH))))


if __name__ == "__main__":
    main()
