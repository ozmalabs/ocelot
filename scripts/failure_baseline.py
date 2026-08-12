#!/usr/bin/env python3
"""THE BASELINE, AS A LIST — build it, and verify it.

    A BASELINE MUST BE A LIST OF NODE IDS WITH LAST-GREEN COMMITS, NEVER A COUNT.
    A COUNT CAN BE HELD; A LIST HAS TO BE READ.

WHY (VISION_GATE_SCOPE_B_RESULTS.md section 10). The convention in this tree is a COUNT:
*"held the bench at the exact pre-existing 19-failure baseline throughout."* 19 became 144
over ~10 days with **no rung on the path negligent** — each honestly held a number that had
stopped meaning anything.

A COUNT IS A SUBSTRING SELECTOR'S COUSIN: it matches the SHAPE of the answer without
touching its CONTENT. This arc is 0-for-6 on substring selectors, and this is the same
defect one level up, at the level of a policy. Concretely, a count cannot distinguish:

  * a NEW red from an OLD one            (so a regression lands inside the number),
  * a red that has been FIXED            (so a success is reported as a failure forever),
  * a test that has NEVER ONCE PASSED    (test_codec_graph_resident: 30 nodes, ~48 days)
    from one that broke this morning.

A list can. Every entry has to be read, and every entry either gets fixed, re-pinned or
deleted.

SUBCOMMANDS
  build   raw sweep JSON  ->  results/failure_baseline.json   (the LIST)
  verify  re-run the listed node ids and report NEW / STALE / held

A `total` field is emitted, but it is DERIVED from the list and never authored — a count
computed FROM content is a summary; a count standing IN FOR content is the defect.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIST_PATH = ROOT / "results" / "failure_baseline.json"

# Classification is by the failure's own message, and every class is one a READER has to
# act on differently. UNCLASSIFIED is a first-class outcome: an entry nobody has diagnosed
# is exactly the entry a count would hide, so it is labelled, never defaulted.
_CLASSES = {
    "ENVIRONMENTAL_ENGINE_OR_IMPORT": (
        "EngineProvenanceError", "importorskip", "ModuleNotFoundError",
        "ImportError", "No module named"),
    # Protocol 12.3. ZERO of these remain at this HEAD -- the two that produced them were
    # range-pinned by this rung. The class is KEPT so a re-introduction is named on sight.
    "PROVENANCE_FALSE_ACCUSATION": (
        "Rust source moved", "CHANGED since", "CHANGED between"),
    # Protocol 10.2: `data/` is gitignored, so a fresh worktree has no slab. These are the
    # LOUD instances -- and 10.2's whole point is that the loud ones are the MINORITY: a
    # missing slab usually produces a fluent, well-formed, WRONG answer that surfaces as an
    # ordinary AssertionError. So this class is a FLOOR on data-conditional entries, never
    # an estimate of them.
    "GITIGNORED_DATA_ABSENT": ("FileNotFoundError", "data/"),
    # 10.3-proposed: `results/*_checkpoints/` is the THIRD gitignored class, red in every
    # worktree and green in canonical, with nothing announcing it.
    "GITIGNORED_RESULTS_ARTIFACT_ABSENT": ("results/run", "_checkpoints"),
}


def classify(message: str) -> str:
    # Order matters: the two gitignored classes are distinguished by PATH, so they are
    # tested on the specific path fragment before the generic exception name.
    if "FileNotFoundError" in message:
        if "/results/" in message or "results/run" in message:
            return "GITIGNORED_RESULTS_ARTIFACT_ABSENT"
        if "/data/" in message:
            return "GITIGNORED_DATA_ABSENT"
    for cls, needles in _CLASSES.items():
        if cls.startswith("GITIGNORED"):
            continue
        if any(n in message for n in needles):
            return cls
    return "UNCLASSIFIED"


# Per-file annotations for entries whose cause has actually been DIAGNOSED. The whole
# point of a list over a count is that entries carry what a reader needs in order to
# fix / re-pin / delete them, so a diagnosis lands HERE rather than in prose nobody
# joins back up to the node id.
#
# `last_green_commit` is MEASURED or STATIC — never inferred from a behavioural re-run
# of an old tree against today's engine (the confound that cost the Scope B peer two
# headline durations).
_ANNOTATIONS = {
    "tests/test_codec_graph_resident.py": {
        "class": "REAL_REGRESSION_ROOT_CAUSED",
        "last_green_commit": "f23849f5 (STATIC, not a behavioural re-run)",
        "diagnosis":
            "runners/dsl/src/codec.rs::install_field_grammar_rules does "
            "`substrate.rules.push(rule)`, bypassing Substrate::add_rule -- the function "
            "whose own comment calls itself 'the sole path that pushes into self.rules, "
            "so it owns making a newly-installed rule live'. All 20 codec rules install "
            "with active:false and the matcher skips every one. PROVEN: same 20 rules via "
            "add_rule -> 10 firings, 10/10 PPS fields byte-correct; via the Rust install "
            "-> 0 firings, 0 fields. export_rules() reads 20x False vs 20x True. "
            "THE GATE'S EXPECTATION ('expected 10 rule firings, got 0') WAS RIGHT ON BOTH "
            "NUMBERS. Do NOT retract the claim and do NOT edit the test. "
            "Broke at 79a05702 ('codec field-grammar Rules native in Rust runner', "
            "2026-06-01), SIX commits after the file was born green at f23849f5 the same "
            "day -- so it is NOT 'never green', it is 'green for six commits, then "
            "absorbed into a baseline for ~2875 commits'. "
            "See VISION_BASELINE_LIST_RESULTS.md section 1.",
    },
}


def build(raw_path: str, out_path: Path, messages_from: str | None = None,
          condition: str | None = None) -> int:
    raw = json.loads(Path(raw_path).read_text())

    # The FIRST full sweep captured correct node ids but truncated messages at column 80
    # (see failure_baseline_sweep.sweep_one). A targeted re-run of the red files with
    # COLUMNS=250 supplies the diagnoses. Overlaying is only legitimate if the two runs
    # AGREE on the red set, so that agreement is CHECKED here and RECORDED in the
    # artifact -- it is also an independent reproducibility measurement of the verdict.
    overlay, repro = {}, None
    if messages_from:
        m = json.loads(Path(messages_from).read_text())
        overlay = {n["node"]: n["message"]
                   for r in m["results"] for n in r["nodes"]}
        first = {n["node"] for r in raw["results"] for n in r["nodes"]}
        repro = {
            "messages_from": messages_from,
            "nodes_first_sweep": len(first),
            "nodes_re_run": len(overlay),
            "identical_node_set": sorted(first) == sorted(overlay),
            "only_in_first": sorted(first - set(overlay))[:20],
            "only_in_re_run": sorted(set(overlay) - first)[:20],
        }
    entries, not_established, nonzero, all_skipped = [], [], [], []
    green_files = 0
    for r in raw["results"]:
        if r["status"] == "NOT_ESTABLISHED":
            not_established.append({"file": r["file"], "reason": r["reason"],
                                    "seconds": r["seconds"]})
            continue
        if r["status"] == "GREEN":
            green_files += 1
            continue
        if r["status"] == "ALL_SKIPPED":
            # every test guarded (absent optional dep / unresolvable pin) — not a
            # red, and NOT silently green either: recorded, so a reader can see how
            # much of the tree was guarded rather than measured.
            all_skipped.append(r["file"])
            continue
        if r["status"] == "NONZERO_NO_NODES":
            nonzero.append({"file": r["file"], "returncode": r["returncode"],
                            "tail": r.get("tail", "")[:300]})
            continue
        for n in r["nodes"]:
            msg = overlay.get(n["node"], n["message"])
            e = {
                "node": n["node"],
                "file": r["file"],
                "kind": n["kind"],
                "message": msg,
                "class": classify(msg),
                # LAST-GREEN is UNKNOWN unless MEASURED on a single engine. The Scope B
                # peer retracted two headline durations to exactly this confound
                # (historical tree x current engine), so it is never inferred here.
                "last_green_commit": "UNKNOWN",
                "file_seconds": r["seconds"],
            }
            e.update(_ANNOTATIONS.get(r["file"], {}))
            entries.append(e)
    entries.sort(key=lambda e: e["node"])
    payload = {
        "_README": "A BASELINE IS A LIST, NEVER A COUNT. Every entry must be fixed, "
                   "re-pinned or deleted. `total` is DERIVED from `entries`; do not "
                   "author it, and never quote it in place of the list.",
        "head": raw["head"],
        "engine": _engine_line(),
        # THE CONDITION IS PART OF THE NUMBER. CLAUDE.md measures this same tree at
        # 144-145 red node ids with data/ symlinked and 565 without — a 3.9x spread
        # on one engine at one commit — so a baseline whose condition is hard-coded
        # to the condition of the FIRST sweep that ever ran is a rumour the moment
        # anyone measures under another one. Passed in, never assumed.
        "condition": condition or "no data/ symlink; own engine build; per-file subprocess",
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "loadavg_start": raw["loadavg_start"],
        "loadavg_end": raw["loadavg_end"],
        "workers": raw["workers"],
        "per_file_timeout_s": raw["per_file_timeout_s"],
        "reproducibility": repro,
        "total": len(entries),                      # DERIVED, not authored
        "by_class": dict(Counter(e["class"] for e in entries)),
        "files_green": green_files,
        "files_red": len({e["file"] for e in entries}),
        "coverage": {
            "files_swept": raw["files"],
            "NOT_ESTABLISHED": not_established,     # never green, never red
            "NONZERO_NO_NODES": nonzero,
            "ALL_SKIPPED": all_skipped,          # guarded, not measured, not red
        },
        "entries": entries,
    }
    out_path.write_text(json.dumps(payload, indent=1))
    print(f"wrote {out_path}: {len(entries)} node ids across "
          f"{payload['files_red']} files; "
          f"{len(not_established)} NOT_ESTABLISHED; classes={payload['by_class']}")
    return 0


def _engine_line() -> str:
    """The engine THE SWEEP ACTUALLY USED — which is not what a bare interpreter loads.

    BUG FOUND IN THIS FUNCTION MID-RUN, and it is the disease this arc keeps finding: an
    instrument mis-recording the very thing it exists to record. Without
    `engine_preamble()` a plain `python3` resolves `substrate_rs` through the global
    `.pth`, which is an ABSOLUTE PATH INTO THE CANONICAL TREE (protocol 10.1). This
    function therefore reported `engine b06e02ed9323 @ <CANONICAL>` while every swept file
    — run under pytest, whose `conftest.py` DOES call `engine_preamble()` — was measured on
    this worktree's own `engine d657468d9e1f`. The artifact would have carried a provenance
    line naming a binary that produced none of its numbers, inside the one field its own
    gate requires.

    Protocol 10.1 rule 3 says it in as many words: *any non-pytest entrypoint (a rung
    script) must call `engine_preamble()` itself.* This is a rung script. It now does.
    """
    sys.path.insert(0, str(ROOT))
    try:
        from domains import engine_provenance
        engine_provenance.engine_preamble()          # <- the missing line
        return engine_provenance.provenance_line()
    except Exception as e:                                  # pragma: no cover
        return f"UNAVAILABLE: {e}"


def verify(list_path: Path, only_fast: float | None, limit: int | None) -> int:
    """Re-run the listed node ids. NEW reds and STALE entries are BOTH failures."""
    data = json.loads(list_path.read_text())
    entries = data["entries"]
    if only_fast is not None:
        entries = [e for e in entries if e["file_seconds"] <= only_fast]
    if limit:
        entries = entries[:limit]
    by_file: dict[str, list[str]] = {}
    for e in entries:
        by_file.setdefault(e["file"], []).append(e["node"])

    listed = {e["node"] for e in entries}
    still_red, now_green, new_red = set(), set(), set()
    for f, nodes in sorted(by_file.items()):
        r = subprocess.run(
            [sys.executable, "-W", "ignore", "-m", "pytest", "-q", "-p", "no:randomly",
             "--tb=no", "-rfE", f], cwd=ROOT, capture_output=True, text=True, timeout=900)
        red_now = {ln.split()[1] for ln in (r.stdout + r.stderr).splitlines()
                   if ln.strip().startswith(("FAILED ", "ERROR "))
                   and len(ln.split()) > 1}
        for n in nodes:
            (still_red if n in red_now else now_green).add(n)
        new_red |= {n for n in red_now if n not in listed and n.split("::")[0] == f}

    print(f"held (still red): {len(still_red)}")
    print(f"STALE (listed but now GREEN — the list must be updated): {len(now_green)}")
    for n in sorted(now_green):
        print(f"    STALE {n}")
    print(f"NEW (red but not on the list): {len(new_red)}")
    for n in sorted(new_red):
        print(f"    NEW   {n}")
    print("LOADAVG:", os.getloadavg())
    return 1 if (now_green or new_red) else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--raw", default="results/failure_baseline_sweep_raw.json")
    b.add_argument("--out", default=str(LIST_PATH))
    b.add_argument("--messages-from", default=None)
    b.add_argument("--condition", default=None,
                   help="the measurement condition, stamped into the artifact "
                        "(data/ symlink? optional deps? engine?) — protocol 10/12")
    v = sub.add_parser("verify")
    v.add_argument("--list", default=str(LIST_PATH))
    v.add_argument("--only-fast", type=float, default=None,
                   help="only re-run entries whose FILE ran in <= this many seconds")
    v.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    if a.cmd == "build":
        return build(a.raw, Path(a.out), a.messages_from, a.condition)
    return verify(Path(a.list), a.only_fast, a.limit)


if __name__ == "__main__":
    raise SystemExit(main())
