"""opgrammar_bulk_parity_sweep — PROGRAM_SYNTHESIS_GAMMA_BULK_TRANSCRIPTION_
RESULTS.md's own verification harness. NOT a production module, NOT part of
the named 9-file regression suite, NOT wired into any agent path — a
one-off diagnostic script, in the family of `scripts/ceiling3_diag_sweep.py`.

For every real MBPP task in `tests/fixtures/mbpp/sanitized-mbpp.json` whose
"primary" revealed rows are runnable, this script:

  1. Computes the 11-flag `_synth_spec_shape_flags` dict from the raw
     revealed rows (the SAME flags `run_enumerate` mints onto a live
     `SynthSpecShape` node).
  2. Computes `_real_admitted_ops(flags)` — a FAITHFUL, hand-traced Python
     replica of the CURRENT `eval_synth_enumerate` default-ops ladder
     (`runners/dsl/src/synth_enumerate.rs:2093-2408`, re-read in full while
     writing this), including the branches this rung's Γ productions
     deliberately do NOT cover (the `DICT_DEFAULT_OPS` branch and its two
     new ops `GroupCount`/`DictMerge`/`DictFromPairs`, and the unconditional
     `Mod`/`Sqrt` append on the bare-scalar branch) — this is the
     "ground truth" oracle.
  3. Computes Γ's admitted set by calling `is_edge_admissible` once per
     real `SynthOp` name (57 calls) against a freshly-minted
     `SynthSpecShape` node carrying the computed flags.
  4. Diffs the two sets and classifies every difference as EXPECTED (an op
     name this rung deliberately left out of Γ scope, or a spec whose real
     admitted set comes from the out-of-scope `DICT_DEFAULT_OPS` branch) or
     UNEXPECTED (anything else — a genuine transcription bug).

Prints a summary table and exits nonzero if any UNEXPECTED mismatch is
found, so it doubles as a CI-style gate when run directly.
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, "runners/dsl/python")
sys.path.insert(0, ".")
sys.path.insert(0, "scripts")

import substrate_rs as srs  # noqa: E402
from domains import mbpp_spec as ms  # noqa: E402
from domains import prog_synthesis as psy  # noqa: E402

# --------------------------------------------------------------------------- #
# The out-of-Gamma-scope op population: never admitted by ANY production
# this rung (or the earlier SLICE1 rung) ships, by deliberate, documented
# design (PROGRAM_SYNTHESIS_GAMMA_BULK_TRANSCRIPTION_PREREG.md section 1).
# --------------------------------------------------------------------------- #
_OUT_OF_SCOPE_OPS = frozenset({"GroupCount", "DictMerge", "DictFromPairs", "Mod", "Sqrt"})

DEFAULT_OPS = ["Plus", "Times", "Minus", "Div", "Min", "Max", "Abs", "Neg",
               "Gt", "Lt", "Eq", "IfThenElse"]
LIST_EXTRA_OPS = ["Len", "SumList", "MaxList", "MinList", "MaxLenOver", "MinLenOver",
                   "First", "LastElem", "JoinList", "FilterList", "MapList",
                   "ProdList", "ConcatList", "ArgMaxLenOver"]
TUPLE_BUILD_OPS = ["TupleOf"]
SET_DEFAULT_OPS = ["Eq", "IfThenElse", "Sort", "Reverse", "Slice", "SetMap",
                    "Intersect", "Union", "IntersectAll", "UnionAll"]
DICT_DEFAULT_OPS = ["Eq", "IfThenElse", "GroupCount", "DictMerge", "DictFromPairs"]
DEFAULT_STR_OPS = ["Concat", "CaseFold", "Eq", "IfThenElse", "Replace", "Split",
                    "StrCount", "Capitalize", "Reverse", "Slice", "Str",
                    "MapList", "JoinList"]


def _real_admitted_ops(flags: "dict[str, bool]") -> "set[str]":
    """Faithful Python replica of the CURRENT `eval_synth_enumerate`
    default-ops ladder (synth_enumerate.rs:2093-2408), branch order
    preserved exactly (`if`/`else if`/`else if`/`else if`/`else`)."""
    T = flags["is_string_shaped"]
    S = flags["output_is_setlike"]
    L = flags["is_list_shaped"]
    D = flags["output_is_dictlike"]
    has_str = flags["has_string_value"]
    has_float = flags["has_float_value"]
    has_dict = flags["has_dict_value"]
    has_rep = flags["has_repeated_list_element"]
    out_listlike = flags["output_is_listlike"]
    out_bare_int = flags["output_is_bare_int"]

    if T:
        return set(DEFAULT_STR_OPS)
    if S:
        return set(SET_DEFAULT_OPS)
    if L:
        v = set(DEFAULT_OPS) | set(LIST_EXTRA_OPS)
        if out_listlike:
            v |= set(TUPLE_BUILD_OPS)
            v.add("Sort")
        if out_listlike and has_str:
            v.add("Split")
        if has_float:
            v.add("Round")
        if (not out_listlike) and out_bare_int and (not has_str) and (not has_float):
            v.add("ParseInt")
        if has_rep:
            v.add("IndexedMap")
        if has_dict:
            v |= {"DictItems", "SortBy", "Reverse"}
        if flags.get("has_list_of_lists") and not has_dict:
            v.add("SortBy")
        if D:
            v.add("GroupCount")
        return v
    if D:
        return set(DICT_DEFAULT_OPS)
    v = set(DEFAULT_OPS)
    if has_str:
        v |= {"Replace", "Split", "StrCount", "Capitalize", "Str", "ParseInt"}
    if has_float:
        v.add("Round")
    # Site K (has_rep -> IndexedMap on this branch) is DEAD in current
    # source (PREREG section 3) -- correctly NOT added here either, this
    # oracle mirrors the REAL, live ladder, not the design doc's original
    # (now-stale) description of it.
    v.add("Mod")
    v.add("Sqrt")
    return v


def _gamma_admitted_ops(sub, all_op_names, flags) -> "set[str]":
    n = sub.add_node("SynthSpecShape", flags)
    out = set()
    for name in all_op_names:
        if sub._inner.is_edge_admissible(n, "admits_op", "SynthOp", {"name": name}):
            out.add(name)
    return out


def main() -> int:
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    all_op_names = sorted(s.node(n)["attrs"]["name"] for n in s.nodes("SynthOp"))
    assert len(all_op_names) == 57, len(all_op_names)

    with open("tests/fixtures/mbpp/sanitized-mbpp.json") as f:
        tasks = json.load(f)

    n_checked = 0
    n_exact = 0
    unexpected = []
    dict_branch_specs = 0
    out_of_scope_diff_specs = 0

    for task in tasks:
        try:
            parsed = ms.parse_asserts(task)
            split = ms.split_rows(parsed["rows"], "primary")
        except Exception:
            continue
        if not split["runnable"]:
            continue
        raw_rows = []
        for r in split["revealed"]:
            raw_rows.append({"inputs": dict(r.get("inputs") or {}), "output": r.get("expected")})
        if not raw_rows:
            continue
        flags = psy._synth_spec_shape_flags(raw_rows)
        real = _real_admitted_ops(flags)
        gamma = _gamma_admitted_ops(s, all_op_names, flags)

        n_checked += 1
        diff = real.symmetric_difference(gamma)
        # Classify: expected if every differing name is out-of-scope, OR the
        # spec's real set came from the (entirely out-of-scope) Dict branch.
        is_dict_branch = (not flags["is_string_shaped"] and not flags["output_is_setlike"]
                           and not flags["is_list_shaped"] and flags["output_is_dictlike"])
        if is_dict_branch:
            dict_branch_specs += 1
        expected_diff = diff <= _OUT_OF_SCOPE_OPS if not is_dict_branch else True
        if not diff:
            n_exact += 1
        elif expected_diff:
            out_of_scope_diff_specs += 1
        else:
            unexpected.append((task["task_id"], sorted(diff), flags))

    print(f"Checked {n_checked} real, runnable MBPP task specs.")
    print(f"Exact set-agreement (Gamma == real, no diff at all): {n_exact}/{n_checked}")
    print(f"Diff-but-fully-explained (out-of-scope ops or Dict branch): "
          f"{out_of_scope_diff_specs}/{n_checked}")
    print(f"Specs landing in the out-of-scope DICT_DEFAULT_OPS branch: {dict_branch_specs}")
    print(f"UNEXPECTED mismatches: {len(unexpected)}")
    for task_id, names, flags in unexpected:
        print(f"  task {task_id}: diff={names} flags={flags}")

    covered = n_exact + out_of_scope_diff_specs
    print(f"\nTOTAL EXPLAINED: {covered}/{n_checked} "
          f"({'ALL EXPLAINED, GO' if not unexpected else 'UNEXPLAINED MISMATCHES FOUND'})")
    return 1 if unexpected else 0


if __name__ == "__main__":
    raise SystemExit(main())
