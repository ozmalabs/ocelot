#!/usr/bin/env python3
"""arc6_full_sweep_diff — PAIR two `arc6_valuelayer_sweep.py` artifacts
(arm A = pre-value-layer baseline, arm C = current HEAD) and emit the
combined artifact `results/arc6_full_sweep.json`.

Everything here is a LIST of node ids. Nothing is a count that could be
"held" while the underlying set drifts (CLAUDE.md's retracted
count-shaped baseline).

  python scripts/arc6_full_sweep_diff.py --a results/..._armA.json \
      --c results/..._armC.json --out results/arc6_full_sweep.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def norm(node: str) -> str:
    """`tests/test_x.py::y` -> `test_x.py::y` (both forms occur)."""
    return node.split("tests/", 1)[-1]


def load(p: Path) -> dict:
    d = json.loads(p.read_text())
    per_file = {r["file"]: r for r in d["results"]}
    nodes = {}
    for r in d["results"]:
        for n in r["nodes"]:
            nodes[norm(n["node"])] = {"file": r["file"], "kind": n["kind"],
                                      "message": n["message"]}
    return {"raw": d, "per_file": per_file, "nodes": nodes}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--c", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    A = load(Path(args.a))
    C = load(Path(args.c))

    base = json.loads((ROOT / "results" / "failure_baseline.json").read_text())
    base_nodes = {norm(e["node"]) for e in base["entries"]}

    new_in_c = sorted(set(C["nodes"]) - set(A["nodes"]))
    fixed_in_c = sorted(set(A["nodes"]) - set(C["nodes"]))
    common = sorted(set(A["nodes"]) & set(C["nodes"]))

    def status_lists(S):
        out = {}
        for st in ("RED", "NOT_ESTABLISHED", "NONZERO_NO_NODES", "GREEN"):
            out[st] = sorted(f for f, r in S["per_file"].items()
                             if r["status"] == st)
        return out

    art = {
        "_README": (
            "PAIRED FULL-TREE SWEEP, arm A (pre-value-layer baseline code + "
            "engine 48da7257...) vs arm C (HEAD + engine 8311d435...), same "
            "tree, same condition (data/ symlinked), same instrument "
            "(scripts/arc6_valuelayer_sweep.py, which passes --confcutdir). "
            "EVERY red is a LIST of node ids. `results/failure_baseline.json` "
            "was measured under a DIFFERENT condition (no data/ symlink, head "
            "0e61f60e8d, 648 files) so membership in it is EVIDENCE, NOT "
            "PROOF, that a red is pre-existing."),
        "arm_A": {
            "engine_sha256": A["raw"]["engine_sha256"],
            "files_requested": A["raw"]["files_requested"],
            "files_done": A["raw"]["files_done"],
            "wall_s": A["raw"]["wall_s"],
            "workers": A["raw"]["workers"],
            "per_file_timeout_s": A["raw"]["per_file_timeout_s"],
            "files_by_status": status_lists(A),
            "red_node_ids": sorted(A["nodes"]),
        },
        "arm_C": {
            "engine_sha256": C["raw"]["engine_sha256"],
            "files_requested": C["raw"]["files_requested"],
            "files_done": C["raw"]["files_done"],
            "wall_s": C["raw"]["wall_s"],
            "workers": C["raw"]["workers"],
            "per_file_timeout_s": C["raw"]["per_file_timeout_s"],
            "files_by_status": status_lists(C),
            "red_node_ids": sorted(C["nodes"]),
        },
        "paired": {
            "new_red_in_C": [
                {"node": n, "file": C["nodes"][n]["file"],
                 "kind": C["nodes"][n]["kind"],
                 "message": C["nodes"][n]["message"],
                 "in_failure_baseline": n in base_nodes}
                for n in new_in_c],
            "red_in_A_green_in_C": [
                {"node": n, "file": A["nodes"][n]["file"],
                 "message": A["nodes"][n]["message"]} for n in fixed_in_c],
            "red_in_both": common,
            "red_in_both_and_in_failure_baseline": [
                n for n in common if n in base_nodes],
            "red_in_both_not_in_failure_baseline": [
                n for n in common if n not in base_nodes],
        },
        "failure_baseline_reference": {
            "path": "results/failure_baseline.json",
            "head": base["head"], "condition": base["condition"],
            "n_entries": len(base["entries"]),
            "files_swept": base["coverage"]["files_swept"],
            "caveat": ("measured with NO data/ symlink; CLAUDE.md records "
                       "that condition is worth 53 red files vs 147 — so "
                       "membership is evidence, not proof"),
        },
    }
    Path(ROOT / args.out).write_text(json.dumps(art, indent=1))
    print("new red in C (%d):" % len(new_in_c))
    for n in new_in_c:
        print("   ", n, "  [in failure_baseline]" if n in base_nodes else "")
    print("red in A, green in C (%d):" % len(fixed_in_c))
    for n in fixed_in_c:
        print("   ", n)
    print("red in both: %d  (of which %d are in failure_baseline)"
          % (len(common), len(art["paired"]["red_in_both_and_in_failure_baseline"])))
    print("== wrote", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
